"""Exact multi-stage money equations with bound prices and quantities.

Readers abstain on unused quantities, ambiguous categories and unsupported
relations. Noun labels come from the problem, never from a product catalog.
"""
import re
from fractions import Fraction
from dataclasses import replace

from ..numbers import format_number, parse_number
from ..problem import Problem
from .._number_syntax import _ORDINALS
from ._money_common import (_numbers, _has, _bounds, _same, _head,
                            _currencies, _role, _singular)
from .money_totals_change_prices_3_steps_r09_a6 import _price as _base_price, _noun
from .money_totals_change_prices_1_2_steps_r06_a4 import _answer


def _sum(values):
    return sum(values, Fraction(0))


def _fmt(value):
    return format_number(value)


def _finish(p, value, expression):
    return _answer(p, value, expression)


def _label(tail):
    tail=re.split(r'\b(?:run|runs|ran|went|last|on|per)\b',tail)[0]
    return re.sub(r'\bkilo\b','kilogram',_noun(re.sub(r'\b(?:new|additional|more)\s+', '', tail)))


def _match(a, b):
    # Packaging may be omitted in a quoted retail price, but do not silently
    # convert quantities such as pairs, dozens, or boxes with stated contents.
    containers = r'^(?:bag|mug|piece|head|set) of '
    a,b=(re.sub(containers, '',label) for label in (a,b))
    if {a,b}<={'person','customer'}:return True
    return _same(a,b)


def _price(p,ns,n):
    """Extend common quote syntax without changing other skills' labels."""
    t=p.text.lower();before,after=t[:n.start],t[n.end:]
    start,end=_bounds(t,n)
    if re.fullmatch(r'\s*for\s*',t[start:n.start]) and re.match(r'\s+(?:a|an|the) [a-z]+ (?:bought|buys?|purchased)\b',after):return '',False
    m=re.match(r'\s*(?:per|a|an) ([a-z -]+?)\s+plus\b',after)
    if m:return _label(m.group(1)),True
    m=re.match(r'\s+(?:tip|bonus|fee) per ([a-z]+)',after)
    if m:return _label(m.group(1)),True
    m=re.match(r'\s+from [a-z]+ (?:a|an) ([a-z -]+)',after)
    if m:return _label(m.group(1)),True
    m=re.search(r'\b(?:sells?|sold|selling) ([a-z -]+?) at\s*$',before)
    if m:return _label(m.group(1)),True
    label,explicit=_base_price(p,ns,n)
    if not label or label=='*':
        start,end=_bounds(t,n)
        local=[c for c in ns if c.kind!='money' and start<=c.start<n.start]
        previous=max([k.end for k in ns if k.kind=='money' and k.end<n.start] or [start])
        local=[c for c in local if c.start>=previous]
        if len(local)==1 and _has(r'\b(?:each|apiece)\b',after[:25]):
            return _label(t[local[0].end:]),True
    m=re.search(r'\b([a-z]+) at\s*$',before)
    if m and label and label!='*' and _head(label) in {'packet','box','bag','can'}:
        candidate=label+' of '+_label(m.group(1))
        if any(c.kind!='money' and _match(candidate,_label(t[c.end:])) for c in ns):return candidate,True
    if label and label!='*':return label,explicit
    m=re.search(r'\b(?:one|a|an) ([a-z -]+?) at\s*$',before)
    if m:return _label(m.group(1)),True
    # Coordinated price catalogs can omit the repeated verb "costs".
    m=re.search(r'\b(?:every|each|a|an) ([a-z -]+?)\s*$',before)
    if m and not _has(r'\b(?:for|at|per|and|to|from|is|was)\b',m.group(1)):
        return _label(m.group(1)),True
    return label,explicit


def _denominations(p, ns):
    """Cash denominations, loose coins, and fixed purchases."""
    t = p.text.lower()
    if not _has(r'\b(?:left|remaining|change|back)\b', p.question):
        return None
    if _has(r'\b(?:each|per|percent|discount|times|half)\b', t):
        return None
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    used, terms = set(), []
    cash_role = None
    for i, n in enumerate(money):
        lower = money[i-1].end if i else 0
        prefix, suffix = t[lower:n.start], t[n.end:]
        role = _role(t, n, lower)
        value = n.value
        if re.match(r'\s+(?:bills?|notes?)\b', suffix):
            cs = [c for c in counts if c.end <= n.start and not t[c.end:n.start].strip()]
            if len(cs) != 1:
                return None
            used.add(id(cs[0])); value *= cs[0].value
            if _has(r'\b(?:has|have|had|wallet)\b', prefix):
                role = 'balance'
            elif _has(r'\b(?:gave|gives|handed|cashier|paid|with|using)\b', prefix):
                role = 'tender'
            else:
                role = cash_role
            cash_role = role
        elif _has(r'^\s+in (?:loose )?coins\b', suffix):
            role = cash_role
        elif _has(r'\b(?:costs?|buys?|bought|spent|spends|paid)\b[^.;]*$', prefix):
            role = 'expense'
        if role not in {'expense', 'balance', 'tender'}:
            return None
        terms.append((role, value))
    if not cash_role or len(used) != len(counts) or not any(r == 'expense' for r,v in terms):
        return None
    cash = _sum(v for r,v in terms if r != 'expense')
    expense = _sum(v for r,v in terms if r == 'expense')
    return _finish(p, cash-expense, '{} - {}'.format(_fmt(cash), _fmt(expense)))


def _population_period_safe(p):
    """A per-period population carries through an unchanged query period."""
    body_periods=set(re.findall(r'\bper (day|week|month|year)\b',p.body))
    query_periods=set(re.findall(r'\bper (day|week|month|year)\b',p.question))
    return len(body_periods)==1 and body_periods==query_periods


