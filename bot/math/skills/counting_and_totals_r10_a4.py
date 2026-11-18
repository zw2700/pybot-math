"""Explicit multi-stage counts, shared rates and average completion.

These readers join units and stated references, and abstain on quantities or
relations outside their schemas. All intermediate arithmetic remains exact.
"""
import re
from fractions import Fraction

from ..numbers import format_number
from ._counting_common import answer, total, fmt, tokenize
from .counting_and_totals_r02_a4 import _normal_unit
from .counting_and_totals_r08_a2 import _unit as _base_unit, _asked
from .rates_and_unit_rates_r01_a4 import _convert


def has(pattern, text):
    return re.search(pattern, text) is not None


def _unit(tail):
    return _base_unit(re.split(r'\b(?:registered|absent)\b',tail)[0])


def tails(p):
    return [p.text.lower()[n.end:p.numbers[i+1].start if i+1 < len(p.numbers)
                                else len(p.text)] for i, n in enumerate(p.numbers)]


def result(value, expression):
    return answer(value, expression)


def _time_query_matches(p, unit):
    """Abstain when a duration query explicitly requests another unit."""
    requested = re.search(r'^(?:how many|how much) (seconds?|minutes?|hours?)\b'
                          r'|\bin (seconds?|minutes?|hours?)\b',p.question)
    return not requested or _normal_unit(requested.group(1) or requested.group(2)) == unit


def _rate_difference(p):
    """Two explicit rates, compared for the same elapsed time."""
    if len(p.numbers) not in (2, 3) or not has(r'\b(?:more|fewer|difference|longer)\b', p.question):
        return None
    text = p.text.lower()
    a, b = p.numbers[:2]
    ts = tails(p)
    rates = []
    for i in (0, 1):
        m = re.match(r'\s+([a-z]+)\s+(?:per|a|an|each|every)\s+(second|minute|hour|day|week)\b', ts[i])
        if not m:
            break
        rates.append((_normal_unit(m.group(1)), m.group(2)))
    if len(rates) == 2 and rates[0] == rates[1]:
        unit, denominator = rates[0]
        if not has(r'\b'+re.escape(unit)+r'(?:s|es)?\b', p.question):
            return None
        if len(p.numbers) == 3:
            c = p.numbers[2]
            if c.start < len(p.body) or _unit(ts[2]) not in ('second', 'minute', 'hour', 'day', 'week'):
                return None
            duration = _convert(c.value, _unit(ts[2]), denominator)
        else:
            m = re.search(r'\b(?:in|for|over) (?:a|an) (second|minute|hour|day|week)\b', p.question)
            duration = _convert(Fraction(1), m.group(1), denominator) if m else None
        if duration is not None:
            return result(abs(a.value-b.value)*duration,
                          '|{} - {}| x {}'.format(*map(format_number,(a.value,b.value,duration))))
    # Time per one task, compared for a stated number of the same task.
    if len(p.numbers) != 3:
        return None
    c = p.numbers[2]
    if c.start < len(p.body) or not has(r'\b(?:longer|difference|more time)\b',p.question):
        return None
    unit = _unit(ts[0])
    if unit not in ('minute','hour','second') or _unit(ts[1]) != unit:
        return None
    if not _time_query_matches(p,unit):
        return None
    task = re.search(r'\b([a-z]+) (?:a|an) ([a-z]+) in\s*$',text[:a.start])
    second = re.match(r'\s+[a-z]+ to ([a-z]+) (?:a|an) ([a-z]+)\b',text[b.end:])
    if not task or not second or task.groups() != second.groups():
        return None
    if _normal_unit(task.group(2)) != _unit(ts[2]):
        return None
    return result(abs(a.value-b.value)*c.value,
                  '|{} - {}| x {}'.format(*map(format_number,(a.value,b.value,c.value))))


def _grouped_stages(p):
    """Count groups once; every group undergoes each stated stage."""
    ns = p.numbers
    if len(ns) != 3 or any(n.start >= len(p.body) for n in ns):
        return None
    if has(r'\b(?:more|less|fewer|than|left|half|twice|percent)\b',p.text.lower()):
        return None
    ts = tails(p)
    groups = _unit(ts[0])
    measure = _unit(ts[1])
    if not groups or measure not in ('minute','hour','second') or _unit(ts[2]) != measure:
        return None
    if not _time_query_matches(p,measure):
        return None
    if not has(r'\b(?:per|each|every) '+re.escape(groups)+r'\b',ts[2]):
        return None
    if not (has(r'\b(?:how long|how much time|total time)\b',p.question) or _asked(p) == measure):
        return None
    if not re.match(r'\s+[a-z]+ to [a-z]+ and\s*$',ts[1]):
        return None
    a,b,c = (n.value for n in ns)
    return result(a*(b+c),'{} x ({} + {})'.format(*map(format_number,(a,b,c))))


def _paired_durations(p):
    """Two amounts applied over their own explicitly stated periods."""
    ns = p.numbers
    if len(ns) != 4 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\b(?:total|in all|altogether|combined|how much sleep)\b',p.question):
        return None
    if has(r'\b(?:more|less|than|left|half|twice|percent|average)\b',p.body):
        return None
    if has(r'\b(?:total of|altogether|combined|in total)\b',p.body):
        return None  # Aggregate observations are not per-period amounts.
    ts = tails(p)
    units = [_unit(t) for t in ts]
    if (not units[3] and re.search(r'for the other\s*$',ts[2])
            and units[1] == 'day' and has(r'\bweek\b',ts[1])
            and ns[1].value+ns[3].value == 7):
        units[3] = 'day'
    if units[0] != units[2] or not units[0] or units[1] != units[3]:
        return None
    if units[1] not in ('day','week','hour','minute','month'):
        return None
    if units[0] in ('second','minute','hour') and not _time_query_matches(p,units[0]):
        return None
    # An amount is a daily/session amount only with an explicit rate or
    # consecutive repeated days; a free-standing observation is insufficient.
    for i in (0,2):
        if not (has(r'(?:/|\b(?:per|a|each|every)\s+)'+re.escape(units[1])+r'\b',ts[i])
                or (units[i] == 'hour' and units[i+1] == 'day' and has(r'\b(?:sleep|sleeps|slept)\b',p.body))):
            return None
    if _asked(p) != units[0] and not has(r'\b(?:how much time|how long|(?:total |much )sleep)\b',p.question):
        return None
    a,b,c,d = (n.value for n in ns)
    return result(a*b+c*d,'{} x {} + {} x {}'.format(*map(format_number,(a,b,c,d))))


def _weekday_rates(p):
    """Weekdays and weekends partition one ordinary seven-day week."""
    if len(p.numbers) != 2 or not has(r'\b(?:in|during|per|each|a) (?:a )?week\b',p.question):
        return None
    ts = tails(p)
    if any(n.start >= len(p.body) for n in p.numbers):
        return None
    if has(r'\b(?:more|less|than|half|twice|except|average)\b',p.body):
        return None
    days = []
    units = [_unit(t) for t in ts]
    if not units[0] or units[0] != units[1] or _asked(p) != units[0]:
        return None
    for t in ts:
        if not has(r'\b(?:each|every|per|a) day\b',t):
            return None
        labels = [v for k,v in (('weekdays?',5),('weekends?',2)) if has(r'\b'+k+r'\b',t)]
        if len(labels) != 1:
            return None
        days.append(labels[0])
    if set(days) != {2,5}:
        return None
    return result(total(n.value*d for n,d in zip(p.numbers,days)),
                  ' + '.join('{} x {}'.format(format_number(n.value),d) for n,d in zip(p.numbers,days)))


def _affine_total(p):
    """A base plus a second amount explicitly expressed in terms of it."""
    if len(p.numbers) != 3 or any(n.start >= len(p.body) for n in p.numbers):
        return None
    text = tokenize(p)
    if has(r'\b(?:fewer|less|average|percent|each|per)\b',p.text.lower()):
        return None
    unit = _unit(tails(p)[0])
    if not unit or _asked(p) != unit:
        return None
    # Deictic "that number" resolves only to the sole preceding count.
    direct = re.search(r'Q1 times (?:that|this) (?:number|amount) plus Q2\b',text)
    gift = re.search(r'\b(?:gave|gives) (?:him|her|them) Q1 plus Q2 times the number of '+re.escape(unit)+r'(?:s|es)?\b',text)
    disjoint = (has(r'\b(?:left|one) side\b',tails(p)[0])
                and has(r'\b(?:right|other) side\b',tails(p)[2]))
    if direct and disjoint and has(r'\b(?:total|in all|altogether)\b',p.question):
        base,factor,extra = p.values
    elif gift and has(r'\b(?:had|has|have)\b.*\bbefore\b',text[text.index('Q2'):]):
        base,extra,factor = p.values
    else:
        return None
    return result(base+factor*base+extra,'{} + {} x {} + {}'.format(*map(format_number,(base,factor,base,extra))))


