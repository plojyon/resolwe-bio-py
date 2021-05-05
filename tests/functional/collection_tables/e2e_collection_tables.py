import numpy as np

import resdk

from ..base import BaseResdkFunctionalTest


class TestCollectionTables(BaseResdkFunctionalTest):
    def setUp(self):
        pass

    @classmethod
    def setUpClass(cls):
        cls.test_server_url = "https://app.genialis.com"
        cls.test_collection_slug = "resdk-test-collection-tables"
        cls.res = resdk.Resolwe(
            url=cls.test_server_url, username="resdk-e2e-test", password="safe4ever"
        )
        cls.collection = cls.res.collection.get(cls.test_collection_slug)
        cls.ct = resdk.CollectionTables(cls.collection)

    def test_meta(self):
        self.assertEqual(self.ct.meta.shape, (8, 9))
        self.assertIn("Copy of SUM149_JQ1_12H_R1", self.ct.meta.index)
        self.assertIn("general.species", self.ct.meta.columns)

    def test_rc(self):
        self.assertEqual(self.ct.rc.shape, (8, 58487))
        self.assertIn("Copy of SUM149_JQ1_12H_R1", self.ct.rc.index)
        self.assertIn("ENSG00000000003", self.ct.rc.columns)
        self.assertEqual(self.ct.rc.iloc[0, 0], 1580)
        self.assertIsInstance(self.ct.rc.iloc[0, 0], np.int64)

    def test_exp(self):
        self.assertEqual(self.ct.exp.shape, (8, 58487))
        self.assertIn("Copy of SUM149_JQ1_12H_R1", self.ct.exp.index)
        self.assertIn("ENSG00000000003", self.ct.exp.columns)
        self.assertAlmostEqual(self.ct.exp.iloc[0, 0], 32.924003, places=3)
        self.assertIsInstance(self.ct.exp.iloc[0, 0], np.float64)
