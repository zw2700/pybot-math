"""Multi-stage comparison graphs, time scopes, composition and abstention."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.comparisons_r04_a3 import solve as compare


def answer(text):
    reply = solve(text)
    return None if reply is None else Fraction(reply.rsplit('Answer: ', 1)[1])


class ThreeStepComparisonTests(unittest.TestCase):
    def test_four_owner_chain_and_inverse(self):
        for base, delta in [(9, 4), (17, 6), (23, 11)]:
            relations = ('Adele is {} years older than Bianca. Bianca is twice as old as Clara. '
                         'Clara is 3 years younger than Daria. ').format(delta)
            self.assertEqual(answer(relations + 'Daria is {} years old. How old is Adele?'.format(base)), 2*(base-3)+delta)
            self.assertEqual(answer(relations + 'Adele is {} years old. How old is Daria?'.format(2*(base-3)+delta)), base)

    def test_independently_anchored_pairs(self):
        text = ('Adele is 4 years older than Bianca. Clara is 3 years younger than Daria. '
                'Bianca is 12 years old and Daria is 19 years old. '
                'How old are all four family members in total?')
        self.assertEqual(answer(text), 63)

    def test_family_aliases_and_average(self):
        for base in (7, 11, 15):
            text = ("Adele's father is twice as old as Adele, who is twice as old as Bianca. "
                    "Bianca is {} years old. What's the average age of the three?").format(base)
            self.assertEqual(compare(Problem.read(text))[0], Fraction(7*base, 3))
            self.assertEqual(answer("Adele is {} years old. Her grandmother is 5 times older than her. "
                                    "Adele's grandfather is 4 years older than her grandmother. "
                                    "What is the age difference between Adele and her grandfather?".format(base)), 4*base+4)

    def test_disconnected_category_pairs_and_noun_elision(self):
        self.assertEqual(answer('A box contains 7 striped beads, 9 spotted beads, '
                                'three times as many plain beads as striped ones and '
                                'twice as many shiny ones as spotted ones. How many beads are in the box?'), 55)

    def test_multiple_of_a_combined_amount(self):
        self.assertEqual(answer('Adele has 7 beads and Bianca has 4 beads. Clara has twice as many '
                                'beads as Adele and Bianca combined. How many beads do they have in total?'), 33)
        self.assertEqual(answer('Adele has three times as many beads as Bianca. Together they '
                                'have 8 more beads than Clara. Bianca has 9 beads. '
                                'How many beads do the three have altogether?'), 64)

    def test_calendar_events(self):
        self.assertEqual(answer('Adele earned $90 in April. She earned three times this amount in May. '
                                'In June she earned twice the money she earned in May. '
                                'How much did she earn over these three months?'), 900)
        self.assertEqual(answer('Adele read 9 books in April, twice as many in May and '
                                '4 fewer in June than in May. How many books did she read during the spring?'), 41)

    def test_prices_for_selected_days(self):
        self.assertEqual(answer('Tickets cost $7 each on Tuesday, twice as much on Thursday, '
                                'and four times as much as Tuesday on Sunday. If Adele goes '
                                'on Thursday and Sunday, how much does she spend?'), 42)

    def test_date_scopes_and_month_conversion(self):
        for base in (8, 13, 21):
            self.assertEqual(answer('Last year Adele was three times the age of Bianca. '
                                    'Bianca is twice as old as Clara, who is {} years old now. '
                                    'How old is Adele now?'.format(base)), 3*(2*base-1)+1)
            self.assertEqual(answer('Adele is 9 years younger than her father. In 4 years, '
                                    'the sum of their ages will be 49. How old is her father now?'), 25)
        self.assertEqual(answer('Adele is twice as old as Bianca. In 15 months she will be '
                                '12 years old. How many months old is Bianca?'), Fraction(129, 2))
        self.assertEqual(answer('Six years ago, Adele was twice as old as Bianca is now. '
                                'Bianca is 9 years old. How old is Adele now?'), 24)
        self.assertEqual(answer('In 4 years Adele will be twice as old as Bianca is now. '
                                'Bianca is 9 years old. How much older is Adele than Bianca now?'), 5)

    def test_age_events(self):
        self.assertEqual(answer('Adele is 7 years old and her father is 37 years old. '
                                'How old will Adele be when her father is twice as old as her?'), 30)
        self.assertEqual(answer('Adele is 20 years old and her little sister is 6 years old. '
                                'In how many years would she be twice her sister\'s age?'), 8)
        self.assertEqual(answer('Adele is 14 years old. Her sister Bianca is half as old as Adele. '
                                'How old will Bianca be when Adele is 23 years old?'), 16)
        self.assertEqual(answer('Adele is 8 years old and her father is 31 years old. '
                                'How old will Adele be when her father is five times as old as Adele is now?'), 17)

    def test_compared_allocations_and_remainders(self):
        self.assertEqual(answer('Adele needs 13 beads. Bianca needs twice as many beads as Adele. '
                                'They bought 60 beads. How many beads will remain after both have used what they need?'), 21)
        self.assertEqual(answer('A box contains 65 beads. There are three times as many red beads as '
                                'blue beads and the rest are yellow. There are 12 blue beads. '
                                'How many yellow beads are there?'), 17)

    def test_daily_span_and_unit_conversion(self):
        self.assertEqual(answer('From Tuesday to Friday, Adele practices for 24 minutes. On Saturday '
                                'she practices twice as much as on a weekday. '
                                'How many hours does she practice each week?'), Fraction(12, 5))

    def test_compared_groups_and_priced_outputs(self):
        self.assertEqual(answer('4 machines use 9 bolts each. 7 engines use three times as much '
                                'as the machines. How many total bolts are used?'), 225)
        self.assertEqual(answer('Adele has an average of 40 viewers per day while Bianca has '
                                'three times the number of viewers Adele has. They earn $0.25 per view. '
                                'How much does Bianca earn per week?'), 210)

    def test_assembly_cost(self):
        self.assertEqual(answer('The frame costs $18, the panel costs $9 more than the frame, '
                                'and the backing costs $4 less than the frame. '
                                'How much does it cost to assemble the frame?'), 59)

    def test_declines_ambiguous_or_unexplained_quantities(self):
        cases = [
            'Adele has twice as many beads as Bianca. Bianca has 8 beads. A box costs $25. How many beads does Adele have?',
            'Adele is twice as old as Bianca. Adele is 17 and Bianca is 9. How old is Adele?',
            "Adele is twice as old as Bianca. Bianca is 8 years old. How old is Adele's brother?",
            'There are twice as many red beads as blue beads. There are 8 blue beads. How many green beads are there?',
            'A bag costs 70 dollars. There are twice as many red beads as blue beads. There are 8 blue beads and the rest are green. How many green beads are there?',
            'Adele has 70 beads. Bianca needs 8 books and Clara needs twice as many books as Bianca. How many beads remain?',
            'Adele has twice as many beads as Bianca. Bianca has 8 beads. How many beads does Adele have after buying 5 more?',
            'Adele is 8 inches taller than Bianca. Bianca is twice as tall as Clara. Clara is 2 feet tall. How tall is Adele in inches?',
        ]
        for text in cases:
            with self.subTest(text=text):
                problem = Problem.read(text)
                self.assertIsNotNone(problem)
                self.assertIsNone(compare(problem))
        self.assertIsNone(solve('I have 3 children and 2 cats.'))


if __name__ == '__main__':
    unittest.main()
