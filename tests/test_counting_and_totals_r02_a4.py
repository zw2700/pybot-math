"""Arithmetic variations and ambiguity checks for the additional schemas."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.counting_and_totals_r02_a4 import solve as counting


def answer(text):
    reply = solve(text)
    return None if reply is None else Fraction(reply.rsplit('Answer: ', 1)[1])


class CountingSchemasTests(unittest.TestCase):
    def test_postposed_stock_events(self):
        for initial, removed, added in [(46, 9, 7), (83, 22, 12)]:
            self.assertEqual(answer(
                'A club has {} members. If {} members quit, but {} new members got in, '
                'how many members are there now?'.format(initial, removed, added)),
                initial-removed+added)

    def test_missing_category_is_not_added_to_its_whole(self):
        for a, b, total in [(7, 11, 32), (17, 8, 61)]:
            self.assertEqual(answer(
                'A sack has {} white stones and {} black stones. If there are {} stones '
                'in the sack, how many are there of the gray color?'.format(a, b, total)),
                total-a-b)
            self.assertEqual(answer(
                'A sack holds {} stones in total. There are {} white stones and {} black '
                'stones. The remaining stones are gray. How many gray stones are there?'.format(total, a, b)),
                total-a-b)

    def test_multiple_group_counts_and_multiple_rates(self):
        self.assertEqual(answer(
            'A florist bought 4 packs of white beads and 7 packs of blue beads. '
            'There are 13 beads in each package. How many beads did she buy in all?'), 143)
        self.assertEqual(answer(
            'There are 3 tokens in each of the 8 drawers. She adds 5 more tokens to '
            'each drawer. Calculate the total number of tokens she has.'), 64)

    def test_grouped_removals_and_extra_stage(self):
        self.assertEqual(answer(
            'At a party, 83 biscuits were served. If each of the 12 guests ate 4 biscuits, '
            'how many biscuits are left?'), 35)
        self.assertEqual(answer(
            'A technician needs to clean 3 loads, which takes 17 minutes per load. '
            'Then she dries everything, which takes 24 minutes. '
            'How long does the work take in total?'), 75)

    def test_recipe_material_is_a_rate(self):
        self.assertEqual(answer(
            'An artist can make a wreath from 4 spools of ribbon. She has 9 spools of red '
            'ribbon, 13 spools of blue ribbon, and 6 spools of white ribbon. '
            'How many wreaths can she make?'), 7)

    def test_goal_minus_inventory_with_adjectives(self):
        self.assertEqual(answer(
            'A decorator needs 95 paper cups for an event. She already has 32 green cups '
            'and 27 blue cups. How many more cups should she buy?'), 36)

    def test_rate_chain_preserves_dimensions(self):
        self.assertEqual(answer(
            'A machine produces 14 parts an hour and runs for 6 hours a day 4 days a week. '
            'How many parts does it produce a week?'), 336)
        self.assertEqual(answer(
            'A tower has 3 sections with 7 floors each. Each floor has 4 rooms, and '
            'each room needs 5 lamps. How many lamps does the tower need?'), 420)

    def test_equal_parts_and_fraction_removed(self):
        self.assertEqual(answer(
            'A 27 meter cord was cut into 9 equal parts. If 4 parts were used for a project, '
            'how long was used for the project?'), 12)
        self.assertEqual(answer(
            'A family bought 1 cake that is cut into 24 slices. Only two-thirds of the '
            'cake was eaten. How many slices were left?'), 8)

    def test_equal_categories_and_capacity_rounding(self):
        self.assertEqual(answer(
            'There are 91 people where the number of adults and teenagers is equal. '
            'The rest are children. How many children are there if there are 37 adults?'), 17)
        self.assertEqual(answer(
            'A worker can carry 7 crates at a time. She finds 30 crates outside. '
            'What is the fewest number of trips she must take to carry all 30 crates?'), 5)

    def test_measurement_conversion_and_mean(self):
        self.assertEqual(answer(
            'A technician waits 3 days for a part, 9 days for a tool, and 3 weeks for an '
            'inspection. How many days does she wait in total?'), 33)
        self.assertEqual(answer(
            'A station recorded 2.2 inches of rain in May, 3.8 inches in June and 6 inches '
            'in July. What is the average amount, in inches, of rain?'), 4)

    def test_abstains_on_overlap_fractions_and_extra_dimensions(self):
        cases = [
            'A collector needs 50 cards. She has 20 cards, including 8 blue cards. '
            'How many more cards should she buy?',
            'A gardener has 80 flowers. She gave 1/4 of her flowers away and 1/5 to '
            'her neighbor. How many flowers are left?',
            'A warehouse has 8 boxes with 12 pens in each box and uses 3 carts. '
            'How many pens are there in total?',
            'A theater has 8 rows with 12 seats in each row. How many rows are left?',
            'An artist needs 6 tiles to make a picture. She has 12 tiles and buys 9 more. '
            'How many brushes can she use?',
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertIsNone(counting(Problem.read(text)))
        self.assertIsNone(solve('I have 3 kids and 2 dogs'))

    def test_runtime_routes_new_schema(self):
        from bot.runtime import turn
        result = turn(
            'A club has 48 members. If 13 members quit, but 6 new members got in, '
            'how many members are there now?', {})
        self.assertEqual(result['module'], 'word_problem')
        self.assertTrue(result['reply'].endswith('41'))


if __name__ == '__main__':
    unittest.main()
