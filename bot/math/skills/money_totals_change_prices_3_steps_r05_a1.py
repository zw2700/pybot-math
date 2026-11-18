"""Linked unit prices, money ledgers, and explicitly stated work schedules.

Prices bind to noun phrases (including distinguishing modifiers), not to the
position of a number in a story. Every non-referential quantity must be used.
Unsupported comparisons, allocations, and ambiguous bindings abstain.
"""
import re
from dataclasses import replace
from fractions import Fraction

from ..numbers import format_number
from ..problem import Problem
from ._money_common import (
    _currencies,
    _has, _bounds, _money, _role, _singular, _STOP, _TIME,
    _phrase, _head, _same, _numbers, _result, _output,
    _price_label, _price_matches, _aggregate, _period_scale,
)


def _basket(p, ns):
    t = p.text.lower()
    if (_has(r'\bexpenses\b', p.question)
            or _has(r'\bingredients\b', p.body) and _has(r'\bmake\b', p.body)):
        return None  # Production costs and receipts need a unit-margin ledger.
    if _has(r'\bnow has\b|\b(?:each|every) letter\b', p.body):
        return None
    if _has(r'\bor\b', p.body) and _has(r'\bseparate(?:ly)?\b', p.question):
        return None
    if (_has(r'\b(?:price|cost)\b', p.question)
            and not _has(r'\b(?:total|all|altogether|together)\b', p.question)
            and _has(r'\btogether cost\b', p.body)):
        return None
    ask = re.split(r'\b(?:if|when)\b', p.question)[0]
    if _has(r'\b(?:each|per|lose|lost|save|saved|savings)\b', ask):
        return None
    if _has(r'\b(?:different|other|remaining)\b', p.question) and _has(r'\bin total[^.;]*\bpaid\b|\bpaid[^.;]*\bin total\b', p.body):
        return None
    periods = set(re.findall(r'\b(?:per|each|every|a) (day|week|month|year)\b', p.body))
    query_periods = set(re.findall(r'\b(?:in|per|each|every|a) (?:a |one )?(day|week|month|year)\b', p.question))
    if query_periods and periods != query_periods:
        return None
    if _has(r'\b(?:percent|twice|thrice|half|third|quarter|times|more|less|discount|rebate|coupon|'
            r'equally|split|shared|average|interest|tax|least|cheap|cheaper|cheapest|free)\b', p.body):
        return None
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if any(c.start >= len(p.body) for c in counts) and any(c.start < len(p.body) for c in counts):
        return None  # A new query quantity is not another purchase in the body.
    if len(money) == 1 and len(counts) == 2:
        price = money[0]
        for c in counts:
            if c.start < price.start and _same(_phrase(t[c.end:]), _phrase(t[counts[0].end:])):
                link = t[c.end:price.start]
                if (_has(r'\b(?:costs?|for)\s*$', link)
                        and not _has(r'\b(?:each|every|per)\b', link + t[price.end:])):
                    return None
    if any(_has(r'\b(?:pack|box|jar|bag|carton) of\s*$', t[:c.start]) for c in counts):
        return None  # Package contents are not another inventory to add.
    labels = {id(c): _phrase(t[c.end:]) for c in counts}
    if any((not v and not _has(r'^\s*[$£€]', t[c.end:])) or _head(v) in _TIME
           for c, v in ((c, labels[id(c)]) for c in counts)):
        return None
    used, terms = set(), []
    for mi, n in enumerate(money):
        lower = money[mi-1].end if mi else 0
        role = _role(t, n, lower)
        if role is None and _has(r'\b(?:babysits?|washes?|charges?|services?)\b[^.;]*$', t[lower:n.start]):
            role = 'income'
        if _has(r'\bcharging\s*$', t[lower:n.start]):
            role = 'income'
        if _has(r'\b(?:ordered|orders?|purchased)\b[^.;]*$', t[lower:n.start]):
            role = 'expense'
        if _has(r'\b(?:rent|rents|rented|expense|expenses)\b[^.;]*$', t[lower:n.start]):
            role = 'expense'
        if _has(r'\b(?:each|every) [a-z -]+ (?:gave|gives)\b[^.;]*$', t[lower:n.start]) or _has(r'\b(?:put in|contributed)\s*$', t[lower:n.start]):
            role = 'income'
        if role is None and terms and not _has(r'[.;]', t[lower:n.start]):
            role = terms[-1][0]
        if _has(r'^\s+(?:leftover|left over|in loose coins)\b', t[n.end:]) or (
                _has(r'\b(?:change|back)\b', t[n.end:]) and _has(r'\breceived\b', t[lower:n.start])):
            role = 'remaining'
        label, explicit = _price_label(p, ns, n)
        if not role and mi and _has(r'\bfor\s*$', t[lower:n.start]) and _has(r'\b(?:service|installation|delivery)\b', t[lower:n.start]):
            role = 'expense'
        if _has(r'^-dollars?\b', t[n.end:]):
            role = 'expense'
            if _has(r'^-dollars? (?:bill|note)\b', t[n.end:]):
                role = 'tender'
            c = next((c for c in reversed(counts) if c.end <= n.start and not t[c.end:n.start].strip()), None)
            if c:
                used.add(id(c))
                terms.append((role, c.value*n.value, '{} * {}'.format(format_number(c.value), format_number(n.value))))
                continue
        if role not in {'expense', 'income', 'balance', 'tender', 'remaining'}:
            return None
        matches = []
        if label:
            matches = [c for c in counts if _price_matches(p, n, label, labels[id(c)])]
            if label == '*':
                start, end = _bounds(t, n)
                matches = [c for c in counts if start <= c.start < n.start and id(c) not in used]
            # A price in a count's own clause binds there before global units.
            local = [c for c in matches if lower <= c.start < n.start]
            if local:
                matches = local
            # Distinguishing modifiers cannot disappear across two categories.
            if len({labels[id(c)] for c in matches}) > 1 and len(money) > 1:
                return None
        if matches:
            if ('profit' in p.question and role == 'expense'
                    and _has(r'\b(?:sell|sells|sold)\b', p.body)
                    and not _has(r'\b(?:buy|buys|bought|spent|spends|materials|supplies|ingredients)\b', t[lower:n.start])):
                role = 'income'
            if any(id(c) in used for c in matches):
                # Shared contents (e.g. two components per plate) need an
                # explicit common denominator and exactly one matching stock.
                if len(matches) != 1 or not explicit or label == '*':
                    return None
            value = sum((c.value for c in matches), Fraction(0))*n.value
            expr = '({}) * {}'.format(' + '.join(format_number(c.value) for c in matches), format_number(n.value))
            used.update(id(c) for c in matches)
        elif explicit:
            # A singular product purchase can supply an implicit one.
            if not label or label == '*' or not _has(r'\b(?:a|an|the) '+re.escape(label.split()[0])+r'\b', t[:n.start]):
                return None
            value, expr = n.value, format_number(n.value)
        else:
            value, expr = n.value, format_number(n.value)
            # Denominations: N $M bills/donations are a product, not a price.
            preceding = [c for c in counts if c.end <= n.start and not t[c.end:n.start].strip()]
            if preceding and _has(r'^\s+(?:bills?|notes?|donations?)\b', t[n.end:]):
                c = preceding[-1]
                used.add(id(c))
                value *= c.value
                expr = '{} * {}'.format(format_number(c.value), expr)
        terms.append((role, value, expr))
    if len(used) != len(counts) or not terms:
        return None
    return _aggregate(p, terms)


