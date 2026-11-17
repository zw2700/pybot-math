"""Money ledgers and explicitly linked purchase quantities.

Money is classified by its transaction, and prices are multiplied only by
counts with a matching unit. Unused quantities or unsupported relations cause
abstention. All computations use rational arithmetic.
"""
import re
from dataclasses import replace
from fractions import Fraction

from ..numbers import format_number


def _has(pattern, text):
    return re.search(pattern, text) is not None


def _singular(word):
    irregular = {'people': 'person', 'children': 'child', 'men': 'man',
                 'women': 'woman', 'feet': 'foot', 'inches': 'inch',
                 'pies': 'pie', 'kg': 'kilogram', 'g': 'gram'}
    if word in irregular:
        return irregular[word]
    if word.endswith('ies'):
        return word[:-3] + 'y'
    if word.endswith(('ches', 'shes', 'sses', 'xes')):
        return word[:-2]
    return word[:-1] if word.endswith('s') and not word.endswith('ss') else word


_STOP = set(('a an the of in on at for to from with by and or but that which who '
             'is are was were has have had will would can could does did do '
             'each every per cost costs costing worth needs need bought buys '
             'buy sold sells sell spent spends spend gets get takes take '
             'paid pays pay earned earns earn made make makes left remaining '
             'only these those his her their its them they it he she '
             'over about into out all total then currently now washed charging so').split())


def _noun(tail):
    tail = re.sub(r'^\s*(?:of )?(?:(?:the|their|his|her|such) )?', '', tail)
    words = re.match(r'\s*[- ]?([a-z]+(?:[ -]+[a-z]+){0,5})', tail)
    result = []
    if words:
        for word in re.split(r'[ -]+', words.group(1)):
            if word in _STOP:
                break
            result.append(word)
            if word in ('day', 'days', 'week', 'weeks', 'month', 'months',
                        'year', 'years', 'hour', 'hours', 'pound', 'pounds',
                        'kilogram', 'kilograms', 'gram', 'grams'):
                break
    return _singular(result[-1]) if result else ''


def _money(text, n):
    return n.kind == 'money' or _has(r'^\s*[- ]?(?:dollars?|cents?|euros?)\b', text[n.end:])


def _amount(text, n):
    return n.value


def _answer(value, expression):
    if value < 0:
        return None
    return value, 'Money total: {} = {} dollars.'.format(expression, format_number(value))


def _sum(values):
    return sum(values, Fraction(0))


def _expr(values):
    return ' + '.join(format_number(v) for v in values)


def _bounds(text, n):
    before = list(re.finditer(r'[.!?;](?:\s|$)', text[:n.start]))
    after = re.search(r'[.!?;](?:\s|$)', text[n.end:])
    return (before[-1].end() if before else 0,
            n.end + after.start() if after else len(text))


