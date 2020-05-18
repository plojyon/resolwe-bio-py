"""Process resource."""
import logging

from .base import BaseResolweResource
from .utils import _print_input_line


class Process(BaseResolweResource):
    """Resolwe Process resource.

    :param resolwe: Resolwe instance
    :type resolwe: Resolwe object
    :param model_data: Resource model data

    """

    endpoint = "process"
    READ_ONLY_FIELDS = BaseResolweResource.READ_ONLY_FIELDS + ("is_active",)
    UPDATE_PROTECTED_FIELDS = BaseResolweResource.UPDATE_PROTECTED_FIELDS + (
        "category",
        "data_name",
        "description",
        "entity_always_create",
        "entity_descriptor_schema",
        "entity_input",
        "entity_type",
        "input_schema",
        "output_schema",
        "persistence",
        "requirements",
        "run",
        "scheduling_class",
        "type",
    )

    all_permissions = ["view", "share", "owner"]

    def __init__(self, resolwe, **model_data):
        """Initialize attributes."""
        self.logger = logging.getLogger(__name__)

        self.data_name = None
        """
        the default name of data object using this process. When data object
        is created you can assign a name to it. But if you don't, the name of
        data object is determined from this field. The field is a expression
        which can take values of other fields.
        """
        #: the type of process ``"type:sub_type:sub_sub_type:..."``
        self.type = None
        #: entity_always_create
        self.entity_always_create = None
        #: entity_descriptor_schema
        self.entity_descriptor_schema = None
        #: entity_input
        self.entity_input = None
        #: entity_type
        self.entity_type = None
        #: used to group processes in a GUI. Examples: ``upload:``, ``analyses:variants:``, ...
        self.category = None
        self.persistence = None
        """
        Measure of how important is to keep the process outputs when
        optimizing disk usage. Options: RAW/CACHED/TEMP. For processes, used
        on frontend use TEMP - the results of this processes can be quickly
        re-calculated any time. For upload processes use RAW - this data
        should never be deleted, since it cannot be re-calculated. For
        analysis use CACHED - the results can stil be calculated from
        imported data but it can take time.
        """
        #: process priority - not used yet
        self.priority = None
        #: process description
        self.description = None
        #: specifications of inputs
        self.input_schema = None
        #: specification of outputs
        self.output_schema = None
        #: the heart of process - here the algorithm is defined.
        self.run = None
        #: required Docker image, amount of memory / CPU ...
        self.requirements = None
        #: Scheduling class
        self.scheduling_class = None
        #: Boolean stating wether process is active
        self.is_active = None

        super().__init__(resolwe, **model_data)

    def print_inputs(self):
        """Pretty print input_schema."""
        _print_input_line(self.input_schema, 0)
