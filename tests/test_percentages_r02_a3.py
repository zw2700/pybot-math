"""Arithmetic and interpretation checks for the percentage readers."""
import unittest
from fractions import Fraction

from bot.math import solve


def answer(text):
    reply = solve(text)
    return None if reply is None else Fraction(reply.rsplit('Answer: ', 1)[1])


class PercentageTests(unittest.TestCase):
    def test_discount_and_inverse_vary_independently(self):
        for price, percent in [(84, 30), (210, 25), (360, 40)]:
            with self.subTest(price=price, percent=percent):
                self.assertEqual(answer(
                    'A merchant sells a lamp that costs ${}. There is a {}% discount. '
                    'How much will a buyer pay?'.format(price, percent)),
                    Fraction(price)*(1-Fraction(percent, 100)))
                self.assertEqual(answer(
                    'A customer bought a table for ${}. It was marked {}% off. '
                    'What was the original price of the table?'.format(price, percent)),
                    Fraction(price)/(1-Fraction(percent, 100)))

    def test_tax_and_interest_are_added(self):
        self.assertEqual(answer(
            'A buyer purchases a desk that costs $85. The tax is 20%. '
            'How much does the buyer pay after tax?'), 102)
        self.assertEqual(answer(
            'A borrower receives $450 from a lender and promises to repay with '
            'an interest of 8%. How much will the borrower pay back?'), 486)

    def test_nested_selection_and_complement(self):
        for count in (200, 600):
            self.assertEqual(answer(
                'A shop has {} beads in stock. 35% are blue. Of the blue beads, '
                '40% are shiny. How many shiny blue beads are there?'.format(count)),
                Fraction(count)*Fraction(35, 100)*Fraction(40, 100))
        self.assertEqual(answer(
            'An orchard contains 250 trees. Half of the trees bear fruit, '
            '20% of the fruit trees are male. How many female fruit trees are there?'), 100)

    def test_percentage_share_and_inverse_complement(self):
        self.assertEqual(answer(
            'There are 240 pupils at a school. 35% of the pupils are boys. '
            'How many girls are at the school?'), 156)
        self.assertEqual(answer(
            'A school has some pupils. 35% of the pupils are boys and the number '
            'of girls is 156. How many boys are at the school?'), 84)

    def test_rate_then_percentage(self):
        self.assertEqual(answer(
            'A museum has 75 visitors entering every hour. It is open for 6 hours. '
            '40% of the visitors see an exhibit. How many visitors see the exhibit?'), 180)

    def test_percentages_from_disjoint_counts(self):
        self.assertEqual(answer(
            'A person does 16 stretches, 12 lunges, and 20 squats. '
            'What percentage of the exercises were lunges?'), 25)

    def test_known_original_inside_condition_is_not_the_unknown(self):
        self.assertEqual(answer(
            'A shopper is preparing to visit a store for a new coat. '
            'How much money should the shopper bring if the original price is '
            '$120 and there is a discount of 25%?'), 90)

    def test_abstains_on_statements_and_unaccounted_quantities(self):
        for text in (
                'I have 3 kids and 2 dogs.',
                'I saved 20% of my income and have 3 kids and 2 dogs.',
                "We're learning about shopping costs. A desk costs $90 with a 15% "
                'discount. How much would we pay?',
                'A shop has $80 in sales and $35 in expenses. The tax is 10%. '
                'How much does the owner take home?'):
            self.assertIsNone(answer(text))

    def test_cannot_recover_a_total_from_zero_percent(self):
        self.assertIsNone(answer(
            'A diner paid a 0% tip of $0 at a restaurant. '
            'The diner now wants to leave 15% instead. How much is a 15% tip?'))


if __name__ == '__main__':
    unittest.main()
