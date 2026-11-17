"""Conservative readers for percentages, price changes and nested subsets.

Rates are exact ratios. A reader must identify the known base (or known part),
the direction of the relation, and the requested part before doing arithmetic.
"""
import re
from fractions import Fraction

from ..numbers import format_number
from .counting_and_totals_r00_a1 import _singular, _sentence


def _has(pattern, text):
    return re.search(pattern, text) is not None


def _answer(value, expression):
    if value < 0:
        return None
    return value, expression + ' = ' + format_number(value) + '.'


def _calc(a, op, b):
    if op == '/' and not b:
        return None
    value = a*b if op == '*' else a/b if op == '/' else a+b if op == '+' else a-b
    return _answer(value, '{} {} {}'.format(format_number(a), op, format_number(b)))


_STOP = set(('a an the of in at to for on with from as by and or but if that those '
             'these them their his her its is are was were be been has have had '
             'do does did will would can could it he she they there each every '
             'total number amount how many much percent percentage which '
             'all only then than now also').split())


def _words(text):
    return set(_singular(w) for w in re.findall(r'[a-z]+', text) if w not in _STOP)


def _labels(text, n):
    """Read the predicate of a proportional statement, excluding its base."""
    tail = text[n.end:]
    tail = re.split(r'[.;!?]|,(?!\d)|\s+(?:and|while|but)\b', tail)[0]
    predicate = re.search(r'\b(?:are|is|were|was|have|has)\s+(.+)', tail)
    if predicate:
        return predicate.group(1)
    # Postposed percentage: "the red ones account for 30%".
    before = re.split(r'[.;!?]', text[:n.start])[-1]
    if _has(r'\b(?:are|is|account for|make up|represent|spent|spends|saves?|lost|loses|sold)\s*$', before):
        return before
    return tail


def _opposite(label, question):
    """Explicit negation, remainder, and a few closed binary distinctions."""
    if _has(r"\b(?:not|other|rest|remaining|left|unspent|unsold|aren't|don't)\b", question):
        return True
    pairs = [('male', 'female'), ('boy', 'girl'), ('adult', 'child'), ('agree', 'disagree'),
             ('interesting', 'uninteresting'), ('below', 'above'), ('men', 'women'),
             ('man', 'woman'), ('invalid', 'valid'), ('incorrect', 'correct'),
             ('wrong', 'right'), ('failed', 'passed'), ('fail', 'pass'),
             ('defective', 'good'), ('busy', 'available'), ('gave away', 'keep'),
             ('go', 'keep'), ('half-day', 'full-day')]
    lw, qw = _words(label), _words(question)
    if _has(r"\b(?:not|aren't|don't|doesn't|won't)\b", label) and lw & qw:
        return True
    for a, b in pairs:
        if (a in lw and b in qw or b in lw and a in qw
                or a in label and b in question and '-' in a):
            return True
    return False


def _selection(label, question, body):
    if _opposite(label, question):
        return -1
    # A rest category may have an arbitrary descriptive name.
    rest = re.search(r'\b(?:the rest|the remainder|remaining\s+\w+)\s+([^.;!?]+)', body)
    if rest and (_words(rest.group(1)) - _words(label)) & _words(question):
        return -1
    if _words(label) & _words(question):
        return 1
    return 0


def _quantities(p):
    result = []
    for n in p.numbers:
        tail = p.text[n.end:].lower()
        if _has(r'\bgrade\s*$', p.text[:n.start].lower()):
            continue  # a school grade label, not a population count
        if n.value == 1 and _has(r'^\s+day\b', tail) and _has(r'^\s*$', p.text[:n.start]):
            continue  # sentence-initial "One day ..."
        # These label an attendance schedule rather than a numerical half.
        if n.raw.lower() == 'half' and tail.startswith('-day'):
            continue
        if n.raw.lower() in ('third', 'quarter', 'fourth') and re.match(r'\s+(?:week|month|year|day|round|test)\b', tail) and _has(r'\bthe\s*$', p.text[:n.start].lower()):
            continue
        # "in one day" repeats the daily unit, rather than supplying a factor.
        if n.value == 1 and re.match(r'\s+(?:day|week|month|year)\b', tail):
            before = p.text[max(0, n.start-8):n.start].lower()
            if _has(r'\bin\s*$', before):
                continue
        result.append(n)
    # An explicit demonstrative can repeat an already stated base count.
    for n in list(result):
        if n.kind != 'percent' and _has(r'\bof (?:those|these)\s*$', p.text[:n.start].lower()):
            earlier = [x for x in result if x.end < n.start and x.kind != 'percent' and x.value == n.value]
            if len(earlier) == 1:
                result.remove(n)
    return result


