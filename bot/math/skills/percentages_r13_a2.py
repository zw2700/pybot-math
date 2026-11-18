"""Conservative multi-stage percentage equations.

Each reader binds the base and every additional quantity to a grammatical
role. Percentage shares, changes and fees remain distinct; all arithmetic is
exact. Unsupported bases and extra quantities cause abstention.
"""
import re
from fractions import Fraction

from ..numbers import format_number
from ..problem import Problem
from ._fractions_common import _has, _answer
from ._money_common import _money_number, _phrase, _same, _price_label, _bounds, _singular, _currencies
from .percentages_r04_a6 import _factor as _old_factor, _finish
from .percentages_r02_a3 import _words


def _sentence(p, n):
    a, b = _bounds(p.text, n)
    return p.text[a:min(b, len(p.body))] if n.start < len(p.body) else p.text[a:b]


def _factor(p, n):
    if re.match(r"\s+(?:sales? tax|processing fee|delivery fee|service fee)\b", p.text[n.end:]):
        return 1+n.value
    if _has(r'\b(?:gained|gains|gain)(?: an? (?:additional|further))?\s*$',p.text[:n.start]):
        return 1+n.value
    if _has(r'\b(?:fell|fallen|fall)(?: by)?\s*$',p.text[:n.start]):
        return 1-n.value
    return _old_factor(p, n)


def _prepare(problem):
    # Keep offsets by lowercasing only. Account for explicit grammatical ones.
    text = problem.text.lower()
    ns = []
    for n in problem.numbers:
        before, after = text[:n.start], text[n.end:]
        # Embedded digits label accounts/models; bare ordinals label events.
        suffix=re.match(r'[a-z]+',after)
        units={'g','mg','kg','oz','lb','lbs','ml','l','km','m','cm','mm','ft','in','kwh','kw','w'}
        if n.kind=='number' and suffix and suffix.group() not in units and _has(r'\b(?:my|your|his|her|their)\s*$',before):
            continue
        from ._fractions_common import _ORDINALS
        if n.raw.lower() in _ORDINALS and re.search(r'\bthe\s*$',before) and re.match(r'\s+[a-z]+',after):
            continue
        if n.value==1 and re.search(r'\bprevious\s*$',before):
            continue
        if n.value == 1 and n.kind != 'percent' and (
                re.search(r'\bin\s*$', before) and re.match(r'\s+(?:day|year)\b', after)
                or re.match(r'\s+day\b', after) and (not before.strip() or re.search(r'[.!?]\s*$', before))):
            continue
        ns.append(_money_number(text, n))
    return Problem(text, problem.body, problem.question, ns)


def _price_chain(p, rates, amounts):
    """Successive discounts/taxes with interleaved coupons or final gift credit."""
    if not 2 <= len(rates) <= 4 or not 1 <= len(amounts) <= 4:
        return None
    if _has(r'\b(?:or|either|versus|instead)\b',p.body):
        return None
    if not _has(r'\b(?:pay|paid|price|cost|save|saved|spend|dollars|worth|left|remaining)\b', p.question):
        return None
    money = [a for a in amounts if a.kind == 'money']
    counts = [a for a in amounts if a.kind != 'money']
    # Stated tenure thresholds choose eligibility; they do not count purchases.
    thresholds=[a for a in counts if _has(r'\bat least\s*$',p.text[:a.start]) and _has(r'^\s+years\b',p.text[a.end:])]
    if thresholds and len(thresholds)==len(counts):
        asked=[a for a in thresholds if a.start>=len(p.body)]
        if len(asked)!=1 or any(a.value>asked[0].value for a in thresholds):
            return None
        counts=[]
    # A single "after N years" dates a nonperiodic price change.
    if len(counts)==1 and _has(r'\bafter\s*$',p.text[:counts[0].start]) and _has(r'^\s+years\b',p.text[counts[0].end:]) and not _has(r'\b(?:every|annual|per year|each year|interest)\b',p.body):
        counts=[]
    if not money or len(counts) > 2:
        return None
    if len(counts)==2 and not _has(r'\bfrom each of (?:his|her|the|their)\s*$',p.text[counts[0].end:counts[1].start]):
        return None
    credits = [a for a in money if _has(r'\b(?:coupon|gift cards?|rebate)\b', _sentence(p, a))]
    bases = [a for a in money if a not in credits]
    if len(bases) != 1:
        return None
    base = bases[0]
    factors = [_factor(p, r) for r in rates]
    if _has(r'\b(?:left|remaining)\b',p.question) and _has(r'\b(?:earns?|paycheck|salary)\b',p.body):
        for i,r in enumerate(rates):
            before=p.text[:r.start];after=p.text[r.end:]
            if (_has(r'\bpay\s*$',before) and _has(r'^\s+for taxes\b',after)
                    or _has(r'\bspends?\s*$',before) and _has(r'^\s+of (?:his|her|their) paycheck\b',after)):
                factors[i]=1-r.value
    if any(f is None or f < 0 for f in factors):
        return None
    if counts and not _has(r'\b(?:each|apiece|per)\b', _sentence(p, base)):
        return None
    if len(counts)==1:
        c=counts[0]
        countlabel=re.split(r'[.;!?]|,(?!\d)|\band\b',p.text[c.end:])[0]
        # Purchasing counts must name the priced item (or its rate unit).
        if not _words(countlabel)&_words(_sentence(p,base)):
            return None
        duration=re.match(r'\s+(hours?|days?|weeks?|months?|years?)\b',p.text[c.end:])
        if duration and not _has(r'\b(?:per|each|every|an?|for each) '+re.escape(_singular(duration.group(1)))+r'\b',_sentence(p,base)):
            return None
    count = Fraction(1)
    for c in counts:
        count *= c.value
    value = base.value*count
    gifts = [a for a in credits if _has(r'\bgift cards?\b', _sentence(p, a))]
    events = sorted([(r.start, 'rate', f) for r, f in zip(rates, factors)] +
                    [(a.start, 'credit', a.value) for a in credits if a not in gifts])
    if any(a.start < base.start for a in credits if a not in gifts):
        return None
    for _, kind, v in events:
        value = value*v if kind == 'rate' else value-v
    value -= sum((a.value for a in gifts), Fraction(0))
    if _has(r'\b(?:save|saved|savings)\b', p.question):
        value = base.value*count-value
    return _answer(value, 'Apply each percentage and fixed credit in the stated order')


