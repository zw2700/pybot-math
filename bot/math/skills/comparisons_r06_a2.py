"""Explicit comparison paraphrases and small compositions of exact amounts.

The affine reader owns equation solving. These adapters resolve local grammar
and recognize a transaction, activity, or period only with explicit operands.
Every numeric token must be accounted for before an adapter returns an answer.
"""
import re
from fractions import Fraction

from ..numbers import read_numbers
from ..problem import ASK
from .comparisons_r03_a4 import _singular, _category_mentions, _UNIT, _UNITS
from .comparisons_r04_a3 import _linear
from .comparisons_r01_a2 import _names
from .comparisons_r05_a6 import (
    _normalise, _read, _NUMBER, _RAW_FACTOR,
    _tokens, _ids, _v, _factor, _FACTOR,
)


def _answer(value, working):
    return (value, working) if value >= 0 else None


def _measured_answer(value, source, query, working):
    requested = re.search(r'\b(?:how many|how much|in) (' + _UNIT + r')\b', query)
    if requested:
        source, dest = _singular(source), _singular(requested.group(1))
        if _UNITS[source][0] != _UNITS[dest][0]:
            return None
        value *= _UNITS[source][1]/_UNITS[dest][1]
    return _answer(value, working)


def _adapt(text):
    """Expand equivalent comparison syntax without dropping any quantities."""
    text = _normalise(text)
    text = re.sub(r'(?<=[a-z])-(?=[a-z])', ' ', text, flags=re.I)
    text = re.sub(r'\b(younger|older) than ([^.;,]+?) by (' + _NUMBER + r') years?\b',
                  r'\3 years \1 than \2', text, flags=re.I)
    text = re.sub(r'\bthis year ([A-Z][a-z]+) will be\b', r'\1 is', text, flags=re.I)
    text = re.sub(r"\bwhat will be (.+?)'s age\b", r'How old will \1 be', text, flags=re.I)
    text = re.sub(r'\bas (huge|far|large|big) as\b', 'as long as', text, flags=re.I)
    text = re.sub(r'\b(more|less|fewer) (pounds?|ounces?|feet|inches|grams?|kilograms?) than\b',
                  r'\2 \1 than', text, flags=re.I)
    # "Triple the chair" is an amount comparison with an omitted measure.
    text = re.sub(r'\b(' + _RAW_FACTOR + r') the (?!number\b|amount\b|age\b|weight\b|height\b|length\b|cost\b|price\b)([a-z]+(?: [a-z]+)?)(?=[.;,])',
                  r'\1 as much as the \2', text, flags=re.I)
    text = re.sub(r'\b(' + _RAW_FACTOR + r') (?:the )?(?:number|amount) of ([a-z]+(?: [a-z]+)?) as\b',
                  r'\1 as many \2 as', text, flags=re.I)
    # A possessive business/item label must remain attached to its owner.
    text = re.sub(r"\b([A-Z][a-z]+)'s ([A-Z][a-z]+)\b",
                  lambda m: m.group(1) + "'s " + m.group(2).lower(), text)
    # The noun before "that" is a shared measured object, not an owner.
    text = re.sub(r'\b(' + _RAW_FACTOR + r') (?:the )?number of [a-z]+ that\s+',
                  r'\1 as much as ', text, flags=re.I)
    text = re.sub(r'\b(' + _RAW_FACTOR + r') the ([a-z]+) that ([A-Z][a-z]+)\b',
                  r'\1 as many \2 as \3', text)
    text = re.sub(r'\b(' + _RAW_FACTOR + r') the number of ([a-z]+) than\b',
                  r'\1 as many \2 as', text, flags=re.I)
    text = re.sub(r"\b([A-Z][a-z]+)'s (Grandmother|Grandfather|Mother|Father|Sister|Brother)\b",
                  lambda m: m.group(1) + "'s " + m.group(2).lower(), text)
    text = re.sub(r', who is (?:a|an) [a-z]+,', '', text, flags=re.I)
    text = re.sub(r'\b([A-Z][a-z]+) is [^.;]+? and his weight is\b',
                  lambda m: m.group() if read_numbers(m.group()) else m.group(1)+' weighs', text)
    text = re.sub(r'\b([A-Z][a-z]+) is [^.;]+? where she discovers that she is\b',
                  lambda m: m.group() if read_numbers(m.group()) else m.group(1)+' is', text)
    text = re.sub(r'\bthe two siblings\b', 'both', text, flags=re.I)
    text = re.sub(r'\b[Bb]ought\b', 'bought', text)
    text = re.sub(r'\bas costly as\b', 'as much as', text, flags=re.I)
    text = re.sub(r'\bhas some [a-z]+,\s*(' + _NUMBER + r' [a-z]+) and some [a-z]+',
                  r'has \1', text, flags=re.I)
    text = re.sub(r'\b([A-Z][a-z]+) walked (' + _NUMBER + r' [a-z]+), which was\b',
                  r'\1 had \2. \1 had', text)
    text = re.sub(r'\bwalked\b', 'had', text, flags=re.I)
    owners = _names(text)
    if len(owners) == 1:
        # These descendants are distinct people, including the son's child.
        possessor = r"(?:his|her|" + re.escape(owners[0]) + r"'s)"
        for kin in ('son', 'daughter', 'grandson', 'granddaughter'):
            text = re.sub(r'\b' + possessor + ' ' + kin + r'\b',
                          'Family' + kin, text, flags=re.I)
    # A size comparison between possessions compares the named owners' amounts.
    text = re.sub(r"\b([A-Z][a-z]+)'s (?:birthday )?party\b", r'\1', text)
    # Work experience grows at the same unit rate as age.
    if re.search(r'\byears? of experience\b', text, re.I):
        text = re.sub(r'\bas much experience as\b', 'as old as', text, flags=re.I)
        text = re.sub(r'\bhow many years of experience does (.+?) have now\b',
                      r'How old is \1 now', text, flags=re.I)
        text = re.sub(r'\bNow (he|she)\b', r'\1 now', text, flags=re.I)
    return text


