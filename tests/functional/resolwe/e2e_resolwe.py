import resdk

from ..base import BaseResdkFunctionalTest


class TestRun(BaseResdkFunctionalTest):
    def test_run(self):
        collection = self.res.collection.get(name="Test collection")

        data = self.res.run(
            slug="test-sleep-progress",
            input={"t": 1},
            descriptor_schema="reads",
            descriptor={"description": "Lorem ipsum ..."},
            collection=collection,
            data_name="Test run data",
        )

        self.assertTrue(isinstance(data, resdk.resources.Data))
        self.assertEqual(data.process.slug, "test-sleep-progress")
        self.assertEqual(data.input, {"t": 1})
        self.assertEqual(data.descriptor_schema.slug, "reads")

        self.assertEqual(data.descriptor["description"], "Lorem ipsum ...")

        self.assertEqual(data.collection, collection)
        self.assertEqual(data.name, "Test run data")


class TestDataUsage(BaseResdkFunctionalTest):

    expected_fields = {
        "user_id",
        "username",
        "full_name",
        "data_size",
        "data_size_normalized",
        "data_count",
        "data_count_normalized",
        "collection_count",
        "collection_count_normalized",
        "sample_count",
        "sample_count_normalized",
    }

    def test_normal_user(self):
        usage_info = self.user_res.data_usage()
        self.assertEqual(len(usage_info), 1)
        self.assertEqual(set(usage_info[0].keys()), self.expected_fields)

    def test_admin_user(self):
        usage_info = self.res.data_usage()
        self.assertGreaterEqual(len(usage_info), 2)
        self.assertEqual(set(usage_info[0].keys()), self.expected_fields)

    def test_ordering(self):
        usage_info = self.res.data_usage(ordering=["full_name", "-data_size"])
        self.assertGreaterEqual(len(usage_info), 2)
        first = usage_info[0]
        second = usage_info[1]
        self.assertEqual(first["full_name"], second["full_name"])
        self.assertGreaterEqual(first["data_size"], second["data_size"])