def _basket(p, rates, amounts):
    """Sum count x unit-price lines; attach item discounts and whole-bill fees."""
    if not 1 <= len(rates) <= 5 or _has(r'\b(?:coupons?|rebate|gift cards?)\b',p.body):
        return None
    prices = [a for a in amounts if a.kind == 'money']
    counts = [a for a in amounts if a.kind != 'money']
    counts = [a for a in counts if not (a.value==1 and re.match(r'\s+[a-z-]+ costs?\b',p.text[a.end:]))]
    if not 2 <= len(prices) <= 6 or len(counts) > len(prices):
        return None
    if not _has(r'\b(?:pay|paid|cost|spend|spent|save|commission|earn|total price|bill)\b', p.question):
        return None
    labels, pairs, used = [], [], set()
    count_words=[]
    for c in counts:
        stop=min([n.start for n in p.numbers if n.start>c.start]+[_bounds(p.text,c)[1]])
        count_words.append(_words(p.text[c.end:stop]))
    common=set.intersection(*count_words) if count_words else set()
    for price in prices:
        label, explicit = _price_label(p, p.numbers, price)
        # Coordinate catalogue entries: "..., a NOUN at PRICE".
        prefix = re.split(r'[,;]|\band\b', p.text[:price.start])[-1]
        m = re.search(r'\b(?:a|an|the)\s+([a-z -]+?)\s+(?:at|for)\s*$', prefix)
        if m and not label:
            label, explicit = _phrase(m.group(1)), True
        matches = [i for i, c in enumerate(counts) if i not in used and label and
                   (_same(label, _phrase(p.text[c.end:])) or
                    label == _phrase(p.text[c.end:]).split(' of ')[0])]
        if not matches and count_words:
            lo=_bounds(p.text,price)[0]
            prior=[n.end for n in p.numbers if lo<=n.start<price.start]
            prefix=p.text[max(prior or [lo]):price.start]
            distinct=[i for i,w in enumerate(count_words) if i not in used and (w-common)&_words(prefix)]
            if len(distinct)==1:
                matches=distinct
        # A contiguous "N $P items" or "N items ... $P each" line.
        if not matches:
            prior = [(i, c) for i, c in enumerate(counts) if i not in used and c.end <= price.start]
            if prior:
                i, c = prior[-1]
                middle = p.text[c.end:price.start]
                if not middle.strip() and re.match(r'\s+[a-z]', p.text[price.end:]):
                    matches = [i]
                    label = _phrase(p.text[price.end:])
                elif not re.search(r'[.!?;]|\band\b', middle) and _has(r'\b(?:each|per|apiece)\b', p.text[price.end:_bounds(p.text, price)[1]]):
                    matches = [i]
                    label = _phrase(middle)
        if not matches:
            lo=_bounds(p.text,price)[0]
            prefix=re.split(r'[,;]|\band\b',p.text[lo:price.start])[-1]
            if not re.search(r'\b(?:a|an)\s+[a-z -]+?\s+(?:at|for|costs?|that costs?)\s*$',prefix):
                return None
            count=Fraction(1)
        elif len(matches)==1:
            i=matches[0]
            used.add(i)
            count=counts[i].value
        else:
            return None
        if not label:
            return None
        labels.append(label)
        pairs.append((price.value*count, price))
    if len(used) != len(counts):
        return None
    original = sum((v for v, _ in pairs), Fraction(0))
    totals = [v for v, _ in pairs]
    whole_factors = []
    for r in rates:
        clause = _sentence(p, r)
        lo,hi=_bounds(p.text,r)
        if not _has(r'\bcommission\b',clause) and sum(lo<=a.start<hi for a in prices)>1:
            hi=min(hi,len(p.body))
            prefix=re.split(r',(?!\d)|\band\b',p.text[lo:r.start])[-1]
            suffix=re.split(r',(?!\d)|\band\b',p.text[r.end:hi])[0]
            clause=prefix+r.raw.lower()+suffix
        # Commission is a share of gross, not a markup.
        if _has(r'\bcommission\b', clause):
            if not _has(r'\bcommission\b', p.question):
                return None
            whole_factors.append(r.value)
            continue
        if _has(r'\b(?:sales? tax|delivery fee|processing fee|service fee|tax)\b', clause):
            whole_factors.append(1-r.value if _has(r'\bearn\w*\b',p.question) and _has(r'\b(?:earnings|income)\b',clause) else 1+r.value)
            continue
        f = _factor(p, r)
        if f is None:
            return None
        hits = [i for i, label in enumerate(labels) if _words(label) & _words(clause)]
        if len(hits) == 1:
            totals[hits[0]] *= f
        elif not hits and _has(r'\b(?:entire|all|total|everything|store|checkout|purchase)\b', clause):
            whole_factors.append(f)
        else:
            return None
    value = sum(totals, Fraction(0))
    for f in whole_factors:
        value *= f
    if _has(r'\b(?:save|savings)\b', p.question):
        value = original-value
    return _answer(value, 'Sum the item counts times their adjusted prices, then apply the bill-wide percentage')


def _loan(p, rates, amounts):
    if len(rates) != 1 or len(amounts) != 3:
        return None
    if not _has(r'\b(?:monthly|each month)\b', p.question) or not _has(r'\b(?:payment|pay)\w*\b', p.question):
        return None
    r = rates[0]
    money = [a for a in amounts if a.kind == 'money']
    periods = [a for a in amounts if _has(r'^\s+equal monthly payments\b', p.text[a.end:])]
    down = [a for a in money if _has(r'\bdown payment[^,.;]*$', p.text[:a.start])]
    if len(money) != 2 or len(periods) != 1 or len(down) != 1 or periods[0].value <= 0:
        return None
    if not _has(r'\binterest\b', _sentence(p, r)) or not _has(r"\b(?:month's payment|monthly payment)\b", p.text[r.end:]):
        return None
    price = next(a for a in money if a != down[0])
    return _answer((price.value-down[0].value)/periods[0].value*(1+r.value),
                   'Subtract the down payment, divide into monthly payments, then add the payment interest')


def _sale_stock(p, rates, amounts):
    """Sold fraction x discounted unit price, minus an explicit debt."""
    if len(rates) not in (1, 2) or len(amounts) not in (2, 3):
        return None
    if not _has(r'\b(?:left|remaining|sales|revenue|profit|keep)\b', p.question):
        return None
    money = [a for a in amounts if a.kind == 'money']
    counts = [a for a in amounts if a.kind != 'money']
    if len(counts) != 1 or not money:
        return None
    debts = [a for a in money if _has(r'\b(?:owed|owes?|debt|creditors)\b', _sentence(p, a))]
    prices = [a for a in money if a not in debts]
    if len(prices) != 1 or len(debts) > 1:
        return None
    if not _has(r'\b(?:retail|each|apiece|all cost)\b', _sentence(p, prices[0])):
        return None
    factor = Fraction(1)
    for r in rates:
        clause = _sentence(p, r)
        f = _factor(p, r)
        if f is not None:
            factor *= f
        elif _has(r'\b(?:returns?|returning|returned)\b', clause):
            factor *= 1-r.value
        elif _has(r'\b(?:sell|sells|sold)\b', clause) and _has(r'^\s+of\b', p.text[r.end:]):
            factor *= r.value
        else:
            return None
    return _answer(counts[0].value*prices[0].value*factor-sum((d.value for d in debts), Fraction(0)),
                   'Revenue from the sold share at its adjusted price, less debt')


def _allocation(p, rates, amounts):
    """Disjoint income shares may mix fractions and percents."""
    shares = sorted(rates+[a for a in amounts if 0<a.value<1], key=lambda n:n.start)
    bases = [a for a in amounts if a not in shares]
    if len(bases) != 1 or not 2 <= len(shares) <= 5:
        return None
    if not _has(r'\b(?:rest|left|remaining)\b', p.text) or not _has(r'\b(?:save|saves|left|remaining)\b', p.question):
        return None
    if bases[0].kind != 'money' or not _has(r'\b(?:earns?|income|salary|paid)\b', _sentence(p, bases[0])):
        return None
    if any(_factor(p, r) is not None for r in rates):
        return None
    if _has(r'\b(?:remaining|left|rest|those)\b', p.text[shares[0].end:shares[-1].start]):
        return None
    f = 1-sum((s.value for s in shares), Fraction(0))
    return _answer(bases[0].value*f, 'Income minus the disjoint fraction and percentage expenses') if f >= 0 else None


