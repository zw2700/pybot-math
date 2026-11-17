"""Rate relations must survive changed quantities and reject missing information."""
import unittest
from fractions import Fraction

from bot.math import solve as solve_all
from bot.math.problem import Problem
from bot.math.skills.rates_and_unit_rates_r06_a3 import solve


def answer(text, integrated=False):
    if integrated:
        reply = solve_all(text)
        return Fraction(reply.rsplit('Answer: ', 1)[1]) if reply else None
    problem = Problem.read(text)
    result = solve(problem) if problem else None
    return result[0] if result else None


class ShortRateTests(unittest.TestCase):
    def test_remaining_work_varies_quantities(self):
        for goal, done, days in [(360, 72, 6), (250, 91, 3), (93, 12, 5)]:
            text = ('A student has to read {} pages for a course. She read {} '
                    'pages yesterday and has {} days left. How many pages '
                    'must she read each day to complete the course?').format(
                        goal, done, days)
            self.assertEqual(answer(text), Fraction(goal-done, days))

    def test_combined_consumption_converts_volume(self):
        text = ('A hiker needs 250 ml of water per hour and his companion '
                'needs 150 ml of water per hour. They can carry 3 liters. '
                'How many hours will the water last them together?')
        self.assertEqual(answer(text), Fraction(15, 2))

    def test_measured_output_and_compound_time(self):
        self.assertEqual(answer(
            'A press stamps 48 tokens every 7 minutes. How many tokens '
            'does it stamp in 35 minutes?'), 240)
        for conjunction in (' and', ''):
            text = ('A van traveled 150 miles in 2 hours{} 30 minutes. '
                    'What was its speed in miles per hour?').format(conjunction)
            self.assertEqual(answer(text), 60)

    def test_per_producer_payment_has_two_denominators(self):
        self.assertEqual(answer(
            "A choir's singers each earn $30 per concert. There are 5 singers "
            'and they earned $900 in total. How many concerts have they played?'), 6)

    def test_fixed_work_is_inverse(self):
        text = ('It takes 12 days for 5 painters to paint a building. '
                'How long will 10 painters take to paint the same size '
                'building working at the same rate?')
        self.assertEqual(answer(text, integrated=True), 6)

    def test_weekly_goal_and_return_journey(self):
        self.assertEqual(answer(
            'Each capsule contains 25 mg of a nutrient. The recommended '
            'daily amount is 100 mg. How many capsules are needed for '
            'the week?', integrated=True), 28)
        self.assertEqual(answer(
            'A courier drives at 30 miles per hour. She travels forth and '
            'back to a depot 45 miles away. How many hours does she spend '
            'driving there and then back?', integrated=True), 3)

    def test_chain_and_conditional_capacity(self):
        self.assertEqual(answer(
            'A cook makes 9 rolls using 2 slices each. How many bags '
            'does she need, assuming each bag has 6 slices?'), 3)
        self.assertEqual(answer(
            'A buyer purchased 6 packs for $72 in total. Each pack '
            'contains 4 cards. How much did each card cost?'), 3)

    def test_whole_capacity_rounding(self):
        self.assertEqual(answer(
            'A cook makes 20 rolls using 2 slices each. How many bags '
            'does she need, assuming each bag has 6 slices?'), 7)
        self.assertEqual(answer(
            'A carpenter has 25 feet of wire. It takes 4 feet to make '
            'a hanger. How many hangers can she make with that wire?'), 6)

    def test_unknown_relations_and_extra_quantities_abstain(self):
        for text in [
            'A driver travels 30 miles per hour but stops for a break. '
            'How many miles does she travel in 2 hours?',
            'A machine stamps 8 tokens every 3 minutes and uses 5 batteries. '
            'How many tokens can it stamp in 12 minutes?',
            'A person uses 1/2 ounce of lotion every other day and buys '
            '8-ounce bottles. How many bottles are needed for a leap year?',
            'A vendor has $60 and earns 5 euros per hour. How many hours '
            'does it take to earn that money?',
            'Two roommates want to buy a new appliance that costs $90. '
            'They earn $6 for each parcel delivered. How many parcels must '
            'they deliver for both to afford the appliance?',
            'I have 3 kids and 2 dogs.',
        ]:
            self.assertIsNone(answer(text), text)


if __name__ == '__main__':
    unittest.main()