def _catalog(p, ns):
    """Itemized prices, with stock remainders, grouped buyers or a target."""
    t, q = p.text.lower(), p.question
    if _has(r'\b(?:percent|discount|half|times|twice|thrice|double|triple|profit|ratio|owe|owes|split|borrowed|repay|wins?)\b|(?<!-)\bfree\b', t) or _has(r'\bsave\b',q):
        return None
    if _has(r'\b(?:per|each|every)\b', re.split(r'\bif\b', q)[0]) and not _population_period_safe(p):
        return None
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if _has(r'\bweek\b',q) and _has(r'\b(?:per day|a day|every (?:day|morning|evening|night)|each day)\b',p.body):
        return None  # An outer duration must be handled before a daily basket.
    if not money or not counts or any(_head(_label(t[c.end:])) in {'day','week','month','year'} for c in counts):
        return None
    if any(not _label(t[c.end:]) for c in counts):
        return None
    population = []
    if _has(r'\beach of (?:them|the [a-z]+)\b|\beach (?:customer|student|person|member)\b', t):
        population = [c for c in counts if _head(_label(t[c.end:])) in {'student','person','child','adult','customer','member'}]
        if len(population) != 1:
            return None
        counts = [c for c in counts if c not in population]
    used, terms, prices = set(), [], []
    signed_terms=[];previous_role=None
    cash, target, rebates = [], [], []
    remaining = _has(r'\b(?:left|remaining)\b', q) and _has(r'\b(?:earn|make|made|sales)\b', q)
    for i, price in enumerate(money):
        lower = money[i-1].end if i else 0
        prefix = t[lower:price.start]
        label, explicit = _price(p, ns, price)
        label = _label(label)
        if _has(r'^\s+rebate\b',t[price.end:]) and _has(r'\breceived\b',prefix):
            rebates.append(price.value);continue
        if not explicit and _has(r'\b(?:quota|goal|needs? to (?:have|sell)|budget)\b',prefix+t[price.end:_bounds(t,price)[1]]):
            target.append(price.value); continue
        if not explicit and (_has(r'\b(?:rest of|has|had|from|with|keep|saved|carried|paid)\b[^.;]*$',prefix)
                             or _has(r'\b(?:change|left|remaining)\b',q) and price.start >= len(p.body)):
            cash.append(price.value); continue
        matches = [c for c in counts if _match(label, _label(t[c.end:]))]
        if label == '*':
            start, end = _bounds(t, price)
            matches = [c for c in counts if start <= c.start < price.start and id(c) not in used]
        # A physical unit (e.g. pounds) is qualified by its local material.
        if label in {'pound','liter','kilogram','gram','acre','box','can','tray'}:
            local = [c for c in matches if lower <= c.start < price.start]
            if local:
                matches = local
        if remaining and len(matches) == 2:
            a,b = sorted(matches,key=lambda c:c.start)
            if not (a.start < len(p.body) <= b.start) or a.value < b.value:
                return None
            amount = a.value-b.value
        elif len(matches) == 1:
            amount = matches[0].value
        elif len(matches)>1 and len({_label(t[c.end:]) for c in matches})==1 and not _has(r'\b(?:left|remaining|lost|gave|rest)\b',t):
            amount = _sum(c.value for c in matches)
        elif not matches:
            # A singular purchase is a fixed term; a catalog quote is not.
            start,end = _bounds(t,price)
            if not _has(r'\b(?:buys?|bought|gets?|builds?|orders?|costs?|cost|fee)\b',t[start:price.start]):
                return None
            if explicit and label and not _has(r'\b(?:a|an|the)\s+(?:[a-z]+\s+){0,2}'+re.escape(label.split()[0])+r'\b', t[start:price.start]):
                return None
            amount = Fraction(1)
        else:
            return None
        if any(id(c) in used for c in matches):
            return None
        used.update(id(c) for c in matches)
        role=_role(t,price,lower)
        if role is None and not _has(r'[.;]',prefix):role=previous_role
        if _has(r'\b(?:pay|paid)\b[^.;]*$',prefix):role='expense'
        if _has(r'\b(?:salary|wage|pay) (?:is|of)\s*$',prefix):role='income'
        previous_role=role
        signed_terms.append((role,price.value*amount))
        terms.append(price.value*amount)
        prices.append((price, price.value*amount))
    if len(used) != len(counts) or not terms or len(target)>1 or len(cash)>1:
        return None
    value = _sum(terms)-_sum(rebates)
    expr = ' + '.join(_fmt(v) for v in terms)
    if rebates:expr = '({}) - {}'.format(expr,_fmt(_sum(rebates)))
    if remaining and (cash or target or population):
        return None
    if population:
        value *= population[0].value
        expr = '({}) * {}'.format(expr,_fmt(population[0].value))
    if target:
        if not _has(r'\b(?:short|above|goal|more|need)\b',q) or cash:
            return None
        if _has(r'\b(?:above|short or|difference)\b',q):
            value = abs(value-target[0]); expr = '|({}) - {}|'.format(expr,_fmt(target[0]))
        else:
            value=target[0]-value;expr='{} - ({})'.format(_fmt(target[0]),expr)
    elif cash:
        if not _has(r'\b(?:left|remaining|change|have|keep|first|originally|initially|start)\b',q):
            return None
        if _has(r'\b(?:first|originally|initially|start)\b',q):
            value += cash[0];expr='{} + ({})'.format(_fmt(cash[0]),expr)
        else:
            value = cash[0]-value; expr = '{} - ({})'.format(_fmt(cash[0]),expr)
    elif _has(r'\b(?:left|remaining)\b',q) and not remaining:
        if not all(role in {'income','expense'} for role,v in signed_terms) or not any(role=='income' for role,v in signed_terms):return None
        value=_sum(-v if role=='expense' else v for role,v in signed_terms)
        expr=' + '.join(_fmt(-v if role=='expense' else v) for role,v in signed_terms)
    elif _has(r'\b(?:more|less|difference)\b',q):
        # Attribute each transaction to an explicitly introduced purchaser.
        events = list(re.finditer(r'\b((?:coach\s+)?[a-z]+)\s+(?:bought|buys?|will buy|spent|spends)\b',p.body))
        assigned = [next((m for m in reversed(events) if m.end()<=n.start),None) for n,v in prices]
        owners = {m.group(1) for m in assigned if m and m.group(1) not in {'he','she','they'}}
        if len(owners)!=2:
            return None
        groups = {owner:Fraction(0) for owner in owners}
        for n,v in prices:
            prior=[m for m in events if m.end()<=n.start]
            if not prior or prior[-1].group(1) not in owners:
                return None
            groups[prior[-1].group(1)]+=v
        a,b=list(groups.values());value=abs(a-b);expr='|{} - {}|'.format(_fmt(a),_fmt(b))
    elif not _has(r'\b(?:cost|costs|pay|paid|spend|spent|earn|earned|make|made|money|value)\b',q):
        return None
    elif {role for role,v in signed_terms}>={'income','expense'}:
        return None
    return _finish(p,value,expr)


