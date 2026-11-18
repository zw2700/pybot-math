"""Compositional counts: explicit rate chains, grouped totals and stock changes.

Each schema consumes the quantities through stated relations.  Unresolved
references, incompatible units and incomplete ledgers deliberately abstain.
"""
import re
from fractions import Fraction

from ..numbers import format_number
from ._counting_common import answer as _answer, total as _sum, fmt as _fmt, tokenize as _tokenize, products as _products
from ..problem import Problem
from ._counting_groups import container_relations
from .counting_and_totals_r00_a1 import _different_owner
from .counting_and_totals_r02_a4 import _head, _asked as _base_asked, _normal_unit
from .rates_and_unit_rates_r01_a4 import _convert, _sentence


def _has(pattern, text):
    return re.search(pattern, text) is not None


def _unit(tail):
    # These words begin predicates rather than modify a count noun.
    measure = re.match(r'\s*-?\s*(yards?|oz|ml)\b', tail)
    if measure:
        return {'oz': 'ounce', 'ml': 'milliliter'}.get(measure.group(1), _normal_unit(measure.group(1)))
    compound = re.match(r'\s+([a-z]+)-([a-z]+)\b',tail)
    if compound and compound.group(2).endswith('s'):
        return compound.group(1)+_normal_unit(compound.group(2))
    tail = re.split(r'\b(?:free|receive|received|riding|combine|combined|match|matches|equally|farther|daily|took|climbed|hopped|burns?|stolen|pop)\b', tail)[0]
    value = _head(tail)
    return {'seat': 'chair'}.get(value, value)


def _asked(p):
    if _has(r'\b(?:total (?:length of )?time|how much time|how long)\b', p.question):
        return 'time'
    value = _base_asked(p)
    return {'seat': 'chair'}.get(value, value)


def _other_owner(p):
    if _different_owner(p):
        return True
    query=re.search(r'\b(?:does|did|will|can) ([A-Z][a-z]+)\b',p.text[len(p.body):])
    owners=re.findall(r'\b([A-Z][a-z]+) (?:bought|purchased|ordered|collected|had|has|harvests|makes)\b',p.text[:p.numbers[0].start])
    return bool(query and owners and query.group(1)!=owners[-1])


_TIME = {'second', 'minute', 'hour', 'day', 'week', 'month', 'year'}


def _rate_chain(p):
    """A single dimensional chain, including explicit repetitions per period."""
    text = p.text.lower()
    if _has(r'\b(?:than|more|less|fewer|half|twice|left|remaining|lost|gave|'
            r'percent|except|another|including|back|round|weekdays?|weekends?)\b', text):
        return None
    ns = p.numbers
    if not 2 <= len(ns) <= 6:
        return None
    units, denominators = [], []
    for i, n in enumerate(ns):
        end = ns[i+1].start if i+1 < len(ns) else len(text)
        tail = re.split(r'[.!?;](?:\s|$)', text[n.end:end])[0]
        unit = _unit(tail)
        # A repetition count has the dimension of an event.
        if re.match(r'\s+times\b', tail):
            unit = 'event'
        units.append(unit)
        m = re.search(r'\b(?:per|each|every|a|an)\s+([a-z]+)\b', tail)
        denominator = _normal_unit(m.group(1)) if m else None
        if denominator in ('of', 'the', 'same'):
            return None
        denominators.append(denominator)
    # "N objects, M times a day" repeats the preceding object count.
    for i in range(1, len(ns)):
        if units[i] == 'event' and denominators[i] and denominators[i-1] is None:
            middle = text[ns[i-1].end:ns[i].start]
            if not _has(r'[.!?;]', middle):
                denominators[i-1] = 'event'
    values = [n.value for n in ns]
    # A named activity performed "N times" supplies its own group unit.
    for i, n in enumerate(ns):
        if units[i] == 'event':
            before = re.search(r'\b([a-z]+)\s*$', text[:n.start])
            if before and before.group(1) in denominators:
                units[i] = before.group(1)
    # Implicit singular durations are units, not a guessed multiplier.
    implicit = re.search(r'\b(?:in|for|during|over)\s+(a|an|one)\s+(week|day|hour|month|year)\b', p.question)
    if implicit and not any(n.start >= len(p.body) for n in ns):
        values.append(Fraction(1))
        units.append(implicit.group(2))
        denominators.append(None)
    elif not any(n.start >= len(p.body) for n in ns):
        period = re.search(r'\b(?:per|each|every|a) (day|week|month|year)\b', p.question)
        if period and period.group(1) in denominators:
            values.append(Fraction(1))
            units.append(period.group(1))
            denominators.append(None)
    if not all(units) or not any(denominators):
        return None
    parents = {}
    for i, denominator in enumerate(denominators):
        if not denominator:
            continue
        candidates = []
        for j, unit in enumerate(units):
            if j == i:
                continue
            factor = _convert(Fraction(1), unit, denominator)
            if factor is not None:
                candidates.append((j, factor))
        exact = [c for c in candidates if units[c[0]] == denominator]
        if len(exact) == 1:
            candidates = exact
        elif len(candidates) > 1:
            linked = [c for c in candidates if denominators[c[0]]]
            if len(linked) == 1:
                candidates = linked
        if len(candidates) != 1:
            return None
        parents[i] = candidates[0]
    consumed = {j for j, factor in parents.values()}
    roots = set(range(len(values))) - consumed
    if len(roots) != 1 or len(consumed) != len(parents):
        return None
    root = next(iter(roots))
    asked = _asked(p)
    event_query = False
    if units[root] == 'event' and root < len(ns):
        verb = re.search(r'\b([a-z]+)\s*$',text[:ns[root].start])
        event_query = bool(verb and _normal_unit(verb.group(1)) == asked)
    if units[root] != asked and not event_query:
        # "Amount of airflow" may ask for a quantity introduced as
        # "an airflow of N liters". Require that explicit noun-to-unit link.
        prefix = text[:ns[root].start] if root < len(ns) else ''
        if not asked or not re.search(r'\b'+re.escape(asked)+r'\s+of\s*$', prefix):
            return None
    terms = _products(values, parents, order='rate_first')
    if terms is None or len(terms) != 1:
        return None
    _, value, expression = terms[0]
    return _answer(value, expression)


