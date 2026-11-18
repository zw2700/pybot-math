"""Fraction readers must preserve scope, exactness, units and abstention."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.fractions_of_a_quantity_r11_a4 import solve as skill


def answer(text):
    result = solve(text)
    return None if result is None else Fraction(result.rsplit('Answer: ', 1)[1])


class FractionQuantityTests(unittest.TestCase):
    def test_initial_stock_is_recovered_after_an_addition(self):
        for added, final, share in ((9, 21, '1/3'), (5, 18, '2/5')):
            text = ('Mina bought {} new tokens to add to her collection. '
                    'She then lost {} of her collection. There are {} tokens left. '
                    'How many tokens did Mina start with?').format(added, share, final)
            self.assertEqual(answer(text), Fraction(final)/(1-Fraction(share))-added)

    def test_inverse_sequential_shares(self):
        self.assertEqual(answer(
            'Mina used 2/5 of her paint. She then used 1/3 of the remaining paint. '
            'She has 14 liters left. How much paint did she have to start?'), 35)

    def test_combined_age_is_a_sum_constraint(self):
        for total, share in ((84,'1/5'),(105,'2/3')):
            text = ('Mina and Oren have a combined age of {}. '
                    'Mina is {} of Oren\'s age. How old is Mina?').format(total,share)
            self.assertEqual(answer(text),total*Fraction(share)/(1+Fraction(share)))

    def test_affine_graph_with_initials_and_total(self):
        self.assertEqual(answer(
            'RK has 7 more than twice as many tokens as LM. '
            'LM has 1/3 as many tokens as NP. '
            'The three friends have 127 tokens all together. How many tokens does NP have?'),60)

    def test_exact_recipe_scaling(self):
        for total in (9,18,27):
            self.assertEqual(answer(
                'A recipe uses 1/3 of a cup of syrup and 7/6 of a cup of water to make one drink. '
                'A jug has {} total cups of this drink. How many cups of syrup are in the jug?'.format(total)),
                Fraction(total)*Fraction(2,9))

    def test_nested_categories_in_both_directions(self):
        self.assertEqual(answer(
            'One third of the tokens are blue. One fifth of the blue tokens are shiny. '
            'There are 150 tokens in the box. How many tokens are blue and shiny?'),10)
        self.assertEqual(answer(
            'One third of the tokens are blue. One fifth of the blue tokens are shiny. '
            'There are 10 blue shiny tokens. How many tokens are in the box?'),150)

    def test_disjoint_categories_leave_a_remainder(self):
        self.assertEqual(answer(
            'Of 90 tokens, 1/6 are red and 2/9 are green. The others are blue. '
            'Calculate the number of blue tokens.'),55)

    def test_equal_servings_keep_the_measurement_base(self):
        self.assertEqual(answer(
            'A recipe serves six people. It uses half a cup of oil. '
            'Oil has 84 grams of fat per cup. How many grams of fat are in each serving?'),7)

    def test_fractional_gift_changes_the_recipient(self):
        self.assertEqual(answer(
            'Mina had 19 badges. Oren gave her 2/5 of his 35 badges. '
            'How many badges does Mina have now?'),33)
        p = Problem.read(
            'Mina had 19 badges. Oren gave her 2/5 of his 35 badges. '
            'How many badges does Oren have now?')
        self.assertIsNone(skill(p))

    def test_paired_quantities_distinguish_forward_and_inverse(self):
        self.assertEqual(answer(
            'Mina has 18 red tokens and half as many green tokens. '
            'How many tokens does Mina have in all?'),27)
        self.assertEqual(answer(
            'Mina has 18 red tokens, half as many as the number of green tokens she owns. '
            'How many tokens does Mina have altogether?'),54)

    def test_time_conversion_after_proportion(self):
        self.assertEqual(answer(
            'Together Mina and Oren spent a combined time of 9 years building their homes. '
            'Mina finished in half the time of Oren. '
            'How many months did Mina spend building her home?'),36)

    def test_negated_category_is_complementary(self):
        self.assertEqual(answer(
            'There are 48 players in a club. A quarter of the players have never lost a match. '
            'How many players have lost a match at least once?'),36)

    def test_nested_ownership_is_not_a_pair_of_disjoint_shares(self):
        for first, second, value in (('2/3','1/5',80),('1/4','2/7',90)):
            text = ('A farmer owned {} of a field. She sold {} of her share for ${}. '
                    'What is the worth of the entire field?').format(first,second,value)
            self.assertEqual(answer(text),Fraction(value)/Fraction(first)/Fraction(second))

    def test_enumerated_equal_groups_supply_a_denominator(self):
        self.assertEqual(answer(
            'There are 240 tokens that are either copper, silver, or gold. '
            'They are divided into equal groups. Mina took 1/4 of the silver ones. '
            'How many tokens did Mina take?'),20)

    def test_measurement_scale_uses_exact_mixed_numbers(self):
        self.assertEqual(answer(
            'On a drawing, 1/3 inch represents 7 miles of actual distance. '
            'The markers are 2 1/2 inches apart on the drawing. '
            'What is the actual distance in miles between them?'),Fraction(105,2))

    def test_avoided_destination_is_the_complement(self):
        self.assertEqual(answer(
            '2/7 of visitors prefer to avoid the ticket booth and instead use a kiosk. '
            'The number of visitors at the museum is 140. '
            'Calculate the number of visitors who pay at the ticket booth.'),100)

    def test_runtime_keeps_the_computed_monetary_answer(self):
        from bot import runtime
        text = ('Mina was only able to work half of her usual 30-hour week. '
                'Her hourly rate is $18. How much was her salary for that week?')
        result = runtime.turn(text,{})
        self.assertEqual(result['module'],'word_problem')
        self.assertIn('270 dollars',result['reply'])
        self.assertEqual(Fraction(result['reply'].rsplit('Answer: ',1)[1]),270)

    def test_unsupported_quantities_and_chat_abstain(self):
        for text in (
            'I have 3 kids and 2 dogs.',
            'I ate half my lunch and bought 2 books.',
            'Mina has 48 tokens. Half of them are blue. A box weighs 7 pounds. '
            'How many blue tokens does Mina have?',
            'Mina has 30 tokens. She gives half of them to Oren. '
            'She then gives half of the tokens to Niko. How many tokens did she have to start?',
            'Mina lost half her tokens. Oren has 30 tokens left. '
            'How many tokens did Mina have at first?',
        ):
            p = Problem.read(text)
            if p is None:
                self.assertIsNone(solve(text))
            else:
                self.assertIsNone(skill(p))


if __name__ == '__main__':
    unittest.main()
