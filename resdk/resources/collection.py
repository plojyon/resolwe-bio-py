"""Collection resources."""
from __future__ import absolute_import, division, print_function, unicode_literals

import logging

import six

from resdk.shortcuts.collection import CollectionRelationsMixin

from .base import BaseResolweResource
from .descriptor import DescriptorSchema
from .utils import get_data_id, get_descriptor_schema_id, get_sample_id, is_descriptor_schema


class BaseCollection(BaseResolweResource):
    """Abstract collection resource.

    One and only one of the identifiers (slug, id or model_data)
    should be given.

    :param resolwe: Resolwe instance
    :type resolwe: Resolwe object
    :param model_data: Resource model data

    """

    full_search_paramater = 'text'

    WRITABLE_FIELDS = BaseResolweResource.WRITABLE_FIELDS + (
        'description', 'descriptor', 'descriptor_schema', 'settings', 'tags',
    )

    ALL_PERMISSIONS = ['view', 'download', 'add', 'edit', 'share', 'owner']

    def __init__(self, resolwe, **model_data):
        """Initialize attributes."""
        self.logger = logging.getLogger(__name__)

        #: list of Data objects in collection (lazy loaded)
        self._data = None
        #: ``DescriptorSchema`` id of a resource object
        self._descriptor_schema = None
        #: ``DescriptorSchema`` of a resource object
        self._hydrated_descriptor_schema = None

        #: description
        self.description = None
        #: descriptor
        self.descriptor = None
        #: settings
        self.settings = None
        #: tags
        self.tags = None

        super(BaseCollection, self).__init__(resolwe, **model_data)

    @property
    def data(self):
        """Return list of attached Data objects."""
        raise NotImplementedError('This should be implemented in subclass')

    @property
    def descriptor_schema(self):
        """Return descriptor schema assigned to the data object."""
        if self._descriptor_schema is None:
            return None

        if self._hydrated_descriptor_schema is None:
            if isinstance(self._descriptor_schema, int):
                query_filters = {'id': self._descriptor_schema}
            else:
                query_filters = {'slug': self._descriptor_schema}

            self._hydrated_descriptor_schema = self.resolwe.descriptor_schema.get(
                ordering='-version', limit=1, **query_filters
            )

        return self._hydrated_descriptor_schema

    @descriptor_schema.setter
    def descriptor_schema(self, dschema):
        """Set collection to which relation belongs."""
        # On single data object endpoint descriptor schema is already
        # hidrated, so it should be transformed into resource.
        if isinstance(dschema, dict):
            dschema = DescriptorSchema(resolwe=self.resolwe, **dschema)

        self._descriptor_schema = get_descriptor_schema_id(dschema)
        # Save descriptor schema if already hydrated, otherwise it will be rerived in getter
        self._hydrated_descriptor_schema = dschema if is_descriptor_schema(dschema) else None

    def update(self):
        """Clear cache and update resource fields from the server."""
        self._data = None
        self._hydrated_descriptor_schema = None

        super(BaseCollection, self).update()

    def _clear_data_cache(self):
        """Clear data cache."""
        self._data = None

    def add_data(self, *data):
        """Add ``data`` objects to the collection."""
        data = [get_data_id(d) for d in data]
        self.api(self.id).add_data.post({'ids': data})
        self._clear_data_cache()

    def remove_data(self, *data):
        """Remove ``data`` objects from the collection."""
        data = [get_data_id(d) for d in data]
        self.api(self.id).remove_data.post({'ids': data})
        self._clear_data_cache()

    def data_types(self):
        """Return a list of data types (process_type).

        :rtype: List

        """
        process_types = set(self.resolwe.api.data(id_).get()['process_type'] for id_ in self.data)
        return sorted(process_types)

    def files(self, file_name=None, field_name=None):
        """Return list of files in resource."""
        file_list = []
        for data in self.data:
            file_list.extend(fname for fname in data.files(file_name=file_name,
                                                           field_name=field_name))

        return file_list

    def download(self, file_name=None, field_name=None, download_dir=None):
        """Download output files of associated Data objects.

        Download files from the Resolwe server to the download
        directory (defaults to the current working directory).

        :param file_name: name of file
        :type file_name: string
        :param field_name: field name
        :type field_name: string
        :param download_dir: download path
        :type download_dir: string
        :rtype: None

        Collections can contain multiple Data objects and Data objects
        can contain multiple files. All files are downloaded by default,
        but may be filtered by file name or Data object type:

        * re.collection.get(42).download(file_name='alignment7.bam')
        * re.collection.get(42).download(data_type='bam')

        """
        files = []

        if field_name and not isinstance(field_name, six.string_types):
            raise ValueError("Invalid argument value `field_name`.")

        for data in self.data:
            data_files = data.files(file_name, field_name)
            files.extend('{}/{}'.format(data.id, file_name) for file_name in data_files)

        self.resolwe._download_files(files, download_dir)  # pylint: disable=protected-access


class Collection(CollectionRelationsMixin, BaseCollection):
    """Resolwe Collection resource.

    One and only one of the identifiers (slug, id or model_data)
    should be given.

    :param resolwe: Resolwe instance
    :type resolwe: Resolwe object
    :param model_data: Resource model data

    """

    endpoint = 'collection'

    def __init__(self, resolwe, **model_data):
        """Initialize attributes."""
        self.logger = logging.getLogger(__name__)

        #: list of ``Sample`` objects in ``Collection`` (lazy loaded)
        self._samples = None
        #: list of ``Relation`` objects in ``Collection`` (lazy loaded)
        self._relations = None

        super(Collection, self).__init__(resolwe, **model_data)

    def update(self):
        """Clear cache and update resource fields from the server."""
        self._samples = None
        self._relations = None

        super(Collection, self).update()

    @property
    def data(self):
        """Return list of data objects on collection."""
        if self.id is None:
            raise ValueError('Instance must be saved before accessing `data` attribute.')
        if self._data is None:
            self._data = self.resolwe.data.filter(collection=self.id)

        return self._data

    @property
    def samples(self):
        """Return list of samples on collection."""
        if self.id is None:
            raise ValueError('Instance must be saved before accessing `samples` attribute.')
        if self._samples is None:
            self._samples = self.resolwe.sample.filter(collections=self.id)

        return self._samples

    @property
    def relations(self):
        """Return list of data objects on collection."""
        if self.id is None:
            raise ValueError('Instance must be saved before accessing `relations` attribute.')
        if self._relations is None:
            self._relations = self.resolwe.relation.filter(collection=self.id)

        return self._relations

    def add_samples(self, *samples):
        """Add `samples` objects to the collection."""
        samples = [get_sample_id(s) for s in samples]
        # XXX: Make in one request when supported on API
        for sample in samples:
            self.resolwe.api.sample(sample).add_to_collection.post({'ids': [self.id]})

        self.samples.clear_cache()

    def remove_samples(self, *samples):
        """Remove ``sample`` objects from the collection."""
        samples = [get_sample_id(s) for s in samples]
        # XXX: Make in one request when supported on API
        for sample in samples:
            self.resolwe.api.sample(sample).remove_from_collection.post({'ids': [self.id]})

        self.samples.clear_cache()
