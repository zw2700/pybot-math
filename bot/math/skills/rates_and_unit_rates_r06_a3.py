"""Small rate schemas with explicit units, residual stocks, and measured work.

A rule must explain all quantities.  Counts are never divided just because
there are two of them; a per-unit relation or equal allocation is required.
"""
import re
from dataclasses import replace
from fractions import Fraction
from itertools import product

from ..numbers import format_number
from . import rates_and_unit_rates_r03_a5 as core


_STOP = core._STOP | set(('over into ate eat eats receive receives got brew brews '
                         'provides provide playing lasts last finish finished equal '
                         'including sold shows show needs need takes took come so yesterday today tomorrow plus ').split())
_ALIASES = {'lb': 'pound', 'lbs': 'pound', 'euro': 'money', 'dollar': 'money',
            'kid': 'person', 'people': 'person', 'member': 'person',
            'movy': 'movie', 'tomatoe': 'tomato', 'row': 'row'}
_TIME = {'second', 'minute', 'hour', 'day', 'week', 'month', 'year'}


def _normal(word):
    return _ALIASES.get(core._normal(word), core._normal(word))


def _head(text):
    text = re.sub(r'^\s*(?:of\s+)?(?:(?:his|her|their|the)\s+)?', '', text)
    words = re.findall(r'[a-z]+|[^a-z\s-]', text.lstrip(' -'))
    kept = []
    words = [w for w in words if w not in ('equal', 'big', 'small', 'single', 'individual', 'best')]
    for w in words:
        if w in _STOP or not w.isalpha():
            break
        w = _normal(w)
        kept.append(w)
        if w in core._MEASURES or w in ('money', 'cent', 'pound'):
            return w
        if len(kept) == 4:
            break
    return kept[-1] if kept else ''


def _unit(p, n):
    tail = p.text[n.end:].lower()
    if n.kind == 'money' or re.match(r'\s*€', tail):
        return 'money'
    tail = re.sub(r'^\s+dozens?(?:\s+of)?\s+', ' ', tail)
    tail = re.sub(r'^\s+(?:more|additional|extra)\s+', ' ', tail)
    return _head(tail)


def _asked(p):
    q = p.question
    if re.match(r'how much time',q):
        explicit = re.search(r'\bin (seconds?|minutes?|hours?|days?|weeks?)\b',q)
        if explicit:
            return _normal(explicit.group(1))
    if q.startswith('how far'):
        distances = [d for d in ('mile', 'kilometer', 'meter', 'foot') if re.search(r'\b'+d+r's?\b', p.body)]
        return distances[0] if len(distances)==1 else 'distance'
    m = re.match(r'how (?:many|much)\s+(?:(?:more|additional|total)\s+)?(.+)', q)
    if m:
        h = _head(m.group(1))
        if h:
            return h
    if re.search(r'\b(?:cost|pay|spend|money|price|take home)\b', q):
        return 'money'
    m = re.search(r'\bnumber of (.+?)\s+(?:given|in|does|did|are|is)', q)
    return _head(m.group(1)) if m else core._question(p)


def _numbers(p):
    ns = []
    for n in p.numbers:
        before, after = p.text[:n.start].lower(), p.text[n.end:].lower()
        if n.value == 1 and re.match(r'\s+[a-z]+ at a time\b', after):
            continue
        if n.value == 1 and (re.search(r'\bat least\s*$',before) and re.match(r'\s+[a-z]+ at each\b',after)
                             or re.search(r'\beach\s*$',before) and re.match(r'\s*[.,!?]',after)
                             or re.match(r'\s+(?:sitting|after the other)\b',after)):
            continue
        if n.value == 2 and re.search(r'\bthe\s*$',before) and re.match(r'\s+working together\b',after):
            continue
        if n.value == 1 and re.match(r'\s+[a-z]+ (?:will )?(?:yield|provide)s?\s+', after):
            continue
        if n.value == 1 and (re.search(r'\b(?:each|every)\s*$', before)
                            and re.match(r'\s+(?:of|ate|gets?|receives?)\b', after)):
            continue
        if n.start >= len(p.body) and any(n.value == old.value and _unit(p, n) == _unit(p, old) for old in ns):
            continue
        if re.match(r'\s+dozens?\b', after):
            n = replace(n, value=n.value*12)
        ns.append(n)
    return ns


def _result(value, expr, p):
    if value < 0:
        return None
    currency = 'euros' if re.search(r'€|\beuros?\b', p.text, re.I) else ('pounds' if '£' in p.text else 'dollars')
    label = 'Amount in {}: '.format(currency) if _asked(p) == 'money' else 'Calculation: '
    return value, label + expr + ' = ' + format_number(value) + '.'


def _f(n):
    return format_number(n.value if hasattr(n, 'value') else n)


