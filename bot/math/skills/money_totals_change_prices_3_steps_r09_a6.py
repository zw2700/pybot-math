"""Itemized money equations, linked schedules, and comparisons.

Every reader binds quantities to a transaction or unit. Unsupported relations
and unconsumed quantities cause abstention; all arithmetic is rational.
"""
import re
from fractions import Fraction

from ..numbers import format_number
from ._money_common import _currencies, _has, _expr, _bounds, _role, _singular
from .money_totals_change_prices_1_2_steps_r06_a4 import _answer, _label
from ._money_common import (
    _numbers, _phrase, _head, _same, _price_matches, _aggregate, _output, _TIME as _PERIODS,
    _period_scale as _scale,
)


def _noun(tail):
    tail = re.sub(r'^\s*(?:a|an|the|each|every)\s+', '', tail)
    tail = re.sub(r'\bback to back\b', '', tail)
    tail = re.split(r'\b(?:repaired|employed|invited|which|who)\b',tail)[0]
    tail = re.sub(r'^\s*one day (passes|tickets)\b',r'\1',tail)
    tail = re.sub(r'\bback home\b','',tail)
    tail = re.sub(r'^\s*(?:kids?|people|students?)\s+(?:want|choose|chose)\s+', ' ', tail)
    tail = re.sub(r'^\s*(?:want|choose|chose)\s+', ' ', tail)
    quoted=re.match(r'\s*["\']([a-z -]+)["\']\s*([a-z]+)?',tail)
    if quoted:
        return quoted.group(1)+' '+_singular(quoted.group(2) or 'item')
    label = _phrase(tail)
    return ' '.join({'mangoe': 'mango', 'potatoe': 'potato','pack':'packet','package':'packet',
                     'tomatoe': 'tomato'}.get(w, w) for w in label.split())


def _compatible(a,b):
    return _same(a, b) or {a, b} == {'ticket', 'pass'}


def _price(p, ns, n):
    t = p.text.lower()
    before, after = t[:n.start], t[n.end:]
    quoted=re.search(r'\b([a-z]+),?\s*["\']([a-z -]+),?["\']\s*,?\s*costs?\s*$',before)
    if quoted:
        return quoted.group(2)+' '+_singular(quoted.group(1)),True
    m=re.search(r'\b(?:salary|pay) of (?:the )?([a-z -]+?) (?:is|was)\s*$',before)
    if m:
        return _noun(m.group(1)),True
    m = re.match(r'\s*(?:dollars?|cents?)?\s*(?:per\s+|/\s*|an?\s+|for each\s+)([a-z -]+)', after)
    if m:
        unit=_noun(m.group(1))
        subject=re.search(r'\b([a-z]+) for\s*$',before)
        if subject:
            item=_singular(subject.group(1))
            if item not in {'a','an','each','it','them'}:
                candidate = _noun(unit+' of '+item)
                if any(c.kind != 'money' and ' of ' in _noun(t[c.end:])
                       and _same(candidate, _noun(t[c.end:])) for c in ns):
                    return candidate, True
        return unit, True
    m = re.search(r'\bfor (?:each|every) ([a-z -]+?) (?:he|she|they|\w+) (?:makes?|earns?|gets?)\s*$', before)
    if m:
        return _noun(m.group(1)), True
    m = re.search(r'\b(?:sell|sells|sold|selling|buys|buy)\s+([a-z -]+?)\s+for\s*$', before)
    if m:
        subject = re.split(r'\band\b|[.;,]', m.group(1))[-1]
        if _noun(subject):
            return _noun(subject), True
    m = re.search(r'\band\s+([a-z -]+?)\s+for\s*$', before)
    if m and _has(r'\b(?:sell|sells|sold|selling)\b', before):
        if _noun(m.group(1)):
            return _noun(m.group(1)), True
    m=re.search(r',\s*([a-z -]+?)\s+for\s*$',before)
    if m and _has(r'\b(?:sell|sells|sold|selling|costs?)\b',before):
        return _noun(m.group(1)),True
    label, explicit = _label(p, ns, n)
    if label and 'back' in label:
        local = [c for c in ns if c.kind != 'money' and _bounds(t,n)[0] <= c.start<n.start]
        if len(local)==1:
            return _noun(t[local[0].end:]), explicit
    if label:
        return _noun(label), explicit
    # Price in the same item clause: "N items at/for PRICE", including
    # "N items which they will be selling for PRICE".
    start, end = _bounds(t, n)
    previous_money = max([k.end for k in ns if k.kind == 'money' and k.end < n.start] or [start])
    local = [k for k in ns if k.kind != 'money' and max(start, previous_money) <= k.start < n.start]
    if len(local) == 1 and _has(r'\b(?:at|for)\s*$', before):
        c = local[0]
        link = t[c.end:n.start]
        if _has(r'\bfor\s*$',before) and not _has(r'\b(?:each|apiece)\b',after[:20]):
            # Bare "N items for PRICE" may be a price for the whole lot.
            # Only an itemized list supplies the per-item quoting convention.
            quotes=0
            for price in (k for k in ns if k.kind=='money'):
                lo=_bounds(t,price)[0]
                lo=max([k.end for k in ns if k.kind=='money' and k.end<price.start] or [lo])
                if any(k.kind!='money' and lo<=k.start<price.start for k in ns):
                    quotes+=1
            if quotes<2:
                return '',False
        if not _has(r'\b(?:total|altogether|all|combined)\b', link):
            return _noun(t[c.end:]), True
    return label, explicit


