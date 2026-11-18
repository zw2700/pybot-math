"""Exact short rate problems with explicit stocks, intervals and equal shares.

Units are read before choosing an operation. Each schema accounts for all
quantities; unsupported clauses and ambiguous unit joins cause abstention.
"""
import re
from dataclasses import replace
from fractions import Fraction

from ..numbers import format_number
from . import rates_and_unit_rates_r07_a4 as previous
from . import rates_and_unit_rates_r03_a5 as core
from ._rates_common import noun_head, dimensional_products, whole_count, each_subject


_TIME = previous._TIME
_WEEKDAYS = {'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'}
_STOP = previous._STOP | set(('fall falls fell wants want aim aims complete '
                             'completes tie ties weigh weighs wide tall long '
                             'growing grow grows live lives decided '
                             'received receive '
                             'sneezes sneeze spend spends used uses use').split())


def _normal(word):
    return previous._normal(word)


def _head(tail):
    return noun_head(tail, _STOP, _normal, core._MEASURES | {'money', 'cent', 'mph'})


def _unit(p, n):
    if n.kind == 'money':
        return 'money'
    tail = p.text[n.end:].lower()
    tail = re.sub(r'^\s+of (?:a|an|the)\s+', ' ', tail)
    if re.match(r'\s+of them\b', tail) and re.search(r'\bthere are\s*$', p.text[:n.start].lower()):
        return 'person'
    if re.search(r'\bfamily of\s*$', p.text[:n.start].lower()):
        return 'person'
    tail = re.sub(r'^\s+(?:more|additional|extra|equal(?:-sized)?)\s+', ' ', tail)
    return _head(tail)


def _numbers(p):
    ns = []
    for n in p.numbers:
        before, after = p.text[:n.start].lower(), p.text[n.end:].lower()
        # Referential "each one" has no measured quantity of its own.
        if n.value == 1 and re.search(r'\beach\s*$', before) and re.match(r'\s*[,.;!?]', after):
            continue
        if n.start >= len(p.body) and any(
                n.value == old.value and _unit(p, n) == _unit(p, old) for old in ns):
            continue
        if re.match(r'\s+dozens?\b', after):
            n = replace(n, value=n.value*12)
        ns.append(n)
    return ns


def _asked(p):
    if p.question.startswith('how fast'):
        return 'speed'
    if re.match(r'how much does each .+ weigh', p.question):
        units = {_unit(p, n) for n in p.numbers} & core._MEASURES
        return next(iter(units)) if len(units) == 1 else ''
    return previous._asked(p)


def _denoms(p, ns, us):
    ds = previous._denoms(p, ns, us)
    t = p.text.lower()
    for i, n in enumerate(ns):
        before = re.split(r'[.!?;](?:\s|$)', t[:n.start])[-1]
        end = ns[i+1].start if i+1 < len(ns) else len(t)
        if n.start < len(p.body):
            end = min(end, len(p.body))
        after = re.split(r'[.!?;](?:\s|$)', t[n.end:end])[0]
        # A later sentence's question does not state a rate for this amount.
        if ds[i] and not re.search(r'\b(?:each|every|per)\b', before+' '+after):
            explicit = any(re.search(r'\b(?:an?|one) '+re.escape(d)+r'\b', before+' '+after)
                           or re.search(r'\b'+re.escape(d)+r's? of\s*$', before) for d in ds[i])
            if not explicit:
                ds[i] = []
        if us[i] == 'mph':
            ds[i] = ['hour']
        subject = each_subject(before, _normal, _STOP, us)
        if subject and not re.search(r'\b(?:per|each|every)\b', after):
            ds[i] = [subject]
        # In "each type costs X per pound", pound is the price unit;
        # 'type' identifies a category rather than a second denominator.
        per = re.search(r'\bper ([a-z]+)\b', after)
        if per:
            ds[i] = [_normal(per.group(1))]
        # A measurement adjective modifies the entire container noun phrase:
        # "N-liter water bottle" and "bottles of N-liter water".
        pack = re.match(r'-([a-z]+)[ -]+([^.!?;,]+)', after)
        if pack and _normal(pack.group(1)) in core._MEASURES:
            container = re.search(r'\b([a-z]+s) of\s*$', before)
            den = _normal(container.group(1)) if container else _head(pack.group(2))
            if den and den not in _STOP and den != us[i]:
                ds[i] = [den]
        # "N hours to complete a task" is time per task, not elapsed
        # time for an unspecified number of tasks.
        task = re.search(r'\bto [a-z]+ (?:a|an|each) ([a-z]+(?: [a-z]+){0,2})', after)
        if task and (us[i] in _TIME or re.search(r'\beach\b', task.group(0))):
            den = _head(task.group(1))
            if den:
                ds[i] = [den]
        subject = re.search(r'\beach ([a-z]+) (?:has|have) to be\s*$', before)
        if subject:
            ds[i] = [_normal(subject.group(1))]
        if i and re.search(r'\beach with\s*$', before):
            ds[i] = [us[i-1]]
        price_subject = re.search(r'\b([a-z]+) costs?\s*$', before)
        if n.kind == 'money' and price_subject and re.match(r'\s+each\b', after):
            ds[i] = [_normal(price_subject.group(1))]
        if n.kind == 'money' and ds[i] == ['normally']:
            subject = re.search(r'\b([a-z]+s) that normally costs?\s*$', before)
            if subject:
                ds[i] = [_normal(subject.group(1))]
        composition = re.search(r'\b([a-z]+s) (?:that )?(?:yield|produce|contain|hold|are)\s*$', before)
        if composition and re.search(r'\beach\b', after):
            ds[i] = [_normal(composition.group(1))]
        relative = re.search(r'\b([a-z]+s),? which (?:use|need|hold|contain)\s*$', before)
        if relative and re.search(r'\beach\b', after):
            ds[i] = [_normal(relative.group(1))]
        divided = re.search(r'\beach ([a-z]+(?:[ -]+[a-z]+){0,2}) into\s*$', before)
        if divided:
            ds[i] = [_head(divided.group(1))]
        if re.search(r'\bfor (?:a |one )?(?:single )?person\b', after):
            ds[i] = ['person']
        # In a capacity comparison, "N bytes each" in the question
        # still refers to the original kind of stored item.
        if n.start >= len(p.body) and re.match(r'\s+[a-z]+ each\b', after):
            if re.search(r'\b(?:hold|fit|capacity)\b', p.body) and us and us[0] != us[i]:
                ds[i] = [us[0]]
        ds[i] = list(dict.fromkeys(_normal(d) for d in ds[i] if d))
    # A shared trailing rate applies to coordinated amounts in one clause,
    # e.g. "A adds N liters and B adds M liters each trip".
    for i, n in enumerate(ns):
        clause = core._sentence(t, n)
        rate = re.search(r'\b(?:each|every) (trip|day|week|hour|minute)\b', clause)
        peers = [j for j, other in enumerate(ns) if core._sentence(t, other) == clause]
        if (rate and len(peers) == 2 and len({us[j] for j in peers}) == 1
                and us[i] not in _TIME and re.search(r'\band\b', clause)
                and re.search(r'\b(?:adds?|carries|carry|uses?|eats?|drinks?)\b', clause)):
            for j in peers:
                if not ds[j]:
                    ds[j] = [rate.group(1)]
    return ds


