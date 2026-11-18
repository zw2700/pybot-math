"""Fraction spelling must not change arithmetic, scope, or source offsets."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.fractions_of_a_quantity_r03_a3 import _prepare
from bot.runtime import turn


def answer(text):
    reply = solve(text)
    return None if reply is None else Fraction(reply.rsplit('Answer: ', 1)[1])


class GeneralFractionTests(unittest.TestCase):
    def test_spelled_shares_use_the_same_scope_as_numeric_fractions(self):
        for phrase, numerator, denominator in (
                ('one eleventh', 1, 11), ('four-twelfths', 4, 12),
                ('five twenty-thirds', 5, 23), ('three fortieths', 3, 40),
                ('twenty-one hundredths', 21, 100),
                ('one hundred and twenty-one thousandths', 121, 1000)):
            for scope in ('original', 'remaining'):
                total = denominator * 120
                prefix = 'A warehouse has {} parcels. Workers shipped {} of them. '.format(total, phrase)
                text = prefix + ('Workers then shipped one-fifth of the {} parcels. '
                                 'How many parcels remain?').format(scope)
                first = total * Fraction(numerator, denominator)
                expected = total-first-Fraction(total if scope == 'original' else total-first, 5)
                with self.subTest(phrase=phrase, scope=scope):
                    self.assertEqual(answer(text), expected)

    def test_compound_numerator_in_a_comparison(self):
        text = ('Nora has one hundred and twenty-one hundredths as many widgets as Inez. '
                'Inez has 100 widgets. How many widgets does Nora have?')
        self.assertEqual(answer(text), 121)
        self.assertEqual(Fraction(turn(text, {})['reply'].rsplit('Answer: ', 1)[1]), 121)

    def test_mixed_named_fraction_and_decimal_magnitude(self):
        self.assertEqual(answer(
            'Nora wants to buy one and one-twelfth dozens of nibs. '
            'How many nibs will she have?'), 13)
        self.assertEqual(answer(
            'A depot has 1.5 thousand parcels. Workers shipped two-fifths of them. '
            'How many parcels remain?'), 900)
        self.assertEqual(answer(
            'A depot has .5 thousand parcels. Workers shipped two-fifths of them. '
            'How many parcels remain?'), 300)

    def test_existing_mixed_number_interpretation_is_preserved(self):
        p = _prepare(Problem.read(
            'Nora has one hundred and two thirds as many widgets as Inez. '
            'Inez has 3 widgets. How many widgets does Nora have?'))
        self.assertEqual(p.numbers[0].value, Fraction(302, 3))
        p = _prepare(Problem.read(
            'A ticket costs $one and a half. A pass costs $4. '
            'How much money do a ticket and a pass cost in total?'))
        self.assertEqual([(n.kind, n.value) for n in p.numbers],
                         [('money', Fraction(3, 2)), ('money', 4)])

    def test_ordinal_labels_are_not_fractional_quantities(self):
        p = _prepare(Problem.read(
            'A depot has 120 parcels on the eleventh day. Workers shipped one twelfth of them. '
            'How many parcels remain?'))
        self.assertIn('the eleventh day', p.text)
        self.assertEqual([n.value for n in p.numbers], [120, Fraction(1, 12)])
        for number in p.numbers:
            self.assertEqual(p.text[number.start:number.end], number.raw)

    def test_new_fraction_spellings_do_not_explain_unrelated_counts(self):
        for phrase in ('one twelfth', 'five twenty-thirds'):
            self.assertIsNone(answer(
                'A depot has 276 parcels. Workers shipped {} of them. '
                'A cabinet has 7 shelves. How many parcels remain?'.format(phrase)))


if __name__ == '__main__':
    unittest.main()
