"""Conservative rate schemas, with units and explicit equal-sharing relations.

All arithmetic is exact.  Unknown or unused quantities make a schema abstain;
in particular, merely finding two numbers is not a division instruction.
"""
import re
from fractions import Fraction

from ..numbers import format_number


def _has(pattern, text):
    return re.search(pattern, text) is not None


def _singular(word):
    irregular = {'people': 'person', 'children': 'child', 'feet': 'foot',
                 'inches': 'inch', 'puppies': 'puppy', 'pies': 'pie',
                 'cookies': 'cookie', 'brownies': 'brownie',
                 'bus': 'bus', 'buses': 'bus'}
    if word in irregular:
        return irregular[word]
    if word.endswith('ies'):
        return word[:-3] + 'y'
    if word.endswith(('ches', 'shes', 'sses', 'xes')):
        return word[:-2]
    return word[:-1] if word.endswith('s') and not word.endswith('ss') else word


_STOPS = set(('of per each every a an the in on at for to from with and or but '
              'is are was were will would can could has have had that which who '
              'when while before after over into out by as than thick long '
              'there left remaining cost costs worth contains contain holds hold '
              'produces produce makes make needs need buys buy pays pay gets get '
              'takes take covers cover together total already containing once '
              'ordered bought sold earned spent walked worked traveled').split())


def _noun(text):
    """The head of a short noun phrase, preserving physical units."""
    words = re.match(r'\s*[- ]?([a-z]+(?:[ -]+[a-z]+){0,4})', text)
    if not words:
        return ''
    result = []
    for word in re.split(r'[ -]+', words.group(1)):
        if word in _STOPS:
            break
        result.append(word)
        if word in ('second', 'minute', 'hour', 'day', 'week', 'month', 'year',
                    'seconds', 'minutes', 'hours', 'days', 'weeks', 'months', 'years',
                    'ounce', 'ounces'):
            break
    return _singular(result[-1]) if result else ''


def _unit(text, number):
    if number.kind == 'money':
        return 'dollar'
    return _noun(text[number.end:])


def _sentence(text, number):
    left = list(re.finditer(r'[.!?;](?:\s|$)', text[:number.start]))
    right = re.search(r'[.!?;](?:\s|$)', text[number.end:])
    return text[left[-1].end() if left else 0:
                number.end + right.start() if right else len(text)]


def _quantities(p):
    """Exclude grammatical 'one', and exact references repeated in the query."""
    text = p.text.lower()
    result = []
    for n in p.numbers:
        before, after = text[:n.start], text[n.end:]
        if n.value == 1 and (
                _has(r'(?:each|every)\s*$', before) and not _noun(after)
                or _has(r'^(?:\s+on average|\s+cost\b)', after)
                or _has(r'^\s+side\b', after) and _has(r'\bother side\b', text)
                or _has(r'\bonly\s*$', before) and _has(r'^\s+[a-z]+\s+with a (?:flow )?rate\b', after)
                or _has(r'\b(?:each|every)\s*$', before) and _has(r'^\s*[.!?]', after)
                or n.start >= len(p.body) and _has(r'how much (?:did|does|will)\s*$', p.question[:n.start-len(p.body)])):
            continue
        if n.start >= len(p.body) and any(
                k.start < len(p.body) and k.value == n.value
                and _unit(text, k) == _unit(text, n) for k in result):
            continue
        if _has(r'\b(?:at the end of|by the end of)\s+(?:the\s+)?$', before) and any(
                k.value == n.value and _unit(text, k) == _unit(text, n) for k in result):
            continue
        result.append(n)
    return result


def _answer(value, expression):
    if value < 0:
        return None
    return value, expression + ' = ' + format_number(value) + '.'


def _calc(a, op, b):
    if op == '/' and b == 0:
        return None
    result = {'+': lambda: a+b, '-': lambda: a-b,
              '*': lambda: a*b, '/': lambda: a/b}[op]()
    return _answer(result, '{} {} {}'.format(format_number(a), op, format_number(b)))