def _paired_groups(p):
    """Two independently described groups, queried as a sum or difference."""
    text = p.text.lower()
    if _has(r'\b(?:half|twice|percent|ratio|except|remaining|left)\b', text):
        return None
    ns = list(p.numbers)
    removed = None
    # "The two friends" refers back to the two described participants.
    if len(ns) == 5 and ns[-1].start >= len(p.body) and ns[-1].value == 2:
        if re.match(r'\s+(?:friends|people|workers|students)\s+(?:combine|combined|together)\b', text[ns[-1].end:]):
            ns.pop()
    if len(ns) == 5 and ns[-1].start < len(p.body):
        last = ns[-1]
        sentence = _sentence(text, last)
        if (_unit(text[last.end:]) == _asked(p) or re.match(r'\s+of (?:the|these|those)\b', text[last.end:])) and _has(r'\b(?:pop|popped|burst|lost|removed|broke)\b', sentence):
            removed = last.value
            ns.pop()
    if len(ns) != 4:
        return None
    units = [_unit(text[n.end:]) for n in ns]
    asked = _asked(p)
    if asked == 'time':
        measures = set(units) & {'minute', 'hour', 'second'}
        if len(measures) != 1:
            return None
        asked = next(iter(measures))
    terms = []
    for i, j in ((0, 1), (2, 3)):
        a, b = ns[i], ns[j]
        middle = text[a.end:b.start]
        tail = text[b.end:]
        # Counted containers with content per container.
        m = re.search(r'\b(?:each|per|every)\s+([a-z]+)', re.split(r'[.!?;]', tail)[0])
        group_match = m and _normal_unit(m.group(1)) == units[i]
        content = re.fullmatch(r'\s+[a-z]+(?: of [a-z ]+?)? (?:with|of)\s+', middle)
        content = content or re.fullmatch(r'\s+[a-z]+ (?:that )?each (?:weighs?|has|have|contains?|holds?)\s+', middle)
        cut = re.search(r'\bcut(?:s)? (?:each |the )?'+re.escape(units[i])+r' into\s*$', middle)
        content = content or cut
        # "N of his walls are M meters wide" is a measured group.
        content = content or re.fullmatch(r'\s+(?:of (?:his|her|the|their) )?[a-z]+ are\s+', middle)
        period = re.search(r'\b(?:each|per|every|a)\s+(day|week|month|hour|minute)\b', middle)
        rate_time = period and units[j] in _TIME
        if not (((group_match or content) and units[j] == asked) or (rate_time and units[i] == asked)):
            return None
        if rate_time and units[i] == asked:
            elapsed = _convert(b.value,units[j],period.group(1))
            if elapsed is None:
                return None
            terms.append(a.value*elapsed)
        else:
            terms.append(a.value*b.value)
    if _has(r'\b(?:more|fewer|difference)\b', p.question):
        if removed is not None:
            return None
        # Explicit comparison queries ask for the magnitude between groups.
        return _answer(abs(terms[0]-terms[1]), '|' + _fmt(terms, ' - ') + '|')
    if not _has(r'\b(?:total|combine|combined|together|altogether|in all)\b', p.question):
        same_owner = (not _has(r'[.!?;]', text[ns[0].start:ns[-1].end])
                      and _has(r'\band\b', text[ns[1].end:ns[2].start])
                      and not _has(r'\b(?:has|have|had)\b', text[ns[1].end:ns[2].start]))
        if not same_owner:
            return None
    if removed is not None:
        return _answer(_sum(terms)-removed, _fmt(terms)+' - '+format_number(removed))
    return _answer(_sum(terms), _fmt(terms))


def _stock_ledger(p):
    """Multiple categories and explicit transfers into or out of one stock."""
    ns = p.numbers
    text = p.text.lower()
    if _other_owner(p):
        return None
    if not 3 <= len(ns) <= 7 or any(n.start >= len(p.body) for n in ns):
        return None
    transit = _has(r'\b(?:get|gets|got) (?:on|off)\b',p.body)
    if not _has(r'\b(?:left|remaining|now)\b', p.question) and not transit:
        return None
    if _has(r'\b(?:each|every|per|than|times|half|twice|percent|some|rest|broken)\b', text):
        return None
    asked = re.match(r'how many (.+?) (?:are|were|is|does|do|did|has|have|will)\b', p.question)
    if not asked:
        return None
    categories = {_head(s) for s in asked.group(1).split(' and ')}
    if '' in categories:
        return None
    totals = {}
    signs, previous = [], None
    for i, n in enumerate(ns):
        after = text[n.end:ns[i+1].start if i+1 < len(ns) else len(p.body)]
        before = text[ns[i-1].end if i else 0:n.start]
        unit = _unit(after)
        # "N of these biscuits" points to an already established category.
        if not unit and re.match(r'\s+of (?:these|those|the)\b', after) and len(totals) == 1:
            unit = next(iter(totals))
        if not unit and re.match(r'\s*[,.;]',after) and len(totals)==1:
            unit=next(iter(totals))
        if unit not in categories:
            return None
        clause = re.split(r'[.!?;]|\b(?:but|then)\b', before)[-1]
        incoming = re.search(r'\b(?:gave|gives?|given)\s+(?:him|her|them|me|us)\s*$', clause)
        outgoing = re.search(r'\b(?:ate|eats?|lost|loses?|sold|sells?|used|uses|removed|quit|gave|gives?|misplaced|broke|took)\b', clause)
        sentence_end = re.split(r'[.!?;]', text[n.end:len(p.body)])[0]
        post = re.search(r'\b(?:quit|were removed)\s*,?\s*$', sentence_end)
        transition = re.match(r'\s+(?:more )?[a-z]+(?: more)? (?:get|gets|got) (on|off)\b',after)
        start = re.search(r'\b(?:has|have|had|there are|there were|bought|buys?|purchased|found|received|gets?|got|added)\b', clause)
        if transition:
            sign = -1 if transition.group(1)=='off' else 1
        elif incoming:
            sign = 1
        elif outgoing or post:
            sign = -1
        elif start:
            sign = 1
        elif previous is not None and not _has(r'[.!?;]', before) and _has(r'\band\b', before):
            sign = previous
        else:
            return None
        previous = sign
        totals[unit] = totals.get(unit, Fraction(0)) + sign*n.value
        signs.append(sign)
    if -1 not in signs or set(totals) != categories or any(v < 0 for v in totals.values()):
        return None
    expr = ''.join((' - ' if sign < 0 else ' + ') + format_number(n.value)
                   for n, sign in zip(ns, signs)).lstrip(' +')
    return _answer(_sum(totals.values()), expr)


def _converted_stock(p):
    """Dozens/pairs minus explicit individual removals."""
    ns = p.numbers
    text = p.text.lower()
    if not 2 <= len(ns) <= 5 or not _has(r'\b(?:left|still|mismatching|unmatched)\b', p.question):
        return None
    first = ns[0]
    m = re.match(r'\s+(dozen|pairs?)(?: of)?\s+([a-z]+)', text[first.end:])
    if m:
        unit = _normal_unit(m.group(2))
        stock = first.value*(12 if m.group(1) == 'dozen' else 2)
        rest = ns[1:]
        if _asked(p) != unit:
            return None
        # Each buyer receives one of the stock items.
        if _has(r'\bbuy (?:a|one) '+re.escape(unit)+r' each\b', p.body):
            if any(not _head(text[n.end:]) for n in rest):
                return None
            return _answer(stock-_sum(n.value for n in rest), '{} - ({})'.format(format_number(stock), _fmt(n.value for n in rest)))
    if len(ns) == 2 and _has(r'\b(?:mismatching|unmatched|don\'t match|do not match)\b', text):
        m = re.match(r'\s+pairs? of ([a-z]+)\b', text[ns[1].end:])
        if m and _head(text[first.end:]) == _normal_unit(m.group(1)):
            return _answer(first.value-2*ns[1].value, '{} - 2 x {}'.format(format_number(first.value), format_number(ns[1].value)))
    return None


