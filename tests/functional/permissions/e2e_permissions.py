from resdk.exceptions import ResolweServerError

from ..base import USER_USERNAME, BaseResdkFunctionalTest


class TestPermissions(BaseResdkFunctionalTest):
    def setUp(self):
        super().setUp()

        self.test_collection = self.res.collection.create(name="Test collection")
        self.collection2 = None

    def tearDown(self):
        super().tearDown()

        self.test_collection.delete(force=True)
        if self.collection2:
            self.collection2.delete(force=True)

    def test_permissions(self):
        # User doesn't have the permission to view the collection.
        with self.assertRaises(LookupError):
            self.user_res.collection.get(self.test_collection.id)

        self.test_collection.permissions.add_user(USER_USERNAME, "view")

        # User can see the collection, but cannot edit it.
        user_collection = self.user_res.collection.get(self.test_collection.id)
        user_collection.name = "Different name"
        with self.assertRaises(ResolweServerError):
            user_collection.save()

        self.test_collection.permissions.add_user(USER_USERNAME, "edit")

        # User can edit the collection.
        user_collection.name = "Different name"
        user_collection.save()

        self.test_collection.permissions.remove_user(USER_USERNAME, "edit")

        # Edit permission is removed again.
        user_collection.name = "Different name 2"
        with self.assertRaises(ResolweServerError):
            user_collection.save()

    def test_get_holders_with_perm(self):
        self.test_collection.permissions.add_user(USER_USERNAME, ["edit", "view"])
        self.test_collection.permissions.add_public("view")

        self.assertEqual(len(self.test_collection.permissions.owners), 1)
        self.assertEqual(self.test_collection.permissions.owners[0].get_name(), "admin")

        self.assertEqual(len(self.test_collection.permissions.editors), 2)
        self.assertEqual(
            self.test_collection.permissions.editors[0].get_name(), "admin"
        )
        self.assertEqual(self.test_collection.permissions.editors[1].get_name(), "user")

        self.assertEqual(len(self.test_collection.permissions.viewers), 3)
        self.assertEqual(
            self.test_collection.permissions.viewers[0].first_name, "admin"
        )
        self.assertEqual(self.test_collection.permissions.viewers[1].first_name, "user")
        self.assertEqual(self.test_collection.permissions.viewers[2].username, "public")

    def test_copy_from(self):
        # Create collection with only user permissions
        self.collection2 = self.user_res.collection.create(name="Test collection 2")
        self.collection2.permissions.fetch()
        self.assertEqual(len(self.collection2.permissions._permissions), 1)

        self.test_collection.permissions.add_public("view")
        self.collection2.permissions.copy_from(self.test_collection)
        self.assertEqual(len(self.collection2.permissions._permissions), 3)
