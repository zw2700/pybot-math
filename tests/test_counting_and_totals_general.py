"""Counting relations survive noun, modifier and clause-structure changes."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.counting_and_totals_r01_a3 import _grouped_total
from bot.math.skills.counting_and_totals_r08_a2 import _nested_groups


def answer(text):
    reply = solve(text)
    return None if reply is None else Fraction(reply.rsplit('Answer: ', 1)[1])


class GeneralCountingTests(unittest.TestCase):
    def test_sharing_uses_the_relationship_not_a_companion_dictionary(self):
        for noun in ('assistants', 'neighbors', 'teammates'):
            text = ('A researcher has 96 samples. She will share equally with '
                    'her 3 {}. How many samples will she have?').format(noun)
            self.assertEqual(answer(text), 24)

    def test_matching_companions_receive_the_same_amount(self):
        for noun in ('teammates', 'apprentices', 'partners'):
            text = ('Rina has 3 cartons. Each carton holds 8 packets. Her 4 {} '
                    'have the same amount as her. How many packets do Rina '
                    'and her {} have altogether?').format(noun, noun)
            self.assertEqual(answer(text), 120)

    def test_included_host_and_arbitrary_invited_group(self):
        for noun in ('apprentices', 'neighbors', 'visitors'):
            text = ('Eli invited 5 {} for a meal. Everyone, including himself, '
                    'receives 2 bowls. Each bowl holds 7 ounces. How many ounces '
                    'are needed altogether?').format(noun)
            self.assertEqual(answer(text), 84)

    def test_enumeration_count_is_not_an_extra_measurement(self):
        for noun in ('flasks', 'ampoules', 'reservoirs'):
            text = ('There are 3 {} containing the following quantities: '
                    '2 liters, 700 milliliters, and 1 liter. How many milliliters '
                    'are there in total?').format(noun)
            self.assertEqual(answer(text), 3700)

    def test_qualified_group_names_and_nested_relative_clauses(self):
        for count, size, content in ((3, 4, 9), (5, 2, 7)):
            stems = [
                'A supplier has {0} insulated freight wagons. Each insulated '
                'freight wagon uses {1} metal bins with a capacity of {2} liters. '
                'How many liters can the supplier carry?',
                'A supplier has {0} crates, each holding {1} boxes, each '
                'containing {2} beads. How many beads can the supplier carry?',
                'A supplier has {0} crates. There are {1} boxes per wooden '
                'crate. Each box contains {2} beads. '
                'How many beads can the supplier carry?',
            ]
            for stem in stems:
                text = stem.format(count, size, content)
                with self.subTest(text=text):
                    self.assertEqual(_nested_groups(Problem.read(text))[0],
                                     count * size * content)
                    self.assertEqual(answer(text), count * size * content)

    def test_group_rule_declines_unresolved_scope_and_shares(self):
        cases = [
            'A traveler takes a 2-mile walk in the morning and a 3-mile walk '
            'in the evening, every day. How many miles does she walk in 8 days?',
            'A collector has 4 folders with 20 stamps each and 2 binders with '
            '50 stamps each. She keeps 1/4 of the stamps. '
            'How many stamps can she give away?',
            'A shop has 4 crates. Each crate holds 3 cartons. Each carton holds '
            '2 crates. How many crates are there in total?',
            'A supplier has 3 crates. Each crate holds 4 boxes. Each box holds '
            '9 beads. The supplier has 2 bicycles. How many beads can she carry?',
            'A worker makes 6 tiles every other day. '
            'How many tiles does she make in 8 days?',
            'A warehouse has 3 red crates. Each blue crate holds 4 boxes. '
            'Each box contains 9 beads. How many beads can the warehouse hold?',
        ]
        for text in cases:
            with self.subTest(text=text):
                problem = Problem.read(text)
                self.assertIsNone(_grouped_total(problem))
                self.assertIsNone(_nested_groups(problem))

    def test_runtime_uses_the_general_group_reader(self):
        from bot.runtime import turn
        result = turn(
            'A supplier has 3 crates, each holding 4 boxes, each containing '
            '9 beads. How many beads can the supplier carry?', {})
        self.assertEqual(result['module'], 'word_problem')
        self.assertTrue(result['reply'].endswith('108'))


if __name__ == '__main__':
    unittest.main()