def _f(value):
    return format_number(value.value if hasattr(value, 'value') else value)


def _result(p, value, expression):
    if value < 0:
        return None
    return previous._result(p, value, expression)


def _residual(p, ns, us, ds):
    """An initial stock minus consumed/left stock, then a stated rate."""
    if len(ns) != 3:
        return None
    t = p.text.lower()
    asked = _asked(p)
    rates = [i for i in range(3) if ds[i] == [asked] and us[i] != asked]
    if len(rates) == 1:
        r = rates[0]
        stocks = [i for i in range(3) if i != r]
        a, b = stocks
        if (a != 0 or us[a] != us[r] or us[b] not in (us[a], '')
                or ds[a] or ds[b]):
            return None
        local = core._sentence(t, ns[b])
        if not ((re.search(r'\b(?:left|remaining|rest|change)\b', t)
                 and re.search(r'\b(?:ate|eaten|used|uses?|gave|give|left|remaining|change)\b', local))
                or re.search(r'\b(?:not ripe|unusable|damaged|rotten|unripe|broken)\b', local)):
            return None
        return _result(p, (ns[a].value-ns[b].value)/ns[r].value,
                       '({} - {}) / {}'.format(_f(ns[a]), _f(ns[b]), _f(ns[r])))
    # A remainder is explicitly shared into N groups. Include the owner
    # only when the text explicitly says "him/her and N friends".
    if (any(ds) or us[0] not in (us[1], asked) or us[1] not in (us[0], '')
            or not re.search(r'\b(?:rest|remaining)\b', t)
            or not re.search(r'\b(?:equally|evenly)\b', t)):
        return None
    if not re.search(r'\b(?:ate|eaten|gave|give|used|uses?)\b', t[ns[0].end:ns[1].start]):
        return None
    groups = ns[2].value
    if re.search(r'\b(?:him|her|himself|herself|me|myself) and (?:his |her |my )?$', t[:ns[2].start]):
        groups += 1
    if asked == us[0] or re.search(r'\beach .+ weigh', p.question):
        return _result(p, (ns[0].value-ns[1].value)/groups,
                       '({} - {}) / {}'.format(_f(ns[0]), _f(ns[1]), _f(groups)))
    return None


def _equal_sharing(p, ns, us, ds):
    if len(ns) != 3 or not re.search(r'\b(?:equally|evenly|equal number|same number|same amount)\b', p.text.lower()):
        return None
    if not re.search(r'\b(?:each|per)\b', p.question):
        return None
    if re.search(r'\b(?:lost|ate|eaten|removed|remaining|left|rest|less|more|twice|thrice|double|triple)\b', p.text.lower()):
        return None
    # A storage location is not a per-location rate when the whole stock
    # is being distributed among a different group of recipients.
    if ds[0] and re.search(r'\b(?:share|divide|give|distribute)\b', p.body):
        if not re.search(r'\b(?:each|every|per)\b', core._sentence(p.body, ns[0])):
            ds = [[], ds[1], ds[2]]
    if any(ds):
        return None
    asked = _asked(p)
    if us[0] == asked and re.search(r'\band\s*$', p.text[ns[1].end:ns[2].start].lower()):
        # Explicitly coordinated recipient counts, e.g. N adults and M children.
        if us[1] != asked and us[2] != asked:
            return _result(p, ns[0].value/(ns[1].value+ns[2].value),
                           '{} / ({} + {})'.format(*(_f(n) for n in ns)))
    recipients = [i for i in range(3) if re.search(
        r'\beach\s+'+re.escape(us[i])+r'(?:s|es)?\b', p.question)]
    if len(recipients) != 1:
        return None
    c = recipients[0]
    a, b = [i for i in range(3) if i != c]
    people = {'boy', 'girl', 'man', 'woman', 'person'}
    if us[a] == us[b] == asked or (asked == 'person' and us[a] in people and us[b] in people):
        if asked == 'money' and not re.search(r'\b(?:combined|together|collected|raised|earned|share|shared)\b', p.body):
            return None
        return _result(p, (ns[a].value+ns[b].value)/ns[c].value,
                       '({} + {}) / {}'.format(_f(ns[a]), _f(ns[b]), _f(ns[c])))
    return None


def _combined_prices(p, ns, us, ds):
    if len(ns) != 3 or us != ['money']*3:
        return None
    rates = [i for i in range(3) if ds[i] == [_asked(p)]]
    if len(rates) != 1 or not re.search(r'\btotal\b', p.question):
        return None
    r = rates[0]
    a, b = [i for i in range(3) if i != r]
    if ds[a] or ds[b] or not re.search(r'\b(?:spent|spends|paid|pays)\b', p.body):
        return None
    return _result(p, (ns[a].value+ns[b].value)/ns[r].value,
                   '({} + {}) / {}'.format(_f(ns[a]), _f(ns[b]), _f(ns[r])))


