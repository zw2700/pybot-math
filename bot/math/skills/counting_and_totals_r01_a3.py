"""Unit-checked counting schemas, including grouped and proportional totals.

Each reader accounts for every explicit quantity. Unsupported relationships
are left to other skills; numerical order alone never selects an operation.
"""
import re
from fractions import Fraction

from ..numbers import format_number
from ._counting_common import answer as _answer, products as _products
from ._counting_groups import container_relations
from .counting_and_totals_r00_a1 import _singular, _different_owner


def _has(pattern, text):
    return re.search(pattern, text) is not None


_STOP = set(('and or of in on at for to from with as by than before after during '
             'that which who while when are is was were will would can could '
             'has have had each per every a an the more extra additional '
             'then takes take fit fits holds hold contains contain makes make '
             'does do did he she they it his her their this these those '
             'used use reserved occupied dedicated weighing weighs weigh '
             'yields yield gets get left remaining').split())
_STOP.update(('total', 'altogether', 'combined', 'now'))


def _phrase(tail):
    """Read the count noun phrase, stopping before a relation or clause."""
    tail = re.sub(r'^\s*(?:of\s+)?(?:(?:his|her|their|the)\s+)?', '', tail)
    words = re.findall(r"[a-z]+|'s|[0-9.,;!?]", tail.lstrip(' -'))
    phrase = []
    for word in words:
        if word in _STOP or not word.isalpha() or (phrase and word.endswith('ing')):
            break
        phrase.append(_singular(word))
        if len(phrase) == 4:
            break
    return phrase


def _unit(p, n):
    tail = p.text.lower()[n.end:]
    compound = re.match(r'-([a-z]+)\b', tail)
    if compound:
        return _singular(compound.group(1))
    words = _phrase(tail)
    return words[-1] if words else ''


def _asked(p):
    match = re.match(r'how (?:many|much)\s+(.+)', p.question)
    tail = re.sub(r'^(?:more|additional|extra)\s+', '', match.group(1)) if match else ''
    words = _phrase(tail)
    return words[-1] if words else ''


def _proportion(p):
    """An observed input/output pair scaled to another amount of either unit."""
    # A daily amount and consecutive durations form a schedule, not an
    # observed input/output pair (hours per day is not hours per month).
    if _has(r'\b(?:each|every|per|a) day\b', p.body):
        return None
    if _has(r'\bsame (?:size|job|work)\b', p.text.lower()) and _has(r'how long', p.question):
        return None
    ns = p.numbers
    if len(ns) != 3 or any(n.kind != 'number' for n in ns):
        return None
    units = [_unit(p, n) for n in ns]
    a, b, c = ns
    # The final amount must be part of an explicit new scenario/question.
    if c.start < len(p.body) and not _has(r'\bif\b', p.body[b.end:c.start]):
        return None
    if not units[0] or not units[1] or units[0] == units[1]:
        return None
    if _has(r'\b(?:more|less|fewer|left|remaining|half|twice|double|percent|each)\b', p.body[:c.start]):
        return None
    if _has(r'\b(?:lost|loses?|removed|sold|leaves?|gave|gives?|away|used|uses)\b', p.body):
        return None
    if not _has(r'\b(?:in|with|for|takes?|fit|fits|make|makes)\b', p.body[a.end:b.start+1]):
        return None
    if units[2] == units[1]:
        numerator, denominator, result_unit = a.value, b.value, units[0]
    elif units[2] == units[0]:
        numerator, denominator, result_unit = b.value, a.value, units[1]
    else:
        return None
    asked = _asked(p)
    if asked != result_unit and not (p.question.startswith('how long') and result_unit in
                                    ('minute', 'hour', 'day', 'second')):
        return None
    if denominator <= 0:
        return None
    value = c.value * numerator / denominator
    if _has(r'\bmore\b', p.question):
        # The observed starting group is already present, so only add the gap.
        if not _has(r'\b(?:total|need)\b', p.question):
            return None
        value -= numerator
    return _answer(value, '{} x {} / {}{}'.format(
        format_number(c.value), format_number(numerator), format_number(denominator),
        ' - ' + format_number(numerator) if _has(r'\bmore\b', p.question) else ''))


