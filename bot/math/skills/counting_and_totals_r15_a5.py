"""Compose explicit counting relations, with complete quantity accounting.

These readers use labels supplied by the narrative.  Calendar dates are only
ignored when explicitly marked as dates; rates, stock and reference counts
have separate roles.  An incomplete or ambiguous relation is left unsolved.
"""
import re
from fractions import Fraction

from ..numbers import format_number
from ._counting_common import answer, total, fmt, tokenize as _tokenize
from ._money_common import _singular
from .counting_and_totals_r13_a4 import label as _label, compatible, converted as _converted, asked as _asked


_DAYS = 'monday tuesday wednesday thursday friday saturday sunday'.split()
_TIME = {'second', 'minute', 'hour', 'day', 'week', 'month', 'year'}


def label(text):
    text=re.split(r'\b(?:remain|remains|swimming|floated|worth|because|where|out|away|must|should)\b',text)[0]
    return _label(text)


def asked(p):
    m=re.match(r'how (?:many|much)\s+(?:(?:more|additional|extra|total|combined|remaining)\s+)*(.*)',p.question)
    return label(m.group(1)) if m else _asked(p)


def has(pattern, text):
    return re.search(pattern, text) is not None


def tails(p):
    t = p.text.lower()
    return [t[n.end:p.numbers[i+1].start if i+1 < len(p.numbers) else len(t)]
            for i, n in enumerate(p.numbers)]


def tokenize(p):
    # A measurement may attach its abbreviation directly to its number.
    return re.sub(r'(Q\d+)(?=[a-z])', r'\1 ', _tokenize(p))


def converted(value, source, dest):
    imperial={'inch':Fraction(1),'foot':Fraction(12),'yard':Fraction(36),'mile':Fraction(63360)}
    if source in imperial and dest in imperial:
        return value*imperial[source]/imperial[dest]
    return _converted(value,source,dest)


def category_match(source, target):
    # Closed noun compounds retain their head (e.g. book / notebook).
    return compatible(source,target) or bool(source and target and len(target)>=4 and source.split()[-1].endswith(target))


def _periodic_stock(p):
    """An initial stock plus a stated gain and loss in every period."""
    if len(p.numbers) != 4:
        return None
    t = tokenize(p)
    m = re.search(r'\b(?:has|had|starts with) Q0 ([a-z -]+?)[.;]', t)
    period = re.search(r'\bevery (day|week|month|year)\b', t)
    if not m or not period or not compatible(label(m.group(1)), asked(p)):
        return None
    u = period.group(1)
    if not has(r'\b(?:buy|buys|gets?|receives?|adds?)\b[^.;]*Q1\b', t):
        return None
    if not has(r'Q2 (?:of (?:them|these) )?(?:dies|die|breaks?|is lost|are lost|is removed|are removed)\b', t):
        return None
    if not has(r'\bin Q3 '+u+r's?\?', t):
        return None
    a,b,c,d = p.values
    if b < c:
        return None
    return answer(a+(b-c)*d, '{} + ({} - {}) x {}'.format(*map(format_number,(a,b,c,d))))


def _dated_ledger(p):
    """An inventory with explicitly dated openings and closures."""
    if not has(r'\b(?:at the end|now|left|remaining)\b', p.question):
        return None
    t = p.text.lower()
    if has(r'\b(?:each|every|per|times|twice|half|more than|fewer than)\b', p.body):
        return None
    dates, active = set(), []
    for i,n in enumerate(p.numbers):
        if n.value.denominator == 1 and has(r'\b(?:in|of|during)\s*$', t[:n.start]) and len(n.raw) == 4 and has(r'^\s*[,.;?!]',t[n.end:]):
            dates.add(i)
        else:
            active.append(i)
    if not dates or not 3 <= len(active) <= 9:
        return None
    if any(p.numbers[i].start >= len(p.body) for i in active):
        return None
    unit = asked(p)
    if not unit:
        return None
    result, work = Fraction(0), []
    for pos,i in enumerate(active):
        n=p.numbers[i]
        start = p.numbers[active[pos-1]].end if pos else 0
        before = re.split(r'[.!?;](?:\s|$)|\b(?:but|and)\b', t[start:n.start])[-1]
        after = t[n.end:p.numbers[i+1].start if i+1<len(p.numbers) else len(p.body)]
        item = label(re.sub(r'^\s*(?:new|the)\s+', '', after))
        if pos == 0:
            if not has(r'\b(?:has|had|owns?|owned)\s*$', before) or not compatible(item,unit):
                return None
            sign=1
        else:
            m=re.search(r'\b(opened|opens?|added|closed|closes?|closing|removed)\s+(?:the\s+)?$',before)
            if not m:
                return None
            sign=-1 if m.group(1).startswith(('clos','remov')) else 1
            if not compatible(item,unit) and not (sign<0 and has(r'^\s+(?:that|worst|least)\b',after)):
                return None
        result += sign*n.value
        work.append((' - ' if sign<0 else ' + ')+format_number(n.value))
    return answer(result,''.join(work).lstrip(' +'))


def _rectangular_groups(p):
    """Sum areas of counted rectangular groups, all in one length unit."""
    if not has(r'\bsquare\b',p.question) or not has(r'\b(?:combined|total|all|altogether)\b',p.question):
        return None
    t=tokenize(p)
    pat=(r'Q(\d+) ([a-z -]+?) (?:that )?each (?:measure|measures|measuring|are) '
         r'Q(\d+) (feet|meters?|yards?|inches|centimeters?) by Q(\d+) \4')
    used=set();terms=[]
    for m in re.finditer(pat,t):
        a,b,c=int(m.group(1)),int(m.group(3)),int(m.group(5))
        if used & {a,b,c} or not has(r'\bsquare '+re.escape(m.group(4))+r'\b',p.question):
            return None
        used.update((a,b,c));terms.append(p.numbers[a].value*p.numbers[b].value*p.numbers[c].value)
    if len(terms)<2 or used != set(range(len(p.numbers))):
        return None
    return answer(total(terms),fmt(terms))


def _unused_area(p):
    """Bought coverage less the area of an explicitly dimensioned rectangle."""
    if len(p.numbers) not in (4,5) or not has(r'\b(?:extra|leftover|remaining)\b',p.question):
        return None
    t=tokenize(p)
    cover=re.search(r'\b(?:a|an|one|Q(\d+)) ([a-z -]+?) covers Q(\d+) square (feet|meters?|yards?)\b',t)
    if not cover:
        return None
    ref,container,rate,u=cover.groups();rate=int(rate)
    used={rate}
    if ref is not None:
        ref=int(ref)
        if p.numbers[ref].value != 1:return None
        used.add(ref)
    dims=re.search(r'Q(\d+) '+u+r' [^Q.!?]*\band Q(\d+) '+u+r'\b',t)
    count=re.search(r'\b(?:bought|buys|purchased) Q(\d+) ([a-z -]+?)(?=[.;]|$)',t)
    if not dims or not count or not compatible(label(count.group(2)),label(container)):
        return None
    a,b=int(dims.group(1)),int(dims.group(2));c=int(count.group(1))
    if used & {a,b,c} or used | {a,b,c} != set(range(len(p.numbers))):return None
    if not has(r'\bsquare '+u+r'\b',p.question):return None
    r,x,y,n=(p.numbers[i].value for i in (rate,a,b,c))
    return answer(r*n-x*y,'{} x {} - {} x {}'.format(*map(format_number,(r,n,x,y))))


