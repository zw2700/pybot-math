"""Short comparisons with explicit ellipsis, grouped amounts and balances.

Each reader accounts for its quantities and requires the requested operation.
Syntactic expansions use the existing exact affine equation reader.
"""
import re
from fractions import Fraction

from ..numbers import read_numbers
from .comparisons_r01_a2 import _names
from .comparisons_r04_a3 import _linear
from .comparisons_r03_a4 import _UNIT, _UNITS, _singular
from .comparisons_r05_a6 import (
    _read, _NUMBER, _RAW_FACTOR, _tokens, _ids, _v, _factor,
    _FACTOR,
)
from .comparisons_r08_a4 import _normalize, _parts


def _answer(value, working):
    return (value, working) if value >= 0 else None


def _adapted(p):
    text = p.text
    if re.search(r'\bsleeps?\b', text, re.I):
        text = re.sub(r"\b[A-Z][a-z]+'s (?:new |old )?([a-z]+)(?= sleeps?\b)", lambda m: m.group(1).title()+' ', text)
        text = re.sub(r'\b(?:his|her) (?:older |younger )?(?:brother|sister) ([A-Z][a-z]+)', r'\1', text)
        text = re.sub(r'\bsleeps?\b', 'had', text, flags=re.I)
        text = re.sub(r'\ba night\b', '', text, flags=re.I)
    text = re.sub(r'\b([A-Z][a-z]+) and ([A-Z][a-z]+) each (?:ate|had|got) ('+_RAW_FACTOR+r') as many as ([A-Z][a-z]+)',
                  r'\1 has \3 as many as \4. \2 has \3 as many as \4', text)
    text = re.sub(r'\bordered\b', 'had', text, flags=re.I)
    if re.search(r'\bin the same period\b', text, re.I):
        text = re.sub(r'\bin '+_NUMBER+r' years\b', '', text, flags=re.I)
        text = re.sub(r'\battended\b', 'had', text, flags=re.I)
    text = re.sub(r'\b(had '+_NUMBER+r' [a-z]+(?: [a-z]+)?) from a [a-z-]+(?: [a-z]+){0,2}(?=[.;])', r'\1', text, flags=re.I)
    text = re.sub(r"\b([A-Z][a-z]+)'s age is (\d+/\d+)(?:st|nd|rd|th)? the age of\b",
                  r'\1 is \2 times as old as', text)
    text = re.sub(r'\bcan grow to weigh\b', 'weighs', text, flags=re.I)
    text = re.sub(r'\b(' + _RAW_FACTOR + r') as high\b', r'\1 as tall', text, flags=re.I)
    text = re.sub(r'\bft\b', 'feet', text, flags=re.I)
    text = re.sub(r'\bas (?:it|he|she|they) did (?=[a-z]+)', 'as ', text, flags=re.I)
    text = re.sub(r'\bIf ('+_NUMBER+r') ([a-z]+) were sold\s*', r'There are \1 \2. ', text, flags=re.I)
    if re.search(r'\bthere are [a-z ,]+, and [a-z ]+[.]', text, re.I):
        text = re.sub(r'\bIf there are ('+_NUMBER+r') pieces of [a-z]+ in [^,]+,\s*',
                      r'They have \1 in total. ', text, flags=re.I)
    # A standalone multiplier of a named age is a ratio of ages.
    text = re.sub(r"\b('?(?:twice|thrice|double|triple)) ([A-Z][a-z]+)'s age", r'\1 as old as \2', text)
    # A multiplicative decrease is a reciprocal, rather than a subtraction.
    def fewer(m):
        factor = read_numbers(m.group(1))[0].value
        return str(1/factor) + ' times as many' if factor > 0 else m.group()
    text = re.sub(r'\b(' + _NUMBER + r') times fewer\b', fewer, text, flags=re.I)
    # In affine age comparisons the additive term can precede a multiplier.
    text = re.sub(r'\b(older|younger) than (?=' + _RAW_FACTOR + r'\b)',
                  lambda m: ('more' if m.group(1).lower() == 'older' else 'less') + ' than ', text, flags=re.I)
    text = re.sub(r'\bquicker than\b', 'less than', text, flags=re.I)
    text = re.sub(r'\bfinished the race in\b', 'had', text, flags=re.I)
    text = re.sub(r'\b(?:finished|took)\b', 'had', text, flags=re.I)
    # A frequency of the same action has the same affine structure as a count.
    text = re.sub(r'\bas often as\b', 'as much as', text, flags=re.I)
    text = re.sub(r'\b(' + _RAW_FACTOR + r') the ([a-z]+) that\b', r'\1 as many \2 as', text, flags=re.I)
    text = re.sub(r'\b(?:drinks|drank)\b', 'has', text, flags=re.I)
    # Repeated daily labels describe a common unit, not extra amounts.
    if re.search(r'\bper day\b', p.question) and re.search(r'\bper day\b', p.body):
        text = re.sub(r'\b(?:in one day|per day)\b', '', text, flags=re.I)
    # Cost questions often put "cost of" after the final ASK cue.
    text = re.sub(r'what is the cost of (.+?)\?', r'How much does \1 cost?', text, flags=re.I)
    text = re.sub(r'\bIf (the [a-z]+ costs [^.;,]+),\s*(?=How much)', r'\1. ', text)
    # Species/objects are the entities when their lifespans are compared.
    if re.search(r'\blifespan\b', p.body):
        text = re.sub(r'Altogether, the lifespan of the [a-z]+ is', 'Together they have', text, flags=re.I)
        text = re.sub(r'\b(?:the )?lifespan of (?:a|the) ([a-z]+)\b',
                      lambda m: m.group(1).title(), text, flags=re.I)
        text = re.sub(r'\bthat of (?:a|the) ([a-z]+)\b', lambda m: m.group(1).title(), text, flags=re.I)
        text = re.sub(r'\b(' + _RAW_FACTOR + r') (?=[A-Z][a-z]+\b)', r'\1 as much as ', text)
        text = re.sub(r'What is ([A-Z][a-z]+)\?', r'How much does \1 have?', text)
    # A possessive bid refers to the sole bidder whose bid is stated directly.
    bidder = re.search(r"\b([A-Z][a-z]+)'s bid was (\$[\d,]+)", text)
    if bidder and len(re.findall(r"\b[A-Z][a-z]+'s bid was\b", text)) == 1:
        target = re.search(r'how much did ([A-Z][a-z]+) get', text)
        if target:
            text = re.sub(r'[^.;]*\bby paying\b', target.group(1) + ' has', p.text, flags=re.I)
            text = re.sub(r'\b(' + _RAW_FACTOR + r') (?:his|her) bid\b',
                          lambda m: m.group(1) + ' as much as ' + bidder.group(1), text, flags=re.I)
            text = re.sub(r"\b([A-Z][a-z]+)'s bid was\b", r'\1 has', text)
            text = re.sub(r'\bat how much did (.+?) get [^?]+\?', r'How much does \1 have?', text, flags=re.I)
    # "Compared to X, ... k times Y" explicitly supplies the reference X.
    front = re.match(r'Compared to the amount of (.+?) (?:he|she|they) [a-z]+,\s*', text, re.I)
    if front:
        reference = front.group(1)
        text = text[front.end():]
        text = re.sub(r'\b(' + _RAW_FACTOR + r' as (?:much|many) [a-z]+)(?= (?:minus|plus)\b)',
                      lambda m: m.group(1) + ' as ' + reference, text, count=1, flags=re.I)
    text = _normalize(text)
    return _read(text) if text != p.text else None