def _period(tail):
    m = re.match(r'\s*(?:dollars?\s*)?(?:per|each|every|a|an)\s+(hour|day|week|month|year)\b', tail)
    return m.group(1) if m else ''


def _schedule(p, ns):
    """A wage times an explicitly linked schedule and a requested duration."""
    t = p.text.lower()
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) != 1 or not counts or _has(
            r'\b(?:remaining|more|less|change|discount|half|twice|thrice|double|triple|times|overtime|bonus|tax)\b', p.body):
        return None
    price = money[0]
    if _period(t[price.end:]) != 'hour':
        return None
    if not _has(r'\b(?:earn|earned|make|made|money|salary|pay|paid)\b', p.question):
        return None
    if all(_head(_phrase(t[n.end:])) == 'hour' for n in counts):
        if _has(r'\b(?:per|each|every)\b', re.split(r'\b(?:if|when)\b', p.question)[0]):
            return None
        hours = sum((n.value for n in counts), Fraction(0))
        return _result(hours*price.value, '({}) * {}'.format(' + '.join(format_number(n.value) for n in counts), format_number(price.value)), p)
    links, stocks, workforce = {}, [], []
    for i, n in enumerate(counts):
        unit = _head(_phrase(t[n.end:]))
        following = min([k.start for k in ns if k.start > n.start] or [len(t)])
        suffix = t[n.end:following]
        m = re.match(r'\s+(?:hours?|days?|afternoons?|mornings?|evenings?|weeks?|months?|years?)\s+(?:per|each|every|a)\s+(day|week|month|year)\b', suffix)
        if unit == 'hour' and _has(r'\b(?:each time|at a time)\b', suffix):
            # A work session occurs once on each explicitly scheduled day.
            munit = 'day'
        else:
            munit = m.group(1) if m else ''
        if unit not in _TIME and not munit and (
                any(_head(_phrase(m.group(1))) == unit
                    for m in re.finditer(r'\b(?:each|every) ([a-z -]+)', p.body))
                or _has(r'\bone of them\b', t)
                or i == 0 and _has(r'\bthey each (?:charge|earn|are paid)\b', p.body)):
            workforce.append(n)
        elif unit == 'day' and _has(r'^\s+days? off\b[^.;]*\bper week\b', suffix):
            if not 0 <= n.value <= 7 or 'day' in links:
                return None
            links['day'] = ('week', 7-n.value, '(7 - {})'.format(format_number(n.value)))
        elif unit in _TIME:
            if munit:
                if unit in links:
                    return None
                links[unit] = (munit, n.value, format_number(n.value))
            else:
                stocks.append((unit, n.value, format_number(n.value)))
        else:
            return None
    # Named workdays form an explicit weekly schedule, not a seven-day week.
    weekdays = re.findall(r'\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', p.body)
    if weekdays:
        if 'day' in links or not _has(r'\beach week\b', p.body):
            return None
        links['day'] = ('week', Fraction(len(set(weekdays))), str(len(set(weekdays))))
    if not stocks and _has(r'\b(?:annual|yearly|per year|a year)\b', p.question):
        stocks.append(('year', Fraction(1), '1'))
    if not stocks and _has(r'\b(?:per|a|each|every) week\b', p.question):
        stocks.append(('week', Fraction(1), '1'))
    if len(stocks) != 1 or len(workforce) > 1:
        return None
    target, duration, expr = stocks[0]
    requested_period = re.search(r'\b(?:per|each) (hour|day|week|month|year)\b', re.split(r'\b(?:if|when)\b', p.question)[0])
    if requested_period and (requested_period.group(1) != target or duration != 1):
        return None
    value, factors = price.value, [format_number(price.value)]
    unit, visited = 'hour', set()
    while unit != target:
        if unit in visited:
            return None
        visited.add(unit)
        if unit in links:
            unit, factor, factor_expr = links[unit]
            value *= factor
            factors.append(factor_expr)
        elif unit == 'month' and target == 'year':
            value *= 12
            factors.append('12')
            unit = 'year'
        else:
            return None
    if set(links) != visited & set(links):
        return None
    value *= duration
    factors.append(expr)
    if workforce:
        value *= workforce[0].value
        factors.append(format_number(workforce[0].value))
    return _result(value, ' * '.join(factors), p)


