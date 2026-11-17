"""Independent examples for composed percentages and conservative dispatch."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.percentages_r04_a6 import solve as composed


def answer(text):
    reply = solve(text)
    return None if reply is None else Fraction(reply.rsplit('Answer: ', 1)[1])


class ComposedPercentageTests(unittest.TestCase):
    def test_relative_totals_and_inverse_category(self):
        for count, rate in ((30, 20), (80, 25), (125, 40)):
            self.assertEqual(answer(
                'A park has {} birches and {}% more cedars than birches. '
                'How many trees are there in total?'.format(count, rate)),
                count*(2+Fraction(rate, 100)))
        self.assertEqual(answer(
            'There are 20% more boys than girls at a club. There are 36 boys. '
            'How many children are there in total?'), 66)

    def test_multiple_and_percentage_change(self):
        for price, percent in ((120, 15), (200, 30)):
            self.assertEqual(answer(
                'It used to cost ${} to fill a tank. A machine now has triple '
                'the capacity. Fuel prices went up by {}%. How much does it cost now?'.format(
                    price, percent)), price*3*(1+Fraction(percent, 100)))

    def test_salary_commission_and_savings(self):
        for sales, salary, commission, savings in ((4200, 350, 5, 20), (1500, 120, 8, 15)):
            expected=(salary+sales*Fraction(commission,100))*Fraction(savings,100)
            self.assertEqual(answer(
                'A salesperson sold ${} worth of goods. Her basic salary is ${}, '
                'with a {}% commission from sales. She saves {}% of her total earnings. '
                'How much money does she save?'.format(sales,salary,commission,savings)),expected)

    def test_same_income_deductions_are_not_compounded(self):
        self.assertEqual(answer(
            'A worker is paid $800 a week. 15% of his weekly income is deducted '
            'as tax. He pays a weekly bill for $35 and gives another 5% of his '
            'weekly income to charity. How much money does he have left?'),605)

    def test_nested_complements_and_query_scope(self):
        self.assertEqual(answer(
            'A team has 80 players. 25% are boys and the rest are girls. '
            'Half the girls are juniors and the other half are seniors. '
            'How many junior girls are there?'),30)
        self.assertEqual(answer(
            'A college has 240 students. 25% are girls and the rest are boys. '
            '20% of the boys joined a club. How many boys did not join a club?'),144)

    def test_dimensional_chain(self):
        self.assertEqual(answer(
            'Each lamp has 6 bulbs. A store has 3 racks, each with 4 shelves '
            'that can hold 5 lamps each. If the shelves are 80% full, '
            'how many bulbs are there on all the lamps?'),288)

    def test_sum_before_selecting_share(self):
        self.assertEqual(answer(
            'A grower picks 15 on Monday and 25 on Tuesday. '
            '30% are red and 20% are green. The rest are yellow. '
            'How many yellow fruits did the grower pick?'),20)
        self.assertEqual(answer(
            'A grower picks 15 on Monday and 25 on Tuesday. '
            '30% of the fruit are sour and the rest are not. '
            'How many non-sour fruits did the grower pick?'),28)

    def test_independent_populations(self):
        self.assertEqual(answer(
            'Mira has 80 counters and 25% of them are blue. '
            'Nell has 60 counters and 30% of them are blue. '
            'In total how many blue counters do they have?'),38)

    def test_share_difference_follows_the_requested_owner(self):
        self.assertEqual(answer(
            'Lena has 40 books. She has read 25% of them. Her sister has read '
            '60% of them. How many more books has her sister read than Lena?'),14)

    def test_complementary_percentage_query(self):
        self.assertEqual(answer(
            'A garden has 18 poppies. There are 42 lilies and 30 roses. '
            'What percentage of the flowers are not poppies?'),80)

    def test_insurance_and_fixed_rebate(self):
        self.assertEqual(answer(
            'A hospital visit cost $240 and a scan cost $360. '
            'Insurance covered 75%. How much was the out-of-pocket cost?'),150)
        self.assertEqual(answer(
            'A shopper buys a device for $240. There is 15% cashback. '
            'She also receives a rebate for $12. How much does the device cost after the offers?'),192)

    def test_stock_removal_and_annual_interval(self):
        self.assertEqual(answer(
            'A collector has 300 tokens. Of these, 50 tokens are damaged. '
            'She gets rid of the damaged tokens and throws out 20% of her remaining tokens. '
            'How many tokens does she have left?'),200)
        self.assertEqual(answer(
            'A workshop uses 120 kilograms of supplies every 4 months. '
            'Production will increase by 25%. How much does it need in a year?'),450)

    def test_abstention_and_extra_quantities(self):
        for text in (
                'I have 3 kids and 2 dogs.',
                'I saved 20% of my income and have 3 kids and 2 dogs.',
                'A store has 120 counters and 30% are blue. Another store has '
                '45 boxes. How many blue counters are there?',
                "We're learning about costs. A desk costs $90 with a 15% discount. "
                'How much would we pay?'):
            p=Problem.read(text)
            self.assertIsNone(None if p is None else composed(p))


if __name__ == '__main__':
    unittest.main()
