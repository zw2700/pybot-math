"""Counting relations with varied quantities, units, owners and unknowns."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.counting_and_totals_r08_a2 import solve as counting


def answer(text):
    reply = solve(text)
    return None if reply is None else Fraction(reply.rsplit('Answer: ', 1)[1])


class CountingTotalsTests(unittest.TestCase):
    def test_nested_capacity_relations(self):
        for wagons, bins, liters in [(2, 4, 9), (5, 3, 11)]:
            text = ('A supplier has {} wagons. Each wagon uses {} bins with a '
                    'capacity of {} liters. How many liters can the supplier carry?').format(wagons, bins, liters)
            self.assertEqual(answer(text), wagons*bins*liters)

    def test_fronted_recipe_scales_yield(self):
        for yield_size, material, target in [(4, 28, 8), (5, 35, 12)]:
            text = ('To make {} liters of dye Mara needs {} grams of pigment. '
                    'How many grams of pigment does Mara need to make {} liters of dye?').format(yield_size, material, target)
            self.assertEqual(answer(text), Fraction(material*target, yield_size))

    def test_container_removals_precede_content_conversion(self):
        for cards, folders, lost in [(13, 8, 2), (9, 12, 4)]:
            text = ('There are {} cards in a folder. If you bought {} folders '
                    'but lose {} of the folders, how many cards would you have?').format(cards, folders, lost)
            self.assertEqual(answer(text), cards*(folders-lost))

    def test_scheduled_singular_items(self):
        self.assertEqual(answer(
            'Nina has 4 children and they each get a snack bag for lunch, '
            '4 days a week. The school term is 12 weeks long. '
            'How many snack bags will she need for the entire term for all her children?'), 192)

    def test_refill_subtracts_remaining_stock(self):
        for start, first, second, capacity in [(15, 4, 3, 20), (21, 8, 5, 30)]:
            text = ('A driver had {} gallons of fuel. She uses {} gallons on a trip '
                    'and uses {} gallons on another trip. The tank can hold up to '
                    '{} gallons. How many gallons will she need to refill the tank?').format(start, first, second, capacity)
            self.assertEqual(answer(text), capacity-start+first+second)

    def test_qualifying_categories_select_ratio_side(self):
        stem = ('A shop has a certain number of cotton scarves and four times more '
                'wool scarves than cotton scarves. The shop has 45 scarves total. ')
        self.assertEqual(answer(stem+'How many cotton scarves does the shop have?'), 9)
        self.assertEqual(answer(stem+'How many wool scarves does the shop have?'), 36)

    def test_mixed_time_units_in_comparative_total(self):
        self.assertEqual(answer(
            'Tara spent 5 more months than Omar preparing a report. Omar spent '
            '2 years preparing his report. How many months in total did Tara '
            'and Omar need to prepare their reports?'), 53)

    def test_daily_schedule_continues(self):
        self.assertEqual(answer(
            'A musician practiced for 3 hours every day for a month (28 days). '
            'She continues to practice for the next 9 days. '
            'How many hours will she practice in total?'), 111)

    def test_spent_stock_is_not_initial_plus_remaining(self):
        self.assertEqual(answer(
            'Omar has 9 tokens. A friend will give him 3 ribbons per token. '
            'If Omar leaves with 4 tokens, how many ribbons did he get?'), 15)

    def test_mass_capacity_rounds_down_to_whole_items(self):
        self.assertEqual(answer(
            'A crate can hold 29 pounds of blocks. Each block weighs 5 ounces. '
            'How many blocks can the crate hold?'), 92)

    def test_one_exception_consumes_all_other_groups(self):
        self.assertEqual(answer(
            'There were 9 workers at a workshop. They made 500 tiles in total, '
            'and 8 of them made 50 tiles each. Calculate the number of tiles '
            'the last worker made.'), 100)

    def test_equal_group_leftover_rounds_package_count_up(self):
        self.assertEqual(answer(
            'There are 17 students in a class. Each student needs 2 yards of cord. '
            'Each packet of cord contains 20 yards. If the teacher buys the least '
            'amount necessary, how much cord is left over?'), 6)

    def test_constant_speed_ignores_explicit_break(self):
        self.assertEqual(answer(
            'A driver travels 45 miles per hour. She drives for 2 hours, takes a '
            '20-minute break, and then drives for another 3 hours. '
            'How many miles will she travel?'), 225)

    def test_task_remainder(self):
        self.assertEqual(answer(
            'A pupil finished his homework in 40 minutes. He spent 11 minutes '
            'on arithmetic and 17 minutes on spelling. He spent the rest reading. '
            'How many minutes did he spend reading?'), 12)

    def test_abstains_on_unresolved_units_and_owners(self):
        examples = [
            'A crafter has 14 red beads and 9 blue beads. She gave 4 blue beads '
            'away. How many red beads are left?',
            'A gardener has 14 pots. She loses 3 pots. She puts 2 labels on '
            'each pot. How many labels are left?',
            'Mara had 28 shells. She gave 7 shells to Leo and lost 3 shells. '
            'How many shells does Leo have left?',
            'A supplier has 3 wagons. Each wagon uses 4 bins with a capacity '
            'of 9 liters. The supplier has 2 bicycles. How many liters can the supplier carry?',
            'A driver travels 45 miles per hour. She drives for 2 hours and '
            'then drives for another 3 hours. How many gallons does she use?',
            'Omar collected 4 ribbons. Inez collected 6 fewer ribbons. '
            'How many ribbons did they donate?',
            'Omar collected 14 ribbons. He collected 6 fewer ribbons. '
            'How many ribbons did they donate?',
            'A dog got 14 bones at the beginning of the month. After 3 months, '
            'he has 4 bones available and has buried the rest. How many bones '
            'has he buried?',
        ]
        for text in examples:
            with self.subTest(text=text):
                self.assertIsNone(counting(Problem.read(text)))
        self.assertIsNone(solve('I have 3 kids and 2 dogs'))

    def test_runtime_routes_and_ends_with_the_answer(self):
        from bot.runtime import turn
        result = turn(
            'A supplier has 2 wagons. Each wagon uses 4 bins with a capacity '
            'of 9 liters. How many liters can the supplier carry?', {})
        self.assertEqual(result['module'], 'word_problem')
        self.assertTrue(result['reply'].endswith('72'))


if __name__ == '__main__':
    unittest.main()