def _basket(p, ns):
    """A basket with explicit counts and prices, plus cash or fixed fees."""
    t, q = p.text.lower(), p.question
    if _has(r'\bsave\b', q) and _has(r'\b(?:gallon|pound|kilogram|liter)\b', t):
        return None
    if (_has(r'\bweek\b', q)
            and _has(r'\b(?:per day|a day|every (?:day|morning|evening|night)|each day)\b', p.body)):
        return None  # A daily basket needs an outer weekly multiplier.
    # Counts in dozens must be converted before applying per-item prices.
    if any(c.kind != 'money' and _has(r'^\s+dozen\b', t[c.end:]) for c in ns):
        return None
    if _has(r'\b(?:lose|lost)\b',q):
        return None
    if _has(r'\b(?:percent|times|twice|thrice|double|triple|half|quarter|ratio|tax|discount|coupon|free|average|equally|more|less)\b', p.body):
        return None
    if _has(r'\b(?:per|each|every|one|single)\b', re.split(r'\b(?:if|when)\b', q)[0]):
        return None
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    descriptive=[c for c in counts if _has(r'^\s+(?:different )?(?:types|kinds)\b',t[c.end:]) and c.value==len(money)]
    descriptive += [c for c in counts if c.start>=len(p.body)
                    and _has(r'\b(?:these|those)\s*$',t[:c.start]) and c.value==len(money)]
    counts=[c for c in counts if c not in descriptive]
    if not money or not counts or any(_head(_noun(t[c.end:])) in {'hour','day','week','month','year'} for c in counts):
        return None
    if _has(r'\b(?:profit|expenses|ingredients)\b', t):
        return None
    if _has(r'\b(?:in total|altogether)\b[^.;]*\bpaid\b|\bpaid\b[^.;]*\b(?:in total|altogether)\b',p.body):
        return None
    labels = {id(c): _noun(t[c.end:]) for c in counts}
    price_labels = {id(n): _price(p, ns, n) for n in money}
    # A coordinated catalog may name the container once, then list only
    # contents. Inherit that unit only from an explicit quote in this basket.
    containers = {_head(label) for label, explicit in price_labels.values()
                  if explicit and ' of ' in label}
    used, terms = set(), []
    for i, n in enumerate(money):
        lower = money[i-1].end if i else 0
        prefix, suffix = t[lower:n.start], t[n.end:]
        role = _role(t, n, lower)
        if (role=='expense' and _has(r'\b(?:salary|wage|pay) of\b',p.body)
                and not _has(r'\b(?:costs?|spends?|spent|buys?|bought|pays?|paid)\b',prefix)):
            role='income'
        if _has(r'\b(?:gave|gives|put in)\s+(?:[a-z]+\s+)?$',prefix):
            role='income'
        if _has(r'^\s+(?:leftover|left over)\b',suffix):
            role='remaining'
        if _has(r'\b(?:selling|charging|makes?|earns?|raise[ds]?)\b[^.;]*$', prefix):
            role = 'income'
        # A count immediately before a denomination supplies the tender.
        bills = [c for c in counts if c.end <= n.start and not t[c.end:n.start].strip()]
        if bills and _has(r'^\s+(?:bills?|notes?)\b', suffix):
            c = bills[-1]
            if not _has(r'\b(?:paid|pay|pays|with|using|handed|gave)\b', prefix):
                return None
            used.add(id(c))
            terms.append(('tender', c.value*n.value, '{} * {}'.format(format_number(c.value),format_number(n.value))))
            continue
        label, explicit = price_labels[id(n)]
        matches = [c for c in counts if _compatible(label, labels[id(c)])
                   or _price_matches(p, n, label, labels[id(c)])]
        if not matches:
            matches = [c for c in counts
                       if ' of ' in labels[id(c)]
                       and _head(labels[id(c)]) in containers
                       and _same(label, labels[id(c)].split(' of ', 1)[1])]
        if not matches and label=='ticket':
            matches=[c for c in counts if lower<=c.start<n.start
                     and _head(labels[id(c)]) in {'person','adult','child','student'}
                     and _has(r'\btickets?\b',t[c.end:n.start])]
        if label == '*':
            start, end = _bounds(t, n)
            matches = [c for c in counts if start <= c.start < n.start and id(c) not in used]
        local = [c for c in matches if lower <= c.start < n.start]
        if local:
            matches = local
        if len(matches) > 1 or any(id(c) in used for c in matches):
            return None
        if matches:
            c = matches[0]
            used.add(id(c))
            value = c.value*n.value
            expression = '{} * {}'.format(format_number(c.value),format_number(n.value))
        elif explicit:
            return None
        else:
            value, expression = n.value, format_number(n.value)
        if role is None and terms and not _has(r'[.;]', prefix):
            role = terms[-1][0]
        if role not in {'expense','income','balance','tender','remaining'}:
            return None
        terms.append((role, value, expression))
    unused = [c for c in counts if id(c) not in used]
    # A stated population is redundant only after the selected subgroups
    # account for it exactly, and the unpriced count denotes people.
    if unused:
        if len(unused) != 1 or _head(labels[id(unused[0])]) not in {'student','person','kid','child'}:
            return None
        if unused[0].value != sum((c.value for c in counts if id(c) in used), Fraction(0)):
            return None
    if {role for role,value,expr in terms}=={'expense','income'}:
        return None
    return _output(p, _aggregate(p, terms))


def _schedule_ledger(p, ns):
    """An hourly wage follows a schedule; fixed expenses follow earnings."""
    t = p.text.lower()
    money = [n for n in ns if n.kind == 'money']
    wages = [n for n in money if _has(r'^\s*(?:per|an?|each)\s+hour\b', t[n.end:])]
    if len(wages) != 1 or _has(r'\b(?:overtime|bonus|tax|times|half|double|twice|thrice|triple)\b', t):
        return None
    wage = wages[0]
    expenses = [n for n in money if n is not wage]
    if expenses and not _has(r'\b(?:left|remaining)\b', p.question):
        return None
    for n in expenses:
        if _role(t,n,max([k.end for k in ns if k.kind == 'money' and k.end<n.start] or [0])) != 'expense':
            return None
    counts = [n for n in ns if n.kind != 'money']
    links, stocks = {}, []
    for c in counts:
        m = re.match(r'\s+(hours?|days?|weeks?|months?|years?)\b\s*(?:of work\b\s*)?', t[c.end:])
        if not m:
            return None
        unit = _singular(m.group(1))
        tail = t[c.end+m.end():]
        link = re.match(r'(?:a|an|per|each|every)\s+(day|week|month|year)\b', tail)
        if link:
            if unit in links:
                return None
            links[unit] = (link.group(1),c.value)
        else:
            stocks.append((unit,c.value))
    if len(stocks) != 1:
        return None
    target, duration = stocks[0]
    unit, hours, used = 'hour', duration, set()
    while unit != target:
        if unit in used:
            return None
        used.add(unit)
        if unit in links:
            unit, factor = links[unit]
        else:
            factor = _scale(unit,target)
            if factor is None:
                return None
            unit = target
        hours *= factor
    if set(links)-used:
        return None
    earned = hours*wage.value
    return _answer(p,earned-sum((n.value for n in expenses),Fraction(0)),
                   '{} * {} - ({})'.format(format_number(hours),format_number(wage.value),_expr([n.value for n in expenses])))


