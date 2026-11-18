"""Money equations transfer across quantities, nouns, and query directions."""
import unittest
from fractions import Fraction

from bot.math.problem import Problem
from bot.math.skills import money_totals_change_prices_1_2_steps_r11_a5 as money


def answer(text):
    problem = Problem.read(text)
    result = money.solve(problem) if problem else None
    return result[0] if result else None


class MoneyEquationTests(unittest.TestCase):
    def test_incoming_and_outgoing_cash_have_distinct_signs(self):
        self.assertEqual(answer(
            'Omar has $70. He writes a cheque for $12. His client pays him $18. '
            'He spends $25 on supplies. How much money is remaining?'), 51)
        self.assertEqual(answer(
            'A shopper spent $7 on lunch and gave his brother $3. '
            'How much did he have at the beginning if he has $19 now?'), 29)

    def test_fractional_prices_remain_exact(self):
        self.assertEqual(answer(
            'A courier buys an envelope for $0.35, 4 days a week. '
            'After 3 weeks, how much money has the courier spent?'), Fraction(21, 5))

    def test_promotion_counts_include_free_items(self):
        self.assertEqual(answer(
            'A stall offers buy 2 get one free. A shopper gets 18 markers '
            'with a normal price of $1.75. How much does the shopper pay?'), 21)
        self.assertIsNone(answer(
            'A stall offers buy 2 get one free. A shopper gets 17 markers '
            'with a normal price of $1.75. How much does the shopper pay?'))
        self.assertEqual(answer(
            'A stall offers buy 1 get one free. A shopper gets 8 markers '
            'with a normal price of 50 cents. How many cents does the shopper pay?'), 200)

    def test_ticket_categories_are_read_from_the_text(self):
        for first, second in [('veteran', 'volunteer'), ('senior', 'apprentice')]:
            with self.subTest(first=first, second=second):
                text = ('A group paid $157 for admission tickets. The price of a {} '
                        'ticket is $9, and a {} ticket is $4. There are 3 more {}s '
                        'than {}s. How many {}s are in the group?').format(
                            first, second, first, second, second)
                self.assertEqual(answer(text), 10)

    def test_required_people_are_whole_people(self):
        self.assertEqual(answer(
            'Each person contributes $12 to the campaign. How many people must '
            'fund a $100 project if the organizer has $15 already?'), 8)

    def test_weight_units_bind_to_materials(self):
        self.assertEqual(answer(
            'A workshop needs 2.5kg of resin and 250 grams of pigment. '
            'The resin costs $4 per kilogram, and the pigment $12 per kilogram. '
            'How much does the workshop pay for the ingredients?'), 13)

    def test_power_and_total_energy_are_distinct(self):
        self.assertEqual(answer(
            'Electricity costs $0.20 per kWh. A machine has a power draw of '
            '1.5 kW. How much will the operator pay for using it for 4 hours?'), Fraction(6, 5))
        self.assertIsNone(answer(
            'Electricity costs $0.20 per kWh. A machine has a total consumption '
            'of 1.5 kWh. How much will the operator pay after 4 hours?'))

    def test_coin_count_is_not_a_cash_amount(self):
        self.assertEqual(answer(
            'A customer pays for a $.63 item with a $1 bill. The cashier gives '
            'the smallest number of coins possible as change. '
            'How many coins does the customer receive?'), 4)

    def test_missing_item_price_uses_remaining_count(self):
        self.assertEqual(answer(
            'A shopper spent $130 on 6 pieces of clothing. One piece was $20 '
            'and another piece was $30. The other pieces were all the same price. '
            'How many dollars was one of the other pieces?'), 20)

    def test_unmodeled_multipliers_and_averages_abstain(self):
        self.assertIsNone(answer(
            'A saver had $90 in her account. She spent $10 on lunch and then '
            'spent thrice as much on supplies. How much money is left?'))
        self.assertIsNone(answer(
            'A stall sells hats for $6 each and scarves for $9 each. '
            'A shopper buys 2 hats and 3 scarves. '
            'What is the average cost of each item in dollars?'))
        self.assertIsNone(answer(
            'Mira had $80 in her bank account. Nola gave Theo $15 for lunch. '
            'How much money does Mira have left?'))
        self.assertIsNone(answer(
            'A worker earns $20 and spends $30 on supplies. '
            'How much money did the worker earn?'))

    def test_unpriced_stock_and_chat_abstain(self):
        self.assertIsNone(answer(
            'A stall sells one set of blue tiles at $6 each and one set of red '
            'tiles at $9 each. A shopper buys two sets of blue tiles and three '
            'sets of red tiles and four sets of green tiles. How much did she spend?'))
        for text in ['I have 3 kids and 2 dogs.',
                     'I have $50 and spent $10. What is a good restaurant?',
                     'My two children are 8 and 11. How should I save for school?']:
            self.assertIsNone(answer(text), text)

    def test_financial_value_and_balance_questions_reach_the_gate(self):
        for text in [
            'A saver has $40 in the bank and makes a $15 deposit. What is her bank balance?',
            'A shopper had $60 and spent $18 on supplies. What is the value in dollars of the rest?',
        ]:
            self.assertIsNotNone(Problem.read(text))

    def test_runtime_keeps_the_verified_calculation(self):
        from bot.runtime import turn
        result = turn(
            'A shopper buys 7 kg of potatoes at the supermarket. If 2 kg of '
            'potatoes costs $8, how much will she pay?', {})
        self.assertEqual(result['module'], 'word_problem')
        self.assertTrue(result['reply'].endswith('Answer: 28'))


if __name__ == '__main__':
    unittest.main()
