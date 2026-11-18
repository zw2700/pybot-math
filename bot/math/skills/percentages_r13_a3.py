"""Explicit percentage bases, remainders, nested shares and short cost ledgers.

Every reader accounts for the quantities it uses and checks the requested unit.
Unsupported relations fall through to the other independent math skills.
"""
import re
from fractions import Fraction

from ..numbers import format_number
from ..problem import Problem
from ._fractions_common import _answer, _has
from .counting_and_totals_r00_a1 import _singular
from .percentages_r02_a3 import _words, _opposite


def _clause(text, start, end):
    left = list(re.finditer(r'[.;!?](?:\s|$)', text[:start]))
    right = re.search(r'[.;!?](?:\s|$)', text[end:])
    return text[left[-1].end() if left else 0:end+right.start() if right else len(text)]


def _unit(p, n):
    m = re.match(r'[- ]+(?:(?:more|new|additional)\s+)?(?:of (?:the |his |her |their )?)?([a-z]+)', p.text[n.end:])
    return _singular(m.group(1)) if m else ''


def _label(p, n):
    source=p.body if n.end<=len(p.body) else p.text
    tail = re.split(r'[.;!?,]|\s+(?:and|while|but)\s+', source[n.end:])[0]
    # In "half of those who did not throw are sacked", the final predicate
    # names the selected group; the earlier negation belongs to its base.
    predicates = list(re.finditer(r'\b(?:is|are|was|were|has|have)\s+', tail))
    if predicates:
        return re.sub(r'\b(?:won|wins)\b','win',tail[predicates[-1].end():])
    before = re.split(r'[.;!?]|\s+and\s+', p.text[:n.start])[-1]
    if re.search(r'\b(?:is|are|was|were|spent|spends|saved|saves|sold|lost|make up|makes up|account for|accounts for|represent|represents|comprise|comprises)\s*$', before):
        return before + ' ' + tail
    return tail


def _result(p, value, working):
    result = _answer(value, working)
    if result is None:
        return None
    # Include monetary units in the prose so the arbiter can recognize a
    # money answer even when the source used a currency symbol only.
    if not _has(r'\bpercent(?:age)?\b',p.question) and any(n.kind == 'money' for n in p.numbers) and _has(
            r'\b(?:pay|paid|cost|price|money|earn|make|spend|bring|give back|tips?|save)\b', p.question):
        currency = next((c for n in p.numbers for c in n.raw if c in '$£€'), '$')
        unit = {'$': 'dollars', '£': 'pounds', '€': 'euros'}[currency]
        return result[0], result[1] + ' The amount is ' + format_number(value) + ' ' + unit + '.'
    return result


def _prepare(problem):
    p = Problem(problem.text.lower(), problem.body, problem.question, list(problem.numbers))
    kept = []
    for n in p.numbers:
        before, after = p.text[:n.start], p.text[n.end:]
        if n.kind != 'percent':
            if n.start and p.text[n.start-1].isalpha() and n.raw.isdigit():
                continue
            if n.start>=len(p.body) and any(x.start<len(p.body) and x.value==n.value and _unit(p,x)==_unit(p,n) and _unit(p,n) for x in kept):
                continue
            if any(m.start() <= n.start < m.end() for m in re.finditer(r'\b\d+(?:\s*-\s*\d+)?\s+years? old\b',p.text)):
                continue
            if re.match(r'\s+(?:days?|years?) ago\b',after):
                continue
            if re.search(r'\bgrade\s*$',before):
                continue
            if n.raw.lower() == 'quarters':
                continue
            if re.match(r'-[a-z]+',after) and n.start >= len(p.body) and any(x.value==n.value and x.start<n.start for x in p.numbers):
                continue
            if kept and kept[-1].kind=='percent' and re.fullmatch(r'\s+(?:of [a-z ]+ )?(?:have|has|had)\s+',p.text[kept[-1].end:n.start]):
                tail=re.split(r'[.;!?]|\band\b',after)[0]
                if not re.search(r'\b(?:each|per|every)\b',tail):
                    continue
            # Age/size descriptors classify items rather than count the items.
            if re.search(r'\b(?:under|over|below|above)\s*$', before) and re.match(r'\s+years?\s+old\b', after):
                continue
            if re.search(r'\bthe\s*$', before) and re.match(r'\s+(?:day|days) ago\b', after):
                continue
            if n.value == 1 and re.search(r'(?:^|[.!?])\s*$', before) and re.match(r'\s+day\b', after):
                continue
            if n.raw.lower() in ('quarter', 'quarters') and re.match(r'[,.;]|\s+(?:are|and|of the quarters)\b', after):
                # A bare coin noun after a counted amount is not a fraction.
                if kept and re.search(r'\d\s*$', before):
                    continue
        kept.append(n)
    p.numbers = kept
    return p


def _progress(p, rates, amounts):
    if rates or len(amounts) != 2 or not _has(r'\bpercent(?:age)?\b', p.question):
        return None
    a, b = amounts
    if not (_has(r'\b(?:goal|target)\b', p.question) and _has(r'\b(?:needs?|more|remaining)\b', _clause(p.text,b.start,b.end))):
        return None
    if a.start < b.start and _has(r'\b(?:has|have|gotten|done|completed|saved|earned)\b', p.text[:a.start]) and a.value+b.value > 0:
        return _result(p, 100*a.value/(a.value+b.value), 'Completed amount / (completed + still needed) x 100')
    return None


def _fraction_percentage(p, rates, amounts):
    if rates or not 1 <= len(amounts) <= 3 or not _has(r'\b(?:as a percentage|expressed as a percent)\b', p.question):
        return None
    if any(not 0 < a.value < 1 for a in amounts):
        return None
    if _has(r'\b(?:takes?|took|eats?|ate|total|altogether|combined)\b', p.text) and not _has(r'\b(?:left|remaining|rest|of those|of these)\b',p.body):
        return _result(p, sum((a.value for a in amounts), Fraction(0))*100, 'Sum the portions and multiply by 100')
    return None


def _parallel_remainder(p, rates, amounts):
    """Select an explicit partition's categories, or its unlisted remainder."""
    if not 2 <= len(rates) <= 3 or len(amounts) != 1:
        return None
    a=amounts[0]
    if a.start>rates[0].start or sum((r.value for r in rates),Fraction(0))>1:
        return None
    rest=re.search(r'\b(?:the rest|the remainder|remaining)\b([^.;!?]+)',p.body)
    exhaustive=re.search(r'\b(?:all (?:either|are)|either|consist(?:s)? of|made up of)\b',p.body)
    if not rest and not exhaustive:
        return None
    labels=[_words(_label(p,r)) for r in rates]
    whole_words=_words(re.split(r'[.!?,]|\b(?:is|are|has|have|live|in|from|to)\b',p.text[a.end:])[0])
    common=set.intersection(*labels)|whole_words
    for r in rates[1:]:
        after=p.text[r.end:]
        if re.match(r'\s+of (?:these|those)\b',after) and re.search(r'[.;!?]',p.text[rates[0].end:r.start]):
            return None
        if re.match(r'\s+of (?:the )?(?:remaining|rest)\b',after):
            return None
        if re.match(r'\s+of them\b',after):
            continue
        base=re.match(r'\s+of\s+(.*?)(?:\b(?:are|is|were|was|have|has)\b|[,.;!?])',after)
        if base and (_words(base.group(1))-common-{'them','these','those','of','will','people'}) & set.union(*labels):
            return None
    chosen=[i for i,label in enumerate(labels) if (label-common)&_words(p.question)]
    if chosen:
        if len(chosen)>1 and not _has(r'\b(?:and|or)\b',p.question):
            return None
        share=sum((rates[i].value for i in chosen),Fraction(0))
        if _has(r'\bnot\b',p.question):
            share=1-share
        return _result(p,a.value*share,'Whole times the explicitly requested disjoint category shares')
    rest_words=(_words(rest.group(1))-set.union(*labels)-whole_words) if rest else set()
    if rest and not (rest_words&_words(p.question) or _has(r'\b(?:rest|remaining|left)\b',p.question)):
        return None
    if not rest and not exhaustive:
        return None
    return _result(p,a.value*(1-sum((r.value for r in rates),Fraction(0))),'Whole times the share remaining after the disjoint categories')


