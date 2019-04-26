"""Differential expressions analysis."""
from resdk.resources.utils import (
    get_data_id, get_resolwe, get_resource_collection, get_samples, is_collection, is_relation,
)

__all__ = ('cuffdiff', )


def cuffdiff(resource, annotation, genome=None, multi_read_correct=None, fdr=None,
             library_type=None, library_normalization=None, dispersion_method=None):
    """Run Cuffdiff_ for selected cuffquants.

    This method runs `Cuffdiff`_ process with ``annotation`` specified
    in arguments. Library type is by defalt fr-unstranded. Other parameters
    defaults: multi_read_correct=false, fdr=0.05, library_normalization=geometric,
    dispersion_method=pooled, threads=1. Parameter genome is optional.

    The way the function works depends on the resource. If it is run on a collection,
    it will perform cuffdiff on every 'compare' relation labeled 'case-control' in
    the selected collection. If it is run on a list of samples (not necesssarily in
    the same collection) it will run cuffdiff on all 'compare' relations labeled
    'case-control' containing all of the given samples but will discard those
    samples in a relation that are not in the list of samples.

    .. _Cuffdiff:
        http://resolwe-bio.readthedocs.io/en/latest/catalog-definitions.html#process-cuffdiff

    :param annotation: annotation file
    :type annotation: `~resdk.resources.data.Data`
    :param genome: genome object to use for bias detection and
        correction algorithm
    :type genome: `~resdk.resources.data.Data`
    :param bool multi_read_correct: do initial estimation procedure to
        more accurately weight reads with multiple genome mappings
    :param fdr: the allowed false discovery rate
    :type fdr: decimal
    :param str library_type: options are: fr-unstranded, fr-firststrand,
        fr-secondstrand
    :param str library_normalization: options are: geometric, classic-fpkm,
        quartile
    :param str dispersion_method: options are: pooled, per-condition,
        blind, poisson

    """
    inputs = {'annotation': get_data_id(annotation)}

    input_objects = [annotation]

    if genome is not None:
        inputs['genome'] = genome.id
        input_objects.append(genome)

    if multi_read_correct is not None:
        inputs['multi_read_correct'] = multi_read_correct

    if fdr is not None:
        inputs['fdr'] = fdr

    if library_type is not None:
        inputs['library_type'] = library_type

    if library_normalization is not None:
        inputs['library_normalization'] = library_normalization

    if dispersion_method is not None:
        inputs['dispersion_method'] = dispersion_method

    samples = get_samples(resource)
    sample_ids = [sample.id for sample in samples]

    input_objects.extend(samples)
    resolwe = get_resolwe(*input_objects)

    collection_id = get_resource_collection(resource)

    relation_filter = {}
    if collection_id:
        relation_filter['collection'] = collection_id
    else:
        relation_filter['entity'] = sample_ids

    relations = resolwe.relation.filter(
        type='compare',
        **relation_filter
    )

    cuffdiff_objects = []
    for relation in relations:
        control = []
        case = []
        for partition in relation.partitions:
            sample = resolwe.sample.get(partition['entity'])
            label = partition['label']
            if sample.id not in sample_ids:
                continue

            if label == 'case':
                case.append(get_data_id(sample.get_cuffquant()))
            elif label == 'control':
                control.append(get_data_id(sample.get_cuffquant()))
            else:
                raise ValueError(
                    "Label different from 'case' or 'control' was found in the "
                    "following relation: {}".format(relation.id)
                )

        if not case or not control:
            continue

        inputs['case'] = case
        inputs['control'] = control

        cuffdiff_obj = resolwe.get_or_run(slug='cuffdiff', input=inputs)
        cuffdiff_objects.append(cuffdiff_obj)

        if is_collection(resource):
            resource.add_data(cuffdiff_obj)
        elif is_relation(resource):
            resource.collection.add_data(cuffdiff_obj)

    if not cuffdiff_objects:
        if not relations:
            raise ValueError("No relation containing all of the given samples was found")
        else:
            raise ValueError(
                "No suitable relation was found (given samples all have either 'case' label "
                "or 'control' label"
            )

    return cuffdiff_objects
