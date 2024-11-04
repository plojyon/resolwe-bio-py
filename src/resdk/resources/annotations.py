"""Annotatitons resources."""

import logging
from typing import TYPE_CHECKING, Optional, Union

from ..utils.decorators import assert_object_exists
from .base import BaseResource
from .sample import Sample
from .utils import parse_resolwe_datetime

if TYPE_CHECKING:
    from resdk.resolwe import Resolwe


class AnnotationGroup(BaseResource):
    """Resolwe AnnotationGroup resource."""

    # There is currently no endpoint for AnnotationGroup object, but it might be
    # created in the future. The objects are created when AnnotationField is
    # initialized.
    endpoint = "annotation_group"

    READ_ONLY_FIELDS = BaseResource.READ_ONLY_FIELDS + ("name", "sort_order", "label")

    def __init__(self, resolwe: "Resolwe", **model_data):
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
        "vocabulary",
        "required",
        "version",
    )

    def __init__(self, resolwe: "Resolwe", **model_data):
        """Initialize the instance.

        :param resolwe: Resolwe instance
        :param model_data: Resource model data
        """
        self.logger = logging.getLogger(__name__)
        #: annotation group
        self._group = None
        super().__init__(resolwe, **model_data)

    @property
    def group(self) -> AnnotationGroup:
        """Get annotation group."""
        assert (
            self._group is not None
        ), "AnnotationGroup must be set before it can be used."
        return self._group

    @group.setter
    def group(self, payload: dict):
        """Set annotation group."""
        if self._group is None:
            self._resource_setter(payload, AnnotationGroup, "_group")
        else:
            raise AttributeError("AnnotationGroup is read-only.")

    def __repr__(self):
        """Return user friendly string representation."""
        return f"AnnotationField <path: {self.group.name}.{self.name}>"

    def __str__(self):
        """Return full path of the annotation field."""
        return f"{self.group.name}.{self.name}"


class AnnotationValue(BaseResource):
    """Resolwe AnnotationValue resource."""

    endpoint = "annotation_value"

    READ_ONLY_FIELDS = BaseResource.READ_ONLY_FIELDS + ("label",)

    UPDATE_PROTECTED_FIELDS = BaseResource.UPDATE_PROTECTED_FIELDS + ("field", "sample")

    WRITABLE_FIELDS = BaseResource.WRITABLE_FIELDS + ("value",)

    def __init__(self, resolwe: "Resolwe", **model_data):
        """Initialize the instance.

        :param resolwe: Resolwe instance
        :param model_data: Resource model data
        """
        self.logger = logging.getLogger(__name__)

        #: annotation field
        self._field: Optional[AnnotationField] = None
        self.field_id: Optional[int] = None

        #: sample
        self.sample_id: Optional[int] = None
        self._sample: Optional[Sample] = None
        super().__init__(resolwe, **model_data)

    @property
    @assert_object_exists
    def modified(self):
        """Modification time."""
        return parse_resolwe_datetime(self._original_values["modified"])

    @property
    def sample(self):
        """Get sample."""
        if self._sample is None:
            if self.sample_id is None:
                self.sample_id = self._original_values["entity"]
            self._sample = Sample(resolwe=self.resolwe, id=self.sample_id)
            # Without this save will fail due to change in read-only field.
            self._original_values["sample"] = {"id": self.sample_id}
        return self._sample

    @sample.setter
    def sample(self, payload):
        """Set the sample."""
        # Update fields sets sample to None.
        if payload is None:
            return
        if self.sample_id is not None:
            raise AttributeError("Sample is read-only.")
        if isinstance(payload, Sample):
            self.sample_id = payload.id
        elif isinstance(payload, dict):
            self.sample_id = payload["id"]
        else:
            self.sample_id = payload

    @property
    def field(self) -> AnnotationField:
        """Get annotation field."""
        if self._field is None:
            assert (
                self.field_id is not None
            ), "AnnotationField must be set before it can be used."
            self._field = self.resolwe.annotation_field.get(id=self.field_id)
            # The field is read-only but we have to modify original values here so save
            # can detect there were no changes.
            self._original_values["field"] = self._field._original_values
        return self._field

    @field.setter
    def field(self, payload: Union[int, AnnotationField, dict]):
        """Set annotation field."""
        field_id = None
        if isinstance(payload, int):
            field_id = payload
        elif isinstance(payload, dict):
            field_id = payload["id"]
        elif isinstance(payload, AnnotationField):
            field_id = payload.id
        if field_id != self.field_id:
            self._field = None
            self.field_id = field_id

    def __repr__(self):
        """Format resource name."""
        return f"AnnotationValue <path: {self.field.group.name}.{self.field.name}, value: '{self.value}'>"