def _category_exclusions(p):
    """A list of stocks followed by a matching list with one defect property."""
    if not has(r'\bwithout\b',p.question) or len(p.numbers)<4 or len(p.numbers)%2:
        return None
    ts=tails(p);k=len(ts)//2;t=p.text.lower()
    stocks=[label(x) for x in ts[:k]]
    if not all(stocks) or len(set(stocks)) != k:return None
    if not has(r'\b(?:has|had|owns?|there are)\s*$',t[:p.numbers[0].start]):return None
    if any(not compatible(label(ts[i+k]),stocks[i]) for i in range(k)):return None
    # The exclusion property must be stated on the second list and repeated
    # in the question.  Quantities may not introduce further actions.
    prop=re.search(r'\b(?:have|has) (?:a |an )?(.+?)(?: in them)?[.]\s*how',ts[-1])
    query=re.search(r'\bwithout (.+?)(?: in them)?\?',p.question)
    if not prop or not query:return None
    def property_words(s):
        return {_singular(w) for w in re.findall(r'[a-z]+',s) if w not in ('a','an','the','in','them')}
    if property_words(prop.group(1)) != property_words(query.group(1)):return None
    target=asked(p)
    if not target or any(not category_match(s,target) for s in stocks):return None
    if any(p.numbers[i+k].value>p.numbers[i].value for i in range(k)):return None
    return answer(total(p.values[:k])-total(p.values[k:]),'({}) - ({})'.format(fmt(p.values[:k]),fmt(p.values[k:])))


def _unit_exchange(p):
    """Explicit exchange definitions joined to inventories by category name."""
    t=tokenize(p);recipes={};used=set()
    pat=r'\b(?:a|an) ([a-z -]+?) has the same value as Q(\d+) ([a-z -]+?)(?= and (?:a|an) |[.;])'
    target=asked(p)
    for m in re.finditer(pat,t):
        key,i,out=label(m.group(1)),int(m.group(2)),label(m.group(3))
        if not key or key in recipes or not compatible(out,target):return None
        recipes[key]=p.numbers[i].value;used.add(i)
    if not recipes or not has(r'\b(?:exchanging|exchange|converting|convert)\b',p.question):return None
    terms=[];seen=set()
    for i,n in enumerate(p.numbers):
        if i in used:continue
        key=label(tails(p)[i]);keys=[k for k in recipes if compatible(key,k)]
        if len(keys)!=1:return None
        seen.add(keys[0]);terms.append(n.value*recipes[keys[0]])
    if seen != set(recipes):return None
    return answer(total(terms),fmt(terms))


def _reverse_shared_stock(p):
    """Undo one recipient's loss, then multiply by all equal recipients."""
    if len(p.numbers)!=3 or not has(r'\b(?:start with|originally|at first)\b',p.question):return None
    t=tokenize(p)
    m=re.search(r'\b(?:split|shared|divided) (?:them|it|[a-z ]+?) (?:among|between) ([a-z]+) and Q0 (?:of (?:his|her|their) )?[a-z -]+?[.;]',t)
    if not m:return None
    person=m.group(1)
    if not has(r'\b'+person+r' (?:decided to )?(?:give|gave) Q1\b',t):return None
    if not has(r'\b(?:he|she|'+person+r') now has Q2\b',t):return None
    a,b,c=p.values
    return answer((a+1)*(b+c),'({} + 1) x ({} + {})'.format(*map(format_number,(a,b,c))))


def _daily_makeup(p):
    """A repeated daily goal with arrears explicitly carried to the next day."""
    if len(p.numbers)<3 or len(p.numbers)>8:return None
    if not has(r'\bmake up\b',p.question) or not has(r'\bgoal\b',p.body):return None
    if any(n.start>=len(p.body) for n in p.numbers):return None
    t=p.text.lower();ts=tails(p)
    if not has(r'\bgoal is\s*$',t[:p.numbers[0].start]):return None
    unit=label(ts[0])
    if not unit or not compatible(unit,asked(p)) or any(not compatible(label(x),unit) for x in ts[1:]):return None
    days=[]
    for i,n in enumerate(p.numbers[1:],1):
        clause=t[p.numbers[i-1].end:n.start]
        ds=[d for d in _DAYS if has(r'\bon '+d+r'\b',clause)]
        if len(ds)!=1:return None
        days.append(_DAYS.index(ds[0]))
    qdays=[_DAYS.index(d) for d in _DAYS if has(r'\bon '+d+r'\b',p.question)]
    if len(qdays)!=1 or any((a+1)%7!=b for a,b in zip(days,days[1:]+qdays)):return None
    goal=p.values[0]*len(p.numbers)
    return answer(goal-total(p.values[1:]),'{} x {} - ({})'.format(format_number(p.values[0]),len(p.numbers),fmt(p.values[1:])))


def _weekly_record(p):
    """Complete a week above a previous integer record, with a skipped day."""
    if not has(r'\b(?:beat|beats|exceed)\b',p.question) or not has(r'\blast week\b',p.body):return None
    if not 3<=len(p.numbers)<=8 or any(n.start>=len(p.body) for n in p.numbers):return None
    qdays=[d for d in _DAYS if has(r'\bon '+d+r'\b',p.question)]
    if len(qdays)!=1:return None
    if not all(has(r'\bon '+d+r'\b',p.body) for d in _DAYS if d!=qdays[0]):return None
    if not has(r'\blast week\b',p.body[:p.numbers[0].start]):return None
    ts=tails(p);unit=label(re.sub(r'^\s*total\s+','',ts[0]))
    for i in range(1,len(p.numbers)):
        before=p.body[p.numbers[i-1].end:p.numbers[i].start]
        if not has(r'\bon (?:'+'|'.join(_DAYS)+r') he did\s*$',before):return None
        if label(ts[i]) and not compatible(label(ts[i]),unit):return None
    if any(n.value.denominator!=1 for n in p.numbers):return None
    return answer(p.values[0]+1-total(p.values[1:]),'{} + 1 - ({})'.format(format_number(p.values[0]),fmt(p.values[1:])))


def _maximum_consumption(p):
    """A multiple of one portion is the daily cap, including earlier use."""
    if len(p.numbers)!=3:return None
    t=tokenize(p);ts=tails(p)
    if not has(r'\bmaximum of Q1 times that amount\b',t):return None
    if not has(r'\balready had Q2\b',t) or not has(r'\bafter (?:eating|consuming|using) all\b',p.question):return None
    unit=label(ts[0]);other=label(ts[2]);target=asked(p)
    if unit.startswith('oz '):unit='ounce'
    if other.startswith('oz '):other='ounce'
    if target.startswith('oz '):target='ounce'
    if not compatible(unit,other) or not compatible(unit,target):return None
    a,b,c=p.values
    return answer(a*b-a-c,'{} x {} - {} - {}'.format(*map(format_number,(a,b,a,c))))


def _measurement_difference(p):
    """One labelled distance compared with several others combined."""
    if not has(r'\b(?:farther|more|longer)\b.*\bthan\b.*\bcombined\b',p.question):return None
    if not 3<=len(p.numbers)<=6 or any(n.start>=len(p.body) for n in p.numbers):return None
    ts=tails(p);target=asked(p)
    quantities=[];days=[]
    for n,tail in zip(p.numbers,ts):
        m=re.match(r'\s+(kilometers?|meters?|centimeters?|miles?|feet|yards?|inches) on ([a-z]+)',tail)
        if not m:return None
        v=converted(n.value,label(m.group(1)),target)
        if v is None:return None
        quantities.append(v);days.append(m.group(2))
    if not has(r'\bon '+re.escape(days[0])+r' than\b',p.question):return None
    if not all(has(r'\b'+re.escape(day)+r'\b',p.question) for day in days[1:]):return None
    return answer(quantities[0]-total(quantities[1:]),'{} - ({})'.format(format_number(quantities[0]),fmt(quantities[1:])))


