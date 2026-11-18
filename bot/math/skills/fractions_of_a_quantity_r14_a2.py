"""Composed shares with explicit stock, transaction, and measurement scopes.

Each reader accounts for every quantity and selects the base of each fraction.
Unsupported comparisons and unidentified numeric roles cause abstention.
"""
import re
from fractions import Fraction

from ._fractions_common import has_fraction, _has, _answer
from .fractions_of_a_quantity_r11_a4 import _prepare, _fractions
from .fractions_of_a_quantity_r03_a3 import _words
from .counting_and_totals_r00_a1 import _singular


_LOSS = r'\b(?:gave|gives?|used|uses?|ate|eats?|spent|spends?|donated|donates?|removed|sold|sells?|lost|loses?|set aside|put|wilted|closed|closes?|dries|dried|turns?|scare[ds]?|fly)\b'
_GAIN = r'\b(?:purchases?|purchased|buys?|bought|received|receives?|added|adds?|gifted|gets?|got)\b'
_REST = r'\b(?:remain(?:ed|ing)?|remainder|rest|left)\b'


def _tail(p, n):
    return p.text[n.end:].lower()


def _unit(p, n):
    m = re.match(r'[- ]+(?:of )?(?:an? )?(?:(?:new|additional|extra) )?([a-z]+)', _tail(p, n))
    return _singular(m.group(1)) if m else ''


def _local(text):
    return re.split(r'[.;!?]|,(?!\d)', text)[0]


def _scope(p, n):
    """Text since the previous sentence, plus the fraction's own complement."""
    before = re.split(r'[.;!?]', p.text[:n.start].lower())[-1]
    return before + ' ' + _local(_tail(p, n))


def _stock(p, fs):
    """Successive explicit remainders, optional equal batches and literal deltas."""
    ns, text = p.numbers, p.text.lower()
    # An elapsed interval labels the narrative, rather than changing stock.
    ns = [n for n in ns if not (re.search(r'\bafter (?:about )?$',text[:n.start]) and re.match(r'\s+hours?\b',_tail(p,n)))]
    fs = [f for f in fs if f in ns]
    if not ns or not fs or not _has(r'\b(?:left|remain(?:ed|ing)?|keep|kept|have now|given out)\b', p.question):
        return None
    if _has(r'\b(?:times|per|as many|as much|more than|less than|originally|at first)\b', text):
        return None
    if any(n.start >= len(p.body) for n in ns) or ns[0] in fs:
        return None
    first = ns[0]
    if not _has(r'\b(?:has|had|have|there are|bought|ordered|brought|baked|made|harvests?|collected|received)\b', text[:first.start]):
        return None
    unit = 'money' if first.kind == 'money' else _unit(p, first)
    current = original = first.value
    if unit == 'dozen':
        m = re.match(r'\s+dozens?\s+([a-z]+)', _tail(p, first))
        if not m:
            return None
        unit = _singular(m.group(1))
        current = original = 12*first.value
    start = 1
    if len(ns) > 2 and ns[1] not in fs and ns[1].start < fs[0].start and unit != 'money':
        second = ns[1]
        if not ((re.match(r'\s+(?:batches|boxes|packs|bags|groups)\b', _tail(p, first)) or _has(r'\b(?:that have|have|has|with)\s*$',text[first.end:second.start]))
                and _has(r'\beach\b', _local(_tail(p, second)))):
            return None
        current = original = first.value*second.value
        unit = _unit(p, second)
        start = 2
    container = re.search(r'\bthe rest in (?:a|the) ([a-z]+)', text)
    contained = bool(len(fs)>1 and container and all(re.search(r'\bof the [a-z]+ in the '+re.escape(container.group(1))+r'\b', _tail(p,n)) for n in fs[1:]))
    if unit not in _words(p.question) and not contained and not (unit == 'money' and _has(r'\b(?:money|dollars?)\b',p.question)):
        return None
    if _has(r'\beach\b', text) and start != 2:
        return None
    previous = ns[start-1].end
    seen_share = False
    for i, n in enumerate(ns[start:], start):
        before = text[previous:n.start]
        end = ns[i+1].start if i+1 < len(ns) else len(p.body)
        after = text[n.end:end]
        if n in fs:
            # No invented base: later fractions explicitly refer to the rest,
            # or explicitly say original; a bare repeated share is ambiguous.
            scoped_rest = _has(_REST, _scope(p, n)) or (seen_share and contained)
            scoped_original = _has(r'\b(?:original|initial)\b', after)
            if seen_share and not (scoped_rest or scoped_original):
                return None
            if not (_has(_LOSS, before) or (seen_share and _has(r'\band\s*$',before)) or _has(r'\b(?:were|was|are|is) (?:wilted|eaten|sold|removed)\b|\bdecide to fly\b', after)):
                return None
            if not (re.match(r'\s+(?:of|the|to|his|her|their|for)\b|\s*[,.;]', after)):
                return None
            base = original if scoped_original else current
            current -= base*n.value
            seen_share = True
        else:
            losses = list(re.finditer(_LOSS+'|'+_GAIN, before))
            elided_loss = _has(r'\band (?:another|an additional)\s*$', before)
            if not losses and not elided_loss:
                return None
            gain = bool(losses and _has(_GAIN, losses[-1].group()))
            if _unit(p,n) != unit and not (unit=='money' and n.kind=='money') and not (elided_loss and re.match(r'\s+to\b', after)):
                return None
            current += n.value if gain else -n.value
        if current < 0:
            return None
        previous = n.end
    return _answer(current, 'Convert the starting groups to items, then apply each stated change to its base')


def _gift_then_share(p, fs):
    if len(p.numbers) != 4 or len(fs) != 2:
        return None
    initial, f, donor, g = p.numbers
    if fs != [f,g] or _unit(p,initial) != _unit(p,donor):
        return None
    text = p.text.lower()
    owner = re.search(r'\b([a-z]+) (?:has|had)\s*$', text[:initial.start])
    if not owner or not _has(r'\b'+owner.group(1)+r'\b',p.question):
        return None
    if not _has(r'\b(?:gave|gives) '+owner.group(1)+r'\s+(?:an? )?$', text[initial.end:f.start]):
        return None
    if not re.fullmatch(r'\s+of (?:his|her|their)\s+',text[f.end:donor.start]):
        return None
    if not _has(r'\b'+owner.group(1)+r' (?:then )?(?:gave|gives)\s+(?:an? )?$',text[donor.end:g.start]):
        return None
    if not re.match(r'\s+of (?:his|her|their) '+re.escape(_unit(p,initial))+r's?\b',_tail(p,g)):
        return None
    if not _has(_REST,p.question):
        return None
    return _answer((initial.value+f.value*donor.value)*(1-g.value), 'Add the donor\'s share, then remove the recipient\'s stated share')


