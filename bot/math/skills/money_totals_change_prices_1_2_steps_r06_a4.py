"""Small money equations with explicit totals, discounts and unit links.

Each reader accounts for every number it receives. Prices attach to item or
time units; unsupported transactions and ambiguous units are left to other
skills. Arithmetic is exact, including prices expressed in cents.
"""
import re
from fractions import Fraction

from ..numbers import format_number
from ._money_common import (
    _currencies,
    _has, _expr, _bounds, _role, _singular, _numbers, _phrase, _head,
    _same, _price_label, _output, _result, _PERIODS, _period_scale,
)


def _answer(p, value, expression):
    if value < 0:
        return None
    if re.match(r'how many (?!dollars?\b|cents?\b|euros?\b)', p.question):
        return value, 'Calculation: {} = {}.'.format(expression, format_number(value))
    result = _output(p, _result(value, expression, p))
    # Keep the named subject in the reply so an unrelated chat card about a
    # story noun does not appear to answer the monetary question more closely.
    original_question = p.text[len(p.body):]
    names = [name for name in re.findall(r'\b[A-Z][a-z]+\b', original_question)
             if name.lower() not in ('how', 'what', 'calculate', 'find', 'determine', 'in')]
    context = names[:2]
    target = re.search(r'\bon ([a-z ]+?)[?]?(?:$)', p.question)
    if target and len(target.group(1).split()) <= 8:
        context.append(target.group(1).replace(' than on ', ' compared with '))
    if context:
        result = result[0], 'For {}: {}'.format(', '.join(context), result[1])
    return result


def _label(p, ns, n):
    t = p.text.lower()
    m = re.match(r'\s*/\s*([a-z]+)\b', t[n.end:])
    if m:
        return _singular(m.group(1)), True
    m = re.match(r'\s*(?:dollars?\s*)?(?:a|per|each) (day|week|month|year) per ([a-z]+)\b', t[n.end:])
    if m and _has(r'\b(?:a|per|each|every) '+m.group(1)+r'\b', p.question):
        return _singular(m.group(2)), True
    m = re.match(r'\s*(?:dollars?|cents?|euros?)?\s*(?:per|a|an|for each) ([a-z]+(?: [a-z]+){0,2})', t[n.end:])
    if m:
        return _phrase(m.group(1)), True
    start, end = _bounds(t, n)
    if _has(r'\bquarterly (?:at|for)\s*$', t[start:n.start]):
        return 'quarter', True
    m = re.search(r'\b(?:charge|cost|price|fee) per ([a-z]+) (?:is|was)\s*$', t[start:n.start])
    if m:
        return _singular(m.group(1)), True
    m = re.search(r'\btickets? for ([a-z]+) costs?\s*$', t[start:n.start])
    if m:
        return _singular(m.group(1)), True
    m = re.search(r'\b(?:one|a|an|each) ([a-z]+(?: [a-z]+){0,2}?) (?:is|was) sold for\s*$', t[start:n.start])
    if m:
        return _phrase(m.group(1)), True
    if _has(r'^\s*(?:each|every) month\b', t[start:n.start]):
        return 'month', True
    if _has(r'\bthey each (?:pay|cost|earn)\s*$', t[start:n.start]):
        candidates = [c for c in ns if c.kind != 'money' and c.start < n.start and _unit(t[c.end:]) not in _PERIODS]
        if candidates:
            return _phrase(t[candidates[-1].end:]), True
    return _price_label(p, ns, n)


def _total(t, n):
    start, end = _bounds(t, n)
    before, after = t[start:n.start], t[n.end:end]
    return (_has(r'\b(?:total|altogether|in all|together cost)\b[^,;]*$', before)
            or _has(r'^\s*(?:dollars?\s*)?(?:in total|in all|altogether|for all)\b', after))


def _priced_terms(p, ns, prices, counts):
    """Bind explicit per-item prices, leaving unpriced stock for an equation."""
    t = p.text.lower()
    used, terms = set(), []
    for price in prices:
        label, explicit = _label(p, ns, price)
        matches = [c for c in counts if id(c) not in used and _same(label, _phrase(t[c.end:]))]
        if label == '*':
            start, end = _bounds(t, price)
            matches = [c for c in counts if id(c) not in used and start <= c.start < price.start]
        if len(matches) > 1:
            return None
        if matches:
            c = matches[0]
            used.add(id(c))
            terms.append(price.value*c.value)
        elif explicit and label in ('day', 'week', 'month', 'year', 'hour', '*'):
            return None
        else:
            terms.append(price.value)
    return terms, [c for c in counts if id(c) not in used]


def _missing_price(p, ns):
    """Total = known purchases + count * unknown item price."""
    t, q = p.text.lower(), p.question
    if not _has(r'\b(?:price|cost|pay|paid|spend|spent|receive|earn|earned)\b', q):
        return None
    if _has(r'\b(?:discount|coupon|percent|more|less|change|profit|times|twice)\b', t):
        return None
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    totals = [n for n in money if _total(t, n)]
    if len(totals) != 1 or len(money) < 2:
        return None
    total = totals[0]
    known = [n for n in money if n is not total]
    bound = _priced_terms(p, ns, known, counts)
    if bound is None:
        return None
    terms, remaining = bound
    divisor = Fraction(1)
    if remaining:
        if len(remaining) != 1:
            return None
        c = remaining[0]
        unit = _head(_phrase(t[c.end:]))
        if not unit or not _has(r'\b'+re.escape(unit)+r'(?:s|ies)?\b', q):
            return None
        if not _has(r'\b(?:single|each|one|per)\b', q):
            return None
        divisor = c.value
    elif _has(r'\b(?:all|total|altogether|together|change|left|remaining)\b', q):
        return None
    if divisor <= 0:
        return None
    return _answer(p, (total.value-sum(terms, Fraction(0)))/divisor,
                   '({} - ({})) / {}'.format(format_number(total.value), _expr(terms), format_number(divisor)))