def _recipe_totals(p):
    """Join reversible, explicitly stated material/task ratios by noun label."""
    if not 3<=len(p.numbers)<=14:return None
    if has(r'\b(?:in|per|a|each|every) (?:day|week|month|year)\b',p.question):return None
    if has(r'\b(?:more|less|fewer|than|half|twice|left|remaining|lost|sold|average|except|rest|some)\b',p.text.lower()):return None
    t=tokenize(p);used=set();recipes={}
    target=asked(p)
    if not target:return None
    material_units={label(m.group(1)) for m in re.finditer(
        r'Q\d+ (yards?|feet|meters?|liters?|ounces?|pounds?) of '+re.escape(target)+r'\b',t)}
    if len(material_units)==1:
        # Equal physical units do not make different materials interchangeable.
        for material in re.finditer(
                r'Q\d+ (?:yards?|feet|meters?|liters?|ounces?|pounds?) of ([a-z -]+)',t):
            if not compatible(label(material.group(1)),target):return None
        target=next(iter(material_units))
    def add(key,out,value,ids):
        if not key or not out or key==out or key in recipes or used & set(ids):return False
        recipes[key]=(out,value);used.update(ids);return True
    # "Birds take N minutes to groom" is a per-bird task duration;
    # plural subjects describe categories rather than named owners.
    pat=r'(?:^|[.;,]\s*|\band\s+)(?:and )?([a-z -]+?) take Q(\d+) (seconds?|minutes?|hours?) to [a-z]+\b'
    for m in re.finditer(pat,t):
        raw,i,out=m.groups();i=int(i)
        if not raw.strip().endswith('s'):return None
        if not add(label(raw),label(out),p.numbers[i].value,[i]):return None
    # A measured amount needed to make one item.
    pat=r'\b(?:needs?|uses?|requires?) Q(\d+) ([a-z -]+?) to (?:make|build|produce) (?:a|an) ([a-z -]+?)(?=[.;,]|$)'
    for m in re.finditer(pat,t):
        i,out,key=int(m.group(1)),label(m.group(2)),label(m.group(3))
        if not add(key,out,p.numbers[i].value,[i]):return None
    # A batch makes N products from an explicit amount of material.
    pat=r'\b(?:make|makes|produce|produces) Q(\d+) ([a-z -]+?) (?:out of|from|with) Q(\d+) ([a-z -]+?)(?=[.;,]|$)'
    for m in re.finditer(pat,t):
        i,key,j,out=int(m.group(1)),label(m.group(2)),int(m.group(3)),label(m.group(4))
        if p.numbers[i].value<=0 or not add(key,out,p.numbers[j].value/p.numbers[i].value,[i,j]):return None
    # A container with an explicit contents per item.
    pat=r'\b(?:each|every|a|an) ([a-z -]+?) (?:has|have|contains?|holds?|needs?|requires?|uses?) Q(\d+) ([a-z -]+?)(?=[.;,]|$)'
    for m in re.finditer(pat,t):
        key,i,out=label(m.group(1)),int(m.group(2)),label(m.group(3))
        if i in used:continue
        if not add(key,out,p.numbers[i].value,[i]):return None
    if not recipes:return None
    visited=set()
    def expand(key,trail):
        factor=converted(Fraction(1),key,target)
        if factor is not None:return factor
        matches=[k for k in recipes if compatible(k,key)]
        if len(matches)!=1 or matches[0] in trail:raise ValueError('ambiguous recipe')
        k=matches[0];visited.add(k);out,rate=recipes[k]
        return rate*expand(out,trail|{k})
    terms=[]
    ts=tails(p)
    for i,n in enumerate(p.numbers):
        if i in used:continue
        if n.start>=len(p.body) and not has(r'\b(?:to|for)\b',p.question[:n.start-len(p.body)]):return None
        key=label(ts[i])
        if converted(Fraction(1),key,target) is not None:return None
        try:terms.append(n.value*expand(key,set()))
        except ValueError:return None
    if not terms or visited!=set(recipes):return None
    return answer(total(terms),fmt(terms))


def _capacity_remainder(p):
    """Total material less selected sized containers, divided by a final size.

    Optional catalogue entries such as "small and large containers" are
    references; each catalogue size must match an actual selected size.
    """
    if not has(r'\b(?:fill|buy|need)\b',p.question):return None
    t=tokenize(p);ts=tails(p);used=set();catalogue=[];demands=[]
    # Explicit hyphenated or spaced measurement modifiers: N-unit containers.
    pat=r'Q(\d+)[ -]+(ounces?|inch(?:es)?|liters?|milliliters?|feet|meters?|yards?)[ -]+([a-z]+)'
    mods=list(re.finditer(pat,t))
    if not mods:return None
    sizes={}
    for m in mods:
        i=int(m.group(1));measure=label(m.group(2));container=label(m.group(3))
        if container:sizes[i]=(p.numbers[i].value,measure,container)
    # A catalogue can omit the repeated measure and noun: "N and M inch ...".
    for i in range(len(p.numbers)-1):
        if i not in sizes and i+1 in sizes and re.fullmatch(r'\s+and\s+',ts[i]):
            sizes[i]=(p.numbers[i].value,)+sizes[i+1][1:]
    finals=[i for i in sizes if p.numbers[i].start>=len(p.body)]
    if len(finals)!=1:return None
    fi=finals[0];size,measure,container=sizes[fi];used.add(fi)
    if size<=0:return None
    totals=[]
    for i,n in enumerate(p.numbers):
        if i in used or i in sizes:continue
        # A count immediately followed by a measurement modifier.
        if i+1 in sizes and re.fullmatch(r'\s*',ts[i]):
            rate,u,item=sizes[i+1]
            if u!=measure or item!=container:return None
            demands.append(n.value*rate);used.update((i,i+1));continue
        unit=label(ts[i])
        if compatible(unit,measure):
            before=t.split('Q'+str(i),1)[0]
            if not has(r'\b(?:has|have|needs?|requires?|total of)\s*$',before):return None
            totals.append(n.value);used.add(i)
        else:return None
    if len(totals)!=1 or not demands:return None
    for i,(v,u,c) in sizes.items():
        if i in used:continue
        if u!=measure or c!=container:return None
        # Unused sizes must be explicitly in a catalogue, before the actions.
        before=t.split('Q'+str(i),1)[0]
        if not has(r'\b(?:has|sells?|offers?)\b[^.!?]*$',before):return None
        if v!=size and not any(v==sizes[j][0] for j in sizes if j in used and j!=fi):return None
        used.add(i);catalogue.append(i)
    if used!=set(range(len(p.numbers))):return None
    remainder=totals[0]-total(demands)
    if remainder<0 or (remainder/size).denominator!=1:return None
    return answer(remainder/size,'({} - ({})) / {}'.format(format_number(totals[0]),fmt(demands),format_number(size)))


def _collected_comparison(p):
    """A shared initial collection, one person's list, and a relative addition."""
    t=tokenize(p)
    if not has(r'\b(?:altogether|combined|in total)\b',p.question):return None
    if not 4<=len(p.numbers)<=10:return None
    initial=re.search(r'\b([a-z]+) and ([a-z]+) (?:already )?had Q0 ([a-z -]+?)(?=[.;])',t)
    if not initial:return None
    first,second=initial.group(1),initial.group(2);unit=label(initial.group(3))
    a=re.search(r'\b'+first+r' found (Q\d+[^.!?]+)[.]',t)
    b=re.search(r'\b'+second+r' found Q(\d+) more ([a-z -]+?) than '+first+r' did[.]',t)
    if not a or not b or not compatible(label(b.group(2)),unit):return None
    used={0,int(b.group(1))};terms=[]
    for m in re.finditer(r'Q(\d+) ([^Q]+)',a.group(1)):
        i=int(m.group(1))
        if i in used or not compatible(label(m.group(2)),unit):return None
        used.add(i);terms.append(p.numbers[i].value)
    if not terms or used!=set(range(len(p.numbers))) or not compatible(unit,asked(p)):return None
    shared=p.values[0];difference=p.numbers[int(b.group(1))].value;s=total(terms)
    return answer(shared+s+s+difference,'{} + ({}) + (({}) + {})'.format(format_number(shared),fmt(terms),fmt(terms),format_number(difference)))


def _defective_sales(p):
    """All usable stock is exhausted; find one unknown sale after defects."""
    if not has(r'\ball non-[a-z]+ [a-z]+ were sold\b',p.body):return None
    if not has(r'\b(?:how many|how much)\b.*\bsold\b',p.question):return None
    if not 4<=len(p.numbers)<=8 or any(n.start>=len(p.body) for n in p.numbers):return None
    t=tokenize(p);ts=tails(p);unit=asked(p)
    if not has(r'\b(?:contains?|has|had) Q0\b',t):return None
    if not compatible(label(ts[0]),unit):return None
    if not has(r'^\s+[a-z]+ (?:units|items|pieces)\b',ts[1]) and not has(r'^\s+defective\b',ts[1]):return None
    if not has(r'\bgot rid of\b',p.body):return None
    for i in range(2,len(p.numbers)):
        before=t.split('Q'+str(i),1)[0]
        if not has(r'\bbought\s*$',before) or not compatible(label(ts[i]),unit):return None
    return answer(p.values[0]-total(p.values[1:]),'{} - ({})'.format(format_number(p.values[0]),fmt(p.values[1:])))