def _installments(p, ns):
    """A recurring payment and a single initial fee over an explicit term."""
    t = p.text.lower()
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) != 2 or len(counts) != 1 or _has(r'\b(?:percent|discount|increase|decrease)\b', t):
        return None
    periodic = []
    for n in money:
        period = _period(t[n.end:])
        if not period and _has(r'\bmonthly payment\b[^.;]*$', t[:n.start]):
            period = 'month'
        if period:
            periodic.append((n, period))
    if len(periodic) != 1:
        return None
    price, period = periodic[0]
    fee = next(n for n in money if n is not price)
    if not _has(r'\b(?:down payment|initial fee|joining fee|registration fee|setup fee)\b', t):
        return None
    if _has(r'\binterest\b', t) and not _has(r'\bno interest\b', t):
        return None
    duration = counts[0]
    unit = _head(_phrase(t[duration.end:]))
    scale = _period_scale(period, unit)
    if scale is None or not _has(r'\b(?:pay|paid|cost|price|spend)\b', p.question):
        return None
    return _result(price.value*duration.value*scale+fee.value,
                   '{} * {} * {} + {}'.format(format_number(price.value), format_number(duration.value), scale, format_number(fee.value)), p)


def _threshold_discount(p, ns):
    """A fixed rebate for each complete threshold of purchase value."""
    t = p.text.lower()
    if len(ns) != 4 or not _has(r'\bdiscount\b', p.body) or not _has(r'\b(?:pay|paid|spend|spent)\b', p.question):
        return None
    rebate, threshold, count, price = ns
    if not (rebate.kind == threshold.kind == price.kind == 'money' and count.kind != 'money'):
        return None
    if not _has(r'^\s+discount for every\s*$', t[rebate.end:threshold.start]):
        return None
    if not _has(r'^\s+purchase\b', t[threshold.end:]) or not _has(r'^\s*(?:cents?\s*)?each\b', t[price.end:]):
        return None
    if threshold.value <= 0 or not 0 <= rebate.value < threshold.value:
        return None
    gross = count.value*price.value
    discount = (gross//threshold.value)*rebate.value
    return _result(gross-discount, '{} - floor({} / {}) * {}'.format(format_number(gross), format_number(gross), format_number(threshold.value), format_number(rebate.value)), p)


def _rate_saving(p, ns):
    """Compare two costs for the same explicit duration or stock."""
    if not _has(r'\b(?:save|saved|saving|savings)\b', p.question):
        return None
    t = p.text.lower()
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) != 2 or len(counts) != 1:
        return None
    a, b = money
    da, db = _period(t[a.end:]), _period(t[b.end:])
    unit = _head(_phrase(t[counts[0].end:]))
    if not da or da != db or unit != da:
        return None
    return _result((a.value-b.value)*counts[0].value,
                   '({} - {}) * {}'.format(format_number(a.value), format_number(b.value), format_number(counts[0].value)), p)


