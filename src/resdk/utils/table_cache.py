"""Cache util functions for CollectionTables."""
import os
import pickle
import sys
from shutil import rmtree
from typing import Any

from resdk.__about__ import __version__


def _default_cache_dir() -> str:
    """Return default cache directory specific for the current OS.

    Code originally from Orange3.misc.environ.
    """
    if sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Caches")
    elif sys.platform == "win32":
        base = os.getenv("APPDATA", os.path.expanduser("~/AppData/Local"))
    elif os.name == "posix":
        base = os.getenv("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
    else:
        base = os.path.expanduser("~/.cache")
    return base


def cache_dir_resdk_base() -> str:
    """Return base ReSDK cache directory."""
    return os.path.join(_default_cache_dir(), "ReSDK")


def cache_dir_resdk() -> str:
    """Return ReSDK cache directory."""
    v = __version__
    if "dev" in v:
        # remove git commit hash
        v = v[: v.find("dev") + 3]
    base = os.path.join(cache_dir_resdk_base(), v)

    if sys.platform == "win32":
        # On Windows cache and data dir are the same.
        # Microsoft suggest using a Cache subdirectory
        return os.path.join(base, "Cache")
    else:
        return base


def clear_cache_dir_resdk() -> None:
    """Delete all cache files from the default cache directory."""
    cache_dir = cache_dir_resdk_base()
    if os.path.exists(cache_dir):
        rmtree(cache_dir)


def load_pickle(pickle_file: str) -> Any:
    """Load object from the pickle file.

    :param pickle_file: file path
    :return: un-pickled object
    """
    if os.path.exists(pickle_file):
        return pickle.load(open(pickle_file, "rb"))


def save_pickle(obj: Any, pickle_file: str, override=False) -> None:
    """Save given object into a pickle file.

    :param obj: object to bi pickled
    :param pickle_file: file path
    :param override: if True than override existing file
    :return:
    """
    if not os.path.exists(pickle_file) or override:
        pickle.dump(obj, open(pickle_file, "wb"))