def _discount(p, ns):
    """A fixed coupon, or an explicitly per-person reduction."""
    t = p.text.lower()
    if not _has(r'\b(?:discount|coupon|rebate)\b', t) or not _has(r'\b(?:cost|pay|paid|spend|spent)\b', p.question):
        return None
    if _has(r'\b(?:percent|every|threshold|total of|more|less|free)\b', t):
        return None
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    discounts = []
    for n in money:
        start, end = _bounds(t, n)
        if (_has(r'\b(?:discount|rebate|coupon)(?: of| for)?\s*$', t[start:n.start])
                or _has(r'^\s*(?:off\s+)?(?:discount|rebate|coupon)\b', t[n.end:end])
                or _has(r'\bcoupon\b[^.;]*$', t[start:n.start]) and _has(r'^\s+off\b', t[n.end:end])):
            discounts.append(n)
    if len(discounts) != 1:
        return None
    discount = discounts[0]
    prices = [n for n in money if n is not discount]
    if not prices:
        return None
    per_discount = _has(r'\beach\b[^.;]*$', t[:discount.start]) or _has(r'^\s+each\b', t[discount.end:])
    if per_discount:
        if len(prices) != 1 or len(counts) != 1:
            return None
        label, explicit = _label(p, ns, prices[0])
        c = counts[0]
        if not explicit or not (label == 'person' and _has(r'^\s+of them\b', t[c.end:]) or _same(label, _phrase(t[c.end:]))):
            return None
        return _answer(p, (prices[0].value-discount.value)*c.value,
                       '({} - {}) * {}'.format(*(format_number(n.value) for n in (prices[0], discount, c))))
    bound = _priced_terms(p, ns, prices, counts)
    if bound is None or bound[1]:
        return None
    terms, _ = bound
    return _answer(p, sum(terms, Fraction(0))-discount.value,
                   '({}) - {}'.format(_expr(terms), format_number(discount.value)))


def _installment_duration(p, ns):
    """Purchase cost less initial payment, divided by recurring payment."""
    t = p.text.lower()
    m = re.match(r'how many (days?|weeks?|months?|years?)\b', p.question)
    if not m or len(ns) != 3 or any(n.kind != 'money' for n in ns):
        return None
    unit = _singular(m.group(1))
    if not _has(r'\b(?:fully paid|paid (?:off|for)|pay off|pay for)\b', p.question):
        return None
    if _has(r'\b(?:interest|percent|discount)\b', t):
        return None
    cost, deposit, payment = ns
    if not _has(r'\b(?:buys?|bought|costs?|price|purchased)\b[^.;]*$', t[:cost.start]):
        return None
    if not _has(r'\b(?:pays?|paid|down payment)\b[^.;]*$', t[cost.end:deposit.start]):
        return None
    if not _has(r'^\s*(?:dollars?\s*)?(?:a|per|each|every) '+unit+r'\b', t[payment.end:]):
        return None
    if not _has(r'\b(?:rest|remaining|balance)\b', t[deposit.end:payment.start]) or payment.value <= 0:
        return None
    return _answer(p, (cost.value-deposit.value)/payment.value,
                   '({} - {}) / {}'.format(*(format_number(n.value) for n in ns)))


def _split_change(p, ns):
    """Equal shares become dearer when some contributors drop out."""
    t = p.text.lower()
    if len(ns) != 3 or not _has(r'\bsplit\b.*\bequally\b', t):
        return None
    original, leaving, extra = ns
    if original.kind == 'money' or leaving.kind == 'money' or extra.kind != 'money':
        return None
    if not _has(r'^\s+more\b', t[extra.end:]) or not _has(r'\b(?:drop out|dropped out|leave|left the group)\b', t[leaving.end:extra.start]):
        return None
    if not _has(r'\b(?:cost|price)\b', p.question) or not 0 < leaving.value < original.value:
        return None
    value = original.value*(original.value-leaving.value)*extra.value/leaving.value
    return _answer(p, value, '{} * ({} - {}) * {} / {}'.format(
        format_number(original.value), format_number(original.value), format_number(leaving.value), format_number(extra.value), format_number(leaving.value)))


def _difference(p, ns):
    """Two explicit stocks at one shared unit price, or two expense groups."""
    t = p.text.lower()
    if not _has(r'\b(?:more|less)\b.*\bthan\b|\bdifference\b', p.question):
        return None
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) == 1 and len(counts) == 2:
        a, b = counts
        label, explicit = _label(p, ns, money[0])
        if label == '*':
            label = _phrase(t[a.end:])
        if not explicit or not _same(label, _phrase(t[a.end:])) or not _same(label, _phrase(t[b.end:])):
            return None
        if _has(r'\b(?:more|less|lost|gave|sold|remaining)\b', p.body):
            return None
        return _answer(p, abs(a.value-b.value)*money[0].value,
                       '|{} - {}| * {}'.format(*(format_number(n.value) for n in (a, b, money[0]))))
    if counts or len(money) < 2:
        return None
    groups = {}
    for n in money:
        start, end = _bounds(t, n)
        groups.setdefault(start, []).append(n.value)
        if not _has(r'\b(?:bought|costs?|spent|spends|buys?|paid|pays?)\b', t[start:n.start]):
            return None
    if len(groups) != 2:
        return None
    values = [sum(v, Fraction(0)) for v in groups.values()]
    return _answer(p, abs(values[0]-values[1]), '|{} - {}|'.format(*map(format_number, values)))


