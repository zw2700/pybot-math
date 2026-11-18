"""Explicit multi-stage rates: stocks, batches, schedules and unit prices.

The schemas join named units and account for all quantities.  A dimensional
chain is allowed only after each rate has been read from an explicit relation;
addition/subtraction require their own narrative relation.
"""
import re
from fractions import Fraction
from itertools import product

from ..numbers import format_number
from . import rates_and_unit_rates_r06_a3 as previous
from . import rates_and_unit_rates_r03_a5 as core


_TIME = previous._TIME
_STOP = previous._STOP | set(('working work delivered thrown rotten preparing '
                            'prepare doing done total all lost lose loses '
                            'each every enough entire whole living there returned damaged '
                            'waiting still only apiece equally evenly').split())


def _normal(word):
    word={'oz':'ounce', 'nights':'days', 'night':'day', 'siblings':'people',
          'sibling':'person'}.get(word,word)
    return previous._normal(word)


def _head(tail):
    words = re.findall(r"[a-z]+(?:'[a-z]+)?|[^a-z\s-]", tail.lstrip(' -'))
    kept = []
    for w in words:
        if w in _STOP or not w[0].isalpha():
            break
        w = _normal(w)
        kept.append(w)
        if w in core._MEASURES or w in ('money', 'cent', 'mph'):
            return w
        if len(kept) == 4:
            break
    return kept[-1] if kept else ''


def _unit(p, n):
    if n.kind == 'money':
        return 'money'
    tail = p.text[n.end:].lower()
    before = p.text[:n.start].lower()
    if re.match(r'\s+cans? of\b',tail):
        return 'can'
    if (re.match(r'\s+of (?:his|her|their) friends\b', tail)
            or re.match(r'\s+of them\b',tail) and re.search(r'\b(?:are|were)\s*$',before)):
        return 'person'
    if re.search(r'\b(?:at )?page\s*$', before):
        return 'page'
    tail = re.sub(r'^\s+(?:more|additional|extra|such|other|equal)\s+', ' ', tail)
    return _head(tail)


def _asked(p):
    q = p.question
    explicit = re.search(r'\bin (cents?|feet|inches|seconds?|minutes?|hours?|days?|weeks?)\b', q)
    if explicit:
        return _normal(explicit.group(1))
    fewer=re.match(r'how many fewer (.+)',q)
    if fewer:
        return _head(fewer.group(1))
    if re.match(r'how (?:long|much time)\b',q):
        return core._question(p)
    if re.search(r'\b(?:cost|price|spend|pay|earn|paid|money|lost|loss)\b', q) and not re.match(r'how many ', q):
        if re.search(r'\bcents?\b', q):
            return 'cent'
        return 'money'
    return _normal(previous._asked(p))


def _numbers(p):
    ns = []
    for n in previous._numbers(p):
        before, after = p.text[:n.start].lower(), p.text[n.end:].lower()
        if n.value == 1 and re.search(r'\b(?:one|[a-z]+)-?$', before) and re.match(r'-up\b', after):
            continue
        if n.value==1 and n.start>=len(p.body) and re.search(r'\b(?:in|per)\s*$',before):
            continue
        label=re.match(r'\s+([a-z]+) charges?\b',after)
        if n.value==1 and label and re.search(r'\b(?:another|other) '+re.escape(label.group(1))+r'\b',after):
            # "One seller ... another seller" labels two observations;
            # it is not an extra purchased item in a unit-price comparison.
            continue
        ns.append(n)
    return ns


def _denoms(p, ns, us):
    ds = previous._denoms(p, ns, us)
    t = p.text.lower()
    for i, n in enumerate(ns):
        before = re.split(r'[.!?;](?:\s|$)', t[:n.start])[-1]
        after = t[n.end:ns[i+1].start if i+1 < len(ns) else len(t)]
        # Packaging: "boxes of N items each" and "N items in a crate".
        m = re.search(r'\b([a-z]+s) (?:of|that (?:could|can) (?:fit|hold))\s*$', before)
        if m and re.search(r'\beach\b', after):
            ds[i] = [_normal(m.group(1))]
        m = re.match(r'\s+[a-z]+\s+in (?:a|an|each) ([a-z]+)\b', after)
        if m:
            ds[i] = [_normal(m.group(1))]
        m = re.search(r'\beach ([a-z]+) can (?:feed|serve|hold|contain)\s*(?:up to\s*)?$', before)
        if m:
            ds[i] = [_normal(m.group(1))]
        if re.search(r'\b(?:each of them|they each|each person)[^.!?;]*?\b(?:eat|have|ordered|gets?|receives?)\s*$', before):
            ds[i] = ['person']
        if re.search(r'\beach (?:eat|eats|have|has|ordered)\s*$', before):
            ds[i] = ['person']
        m = re.search(r'\beach ([a-z]+)\s*$', before)
        if (m and _normal(m.group(1)) not in _STOP
                and _normal(m.group(1)) in us+[_asked(p)]
                and not re.search(r'\b(?:every|each)\b', after)):
            # "feeds each animal N items": the animal is nearer than an
            # earlier every-day phrase.
            ds[i] = [_normal(m.group(1))]
        if re.match(r'\s+miles? to the gallon\b',after):
            ds[i] = ['gallon']
        if us[i] in _TIME:
            interval=re.search(r'\b(?:an?|each) ([a-z]+) every\s*$',before)
            if interval:
                ds[i]=[_normal(interval.group(1))]
        if n.kind=='money':
            item=re.match(r'\s+per person for (?:a|an) ([a-z]+)\b',after)
            if item:
                ds[i]=[_normal(item.group(1))]
        denom=re.match(r'\s+[a-z]+ to (?:a|an|each) ([a-z]+)\b',after)
        if denom:
            ds[i]=[_normal(denom.group(1))]
        package=re.match(r'-([a-z]+)[ -]+([a-z]+)\b',after)
        if package and _normal(package.group(1)) in core._MEASURES:
            ds[i]=[_normal(package.group(2))]
        if i and n.kind=='money' and not ds[i]:
            local=t[ns[i-1].end:n.start]
            if re.match(r'-[a-z]+\s+[a-z]+\b[^.!?;]*\bcosts?\s*$',local) and ds[i-1]:
                ds[i]=list(ds[i-1])
        if i and n.kind=='money' and ds[i-1]:
            local=t[ns[i-1].end:n.start]
            if re.match(r'-[a-z]+\s+[a-z]+\b[^.!?;]*\bfor\s*$',local) and re.match(r'\s+each\b',after):
                ds[i]=list(ds[i-1])
        if i and re.search(r'\beach one of which is\s*$',before):
            ds[i]=[us[i-1]]
        m=re.search(r'\beach ([a-z]+) at\s*$',before)
        if m and us[i] in ('money','cent'):
            ds[i]=[_normal(m.group(1))]
        subject=re.search(r'\b([a-z]+s) contain\s*$',before)
        if subject and re.match(r'\s+[a-z]+\s+each\b',after):
            ds[i]=[_normal(subject.group(1))]
        front=re.search(r'\bfor every ([a-z]+), (?:he|she|they|[a-z]+) (?:uses?|used|needs?)\s*$',before)
        if front:
            ds[i]=[_normal(front.group(1))]
        if re.match(r'\s+cents? per can\b',after):
            ds[i]=['can']
        if n.kind=='money' and re.search(r'\bto raise\s*$',before) and not re.search(r'\b(?:per|each|every)\b',after):
            ds[i]=[]
        price_subject=re.search(r'\b(?:sells?|selling|and) ([a-z]+(?: [a-z]+){0,2}?) for\s*$',before)
        if n.kind=='money' and price_subject and re.match(r'\s+each\b',after):
            ds[i]=[_head(price_subject.group(1))]
        removed=re.search(r'\bfrom each ([a-z]+)\b',after)
        if removed:
            ds[i]=[_normal(removed.group(1))]
        # N dollars from each of M donors: the denominator is the donor,
        # not the unit of the preceding money amount.
        if i+1 < len(ns) and re.search(r'\bfrom each of (?:his |her |their |the )?$', after):
            ds[i] = [us[i+1]]
            ds[i+1] = []
        # A contextual weekday/weekend denotes the same once-weekly cycle.
        if ds[i] == ['weekend']:
            ds[i] = ['week']
    return ds


def _f(n):
    return format_number(n.value if hasattr(n, 'value') else n)


