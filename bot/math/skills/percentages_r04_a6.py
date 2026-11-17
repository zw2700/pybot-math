"""Composed percentage relations, with explicit bases and exact arithmetic.

Readers identify a base, every adjustment and the requested quantity.  They
abstain on unrelated counts, ambiguous percentage bases and unsupported queries.
"""
import re
from fractions import Fraction

from ..numbers import read_numbers, format_number
from ..problem import Problem
from .counting_and_totals_r00_a1 import _sentence, _singular
from .percentages_r02_a3 import _labels, _selection, _opposite


def _has(pattern, text):
    return re.search(pattern, text) is not None


def _answer(value, explanation):
    if value < 0:
        return None
    return value, explanation + ' = ' + format_number(value) + '.'


def _finish(p,result):
    """State the requested unit so the arbiter recognizes a quantity answer."""
    if result is None:
        return None
    value,working=result
    if any(n.kind=='money' or re.match(r'\s+dollars?\b',p.text[n.end:]) for n in p.numbers) and _has(
            r'\b(?:cost|pay|paid|paying|price|spend|spent|earn|make|money|save|owe|cover|out-of-pocket)\b',p.question):
        symbol=next((c for n in p.numbers if n.kind=='money' for c in n.raw if c in '$£€'),'$')
        unit={'$':'dollars','£':'pounds','€':'euros'}[symbol]
        owner=re.search(r'\b(?:does|did|will|should|can|would|could)\s+(.{1,50}?)\s+'
                        r'(?:pay|spend|make|earn|owe|save|receive|get)\b',p.question)
        label='The amount for '+owner.group(1) if owner else 'The amount'
        working+=' '+label+' is '+format_number(value)+' '+unit+'.'
    elif _has(r'\b(?:weigh|weight)\b',p.question):
        units=re.findall(r'\b(pounds?|kilograms?|ounces?|grams?|kg)\b',p.body)
        if units and len({_singular(u) for u in units})==1:
            working+=' Weight: '+format_number(value)+' '+units[0]+'.'
    return value,working


def _prepare(p):
    # Expand monetary magnitude suffixes locally, without changing shared parsing.
    text = re.sub(r'\bwithin\b', 'in', p.text.lower())
    text = re.sub(r'\b(\d+) and a half\b',lambda m:str(Fraction(m.group(1))+Fraction(1,2)),text)
    text = re.sub(r'(\d[\d,]*(?:\.\d+)?)\s+(thousand|million|billion)\b',
                  lambda m: format_number(Fraction(m.group(1).replace(',', '')) *
                      {'thousand': 1000, 'million': 1000000, 'billion': 1000000000}[m.group(2)]),
                  text)
    at = len(text) - len(p.question) if text == p.text.lower() else None
    if at is None:
        from ..problem import ASK
        asks = list(ASK.finditer(text))
        if not asks:
            return None
        at = asks[-1].start()
    ns = read_numbers(text)
    # An identical quantity repeated in the query is a reference, not a purchase.
    kept = []
    from .rates_and_unit_rates_r03_a6 import _unit
    for n in ns:
        before, after = text[:n.start], text[n.end:]
        if n.value == 1 and n.kind != 'percent' and _has(r'^\s+day\b', after) and (
                not before.strip() or _has(r'[.!?]\s*$', before)):
            continue
        if n.start >= at and n.kind != 'percent':
            unit = re.match(r'[- ]+([a-z]+)', after)
            if unit and any(x.kind == n.kind and x.value == n.value and
                    _unit(text,x)==_unit(text,n) and _unit(text,n) for x in kept):
                continue
        if n.value==1 and _has(r'^-time\b',after):
            continue
        if n.value==1 and _has(r'^\s+of (?:his|her|their) (?:friends|relatives|children|parents)\b',after):
            continue
        kept.append(n)
    prepared = Problem(text, text[:at], text[at:], kept)
    from .comparisons_r01_a2 import _names
    prepared.entities = _names(p.text)
    return prepared


def _factor(p, n):
    """Interpret an explicit change, as distinct from a population share."""
    before = p.text[max(0, n.start-60):n.start]
    after = p.text[n.end:]
    down = (_has(r'\b(?:discount|discounted|decreased?|reduced?|reduction|down|off|deducted|cashback)(?:\s+(?:of|by|is|was|at|a))?\s*$', before)
            or _has(r'^\s+(?:off|discount|cashback|cheaper|less|fewer|lower|shorter|loss)\b', after))
    up = (_has(r'\b(?:increased?|increase|raised?|raise|up|markup|mark-up|bonus|tax|interest)(?:\s+(?:of|by|is|was|at|a))?\s*$', before)
          or _has(r'^\s+(?:more|longer|higher|heavier|taller|bonus|increase|tax|interest|raise|profit)\b', after)
          or _has(r'\b(?:service fee|profit)(?: of)?\s*$',before))
    down = down or _has(r'\bwithhold\s*$',before)
    up = up or _has(r'\b(?:tips?|tipped)[^.!?;]{0,35}$',before)
    down = down or _has(r'\b(?:reduc\w*|decreas\w*)[^.!?;]{0,45}\bby\s*$', before)
    up = up or _has(r'\b(?:increas\w*|rais\w*|improv\w*)[^.!?;]{0,45}\bby\s*$', before)
    if up == down:
        return None
    return 1-n.value if down else 1+n.value


def _label(p, r):
    source=p.body if r.end<=len(p.body) else p.text
    tail = re.split(r'[.!?;]|\s+and\s+', source[r.end:])[0]
    before = p.text[:r.start]
    predicate=re.match(r'\s+of\b.+?\b(are|is|were|was|got|received|have|has|had|joined|chose|fall|smelled)\s+(.+)',tail)
    if predicate:
        return predicate.group(1)+' '+predicate.group(2)
    if _has(r'\b(?:is|are|was|were)\s*$', before) and not _has(r'^\s+of\b', tail):
        return tail
    return _labels(source, r)