def _initial_ledger(p, ns):
    """Reverse a ledger with explicitly directed gifts and a final balance."""
    t = p.text.lower()
    if not _has(r'\b(?:at first|initially|originally|beginning)\b', p.question):
        return None
    if any(n.kind != 'money' for n in ns):
        return None
    owner = re.search(r'\b([a-z]+) (?:had|has) some money\b', p.body)
    if not owner:
        return None
    incoming, outgoing, final = [], [], []
    for n in ns:
        start, end = _bounds(t, n)
        before, after = t[start:n.start], t[n.end:end]
        if _has(r'^\s*(?:dollars?\s*)?(?:left|remaining)\b', after):
            final.append(n.value)
        elif _has(r'\b'+re.escape(owner.group(1))+r' (?:then )?(?:gave|gives|paid)\b', before):
            outgoing.append(n.value)
        elif _has(r'\b(?:gave|gives|given) (?:him|her|them) (?:another |an additional )?$', before):
            incoming.append(n.value)
        else:
            return None
    if len(final) != 1 or not outgoing or not incoming:
        return None
    return _answer(p, final[0]+sum(outgoing, Fraction(0))-sum(incoming, Fraction(0)),
                   '{} + ({}) - ({})'.format(format_number(final[0]), _expr(outgoing), _expr(incoming)))


def _flat_and_unit(p, ns):
    """A fixed item or service plus an explicit count of priced extras."""
    if not _has(r'\b(?:cost|pay|paid|spend|spent)\b', p.question):
        return None
    t = p.text.lower()
    if _has(r'\bfor the first (?:day|week|month|year)\b', t):
        return None  # This price replaces a first interval of the unit charge.
    if _has(r'\b(?:discount|more|less|left|remaining|total|profit|twice|times|every|daily|weekly)\b', p.body):
        return None
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) != 2 or len(counts) != 1:
        return None
    c = counts[0]
    unit = _phrase(t[c.end:])
    priced = [n for n in money if _same(_label(p, ns, n)[0], unit)]
    if len(priced) != 1:
        return None
    price = priced[0]
    fixed = next(n for n in money if n is not price)
    if _label(p, ns, fixed)[0] in ('hour', 'day', 'week', 'month', 'year'):
        return None
    if not _has(r'\b(?:costs?|price|fee|charged|for)\b[^.;]*$', t[:fixed.start]):
        return None
    return _answer(p, fixed.value+price.value*c.value,
                   '{} + {} * {}'.format(*(format_number(n.value) for n in (fixed, price, c))))


def _unit(tail):
    measure = re.match(r'\s*[- ]?(seconds?|minutes?|hours?|days?|weeks?|months?|years?|miles?|liters?|litres?|kilograms?|grams?|kg|ml)\b', tail)
    if measure:
        return {'kg': 'kilogram', 'litre': 'liter'}.get(_singular(measure.group(1)), _singular(measure.group(1)))
    if _has(r'^\s+times\b', tail):
        return 'event'
    return _head(_phrase(tail))


def _linked_price(p, ns):
    """A short chain of units: stock -> contents per stock -> money."""
    t = p.text.lower()
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) != 1 or not 2 <= len(counts) <= 4:
        return None
    if not _has(r'\b(?:cost|pay|paid|spend|spent|earn|make|money)\b', p.question):
        return None
    if _has(r'\b(?:more|less|left|remaining|discount|profit|lost|gave|half|twice|tax)\b', t):
        return None
    price = money[0]
    label, explicit = _label(p, ns, price)
    priced = _unit(' '+label)
    if not explicit or not priced or priced == '*':
        return None
    edges, roots = {}, []
    for index, c in enumerate(counts):
        unit = _unit(t[c.end:])
        if not unit:
            return None
        start, end = _bounds(t, c)
        stop = min([n.start for n in ns if n.start > c.start] or [len(t)])
        before, after = t[start:c.start], t[c.end:min(end, stop)]
        denominator = ''
        m = re.search(r'\b(?:each|every) ([a-z]+) (?:[a-z]+\s+){0,3}(?:used|uses|has|holds?|contains?|needs?|requires?|buys?|gets?|lasts)\s*$', before)
        if m:
            denominator = _singular(m.group(1))
        if _has(r'\beach time\b[^.;]*\b(?:buys?|uses?|gets?|needs?)\s*$', before):
            denominator = 'event'
        m = re.search(r'\b(?:per|each|every|a|an|in the) (day|week|month|year)\b', after)
        if m:
            denominator = m.group(1)
        m = re.search(r'\b(?:required|needed) for (?:making )?(?:a|an|each) ([a-z]+)\b', after)
        if m:
            denominator = _singular(m.group(1))
        m = re.search(r'\beach (?:whole )?([a-z]+) into\s*$', before)
        if m:
            denominator = _singular(m.group(1))
        m = re.search(r'\beach ([a-z]+) sold (?:an average of )?\s*$', before)
        if m:
            denominator = _singular(m.group(1))
        if index and _has(r'\b(?:lasting|lasts|takes|holds?|contains?)\s*$', before) and _has(r'^\s+[a-z]+\s+each\b', after):
            denominator = _unit(t[counts[index-1].end:])
        if denominator:
            if denominator == unit or denominator in edges:
                return None
            edges[denominator] = (unit, c.value)
        else:
            roots.append((unit, c.value))
    # A query for a single recurring period supplies one such period.
    if not roots:
        m = re.search(r'\b(?:a|per|each|one) (day|week|month|year)\b', p.question)
        if m:
            roots = [(m.group(1), Fraction(1))]
    if len(roots) != 1 or not edges:
        return None
    unit, value = roots[0]
    expression, used = [format_number(value)], set()
    while unit != priced:
        if unit not in edges or unit in used:
            return None
        used.add(unit)
        unit, factor = edges[unit]
        value *= factor
        expression.append(format_number(factor))
    if used != set(edges):
        return None
    return _answer(p, value*price.value, ' * '.join(expression+[format_number(price.value)]))


