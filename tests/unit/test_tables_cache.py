import unittest
from datetime import datetime

import pandas as pd
import pytz
from mock import MagicMock, patch

from resdk.utils.table_cache import (
    _full_cache_file,
    default_cache_dir,
    load_cache,
    save_cache,
)


class TestCache(unittest.TestCase):
    @patch("resdk.utils.table_cache.__version__", "0.0.0")
    def test_default_cache_dir(self):
        with patch("sys.platform", "darwin"):
            self.assertTrue(default_cache_dir().endswith("Library/Caches/ReSDK/0.0.0"))

        with patch("sys.platform", "win32"):
            self.assertTrue(
                default_cache_dir().endswith("AppData/Local/ReSDK/0.0.0/Cache")
            )

        with patch("sys.platform", "posix"):
            self.assertTrue(default_cache_dir().endswith(".cache/ReSDK/0.0.0"))

    def test_full_cache_file(self):
        dt = datetime(2020, 11, 1, 12, 15, 30, 123456, pytz.UTC)
        path = _full_cache_file("/tmp/", "coll_slug", "dtype", dt)
        self.assertEqual(
            path, "/tmp/coll_slug_dtype_2020-11-01T12:15:30.123456+00:00.pickle"
        )

    @patch("os.path.exists")
    @patch("pandas.read_pickle")
    def test_load_cache(self, read_mock, path_mock):
        # load existing cache file
        path_mock.return_value = True
        table_mock = MagicMock(spec=pd.DataFrame)
        read_mock.return_value = table_mock
        table = load_cache(
            "/tmp/", "coll_slug", "dtype", datetime(2020, 11, 1, 12, 0, 0, 0, pytz.UTC)
        )

        path_mock.assert_called_with(
            "/tmp/coll_slug_dtype_2020-11-01T12:00:00+00:00.pickle"
        )
        read_mock.assert_called_with(
            "/tmp/coll_slug_dtype_2020-11-01T12:00:00+00:00.pickle"
        )
        self.assertIs(table, table_mock)

        # return None for non-existing cache
        read_mock.reset_mock()
        path_mock.return_value = False
        table = load_cache(
            "/tmp/", "coll_slug", "dtype", datetime(2020, 11, 1, 12, 0, 0, 0, pytz.UTC)
        )
        read_mock.assert_not_called()
        self.assertIsNone(table)

    @patch("os.path.exists")
    def test_save_cache(self, path_mock):
        # save to cache file if not non-existing
        path_mock.return_value = False
        table_mock = MagicMock(spec=pd.DataFrame)
        to_mock = table_mock.to_pickle
        save_cache(
            table_mock,
            "/tmp/",
            "coll_slug",
            "dtype",
            datetime(2020, 11, 1, 12, 0, 0, 0, pytz.UTC),
        )

        path_mock.assert_called_with(
            "/tmp/coll_slug_dtype_2020-11-01T12:00:00+00:00.pickle"
        )
        to_mock.assert_called_with(
            "/tmp/coll_slug_dtype_2020-11-01T12:00:00+00:00.pickle"
        )

        # don't save if cache file exists
        to_mock.reset_mock()
        path_mock.return_value = True
        save_cache(
            table_mock,
            "/tmp/",
            "coll_slug",
            "dtype",
            datetime(2020, 11, 1, 12, 0, 0, 0, pytz.UTC),
        )

        to_mock.assert_not_called()
