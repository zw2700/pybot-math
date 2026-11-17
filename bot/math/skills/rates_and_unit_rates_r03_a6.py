"""Exact, unit-checked multi-stage rates.

Relations, rather than the order or count of numbers, determine the operations.
Every quantity must be consumed by a relation; ambiguous dimensions abstain.
"""
import itertools
import re
from dataclasses import dataclass
from fractions import Fraction

from ..numbers import Number, format_number
from .rates_and_unit_rates_r01_a4 import _singular


_STOPS = set(('of per each every a an the in on at for to from with and or but '
              'is are was were will would can could has have had that which who '
              'when while before after over into out by as than thick long wide '
              'there left remaining cost costs worth contains contain holds hold '
              'produces produce makes make needs need buys buy pays pay gets get '
              'takes take covers cover together total already containing once '
              'ordered bought sold earned spent walked worked traveled different '
              'if does do did all only agreed above below less more how capable').split())
_MEASURES = set(('second minute hour day week month year foot inch yard mile '
                 'gallon quart pint cup ounce pound liter milliliter gram kilogram meter page ml '
                 'centimeter kilometer calorie degree chapter').split())
# Base units use seconds, inches, fluid ounces, dollars, and grams respectively.
_UNITS = {
    'second': ('time', Fraction(1)), 'minute': ('time', Fraction(60)),
    'hour': ('time', Fraction(3600)), 'day': ('time', Fraction(86400)),
    'week': ('time', Fraction(604800)),
    'month': ('calendar', Fraction(1)), 'year': ('calendar', Fraction(12)),
    'inch': ('length', Fraction(1)), 'foot': ('length', Fraction(12)),
    'yard': ('length', Fraction(36)), 'mile': ('length', Fraction(63360)),
    'ounce': ('volume', Fraction(1)), 'cup': ('volume', Fraction(8)),
    'pint': ('volume', Fraction(16)), 'quart': ('volume', Fraction(32)),
    'gallon': ('volume', Fraction(128)),
    'cent': ('dollar', Fraction(1, 100)),
    'gram': ('mass', Fraction(1)), 'kilogram': ('mass', Fraction(1000)),
    'millimeter': ('metric_length', Fraction(1)),
    'centimeter': ('metric_length', Fraction(10)),
    'meter': ('metric_length', Fraction(1000)),
    'kilometer': ('metric_length', Fraction(1000000)),
    'liter': ('metric_volume', Fraction(1000)), 'milliliter': ('metric_volume', Fraction(1)),
    'ml': ('metric_volume', Fraction(1)),
}


def _has(pattern, text):
    return re.search(pattern, text) is not None


def _normal(word):
    word = _singular(word)
    return {'calory': 'calorie', 'member': 'person', 'scarve': 'scarf'}.get(word, word)


def _head(tail):
    words = re.match(r"\s*[- ]?([a-z]+(?:[ -]+[a-z]+){0,5})", tail)
    if not words:
        return ''
    kept = []
    for word in re.split(r'[ -]+', words.group(1)):
        if word in ('total', 'different') and not kept:
            continue
        if word in _STOPS:
            break
        word = _normal(word)
        if word in _MEASURES:
            return word
        kept.append(word)
    return kept[-1] if kept else ''


def _unit(text, n):
    return 'dollar' if n.kind == 'money' else _head(text[n.end:])


def _dim(unit):
    return _UNITS.get(unit, (unit, Fraction(1)))


def _convert(value, source, dest):
    a, af = _dim(source)
    b, bf = _dim(dest)
    return value*af/bf if a and a == b else None


def _numbers(p):
    """Repair leading-dot decimals locally and remove grammatical references."""
    text = p.text.lower()
    ns = []
    for n in p.numbers:
        if (n.start and text[n.start-1] == '.' and re.fullmatch(r'\d+', n.raw)
                and (n.start < 2 or not text[n.start-2].isalnum())):
            currency = n.start >= 2 and text[n.start-2] in '$£€'
            n = Number(Fraction('0.'+n.raw), n.start-(2 if currency else 1), n.end, (text[n.start-2] if currency else '')+'.'+n.raw, 'money' if currency else n.kind)
        before, after = text[:n.start], text[n.end:]
        if re.match(r'\s+dozen\b',after):
            n = Number(n.value*12,n.start,n.end,n.raw,n.kind)
        if n.kind == 'number' and re.search(r'[$£€]\s*$',before):
            n = Number(n.value,n.start,n.end,n.raw,'money')
        if n.kind == 'number' and re.match(r'\s*(?:dollars?\b|cents?\b|c\b)',after):
            cents = bool(re.match(r'\s*(?:cents?\b|c\b)',after))
            n = Number(n.value/(100 if cents else 1),n.start,n.end,n.raw,'money')
        if _has(r'\(including\s*$',before) and re.match(r'[^)]*\)',after):
            continue
        if n.value == 1 and (_has(r'\b(?:other|each)\s*$', before)
                             or _has(r'^\s+at a time\b', after)):
            continue
        if n.start >= len(p.body) and any(
                old.value == n.value and _unit(text, old) == _unit(text, n) for old in ns):
            continue
        ns.append(n)
    return ns


def _asked(p):
    q = p.question
    for n in p.numbers:
        if n.start >= len(p.body) and re.fullmatch(r'how many\s+',q[:n.start-len(p.body)]):
            capacity = re.match(r'-[a-z]+\s+([a-z]+)',p.text[n.end:].lower())
            if capacity:
                return _normal(capacity.group(1))
    m = re.match(r'how (?:many|much)\s+(?:(?:more|total|additional)\s+)?([a-z]+(?:[ -]+[a-z]+){0,3})', q)
    if m:
        result = _head(m.group(1))
        if result and result not in ('money', 'time', 'profit', 'rate', 'cost'):
            return result
    m = re.search(r'\bin (seconds?|minutes?|hours?|days?|weeks?|inches|feet|cents?|pounds?)\b', q)
    if m:
        return _normal(m.group(1))
    if _has(r'how much.*\b(?:cost|pay|earn|spend|profit|money|make|rate)\b', q):
        return 'dollar'
    return ''


def _answer(value, expression, context='Calculation'):
    if value < 0:
        return None
    unit = ' dollars' if 'dollars' in context else ''
    return value, '{}: {} = {}{}.'.format(context, expression, format_number(value), unit)


def _fmt(n):
    return format_number(n.value if isinstance(n, Number) else n)