def _role(text, n, lower):
    """Classify a monetary amount using the local transaction clause."""
    prefix = text[lower:n.start]
    suffix = text[n.end:]
    if _has(r'^\s+withdrawal\b', suffix):
        return 'expense'
    if _has(r'^\s+deposit\b', suffix):
        return 'income'
    if _has(r'\b(?:gave|gives?|given|offered) (?:him|her|them)\s*$|\b(?:is|was) given\s*$', prefix):
        return 'income'
    if _has(r'^\s*(?:left(?: over)?|remaining|in change|change)\b', suffix):
        return 'remaining'
    if _has(r'\b(?:discount|rebate|coupon|off)\b[^,.;]*$', prefix):
        return 'discount'
    if _has(r'\bwith\s*$', prefix) and not _has(r'^\s+(?:bill|note)\b', suffix):
        return 'balance'
    if _has(r'\b(?:paid|pays?|pay)\s+(?:using\s+|with\s+)?(?:an?\s+)?$', prefix) and _has(r'^\s+(?:bill|note)\b', suffix):
        return 'tender'
    if _has(r'\b(?:using|with|hands?|handed|gives?|gave)\s+(?:an?\s+)?$', prefix) and _has(r'^\s+(?:bill|note)\b', suffix):
        return 'tender'
    if _has(r'\b(?:budget|balance) (?:is|was)\s*$', prefix):
        return 'balance'
    if _has(r'\b(?:is|are|was|were)\s*$', prefix) and not _has(r'\b(?:salary|earn|earned|income|balance)\b[^.;]*$', prefix):
        return 'expense'
    events = list(re.finditer(r'\b(?:costs?|costing|worth|charges?|charged|spends?|spent|'
                             r'buys?|bought|pays?|paid|contributes?|purchase[sd]?|priced|'
                             r'has|have|had|going for|saved?|savings|budget|earns?|earned|'
                             r'salary|gets?|got|receives?|received|makes?|made|sold|sells?)\b', prefix))
    if events:
        event = events[-1].group()
        if event in ('get', 'gets', 'got') and _has(r'\b(?:for|at)\s*$', prefix[events[-1].end():]):
            return 'expense'
        if event == 'going for':
            return 'expense'
        if event in ('has', 'have', 'had', 'budget', 'savings'):
            return 'balance'
        if event in ('save', 'saves', 'saved', 'earn', 'earns', 'earned', 'salary',
                     'get', 'gets', 'got', 'receive', 'receives', 'received',
                     'make', 'makes', 'made', 'sold', 'sell', 'sells'):
            return 'income'
        return 'expense'
    if _has(r'\b(?:is|are|was|were)\s*$', prefix):
        return 'expense'
    # Lists inherit the transaction from the earlier coordinated clause.
    return None


def _finish(p, terms):
    """Answer only a query whose unknown follows from the classified ledger."""
    q = p.question
    # A computed basket total is not a per-item price or a coin count.
    if _has(r'\b(?:each|per|every|coins?|bills?|notes?)\b', re.split(r'\b(?:if|when)\b', q)[0]):
        return None
    groups = {k: [] for k in ('expense', 'income', 'balance', 'tender', 'remaining', 'discount')}
    for role, value in terms:
        if role not in groups:
            return None
        groups[role].append(value)
    e, i, b, t, r, d = (groups[k] for k in ('expense', 'income', 'balance', 'tender', 'remaining', 'discount'))
    if d:
        return None
    expenses, income = _sum(e), _sum(i)
    if _has(r'\b(?:at first|originally|start(?:ed)? with|initially|beginning|before)\b', q):
        if e and len(r) == 1 and not (i or b or t):
            return _answer(expenses+r[0], '('+_expr(e)+') + '+format_number(r[0]))
        return None
    if _has(r'\b(?:change|back)\b', q):
        cash = t or b
        if e and len(cash) == 1 and not (i or r) and not (t and b):
            return _answer(cash[0]-expenses, format_number(cash[0])+' - ('+_expr(e)+')')
        return None
    if _has(r'\bmore\b.*\b(?:need|earn|save)|\b(?:need|earn|save)\b.*\bmore\b', q) or (
            _has(r'\bneed to (?:earn|save)\b|\b(?:owe|owes)\b', q)):
        if e and len(b) == 1 and not (i or t or r):
            return _answer(expenses-b[0], '('+_expr(e)+') - '+format_number(b[0]))
        return None
    if _has(r'\b(?:left|remaining|save[ds]?)\b', q):
        if e and (i or b or t) and not r and len(b)+len(t) <= 1:
            available = income+_sum(b)+_sum(t)
            return _answer(available-expenses, format_number(available)+' - ('+_expr(e)+')')
        return None
    # A missing expense can be inferred from earnings, known outgoings and remainder.
    if (_has(r'\b(?:pay|spend|spent|lost|cost)\b', q) or _has(r'^how much (?:is|are|was) ', q)) and len(r) == 1 and (i or b) and not t:
        if len(i)+len(b) == 1:
            total = income+_sum(b)
            return _answer(total-expenses-r[0], '{} - ({}) - {}'.format(format_number(total), _expr(e) or '0', format_number(r[0])))
        return None
    if _has(r'\b(?:more|less|compared|difference)\b', q):
        return None
    if e and i and not (b or t or r) and _has(r'\b(?:spent|spend|pay|cost)\b', q) and _has(r'\b(?:sells?|sold|selling)\b', p.body):
        return _answer(expenses-income, '('+_expr(e)+') - ('+_expr(i)+')')
    if not (b or t or r):
        if e and not i and _has(r'\b(?:pay|paid|spend|spent|cost|costs|price|total)\b', q):
            return _answer(expenses, _expr(e))
        if i and not e and _has(r'\b(?:earn|earned|make|made|money|collected|receive)\b', q):
            return _answer(income, _expr(i))
    return None