def _group_remainders(p, rates, amounts):
    """Group count x contents, followed by sequential shares of the remainder."""
    fractions = [a for a in amounts if 0<a.value<1]
    shares = sorted(rates+fractions,key=lambda n:n.start)
    counts = [a for a in amounts if a not in fractions]
    if len(counts) != 2 or not 2 <= len(shares) <= 4:
        return None
    if not _has(r'\b(?:left|remaining|remain)\b', p.question):
        return None
    a,b = counts
    unit = re.match(r'\s+([a-z]+)', p.text[a.end:])
    before = p.text[a.end:b.start]
    if not unit or not _has(r'\beach '+re.escape(_singular(unit.group(1)))+r'\b',before):
        return None
    if not _has(r'\b(?:contained?|contains?|holds?|has|have)\b',before) or b.end>shares[0].start:
        return None
    value = a.value*b.value
    for i,s in enumerate(shares):
        if i and not _has(r"^\s+of (?:what(?:'s| is) |the |his |her |their )?(?:left|remaining|rest)\b",p.text[s.end:]):
            return None
        value *= 1-s.value
    return _answer(value, 'Count the contents, then remove each stated share of the remainder')


def _equal_capacity(p, rates, amounts):
    amounts = [a for a in amounts if not (a.value == 2 and re.match(r'\s+[a-z]+\b',p.text[a.end:]) and (a.start >= len(p.body) or _has(r'\bif the\s*$',p.text[:a.start])))]
    if len(rates) != 1 or len(amounts) != 2:
        return None
    if not _has(r'\bsame capacity\b',p.body) or not _has(r'\b(?:fill|needed)\b',p.question):
        return None
    a,b=amounts; r=rates[0]
    if not a.start<b.start<r.start or not 0<r.value<=1:
        return None
    units=[re.match(r'\s+([a-z]+)',p.text[n.end:]) for n in amounts]
    if not all(units) or units[0].group(1)!=units[1].group(1):
        return None
    if not _has(r'\b(?:second|latter)\b',_sentence(p,r)) or not _has(r'^\s+(?:filled|full)\b',p.text[r.end:]):
        return None
    return _answer(2*b.value/r.value-a.value-b.value,'Recover the common capacity and subtract the contents of both containers')


def _nested_difference(p, rates, amounts):
    if len(rates)!=2 or len(amounts)!=1 or not _has(r'\bhow many more\b',p.question):
        return None
    winners=[r for r in rates if _has(r'\b(?:winner|winning)\b',_sentence(p,r))]
    participation=[r for r in rates if _has(r'\b(?:voted|participated)\b',_sentence(p,r))]
    if len(winners)!=1 or len(participation)!=1 or winners==participation:
        return None
    if not _has(r'\b(?:loser|rest|remaining)\b',p.body):
        return None
    return _answer(amounts[0].value*participation[0].value*(2*winners[0].value-1),
                   'Count participating voters, then subtract the complementary vote share from the winning share')


def _complement_nested(p, rates, amounts):
    """A second category drawn from those without the first category."""
    if len(rates)!=2 or len(amounts)!=1:
        return None
    a=amounts[0]; r,s=rates
    if a.start>r.start or not _has(r'\b(?:no|without any|not have any)\b',p.question):
        return None
    base=re.match(r'\s+of (.+?)\bwithout\b([^,.;]+)',p.text[s.end:])
    first=re.match(r'\s+of .+?\b(?:have|has|are|is|want|wants)\s+(.+?)(?:[,.;]|$)',p.text[r.end:s.start])
    if not base or not first or not _words(first.group(1))&_words(base.group(2)):
        return None
    if not _has(r'\bremaining\b',p.text[s.end:]):
        return None
    return _answer(a.value*(1-r.value)*(1-s.value),'Exclude the first category, then the second share of its complement')


def _comparison_graph(p, rates, amounts):
    """Translate explicit percentage comparisons into the shared affine graph."""
    if not 2<=len(getattr(p,'entities',[]))<=3 or any(0<a.value<1 for a in amounts):
        return None
    from .percentages_r04_a6 import _comparison
    text=re.sub(r'\bcontributed\b',lambda m:'has'+' '*(len(m.group())-3),p.text)
    translated=Problem(text,p.body,p.question,p.numbers)
    translated.entities=p.entities
    return _comparison(translated, rates, amounts)


def _raised_count_cost(p, rates, amounts):
    if len(rates)!=1 or len(amounts)!=3:
        return None
    money=[a for a in amounts if a.kind=='money']
    counts=[a for a in amounts if a.kind!='money']
    if len(money)!=2 or len(counts)!=1 or not _has(r'\b(?:cost|pay|spend)\b',p.question):
        return None
    r=rates[0];c=counts[0]
    if not _has(r'^\s+more than that\b',p.text[r.end:]):
        return None
    owner=re.search(r'\b(?:while|but|and)\s+(.+?)\s+wants\s*$',re.split(r'[.;!?]',p.text[:r.start])[-1])
    if not owner or not _words(owner.group(1))&_words(p.question):
        return None
    unit=re.match(r'\s+([a-z]+)',p.text[c.end:])
    if not unit:
        return None
    per=[a for a in money if _has(r'\b(?:per|each) '+re.escape(_singular(unit.group(1)))+r'\b',_sentence(p,a))]
    if len(per)!=1:
        return None
    fixed=next(a for a in money if a!=per[0])
    if not _has(r'\bcost\b',_sentence(p,fixed)):
        return None
    return _answer(fixed.value+per[0].value*c.value*(1+r.value),
                   'Fixed charge plus the increased item count times its unit cost')


def _multiple_collection(p, rates, amounts):
    if len(rates)!=1 or len(amounts)!=2 or not _has(r'\b(?:after|total|all)\b',p.question):
        return None
    base,scale=amounts;r=rates[0]
    if not base.start<scale.start<r.start or not _has(r'^\s+times as many\b',p.text[scale.end:]):
        return None
    if not _has(r'\b(?:buy|buys|add|adds|purchase)\b',_sentence(p,r)) or not _has(r'^\s+of all\b',p.text[r.end:]):
        return None
    return _answer(base.value*(1+scale.value)*(1+r.value),
                   'Combine the original and multiple-sized category, then add the stated share')


def _parallel_binary(p, rates, amounts):
    if len(rates)!=2:
        return None
    shares=[a for a in amounts if 0<a.value<1]
    bases=[a for a in amounts if a not in shares and not (a.value==1 and _has(r'\beach [a-z]+ gets\s*$',p.text[:a.start]))]
    if len(bases)!=1 or len(shares) not in (1,2):
        return None
    if len(shares)==2 and not (shares[0].value+shares[1].value==1 and _has(r'\b(?:other|remaining)\b',p.text[shares[0].end:shares[1].start])):
        return None
    f=shares[0];a=bases[0]
    if not a.start<f.start<rates[0].start or not _has(r'\b(?:other|remaining)\b',p.text[f.end:rates[0].start]):
        return None
    from .percentages_r02_a3 import _labels
    label=_labels(p.text,f)
    firstbase=re.match(r'\s+of (.+?)\b(?:have|has|are|is|want|wants)\b',p.text[rates[0].end:])
    secondbase=re.match(r'\s+of (.+?)\b(?:have|has|are|is|want|wants)\b',p.text[rates[1].end:])
    if not firstbase or not secondbase or not _words(label)&_words(firstbase.group(1)):
        return None
    if _words(firstbase.group(1))&_words(secondbase.group(1)):
        return None
    if len(shares)==2 and not _words(_labels(p.text,shares[1]))&_words(secondbase.group(1)):
        return None
    predicates=[]
    for r in rates:
        tail=re.split(r'[.;!?]',p.text[r.end:])[0]
        pred=re.split(r'\b(?:have|has|are|is|want|wants)\b',tail,maxsplit=1)
        if len(pred)!=2:
            return None
        predicates.append(_words(pred[1]))
    if not predicates[0]&predicates[1]&_words(p.question):
        return None
    return _answer(a.value*(f.value*rates[0].value+(1-f.value)*rates[1].value),
                   'Sum the selected shares of the two complementary groups')