def _result(p, value, expr):
    if value < 0:
        return None
    label = 'Amount in dollars' if _asked(p) == 'money' else 'Calculation'
    if '£' in p.text:
        label = label.replace('dollars', 'pounds')
    if '€' in p.text or re.search(r'\beuros?\b',p.text,re.I):
        label = label.replace('dollars', 'euros')
    # State the commodity and currency, so the answer is readable as a price
    # for this purchase, including when the shared noun reader misses an
    # apostrophe or an abbreviated measurement unit.
    asked=_asked(p)
    currency=label.rsplit(' ',1)[-1] if asked=='money' else ('euros' if '€' in p.text else 'dollars')
    if asked=='money':
        commodities=[]
        for n in _numbers(p):
            unit=_unit(p,n)
            if unit in _TIME | {'money','cent','person',''}:
                continue
            # Preserve the source noun's spelling and plural in the prose.
            words=re.findall(r"[a-z]+(?:'[a-z]+)?",p.text[n.end:n.end+60].lower())[:5]
            surface=next((w for w in words if _normal(w)==unit),unit)
            if surface not in commodities:
                commodities.append(surface)
        if commodities:
            label+=' for '+', '.join(commodities[:3])
    unit=' '+currency if asked=='money' else (' cents' if asked=='cent' else '')
    equivalent='Equivalent to {} {}. '.format(_f(value/100),currency) if asked=='cent' else ''
    return value, '{}{}: {} works out to {}{}.'.format(equivalent,label,expr,_f(value),unit)


def _convert(value, source, dest):
    a, af = core._measure(source)
    b, bf = core._measure(dest)
    return value*af/bf if a == b else None


def _weighted_prices(p, ns, us, ds):
    """Two disjoint purchases, with an explicit count and unit price each."""
    if len(ns) != 4 or _asked(p) != 'money' or not re.search(r'\baverage\b', p.question):
        return None
    rates = [i for i in range(4) if us[i] == 'money' and len(ds[i]) == 1]
    counts = [i for i in range(4) if i not in rates]
    if len(rates) != 2 or len(counts) != 2 or any(ds[i] for i in counts):
        return None
    # Associate each postposed price with the immediately preceding count.
    pairs = [(i-1, i) for i in rates if i-1 in counts and ds[i] == [us[i-1]]]
    if len(pairs) != 2 or len({a for a, b in pairs}) != 2:
        return None
    if len({us[a] for a,b in pairs}) != 1:
        return None
    a,b = pairs[0]; c,d = pairs[1]
    value = (ns[a].value*ns[b].value+ns[c].value*ns[d].value)/(ns[a].value+ns[c].value)
    return _result(p, value, '({} * {} + {} * {}) / ({} + {})'.format(
        _f(ns[a]), _f(ns[b]), _f(ns[c]), _f(ns[d]), _f(ns[a]), _f(ns[c])))


def _net_savings(p, ns, us, ds):
    if len(ns) != 4 or us != ['money']*4 or _asked(p) not in _TIME:
        return None
    t = p.text.lower(); period = _asked(p)
    rates = [i for i,d in enumerate(ds) if d == [period]]
    stocks = [i for i,d in enumerate(ds) if not d]
    if len(rates) != 2 or len(stocks) != 2:
        return None
    incomes = [i for i in rates if re.search(r'\b(?:give|gives|earn|earns|gets?|receives?)\s+(?:(?:him|her|them)\s+)?$', t[:ns[i].start])]
    outgoings = [i for i in rates if re.search(r'\b(?:spends?|pays?|uses?)\s*$', t[:ns[i].start])]
    goals = [i for i in stocks if re.search(r'\b(?:costs?|price of|needs?)\s*$', t[:ns[i].start])]
    if len(incomes) != 1 or len(outgoings) != 1 or len(goals) != 1:
        return None
    goal = goals[0]; saved = next(i for i in stocks if i != goal)
    if not re.search(r'\b(?:savings|saved|already|has|have)\b', core._sentence(t, ns[saved])):
        return None
    income, cost = incomes[0], outgoings[0]
    net = ns[income].value-ns[cost].value
    if net <= 0:
        return None
    return _result(p, (ns[goal].value-ns[saved].value)/net,
                   '({} - {}) / ({} - {})'.format(*(_f(ns[i]) for i in (goal,saved,income,cost))))


def _repack_loss(p, ns, us, ds):
    if len(ns) != 4 or not re.search(r'\b(?:remaining|rest)\b', p.body):
        return None
    t = p.text.lower(); asked = _asked(p)
    target = [i for i,d in enumerate(ds) if d == [asked]]
    if len(target) != 1:
        return None
    r = target[0]
    removed = [i for i in range(4) if i != r and us[i] == us[r] and not ds[i]
               and re.search(r'\b(?:rotten|thrown away|lost|removed|damaged|broken)\b', core._sentence(t,ns[i]))]
    if len(removed) != 1:
        return None
    loss = removed[0]; a,b = [i for i in range(4) if i not in (r,loss)]
    if ds[a] != [us[b]] or us[a] != us[r] or ds[b]:
        a,b = b,a
    if ds[a] != [us[b]] or us[a] != us[r] or ds[b]:
        return None
    return _result(p, (ns[a].value*ns[b].value-ns[loss].value)/ns[r].value,
                   '({} * {} - {}) / {}'.format(*(_f(ns[i]) for i in (a,b,loss,r))))