def _additional_work(p):
    """Observed time for a quantity, then that quantity plus more work."""
    if len(p.numbers) != 3:
        return None
    a,b,c = p.numbers
    ts = tails(p)
    if a.start >= len(p.body) or b.start >= len(p.body) or c.start < len(p.body):
        return None
    if _unit(ts[0]) not in ('hour','minute','second','day') or not _unit(ts[1]):
        return None
    if not _time_query_matches(p,_unit(ts[0])):
        return None
    if not re.match(r'\s+more\s+',ts[2]) or _unit(ts[1]) != _unit(ts[2]):
        return None
    if not has(r'\btotal time\b|\bhow long\b',p.question):
        return None
    if not has(r'\bto [a-z]+\s*$',ts[0]) or has(r'\b(?:each|per|every|half|twice|less)\b',p.body):
        return None
    if b.value <= 0:
        return None
    return result(a.value*(b.value+c.value)/b.value,
                  '{} x ({} + {}) / {}'.format(*map(format_number,(a.value,b.value,c.value,b.value))))


def _average_completion(p):
    """An average identifies a total: complete or extend a stated list."""
    ns = p.numbers
    text = tokenize(p)
    if not has(r'\baverage\b',p.text.lower()):
        return None
    # N members; K of them average A; the final member has value X.
    if len(ns) == 4 and ns[3].start >= len(p.body):
        if (re.search(r'average (?:age|weight|height|score) of Q1 of them is Q2\b',text)
                and ns[0].value == ns[1].value+1
                and _unit(tails(p)[2]) == _unit(tails(p)[3])
                and _asked(p) == _unit(tails(p)[2])
                and has(r'\b(?:average increase|increase.*average)\b',p.question)):
            n,k,a,x = p.values
            return result((k*a+x)/n-a,'({} x {} + {}) / {} - {}'.format(*map(format_number,(k,a,x,n,a))))
    # A new value is exactly the mean of a fully enumerated list.
    m = re.search(r'\baverage of (?:these|the|those) Q(\d+) (?:scores|values|numbers|marks)\b',text)
    if m:
        ci = int(m.group(1))
        if ci >= 2 and len(ns) == ci+2 and ns[ci].value == ci and ns[-1].value == ci+1:
            if has(r'\btotal (?:score|mark|sum)\b',p.question) and ns[ci].start < len(p.body) and ns[-1].start >= len(p.body):
                if not has(r'\b(?:scored|scores?|marks?)\b',p.body[:ns[0].start]):
                    return None
                for tail in tails(p)[:ci]:
                    if not re.match(r'\s+(?:(?:points?|marks?) )?on\b',tail):
                        return None
                    if not has(r'\b(?:test|exam|quiz|subject)\b',tail):
                        return None
                subtotal = total(n.value for n in ns[:ci])
                return result(subtotal+subtotal/ci,'({}) x {} / {}'.format(fmt(n.value for n in ns[:ci]),ci+1,ci))
    # The query compares a named owner's count to the average of the group.
    if has(r'\bhow many times\b',p.question) and has(r'\baverage (?:amount|number)\b',p.question):
        entries = list(re.finditer(r'\b([a-z]+) (?:has|have) Q(\d+) ([a-z]+)',text))
        if len(entries) != len(ns) or len(ns) < 2:
            return None
        if {int(m.group(2)) for m in entries} != set(range(len(ns))):
            return None
        if len({_normal_unit(m.group(3)) for m in entries}) != 1:
            return None
        owner = re.search(r"how many times can ([a-z]+)'s (?:number|amount)",p.question)
        chosen = [int(m.group(2)) for m in entries if owner and m.group(1) == owner.group(1)]
        if len(chosen) == 1 and ns[chosen[0]].value > 0:
            subtotal = total(p.values)
            return result(subtotal/len(ns)/ns[chosen[0]].value,
                          '({}) / {} / {}'.format(fmt(p.values),len(ns),format_number(ns[chosen[0]].value)))
    return None


def _share_after_removal(p):
    """Remove reserved items, divide the rest, add one recipient's stock."""
    ns = p.numbers
    if len(ns) != 4 or any(n.start >= len(p.body) for n in ns):
        return None
    text = p.text.lower()
    ts = tails(p)
    units = [_unit(t) for t in ts]
    if not units[0] or units[0] != units[1] or units[0] != units[3] or _asked(p) != units[0]:
        return None
    if not has(r'\b(?:equally divided|divided equally|shared equally)\b',text[ns[1].end:ns[2].start]):
        return None
    if not has(r'\b(?:other|remaining|rest)\b',text[ns[1].end:ns[2].start]):
        return None
    if not has(r'\b(?:took out|removed|kept|reserved)\b',text[ns[0].end:ns[1].start]):
        return None
    recipient = re.search(r"\b([a-z]+),? already had\s*$",text[:ns[3].start])
    asked_owner = re.search(r'\bdoes ([a-z]+) have\b',p.question)
    if not recipient or not asked_owner or recipient.group(1) != asked_owner.group(1):
        return None
    if ns[2].value <= 0:
        return None
    a,b,c,d = p.values
    return result((a-b)/c+d,'({} - {}) / {} + {}'.format(*map(format_number,(a,b,c,d))))


def _group_plus_pairs(p):
    """Explicit content per group plus pairs of the same objects."""
    if len(p.numbers) != 3 or not has(r'\b(?:total|in all|altogether)\b',p.question):
        return None
    ts = tails(p)
    unit = _unit(ts[1])
    if not unit or _asked(p) != unit:
        return None
    if not re.fullmatch(r'\s+[a-z ]+ with\s+',ts[0]):
        return None
    if not re.match(r'\s+[a-z]+ each and\s*$',ts[1]):
        return None
    m = re.match(r'\s+(?:additional )?pairs? of ([a-z]+)\b',ts[2])
    if not m or _normal_unit(m.group(1)) != unit:
        return None
    a,b,c = p.values
    return result(a*b+2*c,'{} x {} + 2 x {}'.format(*map(format_number,(a,b,c))))



# Fixed definitions of measurement units, independent of narrative objects.
_MEASURES = {
    'inch': ('length', Fraction(1)), 'foot': ('length', Fraction(12)),
    'yard': ('length', Fraction(36)), 'mile': ('length', Fraction(63360)),
    'meter': ('metric_length', Fraction(1)),
    'kilometer': ('metric_length', Fraction(1000)),
    'centimeter': ('metric_length', Fraction(1,100)),
    'gram': ('mass', Fraction(1)), 'kilogram': ('mass', Fraction(1000)),
    'ounce': ('imperial_mass', Fraction(1)), 'pound': ('imperial_mass', Fraction(16)),
    'second': ('time', Fraction(1)), 'minute': ('time', Fraction(60)),
    'hour': ('time', Fraction(3600)),
}


def _measure(t):
    m = re.match(r'\s*[- ]?([a-z]+)\b',t)
    u = _normal_unit(m.group(1)) if m else ''
    u = {'oz':'ounce'}.get(u,u)
    return u if u in _MEASURES else ''


