"""Semantic rate joins, exact conversions, and conservative abstention."""
import unittest
from fractions import Fraction

from bot.math import solve as solve_all
from bot.math.problem import Problem
from bot.math.skills.rates_and_unit_rates_r07_a4 import solve


def answer(text, integrated=False):
    if integrated:
        reply = solve_all(text)
        return Fraction(reply.rsplit('Answer: ', 1)[1]) if reply else None
    problem = Problem.read(text)
    result = solve(problem) if problem else None
    return result[0] if result else None


class MultiStageRates(unittest.TestCase):
    def test_weighted_prices_are_weighted_by_item_count(self):
        for a, b, pa, pb in [(3, 5, 8, 14), (7, 2, 11, 5), (4, 4, 6, 9)]:
            text = ('A buyer bought {} books in hardback for ${} each and {} '
                    'books in paperback for ${} each. What is the average '
                    'price paid per book?').format(a, pa, b, pb)
            self.assertEqual(answer(text), Fraction(a*pa+b*pb, a+b))

    def test_savings_use_net_income(self):
        text = ('A student wants a lamp that costs $90 and already has $10 '
                'in savings. Her parents give her $12 every week but she '
                'spends $4 each weekend. How many weeks must she save?')
        self.assertEqual(answer(text), 10)

    def test_repack_after_loss(self):
        for size, count, lost, capacity in [(18, 11, 3, 15), (24, 8, 12, 9)]:
            text = ('There were {} letters in each bag. {} bags were delivered '
                    'to an office. {} letters were damaged and thrown away. '
                    'The remaining letters were packed into boxes of {} letters '
                    'each. How many boxes were there?').format(size,count,lost,capacity)
            self.assertEqual(answer(text), Fraction(size*count-lost, capacity))

    def test_budget_joins_the_matching_item_price(self):
        # The purchased category appears second in the price list.
        text = ('A shop sells markers for $3 each and pencils for $2 each. '
                'A buyer has a budget of $26 and buys 4 pencils. How many '
                'markers could she buy with the remaining money?')
        self.assertEqual(answer(text), 6)

    def test_scheduled_work_converts_days_to_weeks(self):
        text = ('A student reads for 2 hours a day at a rate of 9 pages an hour. '
                'The assignment is 126 pages long. How many weeks will it '
                'take to finish the assignment?')
        self.assertEqual(answer(text), 1)

    def test_measured_production_after_grouping(self):
        text = ('A worker buys 4 kits that are 30 pieces each. She can assemble '
                '15 pieces every 6 minutes. How long would it take to finish '
                'all the kits?')
        self.assertEqual(answer(text), 48)

    def test_sum_journey_times(self):
        text = ('A courier travels 150 miles at 50 miles per hour on the first '
                'leg of a trip. She then travels 120 miles at 40 miles per '
                'hour. How many hours does the whole trip take?')
        self.assertEqual(answer(text), 6)

    def test_host_is_an_additional_recipient_and_boxes_round_up(self):
        text = ('Mira and five of her friends order food. Each person will '
                'eat 3 slices. Each pizza has 4 slices. How many pizzas '
                'should they order?')
        self.assertEqual(answer(text), 5)

    def test_batch_discount_in_requested_currency(self):
        text = ('One store charges $9 for 12 bolts while another store charges '
                '$8 for 16 bolts. How much can you save, in cents, on each '
                'bolt by buying from the second store?')
        self.assertEqual(answer(text), 25)

    def test_recovering_capital_converts_cents(self):
        text = ('A seller bought 50 eggs for $8. She will sell each egg for '
                '20 cents. How many eggs will she have left when she '
                'recovers her capital?')
        self.assertEqual(answer(text), 10)

    def test_growth_and_geometric_periods(self):
        self.assertEqual(answer(
            'A plant was 60 inches tall. It grew 3 inches per month for '
            '4 months. How tall is the plant in feet?'), 6)
        self.assertEqual(answer(
            'There are 5 birds in a sanctuary. The population doubles every '
            '3 months. How many birds will there be at the end of a year?'), 80)

    def test_episode_duration_is_distinct_from_daily_schedule(self):
        text = ('A series has 24 episodes, each one of which is 15 minutes '
                'long. A viewer watches for 2 hours a day. How many days '
                'will it take to watch the whole series?')
        self.assertEqual(answer(text), 3)

    def test_workforce_adds_worker_days(self):
        text = ('A farmer has 900 acres to plant in 6 days. A crew of 3 tractors '
                'working for 2 days and then a crew of 6 tractors working for '
                'another 4 days do the job. How many acres per day does each '
                'tractor need to plant?')
        self.assertEqual(answer(text), 30)
        self.assertEqual(answer(text, integrated=True), 30)

    def test_stock_is_shared_then_each_share_is_reduced(self):
        text = ('A person has 100 beads and uses 12 beads. The remaining beads '
                'are divided into 4 bags equally. She takes away 5 beads from '
                'each bag. How many beads are in one bag?')
        self.assertEqual(answer(text), 17)

    def test_integration_preserves_comparison_before_sharing(self):
        text = ('Lena has $24 more money than Oren. If Lena has $96, and '
                'they combine and share their money equally, how much '
                'money does each get?')
        self.assertEqual(answer(text, integrated=True), 84)

    def test_unexplained_quantities_and_ambiguous_prices_abstain(self):
        for text in [
            'A machine makes 8 tokens every 3 minutes and uses 5 batteries. '
            'How many tokens can it make in 12 minutes?',
            'A shop sells pencils for $2 per packet and pencils for $3 per '
            'packet. A buyer wants 4 packets of pencils and has $20. How many '
            'packets can she buy with the rest of her money?',
            'A driver travels 30 miles per hour but stops for a break. '
            'How many miles does she travel in 2 hours?',
            'A vendor has $60 and earns 5 euros per hour. How many '
            'hours does it take to earn that money?',
            'I have 3 kids and 2 dogs.',
        ]:
            self.assertIsNone(answer(text), text)


if __name__ == '__main__':
    unittest.main()
