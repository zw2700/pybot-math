"""Shared quantity syntax, independent of any particular word-problem skill."""
import unittest
from fractions import Fraction

from bot.math.numbers import parse_number, read_numbers


class QuantitySyntaxTests(unittest.TestCase):
    def test_fraction_denominators_and_notations(self):
        cases = {
            'two fifths': Fraction(2, 5),
            'three-eighths': Fraction(3, 8),
            '7 tenths': Fraction(7, 10),
            'a hundredth': Fraction(1, 100),
            'one twenty-third': Fraction(1, 23),
            'one twenty-first': Fraction(1, 21),
            'one twenty-second': Fraction(1, 22),
            'two and three fifths': Fraction(13, 5),
            '2 and a half': Fraction(5, 2),
            'two and 1/2': Fraction(5, 2),
            '2 1 / 3': Fraction(7, 3),
            'one million two hundred thousand and six': Fraction(1200006),
            '2.5 million': Fraction(2500000),
            '$1,200 thousand': Fraction(1200000),
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(parse_number(raw), expected)
                self.assertEqual([n.value for n in read_numbers(raw)], [expected])

    def test_sign_currency_percentage_and_offsets(self):
        cases = {
            '-12.5': (Fraction(-25, 2), 'number'),
            '-$4.50': (Fraction(-9, 2), 'money'),
            '£-4.50': (Fraction(-9, 2), 'money'),
            'two fifths percent': (Fraction(1, 250), 'percent'),
            'one third percent': (Fraction(1, 300), 'percent'),
            '12.5 per cent': (Fraction(1, 8), 'percent'),
        }
        for raw, (expected, kind) in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(parse_number(raw), expected)
                text = 'The recorded quantity was {} today.'.format(raw)
                quantities = read_numbers(text)
                self.assertEqual(len(quantities), 1)
                quantity = quantities[0]
                self.assertEqual((quantity.value, quantity.kind), (expected, kind))
                self.assertEqual(text[quantity.start:quantity.end], raw)

    def test_invalid_inputs_are_not_added_together(self):
        for raw in ['', 'one one', 'twenty thirty', 'one hundred hundred',
                    'one thousand million', '1,23', '12 dogs', '$', '25%%']:
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    parse_number(raw)

    def test_units_ordinals_and_separate_quantities(self):
        for text, expected in [
            ('5 seconds and 3 minutes', [5, 3]),
            ('six and eight', [6, 8]),
            ('2kg and 3.5cm', [2, Fraction(7, 2)]),
            ('the 21st and 33rd loads', []),
            ('the fifth floor and twenty-first row', []),
            ('64 seventh graders', [64]),
            ('a fiftieth birthday', []),
            ('one-third are green', [Fraction(1, 3)]),
            ('one third hour', [Fraction(1, 3)]),
            ('160 quarters', [160, Fraction(1, 4)]),
            ('someone has stonework and quarterbacks', []),
            ('1/0 and 2 1/0', []),
        ]:
            with self.subTest(text=text):
                self.assertEqual([n.value for n in read_numbers(text)], expected)


if __name__ == '__main__':
    unittest.main()
