from resdk.exceptions import ResolweServerError

from ..base import BaseResdkFunctionalTest


class TestDuplication(BaseResdkFunctionalTest):
    def setUp(self):
        super().setUp()
        self.obj = None
        self.duplicate = None

    def tearDown(self):
        if self.obj:
            self.obj.delete(force=True)
        if self.duplicate:
            self.duplicate.delete(force=True)

    def test_collection_duplication(self):
        self.obj = self.res.collection.create(name="Test collection")
        self.duplicate = self.obj.duplicate()
        self.assertEqual(self.duplicate.name, "Copy of Test collection")

    def test_sample_duplication(self):
        self.obj = self.res.sample.create(name="Test sample")
        self.duplicate = self.obj.duplicate()
        self.assertEqual(self.duplicate.name, "Copy of Test sample")

    def test_data_duplication(self):
        self.obj = self.res.run(slug="test-sleep-progress", input={"t": 1})
        # Let's not wait for processing to finish and
        # check the expected exception to be raised.
        with self.assertRaisesRegex(
            ResolweServerError, "done or error status to be duplicated"
        ):
            # Data's `duplicate` raises an exception if status
            # of the object is not done or error.
            self.obj.duplicate()