def _interval(p, ns, us, ds):
    if len(ns) != 2 or not all(u in _TIME for u in us) or any(ds) or _asked(p) in _TIME:
        return None
    t = p.text.lower()
    intervals = [i for i, n in enumerate(ns) if re.search(r'\b(?:once )?every\s*$', t[:n.start])]
    if len(intervals) != 1 or not re.search(r'^how many (?:times|[a-z]+)\b', p.question):
        return None
    i = intervals[0]
    a = 1-i
    duration = previous._convert(ns[a].value, us[a], us[i])
    if duration is not None:
        return _result(p, duration/ns[i].value,
                       '{} {} / {} {}'.format(_f(duration), us[i], _f(ns[i]), us[i]))
    return None


def _periodic_duration(p, ns, us, ds):
    if len(ns) != 3 or not all(u in _TIME for u in us) or any(ds):
        return None
    t = p.text.lower()
    intervals = [i for i, n in enumerate(ns) if re.search(r'\bevery\s*$', t[:n.start])]
    if len(intervals) != 1 or not re.search(r'\b(?:time|minutes|hours)\b', p.question):
        return None
    i = intervals[0]
    durations = [j for j in range(3) if j != i and re.search(
        r'\b(?:takes?|spends?)\b[^.!?;]*$', t[:ns[j].start])]
    if len(durations) != 1:
        return None
    d = durations[0]
    span = next(j for j in range(3) if j not in (i, d))
    # Calendar convention for a recurring weekly schedule over a year.
    if us[span] == 'year' and us[i] == 'week':
        periods = ns[span].value*52/ns[i].value
    else:
        converted = previous._convert(ns[span].value, us[span], us[i])
        if converted is None:
            return None
        periods = converted/ns[i].value
    requested = re.search(r'^how many (seconds?|minutes?|hours?)\b', p.question)
    target = _normal(requested.group(1)) if requested else us[d]
    value = previous._convert(periods*ns[d].value, us[d], target)
    return _result(p, value, '{} occurrences * {} {}'.format(_f(periods), _f(ns[d]), us[d])) if value is not None else None


def _net_flow(p, ns, us, ds):
    if len(ns) != 3 or len(set(us)) != 1 or _asked(p) not in _TIME:
        return None
    t = p.text.lower()
    # In opposing flows, a trailing daily interval is the rate denominator;
    # an incidental indefinite noun ("feet of a vine") is not a unit rate.
    ds = [list(d) for d in ds]
    for i, n in enumerate(ns):
        after = t[n.end:ns[i+1].start if i+1 < len(ns) else len(p.body)]
        after = re.split(r'[.!?;](?:\s|$)', after)[0]
        temporal = re.findall(r'\b(?:per|each|every|a|an) (second|minute|hour|day|night|week|month|year)\b', after)
        if len(set(temporal)) == 1:
            ds[i] = [_normal(temporal[0])]
    rates = [i for i in range(3) if ds[i] == [_asked(p)]]
    if len(rates) != 2:
        return None
    a, b = rates
    stock = next(i for i in range(3) if i not in rates)
    if ds[stock] or not re.search(r'\b(?:but|while)\b', t):
        return None
    removes = r'\b(?:removes?|strips?|loses?|uses?|drains?|spends?)\b'
    adds = r'\b(?:grows?|gains?|adds?|refills?|earns?)\b'
    directions = {}
    for i in rates:
        local = t[ns[i-1].end if i else 0:ns[i].start]
        subtracts, increases = bool(re.search(removes, local)), bool(re.search(adds, local))
        if subtracts == increases:
            return None
        directions[i] = -1 if subtracts else 1
    if set(directions.values()) != {-1, 1}:
        return None
    net = sum((directions[i]*ns[i].value for i in rates), Fraction(0))
    if re.search(removes, p.question):
        net = -net
    elif not re.search(adds, p.question):
        return None
    if net > 0:
        return _result(p, ns[stock].value/net,
                       '{} / ({} - {})'.format(_f(ns[stock]), _f(max(ns[a].value, ns[b].value)), _f(min(ns[a].value, ns[b].value))))
    return None


def _capacity_exchange(p, ns, us, ds):
    """The same capacity holds N old-size items or an unknown new-size count."""
    if (len(ns) == 3 and us[0] == _asked(p) and us[1] == us[2]
            and ds == [[], [us[0]], [us[0]]]
            and ns[2].start >= len(p.body)
            and re.search(r'\b(?:hold|fit|capacity)\b', p.body)):
        return _result(p, ns[0].value*ns[1].value/ns[2].value,
                       '{} * {} / {}'.format(*(_f(n) for n in ns)))
    return None


def _rotating_groups(p, ns, us, ds):
    if (len(ns) != 4 or any(ds) or us[0] != us[2] or us[0] != _asked(p)
            or ns[0].value != ns[2].value or us[1] not in _TIME or us[3] not in _TIME):
        return None
    t = p.text.lower()
    if not re.search(r'\bat a time\b', t[:ns[1].start]) or not re.search(
            r'\bthen another\s*$', t[:ns[2].start]):
        return None
    if not re.search(r'\b(?:each|every)\b', t[ns[0].end:ns[1].start]):
        return None
    span = previous._convert(ns[3].value, us[3], us[1])
    if span is not None:
        return _result(p, ns[0].value*span/ns[1].value,
                       '{} * {} / {}'.format(_f(ns[0]), _f(span), _f(ns[1])))
    return None


def _area_density(p, ns, us, ds):
    if len(ns) != 4 or any(ds) or us[0] != us[1] or us[3] != us[0] or us[2] != _asked(p):
        return None
    t = p.text.lower()
    if not (re.match(r'\s+[a-z]+ long\b', t[ns[0].end:])
            and re.match(r'\s+[a-z]+ wide\b', t[ns[1].end:])
            and re.fullmatch(r'\s+[a-z]+ per\s+', t[ns[2].end:ns[3].start])
            and re.match(r'\s+square\b', t[ns[3].end:])):
        return None
    return _result(p, ns[0].value*ns[1].value*ns[2].value/ns[3].value,
                   '{} * {} * {} / {}'.format(*(_f(n) for n in ns)))


