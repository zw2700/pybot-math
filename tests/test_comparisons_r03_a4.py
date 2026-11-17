"""Affine comparison parsing with varied operands and conservative refusals."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.comparisons_r03_a4 import solve as compare


def answer(text):
    reply = solve(text)
    return None if reply is None else Fraction(reply.rsplit('Answer: ', 1)[1])


class ExtendedComparisonTests(unittest.TestCase):
    def test_omitted_as_and_inverse(self):
        for base, extra in [(17, 4), (23, 8), (30, 11)]:
            relation = 'Lina has {} more than twice as much money Petra has. '.format(extra)
            self.assertEqual(answer(relation + 'Petra has ${}. How much money does Lina have?'.format(base)), 2*base+extra)
            self.assertEqual(answer(relation + 'Lina has ${}. How much money does Petra have?'.format(2*base+extra)), base)

    def test_sold_ratio_and_total(self):
        for total in (36, 75, 120):
            self.assertEqual(answer('Lina sold twice as many tickets as Petra did. '
                                    'In total they sold {} tickets. How many tickets did Petra sell?'.format(total)), total/3)

    def test_category_anchor_is_not_combined_total(self):
        self.assertEqual(answer('There are three times as many adults as children in a choir. '
                                'If there are 9 child members, how many members are there in total?'), 36)
        self.assertEqual(answer('A cooler has 45 bottles of cola and lemonade. '
                                'There are twice as many bottles of cola as there are of lemonade. '
                                'How many bottles of lemonade are there?'), 15)
        self.assertEqual(answer('There are twice as many red beads as blue beads in a box. '
                                'There are 12 red beads in total. How many blue beads are there?'), 6)

    def test_compound_ratio_with_offset(self):
        self.assertEqual(answer('A workshop has 5 less than four times as many chairs as desks. '
                                'There are 70 chairs and desks combined. How many chairs are there?'), 55)
        self.assertEqual(answer('Lina, Petra and Omar can lift a combined weight of 100 pounds. '
                                'Lina can lift twice as much as Petra, and Petra can lift '
                                '4 pounds less than three times the amount that Omar can lift. '
                                'How much can Lina lift?'), Fraction(296, 5))

    def test_parallel_categories(self):
        self.assertEqual(answer('A store has some notebooks and four times as many pencils. '
                                'It has 65 items total. How many notebooks does it have?'), 13)
        self.assertEqual(answer('A library has some books about geology and three times as many '
                                'books about astronomy. There are 64 books total. '
                                'How many astronomy books are there?'), 48)

    def test_price_of_and_purchase_count(self):
        self.assertEqual(answer('The price of the desk is $80 and the price of the chair '
                                'is $25 less than the price of the desk. '
                                'Calculate the total price of the furniture.'), 135)
        self.assertEqual(answer('A folder costs four times as much as a pencil. '
                                'A pencil costs $1.25. How much will Lina pay for 6 folders?'), 30)

    def test_current_and_future_ages(self):
        self.assertEqual(answer("Lina's age is twice Petra's age. If Petra is 8 years old, "
                                'how old will Lina be after 7 years?'), 23)
        self.assertEqual(answer('Lina is three times as old as Petra. In 4 years Petra will be '
                                '15 years old. How old is Lina now?'), 33)

    def test_comparisons_at_different_dates(self):
        for years, younger in [(4, 9), (7, 13), (12, 20)]:
            common = ('In {} years, Lina will be three times as old as Petra. '
                      'Petra is currently {} years old. How old is Lina now?').format(years, younger)
            present = ('In {} years, Lina will be three times as old as Petra today. '
                       'Petra is currently {} years old. How old is Lina now?').format(years, younger)
            self.assertEqual(answer(common), 3*(younger+years)-years)
            self.assertEqual(answer(present), 3*younger-years)
        self.assertEqual(answer('Lina is twice as old as Petra will be in 5 years. '
                                'Petra is 11 years old now. How old is Lina now?'), 32)
        self.assertEqual(answer('Lina will be 18 years old in 4 years. At that time her sister '
                                'Petra will be twice as old as Lina. '
                                "How old is Lina's sister now?"), 32)
        self.assertEqual(answer('Lina is twice as old as Petra is today. '
                                'Petra turned 5 a year ago. How old is Lina today?'), 12)

    def test_two_relations_anchor_each_other(self):
        self.assertEqual(answer('A shop has 30 more red beads than blue beads. '
                                'It has four times as many red beads as blue beads. '
                                'How many blue beads are there?'), 10)

    def test_numeric_labels_and_weekdays(self):
        self.assertEqual(answer('Room 3 has 7 fewer than three times as many chairs as Room 8. '
                                'Room 3 has 29 chairs. How many chairs are in Room 8?'), 12)
        self.assertEqual(answer('Lina sold twice as many tickets on Monday as she did on Tuesday, '
                                'and she sold three times as many on Tuesday as she did on Friday. '
                                'Lina sold 12 tickets on Friday. How many tickets did she sell on Monday?'), 72)

    def test_mixed_unit_comparison(self):
        self.assertEqual(answer('Lina practiced for 2.5 hours last weekend. Petra practiced '
                                '15 minutes less than Lina. How many minutes did they practice together?'), 285)
        self.assertEqual(answer('Lina carried 3 pounds of flour. Petra carried 4 ounces more '
                                'than Lina. How many ounces did they carry in total?'), 100)

    def test_inverse_single_unknown(self):
        self.assertEqual(answer('9 less than three times the number of trees in a park is 60. '
                                'How many trees are in the park?'), 23)

    def test_declines_unexplained_numbers_and_questions(self):
        examples = [
            'Lina sold twice as many tickets as Petra. Lina sold 24 tickets and Petra sold 9 tickets. How many tickets did Lina sell?',
            'Lina has twice as many beads as Petra. Petra has 10 beads. A box costs 7 dollars. How many beads does Lina have?',
            'There are twice as many blue beads as red beads. There are 6 red beads. How many green beads are there?',
            'Lina has twice as many beads as Petra. Petra has 10 beads. How many beads will Lina have after buying 4 more?',
            "Lina is twice as old as Petra. Petra is 10 years old. How old is Lina's sister?",
        ]
        for text in examples:
            with self.subTest(text=text):
                self.assertIsNone(compare(Problem.read(text)))
        self.assertIsNone(solve('I have 3 children and 2 cats'))
        self.assertIsNone(solve('I have 3 children and 2 cats. How old is my cat?'))


if __name__ == '__main__':
    unittest.main()
