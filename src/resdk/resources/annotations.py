"""Annotatitons resources."""

import logging
from typing import TYPE_CHECKING

from .base import BaseResource
from .sample import Sample

if TYPE_CHECKING:
    from resdk.resolwe import Resolwe


class AnnotationGroup(BaseResource):
    """Resolwe AnnotationGroup resource."""

    # There is currently no endpoint for AnnotationGroup object, but it might be
    # created in the future. The objects are created when AnnotationField is
    # initialized.
    endpoint = "annotation_group"

    READ_ONLY_FIELDS = BaseResource.READ_ONLY_FIELDS + ("name", "sort_order", "label")

    def __init__(self, resolwe: "Resolwe", **model_data: dict):
        """Initialize the instance.
        :param resolwe: Resolwe instance
        :param model_data: Resource model data
        """
        self.logger = logging.getLogger(__name__)
        super().__init__(resolwe, **model_data)

    def __repr__(self):
        """Return user friendly string representation."""
        return f"AnnotationGroup <name: {self.name}>"


class AnnotationField(BaseResource):
    """Resolwe AnnotationField resource."""

    endpoint = "annotation_field"

    READ_ONLY_FIELDS = BaseResource.READ_ONLY_FIELDS + (
        "description",
        "group",
        "label",
        "name",
        "sort_order",
        "type",
        "validator_regex",
        "vocubalary",
        "required",
    )

    def __init__(self, resolwe: "Resolwe", **model_data: dict):
        """Initialize the instance.
        :param resolwe: Resolwe instance
        :param model_data: Resource model data
        """
        self.logger = logging.getLogger(__name__)
        #: annotation group
        self._group = None
        super().__init__(resolwe, **model_data)

    @property
    def group(self):
        """Get annotation group."""
        return self._group

    @group.setter
    def group(self, payload):
        """Set annotation group."""
        self._resource_setter(payload, AnnotationGroup, "_group")

    def __repr__(self):
        """Return user friendly string representation."""
        return f"AnnotationField <path: {self.group.name}.{self.name}>"

    def __str__(self):
        """Return full path of the annotation field."""
        return f"{self.group.name}.{self.name}"


class AnnotationValue(BaseResource):
    """Resolwe AnnotationValue resource."""

    endpoint = "annotation_value"

    READ_ONLY_FIELDS = BaseResource.READ_ONLY_FIELDS + (
        "field",
        "entity",
        "value",
        "label",
    )

    UPDATE_PROTECTED_FIELDS = BaseResource.UPDATE_PROTECTED_FIELDS + ("sample", "field")

    WRITABLE_FIELDS = BaseResource.WRITABLE_FIELDS + ("value",)

    def __init__(self, resolwe: "Resolwe", **model_data):
        """Initialize the instance.
        :param resolwe: Resolwe instance
        :param model_data: Resource model data
        """
        self.logger = logging.getLogger(__name__)

        #: annotation field
        self._field = None
        self.field_id = None

        #: sample
        self._sample = None

        super().__init__(resolwe, **model_data)

    @property
    def sample(self):
        """Get sample."""
        return Sample(resolwe=self.resolwe, id=self._original_values["entity"])

    @property
    def field(self):
        """Get annotation field."""
        if self._field is None:
            assert (
                self.field_id is not None
            ), "AnnotationField must be set before it can be used."
            self._field = AnnotationField(self.resolwe, id=self.field_id)
        return self._field

    @field.setter
    def field(self, payload):
        """Set annotation field."""
        self.field_id = payload

    def __repr__(self):
        """Format resource name."""
        return f"AnnotationValue <path: {self.field.group.name}.{self.field.name}, value: '{self.value}'>"
