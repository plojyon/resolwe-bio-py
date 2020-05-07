"""Sample shortcuts."""


class SampleUtilsMixin:
    """Mixin with utility functions for `~resdk.resources.sample.Sample` resource.

    This mixin includes handy methods for common tasks like getting
    data object of specific type from sample (or list of them, based on
    common usecase) and running analysis on the objects in the sample.

    """

    def get_reads(self, **filters):
        """Return the latest ``fastq`` object in sample.

        If there are multiple ``fastq`` objects in sample (trimmed,
        filtered, subsampled...), return the latest one. If any other of
        the ``fastq`` objects is required, one can provide additional
        ``filter`` arguments and limits search to one result.
        """
        kwargs = {
            "process_type": "data:reads:fastq",
            "ordering": "-id",
        }
        kwargs.update(filters)

        reads = self.data.filter(**kwargs)
        # TODO: In future, implement method ``last()`` on ResolweQuery
        # and return the ResolweQuery object.

        if not reads:
            raise LookupError("Reads not found on sample {}.".format(self))
        else:
            return reads[0]

    def get_bam(self):
        """Return ``bam`` object on the sample."""
        return self.data.get(type="data:alignment:bam")

    def get_primary_bam(self, fallback_to_bam=False):
        """Return ``primary bam`` object on the sample.

        If the ``primary bam`` object is not present and
        ``fallback_to_bam`` is set to ``True``, a ``bam`` object will
        be returned.

        """
        try:
            return self.data.get(type="data:alignment:bam:primary")
        except LookupError:
            if fallback_to_bam:
                return self.get_bam()
            else:
                raise

    def get_macs(self):
        """Return list of ``bed`` objects on the sample."""
        return self.data.filter(type="data:chipseq:callpeak:macs14")

    def get_cuffquant(self):
        """Return ``cuffquant`` object on the sample."""
        return self.data.get(type="data:cufflinks:cuffquant")

    def get_expression(self):
        """Return ``expression`` object on the sample."""
        return self.data.get(type="data:expression:")