def _recurring_comparison(p, ns):
    """Compare two costs over the same explicitly specified duration."""
    t,q = p.text.lower(),p.question
    if not _has(r'\b(?:difference|more|less|save|savings)\b',q):
        return None
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind != 'money']
    if len(money)!=2 or len(counts)>1 or _has(r'\b(?:percent|discount|tax|times|half)\b',t):
        return None
    labels = [_price(p,ns,n)[0] for n in money]
    if len(set(labels))!=1 or labels[0] not in _PERIODS:
        return None
    if counts:
        unit = _head(_noun(t[counts[0].end:]))
        duration = counts[0].value
    else:
        m = re.search(r'\b(?:a|one|an entire|the whole) (day|week|month|year)\b',t[money[-1].end:])
        if not m:
            return None
        unit,duration=m.group(1),Fraction(1)
    factor = _scale(labels[0],unit)
    if factor is None:
        return None
    value=abs(money[0].value-money[1].value)*duration*factor
    return _answer(p,value,'|{} - {}| * {} * {}'.format(format_number(money[0].value),format_number(money[1].value),format_number(duration),factor))


def _unit_margin(p, ns):
    """Sell a stock at a unit margin, optionally through counted packages."""
    t,q=p.text.lower(),p.question
    if not _has(r'\b(?:profit|expenses)\b',q):
        return None
    money=[n for n in ns if n.kind=='money']
    counts=[n for n in ns if n.kind!='money']
    if len(money)!=2 or not 1<=len(counts)<=3 or _has(r'\b(?:percent|discount|half|unsold|left|remaining)\b',p.body):
        return None
    sale=[]; cost=[]
    for n in money:
        start,end=_bounds(t,n)
        prefix=t[start:n.start]
        events=list(re.finditer(r'\b(?:buys?|bought|costs?|ingredients|make|sells?|sold)\b',prefix))
        if events and events[-1].group() not in {'sell','sells','sold'}:
            cost.append(n)
        elif events:
            sale.append(n)
    if len(sale)!=1 or len(cost)!=1:
        return None
    price,expense=sale[0],cost[0]
    # "cost PRICE to make 1 unit" is an explicit unit definition.
    definitions=[c for c in counts if c.value==1 and expense.end<c.start<price.start
                 and _has(r'\bto make\s*$',t[expense.end:c.start])]
    stock=[c for c in counts if c not in definitions]
    if len(stock)==1:
        c=stock[0]
        label=_noun(t[c.end:])
        if not (_has(r'^\s+(?:each|apiece|per|a|an)\b',t[price.end:]) or _same(_price(p,ns,price)[0],label)):
            return None
        if not definitions and not _same(_price(p,ns,expense)[0],label):
            return None
        quantity=c.value
    elif len(stock)==2:
        size,boxes=stock
        container=_head(_noun(t[boxes.end:]))
        if not container or not _has(r'\beach '+re.escape(container)+r' (?:has|contains|holds)\s*$',t[:size.start]):
            return None
        if not _same(_price(p,ns,price)[0],_noun(t[size.end:])):
            return None
        if not _same(_price(p,ns,expense)[0],_noun(t[size.end:])):
            return None
        quantity=size.value*boxes.value
    else:
        return None
    return _answer(p,quantity*(price.value-expense.value),'{} * ({} - {})'.format(format_number(quantity),format_number(price.value),format_number(expense.value)))


def _introductory_rate(p, ns):
    """The first interval has a package price; subsequent time has a rate."""
    t=p.text.lower()
    money=[n for n in ns if n.kind=='money']
    counts=[n for n in ns if n.kind!='money']
    if len(money)!=2 or len(counts)!=1 or not _has(r'\b(?:pay|paid|cost|spend|spent)\b',p.question):
        return None
    packages=[n for n in money if _has(r'^\s+for the first (?:day|week|month|year)\b',t[n.end:])]
    if len(packages)!=1:
        return None
    package=packages[0]; rate=next(n for n in money if n is not package)
    period=re.match(r'\s+for the first (day|week|month|year)\b',t[package.end:]).group(1)
    unit=_head(_noun(t[counts[0].end:]))
    rate_unit=_price(p,ns,rate)[0]
    factor=_scale(unit,period)
    if factor is None or rate_unit!=unit or counts[0].value<factor:
        return None
    value=package.value+(counts[0].value-factor)*rate.value
    return _answer(p,value,'{} + ({} - {}) * {}'.format(format_number(package.value),format_number(counts[0].value),factor,format_number(rate.value)))


