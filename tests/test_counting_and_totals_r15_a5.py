"""Changed nouns and quantities, accounting failures, and runtime routing."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.counting_and_totals_r15_a5 import solve as counting


def value(text):
    problem = Problem.read(text)
    result = counting(problem) if problem else None
    return result[0] if result else None


class ThreeStepCountingTests(unittest.TestCase):
    def test_repeated_net_changes_vary_quantities_and_units(self):
        for initial, gain, loss, periods in ((8, 3, 1, 7), (21, 7, 2, 4)):
            text = ('Owen has {} plants. Every month, his parents buy him '
                    '{} more, but {} of them dies. How many plants will he '
                    'have in {} months?').format(initial, gain, loss, periods)
            self.assertEqual(value(text), initial + (gain-loss)*periods)

    def test_calendar_dates_are_not_inventory(self):
        text = ('The cooperative had 46 workshops in 2022. In 2023, it '
                'opened 8 new workshops, but closed the 3 that performed '
                'the worst. How many workshops did it have at the end of 2023?')
        self.assertEqual(value(text), 51)

    def test_grouped_areas(self):
        text = ('Rae is tending 2 plots that each measure 4 meters by 7 meters. '
                'Her partner is tending 3 plots that each measure 6 meters '
                'by 9 meters. How many square meters combined are in all '
                'their plots?')
        self.assertEqual(value(text), 218)

    def test_reverse_material_recipe(self):
        text = ('A tailor can make 7 flags out of two yards of silk. '
                'She needs 5 yards of silk to make a cape. How much silk '
                'does she need to make 2 capes and 14 flags?')
        self.assertEqual(value(text), 14)
        self.assertIsNone(value(text.replace('two yards of silk', 'two yards of cotton')))

    def test_remaining_material_uses_sizes_not_catalogue_counts(self):
        text = ('A cook has 98 ounces of juice. She has 7-ounce jars and '
                '4-ounce jars. If she fills six 7 ounce jars, how many '
                '4 ounce jars can she fill with the remaining juice?')
        self.assertEqual(value(text), 14)
        self.assertIsNone(value(text.replace('98 ounces', '99 ounces')))

    def test_mixed_time_budget(self):
        text = ('Ari spent 25 minutes packing, 10 minutes washing, a certain '
                'amount of time sweeping, and 30 minutes shopping. If he '
                'spent a total of two hours on these tasks, how long, in '
                'minutes, did he spend sweeping?')
        self.assertEqual(value(text), 55)

    def test_category_weights_keep_exact_fractions(self):
        text = ('A porter carries 3 drums and 7 cylinders. The drums weigh '
                '2.5 pounds each, and the cylinders weigh 1.25 pounds each. '
                'How many total pounds does the porter carry?')
        self.assertEqual(value(text), Fraction(65, 4))

    def test_ratio_partition_and_labelled_shares(self):
        text = ('The ratio of cedar beams to steel beams in a depot is 3:7. '
                'How many steel beams are in the depot if the total number '
                'of beams is 120?')
        self.assertEqual(value(text), 84)

    def test_unit_conversion_before_tiling(self):
        text = ('A mural will be 3 feet tall and 4 feet long. Each panel '
                'she uses is 6 inches square. How many panels will she need?')
        self.assertEqual(value(text), 48)

    def test_unknown_relations_and_unaccounted_quantities_abstain(self):
        cases = (
            'A tailor can make 7 flags out of two yards of silk. She needs '
            '5 yards of silk to make a cape and owns 13 scissors. How much '
            'silk does she need to make 2 capes and 14 flags?',
            'A company had 46 workshops in 3000 boxes. It opened 8 new '
            'workshops, but closed 3 workshops. How many workshops are left?',
            'A gardener has 20 plants. Every month his parents buy him '
            '3 more, but some of them die. How many plants will he have '
            'in 5 months?',
            'A household eats 4 bowls in the morning and 6 bowls in the '
            'evening. A bowl has 9 grams of fiber. How many grams of '
            'fiber do they eat in a week?',
            'A lawn measures 12 yards by 8 yards. A shed on it measures '
            '2 yards by 3 yards. How many square yards of sod are needed?',
        )
        for text in cases:
            with self.subTest(text=text):
                self.assertIsNone(value(text))

    def test_existing_group_rule_does_not_add_damaged_stock(self):
        text = ('A shop brought home 4 bags of badges. Each bag has 9 '
                'badges. The worker tore off 2 badges. During the event, '
                'only 11 badges were used. How many badges were unused?')
        self.assertTrue(solve(text).endswith('Answer: 23'))

    def test_existing_coins_compare_owners(self):
        text = ('Ada has 20 quarters in her jar. Her brother Rowan has '
                '52 quarters in his jar. How much more money does Rowan have?')
        self.assertTrue(solve(text).endswith('Answer: 8'))

    def test_comparative_categories_then_equal_distribution(self):
        text = ('There are 120 silver counters and there are 36 more gold '
                'counters than silver counters. The counters will be evenly '
                'divided among 12 teams. How many counters will one team receive?')
        self.assertEqual(value(text), 23)

    def test_shared_event_and_recipient_dimensions(self):
        text = ('A guide takes his 4 children exploring. They are out for '
                '3 hours. Each hour they visited 6 stations. Each station '
                'gives 2 tokens per kid. How many tokens do his children '
                'get in total?')
        self.assertEqual(value(text), 144)

    def test_named_task_frequencies(self):
        text = ('A workshop needs 4 sheets to build a lantern and 7 sheets '
                'to build a tower. How many sheets does it need to build '
                'a lantern 6 times and a tower 3 times?')
        self.assertEqual(value(text), 45)

    def test_repeated_paths_count_every_traversal(self):
        text = ('A worker climbs a tall stairway, which has 9 steps, 4 times '
                'today. She also climbs a short stairway, which has 5 steps, '
                '3 times today. In total, how many times has she climbed '
                'a step today?')
        self.assertEqual(value(text), 51)

    def test_nonquantitative_chat_is_untouched(self):
        self.assertIsNone(solve('I have 3 kids and 2 dogs'))
        self.assertIsNone(solve('I had 20 badges and gave away 3 of them today.'))


if __name__ == '__main__':
    unittest.main()
