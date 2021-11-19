""".. Ignore pydocstyle D400.

========
MATables
========

.. autoclass:: MATables
    :members:

    .. automethod:: __init__

"""
import os
from functools import lru_cache
from typing import Callable, List, Optional

import pandas as pd

from resdk.resources import Collection

from .base import BaseTables

CHUNK_SIZE = 1000


class MATables(BaseTables):
    """A helper class to fetch collection's microarray, qc and meta data.

    This class enables fetching given collection's data and returning it
    as tables which have samples in rows and microarray / qc / metadata
    in columns.

    A simple example:

    .. code-block:: python

        # Get Collection object
        collection = res.collection.get("collection-slug")

        # Fetch collection microarray and metadata
        tables = MATables(collection)
        meta = tables.meta
        exp = tables.exp

    """

    process_type = "data:microarray:normalized"
    EXP = "ma"
    QC = "qc"

    data_type_to_field_name = {
        EXP: "exp",
    }

    def __init__(
        self,
        collection: Collection,
        cache_dir: Optional[str] = None,
        progress_callable: Optional[Callable] = None,
    ):
        """Initialize class.

        :param collection: collection to use
        :param cache_dir: cache directory location, if not specified system specific
                          cache directory is used
        :param progress_callable: custom callable that can be used to report
                                  progress. By default, progress is written to
                                  stderr with tqdm
        """
        super().__init__(collection, cache_dir, progress_callable)

        self.probe_ids = []  # type: List[str]

    @property
    @lru_cache()
    def exp(self) -> pd.DataFrame:
        """Return expressions values table as a pandas DataFrame object."""
        exp = self._load_fetch(self.EXP)
        self.probe_ids = exp.columns.tolist()
        return exp

    def _cache_file(self, data_type: str) -> str:
        """Return full cache file path."""
        if data_type == self.META:
            version = self._metadata_version
        elif data_type == self.QC:
            version = self._qc_version
        else:
            version = self._data_version

        cache_file = f"{self.collection.slug}_{data_type}_{version}.pickle"
        return os.path.join(self.cache_dir, cache_file)

    def _download_qc(self) -> pd.DataFrame:
        """Download sample QC data and transform into table."""
        return pd.DataFrame()

    def _parse_file(self, file_obj, sample_id, data_type):
        """Parse file object and return one DataFrame line."""
        sample_data = pd.read_csv(
            file_obj,
            sep="\t",
            compression="gzip",
            usecols=["ID_REF", "VALUE"],
            index_col="ID_REF",
        )["VALUE"]
        sample_data.name = sample_id
        return sample_data

    async def _download_data(self, data_type: str) -> pd.DataFrame:
        df = await super()._download_data(data_type)
        df.attrs["exp_type"] = self._data[0].output.get("exp_type", "")
        df.attrs["platform"] = self._data[0].output.get("platform", "")
        df.attrs["platform_id"] = self._data[0].output.get("platform_id", "")
        return df