def _ordinal_entities(p):
    """First/second/etc. explicitly enumerate entities, not numeric amounts."""
    text = _adapt(p.text)
    mentions = list(re.finditer(r'\b(first|second|third) ([a-z]+)\b', text, re.I))
    nouns = {m.group(2).lower() for m in mentions}
    if len(nouns) != 1:
        return None
    noun = next(iter(nouns))
    ordinals = sorted({m.group(1).lower() for m in mentions})
    if len(ordinals) < 2:
        return None
    for ordinal in ordinals:
        label = 'Entity' + {'first': 'alpha', 'second': 'beta', 'third': 'gamma'}[ordinal]
        text = re.sub(r'\b' + ordinal + ' ' + re.escape(noun) + r'\b', label, text, flags=re.I)
    # Only an exact count of the enumerated entities is a removable label.
    plural = noun[:-1] + 'ies' if noun.endswith('y') else noun + 's'
    pat = r'\b(' + _NUMBER + r') ((?:old |different )?' + re.escape(plural) + r')\b'
    def group(m):
        return 'the ' + m.group(2) if read_numbers(m.group(1))[0].value == len(ordinals) else m.group()
    text = re.sub(pat, group, text, flags=re.I)
    # A qualitative introduction can describe a different activity; it provides
    # no distance constraint and should not turn "spent" into a transaction.
    intro = re.match(r'[^.;]+[.;]\s*', text)
    if intro and not read_numbers(intro.group()) and not re.search(r'\bEntity[a-z]+\b', intro.group()):
        text = text[intro.end():]
    text = re.sub(r'\bwalked\b', 'had', text, flags=re.I)
    return _read(text)


_ACTIONS = {
    'play': 'play', 'played': 'play', 'plays': 'play',
    'run': 'run', 'ran': 'run', 'runs': 'run',
    'practice': 'practice', 'practiced': 'practice', 'practices': 'practice',
    'read': 'read', 'reads': 'read', 'work': 'work', 'worked': 'work',
    'study': 'study', 'studied': 'study', 'mow': 'mow', 'mowed': 'mow',
    'fertilize': 'fertilize', 'fertilized': 'fertilize',
}


def _activity_key(text):
    actions = list(re.finditer(r'\b(?:'+'|'.join(_ACTIONS)+r')\b', text))
    if len(actions) != 1:
        return None
    action = actions[0]
    tail = re.sub(r'\bq\d+\b', '', text[action.end():])
    tail = re.sub(r'\b(?:last|this|next) (?:day|week|month|year)\b', '', tail)
    stops = set('on in for at of to the a an and before after hour hours minute minutes'.split())
    objects = [_singular(w) for w in re.findall(r'[a-z]+', tail) if w not in stops]
    if len(objects) > 3:
        return None
    return (_ACTIONS[action.group()], tuple(objects))