def _converted_measurements(p):
    """Add independent measurements, or divide a recipe's mass by servings."""
    if has(r'\bfor every\b',p.body):
        return None  # These are rates of time per time, not loose durations.
    ns = p.numbers
    ts = tails(p)
    asked = re.search(r'\b(inches|feet|yards|miles|grams|kilograms|ounces|pounds|seconds|minutes|hours)\b',p.question)
    if not asked or has(r'\b(?:less|more|than|half|twice|lost|removed|left|per|average|back|round|return)\b',p.body):
        return None
    dest = _normal_unit(asked.group(1))
    dim,scale = _MEASURES[dest]
    # An explicit yield followed by a list of ingredients, one serving asked.
    recipe = re.search(r'^for Q0 ([a-z]+) of .+?, (?:you )?(?:need|use)',tokenize(p))
    if recipe:
        if not 3 <= len(ns) <= 7 or ns[0].value <= 0:
            return None
        group = _normal_unit(recipe.group(1))
        last = len(ns)-1
        if ns[-1].start < len(p.body) or ns[-1].value != 1 or _unit(ts[-1]) != group:
            return None
        active = range(1,last)
        divisor = ns[0].value
    else:
        if not 2 <= len(ns) <= 7 or any(n.start >= len(p.body) for n in ns):
            return None
        if not has(r'\b(?:total|combined|altogether|together)\b',p.question):
            return None
        if has(r'\b(?:used|uses?|spent|lost|removed|consumed|yesterday|needs?|requires?)\b',p.body):
            return None
        if has(r'\b(?:each|every|a|an) (?:inch|foot|yard|mile|gram|kilogram|ounce|pound|second|minute|hour)\b',p.body):
            return None
        active = range(len(ns))
        divisor = Fraction(1)
    values = []
    for i in active:
        u = _measure(ts[i])
        if not u or _MEASURES[u][0] != dim:
            return None
        values.append(ns[i].value*_MEASURES[u][1]/scale)
    return result(total(values)/divisor,'({}) / {}'.format(fmt(values),format_number(divisor)))


def _weekly_absences(p):
    """A singular scheduled event on named weekdays, minus missed events."""
    if not 2 <= len(p.numbers) <= 8 or any(n.start >= len(p.body) for n in p.numbers):
        return None
    if not has(r'\b(?:missed|absent)\b',p.body) or not has(r'\b(?:school year|weeks?|total|in all)\b',p.question):
        return None
    text = p.text.lower()
    weekdays = ('monday','tuesday','wednesday','thursday','friday','saturday','sunday')
    prefix = text[:p.numbers[0].start]
    days = [d for d in weekdays if has(r'\b'+d+r's?\b',prefix)]
    if not days or not has(r'\b(?:a|an) [a-z ]+ (?:on|every)\b',prefix):
        return None
    ts = tails(p)
    if _unit(ts[0]) != 'week':
        return None
    missed = []
    for i,n in enumerate(p.numbers[1:],1):
        m = re.match(r'\s+('+'|'.join(weekdays)+r')s?\b',ts[i])
        if not m or m.group(1) not in days or not has(r'\b(?:missed|absent)\b',text[p.numbers[0].end:n.start]):
            return None
        missed.append(n.value)
    return result(p.numbers[0].value*len(days)-total(missed),
                  '{} x {} - ({})'.format(format_number(p.numbers[0].value),len(days),fmt(missed)))


def _session_attendance(p):
    """Sum attendance across sessions with explicit registered/absent counts."""
    ns = list(p.numbers)
    if len(ns) == 5 and ns[-1].start >= len(p.body) and ns[-1].value == 2:
        if not re.match(r'\s+[a-z ]*sessions\b',p.text.lower()[ns[-1].end:]):
            return None
        ns.pop()
    if len(ns) != 4 or any(n.start >= len(p.body) for n in ns):
        return None
    if has(r'\b(?:each|per|every|than|more|average)\b',p.body):
        return None
    text = p.text.lower()
    units = [_unit(text[n.end:]) for n in ns]
    if not units[0] or len(set(units)) != 1 or _asked(p) != units[0]:
        return None
    for i in (0,2):
        middle = text[ns[i].end:ns[i+1].start]
        after = text[ns[i+1].end:ns[i+2].start if i+2 < len(ns) else len(p.body)]
        if not has(r'\bregistered\b',middle) or not has(r'\b(?:were |are )?absent\b',after):
            return None
    a,b,c,d = (n.value for n in ns)
    return result(a-b+c-d,'({} - {}) + ({} - {})'.format(*map(format_number,(a,b,c,d))))


def _category_net_difference(p):
    """Track named categories, then compare two requested residual stocks."""
    if not 3 <= len(p.numbers) <= 8 or any(n.start >= len(p.body) for n in p.numbers):
        return None
    q = re.match(r'how many more ([a-z]+) than ([a-z]+)\b',p.question)
    if not q or has(r'\b(?:each|per|every|half|twice|average)\b',p.body):
        return None
    left,right = map(_normal_unit,q.groups())
    totals = {}
    ts = tails(p)
    mode = None
    removed = set()
    for i,n in enumerate(p.numbers):
        before = p.text.lower()[p.numbers[i-1].end if i else 0:n.start]
        clause = re.split(r'[.!?;]|\b(?:if|then)\b',before)[-1]
        unit = _unit(ts[i])
        if has(r'\b(?:took away|removed|lost|gave away|ate|sold)\b',clause):
            mode = -1
        elif has(r'\b(?:contains?|has|had|there are|there were)\b',clause):
            mode = 1
        elif not has(r'[.!?;]',before) and has(r',|\band\b',before):
            pass
        else:
            return None
        if mode == -1:
            if unit not in totals:
                return None
            totals[unit] -= n.value
            removed.add(unit)
        elif mode == 1:
            if unit in totals or not unit:
                return None
            totals[unit] = n.value
        else:
            return None
    if left == right or not {left,right} <= set(totals) or not removed or min(totals.values()) < 0:
        return None
    return result(totals[left]-totals[right],
                  '{} - {}'.format(format_number(totals[left]),format_number(totals[right])))


def _round_trip_saving(p):
    """A choice between two one-way durations, requested saving both ways."""
    if len(p.numbers) != 2 or not has(r'\b(?:save|saving|less)\b',p.question):
        return None
    if not has(r'\b(?:and back|both ways|round trip)\b',p.question):
        return None
    if not has(r'\bif\b.*\b(?:route|path|road)\b',p.body):
        return None
    ts = tails(p)
    u = _measure(ts[0])
    if u not in ('minute','hour','second') or _measure(ts[1]) != u or not has(r'\btime\b',p.question):
        return None
    if not _time_query_matches(p,u):
        return None
    if any(n.start >= len(p.body) for n in p.numbers):
        return None
    a,b = p.values
    return result(abs(a-b)*2,'|{} - {}| x 2'.format(format_number(a),format_number(b)))


def _serial_stages(p):
    """Sequential independent jobs with multiple stated time stages per job."""
    ns = [n for n in p.numbers if not (n.value == 1 and
          re.match(r'\s+after another\b',p.text.lower()[n.end:]))]
    if len(ns) != 4 or not has(r'\bone after another\b',p.body):
        return None
    ts = [p.text.lower()[n.end:ns[i+1].start if i+1 < len(ns) else len(p.text)]
          for i,n in enumerate(ns)]
    if ns[1].value != 1 or ns[-1].start >= len(p.body):
        return None
    duration = _measure(ts[0])
    group = _unit(ts[1])
    if duration not in ('hour','minute','second') or _measure(ts[2]) != duration or not group or _unit(ts[3]) != group:
        return None
    if not _time_query_matches(p,duration):
        return None
    if not has(r'\b(?:how long|how many hours|how many minutes|how much time)\b',p.question):
        return None
    if not has(r'\b(?:and then|then another)\b',ts[1]):
        return None
    a,_,b,c = (n.value for n in ns)
    return result((a+b)*c,'({} + {}) x {}'.format(*map(format_number,(a,b,c))))

def _group_word(word):
    # Resolve doubled-s plurals of nouns ending in -us; keep singular -us
    # nouns intact before applying the shared ordinary plural grammar.
    if word.endswith('usses'):
        return word[:-3]
    if word.endswith('us'):
        return word
    return _normal_unit(word)


def _group_label(phrase):
    """Read a short nominal label, preserving adjectives and of-complements."""
    stops = set(('a an the are is was were has have had can could would will '
                 'do does did need needs needed require requires required contain contains '
                 'hold holds carry carries play plays eat eats took takes take '
                 'per each every for on in at to from with and while but then '
                 'there that which get gets went seen see remaining left total altogether '
                 'day daily week hour minute live').split())
    words = []
    for word in re.findall(r'[a-z]+|[^a-z\s-]', phrase.strip()):
        if word in stops or not word.isalpha():
            break
        words.append(_group_word(word))
        if len(words) > 5:
            return ()
    return tuple(words)


