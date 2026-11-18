"""Conservative ledgers, nested groups and shortfall calculations.

Quantities are joined by their noun units and explicit relations.  Every reader
accounts for all numbers, and leaves unresolved owners or dimensions alone.
"""
import re
from fractions import Fraction

from ..numbers import format_number
from ..problem import Problem
from .counting_and_totals_r00_a1 import _different_owner
from .counting_and_totals_r02_a4 import _normal_unit
from .counting_and_totals_r01_a3 import _phrase
from .counting_and_totals_r05_a3 import _unit as _old_unit


def _has(pattern, text):
    return re.search(pattern, text) is not None


def _sum(values):
    return sum(values, Fraction(0))


def _fmt(values, op=' + '):
    return op.join(format_number(v) for v in values)


def _answer(value, expression):
    if value < 0:
        return None
    return value, expression + ' = ' + format_number(value) + '.'


def _unit(tail):
    compound = re.match(r'\s*-(words?|pages?|minutes?|hours?|ounces?|liters?|meters?)\b',tail)
    if compound:
        return _normal_unit(compound.group(1))
    if re.match(r'\s*leaves\b',tail):
        return 'leaf'
    tail = re.split(r'\b(?:drive|drives|carry|carries|spends?|practicing|throwing|'
                    r'peeling|sharpening|seated|standing|attended|grow|grown|'
                    r'puts?|selected|chosen|sharpened|uses?|opened|up|'
                    r'still|safely|needed|want|wants|around|near|under|above|'
                    r'below|across|inside|available|buried|wanted|correctly|but|lose)\b', tail)[0]
    tail = re.sub(r'^\s+(?:more|extra|additional)\b', ' ', tail)
    unit = _old_unit(tail)
    return {'kilo': 'kilogram', 'mg': 'milligram'}.get(unit, unit)


def _asked(p):
    m = re.match(r'how (?:many|much)\s+(?:(?:more|fewer|additional|extra|total)\s+)*(.+)', p.question)
    if not m:
        m = re.search(r'(?:total|combined) (?:number|amount) of\s+(.+)', p.question)
    if not m:
        m = re.match(r'(?:calculate|find) (?:the )?(?:total )?(?:number|amount) of\s+(.+)',p.question)
    if not m:
        return ''
    return _unit(m.group(1))


def _tails(p):
    ns = p.numbers
    text = p.text.lower()
    return [text[n.end:ns[i+1].start if i+1 < len(ns) else len(p.body)] for i, n in enumerate(ns)]


def _token(p):
    text = p.text.lower()
    for i, n in reversed(list(enumerate(p.numbers))):
        text = text[:n.start] + 'Q{}'.format(i) + text[n.end:]
    return text


def _asked_label(p):
    m = re.match(r'how (?:many|much)\s+(?:(?:more|additional|extra|total)\s+)*(.+)',p.question)
    return _phrase(m.group(1)) if m else []


def _matches_label(p, tail):
    """A qualified query cannot absorb stock of another qualified category."""
    asked = _asked_label(p)
    actual = _phrase(tail)
    return len(asked) < 2 or not actual or actual == asked


def _recipe(p):
    """A fronted recipe's yield and input, scaled to a requested yield."""
    ns = p.numbers
    if len(ns) != 3 or ns[-1].start < len(p.body):
        return None
    text = p.text.lower()
    a, b, c = ns
    if not re.search(r'\bto (?:make|produce|prepare|bake)\s*$', text[:a.start]):
        return None
    if not re.search(r'\b(?:needs?|requires?|uses?)\s*$', text[a.end:b.start]):
        return None
    units = [_unit(text[n.end:]) for n in ns]
    if units[0] != units[2] or not units[0] or units[0] == units[1] or _asked(p) != units[1]:
        return None
    if _has(r'\b(?:more|less|left|remaining|than|each|every|per|half|twice)\b', text):
        return None
    return _answer(b.value*c.value/a.value, '{} x {} / {}'.format(*map(format_number,(b.value,c.value,a.value))))


def _nested_groups(p):
    """Read explicit container/content edges, including singular denominators."""
    ns = p.numbers
    text = p.text.lower()
    if not 2 <= len(ns) <= 6 or _has(r'\b(?:more|less|fewer|than|left|remaining|half|twice|except|lost|sold|gave|average|ratio|percent|another)\b',text):
        return None
    tails = _tails(p)
    units = [_unit(t) for t in tails]
    if not all(units):
        return None
    parents = {}
    denominator_indices = set()
    for i, n in enumerate(ns):
        before = re.split(r'[.!?;]', text[:n.start])[-1]
        after = re.split(r'[.!?;]|,? and\b', tails[i])[0]
        group = None
        m = re.search(r'\b(?:each|every) ([a-z]+) (?:[a-z]+ ){0,2}(?:has|have|holds?|contains?|uses?|needs?|opened|carries|carry|makes?)\s*$',before)
        if m:
            group = _normal_unit(m.group(1))
        m = re.search(r'\bin each ([a-z]+),? (?:he |she |they |it )?(?:opened|placed|put|has|holds|contains)\s*$',before)
        if m:
            group = _normal_unit(m.group(1))
        m = re.search(r'\b(?:per|each|every|in a single|in single|in a|on a baking|on a|in one) ([a-z]+)\b',after)
        if m and m.group(1) not in ('with','having','of','one'):
            group = _normal_unit(m.group(1))
        # "N tanks with a capacity of M liters" explicitly nests contents.
        if i and re.fullmatch(r'\s+[a-z]+ (?:with|having) (?:a )?capacity of\s+',text[ns[i-1].end:n.start]):
            group = units[i-1]
        if i and re.fullmatch(r'\s+[a-z]+,? each (?:with|having)\s+',text[ns[i-1].end:n.start]):
            group = units[i-1]
        # "M objects in one row" has an explicit denominator quantity.
        if i+1 < len(ns) and re.fullmatch(r'\s+[a-z]+ in\s+',tails[i]) and ns[i+1].value == 1:
            group = units[i+1]
            denominator_indices.add(i+1)
        if group:
            matches = [j for j,u in enumerate(units) if j != i and u == group and j not in denominator_indices]
            if len(matches) != 1:
                return None
            parents[i] = matches[0]
    active = set(range(len(ns))) - denominator_indices
    roots = active - set(parents.values())
    if len(roots) != 1 or len(parents) != len(active)-1:
        return None
    root = next(iter(roots))
    if _asked(p) != units[root] or not _matches_label(p,tails[root]):
        return None
    visited = set()
    i = root
    factors = []
    while i not in visited:
        visited.add(i)
        factors.append(ns[i].value)
        if i not in parents:
            break
        i = parents[i]
    if visited != active:
        return None
    value = Fraction(1)
    for factor in factors:
        value *= factor
    return _answer(value, _fmt(factors,' x '))