def _sentence(text, n):
    left = list(re.finditer(r'[.!?;](?:\s|$)', text[:n.start]))
    start = left[-1].end() if left else 0
    right = re.search(r'[.!?;](?:\s|$)', text[n.end:])
    end = n.end+right.start() if right else len(text)
    return text[start:end]


def _denoms(p, ns):
    """Explicit each/per relations, including fronted and postposed each."""
    text = p.text.lower()
    units = [_unit(text, n) for n in ns]
    result = {}
    indefinite = set()
    verbs = (r'(?:(?:can|will|must)\s+)?(?:has|have|holds?|contains?|needs?|'
             r'produces?|makes?|uses?|eats?|gets?|takes?|took|costs?|needed|records?|writes?|reads?|paints?|bakes?|cooks?|prints?|assembles?|packs?|is|are)')
    for i, n in enumerate(ns):
        end = ns[i+1].start if i+1 < len(ns) else len(text)
        suffix = re.split(r'[.!?;](?:\s|$)', text[n.end:end])[0]
        prefix = re.split(r'[.!?;](?:\s|$)', text[:n.start])[-1]
        capacity = re.match(r'-([a-z]+)\s+([a-z]+)\b',suffix)
        if capacity and _normal(capacity.group(1)) in _MEASURES and _normal(capacity.group(2)) in ('bottle','tank','bag','box','jar','package','container'):
            result[i] = _normal(capacity.group(2))
        m = re.search(r'\b(?:per|each|every|an?)\s+([a-z]+)\b', suffix)
        if (m and not any(w in _STOPS-{'of', 'in', 'for'} for w in re.findall(r'[a-z]+', suffix[:m.start()]))
                and (not m.group(0).startswith(('a ', 'an ')) or m.group(1) in _MEASURES)):
            result[i] = _normal(m.group(1))
        task = re.match(r'\s+[a-z]+\s+to\s+[a-z]+\s+(?:a|an)\s+([a-z]+)\b',suffix)
        if units[i] in ('second','minute','hour') and task:
            result[i] = _normal(task.group(1))
        m = re.search(r'\b(?:each|every)\s+([a-z]+(?:\s+[a-z]+){0,2}?)\s+'+verbs+r'\s+(?:(?:him|her|them|it)\s+)?$', prefix)
        if m:
            result[i] = _head(m.group(1))
        relative = re.search(r'\beach ([a-z]+(?: [a-z]+)?) (?:he|she|they) (?:sells?|makes?|produces?) (?:earns?|gets?|needs?)\s*$',prefix)
        if relative:
            result[i] = _head(relative.group(1))
        if _has(r'\beach\s*$', prefix) and i:
            result[i] = units[i-1]
        if i and (_has(r'^\s+(?!for\b|of\b|in\b|to\b)[a-z]+\s+each\b', suffix) or n.kind == 'money' and _has(r'^\s+each\b',suffix)) and not _has(r'\beach\s+(?:second|minute|hour|day|week|weekend|month|year)\b',suffix):
            # A local subject takes precedence: "some objects with N units each".
            subject = re.search(r'\b(?:some|and|a|an)\s+([a-z]+(?:\s+[a-z]+){0,2}?)\s+(?:with|at|that (?:cost|contain|hold)s?)\s*$', prefix)
            result[i] = _head(subject.group(1)) if subject else units[i-1]
            if result[i] == units[i] and i-1 in result:
                result[i] = result[i-1]
        m = re.search(r'\b(?:a|an)\s+([a-z]+)\s+(?:has|holds|contains|costs)\s*$',prefix)
        if m:
            result[i] = _normal(m.group(1))
            indefinite.add(i)
        if n.kind == 'money' and i and _has(r'\band costs?\s*$',prefix) and i-1 in result:
            result[i] = result[i-1]
        m = re.search(r'\b([a-z]+)\s+(?:that\s+)?each\s+(?:costs?|contains?|holds?)\s*$', prefix)
        if m:
            result[i] = _normal(m.group(1))
        m = re.search(r'\b(?:sell|sells|sold)\s+each\s+([a-z]+)\s+for\s*$', prefix)
        if m:
            result[i] = _normal(m.group(1))
        m = re.search(r'\b(?:bought|buys?|sells?|purchases?)\s+(?:some |the )?([a-z]+(?:[ -]+[a-z]+){0,2}?)\s+(?:at|for|worth)\s*$',prefix)
        if m and _has(r'^\s+each\b',suffix):
            result[i] = _head(m.group(1))
        if i and _has(r'\beach (?:containing|holding|with)\s*$', prefix):
            result[i] = units[i-1]
        # A single-number sentence can put the daily period before the amount.
        sentence = _sentence(text, n)
        m = re.search(r'\b(?:each|every|per)\s+(day|week|hour|minute)\b', sentence)
        if m and n.start < len(p.body) and len([k for k in ns if _sentence(text, k) == sentence]) == 1:
            result.setdefault(i, m.group(1))
    # An indefinite owner is not itself a rate denominator unless another
    # relation actually uses that container (or an explicit each/per cue does).
    for i in indefinite:
        d = result[i]
        if (d not in units and list(result.values()).count(d) == 1
                and not re.search(r'\b(?:each|every|per) '+re.escape(d)+r'\b',text)):
            del result[i]
    return {i: d for i, d in result.items() if d and d not in _STOPS and d != units[i]}


@dataclass
class _Term:
    value: Fraction
    powers: dict
    expression: str
    ids: frozenset


def _term(value, unit, ids, expression=None, denominator=''):
    u, factor = _dim(unit)
    powers = {u: 1}
    value *= factor
    if denominator:
        d, df = _dim(denominator)
        powers[d] = powers.get(d, 0)-1
        value /= df
    return _Term(value, {k:v for k,v in powers.items() if v},
                 expression or _fmt(value), frozenset(ids))


