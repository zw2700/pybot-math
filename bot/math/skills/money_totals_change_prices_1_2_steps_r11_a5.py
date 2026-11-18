"""Conservative readers for money budgets, quotes, and repeated purchases.

Every rule binds all quantities to explicit transaction or unit roles.  A
quantity that cannot be explained makes the reader abstain.  No story nouns,
people, or numerical constants from training examples are used as keys.
"""
import re
from fractions import Fraction

from ..numbers import format_number
from ._money_common import (
    _numbers, _currencies, _has, _bounds, _role, _phrase, _head,
    _same, _singular, _expr, _output, _result,
)
from .money_totals_change_prices_1_2_steps_r06_a4 import _label, _unit


def _answer(p, value, expression):
    if value < 0:
        return None
    if re.match(r'how (?:many|long)\b', p.question) and not re.match(
            r'how many (?:dollars?|cents?|euros?)\b', p.question):
        return value, 'Calculation: {} = {}.'.format(expression, format_number(value))
    result = _output(p, _result(value, expression, p))
    if re.match(r'how many cents\b', p.question) and not _has(r'\bin cents\b', p.question):
        value, working = result
        value *= 100
        return value, working + ' In cents: {}.'.format(format_number(value))
    return result


def _parts(ns):
    return ([n for n in ns if n.kind == 'money'],
            [n for n in ns if n.kind != 'money'])


def _ledger(p, ns):
    """An itemized budget, savings/gifts toward a purchase, or reverse balance."""
    t, q = p.text.lower(), p.question
    if any(n.kind != 'money' for n in ns):
        return None
    if _has(r'\b(?:each|per|every|times|twice|thrice|double[ds]?|triple[ds]?|half|discount|percent|tax|shared|split)\b', t):
        # Monthly ledgers can state every month once, without introducing a
        # multiplicative duration. All their entries describe the same month.
        without_month = re.sub(r'\bevery month\b', '', t)
        if _has(r'\b(?:each|per|every|times|twice|thrice|double[ds]?|triple[ds]?|half|discount|percent|tax|shared|split)\b', without_month):
            return None
    if _has(r'\binterest\b', t) and not _has(r'\bbefore interest\b', q):
        return None
    initial = _has(r'\b(?:beginning|initially|originally|at first|start)\b', q)
    short = (_has(r'\b(?:owe|owes|need)\b', q)
             or _has(r'\b(?:must|have to|has to)\b.*\b(?:earn|save)\b',q)
             or _has(r'\bmore\b.*\b(?:earn|save)\b|\b(?:earn|save)\b.*\bmore\b',q)) and not initial
    left = _has(r'\b(?:left|leave|remaining|change|rest|bank balance)\b', q)
    if re.match(r'how many (?!dollars?\b|cents?\b|euros?\b)',q):
        return None
    if not (initial or short or left):
        return None
    # A named second spender has a separate ledger, unlike a pronoun gift.
    owners = set(re.findall(r'\b([A-Z][a-z]+) (?:has|had|spends|spent|buys|bought)\b', p.text))
    owners -= {'He', 'She', 'They', 'If', 'Then'}
    if len(owners) > 1:
        return None
    expense, funds, final = [], [], []
    previous = None
    kept = []
    for n in ns:
        # A repeated initial payment refers back to the existing cash amount.
        lo = kept[-1].end if kept else 0
        before = t[lo:n.start]
        after = t[n.end:]
        if (_has(r'\b(?:initial|original)\s*$', before)
                and n.value in funds):
            continue
        role = _role(t, n, lo)
        if _has(r'^\s*(?:dollars?\s*)?now\b', after):
            role = 'remaining'
        elif _has(r'\b(?:retail price|price|cost)\b[^.;]*\b(?:at|is|of|was)\s*$', before):
            role = 'expense'
        elif _has(r'\b(?:saves?|saved|offered (?:him|her|them)|gave (?:him|her|them)|pays? (?:him|her|them))\s*$', before):
            role = 'income'
        elif _has(r'\b(?:writes?|wrote)\b[^.;]*\b(?:cheque|check) for\s*$', before):
            role = 'expense'
        elif _has(r'\b(?:bills? include|expenses include|payment of)\b[^.;]*$', before):
            role = 'expense'
        elif _has(r'\bgave (?:(?:his|her|their|the|a) )?(?!him\b|her\b|them\b)[a-z]+\s*$', before):
            giver = re.search(r'\b([a-z]+) (?:then )?gave\b',before)
            if giver and owners and giver.group(1) not in {'he','she','they','and','then','also'} | {name.lower() for name in owners}:
                return None
            role = 'expense'
        elif previous == 'expense' and role != 'income' and _has(r'\b(?:bills|expenses) include\b',t[:n.start]) and not _has(r'[.;]',before):
            role = 'expense'
        elif previous == 'expense' and not _has(r'[.;]', before) and _has(r',|\band\b', before):
            role = role or previous
        if role in ('expense',):
            expense.append(n.value)
        elif role in ('balance', 'income', 'tender'):
            funds.append(n.value)
        elif role == 'remaining':
            final.append(n.value)
        else:
            return None
        previous = role
        kept.append(n)
    e, f = sum(expense, Fraction(0)), sum(funds, Fraction(0))
    if initial and expense and len(final) == 1 and not funds:
        return _answer(p, e+final[0], '{} + ({})'.format(format_number(final[0]), _expr(expense)))
    if not expense or not funds or final:
        return None
    if short:
        return _answer(p, e-f, '({}) - ({})'.format(_expr(expense), _expr(funds)))
    if left:
        return _answer(p, f-e, '({}) - ({})'.format(_expr(funds), _expr(expense)))
    return None


def _weekly_purchases(p, ns):
    """One purchase per scheduled day, for a stated number of weeks."""
    t = p.text.lower()
    money, counts = _parts(ns)
    if len(money) != 1 or len(counts) not in (2, 3):
        return None
    if not _has(r'\b(?:spend|spent|pay|cost)\b', p.question):
        return None
    if _has(r'\b(?:left|remaining|more|less|free|discount|times)\b', t):
        return None
    days = [n for n in counts if _has(r'^\s+days?\s*,?\s*(?:a|per|each|every) week\b', t[n.end:])]
    weeks = [n for n in counts if _has(r'^\s+weeks?\b', t[n.end:])]
    if len(days) != 1 or len(weeks) != 1 or days[0] is weeks[0]:
        return None
    remaining = [n for n in counts if n not in days+weeks]
    party = Fraction(1)
    if remaining:
        n = remaining[0]
        if not (_has(r'\b(?:himself|herself|themselves) and\s*$', t[:n.start])
                and _has(r'^\s+(?:members|friends|colleagues|coworkers)\b', t[n.end:])):
            return None
        party += n.value
    elif not _has(r'\b(?:buys?|bought|purchases?|purchased) (?:a|an)\b', p.body):
        return None
    price = money[0]
    if remaining and not _label(p, ns, price)[1]:
        return None
    value = price.value*days[0].value*weeks[0].value*party
    return _answer(p, value, '{} * {} * {} * {}'.format(*(format_number(v) for v in
                   (price.value, days[0].value, weeks[0].value, party))))


def _party_tickets(p, ns):
    """A shared admission price for an explicitly additive party, less cash."""
    t, q = p.text.lower(), p.question
    money, counts = _parts(ns)
    if not counts or len(counts) > 3 or len(money) not in (1, 2):
        return None
    if not _has(r'\btickets?|admission|entrance\b', t):
        return None
    if _has(r'\b(?:adult.s|child.s|discount|free|less|times|twice)\b', t):
        return None
    prices = [n for n in money if _label(p, ns, n)[1] and _has(r'\b(?:cost|costs|price)\b', t[_bounds(t,n)[0]:n.start])]
    if len(prices) != 1:
        return None
    price = prices[0]
    cash = [n for n in money if n is not price]
    if cash and not _has(r'\b(?:has|had|have)\b[^.;]*$', t[:cash[0].start]):
        return None
    people = Fraction(0)
    for c in counts:
        after, before = t[c.end:], t[:c.start]
        if _has(r'^\s+of (?:his|her|their) friends\b', after) and _has(r'\b(?:him|her|himself|herself|them|themselves|[a-z]+) and (?:for )?\s*$', before):
            people += c.value+1
        elif _unit(after) in ('student', 'teacher', 'adult', 'child', 'person', 'friend', 'member'):
            people += c.value
        else:
            return None
    if cash:
        if not _has(r'\b(?:need|earn|more)\b', q):
            return None
        return _answer(p, people*price.value-cash[0].value, '{} * {} - {}'.format(
            format_number(people), format_number(price.value), format_number(cash[0].value)))
    if not _has(r'\b(?:pay|cost|spend|spent)\b', q):
        return None
    return _answer(p, people*price.value, '{} * {}'.format(format_number(people), format_number(price.value)))