def _implicit_pair(p):
    """A counted component followed by an implicit multiple of that component."""
    body, query = _parts(_tokens(p))
    if set(_names(p.text[len(p.body):])) - {'calculate', 'determine', 'find'} - set(_names(p.text[:len(p.body)])):
        return None
    m = re.search(r'\b(q\d+) ([a-z]+)([^.;]*?)\band\s+(' + _FACTOR + r') as (many|much)([^.;]*)', body)
    if not m or _ids(m.group()) != set(range(len(p.numbers))):
        return None
    if re.search(r'\b(?:as|than|each|per|every|more|less|fewer|left|remaining)\b', m.group(6)):
        return None
    noun = m.group(2)
    if not re.search(r'\b' + re.escape(noun) + r'\b', query) or re.search(r'\b(?:more|less|fewer|left|remaining)\b', query):
        return None
    # Both components must be requested, explicitly or through their whole.
    aggregate = re.search(r'\b(?:total|all|altogether|combined)\b', query)
    aggregate = aggregate or (re.search(r'\b(?:on|in) the\b', m.group(3)) and
                              re.search(r'\b(?:on|in) the\b', m.group(6)))
    aggregate = aggregate or re.search(r'\bhow many ' + re.escape(noun) + r' did [a-z]+ (?:eat|buy|collect|make)\b', query)
    if not aggregate or not re.search(r'\b' + re.escape(noun) + r'\b', m.group(6)):
        return None
    return _answer(_v(m.group(1), p)*(1+_factor(m.group(4), p)), 'Add the first amount and its stated multiple.')


def _grouped_left(p):
    """Two compared owners together differ from a third known owner."""
    text = _tokens(p)
    names = _names(p.text)
    if len(names) != 3:
        return None
    relation = re.search(r'\b([a-z]+) has (' + _FACTOR + r') as many [a-z]+ as ([a-z]+)\b', text)
    group = re.search(r'\b(?:the (?:two|q\d+) of them|they) together have (q\d+) (more|fewer|less) [a-z]+ than ([a-z]+)\b', text)
    if not relation or not group:
        return None
    left, right, other = relation.group(1), relation.group(3), group.group(3)
    if set((left, right, other)) != set(names):
        return None
    known = re.search(r'\b' + re.escape(other) + r' has (q\d+) [a-z]+', text)
    if not known:
        return None
    used = _ids(relation.group()+' '+group.group()+' '+known.group())
    if used != set(range(len(p.numbers))):
        return None
    label = re.search(r'the (q\d+) of them', group.group())
    if label and _v(label.group(1), p) != 2:
        return None
    total = _v(known.group(1), p) + _v(group.group(1), p)*(-1 if group.group(2) in ('less', 'fewer') else 1)
    k = _factor(relation.group(2), p)
    asked = [n for n in (left, right) if re.search(r'\b'+re.escape(n)+r'\b', p.question)]
    if len(asked) != 1 or k <= 0:
        return None
    return _answer(total/(k+1)*(k if asked[0] == left else 1), 'Find the combined amount, then divide it in the stated ratio.')


def _self_age(p):
    text = _tokens(p)
    m = re.search(r"\b(?:i am|i'm) (" + _FACTOR + r') (?:older than|as old as) i was (q\d+) years? ago\b', text)
    if not m or _ids(m.group()) != set(range(len(p.numbers))) or not re.search(r'\b(?:my age|old am i)\b', p.question):
        return None
    k = _factor(m.group(1), p)
    if k <= 1:
        return None
    return k*_v(m.group(2), p)/(k-1), 'The present age equals the stated multiple of the past age.'


def _range_score(p):
    text = _tokens(p)
    factor = re.search(r'\b(' + _FACTOR + r') as much as the (?:least|lowest) score\b', text)
    highest = re.search(r'\bhighest score is (q\d+)\b', text)
    spread = re.search(r'\brange of the scores is (q\d+)\b', text)
    if not all((factor, highest, spread)) or _ids(' '.join((factor.group(), highest.group(), spread.group()))) != set(range(len(p.numbers))):
        return None
    names = _names(p.text)
    if len(names) != 1 or names[0] not in p.question or 'score' not in p.question:
        return None
    return _answer((_v(highest.group(1), p)-_v(spread.group(1), p))*_factor(factor.group(1), p), 'Subtract the range from the highest score, then apply the comparison.')


def _payment_balance(p):
    text = _tokens(p)
    relation = re.search(r'\bnew ([a-z]+) costs? ('+_FACTOR+r') as much as (?:his|her|the) old \1\b', text)
    payment = re.search(r'\bsold (?:his|her|the) old [a-z]+ for (q\d+)\b', text)
    debt = re.search(r'\bstill owes (?:another )?(q\d+)\b', text)
    if not all((relation, payment, debt)) or not re.search(r'\bold [a-z]+ cost\b', p.question):
        return None
    if not re.search(r'\bused that to pay\b', text) or _ids(' '.join((relation.group(), payment.group(), debt.group()))) != set(range(len(p.numbers))):
        return None
    k = _factor(relation.group(2), p)
    return ((_v(payment.group(1), p)+_v(debt.group(1), p))/k, 'Add the payment and balance to find the new price, then divide by the price ratio.') if k > 0 else None


