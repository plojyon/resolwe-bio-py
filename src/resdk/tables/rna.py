""".. Ignore pydocstyle D400.

=========
RNATables
=========

.. autoclass:: RNATables
    :members:

    .. automethod:: __init__

"""
import os
import warnings
from functools import lru_cache
from typing import Callable, Dict, List, Optional

import pandas as pd

from resdk.resources import Collection, Data
from resdk.utils.table_cache import load_pickle, save_pickle

from .base import BaseTables
from .utils import batch_download

CHUNK_SIZE = 1000


MQC_GENERAL_COLUMNS = [
    {
        "name": "FastQC (raw)_mqc-generalstats-fastqc_raw-total_sequences",
        "slug": "total_read_count_raw",
        "type": "Int64",
        "agg_func": "sum",
    },
    {
        "name": "FastQC (trimmed)_mqc-generalstats-fastqc_trimmed-total_sequences",
        "slug": "total_read_count_trimmed",
        "type": "Int64",
        "agg_func": "sum",
    },
    {
        "name": "FastQC (raw)_mqc-generalstats-fastqc_raw-percent_gc",
        "slug": "gc_content_raw",
        "type": "float64",
        "agg_func": "mean",
    },
    {
        "name": "FastQC (trimmed)_mqc-generalstats-fastqc_trimmed-percent_gc",
        "slug": "gc_content_trimmed",
        "type": "float64",
        "agg_func": "mean",
    },
    {
        "name": "FastQC (raw)_mqc-generalstats-fastqc_raw-percent_duplicates",
        "slug": "seq_duplication_raw",
        "type": "float64",
        "agg_func": "mean",
    },
    {
        "name": "FastQC (trimmed)_mqc-generalstats-fastqc_trimmed-percent_duplicates",
        "slug": "seq_duplication_trimmed",
        "type": "float64",
        "agg_func": "mean",
    },
    {
        "name": "FastQC (raw)_mqc-generalstats-fastqc_raw-avg_sequence_length",
        "slug": "avg_seq_length_raw",
        "type": "float64",
        "agg_func": "mean",
    },
    {
        "name": "FastQC (trimmed)_mqc-generalstats-fastqc_trimmed-avg_sequence_length",
        "slug": "avg_seq_length_trimmed",
        "type": "float64",
        "agg_func": "mean",
    },
    {
        "name": "STAR_mqc-generalstats-star-uniquely_mapped_percent",
        "slug": "mapped_reads_percent",
        "type": "float64",
        "agg_func": "mean",
    },
    {
        "name": "STAR_mqc-generalstats-star-uniquely_mapped",
        "slug": "mapped_reads",
        "type": "Int64",
        "agg_func": "sum",
    },
    {
        "name": "STAR (Globin)_mqc-generalstats-star_globin-uniquely_mapped_percent",
        "slug": "mapped_reads_percent_globin",
        "type": "float64",
        "agg_func": "mean",
    },
    {
        "name": "STAR (Globin)_mqc-generalstats-star_globin-uniquely_mapped",
        "slug": "mapped_reads_globin",
        "type": "Int64",
        "agg_func": "sum",
    },
    {
        "name": "STAR (rRNA)_mqc-generalstats-star_rrna-uniquely_mapped_percent",
        "slug": "mapped_reads_percent_rRNA",
        "type": "float64",
        "agg_func": "mean",
    },
    {
        "name": "STAR (rRNA)_mqc-generalstats-star_rrna-uniquely_mapped",
        "slug": "mapped_reads_rRNA",
        "type": "Int64",
        "agg_func": "sum",
    },
    {
        "name": "featureCounts_mqc-generalstats-featurecounts-percent_assigned",
        "slug": "fc_assigned_reads_percent",
        "type": "float64",
        "agg_func": "mean",
    },
    {
        "name": "featureCounts_mqc-generalstats-featurecounts-Assigned",
        "slug": "fc_assigned_reads",
        "type": "Int64",
        "agg_func": "sum",
    },
    {
        "name": "Salmon_mqc-generalstats-salmon-percent_mapped",
        "slug": "salmon_assigned_reads_percent",
        "type": "float64",
        "agg_func": "mean",
    },
    {
        "name": "Salmon_mqc-generalstats-salmon-num_mapped",
        "slug": "salmon_assigned_reads",
        "type": "Int64",
        "agg_func": "sum",
    },
    {
        "name": "QoRTs_mqc-generalstats-qorts-Genes_PercentWithNonzeroCounts",
        "slug": "nonzero_count_features_percent",
        "type": "float64",
        "agg_func": "mean",
    },
    {
        "name": "QoRTs_mqc-generalstats-qorts-NumberOfChromosomesCovered",
        "slug": "contigs_covered",
        "type": "Int64",
        "agg_func": "mean",
    },
    {
        "slug": "strandedness_code",
        "type": "string",
    },
    {
        "slug": "genome_build",
        "type": "string",
    },
]