def _package_change(p, ns):
    """Buy a known quantity in equal packages, then subtract from cash."""
    if not _has(r'\b(?:change|left|remaining)\b', p.question):
        return None
    t = p.text.lower()
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) != 2 or len(counts) != 2:
        return None
    cash, price = money
    needed, size = counts
    if not (cash.start < needed.start < size.start < price.start) or size.value <= 0:
        return None
    unit = _phrase(t[needed.end:])
    if not unit or not _same(unit, _phrase(t[size.end:])):
        return None
    if not _has(r'\b(?:needs?|buy)\b[^.;]*$', t[cash.end:needed.start]):
        return None
    if not _has(r'\b(?:jar|box|bag|pack|carton|container) of\s*$', t[:size.start]):
        return None
    if not _has(r'\bcosts?\s*$', t[size.end:price.start]):
        return None
    packages = needed.value/size.value
    if packages.denominator != 1:
        return None
    return _result(cash.value-packages*price.value, '{} - ({} / {}) * {}'.format(*(format_number(n.value) for n in (cash, needed, size, price))), p)


def _cash_option(p, ns):
    """Savings from cash purchase instead of a deposit and installments."""
    if not _has(r'\b(?:save|saving|savings)\b.*\bcash\b', p.question):
        return None
    t = p.text.lower()
    cash = [n for n in ns if n.kind == 'money' and _has(r'^\s+cash\b', t[n.end:])]
    if len(cash) != 1:
        return None
    others = [n for n in ns if n is not cash[0]]
    # The installment reader validates the fee, period, and duration.
    sub = replace(p, question='how much will the purchase cost?')
    result = _installments(sub, others)
    if result is None:
        return None
    return _result(result[0]-cash[0].value, '{} - {}'.format(format_number(result[0]), format_number(cash[0].value)), p)


def _labor_parts(p, ns):
    """Hourly labor over a schedule, plus explicitly identified parts costs."""
    t = p.text.lower()
    money = [n for n in ns if n.kind == 'money']
    if len(money) != 2 or not _has(r'\b(?:cost|pay|paid|profit)\b', p.question):
        return None
    parts = [n for n in money if _has(r'^\s+(?:in|for|on) (?:parts|materials|supplies)\b', t[n.end:])
             or _has(r'\bcost for (?:supplies|materials|parts)\b[^.;]*$', t[:n.start])]
    if len(parts) != 1:
        return None
    part = parts[0]
    others = [n for n in ns if n is not part]
    # A single object being repaired is a job reference, not a workforce.
    others = [n for n in others if not (n.value == 1 and n.kind != 'money' and _has(r'\bon\s*$', t[:n.start]))]
    result = _schedule(p, others)
    if result is None:
        return None
    sign = -1 if 'profit' in p.question else 1
    return _result(result[0]+sign*part.value, '{} {} {}'.format(format_number(result[0]), '-' if sign < 0 else '+', format_number(part.value)), p)


def _fill_change(p, ns):
    """The cost of filling an unmet capacity, subtracted from the tender."""
    t = p.text.lower()
    if not _has(r'\b(?:change|left|remaining)\b', p.question):
        return None
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) != 2 or len(counts) != 2:
        return None
    capacity, stock = counts
    cash, price = money
    label, explicit = _price_label(p, ns, price)
    if not explicit or not _same(label, _phrase(t[capacity.end:])) or not _same(label, _phrase(t[stock.end:])):
        return None
    if not _has(r'\b(?:holds?|capacity|needs?)\b[^.;]*$', t[:capacity.start]):
        return None
    if not _has(r'\balready\b[^.;]*$', t[:stock.start]) or capacity.value < stock.value:
        return None
    return _result(cash.value-(capacity.value-stock.value)*price.value,
                   '{} - ({} - {}) * {}'.format(*(format_number(n.value) for n in (cash, capacity, stock, price))), p)


def _sales_remainder(p, ns):
    """Spend sale proceeds on as many whole items as affordable."""
    t = p.text.lower()
    if not _has(r'\b(?:leftover|left over|left|remaining)\b', p.question) or not _has(r'\bas many\b.*\bas (?:he|she|they) can\b', p.body):
        return None
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) != 2 or len(counts) != 1:
        return None
    price, cost = money
    stock = counts[0]
    label, explicit = _price_label(p, ns, price)
    if not explicit or not _same(label, _phrase(t[stock.end:])) or cost.value <= 0:
        return None
    if not _has(r'\b(?:sells?|sold|worth)\b', t[:price.start]):
        return None
    proceeds = price.value*stock.value
    value = proceeds % cost.value
    return _result(value, '{} - floor({} / {}) * {}'.format(format_number(proceeds), format_number(proceeds), format_number(cost.value), format_number(cost.value)), p)