_REMOVE = r'took|ate|eats?|lost|loses?|sold|sells?|used|uses?|gave|gives?|removed|broke|taken|takes?'
_START = r'has|have|had|there are|there were|puts?|put|collected|picked|bought|buys?|purchased|made|grew|grow|grows|started (?:off |out )?with'


def _ledger(p):
    """One measured stock, with local removal events and noun ellipsis."""
    ns = p.numbers
    text = p.text.lower()
    if not 2 <= len(ns) <= 7 or any(n.start >= len(p.body) for n in ns):
        return None
    if not _has(r'\b(?:left|remaining|remain|keep|kept|in the end)\b',p.question) or _different_owner(p):
        return None
    if _has(r'\b(?:each|every|per|times|than|fewer|half|double|twice|total|some|average|ratio|percent|ago)\b',p.body):
        return None
    tails = _tails(p)
    units = [_unit(t) for t in tails]
    unit = units[0]
    asked = _asked(p)
    if not asked and re.match(r'how many did [a-z]+ keep\b',p.question):
        asked = unit
    if not unit:
        return None
    # A measured mass is queried by the material, rather than its measure.
    material_query = bool(re.match(r'what is the (?:mass|weight) of ([a-z]+)',p.question))
    if asked != unit and not material_query:
        return None
    if material_query:
        material = re.match(r'what is the (?:mass|weight) of ([a-z]+)',p.question).group(1)
        if unit not in ('kilogram','gram','pound','ounce') or any(not _has(r'\b'+re.escape(material)+r'\b',t) for t in tails):
            return None
    values = []
    signs = []
    previous = None
    for i,n in enumerate(ns):
        before = text[ns[i-1].end if i else 0:n.start]
        clause = re.split(r'[.!?;]|\b(?:and|but|while|then)\b',before)[-1]
        suffix = re.split(r'[.!?;]',tails[i])[0]
        if units[i] not in ('',unit):
            return None
        if not _matches_label(p,tails[i]):
            return None
        post = _has(r'\b(?:were|was|are|is) (?:sold|removed|eaten|used|taken)\b',suffix)
        remove = _has(r'\b(?:'+_REMOVE+r')\b',clause)
        purchase = _has(r'\b(?:buys?|bought|purchased)\b',clause)
        if purchase and _has(r'\bshelf\b',text[:ns[0].end]+p.question):
            remove = True
        start = _has(r'\b(?:'+_START+r')\b',clause)
        if i == 0:
            if not start:
                return None
            sign = 1
        elif post or remove:
            sign = -1
        elif start:
            # A buyer removes stock from a shelf, but acquiring goods in a
            # personal ledger needs explicit ownership; leave that ambiguous.
            sign = 1
        elif not _has(r'[.!?;]',before) and _has(r'\band\b|,',before):
            sign = previous
        else:
            return None
        signs.append(sign)
        values.append(sign*n.value)
        previous = sign
    if -1 not in signs:
        return None
    expression = ''.join((' - ' if s < 0 else ' + ')+format_number(n.value) for s,n in zip(signs,ns)).lstrip(' +')
    return _answer(_sum(values),expression)


