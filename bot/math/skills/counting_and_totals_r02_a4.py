"""Counting schemas with explicit stock, partition and group relationships.

All quantities must participate in a relation. Noun heads join rates to their
groups; changes in stock need a recognized action and a remainder question.
"""
import re
from fractions import Fraction

from ..numbers import format_number
from .counting_and_totals_r00_a1 import _different_owner
from .counting_and_totals_r01_a3 import _STOP
from .rates_and_unit_rates_r01_a4 import _singular


def _has(pattern, text):
    return re.search(pattern, text) is not None


def _normal_unit(word):
    word = _singular(word)
    return {'package': 'pack', 'morning': 'day', 'kg': 'kilogram',
            'ml': 'milliliter', 'cm': 'centimeter', 'km': 'kilometer'}.get(word, word)


def _answer(value, expression):
    if value < 0:
        return None
    return value, expression + ' = ' + format_number(value) + '.'


_STOPS = _STOP | set(('quit leave leaves remain remains got get came come into '
                     'over long wide high tall between waiting normally then '
                     'increased decreases decreased raised raises bought sold '
                     'ate eat eats used loses lost drank spent taught teaches '
                     'teach attend attends containing includes include last next').split())
_STOPS.update(('already', 'assigned', 'underwater', 'should', 'must', 'may',
              'might', 'need', 'needs', 'buy', 'sell', 'collect'))
_MEASURES = set(('second minute hour day week month year meter foot inch '
                 'kilometer mile gram kilogram ounce pound liter gallon mb degree '
                 'milliliter centimeter').split())


def _head(tail):
    tail = re.sub(r'^\s*(?:of\s+)?(?:(?:his|her|their|my|the|new|more)\s+)*', '', tail)
    words = re.findall(r'[a-z]+|[^a-z\s-]', tail.lstrip(' -'))
    phrase = []
    for word in words:
        if word in _STOPS or not word.isalpha() or (phrase and word.endswith('ing')):
            break
        word = _normal_unit(word)
        phrase.append(word)
        # An ordinal immediately before a noun labels a category (second
        # graders), rather than a time measurement.
        if (word in _MEASURES and not (word == 'second' and tail.lstrip().startswith('second '))) or len(phrase) == 4:
            break
    return phrase[-1] if phrase else ''


def _unit(p, n):
    return 'money' if n.kind == 'money' else _head(p.text.lower()[n.end:])


def _asked(p):
    if p.question.startswith('how long') or _has(r'^how much time\b', p.question):
        return 'time'
    m = re.match(r'how (?:many|much)\s+(?:(?:more|additional|extra)\s+)?(.*)', p.question)
    if not m:
        m = re.match(r'(?:calculate|find) (?:the )?(?:total |combined )?(?:number|amount) of\s+(.*)', p.question)
    return _head(m.group(1)) if m else ''


def _suffix(p, ns, i):
    end = ns[i+1].start if i+1 < len(ns) else len(p.body)
    return p.text.lower()[ns[i].end:end]


def _partition(p):
    """Disjoint named categories and their stated whole, in either order."""
    ns = p.numbers
    if not 3 <= len(ns) <= 6 or any(n.start >= len(p.body) for n in ns):
        return None
    text = p.text.lower()
    if _has(r'\b(?:each|every|per|times|twice|half|more|less|fewer|than|'
            r'gave|lost|ate|sold|bought|quit|new|percent|including)\b|\bof which\b', text):
        return None
    totals = []
    for i, n in enumerate(ns):
        prefix = re.sub(r'\b(?:mr|mrs|ms|dr|prof)\.', '', text[:n.start])
        left = re.split(r'[.;!?]', prefix)[-1]
        # A bare count is a whole only after a list in an explicit if-clause.
        right = re.split(r'[.;!?]', _suffix(p, ns, i))[0]
        total_cue = _has(r'\b(?:total|overall|altogether|all together)\b', left+right)
        total_cue = total_cue or (i == len(ns)-1 and _has(r'\bif there (?:are|were)\s*$', left))
        if total_cue:
            totals.append(i)
    if len(totals) != 1:
        return None
    ti = totals[0]
    total_unit = _unit(p, ns[ti])
    if not total_unit:
        return None
    # The query must identify an unknown category, rather than ask for the
    # whole already stated. A "some ..." clause also explicitly labels it.
    unknown = _has(r'\b(?:some|rest|remaining|remainder)\b', p.body)
    unknown = unknown or _has(r'\b(?:color|colour|type|kind)\b', p.question)
    asked_phrase = re.match(r'how many\s+([a-z ]+?)\s+(?:are|were|is|does|do|did)\b', p.question)
    if asked_phrase:
        phrase = asked_phrase.group(1)
        unknown = unknown or (len(phrase.split()) > 1 and phrase not in p.body)
    if not unknown:
        return None
    others = [n for i, n in enumerate(ns) if i != ti]
    if any(_unit(p, n) != total_unit for n in others):
        # Distinct school grades, for example, require an explicit unknown
        # group and a list introduced by "there are".
        if not (_has(r'\bsome\b', p.body) and _has(r'^\s*there (?:are|were)\b', p.body)
                and _has(r'\band\b', p.body)
                and any(_head(m.group(1)) == _asked(p) for m in re.finditer(r'\bsome\s+([^.;]+)', p.body))):
            return None
    value = ns[ti].value - sum((n.value for n in others), Fraction(0))
    return _answer(value, '{} - ({})'.format(format_number(ns[ti].value),
                   ' + '.join(format_number(n.value) for n in others)))


