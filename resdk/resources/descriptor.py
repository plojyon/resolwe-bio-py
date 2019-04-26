"""Process resource."""
import logging

from .base import BaseResolweResource


class DescriptorSchema(BaseResolweResource):
    """Resolwe DescriptorSchema resource.

    One and only one of the identifiers (slug, id or model_data)
    should be given.

    :param resolwe: Resolwe instance
    :type resolwe: Resolwe object
    :param model_data: Resource model data

    """

    endpoint = "descriptorschema"

    READ_ONLY_FIELDS = BaseResolweResource.READ_ONLY_FIELDS + (
        'schema',
    )
    WRITABLE_FIELDS = BaseResolweResource.WRITABLE_FIELDS + (
        'description',
    )

    ALL_PERMISSIONS = ['view', 'edit', 'share', 'owner']

    def __init__(self, resolwe, **model_data):
        """Initialize attributes."""
        self.logger = logging.getLogger(__name__)

        #: description
        self.description = None
        #: schema
        self.schema = None

        super().__init__(resolwe, **model_data)
