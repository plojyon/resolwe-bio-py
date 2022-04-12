import unittest
from io import BytesIO

import pandas as pd
from mock import MagicMock, patch

from resdk.tables import MLTables


class TestMLTables(unittest.TestCase):
    def setUp(self):
        self.table = pd.DataFrame(
            [[10, 20], [20, 30]],
            index=[101, 102],
            columns=["G1", "G2"],
        )

        self.response = MagicMock()
        with BytesIO() as handle:
            self.table.to_csv(handle, sep="\t")
            handle.seek(0)
            self.response.content = handle.read()

        self.resolwe = MagicMock()
        self.resolwe.url = "https://app.genialis.com/"
        self.resolwe.session.get.return_value = self.response

        self.collection = MagicMock()
        self.collection.resolwe = self.resolwe

        self.data = MagicMock()
        self.data.id = 42
        self.data.output = {"exp": {"file": "table.tsv"}}

    @patch.object(MLTables, "_get_datum")
    def test_exp(self, get_datum_mock):
        get_datum_mock.return_value = self.data
        mt = MLTables(self.collection, name="Combat TCGA")

        pd.testing.assert_frame_equal(mt.exp, self.table)