def _labelled_rate_graph(p):
    """Read count nodes and explicitly labelled per-container edges."""
    ns = p.numbers
    if not 3 <= len(ns) <= 10 or any(n.kind != 'number' or n.value <= 0 for n in ns):
        return None
    if has(r'\b(?:more|fewer|less|than|half|twice|percent|ratio|except|average|remaining|left|lost|sold)\b',p.text.lower()):
        return None
    token = tokenize(p)
    labels = []
    parents = {}
    references = set()
    denominators = {}
    contexts = {}
    for i,n in enumerate(ns):
        following = token.split('Q'+str(i),1)[1]
        labels.append(_group_label(following))
        # Restrict the fronted relation to a single clause and explicit action.
        before = token.split('Q'+str(i),1)[0]
        before = re.split(r'[.;,]|\b(?:and|while|but)\b',before)[-1]
        pre = re.search(r'\b(?:each|every) ([a-z]+(?: [a-z]+){0,4}?) '
                        r'(?:has|have|holds?|contains?|carries|carry|'
                        r'needs?(?: to (?:eat|make|use))?|requires?|'
                        r'plays? with|uses?|eats?)\s*$',before)
        # Postposed rates retain their complete category label.
        after = re.split(r'[.;,]|\b(?:and|while|but)\b',following)[0]
        post = re.search(r'\b(?:on|in|for) each ([a-z]+(?: [a-z]+){0,4})\s*$',after)
        per = re.search(r'\bper ([a-z]+(?: [a-z]+){0,4})\s*$',after)
        recipe = re.search(r'\b(?:are |is )?(?:needed|required) for (?:a|an) ([a-z]+(?: [a-z]+){0,4})\s*$',after)
        explicit = re.search(r'\b(?:are |is )?(?:needed|required) for Q(\d+) ([a-z]+(?: [a-z]+){0,4})\s*$',after)
        proposals = []
        if pre:
            proposals.append(_group_label(pre.group(1)))
        if post:
            proposals.append(_group_label(post.group(1)))
        # A time denominator is context for an each-subject rule, rather than
        # another population node. All such contexts must match the query.
        time = re.search(r'\b(?:per|a|each|every) (day|week|hour|minute)\b',after)
        if pre and time:
            contexts[i] = time.group(1)
        if per and not (pre and time and per.group(1).split()[0] == time.group(1)):
            proposals.append(_group_label(per.group(1)))
        if recipe:
            proposals.append(_group_label(recipe.group(1)))
        if explicit:
            j = int(explicit.group(1))
            if j >= len(ns) or ns[j].value != 1:
                return None
            proposals.append(_group_label(explicit.group(2)))
            references.add(j)
        if proposals:
            if not proposals[0] or any(x != proposals[0] for x in proposals):
                return None
            denominators[i] = proposals[0]
    if not denominators or any(not label for i,label in enumerate(labels) if i not in references):
        return None
    if contexts:
        if set(contexts) != set(denominators) or len(set(contexts.values())) != 1:
            return None
        period = next(iter(contexts.values()))
        if not has(r'\b(?:per|a|each|every) '+re.escape(period)+r'\b',p.question):
            return None
    for i,label in denominators.items():
        candidates = [j for j,x in enumerate(labels) if j != i and j not in references and x == label]
        if len(candidates) != 1:
            return None
        parents[i] = candidates[0]
    if set(parents) & references:
        return None
    if contexts:
        if set(contexts) != set(parents) or len(set(contexts.values())) != 1:
            return None
        period = next(iter(contexts.values()))
        if not has(r'\b(?:per|each|every|a) '+period+r'\b',p.question):
            return None
    return labels, parents, references


def _labelled_group_totals(p):
    """Separate labelled populations times their corresponding item rates."""
    graph = _labelled_rate_graph(p)
    if graph is None:
        return None
    labels, parents, references = graph
    active = set(range(len(p.numbers))) - references
    # Parallel products only; nested graphs have a separate reader below.
    if len(parents) < 2 or set(parents) & set(parents.values()):
        return None
    if len(set(parents.values())) != len(parents) or set(parents) | set(parents.values()) != active:
        return None
    outputs = [labels[i] for i in parents]
    if len({x[-1] for x in outputs}) != 1:
        return None
    asked = _asked(p)
    m = re.match(r'how (?:many|much) (.+)',p.question)
    if m:
        query_label = _group_label(m.group(1))
        if query_label:
            asked = _unit(' '.join(query_label))
    if asked != outputs[0][-1] and not all(_unit(' '.join(x)) == asked for x in outputs):
        return None
    m = re.match(r'how (?:many|much) (.+)',p.question)
    if m:
        asked_label = _group_label(m.group(1))
        if len(asked_label) > 1 and any(label != asked_label for label in outputs):
            return None
    terms = [p.numbers[i].value*p.numbers[j].value for i,j in sorted(parents.items())]
    return result(total(terms),' + '.join('{} x {}'.format(format_number(p.numbers[i].value),format_number(p.numbers[j].value)) for i,j in sorted(parents.items())))


def _labelled_count_chain(p):
    """A chain of labelled categories, asking its endpoint or all categories."""
    graph = _labelled_rate_graph(p)
    if graph is None:
        return None
    labels, parents, references = graph
    active = set(range(len(p.numbers))) - references
    if references or len(parents) != len(active)-1 or len(set(parents.values())) != len(parents):
        return None
    roots = active - set(parents.values())
    if len(roots) != 1:
        return None
    calculated = {}
    visiting = set()
    def evaluate(i):
        if i in visiting:
            raise ValueError('cyclic group graph')
        if i in calculated:
            return calculated[i]
        visiting.add(i)
        value = p.numbers[i].value
        if i in parents:
            value *= evaluate(parents[i])
        visiting.remove(i)
        calculated[i] = value
        return value
    root = next(iter(roots))
    try:
        final = evaluate(root)
    except ValueError:
        return None
    if set(calculated) != active:
        return None
    if _asked(p) == labels[root][-1]:
        return result(final,fmt(p.values,' x '))
    # A common acquisition verb scopes the whole coordinated category list;
    # the same verb and an unqualified total in the query ask all acquisitions.
    token = tokenize(p)
    body = token[:token.lower().find('how ')] if 'how ' in token.lower() else token
    acquisition = re.search(r'\b([a-z]+) (collects?|gathers?|finds?|buys?|receives?) Q0\b',body)
    q = re.match(r'how many ([a-z]+) (?:does|did) ([a-z]+) ([a-z]+) (?:in )?total\?',p.question)
    if not acquisition or not q or q.group(2) not in (acquisition.group(1),'he','she','they','it'):
        return None
    if _group_word(q.group(3)) != _group_word(acquisition.group(2)):
        return None
    # This construction is one coordinated acquisition, with no additional
    # independent sentences or quantified actors hidden in the narrative.
    after = body[acquisition.end():]
    if has(r'[.;].*\w',after.rstrip(' .')) or len({x[-1] for x in labels}) != len(labels):
        return None
    return result(total(calculated.values()),' + '.join(format_number(calculated[i]) for i in sorted(calculated)))


def _missing_labelled_average(p):
    """A counted list has one unknown member and a stated overall mean."""
    if not 4 <= len(p.numbers) <= 12 or any(n.start >= len(p.body) for n in p.numbers):
        return None
    text = tokenize(p)
    intro = re.match(r'(?:the )?average (?:number|amount) of ([a-z ]+) per ([a-z]+) '
                     r'in Q0 ([a-z]+) is Q1[.]\s*',text)
    if not intro or _normal_unit(intro.group(2)) != _normal_unit(intro.group(3)):
        return None
    group = intro.group(2)
    # Consume the complete described list; a stated count labels exactly its
    # known entries and its single unknown entry.
    # Numeric substitution changes offsets, so locate the final question cue.
    query = re.search(r'how many (.+?) (?:are|is) in (?:the )?'+re.escape(group)+r' ([a-z]+)\?',text)
    if not query:
        return None
    entries_text = text[intro.end():query.start()].strip(' .,')
    entries = re.split(r',\s*|\s+and\s+',entries_text)
    known = {}; unknown = []
    used = {0,1}
    for entry in entries:
        entry = re.sub(r'^if\s+','',entry.strip())
        m = re.fullmatch(r'(?:'+re.escape(group)+r' )?([a-z]+) '
                         r'(?:contains?|has|holds?) (Q\d+|some) ([a-z]+(?: [a-z]+){0,3})',entry)
        if not m or m.group(1) in known or any(x[0] == m.group(1) for x in unknown):
            return None
        label,quantity,noun = m.groups()
        if quantity == 'some':
            unknown.append((label,noun))
        else:
            i = int(quantity[1:])
            if i in used or i >= len(p.numbers):
                return None
            used.add(i); known[label] = p.numbers[i].value
    if (len(unknown) != 1 or used != set(range(len(p.numbers)))
            or p.numbers[0].value != len(known)+1):
        return None
    if query.group(2) != unknown[0][0] or _group_label(query.group(1)) != _group_label(unknown[0][1]):
        return None
    n,a = p.numbers[:2]
    value = n.value*a.value-total(known.values())
    return result(value,'{} x {} - ({})'.format(format_number(n.value),format_number(a.value),fmt(known.values())))