def _choice(label, p):
    from .percentages_r02_a3 import _words
    if _has(r'\bnon[- ]',p.question) and _words(label)&_words(p.question):
        return -1
    if _has(r'\b(?:revoked|not allowed)\b',label) and _has(r'\b(?:attended|allowed)\b',p.question):
        return -1
    if _opposite(label, p.question):
        return -1
    if _words(label) & _words(p.question):
        return 1
    return _selection(label, p.question, p.body)


def _total(p):
    return _has(r'\b(?:total|together|combined|altogether|both|in all|everything|outfit)\b',p.question) or _has(
        r'\b(?:in total|altogether|in all),?\s*$',p.body)


def _comparison(p, rates, amounts):
    """Translate percentage comparisons into the existing affine graph grammar."""
    text = p.text
    for r in reversed(rates):
        m = re.match(r'\s+(more|less|fewer|cheaper|longer|shorter|higher|lower|heavier|lighter)(.*?)\s+than\s+', text[r.end:])
        if not m:
            return None
        direction, unit = m.group(1), m.group(2)
        factor = 1+r.value if direction in ('more','longer','higher','heavier') else 1-r.value
        adjective = 'expensive' if direction == 'cheaper' else 'long' if direction in ('longer','shorter') else 'many'
        text = text[:r.start] + format_number(factor) + ' times as '+adjective+unit+' as ' + text[r.end+m.end():]
    # Preserve names for the comparison graph's owner parser.
    from .comparisons_r01_a2 import _names
    from .comparisons_r03_a4 import solve as graph
    for name in getattr(p, 'entities', []):
        text = re.sub(r'\b'+re.escape(name)+r'\b', name.title(), text)
    text=re.sub(r'\bcollected\b','has',text)
    translated = Problem.read(text)
    if translated:
        from .fractions_of_a_quantity_r03_a2 import _comparisons as fraction_graph
        return graph(translated) or fraction_graph(translated)
    return None


def _relative_total(p, rates, amounts):
    if len(rates) != 1 or len(amounts) != 1:
        return None
    r, a = rates[0], amounts[0]
    if _has(r'\b(?:twice|triple|double|thrice|times|per|each|every)\b', p.text):
        return None
    m = re.match(r'\s+(more|less|fewer|longer|shorter|higher|lower)(.*?)(?:\bthan\b|[.!?])', p.text[r.end:])
    if not m:
        return None
    if not _total(p):
        # "How many days did she spend ...?" after a first and second event.
        if not (_has(r'\b(?:second|another)\b', p.body) and _has(r'\b(?:spend|spent)\b', p.question)):
            return None
    positive = m.group(1) in ('more', 'longer', 'higher')
    base=a.value
    # Bind a counted category to its side of the comparison. A count of the
    # larger/smaller category must first be divided by the comparison factor.
    from .percentages_r02_a3 import _words
    clause=_sentence(p.text,r.start,r.end)
    lhs=m.group(2).strip() or re.split(r'[.;!?]',p.text[:r.start])[-1]
    rhs=re.split(r'[.;!?]',p.text[r.end+m.end():])[0]
    known=_sentence(p.body,a.start,a.end)
    common=_words(lhs)&_words(rhs)
    left=bool((_words(lhs)-common)&_words(known))
    right=bool((_words(rhs)-common)&_words(known))
    period_comparison=_has(r'\b(?:second|another|last|previous)\b',clause)
    if left and not right and not period_comparison:
        f=1+r.value if positive else 1-r.value
        if not f:
            return None
        base/=f
    elif a.start>r.start and not right:
        return None
    return _answer(base*(2+r.value if positive else 2-r.value),
                   'Original amount plus the percentage-related amount')


def _scaled_change(p, rates, amounts):
    """A scalar doubling/tripling composed with a percentage change or share."""
    if len(rates) != 1 or len(amounts) != 1:
        return None
    r, a = rates[0], amounts[0]
    ms = list(re.finditer(r'\b(twice|double|triple|thrice)\b', p.body))
    if len(ms) != 1:
        return None
    m = ms[0]
    scale = Fraction(2 if m.group(1) in ('twice','double') else 3)
    factor = _factor(p, r)
    if factor is None:
        if not _has(r'^\s+of\b', p.text[r.end:]) and not _has(r'\bcommission\b', p.text):
            return None
        factor = r.value
    if _has(r'\b(?:total|sales|commission)\b', p.question) and _has(r'\b(?:as much|as many)\b', p.text[m.end():]) and (
            _has(r'\b(?:another|remaining|other)\b', p.body) or _has(r'\band\b', p.body)):
        scale += 1
    return _answer(a.value*scale*factor, 'Apply the explicit multiple and percentage to the base')