def _terms(p, ns):
    text = p.text.lower()
    units = [_unit(text, n) for n in ns]
    denoms = _denoms(p, ns)
    used, terms = set(), []
    # A measured rate: N items in T minutes; an input requirement for N outputs;
    # or an explicit equivalence.  Only adjacent quantities in one clause pair.
    for i in range(len(ns)-1):
        if i in used or i+1 in used:
            continue
        a, b = ns[i:i+2]
        middle = text[a.end:b.start]
        measured = (units[i+1] in ('second', 'minute', 'hour', 'day', 'week')
                    and _has(r'\bin\s*$', middle) and not _has(r'[.!?;]', middle)
                    and denoms.get(i) not in ('second','minute','hour','day','week'))
        recipe = (_has(r'\b(?:to (?:print|make|produce)|per|for|every)\s*$', middle)
                  and units[i] and units[i+1] and not _has(r'[.!?;]', middle))
        if (measured or recipe) and units[i] and a.value > 0 and b.value > 0:
            terms.append(_term(a.value/b.value, units[i], (i,i+1),
                               '('+_fmt(a)+' / '+_fmt(b)+')', units[i+1]))
            used.update((i,i+1))
    for i, n in enumerate(ns):
        if i not in used:
            if not units[i]:
                return None
            terms.append(_term(n.value, units[i], (i,), _fmt(n), denoms.get(i,'')))
    return terms


def _chain(p, ns):
    """Multiply/divide a unique fully specified chain, with output conversion."""
    text = p.text.lower()
    if _has(r'forth and back|there and back|and then back', text):
        return None
    if _has(r'how long', p.question) and _has(r'\bsame (?:size|job|work)\b', text):
        return None
    if _has(r'\b(?:either|beat|left|remaining|more|less|than|profit|skips?|rest|already|'
            r'twice|thrice|half|double|times|bonus|extra|except|lost|gave|gives|'
            r'change|difference|wait|catch up|increase|decrease|breaks?|weekdays|weekends|workdays|days off)\b', text):
        return None
    asked = _asked(p)
    # Independent prices belong to a money ledger. Dimensional cancellation
    # alone can manufacture a spurious currency answer from a basket by
    # dividing one of its prices and multiplying the others.
    if asked == 'dollar' and sum(n.kind == 'money' for n in ns) > 1:
        return None
    if not asked:
        # A duration query is unambiguous if there is only one time unit.
        if _has(r'how long|total time', p.question):
            times = {_unit(text, n) for n in ns if _unit(text, n) in ('second','minute','hour','day','week')}
            if len(times) == 1:
                asked = times.pop()
            elif _has(r'\bsav(?:e|es|ing)\b',p.body):
                ds = _denoms(p,ns)
                periods = [ds[i] for i,n in enumerate(ns) if i in ds and _has(r'\bsav(?:e|es|ing)\s*$',text[max(0,n.start-30):n.start])]
                if len(periods) == 1:
                    asked = periods[0]
    if not asked:
        return None
    if asked and _has(r'^how much',p.question):
        measured = set()
        for i,n in enumerate(ns):
            suffix = text[n.end:ns[i+1].start if i+1<len(ns) else len(text)]
            if (_unit(text,n) in _MEASURES
                    and re.search(r'\bof (?:the )?'+re.escape(asked)+r'\b',suffix)):
                measured.add(_unit(text,n))
        if len(measured) == 1:
            asked = measured.pop()
    terms = _terms(p, ns)
    if not terms or len(terms) < 2 or len(terms) > 5:
        return None
    # Equal sharing has an explicit denominator in the output dimension.
    denom = ''
    query = re.split(r'\b(?:if|when|after|while|assuming)\b',p.question)[0]
    m = re.search(r'\b(?:per|each|every|a|an)\s+(?:(?:family|individual)\s+)?([a-z]+)', query)
    if m and m.group(1) not in _STOPS:
        denom = _normal(m.group(1))
    target = _term(Fraction(1), asked, (), denominator=denom)
    # Multiple independent counts may only be divided for explicit equal shares
    # or a requested unit price. A physical rate chain has just one root stock.
    rates = [t for t in terms if any(v < 0 for v in t.powers.values())]
    if not rates:
        return None
    if len(terms)-len(rates) > 1 and not (denom or _has(r'\b(?:same number|equally|equal)\b', text)):
        return None
    candidates = []
    for signs in itertools.product((1,-1), repeat=len(terms)):
        powers = {}
        value = Fraction(1)
        for t, sign in zip(terms, signs):
            value = value*t.value if sign == 1 else value/t.value
            for u, power in t.powers.items():
                powers[u] = powers.get(u,0)+sign*power
        if {k:v for k,v in powers.items() if v} == target.powers:
            candidates.append((value/target.value, signs))
    if not candidates:
        return None
    # Prefer the direct orientation of stated rates; reciprocal time chains
    # otherwise admit a second dimensionally valid but reversed schedule.
    least = min(sum(sign < 0 for sign in signs) for value,signs in candidates)
    candidates = [(value,signs) for value,signs in candidates if sum(sign < 0 for sign in signs) == least]
    if len(candidates) != 1:
        return None
    value, signs = candidates[0]
    # For an amount, never invert the sole unqualified stock. For a unit price,
    # the price is the numerator and counts form the denominator.
    if not denom and any(sign < 0 and not any(v < 0 for v in t.powers.values())
                         for t, sign in zip(terms, signs)):
        return None
    expression = ' * '.join(t.expression if sign == 1 else '(1 / '+t.expression+')'
                            for t,sign in zip(terms,signs))
    return _answer(value, expression+' (converted to '+asked+')',
                   'Calculation in dollars' if asked == 'dollar' else 'Calculation')