def _denoms(p, ns, us):
    ds = [list(dict.fromkeys(_normal(d) for d in core._denominators(p, ns, i, us))) for i in range(len(ns))]
    t = p.text.lower()
    for i, n in enumerate(ns):
        before = re.split(r'[.!?;](?:\s|$)', t[:n.start])[-1]
        after = t[n.end:ns[i+1].start if i+1 < len(ns) else len(t)]
        per = re.search(r'\bper ([a-z -]+)', after)
        if per and not re.search(r'[.!?;]|\b(?:and|but)\b', after[:per.start()]):
            head = _head(per.group(1))
            if head:
                ds[i] = [head]
        # An incidental purpose ('pages for a course') is not a rate.
        # Indefinite non-time denominators need a referenced unit elsewhere.
        if ds[i] and not re.search(r'\b(?:each|every|per)\b', before+' '+after):
            ds[i] = [d for d in ds[i] if d in _TIME or d in us or d == _asked(p)]

        m = re.search(r'\b(?:each|every)\s+(.+?)\s+(?:(?:will|can)\s+)?(?:provides?|brews?|gets?|receives?|ate|eats?|lasts?|is cut into|cuts?[^.;]*?into|has|contains?)\s*(?:about\s*)?$', before)
        if m:
            h = _head(m.group(1))
            if h:
                ds[i] = [h]
        if re.search(r'\beach of (?:them|us) (?:ate|eats?|gets?|receives?)\s*$', before):
            ds[i] = ['person']
        if re.search(r'\beach of (?:his|her|their) friends (?:will )?(?:receive|eat|get)s?\s*$', before):
            ds[i] = ['person']
        # An explicit unit before the verb can be separated by an of-phrase.
        m = re.search(r'\beach (\w+)\.? of [^;!?]*?\b(?:will )?(?:brew|provide|contain|hold)s?\s*(?:about\s*)?$', t[:n.start])
        if m:
            ds[i] = [_normal(m.group(1))]
        m = re.search(r'\b(?:each|every) (\w+) (?:into|to get|to receive)\s*$', before)
        if m:
            ds[i] = [_normal(m.group(1))]
        m = re.search(r'\bone ([a-z]+) (?:will )?(?:yield|provide)s?\s*$',before)
        if m:
            ds[i]=[_normal(m.group(1))]
        m = re.search(r'\beach ([a-z]+) needs? (?:its|his|her|their) (?:own )?(?:dedicated )?space of\s*$',before)
        if m:
            ds[i]=[_normal(m.group(1))]
        m = re.search(r'\b([a-z]+s) are\s*$',before)
        if m and re.search(r'\beach '+re.escape(_normal(m.group(1)))+r's?\b',p.question):
            ds[i]=[_normal(m.group(1))]
        m = re.search(r'\bfrom each of the ([a-z]+)\b',after)
        if m:
            ds[i]=[_normal(m.group(1))]
        m = re.search(r'\beach to (?:his|her|their) ([a-z ]+)',after)
        if m:
            ds[i]=[_head(m.group(1))]
        if i and re.search(r'\b(?:that are|that is) each\s*$',before):
            ds[i]=[us[i-1]]
        m = re.search(r'\bfit in each ([a-z]+)\b',after)
        if m:
            ds[i]=[_normal(m.group(1))]
        m = re.search(r'\b(?:sell|sells|sold) each ([a-z ]+?) for\s*$',before)
        if m and n.kind=='money':
            ds[i]=[_head(m.group(1))]
        m = re.search(r'\beach of (?:his|her|their) ([a-z]+) (?:got|gets?|receives?|ate)\s*$',before)
        if m:
            ds[i]=[_normal(m.group(1))]
        if i and not ds[i] and re.search(r'\band(?: serves? (?:about )?)?\s*$',before) and ds[i-1]:
            # Coordinated requirements under the same each-subject.
            middle=t[ns[i-1].end:n.start]
            if not re.search(r'[.!?;]|\b(?:he|she|they|each|every)\b',middle):
                ds[i]=list(ds[i-1])
        if i and not ds[i] and re.search(r'\busing\s*$',before) and re.search(r'\beach\b',after):
            ds[i]=[us[i-1]]
        m = re.search(r'\bto make (?:a|an) ([a-z]+)\b',after)
        if m:
            ds[i]=[_normal(m.group(1))]
        # The last each/every subject owns the local rate; an earlier
        # coordinated subject cannot steal it.
        each = list(re.finditer(r'\b(?:each|every)\s+', before))
        if each:
            local = before[each[-1].end():]
            m = re.fullmatch(r'([a-z]+(?:[ -]+[a-z]+){0,3}?)\s+(?:(?:will|can)\s+)?(?:provides?|brews?|gets?|got|receives?|ate|eats?|lasts?|is cut into|is topped with|is made up of|has|contains?|needs?|requires?|is|costs?)\s*(?:about\s*)?', local)
            if m and not local.startswith('of '):
                ds[i] = [_head(m.group(1))]
        # An explicitly singular producer adds a producer denominator when
        # the question asks how many producers are needed.
        m = re.search(r'\b(?:a|an) ([a-z]+) (?:can )?(?:process|produce|make|build|deliver)s?\s*$', before)
        if m and _normal(m.group(1)) == _asked(p):
            subject = _normal(m.group(1))
            if subject not in ds[i]:
                ds[i].append(subject)
        m = re.search(r'\b(?:sell|selling|sells) (?:his |her |their )?([a-z ]+?) for\s*$', before)
        if m and n.kind=='money' and re.match(r'\s+each\b',after):
            ds[i]=[_head(m.group(1))]
        # A per-event payment to each producer has two denominators.
        producer = re.search(r'\b([a-z]+) each (?:earns?|receives?|gets?|is paid)\s*$', before)
        if n.kind == 'money' and producer and len(ds[i]) == 1:
            unit = _normal(producer.group(1))
            if unit not in ds[i]:
                ds[i].append(unit)
    return ds