_EVENT = re.compile(r'\b(has|have|had|makes?|made|baked|prepared|bought|buys?|'
                    r'ordered|received|provided|gets?|got|collected|lost|loses|ate|eats?|eat|'
                    r'used|uses|gave|given|gives?|stole|steals?|sold|sells?|quit|leave|'
                    r'leaves|left|joined|join|arrived|added|removed|drank)\b')
_REMOVE = set(('lost loses ate eats eat used uses gave given gives stole steal steals '
               'sold sells quit leave leaves left removed drank').split())


def _stock(p):
    ns = p.numbers
    text = p.text.lower()
    if (not 2 <= len(ns) <= 5 or any(n.start >= len(p.body) for n in ns)
            or not _has(r'\b(?:left|remain|remaining|now|keep|kept)\b', p.question)
            or _different_owner(p)):
        return None
    if _has(r'\b(?:each|every|per|times|than|twice|half|double|percent|'
            r'equal|remainder|cost|price|a day|a week)\b', text):
        return None
    if any(n.value.denominator != 1 and _has(r'^\s+of\b', text[n.end:]) for n in ns):
        return None
    unit = _unit(p, ns[0])
    if not unit or _asked(p) != unit:
        return None
    values, signs, expressions = [], [], []
    previous_event = None
    for i, n in enumerate(ns):
        if _unit(p, n) not in ('', unit):
            return None
        prefix = text[ns[i-1].end if i else 0:n.start]
        # Do not inherit an action across sentences. "N people quit" is a
        # postposed event, and "M new people got in" is an explicit arrival.
        clause = re.split(r'[.;!?]|\b(?:but|while|then)\b', prefix)[-1]
        events = list(_EVENT.finditer(clause))
        suffix = _suffix(p, ns, i)
        post = re.match(r'\s+(?:new\s+)?(?:[a-z]+\s+){1,3}?(quit|leave|leaves|left|joined|join|arrived|got in)\b', suffix)
        if post:
            event = post.group(1)
        elif events:
            event = events[-1].group()
        elif i and not _has(r'[.;!?]', prefix) and _has(r'\band\b', prefix):
            event = previous_event
        else:
            return None
        if not i and event not in ('has', 'have', 'had', 'makes', 'make', 'made', 'baked', 'prepared', 'bought'):
            return None
        sign = -1 if event in _REMOVE else 1
        previous_event = event
        signs.append(sign)
        values.append(sign*n.value)
        expressions.append((' - ' if sign < 0 else ' + ') + format_number(n.value))
    if -1 not in signs:
        return None
    return _answer(sum(values, Fraction(0)), ''.join(expressions).lstrip(' +'))


