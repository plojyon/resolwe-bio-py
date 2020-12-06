import unittest

import pandas as pd
from mock import ANY, MagicMock, patch

from resdk.utils.table_cache import (
    cache_dir_resdk,
    cache_dir_resdk_base,
    clear_cache_dir_resdk,
    load_pickle,
    save_pickle,
)


class TestCache(unittest.TestCase):
    def test_cache_dir_resdk_base(self):
        for platform in ["darwin", "win32", "posix"]:
            with patch("sys.platform", platform):
                self.assertTrue(cache_dir_resdk_base().endswith("ReSDK"))

    @patch("resdk.utils.table_cache.__version__", "0.0.0.dev0+g0d51338")
    def test_cache_dir_resdk(self):
        with patch("sys.platform", "darwin"):
            self.assertTrue(
                cache_dir_resdk().endswith("Library/Caches/ReSDK/0.0.0.dev")
            )

        with patch("sys.platform", "win32"):
            self.assertTrue(
                cache_dir_resdk().endswith("AppData/Local/ReSDK/0.0.0.dev/Cache")
            )

        with patch("sys.platform", "posix"):
            self.assertTrue(cache_dir_resdk().endswith(".cache/ReSDK/0.0.0.dev"))

    @patch("resdk.utils.table_cache.cache_dir_resdk_base")
    @patch("resdk.utils.table_cache.rmtree")
    @patch("os.path.exists", MagicMock(return_value=True))
    def test_clear_cache(self, rm_mock, dir_mock):
        dir_mock.return_value = "/tmp/resdk/"
        clear_cache_dir_resdk()
        rm_mock.assert_called_with("/tmp/resdk/")

    @patch("os.path.exists")
    @patch("pickle.load")
    @patch("resdk.utils.table_cache.open", MagicMock())
    def test_load_pickle(self, pickle_mock, path_mock):
        # load existing cache file
        path_mock.return_value = True
        table_mock = MagicMock(spec=pd.DataFrame)
        pickle_mock.return_value = table_mock
        table = load_pickle("pickle_file_path.pickle")

        path_mock.assert_called_with("pickle_file_path.pickle")
        self.assertIs(table, table_mock)

        # return None for non-existing cache
        pickle_mock.reset_mock()
        path_mock.return_value = False
        table = load_pickle("pickle_file_path.pickle")
        pickle_mock.assert_not_called()
        self.assertIsNone(table)

    @patch("os.path.exists")
    @patch("pickle.dump")
    @patch("resdk.utils.table_cache.open", MagicMock())
    def test_save_pickle(self, pickle_mock, path_mock):
        # save to cache file if not non-existing
        path_mock.return_value = False
        table_mock = MagicMock(spec=pd.DataFrame)
        save_pickle(table_mock, "pickle_file_path.pickle")

        path_mock.assert_called_with("pickle_file_path.pickle")
        pickle_mock.assert_called_with(table_mock, ANY)

        pickle_mock.reset_mock()
        path_mock.return_value = True
        save_pickle(table_mock, "pickle_file_path.pickle")
        pickle_mock.assert_not_called()

        save_pickle(table_mock, "pickle_file_path.pickle", override=True)
        pickle_mock.assert_called_with(table_mock, ANY)