def _change(p, ns):
    """Known price/salary and an explicit discount, raise, tax or comparison."""
    rates = [n for n in ns if n.kind == 'percent']
    amounts = [n for n in ns if n.kind != 'percent']
    if len(rates) != 1 or not amounts:
        return None
    n = rates[0]
    r = n.value
    text, q = p.text.lower(), p.question
    clause = _sentence(text, n.start, n.end)
    tail = text[n.end:]
    # A fraction of a population agreeing to a change is not itself that
    # change. "Raise 30% of the money" similarly describes collecting a share.
    tax_query = n.start >= len(p.body) and _has(r'\btax\b', q) and _has(r'\bprice\b', q)
    if _has(r'^\s+of\b', tail) and not tax_query and not _has(r'^\s+of\s+(?:the |its |their )?(?:original|initial|wholesale)\b', tail):
        return None
    if _has(r'\b(?:annual|yearly)\b', q) and _has(r'/month\b|\bper month\b', p.body):
        return None
    decrease = _has(r'\b(?:discount|off|reduc\w*|decreas\w*|shorten\w*|down|less|fewer|cheaper|shorter|lower)\b', clause)
    increase = _has(r'\b(?:tax|tips?|tipped|interest|rais\w*|increas\w*|markup|mark-up|adds?|added|more|taller|longer|higher)\b', clause)
    subset = _has(r'^\s+of\s+(?:the |its |their )?(?:original|initial|wholesale)\b', tail)
    related_item = _has(r'^\s+as much as\b', tail)
    if _has(r'\bfinance charge\b', clause):
        increase = True
    if not (decrease or increase or subset or related_item) or (decrease and increase):
        return None
    factor = r if subset else 1-r if decrease else 1+r
    if factor <= 0:
        return None
    # Other quantities are accepted only as explicit purchasing counts or a
    # total over the old and new periods.
    period_total = False
    multiplier = Fraction(1)
    if len(amounts) > 1:
        money = [a for a in amounts if a.kind == 'money']
        conversion = None
        if not money and len(amounts) == 2:
            source, scale = amounts
            su = re.match(r'\s+([a-z]+)', text[source.end:])
            cm = re.match(r'\s+([a-z]+)\s+per\s+([a-z]+)', text[scale.end:])
            if su and cm and _singular(su.group(1)) == _singular(cm.group(2)) and _singular(cm.group(1)) in _words(q):
                conversion = scale
                multiplier = scale.value
                amount = source
            else:
                return None
        elif len(money) != 1:
            return None
        else:
            amount = money[0]
        extras = [a for a in amounts if a != amount]
        if conversion:
            pass
        elif len(extras) == 1 and extras[0].start >= len(p.body) and _has(
                r'\btotal\b', q) and extras[0].value == 2 and _has(r'\b(?:months?|days?|years?|weeks?)\b', text[extras[0].end:]):
            period_total = True
        elif len(extras) == 1 and _has(r'\b(?:each|bottles?|items?|buy|buys|buying)\b', text):
            extra = extras[0]
            unit = re.match(r'\s+([a-z]+)', text[extra.end:])
            if not unit or unit.group(1) in ('months', 'years', 'days', 'weeks'):
                return None
            multiplier = extra.value
        else:
            return None
    else:
        amount = amounts[0]
        if increase and _has(r'\bboth (?:years|months|days|weeks)\b', q):
            period_total = True
    if increase and _has(r'\bsells?\b', text) and not _has(
            r'\b(?:cost|price|pay|paid|revenue|profit|earn|sell for)\b', q):
        return None
    requested = re.split(r'\bif\b', q)[0]
    inverse = _has(r'\b(?:original|previous|before|initial|wholesale|old)\b', requested)
    inverse = inverse or (_has(r'\bthen\b', q) and _has(r'\bcurrently\b', p.body) and _has(r'\bthan\b', clause))
    # "cost ... percent as much" is a second item, not a changed price.
    if related_item:
        factor = r
    if inverse:
        value = amount.value/factor
    elif _has(r'\b(?:how much more|how much less|save|savings|discount amount|interest|tax alone|tip)\b', q) and not _has(
            r'\b(?:including|after|with|total|entire|pay back|price|cost)\b', q):
        value = amount.value*r
    else:
        value = amount.value*factor
    if period_total or related_item and _has(r'\b(?:everything|total|altogether|together|both)\b', q):
        value += amount.value
    value *= multiplier
    # Unit conversion is justified only by explicit source and query units.
    if _has(r'\binches\b', text[amount.end:amount.end+15]) and _has(r'\bfeet\b', q):
        value /= 12
    return _answer(value, 'Apply the stated percentage to the known amount')


