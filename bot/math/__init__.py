"""Exact arithmetic word-problem skills, discovered by filename."""
import importlib
import pkgutil
import re
from fractions import Fraction

from . import skills
from .numbers import format_number, parse_number, read_numbers
from .problem import Problem


def _quantity_context(problem):
    """Name the units used, so a calculation stays about its narrative."""
    stops = set(('a an the of in on at for to from with by and or but that which '
                 'who is are was were has have had will would can could does did '
                 'do each every per cost costs costing worth needs need bought '
                 'buys buy sold sells sell spent spends gets takes paid pays '
                 'earned earns make makes left remaining long wide deep now how '
                 'when then after before only it he she they his her their').split())
    labels = []
    for n in problem.numbers:
        if n.kind in ('money', 'percent'):
            continue
        words = re.match(r'\s*[- ]?([a-z]+(?:[ -]+[a-z]+){0,2})', problem.text[n.end:].lower())
        label = []
        for word in words.group(1).split() if words else []:
            if word in stops:
                break
            label.append(word)
        phrase = ' '.join(label)
        if phrase and phrase not in labels:
            labels.append(phrase)
    return 'Using {}: '.format(', '.join(labels[:4])) if labels else ''


def _load_skills():
    solvers = []
    for entry in sorted(pkgutil.iter_modules(skills.__path__), key=lambda item: item.name):
        if entry.name.startswith('_'):
            continue
        try:
            module = importlib.import_module(skills.__name__ + '.' + entry.name)
        except Exception:
            # A broken optional skill must not disable the entire math module.
            continue
        solve = getattr(module, 'solve', None)
        if callable(solve):
            solvers.append(solve)
    return solvers


def solve(text):
    problem = Problem.read(text)
    if problem is None:
        return None
    for skill in _SOLVERS:
        try:
            result = skill(problem)
            if result is None:
                continue
            answer, working = result
            answer = Fraction(answer)
            reply = '{}{} Answer: {}'.format(_quantity_context(problem), working.strip(), format_number(answer))
        except Exception:
            # As with runtime modules, one reader's unsupported input or invalid
            # result must not prevent independent readers from understanding it.
            continue
        return reply.strip()
    return None


_SOLVERS = _load_skills()
