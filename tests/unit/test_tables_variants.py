import json
import shutil
import tempfile
import time
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from mock import MagicMock, PropertyMock, patch

from resdk.tables import VariantTables


class TestVariantTables(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

        mutation_header = [
            "CHROM",
            "POS",
            "REF",
            "ALT",
            "DP",
            "HGVS.p",
            "SAMPLENAME1.GT",
            "Base_A",
            "Base_C",
            "Base_G",
            "Base_T",
            "Total_depth",
        ]

        # Sample and data 1
        self.sample1 = MagicMock()
        self.sample1.id = 101
        self.sample1.name = "Sample 101"
        self.data1 = MagicMock()
        self.data1.id = 1001
        self.data1.input = {"mutations": ["FHIT"]}
        self.data1.sample = self.sample1
        self.variants_file1 = Path(self.tmp_dir) / "variants1.tsv"
        self.variants_data1 = pd.DataFrame(
            columns=mutation_header,
            data=[
                ["chr2", 120, "C", "T", 24, "p.Gly12Asp", "C/T", 0, 10, 0, 55, 65],
                ["chr2", 123, "C", "T", 44, "p.Gly13Asp", "T/T", 0, 10, 0, 41, 51],
            ],
        )
        self.variants_data1.to_csv(self.variants_file1, sep="\t")

        # Sample and data 2
        self.sample2 = MagicMock()
        self.sample2.id = 102
        self.sample2.name = "Sample 102"
        self.data2 = MagicMock()
        self.data2.id = 1002
        self.data2.input = {"mutations": ["FHIT"]}
        self.data2.sample = self.sample2
        self.variants_file2 = Path(self.tmp_dir) / "variants2.tsv"
        self.variants_data2 = pd.DataFrame(
            columns=mutation_header,
            data=[
                ["chr2", 120, "C", "T", 24, "p.Gly12Asp", "C/T", 0, 10, 0, 640, 650],
            ],
        )
        self.variants_data2.to_csv(self.variants_file2, sep="\t")

        uri_resolve_response = MagicMock()
        self.uri2url_mapping = {
            f"{self.data1.sample.id}/{self.variants_file1}": "url1",
            f"{self.data2.sample.id}/{self.variants_file2}": "url2",
        }
        uri_resolve_response.content = json.dumps(self.uri2url_mapping).encode("utf-8")

        self.resolwe = MagicMock()
        self.resolwe.url = "https://server.com"
        self.resolwe.session.post = self.web_request(uri_resolve_response)

        self.collection = MagicMock()
        self.collection.resolwe = self.resolwe
        self.collection.data.filter = self.web_request([self.data1, self.data2])

    @staticmethod
    def web_request(return_value):
        def slow(*args, **kwargs):
            time.sleep(0.1)
            return return_value

        return slow

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    @patch.object(VariantTables, "check_heterogeneous_mutations")
    def test_init(self, hetero_check):
        vt = VariantTables(self.collection)
        self.assertEqual(vt.mutations, None)
        self.assertEqual(vt.discard_fakes, True)
        hetero_check.assert_called_once()

        hetero_check.reset_mock()

        vt = VariantTables(self.collection, mutations=["BRCA2"], discard_fakes=True)
        self.assertEqual(vt.mutations, ["BRCA2"])
        self.assertEqual(vt.discard_fakes, True)
        hetero_check.assert_not_called()

    @patch.object(VariantTables, "_data", new_callable=PropertyMock)
    def test_check_heterogeneous_mutations(self, data_mock):
        data_mock.return_value = [self.data1]
        VariantTables(self.collection)

        self.data2.input = {"mutations": ["FHIT", "BRCA: Gly12"]}
        data_mock.return_value = [self.data1, self.data2]
        with self.assertRaisesRegex(ValueError, r"Variants should be computed .*"):
            VariantTables(self.collection)

        VariantTables(self.collection, mutations=["BRCA2"])

    def test_parse_mutations_string(self):
        vt = VariantTables(self.collection)

        self.assertEqual(
            vt.parse_mutations_string(["BRCA2"]),
            {"BRCA2": set()},
        )
        self.assertEqual(
            vt.parse_mutations_string(["BRCA2: Gly3Thy, Gly7Thy"]),
            {"BRCA2": {"Gly3Thy", "Gly7Thy"}},
        )
        self.assertEqual(
            vt.parse_mutations_string(["BRCA2: Gly3Thy, Gly7Thy", "FHIT"]),
            {
                "BRCA2": {"Gly3Thy", "Gly7Thy"},
                "FHIT": set(),
            },
        )

    def test_is_mutation_subset(self):
        vt = VariantTables(self.collection)

        self.assertTrue(vt.is_mutation_subset(["BRCA2"], ["BRCA2"]))
        self.assertTrue(vt.is_mutation_subset(["BRCA2: Thy12Gly"], ["BRCA2"]))
        self.assertTrue(
            vt.is_mutation_subset(["BRCA2: Thy12Gly"], ["BRCA2: Thy12Gly, Thy15Gly"])
        )
        self.assertTrue(
            vt.is_mutation_subset(
                ["BRCA2: Thy12Gly"], ["BRCA2: Thy12Gly", "BRCA3: Thy15Gly"]
            )
        )
        self.assertFalse(vt.is_mutation_subset(["BRCA2"], ["BRCA2: Thy12Gly"]))
        self.assertFalse(
            vt.is_mutation_subset(["BRCA2: Thy12Gly"], ["BRCA2: Thy15Gly"])
        )

    def test_data(self):
        self.collection.data.filter = self.web_request([self.data1])
        vt = VariantTables(self.collection)
        self.assertEqual(vt._data, [self.data1])

        self.collection.data.filter = self.web_request([self.data1, self.data2])
        vt = VariantTables(self.collection)
        self.assertEqual(vt._data, [self.data1, self.data2])

    def session_get_wrapper(self, url):
        file_name = next(
            Path(uri).name for uri, url_ in self.uri2url_mapping.items() if url_ == url
        )

        async def read_mock():
            with open(Path(self.tmp_dir) / file_name, "rb") as handle:
                return handle.read()

        response_mock = MagicMock()
        response_mock.content.read = read_mock

        aenter_mock = MagicMock()
        aenter_mock.__aenter__.return_value = response_mock

        return aenter_mock

    @patch("resdk.tables.base.aiohttp.ClientSession.get")
    @patch.object(VariantTables, "_get_data_uri")
    def test_variants(self, data_uri_mock, get_mock):
        # Mock the response of _get_data_uri
        data_uri_mock.side_effect = [
            f"{self.data1.sample.id}/{self.variants_file1}",
            f"{self.data2.sample.id}/{self.variants_file2}",
        ]
        # Mock the response of aiohttp.session.get
        get_mock.side_effect = self.session_get_wrapper

        vt = VariantTables(self.collection)
        expected = pd.DataFrame(
            [[1.0, 2.0], [1.0, np.nan]],
            index=[self.sample1.id, self.sample2.id],
            columns=["chr2_120_C>T_Gly12Asp", "chr2_123_C>T_Gly13Asp"],
        )
        expected.index.name = "sample_id"
        pd.testing.assert_frame_equal(vt.variants, expected)

    @patch("resdk.tables.base.aiohttp.ClientSession.get")
    @patch.object(VariantTables, "_get_data_uri")
    def test_depth(self, data_uri_mock, get_mock):
        # Mock the response of _get_data_uri
        data_uri_mock.side_effect = list(self.uri2url_mapping.keys())
        # Mock the response of aiohttp.session.get
        get_mock.side_effect = self.session_get_wrapper

        vt = VariantTables(self.collection)

        expected = pd.DataFrame(
            [[65.0, 51.0], [650.0, np.nan]],
            index=[self.sample1.id, self.sample2.id],
            columns=["chr2_120_C>T_Gly12Asp", "chr2_123_C>T_Gly13Asp"],
        )
        expected.index.name = "sample_id"
        pd.testing.assert_frame_equal(vt.depth, expected)

    @patch("resdk.tables.base.aiohttp.ClientSession.get")
    @patch.object(VariantTables, "_get_data_uri")
    def test_depth_t(self, data_uri_mock, get_mock):
        # Mock the response of _get_data_uri
        data_uri_mock.side_effect = list(self.uri2url_mapping.keys())
        # Mock the response of aiohttp.session.get
        get_mock.side_effect = self.session_get_wrapper

        vt = VariantTables(self.collection)

        expected = pd.DataFrame(
            [[55.0, 41.0], [640.0, np.nan]],
            index=[self.sample1.id, self.sample2.id],
            columns=["chr2_120_C>T_Gly12Asp", "chr2_123_C>T_Gly13Asp"],
        )
        expected.index.name = "sample_id"
        pd.testing.assert_frame_equal(vt.depth_t, expected)

    def test_strip_amino_acid(self):
        vt = VariantTables(self.collection)

        self.assertEqual(vt.strip_amino_acid("Gly12Asp"), "Gly12Asp")
        self.assertEqual(vt.strip_amino_acid("p.Gly12Asp"), "Gly12Asp")
        self.assertEqual(vt.strip_amino_acid("_p.Gly12Asp"), "")
        self.assertEqual(vt.strip_amino_acid("p.Gly12Asp_"), "")
        self.assertEqual(
            vt.strip_amino_acid(
                "foobar",
            ),
            "",
        )
        self.assertEqual(vt.strip_amino_acid("p.Gly12Asp", remove_alt=True), "Gly12")

    def test_construct_index(self):
        vt = VariantTables(self.collection)

        row = pd.Series({"CHROM": "chr2", "POS": 7, "REF": "C"})
        self.assertEqual(vt.construct_index(row), "chr2_7")

        row = pd.Series({"CHROM": "chr2", "POS": 7, "REF": "C", "ALT": "T"})
        self.assertEqual(vt.construct_index(row), "chr2_7_C>T")

        row = pd.Series({"CHROM": "chr2", "POS": 7, "REF": "C", "ALT": "X"})
        self.assertEqual(vt.construct_index(row), "chr2_7")

        row = pd.Series(
            {"CHROM": "chr2", "POS": 7, "REF": "C", "ALT": "T", "HGVS.p": "p.Gly3Asp"}
        )
        self.assertEqual(vt.construct_index(row), "chr2_7_C>T_Gly3Asp")

        row = pd.Series(
            {"CHROM": "chr2", "POS": 7, "REF": "C", "ALT": "T", "HGVS.p": "foobar"}
        )
        self.assertEqual(vt.construct_index(row), "chr2_7_C>T")

    def test_encode_mutation(self):
        vt = VariantTables(self.collection)

        row = pd.Series(
            {"REF": "C", "ALT": "T", "HGVS.p": "p.Gly3Asp", "SAMPLENAME1.GT": "T/T"}
        )
        self.assertEqual(vt.encode_mutation(row), 2)

        row = pd.Series(
            {"REF": "C", "ALT": "T", "HGVS.p": "p.Gly3Asp", "SAMPLENAME1.GT": "C/T"}
        )
        self.assertEqual(vt.encode_mutation(row), 1)

        row = pd.Series(
            {"REF": "C", "ALT": "T", "HGVS.p": "p.Gly3Asp", "SAMPLENAME1.GT": "C/C"}
        )
        self.assertEqual(vt.encode_mutation(row), 0)

        row = pd.Series(
            {"REF": "C", "ALT": np.nan, "HGVS.p": np.nan, "SAMPLENAME1.GT": np.nan}
        )
        self.assertEqual(vt.encode_mutation(row), 0)

    def test_parse_file(self):
        vt = VariantTables(self.collection)

        # Not much of testing here since all the parts of are
        # mostly covered in other tests.
        pd.testing.assert_series_equal(
            vt._parse_file(self.variants_file1, 7, "variants"),
            pd.Series(
                [1, 2], index=["chr2_120_C>T_Gly12Asp", "chr2_123_C>T_Gly13Asp"], name=7
            ),
        )

    def test_postprocess_variants_table(self):
        # Keep fakes
        vt = VariantTables(self.collection, discard_fakes=False)

        df = pd.DataFrame(
            [
                [2.0, np.nan, 1.0],
                [np.nan, 0.0, 1.0],
            ],
            index=[101, 102],
            columns=["chr2_10_C>T_Thy4Asp", "chr2_10", "chr2_13_C>T_Thy4Asp"],
        )

        df2 = vt.postprocess_variants_table(df, "variants")
        np.testing.assert_array_equal(
            df2.values.tolist(),
            [
                [2.0, np.nan, 1.0],
                [0.0, 0.0, 1.0],
            ],
        )
        pd.testing.assert_index_equal(df2.index, df.index)
        pd.testing.assert_index_equal(df2.columns, df.columns)

        # Remove fakes
        vt = VariantTables(self.collection, discard_fakes=True)
        df2 = vt.postprocess_variants_table(df, "variants")
        np.testing.assert_array_equal(
            df2.values.tolist(),
            [
                [2.0, 1.0],
                [0.0, 1.0],
            ],
        )
        pd.testing.assert_index_equal(df2.index, df.index)
        np.testing.assert_array_equal(
            df2.columns, ["chr2_10_C>T_Thy4Asp", "chr2_13_C>T_Thy4Asp"]
        )
