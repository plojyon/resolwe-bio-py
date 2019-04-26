# pylint: disable=missing-docstring
from resdk.exceptions import ResolweServerError
from resdk.tests.functional.base import ADMIN_USERNAME, USER_USERNAME, BaseResdkFunctionalTest


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
