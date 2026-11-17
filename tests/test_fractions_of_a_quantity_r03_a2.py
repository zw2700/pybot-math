"""Fraction scopes, exact arithmetic, reference resolution, and abstention."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.fractions_of_a_quantity_r03_a2 import solve as fraction_skill


def answer(text):
    reply = solve(text)
    return None if reply is None else Fraction(reply.rsplit('Answer: ', 1)[1])


class FractionQuantityTests(unittest.TestCase):
    def test_successive_remainders_vary_independently(self):
        for total, numerator, denominator in ((72, 1, 3), (135, 2, 5), (210, 3, 7)):
            text = ('A warehouse has {} parcels. Workers shipped {}/{} of them '
                    'on Monday and 1/4 of what was left on Tuesday. '
                    'How many parcels remain?').format(total, numerator, denominator)
            self.assertEqual(answer(text), Fraction(total)*(1-Fraction(numerator, denominator))*Fraction(3, 4))

    def test_original_scope_differs_from_remainder(self):
        for scope, expected in (('original', 84), ('remaining', 85.5)):
            text = ('$120 was divided between Nora and Inez. Inez received 3/4 of the money. '
                    'Inez then spent 1/20 of the {} money. How much does Inez have left?').format(scope)
            self.assertEqual(answer(text), Fraction(str(expected)))

    def test_grouped_collection(self):
        self.assertEqual(answer(
            'A warehouse bought 7 crates of 18 jars each. Workers sold 2/7 of the jars. '
            'How many jars remain?'), 90)

    def test_named_fraction_chain_and_adjustment(self):
        self.assertEqual(answer(
            'Nora picked 36 plums. Inez picked one-third as many plums as Nora. '
            'Omar picked 5 more than half the number of plums Inez picked. '
            'How many plums did Nora, Inez, and Omar pick in total?'), 59)

    def test_disjoint_fractions_use_same_whole(self):
        self.assertEqual(answer(
            'There are 120 participants at a meeting. Half are from the north '
            'and one-fifth are from the south. The rest are from the west. '
            'How many participants are from the west?'), 36)

    def test_fractional_measure_is_not_a_share(self):
        text = ('A cook has 12 cups of milk in a jug. She used 1/2 cup of milk. '
                'How many cups of milk remain?')
        self.assertIsNone(fraction_skill(Problem.read(text)))

    def test_unknown_quantity_and_inconsistent_anchors(self):
        for text in (
                'Nora has half as many beads as Inez. Nora has 12 beads. '
                'Nora has 14 beads. How many beads does Inez have?',
                'Nora has half as many beads as Inez. Inez has 30 beads. '
                'A crate weighs 7 pounds. How many beads does Nora have?'):
            self.assertIsNone(fraction_skill(Problem.read(text)))

    def test_combined_relative_amount(self):
        self.assertEqual(answer(
            'Nora has half as many beads as Inez. Inez has 30 beads. '
            'Omar has twice the combined number of beads Nora and Inez have. '
            'How many beads does Omar have?'), 90)

    def test_scaled_fraction_spellings(self):
        self.assertEqual(answer(
            'A depot has 2 million parcels. Workers shipped two-fifths of them. '
            'How many parcels remain?'), 1200000)

    def test_weekday_span_excludes_later_related_days(self):
        self.assertEqual(answer(
            'On Monday a ranger sees 80 birds. On Tuesday he sees half as many birds '
            'as on Monday. On Wednesday he sees 6 more birds than on Tuesday. '
            'On Thursday he sees twice as many birds as on Wednesday. '
            'How many total birds did he see from Monday to Wednesday?'), 166)

    def test_group_guard_keeps_fractional_measurements(self):
        self.assertEqual(answer(
            'A store has 3 tanks holding 10 liters each. It used 1/2 liter. '
            'How many liters remain?'), Fraction(59, 2))

    def test_remaining_material_divided_by_matching_output_rate(self):
        self.assertEqual(answer(
            'A baker has 72 pounds of fruit. She used half of it for jam. '
            'The rest is for pies. She needs 3 pounds of fruit per pie. '
            'How many pies can she make?'), 12)

    def test_complete_outputs_are_rounded_down(self):
        self.assertEqual(answer(
            'A baker has 70 pounds of fruit. She used half of it for jam. '
            'The rest is for pies. She needs 4 pounds of fruit per pie. '
            'How many pies can she make?'), 8)

    def test_unexplained_duration_is_not_discarded(self):
        text = ('A warehouse has 72 parcels. Workers ship half of them each day. '
                'How many parcels remain after 3 days?')
        self.assertIsNone(fraction_skill(Problem.read(text)))

    def test_statements_do_not_trigger_math(self):
        self.assertIsNone(solve('I have 3 kids and 2 dogs.'))
        self.assertIsNone(solve('I gave half my lunch to a friend and bought 2 drinks.'))


if __name__ == '__main__':
    unittest.main()
