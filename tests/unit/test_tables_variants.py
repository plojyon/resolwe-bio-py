import json
import shutil
import tempfile
import time
import unittest
from pathlib import Path

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
            "SAMPLENAME1.GT",
            "Gene_Name",
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
                ["chr2", 120, "C", "T", 24, "C/T", "FHIT", 0, 10, 0, 55, 65],
                ["chr2", 123, "C", "T", 44, "T/T", "FHIT", 0, 10, 0, 41, 51],
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
                ["chr2", 120, "C", "T", 24, "C/T", "FHIT", 0, 10, 0, 640, 650],
            ],
        )
        self.variants_data2.to_csv(self.variants_file2, sep="\t")

        uri_resolve_response = MagicMock()
        self.uri2url_mapping = {
            str(Path(str(self.data1.id)) / self.variants_file1): "url1",
            str(Path(str(self.data2.id)) / self.variants_file1): "url2",
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

    def test_init(self):
        vt = VariantTables(self.collection)
        self.assertEqual(vt.geneset, {"FHIT"})

        vt = VariantTables(self.collection, geneset=["BRCA2"])
        self.assertEqual(vt.geneset, {"BRCA2"})

    @patch.object(VariantTables, "_data", new_callable=PropertyMock)
    def test_check_heterogeneous_mutations(self, data_mock):
        data_mock.return_value = [self.data1]
        VariantTables(self.collection)

        self.data2.input = {"mutations": ["FHIT", "BRCA: Gly12"]}
        data_mock.return_value = [self.data1, self.data2]
        with self.assertRaisesRegex(ValueError, r"Variants should be computed .*"):
            VariantTables(self.collection)

        VariantTables(self.collection, geneset=["BRCA2"])

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

    def test_construct_index(self):
        vt = VariantTables(self.collection)

        row = pd.Series({"CHROM": "chr2", "POS": 7, "REF": "C", "ALT": "T"})
        self.assertEqual(vt._construct_index(row), "chr2_7_C>T")

    def test_encode_mutation(self):
        vt = VariantTables(self.collection)

        row = pd.Series({"REF": "C", "ALT": "T", "SAMPLENAME1.GT": "T/T"})
        self.assertEqual(vt._encode_mutation(row), 2)

        row = pd.Series({"REF": "C", "ALT": "T", "SAMPLENAME1.GT": "C/T"})
        self.assertEqual(vt._encode_mutation(row), 1)

        row = pd.Series({"REF": "C", "ALT": "T", "SAMPLENAME1.GT": "C/C"})
        self.assertEqual(vt._encode_mutation(row), 0)

    def test_parse_file(self):
        vt = VariantTables(self.collection)

        # Not much of testing here since all the parts of are
        # mostly covered in other tests.
        pd.testing.assert_series_equal(
            vt._parse_file(self.variants_file1, 7, "variants"),
            pd.Series([1, 2], index=["chr2_120_C>T", "chr2_123_C>T"], name=7),
        )