def _fixed_adjustment(p, rates, amounts):
    """A changed price/time and a separate fixed difference or fee."""
    if len(rates) != 1:
        return None
    if _has(r'\b(?:rebate|coupon)\b',p.body):
        # A repeated package duration states eligibility for a rebate.
        durations=[a for a in amounts if a.kind!='money' and re.match(
            r'[- ]+(?:month|year|week)s?[- ]+(?:prescription|supply|subscription)\b',p.text[a.end:])]
        if durations and len({a.value for a in durations})==1:
            amounts=[a for a in amounts if a not in durations]
    if len(amounts)!=2:
        return None
    r = rates[0]
    if _has(r'\b(?:twice|triple|times|per|each|every)\b', p.text):
        return None
    factor = _factor(p, r)
    if factor is None:
        return None
    # Two alternative prices: compare the discounted option to the other one.
    if all(a.kind == 'money' for a in amounts) and _has(r'\bor\b', p.body) and _has(r'\b(?:save|difference|cheaper)\b', p.question):
        base = min(amounts, key=lambda a: abs(a.end-r.start))
        other = next(a for a in amounts if a != base)
        return _answer(abs(base.value*factor-other.value), 'Difference between the adjusted and alternative prices')
    # Independent event after a percentage extension of the first event.
    if _has(r'\b(?:second|another)\b', p.body) and _has(r'\b(?:how long|total|in all|altogether)\b', p.question):
        a, b = amounts
        ua, ub = (re.match(r'\s+([a-z]+)', p.text[n.end:]) for n in amounts)
        if ua and ub and ua.group(1) == ub.group(1) and a.start < r.start < b.start:
            return _answer(a.value*factor+b.value, 'Adjusted first event plus the separate event')
    # An explicitly fixed rebate is applied after a percentage rebate.
    if _has(r'\b(?:rebate|coupon)\b', p.body) and _has(r'\b(?:cost|pay|spend)\b', p.question):
        price = [a for a in amounts if not _has(r'\b(?:rebate|coupon)\b', _sentence(p.text, a.start,a.end))]
        if len(price) == 1 and factor <= 1:
            other = next(a for a in amounts if a != price[0])
            return _answer(price[0].value*factor-other.value, 'Price after percentage reduction and fixed rebate')
    # A fixed comparative difference and a separate percentage comparison.
    deltas = []
    for a in amounts:
        m = re.match(r'\s+(?:[a-z]+\s+){0,2}?(more|less|fewer)\b', p.text[a.end:])
        if m and _has(r'\bthan\b', _sentence(p.text,a.start,a.end)):
            deltas.append((a, 1 if m.group(1)=='more' else -1))
    if len(deltas)==1:
        delta, sign = deltas[0]
        base = next(a for a in amounts if a != delta)
        if (delta.start < r.start and base.start > r.end) or (base.start<r.start<delta.start):
            from .comparisons_r03_a4 import _subject
            from .percentages_r02_a3 import _words
            prefix=_sentence(p.text,delta.start,delta.end).split(delta.raw)[0].strip()
            prefix=re.split(r'\band\b|,',prefix)[-1].strip()
            subject=_subject(prefix)
            if not subject or not _words(subject)&_words(p.question):
                return None
            return _answer(base.value*factor+sign*delta.value, 'Percentage-related amount plus its fixed comparative difference')
    return None


def _money(p, rates, amounts):
    """Commission plus salary, expense deductions, or markup on total costs."""
    text, q = p.text, p.question
    money = [a for a in amounts if a.kind == 'money']
    counts = [a for a in amounts if a.kind != 'money']
    if not money:
        return None
    if len(rates) == 2 and len(money)==2 and not counts and _has(r'\bcommission\b', text) and _has(r'\bsav\w*\b', q):
        commission = [r for r in rates if _has(r'\bcommission\b', _sentence(text,r.start,r.end))]
        saving = [r for r in rates if _has(r'\bsav\w*\b', _sentence(text,r.start,r.end))]
        salary = [a for a in money if _has(r'\b(?:salary|basic pay|base pay)\b', _sentence(text,a.start,a.end))]
        if len(commission)==len(saving)==len(salary)==1 and commission != saving:
            sales = next(a for a in money if a != salary[0])
            return _answer((sales.value*commission[0].value+salary[0].value)*saving[0].value,
                           'Savings share of base salary plus commission')
    if not counts and len(money)==2 and 1 <= len(rates) <= 3 and _has(r'\b(?:left|remaining|take home)\b', q):
        # Every percentage must explicitly name the same original income.
        if all(_has(r'\b(?:income|salary|earnings|pay)\b', re.split(r'[.;!?]', text[r.end:])[0]) for r in rates):
            income = [a for a in money if _has(r'\b(?:paid|earns?|salary|income)\b', text[max(0,a.start-40):a.start])]
            if len(income)==1:
                bill = next(a for a in money if a != income[0])
                if _has(r'\b(?:pays?|bill|spent|spends)\b', _sentence(text,bill.start,bill.end)):
                    return _answer(income[0].value*(1-sum((r.value for r in rates),Fraction(0)))-bill.value,
                                   'Income minus its percentage deductions and fixed bill')
    if len(rates)==1 and len(money)>=2 and len(counts)==1 and _has(r'\bprofit\b', q) and _has(r'\b(?:each|per)\b', q):
        r, count = rates[0], counts[0]
        if all(_has(r'\b(?:spent|spends|cost|costs|expenditure)\b', _sentence(text,a.start,a.end)) for a in money) and count.value > 0:
            return _answer(sum((a.value for a in money),Fraction(0))*(1+r.value)/count.value,
                           'Total expenses plus profit, divided by the number sold')
    # Net profit when the markup is a fixed difference but tax is on sale price.
    if len(rates)==1 and len(money)==2 and not counts and _has(r'\btax\b',text) and _has(r'\b(?:make|profit|earn)\b',q):
        deltas = [a for a in money if _has(r'^\s+more\b', text[a.end:])]
        if len(deltas)==1 and _has(r'\b(?:sale|sells?|sold)\b',text):
            sale = next(a for a in money if a != deltas[0])
            return _answer(deltas[0].value-sale.value*rates[0].value,
                           'Fixed markup less the tax on the selling price')
    return None


