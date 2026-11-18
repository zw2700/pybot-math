"""Fraction compositions, scope boundaries, and conservative abstention."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.fractions_of_a_quantity_r09_a1 import solve as skill


def answer(text):
    reply = solve(text)
    return None if reply is None else Fraction(reply.rsplit('Answer: ', 1)[1])


class FractionCompositionTests(unittest.TestCase):
    def test_addition_changes_the_fraction_base(self):
        for start, added, denominator in ((39, 9, 4), (65, 15, 5)):
            text = ('A rancher has {} goats. The rancher adds {} new goats '
                    'and then sells 1/{} of the herd. How many goats are left?').format(start, added, denominator)
            self.assertEqual(answer(text), (start+added)*(1-Fraction(1, denominator)))

    def test_literal_removal_then_remaining_share(self):
        self.assertEqual(answer(
            'Nora gets 800 MB of data each month. She spends 200 MB on movies '
            "and 1/4 of what's left on games. How many MB does she have left?"), 450)

    def test_relative_consumption_is_not_a_stock_delta(self):
        self.assertEqual(answer(
            'Omar made 20 rolls. On the first day he ate half of the rolls he made. '
            'The next day he ate 3 rolls less. How many rolls are left after these two days?'), 3)

    def test_original_and_remaining_scope_stay_distinct(self):
        for scope, expected in (('original', 84), ('remaining', Fraction(171, 2))):
            text = ('$120 was divided between Nora and Inez. Inez received 3/4 of the money. '
                    'Inez then spent 1/20 of the {} money. How much does Inez have left?').format(scope)
            self.assertEqual(answer(text), expected)

    def test_chained_transfers_follow_the_recipient(self):
        self.assertEqual(answer(
            'Nora had 120 beads. She gave half to her brother Omar. '
            'He gave a third of his to his friend Inez. Inez used 7 beads. '
            'How many beads does Inez have left?'), 13)

    def test_repeated_reduction_requires_an_exact_target(self):
        self.assertEqual(answer(
            'Omar drinks 81 sodas a week. He cuts that number in a third each week. '
            'How many weeks until he drinks 3 sodas per week?'), 3)
        p = Problem.read(
            'Omar drinks 80 sodas a week. He cuts that number in half each week. '
            'How many weeks until he drinks 7 sodas per week?')
        self.assertIsNone(skill(p))

    def test_weekly_pay_share(self):
        self.assertEqual(answer(
            'Nora works 4 days a week and earns $12 per hour. She works 5 hours a day '
            'and allocates 2/3 of her weekly earnings for school. How much does she allocate?'), 160)

    def test_both_dimensions_scale(self):
        self.assertEqual(answer(
            'A rectangle has a length of 36 meters and a width of 18 meters. '
            'A smaller rectangle has a third the length and width. '
            'What is the area of the smaller rectangle?'), 72)

    def test_fractional_daily_time(self):
        self.assertEqual(answer(
            'Nora spends a third of an hour twice a day exercising. '
            'She spends a fifth of an hour every day stretching. '
            'How many minutes does Nora spend exercising and stretching each day?'), 52)

    def test_combined_pair_is_not_a_subset(self):
        self.assertEqual(answer(
            'Nora and Omar were running. Together they ran 48 miles. '
            'Omar ran a third of the distance that Nora ran. '
            'How many miles did Nora run?'), 36)

    def test_category_graph_and_forward_reference(self):
        self.assertEqual(answer(
            'A machine has red, green, and blue tokens. It has half as many blue tokens '
            'as red tokens. For each blue token, it has 3 times as many green tokens. '
            'If it has 24 red tokens, how many tokens are in the machine?'), 72)

    def test_indexed_event_sum(self):
        self.assertEqual(answer(
            'A shop sold 20 copies on Monday. On Tuesday it sold three times that many copies. '
            'On Wednesday it sold one-fifth the number of copies it did on Tuesday. '
            'How many copies did it sell by Wednesday?'), 92)
        self.assertEqual(answer(
            'In January a shop sold 20 copies. In February it sold three times as many copies '
            'as it did in January. In March it sold half as many copies as in February. '
            'How many copies did it sell in the first three months?'), 110)

    def test_indexed_rate_is_per_member(self):
        self.assertEqual(answer(
            'Nora has three dogs. The first dog eats 2 cups a day. '
            'The second dog eats twice as much while the third dog eats '
            '3 cups more than the second dog. How many cups should Nora prepare for her three dogs?'), 13)

    def test_participant_count_is_a_label(self):
        self.assertEqual(answer(
            'Nora has half as many beads as Omar. Inez has five times as many beads as Omar. '
            'How many beads do these three people have, if Inez has 40 beads?'), 52)

    def test_fraction_fewer_is_proportional(self):
        for whole, numerator, denominator in ((240, 2, 3), (350, 3, 7)):
            text = ('A garden has {}/{} fewer trees than a nearby orchard, which has {} trees. '
                    'How many trees are in both the garden and orchard combined?').format(numerator, denominator, whole)
            self.assertEqual(answer(text), whole*(2-Fraction(numerator, denominator)))

    def test_mixed_dozen(self):
        self.assertEqual(answer(
            'Nora wants to buy three and one-half dozens of pens. '
            'How many pens will she have?'), 42)

    def test_work_rate_and_fractional_hour(self):
        self.assertEqual(answer(
            'Nora has a report that needs 1200 words. She can type 240 words in half an hour. '
            'She has already written 400 words. How many more minutes to finish the report?'), 100)

    def test_future_age_shifts_both_people(self):
        self.assertEqual(answer(
            "In 4 years, Nora will be half of Omar's age. If Omar is 20 years old, "
            'how many years old is Nora now?'), 8)

    def test_loss_is_local_to_one_equal_group(self):
        self.assertEqual(answer(
            'Nora has 40 kilos of flour. She divides them into 5 bags equally. '
            'Then one of the bags tears and half of the flour falls to the ground. '
            'How many kilos of flour remain?'), 36)

    def test_unexplained_quantities_and_chat_abstain(self):
        self.assertIsNone(solve('I have 3 kids and 2 dogs.'))
        self.assertIsNone(solve('I gave half my lunch to a friend and bought 2 drinks.'))
        p = Problem.read(
            'Nora has 40 beads and gives half of them to Omar. A box weighs 7 pounds. '
            'How many beads does Nora have left?')
        self.assertIsNone(skill(p))
        self.assertIsNone(skill(Problem.read(
            'Nora earns $0 washing cars and $0 walking dogs each month. '
            'She puts half of that money away each month. How long to save $100?')))


if __name__ == '__main__':
    unittest.main()