def _single_subset(p, ns):
    rates = [n for n in ns if n.kind == 'percent']
    amounts = [n for n in ns if n.kind != 'percent']
    if len(rates) != 1 or len(amounts) != 1:
        return None
    rate, amount = rates[0], amounts[0]
    r, a = rate.value, amount.value
    if not 0 < r <= 1:
        return None
    text, q = p.text.lower(), p.question
    label = _labels(text, rate)
    if 'invalid' in _sentence(text, rate.start, rate.end):
        label += ' invalid'
    choice = _selection(label, q, p.body)
    if _has(r'\b(?:take-home|out-of-pocket)\b', q) and _has(r'\b(?:tax|insurance|covers?)\b', p.body):
        choice = -1
    if _has(r'\bmiss\b', q) and _has(r'\b(?:shots|attempted)\b', p.body):
        choice = -1
    if _has(r'\btotal\b', q) and _has(r'^\s+of what\b', text[rate.end:]) and _has(r'\balso\b', p.body):
        return _calc(a, '*', 1+r)
    # A measured amount of the action already described as a percentage is a
    # known part: "spent 30%; spent $12; how much is left?".
    before = text[max(0, amount.start-35):amount.start]
    if _has(r'\b(?:quiz|test|exam)\b', p.body) and _has(r'\b(?:mistakes|errors|wrong|incorrect)\b', text[amount.end:]) and _has(r'\b(?:items|questions|total)\b', q):
        return _calc(a, '/', 1-r) if r < 1 else None
    spent_part = amount.start > rate.end and _has(r'\b(?:spent|spends|used|uses|lost|loses|saved|saves)\s*$', before)
    if spent_part:
        if _has(r'\b(?:left|remaining|unspent|rest)\b', q):
            return _calc(a/r, '-', a)
        if _has(r'\b(?:original|start|total|allowance|income)\b', q):
            return _calc(a, '/', r)
        return None
    if _has(r'\b(?:earnings|start with|originally|in total|altogether)\b', q) and _has(r'\b(?:left|remaining)\b', p.body):
        return _calc(a, '/', 1-r)
    # If the only known count names the opposite of the percentage category,
    # it anchors the complementary part, not the whole population.
    known_label = re.split(r'[.;!?]', text[amount.end:])[0]
    known_before = re.split(r'[.;!?]|\band\b', text[:amount.start])[-1]
    if _opposite(label, known_label+' '+known_before):
        if choice == 1 and r < 1:
            return _answer(a*r/(1-r), 'Known complementary part / remaining share x requested share')
        if choice == 0 and r < 1:
            return _calc(a, '/', 1-r)
        return None
    if not choice:
        return None
    factor = r if choice == 1 else 1-r
    unit_scale = Fraction(1)
    if _has(r'^\s+liters?\b', text[amount.end:]) and _has(r'\b(?:ml|milliliters)\b', q):
        unit_scale = Fraction(1000)
    return _calc(a*unit_scale, '*', factor)


