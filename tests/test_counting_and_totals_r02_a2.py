"""Variations of the relations, with changed quantities and domain nouns."""
import unittest
from fractions import Fraction

from bot.math.problem import Problem
from bot.math.skills.counting_and_totals_r02_a2 import solve


def answer(text):
    problem = Problem.read(text)
    result = solve(problem) if problem is not None else None
    return result[0] if result is not None else None


class ThreeStepCountingTests(unittest.TestCase):
    def test_time_unit_chain(self):
        for speed, hours, days in [(17, 3, 4), (23, 2, 6)]:
            text = ('A clerk types {} words per minute. She types {} hours per day. '
                    'How many words can she type in {} days?').format(speed, hours, days)
            self.assertEqual(answer(text), speed*60*hours*days)

    def test_group_categories_and_comparison_direction(self):
        stem = ('A factory has 7 square bins and 4 round bins. '
                'Each square bin contains 9 tokens. Each round bin contains 6 tokens. ')
        self.assertEqual(answer(stem+'How many tokens are there in total?'), 87)
        self.assertEqual(answer(stem+'How many more tokens are in square bins than round bins?'), 39)
        self.assertIsNone(answer(stem+'How many more tokens are in round bins than square bins?'))

    def test_transitive_category_comparisons(self):
        text = ('A store has 31 red ribbons. There are 8 fewer blue ribbons than red ribbons. '
                'There are 6 more yellow ribbons than blue ribbons. '
                'How many ribbons does the store have in total?')
        self.assertEqual(answer(text), 83)

    def test_passive_inventory(self):
        text = ('A jar contains 12 red beads, 19 blue beads, and 8 green beads. '
                'Five red beads are removed and then six blue beads are removed. '
                'How many beads are left in the jar?')
        self.assertEqual(answer(text), 28)

    def test_recipe_remaining_capacity(self):
        for batch, input_count, made, supply in [(2, 5, 6, 40), (1, 3, 4, 27)]:
            text = ('The recipe for {} batches of paint calls for {} cups of dye. '
                    'A worker makes {} batches of paint. Her supply contains {} cups of dye. '
                    'How many more batches could she make with the remaining dye?').format(
                        batch, input_count, made, supply)
            self.assertEqual(answer(text), Fraction(supply*batch,input_count)-made)

    def test_capacity_balance_and_resource_recipe(self):
        self.assertEqual(answer(
            'A hall has 9 wooden benches. A wooden bench seats 8 visitors and a metal bench '
            'seats 3 visitors. How many metal benches are needed so that 90 visitors can sit '
            'at the same time?'), 6)
        self.assertEqual(answer(
            'One large lantern requires 4 cells, and one small lantern requires 2 cells. '
            'A worker uses a total of 38 cells. If she makes 5 large lanterns, '
            'how many small lanterns does she make?'), 9)

    def test_selected_weekdays_are_not_full_weeks(self):
        self.assertEqual(answer(
            'A worker reads 3 hours a day from Monday to Thursday, and 2 hours a day '
            'on Friday and Saturday. How many hours does she read in one week?'), 16)
        self.assertEqual(answer(
            'A machine makes 11 parts per minute and runs 3 hours a day. '
            'How many parts does it make per week?'), 13860)

    def test_time_allowance_and_explicit_pack_sizes(self):
        self.assertEqual(answer(
            'A worker has 2 hours to finish her tasks. Her filing takes 25 minutes. '
            'Her cleaning takes 35 minutes. How much time does she have left?'), 60)
        self.assertEqual(answer(
            'A club buys 4 packs of striped scarves and 3 packs of plain scarves. '
            'The striped scarves come in packs of 7, and the plain scarves come in packs '
            'of 5. How many scarves did the club buy in all?'), 43)

    def test_no_guessing_past_unexplained_quantities(self):
        cases = [
            'I have 3 kids and 2 dogs',
            'A factory has 7 square bins and 4 round bins. Each square bin contains 9 tokens. '
            'How many tokens are there in total?',
            'A clerk types 17 words per minute and has 3 pens. She types 3 hours per day. '
            'How many words can she type in 4 days?',
            'A worker has 20 beads. She gives 3 beads to Ada and loses 2 beads. '
            'How many beads does Ada have now?',
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertIsNone(answer(text))


if __name__ == '__main__':
    unittest.main()