def _activities(p):
    """Solve durations attached to activities rather than to their one actor.

    An anchor can precede or follow the comparisons, so both forward and
    inverse chains use exactly the same equations.
    """
    if len(_names(p.text)) > 1:
        return None
    text = _tokens(p)
    ask = list(ASK.finditer(text))[-1]
    body, query = text[:ask.start()], text[ask.start():]
    if re.search(r'\b(?:per|each|every|less|more|fewer|ago|lost)\b', body):
        return None
    equations, nodes, used, unit = [], set(), set(), None
    for clause in re.split(r'[.;]|,\s*(?:and\s+)?', body):
        relation = re.search(r'\b(' + _FACTOR + r') as long as\b', clause)
        if relation:
            left = _activity_key(clause[:relation.start()])
            right = _activity_key(clause[relation.end():])
            if not left or not right or left == right:
                return None
            k = _factor(relation.group(1), p)
            if k <= 0 or _ids(clause) != _ids(relation.group()):
                return None
            nodes.update((left, right))
            equations.append(({left: Fraction(1), right: -k}, Fraction(0)))
            used.update(_ids(relation.group()))
        elif _ids(clause):
            duration = re.search(r'\b(q\d+) (hours?|minutes?)\b', clause)
            if not duration or _ids(clause) != _ids(duration.group()):
                return None
            key = _activity_key(clause[:duration.start()]+clause[duration.end():])
            if not key:
                return None
            source = _singular(duration.group(2))
            unit = unit or source
            amount = _v(duration.group(1), p)*_UNITS[source][1]/_UNITS[unit][1]
            equations.append(({key: Fraction(1)}, amount))
            nodes.add(key)
            used.update(_ids(duration.group()))
        elif re.search(r'\b' + _FACTOR + r'\b', clause):
            return None
    if used != set(range(len(p.numbers))) or not unit:
        return None
    state = _linear(equations, nodes)
    if not state:
        return None
    key = _activity_key(query)
    if key in state:
        result = state[key]
    elif re.search(r'\b(?:total|combined|both)\b', query):
        result = sum(state.values(), Fraction(0))
    else:
        return None
    return _measured_answer(result, unit, query, 'Solve the duration comparisons between the named activities.')


def _period_amounts(p):
    """Direct amounts and comparisons between explicitly named days/meals."""
    periods = r'(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|breakfast|lunch|dinner)'
    text = _tokens(p)
    ask = list(ASK.finditer(text))[-1]
    body, query = text[:ask.start()], text[ask.start():]
    state, used, unit, previous, predicted = {}, set(), None, None, None
    for clause in re.split(r'[.;]', body):
        dates = re.findall(r'\b' + periods + r'\b', clause)
        quantities = _ids(clause)
        relation = re.search(r'\b(' + _FACTOR + r') (?:as (?:many|much)(?: [a-z]+){0,3}|the amount of [a-z]+)\b', clause)
        if relation:
            if len(dates) == 1 and previous:
                source, target = previous, dates[0]
            elif len(dates) == 2:
                # Either "on Saturday ... on Friday" or the factor before
                # "on Saturday as ... on Friday" gives the target first.
                target, source = dates
            else:
                return None
            if source not in state:
                # An explicitly dated breakfast/lunch/dinner partition gives
                # the source day's total before predicting another day.
                dated = re.search(r'\bduring (?:that|the) (' + periods + r')\b', body)
                if not dated or dated.group(1) != source or set(state) != {'breakfast', 'lunch', 'dinner'}:
                    return None
                state[source] = sum(state.values(), Fraction(0))
            if target in state or quantities != _ids(relation.group()):
                return None
            state[target] = state[source]*_factor(relation.group(1), p)
            used.update(quantities)
            previous = predicted = target
        elif quantities:
            anchor = re.search(r'\b(q\d+) ([a-z]+(?: [a-z]+)?)(?= for\b|[,.;]|$)', clause.strip())
            if len(dates) != 1 or len(quantities) != 1 or not anchor:
                return None
            noun = anchor.group(2)
            if unit is not None and noun != unit:
                return None
            unit = noun
            if dates[0] in state:
                return None
            state[dates[0]] = _v(anchor.group(1), p)
            used.update(quantities)
            previous = dates[0]
    if used != set(range(len(p.numbers))) or len(state) < 2 or not unit:
        return None
    if not {_singular(w) for w in unit.split()} & {_singular(w) for w in query.split()}:
        return None
    requested = re.findall(r'\b' + periods + r'\b', query)
    if any(key not in state for key in requested):
        return None
    if len(requested) == 2 and re.search(r'\b(?:more|less|fewer|difference)\b', query):
        return abs(state[requested[0]]-state[requested[1]]), 'Compare the amounts for the two requested periods.'
    if len(requested) == 1:
        return state[requested[0]], 'Apply the stated comparison to the earlier period.'
    if not requested and predicted and re.search(r'\bpredict\b', query):
        return state[predicted], 'Sum the source periods and apply the prediction multiplier.'
    return None