def multiqc_general_stats_parser(file_object, name):
    """Parse "multiqc_general_stats.txt" file."""
    df = pd.read_csv(file_object, sep="\t", index_col=0)

    # Keep only specified columns:
    df = df[
        [
            column.get("name", "")
            for column in MQC_GENERAL_COLUMNS
            if column.get("name", "") in df.columns
        ]
    ]
    # Rename
    df = df.rename(
        columns={
            column.get("name", ""): column["slug"]
            for column in MQC_GENERAL_COLUMNS
            if column.get("name", "") in df.columns
        }
    )

    # Perform aggregation
    series = df.agg(
        {
            column["slug"]: column["agg_func"]
            for column in MQC_GENERAL_COLUMNS
            if column["slug"] in df.columns
        }
    )
    series.name = name
    return series


def multiqc_strand_parser(file_object, name):
    """Parse "multiqc_library_strandedness.txt" file."""
    df = pd.read_csv(file_object, sep="\t", index_col=0)
    return pd.Series(
        df["Strandedness code"].iloc[0],
        index=["strandedness_code"],
        name=name,
    )


def multiqc_build_parser(file_object, name):
    """Parse "multiqc_sample_info.txt" file."""
    df = pd.read_csv(file_object, sep="\t", index_col=0)
    return pd.Series(
        df["Genome Build"].iloc[0],
        index=["genome_build"],
        name=name,
    )


