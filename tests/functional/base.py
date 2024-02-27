"""Functional tests for ReSDK."""

import os
import unittest
from unittest.mock import patch

from resdk import Resolwe

URL = os.environ.get("SERVER_URL", "http://localhost:8000")

# Get the regular user credentials from environment variables.
# Fallback to default values if the environment variables are not set.
USER_USERNAME = os.environ.get("USER_USERNAME", "user")
USER_EMAIL = os.environ.get("USER_EMAIL", "user@genialis.com")
USER_PASSWORD = os.environ.get("USER_PASSWORD", "user")

# Get the admin user credentials from environment variables.
# Fallback to default values if the environment variables are not set.
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@genialis.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

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
        """Prepare objects and patch them to use username/password authentication."""
        with patch("resdk.resolwe.AUTOMATIC_LOGIN_POSTFIX", "rest-auth/login/"):
            self.res = Resolwe(ADMIN_EMAIL, ADMIN_PASSWORD, URL)
            self.user_res = Resolwe(USER_EMAIL, USER_PASSWORD, URL)

    def set_slug(self, resource, slug):
        """Set slug of resource."""
        resource.slug = slug
        resource.save()