def _groups(p):
    """Sum counts sharing a rate, or combine a product with a stock change."""
    ns = p.numbers
    text = p.text.lower()
    if not 2 <= len(ns) <= 6 or any(n.kind != 'number' for n in ns):
        return None
    if _has(r'\b(?:than|twice|half|double|percent|average|ratio|except|not|'
            r'fewer|less|cost|price)\b', text):
        return None
    units = [_unit(p, n) for n in ns]
    asked = _asked(p)
    if not asked or not all(units):
        return None
    relations = set()
    for i, n in enumerate(ns):
        before = text[max(0, n.start-65):n.start]
        after = re.split(r'[.;!?](?:\s|$)', _suffix(p, ns, i))[0]
        group = None
        m = re.search(r'\b(?:a|an|per|each|every)\s+([a-z]+)\b', after)
        if m and not any(w in _STOPS - {'in', 'of', 'to', 'on', 'more', 'extra', 'additional'} for w in re.findall(r'[a-z]+', after[:m.start()])):
            group = _normal_unit(m.group(1))
        m = re.search(r'\b(?:each|every)\s+([a-z]+(?:\s+[a-z]+){0,2}?)\s+(?:has|have|holds?|contains?|needs?|requires?|produces?|makes?|uses?)\s*$', before)
        if m:
            matching = set(_normal_unit(w) for w in m.group(1).split()) & set(units)
            group = next(iter(matching)) if len(matching) == 1 else _normal_unit(m.group(1).split()[-1])
        # A postposed each inherits the immediately preceding count's noun.
        if not group and i and (_has(r'^\s+[a-z]+\s+each\b', after)
                                or _has(r'\beach\s+(?:bought|buys?|ate|eats?|gets?|received)\s*$', before)):
            group = units[i-1]
        if group:
            candidates = tuple(j for j, u in enumerate(units) if j != i and u == group)
            if candidates:
                relations.add((i, candidates))
    for m in re.finditer(r'\beach of\b', p.body):
        earlier = [i for i, n in enumerate(ns) if n.end < m.start()]
        later = [i for i, n in enumerate(ns) if n.start > m.end()]
        if not later:
            return None
        if _has(r'\b(?:in|on)\s*$', text[:m.start()]):
            if not earlier:
                return None
            relations.add((earlier[-1], (later[0],)))
        elif len(later) >= 2 and _has(r'\b(?:has|have|ate|eats?|bought|used|uses)\s*$', text[ns[later[0]].end:ns[later[1]].start]):
            relations.add((later[1], (later[0],)))
        else:
            return None
    if len(relations) > 1:
        count_sets = {cs for _, cs in relations}
        rate_ids = {ri for ri, _ in relations}
        if len(count_sets) != 1 or _has(r'\b(?:left|remaining|remain|more)\b', p.question):
            return None
        counts = next(iter(count_sets))
        if rate_ids & set(counts) or rate_ids | set(counts) != set(range(len(ns))):
            return None
        if any(units[i] != asked for i in rate_ids):
            return None
        c = sum((ns[i].value for i in counts), Fraction(0))
        rates = sum((ns[i].value for i in rate_ids), Fraction(0))
        return _answer(c*rates, '({}) x ({})'.format(' + '.join(format_number(ns[i].value) for i in counts), ' + '.join(format_number(ns[i].value) for i in sorted(rate_ids))))
    if len(relations) != 1:
        return None
    ri, counts = next(iter(relations))
    if (units[ri] != asked and not (asked == 'time' and units[ri] in ('minute', 'hour', 'second'))) or ri in counts:
        return None
    other = [i for i in range(len(ns)) if i != ri and i not in counts]
    # Group counts must be a simple disjoint list; changing the number of
    # groups first is a different schema.
    if len(counts) > 1 and _has(r'\b(?:lost|sold|gave|ate|remaining|left|more)\b', text):
        return None
    count = sum((ns[i].value for i in counts), Fraction(0))
    value = count*ns[ri].value
    expression = '({}) x {}'.format(' + '.join(format_number(ns[i].value) for i in counts), format_number(ns[ri].value))
    if not other:
        if _has(r'\b(?:left|remaining|remain|more)\b', p.question):
            return None
        return _answer(value, expression)
    if any(units[i] != units[ri] for i in other):
        return None
    if len(other) > 1:
        if _has(r'\b(?:left|remaining|remain|more|lost|sold|gave|ate|used)\b', text):
            return None
        # Each extra quantity must have its own explicit content statement.
        if not all(_has(r'\b(?:has|have|holds?|contains?|includes?)\s*$',
                        text[ns[i-1].end if i else 0:ns[i].start]) for i in other):
            return None
        return _answer(value + sum((ns[i].value for i in other), Fraction(0)),
                       expression + ' + ' + ' + '.join(format_number(ns[i].value) for i in other))
    oi = other[0]
    other_n = ns[oi]
    prefix = text[max(0, other_n.start-65):other_n.start]
    if _has(r'\bmore\b', p.question) and _has(r'\b(?:need|needs|required|require)\b', text):
        if oi < min(ri, min(counts)) and _has(r'\b(?:has|have|had)\s*$', prefix):
            return _answer(value-other_n.value, expression + ' - ' + format_number(other_n.value))
    if _has(r'\b(?:left|remaining|remain)\b', p.question):
        stock_cue = _has(r'\b(?:has|have|had|hold|holds)\s*$', prefix)
        stock_cue = stock_cue or _has(r'^\s+[a-z]+\s+(?:were|are|was|is)\s+(?:served|prepared|available)\b', text[other_n.end:])
        if oi < min(ri, min(counts)) and stock_cue:
            # Per-group action must remove items from the stated stock.
            rate_prefix = text[max(0, ns[ri].start-60):ns[ri].start]
            if not _has(r'\b(?:bought|buys?|ate|eats?|sold|sells?|gave|gives?|used|uses)\s*$', rate_prefix):
                return None
            return _answer(other_n.value-value, '{} - {}'.format(format_number(other_n.value), expression))
        if oi > max(ri, max(counts)) and _has(r'\b(?:ate|eats?|sold|sells?|gave|gives?|used|uses|lost|loses)\s*$', prefix):
            return _answer(value-other_n.value, expression + ' - ' + format_number(other_n.value))
        return None
    if _has(r'\b(?:extra|additional|also|plus|then)\b', prefix):
        return _answer(value+other_n.value, expression + ' + ' + format_number(other_n.value))
    return None


