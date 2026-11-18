"""Compose labelled contents, schedules and fully specified stock changes.

Labels come from the narrative.  Each reader must account for every quantity;
an unknown rate, ambiguous label or unsupported change causes abstention.
"""
import re
from fractions import Fraction

from ..numbers import format_number
from ._counting_common import answer, total, fmt, tokenize
from ._money_common import _singular
from .counting_and_totals_r02_a2 import _conversion


def has(pattern, text):
    return re.search(pattern, text) is not None


_STOP = set(('a an the of in on at for to from with by and or but as than '
             'is are was were has have had will would can could does do did '
             'each every per that which who his her their its he she they it '
             'makes make needs need requires require contains contain holds hold '
             'produces produce yields yield weighs weigh takes take bought '
             'left remaining total altogether combined now more less fewer '
             'long tall wide high deep late early before after during '
             'eat eats ate consumes consume consumed uses use used gets get '
             'bore bears bear want wants have been goes go weigh weighing '
             'keeps keep kept gives give gave sold sells sell costs cost '
             'daily weekly then herself himself themselves').split())
_STOP.update('this these those last next past same only also inside outside there another inflating'.split())
_STOP.update('burst bursts popped broken damaged respectively study studies watches watch watching takes took spends spent'.split())
_STOP.add('present')
_UNITS = {'ml': 'milliliter', 'litre': 'liter', 'oz': 'ounce', 'lb': 'pound', 'min':'minute',
          'm': 'meter', 'cm': 'centimeter', 'kg': 'kilogram'}
_TIME = {'second', 'minute', 'hour', 'day', 'week', 'month', 'year'}


def label(text):
    """A noun phrase, retaining modifiers needed to distinguish categories."""
    text = re.sub(r"\b([a-z]+)'s\b",r'\1',text)
    words = []
    for m in re.finditer(r'[a-z]+|[^\s-]', text.strip()):
        w = m.group()
        if not w.isalpha() or w in _STOP:
            break
        w = _UNITS.get(w, _singular(w))
        w = {'kid':'child'}.get(w,w)
        words.append(w)
        if w in _TIME or w in {'milliliter', 'liter', 'pound', 'ounce', 'inch', 'foot',
                               'meter','centimeter','kilometer','gram','kilogram','mile','gallon'}:
            break
        if len(words) > 4:
            return ''
    return ' '.join(words)


def compatible(a, b):
    return bool(a and b and (a == b or a.endswith(' '+b) or b.endswith(' '+a)))


def asked(p):
    m = re.match(r'how (?:many|much)\s+(?:(?:more|additional|total|remaining)\s+)?(.*)', p.question)
    if m:
        return label(m.group(1))
    m = re.search(r'(?:number|amount) of\s+(.*)', p.question)
    if m:
        return label(m.group(1))
    m = re.search(r'\bin (seconds?|minutes?|hours?)\b', p.question)
    return label(m.group(1)) if m else ''


def converted(v, source, dest):
    if compatible(source, dest):
        return v
    mass = {'pound': Fraction(16), 'ounce': Fraction(1)}
    if source in mass and dest in mass:
        return v*mass[source]/mass[dest]
    return _conversion(v, source, dest)


def _labelled_contents(p):
    """Expand a recipe graph, summing repeated counts of each category.

    Supports arbitrary numbers of categories, multiword category names and
    nested components.  Every defined recipe must actually be used.
    """
    if not 3 <= len(p.numbers) <= 16:
        return None
    t = tokenize(p)
    if has(r'\b(?:more|less|fewer|than|half|twice|double|percent|average|'
           r'left|remaining|lost|ate|eats?|sold|give|gave|except|rest)\b', t):
        return None
    if has(r'\b(?:some|gives?|gave|donates?|donated|sells?|sold|consumes?|'
           r'consumed|loses?|lost|removes?|removed)\b',p.body):
        return None  # A content graph does not yet describe stock changes.
    target = asked(p)
    if target in ('time','weight'):
        units = {label(p.text.lower()[n.end:]) for n in p.numbers}
        times = units & ({'hour','minute','second'} if target=='time' else {'pound','ounce','gram','kilogram'})
        target = next(iter(times)) if len(times)==1 else ''
    if not target:
        return None
    recipes, used = {}, set()

    def add(key, entries):
        if not key or key in recipes or not entries:
            return False
        recipes[key] = entries
        return True

    # Each category makes/needs N units, and optionally M other components.
    pat = (r'\beach ([a-z -]+?) (?:makes?|produces?|yields?|needs?|requires?|'
           r'has|have|contains?|holds?|is made of|is made up of|consists of)\s+'
           r'(Q\d+[^.!?;]*?)(?=,?\s*(?:and )?each\b|[.!?;]|$)')
    for m in re.finditer(pat, t[:t.lower().find(p.question)] if p.question in t else t):
        key = label(m.group(1))
        entries = []
        for k in re.finditer(r'Q(\d+)\s+([^Q]+)', m.group(2)):
            i, tail = int(k.group(1)), k.group(2)
            u = label(tail)
            if not u or i in used:
                return None
            entries.append((i, u, Fraction(1)))
            used.add(i)
        if not add(key, entries):
            return None
    # N material is needed to make one product.  An explicit batch size is
    # a denominator, rather than another stock entry.
    for m in re.finditer(r'Q(\d+) ([a-z -]+?) (?:are|is) (?:needed|required) to make Q(\d+) ([a-z -]+)', t):
        i, raw, j, key = m.groups()
        i, j = int(i), int(j)
        if i in used or j in used or p.numbers[j].value <= 0:
            return None
        if not add(label(key), [(i, label(raw), p.numbers[j].value)]):
            return None
        used.update((i, j))
    # Time to perform the same action on one member of each category.
    for m in re.finditer(r'Q(\d+) (seconds?|minutes?|hours?) to ([a-z]+) (?:a|an) ([a-z -]+)', t):
        i, u, verb, key = m.groups()
        i = int(i)
        if i in used or not add(label(key), [(i, label(u), Fraction(1))]):
            return None
        used.add(i)
    # Plural category subjects can state their own uniform contents.
    for m in re.finditer(r'(?:^|[.;,]\s*(?:whereas )?|\band\s+)\s*([a-z -]+?) have (?:only )?Q(\d+) ([a-z -]+?)(?=[.,;]| and [a-z -]+? have |$)',t):
        key,i,u=m.groups()
        i=int(i)
        if i in used:
            continue
        # Pronouns and named owners describe stocks, not category recipes.
        if key in ('they','we','you','i') or not key.endswith('s'):
            continue
        if not add(label(key),[(i,label(u),Fraction(1))]):
            return None
        used.add(i)
    for m in re.finditer(r'\bfor every ([a-z -]+?) there are Q(\d+) ([a-z -]+?)(?=[.,;]|$)',t):
        key,i,u=m.groups();i=int(i)
        if i in used or not add(label(key),[(i,label(u),Fraction(1))]):
            return None
        used.add(i)
    if not recipes:
        return None
    definitions = set(used)
    visited = set()

    def expand(key, trail):
        direct = converted(Fraction(1), key, target)
        if direct is not None:
            return direct
        candidates = [k for k in recipes if compatible(k, key)]
        if len(candidates) != 1 or candidates[0] in trail:
            raise ValueError('unknown or cyclic recipe')
        k = candidates[0]
        visited.add(k)
        return total(p.numbers[i].value / d * expand(u, trail | {k})
                     for i, u, d in recipes[k])

    terms = []
    for i, n in enumerate(p.numbers):
        if i in definitions:
            continue
        tail = p.text.lower()[n.end:p.numbers[i+1].start if i+1 < len(p.numbers) else len(p.text)]
        key = label(tail)
        possessive = re.match(r"\s*([a-z]+)'s\b",tail)
        if possessive:
            key = label(possessive.group(1))
        if converted(Fraction(1),key,target) is not None:
            return None  # Loose output stock needs its own inventory reader.
        # Counts in the query must be in a stated new scenario, e.g. time
        # needed to groom N animals; repeated reference counts abstain.
        if n.start >= len(p.body) and not has(r'\b(?:to|for)\b', p.question[:n.start-len(p.body)]):
            return None
        try:
            terms.append(n.value * expand(key, set()))
        except ValueError:
            return None
    if not terms or visited != set(recipes):
        return None
    return answer(total(terms), fmt(terms))


