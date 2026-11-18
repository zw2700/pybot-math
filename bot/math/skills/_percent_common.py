"""Category percentages shared by the simple and composed readers."""
import re
from fractions import Fraction

from ._fractions_common import _answer, _has


def category_percentage(p, amounts):
    """Select disjoint counted categories, using an explicit total when given.

    A common noun cannot select a category: remove words shared by every label.
    Negation complements the selected categories, rather than changing the base.
    """
    if not _has(r'^what (?:is the )?percent(?:age)?\b', p.question):
        return None
    if any(n.kind == 'percent' or n.start >= len(p.body) for n in amounts):
        return None
    if _has(r'\b(?:difference|average|taller|shorter|increase|decrease)\b', p.question):
        return None
    from .percentages_r02_a3 import _words
    money = [a for a in amounts if a.kind == 'money']
    if money:
        # An attached package-mass label is not another price.
        if any(a not in money and not re.match(r'(?:oz|kg|g)\b', p.text[a.end:])
               for a in amounts):
            return None
        if _has(r'\b(?:each|per|every|discount|tax)\b', p.body):
            return None
        counts = money
    else:
        counts = amounts
        if _has(r'\b(?:each|per|every|times|twice|ate|eat|eats|adds?|added|lost|'
                r'loses|sold|removed|more|less|fewer|difference|average)\b', p.body):
            return None
    if len(counts) < 2 or any(a.value < 0 for a in counts):
        return None
    labels, totals = [], []
    for i, amount in enumerate(counts):
        before = re.split(r'[,.;!?]|\band\b', p.text[:amount.start])[-1]
        after = re.split(r'[,.;!?]|\band\b', p.text[amount.end:])[0]
        if money:
            label = _words(before) - {'buy', 'buys', 'bought', 'cost', 'costs', 'price'}
        else:
            owner = re.search(r'\b([a-z]+)\s+(?:has |have |had )?'
                              r'(?:won|scored|made|makes|collected)\s*$', before)
            label = _words(after) | ({owner.group(1)} if owner else set())
        labels.append(label)
        if _has(r'\btotal\b', after) or _has(r'\btotal(?: of| is| was)?\s*$', before):
            totals.append(i)
    if len(totals) > 1:
        return None
    common = set.intersection(*labels)
    chosen = [i for i, label in enumerate(labels)
              if i not in totals and (label-common) & _words(p.question)]
    if not chosen:
        return None
    total = counts[totals[0]].value if totals else sum((a.value for a in counts), Fraction(0))
    selected = sum((counts[i].value for i in chosen), Fraction(0))
    if total <= 0 or selected > total:
        return None
    if totals and sum((a.value for i, a in enumerate(counts) if i not in totals), Fraction(0)) > total:
        return None
    if _has(r'\bnot\b|\bnon[- ]', p.question):
        selected = total-selected
    return _answer(100*selected/total, 'Selected count / total count x 100')