def _remaining_reading(p):
    """Total work minus prior work and work at a stated daily rate."""
    ns = p.numbers
    if len(ns) != 3 or not _has(r'\b(?:left|remaining)\b', p.question):
        return None
    text = p.text.lower()
    units = [_head(text[n.end:]) for n in ns]
    if not units[0] or len(set(units)) != 1 or _asked(p) != units[0]:
        return None
    if not _has(r'\balready\b', text[ns[0].end:ns[1].start]):
        return None
    tail = text[ns[2].end:]
    if not _has(r'\b(?:per|a|each) day for (?:a|one) week\b', tail):
        return None
    return _answer(ns[0].value-ns[1].value-7*ns[2].value,
                   '{} - {} - 7 x {}'.format(*(format_number(n.value) for n in ns)))


def _arithmetic_schedule(p):
    """N sessions, an initial amount, and a fixed increment each session."""
    ns = p.numbers
    if len(ns) != 3 or not _has(r'\b(?:total|altogether)\b', p.question):
        return None
    text = p.text.lower()
    count, initial, delta = ns
    if not re.match(r'\s+times (?:a|per|each) week\b', text[count.end:]):
        return None
    if not _has(r'\bfirst day\b', text[count.end:initial.start]):
        return None
    if not _has(r'\b(?:add|increase)\b', text[initial.end:delta.start]):
        return None
    if not re.match(r'\s+more [a-z-]+ each day\b', text[delta.end:]):
        return None
    if _head(text[initial.end:]) != _asked(p) or count.value.denominator != 1:
        return None
    n, a, d = (q.value for q in ns)
    return _answer(n*a+n*(n-1)*d/2, '{} x {} + {} x ({} - 1) x {} / 2'.format(*map(format_number, (n,a,n,n,d))))


def _labelled_products(p):
    """Join independently stated per-category contents to category counts."""
    if len(p.numbers) != 4:
        return None
    token = _tokenize(p)
    ns = p.numbers
    asked = _asked(p)
    if not asked or _has(r'\b(?:half|twice|left|remaining|percent|except)\b', token):
        return None
    rates = {}
    # A category subject must explicitly contain/need the asked-for unit.
    pattern = r'\b([a-z]+) (?:has|have|needs?|requires?|contains?|holds?) Q(\d+)'
    for m in re.finditer(pattern, token):
        group, index = m.groups()
        content = token[m.end():]
        index = int(index)
        if _unit(content) != asked:
            return None
        key = _unit(group)
        if not key or key in rates:
            return None
        rates[key] = index
    if len(rates) != 2:
        return None
    rate_ids = set(rates.values())
    terms = []
    groups_seen = set()
    for i, n in enumerate(ns):
        if i in rate_ids:
            continue
        end = ns[i+1].start if i+1 < len(ns) else len(p.text)
        tail = re.split(r'[.!?;,]', p.text.lower()[n.end:end])[0]
        candidates = [group for group in rates if re.search(r'\b'+re.escape(group)+r'(?:s|es)?\b', tail)]
        # Counts of riders explicitly identify their vehicle group.
        if len(candidates) != 1:
            return None
        group = candidates[0]
        if group in groups_seen:
            return None
        groups_seen.add(group)
        terms.append(n.value*ns[rates[group]].value)
    if groups_seen != set(rates):
        return None
    mentioned = {g for g in rates if re.search(r'\b'+re.escape(g)+r'(?:s|es)?\b',p.question)}
    if mentioned and mentioned != set(rates):
        return None
    if _has(r'\b(?:more|fewer|difference)\b', p.question):
        return _answer(abs(terms[0]-terms[1]), '|' + _fmt(terms, ' - ') + '|')
    return _answer(_sum(terms), _fmt(terms))


def _category_multipliers(p):
    """Different multiplicative comparisons for disjoint named categories."""
    if len(p.numbers) != 4:
        return None
    text = p.text.lower()
    factors, known = {}, {}
    for n in p.numbers:
        m = re.match(r'\s+times the number of ([a-z]+)\b', text[n.end:])
        if m:
            key = _normal_unit(m.group(1))
            if key in factors:
                return None
            factors[key] = n.value
        else:
            key = _unit(text[n.end:])
            if not key or key in known:
                return None
            known[key] = n.value
    if len(factors) != 2 or set(factors) != set(known):
        return None
    if any(not re.search(r'\b'+re.escape(k)+r'(?:s|es)?\b', p.question) for k in factors):
        return None
    # Confirm the question requests the subject with the multiplied amounts.
    subject = re.match(r'\s*([a-z]+) has\b', text)
    if not subject or not _has(r'\b'+re.escape(subject.group(1))+r'\b', p.question):
        return None
    terms = [factors[k]*known[k] for k in factors]
    return _answer(_sum(terms), _fmt(terms))


def _host_supply(p):
    """Guests plus the host, servings each, and quantity per serving."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or not _has(r'\bincluding (?:himself|herself|myself|the host)\b', p.body):
        return None
    guests, servings, size = ns
    if (not _unit(text[guests.end:])
            or not re.search(r'\b(?:invit(?:es?|ed|ing)|host(?:s|ed|ing)?|'
                             r'welcom(?:es?|ed|ing))\s*$', text[:guests.start])):
        return None
    if not _has(r'\b(?:everyone|each person|every person)\b', text[guests.end:servings.start]):
        return None
    container = _unit(text[servings.end:])
    if not container or _unit(text[size.end:]) != _asked(p):
        return None
    if not re.search(r'\beach '+re.escape(container)+r' (?:holds?|contains?|has)\s*$', text[:size.start]):
        return None
    value = (guests.value+1)*servings.value*size.value
    return _answer(value, '({} + 1) x {} x {}'.format(*(format_number(n.value) for n in ns)))


def _net_population(p):
    """Recover an initial population from final stock and net periodic change."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 4 or not _has(r'\bat first\b', p.question):
        return None
    born, died, final, duration = ns
    if not _has(r'\b(?:born|added)\b.{0,30}$', text[:born.start]):
        return None
    if not _has(r'\b(?:die|dies|removed)\b.{0,30}$', text[born.end:died.start]):
        return None
    periods = []
    for n in (born, died):
        m = re.match(r'\s+per (day|week|month|year)\b', text[n.end:])
        if not m:
            return None
        periods.append(m.group(1))
    if periods[0] != periods[1] or not _has(r'\bafter\s*$', text[final.end:duration.start]):
        return None
    unit = _unit(text[duration.end:])
    elapsed = _convert(duration.value, unit, periods[0])
    if elapsed is None:
        return None
    return _answer(final.value-(born.value-died.value)*elapsed,
                   '{} - ({} - {}) x {}'.format(*map(format_number, (final.value,born.value,died.value,elapsed))))