def _parallel_rates(p):
    """Explicit per-time outputs share a duration; late starts reduce it."""
    ns, t = p.numbers, p.text.lower()
    if not 3 <= len(ns) <= 10 or has(r'\b(?:more|less|than|half|twice|percent|average)\b', t):
        return None
    rates, durations, delays = [], [], {}
    target = asked(p)
    grammatical = {i for i,n in enumerate(ns) if n.value == 1
                   and has(r'\b[a-z]+est\s*$',t[:n.start])
                   and has(r'^\s+[a-z]+ing\b',t[n.end:])}
    for i, n in enumerate(ns):
        if i in grammatical:
            continue
        tail = t[n.end:ns[i+1].start if i+1 < len(ns) else len(t)]
        m = re.match(r'\s+([a-z -]+?)\s*(?:/|per |each |every |an? )(second|minute|hour|day|week)\b', tail)
        if m:
            u = label(m.group(1))
            factor = converted(Fraction(1), u, target)
            if factor is None:
                return None
            rates.append((i, n.value*factor, m.group(2)))
        elif re.match(r'\s+(seconds?|minutes?|hours?|days?|weeks?) late\b', tail):
            following = [j for j in range(i+1,len(ns)) if j not in grammatical]
            if not following:
                return None
            delays[following[0]] = (i, n.value, label(tail))
        elif label(tail) in _TIME:
            durations.append(i)
        else:
            return None
    if len(rates) < 2 or len(durations) != 1 or len(delays) > len(rates):
        return None
    d = durations[0]
    # A stock change or distinct rate scopes need another reader.
    if has(r'\b(?:evaporates?|dumps?|lost|remaining|left|stops?|breaks?|each of)\b', p.body):
        return None
    terms = []
    rate_ids = {i for i, _, _ in rates}
    if not set(delays) <= rate_ids:
        return None
    for i, v, u in rates:
        duration = converted(ns[d].value, label(t[ns[d].end:]), u)
        if duration is None:
            return None
        if i in delays:
            _, delay, delay_unit = delays[i]
            delay = converted(delay, delay_unit, u)
            if delay is None or delay > duration:
                return None
            duration -= delay
        terms.append(v*duration)
    return answer(total(terms), fmt(terms))


_DAYS = 'monday tuesday wednesday thursday friday saturday sunday'.split()


def _daily_progression(p):
    """Initial daily amount and fixed daily change through a named weekday."""
    ns, t = p.numbers, p.text.lower()
    if len(ns) != 2 or any(n.start >= len(p.body) for n in ns):
        return None
    a, d = ns
    if not has(r'\b(?:more|fewer|less)\b[^.;!?]*\beach day than the previous day\b', p.body):
        return None
    starts = [i for i, w in enumerate(_DAYS) if has(r'\bon (?:a |the )?'+w+r'\b', t[:d.start])]
    ends = [i for i, w in enumerate(_DAYS) if has(r'\b(?:by|through|until) '+w+r'\b', p.question)]
    if len(starts) != 1 or len(ends) != 1 or ends[0] < starts[0]:
        return None
    if not compatible(label(t[a.end:]), asked(p)):
        return None
    count = ends[0]-starts[0]+1
    delta = -d.value if has(r'^\s+(?:less|fewer)\b',t[d.end:]) else d.value
    if a.value+(count-1)*delta < 0:
        return None
    return answer(count*a.value+count*(count-1)*delta/2,
                  '{} x {} + {} x {} x {} / 2'.format(*map(format_number,(count,a.value,count,count-1,delta))))


def _weekday_multiplier(p):
    """Different weekday/weekend daily amounts, related by a factor."""
    ns, t = p.numbers, p.text.lower()
    if len(ns) not in (2,3) or not has(r'\b(?:a|one|per|each) week\b',p.question):
        return None
    a, b = ns[:2]
    if len(ns) == 3 and not (ns[2].start >= len(p.body) and ns[2].value == 1):
        return None
    if not has(r'\bweekdays\b',t[a.end:b.start]) or not has(r'\bweekend day\b',t[a.end:b.start]):
        return None
    if not has(r'^\s+times the (?:number|amount) of\b',t[b.end:]):
        return None
    if not compatible(label(t[a.end:]), asked(p)):
        return None
    return answer(a.value*(5+2*b.value), '{} x (5 + 2 x {})'.format(format_number(a.value),format_number(b.value)))


def _combined_ages(p):
    """Each stated person ages one year per elapsed year."""
    ns, t = p.numbers, p.text.lower()
    if not 3 <= len(ns) <= 7 or ns[-1].start < len(p.body):
        return None
    if not has(r'^how many years\b',p.question) or not has(r'\bcombined age\b',p.question):
        return None
    if has(r'\b(?:more|less|older|younger|times|twice|ago)\b',p.body):
        return None
    if any(not re.match(r'\s+years? old\b',t[n.end:]) for n in ns):
        return None
    ages = ns[:-1]
    # Each age must have a subject; a stated aggregate is not another person.
    if any(not has(r'\b[a-z]+ is\s*$',t[ns[i-1].end if i else 0:n.start]) for i,n in enumerate(ages)):
        return None
    return answer((ns[-1].value-total(n.value for n in ages))/len(ages),
                  '({} - ({})) / {}'.format(format_number(ns[-1].value),fmt(n.value for n in ages),len(ages)))


def _square_layers(p):
    """Square layers lose a fixed number of units per side at each level."""
    ns, t = p.numbers, p.text.lower()
    if len(ns) != 3 or any(n.start >= len(p.body) for n in ns):
        return None
    n, a, d = ns
    if not re.match(r'\s+(?:levels|layers)\b',t[n.end:]):
        return None
    if not has(r'\bbottom (?:level|layer) has\s*$',t[n.end:a.start]):
        return None
    if not has(r'\bper side\b',t[a.end:d.start]) or not has(r'\beach (?:level|layer) has\s*$',t[a.end:d.start]):
        return None
    if not has(r'^\s+less [a-z]+ per side than the (?:level|layer) below',t[d.end:]):
        return None
    if not compatible(label(t[a.end:]),asked(p)) or n.value.denominator != 1 or not 0 < n.value <= 1000:
        return None
    if a.value-(n.value-1)*d.value <= 0:
        return None
    vals = [(a.value-i*d.value)**2 for i in range(int(n.value))]
    return answer(total(vals),fmt(vals))


def _partitioned_contents(p):
    """N groups; K have A contents each, and the rest have B."""
    ns, t = p.numbers, p.text.lower()
    if len(ns) != 4 or any(n.start >= len(p.body) for n in ns):
        return None
    n,k,a,b = ns
    group = label(t[n.end:k.start])
    if not group or not has(r'^\s+of the [a-z ]+? have\s*$',t[k.end:a.start]):
        return None
    m = re.search(r'\bof the ([a-z ]+?) have\s*$',t[k.end:a.start])
    if not m or not compatible(group,label(m.group(1))):
        return None
    if not has(r'\band the rest have\s*$',t[a.end:b.start]):
        return None
    if not compatible(label(t[a.end:]),asked(p)) or not compatible(label(t[b.end:]),asked(p)) or k.value > n.value:
        return None
    return answer(k.value*a.value+(n.value-k.value)*b.value,
                  '{} x {} + ({} - {}) x {}'.format(*map(format_number,(k.value,a.value,n.value,k.value,b.value))))


def _repeated_growth_total(p):
    """Known counts repeat once at a stated multiple; include both periods."""
    ns, t = p.numbers, p.text.lower()
    if not 2 <= len(ns) <= 5 or any(n.start >= len(p.body) for n in ns):
        return None
    m = re.search(r'\b(doubled|tripled) the (?:number|amount) of\b',p.body)
    if not m or not has(r'\btotal\b.*\bso far\b',p.question):
        return None
    if has(r'\b(?:each|every|per|more|less|than|lost|left)\b',p.body):
        return None
    if any(n.end > m.start() or not compatible(label(t[n.end:]),asked(p)) for n in ns):
        return None
    s = total(n.value for n in ns)
    factor = 2 if m.group(1) == 'doubled' else 3
    return answer(s*(1+factor),'({}) x (1 + {})'.format(fmt(n.value for n in ns),factor))


def _owner_ledger(p):
    """A single owner's inventory with explicit additions and removals."""
    ns, t = p.numbers, p.text.lower()
    if not 3 <= len(ns) <= 10 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\b(?:left|remaining|now)\b',p.question):
        return None
    if has(r'\b(?:each|every|per|more|less|than|half|times|twice|percent|rest|some|pairs?|dozen)\b',p.body):
        return None
    start = re.search(r'\b([a-z]+) (?:has|had|bought|made|collected)\s*$',t[:ns[0].start])
    if not start:
        return None
    owner = start.group(1)
    u = label(t[ns[0].end:])
    if not compatible(u,asked(p)):
        return None
    plus = r'bought|buys?|received|found|collected|added'
    minus = r'ate|eats?|consumes?|consumed|uses?|used|takes?|took|lost|sold|gave away|removed'
    signs = [1]
    for i,n in enumerate(ns[1:],1):
        before = t[ns[i-1].end:n.start]
        m = re.search(r'\b([a-z]+) ('+plus+'|'+minus+r')(?: another| an additional)?\s*$',before)
        if m and m.group(1) == 'then' and not has(r'[.!?;]',before):
            m = re.search(r'\b('+plus+'|'+minus+r')\s*$',before)
            event, subject = m.group(1), owner
        else:
            event, subject = (m.group(2),m.group(1)) if m else ('','')
        if subject not in (owner,'he','she','they','it'):
            return None
        if not compatible(label(t[n.end:]),u):
            return None
        signs.append(1 if re.fullmatch(plus,event) else -1)
    if -1 not in signs:
        return None
    return answer(total(n.value*s for n,s in zip(ns,signs)),
                  format_number(ns[0].value)+''.join((' + ' if s>0 else ' - ')+format_number(n.value)
                                                     for n,s in zip(ns[1:],signs[1:])))