def _category_difference(p):
    """Separate category stocks, then compare two explicitly named sides."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or any(n.start >= len(p.body) for n in ns):
        return None
    q = re.match(r'how many (?:more|fewer) (.+?) (?:does .+? have )?(?:are [a-z]+ )?than (.+?)\?',p.question)
    if not q or _has(r'\b(?:each|every|per|times|half|twice|percent)\b',text):
        return None
    left = re.findall(r'[a-z]+',q.group(1))
    right = re.findall(r'[a-z]+',q.group(2))
    units = [_unit(t) for t in _tails(p)]
    distinct = set(units[:2])
    if not all(distinct) or len(distinct) != 2:
        return None
    # A removal from one category updates its count before comparison.
    if units[2] in distinct and _has(r'\b(?:gave|sold|lost|removed|ate)\b',text[ns[1].end:ns[2].start]):
        if not all(any(_normal_unit(w) == u for w in left+right) for u in distinct):
            return None
        totals = {units[0]:ns[0].value,units[1]:ns[1].value}
        totals[units[2]] -= ns[2].value
        if min(totals.values()) < 0:
            return None
        return _answer(abs(totals[units[0]]-totals[units[1]]), 'Difference after removing '+format_number(ns[2].value))
    # A disjoint list can compare one named category to two named together.
    if len(set(units)) == 3:
        a = [n.value for n,u in zip(ns,units) if any(_normal_unit(w)==u for w in left)]
        b = [n.value for n,u in zip(ns,units) if any(_normal_unit(w)==u for w in right)]
        if len(a)+len(b) == len(ns) and a and b:
            return _answer(abs(_sum(a)-_sum(b)), '|('+_fmt(a)+') - ('+_fmt(b)+')|')
    return None


def _goal_partition(p):
    """A stated whole minus selected disjoint parts; query an unfilled part."""
    ns = list(p.numbers)
    text = p.text.lower()
    if not 3 <= len(ns) <= 6 or _has(r'\b(?:each|every|per|times|half|twice|percent|than|fewer|sold|lost)\b',text):
        return None
    totals = []
    for i,n in enumerate(ns):
        before = text[ns[i-1].end if i else 0:n.start]
        if _has(r'\b(?:total of|total|only|capacity of)\s*$',before):
            totals.append(i)
    if len(totals) != 1:
        return None
    ti = totals[0]
    # A repeated whole in the question is a reference, not another part.
    extras = [i for i,n in enumerate(ns) if n.start >= len(p.body)]
    if extras:
        if extras != [len(ns)-1] or ns[-1].value != ns[ti].value or not _has(r'\btotal\b',text[ns[-1].end:]):
            return None
        ns.pop()
    parts = [n for i,n in enumerate(ns) if i != ti]
    if any(n.start >= len(p.body) for n in parts):
        return None
    asked = _asked(p)
    if not asked or any(_unit(text[n.end:]) == asked for n in parts):
        return None
    if not (_has(r'\b(?:rest|remaining)\b',p.body) or _has(r'\b(?:need|more|pick|selected|chosen)\b',text)):
        return None
    for n in parts:
        i = ns.index(n)
        if _unit(text[n.end:]) != _unit(text[ns[ti].end:]):
            before = text[ns[i-1].end if i else 0:n.start]
            if not _has(r'\b(?:chosen|selected|picked)\b',before):
                return None
    return _answer(ns[ti].value-_sum(n.value for n in parts),format_number(ns[ti].value)+' - ('+_fmt(n.value for n in parts)+')')


def _group_shortfall(p):
    """Required output = groups x per-group need, minus owned output."""
    ns = list(p.numbers)
    text = p.text.lower()
    if not re.match(r'how (?:many|much) more\b',p.question) or _has(r'\b(?:than|half|twice|percent|fewer)\b',text):
        return None
    # An explicitly repeated group count in "all N groups" is a reference.
    if len(ns) == 4 and ns[-1].start >= len(p.body) and ns[-1].value == ns[0].value:
        if not _has(r'\ball\s*$',text[:ns[-1].start]):
            return None
        repeated_group = _unit(text[ns[-1].end:])
        ns.pop()
    else:
        repeated_group = None
    if len(ns) != 3:
        return None
    tails = [text[n.end:ns[i+1].start if i+1 < len(ns) else len(p.body)] for i,n in enumerate(ns)]
    units = [_unit(t) for t in tails]
    rates = []
    for i,t in enumerate(tails):
        m = re.search(r'\bper ([a-z]+)',t)
        if m:
            rates.append((i,_normal_unit(m.group(1))))
    if len(rates) != 1:
        return None
    ri,group = rates[0]
    stock = [i for i,u in enumerate(units) if i != ri and u == units[ri]]
    if len(stock) != 1 or _asked(p) != units[ri]:
        return None
    si = stock[0]
    ci = next(i for i in range(3) if i not in (ri,si))
    if units[ci] != group and repeated_group != group:
        return None
    if not re.search(r'\b(?:has|have|had|already)\s*$',text[:ns[si].start]):
        return None
    return _answer(ns[ri].value*ns[ci].value-ns[si].value,
                   '{} x {} - {}'.format(*map(format_number,(ns[ci].value,ns[ri].value,ns[si].value))))


def _capacity_remainder(p):
    """A limit minus counted servings of a measured quantity."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or not _has(r'\b(?:more|remaining|left)\b',p.question):
        return None
    limit,rate,count = ns
    if not _has(r'\b(?:maximum|limit|capacity|goal|target)\b',text[:limit.start]):
        return None
    unit = _unit(text[limit.end:])
    if not unit or _unit(text[rate.end:]) != unit:
        return None
    asked = _asked(p)
    if asked != unit and (not asked or not all(
            _has(r'\b'+re.escape(asked)+r'\b',t)
            for t in (text[:rate.start],_tails(p)[1]))):
        return None
    if not re.search(r'\beach [a-z ]+ (?:has|contains|holds|provides)\s*$',text[:rate.start]):
        return None
    if not re.match(r'\s+of (?:them|these|those)\b',text[count.end:]):
        return None
    return _answer(limit.value-rate.value*count.value,'{} - {} x {}'.format(*map(format_number,(limit.value,rate.value,count.value))))


def _multiple_of_time(p):
    """One activity's duration and a multiple for another, queried together."""
    if len(p.numbers) != 2 or not _has(r'\b(?:total|altogether|combined)\b|\bfrom .+? (?:until|through|to)\b',p.question):
        return None
    a,b = p.numbers
    text = p.text.lower()
    unit = _unit(text[a.end:])
    if not unit or _asked(p) not in (unit,'time'):
        return None
    if not re.match(r'\s+times (?:that|this|the) (?:(?:amount of )?time|much\b)',text[b.end:]):
        return None
    if _has(r'\b(?:more|less|fewer|than|each|per|every|left)\b',text):
        return None
    return _answer(a.value*(1+b.value),'{} x (1 + {})'.format(format_number(a.value),format_number(b.value)))


def _continued_periods(p):
    """An unchanged daily rate applied to consecutive stated durations."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or not _has(r'\b(?:continue|continues|another|next)\b',text):
        return None
    a,b,c = ns
    if not re.match(r'\s+hours? (?:each|every|per|a) day\b',text[a.end:]):
        return None
    if any(_unit(text[n.end:]) != 'day' for n in (b,c)) or _asked(p) != 'hour':
        return None
    if _has(r'\b(?:less|more|than|half|twice|lost|left|increase|decrease)\b',text):
        return None
    return _answer(a.value*(b.value+c.value),'{} x ({} + {})'.format(*map(format_number,(a.value,b.value,c.value))))


def _stock_minus_groups(p):
    """Owned stock minus per-group consumption, with an explicit group noun."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or not _has(r'\b(?:left|remain|remaining)\b',p.question):
        return None
    if _different_owner(p) or _has(r'\b(?:than|half|twice|percent|more|fewer)\b',text):
        return None
    tails = _tails(p)
    units = [_unit(t) for t in tails]
    stock,rate,count = ns
    if not units[0] or units[0] != units[1] or _asked(p) != units[0]:
        return None
    if not re.search(r'\b(?:has|have|had)\s*$',text[:stock.start]):
        return None
    before = text[stock.end:rate.start]
    m = re.search(r'\b(?:in |on |for )?each ([a-z ]+?),?\s*$',before)
    if not m or _unit(m.group(1)) != units[2]:
        return None
    if not _has(r'\b(?:used|uses|use|consumes?|consumed|needs?|requires?)\b',tails[1]):
        return None
    return _answer(stock.value-rate.value*count.value,'{} - {} x {}'.format(*map(format_number,(stock.value,rate.value,count.value))))


