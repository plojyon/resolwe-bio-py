from resdk.exceptions import ResolweServerError

from ..base import BaseResdkFunctionalTest


class TestDuplication(BaseResdkFunctionalTest):
    def test_collection_duplication(self):
        collection = self.res.collection.create(name="Test collection")
        duplicate = collection.duplicate()
        self.assertEqual(duplicate.name, "Copy of Test collection")

        duplicate.delete(force=True)
        collection.delete(force=True)

    def test_sample_duplication(self):
        sample = self.res.sample.create(name="Test sample")
        duplicate = sample.duplicate()
        self.assertEqual(duplicate.name, "Copy of Test sample")

        duplicate.delete(force=True)
        sample.delete(force=True)

    def test_data_duplication(self):
        data = self.res.run(slug="test-sleep-progress", input={"t": 1})
        # Let's not wait for processing to finish and
        # check the expected exception to be raised.
        with self.assertRaisesRegex(
            ResolweServerError, "done or error status to be duplicated"
        ):
            # Data's `duplicate` raises an exception if status
            # of the object is not done or error.
            data.duplicate()