def count_label(t):
    t=re.sub(r'^\s*(?:(?:more|extra|additional|baby|colored)\s+)+',' ',t)
    t=re.split(r'\b(?:swimming|floated|worth|because|away)\b',t)[0]
    t=re.sub(r'^\s*(?:pieces?|dozens?) of\s+',' ',t)
    return label(t)


def requested(p):
    m=re.match(r'how (?:many|much)\s+(?:(?:more|extra|total|remaining)\s+)*(.*)',p.question)
    return count_label(m.group(1)) if m else asked(p)


def _inventory(p):
    """Explicit acquisitions, departures and final stock; optional pack sizes."""
    ns=p.numbers;t=p.text.lower();ts=tails(p);target=requested(p)
    if not target or target in _TIME or not 3<=len(ns)<=12:return None
    if any(n.start>=len(p.body) for n in ns):return None
    if has(r'\b(?:times|twice|thrice|half|percent|average|than|ratio|per|some of|rest of)\b',p.body):return None
    reverse=has(r'\b(?:in the morning|beginning|start with|originally)\b',p.question)
    consumed=has(r'\b(?:eaten|used|sold|gave away|given away)\b',p.question)
    if not (reverse or consumed or has(r'\b(?:left|unused|remaining|now|have|has|catch in all)\b',p.question)):return None
    groups={};used=set();metadata=set()
    # Dates/durations without a per-time relation do not change stock.
    for i,n in enumerate(ns):
        before=t[:n.start];after=ts[i]
        if label(after) in _TIME and (has(r'\b(?:next|after|over the next|in the next)\s*$',before)
                                    or has(r'^\s+(?:days?|weeks?|hours?|minutes?) (?:after|later)\b',after)):
            metadata.add(i)
    for i,n in enumerate(ns):
        before=t[:n.start]
        m=re.search(r'\beach ([a-z -]+?) (?:has|holds?|contains?)\s*$',before)
        if not m:continue
        key=count_label(m.group(1));candidates=[j for j in range(i) if count_label(ts[j])==key]
        if len(candidates)!=1:return None
        j=candidates[0]
        if not compatible(count_label(ts[i]),target):return None
        groups[j]=(i,n.value);used.add(i)
    for i in range(1,len(ns)):
        if i in used or i-1 in used:continue
        middle=t[ns[i-1].end:ns[i].start]
        after=ts[i]
        if (has(r'\b(?:laid|produced|made|brought|collected)\s*$',middle)
                and has(r'\beach(?=[.;,]|$)',after)
                and compatible(count_label(after),target)):
            groups[i-1]=(i,ns[i].value);used.add(i)
    signed=[];remaining=[];previous=None;owner=None;has_special=bool(groups)
    for i,n in enumerate(ns):
        if i in used or i in metadata:continue
        before=t[ns[i-1].end if i else 0:n.start]
        clause=re.split(r'[.!?;](?:\s|$)|\b(?:and|but)\b',before)[-1]
        after=ts[i];unit=count_label(after);v=n.value
        if i in groups:
            j,rate=groups[i];unit=count_label(ts[j]);v*=rate
        dozen=re.match(r'\s+dozens?\s+(?:of\s+)?(.*)',after)
        if dozen:
            unit=count_label(dozen.group(1));v*=12;has_special=True
        if not compatible(unit,target):
            # An explicit elided noun after "using up N" or "N more".
            if not (has(r'\b(?:using up|threw)\s*$',clause) or has(r'^\s+(?:more\b|back\b|of them\b|from (?:her|his|their)\b)',after)):
                return None
        if has(r'^\s+(?:[a-z -]+ )?(?:(?:are|were) )?left(?: over)?\b',after) or has(r'^\s+[a-z -]+ left(?: over)?\b',after):
            remaining.append(v);previous=None;continue
        remove=has(r'\b(?:drank|drinks?|ate|eats?|used|uses?|using up|lost|loses?|'
                   r'tore off|gave|gives?|sold|sells?|threw|removed|removes?|passing)\b',clause)
        remove=remove or has(r'\b(?:floated away|were used|was used|were eaten|were sold)\b',after)
        add=has(r'\b(?:has|had|have|bought|buys?|caught|catches|collected|received|gets?|'
                r'grabbed(?: the last)?|sees?|saw|refills?|filled|started with|brought home|brought)\b',clause)
        if i in groups:
            j,_=groups[i]
            group_before=t[ns[j-1].end:ns[j].start]
            add=add or has(r'\b(?:laid|produced|made|brought|collected)\s*$',group_before)
        if remove:sign=-1
        elif add:sign=1
        elif previous is not None and (has(r'^\s*[a-z -]*\band\s*$',before) or has(r'\bin addition to (?:her|his|their|the)\s*$',before)) and not has(r'[.;]',before):sign=previous
        else:return None
        if not signed and not reverse:
            if sign!=1:return None
            # Capture the first stock's owner to reject a second independent
            # inventory unless the question explicitly asks a joint total.
            m=re.search(r'\b([a-z]+) (?:has|had|bought|buys?|caught|started with)\s*$',clause)
            owner=m.group(1) if m and m.group(1) not in ('he','she','they') else None
        elif owner and not has(r'\b(?:they|their|in all|together|total|altogether)\b',p.question):
            m=re.search(r'\b([a-z]+) (?:has|had|bought|buys?|caught|collected|received)\s*$',clause)
            if m and m.group(1) not in (owner,'he','she','they','family'):return None
        signed.append(sign*v);previous=sign
    if reverse:
        if len(remaining)!=1:return None
        return answer(remaining[0]-total(signed),'{} - ({})'.format(format_number(remaining[0]),fmt(signed)))
    if consumed:
        if len(remaining)!=1 or any(x<0 for x in signed):return None
        return answer(total(signed)-remaining[0],'({}) - {}'.format(fmt(signed),format_number(remaining[0])))
    if remaining or not signed or (not has_special and not any(x<0 for x in signed)):return None
    return answer(total(signed),fmt(signed))


def _missing_duration(p):
    """An explicit total task duration less all specified task times."""
    if not has(r'\b(?:certain amount|unknown amount|some time)\b',p.body):return None
    if not 3<=len(p.numbers)<=10 or any(n.start>=len(p.body) for n in p.numbers):return None
    target=asked(p)
    if target not in _TIME:
        m=re.search(r'\bin (minutes?|hours?|seconds?)\b',p.question)
        target=label(m.group(1)) if m else ''
    if target not in ('minute','hour','second'):return None
    ts=tails(p);budget=[];spent=[]
    for i,n in enumerate(p.numbers):
        u=label(ts[i]);v=converted(n.value,u,target)
        if v is None:return None
        before=p.body[p.numbers[i-1].end if i else 0:n.start]
        if has(r'\btotal of\s*$',before):budget.append(v)
        elif has(r'\b(?:spent|spends?)\b',before) or (spent and has(r'^\s+(?:[a-z ]+,|[a-z ]+ and)\s*$',before)):
            spent.append(v)
        else:
            # Coordinated activities inherit "spent" within the same list.
            if spent and not has(r'[.;]',before):spent.append(v)
            else:return None
    if len(budget)!=1 or not spent:return None
    return answer(budget[0]-total(spent),'{} - ({})'.format(format_number(budget[0]),fmt(spent)))


