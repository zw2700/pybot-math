"""Short rate calculations with explicit unit joins and equal partitions.

The readers attach units before doing arithmetic.  A calculation must consume
all the quantities and have the dimension requested by the question; ambiguous
calculations and unsupported changes are left to the other skills.
"""
import re
from dataclasses import dataclass, replace
from fractions import Fraction

from ..numbers import format_number
from .rates_and_unit_rates_r01_a4 import _singular, _sentence


_STOP = set(('of in on at for to from with and or but as by than before after '
             'during that which who while when are is was were will would can '
             'could should must may might has have had each per every a an the '
             'more extra additional then takes take fit fits holds hold contains '
             'contain makes make does do did he she they it his her their this '
             'these those used use weighing weighs weigh gets get left remaining '
             'altogether combined now total long high deep thick bought sold '
             'received requires require needs need called stayed not picked '
             'brought taken read written runs run drives drive travels travel '
             'goes go went cost costs earns earn paid pays pay spends spend '
             'kept keeps keep puts put cooked cooks cook produced produces '
             'attended attend attends cut divided shared distributed weighs '
             'instead further already away approximately about roughly ordered '
             'inside outside collected collect feed feeds chops chopped parked '
             'less fewer together separately').split())
_MEASURES = set(('second minute hour day week month year semester mile kilometer '
                 'meter centimeter inch foot yard pound ounce gram kilogram '
                 'liter milliliter gallon cup degree watt kilowatt').split())
_ALIASES = {'ml': 'milliliter', 'l': 'liter', 'km': 'kilometer', 'cm': 'centimeter',
            'kg': 'kilogram', 'mph': 'mph', 'coworker': 'person', 'colleague': 'person',
            'student': 'person', 'friend': 'person', 'guest': 'person', 'child': 'person',
            'classmate': 'person', 'worker': 'person', 'employee': 'person',
            'bowlful': 'bowl', 'spoonful': 'spoon', 'dollar': 'money',
            'euro': 'money', 'penny': 'cent', 'morning': 'day', 'evening': 'day'}
# Canonical units and exact conversion factors. Calendar months are kept apart
# from elapsed days; a "month" does not imply a fixed number of days.
_SCALE = {'second': ('hour', Fraction(1, 3600)), 'minute': ('hour', Fraction(1, 60)),
          'hour': ('hour', Fraction(1)), 'day': ('hour', Fraction(24)),
          'week': ('hour', Fraction(168)), 'month': ('month', Fraction(1)),
          'year': ('month', Fraction(12)),
          'liter': ('milliliter', Fraction(1000)),
          'kilogram': ('gram', Fraction(1000)),
          'kilometer': ('meter', Fraction(1000)),
          'centimeter': ('meter', Fraction(1, 100)),
          'foot': ('inch', Fraction(12)), 'yard': ('inch', Fraction(36)),
          'cent': ('money', Fraction(1, 100))}


def _has(pattern, text):
    return re.search(pattern, text) is not None


def _normal(word):
    word = {'mice': 'mouse', 'millilitres': 'milliliter', 'litres': 'liter',
            'milligrams': 'milligram', 'salesperson': 'professional',
            'workdays': 'workday'}.get(word, word)
    word = _singular(word)
    return _ALIASES.get(word, word)


def _head(tail):
    words = re.findall(r"[a-z]+(?:'[a-z]+)?|[^a-z\s-]", tail.lstrip(' -'))
    phrase = []
    for word in words:
        if word in _STOP or not word[0].isalpha():
            break
        word = _normal(word)
        phrase.append(word)
        if word in _MEASURES or word in ('money', 'cent', 'mph'):
            return word
        if len(phrase) == 4:
            break
    return phrase[-1] if phrase else ''


def _unit(p, n):
    if n.kind == 'money':
        return 'money'
    return _head(p.text.lower()[n.end:])


def _quantities(p):
    ns = []
    t = p.text.lower()
    for n in p.numbers:
        if n.value == 1 and re.match(r'-way\b', t[n.end:]):
            continue
        if n.value == 1 and re.match(r'\s+side\b',t[n.end:]) and _has(r'\bother side\b',t):
            continue
        if n.value == 1 and n.start >= len(p.body) and _has(r'\b(?:cost|pay|price)\b',p.question):
            if any(_unit(p,k) == _unit(p,n) for k in p.numbers if k.start < len(p.body)):
                continue
        # Referential "one" is not another measured count.
        if n.value == 1 and (re.match(r'\s+(?:selling|costs?|on average)\b', t[n.end:])
                            or _has(r'\b(?:previous|each)\s*$', t[:n.start])
                            and re.match(r'\s*[,.;?!]|\s+(?:get|receive|have|eat)\b', t[n.end:])):
            continue
        if n.start >= len(p.body) and any(k.value == n.value and _unit(p, k) == _unit(p, n) for k in ns):
            continue
        if re.match(r'\s+dozen\b', t[n.end:]):
            n = replace(n, value=n.value*12)
        ns.append(n)
    return ns


