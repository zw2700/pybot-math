"""New fraction compositions, with changed quantities, units and scopes."""
import unittest
from fractions import Fraction

from bot.math import solve
from bot.math.problem import Problem
from bot.math.skills.fractions_of_a_quantity_r12_a5 import solve as skill


def answer(text):
    reply = solve(text)
    return None if reply is None else Fraction(reply.rsplit('Answer: ',1)[1])


class FractionCompositions(unittest.TestCase):
    def test_nested_predicate_can_be_an_adjective(self):
        for total in (45,90,135):
            text = ('A tray contains {} tiles. One third of the tiles are green, '
                    'and half of the green tiles have dots. '
                    'How many green dotted tiles are in the tray?').format(total)
            self.assertEqual(answer(text),Fraction(total,6))

    def test_affine_cash_ledger_with_fixed_costs(self):
        for first, second, extra, final in (('1/3','1/4',7,23),('2/5','1/6',11,39)):
            text = ('Nora spent {} of her money and an additional ${} on supplies. '
                    'She spent {} of the remaining money and an additional $5 on transport. '
                    'She was left with ${}. How much money did she have at first?').format(first,extra,second,final)
            expected = ((Fraction(final)+5)/(1-Fraction(second))+extra)/(1-Fraction(first))
            self.assertEqual(skill(Problem.read(text))[0],expected)
            self.assertAlmostEqual(float(answer(text)),float(expected))

    def test_fractional_measure_is_subtracted_before_output(self):
        for stock, output, used in ((3,18,'1/4'),(5,12,'2/3')):
            text = ('A reservoir holds {} gallons of liquid. Each gallon can fill {} vials. '
                    'A machine uses {} of a gallon of liquid. '
                    'How many vials can the reservoir fill?').format(stock,output,used)
            self.assertEqual(answer(text),(Fraction(stock)-Fraction(used))*output)

    def test_combined_price_is_not_the_reference_price(self):
        for total, share in ((360,'1/5'),(420,'2/5')):
            text = ('Nora bought a vest and a belt for ${}. '
                    'What does the belt cost if it is {} the price of the vest?').format(total,share)
            self.assertEqual(answer(text),Fraction(total)*Fraction(share)/(1+Fraction(share)))

    def test_measured_parts_have_a_common_reference(self):
        text = ("A display has a border that's 1/5 the length of its panel, "
                "and a stand that's 1/3 the length of its panel. "
                'The display is 46 inches long overall. How long is its border?')
        self.assertEqual(answer(text),6)

    def test_hypothetical_stocks_share_the_unknown_initial_value(self):
        text = ('There are several counters in a pouch. Taking 4 counters away would '
                'leave 2/3 as many in the pouch as if 9 were added. '
                'How many counters are in the pouch?')
        self.assertEqual(answer(text),30)

    def test_original_stock_from_grouped_use_and_remainder(self):
        for people, each, retained in ((21,6,'1/4'),(15,8,'2/5')):
            text = ('{} visitors share a supply of tokens. After taking {} tokens each, '
                    'there is still {} of the original amount left. '
                    'What is the original number of tokens?').format(people,each,retained)
            self.assertEqual(answer(text),Fraction(people*each)/(1-Fraction(retained)))

    def test_time_conversion_keeps_component_durations(self):
        text = ('The three-quarter-hour broadcast includes 11 minutes of interviews, '
                '9 minutes of music, and 8 minutes of reports. The rest is discussion. '
                'How many minutes of discussion are in the broadcast?')
        self.assertEqual(answer(text),17)

    def test_group_comparison_is_applied_per_group(self):
        for groups, share in ((30,'1/5'),(24,'3/8')):
            text = ('A cabinet has {} baskets and {} times as many tokens as the '
                    'number of baskets in the cabinet are in each basket. '
                    "What's the total number of tokens in the cabinet?").format(groups,share)
            self.assertEqual(answer(text),groups*groups*Fraction(share))

    def test_equal_groups_and_a_smaller_group(self):
        text = ('Nora bought thirteen dozen counters. She brought three identically-sized '
                'boxes and a pouch. Into the pouch she put 1/4 as many counters as she '
                'put in each of the three boxes. How many counters did she put in the pouch?')
        self.assertEqual(answer(text),12)

    def test_event_comparisons_preserve_distance_and_change_scope(self):
        self.assertEqual(answer(
            'A walker travels 84 meters on the first day. On the second day, '
            'she travels two times as far as on the first day. On the third day, '
            'she travels 30 more meters than on the second day. '
            'What is the total distance she traveled in the three days?'),450)
        self.assertEqual(answer(
            'A machine produces 20 parts in its first year. The second year it '
            'produces 5 more than double the amount from the first year. '
            'In the third year production went down by one third. '
            'How many parts did it produce in total in the first three years?'),95)

    def test_extra_numbers_and_unresolved_scopes_abstain(self):
        for text in (
                'Nora has 48 tiles. Half of them are green. A crate weighs 9 pounds. '
                'How many green tiles does Nora have?',
                'A vehicle travels 12 miles in an hour. A tank is half full. '
                'How many miles does the vehicle travel in total?',
                'Nora has 40 cards. Half as many are in another box. Each box has '
                '7 compartments. How many cards are in the boxes in total?',
                'Nora spent 1/3 of her money and an additional $8 on supplies. '
                'Vera was left with $24. How much money did Nora have at first?'):
            p = Problem.read(text)
            self.assertIsNone(None if p is None else skill(p))
        self.assertIsNone(solve('I have 3 kids and 2 dogs.'))


if __name__ == '__main__':
    unittest.main()