def _grouped_total(p):
    """Reduce explicit per-group relations, then sum disjoint output counts."""
    ns = p.numbers
    text = p.text.lower()
    if _has(r'\bdozen\b', text):
        return None  # A dozen is a conversion, not an individual count.
    if not 2 <= len(ns) <= 5 or any(n.kind != 'number' for n in ns):
        return None
    if _has(r'\b(?:more|less|fewer|than|left|remain|remaining|except|not|lost|loses|sold|'
            r'half|twice|double|average|percent|cost|costs|price)\b', text):
        return None
    if any(0 < n.value < 1 and re.match(r'\s+of\b', text[n.end:]) for n in ns):
        return None
    if _has(r'\bto (?:make|produce|prepare|bake)\b', p.body):
        return None  # Recipe input/output proportions are not loose addends.
    if _has(r'\b(?:in|for|during|over) (?:a|an|one|the entire|the whole) '
            r'(?:second|minute|hour|day|week|month|year)\b', p.question):
        return None  # An implicit duration still needs a schedule relation.
    units = [_unit(p, n) for n in ns]
    for i in range(len(ns)-1):
        if (not text[ns[i].end:ns[i+1].start].strip()
                and re.match(r'-[a-z]+\b', text[ns[i+1].end:])):
            units[i] = units[i+1]
    if not all(units):
        return None
    def head(tail):
        words = _phrase(tail)
        return words[-1] if words else ''

    relations = container_relations(p, head, units)
    if relations is None:
        return None
    parents, references = relations
    if not parents or references:
        return None
    consumed = set(parents.values())
    roots = [i for i in range(len(ns)) if i not in consumed]
    asked = _asked(p)
    if not roots or not asked:
        return None
    if any(units[i] != asked for i in roots):
        return None
    terms = _products([n.value for n in ns],
                      {b: (a, Fraction(1)) for b, a in parents.items()},
                      order='flat')
    if terms is None:
        return None
    return _answer(sum((v for _, v, _ in terms), Fraction(0)),
                   ' + '.join(e for _, _, e in terms))


_EVENT = re.compile(r'\b(has|have|had|makes?|made|ordered|bought|buys?|found|received|'
                    r'got|collected|lost|loses|ate|eats?|used|uses|gave|gives?|'
                    r'steals?|stole|sold|sells?)\b')
_REMOVE = set('lost loses ate eat eats used uses gave gives steal steals stole sold sell sells'.split())


def _inventory(p):
    """One starting inventory, additions/removals, optionally items per survivor."""
    ns = p.numbers
    text = p.text.lower()
    # A proper fraction followed by a possessive/of-relation is a share of
    # inventory, rather than a literal count to add or subtract.
    if any(0 < n.value < 1 and re.match(r'\s+(?:of|his|her|their|the)\b', text[n.end:])
           for n in ns):
        return None
    if not 2 <= len(ns) <= 5 or any(n.start >= len(p.body) or n.kind != 'number' for n in ns):
        return None
    if _different_owner(p) or _has(r'\b(?:than|fewer|half|twice|double|average|percent|per|every)\b', text):
        return None
    rate = None
    counts = list(ns)
    each = re.search(r'\bon each of (?:the|his|her|their) remaining\b', p.body)
    if each:
        rate = ns[-1]
        counts = counts[:-1]
        if not ns[-2].end < rate.start < each.start() or _asked(p) != _unit(p, rate):
            return None
    elif _has(r'\beach\b', text):
        return None
    elif not _has(r'\b(?:left|now|remaining)\b', p.question):
        return None
    unit = _unit(p, counts[0])
    if not unit or (rate is None and _asked(p) != unit):
        return None
    total = Fraction(0)
    signs, expression = [], []
    for i, n in enumerate(counts):
        # A missing repeated noun is allowed after an explicit inventory verb.
        u = _unit(p, n)
        if u and u != unit:
            return None
        start = counts[i-1].end if i else 0
        verbs = list(_EVENT.finditer(text[start:n.start]))
        if not verbs:
            return None
        verb = verbs[-1].group()
        if i == 0 and verb not in ('has', 'have', 'had', 'made', 'makes', 'got'):
            return None
        sign = -1 if verb in _REMOVE else 1
        signs.append(sign)
        expression.append((' - ' if sign < 0 else ' + ') + format_number(n.value))
        total += sign*n.value
    if not any(s < 0 for s in signs):
        return None
    if rate:
        total *= rate.value
    working = ''.join(expression).lstrip(' +')
    if rate:
        working = '(' + working + ') x ' + format_number(rate.value)
    return _answer(total, working)


