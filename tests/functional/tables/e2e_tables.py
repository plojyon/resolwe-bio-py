import os
import shutil
import tempfile
import time

import numpy as np

import resdk
from resdk.tables import RNATables

from ..base import BaseResdkFunctionalTest


class TestTables(BaseResdkFunctionalTest):
    def setUp(self):
        self.cache_dir = tempfile.mkdtemp()
        self.test_server_url = "https://app.genialis.com"
        self.test_collection_slug = "resdk-test-collection-tables"
        self.res = resdk.Resolwe(
            url=self.test_server_url, username="resdk-e2e-test", password="safe4ever"
        )
        self.collection = self.res.collection.get(self.test_collection_slug)
        self.ct = RNATables(self.collection, cache_dir=self.cache_dir)

    def tearDown(self):
        shutil.rmtree(self.cache_dir)

    def test_meta(self):
        self.assertEqual(self.ct.meta.shape, (8, 9))
        self.assertIn(39000, self.ct.meta.index)
        self.assertIn("general.species", self.ct.meta.columns)

    def test_qc(self):
        self.assertEqual(self.ct.qc.shape, (8, 12))
        self.assertIn(39000, self.ct.qc.index)
        self.assertIn("total_read_count_raw", self.ct.qc.columns)
        self.assertEqual(int(self.ct.qc.loc[39000, "total_read_count_raw"]), 42738650)

    def test_rc(self):
        self.assertEqual(self.ct.rc.shape, (8, 58487))
        self.assertIn(39000, self.ct.rc.index)
        self.assertIn("ENSG00000000003", self.ct.rc.columns)
        self.assertEqual(self.ct.rc.iloc[0, 0], 792)
        self.assertIsInstance(self.ct.rc.iloc[0, 0], np.int64)

    def test_exp(self):
        self.assertEqual(self.ct.exp.shape, (8, 58487))
        self.assertIn(39000, self.ct.exp.index)
        self.assertIn("ENSG00000000003", self.ct.exp.columns)
        self.assertAlmostEqual(self.ct.exp.iloc[0, 0], 19.447467, places=3)
        self.assertIsInstance(self.ct.exp.iloc[0, 0], np.float64)

    def test_consistent_index(self):
        self.assertTrue(all(self.ct.exp.index == self.ct.meta.index))
        self.assertTrue(all(self.ct.rc.index == self.ct.meta.index))

    def test_caching(self):
        # Call rc first time with self.ct to populate the cache
        t0 = time.time()
        rc1 = self.ct.rc
        t1 = time.time() - t0

        # Make sure that cache file is created
        cache_file = self.ct._cache_file(self.ct.RC)
        self.assertTrue(os.path.isfile(cache_file))

        # Make new table instance (to prevent loading from memory)
        ct2 = RNATables(self.collection, cache_dir=self.cache_dir)
        # Call rc second time, with it should load from disk cache
        t0 = time.time()
        rc2 = ct2.rc
        t2 = time.time() - t0
        self.assertTrue((rc1 == rc2).all(axis=None))
        self.assertTrue(t2 < t1)

        # Call rc second time with rc2 to test loading from memory
        t0 = time.time()
        rc3 = ct2.rc
        t3 = time.time() - t0
        self.assertTrue((rc2 == rc3).all(axis=None))
        self.assertTrue(t3 < t2)