def _equal_shares_with_owner(p):
    """Divide equally with N companions: the original owner also gets a share."""
    ns = p.numbers
    if len(ns) != 2 or _has(r'\b(?:each|per|times|half|more|less|than)\b', p.body):
        return None
    text = p.text.lower()
    total, companions = ns
    if not _has(r'\b(?:divide|split|share)\s+(?:it\s+)?equally with (?:his|her|their|my)\s*$', text[:companions.start]):
        return None
    if not _has(r'^\s+(?:siblings|friends|brothers|sisters|classmates|colleagues)\b', text[companions.end:]):
        return None
    query_unit = _asked(p)
    explicit_unit = re.search(r'\bin (?:the )?(?:square )?([a-z]+)', p.question)
    if explicit_unit:
        query_unit = _singular(explicit_unit.group(1))
    if not _has(r'\b(?:have|get|receive)\b', p.question) or query_unit != _unit(p, total):
        return None
    return _answer(total.value/(companions.value+1), '{} / ({} + 1)'.format(format_number(total.value), format_number(companions.value)))


def _rate_chain(p):
    """Multiply a chain of explicit rates ending at the requested unit."""
    ns = p.numbers
    text = p.text.lower()
    if not 3 <= len(ns) <= 5 or any(n.kind != 'number' for n in ns):
        return None
    if _has(r'\b(?:left|remaining|more|less|than|lost|sold|ate|half|twice|'
            r'except|not|average|percent)\b', text):
        return None
    units = [_unit(p, n) for n in ns]
    asked = _asked(p)
    if not all(units) or not asked:
        return None
    denominators = {}
    references = set()
    for i, n in enumerate(ns):
        after = re.split(r'[.;!?](?:\s|$)', _suffix(p, ns, i))[0]
        before = text[max(0, n.start-80):n.start]
        m = re.search(r'\b(?:a|an|per|each|every)\s+([a-z]+)\b', after)
        if m and not any(w in _STOPS - {'in', 'of'} for w in re.findall(r'[a-z]+', after[:m.start()])):
            denominators[i] = _normal_unit(m.group(1))
        m = re.search(r'\b(?:each|every)\s+([a-z]+)\s+(?:(?:can|will)\s+)?(?:has|have|holds?|contains?|needs?|produces?|makes?|uses?)\s*$', before)
        if m:
            denominators[i] = _normal_unit(m.group(1))
        m = re.search(r'\b(?:each|every)\s+(second|minute|hour|day|week)\b[^.;!?]*$', before)
        if m and not any(k.start > m.start()+max(0, n.start-80) and k.end <= n.start for k in ns):
            denominators[i] = m.group(1)
        if i and _has(r'^\s+[a-z]+\s+each\b', after):
            denominators[i] = units[i-1]
        # A stated recipe for one unit is a rate, rather than another group.
        if i and ns[i-1].value == 1 and _has(r'\b(?:to (?:produce|make)|for)\s*$', text[:ns[i-1].start]) and _has(
                r'\b(?:needs?|requires?)\s*$', before):
            denominators[i] = units[i-1]
            references.add(i-1)
    if not denominators:
        return None
    remaining = set(range(len(ns))) - references
    current = asked
    order = []
    while remaining:
        candidates = [i for i in remaining if units[i] == current]
        if len(candidates) != 1:
            return None
        i = candidates[0]
        remaining.remove(i)
        order.append(i)
        if i not in denominators:
            if remaining:
                return None
            break
        current = denominators[i]
    implicit_period = (order and order[-1] in denominators and not remaining
                       and _has(r'\b(?:a|an|per|each|every)\s+' + re.escape(current) + r'\b', p.question))
    if not order or (order[-1] in denominators and not implicit_period) or len(order) < 3:
        return None
    result = Fraction(1)
    for i in order:
        result *= ns[i].value
    return _answer(result, ' x '.join(format_number(ns[i].value) for i in reversed(order)))


