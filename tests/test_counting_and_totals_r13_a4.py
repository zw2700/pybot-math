"""Relation composition with changed quantities, units, nouns and scope."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.counting_and_totals_r13_a4 import solve as counting


def value(text):
    p = Problem.read(text)
    result = counting(p) if p else None
    return result[0] if result else None


class CountingCompositionTests(unittest.TestCase):
    def test_modified_categories_do_not_cross_multiply(self):
        for noun in ('crates', 'baskets', 'wagons'):
            text = ('Each cedar {0} contains 9 beads, each metal {0} contains '
                    '13 beads, and each glass {0} contains 5 beads. A supplier '
                    'has 7 cedar {1}, 4 metal {1}, and 2 glass {1}. '
                    'How many beads does the supplier have in total?').format(
                        noun[:-1], noun)
            self.assertEqual(value(text), 125)
            self.assertTrue(solve(text).endswith('Answer: 125'))

    def test_nested_recipes_share_a_count(self):
        text = ('Each panel is made of 4 plates and 3 brackets. There are '
                '6 panels. Each plate contains 8 pins and each bracket '
                'contains 5 pins. How many pins are needed in total?')
        self.assertEqual(value(text), 282)

    def test_time_per_category_and_requested_conversion(self):
        text = ('It takes 1.25 hours to inspect a capsule and 0.5 hours to '
                'inspect a canister. What is the number of minutes needed '
                'to inspect 4 capsules and 6 canisters?')
        self.assertEqual(value(text), 480)

    def test_parallel_outputs_account_for_late_start(self):
        text = ('The team has 20 minutes to work. Ava produces 10 tokens per '
                'minute, Bo produces 7 tokens per minute, and Cy arrives '
                '6 minutes late and produces 3 tokens per minute. '
                'How many tokens can they produce in total?')
        self.assertEqual(value(text), 382)

    def test_independent_local_pairs_keep_their_sizes(self):
        text = ('A worker filled 2 bins with 5 liters each, 3 bins with '
                '7 liters each, and 4 bins with 1.5 liters each. '
                'How many liters did the worker use in total?')
        self.assertEqual(value(text), 37)
        self.assertTrue(solve(text).endswith('Answer: 37'))

    def test_comparison_graph_anchor_can_follow_the_question(self):
        text = ('Ava has 6 more counters than Bo and Cy has 9 more counters '
                'than Ava. How many counters do they have together '
                'if Bo has 17 counters?')
        self.assertEqual(value(text), 72)

    def test_simultaneous_aging(self):
        text = ('Ava is 9 years old and Bo is 15 years old. How many years '
                'will pass before their combined age is 50 years old?')
        self.assertEqual(value(text), 13)

    def test_weekday_factor_needs_two_separate_day_counts(self):
        text = ('Ava produces 6 tokens each day during weekdays. On each '
                'weekend day she produces 2 times the number of tokens '
                'she produces on weekdays. How many tokens can she '
                'produce in a week?')
        self.assertEqual(value(text), 54)
        self.assertTrue(solve(text).endswith('Answer: 54'))

    def test_ratio_share_transfer(self):
        text = ('Ava has 900 counters. She shared them between Bo, Cy and '
                'Dee in the ratio 2:1:3 respectively. Dee gave Bo half '
                'of her own share. How many counters does Bo now have?')
        self.assertEqual(value(text), 525)

    def test_fraction_is_of_the_updated_stock(self):
        text = ('Ava has 48 pairs of gloves. She loses 12 pairs of gloves. '
                'Of the remaining pairs of gloves, she donates one-fourth '
                'to charity. She purchases 6 new pairs of gloves and '
                'receives 3 new pairs of gloves. How many pairs of '
                'gloves does Ava have in total?')
        self.assertEqual(value(text), 36)

    def test_weighted_ratings_validate_the_total(self):
        text = ('A shop receives 10 reviews. There are 3 5-star reviews, '
                '4 4-star reviews, and 3 2-star reviews. What is the '
                'average star rating based on these reviews?')
        self.assertEqual(value(text), Fraction(37, 10))
        self.assertIsNone(value(text.replace('10 reviews', '11 reviews')))

    def test_capacity_rounds_up_only_after_adding_masses(self):
        text = ('A machine holds 4 pounds at a time. 3 towels weigh '
                '2 pounds and 5 cloths weigh 1 pound. There are '
                '12 towels and 15 cloths to wash. How many loads '
                'must the machine wash?')
        self.assertEqual(value(text), 3)

    def test_full_reservoir_has_opposing_rates(self):
        text = ('The drain can empty a reservoir in 5 hours and the hose '
                'can fill the reservoir in 10 hours. The reservoir holds '
                '200 liters of water. The reservoir starts filled with '
                'water. How much water will be left after 3 hours?')
        self.assertEqual(value(text), 140)

    def test_unknown_quantity_or_rate_abstains(self):
        cases = [
            'Each wooden box contains 7 beads and each metal box contains '
            '9 beads. A supplier has 3 wooden boxes and 4 glass boxes. '
            'How many beads does the supplier have in total?',
            'Each box contains 7 beads. A supplier has 3 boxes and '
            '5 beads are required to decorate a card. How many beads '
            'does the supplier have in total?',
            'Each box contains 7 beads. A supplier has 3 boxes and '
            'is 29 years old. How many beads does the supplier have?',
            'Each box contains 7 beads. A supplier has 3 boxes and '
            'donates some beads. How many beads does the supplier have?',
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertIsNone(value(text))

    def test_personal_statements_do_not_enter_the_math_gate(self):
        self.assertIsNone(solve('I have 3 kids and 2 dogs.'))
        self.assertIsNone(solve('We have 8 crates and 6 bags at work.'))


if __name__ == '__main__':
    unittest.main()
