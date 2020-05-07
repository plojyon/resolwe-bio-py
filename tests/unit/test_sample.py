"""
Unit tests for resdk/resources/sample.py file.
"""


import unittest

from mock import MagicMock

from resdk.resources.descriptor import DescriptorSchema
from resdk.resources.sample import Sample


class TestSampleUtilsMixin(unittest.TestCase):
    def test_get_reads(self):
        sample = Sample(resolwe=MagicMock(), id=42)
        data1 = MagicMock(process_type="data:reads:fastq:single", id=1)
        data2 = MagicMock(process_type="data:reads:fastq:single:cutadapt", id=2)
        sample.data.filter = MagicMock(return_value=[data2, data1])

        self.assertEqual(sample.get_reads(), data2)


class TestSample(unittest.TestCase):
    def test_descriptor_schema(self):
        # hidrated descriptor schema
        descriptor_schema = {
            "slug": "test-schema",
            "name": "Test schema",
            "version": "1.0.0",
            "schema": [
                {
                    "default": "56G",
                    "type": "basic:string:",
                    "name": "description",
                    "label": "Object description",
                }
            ],
            "id": 1,
        }
        sample = Sample(id=1, descriptor_schema=descriptor_schema, resolwe=MagicMock())
        self.assertTrue(isinstance(sample.descriptor_schema, DescriptorSchema))

        self.assertEqual(sample.descriptor_schema.slug, "test-schema")

    def test_data(self):
        sample = Sample(id=1, resolwe=MagicMock())

        # test getting data attribute
        sample.resolwe.data.filter = MagicMock(
            return_value=["data_1", "data_2", "data_3"]
        )
        self.assertEqual(sample.data, ["data_1", "data_2", "data_3"])

        # test caching data attribute
        self.assertEqual(sample.data, ["data_1", "data_2", "data_3"])
        self.assertEqual(sample.resolwe.data.filter.call_count, 1)

        # cache is cleared at update
        sample._data = ["data"]
        sample.update()
        self.assertEqual(sample._data, None)

        # raising error if sample is not saved
        sample.id = None
        with self.assertRaises(ValueError):
            _ = sample.data


if __name__ == "__main__":
    unittest.main()
