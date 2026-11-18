"""Independent variations for percentage bases and complement scope."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.percentages_r13_a3 import solve as explicit


def answer(text):
    reply = solve(text)
    return None if reply is None else Fraction(reply.rsplit('Answer: ', 1)[1])


class PercentageBaseTests(unittest.TestCase):
    def test_remainder_before_share_varies(self):
        for total, other, percent in ((800, 250, 20), (1200, 400, 35)):
            self.assertEqual(answer(
                'A town has {} residents. {} are men and the rest are women. '
                '{} percent of the women wear hats. How many women wear hats?'.format(
                    total, other, percent)), (total-other)*Fraction(percent, 100))

    def test_parallel_is_not_nested(self):
        self.assertEqual(answer(
            'A mechanic has 150 devices. 20% of them are broken, and 30% of them '
            'need new parts. The rest can be repaired today. '
            'How many devices can be repaired today?'), 75)
        self.assertEqual(answer(
            'A mechanic has 150 devices. 20% of them are broken. '
            '30% of the broken devices need new parts. '
            'How many broken devices need new parts?'), 9)

    def test_negation_is_local_to_nested_base(self):
        self.assertEqual(answer(
            'An athlete attempts 120 passes in a season. 40% of the time he does '
            'not throw the ball. Half of the times he does not throw he is tackled. '
            'How many times is the athlete tackled?'), 24)

    def test_coin_noun_and_named_fraction(self):
        self.assertEqual(answer(
            'A collector has 60 quarters. 1/3 of the quarters are special quarters, '
            'and 40% of the special quarters are silver. '
            'How many silver quarters does the collector have?'), 8)

    def test_money_items_are_combined_before_tip(self):
        self.assertEqual(answer(
            'Lena and Ava went to dinner. They shared a dish that cost $8. '
            'Each of their entrees was $15 and they shared a dessert that was $12. '
            'If they left a 10% tip, what was the entire price of the meal?'), 55)

    def test_reading_remainder(self):
        self.assertEqual(answer(
            'A reader has a 250-page book. She finished reading 36% of the book. '
            'How many pages does she need to read to finish the book?'), 160)

    def test_descriptor_count_does_not_multiply_population(self):
        self.assertEqual(answer(
            'In a field of 600 flowers, 30% have six petals and one quarter of '
            'these are yellow. How many flowers are both yellow and six-petaled?'),45)

    def test_partition_uses_descriptors_not_shared_nouns(self):
        for total in (100, 240):
            self.assertEqual(answer(
                'A store has {} tokens. 30% are red tokens and 20% are blue tokens. '
                'The rest are green tokens. How many red tokens are there?'.format(total)),
                total*Fraction(30,100))
            self.assertEqual(answer(
                'A store has {} tokens. 30% are red tokens and 20% are blue tokens. '
                'The rest are green tokens. How many green tokens are there?'.format(total)),
                total*Fraction(50,100))

    def test_postposed_share_preserves_subject(self):
        self.assertEqual(answer(
            'There are 120 passengers on a boat. Children make up 35% of the '
            'boat riders. How many adults are on the boat?'),78)

    def test_price_comparison_follows_requested_owner(self):
        self.assertEqual(answer(
            'Lena buys a bicycle for $240, which is 20% less than what '
            'Mira bought the same bicycle for. How much did Mira pay for her bicycle?'),300)

    def test_known_discount_amount_is_not_the_original_price(self):
        self.assertEqual(answer(
            'A shopper received a 30% discount at a store. If the discount '
            'she received is $45, how much did she pay in total?'),105)

    def test_percent_change_uses_original_as_denominator(self):
        self.assertEqual(answer(
            'An appliance was bought for $450. It was later sold for $360. '
            'What percentage of the original price did the owner lose?'),20)

    def test_simple_and_successive_percentage_bases(self):
        self.assertEqual(answer(
            'A village had a population of 800 people. The population increased '
            'by 20% then 25% of the population moved away. '
            'What is the current population?'),720)
        self.assertEqual(answer(
            'A worker receives $12000 a year. He loses 15 percent to taxes, '
            '5 percent to insurance, and $300 to union dues. '
            'How much money does the worker take home?'),9300)

    def test_repeated_annual_retention_has_percentage_units(self):
        self.assertEqual(answer(
            'A liquid is stored in a bottle for 3 years. Each year 10% of '
            'the liquid evaporates. What percent of the liquid is left after 3 years?'),
            Fraction(729,10))

    def test_abstain_unrelated_or_unselected(self):
        for text in (
                'A club has 50 members and 20% are artists. Another club has 30 '
                'chairs. How many artists are there?',
                'A reader finished 25% of a 300-page book and bought 4 pens. '
                'How many pages does she need to finish the book?',
                'I have 3 kids and 2 dogs.',
                'A deposit of $800 was made 3 years ago. It earns 10% interest '
                'annually. What is the current value of the deposit?'):
            p=Problem.read(text)
            self.assertIsNone(explicit(p) if p else None)


if __name__ == '__main__':
    unittest.main()
