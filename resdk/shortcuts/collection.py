"""ReSDK Resolwe shortcuts."""
from __future__ import absolute_import, division, print_function, unicode_literals

from six.moves import zip_longest

from resdk.resources.utils import get_sample_id


class CollectionRelationsMixin(object):
    """Shortcuts mixin for ``Collection`` class.

    This is a collection of utility functions for managing relations on
    collection.
    """

    def _create_relation(self, relation_type, samples, positions=[], label=None):
        """Create group relation with the given samples and positions."""
        if not isinstance(samples, list):
            raise ValueError("`samples` argument must be list.")

        if not isinstance(positions, list):
            raise ValueError("`positions` argument must be list.")

        if positions:
            if len(samples) != len(positions):
                raise ValueError("`samples` and `positions` arguments must be of the same length.")

        relation_data = {
            'type': relation_type,
            'collection': self.id,
            'entities': []
        }

        for sample, position in zip_longest(samples, positions):
            entity_dict = {'entity': get_sample_id(sample)}
            if position:
                entity_dict['position'] = position

            relation_data['entities'].append(entity_dict)

        if label:
            relation_data['label'] = label

        return self.resolwe.relation.create(**relation_data)

    def _update_relation(self, id_, relation_type, samples, positions=[], label=None,
                         relation=None):
        """Update existing relation."""
        if relation is None:
            relation = self.resolwe.relation.get(id=id_)

        to_delete = copy.copy(relation.entities)
        to_add = []

        for sample, position in zip_longest(samples, positions):
            entity_obj = {'entity': sample, 'position': position}
            if entity_obj in relation.entities:
                to_delete.remove(entity_obj)
            else:
                to_add.append(entity_obj)

        if to_add:
            relation.add_sample(*to_add)

        if to_delete:
            relation.remove_samples(*[obj['entity'] for obj in to_delete])

        if label != relation.label:
            relation.label = label
            relation.save()

    def create_group_relation(self, samples, positions=[], label=None):
        """Create group relation.

        :param list samples: List of samples to include in relation.
        :param list position: List of optional positions assigned to the
            relations (i.e. ``first``, ``second``...). If given it shoud
            be of the same length as ``samples``.
        :param str label: Optional label of the relation (i.e.
            ``replicates``)
        """
        return self._create_relation('group', samples, positions, label)

    def create_compare_relation(self, samples, positions=[], label=None):
        """Create compare relation.

        :param list samples: List of samples to include in relation.
        :param list position: List of optional positions assigned to the
            relations (i.e. ``case``, ``control``...). If given it shoud
            be of the same length as ``samples``.
        :param str label: Optional label of the relation (i.e.
            ``case-control``)
        """
        return self._create_relation('compare', samples, positions, label)

    def create_series_relation(self, samples, positions=[], label=None):
        """Create series relation.

        :param list samples: List of samples to include in relation.
        :param list position: List of optional positions assigned to the
            relations (i.e. ``1``, ``2``...). If given it shoud be of
            the same length as ``samples``.
        :param str label: Optional label of the relation (i.e.
            ``time-series``)
        """
        return self._create_relation('series', samples, positions, label)

    def create_background_relation(self, sample, background):
        """Create compare relation with ``background`` label.

        Creates special compare relatio labeled with ``background`` abd
        containing two sampes tagged as ``sample`` and ``background``.

        :param sample: Sample
        :type sample: int or `~resdk.resources.sample.Sample`
        :param background: Background sample
        :type background: int or `~resdk.resources.sample.Sample`
        """
        return self.create_compare_relation(
            samples=[sample, background],
            positions=['sample', 'background'],
            label='background'
        )
