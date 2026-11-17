"""Generalization checks for multi-stage comparison composition."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.comparisons_r05_a6 import solve as compare


def answer(text):
    reply = solve(text)
    return Fraction(reply.rsplit('Answer: ', 1)[1]) if reply else None


class MultiStageComparisonTests(unittest.TestCase):
    def test_shortfall_and_inverse_chain(self):
        for base, shortage, factor in [(13, 7, 3), (21, 4, 5), (8, 2, 4)]:
            text = ('Aria needs {} more beads to have twice as many beads as Bella. '
                    'Cara has {} times as many beads as Bella. Cara has {} beads. '
                    'How many more beads does Cara have than Aria?').format(shortage, factor, factor*base)
            self.assertEqual(answer(text), factor*base-(2*base-shortage))

    def test_scaled_sum_on_both_sides(self):
        for a, delta, left, right in [(11, 5, 2, 3), (23, 7, 3, 5)]:
            text = ('Aria has {} tokens and Bella has {} more tokens than Aria. '
                    'If {} times the sum of Aria and Bella\'s tokens is {} times '
                    'the number of tokens Cara has, how many tokens does Cara have?').format(a, delta, left, right)
            self.assertEqual(answer(text), Fraction((2*a+delta)*left, right))

    def test_explicit_unit_conversion(self):
        text = ('Aria worked for 3.5 hours. Bella worked for twice that amount of time '
                'and Cara worked 1.5 hours less than Bella. '
                'How many minutes did the 3 people work in total?')
        self.assertEqual(answer(text), 960)
        text = ('Aria brought four 3-pound bags of rice. Bella brought twice as much '
                'rice as Aria. Cara brought 7 pounds less than Bella. '
                'How much more rice, in ounces, did Cara bring than Aria?')
        self.assertEqual(answer(text), 80)
        text = ('Aria brought two 3-foot rolls of ribbon. Bella brought twice as much '
                'ribbon as Aria. Cara brought 3 feet less than Bella. '
                'How much more ribbon, in inches, did Cara bring than Aria?')
        self.assertEqual(answer(text), 36)

    def test_age_dates_and_invariant_difference(self):
        self.assertEqual(answer('Aria is twice as old as Bella. Bella is 11 years old. '
                                'In 4 years, what is the sum of the ages of Aria and Bella?'), 41)
        self.assertEqual(answer("Aria's older brother was twice her age 12 years ago. "
                                'Her brother is now 40 years old. How old was Aria a decade ago?'), 16)
        self.assertEqual(answer('Aria is 9 years old and her dad is 5 more than 3 times her age. '
                                'In 7 years, how many years older is her dad than her?'), 23)

    def test_person_named_after_a_month(self):
        text = ("June's ribbon is 7 inches longer than Bella's ribbon. Bella's ribbon is "
                "4 inches longer than twice the length of Cara's ribbon. "
                "Cara's ribbon is 13 inches long. How many inches longer is June's ribbon than Cara's ribbon?")
        self.assertEqual(answer(text), 24)

    def test_shared_head_and_remainder(self):
        text = ('There are 9 blue buttons. Green buttons are twice as many as blue buttons. '
                'There are 5 fewer white buttons than the blue and green buttons combined. '
                'How many buttons are there in total?')
        self.assertEqual(answer(text), 49)
        text = ('A box contains 70 buttons. There are 8 blue buttons and three times as many '
                'red buttons as blue buttons. The same number of white buttons as the blue '
                'and red buttons combined are in the box. The rest are gold buttons. '
                'How many gold buttons are there?')
        self.assertEqual(answer(text), 6)

    def test_individual_sale_prices(self):
        text = ('Aria has 8 books. Bella has three times as many books as Aria. '
                'Aria will sell her books for $4 each while Bella will sell them for $2.50 each. '
                'How much money will they earn in total?')
        self.assertEqual(answer(text), 92)

    def test_daily_and_calendar_sequences(self):
        text = ('On the first day, Aria earned $7. Every day after that, she earned '
                '$3 more than the previous day. How much did she earn after 6 days?')
        self.assertEqual(answer(text), 87)
        text = ('Aria saves $9 in March. Each month, she saves twice as much as her '
                "previous month's savings. How much will she save in June?")
        self.assertEqual(answer(text), 72)

    def test_ratio_budget_and_material_choices(self):
        text = ('Aria will have 48 guests. Twice as many guests want coffee as tea. '
                'Each coffee drink costs $4 and each tea drink costs $3. '
                'How much is the total budget?')
        self.assertEqual(answer(text), 176)
        text = ('A ring takes 8 grams of clay and sells for $10. A band takes twice '
                'as much clay and sells for $25. Aria has 160 grams of clay. '
                'How much more money will she make turning it all into bands instead of rings?')
        self.assertEqual(answer(text), 50)

    def test_weighted_container_outputs(self):
        text = ('A box of cork can create 5 tokens, a box of rubber can create 7 tokens, '
                'and a box of metal can make twice the amount of tokens compared to cork. '
                'How many tokens can Aria make if she owns 4 boxes of cork, 3 boxes '
                'of rubber, and 6 boxes of metal?')
        self.assertEqual(answer(text), 101)

    def test_runtime_keeps_the_calculated_amount(self):
        from bot.runtime import turn
        cases = [
            ('Aria and Bella are baking bread. Aria brought two 4-pound bags of flour. '
             'Bella brought three times as much flour as Aria. '
             'How much more flour, in ounces, did Bella bring than Aria?', 256),
            ("Aria's website got 60 visitors a day for the first 6 days. On the last day "
             'of the week it got twice as many visitors as every other day combined. '
             'She gets $0.25 per visit. How much did she make that week?', 270),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                result = turn(text, {})
                self.assertEqual(result['module'], 'word_problem')
                self.assertEqual(Fraction(result['reply'].rsplit('Answer: ', 1)[1]), expected)

    def test_declines_unexplained_quantities_and_changes(self):
        cases = [
            'Aria has twice as many beads as Bella. Bella has 13 beads. A ticket costs $9. How many beads does Aria have?',
            'Aria worked 7 hours. Bella worked twice as long as Aria. Bella gave 3 books away. How many hours did they work in total?',
            'A box contains 60 buttons. There are 8 blue buttons and twice as many red buttons as blue buttons. How many green buttons are there?',
            'Aria has 15 beads. Bella has three times more than Aria. How many beads do they have in total?',
            'Aria has 8 books. Bella has three times as many books as Aria. Aria will sell her bikes for $4 each while Bella will sell her bikes for $2 each. How much money will they earn in total?',
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertIsNone(compare(Problem.read(text)))
        self.assertIsNone(solve('I have 3 kids and 2 dogs.'))


if __name__ == '__main__':
    unittest.main()
