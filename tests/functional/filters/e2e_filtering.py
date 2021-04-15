from __future__ import absolute_import, division, print_function, unicode_literals

import os
import unittest

from ..base import FILES_PATH, BaseResdkFunctionalTest


class BaseResdkFilteringTest(BaseResdkFunctionalTest):
    def setUp(self):
        super().setUp()
        self.endpoint = self.res.data

    def _get_ids(self, query):
        """Return id's of objects in query."""
        return [getattr(elm, "id") for elm in query]

    def _check_filter(self, query_args, expected):
        response = self._get_ids(self.endpoint.filter(**query_args))
        expected = self._get_ids(expected)
        self.assertCountEqual(response, expected)

    @staticmethod
    def datetime_to_str(datetime):
        return datetime.strftime("%Y-%m-%dT%H:%M:%S.%f%z")


class TestDataFilter(BaseResdkFilteringTest):
    def setUp(self):
        super().setUp()

        self.endpoint = self.res.data

        self.data1 = self.res.run(
            slug="upload-fasta-nucl",
            input={
                "src": os.path.join(FILES_PATH, "genome.fasta.gz"),
                "species": "Homo sapiens",
                "build": "hg38",
            },
            data_name="Data 1",
        )
        self.data2 = self.res.run(
            slug="upload-fasta-nucl",
            input={
                "src": os.path.join(FILES_PATH, "genome.fasta.gz"),
                "species": "Homo sapiens",
                "build": "hg38",
            },
            data_name="Data 2",
        )

    def tearDown(self):
        super().tearDown()
        self.data1.delete(force=True)
        self.data2.delete(force=True)

    def test_id(self):
        self._check_filter({"id": self.data1.id}, [self.data1])
        self._check_filter({"id": self.data2.id}, [self.data2])
        self._check_filter({"id__in": [self.data1.id]}, [self.data1])
        self._check_filter(
            {"id__in": [self.data1.id, self.data2.id]}, [self.data1, self.data2]
        )


class TestProcessFilter(BaseResdkFilteringTest):
    def setUp(self):
        super().setUp()

        self.endpoint = self.res.process

        self.star = self.res.process.get(slug="alignment-star")

        self.hisat2 = self.res.process.get(slug="alignment-hisat2")

    def test_id(self):
        self._check_filter({"id": self.star.id}, [self.star])
        self._check_filter({"id": self.hisat2.id}, [self.hisat2])
        self._check_filter({"id__in": [self.star.id]}, [self.star])
        self._check_filter(
            {"id__in": [self.star.id, self.hisat2.id]}, [self.star, self.hisat2]
        )

    def test_iterate_method(self):
        workflows = list(
            self.res.process.filter(type="data:workflow").iterate(chunk_size=10)
        )
        # Use ``assertGreater`` to avoid updating this test each time
        # after new workflow is added / removed.
        self.assertGreater(len(workflows), 30)


class TestFeatureFilter(BaseResdkFilteringTest):
    def setUp(self):
        super().setUp()

        self.endpoint = self.res.feature

        self.ft1 = self.res.feature.get(
            source="ENSEMBL",
            feature_id="id_001",
            species="Homo sapiens",
        )
        self.ft2 = self.res.feature.get(
            source="ENSEMBL",
            feature_id="id_002",
            species="Mus musculus",
        )

    @unittest.skip("Turn on when one can prepare KnowledgeBase and ES index for it.")
    def test_id(self):
        self._check_filter({"feature_id": self.ft1.feature_id}, [self.ft1])
        self._check_filter(
            {"feature_id__in": [self.ft1.feature_id, self.ft2.feature_id]},
            [self.ft1, self.ft2],
        )