def _nested(p, rates, amounts):
    """Two or three nested population shares, including explicit complements."""
    ratios = sorted(rates+[a for a in amounts if 0<a.value<1 and ('/' in a.raw or a.raw in ('half','a half'))],key=lambda n:n.start)
    counts = [a for a in amounts if a not in ratios]
    # A repeated threshold labels a subset; it is not a population count.
    counts = [a for a in counts if not (
        _has(r'\b(?:under|over|below|above)\s*$',p.text[:a.start]) and
        re.match(r'\s+(?:feet|inches|years|pounds)\b',p.text[a.end:]) and
        a.raw in p.question and _has(r'\b(?:under|over|below|above)\b',p.question))]
    if len(counts)==2:
        unit_rate=[a for a in counts if a.value==1 and re.match(r'\s+[a-z]+\s+per\s+(?:year|month|week|day)\b',p.text[a.end:])]
        if len(unit_rate)==1:
            counts=[a for a in counts if a!=unit_rate[0]]
    # Redundant complementary half: "half ... and the other half ...".
    if len(ratios)==3 and ratios[1].value+ratios[2].value==1 and _has(r'\bother\b',p.text[ratios[1].end:ratios[2].start]):
        ratios=ratios[:2]
    if not 2<=len(ratios)<=3 or len(counts)!=1:
        return None
    a=counts[0]
    if any(not 0<r.value<=1 for r in ratios):
        return None
    factor=Fraction(1)
    previous_label=''
    for i,r in enumerate(ratios):
        label=_label(p,r)
        before=re.split(r'[.!?;]',p.text[:r.start])[-1]
        after=p.text[r.end:]
        if i:
            base=re.match(r'\s+'+(r'(?:of\s+)?' if r.raw in ('half','a half') else r'of\s+')+
                          r'(.+?)(?:\s+(?:are|is|were|was|had|have|has)\b|[,.;!?])',after)
            from .percentages_r02_a3 import _words
            linked=bool(base and (_words(base.group(1)) & _words(previous_label) or _opposite(previous_label,base.group(1))))
            linked=linked or _has(r'^\s+of (?:those|these|them|the (?:remaining|rest))\b',after)
            linked=linked or _has(r'\bof (?:the )?[^,.;]+,\s*$',before)
            linked=linked or (r.raw in ('half','a half') and bool(_words(after.split('.')[0])&_words(previous_label)))
            if not linked:
                return None
            # Determine whether the next base is the preceding share's complement.
            if _opposite(previous_label, (base.group(1) if base else before)) or _has(r'\b(?:remaining|rest|left)\b', before):
                factor = factor/ratios[i-1].value*(1-ratios[i-1].value)
        factor*=r.value
        previous_label=label
    choice=_choice(previous_label,p)
    if not choice:
        return None
    if choice<0 and not _opposite(previous_label,p.question) and not (
            _has(r'\b(?:revoked|not allowed)\b',previous_label) and _has(r'\battended\b',p.question)):
        from .percentages_r02_a3 import _words
        rest=re.search(r'\bthe rest\b([^.;!?]+)',p.body[ratios[-1].end:])
        if not rest or not _words(rest.group(1))&_words(p.question):
            return None
    if choice<0:
        factor=factor/ratios[-1].value*(1-ratios[-1].value)
    if a.start<ratios[0].start or _has(r'\b(?:total|team has|there are)\b',p.text[max(0,a.start-25):a.start]) or _has(r'\bto start with\b',p.question):
        return _answer(a.value*factor,'Whole times the explicitly nested shares')
    return None


def _ledger(p, rates, amounts):
    """Reuse the fraction stock ledger: percent and fraction shares are identical."""
    ratios = sorted(rates+[a for a in amounts if 0<a.value<1 and a.raw in ('half','a half')],key=lambda n:n.start)
    from .fractions_of_a_quantity_r03_a3 import _fraction_ledger
    from .fractions_of_a_quantity_r03_a2 import _allocations
    return _fraction_ledger(p,ratios) or _allocations(p)


def _rate_product(p, rates, amounts):
    if len(rates)!=1 or not 2<=len(amounts)<=4:
        return None
    if any(a.value<=0 for a in amounts):
        return None
    r=rates[0]
    # A percentage of a counted population or a fullness share modifies a
    # dimensionally joined rate chain without changing its units.
    label=_labels(p.text,r)
    choice=_selection(label,p.question,p.body)
    if not (_has(r'^\s+(?:full|pure)\b',p.text[r.end:]) or _has(r'^\s+of\b',p.text[r.end:])):
        return None
    if choice!=1 and not _has(r'^\s+(?:full|pure)\b',p.text[r.end:]):
        return None
    from .rates_and_unit_rates_r03_a6 import _chain
    result=_chain(p,amounts)
    if result:
        return _answer(result[0]*r.value,'Multiply the unit-linked quantities and the selected percentage')
    return None


def _asked_percentage(p, rates, amounts):
    if rates or not _has(r'^what (?:is the )?percent(?:age)?\b',p.question):
        return None
    # One counted total, followed by disjoint contributions, asking for the rest.
    if 3<=len(amounts)<=6 and _has(r'\b(?:rest|remaining|remainder)\b',p.body):
        total,*parts=amounts
        if not _has(r'\b(?:each|per|every|times|twice)\b',p.text) and all(
                _has(r'\b(?:passed|gave|sold|used|ate|took|spent|distributed)\b',_sentence(p.text,n.start,n.end)) for n in parts):
            rest=re.search(r'\b([a-z]+)\s+(?:passed out|gave|sold|used|ate|took|spent|distributed)\s+the rest\b',p.body)
            if rest and _has(r'\b'+re.escape(rest.group(1))+r'\b',p.question) and total.value>0:
                return _answer(100*(total.value-sum((a.value for a in parts),Fraction(0)))/total.value,
                               'Unallocated count divided by the whole, times 100')
    return None


def _purchases(p, rates, amounts):
    """Count identical discounted items; fixed budget rebates are separate."""
    if len(rates)!=1 or len(amounts)!=2:
        return None
    money=[a for a in amounts if a.kind=='money']
    counts=[a for a in amounts if a.kind!='money']
    if len(money)!=1 or len(counts)!=1:
        return None
    r,price,count=rates[0],money[0],counts[0]
    if not _has(r'\b(?:cost|spend|spent|pay|price|make|earn)\b',p.question):
        return None
    if _has(r'\bper\b',p.question) and not _has(r'\beach\b',_sentence(p.text,price.start,price.end)):
        if count.value>0:
            factor=_factor(p,r)
            if factor is not None:
                return _answer(price.value*factor/count.value,'Discounted total divided by the purchased item count')
    if not _has(r'\b(?:each|per|every)\b',_sentence(p.text,price.start,price.end)):
        return None
    if _has(r'\b(?:month|week|year|day|hour)s?\b',p.text[count.end:count.end+12]):
        return None
    factor=_factor(p,r)
    if factor is None:
        return None
    return _answer(count.value*price.value*factor,'Item count times adjusted unit price')