def _remaining_capacity(p, ns):
    """Existing groups * capacity, then divide the unmet target by new capacity."""
    if len(ns) != 4 or not _has(r'\b(?:more|rest|remaining|total|altogether|needs?|enough)\b', p.text.lower()):
        return None
    text = p.text.lower()
    ds = _denoms(p, ns)
    us = [_unit(text,n) for n in ns]
    if len(ds) != 2:
        return None
    for i,j in (tuple(ds),tuple(reversed(ds))):
        if us[i] != us[j]:
            continue
        counts = [k for k in range(4) if k not in ds and us[k] == ds[i]]
        totals = [k for k in range(4) if k not in ds and us[k] == us[i]]
        if len(counts) != 1 or len(totals) != 1:
            continue
        c,t = counts[0],totals[0]
        if (ds[i] == ds[j] and (c >= i or j <= i)) or not _has(r'\b(?:total|enough|needs?|target|altogether|all)\b', _sentence(text,ns[t])):
            continue
        if _asked(p) not in ('',ds[j]) or not _has(r'how many', p.question):
            continue
        value = (ns[t].value-ns[c].value*ns[i].value)/ns[j].value
        if value >= 0:
            value = Fraction(-(-value.numerator//value.denominator))
            return _answer(value, '({} - {} * {}) / {}'.format(*(_fmt(ns[k]) for k in (t,c,i,j))))
    return None


def _stock_change(p, ns):
    """An explicitly changed stock divided by a measured or unit rate."""
    text = p.text.lower()
    if len(ns) not in (3,4) or not _has(r'\b(?:already|knew|started|stopped|more|left|remaining|now|so far)\b', text):
        return None
    us = [_unit(text,n) for n in ns]
    ds = _denoms(p,ns)
    asked = _asked(p)
    # A discrete rate N every T minutes may omit its numerator's noun.
    if len(ns) == 4:
        for i in range(1,3):
            if i+1 >= len(ns):
                continue
            middle = text[ns[i].end:ns[i+1].start]
            if not _has(r'\bevery\s*$', middle) or us[i+1] not in _MEASURES:
                continue
            others = [k for k in range(4) if k not in (i,i+1)]
            a,b = others
            if us[a] and us[a] == us[b] and _convert(Fraction(1),us[i+1],asked) is not None:
                delta = abs(ns[a].value-ns[b].value)
                v = _convert(delta/ns[i].value*ns[i+1].value,us[i+1],asked)
                return _answer(v,'({} - {}) / {} * {}'.format(_fmt(max(ns[a].value,ns[b].value)),_fmt(min(ns[a].value,ns[b].value)),_fmt(ns[i]),_fmt(ns[i+1])))
    if len(ns) == 3 and len(ds) == 1:
        i = next(iter(ds)); a,b = [j for j in range(3) if j != i]
        if us[a] == us[b] == us[i] and us[i] and _convert(Fraction(1),ds[i],asked) is not None:
            delta = abs(ns[a].value-ns[b].value)
            value = _convert(delta/ns[i].value, ds[i], asked)
            return _answer(value, '({} - {}) / {} (converted to {})'.format(_fmt(max(ns[a].value,ns[b].value)),_fmt(min(ns[a].value,ns[b].value)),_fmt(ns[i]),asked))
    return None


def _travel_wait(p, ns):
    """Same journey at two speeds: difference between arrival times."""
    text = p.text.lower()
    if len(ns) != 3 or not (_has(r'\bwait\b.*\b(?:catch up|arrive|reach)\b', p.question) or _has(r'how many (?:hours|minutes).*\bahead\b',p.question)):
        return None
    ds = _denoms(p,ns)
    if len(ds) != 2:
        return None
    i,j = ds
    k = next(k for k in range(3) if k not in ds)
    us = [_unit(text,n) for n in ns]
    if us[i] != us[j] or ds[i] != ds[j] or _convert(ns[k].value, us[k], us[i]) is None:
        return None
    distance = _convert(ns[k].value,us[k],us[i])
    v = abs(distance/ns[i].value-distance/ns[j].value)
    asked = _asked(p) or ds[i]
    value = _convert(v,ds[i],asked)
    return _answer(value, '{} / {} - {} / {}'.format(_fmt(distance),_fmt(min(ns[i].value,ns[j].value)),_fmt(distance),_fmt(max(ns[i].value,ns[j].value)))) if value is not None else None


def _residual_budget(p, ns):
    """Total minus known purchases, divided by the unknown item's unit cost.

    This applies equally to a money budget and a calorie budget.  Counts are
    joined to their own unit costs before any subtraction is allowed.
    """
    text = p.text.lower()
    if len(ns) not in (4,5) or not _has(r'\b(?:total|spent|budget)\b',text):
        return None
    if _has(r'\b(?:profit|tax|discount|percent|half|twice|more than|less than)\b',text):
        return None
    us = [_unit(text,n) for n in ns]
    ds = _denoms(p,ns)
    # Costs can refer to an explicitly described subtype, e.g. striped ones.
    for i,n in enumerate(ns):
        end = ns[i+1].start if i+1 < len(ns) else len(text)
        if n.kind == 'money' and _has(r'^\s+each\b',text[n.end:end]) and i not in ds:
            ds[i] = us[i-1] if i else ''
    amounts = [i for i,u in enumerate(us) if u in ('dollar','calorie')]
    counts = [i for i in range(len(ns)) if i not in amounts]
    if len(counts) != 1 or len(amounts) < 3:
        return None
    c = counts[0]
    totals = [i for i in amounts if i not in ds and _has(r'\b(?:total|spent|budget)\b',_sentence(text,ns[i]))]
    if len(totals) != 1:
        return None
    t = totals[0]
    if any(us[i] != us[t] for i in amounts):
        return None
    paired = [i for i in ds if i in amounts and (ds[i] == us[c] and us[c] or i == c+1)]
    if len(paired) != 1:
        return None
    known = paired[0]
    unknown = [i for i in amounts if i in ds and i != known]
    if len(unknown) != 1:
        return None
    u = unknown[0]
    asked = _asked(p)
    if asked != ds[u] and not (asked and _has(r'\b(?:ones|items)\b',text[ns[known].end:ns[u].start]) and _has(r'how many',p.question)):
        return None
    fixed = [i for i in amounts if i not in (t,known,u)]
    value = (ns[t].value-ns[c].value*ns[known].value-sum((ns[i].value for i in fixed),Fraction(0)))/ns[u].value
    expression = '({} - {} * {}{}) / {}'.format(_fmt(ns[t]),_fmt(ns[c]),_fmt(ns[known]),''.join(' - '+_fmt(ns[i]) for i in fixed),_fmt(ns[u]))
    return _answer(value,expression,'Remaining budget per '+ds[u]+(' in dollars' if us[t] == 'dollar' else ''))


def _group_measurement(p, ns):
    """Measured output of N producers over one period, then a total interval."""
    if len(ns) != 4:
        return None
    text = p.text.lower()
    a,r,d,t = ns
    us = [_unit(text,n) for n in ns]
    ds = _denoms(p,ns)
    if not _has(r'\b(?:each|every)\s*$',text[:a.start]) or not _has(r'\bproduce[sd]?\s*$',text[a.end:r.start]):
        return None
    if ds != {1: us[2]} or us[1] != us[3] or _asked(p) != us[0]:
        return None
    return _answer(t.value/(r.value*d.value)*a.value,'{} / ({} * {}) * {}'.format(_fmt(t),_fmt(r),_fmt(d),_fmt(a)))


def _partial_period(p, ns):
    """Flow supplied over T periods, subtracted from a total capacity."""
    if len(ns) != 4 or not _has(r'\b(?:more|remaining|left)\b',p.question):
        return None
    text = p.text.lower()
    total, amount, period, duration = ns
    us = [_unit(text,n) for n in ns]
    if us[0] != us[1] or _asked(p) != us[0]:
        return None
    if not _has(r'\bevery\s*$',text[amount.end:period.start]):
        return None
    elapsed = _convert(duration.value,us[3],us[2])
    if elapsed is None:
        return None
    return _answer(total.value-amount.value*elapsed/period.value,'{} - {} * {} / {}'.format(_fmt(total),_fmt(amount),_fmt(elapsed),_fmt(period)))


def _profit(p, ns):
    """Materials / material per item * (sale price - cost per item)."""
    text = p.text.lower()
    if len(ns) != 4 or not _has(r'\bprofit\b',p.question):
        return None
    money = [i for i,n in enumerate(ns) if n.kind == 'money']
    if len(money) != 2:
        return None
    ds = _denoms(p,ns)
    us = [_unit(text,n) for n in ns]
    costs = [i for i in money if _has(r'\b(?:costs?|buys?|bought|takes?)\b',re.split(r'[.!?;](?:\s|$)',text[ns[i-1].end if i else 0:ns[i].start])[-1])]
    sales = [i for i in money if _has(r'\b(?:sell|sells|sold|price)\b',re.split(r'[.!?;](?:\s|$)',text[ns[i-1].end if i else 0:ns[i].start])[-1])]
    if len(costs) != 1 or len(sales) != 1 or costs == sales:
        return None
    c,s = costs[0],sales[0]
    other = [i for i in range(4) if i not in money]
    # Stock of material and its consumption per saleable item.
    if c in ds and s in ds and ds[c] == ds[s]:
        rates = [i for i in other if ds.get(i) == ds[s]]
        if len(rates) == 1:
            r = rates[0]; t = next(i for i in other if i != r)
            if us[t] == us[r] and t not in ds and _has(r'\ball\b',p.question):
                v = ns[t].value/ns[r].value*(ns[s].value-ns[c].value)
                return _answer(v,'{} / {} * ({} - {})'.format(*(_fmt(ns[i]) for i in (t,r,s,c))),'Profit in dollars')
    # Bulk cost and units per bulk package, followed by individual sales.
    if c in ds and s in ds:
        rates = [i for i in other if ds.get(i) == ds[c] and us[i] == ds[s]]
        if len(rates) == 1:
            r = rates[0]; t = next(i for i in other if i != r)
            if us[t] == us[r] and t not in ds:
                v = (ns[s].value-ns[c].value/ns[r].value)*ns[t].value
                return _answer(v,'({} - {} / {}) * {}'.format(*(_fmt(ns[i]) for i in (s,c,r,t))),'Profit in dollars')
    return None


def _mixed_length_shares(p, ns):
    """A composite measurement shared equally, with optional stated conversion."""
    if len(ns) not in (3,5) or not _has(r'\b(?:equal parts|equal pieces|equally)\b',p.text.lower()):
        return None
    text = p.text.lower()
    a,b,count = ns[:3]
    au,bu,cu = (_unit(text,n) for n in ns[:3])
    asked = _asked(p)
    if cu not in ('part','piece') or _convert(a.value,au,bu) is None or asked != bu:
        return None
    if len(ns) == 5:
        x,y = ns[3:]
        if not _has(r'\b(?:equal to|equals|is)\s*$',text[x.end:y.start]):
            return None
        if _convert(x.value,_unit(text,x),_unit(text,y)) != y.value:
            return None
    total = _convert(a.value,au,bu)+b.value
    return _answer(total/count.value,'({} + {}) / {}'.format(_fmt(total-b.value),_fmt(b),_fmt(count)))


def _periodic_skip(p, ns):
    """Skip numbered units divisible by K, then convert per-unit work time."""
    if len(ns) != 3:
        return None
    text = p.text.lower()
    count,divisor,duration = ns
    unit = _unit(text,count)
    if not unit or not _has(r'\bskip[s]?\b',p.body) or not _has(r'\bdivisible by\s*$',text[:divisor.start]):
        return None
    if not _has(r'\b(?:each|per) '+re.escape(unit)+r'\b',text[duration.end:]):
        return None
    if divisor.value.denominator != 1 or count.value.denominator != 1:
        return None
    value = (count.value-count.value//divisor.value)*duration.value
    value = _convert(value,_unit(text,duration),_asked(p))
    if value is None:
        return None
    return _answer(value,'({} - floor({} / {})) * {} (converted)'.format(_fmt(count),_fmt(count),_fmt(divisor),_fmt(duration)))


def _residual_price(p, ns):
    """Known quantity * price plus unknown quantity * price equals total."""
    text = p.text.lower()
    if len(ns) != 4 or not _has(r'how much.*(?:cost|each|per)',p.question):
        return None
    us = [_unit(text,n) for n in ns]
    money = [i for i,n in enumerate(ns) if n.kind == 'money']
    counts = [i for i in range(4) if i not in money]
    if len(money) != 2 or len(counts) != 2:
        return None
    ds = _denoms(p,ns)
    prices = [i for i in money if i in ds]
    if len(prices) != 1:
        return None
    r = prices[0]; t = next(i for i in money if i != r)
    cs = [i for i in counts if us[i] == ds[r]]
    if len(cs) != 1 or not _has(r'\b(?:total|enough|wallet|paid|spent)\b',_sentence(text,ns[t])):
        return None
    c = cs[0]; u = next(i for i in counts if i != c)
    if not us[u] or not re.search(r'\b'+re.escape(us[u])+r'(?:s|es)?\b',p.question):
        return None
    return _answer((ns[t].value-ns[c].value*ns[r].value)/ns[u].value,'({} - {} * {}) / {}'.format(*(_fmt(ns[i]) for i in (t,c,r,u))),'Cost in dollars')


def _change_bills(p, ns):
    """Tender less a repeated purchase, paid back in fixed denominations."""
    text = p.text.lower()
    if len(ns) != 4 or not _has(r'\bchange\b',p.body) or _asked(p) not in ('bill','note'):
        return None
    ds = _denoms(p,ns)
    money = [i for i,n in enumerate(ns) if n.kind == 'money']
    counts = [i for i in range(4) if i not in money]
    if len(money) != 3 or len(counts) != 1:
        return None
    c = counts[0]
    denoms = [i for i in money if _has(r'^\s+(?:bills|notes)\b',text[ns[i].end:])]
    prices = [i for i in money if ds.get(i) == _unit(text,ns[c])]
    if len(denoms) != 1 or len(prices) != 1 or denoms == prices:
        return None
    d,r = denoms[0],prices[0]; t = next(i for i in money if i not in (d,r))
    if not _has(r'\b(?:paid|pays?|using|with)\b',_sentence(text,ns[t])):
        return None
    return _answer((ns[t].value-ns[c].value*ns[r].value)/ns[d].value,'({} - {} * {}) / {}'.format(*(_fmt(ns[i]) for i in (t,c,r,d))))


def _remaining_amount(p, ns):
    """A rate, a target and an existing balance; or more time on an old stock."""
    if len(ns) != 3:
        return None
    text = p.text.lower()
    ds = _denoms(p,ns)
    if len(ds) != 1:
        return None
    r = next(iter(ds)); a,b = [i for i in range(3) if i != r]
    us = [_unit(text,n) for n in ns]
    asked = _asked(p)
    for t,c in ((a,b),(b,a)):
        # Required distance / efficiency - fuel already aboard.
        if (us[t] == us[r] and us[c] == ds[r] == asked
                and _has(r'\b(?:more|remaining|still)\b',p.question)
                and _has(r'\b(?:already|has|have|had|available)\b',_sentence(text,ns[c]))):
            return _answer(ns[t].value/ns[r].value-ns[c].value,'{} / {} - {}'.format(*(_fmt(ns[i]) for i in (t,r,c))))
        # Stock depletion after an explicitly stated elapsed period.
        if us[t] == us[r] and _has(r'\b(?:more|remaining)\b',p.question):
            elapsed = _convert(ns[c].value,us[c],ds[r])
            if elapsed is not None and _asked(p) == ds[r]:
                return _answer(ns[t].value/ns[r].value-elapsed,'{} / {} - {}'.format(_fmt(ns[t]),_fmt(ns[r]),_fmt(elapsed)))
        # Additional work at the same per-item duration.
        if (us[c] == ds[r] == asked and _has(r'\btotal\b',p.question)
                and _has(r'\bnext\b',text)):
            available = _convert(ns[t].value,us[t],us[r])
            if available is not None:
                return _answer(ns[c].value+available/ns[r].value,'{} + {} / {}'.format(_fmt(ns[c]),_fmt(available),_fmt(ns[r])))
    return None


def _round_trip(p, ns):
    """One journey distance and a separately stated speed for each direction."""
    text = p.text.lower()
    if len(ns) != 3 or not _has(r'\b(?:returns?|back)\b',p.body) or not _has(r'how long|how many hours|total time',p.question):
        return None
    ds = _denoms(p,ns)
    if len(ds) != 2:
        return None
    i,j = ds; d = next(k for k in range(3) if k not in ds)
    us = [_unit(text,n) for n in ns]
    if us[i] != us[j] or ds[i] != ds[j]:
        return None
    distance = _convert(ns[d].value,us[d],us[i])
    if distance is None:
        return None
    value = distance/ns[i].value+distance/ns[j].value
    value = _convert(value,ds[i],_asked(p) or ds[i])
    if value is None:
        return None
    return _answer(value,'{} / {} + {} / {}'.format(_fmt(distance),_fmt(ns[i]),_fmt(distance),_fmt(ns[j])))


def _pursuit(p, ns):
    """A head start closes at the difference of two explicit speeds."""
    text = p.text.lower()
    if len(ns) not in (3,4) or not _has(r'\bhead[ -]start\b',p.body):
        return None
    if not _has(r'\b(?:catch|catches|within|get to|before)\b',p.question):
        return None
    ds = _denoms(p,ns)
    if len(ds) != 2:
        return None
    i,j = ds
    us = [_unit(text,n) for n in ns]
    if us[i] != us[j] or ds[i] != ds[j]:
        return None
    stocks = [k for k in range(len(ns)) if k not in ds]
    gaps = [_convert(ns[k].value,us[k],us[i]) for k in stocks]
    if any(v is None for v in gaps) or ns[i].value == ns[j].value:
        return None
    if len(stocks) == 2 and not _has(r'\bwithin\b',text[ns[stocks[0]].end:ns[stocks[1]].start]):
        return None
    gap = gaps[0] if len(gaps) == 1 else gaps[0]-gaps[1]
    period = _asked(p)
    value = _convert(gap/abs(ns[i].value-ns[j].value),ds[i],period)
    return _answer(value,'{} / ({} - {}) (converted to {})'.format(_fmt(gap),_fmt(max(ns[i].value,ns[j].value)),_fmt(min(ns[i].value,ns[j].value)),period)) if value is not None else None


def _commute_requirement(p, ns):
    """A time requirement met by one outward and one return trip each day."""
    if len(ns) != 2 or not _has(r'\bto and from\b',p.body):
        return None
    text = p.text.lower()
    if not _has(r'\b(?:every|each) day\b',p.body) or not _has(r'\b(?:days|day)\b',p.question):
        return None
    if not _has(r'\b(?:must|requirement|complete)\b',text):
        return None
    total,duration = ns
    elapsed = _convert(total.value,_unit(text,total),_unit(text,duration))
    if elapsed is None:
        return None
    return _answer(elapsed/(2*duration.value),'{} / (2 * {})'.format(_fmt(elapsed),_fmt(duration)))


def _cost_per_share(p, ns):
    """A list of purchases, including one repeated price, shared equally."""
    text = p.text.lower()
    if not 4 <= len(ns) <= 6 or not _has(r'how much.*\b(?:cost|pay|spend)\b',p.question):
        return None
    if not _has(r'\b(?:per|each) person\b',p.question):
        return None
    ds = _denoms(p,ns)
    money = [i for i,n in enumerate(ns) if n.kind == 'money']
    counts = [i for i in range(len(ns)) if i not in money]
    if len(counts) != 2:
        return None
    people = [i for i in counts if _unit(text,ns[i]) == 'person']
    if len(people) != 1:
        return None
    d = people[0]; c = next(i for i in counts if i != d)
    paired = [i for i in money if ds.get(i) == _unit(text,ns[c])]
    if len(paired) != 1 or any(i in ds for i in money if i not in paired):
        return None
    r = paired[0]; fixed = [i for i in money if i != r]
    value = (ns[c].value*ns[r].value+sum((ns[i].value for i in fixed),Fraction(0)))/ns[d].value
    return _answer(value,'({} * {}{}) / {}'.format(_fmt(ns[c]),_fmt(ns[r]),''.join(' + '+_fmt(ns[i]) for i in fixed),_fmt(ns[d])),'Cost per person in dollars')


def _profit_from_revenue(p, ns):
    """Revenue less repeated unit expenses, or profit used to infer unit cost."""
    text = p.text.lower()
    if not 3 <= len(ns) <= 5 or not _has(r'\bprofit\b',text):
        return None
    money = [i for i,n in enumerate(ns) if n.kind == 'money']
    counts = [i for i in range(len(ns)) if i not in money]
    if len(counts) != 1:
        return None
    c = counts[0]; ds = _denoms(p,ns)
    prices = [i for i in money if ds.get(i) == _unit(text,ns[c])]
    totals = [i for i in money if i not in prices]
    if len(totals) != 1 or len(prices) != len(money)-1:
        return None
    t = totals[0]
    if len(prices) >= 2 and _has(r'\bprofit\b',p.question) and _has(r'\b(?:sell|sells|sold)\b',_sentence(text,ns[t])):
        value = ns[t].value-ns[c].value*sum((ns[i].value for i in prices),Fraction(0))
        return _answer(value,'{} - {} * ({})'.format(_fmt(ns[t]),_fmt(ns[c]),' + '.join(_fmt(ns[i]) for i in prices)),'Profit in dollars')
    if len(prices) == 1 and _has(r'\bprofit\b',_sentence(text,ns[t])) and _has(r'\b(?:buy|bought|cost)\b',p.question):
        r = prices[0]
        return _answer(ns[r].value-ns[t].value/ns[c].value,'{} - {} / {}'.format(_fmt(ns[r]),_fmt(ns[t]),_fmt(ns[c])),'Purchase cost in dollars')
    return None


def _saving_goal(p, ns):
    """A remaining money goal divided by tasks per period and pay per task."""
    text = p.text.lower()
    if len(ns) != 4 or not _has(r'\b(?:save|saved|saving|already)\b',p.body):
        return None
    money = [i for i,n in enumerate(ns) if n.kind == 'money']
    counts = [i for i in range(4) if i not in money]
    if len(money) != 3 or len(counts) != 1:
        return None
    c = counts[0]; ds = _denoms(p,ns)
    rates = [i for i in money if ds.get(i) == _unit(text,ns[c])]
    if len(rates) != 1 or ds.get(c) != _asked(p):
        return None
    r = rates[0]; goals = [i for i in money if i != r]
    existing = [i for i in goals if _has(r'\b(?:saved|already)\b',_sentence(text,ns[i]))]
    if len(existing) != 1:
        return None
    e = existing[0]; t = next(i for i in goals if i != e)
    return _answer((ns[t].value-ns[e].value)/(ns[c].value*ns[r].value),'({} - {}) / ({} * {})'.format(*(_fmt(ns[i]) for i in (t,e,c,r))),'Saving time')


def _recurring_product(p, ns):
    """One product every N periods, then a duration and a unit payment."""
    text = p.text.lower()
    if len(ns) != 3:
        return None
    period,duration,pay = ns
    relation = re.search(r'\b(?:a|an) ([a-z]+) every\s*$',text[:period.start])
    if not relation or pay.kind != 'money' or _asked(p) != 'dollar':
        return None
    ds = _denoms(p,ns)
    if ds != {2:_normal(relation.group(1))}:
        return None
    available = _convert(duration.value,_unit(text,duration),_unit(text,period))
    if available is None:
        return None
    return _answer(available/period.value*pay.value,'{} / {} * {}'.format(_fmt(available),_fmt(period),_fmt(pay)),'Earnings in dollars')


def _recycling_purchases(p, ns):
    """Recurring consumption, a per-item refund, then purchases at unit price."""
    text = p.text.lower()
    if len(ns) != 4 or not _has(r'\b(?:refund|recycl(?:e|ing))\b',p.body):
        return None
    if not _has(r'how many.*\bbuy\b',p.question):
        return None
    ds = _denoms(p,ns)
    money = [i for i,n in enumerate(ns) if n.kind == 'money']
    counts = [i for i in range(4) if i not in money]
    if len(money) != 2 or len(counts) != 2:
        return None
    stocks = [i for i in counts if i in ds]
    if len(stocks) != 1:
        return None
    c = stocks[0]; d = next(i for i in counts if i != c)
    item = _unit(text,ns[c])
    if _asked(p) != item or any(ds.get(i) != item for i in money):
        return None
    refunds = [i for i in money if _has(r'\brefund(?: of)?\s*$',text[:ns[i].start])]
    if len(refunds) != 1:
        return None
    r = refunds[0]; price = next(i for i in money if i != r)
    periods = _convert(ns[d].value,_unit(text,ns[d]),ds[c])
    if periods is None:
        return None
    v = ns[c].value*periods*ns[r].value/ns[price].value
    return _answer(Fraction(v.numerator//v.denominator),'{} * {} * {} / {}'.format(_fmt(ns[c]),_fmt(periods),_fmt(ns[r]),_fmt(ns[price])))


def _metered_with_fee(p, ns):
    """Distance / speed * hourly price, plus an explicitly fixed fee."""
    text = p.text.lower()
    if len(ns) != 4 or not _has(r'\bflat fee\b',p.body) or _asked(p) != 'dollar':
        return None
    ds = _denoms(p,ns)
    money = [i for i,n in enumerate(ns) if n.kind == 'money']
    if len(money) != 2:
        return None
    prices = [i for i in money if i in ds]
    if len(prices) != 1:
        return None
    price = prices[0]; fee = next(i for i in money if i != price)
    if not _has(r'\bflat fee(?: of)?\s*$',text[:ns[fee].start]):
        return None
    other = [i for i in range(4) if i not in money]
    speeds = [i for i in other if i in ds]
    if len(speeds) != 1:
        return None
    speed = speeds[0]; distance = next(i for i in other if i != speed)
    length = _convert(ns[distance].value,_unit(text,ns[distance]),_unit(text,ns[speed]))
    if length is None:
        return None
    duration = _convert(length/ns[speed].value,ds[speed],ds[price])
    if duration is None:
        return None
    return _answer(duration*ns[price].value+ns[fee].value,'{} / {} * {} + {}'.format(_fmt(length),_fmt(ns[speed]),_fmt(ns[price]),_fmt(ns[fee])),'Cost in dollars')


def _changed_groups(p, ns):
    """Missing people or supplies reduce a known equal allocation."""
    if len(ns) != 3:
        return None
    text = p.text.lower()
    ds = _denoms(p,ns)
    if len(ds) != 1:
        return None
    r = next(iter(ds)); a,b = [i for i in range(3) if i != r]
    us = [_unit(text,n) for n in ns]
    asked = _asked(p)
    for total,removed in ((a,b),(b,a)):
        if (us[total] == us[r] == asked and us[removed] == ds[r]
                and _has(r'\b(?:absent|not be coming|not coming|fewer)\b',_sentence(text,ns[removed]))):
            return _answer(ns[total].value-ns[removed].value*ns[r].value,'{} - {} * {}'.format(*(_fmt(ns[i]) for i in (total,removed,r))))
        if (us[total] == ds[r] == asked and us[removed] == us[r]
                and _has(r'\bless than (?:the )?required\b',text)):
            return _answer(ns[total].value-ns[removed].value/ns[r].value,'{} - {} / {}'.format(*(_fmt(ns[i]) for i in (total,removed,r))))
    return None


def _salary_goal(p, ns):
    """A purchase priced at N periods of salary, funded by periodic savings."""
    if len(ns) != 3 or not _has(r'how long',p.question):
        return None
    text = p.text.lower()
    us = [_unit(text,n) for n in ns]
    periods = [i for i,u in enumerate(us) if u in ('month','year','week','day')]
    if len(periods) != 1:
        return None
    c = periods[0]
    if not _has(r"^\s+[a-z]+['’]?\s+salary\b",text[ns[c].end:]):
        return None
    ds = _denoms(p,ns)
    money = [i for i,n in enumerate(ns) if n.kind == 'money']
    if len(money) != 2 or any(i not in ds for i in money):
        return None
    savings = [i for i in money if _has(r'\bsave\s*$',text[:ns[i].start])]
    if len(savings) != 1:
        return None
    s = savings[0]; income = next(i for i in money if i != s)
    # Income per requested salary period, then money / savings per period.
    ratio = _convert(Fraction(1),us[c],ds[income])
    if ratio is None:
        return None
    goal = ns[c].value*ns[income].value*ratio
    return _answer(goal/ns[s].value,'{} * {} * {} / {}'.format(_fmt(ns[c]),_fmt(ns[income]),_fmt(ratio),_fmt(ns[s])),'Saving time in '+ds[s]+'s')


def _equal_daily_output(p, ns):
    """A host and N friends produce a total over D days and share the work."""
    if len(ns) != 3:
        return None
    text = p.text.lower()
    group,duration,total = ns
    if not _has(r'\band\s*$',text[:group.start]) or not _has(r'^\s+of (?:his|her|their) friends\b',text[group.end:]):
        return None
    if not _has(r'\b(?:same number|equally)\b',text) or not _has(r'\b(?:a|each|per) day\b',p.question):
        return None
    if _unit(text,duration) != 'day' or _unit(text,total) != _asked(p):
        return None
    return _answer(total.value/(group.value+1)/duration.value,'{} / ({} + 1) / {}'.format(_fmt(total),_fmt(group),_fmt(duration)))


def _journey_portions(p, ns):
    """Progress at a speed, expressed in equal portions of a whole journey."""
    if len(ns) != 4:
        return None
    text = p.text.lower()
    distance,parts,speed,duration = ns
    du,pu,su,tu = [_unit(text,n) for n in ns]
    ds = _denoms(p,ns)
    if (ds.keys() != {2} or _asked(p) != pu or not pu
            or not _has(r'\bdivided into\s*$',text[:parts.start])
            or not _has(r'^\s+equal\b',text[parts.end:])):
        return None
    total = _convert(distance.value,du,su)
    elapsed = _convert(duration.value,tu,ds[2])
    if total is None or elapsed is None:
        return None
    return _answer(speed.value*elapsed/(total/parts.value),'{} * {} / ({} / {})'.format(_fmt(speed),_fmt(elapsed),_fmt(total),_fmt(parts)))


def _increment_cost(p, ns):
    """Observed measurement change / change per object * price per object."""
    text = p.text.lower()
    if len(ns) != 4 or _asked(p) != 'dollar':
        return None
    increment,price,start,end = ns
    if price.kind != 'money' or _unit(text,start) or _unit(text,end):
        return None
    relation = re.search(r'\bfor each ([a-z]+)\b[^.!?]*?\b(?:drops?|rises?|increases?|decreases?)\s*$',text[:increment.start])
    ds = _denoms(p,ns)
    if not relation or ds.get(1) != _normal(relation.group(1)):
        return None
    if not _has(r'\bfrom\s*$',text[:start.start]) or not re.fullmatch(r'\s+to\s+',text[start.end:end.start]):
        return None
    return _answer(abs(start.value-end.value)/increment.value*price.value,'({} - {}) / {} * {}'.format(_fmt(max(start.value,end.value)),_fmt(min(start.value,end.value)),_fmt(increment),_fmt(price)),'Cost in dollars')


def solve(problem):
    if re.search(r'how many [a-z]+ and [a-z]+.*(?:altogether|total)', problem.question):
        return None
    if (re.search(r'\b(?:daily (?:serving|amount|requirement|goal|quota|intake)|recommended daily)\b', problem.body)
            and re.search(r'\bweek\b', problem.question)):
        return None
    ns = _numbers(problem)
    if not 2 <= len(ns) <= 7 or any(n.value <= 0 or n.kind == 'percent' for n in ns):
        return None
    currencies = {next((c for c in n.raw if c in '$£€'), '$') for n in ns if n.kind == 'money'}
    if len(currencies) > 1:
        return None
    for rule in (_journey_portions, _increment_cost, _salary_goal,
                 _equal_daily_output, _metered_with_fee, _changed_groups,
                 _cost_per_share, _profit_from_revenue, _saving_goal, _recurring_product,
                 _recycling_purchases, _residual_budget, _residual_price, _change_bills, _remaining_amount,
                 _round_trip, _pursuit, _commute_requirement, _remaining_capacity, _stock_change, _travel_wait,
                 _group_measurement, _partial_period, _profit, _mixed_length_shares,
                 _periodic_skip, _chain):
        result = rule(problem, ns)
        if result is not None:
            value, working = result
            if currencies == {'£'}:
                working = working.replace('dollars', 'pounds')
            elif currencies == {'€'}:
                working = working.replace('dollars', 'euros')
            return value, working
    return None
