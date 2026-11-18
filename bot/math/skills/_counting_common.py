"""Exact arithmetic and fully accounted relation graphs for counting readers.

The language readers supply edges only after recognizing an explicit relation.
This module never infers an operation from the number of quantities.
"""
from fractions import Fraction

from ..numbers import format_number


def answer(value, expression):
    if value < 0:
        return None
    return value, expression + ' = ' + format_number(value) + '.'


def total(values):
    return sum(values, Fraction(0))


def fmt(values, op=' + '):
    return op.join(format_number(v) for v in values)


def tokenize(problem):
    """Replace quantities in reverse offset order, preserving the other text."""
    text = problem.text.lower()
    for i, number in reversed(list(enumerate(problem.numbers))):
        text = text[:number.start] + 'Q{}'.format(i) + text[number.end:]
    return text


def products(values, parents, active=None, order='count_first', shared=False):
    """Evaluate explicit rate -> (count, conversion) edges, or abstain.

    Every active quantity must reach an output. Cycles, dangling references,
    and accidental reuse of a count are rejected. Readers that explicitly
    establish a common count for several rates may opt into shared counts.
    The result retains output indices so callers can check requested units.
    """
    active = set(range(len(values))) if active is None else set(active)
    if not active or not active <= set(range(len(values))):
        return None
    if any(i not in active or j not in active or factor <= 0
           for i, (j, factor) in parents.items()):
        return None
    consumed = {j for j, factor in parents.values()}
    if not shared and len(consumed) != len(parents):
        return None
    roots = sorted(active - consumed)
    if not roots:
        return None
    seen = set()

    def evaluate(i, visiting):
        if i in visiting or (not shared and i in seen):
            raise ValueError('cyclic or reused quantity')
        seen.add(i)
        value, expression = values[i], format_number(values[i])
        if i in parents:
            j, factor = parents[i]
            count, working = evaluate(j, visiting | {i})
            value *= count * factor
            if order == 'rate_first':
                expression += ' x (' + working + ')'
            elif order == 'flat':
                expression = working + ' x ' + expression
            else:
                expression = '(' + working + ') x ' + expression
            if factor != 1:
                expression += ' x ' + format_number(factor)
        return value, expression

    try:
        terms = [(i,) + evaluate(i, set()) for i in roots]
    except ValueError:
        return None
    return terms if seen == active else None
