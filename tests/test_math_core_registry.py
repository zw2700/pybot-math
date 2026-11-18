"""The math extension boundary must preserve independent skills and chat routing."""
import types
import unittest
from unittest.mock import Mock, patch

import bot.math as math


STORY = ('A vendor has 9 crates with 8 apples in each crate. '
         'How many apples are there altogether?')


class RegistryTests(unittest.TestCase):
    def test_independent_reader_survives_failed_or_invalid_readers(self):
        good = Mock(return_value=(72, 'Multiply the crate count by the crate size.'))
        readers = [Mock(side_effect=ZeroDivisionError), Mock(return_value=(1,)),
                   Mock(return_value=('not a number', 'Unknown.')),
                   Mock(return_value=(12, None)), good]
        with patch.object(math, '_SOLVERS', readers):
            self.assertTrue(math.solve(STORY).endswith('Answer: 72'))
        good.assert_called_once()

    def test_failed_readers_and_ordinary_chat_abstain(self):
        reader = Mock(side_effect=ValueError)
        with patch.object(math, '_SOLVERS', [reader]):
            self.assertIsNone(math.solve(STORY))
            reader.reset_mock()
            self.assertIsNone(math.solve('I have 3 kids and 2 dogs'))
            reader.assert_not_called()

    def test_discovery_is_ordered_and_optional_modules_are_isolated(self):
        good = Mock()
        entries = [types.SimpleNamespace(name=name)
                   for name in ['z_valid', '_helper', 'b_invalid', 'a_broken']]

        def import_module(name):
            if name.endswith('a_broken'):
                raise ImportError('Unavailable optional dependency')
            if name.endswith('b_invalid'):
                return types.SimpleNamespace(solve=None)
            return types.SimpleNamespace(solve=good)

        with patch.object(math.pkgutil, 'iter_modules', return_value=entries), \
                patch.object(math.importlib, 'import_module', side_effect=import_module) as importer:
            self.assertEqual(math._load_skills(), [good])
        self.assertEqual([call.args[0].rsplit('.', 1)[1] for call in importer.call_args_list],
                         ['a_broken', 'b_invalid', 'z_valid'])


if __name__ == '__main__':
    unittest.main()