def _staged_saving(p, ns):
    """Successive rates with explicit durations and an optional total duration."""
    t=p.text.lower()
    if not _has(r'\b(?:save|saved|saving|saves)\b',t) or not _has(r'\b(?:saved|save|money)\b',p.question):
        return None
    if _has(r'\b(?:spend|spent|interest|percent|more|less|twice)\b',t):
        return None
    money=[n for n in ns if n.kind=='money']
    counts=[n for n in ns if n.kind!='money']
    if len(money)<2:return None
    used=set();terms=[];units=set();durations=[]
    for i,n in enumerate(money):
        end=money[i+1].start if i+1<len(money) else len(p.body)
        m=re.match(r'\s*(?:per|a|each|every) (day|week|month|year)\b',t[n.end:])
        local=[c for c in counts if n.end<c.start<end]
        if not m or len(local)!=1:return None
        c=local[0];unit=_head(_label(t[c.end:]))
        if unit!=m.group(1):return None
        units.add(unit);used.add(id(c));durations.append(c.value);terms.append(n.value*c.value)
    extra=[c for c in counts if id(c) not in used]
    if len(units)!=1 or len(extra)>1:return None
    if extra and not (extra[0].start>=len(p.body) and extra[0].value==_sum(durations) and _head(_label(t[extra[0].end:])) in units):return None
    return _finish(p,_sum(terms),' + '.join(_fmt(v) for v in terms))


def _grouped_units(p, ns):
    """Groups with a stated quantity per group, all paid at a common rate."""
    t=p.text.lower()
    money=[n for n in ns if n.kind=='money'];counts=[n for n in ns if n.kind!='money']
    if len(money)!=1 or len(counts)<4 or len(counts)%2:return None
    if _has(r'\b(?:more|less|half|times|discount|left|remaining|profit)\b',t):return None
    price=money[0];label,explicit=_price(p,ns,price)
    if not explicit or not label:return None
    units=[];groups=[];terms=[]
    for a,b in zip(counts[::2],counts[1::2]):
        link=t[a.end:b.start]
        if not _has(r'\b(?:with|of|each (?:has|have)|containing)\s*$',link):return None
        group=_label(t[a.end:]);unit=_label(t[b.end:])
        if not _match(label,unit):return None
        groups.append(group);units.append(unit);terms.append(a.value*b.value)
    if len(set(groups))!=1 or len(set(units))!=1:return None
    total=_sum(terms)
    return _finish(p,total*price.value,'({}) * {}'.format(' + '.join(_fmt(v) for v in terms),_fmt(price.value)))


def _parallel_jobs(p,ns):
    """Several hourly jobs, each with its hours, and a common days/week factor."""
    t=p.text.lower();money=[n for n in ns if n.kind=='money'];counts=[n for n in ns if n.kind!='money']
    if len(money)<2 or not _has(r'\b(?:earn|make|made|money)\b',p.question):return None
    if _has(r'\b(?:bonus|overtime|tax|percent|twice|half)\b',t):return None
    factors=[c for c in counts if re.match(r'\s+days? (?:a|per|each) week\b',t[c.end:])]
    if len(factors)!=1:return None
    factor=factors[0];hours=[c for c in counts if c is not factor]
    if len(hours)!=len(money):return None
    used=set();terms=[]
    for i,n in enumerate(money):
        start=_bounds(t,n)[0];end=money[i+1].start if i+1<len(money) else len(t)
        if i+1<len(money):
            # The next job may introduce its hours before its wage.
            end=min(end,_bounds(t,money[i+1])[0])
        local=[c for c in hours if start<=c.start<end and _head(_label(t[c.end:]))=='hour']
        if len(local)!=1:return None
        c=local[0]
        if id(c) in used:return None
        if not (_has(r'^\s*(?:an?|per|each) hour\b',t[n.end:]) or _has(r'\b(?:main job|hourly|an hour|per hour)\b',t[start:c.end])):return None
        used.add(id(c));terms.append(n.value*c.value)
    if len(used)!=len(hours):return None
    return _finish(p,_sum(terms)*factor.value,'({}) * {}'.format(' + '.join(_fmt(v) for v in terms),_fmt(factor.value)))


def _weight_margin(p, ns):
    """Buy items by count, sell each item's weight at a unit mass price."""
    t=p.text.lower();money=[n for n in ns if n.kind=='money'];counts=[n for n in ns if n.kind!='money']
    if len(money)!=2 or len(counts)!=2 or 'profit' not in p.question:return None
    if _has(r'\b(?:percent|lost|half|times|total weight)\b',t):return None
    count,weight=counts;buy,sell=money
    if not count.start<buy.start<weight.start<sell.start:return None
    if not _has(r'\b(?:buys?|bought)\s*$',t[:count.start]):return None
    if not _has(r'^\s+each\b',t[buy.end:]) or not _has(r'\bweighs?\s*$',t[buy.end:weight.start]):return None
    label,explicit=_price(p,ns,sell)
    if not explicit or not _match(label,_label(t[weight.end:])) or weight.value<=0:return None
    return _finish(p,count.value*(weight.value*sell.value-buy.value),'{} * ({} * {} - {})'.format(*(_fmt(n.value) for n in (count,weight,sell,buy))))