def _residual(p, ns, us, ds):
    """Subtract consumed/left work, or add a stated shortfall, before sharing."""
    if len(ns) != 3:
        return None
    t = p.text.lower()
    asked = _asked(p)
    # Total work - already completed work, divided by remaining periods.
    periods = [i for i, u in enumerate(us) if u in _TIME]
    if len(periods) == 1 and re.search(r'\b(?:each|every|per)\b', p.question):
        k = periods[0]
        a, b = [i for i in range(3) if i != k]
        if us[a] == us[b] == asked and re.search(r'\b(?:left|finish|complete|remaining)\b', t) and not any(ds):
            av = core._measure(us[k]); target = re.search(r'\b(?:per|each|every) (\w+)', p.question)
            dest = _normal(target.group(1)) if target else us[k]
            dv = core._measure(dest)
            if av[0] == dv[0]:
                duration = ns[k].value*av[1]/dv[1]
                return _result((ns[a].value-ns[b].value)/duration, '({} - {}) / {}'.format(_f(ns[a]),_f(ns[b]),_f(duration)),p)
    # A count of groups inferred from the available quantity and a share size.
    rates = [i for i,d in enumerate(ds) if d == [asked]]
    if len(rates) == 1:
        r = rates[0]
        a,b = [i for i in range(3) if i != r]
        if us[a] == us[b] == us[r] and not ds[a] and not ds[b]:
            if re.search(r'\b(?:left|remaining)\b',t) or re.search(r'\bonly (?:ate|eats?|gets?|got)\b',t):
                return _result((ns[a].value-ns[b].value)/ns[r].value,'({} - {}) / {}'.format(_f(ns[a]),_f(ns[b]),_f(ns[r])),p)
    # Tender and remaining cash explicitly determine the purchase cost.
    cash = [i for i,u in enumerate(us) if u == 'money']
    if len(cash) == 2 and asked == 'money' and re.search(r'\beach\b.*\bcost\b',p.question):
        a,b = cash; k = next(i for i in range(3) if i not in cash)
        if not any(ds) and ((re.search(r'\bafter buying\b',p.body) and re.search(r'\b(?:had|has)\b',p.body[ns[k].end:])) or re.search(r'\bchange\b',p.body) or (re.search(r'\bsame amount\b',p.body) and re.search(r'\bcost\s*$',t[:ns[b].start]) and re.search(r'\bfor\s*$',t[:ns[a].start]))):
            return _result((ns[a].value-ns[b].value)/ns[k].value,'({} - {}) / {}'.format(_f(ns[a]),_f(ns[b]),_f(ns[k])),p)
    return None


def _measured(p, ns, us, ds):
    """N outputs every T minutes, or a speed over a compound duration."""
    t = p.text.lower(); asked = _asked(p)
    if len(ns) == 3 and us[1] in _TIME and us[0] not in _TIME and not ds[0]:
        between = t[ns[0].end:ns[1].start]
        if re.search(r'\b(?:every|in|over)\s*$', between) and not re.search(r'[.!?;]',between):
            if us[2] == us[1] and asked == us[0] and not ds[1]:
                return _result(ns[0].value*ns[2].value/ns[1].value,'{} * {} / {}'.format(_f(ns[0]),_f(ns[2]),_f(ns[1])),p)
            if us[2] == us[0] and asked == us[1] and not any(ds):
                return _result(ns[2].value*ns[1].value/ns[0].value,'{} * {} / {}'.format(_f(ns[2]),_f(ns[1]),_f(ns[0])),p)
    if len(ns) == 3 and us[1] in _TIME and us[2] in _TIME and asked == 'speed':
        if not re.search(r'\bin\s*$',t[ns[0].end:ns[1].start]) or not re.fullmatch(r'\s+(?:seconds?|minutes?|hours?)(?:\s+and)?\s+',t[ns[1].end:ns[2].start]):
            return None
        m = re.search(r'\bper (second|minute|hour)\b',p.question)
        if m:
            unit=m.group(1); base,fac=core._measure(unit)
            a,af=core._measure(us[1]); b,bf=core._measure(us[2])
            if a == b == base:
                elapsed=(ns[1].value*af+ns[2].value*bf)/fac
                return _result(ns[0].value/elapsed,'{} / {}'.format(_f(ns[0]),_f(elapsed)),p)
    return None