def _calendar_cost(p, ns):
    """Weekly named-day purchases, or an explicitly monthly recurring charge."""
    t = p.text.lower()
    if not all(n.kind == 'money' for n in ns):
        return None
    if not _has(r'\b(?:spend|spent|cost|pay|paid)\b', p.question):
        return None
    if not _has(r'\bin (?:a|one) year\b|\b(?:annual|yearly)\b', p.question):
        return None
    if _has(r'\b(?:discount|left|remaining|more|less|once|last|first|interest|split)\b', p.body):
        return None
    weekdays = r'(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)s'
    factor = None
    if len(re.findall(r'\bon '+weekdays+r'\b', p.body)) == len(ns):
        factor = 52
    elif all(_has(r'^\s*(?:dollars?\s*)?(?:a|per|each|every) month\b', t[n.end:]) for n in ns):
        factor = 12
    if factor is None:
        return None
    values = [n.value for n in ns]
    return _answer(p, sum(values, Fraction(0))*factor, '({}) * {}'.format(_expr(values), factor))


def _party_cost(p, ns):
    """Person prices with an explicitly described party and optional nights."""
    t = p.text.lower()
    if not _has(r'\b(?:cost|pay|paid|spend|spent|total|change|left|remaining)\b', p.question):
        return None
    if _has(r'\b(?:discount|more|less|split|equally)\b', t):
        return None
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    prices = [n for n in money if _has(r'^\s*(?:per (?:night|day) )?per person\b', t[n.end:])]
    if len(prices) != 1:
        return None
    price = prices[0]
    extras = [n for n in money if n is not price]
    change = _has(r'\b(?:left|remaining|change)\b', p.question)
    if change and (len(extras) != 1 or not _has(r'\b(?:has|had|brought|have)\b[^.;]*$', t[:extras[0].start])):
        return None
    if not change and any(not _has(r'^\s+(?:service|booking|transaction|delivery) fee\b', t[n.end:]) for n in extras):
        return None
    people, duration = None, Fraction(1)
    used = set()
    for c in counts:
        if _has(r'^\s+of (?:his|her|their) friends\b', t[c.end:]) and _has(r'\b[a-z]+ and\s*$', t[:c.start]):
            if people is not None:
                return None
            people = c.value+1
            used.add(id(c))
        elif _unit(t[c.end:]) in ('person', 'people', 'friend', 'sister', 'brother', 'member', 'guest', 'adult', 'child', 'student'):
            if people is not None:
                return None
            people = c.value
            used.add(id(c))
        if _has(r'^\s+(?:nights?|days?)\b', t[c.end:]) and _has(r'^\s+per (?:night|day) per person\b', t[price.end:]):
            duration = c.value
            used.add(id(c))
    if _has(r'\b(?:his|her|their) parents and (?:himself|herself|themselves)\b', t):
        if people is not None:
            return None
        people = Fraction(3)
    if people is None or len(used) != len(counts):
        return None
    if change:
        return _answer(p, extras[0].value-people*duration*price.value,
                       '{} - {} * {} * {}'.format(format_number(extras[0].value), format_number(people), format_number(duration), format_number(price.value)))
    return _answer(p, people*duration*price.value+sum((n.value for n in extras), Fraction(0)),
                   '{} * {} * {} + ({})'.format(format_number(people), format_number(duration), format_number(price.value), _expr(n.value for n in extras)))


def _quoted_price(p, ns):
    """An observed total for one quantity determines the cost of another."""
    t = p.text.lower()
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) != 1 or len(counts) != 2 or not _has(r'\b(?:cost|pay|paid|spend|spent)\b', p.question):
        return None
    if _has(r'\b(?:each|per|every|more|less|left|remaining|profit|discount|times)\b', t):
        return None
    price = money[0]
    candidates = []
    for c in counts:
        if c.end < price.start:
            link = t[c.end:price.start]
            if not _has(r'[.!?;]', link) and _has(r'\b(?:costs?|for|worth)\s*$', link):
                candidates.append(c)
    if len(candidates) != 1:
        return None
    base = candidates[0]
    target = next(c for c in counts if c is not base)
    if _unit(t[base.end:]) != _unit(t[target.end:]) or not _unit(t[base.end:]) or base.value <= 0:
        return None
    return _answer(p, target.value*price.value/base.value,
                   '{} * {} / {}'.format(*(format_number(n.value) for n in (target, price, base))))


def _recurring_cost(p, ns):
    """A recurring unit charge, or one consumable per stated period."""
    t, q = p.text.lower(), p.question
    if not _has(r'\b(?:cost|pay|paid|spend|spent|finance|money)\b', q):
        return None
    if _has(r'\b(?:discount|left|remaining|more|less|split|half|free|twice|times)\b', t):
        return None
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) != 1 or len(counts) > 1:
        return None
    price = money[0]
    label, explicit = _label(p, ns, price)
    period = _head(label)
    if not explicit:
        return None
    if counts:
        duration = counts[0]
        target, count = _unit(t[duration.end:]), duration.value
    else:
        m = re.search(r'\b(?:a|one|entire|whole|the first) (day|week|month|year)\b', q)
        if not m:
            return None
        target, count = m.group(1), Fraction(1)
    if target not in _PERIODS:
        return None
    if period not in _PERIODS:
        # A singular consumable is used once every explicitly named period.
        m = re.search(r'\b(?:uses?|buys?|needs?) (?:a|an) ([a-z]+)(?: of [a-z]+)? every (day|week|month|year)\b', p.body)
        if not m or not _same(label, m.group(1)):
            return None
        period = m.group(2)
    scale = _period_scale(period, target)
    if scale is None:
        return None
    return _answer(p, price.value*count*scale,
                   '{} * {} * {}'.format(format_number(price.value), format_number(count), format_number(scale)))