def _yearly_increase(p,ns):
    """An initial annual fee, a fixed annual increase, and an ordinal year."""
    t=p.text.lower()
    if len(ns)!=2 or any(n.kind!='money' for n in ns):return None
    if not _has(r'\bincreases? (?:yearly|annually|each year|every year)\b',p.body):return None
    increases=[n for n in ns if _has(r'\bincreases? (?:yearly|annually|each year|every year) by\s*$',t[:n.start])]
    if len(increases)!=1:return None
    increase=increases[0];initial=next(n for n in ns if n is not increase)
    if not _has(r'^\s+in the first year\b',t[initial.end:]):return None
    m=re.search(r'\bin the ([a-z -]+|\d+(?:st|nd|rd|th)) year\b',p.question)
    if not m:return None
    ordinal=m.group(1)
    if re.fullmatch(r'\d+(?:st|nd|rd|th)',ordinal):year=Fraction(re.sub(r'\D','',ordinal))
    else:
        words=ordinal.split();last=words[-1]
        if last not in _ORDINALS:return None
        words[-1]=_ORDINALS[last];year=parse_number(' '.join(words))
    if year is None or year<1:return None
    return _finish(p,initial.value+(year-1)*increase.value,'{} + ({} - 1) * {}'.format(_fmt(initial.value),_fmt(year),_fmt(increase.value)))


def _delivery(p,ns):
    """Delivery fee plus successful items, minus penalties for damaged items."""
    t=p.text.lower();money=[n for n in ns if n.kind=='money'];counts=[n for n in ns if n.kind!='money']
    if len(money)!=3 or len(counts)<2:return None
    if not _has(r'\b(?:delivered safely|delivered successfully)\b',t) or not _has(r'\b(?:lost|broken|damaged)\b',t):return None
    fee,rate,penalty=money;stock=counts[0];losses=counts[1:]
    if not (stock.start<fee.start<rate.start<penalty.start<losses[0].start):return None
    if not _has(r'^\s+fee\b',t[fee.end:]) or not _has(r'^\s+for every\b',t[rate.end:]):return None
    label=_label(t[stock.end:]);rate_label=re.match(r'\s+for every ([a-z]+)',t[rate.end:])
    if not rate_label or not _match(label,_label(rate_label.group(1))):return None
    for c in losses:
        if not _match(label,_label(t[c.end:])) or not _has(r'^\s+[a-z]+ (?:are |were )?(?:lost|broken|damaged)\b',t[c.end:]):return None
    if not _has(r'^\s+each for any\b',t[penalty.end:]) or not _has(r'\bmust pay\b',t[rate.end:penalty.start]):return None
    bad=_sum(c.value for c in losses)
    if bad>stock.value:return None
    return _finish(p,fee.value+(stock.value-bad)*rate.value-bad*penalty.value,'{} + ({} - {}) * {} - {} * {}'.format(_fmt(fee.value),_fmt(stock.value),_fmt(bad),_fmt(rate.value),_fmt(bad),_fmt(penalty.value)))


def _rate_difference(p,ns):
    """Two sales rates at one price, over the same stated duration."""
    t=p.text.lower();money=[n for n in ns if n.kind=='money'];counts=[n for n in ns if n.kind!='money']
    if len(money)!=1 or len(counts)!=3 or not _has(r'\b(?:more|difference)\b',p.question):return None
    a,b,duration=counts;price=money[0]
    if not _has(r'\bper hour\b',t[a.end:b.start]) or not _has(r'\bper hour\b',t[b.end:price.start]):return None
    if _head(_label(t[duration.end:]))!='hour':return None
    la,lb=_label(t[a.end:]),_label(t[b.end:]);lp,explicit=_price(p,ns,price)
    # Nouns can insert the product after a container ("packs of X").
    if not _match(la,lb) or not explicit or not (_match(lp,la) or _head(lp)==_head(la)):return None
    return _finish(p,abs(a.value-b.value)*duration.value*price.value,'|{} - {}| * {} * {}'.format(*(_fmt(n.value) for n in (a,b,duration,price))))


def _cashflow(p,ns):
    """A funding target or loan balance, with income and expense products."""
    t,q=p.text.lower(),p.question
    if not (_has(r'\b(?:borrowed|repay|pays back|wins?|gift)\b',t)
            and _has(r'\b(?:more|need|have|left|remaining)\b',q)):return None
    if _has(r'\b(?:percent|interest|times|half|weekly|daily|a week|a day)\b',t):return None
    money=[n for n in ns if n.kind=='money'];counts=[n for n in ns if n.kind!='money']
    used=set();terms=[];target=[]
    for i,n in enumerate(money):
        lower=money[i-1].end if i else 0
        prefix=t[lower:n.start];suffix=t[n.end:]
        if _has(r'\bneeds? to have\s*$',prefix):
            target.append(n.value);continue
        role=_role(t,n,lower)
        if _has(r'\b(?:borrowed|wins?|won|earning)\s*$',prefix):role='income'
        if _has(r'\b(?:repay|pay back)\s+(?:(?:him|her|them)\s+)?$',prefix):role='expense'
        if role not in {'income','expense','balance'}:return None
        label,explicit=_price(p,ns,n)
        if _has(r'\bborrowed\s*$',prefix):label,explicit='',False
        matches=[c for c in counts if _match(label,_label(t[c.end:]))]
        if label=='*' or not label and explicit:
            start,end=_bounds(t,n)
            matches=[c for c in counts if start<=c.start<end and id(c) not in used]
            if not matches:
                subject=re.search(r'\b(?:sell|sells|sold) ([a-z]+) for\s*$',prefix)
                if subject:matches=[c for c in counts if _match(_label(subject.group(1)),_label(t[c.end:]))]
        if len(matches)>1 or any(id(c) in used for c in matches):return None
        if matches:
            used.add(id(matches[0]));value=n.value*matches[0].value
        elif explicit:
            start,end=_bounds(t,n)
            if role!='expense' or not label or not _has(r'\b(?:a|an) '+re.escape(label)+r'\b',t[start:n.start]):return None
            value=n.value
        else:value=n.value
        if re.match(r'\s+from both of (?:his|her|their) [a-z]+',suffix):value*=2
        terms.append(-value if role=='expense' else value)
    if len(used)!=len(counts) or len(target)>1:return None
    value=_sum(terms);expr=' + '.join(_fmt(v) for v in terms)
    if target:
        value=target[0]-value;expr='{} - ({})'.format(_fmt(target[0]),expr)
    elif not _has(r'\b(?:have|left|remaining)\b',q):return None
    return _finish(p,value,expr)