def _nested_shares(p, rates, amounts):
    ratios = sorted(rates + [a for a in amounts if 0<a.value<1], key=lambda n:n.start)
    counts = [a for a in amounts if a not in ratios]
    if len(counts) != 1 or not 2 <= len(ratios) <= 3:
        return None
    a = counts[0]
    if a.start > ratios[0].start:
        return None
    factor = ratios[0].value
    previous = _label(p, ratios[0])
    for r in ratios[1:]:
        tail = p.text[r.end:]
        before = re.split(r'[.;!?]',p.text[:r.start])[-1]
        base = re.match(r'\s+(?:of\s+)?(.+?)(?=\b(?:is|are|was|were|has|have)\b|[,.;!?])',tail)
        base_text = base.group(1) if base else ''
        linked = bool((_words(base_text)-_words(_clause(p.text,a.start,a.end))) & _words(previous))
        linked = linked or bool(re.match(r'\s+of (?:these|those|them|that number)\b',tail))
        linked = linked or bool(re.search(r'^\s*of (?:the )?[^,.;]+,?\s*$',before))
        if not linked:
            return None
        if _has(r'\b(?:remaining|rest)\b',base_text+' '+before):
            factor = factor/ratios[ratios.index(r)-1].value*(1-ratios[ratios.index(r)-1].value)
        factor *= r.value
        previous = _label(p,r)
    # Negation in an earlier base must not negate the final predicate.
    if not _words(previous)&_words(p.question):
        return None
    if _opposite(previous,p.question):
        factor = factor/ratios[-1].value*(1-ratios[-1].value)
    return _result(p,a.value*factor,'Whole times the linked subset shares')


