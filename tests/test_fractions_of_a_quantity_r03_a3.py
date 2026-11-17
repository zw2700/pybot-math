"""Fraction interpretations, including changed amounts and ambiguous inputs."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.fractions_of_a_quantity_r03_a3 import solve as fraction_skill


def answer(text):
    result = solve(text)
    return None if result is None else Fraction(result.rsplit('Answer: ', 1)[1])


class FractionQuantityTests(unittest.TestCase):
    def test_population_and_complement(self):
        for count in (75, 150, 225):
            story = 'There are {} pupils at a school. Two-fifths of them are boys. '.format(count)
            self.assertEqual(answer(story + 'How many boys are at the school?'), Fraction(count)*2/5)
            self.assertEqual(answer(story + 'How many girls are at the school?'), Fraction(count)*3/5)

    def test_counted_share_recovers_the_whole(self):
        for part in (24, 36, 60):
            self.assertEqual(answer(
                'Mira sold 3/5 of her collection for ${}. '
                'How much would she earn from the entire collection?'.format(part)), Fraction(part)*5/3)

    def test_original_and_remaining_denominators(self):
        self.assertEqual(answer(
            'Mira spent 1/3 of her money and then spent 1/4 of the remaining money. '
            'She has $90 left. How much money did she have at first?'), 180)
        self.assertEqual(answer(
            'Mira spent 1/3 of her money and 1/4 of it, and then spent $10. '
            'She has $90 left. How much money did she have at first?'), 240)

    def test_remainder_then_return(self):
        self.assertEqual(answer(
            'Omar collected 36 stones. A bird took 2/3 of them. '
            'The bird returned 5 stones. How many stones does Omar have left?'), 17)

    def test_independent_shares(self):
        self.assertEqual(answer(
            'A jar has 180 beads. One-third are green, one-fourth are white, '
            'and the rest are black. How many black beads are there?'), 75)

    def test_nested_query_selects_correct_stage(self):
        story = ('A shop has 200 beads. Half of the beads are blue, and '
                 'one-fourth of the blue beads are shiny. ')
        self.assertEqual(answer(story + 'How many shiny blue beads are there?'), 25)
        self.assertEqual(answer(story + 'How many blue beads are there?'), 100)
        self.assertEqual(answer(story + 'How many blue beads are not shiny?'), 75)

    def test_fraction_more_and_combined_total(self):
        self.assertEqual(answer(
            'Mira spent 2/5 times more money than Omar. Omar spent $250. '
            'What is the total amount of money they spent together?'), 600)

    def test_shared_possession_noun_keeps_owners_distinct(self):
        self.assertEqual(answer(
            "Mira's garage has 12 shelves. Omar's garage has 3 times as many shelves "
            "as Mira's garage. Hana's garage has 1/6 as many shelves as Omar's "
            "garage. How many shelves does Hana's garage have?"), 6)

    def test_fraction_interval_is_a_divisor(self):
        self.assertEqual(answer(
            'At a terminal, a tram leaves every quarter-hour for 9 hours a day. '
            'How many trams leave the terminal for 4 days?'), 144)

    def test_measured_fractional_stocks(self):
        self.assertEqual(answer(
            'Mira has 1/2 of a bottle of paint and 1/3 of a bottle of paint. '
            'She uses 1/12 of a bottle of paint per day. How many days will the paint last?'), 10)

    def test_abstains_on_extra_quantities_and_mixed_units(self):
        for text in (
            'Mira has 36 beads. She sold half of them and bought 3 books. '
            'How many beads does she have left?',
            'Mira has 36 beads and her sister has 20 beads. Half of them are blue. '
            'How many blue beads does Mira have?',
            "We're learning about fractions. I have 12 beads and half are blue. "
            'How many blue beads are there?',
        ):
            problem = Problem.read(text)
            self.assertIsNone(None if problem is None else fraction_skill(problem))
        self.assertIsNone(solve('I have 3 kids and 2 dogs.'))


if __name__ == '__main__':
    unittest.main()