def _changed_inventory(p):
    """Solve a comparison first, then subtract an explicit loss of that unit."""
    if not re.search(r'\b(?:left|remaining)\b', p.question):
        return None
    text = p.text
    loss = re.search(r'\bbut (?:he|she|they) (?:lost|gave away) (' + _NUMBER + r') of them\b', text, re.I)
    if not loss:
        return None
    amount = read_numbers(loss.group(1))[0].value
    text = text[:loss.start()] + text[loss.end():]
    text = re.sub(r'\b(?:are )?left with\b', 'does', text, flags=re.I)
    text = re.sub(r"\bthe number of ([A-Z][a-z]+)'s ([A-Z][a-z]+)\b",
                  lambda m: 'as many ' + m.group(2).lower() + ' as ' + m.group(1), text)
    result = _read(_adapt(text))
    return _answer(result[0]-amount, result[1]+' Subtract the explicit loss.') if result else None


def _used_remainder(p):
    """A compared ingredient is based on the used part, not the purchased part."""
    text = _tokens(p)
    anchor = re.search(r'\b(?:buys?|bought|has) (q\d+) (pounds?|grams?|kilograms?|ounces?) of ([a-z]+)\b', text)
    loss = re.search(r'\buses? all but (q\d+) (pounds?|grams?|kilograms?|ounces?)\b', text)
    ratio = re.search(r'\buses? (' + _FACTOR + r') as many (pounds?|grams?|kilograms?|ounces?) of ([a-z]+) as ([a-z]+)\b', text)
    if not all((anchor, loss, ratio)):
        return None
    if anchor.group(3) != ratio.group(4) or len({_singular(anchor.group(2)), _singular(loss.group(2)), _singular(ratio.group(2))}) != 1:
        return None
    if ratio.group(3) not in p.question or _ids(anchor.group()+' '+loss.group()+' '+ratio.group()) != set(range(len(p.numbers))):
        return None
    return _measured_answer((_v(anchor.group(1), p)-_v(loss.group(1), p))*_factor(ratio.group(1), p),
                            anchor.group(2), p.question,
                            'Subtract the unused amount, then apply the ingredient comparison.')


def _outfit_product(p):
    """All pairwise combinations of two compared inventories."""
    if not re.search(r'\b(?:each|every) (?:unique )?combination\b', p.body):
        return None
    if not re.search(r'\b(?:outfits?|combinations?)\b', p.question):
        return None
    body = p.text[:len(p.body)]
    # The outfit definition is qualitative. Keep all numeric constraints.
    definition_clause = re.search(r'\band considers each [^.;]+', body, re.I)
    if definition_clause and read_numbers(definition_clause.group()):
        return None
    reduced = re.sub(r'\band considers each [^.;]+', '', body, flags=re.I)
    state = _read(_adapt(reduced) + ' How many are there in total?', True)
    if not state or len(state) != 2:
        return None
    definition = re.search(r'\bcombination of (.+?) to be (?:an?|one) outfit\b', body, re.I)
    if not definition:
        return None
    objects = {_singular(w.lower()) for w in re.findall(r'[a-z]+', definition.group(1), re.I)}
    if not all(_singular(category.split()[-1]) in objects for category in state):
        return None
    amounts = list(state.values())
    return amounts[0]*amounts[1], 'Multiply the two inventories to count all pairwise combinations.'


def _speed_comparison(p):
    """A speed ratio reverses a given time per distance."""
    text = _tokens(p)
    ratio = re.search(r'\b([a-z]+) runs? (' + _FACTOR + r') as fast as ([a-z]+)\b', text)
    base = re.search(r'\btakes ([a-z]+) (q\d+) minutes to run (?:a|one) mile\b', text)
    goal = re.search(r'\btake ([a-z]+) to (?:run )?(q\d+) miles\b', text)
    if not all((ratio, base, goal)) or ratio.group(3) != base.group(1) or ratio.group(1) != goal.group(1):
        return None
    if _ids(ratio.group()+' '+base.group()+' '+goal.group()) != set(range(len(p.numbers))):
        return None
    k = _factor(ratio.group(2), p)
    return _measured_answer(_v(base.group(2), p)*_v(goal.group(2), p)/k, 'minute', p.question,
                            'Divide the time per mile by the speed ratio, then multiply by the distance.') if k > 0 else None