class RNATables(BaseTables):
    """A helper class to fetch collection's expression and meta data.

    This class enables fetching given collection's data and returning it
    as tables which have samples in rows and expressions/metadata in
    columns.

    When calling :attr:`RNATables.exp`,
    :attr:`RNATables.rc` and :attr:`RNATables.meta`
    for the first time the corresponding data gets downloaded from the
    server. This data than gets cached in memory and on disc and is used
    in consequent calls. If the data on the server changes the updated
    version gets re-downloaded.

    A simple example:

    .. code-block:: python

        # Get Collection object
        collection = res.collection.get("collection-slug")

        # Fetch collection expressions and metadata
        tables = RNATables(collection)
        exp = tables.exp
        rc = tables.rc
        meta = tables.meta

    """

    process_type = "data:expression:"
    EXP = "exp"
    RC = "rc"
    data_type_to_field_name = {
        EXP: "exp",
        RC: "rc",
    }

    def __init__(
        self,
        collection: Collection,
        cache_dir: Optional[str] = None,
        progress_callable: Optional[Callable] = None,
        expression_source: Optional[str] = None,
        expression_process_slug: Optional[str] = None,
    ):
        """Initialize class.

        :param collection: collection to use
        :param cache_dir: cache directory location, if not specified system specific
                          cache directory is used
        :param progress_callable: custom callable that can be used to report
                                  progress. By default, progress is written to
                                  stderr with tqdm
        :param expression_source: Only consider samples in the
                                  collection with specified source
        :param expression_process_slug: Only consider samples in the
                                        collection with specified
                                        process slug
        """
        super().__init__(collection, cache_dir, progress_callable)

        self.expression_source = expression_source
        self.expression_process_slug = expression_process_slug

        self.check_heterogeneous_collections()

        self.gene_ids = []  # type: List[str]

    def check_heterogeneous_collections(self):
        """Ensure consistency among expressions."""
        message = ""

        process_slugs = sorted({d.process.slug for d in self._data})
        if len(process_slugs) > 1:
            message += (
                "Expressions of all samples must be computed with the "
                "same process. Expressions of samples in collection "
                f"{self.collection.name} have been computed with "
                f"{', '.join(process_slugs)}.\n"
                "Use expression_process_slug filter in the "
                "RNATable constructor.\n"
            )

        exp_sources = {d.output["source"] for d in self._data}
        if len(exp_sources) > 1:
            message += (
                "Alignment of all samples must be computed with the "
                "same genome source. Alignments of samples in "
                f"collection {self.collection.name} have been computed "
                f"with {', '.join(exp_sources)}.\n"
                "Use expression_source filter in the RNATable "
                "constructor.\n"
            )

        if message:
            raise ValueError(message)

    @property
    @lru_cache()
    def exp(self) -> pd.DataFrame:
        """Return expressions table as a pandas DataFrame object.

        Which type of expressions (TPM, CPM, FPKM, ...) get returned
        depends on how the data was processed. The expression type can
        be checked in the returned table attribute `attrs['exp_type']`:

        .. code-block:: python

            exp = tables.exp
            print(exp.attrs['exp_type'])

        :return: table of expressions
        """
        exp = self._load_fetch(self.EXP)
        self.gene_ids = exp.columns.tolist()
        return exp

    @property
    @lru_cache()
    def rc(self) -> pd.DataFrame:
        """Return expression counts table as a pandas DataFrame object.

        :return: table of counts
        """
        rc = self._load_fetch(self.RC)
        self.gene_ids = rc.columns.tolist()
        return rc

    @property
    @lru_cache()
    def readable_columns(self) -> Dict[str, str]:
        """Map of source gene ids to symbols.

        This also gets fetched only once and then cached in memory and
        on disc. :attr:`RNATables.exp` or
        :attr:`RNATables.rc` must be called before this as the
        mapping is specific to just this data. Its intended use is to
        rename table column labels from gene ids to symbols.

        Example of use:

        .. code-block:: python

            exp = exp.rename(columns=tables.id_to_symbol)

        :return: dict with gene ids as keys and gene symbols as values
        """
        species = self._data[0].output["species"]
        source = self._data[0].output["source"]

        if not self.gene_ids:
            raise ValueError("Expression data must be used before!")

        return self._mapping(self.gene_ids, source, species)

    @property
    @lru_cache()
    def id_to_symbol(self) -> Dict[str, str]:
        """Map of source gene ids to symbols."""
        warnings.warn(
            "Attribute `id_to_symbol` will be removed in Q1 of 2022. "
            "Use `readable_columns` instead.",
            DeprecationWarning,
        )
        return self.readable_columns

    @property
    @lru_cache()
    def _data(self) -> List[Data]:
        """Fetch data objects.

        Fetch expression data objects from given collection and cache
        the results in memory. If ``expression_source``  /
        ``expression_process_slug`` is provided also filter for that.
        Only the needed subset of fields is fetched.

        :return: list of Data objects
        """
        data = super()._data

        if self.expression_process_slug:
            data = [d for d in data if d.process.slug == self.expression_process_slug]
        if self.expression_source:
            data = [d for d in data if d.output["source"] == self.expression_source]

        return data

    def _cache_file(self, data_type: str) -> str:
        """Return full cache file path."""
        if data_type == self.META:
            version = self._metadata_version
        elif data_type == self.QC:
            version = self._qc_version
        else:
            version = self._data_version

        cache_file = f"{self.collection.slug}_{data_type}_{self.expression_source}_{self.expression_process_slug}_{version}.pickle"
        return os.path.join(self.cache_dir, cache_file)

    def _download_qc(self) -> pd.DataFrame:
        """Download sample QC data and transform into table.

        QC info can be sourced from multiple files and multiple columns
        in those files.
        """
        mqc_db = {}
        for mqc in self.collection.data.filter(
            type="data:multiqc",
            status="OK",
            ordering="created",
            entity__isnull=False,
            fields=["id", "entity__id"],
        ):
            if mqc.sample.id in mqc_db:
                warnings.warn(
                    f"Sample with ID={mqc.sample.id} has multiple MultiQC Data. "
                    "Using the latest one.",
                    UserWarning,
                )
            mqc_db[mqc.sample.id] = {
                "mqc_id": mqc.id,
                "uri_general": f"{mqc.id}/multiqc_data/multiqc_general_stats.txt",
                "uri_strand": f"{mqc.id}/multiqc_data/multiqc_library_strandedness.txt",
                "uri_build": f"{mqc.id}/multiqc_data/multiqc_sample_info.txt",
            }

        df = pd.DataFrame(index=[sample.id for sample in self._samples])

        parsers = {
            "uri_general": multiqc_general_stats_parser,
            "uri_strand": multiqc_strand_parser,
            "uri_build": multiqc_build_parser,
        }
        for type_, parser in parsers.items():
            uris = [item[type_] for item in mqc_db.values()]
            qc = batch_download(self.resolwe, uris, parser)
            qc = qc.rename(index={value[type_]: key for key, value in mqc_db.items()})
            df = df.merge(qc, how="left", left_index=True, right_index=True)

        # Cast to correct dtype
        column_types = {
            c["slug"]: c["type"] for c in MQC_GENERAL_COLUMNS if c["slug"] in df.columns
        }
        df = df[column_types.keys()].astype(column_types)

        return df

    def _parse_file(self, file_obj, sample_id, data_type):
        """Parse file object and return a one DataFrame line."""
        sample_data = pd.read_csv(file_obj, sep="\t", compression="gzip")
        sample_data = sample_data.set_index("Gene")["Expression"]
        sample_data.name = sample_id
        return sample_data

    async def _download_data(self, data_type: str) -> pd.DataFrame:
        df = await super()._download_data(data_type)
        source = self._data[0].output["source"]
        df.columns.name = source.capitalize() if source == "ENSEMBL" else source
        df.attrs["exp_type"] = (
            "rc" if data_type == self.RC else self._data[0].output["exp_type"]
        )
        return df

    def _mapping(self, ids: List[str], source: str, species: str) -> Dict[str, str]:
        """Fetch and cache gene mapping."""
        mapping_cache = os.path.join(self.cache_dir, f"{source}_{species}.pickle")
        mapping = load_pickle(mapping_cache)
        if mapping is None:
            mapping = {}

        # download only the genes that are not in cache
        diff = list(set(ids) - set(mapping.keys()))
        if diff:
            diff_mapping = self._download_mapping(diff, source, species)
            mapping.update(diff_mapping)
            save_pickle(mapping, mapping_cache, override=True)
        return mapping

    def _download_mapping(
        self, ids: List[str], source: str, species: str
    ) -> Dict[str, str]:
        """Download gene mapping."""
        sublists = [ids[i : i + CHUNK_SIZE] for i in range(0, len(ids), CHUNK_SIZE)]
        mapping = {}
        for sublist in self.tqdm(
            sublists,
            desc="Downloading gene mapping",
            ncols=100,
            file=open(os.devnull, "w") if self.progress_callable else None,
            callable=self.progress_callable,
        ):
            features = self.resolwe.feature.filter(
                source=source, species=species, feature_id__in=sublist
            )
            mapping.update({f.feature_id: f.name for f in features})
        return mapping
