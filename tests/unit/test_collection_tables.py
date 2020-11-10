import unittest
from datetime import datetime, timedelta

import pandas as pd
import pytz
from mock import ANY, MagicMock, PropertyMock, call, patch
from pandas.testing import assert_frame_equal

from resdk.collection_tables import COUNTS, META, TPM, CollectionTables, _TableSample
from resdk.resolwe import Resolwe
from resdk.resources import Collection, Data, Sample
from resdk.resources.kb import Feature


class TestCollectionTables(unittest.TestCase):
    def setUp(self):
        self.sample = MagicMock(spec=Sample)
        self.collection = MagicMock(spec=Collection)
        self.collection.slug = "slug"
        self.collection.name = "Name"
        self.collection.samples.count.return_value = 1
        self.collection.samples.iterate.return_value = [self.sample]
        self.resolwe = MagicMock(spec=Resolwe)
        self.collection.resolwe = self.resolwe
        self.table_samples = [
            MagicMock(
                spec=_TableSample,
                sample_slug=str(i),
                expression_files={TPM: f"{i}/tpm.csv", COUNTS: f"{i}/counts.csv"},
                metadata={"sample_slug": str(i), "PFS": i ** 2},
            )
            for i in range(3)
        ]
        self.metadata_df = pd.DataFrame(
            [[0], [1], [4]], index=["0", "1", "2"], columns=["PFS"]
        )
        self.metadata_df.index.name = "sample_slug"
        self.expressions_df = pd.DataFrame(
            [[0, 1, 2], [1, 2, 3], [2, 3, 4]],
            index=["0", "1", "2"],
            columns=["GA", "GB", "GC"],
        )
        self.expressions_df.index.name = "sample_slug"
        self.ensembl_ids = ["ENSG001", "ENSG002", "ENSG003"]
        self.gene_map = {"ENSG001": "GA", "ENSG002": "GB", "ENSG003": "GC"}

    @patch("resdk.collection_tables.default_cache_dir")
    @patch("os.path.exists")
    def test_init(self, exists_mock, cache_mock):
        cache_mock.return_value = "/tmp/resdk/"
        ct = CollectionTables(self.collection)

        self.assertIs(ct.collection, self.collection)
        self.assertEqual(ct.cache_dir, "/tmp/resdk/")
        exists_mock.assert_called_with("/tmp/resdk/")

        # using different cache dir
        ct = CollectionTables(self.collection, cache_dir="/tmp/cache_dir/")
        self.assertEqual(ct.cache_dir, "/tmp/cache_dir/")
        exists_mock.assert_called_with("/tmp/cache_dir/")

        # using collection with no samples should rise error
        self.collection.samples.count.return_value = 0
        with self.assertRaises(ValueError):
            CollectionTables(self.collection)

    def test_modified(self):
        sample_datetime = datetime(2020, 11, 1, 12, 15, 0, 0, tzinfo=pytz.UTC)
        self.sample.modified = sample_datetime

        ct = CollectionTables(self.collection)
        self.assertEqual(ct.modified, sample_datetime)

        # check if the newest
        self.collection.samples.iterate.return_value = [
            MagicMock(spec=Sample, modified=sample_datetime + timedelta(minutes=5 * i))
            for i in range(3)
        ]
        ct = CollectionTables(self.collection)
        self.assertEqual(
            ct.modified, datetime(2020, 11, 1, 12, 25, 0, 0, tzinfo=pytz.UTC)
        )

        # datetime should transform into UTC
        self.collection.samples.iterate.return_value = [
            MagicMock(
                spec=Sample,
                modified=sample_datetime.astimezone(pytz.timezone("Europe/Ljubljana")),
            )
        ]
        ct = CollectionTables(self.collection)
        self.assertEqual(ct.modified, sample_datetime)

        # modified should be calculated only once
        self.collection.samples.iterate.reset_mock()
        ct = CollectionTables(self.collection)
        _ = ct.modified
        self.collection.samples.iterate.assert_called_once()
        _ = ct.modified
        self.collection.samples.iterate.assert_called_once()

    @patch("resdk.collection_tables.load_cache")
    @patch("resdk.collection_tables.save_cache")
    @patch.object(CollectionTables, "_get_metadata")
    def test_metadata(self, get_mock, save_mock, load_mock):
        get_mock.return_value = self.metadata_df
        load_mock.return_value = None

        ct = CollectionTables(self.collection)
        return_meta = ct.metadata()

        load_mock.assert_called_once()
        load_mock.assert_called_once_with(ANY, ANY, META, ANY)
        get_mock.assert_called_once()
        save_mock.assert_called_once()
        save_mock.assert_called_once_with(self.metadata_df, ANY, ANY, META, ANY)
        self.assertIs(return_meta, self.metadata_df)

        # test cache behavior
        load_mock.reset_mock()
        load_mock.return_value = self.metadata_df
        get_mock.reset_mock()

        ct = CollectionTables(self.collection)
        return_meta = ct.metadata()
        # if on disk don't fetch from web
        load_mock.assert_called_once()
        get_mock.assert_not_called()
        self.assertIs(return_meta, self.metadata_df)

        load_mock.reset_mock()
        return_meta = ct.metadata()
        # if in memory don't load from disk
        load_mock.assert_not_called()
        get_mock.assert_not_called()
        self.assertIs(return_meta, self.metadata_df)

    @patch.object(CollectionTables, "_table_samples", new_callable=PropertyMock)
    def test_get_metadata(self, samples_mock):
        samples_mock.return_value = self.table_samples
        ct = CollectionTables(self.collection)
        metadata = ct._get_metadata()
        assert_frame_equal(metadata, self.metadata_df)

    @patch.object(CollectionTables, "_get_table_samples")
    def test_table_samples(self, get_mock):
        get_mock.return_value = self.table_samples

        ct = CollectionTables(self.collection)
        return_samples = ct._table_samples
        get_mock.assert_called_once()
        self.assertListEqual(return_samples, self.table_samples)

        # fetch table samples only once
        return_samples = ct._table_samples
        get_mock.assert_called_once()
        self.assertListEqual(return_samples, self.table_samples)

    def test_get_table_samples(self):
        def files(field_name=None):
            if field_name == TPM:
                return ["tpm.csv"]
            elif field_name == COUNTS:
                return ["counts.csv"]
            else:
                raise Exception

        files_mock = MagicMock(side_effect=files)
        expression_mock = MagicMock(spec=Data, id=123, files=files_mock)
        self.sample.get_expression.return_value = expression_mock
        self.sample.descriptor = {"PFS": 42}
        self.sample.slug = "sample_42"

        ct = CollectionTables(self.collection)
        table_samples = ct._get_table_samples()
        self.assertEqual(len(table_samples), 1)
        self.assertIsInstance(table_samples[0], _TableSample)
        self.assertEqual(
            table_samples[0].metadata, {"sample_slug": "sample_42", "PFS": 42}
        )
        self.assertEqual(table_samples[0].sample_slug, "sample_42")
        self.assertEqual(table_samples[0].expression_files[TPM], "123/tpm.csv")
        self.assertEqual(table_samples[0].expression_files[COUNTS], "123/counts.csv")

        # raise exception on sample with no expression data
        self.sample.get_expression = MagicMock(side_effect=LookupError)
        ct = CollectionTables(self.collection)
        with self.assertRaisesRegex(LookupError, "Sample sample_42 *"):
            ct._get_table_samples()

        # check for multiple expression files
        self.sample.get_expression = MagicMock(spec=Data)
        self.sample.get_expression.return_value.files.return_value = [1, 2, 3]
        ct = CollectionTables(self.collection)
        with self.assertRaisesRegex(AssertionError, "Multiple expression files *"):
            ct._get_table_samples()

    @patch("resdk.collection_tables.load_cache")
    @patch("resdk.collection_tables.save_cache")
    @patch.object(CollectionTables, "_download_expressions")
    def test_expressions(self, download_mock, save_mock, load_mock):
        download_mock.return_value = self.expressions_df
        load_mock.return_value = None

        ct = CollectionTables(self.collection)
        return_expression = ct.expressions()

        load_mock.assert_called_once()
        load_mock.assert_called_once_with(ANY, ANY, TPM, ANY)
        download_mock.assert_called_once()
        save_mock.assert_called_once()
        save_mock.assert_called_once_with(self.expressions_df, ANY, ANY, TPM, ANY)
        self.assertIs(return_expression, self.expressions_df)

        # if on disk don't fetch from web
        load_mock.reset_mock()
        load_mock.return_value = self.expressions_df
        download_mock.reset_mock()

        ct = CollectionTables(self.collection)
        return_expression = ct.expressions()

        load_mock.assert_called_once()
        download_mock.assert_not_called()
        self.assertIs(return_expression, self.expressions_df)

        # use preprocessor
        preprocessor_mock = MagicMock(side_effect=lambda x: x + 1)
        ct = CollectionTables(self.collection)
        return_expression = ct.expressions(preprocess=preprocessor_mock)
        preprocessor_mock.assert_called_once()
        assert_frame_equal(return_expression, preprocessor_mock(self.expressions_df))

        # cache in memory
        load_mock.reset_mock()
        preprocessor_mock.reset_mock()
        return_cache_expression = ct.expressions(preprocess=preprocessor_mock)
        load_mock.assert_not_called()
        preprocessor_mock.assert_not_called()
        download_mock.assert_not_called()
        self.assertIs(return_cache_expression, return_expression)

    @patch("resdk.collection_tables.load_cache")
    @patch("resdk.collection_tables.save_cache")
    @patch.object(CollectionTables, "_download_expressions")
    def test_counts(self, download_mock, save_mock, load_mock):
        download_mock.return_value = self.expressions_df
        load_mock.return_value = None

        ct = CollectionTables(self.collection)
        return_counts = ct.counts()

        load_mock.assert_called_once()
        load_mock.assert_called_once_with(ANY, ANY, COUNTS, ANY)
        download_mock.assert_called_once()
        save_mock.assert_called_once()
        save_mock.assert_called_once_with(self.expressions_df, ANY, ANY, COUNTS, ANY)
        self.assertIs(return_counts, self.expressions_df)

        # test cache behavior
        load_mock.reset_mock()
        load_mock.return_value = self.metadata_df
        download_mock.reset_mock()

        ct = CollectionTables(self.collection)
        return_counts = ct.counts()
        # if on disk don't fetch from web
        load_mock.assert_called_once()
        download_mock.assert_not_called()
        self.assertIs(return_counts, self.metadata_df)

        load_mock.reset_mock()
        return_counts = ct.counts()
        # if in memory don't load from disk
        load_mock.assert_not_called()
        download_mock.assert_not_called()
        self.assertIs(return_counts, self.metadata_df)

    @patch.object(CollectionTables, "_get_gene_map")
    def test_gene_map(self, get_mock):
        get_mock.return_value = self.gene_map

        ct = CollectionTables(self.collection)
        return_map = ct._gene_map(self.ensembl_ids)
        get_mock.assert_called_once()
        get_mock.assert_called_once_with(self.ensembl_ids)
        self.assertDictEqual(return_map, self.gene_map)

        # fetch gene map only once
        return_map = ct._gene_map(self.ensembl_ids)
        get_mock.assert_called_once()
        self.assertDictEqual(return_map, self.gene_map)

    @patch.object(CollectionTables, "_table_samples")
    def test_get_gene_map(self, sample_mock):
        def create_feature(fid, name):
            m = MagicMock(spec=Feature, feature_id=fid)
            # name can't be set on initialization
            m.name = name
            return m

        sample_mock.__getitem__().metadata = {"general": {"species": "Homo sapiens"}}
        self.resolwe.feature.filter.return_value = [
            create_feature(fid, name) for fid, name in self.gene_map.items()
        ]

        ct = CollectionTables(self.collection)
        return_map = ct._get_gene_map(self.ensembl_ids)

        self.resolwe.feature.filter.assert_called_once()
        self.resolwe.feature.filter.assert_called_once_with(
            species="Homo sapiens", feature_id__in=self.ensembl_ids
        )
        self.assertDictEqual(return_map, self.gene_map)

    @patch.object(CollectionTables, "_gene_map")
    def test_gene_mapping(self, map_mock):
        map_mock.return_value = self.gene_map
        pre_map_df = self.expressions_df.copy()
        pre_map_df.columns = self.ensembl_ids

        ct = CollectionTables(self.collection)
        mapped_df = ct._gene_mapping(pre_map_df)
        assert_frame_equal(mapped_df, self.expressions_df)

    @patch("resdk.collection_tables.BytesIO", MagicMock)
    @patch(
        "pandas.read_csv",
        MagicMock(
            side_effect=[
                pd.DataFrame(
                    [["GA", 0 + i], ["GB", 1 + i], ["GC", 2 + i]],
                    columns=["Gene", "Expression"],
                )
                for i in range(3)
            ]
        ),
    )
    @patch.object(CollectionTables, "_table_samples", new_callable=PropertyMock)
    @patch.object(CollectionTables, "_gene_mapping", new_callable=PropertyMock)
    def test_download_expressions(self, map_mock, sample_mock):
        map_mock.return_value = lambda x: x
        sample_mock.return_value = self.table_samples
        self.resolwe.url = "https://server.com"
        self.resolwe.auth = MagicMock()
        get_mock = MagicMock(return_value=MagicMock())
        self.resolwe.session.get = get_mock

        ct = CollectionTables(self.collection)
        expression_df = ct._download_expressions(TPM)

        get_calls = [
            call("https://server.com/data/0/tpm.csv", auth=ANY),
            call("https://server.com/data/1/tpm.csv", auth=ANY),
            call("https://server.com/data/2/tpm.csv", auth=ANY),
        ]
        get_mock.assert_has_calls(get_calls)
        assert_frame_equal(expression_df, self.expressions_df)
