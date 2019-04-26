"""
Unit tests for resdk/resources/sample.py file.
"""
# pylint: disable=missing-docstring, protected-access

import unittest

from mock import MagicMock, patch

from resdk.resources.descriptor import DescriptorSchema
from resdk.resources.sample import Sample


class TestSampleUtilsMixin(unittest.TestCase):

    def test_get_reads(self):
        sample = Sample(resolwe=MagicMock(), id=42)
        data1 = MagicMock(process_type='data:reads:fastq:single', id=1)
        data2 = MagicMock(process_type='data:reads:fastq:single:cutadapt', id=2)
        sample.data.filter = MagicMock(return_value=[data2, data1])

        self.assertEqual(sample.get_reads(), data2)


class TestSample(unittest.TestCase):

    def test_descriptor_schema(self):
        sample = Sample(id=1, resolwe=MagicMock())
        sample._descriptor_schema = 1

        # test getting descriptor schema attribute
        sample.resolwe.descriptor_schema.get = MagicMock(return_value='descriptor_schema')
        self.assertEqual(sample.descriptor_schema, 'descriptor_schema')
        _, get_kwargs = sample.resolwe.descriptor_schema.get.call_args
        self.assertEqual(get_kwargs['id'], 1)

        # descriptor schema is not set
        sample._descriptor_schema = None
        self.assertEqual(sample.descriptor_schema, None)

        # cache is cleared at update
        sample._hydrated_descriptor_schema = 'descriptor_schema'
        sample.update()
        self.assertEqual(sample._hydrated_descriptor_schema, None)

        # new collection
        sample = Sample(resolwe=MagicMock())

        sample.descriptor_schema = 'my-schema'
        self.assertEqual(sample._descriptor_schema, 'my-schema')

        sample.resolwe.descriptor_schema.get = MagicMock(return_value='descriptor_schema')
        self.assertEqual(sample.descriptor_schema, 'descriptor_schema')
        _, get_kwargs = sample.resolwe.descriptor_schema.get.call_args
        self.assertEqual(get_kwargs['slug'], 'my-schema')

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
                    "label": "Object description"
                }
            ],
            "id": 1,
        }
        sample = Sample(id=1, descriptor_schema=descriptor_schema, resolwe=MagicMock())
        self.assertTrue(isinstance(sample.descriptor_schema, DescriptorSchema))
        # pylint: disable=no-member
        self.assertEqual(sample.descriptor_schema.slug, 'test-schema')
        # pylint: enable=no-member

    def test_data(self):
        sample = Sample(id=1, resolwe=MagicMock())

        # test getting data attribute
        sample.resolwe.data.filter = MagicMock(return_value=['data_1', 'data_2', 'data_3'])
        self.assertEqual(sample.data, ['data_1', 'data_2', 'data_3'])

        # test caching data attribute
        self.assertEqual(sample.data, ['data_1', 'data_2', 'data_3'])
        self.assertEqual(sample.resolwe.data.filter.call_count, 1)

        # cache is cleared at update
        sample._data = ['data']
        sample.update()
        self.assertEqual(sample._data, None)

        # raising error if sample is not saved
        sample.id = None
        with self.assertRaises(ValueError):
            _ = sample.data

    def test_collections(self):
        sample = Sample(id=1, resolwe=MagicMock())
        sample._original_values = {'collections': [1, 2, 3]}

        # test getting data attribute
        sample.resolwe.collection.filter = MagicMock(
            return_value=['collection_1', 'collection_2', 'collection_3'])
        self.assertEqual(sample.collections, ['collection_1', 'collection_2', 'collection_3'])

        # test caching data attribute
        self.assertEqual(sample.collections, ['collection_1', 'collection_2', 'collection_3'])
        self.assertEqual(sample.resolwe.collection.filter.call_count, 1)

        # cache is cleared at update
        sample._collections = ['collection']
        sample.update()
        self.assertEqual(sample._collections, None)

        # raising error if sample is not saved
        sample.id = None
        with self.assertRaises(ValueError):
            _ = sample.collections

    @patch('resdk.resources.sample.Sample', spec=True)
    def test_update_descriptor(self, sample_mock):
        sample_mock.configure_mock(id=42, api=MagicMock())
        Sample.update_descriptor(sample_mock, {'field': 'value'})
        sample_mock.api(42).patch.assert_called_once_with({'descriptor': {'field': 'value'}})

    @patch('resdk.resources.sample.Sample', spec=True)
    def test_confirm_is_annotated(self, sample_mock):
        sample_mock.configure_mock(endpoint='sample', id=42, api=MagicMock(), logger=MagicMock())
        Sample.confirm_is_annotated(sample_mock)
        sample_mock.api(42).patch.assert_called_once_with({'descriptor_completed': True})


if __name__ == '__main__':
    unittest.main()