def _retained_branch(p, rates, amounts):
    if len(rates)!=2 or len(amounts)!=1 or not _has(r'\b(?:left|remaining)\b',p.question):
        return None
    r,s=rates
    if not _has(r'\bkeeps?\s*$',p.text[:r.start]) or not _has(r'\brest\b',p.text[r.end:s.start]):
        return None
    if not _has(r'\bof those\b',p.text[r.end:s.start]) or not _has(r'\bremoves? everyone who did not\b',p.text[s.end:]):
        return None
    return _answer(amounts[0].value*(r.value+(1-r.value)*s.value),
                   'Keep the initial share plus the retained share of the rest')


def _contribution_match(p, rates, amounts):
    if len(rates)!=1 or not _has(r'\bmatch\b',p.body) or not _has(r'\b(?:contributed|contributions|total)\b',p.question):
        return None
    money=[a for a in amounts if a.kind=='money']
    counts=[a for a in amounts if a.kind!='money']
    # Plan labels such as 401k are already excluded by the core number parser.
    counts=[a for a in counts if not (a.value==1 and _has(r'^\s+year\b',p.text[a.end:]) and a.start>=len(p.body))]
    if len(money)!=1 or len(counts)!=1:
        return None
    a,c=money[0],counts[0]
    unit=re.match(r'\s+([a-z]+) per year\b',p.text[c.end:])
    if not unit or not _has(r'\b(?:every|each) '+re.escape(_singular(unit.group(1)))+r'\b',_sentence(p,a)):
        return None
    return _answer(a.value*c.value*(1+rates[0].value),'Annual contributions plus the matching percentage')


def _calendar_saving(p, rates, amounts):
    if len(rates)!=1 or len(amounts)!=2 or not _has(r'\bsave\b',p.question):
        return None
    a,b=amounts;r=rates[0]
    unit=re.match(r'\s+([a-z]+) of [a-z]+ per ([a-z]+)\b',p.text[a.end:])
    frequency=re.match(r'\s+times per day\b',p.text[b.end:])
    if not unit or not frequency or not _has(r'^\s+less [a-z]+ per '+re.escape(unit.group(2))+r'\b',p.text[r.end:]):
        return None
    months={'january':31,'march':31,'april':30,'may':31,'june':30,'july':31,
            'august':31,'september':30,'october':31,'november':30,'december':31}
    found=[days for month,days in months.items() if _has(r'\bin '+month+r'\b',p.question)]
    if len(found)!=1:
        return None
    return _answer(a.value*b.value*r.value*found[0],'Daily usage times the saved share times days in the named month')


def _geometric_production(p, rates, amounts):
    if len(rates)!=1 or len(amounts)!=4 or not _has(r'\b(?:produce|produces|production)\b',p.question):
        return None
    rate=next((a for a in amounts if _has(r'^\s+[a-z]+ per year\b',p.text[a.end:])),None)
    duration=next((a for a in amounts if _has(r'^\s+years?\b',p.text[a.end:]) and a.start>=len(p.body)),None)
    if rate is None or duration is None:
        return None
    sides=[a for a in amounts if a not in (rate,duration)]
    x,y=sides
    ux=re.match(r'\s+([a-z]+) by\s*$',p.text[x.end:y.start])
    uy=re.match(r'\s+([a-z]+)',p.text[y.end:])
    if not ux or not uy or ux.group(1)!=uy.group(1):
        return None
    f=_factor(p,rates[0])
    if f is None:
        return None
    return _answer(rate.value*x.value*y.value*duration.value*f,
                   'Annual output times the rectangular group count times years, with the percentage change')


def _repeated_change(p, rates, amounts):
    """A stated number of identical successive percentage operations."""
    if len(rates)!=1 or len(amounts)!=2:
        return None
    r=rates[0]
    rounds=[a for a in amounts if _has(r'^\s+rounds? of\b',p.text[a.end:])]
    if len(rounds)==1:
        n=rounds[0];base=next(a for a in amounts if a!=n)
        if not _has(r'^\s+of the remaining\b',p.text[r.end:]) or not _has(r'\bfor each round\b',p.body):
            return None
        if not _has(r'\blaid off\b',p.text[r.end:]) or not _has(r'\blaid off\b',p.question):
            return None
        exponent=n.value
        if exponent.denominator!=1 or not 1<=exponent<=100:
            return None
        value=base.value*(1-(1-r.value)**int(exponent))
        return _answer(value,'Subtract the final balance after repeated percentage removals from the initial count')
    from ._fractions_common import _ORDINALS
    a,b=amounts
    if not _has(r'^\s+fewer\b',p.text[r.end:]) or not _has(r'\bin each next\b',p.body):
        return None
    if not _has(r'\bprevious one\b',p.body):
        return None
    m=re.search(r'\bthe ('+'|'.join(_ORDINALS)+r') ([a-z]+)\b',p.question)
    label=re.match(r'\s+([a-z]+)',p.text[a.end:])
    if not m or not label or _singular(m.group(2))!=_singular(label.group(1)) or _ORDINALS[m.group(1)]>a.value:
        return None
    return _answer(b.value*(1-r.value)**(_ORDINALS[m.group(1)]-1),
                   'Apply the percentage decrease once for each transition from the first group')


def _income_commission_allocation(p, rates, amounts):
    if len(rates)!=2 or len(amounts) not in (2,3):
        return None
    commissions=[r for r in rates if _has(r'\bcommission\b',_sentence(p,r))]
    if len(commissions)!=1:
        return None
    commission=commissions[0];allocation=next(r for r in rates if r!=commission)
    if not _has(r'^\s+of (?:her |his |their )?total (?:monthly )?earnings\b',p.text[allocation.end:]):
        return None
    money=[a for a in amounts if a.kind=='money']
    if len(money)!=2:
        return None
    salaries=[a for a in money if _has(r'\b(?:basic salary|base pay)\b',_sentence(p,a))]
    if len(salaries)!=1:
        return None
    salary=salaries[0];sales=next(a for a in money if a!=salary)
    if not _has(r'\b(?:sold|sales)\b',_sentence(p,sales)):
        return None
    wage=salary.value
    counts=[a for a in amounts if a.kind!='money']
    if counts:
        h=counts[0]
        if not _has(r'^\s+per hour\b',p.text[salary.end:]) or not _has(r'^\s+hours\b',p.text[h.end:]):
            return None
        wage*=h.value
    from .percentages_r04_a6 import _label, _choice
    label=_label(p,allocation)
    choice=_choice(label,p)
    if _has(r'\brest\b',p.text[allocation.end:]) and not _words(label)&_words(p.question):
        choice=-1
    if not choice:
        return None
    return _answer((wage+sales.value*commission.value)*(allocation.value if choice>0 else 1-allocation.value),
                   'Salary plus sales commission, times the requested allocation share')