def _fixed_share(p):
    """Remove a separately known recipient before dividing a ratio remainder."""
    text = _tokens(p)
    total = re.search(r'\b(?:share|split) (q\d+) ([a-z]+)\b', text)
    fixed = re.search(r'\b([a-z]+) (?:took|received|got) (q\d+) ([a-z]+)\b', text)
    ratio = re.search(r'\b([a-z]+) took (' + _FACTOR + r') as many as ([a-z]+)\b', text)
    if not all((total, fixed, ratio)) or total.group(2) != fixed.group(3):
        return None
    if _ids(total.group()+fixed.group()+ratio.group()) != set(range(len(p.numbers))):
        return None
    if fixed.group(1) in (ratio.group(1), ratio.group(3)):
        return None
    asked = [n for n in (ratio.group(1), ratio.group(3)) if re.search(r'\b'+re.escape(n)+r'\b', p.question)]
    k = _factor(ratio.group(2), p)
    if len(asked) != 1 or k <= 0:
        return None
    return _answer((_v(total.group(1), p)-_v(fixed.group(2), p))/(1+k)*(k if asked[0] == ratio.group(1) else 1), 'Subtract the fixed share and divide the remaining amount in the stated ratio.')


def _allocated_stock(p):
    text = _tokens(p)
    gift = re.search(r'\bgives? (q\d+) ([a-z]+) to (?:one|q\d+) of [^.;]+? and keeps ('+_FACTOR+r') (?:this|that) amount for (?:herself|himself)\b', text)
    stock = re.search(r'\boriginally (?:made|had|bought) (q\d+) ([a-z]+)\b', text)
    if not gift or not stock or gift.group(2) != stock.group(2) or not re.search(r'\bleft to give\b', p.question):
        return None
    if _ids(gift.group()+' '+stock.group()) != set(range(len(p.numbers))):
        return None
    recipient = re.search(r'\bto (q\d+) of\b', gift.group())
    if recipient and _v(recipient.group(1), p) != 1:
        return None
    return _answer(_v(stock.group(1), p)-_v(gift.group(1), p)*(1+_factor(gift.group(3), p)), 'Subtract the given amount and the compared amount kept from the original stock.')


def _capacity(p):
    text = _tokens(p)
    relation = re.search(r'\b(?:store|hold|contain)s? (q\d+) ([a-z]+) more than ('+_FACTOR+r') as much as (?:a|an|the) (?:large |small )?([a-z]+)\b', text)
    count = re.search(r'\bhas (q\d+) ([a-z]+)\b', text)
    known = re.search(r'\ba ([a-z]+) (?:stores?|holds?|contains?) (q\d+) ([a-z]+)\b', text)
    if not all((relation, count, known)) or relation.group(4) != known.group(1) or relation.group(2) != known.group(3):
        return None
    if not re.search(r'\bhow much .+? can .+? (?:store|hold)\b', p.question):
        return None
    if _ids(' '.join((relation.group(), count.group(), known.group()))) != set(range(len(p.numbers))):
        return None
    # The repeated container must be the one described immediately before the relation.
    intro = text[:relation.start()]
    if not re.search(r'\b'+re.escape(count.group(2))+r'\b', intro):
        return None
    return _v(count.group(1), p)*(_factor(relation.group(3), p)*_v(known.group(2), p)+_v(relation.group(1), p)), 'Find one container\'s capacity from the comparison, then multiply by the container count.'


def _repeat_order(p):
    if not re.search(r'\b(?:order|buy) another set\b', p.body):
        return None
    body, query = _parts(p.text)
    repeat = re.search(r'\bIf they (?:order|buy) another set of ([a-z ]+),\s*$', body, re.I)
    if not repeat or read_numbers(query):
        return None
    base = body[:repeat.start()]
    base = re.sub(r'\bordered\b', 'has', base, flags=re.I)
    result = _read(base+query)
    if result is None:
        return None
    return result[0]*2, 'Find the compared order and count both identical sets.'


def _destinations(p):
    """The counted noun is shared, but destinations name separate variables."""
    body, query = _parts(_tokens(p))
    if re.search(r'\b(?:per|each|every)\b', body):
        return None
    tail = r'\s+(?:to|on|in) the ([a-z]+(?: [a-z]+){0,3}?)(?: of the field)?'
    reference = r'\s+(?:as|than) (?:it|he|she) (?:did|does|do)(?: to| on| in) the ([a-z]+(?: [a-z]+){0,3}?)(?: of the field)?(?=[.;,]|$)'
    mult = re.compile(r'(?:(q\d+) (more|less|fewer) than )?('+_FACTOR+r') (?:the number of|as many) ([a-z]+)'+tail+reference)
    add = re.compile(r'(q\d+) (more|less|fewer) ([a-z]+)'+tail+reference)
    equations, nodes, used, spans = [], set(), set(), []
    unit = None
    for m in mult.finditer(body):
        left, right = m.group(5), m.group(6)
        if left == right or unit and unit != m.group(4):
            return None
        unit = m.group(4)
        k = _factor(m.group(3), p)
        d = _v(m.group(1), p)*(-1 if m.group(2) in ('less', 'fewer') else 1) if m.group(1) else Fraction(0)
        equations.append(({left: Fraction(1), right: -k}, d))
        nodes.update((left, right)); used.update(_ids(m.group())); spans.append(m.span())
    for m in add.finditer(body):
        if any(a <= m.start() < b for a, b in spans):
            continue
        left, right = m.group(4), m.group(5)
        if left == right or unit and unit != m.group(3):
            return None
        unit = m.group(3)
        equations.append(({left: Fraction(1), right: Fraction(-1)}, _v(m.group(1), p)*(-1 if m.group(2) in ('less', 'fewer') else 1)))
        nodes.update((left, right)); used.update(_ids(m.group()))
    if not nodes or not unit or not re.search(r'\b'+re.escape(unit)+r'\b', query):
        return None
    for i, n in enumerate(p.numbers):
        if i in used:
            continue
        token = 'q'+str(i)
        if re.search(r'\b'+token+r'\b', query):
            return None
        anchor = re.search(r'\b'+token+' '+re.escape(unit)+r' (?:to|on|in) the ([a-z]+(?: [a-z]+){0,3}?)(?: of the field)?(?=[.;,]|$)', body)
        if anchor:
            if anchor.group(1) not in nodes:
                return None
            equations.append(({anchor.group(1): Fraction(1)}, n.value))
        elif n.value == 1 and re.search(r'\bin '+token+r' (?:game|day)\b', body):
            pass
        elif re.search(r'\b'+token+' '+re.escape(unit)+r'\b', body):
            equations.append(({node: Fraction(1) for node in nodes}, n.value))
        else:
            return None
        used.add(i)
    state = _linear(equations, nodes)
    asked = [node for node in nodes if re.search(r'\b'+re.escape(node)+r'\b', query)]
    if state and len(asked) == 1:
        return state[asked[0]], 'Solve the comparisons between destinations using the stated amount.'
    return None