def _period_profit(p, ns):
    """Income and running costs expressed in compatible recurring periods."""
    t = p.text.lower()
    if not _has(r'\b(?:profit|save|saves|saving|savings)\b', p.question) or any(n.kind != 'money' for n in ns):
        return None
    m = re.search(r'\b(?:every|per|each|a) (day|week|month|year)\b', p.question)
    if not m or _has(r'\b(?:discount|more|less|half|twice|total)\b', p.body):
        return None
    values, signs = [], set()
    for n in ns:
        label, explicit = _label(p, ns, n)
        scale = _period_scale(_head(label), m.group(1))
        if not explicit or scale is None:
            return None
        start, end = _bounds(t, n)
        role = _role(t, n, start)
        if _has(r'\bdeposits\b[^.;]*$', t[start:n.start]):
            role = 'income'
        if _has(r'\bexpenses\b[^.;]*$', t[start:n.start]):
            role = 'expense'
        if role not in ('income', 'expense'):
            return None
        sign = 1 if role == 'income' else -1
        signs.add(sign)
        values.append(sign*n.value*scale)
    if signs != {-1, 1}:
        return None
    return _answer(p, sum(values, Fraction(0)), _expr(values))


def _inverse_profit(p, ns):
    """Operating expenses = gross receipts minus explicitly stated net profit."""
    t = p.text.lower()
    if not _has(r'\b(?:spend|spent|expenses|cost)\b', p.question) or any(n.kind != 'money' for n in ns):
        return None
    profits, receipts = [], []
    for n in ns:
        start, end = _bounds(t, n)
        before, after = t[start:n.start], t[n.end:end]
        if _has(r'\b(?:net|profit(?: of)?)\s*$', before) or _has(r'^\s+(?:in )?profit\b', after):
            profits.append(n.value)
        elif _role(t, n, start) == 'income' or _has(r'\bgross revenue(?: of)?\s*$', before):
            receipts.append(n.value)
        else:
            return None
    if len(profits) != 1 or not receipts:
        return None
    return _answer(p, sum(receipts, Fraction(0))-profits[0],
                   '({}) - {}'.format(_expr(receipts), format_number(profits[0])))


def _tickets(p, ns):
    """Tickets for explicitly counted categories, with a separate pass option."""
    t, q = p.text.lower(), p.question
    if not _has(r'\btickets?\b', t) or not _has(r'\b(?:cost|pay|paid|price|spend|spent)\b', q):
        return None
    if _has(r'\b(?:discount|more|less|left|remaining|free)\b', t):
        return None
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if not counts:
        return None
    used, values = set(), []
    for n in money:
        label, explicit = _label(p, ns, n)
        if not explicit:
            start, end = _bounds(t, n)
            if _has(r'\bseparate(?:ly)?\b', q) and _has(r'\bfamily pass\b', t[start:n.start]) and _has(r'\bor\b', t[n.end:]):
                continue
            return None
        matches = [c for c in counts if id(c) not in used and _same(label, _phrase(t[c.end:]))]
        if len(matches) != 1:
            return None
        c = matches[0]
        used.add(id(c))
        values.append(n.value*c.value)
    if len(used) != len(counts):
        return None
    return _answer(p, sum(values, Fraction(0)), _expr(values))


def _free_items(p, ns):
    """Only the unpaid remainder is charged at the explicitly stated price."""
    t, q = p.text.lower(), p.question
    if not _has(r'\b(?:pay|paid|cost|spend|spent)\b', q):
        return None
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) != 1 or len(counts) != 2:
        return None
    stock, free = counts
    if not _has(r'^\s+of them (?:for free|free)\b', t[free.end:]) and not (
            _has(r'\b(?:pays?|paid) for\s*$', t[:free.start]) and _has(r'^\s+of them\b', t[free.end:])):
        return None
    label, explicit = _label(p, ns, money[0])
    if not explicit or not (label == '*' or _same(label, _phrase(t[stock.end:]))):
        return None
    if not 0 <= free.value <= stock.value:
        return None
    return _answer(p, (stock.value-free.value)*money[0].value,
                   '({} - {}) * {}'.format(*(format_number(n.value) for n in (stock, free, money[0]))))