def _recurring_net_cost(p, ns, us, ds):
    if len(ns) != 3 or us != ['money']*3 or _asked(p) not in _TIME:
        return None
    t = p.text.lower()
    if not (ds[0] == [_asked(p)] and not ds[2]
            and re.search(r'\b(?:buy|buys|buying|spends?)\b', core._sentence(t, ns[0]))
            and re.search(r'\b(?:sell|sells|selling)\b', core._sentence(t, ns[1]))
            and re.search(r'\b(?:starts?|starting) with\s*$', t[:ns[2].start])
            and re.search(r'\bout of money\b', p.question)):
        return None
    # The query explicitly describes one purchase/resale cycle per period.
    if not re.search(r'\bbuy\b.*\band sell\b', p.question) or ns[0].value <= ns[1].value:
        return None
    return _result(p, ns[2].value/(ns[0].value-ns[1].value),
                   '{} / ({} - {})'.format(_f(ns[2]), _f(ns[0]), _f(ns[1])))


def _combined_flow(p, ns, us, ds):
    """Two explicitly parallel consumption/production rates and one stock."""
    if len(ns) != 3 or _asked(p) not in _TIME | {'trip'}:
        return None
    t = p.text.lower()
    rates = [i for i in range(3) if ds[i] == [_asked(p)]]
    if len(rates) != 2:
        return None
    a, b = rates
    s = next(i for i in range(3) if i not in rates)
    if ds[s] or not us[s] or us[a] not in (us[s], '') or us[b] not in (us[s], ''):
        return None
    consume = r'\b(?:eats?|gives?|uses?|burns?|consumes?|spends?|drinks?)\b'
    produce = r'\b(?:adds?|fills?|makes?|produces?|collects?|cuts?|carries|carry)\b'
    clauses = [core._sentence(t, ns[i]) for i in rates]
    if not (all(re.search(consume, c) and not re.search(produce, c) for c in clauses)
            or all(re.search(produce, c) and not re.search(consume, c) for c in clauses)):
        return None
    if re.search(r'\b(?:but|instead|faster|slower|more|less)\b', t):
        return None
    return _result(p, ns[s].value/(ns[a].value+ns[b].value),
                   '{} / ({} + {})'.format(_f(ns[s]), _f(ns[a]), _f(ns[b])))


