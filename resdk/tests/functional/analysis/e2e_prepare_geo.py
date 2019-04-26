# pylint: disable=missing-docstring
from resdk.analysis import prepare_geo
from resdk.tests.functional.base import BaseResdkFunctionalTest


def change_samples(data1, data2):
    """Add data2 to data1's sample and remove data2's sample."""
    data2.sample.delete(force=True)
    data1.sample.add_data(data2)
    data1.sample.save()


class TestPrepareGeo(BaseResdkFunctionalTest):

    def test_prepare_geo_chipseq(self):
        collection_1 = self.res.collection.create(name='Test collection')
        collection_2 = self.res.collection.create(name='Another collection')
        collection_3 = self.res.collection.create(name='To-be-deleted collection')

        # pylint: disable=unbalanced-tuple-unpacking
        reads_1, reads_2, reads_3 = self.get_reads(3, collection_1)
        reads_4, reads_5, reads_6 = self.get_reads(3)
        background_1, bam_1, bam_2 = self.get_bams(3, collection_1)
        background_2, bam_3, bam_4 = self.get_bams(3)
        # pylint: enable=unbalanced-tuple-unpacking

        reads = [reads_1, reads_2, reads_3, reads_4, reads_5, reads_6]
        bams = [background_1, bam_1, bam_2, background_2, bam_3, bam_4]
        for data1, data2 in zip(reads, bams):
            change_samples(data1, data2)

        samples = [read.sample for read in reads]

        collection_1.create_background_relation('background1', samples[0], samples[1:3])

        collection_2.add_samples(samples[5])

        # Create a relation that is not connected to a collection in use
        relation = collection_3.create_background_relation('background1', samples[3], [samples[4]])

        # Run macs
        macs_1, macs_2 = collection_1.run_macs()
        macs_3 = relation.run_macs()[0]
        macs_4 = samples[5].run_macs(use_background=False)[0]

        reads_id = [read.id for read in reads]
        macs_id = [macs_1.id, macs_2.id, macs_3.id, macs_4.id]

        # Run on collection
        prepare_geo_chipseq = collection_1.run_prepare_geo_chipseq()
        self.assertEqual(prepare_geo_chipseq.input['reads'], reads_id[:3])
        self.assertEqual(prepare_geo_chipseq.input['macs'], macs_id[:2])
        self.assertEqual(prepare_geo_chipseq.input['name'], collection_1.name)

        # Second run with same parameters should return same objects
        prepare_geo_chipseq_2 = collection_1.run_prepare_geo_chipseq()
        self.assertEqual(prepare_geo_chipseq.id, prepare_geo_chipseq_2.id)

        # Run on a list of samples all in the same collection
        prepare_geo_chipseq = prepare_geo.prepare_geo_chipseq(samples[:3])
        self.assertEqual(prepare_geo_chipseq.id, prepare_geo_chipseq_2.id)

        # Run on samples that are in two different collections
        prepare_geo_chipseq = prepare_geo.prepare_geo_chipseq(samples[:3] + [samples[5]])
        self.assertEqual(prepare_geo_chipseq.input['reads'], reads_id[:3] + [reads_id[5]])
        self.assertEqual(prepare_geo_chipseq.input['macs'], macs_id[:2] + [macs_id[3]])

        # Run on all samples
        prepare_geo_chipseq = prepare_geo.prepare_geo_chipseq(samples)
        self.assertEqual(prepare_geo_chipseq.input['reads'], reads_id)
        self.assertEqual(prepare_geo_chipseq.input['macs'], macs_id)

        # Run only on samples that are not in a collection
        prepare_geo_chipseq = prepare_geo.prepare_geo_chipseq(samples[3:5])
        self.assertEqual(prepare_geo_chipseq.input['reads'], reads_id[3:5])
        self.assertEqual(prepare_geo_chipseq.input['macs'], [macs_id[2]])

        # Run on a sample that has two macs data objects
        samples[1].add_data(macs_2)
        with self.assertRaises(ValueError):
            collection_1.run_prepare_geo_chipseq()

        # Run on a sample that has no macs data object
        samples[1].remove_data(macs_2)
        samples[1].remove_data(macs_1)
        with self.assertRaises(ValueError):
            collection_1.run_prepare_geo_chipseq()

        # Run on a sample whose background is not in the resource - sample_list
        with self.assertRaises(ValueError):
            prepare_geo_chipseq = prepare_geo.prepare_geo_chipseq(samples[4:])

        # Run on a sample whose background is not in the resource - collection
        samples[1].add_data(macs_1)
        collection_1.remove_samples(samples[0])
        with self.assertRaises(ValueError):
            collection_1.run_prepare_geo_chipseq()

    def test_prepare_geo_rnaseq(self):
        collection_1 = self.res.collection.create(name='Test collection')
        collection_2 = self.res.collection.create(name='Another collection')

        # pylint: disable=unbalanced-tuple-unpacking
        reads_1, reads_2 = self.get_reads(2, collection_1)
        exp_1, exp_2 = self.get_expression(2, collection_1)
        # pylint: enable=unbalanced-tuple-unpacking
        reads_3 = self.get_reads(1, collection_2)[0]
        exp_3 = self.get_expression(1, collection_2)[0]
        reads_4 = self.get_reads()[0]
        exp_4 = self.get_expression()[0]
        reads_5 = self.get_reads()[0]
        exp_5 = self.get_expression()[0]

        reads = [reads_1, reads_2, reads_3, reads_4, reads_5]
        expressions = [exp_1, exp_2, exp_3, exp_4, exp_5]
        for data1, data2 in zip(reads, expressions):
            change_samples(data1, data2)

        samples = [read.sample for read in reads]

        reads_id = [read.id for read in reads]
        expressions_id = [expression.id for expression in expressions]

        # Run on collection
        prepare_geo_rnaseq = collection_1.run_prepare_geo_rnaseq()
        self.assertEqual(prepare_geo_rnaseq.input['reads'], reads_id[:2])
        self.assertEqual(prepare_geo_rnaseq.input['expressions'], expressions_id[:2])
        self.assertEqual(prepare_geo_rnaseq.input['name'], collection_1.name)

        # Second run with same parameters should return same objects
        prepare_geo_rnaseq_2 = prepare_geo.prepare_geo_rnaseq(samples[:2])
        self.assertEqual(prepare_geo_rnaseq.id, prepare_geo_rnaseq_2.id)

        # Run on samples that are in two different collections
        prepare_geo_rnaseq = prepare_geo.prepare_geo_rnaseq(samples[:3])
        self.assertEqual(prepare_geo_rnaseq.input['reads'], reads_id[:3])
        self.assertEqual(prepare_geo_rnaseq.input['expressions'], expressions_id[:3])

        # Run on all samples
        prepare_geo_rnaseq = prepare_geo.prepare_geo_rnaseq(samples)
        self.assertEqual(prepare_geo_rnaseq.input['reads'], reads_id)
        self.assertEqual(prepare_geo_rnaseq.input['expressions'], expressions_id)

        # Run on samples without a collection
        prepare_geo_rnaseq = prepare_geo.prepare_geo_rnaseq(samples[3:])
        self.assertEqual(prepare_geo_rnaseq.input['reads'], reads_id[3:])
        self.assertEqual(prepare_geo_rnaseq.input['expressions'], expressions_id[3:])

        # Run on a sample without expression
        samples[0].remove_data(exp_1)
        with self.assertRaises(LookupError):
            collection_1.run_prepare_geo_rnaseq()