def _parallel_money_shares(p, rates, amounts):
    if not 2<=len(rates)==len(amounts)<=5 or any(a.kind!='money' for a in amounts):
        return None
    if not _has(r'\b(?:total|altogether|in all)\b',p.question):
        return None
    from .percentages_r04_a6 import _choice, _label
    for a,r in zip(amounts,rates):
        if not a.start<r.start or _sentence(p,a)!=_sentence(p,r) or not _has(r'\bdonat\w*\b',_sentence(p,r)) or not _has(r'\bdonate\b',p.question):
            return None
        if not _has(r'^\s+of (?:the )?(?:proceeds|earnings|income)\b',p.text[r.end:]):
            return None
    return _answer(sum((a.value*r.value for a,r in zip(amounts,rates)),Fraction(0)),
                   'Add the percentage contributions from each separate amount')


def _fraction_budget(p, rates, amounts):
    if len(rates)!=1 or len(amounts)!=2 or not _has(r'\b(?:remain|left)\w*\b',p.question):
        return None
    money=[a for a in amounts if a.kind=='money']
    fractions=[a for a in amounts if 0<a.value<1]
    if len(money)!=1 or len(fractions)!=1:
        return None
    a=money[0];f=fractions[0];r=rates[0]
    if not _has(r'\bbudget\b',_sentence(p,a)) or not _has(r'^\s+more expensive than\b',p.text[r.end:]):
        return None
    if not _has(r'^\s+the new price\b',p.text[f.end:]):
        return None
    return _answer(a.value-a.value*(1+r.value)*f.value,'Budget less the selected fraction of the increased price')


def _updated_win_percentage(p, rates, amounts):
    if len(rates)!=1 or len(amounts)!=3 or not _has(r'\b(?:new|overall) win percentage\b',p.question):
        return None
    a,b,c=amounts;r=rates[0]
    if not a.start<r.start<b.start<c.start or not _has(r'\bwon\s*$',p.text[:r.start]):
        return None
    unit=re.match(r'\s+([a-z]+)',p.text[a.end:])
    extra=re.match(r'\s+more ([a-z]+)',p.text[b.end:])
    if not unit or not extra or unit.group(1)!=extra.group(1) or not _has(r'\bloses?\s*$',p.text[:c.start]):
        return None
    if c.value>b.value or not a.value+b.value:
        return None
    return _answer(100*(a.value*r.value+b.value-c.value)/(a.value+b.value),
                   'Previous wins plus new wins, divided by the combined number of games, times 100')


def _inverse_remainder(p, rates, amounts):
    """Recover a starting budget after sequential shares and fixed spending."""
    if not 2<=len(rates)<=4 or len(amounts)!=2 or any(a.kind!='money' for a in amounts):
        return None
    if not _has(r'\b(?:initially|originally|start|beginning)\b',p.question):
        return None
    if not all(_has(r'^\s+of (?:the )?(?:remainder|remaining)',p.text[r.end:]) for r in rates[1:]):
        return None
    spent=[a for a in amounts if _has(r'\b(?:spending|spent|spends)\s*$',p.text[:a.start])]
    left=[a for a in amounts if _has(r'\b(?:left with|has left|remaining)\s*$',p.text[:a.start])]
    if len(spent)!=1 or len(left)!=1 or spent==left or any(a.start<rates[-1].end for a in amounts):
        return None
    factor=Fraction(1)
    for r in rates:
        factor*=1-r.value
    if not factor:
        return None
    return _answer((spent[0].value+left[0].value)/factor,
                   'Add back the fixed expense, then divide by each remaining percentage share')


def _geometric_levels(p, rates, amounts):
    if len(rates)!=1 or len(amounts)!=2:
        return None
    r=rates[0]
    if not _has(r'^\s+as many\b',p.text[r.end:]) or not _has(r'\bprevious level\b',p.body):
        return None
    levels=[a for a in amounts if _has(r'^\s+levels\b',p.text[a.end:])]
    if len(levels)!=1:
        return None
    n=levels[0];top=next(a for a in amounts if a!=n)
    if not _has(r'\btop level has\s*$',p.text[:top.start]) or not _has(r'\btotal\b',p.question):
        return None
    if n.value.denominator!=1 or not 1<=n.value<=100:
        return None
    return _answer(sum((top.value/r.value**i for i in range(int(n.value))),Fraction(0)),
                   'Sum the levels, undoing one percentage factor for each level below the top')


def _trade_in(p, rates, amounts):
    if not 1<=len(rates)<=2 or not 2<=len(amounts)<=4 or any(a.kind!='money' for a in amounts):
        return None
    if not _has(r"\b(?:out of (?:his|her|their) pocket|out-of-pocket)\b",p.question):
        return None
    sold=[a for a in amounts if _has(r'\b(?:old|worth)\b',_sentence(p,a)) and _has(r'\b(?:sold|got|trade)\b',p.body)]
    if len(sold)!=1:
        return None
    old=sold[0]
    sales=[r for r in rates if _sentence(p,r)==_sentence(p,old)]
    if len(sales)!=1:
        return None
    sale=sales[0]
    f=_factor(p,sale)
    if f is None:
        if not _has(r'^\s+of the value\b',p.text[sale.end:]):
            return None
        f=sale.value
    value=Fraction(0)
    for a in amounts:
        if a==old:
            continue
        if not _has(r'\bcosts?\b',_sentence(p,a)):
            return None
        rs=[r for r in rates if r!=sale and _sentence(p,r)==_sentence(p,a)]
        if len(rs)>1:
            return None
        af=_factor(p,rs[0]) if rs else Fraction(1)
        if af is None:
            return None
        value+=a.value*af
    if any(r!=sale and not any(_sentence(p,r)==_sentence(p,a) for a in amounts if a!=old) for r in rates):
        return None
    return _answer(value-old.value*f,'New purchase costs less the proceeds of the old item')


def _partial_discount(p, rates, amounts):
    amounts=list(amounts)
    fractions=[a for a in amounts if a.kind!='money' and 0<a.value<1]
    if len(fractions)==2 and fractions[0].value+fractions[1].value==1 and _has(r'\bother\b',p.text[fractions[0].end:fractions[1].start]):
        amounts.remove(fractions[1])
    if len(rates)!=1 or len(amounts)!=3 or not _has(r'\b(?:cost|pay|spend)\b',p.question):
        return None
    shares=[a for a in amounts if 0<a.value<1 and a.kind!='money']
    counts=[a for a in amounts if a.kind!='money' and a not in shares]
    money=[a for a in amounts if a.kind=='money']
    if len(shares)!=1 or len(counts)!=1 or len(money)!=1:
        return None
    s=shares[0];r=rates[0]
    if not _has(r'\bfull price\b',p.body) or not _has(r'^\s+off\b',p.text[r.end:]):
        return None
    if not counts[0].start<s.start<r.start<money[0].start:
        return None
    return _answer(counts[0].value*money[0].value*(1-s.value*r.value),
                   'Pay the discounted price for the selected share and full price for the rest')


def _inventory_profit(p, rates, amounts):
    if len(rates)!=1 or len(amounts)!=3 or not _has(r'\b(?:profit|compared to before)\b',p.question):
        return None
    money=[a for a in amounts if a.kind=='money']
    counts=[a for a in amounts if a.kind!='money']
    if len(money)!=2 or len(counts)!=1:
        return None
    buys=[a for a in money if _has(r'\b(?:bought|buys?|paid)[^.;]*$',re.split(r'\band\b',p.text[:a.start])[-1])]
    sells=[a for a in money if _has(r'\b(?:sells?|sold)[^.;]*$',re.split(r'\band\b',p.text[:a.start])[-1])]
    if len(buys)!=1 or len(sells)!=1 or buys==sells:
        return None
    if not all(_has(r'^\s+each\b',p.text[a.end:]) for a in money):
        return None
    if not _has(r'\bsell\s*$',p.text[:rates[0].start]) or not _has(r'^\s+of\b',p.text[rates[0].end:]):
        return None
    return _answer(counts[0].value*(rates[0].value*sells[0].value-buys[0].value),
                   'Proceeds from the sold share minus the cost of the entire original stock')