def _category_paraphrases(p):
    """An actor can own several independent measured categories."""
    text = _adapt(p.text)
    activity = r'(?:students|those) who (?:wish|want) to go on (?:a|the) ([a-z]+(?: [a-z]+){0,2} trip)'
    text = re.sub(activity, r'\1 participants', text, flags=re.I)
    counted = r'(?:the )?number of ([a-z]+(?: [a-z]+){0,2}?) (?:[A-Z][a-z]+|he|she) (?:washed|cooked|picked|found)'
    category_mode = bool(re.search(counted, text, re.I)) or 'trip participants' in text
    if category_mode:
        text = re.sub(counted, r'the number of \1', text, flags=re.I)
        text = re.sub(r'(?:(?<=[.;])|^)\s*also,\s*', ' ', text, flags=re.I)
        # Owner verbs in anchors do not merge different objects into one amount.
        text = re.sub(r'\b[A-Z][a-z]+ (?:found|picked|cooked|washed) (?:a total of )?(' + _NUMBER + r') ([a-z]+(?: [a-z]+){0,2}?)(?=[,.;])',
                      r'There are \1 \2', text)
        text = text.lower()
    # With two compared categories, a direct purchase total is the group total.
    if re.search(r'\bas many [a-z]+ as [a-z]+\b', text, re.I):
        text = re.sub(r'\b[A-Z][a-z]+ buys (' + _NUMBER + r') ([a-z]+(?: [a-z]+)?) total\b',
                      r'There are \1 \2 in total', text)
    # An omitted reference is local to the immediately preceding category count.
    implicit = (r'\bthere (?:are|were) (' + _NUMBER + r') ([a-z]+(?: [a-z]+)?)[.;]\s*'
                r'there (?:are|were) (' + _RAW_FACTOR + r') as many ([a-z]+(?: [a-z]+)?)(?: in this [a-z]+)?[.;]')
    text = re.sub(implicit, r'There are \1 \2. There are \3 as many \4 as \2.', text, flags=re.I)
    return _read(text) if text != p.text else None


def _added_inventory(p):
    """An explicitly named owner adds items after an initial comparison."""
    addition = re.search(r'\b([A-Z][a-z]+) then adds (' + _NUMBER + r') more (?:pieces of )?([a-z]+) to (?:her|his) collection[.;]', p.text)
    if not addition:
        return None
    if not re.search(r'\b' + re.escape(addition.group(1).lower()) + r'\b', p.question):
        return None
    if addition.group(3).lower() not in p.body[:addition.start()]:
        return None
    text = p.text[:addition.start()] + p.text[addition.end():]
    result = _read(_adapt(text))
    return _answer(result[0]+read_numbers(addition.group(2))[0].value,
                   result[1]+' Add the new items to that owner.') if result else None


def _two_durations(p):
    """One explicit duration and an explicitly compared second duration."""
    text = _tokens(p)
    routine = re.search(r'\btakes (q\d+) (minutes?|hours?) to [^.;]+? and (' + _FACTOR + r') that long to\b', text)
    if routine and 'routine' in p.question and _ids(routine.group()) == set(range(len(p.numbers))):
        return _measured_answer(_v(routine.group(1), p)*(1+_factor(routine.group(3), p)),
                                routine.group(2), p.question,
                                'Add the durations of both parts of the routine.')
    base = re.search(r'\bin (q\d+) (minutes?|hours?)\b', text)
    comparison = re.search(r'\btakes (?:him|her|them) (' + _FACTOR + r') that long to ([a-z]+)\b', text)
    if not base or not comparison or not re.search(r'\bboth\b', p.question):
        return None
    if comparison.group(2) not in p.question or _ids(base.group()+' '+comparison.group()) != set(range(len(p.numbers))):
        return None
    return _measured_answer(_v(base.group(1), p)*(1+_factor(comparison.group(1), p)),
                            base.group(2), p.question,
                            'Add the original duration and the compared duration.')


def _group_query(p):
    """A cardinal count in a query can label an already enumerated group."""
    text = _adapt(p.text)
    ask = list(ASK.finditer(text))[-1]
    body, query = text[:ask.start()], text[ask.start():]
    label = re.search(r'\b(' + _NUMBER + r') (girls|boys|siblings|friends|people|ladies|men|women)\b', query, re.I)
    if not label or len(read_numbers(query)) != 1:
        return None
    state = _read(body + ' How many are there in total?', True)
    if not state or read_numbers(label.group(1))[0].value != len(state):
        return None
    query = query[:label.start()] + 'people' + query[label.end():]
    return _read(body+query)


