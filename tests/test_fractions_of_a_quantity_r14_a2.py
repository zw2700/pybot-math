"""Fraction compositions preserve their bases under changed quantities and units."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.fractions_of_a_quantity_r14_a2 import solve as skill


def answer(text):
    reply = solve(text)
    return None if reply is None else Fraction(reply.rsplit('Answer: ', 1)[1])


class ComposedFractions(unittest.TestCase):
    def test_running_remainders_and_literal_loss(self):
        for name, unit, total in (('Ivy', 'shells', 72), ('Omar', 'tokens', 180)):
            text = ('{} had {} {}. She gave 1/3 of them to a friend. '
                    'Of the remaining {}, she gave 1/4 to a neighbor and another '
                    '5 {} to a cousin. How many {} did she have left?').format(
                        name, total, unit, unit, unit, unit)
            self.assertEqual(answer(text), Fraction(total, 2)-5)

    def test_original_and_remaining_are_different_bases(self):
        texts = [
            ('Ivy had 120 tiles. She used 1/3 of her tiles and gave 1/4 of '
             'the remaining tiles to a friend. How many tiles did she keep?', 60),
            ('Ivy had 120 tiles. She used 1/3 of her tiles and gave 1/4 of '
             'the original tiles to a friend. How many tiles did she keep?', 50),
        ]
        for text, expected in texts:
            self.assertEqual(skill(Problem.read(text))[0], expected)

    def test_unresolved_repeated_share_abstains(self):
        text = ('Ivy had 120 tiles. She used 1/3 of her tiles and gave 1/4 of '
                'her tiles to a friend. How many tiles did she keep?')
        self.assertIsNone(skill(Problem.read(text)))

    def test_group_counts_are_converted_before_shares(self):
        text = ('Omar baked 6 batches of rolls, with 24 rolls in each batch. '
                'He set aside 1/3 of the rolls in each batch for guests, put '
                '3/4 of the remaining in a container, and gave out the rest. '
                'How many rolls are given out?')
        self.assertEqual(answer(text), 24)

    def test_gift_changes_the_recipients_base(self):
        text = ('Ava has 11 cards. Ben gives Ava a fifth of his 30 cards. '
                'Then Ava gives a third of her cards to a neighbor. '
                'How many cards does Ava have remaining?')
        self.assertAlmostEqual(float(answer(text)), float(Fraction(34, 3)))

    def test_inventory_and_requested_subset(self):
        text = ('There are 18 ponies, 22 sheep, and 16 goats on a farm. '
                'A storm hits and half of all the animals get sick. '
                'How many animals in total get sick?')
        self.assertEqual(answer(text), 28)

    def test_fractional_expenses_refer_to_previous_expense(self):
        text = ('A club was given a $600 budget for the month. They bought '
                '$240 worth of equipment, spent 1/3 of that amount on transport, '
                'and used 1/4 of the transport cost on packing. '
                'How many dollars of their budget remained?')
        self.assertEqual(answer(text), 260)

    def test_denominations_are_divisors_of_their_allocations(self):
        text = ('An organizer has a $720 bill to change into smaller bills. '
                'She wants to change 2/5 of the money into $12 bills while '
                'the rest into $18 bills. How many pieces of bills will she '
                'have in all?')
        self.assertEqual(answer(text), 48)

    def test_overlapping_shares_use_inclusion_exclusion(self):
        for total in (60, 180):
            text = ('There are {} students in a class. Half of them play chess. '
                    'One-third play tennis and one-sixth play both chess and '
                    'tennis. How many students do not play either game?').format(total)
            self.assertEqual(answer(text), Fraction(total, 3))

    def test_nested_subset_only_its_nonfinishers_are_removed(self):
        text = ('There are 120 runners in a race. 1/3 of the runners were unable '
                'to finish. 3/4 of the remaining runners were tired and 1/5 of '
                "those tired runners couldn't finish the race. How many runners "
                'finished the race?')
        self.assertEqual(answer(text), 68)

    def test_separate_categories_with_different_yields(self):
        text = ('There are 48 racks in a room. Half the racks have 3 shelves '
                'each, 8 have 4 shelves each and the rest have 5 shelves each. '
                'How many shelves in total are in the room?')
        self.assertEqual(answer(text), 184)

    def test_each_fraction_is_of_a_single_unit(self):
        text = ('Some friends share 3 pies. Ada ate half of a pie. Ben ate '
                'one-third of a pie and Cora ate a quarter of a pie. '
                'If each pie is cut into 24 slices, how many slices were left over?')
        self.assertEqual(answer(text), 46)

    def test_multi_level_subset_chain(self):
        text = ('A school has 900 students. One-third of the students are in '
                'the choir. Of the students in the choir, half of them play '
                'a string instrument. Of the students that play a string '
                'instrument, a fifth of them play the violin. Of the students '
                'that play the violin, a third of them play the electric violin. '
                'How many students play the electric violin?')
        self.assertEqual(answer(text), 10)

    def test_weekly_earnings_and_successive_expenses(self):
        text = ('The rate for repairing tools is $18 per hour. Uma worked for '
                '3 hours a day for a week. She then spent 1/3 of the money '
                'on supplies and gave 1/4 of the remaining money to a charity. '
                'How much money did she have left?')
        self.assertEqual(answer(text), 189)

    def test_bounce_count_is_an_ordinal(self):
        text = ('A worker drops a ball from a 128-foot tall tower. The ball '
                'bounces to half the height from which it fell on each bounce. '
                'How high will it bounce on the sixth bounce?')
        self.assertEqual(answer(text), 2)

    def test_unexplained_quantities_and_chat_abstain(self):
        for text in (
            'Ava has 60 cards. She gives half to a friend. A crate weighs '
            '9 pounds. How many cards does Ava have left?',
            'Ava had 60 cards. A clock shows 4 hours. She gave half of her '
            'cards to a friend. How many cards are left?',
            'Ava has 60 cards and half as many postcards. How many cards '
            'will she buy at the shop?',
        ):
            p = Problem.read(text)
            self.assertIsNone(None if p is None else skill(p))
        for text in ('I have 3 kids and 2 dogs.', 'I spent half my day reading.',
                     'I have 12 cards and gave half to my friend.'):
            self.assertIsNone(solve(text))

    def test_runtime_routes_exact_answer(self):
        from bot.runtime import turn
        text = ('Ravi had 90 counters. He used 1/3 of his counters, gave 1/4 '
                'of the remaining to a friend, and kept the rest. '
                'How many counters did he keep?')
        result = turn(text, {})
        self.assertEqual(result['module'], 'word_problem')
        self.assertTrue(result['reply'].endswith('Answer: 45'))


if __name__ == '__main__':
    unittest.main()