def _appointment_hours(p,ns):
    """A common hourly price times several individual or grouped sessions."""
    t=p.text.lower();money=[n for n in ns if n.kind=='money'];counts=[n for n in ns if n.kind!='money']
    if len(money)!=1 or not counts:return None
    if not _has(r'^\s*(?:per|an?|each) hour\b',t[money[0].end:]):return None
    if not _has(r'\b(?:earn|make|made|money|pay|paid)\b',p.question):return None
    if _has(r'\b(?:per day|a day|per week|a week|each day|every day|overtime|bonus|half|twice)\b',t):return None
    terms=[];i=0
    while i<len(counts):
        c=counts[i]
        if _head(_label(t[c.end:]))=='hour':
            terms.append(c.value);i+=1
        elif i+1<len(counts) and not t[c.end:counts[i+1].start].strip():
            h=counts[i+1]
            if not re.match(r'\s*[- ]?hours? (?:appointments?|sessions?|visits?)\b',t[h.end:]):return None
            terms.append(c.value*h.value);i+=2
        elif c.value==1 and re.match(r'\s+client\'s house\b',t[c.end:]) and _has(r'\bat\s*$',t[:c.start]):
            i+=1
        else:return None
    return _finish(p,_sum(terms)*money[0].value,'({}) * {}'.format(' + '.join(_fmt(v) for v in terms),_fmt(money[0].value)))


def _money_ledger(p,ns):
    """Only currency amounts: an initial balance, deposits and payments."""
    t,q=p.text.lower(),p.question
    if any(n.kind!='money' for n in ns) or not _has(r'\b(?:left|remaining)\b',q):return None
    if _has(r'\b(?:each|per|percent|half|double|times|more|less|interest|discount|rebate)\b',t):return None
    terms=[];previous=None
    for i,n in enumerate(ns):
        lo=ns[i-1].end if i else 0;prefix=t[lo:n.start]
        role=_role(t,n,lo)
        if _has(r'\b(?:deposited|found)\s+(?:her |his |their )?$',prefix):role='income'
        if _has(r'\b(?:paid|pay|spent|spends|cost|costs)\b[^.;]*$',prefix):role='expense'
        if role is None and not _has(r'[.;]',prefix):role=previous
        if role not in {'balance','income','expense'}:return None
        if i==0 and role!='balance':return None
        if i>0 and role=='balance':return None
        previous=role;terms.append(-n.value if role=='expense' else n.value)
    if not any(v<0 for v in terms):return None
    return _finish(p,_sum(terms),' + '.join(_fmt(v) for v in terms))


def _weighted_average(p,ns):
    """A weighted mean of item groups, each quoted at its average price."""
    t=p.text.lower()
    if not _has(r'\baverage (?:cost|price)\b',p.question):return None
    if _has(r'\b(?:discount|percent|left|remaining|more|less)\b',t):return None
    money=[n for n in ns if n.kind=='money'];counts=[n for n in ns if n.kind!='money']
    if len(money)<2 or len(money)!=len(counts):return None
    used=set();terms=[]
    for i,n in enumerate(money):
        lo=money[i-1].end if i else 0
        local=[c for c in counts if lo<=c.start<n.start]
        if len(local)!=1 or not _has(r'\bfor an average (?:cost|price) of\s*$',t[local[0].end:n.start]):return None
        used.add(id(local[0]));terms.append(n.value*local[0].value)
    total=_sum(c.value for c in counts)
    if total<=0:return None
    return _finish(p,_sum(terms)/total,'({}) / {}'.format(' + '.join(_fmt(v) for v in terms),_fmt(total)))


def _tiered_rate(p,ns):
    """The first N units at one rate, all subsequent units at another."""
    t=p.text.lower();money=[n for n in ns if n.kind=='money'];counts=[n for n in ns if n.kind!='money']
    if len(money)!=2 or len(counts)!=2:return None
    if not _has(r'\bfirst\b',p.body) or not _has(r'\b(?:after that|additional|subsequent|afterwards)\b',p.body):return None
    if _has(r'\b(?:percent|discount|half|times|more|less)\b',t):return None
    first,second=money;threshold,total=counts
    if not first.start<threshold.start<second.start<total.start:return None
    unit=_label(t[threshold.end:]);target=_label(t[total.end:])
    if not _match(unit,target) or total.value<threshold.value:return None
    a,ea=_price(p,ns,first);b,eb=_price(p,ns,second)
    if not ea or not eb or not _match(a,unit) or not _match(b,unit):return None
    value=threshold.value*first.value+(total.value-threshold.value)*second.value
    return _finish(p,value,'{} * {} + ({} - {}) * {}'.format(*(_fmt(n.value) for n in (threshold,first,total,threshold,second))))


def _remaining_group(p,ns):
    """Known subgroup rates and one rate for everyone else; optional shift."""
    t=p.text.lower();money=[n for n in ns if n.kind=='money'];counts=[n for n in ns if n.kind!='money']
    if len(money)<2 or not _has(r'\b(?:rest|all others|remaining)\b',p.body):return None
    shift=[c for c in counts if re.match(r'\s*[- ]?hours?\b',t[c.end:])]
    if len(shift)>1:return None
    stocks=[c for c in counts if c not in shift]
    if len(stocks)!=len(money):return None
    total=stocks[0];groups=stocks[1:]
    if not all(total.start<c.start for c in groups):return None
    if not _has(r'\b(?:there are|factory|students|employees|people)\b',t[:total.start]+t[total.end:_bounds(t,total)[1]]):return None
    terms=[]
    for c,n in zip(groups,money[:-1]):
        if not c.start<n.start:return None
        middle=t[c.end:n.start]
        if not _has(r'\b(?:earn|earns|raised|raise|paid)\s*$',middle):return None
        if not (_match(_label(t[total.end:]),_label(t[c.end:])) or re.match(r'\s+of (?:them|the [a-z]+)\b',t[c.end:])):return None
        terms.append(c.value*n.value)
    last=money[-1]
    if not _has(r'\b(?:rest|all others|remaining)\b[^.;]*$',t[money[-2].end:last.start]):return None
    remaining=total.value-_sum(c.value for c in groups)
    if remaining<0:return None
    terms.append(remaining*last.value)
    if shift:
        if not all(_has(r'^\s+per hour\b',t[n.end:]) for n in money):return None
        factor=shift[0].value
    else:
        if any(_has(r'^\s+per hour\b',t[n.end:]) for n in money):return None
        factor=Fraction(1)
    return _finish(p,_sum(terms)*factor,'({}) * {}'.format(' + '.join(_fmt(v) for v in terms),_fmt(factor)))