def _remainder_base(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=2:
        return None
    a,b=amounts; r=rates[0]
    if not a.start<b.start<r.start or not _has(r'\b(?:rest|remaining|remainder)\b',p.text[b.end:r.start]):
        return None
    if not _has(r'\bof\b',p.text[r.end:r.end+12]) or a.value<b.value:
        return None
    rest=re.search(r'\b(?:rest|remaining|remainder)[^.;!?]*?\b(?:are|is)\s+([^.;!?]+)',p.text[b.end:r.start])
    base=re.match(r'\s+of\s+(.+?)(?=\b(?:wear|wears|are|is|have|has)\b|[,.;!?])',p.text[r.end:])
    if not rest or not base or not _words(rest.group(1))&_words(base.group(1)):
        return None
    if _words(_label(p,r)) & _words(p.question):
        return _result(p,(a.value-b.value)*r.value,'Subtract the other category, then take the stated share')
    return None


def _single_remainder(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=1:
        return None
    a=amounts[0]; r=rates[0]
    if _has(r'\b(?:read|reading|finished)\b',p.body) and (_has(r'\b(?:finish|remaining|left)\b',p.question) or _has(r'\bbreak\b',p.body) and _has(r'\bafter\b',p.question)) and _has(r'\b(?:pages|book)\b',p.question):
        if a.start<r.start and _unit(p,a) in ('page','book'):
            return _result(p,a.value*(1-r.value),'Total pages minus the pages already read')
    rest=re.search(r'\bthe rest\s+(?:are|is|were|was)\s+([^.;!?]+)',p.body)
    if rest and (_words(rest.group(1))-_words(_label(p,r))-{_unit(p,a)})&_words(p.question):
        return _result(p,a.value*(1-r.value),'Whole times the complementary share')
    return None


def _price_share(p,rates,amounts):
    if len(rates)!=1 or not 1<=len(amounts)<=2:
        return None
    r=rates[0]
    if not _has(r'\b(?:only|just) (?:has? to |have to )?pay\s*$',p.text[:r.start]):
        return None
    if not _has(r'\b(?:pay|paid|price|cost)\b',p.question):
        return None
    money=[a for a in amounts if a.kind=='money' or re.match(r'\s+dollars?\b',p.text[a.end:])]
    if len(money)!=1:
        return None
    value=money[0].value*r.value
    if len(amounts)==2:
        count=next(a for a in amounts if a!=money[0])
        if not _has(r'\b(?:package|pack|bundle|each|per|every)\b',p.text):
            return None
        value*=count.value
    return _result(p,value,'Apply the payable percentage to the full cost')


def _population_change(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=2:
        return None
    a,b=amounts; r=rates[0]
    if not a.start<r.start<b.start or not _has(r'\b(?:new|additional|more)\b',p.text[max(r.end,b.start-20):b.end+30]):
        return None
    if not _has(r'\b(?:join|joins|joined|begin|arriv\w*|added|add|enroll\w*)\b',_clause(p.text,b.start,b.end)):
        return None
    label=_label(p,r)
    added=_clause(p.text,b.start,b.end)
    if _has(r'\bpercent(?:age)?\b',p.question):
        # Only the denominator changes when the arrivals are the opposite group.
        if _opposite(label,added) and _words(label)&_words(p.question):
            return _result(p,100*a.value*r.value/(a.value+b.value),'Original selected count / expanded total x 100')
    elif _words(label)&_words(p.question) and not _opposite(label,added):
        if _words(label)&_words(added) or _has(r'\b(?:foreign|from other countries)\b',label) and _has(r'\bforeign\b',added):
            return _result(p,a.value*r.value+b.value,'Original selected count plus new members of that category')
    return None


def _income_deductions(p,rates,amounts):
    if not 1<=len(rates)<=3 or len(amounts)!=2 or not _has(r'\b(?:take home|left|remaining)\b',p.question):
        return None
    if not _has(r'\b(?:salary|income|earns?|makes|paid|receives?)\b',p.body):
        return None
    a,b=amounts
    if not a.start<rates[0].start<b.start or any(not _has(r'\b(?:tax\w*|healthcare|insurance|deduct\w*|dues|loses|charity)\b',_clause(p.text,r.start,r.end)) for r in rates):
        return None
    if not all(n.kind=='money' or re.match(r'\s*\$|\s+dollars?\b',p.text[n.end:]) for n in amounts):
        return None
    if _has(r'\b(?:remaining|rest|after tax)\b',p.text[rates[0].end:rates[-1].end]):
        return None
    return _result(p,a.value*(1-sum((r.value for r in rates),Fraction(0)))-b.value,'Income minus percentage deductions of that income and fixed dues')


def _relative_price(p,rates,amounts):
    if len(rates)!=1:
        return None
    r=rates[0]
    # Dimensions of a priced item are descriptive when its price is explicit.
    money=[a for a in amounts if a.kind=='money']
    if len(money)==1 and len(amounts)==3:
        extras=[a for a in amounts if a not in money]
        if not re.fullmatch(r'\s+by\s+',p.text[extras[0].end:extras[1].start]):
            return None
        if not _has(r'\b(?:size|dimensions|measures|measuring)\b',p.body):
            return None
        amounts=money
    if len(amounts)!=1:
        return None
    a=amounts[0]
    if not _has(r'^\s+(?:more expensive|cheaper|higher cost)\b',p.text[r.end:]) or not _has(r'\b(?:pay|paid|price|cost)\b',p.question):
        return None
    if _has(r'\b(?:original|initial|previous price|before the)\b',p.question):
        return None
    # A calendar reference such as "the day before" does not ask for an
    # original price: the rate names which period is more expensive.
    if not (r.start<a.start and _has(r'\b(?:weekends?|holidays?|evenings?)\b',_clause(p.text,r.start,r.end)) or len(money)==1 and len(p.numbers)>2):
        return None
    f=1-r.value if _has(r'^\s+cheaper\b',p.text[r.end:]) else 1+r.value
    return _result(p,a.value*f,'Known regular price times the stated price factor')


def _successive_ratio(p,rates,amounts):
    if len(rates)!=2 or len(amounts)!=1 or not _has(r'\bpercent(?:age)?\b',p.question):
        return None
    if not _has(r'\b(?:starting|original|initial)\b',p.question):
        return None
    factors=[]
    for r in rates:
        prefix=p.text[max(0,r.start-55):r.start]
        if re.search(r'\b(?:increase[ds]?|grew|raise[ds]?)\b[^.;!?]*\bby\s*$',prefix):
            factors.append(1+r.value)
        elif re.search(r'\b(?:decrease[ds]?|reduce[ds]?|fell)\b[^.;!?]*\bby\s*$',prefix):
            factors.append(1-r.value)
        else:
            return None
    return _result(p,100*factors[0]*factors[1],'Final / starting balance x 100 after successive changes')



def _portion_conversion(p,rates,amounts):
    """Convert a portion of a whole through an explicit amount per piece."""
    if len(rates)!=1 or len(amounts)!=2:
        return None
    a,b=amounts
    if not _unit(p,a) or _unit(p,a)!=_unit(p,b):
        return None
    for per,whole in ((a,b),(b,a)):
        before=re.split(r'[.;!?]',p.text[:per.start])[-1]
        m=re.search(r'\b(?:each|every)\s+([a-z]+)(?:\s+of\s+[a-z]+)?\s+(?:has|contains|weighs|needs|takes|costs)\s*$',before)
        if not m or _singular(m.group(1)) not in _words(p.question) or per.value<=0:
            continue
        if not _has(r'\b(?:total|every|each|whole|entire)\b',_clause(p.text,whole.start,whole.end)):
            continue
        return _result(p,whole.value/per.value*rates[0].value,'Whole amount / amount per piece, times the selected share')
    return None


def _meal_total(p,rates,amounts):
    if len(rates)!=1:
        return None
    money=[a for a in amounts if a.kind=='money']
    counts=[a for a in amounts if a.kind!='money']
    if not 2<=len(money)<=6:
        return None
    for c in counts:
        if not (c.start<money[0].start and re.match(r'\s+(?:best )?friends\b',p.text[c.end:]) and c.value+1==len(money)):
            return None
    amounts=money
    r=rates[0]
    if not _has(r'\b(?:tips?|tax|service charge)\b',_clause(p.text,r.start,r.end)):
        return None
    if not _has(r'\b(?:meal|dinner|bill|food|restaurant|waiter|server)\b',p.text):
        return None
    if not _has(r'\b(?:price|cost|pay|paid|tips?|bill)\b',p.question):
        return None
    total=Fraction(0)
    # Explicit named participants can supply the count for "each entree" or
    # "split evenly". No particular name or number of diners is assumed.
    first=re.split(r'[.!?]',p.text)[0]
    party=re.match(r"^([a-z]+(?:,\s*[a-z]+)*(?:,? and [a-z]+))\s+(?:went|decided|go|are|were)\b",first)
    diners=len(re.findall(r'[a-z]+',party.group(1).replace(' and ',','))) if party else None
    for a in amounts:
        clause=_clause(p.text,a.start,a.end)
        if not _has(r'\b(?:orders?|cost|costs|was|were|worth|paid|is)\b',clause):
            return None
        multiplier=1
        local_prefix=re.split(r'\band\b',clause[:clause.find(a.raw.lower())])[-1]
        if _has(r'\beach\b',local_prefix):
            if not diners or not _has(r"\beach of (?:their|the)\b",clause):
                return None
            multiplier=diners
        total+=a.value*multiplier
    if _has(r'\b(?:split|evenly|equally)\b',p.question) and _has(r'\b(?:each|per person)\b',p.question):
        # Separate per-person orders also identify a diner count.
        if not diners or any(_has(r'\beach\b',_clause(p.text,a.start,a.end)) for a in amounts):
            return None
        return _result(p,total*r.value/diners,'Tip on the combined bill divided equally among the diners')
    if not _has(r'\b(?:total|entire|including|with|after|final)\b',p.question):
        return None
    return _result(p,total*(1+r.value),'Combine the meal prices, then add the stated tip or tax')


def _markup_total(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=2:
        return None
    money=[a for a in amounts if a.kind=='money']
    if len(money)!=1:
        return None
    price=money[0];count=next(a for a in amounts if a!=price);r=rates[0]
    if not re.match(r'\s+(?:each|per)\b',p.text[price.end:]):
        return None
    if not _has(r'\b(?:sells?|selling|sold)\b',p.body) or not re.match(r'\s+(?:higher|more|profit|markup)\b',p.text[r.end:]):
        return None
    if not _has(r'\b(?:profit|benefit|give back)\b',p.question):
        return None
    return _result(p,price.value*count.value*r.value,'Number sold times the markup earned on each item')


def _temporal_inverse(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=1:
        return None
    r=rates[0];a=amounts[0]
    m=re.match(r'\s+(less|more|lower|higher) than (?:what|the amount) (.+?)(?:[.;!?]|$)',p.text[r.end:])
    if not m or not _has(r'\b(?:ago|previously|last|before)\b',m.group(2)):
        return None
    # Query must name the same earlier period, excluding the comparison words.
    period=re.search(r'\b(?:[a-z]+ days? ago|last [a-z]+|previous [a-z]+)\b',m.group(2))
    if not period or period.group() not in p.question:
        return None
    factor=1-r.value if m.group(1) in ('less','lower') else 1+r.value
    if factor<=0:
        return None
    return _result(p,a.value/factor,'Known later amount divided by its percentage of the earlier amount')


def _basic_price(p,rates,amounts):
    """Ignore only explicit duration labels when a price is already known."""
    if len(rates)!=1 or not 1<=len(amounts)<=2:
        return None
    if _has(r'\b(?:twice|thrice|double[ds]?|triple[ds]?|times)\b',p.body):
        return None
    money=[a for a in amounts if a.kind=='money']
    if len(money)!=1 or not _has(r'\b(?:salary|cost|price|pay|paid|bill|value)\b',p.question):
        return None
    for a in amounts:
        if a in money:
            continue
        before,after=p.text[:a.start],p.text[a.end:]
        if re.match(r'\s+(?:cm|inches|feet|meters|centimeters)\s+(?:high|tall|long|wide)\b',after):
            continue
        if re.match(r'-year\s+subscription\b',after):
            continue
        if re.match(r'\s+years?\b',after) and _has(r'\b(?:working|worked|employed)\b',_clause(p.text,a.start,a.end)):
            continue
        return None
    from .percentages_r04_a6 import _factor
    r=rates[0];f=_factor(p,r)
    if f is None or _has(r'\bthan\b',_clause(p.text,r.start,r.end)):
        return None
    if _has(r'\b(?:tax|tip|interest|savings|save|bonus|discount amount|how much more|how much less)\b',p.question) and not _has(r'\b(?:including|after|with|total|price|cost|bill|salary)\b',p.question):
        return None
    if _has(r'\b(?:year|annual|annually)\b',p.question) and _has(r'\b(?:a month|per month|monthly)\b',p.body):
        scale=12
    else:
        scale=1
    inverse=_has(r'\b(?:original|initial|before|morning)\b',re.split(r'\bif\b',p.question)[0])
    value=money[0].value/f if inverse and f else money[0].value*f
    return _result(p,value*scale,'Apply the price factor and the requested time period')


def _unpaid_share(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=1:
        return None
    r=rates[0];a=amounts[0]
    if _has(r'\b(?:take-home|take home)\b',p.question) and _has(r'\btax\b',p.body):
        return _result(p,a.value*(1-r.value),'Income minus the tax share')
    if _has(r'\b(?:gave away|gives away|given away)\b',p.body) and _has(r'\b(?:keep|kept|left|remaining)\b',p.question):
        return _result(p,a.value*(1-r.value),'Whole minus the share given away')
    contributor=re.search(r'\b(?:friend|sister|brother|partner|insurance)\b[^.;!?]*?\b(?:pay|pays|cover|covers|contribute|contributes)\s*$',p.text[:r.start])
    completion=_has(r'\b(?:complete|rest|remaining|left)\b',p.question)
    if contributor and _has(r'\b(?:pay|paid|cost)\b',p.question) and not _has(r'\b(?:friend|sister|brother|partner|insurance)\b',p.question):
        return _result(p,a.value*(1-r.value),'Total charge minus the other contributor share')
    if completion and _has(r'\b(?:raise|pay|contribute)\b',p.question) and _has(r'\b(?:raise|pay|contribute)\b',p.body):
        return _result(p,a.value*(1-r.value),'Required total less the contribution already promised')
    return None


def _coupon_sequence(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=2 or not all(a.kind=='money' for a in amounts):
        return None
    if not _has(r'\b(?:cost|pay|price)\b',p.question):
        return None
    r=rates[0]
    if not _has(r'\bdiscount\b',_clause(p.text,r.start,r.end)):
        return None
    fixed=[]
    for a in amounts:
        before=p.text[max(0,a.start-45):a.start]
        if re.search(r'\b(?:coupon|rebate)\b[^.;!?]*$',before) or re.match(r'\s+off\b',p.text[a.end:]):
            fixed.append(a)
    if len(fixed)!=1:
        return None
    fee=fixed[0];price=next(a for a in amounts if a!=fee)
    factor=1-r.value
    if not factor:
        return None
    fixed_first=fee.start<r.start and _has(r'\badditional\b',p.text[fee.end:r.start])
    inverse=_has(r'\b(?:original|before all)\b',p.question)
    if inverse:
        value=price.value/factor+fee.value if fixed_first else (price.value+fee.value)/factor
    else:
        value=(price.value-fee.value)*factor if fixed_first else price.value*factor-fee.value
    return _result(p,value,'Apply the fixed and percentage discounts in the stated order')


def _fixed_stock(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=2:
        return None
    a,b=amounts;r=rates[0]
    if not a.start<r.start<b.start:
        return None
    if not _has(r'\b(?:left|remaining|remain|attended)\b',p.question):
        return None
    if _unit(p,a)!=_unit(p,b) and not re.match(r'\s+(?:are|were)\b',p.text[b.end:]) and not (_has(r'\bseats?\b',p.text[a.end:a.end+15]) and _has(r'\bfans?\b',p.text[b.end:b.end+15])):
        return None
    first=_clause(p.text,r.start,r.end)
    last=_clause(p.text,b.start,b.end)
    if not _has(r'\b(?:eaten|ate|lost|removed|taken|stayed home|leave|left|harvested|destroyed)\b',last):
        return None
    if _has(r'\b(?:harvested|eaten|ate|lost|removed|taken|destroyed|gave away)\b',first):
        factor=1-r.value
    elif _has(r'\b(?:sold|reserved|attending|attended)\b',first):
        factor=r.value
    else:
        return None
    return _result(p,a.value*factor-b.value,'Apply the percentage to the original stock, then subtract the separate loss')


def _fixed_comparison(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=2:
        return None
    r=rates[0]
    deltas=[]
    for a in amounts:
        m=re.match(r'\s+(?:(?:[a-z]+)\s+){0,2}?(fewer|less|more)\b',p.text[a.end:])
        if m:
            deltas.append((a,1 if m.group(1)=='more' else -1))
    if len(deltas)!=1:
        return None
    delta,sign=deltas[0];base=next(a for a in amounts if a!=delta)
    if not _has(r'\b(?:second|next|following)\b',p.question):
        return None
    if not _has(r'\b(?:first|previous|last)\b',_clause(p.text,delta.start,delta.end)):
        return None
    if _unit(p,base) not in _words(p.question):
        return None
    return _result(p,base.value*r.value+sign*delta.value,'Selected first-period amount plus the stated difference for the next period')


def _percentage_difference(p,rates,amounts):
    if rates or len(amounts)!=2 or not _has(r'\bpercent(?:age)?\b',p.question):
        return None
    a,b=amounts
    if all(n.kind=='money' for n in amounts):
        original=[n for n in amounts if re.search(r'\b(?:originally|original)[^.;!?]*$',p.text[max(0,n.start-45):n.start])]
        if len(original)==1 and _has(r'\b(?:off|discount|save|saved)\b',p.question):
            base=original[0];sale=next(n for n in amounts if n!=base)
            if base.value>0:
                return _result(p,100*(base.value-sale.value)/base.value,'Discount / original price x 100')
        if _has(r'\bdiscount\b',p.question) and _has(r'\b(?:cost|worth)\b',p.text[:a.start]) and _has(r'\bnow on sale\b',p.body) and a.value>0:
            return _result(p,100*(a.value-b.value)/a.value,'Discount / earlier regular price x 100')
        if _has(r'\b(?:increase|decrease)\b',p.question) and _has(r'\blast year\b',_clause(p.text,a.start,a.end)) and _has(r'\bthis year\b',_clause(p.text,b.start,b.end)) and a.value>0:
            return _result(p,100*abs(b.value-a.value)/a.value,'Price change / earlier price x 100')
    if _has(r'\b(?:lose|lost|loss|decrease|increase)\b',p.question) and all(n.kind=='money' for n in amounts):
        if _has(r'\b(?:initial|original)\b',p.question) and _has(r'\b(?:bought|paid|cost)\b',_clause(p.text,a.start,a.end)) and _has(r'\b(?:sold|sells?|resold)\b',_clause(p.text,b.start,b.end)) and a.value:
            return _result(p,100*abs(a.value-b.value)/a.value,'Price difference / original price x 100')
    if not _has(r'\bdifference\b',p.question):
        return None
    reference=re.search(r'(?:as a percentage of|percent(?:age)? of)\s+(.*)',p.question)
    if not reference:
        return None
    labels=[_words(re.split(r'[.;!?]|\b(?:while|and|but)\b',p.text[:n.start])[-1]) for n in amounts]
    common=labels[0]&labels[1]
    chosen=[i for i,label in enumerate(labels) if (label-common)&_words(reference.group(1))]
    if len(chosen)!=1 or not amounts[chosen[0]].value:
        return None
    return _result(p,100*abs(a.value-b.value)/amounts[chosen[0]].value,'Difference / explicitly requested reference amount x 100')


def _weighted_average(p,rates,amounts):
    if len(rates)!=3 or amounts or not _has(r'\baverage\b',p.question):
        return None
    share,left,right=rates
    if not _has(r'\b(?:rest|remaining)\b',p.body) or not _has(r'\b(?:every|each)\b',p.text[share.end:left.start]):
        return None
    from .percentages_r02_a3 import _words
    category=_words(_label(p,share))
    left_clause=_clause(p.text,left.start,left.end)
    if not category&_words(left_clause):
        return None
    return _result(p,100*(share.value*left.value+(1-share.value)*right.value),'Weighted average of the two groups using their complementary shares')


def _equal_cost(p,rates,amounts):
    if len(rates)!=2 or len(amounts)!=1:
        return None
    a=amounts[0];r,s=rates
    if not r.start<a.start<s.start or not _has(r'\b(?:income|salary)\b',p.body):
        return None
    if not _has(r'\b(?:increased?|raise[ds]?)\b',_clause(p.text,a.start,a.end)):
        return None
    # The same named expense appears on both sides; no changed rent/fee.
    first=_words(_clause(p.text,r.start,r.end))-{'income','monthly','salary'}
    second=_words(_clause(p.text,s.start,s.end))-{'income','monthly','salary'}
    if not first&second or r.value<=s.value:
        return None
    original=s.value*a.value/(r.value-s.value)
    if _has(r'\b(?:previous|original|before|old)\b',p.question):
        return _result(p,original,'Equal expense before and after the raise: old share x old income = new share x new income')
    if _has(r'\b(?:new|now|current)\b',p.question):
        return _result(p,original+a.value,'Recover the original income from equal expenses, then add the raise')
    return None


def _inclusion_exclusion(p,rates,amounts):
    if rates or len(amounts)!=3 or not all(0<a.value<1 for a in amounts):
        return None
    if not _has(r'\bpercent(?:age)?\b',p.question) or not _has(r'\b(?:either|some way|at least one|or)\b',p.question):
        return None
    if not _has(r'\bboth\b',_clause(p.text,amounts[-1].start,amounts[-1].end)):
        return None
    value=amounts[0].value+amounts[1].value-amounts[2].value
    if not 0<=value<=1:
        return None
    return _result(p,100*value,'Add both category shares and subtract the overlap once')


def _same_bonus_rate(p,rates,amounts):
    if rates or len(amounts)!=3 or not all(a.kind=='money' for a in amounts):
        return None
    if not _has(r'\bsame percentage\b',p.body) or not _has(r'\bbonus\b',p.body) or not _has(r'\b(?:total|both|adding)\b',p.question):
        return None
    old,bonus,new=amounts
    if not re.match(r'\s+bonus\b',p.text[bonus.end:]) or old.value<=0:
        return None
    if not _has(r'\blast year\b',_clause(p.text,old.start,old.end)) or not _has(r'\bthis year\b',_clause(p.text,new.start,new.end)):
        return None
    return _result(p,new.value*(1+bonus.value/old.value),'Infer the unchanged bonus rate from last year and apply it to this year')


def _inverse_share(p,rates,amounts):
    if len(rates)!=1 or not 1<=len(amounts)<=2:
        return None
    r=rates[0]
    if len(amounts)==1:
        a=amounts[0]
        if not r.start<a.start or not re.match(r'\s+(?:of )?(?:her |his |their |the )?(?:body weight|capacity)\b',p.text[r.end:]):
            return None
        if not _has(r'\b(?:weigh|capacity)\b',p.question):
            return None
        return _result(p,a.value/r.value,'Known portion divided by its share of the whole')
    a,b=amounts
    if not a.start<r.start<b.start or not re.match(r'\s+(?:the )?capacity\b',p.text[r.end:]):
        return None
    if not _has(r'\btotal capacity\b',p.question) or not _has(r'\bsuch\b',p.text[b.end:b.end+15]):
        return None
    return _result(p,a.value/r.value*b.value,'Recover one full capacity and multiply by the number of containers')


def _changed_category_percent(p,rates,amounts):
    if rates or len(amounts)!=3 or not _has(r'\bpercent(?:age)?\b',p.question):
        return None
    a,b,delta=amounts
    if not all(n.value>=0 for n in amounts) or any(n.kind=='money' for n in amounts):
        return None
    unit=_unit(p,delta)
    if unit not in (_unit(p,a),_unit(p,b)):
        return None
    prefix=p.text[max(0,delta.start-45):delta.start]
    if _has(r'\b(?:adds?|added|buys?|bought|joins?|joined)\b',prefix):
        sign=1
    elif _has(r'\b(?:removes?|removed|ate|eats?|lost|loses)\b',prefix):
        sign=-1
    elif _has(r'\b(?:added|bought|joined)\b',_clause(p.text,delta.start,delta.end)):
        sign=1
    else:
        return None
    totals=[a.value,b.value]
    totals[0 if _unit(p,a)==unit else 1]+=sign*delta.value
    selected=[i for i,n in enumerate((a,b)) if _unit(p,n) in _words(p.question)]
    if len(selected)!=1 or sum(totals)<=0 or min(totals)<0:
        return None
    return _result(p,100*totals[selected[0]]/sum(totals),'Update the changed category, then selected count / new total x 100')


def _named_score_percent(p,rates,amounts):
    if rates or len(amounts)!=2 or not _has(r'\bpercent(?:age)?\b',p.question):
        return None
    if _has(r'\b(?:more|less|fewer|lost|ate|left|remaining|difference|each|per)\b',p.body.replace('each other','')):
        return None
    owners=[]
    for n in amounts:
        prefix=re.split(r'[.;!?]|\band\b',p.text[:n.start])[-1]
        m=re.search(r'([a-z]+)\s+(?:has |have |had )?(?:won|scored|collected|earned)\s*$',prefix)
        if not m:
            return None
        owners.append(m.group(1))
    selected=[i for i,owner in enumerate(owners) if owner in _words(p.question)]
    total=sum((n.value for n in amounts),Fraction(0))
    if len(selected)!=1 or total<=0:
        return None
    return _result(p,100*amounts[selected[0]].value/total,'Selected owner score / combined scores x 100')


def _irregular_change(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=1:
        return None
    r=rates[0];a=amounts[0]
    prefix=p.text[max(0,r.start-30):r.start]
    if re.search(r'\b(?:fell|dropped|shrank)(?: by)?\s*$',prefix):
        factor=1-r.value
    elif re.search(r'\b(?:rose|grew)(?: by)?\s*$',prefix):
        factor=1+r.value
    else:
        return None
    inverse=_has(r'\b(?:before|morning|original|initial)\b',p.question)
    if factor<=0:
        return None
    return _result(p,a.value/factor if inverse else a.value*factor,'Undo the change for the earlier amount, or apply it for the later amount')


def _whole_share(p,rates,amounts):
    """Separate an explicitly counted whole from an explicitly counted part."""
    if len(rates)!=1 or len(amounts)!=1 or _has(r'\bpercent(?:age)?\b',p.question):
        return None
    r=rates[0];a=amounts[0]
    from .percentages_r04_a6 import _factor
    # A vote about an increase is a share, not an increase of the voters.
    tail=p.text[r.end:]
    subset=re.match(r'\s+of\b',tail)
    if _factor(p,r) is not None and not subset:
        return None
    label=_label(p,r)
    if _has(r'\binvalid\b',_clause(p.text,r.start,r.end)):
        label+=' invalid'
    count_before=re.split(r'[.;!?]|\band\b',p.text[:a.start])[-1]
    known_whole=(a.start<r.start or bool(re.fullmatch(r'\s+of (?:the |all (?:the )?)?',p.text[r.end:a.start])))
    known_whole=known_whole or bool(re.search(r'\b(?:there (?:are|were|was)|(?:has|have|had)|in total[^.;!?]*)\s*$',count_before))
    if not known_whole:
        count_label=_words(_clause(p.text,a.start,a.end))
        distinctive=_words(label)-_words(_unit(p,a))-{'student','person','number','class','school'}
        if distinctive & count_label and not distinctive&_words(p.question) and _has(r'\b(?:total|all|go to|entire|school|class)\b',p.question):
            return _result(p,a.value/r.value,'Known selected group divided by its fraction of the whole')
        return None
    if _has(r'\b(?:take-home|take home)\b',p.question) and _has(r'\btax\b',p.body):
        factor=1-r.value
    elif _opposite(label,p.question) or _has(r'\b(?:unfilled|unread|unsold|unspent|unbroken|not|remaining)\b',p.question):
        factor=1-r.value
    elif _words(label)&_words(p.question):
        factor=r.value
    else:
        return None
    return _result(p,a.value*factor,'Counted whole times the requested share or its complement')


def _direct_change(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=1:
        return None
    from .percentages_r04_a6 import _factor
    r=rates[0];a=amounts[0];f=_factor(p,r)
    if f is None or f<=0 or _has(r'\b(?:twice|double|triple|thrice|times|each|every|per)\b',p.body):
        return None
    if _has(r'^\s+of\b',p.text[r.end:]):
        return None
    inverse=_has(r'\b(?:last year|previous year|original|initial|before the)\b',p.question)
    if inverse and _has(r'\b(?:this year|now|current|new)\b',_clause(p.text,a.start,a.end)):
        return _result(p,a.value/f,'Known current amount divided by the percentage change factor')
    # A desired change to a single existing stock is not a two-stock total.
    if a.start<r.start and _has(r'\b(?:plans?|wants?|hopes?|aims?)\b',p.body) and not _has(r'\b(?:than|another|second|other)\b',p.body):
        return _result(p,a.value*f,'Existing stock times the desired change factor')
    if a.kind=='money' and _has(r'\bprofit\b',p.body) and _has(r'\bsell\b',p.question) and not _has(r'\bprofit\b',p.question):
        return _result(p,a.value*f,'Cost plus the specified profit margin on cost')
    return None


def _change_then_loss(p,rates,amounts):
    if len(rates)!=2 or len(amounts)!=1 or not _has(r'\b(?:current|now|left|remaining|final)\b',p.question):
        return None
    from .percentages_r04_a6 import _factor
    first,second=rates;a=amounts[0]
    f=_factor(p,first)
    if re.match(r'\s+of\b',p.text[first.end:]):
        return None
    if f is None or not a.start<first.start<second.start:
        return None
    if not _has(r'\b(?:moved away|left|lost|removed|eaten|destroyed|sold)\b',_clause(p.text,second.start,second.end)):
        return None
    return _result(p,a.value*f*(1-second.value),'Apply the first change, then remove a share of the changed amount')


def _percent_of_explicit_total(p,rates,amounts):
    if rates or not 3<=len(amounts)<=5 or not _has(r'\bpercent(?:age)?\b',p.question):
        return None
    a=amounts[0]
    if not re.search(r'\bthere (?:are|were|was)\s*$',p.text[:a.start]):
        return None
    if not all(_unit(p,n)==_unit(p,a) for n in amounts):
        return None
    rest=re.search(r'\bthe rest\b([^.;!?]+)',p.body)
    if not rest or not _words(rest.group(1))&_words(p.question) or a.value<=0:
        return None
    remaining=a.value-sum((n.value for n in amounts[1:]),Fraction(0))
    return _result(p,100*remaining/a.value,'Subtract counted categories from the explicit total, then divide by that total')


def _gross_income(p,rates,amounts):
    if len(rates)!=1 or not 2<=len(amounts)<=4 or not all(a.kind=='money' for a in amounts):
        return None
    if not _has(r'\bgross (?:salary|income|pay)\b',p.question):
        return None
    net=amounts[0];r=rates[0]
    if not _has(r'\btake-home\b',_clause(p.text,net.start,net.end)) or not _has(r'\bof (?:his |her |their )?gross\b',p.text[r.end:]):
        return None
    if not all(_has(r'\b(?:tax|taxes|deduction|bill)\b',_clause(p.text,a.start,a.end)) for a in amounts[1:]):
        return None
    if r.value>=1:
        return None
    return _result(p,sum((a.value for a in amounts),Fraction(0))/(1-r.value),'Add back fixed deductions and divide by the retained fraction of gross income')


def _loan_cost(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=2 or not all(a.kind=='money' for a in amounts):
        return None
    if not _has(r'\b(?:loan|borrow|bank)\b',p.body) or not _has(r'\btotal\b',p.question):
        return None
    price,loan=amounts;r=rates[0]
    if not price.start<r.start<loan.start or not _has(r'\bbank\b',_clause(p.text,loan.start,loan.end)) or price.value<loan.value:
        return None
    return _result(p,price.value+loan.value*r.value,'Purchase price plus interest on only the borrowed portion')


def _simple_interest(p,rates,amounts):
    if len(rates)!=1 or not 2<=len(amounts)<=3:
        return None
    money=[a for a in amounts if a.kind=='money']
    years=[a for a in amounts if re.match(r'\s+years?\b',p.text[a.end:])]
    if len(money)!=1 or len(years)!=len(amounts)-1 or len({a.value for a in years})!=1:
        return None
    if not _has(r'\binterest\b',p.body) or not _has(r'\b(?:original|simple)\b',p.body):
        return None
    interest=money[0].value*rates[0].value*years[0].value
    if _has(r'\b(?:have|total|including|balance)\b',p.question):
        interest+=money[0].value
    return _result(p,interest,'Annual simple interest on the original principal for the stated duration')


def _selected_disjoint_shares(p,rates,amounts):
    if not 2<=len(rates)<=4 or len(amounts)!=1:
        return None
    if sum((r.value for r in rates),Fraction(0))>1 or not _has(r'\b(?:and|or)\b',p.question):
        return None
    a=amounts[0]
    if not _has(r'\b(?:rest|remaining|remainder)\b',p.body):
        return None
    if a.start>rates[0].start and not _has(r'\b(?:interviewed|surveyed|total|there were|there are)\b',_clause(p.text,a.start,a.end)):
        return None
    labels=[_words(_label(p,r)) for r in rates]
    common=set.intersection(*labels)
    selected=[i for i,label in enumerate(labels) if (label-common)&_words(p.question)]
    if not selected:
        return None
    if any(re.match(r'\s+of (?:those|these|the remaining|the rest)\b',p.text[r.end:]) for r in rates[1:]):
        return None
    return _result(p,a.value*sum((rates[i].value for i in selected),Fraction(0)),'Whole times the sum of the requested disjoint category shares')


def _implicit_multiple_share(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=1:
        return None
    r=rates[0];a=amounts[0]
    m=re.search(r'\b(doubled|tripled) in value\b',p.body)
    if not m or not re.match(r'\s+of\b',p.text[r.end:]):
        return None
    if not _has(r'\b(?:sell|sold|worth|price|cost)\b',p.question) or a.kind!='money':
        return None
    return _result(p,a.value*(2 if m.group(1)=='doubled' else 3)*r.value,'Changed total value times the share sold')


def _share_purchase(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=2:
        return None
    money=[a for a in amounts if a.kind=='money']
    if len(money)!=1:
        return None
    price=money[0];count=next(a for a in amounts if a!=price);r=rates[0]
    if not count.start<r.start<price.start or not _has(r'\b(?:each|per)\b',_clause(p.text,price.start,price.end)):
        return None
    if not _has(r'\b(?:refunded|refund|returned|return)\b',p.question):
        return None
    if not _has(r'\b(?:expired|broken|defective|spoiled|damaged|returned)\b',_label(p,r)):
        return None
    return _result(p,count.value*r.value*price.value,'Number of items times the returned share times the price per item')


def _percentage_capacity(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=2:
        return None
    r=rates[0];a,b=amounts
    if not a.start<r.start<b.start or not _unit(p,a) or _unit(p,a)!=_unit(p,b):
        return None
    if not _has(r'\b(?:more|additional)\b',p.question) or not _has(r'\b(?:miss|skip|allowed|maximum|limit)\b',p.body):
        return None
    if not _has(r'\b(?:missed|used|already)\b',_clause(p.text,b.start,b.end)):
        return None
    return _result(p,a.value*r.value-b.value,'Percentage allowance minus the amount already used')


def _tax_or_finance_total(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=1 or amounts[0].kind!='money':
        return None
    r=rates[0];a=amounts[0]
    clause=_clause(p.text,r.start,r.end)
    if not _has(r'\b(?:tax|finance charge)\b',clause):
        return None
    if _has(r'\b(?:take-home|take home|tax alone|original|before)\b',p.question):
        return None
    if not _has(r'\b(?:pay|paid|spend|cost|price)\b',p.question):
        return None
    if _has(r'\b(?:including|total|settle|with|after)\b',p.question) or _has(r'\bfinance charge\b',clause):
        return _result(p,a.value*(1+r.value),'Base charge plus its percentage tax or finance charge')
    return None


def _known_price_fraction(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=1 or amounts[0].kind!='money':
        return None
    r=rates[0];a=amounts[0]
    if re.match(r'\s+of (?:the )?original price\b',p.text[r.end:]) and _has(r'\boriginal price\b',p.question):
        return _result(p,a.value/r.value,'Known price divided by its fraction of the original price')
    if _has(r'\bdiscount\b',_clause(p.text,r.start,r.end)) and _has(r'\b(?:pay|paid|cost)\b',p.question):
        if re.search(r'\bdiscount[^.;!?]*\b(?:is|was|of)\s*$',p.text[max(0,a.start-65):a.start]) and r.end<a.start:
            return _result(p,a.value/r.value*(1-r.value),'Discount amount / discount rate, less the discount')
    if _has(r'\bmore\b',p.question) and _has(r'\bneed\b',p.question) and _has(r'\balready has\b',p.text[max(0,r.start-35):r.start]):
        return _result(p,a.value*(1-r.value),'Full price less the share already available')
    return None


def _category_ratio(p,rates,amounts):
    if not 2<=len(rates)<=4 or len(amounts)!=1:
        return None
    a=amounts[0]
    if a.start<rates[-1].start or sum((r.value for r in rates),Fraction(0))!=1:
        return None
    labels=[_words(_label(p,r)) for r in rates]
    common=set.intersection(*labels)
    known=_words(re.split(r'[.;!?]',p.body[a.end:])[0])
    anchor=[i for i,label in enumerate(labels) if (label-common)&known]
    target=[i for i,label in enumerate(labels) if (label-common)&_words(p.question)]
    if len(anchor)!=1 or len(target)!=1:
        return None
    return _result(p,a.value/rates[anchor[0]].value*rates[target[0]].value,'Known category / its share times the requested category share')


def _share_equally(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=2 or not _has(r'\beach\b',p.question):
        return None
    r=rates[0]
    if not _has(r'\b(?:equal|equally|receive|receives)\b',p.text):
        return None
    for count,total in ((amounts[0],amounts[1]),(amounts[1],amounts[0])):
        if count.kind=='money' or count.value<=0 or not _unit(p,count) or _unit(p,count) not in _words(p.question):
            continue
        if not _has(r'\b(?:total|raised|donated|charity|all)\b',_clause(p.text,total.start,total.end)):
            continue
        return _result(p,total.value*r.value/count.value,'Selected share of the whole divided equally among the recipients')
    return None


def _annual_retention(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=1 or not _has(r'\bpercent(?:age)?\b',p.question):
        return None
    r=rates[0];period=amounts[0]
    if not re.match(r'\s+years?\b',p.text[period.end:]) or not _has(r'\b(?:each|every) year\b',p.body):
        return None
    if not _has(r'\b(?:evaporates?|lost|loses|shrinks?|decreases?)\b',_clause(p.text,r.start,r.end)):
        return None
    if not _has(r'\b(?:left|remaining)\b',p.question) or period.value.denominator!=1 or not 0<=period.value<=100:
        return None
    return _result(p,100*(1-r.value)**int(period.value),'Compound the retained fraction for the stated number of years')


def _exam_target(p,rates,amounts):
    if amounts or len(rates)<3 or not _has(r'\b(?:average|grade)\b',p.body):
        return None
    from ._fractions_common import _ORDINALS
    ordinal=re.search(r'\b('+'|'.join(_ORDINALS)+r')\b',p.question)
    if not ordinal or _ORDINALS[ordinal.group() ]!=len(rates) or not _has(r'\b(?:test|exam)\b',p.question):
        return None
    target=rates[-1].value
    return _result(p,100*(len(rates)*target-sum((r.value for r in rates[:-1]),Fraction(0))),'Required total marks minus the marks on the completed tests')


def _two_period_total(p,rates,amounts):
    if len(rates)!=1 or not 1<=len(amounts)<=2:
        return None
    r=rates[0]
    m=re.match(r'\s+(more|less|fewer)\b',p.text[r.end:])
    if not m or not _has(r'\bthan\b',_clause(p.text,r.start,r.end)):
        return None
    factor=1+r.value if m.group(1)=='more' else 1-r.value
    a=amounts[0]
    if len(amounts)==2:
        duration=amounts[1]
        if duration.value!=2 or _unit(p,duration) not in ('day','week','month','year'):
            return None
    # Repeated weekday names explicitly identify the two periods being added.
    days=r'(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)'
    clause=_clause(p.text,r.start,r.end)
    d=re.search(r'\bon ('+days+r')\b.*\bthan\b.*\bon ('+days+r')\b',clause)
    if not d:
        return None
    if _has(r'\b(?:total|both|together)\b',p.question) and a.start<r.start:
        return _result(p,a.value*(1+factor),'First period plus its percentage-related second period')
    if a.start>r.start and _has(r'\btotal\b',_clause(p.text,a.start,a.end)):
        if d.group(2) in p.question:
            return _result(p,a.value/(1+factor),'Combined total divided by the sum of the two period factors')
        if d.group(1) in p.question:
            return _result(p,a.value/(1+factor)*factor,'Recover the first period from the total, then apply the second-period factor')
    return None


def _joint_complement(p,rates,amounts):
    if len(rates)!=2 or amounts or not _has(r'\bpercent(?:age)?\b',p.question):
        return None
    if not _has(r"\b(?:not|never|doesn't|don't)\b",p.question) or _has(r'\band\b',p.question):
        return None
    first,second=rates
    if not re.match(r'\s+of the time\b',p.text[second.end:]):
        return None
    if not _words(_clause(p.text,second.start,second.end))&_words(p.question):
        return None
    before=_words(_clause(p.text,first.start,first.end))
    base=re.match(r'\s+of the time (.*?)[,.;!?]',p.text[second.end:])
    if not base or not before&_words(base.group(1)):
        return None
    return _result(p,100*(1-first.value*second.value),'Complement of the probability of both linked events')


def _profit_sales_count(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=2 or not all(a.kind=='money' for a in amounts):
        return None
    r=rates[0]
    if not _has(r'\bexpenses\b',_clause(p.text,r.start,r.end)) or not re.match(r'\s+of total sales\b',p.text[r.end:]):
        return None
    if not _has(r'\b(?:how many|sell)\b',p.question) or not _has(r'\bprofit\b',p.question) or r.value>=1:
        return None
    prices=[a for a in amounts if re.match(r'\s+(?:each|per)\b',p.text[a.end:])]
    if len(prices)!=1 or prices[0].value<=0:
        return None
    profit=next(a for a in amounts if a!=prices[0])
    return _result(p,profit.value/((1-r.value)*prices[0].value),'Required profit divided by net profit per item')


def _tip_from_change(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=2 or not all(a.kind=='money' for a in amounts):
        return None
    r=rates[0]
    if not _has(r'\btax\b',_clause(p.text,r.start,r.end)) or not _has(r'\btip\b',p.question) or not _has(r'\bkeep the change\b',p.body):
        return None
    bill,tender=amounts
    if not bill.start<r.start<tender.start or not _has(r'\b(?:check|cost|bill)\b',_clause(p.text,bill.start,bill.end)):
        return None
    return _result(p,tender.value-bill.value*(1+r.value),'Payment less the bill and its sales tax')


def _after_tax_inverse(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=2:
        return None
    r=rates[0]
    money=[a for a in amounts if a.kind=='money']
    fractions=[a for a in amounts if 0<a.value<1]
    if len(money)!=1 or len(fractions)!=1:
        return None
    tax=fractions[0]
    if not re.match(r'\s+of (?:his |her |their )?after-tax income\b',p.text[r.end:]):
        return None
    if not _has(r'\b(?:before tax|before taxes|gross)\b',p.question) or not _has(r'\b(?:tax|taxes)\b',_clause(p.text,tax.start,tax.end)):
        return None
    return _result(p,money[0].value/r.value/(1-tax.value),'Recover after-tax income from the payment share, then undo income tax')


def _related_total(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=1 or not _has(r'\btotal\b',p.question):
        return None
    r=rates[0];a=amounts[0]
    if not re.match(r'\s+of the time (?:it|he|she|they) (?:traveled|spent|took)\b',p.text[r.end:]):
        return None
    if _unit(p,a) not in ('hour','minute','day','week','month'):
        return None
    return _result(p,a.value*(1+r.value),'Known duration plus the duration that is its stated percentage')


def _benefit_comparison(p,rates,amounts):
    if len(rates)!=1 or len(amounts)!=2:
        return None
    a,b=amounts;r=rates[0]
    if not a.start<b.start<r.start or _unit(p,a)!=_unit(p,b):
        return None
    if not _has(r'\b(?:versus|compared to|rather than)\b',p.question) or not _has(r'\bmore\b',p.question):
        return None
    if not _has(r'\badds?\b',_clause(p.text,b.start,b.end)) or not _has(r'\badds?\b',_clause(p.text,r.start,r.end)):
        return None
    return _result(p,a.value*r.value-b.value,'Percentage benefit minus the alternative fixed benefit')


def _missing_class_score(p,rates,amounts):
    if len(rates)!=2 or len(amounts)!=1 or not _has(r'\bscore\b',p.question):
        return None
    n=amounts[0]
    if n.value<1 or n.value.denominator!=1 or not _has(r'\b(?:everyone|all)[^.;!?]*except\b',p.body):
        return None
    target,current=rates
    if not _has(r'\baverage(?:d)?\b',_clause(p.text,target.start,target.end)) or not _has(r'\baverage\b',_clause(p.text,current.start,current.end)):
        return None
    value=100*(n.value*target.value-(n.value-1)*current.value)
    if not 0<=value<=100:
        return None
    return _result(p,value,'Required class total minus the total of the completed scores')

def solve(problem):
    if _has(r"^(?:i(?: am|'m)|we(?: are|'re))\s+(?:trying|learning|wondering)\b",problem.text.lower()):
        return None
    if not any(n.kind=='percent' for n in problem.numbers) and not _has(r'\bpercent(?:age)?\b',problem.text.lower()):
        return None
    # A historical date becomes a duration when a change repeats annually.
    # Do not discard that duration as though the rate were a one-time change.
    if _has(r'\b(?:annually|annual|each year|every year)\b',problem.body) and any(
            re.match(r'\s+years? ago\b',problem.text[n.end:].lower())
            for n in problem.numbers if n.kind!='percent'):
        return None
    p=_prepare(problem)
    rates=[n for n in p.numbers if n.kind=='percent']
    amounts=[n for n in p.numbers if n.kind!='percent']
    if any(not 0<r.value<=1 for r in rates):
        return None
    for reader in (_annual_retention,_related_total,_tax_or_finance_total,_known_price_fraction,_two_period_total,
                   _change_then_loss,_progress,_fraction_percentage,_parallel_remainder,_remainder_base,
                   _single_remainder,_nested_shares,_price_share,_population_change,
                   _income_deductions,_relative_price,_successive_ratio,_portion_conversion,
                   _meal_total,_markup_total,_temporal_inverse,_basic_price,_unpaid_share,
                   _coupon_sequence,_fixed_stock,_fixed_comparison,_percentage_difference,
                   _weighted_average,_equal_cost,_inclusion_exclusion,_same_bonus_rate,
                   _inverse_share,_changed_category_percent,_named_score_percent,_irregular_change,
                   _direct_change,_whole_share,_percent_of_explicit_total,
                   _gross_income,_loan_cost,_simple_interest,_selected_disjoint_shares,
                   _implicit_multiple_share,_share_purchase,_percentage_capacity,_category_ratio,
                   _share_equally,_exam_target,_joint_complement,_profit_sales_count,
                   _tip_from_change,_after_tax_inverse,_benefit_comparison,_missing_class_score):
        result=reader(p,rates,amounts)
        if result is not None:
            return result
    return None
