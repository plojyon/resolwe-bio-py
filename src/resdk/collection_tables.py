""".. Ignore pydocstyle D400.

=================
Collection Tables
=================

.. autoclass:: CollectionTables
    :members:

    .. automethod:: __init__
"""
import os
from datetime import datetime
from functools import lru_cache
from io import BytesIO
from typing import Callable, Dict, List, NamedTuple, Optional
from urllib.parse import urljoin

import pandas as pd
import pytz

from resdk import Resolwe
from resdk.resources import Collection
from resdk.utils.table_cache import default_cache_dir, load_cache, save_cache

TPM = "tpm"
COUNTS = "rc"
EXPRESSION_TYPES = [TPM, COUNTS]

META = "meta"

CHUNK_SIZE = 1000


class _TableSample(NamedTuple):
    sample_slug: str
    expression_files: Dict[str, str]
    metadata: dict


class CollectionTables:
    """A helper class to fetch collection's expression and meta data.

    This class enables fetching given collection's data and returning it as tables which have samples in rows
    and gene symbols in columns.

    When calling :meth:`CollectionTables.expressions`, :meth:`CollectionTables.counts` and
    :meth:`CollectionTables.metadata` for the first time the corresponding data gets fetched from the server.
    This data than gets cached in memory and on disc and is used in consequent calls until the modified
    attribute changes.
    """

    def __init__(self, collection: Collection, cache_dir=None):
        """Initialize class.

        :param collection: collection to use
        :param cache_dir: cache directory location, if not specified system specific cache directory is used
        """
        self.resolwe = collection.resolwe  # type: Resolwe
        self.collection = collection
        if self.collection.samples.count() == 0:
            raise ValueError(f"Collection {self.collection.name} has no samples!")

        self.cache_dir = cache_dir
        if self.cache_dir is None:
            self.cache_dir = default_cache_dir()
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        self._table_samples_ = []  # type: List[_TableSample]
        self._meta = None  # type: Optional[pd.DataFrame]
        self._expressions = {}  # type: Dict[str, pd.DataFrame]
        self._gene_map_ = {}  # type: Dict[str, str]
        self._modified = None  # type: Optional[datetime]

    @property
    def modified(self) -> datetime:
        """Return the newest modification date out of all sample.

        The returned datetime object is used to detect data changes on the server.

        :return: modified datetime in UTC
        """
        if self._modified is None:
            newest_modified = max(s.modified for s in self.collection.samples.iterate())
            # transform into UTC so changing timezones won't effect cache
            self._modified = newest_modified.astimezone(pytz.utc)
        return self._modified

    @lru_cache()
    def metadata(self) -> pd.DataFrame:
        """Return samples metadata in a table format.

        :return: table of metadata
        """
        cache = load_cache(self.cache_dir, self.collection.slug, META, self.modified)
        if cache is not None:
            self._meta = cache

        if self._meta is None:
            self._meta = self._get_metadata()

        save_cache(
            self._meta, self.cache_dir, self.collection.slug, META, self.modified
        )
        return self._meta

    def _get_metadata(self) -> pd.DataFrame:
        """Flatten samples JSON metadata into a table."""
        meta = pd.json_normalize([ts.metadata for ts in self._table_samples])
        meta = meta.set_index("sample_slug").sort_index()
        return meta

    @property
    def _table_samples(self) -> List[_TableSample]:
        """Return a list of _TableSample objects containing expression files urls and metadata."""
        if not self._table_samples_:
            self._table_samples_ = self._get_table_samples()
        return self._table_samples_

    def _get_table_samples(self):
        """Fetch expressions files urls and sample metadata."""
        table_samples = []
        for sample in self.collection.samples.iterate():
            # get sample metadata from description
            metadata = sample.descriptor
            metadata["sample_slug"] = sample.slug

            # get expressions data objects
            try:
                expression = sample.get_expression()
            except LookupError:
                raise LookupError(
                    f"Sample {sample.slug} has not expression data!"
                ) from None

            # get expression files urls
            expression_files = {}
            for exp_type in EXPRESSION_TYPES:
                exp_files = expression.files(field_name=exp_type)
                assert (
                    len(exp_files) == 1
                ), "Multiple expression files with same expression type!"
                exp_file = exp_files[0]
                exp_file_url = "{}/{}".format(expression.id, exp_file)
                expression_files[exp_type] = exp_file_url

            table_samples.append(
                _TableSample(
                    sample_slug=sample.slug,
                    expression_files=expression_files,
                    metadata=metadata,
                )
            )
        return table_samples

    @lru_cache(maxsize=16)
    def expressions(
        self, preprocess: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None
    ) -> pd.DataFrame:
        """Return TPM data in a table format.

        If a data preprocess is set then its executed and its results returned and cached in memory. The preprocess
        must be a callable that expects one argument of type DataFrame and return an object of the same type.

        :param preprocess: a callable that preprocess expression data
        :return: table of TPM
        """
        cache = load_cache(self.cache_dir, self.collection.slug, TPM, self.modified)
        if cache is not None:
            self._expressions[TPM] = cache

        if TPM not in self._expressions:
            self._expressions[TPM] = self._download_expressions(TPM)

        save_cache(
            self._expressions[TPM],
            self.cache_dir,
            self.collection.slug,
            TPM,
            self.modified,
        )

        _expressions = self._expressions[TPM]
        if preprocess is not None:
            _expressions = preprocess(_expressions.copy())
        return _expressions

    @lru_cache()
    def counts(self) -> pd.DataFrame:
        """Return counts in a table format.

        :return: table of counts
        """
        cache = load_cache(self.cache_dir, self.collection.slug, COUNTS, self.modified)
        if cache is not None:
            self._expressions[COUNTS] = cache

        if COUNTS not in self._expressions:
            self._expressions[COUNTS] = self._download_expressions(COUNTS)

        save_cache(
            self._expressions[COUNTS],
            self.cache_dir,
            self.collection.slug,
            COUNTS,
            self.modified,
        )
        return self._expressions[COUNTS]

    def _gene_map(self, ensembl_ids: List[str]) -> dict:
        """Return the mapping of ensemble ids to gene symbols.

        :param ensembl_ids: list of ensemble ids
        :return: dictionary with ensemble ids as keys and gene symbol for corresponding values
        """
        if not self._gene_map_:
            self._gene_map_ = self._get_gene_map(ensembl_ids)
        return self._gene_map_

    def _get_gene_map(self, ensembl_ids: List[str]) -> dict:
        """Fetch gene mapping from resolwe server."""
        sublists = [
            ensembl_ids[i : i + CHUNK_SIZE]
            for i in range(0, len(ensembl_ids), CHUNK_SIZE)
        ]
        species = self._table_samples[0].metadata["general"]["species"]
        gene_map = {}
        for sublist in sublists:
            features = self.resolwe.feature.filter(
                species=species, feature_id__in=sublist
            )
            gene_map.update({f.feature_id: f.name for f in features})
        return gene_map

    def _gene_mapping(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform columns of the given table from ensemble ids to gene symbols."""
        genes = df.columns.tolist()
        gene_map = self._gene_map(genes)
        df.columns = df.columns.map(gene_map)
        return df

    def _download_expressions(self, exp_type: str) -> pd.DataFrame:
        """Download expression files and marge them into a pandas DataFrame.

        :param exp_type: expression type
        :return: table with expression data, genes in columns, samples in rows
        """
        df_list = []
        for ts in self._table_samples:
            full_file_url = urljoin(
                self.resolwe.url, f"data/{ts.expression_files[exp_type]}"
            )
            response = self.resolwe.session.get(full_file_url, auth=self.resolwe.auth)
            response.raise_for_status()
            with BytesIO() as f:
                f.write(response.content)
                f.seek(0)
                df_ = pd.read_csv(f, sep="\t", compression="gzip")
                df_ = df_.set_index("Gene").T
                df_.index = [ts.sample_slug]
                df_list.append(df_)

        df = pd.concat(df_list, axis=0).sort_index()
        df.index.name = "sample_slug"
        df.columns.name = None
        df = self._gene_mapping(df)
        return df
