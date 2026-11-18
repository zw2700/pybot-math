"""Shared readers and exact arithmetic for the rate skills.

Readers describe units and relations only. Solvers remain responsible for
explaining every quantity and for rejecting unsupported changes or schedules.
"""
import re
from fractions import Fraction
from itertools import product


def has(pattern, text):
    return re.search(pattern, text) is not None


def sentence(text, number):
    left = list(re.finditer(r'[.!?;](?:\s|$)', text[:number.start]))
    right = re.search(r'[.!?;](?:\s|$)', text[number.end:])
    return text[left[-1].end() if left else 0:
                number.end + right.start() if right else len(text)]


def noun_head(text, stops, normal, measures, limit=4, skip=(), possessives=True):
    """Read a bounded noun phrase, stopping at punctuation or a clause word.

    Physical measurements end the phrase immediately: in "liters of paint",
    the unit is liters. Other noun phrases use their final word, so new
    commodities and modifiers need no object vocabulary.
    """
    token = r"[a-z]+(?:'[a-z]+)?|[^a-z\s-]" if possessives else r'[a-z]+|[^a-z\s-]'
    kept = []
    for word in re.findall(token, text.lstrip(' -')):
        if word in skip and not kept:
            continue
        if word in stops or word in {'he', 'she', 'it', 'they', 'we', 'you', 'i'} or not word[0].isalpha():
            break
        word = normal(word)
        kept.append(word)
        if word in measures or len(kept) == limit:
            break
    return kept[-1] if kept else ''


def per_unit(suffix, head, stops, indefinite_units=None):
    """Read a local amount per noun phrase, without crossing a predicate.

    Some solvers accept indefinite articles only for measured units; this
    prevents an incidental purpose such as "for a course" becoming a rate.
    """
    match = re.search(r'(\b(?:per|each|every|an?)\s+|/)([a-z]+)\b', suffix)
    if not match or any(w in stops - {'of', 'in', 'for', 'it'}
                        for w in re.findall(r'[a-z]+', suffix[:match.start()])):
        return ''
    unit = head(suffix[match.start(2):])
    if not unit or unit in stops or unit in {'one', 'other', 'once'}:
        return ''
    if (match.group(1).strip() in {'a', 'an'} and indefinite_units is not None
            and unit not in indefinite_units):
        return ''
    return unit


def group_unit(text, numbers, index, units, head):
    """In "N groups of M items", M is a per-group amount.

    The complete text between the adjacent quantities must be the grouping
    noun phrase and "of"; intervening clauses or quantities are not inferred.
    """
    if not index or not units[index] or units[index] == units[index-1]:
        return ''
    middle = text[numbers[index-1].end:numbers[index].start]
    match = re.fullmatch(r'\s+([a-z]+(?:[ -]+[a-z]+){0,3})\s+of\s+', middle)
    if match:
        words = re.split(r'[ -]+', match.group(1))
        if (all(head(word) for word in words)
                and head(words[-1]) == head(match.group(1)) == units[index-1]):
            return units[index-1]
    return ''


def each_subject(prefix, normal, stops, known_units=()):
    """Read the subject of a local "each noun [auxiliary] verb N" clause.

    A known unit anchors unfamiliar verbs. Otherwise require an inflected
    predicate, a modal, or a copula. Relative clauses, negation, conjunctions,
    and intervening quantities cannot be swallowed as noun modifiers.
    """
    markers = list(re.finditer(r'\b(?:each|every)\s+', prefix))
    if not markers:
        return ''
    clause = prefix[markers[-1].end():].strip()
    noun = r'[a-z]+(?:[ -]+[a-z]+){0,3}?'
    nominal = r'(' + noun + r')(?:\s+of\s+' + noun + r')?'
    # A fronted "for every X [relative clause], S verb N" is an explicit
    # per-X relation. Neither clause may hide another measured quantity.
    if re.search(r'\bfor\s*$', prefix[:markers[-1].start()]):
        front = re.fullmatch(nominal + r'(?:\s+(?:that|which|who)\s+[a-z ]+)?'
                             r',\s+[a-z]+\s+[a-z]+\s*', clause)
        if front and not re.search(r'\b(?:not|never|no)\b', clause):
            words = re.split(r'[ -]+', front.group(1))
            if not any(w in stops for w in words):
                return normal(words[-1])
    # A passive or composition describes the amount per subject just as
    # an active verb does; the participle is independent of the object.
    passive = re.fullmatch(nominal + r'\s+(?:(?:can|will|must)\s+be|is|are|was|were)'
                           r'\s+[a-z]+\s+(?:into|with|of|up of)\s*', clause)
    if passive:
        words = re.split(r'[ -]+', passive.group(1))
        return normal(words[-1]) if not any(w in stops for w in words) else ''
    # "process each form in N minutes" expresses time per form.
    task = re.fullmatch(nominal + r'\s+in\s*', clause)
    if task and markers[-1].start() and re.search(r'[a-z]+\s+$', prefix[:markers[-1].start()]):
        words = re.split(r'[ -]+', task.group(1))
        unit = normal(words[-1])
        if (len(words) == 1 or unit in known_units) and not any(w in stops for w in words):
            return unit
    match = re.fullmatch(
        nominal + r'\s+'
        r'(?:(can|will|must|would|should|to)\s+)?'
        r'([a-z]+)(?:\s+(?:him|her|them|it))?'
        r'(?:\s+(?:about|approximately|roughly|exactly|up to))?', clause)
    if not match:
        return ''
    subject, modal, verb = match.groups()
    words = re.split(r'[ -]+', subject)
    if any(w in stops for w in words):
        return ''
    # These words introduce another relation, rather than a direct quantity.
    if verb in {'not', 'never', 'no', 'only', 'also', 'than', 'and', 'or',
                'with', 'without', 'of', 'to', 'for', 'per', 'in', 'on', 'at'}:
        return ''
    unit = normal(words[-1])
    if (unit in known_units or modal or verb.endswith(('s', 'ed'))
            or verb in {'has', 'had', 'have', 'is', 'are', 'was', 'were', 'ate', 'took'}):
        return unit
    return ''


def dimensional_products(factors, target):
    """Yield exact products/quotients with the requested unit powers.

    Each factor is (value, iterable of (unit, power)). Every factor is used
    exactly once. Callers apply their semantic restrictions on reciprocals
    and require a unique interpretation before returning an answer.
    """
    target = dict(target)
    factors = [(amount, tuple(dimensions)) for amount, dimensions in factors]
    for signs in product((1, -1), repeat=len(factors)):
        value = Fraction(1)
        powers = {}
        for (amount, dimensions), sign in zip(factors, signs):
            if sign < 0 and not amount:
                break
            value = value * amount if sign > 0 else value / amount
            for unit, power in dimensions:
                powers[unit] = powers.get(unit, 0) + sign * power
        else:
            if {u: p for u, p in powers.items() if p} == target:
                yield value, signs


def whole_count(value, question):
    """Round a final discrete capacity only when the question fixes direction."""
    if re.search(r'\b(?:need(?:s|ed)?|required|necessary|should|must|order)\b', question):
        return Fraction(-(-value.numerator // value.denominator))
    if (re.search(r'\b(?:can|could)\b', question)
            and re.search(r'\b(?:make|produce|fit|fill|filled|buy|wrap)\b', question)):
        return Fraction(value.numerator // value.denominator)
    return value