def _owners(p, ns):
    """Independent personal balances or itemized expenditures, then compare."""
    t,q=p.text.lower(),p.question
    if not all(n.kind=='money' for n in ns) or not _has(r'\b(?:more|less|difference)\b',q):
        return None
    if _has(r'\b(?:per|each|times|half|percent|would|could|if|than)\b',p.body):
        return None
    events=list(re.finditer(r"\b([A-Z][a-z]+)\s+(?:has|had|spent|spends|saved|earned|earns)\b",p.text[:len(p.body)]))
    events=[e for e in events if e.group(1) not in {'He','She','They','If','Then'}]
    owners={e.group(1).lower() for e in events}
    if len(owners)!=2:
        return None
    groups={owner:[] for owner in owners}
    for n in ns:
        prior=[e for e in events if e.end()<=n.start]
        if not prior:
            return None
        owner=prior[-1].group(1).lower()
        lower=max([k.end for k in ns if k.end<n.start] or [0])
        role=_role(t,n,lower)
        if role is None and groups[owner]:
            role=groups[owner][-1][0]
        if role not in {'expense','balance','income'}:
            return None
        groups[owner].append((role,n.value))
    totals=[]
    for terms in groups.values():
        if _has(r'\b(?:left|remaining)\b',q):
            if not any(r in {'balance','income'} for r,v in terms):
                return None
            value=sum(((-v if r=='expense' else v) for r,v in terms),Fraction(0))
        else:
            if any(r!='expense' for r,v in terms):
                return None
            value=sum((v for r,v in terms),Fraction(0))
        if value<0:
            return None
        totals.append(value)
    return _answer(p,abs(totals[0]-totals[1]),'|{} - {}|'.format(*(format_number(v) for v in totals)))


def _same_proceeds(p, ns):
    """The same receipt at two per-unit rates requires different quantities."""
    t,q=p.text.lower(),p.question
    if len(ns)!=3 or not all(n.kind=='money' for n in ns):
        return None
    if not _has(r'\bhow many more\b',q) or not _has(r'\bsame amount\b',q):
        return None
    a,b,total=ns
    la,ea=_price(p,ns,a); lb,eb=_price(p,ns,b)
    if not ea or not eb or not la or not _same(la,lb) or min(a.value,b.value)<=0:
        return None
    if not _has(r'\b(?:collected|earned|made|received)\s*$',t[:total.start]):
        return None
    value=abs(total.value/a.value-total.value/b.value)
    return _answer(p,value,'|{} / {} - {} / {}|'.format(format_number(total.value),format_number(a.value),format_number(total.value),format_number(b.value)))


def _scaled_value(p, ns):
    """A multiplicative change in a quantity, valued at a common unit price."""
    t,q=p.text.lower(),p.question
    money=[n for n in ns if n.kind=='money']
    counts=[n for n in ns if n.kind!='money']
    if len(money)!=1 or len(counts)!=2 or not _has(r'\b(?:more|difference)\b',q):
        return None
    base,factor=counts
    if not _has(r'^\s+times\b',t[factor.end:]):
        return None
    price=money[0]
    unit=_noun(t[base.end:]); label,explicit=_price(p,ns,price)
    if not unit or not explicit or not _same(unit,label):
        return None
    if not _has(r'\b(?:starting|original|as|that|number of|amount of)\b',t[factor.end:]):
        return None
    if _has(r'\b(?:total|together|altogether|all)\b',q):
        return None
    value=base.value*abs(factor.value-1)*price.value
    return _answer(p,value,'{} * |{} - 1| * {}'.format(format_number(base.value),format_number(factor.value),format_number(price.value)))


def _bundle(p, ns):
    """One complete purchase set per person, including the purchaser."""
    t,q=p.text.lower(),p.question
    if len(ns)<3 or not all(n.kind=='money' for n in ns) or not _has(r'^how many (?:of (?:his|her|their) )?friends\b',q):
        return None
    if not _has(r'\b(?:himself|herself|themselves) and (?:his|her|their) friends\b',p.body):
        return None
    cash=[n for n in ns if _role(t,n,_bounds(t,n)[0])=='balance']
    if len(cash)!=1:
        return None
    prices=[n for n in ns if n is not cash[0]]
    if not all(_price(p,ns,n)[1] for n in prices):
        return None
    cost=sum((n.value for n in prices),Fraction(0))
    if cost<=0:
        return None
    value=cash[0].value//cost-1
    return _answer(p,value,'floor({} / ({})) - 1'.format(format_number(cash[0].value),_expr([n.value for n in prices])))


def _per_item_surcharge(p, ns):
    """An explicit per-item price plus an additive per-item surcharge."""
    t=p.text.lower()
    money=[n for n in ns if n.kind=='money']
    counts=[n for n in ns if n.kind!='money']
    if len(money)!=2 or len(counts)!=1 or not _has(r'\b(?:cost|pay|paid|price)\b',p.question):
        return None
    a,b=money; c=counts[0]
    if not _has(r'^\s*,?\s*plus (?:another |an extra |an additional )?$',t[a.end:b.start]):
        return None
    if not _has(r'\bfor each\b|\beach [a-z]+ costs?\b',t[:a.start]):
        return None
    label,explicit=_price(p,ns,a)
    if not explicit or not _same(label,_noun(t[c.end:])):
        return None
    if not _has(r'\b(?:tax|fee|surcharge)\b',t[b.end:c.start]):
        return None
    return _answer(p,c.value*(a.value+b.value),'{} * ({} + {})'.format(format_number(c.value),format_number(a.value),format_number(b.value)))


def _missing_category(p, ns):
    """Known receipts = one category's sales plus unknown category's sales."""
    t,q=p.text.lower(),p.question
    money=[n for n in ns if n.kind=='money']
    counts=[n for n in ns if n.kind!='money']
    if len(money)!=3 or len(counts)!=1 or not _has(r'^how many\b',q):
        return None
    if _has(r'\b(?:more|less|times|percent|discount)\b',t):
        return None
    c=counts[0]; target=_noun(re.sub(r'^how many\s+','',q))
    unit=_noun(t[c.end:])
    priced=[(n,_price(p,ns,n)) for n in money]
    known=[n for n,(l,e) in priced if e and _same(l,unit)]
    unknown=[n for n,(l,e) in priced if e and _same(l,target)]
    if len(known)!=1 or len(unknown)!=1 or known[0] is unknown[0]:
        return None
    total=[n for n in money if n not in known+unknown]
    if len(total)!=1 or _price(p,ns,total[0])[1] or unknown[0].value<=0:
        return None
    start,end=_bounds(t,total[0])
    if not _has(r'\b(?:sold|earned|total|made|collected)\b',t[start:total[0].start]):
        return None
    value=(total[0].value-c.value*known[0].value)/unknown[0].value
    if value.denominator!=1:
        return None
    return _answer(p,value,'({} - {} * {}) / {}'.format(format_number(total[0].value),format_number(c.value),format_number(known[0].value),format_number(unknown[0].value)))