def _budget(p):
    """An initial budget less purchases, optionally a quantity at a unit price."""
    ns = p.numbers
    text = p.text.lower()
    if not 3 <= len(ns) <= 8 or not _has(r'how much (?:money )?.*\bleft\b', p.question):
        return None
    if any(n.start >= len(p.body) for n in ns) or ns[0].kind != 'money':
        return None
    if _has(r'\b(?:earned|received|gave|sold|discount|percent|change|refund)\b', p.body):
        return None
    if not _has(r'\b(?:has|had|have|with)\s*$', text[:ns[0].start]) or not _has(r'\b(?:bought|buys?|purchased)\b', p.body):
        return None
    if len({n.raw[0] for n in ns if n.kind == 'money'}) != 1:
        return None
    costs, expressions = [], []
    i = 1
    while i < len(ns):
        n = ns[i]
        if n.kind == 'money':
            if _has(r'^\s+each\b', text[n.end:]):
                return None
            costs.append(n.value)
            expressions.append(format_number(n.value))
            i += 1
        elif (i+1 < len(ns) and ns[i+1].kind == 'money'
              and _has(r'^\s+each\b', text[ns[i+1].end:])
              and _has(r'\bfor\s*$', text[n.end:ns[i+1].start])):
            costs.append(n.value*ns[i+1].value)
            expressions.append('{} x {}'.format(format_number(n.value), format_number(ns[i+1].value)))
            i += 2
        else:
            return None
    return _answer(ns[0].value-sum(costs, Fraction(0)), '{} - ({})'.format(format_number(ns[0].value), ' + '.join(expressions)))


def _converted_stock(p):
    """A stock in larger units, a removal, and an explicit conversion factor."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or not _has(r'\b(?:left|remaining|remain)\b', p.question):
        return None
    stock, removed, factor = ns
    source, dest = _unit(p, stock), _unit(p, removed)
    if source == dest or _unit(p, factor) != dest or _asked(p) != dest:
        return None
    if not _has(r'\b(?:ate|drank|used|lost|sold|gave)\s*$', text[max(stock.end, removed.start-40):removed.start]):
        return None
    relation = re.match(r'\s+[a-z]+\s+in (?:a|an)\s+([a-z]+)', text[factor.end:])
    if not relation or _singular(relation.group(1)) != source:
        return None
    return _answer(stock.value*factor.value-removed.value, '{} x {} - {}'.format(*(format_number(n.value) for n in (stock, factor, removed))))


def _remaining_work(p):
    """A stated task size minus progress, divided by its current rate."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or not _has(r'^how many more\s+', p.question):
        return None
    goal, done, rate = ns
    unit = _unit(p, goal)
    if not unit or any(_unit(p, n) != unit for n in ns):
        return None
    denom = re.match(r'\s*[a-z]+\s*(?:/|per\s+)([a-z]+)', text[rate.end:])
    if not denom or _singular(denom.group(1)) != _asked(p) or rate.value <= 0:
        return None
    if not _has(r'\bafter\b', text[goal.end:done.start]):
        return None
    return _answer((goal.value-done.value)/rate.value, '({} - {}) / {}'.format(*(format_number(n.value) for n in ns)))


def _factor_total(p):
    """A base and a second amount explicitly scaled from it, summed together."""
    text = p.text.lower()
    ns = p.numbers
    if not _has(r'\b(?:total|together|combined|altogether)\b', p.question):
        return None
    if _has(r'\b(?:less|fewer|half|each|every|per|left|remaining|percent)\b', text):
        return None
    factors = list(re.finditer(r'\b(?:twice|double|triple|thrice|quadruple)\b', p.body))
    factor = None
    used = set()
    if len(factors) == 1:
        m = factors[0]
        factor = {'twice': 2, 'double': 2, 'triple': 3, 'thrice': 3, 'quadruple': 4}[m.group()]
        if not _has(r'^\s+(?:what|that amount|the (?:number|amount)|as (?:many|much)|more)', text[m.end():]):
            return None
    elif not factors:
        for i, n in enumerate(ns):
            if _has(r'^\s+times (?:more|as (?:many|much))\b', text[n.end:]):
                # A fractional increase adds a share of the base; it is not
                # itself the entire second group's multiplier.
                if n.value < 1 and _has(r'^\s+times more\b', text[n.end:]):
                    return None
                if factor is not None:
                    return None
                factor = n.value
                used.add(i)
    if factor is None or factor <= 0:
        return None
    # A query mentioning two successive periods describes both contributions.
    for i, n in enumerate(ns):
        if n.start >= len(p.body):
            if n.value == 2 and _unit(p, n) in ('week', 'day', 'month', 'year') and _has(
                    r'\b(?:following|next)\b', p.body):
                used.add(i)
            else:
                return None
    remaining = [n for i, n in enumerate(ns) if i not in used]
    if len(remaining) == 1:
        base = remaining[0]
        requested = _asked(p)
        if requested and requested not in (_unit(p, base), 'time'):
            return None
        return _answer(base.value*(1+factor), '{} x (1 + {})'.format(format_number(base.value), format_number(factor)))
    if len(remaining) == 2 and _has(r'\bplus\s*$', text[:remaining[1].start]):
        a, b = remaining
        if _unit(p, a) != _unit(p, b):
            return None
        return _answer(a.value*(1+factor)+b.value, '{} x (1 + {}) + {}'.format(format_number(a.value), format_number(factor), format_number(b.value)))
    return None


