"""Independent rate examples: exact units, changed values, and abstention."""
import unittest
from fractions import Fraction

from bot.math.problem import Problem
from bot.math.skills.rates_and_unit_rates_r03_a6 import solve


def answer(text):
    problem = Problem.read(text)
    result = solve(problem) if problem else None
    return result[0] if result else None


class MultistageRateTests(unittest.TestCase):
    def test_measured_rate_converts_duration(self):
        for quantity, seconds, minutes in [(9, 20, 4), (7, 12, 3), (11, 45, 2)]:
            text = ('A machine stamps {} tokens in {} seconds. At the same rate, '
                    'how many tokens does it stamp in {} minutes?').format(
                        quantity, seconds, minutes)
            self.assertEqual(answer(text), Fraction(quantity*minutes*60, seconds))

    def test_nested_rates_use_all_units(self):
        self.assertEqual(answer(
            'A studio has 6 actors. Each actor records 8 lines and each line '
            'takes 15 seconds. How many minutes do all the recordings take?'), 12)
        self.assertEqual(answer(
            'A warehouse has 3 crates, each containing 4 packages, with '
            '150 labels per package. A printer uses 30 labels to produce one '
            'poster. How many posters can the printer produce?'), 60)

    def test_remaining_budget_and_change(self):
        self.assertEqual(answer(
            'A shopper bought 7 cups at $4 each and some bowls at $6 each. '
            'She spent a total of $70. How many bowls did she buy?'), 7)
        self.assertEqual(answer(
            'A customer buys 4 board games. Each board game costs $18. '
            'He paid using a $100 bill. The clerk gave only $7 bills for '
            'his change. How many bills did he receive?'), 4)

    def test_profit_converts_bulk_cost(self):
        self.assertEqual(answer(
            'A vendor buys fruit at a cost of $18 per crate and sells it '
            'at a price of $1 per pear. Each crate contains 30 pears. '
            'How much profit does the vendor make after selling 45 pears?'), 18)

    def test_relative_arrival_and_round_trip(self):
        self.assertEqual(answer(
            'A bus travels 36 miles per hour. A cyclist follows at '
            '12 miles per hour. The route is 72 miles long. How long '
            'does the driver wait for the cyclist to catch up?'), 4)
        self.assertEqual(answer(
            'A hiker travels 18 miles at 3 miles per hour and returns '
            'at 6 miles per hour. How long does the hike take, in hours?'), 9)

    def test_decimal_currency_and_unit_price(self):
        self.assertEqual(answer(
            'A player stays at the arcade for 2 hours. She pays $.75 '
            'for every 5 minutes. How much money does she spend?'), 18)
        self.assertEqual(answer(
            'A worker earns 40 cents per parcel. It takes 12 seconds '
            'to check a parcel. How much does she earn per hour?'), 120)

    def test_extra_quantities_and_unspecified_schedules_abstain(self):
        for text in [
            'A machine stamps 9 tokens in 20 seconds and uses 4 batteries. '
            'How many tokens does it stamp in 3 minutes?',
            'A driver travels 30 miles per hour but stops for a break. '
            'How many miles does the driver travel in 2 hours?',
            'I have 3 children and 2 bicycles at home.',
        ]:
            self.assertIsNone(answer(text), text)

    def test_earlier_rule_converts_daily_minutes(self):
        from bot.math.skills.counting_and_totals_r00_a1 import _daily_groups
        p = Problem.read(
            'It takes 15 minutes to clean each of 4 cages. They are cleaned '
            'every day. How many hours are spent cleaning in 6 days?')
        self.assertEqual(_daily_groups(p)[0], 6)

    def test_dozens_and_owner_are_included_in_equal_split(self):
        from bot.math.skills.rates_and_unit_rates_r01_a4 import solve as earlier
        p = Problem.read(
            'Ari has three dozen plums to split with her five siblings. '
            'They eat the same amount. How many plums does each person get?')
        self.assertEqual(earlier(p)[0], 6)


if __name__ == '__main__':
    unittest.main()