def _combined(p, ns, us, ds):
    if len(ns) != 3 or _asked(p) not in _TIME or not re.search(r'\b(?:last|together|both|she and|he and|them)\b',p.text.lower()):
        return None
    asked = _asked(p)
    rs = [i for i,d in enumerate(ds) if d == [asked]]
    if len(rs) != 2:
        return None
    i,j=rs; k=next(k for k in range(3) if k not in rs)
    a,af=core._measure(us[i]); b,bf=core._measure(us[j]); c,cf=core._measure(us[k])
    if a == b == c and not ds[k]:
        return _result(ns[k].value*cf/(ns[i].value*af+ns[j].value*bf),'Combine consumption in compatible units, then divide the stock by that rate',p)
    return None


def _sharing_sum(p, ns, us, ds):
    q=p.question; t=p.text.lower(); asked=_asked(p)
    if len(ns) == 3 and re.search(r'\b(?:equally|equal number|same number)\b',t) and re.search(r'\b(?:divide|divided|split|share|shared|given)\b',t):
        group=re.search(r'\beach (\w+)\b',q)
        if group:
            unit=_normal(group.group(1)); ks=[i for i,u in enumerate(us) if u == unit]
            if len(ks)==1:
                k=ks[0]; a,b=[i for i in range(3) if i != k]
                if us[a] == us[b] == asked and not any(ds):
                    return _result((ns[a].value+ns[b].value)/ns[k].value,'({} + {}) / {}'.format(_f(ns[a]),_f(ns[b]),_f(ns[k])),p)
    # A listed daily observation is one sample per distinct named day.
    if 2 <= len(ns) <= 7 and re.search(r'\baverage\b.*\bper day\b',q) and len(set(us)) == 1 and not any(ds):
        days=re.findall(r'\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',p.body)
        if len(days)==len(ns) and len(set(days))==len(days):
            return _result(sum((n.value for n in ns),Fraction(0))/len(ns),'({}) / {}'.format(' + '.join(_f(n) for n in ns),len(ns)),p)
    # Two named participants share a metered bill equally.
    if len(ns)==2 and asked=='money' and re.search(r'\bshared the cost\b',p.body) and re.search(r'\beach (?:friend|person)\b',q):
        names=re.match(r"([A-Z][a-z]+) and ([A-Z][a-z]+) shared\b",p.text)
        if names and names.group(1)!=names.group(2):
            r=[i for i,d in enumerate(ds) if len(d)==1 and d[0] in _TIME]
            if len(r)==1:
                i=r[0]; j=1-i
                if us[i]=='money' and us[j]==ds[i][0] and not ds[j]:
                    return _result(ns[i].value*ns[j].value/2,'{} * {} / 2'.format(_f(ns[i]),_f(ns[j])),p)
    return None