def _paired_task_time(p, rates, amounts):
    if len(rates)!=1 or len(amounts)!=2 or not _has(r'\b(?:how long|total time)\b',p.question):
        return None
    r=rates[0]
    if not _has(r'^\s+less time\b',p.text[r.end:]):
        return None
    durations=[a for a in amounts if _has(r'^\s+(?:hours?|minutes?)\b',p.text[a.end:])]
    if len(durations)!=1:
        return None
    duration=durations[0];count=next(a for a in amounts if a!=duration)
    unit=re.match(r'\s+([a-z]+)',p.text[count.end:])
    if not unit or not _has(r'\beach '+re.escape(_singular(unit.group(1)))+r'\b',_sentence(p,duration)):
        return None
    if not _has(r'\band\b',p.text[:count.start]) or not _has(r'\btime to\b',p.text[r.end:]):
        return None
    return _answer(count.value*duration.value*(2-r.value),'Number of items times the original task time plus the reduced second task time')


def _annual_purchase(p, rates, amounts):
    if len(rates)!=1 or len(amounts)!=2 or not _has(r'\b(?:entire year|whole year)\b',p.body):
        return None
    money=[a for a in amounts if a.kind=='money'];counts=[a for a in amounts if a.kind!='money']
    if len(money)!=1 or len(counts)!=1 or not _has(r'\b(?:cost|pay|spend)\b',p.question):
        return None
    c=counts[0];a=money[0]
    m=re.match(r'\s+([a-z]+)(?: of [a-z]+)? a month\b',p.text[c.end:])
    if not m or not _has(r'\beach '+re.escape(_singular(m.group(1)))+r'\b',_sentence(p,a)):
        return None
    f=_factor(p,rates[0])
    return _answer(c.value*12*a.value*f,'Monthly item count times twelve times the discounted item price') if f is not None else None


def _annuity(p, rates, amounts):
    if len(rates)!=1 or len(amounts)!=3 or not _has(r'\binterest every year\b',p.body):
        return None
    years=[a for a in amounts if _has(r'^\s+years\b',p.text[a.end:]) and a.start>=len(p.body)]
    deposits=[a for a in amounts if _has(r'^\s+each year\b',p.text[a.end:])]
    if len(years)!=1 or len(deposits)!=1:
        return None
    n=years[0];d=deposits[0];initial=next(a for a in amounts if a not in (n,d))
    if initial.kind!='money' or n.value.denominator!=1 or not 1<=n.value<=100:
        return None
    if not _has(r'\bputs\b',_sentence(p,initial)):
        return None
    value=initial.value
    for _ in range(int(n.value)):
        value=value*(1+rates[0].value)+d.value
    return _answer(value,'Apply annual interest and then add the annual deposit each year')


def _disjoint_nonresponse(p, rates, amounts):
    if len(rates)!=2 or len(amounts)!=1 or not _has(r'\b(?:not respond|no response)\b',p.question):
        return None
    clauses=[_sentence(p,r) for r in rates]
    if not all(_has(r'\b(?:rsvp|respond|response)\b',c) for c in clauses):
        return None
    if not _has(r'\byes\b',p.body) or not _has(r'\bno\b',p.body) or sum((r.value for r in rates),Fraction(0))>1:
        return None
    return _answer(amounts[0].value*(1-rates[0].value-rates[1].value),
                   'Exclude the yes and no response shares from the invited total')


def _attendance_remainder(p, rates, amounts):
    if len(rates)!=2 or len(amounts)!=1:
        return None
    r,s=rates
    if not _has(r"^\s+(?:didn't|did not) show up\b",p.text[r.end:]):
        return None
    if not _has(r'^\s+of the people who show up\b',p.text[s.end:]):
        return None
    rest=re.search(r'\bthe rest\b([^.;!?]+)',p.text[s.end:len(p.body)])
    if not rest or not _words(rest.group(1))&_words(p.question):
        return None
    return _answer(amounts[0].value*(1-r.value)*(1-s.value),
                   'Attending share times the complementary choice share')


def _progress_rate(p, rates, amounts):
    if len(rates)!=1 or len(amounts)!=3 or not _has(r'\b(?:finishes|finish|complete)\b',p.question):
        return None
    r=rates[0]
    if not _has(r'^\s+done\b',p.text[r.end:]):
        return None
    daily=[a for a in amounts if _has(r'^\s+hours a day\b',p.text[a.end:])]
    durations=[a for a in amounts if _has(r'^\s+(?:weeks|days)\b',p.text[a.end:])]
    if len(daily)!=2 or len(durations)!=1:
        return None
    old,new=daily;duration=durations[0]
    if not old.start<duration.start<r.start<new.start or not _has(r'\bincreased\b',_sentence(p,new)):
        return None
    if old.value<=0 or new.value<=0:
        return None
    days=duration.value*(7 if _has(r'^\s+weeks\b',p.text[duration.end:]) else 1)
    return _answer(old.value*days*(1-r.value)/r.value/new.value,
                   'Recover the unfinished hours from the completed share and divide by the new daily rate')


def _replacement_count(p, rates, amounts):
    if len(rates)!=1 or len(amounts)!=2 or not _has(r'\btotal number\b',p.question):
        return None
    r=rates[0]
    multiples=[a for a in amounts if _has(r'^\s+new [a-z]+\b',p.text[a.end:])]
    if len(multiples)!=1:
        return None
    m=multiples[0];base=next(a for a in amounts if a!=m)
    prefix=_sentence(p,m)
    if not _has(r'\bfor every\b',prefix) or not _has(r'\b(?:plants?|replaces?|adds?)\s*$',p.text[:m.start]):
        return None
    if not _has(r'\b(?:cut|removed|lost)\s*$',p.text[:r.start]) or not _has(r'^\s+of them\b',p.text[r.end:]):
        return None
    unit=re.match(r'\s+(?:new )?([a-z]+)',p.text[m.end:])
    known=re.match(r'\s+([a-z]+)',p.text[base.end:])
    if not unit or not known or unit.group(1)!=known.group(1):
        return None
    return _answer(base.value*(1-r.value+m.value*r.value),
                   'Remove the stated percentage and add its counted replacements')


def _discount_threshold(p, rates, amounts):
    if len(rates)!=1 or len(amounts)!=3 or not _has(r'\b(?:cost|pay|price)\b',p.question):
        return None
    money=[a for a in amounts if a.kind=='money'];counts=[a for a in amounts if a.kind!='money']
    if len(money)!=2 or len(counts)!=1:
        return None
    thresholds=[a for a in money if _has(r'\bover\s*$',p.text[:a.start])]
    if len(thresholds)!=1:
        return None
    t=thresholds[0];price=next(a for a in money if a!=t);c=counts[0]
    if not _has(r'\bdiscount for the amount\b',p.body) or not _has(r'\beach cost\s*$',p.text[:price.start]):
        return None
    total=c.value*price.value
    return _answer(total-max(Fraction(0),total-t.value)*rates[0].value,
                   'Subtract the discount on only the portion above the threshold')


