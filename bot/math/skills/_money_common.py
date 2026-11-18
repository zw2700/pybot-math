"""Shared exact money arithmetic, transaction roles and unit binding.

Only helpers live here; individual readers still account for every quantity.
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


def _money(text, n):
    return (n.kind == 'money'
            or _has(r'^\s*[- ]?(?:dollars?|cents?|euros?)\b', text[n.end:])
            or _has(r'^\s*[$£€](?!\s*\d)', text[n.end:]))


def _money_number(text, n):
    """Normalize a monetary quantity once, keeping the original offsets.

    An explicit currency symbol takes precedence over a trailing unit word.
    All later calculations use major currency units, including cent prices.
    """
    if not (_money(text, n) or _has(r'^-dollars?\b', text[n.end:])):
        return n
    cents = n.raw[:1] not in '$£€' and _has(r'^\s*cents?\b', text[n.end:])
    return replace(n, value=n.value / 100 if cents else n.value, kind='money')


def _currencies(p, ns):
    symbols = {n.raw[0] for n in ns if n.raw[:1] in '$£€'}
    for n in ns:
        suffix = re.match(r'\s*([$£€])(?!\s*\d)', p.text[n.end:])
        if suffix:
            symbols.add(suffix.group(1))
    for word, symbol in (('dollars?', '$'), ('euros?', '€')):
        if _has(r'\b' + word + r'\b', p.text.lower()):
            symbols.add(symbol)
    return symbols


def _bounds(text, n):
    before = list(re.finditer(r'[.!?;](?:\s|$)', text[:n.start]))
    after = re.search(r'[.!?;](?:\s|$)', text[n.end:])
    return (before[-1].end() if before else 0,
            n.end + after.start() if after else len(text))


def _role(text, n, lower):
    """Classify a monetary amount using the local transaction clause."""
    prefix = text[lower:n.start]
    suffix = re.sub(r'^\s*(?:[$£€]|dollars?\b|cents?\b|euros?\b)', '', text[n.end:])
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


_STOP = set(('a an the of in on at for to from with by and or but that which who '
             'is are was were has have had will would can could does did do '
             'each every per cost costs costing worth needs need bought buys '
             'buy sold sells sell spent spends spend gets get takes take '
             'paid pays pay earned earns earn made make makes left remaining '
             'only these those his her their its them they it he she '
             'over about into out all total then currently now charging so '
             'wants want wanted go goes went work works working worked gave gives '
             'received receives purchased purchase indicate indicates '
             'watched washed subscribed before after last just more less pre how mowed away full').split())


_TIME = {'hour', 'day', 'week', 'month', 'year'}


_PERIODS = (_TIME - {'hour'}) | {'quarter'}
_CONVERSIONS = {('day', 'week'): 7, ('week', 'year'): 52,
                ('month', 'year'): 12, ('day', 'year'): 365,
                ('quarter', 'year'): 4, ('month', 'quarter'): 3}


def _period_scale(source, target):
    """Conventional calendar conversions, without assuming a work schedule.

    Do not compose paths: 52 seven-day weeks and 365 days are different
    conventions, and a month has no unambiguous length in days or weeks.
    """
    return Fraction(1) if source == target else _CONVERSIONS.get((source, target))


_MEASURE = {'pair', 'dozen', 'gram', 'kilogram', 'pound', 'meter', 'foot', 'gallon'}


def _phrase(tail):
    """A short noun phrase; measures and containers retain their own unit."""
    tail = re.sub(r'^\s*[- ]?(?:of\s+)?(?:(?:the|his|her|their|one)\s+)?', '', tail)
    words = re.findall(r"[a-z]+(?:'[a-z]+)?|[^a-z\s-]", tail)
    result = []
    for i, word in enumerate(words):
        if word in _STOP or not word[0].isalpha():
            break
        word = _singular(word.replace("'s", '').rstrip("'"))
        word = {'ft': 'foot', 'kg': 'kilogram', 'g': 'gram', 'loave': 'loaf',
                'afternoon': 'day', 'morning': 'day', 'evening': 'day',
                'tomatoe': 'tomato', 'potatoe': 'potato'}.get(word, word)
        result.append(word)
        # "X of Y" explicitly names a unit/container and its contents. Keep
        # that structure for arbitrary nouns, rather than enumerating packages.
        if words[i+1:i+2] == ['of']:
            material = _phrase(' '.join(words[i+2:]))
            if material:
                return ' '.join(result) + ' of ' + material
            break
        if word in _TIME | _MEASURE:
            break
        if len(result) == 4:
            break
    return ' '.join(result)


def _head(label):
    if not label:
        return ''
    subject = label.split(' of ', 1)[0]
    return subject.split()[0] if subject.split()[0] in _MEASURE else subject.split()[-1]


def _same(a, b):
    if not a or not b:
        return False
    if a == b:
        return True
    if a.endswith(' ticket'):
        return _same(a[:-7], b)
    if _head(a) == _head(b) and (set(a.split()) <= set(b.split()) or set(b.split()) <= set(a.split())):
        return True
    return _head(a) == _head(b) and (len(a.split()) == 1 or len(b.split()) == 1)


def _price_matches(p, n, label, stock):
    """An explicit category can also qualify a counted noun, e.g. a role."""
    if _same(label, stock):
        return True
    category = label[:-7] if label.endswith(' ticket') else label
    if not category or not stock.startswith(category + ' '):
        return False
    if label.endswith(' ticket'):
        return True
    start, end = _bounds(p.text.lower(), n)
    categories = re.findall(r'\bfor\s+([a-z -]+)', p.text.lower()[start:end])
    return any(_phrase(text) == category for text in categories)


def _numbers(p):
    t = p.text.lower()
    result = []
    for n in p.numbers:
        before, after = t[:n.start], t[n.end:]
        # A count followed by an itemized list is a reference to that list,
        # not an extra purchase. Require all entries and their nouns to agree.
        if not _money(t, n) and re.match(r'\s+[a-z -]+:', after):
            end = _bounds(t, n)[1]
            entries = [re.search(r'\b(?:a|an|one) ([a-z -]+?) (?:for|at|costs?)\s*$', t[n.end:k.start])
                       for k in p.numbers if n.end < k.start < end and _money(t, k)]
            if (len(entries) == n.value and all(entries)
                    and all(_same(_phrase(after), _phrase(m.group(1))) for m in entries)):
                continue
        if (n.start >= len(p.body) and _has(r'\bthese\s*$', before)
                and _has(r'^\s+days?\b', after)
                and n.value == len(set(re.findall(r'\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', p.body)))):
            continue
        if n.value == 1 and _has(r'^\s+day (?:the|he|she|they)\b', after):
            continue
        # A unit definition is not another item to buy.
        if n.value == 1 and not _money(t, n) and (
                _has(r'\bprice of\s*$', before)
                or _has(r'^\s+of them\b', after)
                or n.start >= len(p.body) and _has(r'^\s+of (?:the )?other\b', after)
                or (_has(r'^\s+(?:[a-z]+\s+){1,6}(?:is|was|costs?)\s+[$\d]', after)
                    and not _has(r'\b(?:bought|buys?|purchased)\b[^.;]*$', before))
                or _has(r'\beach\s*$', before) and _has(r'^\s*(?:of|[.,;])', after)):
            continue
        if n.start >= len(p.body) and not _money(t, n) and any(
                k.value == n.value and _same(_phrase(t[k.end:]), _phrase(after))
                for k in result):
            continue
        result.append(_money_number(t, n))
    return result


def _result(value, expression, p):
    if value < 0:
        return None
    label = 'Money total'
    for pattern, name in ((r'profit', 'Profit'), (r'change', 'Change'),
                          (r'left|remaining', 'Money remaining'),
                          (r'earn|salary|make|made', 'Earnings'),
                          (r'cost|price', 'Cost'), (r'pay|paid', 'Payment'),
                          (r'spend|spent', 'Spending')):
        if _has(r'\b(?:'+pattern+r')\b', p.question):
            label = name
            break
    return value, '{}: {} = {} dollars.'.format(label, expression, format_number(value))


def _output(p, result):
    """Convert the final result only; internal ledger terms stay in dollars."""
    if result is None:
        return None
    value, working = result
    if _has(r'\bin cents\b', p.question):
        value *= 100
        working += ' In cents: {}.'.format(format_number(value))
    elif '£' in p.text:
        working = working.replace('dollars', 'pounds')
    elif '€' in p.text:
        working = working.replace('dollars', 'euros')
    return value, working


def _price_label(p, ns, n):
    """Return (unit label, explicit unit-price cue)."""
    t = p.text.lower()
    start, end = _bounds(t, n)
    following = min([k.start for k in ns if k.start > n.start] or [len(t)])
    prefix, suffix = t[start:n.start], t[n.end:min(end, following)]
    suffix = re.sub(r'^\s*(?:[$£€]|dollars?\b|cents?\b|euros?\b)', '', suffix)
    m = re.search(r'\bprice of (?:one|a|an)\s+([a-z -]+?)\s+is\s*$', prefix)
    if m:
        return _phrase(m.group(1)), True
    m = re.match(r'\s*(?:per|for (?:a|an|each|every)|a|an)\s+(.+)', suffix)
    if m:
        return _phrase(m.group(1)), True
    m = re.match(r'\s+for\s+([a-z]+s)\b', suffix)
    if m and _has(r'\b(?:fee|price|rate|tickets?|admission|charges?)\b', prefix):
        return _phrase(m.group(1)), True
    m = re.match(r'\s+to\s+\w+\s+(?:for\s+)?(?:a|an|each)\s+(.+)', suffix)
    if m:
        label = _phrase(m.group(1))
        if label:
            return label, True
    m = re.search(r'\b(?:fee|price|cost) for\s+([a-z]+)\s+costs?\s*$', prefix)
    if m:
        return _phrase(m.group(1)), True
    # The closest determiner identifies the price subject even when a longer
    # sentence introduces it: "a vendor lists a decorated item that costs ...".
    for determiner in reversed(list(re.finditer(r'\b(?:each|every|a|an)\s+', prefix))):
        m = re.fullmatch(r'([a-z -]+?)\s*,?\s+(?:(?:that|which)\s+)?(?:costs?|is|was|are|were|gave|gives|pays?|paid|gets?|earns?|sells? for)\s+(?:(?:him|her|them|\w+)\s+)?', prefix[determiner.end():])
        if m:
            label = _subject_phrase(m.group(1))
            if label:
                return label, True
    m = re.search(r'\b(?:sells?|sold|selling)\s+each\s+([a-z -]+?)\s+(?:at|for)\s*$', prefix)
    if m:
        return _phrase(m.group(1)), True
    m = re.search(r'\b(?:sell|sells|sold)\s+(?:a|an)\s+([a-z -]+?)\s+for\s*$', prefix)
    if m:
        return _phrase(m.group(1)), True
    m = re.search(r'\band\s+(?:a|an)\s+([a-z -]+?)\s+for\s*$', prefix)
    if m:
        return _phrase(m.group(1)), True
    # A quoted title or modified noun is preserved as a category.
    m = re.search(r'([a-z"\' -]+?)\s+(?:(?:that|which)\s+)?(?:costs?|are|were|is|was)(?:\s+at)?\s*$', prefix)
    if m:
        subject = re.split(r'[,;]|\band\b|\bif\b', m.group(1))[-1]
        subject = re.sub(r'^\s*(?:the|a|an)\s+', '', subject)
        subject = re.sub(r'\b(?:least-selling|best-selling)\s+', '', subject)
        label = _subject_phrase(subject)
        if label and _head(label) not in _STOP:
            return label, True
    local_counts = [k for k in ns if k.kind != 'money' and start <= k.start < n.start]
    # "N items which cost PRICE" and "N items at PRICE each".
    if local_counts:
        c = local_counts[-1]
        middle = t[c.end:n.start]
        if (_has(r'\b(?:each|apiece|a piece)\b', suffix)
                or _has(r'\b(?:which|that)\s+costs?\s*$', middle)):
            return _phrase(t[c.end:]), True
    if _has(r'^\s*(?:each|apiece|a piece)\b', suffix):
        # Resolve postposed each to a named price subject or a unique count.
        m = re.search(r'\b([a-z]+(?: [a-z]+)?)\s+(?:at|for)\s*$', prefix)
        if m:
            return _phrase(m.group(1)), True
        return '*', True
    return '', False


def _subject_phrase(text):
    """The priced subject follows the last purchase/sale verb in a clause."""
    return _phrase(re.split(r'\b(?:buys?|bought|sells?|sold|purchases?|purchased)\b', text)[-1])


def _aggregate(p, terms):
    """Terms are classified transaction totals after resolving their units."""
    q = p.question
    groups = {}
    for role, value, expr in terms:
        groups.setdefault(role, []).append((value, expr))
    def total(roles):
        return sum((v for r in roles for v, e in groups.get(r, [])), Fraction(0))
    def expression(roles):
        return ' + '.join(e for r in roles for v, e in groups.get(r, [])) or '0'
    if _has(r'\b(?:difference|more.*than|less.*than)\b', q):
        if len(terms) == 2 and not set(groups) & {'balance', 'remaining', 'tender'}:
            return _result(abs(terms[0][1]-terms[1][1]),
                           '|{} - {}|'.format(terms[0][2], terms[1][2]), p)
        return None
    if 'profit' in q:
        if set(groups) == {'income', 'expense'}:
            return _result(total(['income'])-total(['expense']),
                           '({}) - ({})'.format(expression(['income']), expression(['expense'])), p)
        return None
    if _has(r'\b(?:initially|originally|at first|start|before)\b', q):
        if set(groups) <= {'expense', 'remaining'} and 'remaining' in groups:
            return _result(total(groups), expression(groups), p)
        return None
    if _has(r'\bmore\b.*\b(?:need|earn|save)|\b(?:need|earn|save)\b.*\bmore\b|\b(?:owe|owes)\b', q):
        if set(groups) <= {'expense', 'balance', 'income'} and 'expense' in groups:
            return _result(total(['expense'])-total(['balance', 'income']),
                           '({}) - ({})'.format(expression(['expense']), expression(['balance', 'income'])), p)
        return None
    if _has(r'\b(?:left|remaining|change|back|returns?)\b', q):
        if 'expense' in groups and set(groups) <= {'balance', 'tender', 'income', 'expense'}:
            return _result(total(['balance', 'tender', 'income'])-total(['expense']),
                           '({}) - ({})'.format(expression(['balance', 'tender', 'income']), expression(['expense'])), p)
        return None
    if 'remaining' in groups:
        if set(groups) <= {'balance', 'income', 'remaining', 'expense'}:
            return _result(total(['balance', 'income'])-total(['remaining', 'expense']),
                           '({}) - ({})'.format(expression(['balance', 'income']), expression(['remaining', 'expense'])), p)
        return None
    if set(groups) <= {'income', 'expense'}:
        # A seller's receipts are the buyer's spending; both use the basket sum.
        return _result(total(groups), expression(groups), p)
    if set(groups) == {'tender'} and _has(r'\bbills?\b', q):
        return _result(total(groups), expression(groups), p)
    return None


def _expr(values):
    return ' + '.join(format_number(v) for v in values) or '0'