def _relative_age_difference(p):
    """Absolute ages are unnecessary for a difference of connected ages."""
    if not re.search(r'\bhow much older in months\b|\bhow many (?:years|months) (?:older|younger)\b', p.question):
        return None
    text = _tokens(p)
    edges = list(re.finditer(r'\b([a-z]+) is (q\d+) (months?|years?) (older|younger) than ([a-z]+)\b', text))
    if not edges or len({_singular(m.group(3)) for m in edges}) != 1:
        return None
    used = set().union(*(_ids(m.group()) for m in edges))
    nodes = {m.group(i) for m in edges for i in (1, 5)}
    for i in set(range(len(p.numbers)))-used:
        n = p.numbers[i]
        if n.value != len(nodes) or not re.match(r'\s+(?:classmates|friends|people|siblings)\b', p.text[n.end:], re.I):
            return None
    offsets = {next(iter(nodes)): Fraction(0)}
    for _ in nodes:
        for m in edges:
            left, right = m.group(1), m.group(5)
            delta = _v(m.group(2), p)*(-1 if m.group(4) == 'younger' else 1)
            if right in offsets:
                if left in offsets and offsets[left] != offsets[right]+delta:
                    return None
                offsets[left] = offsets[right]+delta
            elif left in offsets:
                offsets[right] = offsets[left]-delta
    requested = [n for n in nodes if re.search(r'\b'+re.escape(n)+r'\b', p.question)]
    if len(requested) != 2 or not all(n in offsets for n in requested):
        return None
    value = abs(offsets[requested[0]]-offsets[requested[1]])
    if edges[0].group(3).startswith('year') and 'months' in p.question:
        value *= 12
    elif edges[0].group(3).startswith('month') and 'years' in p.question:
        value /= 12
    return value, 'Combine the signed age differences along the comparison chain.'


def _complement_query(p):
    if not re.search(r'\bnot [a-z]+\b', p.question):
        return None
    body = _adapt(p.text[:len(p.body)])
    state = _read(body+' How many are there in total?', True)
    if not state:
        return None
    excluded_text = re.search(r'\bnot ([a-z]+(?: [a-z]+)?)', p.question).group(1)
    excluded = _category_mentions(excluded_text, state)
    if len(excluded) != 1:
        return None
    return sum((v for k, v in state.items() if k != excluded[0]), Fraction(0)), 'Add all categories except the excluded category.'


def _paired_amounts(p):
    """An amount and a directly adjacent implicit multiple, requested together."""
    body_names = set(_names(p.text[:len(p.body)]))
    query_names = set(_names(p.text[len(p.body):])) - {'calculate', 'determine', 'find'}
    if query_names - body_names:
        return None
    two_years = (re.search(r'\blast year\b', p.body) and re.search(r'\bthe year before\b', p.body)
                 and re.search(r'\blast (' + _NUMBER + r') years\b', p.question))
    if two_years and read_numbers(two_years.group(1))[0].value != 2:
        return None
    if not two_years and not re.search(r'\b(?:total|combined|altogether|in total|in all)\b', p.question):
        return None
    text = _tokens(p)
    relation = re.search(r'\b(' + _FACTOR + r') (?:this many|that (?:many|number)|as many)(?: [a-z]+){0,3}?(?=[,.;]|$)', text)
    if not relation:
        return None
    remaining = set(range(len(p.numbers)))-_ids(relation.group())
    if re.search(r'\blast year\b', p.body) and re.search(r'\bthe year before\b', p.body):
        for i in list(remaining):
            n = p.numbers[i]
            if (n.value == 2 and n.start >= len(p.body) and
                    re.match(r'\s+years\b', p.text[n.end:], re.I)):
                remaining.remove(i)
    if len(remaining) != 1:
        return None
    i = next(iter(remaining))
    n = p.numbers[i]
    noun = re.match(r'\s+([a-z]+)', p.text[n.end:], re.I)
    if not noun or _singular(noun.group(1).lower()) not in {_singular(w) for w in re.findall(r'[a-z]+', p.question)}:
        return None
    # The relation may omit its unit, but it cannot silently change the unit.
    many_unit = re.search(r'\bas many ([a-z]+)', relation.group())
    if many_unit and many_unit.group(1) not in ('on', 'today', 'yesterday', 'the') and _singular(many_unit.group(1)) != _singular(noun.group(1).lower()):
        return None
    if n.start >= p.text.lower().find(relation.group(1)) and relation.group(1) in ('twice','thrice','double','triple'):
        return None
    if re.search(r'\b(?:lost|gave|left|remaining|per|each|every|price|cost|ago)\b', p.body):
        return None
    return p.values[i]*(1+_factor(relation.group(1), p)), 'Add the initial amount and its stated multiple.'


def _self_age(p):
    """Compare the same person's age at two explicitly shifted dates."""
    text = _tokens(p)
    future = re.search(r'\b(q\d+) years? from now,? ([a-z]+) will be (' + _FACTOR + r') as old as (?:he|she) was (q\d+) years? ago\b', text)
    if not future or _ids(future.group()) != set(range(len(p.numbers))):
        return None
    if not re.search(r'\b(?:now|currently)\b', p.question) or not p.question.startswith('how old'):
        return None
    k = _factor(future.group(3), p)
    if k <= 1:
        return None
    return (_v(future.group(1), p)+k*_v(future.group(4), p))/(k-1), 'Solve the comparison between the future and past ages.'


