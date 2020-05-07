"""Process resource."""
import logging

from .base import BaseResolweResource


class DescriptorSchema(BaseResolweResource):
    """Resolwe DescriptorSchema resource.

    :param resolwe: Resolwe instance
    :type resolwe: Resolwe object
    :param model_data: Resource model data

    """

    endpoint = "descriptorschema"

    READ_ONLY_FIELDS = BaseResolweResource.READ_ONLY_FIELDS + ("schema",)
    WRITABLE_FIELDS = BaseResolweResource.WRITABLE_FIELDS + ("description",)

    def __init__(self, resolwe, **model_data):
        """Initialize attributes."""
        self.logger = logging.getLogger(__name__)

        #: description
        self.description = None
        #: schema
        self.schema = None

        super().__init__(resolwe, **model_data)