def _question(p):
    q = p.question
    if q.startswith('how long') or _has(r'^how much time\b', q):
        m = re.search(r'\bin (seconds?|minutes?|hours?|days?|weeks?|months?|years?)\b', q)
        if m:
            return _normal(m.group(1))
        times = set(_unit(p,n) for n in p.numbers if _unit(p,n) in ('second','minute','hour','day','week'))
        if len(times) == 1:
            return next(iter(times))
        periods = set(re.findall(r'\b(?:per|each|every|a|an) (second|minute|hour|day|week|month|year)\b', p.body))
        return next(iter(periods)) if len(periods) == 1 else 'hour'
    if q.startswith('how far'):
        return 'distance'
    if _has(r'\b(?:speed|mph|km/hr)\b', q):
        return 'speed'
    if _has(r'^(?:what (?:is the )?distance|what distance)', q):
        m = re.search(r'\bin (miles?|kilometers?|meters?)\b', q)
        return _normal(m.group(1)) if m else 'distance'
    if q.startswith(('how much', 'what is', 'what was')) and _has(r'\b(?:money|earn|make|made|save|saved|pay|cost|spend|share|sell)\b', q):
        return 'money'
    m = re.match(r'how (?:many|much)\s+(?:(?:more|additional|extra)\s+)?(.*)', q)
    if not m:
        m = re.match(r'(?:calculate|find) (?:the )?(?:total )?(?:number|amount) of\s+(.*)', q)
    return _head(m.group(1)) if m else ''


def _result(value, expression, p=None):
    if value < 0:
        return None
    label = ''
    if p is not None and _question(p) == 'money':
        label = 'Amount in dollars: '
    return value, label + expression + ' = ' + format_number(value) + '.'


def _dim(parts):
    return tuple(sorted((k, v) for k, v in parts.items() if v))


def _measure(unit):
    return _SCALE.get(unit, (unit, Fraction(1)))


@dataclass(frozen=True)
class _Amount:
    value: Fraction
    dims: tuple
    expression: str
    used: frozenset


def _amount(value, numerator, denominators, expression, used):
    unit, scale = _measure(numerator)
    dims = {unit: 1}
    value *= scale
    for den in denominators:
        unit, scale = _measure(den)
        dims[unit] = dims.get(unit, 0) - 1
        value /= scale
    return _Amount(value, _dim(dims), expression, frozenset(used))


def _combine(a, b, divide=False):
    if a.used & b.used or (divide and not b.value):
        return None
    dims = dict(a.dims)
    for unit, power in b.dims:
        dims[unit] = dims.get(unit, 0) + (-power if divide else power)
    return _Amount(a.value/b.value if divide else a.value*b.value, _dim(dims),
                   '('+a.expression+(' / ' if divide else ' * ')+b.expression+')', a.used | b.used)


def _denominators(p, ns, i, units):
    """Read N units per group, or each group produces N units."""
    n = ns[i]
    t = p.text.lower()
    end = ns[i+1].start if i+1 < len(ns) else len(t)
    suffix = re.split(r'[.!?;](?:\s|$)', t[n.end:end])[0]
    before = re.split(r'[.!?;](?:\s|$)', t[:n.start])[-1]
    dens = []
    m = re.search(r'(?:\b(?:per|each|every|an?)\s+|/)([a-z]+)\b', suffix)
    if m and not any(w in _STOP - {'of', 'in', 'for', 'it'} for w in re.findall(r'[a-z]+', suffix[:m.start()])):
        den = _head(suffix[m.start(1):])
        if den and den not in _STOP and den not in ('one', 'other'):
            dens.append(den)
    # A subject's rate: "Each jar contains N ...".  A unit may have both
    # a container denominator and a time denominator.
    m = re.search(r'\b(?:each|every)\s+([a-z]+(?:\s+[a-z]+){0,2}?)\s+'
                  r'(?:(?:is|can|will)\s+)?(?:[a-z]+\s+){0,3}?'
                  r'(?:has|holds?|contains?|uses?|produces?|makes?|needs?|takes?|is|had|lays?|seats?|fits?|fills?|yields?|cut into|in)\s*$', before)
    if m:
        den = _head(m.group(1))
        if den and den not in dens:
            dens.append(den)
    # Relative clauses and verb phrases do not change the container's role.
    m = re.search(r'\b(?:each|every)\s+(?:individual\s+)?([a-z]+)\b[^,.;!?]*?'
                  r'\b(?:is (?:then )?(?:cut|chopped) into|produces|weighs|sells)\s*$', before)
    if m:
        den = _normal(m.group(1))
        if den not in dens:
            dens.append(den)
    m = re.search(r'\b(?:a|an)\s+([a-z]+)(?:\s+of\s+[a-z]+)? weighs\s*$', before)
    if m and _normal(m.group(1)) not in dens:
        dens.append(_normal(m.group(1)))
    m = re.search(r'\bin each\s+([a-z]+)(?:\s+of\s+[a-z ]+)?\s*,[^.!?;]*$', before)
    if m:
        den = _normal(m.group(1))
        if den not in dens:
            dens.append(den)
    # "The average weight of a pebble is N pounds."
    m = re.search(r'\b(?:average )?(?:weight|volume|capacity) of (?:a|an|each)\s+([a-z]+) is\s*$', before)
    if m:
        dens.append(_normal(m.group(1)))
    # A plural container as subject explicitly supplies its capacity.
    m = re.search(r'\b([a-z]+s) (?:can )?(?:hold|contain)\s*$', before)
    if m:
        den = _normal(m.group(1))
        if den not in dens:
            dens.append(den)
    if units[i] == 'mph':
        dens.append('hour')
    if i+1 < len(ns) and _has(r'\bin each of\s*$', suffix):
        dens.append(units[i+1])
    if i and _has(r'\beach (?:one )?(?:selling|sells?|costs?) (?:for )?\s*$', before):
        dens.append(units[i-1])
    m = re.search(r'\beach to (?:his|her|their)\s+([a-z]+)', suffix)
    if m and not dens:
        dens.append(_normal(m.group(1)))
    if i and re.match(r'\s*(?:[a-z]+\s+)?each\b', suffix) and not dens:
        dens.append(units[i-1])
    # A supplied calendar length avoids guessing the duration of a month.
    m = re.match(r'\s*(?:day|week)\s+(month|year)\b', suffix)
    if m and units[i] in ('day', 'week'):
        dens.append(m.group(1))
    if units[i] == 'workday' and _has(r'\bspread equally over\s*$', before):
        previous = [ds for j in range(i) for ds in _denominators(p,ns,j,units) if ds in ('week','month')]
        if len(previous) == 1:
            dens.append(previous[0])
    m = re.match(r'\s*-(?:liter|litre|gallon|milliliter|pound|ounce|gram|kilogram)s?\s+([a-z]+)\b',suffix)
    if m and not dens:
        dens.append(_normal(m.group(1)))
    # "N animals that each require H hours", with the count as antecedent.
    if i and _has(r'\b(?:that )?each (?:can )?(?:require|need|hold|contain|use|produce|lay|seat)s?\s*$',before):
        if units[i-1] not in dens:
            dens.append(units[i-1])
    # Unit prices and capacities whose singular subject already denotes one.
    m = re.search(r'\b(?:a|an)\s+([a-z]+)(?:\s+of\s+[a-z ]+)?\s+'
                  r'(?:costs?|needs?|holds?|contains?|is (?:approximately )?|can be sold for)\s*$',before)
    if m and not dens:
        dens.append(_normal(m.group(1)))
    m = re.search(r'\b(?:selling|sells?)\s+([a-z]+)\s+for\s*$',before)
    if m and re.match(r'\s+each\b',suffix) and not dens:
        dens.append(_normal(m.group(1)))
    m = re.search(r'\bto [a-z]+ each ([a-z]+)\b',suffix)
    if m and units[i] in ('second','minute','hour'):
        dens = [_normal(m.group(1))]
    if not dens or (units[i] in ('second','minute','hour') and dens == ['person']):
        sentence = _sentence(t,n)
        m = re.search(r'\b(?:every|each) (day|week|month|hour)\b',sentence)
        if m and len([k for k in ns if _sentence(t,k) == sentence]) == 1:
            dens = [m.group(1)]
    return list(dict.fromkeys(dens))


