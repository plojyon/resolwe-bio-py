# pylint: disable=missing-docstring
from resdk.analysis import expressions
from resdk.tests.functional.base import BaseResdkFunctionalTest


class TestExpressions(BaseResdkFunctionalTest):

    def test_cuffquant(self):
        collection = self.res.collection.create(name='Test collection')

        # pylint: disable=unbalanced-tuple-unpacking
        bam_1, bam_2 = self.get_bams(2, collection)
        # pylint: enable=unbalanced-tuple-unpacking
        bam_3 = self.get_bams(1)[0]
        annotation = self.get_gtf()

        group = collection.create_group_relation(category='replicates', samples=[bam_1.sample])

        # Run cuffquant on a collection
        cuffquants = collection.run_cuffquant(annotation=annotation)
        self.assertEqual(len(cuffquants), 2)
        self.assertEqual(cuffquants[0].input['alignment'], bam_1.id)
        self.assertEqual(cuffquants[0].input['annotation'], annotation.id)
        self.assertEqual(cuffquants[1].input['alignment'], bam_2.id)
        self.assertEqual(cuffquants[1].input['annotation'], annotation.id)

        # Run cuffquant on a relation
        cuffquants = group.run_cuffquant(annotation=annotation)
        self.assertEqual(len(cuffquants), 1)
        self.assertEqual(cuffquants[0].input['alignment'], bam_1.id)
        self.assertEqual(cuffquants[0].input['annotation'], annotation.id)

        # Run cuffquant on a sample
        cuffquants = bam_3.sample.run_cuffquant(annotation=annotation)
        self.assertEqual(len(cuffquants), 1)
        self.assertEqual(cuffquants[0].input['alignment'], bam_3.id)
        self.assertEqual(cuffquants[0].input['annotation'], annotation.id)

    def test_cuffnorm(self):
        collection = self.res.collection.create(name='Test collection')

        # pylint: disable=unbalanced-tuple-unpacking
        cuffquant_1, cuffquant_2, cuffquant_3, cuffquant_4 = self.get_cuffquants(4, collection)
        # pylint: enable=unbalanced-tuple-unpacking
        annotation = self.get_gtf()

        group = collection.create_group_relation(
            samples=[
                cuffquant_1.sample,
                cuffquant_2.sample,
                cuffquant_3.sample,
                cuffquant_4.sample,
            ],
            labels=['1', '1', '2', '2'],
            category='replicates',
        )

        # Run cuffnorm on a collection
        cuffnorm = collection.run_cuffnorm(annotation=annotation)
        self.assertEqual(
            cuffnorm.input['cuffquant'],
            [cuffquant_1.id, cuffquant_2.id, cuffquant_3.id, cuffquant_4.id]
        )
        self.assertEqual(cuffnorm.input['annotation'], annotation.id)

        # Run cuffnorm on two groups of replicates in collection
        cuffnorm = expressions.cuffnorm(group, annotation=annotation)
        self.assertEqual(
            cuffnorm.input['cuffquant'],
            [cuffquant_1.id, cuffquant_2.id, cuffquant_3.id, cuffquant_4.id]
        )
        self.assertEqual(cuffnorm.input['annotation'], annotation.id)