def _nested(p, ns):
    """Two explicit nested proportions of a single base, or disjoint shares."""
    ratios = [n for n in ns if n.kind == 'percent' or n.value < 1]
    amounts = [n for n in ns if n not in ratios]
    if len(amounts) != 1 or not 2 <= len(ratios) <= 3:
        return None
    text, q = p.text.lower(), p.question
    if any(not 0 < n.value <= 1 for n in ratios):
        return None
    a = amounts[0]
    first, second = ratios[:2]
    between = text[first.end:second.start]
    tail = text[second.end:]
    first_label = _labels(text, first)
    second_label = _labels(text, second)
    prefix = re.split(r'[.;!?]', text[:second.start])[-1]
    nested = _has(r'^\s+of (?:those|these|them|the remaining)\b', tail)
    nested = nested or _has(r'\bof (?:those|these|the (?:remaining|\w+ who|\w+ that))\b', prefix)
    prefix_base = re.search(r'^\s*of (?:the )?([^,.;!?]+),', prefix)
    if prefix_base and _words(prefix_base.group(1)) & _words(first_label):
        nested = True
    # Repeating the first group's distinguishing noun after "of" establishes
    # the base of the second percentage.
    second_base = re.search(r'^\s+of\s+([^,.;!?]+?)(?:\s+(?:are|is|have|has)\b|[,.;!?])', tail)
    first_predicate = re.search(r'\b(?:are|is|were|was|have|has|bear|play|wear|work)\s+', text[first.end:second.start])
    if second_base and first_predicate and _words(second_base.group(1)) & _words(first_label):
        nested = True
    if first_predicate and _has(r'^\s+of\b', tail) and _words(tail.split('.')[0]) & _words(first_label):
        nested = True
    if nested:
        if a.start > first.start and not (_has(r'\b(?:left|remaining)\b', text[a.end:]) and _has(r'\bstart\b', q)):
            return None
        if len(ratios) == 3:
            # A redundant complementary percentage is not another stage.
            third = ratios[2]
            if second.value+third.value != 1 or not _has(r'\b(?:other|rest|remaining)\b', text[second.end:third.start]):
                return None
        if a.start > second.end and _has(r'\b(?:left|remaining)\b', text[a.end:]) and _has(r'\bstart\b', q):
            f = (1-first.value)*(1-second.value)
            return _calc(a.value, '/', f) if f else None
        choice = _selection(second_label, q, p.body)
        if not choice:
            return None
        first_share = 1-first.value if _has(r"\b(?:remaining|don't|not)\b", prefix) or _has(r'^\s+of the remaining\b', tail) else first.value
        second_share = second.value if choice == 1 else 1-second.value
        if _has(r'\bfinish\b', q) and _has(r'\breads?\b', p.body):
            first_share, second_share = 1-first.value, 1-second.value
        f = first_share*second_share
        return _calc(a.value, '*', f)
    if len(ratios) == 2 and _has(r'\b(?:remainder|rest|remaining)\b', p.body) and (
            _has(r'\b(?:remainder|rest|other|remaining)\b', q) or _selection(second_label, q, p.body) == -1):
        f = 1-first.value-second.value
        if f >= 0:
            # The base can itself be a known category count.
            if a.start < first.start and _has(r'^\s+of (?:the )?(?:entire|total|all)\b', text[first.end:]):
                return _calc(a.value/first.value, '*', f)
            if a.start > second.end:
                known = _words(re.split(r'[,.;!?]', p.body[a.end:])[0])
                common = _words(first_label) & _words(second_label)
                if known & (_words(first_label)-common):
                    return _calc(a.value/first.value, '*', f)
                if known & (_words(second_label)-common):
                    return _calc(a.value/second.value, '*', f)
            return _calc(a.value, '*', f)
    return None