def _batch_cost(p,ns):
    """An explicit recipe of materials per batch and a requested batch count."""
    t=p.text.lower();counts=[n for n in ns if n.kind!='money']
    definitions=[c for c in counts if c.value==1 and _has(r'\b(?:make|produce)\s*$',t[:c.start]) and re.match(r'\s+batch\b',t[c.end:])]
    targets=[c for c in counts if c.start>=len(p.body) and re.match(r'\s+batches\b',t[c.end:])]
    if len(definitions)!=1 or len(targets)!=1:return None
    others=[n for n in ns if n not in definitions+targets]
    result=_catalog(p,others)
    if result is None:return None
    value=result[0]*targets[0].value
    return _finish(p,value,'{} * {}'.format(_fmt(result[0]),_fmt(targets[0].value)))


def _period_options(p,ns):
    """Two subscription periods with an explicit conversion and duration."""
    t=p.text.lower();money=[n for n in ns if n.kind=='money'];counts=[n for n in ns if n.kind!='money']
    if len(money)!=2 or len(counts)!=2 or not _has(r'\b(?:save|saves|saving)\b',p.question):return None
    if not _has(r'\bor\b',p.body) or not _has(r'\beach with exactly\b',p.body):return None
    a,b=money;duration,conversion=counts
    la,ea=_price(p,ns,a);lb,eb=_price(p,ns,b)
    if not ea or not eb or _head(_label(t[duration.end:]))!=lb or _head(_label(t[conversion.end:]))!=la:return None
    return _finish(p,abs(a.value*conversion.value-b.value)*duration.value,'|{} * {} - {}| * {}'.format(*(_fmt(n.value) for n in (a,conversion,b,duration))))


def _bill_values(p,ns):
    """An itemized collection of banknotes, optionally exchanged or tendered."""
    t,q=p.text.lower(),p.question
    if not _has(r'\b(?:bills?|notes?)\b',t):return None
    if _has(r'\b(?:percent|half|times|interest|discount)\b',t):return None
    money=[n for n in ns if n.kind=='money'];counts=[n for n in ns if n.kind!='money']
    used=set();values=[];unbound=[]
    for n in money:
        if not re.match(r'\s+(?:bills?|notes?)\b',t[n.end:]):return None
        local=[c for c in counts if c.end<=n.start and not t[c.end:n.start].strip()]
        if len(local)==1:
            c=local[0]
            if id(c) in used:return None
            used.add(id(c));values.append(c.value*n.value)
        else:unbound.append(n)
    if len(used)!=len(counts) or not values:return None
    total=_sum(values)
    if not unbound:
        if q.startswith('how many') or not _has(r'\b(?:money|cost|fee|have|has|total|worth)\b',q):return None
        return _finish(p,total,' + '.join(_fmt(v) for v in values))
    if len({n.value for n in unbound})!=1 or unbound[0].value<=0:return None
    if not _has(r'\b(?:change|exchange)\b',t) or not _has(r'\bhow many\b',q):return None
    value=total/unbound[0].value
    if value.denominator!=1:return None
    return value,'Banknotes: {} / {}.'.format(_fmt(total),_fmt(unbound[0].value))


def _group_service(p,ns):
    """Each group pays a flat per-item fee plus a time fee per item."""
    t=p.text.lower();money=[n for n in ns if n.kind=='money'];counts=[n for n in ns if n.kind!='money']
    if len(money)!=2 or len(counts)<2 or len(counts)%2:return None
    base,rate=money
    a,ea=_price(p,ns,base);b,eb=_price(p,ns,rate)
    if not ea or not eb or not _has(r'\bplus\b',t[base.end:rate.start]):return None
    if not re.match(r'\s+per (?:minute|hour) per '+re.escape(a)+r'\b',t[rate.end:]):return None
    terms=[]
    for c,d in zip(counts[::2],counts[1::2]):
        if not _match(a,_label(t[c.end:])) or not _match(b,_label(t[d.end:])):return None
        if not _has(r'\bfor\s*$',t[c.end:d.start]):return None
        terms.append(c.value*(base.value+d.value*rate.value))
    return _finish(p,_sum(terms),' + '.join(_fmt(v) for v in terms))


def _production_time(p,ns):
    """A paid unit-output rate over a writing/manufacturing interval."""
    t=p.text.lower();money=[n for n in ns if n.kind=='money'];counts=[n for n in ns if n.kind!='money']
    if len(money)!=1 or len(counts)!=3:return None
    output,interval,duration=counts;price=money[0]
    lp,ep=_price(p,ns,price)
    if not ep or not _match(lp,_label(t[output.end:])):return None
    if not _has(r'\bin\s*$',t[output.end:interval.start]):return None
    source=_head(_label(t[interval.end:]));target=_head(_label(t[duration.end:]))
    conversion={('minute','hour'):60,('second','minute'):60,('hour','day'):24}.get((source,target))
    if conversion is None or interval.value<=0:return None
    if not _has(r'\b(?:earn|make|money)\b',p.question):return None
    return _finish(p,price.value*output.value*duration.value*conversion/interval.value,'{} * {} * {} * {} / {}'.format(_fmt(price.value),_fmt(output.value),_fmt(duration.value),conversion,_fmt(interval.value)))