def _denominator(text, n, previous_end):
    """Unit in 'price per unit', 'each unit costs price', or 'price each'."""
    start, end = _bounds(text, n)
    suffix = text[n.end:end]
    m = re.match(r'\s*(?:dollars?|cents?|pounds?|euros?)?\s*(?:per|an?|for (?:each|a|an))\s+([a-z]+(?: [a-z]+){0,3})', suffix)
    if m:
        return _noun(m.group(1))
    # Postposed each takes its unit from the item being priced.
    if _has(r'^\s*(?:(?:dollars?|cents?)\s+)?each\b', suffix):
        prefix = text[start:n.start]
        m = re.search(r'\b([a-z]+(?:-[a-z]+)?)\s+(?:(?:that|which)\s+)?(?:costs?|are|were|is|was)\s*$', prefix)
        if m:
            return _noun(m.group(1)) if m.group(1) not in ('they', 'them', 'these', 'those') else '*'
        return '*'  # must bind locally to an explicit preceding count
    prefix = text[start:n.start]
    if _has(r'\beach of which costs?\s*$', prefix):
        return '*'
    if _has(r'\beach (?:costing|costs?)(?: (?:him|her|them))?\s*$', prefix):
        return '*'
    m = re.search(r'\b(?:each|every|one|an?)\s+([a-z]+(?: [a-z]+){0,3}?)\s+(?:costs?|is|was|at|for|costing)\s*(?:\w+\s+){0,2}$', prefix)
    if m:
        return _noun(m.group(1))
    m = re.search(r'\b(?:for|in) each ([a-z]+)\b[^.;]*$', prefix)
    if m:
        return _singular(m.group(1))
    m = re.match(r'\s+in each ([a-z]+)', suffix)
    if m:
        return _singular(m.group(1))
    # 'a pound of X is going for PRICE'
    m = re.search(r'\b(?:an?|each)\s+(pound|kilogram|gram|hour)\b[^.;]*?\b(?:for|costs?|charges?)\s*$', prefix)
    if m:
        return m.group(1)
    return None


