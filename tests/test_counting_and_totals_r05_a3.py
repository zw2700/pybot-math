"""Dimensional, ownership and disjoint-group regressions for counting rules."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.counting_and_totals_r05_a3 import solve as counting


def answer(text):
    reply = solve(text)
    return None if reply is None else Fraction(reply.rsplit('Answer: ', 1)[1])


class CompositionalCountingTests(unittest.TestCase):
    def test_nested_repetitions(self):
        for per_minute, minutes, sessions, days in [(6, 8, 3, 4), (9, 5, 2, 6)]:
            text = ('Tara skips {} times per minute. She skips for {} minutes each '
                    'session and does {} sessions each day. How many skips will '
                    'Tara do in {} days?').format(per_minute, minutes, sessions, days)
            self.assertEqual(answer(text), per_minute*minutes*sessions*days)

    def test_operating_duration_converts_to_rate_denominator(self):
        for rate, minutes, days in [(7, 4, 2), (3, 11, 5)]:
            text = ('A machine makes {} pieces per second. It runs for {} minutes '
                    'each day. How many pieces does it make in {} days?').format(rate, minutes, days)
            self.assertEqual(answer(text), rate*60*minutes*days)

    def test_distinct_contents_are_not_cross_multiplied(self):
        self.assertEqual(answer(
            'A crafter has 5 bundles with 9 ribbons in each bundle and 3 bundles '
            'with 7 ribbons in each bundle. How many ribbons does the crafter have?'), 66)
        self.assertEqual(answer(
            'A collector has 6 folders of 8 labels and 4 folders of 13 labels. '
            'How many labels does the collector have?'), 100)

    def test_container_changes_precede_conversion(self):
        self.assertEqual(answer(
            'Omar bought 9 sacks. He gave out 2 sacks and bought another 4 sacks. '
            'One sack holds 6 seeds. How many seeds does Omar have now?'), 66)
        self.assertEqual(answer(
            'A supplier bought 19 pens, 8 pads, and some clips. She transports '
            'all of them in 4 equally-sized groups of 15 items per group. '
            'How many clips does she own?'), 33)

    def test_multiple_categories_and_postposed_departures(self):
        self.assertEqual(answer(
            'The club has 18 drummers and 14 singers. If 5 drummers and 3 singers '
            'quit, how many drummers and singers are left?'), 24)
        self.assertEqual(answer(
            'There are 38 passengers on a bus. At a stop 7 passengers get on the '
            'bus. Later 12 passengers get off the bus and 4 passengers get on. '
            'How many passengers are there on the bus now?'), 37)

    def test_weekday_restriction_is_preserved(self):
        self.assertEqual(answer(
            'Nell walks 8 miles per day on weekdays only. How many miles does '
            'she walk over four weeks?'), 160)

    def test_converts_dozens_before_group_addition(self):
        self.assertEqual(answer(
            'After a concert, Mira received 3 dozen flowers from relatives and '
            '4 flowers from each of her 7 friends. How many flowers did Mira receive?'), 64)

    def test_rectangle_perimeter_to_area(self):
        self.assertEqual(answer(
            'A rectangle is 7 centimeters wide. Its perimeter is 34 centimeters. '
            'What is the area of the rectangle?'), 70)

    def test_abstains_on_wrong_owner_or_unresolved_dimensions(self):
        cases = [
            'Alex had 19 tokens. He gave 4 tokens to Bea and received 3 tokens. '
            'How many tokens does Bea have now?',
            'A machine makes 7 parts per minute and runs for 4 minutes each day. '
            'It uses 3 tools. How many parts does it make in 2 days?',
            'A machine jumps 7 times per minute and runs for 4 minutes each day. '
            'How many gallons does it make in 2 days?',
            'A baker had 36 biscuits. She gave 1/2 of the biscuits to a friend '
            'and bought 7 biscuits. How many biscuits does she have now?',
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertIsNone(counting(Problem.read(text)))
        self.assertIsNone(solve('I have 4 kids and 3 dogs'))

    def test_runtime_routes_three_step_chain(self):
        from bot.runtime import turn
        result = turn(
            'A machine makes 7 pieces per second. It runs for 4 minutes each day. '
            'How many pieces does it make in 2 days?', {})
        self.assertEqual(result['module'], 'word_problem')
        self.assertTrue(result['reply'].endswith('3360'))


if __name__ == '__main__':
    unittest.main()
