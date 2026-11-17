"""Comparison equations with varied amounts, owners, directions and unknowns."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.comparisons_r01_a2 import solve as compare


def answer(text):
    reply = solve(text)
    return None if reply is None else Fraction(reply.rsplit('Answer: ', 1)[1])


class ComparisonTests(unittest.TestCase):
    def test_direct_and_inverse_affine_comparison(self):
        for base, factor, delta in [(13, 4, 7), (18, 3, 2), (21, 5, 9)]:
            large = base*factor+delta
            relation = ('Nora has {} more than {} times the number of beads Inez has. ').format(delta, factor)
            self.assertEqual(answer(relation + 'Inez has {} beads. How many beads does Nora have?'.format(base)), large)
            self.assertEqual(answer(relation + 'Nora has {} beads. How many beads does Inez have?'.format(large)), base)
            self.assertEqual(answer(relation + 'They have {} beads total. How many beads does Inez have?'.format(large+base)), base)

    def test_chain_with_relative_clause(self):
        self.assertEqual(answer('Nora walks three times as many miles as Inez, who walks '
                                '4 times as many miles as Omar. Nora walks 96 miles. '
                                'How many miles does Omar walk?'), 8)

    def test_implicit_factor_and_category(self):
        self.assertEqual(answer('A shop has twice as many jackets as scarves. '
                                'There are 72 garments total. How many scarves are there?'), 24)
        self.assertEqual(answer('Nora has 12 beads and Inez has 4 fewer beads than Nora. '
                                'How many beads does Inez have?'), 8)

    def test_ages_and_total(self):
        self.assertEqual(answer('The sum of Nora and Inez\'s ages is 23. '
                                'Nora is 5 years older than Inez. How old is Nora?'), 14)
        self.assertEqual(answer('Nora is 4 years older than Inez but 6 years younger than Omar. '
                                'Nora is 17 years old. What is the sum of Inez and Omar\'s ages?'), 36)

    def test_decline_unexplained_or_inconsistent_quantities(self):
        examples = [
            'Nora has twice as many beads as Inez. Nora has 12 beads. Inez has 9 beads. How many beads does Inez have?',
            'Nora has twice as many beads as Inez. Nora has 12 beads. A box costs 7 dollars. How many beads does Inez have?',
            'There are twice as many jackets as scarves. There are 12 scarves. How many gloves are there?',
            'Nora bought three times as many toys for her younger son as she bought for her elder son. The elder son received 40 toys. How many toys did Nora buy?',
        ]
        for text in examples:
            with self.subTest(text=text):
                self.assertIsNone(compare(Problem.read(text)))
        self.assertIsNone(solve('I have 3 kids and 2 dogs'))


if __name__ == '__main__':
    unittest.main()