def _next_mean(p):
    """One further observation must bring a fully listed sequence to a mean."""
    if not has(r'\b(?:next|another)\b',p.question) or not has(r'\baverage\b',p.body):return None
    if not 4<=len(p.numbers)<=25 or any(n.start>=len(p.body) for n in p.numbers):return None
    t=tokenize(p)
    m=re.search(r'\baverage of all (?:his|her|their|the) ([a-z]+) is (?:a )?Q0[.]',t)
    if not m:return None
    sequence=re.search(r'\b(?:he|she|they) ([a-z]+) (Q1[^.!?]+)[.]',t)
    if not sequence:return None
    # The observed verb must be the same action requested on the next one.
    verb=sequence.group(1).rstrip('s')
    if not has(r'\b'+re.escape(verb)+r'\b',p.question):return None
    ids=[int(x) for x in re.findall(r'Q(\d+)',sequence.group(2))]
    if ids!=list(range(1,len(p.numbers))):return None
    # Each observation is an explicitly enumerated value, not a rate.
    residue=re.sub(r'Q\d+','',sequence.group(2))
    if re.sub(r'\b(?:a|an|and)\b|[,\s]','',residue):return None
    mean=p.values[0]
    return answer(mean*len(p.numbers)-total(p.values[1:]),'{} x {} - ({})'.format(format_number(mean),len(p.numbers),fmt(p.values[1:])))


def _weighted_sizes(p):
    """Counted categories explicitly weigh or are worth a measured amount."""
    if not 4<=len(p.numbers)<=14:return None
    if has(r'\b(?:more|less|than|half|remaining|left|average|lost)\b',p.text.lower()):return None
    t=tokenize(p);rates={};used=set();target=asked(p)
    pat=r'\b(?:the )?([a-z]+(?: [a-z]+){0,3}?) (?:weigh|weighs|are worth|is worth) Q(\d+) ([a-z]+)(?: each)?(?=[,.;]|$)'
    for m in re.finditer(pat,t):
        key=label(re.sub(r'^(?:(?:if|and|the) )+','',m.group(1)));i=int(m.group(2));u=label(m.group(3))
        if key in rates or not compatible(u,target):return None
        rates[key]=p.numbers[i].value;used.add(i)
    # Postposed worth: N products worth M points.
    for m in re.finditer(r'Q(\d+) ([a-z -]+?) worth Q(\d+) ([a-z]+)',t):
        i,key,j,u=int(m.group(1)),label(m.group(2)),int(m.group(3)),label(m.group(4))
        if key in rates or not compatible(u,target):return None
        rates[key]=p.numbers[j].value;used.add(j)
    if not rates:return None
    terms=[];visited=set();ts=tails(p)
    for i,n in enumerate(p.numbers):
        if i in used:continue
        key=count_label(ts[i]);matches=[k for k in rates if compatible(key,k)]
        if len(matches)!=1:return None
        visited.add(matches[0]);terms.append(n.value*rates[matches[0]])
    if visited!=set(rates):return None
    return answer(total(terms),fmt(terms))


def _square_tiles(p):
    """Convert the two sides of a rectangle before dividing by square tiles."""
    if len(p.numbers)!=3:return None
    t=tokenize(p)
    rect=re.search(r'Q0 (feet|meters?|yards?|inches|centimeters?) (?:tall|wide|long|high) and Q1 \1 (?:tall|wide|long|high)',t)
    tile=re.search(r'\beach ([a-z -]+?) (?:she uses |he uses |they use )?is Q2 (inch|foot|meter|centimeter|yard)(?:es|s)? square\b',t)
    if not rect or not tile or not compatible(label(tile.group(1)),asked(p)):return None
    u=label(rect.group(1));v=label(tile.group(2));side=p.values[2]
    a=converted(p.values[0],u,v);b=converted(p.values[1],u,v)
    if a is None or b is None or side<=0 or (a/side).denominator!=1 or (b/side).denominator!=1:return None
    return answer(a*b/side**2,'{} x {} / ({} x {})'.format(*map(format_number,(a,b,side,side))))


def _mixed_rectangle_areas(p):
    """Combine individual rectangles and counted equal rectangles."""
    if not has(r'\bsquare\b',p.question) or not has(r'\b(?:and|combined|total|altogether|all)\b',p.question):return None
    t=tokenize(p);used=set();terms=[];counts={};unit=None
    pat=r'Q(\d+) (?:(feet|meters?|yards?|inches|centimeters?) )?by Q(\d+) (feet|meters?|yards?|inches|centimeters?)'
    for m in re.finditer(pat,t):
        a,u,b,v=int(m.group(1)),m.group(2),int(m.group(3)),m.group(4)
        if u and u!=v:return None
        if unit is not None and unit!=v:return None
        unit=v
        before=t[:m.start()]
        group=re.search(r'Q(\d+) ([a-z -]+?) (?:that are|that each measure|each measuring|each measure)\s*$',before)
        factor=Fraction(1)
        if group:
            i=int(group.group(1));key=label(group.group(2))
            if i in used:return None
            used.add(i);factor=p.numbers[i].value;counts[key]=factor
        elif not has(r'\b(?:measures?|measuring|is)\s*$',before):return None
        if used & {a,b}:return None
        used.update((a,b));terms.append(factor*p.numbers[a].value*p.numbers[b].value)
    if len(terms)<2 or not unit or not has(r'\bsquare '+unit+r'\b',p.question):return None
    for i,n in enumerate(p.numbers):
        if i in used:continue
        if n.start<len(p.body) or counts.get(label(tails(p)[i]))!=n.value:return None
        used.add(i)
    return answer(total(terms),fmt(terms))


def _reverse_pack_ledger(p):
    """Recover packed stock from departed and remaining packs plus loose items."""
    if len(p.numbers)!=4 or not has(r'\b(?:beginning|start|originally)\b',p.question):return None
    t=tokenize(p)
    recipe=re.search(r'Q0 ([a-z -]+?) in each ([a-z]+)\b',t)
    if not recipe or not compatible(label(recipe.group(1)),asked(p)):return None
    item,pack=label(recipe.group(1)),label(recipe.group(2))
    if not has(r'Q1 [a-z -]+ were not placed in (?:a|an) '+re.escape(pack)+r'\b',t):return None
    if not has(r'\b(?:gave away|sold|removed) Q2 '+re.escape(pack)+r'(?:s|es)?\b',t):return None
    if not has(r'\b(?:has|had) Q3 '+re.escape(pack)+r'(?:s|es)?\b',t):return None
    a,b,c,d=p.values
    return answer(a*(c+d)+b,'{} x ({} + {}) + {}'.format(*map(format_number,(a,c,d,b))))


def _remaining_workday(p):
    """Counted timed interruptions leave a workday at a stated output rate."""
    if len(p.numbers)!=4:return None
    t=tokenize(p)
    block=re.search(r'Q0 Q1-(hours?|minutes?) ([a-z]+)',t)
    budget=re.search(r'Q2-(hours?|minutes?) (?:workday|shift|work day)\b',t)
    rate=re.search(r'Q3 ([a-z -]+?) (?:an?|per|each) (hour|minute)\b',t)
    if not block or not budget or not rate or not has(r'\brest of\b',p.body):return None
    if not (category_match(label(rate.group(1)),asked(p)) or label(rate.group(1)).startswith(asked(p)+' ')):return None
    u=rate.group(2)
    used=converted(p.values[0]*p.values[1],label(block.group(1)),u)
    available=converted(p.values[2],label(budget.group(1)),u)
    if used is None or available is None:return None
    return answer((available-used)*p.values[3],'({} - {}) x {}'.format(*map(format_number,(available,used,p.values[3]))))


def _ratio_partition(p):
    """An explicit two-part ratio and total determine shares or their gap."""
    if len(p.numbers)!=3:return None
    t=tokenize(p)
    m=re.search(r'\bratio (?:of ([a-z -]+?) to ([a-z -]+?) (?:is|was)|of [^.;]+? (?:is|of)|of) Q0\s*:\s*Q1',t)
    if not m:return None
    # The remaining amount must explicitly be the whole population.
    before=t.split('Q2',1)[0]
    if not has(r'\b(?:total number|total|has)\b[^.;]*$',before):return None
    a,b,n=p.values
    if a+b<=0:return None
    if has(r'\b(?:more|less|difference)\b',p.question):
        if not has(r'\bthan\b',p.question):return None
        part=abs(a-b)
    elif m.group(1) and m.group(2):
        target=asked(p)
        if compatible(target,label(m.group(1))):part=a
        elif compatible(target,label(m.group(2))):part=b
        else:return None
    else:return None
    return answer(n*part/(a+b),'{} x {} / ({} + {})'.format(*map(format_number,(n,part,a,b))))


