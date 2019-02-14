"""Prepare GEO."""
from __future__ import absolute_import, division, print_function, unicode_literals

import time

from resdk.resources.utils import get_resolwe, get_resource_collection, get_samples

__all__ = ('prepare_geo_chipseq', 'prepare_geo_rnaseq', 'prepare_geo')


def get_name_collection(collection_ids, res):
    """Get the ``name`` input for ``prepare_geo`` processes.

    This function returns collection name and collection id if there
    is only one element in 'collection_ids' (all the samples are in the
    same collection). Otherwise it returns current date as ``name``.

    :param set collection_ids: set of collection id's of samples
    :param res: Resolwe instance
    :type res: :class:`resdk.resolwe.Resolwe`

    """
    collection_ids = list(collection_ids)

    if len(collection_ids) == 1 and collection_ids[0]:
        collection = res.collection.get(collection_ids[0])
        name = collection.name
    else:
        collection = None
        name = time.strftime("%d-%m-%Y")

    return name, collection


def prepare_geo_chipseq(resource, name=None):
    """Run ``Prepare GEO - ChIP-Seq`` process on the resource.

    This method can be used to run ``Prepare GEO - ChIP-Seq`` process
    on a single collection or a list of samples.

    :param resource: resource on which prepare_geo_chipseq will be run
    :param str name: name of the prepare GEO tarball and table

    """
    reads = []
    macs = []

    samples = get_samples(resource)
    resolwe = get_resolwe(*samples)
    collection_ids = set()

    for sample in samples:
        reads.append(sample.get_reads().id)

        if sample.is_background:
            continue

        macs_list = sample.get_macs()
        if not macs_list:
            raise ValueError("Sample {} has no `macs` data object!".format(sample))
        elif len(macs_list) != 1:
            raise ValueError("Sample {} has more than one `macs` data objects!".format(sample))

        macs.append(macs_list[0].id)

        if sample.background:
            if sample.background not in samples:
                raise ValueError(
                    "Background of the sample {} cannot be found in the resource you provided: "
                    "{}!".format(sample, resource)
                )

        collection_ids.add(get_resource_collection(sample))

    auto_name, collection = get_name_collection(collection_ids, resolwe)

    inputs = {
        'reads': reads,
        'macs': macs,
        'name': name or auto_name,
    }
    geo = resolwe.get_or_run(slug='prepare-geo-chipseq', input=inputs)

    if collection:
        collection.add_data(geo)

    return geo


def prepare_geo_rnaseq(resource, name=None):
    """Run ``Prepare GEO - RNA-Seq`` process on the resource.

    This method can be used to run ``Prepare GEO - RNA-Seq`` process
    on a single collection or a list of samples.

    :param resource: resource on which prepare_geo_rnaseq will be run
    :param str name: name of the prepare GEO tarball and table

    """
    reads = []
    expressions = []

    samples = get_samples(resource)
    resolwe = get_resolwe(*samples)
    collection_ids = set()

    for sample in samples:
        reads.append(sample.get_reads().id)
        expressions.append(sample.get_expression().id)
        collection_ids.add(get_resource_collection(sample))

    auto_name, collection = get_name_collection(collection_ids, resolwe)

    inputs = {
        'reads': reads,
        'expressions': expressions,
        'name': name or auto_name,
    }
    geo = resolwe.get_or_run(slug='prepare-geo-rnaseq', input=inputs)

    if collection:
        collection.add_data(geo)

    return geo


def prepare_geo(resource, types=[], name=None):
    """Run several prepare geo functions on a resource.

    :param list types: list of sequencing types of the samples in the
        resource. If none are given, the function is run on all types.
        Options are: ChIP-Seq, RNA-Seq
    :param str name: name of the prepare GEO tarball and table

    """
    type_to_function = {
        'rna-seq': prepare_geo_rnaseq,
        'chip-seq': prepare_geo_chipseq,
    }

    results = []

    invalid_types = [type_ for type_ in types if type_ not in type_to_function.keys()]
    if invalid_types:
        raise ValueError(
            "Invalid types '{}', the following are supported: '{}'".format(
                "', '".join(invalid_types),
                "', '".join(type_to_function.keys()),
            )
        )

    if not types:
        types = type_to_function.keys()

    for seq_type in types:
        result = type_to_function[seq_type.lower()](resource, name)
        results.append(result)

    return results
