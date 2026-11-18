"""Independent, varied examples for multi-stage percentage equations."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.percentages_r13_a2 import solve as skill


def answer(text):
    result = solve(text)
    return None if result is None else Fraction(result.rsplit('Answer: ', 1)[1])


class MultistagePercentageTests(unittest.TestCase):
    def test_discount_tax_and_credit_order(self):
        for price in (120, 360, 800):
            text = ('A desk costs ${}. It is on sale for 25% off. A coupon takes off $12. '
                    'There is then a 10% tax on the remaining price. How much does it cost?').format(price)
            self.assertEqual(answer(text), (price*Fraction(3,4)-12)*Fraction(11,10))

    def test_basket_percentage(self):
        for quantity in (3, 7, 11):
            text = ('Rae ordered {} boxes at $12 each and 5 folders at $4 each. '
                    'The delivery fee is 10% of the total sales. How much did Rae pay?').format(quantity)
            self.assertEqual(answer(text), (quantity*12+20)*Fraction(11,10))

    def test_item_discounts(self):
        self.assertEqual(answer(
            'A bag of flour costs $20 and is sold at 30% off. A jar of jam costs $10 '
            'and is sold at 10% off. How much will you save if you buy 4 bags of flour '
            'and 6 jars of jam?'), 30)

    def test_loan_interest_on_installment(self):
        self.assertEqual(answer(
            "A bicycle costs $900, with a down payment of $300. The loan has 12 equal monthly payments. "
            "Interest is 8% of that month's payment. How much are the monthly payments?"), 54)

    def test_sale_stock_and_debt(self):
        self.assertEqual(answer(
            'A shop has 400 items that retail for $20 each. It offers a 25% discount and '
            'sells 80% of the items. It owes $2000 to creditors. How much money is left?'), 2800)

    def test_mixed_expense_shares(self):
        self.assertEqual(answer(
            'A worker earns $2400 per month and spends 60% of it on bills, one-fourth on '
            'rent, and saves the rest. How much does she save per month?'), 360)

    def test_sequential_group_remainders(self):
        self.assertEqual(answer(
            'A school bought 12 boxes of pencils. Each box contains 10 pencils. '
            'It gave 25% to pupils and one-third of what is remaining to teachers. '
            'How many pencils are left?'), 60)

    def test_nested_complement(self):
        self.assertEqual(answer(
            'A farm has 200 goats. 30% of the goats have a black patch. 20% of the goats '
            'without a black patch have a white patch, and the remaining goats have no patch. '
            'How many goats have no patch?'),112)

    def test_parallel_complements(self):
        self.assertEqual(answer(
            'A club has 200 members. Half of the members are adults, the other half are children. '
            '30% of the adults have bikes and 20% of the children have bikes. '
            'How many members have bikes?'),50)

    def test_repeated_removals(self):
        for size, rounds, percent in ((800, 4, 25), (100, 2, 10), (500, 3, 20)):
            text = ('A company has {} employees. There will be {} rounds of layoffs. '
                    'For each round of layoff, {}% of the remaining employees will be laid off. '
                    'How many employees will be laid off in total?').format(size, rounds, percent)
            self.assertEqual(answer(text), size*(1-(1-Fraction(percent,100))**rounds))

    def test_updated_win_percentage(self):
        self.assertEqual(answer(
            'A player has played 80 matches and won 60% of them. She plays 20 more matches '
            'and loses 5 of them. What is her new win percentage?'),63)

    def test_salary_commission_remaining_allocation(self):
        self.assertEqual(answer(
            'A sales agent earns a basic salary of $10 per hour plus a 20% commission. '
            'She worked 80 hours and sold $6000 worth of goods. She allocated 30% of her '
            'total earnings to savings and the rest to monthly expenses. '
            'How much were her monthly expenses?'),1400)

    def test_inverse_spending(self):
        self.assertEqual(answer(
            'A shopper spent 20% of her money on food and 50% of the remainder on bills. '
            'After spending $12 on books, she is left with $28. '
            'How much money did she have initially?'),100)

    def test_sequential_fixed_and_percentage_removals(self):
        self.assertEqual(answer(
            'A notebook has 300 pages. A writer wrote on 60 pages, then wrote on 25% '
            'of the remaining pages. A spill damaged 10% of the empty pages. '
            'How many empty pages are remaining?'),162)
        self.assertEqual(answer(
            'A donor received $1000. She gave 1/2 of the amount to a charity, 1/5 of the '
            'remaining amount to a library, and 25% of the remaining amount to a museum. '
            'Calculate the total amount she kept.'),300)

    def test_discount_above_threshold(self):
        for count in (2, 8):
            text = ('A shop gives a 20% discount for the amount of the sale that was over $100. '
                    'A buyer buys {} items that each cost $25. What does the order cost?').format(count)
            total=count*25
            self.assertEqual(answer(text),total-max(0,total-100)*Fraction(1,5))

    def test_recurring_deposits_after_interest(self):
        for years in (2, 3, 4):
            text = ('A bank account earns 5% interest every year. A saver puts $200 in it, '
                    'and then 20 each year. How much money is in it after {} years?').format(years)
            expected=Fraction(200)
            for _ in range(years):
                expected=expected*Fraction(21,20)+20
            self.assertEqual(answer(text),expected)

    def test_percentage_profit_uses_cost_as_base(self):
        self.assertEqual(answer(
            'A store marks a lamp 50% above the cost. A 20% discount was given during a sale. '
            'The lamp costs $40. What is the percent profit?'),20)

    def test_counted_coupons(self):
        self.assertEqual(answer(
            'A buyer pays $20 per bottle. The bottles are 25% off. She also has 4 $3 coupons. '
            'How much will 4 bottles cost?'),48)

    def test_valued_cube_above_one_hundred_percent(self):
        self.assertEqual(answer(
            'A seller has a cube of metal that measures 2 inches on each side. A cubic inch '
            'of metal weighs 5 ounces. Each ounce of metal sells for $4. He sells it for '
            '125% of its metal value. How much does he sell it for?'),200)

    def test_trade_in(self):
        self.assertEqual(answer(
            'A customer trades in a used machine. His old machine cost 300 dollars and he got '
            '50% of the value for it. He buys a new machine that costs $800 with a 25% discount. '
            'How much came out of his pocket?'),450)

    def test_unsupported_and_chat(self):
        for text in (
            'I have 3 kids and 2 dogs.',
            'I am learning percentages. What is 20% of 400?',
            'A chair costs $90 and the tax is 10%. Its weight is 7 pounds. How much does it cost?',
            'A shop has 12 chairs and 7 tables. The profit is 20%. How much money does it make?',
            'A desk costs $500 each with 10% off and 5% tax. Shipping takes 8 days. How much does it cost?',
            'A desk costs $500 with 10% off and 5% tax. It weighs 8kg. How much does it cost?',
            'A desk costs $500 with either 10% off or 20% off. How much does it cost?',
            'A desk costs $500. It is 20% off and has 10% tax. A €10 coupon applies. How much does it cost?',
            'A notebook has 200 pages. 20% of the pages are red and 30% are blue. How many pages are green?',
        ):
            p = Problem.read(text)
            self.assertIsNone(skill(p) if p else None)


if __name__ == '__main__':
    unittest.main()