def _converted_chain(p):
    requested = re.search(r'\b(?:how many|how much|in) ('+_UNIT+r')\b', p.question)
    if not requested:
        return None
    measures = []
    for n in p.numbers:
        unit = re.match(r'\s+('+_UNIT+r')\b', p.text[n.end:], re.I)
        if unit:
            measures.append(unit.group(1).lower())
    if not measures or len({_UNITS[_singular(u)] for u in measures}) != 1:
        return None
    source, dest = _UNITS[_singular(measures[0])], _UNITS[_singular(requested.group(1))]
    if source == dest or source[0] != dest[0]:
        return None
    body, query = _parts(p.text)
    query = re.sub(r'\b'+re.escape(requested.group(1))+r'\b', measures[0], query, flags=re.I)
    result = _read(_normalize(body+query))
    if result is None:
        return None
    return result[0]*source[1]/dest[1], result[1]+' Convert to the requested unit.'


def _rectangle(p):
    if not re.search(r'\b(?:rectangle|rectangular)\b', p.body):
        return None
    text = _tokens(p)
    perimeter = re.search(r'\bperimeter (?:of [^.;]+? )?is (q\d+)\b', text)
    ratio = re.search(r'\b(length|width) is ('+_FACTOR+r') (?:the )?(length|width)\b', text)
    if not perimeter or not ratio or ratio.group(1) == ratio.group(3):
        return None
    if _ids(perimeter.group()+' '+ratio.group()) != set(range(len(p.numbers))):
        return None
    asked = [side for side in ('length', 'width') if re.search(r'\b'+side+r'\b', p.question)]
    k = _factor(ratio.group(2), p)
    if len(asked) != 1 or k <= 0:
        return None
    return _v(perimeter.group(1), p)/(2*(1+k))*(k if asked[0] == ratio.group(1) else 1), 'The perimeter is twice the sum of the length and width.'


def _scaled_age(p):
    text = _tokens(p)
    m = re.fullmatch(r"\s*("+_FACTOR+r") ([a-z]+)'s age,? (plus|minus) (q\d+),? is (q\d+)[. ]*", _parts(text)[0])
    if not m or _ids(m.group()) != set(range(len(p.numbers))) or not re.search(r'\bhow old is '+re.escape(m.group(2))+r'\b', p.question):
        return None
    k = _factor(m.group(1), p)
    d = _v(m.group(4), p)*(-1 if m.group(3) == 'minus' else 1)
    return _answer((_v(m.group(5), p)-d)/k, 'Subtract the offset and divide by the age multiplier.') if k > 0 else None


def _partition_ratio(p):
    """Known categories are removed from a total before dividing the rest."""
    body, query = _parts(_tokens(p))
    ratio = re.search(r'\b('+_FACTOR+r') as many ([a-z]+) as ([a-z]+) ([a-z]+)\b', body)
    if not ratio:
        return None
    left, right, unit = ratio.group(2), ratio.group(3), ratio.group(4)
    rest = re.search(r'\bthe rest are (?:either )?'+re.escape(left)+r' or '+re.escape(right)+r'\b', body)
    if not rest:
        return None
    total = re.search(r'\bhas (q\d+) '+re.escape(unit)+r'\b', body)
    if not total:
        return None
    amounts = list(re.finditer(r'\b(q\d+)(?: '+re.escape(unit)+r')? are ([a-z]+)\b', body))
    used = _ids(ratio.group()+' '+total.group()+' '+' '.join(m.group() for m in amounts))
    if not amounts or used != set(range(len(p.numbers))) or any(m.group(2) in (left, right) for m in amounts):
        return None
    requested = [c for c in (left, right) if re.search(r'\b'+re.escape(c)+r'\b', query)]
    k = _factor(ratio.group(1), p)
    if len(requested) != 1 or k <= 0:
        return None
    remainder = _v(total.group(1), p)-sum((_v(m.group(1), p) for m in amounts), Fraction(0))
    return _answer(remainder/(k+1)*(k if requested[0] == left else 1), 'Remove the known categories and divide the rest in the stated ratio.')


def _compared_servings(p):
    text = _tokens(p)
    ratio = re.search(r'\b(q\d+) ([a-z]+) and ('+_FACTOR+r') as many ([a-z]+(?: [a-z]+)?) as \2\b', text)
    count = re.search(r'\b(q\d+) (?:customers|people|guests) order ([a-z]+(?: [a-z]+)?)\b', text)
    if not ratio or not count or _ids(ratio.group()+' '+count.group()) != set(range(len(p.numbers))):
        return None
    if not re.search(r'\b'+re.escape(ratio.group(4))+r'\b', p.question):
        return None
    # One complete serving per customer must be named in both clauses.
    serving = re.sub(r's$', '', count.group(2))
    if not re.search(r'\b'+re.escape(serving)+r' has\b', text[:ratio.start()]):
        return None
    return _v(ratio.group(1), p)*_factor(ratio.group(3), p)*_v(count.group(1), p), 'Find the compared amount in one serving and multiply by the number of servings.'


def _deletion_limit(p):
    text = _tokens(p)
    maximum = re.search(r'\bmaximum of (q\d+) ([a-z]+)\b', text)
    recommended = re.search(r'\brecommended number of ([a-z]+) is (q\d+)\b', text)
    ratio = re.search(r'\b('+_FACTOR+r') the recommended number of ([a-z]+)\b', text)
    if not all((maximum, recommended, ratio)) or len({maximum.group(2), recommended.group(1), ratio.group(2)}) != 1:
        return None
    if not re.search(r'\b(?:delete|remove|discard)\b', p.question):
        return None
    if _ids(' '.join((maximum.group(), recommended.group(), ratio.group()))) != set(range(len(p.numbers))):
        return None
    return _answer(_factor(ratio.group(1), p)*_v(recommended.group(2), p)-_v(maximum.group(1), p), 'Find the current amount and subtract the maximum allowed amount.')