def _reverse_additions(p):
    """A final stock after purchases, asking how much was present before."""
    ns = p.numbers
    text = p.text.lower()
    if not 3 <= len(ns) <= 5 or any(n.start >= len(p.body) for n in ns):
        return None
    if not _has(r'\b(?:already|originally|initially|start|before)\b', p.question):
        return None
    if _has(r'\b(?:each|every|per|than|half|twice|sold|gave|ate|lost|percent)\b', text):
        return None
    units = [_unit(p, n) for n in ns]
    if not units[0] or len(set(units)) != 1 or _asked(p) != units[0]:
        return None
    final_prefix = text[ns[-2].end:ns[-1].start]
    if not _has(r'\bnow has\s*$', final_prefix):
        return None
    for i, n in enumerate(ns[:-1]):
        prefix = text[ns[i-1].end if i else 0:n.start]
        if not _has(r'\b(?:buys?|bought|purchased|received|another)\s+(?:an?\s+)?$', prefix):
            return None
    return _answer(ns[-1].value-sum((n.value for n in ns[:-1]), Fraction(0)),
                   '{} - ({})'.format(format_number(ns[-1].value), ' + '.join(format_number(n.value) for n in ns[:-1])))


def _equal_parts(p):
    """Use some of a whole divided into equal parts."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or any(n.kind != 'number' for n in ns):
        return None
    whole, parts, used = ns
    if not _has(r'\b(?:cut|divided|split) into\s*$', text[whole.end:parts.start]):
        return None
    if not _has(r'^\s+equal\s+parts?\b', text[parts.end:]):
        return None
    if not _has(r'^\s+parts?\s+(?:were|are) used\b', text[used.end:]):
        return None
    if not _has(r'\bused\b', p.question) or parts.value <= 0 or used.value > parts.value:
        return None
    if _asked(p) not in ('time', _unit(p, whole)):
        return None
    return _answer(whole.value*used.value/parts.value, '{} / {} x {}'.format(*(format_number(n.value) for n in (whole, parts, used))))


def _fraction_removed(p):
    """A stated fraction of a count is removed from the entire stock."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) not in (2, 3) or not _has(r'\b(?:left|remain|remaining)\b', p.question):
        return None
    if _has(r'\b(?:each|every|per|more|less|than)\b', text):
        return None
    if len(ns) == 3:
        container, whole, fraction = ns
        if container.value != 1 or not _has(r'\b(?:cut|divided|split) into\s*$', text[container.end:whole.start]):
            return None
    else:
        whole, fraction = ns
    if not 0 < fraction.value < 1 or _unit(p, whole) != _asked(p):
        return None
    tail = text[fraction.end:len(p.body)]
    if not re.match(r'\s+of (?:the|his|her|their) [a-z]+\s+(?:was|were|is|are)\s+(?:eaten|used|sold|removed|given away)\b', tail):
        return None
    return _answer(whole.value*(1-fraction.value), '{} x (1 - {})'.format(format_number(whole.value), format_number(fraction.value)))


def _same_period(p):
    """An initial task plus N more taking the same time, and an extra task."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or not _has(r'\bsame (?:period of )?time\b', p.body):
        return None
    first, additional, last = ns
    unit = _unit(p, first)
    if unit not in _MEASURES or unit != _unit(p, last) or _asked(p) != unit:
        return None
    if not _has(r'^\s+more\b', text[additional.end:]) or not _has(r'\banother\s*$', text[additional.end:last.start]):
        return None
    if not _has(r'\btotal\b', p.question):
        return None
    return _answer(first.value*(additional.value+1)+last.value, '{} x (1 + {}) + {}'.format(*(format_number(n.value) for n in ns)))


def _daily_meals(p):
    """Daily morning and evening consumption, and the number of days a stock lasts."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or _asked(p) != 'day' or not _has(r'\b(?:feed|last)\b', p.question):
        return None
    a, b, stock = ns
    if not _has(r'\bin the morning\b', text[a.end:b.start]) or not _has(r'\bin the evening\b', text[b.end:stock.start]):
        return None
    if len({_unit(p, n) for n in ns}) != 1 or not _unit(p, a):
        return None
    if not _has(r'\b(?:has|holds|contains)\s*$', text[b.end:stock.start]):
        return None
    if a.value+b.value <= 0:
        return None
    return _answer(stock.value/(a.value+b.value), '{} / ({} + {})'.format(*(format_number(n.value) for n in (stock, a, b))))