def _break_even(p, ns):
    """Number sold needed to cover explicitly stated fixed costs."""
    t = p.text.lower()
    if not _has(r'\bbreak even\b', p.question) or not p.question.startswith('how many '):
        return None
    if not all(n.kind == 'money' for n in ns):
        return None
    sales = [n for n in ns if _has(r'\b(?:sell|sells|sold)\b[^.;]*$', t[:n.start])]
    if len(sales) != 1 or sales[0].value <= 0:
        return None
    price = sales[0]
    costs = [n.value for n in ns if n is not price]
    if any(_role(t, n, _bounds(t, n)[0]) != 'expense' for n in ns if n is not price):
        return None
    units = sum(costs, Fraction(0))/price.value
    value = Fraction(-(-units.numerator//units.denominator))
    return _answer(p, value, 'ceil(({}) / {})'.format(_expr(costs), format_number(price.value)))


def _scaled_wage(p, ns):
    """An explicit comparison of wages followed by an explicit work duration."""
    t = p.text.lower()
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) != 1 or not _has(r'\b(?:earn|make)\b', p.question):
        return None
    factors = [n for n in counts if _has(r'^\s+times (?:more money|the amount|as much)\b', t[n.end:])]
    if len(factors) != 1:
        return None
    factor = factors[0]
    # Do not apply the comparison backwards or to a third person's wages.
    start, end = _bounds(t, factor)
    subject = re.search(r'\b([a-z]+) (?:makes?|earns?)\s*$', t[start:factor.start])
    if subject and not _has(r'\b'+re.escape(subject.group(1))+r'\b', p.question):
        return None
    price = money[0]
    period = _head(_label(p, ns, price)[0])
    durations = [n for n in counts if n is not factor]
    if len(durations) == 1:
        duration = durations[0]
        if _unit(t[duration.end:]) != period:
            return None
        count = duration.value
    elif not durations:
        m = re.search(r'\b(?:a|one) (day|week|month|year)\b', p.question)
        if not m:
            return None
        count = _period_scale(period, m.group(1))
        if count is None:
            return None
    else:
        return None
    if _has(r'\b(?:bonus|overtime|tax|discount|half|less)\b', t):
        return None
    return _answer(p, factor.value*price.value*count,
                   '{} * {} * {}'.format(format_number(factor.value), format_number(price.value), format_number(count)))


def _round_trip(p, ns):
    """The explicitly stated one-way measure is paid for in both directions."""
    t = p.text.lower()
    if not _has(r'\b(?:round trip|back and forth|there and back)\b', t):
        return None
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) != 1 or len(counts) != 1:
        return None
    if not _has(r'\b(?:one way|one direction)\b', p.body):
        return None
    price, count = money[0], counts[0]
    if _unit(' '+_label(p, ns, price)[0]) != _unit(t[count.end:]):
        return None
    return _answer(p, 2*count.value*price.value,
                   '2 * {} * {}'.format(format_number(count.value), format_number(price.value)))


def _stock_value(p, ns):
    """Two explicitly additive stocks valued at the same price."""
    t, q = p.text.lower(), p.question
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) != 1 or len(counts) != 2:
        return None
    if not _has(r'\b(?:cost|pay|paid|spend|spent|worth|earn|make|money)\b', q):
        return None
    if _has(r'\b(?:more than|less|left|remaining|lost|gave|free|discount|times|profit|each letter)\b', t):
        return None
    label, explicit = _label(p, ns, money[0])
    if label == '*':
        label = _phrase(t[counts[0].end:])
    if not label or not explicit:
        return None
    first, second = counts
    # A quoted price for N objects is a batch total. A question about M
    # objects needs a unit-price conversion, not the value of N+M objects.
    if (second.start >= len(p.body) and first.start < money[0].start
            and _has(r'\bcosts?\s*$', t[first.end:money[0].start])
            and not _has(r'\b(?:each|per|apiece)\b', t[:len(p.body)])):
        return None
    a, b = _phrase(t[first.end:]), _phrase(t[second.end:])
    if _has(r'^\s+more\b', t[second.end:]) and _has(r'\b(?:buy|buys|bought)\s*$', t[:second.start]):
        if not _has(r'\b(?:all|total|worth)\b', q):
            return None
        b = a
    if _has(r'^\s+in (?:the|his|her|their)\b', t[second.end:]) and _has(r'\band\s*$', t[first.end:second.start]):
        b = a
    if not (_same(label, a) and _same(label, b)):
        return None
    return _answer(p, (first.value+second.value)*money[0].value,
                   '({} + {}) * {}'.format(*(format_number(n.value) for n in (first, second, money[0]))))


def _unit_price(p, ns):
    """A known price of N containers with M units in each, quoted per unit."""
    t = p.text.lower()
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) != 1 or len(counts) not in (2, 3) or not _has(r'\b(?:price|cost)\b', p.question):
        return None
    stock, size = counts[:2]
    if not stock.start < size.start < money[0].start:
        return None
    if not re.fullmatch(r'\s+[a-z]+ of\s+', t[stock.end:size.start]):
        return None
    if not _has(r'\bcosts?\s*$', t[size.end:money[0].start]):
        return None
    target = Fraction(1)
    unit = _unit(t[size.end:])
    if len(counts) == 3:
        query = counts[2]
        if query.start < len(p.body) or _unit(t[query.end:]) != unit:
            return None
        target = query.value
    elif not _has(r'\b(?:per|each|of (?:1|one|a|an)) '+re.escape(unit)+r'\b', p.question):
        return None
    if stock.value <= 0 or size.value <= 0:
        return None
    return _answer(p, money[0].value*target/(stock.value*size.value),
                   '{} * {} / ({} * {})'.format(format_number(money[0].value), format_number(target), format_number(stock.value), format_number(size.value)))


def _inverse_purchase(p, ns):
    """Units purchased = (cash brought minus cash left) / unit price."""
    t = p.text.lower()
    if not p.question.startswith('how many ') or len(ns) != 3 or any(n.kind != 'money' for n in ns):
        return None
    remaining = [n for n in ns if _has(r'\b(?:leaves? with|has left|left with)\s*$', t[:n.start])]
    cash = [n for n in ns if _has(r'\b(?:brought|had|has)\s*$', t[:n.start])]
    if len(remaining) != 1 or len(cash) != 1 or remaining[0] is cash[0]:
        return None
    price = next(n for n in ns if n not in remaining+cash)
    label, explicit = _label(p, ns, price)
    if not explicit or not _has(r'\b'+re.escape(label)+r's?\b', p.question) or price.value <= 0:
        return None
    return _answer(p, (cash[0].value-remaining[0].value)/price.value,
                   '({} - {}) / {}'.format(format_number(cash[0].value), format_number(remaining[0].value), format_number(price.value)))