def _target(p, asked, units):
    if asked == 'speed':
        distances = [u for u in units if u in ('mile', 'kilometer', 'meter', 'mph')]
        if not distances:
            return None
        explicit = re.search(r'\b(miles?|kilometers?|meters?)\s+per\s+(second|minute|hour)\b',p.question)
        asked = _normal(explicit.group(1)) if explicit else ('mile' if distances[0] == 'mph' else distances[0])
        return _amount(Fraction(1), asked, [explicit.group(2) if explicit else 'hour'], '', [])
    if asked == 'distance':
        distances = [u for u in units if u in ('mile', 'kilometer', 'meter', 'mph')]
        if not distances:
            return None
        asked = 'mile' if distances[0] == 'mph' else distances[0]
    dens = []
    query = re.split(r'\b(?:if|when)\b', p.question)[0]
    m = re.search(r'(?<!for )\b(?:per|each|every|an?)\s+([a-z]+)\b', query)
    if m:
        den = _normal(m.group(1))
        if den not in _STOP and den != 'one':
            dens.append(den)
    return _amount(Fraction(1), asked, dens, '', [])


def _dimensional(p, ns):
    if not 2 <= len(ns) <= 3:
        return None
    t = p.text.lower()
    if _has(r'\bbeat\b|\b(?:forth|there) and back\b|and then back', p.question+' '+p.body):
        return None
    if _has(r'\bwith (?:his|her|their)\b', t) and any(_unit(p, n) == 'person' for n in ns):
        return None  # The host may need an additional share.
    # Unit cancellation does not explain a change in stock, a comparison,
    # partial work, or an allocation between different owners.
    if _has(r'\b(?:left|remaining|remain|more|less|fewer|than|instead|minimum|'
            r'twice|times|half|double|percent|already|rest|kept|gave|gives|trade|'
            r'profit|change|increase|decrease|except|round[ -]trip)\b', t):
        # "more" in the query can just mean a future distance, but only with
        # an explicit same-rate statement and a new duration.
        if not (_has(r'\bat (?:this|the same) rate\b', t) and _has(r'\bnext\b', p.question)
                and not _has(r'\b(?:left|remaining|instead|half|twice|gave|change)\b', t)):
            return None
    units = [_unit(p, n) for n in ns]
    if not all(units):
        return None
    asked = _question(p)
    if not asked:
        return None
    atoms = []
    rates = []
    for i, n in enumerate(ns):
        dens = _denominators(p, ns, i, units)
        rates.append(dens)
        numerator = 'mile' if units[i] == 'mph' else units[i]
        atoms.append(_amount(n.value, numerator, dens, format_number(n.value), [i]))
    target = _target(p, asked, units)
    if target is None or not target.dims:
        return None
    # An equal partition supplies a missing denominator even when the unit
    # label is omitted from "each person" in a later clause.
    sharing = _has(r'\b(?:equally|evenly|same (?:number|amount)|exact same amount)\b', t)
    if not any(rates) and not sharing:
        # An observed quantity in a measured duration establishes a rate.
        # Only connect adjacent quantities within the same sentence.
        observed = None
        for i in range(len(ns)-1):
            middle = t[ns[i].end:ns[i+1].start]
            if (units[i+1] in ('second', 'minute', 'hour', 'day', 'week')
                    and units[i] not in _MEASURES.intersection({'second', 'minute', 'hour', 'day', 'week'})
                    and re.fullmatch(r'\s*(?:-?[a-z]+(?:\s+(?:of\s+)?[a-z]+){0,2}\s+)?(?:in|for|over|during)\s+', middle)):
                observed = i
        if observed is None:
            return None
        i = observed
        measured_rate = _combine(atoms[i], atoms[i+1], True)
        atoms = [a for j, a in enumerate(atoms) if j not in (i, i+1)] + [measured_rate]
    # Enumerate the at most two multiplicative operations, retaining only
    # one numerical interpretation for the requested dimension.
    full = frozenset(range(len(ns)))
    candidates = list(atoms)
    for _ in range(len(atoms)-1):
        additions = []
        for a in candidates:
            for b in candidates:
                if a.used & b.used:
                    continue
                for divide in (False, True):
                    c = _combine(a, b, divide)
                    if c is not None and c not in candidates and c not in additions:
                        additions.append(c)
        candidates.extend(additions)
    answers = {}
    for a in candidates:
        if a.used == full and a.dims == target.dims:
            answers[a.value/target.value] = a.expression
    if len(answers) != 1:
        return None
    value, expression = next(iter(answers.items()))
    # Calendar conversions are reflected in the final result; the explanation
    # notes them so the unconverted source-number expression is not misleading.
    if any(_measure(u)[1] != 1 for u in units) or any(_measure(d)[1] != 1 for ds in rates for d in ds):
        return value, 'Using compatible units for {} gives {}.'.format(expression, format_number(value))
    return _result(value, expression, p)