def _perimeters(p):
    """Combine a square boundary and a rectangular boundary."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or not _has(r'\b(?:fence|fencing|perimeter)\b', text):
        return None
    if not _has(r'\b(?:together|total|combined|altogether)\b', p.question):
        return None
    if not _has(r'\bsquare\b.{0,45}(?:side length|side|length) of\s*$', text[:ns[0].start]):
        return None
    if not re.fullmatch(r'\s+[a-z]+ by\s+', text[ns[1].end:ns[2].start]):
        return None
    units = [_unit(text[n.end:]) for n in ns]
    if len(set(units)) != 1 or units[0] != _asked(p):
        return None
    a,b,c = (n.value for n in ns)
    return _answer(4*a+2*(b+c), '4 x {} + 2 x ({} + {})'.format(*map(format_number,(a,b,c))))


def _capacity_distance(p):
    """A full resource capacity times efficiency, less distance travelled."""
    if len(p.numbers) != 3:
        return None
    text = p.text.lower()
    if not _has(r'\b(?:fill|fills|filled)\b', p.body) or not _has(r'\b(?:more|remaining) miles\b', p.question):
        return None
    trip, efficiency, capacity = p.numbers
    if _unit(text[trip.end:]) != 'mile':
        return None
    m = re.match(r'\s+miles (?:to the|per|a) (gallon|liter)\b', text[efficiency.end:])
    if not m or not re.match(r'-'+m.group(1)+r'\b', text[capacity.end:]):
        return None
    if not _has(r'\b(?:tank|capacity)\b', text[capacity.end:]):
        return None
    return _answer(efficiency.value*capacity.value-trip.value,
                   '{} x {} - {}'.format(*map(format_number,(efficiency.value,capacity.value,trip.value))))


def _shared_rate_difference(p):
    """Two per-unit amounts compared over the same explicit number of units."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or not _has(r'\b(?:longer|shorter|more|fewer|difference)\b', p.question):
        return None
    a, b, count = ns
    unit = _unit(text[a.end:])
    if not unit or _unit(text[b.end:]) != unit or _asked(p) != unit:
        return None
    group = _unit(text[count.end:])
    if not group:
        return None
    for n in (a, b):
        sentence = _sentence(text, n)
        if not re.search(r'\b(?:per|each|a|an) '+re.escape(group)+r'\b', sentence):
            return None
    return _answer(abs(a.value-b.value)*count.value,
                   '|{} - {}| x {}'.format(*(format_number(n.value) for n in ns)))


def _ratio_groups(p):
    """Two ratio parts with either a difference or a total and a removal."""
    ns = p.numbers
    token = _tokenize(p)
    if len(ns) not in (3, 4) or not _has(r'\bratio\b', p.body):
        return None
    pair = re.search(r'Q(\d+)\s*:\s*Q(\d+)', token)
    if not pair:
        return None
    i, j = map(int, pair.groups())
    if (i,j) != (0,1):
        return None
    a,b = ns[0].value, ns[1].value
    if a == b:
        return None
    if len(ns) == 3:
        tail = p.text.lower()[ns[2].end:]
        if not re.match(r'\s+more [a-z]+ than [a-z]+', tail):
            return None
        groups = re.search(r'ratio of ([a-z]+) to ([a-z]+)', p.body)
        if not groups or any(_normal_unit(g) == _asked(p) for g in groups.groups()):
            return None
        value = (a+b)*ns[2].value/abs(a-b)
        return _answer(value, '({} + {}) x {} / |{} - {}|'.format(*map(format_number,(a,b,ns[2].value,a,b))))
    groups = re.search(r'\b([a-z]+) and ([a-z]+) in the ratio', p.body)
    if not groups or not _has(r'\btotal\b', p.body[ns[1].end:ns[2].start]):
        return None
    labels = [_normal_unit(g) for g in groups.groups()]
    removed_unit = _unit(p.text.lower()[ns[3].end:])
    if removed_unit not in labels or removed_unit != _asked(p):
        return None
    if not _has(r'\b(?:gives?|gave|removed)\b', p.body[ns[2].end:ns[3].start]):
        return None
    share = (a,b)[labels.index(removed_unit)]
    return _answer(ns[2].value*share/(a+b)-ns[3].value,
                   '{} x {} / ({} + {}) - {}'.format(*map(format_number,(ns[2].value,share,a,b,ns[3].value))))


def _equal_share_subgroup(p):
    """Equal shares among two groups; ask the combined share of one group."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or not _has(r'\bequally (?:among|between)\b', p.body):
        return None
    a,b,total = ns
    if not _has(r'\band\b', text[a.end:b.start]):
        return None
    labels = [_unit(text[n.end:]) for n in (a,b)]
    if not all(labels) or labels[0] == labels[1] or _unit(text[total.end:]) != _asked(p):
        return None
    selected = [i for i,label in enumerate(labels) if re.search(r'\b'+re.escape(label)+r'(?:s|es)?\b', p.question)]
    if len(selected) != 1:
        return None
    count = (a,b)[selected[0]].value
    return _answer(total.value*count/(a.value+b.value), '{} x {} / ({} + {})'.format(*map(format_number,(total.value,count,a.value,b.value))))


def _rectangle_area(p):
    """Find the other side from a rectangle's perimeter, then its area."""
    ns = p.numbers
    if len(ns) != 2 or not _has(r'\brectangle\b', p.body) or not _has(r'\barea\b', p.question):
        return None
    text = p.text.lower()
    side, perimeter = ns
    if not _has(r'\b(?:wide|long|width|length)\b', text[side.end:perimeter.start]):
        return None
    if not _has(r'\bperimeter\b.{0,15}$', text[:perimeter.start]):
        return None
    if not _unit(text[side.end:]) or _unit(text[side.end:]) != _unit(text[perimeter.end:]):
        return None
    a,b = side.value, perimeter.value
    return _answer(a*(b/2-a), '{} x ({} / 2 - {})'.format(*map(format_number,(a,b,a))))


def _grouped_partition(p):
    """The total is a number of equal groups; subtract known categories."""
    ns = p.numbers
    if len(ns) != 4 or not _has(r'\bsome\b', p.body):
        return None
    text = p.text.lower()
    a,b,groups,size = ns
    unknown = re.search(r'\bsome ([a-z]+)', p.body)
    if not unknown or _normal_unit(unknown.group(1)) != _asked(p):
        return None
    if not _has(r'\ball of them\b', text[b.end:groups.start]):
        return None
    description = re.match(r'\s+(?:equally[- ]sized )?([a-z]+) of\b',text[groups.end:])
    group = _normal_unit(description.group(1)) if description else _unit(text[groups.end:])
    if not group or not re.search(r'\bper '+re.escape(group)+r'\b', text[size.end:]):
        return None
    if not _has(r'\b(?:equally|equal|same)\b', text[b.end:size.start]):
        return None
    return _answer(groups.value*size.value-a.value-b.value,
                   '{} x {} - {} - {}'.format(*map(format_number,(groups.value,size.value,a.value,b.value))))