def _population_owner(phrase):
    """A possessive owner label, independent of optional honorific spelling."""
    words = re.findall(r"\b([a-z]+)'(?:s)?\b|\b([a-z]+)'(?=\s|$)",phrase)
    names = [a or b for a,b in words]
    return names[0] if len(names) == 1 else None


def _averaged_population_difference(p):
    """Two labelled population sizes times their per-member averages."""
    if len(p.numbers) != 4 or any(n.start >= len(p.body) for n in p.numbers):
        return None
    if has(r'\b(?:percent|half|twice|ratio|lost|left|remaining)\b',p.body):
        return None
    token = tokenize(p)
    records = []
    for i in (0,1):
        before = token.split('Q'+str(i),1)[0]
        before = re.split(r'\beach[.]\s*',before)[-1]
        m = re.search(r'(?:the )?([a-z]+) in (.+?) (?:have|has) an average of\s*$',before)
        following = token.split('Q'+str(i),1)[1]
        unit = re.match(r'\s+([a-z]+) each[.]',following)
        owner = _population_owner(m.group(2)) if m else None
        if not m or not unit or not owner:
            return None
        records.append((owner,_normal_unit(m.group(1)),_normal_unit(unit.group(1)),i))
    if records[0][0] == records[1][0] or records[0][1:3] != records[1][1:3]:
        return None
    # Both counts name their population owner; the second may elide the
    # repeated population noun, but no owner or average is inferred by order.
    counts = {}
    for i in (2,3):
        after = token.split('Q'+str(i),1)[1]
        after = re.split(r'\band\b|,|\bhow\b',after)[0].strip()
        m = re.fullmatch(r'(?:([a-z]+) )?in (.+)',after)
        owner = _population_owner(m.group(2)) if m else None
        if not m or owner not in {x[0] for x in records} or owner in counts:
            return None
        if m.group(1) and _normal_unit(m.group(1)) != records[0][1]:
            return None
        counts[owner] = p.numbers[i].value
    q = re.match(r'how many (more|fewer) ([a-z]+) are there in (.+?) than in (.+?)\?',p.question)
    if not q or _normal_unit(q.group(2)) != records[0][2]:
        return None
    left,right = _population_owner(q.group(3)),_population_owner(q.group(4))
    if not left or not right or left == right or {left,right} != set(counts):
        return None
    amounts = {owner:p.numbers[i].value*counts[owner] for owner,pop,unit,i in records}
    value = amounts[left]-amounts[right]
    if q.group(1) == 'fewer':
        value = -value
    return result(value,'{} - {}'.format(format_number(amounts[left if q.group(1)=='more' else right]),format_number(amounts[right if q.group(1)=='more' else left])))



def _shared_group_contents(p):
    """One count of identical groups, each containing a list of categories."""
    ns = p.numbers
    if not 3 <= len(ns) <= 8 or any(n.start >= len(p.body) for n in ns):
        return None
    if has(r'\b(?:more|fewer|less|than|half|twice|percent|left|remaining|except)\b',p.body):
        return None
    token = tokenize(p)
    start = re.search(r'Q0 ([a-z]+),? (?:and )?(?:each|every) ([a-z]+) '
                      r'(?:has|holds|contains)\s+',token)
    if not start or _normal_unit(start.group(1)) != _normal_unit(start.group(2)):
        return None
    # All the following numbered categories belong to this single each-clause.
    after = token[start.end():]
    sentence = re.split(r'[.;]',after)[0]
    entries = re.split(r',\s*(?:and )?|\s+and\s+',sentence)
    labels=[]; values=[]; used={0}
    for entry in entries:
        m = re.fullmatch(r'Q(\d+) ([a-z]+(?: [a-z]+){0,3})',entry.strip())
        if not m:
            return None
        i = int(m.group(1)); label = _group_label(m.group(2))
        if i in used or i >= len(ns) or not label:
            return None
        used.add(i); labels.append(label); values.append(ns[i].value)
    if used != set(range(len(ns))) or len({x[-1] for x in labels}) != 1:
        return None
    q = re.search(r'(?:how many|total number of) (.+)',p.question)
    requested = _group_label(q.group(1)) if q else ()
    if not requested or _asked(p) != labels[0][-1]:
        return None
    if len(requested) > 1 and any(x != requested for x in labels):
        return None
    return result(ns[0].value*total(values),
                  '{} x ({})'.format(format_number(ns[0].value),fmt(values)))


def _task_action_forms(base):
    forms = {base,base+'s',base+'ed'}
    if base.endswith('e'):
        forms.add(base+'d')
    if base.endswith('y'):
        forms.update((base[:-1]+'ies',base[:-1]+'ied'))
    if base.endswith(('ch','sh','x','z','ss','o')):
        forms.add(base+'es')
    return forms


def _separate_task_times(p):
    """Match each task's count, verb and noun to its own per-task time."""
    ns = p.numbers
    if len(ns) not in (4,6,8) or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\b(?:separately|one at a time|in sequence|sequentially)\b',p.body):
        return None
    if not has(r'\b(?:how long|total time|how many (?:minutes|hours|seconds))\b',p.question):
        return None
    if has(r'\b(?:more|less|than|half|twice|percent|simultaneously)\b',p.body):
        return None
    token=tokenize(p)
    rates=[]
    for m in re.finditer(r'Q(\d+) (seconds?|minutes?|hours?) to ([a-z]+) '
                         r'(?:each|every) ([a-z]+(?: [a-z]+){0,3}?)'
                         r'(?=\s+(?:and|then)\b|[.;,]|$)',token):
        rates.append((int(m.group(1)),_normal_unit(m.group(2)),m.group(3),_group_label(m.group(4))))
    if len(rates)*2 != len(ns) or len({x[0] for x in rates}) != len(rates):
        return None
    target=re.search(r'\bin (seconds?|minutes?|hours?)\b',p.question)
    measure=_normal_unit(target.group(1)) if target else rates[0][1]
    used={x[0] for x in rates};terms=[];work=[]
    for ri,unit,action,label in rates:
        candidates=[]
        for i,n in enumerate(ns):
            if i in used:
                continue
            if _group_label(tails(p)[i]) != label:
                continue
            before=token.split('Q'+str(i),1)[0]
            verb=re.search(r'\b([a-z]+)\s*$',before)
            if verb and verb.group(1) in _task_action_forms(action):
                candidates.append(i)
        if len(candidates) != 1:
            return None
        ci=candidates[0];used.add(ci)
        duration=_convert(ns[ri].value,unit,measure)
        if duration is None:
            return None
        terms.append(ns[ci].value*duration)
        work.append('{} x {}'.format(format_number(ns[ci].value),format_number(duration)))
    if used != set(range(len(ns))):
        return None
    return result(total(terms),' + '.join(work))


def _divided_quantity_measure(p):
    """Equal containers of a measured whole; convert the consumed share."""
    ns=p.numbers
    if len(ns) != 3 or any(n.start >= len(p.body) for n in ns):
        return None
    if any(n.value <= 0 for n in ns) or ns[2].value > ns[1].value:
        return None
    token=tokenize(p)
    allocation=re.search(r'Q0 ([a-z]+) of ([a-z]+(?: [a-z]+){0,3}?) '
                         r'(?:were|was) (?:divided|split|shared)(?: equally)? among Q1 ([a-z]+)[.]',token)
    consumed=re.search(r'\b([a-z]+) (drank|used|consumed|emptied) Q2 ([a-z]+)[.]',token)
    query=re.match(r'how many ([a-z]+) of ([a-z]+(?: [a-z]+){0,3}?) did ([a-z]+) '
                   r'(drink|use|consume|empty)\?',p.question)
    if not all((allocation,consumed,query)):
        return None
    if (_group_label(allocation.group(3)) != _group_label(consumed.group(3))
            or _group_label(allocation.group(2)) != _group_label(query.group(2))
            or consumed.group(1) != query.group(3)):
        return None
    actions={'drank':'drink','used':'use','consumed':'consume','emptied':'empty'}
    if actions[consumed.group(2)] != query.group(4):
        return None
    from .rates_and_unit_rates_r03_a6 import _convert as convert_measure
    source=_normal_unit(allocation.group(1));dest=_normal_unit(query.group(1))
    converted=convert_measure(ns[0].value,source,dest)
    if converted is None:
        return None
    return result(converted/ns[1].value*ns[2].value,
                  '{} / {} x {}'.format(*map(format_number,(converted,ns[1].value,ns[2].value))))


