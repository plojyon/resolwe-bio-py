"""KB feature resource."""
from __future__ import absolute_import, division, print_function, unicode_literals

from ..base import BaseResource


class Feature(BaseResource):
    """Knowledge base Feature resource."""

    endpoint = 'kb.feature.admin'
    query_endpoint = 'kb.feature.search'
    query_method = 'POST'

    WRITABLE_FIELDS = BaseResource.WRITABLE_FIELDS + (
        'aliases', 'description', 'feature_id', 'full_name', 'name', 'species', 'source',
        'sub_type', 'type',
    )
    UPDATE_PROTECTED_FIELDS = BaseResource.WRITABLE_FIELDS + (
        'feature_id', 'source',
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
        #: Feature type (gene, transcript, exon, ...)
        self.type = None
        #: Feature subtype (tRNA, protein coding, rRNA, ...)
        self.sub_type = None

        super(Feature, self).__init__(resolwe, **model_data)

    def __repr__(self):
        """Format feature representation."""
        # pylint: disable=no-member
        return "<Feature source='{}' feature_id='{}'>".format(self.source, self.feature_id)