def _inventory_share(p, fs):
    """A listed whole, optionally reduced and replenished, then a subset."""
    if not 1 <= len(fs) <= 2 or len(p.numbers) < 4:
        return None
    text = p.text.lower()
    before = [n for n in p.numbers if n.start < fs[0].start]
    if not 2 <= len(before) <= 6 or any(n in fs for n in before):
        return None
    if not _has(r'\b(?:there are|there were|has|have|had)\b',text[:before[0].start]):
        return None
    # A simple enumeration, without comparison or rate syntax.
    if _has(r'\b(?:more|fewer|less|each|per|times)\b',text[:fs[0].start]):
        return None
    for a,b in zip(before,before[1:]):
        if not re.fullmatch(r'\s+[a-z]+(?: [a-z]+)?\s*,?\s*(?:and\s*)?',text[a.end:b.start]):
            return None
    f = fs[-1]
    scope = re.match(r'\s+of (?:all )?(?:the )?([a-z]+)\b([^.;!?]*)',_tail(p,f))
    if not scope or _singular(scope.group(1)) not in _words(p.question):
        return None
    label = _words(scope.group(2)) - {'get','exactly'}
    if not label & _words(p.question):
        return None
    current = sum((n.value for n in before),Fraction(0))
    pending = [n for n in p.numbers if n not in before and n != f]
    if len(fs)==1 and pending:
        return None
    previous = before[-1].end
    for n in pending:
        bridge = text[previous:n.start]
        if n in fs:
            if not _has(r'\b(?:bought|sold|gave|removed)\b',bridge) or not re.match(r'\s+of (?:all )?(?:the )?'+scope.group(1)+r'\b',_tail(p,n)):
                return None
            current *= 1-n.value
        else:
            if not _has(r'\b(?:gifted|added|bought|received)\b',bridge):
                return None
            current += n.value
        previous = n.end
    return _answer(current*f.value,'Add the listed stock, apply the stated changes, and select the requested subset')


def _expense_chain(p, fs):
    """A budget minus an expense and expenses proportional to the last one."""
    ns, text = p.numbers, p.text.lower()
    if len(ns)<4 or len(fs)!=len(ns)-2 or not _has(_REST,p.question):
        return None
    budget, first = ns[:2]
    if budget.kind!='money' or first.kind!='money' or ns[2:]!=fs:
        return None
    if not _has(r'\bbudget\b',_scope(p,budget)) or not _has(r'\b(?:bought|spent|paid)\b',text[budget.end:first.start]):
        return None
    total = last = first.value
    for i,f in enumerate(fs):
        bridge = text[ns[i+1].end:f.start]
        tail = _local(_tail(p,f))
        if not _has(r'\b(?:spent|used|paid)\b',bridge):
            return None
        if not re.match(r'\s+(?:of )?(?:that amount|the [a-z ]+? cost)\b',tail):
            return None
        last *= f.value
        total += last
    return _answer(budget.value-total,'Subtract the initial expense and each expense based on the preceding expense from the budget')


