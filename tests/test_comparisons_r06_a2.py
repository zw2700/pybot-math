"""Generalization and refusal checks for explicit comparison compositions."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.comparisons_r06_a2 import solve as compare


def answer(text):
    reply = solve(text)
    return Fraction(reply.rsplit('Answer: ', 1)[1]) if reply else None


class ComparisonCompositionTests(unittest.TestCase):
    def test_reversed_age_and_calendar_dates(self):
        self.assertEqual(answer('Aria is younger than Bella by 4 years. Aria is 17 years old. '
                                "What will be Bella's age 6 years from now?"), 27)
        self.assertEqual(answer('Aria is 8 years younger than Bella. In 1998, Aria is 13 years old. '
                                'In 2007, how old is Bella?'), 30)

    def test_time_shifts_apply_to_both_people(self):
        for elapsed, old_ratio, new_ratio in [(4, 4, 2), (6, 3, 2)]:
            text = ('Aria and Bella work together. {} years ago, Aria had {} times as much '
                    'experience as Bella. Now she has {} times as much experience as Bella. '
                    'How many years of experience does Bella have now?').format(elapsed, old_ratio, new_ratio)
            self.assertEqual(answer(text), Fraction(elapsed*(old_ratio-1), old_ratio-new_ratio))
        self.assertEqual(answer('8 years from now, Aria will be 3 times as old as she was '
                                '6 years ago. How old is she now?'), 13)

    def test_object_categories_are_distinct_from_the_actor(self):
        text = ('The number of towels Aria washed was 7 more than the number of sheets Bella washed. '
                'The number of sheets Bella washed was 4 times the number of blankets she washed. '
                'If Bella washed 9 blankets, how many towels did Aria wash?')
        self.assertEqual(answer(text), 43)

    def test_affine_category_total_and_exclusion(self):
        self.assertEqual(answer('A shop has 3 less than 4 times the amount of red pins as blue pins. '
                                'If there are 47 total pins, how many red pins are there?'), 37)
        self.assertEqual(answer('Aria has twice as many red buttons as blue buttons. '
                                'She has 3 fewer green buttons than blue buttons. '
                                'She has 16 red buttons. How many buttons are not blue?'), 21)

    def test_comparison_then_transaction(self):
        self.assertEqual(answer('Aria has 11 books and Bella has twice the number of Aria\'s Books '
                                'but she lost 4 of them. How many books are left with Bella?'), 18)
        self.assertEqual(answer('Aria has 4 times as much candy as Bella. Aria then adds 7 more '
                                'pieces of candy to her collection. If Bella has 8 pieces of '
                                'candy, how many does Aria have in total?'), 39)
        self.assertEqual(answer('Aria buys 9 pounds of rice. She uses all but 2 pounds in soup. '
                                'She uses three times as many pounds of vegetables as rice. '
                                'How many pounds of vegetables did she use?'), 21)

    def test_compared_activity_chain(self):
        text = ('Aria played 7 hours of tennis. She ran for three times as long as she played '
                'tennis, and she practiced on the flute for twice as long as she ran. '
                'How many hours did Aria practice on the flute?')
        self.assertEqual(answer(text), 42)
        text = ('Aria played tennis. She ran for three times as long as she played '
                'tennis, and she practiced on the flute for twice as long as she ran. '
                'If she practiced on the flute for 54 hours, how many hours did Aria play tennis?')
        self.assertEqual(answer(text), 9)
        self.assertEqual(answer('Aria played 3 hours of tennis. She ran for twice as long as '
                                'she played tennis. How many minutes did Aria run?'), 360)

    def test_periods_and_local_omissions(self):
        self.assertEqual(answer('On Monday, Aria sold 37 raffle tickets. She sold twice as many '
                                'on Tuesday. On Friday, she sold 19 raffle tickets. How many '
                                'more raffle tickets were sold on Tuesday than Friday?'), 55)
        self.assertEqual(answer('There were 17 blue pins. There were three times as many red '
                                'pins in this box. How many pins were in the box?'), 68)

    def test_compared_withdrawals_and_time_allocations(self):
        self.assertEqual(answer('Aria has 70 cards. Aria gives 7 cards to Bella. '
                                'Aria gives Cara three times as many cards as she gave to Bella. '
                                'How many cards does Aria have left?'), 42)
        self.assertEqual(answer('Aria spends four times as long studying history as reading poetry. '
                                'If she worked 150 minutes today, how many minutes did she '
                                'spend reading poetry?'), 30)

    def test_relative_ages_need_no_absolute_anchor(self):
        text = ('Three friends compare ages. Aria is 4 months older than Bella while Bella is '
                '9 months older than Cara. How much older in months is Aria than Cara?')
        self.assertEqual(answer(text), 13)

    def test_pairwise_totals_and_weighted_family_prices(self):
        text = ('The hat and scarf cost $35. The hat and coat cost $95. '
                'The coat costs 4 times as much as the scarf. How much does the coat cost?')
        self.assertEqual(answer(text), 80)
        text = ('Aria takes her 4 children to a museum. They buy tickets for the whole family. '
                'The cost of an adult ticket is $5 more than the cost of a child ticket. '
                'The total cost of the 6 tickets is $70. What is the cost of an adult ticket?')
        self.assertEqual(answer(text), 15)

    def test_unexplained_quantities_units_and_actions_decline(self):
        cases = [
            'Aria has 8 books and Bella has twice as many books. A ticket costs $7. How many books do they have in total?',
            'Aria buys 9 pounds of rice. She uses all but 2 kilograms in soup. She uses twice as many pounds of vegetables as rice. How many pounds of vegetables did she use?',
            'Aria played 7 hours of tennis. She ran twice as long as Bella played tennis. How many hours did Aria run?',
            'The hat and scarf cost $35. The hat and coat cost $95. The coat costs 4 times as much as the scarf. A bag costs $12. How much does the coat cost?',
            'Aria bought 9 apples and Bella bought twice as many oranges. How many apples did they buy in total?',
            'Aria scored 18 points and Bella scored twice that number. What is the total number of points Cara and Bella scored?',
            'Aria is a student with 3 siblings and his weight is 60 kilograms. Aria is twice as heavy as Bella. How much does Bella weigh?',
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertIsNone(compare(Problem.read(text)))
        self.assertIsNone(solve('I have 3 kids and 2 dogs.'))

    def test_runtime_retains_math_answer(self):
        from bot.runtime import turn
        text = ('Aria buys 12 pounds of flour. She uses all but 3 pounds in bread. '
                'She uses twice as many pounds of water as flour. '
                'How many pounds of water did she use?')
        result = turn(text, {})
        self.assertEqual(result['module'], 'word_problem')
        self.assertEqual(Fraction(result['reply'].rsplit('Answer: ', 1)[1]), 18)


if __name__ == '__main__':
    unittest.main()