def _percent_of_rate(p, ns):
    """Scale an explicit per-period amount before taking its percentage."""
    rates = [n for n in ns if n.kind == 'percent']
    amounts = [n for n in ns if n.kind != 'percent']
    if len(rates) != 1:
        return None
    text, q = p.text.lower(), p.question
    if _has(r'\b(?:more|higher|longer|taller|less|shorter|lower)\b', _sentence(text, rates[0].start, rates[0].end)):
        return None
    r = rates[0].value
    if not 0 < r <= 1:
        return None
    # Annual bill quoted monthly, with a yearly discount.
    if len(amounts) == 1 and _has(r'\bdiscount\b', text) and _has(r'\bannual\b', q):
        if _has(r'/month\b|\bper month\b', p.body):
            return _calc(amounts[0].value*12, '*', 1-r)
    if len(amounts) == 1 and _has(r'\beach year\b', q) and _has(r'\ba month\b', p.body) and _has(r'\bpay\b', q):
        return _calc(amounts[0].value*12, '*', r)
    if len(amounts) != 2:
        return None
    a, b = amounts
    # Equal monthly instalments of an annual income.
    if _has(r'\bequal monthly payments\b', text[b.end:]) and _has(r'\beach month\b', q):
        if b.value > 0 and _has(r'\ba year\b', text[a.end:b.start]):
            return _calc(a.value/b.value, '*', r)
    # Product of an hourly/daily rate and an explicitly matching duration.
    units = r'(second|minute|hour|day|week|month|year)'
    for rate, duration in ((a, b), (b, a)):
        suffix = text[rate.end:]
        rm = re.match(r'\s+[a-z -]+?\s+(?:a|per|each|every)\s+'+units+r'\b', suffix)
        dm = re.match(r'\s+'+units+r's?\b', text[duration.end:])
        if rm and dm and rm.group(1) == dm.group(1):
            if _selection(_labels(text, rates[0]), q, p.body) == 1:
                return _calc(rate.value*duration.value, '*', r)
    # N items per group, G groups, and a percentage choosing a category.
    for rate, count in ((a, b), (b, a)):
        rm = re.match(r'\s+([a-z]+)\s+(?:per|each|a)\s+([a-z]+)\b', text[rate.end:])
        cm = re.match(r'\s+([a-z]+)\b', text[count.end:])
        if rm and cm and _singular(rm.group(2)) == _singular(cm.group(1)):
            if _singular(rm.group(1)) in _words(q) and _selection(_labels(text, rates[0]), q, p.body) == 1:
                return _calc(rate.value*count.value, '*', r)
    # Hours/day x days/week, asked for weekly hours.
    if _has(r'^\s+hours? a day\b', text[a.end:]) and _has(r'^\s+days? a week\b', text[b.end:]):
        if _has(r'\bhours? per week\b', q):
            return _calc(a.value*b.value, '*', r)
    return None


def _same_base_rates(p, ns):
    """A known percentage amount and a new percentage of the same whole."""
    rates = [n for n in ns if n.kind == 'percent']
    amounts = [n for n in ns if n.kind != 'percent']
    if len(amounts) != 1 or len(rates) not in (2, 3):
        return None
    text = p.text.lower()
    first = rates[0]
    amount = amounts[0]
    target = rates[-1]
    if first.value <= 0:
        return None
    if len(rates) == 3 and target.value != rates[1].value:
        return None
    if _has(r'\btip\b', p.body) and _has(r'\btip\b', p.question):
        if _has(r'^\s+tip of\s*$', text[first.end:amount.start]):
            return _calc(amount.value/first.value, '*', target.value)
    if len(rates) == 2 and amount.end < first.start and _has(
            r'\bthis is\s*$', text[:first.start]) and _has(r'^\s+of\b', text[first.end:]):
        before = re.split(r'[.;!?]', text[:target.start])[-1]
        subject = re.sub(r'\b(?:comprise|represent|account for|make up|are|is)\s*$', '', before).strip()
        first_words = _words(re.split(r'[.;!?]', text[amount.end:])[0])
        if (_words(subject)-first_words) & _words(p.question):
            return _calc(amount.value/first.value, '*', target.value)
    return None


def _successive_changes(p, ns):
    rates = [n for n in ns if n.kind == 'percent']
    amounts = [n for n in ns if n.kind != 'percent']
    if len(rates) != 2 or len(amounts) != 1 or not _has(r'\b(?:current|new|final|now)\b', p.question):
        return None
    text = p.text.lower()
    factors = []
    for n in rates:
        prefix = text[max(0, n.start-35):n.start]
        tail = text[n.end:n.end+35]
        if _has(r'\b(?:raise|increase)(?: of| by)?\s*$', prefix) or _has(r'^\s+(?:higher|more|increase|raise)\b', tail):
            factors.append(1+n.value)
        elif _has(r'\b(?:discount|decrease|reduction)(?: of| by)?\s*$', prefix) or _has(r'^\s+(?:lower|less|off)\b', tail):
            factors.append(1-n.value)
        else:
            return None
    if any(f <= 0 for f in factors):
        return None
    return _calc(amounts[0].value*factors[0], '*', factors[1])


