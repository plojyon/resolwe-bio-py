import unittest
from datetime import datetime
from time import sleep, time

import pandas as pd
import pytz
from mock import MagicMock, patch
from pandas.testing import assert_frame_equal

from resdk import CollectionTables
from resdk.collection_tables import EXP, META, RC


class TestCollectionTables(unittest.TestCase):
    def setUp(self):
        self.sample = MagicMock()
        self.sample.modified = datetime(
            2020, 11, 1, 12, 15, 0, 0, tzinfo=pytz.UTC
        ).astimezone(pytz.timezone("Europe/Ljubljana"))
        self.sample.descriptor = {"PFS": 1}
        self.sample.name = "Sample123"
        self.data = MagicMock()
        self.data.id = 12345
        self.data.output.__getitem__.side_effect = {
            "species": "Homo sapiens",
            "source": "ENSEMBL",
            "exp_type": "TPM",
        }.__getitem__
        self.collection = MagicMock()
        self.collection.slug = "slug"
        self.collection.name = "Name"
        self.collection.samples.filter = self.web_request([self.sample])
        self.collection.data.filter = self.web_request([self.data])
        self.resolwe = MagicMock()
        self.resolwe.url = "https://server.com"
        self.collection.resolwe = self.resolwe
        self.metadata_df = pd.DataFrame(
            [[0], [1], [4]], index=["0", "1", "2"], columns=["PFS"]
        )
        self.expressions_df = pd.DataFrame(
            [[0, 1, 2], [1, 2, 3], [2, 3, 4]],
            index=["0", "1", "2"],
            columns=["ENSG001", "ENSG002", "ENSG003"],
        )
        self.gene_map = {"ENSG001": "GA", "ENSG002": "GB", "ENSG003": "GC"}

    @staticmethod
    def web_request(return_value):
        def slow(*args, **kwargs):
            sleep(0.1)
            return return_value

        return slow

    @patch(
        "resdk.collection_tables.cache_dir_resdk", MagicMock(return_value="/tmp/resdk/")
    )
    @patch("os.path.exists")
    def test_init(self, exists_mock):
        ct = CollectionTables(self.collection)

        self.assertIs(ct.collection, self.collection)
        self.assertEqual(ct.cache_dir, "/tmp/resdk/")
        exists_mock.assert_called_with("/tmp/resdk/")

        # using different cache dir
        ct = CollectionTables(self.collection, cache_dir="/tmp/cache_dir/")
        self.assertEqual(ct.cache_dir, "/tmp/cache_dir/")
        exists_mock.assert_called_with("/tmp/cache_dir/")

    @patch.object(CollectionTables, "_load_fetch")
    def test_meta(self, load_mock):
        load_mock.side_effect = self.web_request(self.metadata_df)

        ct = CollectionTables(self.collection)
        t = time()
        meta = ct.meta
        self.assertTrue(time() - t > 0.1)
        self.assertIs(meta, self.metadata_df)
        load_mock.assert_called_with(META)

        # use cache
        t = time()
        meta = ct.meta
        self.assertTrue(time() - t < 0.1)
        self.assertIs(meta, self.metadata_df)

    @patch.object(CollectionTables, "_load_fetch")
    def test_exp(self, load_mock):
        load_mock.side_effect = self.web_request(self.expressions_df)

        ct = CollectionTables(self.collection)
        t = time()
        exp = ct.exp
        self.assertTrue(time() - t > 0.1)
        self.assertIs(exp, self.expressions_df)
        load_mock.assert_called_with(EXP)
        self.assertListEqual(ct.gene_ids, ["ENSG001", "ENSG002", "ENSG003"])

        # use cache
        t = time()
        exp = ct.exp
        self.assertTrue(time() - t < 0.1)
        self.assertIs(exp, self.expressions_df)

    @patch.object(CollectionTables, "_load_fetch")
    def test_rc(self, load_mock):
        load_mock.side_effect = self.web_request(self.expressions_df)

        ct = CollectionTables(self.collection)
        t = time()
        rc = ct.rc
        self.assertTrue(time() - t > 0.1)
        self.assertIs(rc, self.expressions_df)
        load_mock.assert_called_with(RC)
        self.assertListEqual(ct.gene_ids, ["ENSG001", "ENSG002", "ENSG003"])

        # use cache
        t = time()
        rc = ct.rc
        self.assertTrue(time() - t < 0.1)
        self.assertIs(rc, self.expressions_df)

    @patch.object(CollectionTables, "_mapping")
    def test_id_to_symbol(self, mapping_mock):
        mapping_mock.side_effect = self.web_request(self.gene_map)

        ct = CollectionTables(self.collection)
        with self.assertRaises(ValueError):
            mapping = ct.id_to_symbol

        ct = CollectionTables(self.collection)
        ct.gene_ids = ["ENSG001", "ENSG002", "ENSG003"]
        t = time()
        mapping = ct.id_to_symbol
        self.assertTrue(time() - t > 0.1)
        mapping_mock.assert_called_with(
            ["ENSG001", "ENSG002", "ENSG003"], "ENSEMBL", "Homo sapiens"
        )
        self.assertIs(mapping, self.gene_map)

        # test if use case works
        new_exp = self.expressions_df.rename(columns=ct.id_to_symbol)
        self.assertListEqual(new_exp.columns.tolist(), ["GA", "GB", "GC"])

        # use cache
        t = time()
        mapping = ct.id_to_symbol
        self.assertTrue(time() - t < 0.1)
        self.assertIs(mapping, self.gene_map)

    @patch("resdk.collection_tables.clear_cache_dir_resdk")
    def test_clear_cache(self, clear_mock):
        CollectionTables.clear_cache()
        clear_mock.assert_called()

    def test_metadata_version(self):
        ct = CollectionTables(self.collection)
        version = ct._metadata_version
        self.assertEqual(version, "2020-11-01T12:15:00Z")

        # use cache
        t = time()
        version = ct._metadata_version
        self.assertTrue(time() - t < 0.1)

        self.collection.samples.filter = MagicMock(return_value=[])
        ct1 = CollectionTables(self.collection)
        with self.assertRaises(ValueError):
            version = ct1._metadata_version

    def test_expressions_version(self):
        ct = CollectionTables(self.collection)
        version = ct._expression_version
        self.assertEqual(version, str(hash(tuple([12345]))))

        # use cache
        t = time()
        version = ct._expression_version
        self.assertTrue(time() - t < 0.1)

        self.collection.data.filter = MagicMock(return_value=[])
        ct = CollectionTables(self.collection)
        with self.assertRaises(ValueError):
            version = ct._expression_version

    @patch(
        "resdk.collection_tables.cache_dir_resdk", MagicMock(return_value="/tmp/resdk/")
    )
    @patch("resdk.collection_tables.load_pickle")
    @patch("resdk.collection_tables.save_pickle")
    @patch.object(CollectionTables, "_download_metadata")
    @patch.object(CollectionTables, "_download_expressions")
    def test_load_fetch(self, exp_mock, mata_mock, save_mock, load_mock):
        exp_mock.return_value = self.expressions_df
        mata_mock.return_value = self.metadata_df
        load_mock.return_value = None

        ct = CollectionTables(self.collection)
        data = ct._load_fetch(META)
        self.assertIs(data, self.metadata_df)
        save_mock.assert_called_with(
            self.metadata_df, "/tmp/resdk/slug_meta_2020-11-01T12:15:00Z.pickle"
        )

        save_mock.reset_mock()
        data = ct._load_fetch(EXP)
        self.assertIs(data, self.expressions_df)
        exp_mock.assert_called_with(EXP)
        save_mock.assert_called_with(
            self.expressions_df, f"/tmp/resdk/slug_exp_{str(hash((12345,)))}.pickle"
        )

        exp_mock.reset_mock()
        save_mock.reset_mock()
        data = ct._load_fetch(RC)
        self.assertIs(data, self.expressions_df)
        exp_mock.assert_called_with(RC)
        save_mock.assert_called_with(
            self.expressions_df, f"/tmp/resdk/slug_rc_{str(hash((12345,)))}.pickle"
        )

        exp_mock.reset_mock()
        load_mock.return_value = self.expressions_df
        data = ct._load_fetch(EXP)
        self.assertIs(data, self.expressions_df)
        exp_mock.assert_not_called()

    def test_download_metadata(self):
        ct = CollectionTables(self.collection)
        meta = ct._download_metadata()
        expected_meta = pd.DataFrame([1], columns=["PFS"], index=["Sample123"])
        expected_meta.index.name = "sample_name"
        assert_frame_equal(meta, expected_meta)

    def test_expression_file_url(self):
        self.data.files.return_value = ["exp_file.csv"]

        ct = CollectionTables(self.collection)
        file_url = ct._expression_file_url(self.data, EXP)
        self.assertEqual(file_url, "https://server.com/data/12345/exp_file.csv")

        self.data.files.return_value = []
        with self.assertRaises(LookupError):
            file_url = ct._expression_file_url(self.data, EXP)

        self.data.files.return_value = ["exp_file1.csv", "exp_file2.csv"]
        with self.assertRaises(LookupError):
            file_url = ct._expression_file_url(self.data, EXP)

    @patch("resdk.collection_tables.BytesIO", MagicMock)
    @patch.object(CollectionTables, "_expression_file_url", MagicMock)
    @patch("pandas.read_csv")
    def test_download_expressions(self, pandas_mock):
        exp_df = pd.DataFrame(
            [["ENSG001", 0], ["ENSG002", 1], ["ENSG003", 2]],
            columns=["Gene", "Expression"],
        )
        pandas_mock.return_value = exp_df
        return_exp = pd.DataFrame(
            [[0, 1, 2]], columns=["ENSG001", "ENSG002", "ENSG003"], index=["Sample123"]
        )
        return_exp.index.name = "sample_name"
        return_exp.columns.name = "Ensembl"
        self.data._original_values.__getitem__.side_effect = {
            "entity": {"name": "Sample123"}
        }.__getitem__
        ct = CollectionTables(self.collection)
        exp = ct._download_expressions(EXP)
        assert_frame_equal(exp, return_exp)
        self.assertEqual(exp.attrs["exp_type"], "TPM")

    @patch(
        "resdk.collection_tables.cache_dir_resdk", MagicMock(return_value="/tmp/resdk/")
    )
    @patch("resdk.collection_tables.load_pickle")
    @patch("resdk.collection_tables.save_pickle")
    @patch.object(CollectionTables, "_download_mapping")
    def test_mapping(self, download_mock, save_mock, load_mock):
        load_mock.return_value = None
        download_mock.return_value = self.gene_map

        ct = CollectionTables(self.collection)
        mapping = ct._mapping(
            ["ENSG001", "ENSG002", "ENSG003"], "ENSEMBL", "Homo sapiens"
        )
        self.assertDictEqual(mapping, self.gene_map)
        self.assertListEqual(
            sorted(download_mock.call_args[0][0]), ["ENSG001", "ENSG002", "ENSG003"]
        )
        save_mock.assert_called_with(
            self.gene_map, "/tmp/resdk/ENSEMBL_Homo sapiens.pickle", override=True
        )

        # download only missing values
        download_mock.reset_mock()
        load_mock.return_value = {"ENSG002": "GB", "ENSG003": "GC"}
        mapping = ct._mapping(
            ["ENSG001", "ENSG002", "ENSG003"], "ENSEMBL", "Homo sapiens"
        )
        self.assertDictEqual(mapping, self.gene_map)
        self.assertListEqual(sorted(download_mock.call_args[0][0]), ["ENSG001"])

    def test_download_mapping(self):
        def create_feature(fid, name):
            m = MagicMock(feature_id=fid)
            # name can't be set on initialization
            m.name = name
            return m

        self.resolwe.feature.filter.return_value = [
            create_feature(fid, name) for fid, name in self.gene_map.items()
        ]

        ct = CollectionTables(self.collection)
        mapping = ct._download_mapping(
            ["ENSG001", "ENSG002", "ENSG003"], "ENSEMBL", "Homo sapiens"
        )

        self.resolwe.feature.filter.assert_called_once()
        self.resolwe.feature.filter.assert_called_once_with(
            source="ENSEMBL",
            species="Homo sapiens",
            feature_id__in=["ENSG001", "ENSG002", "ENSG003"],
        )
        self.assertDictEqual(mapping, self.gene_map)