def _equal_losses(p):
    """Two categories lose equally; one initial count and both finals are known."""
    if len(p.numbers)!=3 or not has(r'\b(?:begin with|beginning|at first|originally)\b',p.question):return None
    if not has(r'\bsame number of [a-z -]+? and [a-z -]+? (?:flew away|left|were removed|were sold)\b',p.body):return None
    t=tokenize(p);ts=tails(p)
    first=count_label(ts[0]);second=count_label(ts[1]);third=count_label(ts[2])
    # Initial unknown stock is explicitly coordinated with the known stock.
    if not has(r'Q0 [a-z]+ and some [a-z]+\b',t) or first!=second or third==first:return None
    if not has(r'Q1 [a-z]+ and Q2 [a-z]+ are left\b',t):return None
    a,b,c=p.values
    if a<b:return None
    return answer(a+(a-b)+c,'{} + ({} - {}) + {}'.format(*map(format_number,(a,a,b,c))))


def _shared_picking(p):
    """An individual makes groups; companions each explicitly match that amount."""
    if len(p.numbers)!=3 or not has(r'\bin all|altogether|total|together',p.question):return None
    t=tokenize(p)
    count=re.search(r'\b([a-z]+) (?:fills?|makes?|picks?) Q0 ([a-z]+)',t)
    contents=re.search(r'\beach ([a-z]+) holds Q1 ([a-z -]+?)[.]',t)
    people=re.search(r"Q2 of ([a-z]+)'s [a-z]+ [a-z ]+the same amount as (?:her|him|them)\b",t)
    if not count or not contents or not people:return None
    if count.group(1)!=people.group(1) or label(count.group(2))!=label(contents.group(1)) or not compatible(label(contents.group(2)),asked(p)):return None
    a,b,c=p.values
    return answer(a*b*(c+1),'{} x {} x ({} + 1)'.format(*map(format_number,(a,b,c))))


def _split_purchases(p):
    """A fully enumerated shopping list is split equally among counted charges."""
    if not 3<=len(p.numbers)<=10 or not has(r'\bitems\b',p.question):return None
    if not has(r'\bsplit\b.*\bequally (?:across|among|between)\b',p.body):return None
    t=tokenize(p);last=len(p.numbers)-1
    split=re.search(r'\bsplit [^.!?]+ equally (?:across|among|between) Q'+str(last)+r' ([a-z -]+?)[.]',t)
    if not split or p.values[-1]<=0:return None
    # Every other quantity belongs to an explicit acquisition, or its
    # coordinated list, before the equal distribution.
    previous=False
    for i,n in enumerate(p.numbers[:-1]):
        before=p.body[p.numbers[i-1].end if i else 0:n.start]
        if has(r'\b(?:bought|buys?|got|received|purchased)\b',before):previous=True
        elif not (previous and has(r'\band (?:an additional )?\s*$',before) and not has(r'[.;]',before)):return None
        if not count_label(tails(p)[i]):return None
    return answer(total(p.values[:-1])/p.values[-1],'({}) / {}'.format(fmt(p.values[:-1]),format_number(p.values[-1])))


def _category_sales(p):
    """Two explicit category inventories followed by the same categories sold."""
    if len(p.numbers)!=4 or not has(r'\b(?:remain|remaining|left)\b',p.question):return None
    ts=tails(p);t=tokenize(p)
    stocks=[count_label(x) for x in ts[:2]]
    if not all(stocks) or stocks[0]==stocks[1]:return None
    if [count_label(x) for x in ts[2:]]!=stocks:return None
    if not has(r'\bthere are Q0 [a-z]+ and Q1 [a-z]+ for sale[.]',t):return None
    if not has(r'Q2 [a-z]+ and Q3 [a-z]+ are sold[.]',t):return None
    if not has(r'\b'+re.escape(asked(p))+r'\b',p.body):return None
    if any(p.values[i]<p.values[i+2] for i in (0,1)):return None
    return answer(total(p.values[:2])-total(p.values[2:]),'({}) - ({})'.format(fmt(p.values[:2]),fmt(p.values[2:])))


def _weekly_sessions(p):
    """Sessions per week, measured time per session, and an integer year count."""
    if len(p.numbers)!=3:return None
    t=tokenize(p)
    m=re.search(r'Q0 times a week for Q1 (hours?|minutes?) at a time',t)
    if not m or not has(r'\bevery year for Q2 years\b',t):return None
    target=asked(p);u=label(m.group(1))
    session=converted(p.values[1],u,target)
    if session is None:return None
    a,_,c=p.values
    return answer(a*session*52*c,'{} x {} x 52 x {}'.format(*map(format_number,(a,session,c))))


def _round_trip_detour(p):
    """A three-leg trip compared with the direct out-and-back trip."""
    if len(p.numbers)!=3 or not has(r'\badditional\b.*\bround trip\b',p.question):return None
    if not has(r'\bround trip without\b',p.question):return None
    t=tokenize(p);ts=tails(p);unit=asked(p)
    if not all(compatible(label(x),unit) for x in ts):return None
    # The last leg returns to the same start as the first leg departs from.
    start=re.search(r'\bfrom (?:his|her|their) ([a-z -]+?), [a-z]+ (?:drives?|walks?|travels?) Q0',t)
    if not start:return None
    if not has(r'Q2 [a-z]+ straight to (?:his|her|their) '+re.escape(start.group(1))+r'[.]',t):return None
    if not has(r'\bfrom there\b',t):return None
    a,b,c=p.values
    return answer(a+b-c,'({} + {} + {}) - 2 x {}'.format(*map(format_number,(a,b,c,c))))


def _comparative_shared_total(p):
    """Combine a stock with a category differing from it, then divide equally."""
    if len(p.numbers) not in (3,4):return None
    t=tokenize(p)
    relation=re.search(r'Q0 ([a-z -]+?) and there are Q1 more ([a-z -]+?) than ([a-z -]+?)[.]',t)
    if not relation or not compatible(label(relation.group(1)),label(relation.group(3))):return None
    first,second=label(relation.group(1)),label(relation.group(2))
    if not first or not second or first==second:return None
    split=re.search(r'\b(?:evenly|equally) divided among Q2 ([a-z]+)',t)
    query=re.search(r'how many ([a-z]+) will (?:one|each|Q3) ([a-z]+) receive',t)
    if not split or not query or not category_match(first,label(query.group(1))) or not category_match(second,label(query.group(1))):return None
    if label(split.group(1))!=label(query.group(2)):return None
    if len(p.numbers)==4 and p.values[3]!=1:return None
    a,b,c=p.values[:3]
    if c<=0:return None
    return answer((2*a+b)/c,'({} + ({} + {})) / {}'.format(*map(format_number,(a,a,b,c))))


def _sum_group_chain(p):
    """Two kinds of members per group share one stated output per member."""
    if len(p.numbers)!=4:return None
    t=tokenize(p)
    rate=re.search(r'Q0 ([a-z -]+?) per (?:each )?([a-z]+) in Q1 ([a-z]+)',t)
    contents=re.search(r'\beach ([a-z]+) has Q2 ([a-z -]+?) and Q3 ([a-z -]+?)[.]',t)
    if not rate or not contents:return None
    output,member,groups=label(rate.group(1)),label(rate.group(2)),label(rate.group(3))
    if groups!=label(contents.group(1)) or not compatible(output,asked(p)):return None
    if not all(category_match(label(contents.group(i)),member) for i in (2,3)):return None
    a,b,c,d=p.values
    return answer(a*b*(c+d),'{} x {} x ({} + {})'.format(*map(format_number,(a,b,c,d))))


