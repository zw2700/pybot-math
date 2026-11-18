"""Rate relations must survive new quantities, units, and narrative subjects."""
import unittest
from fractions import Fraction

from bot.math import solve as solve_all
from bot.math.numbers import read_numbers, parse_number
from bot.math.problem import Problem
from bot.math.skills.rates_and_unit_rates_r10_a1 import solve


def answer(text, integrated=False):
    if integrated:
        reply = solve_all(text)
        return Fraction(reply.rsplit('Answer: ', 1)[1]) if reply else None
    problem = Problem.read(text)
    result = solve(problem) if problem else None
    return result[0] if result else None


class ShortRateRelations(unittest.TestCase):
    def test_container_capacity_divides_instead_of_multiplying(self):
        for daily, size, days in [('1.5', '0.5', 4), ('3', '2', 5), ('2.4', '0.6', 3)]:
            text = ('A traveler drinks {} liters of water each day. How many '
                    'bottles of {}-liter water should she buy for her {} days '
                    'consumption?').format(daily, size, days)
            value = Fraction(daily)*days/Fraction(size)
            expected = -(-value.numerator//value.denominator)
            self.assertEqual(answer(text, integrated=True), expected)

    def test_remainder_has_an_omitted_object(self):
        for total, eaten, per_child in [(146, 26, 15), (215, 35, 12), (87, 12, 5)]:
            text = ('A parent made {} dumplings for the family. The adults ate {}, '
                    'and the rest was divided equally among the children. If each '
                    'child received {} dumplings, how many children are there?').format(total, eaten, per_child)
            self.assertEqual(answer(text), Fraction(total-eaten, per_child))

    def test_available_work_hours_do_not_invert(self):
        text = ('A craftsperson spends 24 hours every week shaping. It takes her '
                '6 hours to complete a sculpture. How many sculptures can she '
                'make in 5 weeks?')
        self.assertEqual(answer(text), 20)

    def test_capacity_comparison_has_an_ordered_old_and_new_size(self):
        text = ('A storage drive can hold 900 drawings of 12 kilobytes each. '
                'How many drawings can it hold of 9 kilobytes each?')
        self.assertEqual(answer(text), 1200)

    def test_observed_speed_converts_minutes(self):
        text = ('A courier must cross a 12 kilometer valley in her vehicle in '
                '18 minutes. How fast must she travel in kilometers per hour?')
        self.assertEqual(answer(text), 40)

    def test_mixture_total_includes_both_ingredients(self):
        text = ('A painter uses a ratio of 3 grams of pigment to every 7 grams '
                'of solvent. The finished batch weighs 80 grams. How many grams '
                'of pigment did the painter use?')
        self.assertEqual(answer(text), 24)

    def test_weekday_schedule_is_per_week(self):
        text = ('A technician has 84 filters to inspect. She inspects 3 filters '
                'every Tuesday and 4 filters every Friday each week. How many '
                'weeks will it take her to inspect all the filters?')
        self.assertEqual(answer(text), 12)

    def test_time_duty_cycle_is_not_an_occurrence_count(self):
        text = ('A device activates every 20 seconds, and each time it activates '
                'it runs for 4 seconds. How many seconds per minute does it run?')
        self.assertEqual(answer(text), 12)

    def test_net_flow_must_move_toward_the_requested_goal(self):
        for removed, grown, expected in [(4, 1, 8), (2, 3, None)]:
            text = ('A worker strips {} feet of a vine every day, but the vine '
                    'grows {} feet every night. The wall is covered by 24 feet '
                    'of vine. How many days will it take to strip all the vine?').format(removed, grown)
            self.assertEqual(answer(text), expected)

    def test_stopping_waste_is_not_a_work_break(self):
        text = ('A traveler drinks 96 ounces of water per day. To stop wasting '
                'plastic, she buys a 96-ounce water bottle. How many times '
                'will she fill it each week?')
        self.assertEqual(answer(text), 7)

    def test_quoted_batch_price_is_not_a_unit_price(self):
        text = ('A set of 8 forks costs $36. If the forks are sold separately, '
                'how much would 6 forks cost?')
        self.assertEqual(answer(text, integrated=True), 27)

    def test_currency_result_keeps_the_arithmetic_answer_in_runtime(self):
        from bot.runtime import turn
        text = ('A buyer bought a desk and 5 chairs for $230. The desk cost '
                '$80. If each chair cost the same amount, how much did '
                'each chair cost?')
        result = turn(text, {})
        self.assertEqual(result['module'], 'word_problem')
        self.assertTrue(result['reply'].endswith('Answer: 30'))

    def test_dozen_is_a_count_conversion(self):
        text = ('A crafter buys 5 dozen beads. Beads cost $0.25 each. '
                'How much did the crafter pay for beads?')
        self.assertEqual(answer(text), 15)

    def test_ordinal_suffix_on_slash_fractions_preserves_offsets(self):
        for raw in ('3/8th', '1/2nd', '5/3rd'):
            text = 'The measured width is {} of a meter.'.format(raw)
            numbers = read_numbers(text)
            self.assertEqual(len(numbers), 1)
            number = numbers[0]
            self.assertEqual(number.value, parse_number(raw[:-2]))
            self.assertEqual(text[number.start:number.end], raw)

    def test_fractional_length_is_not_a_selected_share_of_time(self):
        text = ('A runner has 15 minutes to travel 12 blocks, and each block '
                'is 1/4th of a mile. How fast must she run in miles per hour?')
        self.assertEqual(answer(text, integrated=True), 12)

    def test_purpose_clause_does_not_create_a_rate_denominator(self):
        text = ('A group has 18 students. Every session is 30 minutes long. '
                'How many sessions will it take for every student to finish '
                'if they have 4 minutes to do so?')
        self.assertIsNone(answer(text, integrated=True))

    def test_unsupported_quantities_and_changes_abstain(self):
        for text in [
            'A maker owns 12 tools and 8 bins. How many gadgets can she make?',
            'A maker produces 12 cups per hour and rests for 3 hours. How many cups does she make?',
            'A buyer has $24 and pays €3 for each pad. How many pads can she buy?',
            'A depot has 200 red bolts to share equally across 4 bins. It adds 20 blue bolts '
            'and twice as many green bolts. How many bolts in total go in each bin?',
            'A team shares 90 clips equally in 5 boxes. It loses 15 clips first. '
            'How many clips go in each box?',
            'I have 3 kids and 2 dogs',
        ]:
            self.assertIsNone(answer(text))


if __name__ == '__main__':
    unittest.main()