def _converted_inventory(p):
    """Changes in container counts followed by explicit uniform contents."""
    ns = list(p.numbers)
    text = p.text.lower()
    if _other_owner(p):
        return None
    if not 4 <= len(ns) <= 7 or not _has(r'\b(?:now|left|remaining)\b', p.question):
        return None
    size = ns[-1]
    if _unit(text[size.end:]) != _asked(p):
        return None
    prefix = text[:size.start]
    group_match = re.search(r'\b(?:each|one|a|an) ([a-z]+) (?:holds?|contains?|has)\s*$', prefix)
    if not group_match:
        return None
    group = _normal_unit(group_match.group(1))
    counts = ns[:-1]
    if counts[-1].value == 1 and counts[-1].start >= group_match.start():
        counts.pop()
    if len(counts) < 2 or any(_unit(text[n.end:]) != group for n in counts):
        return None
    amounts = []
    for i,n in enumerate(counts):
        before = text[counts[i-1].end if i else 0:n.start]
        before = re.split(r'[.!?;]', before)[-1]
        verbs = list(re.finditer(r'\b(bought|buys?|got|received|gave|gives?|sold|lost|used)\b', before))
        if not verbs:
            return None
        sign = -1 if verbs[-1].group() in ('gave','give','gives','sold','lost','used') else 1
        amounts.append(sign*n.value)
    if not any(v < 0 for v in amounts):
        return None
    return _answer(_sum(amounts)*size.value,
                   '({}) x {}'.format(_fmt(amounts),format_number(size.value)))


def _production_remainder(p):
    """Daily production for a duration, followed by individual removals."""
    ns = p.numbers
    text = p.text.lower()
    if _other_owner(p):
        return None
    if len(ns) not in (3,4) or not _has(r'\b(?:have|left|remaining)\b', p.question):
        return None
    rate, duration = ns[:2]
    asked = _asked(p)
    if _unit(text[rate.end:]) != asked or _unit(text[duration.end:]) != 'day':
        return None
    if not _has(r'\b(?:daily|each day|every day|per day|a day)\b', text[rate.end:duration.start]):
        return None
    losses = []
    opening = []
    for i,n in enumerate(ns[2:],2):
        before = text[ns[i-1].end:n.start]
        if re.search(r'\b(?:started|began) [^.!?;]*with\s*$',before):
            if _unit(text[n.end:]) != asked or opening:
                return None
            opening.append(n.value)
            continue
        if _unit(text[n.end:]) != asked or not _has(r'\b(?:gives? away|gave|stolen|used|lost|sold)\b', _sentence(text,n)):
            return None
        losses.append(n.value)
    return _answer(rate.value*duration.value+_sum(opening)-_sum(losses),
                   '{} x {}{} - ({})'.format(format_number(rate.value),format_number(duration.value),
                       ' + '+_fmt(opening) if opening else '',_fmt(losses)))


def _mixed_daily_time(p):
    """A compound hours-and-minutes duration repeated each day."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or not _has(r'\b(?:every|each|per) day\b', p.body):
        return None
    a,b,duration = ns
    if _unit(text[a.end:]) != 'hour' or _unit(text[b.end:]) != 'minute':
        return None
    if _sentence(text,a) != _sentence(text,b) or duration.start < len(p.body):
        return None
    target = re.search(r'\bin (hours?|minutes?)\b', p.question)
    days = _convert(duration.value,_unit(text[duration.end:]),'day')
    if not target or days is None:
        return None
    target = _normal_unit(target.group(1))
    value = (_convert(a.value,'hour',target)+_convert(b.value,'minute',target))*days
    return _answer(value,'Daily duration converted to '+target+' x '+format_number(days))


def _weekday_schedule(p):
    """An amount each weekday plus one weekend day, over explicit weeks."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or not re.match(r'\s+[a-z]+ every weekday\b', text[ns[0].end:]):
        return None
    if _unit(text[ns[0].end:]) != _unit(text[ns[1].end:]) or _unit(text[ns[0].end:]) != _asked(p):
        return None
    if not _has(r'\bon saturdays\b', text[ns[0].end:ns[1].start]) or not _has(r'\bsundays off\b', p.body):
        return None
    if _unit(text[ns[2].end:]) != 'week' or ns[2].start < len(p.body):
        return None
    a,b,weeks = (n.value for n in ns)
    return _answer((5*a+b)*weeks,'(5 x {} + {}) x {}'.format(*map(format_number,(a,b,weeks))))


def _square_rectangle(p):
    """A square and rectangle measured in the same units, sum or difference."""
    ns = list(p.numbers)
    text = p.text.lower()
    if len(ns) == 4 and ns[-1].start >= len(p.body) and ns[-1].value == 2 and re.match(r'\s+shapes\b',text[ns[-1].end:]):
        ns.pop()
    if len(ns) != 3 or not _has(r'\barea\b', p.question):
        return None
    if not _has(r'\brectangle\b', text[:ns[0].start]) or not _has(r'\bsquare\b', text[ns[1].end:ns[2].start]):
        return None
    units = [_unit(text[n.end:]) for n in ns]
    if not units[0] or len(set(units)) != 1:
        return None
    a,b,c = (n.value for n in ns)
    if _has(r'\bdifference\b', p.question):
        return _answer(abs(a*b-c*c),'|{} x {} - {} x {}|'.format(*map(format_number,(a,b,c,c))))
    if _has(r'\b(?:total|combined|together)\b', p.question):
        return _answer(a*b+c*c,'{} x {} + {} x {}'.format(*map(format_number,(a,b,c,c))))
    return None


def _overlap(p):
    """Two counted sets with an explicitly counted intersection."""
    ns = list(p.numbers)
    text = p.text.lower()
    ns = [n for n in ns if not (n.value == 1 and re.match(r'\s+or more\b',text[n.end:]))]
    if len(ns) != 3 or not _has(r'\b(?:altogether|total|in all|either)\b',p.question):
        return None
    units = [_unit(text[n.end:]) for n in ns]
    if len(set(units)) != 1 or not units[0] or units[0] != _asked(p):
        return None
    intersection = [i for i,n in enumerate(ns) if _has(r'\bboth\b', re.split(r'[.!?;,]',text[n.end:])[0])]
    if intersection != [2] or ns[2].value > min(ns[0].value,ns[1].value):
        return None
    # No unquantified third category or people in neither set.
    if _has(r'\b(?:neither|none|not|other)\b',p.body):
        return None
    a,b,c=(n.value for n in ns)
    return _answer(a+b-c,'{} + {} - {}'.format(*map(format_number,(a,b,c))))


def _category_difference(p):
    """Combine repeated counts of two categories and compare the totals."""
    ns=p.numbers
    text=p.text.lower()
    if not 4 <= len(ns) <= 8 or any(n.start >= len(p.body) for n in ns):
        return None
    if _has(r'\b(?:than|fewer|less|each|per|every|half|times|twice|gave|sold|lost|used)\b',p.body):
        return None
    m=re.match(r'how many more (.+?) (?:did|does|do|are|were|has|have)\b.+?\bthan (.+?)[?!.]?$',p.question)
    if not m:
        return None
    first,second=(_unit(s) for s in m.groups())
    if not first or not second or first == second:
        return None
    totals={first:Fraction(0),second:Fraction(0)}
    for n in ns:
        unit=_unit(text[n.end:])
        if unit not in totals:
            return None
        totals[unit]+=n.value
    return _answer(totals[first]-totals[second], '{} - {}'.format(format_number(totals[first]),format_number(totals[second])))