def _exception_price(p, ns):
    """Total value minus one exceptional item's value, shared by the rest."""
    t = p.text.lower()
    if not _has(r'\ball (?:the )?other\b.*\bsame (?:value|price)\b', p.body):
        return None
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) != 2 or len(counts) != 2:
        return None
    stock, exceptional = counts
    total, price = money
    if not _same(_phrase(t[stock.end:]), _phrase(t[exceptional.end:])) or stock.value <= exceptional.value:
        return None
    if not _has(r'\b(?:cost|price|worth)\b', p.question):
        return None
    return _result((total.value-price.value)/(stock.value-exceptional.value),
                   '({} - {}) / ({} - {})'.format(*(format_number(n.value) for n in (total, price, stock, exceptional))), p)


def _inventory_profit(p, ns):
    """Sales of a stock after an explicit gift/removal, minus materials."""
    if 'profit' not in p.question:
        return None
    t = p.text.lower()
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) != 2 or len(counts) != 2:
        return None
    stock, removed = counts
    cost, price = money
    unit = _phrase(t[stock.end:])
    if not unit or not _same(unit, _phrase(t[removed.end:])):
        return None
    if not _has(r'\b(?:gave|give|gives|donated)\s*$', t[:removed.start]):
        return None
    if not _has(r'\b(?:materials|supplies|ingredients)\b', t[cost.end:price.start]):
        return None
    if not _has(r'\b(?:sell|sells|sold)\b[^.;]*$', t[:price.start]) or not _has(r'^\s+each\b', t[price.end:]):
        return None
    return _result((stock.value-removed.value)*price.value-cost.value,
                   '({} - {}) * {} - {}'.format(*(format_number(n.value) for n in (stock, removed, price, cost))), p)


def _area_cost(p, ns):
    """Explicit rectangular dimensions and one or more prices per square unit."""
    t = p.text.lower()
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(counts) != 2 or not 1 <= len(money) <= 3:
        return None
    a, b = counts
    unit = _head(_phrase(t[a.end:]))
    if unit not in {'foot', 'meter', 'yard'} or _head(_phrase(t[b.end:])) != unit:
        return None
    if not _has(r'\bby\s*$', t[a.end:b.start]):
        return None
    if not all(_has(r'^\s+per square '+re.escape(unit)+r'\b', t[n.end:]) for n in money):
        return None
    if not _has(r'\b(?:cost|pay|paid|spend|spent)\b', p.question):
        return None
    price = sum((n.value for n in money), Fraction(0))
    return _result(a.value*b.value*price, '{} * {} * ({})'.format(format_number(a.value), format_number(b.value), ' + '.join(format_number(n.value) for n in money)), p)


def _calendar_depreciation(p, ns):
    """An explicit price in one calendar year, minus a yearly loss until another."""
    t = p.text.lower()
    money = [n for n in ns if n.kind == 'money']
    years = [n for n in ns if n.kind != 'money']
    if len(money) != 2 or len(years) != 2:
        return None
    if not _has(r'\beach year\b.*\bdecreased?\b', p.body) or 'price' not in p.question:
        return None
    if not all(_has(r'\bin\s*$', t[:n.start]) for n in years):
        return None
    loss, initial = money
    first, last = years
    if last.value <= first.value:
        return None
    return _result(initial.value-(last.value-first.value)*loss.value,
                   '{} - ({} - {}) * {}'.format(*(format_number(n.value) for n in (initial, last, first, loss))), p)


def _missing_count(p, ns):
    """A total value minus a known category, divided by the other unit price."""
    t = p.text.lower()
    m = re.match(r'how many\s+(.+)', p.question)
    if not m:
        return None
    asked = _phrase(m.group(1))
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) != 3 or len(counts) != 1:
        return None
    stock = counts[0]
    prices = [(n, _price_label(p, ns, n)[0]) for n in money]
    known = [(n, label) for n, label in prices if _same(label, _phrase(t[stock.end:]))]
    unknown = [(n, label) for n, label in prices if _same(label, asked)]
    if len(known) != 1 or len(unknown) != 1 or known[0][0] is unknown[0][0]:
        return None
    a, b = known[0][0], unknown[0][0]
    total = next(n for n in money if n is not a and n is not b)
    if not _has(r'\b(?:total|worth|raise|goal)\b[^.;]*$', t[:total.start]) or b.value <= 0:
        return None
    value = (total.value-stock.value*a.value)/b.value
    if value < 0 or value.denominator != 1:
        return None
    return value, '({} - {} * {}) / {} = {} items.'.format(*(format_number(n.value) for n in (total, stock, a, b)), format_number(value))