def _equal_categories(p):
    """A whole less two equally sized categories, one of which is known."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 2 or ns[0].start >= len(p.body):
        return None
    relation = re.search(r'\bnumber of (?:the )?([a-z]+) and (?:the )?([a-z]+)\s+(?:is|was|are|were)\s+(?:the same|equal)\b', p.body)
    if not relation:
        return None
    first, second = (_normal_unit(w) for w in relation.groups())
    total, known = ns
    known_unit = _unit(p, known)
    identity = re.match(r'\s+of these [a-z]+ were ([a-z]+)\b', text[known.end:])
    if identity:
        known_unit = _normal_unit(identity.group(1))
    if known_unit not in (first, second) or _unit(p, total) in (first, second):
        return None
    # Ask for the third category, or for those removed to equalize the two.
    if not _has(r'\b(?:rest|remaining|not able|unable)\b', text):
        return None
    if _asked(p) in (first, second) and not _has(r'\b(?:not able|unable)\b', p.question):
        return None
    return _answer(total.value-2*known.value, '{} - 2 x {}'.format(format_number(total.value), format_number(known.value)))


def _category_ratio_total(p):
    """Two disjoint categories with a multiplicative ratio and their total."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 2 or _has(r'\b(?:each|per|half|more than|fewer|less|percent)\b', text):
        return None
    relation = None
    for i, n in enumerate(ns):
        m = re.match(r'\s+times\s+(?:more\s+)?([a-z]+(?:\s+[a-z]+){0,2}?)\s+than\s+([a-z]+(?:\s+[a-z]+){0,2}?)(?=[.,;])', text[n.end:])
        if m:
            relation = (i, m.group(1), m.group(2))
            break
        m = re.search(r'\b(?:the )?number of ([a-z]+)\s+(?:is|was)\s*$', text[:n.start])
        other = re.match(r'\s+times (?:the )?number of ([a-z]+)\b', text[n.end:])
        if m and other:
            relation = (i, m.group(1), other.group(1))
            break
    if relation is None:
        return None
    ri, first, second = relation
    total = ns[1-ri]
    total_clause = re.split(r'[.;!?]', text[:total.start])[-1]
    total_suffix = re.split(r'[.;!?]', text[total.end:])[0]
    if not (_has(r'\btotal\b', total_clause+total_suffix) or _has(r'\bsome of them turned out to be\b', text)):
        return None
    asked = _asked(p)
    if asked == _head(first):
        factor = ns[ri].value
    elif asked == _head(second):
        factor = Fraction(1)
    else:
        return None
    if ns[ri].value <= 0:
        return None
    return _answer(total.value*factor/(ns[ri].value+1), '{} x {} / ({} + 1)'.format(format_number(total.value), format_number(factor), format_number(ns[ri].value)))


# Conversion factors are physical definitions, independent of story nouns.
_STANDARD_UNITS = {
    'second': ('time', Fraction(1)), 'minute': ('time', Fraction(60)),
    'hour': ('time', Fraction(3600)), 'day': ('time', Fraction(86400)),
    'week': ('time', Fraction(604800)),
    'inch': ('length', Fraction(1)), 'foot': ('length', Fraction(12)),
    'centimeter': ('metric_length', Fraction(1)), 'meter': ('metric_length', Fraction(100)),
    'kilometer': ('metric_length', Fraction(100000)),
    'milliliter': ('volume', Fraction(1)), 'liter': ('volume', Fraction(1000)),
    'gram': ('mass', Fraction(1)), 'kilogram': ('mass', Fraction(1000)),
}


def _convert(value, source, target):
    if source == target:
        return value
    a, b = _STANDARD_UNITS.get(source), _STANDARD_UNITS.get(target)
    if a and b and a[0] == b[0]:
        return value*a[1]/b[1]
    return None


def _measurement_sum(p):
    """Total or arithmetic mean of explicitly stated measurements."""
    ns = p.numbers
    if not 2 <= len(ns) <= 8 or any(n.start >= len(p.body) for n in ns):
        return None
    if not _has(r'\b(?:total|combined|together|altogether|average)\b', p.question):
        return None
    if _has(r'\b(?:each|per|every|more|less|than|half|twice|lost|sold|gave|'
            r'left|remaining|increase|decrease|percent)\b', p.text.lower()):
        return None
    units = [_unit(p, n) for n in ns]
    target = _asked(p)
    if target not in _STANDARD_UNITS:
        # "average ... in inches" and similar explicit output units.
        m = re.search(r'\bin (?:the )?([a-z]+)\b', p.question)
        target = _normal_unit(m.group(1)) if m else ''
    if target not in _STANDARD_UNITS:
        return None
    terms = [_convert(n.value, u, target) for n, u in zip(ns, units)]
    if any(v is None for v in terms):
        return None
    expression = ' + '.join(format_number(v) for v in terms)
    value = sum(terms, Fraction(0))
    if _has(r'\baverage\b', p.question):
        value /= len(terms)
        expression = '(' + expression + ') / ' + str(len(terms))
    return _answer(value, expression)