def _dozen_sum(p):
    """Add individuals and dozens of the explicitly requested count noun."""
    ns=p.numbers
    text=p.text.lower()
    asked=_asked(p)
    if not asked or not 2 <= len(ns) <= 6 or not _has(r'\bdozen\b',p.body):
        return None
    if _has(r'\b(?:than|fewer|less|each|per|every|half|times|twice|gave|sold|lost|used|left)\b',text):
        return None
    values=[]
    for i,n in enumerate(ns):
        tail=text[n.end:ns[i+1].start if i+1<len(ns) else len(p.body)]
        words=re.findall(r'[a-z]+',tail)[:4]
        if not any(_normal_unit(w)==asked for w in words):
            return None
        values.append(n.value*(12 if words and words[0]=='dozen' else 1))
    return _answer(_sum(values),_fmt(values))


def _nested_containers(p):
    """Follow an explicit chain of containers, contents and a final count."""
    ns=p.numbers
    text=p.text.lower()
    if not 3 <= len(ns) <= 5 or any(n.start>=len(p.body) for n in ns):
        return None
    if _has(r'\b(?:than|more|fewer|less|half|twice|lost|gave|sold|left|remaining|percent|per)\b',text):
        return None
    units=[_unit(text[n.end:]) for n in ns]
    for i,n in enumerate(ns):
        m=re.search(r'\bnumber of ([a-z]+)(?: [a-z ]+)? is\s*$',text[:n.start])
        if m:
            units[i]=_normal_unit(m.group(1))
    relations = container_relations(p, _unit, units, singular=True, postposed=False)
    if relations is None:
        return None
    parents, references = relations
    if references:
        return None
    if len(parents)!=len(ns)-1 or len(set(parents.values()))!=len(parents):
        return None
    roots=set(range(len(ns)))-set(parents.values())
    if len(roots)!=1:
        return None
    root=next(iter(roots))
    if units[root]!=_asked(p):
        return None
    terms = _products([n.value for n in ns],
                      {i: (j, Fraction(1)) for i, j in parents.items()})
    if terms is None or len(terms) != 1:
        return None
    _, value, _ = terms[0]
    sides=2 if _has(r'\b(?:each opposite side|both sides)\b',text) else 1
    return _answer(value*sides,_fmt([n.value for n in ns]+([Fraction(2)] if sides==2 else []),' x '))


def _dozens(p):
    """Convert dozens locally, then reuse the existing counting readers."""
    text=p.text
    if not _has(r'\bdozen\b',text.lower()):
        return None
    for n in reversed(p.numbers):
        m=re.match(r'\s+dozen\b',text[n.end:],re.I)
        if m:
            text=text[:n.start]+format_number(12*n.value)+text[n.end+m.end():]
    text=re.sub(r'\ba dozen\b','12',text,flags=re.I)
    converted=Problem.read(text)
    if converted is None or _has(r'\bdozen\b',converted.text.lower()):
        return None
    from . import counting_and_totals_r00_a1, counting_and_totals_r01_a3
    from . import counting_and_totals_r02_a2, counting_and_totals_r02_a4
    for module in (counting_and_totals_r00_a1,counting_and_totals_r01_a3,
                   counting_and_totals_r02_a2,counting_and_totals_r02_a4):
        result=module.solve(converted)
        if result is not None:
            return result
    return solve(converted) or _dozen_sum(p)


def _shared_rate_sum(p):
    """Two stated rates for the same unit and period, over a common duration."""
    ns=p.numbers
    text=p.text.lower()
    if len(ns)!=3 or not _has(r'\b(?:total|combined|together|altogether)\b',p.question):
        return None
    if _has(r'\b(?:than|more|less|fewer|half|twice|left|remaining|except)\b',text):
        return None
    a,b,count=ns
    group=_unit(text[count.end:])
    asked=_asked(p)
    if not group or not asked:
        return None
    for n in (a,b):
        sentence=_sentence(text,n)
        if not re.search(r'\b(?:per|a|an|each|every) '+re.escape(group)+r'\b',sentence):
            return None
        if _unit(text[n.end:])!=asked:
            # A fronted rate: "points per game is N".
            if not re.search(r'\b'+re.escape(asked)+r'(?:s|es)? per '+re.escape(group)+r' (?:is|are)\s*$',text[:n.start]):
                return None
    return _answer((a.value+b.value)*count.value,'({} + {}) x {}'.format(*(format_number(n.value) for n in ns)))


def _parallel_daily_groups(p):
    """Two populations with different daily rates over the same duration."""
    ns=p.numbers
    text=p.text.lower()
    if len(ns)!=5 or not _has(r'\b(?:total|in all|how many)\b',p.question):
        return None
    if _has(r'\b(?:than|more|less|fewer|half|twice|left|remaining|except|lost|sold)\b',text):
        return None
    c1,r1,c2,r2,duration=ns
    if _unit(text[c1.end:])!=_unit(text[c2.end:]) or _unit(text[duration.end:])!='day':
        return None
    asked=_asked(p)
    if not asked or any(_unit(text[n.end:])!=asked for n in (r1,r2)):
        return None
    for c,r in ((c1,r1),(c2,r2)):
        if not _has(r'\b(?:have|has|each|every)\b',text[c.end:r.start]):
            return None
        if not re.match(r'\s+[a-z]+(?:/day| (?:per|each|every|a) day)\b',text[r.end:]):
            return None
    value=(c1.value*r1.value+c2.value*r2.value)*duration.value
    return _answer(value,'({} x {} + {} x {}) x {}'.format(*(format_number(n.value) for n in ns)))


def _ratio_length(p):
    """Split a stated length into two ratio parts; choose shorter or longer."""
    ns=p.numbers
    text=p.text.lower()
    if len(ns)!=4 or not _has(r'\bratio\b',p.body):
        return None
    whole,parts,a,b=ns
    if parts.value!=2 or not re.match(r'\s+parts\b',text[parts.end:]):
        return None
    if not re.fullmatch(r'\s*:\s*',text[a.end:b.start]):
        return None
    if _has(r'\bshorter\b',p.question):
        selected=min(a.value,b.value)
    elif _has(r'\blonger\b',p.question):
        selected=max(a.value,b.value)
    else:
        return None
    return _answer(whole.value*selected/(a.value+b.value),
                   '{} x {} / ({} + {})'.format(*map(format_number,(whole.value,selected,a.value,b.value))))