def _work_schedule(p, ns):
    """An output/hour rate and hours/day schedule determine days of work."""
    if len(ns) != 3:
        return None
    t = p.text.lower()
    if _has(r'\b(?:left|remaining|more|less|half|twice|instead|already|off|once|then|finally)\b', t):
        return None
    units = [_unit(p, n) for n in ns]
    ds = [_denominators(p, ns, i, units) for i in range(3)]
    asked = _question(p)
    target = _target(p, asked, units)
    # Equal allocation of weekly hours over explicitly stated workdays.
    if asked == 'money' and target is not None and _has(r'\bspread equally over\b', t):
        for i in range(3):
            if units[i] != 'hour' or len(ds[i]) != 1:
                continue
            for j in range(3):
                if i == j or ds[j] != ds[i] or units[j] != 'workday':
                    continue
                k = next(k for k in range(3) if k not in (i,j))
                if units[k] == 'money' and ds[k] == ['hour'] and _has(r'\beach workday\b', p.question):
                    return _result(ns[i].value/ns[j].value*ns[k].value,
                                   '{} / {} * {}'.format(*(format_number(ns[x].value) for x in (i,j,k))),p)
    for i in range(3):
        for j in range(3):
            if i == j or len(ds[i]) != 1 or len(ds[j]) != 1:
                continue
            k = next(k for k in range(3) if k not in (i, j))
            if units[k] != units[i] or ds[k] or units[j] != ds[i][0] or asked != ds[j][0]:
                continue
            if units[j] not in ('second', 'minute', 'hour', 'day') or asked not in ('hour', 'day', 'week'):
                continue
            return _result(ns[k].value/ns[i].value/ns[j].value,
                           '{} / {} / {}'.format(*(format_number(ns[x].value) for x in (k, i, j))), p)
    # Per-group daily consumption, a period total, and explicit operating days.
    for i in range(3):
        if set(ds[i]) != {asked, 'day'}:
            continue
        for j in range(3):
            if i == j or units[j] != 'day' or ds[j]:
                continue
            k = next(k for k in range(3) if k not in (i, j))
            if units[k] != units[i] or ds[k] not in (['week'], ['month']):
                continue
            if not _has(r'\btotal\b', _sentence(t, ns[k])):
                continue
            return _result(ns[k].value/ns[i].value/ns[j].value,
                           '{} / {} / {}'.format(*(format_number(ns[x].value) for x in (k, i, j))), p)
    return None


def _route_time(p, ns):
    """Add explicit legs of a journey before dividing by its uniform speed."""
    if len(ns) != 3 or not _has(r'\b(?:drive|drives|travel|travels|walk|walks|run|runs|drove|traveled|walked)\b', p.body):
        return None
    t = p.text.lower()
    if _has(r'\b(?:left|remaining|more|less|than|already|twice|half|back|return|round)\b', t):
        return None
    units = [_unit(p,n) for n in ns]
    ds = [_denominators(p,ns,i,units) for i in range(3)]
    rates = [i for i in range(3) if ds[i] == [_question(p)]]
    if len(rates) != 1 or len(set(units)) != 1 or units[0] not in ('mile', 'kilometer', 'meter'):
        return None
    ri = rates[0]
    others = [n for i,n in enumerate(ns) if i != ri]
    if any(ds[i] for i in range(3) if i != ri):
        return None
    return _result(sum((n.value for n in others), Fraction(0))/ns[ri].value,
                   '({} + {}) / {}'.format(*(format_number(n.value) for n in others+[ns[ri]])), p)


def _sum_groups(p, ns):
    if _has(r'\bin (?:tips|bonuses)\b', p.body):
        return None
    if len(ns) != 3:
        return None
    t = p.text.lower()
    if _has(r'\b(?:gave|lost|ate|kept|left|remaining|more|less|twice|half|instead|than)\b', t):
        return None
    units = [_unit(p,n) for n in ns]
    if len(set(units)) == 1 and all(units):
        rates = [(i,_denominators(p,ns,i,units)) for i in range(3)]
        matches = [i for i,ds in rates if ds == [_question(p)]]
        if len(matches) == 1 and _has(r'\b(?:picked|picks|collected|collects|bought|buys|buy|another|additional)\b', t):
            i = matches[0]
            if any(ds for j,ds in rates if j != i):
                return None
            a,b = [n for j,n in enumerate(ns) if j != i]
            return _result((a.value+b.value)/ns[i].value,
                           '({} + {}) / {}'.format(*(format_number(n.value) for n in (a,b,ns[i]))),p)
    # An explicit equal sum shared among a stated number "of them".
    if not _has(r'\b(?:equally|evenly)\b', p.body) or not _has(r'\b(?:each|per)\b', p.question):
        return None
    a,b,count = ns
    if units[0] != units[1] or units[0] != _question(p):
        return None
    if not (_has(r'\b(?:among|amongst|between) (?:the )?\s*$', t[:count.start])
            and re.match(r'\s+of them\b', t[count.end:])):
        return None
    return _result((a.value+b.value)/count.value,
                   '({} + {}) / {}'.format(*(format_number(n.value) for n in ns)), p)


