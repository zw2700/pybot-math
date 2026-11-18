"""Arithmetic invariants and refusal checks for composed comparisons."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.comparisons_r08_a4 import solve as compare


def answer(text):
    reply = solve(text)
    return Fraction(reply.rsplit('Answer: ', 1)[1]) if reply else None


class ComparisonCompositionTests(unittest.TestCase):
    def test_inventory_conservation_with_final_reserve(self):
        for stock, first, extra, reserve in [(50, 7, 3, 5), (91, 12, 4, 9), (33, 4, 2, 6)]:
            text = ('Aria has {} stones. Bella got {} stones from her, and Cora got {} more '
                    'than Bella. How many more stones would Aria need to give away to be '
                    'left with only {} of them?').format(stock, first, extra, reserve)
            self.assertEqual(answer(text), stock-2*first-extra-reserve)

    def test_age_translation_and_inverse_comparison(self):
        for old_age, elapsed, factor in [(20, 4, 2), (27, 6, 3), (48, 5, 4)]:
            text = ('Aria is {} times as old as Bella. In {} years, she will be {}. '
                    'How old will Bella be?').format(factor, elapsed, old_age+elapsed)
            self.assertEqual(answer(text), Fraction(old_age, factor)+elapsed)
            text = ('{} years ago, Aria was {} times as old as Bella. '
                    'If Bella will be {} in {} years, how old is Aria now?').format(
                        elapsed, factor, old_age+elapsed, elapsed)
            self.assertEqual(answer(text), factor*(old_age-elapsed)+elapsed)

    def test_equal_sharing_preserves_combined_amount(self):
        for base, factor in [(6, 3), (9, 5), (7, 7)]:
            story = ('Aria has {} times as many cards as Bella. Bella has {} cards. ').format(factor, base)
            self.assertEqual(answer(story+'How many cards do they have together?'), (factor+1)*base)
            self.assertEqual(answer(story+'How many cards will they each have if they put the '
                                    'cards together and shared them equally between themselves?'),
                             Fraction((factor+1)*base, 2))

    def test_objects_are_distinct_and_irrelevant_counts_stay_separate(self):
        for a, b, k in [(4, 7, 3), (5, 11, 2), (9, 13, 4)]:
            text = ('Aria has {} oranges and 2 apples. Bella has 8 oranges and {} apples. '
                    'If Cora has twice as many oranges as Aria and {} times as many apples '
                    'as Bella, how many fruits in total does Cora have?').format(a, b, k)
            self.assertEqual(answer(text), 2*a+k*b)
        text = ('Aria picked 12 bags of peaches and 9 bags of plums. Bella picked '
                '4 bags of peaches more than Aria, and 3 fewer bags of plums than Aria. '
                'How many bags of fruit did Bella pick, in total?')
        self.assertEqual(answer(text), 22)

    def test_overlap_is_subtracted_once(self):
        for base, factor, overlap in [(10, 3, 4), (24, 2, 9), (11, 4, 2)]:
            text = ('Aria and Bella combine their guest lists. Aria has {} guests. Bella has '
                    '{} times as many guests as Aria. They share {} guests. '
                    'How many people are on the combined list?').format(base, factor, overlap)
            self.assertEqual(answer(text), base*(factor+1)-overlap)

    def test_new_query_forms(self):
        self.assertEqual(answer('In 2040, Aria is 21 years old. Bella is 7 years older than '
                                'Aria. What year was Bella born in?'), 2012)
        self.assertEqual(answer('Aria wears a size 4. Bella wears a size twice as large as '
                                "Aria's. Cora wears a size twice Bella's size minus 3. "
                                'What size does Cora wear?'), 13)

    def test_abstains_on_unexplained_quantities(self):
        p = Problem.read('Aria has 5 stones. Bella has twice as many stones as Aria. '
                         'How many stones can Bella buy for 17 dollars?')
        self.assertIsNotNone(p)
        self.assertIsNone(compare(p))
        self.assertIsNone(solve('I have 3 kids and 2 dogs.'))
        self.assertIsNone(solve('My sister is 8 years older than me.'))

    def test_fractional_increment_keeps_its_meaning(self):
        self.assertEqual(answer('Aria spent 1/4 times more money than Bella. Bella spent $80. '
                                'What is the total amount of money they spent together?'), 180)


if __name__ == '__main__':
    unittest.main()