def _container_categories(p):
    """Repeated 'container of category' and 'category container' name one slot."""
    text = p.text
    descriptions = list(re.finditer(r'\bthe ([a-z]+) of ([a-z]+(?: [a-z]+){0,3}?) (?:had|has)\b', text, re.I))
    heads = {m.group(1).lower() for m in descriptions}
    if len(heads) != 1 or len(descriptions) < 2:
        return None
    head = next(iter(heads))
    if head in ('number', 'amount', 'age', 'weight', 'height', 'sum', 'total'):
        return None
    categories = [m.group(2).lower().split() for m in descriptions]
    # References supply further categories not yet used as a subject.
    pattern = r'\bthe '+re.escape(head)+r' of ([a-z]+(?: [a-z]+){0,3}?)(?=[.;]|\s+had\b|\s+has\b)'
    categories += [m.group(1).lower().split() for m in re.finditer(pattern, text, re.I)]
    categories = list(dict.fromkeys(tuple(c) for c in categories))
    if not 2 <= len(categories) <= 4 or len({c[-1] for c in categories}) != 1:
        return None
    common = categories[0][-1]
    if any(len(c) < 2 for c in categories):
        return None
    labels = [' '.join(c[:-1]) for c in categories]
    for i, label in enumerate(sorted(labels, key=len, reverse=True)):
        alias = 'Category'+chr(97+i)
        text = re.sub(r'\b(?:the )?'+re.escape(head)+r' of '+re.escape(label)+r' '+re.escape(common)+r'\b', alias, text, flags=re.I)
        text = re.sub(r'\b(?:the )?'+re.escape(label)+r' '+re.escape(head)+r'\b', alias, text, flags=re.I)
    intro = re.match(r'There (?:are|were) ('+_NUMBER+r') '+re.escape(head)+r's of '+re.escape(common)+r' [^.;]+[.;]\s*', text, re.I)
    if intro:
        if read_numbers(intro.group(1))[0].value != len(categories):
            return None
        text = text[intro.end():]
    return _read(_normalize(text))


def _original_stock(p):
    text = _tokens(p)
    relation = re.search(r'\bgives ([a-z]+) ('+_FACTOR+r') as many ([a-z]+) as (?:she|he) gives ([a-z]+) and remains with (q\d+) \3\b', text)
    if not relation or not re.search(r'\bhave before\b', p.question):
        return None
    known = re.search(r'\b'+re.escape(relation.group(4))+r' received (q\d+) '+re.escape(relation.group(3))+r'\b', text)
    if not known or _ids(relation.group()+' '+known.group()) != set(range(len(p.numbers))):
        return None
    return _v(known.group(1), p)*(1+_factor(relation.group(2), p))+_v(relation.group(5), p), 'Add the compared gifts and the amount retained.'


def _future_sibling_sum(p):
    text = _tokens(p)
    relation = re.search(r"\bin (q\d+) years, i'll be ("+_FACTOR+r") my (brother|sister)'s age\b", text)
    total = re.search(r'\bsum of our ages will then be (q\d+)', text)
    if not relation or not total or not re.search(r'\bhow old am i now\b', p.question):
        return None
    if _ids(relation.group()+' '+total.group()) != set(range(len(p.numbers))):
        return None
    k = _factor(relation.group(2), p)
    if k <= 0:
        return None
    return _answer(_v(total.group(1), p)*k/(k+1)-_v(relation.group(1), p), 'Divide the future age total in the stated ratio, then subtract the elapsed years.')


def _rectangle_area(p):
    if re.search(r'\b(?:triangle|triangular|circle|circular|ellipse|elliptical|trapezoid|trapezium)\b', p.body):
        return None
    text = _tokens(p)
    known = re.search(r'\b(q\d+) ('+_UNIT+r') (wide|long)\b', text)
    ratio = re.search(r'\b('+_FACTOR+r') as (long|wide) as it is (wide|long)\b', text)
    if not known or not ratio or ratio.group(2) == ratio.group(3) or not re.search(r'\barea\b', p.question):
        return None
    if _ids(known.group()+' '+ratio.group()) != set(range(len(p.numbers))):
        return None
    k = _factor(ratio.group(1), p)
    if k <= 0:
        return None
    side = _v(known.group(1), p)
    return side*side*(k if known.group(3) == ratio.group(3) else 1/k), 'Use the side comparison and multiply length by width.'


def _remaining_category(p):
    text = _tokens(p)
    ratio = re.search(r'\b('+_FACTOR+r') as many ([a-z]+) as ([a-z]+)\b', text)
    if not ratio:
        return None
    left, right = ratio.group(2), ratio.group(3)
    unknown = re.search(r'\b(?:also )?some ([a-z]+)\b', text)
    if not unknown or unknown.group(1) in (left, right) or not re.search(r'\b'+re.escape(unknown.group(1))+r'\b', p.question):
        return None
    known = re.search(r'\bthere are (q\d+) '+re.escape(right)+r'\b', text)
    total = re.search(r'\ball the (q\d+) ([a-z]+)\b', text)
    if not known or not total or _ids(' '.join((ratio.group(), known.group(), total.group()))) != set(range(len(p.numbers))):
        return None
    return _answer(_v(total.group(1), p)-_v(known.group(1), p)*(1+_factor(ratio.group(1), p)), 'Subtract the two known compared categories from the whole group.')


def _implicit_remainder(p):
    text = _tokens(p)
    pair = re.search(r'\b(q\d+) ([a-z]+), ('+_FACTOR+r') as many ([a-z]+), and some ([a-z]+)\b', text)
    total = re.search(r'\bin total there are (q\d+) ([a-z]+)\b', text)
    if not pair or not total or _ids(pair.group()+' '+total.group()) != set(range(len(p.numbers))):
        return None
    if not re.search(r'\b'+re.escape(pair.group(5))+r'\b', p.question):
        return None
    return _answer(_v(total.group(1), p)-_v(pair.group(1), p)*(1+_factor(pair.group(3), p)), 'Subtract the first category and its multiple from the total.')


