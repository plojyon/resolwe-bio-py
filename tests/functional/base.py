"""Functional tests for ReSDK."""
import os
import unittest

from resdk import Resolwe

URL = os.environ.get("SERVER_URL", "http://localhost:8000")
USER_USERNAME = "user"
USER_PASSWORD = "user"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"

FILES_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "files")
)


class BaseResdkFunctionalTest(unittest.TestCase):
    """Base class for functional tests in ReSDK.

    It generates 2 Resolwe classes for connection to server. One with
    admin's credentials (``self.res``) and one with normal user's
    credentials (``self.user_res``).

    """

    def setUp(self):
        self.res = Resolwe(ADMIN_USERNAME, ADMIN_PASSWORD, URL)
        self.user_res = Resolwe(USER_USERNAME, USER_PASSWORD, URL)

    def set_slug(self, resource, slug):
        """Set slug of resource."""
        resource.slug = slug
        resource.save()