def _budget_then_rate(p):
    """A time budget less fully counted activities, then a per-time output."""
    if not has(r'\b(?:time is up|time left|rest|remaining|leftover)\b',p.text.lower()):return None
    if not 4<=len(p.numbers)<=12:return None
    t=tokenize(p);ts=tails(p)
    budget=re.search(r'\b(?:has|have) Q0 (hours?|minutes?|seconds?) to\b',t)
    if not budget:return None
    ri=len(p.numbers)-1
    rate=re.search(r'Q'+str(ri)+r' ([a-z -]+?) (?:a|an|per|each) (hour|minute|second)\b',t)
    if not rate or not compatible(label(rate.group(1)),asked(p)):return None
    u=rate.group(2);available=converted(p.values[0],label(budget.group(1)),u)
    if available is None:return None
    used={0,ri};spent=[]
    for i,n in enumerate(p.numbers):
        if i in used:continue
        # An explicitly counted activity states its own total duration.
        if i+1<ri and has(r'^\s+[a-z -]+? that is\s*$',ts[i]):
            duration=converted(p.numbers[i+1].value,label(ts[i+1]),u)
            if duration is None:return None
            spent.append(n.value*duration);used.update((i,i+1));continue
        return None
    return answer((available-total(spent))*p.values[ri],'({} - ({})) x {}'.format(format_number(available),fmt(spent),format_number(p.values[ri])))


def _repeated_measures(p):
    """Two structures have a measured path, each traversed a stated frequency."""
    if len(p.numbers)!=4:return None
    if not has(r'\b(?:in total|total|in all)\b',p.text.lower()):return None
    t=tokenize(p);ts=tails(p)
    pat=r'\b(?:which )?has Q(\d+) ([a-z]+), Q(\d+) times\b'
    pairs=list(re.finditer(pat,t))
    if len(pairs)!=2:return None
    used=set();terms=[];units=set()
    for m in pairs:
        i,j=int(m.group(1)),int(m.group(3));u=label(m.group(2))
        if used & {i,j}:return None
        used.update((i,j));units.add(u);terms.append(p.numbers[i].value*p.numbers[j].value)
    if len(units)!=1 or used!=set(range(4)):return None
    unit=next(iter(units))
    if asked(p)!=unit and not has(r'\ba '+re.escape(unit)+r'\b',p.question):return None
    return answer(total(terms),fmt(terms))


def _monthly_net_stock(p):
    """An initial population with explicit births and deaths at monthly rates."""
    if len(p.numbers)!=4:return None
    t=tokenize(p)
    initial=re.search(r'\bthere are Q0 ([^.!?]+) at first[.]',t)
    if not initial or not compatible(label(initial.group(1)),asked(p)):return None
    gain=re.search(r'\bborn at the rate of Q1 per (day|week|month|year)',t)
    loss=re.search(r'\bdie at the rate of Q2 per (day|week|month|year)',t)
    duration=re.search(r'\bafter Q3 (day|week|month|year)s?\?',t)
    if not gain or not loss or not duration or gain.group(1)!=loss.group(1):return None
    unit=gain.group(1);source=duration.group(1)
    factors={'day':Fraction(1),'week':Fraction(7)}
    if source==unit:d=p.values[3]
    elif unit=='month' and source=='year':d=p.values[3]*12
    elif source in factors and unit in factors:d=p.values[3]*factors[source]/factors[unit]
    else:return None
    a,b,c,_=p.values
    return answer(a+(b-c)*d,'{} + ({} - {}) x {}'.format(*map(format_number,(a,b,c,d))))


def _labelled_task_costs(p):
    """Material costs per named task joined to task frequencies in the query."""
    if not 4<=len(p.numbers)<=12 or len(p.numbers)%2:return None
    if has(r'\b(?:more|less|than|half|average|left|remaining)\b',p.text.lower()):return None
    t=tokenize(p);costs={};used=set();target=asked(p)
    pat=r'Q(\d+) ([a-z -]+?) to ([a-z]+) (?:the |a |an )?([a-z -]+?)(?= and |[.;])'
    for m in re.finditer(pat,t):
        i=int(m.group(1));u=label(m.group(2));verb=m.group(3);key=label(m.group(4))
        if i in used or key in costs or not compatible(u,target):return None
        costs[key]=(verb,p.numbers[i].value);used.add(i)
    if not costs:return None
    terms=[]
    for key,(verb,cost) in costs.items():
        pat=(r'\b(?:'+re.escape(verb)+r'|and) (?:the |a |an )?'
             +re.escape(key)+r' Q(\d+) times\b')
        matches=list(re.finditer(pat,t))
        if len(matches)!=1:return None
        i=int(matches[0].group(1))
        if i in used or p.numbers[i].start<len(p.body):return None
        used.add(i);terms.append(p.numbers[i].value*cost)
    if used!=set(range(len(p.numbers))):return None
    return answer(total(terms),fmt(terms))


def _total_duration_less_stages(p):
    """Start-to-finish duration less all the named, measured stages."""
    if not 3<=len(p.numbers)<=10:return None
    if not has(r'\bfrom start to finish\b',p.body) or not p.question.startswith('how long'):return None
    ts=tails(p);target=label(ts[0])
    if target not in ('minute','hour','second'):return None
    values=[]
    for n,tail in zip(p.numbers,ts):
        v=converted(n.value,label(tail),target)
        if v is None:return None
        values.append(v)
    if not has(r'\bfrom start to finish\b',ts[-1]):return None
    if not has(r'\b(?:takes?|took) (?:her|him|them)\s*$',p.body[:p.numbers[-1].start]):return None
    return answer(values[-1]-total(values[:-1]),'{} - ({})'.format(format_number(values[-1]),fmt(values[:-1])))


def _measured_rectangle_difference(p):
    """Subtract two areas whose width and length are explicitly measured."""
    if len(p.numbers)!=4 or not has(r'\bdifference in area\b',p.question):return None
    t=tokenize(p)
    pairs=list(re.finditer(r'Q(\d+) (feet|meters?|yards?|inches|centimeters?) wide and Q(\d+) \2 long',t))
    if len(pairs)!=2 or pairs[0].group(2)!=pairs[1].group(2):return None
    used=set();areas=[]
    for m in pairs:
        i,j=int(m.group(1)),int(m.group(3))
        if used & {i,j}:return None
        used.update((i,j));areas.append(p.numbers[i].value*p.numbers[j].value)
    if used!=set(range(4)):return None
    return answer(abs(areas[0]-areas[1]),'|{} - {}|'.format(*map(format_number,areas)))


def _current_stock_gift_multiple(p):
    """An incoming gift is explicitly a multiple of the recipient's new stock."""
    if len(p.numbers)!=3 or not has(r'\btotal\b',p.question):return None
    t=tokenize(p);ts=tails(p)
    initial=re.search(r'\b([a-z]+) has Q0\b',t)
    gift=re.search(r'\bgives? (?:him|her|them) Q1 more\b',t)
    multiple=re.search(r'\bgives? (?:him|her|them) Q2 times more [a-z -]+? than (?:he|she|they) has\b',t)
    if not initial or not gift or not multiple:return None
    unit=asked(p)
    if not all(compatible(count_label(ts[i]),unit) for i in (0,1)):return None
    a,b,c=p.values
    return answer((a+b)*(c+1),'({} + {}) x ({} + 1)'.format(*map(format_number,(a,b,c))))


def _reverse_transfer_multiple(p):
    """Undo a gift after a named recipient's stock fixes a stated multiple."""
    if len(p.numbers)!=3:return None
    t=tokenize(p)
    start=re.search(r'\b([a-z]+) had some ([a-z -]+?),? and (?:he|she|they) gave Q0 of them to ([a-z]+)[.]',t)
    if not start:return None
    a,item,b=start.groups()
    if not has(r'\b'+a+r' has Q1 times more [a-z -]+? than '+b+r'[.]',t):return None
    if not has(r'\b'+b+r' had Q2 [a-z -]+? at first',t):return None
    if not has(r'how many [a-z -]+? did '+a+r' have at first',p.question):return None
    if not compatible(label(item),asked(p)):return None
    gift,factor,original=p.values
    return answer((original+gift)*factor+gift,'({} + {}) x {} + {}'.format(*map(format_number,(original,gift,factor,gift))))