def _comparison_categories(p):
    """A known category and consecutive additive category descriptions."""
    ns=p.numbers
    text=p.text.lower()
    if not 3 <= len(ns) <= 5 or any(n.start>=len(p.body) for n in ns):
        return None
    if _has(r'\b(?:each|every|per|times|half|twice|left|remaining|gave|sold|lost|bought)\b',text):
        return None
    known={};last=None;head=None
    for i,n in enumerate(ns):
        end=ns[i+1].start if i+1<len(ns) else len(p.body)
        tail=re.split(r'[.!?;,]',text[n.end:end])[0].strip()
        tail=re.sub(r'\s+and$','',tail)
        m=re.fullmatch(r'(?:(more|less|fewer) )?([a-z]+) ([a-z]+)(?: than ([a-z]+) ([a-z]+))?',tail)
        if not m:
            return None
        direction,color,noun,reference,refnoun=m.groups()
        noun=_normal_unit(noun)
        if head is not None and noun!=head:
            return None
        head=noun
        if direction:
            ref=reference or last
            if ref not in known or (refnoun and _normal_unit(refnoun)!=head):
                return None
            value=known[ref]+n.value*(-1 if direction in ('less','fewer') else 1)
        elif known:
            return None
        else:
            value=n.value
        if color in known or value<0:
            return None
        known[color]=value;last=color
    if _asked(p)!=head:
        # A collective label is explicitly linked to its contents by "a box
        # of X contains ...". Never infer an arbitrary category taxonomy.
        asked=_asked(p)
        if not asked or not re.search(r'\bof (?:[a-z]+ ){0,2}'+re.escape(asked)+r'(?:s|es)? (?:contains?|has|holds?)\b',text[:ns[0].start]):
            return None
    if any(re.search(r'\b'+re.escape(label)+r'\b',p.question) for label in known):
        return None
    return _answer(_sum(known.values()),_fmt(known.values()))


def _qualified_rates(p):
    """Match two disjoint categories by their explicit qualifying labels."""
    ns=p.numbers
    text=p.text.lower()
    if len(ns)!=4 or _has(r'\b(?:left|remaining|half|twice|percent|lost|sold)\b',text):
        return None
    token=_tokenize(p)
    rates=[]
    for m in re.finditer(r'Q(\d+) [a-z ]+? (?:for every|per|for each|in each|on each) ([a-z]+) ([a-z]+)',token):
        rates.append((int(m.group(1)),m.group(2),_normal_unit(m.group(3))))
    if len(rates)!=2 or rates[0][1]==rates[1][1] or rates[0][2]!=rates[1][2]:
        return None
    output=_unit(text[ns[rates[0][0]].end:])
    if not output or _unit(text[ns[rates[1][0]].end:])!=output or _asked(p)!=output:
        return None
    consumed={r[0] for r in rates};terms=[];heads=set()
    for ri,qualifier,group in rates:
        matches=[]
        for i,n in enumerate(ns):
            if i in consumed:
                continue
            m=re.match(r'\s+'+re.escape(qualifier)+r' ([a-z]+)\b',text[n.end:])
            if m:
                matches.append((i,_normal_unit(m.group(1))))
        if len(matches)!=1:
            return None
        ci,head=matches[0];consumed.add(ci);heads.add(head)
        terms.append(ns[ri].value*ns[ci].value)
    if len(consumed)!=len(ns) or len(heads)!=1:
        return None
    mentioned={qualifier for ri,qualifier,group in rates if re.search(r'\b'+re.escape(qualifier)+r'\b',p.question)}
    if mentioned and len(mentioned)!=len(rates):
        return None
    if _has(r'\b(?:more|fewer|difference)\b',p.question):
        return _answer(abs(terms[0]-terms[1]),'|'+_fmt(terms,' - ')+'|')
    return _answer(_sum(terms),_fmt(terms))


def _past_age_sum(p):
    """One current age and the sum of two ages a stated time ago."""
    ns=p.numbers
    text=p.text.lower()
    if len(ns)!=3 or not _has(r'\b(?:today|now)\b',p.question):
        return None
    age,ago,total=ns
    if not re.match(r'\s+years? old\b',text[age.end:]) or not re.match(r'\s+years? ago\b',text[ago.end:]):
        return None
    if not re.search(r'\b(?:sum was|sum of their ages was|combined age was)\s*$',text[:total.start]):
        return None
    owner=re.search(r'\b([a-z]+) is\s*$',text[:age.start])
    if not owner:
        return None
    if (_has(r'\b'+re.escape(owner.group(1))+r'\b',p.question)
            and not _has(r"\b"+re.escape(owner.group(1))+r"'s (?:sister|brother|friend|mother|father|wife|husband)\b",p.question)):
        return None
    if not _has(r'\b(?:sister|brother|friend|mother|father|wife|husband)\b',p.question):
        return None
    return _answer(total.value-age.value+2*ago.value,
                   '{} - {} + 2 x {}'.format(*map(format_number,(total.value,age.value,ago.value))))


def _future_relative_age(p):
    """A future known age, an age difference and another target future age."""
    ns=p.numbers
    text=p.text.lower()
    if len(ns)!=4 or not _has(r'^how many years\b',p.question):
        return None
    age,shift,delta,target=ns
    if not re.match(r'\s+years old in\s+',text[age.end:]):
        return None
    if not re.match(r'\s+years\b',text[shift.end:]):
        return None
    relation=re.match(r'\s+years (younger|older)\b',text[delta.end:])
    owner=re.search(r'\b([a-z]+),? is\s*$',text[:delta.start])
    if not relation or not owner or not _has(r'\b'+re.escape(owner.group(1))+r'\b',p.question):
        return None
    if target.start<len(p.body) or not re.match(r'\s+years old\b',text[target.end:]):
        return None
    adjustment=delta.value*(-1 if relation.group(1)=='younger' else 1)
    current=age.value-shift.value+adjustment
    if current<0:
        return None
    return _answer(target.value-current,'{} - ({})'.format(format_number(target.value),format_number(current)))


def _box_volume_difference(p):
    """Two explicitly dimensioned cuboids, with feet/inches converted exactly."""
    ns=list(p.numbers)
    text=p.text.lower()
    if len(ns)==7 and ns[-1].start>=len(p.body) and ns[-1].value==2:
        noun=_unit(text[ns[-1].end:])
        if noun and len(re.findall(r'\b'+re.escape(noun)+r'(?:s|es)?\b',p.body))>=2:
            ns.pop()
    if len(ns)!=6 or not _has(r'\bdifference in volume\b',p.question):
        return None
    scales={'foot':Fraction(12),'inch':Fraction(1),'meter':Fraction(100),'centimeter':Fraction(1)}
    families={'foot':0,'inch':0,'meter':1,'centimeter':1}
    values=[];family=set()
    for n in ns:
        unit=_unit(text[n.end:])
        if unit not in scales:
            return None
        family.add(families[unit]);values.append(n.value*scales[unit])
    if len(family)!=1:
        return None
    for chunk in (ns[:3],ns[3:]):
        terms=text[chunk[0].end:chunk[-1].end+20]
        if not all(_has(r'\b'+word+r'\b',terms) for word in ('wide','tall','deep')):
            return None
    a,b,c,d,e,f=values
    value=abs(a*b*c-d*e*f)
    target=re.search(r'\bcubic (feet|foot|inches|inch|meters?|centimeters?)\b',p.question)
    if target:
        unit=_normal_unit(target.group(1))
        if unit not in scales or families[unit] not in family:
            return None
        value/=scales[unit]**3
    return _answer(value,'Difference of the two volumes in the requested units')