def _currency_split(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(ns)!=4 or len(fs)!=1:
        return None
    total,f,a,b=ns
    if fs!=[f] or any(n.kind!='money' for n in (total,a,b)):
        return None
    if not _has(r'\b(?:change|exchange)\b',text) or not _has(r'\b(?:all|total)\b',p.question):
        return None
    if not re.match(r'\s+of (?:the |his |her |their )?money into\s*$',text[f.end:a.start]):
        return None
    ma=re.match(r'\s+([a-z]+)',_tail(p,a)); mb=re.match(r'\s+([a-z]+)',_tail(p,b))
    if not ma or not mb or ma.group(1)!=mb.group(1) or _singular(ma.group(1)) not in _words(p.question):
        return None
    if not _has(r'\b(?:rest|remaining)\b[^.;]*\binto\s*$',text[a.end:b.start]):
        return None
    return _answer(total.value*f.value/a.value+total.value*(1-f.value)/b.value,'Divide each allocation by its denomination and add the resulting counts')


def _relative_joint_savings(p,fs):
    if len(p.numbers)!=3 or len(fs)!=2:
        return None
    base,f,g=p.numbers
    if fs!=[f,g] or base.kind!='money':
        return None
    text=p.text.lower()
    relative=re.match(r'\s+(less|more) money\b',_tail(p,f))
    if not relative or not _has(r'\b(?:received|earned|earns|made|makes)\b',text[:base.start]):
        return None
    if not _has(r'\bboth\b[^.;]*\bsave\s*$',text[f.end:g.start]):
        return None
    if not re.match(r'\s+of their earnings\b',_tail(p,g)):
        return None
    if not _has(r'\b(?:total|joint|combined)\b',p.question):
        return None
    other=base.value*(1+f.value if relative.group(1)=='more' else 1-f.value)
    return _answer((base.value+other)*g.value,'Find the second earnings from the relative change, then save the stated share of both earnings')


def _scaled_trip(p,fs):
    if len(p.numbers)!=4 or len(fs)!=1 or not _has(r'\b(?:miles?|kilometers?|distance)\b',p.question):
        return None
    hours,speed,f,factor=p.numbers
    if fs!=[f] or _unit(p,hours)!='hour':
        return None
    if not re.match(r'\s+(?:miles?|kilometers?) per hour\b',_tail(p,speed)):
        return None
    if not re.match(r'\s+the time at\s*$',p.text[f.end:factor.start].lower()) or not re.match(r'\s+times the speed\b',_tail(p,factor)):
        return None
    return _answer(hours.value*speed.value*(1+f.value*factor.value),'Add the original distance and the distance at the scaled time and speed')


def _area_work(p,fs):
    if len(p.numbers)!=4 or len(fs)!=1 or not _has(r'\bhours?\b',p.question):
        return None
    a,b,rate,f=p.numbers
    if fs!=[f] or not re.fullmatch(r'\s+[a-z]+ by\s+',p.text[a.end:b.start].lower()):
        return None
    if _unit(p,a)!=_unit(p,b) or not re.match(r'\s+minutes?\b',_tail(p,rate)):
        return None
    if not _has(r'\beach '+re.escape(_unit(p,a))+r'\b',p.text[rate.end:f.start].lower()):
        return None
    if not re.match(r'\s+as long\b',_tail(p,f)):
        return None
    return _answer(a.value*b.value*rate.value*f.value/60,'Rows x columns x time per item x reduced time factor, converted to hours')


def _introductory_price(p,fs):
    if len(p.numbers)!=4 or len(fs)!=1:
        return None
    price,f,fee,duration=p.numbers
    if fs!=[f] or price.kind!='money' or fee.kind!='money' or _unit(p,duration)!='month':
        return None
    text=p.text.lower()
    if duration.start<len(p.body) or not re.match(r'\s+per month\b',_tail(p,price)):
        return None
    if not _has(r'\bfirst month\b',text[price.end:f.start]) or not re.match(r'\s+the normal price\b',_tail(p,f)):
        return None
    if not _has(r'\b(?:extra|additional) fee of\s*$',text[f.end:fee.start]):
        return None
    if not _has(r'\b(?:pay|paid)\b',p.question):
        return None
    return _answer(price.value*(duration.value-1+f.value)+fee.value,'Regular monthly charges, replacing the first month by its promotional share, plus the extra fee')



def _disjoint_categories(p,fs):
    """Three or more labelled allocations of one whole; no nested bases."""
    ns,text=p.numbers,p.text.lower()
    if len(fs)<3 or ns[0] in fs or not _has(r'\b(?:rest|left|remaining)\b',p.body+' '+p.question):
        return None
    base=ns[0]
    others=[n for n in ns[1:] if n not in fs]
    for n in others:
        # Recipient counts are metadata only for a collective allocation.
        if not (_has(r'\bfor (?:his|her|their)\s*$',text[:n.start]) and
                _unit(p,n) in ('child','children','friend') and not _has(r'\beach\b',_local(_tail(p,n)))):
            return None
    if _has(r'\b(?:times|per|each|more|less|both)\b',text):
        return None
    for f in fs:
        tail=_local(_tail(p,f))
        if not re.match(r'\s+(?:of|for|the|were|are|was|is)\b',tail):
            return None
        if _has(_REST,tail):
            return None
    rest=re.search(r'\bthe rest (?:were|are|was|is) ([^.;]+)',p.body)
    if not (_has(_REST,p.question) or (rest and _words(rest.group(1)) & _words(p.question))):
        return None
    return _answer(base.value*(1-sum((f.value for f in fs),Fraction(0))), 'Whole minus its explicitly separate category shares')


def _overlapping_shares(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(fs)!=3 or len(ns)!=4 or ns[0] in fs:
        return None
    base,a,b,both=ns
    if fs!=[a,b,both] or not _has(r"\b(?:not|don't|do not)\b.*\beither\b",p.question):
        return None
    overlap=re.match(r'\s+(?:[a-z]+ )?both ([a-z]+) and ([a-z]+)',_tail(p,both))
    if not overlap:
        return None
    if not _has(r'\b'+re.escape(overlap.group(1))+r'\b',_local(_tail(p,a))) or not _has(r'\b'+re.escape(overlap.group(2))+r'\b',_local(_tail(p,b))):
        return None
    if both.value>min(a.value,b.value):
        return None
    return _answer(base.value*(1-a.value-b.value+both.value),'Subtract the two shares from the whole and add their overlap once')


def _weighted_groups(p,fs):
    """A fractional group, a counted group, and a rest group with unit yields."""
    ns,text=p.numbers,p.text.lower()
    if len(ns)!=6 or len(fs)!=1:
        return None
    total,f,r1,count,r2,r3=ns
    if fs!=[f] or _unit(p,total) not in _words(_local(_tail(p,f))):
        return None
    unit=_unit(p,r1)
    if not unit or unit!=_unit(p,r2) or unit!=_unit(p,r3) or unit not in _words(p.question):
        return None
    if not all(_has(r'\beach\b',_local(_tail(p,n))) for n in (r1,r2,r3)):
        return None
    if not _has(r'\bthe rest (?:have|has)\s*$',text[r2.end:r3.start]):
        return None
    first=total.value*f.value
    rest=total.value-first-count.value
    if rest<0:
        return None
    return _answer(first*r1.value+count.value*r2.value+rest*r3.value,'Find each group size, multiply by its per-group yield, then add the yields')


def _complementary_capacity(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(fs)!=2 or len(ns)!=7:
        return None
    total,f,a,g,b,one,capacity=ns
    if fs!=[f,g] or f.value+g.value!=1 or one.value!=1:
        return None
    if not re.match(r'\s+(?:of )?(?:the )?'+re.escape(_unit(p,total))+r's?\b',_tail(p,f)):
        return None
    if _unit(p,a)!=_unit(p,b) or _unit(p,one)!=_unit(p,a) or _unit(p,capacity) not in _words(p.question):
        return None
    if not _has(r'\bthe other\s*$',text[a.end:g.start]):
        return None
    if not _has(r'\b(?:accommodate|hold|holds)\b',text[one.end:capacity.start]):
        return None
    return _answer(total.value*(f.value*a.value+g.value*b.value)*capacity.value,'Add the capacities of the complementary groups and multiply by capacity per item')


def _markup_per_item(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(ns)!=3 or len(fs)!=1:
        return None
    count,cost,f=ns
    if fs!=[f] or cost.kind!='money' or count.kind=='money' or count.value<=0:
        return None
    if not _has(r'\bbought\b',text[:count.start]) or not _has(r'\bfor (?:just )?$',text[count.end:cost.start]):
        return None
    if not re.match(r'\s+of the initial investment in profits?\b',_tail(p,f)):
        return None
    if not _has(r'\bselling price\b.*\beach\b',p.question):
        return None
    return _answer(cost.value*(1+f.value)/count.value,'Investment plus the requested fractional profit, divided by item count')


def _incorrect_difference(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(ns)!=3 or len(fs)!=1:
        return None
    f,mistakes,total=ns
    if fs!=[f] or not re.match(r'\s+of incorrect answers\b',_tail(p,f)):
        return None
    if not re.match(r'\s+mistakes\b',_tail(p,mistakes)) or not re.match(r'\s+questions\b',_tail(p,total)):
        return None
    if not _has(r'\bmore correct answers\b',p.question):
        return None
    owner=re.search(r'\b([a-z]+) got\s*$',text[f.end:mistakes.start])
    asked=re.search(r'\bcorrect answers does ([a-z]+) have\b',p.question)
    if not owner or not asked or owner.group(1)!=asked.group(1):
        return None
    return _answer(total.value*f.value-mistakes.value,'Difference in correct answers equals the opposite difference in mistakes')


def _per_instance_removals(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(fs)<2 or len(ns)!=len(fs)+3:
        return None
    count,per=ns[:2]
    literal=ns[-1]
    if count.value!=len(fs)+1 or ns[2:-1]!=fs:
        return None
    if _unit(p,per)!=_unit(p,literal) or _unit(p,per) not in _words(p.question):
        return None
    if not _has(r'\btotal\b',p.question) or not _has(r'\bremoved\b',p.question):
        return None
    # Each share has its own indexed owner and explicitly refers to that
    # owner's whole, rather than the remainder of a prior owner.
    for f in fs:
        if not re.match(r'\s+of (?:all )?(?:his|her|their) '+re.escape(_unit(p,per))+r'\b',_tail(p,f)):
            # Plural normalization may leave the surface noun unchanged.
            if not re.match(r'\s+of (?:all )?(?:his|her|their) [a-z]+ removed\b',_tail(p,f)):
                return None
    if not all(_has(r'\b(?:first|second|third|fourth|fifth|last) (?:person|adult|child)\b',_scope(p,f)) for f in fs):
        return None
    if not _has(r'\blast (?:person|adult|child)\b',text[fs[-1].end:literal.start]):
        return None
    return _answer(per.value*sum((f.value for f in fs),Fraction(0))+literal.value,'Sum each individual share of the common whole and the final literal removal')


def _independent_group_losses(p,fs):
    """Whole equal groups; a share of a named group, plus literal removals."""
    ns,text=p.numbers,p.text.lower()
    if len(ns)<5 or len(fs)<2 or not _has(_REST,p.question):
        return None
    count,size=ns[:2]
    if not re.match(r'\s+(?:large )?([a-z]+)',_tail(p,count)):
        return None
    group=re.match(r'\s+(?:large )?([a-z]+)',_tail(p,count)).group(1)
    if not _has(r'\beach\b',text[count.end:size.start]) or _unit(p,size) not in _words(p.question):
        return None
    # Each named source is one of the equal groups, not the combined stock.
    labels=[]
    total=count.value*size.value
    previous=size.end
    for n in ns[2:]:
        before=text[previous:n.start]
        if not _has(_LOSS,before):
            return None
        if n in fs:
            m=re.match(r'\s+of the ([a-z]+) '+re.escape(_singular(group))+r'\b',_tail(p,n))
            if not m or m.group(1) in labels:
                return None
            labels.append(m.group(1))
            total-=n.value*size.value
        else:
            if _unit(p,n)!=_unit(p,size):
                return None
            total-=n.value
        previous=n.end
    if count.value!=len(labels) or any(label in _words(p.question) for label in labels):
        return None
    return _answer(total,'Start with all equal groups and subtract each named group share and literal removal')


def _nested_unfinished(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(ns)!=4 or len(fs)!=3 or fs!=ns[1:]:
        return None
    total,a,b,c=ns
    if not _has(r'\bfinished\b',p.question):
        return None
    if not _has(r"\b(?:unable to finish|couldn't finish|did not finish)\b",_local(_tail(p,a))):
        return None
    if not re.match(r'\s+of the remaining\b',_tail(p,b)):
        return None
    middle=re.match(r'\s+of the remaining [a-z]+ were ([a-z]+)',_tail(p,b))
    if not middle or not re.match(r'\s+of those '+re.escape(middle.group(1))+r' [a-z]+',_tail(p,c)):
        return None
    if not _has(r"\bcouldn't finish\b",_local(_tail(p,c))):
        return None
    return _answer(total.value*(1-a.value)*(1-b.value*c.value),'Remove the first unfinished group, then only the unfinished share of the intermediate subset')


def _changing_fill_rate(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(ns)!=7 or len(fs)!=1:
        return None
    count,capacity,t1,r1,t2,f,r2=ns
    if fs!=[f] or _unit(p,capacity)!=_unit(p,r1) or _unit(p,r1)!=_unit(p,r2):
        return None
    if _unit(p,t1)!=_unit(p,t2) or _unit(p,t1) not in _words(p.question):
        return None
    if not _has(r'\beach\b',text[count.end:capacity.start]) or not _has(r'\bholds\b',text[count.end:capacity.start]):
        return None
    if not re.match(r'\s+that rate\b',_tail(p,f)) or not _has(r'\bthe rest\b',text[f.end:r2.start]):
        return None
    if not all(re.match(r'\s+[a-z]+(?: of [a-z]+)? per '+re.escape(_unit(p,t1))+r'\b',_tail(p,n)) for n in (r1,r2)):
        return None
    remaining=count.value*capacity.value-r1.value*t1.value-r1.value*f.value*t2.value
    if remaining<0 or r2.value<=0:
        return None
    return _answer(t1.value+t2.value+remaining/r2.value,'Subtract output in the first two timed phases, then add the time for the remaining output')


def _category_ledger(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(fs)!=1 or not _has(_REST,p.question):
        return None
    f=fs[0]
    initial=[n for n in ns if n.start<f.start]
    if len(initial)<2 or not _has(r'\b(?:had|has|have)\b',text[:initial[0].start]):
        return None
    if not all(re.fullmatch(r'\s+[a-z]+\s*,?\s*(?:and\s*)?',text[a.end:b.start]) for a,b in zip(initial,initial[1:])):
        return None
    categories={_unit(p,n):n.value for n in initial}
    if len(categories)!=len(initial):
        return None
    previous=initial[-1].end
    for n in ns[len(initial):]:
        after=_local(_tail(p,n))
        before=text[previous:n.start]
        if n==f:
            m=re.match(r'\s+(?:of )?(?:the )?([a-z]+) (?:were|are) sold\b',after)
            unit=_singular(m.group(1)) if m else ''
            if unit not in categories:
                return None
            categories[unit]*=1-f.value
        else:
            unit=_unit(p,n)
            if re.match(r'\s+of them\b',after):
                references=[u for u in categories if _has(r'\b'+re.escape(u)+r's?\b',before)]
                if len(references)!=1:
                    return None
                unit=references[0]
            if unit not in categories or not _has(r'\b(?:adopted|sold|went loose|removed|lost)\b',after):
                return None
            categories[unit]-=n.value
        previous=n.end
    if min(categories.values())<0:
        return None
    asked=[key for key in categories if key in _words(p.question)]
    value=sum((categories[key] for key in asked),Fraction(0)) if asked else sum(categories.values(),Fraction(0))
    return _answer(value,'Apply each loss to its named category, then add the requested remaining categories')


def _complementary_yields(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(fs)!=2 or fs[0].value+fs[1].value!=1:
        return None
    if len(ns)==5 and fs==[ns[1],ns[3]]:
        total,f,a,g,b=ns
        group=_unit(p,total)
        # Both equal parts refer to the same explicit whole, not different
        # owners or independent groups.
        if not re.match(r'\s+of (?:the |his |her )?[a-z]+\b',_tail(p,f)) or not (re.match(r'\s+of (?:the |his |her )?[a-z]+\b',_tail(p,g)) or (_has(r'\bsecond\s*$',text[:g.start]) and re.match(r'\s+at a speed\b',_tail(p,g)))):
            return None
        if not _has(r'\b(?:bottom|top|first|second|other)\b',text):
            return None
        if _unit(p,a)!=_unit(p,b):
            return None
        if re.match(r'\s+(?:miles?|kilometers?) per hour\b',_tail(p,a)):
            if group!='hour' or not _has(r'\b(?:miles?|kilometers?)\b',p.question):
                return None
        elif _unit(p,a) not in _words(p.question) or not all(_has(r'\beach '+re.escape(group)+r'\b',_local(_tail(p,n))) for n in (a,b)):
            return None
        return _answer(total.value*(f.value*a.value+g.value*b.value),'Split the whole into the stated complementary parts and add their individual yields')
    if len(ns)==4 and fs==[ns[0],ns[2]]:
        f,a,g,b=ns
        if not all(re.match(r'\s+of the year\b',_tail(p,n)) for n in fs):
            return None
        if not all(re.match(r'\s+miles? per week\b',_tail(p,n)) for n in (a,b)):
            return None
        if not _has(r'\byear\b',p.question) or not _has(r'\bmiles?\b',p.question):
            return None
        return _answer(52*(f.value*a.value+g.value*b.value),'Use 52 weeks per year and add the mileage from each stated part of the year')
    return None


def _two_category_departures(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(ns)!=4 or len(fs)!=2:
        return None
    total,a,b,known=ns
    if fs!=[a,b] or not _has(r'\b(?:remained|remaining|left)\b',p.question):
        return None
    labels=[]
    for f in fs:
        m=re.match(r'\s+of the ([a-z]+)\b([^.;]*)',_tail(p,f))
        if not m or not _has(r'\bleft\b',m.group(2)):
            return None
        labels.append(_singular(m.group(1)))
    if len(set(labels))!=2 or _unit(p,known) not in labels:
        return None
    # Explicitly asks for the original population's remainder.
    if _unit(p,total) not in _words(p.question):
        return None
    i=labels.index(_unit(p,known))
    shares=[a.value,b.value]
    return _answer(known.value*(1-shares[i])+(total.value-known.value)*(1-shares[1-i]),'Split the whole into the known category and its complement, then remove each category share')


def _tip_change(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(ns)!=4 or len(fs)!=1:
        return None
    count,price,f,paid=ns
    if fs!=[f] or price.kind!='money' or paid.kind!='money':
        return None
    if not _has(r'\btip\b',text[price.end:f.start]) or not re.match(r'\s+of the total cost\b',_tail(p,f)):
        return None
    if not _has(r'\beach\b',text[price.end:f.start]) or not _has(r'\bchange\b',p.question):
        return None
    return _answer(paid.value-count.value*price.value*(1+f.value),'Payment minus the purchase cost and its fractional tip')


def _shared_units(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(fs)<2 or len(ns)!=len(fs)+2 or ns[0] in fs or ns[-1] in fs:
        return None
    count,size=ns[0],ns[-1]
    unit=_unit(p,count)
    if not _has(_REST,p.question) or _unit(p,size) not in _words(p.question):
        return None
    per=re.search(r'\beach ([a-z]+)\b',text[fs[-1].end:size.start])
    whole=re.match(r'\s+([a-z]+)\b',_tail(p,count))
    if not per or not whole or not (whole.group(1)==per.group(1)+'s' or _singular(whole.group(1))==_singular(per.group(1))):
        return None
    unit=per.group(1)
    previous=count.end
    for f in fs:
        if not re.match(r'\s+of (?:an? |the )?'+re.escape(unit)+r'\b',_tail(p,f)):
            return None
        if not _has(_LOSS,text[previous:f.start]):
            return None
        previous=f.end
    return _answer((count.value-sum((f.value for f in fs),Fraction(0)))*size.value,'Subtract the fractional units consumed, then convert the remaining units to pieces')


def _indexed_capacities(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(fs)<2 or len(ns)!=2*len(fs)+1:
        return None
    count=ns[0]
    amounts=ns[1:len(fs)+1]
    if count.value!=len(fs) or ns[len(fs)+1:]!=fs or any(n in fs for n in amounts):
        return None
    if not _has(r'\brespectively\b',text[amounts[-1].end:fs[0].start]):
        return None
    if len({_unit(p,n) for n in amounts})!=1 or _unit(p,amounts[0]) not in _words(p.question):
        return None
    labels=('first','second','third','fourth','fifth','sixth')
    previous=amounts[-1].end
    for i,f in enumerate(fs):
        if not _has(r'\b'+labels[i]+r' '+re.escape(_unit(p,count))+r'\b',text[previous:f.start]):
            return None
        if not re.match(r'\s+(?:full|of its capacity)\b',_tail(p,f)):
            return None
        previous=f.end
    return _answer(sum((a.value*f.value for a,f in zip(amounts,fs)),Fraction(0)),'Multiply each listed capacity by its indexed fill fraction, then add the contents')


def _monthly_pay_expenses(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(ns)<4 or len(fs)!=1:
        return None
    rate,hours,f=ns[:3]
    expenses=ns[3:]
    if fs!=[f] or rate.kind!='money' or any(n.kind!='money' for n in expenses):
        return None
    if not re.match(r'\s+per hour\b',_tail(p,rate)) or not re.match(r'[- ]hour workweek\b',_tail(p,hours)):
        return None
    if not _has(r'\b(?:monthly|month)\b',p.question) or not _has(r'\bafter\b',p.question):
        return None
    if not re.match(r'\s+of the money on\b',_tail(p,f)) or not _has(r'\bper month\b',_tail(p,expenses[-1])):
        return None
    return _answer(rate.value*hours.value*4*(1-f.value)-sum((n.value for n in expenses),Fraction(0)),'Four weeks of hourly pay minus its fractional expense and the fixed monthly expenses')


def _gift_cost_savings(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(ns)!=4 or len(fs)!=1:
        return None
    cost,saved,f,extra=ns
    if fs!=[f] or any(n.kind!='money' for n in (cost,saved,extra)):
        return None
    if not _has(r'\bsaved\b',text[cost.end:saved.start]) or not _has(r'\bsaved\b',text[saved.end:f.start]):
        return None
    ref=re.match(r'\s+of the cost of the ([a-z]+)',_tail(p,f))
    if not ref or not _has(r'\b'+re.escape(ref.group(1))+r'\b',text[:cost.start]):
        return None
    if not _has(r'\bcosts?\s*$',text[f.end:extra.start]) or not _has(_REST,p.question):
        return None
    return _answer(saved.value+cost.value*f.value-cost.value-extra.value,'Combine the literal savings and the savings based on the gift price, then pay both costs')


def _referenced_gift_total(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(ns)!=4 or len(fs)!=2:
        return None
    a,b,f,g=ns
    if fs!=[f,g] or _unit(p,a)!=_unit(p,b) or _unit(p,a) not in _words(p.question):
        return None
    if not _has(r'\b(?:already had|already has)\b',text[a.end:b.start]):
        return None
    # The gift explicitly points to the second stock's location.
    location=re.match(r'\s+[a-z]+ in (?:his|her|their) ([a-z]+)',_tail(p,b))
    if not location or not re.match(r'\s+the amount (?:he|she|they) already had in (?:his|her|their) '+re.escape(location.group(1))+r'\b',_tail(p,f)):
        return None
    if not _has(r'\b(?:gave|gives?)\b',text[b.end:f.start]) or not re.match(r'\s+of (?:his|her|their) total amount\b',_tail(p,g)):
        return None
    if not _has(r'\b(?:give|gives?)\b',p.question):
        return None
    return _answer((a.value+b.value+b.value*f.value)*g.value,'Add both stocks and the gift based on the referenced stock, then take the share given away')


def _category_expression_chain(p,fs):
    """Counted categories related to one category or a sum of categories."""
    ns,text=p.numbers,p.text.lower()
    if not 3<=len(ns)<=6 or ns[0] in fs or any(n.start>=len(p.body) for n in ns):
        return None
    first=ns[0]
    if not _has(r'\b(?:there are|has|have|had|puts?)\b',text[:first.start]):
        return None
    anchor=_unit(p,first)
    if anchor in ('money','hour','year','day','week'):
        return None
    values={anchor:first.value}
    previous=first.end
    for n in ns[1:]:
        tail=_tail(p,n)
        before=text[previous:n.start]
        direct=re.match(r'\s+(?:times )?as many ([a-z]+)(?: as ([a-z]+))?\b',tail)
        if direct:
            left=_singular(direct.group(1))
            right=_singular(direct.group(2)) if direct.group(2) else anchor
            if left in values or right not in values:
                return None
            values[left]=n.value*values[right]
        else:
            left_match=re.search(r'\b(?:the )?number of ([a-z]+) (?:is|was) (?:an? )?$',before)
            if not left_match:
                return None
            left=_singular(left_match.group(1))
            sources=re.match(r'\s+of (?:the )?(?:total|combined number) of (?:the )?([a-z]+) and ([a-z]+)',tail)
            one=re.match(r'\s+of the number of ([a-z]+)',tail)
            if sources:
                keys=[_singular(sources.group(1)),_singular(sources.group(2))]
            elif one:
                keys=[_singular(one.group(1))]
            else:
                return None
            if left in values or any(k not in values for k in keys):
                return None
            values[left]=n.value*sum((values[k] for k in keys),Fraction(0))
        previous=n.end
    def mentioned(t):
        words=_words(t)
        return [k for k in values if k in words]
    chosen=mentioned(p.question)
    if _has(r'\bmore\b.*\bthan\b',p.question):
        left,right=p.question.split('than',1)
        a,b=mentioned(left),mentioned(right)
        if len(a)!=1 or len(b)!=1:
            return None
        return _answer(values[a[0]]-values[b[0]],'Resolve each category from its stated base, then compare the requested categories')
    if not _has(r'\b(?:total|in total|in all|all|altogether|donating)\b',p.question):
        return None
    if len(chosen)==1:
        return _answer(values[chosen[0]],'Resolve the requested category from its stated base')
    return _answer(sum(values.values(),Fraction(0)),'Resolve each category from its stated base and add all categories')


def _two_owner_additions(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(ns)!=5 or len(fs)!=1 or fs!=[ns[-1]]:
        return None
    a,b,c,d,f=ns
    if not re.match(r'\s+[a-z]+ to (?:his|her|their) current\s*$',text[a.end:b.start]):
        return None
    if not re.fullmatch(r'\s+to (?:his|her|their) current\s*',text[c.end:d.start]):
        return None
    owner=re.search(r'\b([a-z]+) adds\s*$',text[b.end:c.start])
    consumer=re.search(r'\b([a-z]+) (?:pops|uses|gives away|loses)\s*$',text[d.end:f.start])
    if not owner or not consumer or owner.group(1)!=consumer.group(1):
        return None
    if not re.match(r'\s+of (?:his|her|their) [a-z]+',_tail(p,f)) or not _has(r'\btotal\b',p.question):
        return None
    return _answer(a.value+b.value+(c.value+d.value)*(1-f.value),'Add each owner starting stock and addition, then apply the loss only to its stated owner')


def _ratio_transfer(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(fs)!=1 or len(ns)<4 or fs!=[ns[-1]]:
        return None
    f=fs[0]
    ratio=re.search(r'\bratio\s+([0-9]+(?:\s*:\s*[0-9]+)+)',text)
    if not ratio:
        return None
    names=re.match(r'([a-z]+(?:\s*,\s*[a-z]+)*(?:,? and [a-z]+)) all share\b',text)
    if not names:
        return None
    owners=re.findall(r'[a-z]+',re.sub(r'\band\b','',names.group(1)))
    parts=[Fraction(x.strip()) for x in ratio.group(1).split(':')]
    if len(owners)!=len(parts) or len(ns)!=len(parts)+2 or any(v<=0 for v in parts):
        return None
    total=ns[0]
    if [n.value for n in ns[1:-1]]!=parts:
        return None
    transfer=re.search(r'\bif ([a-z]+) gives ([a-z]+)\s*$',text[:f.start])
    if not transfer or any(o not in owners for o in transfer.groups()):
        return None
    giver,receiver=transfer.groups()
    if not _has(r'\b'+re.escape(receiver)+r'\b',p.question) or _has(r'\b'+re.escape(giver)+r'\b',p.question):
        return None
    return _answer(total.value*(parts[owners.index(receiver)]+f.value*parts[owners.index(giver)])/sum(parts,Fraction(0)),'Divide the whole by the ratio parts and add the giver fractional share to the receiver')


def _purchase_multiple_then_loss(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(ns)!=3 or len(fs)!=1:
        return None
    base,mult,f=ns
    if fs!=[f] or mult.value<1:
        return None
    if not _has(r'\b(?:bought|buys?|purchased)\s*$',text[base.end:mult.start]):
        return None
    if not re.match(r'\s+times the number of [a-z]+ (?:he|she|they) had\b',_tail(p,mult)):
        return None
    if not _has(_LOSS,text[mult.end:f.start]) or not re.match(r'\s+of what (?:he|she|they) had\b',_tail(p,f)):
        return None
    if not _has(r'\b(?:have now|left|remaining)\b',p.question):
        return None
    return _answer(base.value*(1+mult.value)*(1-f.value),'Add the purchase based on the original stock, then remove the share of the resulting stock')


def _paired_daily_quantities(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(ns)<4 or len(ns)%2 or not fs or not _has(r'\b(?:total|altogether|in all)\b',p.question):
        return None
    pairs=list(zip(ns[::2],ns[1::2]))
    if any(count in fs for count,rate in pairs):
        return None
    units={_unit(p,rate) for count,rate in pairs}
    if len(units)!=1:
        return None
    unit=next(iter(units))
    if unit not in _words(p.question) and not _has(r'\bfood\b',p.question):
        return None
    previous=0
    for count,rate in pairs:
        bridge=text[count.end:rate.start]
        if not _has(r'\beach (?:get|gets|eat|eats|receive|receives|need|needs)\s*$',bridge):
            return None
        if _has(r'\b(?:per|times|twice|day|week)\b',text[previous:rate.end]):
            return None
        previous=rate.end
    return _answer(sum((a.value*b.value for a,b in pairs),Fraction(0)),'Multiply each group count by its individual quantity and add the results')


def _nested_category_chain(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(fs)<3 or len(ns)!=len(fs)+1 or ns[1:]!=fs:
        return None
    total=ns[0]
    if _unit(p,total) not in _words(p.question):
        return None
    previous_label=None
    product=total.value
    previous_end=total.end
    for f in fs:
        before=text[previous_end:f.start]
        after=_local(_tail(p,f))
        if not re.match(r'\s+of (?:the [a-z]+|them)\b',after):
            return None
        pred=re.search(r'\b(?:are|play|plays|have|has) (.+)',after)
        if not pred:
            return None
        if previous_label is not None and not previous_label<=_words(before):
            return None
        previous_label=_words(pred.group(1))
        if not previous_label:
            return None
        product*=f.value
        previous_end=f.end+len(_local(_tail(p,f)))
    if not previous_label<=_words(p.question):
        return None
    return _answer(product,'Follow each explicitly nested subset and multiply its fraction by its parent subset')


def _save_after_disjoint_spending(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(fs)<3 or len(ns)!=len(fs)+1 or ns[1:]!=fs or ns[0].kind!='money':
        return None
    if not _has(r'\bsave\b',p.question):
        return None
    last=fs[-1]
    if not re.match(r'\s+of the remaining money\b',_tail(p,last)):
        return None
    if not _has(r'\bsavings account\b',text[fs[-2].end:last.start]):
        return None
    previous=ns[0].end
    for f in fs[:-1]:
        if not re.match(r'\s+of (?:the money|it)\b',_tail(p,f)):
            return None
        if f==fs[0] and not _has(r'\bspent\b',text[previous:f.start]):
            return None
        if _has(_REST,_local(_tail(p,f))):
            return None
        previous=f.end
    return _answer(ns[0].value*(1-sum((f.value for f in fs[:-1]),Fraction(0)))*last.value,'Subtract the separate shares of the original money, then save the stated share of the remainder')


def _partially_full_tanks(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(ns)!=4 or len(fs)!=2:
        return None
    a,b,f,g=ns
    if fs!=[f,g] or _unit(p,a)!=_unit(p,b) or _unit(p,a) not in _words(p.question):
        return None
    if not _has(r'\b(?:fill|fills)\b.*\bboth\b.*\bcompletely\b',text) or not _has(r'\badd\b',p.question):
        return None
    # Match each tank owner's repeated label to its capacity and fill.
    owners=[]
    previous=0
    for capacity in (a,b):
        before=text[previous:capacity.start]
        m=re.search(r'\b([a-z]+) with a gas tank|\b([a-z]+) has a gas tank',before)
        owner=(m.group(1) or m.group(2)) if m else None
        if not owner:
            return None
        owners.append(owner)
        previous=capacity.end
    if owners[0]==owners[1]:
        return None
    previous=b.end
    for owner,fraction in zip(owners,fs):
        if not _has(r"\b"+re.escape(owner)+r"'s tank is\s*$",text[previous:fraction.start]):
            return None
        if not re.match(r'\s+full\b',_tail(p,fraction)):
            return None
        previous=fraction.end
    return _answer(a.value*(1-f.value)+b.value*(1-g.value),'Add the unfilled shares of the two identified tank capacities')


def _weekly_hourly_remainders(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(ns)!=len(fs)+2 or len(fs)<2:
        return None
    rate,hours=ns[:2]
    if ns[2:]!=fs or rate.kind!='money' or _unit(p,hours)!='hour':
        return None
    if not re.match(r'\s+per hour\b',_tail(p,rate)) or not re.match(r'\s+hours? a day for a week\b',_tail(p,hours)):
        return None
    if not _has(_REST,p.question):
        return None
    value=rate.value*hours.value*7
    previous=hours.end
    for i,f in enumerate(fs):
        if not _has(_LOSS,text[previous:f.start]):
            return None
        if i and not re.match(r'\s+of the remaining money\b',_tail(p,f)):
            return None
        value*=1-f.value
        previous=f.end
    return _answer(value,'Hourly pay x hours per day x seven days, followed by each stated fractional expense')


def _purchase_yield(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(ns)!=4 or len(fs)!=1:
        return None
    base,f,per,price=ns
    if fs!=[f] or price.kind!='money' or _unit(p,base)!=_unit(p,per):
        return None
    if not re.match(r'\s+that much [a-z]+',_tail(p,f)) or not _has(r'\bbuys?\b',text[:base.start]):
        return None
    if not _has(r'\buses?\s*$',text[f.end:per.start]) or not _has(r'\beach\b.*\bsells? for\s*$',text[per.end:price.start]):
        return None
    if not _has(r'\bmoney\b',p.question) or per.value<=0:
        return None
    return _answer(base.value*(1+f.value)/per.value*price.value,'Combine the purchased quantities, divide by quantity per sale, and multiply by sale price')


def _geometric_bounces(p,fs):
    from ._fractions_common import _ORDINALS
    ns,text=p.numbers,p.text.lower()
    if len(ns)!=2 or len(fs)!=1:
        return None
    height,f=ns
    if fs!=[f] or not re.match(r'\s+the height from which it fell on each bounce\b',_tail(p,f)):
        return None
    index=re.search(r'\bon the ([a-z]+|[0-9]+(?:st|nd|rd|th)) bounce\b',p.question)
    if not index or not _has(r'\bhow high\b',p.question):
        return None
    ordinal=index.group(1)
    n=_ORDINALS.get(ordinal)
    if n is None and re.fullmatch(r'[0-9]+(?:st|nd|rd|th)',ordinal):
        n=int(re.match(r'[0-9]+',ordinal).group())
    if n is None or not 1<=n<=100:
        return None
    return _answer(height.value*f.value**n,'Multiply the initial height by the bounce fraction once for each bounce')


def _related_category_additions(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(ns)!=4 or len(fs)!=2:
        return None
    base,factor,a,b=ns
    if fs!=[a,b] or not re.match(r'\s+times as many ([a-z]+) as ([a-z]+)',_tail(p,factor)):
        return None
    relation=re.match(r'\s+times as many ([a-z]+) as ([a-z]+)',_tail(p,factor))
    second,first=(_singular(w) for w in relation.groups())
    if first!=_unit(p,base) or first==second:
        return None
    if not re.match(r'\s+as many additional '+re.escape(first)+r's?\b',_tail(p,a)) or not re.match(r'\s+as many additional '+re.escape(second)+r's?\b',_tail(p,b)):
        return None
    if not _has(r'\bbought\b',text[factor.end:a.start]) or not _has(r'\btotal\b',p.question):
        return None
    return _answer(base.value*(1+a.value)+base.value*factor.value*(1+b.value),'Add each purchase to the category whose original quantity it references')


def _shared_group_remainder(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(ns)!=4 or len(fs)!=1:
        return None
    eaters,groups,size,f=ns
    if fs!=[f] or min(eaters.value,groups.value,size.value)<=0:
        return None
    if not _has(r'\beach with\s*$',text[groups.end:size.start]):
        return None
    if not re.match(r'\s+of the [a-z]+ were remaining out of all\b',_tail(p,f)):
        return None
    if not _has(r'\beach ate an equal number\b',text[size.end:f.start]):
        return None
    if not _has(r'\beach\b.*\bate\b',p.question) or _unit(p,size) not in _words(p.question):
        return None
    return _answer(groups.value*size.value*(1-f.value)/eaters.value,'Find all the grouped items, remove the remaining share, and split the consumed items equally')


def _regular_joint_saving(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(ns)!=3 or len(fs)!=1:
        return None
    amount,years,f=ns
    if fs!=[f] or amount.kind!='money' or _unit(p,years)!='year':
        return None
    if not _has(r'\bevery month for\s*$',text[amount.end:years.start]):
        return None
    less=re.match(r'\s+(?:times )?(less|more) money per month\b',_tail(p,f))
    if not less or not _has(r'\b(?:altogether|together|combined)\b',p.question):
        return None
    factor=2-f.value if less.group(1)=='less' else 2+f.value
    return _answer(amount.value*years.value*12*factor,'Convert the years to months and combine the two related monthly savings amounts')


def _weekly_extra_time(p,fs):
    ns,text=p.numbers,p.text.lower()
    if len(ns)!=3 or len(fs)!=1:
        return None
    frequency,hours,f=ns
    if fs!=[f] or not re.match(r'\s+times a week\b',_tail(p,frequency)) or _unit(p,hours)!='hour':
        return None
    if not re.match(r'\s+of (?:his|her|their) ([a-z]+) time\b',_tail(p,f)):
        return None
    if not _has(r'\badditionally\b',text[hours.end:f.start]) or not _has(r'\beach day\b',_tail(p,f)):
        return None
    if not _has(r'\bhours?\b.*\bweek\b',p.question):
        return None
    return _answer(frequency.value*hours.value*(1+f.value),'Add the fractional extra time to each visit, then multiply by weekly visits')

_READERS = (
    _geometric_bounces, _related_category_additions, _shared_group_remainder,
    _regular_joint_saving, _weekly_extra_time, _purchase_multiple_then_loss,
    _paired_daily_quantities, _nested_category_chain,
    _save_after_disjoint_spending, _partially_full_tanks,
    _weekly_hourly_remainders, _purchase_yield, _category_expression_chain,
    _two_owner_additions, _ratio_transfer, _complementary_yields,
    _two_category_departures, _tip_change, _shared_units,
    _indexed_capacities, _monthly_pay_expenses, _gift_cost_savings,
    _referenced_gift_total, _independent_group_losses, _nested_unfinished,
    _changing_fill_rate, _category_ledger, _disjoint_categories,
    _overlapping_shares, _weighted_groups, _complementary_capacity,
    _markup_per_item, _incorrect_difference, _per_instance_removals,
    _stock, _gift_then_share, _inventory_share, _expense_chain, _currency_split,
    _relative_joint_savings, _scaled_trip, _area_work, _introductory_price,
)


def solve(problem):
    if not has_fraction(problem.text) or any(n.kind=='percent' for n in problem.numbers):
        return None
    p=_prepare(problem)
    if p is None:
        return None
    p.numbers = [n for n in p.numbers if not (n.raw.lower() in ('third','fourth') and re.search(r'\bthe\s*$',p.text[:n.start],re.I) and re.match(r'\s+(?:person|adult|child|round|try|tank)\b',_tail(p,n)))]
    fs=_fractions(p)
    if not fs:
        return None
    for reader in _READERS:
        result=reader(p,fs)
        if result is not None:
            return result
    return None