def _money_answer(value, expression, context, unit='dollars'):
    """Include both a currency and the subject of the requested amount.

    Besides being clearer to the reader, units let the arbiter recognize an
    amount answer alongside the ordinary chat modules' price suggestions.
    """
    if value < 0:
        return None
    return value, '{}: {} = {} {}.'.format(context, expression, format_number(value), unit)


def _currency(ns):
    for n in ns:
        if n.kind == 'money':
            return {'$': 'dollars', '£': 'pounds', '€': 'euros'}.get(n.raw[0], 'dollars')
    return 'dollars'


# Seconds per unit, or months per calendar unit.  The two families must not mix.
_TIME = {'second': (0, 1), 'minute': (0, 60), 'hour': (0, 3600),
         'day': (0, 86400), 'week': (0, 604800),
         'month': (1, 1), 'year': (1, 12)}


def _convert(value, source, dest):
    if source == dest:
        return value
    if source in _TIME and dest in _TIME and _TIME[source][0] == _TIME[dest][0]:
        return value * Fraction(_TIME[source][1], _TIME[dest][1])
    return None


def _rates(p, ns):
    """(quantity index, denominator unit).  Only unit denominators here."""
    text = p.text.lower()
    found = []
    for i, n in enumerate(ns):
        # Bound the suffix at the next quantity and at sentence punctuation.
        end = ns[i+1].start if i+1 < len(ns) else len(p.body)
        suffix = text[n.end:end]
        suffix = re.split(r'[.!?;](?:\s|$)', suffix)[0]
        m = re.search(r'\b(?:per|every|each|an?)\s+(second|minute|hour|day|week|month|year)\b', suffix)
        # A later clause's rate belongs to that clause, not to this number.
        if m and any(w in _STOPS-{'in', 'from', 'for'} for w in re.findall(r'[a-z]+', suffix[:m.start()])):
            m = None
        if m:
            found.append((i, m.group(1)))
            continue
        m = re.search(r'\b(?:per|each)\s+([a-z]+)\b', suffix)
        if m and m.group(1) not in _STOPS and m.group(1) not in ('once', 'of', 'one') and not any(
                w in _STOPS-{'in', 'from', 'for'} for w in re.findall(r'[a-z]+', suffix[:m.start()])):
            found.append((i, _singular(m.group(1))))
            continue
        sentence = _sentence(text, n)
        m = re.search(r'\b(?:every|each)\s+(second|minute|hour|day|week|month|year)\b', sentence)
        if m and len([k for k in ns if _sentence(text, k) == sentence]) == 1:
            found.append((i, m.group(1)))
            continue
        # "Each container holds N objects", not "N containers each".
        prefix = text[max(0, n.start-65):n.start]
        m = re.search(r'\beach\s+([a-z]+)\s+(?:(?:has|holds|contains|had|costs?|takes|needs)\s*|(?:(?:can\s+)?[a-z]+\s+)?in\s*)$', prefix)
        if m:
            found.append((i, _singular(m.group(1))))
            continue
        if i and _has(r'\beach (?:containing|holding|with)\s*$', prefix):
            found.append((i, _unit(text, ns[i-1])))
    return found


def _asked(p):
    m = re.match(r'(?:how (?:many|much)|calculate the number of)\s+(?:(?:more|new|additional)\s+)?([a-z]+)', p.question)
    if m:
        word = _singular(m.group(1))
        if word not in ('did', 'does', 'do', 'will', 'would', 'can', 'is', 'was', 'money', 'more'):
            return word
    if _has(r'how much.*\b(?:earn|pay|cost|save|spend|money)\b', p.question):
        return 'dollar'
    return ''


