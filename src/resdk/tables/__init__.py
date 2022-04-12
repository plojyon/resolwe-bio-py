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
from .ml_ready import MLTables  # noqa
from .rna import RNATables  # noqa
from .variant import VariantTables  # noqa

__all__ = (
    "MATables",
    "MLTables",
    "MethylationTables",
    "RNATables",
    "VariantTables",
)