def _catalog_period(p,ns):
    """A daily basket or daily sales schedule repeated over explicit days."""
    t=p.text.lower()
    if _has(r'\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|weekends?|weekdays?|double|triple|twice|thrice)\b',t):return None
    counts=[n for n in ns if n.kind!='money']
    durations=[n for n in counts if n.start>=len(p.body) and _head(_label(t[n.end:]))=='day']
    if durations:
        if len(durations)!=1 or not _has(r'\b(?:in a day|per day|each day|every day|a day)\b',p.body):return None
        duration=durations[0].value;others=[n for n in ns if n is not durations[0]]
    elif _has(r'\b(?:per week|a week|one week|every week|each week|this week)\b',p.question) and _has(r'\b(?:per day|a day|every (?:day|morning|evening|night)|each day)\b',p.body):
        duration=Fraction(7);others=ns
    else:return None
    # The inner calculation is daily; remove only the outer query period.
    daily=replace(p,question=re.sub(r'\b(?:per week|a week|one week|every week|each week|this week)\b','in total',p.question))
    result=_catalog(daily,others)
    if result is None:return None
    return _finish(p,result[0]*duration,'{} * {}'.format(_fmt(result[0]),_fmt(duration)))


def _bulk_saving(p,ns):
    """Compare equivalent volumes or weights quoted in different units."""
    t=p.text.lower();money=[n for n in ns if n.kind=='money'];counts=[n for n in ns if n.kind!='money']
    if len(money)!=2 or len(counts)!=2 or not _has(r'\bsave\b',p.question):return None
    large,small=counts;a,b=money
    if not large.start<a.start<small.start<b.start:return None
    u,v=(_label(t[n.end:]).split()[0] for n in (large,small))
    conversion={('gallon','ounce'):128,('pound','ounce'):16,('kilogram','gram'):1000,('liter','milliliter'):1000}.get((u,v))
    if conversion is None or small.value<=0:return None
    count=large.value*conversion/small.value
    if count.denominator!=1:return None
    return _finish(p,b.value*count-a.value,'{} * {} - {}'.format(_fmt(count),_fmt(b.value),_fmt(a.value)))


def _catalog_equation(p,ns):
    """Known basket total minus priced products gives one unknown term."""
    t,q=p.text.lower(),p.question
    if _has(r'\b(?:discount|percent|half|times|more|less|profit)\b',t):return None
    money=[n for n in ns if n.kind=='money'];counts=[n for n in ns if n.kind!='money']
    if len(money)<3:return None
    totals=[]
    for n in money:
        label,explicit=_price(p,ns,n)
        lo,hi=_bounds(t,n);prefix=t[lo:n.start];suffix=t[n.end:hi]
        if explicit:continue
        if (_has(r'\b(?:raised|paid|spent)\s*$',prefix) and _has(r'\b(?:total|all|altogether)\b',suffix)
                or _has(r'^\s*for\s*$',prefix) and _has(r'\b(?:bought|buys?|purchased)\b',suffix)
                or _has(r'\b(?:gave|gives) (?:the )?cashier\s*$',prefix) and _has(r'\bno change\b',t)):
            totals.append(n)
    if len(totals)!=1:return None
    total=totals[0];prices=[n for n in money if n is not total]
    used=set();known=[];unpriced=[]
    for n in prices:
        label,explicit=_price(p,ns,n)
        matches=[c for c in counts if _match(label,_label(t[c.end:]))]
        if label=='*':
            lo,hi=_bounds(t,n)
            prev=max([k.end for k in money if k.end<n.start] or [lo])
            matches=[c for c in counts if max(prev,lo)<=c.start<n.start]
        if not explicit or not label:return None
        if not matches:
            unpriced.append(n);continue
        if any(id(c) in used for c in matches):return None
        used.update(id(c) for c in matches)
        known.append(n.value*_sum(c.value for c in matches))
    missing=[c for c in counts if id(c) not in used]
    remainder=total.value-_sum(known)
    if remainder<0:return None
    if len(missing)==1 and not unpriced and not q.startswith('how many'):
        c=missing[0];label=_label(t[c.end:])
        if not label or not _has(r'\b'+re.escape(label)+r'\b',q) or c.value<=0:return None
        divisor=c.value
    elif len(unpriced)==1 and not missing and q.startswith('how many'):
        n=unpriced[0];label,explicit=_price(p,ns,n)
        if not _match(label,_label(re.sub(r'^how many\s+','',q))) or n.value<=0:return None
        divisor=n.value
    else:return None
    return remainder/divisor,'Basket equation: ({} - {}) / {}.'.format(_fmt(total.value),_fmt(_sum(known)),_fmt(divisor))


def _job_comparison(p,ns):
    """Several explicit hourly jobs, combined over a common duration."""
    t,q=p.text.lower(),p.question
    money=[n for n in ns if n.kind=='money'];counts=[n for n in ns if n.kind!='money']
    if len(money)<2 or not _has(r'\b(?:make|earn|money)\b',q):return None
    if _has(r'\b(?:overtime|tax|bonus|percent|half|twice)\b',t):return None
    hours=[c for c in counts if _head(_label(t[c.end:]))=='hour']
    durations=[c for c in counts if c not in hours]
    if len(hours)!=len(money) or len(durations)!=1:return None
    duration=durations[0];period=_head(_label(t[duration.end:]))
    if period not in {'day','week'}:return None
    if duration.start<len(p.body) and not _has(r'\b(?:days? in a row|weeks? a year)\b',t[duration.end:]):return None
    terms=[];used=set()
    for i,n in enumerate(money):
        if not re.match(r'\s*(?:per|an?|/)\s*hour\b',t[n.end:]):return None
        # Hours and wages for one job may appear in either order, but cannot
        # cross the preceding or next job's wage.
        previous=money[i-1].end if i else 0
        following=money[i+1].start if i+1<len(money) else len(t)
        before=[c for c in hours if previous<=c.start<n.start and id(c) not in used]
        after=[c for c in hours if n.end<c.start<following and id(c) not in used]
        local=before if len(before)==1 else after
        if len(local)!=1:return None
        c=local[0];used.add(id(c))
        if period=='week' and not re.match(r'\s+hours? (?:a|per) week\b',t[c.end:]):return None
        terms.append(n.value*c.value)
    if len(used)!=len(hours):return None
    if _has(r'\b(?:more|difference)\b',q):
        if len(terms)!=2:return None
        base=abs(terms[0]-terms[1]);expr='|{} - {}|'.format(*(_fmt(v) for v in terms))
    else:
        base=_sum(terms);expr=' + '.join(_fmt(v) for v in terms)
    return _finish(p,base*duration.value,'({}) * {}'.format(expr,_fmt(duration.value)))


