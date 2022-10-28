""".. Ignore pydocstyle D400.

============
ReSDK Tables
============

Helper classes for aggregating collection data in tabular format.

Table classes
=============

.. autoclass:: resdk.tables.microarray.MATables
   :members:

   .. automethod:: __init__

.. autoclass:: resdk.tables.ml_ready.MLTables
   :members:

   .. automethod:: __init__

.. autoclass:: resdk.tables.rna.RNATables
   :members:

   .. automethod:: __init__

.. autoclass:: resdk.tables.methylation.MethylationTables
   :members:

   .. automethod:: __init__

.. autoclass:: resdk.tables.variant.VariantTables
   :members:

   .. automethod:: __init__

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
