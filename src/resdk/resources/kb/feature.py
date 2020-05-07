"""KB feature resource."""
from ..base import BaseResource


class Feature(BaseResource):
    """Knowledge base Feature resource."""

    endpoint = "kb.feature.admin"
    query_endpoint = "kb.feature.search"
    query_method = "POST"

    READ_ONLY_FIELDS = BaseResource.READ_ONLY_FIELDS + (
        "aliases",
        "description",
        "feature_id",
        "full_name",
        "name",
        "source",
        "species",
        "sub_type",
        "type",
    )

    def __init__(self, resolwe, **model_data):
        """Initialize attributes."""
        #: Aliases
        self.aliases = None
        #: Description
        self.description = None
        #: Feature ID
        self.feature_id = None
        #: Full name
        self.full_name = None
        #: Name
        self.name = None
        #: Source
        self.source = None
        #: Species
        self.species = None
        #: Feature subtype (tRNA, protein coding, rRNA, ...)
        self.sub_type = None
        #: Feature type (gene, transcript, exon, ...)
        self.type = None

        super().__init__(resolwe, **model_data)

    def __repr__(self):
        """Format feature representation."""
        return "<Feature source='{}' feature_id='{}'>".format(
            self.source, self.feature_id
        )