def _trip_spending(p, ns):
    """A recurring number of store visits, each with a fixed expense."""
    t,q=p.text.lower(),p.question
    money=[n for n in ns if n.kind=='money']
    counts=[n for n in ns if n.kind!='money']
    if len(money)!=2 or len(counts)!=1:
        return None
    prices=[n for n in money if _has(r'^\s*(?:dollars?\s+)?every time\b',t[n.end:])]
    if len(prices)!=1:
        return None
    price=prices[0]; cash=next(n for n in money if n is not price); c=counts[0]
    if not _has(r'\bspends?\s*$',t[:price.start]):
        return None
    m=re.match(r'\s+(?:trips?|visits?)\b[^.;]*?\b(?:every|per|a|each) (day|week|month|year)\b',t[c.end:])
    duration=re.search(r'\b(?:after|for|in) (?:a|one) (day|week|month|year)\b',t)
    if not m or not duration:
        return None
    factor=_scale(m.group(1),duration.group(1))
    if factor is None:
        return None
    expense=price.value*c.value*factor
    if _has(r'\b(?:at first|originally|initially|beginning)\b',q) and _has(r'^\s*(?:dollars?\s+)?left\b',t[cash.end:]):
        value=cash.value+expense
    elif _has(r'\b(?:left|remaining|will be in)\b',q) and _role(t,cash,0)=='balance':
        value=cash.value-expense
    else:
        return None
    return _answer(p,value,'Starting/remaining cash adjusted by {} * {} * {}'.format(format_number(price.value),format_number(c.value),factor))


def _unsold_value(p, ns):
    """Lost sales when a stated capacity is not fully sold."""
    t,q=p.text.lower(),p.question
    money=[n for n in ns if n.kind=='money']; counts=[n for n in ns if n.kind!='money']
    if len(money)!=1 or len(counts)!=2 or not _has(r'\b(?:lose|lost)\b',q):
        return None
    capacity,sold=counts
    if not _has(r'\b(?:hold|holds|capacity of|seats)\s*$',t[:capacity.start]) or not _has(r'\b(?:only )?sold\s*$',t[:sold.start]):
        return None
    label,explicit=_price(p,ns,money[0])
    if not explicit or not _same(label,_noun(t[sold.end:])) or sold.value>capacity.value:
        return None
    return _answer(p,(capacity.value-sold.value)*money[0].value,'({} - {}) * {}'.format(format_number(capacity.value),format_number(sold.value),format_number(money[0].value)))


def _installment_saving(p, ns):
    """Cash price compared with deposit plus fixed installments."""
    t,q=p.text.lower(),p.question
    money=[n for n in ns if n.kind=='money']; counts=[n for n in ns if n.kind!='money']
    if len(money)!=3 or len(counts)!=1 or not _has(r'\b(?:saved|save|saving|difference)\b',q):
        return None
    if not _has(r'\binstallments?\b',t) or _has(r'\b(?:percent|interest)\b',t):
        return None
    cash=[n for n in money if _has(r'\bcash price\b[^.;]*$',t[:n.start])]
    deposit=[n for n in money if _has(r'\b(?:deposit|down payment) of\s*$',t[:n.start])]
    if len(cash)!=1 or len(deposit)!=1 or cash[0] is deposit[0]:
        return None
    rate=next(n for n in money if n not in cash+deposit); c=counts[0]
    if not _has(r'^\s+(?:equal )?(?:monthly |weekly )?installments?\b',t[c.end:]):
        return None
    return _answer(p,deposit[0].value+c.value*rate.value-cash[0].value,'{} + {} * {} - {}'.format(format_number(deposit[0].value),format_number(c.value),format_number(rate.value),format_number(cash[0].value)))


def _required_income(p, ns):
    """Desired remainder minus the remainder from current income/expenses."""
    t,q=p.text.lower(),p.question
    if not all(n.kind=='money' for n in ns) or not _has(r'\bmore money\b.*\bmake\b',q):
        return None
    wanted=[n for n in ns if _has(r'^\s+left\b',t[n.end:]) and _has(r'\b(?:wants?|needs?)\b[^.;]*$',t[:n.start])]
    if len(wanted)!=1:
        return None
    income=[]; expenses=[]
    last_role=None
    for i,n in enumerate(ns):
        if n in wanted:
            continue
        role=_role(t,n,ns[i-1].end if i else 0)
        if role is None and i and not _has(r'[.;]',t[ns[i-1].end:n.start]):
            role=last_role
        last_role=role
        if role=='income': income.append(n.value)
        elif role=='expense': expenses.append(n.value)
        else: return None
    if len(income)!=1 or not expenses:
        return None
    value=wanted[0].value+sum(expenses,Fraction(0))-income[0]
    return _answer(p,max(Fraction(0),value),'{} + ({}) - {}'.format(format_number(wanted[0].value),_expr(expenses),format_number(income[0])))


def _area_with_fee(p, ns):
    """Rectangle area times a square-unit price plus a fixed removal fee."""
    t=p.text.lower()
    money=[n for n in ns if n.kind=='money']; counts=[n for n in ns if n.kind!='money']
    if len(money)!=2 or len(counts)!=2 or not _has(r'\b(?:cost|pay|paid|price)\b',p.question):
        return None
    rates=[n for n in money if _has(r'^\s+per square (?:foot|feet|meter|yard)\b',t[n.end:])]
    if len(rates)!=1:
        return None
    rate=rates[0]; fee=next(n for n in money if n is not rate)
    if not _has(r'\b(?:remove|removal|installation|install)\b',t[fee.end:_bounds(t,fee)[1]]):
        return None
    a,b=counts
    if not _has(r'^\s*(?:\*|x|by)\s*$',t[a.end:b.start]):
        return None
    dimensions=re.match(r'^\s*(feet|foot|meters?|yards?)\b',t[b.end:])
    pricing=re.match(r'^\s+per square (foot|feet|meter|yard)\b',t[rate.end:])
    if not dimensions or not pricing or _singular(dimensions.group(1))!=_singular(pricing.group(1)):
        return None
    return _answer(p,fee.value+a.value*b.value*rate.value,'{} + {} * {} * {}'.format(format_number(fee.value),format_number(a.value),format_number(b.value),format_number(rate.value)))