def _recipe_margin(p, ns):
    """Material units per product, unit material cost, and per-product margin."""
    t = p.text.lower()
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) != 2 or len(counts) != 2:
        return None
    components, products = counts
    cost, sale = money
    ingredient = _phrase(t[components.end:])
    if not ingredient or not _same(ingredient, _price_label(p, ns, cost)[0]):
        return None
    middle = t[components.end:cost.start]
    m = re.search(r'\b(?:for each|to make each|per)\s+([a-z]+)', middle)
    if not m:
        return None
    product = _singular(m.group(1))
    product_unit = _phrase(t[products.end:])
    if product_unit and not _same(product, product_unit):
        return None
    base = components.value*cost.value
    if _has(r'^\s+profit per '+re.escape(product)+r'\b', t[sale.end:]):
        if not _has(r'\b(?:charge|cost|pay)\b', p.question):
            return None
        value = (base+sale.value)*products.value
        expr = '({} * {} + {}) * {}'
        quantities = (components, cost, sale, products)
    elif 'profit' in p.question and _has(r'\b(?:sell|sells|sold)\b[^.;]*$', t[:sale.start]):
        value = (sale.value-base)*products.value
        expr = '({} - {} * {}) * {}'
        quantities = (sale, components, cost, products)
    else:
        return None
    return _result(value, expr.format(*(format_number(n.value) for n in quantities)), p)


def _menu(p, ns):
    """A fully specified order from a list of prices, including double items."""
    t = p.text.lower()
    selections = list(re.finditer(r'\b(?:orders?|ordered|buys?|bought)\b', p.body))
    if not selections:
        return None
    start = selections[-1].start()
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if not 2 <= len(money) <= 6 or not all(n.start < start for n in money):
        return None
    if not all(c.start >= start for c in counts):
        return None
    if not _has(r'\b(?:pay|cost|spend)\b', p.question):
        return None
    order = t[start:len(p.body)]
    words = [_singular(w) for w in re.findall(r'[a-z]+', order)]
    used, terms = set(), []
    for n in money:
        label, explicit = _price_label(p, ns, n)
        unit = _head(label)
        if not unit or unit not in words:
            return None
        matching = [c for c in counts if _same(label, _phrase(t[c.end:]))]
        if len(matching) > 1:
            return None
        if matching:
            c = matching[0]
            used.add(id(c))
            count = c.value
        else:
            plural = unit+r'(?:s|es)?'
            m = re.search(r'\b(double|triple)\s+'+plural+r'\b', order)
            count = Fraction({'double': 2, 'triple': 3}[m.group(1)]) if m else Fraction(1)
        terms.append(count*n.value)
    if len(used) != len(counts):
        return None
    return _result(sum(terms, Fraction(0)), ' + '.join(format_number(v) for v in terms), p)


def _overtime(p, ns):
    """Explicit regular-hour threshold and an overtime multiple or hourly pay."""
    t = p.text.lower()
    money = [n for n in ns if n.kind == 'money']
    hours = [n for n in ns if n.kind != 'money']
    if len(hours) != 2 or not all(_head(_phrase(t[n.end:])) == 'hour' for n in hours):
        return None
    cap, worked = hours
    if cap.value <= 0 or worked.value < cap.value:
        return None
    if len(money) == 1:
        price = money[0]
        factor = re.search(r'\b(double|triple) that amount per hour\b', p.body)
        if not factor or _period(t[price.end:]) != 'hour':
            return None
        if not _has(r'\bup to\b[^.;]*$', t[:cap.start]):
            return None
        multiplier = Fraction(2 if factor.group(1) == 'double' else 3)
        value = price.value*(cap.value+(worked.value-cap.value)*multiplier)
        expr = '{} * ({} + ({} - {}) * {})'.format(format_number(price.value), format_number(cap.value), format_number(worked.value), format_number(cap.value), format_number(multiplier))
    elif len(money) == 2:
        fixed, price = money
        if not _has(r'\bif (?:he|she|they) works? for\s*$', t[fixed.end:cap.start]):
            return None
        if not _has(r'^\s+for every hour of overtime\b', t[price.end:]):
            return None
        value = fixed.value+(worked.value-cap.value)*price.value
        expr = '{} + ({} - {}) * {}'.format(*(format_number(n.value) for n in (fixed, worked, cap, price)))
    else:
        return None
    return _result(value, expr, p)