def _repeated_groups(p):
    text = _tokens(p)
    count = re.search(r'\bhas (q\d+) ([a-z]+(?: [a-z]+)?)\b', text)
    first = re.search(r'\b(q\d+) of the ([a-z]+) has (q\d+) ([a-z]+)\b', text)
    others = re.search(r'\bthe other (q\d+) have ('+_FACTOR+r') as many \b', text)
    if not all((count, first, others)) or not re.search(r'\beach as the first\b', text):
        return None
    if _v(first.group(1), p) != 1 or _v(count.group(1), p) != _v(others.group(1), p)+1:
        return None
    if not count.group(2).endswith(first.group(2)) or not re.search(r'\b'+re.escape(first.group(4))+r'\b', p.question):
        return None
    if _ids(' '.join((count.group(), first.group(), others.group()))) != set(range(len(p.numbers))):
        return None
    return _v(first.group(3), p)*(1+_v(others.group(1), p)*_factor(others.group(2), p)), 'Add the first group and the repeated larger groups.'


def _two_numbers(p):
    text = _tokens(p)
    total = re.search(r'\bsum of (q\d+) numbers is (q\d+)', text)
    ratio = re.search(r'\b(second|first) number is ('+_FACTOR+r') the (first|second) number\b', text)
    if not total or not ratio or ratio.group(1) == ratio.group(3) or _v(total.group(1), p) != 2:
        return None
    if _ids(total.group()+' '+ratio.group()) != set(range(len(p.numbers))):
        return None
    asked = re.search(r'\b(first|second) number\b', p.question)
    k = _factor(ratio.group(2), p)
    if not asked or k <= 0:
        return None
    return _v(total.group(2), p)/(1+k)*(k if asked.group(1) == ratio.group(1) else 1), 'Divide the sum of the two numbers in the stated ratio.'


def _event_age_ratio(p):
    body, query = _parts(p.text)
    event = re.search(r'\bwhen ([A-Z][a-z]+) becomes ('+_RAW_FACTOR+r') as old as ([A-Z][a-z]+)\?', query)
    if not event or read_numbers(query[:event.start()]):
        return None
    # With only constant age differences, the event fixes all ages.
    normalized = _normalize(body)
    nums = read_numbers(normalized)
    if not nums or any(not re.match(r'\s+years? (?:older|younger) than\b', normalized[n.end:], re.I) for n in nums):
        return None
    rewritten = normalized + '{} is {} as old as {}. '.format(event.group(1), event.group(2), event.group(3))
    return _read(rewritten + query[:event.start()].rstrip(' ?')+'?')


def _scaled_speed(p):
    text = _tokens(p)
    speed = re.search(r'\b(q\d+) ([a-z]+) per (hour|minute)\b', text)
    ratio = re.search(r'\b('+_FACTOR+r') as fast for (q\d+) (hours|minutes)\b', text)
    if not speed or not ratio or _singular(ratio.group(3)) != speed.group(3):
        return None
    if _ids(speed.group()+' '+ratio.group()) != set(range(len(p.numbers))):
        return None
    if not re.search(r'\bhow many '+re.escape(speed.group(2))+r'\b', p.question):
        return None
    return _v(speed.group(1), p)*_factor(ratio.group(1), p)*_v(ratio.group(2), p), 'Multiply the compared speed by the travel time.'


def _activity_total(p):
    text = _tokens(p)
    ratio = re.search(r'\bfor ('+_FACTOR+r') as long as (?:he|she) was ([a-z]+)\b', text)
    known = re.search(r'\b(?:he|she) ([a-z]+) (q\d+) (hours?|minutes?)\b', text)
    if not ratio or not known or _ids(ratio.group()+' '+known.group()) != set(range(len(p.numbers))):
        return None
    irregular = {'drove': 'driving', 'ran': 'running', 'read': 'reading', 'swam': 'swimming'}
    verb = known.group(1)
    gerund = irregular.get(verb, verb[:-2]+'ing' if verb.endswith('ed') else verb+'ing')
    if gerund != ratio.group(2):
        return None
    if not re.search(r'\b(?:how long was the trip|total (?:time|duration))\b', p.question):
        return None
    return _v(known.group(2), p)*(1+_factor(ratio.group(1), p)), 'Add the two compared activity durations.'


def _located_duration(p):
    text = _tokens(p)
    ratio = re.search(r'\b(q\d+) more than ('+_FACTOR+r') as long to ([a-z]+) ([a-z]+) (?:than|then) to \3 ([a-z]+)\b', text)
    total = re.search(r'\bfor a total of (q\d+) (minutes?|hours?)\b', text)
    if not ratio or not total or ratio.group(4) == ratio.group(5):
        return None
    if _ids(ratio.group()+' '+total.group()) != set(range(len(p.numbers))):
        return None
    targets = [n for n in (ratio.group(4), ratio.group(5)) if re.search(r'\b'+re.escape(n)+r'\b', p.question)]
    if len(targets) != 1:
        return None
    k, extra = _factor(ratio.group(2), p), _v(ratio.group(1), p)
    base = (_v(total.group(1), p)-extra)/(1+k)
    return _answer(base*k+extra if targets[0] == ratio.group(4) else base, 'Divide the total time using the duration ratio and the extra time.')


def _relative_birth_year(p):
    text = _tokens(p)
    born = re.search(r'\b([a-z]+) was born in (q\d+)\b', text)
    ratio = re.search(r'\bcurrently ('+_FACTOR+r') as old as (?:her|his) (brother|sister)\b', text)
    age = re.search(r'\bcurrent age is (q\d+)\b', text)
    if not all((born, ratio, age)) or _ids(' '.join((born.group(), ratio.group(), age.group()))) != set(range(len(p.numbers))):
        return None
    if not re.search(r'\bwhat year\b.*\b'+ratio.group(2)+r' born\b', p.question):
        return None
    k = _factor(ratio.group(1), p)
    if k <= 0:
        return None
    return _v(born.group(2), p)+_v(age.group(1), p)-_v(age.group(1), p)/k, 'Use the known birth year and age to determine the relative\'s birth year.'


