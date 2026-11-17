"""Exact arithmetic word-problem skills, discovered by filename."""
import importlib
import pkgutil
from fractions import Fraction

from . import skills
from .numbers import format_number, parse_number, read_numbers
from .problem import Problem


def _load_skills():
    solvers = []
    for entry in sorted(pkgutil.iter_modules(skills.__path__), key=lambda item: item.name):
        if entry.name.startswith('_'):
            continue
        module = importlib.import_module(skills.__name__ + '.' + entry.name)
        solve = getattr(module, 'solve', None)
        if callable(solve):
            solvers.append(solve)
    return solvers


def solve(text):
    problem = Problem.read(text)
    if problem is None:
        return None
    for skill in _SOLVERS:
        result = skill(problem)
        if result is None:
            continue
        answer, working = result
        answer = Fraction(answer)
        return '{} Answer: {}'.format(working.strip(), format_number(answer)).strip()
    return None


_SOLVERS = _load_skills()
