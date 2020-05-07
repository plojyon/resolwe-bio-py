"""
Unit tests for resdk/resources/process.py file.
"""


import unittest

from mock import patch

from resdk.resources.process import Process


class TestBaseCollection(unittest.TestCase):
    @patch("resdk.resources.process._print_input_line", spec=True)
    @patch("resdk.resources.process.Process", spec=True)
    def test_print_inputs(self, process_mock, print_input_mock):
        process_mock.configure_mock(input_schema="fake_input_schema")
        Process.print_inputs(process_mock)
        print_input_mock.assert_called_once_with("fake_input_schema", 0)


if __name__ == "__main__":
    unittest.main()