def _mixed_measure_comparison(p):
    """Compare two mixed-unit heights using an explicitly supplied conversion."""
    ns=p.numbers
    if len(ns) != 6 or any(n.start >= len(p.body) for n in ns[:4]) or any(n.start < len(p.body) for n in ns[4:]):
        return None
    token=tokenize(p)
    records=list(re.finditer(r'\b([a-z]+) is Q(\d+) ([a-z]+)(?: and)? '
                             r'Q(\d+) ([a-z]+) tall',token))
    if len(records) != 2 or [int(x) for m in records for x in (m.group(2),m.group(4))] != [0,1,2,3]:
        return None
    big={_normal_unit(m.group(3)) for m in records}
    small={_normal_unit(m.group(5)) for m in records}
    if len(big) != 1 or len(small) != 1 or big == small:
        return None
    q=re.match(r'how much (taller|shorter) is ([a-z]+) than ([a-z]+) in ([a-z]+) '
               r'if Q4 ([a-z]+) is equal to Q5 ([a-z]+)\?',token[token.lower().rfind('how much '):])
    if not q or {_normal_unit(q.group(4)),_normal_unit(q.group(6))} != small or {_normal_unit(q.group(5))} != big:
        return None
    if ns[4].value <= 0 or ns[5].value <= 0:
        return None
    factor=ns[5].value/ns[4].value
    heights={m.group(1):ns[int(m.group(2))].value*factor+ns[int(m.group(4))].value for m in records}
    if q.group(2) == q.group(3) or {q.group(2),q.group(3)} != set(heights):
        return None
    left,right=heights[q.group(2)],heights[q.group(3)]
    if q.group(1) == 'shorter':
        left,right=right,left
    return result(left-right,'{} - {}'.format(format_number(left),format_number(right)))

def _time_rate_pairs(p):
    """Two explicit duration/rate observations compared or combined."""
    ns = p.numbers
    if len(ns) != 4:
        return None
    ts = tails(p)
    terms = []
    outputs = []
    for i,j in ((0,1),(2,3)):
        if _measure(ts[i]) in ('hour','minute','second','day'):
            di,ri = i,j
        elif _measure(ts[j]) in ('hour','minute','second','day'):
            ri,di = i,j
        else:
            return None
        rate = re.match(r'\s+([a-z]+) (?:per|an?|each|every) (second|minute|hour|day)\b',ts[ri])
        if not rate or not _measure(ts[ri]):
            return None
        duration = _convert(ns[di].value,_measure(ts[di]),rate.group(2))
        if duration is None:
            return None
        # The relation must stay local to a single explicitly described trip.
        middle = p.text.lower()[ns[i].end:ns[j].start]
        if has(r'[.!?;]',middle) or not has(r'\b(?:for|at|during|in)\b',middle):
            return None
        terms.append(ns[ri].value*duration)
        outputs.append(_normal_unit(rate.group(1)))
    if outputs[0] != outputs[1] or not has(r'\b'+re.escape(outputs[0])+r'(?:s|es)?\b',p.question):
        return None
    if has(r'\b(?:farther|further|more|fewer|difference)\b',p.question):
        return result(abs(terms[0]-terms[1]),'|'+fmt(terms,' - ')+'|')
    if has(r'\b(?:total|altogether|combined|in all)\b',p.question):
        return result(total(terms),fmt(terms))
    return None