def _allocated_remainder(p):
    ns = p.numbers
    text = p.text.lower()
    if not 3 <= len(ns) <= 5 or any(n.start >= len(p.body) for n in ns):
        return None
    if not _has(r'\b(?:rest|remaining|remainder)\b', text) or not _has(r'\btotal\b', p.body[:ns[0].end]):
        return None
    units = [_unit(p, n) for n in ns]
    if not all(u == units[0] for u in units) or _asked(p) != units[0]:
        return None
    if _has(r'\b(?:each|every|per|more|less|than|half|twice|percent)\b', text):
        return None
    for n in ns[1:]:
        tail = text[n.end:]
        if not re.match(r'\s+\w+\s+(?:are|is|were|was|have been|has been)\s+'
                        r'(?:occupied|reserved|dedicated|used|allocated|set aside)\b', tail):
            return None
    return _answer(ns[0].value - sum((n.value for n in ns[1:]), Fraction(0)),
                   format_number(ns[0].value) + ' - (' +
                   ' + '.join(format_number(n.value) for n in ns[1:]) + ')')


def _dozens(p):
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 2 or not _has(r'\b(?:total|altogether|combined|all)\b', p.question):
        return None
    if _has(r'\b(?:each|per|than|more|less|left|lost|sold|half|gave|gives?|ate|eats?|'
            r'used|uses|away|removed|spent)\b', text):
        return None
    terms, units = [], []
    for n in ns:
        tail = text[n.end:]
        dozen = re.match(r'\s+dozen\s+', tail)
        if dozen:
            phrase = _phrase(tail[dozen.end():])
            terms.append(n.value * 12)
        else:
            phrase = _phrase(tail)
            terms.append(n.value)
        units.append(phrase[-1] if phrase else '')
    if not units[0] or units[0] != units[1] or _asked(p) != units[0] or not any(
            re.match(r'\s+dozen\b', text[n.end:]) for n in ns):
        return None
    return _answer(sum(terms, Fraction(0)), ' + '.join(map(format_number, terms)))


def _comparative_categories(p):
    """Two named categories share a count noun, one is a known difference."""
    ns = p.numbers
    if len(ns) != 2 or _has(r'\b(?:each|per|times|half|twice|average)\b', p.text.lower()):
        return None
    text = p.text.lower()
    for i, n in enumerate(ns):
        relation = re.match(r'\s+(more|fewer|less)\s+([a-z ]+?)\s+than\s+([a-z ]+?)[.,;]', text[n.end:])
        if not relation:
            continue
        direction, first, second = relation.groups()
        first, second = _phrase(first), _phrase(second)
        base_phrase = _phrase(text[ns[1-i].end:])
        if (len(first) < 2 or len(second) < 2 or first[-1] != second[-1]
                or base_phrase != second or _asked(p) != first[-1]):
            return None
        # A bare shared noun or an explicit combined total asks for both.
        asked_phrase = _phrase(re.sub(r'^how many\s+', '', p.question))
        if asked_phrase != [first[-1]]:
            return None
        base = ns[1-i].value
        delta = n.value if direction == 'more' else -n.value
        if base + delta < 0:
            return None
        return _answer(2*base+delta, '{} + ({} {} {})'.format(
            format_number(base), format_number(base), '+' if delta >= 0 else '-',
            format_number(abs(delta))))
    return None