def _remaining_budget(p, ns, us, ds):
    if len(ns) != 4 or not re.search(r'\b(?:rest|left|budget|remaining|afford)\b', p.text.lower()):
        return None
    t = p.text.lower(); asked = _asked(p)
    # Known purchase + amount left for a second purchase at a stated price.
    if us.count('money') == 3:
        rates = [i for i,d in enumerate(ds) if us[i] == 'money' and len(d) == 1]
        totals = [i for i in range(4) if us[i] == 'money' and not ds[i]]
        counts = [i for i in range(4) if us[i] != 'money' and not ds[i]]
        if len(rates)==2 and len(totals)==1 and len(counts)==1:
            c=counts[0]; total=totals[0]
            # Read the purchased commodity, retaining modifiers: two prices
            # "per packet" alone do not identify which price the count uses.
            commodity = re.match(r'\s+[a-z]+\s+of\s+([a-z ]+?)(?:,|\s+and|\.|$)', t[ns[c].end:])
            known=[i for i in rates if ds[i]==[us[c]]] if len(set(tuple(ds[i]) for i in rates))==2 else []
            for i in rates:
                subject=re.search(r'(?:\b(?:sells?|selling)|\band)\s+([a-z ]+?)\s+for\s*$',t[:ns[i].start])
                if (commodity and subject and commodity.group(1).strip()==subject.group(1).strip()
                        and ds[i]==[us[c]]):
                    if i not in known:
                        known.append(i)
            if len(known)==1:
                r=known[0]; other=next(i for i in rates if i!=r)
                if ds[other]==[asked] and re.search(r'\bbuy\b',p.question):
                    v=(ns[total].value-ns[c].value*ns[r].value)/ns[other].value
                    if re.search(r'\b(?:can|could|as many)\b',p.question):
                        v=Fraction(v.numerator//v.denominator)
                    return _result(p,v,'({} - {} * {}) / {}'.format(*(_f(ns[i]) for i in (total,c,r,other))))
    # Budget minus a known line item, divided across the other item count.
    if us.count('money')==2 and asked=='money':
        rates=[i for i,d in enumerate(ds) if us[i]=='money' and len(d)==1]
        totals=[i for i in range(4) if us[i]=='money' and not ds[i]]
        if len(rates)==len(totals)==1:
            r,total=rates[0],totals[0]
            cs=[i for i in range(4) if us[i]!='money' and not ds[i]]
            known=[i for i in cs if ds[r]==[us[i]]]
            if len(cs)==2 and len(known)==1 and re.search(r'\bbudget\b',core._sentence(t,ns[total])):
                c=known[0]; other=next(i for i in cs if i!=c)
                m=re.search(r'\beach ([a-z -]+?)(?:\?|$)',p.question)
                if m and _head(m.group(1))==us[other]:
                    return _result(p,(ns[total].value-ns[c].value*ns[r].value)/ns[other].value,
                                   '({} - {} * {}) / {}'.format(*(_f(ns[i]) for i in (total,c,r,other))))
    return None


def _sum_costs(p, ns, us, ds):
    if len(ns)!=3 or us!=['money']*3:
        return None
    asked=_asked(p); rates=[i for i,d in enumerate(ds) if d==[asked]]
    if len(rates)!=1 or not re.search(r'\b(?:total|altogether)\b',p.question):
        return None
    r=rates[0]; a,b=[i for i in range(3) if i!=r]
    if ds[a] or ds[b] or not re.search(r'\b(?:both|same)\b',p.body):
        return None
    if not re.search(r'\b(?:spent|paid|spends?)\b',p.body):
        return None
    return _result(p,(ns[a].value+ns[b].value)/ns[r].value,
                   '({} + {}) / {}'.format(*(_f(ns[i]) for i in (a,b,r))))


def _equal_shares(p, ns, us, ds):
    t=p.text.lower(); q=p.question; asked=_asked(p)
    if not re.search(r'\b(?:equally|evenly|equal amount)\b',t) or not re.search(r'\b(?:each|per)\b',q):
        return None
    # Two people combine their money; one has a stated difference from the other.
    if len(ns)==2 and us==['money','money'] and asked=='money' and not any(ds):
        diff=[i for i in range(2) if re.match(r'\s+more (?:money )?than\b',t[ns[i].end:])]
        if len(diff)==1 and re.search(r'\b(?:combine|share)\b',p.body):
            d=diff[0]; a=1-d
            # The owner of the larger balance must be the owner named before
            # the difference; names are variables, never lexical triggers.
            owner=re.search(r'\b([a-z]+) has\s*$',t[:ns[d].start])
            balance=re.search(r'\b([a-z]+) has\s*$',t[:ns[a].start])
            if owner and balance and owner.group(1)==balance.group(1):
                return _result(p,(2*ns[a].value-ns[d].value)/2,
                               '(2 * {} - {}) / 2'.format(_f(ns[a]),_f(ns[d])))
    # Equal card/item shares include the host as well as N other participants.
    if len(ns)==3 and us[0]==us[1]==asked and not any(ds):
        if re.search(r'\b(?:adds?|additional|more)\b',t[ns[0].end:ns[1].end]) and re.search(r'\b(?:herself|himself|themself|myself) and\s*$',t[:ns[2].start]):
            if re.match(r'\s+(?:other )?(?:players?|people|friends?|persons?)\b',t[ns[2].end:]):
                return _result(p,(ns[0].value+ns[1].value)/(ns[2].value+1),
                               '({} + {}) / ({} + 1)'.format(*(_f(n) for n in ns)))
    return None


def _two_legs(p, ns, us, ds):
    asked=_asked(p)
    if len(ns)!=4 or not re.search(r'\b(?:trip|travel|journey|destination)\b',p.body):
        return None
    rates=[i for i,d in enumerate(ds) if len(d)==1 and (d[0] in _TIME or d[0]==asked)]
    stocks=[i for i in range(4) if not ds[i]]
    if len(rates)!=2 or len(stocks)!=2 or len(set(us))!=1:
        return None
    # Ordered legs are stated either as distance,speed,distance,speed or
    # distance,distance,speed,speed. Other layouts are ambiguous.
    if rates not in ([1,3],[2,3]) or re.search(r'\b(?:return|round[ -]trip|back|half|remaining)\b',p.body):
        return None
    a,b=stocks; r,s=rates
    time1=_convert(ns[a].value/ns[r].value,ds[r][0],asked)
    time2=_convert(ns[b].value/ns[s].value,ds[s][0],asked)
    if time1 is not None and time2 is not None:
        return _result(p,time1+time2,'{} / {} + {} / {} (in {})'.format(_f(ns[a]),_f(ns[r]),_f(ns[b]),_f(ns[s]),asked))
    return None


def _capital(p, ns, us, ds):
    if len(ns)!=3 or not re.search(r'\b(?:recover|recovers)\b.*\b(?:capital|cost|investment)\b',p.question):
        return None
    asked=_asked(p)
    counts=[i for i in range(3) if us[i]==asked and not ds[i]]
    cash=[i for i in range(3) if us[i] in ('money','cent')]
    if len(counts)!=1 or len(cash)!=2 or not re.search(r'\bleft\b',p.question):
        return None
    rates=[i for i in cash if re.search(r'\bsell each [a-z]+ for\s*$',p.text[:ns[i].start].lower())]
    if len(rates)!=1:
        return None
    r=rates[0]; total=next(i for i in cash if i!=r); c=counts[0]
    cost=_convert(ns[total].value,us[total],us[r])
    if cost is not None:
        return _result(p,ns[c].value-cost/ns[r].value,'{} - {} / {}'.format(_f(ns[c]),_f(cost),_f(ns[r])))
    return None


def _production_batch(p, ns, us, ds):
    """A group stock processed at N items every T units of time."""
    if len(ns)!=4 or _asked(p) not in _TIME:
        return None
    t=p.text.lower()
    a,b,r,d=range(4)
    if ds[b]!=[us[a]] or ds[a] or ds[r] or ds[d] or us[b]!=us[r] or us[d] not in _TIME:
        return None
    if not re.search(r'\b(?:every|in)\s*$',t[ns[r].end:ns[d].start]):
        return None
    duration=_convert(ns[d].value,us[d],_asked(p))
    if duration is not None:
        return _result(p,ns[a].value*ns[b].value*duration/ns[r].value,
                       '{} * {} * {} / {}'.format(_f(ns[a]),_f(ns[b]),_f(duration),_f(ns[r])))
    return None


def _scheduled_work(p, ns, us, ds):
    """Total output / (output per work-hour * work-hours per day)."""
    if len(ns)!=3 or _asked(p) not in _TIME:
        return None
    if re.search(r'\b(?:left|remaining|twice|half|except|weekdays|weekends|then|more)\b',p.text.lower()):
        return None
    for a in range(3):
        if us[a] not in _TIME or len(ds[a])!=1 or ds[a][0] not in _TIME:
            continue
        for r in range(3):
            if r==a or ds[r]!=[us[a]]:
                continue
            total=next(i for i in range(3) if i not in (a,r))
            if ds[total] or us[total]!=us[r]:
                continue
            periods=ns[total].value/(ns[r].value*ns[a].value)
            value=_convert(periods,ds[a][0],_asked(p))
            if value is not None:
                return _result(p,value,'{} / ({} * {}) (converted to {})'.format(_f(ns[total]),_f(ns[r]),_f(ns[a]),_asked(p)))
    return None


def _group_plus_single(p, ns, us, ds):
    if len(ns)!=4:
        return None
    t=p.text.lower(); asked=_asked(p)
    caps=[i for i,d in enumerate(ds) if d==[asked]]
    if len(caps)!=1:
        return None
    cap=caps[0]; groups=[i for i in range(4) if us[i]=='person' and not ds[i]]
    if len(groups)!=1:
        return None
    g=groups[0]; a,b=[i for i in range(4) if i not in (cap,g)]
    if us[a]!=us[b] or us[a]!=us[cap] or ds[a] or ds[b]!=['person']:
        a,b=b,a
    if us[a]!=us[b] or us[a]!=us[cap] or ds[a] or ds[b]!=['person']:
        return None
    if not re.search(r'\b(?:all|total|altogether)\b',p.question):
        return None
    return _result(p,(ns[a].value+ns[g].value*ns[b].value)/ns[cap].value,
                   '({} + {} * {}) / {}'.format(*(_f(ns[i]) for i in (a,g,b,cap))))


def _batch_price(p, ns, us, ds):
    """An explicit price for a batch, with demand per person and headcount."""
    if len(ns)!=4 or _asked(p)!='money':
        return None
    cash=[i for i,u in enumerate(us) if u=='money']
    group=[i for i,u in enumerate(us) if u=='person' and not ds[i]]
    if len(cash)!=1 or len(group)!=1:
        return None
    price,g=cash[0],group[0]; a,b=[i for i in range(4) if i not in (price,g)]
    demand=[i for i in (a,b) if ds[i]==['person']]
    if len(demand)!=1:
        return None
    d=demand[0]; size=next(i for i in (a,b) if i!=d)
    if us[d]!=us[size] or ds[size] or ds[price]:
        return None
    t=p.text.lower()
    # The batch quantity and batch price must be bound by a local price clause.
    middle=t[min(ns[size].end,ns[price].end):max(ns[size].start,ns[price].start)]
    if not re.search(r'\b(?:for|to make)\s*$',middle) or re.search(r'[.!?;]',middle):
        return None
    return _result(p,ns[d].value*ns[g].value*ns[price].value/ns[size].value,
                   '{} * {} * {} / {}'.format(*(_f(ns[i]) for i in (d,g,price,size))))


def _speed_difference(p, ns, us, ds):
    if len(ns)!=3 or not re.search(r'\b(?:farther|further|more)\b',p.question):
        return None
    if us[0]!=us[2] or us[1] not in _TIME or len(ds[2])!=1 or ds[2][0] not in _TIME or ds[0] or ds[1]:
        return None
    t=p.text.lower()
    if not re.search(r'\bin\s*$',t[ns[0].end:ns[1].start]) or not re.search(r'\bin (?:an?|one) '+ds[2][0]+r'\b',p.question):
        return None
    duration=_convert(Fraction(1),ds[2][0],us[1])
    if duration is not None and _asked(p)==us[0]:
        return _result(p,ns[0].value*duration/ns[1].value-ns[2].value,
                       '{} * {} / {} - {}'.format(_f(ns[0]),_f(duration),_f(ns[1]),_f(ns[2])))
    return None


def _daily_consumption(p, ns, us, ds):
    if len(ns)!=4 or not re.search(r'\b(?:daily|each day|every day|bedtime)\b',p.body):
        return None
    asked=_asked(p)
    caps=[i for i,d in enumerate(ds) if d==[asked]]
    days=[i for i,u in enumerate(us) if u=='day' and not ds[i]]
    if len(caps)!=1 or len(days)!=1:
        return None
    cap,day=caps[0],days[0]; a,b=[i for i in range(4) if i not in (cap,day)]
    if us[a]!=us[b] or us[a]!=us[cap] or any(ds[i] not in ([],['day'],['snack']) for i in (a,b)):
        return None
    if not re.search(r'\b(?:eats?|consumes?|drinks?|gives?)\b',p.body):
        return None
    v=(ns[a].value+ns[b].value)*ns[day].value/ns[cap].value
    if re.search(r'\b(?:need|enough)\b',p.question):
        v=Fraction(-(-v.numerator//v.denominator))
    return _result(p,v,'({} + {}) * {} / {}'.format(*(_f(ns[i]) for i in (a,b,day,cap))))


def _melted_volume(p, ns, us, ds):
    """Conserve rectangular-solid volume when recasting identical objects."""
    if len(ns)!=5 or not re.search(r'\b(?:melt|melts|melted)\b',p.body) or not re.search(r'\bvolume\b',p.body):
        return None
    if us[0]!=us[1] or us[0]!=us[2] or us[0]!=us[4] or us[0] not in ('centimeter','meter','inch','foot'):
        return None
    t=p.text.lower()
    if not all(re.fullmatch(r'\s*[a-z]+\s+by\s*',t[ns[i].end:ns[i+1].start]) for i in (0,1)):
        return None
    m=re.search(r'\beach (.+?) has a volume of\s*$',t[:ns[4].start])
    if not m or _head(m.group(1))!=_asked(p) or not re.match(r'\s+cubic\b',t[ns[4].end:]):
        return None
    return _result(p,ns[0].value*ns[1].value*ns[2].value*ns[3].value/ns[4].value,
                   '{} * {} * {} * {} / {}'.format(*(_f(n) for n in ns)))


def _growth(p, ns, us, ds):
    if len(ns)!=3 or not re.search(r'\b(?:grew|grows?|growth|gained|increased)\b',p.body):
        return None
    asked=_asked(p)
    rates=[i for i,d in enumerate(ds) if len(d)==1]
    if len(rates)!=1:
        return None
    r=rates[0]; duration=[i for i in range(3) if us[i]==ds[r][0] and not ds[i]]
    if len(duration)!=1:
        return None
    d=duration[0]; stock=next(i for i in range(3) if i not in (r,d))
    if us[stock]!=us[r] or ds[stock]:
        return None
    value=_convert(ns[stock].value+ns[r].value*ns[d].value,us[r],asked)
    if value is not None:
        return _result(p,value,'{} + {} * {} (converted to {})'.format(_f(ns[stock]),_f(ns[r]),_f(ns[d]),asked))
    return None


def _host_group(p, ns, us, ds):
    """A named host and N friends, each with the same requirements."""
    if len(ns)!=3:
        return None
    t=p.text.lower(); asked=_asked(p)
    groups=[i for i,u in enumerate(us) if u=='person' and not ds[i]]
    if len(groups)!=1:
        return None
    g=groups[0]
    if not re.search(r'\band\s*$',t[:ns[g].start]) or not re.match(r'\s+(?:of (?:his|her|their) |(?:his|her|their) )?friends\b',t[ns[g].end:]):
        return None
    a,b=[i for i in range(3) if i!=g]
    if ds[a]==['person'] and ds[b]==[asked] and us[a]==us[b]:
        v=(ns[g].value+1)*ns[a].value/ns[b].value
        if re.search(r'\b(?:should|need|order|must)\b',p.question):
            v=Fraction(-(-v.numerator//v.denominator))
        return _result(p,v,'({} + 1) * {} / {}'.format(_f(ns[g]),_f(ns[a]),_f(ns[b])))
    # A first course has a known per-person price. The rest of the total bill
    # buys exactly one second course per person.
    if asked=='money' and us[a]==us[b]=='money' and ds[a]==['person'] and not ds[b]:
        later=t[ns[a].end:]
        if re.search(r'\b(?:afterwards|afterward|then)\b[^.!?]*\beach (?:had|ordered|bought)\b',later):
            return _result(p,ns[b].value/(ns[g].value+1)-ns[a].value,
                           '{} / ({} + 1) - {}'.format(_f(ns[b]),_f(ns[g]),_f(ns[a])))
    return None


def _interval_difference(p, ns, us, ds):
    if len(ns)!=3 or len(set(us))!=1 or us[0] not in _TIME or any(ds):
        return None
    t=p.text.lower()
    if not re.search(r'\bhow many more\b.*\bthan\b',p.question):
        return None
    if not all(re.search(r'\bevery\s*$',t[:ns[i].start]) for i in (1,2)):
        return None
    if not re.search(r'\b(?:works?|working|lasts?|duration)\b',t[:ns[0].start]):
        return None
    # The query's first event must be the first event in the narrative.
    first=re.search(r'\b(?:an?|the) (.+?) every\s*$',t[ns[0].end:ns[1].start])
    if not first or first.group(1).strip() not in p.question:
        return None
    return _result(p,ns[0].value/ns[1].value-ns[0].value/ns[2].value,
                   '{} / {} - {} / {}'.format(_f(ns[0]),_f(ns[1]),_f(ns[0]),_f(ns[2])))


def _geometric_change(p, ns, us, ds):
    t=p.text.lower()
    change=re.search(r'\b(doubles?|halved|halves|triples?) every\s*$',t[:ns[1].start]) if len(ns)>=2 else None
    if change is None or len(ns) not in (2,3) or us[1] not in _TIME:
        return None
    if _asked(p)!=us[0]:
        return None
    factor=Fraction(1,2) if change.group(1) in ('halved','halves') else Fraction(3 if change.group(1).startswith('triple') else 2)
    if len(ns)==2:
        horizon=re.search(r'\b(?:end of|after|in) (?:a|an|one) (day|week|month|year)\b',p.question)
        if not horizon:
            return None
        elapsed=_convert(Fraction(1),horizon.group(1),us[1])
    else:
        unit=us[2]
        if not unit and re.search(r'\bwhen [a-z]+ is\s*$',t[:ns[2].start]) and us[1]=='year':
            unit='year'
        elapsed=_convert(ns[2].value,unit,us[1])
    if elapsed is None:
        return None
    cycles=elapsed/ns[1].value
    if cycles.denominator!=1 or not 0<=cycles<=100:
        return None
    return _result(p,ns[0].value*factor**int(cycles),'{} * {}^{}'.format(_f(ns[0]),_f(factor),_f(cycles)))


def _unit_savings(p, ns, us, ds):
    if len(ns)!=3 or not re.search(r'\bsave\b',p.question) or not re.search(r'\bper [a-z]+',p.question):
        return None
    money=[i for i,u in enumerate(us) if u in ('money','cent')]
    if len(money)!=2:
        return None
    count=next(i for i in range(3) if i not in money)
    t=p.text.lower(); individual=[i for i in money if re.search(r'\bprice per [a-z ]+ is\s*$',t[:ns[i].start])]
    if len(individual)!=1:
        return None
    r=individual[0]; pack=next(i for i in money if i!=r)
    if not re.search(r'\bcontains?\s*$',t[:ns[count].start]):
        return None
    a=_convert(ns[r].value,us[r],_asked(p)); b=_convert(ns[pack].value,us[pack],_asked(p))
    if a is not None and b is not None:
        return _result(p,a-b/ns[count].value,'{} - {} / {}'.format(_f(a),_f(b),_f(ns[count])))
    return None


def _observed_progress(p, ns, us, ds):
    if len(ns)!=3 or us!=['page']*3 or any(ds) or _asked(p) not in _TIME:
        return None
    t=p.text.lower()
    if not re.search(r'\b(?:now|currently)\b[^.!?]*$',t[:ns[1].start]):
        return None
    ago=re.search(r'\b(?:an?|one) (hour|minute|day) ago\b[^.!?]*$',t[:ns[2].start])
    if not ago or not re.search(r'\b(?:steady|constant) pace\b',p.body):
        return None
    delta=ns[1].value-ns[2].value
    elapsed=_convert(Fraction(1),ago.group(1),_asked(p))
    if delta>0 and elapsed is not None:
        return _result(p,(ns[0].value-ns[1].value)*elapsed/delta,
                       '({} - {}) / ({} - {}) * {}'.format(_f(ns[0]),_f(ns[1]),_f(ns[1]),_f(ns[2]),_f(elapsed)))
    return None


def _annual_rate_goal(p, ns, us, ds):
    if len(ns)!=2 or us!=['money','money'] or not re.search(r'\bmore\b',p.question):
        return None
    t=p.text.lower()
    period=re.match(r'\s+(?:worth of [a-z]+ )?(?:every|per|each) (month|week|day)\b',t[ns[0].end:])
    goal=re.match(r'\s+in (?:an?|one) (?:entire |whole )?(year|month|week)\b',t[ns[1].end:])
    if not period or not goal or not re.search(r'\bper '+period.group(1)+r'\b',p.question):
        return None
    elapsed=_convert(Fraction(1),goal.group(1),period.group(1))
    if elapsed is not None:
        return _result(p,ns[1].value/elapsed-ns[0].value,
                       '{} / {} - {}'.format(_f(ns[1]),_f(elapsed),_f(ns[0])))
    return None


def _proportional_mixture(p, ns, us, ds):
    if len(ns)!=4 or us[0]!=us[2] or us[0]!=us[3] or us[1]!='time':
        return None
    t=p.text.lower()
    if not re.match(r'\s+times as much\b',t[ns[1].end:]) or ds[3]!=[_asked(p)] or any(ds[i] for i in (0,1,2)):
        return None
    if not re.search(r'\b(?:adds?|mixes?|combines?)\b',t[:ns[0].start]) or not re.search(r'\b(?:divides?|pours?|packs?)\b',t[ns[2].end:ns[3].start]):
        return None
    return _result(p,(ns[0].value*(1+ns[1].value)+ns[2].value)/ns[3].value,
                   '({} * (1 + {}) + {}) / {}'.format(*(_f(n) for n in ns)))


def _needed_purchase(p, ns, us, ds):
    """A resource requirement determines item count, price and remaining cash."""
    if len(ns)!=4 or _asked(p)!='money' or not re.search(r'\bleft\b',p.question):
        return None
    t=p.text.lower()
    if us[0]!=us[3] or us[1:3]!=['money','money']:
        return None
    subject=re.search(r'\b([a-z]+s) (?:have|contain|provide)\s*$',t[:ns[0].start])
    if not subject or not re.search(r'\band costs?\s*$',t[ns[0].end:ns[1].start]):
        return None
    if not re.match(r'\s+each\b',t[ns[1].end:]) or not re.search(r'\b(?:needs?|requires?)\b',t[ns[2].end:ns[3].start]):
        return None
    return _result(p,ns[2].value-ns[3].value/ns[0].value*ns[1].value,
                   '{} - {} / {} * {}'.format(*(_f(ns[i]) for i in (2,3,0,1))))


def _area_groups(p, ns, us, ds):
    if len(ns)!=5 or us[0]!=us[2] or us[0]!=us[4] or us[3]!=_asked(p):
        return None
    t=p.text.lower()
    if not all(re.match(r'\s+square\b',t[ns[i].end:]) for i in (0,2,4)):
        return None
    group=re.search(r'\bin each ([a-z]+)\b[^.!?]*$',t[:ns[2].start])
    if not group or _normal(group.group(1))!=us[1] or not re.search(r'\bcan cover\s*$',t[:ns[4].start]):
        return None
    if not re.search(r'\b'+re.escape(us[3])+r'\b',t[ns[3].end:ns[4].start]):
        return None
    return _result(p,(ns[0].value+ns[1].value*ns[2].value)*ns[3].value/ns[4].value,
                   '({} + {} * {}) * {} / {}'.format(*(_f(n) for n in ns)))


def _processing_time(p, ns, us, ds):
    if len(ns)!=5 or _asked(p) not in _TIME:
        return None
    # Input per batch; observed picking time and input; fixed processing time;
    # requested batch count. Both stages are required exactly once.
    if len(ds[0])!=1 or us[1] not in _TIME or us[0]!=us[2] or us[3] not in _TIME or ds[0]!=[us[4]] or any(ds[i] for i in (1,2,3,4)):
        return None
    t=p.text.lower()
    if not re.search(r'\bto (?:pick|collect|gather|prepare|produce|make)\s*$',t[ns[1].end:ns[2].start]):
        return None
    if not re.match(r'\s+[a-z]+ to (?:make|cook|process|bake|finish)\b',t[ns[3].end:]):
        return None
    a=_convert(ns[1].value,us[1],_asked(p)); b=_convert(ns[3].value,us[3],_asked(p))
    if a is not None and b is not None:
        return _result(p,ns[0].value*ns[4].value*a/ns[2].value+b,
                       '{} * {} * {} / {} + {}'.format(_f(ns[0]),_f(ns[4]),_f(a),_f(ns[2]),_f(b)))
    return None


def _time_ratio(p, ns, us, ds):
    if len(ns)!=3 or any(u not in _TIME for u in us):
        return None
    t=p.text.lower()
    middle=t[ns[0].end:ns[1].start]
    if not re.search(r'\bfor every\s*$',middle) or re.search(r'[.!?;]',middle):
        return None
    if not re.match(r'how (?:long|much time)',p.question):
        return None
    elapsed=_convert(ns[2].value,us[2],us[1])
    if elapsed is None:
        return None
    value=ns[0].value*elapsed/ns[1].value
    explicit=re.search(r'\bin (seconds?|minutes?|hours?|days?)\b',p.question)
    if explicit:
        value=_convert(value,us[0],_normal(explicit.group(1)))
    if value is not None:
        return _result(p,value,'{} * {} / {}'.format(_f(ns[0]),_f(elapsed),_f(ns[1])))
    return None


def _interval_consumption(p, ns, us, ds):
    if len(ns)!=3 or us[1] not in _TIME or len(ds[1])!=1 or ds[1]!=ds[2]:
        return None
    if _asked(p) not in _TIME or not re.search(r'\b(?:drink|consume|use|empty|finish)\b',p.question):
        return None
    total=_convert(ns[0].value,us[0],us[2])
    time=_convert(ns[1].value,us[1],_asked(p))
    if total is not None and time is not None:
        return _result(p,total/ns[2].value*time,'{} / {} * {}'.format(_f(total),_f(ns[2]),_f(time)))
    return None


def _fraction_duration(p, ns, us, ds):
    if len(ns)!=3 or us[0] not in _TIME or us[2] not in _TIME or not 0<ns[1].value<1:
        return None
    t=p.text.lower()
    if not re.match(r'\s+of (?:this|that|the) time\b',t[ns[1].end:]):
        return None
    event=re.search(r'\b(?:a|an) ([a-z]+) every\s*$',t[:ns[2].start])
    if not event or _normal(event.group(1))!=_asked(p):
        return None
    elapsed=_convert(ns[0].value,us[0],us[2])
    if elapsed is not None:
        return _result(p,elapsed*ns[1].value/ns[2].value,
                       '{} * {} / {}'.format(_f(elapsed),_f(ns[1]),_f(ns[2])))
    return None


def _two_measured_rates(p, ns, us, ds):
    if len(ns)!=4 or us[0]!=us[2] or us[1] not in _TIME or us[3] not in _TIME or any(ds):
        return None
    t=p.text.lower()
    if not all(re.fullmatch(r'\s+[a-z]+\s+in\s+',t[ns[i].end:ns[i+1].start]) for i in (0,2)):
        return None
    period=re.search(r'\bin (?:an?|one) (hour|minute|day)\b',p.question)
    if not period or not re.search(r'\b(?:more|farther|further)\b',p.question) or _asked(p)!=us[0]:
        return None
    a=_convert(ns[1].value,us[1],period.group(1));b=_convert(ns[3].value,us[3],period.group(1))
    if a is not None and b is not None:
        return _result(p,abs(ns[2].value/b-ns[0].value/a),
                       '|{} / {} - {} / {}|'.format(_f(ns[2]),_f(b),_f(ns[0]),_f(a)))
    return None


def _two_products(p, ns, us, ds):
    if len(ns)!=4 or not re.search(r'\btotal\b',p.question) or us[0]!=us[2] or len(ds[0])!=1 or ds[0]!=ds[2]:
        return None
    if ds[0][0] not in _TIME or us[1] not in _TIME or us[3] not in _TIME or ds[1] or ds[3]:
        return None
    output='mile' if us[0]=='mph' else us[0]
    if _asked(p)!=output:
        return None
    a=_convert(ns[1].value,us[1],ds[0][0]);b=_convert(ns[3].value,us[3],ds[2][0])
    if a is not None and b is not None:
        return _result(p,ns[0].value*a+ns[2].value*b,
                       '{} * {} + {} * {}'.format(_f(ns[0]),_f(a),_f(ns[2]),_f(b)))
    return None


def _journey_difference(p, ns, us, ds):
    if len(ns)!=4 or not re.search(r'\bhow much longer\b',p.question) or len(set(us))!=1:
        return None
    if ds[0] or ds[2] or len(ds[1])!=1 or ds[1]!=ds[3] or ds[1][0] not in _TIME:
        return None
    value=abs(ns[2].value/ns[3].value-ns[0].value/ns[1].value)
    return _result(p,value,'|{} / {} - {} / {}|'.format(_f(ns[2]),_f(ns[3]),_f(ns[0]),_f(ns[1])))


def _age_growth(p, ns, us, ds):
    if len(ns)!=4 or not re.match(r'how old\b',p.question) or us[0] not in _TIME:
        return None
    if us[1]!=us[2] or us[1]!=us[3] or ds[2]!=[us[0]] or ds[1] or ds[3]:
        return None
    if not re.search(r'\b(?:gains?|grows?|increases?)\b',p.body):
        return None
    return _result(p,ns[0].value+(ns[3].value-ns[1].value)/ns[2].value,
                   '{} + ({} - {}) / {}'.format(*(_f(ns[i]) for i in (0,3,1,2))))


def _sold_then_repack(p, ns, us, ds):
    if len(ns)!=4 or not re.search(r'\bremaining\b',p.body) or not re.search(r'\bselling\b',p.body):
        return None
    rates=[i for i,d in enumerate(ds) if us[i]=='money' and len(d)==1]
    packs=[i for i,d in enumerate(ds) if d==[_asked(p)]]
    if len(rates)!=1 or len(packs)!=1:
        return None
    r,pack=rates[0],packs[0]
    stocks=[i for i in range(4) if us[i]==us[pack] and not ds[i]]
    revenues=[i for i in range(4) if us[i]=='money' and not ds[i]]
    if len(stocks)!=1 or len(revenues)!=1 or ds[r]!=[us[pack]]:
        return None
    s,total=stocks[0],revenues[0]
    return _result(p,(ns[s].value-ns[total].value/ns[r].value)/ns[pack].value,
                   '({} - {} / {}) / {}'.format(*(_f(ns[i]) for i in (s,total,r,pack))))


def _residual_shares(p, ns, us, ds):
    if len(ns)!=4 or not re.search(r'\beach (?:person|student|friend|child)\b',p.question):
        return None
    if us[0]!=_asked(p) or us[3]!='person' or any(ds):
        return None
    t=p.text.lower()
    for i in (1,2):
        if us[i] not in ('',us[0]) or not re.search(r'\b(?:keeps?|kept|gives?|gave|ate|eats?|removed|reserves?)\s*$',t[:ns[i].start]):
            return None
    return _result(p,(ns[0].value-ns[1].value-ns[2].value)/ns[3].value,
                   '({} - {} - {}) / {}'.format(*(_f(n) for n in ns)))


def _coupon_unit_price(p, ns, us, ds):
    if len(ns)!=5 or _asked(p) not in ('money','cent') or us[1]!='coupon' or us[2] not in ('cent','money') or us[3:]!=['money','money']:
        return None
    t=p.text.lower()
    if not re.search(r'\boff\b',t[ns[2].end:ns[3].start]) or not re.search(r'\bin change\b',t[ns[4].end:]):
        return None
    if not re.search(r'\b(?:paid|pays?)\s*$',t[:ns[3].start]):
        return None
    a=_convert(ns[2].value,us[2],_asked(p)); b=_convert(ns[3].value-ns[4].value,'money',_asked(p))
    if a is not None and b is not None:
        return _result(p,(b+ns[1].value*a)/ns[0].value,
                       '({} + {} * {}) / {}'.format(_f(b),_f(ns[1]),_f(a),_f(ns[0])))
    return None


def _double_sided(p, ns, us, ds):
    if len(ns)!=3 or not re.search(r'\bdouble-sided\b',p.body) or _asked(p)!='sheet':
        return None
    if us[1]!=us[2] or ds[2]!=['side'] or not re.search(r'\b(?:each|they are each)\s*$',p.text[:ns[1].start].lower()):
        return None
    return _result(p,ns[0].value*ns[1].value/(ns[2].value*2),
                   '{} * {} / ({} * 2)'.format(*(_f(n) for n in ns)))


def _uniform_stock_change(p, ns, us, ds):
    if len(ns)!=3 or us[0]!=us[1] or us[0]!=_asked(p) or us[2] not in _TIME:
        return None
    t=p.text.lower()
    horizon=re.search(r'\bafter (?:an?|one) (week|day|hour)\b',t[ns[1].end:ns[2].start])
    if not horizon or not re.search(r'\bsame amount each day\b',p.body):
        return None
    elapsed=_convert(Fraction(1),horizon.group(1),us[2])
    if elapsed is not None:
        return _result(p,(ns[0].value-ns[1].value)*ns[2].value/elapsed,
                       '({} - {}) * {} / {}'.format(_f(ns[0]),_f(ns[1]),_f(ns[2]),_f(elapsed)))
    return None


def _resource_remaining(p, ns, us, ds):
    """Two explicit per-unit requirements and one known partial allocation."""
    if len(ns)!=4:
        return None
    asked=_asked(p); rates=[i for i,d in enumerate(ds) if len(d)==1]
    if len(rates)!=2:
        return None
    unknown=[i for i in rates if ds[i]==[asked]]
    if len(unknown)!=1:
        return None
    r=unknown[0]; known=next(i for i in rates if i!=r)
    counts=[i for i in range(4) if not ds[i] and us[i]==ds[known][0]]
    if len(counts)!=1:
        return None
    c=counts[0]; total=next(i for i in range(4) if i not in (r,known,c))
    if ds[total]:
        return None
    av=_convert(ns[total].value,us[total],us[r])
    bv=_convert(ns[known].value,us[known],us[r])
    if av is None or bv is None:
        return None
    t=p.text.lower(); sentence=core._sentence(t,ns[total])
    if not re.search(r'\b(?:total|all|picked|budget|made|earned|paid|has|had|remaining)\b',sentence):
        return None
    return _result(p,(av-ns[c].value*bv)/ns[r].value,
                   '({} - {} * {}) / {}'.format(_f(av),_f(ns[c]),_f(bv),_f(ns[r])))


def _subset_price(p, ns, us, ds):
    if len(ns)!=4 or _asked(p)!='money' or us[2]!='money' or ds[2]:
        return None
    if ds[1]!=[us[0]] or us[1]!=us[3] or ds[0] or ds[3]:
        return None
    if ns[3].start<len(p.body) or not re.search(r'\bcost\b',p.question):
        return None
    return _result(p,ns[2].value*ns[3].value/(ns[0].value*ns[1].value),
                   '{} * {} / ({} * {})'.format(*(_f(ns[i]) for i in (2,3,0,1))))


def _reverse_stock(p, ns, us, ds):
    if len(ns)!=4 or not re.search(r'\bat first\b',p.question):
        return None
    if us[0]!=us[2] or us[0]!=_asked(p) or us[1] not in _TIME or us[3] not in _TIME:
        return None
    t=p.text.lower()
    if not re.search(r'\b(?:every|per)\s*$',t[ns[0].end:ns[1].start]) or not re.search(r'\badditional\b',t[:ns[0].start]):
        return None
    elapsed=_convert(ns[3].value,us[3],us[1])
    if elapsed is not None:
        return _result(p,ns[2].value-ns[0].value*elapsed/ns[1].value,
                       '{} - {} * {} / {}'.format(_f(ns[2]),_f(ns[0]),_f(elapsed),_f(ns[1])))
    return None


def _portion_size_difference(p, ns, us, ds):
    if len(ns)!=3 or len(set(us))!=1 or not re.search(r'\b(?:fewer|more) servings\b',p.question):
        return None
    if us[0] not in core._MEASURES or not all('serving' in ds[i] for i in (1,2)):
        return None
    return _result(p,abs(ns[0].value/ns[1].value-ns[0].value/ns[2].value),
                   '|{} / {} - {} / {}|'.format(_f(ns[0]),_f(ns[1]),_f(ns[0]),_f(ns[2])))


def _pack_price_comparison(p, ns, us, ds):
    if len(ns)!=4 or us[0] not in ('money','cent') or us[2] not in ('money','cent') or us[1]!=us[3]:
        return None
    if _asked(p) not in ('money','cent') or not re.search(r'\bsave\b',p.question):
        return None
    t=p.text.lower()
    if not all(re.search(r'\bfor\s*$',t[ns[i].end:ns[i+1].start]) for i in (0,2)):
        return None
    a=_convert(ns[0].value,us[0],_asked(p));b=_convert(ns[2].value,us[2],_asked(p))
    if a is not None and b is not None:
        return _result(p,abs(a/ns[1].value-b/ns[3].value),
                       '|{} / {} - {} / {}|'.format(_f(a),_f(ns[1]),_f(b),_f(ns[3])))
    return None


def _coupon_portion(p, ns, us, ds):
    if len(ns)!=4 or _asked(p) not in ('cent','money'):
        return None
    cash=[i for i,u in enumerate(us) if u in ('cent','money')]
    if len(cash)!=2:
        return None
    portions=[i for i in range(4) if i not in cash]
    if us[portions[0]]!=us[portions[1]] or us[portions[0]] not in core._MEASURES:
        return None
    t=p.text.lower()
    coupons=[i for i in cash if re.match(r'\s+coupon\b',t[ns[i].end:])]
    if len(coupons)!=1 or not re.search(r'\beach serving\b',p.question):
        return None
    coupon=coupons[0];price=next(i for i in cash if i!=coupon)
    small,large=portions
    if not re.search(r'\b(?:holds?|contains?)\s*$',t[:ns[large].start]):
        return None
    a=_convert(ns[price].value,us[price],_asked(p));b=_convert(ns[coupon].value,us[coupon],_asked(p))
    if a is not None and b is not None:
        return _result(p,(a-b)*ns[small].value/ns[large].value,
                       '({} - {}) * {} / {}'.format(_f(a),_f(b),_f(ns[small]),_f(ns[large])))
    return None


def _average_measurements(p, ns, us, ds):
    if not 2<=len(ns)<=7 or len(set(us))!=1 or any(ds) or not re.search(r'\baverage\b',p.body[-40:]+' '+p.question):
        return None
    if us[0] not in _TIME or _asked(p) not in _TIME:
        return None
    t=p.text.lower();labels=[]
    for n in ns:
        m=re.match(r'\s+[a-z]+ of the ([a-z ]+?)(?:,|\.|$)',t[n.end:])
        if not m:
            return None
        labels.append(m.group(1))
    if len(set(labels))!=len(labels):
        return None
    value=_convert(sum((n.value for n in ns),Fraction(0))/len(ns),us[0],_asked(p))
    if value is not None:
        return _result(p,value,'({}) / {} (converted to {})'.format(' + '.join(_f(n) for n in ns),len(ns),_asked(p)))
    return None


def _equal_remainder(p, ns, us, ds):
    if len(ns)!=2 or any(ds) or not re.search(r'\bleft over\b',p.question):
        return None
    if not re.search(r'\b(?:same amount|equally|evenly|equal number)\b',p.body):
        return None
    if not re.search(r'\b(?:each|all)\b',p.body) or not all(n.value.denominator==1 for n in ns):
        return None
    t=p.text.lower()
    # The stock is explicitly counted after the recipient count, and the
    # query asks for leftovers after exhausting all possible whole shares.
    if not re.search(r'\b(?:has|have|counted)\s*$',t[:ns[1].start]):
        return None
    return _result(p,ns[1].value % ns[0].value,'{} mod {}'.format(_f(ns[1]),_f(ns[0])))


def _event_schedule(p, ns, us, ds):
    if len(ns)!=3 or _asked(p) not in _TIME or ds[1]!=[us[0]] or us[1] not in _TIME or us[2] not in _TIME or len(ds[2])!=1:
        return None
    if ds[2][0] not in _TIME or ds[0]:
        return None
    per_event=_convert(ns[1].value,us[1],us[2])
    if per_event is None:
        return None
    periods=ns[0].value*per_event/ns[2].value
    value=_convert(periods,ds[2][0],_asked(p))
    if value is not None:
        return _result(p,value,'{} * {} / {} (converted to {})'.format(_f(ns[0]),_f(per_event),_f(ns[2]),_asked(p)))
    return None


def _observed_schedule(p, ns, us, ds):
    if len(ns)!=4 or us[0] not in _TIME or us[2] not in _TIME or ds[2]!=[us[3]] or ds[0] or ds[1] or ds[3]:
        return None
    if us[1]!=_asked(p) or not re.search(r'\bconsume\b',p.body):
        return None
    t=p.text.lower()
    if not re.search(r'\b(?:consume|use|produce)\s*$',t[ns[0].end:ns[1].start]):
        return None
    elapsed=_convert(ns[2].value,us[2],us[0])
    if elapsed is not None:
        return _result(p,ns[1].value*elapsed*ns[3].value/ns[0].value,
                       '{} * {} * {} / {}'.format(_f(ns[1]),_f(elapsed),_f(ns[3]),_f(ns[0])))
    return None


def _repeated_daily(p, ns):
    if len(ns)!=1 or not re.search(r'\b(?:twice|thrice) a day\b',p.body):
        return None
    period=re.search(r'\b(?:a|per|each) (week|day)\b',p.question)
    unit=_unit(p,ns[0]); asked=_asked(p)
    if not period or unit not in _TIME or asked not in _TIME:
        return None
    per_day=3 if re.search(r'\bthrice a day\b',p.body) else 2
    days=_convert(Fraction(1),period.group(1),'day')
    value=_convert(ns[0].value*per_day*days,unit,asked)
    if value is not None:
        return _result(p,value,'{} * {} * {} (converted to {})'.format(_f(ns[0]),per_day,_f(days),asked))
    return None


def _reverse_equal_stock(p, ns, us, ds):
    if len(ns)!=4 or us[1]!=us[3] or us[1]!=_asked(p) or us[2]!='person' or ds[3]!=['person']:
        return None
    t=p.text.lower()
    if not re.search(r'\b(?:kept|keeps|reserved)\s*$',t[:ns[1].start]) or not re.search(r'\bequally\b',p.body):
        return None
    container=re.search(r'\beach ([a-z]+)\b',p.question)
    if not container or _normal(container.group(1))!=us[0] or any(ds[i] for i in (0,1,2)):
        return None
    return _result(p,(ns[1].value+ns[2].value*ns[3].value)/ns[0].value,
                   '({} + {} * {}) / {}'.format(*(_f(ns[i]) for i in (1,2,3,0))))


def _combined_requirements(p, ns, us, ds):
    if len(ns)!=4 or len(set(us))!=1 or _asked(p) not in ('customer','person'):
        return None
    asked=_asked(p);t=p.text.lower()
    if ds[0]!=[asked] or ds[2]!=['day'] or ds[3]!=['day']:
        return None
    if not re.search(r'\band is also given\s*$',t[:ns[1].start]) or not re.search(r'\bextra\s*$',t[:ns[2].start]):
        return None
    return _result(p,(ns[3].value-ns[2].value)/(ns[0].value+ns[1].value),
                   '({} - {}) / ({} + {})'.format(*(_f(ns[i]) for i in (3,2,0,1))))


def _refill_volume(p, ns, us, ds):
    if len(ns)!=3 or len(ds[0])!=1 or ds[0][0]!='day' or ds[1]!=[us[0]]:
        return None
    if not re.search(r'\bfill\b',p.question):
        return None
    period=re.search(r'\b(?:each|per|every|a) (day|week)\b',p.question)
    if not period:
        return None
    capacity=_convert(ns[2].value,us[2],us[1]);days=_convert(Fraction(1),period.group(1),'day')
    if capacity is not None and days is not None:
        value=ns[0].value*ns[1].value*days/capacity
        return _result(p,Fraction(-(-value.numerator//value.denominator)),
                       '{} * {} * {} / {}'.format(_f(ns[0]),_f(ns[1]),_f(days),_f(capacity)))
    return None


def _all_but_groups(p, ns, us, ds):
    if len(ns)!=4 or ds[0]!=[us[1]] or ds[3]!=[_asked(p)] or us[0]!=us[3]:
        return None
    t=p.text.lower()
    if not re.search(r'\ball but\s*$',t[:ns[2].start]) or not re.match(r'\s+of the '+re.escape(us[1])+r's?\b',t[ns[2].end:]):
        return None
    return _result(p,(ns[1].value-ns[2].value)*ns[0].value/ns[3].value,
                   '({} - {}) * {} / {}'.format(_f(ns[1]),_f(ns[2]),_f(ns[0]),_f(ns[3])))


def _periodic_inflow_outflow(p, ns, us, ds):
    if len(ns)!=4 or us[0]!=us[1] or us[0]!=_asked(p) or len(ds[0])!=1 or us[2] not in _TIME or us[3] not in _TIME:
        return None
    t=p.text.lower()
    if not re.search(r'\bevery\s*$',t[ns[1].end:ns[2].start]):
        return None
    if not re.search(r'\b(?:buys?|gives?|receives?|gets?)\b',t[:ns[0].start]) or not re.search(r'\b(?:eat|eats|uses?|consumes?)\s*$',t[:ns[1].start]):
        return None
    if not re.search(r'\b(?:saved|left|remaining)\b',p.question):
        return None
    a=_convert(ns[3].value,us[3],ds[0][0]);b=_convert(ns[3].value,us[3],us[2])
    if a is not None and b is not None:
        return _result(p,ns[0].value*a-ns[1].value*b/ns[2].value,
                       '{} * {} - {} * {} / {}'.format(_f(ns[0]),_f(a),_f(ns[1]),_f(b),_f(ns[2])))
    return None


def _weekly_pack_cost(p, ns, us, ds):
    if len(ns)!=4 or _asked(p)!='money' or len(ds[0])!=1 or ds[0]!=ds[1] or us[1]!='money' or us[0]!=us[2] or us[3] not in _TIME:
        return None
    t=p.text.lower()
    if not re.search(r'\b(?:changes?|replaces?|uses?)\b[^.!?]*\bweekly\b',p.body) or not re.search(r'\bholds?\s*$',t[:ns[2].start]):
        return None
    weeks=_convert(ns[3].value,us[3],'week')
    if weeks is not None:
        packs=ns[2].value*weeks/ns[0].value
        packs=Fraction(-(-packs.numerator//packs.denominator))
        return _result(p,packs*ns[1].value,'{} whole packages * {}'.format(_f(packs),_f(ns[1])))
    return None


def _phased_workforce(p, ns, us, ds):
    if len(ns)!=6 or us[2]!=us[4] or us[1]!=us[3] or us[1]!=us[5] or us[1] not in _TIME or _asked(p)!=us[0]:
        return None
    if ns[1].value!=ns[3].value+ns[5].value:
        return None
    t=p.text.lower()
    if not all(re.match(r'\s+[a-z]+ working for (?:another )?$',t[ns[i].end:ns[i+1].start]) for i in (2,4)):
        return None
    if not re.search(r'\beach '+re.escape(us[2])+r'\b',p.question) or not re.search(r'\bper '+us[1]+r'\b',p.question):
        return None
    effort=ns[2].value*ns[3].value+ns[4].value*ns[5].value
    return _result(p,ns[0].value/effort,'{} / ({} * {} + {} * {})'.format(*(_f(ns[i]) for i in (0,2,3,4,5))))


def _net_resource_goal(p, ns, us, ds):
    if len(ns) not in (4,5) or _asked(p) not in _TIME:
        return None
    t=p.text.lower(); period=_asked(p)
    timed=[i for i,d in enumerate(ds) if d==[period]]
    if len(timed)!=2:
        return None
    burn=[i for i in timed if re.search(r'\bburns?\s*$',t[:ns[i].start])]
    intake=[i for i in timed if re.search(r'\b(?:eats?|eating|consumes?|consuming)\s*$',t[:ns[i].start])]
    if len(burn)!=1 or len(intake)!=1:
        return None
    b,a=burn[0],intake[0]
    if us[b] not in ('',us[a]) or ns[b].value<=ns[a].value:
        return None
    others=[i for i in range(len(ns)) if i not in timed]
    if len(ns)==4:
        equations=[i for i in others if len(ds[i])==1]
        if len(equations)!=1:
            return None
        e=equations[0];goal=next(i for i in others if i!=e)
        if ds[e]!=[us[goal]] or us[e]!=us[a] or ds[goal]:
            return None
        required=ns[e].value*ns[goal].value
    else:
        e,w,goal=others
        if us[e]!=us[a] or us[w]!=us[goal] or not re.search(r'\bto lose\s*$',t[ns[e].end:ns[w].start]):
            return None
        required=ns[e].value/ns[w].value*ns[goal].value
    return _result(p,required/(ns[b].value-ns[a].value),
                   '{} / ({} - {})'.format(_f(required),_f(ns[b]),_f(ns[a])))


def _rectangular_capacity(p, ns, us, ds):
    if len(ns)!=5 or len(set(us[1:]))!=1 or us[1] not in ('foot','inch','centimeter','meter') or ds[4]!=[_asked(p)]:
        return None
    t=p.text.lower()
    for i,label in ((1,'long'),(2,'wide'),(3,'high')):
        if not re.match(r'\s+[a-z]+ '+label+r'\b',t[ns[i].end:]):
            return None
    if not re.match(r'\s+cubic\b',t[ns[4].end:]):
        return None
    value=ns[0].value*ns[1].value*ns[2].value*ns[3].value/ns[4].value
    if re.search(r'\b(?:need|bags|boxes)\b',p.question):
        value=Fraction(-(-value.numerator//value.denominator))
    return _result(p,value,'{} * {} * {} * {} / {}'.format(*(_f(n) for n in ns)))


def _two_stage_sharing(p, ns, us, ds):
    if len(ns)!=4 or us[0]!=us[1] or us[0]!=us[3] or us[0]!=_asked(p) or ds[3]!=[us[2]]:
        return None
    if any(ds[i] for i in (0,1,2)) or not re.search(r'\b(?:equal|equally|evenly)\b',p.body):
        return None
    t=p.text.lower()
    if not re.search(r'\b(?:ate|eats?|used|uses?|removed)\s*$',t[:ns[1].start]) or not re.search(r'\b(?:takes? away|removes?)\s*$',t[:ns[3].start]):
        return None
    return _result(p,(ns[0].value-ns[1].value)/ns[2].value-ns[3].value,
                   '({} - {}) / {} - {}'.format(*(_f(n) for n in ns)))


def _rate_chain(p, ns, us, ds):
    """At most four unambiguous, explicitly connected multiplicative amounts."""
    if not 2<=len(ns)<=5 or not all(us) or not any(ds):
        return None
    t=p.text.lower(); asked=_asked(p)
    if not asked or re.search(r'\b(?:left|remaining|more|less|than|half|twice|double|times as|rest|already|change|profit|loss|lost|average|except|stops?|breaks?|waits?|weekdays|weekends|other|both)\b',t):
        return None
    # A temporal schedule is a count of working hours/day, not elapsed time;
    # target conversion is performed after cancellation, in exact units.
    atoms=[]; consumed=set()
    for i in range(len(ns)):
        if i in consumed:
            continue
        if i+1<len(ns) and not ds[i] and not ds[i+1]:
            middle=t[ns[i].end:ns[i+1].start]
            if re.fullmatch(r"\s+[a-z]+(?:'[a-z]+)?\s+(?:for every|for|every|in)\s+",middle):
                a=core._amount(ns[i].value,us[i],[],_f(ns[i]),[i])
                b=core._amount(ns[i+1].value,us[i+1],[],_f(ns[i+1]),[i+1])
                atoms.append(core._combine(a,b,True));consumed.add(i+1)
                continue
        atoms.append(core._amount(ns[i].value,us[i],ds[i],_f(ns[i]),[i]))
    target=core._target(p,asked,us)
    if target is None or not target.dims:
        return None
    answers={}
    if len(atoms)>4:
        return None
    # A direct amount has one root stock. Multiple unrelated stocks cannot
    # be combined by cancellation, even if their dimensions happen to fit.
    if not any(e<0 for u,e in target.dims) and sum(not any(e<0 for u,e in a.dims) for a in atoms)>1:
        return None
    for signs in product((1,-1),repeat=len(atoms)):
        # Plain stocks and group counts multiply; only a quantity whose unit
        # is requested as a denominator or a stated rate may be inverted.
        if any(s<0 and not any(e<0 for u,e in a.dims)
               and not any(u==v and e>0 and power<0 for u,e in a.dims for v,power in target.dims)
               for a,s in zip(atoms,signs)):
            continue
        val=Fraction(1); dims={}
        for a,s in zip(atoms,signs):
            val=val*a.value if s==1 else val/a.value
            for u,e in a.dims:
                dims[u]=dims.get(u,0)+s*e
        if core._dim(dims)==target.dims:
            answers[val/target.value]=signs
    if len(answers)!=1:
        return None
    value,signs=next(iter(answers.items()))
    return _result(p,value,' * '.join(a.expression if s==1 else '(1 / {})'.format(a.expression) for a,s in zip(atoms,signs))+' (using compatible units)')


def solve(problem):
    ns=_numbers(problem)
    repeated=_repeated_daily(problem,ns)
    if repeated is not None:
        return repeated
    if not 2<=len(ns)<=7 or any(n.value<=0 or n.kind=='percent' for n in ns):
        return None
    currencies=set(re.findall(r'[$£€]',problem.text))
    if re.search(r'\bdollars?\b',problem.text,re.I):
        currencies.add('$')
    if re.search(r'\beuros?\b',problem.text,re.I):
        currencies.add('€')
    if len(currencies)>1:
        return None
    us=[_unit(problem,n) for n in ns]
    ds=_denoms(problem,ns,us)
    for rule in (_weighted_prices,_net_savings,_repack_loss,_remaining_budget,
                 _sum_costs,_equal_shares,_two_legs,_capital,_production_batch,
                 _scheduled_work,_group_plus_single,_batch_price,_speed_difference,
                 _daily_consumption,_melted_volume,_growth,_host_group,
                 _interval_difference,_geometric_change,_unit_savings,
                 _observed_progress,_annual_rate_goal,_proportional_mixture,
                 _needed_purchase,_area_groups,_processing_time,_time_ratio,
                 _interval_consumption,_fraction_duration,_two_measured_rates,
                 _two_products,_journey_difference,_age_growth,_sold_then_repack,
                 _residual_shares,_coupon_unit_price,_double_sided,
                 _uniform_stock_change,_resource_remaining,_subset_price,
                 _reverse_stock,_portion_size_difference,_pack_price_comparison,
                 _coupon_portion,_average_measurements,_equal_remainder,
                 _event_schedule,_observed_schedule,_reverse_equal_stock,
                 _combined_requirements,_refill_volume,_all_but_groups,
                 _periodic_inflow_outflow,_weekly_pack_cost,_phased_workforce,
                 _net_resource_goal,_rectangular_capacity,_two_stage_sharing,
                 _rate_chain):
        result=rule(problem,ns,us,ds)
        if result is not None:
            return result
    return None
