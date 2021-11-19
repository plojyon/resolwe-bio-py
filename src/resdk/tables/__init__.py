""".. Ignore pydocstyle D400.

============
ReSDK Tables
============

Helper classes for aggregating collection data in tabular format.

Table classes
=============

.. autoclass:: resdk.tables.rna.RNATables
   :members:

.. autoclass:: resdk.tables.methylation.MethylationTables
   :members:

"""
from .methylation import MethylationTables  # noqa
from .microarray import MATables  # noqa
from .rna import RNATables  # noqa

__all__ = (
    "MATables",
    "MethylationTables",
    "RNATables",
)
