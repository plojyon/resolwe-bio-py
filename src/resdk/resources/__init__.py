""".. Ignore pydocstyle D400.

=========
Resources
=========

Resource classes
================

.. autoclass:: resdk.resources.base.BaseResource
   :members:

.. autoclass:: resdk.resources.base.BaseResolweResource
   :members:

.. autoclass:: resdk.resources.Data
   :members:

.. autoclass:: resdk.resources.collection.BaseCollection
   :members:

.. autoclass:: resdk.resources.Collection
   :members:

.. autoclass:: resdk.resources.Sample
   :members:

.. autoclass:: resdk.resources.Relation
   :members:

.. autoclass:: resdk.resources.Process
   :members:

.. autoclass:: resdk.resources.DescriptorSchema
   :members:

.. autoclass:: resdk.resources.User
   :members:

.. autoclass:: resdk.resources.Group
   :members:

.. automodule:: resdk.resources.kb

Permissions
===========

Resources like :class:`resdk.resources.Data`,
:class:`resdk.resources.Collection`, :class:`resdk.resources.Sample`, and
:class:`resdk.resources.Process` include a `permissions` attribute to manage
permissions. The `permissions` attribute is an instance of
`resdk.resources.permissions.PermissionsManager`.

.. autoclass:: resdk.resources.permissions.PermissionsManager
   :members:

Utility functions
=================

.. automodule:: resdk.resources.utils
   :members:

"""
from .collection import Collection
from .data import Data
from .descriptor import DescriptorSchema
from .process import Process
from .relation import Relation
from .sample import Sample
from .user import Group, User

__all__ = (
    "Collection",
    "Data",
    "DescriptorSchema",
    "Group",
    "Sample",
    "Process",
    "Relation",
    "User",
)