def _wage_target(p, ns):
    """Scale observed earnings for known hours to requested earnings."""
    t = p.text.lower()
    if not p.question.startswith('how many hours') or not _has(r'\bearn\b', p.question):
        return None
    money = [n for n in ns if n.kind == 'money']
    hours = [n for n in ns if n.kind != 'money']
    if len(money) != 2 or len(hours) != 1 or _unit(t[hours[0].end:]) != 'hour':
        return None
    base = [n for n in money if n.start < len(p.body)]
    target = [n for n in money if n.start >= len(p.body)]
    if len(base) != 1 or len(target) != 1 or base[0].value <= 0:
        return None
    if not _has(r'\b(?:earn|earns|earned|paid)\b', t[:base[0].start]):
        return None
    return _answer(p, hours[0].value*target[0].value/base[0].value,
                   '{} * {} / {}'.format(format_number(hours[0].value), format_number(target[0].value), format_number(base[0].value)))


def _hour_totals(p, ns):
    """Sum hours across explicitly named periods; a query count labels them."""
    t = p.text.lower()
    if not _has(r'\b(?:earn|earned|make|made|paid)\b', p.question):
        return None
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) != 1 or _unit(' '+_label(p, ns, money[0])[0]) != 'hour':
        return None
    hours = [n for n in counts if n.start < len(p.body) and _unit(t[n.end:]) == 'hour']
    references = [n for n in counts if n not in hours]
    if not hours or len(references) != 1:
        return None
    ref = references[0]
    period = _unit(t[ref.end:])
    if (ref.start < len(p.body) or period not in _PERIODS
            or ref.value != len(hours) or len(re.findall(r'\b(?:last|this) '+period+r'\b', p.body)) != len(hours)):
        return None
    return _answer(p, sum((n.value for n in hours), Fraction(0))*money[0].value,
                   '({}) * {}'.format(_expr(n.value for n in hours), format_number(money[0].value)))


def _calendar_sales(p, ns):
    """Sales counts on named days refer to the sole priced product."""
    t = p.text.lower()
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) != 1 or not 2 <= len(counts) <= 7 or not _has(r'\b(?:earn|make|made|money)\b', p.question):
        return None
    label, explicit = _label(p, ns, money[0])
    if not explicit or not label or label in _PERIODS:
        return None
    days = r'(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)'
    for i, n in enumerate(counts):
        if not _has(r'^\s+on '+days+r'\b', t[n.end:]):
            return None
        before = t[:n.start] if i == 0 else t[counts[i-1].end:n.start]
        if not _has(r'\b(?:sold|sells|sell)\s*$', before) and not (i and _has(r'\band\s*$', before)):
            return None
    return _answer(p, sum((n.value for n in counts), Fraction(0))*money[0].value,
                   '({}) * {}'.format(_expr(n.value for n in counts), format_number(money[0].value)))


def _credit(p, ns):
    """The fully used credit limit less repayments already made."""
    t = p.text.lower()
    if not _has(r'\bcredit\b', p.question) or not _has(r'\b(?:pay|owe)\b', p.question):
        return None
    if not _has(r'\b(?:full credit limit|entire credit limit)\b', p.body) or not all(n.kind == 'money' for n in ns):
        return None
    limit, payments = ns[0], ns[1:]
    if not _has(r'\bcredit(?: of)?\s*$', t[:limit.start]):
        return None
    for i, n in enumerate(payments):
        before = t[limit.end if i == 0 else payments[i-1].end:n.start]
        if not _has(r'\bpaid\s*$', before) and not (i and _has(r'\band\s*$', before)):
            return None
    return _answer(p, limit.value-sum((n.value for n in payments), Fraction(0)),
                   '{} - ({})'.format(format_number(limit.value), _expr(n.value for n in payments)))


def _net_spending(p, ns):
    """Purchase outlay reduced by explicit sale receipts."""
    t = p.text.lower()
    if not _has(r'\b(?:spend|spent)\b', p.question) or not _has(r'\b(?:sells?|sold)\b', p.body):
        return None
    if not all(n.kind == 'money' for n in ns) or _has(r'\b(?:discount|interest|tax|each|per|twice|times|half)\b', t):
        return None
    expenses, receipts = [], []
    for i, n in enumerate(ns):
        role = _role(t, n, ns[i-1].end if i else 0)
        if role == 'expense':
            expenses.append(n.value)
        elif role == 'income':
            receipts.append(n.value)
        else:
            return None
    if not expenses or not receipts:
        return None
    return _answer(p, sum(expenses, Fraction(0))-sum(receipts, Fraction(0)),
                   '({}) - ({})'.format(_expr(expenses), _expr(receipts)))


def _price_reduction(p, ns):
    """A fixed decrease in a unit's original price, applied to a purchase."""
    t = p.text.lower()
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) != 2 or len(counts) != 1 or not _has(r'\b(?:cost|price|pay|paid|spend|spent)\b', p.question):
        return None
    reductions = [n for n in money if _has(r'\b(?:reduced|decreased|lowered) by\s*$', t[:n.start])]
    originals = [n for n in money if _has(r'\b(?:initial|original) price (?:was|is)\s*$', t[:n.start])]
    if len(reductions) != 1 or len(originals) != 1 or reductions[0] is originals[0]:
        return None
    c = counts[0]
    if not _has(r'^\s+of (?:such|these|those)\b', t[c.end:]):
        return None
    return _answer(p, (originals[0].value-reductions[0].value)*c.value,
                   '({} - {}) * {}'.format(format_number(originals[0].value), format_number(reductions[0].value), format_number(c.value)))