def _shared_cost(p, ns):
    if len(ns) != 2 or _question(p) != 'money':
        return None
    t = p.text.lower()
    # One purchaser and one explicitly singular partner share the whole cost.
    partner = re.search(r'\bsplits? the cost with (?:his|her|their) ([a-z]+)\b', p.body)
    if not partner or partner.group(1) not in ('brother','sister','friend','partner','wife','husband','colleague','roommate'):
        return None
    units = [_unit(p,n) for n in ns]
    prices = [i for i,u in enumerate(units) if u == 'money']
    if len(prices) != 1:
        return None
    i = prices[0]
    if _denominators(p,ns,i,units) != [units[1-i]]:
        return None
    return _result(ns[i].value*ns[1-i].value/2,
                   '{} * {} / 2'.format(format_number(ns[i].value),format_number(ns[1-i].value)),p)


def _explicit_ratio(p, ns):
    if len(ns) != 3:
        return None
    t = p.text.lower()
    a,b,total = ns
    middle = t[a.end:b.start]
    if not _has(r'\bfor every\s*$', middle):
        return None
    au,bu,tu = [_unit(p,n) for n in ns]
    asked = _question(p)
    if asked == 'distance' and au in ('mile','kilometer','meter'):
        asked = au
    if au != asked or bu != tu or not all((au,bu)):
        return None
    if _has(r'\b(?:twice|half|less|more|instead|percent)\b', t):
        return None
    return _result(total.value*a.value/b.value,
                   '{} * {} / {}'.format(*(format_number(n.value) for n in (total,a,b))),p)


def _interval(p, ns):
    if len(ns) != 1:
        return None
    n = ns[0]
    t = p.text.lower()
    m = re.search(r'\b(?:a|an)\s+([a-z]+)\s+every\s*$', t[:n.start])
    if not m or _normal(m.group(1)) != _question(p):
        return None
    unit = _unit(p,n)
    if unit not in ('second', 'minute', 'hour', 'day', 'week'):
        return None
    period = re.search(r'\b(?:a|an|per|each|every)\s+(second|minute|hour|day|week)\b', p.question)
    if not period:
        return None
    a, av = _measure(period.group(1))
    b, bv = _measure(unit)
    if a != b:
        return None
    return _result(av/bv/n.value, 'Intervals per '+period.group(1), p)