def _common_point_difference(p):
    """Two scores use the same explicitly stated points per event."""
    if len(p.numbers)!=3 or not has(r'\bmore\b.*\bthan\b',p.question):return None
    t=tokenize(p)
    rate=re.search(r'(?:^|[.;]\s*)([a-z]+) (?:were|are) worth Q0 ([a-z]+)[.]',t)
    if not rate or not compatible(label(rate.group(2)),asked(p)):return None
    key=label(rate.group(1));ts=tails(p)
    if any(label(ts[i])!=key for i in (1,2)):return None
    for i in (1,2):
        if not has(r'\bscored\s*$',p.body[:p.numbers[i].start]):return None
    a,b,c=p.values
    return answer(a*abs(c-b),'{} x |{} - {}|'.format(*map(format_number,(a,c,b))))


def _greatest_pair_difference(p):
    """Compare differences within every fully enumerated container."""
    if not has(r'\bgreatest difference\b',p.question):return None
    t=tokenize(p);used=set();diffs=[];keys=[]
    pat=r'\b([a-z]+ [a-z]+) contains Q(\d+) ([a-z -]+?) and Q(\d+) ([a-z -]+?)[.]'
    for m in re.finditer(pat,t):
        key,i,u,j,v=m.group(1),int(m.group(2)),label(m.group(3)),int(m.group(4)),label(m.group(5))
        if used & {i,j} or not u or not v or u.split()[-1]!=v.split()[-1]:return None
        used.update((i,j));keys.append(key);diffs.append(abs(p.numbers[i].value-p.numbers[j].value))
    if len(diffs)<2 or len(set(keys))!=len(keys):return None
    unused=set(range(len(p.numbers)))-used
    if unused:
        if unused!={0} or p.values[0]!=len(diffs):return None
        intro=re.search(r'Q0 ([a-z]+) ([a-z]+(?:, [a-z]+)*(?: and [a-z]+)) contain',t)
        if not intro:return None
        names=re.split(r', | and ',intro.group(2))
        declared={label(intro.group(1))+' '+name for name in names}
        if declared!=set(keys):return None
    return answer(max(diffs),'Largest of '+fmt(diffs,', '))





def _enumerated_group_contents(p):
    """Explicit counts of containers, each with its own stated contents."""
    t=tokenize(p);used=set();terms=[];target=asked(p)
    if not 4<=len(p.numbers)<=12:return None
    pat=(r'\beach (?:(?:(?:Q(\d+)|one) )?of (?:another )?)?'
         r'Q(\d+) ([a-z -]+?) (?:holds?|has|contains?) Q(\d+) '
         r'([a-z -]+?)(?= and each|[.;]|$)')
    for m in re.finditer(pat,t):
        ref,i,group,j,out=m.groups();i,j=int(i),int(j)
        ids={i,j}
        if ref is not None:
            ref=int(ref)
            if p.numbers[ref].value!=1:return None
            ids.add(ref)
        if ids & used or not compatible(label(out),target):return None
        used.update(ids);terms.append(p.numbers[i].value*p.numbers[j].value)
    if len(terms)<2 or used!=set(range(len(p.numbers))):return None
    return answer(total(terms),fmt(terms))


def _type_output_chain(p):
    """Types times units per type per container, containers per time, duration."""
    if len(p.numbers)!=4:return None
    t=tokenize(p)
    types=re.search(r'Q0 ([a-z]+) of ([a-z -]+?)[.]',t)
    if not types:return None
    category,item=label(types.group(1)),label(types.group(2))
    contents=re.search(r'Q1 of each ([a-z]+) ([a-z -]+?) in each ([a-z]+)[.]',t)
    rate=re.search(r'Q2 ([a-z]+) per (hour|minute|day)\b',t)
    duration=re.search(r'\bin Q3 (hours?|minutes?|days?)\?',t)
    if not contents or not rate or not duration:return None
    if label(contents.group(1))!=category or not compatible(label(contents.group(2)),item):return None
    if label(contents.group(3))!=label(rate.group(1)) or not compatible(asked(p),item):return None
    d=converted(p.values[3],label(duration.group(1)),rate.group(2))
    if d is None:return None
    a,b,c,_=p.values
    return answer(a*b*c*d,fmt((a,b,c,d),' x '))


def _people_event_output(p):
    """Each person receives an output at every visited event in every hour."""
    if len(p.numbers)!=4:return None
    t=tokenize(p);ts=tails(p)
    duration=re.search(r'\bout for Q1 (hours?|minutes?|days?)[.]',t)
    events=re.search(r'\beach (hour|minute|day) they (?:visited|visit) Q2 ([a-z]+)[.]',t)
    output=re.search(r'\beach ([a-z]+) gives Q3 ([a-z -]+?) per ([a-z]+)[.]',t)
    if not duration or not events or not output:return None
    if label(output.group(1))!=label(events.group(2)) or not compatible(label(output.group(2)),asked(p)):return None
    actor=re.match(r'\s+([a-z]+)\b',ts[0])
    if not actor or label(actor.group(1))!=label(output.group(3)):return None
    d=converted(p.values[1],label(duration.group(1)),events.group(1))
    if d is None:return None
    a,_,c,e=p.values
    return answer(a*d*c*e,fmt((a,d,c,e),' x '))


def _relative_roundtrip_activity(p):
    """Two equal travel legs and an activity measured against both legs."""
    if len(p.numbers)!=2 or not has(r'\b(?:total|trip take)\b',p.question):return None
    t=tokenize(p)
    leg=re.search(r'Q0-(hour|minute) [a-z]+ each way[.]',t)
    multiple=re.search(r'Q1 times (?:as|at) long [^.!?]+? as (?:his|her|their) total [a-z]+ time',t)
    if not leg or not multiple or asked(p) not in (leg.group(1),'time'):return None
    a,b=p.values
    return answer(2*a*(1+b),'2 x {} x (1 + {})'.format(*map(format_number,(a,b))))


def _equal_gift_collections(p):
    """Two disjoint collections receive the same incoming gift each."""
    if len(p.numbers)!=3 or not has(r'\b(?:combined|together|total)\b',p.question):return None
    t=tokenize(p);ts=tails(p);target=asked(p)
    if not all(has(r'^\s+in (?:her|his|their) collection[.]',ts[i]) for i in (0,1)):return None
    if not has(r'\bgave them Q2 [a-z -]+? each[.]',t) or not compatible(label(ts[2]),target):return None
    # Both earlier clauses must explicitly collect the very requested unit.
    segments=(p.body[:p.numbers[0].start],p.body[p.numbers[0].end:p.numbers[1].start])
    if not all(has(r'\bcollect(?:ed|s|ing)? [a-z -]*'+re.escape(target)+r's?\b',x) for x in segments):return None
    a,b,c=p.values
    return answer(a+b+2*c,'{} + {} + 2 x {}'.format(*map(format_number,(a,b,c))))

_RULES = (
    _enumerated_group_contents, _type_output_chain, _people_event_output,
    _relative_roundtrip_activity, _equal_gift_collections,
    _periodic_stock, _dated_ledger, _rectangular_groups,
    _unused_area, _category_exclusions, _unit_exchange,
    _reverse_shared_stock, _daily_makeup, _weekly_record,
    _maximum_consumption, _measurement_difference, _recipe_totals,
    _capacity_remainder, _collected_comparison, _defective_sales,
    _inventory, _missing_duration, _next_mean,
    _weighted_sizes, _square_tiles, _mixed_rectangle_areas,
    _reverse_pack_ledger, _remaining_workday, _ratio_partition,
    _equal_losses, _shared_picking, _split_purchases,
    _category_sales, _weekly_sessions, _round_trip_detour,
    _comparative_shared_total, _sum_group_chain, _budget_then_rate,
    _repeated_measures, _monthly_net_stock, _labelled_task_costs,
    _total_duration_less_stages, _measured_rectangle_difference, _current_stock_gift_multiple,
    _reverse_transfer_multiple, _common_point_difference, _greatest_pair_difference,
)


def solve(problem):
    if any(n.value < 0 or n.kind == "percent" for n in problem.numbers):
        return None
    for rule in _RULES:
        result = rule(problem)
        if result is not None:
            return result
    return None
