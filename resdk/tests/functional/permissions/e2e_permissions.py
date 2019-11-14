# pylint: disable=missing-docstring,no-member
from resdk.exceptions import ResolweServerError

from ..base import USER_USERNAME, BaseResdkFunctionalTest


class TestPermissions(BaseResdkFunctionalTest):

    def test_permissions(self):
        collection_admin = self.res.collection.create(name='Test collection')

        # User doesn't have the permission to view the collection.
        with self.assertRaises(LookupError):
            self.user_res.collection.get(collection_admin.id)

        collection_admin.permissions.add_user(USER_USERNAME, 'view')

        # User can see the collection, but cannot edit it.
        collection_user = self.user_res.collection.get(collection_admin.id)
        collection_user.name = 'New test collection'
        with self.assertRaises(ResolweServerError):
            collection_user.save()

        collection_admin.permissions.add_user(USER_USERNAME, 'edit')

        # User can edit the collection.
        collection_user = self.user_res.collection.get(collection_admin.id)
        collection_user.name = 'New test collection'
        collection_user.save()

        collection_admin.permissions.remove_user(USER_USERNAME, 'edit')

        # Edit permission is removed again.
        collection_user = self.user_res.collection.get(collection_admin.id)
        collection_user.name = 'Another collection'
        with self.assertRaises(ResolweServerError):
            collection_user.save()

    def test_get_holders_with_perm(self):
        collection = self.res.collection.create(name='Test collection')
        collection.permissions.add_user(USER_USERNAME, ['edit', 'view'])
        collection.permissions.add_public('view')

        self.assertEqual(len(collection.permissions.owners), 1)
        self.assertEqual(collection.permissions.owners[0].get_name(), "admin")

        self.assertEqual(len(collection.permissions.editors), 2)
        self.assertEqual(collection.permissions.editors[0].get_name(), "admin")
        self.assertEqual(collection.permissions.editors[1].get_name(), "user")


        self.assertEqual(len(collection.permissions.viewers), 3)
        self.assertEqual(collection.permissions.viewers[0].first_name, "admin")
        self.assertEqual(collection.permissions.viewers[1].first_name, "user")
        self.assertEqual(collection.permissions.viewers[2].username, "public")
