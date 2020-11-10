"""Cache util functions for CollectionTables."""
import os
import sys
from datetime import datetime
from typing import Optional

import pandas as pd

from resdk.__about__ import __version__


def default_cache_dir() -> str:
    """Return default cache directory specific for the current OS. Code from Orange3.misc.environ."""
    if sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Caches")
    elif sys.platform == "win32":
        base = os.getenv("APPDATA", os.path.expanduser("~/AppData/Local"))
    elif os.name == "posix":
        base = os.getenv("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
    else:
        base = os.path.expanduser("~/.cache")

    base = os.path.join(base, "ReSDK", __version__)
    if sys.platform == "win32":
        # On Windows cache and data dir are the same.
        # Microsoft suggest using a Cache subdirectory
        return os.path.join(base, "Cache")
    else:
        return base


def load_cache(
    directory: str, collection_slug: str, data_type: str, modified: datetime
) -> Optional[pd.DataFrame]:
    """If there is a cached file for the same data return it."""
    full_cache_file = _full_cache_file(directory, collection_slug, data_type, modified)
    if os.path.exists(full_cache_file):
        return pd.read_pickle(full_cache_file)


def save_cache(
    df: pd.DataFrame,
    directory: str,
    collection_slug: str,
    data_type: str,
    modified: datetime,
):
    """If not existing, save data to cache file."""
    full_cache_file = _full_cache_file(directory, collection_slug, data_type, modified)
    if not os.path.exists(full_cache_file):
        df.to_pickle(full_cache_file)


def _full_cache_file(
    directory: str, collection_slug: str, data_type: str, modified: datetime
) -> str:
    """Return full path to specified cache file."""
    datetime_str = modified.isoformat()
    cache_file = f"{collection_slug}_{data_type}_{datetime_str}.pickle"
    return os.path.join(directory, cache_file)
