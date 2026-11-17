"""Rate reasoning across varied values, units, and unsupported relations."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.rates_and_unit_rates_r01_a4 import solve as rate_solve


def rate_answer(text):
    problem = Problem.read(text)
    result = rate_solve(problem) if problem else None
    return result[0] if result else None


class RateTests(unittest.TestCase):
    def test_time_conversion_both_directions(self):
        for wage, minutes in [(18, 45), (24, 75), (15, 12)]:
            text = ('A tutor earns ${} per hour for lessons. Today she taught for '
                    '{} minutes. How much did she earn?').format(wage, minutes)
            self.assertEqual(rate_answer(text), Fraction(wage*minutes, 60))
        self.assertEqual(rate_answer(
            'A worker spent 3 hours on the entire job. Each device takes 15 minutes. '
            'How many devices did the worker finish?'), 12)

    def test_measured_unit_rate(self):
        self.assertEqual(rate_answer(
            'A machine produced 84 buttons in 7 hours of operation. '
            'How many buttons did it produce per hour?'), 12)
        self.assertEqual(rate_answer(
            'A driver earned $180 for 6 hours of work yesterday. '
            'How much did the driver earn per hour?'), 30)
        self.assertEqual(rate_answer(
            'A book costs $7 per copy at the shop. A customer has $30. '
            'How many copies can the customer afford?'), 4)
        self.assertEqual(rate_answer(
            'A van carries 8 crates per trip. The warehouse has 35 crates. '
            'How many trips will the driver need to move all the crates?'), 5)

    def test_remaining_work(self):
        for goal, saved, rate in [(1500, 300, 200), (960, 120, 70)]:
            text = ('An artist needs ${} for supplies. She has ${} in savings. '
                    'She can save ${} each week. How many weeks does she need '
                    'to reach her goal?').format(goal, saved, rate)
            self.assertEqual(rate_answer(text), Fraction(goal-saved, rate))
        self.assertEqual(rate_answer(
            'A collector has 940 stamps. The average number of stamps she sells '
            'per month is 20. How many months will it take to reduce her '
            'stamp collection to 300?'), 32)

    def test_grouped_volume_and_flow(self):
        for groups, size, flow in [(6, 12, 3), (5, 9, 2)]:
            text = ('A worker has {} tanks of {} liters each. A pump supplies '
                    '{} liters per minute. How many minutes will it take '
                    'to fill the tanks?').format(groups, size, flow)
            self.assertEqual(rate_answer(text), Fraction(groups*size, flow))

    def test_equal_sharing_includes_host(self):
        self.assertEqual(rate_answer(
            'Rosa with her three friends ordered 5 pies. Each pie had 12 pieces. '
            'They ate the same number of pieces. How many pieces did each person eat?'), 15)
        self.assertEqual(rate_answer(
            'Ada and Ravi bought 10 pastries together. Each pastry cost $3. '
            'They split the costs evenly. How much did each person pay?'), 15)
        self.assertIsNone(rate_answer(
            'Ada and her friends bought 10 pastries together. Each pastry cost $3. '
            'They split the costs evenly. How much did each person pay?'))

    def test_prices_and_change(self):
        for count, tender, change in [(4, 50, 10), (7, 100, 16)]:
            text = ('A shopper buys {} bags of flour. He pays with a ${} bill and '
                    'gets ${} change. How much did each bag cost?').format(count, tender, change)
            self.assertEqual(rate_answer(text), Fraction(tender-change, count))
        self.assertIsNone(rate_answer(
            'A shopper buys 4 bags of flour. He pays with a $50 bill and gets '
            '$10 change. How much did each jar cost?'))

    def test_two_rate_operations(self):
        self.assertEqual(rate_answer(
            'A boat can travel 15 kilometers per hour on a lake. A river flows '
            'in the opposite direction at 3 kilometers per hour. The route is '
            '36 kilometers long. How many hours will the boat take?'), 3)
        self.assertEqual(rate_answer(
            'Two workers need to move 85 bricks. One worker can carry 6 bricks '
            'at a time, while another can carry 4 bricks at a time. '
            'How many trips together must they make?'), None)  # Unused headcount.
        self.assertEqual(rate_answer(
            'Workers need to move 85 bricks. Ada can carry 6 bricks at a time, '
            'while Lee can carry 4 bricks at a time. '
            'How many trips together must they make?'), 9)

    def test_schedule_and_unused_quantities(self):
        self.assertEqual(rate_answer(
            'A hiker walks 8 miles per day on weekdays only. '
            'How many miles does the hiker walk over 4 weeks?'), 160)
        for text in [
            'A hiker walks 8 miles per day but takes days off. '
            'How many miles does the hiker walk over 4 weeks?',
            'A worker earns $18 per hour. She worked 3 hours and paid $5 for lunch. '
            'How much did she earn?',
            'A van carries 8 boxes per trip. There are 24 boxes in the warehouse '
            'and 16 boxes outside. How many trips will the driver need?',
            'A cook has 3 pots and 2 pans. How many recipes should he learn?',
            'A driver travels 60 miles per hour. A town is 90 miles away. '
            'How many hours will the round trip take?',
        ]:
            self.assertIsNone(rate_answer(text), text)

    def test_plain_chat_abstains(self):
        self.assertIsNone(solve('I have 3 kids and 2 dogs'))

    def test_runtime_money_keeps_math(self):
        from bot.runtime import turn
        examples = [
            ('Marissa wants to save $840 over 8 months for a holiday. She has '
             '$120 left over from last year. How much money does Marissa need '
             'to save each month to reach her goal in 8 months?', 90),
            ('Eliana went to a furniture sale and spent $72. She bought a table '
             'for $42 and 3 chairs. Each chair cost the same amount. '
             'How much did one chair cost?', 10),
        ]
        for text, expected in examples:
            result = turn(text, {})
            self.assertEqual(result['module'], 'word_problem')
            self.assertTrue(result['reply'].endswith('Answer: '+str(expected)))


if __name__ == '__main__':
    unittest.main()