def _grouped_price(p, ns):
    """Follow explicit contents-per-group relations to a unit selling price."""
    t = p.text.lower()
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) != 1 or not 2 <= len(counts) <= 5:
        return None
    if _has(r'\b(?:profit|change|left|remaining|more|less|half|twice|thrice|double|times|'
            r'gave|lost|sold out|each day|every day|per day)\b', t):
        return None
    # Unstated calendar multipliers cannot be inferred from dimensional units.
    if _has(r'\b(?:week|month|year)\b', p.question) and not any(
            n.start >= len(p.body) and _head(_phrase(t[n.end:])) in _TIME for n in counts):
        return None
    price = money[0]
    priced, explicit = _price_label(p, ns, price)
    if _has(r'^\s+for every person who visits\b', t[price.end:]):
        priced = 'visit'
    priced = _head(priced)
    if not explicit or not priced or priced == '*':
        return None
    units = [_head(_phrase(t[n.end:])) for n in counts]
    if any(not u for u in units):
        return None
    edges, roots = {}, []
    used = set()
    # Two explicit array dimensions determine a single count of cells.
    if len(counts) >= 2 and units[0] == units[1] and _has(r'\bby\s*$', t[counts[0].end:counts[1].start]):
        roots.append((units[0], counts[0].value*counts[1].value))
        used.update((0, 1))
    for i, n in enumerate(counts):
        if i in used:
            continue
        start, end = _bounds(t, n)
        before = t[start:n.start]
        next_start = min([k.start for k in ns if k.start > n.start] or [len(t)])
        after = t[n.end:min(end, next_start)]
        denominator = ''
        m = re.search(r'\b(?:each|every|per)\s+([a-z]+(?: [a-z]+){0,2}?)\s+(?:has|have|holds?|contains?|gives?|gets?|produces?|needs?|uses?)\s*$', before)
        if m:
            denominator = _head(_phrase(m.group(1)))
        m = re.search(r'\bfor each ([a-z]+)\b[^.;]*\b(?:collects?|gets?|earns?|receives?)\s*$', before)
        if m:
            denominator = _singular(m.group(1))
        m = re.match(r'\s+[a-z]+\s+(?:per|for each|in each|each|every|a|an)\s+([a-z]+)\b', after)
        if m:
            denominator = _singular(m.group(1))
        if i and _has(r'\bthey each (?:give birth to|produce|have|get)\s*$', before):
            denominator = units[i-1]
        if i and _has(r'\beach\s*$', after) and _has(r'\bwith\s*$', t[counts[i-1].end:n.start]):
            denominator = units[i-1]
        if not denominator:
            roots.append((units[i], n.value))
        else:
            if denominator in edges or denominator == units[i]:
                return None
            edges[denominator] = (units[i], n.value)
    if not roots or len({u for u, v in roots}) != 1 or not edges:
        return None
    unit = roots[0][0]
    value = sum((v for u, v in roots), Fraction(0))
    expression = ['('+' + '.join(format_number(v) for u, v in roots)+')']
    consumed = set()
    while unit != priced:
        if unit not in edges or unit in consumed:
            return None
        consumed.add(unit)
        unit, factor = edges[unit]
        value *= factor
        expression.append(format_number(factor))
    if consumed != set(edges):
        return None
    value *= price.value
    expression.append(format_number(price.value))
    return _result(value, ' * '.join(expression), p)


def _coin_value(p, ns):
    """Conventional denominations, with optional explicitly grouped coins."""
    t = p.text.lower()
    if not _has(r'\b(?:dollars?|money|pay|left|remaining)\b', p.question):
        return None
    if _has(r'\b(?:per|each|every|a) (?:day|week|month|year)\b', t):
        return None
    denominations = {'quartercoin': Fraction(1, 4), 'dime': Fraction(1, 10),
                     'nickel': Fraction(1, 20), 'penny': Fraction(1, 100)}
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) > 1 or not counts:
        return None
    coins = [n for n in counts if _head(_phrase(t[n.end:])) in denominations]
    others = [n for n in counts if n not in coins]
    if not coins:
        return None
    total = Fraction(0)
    terms = []
    if not others:
        for n in coins:
            denomination = denominations[_head(_phrase(t[n.end:]))]
            total += n.value*denomination
            terms.append('{} * {}'.format(format_number(n.value), format_number(denomination)))
    elif len(others) == 1 and len(coins) == 1:
        stock, size = others[0], coins[0]
        container = _head(_phrase(t[stock.end:]))
        if not _has(r'\beach '+re.escape(container)+r' (?:can )?(?:hold|holds|contains|has)\s*$', t[:size.start]):
            return None
        denomination = denominations[_head(_phrase(t[size.end:]))]
        total = stock.value*size.value*denomination
        terms.append('{} * {} * {}'.format(format_number(stock.value), format_number(size.value), format_number(denomination)))
    else:
        return None
    if money:
        if not _has(r'\b(?:left|remaining)\b', p.question) or not _has(r'\b(?:cost|costs|buy|buying|pay)\b', t):
            return None
        total -= money[0].value
        terms.append('- '+format_number(money[0].value))
    return _result(total, ' + '.join(terms), p)