def _spent_groups(p):
    """The reduction in a stock exchanged at a stated per-unit rate."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or _has(r'\b(?:more|less|than|half|twice|percent)\b',text):
        return None
    initial,rate,remaining = ns
    units = [_unit(t) for t in _tails(p)]
    if not units[0] or units[0] != units[2] or _asked(p) != units[1]:
        return None
    if not re.search(r'\b(?:has|have|had)\s*$',text[:initial.start]):
        return None
    if not re.search(r'\b(?:leaves?|left|ends?|ended) with\s*$',text[:remaining.start]):
        return None
    if not re.search(r'\bper '+re.escape(units[0])+r'\b',text[rate.end:remaining.start]):
        return None
    return _answer((initial.value-remaining.value)*rate.value,
                   '({} - {}) x {}'.format(*map(format_number,(initial.value,remaining.value,rate.value))))


def _refill(p):
    """Fill a container back to capacity after stated withdrawals."""
    ns = p.numbers
    text = p.text.lower()
    if not 3 <= len(ns) <= 6 or not _has(r'\brefill\b',p.question):
        return None
    if any(n.start >= len(p.body) for n in ns) or _has(r'\b(?:each|per|every|half|twice|more|less|than)\b',p.body):
        return None
    unit = _unit(text[ns[0].end:])
    if not unit or _asked(p) != unit or any(_unit(text[n.end:]) != unit for n in ns):
        return None
    if not re.search(r'\b(?:had|has|have)\s*$',text[:ns[0].start]):
        return None
    if not re.search(r'\b(?:hold(?:s)?(?: up to)?|capacity of)\s*$',text[:ns[-1].start]):
        return None
    for i,n in enumerate(ns[1:-1],1):
        if not re.search(r'\b(?:uses?|used|removed|drank|consumed|lost)\s*$',text[ns[i-1].end:n.start]):
            return None
    remaining = ns[0].value-_sum(n.value for n in ns[1:-1])
    if remaining < 0 or remaining > ns[-1].value:
        return None
    return _answer(ns[-1].value-remaining,'{} - ({} - ({}))'.format(format_number(ns[-1].value),format_number(ns[0].value),_fmt(n.value for n in ns[1:-1])))


def _resource_budget(p):
    """One purchase minus explicit task requirements and accidental losses."""
    ns = p.numbers
    text = p.text.lower()
    if not 3 <= len(ns) <= 6 or not _has(r'\bleft\b',p.question):
        return None
    if _has(r'\b(?:each|every|per|more|than|half|twice|percent)\b',text):
        return None
    units = [_unit(t) for t in _tails(p)]
    if len(set(units)) != 1 or not units[0] or _asked(p) != units[0]:
        return None
    bought = []
    spent = []
    previous = None
    for i,n in enumerate(ns):
        before = text[ns[i-1].end if i else 0:n.start]
        clause = re.split(r'[.!?;]|\b(?:and|but)\b',before)[-1]
        if re.search(r'\b(?:bought|purchased|has|had)\s+(?:an? )?$',clause):
            bought.append(n.value);previous='bought'
        elif _has(r'\b(?:takes?|needs?|requires?|spilled|lost|used)\b',clause):
            spent.append(n.value);previous='spent'
        elif previous == 'spent' and _has(r'\band\b',before) and not _has(r'[.!?;]',before):
            spent.append(n.value)
        else:
            return None
    if len(bought) != 1 or len(spent) != len(ns)-1:
        return None
    return _answer(bought[0]-_sum(spent),format_number(bought[0])+' - ('+_fmt(spent)+')')


_MASS = {'pound': Fraction(16), 'ounce': Fraction(1), 'kilogram': Fraction(1000), 'gram': Fraction(1)}


def _mass_capacity(p):
    """A measured carrying capacity divided by each item's measured mass."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 2 or not _has(r'\b(?:hold|holds|capacity|fit)\b',p.body):
        return None
    cap,size = ns
    u,v = (_unit(text[n.end:]) for n in ns)
    if u not in _MASS or v not in _MASS or (u in ('pound','ounce')) != (v in ('pound','ounce')):
        return None
    m = re.search(r'\beach ([a-z]+) weighs\s*$',text[:size.start])
    if not m or _normal_unit(m.group(1)) != _asked(p):
        return None
    if not _has(r'\b(?:fit|hold|carry)\b',p.question):
        return None
    value = cap.value*_MASS[u]/(size.value*_MASS[v])
    return _answer(Fraction(value.numerator//value.denominator),'{} / {}'.format(format_number(cap.value*_MASS[u]),format_number(size.value*_MASS[v])))


def _mixture_scale(p):
    """Scale measured ingredients by repeated explicit material labels."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or _has(r'\b(?:than|more|less|half|twice|left|per|each|every|percent)\b',text):
        return None
    if not _has(r'\b(?:mixed|mixes|mix|combines?|combined)\b',p.body):
        return None
    units = []
    labels = []
    for n in ns:
        m = re.match(r'\s+([a-z]+) of ([a-z]+)\b',text[n.end:])
        if not m:
            return None
        units.append(_normal_unit(m.group(1)));labels.append(m.group(2))
    q = re.match(r'how (?:many|much) ([a-z]+) of ([a-z]+)',p.question)
    if not q or len(set(units)) != 1 or _normal_unit(q.group(1)) != units[0]:
        return None
    if labels[0] == labels[1] or labels[2] not in labels[:2]:
        return None
    known = labels.index(labels[2])
    output = 1-known
    if q.group(2) != labels[output]:
        return None
    return _answer(ns[2].value*ns[output].value/ns[known].value,'{} x {} / {}'.format(*map(format_number,(ns[2].value,ns[output].value,ns[known].value))))


def _weekday_normalization(p):
    """Daily sessions restricted to an explicit Monday-through-Friday range."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 2 or not re.search(r'\bevery (?:morning|afternoon|evening),? monday (?:through|to) friday\b',text):
        return None
    if ns[1].start < len(p.body) or _unit(text[ns[1].end:]) != 'week':
        return None
    if _asked(p) != _unit(text[ns[0].end:]):
        return None
    return _answer(ns[0].value*5*ns[1].value,
                   '{} x 5 x {}'.format(format_number(ns[0].value),format_number(ns[1].value)))


def _task_remainder(p):
    """A task's whole minus completed components, with one output unit."""
    ns = p.numbers
    text = p.text.lower()
    if not 3 <= len(ns) <= 6 or any(n.start >= len(p.body) for n in ns):
        return None
    if _has(r'\b(?:each|every|per|times|half|twice|than|percent|more|less|fewer)\b',text):
        return None
    units = [_unit(t) for t in _tails(p)]
    if not units[0] or len(set(units)) != 1:
        return None
    asked = _asked(p)
    if asked not in (units[0],'time') or (asked == 'time' and units[0] not in ('minute','hour','second')):
        return None
    # One explicit total/goal (possibly after a list) and disjoint progress.
    wholes = []
    for i,n in enumerate(ns):
        before = text[ns[i-1].end if i else 0:n.start]
        clause = re.split(r'[.!?;]',before)[-1]
        if _has(r'\b(?:total|goal|limit|needed to|needs? to|required|finished|distance across)\b',clause):
            wholes.append(i)
        elif i == 0 and _has(r'\blimit\b',_tails(p)[0]):
            wholes.append(i)
        elif i == 0 and units[0] in ('minute','hour','second') and _has(r'\bhave\b',clause):
            wholes.append(i)
    if len(wholes) != 1:
        return None
    wi = wholes[0]
    if not (_has(r'\b(?:rest|still|remaining|remain|left|goal|to get|to drive)\b',text)
            or _has(r'\b(?:exceeded|exceed)\b',p.question)):
        return None
    for i,n in enumerate(ns):
        if i == wi:
            continue
        before = text[ns[i-1].end if i else 0:n.start]
        if not _has(r'\b(?:read|drove|driven|spent|takes?|wrote|another)\b',before):
            if i == 0 or _has(r'[.!?;]',before) or not _has(r'\band\b',before):
                return None
    total = ns[wi].value
    parts = _sum(n.value for i,n in enumerate(ns) if i != wi)
    if _has(r'\bexceeded\b',p.question):
        return _answer(parts-total,format_number(parts)+' - '+format_number(total))
    return _answer(total-parts,format_number(total)+' - ('+_fmt(n.value for i,n in enumerate(ns) if i != wi)+')')


def _same_contents_additional(p):
    """One container's contents and N additional identical containers."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 2 or not _has(r'\b(?:total|in all|altogether|together)\b',p.question):
        return None
    content,extra = ns
    intro = re.search(r'\b(?:has|had|have) (?:a|an) ([a-z]+) (?:of|containing|with)\s*$',text[:content.start])
    if not intro or _asked(p) != _unit(text[content.end:]):
        return None
    m = re.match(r'\s+more ([a-z]+) with the same (?:amount|number)\b',text[extra.end:])
    if not m or _normal_unit(m.group(1)) != _normal_unit(intro.group(1)):
        return None
    if _has(r'\b(?:lost|gave|sold|used|half|twice|than|per|each)\b',text):
        return None
    return _answer(content.value*(extra.value+1),'{} x ({} + 1)'.format(format_number(content.value),format_number(extra.value)))


def _dozen_difference(p):
    """Compare two named count nouns after converting explicit dozens."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 2 or not _has(r'\b(?:more|fewer)\b.+\bthan\b',p.question):
        return None
    if _has(r'\b(?:each|per|every|half|twice|sold|lost|gave|ate)\b',p.body):
        return None
    units = []
    values = []
    dozen_found = False
    for n in ns:
        tail = text[n.end:]
        m = re.match(r'\s+dozen\b',tail)
        if m:
            dozen_found = True
            tail = tail[m.end():]
        units.append(_unit(tail))
        values.append(n.value*(12 if m else 1))
    if not dozen_found or not all(units) or units[0] == units[1]:
        return None
    if not all(any(_normal_unit(w) == u for w in re.findall(r'[a-z]+',p.question)) for u in units):
        return None
    return _answer(abs(values[0]-values[1]),'|'+_fmt(values,' - ')+'|')


def _fronted_daily_sum(p):
    """Several durations performed every day, requested for a week."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 2 or not re.match(r'every day\b',p.body):
        return None
    if not _has(r'\b(?:per|each|every|a) week\b',p.question):
        return None
    if _has(r'\b(?:than|more|less|half|twice|except|weekend|weekday)\b',text):
        return None
    units = [_unit(t) for t in _tails(p)]
    if len(set(units)) != 1 or units[0] not in ('minute','hour','second') or _asked(p) != units[0]:
        return None
    if not _has(r'\band (?:another|an additional)\b',text[ns[0].end:ns[1].start]):
        return None
    return _answer(_sum(n.value for n in ns)*7,'('+_fmt(n.value for n in ns)+') x 7')


def _sided_groups(p):
    """A count of explicitly N-sided objects, optionally for both owners."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 2 or _asked(p) != 'side':
        return None
    count,sides = ns
    if not re.fullmatch(r'\s*,?\s*',text[count.end:sides.start]):
        return None
    if not re.match(r'-sided [a-z]+\b',text[sides.end:]):
        return None
    if _has(r'\b(?:lost|gave|sold|half|twice|than|more|less)\b',text):
        return None
    factor = Fraction(1)
    if _has(r'\bboth\b',text[:count.start]):
        if not re.search(r'\b[A-Z][a-z]+ and [A-Z][a-z]+ both\b',p.text[:count.start]):
            return None
        factor = Fraction(2)
    return _answer(factor*count.value*sides.value,_fmt([factor,count.value,sides.value],' x '))


def _uniform_leftover(p):
    """Buy the minimum number of packages and report unused contents."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or not _has(r'\bleft over\b',p.question):
        return None
    count,need,capacity = ns
    units = [_unit(t) for t in _tails(p)]
    if units[1] != units[2] or not units[1] or _asked(p) != units[1]:
        # The material itself may be asked for without its length unit.
        if not (units[1] == units[2] and units[1] in ('yard','meter','inch','foot')
                and _has(r'\bhow much\b',p.question)):
            return None
    before_need = text[count.end:need.start]
    m = re.search(r'\beach ([a-z]+) needs\s*$',before_need)
    if not m or _normal_unit(m.group(1)) != units[0]:
        return None
    if not re.search(r'\beach [a-z ]+ (?:contains|holds|has)\s*$',text[need.end:capacity.start]):
        return None
    if not _has(r'\b(?:least|minimum)\b',text):
        return None
    total = count.value*need.value
    packs = total/capacity.value
    rounded = -(-packs.numerator//packs.denominator)
    return _answer(rounded*capacity.value-total,'{} x {} - {}'.format(rounded,format_number(capacity.value),format_number(total)))



def _grammatical_numbers(p):
    """Remove unambiguously grammatical 'one', then reuse relation readers."""
    text = p.text
    text = re.sub(r'\bone another\b','each other',text,flags=re.I)
    text = re.sub(r'\b(?:at|from) one end\b',lambda m:m.group().replace('one','an'),text,flags=re.I)
    # Separate coordinated named subjects so each comparison supplies its
    # own equation rather than swallowing the next subject's relation.
    if _has(r'\b(?:more|fewer|less)\b.+\bthan\b',p.body):
        text = re.sub(r',? and ([A-Z][a-z]+) ([a-z]+)\b',r'. \1 \2',text)
    if text == p.text:
        return None
    converted = Problem.read(text)
    if converted is None:
        return None
    from . import comparisons_r01_a2, comparisons_r03_a4, comparisons_r04_a3
    for module in (comparisons_r01_a2,comparisons_r03_a4,comparisons_r04_a3):
        result = module.solve(converted)
        if result is not None:
            return result
    return solve(converted)


def _category_partition(p):
    """One whole, disjoint labelled parts, and an explicitly named rest."""
    ns = p.numbers
    text = p.text.lower()
    if not 3 <= len(ns) <= 6 or any(n.start >= len(p.body) for n in ns):
        return None
    if _has(r'\b(?:each|every|per|more|less|than|half|twice|sold|gave|lost|used|percent)\b',text):
        return None
    rest = re.search(r'\b(?:rest|remaining [a-z]+) (?:are|is|were|was) ([a-z ]+?)[.!;]',p.body)
    units = [_unit(t) for t in _tails(p)]
    if rest and len(set(units)) == 1 and units[0] and _asked(p) == units[0]:
        label = rest.group(1).strip()
        if not _has(r'\b'+re.escape(label)+r'\b',p.question):
            # "the rest are green marbles" identifies the unknown modifier.
            words = label.split()
            if not words or not _has(r'\b'+re.escape(words[0])+r'\b',p.question):
                return None
        if not _has(r'\b(?:has|have|had|there are|there were)\b',text[:ns[0].start]):
            return None
        return _answer(ns[0].value-_sum(n.value for n in ns[1:]),
                       format_number(ns[0].value)+' - ('+_fmt(n.value for n in ns[1:])+')')
    # An explicit list declares the disjoint category universe, even where
    # the category words are unrelated to the whole's noun.
    first_tail = _tails(p)[0]
    listed = re.search(r'\bin total between ([^.]+)\.',first_tail)
    if not listed:
        return None
    categories = [x.strip() for x in re.split(r',\s*(?:and )?| and ',listed.group(1)) if x.strip()]
    if len(categories) != len(ns):
        return None
    seen = set()
    for n in ns[1:]:
        found = [c for c in categories if re.match(r'\s+'+re.escape(c)+r'\b',text[n.end:])]
        if len(found) != 1 or found[0] in seen:
            return None
        seen.add(found[0])
    missing = set(categories)-seen
    if len(missing) != 1 or not _has(r'\b'+re.escape(next(iter(missing)))+r'\b',p.question):
        return None
    return _answer(ns[0].value-_sum(n.value for n in ns[1:]),
                   format_number(ns[0].value)+' - ('+_fmt(n.value for n in ns[1:])+')')


def _grouped_stock(p):
    """Convert an explicit container ledger to contents, including removals."""
    ns = p.numbers
    text = p.text.lower()
    if not 3 <= len(ns) <= 6 or any(n.start >= len(p.body) for n in ns):
        return None
    if _has(r'\b(?:than|half|twice|percent|ratio|fewer|less|rest|another)\b',text):
        return None
    tails = _tails(p)
    units = [_unit(t) for t in tails]
    asked = _asked(p)
    if not asked:
        return None
    rates = []
    for i,n in enumerate(ns):
        if units[i] != asked:
            continue
        if not _matches_label(p,tails[i]):
            continue
        before = re.split(r'[.!?;]',text[:n.start])[-1]
        if not _has(r'\b(?:there are|there were|has|have|had|holds?|contains?)\b',before):
            continue
        local = re.split(r'[.!?;]',tails[i])[0]
        m = re.search(r'\b(?:inside|in|on|per) (?:a |an |each )?([a-z]+(?: [a-z]+){0,2})',local)
        if m:
            group = _unit(m.group(1))
            if group and group in units and group != asked:
                rates.append((i,group))
    if len(rates) != 1:
        return None
    ri,group = rates[0]
    group_terms = []
    output_terms = []
    for i,n in enumerate(ns):
        if i == ri:
            continue
        before = text[ns[i-1].end if i else 0:n.start]
        clause = re.split(r'[.!?;]|\b(?:and|but|then)\b',before)[-1]
        removed = _has(r'\b(?:lose|loses|lost|gave|gives?|used|uses?|ate|eats?|sold|sells?)\b',clause)
        if units[i] == group:
            if not removed and not _has(r'\b(?:has|have|had|bought|buys?|there are|there were)\b',clause):
                return None
            group_terms.append(n.value*(-1 if removed else 1))
        elif units[i] == asked:
            if not removed:
                return None
            output_terms.append(-n.value)
        else:
            return None
    if not group_terms or _sum(group_terms) < 0:
        return None
    answer = ns[ri].value*_sum(group_terms)+_sum(output_terms)
    return _answer(answer,'{} x ({}){}'.format(format_number(ns[ri].value),_fmt(group_terms),
                   ' + ('+_fmt(output_terms)+')' if output_terms else ''))


def _equal_group_capacity(p):
    """Several same-unit populations carried in equal-capacity containers."""
    ns = p.numbers
    text = p.text.lower()
    if not 3 <= len(ns) <= 5 or _has(r'\b(?:than|half|twice|percent|more|less|fewer)\b',text):
        return None
    if not _has(r'\b(?:need|requires?|necessary)\b',p.question):
        return None
    cap = ns[0]
    unit = _unit(text[cap.end:])
    before = text[:cap.start]
    after = text[cap.end:ns[1].start]
    group = re.search(r'\b(?:in|on) (?:a|an|each) ([a-z ]+?)[.!;]',after)
    if not group or _unit(group.group(1)) != _asked(p) or not _has(r'\b(?:fit|fits|hold|holds|carry|carries)\b',before):
        return None
    for i,n in enumerate(ns[1:],1):
        u = _unit(text[n.end:ns[i+1].start if i+1 < len(ns) else len(p.body)])
        if u != unit:
            # A later coordinated count may omit the repeated count noun.
            if u or i == 1 or not _has(r'\band\s*$',text[ns[i-1].end:n.start]):
                return None
    value = _sum(n.value for n in ns[1:])/cap.value
    answer = Fraction(-(-value.numerator//value.denominator))
    return _answer(answer,'Round up ('+_fmt(n.value for n in ns[1:])+') / '+format_number(cap.value))


def _completed_groups(p):
    """A stated whole minus already completed equal groups, with conversion."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or not _has(r'\bother (?:days|weeks|months|hours)\b',p.question):
        return None
    whole,rate,count = ns
    if not _has(r'\btotal\b',text[:whole.start]):
        return None
    if not re.search(r'\bon each of\s*$',text[rate.end:count.start]):
        return None
    from .counting_and_totals_r02_a4 import _convert
    asked = _asked(p)
    total = _convert(whole.value,_unit(text[whole.end:]),asked)
    per_group = _convert(rate.value,_unit(text[rate.end:]),asked)
    if total is None or per_group is None:
        return None
    return _answer(total-per_group*count.value,'{} - {} x {}'.format(*map(format_number,(total,per_group,count.value))))


def _one_exception(p):
    """One group's contribution is left after N identical contributions."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 4 or _has(r'\b(?:half|twice|percent|more|less|fewer|than)\b',text):
        return None
    population,total,count,rate = ns
    if population.value-count.value != 1:
        return None
    if not _has(r'\btotal\b',text[total.end:count.start]):
        return None
    if not re.match(r'\s+of (?:them|these|those)\b',text[count.end:]):
        return None
    if not re.match(r'\s+[a-z]+ each\b',text[rate.end:]):
        return None
    unit = _unit(text[total.end:])
    if not unit or _unit(text[rate.end:]) != unit or _asked(p) != unit:
        return None
    return _answer(total.value-count.value*rate.value,'{} - {} x {}'.format(*map(format_number,(total.value,count.value,rate.value))))


def _missing_servings(p):
    """A target measure, one existing ingredient and one adjustable serving."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 4 or not _has(r'\b(?:should|need|add)\b',p.question):
        return None
    goal,a,b,count = ns
    measure = _unit(text[goal.end:])
    if not measure or any(_unit(text[n.end:]) != measure for n in (a,b)):
        return None
    if not _has(r'\b(?:wants?|target|goal|needs?)\b',text[:goal.start]):
        return None
    groups = []
    for start,n in ((goal.end,a),(a.end,b)):
        m = re.search(r'\b(?:a|an|each) ([a-z ]+?) (?:has|contains|provides)\s*$',text[start:n.start])
        if not m:
            return None
        groups.append(_unit(m.group(1)))
    if not all(groups) or groups[0] == groups[1]:
        return None
    asked = _asked(p)
    known = _unit(text[count.end:])
    if known not in groups or asked not in groups or known == asked:
        return None
    values = [a.value,b.value]
    used = values[groups.index(known)]*count.value
    per = values[groups.index(asked)]
    return _answer((goal.value-used)/per,'({} - {}) / {}'.format(*map(format_number,(goal.value,used,per))))


def _per_group_days(p):
    """One item per person on scheduled days in each of several weeks."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or _has(r'\b(?:than|more|less|lost|sold|left|remaining|half|twice)\b',text):
        return None
    people,days,weeks = ns
    if _unit(text[days.end:]) != 'day' or _unit(text[weeks.end:]) != 'week':
        return None
    if not re.match(r'\s+days (?:a|per|each|every) week\b',text[days.end:]):
        return None
    middle = text[people.end:days.start]
    gift = re.search(r'\beach (?:gets?|receives?|needs?|uses?) (?:a|an) ([a-z ]+?)(?: in | for |,)',middle)
    if not gift or _unit(gift.group(1)) != _asked(p):
        return None
    if not _has(r'\b(?:entire|all|total)\b',p.question):
        return None
    return _answer(people.value*days.value*weeks.value,_fmt((people.value,days.value,weeks.value),' x '))


def _constant_speed_segments(p):
    """Distance at one speed over several driving intervals; breaks add none."""
    ns = p.numbers
    text = p.text.lower()
    if not 3 <= len(ns) <= 6 or not _has(r'\b(?:travel|drive|driven)\b',p.question):
        return None
    rate = ns[0]
    m = re.match(r'\s+(miles?|kilometers?) per (hour|minute)\b',text[rate.end:])
    if not m or _normal_unit(m.group(1)) != _asked(p):
        return None
    if _has(r'\b(?:faster|slower|twice|half|back|round|different)\b',text):
        return None
    from .rates_and_unit_rates_r01_a4 import _convert
    durations = []
    for i,n in enumerate(ns[1:],1):
        tail = text[n.end:ns[i+1].start if i+1 < len(ns) else len(p.body)]
        before = text[ns[i-1].end:n.start]
        if re.match(r'-?(?:minute|hour)s? break\b',tail):
            continue
        if not _has(r'\b(?:drives?|driving|travels?|traveling)\b',before):
            return None
        value = _convert(n.value,_unit(tail),m.group(2))
        if value is None:
            return None
        durations.append(value)
    if len(durations) < 2:
        return None
    return _answer(rate.value*_sum(durations),format_number(rate.value)+' x ('+_fmt(durations)+')')


def _weekly_rate_chain(p):
    """Scheduled days/week, hours/day and distance/hour, queried per week."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or not _has(r'\b(?:a|per|each|one|the) week\b',p.question):
        return None
    if _has(r'\b(?:than|more|less|half|twice|left|remaining|except)\b',text):
        return None
    units = [_unit(t) for t in _tails(p)]
    if sorted(units[:2]) != ['day','hour']:
        return None
    di = units.index('day');hi = units.index('hour')
    if not re.match(r'\s+days (?:a|per|each) week\b',text[ns[di].end:]):
        return None
    if not re.match(r'\s+hours (?:a|per|each|every) day\b',text[ns[hi].end:]):
        return None
    tail = text[ns[2].end:]
    out = re.match(r'\s+(miles?|kilometers?) per hour\b',tail)
    if out:
        measure = _normal_unit(out.group(1))
    elif re.match(r'\s+mph\b',tail):
        measure = 'mile'
    else:
        return None
    if _asked(p) != measure:
        return None
    return _answer(ns[0].value*ns[1].value*ns[2].value,_fmt((n.value for n in ns),' x '))


def _reward_groups(p):
    """One reward for every N completed items, at a stated weekly rate."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or _has(r'\b(?:than|more|less|half|twice|left|remaining)\b',text):
        return None
    cost,rate,duration = ns
    if not re.search(r'\bfor every\s*$',text[:cost.start]):
        return None
    unit = _unit(text[cost.end:])
    if not unit or _unit(text[rate.end:]) != unit or _unit(text[duration.end:]) != 'week':
        return None
    if not re.match(r'\s+[a-z]+ (?:a|per|each) week\b',text[rate.end:]):
        return None
    reward = re.search(r'\b(?:a|an) (?:free )?([a-z]+) (?:at|for|from)\b',text[cost.end:rate.start])
    if not reward or _normal_unit(reward.group(1)) != _asked(p):
        return None
    value = rate.value*duration.value/cost.value
    return _answer(Fraction(value.numerator//value.denominator),
                   '{} x {} / {}'.format(*map(format_number,(rate.value,duration.value,cost.value))))


def _monthly_stock(p):
    """Regular monthly acquisitions minus the explicitly unconsumed stock."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or _has(r'\b(?:than|more|less|half|twice|each|per)\b',text):
        return None
    rate,months,remaining = ns
    # A present-tense recurring acquisition can recur at the month boundary;
    # a one-time past acquisition cannot be multiplied by elapsed months.
    if not re.search(r'\b(?:gets?|receives?|buys?)\s*$',text[:rate.start]):
        return None
    unit = _unit(text[rate.end:])
    if not unit or _unit(text[remaining.end:]) != unit or _asked(p) != unit:
        return None
    if not re.search(r'\bat the beginning of (?:the|each|every) month\b',text[rate.end:months.start]):
        return None
    if not re.match(r'\s+months\b',text[months.end:]) or not _has(r'\bafter\s*$',text[:months.start]):
        return None
    if not _has(r'\b(?:available|left|remaining)\b',text[remaining.end:len(p.body)]) or not _has(r'\brest\b',p.body):
        return None
    return _answer(rate.value*months.value-remaining.value,
                   '{} x {} - {}'.format(*map(format_number,(rate.value,months.value,remaining.value))))


def _known_and_related(p):
    """Two known named stocks and one explicitly compared stock, summed."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or not _has(r'\b(?:total|altogether|combined|in all)\b',p.question):
        return None
    if _has(r'\b(?:each|every|per|half|twice|times|left|remaining|percent)\b',text):
        return None
    token = _token(p)
    relation = re.search(r'\b([a-z]+) (?:has|had|collected|made|won|scored) Q(\d+) (more|fewer|less) ([a-z]+) than ([a-z]+)\b',token)
    if not relation:
        return None
    owner,ri,direction,noun,reference = relation.groups()
    ri = int(ri)
    known = {}
    for match in re.finditer(r'\b([a-z]+) (?:has|had|collected|made|won|scored) Q(\d+)',token):
        name,index = match.group(1),int(match.group(2))
        if index == ri:
            continue
        if name in known or _unit(text[ns[index].end:]) not in ('',_normal_unit(noun)):
            return None
        known[name] = (index,ns[index].value)
    if len(known) != 2 or reference not in known or owner in known:
        return None
    if {index for index,value in known.values()} | {ri} != set(range(3)):
        return None
    if _asked(p) != _normal_unit(noun):
        return None
    mentioned = [name for name in set(known)|{owner} if _has(r'\b'+re.escape(name)+r'\b',p.question)]
    if mentioned and len(mentioned) != 3:
        return None
    other = known[reference][1]+ns[ri].value*(-1 if direction in ('less','fewer') else 1)
    if other < 0:
        return None
    values = [value for index,value in known.values()]+[other]
    return _answer(_sum(values),_fmt(values))


def _elliptical_comparison_total(p):
    """Same-unit known amount and explicit difference with omitted reference."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 2 or _has(r'\b(?:times|each|every|per|half|twice|than|percent|left|remaining)\b',text):
        return None
    if not (_has(r'\b(?:total|combined|together|altogether|in all)\b',p.question)
            or _has(r'\bthey (?:donate|have|collected|collect|give)\b',p.question)):
        return None
    first,difference = ns
    unit = _unit(text[first.end:])
    requested = _asked(p)
    if requested and requested not in (unit,'time'):
        return None
    m = re.match(r'\s+(?:(more|less|fewer) ([a-z]+)|([a-z]+) (more|less|fewer))\b',text[difference.end:])
    if not m:
        return None
    direction,noun = (m.group(1),m.group(2)) if m.group(1) else (m.group(4),m.group(3))
    if _normal_unit(noun) != unit:
        return None
    # The difference describes another owner (including a stated partner),
    # never an increase to the same owner's inventory.
    between = text[first.end:difference.start]
    if not _has(r'[.!?;]',between):
        return None
    from .comparisons_r01_a2 import _names
    start_owners = _names(p.text[:first.start])
    second_owners = _names(p.text[first.end:difference.start])
    partner = _has(r'\b(?:partner|friend|sister|brother|colleague)\b',between)
    if not partner and (not start_owners or not second_owners or start_owners[-1]==second_owners[-1]):
        return None
    sign = -1 if direction in ('less','fewer') else 1
    if first.value+sign*difference.value < 0:
        return None
    return _answer(2*first.value+sign*difference.value,
                   '2 x {} {} {}'.format(format_number(first.value),'+' if sign > 0 else '-',format_number(difference.value)))

def solve(problem):
    if any(n.kind != 'number' or n.value <= 0 for n in problem.numbers):
        return None
    for rule in (_recipe, _nested_groups, _ledger, _category_difference,
                 _goal_partition, _group_shortfall, _capacity_remainder,
                 _multiple_of_time, _continued_periods, _stock_minus_groups,
                 _spent_groups, _refill, _resource_budget, _mass_capacity,
                 _mixture_scale, _weekday_normalization, _task_remainder,
                 _same_contents_additional, _dozen_difference, _fronted_daily_sum,
                 _sided_groups, _uniform_leftover, _grammatical_numbers,
                 _category_partition, _grouped_stock, _equal_group_capacity,
                 _completed_groups, _one_exception, _missing_servings,
                 _per_group_days, _constant_speed_segments, _weekly_rate_chain,
                 _reward_groups, _monthly_stock, _known_and_related,
                 _elliptical_comparison_total):
        result = rule(problem)
        if result is not None:
            return result
    return None
