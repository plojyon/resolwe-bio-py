"""Constants and abstract classes."""
import copy
import logging
import operator

from .permissions import PermissionsManager
from .utils import parse_resolwe_datetime


class BaseResource:
    """Abstract resource.

    One and only one of the identifiers (slug, id or model_data)
    should be given.

    :param resolwe: Resolwe instance
    :type resolwe: Resolwe object
    :param model_data: Resource model data

    """

    endpoint = None
    query_endpoint = None
    query_method = 'GET'
    full_search_paramater = None

    READ_ONLY_FIELDS = (
        'id',
    )
    UPDATE_PROTECTED_FIELDS = ()
    WRITABLE_FIELDS = ()

    ALL_PERMISSIONS = []  # override this in subclass

    def __init__(self, resolwe, **model_data):
        """Verify that only a single attribute of slug, id or model_data given."""
        self._original_values = {}

        self.api = operator.attrgetter(self.endpoint)(resolwe.api)
        self.resolwe = resolwe
        self.logger = logging.getLogger(__name__)

        #: unique identifier of an object
        self.id = None  # pylint: disable=invalid-name

        if model_data:
            self._update_fields(model_data)

    def fields(self):
        """Resource fields."""
        return self.READ_ONLY_FIELDS + self.UPDATE_PROTECTED_FIELDS + self.WRITABLE_FIELDS

    def _update_fields(self, payload):
        """Update fields of the local resource based on the server values.

        :param dict payload: Resource field values

        """
        self._original_values = copy.deepcopy(payload)
        for field_name in self.fields():
            setattr(self, field_name, payload.get(field_name, None))

    def update(self):
        """Update resource fields from the server."""
        response = self.api(self.id).get()
        self._update_fields(response)

    def _dehydrate_resources(self, obj):
        """Iterate through object and replace all objects with their ids."""
        # Prevent circular imports:
        from .descriptor import DescriptorSchema
        from .process import Process

        if isinstance(obj, DescriptorSchema) or isinstance(obj, Process):
            return obj.slug
        if isinstance(obj, BaseResource):
            return obj.id
        if isinstance(obj, list):
            return [self._dehydrate_resources(element) for element in obj]
        if isinstance(obj, dict):
            return {key: self._dehydrate_resources(value) for key, value in obj.items()}
        return obj

    def save(self):
        """Save resource to the server."""
        def field_changed(field_name):
            """Check if local field value is different from the server."""
            return getattr(self, field_name) != self._original_values.get(field_name, None)

        def assert_fields_unchanged(field_names):
            """Assert that fields in ``field_names`` were not changed."""
            changed_fields = [name for name in field_names if field_changed(name)]

            if changed_fields:
                msg = "Not allowed to change read only fields {}".format(', '.join(changed_fields))
                raise ValueError(msg)

        if self.id:  # update resource
            assert_fields_unchanged(self.READ_ONLY_FIELDS + self.UPDATE_PROTECTED_FIELDS)

            payload = {}
            for field_name in self.WRITABLE_FIELDS:
                if field_changed(field_name):
                    payload[field_name] = self._dehydrate_resources(getattr(self, field_name))

            if payload:
                response = self.api(self.id).patch(payload)
                self._update_fields(response)

        else:  # create resource
            assert_fields_unchanged(self.READ_ONLY_FIELDS)

            field_names = self.WRITABLE_FIELDS + self.UPDATE_PROTECTED_FIELDS
            payload = {field_name: self._dehydrate_resources(getattr(self, field_name))
                       for field_name in field_names if getattr(self, field_name) is not None}

            response = self.api.post(payload)
            self._update_fields(response)

    def delete(self, force=False):
        """Delete the resource object from the server.

        :param bool force: Do not trigger confirmation prompt. WARNING: Be
            sure that you really know what you are doing as deleted objects
            are not recoverable.

        """
        if force is not True:
            user_input = input('Do you really want to delete {}?[yN] '.format(self))

            if user_input.strip().lower() != 'y':
                return

        self.api(self.id).delete()

    def __setattr__(self, name, value):
        """Detect changes of read only fields.

        This method detects changes of scalar fields and references. A
        more comprehensive check is called before save.

        """
        if (hasattr(self, '_original_values')
                and name in self._original_values
                and name in self.READ_ONLY_FIELDS
                and value != self._original_values[name]):
            raise ValueError("Can not change read only field {}".format(name))

        super().__setattr__(name, value)

    def __eq__(self, obj):
        """Evaluate if objects are the same."""
        if (self.__class__ == obj.__class__ and self.resolwe.url == obj.resolwe.url
                and self.id == obj.id):
            return True
        else:
            return False


class BaseResolweResource(BaseResource):
    """Base class for Resolwe resources.

    One and only one of the identifiers (slug, id or model_data)
    should be given.

    :param resolwe: Resolwe instance
    :type resolwe: Resolwe object
    :param model_data: Resource model data

    """

    _permissions = None

    READ_ONLY_FIELDS = BaseResource.READ_ONLY_FIELDS + (
        'current_user_permissions', 'id', 'version',
    )
    WRITABLE_FIELDS = (
        'name', 'slug',
    )

    def __init__(self, resolwe, **model_data):
        """Initialize attributes."""
        self.logger = logging.getLogger(__name__)

        #: User object of the contributor (lazy loaded)
        self._contributor = None

        #: current user permissions
        self.current_user_permissions = None
        #: name of resource
        self.name = None
        #: human-readable unique identifier
        self.slug = None
        #: resource version
        self.version = None

        BaseResource.__init__(self, resolwe, **model_data)

    @property
    def permissions(self):
        """TODO."""
        if not self.id:
            raise ValueError('Instance must be saved before accessing `permissions` attribute.')
        if not self._permissions:
            self._permissions = PermissionsManager(
                self.ALL_PERMISSIONS,
                self.api(self.id),
                self.resolwe
            )

        return self._permissions

    @property
    def contributor(self):
        """Get contributor."""
        if self.id is None:
            raise ValueError('Instance must be saved before accessing `contributor` attribute.')
        if self._contributor is None:
            contributor_data = self._original_values.get('contributor', {})
            try:
                self._contributor = self.resolwe.user.get(id=contributor_data.get('id'))
            except LookupError:
                from . import User
                # Normal user has only access to his user instance on user
                # endpoint. Instead of returning None for all other
                # contributors, data that is received in response is used to
                # populate User resource.
                self._contributor = User(
                    self.resolwe,
                    id=contributor_data.get('id'),
                    username=contributor_data.get('username'),
                    first_name=contributor_data.get('first_name'),
                    last_name=contributor_data.get('last_name'),
                )

        return self._contributor

    @property
    def created(self):
        """Creation time."""
        if not self.id:
            raise ValueError('Instance must be saved before acessing `created` attribute.')
        return parse_resolwe_datetime(self._original_values['created'])

    @property
    def modified(self):
        """Modification time."""
        if not self.id:
            raise ValueError('Instance must be saved before acessing `modified` attribute.')
        return parse_resolwe_datetime(self._original_values['modified'])

    def update(self):
        """Clear permissions cache and update the object."""
        self.permissions.clear_cache()

        super().update()

    def __repr__(self):
        """Format resource name."""
        return "{} <id: {}, slug: '{}', name: '{}'>".format(
            self.__class__.__name__, self.id, self.slug, self.name
        )
