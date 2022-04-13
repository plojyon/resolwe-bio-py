""".. Ignore pydocstyle D400.

=================
MethylationTables
=================

.. autoclass:: MethylationTables
    :members:

    .. automethod:: __init__

"""
from functools import lru_cache
from typing import Callable, List, Optional

import pandas as pd

from resdk.resources import Collection

from .base import BaseTables

CHUNK_SIZE = 1000


class MethylationTables(BaseTables):
    """A helper class to fetch collection's methylation and meta data.

    This class enables fetching given collection's data and returning it
    as tables which have samples in rows and methylation/metadata in
    columns.

    A simple example:

    .. code-block:: python

        # Get Collection object
        collection = res.collection.get("collection-slug")

        # Fetch collection methylation and metadata
        tables = MethylationTables(collection)
        meta = tables.meta
        beta = tables.beta
        m_values = tables.mval

    """

    process_type = "data:methylation:"
    BETA = "betas"
    MVAL = "mvals"

    data_type_to_field_name = {
        BETA: "methylation_data",
        MVAL: "methylation_data",
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
    def beta(self) -> pd.DataFrame:
        """Return beta values table as a pandas DataFrame object."""
        beta = self._load_fetch(self.BETA)
        self.probe_ids = beta.columns.tolist()
        return beta

    @property
    @lru_cache()
    def mval(self) -> pd.DataFrame:
        """Return m-values as a pandas DataFrame object."""
        mval = self._load_fetch(self.MVAL)
        self.probe_ids = mval.columns.tolist()
        return mval

    def _download_qc(self) -> pd.DataFrame:
        """Download sample QC data and transform into table."""
        return pd.DataFrame()

    def _parse_file(self, file_obj, sample_id, data_type):
        """Parse file object and return one DataFrame line."""
        sample_data = pd.read_csv(
            file_obj,
            sep="\t",
            compression="gzip",
            usecols=["probe_ids", data_type],
            index_col="probe_ids",
        )[data_type]
        sample_data.name = sample_id
        return sample_data