def _calendar_ages(p):
    """Two explicit calendar dates identify an age shift without today's date."""
    dates = list(re.finditer(r'\bIn (' + _NUMBER + r'),?\s*', p.text))
    if len(dates) != 2 or not re.search(r'\bhow old\b', p.question):
        return None
    start, end = [read_numbers(m.group(1))[0].value for m in dates]
    if not all(v.denominator == 1 and 1000 <= v <= 9999 for v in (start, end)):
        return None
    text = p.text
    for m in reversed(dates):
        text = text[:m.start()]+text[m.end():]
    result = _read(_adapt(text))
    return _answer(result[0]+end-start, result[1]+' Advance by the difference between the calendar years.') if result else None


def _group_ages(p):
    text = _tokens(p)
    count = re.search(r'\b([a-z]+) has (q\d+) (brothers|sisters|children)\b', text)
    age = re.search(r'\b(?:brothers|sisters|children) are all (q\d+) years? old\b', text)
    ratio = re.search(r'\b(' + _FACTOR + r") as old as the sum of (?:her|his) (?:brother|sister|child)(?:'s|ren's|s') ages", text)
    if not all((count, age, ratio)) or _ids(count.group()+' '+age.group()+' '+ratio.group()) != set(range(len(p.numbers))):
        return None
    if count.group(1) not in p.question:
        return None
    return _v(count.group(2), p)*_v(age.group(1), p)*_factor(ratio.group(1), p), 'Add the equal ages in the group, then apply the age ratio.'


def _geometry(p):
    text = _tokens(p)
    ratio = re.search(r'\b(' + _FACTOR + r') as long as it was wide\b', text)
    perimeter = re.search(r'\bperimeter of (?:the )?[a-z]+ was (q\d+) (feet|meters|inches|yards)\b', text)
    if 'rectangular' in p.body and ratio and perimeter:
        if _ids(ratio.group()+' '+perimeter.group()) != set(range(len(p.numbers))):
            return None
        k = _factor(ratio.group(1), p)
        if k <= 0 or not re.search(r'\b(?:length|width)\b', p.question):
            return None
        width = _v(perimeter.group(1), p)/(2*(1+k))
        return _measured_answer(width*(k if 'length' in p.question else 1), perimeter.group(2), p.question,
                                'Use twice the sum of length and width for the perimeter.')
    if not re.search(r'\bin a triangle with angles\b', text):
        return None
    known = re.search(r'\b([a-z]) is (q\d+) degrees\b', text)
    ratio = re.search(r'\b([a-z]) is (' + _FACTOR + r') as big as ([a-z])\b', text)
    if not known or not ratio or len({known.group(1), ratio.group(1), ratio.group(3)}) != 3:
        return None
    if _ids(known.group()+' '+ratio.group()) != set(range(len(p.numbers))):
        return None
    requested = re.search(r'\bangle of ([a-z])\b', p.question)
    if not requested or requested.group(1) not in (ratio.group(1), ratio.group(3)):
        return None
    k = _factor(ratio.group(2), p)
    if k <= 0 or not 0 < _v(known.group(2), p) < 180:
        return None
    base = (180-_v(known.group(2), p))/(1+k)
    return base*(k if requested.group(1) == ratio.group(1) else 1), 'The three interior angles sum to 180 degrees.'


def _pairwise_totals(p):
    """Two shared-item totals plus a price comparison form a small system."""
    text = _tokens(p)
    label = r'(?:the )?(?:pair of )?([a-z]+(?: [a-z]+)?)'
    sums = list(re.finditer(r'\b' + label + ' and ' + label + r' costs? (q\d+)\b', text))
    relation = re.search(r'\bthe ([a-z]+) costs? (' + _FACTOR + r') as much as the ([a-z]+)\b', text)
    if len(sums) != 2 or not relation:
        return None
    used = _ids(relation.group()) | set().union(*(_ids(m.group()) for m in sums))
    if used != set(range(len(p.numbers))):
        return None
    equations = []
    nodes = set()
    for m in sums:
        a, b = m.group(1), m.group(2)
        if a == b:
            return None
        nodes.update((a, b))
        equations.append(({a: Fraction(1), b: Fraction(1)}, _v(m.group(3), p)))
    a, b = relation.group(1), relation.group(3)
    if a not in nodes or b not in nodes or len(nodes) != 3:
        return None
    equations.append(({a: Fraction(1), b: -_factor(relation.group(2), p)}, Fraction(0)))
    state = _linear(equations, nodes)
    requested = _category_mentions(p.question, nodes)
    if not state or len(requested) != 1:
        return None
    return state[requested[0]], 'Solve the two shared-item totals together with the price comparison.'


