# pylint: disable=missing-docstring
from __future__ import absolute_import, division, print_function, unicode_literals

from resdk.analysis import differential_expressions
from resdk.tests.functional.base import BaseResdkFunctionalTest


class TestExpressions(BaseResdkFunctionalTest):

    def test_cuffdiff(self):
        collection_1 = self.res.collection.create(name='Test collection 1')
        collection_2 = self.res.collection.create(name='Test collection 2')

        # pylint: disable=unbalanced-tuple-unpacking
        cuffquant_1, cuffquant_2, cuffquant_3, cuffquant_4 = self.get_cuffquants(4, collection_1)
        self.get_cuffquants(1, collection_1)
        cuffquant_6, cuffquant_7, cuffquant_8, cuffquant_9 = self.get_cuffquants(4, collection_2)
        cuffquant_10, cuffquant_11 = self.get_cuffquants(2, collection_2)
        # pylint: enable=unbalanced-tuple-unpacking
        gff = self.get_gtf()

        relation = collection_1.create_compare_relation(
            samples=[
                cuffquant_1.sample,
                cuffquant_2.sample,
                cuffquant_3.sample,
                cuffquant_4.sample,
            ],
            labels=['control', 'control', 'case', 'case'],
            category='case-control'
        )

        collection_2.create_compare_relation(
            samples=[
                cuffquant_6.sample,
                cuffquant_7.sample,
                cuffquant_8.sample,
                cuffquant_9.sample,
            ],
            labels=['control', 'control', 'case', 'case'],
            category='case-control'
        )

        collection_2.create_compare_relation(
            samples=[
                cuffquant_6.sample,
                cuffquant_7.sample,
                cuffquant_10.sample,
                cuffquant_11.sample,
            ],
            labels=['control', 'control', 'case', 'case'],
            category='case-control-2'
        )

        samples = [
            cuffquant_1.sample,
            cuffquant_2.sample,
            cuffquant_3.sample,
            cuffquant_4.sample,
        ]

        # Run cuffdiff on a collection (one sample not in any relation)
        cuffdiff = collection_1.run_cuffdiff(annotation=gff)
        self.assertEqual(len(cuffdiff), 1)
        self.assertEqual(cuffdiff[0].input['case'], [cuffquant_3.id, cuffquant_4.id])
        self.assertEqual(cuffdiff[0].input['control'], [cuffquant_1.id, cuffquant_2.id])
        self.assertEqual(cuffdiff[0].input['annotation'], gff.id)

        # Run cuffdiff on a relation
        cuffdiff = relation.run_cuffdiff(annotation=gff)
        self.assertEqual(len(cuffdiff), 1)
        self.assertEqual(cuffdiff[0].input['case'], [cuffquant_3.id, cuffquant_4.id])
        self.assertEqual(cuffdiff[0].input['control'], [cuffquant_1.id, cuffquant_2.id])
        self.assertEqual(cuffdiff[0].input['annotation'], gff.id)

        # Run cuffdiff on a list of samples
        cuffdiff = differential_expressions.cuffdiff(samples, annotation=gff)
        self.assertEqual(len(cuffdiff), 1)
        self.assertEqual(cuffdiff[0].input['case'], [cuffquant_3.id, cuffquant_4.id])
        self.assertEqual(cuffdiff[0].input['control'], [cuffquant_1.id, cuffquant_2.id])
        self.assertEqual(cuffdiff[0].input['annotation'], gff.id)

        # Run cuffdiff on a collection (two different relation)
        cuffdiff = collection_2.run_cuffdiff(annotation=gff)
        self.assertEqual(len(cuffdiff), 2)
        self.assertEqual(cuffdiff[0].input['case'], [cuffquant_8.id, cuffquant_9.id])
        self.assertEqual(cuffdiff[0].input['control'], [cuffquant_6.id, cuffquant_7.id])
        self.assertEqual(cuffdiff[1].input['case'], [cuffquant_10.id, cuffquant_11.id])
        self.assertEqual(cuffdiff[1].input['control'], [cuffquant_6.id, cuffquant_7.id])
        self.assertEqual(cuffdiff[0].input['annotation'], gff.id)
        self.assertEqual(cuffdiff[1].input['annotation'], gff.id)
