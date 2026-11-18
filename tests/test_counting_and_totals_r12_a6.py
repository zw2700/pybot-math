"""Changed quantities, nouns and scopes exercise the new counting relations."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.counting_and_totals_r12_a6 import solve as counting


def result(text):
    parsed = Problem.read(text)
    value = counting(parsed) if parsed else None
    return value[0] if value else None


class ThreeStepCountingTests(unittest.TestCase):
    def test_grouped_stock_with_two_exclusions(self):
        for noun,groups,size,bad,reserved in (
                ('beads',7,12,8,9), ('tiles',4,23,6,11)):
            text = ('There are {} bags with {} {} each. A total of {} {} '
                    'are broken. {} {} will be kept for later and the rest '
                    'will be sold. How many {} will be sold?').format(
                        groups,size,noun,bad,noun,reserved,noun,noun)
            self.assertEqual(result(text),groups*size-bad-reserved)

    def test_grouped_arrivals_then_removal(self):
        for unit in ('books','ribbons','shells'):
            text = ('A collector has 80 {}. Six people donate three {} each. '
                    'Then 17 {} are borrowed. How many {} are remaining?').format(
                        unit,unit,unit,unit)
            self.assertEqual(result(text),81)

    def test_group_differences_use_each_group_frequency(self):
        text = ('Eight workers brought 13 tokens each. Seven visitors brought '
                '11 tokens each. How many fewer tokens did the visitors '
                'bring than the workers?')
        self.assertEqual(result(text),27)

    def test_elided_inventory_is_distinct_from_group_count(self):
        text = ('A drawing shows creatures. A parent had 2 horns and the '
                'other had 5. They had 4 children, each with 3 horns. '
                'How many horns did the whole family have?')
        self.assertEqual(result(text),19)

    def test_daily_activity_window_is_not_a_full_day(self):
        for speed,days in ((7,3),(12,4)):
            text = ('A walker travels {} meters each minute. Every day, '
                    'she walks for an hour. How many meters will she walk '
                    'in {} days?').format(speed,days)
            self.assertEqual(result(text),speed*60*days)
            self.assertTrue(solve(text).endswith('Answer: '+str(speed*60*days)))

    def test_named_comparison_chain_varies_names_and_numbers(self):
        for a,b,c in (('Mira','Oren','Tavi'),('Lena','Pavel','Iris')):
            text = ('{} has 19 tokens. {} has 8 more tokens than {}. '
                    '{} has 6 fewer tokens than {}. How many tokens '
                    'do they have altogether?').format(a,b,a,c,b)
            self.assertEqual(result(text),67)

    def test_overlap_is_counted_once(self):
        text = ('Out of her 40 clients, 12 need hot meals, 9 need soft meals, '
                'and 4 people need meals that are both hot and soft. '
                'How many meals are neither soft nor hot?')
        self.assertEqual(result(text),23)

    def test_incoming_gift_is_not_an_outgoing_transfer(self):
        text = ('A collector has 20 tokens. A friend gave her 7 tokens. '
                'She lost 4 tokens. How many tokens are remaining?')
        self.assertEqual(result(text),23)

    def test_required_material_is_consumed_from_available_stock(self):
        text = ('A crafter has 5 parcels. Each parcel requires 2.5 meters '
                'of cord. She has 20 meters of cord. How many meters '
                'of cord will be left?')
        self.assertEqual(result(text),Fraction(15,2))

    def test_explicit_conversion_uses_available_capacity(self):
        text = ('An archive has 18 XB of storage. It is already using 3 XB. '
                'If a record takes up about 25YB of storage, how many records '
                'can it store? (There are 200 YB in a XB).')
        self.assertEqual(result(text),120)

    def test_end_to_end_count_uses_diameter_and_common_length_units(self):
        text = ('A circle has a radius of 9 feet. How many 4-inch rods can '
                'be placed end-to-end across the diameter of the circle?')
        self.assertEqual(result(text),54)
        self.assertTrue(solve(text).endswith('Answer: 54'))

    def test_declines_unresolved_owner_category_and_extra_quantities(self):
        cases = [
            'A fruit has 30 slices, and each slice has 12 dark seeds and '
            '9 pale seeds. What is the total number of seeds in the fruit?',
            'Rina has 9 more tokens than Oren. Oren has 20% more tokens '
            'than Tavi. Tavi has 15 tokens. How many tokens do they '
            'have in total?',
            'A gardener has 90 flowers. Two-thirds of the flowers are red, '
            'one-fourth of the remaining flowers are blue, and the rest '
            'are yellow. How many flowers are either red or yellow?',
            'Eight workers brought 13 tokens each. Seven visitors brought '
            '11 tokens each. How many tokens did the workers bring in total?',
            'Mira has 4 cartons with 8 beads each. She gave 3 beads to Oren. '
            'How many beads does Oren have left?',
            'A crafter has 12 red beads and 9 blue beads. She gave 4 blue '
            'beads away. How many red beads are left?',
            'A seller has 4 boxes with 9 tiles each. She has 2 bicycles. '
            'How many tiles does she have altogether?',
            'A worker makes 7 tiles every other day. '
            'How many tiles does she make in 12 days?',
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertIsNone(result(text))
        self.assertIsNone(solve('I have 3 kids and 2 dogs'))

    def test_runtime_routes_and_ends_with_exact_answer(self):
        from bot.runtime import turn
        response = turn('A worker trains for 2 hours 3 times a week. She also '
                        'trains 4 times a week for 1.5 hours. How many hours '
                        'a week does she train?',{})
        self.assertEqual(response['module'],'word_problem')
        self.assertTrue(response['reply'].endswith('Answer: 12'))


if __name__ == '__main__':
    unittest.main()