def _simple_pair_total(p):
    if set(_names(p.text[len(p.body):])) - {'calculate', 'determine', 'find'} - set(_names(p.text[:len(p.body)])):
        return None
    body, query = _parts(_tokens(p))
    ratio = re.search(r'\b('+_FACTOR+r') (?:this many|that (?:many|number)|as many|as (?:much|long))\b', body)
    if not ratio:
        return None
    remaining = set(range(len(p.numbers)))-_ids(ratio.group())
    if len(remaining) != 1:
        return None
    index = next(iter(remaining))
    known = p.numbers[index]
    if known.start >= len(p.body) or known.start > p.text.lower().find(ratio.group(1)) and ratio.group(1) in ('twice', 'thrice', 'double', 'triple'):
        return None
    if re.search(r'\b(?:per|each|every|left|lost|remaining|more|less|fewer|only|sold|price|cost)\b', p.body):
        return None
    # An explicit total can precede the final question cue.
    aggregate = re.search(r'\b(?:total|combined|altogether|both|in all)\b', query)
    aggregate = aggregate or re.search(r'\b(?:in total|all of these should be delivered)[^.;?]*[.;,]?\s*$', p.body)
    rest = re.search(r'\bthe rest of (?:his|her) ([a-z]+)\b', body)
    aggregate = aggregate or (rest and re.search(r'\b'+re.escape(rest.group(1))+r'\b', query))
    if not aggregate:
        return None
    noun = re.match(r'\s+([a-z]+(?: [a-z]+)?)', p.text[known.end:], re.I)
    if not noun:
        return None
    noun_words = {_singular(w) for w in noun.group(1).lower().split()}
    query_words = {_singular(w) for w in re.findall(r'[a-z]+', query)}
    if not noun_words & query_words and not re.search(r'\b(?:how long|combined height|total time)\b', query):
        return None
    return _v('q'+str(index), p)*(1+_factor(ratio.group(1), p)), 'Add the initial amount and its stated multiple.'


def _maximum_from_minimum(p):
    text = _tokens(p)
    ratio = re.search(r'\bno more than ('+_FACTOR+r') the minimum weight\b', text)
    difference = re.search(r'\bno less than (q\d+) (pounds?|kilograms?) heavier than the standard [a-z]+\b', text)
    known = re.search(r'\bstandard [a-z]+ weighs (q\d+) (pounds?|kilograms?)\b', text)
    if not all((ratio, difference, known)) or difference.group(2) != known.group(2) or 'maximum weight' not in p.question:
        return None
    if _ids(' '.join((ratio.group(), difference.group(), known.group()))) != set(range(len(p.numbers))):
        return None
    return (_v(known.group(1), p)+_v(difference.group(1), p))*_factor(ratio.group(1), p), 'Add the minimum excess to the standard weight, then apply the maximum-to-minimum ratio.'


def _rate_capacity(p):
    text = _tokens(p)
    rate = re.search(r'\brate of (q\d+) ([a-z]+) per (hour|minute)\b', text)
    ratio = re.search(r'\bhold ('+_FACTOR+r') the amount of [a-z]+ that would [a-z]+ over (q\d+) (hours?|minutes?)\b', text)
    if not rate or not ratio or _singular(ratio.group(3)) != rate.group(3):
        return None
    # A stated waiting time can repeat the same duration; it is a label for
    # this interval, not an additional interval.
    unused = set(range(len(p.numbers)))-_ids(rate.group()+' '+ratio.group())
    for index in unused:
        number = p.numbers[index]
        if number.value != _v(ratio.group(2), p) or not re.match(r'\s+'+re.escape(ratio.group(3))+r'\b', p.text[number.end:], re.I):
            return None
    if not re.search(r'\bin '+re.escape(rate.group(2))+r'\b', p.question):
        return None
    return _v(rate.group(1), p)*_v(ratio.group(2), p)*_factor(ratio.group(1), p), 'Multiply the rate by the waiting time and the capacity multiplier.'


def _diameter_radius(p):
    text = _tokens(p)
    ratio = re.search(r'\bdiameter ('+_FACTOR+r') as far as the distance\b', text)
    distance = re.search(r'\b(q\d+) ('+_UNIT+r')\b', text)
    if not ratio or not distance or 'radius' not in p.question:
        return None
    if _UNITS[_singular(distance.group(2))][0] not in ('length', 'metric_length'):
        return None
    if _ids(ratio.group()+' '+distance.group()) != set(range(len(p.numbers))):
        return None
    return _v(distance.group(1), p)*_factor(ratio.group(1), p)/2, 'Find the diameter from the comparison, then divide by two for the radius.'


def _calendar_frequency(p):
    text = _tokens(p)
    frequency = re.search(r'\b('+_FACTOR+r') a (week|month) for (q\d+) (hours?|minutes?)\b', text)
    if not frequency or _ids(frequency.group()) != set(range(len(p.numbers))):
        return None
    if not re.search(r'\bper year\b', p.question) or not re.search(r'\b'+re.escape(frequency.group(4))+r'\b', p.question):
        return None
    return _factor(frequency.group(1), p)*_v(frequency.group(3), p)*(12 if frequency.group(2) == 'month' else 52), 'Multiply the visits per period, time per visit, and periods per year.'


def _daily_compared_time(p):
    text = _tokens(p)
    initial = re.search(r'\bspends? (q\d+) (hours?|minutes?) a day ([a-z]+)\b', text)
    ratio = re.search(r'\bspends? ('+_FACTOR+r') as much time ([a-z]+)\b', text)
    if not initial or not ratio or _ids(initial.group()+' '+ratio.group()) != set(range(len(p.numbers))):
        return None
    if not re.search(r'\ba week\b', p.question) or not re.search(r'\b'+re.escape(ratio.group(2))+r'\b', p.question):
        return None
    return _v(initial.group(1), p)*_factor(ratio.group(1), p)*7, 'Find the daily time for the compared activity and multiply by seven days.'


def _event_frequency_sum(p):
    text = _tokens(p)
    if len(_names(p.text)) > 1:
        return None
    body, query = _parts(text)
    events = list(re.finditer(r'\b(once|twice|thrice|q\d+ times) a (day|week|month)\b', body))
    if len(events) < 2 or len({m.group(2) for m in events}) != 1 or not re.search(r'\btotal times\b', query):
        return None
    duration = re.search(r'\bin (q\d+) '+events[0].group(2)+r's\b', query)
    if not duration:
        return None
    used = _ids(' '.join(m.group() for m in events)+' '+duration.group())
    unused = set(range(len(p.numbers)))-used
    for i in unused:
        n = p.numbers[i]
        if not (n.value == 1 and re.match(r'\s+year\b', p.text[n.end:], re.I) and
                events[0].group(2) == 'week' and _v(duration.group(1), p) == 52):
            return None
    frequency = sum((Fraction(1) if m.group(1) == 'once' else _factor(m.group(1), p) for m in events), Fraction(0))
    return frequency*_v(duration.group(1), p), 'Add the event frequencies and multiply by the number of periods.'