def _fuel_cost(p, ns):
    """Sum explicit journey distances, divide by distance per fuel unit."""
    t=p.text.lower()
    money=[n for n in ns if n.kind=='money']; counts=[n for n in ns if n.kind!='money']
    if len(money)!=1 or not _has(r'\b(?:cost|spend|spent|pay)\b',p.question):
        return None
    price=money[0]
    if not _has(r'\b(?:gallon|liter|litre)\b[^.;]*\bcosts?\s*$',t[:price.start]):
        return None
    rates=[c for c in counts if _has(r'\b(?:gallon|liter|litre)\b[^.;]*\b(?:drive|travel|go)\s*$',t[:c.start])]
    if len(rates)!=1:
        return None
    rate=rates[0]; distance_unit=_head(_noun(t[rate.end:]))
    distances=[c for c in counts if c is not rate and _head(_noun(t[c.end:]))==distance_unit]
    definitions=[c for c in counts if c not in distances and c is not rate]
    if not distances or rate.value<=0 or any(c.value!=1 or not _has(r'^\s+(?:gallon|liter|litre)\b',t[c.end:]) for c in definitions):
        return None
    value=sum((c.value for c in distances),Fraction(0))/rate.value*price.value
    return _answer(p,value,'({}) / {} * {}'.format(_expr([c.value for c in distances]),format_number(rate.value),format_number(price.value)))


def _hypothetical(p, ns):
    """'If X had D more/less, X would have V' gives X = V -/+ D."""
    t,q=p.text.lower(),p.question
    if not all(n.kind=='money' for n in ns) or not _has(r'\b(?:altogether|total|together)\b',q):
        return None
    values={}; used=set(); pending=[]
    for match in re.finditer(r'\bif ([a-z]+) (?:had|has)\s+',p.body):
        local=[n for n in ns if match.end()<=n.start and not _has(r'[.;]',t[match.end():n.start])]
        if not local:
            return None
        delta=local[0]
        direction=re.match(r'\s+(more|less)\b',t[delta.end:])
        if not direction:
            return None
        sign=-1 if direction.group(1)=='more' else 1
        if len(local)==2:
            total=local[1]; values[match.group(1)]=total.value+sign*delta.value
            used.update([id(total),id(delta)])
        elif len(local)==1:
            m=re.search(r'\bsame (?:amount of )?money as ([a-z]+)\b',t[delta.end:_bounds(t,delta)[1]])
            if not m:
                return None
            pending.append((match.group(1),m.group(1),sign*delta.value)); used.add(id(delta))
        else:
            return None
    for subject,reference,adjustment in pending:
        if reference not in values:
            return None
        values[subject]=values[reference]+adjustment
    if len(used)!=len(ns) or len(values)<2 or min(values.values())<0:
        return None
    return _answer(p,sum(values.values(),Fraction(0)),_expr(list(values.values())))


def _average_target(p, ns):
    """One final earning needed to reach a specified average."""
    t,q=p.text.lower(),p.question
    money=[n for n in ns if n.kind=='money']; counts=[n for n in ns if n.kind!='money']
    if len(counts)!=2 or len(money)<3 or not _has(r'\baverage of\b',q):
        return None
    total,past=counts
    if not _has(r'\b(?:past|last)\s*$',t[:past.start]) or not _has(r'^\s+(?:days?|nights?)\b',t[past.end:]):
        return None
    target=[n for n in money if n.start>=len(p.body)]
    if len(target)!=1 or past.value!=len(money)-1 or total.value!=past.value+1:
        return None
    if not _has(r'^\s+days? a week\b',t[total.end:]):
        return None
    earned=[n.value for n in money if n not in target]
    value=total.value*target[0].value-sum(earned,Fraction(0))
    return _answer(p,value,'{} * {} - ({})'.format(format_number(total.value),format_number(target[0].value),_expr(earned)))


def _equal_split_unknown(p, ns):
    """A member's equal share determines the total of several expenses."""
    t,q=p.text.lower(),p.question
    if not _has(r'\b(?:split|share)\b[^.;]*\bequally\b',p.body):
        return None
    money=[n for n in ns if n.kind=='money']; counts=[n for n in ns if n.kind!='money']
    if len(money)<3 or not 1<=len(counts)<=2 or not _has(r'\b(?:whole|total|all)\b',q):
        return None
    group=counts[0]
    if not _has(r'^\s+(?:[a-z]+\s+)?(?:roommates?|people|friends?|partners?)\b',t[group.end:]):
        return None
    if len(counts)==2 and (counts[1].value!=1 or not _has(r'^\s+(?:roommate|person|friend|partner)\b',t[counts[1].end:])):
        return None
    shares=[n for n in money if _has(r'^\s+(?:in all|in total|altogether)\b',t[n.end:])]
    if len(shares)!=1:
        return None
    share=shares[0]; expenses=[n.value for n in money if n is not share]
    return _answer(p,group.value*share.value-sum(expenses,Fraction(0)),
                   '{} * {} - ({})'.format(format_number(group.value),format_number(share.value),_expr(expenses)))


def _pack_and_single(p, ns):
    """Buy an exact quantity using complete packages and individual units."""
    t,q=p.text.lower(),p.question
    money=[n for n in ns if n.kind=='money']; counts=[n for n in ns if n.kind!='money']
    if len(money)!=2 or len(counts)!=2 or not _has(r'\b(?:cheaper|cheapest|least)\b',t):
        return None
    size,total=counts
    if not _has(r'\b(?:pack|package|box) of\s*$',t[:size.start]):
        return None
    unit=_noun(t[size.end:]); target=_noun(t[total.end:])
    if not _same(unit,target) or size.value.denominator!=1 or total.value.denominator!=1 or size.value<=0:
        return None
    package=[n for n in money if size.end<n.start<total.start
             and not _has(r'[.;]',t[size.end:n.start])]
    if len(package)!=1:
        return None
    single=next(n for n in money if n not in package)
    label,explicit=_price(p,ns,single)
    if not explicit or not _same(label,unit):
        return None
    packs=total.value//size.value
    remainder=total.value-packs*size.value
    value=min(total.value*single.value,packs*package[0].value+remainder*single.value)
    return _answer(p,value,'Minimum exact purchase: {} packages and {} individual units'.format(packs,format_number(remainder)))


