"""Comparison invariants with changed amounts, units and owner names."""
import unittest
from fractions import Fraction

from bot.math import solve


def answer(text):
    reply = solve(text)
    return Fraction(reply.rsplit('Answer: ', 1)[1]) if reply else None


class ShortComparisonTests(unittest.TestCase):
    def test_grouped_left_conserves_total(self):
        for total, delta, factor in [(56, 8, 3), (97, 7, 4), (45, 3, 2)]:
            text = ('Mira has {} times as many tokens as Len and the two of them together '
                    'have {} fewer tokens than Ora. If Ora has {} tokens, '
                    'how many tokens does Mira have?').format(factor, delta, total)
            self.assertEqual(answer(text), Fraction((total-delta)*factor, factor+1))

    def test_affine_ages_and_reciprocal_counts(self):
        for base, delta, factor in [(7, 4, 3), (12, 5, 4), (18, 2, 2)]:
            text = ('Tara is {} years older than {} times the age of Niko. '
                    'If Niko is {} years old, how old is Tara?').format(delta, factor, base)
            self.assertEqual(answer(text), base*factor+delta)
            text = ('Tara has twice as many shells as Niko, and Niko has {} times fewer '
                    'shells than Ora. If Ora has {} shells, '
                    'how many shells does Tara have?').format(factor, base*factor)
            self.assertEqual(answer(text), base*2)

    def test_destination_categories_remain_distinct(self):
        for base, factor, extra in [(11, 2, 7), (16, 4, 3), (9, 3, 6)]:
            text = ('The shop sold {} more than {} times the number of tickets to the '
                    'action movie as it did to the comedy movie. If the shop sold {} '
                    'tickets to the comedy movie, how many tickets did it sell to the '
                    'action movie?').format(extra, factor, base)
            self.assertEqual(answer(text), base*factor+extra)

    def test_repeat_order_and_stock_balance(self):
        text = ('Uma and Ben ordered food. Uma ordered 7 rolls, and Ben ordered three '
                'times as many rolls as Uma did. If they order another set of rolls, '
                'how many rolls will Ben have eaten in all?')
        self.assertEqual(answer(text), 42)
        text = ('Uma gives 5 rolls to one of her friends and keeps three times this '
                'amount for herself. If she had originally made 37 rolls, how many '
                'rolls does she have left to give to her other friends?')
        self.assertEqual(answer(text), 17)

    def test_missing_information_and_chat_abstain(self):
        self.assertIsNone(solve('I have 3 kids and 2 dogs.'))
        self.assertIsNone(solve('Mira has twice as many shells as Len. '
                                'How many shells does Mira have?'))
        self.assertIsNone(solve('The shop sold twice as many tickets to the action '
                                'movie as it did to the comedy movie. '
                                'How many tickets did it sell to the action movie?'))
        self.assertIsNone(solve('Aria collected 12 shells, and Bella collected twice '
                                'that number. How many shells did Chris and Bella '
                                'collect in total?'))
        self.assertEqual(answer('Aria collected 12 shells, and Bella collected twice '
                                'that number. Calculate the total number of shells '
                                'they collected.'), 36)

    def test_event_ratio_is_independent_of_the_action(self):
        for action in ('laugh', 'jump', 'sing'):
            text = ('Aria {}s three times as often as Bella. Together they {} '
                    '40 times. How many times does Bella {}?').format(action, action, action)
            self.assertEqual(answer(text), 10)

    def test_future_age_and_unit_conversion(self):
        self.assertEqual(answer('Mira is 8 years younger than Len. If Len is 30 years '
                                'old now, how old will Mira be next year?'), 23)
        self.assertEqual(answer('Mira takes 20 minutes to finish the course. Len takes '
                                'six times as long as Mira. How many hours does Len '
                                'take to finish the course?'), 2)
        self.assertEqual(answer("In six years, I'll be three times my sister's age. "
                                'The sum of our ages will then be 40 years old. '
                                'How old am I now?'), 24)

    def test_denominations_and_weighted_prices(self):
        for small, large, ratio, count in [(5, 20, 3, 4), (10, 50, 2, 6), (2, 10, 4, 8)]:
            total = (small*ratio+large)*count
            text = ('The fund contains only ${} and ${} bills, which amount to ${}. '
                    'The number of ${} bills is {} times as many ${} bills. '
                    'How many ${} bills do they have in their fund?').format(
                        small, large, total, small, ratio, large, large)
            self.assertEqual(answer(text), count)
        text = ('30 adults and 20 children go to a concert. The price of an adult '
                "ticket is three times that of a child's ticket. What is the price "
                'of an adult ticket if the total amount collected is $1100?')
        self.assertEqual(answer(text), 30)

    def test_remainder_and_measurement_conservation(self):
        text = ('In a basket, there are 4 pears, three times as many apples, and some '
                'plums. In total there are 25 fruits in the basket. '
                'How many plums are in the basket?')
        self.assertEqual(answer(text), 9)
        text = ('Mira had 6 pounds of clay. Len had 8 ounces less than 5 pounds of clay. '
                'How many more ounces of clay did Mira have than Len?')
        self.assertEqual(answer(text), 24)


if __name__ == '__main__':
    unittest.main()
