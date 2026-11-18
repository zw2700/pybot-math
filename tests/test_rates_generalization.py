"""Rate grammar should transfer across objects, predicates, and modifiers."""
import unittest
from fractions import Fraction

from bot.math.problem import Problem
from bot.math.skills import rates_and_unit_rates_r03_a5 as first
from bot.math.skills import rates_and_unit_rates_r03_a6 as second
from bot.math.skills import rates_and_unit_rates_r06_a3 as third
from bot.math.skills import rates_and_unit_rates_r07_a4 as fourth


SOLVERS = (first.solve, second.solve, third.solve, fourth.solve)


class GeneralRateGrammarTests(unittest.TestCase):
    def check_solvers(self, text, expected):
        problem = Problem.read(text)
        self.assertIsNotNone(problem)
        for solve in SOLVERS:
            with self.subTest(solver=solve.__module__, text=text):
                result = solve(problem)
                self.assertEqual(result[0] if result else None, expected)

    def test_unlisted_actions_and_compound_nouns(self):
        examples = [
            ('artisans', 'artisan', 'engraves', 'pendants'),
            ('mobile cranes', 'mobile crane', 'hoists', 'marble panels'),
            ('small robots', 'small robot', 'polishes', 'brass fittings'),
        ]
        for plural, singular, action, output in examples:
            for count, amount in [(4, 13), (7, 9)]:
                text = ('A workshop has {} {}. Each {} {} {} {}. '
                        'How many {} are handled altogether?').format(
                            count, plural, singular, action, amount, output, output)
                self.check_solvers(text, count*amount)

    def test_modals_and_of_phrases(self):
        for auxiliary in ('', 'can ', 'will '):
            action = 'measures' if not auxiliary else 'measure'
            text = ('A shop has 5 spools of ribbon. Each spool of ribbon '
                    '{}{} 8 meters. How many meters of ribbon does the '
                    'shop have?').format(auxiliary, action)
            self.check_solvers(text, 40)

    def test_passive_capacity_has_no_object_vocabulary(self):
        for predicate in ('is decorated with', 'is filled with', 'will be filled with'):
            text = ('A club has 6 mats. Each mat {} 11 silver stars. '
                    'How many silver stars are on all the mats?').format(predicate)
            self.check_solvers(text, 66)

    def test_nested_relations_keep_exact_time_conversion(self):
        for people, output, seconds in [(3, 8, 15), (5, 7, 11)]:
            text = ('A studio has {} artists. Each artist engraves {} seals '
                    'and each seal requires {} seconds. How many minutes '
                    'do the engravings take?').format(people, output, seconds)
            self.check_solvers(text, Fraction(people*output*seconds, 60))

    def test_each_subject_can_have_a_separate_period_denominator(self):
        text = ('A workshop has 4 artisans. Each artisan engraves 7 pendants '
                'per hour. How many pendants do they engrave in 3 hours?')
        # Both the artisan count and the operating duration must be consumed.
        for solve in (first.solve, third.solve):
            result = solve(Problem.read(text))
            self.assertEqual(result[0] if result else None, 84)

    def test_any_named_container_can_have_a_measured_capacity(self):
        text = ('A store has 4 vats of 8 liters each. '
                'How many 2-liter flasks can be filled?')
        result = second.solve(Problem.read(text))
        self.assertEqual(result[0] if result else None, 16)
        for question, expected in [
            ('How many 4-liter flasks can be filled?', 7),
            ('How many 4-liter flasks are needed to hold the liquid?', 8),
        ]:
            text = 'A store has 3 vats of 10 liters each. ' + question
            result = second.solve(Problem.read(text))
            self.assertEqual(result[0] if result else None, expected)

    def test_group_size_without_postposed_each(self):
        for groups, size in [(7, 250), (12, 125), (3, 400)]:
            text = ('A trader sells {} parcels of {} grams of resin every '
                    'week. How many kilograms of resin does the trader '
                    'sell every week?').format(groups, size)
            for solve in (first.solve, third.solve, fourth.solve):
                with self.subTest(solver=solve.__module__, text=text):
                    result = solve(Problem.read(text))
                    self.assertEqual(result[0] if result else None,
                                     Fraction(groups*size, 1000))

    def test_unit_rates_keep_the_full_denominator_noun_phrase(self):
        text = ('A machine supplies 12 tiles per wooden crate. '
                'A warehouse has 60 tiles. How many crates does the warehouse need?')
        self.check_solvers(text, 5)

    def test_unknown_relations_and_unused_quantities_abstain(self):
        for text in [
            'A workshop has 7 artisans. Each artisan does not engrave 9 '
            'pendants. How many pendants do they engrave?',
            'A workshop has 7 artisans. Each artisan engraves at least 9 '
            'pendants. How many pendants do they engrave?',
            'A workshop has 7 artisans. Each artisan may engrave 9 '
            'pendants. How many pendants do they engrave?',
            'A workshop has 7 artisans and 3 supervisors. Each artisan '
            'engraves 9 pendants. How many pendants do they engrave?',
            'A workshop has 7 artisans. Each artisan engraves 9 pendants. '
            'How many bracelets do they engrave?',
            'A trader sells 7 parcels out of 250 boxes of resin every '
            'week. How many kilograms of resin does the trader sell every week?',
        ]:
            self.check_solvers(text, None)

    def test_runtime_routes_generalized_rate_relations(self):
        from bot.runtime import turn
        text = ('A workshop has 7 artisans. Each artisan engraves 9 pendants. '
                'How many pendants do they engrave?')
        result = turn(text, {})
        self.assertEqual(result['module'], 'word_problem')
        self.assertTrue(result['reply'].endswith('Answer: 63'), result['reply'])


if __name__ == '__main__':
    unittest.main()
