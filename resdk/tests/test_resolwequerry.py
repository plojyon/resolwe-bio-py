"""
Unit tests for resdk/resolwe.py file.
"""
# pylint: disable=missing-docstring, protected-access

import unittest
import six

import slumber

from mock import patch, MagicMock

from resdk.tests.mocks.data import PROCESS_SAMPLE, DATA_SAMPLE
from resdk.resolwe import ResolweQuerry
from resdk.resources.data import Data

if six.PY2:
    # pylint: disable=deprecated-method
    unittest.TestCase.assertRegex = unittest.TestCase.assertRegexpMatches


class TestResolweQuerry(unittest.TestCase):

    @patch('resdk.resolwe.ResolweQuerry', spec=True)
    def test_get(self, resq_mock):

        # User provides correct ID
        resq_mock.api = MagicMock()
        resq_mock.resolwe = MagicMock()
        resq_mock.resource = MagicMock(return_value="Some response")
        d = ResolweQuerry.get(resq_mock, 40)
        self.assertEqual(d, "Some response")

        # User provides wrong ID.
        resq_mock.resource = MagicMock(side_effect=[slumber.exceptions.HttpNotFoundError])
        with self.assertRaises(ValueError) as exc:
            ResolweQuerry.get(resq_mock, 12345)
        self.assertRegex(exc.exception.args[0], r'Id: .* does not exist or you dont have access permission.')

        # User provides correct slug.
        resq_mock.api = MagicMock()
        resq_mock.resolwe = MagicMock()
        resq_mock.resource = MagicMock(return_value="Some response")
        d = ResolweQuerry.get(resq_mock, "some-slug")
        self.assertEqual(d, "Some response")

        # User provides wrong slug.
        resq_mock.resource = MagicMock(side_effect=[IndexError])
        with self.assertRaises(ValueError) as exc:
            ResolweQuerry.get(resq_mock, "some-slug")
        self.assertRegex(exc.exception.args[0], r'Slug: .* does not exist or you dont have access permission.')

    @patch('resdk.resolwe.ResolweQuerry', spec=True)
    def test_filter(self, resq_mock):

        resq_mock.api = MagicMock()
        resq_mock.api.get = MagicMock(return_value=[{'id': 42}])
        resq_mock.resolwe = MagicMock()
        resq_mock.resource = MagicMock(return_value=12345)
        d = ResolweQuerry.filter(resq_mock, slug="some-slug")
        self.assertIsInstance(d, list)
        self.assertEqual(d[0], 12345)

if __name__ == '__main__':
    unittest.main()