def _multiple_group_contents(p):
    """A disjoint list of container counts with individual content sizes."""
    ns=p.numbers
    text=p.text.lower()
    if _other_owner(p):
        return None
    if len(ns) not in (4,6,8) or not _has(r'\b(?:total|altogether|combined|in all)\b',p.question):
        return None
    if _has(r'\b(?:than|more|less|fewer|half|twice|left|remaining|except|lost|sold)\b',text):
        return None
    asked=_asked(p)
    if not asked:
        return None
    terms=[]
    for i in range(0,len(ns),2):
        count,size=ns[i:i+2]
        middle=text[count.end:size.start]
        if _unit(text[size.end:])!=asked:
            return None
        # The grouping relation must occur between the two quantities.
        if not re.fullmatch(r'\s+[a-z]+(?: of [a-z ]+?)?(?: that)? (?:hold|holds|have|has|contain|contains|with|of)\s+',middle):
            return None
        terms.append(count.value*size.value)
    return _answer(_sum(terms),_fmt(terms))


def _typed_group_contents(p):
    """Different explicitly named container types with stated per-type sizes."""
    ns=p.numbers
    text=p.text.lower()
    if len(ns) not in (4,6) or _has(r'\b(?:than|more|less|fewer|half|twice|left|remaining|except|lost|sold)\b',text):
        return None
    asked=_asked(p)
    if not asked:
        return None
    rates={}
    for i,n in enumerate(ns):
        end=ns[i+1].start if i+1<len(ns) else len(text)
        tail=re.split(r'[.!?;]',text[n.end:end])[0]
        m=re.search(r'\b(?:in |on |for )?(?:each|per|every) ([a-z]+)\b',tail)
        if m and _unit(tail)==asked:
            group=_normal_unit(m.group(1))
            if group in rates:
                return None
            rates[group]=i
    if len(rates)*2!=len(ns):
        return None
    used=set(rates.values());terms=[]
    for group,ri in rates.items():
        counts=[i for i,n in enumerate(ns) if i not in used and _unit(text[n.end:])==group]
        if len(counts)!=1:
            return None
        ci=counts[0];used.add(ci);terms.append(ns[ri].value*ns[ci].value)
    if len(used)!=len(ns):
        return None
    mentioned={g for g in rates if re.search(r'\b'+re.escape(g)+r'(?:s|es)?\b',p.question)}
    if mentioned and mentioned!=set(rates):
        return None
    return _answer(_sum(terms),_fmt(terms))


def _mixture_servings(p):
    """Grouped containers plus individual volumes, divided into servings."""
    ns=p.numbers
    text=p.text.lower()
    if not 4 <= len(ns) <= 7 or ns[-1].start<len(p.body):
        return None
    count,size=ns[:2]
    if text[count.end:size.start].strip():
        return None
    if not re.match(r'-(?:oz|ounce|liter|ml|milliliter)s?\b',text[size.end:]):
        return None
    measure=_unit(text[size.end:])
    if not measure or not all(_unit(text[n.end:])==measure for n in ns[2:]):
        return None
    if not _has(r'\b(?:adds?|mix|mixes|combines?|contains?)\b',p.body):
        return None
    if not re.match(r'\s*-?\s*[a-z]+ (?:servings|portions|cups|glasses)\b',text[ns[-1].end:]):
        return None
    total=count.value*size.value+_sum(n.value for n in ns[2:-1])
    return _answer(total/ns[-1].value,'({} x {} + {}) / {}'.format(format_number(count.value),format_number(size.value),_fmt(n.value for n in ns[2:-1]),format_number(ns[-1].value)))


def _pack_distribution(p):
    """Sum a package's contents and multiply by recipients plus an extra pack."""
    ns=p.numbers
    text=p.text.lower()
    if not 3 <= len(ns) <= 7 or any(n.start>=len(p.body) for n in ns):
        return None
    intro=re.search(r'\beach ([a-z]+) of ([a-z]+) contains\s*$',text[:ns[0].start])
    if not intro or _normal_unit(intro.group(2))!=_asked(p):
        return None
    group=intro.group(1)
    sentence=_sentence(text,ns[0])
    contents=[n for n in ns if _sentence(text,n)==sentence]
    if len(contents)!=len(ns)-1:
        return None
    recipients=ns[-1]
    if not re.match(r'\s+[a-z]+ receive a '+re.escape(group)+r'\b',text[recipients.end:]):
        return None
    if not _has(r'\banother '+re.escape(group)+r' is given\b',text[recipients.end:]):
        return None
    total=_sum(n.value for n in contents)
    return _answer(total*(recipients.value+1),'({}) x ({} + 1)'.format(_fmt(n.value for n in contents),format_number(recipients.value)))


def _changed_population_rate(p):
    """A before-removal population and an individual daily production rate."""
    ns=p.numbers
    text=p.text.lower()
    if len(ns)!=3 or not _has(r'\bremaining\b',p.question):
        return None
    removed,rate,total=ns
    group=_unit(text[removed.end:])
    total_unit=_unit(text[total.end:])
    if not total_unit and group and re.search(r'\bnumber of '+re.escape(group)+r'(?:s|es)?\b[^.;]*\bwas\s*$',text[:total.start]):
        total_unit=group
    if not group or total_unit!=group or _unit(text[rate.end:])!=_asked(p):
        return None
    if not _has(r'\b(?:were|was) removed\b',text[removed.end:rate.start]):
        return None
    if not re.search(r'\beach '+re.escape(group)+r' [a-z]+\s*$',text[:rate.start]):
        return None
    if not _has(r'\bper day\b',text[rate.end:total.start]) or not _has(r'\bbefore\b',text[total.end:len(p.body)]):
        return None
    period=re.search(r'\bin (?:a|one) (week|day)\b',p.question)
    if not period:
        return None
    days=Fraction(7 if period.group(1)=='week' else 1)
    return _answer((total.value-removed.value)*rate.value*days,
                   '({} - {}) x {} x {}'.format(*map(format_number,(total.value,removed.value,rate.value,days))))


def solve(problem):
    if any(n.kind != 'number' or n.value <= 0 for n in problem.numbers):
        return None
    text=problem.text.lower()
    # These readers handle absolute counts and explicit numerical factors.
    # Fractional allocations and unstated multipliers need other skills.
    if _has(r'\b(?:twice|thrice|double|triple|doubled|tripled)\b',text):
        return None
    if any(n.value.denominator!=1 and re.match(r'\s+of\b',text[n.end:])
           for n in problem.numbers):
        return None
    if _has(r'\bdozen\b',problem.text.lower()):
        return _dozens(problem)
    for rule in (_rate_chain, _paired_groups, _labelled_products,
                 _category_multipliers, _stock_ledger, _converted_stock,
                 _remaining_reading, _arithmetic_schedule, _host_supply,
                 _net_population, _perimeters, _capacity_distance,
                 _shared_rate_difference, _ratio_groups, _equal_share_subgroup,
                 _rectangle_area, _grouped_partition, _converted_inventory,
                 _production_remainder, _mixed_daily_time, _weekday_schedule,
                 _square_rectangle, _overlap, _category_difference,
                 _nested_containers, _shared_rate_sum,
                 _parallel_daily_groups, _ratio_length, _comparison_categories,
                 _qualified_rates, _past_age_sum, _future_relative_age,
                 _box_volume_difference, _multiple_group_contents,
                 _typed_group_contents, _mixture_servings, _pack_distribution,
                 _changed_population_rate):
        result = rule(problem)
        if result is not None:
            return result
    return None
