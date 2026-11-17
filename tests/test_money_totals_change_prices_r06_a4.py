"""Independent variations of money equations and their abstention boundaries."""
import unittest

from bot.math import solve as engine
from bot.math.problem import Problem
from bot.math.skills.money_totals_change_prices_1_2_steps_r06_a4 import solve


def answer(text):
    problem = Problem.read(text)
    result = solve(problem) if problem else None
    return result[0] if result else None


class MoneyEquationTests(unittest.TestCase):
    def test_missing_price_and_flat_discount(self):
        for count, price, total, coupon in [(3, 8, 71, 6), (7, 4, 83, 9)]:
            self.assertEqual(answer(
                'A visitor bought {} candles for ${} each and a vase. '
                'She paid ${} in total. How much did the vase cost?'.format(count, price, total)),
                total-count*price)
            self.assertEqual(answer(
                'A visitor bought {} candles for ${} each. She has a ${} off coupon. '
                'How much did she pay?'.format(count, price, coupon)), count*price-coupon)

    def test_group_change_equation(self):
        self.assertEqual(answer(
            'Twelve colleagues plan to split the cost of a gift equally. '
            'Three of them drop out. The remaining colleagues split it equally. '
            'Each share is now $4 more. How much does the gift cost?'), 144)

    def test_quote_is_a_total_not_a_unit_price(self):
        self.assertEqual(answer(
            'A cook needs 8 pounds of apples for a recipe. If 3 pounds of '
            'apples costs $9, how much will she pay?'), 24)
        reply = engine(
            'A cook needs 8 pounds of apples for a recipe. If 3 pounds of '
            'apples costs $9, how much will she pay?')
        self.assertTrue(reply.endswith('Answer: 24'))

    def test_two_kinds_and_separate_option(self):
        self.assertEqual(answer(
            'Adult tickets cost $17 and tickets for children cost $6. '
            'The party has 2 adults and 5 children. '
            'What is the total price they will pay?'), 64)
        self.assertEqual(answer(
            'A family can buy a family pass for $80 or pay for tickets separately. '
            'Adult tickets cost $17 and children\'s tickets cost $6. '
            'The family has 2 adults and 5 children. '
            'How much will they pay for separate tickets?'), 64)

    def test_directed_ledger_and_current_balance(self):
        self.assertEqual(answer(
            'Rina had some money. Tomas gave her another $40. Rina then '
            'gave Paula $90. She has $160 left. '
            'How much money did Rina have at first?'), 210)
        self.assertEqual(answer(
            'A girl received $10 from her aunt and $15 from her uncle. '
            'With her savings she now has $80. She buys 3 games at $12 each. '
            'How much does she have left?'), 44)

    def test_cash_left_inverse_and_loan_duration(self):
        self.assertEqual(answer(
            'Juice costs $0.75 an ounce. A buyer brought $8 and leaves with $2. '
            'How many ounces of juice did she buy?'), 8)
        self.assertEqual(answer(
            'A customer buys a scooter for $1800. She pays $300 and pays '
            'the rest by giving $125 a month. '
            'In how many months will the scooter be fully paid for?'), 12)

    def test_exact_prices_and_round_trip(self):
        self.assertEqual(answer(
            'A museum charges $2 per person. A group of 7 friends is going. '
            'They brought $20. How much change will they receive?'), 6)
        self.assertEqual(answer(
            'A crossing takes 3 hours in one direction. Hiring a guide costs '
            '$12.50 per hour. How much will the guide cost for the crossing '
            'back and forth?'), 75)

    def test_rate_comparison_and_calendar(self):
        self.assertEqual(answer(
            'Elena earns 2.5 times more money per hour than Pablo. '
            'Pablo earns $8 per hour. How much does Elena earn for a 7-hour day?'), 140)
        self.assertEqual(answer(
            'A child buys a roll on Mondays for $1.25 and a bun on Fridays '
            'for $2.75. How much does the child spend in a year?'), 208)

    def test_credit_calendar_savings_and_volume_price(self):
        self.assertEqual(answer(
            'A buyer is allowed a credit of $90. She spent the full credit limit '
            'and paid $17 on Monday and $23 on Friday. '
            'How much credit does she still need to pay?'), 50)
        self.assertEqual(answer(
            'A customer pays her insurance quarterly at $135. '
            'How much does she pay in a year?'), 540)
        self.assertEqual(answer(
            'Each month, a worker deposits his $3500 paycheck in the bank. '
            'His expenses amount to $2700 per month. '
            'How much does he save over the course of a year?'), 9600)
        self.assertEqual(answer(
            'Four bottles of 3 liters of oil cost $36. '
            'What is the price of 1 liter of oil?'), 3)

    def test_money_answer_keeps_its_subject_through_routing(self):
        from bot.runtime import turn
        result = turn(
            'For breakfast a shopper spent $2 on orange juice and $3 on toast. '
            'At lunch she spent $7 on soup and $4 on milk. '
            'How much more money did she spend on lunch than on breakfast?', {})
        self.assertEqual(result['module'], 'word_problem')
        self.assertTrue(result['reply'].endswith('Answer: 6'))

    def test_declines_unexplained_values_and_relations(self):
        for text in [
            'I have 3 kids and 2 dogs.',
            'A girl has $50 and her friend has $80. How much should she spend?',
            'A buyer bought 3 candles for $8 each and 5 vases. She has a $2 coupon. '
            'How much did she pay?',
            'A buyer bought 3 candles for $8 each. She has a discount. '
            'How much did she pay?',
            'Adult tickets cost $17 and tickets for children cost $6. '
            'The group has 2 adults, 5 children and 3 teachers. '
            'How much will they pay?',
            'A worker earns $12 an hour and worked 7 hours. She gets a bonus. '
            'How much money did she earn?',
            'Nora buys a dress for $40. Petra buys a coat for $60. '
            'Nora has a $5 off coupon. How much did Nora spend?',
            'A shopper wants a book that costs $6 and a cookbook that costs $14. '
            'She has $18 saved. How much more money does she need to buy all '
            'two books?',
            'A shop sells a lamp for $40 and a stool costs twice as much. '
            'A buyer spent $150 in total. What was the price of another item?',
            'A girl and her friend want a game that costs $50. They sell '
            'cookies for $5 each. How many cookies do they need to sell '
            'to buy the game?',
        ]:
            with self.subTest(text=text):
                self.assertIsNone(answer(text))


if __name__ == '__main__':
    unittest.main()