def _single_rate(p, ns):
    """Known rate and amount/time, optionally a starting or target balance."""
    text = p.text.lower()
    rates = _rates(p, ns)
    if len(rates) != 1 or len(ns) not in (2, 3):
        return None
    ri, denominator = rates[0]
    rate = ns[ri].value
    numerator = _unit(text, ns[ri])
    if not numerator or rate <= 0 or _has(
            r'\b(?:twice|half|percent|times as|discount|doubles?|doubled|triples?|tripled|'
            r'round[ -]trip|there and back)\b', text):
        return None
    asked = _asked(p)
    others = [n for i, n in enumerate(ns) if i != ri]
    if len(others) == 1:
        n = others[0]
        unit = _unit(text, n)
        # Time worked at an hourly wage, or N units consumed at a unit price.
        duration = _convert(n.value, unit, denominator)
        if _has(r'\b(?:weekdays|workdays|weekends|off)\b', p.body):
            if denominator == 'day' and unit == 'week' and _has(r'\bweekdays only\b', p.body):
                duration = n.value*5
            else:
                return None
        if duration is not None and asked == numerator and not _has(
                r'\b(?:left|remaining|more|less|profit|change|difference|each|per|equally|evenly)\b', p.question) and not _has(
                r'\b(?:split|shared|divided)\b', p.body):
            return _calc(rate, '*', duration)
        if unit == numerator and asked == denominator:
            if _has(r'\b(?:more|left|remaining)\b', p.question):
                return None
            quotient = n.value/rate
            if numerator == 'dollar' and denominator not in _TIME and _has(
                    r'\b(?:afford|can .*buy)\b', p.question):
                return _answer(Fraction(quotient.numerator // quotient.denominator),
                               'Whole items affordable from {} / {}'.format(format_number(n.value), format_number(rate)))
            if denominator in ('trip', 'batch', 'box', 'bus', 'container') and _has(
                    r'\b(?:need|required|necessary)\b', p.question):
                return _answer(Fraction(-(-quotient.numerator // quotient.denominator)),
                               'Round up ({} / {})'.format(format_number(n.value), format_number(rate)))
            return _calc(n.value, '/', rate)
        # "It takes N minutes per room; whole job takes T hours."
        duration = _convert(n.value, unit, numerator)
        if duration is not None and asked == denominator:
            return _calc(duration, '/', rate)
        return None
    if asked != denominator:
        return None
    a, b = others
    au, bu = _unit(text, a), _unit(text, b)
    if au == bu == numerator:
        if _has(r'\b(?:extra|aside from|in addition)\b',p.body):
            return None  # An additional rate is not an existing stock.
        # Explicit net change: a goal and existing balance, heating/cooling,
        # a final stock, or before/after inventory with a per-box quantity.
        if not _has(r'\b(?:needs?|goal|save|savings|reduce|reach|ready|now|remaining|left)\b', text):
            return None
        # Two amounts of the same dimension alone do not specify a difference.
        if not (_has(r'\b(?:has|had|is|was|savings|now|reduce|start|initial|places)\b', text)
                and _has(r'\b(?:needs?|goal|reach|reduce|ready|now|more)\b', text)):
            return None
        if (_has(r'\bis\s*$', text[:a.start]) and _has(r'\bis\s*$', text[:b.start])
                and _has(r'^\s+square\b', text[a.end:]) and _has(r'^\s+square\b', text[b.end:])
                and not _has(r'\b(?:already|left|remaining|goal|reach|reduce)\b', text)):
            return None
        delta = abs(a.value-b.value)
        return _answer(delta/rate, '({} - {}) / {}'.format(
            format_number(max(a.value, b.value)), format_number(min(a.value, b.value)),
            format_number(rate)))
    # Work already completed for T hours, and a total distance goal.
    timed = [(n, _convert(n.value, _unit(text, n), denominator)) for n in others]
    durations = [(n, v) for n, v in timed if v is not None]
    totals = [n for n in others if _unit(text, n) == numerator]
    if len(durations) == len(totals) == 1 and _has(r'\bmore\b', p.question) and _has(r'\btotal\b', text):
        value = totals[0].value/rate-durations[0][1]
        return _answer(value, '{} / {} - {}'.format(format_number(totals[0].value),
                       format_number(rate), format_number(durations[0][1])))
    return None


def _unit_rate(p, ns):
    """A measured total divided by its explicit duration or group count."""
    if len(ns) != 2 or _rates(p, ns):
        return None
    text = p.text.lower()
    asked = _asked(p)
    denom = re.search(r'\b(?:per|each|every|an?)\s+([a-z]+)\b', p.question)
    if not denom or denom.group(1) in _STOPS:
        return None
    group = _singular(denom.group(1))
    for total, count in (ns, ns[::-1]):
        if _unit(text, total) != asked or _unit(text, count) != group:
            continue
        # A comparison or a residual stock requires more than a simple quotient.
        if _has(r'\b(?:more|fewer|less|left|remaining|than|twice|half|difference|change)\b', text):
            return None
        if not _has(r'\b(?:in|for|over|during|among|between|into|each|every)\b', p.body):
            return None
        return _calc(total.value, '/', count.value)
    return None


def _reported_rate(p, ns):
    """'The number of objects removed per period is N', with a target stock.

    Here the number follows its units, and the target can inherit the stock's
    unit.  Require the removal relation and a query about reducing that stock.
    """
    if len(ns) != 3 or not _has(r'\breduce\b', p.question):
        return None
    text = p.text.lower()
    stock, rate, target = ns
    if not _has(r'\b(?:gives? away|sells?|loses?|removes?)\b', p.body):
        return None
    pattern = (r'\b(?:number|amount) of ([a-z]+)\s+[^.!?;]*?'
               r'\bper (day|week|month|year|hour) is\s*$')
    relation = re.search(pattern, text[:rate.start])
    if not relation or _singular(relation.group(1)) != _unit(text, stock):
        return None
    if _asked(p) != relation.group(2):
        return None
    if not _has(r'\bto\s*$', text[:target.start]) or target.start < len(p.body):
        return None
    if target.value > stock.value:
        return None
    return _answer((stock.value-target.value)/rate.value, '({} - {}) / {}'.format(
        *(format_number(n.value) for n in (stock, target, rate))))


def _chained_rates(p, ns):
    """N groups x amount/group / amount/period, with explicit unit joins."""
    if len(ns) != 3:
        return None
    text = p.text.lower()
    rates = _rates(p, ns)
    asked = _asked(p)
    if len(rates) != 2:
        # Postposed each: "N containers of V gallons each".
        for i, n in enumerate(ns):
            suffix = text[n.end:ns[i+1].start if i+1 < len(ns) else len(p.body)]
            if _has(r'\beach\b', suffix) and i > 0 and _has(r'\bof\s*$', text[ns[i-1].end:n.start]):
                rates.append((i, _unit(text, ns[i-1])))
    if len(rates) != 2:
        return None
    for (i, group), (j, period) in (rates, rates[::-1]):
        other = [k for k in range(3) if k not in (i, j)]
        if len(other) != 1 or asked != period:
            continue
        k = other[0]
        if (_unit(text, ns[k]) == group and _unit(text, ns[i]) == _unit(text, ns[j])
                and ns[j].value > 0):
            return _answer(ns[k].value*ns[i].value/ns[j].value,
                           '{} * {} / {}'.format(*(format_number(ns[x].value) for x in (k, i, j))))
    return None


def _price_schemas(p, ns):
    text = p.text.lower()
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    item = re.search(r'\b(?:each|one)\s+([a-z]+)', p.question)
    asked_item = _singular(item.group(1)) if item else ''
    if not money:
        return None
    # Tender minus change, divided among identical purchases.
    if len(money) == 2 and len(counts) == 1 and _has(r'\bchange\b', p.body):
        if not _has(r'how much.*\b(?:each|one)\b.*\bcost\b', p.question):
            return None
        if asked_item != _unit(text, counts[0]):
            return None
        paid = [n for n in money if _has(r'\b(?:pays?|paid|with)\s+(?:a\s+)?$|\b(?:pays?|paid)\s*$', text[max(0, n.start-25):n.start])]
        change = [n for n in money if _has(r'^\s+change\b', text[n.end:])]
        if len(paid) == len(change) == 1 and paid[0] != change[0] and counts[0].value > 0:
            return _money_answer((paid[0].value-change[0].value)/counts[0].value,
                                 '({} - {}) / {}'.format(*(format_number(n.value) for n in (paid[0], change[0], counts[0]))),
                                 'Cost per '+asked_item, _currency(ns))
    # Total spending less a separately priced item, balance split equally.
    if len(money) == 2 and len(counts) == 1 and _has(r'\b(?:same amount|equal|equally)\b', text):
        if not _has(r'how much.*\bcost\b', p.question):
            return None
        if asked_item != _unit(text, counts[0]):
            return None
        totals = [n for n in money if _has(r'\b(?:spent|total|paid)\s*$', text[max(0, n.start-30):n.start])]
        if len(totals) == 1 and counts[0].value > 0:
            total = totals[0]
            other = next(n for n in money if n != total)
            return _money_answer((total.value-other.value)/counts[0].value,
                                 '({} - {}) / {}'.format(*(format_number(n.value) for n in (total, other, counts[0]))),
                                 'Cost per '+asked_item, _currency(ns))
    # Budget for an old unit price, now buying at a changed unit price.
    if len(money) == 2 and len(counts) == 1 and _has(r'\bprice\b.*\b(?:increased|decreased|changed)\b', text):
        if not _has(r'how many.*\b(?:buy|afford)\b', p.question):
            return None
        if _asked(p) != _unit(text, counts[0]):
            return None
        old, new = money
        if _has(r'\beach\b.*\bcost\b', text[:old.start]) and new.value > 0:
            value = old.value*counts[0].value/new.value
            return _answer(Fraction(value.numerator // value.denominator),
                           'Whole items affordable from {} * {} / {}'.format(*(format_number(n.value) for n in (old, counts[0], new))))
    # Revenue/unit price + unsold inventory = starting inventory.
    if len(money) == 2 and len(counts) == 1 and _has(r'how many.*\bstart\b', p.question):
        if _asked(p) != _unit(text, counts[0]):
            return None
        prices = [n for n in money if _has(r'^\s+each\b', text[n.end:])]
        if len(prices) == 1 and _has(r'\b(?:selling|sold|sells)\b', p.body) and _has(r'\b(?:left|home with|remaining|unsold)\b', p.body):
            price = prices[0]
            revenue = next(n for n in money if n != price)
            if price.value > 0:
                return _answer(revenue.value/price.value+counts[0].value,
                               '{} / {} + {}'.format(*(format_number(n.value) for n in (revenue, price, counts[0]))))
    return None


def _parallel_rates(p, ns):
    """Combined carrying capacity or an opposing current."""
    if len(ns) != 3:
        return None
    text = p.text.lower()
    asked = _asked(p)
    rates = _rates(p, ns)
    if len(rates) == 2 and rates[0][1] == rates[1][1] == asked:
        (i, _), (j, _) = rates
        k = next(k for k in range(3) if k not in (i, j))
        if len({_unit(text, n) for n in ns}) != 1:
            return None
        if _has(r'\b(?:against the current|opposite direction|upstream)\b', text):
            divisor = ns[i].value-ns[j].value
            if divisor > 0:
                return _answer(ns[k].value/divisor, '{} / ({} - {})'.format(
                    *(format_number(ns[x].value) for x in (k, i, j))))
    if asked == 'trip' and _has(r'\btogether\b', p.question):
        capacities = [i for i, n in enumerate(ns) if _has(r'^\s+[a-z]+\s+at a time\b', text[n.end:])]
        if len(capacities) == 2 and len({_unit(text, n) for n in ns}) == 1:
            i, j = capacities
            k = next(k for k in range(3) if k not in (i, j))
            divisor = ns[i].value+ns[j].value
            if divisor > 0:
                v = ns[k].value/divisor
                return _answer(Fraction(-(-v.numerator // v.denominator)),
                               'Round up ({} / ({} + {}))'.format(*(format_number(ns[x].value) for x in (k, i, j))))
    return None


def _proportion(p, ns):
    """A for every B, and an explicitly repeated noun phrase."""
    if len(ns) != 3:
        return None
    text = p.text.lower()
    a, b, total = ns
    middle = text[a.end:b.start]
    m = re.fullmatch(r'\s+([a-z]+(?:\s+[a-z]+){0,2})\s+for every\s+', middle)
    if not m:
        return None
    first = m.group(1).strip()
    m = re.match(r'\s+([a-z]+(?:\s+[a-z]+){0,2}?)(?=\s+(?:that|and|if|in)\b|[.,;?])', text[b.end:])
    if not m:
        return None
    second = m.group(1).strip()
    if text[total.end:].lstrip().startswith(first) and p.question.startswith('how many '+second) and a.value > 0:
        return _answer(total.value*b.value/a.value, '{} * {} / {}'.format(
            *(format_number(n.value) for n in (total, b, a))))
    if text[total.end:].lstrip().startswith(second) and p.question.startswith('how many '+first) and b.value > 0:
        return _answer(total.value*a.value/b.value, '{} * {} / {}'.format(
            *(format_number(n.value) for n in (total, a, b))))
    return None


def _sharing(p, ns):
    """An explicit equal split, including product divided by recipient count."""
    text = p.text.lower()
    if not _has(r'\b(?:each|per|equally|evenly)\b', p.question):
        return None
    if not _has(r'\b(?:equal|equally|evenly|same amount|same number)\b', text):
        return None
    if len(ns) == 2:
        total, people = ns
        if _has(r'\b(?:shared|share|split|divided|divide|distributed|distribute)\b', text) and people.value > 0:
            if _unit(text, total) == _asked(p) and _unit(text, people) != _asked(p):
                amount, recipients = total.value, people.value
                if _has(r'^\s+dozen\b', text[total.end:]):
                    amount *= 12
                # 'With her N siblings/friends' includes the owner in the split.
                if (_has(r'\b(?:with|and)\s+(?:his|her|their)\s*$', text[:people.start])
                        and _unit(text, people) in ('sibling', 'friend', 'brother', 'sister', 'child')
                        and _has(r'\beach person\b', p.question)):
                    recipients += 1
                return _calc(amount, '/', recipients)
        # A coordinated pair of buyers, with explicitly even sharing.
        # Do not infer group size from an arbitrary list elsewhere in the story.
        if _has(r'\bsplit (?:the )?costs? evenly\b', p.body) and _asked(p) == 'dollar':
            subject = re.search(
                r'^\s*[a-z]+ and (?:his|her|their) '
                r'(?:(?:best|close|good|old|new)\s+)?([a-z]+)'
                r'(?:\s+[a-z]+)?\s+(?:bought|buy)\b', p.body)
            singular_partner = subject and subject.group(1) in (
                'friend', 'sister', 'brother', 'partner', 'wife', 'husband',
                'mother', 'father', 'colleague', 'classmate', 'neighbor')
            named_pair = re.match(r'^\s*[A-Z][a-z]+ and [A-Z][a-z]+\s+(?:bought|buy)\b', p.text)
            rates = _rates(p, ns)
            if (singular_partner or named_pair) and len(rates) == 1:
                ri, group = rates[0]
                ci = 1-ri
                if _unit(text, ns[ri]) == 'dollar' and _unit(text, ns[ci]) == group:
                    return _answer(ns[ri].value*ns[ci].value/2,
                                   '{} * {} / 2'.format(format_number(ns[ri].value), format_number(ns[ci].value)))
        return None
    if len(ns) != 3:
        return None
    rates = _rates(p, ns)
    # N friends plus the host, sharing G packs with U units each.
    friends = [i for i, n in enumerate(ns) if _has(
        r'^\s+(?:friends|guests|classmates|coworkers|colleagues|neighbors|relatives)\b', text[n.end:])]
    if len(friends) == 1 and len(rates) == 1:
        fi = friends[0]
        ri, group = rates[0]
        if fi == ri:
            return None
        counts = [i for i, n in enumerate(ns) if i not in (fi, ri) and _unit(text, n) == group]
        if len(counts) == 1 and _unit(text, ns[ri]) == _asked(p):
            if not _has(r'\b(?:invited|with (?:his|her|their))\b', p.body):
                return None
            ci = counts[0]
            return _answer(ns[ci].value*ns[ri].value/(ns[fi].value+1),
                           '{} * {} / ({} + 1)'.format(*(format_number(ns[i].value) for i in (ci, ri, fi))))
    return None


def _period_payments(p, ns):
    """A balance or savings goal paid in equal instalments over a duration."""
    if len(ns) != 3 or not _has(r'how much.*\b(?:each|per|every) (?:month|week|year|day)\b', p.question):
        return None
    text = p.text.lower()
    money = [n for n in ns if n.kind == 'money']
    times = [n for n in ns if _unit(text, n) in _TIME]
    if len(money) != 2 or len(times) != 1:
        return None
    if not _has(r'\b(?:goal|save|saving|balance|deposit|rest|remaining)\b', p.body):
        return None
    if not _has(r'\b(?:left over|already|deposit|savings|has|have)\b', p.body):
        return None
    period = re.search(r'\b(?:each|per|every) (month|week|year|day)\b', p.question).group(1)
    duration = _convert(times[0].value, _unit(text, times[0]), period)
    if duration is not None and duration > 0:
        a, b = money
        if a.value < b.value:
            return None
        subject = re.search(r'how much (?:money )?(?:does|did|will|can) ([a-z]+)', p.question)
        action = 'savings' if _has(r'\bsave\b', p.body) else 'payment'
        context = action + (' for '+subject.group(1) if subject else '')+' each '+period
        unit = 'thousand dollars' if _has(r'\bthousands of dollars\b', p.question) else _currency(ns)
        return _money_answer((a.value-b.value)/duration, '({} - {}) / {}'.format(
            format_number(a.value), format_number(b.value), format_number(duration)), context, unit)
    return None


def _grouped_conversion(p, ns):
    """Explicit equivalence, or every N source objects yielding one target."""
    text = p.text.lower()
    if len(ns) == 4:
        for i in range(3):
            a, b = ns[i:i+2]
            if not re.fullmatch(r'\s+[a-z]+\s+(?:is|equals|contains)\s+', text[a.end:b.start]):
                continue
            if a.value <= 0 or b.value <= 0:
                continue
            au, bu = _unit(text, a), _unit(text, b)
            if _asked(p) != au:
                continue
            others = [n for n in ns if n not in (a, b)]
            sizes = [n for n in others if _unit(text, n) == bu]
            groups = [n for n in others if n not in sizes]
            if len(sizes) == len(groups) == 1 and _has(r'\b(?:each|average)\b', p.question):
                return _answer(sizes[0].value*a.value/b.value/groups[0].value,
                               '{} * {} / {} / {}'.format(*(format_number(n.value) for n in (sizes[0], a, b, groups[0]))))
    if len(ns) != 3:
        return None
    for i, n in enumerate(ns):
        prefix = text[max(0, n.start-15):n.start]
        suffix = text[n.end:]
        relation = re.match(r'\s+([a-z ]+?)\s+(?:will )?(?:produce|yield|make)s?\s+(?:a|an)\s+([a-z]+)\b', suffix)
        if not relation or not _has(r'\bevery\s*$', prefix) or _singular(relation.group(2)) != _asked(p):
            continue
        rates = [(j, u) for j, u in _rates(p, ns) if j != i]
        if len(rates) != 1:
            continue
        ri, group = rates[0]
        ci = next(k for k in range(3) if k not in (i, ri))
        if _unit(text, ns[ci]) == group and _unit(text, ns[ri]) == _unit(text, n):
            return _answer(ns[ci].value*ns[ri].value/n.value,
                           '{} * {} / {}'.format(*(format_number(ns[k].value) for k in (ci, ri, i))))
    return None


def _distribution_changes(p, ns):
    """An equal distribution followed by removal from every container."""
    if len(ns) != 3:
        return None
    text = p.text.lower()
    total, count, removed = ns
    container = _unit(text, count)
    if not _has(r'\b(?:placed|put|divided|distributed)\b', text[:total.start]):
        return None
    if not _has(r'\b(?:into|among|between)\b', text[total.end:count.start]):
        return None
    if not _has(r'\b(?:take|took|remove|removed)\s*$', text[max(0, removed.start-25):removed.start]):
        return None
    if not _has(r'\bout of each '+re.escape(container)+r'\b', text[removed.end:]):
        return None
    if _asked(p) == _unit(text, total) and _has(r'\bleft\b.*\beach '+re.escape(container)+r'\b', p.question):
        return _answer(total.value/count.value-removed.value, '{} / {} - {}'.format(
            *(format_number(n.value) for n in ns)))
    return None


def _denominations(p, ns):
    """Repeated equal withdrawals expressed as a count of banknotes."""
    if len(ns) != 3 or _asked(p) not in ('bill', 'note'):
        return None
    text = p.text.lower()
    if not _has(r'\b(?:withdraws?|withdrew|withdrawn)\b', p.body):
        return None
    money = [i for i, n in enumerate(ns) if n.kind == 'money']
    denoms = [i for i, n in enumerate(ns) if _has(r'^\s*[- ]?(?:dollar|pound|euro)\s+(?:bills|notes)\b', text[n.end:])]
    if len(money) != 1 or len(denoms) != 1 or money == denoms:
        return None
    ri, di = money[0], denoms[0]
    ci = next(k for k in range(3) if k not in (ri, di))
    if (ri, _unit(text, ns[ci])) not in _rates(p, ns):
        return None
    return _answer(ns[ri].value*ns[ci].value/ns[di].value,
                   '{} * {} / {}'.format(*(format_number(ns[k].value) for k in (ri, ci, di))))


def solve(problem):
    if re.search(r'how many [a-z]+ and [a-z]+.*(?:altogether|total)', problem.question):
        return None
    if (re.search(r'\b(?:daily (?:serving|amount|requirement|goal|quota|intake)|recommended daily)\b', problem.body)
            and re.search(r'\bweek\b', problem.question)):
        return None
    ns = _quantities(problem)
    if not 2 <= len(ns) <= 4 or any(n.kind == 'percent' or n.value <= 0 for n in ns):
        return None
    if len({n.raw[0] for n in ns if n.kind == 'money'}) > 1:
        return None
    # The shared reader leaves a monetary 'k' suffix in the source text.  Its
    # values are usable directly only when the requested unit is thousands.
    scaled = [n for n in ns if n.kind == 'money' and re.match(r'k\b', problem.text[n.end:], re.I)]
    if scaled and (not _has(r'\bthousands of dollars\b', problem.question)
                   or len(scaled) != len([n for n in ns if n.kind == 'money'])):
        return None
    for rule in (_proportion, _price_schemas, _parallel_rates, _sharing,
                 _period_payments, _grouped_conversion, _distribution_changes, _denominations,
                 _chained_rates, _single_rate, _unit_rate, _reported_rate):
        result = rule(problem, ns)
        if result is not None:
            return result
    return None