def _purchases(p, ns):
    text = p.text.lower()
    money = [n for n in ns if _money(text, n)]
    counts = [n for n in ns if not _money(text, n)]
    if not money:
        return None
    # Nonlinear and comparative relations need dedicated schemas.
    if _has(r'\b(?:percent|twice|thrice|half|thirds?|fourths?|quarters?|ratio|profit|interest|tax rate|times as|more than|less than)\b', text):
        return None
    if _has(r'\b(?:discount|rebate|coupon)\b', text):
        return None
    if any(n.start >= len(p.body) and _money(text, n) for n in ns):
        return None
    # An unnumbered query period must agree with a stated recurring period.
    periods = set(re.findall(r'\b(?:each|every|per|a) (day|week|month|year)\b', p.body))
    if _has(r'\b(?:each|every) (?:morning|afternoon|evening|night)\b', p.body):
        periods.add('day')
    query_periods = set(re.findall(r'\b(?:each|every|per|a|one) (day|week|month|year)\b', p.question))
    if query_periods and query_periods != periods:
        return None
    used, terms = set(), []
    for mi, n in enumerate(money):
        lower = money[mi-1].end if mi else 0
        role = _role(text, n, lower)
        if role is None and terms:
            # Coordinate lists such as 'spent $X on A and $Y on B'.
            fragment = text[lower:n.start]
            if _has(r'\b(?:and|plus)\b|,', fragment) and not _has(r'[.;]', fragment):
                role = terms[-1][0]
        if role is None:
            return None
        denom = _denominator(text, n, lower)
        # A singular item bought for a stated price is a fixed purchase when
        # no explicit count or repeated-unit cue calls for multiplication.
        start, end = _bounds(text, n)
        if denom and denom != '*' and not any(_noun(text[c.end:]) == denom for c in counts):
            prefix = text[start:n.start]
            next_start = min([k.start for k in ns if k.start > n.end] or [end])
            context = prefix + text[n.end:min(end, next_start)]
            if not _has(r'\b(?:each|every|per)\b', context):
                denom = None
        if denom in ('day', 'week', 'month', 'year') and not counts:
            periods = set(re.findall(r'\b(?:per|a|each|every) (day|week|month|year)\b', p.body))
            if periods == {denom} and not _has(r'\b(?:each|per|every)\b', p.question):
                denom = None
        if denom:
            if role not in ('expense', 'income'):
                return None
            matching = [c for c in counts if id(c) not in used and _noun(text[c.end:]) == denom]
            if denom == '*':
                start, end = _bounds(text, n)
                matching = [c for c in counts if id(c) not in used and start <= c.start < n.start]
                if len({_noun(text[c.end:]) for c in matching}) > 1:
                    return None
            if not matching:
                # A count expressed as N of them or N times can refer back to
                # the sole priced item. This is safe only with one unit price.
                if len(money) <= 2:
                    matching = [c for c in counts if id(c) not in used and _has(r'^\s+(?:of them|times)\b', text[c.end:])]
            if not matching:
                return None
            # Count statements may be added, but not inventories with removals.
            if len(matching) > 1 and _has(r'\b(?:lost|gave|sold|remaining|rest|only|already)\b', p.body):
                return None
            count = _sum(c.value for c in matching)
            for c in matching:
                used.add(id(c))
            value = _amount(text, n)*count
        else:
            value = _amount(text, n)
        terms.append((role, value))
    if len(used) != len(counts):
        return None
    return _finish(p, terms)


def _discount(p, ns):
    text = p.text.lower()
    if not _has(r'\bdiscount\b', text):
        return None
    money = [n for n in ns if _money(text, n)]
    counts = [n for n in ns if not _money(text, n)]
    if not counts and 2 <= len(money) <= 6 and _has(r'\bdiscount\b', p.question):
        paid = [n for n in money if _has(r'\b(?:pays?|paid|spent)\s*$', text[:n.start])]
        if len(paid) == 1:
            actual = paid[0]
            original = [n for n in money if n is not actual]
            if all(_has(r'\b(?:costs?|bought|buys?)\b', text[:n.start]) for n in original):
                return _answer(_sum(n.value for n in original)-actual.value, '('+_expr(n.value for n in original)+') - '+format_number(actual.value))
    if len(money) != 2 or len(counts) != 1 or any(n.start >= len(p.body) for n in ns):
        return None
    price, other = money
    count = counts[0]
    if _has(r'\b(?:percent|more|less|twice)\b', text):
        return None
    if _has(r'\bhow much (?:was|is).*discount\b', p.question):
        if _has(r'\b(?:cost|costs|for)\s*$', text[:price.start]) and _has(r'\b(?:pay|paid)\s*$', text[:other.start]):
            return _answer(price.value*count.value-other.value, '{} * {} - {}'.format(*map(format_number, (price.value, count.value, other.value))))
    if _has(r'\b(?:pay|paid|cost|spend|spent)\b', p.question) and _has(r'\bdiscount of\s*$', text[:other.start]) and _has(r'^\s+each\b', text[other.end:]):
        if _noun(text[count.end:]) and (_noun(text[count.end:]) in ('piece', 'item') or _denominator(text, price, 0) in (None, '*', _noun(text[count.end:]))):
            return _answer((price.value-other.value)*count.value, '({} - {}) * {}'.format(*map(format_number, (price.value, other.value, count.value))))
    return None


