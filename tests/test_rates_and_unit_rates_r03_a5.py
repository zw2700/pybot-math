"""Unit conversions, linked rates, and conservative rate interpretation."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.numbers import read_numbers
from bot.math.problem import Problem
from bot.math.skills.rates_and_unit_rates_r03_a5 import solve as rate_solve


def rate_answer(text):
    problem = Problem.read(text)
    result = rate_solve(problem) if problem else None
    return result[0] if result else None


class RateCompositionTests(unittest.TestCase):
    def test_leading_decimal_preserves_value_kind_and_offsets(self):
        text = 'A sample weighs .75 grams and costs $.06.'
        ns = read_numbers(text)
        self.assertEqual([n.value for n in ns], [Fraction(3,4), Fraction(3,50)])
        self.assertEqual([n.kind for n in ns], ['number','money'])
        self.assertTrue(all(text[n.start:n.end] == n.raw for n in ns))

    def test_observed_rate_has_a_fixed_direction(self):
        for distance, elapsed, future in [(84, 7, 4), (125, 5, 3)]:
            text = ('A vehicle traveled {} miles in {} hours. At this rate, '
                    'how many miles will it travel in the next {} hours?').format(distance, elapsed, future)
            self.assertEqual(rate_answer(text), Fraction(distance*future,elapsed))

    def test_speed_uses_the_requested_time_unit(self):
        stem = 'A vehicle traveled 3 kilometers in 5 minutes. '
        self.assertEqual(rate_answer(stem+'What is its speed in kilometers per hour?'),36)
        self.assertEqual(rate_answer(stem+'What is its speed in meters per minute?'),600)

    def test_two_rates_compose_through_their_units(self):
        for output, hours, total in [(12, 6, 360), (7, 5, 210)]:
            text = ('A machine produces {} tiles per hour. The order requires {} tiles. '
                    'The machine works {} hours every day. How many days will the order take?').format(output,total,hours)
            self.assertEqual(rate_answer(text),Fraction(total,output*hours))

    def test_equal_sharing_of_a_product(self):
        self.assertEqual(rate_answer(
            'Nine coworkers ordered four trays. Each tray contains eighteen sandwiches. '
            'They share the same number. How many sandwiches does each person get?'),8)

    def test_periodic_quantity_and_unit_conversion(self):
        self.assertEqual(rate_answer(
            'A worker needs a total of 2 liters of fluid. She drinks 250 milliliters '
            'every 3 hours. How many hours will reaching her goal take?'),24)

    def test_operating_schedule_and_energy_conversion(self):
        self.assertEqual(rate_answer(
            'An appliance uses 120 watts for 6 hours a day. How much kWh does it '
            'use per month (30 days)?'),Fraction(108,5))
        self.assertEqual(rate_answer(
            'A worker needs 3 hours extra aside from her normal schedule each day. '
            'Each day her normal schedule is 5 hours. The project requires 240 hours. '
            'Calculate the number of days it will take her to finish.'),30)

    def test_parallel_rates_and_a_leak(self):
        self.assertEqual(rate_answer(
            'A pump supplies 7 liters per minute. Another pump supplies 5 liters per minute. '
            'Together they must supply 84 liters. How many minutes will they take?'),7)
        self.assertEqual(rate_answer(
            'A tank holds 84 liters. A pipe supplies 8 liters per minute. A hole leaks '
            '2 liters per minute. How many minutes will it take to fill the tank?'),14)

    def test_uncertain_relations_abstain(self):
        for text in [
            'A worker earns $9 per hour. Another worker earns $12 per hour. '
            'Someone works 5 hours. How many hours should the other worker work?',
            'A truck travels 40 miles per hour. The destination is 80 miles away. '
            'How many hours will the round trip take?',
            'An artist owns 6 jars and 4 brushes. How many pictures should she paint?',
            'A courier earns $20 per hour. She works 4 hours and pays $7 for lunch. '
            'How much does she earn?',
            'A trip costs $90. Her family gave her $120 toward the trip. She earns '
            '$3 for every ticket she sells. How many tickets does she need to sell?',
        ]:
            self.assertIsNone(rate_answer(text),text)
        self.assertIsNone(solve('I have 3 kids and 2 dogs'))

    def test_runtime_preserves_converted_answer(self):
        from bot.runtime import turn
        result = turn('A clerk needs 6 minutes to process each form. There are 70 forms. '
                      'How many hours will the clerk need to process all the forms?',{})
        self.assertEqual(result['module'],'word_problem')
        self.assertTrue(result['reply'].endswith('Answer: 7'),result['reply'])


if __name__ == '__main__':
    unittest.main()