def _family_tickets(p):
    """The remaining members of an explicitly counted family buy adult tickets."""
    if not re.search(r'\btickets for the whole family\b', p.body):
        return None
    text = _tokens(p)
    children = re.search(r'\b(q\d+) children\b', text)
    delta = re.search(r'\badult ticket is (q\d+) more than the cost of a child ticket\b', text)
    total = re.search(r'\btotal cost of the (q\d+) tickets is (q\d+)\b', text)
    if not all((children, delta, total)) or _ids(children.group()+' '+delta.group()+' '+total.group()) != set(range(len(p.numbers))):
        return None
    n, c = _v(total.group(1), p), _v(children.group(1), p)
    if n <= c or c < 0 or not re.search(r'\bcost of (?:an? )?(?:adult|child) ticket\b', p.question):
        return None
    gap = _v(delta.group(1), p)
    child_price = (_v(total.group(2), p)-(n-c)*gap)/n
    return _answer(child_price+(gap if 'adult' in p.question else 0), 'Use the family count to weight the adult and child ticket prices.')


def _paired_losses(p):
    """Two withdrawals from a stock, the second compared with the first."""
    if not re.search(r'\b(?:left|remaining|remain)\b', p.question):
        return None
    text = _tokens(p)
    stock = re.search(r'\b([a-z]+) (?:has|had|starts?(?: [a-z]+){0,5} with) (q\d+) ([a-z]+)\b', text)
    debit = r'(?:gives?|gave|drops?|dropped|loses?|lost|eats?|ate|sends?|sent)'
    first = re.search(r'\b' + debit + r' (q\d+)(?: ([a-z]+))?', text)
    second = re.search(r'\b' + debit + r'(?: [a-z]+)? (' + _FACTOR + r') as many(?: ([a-z]+))?', text)
    if not all((stock, first, second)) or not stock.end() <= first.start() < second.start():
        return None
    unit = _singular(stock.group(3))
    if unit not in {_singular(w) for w in re.findall(r'[a-z]+', p.question)}:
        return None
    for noun in (first.group(2), second.group(2)):
        if noun and noun not in ('in', 'to', 'as', 'of', 'on') and _singular(noun) != unit:
            return None
    if _ids(stock.group()+' '+first.group()+' '+second.group()) != set(range(len(p.numbers))):
        return None
    # A separately named giver may be redistributing the first withdrawal.
    names = _names(p.text)
    for name in names:
        if name != stock.group(1) and re.search(r'\b' + re.escape(name) + ' ' + debit + r'\b', text):
            return None
    value = _v(stock.group(2), p)-_v(first.group(1), p)*(1+_factor(second.group(1), p))
    return _answer(value, 'Subtract the first withdrawal and the compared second withdrawal from the original stock.')


def _time_allocation(p):
    """An explicitly stated working duration split between two activities."""
    if len(_names(p.text)) > 1:
        return None
    text = _tokens(p)
    ratio = re.search(r'\bspends? (' + _FACTOR + r') as long (?:doing )?([^.;]+?) as ([^.;]+?)[.;]', text)
    total = re.search(r'\bworked (q\d+) (minutes?|hours?) (?:today|in total|altogether)\b', text)
    if not ratio or not total or _ids(ratio.group()+' '+total.group()) != set(range(len(p.numbers))):
        return None
    left, right = ratio.group(2).strip(), ratio.group(3).strip()
    requested = [part for part in (left, right) if part in p.question]
    k = _factor(ratio.group(1), p)
    if len(requested) != 1 or k <= 0:
        return None
    value = _v(total.group(1), p)/(1+k)*(k if requested[0] == left else 1)
    return _measured_answer(value, total.group(2), p.question, 'Split the total working duration by the activity ratio.')


def solve(problem):
    if (len(_names(problem.text)) > 1 and
            re.search(r'\bas long as [A-Z][a-z]+ (?:played|ran|practiced)\b', problem.text)):
        return None
    if not re.search(r'\b(?:twice|thrice|double|triple|times|more|less|fewer|older|younger)\b', problem.text, re.I):
        return None
    if re.search(r'\btimes more than\b', problem.text, re.I):
        return None
    for rule in (_ordinal_entities, _activities, _period_amounts, _changed_inventory,
                 _used_remainder, _outfit_product, _speed_comparison,
                 _category_paraphrases, _added_inventory, _two_durations,
                 _group_query, _relative_age_difference, _complement_query,
                 _paired_amounts, _self_age, _calendar_ages, _group_ages,
                 _geometry, _pairwise_totals, _family_tickets,
                 _paired_losses, _time_allocation):
        result = rule(problem)
        if result is not None:
            return result
    text = _adapt(problem.text)
    return _read(text) if text != problem.text else None
