"""Independent variations and abstention checks for multi-stage money rules."""
import random
import unittest
from fractions import Fraction

from bot.math.problem import Problem
from bot.math.skills.money_totals_change_prices_4_steps_r13_a5 import solve


def answer(text):
    problem = Problem.read(text)
    result = solve(problem) if problem else None
    return result[0] if result else None


class MultiStageMoneyTests(unittest.TestCase):
    def test_denominations_and_coins(self):
        self.assertEqual(answer(
            'Nora has four $10 bills, two $5 bills, and $2 in loose coins. '
            'She buys a lamp that costs $17. How much money is left in her wallet?'), 35)
        self.assertEqual(answer(
            'A shopper buys a basket that costs $12 and a vase that costs $7. '
            'She gave the cashier three $10 bills and $1 in loose coins. '
            'How much change will she receive?'), 12)

    def test_reordered_catalog_and_exact_prices(self):
        for a, b, pa, pb in [(4, 7, 2, 3), (9, 2, 5, 8)]:
            text = ('A shop sells striped ribbons for ${} each and plain ribbons '
                    'for ${} each. A customer buys {} plain ribbons and {} '
                    'striped ribbons. How much money does the customer spend?')
            self.assertEqual(answer(text.format(pa, pb, b, a)), a*pa+b*pb)
        self.assertEqual(answer(
            'A clerk sells 7 small boxes for $1.25 each and 3 large boxes '
            'for $2.50 each. How much money did the clerk make?'), Fraction(65, 4))

    def test_remaining_inventory(self):
        self.assertEqual(answer(
            'There are 70 red ribbons and 60 blue ribbons in a stall. '
            'A red ribbon costs $2 and a blue ribbon costs $3. '
            'How much does the stall earn if 12 red ribbons and 8 blue ribbons '
            'are left?'), 272)

    def test_common_buyers(self):
        self.assertEqual(answer(
            'A shop sells badges for $3 each and stickers for $0.25 each. '
            'How much money do 8 students need in total if each of them gets '
            '2 badges and 4 stickers?'), 56)

    def test_daily_basket_over_a_week(self):
        self.assertEqual(answer(
            'A visitor eats 3 snack bars and 2 fruits every evening. '
            'Each snack bar costs $2 and each fruit costs $1. '
            'How much does it cost to feed the visitor for a week?'), 56)

    def test_wage_and_tips_over_separate_days(self):
        self.assertEqual(answer(
            'A courier has base pay of $8 an hour. The courier earns a $3 '
            'tip per customer. On Saturday the courier worked 3 hours and '
            'served 4 people. On Sunday the courier worked 2 hours and served '
            '6 people. How much money did the courier earn in total?'), 70)

    def test_dozen_conversion(self):
        self.assertEqual(answer(
            'A shop sells 3 dozen red ribbons for $2 each and 5 blue ribbons '
            'for $4 each. How much money did the shop make?'), 92)

    def test_progressive_annual_fee(self):
        self.assertEqual(answer(
            'A club charges an annual membership fee. The fee increases yearly '
            'by $7. A member pays $45 in the first year. How much does membership '
            'cost in the eighth year?'), 94)

    def test_delivery_penalties(self):
        for stock, lost, broken in [(80, 4, 3), (120, 2, 9)]:
            text = ('A courier takes {} parcels to a warehouse. The warehouse '
                    'pays a $30 fee, plus $2 for every parcel delivered safely. '
                    'The courier must pay $5 each for any parcels lost or broken. '
                    'If {} parcels are lost, {} parcels are broken, and the rest '
                    'are delivered safely, how much should the courier be paid?')
            self.assertEqual(answer(text.format(stock, lost, broken)),
                             30+(stock-lost-broken)*2-(lost+broken)*5)

    def test_loan_ledger(self):
        self.assertEqual(answer(
            'A vendor borrowed $200 to open a stall and must repay him $220. '
            'The vendor spent $120 on supplies and sells 100 of them for $3 '
            'each. After paying back the loan, how much money does the vendor '
            'have left?'), 160)

    def test_initial_balance_equation(self):
        self.assertEqual(answer(
            'A store sells small lamps for $6 each and large lamps for $9 '
            'each. Dana buys 4 small lamps and 3 large lamps. She has $25 '
            'left. How much money did Dana have at first?'), 76)

    def test_missing_unit_price(self):
        self.assertEqual(answer(
            'For $90 a visitor bought 4 scarves for $8 each and 2 hats for '
            '$9 each. She also bought 5 ribbons at the same price. '
            'How much did each ribbon cost?'), 8)

    def test_missing_sales_count(self):
        self.assertEqual(answer(
            'A vendor charges $4 for a small box, $6 for a medium box, and '
            '$9 for a large box. He raised $108 in total. If he sold 4 medium '
            'boxes and 4 large boxes, how many small boxes did he sell?'), 12)

    def test_time_and_fixed_service(self):
        self.assertEqual(answer(
            'A rental service charges $12 per cart plus $2 per hour per cart. '
            'A group rents 2 carts for 3 hours and 4 carts for 5 hours. '
            'How much money does the rental service earn?'), 124)

    def test_coin_conservation(self):
        self.assertEqual(answer(
            'Alex has $25 and 80 quarters. Alex gives his brother $7 and '
            '24 quarters. How much money is Alex left with?'), 32)
        self.assertEqual(answer(
            'A visitor has $6 in quarters, dimes, and nickels. The visitor '
            'has 12 quarters and 20 dimes. How many nickels does the visitor '
            'have?'), 20)

    def test_bulk_units(self):
        self.assertEqual(answer(
            'A cook can buy 2 pounds of flour for $6. At another store, '
            'an 8-ounce bag costs $2. How much money does the cook save '
            'by buying the larger container?'), 2)

    def test_unknown_quantity_and_ambiguity_abstain(self):
        for text in [
            'A shop sells ribbons for $3 each and ribbons for $4 each. '
            'Someone buys 5 ribbons. How much money did they spend?',
            'A vendor sells badges for $2 each and stickers for $1 each. '
            'Someone buys 5 badges and 4 stickers and 3 other items. '
            'How much money did they spend?',
            'I have 3 children and 2 dogs. I spent $15 yesterday.',
            'A customer bought 3 boxes for $5 each, and used a coupon. '
            'How much money did the customer spend?',
            'A worker earns $4 an hour and works 3 hours every day from '
            'Monday to Friday and 2 hours every Saturday and Sunday. '
            'The worker earns double on weekends. How much money does '
            'the worker earn every week?',
        ]:
            self.assertIsNone(answer(text), text)

    def test_runtime_routing(self):
        from bot.runtime import turn
        random.seed(321)
        result = turn(
            'A shopper has three $20 bills and two $5 bills in her wallet. '
            'She buys a basket that costs $26. How much money is left?', {})
        self.assertEqual(result['module'], 'word_problem')
        self.assertTrue(result['reply'].endswith('44'), result['reply'])


if __name__ == '__main__':
    unittest.main()