def _missing_receipt(p, ns):
    """Total paid minus the fully priced, itemized part of the basket."""
    t,q=p.text.lower(),p.question
    if not _has(r'\b(?:different|other|remaining|unmentioned)\b',q):
        return None
    money=[n for n in ns if n.kind=='money']; counts=[n for n in ns if n.kind!='money']
    totals=[n for n in money if _has(r'\b(?:in total|altogether)\b[^.;]*\bpaid\s*$',t[:n.start])]
    if len(totals)!=1 or not counts:
        return None
    total=totals[0]; used=set(); terms=[]
    for n in money:
        if n is total: continue
        label,explicit=_price(p,ns,n)
        matches=[c for c in counts if id(c) not in used and _compatible(label,_noun(t[c.end:]))]
        if len(matches)!=1 or not explicit:
            return None
        used.add(id(matches[0])); terms.append(n.value*matches[0].value)
    if len(used)!=len(counts): return None
    return _answer(p,total.value-sum(terms,Fraction(0)),
                   '{} - ({})'.format(format_number(total.value),_expr(terms)))


_WEEKDAYS=r'(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)'


def _weekly_named_sales(p, ns):
    """Each named weekday specifies one occurrence of a counted service."""
    t,q=p.text.lower(),p.question
    money=[n for n in ns if n.kind=='money']; counts=[n for n in ns if n.kind!='money']
    if len(money)!=1 or not counts or not _has(r'\bin a week\b|\bper week\b',q):
        return None
    if _has(r'\b(?:times|twice|thrice|more|less|half)\b',p.body):
        return None
    price=money[0]; label,explicit=_price(p,ns,price)
    if not label or not explicit:
        return None
    quantities=[]; days=set()
    for c in counts:
        if not _compatible(label,_noun(t[c.end:])):
            return None
        start,end=_bounds(t,c)
        weekdays=re.findall(_WEEKDAYS,t[start:c.start])
        if not weekdays or len(set(weekdays))!=len(weekdays) or days & set(weekdays):
            return None
        days.update(weekdays); quantities.append(c.value*len(weekdays))
    return _answer(p,sum(quantities,Fraction(0))*price.value,
                   '({}) * {}'.format(_expr(quantities),format_number(price.value)))


def _weekly_named_prices(p, ns):
    """Several named editions/visits have prices; repeat the weekly basket."""
    t=p.text.lower()
    money=[n for n in ns if n.kind=='money']; counts=[n for n in ns if n.kind!='money']
    if len(money)<2 or len(counts)!=1 or not _has(r'^\s+weeks?\b',t[counts[0].end:]):
        return None
    if _has(r'\b(?:times|more|less|half|discount)\b',t):
        return None
    days=set(); terms=[]
    for n in money:
        start,end=_bounds(t,n)
        weekdays=re.findall(_WEEKDAYS,t[start:n.start])
        if not weekdays or days & set(weekdays): return None
        days.update(weekdays); terms.append(n.value*len(set(weekdays)))
    return _answer(p,sum(terms,Fraction(0))*counts[0].value,
                   '({}) * {}'.format(_expr(terms),format_number(counts[0].value)))


def _resale_loss(p, ns):
    """Repeated purchases at a unit price, then a stated total resale value."""
    t,q=p.text.lower(),p.question
    money=[n for n in ns if n.kind=='money']; counts=[n for n in ns if n.kind!='money']
    if len(money)!=2 or len(counts)!=1 or not _has(r'\b(?:lose|lost)\b',q):
        return None
    c=counts[0]
    m=re.match(r'\s+[a-z -]+?\s+(?:a|per|each|every) (month|week|day)\b',t[c.end:])
    duration=re.search(r'\bat the end of (?:the|a|one) (year|month|week)\b',p.body)
    if not m or not duration:
        return None
    factor=_scale(m.group(1),duration.group(1))
    if factor is None:
        return None
    sale=[n for n in money if _has(r'\bsells?\b[^.;]*$',t[:n.start])]
    if len(sale)!=1:
        return None
    cost=next(n for n in money if n not in sale)
    if not _compatible(_price(p,ns,cost)[0],_noun(t[c.end:])):
        return None
    return _answer(p,c.value*cost.value*factor-sale[0].value,
                   '{} * {} * {} - {}'.format(format_number(c.value),format_number(cost.value),factor,format_number(sale[0].value)))


def _break_even_net(p, ns):
    """Recover fixed expenses from income less running cost per hour."""
    t,q=p.text.lower(),p.question
    if not _has(r'\bbreak even\b',q) or not all(n.kind=='money' for n in ns):
        return None
    rates=[n for n in ns if _price(p,ns,n)[0]=='hour']
    if len(rates)!=2 or len(ns)<3:
        return None
    income=[]; expense=[]; fixed=[]; last=None
    for i,n in enumerate(ns):
        role=_role(t,n,ns[i-1].end if i else 0)
        if role is None and i and not _has(r'[.;]',t[ns[i-1].end:n.start]): role=last
        last=role
        if n in rates:
            if role=='income': income.append(n.value)
            elif role=='expense': expense.append(n.value)
            else: return None
        elif role=='expense': fixed.append(n.value)
        else: return None
    if len(income)!=1 or len(expense)!=1 or income[0]<=expense[0]: return None
    return _answer(p,sum(fixed,Fraction(0))/(income[0]-expense[0]),
                   '({}) / ({} - {})'.format(_expr(fixed),format_number(income[0]),format_number(expense[0])))