def _batch_repetitions(p, ns, us, ds):
    if len(ns) != 3 or _asked(p) != 'time' or ds[0] or ds[1] or ds[2] != [us[1]] or us[0] != us[2]:
        return None
    if not (re.search(r'\b(?:seats?|holds?|carries|carry)\b', core._sentence(p.text.lower(), ns[2]))
            and re.search(r'\b(?:run|trip|turn|ride)\b', p.question)):
        return None
    value = ns[0].value/(ns[1].value*ns[2].value)
    return _result(p, Fraction(-(-value.numerator//value.denominator)),
                   '{} / ({} * {})'.format(*(_f(n) for n in ns)))


def _mixture_fraction(p, ns, us, ds):
    """An explicit two-ingredient ratio and the mass of the mixture."""
    if len(ns) != 3 or len(set(us)) != 1 or us[0] not in core._MEASURES:
        return None
    if not re.search(r'\bratio\b', p.body) or any(ds):
        return None
    t = p.text.lower()
    labels = []
    for n in ns[:2]:
        m = re.match(r'\s+[a-z]+ of ([a-z]+)\b', t[n.end:])
        labels.append(_normal(m.group(1)) if m else '')
    q = re.match(r'how (?:many|much) [a-z]+ of ([a-z]+)\b', p.question)
    if not q or not all(labels) or labels[0] == labels[1] or _normal(q.group(1)) not in labels:
        return None
    component = labels.index(_normal(q.group(1)))
    return _result(p, ns[2].value*ns[component].value/(ns[0].value+ns[1].value),
                   '{} * {} / ({} + {})'.format(_f(ns[2]), _f(ns[component]), _f(ns[0]), _f(ns[1])))


def _unread_stock(p, ns, us, ds):
    """Already completed groups plus an explicitly unused amount in groups."""
    if len(ns) != 3 or ds[0] != [_asked(p)] or us[1] != _asked(p) or us[2] != us[0] or ds[1] or ds[2]:
        return None
    t = p.text.lower()
    if not (re.search(r'\bin all\b|\btotal\b', p.question)
            and re.search(r'\b(?:never|not|unused|unread|unheard)\b', core._sentence(t, ns[2]))):
        return None
    return _result(p, ns[1].value+ns[2].value/ns[0].value,
                   '{} + {} / {}'.format(_f(ns[1]), _f(ns[2]), _f(ns[0])))


def _daily_item_total(p, ns, us, ds):
    if len(ns) != 3 or _asked(p) not in {'item', 'object'}:
        return None
    if not re.search(r'\b(?:same daily amount|same (?:number|amount).*each day)\b', p.question):
        return None
    days = [i for i in range(3) if us[i] == 'day' and not ds[i]]
    if len(days) != 1:
        return None
    d = days[0]
    rest = [i for i in range(3) if i != d]
    if any(ds[i] or not us[i] or us[i] in _TIME | {'money'} for i in rest):
        return None
    a, b = rest
    return _result(p, (ns[a].value+ns[b].value)/ns[d].value,
                   '({} + {}) / {}'.format(_f(ns[a]), _f(ns[b]), _f(ns[d])))


def _time_comparison(p, ns, us, ds):
    """Compare a measured journey time with a supplied time or speed."""
    if len(ns) != 3:
        return None
    t = p.text.lower()
    if (us[0] == 'mph' and us[1] == 'mile' and us[2] in _TIME
            and re.search(r'\b(?:win|beat|faster)\b', p.question)):
        own_time = previous._convert(ns[1].value/ns[0].value, 'hour', us[2])
        if own_time is not None:
            return _result(p, ns[2].value-own_time,
                           '{} - {} {}'.format(_f(ns[2]), _f(own_time), us[2]))
    if (us[0] == 'mile' and us[1] in _TIME and us[2] == 'mph'
            and re.search(r'\b(?:above|over) the speed limit\b', p.question)):
        hours = previous._convert(ns[1].value, us[1], 'hour')
        if hours:
            return _result(p, ns[0].value/hours-ns[2].value,
                           '{} / {} - {}'.format(_f(ns[0]), _f(hours), _f(ns[2])))
    return None


def _scheduled_sum(p, ns, us, ds):
    if len(ns) != 3 or len(set(us)) != 1 or _asked(p) != 'day' or any(ds):
        return None
    t = p.text.lower()
    if not (re.search(r'\btwice a day\b', p.body)
            and re.search(r'\bin the morning\b', t[ns[0].end:ns[1].start])
            and re.search(r'\bin the evening\b', t[ns[1].end:ns[2].start])):
        return None
    return _result(p, ns[2].value/(ns[0].value+ns[1].value),
                   '{} / ({} + {})'.format(_f(ns[2]), _f(ns[0]), _f(ns[1])))


def _annual_growth(p, ns, us, ds):
    if len(ns) != 2 or us[0] != us[1] or us[0] != _asked(p) or us[0] not in core._MEASURES:
        return None
    if not (re.search(r'\bmonthly growth rate\b', p.question)
            and re.search(r'\bafter a year\b', p.body)
            and re.search(r'\bcurrently\b', p.body)):
        return None
    return _result(p, (ns[0].value-ns[1].value)/12,
                   '({} - {}) / 12'.format(_f(ns[0]), _f(ns[1])))


def _shared_carry(p, ns, us, ds):
    """Two named participants explicitly have the same carrying capacity."""
    if len(ns) != 2 or us[0] != us[1] or _asked(p) != 'trip':
        return None
    t = p.text.lower()
    if not (re.search(r'\bwith each trip\b', core._sentence(t, ns[0]))
            and re.search(r'\b(?:brother|sister|friend|partner|colleague) can carry the same amount\b', p.body)
            and re.search(r'\bit take them to carry\b', p.question)):
        return None
    value = ns[1].value/(2*ns[0].value)
    return _result(p, Fraction(-(-value.numerator//value.denominator)),
                   '{} / (2 * {})'.format(_f(ns[1]), _f(ns[0])))


def _weekly_unit_batches(p, ns, us, ds):
    """An explicitly measured closed loop turns distance into lap counts."""
    if len(ns) != 2 or us[0] != us[1] or us[0] not in {'mile', 'kilometer', 'meter', 'foot', 'yard'}:
        return None
    if _asked(p) not in {'loop', 'lap'} or not re.search(r'\bper day\b', p.question):
        return None
    t = p.text.lower()
    if ds[0] != ['week'] or not re.match(r'\s+[a-z]+ around\b', t[ns[1].end:]):
        return None
    if not re.search(r'\bsame amount each day\b', t):
        return None
    return _result(p, ns[0].value/ns[1].value/7,
                   '{} / {} / 7'.format(_f(ns[0]), _f(ns[1])))


def _ratio_chain(p, ns, us, ds):
    """A measured pair ('N items weigh M mass') is one conversion rate."""
    if not 3 <= len(ns) <= 4:
        return None
    t = p.text.lower()
    pairs = []
    for i in range(len(ns)-1):
        middle = t[ns[i].end:ns[i+1].start]
        if re.fullmatch(r'\s+[a-z]+(?: of [a-z]+)?\s+(?:weighs?|(?:to|can) (?:make|produce|yield)|per|for every)\s+', middle):
            if not ds[i] and not ds[i+1] and us[i] and us[i+1]:
                pairs.append(i)
    if len(pairs) != 1 or re.search(r'\b(?:left|remaining|more|less|twice|half|difference|profit)\b', t):
        return None
    i = pairs[0]
    local_us = list(us)
    if not local_us[0] and re.search(r'\bpopulation\b[^.!?;]*$', t[:ns[0].start]):
        local_us[0] = 'person'
    if not all(local_us):
        return None
    atoms = [core._amount(n.value, u, den, _f(n), [j]) for j, (n, u, den) in enumerate(zip(ns, local_us, ds))]
    ratio = core._combine(atoms[i], atoms[i+1], True)
    atoms = [a for j, a in enumerate(atoms) if j not in (i, i+1)] + [ratio]
    target = _target(p, _asked(p), local_us)
    if target is None or not target.dims:
        return None
    answers = {}
    for value, signs in dimensional_products([(a.value, a.dims) for a in atoms], target.dims):
        # Stocks remain direct; only the explicit conversion can invert.
        if any(sign < 0 and not any(power < 0 for unit, power in a.dims) for a, sign in zip(atoms, signs)):
            continue
        answers[value/target.value] = signs
    if len(answers) != 1:
        return None
    value, signs = next(iter(answers.items()))
    return _result(p, value, ' * '.join(a.expression if s > 0 else '(1 / {})'.format(a.expression)
                                      for a, s in zip(atoms, signs))+' (in compatible units)')


def _money_goal(p, ns, us, ds):
    if (len(ns) != 4 or us != ['money']*4 or any(ds[:3])
            or ds[3] != [_asked(p)]):
        return None
    t = p.text.lower()
    if not (re.search(r'\b(?:costs?|needs?|goal)\b', core._sentence(t, ns[0]))
            and re.search(r'\b(?:gets?|received?|given)\b', core._sentence(t, ns[1]))
            and re.search(r'\b(?:sell|earn|raise)\b', p.question)
            and re.search(r'\b(?:rest|goal|save up)\b', t)):
        return None
    value = (ns[0].value-ns[1].value-ns[2].value)/ns[3].value
    return _result(p, whole_count(value, p.question),
                   '({} - {} - {}) / {}'.format(*(_f(n) for n in ns)))


def _daily_expenses(p, ns, us, ds):
    if (len(ns) != 3 or us != ['money']*3 or ds[0] != ['day'] or ds[1] != ['day']
            or ds[2] != [_asked(p)] or not re.search(r'\bcover (?:her |his |their |the )?expenses\b', p.question)):
        return None
    return _result(p, whole_count((ns[0].value+ns[1].value)/ns[2].value, p.question),
                   '({} + {}) / {}'.format(*(_f(n) for n in ns)))


def _batch_unit_price(p, ns, us, ds):
    if len(ns) != 3 or us[0] != us[2] or not us[0] or us[1] != 'money' or _asked(p) != 'money' or any(ds):
        return None
    t = p.text.lower()
    if not (core._sentence(t, ns[0]) == core._sentence(t, ns[1])
            and re.search(r'\bcosts?\b', t[ns[0].end:ns[1].start])
            and ns[2].start >= len(p.body)):
        return None
    if re.search(r'\b(?:more|less|discount|instead|additional|left)\b', t):
        return None
    return _result(p, ns[1].value/ns[0].value*ns[2].value,
                   '{} / {} * {}'.format(_f(ns[1]), _f(ns[0]), _f(ns[2])))


def _compare_observed_rates(p, ns, us, ds):
    if len(ns) != 4 or any(ds) or us[0] != us[2] or us[1] not in _TIME or us[3] not in _TIME:
        return None
    q = p.question
    if not re.search(r'\b(?:speed|rate)\b', q) or not re.search(r'\b(?:higher|lower|faster|slower|fastest|slowest)\b', q):
        return None
    t = p.text.lower()
    if not all(core._sentence(t, ns[i]) == core._sentence(t, ns[i+1]) for i in (0, 2)):
        return None
    per = re.search(r'\bper (second|minute|hour|day|week)\b', q)
    target = per.group(1) if per else us[1]
    times = [previous._convert(ns[i].value, us[i], target) for i in (1, 3)]
    if any(x is None or not x for x in times):
        return None
    rates = [ns[0].value/times[0], ns[2].value/times[1]]
    value = min(rates) if re.search(r'\b(?:lower|slower|slowest)\b', q) else max(rates)
    return _result(p, value, 'Compare {} and {} per {}'.format(_f(rates[0]), _f(rates[1]), target))


def _duty_cycle(p, ns, us, ds):
    if len(ns) != 2 or not all(u in _TIME for u in us):
        return None
    t = p.text.lower()
    if not (re.search(r'\bevery\s*$', t[:ns[0].start])
            and re.search(r'\beach time\b', t[ns[0].end:ns[1].start])):
        return None
    numerator = _asked(p)
    denominator = re.search(r'\bper (second|minute|hour|day|week)\b', p.question)
    if numerator not in _TIME or not denominator:
        return None
    span = previous._convert(Fraction(1), denominator.group(1), us[0])
    duration = previous._convert(ns[1].value, us[1], numerator)
    if span is None or duration is None:
        return None
    return _result(p, span/ns[0].value*duration,
                   '{} / {} * {}'.format(_f(span), _f(ns[0]), _f(duration)))


def _weekly_schedule(p, ns, us, ds):
    if len(ns) != 3 or len(set(us)) != 1 or _asked(p) != 'week' or ds[0]:
        return None
    if (not all(len(d) == 1 and d[0] in _WEEKDAYS for d in ds[1:])
            or ds[1] == ds[2] or not re.search(r'\beach week\b', p.body)):
        return None
    value = ns[0].value/(ns[1].value+ns[2].value)
    return _result(p, Fraction(-(-value.numerator//value.denominator)),
                   '{} / ({} + {})'.format(_f(ns[0]), _f(ns[1]), _f(ns[2])))


def _interval_with_definition(p, ns, us, ds):
    if len(ns) != 3 or us[2] not in _TIME or len(ds[2]) != 1 or ds[2][0] not in _TIME:
        return None
    if not re.search(r'\beach [a-z]+ is\s*$', p.text[:ns[2].start].lower()):
        return None
    conversion = previous._convert(ns[2].value, us[2], ds[2][0])
    if conversion != 1:
        return None
    return _interval(p, ns[:2], us[:2], ds[:2])


def _pooled_shares(p, ns, us, ds):
    """Combine explicitly shared stocks, including an explicitly included host."""
    if not 3 <= len(ns) <= 5:
        return None
    t = p.text.lower()
    if re.search(r'\b(?:lost|ate|eaten|removed|remaining|left|rest|less|more|twice|thrice|double|triple)\b', t):
        return None
    if not re.search(r'\b(?:share|shared|equally|evenly|exact same amount|equal amount|equal number)\b', t):
        return None
    if not re.search(r'\beach\b', p.question):
        return None
    groups = [i for i in range(len(ns)) if us[i] == 'person']
    if len(groups) != 1:
        return None
    g = groups[0]
    stocks = [i for i in range(len(ns)) if i != g]
    if any(ds[i] for i in stocks):
        return None
    if ds[g] and not (len(ds[g]) == 1 and ds[g][0] not in us
                      and re.search(r'\b[a-z]+ of\s*$', t[:ns[g].start])):
        return None
    asked = _asked(p)
    if any(not us[i] or us[i] in _TIME | {'money', 'person'} for i in stocks):
        return None
    if len({us[i] for i in stocks}) != 1:
        # Distinct categories need an explicit promise to distribute the
        # combined number equally, not separate unknown portion sizes.
        if not re.search(r'\b(?:exact same amount|equal amount)\b', t) or asked in {us[i] for i in stocks}:
            return None
    elif asked != us[stocks[0]]:
        return None
    count = ns[g].value
    if re.search(r'\b(?:herself|himself|myself|him|her|me) and (?:his |her |my )?$', t[:ns[g].start]):
        count += 1
    value = sum((ns[i].value for i in stocks), Fraction(0))/count
    return _result(p, value, '({}) / {}'.format(' + '.join(_f(ns[i]) for i in stocks), _f(count)))


def _several_removals(p, ns, us, ds):
    if not 4 <= len(ns) <= 8 or any(ds):
        return None
    t = p.text.lower()
    if not re.search(r'\bremaining\b.*\bequally\b|\bequally\b.*\bremaining\b', t):
        return None
    recipients = [i for i, n in enumerate(ns) if re.search(r'\bamong (?:his |her |their )?$', t[:n.start])]
    totals = [i for i, n in enumerate(ns) if re.search(r'\boriginally (?:[a-z]+ ){1,3}$', t[:n.start])]
    if len(recipients) != 1 or len(totals) != 1:
        return None
    g, a = recipients[0], totals[0]
    if us[a] != _asked(p) or us[g] != 'person':
        return None
    removed = [i for i in range(len(ns)) if i not in (g, a)]
    for i in removed:
        if (us[i] not in ('', us[a]) or i >= g
                or not re.match(r'\s+(?:[a-z]+(?: [a-z]+){0,2} )?to\b', t[ns[i].end:])
                or not re.search(r'\b(?:gave|gives|give)\b', core._sentence(t, ns[i]))):
            return None
    value = (ns[a].value-sum((ns[i].value for i in removed), Fraction(0)))/ns[g].value
    return _result(p, value, '({} - ({})) / {}'.format(_f(ns[a]), ' + '.join(_f(ns[i]) for i in removed), _f(ns[g])))


def _group_shortfall(p, ns, us, ds):
    if len(ns) != 3 or ds[0] or ds[1] or ds[2] != [us[0]] or us[1] != us[2] or _asked(p) != us[1]:
        return None
    if not (re.search(r'^how many more\b', p.question)
            and re.search(r'\bneeds?\b', core._sentence(p.text.lower(), ns[2]))):
        return None
    return _result(p, ns[2].value-ns[1].value/ns[0].value,
                   '{} - {} / {}'.format(_f(ns[2]), _f(ns[1]), _f(ns[0])))


def _fixed_budget_exchange(p, ns, us, ds):
    if len(ns) != 3 or us[0] != 'money' or us[2] != 'money' or us[1] != _asked(p):
        return None
    if ds[0] != [us[1]] or ds[2] != [us[1]] or ds[1]:
        return None
    if not (re.search(r'\b(?:price|cost)\b.*\b(?:drops?|lower|discount)', p.body)
            and re.search(r'\b(?:now|discounted|savings)\b', p.question)):
        return None
    return _result(p, whole_count(ns[0].value*ns[1].value/ns[2].value, p.question),
                   '{} * {} / {}'.format(*(_f(n) for n in ns)))


def _same_distance_speeds(p, ns, us, ds):
    if len(ns) != 3 or us[0] not in _TIME or us[1] not in _TIME or us[2] != 'mph' or _asked(p) != 'speed':
        return None
    t = p.text.lower()
    # The second runner's time inherits the same named route from the
    # coordinated predicate, rather than describing a different journey.
    if not (re.search(r'\band it takes\b', t[ns[0].end:ns[1].start])
            and re.search(r'\b(?:trail|track|route|circuit)\b', t[:ns[1].start])):
        return None
    second = previous._convert(ns[1].value, us[1], us[0])
    if second is not None:
        return _result(p, ns[2].value*ns[0].value/second,
                       '{} * {} / {}'.format(_f(ns[2]), _f(ns[0]), _f(second)))
    return None


def _rectangular_pieces(p, ns, us, ds):
    if len(ns) != 4 or len(set(us)) != 1 or us[0] not in {'inch', 'foot', 'meter', 'centimeter'}:
        return None
    t = p.text.lower()
    if not (re.fullmatch(r'\s+[a-z]+ by\s+', t[ns[0].end:ns[1].start])
            and re.fullmatch(r'\s+[a-z]+ by\s+', t[ns[2].end:ns[3].start])
            and ds[2] == [_asked(p)] and not ds[0] and not ds[1] and not ds[3]):
        return None
    # Each dimension must tile independently. Area alone does not prove
    # that rectangular pieces fit into the original rectangle.
    fits = []
    for a, b in ((2, 3), (3, 2)):
        x, y = ns[0].value/ns[a].value, ns[1].value/ns[b].value
        if x.denominator == y.denominator == 1:
            fits.append(x*y)
    if not fits:
        return None
    return _result(p, max(fits), '{} * {} / ({} * {})'.format(*(_f(n) for n in ns)))


def _target_plus_payment(p, ns, us, ds):
    if len(ns) != 3 or any(ds) or us[0] != us[2] or us[0] != _asked(p) or us[1] not in _TIME:
        return None
    t = p.text.lower()
    if not (re.search(r'\bgoal of selling\b', t[:ns[0].start])
            and re.search(r'\bas payment\b', core._sentence(t, ns[2]))
            and re.search(r'\b(?:per|each) '+re.escape(us[1])+r'\b', p.question)):
        return None
    return _result(p, (ns[0].value+ns[2].value)/ns[1].value,
                   '({} + {}) / {}'.format(_f(ns[0]), _f(ns[2]), _f(ns[1])))


def _per_group_space(p, ns, us, ds):
    if len(ns) != 4 or any(ds) or us[0] != _asked(p) or us[1] != us[2] or ns[2].value != 1:
        return None
    t = p.text.lower()
    if not (re.search(r'\beach of the same size\b', p.body)
            and re.search(r'\balready\s*$', t[:ns[3].start])
            and re.search(r'\bmore\b', p.question)):
        return None
    return _result(p, ns[0].value/ns[1].value-ns[3].value,
                   '{} / {} - {}'.format(_f(ns[0]), _f(ns[1]), _f(ns[3])))


def _remaining_resource_groups(p, ns, us, ds):
    if len(ns) != 4 or ds[0] or ds[1] != [us[0]] or ds[2] != [_asked(p)] or ds[3]:
        return None
    if us[1] != us[2] or us[1] != us[3] or not re.search(r'\bin total\b', p.body):
        return None
    return _result(p, (ns[3].value-ns[0].value*ns[1].value)/ns[2].value,
                   '({} - {} * {}) / {}'.format(_f(ns[3]), _f(ns[0]), _f(ns[1]), _f(ns[2])))


def _two_contents_daily(p, ns, us, ds):
    if (len(ns) != 5 or any(ds) or ns[0].value != 2 or ns[1].value != 1
            or us[0] != us[1] or us[2] != us[3] or us[2] != _asked(p) or us[4] not in _TIME):
        return None
    t = p.text.lower()
    if not (re.search(r'\bother\b', t[ns[2].end:ns[3].start])
            and re.search(r'\b(?:every|each) day\b', p.question)
            and re.search(r'\bequal number\b', p.question)):
        return None
    days = previous._convert(ns[4].value, us[4], 'day')
    if days is not None:
        return _result(p, (ns[2].value+ns[3].value)/days,
                       '({} + {}) / {}'.format(_f(ns[2]), _f(ns[3]), _f(days)))
    return None


def _amount(value, unit, denoms, expression, used):
    # Standard avoirdupois conversion, kept local to this skill.
    if unit == 'pound':
        value *= 16
        unit = 'ounce'
    denoms = list(denoms)
    for i, den in enumerate(denoms):
        if den == 'pound':
            value /= 16
            denoms[i] = 'ounce'
    return core._amount(value, unit, denoms, expression, used)


def _target(p, asked, units):
    if asked in ('speed', 'distance'):
        return core._target(p, asked, units)
    if not asked:
        return None
    query = re.split(r'\b(?:if|when)\b', p.question)[0]
    denoms = []
    marker = re.search(r'(?<!take for )\b(?:per|each|every) ([a-z]+)\b', query)
    if marker:
        unit = _normal(marker.group(1))
        if unit not in _STOP and unit not in {'one', 'time'}:
            denoms = [unit]
    else:
        marker = re.search(r'\ban? (second|minute|hour|day|week|month|year)\b', query)
        if marker:
            denoms = [marker.group(1)]
    return _amount(Fraction(1), asked, denoms, '', [])


def _observed_speed(p, ns, us, ds):
    if len(ns) != 2 or _asked(p) != 'speed' or any(ds):
        return None
    distances = {'mile', 'kilometer', 'meter', 'foot', 'yard'}
    if us[0] not in distances or us[1] not in _TIME:
        return None
    middle = p.text[ns[0].end:ns[1].start].lower()
    if (not re.fullmatch(r'\s+[a-z]+(?: [a-z]+){0,5} (?:in|over|during)\s+', middle)
            or re.search(r'\b(?:and|but|then|not|to)\b', middle)):
        return None
    target = _target(p, 'speed', us)
    distance = _amount(ns[0].value, us[0], [], '', [0])
    duration = _amount(ns[1].value, us[1], [], '', [1])
    rate = core._combine(distance, duration, True)
    if target and target.dims == rate.dims:
        return _result(p, rate.value/target.value,
                       '{} / {} (in requested units)'.format(_f(ns[0]), _f(ns[1])))
    return None


def _chain(p, ns, us, ds):
    """Unique unit cancellation using only explicitly read per-unit links."""
    if not 2 <= len(ns) <= 4 or not all(us) or not any(ds):
        return None
    t = p.text.lower()
    if re.search(r'\b(?:left|remaining|rests?|rested|waits?|waited|breaks?|'
                 r'more|less|than|twice|half|double|average|difference|lost|profit|except|only|both|another|'
                 r'every other|leap year|weekdays?|weekends?)\b', t):
        return None
    if re.search(r'\b(?:stops?|stopped) (?:for|after|before|working|to rest)\b', t):
        return None
    asked = _asked(p)
    if not asked and re.match(r'how many (?:does|did|will|should)\b', p.question):
        candidates = {d for dens in ds for d in dens if d not in _TIME | {'person', 'money'} and d not in us}
        if len(candidates) == 1:
            asked = next(iter(candidates))
    # A request for number of occurrences refers to the explicit container
    # in a filling/emptying narrative, rather than physical time.
    if asked == 'time' and re.search(r'\bfill\b', p.question):
        containers = [d for u, dens in zip(us, ds) for d in dens if d not in _TIME and d != u]
        if len(set(containers)) == 1:
            asked = containers[0]
    target = _target(p, asked, us)
    if target is None or not target.dims:
        return None
    atoms = [_amount(n.value, u, den, _f(n), [i]) for i, (n, u, den) in enumerate(zip(ns, us, ds))]
    # Independent plain stocks cannot be multiplied just because their
    # dimensions cancel. A measured rate must connect each additional stock.
    if not any(power < 0 for unit, power in target.dims) and sum(not den for den in ds) > 1:
        return None
    answers = {}
    for value, signs in dimensional_products([(a.value, a.dims) for a in atoms], target.dims):
        # Work-hours per week describes the fraction of elapsed time
        # available for work. Its reciprocal is not another possible rate.
        if any(sign < 0 and u in _TIME and den and all(d in _TIME for d in den)
               for sign, den, u in zip(signs, ds, us)):
            continue
        if any(sign < 0 and not den and not any(
                power < 0 for unit, power in target.dims)
               for sign, den, u in zip(signs, ds, us)):
            continue
        answers[value/target.value] = signs
    if len(answers) != 1:
        return None
    value, signs = next(iter(answers.items()))
    value = whole_count(value, p.question)
    return _result(p, value, ' * '.join(_f(n) if s > 0 else '(1 / {})'.format(_f(n))
                                      for n, s in zip(ns, signs))+' (in compatible units)')


def solve(problem):
    ns = _numbers(problem)
    if not 2 <= len(ns) <= 8 or any(n.value <= 0 or n.kind == 'percent' for n in ns):
        return None
    if len(set(re.findall(r'[$£€]', problem.text))) > 1:
        return None
    us = [_unit(problem, n) for n in ns]
    ds = _denoms(problem, ns, us)
    for rule in (_residual, _equal_sharing, _combined_prices, _interval,
                 _periodic_duration, _net_flow, _capacity_exchange,
                 _rotating_groups, _area_density, _recurring_net_cost,
                 _combined_flow, _batch_repetitions, _mixture_fraction,
                 _unread_stock, _daily_item_total, _time_comparison,
                 _scheduled_sum, _annual_growth, _shared_carry,
                 _weekly_unit_batches, _ratio_chain, _money_goal,
                 _daily_expenses, _batch_unit_price, _compare_observed_rates,
                 _duty_cycle, _weekly_schedule, _interval_with_definition,
                 _pooled_shares, _several_removals, _group_shortfall,
                 _fixed_budget_exchange, _same_distance_speeds,
                 _rectangular_pieces, _target_plus_payment, _per_group_space,
                 _remaining_resource_groups, _two_contents_daily,
                 _observed_speed, _chain):
        result = rule(problem, ns, us, ds)
        if result is not None:
            return result
    return None