def _named_differences(p):
    """Solve an additive comparison graph, including an anchor in an if-clause."""
    ns, t = p.numbers, p.text.lower()
    if not 3 <= len(ns) <= 8 or has(r'\b(?:each|per|times|half|twice|percent|gave|lost|sold|ate)\b',t):
        return None
    edges, known, unit = [], {}, ''
    for i,n in enumerate(ns):
        before = t[ns[i-1].end if i else 0:n.start]
        m = re.search(r'\b([a-z]+) (?:has|had|owns?|collected)\s*$',before)
        if not m:
            return None
        owner = m.group(1)
        tail = t[n.end:ns[i+1].start if i+1<len(ns) else len(t)]
        rel = re.match(r'\s+(more|fewer|less) ([a-z -]+?) than ([a-z]+)\b',tail)
        u = label(rel.group(2)) if rel else label(tail)
        if not u or unit and not compatible(u,unit):
            return None
        unit = u
        if rel:
            delta = n.value*(1 if rel.group(1)=='more' else -1)
            edges.append((owner,rel.group(3),delta))
        elif owner not in known:
            known[owner] = n.value
        else:
            return None
    if len(known) != 1 or not edges or not compatible(asked(p),unit):
        return None
    for _ in edges:
        for a,b,d in edges:
            if b in known:
                if a in known and known[a] != known[b]+d:
                    return None
                known[a] = known[b]+d
            elif a in known:
                known[b] = known[a]-d
    if len(known) != len(edges)+1 or min(known.values())<0:
        return None
    if has(r'\b(?:together|combined|in all|total|altogether)\b',p.question):
        return answer(total(known.values()),fmt(known.values()))
    owners = [k for k in known if has(r'\b'+re.escape(k)+r'\b',p.question)]
    if len(owners) == 1:
        return answer(known[owners[0]],'Following the stated count differences')
    return None


def _parents_and_contents(p):
    """Count both containers/parents and their explicitly grouped contents."""
    ns, t = p.numbers, p.text.lower()
    if not 4 <= len(ns) <= 14 or len(ns)%2 or any(n.start >= len(p.body) for n in ns):
        return None
    terms, groups, contents = [], set(), set()
    for i in range(0,len(ns),2):
        a,b = ns[i:i+2]
        m = re.fullmatch(r'\s+([a-z -]+?) with\s*',t[a.end:b.start])
        tail = t[b.end:ns[i+2].start if i+2<len(ns) else len(p.body)]
        k = re.match(r'\s+([a-z -]+?) each\b',tail)
        if not m or not k:
            return None
        groups.add(label(m.group(1)))
        contents.add(label(k.group(1)))
        terms.append(a.value*(1+b.value))
    if len(groups)!=1 or len(contents)!=1 or groups==contents:
        return None
    a,b = next(iter(groups)), next(iter(contents))
    if not has(r'^how many '+re.escape(a)+r's? and '+re.escape(b)+r's?\b',p.question):
        return None
    return answer(total(terms),fmt(terms))


def _remaining_measure(p):
    """An initial mass distributed uniformly among pieces, some removed."""
    ns, t = p.numbers, p.text.lower()
    if len(ns)!=3 or any(n.start>=len(p.body) for n in ns):
        return None
    a,b,c = ns
    if not has(r'\bremaining\b',p.question):
        return None
    source, target = label(t[a.end:]), asked(p)
    if source not in ('pound','ounce','gram','kilogram','liter','milliliter'):
        return None
    v = converted(a.value,source,target)
    if v is None or not compatible(label(t[b.end:]),label(t[c.end:])):
        return None
    if not has(r'\b(?:ate|removed|sold|used|lost|gave away)\s*$',t[b.end:c.start]):
        return None
    if b.value<=0 or c.value>b.value:
        return None
    return answer(v*(b.value-c.value)/b.value,
                  '{} x ({} - {}) / {}'.format(*map(format_number,(v,b.value,c.value,b.value))))