def _quantities(p):
    """Drop only grammatical unit ones and exact repeated query references."""
    text = p.text.lower()
    ns = []
    for n in p.numbers:
        if n.value == 1 and _has(r'^\s+[a-z]+\s+cost(?:s| is)?\b', text[n.end:]):
            continue
        if n.start >= len(p.body) and not _money(text, n) and any(
                k.value == n.value and _noun(text[k.end:]) == _noun(text[n.end:])
                for k in ns):
            continue
        if _money(text, n) and _has(r'^\s+cents?\b', text[n.end:]):
            n = replace(n, value=n.value/100)
        ns.append(n)
    return ns


def _area_price(p, ns):
    if len(ns) != 3:
        return None
    text = p.text.lower()
    a, b, price = ns
    if not _money(text, price) or _money(text, a) or _money(text, b):
        return None
    relation = text[a.end:b.start]
    unit = re.fullmatch(r'\s*[- ]?(foot|feet|meter|meters|yard|yards|inch|inches)\s+by\s+', relation)
    if not unit:
        return None
    unit = _singular(unit.group(1))
    if not _has(r'^\s*[- ]?(?:'+unit+r'|'+unit+r's)\b', text[b.end:]):
        return None
    if not _has(r'^\s+per square '+unit+r'\b', text[price.end:]):
        return None
    if not _has(r'\b(?:cost|pay|price|spend)\b', p.question):
        return None
    return _answer(a.value*b.value*price.value, ' * '.join(format_number(n.value) for n in ns))


def _bundle(p, ns):
    """A set of item prices repeated once for every stated recipient."""
    text = p.text.lower()
    money = [n for n in ns if _money(text, n)]
    counts = [n for n in ns if not _money(text, n)]
    if len(counts) != 1 or len(money) < 2 or any(n.start >= len(p.body) for n in ns):
        return None
    count = counts[0]
    unit = _noun(text[count.end:])
    per_person = _has(r'\beach '+re.escape(unit)+r'\b[^.;]*\bneeds?\b', p.body)
    kit = _has(r'\beach (?:piece|set|kit|bundle|package)\b[^.;]*\b(?:consists of|contains|includes)\b', p.body)
    if kit and not _has(r'\bfor (?:all )?(?:(?:the|his|her|their) )?$', text[:count.start]):
        kit = False
    if not unit or not (per_person or kit):
        return None
    if _has(r'\b(?:left|more|remaining|change|discount|save|profit|earn)\b', p.question):
        return None
    if not _has(r'\b(?:cost|pay|spend|spent)\b', p.question):
        return None
    if any(_role(text, n, 0) not in ('expense',) for n in money):
        return None
    return _answer(_sum(n.value for n in money)*count.value,
                   '('+_expr(n.value for n in money)+') * '+format_number(count.value))


