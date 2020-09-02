"""Relation resource."""
import logging

from resdk.exceptions import ValidationError

from .base import BaseResolweResource
from .collection import Collection
from .utils import get_sample_id


class Relation(BaseResolweResource):
    """Resolwe Relation resource.

    :param resolwe: Resolwe instance
    :type resolwe: Resolwe object
    :param model_data: Resource model data

    """

    endpoint = "relation"

    UPDATE_PROTECTED_FIELDS = BaseResolweResource.UPDATE_PROTECTED_FIELDS + ("type",)
    WRITABLE_FIELDS = BaseResolweResource.WRITABLE_FIELDS + (
        "collection",
        "category",
        "partitions",
        "unit",
    )

    def __init__(self, resolwe, **model_data):
        """Initialize attributes."""
        self.logger = logging.getLogger(__name__)

        #: Collection in which relation is
        self._collection = None
        #: List of samples in the relation
        self._samples = None

        #: list of ``RelationPartition`` objects in the ``Relation``
        self.partitions = None
        #: type of the relation
        self.type = None
        #: category of the relation
        self.category = None
        #: unit (where applicable, e.g. for serieses)
        self.unit = None

        super().__init__(resolwe, **model_data)

    @property
    def samples(self):
        """Return list of sample objects in the relation."""
        if not self._samples:
            if not self.partitions:
                self._samples = []
            else:
                sample_ids = [partition["entity"] for partition in self.partitions]
                self._samples = self.resolwe.sample.filter(id__in=sample_ids)
                # Samples should be sorted, so they have same order as positions
                # XXX: This may be slow for many samples in single collection
                self._samples = sorted(
                    self._samples, key=lambda sample: sample_ids.index(sample.id)
                )
        return self._samples

    @property
    def collection(self):
        """Return collection object to which relation belongs."""
        if not self._collection:
            self._collection = self.resolwe.collection.get(
                self._original_values.get("colection", None)
            )
        return self._collection

    @collection.setter
    def collection(self, payload):
        """Set collection to which relation belongs."""
        self._resource_setter(payload, Collection, "_collection")

    def update(self):
        """Clear cache and update resource fields from the server."""
        self._samples = None

        super().update()

    def add_sample(self, sample, label=None, position=None):
        """Add ``sample`` object to relation."""
        self.partitions.append(
            {
                "entity": sample.id,
                "position": position,
                "label": label,
            }
        )
        self.save()
        self._samples = None

    def remove_samples(self, *samples):
        """Remove ``sample`` objects from relation."""
        sample_ids = [get_sample_id(sample) for sample in samples]
        self.partitions = [
            partition
            for partition in self.partitions
            if partition["entity"] not in sample_ids
        ]
        self.save()
        self._samples = None

    def save(self):
        """Check that collection is saved and save instance."""
        if self._collection is None:
            # `save` fails in an ugly way if collection is not set
            raise ValidationError("`collection` attribute is required.")

        super().save()

    def __repr__(self):
        """Format relation name."""
        sample_info = []
        for sample, partition in zip(self.samples, self.partitions):
            name = sample.name
            label = partition.get("label", None)
            position = partition.get("position", None)

            if label and position:
                sample_info.append(
                    "{} ({} {}): {}".format(label, position, self.unit, name)
                )
            elif partition["label"]:
                sample_info.append("{}: {}".format(label, name))
            elif partition["position"]:
                sample_info.append("{} {}: {}".format(position, self.unit, name))
            else:
                sample_info.append(name)

        return "{} id: {}, type: '{}', category: '{}', samples: {{{}}}".format(
            self.__class__.__name__,
            self.id,
            self.type,
            self.category,
            ", ".join(sample_info),
        )