def _spending_percentage(p, rates, amounts):
    if len(rates)!=1 or len(amounts)!=3 or not _has(r'^what percentage of (?:his|her|their) money\b',p.question):
        return None
    money=[a for a in amounts if a.kind=='money'];counts=[a for a in amounts if a.kind!='money']
    if len(money)!=2 or len(counts)!=1:
        return None
    prices=[a for a in money if _has(r'^\s+each\b',p.text[a.end:])]
    if len(prices)!=1:
        return None
    price=prices[0];budget=next(a for a in money if a!=price)
    if not _has(r'\bhas\s*$',p.text[:budget.start]) or budget.value<=0:
        return None
    r=rates[0]
    if not _has(r'^\s+of them\b',p.text[r.end:]) or not _has(r'\b(?:give|buy)\b',_sentence(p,r)):
        return None
    return _answer(100*counts[0].value*r.value*price.value/budget.value,
                   'Cost of the selected share divided by the budget, times 100')


def _sequential_remainder(p, rates, amounts):
    """A stock ledger with fixed removals and shares of its current remainder."""
    shares=sorted(rates+[a for a in amounts if 0<a.value<1 and a.kind!='money'],key=lambda n:n.start)
    counts=[a for a in amounts if a not in shares]
    if not counts or not 2<=len(shares)<=4 or not 1<=len(counts)<=3:
        return None
    if not _has(r"\b(?:left|remaining|empty|kept|not eat|need to grade)\b",p.question):
        return None
    base=counts[0]
    if base.start>shares[0].start or any(n.start>=len(p.body) for n in shares+counts):
        return None
    if any(_factor(p,r) is not None for r in rates):
        return None
    baseunit=re.match(r'\s+([a-z]+)',p.text[base.end:])
    events=sorted(shares+counts[1:],key=lambda n:n.start)
    current=base.value
    for i,n in enumerate(events):
        before=re.split(r'[.!?;]|,(?!\d)|\band\b',p.text[:n.start])[-1]
        after=p.text[n.end:]
        if not _has(r'\b(?:gave|gives|spent|spends|spending|wrote|writes|written|grades|graded|ate|eats|took|takes|damaged|shed)\b',before):
            if not (n in shares and n!=shares[0] and _has(r'^\s+of the remaining\b',after) and _has(r'\bgave\b',_sentence(p,n))):
                return None
        if n in shares:
            if n!=shares[0] and not _has(r'^\s+of (?:the |his |her |their )?(?:remaining|remainder|empty)\b',after):
                return None
            if not _has(r'^\s+of\b',after) and not (n==shares[0] and _has(r'^\s*[,.;]',after)):
                return None
            current*=1-n.value
        else:
            unit=re.match(r'\s+([a-z]+)',after)
            linked=_has(r'^\s+from the remaining\b',after)
            if not linked and (not unit or not baseunit or _singular(unit.group(1))!=_singular(baseunit.group(1))):
                return None
            current-=n.value
    return _answer(current,'Remove each fixed amount or share from the running remainder')


def _percentage_profit(p, rates, amounts):
    if len(rates)!=2 or len(amounts)!=1 or not _has(r'\bpercent(?:age)? profit\b',p.question):
        return None
    up,down=rates
    if not _has(r'^\s+above the cost\b',p.text[up.end:]) or not _has(r'\bdiscount\b',_sentence(p,down)):
        return None
    return _answer(100*((1+up.value)*(1-down.value)-1),
                   'Selling price as a share of cost, minus one, times 100')


def _alternating_work(p, rates, amounts):
    if len(rates)!=1 or len(amounts)!=3 or not _has(r'\b(?:make|earn)\b',p.question):
        return None
    money=[a for a in amounts if a.kind=='money']
    hours=[a for a in amounts if _has(r'^\s+hours every other day\b',p.text[a.end:])]
    days=[a for a in amounts if _has(r'^\s+day month\b',p.text[a.end:])]
    if not len(money)==len(hours)==len(days)==1 or not _has(r'^\s+an hour\b',p.text[money[0].end:]):
        return None
    if not _has(r'\braise\b',_sentence(p,rates[0])):
        return None
    return _answer(days[0].value/2*hours[0].value*money[0].value*(1+rates[0].value),
                   'Every-other-day work hours times the raised hourly wage')


def _period_rate_totals(p, rates, amounts):
    if len(rates)!=1 or len(amounts)!=3 or not _has(r'\b(?:total|altogether)\b',p.question):
        return None
    r=rates[0];money=[a for a in amounts if a.kind=='money'];periods=[a for a in amounts if a.kind!='money']
    if len(money)!=1 or len(periods)!=2:
        return None
    a,b=periods;w=money[0]
    ua=re.match(r'\s+([a-z]+)',p.text[a.end:]);ub=re.match(r'\s+([a-z]+)',p.text[b.end:])
    if not ua or not ub or ua.group(1)!=ub.group(1):
        return None
    unit=_singular(ua.group(1))
    if unit not in ('hour','day','week','month') or not _has(r'^\s+per '+unit+r'\b',p.text[w.end:]):
        return None
    if not a.start<w.start<b.start<r.start or not _has(r'\b(?:remaining|next|last)\s*$',p.text[:b.start]):
        return None
    f=_factor(p,r)
    if f is None:
        return None
    return _answer(w.value*(a.value+b.value*f),'Original period earnings plus the later period at the changed rate')


def _insurance_net_saving(p, rates, amounts):
    if len(rates)!=1 or len(amounts)!=3 or not _has(r'\bsave\b',p.question):
        return None
    money=[a for a in amounts if a.kind=='money'];periods=[a for a in amounts if a.kind!='money']
    if len(money)!=2 or len(periods)!=1:
        return None
    n=periods[0]
    if not _has(r'^\s+months\b',p.text[n.end:]) or not _has(r'\binsurance\b',p.body):
        return None
    premiums=[a for a in money if _has(r'^\s+per month\b',p.text[a.end:])]
    if len(premiums)!=1 or not _has(r'\bcovers all but\s*$',p.text[:rates[0].start]):
        return None
    premium=premiums[0];bill=next(a for a in money if a!=premium)
    if not _has(r'\bcost\b',_sentence(p,bill)):
        return None
    return _answer(bill.value*(1-rates[0].value)-premium.value*n.value,
                   'Insurance benefit less all premiums paid')


def _remaining_installments(p, rates, amounts):
    if len(rates)!=1 or len(amounts)!=4 or not _has(r'\bbalance\b',p.question):
        return None
    money=[a for a in amounts if a.kind=='money'];counts=[a for a in amounts if a.kind!='money']
    if len(money)!=3 or len(counts)!=1:
        return None
    r=rates[0]
    if not _has(r'^\s+down payment\b',p.text[r.end:]):
        return None
    monthly=[a for a in money if _has(r'^\s+per month\b',p.text[a.end:])]
    extra=[a for a in money if _has(r'\badditional\s*$',p.text[:a.start]) and _has(r'^\s+for the down payment\b',p.text[a.end:])]
    if len(monthly)!=1 or len(extra)!=1 or monthly==extra:
        return None
    price=next(a for a in money if a not in (monthly[0],extra[0]));n=counts[0]
    if not _has(r'^\s+months\b',p.text[n.end:]) or n.start<len(p.body):
        return None
    return _answer(price.value*(1-r.value)-extra[0].value-monthly[0].value*n.value,
                   'Price less the down payment, extra deposit, and installments already paid')