def _cycle_time(p):
    """A repeated serial cycle, divided into an available time budget."""
    ns = p.numbers
    if len(ns) != 3 or not has(r'\b(?:number of times|how many times)\b',p.question):
        return None
    if ns[2].start < len(p.body) or any(n.start >= len(p.body) for n in ns[:2]):
        return None
    ts = tails(p)
    unit = _measure(ts[0])
    if unit not in ('minute','hour','second') or _measure(ts[1]) != unit:
        return None
    if not has(r'\b(?:and then|then|after that)\b',ts[0]):
        return None
    if not has(r'\btakes?\b',p.body[:ns[0].start]) or not has(r'\btakes?\b',ts[0]):
        return None
    available = _convert(ns[2].value,_measure(ts[2]),unit)
    per_cycle = ns[0].value+ns[1].value
    if available is None or per_cycle <= 0:
        return None
    count = available/per_cycle
    return result(Fraction(count.numerator//count.denominator),
                  '{} / ({} + {}), counting complete cycles'.format(*map(format_number,(available,ns[0].value,ns[1].value))))


def _relative_rate_period(p):
    """An explicit increase by a multiple of the old rate, over a duration."""
    if len(p.numbers) != 3:
        return None
    a,b,c = p.numbers
    ts = tails(p)
    rate = re.match(r'\s+([a-z]+) per (day|hour|minute|week|month|year)\b',ts[0])
    if not rate or c.start < len(p.body):
        return None
    text = p.text.lower()
    if not re.search(r'\bincreased by\s*$',text[a.end:b.start]):
        return None
    if not re.match(r'\s+times more per '+rate.group(2)+r'\b',ts[1]):
        return None
    if not has(r'\btotal\b',p.question) or not has(r'\b'+rate.group(1)+r'\b',p.question):
        return None
    duration = _convert(c.value,_unit(ts[2]),rate.group(2))
    if duration is None:
        return None
    return result(a.value*(1+b.value)*duration,
                  '{} x (1 + {}) x {}'.format(*map(format_number,(a.value,b.value,duration))))


def _net_stock_change(p):
    """The net change caused by purchases and sales, without an initial stock."""
    if not has(r'\bnet (?:increase|decrease|change)\b',p.question):
        return None
    ns = list(p.numbers)
    text = p.text.lower()
    # A stated duration refers to the distinct named days in this ledger.
    if ns and ns[-1].start >= len(p.body):
        n = ns.pop()
        weekdays = re.findall(r'\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',p.body)
        if _unit(text[n.end:]) != 'day' or n.value != len(set(weekdays)):
            return None
    if not 2 <= len(ns) <= 10 or any(n.start >= len(p.body) for n in ns):
        return None
    if has(r'\b(?:each|per|every|times|more than|fewer|half|twice)\b',p.body):
        return None
    query = re.search(r'\bnumber of ([a-z]+)\b',p.question)
    if not query:
        return None
    unit = _normal_unit(query.group(1))
    signed = []
    for i,n in enumerate(ns):
        before = text[ns[i-1].end if i else 0:n.start]
        clause = re.split(r'[.!?;]|\band\b',before)[-1]
        verbs = re.findall(r'\b(sold|sells?|bought|buys?|purchased)\b',clause)
        if len(verbs) != 1:
            return None
        u = _unit(text[n.end:ns[i+1].start if i+1<len(ns) else len(p.body)])
        if u not in ('',unit):
            return None
        signed.append(n.value*(-1 if verbs[0] in ('sold','sell','sells') else 1))
    value = total(signed)
    if has(r'\bnet decrease\b',p.question):
        value = -value
    return result(value,fmt(signed))


def _goal_time(p):
    """A requested duration to complete an explicit count goal at a rate."""
    if len(p.numbers) != 2 or any(n.start >= len(p.body) for n in p.numbers):
        return None
    q = re.match(r'how many (seconds|minutes|hours|days)\b',p.question)
    if not q or not has(r'\b(?:need|take|required)\b',p.question):
        return None
    ts = tails(p)
    rate = re.match(r'\s+(times|[a-z]+) (?:per|a|an|each|every) (second|minute|hour|day)\b',ts[1])
    if not rate or p.numbers[1].value <= 0:
        return None
    unit = _normal_unit(rate.group(1))
    goal = _unit(ts[0])
    record = has(r'\brecord is\s*$',p.body[:p.numbers[0].start]) and rate.group(1) == 'times'
    if goal != unit and not record:
        return None
    if not record and not has(r'\b(?:goal|target|needs? to|wants? to)\b',p.body[:p.numbers[0].start]):
        return None
    duration = _convert(p.numbers[0].value/p.numbers[1].value,rate.group(2),_normal_unit(q.group(1)))
    if duration is None:
        return None
    return result(duration, '{} / {} in {}'.format(*map(format_number,p.values),q.group(1)))


def _uncovered_rectangle(p):
    """Rectangular area less the area of a square covering."""
    if len(p.numbers) != 3 or any(n.start >= len(p.body) for n in p.numbers):
        return None
    text = p.text.lower()
    if not has(r'\brectangular\b',p.body) or not has(r'\bsquare\b',p.body):
        return None
    if not has(r'\b(?:uncovered|not covered)\b',p.question):
        return None
    ts = tails(p)
    dimensions = []
    for t in ts:
        m = re.match(r'\s+(m|meters?|cm|centimeters?|feet|inches)\b',t)
        if not m:
            return None
        u = _normal_unit(m.group(1))
        dimensions.append({'m':'meter','cm':'centimeter'}.get(u,u))
    if len(set(dimensions)) != 1:
        return None
    if not has(r'\blong\b',ts[0]) or not has(r'\bwide\b',ts[1]) or not has(r'\bsides?\b',ts[2]):
        return None
    requested = re.search(r'\bsquare (meters?|centimeters?|feet|inches)\b',p.question)
    if not requested or _normal_unit(requested.group(1)) != dimensions[0]:
        return None
    a,b,c = p.values
    return result(a*b-c*c,'{} x {} - {} x {}'.format(*map(format_number,(a,b,c,c))))


def _elapsed_stages(p):
    """Sequential measured activity and explicit added delay, all same units."""
    ns = p.numbers
    if not 3 <= len(ns) <= 8 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\b(?:total time|how many (?:minutes|hours|seconds).*take)\b',p.question):
        return None
    if has(r'\b(?:each|every|per|less|than|half|twice|meanwhile|simultaneously|at the same time)\b',p.body):
        return None
    ts = tails(p)
    unit = _measure(ts[0])
    if unit not in ('minute','second','hour') or any(_measure(t) != unit for t in ts):
        return None
    if not _time_query_matches(p,unit):
        return None
    if not has(r'\b(?:another|finally|then)\b',p.body):
        return None
    signs = []
    for i,n in enumerate(ns):
        before = p.text.lower()[ns[i-1].end if i else 0:n.start]
        clause = re.split(r'[.!?;]|\b(?:and|but|a process that)\b',before)[-1]
        if not re.search(r'\b(?:watches?|watched|adds?|adding|takes?|took|spent|spends?) '
                         r'(?:(?:the|a|an) [a-z]+ )?(?:for )?(?:another |the last )?$',clause):
            return None
        signs.append(n.value)
    return result(total(signs),fmt(signs))


def _compound_time_difference(p):
    """Per-task durations with an explicit singular reference, then a batch."""
    ns = p.numbers
    if len(ns) != 4 or not has(r'\b(?:longer|more time)\b',p.question):
        return None
    if ns[2].value != 1 or ns[-1].start < len(p.body):
        return None
    ts = tails(p)
    unit = _measure(ts[0])
    if unit not in ('minute','hour','second') or _measure(ts[1]) != unit:
        return None
    if not _time_query_matches(p,unit):
        return None
    token = tokenize(p)
    first = re.search(r'\b([a-z]+) (?:a|an) ([a-z]+)(?: of [a-z]+)? in Q0\b',token)
    second = re.search(r'Q1 [a-z]+ to ([a-z]+) Q2 ([a-z]+)\b',token)
    if not first or not second or first.groups() != second.groups():
        return None
    if _normal_unit(first.group(2)) != _unit(ts[3]):
        return None
    if not has(r'\b'+re.escape(first.group(1))+r' Q3\b',token):
        return None
    a,b,_,c = p.values
    return result(abs(a-b)*c,'|{} - {}| x {}'.format(*map(format_number,(a,b,c))))


def _excluded_weekdays(p):
    """Daily distance/work, some days off every week, then stated weeks."""
    ns = p.numbers
    if len(ns) != 3 or ns[2].start < len(p.body):
        return None
    ts = tails(p)
    if not has(r'\b(?:each|per|every|a) day\b',ts[0]) or _unit(ts[1]) != 'day' or _unit(ts[2]) != 'week':
        return None
    if not has(r'\b(?:every|each|a|per) week\b',ts[1]):
        return None
    before = p.body[ns[0].end:ns[1].start]
    if not has(r'\b(?:does not|doesn\'t|do not|not go|days off)\b',before):
        return None
    unit = _unit(ts[0])
    if not unit or not has(r'\b'+re.escape(unit)+r'(?:s|es)?\b',p.question):
        return None
    if not 0 <= ns[1].value <= 7:
        return None
    a,b,c = p.values
    return result(a*(7-b)*c,'{} x (7 - {}) x {}'.format(*map(format_number,(a,b,c))))


def _measurement_difference(p):
    """Two comparable lengths with an explicit output unit."""
    if len(p.numbers) != 2 or any(n.start >= len(p.body) for n in p.numbers):
        return None
    if not has(r'\b(?:longer|shorter|taller|difference)\b',p.question):
        return None
    ts = tails(p)
    units = [_measure(t) for t in ts]
    if not all(units) or _MEASURES[units[0]][0] != _MEASURES[units[1]][0]:
        return None
    m = re.search(r'\b(kilometers?|meters?|centimeters?|inches|feet|yards|miles)\b',p.question)
    if not m:
        return None
    dest = _normal_unit(m.group(1))
    if dest not in _MEASURES or _MEASURES[dest][0] != _MEASURES[units[0]][0]:
        return None
    if has(r'\b(?:each|per|every|than|more|less|twice|half)\b',p.body):
        return None
    vals = [n.value*_MEASURES[u][1]/_MEASURES[dest][1] for n,u in zip(p.numbers,units)]
    return result(abs(vals[0]-vals[1]),'|'+fmt(vals,' - ')+'|')


def _average_relative_measurement(p):
    """Compare a named person's own measurement with the group mean."""
    ns = p.numbers
    if not 2 <= len(ns) <= 6 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\baverage (?:height|weight|length)\b',p.question):
        return None
    if not has(r'\b(?:shorter|taller|heavier|lighter|longer)\b',p.question):
        return None
    ts = tails(p)
    units = [_measure(t) for t in ts]
    if not units[0] or len(set(units)) != 1:
        return None
    if has(r'\b(?:each|per|every|than|times|more|less|twice|half|total)\b',p.body):
        return None
    # The first measurement must belong to the person or household asked,
    # rather than an arbitrary member of the list.
    owner = re.search(r"\b([a-z]+)'s ([a-z]+)\b",p.question)
    if not owner or not has(r'\b'+re.escape(owner.group(1))+r'\b',p.body[:ns[0].start]):
        return None
    first = p.body[:ns[0].start]
    if not has(r"\b(?:his|her|their) (?:family's )?"+re.escape(owner.group(2))+r' is\s*$',first):
        return None
    mean = total(p.values)/len(ns)
    value = mean-ns[0].value if has(r'\b(?:shorter|lighter)\b',p.question) else ns[0].value-mean
    return result(value,'({}) / {} compared with {}'.format(fmt(p.values),len(ns),format_number(ns[0].value)))


def _sequential_measure(p):
    """A measured stock with explicit interleaved scaling and additions."""
    ns = p.numbers
    if not 2 <= len(ns) <= 5 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\bfinal (?:weight|mass|volume|length|height)\b',p.question):
        return None
    ts = tails(p)
    units = [_measure(t) for t in ts]
    if not all(units) or len(set(units)) != 1:
        return None
    requested = re.search(r'\bin ([a-z]+)\b',p.question)
    if not requested or _measure(requested.group(1)) != units[0]:
        return None
    state = re.search(r'\b(weight|mass|volume|length|height) to\s*$',p.body[:ns[0].start])
    if not state:
        return None
    token = tokenize(p)
    matches = list(re.finditer(r'Q\d+|\b(?:double[ds]?|triple[ds]?)\b',token))
    if not matches or matches[0].group() != 'Q0':
        return None
    value = Fraction(0)
    work = ''
    used = set()
    for m in matches:
        word = m.group()
        if word.startswith('Q'):
            i = int(word[1:])
            if i in used:
                return None
            used.add(i)
            if i:
                before = token[matches[matches.index(m)-1].end():m.start()]
                if not re.search(r'\badded (?:another )?$',before):
                    return None
                value += ns[i].value
                work = '('+work+' + '+format_number(ns[i].value)+')'
            else:
                value = ns[i].value
                work = format_number(value)
        else:
            local = token[max(0,m.start()-50):m.end()+50]
            if not has(r'\b'+state.group(1)+r'\b',local):
                return None
            factor = 2 if word.startswith('double') else 3
            value *= factor
            work = '('+work+' x '+str(factor)+')'
    if used != set(range(len(ns))) or len(matches)-len(ns) < 2:
        return None
    return result(value,work)


def _daily_group_and_loose(p):
    """Daily grouped measured servings plus a loose measured amount."""
    ns = p.numbers
    if len(ns) != 3 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\bevery day\b',p.body) or not has(r'\b(?:a|each|per) week\b',p.question):
        return None
    if has(r'\b(?:more|less|than|left|half|twice|not)\b',p.body):
        return None
    ts = tails(p)
    if ts[0].strip() or not re.match(r'-[a-z]+ [a-z]+(?: of [a-z]+)? plus\s*$',ts[1]):
        return None
    unit = _measure(ts[1])
    if not unit or _measure(ts[2]) != unit or not has(r'\b'+unit+r'(?:s|es)?\b',p.question):
        return None
    a,b,c = p.values
    return result((a*b+c)*7,'({} x {} + {}) x 7'.format(*map(format_number,(a,b,c))))


def _weekday_commute(p):
    """Two daily legs over an explicitly bounded weekday schedule."""
    if len(p.numbers) != 2 or any(n.start >= len(p.body) for n in p.numbers):
        return None
    days = ('monday','tuesday','wednesday','thursday','friday','saturday','sunday')
    text = p.text.lower()
    span = re.search(r'\bevery ('+'|'.join(days)+r') (?:to|through) ('+'|'.join(days)+r')\b',p.body)
    if not span or not has(r'\b(?:week|that week)\b',p.question):
        return None
    ts = tails(p)
    unit = _measure(ts[0])
    if not unit or _measure(ts[1]) != unit or not has(r'\b'+unit+r'(?:s|es)?\b',p.question):
        return None
    if not has(r'\b(?:to get to|to work|to school)\b',ts[0]) or not has(r'\b(?:home|back)\b',text[p.numbers[0].end:]):
        return None
    if has(r'\b(?:except|not|twice|more|less|than|per)\b',p.body):
        return None
    end = days.index(span.group(2))
    if not (has(r'\b'+days[end]+r'\b',p.question)
            or re.search(r'\bwhen [^.!?;]+ on '+days[end]+r',?\s*$',p.body)):
        return None
    count = (end-days.index(span.group(1)))%7+1
    return result(total(p.values)*count,'({}) x {}'.format(fmt(p.values),count))


def _day_referenced_events(p):
    """Two dated events and a third explicitly scaled from a named day."""
    if len(p.numbers) != 2 or any(n.start >= len(p.body) for n in p.numbers):
        return None
    token = tokenize(p)
    days = 'monday|tuesday|wednesday|thursday|friday|saturday|sunday'
    events = {}
    unit = None
    subjects = set()
    previous_subject = None
    for i,n in enumerate(p.numbers):
        before = token.split('Q'+str(i),1)[0]
        m = re.search(r'\b([a-z]+) (buys?|bought|sold|sells?|collected|found|made)\s*$',before)
        after = token.split('Q'+str(i),1)[1]
        label = re.match(r'\s+(?:more )?([a-z]+) on ('+days+r')\b',after)
        if not label or label.group(2) in events:
            return None
        if m:
            subject = m.group(1)
        elif i and previous_subject:
            bridge = p.text.lower()[p.numbers[i-1].end:n.start]
            if has(r'[.!?;]',bridge) or not has(r',|\band\b',bridge):
                return None
            subject = previous_subject
        else:
            return None
        u = _normal_unit(label.group(1))
        if unit and unit != u:
            return None
        unit = u
        events[label.group(2)] = n.value
        previous_subject = subject
        if subject not in ('he','she','they','it'):
            subjects.add(subject)
    if len(subjects) > 1:
        return None
    relation = re.search(r'\bon ('+days+r'),? ([a-z]+) (?:buys?|bought|sold|sells?|collected|found|made) '
                         r'(double|triple|twice) the number of '+re.escape(unit)+r'(?:s|es)? '
                         r'(?:he|she|they|it) (?:did|bought|sold|collected|found|made) on ('+days+r')\b',token)
    if not relation or relation.group(1) in events or relation.group(4) not in events:
        return None
    if not has(r'\b'+re.escape(unit)+r'(?:s|es)?\b',p.question):
        return None
    if not has(r'\b(?:have|total|sell|sold|altogether|collect|in all)\b',p.question):
        return None
    if relation.group(2) not in subjects | {'he','she','they','it'}:
        return None
    factor = 3 if relation.group(3) == 'triple' else 2
    base = events[relation.group(4)]
    return result(total(events.values())+factor*base,
                  '({}) + {} x {}'.format(fmt(events.values()),factor,format_number(base)))

def _lettered_category_total(p):
    """A counted set of letter-labelled containers linked by differences."""
    ns = p.numbers
    if not 4 <= len(ns) <= 12:
        return None
    token = tokenize(p)
    q = re.search(r'how many ([a-z ]+) are in all Q(\d+) ([a-z]+)\?',token)
    intro = re.match(r'Q0 ([a-z]+)\b',token)
    if not q or not intro or _normal_unit(q.group(3)) != _normal_unit(intro.group(1)):
        return None
    gi = int(q.group(2))
    if gi != len(ns)-1 or ns[gi].value != ns[0].value:
        return None
    group = _normal_unit(intro.group(1))
    noun = _group_label(q.group(1))
    if not noun:
        return None
    known = {}; edges = []; used = {0,gi}
    pattern = r'\b'+re.escape(group)+r' ([a-z]) has Q(\d+) (more |fewer |less )?([a-z ]+?)(?= than\b|[,.;?])'
    for m in re.finditer(pattern,token):
        label,index,direction,unit = m.groups()
        i = int(index)
        if i in used or i >= len(ns) or _group_label(unit) != noun:
            return None
        used.add(i)
        if direction:
            target = re.match(r' than '+re.escape(group)+r' ([a-z])\b',token[m.end():])
            if not target:
                return None
            edges.append((label,target.group(1),ns[i].value*(-1 if direction.strip() in ('fewer','less') else 1)))
        else:
            if label in known:
                return None
            known[label] = ns[i].value
    if used != set(range(len(ns))) or len(known) != 1:
        return None
    labels = set(known)
    for a,b,_ in edges:
        labels.update((a,b))
    if ns[0].value != len(labels) or len(edges) != len(labels)-1:
        return None
    for _ in range(len(labels)):
        for a,b,d in edges:
            if b in known and a not in known:
                known[a] = known[b]+d
            elif a in known and b not in known:
                known[b] = known[a]-d
            elif a in known and b in known and known[a] != known[b]+d:
                return None
    if set(known) != labels or min(known.values()) < 0:
        return None
    return result(total(known.values()),fmt(known.values()))

def solve(problem):
    for reader in (_lettered_category_total, _shared_group_contents, _separate_task_times,
                   _divided_quantity_measure, _mixed_measure_comparison,
                   _missing_labelled_average, _averaged_population_difference,
                   _labelled_group_totals, _labelled_count_chain, _rate_difference, _grouped_stages, _paired_durations,
                   _weekday_rates, _affine_total, _additional_work,
                   _average_completion, _share_after_removal, _group_plus_pairs,
                   _converted_measurements, _weekly_absences, _session_attendance,
                   _category_net_difference, _round_trip_saving, _serial_stages,
                   _time_rate_pairs, _cycle_time, _relative_rate_period,
                   _net_stock_change, _goal_time, _uncovered_rectangle,
                   _elapsed_stages, _compound_time_difference,
                   _excluded_weekdays, _measurement_difference,
                   _average_relative_measurement, _sequential_measure,
                   _daily_group_and_loose, _weekday_commute,
                   _day_referenced_events):
        value = reader(problem)
        if value is not None:
            return value
    return None
