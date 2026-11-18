"""Money rules must transfer across nouns without discarding price categories."""
import unittest
from fractions import Fraction

from bot.math.problem import Problem
from bot.math.skills import money_totals_change_prices_1_2_steps_r02_a1 as basic
from bot.math.skills import money_totals_change_prices_1_2_steps_r06_a4 as equations
from bot.math.skills import money_totals_change_prices_3_steps_r05_a1 as linked
from bot.math.skills import money_totals_change_prices_3_steps_r09_a6 as itemized


def answer(skill, text):
    problem = Problem.read(text)
    result = skill.solve(problem) if problem else None
    return result[0] if result else None


class GeneralMoneyTests(unittest.TestCase):
    def test_ticket_categories_follow_the_text(self):
        for first, second in [('senior', 'apprentice'), ('veteran', 'volunteer')]:
            for quantity, other in [(3, 5), (7, 2)]:
                text = ('{} tickets cost $9 and {} tickets cost $4. '
                        'A group has {} {}s and {} {}s. '
                        'How much will they pay?').format(
                            first.capitalize(), second, quantity, first, other, second)
                self.assertEqual(answer(equations, text), 9*quantity+4*other)

    def test_container_contents_and_modifiers_stay_distinct(self):
        for first, second in [('trays of seedlings', 'trays of pots'),
                              ('crates of red apples', 'crates of green apples'),
                              ('small sacks of rice', 'large sacks of rice')]:
            text = ('A stall sells {} for $6 each and {} for $9 each. '
                    'A shopper buys 2 {} and 3 {}. '
                    'How much did she spend?').format(first, second, first, second)
            self.assertEqual(answer(itemized, text), 39)

    def test_cent_prices_and_arbitrary_containers(self):
        for container in ['trays', 'bundles', 'hampers']:
            text = ('A shopper buys 3 {} of seedlings for 45 cents each. '
                    'She pays with a $5 bill. How much change does she get?').format(container)
            for skill in (basic, linked):
                self.assertEqual(answer(skill, text), Fraction(73, 20))

    def test_installments_use_known_calendar_conversions(self):
        self.assertEqual(answer(linked,
            'A club charges $5 per week and has a $20 joining fee. '
            'How much will a member pay for the first 2 years?'), 540)
        self.assertIsNone(answer(linked,
            'A club charges $5 per week and has a $20 joining fee. '
            'How much will a member pay for the first 2 months?'))

    def test_relative_clauses_keep_the_whole_priced_unit(self):
        self.assertEqual(answer(itemized,
            'A shopper bought 4 brushes which cost $1.50 each and 2 '
            'bundles of cloths which cost $2 each. She has $15. '
            'How much money does she have left?'), 5)

    def test_workforce_comes_from_distributive_grammar(self):
        self.assertEqual(answer(linked,
            'A studio hires 4 qualified sculptors. Each qualified sculptor '
            'works 2 hours a day for 3 days and earns $11 per hour. '
            'How much money will the studio pay?'), 264)

    def test_itemized_counts_are_not_added_to_the_list(self):
        for skill in (equations, linked):
            self.assertEqual(answer(skill,
                'A shopper buys two manuals: a manual for 5.5£ and a '
                'manual for 6.5£. She gives a 20£ bill to the seller. '
                'How much change does she get back?'), 8)

    def test_unpriced_contents_and_categories_abstain(self):
        for text in [
            'A stall sells trays of seedlings for $6 each. A shopper buys '
            '2 trays of seedlings and 3 trays of pots. How much did she spend?',
            'Senior tickets cost $9 and apprentice tickets cost $4. A group '
            'has 3 seniors, 5 apprentices and 2 volunteers. How much will they pay?',
            'A shopper buys 3 hampers of seedlings for $4 each and 2 hampers '
            'of pots. How much did she pay?',
            'The price of 3 liters of oil and 2 liters of syrup is $22. '
            'A liter of oil costs $4. How much will 2 liters of oil and '
            'a liter of syrup cost?',
            'A shopper buys 3 pencils for 2€ each and 4 markers for $3 '
            'each. How much money did she spend?',
        ]:
            for skill in (basic, equations, linked, itemized):
                self.assertIsNone(answer(skill, text), (skill.__name__, text))

    def test_general_categories_survive_runtime_routing(self):
        from bot.runtime import turn
        result = turn(
            'Veteran tickets cost $9 and volunteer tickets cost $4. '
            'A group has 3 veterans and 5 volunteers. How much will they pay?', {})
        self.assertEqual(result['module'], 'word_problem')
        self.assertTrue(result['reply'].endswith('Answer: 47'))


if __name__ == '__main__':
    unittest.main()