def _combined_rates(p, ns):
    if len(ns) != 3:
        return None
    t = p.text.lower()
    if _has(r'\b(?:less|fewer|than|instead|half|twice|already|remaining|left|leaks?)\b', t):
        return None
    units = [_unit(p,n) for n in ns]
    ds = [_denominators(p,ns,i,units) for i in range(3)]
    asked = _question(p)
    # Parallel work (or consumption) adds rates; it does not multiply them.
    if len(set(units)) == 1 and units[0] and asked in ('hour','minute','day','trip','round'):
        ris = [i for i in range(3) if ds[i] == [asked]]
        if asked == 'trip':
            ris = [i for i,n in enumerate(ns) if re.match(r'\s+[a-z]+\s+at a time\b',t[n.end:])]
        if len(ris) == 1:
            # A denominator after a coordinated clause applies to both:
            # "A consumes X kg and B consumes Y kg per day."
            i = ris[0]
            earlier = [j for j in range(i) if _sentence(t,ns[j]) == _sentence(t,ns[i])
                       and not ds[j] and _has(r'\band\b',t[ns[j].end:ns[i].start])]
            if len(earlier) == 1:
                ris.append(earlier[0])
        if len(ris) == 2 and (_has(r'\b(?:together|both|last|consumes?|consumption|extra|aside|fill)\b',t)):
            i,j = ris
            k = next(k for k in range(3) if k not in (i,j))
            if ds[k]:
                return None
            value = ns[k].value/(ns[i].value+ns[j].value)
            if asked == 'trip' and _has(r'\b(?:need|required)\b',p.question):
                value = Fraction(-(-value.numerator//value.denominator))
            return _result(value,'{} / ({} + {})'.format(*(format_number(ns[x].value) for x in (k,i,j))),p)
    # Two production rates, possibly in different time units, for one duration.
    if asked == 'skip' and _has(r'\bskip\b',p.body):
        asked = 'time'
    ris = [i for i in range(3) if len(ds[i]) == 1 and units[i] == asked]
    if len(ris) == 2 and _has(r'\b(?:total|together|combined|altogether)\b',p.question):
        i,j = ris
        k = next(k for k in range(3) if k not in (i,j))
        du,df = _measure(units[k]); au,af = _measure(ds[i][0]); bu,bf = _measure(ds[j][0])
        if du == au == bu and not ds[k]:
            value = (ns[i].value/af+ns[j].value/bf)*ns[k].value*df
            return _result(value,'Combine the rates in the same time unit, then multiply by the duration',p)
    return None


def _changed_rate(p, ns):
    if len(ns) != 3:
        return None
    t = p.text.lower()
    units = [_unit(p,n) for n in ns]
    ds = [_denominators(p,ns,i,units) for i in range(3)]
    asked = _question(p)
    if not units[0] or len(set(units)) != 1 or ds[0] != [asked] or ds[2]:
        return None
    # A change explicitly measures output per unit time, rather than a change
    # in total stock or in working duration.
    after = t[ns[1].end:ns[2].start]
    m = re.match(r'\s+[a-z]+\s+(less|more) per '+re.escape(asked)+r'\b',after)
    if not m or not _has(r'\b(?:speed|rate|now)\b',t[:ns[1].start]):
        return None
    rate = ns[0].value + (ns[1].value if m.group(1)=='more' else -ns[1].value)
    if rate <= 0:
        return None
    return _result(ns[2].value/rate,'{} / ({} {} {})'.format(format_number(ns[2].value),format_number(ns[0].value),
                   '+' if m.group(1)=='more' else '-',format_number(ns[1].value)),p)


def _equal_total_shares(p, ns):
    if not 3 <= len(ns) <= 5 or not _has(r'\b(?:equally|evenly|same amount|same number)\b',p.body):
        return None
    if not _has(r'\b(?:share|shares|sharing|split|splitting|distributed|distribute)\b',p.body):
        return None
    t = p.text.lower()
    if _has(r'\b(?:lost|gave|kept|remaining|rest|left|more|less|times|half|per)\b',p.body):
        return None
    asked = _question(p)
    if not asked:
        return None
    units = [_unit(p,n) for n in ns]
    groups = [i for i,u in enumerate(units) if u == 'person']
    if len(groups) != 1:
        return None
    i = groups[0]
    if any(u != asked for j,u in enumerate(units) if j != i):
        return None
    if not _has(r'\b(?:each|per)\b',p.question):
        return None
    total = sum((n.value for j,n in enumerate(ns) if j != i),Fraction(0))
    return _result(total/ns[i].value,'({}) / {}'.format(' + '.join(format_number(n.value) for j,n in enumerate(ns) if j != i),format_number(ns[i].value)),p)


def _elapsed_work(p, ns):
    if len(ns) != 3 or not _has(r'\b(?:whole|total|entire)\b',p.question):
        return None
    t = p.text.lower()
    units = [_unit(p,n) for n in ns]
    ds = [_denominators(p,ns,i,units) for i in range(3)]
    asked = _question(p)
    for i in range(3):
        if ds[i] != [asked]:
            continue
        for j in range(3):
            if j == i or units[j] != units[i] or ds[j]:
                continue
            k = next(k for k in range(3) if k not in (i,j))
            if units[k] != asked or ds[k] or not _has(r'\b(?:then|after|before)\b',t):
                continue
            return _result(ns[j].value/ns[i].value+ns[k].value,
                           '{} / {} + {}'.format(*(format_number(ns[x].value) for x in (j,i,k))),p)
    return None


def _matched_earnings(p, ns):
    if len(ns) != 3 or not _has(r'\bequal\b.*\bearnings\b',p.question):
        return None
    units = [_unit(p,n) for n in ns]
    ds = [_denominators(p,ns,i,units) for i in range(3)]
    if units != ['hour','money','money'] or ds != [[],['hour'],['hour']] or _question(p) != 'hour':
        return None
    t = p.text.lower()
    if _sentence(t,ns[0]) != _sentence(t,ns[1]) or _sentence(t,ns[1]) == _sentence(t,ns[2]):
        return None
    return _result(ns[0].value*ns[1].value/ns[2].value,
                   '{} * {} / {}'.format(*(format_number(n.value) for n in ns)),p)


def _money_goal_units(p, ns):
    if len(ns) != 3:
        return None
    t = p.text.lower()
    units = [_unit(p,n) for n in ns]
    if any(u not in ('money','cent') for u in units):
        return None
    asked = _question(p)
    ds = [_denominators(p,ns,i,units) for i in range(3)]
    prices = [i for i in range(3) if ds[i] == [asked]]
    if len(prices) != 1:
        return None
    i = prices[0]
    knowns = [j for j in range(3) if j != i]
    if any(ds[j] for j in knowns):
        return None
    # A goal less a contribution, or a payment less returned change, leaves
    # the amount obtained by repeating the stated price or wage.
    contribution = _has(r'\b(?:gave|gift|toward|paid|change)\b',p.body)
    goal = _has(r'\b(?:cost|costs|owed|owe|debt|change)\b',p.body)
    if not contribution or not goal or not _has(r'\b(?:buy|sell|work|earn|pay|purchase)\b',p.question):
        return None
    changes = [j for j in knowns if re.match(r'\s+(?:in )?change\b',t[ns[j].end:])]
    if len(changes) == 1:
        sub = changes[0]
        total = next(j for j in knowns if j != sub)
    else:
        goals = []
        for j in knowns:
            prefix = re.split(r'[.!?;](?:\s|$)',t[:ns[j].start])[-1]
            actions = list(re.finditer(r'\b(?:costs?|owed|owes?|paid|gave|given)\b',prefix))
            if actions and actions[-1].group() in ('cost','costs','owed','owe','owes'):
                goals.append(j)
        if len(goals) != 1:
            return None
        total = goals[0]
        sub = next(j for j in knowns if j != total)
    total_value = ns[total].value*_measure(units[total])[1]
    sub_value = ns[sub].value*_measure(units[sub])[1]
    amount = total_value-sub_value
    if amount < 0:
        return None
    rate = ns[i].value*_measure(units[i])[1]
    return _result(amount/rate,'({} - {}) / {}'.format(format_number(total_value),format_number(sub_value),format_number(rate)),p)


def _electric_energy(p, ns):
    if len(ns) != 3 or not _has(r'\b(?:kwh|kilowatt[ -]hours?)\b',p.question):
        return None
    t = p.text.lower()
    units = [_unit(p,n) for n in ns]
    if units != ['watt','hour','day']:
        return None
    if _denominators(p,ns,1,units) != ['day'] or not _has(r'\bper month\b',p.question):
        return None
    return _result(ns[0].value*ns[1].value*ns[2].value/1000,
                   '{} * {} * {} / 1000'.format(*(format_number(n.value) for n in ns)),p)


def _periodic_amount(p, ns):
    """A measured dose every N time units, repeated to reach a total."""
    if len(ns) != 3:
        return None
    t = p.text.lower()
    asked = _question(p)
    if asked not in ('second','minute','hour','day','week'):
        return None
    units = [_unit(p,n) for n in ns]
    for i in range(1,3):
        prefix = t[ns[i-1].end:ns[i].start]
        if not _has(r'\bevery (?:after )?\s*$',prefix):
            continue
        j = i-1
        k = next(k for k in range(3) if k not in (i,j))
        au,af = _measure(units[j]);bu,bf = _measure(units[k])
        tu,tf = _measure(units[i]);qu,qf = _measure(asked)
        if au != bu or tu != qu or units[i] not in ('second','minute','hour','day','week'):
            continue
        if not _has(r'\b(?:total|goal|needs?|finish|complete)\b',t):
            continue
        value = ns[k].value*bf/(ns[j].value*af)*ns[i].value*tf/qf
        return _result(value,'Convert the total and dose to the same units, then multiply the number of doses by the interval',p)
    return None


def _measured_work(p, ns):
    """The measured time for a job scales to a new amount of that job."""
    if len(ns) != 3 or not _has(r'\b(?:constant|same|this) rate\b|\btakes?\b',p.body):
        return None
    t = p.text.lower()
    a,b,target = ns
    if target.start < len(p.body) or not _has(r'\btake\b',p.question):
        return None
    units = [_unit(p,n) for n in ns]
    times = [i for i in (0,1) if units[i] in ('second','minute','hour','day')]
    if len(times) != 1:
        return None
    i = times[0];j = 1-i
    if not units[j] or units[j] != units[2] or _question(p) not in ('second','minute','hour','day'):
        return None
    if i == 0:
        if not re.fullmatch(r'\s+(?:seconds?|minutes?|hours?|days?)\s+to\s+(?:[a-z]+\s+){1,3}',t[a.end:b.start]):
            return None
    else:
        return None  # The ordinary observed-rate reader handles this order.
    u,uf = _measure(units[i]);v,vf = _measure(_question(p))
    if u != v:
        return None
    return _result(ns[i].value*target.value/ns[j].value*uf/vf,
                   '{} * {} / {}'.format(*(format_number(n.value) for n in (ns[i],target,ns[j]))),p)


def _net_flow(p, ns):
    """A filling rate opposed by an explicitly described leak."""
    if len(ns) != 3 or not _has(r'\bleaks?\b',p.body) or not _has(r'\bfill\b',p.question):
        return None
    units = [_unit(p,n) for n in ns]
    if not units[0] or len(set(units)) != 1:
        return None
    asked = _question(p)
    ds = [_denominators(p,ns,i,units) for i in range(3)]
    rates = [i for i in range(3) if ds[i] == [asked]]
    if len(rates) != 2:
        return None
    leaks = [i for i in rates if _has(r'\bleaks?\b',_sentence(p.text.lower(),ns[i]))]
    if len(leaks) != 1:
        return None
    li = leaks[0]; fi = next(i for i in rates if i != li)
    k = next(k for k in range(3) if k not in rates)
    rate = ns[fi].value-ns[li].value
    single_container = len(ds[k]) == 1 and _has(r'\bfill (?:the|a|an) '+re.escape(ds[k][0])+r'\b',p.question)
    if (ds[k] and not single_container) or rate <= 0:
        return None
    return _result(ns[k].value/rate,'{} / ({} - {})'.format(*(format_number(ns[x].value) for x in (k,fi,li))),p)


def _money_division(p, ns):
    if len(ns) != 3 or _question(p) != 'money':
        return None
    t = p.text.lower()
    money = [n for n in ns if _unit(p,n) == 'money']
    others = [n for n in ns if _unit(p,n) != 'money']
    if len(money) != 2 or len(others) != 1:
        return None
    count = others[0]
    # Total spending minus a separately priced item leaves equal unit costs.
    if _has(r'\b(?:same amount|same price|equally)\b',p.body) and _has(r'\b(?:one|each)\b.*\bcost\b',p.question):
        totals = [n for n in money if _has(r'\b(?:spent|total|paid)\s*$',t[max(0,n.start-30):n.start])]
        if len(totals) == 1:
            total = totals[0]
            other = next(n for n in money if n != total)
            item = re.search(r'\b(?:one|each) ([a-z]+)',p.question)
            if item and _normal(item.group(1)) == _unit(p,count):
                return _result((total.value-other.value)/count.value,
                               '({} - {}) / {}'.format(*(format_number(n.value) for n in (total,other,count))),p)
    # Payment less returned change, then price per purchased item.
    if _has(r'\bchange\b', p.body) and _has(r'\b(?:each|one)\b.*\bcost\b', p.question):
        item = re.search(r'\b(?:each|one)\s+([a-z]+)', p.question)
        changes = [n for n in money if re.match(r'\s+(?:in )?change\b', t[n.end:])]
        if not item or _normal(item.group(1)) != _unit(p,count) or len(changes) != 1:
            return None
        change = changes[0]
        paid = next(n for n in money if n != change)
        if not _has(r'\b(?:pays?|paid|with)\b', _sentence(t,paid)):
            return None
        return _result((paid.value-change.value)/count.value,
                       '({} - {}) / {}'.format(*(format_number(n.value) for n in (paid,change,count))), p)
    # A purchase funded by equal savings per period and a separate gift.
    period = re.search(r'\b(?:per|each|every)\s+(month|week|day|year)\b', p.question)
    if period and _unit(p,count) == period.group(1) and _has(r'\bsave\b', p.question):
        gifts = [n for n in money if _has(r'\b(?:gave|given|gift|gives)\b', _sentence(t,n))]
        totals = [n for n in money if _has(r'\b(?:paid|costs?|total)\b', _sentence(t,n))]
        if len(gifts) == len(totals) == 1 and gifts[0] != totals[0]:
            total, gift = totals[0], gifts[0]
            return _result((total.value-gift.value)/count.value,
                           '({} - {}) / {}'.format(*(format_number(n.value) for n in (total,gift,count))), p)
    return None


def _remove_groups(p, ns):
    if len(ns) != 3 or not _has(r'\b(?:left|remaining)\b', p.question):
        return None
    t = p.text.lower()
    total, groups, removed = ns
    if _unit(p,total) != _question(p) or _unit(p,groups) != _unit(p,removed):
        return None
    if not _has(r'\b(?:same number|same amount|equally|evenly)\b', p.body):
        return None
    if not _has(r'\b(?:puts?|put|divided|distributed)\b', t[total.end:groups.start]):
        return None
    if not _has(r'\b(?:gives?|gave|removes?|removed)\b', t[groups.end:removed.start]):
        return None
    if removed.value > groups.value:
        return None
    return _result(total.value*(groups.value-removed.value)/groups.value,
                   '{} * ({} - {}) / {}'.format(*(format_number(n.value) for n in (total,groups,removed,groups))),p)


def _savings_goal(p, ns):
    if len(ns) != 3 or _question(p) not in ('week', 'month', 'day', 'hour'):
        return None
    if not _has(r'\b(?:buy|purchase|afford|raise|save)\b', p.text.lower()):
        return None
    if not all(_unit(p, n) == 'money' for n in ns):
        return None
    units = ['money']*3
    rates = [(i, _denominators(p, ns, i, units)) for i in range(3)]
    rate = [(i, ds) for i, ds in rates if ds == [_question(p)]]
    if len(rate) != 1:
        return None
    i, _ = rate[0]
    others = [n for j, n in enumerate(ns) if j != i]
    t = p.text.lower()
    goals = [n for n in others if _has(r'\b(?:costs?|price|paid)\s*$', t[max(0,n.start-30):n.start])]
    if len(goals) != 1:
        return None
    goal = goals[0]
    existing = next(n for n in others if n != goal)
    if not _has(r'\b(?:collected|saved|save|has|have|trade in)\b', _sentence(t, existing)):
        return None
    value = (goal.value-existing.value)/ns[i].value
    return _result(value, '({} - {}) / {}'.format(*(format_number(n.value) for n in (goal, existing, ns[i]))), p)


def _split_remainder(p, ns):
    if len(ns) != 3:
        return None
    t = p.text.lower()
    if not _has(r'\b(?:shared|share|split|divided|distributed|distributes)\b', p.body):
        return None
    if not _has(r'\b(?:equally|evenly|same (?:number|amount))\b', t):
        return None
    if not _has(r'\b(?:each|per)\b', p.question):
        return None
    units = [_unit(p, n) for n in ns]
    asked = _question(p)
    groups = [i for i, u in enumerate(units) if u != asked]
    if len(groups) != 1:
        return None
    gi = groups[0]
    amounts = [n for i, n in enumerate(ns) if i != gi]
    if any(_unit(p, n) != asked for n in amounts):
        return None
    reserved = [n for n in amounts if _has(r'\b(?:kept|keeps|reserved|ate|eats?|gave away)\s*$', t[max(0,n.start-30):n.start])]
    if len(reserved) != 1 or not _has(r'\b(?:rest|remaining|remainder)\b', p.body):
        return None
    sub = reserved[0]
    total = next(n for n in amounts if n != sub)
    return _result((total.value-sub.value)/ns[gi].value,
                   '({} - {}) / {}'.format(*(format_number(n.value) for n in (total, sub, ns[gi]))), p)


def _regroup(p, ns):
    if len(ns) != 3 or not _has(r'\binstead\b', p.question):
        return None
    t = p.text.lower()
    count, old, new = ns
    units = [_unit(p, n) for n in ns]
    if units[1] != units[2] or _question(p) != units[0] or not units[0]:
        return None
    ds1 = _denominators(p, ns, 1, units)
    ds2 = _denominators(p, ns, 2, units)
    if ds1 != [units[0]] or ds2 != [units[0]]:
        return None
    return _result(count.value*old.value/new.value,
                   '{} * {} / {}'.format(*(format_number(n.value) for n in ns)), p)


def solve(problem):
    if re.search(r'how many [a-z]+ and [a-z]+.*(?:altogether|total)', problem.question):
        return None
    if (re.search(r'\b(?:daily (?:serving|amount|requirement|goal|quota|intake)|recommended daily)\b', problem.body)
            and re.search(r'\bweek\b', problem.question)):
        return None
    ns = _quantities(problem)
    if not ns or any(n.value <= 0 or n.kind == 'percent' for n in ns):
        return None
    if len({n.raw[0] for n in ns if n.kind == 'money'}) > 1:
        return None
    for rule in (_interval, _work_schedule, _route_time, _money_division, _remove_groups,
                 _combined_rates, _changed_rate, _equal_total_shares, _elapsed_work, _matched_earnings,
                 _money_goal_units, _electric_energy, _periodic_amount, _net_flow, _measured_work,
                 _savings_goal, _split_remainder, _regroup, _sum_groups, _shared_cost,
                 _explicit_ratio, _dimensional):
        result = rule(problem, ns)
        if result is not None:
            return result
    return None
