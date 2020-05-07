"""
Unit tests for resdk/utils/decorators.py file.
"""


import unittest

from resdk.utils.decorators import assert_object_exists, return_first_element


class TestDecorators(unittest.TestCase):
    def test_return_first_element(self):
        @return_first_element
        def test_function():
            return [1]

        self.assertEqual(test_function(), 1)

        @return_first_element
        def test_function_2():
            return [1, 2]

        with self.assertRaises(RuntimeError):
            test_function_2()

        @return_first_element
        def test_function_3():
            return 1

        with self.assertRaises(TypeError):
            test_function_3()

    def test_assert_object_exists(self):
        class Example:
            def __init__(self, id=None):
                self.id = id
                super().__init__()

            @property
            @assert_object_exists
            def attr(self):
                return "attr"

            @assert_object_exists
            def method(self):
                return "method"

        # Case where id is defined.
        example = Example(id=42)
        self.assertEqual(example.attr, "attr")
        self.assertEqual(example.method(), "method")

        # Case where id is not defined.
        example = Example()
        message = "Instance must be saved before accessing `attr` attribute."
        with self.assertRaisesRegex(ValueError, message):
            example.attr
        message = "Instance must be saved before accessing `method` method."
        with self.assertRaisesRegex(ValueError, message):
            example.method()
