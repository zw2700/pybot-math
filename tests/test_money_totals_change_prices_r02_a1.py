"""Purchase reasoning, exact arithmetic, and confident abstention."""
import unittest
from fractions import Fraction

from bot.math.problem import Problem
from bot.math.skills.money_totals_change_prices_1_2_steps_r02_a1 import solve


def answer(text):
    p = Problem.read(text)
    result = solve(p) if p else None
    return result[0] if result else None


class MoneyTests(unittest.TestCase):
    def test_basket_and_change(self):
        for count, price, extra, cash in [(4, 7, 9, 50), (6, 3, 11, 40)]:
            text = ('A shopper buys {} candles that cost ${} each. She also buys '
                    '${} in soap. She pays with a ${} bill. How much change '
                    'does she get?').format(count, price, extra, cash)
            self.assertEqual(answer(text), cash-count*price-extra)

    def test_fractional_prices_remain_exact(self):
        self.assertEqual(answer(
            'A gardener buys 3 pots that cost $2.35 each. She pays with a $10 bill. '
            'How much money does she get back?'), Fraction(59, 20))

    def test_ledger_and_unknown_start(self):
        self.assertEqual(answer(
            'A student saved $16 in June and $29 in July. She spent $18 on '
            'a backpack and $7 on stationery. How much money does she have left?'), 20)
        self.assertEqual(answer(
            'A student bought a backpack for $18 and stationery for $7. '
            'She had $20 left. How much money did she have at first?'), 45)

    def test_shortage_and_discount(self):
        self.assertEqual(answer(
            'A shopper wants a chair that costs $45 and a table that costs $80. '
            'She has $90. How much more money does she need?'), 35)
        self.assertEqual(answer(
            'A notebook costs $8. A student bought 7 notebooks and received a '
            'discount of $1.25 each. How much did the student pay in all?'), Fraction(189, 4))

    def test_flat_fee_and_weight(self):
        self.assertEqual(answer(
            'The delivery cost is a $6 fee plus $1.50 per pound. '
            'The package weighs 8 pounds. How much does delivery cost?'), 18)

    def test_cents_and_currency_units(self):
        self.assertEqual(answer(
            'A child buys 4 badges that cost 35 cents each. She pays with a $2 bill. '
            'How much money does she get back?'), Fraction(3, 5))
        self.assertEqual(answer(
            'A child buys 4 badges that cost 35 cents each. She pays with a $2 bill. '
            'How much change does she get, in cents?'), 60)

    def test_linked_rates(self):
        self.assertEqual(answer(
            'A workshop makes 12 baskets per day. They sell each basket for $8. '
            'How much money will they earn in 5 days?'), 480)

    def test_profit_and_pack_size(self):
        self.assertEqual(answer(
            'A baker spent $28 on ingredients. She made 16 buns and sells each '
            'for $3. How much was her profit?'), 20)
        self.assertEqual(answer(
            'A carton contains 24 markers and costs $18. A club needs 72 markers. '
            'How much will the markers cost?'), 54)

    def test_tax_question_routes_to_arithmetic(self):
        from bot.runtime import turn
        result = turn(
            'A worker has a salary of $90 per month. She contributes $32 a month '
            'for necessities and pays some household taxes. She has $18 left. '
            'How much did she pay in taxes this month?', {})
        self.assertEqual(result['module'], 'word_problem')
        self.assertTrue(result['reply'].endswith('Answer: 40'))

    def test_unsupported_relations_abstain(self):
        for text in [
            'I have 3 kids and 2 dogs.',
            'A baker buys 4 loaves for $8 and sells them for $12. '
            'How much was the profit?',
            'A pet eats 3 biscuits that cost $2 each every evening. '
            'How much money does it cost to feed the pet for a week?',
            'Ada has $40. Bruno spent $12 on lunch yesterday. '
            'How much money does Ada have left?',
            'A shopper buys 4 candles at $5 each. '
            'How much does each candle cost?',
            'A shopper buys 4 candles at $5 each every day. '
            'How much money does she spend in a week?',
            'I have $30 and my friend has $20. How much money should I invest?',
            'A shopper buys 4 candles at $5 each and 2 lamps. '
            'How much money did she spend?',
            'A shopper buys 4 candles at $5 each and gets a discount. '
            'How much money did she spend?',
            'A worker earns $8 per hour and works 3 hours. She paid $5 for lunch. '
            'How much money did she earn?',
            'A shopper buys 4 candles at $5 each. How much does each candle cost?',
        ]:
            with self.subTest(text=text):
                self.assertIsNone(answer(text))


if __name__ == '__main__':
    unittest.main()