def _changed_budget(p, rates, amounts):
    if len(rates)!=1 or len(amounts)!=3 or not _has(r'\b(?:how many|buy)\b',p.question):
        return None
    money=[a for a in amounts if a.kind=='money'];counts=[a for a in amounts if a.kind!='money']
    if len(money)!=2 or len(counts)!=1:
        return None
    r=rates[0];count=counts[0]
    if not _has(r'\badd\s*$',p.text[:r.start]) or not _has(r'^\s+to the [a-z]+ budget\b',p.text[r.end:]):
        return None
    old,new=money
    if not count.start<old.start<new.start or not _has(r'\bentire budget\b',p.text[old.end:new.start]):
        return None
    if not _has(r'^\s+each\b',p.text[old.end:]) or not _has(r'^\s+each\b',p.text[new.end:]) or new.value<=0:
        return None
    value=count.value*old.value*(1+r.value)/new.value
    return _answer(value.numerator//value.denominator,'Increased original budget divided by the new unit price, taking whole items')


def _weighted_outputs(p, rates, amounts):
    if len(rates)!=1 or len(amounts)!=4 or not _has(r'\btotal\b',p.question):
        return None
    a,b,c,d=amounts;r=rates[0]
    if not a.start<b.start<r.start<c.start<d.start:
        return None
    ua=re.match(r'\s+([a-z]+) with\b',p.text[a.end:])
    link=re.match(r'\s+([a-z]+) per ([a-z]+)',p.text[b.end:])
    if not ua or not link or _singular(ua.group(1))!=_singular(link.group(2)):
        return None
    uc=re.match(r'\s+([a-z]+)',p.text[c.end:]);ud=re.match(r'\s+([a-z]+)',p.text[d.end:])
    if not uc or not ud or uc.group(1)!=ud.group(1):
        return None
    if not _has(r'\bthe rest\b',p.text[c.end:d.start]) or not _has(r'^\s+of the '+re.escape(link.group(1))+r'\b',p.text[r.end:]):
        return None
    return _answer(a.value*b.value*(r.value*c.value+(1-r.value)*d.value),
                   'Total members times the weighted output of the two complementary groups')


def _counted_coupons(p, rates, amounts):
    if len(rates)!=1 or len(amounts)!=4 or not _has(r'\b(?:cost|pay|spend)\b',p.question):
        return None
    money=[a for a in amounts if a.kind=='money'];counts=[a for a in amounts if a.kind!='money']
    if len(money)!=2 or len(counts)!=2:
        return None
    credits=[a for a in money if _has(r'^\s+coupons?\b',p.text[a.end:])]
    if len(credits)!=1:
        return None
    credit=credits[0];price=next(a for a in money if a!=credit)
    ccs=[a for a in counts if not p.text[a.end:credit.start].strip() and a.end<=credit.start]
    if len(ccs)!=1:
        return None
    cc=ccs[0];purchase=next(a for a in counts if a!=cc)
    unit=re.match(r'\s+per ([a-z]+)',p.text[price.end:])
    countunit=re.match(r'\s+([a-z]+)',p.text[purchase.end:])
    if not unit or not countunit or _singular(unit.group(1))!=_singular(countunit.group(1)):
        return None
    f=_factor(p,rates[0])
    if f is None or f>1:
        return None
    return _answer(price.value*purchase.value*f-credit.value*cc.value,
                   'Discounted purchases less the number of coupons times each coupon value')


def _energy_cost(p, rates, amounts):
    if len(rates)!=2 or len(amounts)!=3 or not _has(r'\b(?:cost|pay)\b',p.question):
        return None
    watts=[a for a in amounts if _has(r'^\s+watts\b',p.text[a.end:])]
    prices=[a for a in amounts if _has(r'^\s+cents per kilowatt-hour\b',p.text[a.end:])]
    durations=[a for a in amounts if _has(r'^\s+hours\b',p.text[a.end:])]
    if not len(watts)==len(prices)==len(durations)==1:
        return None
    power=watts[0];price=prices[0];hours=durations[0]
    pr=[r for r in rates if _sentence(p,r)==_sentence(p,power)]
    if len(pr)!=1:
        return None
    power_rate=pr[0];price_rate=next(r for r in rates if r!=power_rate)
    if not _has(r'\bprice\b',_sentence(p,price_rate)) or not _has(r'\bdollars\b',p.question):
        return None
    fs=[_factor(p,r) for r in rates]
    if any(f is None for f in fs):
        return None
    # _money_number already converts cents into dollars.
    return _answer(power.value/1000*price.value*hours.value*fs[0]*fs[1],
                   'Changed kilowatts times hours times the changed price per kilowatt-hour')


def _valued_cube(p, rates, amounts):
    """Volume x density x price per mass x stated selling-value ratio."""
    if len(rates)!=1 or len(amounts)!=3 or not _has(r'\b(?:sell|sells|sold|cost|price)\b',p.question):
        return None
    side,density,price=amounts;r=rates[0]
    if not _has(r'\bcube\b',p.text[:side.start]) or not _has(r'^\s+of (?:its |the )?[a-z]+ value\b',p.text[r.end:]):
        return None
    length=re.match(r'\s+([a-z]+) on each side\b',p.text[side.end:])
    mass=re.match(r'\s+([a-z]+)',p.text[density.end:])
    if not length or not mass or price.kind!='money':
        return None
    lu=_singular(length.group(1));mu=_singular(mass.group(1))
    if not _has(r'\ba cubic '+re.escape(lu)+r'\b[^.;]*\bweighs\s*$',p.text[:density.start]):
        return None
    if not _has(r'\beach '+re.escape(mu)+r'\b[^.;]*\bsells for\s*$',p.text[:price.start]):
        return None
    return _answer(side.value**3*density.value*price.value*r.value,
                   'Cube volume times mass per cubic unit times price per mass unit times the selling-value share')


def solve(problem):
    if not any(n.kind=='percent' for n in problem.numbers):
        return None
    if _has(r"^(?:i(?: am|'m)|we(?: are|'re))\s+(?:trying|learning|wondering)\b",problem.text.lower()):
        return None
    p=_prepare(problem)
    if len(_currencies(p,p.numbers))>1:
        return None
    from .comparisons_r01_a2 import _names
    p.entities=_names(problem.text)
    rates=[n for n in p.numbers if n.kind=='percent']
    amounts=[n for n in p.numbers if n.kind!='percent']
    if any(n.value<=0 for n in rates):
        return None
    if any(n.value>1 for n in rates):
        return _finish(p,_valued_cube(p,rates,amounts))
    for reader in (_counted_coupons, _energy_cost, _valued_cube, _sequential_remainder, _percentage_profit, _alternating_work,
                   _period_rate_totals, _insurance_net_saving, _remaining_installments,
                   _changed_budget, _weighted_outputs, _progress_rate, _replacement_count, _discount_threshold, _spending_percentage,
                   _inverse_remainder, _geometric_levels, _trade_in, _partial_discount,
                   _inventory_profit, _paired_task_time, _annual_purchase, _annuity,
                   _disjoint_nonresponse, _attendance_remainder, _repeated_change, _income_commission_allocation, _parallel_money_shares,
                   _fraction_budget, _updated_win_percentage, _comparison_graph, _price_chain, _basket, _loan, _sale_stock, _allocation,
                   _raised_count_cost, _multiple_collection, _parallel_binary, _retained_branch,
                   _contribution_match, _calendar_saving, _geometric_production,
                   _group_remainders, _equal_capacity, _nested_difference, _complement_nested):
        result=reader(p,rates,amounts)
        if result is not None:
            return result if _has(r'\bpercent(?:age)?\b',p.question) else _finish(p,result)
    return None