def _unit_quotes(p, ns):
    """Two bulk quotes, requested as one of each item."""
    t,q=p.text.lower(),p.question
    money=[n for n in ns if n.kind=='money']; counts=[n for n in ns if n.kind!='money']
    if len(money)!=2 or len(counts)!=4 or not _has(r'\b(?:pay|cost|spend)\b',q):
        return None
    source=[c for c in counts if c.start<len(p.body)]; target=[c for c in counts if c.start>=len(p.body)]
    if len(source)!=2 or len(target)!=2:
        return None
    terms=[]; used=set()
    for i,n in enumerate(money):
        local=[c for c in source if (money[i-1].end if i else 0)<=c.start<n.start]
        if len(local)!=1 or local[0].value<=0: return None
        c=local[0]
        if not _has(r'\bfor\s*$',t[c.end:n.start]) or not _has(r'^\s+in total\b',t[n.end:]): return None
        matches=[v for v in target if id(v) not in used and _same(_noun(t[v.end:]),_noun(t[c.end:]))]
        if len(matches)!=1: return None
        used.add(id(matches[0])); terms.append(n.value/c.value*matches[0].value)
    return _answer(p,sum(terms,Fraction(0)),_expr(terms))


def _area_packages(p, ns):
    """Cover a rectangle using packages labeled with their area coverage."""
    t=p.text.lower()
    money=[n for n in ns if n.kind=='money']; counts=[n for n in ns if n.kind!='money']
    if len(money)!=1 or len(counts)!=3 or not _has(r'\b(?:cost|pay|spend)\b',p.question): return None
    a,b,size=counts
    length=re.match(r'^\s*(ft|feet|meters?|yards?)\s+long\b',t[a.end:])
    width=re.match(r'^\s*(ft|feet|meters?|yards?)\s+wide\b',t[b.end:])
    coverage=re.match(r'^\s*(?:sq\.? (ft)|square (feet|meters?|yards?))\s+bags?\b',t[size.end:])
    if not length or not width or not coverage: return None
    def unit(s): return 'foot' if s=='ft' else _singular(s)
    if len({unit(length.group(1)),unit(width.group(1)),unit(coverage.group(1) or coverage.group(2))})!=1: return None
    if not _has(r'^\s+(?:a|per|each) bag\b',t[money[0].end:]) or size.value<=0: return None
    quantity=a.value*b.value/size.value
    packages=-(-quantity.numerator//quantity.denominator)
    return _answer(p,packages*money[0].value,'ceil({} * {} / {}) * {}'.format(format_number(a.value),format_number(b.value),format_number(size.value),format_number(money[0].value)))


def _salary_topup(p, ns):
    """An employer funds the same raise for every employee from her salary."""
    t,q=p.text.lower(),p.question
    money=[n for n in ns if n.kind=='money']; counts=[n for n in ns if n.kind!='money']
    if len(money)!=3 or len(counts)!=1 or not _has(r'\bsalary\b',q): return None
    c=counts[0]
    if not _has(r'^\s+employees\b',t[c.end:]) or not _has(r'\bpart of (?:his|her|their) salary\b',q): return None
    old,employee,new=money
    if not old.start<c.start<employee.start<new.start or new.start<len(p.body): return None
    if not _has(r'\ball of (?:his|her|their) employees\b',q): return None
    if not all(_price(p,ns,n)[0]=='year' for n in money): return None
    return _answer(p,old.value-c.value*(new.value-employee.value),
                   '{} - {} * ({} - {})'.format(format_number(old.value),format_number(c.value),format_number(new.value),format_number(employee.value)))


def _repeated_expense(p, ns):
    """Starting cash, one purchase, then twice/thrice that same expense."""
    t,q=p.text.lower(),p.question
    if len(ns)!=2 or not all(n.kind=='money' for n in ns) or not _has(r'\b(?:left|remaining)\b',q): return None
    a,b=ns
    if _role(t,a,0)!='balance' or _role(t,b,a.end)!='expense': return None
    relation=re.search(r'\bspent (twice|thrice|double|triple) as much as (?:he|she|they) spent\b',t[b.end:])
    if not relation: return None
    factor={'twice':2,'thrice':3,'double':2,'triple':3}[relation.group(1)]
    return _answer(p,a.value-(1+factor)*b.value,'{} - (1 + {}) * {}'.format(format_number(a.value),factor,format_number(b.value)))


def solve(problem):
    t=problem.text.lower()
    if not _has(r'[$£€]|\b(?:dollars?|cents?|euros?)\b',t):
        return None
    ns=_numbers(problem)
    ns=[n for n in ns if not (n.value==1 and n.kind!='money'
        and _has(r'^\s+day (?:passes|tickets)\b',t[n.end:]))]
    if not 2<=len(ns)<=12 or any(n.kind=='percent' or n.value<0 for n in ns):
        return None
    if len(_currencies(problem, ns))>1:
        return None
    if re.match(r'how many (?!(?:more |fewer )?(?:dollars?|cents?|euros?)\b)',problem.question):
        for rule in (_break_even_net,_missing_category,_bundle,_same_proceeds):
            result=rule(problem,ns)
            if result is not None:
                return result
        return None
    if not _has(r'\b(?:money|dollars?|cents?|pay|paid|spend|spent|costs?|price|earn|earned|earnings|make|made|change|profit|salary|left|remaining|raise|raised|worth|difference)\b',problem.question) and not _has(r'^how many\b',problem.question):
        return None
    for rule in (_resale_loss,_break_even_net,_unit_quotes,_area_packages,_salary_topup,_repeated_expense,
                 _average_target,_equal_split_unknown,_pack_and_single,_missing_receipt,
                 _weekly_named_sales,_weekly_named_prices,
                 _trip_spending,_unsold_value,_installment_saving,_required_income,
                 _area_with_fee,_fuel_cost,_hypothetical,
                 _missing_category,_bundle,_same_proceeds,_scaled_value,_per_item_surcharge,
                 _owners,_introductory_rate,_unit_margin,_schedule_ledger,_recurring_comparison,_basket):
        result=rule(problem,ns)
        if result is not None:
            return result
    return None
