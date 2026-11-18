"""Category selection must preserve the stated population and all counts."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.percentages_r02_a3 import solve as simple
from bot.math.skills.percentages_r04_a6 import solve as composed
from bot.runtime import turn


def answer(text):
    reply = solve(text)
    return None if reply is None else Fraction(reply.rsplit('Answer: ', 1)[1])


class CategoryPercentageTests(unittest.TestCase):
    def test_several_categories_and_complement_with_an_explicit_total(self):
        for total, first, second in ((50, 10, 15), (80, 12, 28), (125, 15, 35)):
            for noun, a, b in (('tokens', 'red', 'blue'), ('crystals', 'rough', 'smooth')):
                story = ('A cabinet has {} {} in total. There are {} {} {} '
                         'and {} {} {}. ').format(total, noun, first, a, noun, second, b, noun)
                with self.subTest(total=total, noun=noun):
                    self.assertEqual(answer(story + 'What percentage of the {} are {} or {}?'.format(noun, a, b)),
                                     100*Fraction(first+second, total))
                    self.assertEqual(answer(story + 'What percentage of the {} are not {}?'.format(noun, a)),
                                     100*Fraction(total-first, total))

    def test_a_longer_list_is_still_a_partition(self):
        text = ('A collection contains 10 red tokens, 20 blue tokens, 15 green tokens, '
                '5 yellow tokens, 25 white tokens, and 25 black tokens. '
                'What percentage of the tokens are red or white?')
        self.assertEqual(answer(text), 35)
        self.assertEqual(Fraction(turn(text, {})['reply'].rsplit('Answer: ', 1)[1]), 35)

    def test_owners_and_objects_select_categories(self):
        story = 'Nora scored 10 points. Inez scored 15 points. Omar scored 25 points. '
        self.assertEqual(answer(story + 'What percentage of the points did Nora and Inez score?'), 50)
        self.assertEqual(answer(story + 'What percentage of the points did Nora not score?'), 80)

    def test_inconsistent_totals_and_unexplained_quantities_abstain(self):
        for text in (
                'A cabinet has 20 tokens in total. There are 15 red tokens and 15 blue tokens. '
                'What percentage of the tokens are red or blue?',
                'A cabinet has 50 tokens. There are 10 red tokens and 15 blue tokens. '
                'What percentage of the tokens are red after 3 days?',
                'A cabinet has 10 red tokens and 15 blue tokens. '
                'What percentage of the tokens are there?',
                'A cabinet has 10 red tokens and sells 5 red tokens. '
                'What percentage of the tokens are red?'):
            p = Problem.read(text)
            for skill in (simple, composed):
                with self.subTest(text=text, skill=skill.__module__):
                    self.assertIsNone(skill(p))


if __name__ == '__main__':
    unittest.main()