def _chain(p, ns, us, ds):
    """A unique dimensional chain of explicitly stated per-unit quantities."""
    t=p.text.lower(); asked=_asked(p)
    if not 2 <= len(ns) <= 3 or not all(us) or not asked or not any(ds):
        return None
    guard_text = re.sub(r'\b(?:no|without) breaks?\b', '', t)
    if re.search(r'\b(?:left|remaining|more|less|than|beat|instead|half|twice|rest|already|gives|change|profit|free|leap year|every other|stops?|breaks?|waits?|weekdays|weekends|except|skips?)\b',guard_text) or (re.search(r'\bgave\b',t) and not re.search(r'\bgave all\b',t)):
        return None
    if re.search(r'\bfor (?:both|each of them)\b', p.question):
        return None
    atoms=[core._amount(n.value,u,d,_f(n),[i]) for i,(n,u,d) in enumerate(zip(ns,us,ds))]
    den=[]
    if asked=='money' and re.search(r'\beach use\b',p.question):
        asked='money'
        ds=[[('use' if d=='time' else d) for d in group] for group in ds]
        us=['use' if u=='time' else u for u in us]
        atoms=[core._amount(n.value,u,d,_f(n),[i]) for i,(n,u,d) in enumerate(zip(ns,us,ds))]
    query=re.split(r'\b(?:if|when|assuming|since|because)\b',p.question)[0]
    m=re.search(r'\b(?:each|every|per) (\w+)',query)
    if m:
        h='use' if m.group(1)=='use' else _head(query[m.start(1):])
        if h and (h not in _STOP or h=='use'):
            den=[h]
    target=core._amount(Fraction(1),asked,den,'',[])
    answers={}
    for signs in product((1,-1),repeat=len(atoms)):
        # The available stock is a numerator, never a reciprocal.
        if not den and any(s<0 and not ds[i] and us[i] not in [d for group in ds for d in group] for i,s in enumerate(signs)):
            continue
        value=Fraction(1); powers={}
        for a,s in zip(atoms,signs):
            value=value*a.value if s==1 else value/a.value
            for u,e in a.dims:
                powers[u]=powers.get(u,0)+s*e
        if core._dim(powers)==target.dims:
            answers[value/target.value]=signs
    if len(answers)!=1:
        return None
    value,signs=next(iter(answers.items()))
    # Physical count queries require whole containers/items. Time and other
    # measured units retain their exact fractional values.
    discrete = asked not in core._MEASURES | _TIME | {'money', 'cent'}
    if not den and discrete and any(asked in group for group in ds):
        if re.search(r'\b(?:need|required|should|must|order)\b', query):
            value = Fraction(-(-value.numerator // value.denominator))
        elif re.search(r'\bcan\b', query) and re.search(r'\b(?:make|produce|fit|fill|buy|wrap)\b', query):
            value = Fraction(value.numerator // value.denominator)
    return _result(value,' * '.join(_f(n) if s==1 else '(1 / {})'.format(_f(n)) for n,s in zip(ns,signs))+' (using compatible units)',p)



def _work_and_production(p, ns, us, ds):
    if len(ns) != 3:
        return None
    t=p.text.lower(); asked=_asked(p)
    # Constant work: worker count times duration is conserved for the same job.
    times=[i for i,u in enumerate(us) if u in _TIME]
    if len(times)==1 and re.search(r'how long',p.question) and re.search(r'\bsame (?:size|job|work)\b',t) and re.search(r'\bsame rate\b',t):
        k=times[0]; a,b=[i for i in range(3) if i != k]
        if us[a] == us[b] and us[a] and not any(ds):
            return _result(ns[k].value*ns[a].value/ns[b].value,'{} * {} / {}'.format(_f(ns[k]),_f(ns[a]),_f(ns[b])),p)
    # A team produces a measured output per period; scale the team, not time.
    if us[1] == us[2] and us[0] == asked and len(ds[1])==1 and ds[1]==ds[2] and ds[1][0] in _TIME:
        if re.search(r'\b(?:make|produce|build)\b',t[:ns[1].start]):
            return _result(ns[0].value*ns[2].value/ns[1].value,'{} * {} / {}'.format(_f(ns[0]),_f(ns[2]),_f(ns[1])),p)
    # Independent resources run identical jobs continuously during open time.
    rs=[i for i,d in enumerate(ds) if d == [asked] and us[i] in _TIME]
    if len(rs)==1 and re.search(r'\b(?:back-to-back|continuously|nonstop)\b',t) and re.search(r'\btotal\b',p.question):
        r=rs[0]; duration=[i for i in range(3) if i != r and us[i] == us[r] and not ds[i]]
        if len(duration)==1:
            j=duration[0]; k=next(i for i in range(3) if i not in (r,j))
            if not ds[k]:
                return _result(ns[k].value*ns[j].value/ns[r].value,'{} * {} / {}'.format(_f(ns[k]),_f(ns[j]),_f(ns[r])),p)
    return None


def _grid(p, ns, us, ds):
    if len(ns)!=3 or set(us) != {'column','row','person'} or any(ds):
        return None
    if not re.search(r'\b(?:cut|cuts|cutting)\b',p.body) or not re.search(r'\b(?:even|equal)\b',p.body) or not re.search(r'\beach\b',p.question):
        return None
    k=us.index('person'); a,b=[i for i in range(3) if i != k]
    return _result(ns[a].value*ns[b].value/ns[k].value,'{} * {} / {}'.format(_f(ns[a]),_f(ns[b]),_f(ns[k])),p)


def _basket(p, ns, us, ds):
    if len(ns)!=4 or _asked(p)!='money' or us.count('money')!=2:
        return None
    t=p.text.lower()
    amounts=[i for i,u in enumerate(us) if u=='money']; counts=[i for i,u in enumerate(us) if u!='money']
    for r in amounts:
        before=t[:ns[r].start]
        m=re.search(r'\b(?:a|an|each) ([a-z -]+?) costs?\s*$',before)
        if not m:
            continue
        unit=_head(m.group(1)); matches=[i for i in counts if us[i]==unit]
        if len(matches)!=1:
            continue
        a=matches[0]; b=next(i for i in counts if i != a); total=next(i for i in amounts if i != r)
        if not re.search(r'\b(?:bought|buys?|purchased)\b',t[:ns[total].start]) or not re.search(r'\bfor\s*$',t[:ns[total].start]):
            continue
        query=re.search(r'\beach (.+?) cost',p.question)
        if query and _head(query.group(1))==us[b]:
            return _result((ns[total].value-ns[a].value*ns[r].value)/ns[b].value,'({} - {} * {}) / {}'.format(*(_f(ns[i]) for i in (total,a,r,b))),p)
    return None


def _strict_record(p, ns, us, ds):
    if len(ns)==2 and us[0] == us[1] and ds[0] == [_asked(p)] and not ds[1] and re.search(r'\bbeat\b',p.question):
        q=ns[1].value/ns[0].value
        return _result(Fraction(q.numerator//q.denominator+1),'Whole units strictly exceeding {} / {}'.format(_f(ns[1]),_f(ns[0])),p)
    return None


def _additive_rates(p, ns, us, ds):
    t=p.text.lower(); asked=_asked(p)
    if len(ns)==3:
        # Distinct stated measurements add before dividing by the work rate.
        rs=[i for i,d in enumerate(ds) if d == [asked]]
        if len(rs)==1 and asked in _TIME:
            r=rs[0]; a,b=[i for i in range(3) if i!=r]
            if (us[a]==us[b]==us[r] and not ds[a] and not ds[b]
                    and re.search(r'\bis\s*$',t[:ns[a].start])
                    and re.search(r'\bis\s*$',t[:ns[b].start])
                    and re.match(r'\s+square\b',t[ns[a].end:])
                    and re.match(r'\s+square\b',t[ns[b].end:])
                    and not re.search(r'\b(?:left|remaining|goal|reach|reduce|already)\b',t)):
                return _result((ns[a].value+ns[b].value)/ns[r].value,'({} + {}) / {}'.format(_f(ns[a]),_f(ns[b]),_f(ns[r])),p)
        # Recovered complete groups added to intact groups already present.
        rs=[i for i,d in enumerate(ds) if d == [asked] and us[i]!=asked]
        if len(rs)==1 and re.search(r'\balready\b',p.body) and re.search(r'\bnow\b',p.question):
            r=rs[0]; stocks=[i for i in range(3) if not ds[i] and us[i]==us[r]]; groups=[i for i in range(3) if not ds[i] and us[i]==asked]
            if len(stocks)==len(groups)==1:
                a,b=stocks[0],groups[0]
                return _result(ns[a].value/ns[r].value+ns[b].value,'{} / {} + {}'.format(_f(ns[a]),_f(ns[r]),_f(ns[b])),p)
        # Flat fee plus one variable price, with an explicit final total.
        if us==['money']*3:
            rates=[i for i,d in enumerate(ds) if d==[asked]]
            if len(rates)==1:
                r=rates[0]; a,b=[i for i in range(3) if i!=r]
                if (re.search(r'\b(?:base (?:price|fee)|flat (?:price|fee|rate)|paid.*per day)\b',t)
                        and re.search(r'\b(?:paid|earned|total)\b',t[ns[r].end:])):
                    return _result((ns[b].value-ns[a].value)/ns[r].value,'({} - {}) / {}'.format(_f(ns[b]),_f(ns[a]),_f(ns[r])),p)
        # Reading/using existing stock while new stock arrives at a stated rate.
        if len(set(us))==1 and asked in _TIME and ds[0]==[] and ds[1]==ds[2]==[asked]:
            before1=t[:ns[1].start]; before2=t[:ns[2].start]
            if re.search(r'\b(?:reading|reads?|uses?|consumes?|removes?)\s*$',before1) and re.search(r'\b(?:gets?|receives?|gains?) (?:new )?\s*$',before2):
                rate=ns[1].value-ns[2].value
                if rate>0:
                    return _result(ns[0].value/rate,'{} / ({} - {})'.format(*(_f(n) for n in ns)),p)
    # Redistribution of each explicitly named owner's entire stock.
    if 2 <= len(ns) <= 6 and len(set(us))==1 and us[0]==asked and not any(ds) and re.search(r'\b(?:equal number|equally)\b',t) and re.search(r'\b(?:share|sharing|redistribute)\b',t):
        if all(re.search(r'\b[A-Z][a-z]+ (?:has|had) (?:only )?$',p.text[:n.start]) for n in ns):
            return _result(sum((n.value for n in ns),Fraction(0))/len(ns),'({}) / {}'.format(' + '.join(_f(n) for n in ns),len(ns)),p)
    # A host explicitly shares the total with N invited friends.
    if len(ns)==2 and us[0]=='person' and not any(ds) and re.search(r'\b(?:herself|himself) and (?:her|his) friends\b',p.body) and re.search(r'\bequally\b',p.body) and re.search(r'\beach person\b',p.question):
        return _result(ns[1].value/(ns[0].value+1),'{} / ({} + 1)'.format(_f(ns[1]),_f(ns[0])),p)
    return None


def _rate_changes(p, ns, us, ds):
    t=p.text.lower(); asked=_asked(p)
    if len(ns)==2 and us[0]==us[1]==asked and len(ds[0])==len(ds[1])==1 and re.search(r'\b(?:add|increase)\b',p.question):
        a,af=core._measure(ds[0][0]); b,bf=core._measure(ds[1][0])
        if a==b and ds[0][0] in _TIME and ds[1][0] in _TIME:
            return _result(ns[1].value*af/bf-ns[0].value,'Convert the target to the current period and subtract the current rate',p)
    # Chase: both speeds and the initial separation are explicit.
    if len(ns)==3 and asked in _TIME and re.search(r'\bcatch\b',p.question):
        rs=[i for i,d in enumerate(ds) if d==[asked]]
        if len(rs)==2:
            a,b=rs; k=next(i for i in range(3) if i not in rs)
            if us[a]==us[b]==us[k] and re.search(r'\baway\b',p.body) and not ds[k]:
                delta=abs(ns[a].value-ns[b].value)
                if delta:
                    return _result(ns[k].value/delta,'{} / ({} - {})'.format(_f(ns[k]),_f(max(ns[a].value,ns[b].value)),_f(min(ns[a].value,ns[b].value))),p)
    # A journey with exactly one stop: travel time plus stopped time.
    if len(ns)==3 and re.search(r'\bstop\b',p.body) and asked=='hour':
        speeds=[i for i,u in enumerate(us) if u=='mph']; dist=[i for i,u in enumerate(us) if u=='mile']; wait=[i for i,u in enumerate(us) if u=='hour']
        if len(speeds)==len(dist)==len(wait)==1 and not re.search(r'\b(?:each|every|return|back)\b',p.body):
            a,b,c=dist[0],speeds[0],wait[0]
            return _result(ns[a].value/ns[b].value+ns[c].value,'{} / {} + {}'.format(_f(ns[a]),_f(ns[b]),_f(ns[c])),p)
    return None


def _partitions(p, ns, us, ds):
    t=p.text.lower(); asked=_asked(p)
    # Combined ratio categories: known A plus known A / (A per B).
    if len(ns)==2 and us[0]==us[1] and ds[0]==[asked] and not ds[1] and re.search(r'how many [a-z]+ and [a-z]+.*(?:altogether|total)',p.question):
        return _result(ns[1].value+ns[1].value/ns[0].value,'{} + {} / {}'.format(_f(ns[1]),_f(ns[1]),_f(ns[0])),p)
    if len(ns)==3:
        # An equal allocation followed by the same removal from every group.
        groups=[i for i,u in enumerate(us) if u!=asked and u not in _TIME]
        if len(groups)==1 and re.search(r'\b(?:now|left|remaining)\b',p.question):
            g=groups[0]; rates=[i for i,d in enumerate(ds) if d==[us[g]] and us[i]==asked]
            stocks=[i for i in range(3) if us[i]==asked and not ds[i]]
            if len(rates)==len(stocks)==1 and re.search(r'\b(?:took|takes?|removes?|removed|stole|steals?)\b',p.body):
                r,a=rates[0],stocks[0]
                return _result(ns[a].value/ns[g].value-ns[r].value,'{} / {} - {}'.format(_f(ns[a]),_f(ns[g]),_f(ns[r])),p)
        # Equal shares of stock after an explicit loss or extra purchase.
        if not any(ds) and re.search(r'\b(?:each|per)\b',p.question):
            groups=[i for i,u in enumerate(us) if u=='person' or u in _TIME]
            if len(groups)==1:
                g=groups[0]; a,b=[i for i in range(3) if i!=g]
                if us[a]==us[b]==asked:
                    sign=None
                    if re.search(r'\b(?:steals?|stole|took|lost|loses?|gave|left|remaining|rest)\b',t):
                        sign=-1
                    elif re.search(r'\b(?:buy|buys?|bought)\b[^.!?]*\b(?:additional|more|extra)\b',p.body):
                        sign=1
                    if sign:
                        return _result((ns[a].value+sign*ns[b].value)/ns[g].value,'({} {} {}) / {}'.format(_f(ns[a]),'+' if sign==1 else '-',_f(ns[b]),_f(ns[g])),p)
    # A daily physical requirement is repeated for all days of the week.
    if len(ns)==2 and ds[0]==[asked] and not ds[1] and us[0]==us[1] and re.search(r'\bdaily\b',p.body) and re.search(r'\b(?:the|a|one) week\b',p.question):
        return _result(ns[1].value*7/ns[0].value,'{} * 7 / {}'.format(_f(ns[1]),_f(ns[0])),p)
    # One distance out and back at one stated speed.
    if len(ns)==2 and asked in _TIME and re.search(r'\b(?:forth and back|there and back|and then back)\b',t):
        r=[i for i,d in enumerate(ds) if d==[asked]]
        if len(r)==1:
            i=r[0]; j=1-i
            if us[i]==us[j] and not ds[j]:
                return _result(ns[j].value*2/ns[i].value,'{} * 2 / {}'.format(_f(ns[j]),_f(ns[i])),p)
    return None


def _fees_and_savings(p, ns, us, ds):
    if len(ns)!=3 or us!=['money']*3:
        return None
    t=p.text.lower();asked=_asked(p)
    rates=[i for i,d in enumerate(ds) if d==[asked]]
    if len(rates)==1:
        r=rates[0];a,b=[i for i in range(3) if i!=r]
        if re.search(r'\bbudget\b',t[:ns[b].start]) and re.search(r'\bcost\b',t[:ns[a].start]):
            return _result((ns[b].value-ns[a].value)/ns[r].value,'({} - {}) / {}'.format(_f(ns[b]),_f(ns[a]),_f(ns[r])),p)
        tips=[i for i in (a,b) if re.match(r'\s+in (?:tips|bonuses)\b',t[ns[i].end:])]
        if len(tips)==1 and re.search(r'\b(?:collected|earned|made)\b',t):
            tip=tips[0];total=next(i for i in (a,b) if i!=tip)
            return _result((ns[total].value-ns[tip].value)/ns[r].value,'({} - {}) / {}'.format(_f(ns[total]),_f(ns[tip]),_f(ns[r])),p)
    return None


def _periodic_event(p, ns, us, ds):
    # One event each explicit interval, with one measured observation window.
    if len(ns)!=2 or us[0] not in _TIME or us[1] not in _TIME or any(ds):
        return None
    t=p.text.lower()
    if not re.search(r'\bevery\s*$',t[:ns[0].start]) or not re.search(r'\b(?:record|records|recording|occurs?|happens?|flashes?)\b',p.body):
        return None
    if not re.search(r'\b(?:instances|times|records|events|flashes)\b',p.question):
        return None
    a,af=core._measure(us[0]); b,bf=core._measure(us[1])
    if a==b:
        value = ns[1].value*bf/(ns[0].value*af)
        if value.denominator != 1:
            return None
        return _result(value,'Convert the observation window to the interval unit and divide',p)
    return None


def _means_and_discounts(p, ns, us, ds):
    t=p.text.lower(); asked=_asked(p)
    # Each observation belongs to a separately named observer.
    if 2 <= len(ns) <= 6 and len(set(us))==1 and asked==us[0] and not any(ds) and re.search(r'\baverage\b',p.question):
        if all(re.search(r'\b[A-Z][a-z]+ (?:sees?|saw|has|had|counted|collected|received)\s*$',p.text[:n.start]) for n in ns):
            return _result(sum((n.value for n in ns),Fraction(0))/len(ns),'({}) / {}'.format(' + '.join(_f(n) for n in ns),len(ns)),p)
    # Total savings on identical items are divided across their item count.
    if len(ns)==3 and asked=='money' and re.search(r'\boriginal price\b',p.question):
        counts=[i for i,u in enumerate(us) if u!='money']
        if len(counts)==1:
            c=counts[0]; prices=[i for i,d in enumerate(ds) if d==[us[c]] and us[i]=='money']
            if len(prices)==1:
                r=prices[0]; saving=next(i for i in range(3) if i not in (c,r))
                if (us[saving]=='money' and not ds[saving]
                        and re.search(r'\bsaved a total of\s*$',t[:ns[saving].start])):
                    return _result(ns[r].value+ns[saving].value/ns[c].value,'{} + {} / {}'.format(_f(ns[r]),_f(ns[saving]),_f(ns[c])),p)
    # A known number of flat-fee sessions plus a metered charge.
    if len(ns)==4 and re.search(r'\b(?:flat rate|base fee|base price)\b',p.body):
        variable=[i for i,d in enumerate(ds) if d==[asked] and us[i]=='money']
        if len(variable)==1:
            r=variable[0]
            for b in range(4):
                if b==r or us[b]!='money' or len(ds[b])!=1:
                    continue
                counts=[i for i in range(4) if us[i]==ds[b][0] and not ds[i]]
                if len(counts)==1:
                    c=counts[0]; totals=[i for i in range(4) if i not in (r,b,c) and us[i]=='money' and not ds[i]]
                    if len(totals)==1:
                        total=totals[0]
                        return _result((ns[total].value-ns[b].value*ns[c].value)/ns[r].value,'({} - {} * {}) / {}'.format(*(_f(ns[i]) for i in (total,b,c,r))),p)
    return None

def solve(problem):
    currencies = set(re.findall(r'[$£€]', problem.text))
    if re.search(r'\beuros?\b', problem.text, re.I):
        currencies.add('€')
    if re.search(r'\bdollars?\b', problem.text, re.I):
        currencies.add('$')
    if len(currencies) > 1:
        return None
    ns=_numbers(problem)
    if not 2 <= len(ns) <= 6 or any(n.value <= 0 or n.kind=='percent' for n in ns):
        return None
    us=[_unit(problem,n) for n in ns]
    ds=_denoms(problem,ns,us)
    for rule in (_means_and_discounts,_fees_and_savings,_periodic_event,_partitions,_rate_changes,_additive_rates,_strict_record,_work_and_production,_grid,_basket,_residual,_measured,_combined,_sharing_sum,_chain):
        result=rule(problem,ns,us,ds)
        if result is not None:
            return result
    return None