def _chain(p, ns):
    """Follow count -> contents per count -> unit price, with explicit units."""
    text = p.text.lower()
    if not 3 <= len(ns) <= 5 or sum(_money(text, n) for n in ns) != 1:
        return None
    if _has(r'\b(?:left|more|remaining|change|discount|profit|less|half|twice|tax)\b', text):
        return None
    units, denoms = {}, {}
    for j, n in enumerate(ns):
        units[j] = 'money' if _money(text, n) else _noun(text[n.end:])
        if not units[j]:
            return None
        start, end = _bounds(text, n)
        prefix = text[start:n.start]
        stop = ns[j+1].start if j+1 < len(ns) else len(text)
        suffix = text[n.end:min(end, stop)]
        if units[j] == 'money':
            denom = _denominator(text, n, 0)
            if denom == '*':
                sale = re.search(r'\b(?:sells?|sold) (?:the |these |those )?([a-z]+)\s+for\s*$', prefix)
                denom = _singular(sale.group(1)) if sale else None
            if not denom:
                return None
            denoms[j] = denom
            continue
        m = re.search(r'\b(?:per|a|each|every) ([a-z]+)\b', suffix)
        if m:
            denoms[j] = _singular(m.group(1))
            continue
        m = re.search(r'\b(?:in|on) each ([a-z]+)\b', suffix)
        if m:
            denoms[j] = _singular(m.group(1))
            continue
        if _has(r'\beach\b', suffix) and j and units[j-1] != 'money':
            denoms[j] = units[j-1]
            continue
        m = re.search(r'\beach ([a-z]+(?: [a-z]+){0,2}?)\s+(?:(?:is|was) (?:cut|divided) )?(?:into|contains?|holds?|needs?|gets?|gives?|buys?|has|have)\s*$', prefix)
        if m:
            denoms[j] = _noun(m.group(1))
            continue
        # A sentence containing only one quantity: "In a day, A makes N items."
        sentence_ns = [k for k in ns if start <= k.start < end]
        m = re.search(r'\b(?:in a|each|every|per) (day|week|month|year|hour)\b', prefix)
        if m and len(sentence_ns) == 1 and units[j] != m.group(1):
            denoms[j] = m.group(1)
    if len(denoms) != len(ns)-1:
        return None
    root = next(j for j in units if units[j] == 'money')
    used = set()
    def evaluate(j):
        if j in used:
            return None
        used.add(j)
        value = ns[j].value
        if j in denoms:
            matches = [k for k in units if k != j and units[k] == denoms[j]]
            if len(matches) != 1:
                return None
            count = evaluate(matches[0])
            if count is None:
                return None
            value *= count
        return value
    value = evaluate(root)
    if value is None or len(used) != len(ns):
        return None
    role = _role(text, ns[root], 0)
    if _has(r'\b(?:make|earn|made|earned)\b', p.question) and _has(r'\b(?:sell|sells|sold)\b', text):
        role = 'income'
    return _finish(p, [(role, value)])