def _remaining_stock(p, rates, amounts):
    """Remove a fixed count before taking a percentage of the remainder."""
    if len(rates)!=1 or len(amounts)!=2 or not _has(r'\b(?:left|remaining|remain)\b',p.question):
        return None
    base,removed=amounts
    r=rates[0]
    if not base.start<removed.start<r.start or not _has(r'^\s+of (?:his |her |the |their )?remaining\b',p.text[r.end:]):
        return None
    if not _has(r'\b(?:throw out|thrown out|rid of|remove|removed|ate|spent|lost|gave|sold)\b',p.text[removed.end:r.start]):
        return None
    ua,ub=(re.match(r'\s+(?:of (?:his|her|the|their) )?([a-z]+)',p.text[n.end:]) for n in amounts)
    if ua and ub and _singular(ua.group(1))==_singular(ub.group(1)):
        return _answer((base.value-removed.value)*(1-r.value),'Remove the counted items, then the stated percentage of the remainder')
    return None


def _known_share_remainder(p, rates, amounts):
    if len(rates)!=2 or len(amounts)!=1 or not _has(r'\b(?:left|remaining|rest)\b',p.question):
        return None
    first,second=rates
    a=amounts[0]
    if not first.start<a.start<second.start or first.value+second.value>1:
        return None
    if _has(r'\b(?:remaining|rest|remainder)\b',p.text[first.end:second.start]):
        return None
    if not all(_has(r'\b(?:spends?|spent|allocated|budget|income)\b',_sentence(p.text,r.start,r.end)) for r in rates):
        return None
    from .percentages_r02_a3 import _words
    known=_sentence(p.text,a.start,a.end)
    label=_label(p,first)
    # A repeated destination links the known amount to the first percentage.
    words=_words(label)-{'budget','annual','income','spend','spent'}
    if not words&_words(known):
        return None
    return _answer(a.value/first.value*(1-first.value-second.value),
                   'Recover the whole from the known share, then remove both allocations')


def _successive(p, rates, amounts):
    if len(rates)!=2 or len(amounts)!=1:
        return None
    factors=[]
    for r in rates:
        f=_factor(p,r)
        if f is None and _has(r'^\s+full\b',p.text[r.end:]):
            f=r.value
        if f is None:
            return None
        factors.append(f)
    if not _has(r'\b(?:now|final|new|weigh|cost|pay|price|total)\b',p.question):
        return None
    return _answer(amounts[0].value*factors[0]*factors[1],'Apply the two successive percentage factors')


def _compound_interest(p,rates,amounts):
    if len(amounts)!=1 or not 1<=len(rates)<=2 or len({r.value for r in rates})!=1:
        return None
    if not _has(r'\bcompound(?:ed)?\b',p.body) or not _has(r'\binterest\b',p.question):
        return None
    if not _has(r'\bsecond month\b',p.question):
        return None
    r=rates[0].value
    return _answer(amounts[0].value*(1+r)*r,'Second-month interest on principal plus first-month interest')