def _catalog(p, ns):
    """Unit definitions may include 'one'; purchases use the later counts."""
    t = p.text.lower()
    money, counts = _parts(ns)
    if not 2 <= len(money) <= 5 or not _has(r'\b(?:spend|spent|pay|cost)\b', p.question):
        return None
    if _has(r'\b(?:more|less|left|remaining|free|discount|times|total cost was)\b', t):
        return None
    used, terms = set(), []
    for n in money:
        label, explicit = _label(p, ns, n)
        if not explicit or not label or label == '*':
            return None
        matches = [c for c in counts if _same(label, _phrase(t[c.end:]))]
        definitions = [c for c in matches if c.value == 1 and c.end <= n.start
                       and not _has(r'[.;]', t[c.end:n.start])
                       and _has(r'\b(?:sells?|costs?|priced)\b', t[_bounds(t,c)[0]:n.start])]
        purchases = [c for c in matches if c not in definitions and c.start > n.end]
        if len(purchases) != 1 or len(definitions) > 1 or len(matches) != len(definitions)+1:
            return None
        c = purchases[0]
        if any(id(k) in used for k in matches):
            return None
        used.update(id(k) for k in matches)
        terms.append(n.value*c.value)
    if len(used) != len(counts):
        return None
    return _answer(p, sum(terms,Fraction(0)), _expr(terms))


def _bogo(p, ns):
    """Buy N, get M free; an explicitly stated total includes the free units."""
    t = p.text.lower()
    money, counts = _parts(ns)
    if len(money) != 1 or len(counts) != 3 or not _has(r'\b(?:pay|spend|spent|cost)\b', p.question):
        return None
    buy, free, stock = counts
    if not (_has(r'\bbuy\s*$', t[:buy.start])
            and re.fullmatch(r'\s+get\s+', t[buy.end:free.start])
            and _has(r'^\s+free\b', t[free.end:])):
        return None
    if not _has(r'\b(?:gets?|bought|buys?|purchased)\s*$', t[free.end:stock.start]):
        return None
    if buy.value <= 0 or free.value <= 0 or stock.value % (buy.value+free.value):
        return None
    if not _has(r'\b(?:normal|regular|usual|each|unit)\b', t[stock.end:]):
        return None
    value = stock.value*buy.value/(buy.value+free.value)*money[0].value
    return _answer(p, value, '{} / ({} + {}) * {} * {}'.format(*(format_number(v) for v in
        (stock.value,buy.value,free.value,buy.value,money[0].value))))


def _quoted_comparison(p, ns):
    """Compare the per-unit prices of two explicitly quoted lots."""
    t, q = p.text.lower(), p.question
    money, counts = _parts(ns)
    if len(money) != 2 or len(counts) != 2 or not _has(r'\b(?:per|each)\b', q):
        return None
    if not _has(r'\b(?:more expensive|cheaper|difference)\b', q):
        return None
    if not _same(_phrase(t[counts[0].end:]), _phrase(t[counts[1].end:])):
        return None
    pairs = []
    for price in money:
        lo, hi = _bounds(t, price)
        local = [c for c in counts if lo <= c.start < hi]
        if len(local) != 1 or local[0].value <= 0:
            return None
        if not _has(r'\b(?:for|offering|costs?|price|has|contains)\b', t[lo:hi]):
            return None
        pairs.append(price.value/local[0].value)
    return _answer(p, abs(pairs[0]-pairs[1]), '|{} - {}|'.format(*(format_number(v) for v in pairs)))


def _payback(p, ns):
    """Startup outlay divided by recurring net income, never gross receipts."""
    t, q = p.text.lower(), p.question
    if len(ns) != 3 or any(n.kind != 'money' for n in ns):
        return None
    if not _has(r'\b(?:how long|how many months|how many weeks|how many years)\b', q) or not _has(r'\b(?:pay back|make back|recover|recoup)\b', q):
        return None
    startup, income, expense = ns
    if not _has(r'\b(?:open|start|startup|initial|investment)\b', t[:income.start]):
        return None
    if not _has(r'\b(?:makes?|earns?|revenue|income)\b', t[startup.end:income.start]+t[income.end:expense.start]):
        return None
    if not _has(r'\bexpenses?\b', t[income.end:expense.start]):
        return None
    a, b = _label(p, ns, income)[0], _label(p, ns, expense)[0]
    if a != b or a not in ('day','week','month','year') or income.value <= expense.value:
        return None
    return _answer(p, startup.value/(income.value-expense.value), '{} / ({} - {})'.format(*(format_number(n.value) for n in ns)))