def _asked_percentage(p, ns):
    """Express a selected count as a percentage of disjoint category counts."""
    if not _has(r'^what (?:is the )?percent(?:age)?\b', p.question):
        return None
    if any(n.kind == 'percent' for n in ns) or not 2 <= len(ns) <= 4:
        return None
    text = p.text.lower()
    if _has(r'\b(?:difference|average|taller|shorter|increase|decrease)\b', p.question):
        return None
    if any(n.start >= len(p.body) for n in ns):
        return None
    if _has(r'\b(?:each|per|every|times|twice|ate|eat|eats|adds?|added|lost|loses|sold|removed|more|fewer|difference|average)\b', p.body):
        return None
    labels = []
    for n in ns:
        after = re.split(r'[,.;!?]|\band\b', text[n.end:])[0]
        before = re.split(r'[,.;!?]|\band\b', text[:n.start])[-1]
        owner = re.search(r'\b([a-z]+)\s+(?:has |have |had )?(?:won|scored|made|makes|collected)\s*$', before)
        labels.append(_words(after) | ({owner.group(1)} if owner else set()))
    common = set.intersection(*labels)
    targets = [i for i, label in enumerate(labels) if (label-common) & _words(p.question)]
    if len(targets) != 1:
        return None
    selected = ns[targets[0]].value
    total = sum((n.value for n in ns), Fraction(0))
    totals = [i for i, n in enumerate(ns) if _has(r'\btotal\b', re.split(r'[.;!?]', text[n.end:])[0])]
    if totals:
        if len(totals) != 1 or totals[0] == targets[0]:
            return None
        total = ns[totals[0]].value
    if total <= 0 or selected > total:
        return None
    return _answer(100*selected/total, 'Selected count / total count x 100')


def _quantity_adjustment(p, ns):
    """An explicit percentage target, minus the amount already present."""
    rates = [n for n in ns if n.kind == 'percent']
    amounts = [n for n in ns if n.kind != 'percent']
    if len(rates) != 1 or len(amounts) != 2:
        return None
    text, q = p.text.lower(), p.question
    r = rates[0].value
    a, b = amounts
    if not 0 < r <= 1:
        return None
    if _has(r'\b(?:capacity|holds?)\b', text[:a.start]) and _has(r'\b(?:more|additional)\b', q):
        unit_a = re.match(r'\s+([a-z]+)', text[a.end:])
        unit_b = re.match(r'\s+([a-z]+)', text[b.end:])
        if unit_a and unit_b and unit_a.group(1) == unit_b.group(1) and _has(r'\b(?:currently|already|now)\b', p.body):
            return _calc(a.value*r, '-', b.value)
    # The tip is a percentage of a bill, less another person's contribution.
    if _has(r'\btip\b', p.body) and _has(r'\b(?:kick in|contribut\w*)\b', p.body) and _has(r'\b(?:add|pay|contribute)\b', q):
        if a.kind == b.kind == 'money' and rates[0].start < a.start < b.start:
            return _calc(a.value*r, '-', b.value)
    if a.end < rates[0].start < b.start and _has(r'\b(?:left|now|remaining)\b', q):
        # The first stage either retains a selected group or removes a group.
        percent_clause = _sentence(text, rates[0].start, rates[0].end)
        if _has(r'\b(?:fresh|sprout|sprouted|usable|valid)\b', percent_clause):
            retained = r
        elif _has(r'\b(?:eaten|adopts? out|gave away|loses?|lost|destroyed|burned)\b', percent_clause):
            retained = 1-r
        else:
            return None
        before_b = text[max(rates[0].end, b.start-55):b.start]
        if _has(r'\b(?:take back|returned|returns?|back)\b', before_b):
            return _calc(a.value*retained, '+', b.value)
        if _has(r'\b(?:sells?|sold|throw|throws|shoots?|destroys?|removes?)\b', before_b):
            return _calc(a.value*retained, '-', b.value)
    return None


def _income_sum(p, ns):
    rates = [n for n in ns if n.kind == 'percent']
    amounts = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n.kind == 'number']
    if len(rates) != 1 or not 2 <= len(amounts) <= 5:
        return None
    text, q = p.text.lower(), p.question
    saving = _has(r'\bsaves?\b', p.body) and _has(r'\bsave\b', q)
    commission = _has(r'\bcommission\b', p.body) and _has(r'\bcommission\b', q)
    if not (saving or commission):
        return None
    if counts:
        if not commission or any(n.value != len(amounts) for n in counts):
            return None
    for n in amounts:
        clause = _sentence(text, n.start, n.end)
        if not _has(r'\b(?:made|earned|received|sold for|selling|another)\b', clause):
            return None
    return _calc(sum((n.value for n in amounts), Fraction(0)), '*', rates[0].value)