def _threshold_rebate(p, ns):
    text = p.text.lower()
    if len(ns) != 3 or not all(_money(text, n) for n in ns):
        return None
    a, threshold, total = ns
    if not _has(r'\b(?:get|save|off)\s*$', text[:a.start]):
        return None
    if not re.fullmatch(r'\s+for every\s+', text[a.end:threshold.start]):
        return None
    if not _has(r'^\s+that you spend\b', text[threshold.end:]):
        return None
    if not _has(r'\bbefore discounts\b', text[total.end:]):
        return None
    if not _has(r'\b(?:pay|paying|paid)\b', p.question) or threshold.value <= 0:
        return None
    value = total.value-a.value*(total.value//threshold.value)
    return _answer(value, '{} - {} * floor({} / {})'.format(*map(format_number, (total.value, a.value, total.value, threshold.value))))


def _profit(p, ns):
    """Net sales, with either a total input cost or equal per-item costs."""
    if not _has(r'\bprofit\b', p.question):
        return None
    text = p.text.lower()
    money = [n for n in ns if _money(text, n)]
    counts = [n for n in ns if not _money(text, n)]
    if len(money) != 2 or len(counts) != 1:
        return None
    cost, sales = money
    if not cost.start < sales.start or not _has(r'\b(?:bought|buys?|spent|spends?)\b', text[:cost.start]):
        return None
    if not _has(r'\b(?:sell|sells|sold)\b', text[cost.end:sales.start]):
        return None
    if _has(r'\b(?:percent|discount|left|remaining|unsold)\b', text):
        return None
    count = counts[0]
    if not _noun(text[count.end:]):
        return None
    # A unit price is stated for the same noun that is bought and resold.
    if _has(r'\bspent\s*$', text[:cost.start]):
        value = sales.value*count.value-cost.value
        expr = '{} * {} - {}'.format(*map(format_number, (sales.value, count.value, cost.value)))
    else:
        if count.start < cost.start and not _has(r'^\s+each\b', text[cost.end:]):
            return None
        # With a singular/collective item followed by "for", both prices
        # describe that same item; reject total-cost wording.
        if not _has(r'\b(?:for|at)\s*$', text[:cost.start]) or not _has(r'\b(?:for|at)\s*$', text[:sales.start]):
            return None
        value = (sales.value-cost.value)*count.value
        expr = '({} - {}) * {}'.format(*map(format_number, (sales.value, cost.value, count.value)))
    return _answer(value, expr)


def _shortfall(p, ns):
    """Buy the unmet part of an explicitly stated requirement at a unit price."""
    text = p.text.lower()
    money = [n for n in ns if _money(text, n)]
    counts = [n for n in ns if not _money(text, n)]
    if len(money) != 1 or len(counts) != 2:
        return None
    goal, available = counts
    if not _has(r'\b(?:needs?|requires?|required)\b', text[:goal.start]):
        return None
    if not _has(r'\b(?:free|already|currently|has only|have only)\b', text[goal.end:]):
        return None
    denom = _denominator(text, money[0], 0)
    if not denom or _noun(text[goal.end:]) != denom or _noun(text[available.end:]) != denom:
        return None
    if not _has(r'\b(?:pay|cost|spend)\b', p.question):
        return None
    value = (goal.value-available.value)*money[0].value
    return _answer(value, '({} - {}) * {}'.format(*map(format_number, (goal.value, available.value, money[0].value))))


def _package_price(p, ns):
    """A known package price and contents, and a requested amount of contents."""
    text = p.text.lower()
    if len(ns) != 3 or sum(_money(text, n) for n in ns) != 1:
        return None
    price = next(n for n in ns if _money(text, n))
    counts = [n for n in ns if n is not price]
    size, needed = counts
    unit = _noun(text[size.end:])
    if not unit or unit != _noun(text[needed.end:]) or size.value <= 0:
        return None
    if _has(r'\b(?:left|more|remaining|change|discount|profit|less)\b', text):
        return None
    # The unit size must be linked to the price in the same sentence.
    start, end = _bounds(text, size)
    if not start <= price.start < end:
        return None
    sentence = text[start:end]
    package = _has(r'\b(?:has|contains|holds|lasts)\b', sentence)
    if not package or not _has(r'\b(?:costs?|price)\b', sentence):
        return None
    if not _has(r'\b(?:needs?|buy|pay|cost)\b', p.question+' '+text[end:]):
        return None
    count = needed.value/size.value
    # No rounding assumptions about partial packages.
    if count.denominator != 1:
        return None
    return _answer(count*price.value, '{} / {} * {}'.format(*map(format_number, (needed.value, size.value, price.value))))


def _measured_price(p, ns):
    """Scale an observed total price by two amounts of the same unit."""
    text = p.text.lower()
    money = [n for n in ns if _money(text, n)]
    counts = [n for n in ns if not _money(text, n)]
    if len(money) != 1 or len(counts) != 2:
        return None
    price = money[0]
    base, target = counts
    unit = _noun(text[base.end:])
    if not unit or unit != _noun(text[target.end:]) or base.value <= 0:
        return None
    if not base.start < len(p.body) <= target.start:
        return None
    if _has(r'\b(?:left|more|remaining|change|discount|profit|less|each|per|every)\b', text):
        return None
    if not _has(r'\b(?:paid|pays?|costs?)\b', text[:base.end]) or not _has(r'\b(?:pay|cost)\b', p.question):
        return None
    start, end = _bounds(text, base)
    if not start <= price.start < end:
        return None
    return _answer(price.value*target.value/base.value, '{} * {} / {}'.format(*map(format_number, (price.value, target.value, base.value))))


def _depreciation(p, ns):
    """Initial value minus an explicitly stated loss per period."""
    text = p.text.lower()
    money = [n for n in ns if _money(text, n)]
    counts = [n for n in ns if not _money(text, n)]
    if len(money) != 2 or len(counts) != 1 or not _has(r'\bworth\b', p.question):
        return None
    losses = [n for n in money if _has(r'\b(?:down in value|loses value|depreciates)\b[^.;]*$', text[:n.start])]
    if len(losses) != 1:
        return None
    loss = losses[0]
    initial = next(n for n in money if n is not loss)
    if not _has(r'\b(?:bought|purchased|initially|originally)\b[^.;]*$', text[:initial.start]):
        return None
    period = _denominator(text, loss, 0)
    if not period or _noun(text[counts[0].end:]) != period:
        return None
    return _answer(initial.value-loss.value*counts[0].value,
                   '{} - {} * {}'.format(*map(format_number, (initial.value, loss.value, counts[0].value))))


def solve(problem):
    text = problem.text.lower()
    ns = _quantities(problem)
    ask = re.split(r'\b(?:if|when)\b', problem.question)[0]
    if _has(r'\b(?:each|per|every|coins?|bills?|notes?)\b', ask):
        return None
    if not 2 <= len(ns) <= 9 or any(n.value < 0 or n.kind == 'percent' for n in ns):
        return None
    if not _has(r'\b(?:money|dollars?|cents?|pay|paid|spend|spent|costs?|price|earn|earned|make|made|change|collected|discount|paying|payment|lost|profit|savings|save|saved|worth|balance|owe|owes)\b|^how much (?:is|are|was) ', problem.question):
        return None
    currencies = {n.raw[0] for n in ns if n.kind == 'money'}
    if _has(r'\bdollars?\b', text):
        currencies.add('$')
    if _has(r'\beuros?\b', text):
        currencies.add('€')
    if len(currencies) > 1:
        return None
    if _has(r'\b(?:equally|evenly|splits?|shared (?!expenses)|average|round trip|there and back)\b', text):
        return None
    # Distinct named people with their own transactions need an ownership
    # model. A pronoun recipient of a gift does not introduce another ledger.
    owners = set(re.findall(r'\b([A-Z][a-z]+) (?:has|had|spent|spends|earns|earned|saved|buys|bought)\b', problem.text[:len(problem.body)]))
    owners = {name for name in owners if name.lower() not in _STOP}
    if len(owners) > 1 and not _has(r'\b(?:total|together|combined|altogether|their|they)\b', problem.question):
        return None
    for rule in (_depreciation, _measured_price, _profit, _shortfall, _package_price, _area_price, _threshold_rebate, _discount, _bundle, _chain, _purchases):
        result = rule(problem, ns)
        if result is not None:
            value, working = result
            if currencies == {'£'}:
                working = working.replace('dollars', 'pounds')
            elif currencies == {'€'}:
                working = working.replace('dollars', 'euros')
            # State the requested monetary quantity, so the arbiter can
            # recognize this as an answer to the user's actual question.
            labels = ((r'\bchange\b', 'Change received'),
                      (r'\btax(?:es)?\b', 'Taxes paid'),
                      (r'\bdiscount\b', 'Discount'),
                      (r'\bprofit\b', 'Profit'),
                      (r'\b(?:save|saved|savings)\b', 'Savings'),
                      (r'\b(?:left|remaining)\b', 'Money remaining'),
                      (r'\b(?:earn|earned|make|made)\b', 'Earnings'),
                      (r'\b(?:cost|costs|price)\b', 'Cost'),
                      (r'\b(?:pay|paid|paying)\b', 'Payment'),
                      (r'\b(?:spend|spent)\b', 'Spending'))
            for pattern, label in labels:
                if _has(pattern, problem.question):
                    working = working.replace('Money total', label)
                    break
            if _has(r'\bin cents\b', problem.question):
                value *= 100
                working += ' In cents: {}.'.format(format_number(value))
            return value, working
    return None
