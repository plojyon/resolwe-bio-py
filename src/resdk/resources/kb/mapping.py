"""KB mapping resource."""
from ..base import BaseResource


class Mapping(BaseResource):
    """Knowledge base Mapping resource."""

    endpoint = "kb.mapping.admin"
    query_endpoint = "kb.mapping.search"
    query_method = "POST"

    READ_ONLY_FIELDS = BaseResource.READ_ONLY_FIELDS + (
        "relation_type",
        "source_db",
        "source_id",
        "source_species",
        "target_db",
        "target_id",
        "target_species",
    )

    def __init__(self, resolwe, **model_data):
        """Initialize attributes."""
        # Relation type (crossdb, ortholog, transcript, ...)
        self.relation_type = None
        #: Source database
        self.source_db = None
        #: Source feature ID
        self.source_id = None
        #: Source feature species
        self.source_species = None
        #: Target database
        self.target_db = None
        #: Target feature ID
        self.target_id = None
        #: Target feature species
        self.target_species = None

        super().__init__(resolwe, **model_data)

    def __repr__(self):
        """Format mapping representation."""
        return "<Mapping source_db='{}' source_id='{}' target_db='{}' target_id='{}'>".format(
            self.source_db, self.source_id, self.target_db, self.target_id
        )