def _ledger(p, ns):
    """An explicit starting balance, purchases, and money received or fined."""
    t, q = p.text.lower(), p.question
    is_left = _has(r'\b(?:left|remaining|change|back)\b', q)
    is_short = _has(r'\bneed\b.*\bbuy\b', q)
    if not (is_left or is_short):
        return None
    if _has(r'\b(?:more|less|discount|coupon|free|times|twice|half|interest|total|allowance|all her money|all his money)\b', p.body):
        return None
    if any(n.kind != 'money' and n.start >= len(p.body) for n in ns):
        return None
    owners = set(re.findall(r'\b([A-Z][a-z]+) (?:has|had|brought|spent|spends|saved|buys|bought)\b', p.text[:len(p.body)]))
    owners -= {'He', 'She', 'They', 'If', 'Then'}
    if len(owners) > 1 and not _has(r'\b(?:they|them|their|together|combined)\b', q):
        return None
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    used, groups = set(), {}
    for i, n in enumerate(money):
        lower = money[i-1].end if i else 0
        role = _role(t, n, lower)
        if _has(r'\bbrought\s*$', t[lower:n.start]):
            role = 'balance'
        if _has(r'\bsaves\s*$', t[lower:n.start]):
            role = 'balance'
        if _has(r'\b(?:fined|fine of)\s*$', t[lower:n.start]):
            role = 'expense'
        if role is None and i and not _has(r'[.;]', t[lower:n.start]):
            role = previous
        if role not in ('income', 'expense', 'balance', 'tender'):
            return None
        bound = _priced_terms(p, ns, [n], [c for c in counts if id(c) not in used])
        if bound is None:
            return None
        terms, remaining = bound
        used.update(id(c) for c in counts if c not in remaining)
        if role == 'balance' and _has(r'\bnow has\s*$', t[lower:n.start]):
            # A later explicitly current balance already includes earlier gifts.
            groups = {}
        groups.setdefault(role, []).extend(terms)
        previous = role
    if len(used) != len(counts) or 'expense' not in groups:
        return None
    available = sum((v for role, vs in groups.items() if role != 'expense' for v in vs), Fraction(0))
    spent = sum(groups['expense'], Fraction(0))
    if is_short:
        value, expression = spent-available, '{} - {}'.format(format_number(spent), format_number(available))
    else:
        value, expression = available-spent, '{} - {}'.format(format_number(available), format_number(spent))
    return _answer(p, value, expression)


def solve(problem):
    t = problem.text.lower()
    if not _has(r'[$£€]|\b(?:dollars?|cents?|euros?)\b', t):
        return None
    if not _has(r'\b(?:cost|costs|price|pay|paid|spend|spent|money|change|save|earn|earned|make|made|profit|weeks|months|finance|receive|back|left|remaining|worth|discount|buy)\b', problem.question):
        return None
    if _has(r'\b(?:percent|tax|ratio)\b', t) or _has(r'\binterest\b', t) and not _has(r'\bno interest\b', t):
        return None
    if _has(r'\bbonus\b', t) or _has(r'\baverage\b', problem.question):
        return None
    if _has(r'\b(?:twice|thrice|double[ds]?|triple[ds]?)\b', t):
        return None
    ns = _numbers(problem)
    # A grammatical "one item was sold for PRICE" defines a unit price.
    ns = [n for n in ns if not (n.kind != 'money' and n.value == 1
          and _has(r'^\s+[a-z]+(?: [a-z]+){0,2} (?:is|was) sold for\s+[$£€]', t[n.end:]))]
    ns = [n for n in ns if not (n.kind != 'money' and n.value == 1 and _has(r'^\s+(?:way|direction)\b', t[n.end:]))]
    ns = [n for n in ns if not (n.kind != 'money' and n.value == 1
          and _has(r'\b(?:a|an) (?:new|old|replacement)\s*$', t[:n.start])
          and _has(r'^\s+for\s+[$£€]', t[n.end:]))]
    enough = 2 <= len(ns) <= 10 or len(ns) == 1 and _has(r'\bquarterly\b', t)
    if not enough or any(n.value < 0 or n.kind == 'percent' for n in ns):
        return None
    currencies = _currencies(problem, ns)
    if len(currencies) > 1:
        return None
    owners = set(re.findall(r'\b([A-Z][a-z]+) (?:has|had|buys|bought|spent|spends|earns|earned|makes)\b', problem.text[:len(problem.body)]))
    owners -= {'He', 'She', 'They', 'If', 'Then'}
    separate_owners = len(owners) > 1 and not _has(r'\b(?:total|together|combined|they|their|them)\b', problem.question)
    count_question = re.match(r'how many (?!dollars?\b|cents?\b|euros?\b)', problem.question)
    for rule in (_missing_price, _discount, _installment_duration, _split_change,
                 _difference, _initial_ledger, _linked_price, _calendar_cost,
                 _party_cost, _quoted_price, _recurring_cost, _period_profit,
                 _inverse_profit, _tickets, _free_items, _break_even,
                 _scaled_wage, _round_trip, _stock_value, _unit_price,
                 _inverse_purchase, _wage_target, _hour_totals, _calendar_sales,
                 _credit, _net_spending, _price_reduction, _ledger,
                 _flat_and_unit):
        if separate_owners and rule not in (_difference, _initial_ledger, _scaled_wage):
            continue
        if count_question and rule not in (_installment_duration, _break_even, _inverse_purchase, _wage_target):
            continue
        result = rule(problem, ns)
        if result is not None:
            return result
    return None