def _named_wins(p):
    """A combined event count and a difference between two named participants."""
    ns = p.numbers
    if len(ns) != 2 or not _has(r'\bplayed\b', p.body):
        return None
    relation = re.search(r"\b([a-z]+) won\s*$", p.body[:ns[1].start])
    other = re.match(r'\s+(more|fewer)\s+([a-z]+)\s+than\s+([a-z]+)\b', p.body[ns[1].end:])
    query = re.match(r'how many\s+([a-z]+)\s+did\s+([a-z]+)\s+win\b', p.question)
    if not relation or not other or not query:
        return None
    direction, unit, second = other.groups()
    first = relation.group(1)
    if query.group(1) != unit or _unit(p, ns[0]) != _singular(unit):
        return None
    asked = query.group(2)
    if asked not in (first, second) or ns[0].value < ns[1].value:
        return None
    if _has(r'\b(?:tie|ties|draw|draws|other|third)\b', p.body):
        return None
    sign = (1 if direction == 'more' else -1) * (1 if asked == first else -1)
    return _answer((ns[0].value+sign*ns[1].value)/2, '({} {} {}) / 2'.format(
        format_number(ns[0].value), '+' if sign > 0 else '-', format_number(ns[1].value)))


def _exception_group(p):
    """Uniform containers, except for a stated number with another content."""
    ns = p.numbers
    if len(ns) != 4 or not _has(r'\bexcept for\b', p.body):
        return None
    a, exceptions, b, groups = ns
    text = p.text.lower()
    if not re.search(r'except for\s*$', text[a.end:exceptions.start]):
        return None
    relation = re.fullmatch(r'\s+([a-z]+)\s+that\s+(?:has|have|holds?|contains?)\s+',
                            text[exceptions.end:b.start])
    if not relation or _unit(p, groups) != _singular(relation.group(1)):
        return None
    if not _unit(p, a) or _unit(p, a) != _unit(p, b) or _asked(p) != _unit(p, a):
        return None
    if not _has(r'\bthere (?:are|were)\b', text[b.end:groups.start]):
        return None
    if groups.value < exceptions.value:
        return None
    value = (groups.value-exceptions.value)*a.value + exceptions.value*b.value
    return _answer(value, '({} - {}) x {} + {} x {}'.format(
        *map(format_number, (groups.value, exceptions.value, a.value, exceptions.value, b.value))))


def _expanded_total(p):
    """An increase to one component, with old components and a new combined total."""
    ns = p.numbers
    if len(ns) != 3 or not _has(r'\b(?:expanded|increased|enlarged)\b', p.question):
        return None
    if not _has(r'\bby\b', p.question) or not _has(r'\bnew total\b', p.body[ns[1].end:ns[2].start]):
        return None
    text = p.text.lower()
    # Require exactly the same explicit measurement unit on all three values.
    tails = [text[n.end:] for n in ns]
    unit = re.match(r'\s+([a-z]+(?:\.\s*[a-z]+\.)?)', tails[0])
    if not unit or not all(re.match(r'\s+' + re.escape(unit.group(1)) + r'(?:\s|[.,])', t)
                           for t in tails[1:]):
        return None
    if _has(r'\b(?:each|per|twice|half|percent|than|fewer|less|more)\b',
            p.body.replace('each other', '')):
        return None
    a, b, total = (n.value for n in ns)
    return _answer(total-a-b, '{} - ({} + {})'.format(*map(format_number, (total, a, b))))


def solve(problem):
    if any(n.kind != 'number' for n in problem.numbers):
        return None
    for rule in (_proportion, _grouped_total, _inventory, _allocated_remainder, _dozens,
                 _comparative_categories, _named_wins, _exception_group, _expanded_total):
        result = rule(problem)
        if result is not None:
            return result
    return None
