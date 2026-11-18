"""Quantitative requests share a conservative gate, independent of skills."""
import unittest

from bot.math.problem import Problem


class ProblemReadingTests(unittest.TestCase):
    def test_quantity_requests_use_shared_measurement_vocabulary(self):
        body = 'A sack weighs 8 kilograms and another sack weighs 5 kilograms. '
        for question in ['How heavy are the sacks together?',
                         'What is the combined mass of the sacks?',
                         'Determine the total weight of the sacks.',
                         'Find the combined weight of the sacks.']:
            with self.subTest(question=question):
                problem = Problem.read(body + question)
                self.assertIsNotNone(problem)
                self.assertEqual(problem.question, question.lower())
                self.assertEqual(problem.body, body.lower())

    def test_singular_interval_uses_number_spans_and_arbitrary_units(self):
        for interval in ['eight', '8', '2.5', 'one and a half']:
            text = ('A device emits a short pulse every {} cycles during normal operation. '
                    'How many pulses are emitted in a cycle?').format(interval)
            with self.subTest(interval=interval):
                problem = Problem.read(text)
                self.assertIsNotNone(problem)
                self.assertEqual(len(problem.numbers), 1)
                self.assertEqual(problem.numbers[0].raw, interval)

    def test_personal_statements_and_advice_do_not_become_problems(self):
        for text in [
            'I have 3 kids and 2 dogs.',
            'I am 28 and my sister is 24. How should we plan a vacation?',
            'I have $20 and my sister has $30. What is a good place to visit?',
            'My jars have 8 and 5 stones. What are the best colors for my room?',
        ]:
            with self.subTest(text=text):
                self.assertIsNone(Problem.read(text))


if __name__ == '__main__':
    unittest.main()
