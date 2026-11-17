"""Independent examples and arithmetic variations of the supported schemas."""
import re
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.numbers import format_number, parse_number, read_numbers


def answer(text):
    reply = solve(text)
    return None if reply is None else Fraction(reply.rsplit('Answer: ', 1)[1])


class NumberTests(unittest.TestCase):
    def test_exact_input_formats(self):
        cases = {'1,234': Fraction(1234), '$2.40': Fraction(12, 5),
                 '12.5%': Fraction(1, 8), 'twenty-seven': Fraction(27),
                 'one hundred and six': Fraction(106), '3/4': Fraction(3, 4),
                 '2 1/3': Fraction(7, 3), 'three quarters': Fraction(3, 4),
                 'two and a half': Fraction(5, 2)}
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(parse_number(raw), expected)
                self.assertEqual([n.value for n in read_numbers(raw)], [expected])

    def test_offsets_units_and_ordinals(self):
        text = 'The 1st load has 2kg and twenty-one boxes.'
        quantities = read_numbers(text)
        self.assertEqual([n.value for n in quantities], [2, 21])
        self.assertTrue(all(text[n.start:n.end] == n.raw for n in quantities))
        self.assertEqual([n.value for n in read_numbers('six and eight')], [6, 8])

    def test_format(self):
        self.assertEqual(format_number(Fraction(24, 3)), '8')
        self.assertEqual(format_number(Fraction(1, 8)), '0.125')


class CountingTests(unittest.TestCase):
    def test_inventory_varies_all_quantities(self):
        for initial, removed, added in [(33, 8, 4), (18, 5, 9), (120, 37, 6)]:
            text = ('A vendor prepared {} baskets. She sold {} baskets. '
                    'Then she made {} baskets. How many baskets does she have left?').format(
                        initial, removed, added)
            self.assertEqual(answer(text), initial-removed+added)

    def test_combined_comparative(self):
        self.assertEqual(answer('Mira has 18 stamps. Nell has 7 fewer stamps than Mira. '
                                'How many stamps do they have combined?'), 29)
        self.assertEqual(answer('An artist painted 19 tiles in the morning and 8 more tiles '
                                'in the afternoon. How many tiles did she paint altogether?'), 27)

    def test_groups_with_addition(self):
        for rows, size, extra in [(4, 9, 7), (13, 8, 5)]:
            text = ('There are {} rows with {} seats in each row. Workers added {} extra seats. '
                    'How many seats are there altogether?').format(rows, size, extra)
            self.assertEqual(answer(text), rows*size+extra)

    def test_fractional_group_size(self):
        self.assertEqual(answer('A cook bought 7 bags of rice. Each bag weighs 2.5 kilograms. '
                                'How many kilograms did the cook buy altogether?'), Fraction(35, 2))

    def test_daily_groups_and_weeks(self):
        self.assertEqual(answer('A keeper has 8 goats. Each goat drinks 3 liters of water a day. '
                                'How many liters do they drink in a week?'), 168)

    def test_sum_and_difference_both_unknowns(self):
        stem = 'There are 30 students in a club. There are 8 more girls than boys. '
        self.assertEqual(answer(stem + 'How many girls are in the club?'), 19)
        self.assertEqual(answer(stem + 'How many boys are in the club?'), 11)

    def test_loss_and_time_conversion(self):
        self.assertEqual(answer('Initially a tank holds 90 liters. It loses 4 liters every day. '
                                'How much is remaining after 2 weeks?'), 34)

    def test_corrected_count(self):
        self.assertEqual(answer('A clerk double-counts 5 parcels and misses 2 parcels. '
                                'She thinks she counted 40 parcels. How many parcels are there really?'), 37)

    def test_target_minus_repeated_contributions(self):
        self.assertEqual(answer('A gardener wants to use 80 liters of water. A bucket can hold '
                                '9 liters of water. She fills the bucket 6 times. '
                                'How much more water does she need?'), 26)

    def test_remaining_work_divided_by_rate(self):
        self.assertEqual(answer('A course requires 120 hours of work. A student has already completed '
                                '15 hours of reading and 21 hours of writing. She does 14 hours of '
                                'work every week. How many weeks does she need to finish?'), 6)

    def test_explicit_unit_conversion(self):
        self.assertEqual(answer('A vendor has 96 pencils to pack. If one dozen is 12 pencils, '
                                'how many dozens can the vendor pack?'), 8)

    def test_two_observation_average(self):
        self.assertEqual(answer('Nora got 63 on her first exam. After her second exam her average '
                                'was 70. What score did she get on her second exam?'), 77)

    def test_combined_daily_rates(self):
        self.assertEqual(answer('A rabbit eats 11 grams a day and 3 mice who each eat 2 grams a day. '
                                'How many grams per day do the animals need?'), 17)

    def test_both_members_of_each_group(self):
        self.assertEqual(answer('There are 4 junior teams and 6 senior teams. Both coaches of each '
                                'team attend a meeting. How many coaches attend the meeting?'), 20)

    def test_declines_incomplete_or_different_relations(self):
        for text in [
            'I have 3 kids and 2 dogs',
            'I am 28 and my sister is 24. How should we plan a vacation?',
            'Alex had 12 apples. Alex gave 3 apples to Kim. How many apples does Kim have?',
            'Alex has 3 pens and 2 pads. How many pens does Alex have?',
            'A box has 8 beads and costs 5 dollars. How many beads are there?',
            'There are 10 birds. Each bird eats 3 seeds. How many seeds are left?',
            'There are 4 boxes with 8 pencils in each box. How many boxes are there?',
            'Nora got 63 on her first exam. Her average after the second exam was 70. '
            'What score did Nora get on her first exam?',
            'A tank starts with 90 liters and loses 4 liters every day. '
            'How much water has it lost after 2 weeks?',
        ]:
            with self.subTest(text=text):
                self.assertIsNone(solve(text))

    def test_runtime_routes_to_math(self):
        from bot.runtime import turn
        result = turn('A farmer has 9 crates with 8 apples in each crate. '
                      'How many apples are there altogether?', {})
        self.assertEqual(result['module'], 'word_problem')
        self.assertTrue(re.search(r'\b72$', result['reply']))


if __name__ == '__main__':
    unittest.main()