def _mass_loads(p):
    """Category counts -> mass via explicit ratios -> whole capacity loads."""
    ns, t = p.numbers, p.text.lower()
    if not 7 <= len(ns) <= 13 or not has(r'^how many loads\b',p.question):
        return None
    if has(r'\b(?:more|less|than|half|twice|percent|left|remaining)\b',p.body):
        return None
    capacity = ns[0]
    u = label(t[capacity.end:])
    if u not in ('pound','ounce','gram','kilogram') or capacity.value<=0:
        return None
    rates, used = {}, {0}
    for i in range(1,len(ns)-1):
        a,b = ns[i:i+2]
        middle = t[a.end:b.start]
        m = re.fullmatch(r'\s+(?:pairs of )?([a-z -]+?) weighs?\s*',middle)
        if not m:
            continue
        key = label(m.group(1))
        mass = converted(b.value,label(t[b.end:]),u)
        if not key or key in rates or mass is None or a.value<=0 or i in used:
            return None
        rates[key] = mass/a.value
        used.update((i,i+1))
    if len(rates)<2:
        return None
    terms, seen = [],set()
    for i,n in enumerate(ns):
        if i in used:
            continue
        key = label(t[n.end:])
        if key not in rates:
            return None
        seen.add(key)
        terms.append(n.value*rates[key])
    if seen != set(rates):
        return None
    loads = total(terms)/capacity.value
    rounded = Fraction((loads.numerator+loads.denominator-1)//loads.denominator)
    return answer(rounded,'Round up ({}) / {}'.format(fmt(terms),format_number(capacity.value)))


def _relative_daily_time(p):
    """Two daily/nightly durations, the second a stated amount longer."""
    ns, t = p.numbers, p.text.lower()
    if len(ns)!=3 or ns[-1].start<len(p.body):
        return None
    a,d,w = ns
    u = label(t[a.end:])
    if u not in ('hour','minute') or label(t[d.end:])!=u or w.value<=0:
        return None
    if not has(r'\b(?:at night|each day|every day|per day)\b',p.body):
        return None
    if not re.match(r'\s+(?:hours?|minutes?) more\b',t[d.end:]):
        return None
    if not has(r'\bboth\b',p.question) or not has(r'how much time|how long',p.question):
        return None
    days = converted(w.value,label(t[w.end:]),'day')
    if days is None:
        return None
    return answer((2*a.value+d.value)*days,'(2 x {} + {}) x {}'.format(*map(format_number,(a.value,d.value,days))))


def _measure_comparisons(p):
    """Named measurement differences and equalities, summed or averaged."""
    ns,t = p.numbers,p.text.lower()
    if not 3 <= len(ns) <= 7 or not has(r'\b(?:average|total|combined|number)\b',p.question):
        return None
    if has(r'\b(?:each|per|times|half|twice|percent|gave|lost|sold|ate)\b',t):
        return None
    known, edges, refs = {}, [], []
    unit, previous_ref = '', ''
    for i,n in enumerate(ns):
        if n.start>=len(p.body) and re.match(r'\s*(?:[?.]|(?:people|persons|towns|friends)\b)',t[n.end:]):
            refs.append(n.value)
            continue
        before = p.text[ns[i-1].end if i else 0:n.start]
        subject = re.search(r'\b([A-Z][a-z]*(?: [A-Z][a-z]*)*) (?:is|was|has|had|weighs?|weighed)\s*$',before)
        if subject:
            owner = re.sub(r'^(?:if|then|and|since) ', '', subject.group(1).lower())
        elif has(r'\bwho (?:is|was)\s*$',before) and previous_ref:
            owner = previous_ref
        else:
            return None
        tail = t[n.end:ns[i+1].start if i+1<len(ns) else len(t)]
        rel = re.match(r'\s+(?:(more|less|fewer) ([a-z -]+?)|([a-z -]+?) (heavier|lighter|taller|shorter)) than ([a-z ]+?)(?=[,.;?]| and |$)',tail)
        u = label((rel.group(2) or rel.group(3))) if rel else label(tail)
        if not u or unit and not compatible(unit,u):
            return None
        unit=u
        if rel:
            sign = 1 if (rel.group(1) or rel.group(4)) in ('more','heavier','taller') else -1
            ref=rel.group(5).strip()
            edges.append((owner,ref,sign*n.value))
            previous_ref=ref
        else:
            if owner in known:
                return None
            known[owner]=n.value
            eq = re.search(r'\b(?:has|have) the same (?:height|weight|number) as ([a-z ]+?)(?=[,.;?]|$)',tail)
            if eq:
                edges.append((owner,eq.group(1).strip(),Fraction(0)))
    if len(known)!=1 or not edges:
        return None
    for _ in edges:
        for a,b,d in edges:
            if a in known:
                if b in known and known[b]!=known[a]-d:
                    return None
                known[b]=known[a]-d
            elif b in known:
                known[a]=known[b]+d
    if len(known)!=len(edges)+1 or any(v!=len(known) for v in refs) or min(known.values())<0:
        return None
    requested=asked(p)
    if requested and not compatible(requested,unit):
        return None
    if not requested:
        weight=has(r'\baverage weight\b',p.question) and unit in ('pound','ounce','gram','kilogram')
        height=has(r'\baverage height\b',p.question) and unit in ('inch','foot','centimeter','meter')
        if not weight and not height:
            return None
    result=total(known.values())
    work=fmt(known.values())
    if has(r'\baverage\b',p.question):
        result/=len(known)
        work='('+work+') / '+str(len(known))
    return answer(result,work)


def _ratio_difference(p):
    """A population partitioned by a ratio; ask for the count difference."""
    ns,t = p.numbers,tokenize(p)
    if len(ns)!=3 or not has(r'\bratio of [a-z ]+ is Q1\s*:\s*Q2\b',t):
        return None
    if not has(r'^how many more\b.*\bthan\b',p.question):
        return None
    if has(r'\b(?:gave|lost|sold|ate|half|percent|twice)\b',p.body) or ns[1].value+ns[2].value<=0:
        return None
    a,b,c=p.values
    return answer(a*abs(b-c)/(b+c),'{} x |{} - {}| / ({} + {})'.format(*map(format_number,(a,b,c,b,c))))


def _ratio_transfer(p):
    """Partition a stock among named recipients, then transfer one share."""
    ns,t=p.numbers,tokenize(p)
    m=re.search(r'\bbetween ([a-z ,]+?) in the ratio (Q\d+(?:\s*:\s*Q\d+)+) respectively',t)
    if not m:
        return None
    names=[w.strip() for w in re.split(r',\s*|\s+and\s+',m.group(1)) if w.strip()]
    ids=[int(i) for i in re.findall(r'Q(\d+)',m.group(2))]
    if ids!=list(range(1,len(ns)-1)) or len(names)!=len(ids) or len(set(names))!=len(names):
        return None
    f=len(ns)-1
    move=re.search(r'\b([a-z]+) gave ([a-z]+) Q'+str(f)+r' of (?:his|her|their) own share',t)
    if not move or not 0<=ns[f].value<=1:
        return None
    source,dest=move.groups()
    query=re.search(r'\bdoes ([a-z]+) now have\b',p.question)
    if not query or source not in names or dest not in names or source==dest or query.group(1) not in (source,dest):
        return None
    if not compatible(label(p.text.lower()[ns[0].end:]),asked(p)):
        return None
    parts=total(ns[i].value for i in ids)
    if parts<=0:
        return None
    shares={name:ns[0].value*ns[i].value/parts for name,i in zip(names,ids)}
    transfer=shares[source]*ns[f].value
    shares[source]-=transfer
    shares[dest]+=transfer
    return answer(shares[query.group(1)],'Divide the stock by the ratio and transfer the stated fraction')


def _mixed_time_budget(p):
    """A mixed-unit total duration less mixed-unit activity durations."""
    ns,t=p.numbers,p.text.lower()
    if not 4<=len(ns)<=14 or not has(r'\b(?:left|remaining)\b',p.question):
        return None
    target=asked(p)
    if target not in ('hour','minute','second') or has(r'\b(?:each|per|every|more|less|than|half|twice)\b',p.body):
        return None
    if not has(r'\b(?:flight|trip|journey|shift|break)\b',t[:ns[0].start]):
        return None
    budget,spent=Fraction(0),Fraction(0)
    in_budget=True
    for i,n in enumerate(ns):
        if n.start>=len(p.body):
            return None
        before=t[ns[i-1].end if i else 0:n.start]
        if has(r'\b(?:spends?|spent)\b',before):
            in_budget=False
        u=label(t[n.end:])
        value=converted(n.value,u,target)
        if value is None:
            # Counts of tasks are descriptions of the preceding duration.
            if i and has(r'\b(?:watching|reading|playing)\s*$',before) and u not in _TIME:
                continue
            return None
        if in_budget:
            budget+=value
        else:
            spent+=value
    if budget<=0 or spent<=0:
        return None
    return answer(budget-spent,'{} - {}'.format(format_number(budget),format_number(spent)))


def _fill_and_drain(p):
    """Full reservoir, empty/fill times, and a common elapsed duration."""
    ns,t=p.numbers,p.text.lower()
    if len(ns)!=4 or not has(r'\b(?:left|remaining)\b',p.question):
        return None
    empty,fill,stock,elapsed=ns
    if not has(r'\bempty\b[^.;]*\bin\s*$',t[:empty.start]):
        return None
    if not has(r'\bfill\b[^.;]*\bin\s*$',t[empty.end:fill.start]):
        return None
    material = re.match(r'\s+[a-z]+ of ([a-z -]+)',t[stock.end:])
    matched = compatible(label(t[stock.end:]),asked(p)) or bool(material and compatible(label(material.group(1)),asked(p)))
    if not has(r'\bstarts? (?:filled|full)\b',p.body) or not matched:
        return None
    eu=label(t[empty.end:])
    ftime=converted(fill.value,label(t[fill.end:]),eu)
    duration=converted(elapsed.value,label(t[elapsed.end:]),eu)
    if ftime is None or duration is None or empty.value<=0 or ftime<=0:
        return None
    value=stock.value*(1+duration/ftime-duration/empty.value)
    if value>stock.value:
        return None  # Overflow needs its own capacity reasoning.
    return answer(value,'{} x (1 + {} / {} - {} / {})'.format(*map(format_number,(stock.value,duration,ftime,duration,empty.value))))


def _grouped_resource_output(p):
    """Sum purchases in groups, then divide by the input needed per product."""
    ns,t=p.numbers,tokenize(p)
    if not 6<=len(ns)<=14:
        return None
    r=len(ns)-2
    conversion=re.search(r'Q'+str(r)+r' ([a-z -]+?) (?:are|is) used to make Q'+str(r+1)+r' ([a-z -]+)',t)
    if not conversion or r%2 or ns[r].value<=0:
        return None
    material,product=label(conversion.group(1)),label(conversion.group(2))
    if not compatible(product,asked(p)):
        return None
    vals=[]
    for i in range(0,r,2):
        a,b=ns[i:i+2]
        middle=p.text.lower()[a.end:b.start]
        if not re.fullmatch(r'\s+[a-z -]+? of\s*',middle) or not compatible(label(p.text.lower()[b.end:]),material):
            return None
        vals.append(a.value*b.value)
    return answer(total(vals)*ns[r+1].value/ns[r].value,
                  '({}) x {} / {}'.format(fmt(vals),format_number(ns[r+1].value),format_number(ns[r].value)))


def _exception_contents(p):
    """Two container types partition a known whole at different capacities."""
    ns,t=p.numbers,tokenize(p)
    if len(ns)!=4 or not has(r'\b(?:total|in all|altogether)\b',p.question):
        return None
    whole,regular,special,count=ns
    m=re.search(r'\b([a-z]+) ([a-z]+)s? have Q1 ([a-z]+)',t)
    k=re.search(r'\b([a-z]+) ([a-z]+)s? have (?:only )?Q2 ([a-z]+)',t)
    if not m or not k or m.group(1)==k.group(1) or not compatible(label(m.group(2)),label(k.group(2))):
        return None
    if not compatible(label(m.group(3)),asked(p)) or not compatible(label(k.group(3)),asked(p)):
        return None
    if not compatible(label(p.text.lower()[whole.end:]),label(m.group(2))):
        return None
    assignment=re.search(r'Q3 ([a-z]+)s? are (?:assigned|reserved|used) for ([a-z]+)',t)
    if not assignment or assignment.group(2)!=k.group(1) or count.value>whole.value:
        return None
    return answer((whole.value-count.value)*regular.value+count.value*special.value,
                  '({} - {}) x {} + {} x {}'.format(*map(format_number,(whole.value,count.value,regular.value,count.value,special.value))))


def _daily_category_losses(p):
    """Several initial categories each have an explicit daily loss."""
    ns,t=p.numbers,p.text.lower()
    if len(ns)<4 or len(ns)%2 or any(n.start>=len(p.body) for n in ns):
        return None
    mid=len(ns)//2
    if not has(r'\b(?:every|each|per) day\b',t[ns[mid-1].end:ns[mid].start]):
        return None
    if not has(r'\b(?:lost|loses?|removed|used|uses?|ate|eats?)\s*$',t[ns[mid-1].end:ns[mid].start]):
        return None
    if not has(r'\b(?:a|one) week\b',t[ns[-1].end:]) or not has(r'\bleft\b',p.question):
        return None
    keys=[label(t[n.end:]) for n in ns]
    if not all(keys) or len(set(keys[:mid]))!=mid or keys[:mid]!=keys[mid:]:
        return None
    remaining=[a.value-7*b.value for a,b in zip(ns[:mid],ns[mid:])]
    if min(remaining)<0:
        return None
    selected=[i for i,k in enumerate(keys[:mid]) if compatible(k,asked(p))]
    if selected:
        return answer(total(remaining[i] for i in selected),fmt(remaining[i] for i in selected))
    if not has(r'\b(?:left|remaining) in\b',p.question):
        return None
    return answer(total(remaining),fmt(remaining))


def _repeated_route(p):
    """A fixed circuit repeated morning and afternoon on each day of a week."""
    ns,t=p.numbers,p.text.lower()
    if len(ns)!=3 or any(n.start>=len(p.body) for n in ns):
        return None
    distance,a,b=ns
    if not compatible(label(t[distance.end:]),asked(p)) or not has(r'\b(?:circuit|loop|lap)\b',t[:distance.start]):
        return None
    if not has(r'^\s+times in the morning\b',t[a.end:]) or not has(r'^\s+times in the afternoon\b',t[b.end:]):
        return None
    if not has(r'\b(?:a|one) week\b',p.question):
        return None
    return answer(distance.value*(a.value+b.value)*7,'{} x ({} + {}) x 7'.format(*map(format_number,p.values)))


def _weekly_consumption(p):
    """Weekly grouped supply minus explicitly daily morning/night usage."""
    ns,t=p.numbers,p.text.lower()
    if len(ns)!=4 or any(n.start>=len(p.body) for n in ns):
        return None
    stock,a,b,rate=ns
    if not has(r'\b(?:not being eaten|left|remaining|uneaten)\b',p.question) or not has(r'\b(?:each|every|per|a) week\b',p.question):
        return None
    if not has(r'\b(?:each|every|per|a) week\b',t[stock.end:a.start]):
        return None
    if not has(r'^\s+[a-z]+ every morning\b',t[a.end:]) or not has(r'^\s+[a-z]+ every night\b',t[b.end:]):
        return None
    group=label(t[stock.end:])
    m=re.search(r'\beach ([a-z]+) has\s*$',t[b.end:rate.start])
    if not m or not compatible(group,label(m.group(1))):
        return None
    if not all(compatible(label(t[n.end:]),asked(p)) for n in (a,b,rate)):
        return None
    if not has(r'\beat\s*$',t[stock.end:a.start]) or not has(r'\beat\s*$',t[a.end:b.start]):
        return None
    return answer(stock.value*rate.value-7*(a.value+b.value),
                  '{} x {} - 7 x ({} + {})'.format(*map(format_number,(stock.value,rate.value,a.value,b.value))))


def _weekly_opening_hours(p):
    """Explicit weekday and weekend opening/closing clock times."""
    ns,t=p.numbers,p.text.lower()
    if len(ns)!=4 or any(n.start>=len(p.body) for n in ns) or asked(p)!='hour':
        return None
    if not has(r'\b(?:a|one|per|each) week\b',p.question):
        return None
    if not has(r'\bmonday through friday\b',p.body) or not has(r'\bon weekends\b',p.body):
        return None
    hours=[]
    for n in ns:
        m=re.match(r'\s*(am|pm|a|p)\b',t[n.end:])
        if not m or not 1<=n.value<=12:
            return None
        hours.append(n.value%12+(12 if m.group(1).startswith('p') else 0))
    a,b,c,d=hours
    return answer(5*((b-a)%24)+2*((d-c)%24),
                  '5 x {} + 2 x {}'.format(format_number((b-a)%24),format_number((d-c)%24)))


def _group_pair_totals(p):
    """Explicit independent count/content pairs, optionally a whole or loss."""
    ns,t=p.numbers,p.text.lower()
    if not 4<=len(ns)<=14 or has(r'\b(?:times|twice|half|percent|than|average)\b',p.body):
        return None
    target=asked(p)
    if not target and has(r'\btotal capacity\b',p.question):
        units={label(t[n.end:]) for n in ns}
        target='person' if 'person' in units else ''
    if not target:
        return None
    terms,used,groups={},set(),[]
    for i in range(len(ns)-1):
        if i in used:
            continue
        a,b=ns[i:i+2]
        middle=t[a.end:b.start]
        tail=t[b.end:ns[i+2].start if i+2<len(ns) else len(t)]
        direct=re.fullmatch(r'\s+([a-z -]+?)(?: of [a-z -]+?)? (?:with|containing)\s*',middle)
        direct=direct or re.fullmatch(r'\s+([a-z -]+?) (?:that )?(?:bought|buy|buys|have|has|hold|holds|seat|seats)\s*',middle)
        if direct and has(r'\beach\b',tail) and compatible(label(tail),target):
            terms[i]=a.value*b.value
            groups.append((a.value,label(direct.group(1))))
            used.update((i,i+1))
            continue
        # N bags ... M items in each bag, retaining local bag identity.
        if has(r'\bwith\s*$',middle) and has(r'\bin each [a-z]+\b',tail) and compatible(label(tail),target):
            m=re.search(r'\bin each ([a-z]+)\b',tail)
            if compatible(label(middle),label(m.group(1))):
                terms[i]=a.value*b.value
                used.update((i,i+1))
                groups.append((a.value,label(m.group(1))))
                continue
        # Counts of duration-adjective tasks: N D-minute songs.
        if not middle.strip() and re.match(r'-(?:seconds?|minutes?|hours?)\b',tail):
            u=label(tail.lstrip('-'))
            v=converted(b.value,u,target)
            if v is not None:
                terms[i]=a.value*v
                used.update((i,i+1))
                continue
        # A packing instruction: C contents in N containers.
        if compatible(label(middle),target) and has(r'\bin\s*$',middle):
            prefix=t[ns[i-1].end if i else 0:a.start]
            if has(r'\bpacks?\s*$',prefix) and label(tail):
                terms[i]=a.value*b.value
                used.update((i,i+1))
    if len(terms)<2:
        return None
    result=total(terms.values())
    extras=[i for i in range(len(ns)) if i not in used]
    for i in extras:
        n=ns[i]
        u=label(t[n.end:])
        same_groups = groups and (all(compatible(u,k) for _,k in groups)
                                  or u=='person' and all(k in ('customer','person') for _,k in groups))
        if same_groups and i==0 and n.value==total(v for v,_ in groups):
            continue  # Explicit total of the following disjoint subgroups.
        before=t[ns[i-1].end if i else 0:n.start]
        tail=t[n.end:ns[i+1].start if i+1<len(ns) else len(t)]
        if not compatible(u,target):
            return None
        if has(r'\b(?:left|remaining|more minutes)\b',p.question) and has(r'\b(?:has|have|had|takes)\s*$',before):
            if len(extras)!=1:
                return None
            return answer(n.value-result,'{} - ({})'.format(format_number(n.value),fmt(terms.values())))
        if has(r'\b(?:burst|popped|broken|lost)\b',tail) or has(r'\b(?:lost|ate|used|removed)\s*$',before):
            if not has(r'\b(?:left|remaining|now)\b',p.question):
                return None
            result-=n.value
        else:
            return None
    if not extras and not has(r'\b(?:total|in all|altogether|sold|uses?|gets?|filled)\b',p.question):
        return None
    return answer(result,fmt(terms.values())+(' minus the stated losses' if extras else ''))


def _weekday_rates(p):
    """Explicit weekday/weekend daily quantities, with duration or capacity."""
    ns,t=p.numbers,p.text.lower()
    if not 3<=len(ns)<=5:
        return None
    a,b=ns[:2]
    if not has(r'\bweekdays\b',t[a.end:b.start]) or not has(r'\bweekend',t[b.end:ns[2].start]):
        return None
    unit=label(t[a.end:])
    other=label(t[b.end:])
    if not unit or not other or unit.split()[-1]!=other.split()[-1]:
        return None
    weekly=5*a.value+2*b.value
    if len(ns)==3 and has(r'^how many weeks\b',p.question):
        if not compatible(unit,label(t[ns[2].end:])) or weekly<=0 or not has(r'\bin total\b',p.body):
            return None
        return answer(ns[2].value/weekly,'{} / (5 x {} + 2 x {})'.format(*map(format_number,(ns[2].value,a.value,b.value))))
    if len(ns)==4:
        capacity,span=ns[2:]
        m=re.search(r'\beach ([a-z]+) has room for\s*$',t[b.end:capacity.start])
        if not m or not compatible(label(m.group(1)),unit) or not compatible(label(t[capacity.end:]),asked(p)):
            return None
        if label(t[span.end:])!='week':
            return None
        return answer(weekly*capacity.value*span.value,
                      '(5 x {} + 2 x {}) x {} x {}'.format(*map(format_number,(a.value,b.value,capacity.value,span.value))))
    return None


def _named_week_schedule(p):
    """Weekday daily amount and separately stated Saturday/Sunday amounts."""
    ns,t=p.numbers,p.text.lower()
    if len(ns)!=4 or any(n.start>=len(p.body) for n in ns):
        return None
    span,a,b,c=ns
    if label(t[span.end:])!='week' or not has(r'\bweekdays\b',t[span.end:a.start]):
        return None
    if not has(r'\ba day\b',t[a.end:b.start]) or not has(r'\bon saturday\b',t[b.end:c.start]) or not has(r'\bon sunday\b',t[c.end:]):
        return None
    u=label(t[a.end:])
    if u not in ('hour','minute') or any(label(t[n.end:])!=u for n in (b,c)):
        return None
    if not has(r'how much time|how long',p.question) and asked(p)!=u:
        return None
    return answer(span.value*(5*a.value+b.value+c.value),
                  '{} x (5 x {} + {} + {})'.format(*map(format_number,(span.value,a.value,b.value,c.value))))


def _progressive_daily_total(p):
    """First-day quantity, then a fixed increment; ask for a week's total."""
    ns,t=p.numbers,p.text.lower()
    if len(ns)!=2 or any(n.start>=len(p.body) for n in ns):
        return None
    a,d=ns
    if not has(r'\bfirst day\b',t[:a.start]) or not has(r'\beach day\b',t[a.end:d.start]):
        return None
    if not has(r'^\s+more [a-z -]+? than the previous day\b',t[d.end:]):
        return None
    if not has(r'\b(?:a|one) week\b',p.question) or not compatible(label(t[a.end:]),asked(p)):
        return None
    return answer(7*a.value+21*d.value,'7 x {} + 21 x {}'.format(format_number(a.value),format_number(d.value)))


def _periodic_doubling(p):
    """A count doubles at an explicit interval, for a whole number of cycles."""
    ns,t=p.numbers,p.text.lower()
    if len(ns)!=3 or ns[-1].start<len(p.body):
        return None
    interval,start,end=ns
    if not has(r'\bevery\s*$',t[:interval.start]) or not has(r'\bdoubles\b',t[interval.end:start.start]):
        return None
    cycles=converted(end.value,label(t[end.end:]),label(t[interval.end:]))
    if cycles is None or interval.value<=0 or not compatible(label(t[start.end:]),asked(p)):
        return None
    cycles/=interval.value
    if cycles.denominator!=1 or not 0<=cycles<=1000:
        return None
    return answer(start.value*2**int(cycles),'{} x 2^{}'.format(format_number(start.value),format_number(cycles)))


def _weighted_rating(p):
    """A total review count and explicit counts at each numeric rating."""
    ns,t=p.numbers,tokenize(p)
    if not 5<=len(ns)<=15 or len(ns)%2!=1 or not has(r'\baverage\b',p.question):
        return None
    if not has(r'\b(?:rating|reviews?)\b',p.question):
        return None
    terms,counts=[],[]
    for i in range(1,len(ns),2):
        if not re.search(r'Q'+str(i)+r' Q'+str(i+1)+r'-star reviews?\b',t):
            return None
        counts.append(ns[i].value)
        terms.append(ns[i].value*ns[i+1].value)
    if total(counts)!=ns[0].value or ns[0].value<=0:
        return None
    return answer(total(terms)/ns[0].value,'({}) / {}'.format(fmt(terms),format_number(ns[0].value)))


def _residual_groups(p):
    """A total number of groups, explicit subgroups, then a remaining type."""
    ns,t=p.numbers,p.text.lower()
    if not 6<=len(ns)<=12 or len(ns)%2 or any(n.start>=len(p.body) for n in ns):
        return None
    whole=ns[0]
    group=label(t[whole.end:])
    if not group or not has(r'\b(?:in all|total|altogether)\b',p.question):
        return None
    counts,terms,outputs=[],[],set()
    for i in range(1,len(ns)-1,2):
        a,b=ns[i:i+2]
        m=re.fullmatch(r'\s+([a-z -]+?) (?:own|owns|have|has|hold|holds|contain|contains)\s*',t[a.end:b.start])
        if not m or not compatible(label(m.group(1)),group):
            return None
        counts.append(a.value)
        terms.append(a.value*b.value)
        outputs.add(label(t[b.end:]))
    rate=ns[-1]
    before=t[ns[-2].end:rate.start]
    m=re.search(r'\b(?:the )?remaining ([a-z -]+?) (?:own|owns|have|has|hold|holds|contain|contains)\s*$',before)
    if not m or not compatible(label(m.group(1)),group) or total(counts)>whole.value:
        return None
    outputs.add(label(t[rate.end:]))
    if not all(u and has(r'\b'+re.escape(u)+r's?\b',p.question) for u in outputs):
        return None
    terms.append((whole.value-total(counts))*rate.value)
    return answer(total(terms),fmt(terms))


def _fraction_subgroup_complement(p):
    """A complementary population and a complementary subset of that group."""
    ns,t=p.numbers,p.text.lower()
    if len(ns)!=3 or any(n.start>=len(p.body) for n in ns):
        return None
    n,f,g=ns
    if not 0<f.value<1 or not 0<g.value<1:
        return None
    m=re.search(r'\bthe rest are ([a-z]+)\b',t[f.end:g.start])
    if not m or not has(r'^\s+of the '+re.escape(m.group(1))+r' are\b',t[g.end:]):
        return None
    group=m.group(1)
    state=re.match(r'\s+of the [a-z]+ are ([a-z]+)',t[g.end:]).group(1)
    query=re.match(r'how many '+re.escape(group)+r' are (?:not )?([a-z]+)',p.question)
    if not query:
        return None
    opposite={'standing':'seated','seated':'standing','present':'absent','absent':'present'}
    if query.group(1)==state and not has(r'\bnot\b',p.question):
        value=n.value*(1-f.value)*g.value
    elif query.group(1)==opposite.get(state) or query.group(1)==state and has(r'\bnot\b',p.question):
        value=n.value*(1-f.value)*(1-g.value)
    else:
        return None
    return answer(value,'Apply the stated population fractions and their complements')


def _two_speed_journey(p):
    """Travel D at one speed for T, then the remainder at another speed."""
    ns,t=p.numbers,p.text.lower()
    if len(ns)!=4 or not has(r'^how long\b',p.question):
        return None
    distance,speed,duration,slow=ns
    if label(t[distance.end:])!='mile' or not re.match(r'\s+mph\b',t[speed.end:]) or not re.match(r'\s+mph\b',t[slow.end:]):
        return None
    if not has(r'\bfor\s*$',t[speed.end:duration.start]) or label(t[duration.end:])!='hour':
        return None
    if not has(r'\buntil\b',t[slow.end:]) or min(speed.value,slow.value)<=0:
        return None
    remainder=distance.value-speed.value*duration.value
    if remainder<0:
        return None
    return answer(duration.value+remainder/slow.value,'{} + ({} - {} x {}) / {}'.format(*map(format_number,(duration.value,distance.value,speed.value,duration.value,slow.value))))


def _detour_return(p):
    """An out-and-back detour at the trip's stated constant speed."""
    ns,t=p.numbers,p.text.lower()
    if len(ns)!=3 or not has(r'^how long\b',p.question):
        return None
    distance,duration,extra=ns
    if label(t[distance.end:])!='mile' or label(t[duration.end:])!='hour' or label(t[extra.end:])!='mile':
        return None
    if not has(r'\bout of the way\b.*\bget back on track\b',p.body) or not has(r'\bsame speed\b',p.question) or distance.value<=0:
        return None
    return answer(duration.value*(distance.value+2*extra.value)/distance.value,
                  '{} x ({} + 2 x {}) / {}'.format(*map(format_number,(duration.value,distance.value,extra.value,distance.value))))


def _group_fraction_removal(p):
    """Two named ratio shares, then an absolute withdrawal from one share."""
    ns,t=p.numbers,tokenize(p)
    if len(ns)!=4:
        return None
    m=re.search(r'\bbetween ([a-z]+) and ([a-z]+) in the ratio Q1\s*:\s*Q2',t)
    event=re.search(r'\b([a-z]+) decided to give Q3\b',t)
    query=re.search(r'\bdoes ([a-z]+) have now\b',p.question)
    if not m or not event or not query or event.group(1)!=query.group(1):
        return None
    names=m.groups()
    if event.group(1) not in names or ns[1].value+ns[2].value<=0:
        return None
    index=1+names.index(event.group(1))
    share=ns[0].value*ns[index].value/(ns[1].value+ns[2].value)
    return answer(share-ns[3].value,'{} - {}'.format(format_number(share),format_number(ns[3].value)))


def _calendar_duration_sum(p):
    """Separate durations on explicit sets/ranges of weekdays, repeated weekly."""
    ns,t=p.numbers,p.text.lower()
    if not 3<=len(ns)<=7 or has(r'\b(?:more|less|than|half|twice|break|late)\b',t):
        return None
    spans=[i for i,n in enumerate(ns) if label(t[n.end:])=='week']
    if len(spans)!=1:
        return None
    span=spans[0]
    target=asked(p)
    if target in ('time','sleep') or not target and has(r'\b(?:sleep|study)\b',p.question):
        target='hour'
    if target not in ('second','minute','hour'):
        return None
    terms,seen=[],set()
    for i,n in enumerate(ns):
        if i==span:
            continue
        value=converted(n.value,label(t[n.end:]),target)
        if value is None:
            return None
        # Calendar scope is local to this numeric sentence/clause.
        boundaries=list(re.finditer(r'[.;!?]|\band on\b',t))
        starts=[m.end() for m in boundaries if m.end()<=n.start]
        ends=[m.start() for m in boundaries if m.start()>=n.end]
        start=max(starts) if starts else 0
        end=min(ends) if ends else len(p.body)
        sentence=t[start:end]
        if len([k for j,k in enumerate(ns) if j!=span and start<=k.start<end])!=1:
            return None
        days={d for d in _DAYS if has(r'\b'+d+r's?\b',sentence)}
        r=re.search(r'\b('+ '|'.join(_DAYS)+r') (?:to|through) ('+'|'.join(_DAYS)+r')\b',sentence)
        if r:
            a,b=_DAYS.index(r.group(1)),_DAYS.index(r.group(2))
            days={_DAYS[(a+j)%7] for j in range((b-a)%7+1)}
        if not days:
            return None
        # Two distinct daily activities may share weekdays (sleep and naps).
        terms.append(value*len(days))
        seen.update(days)
    if len(terms)<2:
        return None
    return answer(total(terms)*ns[span].value,
                  '({}) x {}'.format(fmt(terms),format_number(ns[span].value)))


def _weekday_nights(p):
    """Explicit nights per week plus a daily weekend duration."""
    ns,t=p.numbers,p.text.lower()
    if len(ns)!=4:
        return None
    a,n,b,w=ns
    if label(t[a.end:])!='hour' or not has(r'\bper night\s*$',t[a.end:n.start]):
        return None
    if not re.match(r'\s+nights a week\b',t[n.end:]) or not has(r'\bon the weekends\b',t[n.end:b.start]):
        return None
    if not re.match(r'\s+hours a day\b',t[b.end:]) or label(t[w.end:])!='week':
        return None
    if n.value!=5 or not has(r'how much time|how long|how many hours',p.question):
        return None
    return answer((a.value*n.value+2*b.value)*w.value,
                  '({} x {} + 2 x {}) x {}'.format(*map(format_number,(a.value,n.value,b.value,w.value))))


def _polygon_sides(p):
    """Count sides of named polygons; one drawn line may represent a side."""
    ns,t=p.numbers,p.text.lower()
    if not 2<=len(ns)<=12 or not has(r'^how many (?:sides|lines)\b',p.question):
        return None
    if has(r'\blines\b',p.question) and not has(r'\bone line per side\b',p.body):
        return None
    sides={'triangle':3,'square':4,'rectangle':4,'pentagon':5,'hexagon':6,
           'heptagon':7,'octagon':8,'nonagon':9,'decagon':10}
    terms=[]
    for i,n in enumerate(ns):
        tail=t[n.end:ns[i+1].start if i+1<len(ns) else len(p.body)]
        if n.value==1 and re.match(r'\s+line per side\b',tail):
            continue
        shapes={k for k in sides if has(r'\b'+k+r's?\b',tail)}
        if len(shapes)!=1:
            return None
        terms.append(n.value*sides[next(iter(shapes))])
    return answer(total(terms),fmt(terms))


def _alternating_floors(p):
    """Different per-floor durations for even and odd floor numbers."""
    ns,t=p.numbers,p.text.lower()
    if len(ns) not in (3,4) or not has(r'\bincludes getting to the first floor\b',p.body):
        return None
    n,even,odd=ns[:3]
    ref=ns[3] if len(ns)==4 else None
    ordinal=re.search(r'\b(\d+)(?:st|nd|rd|th) floor\b',p.question)
    if n.value.denominator!=1 or ref and n.value!=ref.value or label(t[n.end:])!='floor':
        return None
    if not ref and (not ordinal or int(ordinal.group(1))!=n.value):
        return None
    if not has(r'\beven-numbered floors\b',t[even.end:odd.start]) or not has(r'\bodd-numbered floors\b',t[odd.end:ref.start if ref else len(p.body)]):
        return None
    e=converted(even.value,label(t[even.end:]),asked(p))
    o=converted(odd.value,label(t[odd.end:]),asked(p))
    if e is None or o is None:
        return None
    count=int(n.value)
    return answer((count//2)*e+((count+1)//2)*o,
                  '{} x {} + {} x {}'.format(*map(format_number,(count//2,e,(count+1)//2,o))))


def _opposite_round_trip_difference(p):
    """Difference between two one-way distances, repeated round trips."""
    ns,t=p.numbers,p.text.lower()
    if len(ns)!=3 or ns[-1].start<len(p.body):
        return None
    a,b,d=ns
    if not has(r'\bfarther\b',p.question) or not has(r'\bto [a-z]+ and back\b',p.question):
        return None
    if not has(r'\bevery day\b',p.body) or label(t[d.end:])!='day':
        return None
    unit=label(t[a.end:])
    if unit not in ('mile','meter','kilometer','foot') or label(t[b.end:])!=unit:
        return None
    return answer(2*abs(a.value-b.value)*d.value,
                  '2 x |{} - {}| x {}'.format(*map(format_number,p.values)))


def _fractional_inventory(p):
    """Literal stock losses, a fraction of the remainder, then additions."""
    ns,t=p.numbers,p.text.lower()
    if not 4<=len(ns)<=9 or any(n.start>=len(p.body) for n in ns):
        return None
    if has(r'\b(?:each|every|per|times|twice|more than|fewer than)\b',p.body):
        return None
    fractions=[i for i,n in enumerate(ns) if 0<n.value<1]
    if len(fractions)!=1 or fractions[0]<2:
        return None
    fi=fractions[0]
    unit=label(t[ns[0].end:])
    if not compatible(unit,asked(p)) or not has(r'\b(?:has|had|have)\s*$',t[:ns[0].start]):
        return None
    value=ns[0].value
    work=format_number(value)
    for i,n in enumerate(ns[1:],1):
        before=t[ns[i-1].end:n.start]
        if i==fi:
            if not has(r'\bremaining\b',before) or not has(r'\b(?:donates?|gives?|gave away|uses?|eats?)\s*$',before):
                return None
            value*=1-n.value
            work='('+work+') x (1 - '+format_number(n.value)+')'
            continue
        if not compatible(unit,label(t[n.end:])):
            return None
        remove=has(r'\b(?:loses?|lost|used|ate|donates?|gave away)\s*$',before)
        add=has(r'\b(?:purchases?|buys?|bought|receives?|received)(?: [a-z]+)?\s*$',before)
        if remove==add:
            return None
        value+=(-1 if remove else 1)*n.value
        work+=(' - ' if remove else ' + ')+format_number(n.value)
    return answer(value,work)


def _task_time_budgets(p):
    """Time per task and separate time budgets for each category of task."""
    ns,t=p.numbers,tokenize(p)
    if not 4<=len(ns)<=12 or len(ns)%2 or not has(r'^how many (?:pieces|items|objects)\b',p.question):
        return None
    rates,used={},set()
    for m in re.finditer(r'\b(?:a|an) ([a-z]+) in Q(\d+) (seconds?|minutes?|hours?)\b',t):
        key,i,u=m.groups();i=int(i);key=label(key)
        if key in rates or ns[i].value<=0:
            return None
        rates[key]=(ns[i].value,label(u));used.add(i)
    if len(rates)<2:
        return None
    terms,seen=[],set()
    for i,n in enumerate(ns):
        if i in used:
            continue
        tail=p.text.lower()[n.end:ns[i+1].start if i+1<len(ns) else len(p.body)]
        keys=[k for k in rates if has(r'\b'+re.escape(k)+r'(?:s|es)?\b',tail)]
        if len(keys)!=1:
            return None
        key=keys[0];duration=converted(n.value,label(tail),rates[key][1])
        if duration is None:
            return None
        seen.add(key);terms.append(duration/rates[key][0])
    if seen!=set(rates):
        return None
    return answer(total(terms),fmt(terms))


def _interval_rate_breaks(p):
    """An output/time ratio, minus explicit repeated breaks in the new span."""
    ns,t=p.numbers,p.text.lower()
    if len(ns)!=5:
        return None
    output,interval,span,count,length=ns
    if not compatible(label(t[output.end:]),asked(p)) or interval.value<=0:
        return None
    if not has(r'\bin\s*$',t[output.end:interval.start]):
        return None
    if not re.fullmatch(r'\s*',t[count.end:length.start]) or not has(r'^-(?:seconds?|minutes?|hours?) breaks\b',t[length.end:]):
        return None
    unit=label(t[interval.end:])
    duration=converted(span.value,label(t[span.end:]),unit)
    pause=converted(length.value,label(t[length.end:].lstrip('-')),unit)
    if duration is None or pause is None or duration<count.value*pause:
        return None
    return answer(output.value*(duration-count.value*pause)/interval.value,
                  '{} x ({} - {} x {}) / {}'.format(*map(format_number,(output.value,duration,count.value,pause,interval.value))))


def _rate_difference_break(p):
    """Two named production rates, with a break for one named producer."""
    ns,t=p.numbers,p.text.lower()
    if len(ns)!=4 or not has(r'\bdifference\b',p.question):
        return None
    a,b,pause,span=ns
    owners=[];unit='';period=''
    for i,n in enumerate((a,b)):
        before=t[ns[i-1].end if i else 0:n.start]
        owner=re.search(r'\b([a-z]+) (?:makes?|produces?|bakes?|writes?|types?)\s*$',before)
        tail=t[n.end:ns[i+1].start]
        rate=re.match(r'\s*(?:([a-z]+) )?(?:every|each|per) (second|minute|hour)\b',tail)
        if not owner or not rate:
            return None
        owners.append(owner.group(1))
        if i==0:
            unit=label(rate.group(1) or '');period=rate.group(2)
        elif rate.group(1) and not compatible(label(rate.group(1)),unit) or rate.group(2)!=period:
            return None
    m=re.search(r'\b([a-z]+) took (?:a |an )?$',t[b.end:pause.start])
    if not m or m.group(1) not in owners or not has(r'^-(?:second|minute|hour) break\b',t[pause.end:]):
        return None
    duration=converted(span.value,label(t[span.end:]),period)
    breaktime=converted(pause.value,label(t[pause.end:].lstrip('-')),period)
    if duration is None or breaktime is None or duration<breaktime:
        return None
    values=[a.value*duration,b.value*duration]
    values[owners.index(m.group(1))]-=ns[owners.index(m.group(1))].value*breaktime
    return answer(abs(values[0]-values[1]),'|{} - {}|'.format(*map(format_number,values)))


def _shared_input_ratios(p):
    """One input amount suffices for separate stated amounts of each category."""
    ns,t=p.numbers,tokenize(p)
    if not 5<=len(ns)<=13 or len(ns)%2!=1:
        return None
    intro=re.search(r'Q0 ([a-z -]+?) can ([a-z]+) (Q1[^.?!;]+)',t)
    if not intro or not compatible(label(intro.group(1)),asked(p)):
        return None
    split=(len(ns)+1)//2
    ids=[int(i) for i in re.findall(r'Q(\d+)',intro.group(3))]
    if ids!=list(range(1,split)):
        return None
    ratios={}
    for i in ids:
        key=label(p.text.lower()[ns[i].end:])
        if not key or key in ratios or ns[i].value<=0:
            return None
        ratios[key]=ns[0].value/ns[i].value
    terms,seen=[],set()
    for i,n in enumerate(ns[split:],split):
        key=label(p.text.lower()[n.end:])
        if key not in ratios or key in seen:
            return None
        seen.add(key);terms.append(n.value*ratios[key])
    if seen!=set(ratios):
        return None
    return answer(total(terms),fmt(terms))


def _net_flow_with_removal(p):
    """Two simultaneous flow rates, then a final removal in another unit."""
    ns,t=p.numbers,p.text.lower()
    if len(ns)!=4 or not has(r'\b(?:left|remaining)\b',p.question):
        return None
    a,b,d,r=ns
    rates=[]
    for i,n in enumerate((a,b)):
        tail=t[n.end:ns[i+1].start]
        m=re.match(r'\s+([a-z]+)\s*(?:/|per )(second|minute|hour)\b',tail)
        if not m:
            return None
        before=t[ns[i-1].end if i else 0:n.start]
        minus=has(r'\b(?:evaporates?|loses?|leaks?|drains?)\b',before)
        plus=has(r'\b(?:dripping|fills?|filling|flows?|running)\b',before)
        if minus==plus:
            return None
        value=converted(n.value,label(m.group(1)),asked(p))
        duration=converted(d.value,label(t[d.end:]),m.group(2))
        if value is None or duration is None:
            return None
        rates.append((-1 if minus else 1)*value*duration)
    if not has(r'\b(?:dumps? out|pours? out|removes?|empties)\s*$',t[d.end:r.start]):
        return None
    removed=converted(r.value,label(t[r.end:]),asked(p))
    if removed is None:
        return None
    return answer(total(rates)-removed,'({}) - {}'.format(fmt(rates),format_number(removed)))


def _inverse_rate_inventory(p):
    """One output rate, several work durations, losses and a final inventory."""
    ns,t=p.numbers,p.text.lower()
    if not 5<=len(ns)<=10 or not has(r'\b(?:start with|begin with|at the beginning)\b',p.question):
        return None
    rate,final=ns[0],ns[-1]
    m=re.match(r'\s+([a-z -]+?) per (second|minute|hour)\b',t[rate.end:])
    if not m or not compatible(label(m.group(1)),asked(p)):
        return None
    u,period=label(m.group(1)),m.group(2)
    if not compatible(label(t[final.end:]),u) or not has(r'\b(?:had|has|total of)\s*$',t[ns[-2].end:final.start]):
        return None
    output,losses,work=Fraction(0),Fraction(0),[]
    for i,n in enumerate(ns[1:-1],1):
        unit=label(t[n.end:])
        before=t[ns[i-1].end:n.start]
        duration=converted(n.value,unit,period)
        if duration is not None:
            if has(r'\b(?:break|rest|nap)[^.;]*for\s*$',before):
                return None
            output+=rate.value*duration
            work.append(rate.value*duration)
        elif compatible(unit,u) and has(r'\b(?:erase|erased|remove|removed|lost|discard|discarded)\s*$',before):
            losses+=n.value
        else:
            return None
    if not work:
        return None
    return answer(final.value-output+losses,'{} - ({}) + {}'.format(format_number(final.value),fmt(work),format_number(losses)))


def _growing_sequence_sum(p):
    """First term plus a constant increment, queried over an initial prefix."""
    ns,t=p.numbers,p.text.lower()
    if len(ns)!=4 or ns[-1].start<len(p.body):
        return None
    initial,observed,delta,count=ns
    if not has(r'\bon the first [a-z]+\b',t[initial.end:observed.start]):
        return None
    if not has(r'\bfirst\s*$',t[initial.end:observed.start]) or not has(r'\bincreased by\s*$',t[observed.end:delta.start]):
        return None
    m=re.match(r'\s+after every ([a-z]+)\b',t[delta.end:])
    if not m or not compatible(label(m.group(1)),label(t[count.end:])) or not compatible(label(t[observed.end:]),label(t[count.end:])):
        return None
    if not compatible(label(t[initial.end:]),asked(p)) or count.value>observed.value or count.value.denominator!=1:
        return None
    n=count.value
    return answer(n*initial.value+n*(n-1)*delta.value/2,
                  '{} x {} + {} x ({} - 1) x {} / 2'.format(*map(format_number,(n,initial.value,n,n,delta.value))))


def _extension_progress(p):
    """A starting measurement, an expanded target, and related work stages."""
    ns,t=p.numbers,p.text.lower()
    if len(ns)!=4 or any(n.start>=len(p.body) for n in ns):
        return None
    start,end,work,factor=ns
    unit=label(t[start.end:])
    if unit not in ('mile','meter','kilometer','foot') or not compatible(unit,asked(p)):
        return None
    if label(t[end.end:])!=unit or label(t[work.end:])!=unit:
        return None
    if not has(r'\bextended\b',t[:start.start]) or not has(r'\bup to\s*$',t[start.end:end.start]):
        return None
    if not has(r'\bfirst day\b',t[work.end:factor.start]) or not has(r'^\s+times this amount\b',t[factor.end:]):
        return None
    if not has(r'\bsecond day\b',t[factor.end:]) or not has(r'\bstill need\b',p.question):
        return None
    return answer(end.value-start.value-work.value*(1+factor.value),
                  '{} - {} - {} x (1 + {})'.format(*map(format_number,(end.value,start.value,work.value,factor.value))))


def _relative_inventory_gap(p):
    """Two related starting categories, a loss, then a third unknown category."""
    ns,t=p.numbers,tokenize(p)
    if len(ns)!=4:
        return None
    m=re.search(r'Q0 ([a-z -]+?) and Q1 times (?:more|as many) ([a-z -]+)',t)
    if not m or not has(r'\blost Q2\b',t) or not has(r'\b(?:had|has) Q3\b.*\bin total\b',t):
        return None
    a,b=label(m.group(1)),label(m.group(2))
    if not a or not b or a==b or a.split()[-1]!=b.split()[-1]:
        return None
    loss=label(re.sub(r'^\s*of (?:the )?','',p.text.lower()[ns[2].end:]))
    final=label(p.text.lower()[ns[3].end:])
    target=asked(p)
    if not compatible(loss,a) or not compatible(final,a) or not compatible(target,final) or target in (a,b):
        return None
    if not has(r'\bbuy some\b',p.body):
        return None
    return answer(ns[3].value-ns[0].value*(1+ns[1].value)+ns[2].value,
                  '{} - {} x (1 + {}) + {}'.format(*map(format_number,(ns[3].value,ns[0].value,ns[1].value,ns[2].value))))


def solve(problem):
    if any(n.kind != 'number' or n.value < 0 for n in problem.numbers):
        return None
    for reader in (_labelled_contents, _parallel_rates, _daily_progression,
                   _weekday_multiplier, _combined_ages, _square_layers,
                   _partitioned_contents, _repeated_growth_total,
                   _owner_ledger, _named_differences, _parents_and_contents,
                   _remaining_measure, _mass_loads, _relative_daily_time,
                   _measure_comparisons, _ratio_difference, _ratio_transfer,
                   _mixed_time_budget, _fill_and_drain, _grouped_resource_output,
                   _exception_contents, _daily_category_losses, _repeated_route,
                   _weekly_consumption, _weekly_opening_hours, _group_pair_totals,
                   _weekday_rates, _named_week_schedule, _progressive_daily_total,
                   _periodic_doubling, _weighted_rating, _residual_groups,
                   _fraction_subgroup_complement, _two_speed_journey,
                   _detour_return, _group_fraction_removal, _calendar_duration_sum,
                   _weekday_nights, _polygon_sides, _alternating_floors,
                   _opposite_round_trip_difference, _fractional_inventory,
                   _task_time_budgets, _interval_rate_breaks, _rate_difference_break,
                   _shared_input_ratios, _net_flow_with_removal, _inverse_rate_inventory,
                   _growing_sequence_sum, _extension_progress, _relative_inventory_gap):
        result = reader(problem)
        if result is not None:
            return result
    return None