def _wage_budget(p, ns):
    """Whole work hours needed to fund an itemized list of requirements."""
    t, q = p.text.lower(), p.question
    if not q.startswith('how many hours') or not _has(r'\b(?:need|work)\b', q):
        return None
    if len(ns) < 3 or any(n.kind != 'money' for n in ns):
        return None
    wage = ns[-1]
    if not _has(r'^\s*(?:dollars?\s*)?(?:per|an?|each) hour\b', t[wage.end:]) or wage.value <= 0:
        return None
    if not _has(r'\bneeds?\b', t[:ns[0].start]) or _has(r'\b(?:has|had|earned|discount|interest|tax|each|per)\b', t[:wage.start]):
        return None
    costs = [n.value for n in ns[:-1]]
    hours = sum(costs,Fraction(0))/wage.value
    result = Fraction(-(-hours.numerator//hours.denominator))
    return _answer(p,result,'ceil(({}) / {})'.format(_expr(costs),format_number(wage.value)))


def _missing_equal_price(p, ns):
    """Total price of N pieces minus individually priced pieces, then divide."""
    t, q = p.text.lower(), p.question
    money, counts = _parts(ns)
    if len(money) < 2 or len(counts) != 1 or not _has(r'\b(?:other|remaining)\b.*\bsame price\b', t):
        return None
    if not _has(r'\b(?:one|each|per)\b', q):
        return None
    total = money[0]
    count = counts[0]
    if not _has(r'\b(?:spent|paid)\s*$', t[:total.start]) or not _has(r'^\s+on\s*$', t[total.end:count.start]):
        return None
    if not _has(r'\bone\b[^.;]*\bwas\s*$', t[count.end:money[1].start]):
        return None
    if any(not _has(r'\b(?:another|other)\b[^.;]*\bwas\s*$',t[money[i-1].end:n.start]) for i,n in enumerate(money[2:],2)):
        return None
    remaining = count.value-(len(money)-1)
    if remaining <= 0:
        return None
    known = sum((n.value for n in money[1:]),Fraction(0))
    return _answer(p,(total.value-known)/remaining,'({} - {}) / {}'.format(format_number(total.value),format_number(known),format_number(remaining)))


def _denomination(p, ns):
    """An explicit count of bills, their denomination, and an existing balance."""
    t = p.text.lower()
    if len(ns) != 3:
        return None
    count, denom, balance = ns
    if count.kind == 'money' or denom.kind == 'money' or balance.kind != 'money':
        return None
    if not _has(r'^\s+(?:bills|notes)\b',t[count.end:]) or not _has(r'^s\b',t[denom.end:]):
        return None
    if not _has(r'\b(?:all|each)\s*$',t[count.end:denom.start]) or not _has(r'\b(?:already had|already has)\s*$',t[denom.end:balance.start]):
        return None
    if not _has(r'\b(?:have|has)\b.*\bnow\b',p.question):
        return None
    return _answer(p,count.value*denom.value+balance.value,'{} * {} + {}'.format(*(format_number(n.value) for n in ns)))


def _overage(p, ns):
    """A bill total = base allowance fee + rate * excess usage."""
    t, q = p.text.lower(), p.question
    money, counts = _parts(ns)
    if len(money) != 3 or len(counts) != 2 or not q.startswith('how many '):
        return None
    base, rate, total = money
    allowance, block = counts
    if not base.start < allowance.start < rate.start < block.start < total.start:
        return None
    if not _has(r'\b(?:over|extra|excess)\b',q) or not _has(r'\b(?:every|per|each)\s*$',t[rate.end:block.start]):
        return None
    if not _has(r'^\s+[a-z]+\s+(?:over|extra)\b',t[block.end:]):
        return None
    if not _same(_phrase(t[allowance.end:]),_phrase(t[block.end:])) or rate.value <= 0:
        return None
    if not _has(r'\bbill\b[^.;]*\bis\s*$',t[block.end:total.start]):
        return None
    return _answer(p,(total.value-base.value)*block.value/rate.value,'({} - {}) * {} / {}'.format(*(format_number(n.value) for n in (total,base,block,rate))))


def _tips(p, ns):
    """An hourly base plus the same tip from each explicitly counted customer."""
    t, q = p.text.lower(), p.question
    money, counts = _parts(ns)
    if len(money) != 2 or len(counts) != 2 or not _has(r'\b(?:make|earn|made|earned)\b',q):
        return None
    base, tip = money
    hour, customers = counts
    if hour.value != 1 or _unit(t[hour.end:]) != 'hour' or not base.start < hour.start < customers.start < tip.start:
        return None
    if not _has(r'\b(?:people|customers|clients)\b',t[customers.end:tip.start]) or not _has(r'\b(?:all|each)\b.*\bleave\b',t[customers.end:tip.start]):
        return None
    if not _has(r'^\s+tip\b',t[tip.end:]) or not _has(r'\b(?:that|this|one) hour\b',q):
        return None
    return _answer(p,base.value+customers.value*tip.value,'{} + {} * {}'.format(*(format_number(n.value) for n in (base,customers,tip))))



def _equal_category_purchase(p, ns):
    """The same number is bought from each of several enumerated categories."""
    t = p.text.lower()
    money, counts = _parts(ns)
    if len(counts) != 2 or not 2 <= len(money) <= 5:
        return None
    groups, count = counts
    if groups.value != len(money) or not groups.start < money[0].start < money[-1].start < count.start:
        return None
    container = _head(_phrase(t[groups.end:]))
    link = re.search(r'\bfrom each ([a-z]+)\b', t[count.end:])
    if not container or not link or _singular(link.group(1)) != container:
        return None
    if not _has(r'\b(?:cost|pay|spent|spend)\b',p.question):
        return None
    if any(not _has(r'^\s*(?:dollars?\s*)?each\b',t[n.end:]) for n in money):
        return None
    # The categories must be explicitly enumerated, rather than merely
    # assuming any arbitrary list of prices corresponds to the group count.
    ordinals = re.findall(r'\b(?:first|second|third|fourth|fifth) '+re.escape(container)+r'\b',p.body)
    if len(ordinals) != len(money) or len(set(ordinals)) != len(money):
        return None
    return _answer(p,count.value*sum((n.value for n in money),Fraction(0)),
                   '{} * ({})'.format(format_number(count.value),_expr(n.value for n in money)))


def _work_comparison(p, ns):
    """Compare two explicitly counted batches with a price for each task."""
    t, q = p.text.lower(), p.question
    money, counts = _parts(ns)
    if len(money) != 2 or len(counts) != 2 or not _has(r'\b(?:more|difference|compared)\b',q):
        return None
    if not _has(r'\b(?:earn|earned|make|made)\b',q):
        return None
    terms=[]
    for n,c in zip(money,counts):
        if not c.end < n.start or _has(r'[.;]',t[c.end:n.start]):
            return None
        if not _has(r'\b(?:doing|completed|completes|performed)\s*$',t[:c.start]):
            return None
        if not _has(r'^\s+each\b',t[n.end:]):
            return None
        terms.append(n.value*c.value)
    if not _same(_phrase(re.sub(r'^\s*work ', ' ', t[counts[0].end:])),_phrase(re.sub(r'^\s*work ', ' ', t[counts[1].end:]))):
        return None
    return _answer(p,abs(terms[0]-terms[1]),'|{} - {}|'.format(*(format_number(v) for v in terms)))


def _monthly_extra(p, ns):
    """One monthly subscription plus a daily surcharge for explicit days."""
    t, q = p.text.lower(), p.question
    money, counts = _parts(ns)
    if len(money)!=2 or len(counts)!=1 or not _has(r'\b(?:charges|cost|pay|bill)\b',q):
        return None
    day=counts[0]
    if _unit(t[day.end:])!='day':
        return None
    rates={_label(p,ns,n)[0]:n for n in money}
    if set(rates)!={'day','month'}:
        return None
    months=r'(?:january|february|march|april|may|june|july|august|september|october|november|december)'
    named=re.findall(r'\b'+months+r'\b',q)
    if not named or not _has(r'\b'+named[0]+r'\b',p.body):
        return None
    if not _has(r'\b(?:regular|plan|subscription|base)\b',t[rates['month'].end:]) or _has(r'\b(?:instead|replace|discount|free)\b',t):
        return None
    return _answer(p,rates['month'].value+day.value*rates['day'].value,
                   '{} + {} * {}'.format(*(format_number(v) for v in (rates['month'].value,day.value,rates['day'].value))))


def _missing_receipt(p, ns):
    """Sale total less a priced stock leaves the other item's receipt."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=2 or len(counts)!=2 or not _has(r'\b(?:cost|price|sold)\b',q):
        return None
    total,price=money
    stock,definition=counts
    if definition.value!=1 or not definition.start>=len(p.body) or not price.start>definition.end:
        return None
    if not _has(r'\b(?:total|earned)\b[^.;]*$',t[stock.end:total.start]):
        return None
    if not _has(r'\b(?:sold|sell|selling)\b',t[:stock.start]) or not _has(r'\b(?:was|is) sold for\s*$',t[definition.end:price.start]):
        return None
    if not _same(_phrase(t[stock.end:]),_phrase(t[definition.end:])):
        return None
    # The asked item must differ from the individually priced item.
    item=_head(_phrase(t[definition.end:]))
    if _has(r'\b'+re.escape(item)+r's?\b',q.split('if')[0]):
        return None
    return _answer(p,total.value-stock.value*price.value,'{} - {} * {}'.format(*(format_number(n.value) for n in (total,stock,price))))


def _sales_interval(p, ns):
    """N tickets sold per interval, scaled by query duration and ticket price."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=1 or len(counts)!=3 or not _has(r'\b(?:earnings|earn|make|revenue)\b',q):
        return None
    interval,stock,duration=counts
    if _unit(t[interval.end:])!=_unit(t[duration.end:]) or _unit(t[interval.end:]) not in ('minute','hour','day','week'):
        return None
    if not interval.start<stock.start<len(p.body)<=duration.start or interval.value<=0:
        return None
    if not _has(r'\bin\s*$',t[:interval.start]) or not _has(r'\b(?:sells|sold)\b',t[interval.end:stock.start]):
        return None
    if not _same(_label(p,ns,money[0])[0],_phrase(t[stock.end:])):
        return None
    return _answer(p,money[0].value*stock.value*duration.value/interval.value,
        '{} * {} * {} / {}'.format(*(format_number(n.value) for n in (money[0],stock,duration,interval))))


def _scaled_purchase(p, ns):
    """One known item price and another costing an explicit multiple."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=1 or len(counts)!=1 or not _has(r'\b(?:both|total|all|together)\b',q):
        return None
    price,factor=money[0],counts[0]
    if not price.start<factor.start or not _has(r'^\s+times (?:the price|as much|that much)\b',t[factor.end:]):
        return None
    if not _has(r'\b(?:buys?|bought|pays?|paid|gets?|received)\b',t[:price.start]):
        return None
    if not _has(r'\b(?:and|then)\b',t[price.end:factor.start]):
        return None
    if _has(r'\b(?:profit|less|left|save|discount)\b',q):
        return None
    return _answer(p,price.value*(1+factor.value),'{} * (1 + {})'.format(format_number(price.value),format_number(factor.value)))


def _value_multiplier(p, ns):
    """Profit when an item's value doubles/triples, or invert a scaled balance."""
    t,q=p.text.lower(),p.question
    factors=re.findall(r'\b(double[ds]?|triple[ds]?)\b',t)
    if len(factors)!=1 or any(n.kind!='money' for n in ns):
        return None
    factor=Fraction(2 if factors[0].startswith('double') else 3)
    if len(ns)==1 and _has(r'\bprofit\b',q) and _has(r'\bvalue\b',p.body) and _has(r'\b(?:buys?|bought|paid)\b',p.body):
        return _answer(p,ns[0].value*(factor-1),'{} * ({} - 1)'.format(format_number(ns[0].value),format_number(factor)))
    if len(ns)==2 and _has(r'\b(?:beginning|initial|start)\b',q) and _has(r'\bbalance\b',p.body):
        withdrawal,current=ns
        if not _has(r'\bwithdrew\s*$',t[:withdrawal.start]) or not _has(r'\bcurrent balance is\s*$',t[withdrawal.end:current.start]):
            return None
        return _answer(p,(withdrawal.value+current.value)/factor,'({} + {}) / {}'.format(format_number(current.value),format_number(withdrawal.value),format_number(factor)))
    return None


def _consumable_duration(p, ns):
    """A unit-price consumable lasts a specified duration; buy a year's supply."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=1 or len(counts)!=1 or not _has(r'\b(?:entire|whole|one|a) year\b',t):
        return None
    lifespan=counts[0]
    unit=_unit(t[lifespan.end:])
    factor={'month':12,'week':52,'day':365}.get(unit)
    if factor is None or lifespan.value<=0 or not _has(r'\b(?:lasts?|lasting)\b[^.;]*$',t[:lifespan.start]):
        return None
    label,explicit=_label(p,ns,money[0])
    if not explicit or not label or _head(label) in ('day','week','month','year'):
        return None
    if not _has(r'\b(?:spend|pay|cost)\b',q) or _has(r'\b(?:discount|free|left|more|less)\b',t):
        return None
    return _answer(p,money[0].value*factor/lifespan.value,'{} * {} / {}'.format(format_number(money[0].value),factor,format_number(lifespan.value)))


def _daily_events(p, ns):
    """A priced event repeated N times daily over an explicit full week."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=1 or len(counts)!=1 or not _has(r'^\s+times (?:a|per|each) day\b',t[counts[0].end:]):
        return None
    if not _has(r'\bfor (?:a|one|an entire|a whole) week\b',t) or not _has(r'\b(?:buy|cost|spend|pay)\b',q):
        return None
    if not _has(r'^\s*(?:dollars?\s*)?each\b',t[money[0].end:]) or _has(r'\b(?:free|discount|extra|more|less|remaining)\b',t):
        return None
    return _answer(p,counts[0].value*money[0].value*7,'{} * {} * 7'.format(format_number(counts[0].value),format_number(money[0].value)))


def _weekly_event(p, ns):
    """One weekly call/session, with minutes per event and a price per minute."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=1 or len(counts)!=1 or _unit(t[counts[0].end:])!='minute':
        return None
    event=re.search(r'\beach ([a-z]+) lasts?\s*$',t[:counts[0].start])
    if not event or not _has(r'\bevery week\b',t[:counts[0].start]):
        return None
    if not _has(r'^\s+per (?:'+re.escape(event.group(1))+r' )?minute\b',t[money[0].end:]):
        return None
    if not _has(r'\b(?:a|one|an entire|a whole) year\b',q) or not _has(r'\b(?:billed|spend|pay|cost)\b',q):
        return None
    return _answer(p,counts[0].value*money[0].value*52,'{} * {} * 52'.format(format_number(counts[0].value),format_number(money[0].value)))


def _package_weight(p, ns):
    """N packages, each of a specified weight, priced per unit of weight."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=1 or len(counts)!=2 or not _has(r'\b(?:pay|cost|spend)\b',q):
        return None
    size,stock=counts
    if not _has(r'^-[a-z]+ (?:packages?|packs?|bags?|boxes?)\b',t[size.end:]):
        return None
    if not _has(r'^\s+of them\b',t[stock.end:]) or not size.start<stock.start<money[0].start:
        return None
    unit=_unit(t[size.end:])
    if not unit or _label(p,ns,money[0])[0]!=unit:
        return None
    return _answer(p,size.value*stock.value*money[0].value,'{} * {} * {}'.format(*(format_number(n.value) for n in (size,stock,money[0]))))


def _per_serving(p, ns):
    """Ingredient basket divided by the explicitly stated number of servings."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)<2 or not counts or not _has(r'\beach serving\b|\bper serving\b',q):
        return None
    servings=counts[0]
    if not _has(r'\b(?:serve|serves|serving|feeds?)\s*$',t[:servings.start]) or _unit(t[servings.end:]) not in ('person','people','serving'):
        return None
    ingredients=counts[1:]
    used=set();terms=[]
    for n in money:
        label,explicit=_label(p,ns,n)
        matches=[c for c in ingredients if _same(label,_phrase(t[c.end:]))]
        if len(matches)>1 or any(id(c) in used for c in matches):
            return None
        if matches:
            used.add(id(matches[0]));terms.append(n.value*matches[0].value)
        elif explicit and _has(r'\b(?:per|each)\b',t[n.end:_bounds(t,n)[1]]):
            return None
        elif _has(r'\b(?:costs?|price)\s*$',t[_bounds(t,n)[0]:n.start]):
            terms.append(n.value)
        else:
            return None
    if len(used)!=len(ingredients) or servings.value<=0:
        return None
    return _answer(p,sum(terms,Fraction(0))/servings.value,'({}) / {}'.format(_expr(terms),format_number(servings.value)))


def _promotion_savings(p, ns):
    """A normal and a promotional unit price applied to the promoted quantity."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=2 or len(counts)!=1 or not _has(r'\bsavings\b',q) or not _has(r'\bpromotion\b',t):
        return None
    sale,regular=money
    if not _has(r'^\s+each\b',t[sale.end:]) or not _has(r'\b(?:regular|normal|usual)\b[^.;?]*\bprice is\s*$',t[sale.end:regular.start]):
        return None
    if not counts[0].start<sale.start<regular.start or not _has(r'\b(?:full advantage|all)\b',q):
        return None
    return _answer(p,(regular.value-sale.value)*counts[0].value,'({} - {}) * {}'.format(*(format_number(n.value) for n in (regular,sale,counts[0]))))


def _contributors(p, ns):
    """Required money less cash on hand, divided by a person's contribution."""
    t,q=p.text.lower(),p.question
    if len(ns)!=3 or any(n.kind!='money' for n in ns) or not q.startswith('how many people'):
        return None
    rate,target,cash=ns
    if not _has(r'\b(?:average|each|every) person (?:funds|gives|contributes|donates)\s*$',t[:rate.start]):
        return None
    if not _has(r'\b(?:fund|funding|raise)\b',q) or not _has(r'\b(?:has|have|had)\s*$',t[target.end:cash.start]):
        return None
    if rate.value<=0:
        return None
    n=(target.value-cash.value)/rate.value
    return _answer(p,Fraction(-(-n.numerator//n.denominator)),'ceil(({} - {}) / {})'.format(*(format_number(n.value) for n in (target,cash,rate))))


def _one_each_budget(p, ns):
    """A stated recipient count, with one priced item for every recipient."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=2 or len(counts)!=1 or not _has(r'\b(?:out of pocket|pay the rest|more|need)\b',q):
        return None
    cash,price=money
    count=counts[0]
    recipient=_head(_phrase(t[count.end:]))
    label,explicit=_label(p,ns,price)
    if not explicit or not label or not recipient or recipient==label:
        return None
    if not _has(r'\bevery '+re.escape(recipient)+r' (?:a|an) '+re.escape(label)+r'\b',q):
        return None
    if not _has(r'\b(?:given|has|had|budget)\b[^.;]*$',t[:cash.start]):
        return None
    return _answer(p,count.value*price.value-cash.value,'{} * {} - {}'.format(*(format_number(n.value) for n in (count,price,cash))))


def _register(p, ns):
    """Value of explicitly counted banknotes, less the notes kept in the till."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=len(counts)+1 or not counts or not _has(r'\b(?:handing in|turn in|hand in)\b',q):
        return None
    reserve=money[-1]
    if not _has(r'\bleave\s*$',t[:reserve.start]) or not _has(r'^\s+in notes\b',t[reserve.end:]):
        return None
    terms=[]
    for c,n in zip(counts,money[:-1]):
        if not c.end<=n.start or t[c.end:n.start].strip() or not _has(r'^\s+bills?\b',t[n.end:]):
            return None
        terms.append(c.value*n.value)
    return _answer(p,sum(terms,Fraction(0))-reserve.value,'({}) - {}'.format(_expr(terms),format_number(reserve.value)))


def _repeated_deposit(p, ns):
    """Two equal deposits, followed by an unknown deposit and a final total."""
    t,q=p.text.lower(),p.question
    if len(ns)!=2 or any(n.kind!='money' for n in ns) or not _has(r'\b(?:add|deposit)\b',q):
        return None
    deposit,total=ns
    if not _has(r'\b(?:adds?|deposits?)\s*$',t[:deposit.start]) or not _has(r'\bthen (?:adds?|deposits?) the same amount\b',t[deposit.end:total.start]):
        return None
    if not _has(r'\b(?:has|balance|total)\s*$',t[deposit.end:total.start]):
        return None
    if not _has(r'\b(?:start saving|new .*bank)\b',p.body):
        return None
    return _answer(p,total.value-2*deposit.value,'{} - 2 * {}'.format(format_number(total.value),format_number(deposit.value)))


def _recipient_gifts(p, ns):
    """N recipients each receive M envelopes/items containing a fixed sum."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=1 or len(counts)!=2 or not _has(r'\b(?:give|gives|given|spend|spent)\b',q):
        return None
    recipients,items=counts
    if not recipients.start<items.start<money[0].start:
        return None
    recipient=_head(_phrase(t[recipients.end:]))
    recipient={'grandchildren':'grandchild','grandkid':'grandchild','grandchild':'grandchild','kid':'child'}.get(recipient,recipient)
    m=re.search(r'\beach ([a-z]+)\s*$',t[recipients.end:items.start])
    if not m:
        return None
    target=_singular(m.group(1))
    target={'grandkid':'grandchild','grandchildren':'grandchild','kid':'child'}.get(target,target)
    if recipient!=target:
        return None
    if not _same(_label(p,ns,money[0])[0],_phrase(t[items.end:])) or not _has(r'\b(?:puts?|places?)\s*$',t[items.end:money[0].start]):
        return None
    periods=re.findall(r'\b(?:a|per|each|every) (year|month|week|day)\b',t)
    if len(set(periods))>1:
        return None
    return _answer(p,recipients.value*items.value*money[0].value,'{} * {} * {}'.format(*(format_number(n.value) for n in (recipients,items,money[0]))))


def _restated_rate(p, ns):
    """Repeated stock-per-week facts describe the same rate, not extra stock."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=1 or len(counts)!=3 or not _has(r'\b(?:spend|spent|pay|cost)\b',q):
        return None
    first,repeat,duration=counts
    if first.value!=repeat.value or not _same(_phrase(t[first.end:]),_phrase(t[repeat.end:])):
        return None
    if not _has(r'\b(?:a|each|every|per) week\b',t[first.end:money[0].start]) or not _has(r'\b(?:a|each|every|per) week\b',t[repeat.end:duration.start]):
        return None
    if _unit(t[duration.end:])!='week' or not _same(_label(p,ns,money[0])[0],_phrase(t[first.end:])):
        return None
    return _answer(p,first.value*duration.value*money[0].value,'{} * {} * {}'.format(*(format_number(n.value) for n in (first,duration,money[0]))))


def _calendar_daily(p, ns):
    """An explicit daily purchase and unit price, for a named calendar month."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=1 or len(counts)!=1 or not _has(r'\b(?:spend|spent|pay|cost)\b',q):
        return None
    month=re.search(r'\bin (january|march|april|may|june|july|august|september|october|november|december)\b',q)
    if not month or not _has(r'\b(?:a|per|each|every) day\b',t[counts[0].end:money[0].start]):
        return None
    if not _has(r'^\s+each\b',t[money[0].end:]) or not _has(r'\b(?:buys?|bought|purchases?|purchased)\s*$',t[:counts[0].start]):
        return None
    days=30 if month.group(1) in ('april','june','september','november') else 31
    return _answer(p,counts[0].value*money[0].value*days,'{} * {} * {}'.format(format_number(counts[0].value),format_number(money[0].value),days))


def _energy(p, ns):
    """A power-based electricity rate times power draw and hours of use."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=1 or len(counts)!=2 or not _has(r'\b(?:pay|cost|spend)\b',q):
        return None
    power,hours=counts
    if not _has(r'^\s+per kw(?:h)?\b',t[money[0].end:]) or not _has(r'^\s+kwh?\b',t[power.end:]) or _unit(t[hours.end:])!='hour':
        return None
    if not _has(r'\b(?:consumption|power|draw)\b',t[money[0].end:power.start]):
        return None
    # kWh normally states total energy, so hours must not multiply it again.
    # Some elementary questions explicitly call this a consumption *rate*;
    # accept that convention only when the rate is actually named.
    if _has(r'^\s+kwh\b',t[power.end:]) and not _has(r'\bconsumption rate\b',t[money[0].end:power.start]):
        return None
    return _answer(p,money[0].value*power.value*hours.value,'{} * {} * {}'.format(*(format_number(n.value) for n in (money[0],power,hours))))


def _scaled_total_unit(p, ns):
    """A purchase totals K times another's outlay; divide by purchased stock."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=1 or len(counts)!=2 or not _has(r'\b(?:each|per)\b',q):
        return None
    stock,factor=counts
    if not stock.start<factor.start<money[0].start or not _has(r'\b(?:purchased|bought|buys?)\s*$',t[:stock.start]):
        return None
    if not _has(r'^\s+times the price ([a-z]+) paid\b',t[factor.end:]):
        return None
    ref=re.match(r'\s+times the price ([a-z]+) paid\b',t[factor.end:]).group(1)
    if not _has(r'\b'+re.escape(ref)+r' paid\s*$',t[factor.end:money[0].start]):
        return None
    if not _has(r'\b'+re.escape(_head(_phrase(t[stock.end:])))+r's?\b',q) or stock.value<=0:
        return None
    return _answer(p,money[0].value*factor.value/stock.value,'{} * {} / {}'.format(*(format_number(n.value) for n in (money[0],factor,stock))))


def _category_difference(p, ns):
    """Two ticket categories with a stated count difference and basket total."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=3 or len(counts)!=1 or not q.startswith('how many '):
        return None
    total,a,b=money;delta=counts[0]
    labels=[]
    for n in (a,b):
        label,explicit=_label(p,ns,n)
        if not explicit or not label.endswith(' ticket'):
            return None
        labels.append(label[:-7])
    relation=re.match(r'\s+more ([a-z]+) than ([a-z]+)\b',t[delta.end:])
    if not relation or not _has(r'\b(?:pays?|paid|spends?|spent)\b',t[:total.start]):
        return None
    larger,smaller=(_singular(x) for x in relation.groups())
    if set(labels)!={larger,smaller}:
        return None
    prices=dict(zip(labels,(a.value,b.value)))
    if prices[larger]+prices[smaller]<=0:
        return None
    small=(total.value-delta.value*prices[larger])/(prices[larger]+prices[smaller])
    target=re.match(r'how many ([a-z]+)',q)
    wanted=_singular(target.group(1))
    if wanted not in prices or small.denominator!=1:
        return None
    value=small+(delta.value if wanted==larger else 0)
    return _answer(p,value,'({} - {} * {}) / ({} + {}){}'.format(
        format_number(total.value),format_number(delta.value),format_number(prices[larger]),
        format_number(prices[larger]),format_number(prices[smaller]),
        ' + '+format_number(delta.value) if wanted==larger else ''))


def _area_sum(p, ns):
    """A shared price per square unit for explicitly stated building areas."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=1 or not 2<=len(counts)<=4 or not _has(r'\b(?:property|cost|pay|worth)\b',q):
        return None
    if not _has(r'^\s+per (?:square foot|sq[.]? ft)\b',t[money[0].end:]):
        return None
    if not all(_has(r'^\s+(?:sq[.]? ft|square feet)\b',t[n.end:]) for n in counts):
        return None
    if _has(r'\b(?:more|less|twice|half|discount|tax|perimeter)\b',t):
        return None
    return _answer(p,sum((n.value for n in counts),Fraction(0))*money[0].value,
        '({}) * {}'.format(_expr(n.value for n in counts),format_number(money[0].value)))


def _missing_categories(p, ns):
    """A basket total with two counted categories and one known unit price."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=2 or len(counts)!=2 or not _has(r'\b(?:cost|price)\b',q):
        return None
    total,price=money
    if not _has(r'^\s*(?:dollars?\s*)?(?:total|in total|altogether)\b',t[total.end:]):
        return None
    label,explicit=_label(p,ns,price)
    if not explicit:
        return None
    labels=[]
    for c in counts:
        phrase=_phrase(t[c.end:])
        # "large ones" and "small ones" retain their explicit modifier.
        phrase=re.sub(r' ones?$', '',phrase)
        labels.append(phrase)
    matched=[i for i,label_c in enumerate(labels) if _same(label_c,label) or label.startswith(label_c+' ')]
    if len(matched)!=1:
        return None
    known=matched[0];unknown=1-known
    if not _has(r'\b'+re.escape(labels[unknown])+r'\b',q) or counts[unknown].value<=0:
        return None
    return _answer(p,(total.value-counts[known].value*price.value)/counts[unknown].value,
        '({} - {} * {}) / {}'.format(*(format_number(n.value) for n in (total,counts[known],price,counts[unknown]))))


def _relative_cost_pair(p, ns):
    """One known cost, another a stated fraction/multiple, and their total."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=1 or len(counts)!=1 or not _has(r'\b(?:total|both|all|spent|spend)\b',q):
        return None
    price,factor=money[0],counts[0]
    if factor.start>price.start:
        if not _has(r'\b(?:cost|costs|price)\b',t[:price.start]) or not _has(r'^\s+as much\b',t[factor.end:]):
            return None
    else:
        if not _has(r'^\s+times (?:greater than |as much as )?(?:the )?cost of\b',t[factor.end:]):
            return None
        if not _has(r'\b(?:cost|costs)\s*$',t[factor.end:price.start]):
            return None
    if _has(r'\b(?:save|discount|left|remaining|profit|less)\b',q):
        return None
    return _answer(p,price.value*(1+factor.value),'{} * (1 + {})'.format(format_number(price.value),format_number(factor.value)))


def _single_item_shortage(p, ns):
    """One required item per participant, minus the items already owned."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=1 or len(counts)!=2 or not _has(r'\b(?:spend|pay|cost)\b',q):
        return None
    required,owned=counts
    if not required.start<owned.start<money[0].start or not _has(r'\bfor each of (?:its|the|their)\s*$',t[:required.start]):
        return None
    label,explicit=_label(p,ns,money[0])
    if not explicit or not _same(label,_phrase(t[owned.end:])):
        return None
    if not _has(r'\b(?:has|have|had) (?:only )?\s*$',t[required.end:owned.start]) or not _has(r'\bbuy the rest\b',p.body):
        return None
    return _answer(p,(required.value-owned.value)*money[0].value,'({} - {}) * {}'.format(*(format_number(n.value) for n in (required,owned,money[0]))))


def _pronoun_stock(p, ns):
    """An explicit singular item price, N of them, and available cash."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=2 or len(counts)!=1 or not _has(r'\b(?:left|remaining|change)\b',q):
        return None
    price,cash=money;stock=counts[0]
    if not price.start<stock.start<cash.start or not _has(r'^\s+of them\b',t[stock.end:]):
        return None
    if not _has(r'\bneeds?\s*$',t[price.end:stock.start]) or not _has(r'\b(?:has|have|had)\s*$',t[stock.end:cash.start]):
        return None
    if not _label(p,ns,price)[1] or not _label(p,ns,price)[0]:
        return None
    return _answer(p,cash.value-stock.value*price.value,'{} - {} * {}'.format(*(format_number(n.value) for n in (cash,stock,price))))


def _repeated_saving(p, ns):
    """A saving rate, explicit weeks per cycle, and number of complete cycles."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=1 or len(counts)!=2 or not _has(r'\b(?:money|total)\b',q):
        return None
    weeks,cycles=counts
    if _unit(t[weeks.end:])!='week' or not _has(r'^\s+times\b',t[cycles.end:]):
        return None
    if not _has(r'\bevery week\b[^.;]*$',t[:money[0].start]) or not _has(r'\brepeated this (?:whole )?process\s*$',t[weeks.end:cycles.start]):
        return None
    if not _has(r'\b(?:saving|saved|moneybox|saves)\b',p.body):
        return None
    return _answer(p,money[0].value*weeks.value*cycles.value,'{} * {} * {}'.format(*(format_number(n.value) for n in (money[0],weeks,cycles))))


def _savings_meet(p, ns):
    """Two initial balances with recurring savings; find the meeting time."""
    t,q=p.text.lower(),p.question
    if len(ns)!=4 or any(n.kind!='money' for n in ns) or not q.startswith('how many weeks'):
        return None
    if not _has(r'\bboth have the same amount\b',q):
        return None
    a,ra,b,rb=ns
    if not all(_has(r'^\s+per week\b',t[n.end:]) for n in (ra,rb)):
        return None
    if not all(_has(r'\bsaves?\s*$',t[_bounds(t,n)[0]:n.start]) for n in (ra,rb)):
        return None
    if not all(_has(r'\bhas\s*$',t[_bounds(t,n)[0]:n.start]) for n in (a,b)) or ra.value==rb.value:
        return None
    return _answer(p,(b.value-a.value)/(ra.value-rb.value),'({} - {}) / ({} - {})'.format(*(format_number(n.value) for n in (b,a,ra,rb))))


def _replacement_net(p, ns):
    """Replace an entire collection, receiving credit for each old item."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=2 or len(counts)!=1 or not _has(r'\breplace all\b.*\bwith\b',p.body):
        return None
    credit,price=money;stock=counts[0]
    if not _has(r'\btrade in\b[^.;]*$',t[:credit.start]) or not _has(r'\bbuy\b[^.;]*$',t[credit.end:price.start]):
        return None
    if not all(_has(r'^\s+each\b',t[n.end:]) for n in money) or not _has(r'\bhas\s*$',t[price.end:stock.start]):
        return None
    if not _has(r'\bcost to replace\b',q):
        return None
    return _answer(p,(price.value-credit.value)*stock.value,'({} - {}) * {}'.format(*(format_number(n.value) for n in (price,credit,stock))))


def _hourly_job(p, ns):
    """Total earnings divided by jobs times the stated hours per job."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=1 or len(counts) not in (3,4) or not _has(r'\bper hour\b',q):
        return None
    hours,unit,stock=counts[:3]
    if _unit(t[hours.end:])!='hour' or not _has(r'\btakes?\b[^.;]*$',t[:hours.start]):
        return None
    if not _same(_phrase(t[unit.end:]),_phrase(t[stock.end:])) or unit.value<=0 or hours.value<=0:
        return None
    if not hours.start<unit.start<stock.start<money[0].start or not _has(r'\b(?:earn|earned|paid)\s*$',t[stock.end:money[0].start]):
        return None
    if len(counts)==4 and (counts[3].value!=stock.value or not _same(_phrase(t[counts[3].end:]),_phrase(t[stock.end:]))):
        return None
    return _answer(p,money[0].value*unit.value/(hours.value*stock.value),'{} * {} / ({} * {})'.format(*(format_number(n.value) for n in (money[0],unit,hours,stock))))


def _two_costs_difference(p, ns):
    """The sum of two costs and an explicit difference determine each cost."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=2 or len(counts)!=2 or counts[0].value!=2 or counts[1].value!=1:
        return None
    total,difference=money
    if not counts[0].start<total.start<counts[1].start<difference.start:
        return None
    if not _has(r'\bfirst\s*$',t[total.end:counts[1].start]) or not _has(r'\bexceeds the other by\s*$',t[counts[1].end:difference.start]):
        return None
    if not _has(r'\b(?:price|cost)\b.*\bfirst\b',q):
        return None
    return _answer(p,(total.value+difference.value)/2,'({} + {}) / 2'.format(format_number(total.value),format_number(difference.value)))


def _coin_change(p, ns):
    """Minimum US cent coins for change below a dollar, at standard values."""
    t,q=p.text.lower(),p.question
    if len(ns)!=2 or any(n.kind!='money' for n in ns) or not _has(r'\bsmallest number of coins\b',t):
        return None
    cost,tender=ns
    if not cost.raw.startswith('$') or not tender.raw.startswith('$') or not _has(r'^\s+bill\b',t[tender.end:]):
        return None
    cents=(tender.value-cost.value)*100
    if not 0<=cents<100 or cents.denominator!=1:
        return None
    n=int(cents);count=0
    for denomination in (25,10,5,1):
        c,n=divmod(n,denomination);count+=c
    return _answer(p,Fraction(count),'Minimum coins for {} cents of change: {}'.format(format_number(cents),count))


def _coin_inventory(p, ns):
    """Pay a dollar expense from an inventory of a single named US cent coin."""
    t,q=p.text.lower(),p.question
    if not q.startswith('how many ') or not _has(r'\bleft\b',q):
        return None
    denominations={'penny':Fraction(1,100),'pennies':Fraction(1,100),
                   'nickel':Fraction(1,20),'dime':Fraction(1,10),'quarter':Fraction(1,4)}
    # Bare plural quarters are also parsed as fraction words by the shared
    # number grammar. Their noun use is resolved from the inventory and query.
    ns=[n for n in ns if n.raw.lower()!='quarters']
    money,counts=_parts(ns)
    if len(money)!=1 or len(counts)!=1:
        return None
    count=counts[0]
    name=re.match(r'\s+([a-z]+)',t[count.end:])
    if not name:
        return None
    noun=name.group(1);unit=_singular(noun)
    value=denominations.get(unit,denominations.get(noun))
    if value is None or not _has(r'\b'+re.escape(noun)+r'\b',q) or not money[0].raw.startswith('$'):
        return None
    if not _has(r'\bpay\s*$',t[count.end:money[0].start]):
        return None
    result=count.value-money[0].value/value
    if result.denominator!=1:
        return None
    return _answer(p,result,'{} - {} / {}'.format(format_number(count.value),format_number(money[0].value),format_number(value)))


def _letter_cost(p, ns):
    """One priced item for every letter of an explicitly listed first name."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=1 or len(counts)!=1 or counts[0].value!=1:
        return None
    if not _has(r'\bfor each letter of (?:the )?(?:first )?name\b',t) or not _has(r'\btotal\b',q):
        return None
    label,explicit=_label(p,ns,money[0])
    if not explicit or not _same(label,_phrase(t[counts[0].end:])):
        return None
    listing=re.search(r'\b(?:[A-Za-z]+ are|names are) ([A-Z][a-z]+(?:, [A-Z][a-z]+)*(?:,? and [A-Z][a-z]+))[.]',p.text)
    if not listing:
        return None
    names=re.findall(r'[A-Z][a-z]+',listing.group(1))
    letters=sum(len(name) for name in names)
    return _answer(p,letters*money[0].value,'{} letters * {}'.format(letters,format_number(money[0].value)))


def _party_events(p, ns):
    """A whole team pays an individual admission charge for each event."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=1 or len(counts)!=2 or not _has(r'\b(?:money collected|pay|cost|spend)\b',q):
        return None
    people,events=counts
    if not _has(r'\beach [a-z ]*team member must pay\s*$',t[:money[0].start]):
        return None
    if not _has(r'^\s+players on (?:the )?[a-z ]*team\b',t[people.end:]):
        return None
    if not _has(r'\bentire team attends\s*$',t[people.end:events.start]) or not _has(r'^\s+such [a-z]+\b',t[events.end:]):
        return None
    return _answer(p,money[0].value*people.value*events.value,'{} * {} * {}'.format(*(format_number(n.value) for n in (money[0],people,events))))


def _container_margin(p, ns):
    """A purchased container is resold as explicitly counted portions."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=2 or len(counts) not in (1,2,3) or not _has(r'\b(?:make|profit)\b',q):
        return None
    cost,price=money
    portions=[c for c in counts if _has(r'^\s+[a-z]+ per [a-z]+\b',t[c.end:])]
    if len(portions)!=1:
        return None
    portions=portions[0]
    m=re.match(r'\s+([a-z]+) per ([a-z]+)\b',t[portions.end:])
    portion,container=(_singular(x) for x in m.groups())
    if not _has(r'\b'+re.escape(container)+r'\b[^.;]*\bcosts?\s*$',t[:cost.start]):
        return None
    if not _has(r'\bcharges?\s*$',t[cost.end:price.start]):
        return None
    definition=[c for c in counts if c is not portions and c.start>price.end]
    if len(definition)>1 or definition and (definition[0].value!=1 or _unit(t[definition[0].end:])!=portion or not _has(r'^\s+for\s*$',t[price.end:definition[0].start])):
        return None
    decorative=[c for c in counts if c is not portions and c not in definition]
    if any(not _has(r'^\s+(?:ml|milliliters?|liters?|ounces?) '+re.escape(container)+r'\b',t[c.end:]) for c in decorative):
        return None
    if not definition and _label(p,ns,price)[0]!=portion:
        return None
    return _answer(p,portions.value*price.value-cost.value,'{} * {} - {}'.format(*(format_number(n.value) for n in (portions,price,cost))))


def _package_duration(p, ns):
    """A discounted duration package plus the remaining days at the day rate."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=2 or len(counts)!=2 or not _has(r'\b(?:cost|pay|spend)\b',q):
        return None
    daily,package=money;block,duration=counts
    if not daily.start<package.start<block.start<duration.start or _label(p,ns,daily)[0]!='day':
        return None
    if not _has(r'\bor\s*$',t[daily.end:package.start]) or not _has(r'^\s+for\s*$',t[package.end:block.start]):
        return None
    if any(_unit(t[c.end:])!='day' for c in counts) or block.value<=0 or duration.value<block.value:
        return None
    if package.value>block.value*daily.value or duration.value.denominator!=1 or block.value.denominator!=1:
        return None
    blocks,remainder=divmod(duration.value,block.value)
    if remainder*daily.value>package.value:
        return None
    return _answer(p,blocks*package.value+remainder*daily.value,'{} * {} + {} * {}'.format(
        format_number(blocks),format_number(package.value),format_number(remainder),format_number(daily.value)))


def _shopping_missing_price(p, ns):
    """Remove stated shopping companions and repeated query references."""
    from .money_totals_change_prices_1_2_steps_r06_a4 import _missing_price
    t=p.text.lower();filtered=[]
    companions=[c for c in ns if c.kind!='money' and _has(r'^\s+(?:kids|children|friends) shopping\b',t[c.end:])]
    if len(companions)!=1:
        return None
    for n in ns:
        if n in companions:
            continue
        if n.kind!='money' and n.start>=len(p.body):
            if n.value==1 and _has(r'\b(?:one|each|per)\b',p.question):
                continue
            if any(c.kind!='money' and c.start<len(p.body) and c.value==n.value and _same(_phrase(t[c.end:]),_phrase(t[n.end:])) for c in ns):
                continue
        filtered.append(n)
    return _missing_price(p,filtered)


def _barter(p, ns):
    """Value received minus value given in an explicitly described trade."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=2 or len(counts)!=2 or not _has(r'\bprofit\b',q):
        return None
    given,received=counts;cost,value=money
    if not given.start<cost.start<received.start<value.start or not _has(r'\btrades?\s*$',t[:given.start]):
        return None
    if not _has(r'^\s+each for\s*$',t[cost.end:received.start]):
        return None
    if not _same(_phrase(t[given.end:]),_phrase(t[received.end:])) or not all(_has(r'\bworth\s*$',t[c.end:n.start]) for c,n in ((given,cost),(received,value))):
        return None
    if received.value!=1 and not _has(r'^\s+each\b',t[value.end:]):
        return None
    return _answer(p,received.value*value.value-given.value*cost.value,
        '{} * {} - {} * {}'.format(*(format_number(n.value) for n in (received,value,given,cost))))


def _overcharge(p, ns):
    """An amount paid exceeds count times the stated correct unit price."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=2 or len(counts)!=1 or not _has(r'\b(?:reimburse|refund|overcharged|overcharge)\b',q):
        return None
    paid,price=money;stock=counts[0]
    if not paid.start<stock.start<price.start or not _has(r'\bpaid\b[^.;]*$',t[:paid.start]):
        return None
    if not _has(r'^\s+for\s*$',t[paid.end:stock.start]):
        return None
    if not _same(_label(p,ns,price)[0],_phrase(t[stock.end:])):
        return None
    return _answer(p,paid.value-stock.value*price.value,'{} - {} * {}'.format(*(format_number(n.value) for n in (paid,stock,price))))


def _equal_transfer(p, ns):
    """A transfer makes two balances equal; recover the recipient's balance."""
    t,q=p.text.lower(),p.question
    if len(ns)!=2 or any(n.kind!='money' for n in ns) or not _has(r'\b(?:beginning|originally|at first)\b',q):
        return None
    gift,original=ns
    giver=re.search(r'\b([a-z]+) would give ([a-z]+)\s*$',t[:gift.start])
    if not giver or not _has(r'\bsame amount of money\b',t[gift.end:original.start]):
        return None
    a,b=giver.groups()
    if not _has(r'\b'+re.escape(a)+r' originally had\s*$',t[gift.end:original.start]) or not _has(r'\b'+re.escape(b)+r'\b',q):
        return None
    return _answer(p,original.value-2*gift.value,'{} - 2 * {}'.format(format_number(original.value),format_number(gift.value)))


def _mass_basket(p, ns):
    """Bind ingredient prices by material and convert grams to kilograms."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=len(counts) or not 2<=len(money)<=4 or not _has(r'\b(?:pay|cost|spend)\b',q):
        return None
    amounts={}
    for c in counts:
        m=re.match(r'\s*(kg|kilograms?|grams?|g) of ([a-z]+)\b',t[c.end:])
        if not m:
            return None
        unit,material=m.groups()
        if material in amounts:
            return None
        amounts[material]=c.value/(1000 if unit in ('g','gram','grams') else 1)
    terms=[];used=set()
    for n in money:
        if not _has(r'^\s+per (?:kilogram|kg)\b',t[n.end:]):
            return None
        m=re.search(r'\b(?:the )?([a-z]+)(?: costs?)?\s*$',t[_bounds(t,n)[0]:n.start])
        if not m or m.group(1) not in amounts or m.group(1) in used:
            return None
        material=m.group(1);used.add(material);terms.append(amounts[material]*n.value)
    return _answer(p,sum(terms,Fraction(0)),_expr(terms))


def _pack_size_price(p, ns):
    """A box with an explicit piece count supplies the quoted stock."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=1 or len(counts)!=2 or not _has(r'\b(?:pay|paid|cost|spend)\b',q):
        return None
    stock,size=counts
    if not stock.start<size.start<money[0].start or not _has(r'\b(?:a|an)\s*$',t[stock.end:size.start]):
        return None
    box=re.match(r'\s+(?:box|pack|bag) of ([a-z ]+?) costs?\s*$',t[size.end:money[0].start])
    if not box or not _same(_phrase(box.group(1)),_phrase(t[stock.end:])) or size.value<=0:
        return None
    boxes=stock.value/size.value
    return _answer(p,Fraction(-(-boxes.numerator//boxes.denominator))*money[0].value,
        'ceil({} / {}) * {}'.format(*(format_number(n.value) for n in (stock,size,money[0]))))


def _ratio_allocation(p, ns):
    """An explicitly labeled two-part ratio divides a monetary total."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=1 or len(counts)!=2 or not _has(r'\bratio(?: of)?\s*$',t[:counts[0].start]):
        return None
    a,b=counts
    if t[a.end:b.start].strip()!=':' or a.value<=0 or b.value<=0:
        return None
    m=re.match(r'\s+for ([a-z ]+?) and ([a-z ]+?),? respectively[.]',t[b.end:])
    if not m:
        return None
    question_words={_singular(w) for w in re.findall(r'[a-z]+',q)}
    categories=[{_singular(w) for w in label.split()} for label in m.groups()]
    matched=[i for i,words in enumerate(categories) if words<=question_words]
    if len(matched)!=1:
        return None
    part=(a,b)[matched[0]].value
    return _answer(p,money[0].value*part/(a.value+b.value),'{} * {} / ({} + {})'.format(
        format_number(money[0].value),format_number(part),format_number(a.value),format_number(b.value)))


def _ratio_named_share(p, ns):
    """A named list and its corresponding ratio scale a known person's share."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=1 or len(counts)<3 or not _has(r'\bin the ratio\b',p.body):
        return None
    group=counts[0];ratios=counts[1:]
    if group.value!=len(ratios) or any(n.value<=0 for n in ratios):
        return None
    if not _has(r'\bin the ratio\s*$',t[group.end:ratios[0].start]) or any(t[a.end:b.start].strip()!=':' for a,b in zip(ratios,ratios[1:])):
        return None
    listing=p.text[group.end:ratios[0].start]
    names=re.findall(r'\b[A-Z][a-z]+\b',listing)
    if len(names)!=len(ratios) or len(set(names))!=len(names):
        return None
    known=re.search(r'\b([a-z]+) (?:got|received|gets)\s*$',t[ratios[-1].end:money[0].start])
    targets=[i for i,name in enumerate(names) if _has(r'\b'+re.escape(name.lower())+r'\b',q)]
    if not known or known.group(1) not in [name.lower() for name in names] or len(targets)!=1:
        return None
    known_index=[name.lower() for name in names].index(known.group(1))
    return _answer(p,money[0].value*ratios[targets[0]].value/ratios[known_index].value,
        '{} * {} / {}'.format(*(format_number(v) for v in (money[0].value,ratios[targets[0]].value,ratios[known_index].value))))


def _relative_price_cash(p, ns):
    """Buy the dearer of two multiplicatively compared prices using cash."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=2 or len(counts)!=1 or not _has(r'\b(?:left|remaining)\b',q):
        return None
    base,cash=money;factor=counts[0]
    if not base.start<factor.start<cash.start or not _has(r'\bcheapest\b',t[:base.start]):
        return None
    if not _has(r'\bmost expensive\b[^.;]*$',t[base.end:factor.start]) or not _has(r'^\s+times (?:more expensive|as expensive)\b',t[factor.end:]):
        return None
    if not _has(r'\bbuys the most expensive\b',q) or not _has(r'\b(?:has|have|had)\s*$',t[factor.end:cash.start]):
        return None
    return _answer(p,cash.value-base.value*factor.value,'{} - {} * {}'.format(*(format_number(n.value) for n in (cash,base,factor))))


def _receipts_refund(p, ns):
    """Gross receipts less explicitly returned funds, ignoring a business label."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=3 or not _has(r'\btaken altogether\b',q):
        return None
    for c in counts:
        if not re.search(r'\b[A-Z][a-z]+\s*$',p.text[:c.start]) or not re.match(r'\s+[A-Z][a-z]+(?: [A-Z][a-z]+)* Company\b',p.text[c.end:]):
            return None
    a,b,refund=money
    if not _has(r'\btaken\b[^.;]*\bworth\s*$',t[:a.start]) or not _has(r'\band\b[^.;]*\bworth\s*$',t[a.end:b.start]):
        return None
    if not _has(r'^\s+has had to be returned\b',t[refund.end:]):
        return None
    return _answer(p,a.value+b.value-refund.value,'{} + {} - {}'.format(*(format_number(n.value) for n in money)))


def _subscription_comparison(p, ns):
    """Base subscription plus two extras, one a fixed amount cheaper."""
    t,q=p.text.lower(),p.question
    if len(ns)!=3 or any(n.kind!='money' for n in ns) or not _has(r'\btotal monthly (?:payment|cost|bill)\b',q):
        return None
    base,extra,difference=ns
    if not all(_has(r'^\s+per month\b',t[n.end:]) for n in (base,extra)) or not _has(r'^\s+less per month than\b',t[difference.end:]):
        return None
    source=re.search(r'\badds the ([a-z ]+?),[^.;]*$',t[base.end:extra.start])
    target=re.search(r'\bthe ([a-z ]+?) costs?\s*$',t[extra.end:difference.start])
    comparison=re.match(r'\s+less per month than the ([a-z ]+?)[.]',t[difference.end:])
    if not source or not target or not comparison or source.group(1)!=comparison.group(1):
        return None
    if not re.search(r'\badds (?:the )?'+re.escape(source.group(1))+r' and (?:the )?'+re.escape(target.group(1))+r',?\s*$',p.body):
        return None
    return _answer(p,base.value+2*extra.value-difference.value,'{} + 2 * {} - {}'.format(*(format_number(n.value) for n in ns)))


def _priced_tokens(p, ns):
    """Per-person games use tokens sold at an explicit tokens-for-money quote."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=1 or len(counts)!=4 or not _has(r'\b(?:cost|pay|spend)\b',q):
        return None
    people,bundle,rate,games=counts
    if not people.start<bundle.start<money[0].start<rate.start<games.start or bundle.value<=0:
        return None
    quote=re.search(r'\b([a-z]+) cost\s*$',t[people.end:bundle.start])
    event=re.search(r'\beach ([a-z]+) costs?\s*$',t[money[0].end:rate.start])
    if not quote or not event or not _has(r'^\s+for\s*$',t[bundle.end:money[0].start]):
        return None
    if _unit(t[rate.end:])!=_singular(quote.group(1)) or _unit(t[games.end:])!=_singular(event.group(1)):
        return None
    party=_head(_phrase(t[people.end:]))
    if not party or not _has(r'\ball (?:his|her|their) '+re.escape(party)+r's\b',t[rate.end:games.start]) or not _has(r'^\s+[a-z]+ each\b',t[games.end:]):
        return None
    return _answer(p,people.value*games.value*rate.value*money[0].value/bundle.value,
        '{} * {} * {} * {} / {}'.format(*(format_number(n.value) for n in (people,games,rate,money[0],bundle))))


def _hourly_group_share(p, ns):
    """Weekly aggregate hours apportioned to a queried share of equal classes."""
    t,q=p.text.lower(),p.question
    money,counts=_parts(ns)
    if len(money)!=1 or len(counts)!=4 or not _has(r'\b(?:earn|earned|make)\b',q):
        return None
    groups,hours,selected,weeks=counts
    if not groups.start<hours.start<len(p.body)<=selected.start<weeks.start<money[0].start:
        return None
    if not _has(r'^\s+hours (?:a|per|each) week altogether\b',t[hours.end:]) or _unit(t[weeks.end:])!='week':
        return None
    if not _same(_phrase(t[groups.end:]),_phrase(t[selected.end:])) or not 0<selected.value<=groups.value:
        return None
    if not _has(r'\bhourly rate per (?:class|course|session) is\s*$',t[weeks.end:money[0].start]):
        return None
    return _answer(p,hours.value*selected.value/groups.value*weeks.value*money[0].value,
        '{} * {} / {} * {} * {}'.format(*(format_number(n.value) for n in (hours,selected,groups,weeks,money[0]))))

def solve(problem):
    t = problem.text.lower()
    if _has(r'\baverage\b',problem.question):
        return None
    if not _has(r'[$£€]|\b(?:dollars?|cents?|euros?)\b', t):
        return None
    ns = _numbers(problem)
    if not 1 <= len(ns) <= 16 or any(n.kind == 'percent' or n.value < 0 for n in ns):
        return None
    if len(_currencies(problem, ns)) > 1:
        return None
    for rule in (_ledger, _weekly_purchases, _party_tickets, _catalog, _bogo,
                 _quoted_comparison, _payback, _wage_budget, _missing_equal_price,
                 _denomination, _overage, _tips, _equal_category_purchase,
                 _work_comparison, _monthly_extra, _missing_receipt, _sales_interval,
                 _scaled_purchase, _value_multiplier, _consumable_duration,
                 _daily_events, _weekly_event, _package_weight, _per_serving,
                 _promotion_savings, _contributors, _one_each_budget, _register,
                 _repeated_deposit, _recipient_gifts, _restated_rate, _calendar_daily,
                 _energy, _scaled_total_unit, _category_difference, _area_sum,
                 _missing_categories, _relative_cost_pair, _single_item_shortage,
                 _pronoun_stock, _repeated_saving, _savings_meet, _replacement_net,
                 _hourly_job, _two_costs_difference, _coin_change, _coin_inventory,
                 _letter_cost, _party_events, _container_margin, _package_duration,
                 _shopping_missing_price, _barter, _overcharge, _equal_transfer,
                 _mass_basket, _pack_size_price, _ratio_allocation, _ratio_named_share,
                 _relative_price_cash, _receipts_refund, _subscription_comparison,
                 _priced_tokens, _hourly_group_share):
        result = rule(problem, ns)
        if result is not None:
            return result
    return None