def _allocation(p, ns):
    """Recover a whole from a counted share, or split a remaining budget."""
    rates = [n for n in ns if n.kind == 'percent']
    amounts = [n for n in ns if n.kind != 'percent']
    if len(rates) != 1 or not 2 <= len(amounts) <= 3:
        return None
    rate = rates[0]
    if not 0 < rate.value < 1:
        return None
    text, q = p.text.lower(), p.question
    # Two known categories and one uncounted category; one known category is
    # explicitly a fraction of the total.
    if len(amounts) == 2 and _has(r'\b(?:some|unknown)\b', p.body) and _has(r'\btotal\b', _sentence(text, rate.start, rate.end)):
        label = _labels(text, rate)
        # In "the green pieces are 25%", use the subject, not "of total".
        before = re.split(r'[.;!?]', text[:rate.start])[-1]
        subject = re.search(r'(?:if )?(?:the )?(.+?)\s+(?:is|are|represent)\s*$', before)
        if not subject:
            return None
        label = _words(subject.group(1))
        descriptors = []
        for n in amounts:
            tail = re.split(r'[,.;!?]|\band\b', text[n.end:])[0]
            descriptors.append(_words(tail))
        unique = [label & words - set.intersection(*descriptors) for words in descriptors]
        anchors = [i for i, words in enumerate(unique) if words]
        unknown = re.search(r'\b(?:some|unknown)\s+([^.;!?]+)', p.body)
        if len(anchors) == 1 and unknown and _words(unknown.group(1)) & _words(q):
            whole = amounts[anchors[0]].value/rate.value
            return _answer(whole-sum((n.value for n in amounts), Fraction(0)), 'Known part / its share - the counted categories')
    money = [n for n in amounts if n.kind == 'money']
    counts = [n for n in amounts if n.kind == 'number']
    if len(money) == 1 and counts and _has(r'\b(?:rest|remaining)\b', p.body) and _has(r'\b(?:same amount|equally|each)\b', text):
        target = []
        label = _words(_labels(text, rate))
        for n in counts:
            unit = re.match(r'\s+([a-z]+)', text[n.end:])
            if not unit:
                return None
            word = _singular(unit.group(1))
            if word in _words(q):
                target.append(n)
            elif word not in label:
                return None
        if len(target) == 1 and target[0].value > 0:
            return _calc(money[0].value*(1-rate.value), '/', target[0].value)
    return None


def _mixture(p, ns):
    """One ingredient reduced to a proportion, then known ingredients added."""
    rates = [n for n in ns if n.kind == 'percent']
    amounts = [n for n in ns if n.kind != 'percent']
    if len(rates) != 1 or not 2 <= len(amounts) <= 4 or not _has(r'\btotal\b', p.question):
        return None
    text = p.text.lower()
    rate = rates[0]
    if not _has(r'^\s+of (?:its|the) (?:initial|original) (?:volume|weight|size|amount)\b', text[rate.end:]):
        return None
    base = [n for n in amounts if n.end < rate.start]
    extras = [n for n in amounts if n.start > rate.end]
    if len(base) != 1 or len(extras) != len(amounts)-1:
        return None
    units = [re.match(r'\s+([a-z]+)', text[n.end:]) for n in amounts]
    if not all(units) or len(set(m.group(1) for m in units)) != 1:
        return None
    if not _has(r'\b(?:mixes?|adds?|combines?)\b', text[rate.end:]):
        return None
    return _answer(base[0].value*rate.value+sum((n.value for n in extras), Fraction(0)), 'Reduced ingredient + the other ingredients')


def solve(problem):
    # Conversational descriptions of what the speaker is trying to learn
    # belong to the ordinary help modules, rather than this narrative reader.
    if _has(r"^(?:i(?: am|'m)|we(?: are|'re))\s+(?:trying|learning|wondering)\b", problem.text.lower()):
        return None
    # Resolve composed relations before trying the one-base readers below.
    from .percentages_r04_a6 import solve as composed_percentages
    composed = composed_percentages(problem)
    if composed is not None:
        return composed
    ns = _quantities(problem)
    if _has(r'^what (?:is the )?percent(?:age)?\b', problem.question):
        return _asked_percentage(problem, ns)
    if not any(n.kind == 'percent' for n in ns):
        return None
    for rule in (_same_base_rates, _successive_changes, _allocation, _quantity_adjustment, _income_sum,
                 _mixture, _change, _single_subset, _nested, _percent_of_rate):
        result = rule(problem, ns)
        if result is not None:
            return result
    return None