def _comparative_quantity(p, ns):
    """Two purchases of the same measure, the second D more than the first."""
    t = p.text.lower()
    if len(ns) != 3 or not _has(r'\b(?:cost|spent|spend|pay)\b', p.question):
        return None
    a, delta, price = ns
    if a.kind == 'money' or delta.kind == 'money' or price.kind != 'money':
        return None
    unit = _head(_phrase(t[a.end:]))
    m = re.match(r'\s+more\s+([a-z]+)\b', t[delta.end:])
    label, explicit = _price_label(p, ns, price)
    if not m or _singular(m.group(1)) != unit or label != unit or not explicit:
        return None
    if not _has(r'\band\s*$', t[a.end:delta.start]) or _has(r'\bthan\b', t[delta.end:price.start]):
        return None
    return _result((2*a.value+delta.value)*price.value,
                   '(2 * {} + {}) * {}'.format(format_number(a.value), format_number(delta.value), format_number(price.value)), p)


def _packed_profit(p, ns):
    """Sell the contents of purchased containers; the input price is total."""
    if 'profit' not in p.question:
        return None
    t = p.text.lower()
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money) != 2 or len(counts) not in (2, 3):
        return None
    revenues = [n for n in money if _has(r'\b(?:sell|sells|sold)\b[^.;]*$', t[:n.start]) and _has(r'^\s+each\b', t[n.end:])]
    if len(revenues) != 1:
        return None
    price = revenues[0]
    cost = next(n for n in money if n is not price)
    stock, size = counts[:2]
    container = _head(_phrase(t[stock.end:]))
    if not container or not _has(r'\beach '+re.escape(container)+r'\s+(?:has|contains|holds)\s*$', t[:size.start]):
        return None
    if not _has(r'\bbought\b[^.;]*$', t[:cost.start]) or _has(r'^\s+each\b', t[cost.end:]):
        return None
    if len(counts) == 3 and (counts[2].value != stock.value or _head(_phrase(t[counts[2].end:])) != container):
        return None
    if _has(r'\b(?:unsold|left|remaining|discount|half|percent)\b', p.body):
        return None
    return _result(stock.value*size.value*price.value-cost.value,
                   '{} * {} * {} - {}'.format(*(format_number(n.value) for n in (stock, size, price, cost))), p)


def solve(problem):
    # Bare scales are natural English quantities but are not shared cardinal
    # tokens. Normalize locally, leaving the shared reader unchanged.
    normalized = re.sub(r'\b(?:a|an) (hundred|thousand|million)\b', r'one \1', problem.text, flags=re.I)
    normalized = re.sub(r'\bone ([a-z]+-dollar (?:bill|note))\b', r'a \1', normalized, flags=re.I)
    normalized = re.sub(r'\bquarters\b(?!\s+of\b)', 'quartercoins', normalized, flags=re.I)
    if normalized != problem.text:
        problem = Problem.read(normalized)
        if problem is None:
            return None
    ns = _numbers(problem)
    if not 2 <= len(ns) <= 12 or any(n.kind == 'percent' or n.value < 0 for n in ns):
        return None
    if re.match(r'how many (?!dollars?\b|cents?\b|euros?\b)', problem.question):
        return _output(problem, _missing_count(problem, ns))
    currencies = _currencies(problem, ns)
    if len(currencies) > 1:
        return None
    coins = _coin_value(problem, ns)
    if coins is not None:
        return _output(problem, coins)
    if not any(n.kind == 'money' for n in ns):
        return None
    if not _has(r'\b(?:money|dollars?|cents?|pay|paid|paying|spend|spent|costs?|price|earn|earned|earnings|income|make|made|change|profit|salary|left|remaining|raise|raised|save|saved|savings|lose|lost|bills?|charge)\b', problem.question):
        return _missing_count(problem, ns)
    if _has(r'\b(?:equally|evenly|average|ratio)\b', problem.text.lower()):
        return None
    owners = set(re.findall(r'\b([A-Z][a-z]+) (?:has|had|spent|spends|earns|earned|saved|buys|bought)\b', problem.text[:len(problem.body)]))
    owners = {n for n in owners if n.lower() not in _STOP}
    if len(owners) > 1 and not _has(r'\b(?:total|together|combined|altogether|their|they|difference|than)\b', problem.question):
        return None
    if _has(r'\b(?:per|each)\b', re.split(r'\b(?:if|when)\b', problem.question)[0]):
        return _output(problem, _schedule(problem, ns))
    if _has(r'\b(?:overtime|double that amount|triple that amount)\b', problem.body):
        return _output(problem, _overtime(problem, ns))
    if _has(r'\bbonus\b', problem.body):
        return None
    for rule in (_grouped_price, _menu, _recipe_margin, _area_cost, _calendar_depreciation, _threshold_discount, _comparative_quantity, _exception_price, _inventory_profit, _packed_profit, _rate_saving,
                 _fill_change, _sales_remainder,
                 _cash_option, _package_change, _labor_parts, _installments, _schedule, _basket):
        answer = rule(problem, ns)
        if answer is not None:
            return _output(problem, answer)
    return None
