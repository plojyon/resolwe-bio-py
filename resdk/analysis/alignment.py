"""Alignment analysis."""
from resdk.resources.utils import get_data_id, get_samples

__all__ = ('bowtie2', 'hisat2')


def bowtie2(resource, genome, mode=None, speed=None, use_se=None, discordantly=None, rep_se=None,
            minins=None, maxins=None, trim_5=None, trim_3=None, trim_iter=None, trim_nucl=None,
            rep_mode=None, k_reports=None):
    """Run bowtie2 aligner on given resource.

    Align reads files of given resource to the given genome using the
    `Bowtie2`_ aligner. If reads were already aligned, existing objects
    will be returned.

    .. _Bowtie2:
        http://resolwe-bio.readthedocs.io/en/latest/catalog-definitions.html#process-alignment-bowtie2

    :param resource: resource of which reads will be aligned
    :param genome: data object with genome that will be used
    :type genome: `~resdk.resources.data.Data`
    :param str mode: alignment mode (options are: --end-to-end,
        --local), default is --end-to-end
    :param str speed: speed vs sensitivity (options are: --very-fast,
        --fast, --semsitive, --very-sensitive), default is --sensitive
    :param bool use_se: map as single-ended (for paired-end reads
        only), default is False
    :param bool discordantly: report discordantly matched read, default
        is True
    :param bool rep_se: report single ended, default is True
    :param int minins: minimum fragment length, default is 0
    :param int maxins: maximum fragment length, default is 500
    :param int trim_5: number of bases to trim from 5', default is 0
    :param int trim_3: number of bases to trim from 3', default is 0
    :param int trim_iter: number of iterations, default is 0
    :param int trim_nucl: number of bases to trim from 3' in each
        iteration, default is 2
    :param str rep_mode: report mode (options are: def, k, a), default
        is def
    :param int k_reports: number of reports (for -k mode only), default
        is 5

    """
    inputs = {'genome': get_data_id(genome)}

    if mode is not None:
        inputs['mode'] = mode

    if speed is not None:
        inputs['speed'] = speed

    if use_se is not None:
        inputs['use_se'] = use_se

    if discordantly is not None:
        inputs['discordantly'] = discordantly

    if rep_se is not None:
        inputs['rep_se'] = rep_se

    if minins is not None:
        inputs['minins'] = minins

    if maxins is not None:
        inputs['maxins'] = maxins

    if trim_5 is not None:
        inputs['trim_5'] = trim_5

    if trim_3 is not None:
        inputs['trim_3'] = trim_3

    if trim_iter is not None:
        inputs['trim_iter'] = trim_iter

    if trim_nucl is not None:
        inputs['trim_nucl'] = trim_nucl

    if rep_mode is not None:
        inputs['rep_mode'] = rep_mode

    if k_reports is not None:
        inputs['k_reports'] = k_reports

    results = []

    if not isinstance(resource, list):
        resource = [resource]

    for single_resource in resource:

        for sample in get_samples(single_resource):
            inputs['reads'] = sample.get_reads().id

            aligned = sample.resolwe.get_or_run(slug='alignment-bowtie2', input=inputs)
            sample.add_data(aligned)
            results.append(aligned)

    return results


def hisat2(resource, genome):
    """Run hisat2 aligner on given resource.

    Align reads files of given resource to the given genome using the
    `Hisat2`_ aligner. If reads were already aligned, existing objects
    will be returned.

    .. _Hisat2:
        http://resolwe-bio.readthedocs.io/en/latest/catalog-definitions.html#process-alignment-hisat2

    :param resource: resource of which reads will be aligned
    :param genome: data object with genome that will be used
    :type genome: `~resdk.resources.data.Data`

    """
    results = []

    if not isinstance(resource, list):
        resource = [resource]

    for single_resource in resource:

        for sample in get_samples(single_resource):
            inputs = {
                'reads': sample.get_reads().id,
                'genome': get_data_id(genome),
            }

            aligned = sample.resolwe.get_or_run(slug='alignment-hisat2', input=inputs)
            sample.add_data(aligned)
            results.append(aligned)

    return results
