"""Expressions analysis."""
from __future__ import absolute_import, division, print_function, unicode_literals

from resdk.resources.utils import (
    get_data_id, get_resolwe, get_resource_collection, get_samples, is_collection, is_relation,
)

__all__ = ('cuffquant', 'cuffnorm')


def cuffquant(resource, annotation, genome=None, mask_file=None,
              library_type=None, multi_read_correct=None):
    """Run Cuffquant_ for selected cuffquats.

    This method runs `Cuffquant`_ process with ``annotation`` specified
    in arguments. Library type is by defalt fr-unsstranded. Other
    parameters: genome, mask_file and multi_reads_correct are optional.

    .. _Cuffquant:
        http://resolwe-bio.readthedocs.io/en/latest/catalog-definitions.html#process-cuffquant

    :param annotation: annotation file
    :type annotation: `~resdk.resources.data.Data`
    :param genome: genome object to use for bias detection and
        correction algorithm
    :type genome: `~resdk.resources.data.Data`
    :param mask_file: mask file to use in process
    :type mask_file: `~resdk.resources.data.Data`
    :param str library_type: options are: fr-unstranded, fr-firststrand,
        fr-secondstrand
    :param bool multi_read_correct: do initial estimation procedure to
        more accurately weight reads with multiple genome mappings

    """
    results = []
    for sample in get_samples(resource):
        inputs = {
            'alignment': sample.get_bam().id,
            'annotation': get_data_id(annotation),
        }

        if genome is not None:
            inputs['genome'] = genome

        if mask_file is not None:
            inputs['mask_file'] = mask_file

        if library_type is not None:
            inputs['library_type'] = library_type

        if multi_read_correct is not None:
            inputs['multi_read_correct'] = multi_read_correct

        cuffquant_obj = sample.resolwe.get_or_run(slug='cuffquant', input=inputs)
        sample.add_data(cuffquant_obj)
        results.append(cuffquant_obj)

    return results


def cuffnorm(resource, annotation, use_ercc=None):
    """Run Cuffnorm_ for selected cuffquats.

    This method runs `Cuffnorm`_ process on ``resource`` with
    ``annotation`` and ``use_ercc`` parameters specified in arguments.

    .. _Cuffnorm:
        http://resolwe-bio.readthedocs.io/en/latest/catalog-definitions.html#process-upload-expression-cuffnorm

    :param resource: resource on which cuffnorm will be run
    :param annotation: annotation object used in cuffnorm
    :type annotation: `~resdk.resources.data.Data`
    :param bool use_ercc: use ERRCC spike-in controls for normalization

    """
    relation_filter = {}
    collection_id = get_resource_collection(resource)
    if collection_id:
        relation_filter['collection'] = collection_id

    samples = get_samples(resource)

    input_objects = [annotation]
    input_objects.extend(samples)
    resolwe = get_resolwe(*input_objects)

    cuffquants = [get_data_id(sample.get_cuffquant()) for sample in samples]

    inputs = {
        'cuffquant': cuffquants,
        'annotation': get_data_id(annotation),
    }

    if use_ercc is not None:
        inputs['useERCC'] = use_ercc

    cuffnorm_obj = resolwe.get_or_run(slug='cuffnorm', input=inputs)

    if is_collection(resource):
        resource.add_data(cuffnorm_obj)
    elif is_relation(resource):
        resource.collection.add_data(cuffnorm_obj)

    return cuffnorm_obj