def _coin_ledger(p,ns):
    """Currency conservation with named standard coin denominations."""
    t,q=p.text.lower(),p.question
    denominations={'quartercoin':Fraction(1,4),'dime':Fraction(1,10),
                   'nickel':Fraction(1,20),'penny':Fraction(1,100)}
    if not _has(r'\b(?:quartercoins?|dimes?|nickels?|penn(?:y|ies))\b',t):return None
    if _has(r'\b(?:percent|times|half|more|less|each|per|doubled|total number)\b',t):return None
    if not _has(r'\b(?:left|remaining|how many)\b',q):return None
    terms=[];coins=[];previous=None
    for i,n in enumerate(ns):
        lo=ns[i-1].end if i else 0;prefix=t[lo:n.start]
        role=_role(t,n,lo)
        if _has(r'\b(?:gives?|gave)\b[^.;]*$',prefix):role='expense'
        if _has(r'\b(?:bought|buys?|costs?|spent|spends)\b[^.;]*$',prefix):role='expense'
        if role is None and not _has(r'[.;]',prefix):role=previous
        if role not in {'balance','income','expense'}:return None
        previous=role
        if n.kind=='money':terms.append(-n.value if role=='expense' else n.value)
        else:
            unit=_label(t[n.end:])
            if unit not in denominations:return None
            v=n.value*denominations[unit];coins.append((-v if role=='expense' else v))
    target=re.match(r'how many (quartercoins?|dimes?|nickels?|penn(?:y|ies))\b',q)
    if target:
        unit=_singular(target.group(1))
        if coins:
            if len(terms)!=1:return None
            value=terms[0]-_sum(coins)
        else:value=_sum(terms)
        if value<0:return None
        value/=denominations[unit]
        if value.denominator!=1:return None
        return value,'Coin count: {}.'.format(_fmt(value))
    return _finish(p,_sum(terms)+_sum(coins),'{} + {}'.format(_fmt(_sum(terms)),_fmt(_sum(coins))))


def solve(problem):
    normalized=re.sub(r'\bquarters\b(?!\s+of\b)','quartercoins',problem.text,flags=re.I)
    if normalized!=problem.text:
        problem=Problem.read(normalized)
        if problem is None:return None
    t=problem.text.lower()
    if _has(r'\bcoupons?\b',t):return None
    if not _has(r'[$£€]|\b(?:dollars?|cents?|euros?)\b',t):return None
    if not _has(r'\b(?:money|dollars?|costs?|pay|paid|spend|spent|earn|earned|earnings|make|made|change|profit|save|saved|left|remaining|goal|value|bills?|notes?|fee|worth|have|savings|raise|raised|collect|sales)\b',problem.question) and not problem.question.startswith('how many'):return None
    count_question=bool(re.match(r'how many (?!(?:more )?(?:dollars?|cents?|euros?)\b)',problem.question))
    ns=_numbers(problem)
    converted=[]
    for n in ns:
        m=re.match(r'\s+dozen\s+([a-z -]+)',t[n.end:]) if n.kind!='money' else None
        if m and not _has(r'\bper dozen\b|\ba dozen\b',t):
            # Keep offsets just after the scale, so ordinary noun binding works.
            n=replace(n,value=n.value*12,end=n.end+m.start(1))
        converted.append(n)
    ns=converted
    definitions=[]
    for n in ns:
        if n.kind=='money' or n.value!=1:continue
        after=t[n.end:]
        if (re.match(r'\s+[a-z-]+(?:\s+[a-z-]+){0,4}\s+(?:costs?|is worth|is|was|at)\s+[$£€]',after)
                and not _has(r'\b(?:buys?|bought|orders?|ordered)\b[^.;]*$',t[:n.start])):
            definitions.append(n)
        elif n.start>=len(problem.body) and re.match(r'\s+week\b',after) and _has(r'\ba week\b',problem.body):
            definitions.append(n)
    ns=[n for n in ns if n not in definitions]
    ns=[n for i,n in enumerate(ns) if not (n.kind!='money' and n.value==1 and i+1<len(ns) and not t[n.end:ns[i+1].start].strip() and re.match(r'\s*[- ]?hours?[^.;]*\bshift\b',t[ns[i+1].end:]))]
    # "One of her clients" selects an actor; it is not a purchased item.
    ns=[n for n in ns if not (n.kind!='money' and n.value==1
        and _has(r'^\s+of (?:his|her|their|the) [a-z]+\b',t[n.end:])
        and not _has(r'\b(?:buy|bought|sell|sold|needs?|wants?)\s*$',t[:n.start]))]
    if not 2<=len(ns)<=24 or any(n.kind=='percent' or n.value<0 for n in ns) or len(_currencies(problem,ns))>1:return None
    coins=_coin_ledger(problem,ns)
    if coins is not None:return coins
    if count_question and not _has(r'\b(?:bills?|notes?)\b',problem.question):
        return _catalog_equation(problem,ns)
    for reader in (_catalog_equation,_job_comparison,_bulk_saving,_bill_values,_group_service,_production_time,_catalog_period,_money_ledger,_weighted_average,_tiered_rate,_remaining_group,_batch_cost,_period_options,_denominations,_yearly_increase,_delivery,_weight_margin,_cashflow,_appointment_hours,
                   _staged_saving,_grouped_units,_parallel_jobs,_rate_difference,_catalog):
        result=reader(problem,ns)
        if result is not None:return result
    return None
