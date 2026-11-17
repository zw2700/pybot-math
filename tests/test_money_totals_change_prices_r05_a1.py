"""Independent variations of linked prices and multi-stage money arithmetic."""
import unittest
from fractions import Fraction

from bot.math.problem import Problem
from bot.math.skills.money_totals_change_prices_3_steps_r05_a1 import solve


def answer(text):
    p = Problem.read(text)
    result = solve(p) if p else None
    return result[0] if result else None


class LinkedMoneyTests(unittest.TestCase):
    def test_modified_categories(self):
        for small, large, a, b in [(7, 4, 3, 8), (11, 6, 2, 5)]:
            self.assertEqual(answer(
                'A stall sells small lanterns for ${} each and large lanterns '
                'for ${} each. A visitor bought {} small lanterns and {} large '
                'lanterns. How much did the visitor pay?'.format(a, b, small, large)),
                small*a+large*b)

    def test_local_measure_binding(self):
        self.assertEqual(answer(
            'A cook bought 7 pounds of flour for $2 per pound and 3 pounds '
            'of sugar for $4 per pound. How much money did the cook spend?'), 26)

    def test_change_and_exact_cents(self):
        self.assertEqual(answer(
            'A shopper has $20. She buys 6 pairs of gloves for $1.25 a pair '
            'and a scarf for $4. How much money does she have left?'), Fraction(17, 2))
        self.assertEqual(answer(
            'A shopper buys 3 small lanterns at $2.25 each and 2 large '
            'lanterns at $5 each. How much did she spend, in cents?'), 1675)

    def test_schedules_and_calendar(self):
        self.assertEqual(answer(
            'A worker earns $13 an hour. She works 5 hours a day and '
            '18 days a month. Determine her annual salary.'), 14040)
        self.assertEqual(answer(
            'A worker earns $7 an hour. She works 3 days each week and '
            '4 hours each time. After 5 weeks, how much money has she earned?'), 420)

    def test_installments(self):
        self.assertEqual(answer(
            'A club costs $9 per month and has a $24 down payment. '
            'How much will a member pay for the first 2 years?'), 240)

    def test_sales_and_expenses(self):
        self.assertEqual(answer(
            'A breeder bought 3 animals for $80 each. They had 7 babies. '
            'She sells each baby for $90. How much is her total profit?'), 390)

    def test_grouped_rates_and_summed_stocks(self):
        self.assertEqual(answer(
            'A factory packs 8 buttons in each bag. A clerk sells 6 bags '
            'on Monday and 9 bags on Tuesday. Each button sells for $0.30. '
            'How much money did the clerk earn?'), 36)
        self.assertEqual(answer(
            'A keeper has 4 animals. They each give birth to 3 babies. '
            'Each baby needs 2 treatments. Each treatment costs $7. '
            'How much do all the treatments cost?'), 168)

    def test_overtime_and_material_costs(self):
        self.assertEqual(answer(
            'A worker gets paid $16 every hour up to a total of 30 hours, '
            'after which she gets paid double that amount per hour. '
            'How much does she get paid for a 35-hour workweek?'), 640)
        self.assertEqual(answer(
            'A craft worker works 3 hours a day for 2 days. She is paid '
            '$25 an hour. The cost for supplies was $38. '
            'How much profit did she earn?'), 112)

    def test_threshold_discount_and_coin_groups(self):
        self.assertEqual(answer(
            'A store offers a $3 discount for every $20 purchase. '
            'A shopper bought 75 badges sold at eighty cents each. '
            'How much money did the shopper pay?'), 51)
        self.assertEqual(answer(
            'A child has 3 jars of quarters. Each jar can hold 80 quarters. '
            'A toy costs $45. How much money will the child have left '
            'after buying the toy?'), 15)

    def test_inverse_value_and_cash_option(self):
        self.assertEqual(answer(
            'A stall has 3 lamps and some clocks. A lamp costs $12 '
            'and a clock costs $8. The stock is worth $92. '
            'How many clocks does the stall have?'), 7)
        self.assertEqual(answer(
            'A shopper can buy an appliance for $700 cash or $100 '
            'down payment and $40 a month for 18 months. '
            'How much can she save by paying cash?'), 120)

    def test_menu_quantities(self):
        self.assertEqual(answer(
            'A cafe lists a waffle that costs $4 and each scoop costs $2. '
            'Any sauce costs $1 and nuts cost $3. A diner orders a waffle '
            'with 3 scoops, double sauce, and nuts. '
            'How much will the order cost?'), 15)

    def test_calculation_keeps_its_context_through_routing(self):
        from bot.runtime import turn
        result = turn(
            'A tutor teaches 4 sessions a day and works 15 days a month. '
            'She is paid $8 per session. After working 2 months, '
            'how much has she earned in total?', {})
        self.assertEqual(result['module'], 'word_problem')
        self.assertTrue(result['reply'].endswith('Answer: 960'))

    def test_abstains_on_unresolved_quantities(self):
        for text in [
            'I have 3 kids and 2 dogs.',
            'A shopper buys 4 small lanterns for $3 each and 5 large lanterns. '
            'How much money did the shopper spend?',
            'A shopper buys 4 small lanterns at $3 each and gets a discount. '
            'How much money did the shopper spend?',
            'A worker earns $12 per hour and works 6 hours. She gets a bonus. '
            'How much money did the worker earn?',
            'A shopper buys 6 hats at $9 each. How much does each hat cost?',
            'A shopper buys 6 hats at $9 each every day. '
            'How much does she spend in a month?',
            'Nora has $80. Petra spent $25 on a dress. '
            'How much money does Nora have left?',
            'A shop sells small and large lamps for $7 each. '
            'It has 4 small lamps and 8 large lamps. '
            'How much is each large lamp?',
            'A child pays 4 quarters per day and 8 quarters per week. '
            'How much money does the child pay per month?',
            'A worker earns $9 per hour and works 4 hours a day for '
            '5 days. How much does the worker earn per hour?',
        ]:
            with self.subTest(text=text):
                self.assertIsNone(answer(text))


if __name__ == '__main__':
    unittest.main()
