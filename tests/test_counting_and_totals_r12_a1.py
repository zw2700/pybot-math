"""Arithmetic variations, relation scope, and abstention for short counts."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.counting_and_totals_r12_a1 import solve as counting


def value(text):
    reply = solve(text)
    return None if reply is None else Fraction(reply.rsplit('Answer: ', 1)[1])


class ShortCountingTests(unittest.TestCase):
    def test_stock_nouns_can_be_omitted_in_later_dated_events(self):
        for noun in ('badges','postcards','ribbons'):
            text = ('Nora has 47 {} to sell. She sold 12 last month and 9 this '
                    'month. How many more {} does Nora need to sell?').format(noun,noun)
            self.assertEqual(value(text),26)

    def test_passive_departures_and_returns(self):
        for noun, initial, removed, returned in (
                ('tools', 84, 19, 7), ('folders', 93, 22, 14)):
            text = ('There are {} {} in storage. On Monday, {} {} are taken out. '
                    'On Tuesday, {} {} are brought back. How many {} are there now?').format(
                        initial,noun,removed,noun,returned,noun,noun)
            self.assertEqual(value(text), initial-removed+returned)

    def test_parts_scale_with_the_known_ingredient(self):
        for amount in (9, 15):
            text = ('A mixture has 3 parts red paint, 2 parts green paint and '
                    '4 parts blue paint. It contains {} ounces of red paint. '
                    'How many ounces is the mixture?').format(amount)
            self.assertEqual(value(text), amount*3)

    def test_ratios_keep_category_labels(self):
        for base in (21, 35):
            text = ('A collector bought striped beads and plain beads in the ratio '
                    'of 7:4. She had {} striped beads on Monday. '
                    'How many plain beads did she have?').format(base)
            self.assertEqual(value(text), Fraction(base*4,7))

    def test_fixed_work_uses_inverse_proportion(self):
        for workers, minutes, new_workers in ((6, 24, 9), (8, 15, 5)):
            text = ('Working together, {} helpers can clean the hall in {} minutes. '
                    'In how many minutes will {} helpers working together be able '
                    'to clean the hall?').format(workers,minutes,new_workers)
            self.assertEqual(value(text), Fraction(workers*minutes,new_workers))

    def test_stock_changes_before_per_survivor_contents(self):
        for noun, content in (('lanterns','beads'), ('baskets','tokens')):
            text = ('Mira made 13 {}. Then she gives away 4 {}. Mira wants to put '
                    '{} on the remaining {}. If she puts 7 {} on each {}, '
                    'how many {} will she use in total?').format(
                        noun,noun,content,noun,content,noun[:-1],content)
            self.assertEqual(value(text), 63)

    def test_common_noun_owners_are_distinct_from_the_counted_unit(self):
        for initial, fewer, more in ((21, 4, 9), (34, 7, 5)):
            text = ('A crate has {} compartments. A chest has {} fewer compartments '
                    'than a crate. A cabinet has {} more compartments than a chest. '
                    'How many compartments does a cabinet have?').format(initial,fewer,more)
            self.assertEqual(value(text), initial-fewer+more)

    def test_reverse_arrivals_and_departures(self):
        for final, entered, departed in ((32, 8, 3), (65, 11, 6)):
            text = ('There were some visitors in a room. Then {} more visitors came in '
                    'and {} visitors left. There are now {} visitors in the room. '
                    'How many visitors were in the room at the start?').format(
                        entered,departed,final)
            self.assertEqual(value(text), final-entered+departed)

    def test_separate_daily_rates_and_weekday_schedule(self):
        text = ('A courier travels 12 miles per hour for 2 hours and 18 miles per hour '
                'for 3 hours every day from Tuesday to Friday. '
                'How many miles does the courier travel in a week?')
        self.assertEqual(value(text), (12*2+18*3)*4)

    def test_each_member_each_day(self):
        for count, rate in ((3, 4), (7, 2)):
            text = ('A caretaker provides {} pounds of supplies per worker per day. '
                    'The caretaker has {} workers. How many pounds of supplies '
                    'are provided per week?').format(rate,count)
            self.assertEqual(value(text), count*rate*7)

    def test_capacity_subtracts_current_users(self):
        text = ('A theater has 9 benches with a capacity of 6 people each. '
                'At noon, 31 people were sitting on the benches. '
                "What's the number of available spaces on the benches?")
        self.assertEqual(value(text), 23)

    def test_fraction_of_absentees_is_complemented(self):
        for size in (35, 70):
            text = ('There are {} members in a club. Two-fifths of them were absent '
                    'last Friday. How many members were present last Friday?').format(size)
            self.assertEqual(value(text), size*Fraction(3,5))

    def test_type_enumeration_is_not_a_counted_item(self):
        text = ('A maker manufactures two types of bags, one with 4 clasps and '
                'the other with 7 clasps. A retailer ordered 30 of each type of bag. '
                'How many clasps will the maker use in total?')
        self.assertEqual(value(text), 330)

    def test_ratio_part_extremes(self):
        for label, known, expected in (('shortest', 14, 77), ('longest', 30, 66)):
            text = ('A cord is cut into three smaller pieces in the ratio of 5:4:2. '
                    'If the {} piece is {} cm, how long was the entire cord '
                    'before it was cut?').format(label,known)
            self.assertEqual(value(text), expected)

    def test_extra_quantities_and_unresolved_queries_are_declined(self):
        texts = [
            'There are 80 folders in storage. Then 12 folders are taken out and '
            '7 folders are brought back. There are 4 boxes. How many folders are there now?',
            'A mixture has 3 parts red paint and 2 parts blue paint. It contains '
            '9 ounces of green paint. How many ounces is the mixture?',
            'Five wagons carry 14 tokens each, 20 of which are shiny. '
            'How many tokens do all the wagons carry in total?',
            'A club has 80 members. Two-fifths of them were absent. '
            'How many members will attend next month?',
        ]
        for text in texts:
            with self.subTest(text=text):
                self.assertIsNone(counting(Problem.read(text)))

    def test_personal_statements_do_not_pass_the_math_gate(self):
        for text in ('I have 3 kids and 2 dogs.', 'We bought 8 books and 4 folders.'):
            self.assertIsNone(solve(text))


if __name__ == '__main__':
    unittest.main()
