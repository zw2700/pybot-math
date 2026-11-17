"""Arithmetic variations and abstentions for the additional counting schemas."""
import unittest
from fractions import Fraction

from bot.math import solve


def answer(text):
    reply = solve(text)
    return None if reply is None else Fraction(reply.rsplit('Answer: ', 1)[1])


class CountingRelationsTests(unittest.TestCase):
    def test_proportions_in_either_direction_and_missing_input(self):
        for output, groups, target in [(36, 4, 9), (75, 5, 12)]:
            self.assertEqual(answer(
                '{} passengers fit into {} vans. How many passengers fit in {} vans?'.format(
                    output, groups, target)), Fraction(output*target, groups))
        self.assertEqual(answer(
            'A printer makes 18 labels with 3 sheets. How many more sheets does the printer '
            'need to make a total of 42 labels?'), 4)
        self.assertEqual(answer(
            'It takes 24 minutes for a worker to enter a room 8 times. '
            'How long would it take to enter 5 times?'), 15)

    def test_product_chain(self):
        for rows, pots, flowers in [(4, 6, 3), (7, 5, 8)]:
            self.assertEqual(answer(
                'A gardener has {} rows with {} pots in each row. Each pot contains {} flowers. '
                'How many flowers are there altogether?'.format(rows, pots, flowers)),
                rows*pots*flowers)

    def test_sum_of_grouped_measurements(self):
        self.assertEqual(answer(
            'During the afternoon there were four 7-minute talks and three 9-minute talks. '
            'How many minutes were the talks altogether?'), 55)
        self.assertEqual(answer(
            'A painter applies a coat that takes 4 minutes to dry, three color coats that '
            'take 6 minutes each to dry, and a final coat that takes 8 minutes to dry. '
            'How many minutes total does the painter wait?'), 30)

    def test_inventory_ellipsis_and_grouping_survivors(self):
        self.assertEqual(answer(
            'A collector has 19 silver coins. Last month she ordered 8 more coins '
            'and then lost 5. How many coins does she have now?'), 22)
        self.assertEqual(answer(
            'A gardener has 14 flower pots. She loses 3 pots. Someone steals 2 of her pots. '
            'She puts 4 labels on each of her remaining pots. '
            'How many labels does she use in total?'), 36)

    def test_disjoint_allocations(self):
        self.assertEqual(answer(
            'In total a gardener has 90 acres. 12 acres are occupied by buildings, '
            '8 acres have been reserved for expansion, and 20 acres are dedicated to trees. '
            'The rest is for vegetables. How many acres are used for vegetables?'), 50)

    def test_comparison_is_not_sum_and_difference(self):
        self.assertEqual(answer(
            'There are 9 fewer drums than flutes. There are 34 flutes. '
            'How many drums and flutes are there in total?'), 59)
        self.assertEqual(answer(
            'There are 6 more large boxes than small boxes. There are 23 small boxes. '
            'How many boxes are there?'), 52)

    def test_exception_to_uniform_group_size(self):
        self.assertEqual(answer(
            'Each display includes a bowl containing 4 stones, except for two trays '
            'that hold 7 stones. There are 11 trays. How many stones are there?'), 50)

    def test_new_combined_total_and_dozen_counts(self):
        self.assertEqual(answer(
            'An orchard covers 120 acres and a vineyard covers 180 acres. The orchard '
            'is being enlarged. The new total area is 350 acres. '
            'How much is the orchard enlarged by?'), 50)
        self.assertEqual(answer(
            'A shopper found 11 red beads in a bag and 3 dozen blue beads in another bag. '
            'How many beads did the shopper find altogether?'), 47)

    def test_named_difference_in_wins(self):
        stem = ('Nell and Mira played 28 games. Nell won 6 fewer games than Mira. ')
        self.assertEqual(answer(stem + 'How many games did Nell win?'), 11)
        self.assertEqual(answer(stem + 'How many games did Mira win?'), 17)

    def test_runtime_routes_grouped_sum(self):
        from bot.runtime import turn
        result = turn(
            'At the workshop there were five 8-minute speeches and two 6-minute speeches. '
            'How many minutes were the speeches altogether?', {})
        self.assertEqual(result['module'], 'word_problem')
        self.assertTrue(result['reply'].endswith('52'))

    def test_declines_unaccounted_quantities_and_unrelated_units(self):
        cases = [
            'A worker makes 20 toys in 4 hours and uses 3 tools. '
            'How many toys can she make in 8 hours?',
            'A warehouse has 9 boxes with 6 books in each box. '
            'How many boxes are there altogether?',
            'A worker makes 20 toys in 4 hours. How many tools does she need for 8 hours?',
            'A gardener has 14 pots. She loses 3 pots. She puts 2 labels on each pot. '
            'How many labels are left?',
            'I have 3 kids and 2 dogs',
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertIsNone(solve(text))


if __name__ == '__main__':
    unittest.main()
