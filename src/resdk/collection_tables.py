"""CollectionTables."""
import warnings

from .tables import RNATables


class CollectionTables(RNATables):
    """CollectionTables."""

    def __init__(self, *args, **kwargs):
        """Initialize."""
        warnings.warn(
            "resdk.CollectionTables will be deprecated in November 2021."
            "Please use resdk.tables.RNATables instead."
        )
        return super().__init__(*args, **kwargs)