def _task_duration(p):
    """A duration to do a single task, then a time budget for repeated tasks."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 2 or not _has(r'\b(?:takes?|takes? him|takes? her)\b', p.body):
        return None
    duration, budget = ns
    if duration.value <= 0 or duration.start >= len(p.body) or budget.start < len(p.body):
        return None
    relation = re.match(r'\s+[a-z]+\s+to\s+[a-z]+\s+(?:a|an)\s+([a-z]+)\b', text[duration.end:])
    if not relation or _normal_unit(relation.group(1)) != _asked(p):
        return None
    if _has(r'\b(?:each|per|more|less|than|half|twice|lost|remaining)\b', text):
        return None
    available = _convert(budget.value, _unit(p, budget), _unit(p, duration))
    if available is None:
        return None
    return _answer(available/duration.value, '{} / {}'.format(format_number(available), format_number(duration.value)))


def _capacity_trips(p):
    """A carrying capacity and total stock, rounding up for the last trip."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) not in (2, 3) or not _has(r'\b(?:number of )?trips\b', p.question):
        return None
    capacity, total = ns[:2]
    def noun(n):
        m = re.match(r'\s+([a-z]+)\b', text[n.end:])
        return _normal_unit(m.group(1)) if m else ''
    if len(ns) == 3 and (ns[2].start < len(p.body) or ns[2].value != total.value
                        or noun(ns[2]) != noun(total)):
        return None
    if capacity.value <= 0 or not noun(total) or noun(capacity) != noun(total):
        return None
    if not _has(r'^\s+[a-z]+\s+at a time\b', text[capacity.end:]):
        return None
    if not _has(r'\bcarry\s*$', text[:capacity.start]):
        return None
    if _has(r'\b(?:each|per|more|less|than|half|twice|lost|sold|gave)\b', text):
        return None
    value = total.value/capacity.value
    return _answer(Fraction(-(-value.numerator//value.denominator)),
                   'Round up {} / {}'.format(format_number(total.value), format_number(capacity.value)))


def _goal_gap(p):
    """A target count less known contributions or existing inventory."""
    ns = p.numbers
    text = p.text.lower()
    if not 3 <= len(ns) <= 6 or any(n.start >= len(p.body) for n in ns):
        return None
    if not _has(r'\bmore\b.*\b(?:need|collect|buy|sell)\b', p.question):
        return None
    if _has(r'\b(?:each|every|per|times|than|half|twice|percent|lost|gave|ate|including)\b|\bof which\b', text):
        return None
    goals = []
    for i, n in enumerate(ns):
        prefix = text[ns[i-1].end if i else 0:n.start]
        if _has(r'\b(?:needs?|wants?|goal|target)\b', prefix):
            goals.append(i)
    if len(goals) != 1:
        return None
    gi = goals[0]
    unit = _unit(p, ns[gi])
    if not unit or unit != _asked(p):
        return None
    for i, n in enumerate(ns):
        if i == gi:
            continue
        if _unit(p, n) not in (unit, ''):
            return None
        prefix = text[ns[i-1].end if i else 0:n.start]
        if not _has(r'\b(?:has|have|had|collected|sold|bought|already|and)\b', prefix):
            return None
    others = [n for i, n in enumerate(ns) if i != gi]
    return _answer(ns[gi].value-sum((n.value for n in others), Fraction(0)), '{} - ({})'.format(format_number(ns[gi].value), ' + '.join(format_number(n.value) for n in others)))


def _production_batches(p):
    """One output requires a stated input count, with disjoint input stocks."""
    ns = p.numbers
    text = p.text.lower()
    if not 3 <= len(ns) <= 6 or any(n.start >= len(p.body) for n in ns):
        return None
    rate = ns[0]
    relation = re.search(r'\b(?:make|produce) (?:a|an) ([a-z]+) from\s*$', text[:rate.start])
    if not relation or _normal_unit(relation.group(1)) != _asked(p) or rate.value <= 0:
        return None
    unit = _unit(p, rate)
    if not unit or any(_unit(p, n) != unit for n in ns[1:]):
        return None
    if not _has(r'\b(?:has|have|had)\s*$', text[rate.end:ns[1].start]):
        return None
    if _has(r'\b(?:each|every|per|times|than|half|twice|percent|lost|gave|sold|ate)\b', text):
        return None
    amount = sum((n.value for n in ns[1:]), Fraction(0))/rate.value
    # Output objects must be complete; unusable material may remain.
    return _answer(Fraction(amount.numerator//amount.denominator), 'Whole items from ({}) / {}'.format(' + '.join(format_number(n.value) for n in ns[1:]), format_number(rate.value)))


def solve(problem):
    if any(n.kind == 'percent' or n.value < 0 for n in problem.numbers):
        return None
    for rule in (_partition, _stock, _groups, _rate_chain, _budget,
                 _equal_shares_with_owner, _converted_stock, _remaining_work,
                 _factor_total, _reverse_additions, _equal_parts, _fraction_removed,
                 _same_period, _daily_meals, _equal_categories, _category_ratio_total,
                 _measurement_sum, _task_duration, _capacity_trips,
                 _goal_gap, _production_batches):
        result = rule(problem)
        if result is not None:
            return result
    return None