def _implicit_difference(p):
    if not re.search(r'^how many more\b', p.question):
        return None
    text = p.text
    text = re.sub(r'\b('+_RAW_FACTOR+r') the ([a-z]+) that\b', r'\1 as many \2 as', text, flags=re.I)
    body, query = _parts(_normalize(text))
    state = _read(body+' How many are there in total?', True)
    if not state or len(state) != 2:
        return None
    asked = [name for name in state if re.search(r'\b'+re.escape(name)+r'\b', query.lower())]
    if len(asked) != 1 or read_numbers(query):
        return None
    values = list(state.values())
    return abs(values[0]-values[1]), 'Subtract the smaller compared amount from the larger amount.'


def _frequency_ratio(p):
    body, query = _parts(_tokens(p))
    ratio = re.search(r'\b('+_FACTOR+r') as often as ([a-z]+)\b', body)
    total = re.search(r'\btogether [^.;]*?\b(q\d+) times\b', body)
    if not ratio or not total or _ids(ratio.group()+' '+total.group()) != set(range(len(p.numbers))):
        return None
    names = _names(p.text)
    if len(names) != 2 or ratio.group(2) not in names or not re.search(r'\bhow many times\b', query):
        return None
    left = next(n for n in names if n != ratio.group(2))
    if not re.search(r'\b'+re.escape(left)+r'\b', body[:ratio.start()]):
        return None
    asked = [n for n in names if re.search(r'\b'+re.escape(n)+r'\b', query)]
    k = _factor(ratio.group(1), p)
    if len(asked) != 1 or k <= 0:
        return None
    return _v(total.group(1), p)/(1+k)*(k if asked[0] == left else 1), 'Divide the combined event count in the stated frequency ratio.'


def _numeric_measure_comparison(p):
    text = _tokens(p)
    known = re.search(r'\b([a-z]+) had (q\d+) ('+_UNIT+r')\b', text)
    adjusted = re.search(r'\b([a-z]+) had (q\d+) ('+_UNIT+r') (less|more) than (q\d+) ('+_UNIT+r')\b', text)
    requested = re.search(r'\bhow many more ('+_UNIT+r')\b', p.question)
    if not all((known, adjusted, requested)) or known.group(1) == adjusted.group(1):
        return None
    if _ids(known.group()+' '+adjusted.group()) != set(range(len(p.numbers))):
        return None
    measures = [_UNITS[_singular(unit)] for unit in (known.group(3), adjusted.group(3), adjusted.group(6), requested.group(1))]
    if len({unit[0] for unit in measures}) != 1:
        return None
    first = _v(known.group(2), p)*measures[0][1]
    second = _v(adjusted.group(5), p)*measures[2][1]+_v(adjusted.group(2), p)*measures[1][1]*(-1 if adjusted.group(4) == 'less' else 1)
    if second < 0:
        return None
    return abs(first-second)/measures[3][1], 'Convert the measured amounts to one unit, apply the adjustment, and find the difference.'


def _bill_counts(p):
    text = _tokens(p)
    denominations = re.search(r'\bonly (q\d+) and (q\d+) bills\b', text)
    total = re.search(r'\bamount to (q\d+)\b', text)
    ratio = re.search(r'\bnumber of (q\d+) bills is ('+_FACTOR+r') as many (q\d+) bills\b', text)
    requested = re.search(r'\bhow many (q\d+) bills\b', _parts(text)[1])
    if not all((denominations, total, ratio, requested)):
        return None
    if _ids(' '.join((denominations.group(), total.group(), ratio.group(), requested.group()))) != set(range(len(p.numbers))):
        return None
    a, b = _v(ratio.group(1), p), _v(ratio.group(3), p)
    if a == b or {a, b} != {_v(denominations.group(1), p), _v(denominations.group(2), p)}:
        return None
    asked, k = _v(requested.group(1), p), _factor(ratio.group(2), p)
    if asked not in (a, b) or a <= 0 or b <= 0 or k <= 0:
        return None
    return _v(total.group(1), p)/(a*k+b)*(k if asked == a else 1), 'Use the count ratio and denomination values to divide the total value.'


def _weighted_prices(p):
    text = _tokens(p)
    counts = re.search(r'\b(q\d+) ([a-z]+) and (q\d+) ([a-z]+)\b', text)
    ratio = re.search(r"\bprice of (?:an?|the) ([a-z]+) ([a-z]+) is ("+_FACTOR+r") that of (?:an?|the) ([a-z]+)'s \2\b", text)
    total = re.search(r'\btotal amount collected is (q\d+)\b', text)
    if not all((counts, ratio, total)) or _ids(' '.join((counts.group(), ratio.group(), total.group()))) != set(range(len(p.numbers))):
        return None
    quantities = {_singular(counts.group(2)): _v(counts.group(1), p), _singular(counts.group(4)): _v(counts.group(3), p)}
    left, right = ratio.group(1), ratio.group(4)
    if left == right or set(quantities) != {left, right}:
        return None
    k = _factor(ratio.group(3), p)
    denominator = quantities[left]*k+quantities[right]
    requested = [node for node in (left, right) if re.search(r'\b'+re.escape(node)+r'\b', p.question)]
    if len(requested) != 1 or denominator <= 0:
        return None
    return _v(total.group(1), p)/denominator*(k if requested[0] == left else 1), 'Use the price ratio and the two group counts to divide the total revenue.'


def solve(problem):
    if any(n.kind == 'percent' for n in problem.numbers):
        return None
    if not re.search(r'\b(?:twice|thrice|double|triple|times|more|less|fewer|older|younger)\b', problem.body):
        return None
    for reader in (_grouped_left, _self_age, _range_score, _payment_balance,
                   _fixed_share, _allocated_stock, _capacity, _repeat_order,
                   _destinations, _rectangle, _scaled_age, _converted_chain,
                   _partition_ratio, _compared_servings, _deletion_limit,
                   _container_categories, _original_stock, _future_sibling_sum,
                   _rectangle_area, _remaining_category, _implicit_remainder,
                   _repeated_groups, _two_numbers, _event_age_ratio, _scaled_speed,
                   _activity_total, _located_duration, _relative_birth_year,
                   _simple_pair_total, _maximum_from_minimum, _rate_capacity,
                   _diameter_radius, _calendar_frequency, _daily_compared_time,
                   _event_frequency_sum, _frequency_ratio, _implicit_difference,
                   _numeric_measure_comparison, _bill_counts, _weighted_prices,
                   _implicit_pair, _adapted):
        result = reader(problem)
        if result is not None:
            return result
    return None