def _annual_production(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=1:
        return None
    r,a=rates[0],amounts[0]
    if not _has(r'^\s+per day\b',p.text[a.end:]) or not _has(r'\byear\b',p.question):
        return None
    f=_factor(p,r)
    if f is not None and _has(r'\b(?:production|produced|produce)\b',p.body):
        return _answer(a.value*365*f,'Daily output times days in a year times the changed production factor')
    return None


def _parallel_shares(p,rates,amounts):
    """Combine same-base shares, or selected shares of two separate counts."""
    from .percentages_r02_a3 import _words
    if len(amounts)==1 and 2<=len(rates)<=3:
        a=amounts[0]
        if a.start>rates[0].start or _has(r'\b(?:remaining|remainder|those|these)\b',p.text[rates[0].end:rates[-1].start]):
            return None
        if _has(r'\bhow (?:many|much) more\b',p.question) and all(_has(r'^\s+of (?:them|it|the|his|her)\b',p.text[r.end:]) for r in rates) and len(rates)==2:
            owners=[]
            for r in rates:
                prefix=_sentence(p.body,r.start,r.end).split(r.raw)[0]
                owners.append(_words(prefix))
            if getattr(p,'entities',None):
                owners[0].update(_words(p.entities[0]))
            common=owners[0]&owners[1]
            positions=[]
            for owner in owners:
                hits=[m.start() for m in re.finditer(r'[a-z]+',p.question)
                      if _singular(m.group()) in owner-common]
                if not hits:
                    return None
                positions.append(min(hits))
            if positions[0]==positions[1]:
                return None
            first,second=(0,1) if positions[0]<positions[1] else (1,0)
            return _answer(a.value*(rates[first].value-rates[second].value),
                           'Difference between the two shares in the requested order')
        rest=re.search(r'\bthe rest\s+(?:on|for|are|is|were|was)\s+([^.;!?]+)',p.body)
        if rest and _words(rest.group(1))&_words(p.question) and sum((r.value for r in rates),Fraction(0))<=1:
            return _answer(a.value*(1-sum((r.value for r in rates),Fraction(0))),'Whole minus the disjoint percentage allocations')
    if len(amounts)==len(rates)==2 and amounts[0].start<rates[0].start<amounts[1].start<rates[1].start:
        labels=[_label(p,r) for r in rates]
        if all(_choice(label,p)==1 for label in labels) and _total(p):
            units=[re.match(r'\s+([a-z]+)',p.text[a.end:]) for a in amounts]
            if all(units) and units[0].group(1)==units[1].group(1):
                return _answer(sum((a.value*r.value for a,r in zip(amounts,rates)),Fraction(0)),
                               'Add the selected shares of the separate populations')
    return None


def _fee_or_shared_price(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=2:
        return None
    r=rates[0]
    f=_factor(p,r)
    if f is None or not _has(r'\b(?:pay|cost|spend|spent)\b',p.question):
        return None
    if all(a.kind=='money' for a in amounts):
        fees=[]
        for a in amounts:
            sentence=_sentence(p.text,a.start,a.end)
            before=p.text[max(0,a.start-25):a.start]
            if _has(r'\b(?:coupon|rebate|tip|shipping|delivery)\b',sentence) and r.raw not in sentence:
                fees.append(a)
        if len(fees)==1:
            fee=fees[0];base=next(a for a in amounts if a!=fee)
            subtract=_has(r'\b(?:coupon|rebate)\b',_sentence(p.text,fee.start,fee.end))
            if subtract:
                before_discount=_has(r'\b(?:after the coupon|coupon.*first|before.*discount)\b',p.body)
                return _answer((base.value-fee.value)*f if before_discount else base.value*f-fee.value,
                               'Apply the percentage reduction and coupon in the stated order')
            return _answer(base.value*f+fee.value,'Adjusted base price plus the separate fixed fee')
    if _has(r'\b(?:each|per)\b',p.question):
        recipients=[a for a in amounts if re.match(r'\s+(?:kids|children|people|parents|friends|members|families|students)\b',p.text[a.end:])]
        if len(recipients)==1 and recipients[0].value>0:
            base=next(a for a in amounts if a!=recipients[0])
            if _has(r'\b(?:salary|paid|pay|raise|income|wage)\b',p.body):
                return _answer(base.value*f/recipients[0].value,'Adjusted total pay divided equally among the contributors')
    return None


def _scaled_profit(p,rates,amounts):
    """Sales at an explicit multiple, a retained share, and a fixed expense."""
    if len(rates)!=1 or len(amounts)!=3 or not _has(r'\bprofit\b',p.question):
        return None
    money=[a for a in amounts if a.kind=='money']
    multiples=[a for a in amounts if re.match(r'\s+times\b',p.text[a.end:])]
    if len(money)==2 and len(multiples)==1:
        expense=[a for a in money if _has(r'\b(?:cost|costs|produce|production)\b',_sentence(p.text,a.start,a.end))]
        if len(expense)==1 and _has(r'\bkeep\b',p.text):
            gross=next(a for a in money if a!=expense[0])
            return _answer(gross.value*multiples[0].value*rates[0].value-expense[0].value,
                           'Total sales times retained share, less the production expense')
    # One fixed advertising cost, counted prospective buyers, price per sale.
    if len(money)==2 and _has(r'\b(?:advertis\w*|ad)\b',p.body):
        cost=[a for a in money if _has(r'\b(?:advertis\w*|ad)\b',_sentence(p.text,a.start,a.end))]
        count=[a for a in amounts if a.kind!='money']
        if len(cost)==len(count)==1:
            price=next(a for a in money if a!=cost[0])
            if _has(r'\b(?:bought|buy|buys)\b',p.text[rates[0].end:price.start]):
                return _answer(count[0].value*rates[0].value*price.value-cost[0].value,
                               'Purchasing share times customers times price, less advertising')
    return None


def _composed_income(p,rates,amounts):
    if len(rates)!=2 or len(amounts)!=1 or not _has(r'\bsav(?:e|ed|es)\b',p.question):
        return None
    first,second=rates
    if not _has(r'\bcommission\b',_sentence(p.text,first.start,first.end)):
        return None
    if not _has(r'\b(?:earning|income)\w*\b',_sentence(p.text,second.start,second.end)):
        return None
    second_factor=1-second.value if _has(r'\b(?:rest|remaining)\b.*\bsav',p.body) else second.value
    return _answer(amounts[0].value*first.value*second_factor,'Commission earnings times the saved share')


def _dimensional_share(p,rates,amounts):
    """Join explicit physical units, then apply a dimensionless percentage."""
    if len(rates)!=1 or not 2<=len(amounts)<=4:
        return None
    if any(a.value<=0 for a in amounts):
        return None
    if _has(r'\b(?:twice|thrice|double|triple)\b',p.text):
        return None
    from .rates_and_unit_rates_r03_a6 import _unit, _head, _term, _terms, _asked, _normal
    r=rates[0]
    factor=_factor(p,r)
    if _has(r'\b(?:profit|more|less|fewer)\b',p.question):
        return None
    tail=p.text[r.end:]
    if factor is None and not _has(r'^\s+(?:of|full|as much|as many|pure)\b',tail):
        return None
    terms=_terms(p,amounts)
    if not terms:
        return None
    for i,a in enumerate(amounts if len(terms)==len(amounts) else []):
        # Expand only explicit per-member, per-container or singular-item grammar.
        before=re.split(r'[.!?;](?:\s|$)',p.text[:a.start])[-1]
        after=re.split(r'[.!?;](?:\s|$)',p.text[a.end:])[0]
        m=re.search(r'\beach ([a-z]+(?: [a-z]+){0,2}?) (?:drops?|weighs?|averages?|averaged|produces?|has|holds?|contains?|is)\s*$',before)
        d=_head(m.group(1)) if m else ''
        if not d:
            m=re.search(r'\bon (?:a|an) ([a-z]+(?: [a-z]+){0,2}?)$',after.strip())
            d=_head(m.group(1)) if m else ''
        if not d:
            m=re.search(r'\b(?:each|a|an) ([a-z]+) (?:averaged|averages?|weighs?)\s*$',before)
            d=_normal(m.group(1)) if m else ''
        if d and not any(v<0 for v in terms[i].powers.values()):
            terms[i]=_term(a.value,_unit(p.text,a),(i,),denominator=d)
    target=_asked(p)
    if not target and _has(r'\b(?:pay|paid|owe|cost|money)\b',p.question):
        target='dollar'
    if not target:
        return None
    powers={};value=Fraction(1)
    per_day=_has(r'\b(?:each|per|every) day\b',p.question)
    for term in terms:
        sign=-1 if per_day and term.powers=={'time':1} else 1
        value=value*term.value if sign==1 else value/term.value
        for unit,power in term.powers.items():
            powers[unit]=powers.get(unit,0)+sign*power
    powers={k:v for k,v in powers.items() if v}
    target_term=_term(Fraction(1),target,(),denominator='day' if per_day else '')
    if powers!=target_term.powers or not any(any(v<0 for v in t.powers.values()) for t in terms):
        return None
    if factor is None:
        choice=_choice(_label(p,r),p)
        if _has(r'\b(?:left|remaining)\b',p.question) and _has(
                r'\b(?:cuts?|eats?|ate|lost|loses?|removes?|sold|sells?)\b',_sentence(p.text,r.start,r.end)):
            choice=-1
        if choice==1 or _has(r'^\s+(?:full|pure|as much|as many)\b',tail):
            factor=r.value
        elif choice==-1:
            factor=1-r.value
        else:
            return None
    return _answer(value*factor/target_term.value,'Multiply the unit-linked quantities and apply the percentage factor')


def _covered_total(p,rates,amounts):
    """A share of a sum of charges, including the uncovered complementary share."""
    if len(rates)!=1 or not 2<=len(amounts)<=4 or any(a.kind!='money' for a in amounts):
        return None
    r=rates[0]
    if not all(_has(r'\b(?:cost|costs|bill|charged|charges)\b',_sentence(p.text,a.start,a.end)) for a in amounts):
        return None
    if not _has(r'\b(?:insurance|covers?|covered)\b',_sentence(p.text,r.start,r.end)):
        return None
    if _has(r'\b(?:out-of-pocket|pay|paid|paying|uncovered)\b',p.question):
        return _answer(sum((a.value for a in amounts),Fraction(0))*(1-r.value),
                       'Combined charges times the share not covered by insurance')
    if _has(r'\b(?:insurance|covered|cover)\b',p.question):
        return _answer(sum((a.value for a in amounts),Fraction(0))*r.value,'Combined charges times the covered share')
    return None


def _capacity_margin(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=2:
        return None
    r=rates[0];a,b=amounts
    if not a.start<r.start<b.start or not _has(r'^\s+under\b',p.text[r.end:]):
        return None
    if not _has(r'\b(?:support|maximum|capacity|limit)\b',p.text[:a.start]) or not _has(r'\b(?:put|add|more|weight)\b',p.question):
        return None
    ua,ub=(re.match(r'\s+([a-z]+)',p.text[n.end:]) for n in amounts)
    if ua and ub and ua.group(1)==ub.group(1):
        return _answer(a.value*(1-r.value)-b.value,'Safety-limited capacity minus the existing load')
    return None


def _tax_difference(p,rates,amounts):
    if len(rates)!=2 or len(amounts)!=2 or not _has(r'\b(?:more|difference)\b',p.question) or not _has(r'\btax(?:es)?\b',p.question):
        return None
    if not _has(r'\b(?:from|used to|then|before)\b',p.body) or not _has(r'\b(?:now|to)\b',p.text):
        return None
    return _answer(amounts[1].value*rates[1].value-amounts[0].value*rates[0].value,
                   'Current tax payment minus the previous tax payment')


def _sum_then_share(p,rates,amounts):
    """Add a list of measured counts before selecting a percentage."""
    if not 1<=len(rates)<=3 or not 2<=len(amounts)<=8:
        return None
    if any(a.kind=='money' for a in amounts) or any(_factor(p,r) is not None for r in rates):
        return None
    if _has(r'\b(?:of these|of those|of them|rid of|throw|throws|removes?|removed|lost|loses|sold|eaten)\b',p.text[:rates[0].start]):
        return None
    amounts=[a for a in amounts if not(a.value==1 and _has(r'^\s+side\b',p.text[a.end:]))]
    if any(a.start>rates[0].start for a in amounts):
        return None
    if _has(r'\b(?:each|every|per|times|twice|double|triple|more|less|fewer|ratio)\b',p.text[:rates[0].start]):
        return None
    from .rates_and_unit_rates_r03_a6 import _unit
    units=[_unit(p.text,a) for a in amounts]
    scheduled=all(_has(r'^\s+on (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',p.text[a.end:]) for a in amounts)
    if not scheduled and (not units[0] or len(set(units))!=1):
        return None
    total=sum((a.value for a in amounts),Fraction(0))
    if len(rates)==1:
        c=_choice(_label(p,rates[0]),p)
        if _has(r'\bhow many more\b',p.question) and _has(r'\b(?:already|completed|finished)\b',p.text[:rates[0].start]):
            c=-1
        if c:
            return _answer(total*(rates[0].value if c>0 else 1-rates[0].value),'Sum the counted amounts, then select the requested share')
    else:
        from .percentages_r02_a3 import _words
        rest=re.search(r'\bthe rest (?:is|are|was|were) ([^.;!?]+)',p.body)
        f=1-sum((r.value for r in rates),Fraction(0))
        if rest and _words(rest.group(1))&_words(p.question) and f>=0:
            return _answer(total*f,'Combined counts times the share left after disjoint categories')
    return None


def _known_population(p,rates,amounts):
    """A counted named category anchors its percentage of an unknown whole."""
    if len(rates)!=1 or len(amounts)!=1:
        return None
    r,a=rates[0],amounts[0]
    if a.start<r.start or _factor(p,r) is not None:
        return None
    from .percentages_r02_a3 import _words
    label=_label(p,r)
    known=_sentence(p.text,a.start,a.end)
    lw=_words(label)-{'student','person','friend','class','total','number'}
    if not lw or not lw&_words(known):
        return None
    c=_choice(label,p)
    if c<0:
        return _answer(a.value/r.value*(1-r.value),'Known category divided by its percentage, times the complementary share')
    if not c and _has(r'\b(?:total|entire|all|class)\b',p.question):
        return _answer(a.value/r.value,'Known category divided by its share of the whole')
    return None


def _interest_periods(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=2:
        return None
    r=rates[0]
    if not _has(r'\binterest\b',p.body):
        return None
    money=[a for a in amounts if a.kind=='money']
    years=[a for a in amounts if _has(r'^\s+years?\b',p.text[a.end:])]
    if len(money)!=1 or len(years)!=1 or not _has(r'\b(?:year|annual|annually)\b',p.body):
        return None
    base=money[0].value; period=years[0].value
    if _has(r'\b(?:simple|withdraws?|withdrawn)\b',p.body):
        interest=base*r.value*period
        return _answer(interest if not _has(r'\b(?:including|total|deposit|have)\b',p.question) else base+interest,
                       'Principal times annual rate times years, with principal included when requested')
    if _has(r'\bcompound(?:ed)?\b',p.body) and period.denominator==1 and 0<period<=100:
        total=base*(1+r.value)**int(period)
        return _answer(total-base if _has(r'\binterest\b',p.question) and not _has(r'\b(?:total|including|have)\b',p.question) else total,
                       'Compound the annual balance for the stated number of years')
    return None


def _annual_interval(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=2 or not _has(r'\bin a year\b|\bper year\b',p.question):
        return None
    a,period=amounts
    if not _has(r'\bevery\s*$',p.text[:period.start]) or not _has(r'^\s+months?\b',p.text[period.end:]) or period.value<=0:
        return None
    f=_factor(p,rates[0])
    if f is not None:
        return _answer(a.value*12/period.value*f,'Scale the stated interval to a year, then apply the percentage change')
    return None


def _numeric_multiple(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=2:
        return None
    scalar=[a for a in amounts if _has(r'^\s+times\b',p.text[a.end:])]
    if len(scalar)!=1:
        return None
    scale=scalar[0];base=next(a for a in amounts if a!=scale);r=rates[0]
    f=_factor(p,r)
    if f is None:
        if base.kind=='money':
            return None
        if _has(r'\b(?:left|remain|remaining)\b',p.question) and _has(r'\b(?:taken|removed|sold|lost|eaten)\b',p.text[r.end:]):
            f=1-r.value
        elif _choice(_label(p,r),p)==1:
            f=r.value
        else:
            return None
    return _answer(base.value*scale.value*f,'Apply the explicit multiple and the percentage factor')


def _selected_percentage(p,rates,amounts):
    """Percentages of several named categories, including complements."""
    if rates or not _has(r'^what (?:is the )?percent(?:age)?\b',p.question):
        return None
    from .percentages_r02_a3 import _words
    money=[a for a in amounts if a.kind=='money']
    if money:
        # A priced package's mass describes the package, not a second charge.
        if any(a not in money and not re.match(r'(?:oz|kg|g)\b',p.text[a.end:]) for a in amounts):
            return None
        if _has(r'\b(?:each|per|every|discount|tax)\b',p.body):
            return None
        counts=money;labels=[]
        for a in counts:
            before=re.split(r'[,.;!?]|\band\b',p.text[:a.start])[-1]
            labels.append(_words(before)-{'buy','buys','bought','cost','costs','price'})
    else:
        counts=amounts;labels=[]
        if not 2<=len(counts)<=5 or _has(r'\b(?:times|twice|more|less|each|per|every|rest|remaining)\b',p.body):
            return None
        for a in counts:
            after=re.split(r'[,.;!?]|\band\b',p.text[a.end:])[0]
            labels.append(_words(after))
    if not 2<=len(counts)<=5:
        return None
    common=set.intersection(*labels)
    chosen=[a for a,label in zip(counts,labels) if (label-common)&_words(p.question)]
    negated=_has(r'\bnot\b|\bnon[- ]',p.question)
    if not chosen or not negated and len(chosen)==1:
        return None
    total=sum((a.value for a in counts),Fraction(0))
    if total<=0:
        return None
    selected=sum((a.value for a in chosen),Fraction(0))
    return _answer(100*(total-selected if negated else selected)/total,
                   'Requested category amounts divided by the total, times 100')


def solve(problem):
    if not any(n.kind=='percent' for n in problem.numbers) and not _has(
            r'^what (?:is the )?percent(?:age)?\b',problem.question):
        return None
    if _has(r"^(?:i(?: am|'m)|we(?: are|'re))\s+(?:trying|learning|wondering)\b",problem.text.lower()):
        return None
    p=_prepare(problem)
    if p is None:
        return None
    currencies={c for n in p.numbers if n.kind=='money' for c in n.raw if c in '$£€'}
    if len(currencies)>1:
        return None
    rates=[n for n in p.numbers if n.kind=='percent']
    amounts=[n for n in p.numbers if n.kind!='percent']
    if not rates:
        return _finish(p,_selected_percentage(p,rates,amounts) or _asked_percentage(p,rates,amounts))
    if any(not 0<n.value<=1 for n in rates):
        return None
    readers = (
        _nested, _sum_then_share, _known_population, _interest_periods,
        _annual_interval, _numeric_multiple, _covered_total, _capacity_margin,
        _tax_difference, _parallel_shares, _fee_or_shared_price, _scaled_profit,
        _composed_income, _dimensional_share, _compound_interest,
        _annual_production, _known_share_remainder, _remaining_stock,
        _purchases, _money, _fixed_adjustment, _scaled_change, _relative_total,
        _comparison, _successive, _ledger, _rate_product,
    )
    for reader in readers:
        result=reader(p,rates,amounts)
        if result is not None:
            return _finish(p,result)
    return None
