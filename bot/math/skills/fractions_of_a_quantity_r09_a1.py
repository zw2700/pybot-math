"""Composed fraction operations with explicit bases, units and question scopes.

These readers distinguish an original stock, a running remainder and a previous
transaction. Each reader accounts for every numeric quantity before answering.
"""
import re
from fractions import Fraction

from ._fractions_common import _has, _answer, has_fraction
from ..numbers import read_numbers, format_number
from ..problem import Problem, ASK
from .fractions_of_a_quantity_r03_a3 import _prepare as _base_prepare, _words, _label
from .counting_and_totals_r00_a1 import _singular
from .comparisons_r01_a2 import _mentions, _noun


def _tokens(p):
    text = p.text
    for i, n in reversed(list(enumerate(p.numbers))):
        text = text[:n.start] + 'N' + str(i) + text[n.end:]
    return text


def _prepare(problem):
    text = problem.text
    asks = list(ASK.finditer(text))
    if not asks:
        return None
    at = asks[-1].start()
    normalized = Problem(text, text[:at].lower(), text[at:].lower(), read_numbers(text))
    result = _base_prepare(normalized)
    if result is not None:
        result.entities = [name for name in result.entities if name not in
                           ('calculate','determine','once','over','since','during','next','finally','half')]
    return result


def _unit(p, n):
    m = re.match(r'\s+(?:(?:brand )?new |additional |female |male |dozens? )?([a-z]+)', p.text[n.end:])
    return _singular(m.group(1)) if m else ''


_LOSS = r'\b(?:ate|eats?|eat|eaten|lost|loses?|spent|spends?|used|uses?|sold|sells?|gave|gives?|donated|drank|drinks?|chewed|removed|stolen|broke|broken|paints?|painted|completed|finished)\b'
_GAIN = r'\b(?:adds?|added|receives?|received|gets?|got|buys?|bought|returned|returns?)\b'


def _stock(p, fs):
    """Literal stock changes followed by scoped proportional consumption."""
    if not fs or not _has(r'\b(?:left|remaining|currently have|have now|now have|still have)\b', p.question):
        return None
    if _has(r'\b(?:every|per|times|as many|as much|originally|at first)\b', p.text):
        return None
    if _has(r'\beach\b', re.sub(r'\beach (?:month|week|year)\b', '', p.text)):
        return None
    ns = list(p.numbers)
    ns = [n for n in ns if not (_has(r'\bafter\s*$', p.text[:n.start]) and
          re.match(r'\s+(?:days|weeks|months)\b', p.text[n.end:]) and n.start < len(p.body))]
    if not 2 <= len(ns) <= 5 or ns[0] in fs:
        return None
    # A count of elapsed days in the query is a label, not another stock.
    if ns[-1].start >= len(p.body):
        if not (_has(r'\bafter (?:these |the )?$', p.text[:ns[-1].start]) and
                re.match(r'\s+days?\b', p.text[ns[-1].end:]) and
                ns[-1].value == len(ns)-2):
            return None
        ns.pop()
    if any(n.start >= len(p.body) for n in ns):
        return None
    first = ns[0]
    if not _has(r'\b(?:has|have|had|made|bought|gets?|collected|contains?|harvested|ordered)\b', p.text[:first.start]):
        return None
    unit = _unit(p, first)
    initial_owners = _mentions(p.text[:first.start], p.entities)
    asked = _mentions(p.question, p.entities)
    if initial_owners and asked and initial_owners[-1] != asked[0]:
        return None
    current = original = first.value*(12 if re.match(r'\s+dozens?\b', p.text[first.end:]) else 1)
    last_loss = None
    for i, n in enumerate(ns[1:], 1):
        before = p.text[ns[i-1].end:n.start]
        after = p.text[n.end:ns[i+1].start if i+1 < len(ns) else len(p.body)]
        verbs = list(re.finditer(_LOSS + '|' + _GAIN, before))
        passive_loss = n in fs and re.match(r'\s+were (?:stolen|eaten|lost|sold|removed)\b', after)
        if not verbs and not passive_loss and not (n in fs and last_loss is not None and _has(r'\band\s*$', before)):
            return None
        gain = bool(verbs and _has(_GAIN, verbs[-1].group()))
        if n in fs:
            if gain or not (passive_loss or re.match(r"\s+(?:of|the|his|her|their|to|that)\b", after)):
                return None
            base = original if _has(r'\b(?:original|initial|he made|she made|they made)\b', after) else current
            if last_loss is not None and _has(r'\bthe number\b.*\b(?:he|she|they) did this (?:week|day|month)\b', after):
                base = last_loss
            loss = base*n.value
        else:
            elided = bool(re.match(r'\s*[.;,]', after))
            remaining_unit = re.match(r'\s+of the remaining ([a-z]+)', after)
            elided = elided or bool(remaining_unit and _singular(remaining_unit.group(1)) == unit)
            if _unit(p, n) != unit and not elided and not re.match(r'\s+of (?:them|these|those)\b', after):
                return None
            if _has(r'\b(?:less|fewer|more)\b', after):
                if last_loss is None or gain:
                    return None
                loss = last_loss + (n.value if _has(r'\bmore\b', after) else -n.value)
            else:
                loss = -n.value if gain else n.value
        if loss < 0 and not gain:
            return None
        current -= loss
        if current < 0:
            return None
        if not gain:
            last_loss = loss
    return _answer(current, 'Apply each change to the stock and each fraction to its stated base')


def _repeated_reduction(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    if not _has(r'how (?:many (?:days|weeks|months|years)|long)', p.question):
        return None
    f = fs[0]
    amounts = [n for n in p.numbers if n not in fs]
    start, target = amounts
    if not start.start < f.start < target.start or not 0 < target.value < start.value:
        return None
    if not _has(r'\b(?:cuts?|reduces?|decreases?|divides?)\b', p.body) or not _has(
            r'\b(?:each|every) (?:day|week|month|year)\b', p.body):
        return None
    if not _has(r'\bin\s*$', p.text[:f.start]):
        return None
    current, count = start.value, 0
    while current > target.value and count < 100:
        current *= f.value
        count += 1
    if current != target.value:
        return None
    return _answer(Fraction(count), 'Count the repeated proportional reductions needed to reach the target')


def _depletion_time(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3 or not _has(r'how (?:many (?:days|hours|weeks)|long)', p.question):
        return None
    total, rate = [n for n in p.numbers if n not in fs]
    f = fs[0]
    if not total.start < rate.start < f.start or rate.value <= 0:
        return None
    if not _has(r'\b(?:lose|loses|losing|die|dies|use|uses|consume|consumes)\b', p.text[:rate.start]):
        return None
    if not _has(r'\bper (?:day|hour|week)\b', p.text[rate.end:f.start]):
        return None
    if not _has(r'\b(?:initial|original)\b', p.text[f.end:]):
        return None
    return _answer(total.value*(1-f.value)/rate.value, 'Amount lost before reaching the target share / loss per period')


def _weekly_pay_share(p, fs):
    if len(fs) != 1 or len(p.numbers) != 4:
        return None
    f = fs[0]
    others = [n for n in p.numbers if n not in fs]
    days = [n for n in others if re.match(r'\s+days? (?:a|per|each|every) week\b', p.text[n.end:])]
    hours = [n for n in others if re.match(r'\s+hours? (?:a|per|each|every) day\b', p.text[n.end:])]
    pay = [n for n in others if n.kind == 'money' and re.match(r'\s+(?:an? |per |each )hour\b', p.text[n.end:])]
    if len(days) != 1 or len(hours) != 1 or len(pay) != 1:
        return None
    if not _has(r'\bweekly\b', p.text[f.end:]) or not _has(r'\b(?:allocat|sav|spend|donat|keep)', p.text[:f.start]):
        return None
    if not _has(r'\b(?:allocat|sav|spend|donat|keep)', p.question):
        return None
    return _answer(days[0].value*hours[0].value*pay[0].value*f.value,
                   'Days per week x hours per day x hourly pay x allocated share')


def _population_product(p, fs):
    """Count x output per member x a share, with either removal or growth."""
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    f = fs[0]
    count, rate = [n for n in p.numbers if n not in fs]
    if not count.start < rate.start < f.start:
        return None
    if not _has(r'\b(?:each|per)\b', p.text[count.end:f.start]):
        return None
    tail = p.text[f.end:len(p.body)]
    if _has(r'\b(?:laid off|fired|dismissed|removed)\s*$', p.text[:f.start]) and _has(r'\bremaining\b', p.question):
        if not _has(r'\b(?:paid|pay|money|cost|earn)\b', p.question):
            return None
        return _answer(count.value*(1-f.value)*rate.value, 'Remaining members x pay per member')
    if _has(r'\b(?:hatched|hatch|survived)\b', tail) and _has(r'\b(?:laid|lay|produced)\b', p.text[count.end:rate.start]):
        if not _has(r'\b(?:total|now|in all)\b', p.question):
            return None
        if _unit(p, count) not in _words(p.question):
            return None
        return _answer(count.value+count.value*rate.value*f.value,
                       'Original population plus the surviving offspring')
    return None


def _capacity_share(p, fs):
    if len(fs) != 1 or not 3 <= len(p.numbers) <= 4:
        return None
    f = fs[0]
    amounts = [n for n in p.numbers if n not in fs]
    if not amounts[0].start < amounts[1].start < f.start:
        return None
    if len(amounts) == 3 and (amounts[2].start < f.start or amounts[2].value != amounts[1].value):
        return None
    if not _has(r'\bcapacity\b', p.text[amounts[0].end:amounts[1].start]):
        return None
    if not _has(r'\b(?:not occupied|empty|unoccupied)\b', p.text[f.end:len(p.body)]):
        return None
    if not _has(r'\b(?:attend|present|occup|people|member)', p.question):
        return None
    return _answer(amounts[0].value*amounts[1].value*(1-f.value),
                   'Number of groups x capacity x occupied share')


def _area_shares(p, fs):
    if not 1 <= len(fs) <= 2 or len(p.numbers) != len(fs)+2:
        return None
    a, b = [n for n in p.numbers if n not in fs]
    if not a.start < b.start < fs[0].start:
        return None
    if not _has(r'\b(?:length|long)\b', p.text[:b.start]) or not _has(r'\b(?:width|wide)\b', p.text[a.end:fs[0].start]):
        return None
    if len(fs) == 1:
        if not _has(r'\barea\b', p.question) or not _has(r'\blength and width\b', p.text[fs[0].end:]):
            return None
        return _answer(a.value*b.value*fs[0].value**2, 'Scale both dimensions, then multiply for area')
    first, second = fs
    if not _has(r'^\s+of (?:the )?(?:rest|remaining)\b', p.text[second.end:]):
        return None
    rest = re.search(r'\bthe rest\b[^.;]*\b(?:for|to|be|as)\s+([^.;]+)', p.text[second.end:len(p.body)])
    if not rest or not (_words(rest.group(1)) & _words(p.question)):
        return None
    return _answer(a.value*b.value*(1-first.value)*(1-second.value),
                   'Area x first remaining share x second remaining share')


def _successive_transfers(p, fs):
    if len(fs) != 2 or len(p.numbers) != 4 or not _has(r'\bleft\b', p.question):
        return None
    total, used = [n for n in p.numbers if n not in fs]
    if not total.start < fs[0].start < fs[1].start < used.start:
        return None
    recipients = []
    for i, f in enumerate(fs):
        before = p.text[total.end if i == 0 else fs[0].end:f.start]
        after = p.text[f.end:fs[1].start if i == 0 else used.start]
        if not _has(r'\b(?:gave|gives?|passed|passes?)\s*$', before):
            return None
        who = re.search(r'\bto (?:his |her |their )?(?:(?:friend|brother|sister|cousin) )?([a-z]+)', after)
        if not who:
            return None
        recipients.append(who.group(1))
    if recipients[0] == recipients[1] or not _has(r'\b'+re.escape(recipients[1])+r'\b', p.question):
        return None
    before = p.text[fs[1].end:used.start]
    if not _has(r'\b'+re.escape(recipients[1])+r'\b', before) or not _has(_LOSS, before):
        return None
    return _answer(total.value*fs[0].value*fs[1].value-used.value,
                   'Follow the two transferred shares, then subtract the final recipient\'s use')


def _relative_amount(p, fs):
    """An extra gift or expense explicitly refers to the preceding amount."""
    if len(fs) != 1 or len(p.numbers) not in (3, 4):
        return None
    f = fs[0]
    if not re.match(r'\s+(?:that (?:amount|many|much)|of that (?:amount|many)|as much as [a-z]+)\b', p.text[f.end:]):
        return None
    amounts = [n for n in p.numbers if n not in fs]
    # A stated count of transactions is a label only when all are enumerated.
    if len(amounts) == 3:
        label = amounts[0]
        if label.value != 2 or not re.match(r'\s+(?:[a-z]+ ){0,3}transactions\b', p.text[label.end:]):
            return None
        amounts = amounts[1:]
    a, b = amounts
    if _has(r'\b(?:before|original|at first)\b', p.question):
        if not a.start < f.start < b.start or not _has(r'\b(?:transferred|spent|paid|gave)\b', p.text[:a.start]):
            return None
        if not _has(r'\b(?:left|remaining)\b', p.text[b.end:len(p.body)]):
            return None
        return _answer(a.value*(1+f.value)+b.value, 'Remaining balance plus both related withdrawals')
    if a.start < b.start < f.start and _has(r'\b(?:now|total|in all|altogether)\b', p.question):
        gift = _has(r'\b(?:gives?|gave)\b', p.text[a.end:b.start]) and any(
            _has(r'\b'+re.escape(name)+r'\b', p.text[a.end:b.start]) for name in p.entities)
        if not (_has(_GAIN, p.text[a.end:b.start]) or gift) or not _has(_GAIN, p.text[b.end:f.start]):
            return None
        if _unit(p, a) != _unit(p, b):
            return None
        return _answer(a.value+b.value*(1+f.value), 'Opening stock plus the gift and the proportional extra gift')
    return None


def _nested_remainder(p, fs):
    """Two allocated shares, the second explicitly of the remainder."""
    if len(fs) != 2 or len(p.numbers) != 3:
        return None
    total = next(n for n in p.numbers if n not in fs)
    first, second = fs
    if not total.start < first.start < second.start:
        return None
    if not re.match(r'\s+of (?:the )?(?:remaining|rest)\b', p.text[second.end:]):
        return None
    if not (_has(r'\b(?:left|remaining|rest|final|last)\b', p.question) and
            _has(r'\b(?:all|whole|rest|remaining)\b', p.question)):
        return None
    return _answer(total.value*(1-first.value)*(1-second.value),
                   'Whole x unallocated first share x unallocated second share')


def _relative_earning_time(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3 or not p.question.startswith('how long'):
        return None
    f = fs[0]
    amounts = [n for n in p.numbers if n not in fs]
    pay, periods = amounts
    if not f.start < pay.start < periods.start or pay.kind != 'money' or pay.value <= 0:
        return None
    if not _has(r"^\s*(?:'s)?\s+(?:the )?(?:salary|income|pay|amount)", p.text[f.end:]):
        return None
    unit = re.match(r'\s+per (month|week|day|year)\b', p.text[pay.end:])
    if not unit or not re.match(r'\s+'+unit.group(1)+r's?\b', p.text[periods.end:]):
        return None
    if not _has(r'\bsame amount\b', p.question):
        return None
    return _answer(periods.value/f.value, 'Time for the lower earner = comparison period / salary ratio')


def _grouped_remainder(p, fs):
    """A share of a stock explicitly built from equal groups."""
    if len(fs) != 1 or len(p.numbers) not in (3, 4):
        return None
    f = fs[0]
    counts = [n for n in p.numbers if n not in fs and n.kind != 'money']
    prices = [n for n in p.numbers if n.kind == 'money']
    if len(counts) != 2 or len(prices) > 1:
        return None
    a, b = counts
    if not a.start < b.start < f.start:
        return None
    middle, tail = p.text[a.end:b.start], p.text[b.end:f.start]
    unit_a, unit_b = _unit(p, a), _unit(p, b)
    grouping = _has(r'\bon each of\b', middle)
    grouping = grouping or _has(r'\beach '+re.escape(unit_a)+r'\b', middle)
    grouping = grouping or _has(r'\beach\b', tail)
    grouping = grouping or _has(r'\beach [a-z]+ (?:had|has|contains?) (?:exactly )?$', p.text[:a.start])
    if not grouping or not re.match(r'\s+(?:of|the|his|her|their)\b', p.text[f.end:]):
        return None
    complement = _has(r'\b(?:left|remaining|remain|not sold|unsold|uneaten)\b', p.question)
    selected = _has(r'\b(?:sold|sale|received|money)\b', p.question)
    if not complement and not selected:
        return None
    if prices:
        price = prices[0]
        if price.start < f.start or not _has(r'\beach (?:at|for)?\s*$', p.text[f.end:price.start]):
            return None
    scale = 12 if re.match(r'\s+dozens?\b', p.text[b.end:]) else 1
    value = a.value*b.value*scale*(1-f.value if complement else f.value)
    return _answer(value*(prices[0].value if prices else 1),
                   'Equal groups x quantity per group x requested share x any unit price')


def _allowance_savings(p, fs):
    if len(fs) != 1 or len(p.numbers) != 4:
        return None
    f = fs[0]
    opening, rate, periods = [n for n in p.numbers if n not in fs]
    if not opening.start < rate.start < f.start < periods.start or opening.kind != 'money' or rate.kind != 'money':
        return None
    unit = re.match(r'\s+(?:a|per|each) (day|week|month)\b', p.text[rate.end:])
    if not unit or not re.match(r'\s+'+unit.group(1)+r's\b', p.text[periods.end:]):
        return None
    if not _has(r'\b(?:puts?|saves?|deposits?)\b', p.text[rate.end:f.start]) or not _has(r'\b(?:have|total|balance)\b', p.question):
        return None
    return _answer(opening.value+rate.value*f.value*periods.value,
                   'Opening savings plus periods x income per period x saved share')


def _related_price_purchase(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    f = fs[0]
    amounts = [n for n in p.numbers if n not in fs]
    price, count = amounts
    if not f.start < price.start < count.start or price.kind != 'money' or count.start < len(p.body):
        return None
    if not re.match(r'\s+of the (?:cost|price) of\b', p.text[f.end:]):
        return None
    if not _has(r'\b(?:buy|purchase)\b', p.question) or not _has(r'\band\b', p.question):
        return None
    related = re.search(r'\ban? ([a-z]+) costs?\s*$', p.text[:f.start])
    if not related or _unit(p, count) != _singular(related.group(1)):
        return None
    return _answer(price.value*(1+count.value*f.value),
                   'Known item price plus count x proportional item price')


def _proportional_collection_sale(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    f = fs[0]
    count, price = [n for n in p.numbers if n not in fs]
    if not count.start < f.start < price.start or price.kind != 'money':
        return None
    if not re.match(r'\s+as many\b', p.text[f.end:]):
        return None
    if not _has(r'\beach\b', p.text[f.end:price.start]) or not _has(r'\bsell', p.question):
        return None
    if not _has(r'\ball\b', p.question):
        return None
    return _answer(count.value*(1+f.value)*price.value,
                   'Combine the original and proportional collections, then multiply by the selling price')


def _labelled_parts(p, fs):
    """Distinct counted categories, with one requested fraction of each."""
    counts = [n for n in p.numbers if n not in fs]
    if len(fs) != len(counts) or not 2 <= len(fs) <= 3:
        return None
    if not all(n.start < fs[0].start for n in counts) or not _has(r'\b(?:total|altogether|combined|in all)\b', p.question):
        return None
    labels = {}
    for n in counts:
        m = re.match(r'\s+([a-z]+(?: [a-z]+)?)', p.text[n.end:])
        if not m:
            return None
        label = _noun(m.group(1))
        if not label or label in labels:
            return None
        labels[label] = n.value
    selected = set()
    value = Fraction(0)
    for f in fs:
        tail = p.text[f.end:]
        matches = [label for label in labels if re.match(r'\s+of (?:the )?'+re.escape(label)+r'\b', tail)]
        if len(matches) != 1 or matches[0] in selected:
            return None
        selected.add(matches[0])
        value += labels[matches[0]]*f.value
    return _answer(value, 'Add the requested fraction of each separately counted category')


def _gift_then_output(p, fs):
    if len(fs) != 1 or len(p.numbers) != 4:
        return None
    f = fs[0]
    initial, donor, output = [n for n in p.numbers if n not in fs]
    if not initial.start < f.start < donor.start < output.start:
        return None
    if _unit(p, initial) != _unit(p, donor):
        return None
    owners = _mentions(p.text[:initial.start], p.entities)
    if not owners:
        return None
    gift = p.text[initial.end:f.start]
    if not _has(r'\b(?:gave|gives?)\s+'+re.escape(owners[-1])+r'\b', gift):
        return None
    if not re.match(r'\s+of (?:his|her|their)\s*$', p.text[f.end:donor.start]):
        return None
    if not _has(r'\beach '+re.escape(_unit(p, initial))+r'\b', p.text[donor.end:output.start]):
        return None
    if _unit(p, output) not in _words(p.question):
        return None
    return _answer((initial.value+donor.value*f.value)*output.value,
                   'Original stock plus the received share, times output per item')


def _combined_pair(p, fs):
    """A total and a proportional relationship between its two members."""
    if len(fs) != 1 or len(p.numbers) != 2:
        return None
    f = fs[0]
    total = next(n for n in p.numbers if n not in fs)
    if not total.start < f.start or not _has(r'\b(?:together|combined|total)\b', p.text[:total.start]):
        return None
    before = re.split(r'[.;!?]', p.text[:f.start])[-1]
    after = re.split(r'[.;!?]', p.text[f.end:])[0]
    lefts, rights = _mentions(before, p.entities), _mentions(after, p.entities)
    if not lefts or not rights or lefts[-1] == rights[0]:
        return None
    if not re.match(r'\s+(?:of|the|as)\b', after):
        return None
    asked = list(dict.fromkeys(_mentions(p.question, [lefts[-1], rights[0]])))
    if len(asked) != 1:
        return None
    large = total.value/(1+f.value)
    answer = large*f.value if asked[0] == lefts[-1] else large
    # A proportional time retains the total's unit until the query converts it.
    if re.match(r'\s+years?\b', p.text[total.end:]) and _has(r'\bmonths?\b', p.question):
        answer *= 12
    return _answer(answer,
                   'Combined total / sum of the two relative shares, then select the requested member')


def _fixed_money_allocations(p, fs):
    amounts = [n for n in p.numbers if n not in fs]
    if not 2 <= len(fs) <= 3 or len(amounts) != 1 or amounts[0].kind != 'money':
        return None
    if not _has(r'\b(?:left|remaining|unspent)\b', p.question):
        return None
    if _has(r'\b(?:remaining|remainder|rest|each|per|times)\b', p.body):
        return None
    if not _has(r'\b(?:spent|spends|paid|pays)\b', p.body):
        return None
    if not _has(r'\b(?:money|budget|allowance|income|salary)\b', p.body):
        return None
    if not all(re.match(r'\s+(?:of|on|for)\b', p.text[f.end:]) for f in fs):
        return None
    return _answer(amounts[0].value*(1-sum((f.value for f in fs), Fraction(0))),
                   'Original money minus the disjoint allocations of that money')


def _split_recipients(p, fs):
    if len(fs) != 1 or len(p.numbers) != 4:
        return None
    f = fs[0]
    total, a, b = [n for n in p.numbers if n not in fs]
    if not total.start < f.start < a.start < b.start or min(a.value, b.value) <= 0:
        return None
    if not _has(r'\b(?:rest|remaining)\b', p.text[f.end:a.start]) or not _has(r'\bequally\b', p.body):
        return None
    for n in (a, b):
        before = re.split(r'[.;!?]', p.text[:n.start])[-1]
        if not _has(r'\beach\b', before) or not _has(r'\b(?:received|gets?|given)\s*$', before):
            return None
    if not _has(r'\b(?:altogether|total|in all|combined)\b', p.question):
        return None
    return _answer(total.value*f.value/a.value+total.value*(1-f.value)/b.value,
                   'Recipients of the first share plus recipients of the complementary share')


def _saving_time(p, fs):
    if len(fs) != 1 or len(p.numbers) != 4 or not p.question.startswith('how long'):
        return None
    f = fs[0]
    a, b, goal = [n for n in p.numbers if n not in fs]
    if not a.start < b.start < f.start < goal.start or any(n.kind != 'money' for n in (a, b, goal)):
        return None
    if not _has(r'\b(?:earns?|makes?|income)\b', p.text[:a.start]) or not _has(r'\b(?:month|week|day)\b', p.text[b.end:f.start]):
        return None
    if not _has(r'\b(?:away|saves?|saving)\b', p.text[f.end:]) or not _has(r'\bsave\b', p.question):
        return None
    if a.value+b.value <= 0:
        return None
    return _answer(goal.value/((a.value+b.value)*f.value),
                   'Savings goal / (combined income per period x saved share)')


def _exam_score(p, fs):
    if len(fs) != 1 or len(p.numbers) != 4 or not _has(r'\b(?:exam|test|quiz)\b', p.body):
        return None
    if not _has(r'\bscore\b', p.question):
        return None
    f = fs[0]
    total, wrong, delta = [n for n in p.numbers if n not in fs]
    if not total.start < wrong.start < delta.start < f.start:
        return None
    if not re.match(r'\s+(?:incorrect|wrong|mistakes?|errors?)\b', p.text[wrong.end:]):
        return None
    direction = re.match(r'\s+(more|less|fewer) than\s*$', p.text[delta.end:f.start])
    if not direction or not re.match(r'\s+(?:of )?the score of\b', p.text[f.end:]):
        return None
    return _answer((total.value-wrong.value)*f.value+delta.value*(1 if direction.group(1) == 'more' else -1),
                   'Correct answers x comparison fraction, then apply the score difference')


def _fractional_increase(p, fs):
    if len(fs) != 1 or len(p.numbers) not in (2, 3):
        return None
    f = fs[0]
    amounts = [n for n in p.numbers if n not in fs]
    if len(amounts) == 2:
        label = amounts[-1]
        if label.value != 2 or label.start < len(p.body) or not _has(r'\b(?:two|both)\b', p.question):
            return None
        amounts.pop()
    base = amounts[0]
    direction = re.match(r'\s+(?:times )?(more|greater|fewer|less)\b', p.text[f.end:])
    if not direction:
        return None
    if not _has(r'\b(?:total|together|combined|altogether)\b', p.question):
        return None
    sign = -1 if direction.group(1) in ('fewer', 'less') else 1
    return _answer(base.value*(2+sign*f.value), 'Original amount plus the amount changed by the stated fraction')


def _category_graph(p, fs):
    """Resolve explicitly compared noun categories and their counted anchors."""
    from .fractions_of_a_quantity_r03_a2 import _graph
    text = re.sub(r'\b(twice|thrice|double)\b',
                  lambda m: '3 times' if m.group() == 'thrice' else '2 times', p.text)
    q = Problem.read(text)
    if q is None:
        return None
    # Currency coin plurals name categories; they do not supply a bare fraction.
    q.numbers = [n for n in q.numbers if n.raw not in ('quarters', 'thirds', 'fourths')]
    t = _tokens(q)
    def category(s):
        s = re.sub(r'^(?:there (?:are|were) |the )', '', s.strip())
        s = _noun(s)
        return ' '.join(_singular(w) for w in s.split()) if s else None
    ending = r'(?=[,.;!?]|\s+(?:and|but|in|on|at|from|for|with)\b|$)'
    edges, used = [], set()
    patterns = [
        r'N(\d+)\s+(?:times\s+)?as (?:many|much)\s+(.+?)\s+as\s+(.+?)'+ending,
        r'N(\d+)\s+times (?:more|fewer)\s+(.+?)\s+than\s+(.+?)'+ending,
    ]
    for pattern in patterns:
        for m in re.finditer(pattern, t):
            i = int(m.group(1))
            left, right = category(m.group(2)), category(m.group(3))
            if not left or not right or left == right or len(left.split()) > 4 or len(right.split()) > 4:
                return None
            scale = q.numbers[i].value
            if scale <= 0:
                return None
            if _has(r'\bN'+str(i)+r'\s+times fewer\b', m.group()):
                scale = 1/scale
            edges.append((left, right, scale, Fraction(0)))
            used.add(i)
    # "For each A, there are k times as many B" supplies the omitted RHS.
    for m in re.finditer(r'for each ([a-z ]+?),[^.;]*?N(\d+) times as many ([a-z ]+?)'+ending, t):
        i = int(m.group(2))
        if i in used:
            continue
        left, right = category(m.group(3)), category(m.group(1))
        if not left or not right or left == right:
            return None
        edges.append((left, right, q.numbers[i].value, Fraction(0)))
        used.add(i)
    if not edges:
        return None
    nodes = {n for edge in edges for n in edge[:2]}
    known = []
    for i, n in enumerate(q.numbers):
        if i in used:
            continue
        candidates = [node for node in nodes if re.match(
            r'\s+'+r'\s+'.join(re.escape(w)+r'(?:s)?' for w in node.split())+r'\b', q.text[n.end:])]
        if len(candidates) != 1:
            return None
        known.append((candidates[0], n.value))
    values = _graph(edges, known)
    if values is None:
        return None
    asked_words = ' '.join(_singular(w) for w in re.findall(r'[a-z]+', q.question))
    asked = [node for node in nodes if _has(r'\b'+re.escape(node)+r'\b', asked_words)]
    if len(asked) == 1 and not _has(r'\b(?:total|altogether|combined|in all)\b', q.question):
        value = values[asked[0]]
    elif not asked and (_has(r'\b(?:total|altogether|combined|in all|are there|in the|in this)\b', q.question)):
        value = sum(values.values(), Fraction(0))
    else:
        return None
    return _answer(value, '; '.join(node+' = '+format_number(v) for node, v in sorted(values.items())))


def _named_relations(problem, p):
    """Use the established comparison graph after resolving linguistic labels."""
    from .fractions_of_a_quantity_r03_a2 import _comparisons, _prepare as graph_prepare
    text = problem.text
    text = re.sub(r'\bcircumference\b', 'length', text, flags=re.I)
    periods = set(re.findall(r'\bper (game|round|day|week|month)\b', p.text))
    if len(periods) == 1 and len(re.findall(r'\bper (?:game|round|day|week|month)\b', p.text)) >= 3:
        text = re.sub(r'\bper '+next(iter(periods))+r'\b|\bon average\b|\baverage(?= total)', '', text, flags=re.I)
    # An entity can have both a counted amount and a relative amount in one
    # sentence. Split the predicates so neither anchor is silently discarded.
    def split_predicate(m):
        clause = re.split(r'[.;!?]', text[:m.start()])[-1]
        subjects = _mentions(clause, p.entities)
        return '. '+subjects[0].title()+' has ' if subjects else m.group()
    text = re.sub(r'\band (?:only )?(?=(?:half|a third|one-third|\d+/\d+) of what)',
                  split_predicate, text, flags=re.I)
    # Participant counts are metadata only when they enumerate the named group.
    for n in reversed(problem.numbers):
        if n.value == len(p.entities)-1 and re.match(r'\s+(?:best )?friends\b', problem.text[n.end:], re.I):
            text = text[:n.start]+'some'+text[n.end:]
    # Query-side participant counts enumerate the names, not another holding.
    text = re.sub(r'\bthese (one|two|three|four|five|six|\d+) (boys|girls|people|teammates)\b',
                  lambda m: 'these '+m.group(2) if read_numbers(m.group(1))[0].value == len(p.entities) else m.group(), text, flags=re.I)
    text = re.sub(r'\bthese (boys|girls|people|teammates) have\b', r'these \1 have in total', text, flags=re.I)
    if problem.numbers:
        prefix = problem.text[:problem.numbers[0].start]
        subjects = _mentions(prefix.lower(), p.entities)
        if len(set(subjects)) == 1:
            first_sentence = text.find('.')
            if first_sentence >= 0:
                text = text[:first_sentence+1]+re.sub(r'\b(?:he|she)\b', subjects[0].title(), text[first_sentence+1:], count=1, flags=re.I)
    text = re.sub(r'\bhow many (.+?) are there\?', r'How many \1 are there in total?', text, flags=re.I)
    q = Problem.read(text)
    if q is None:
        return None
    return _comparisons(graph_prepare(q))


def _inverse_disjoint(p, fs):
    if len(fs) != 2 or len(p.numbers) != 3:
        return None
    amount = next(n for n in p.numbers if n not in fs)
    if amount.start < fs[-1].end or sum((f.value for f in fs), Fraction(0)) >= 1:
        return None
    if re.match(r'\s+of (?:the )?(?:remaining|rest|those|these)\b', p.text[fs[-1].end:]):
        return None
    rest = re.search(r'\b(?:the remaining|the rest|remaining)\s+([^.;]+)', p.body)
    if not rest or not _words(rest.group(1)) & _words(p.question):
        return None
    labels = [_words(_label(p, f)) for f in fs]
    common = labels[0] & labels[1]
    known = _words(re.split(r'[.;!?]', p.text[amount.end:])[0])
    scores = [len((label-common) & known) for label in labels]
    if max(scores) == 0 or scores.count(max(scores)) != 1:
        return None
    whole = amount.value/fs[scores.index(max(scores))].value
    return _answer(whole*(1-sum((f.value for f in fs), Fraction(0))),
                   'Recover the whole from its labelled part, then remove the disjoint shares')


def _earnings_gap(p, fs):
    if len(fs) != 1 or len(p.numbers) != 4:
        return None
    f = fs[0]
    a, b, goal = [n for n in p.numbers if n not in fs]
    if not a.start < f.start < b.start < goal.start or any(n.kind != 'money' for n in (a, b, goal)):
        return None
    if not re.match(r'\s+that amount\b', p.text[f.end:]):
        return None
    if not _has(r'\bearn', p.text[:a.start]) or not _has(r'\bearn', p.text[f.end:b.start]):
        return None
    if not _has(r'\b(?:more|need)\b', p.question):
        return None
    return _answer(goal.value-a.value*(1+f.value)-b.value,
                   'Goal minus the two related earnings and the earlier earnings')


def _mixed_dozen(p):
    if len(p.numbers) != 1:
        return None
    n = p.numbers[0]
    if n.value <= 1 or n.value.denominator == 1 or not re.match(r'\s+dozens?\b', p.text[n.end:]):
        return None
    if not _has(r'\b(?:many|total)\b', p.question):
        return None
    return _answer(n.value*12, 'Dozens x items per dozen')


def _occupied_yearly_income(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    f = fs[0]
    count, rent = [n for n in p.numbers if n not in fs]
    if not count.start < f.start < rent.start or rent.kind != 'money':
        return None
    if not re.match(r'\s+occupied\b', p.text[f.end:]) or not _has(r'\b(?:every|per|each) month\b', p.body):
        return None
    if not _has(r'\beach (?:resident|tenant|occupant)\b', p.text[f.end:rent.start]) or not _has(r'\byear\b', p.question):
        return None
    return _answer(count.value*f.value*rent.value*12, 'Occupied units x monthly rent x months in a year')


def _fractional_travel_time(p, fs):
    if len(fs) != 2 or len(p.numbers) != 4 or not _has(r'\bminutes?\b', p.question):
        return None
    rates = [n for n in p.numbers if n not in fs]
    if not all(n.start < fs[0].start and n.value > 0 for n in rates):
        return None
    rates_by_verb = {}
    for n in rates:
        before = re.search(r'\b(runs?|walks?|drives?|rides?|swims?) at\s*$', p.text[:n.start])
        unit = re.match(r'\s+(miles?|kilometers?|km) per hour\b', p.text[n.end:])
        if not before or not unit:
            return None
        rates_by_verb[before.group(1).rstrip('s')] = (n.value, _singular(unit.group(1)))
    if len(rates_by_verb) != 2:
        return None
    value = Fraction(0)
    seen = set()
    for f in fs:
        before = re.search(r'\b(runs?|walks?|drives?|rides?|swims?) for\s*$', p.text[:f.start])
        unit = re.match(r'\s+(?:a |an )?(miles?|kilometers?|km)\b', p.text[f.end:])
        if not before or not unit:
            return None
        key = before.group(1).rstrip('s')
        if key not in rates_by_verb or key in seen or rates_by_verb[key][1] != _singular(unit.group(1)):
            return None
        seen.add(key)
        value += f.value/rates_by_verb[key][0]*60
    return _answer(value, 'Add each distance / its matching speed, converted to minutes')


def _grouped_container_share(p, fs):
    if len(fs) != 1 or len(p.numbers) != 4:
        return None
    f = fs[0]
    groups, rate, capacity = [n for n in p.numbers if n not in fs]
    if not groups.start < rate.start < capacity.start < f.start or capacity.value <= 0:
        return None
    if not _has(r'\beach (?:produce|produces|make|makes|yields?)\s*$', p.text[groups.end:rate.start]):
        return None
    container = re.search(r'\beach ([a-z]+) (?:can )?(?:hold|holds|contain|contains)\s*$', p.text[rate.end:capacity.start])
    if not container or _singular(container.group(1)) not in _words(p.question):
        return None
    if _unit(p, rate) != _unit(p, capacity) or not _has(r'\bown\b', p.text[capacity.end:f.start]):
        return None
    value = groups.value*rate.value*(1-f.value)/capacity.value
    return _answer(Fraction(-(-value.numerator//value.denominator)),
                   'Production x share needing containers / capacity per container, rounded up')


def _people_time_consumption(p, fs):
    if len(fs) != 1 or len(p.numbers) != 4:
        return None
    f = fs[0]
    people, outward, back = [n for n in p.numbers if n not in fs]
    if not people.start < outward.start < back.start < f.start:
        return None
    if not re.match(r'\s+people (?:total|in all)\b', p.text[people.end:]):
        return None
    if not all(re.match(r'\s+hours?\b', p.text[n.end:]) for n in (outward, back)):
        return None
    if not _has(r'\b(?:every|each) hour each person\b', p.text[back.end:f.start]):
        return None
    if not _has(r'\btotal\b', p.question):
        return None
    return _answer(people.value*(outward.value+back.value)*f.value,
                   'People x combined travel hours x consumption per person per hour')


def _listed_comparison_sum(p, fs):
    if len(fs) != 1 or not 3 <= len(p.numbers) <= 5:
        return None
    f = fs[0]
    counts = [n for n in p.numbers if n not in fs]
    if not all(n.start < f.start for n in counts) or not _has(r'\b(?:total|combined|all the subjects)\b', p.question):
        return None
    if not re.match(r'\s+(?:times )?as many\b', p.text[f.end:]):
        return None
    labels = []
    for n in counts:
        tail = re.split(r'[,.;!?]|\band\b', p.text[n.end:])[0]
        m = re.match(r'\s+[a-z]+ (?:of|in) ([a-z]+(?: [a-z]+)?)', tail)
        if not m:
            return None
        labels.append(m.group(1).strip())
    reference = re.split(r'[.;!?]', p.text[f.end:])[0]
    matches = [i for i, label in enumerate(labels) if _has(r'\b'+re.escape(label)+r'\b', reference)]
    if len(matches) != 1:
        return None
    return _answer(sum((n.value for n in counts), Fraction(0))+counts[matches[0]].value*f.value,
                   'Add the listed quantities and the fraction of the explicitly referenced quantity')


def _unknown_last_expense(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    f = fs[0]
    opening, balance = [n for n in p.numbers if n not in fs]
    if not opening.start < f.start < balance.start or any(n.kind != 'money' for n in (opening, balance)):
        return None
    unknown = re.search(r'\bspent some money on ([a-z ]+?)\s+and\b', p.text[f.end:balance.start])
    if not unknown or not _words(unknown.group(1)) & _words(p.question):
        return None
    if not _has(r'\bleft\b', p.text[balance.end:len(p.body)]):
        return None
    return _answer(opening.value*(1-f.value)-balance.value,
                   'Balance after the known expense minus the final balance')


def _capacity_trips(p, fs):
    if len(fs) != 2 or not _has(r'\btotal\b', p.question):
        return None
    amounts = [n for n in p.numbers if n not in fs]
    if len(amounts) == 2:
        label = amounts[-1]
        if label.start < len(p.body) or label.value != len(fs) or not re.match(r'\s+trips?\b', p.text[label.end:]):
            return None
        amounts.pop()
    if len(amounts) != 1:
        return None
    total = amounts[0]
    if total.start > fs[0].start or not _has(r'\bcapacity of\s*$', p.text[:total.start]):
        return None
    if not all(re.match(r'\s+of (?:its|the|his|her) capacity\b', p.text[f.end:]) for f in fs):
        return None
    return _answer(total.value*sum((f.value for f in fs), Fraction(0)),
                   'Capacity x sum of the occupied shares on the separate trips')


def _future_shared_age(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3 or not _has(r'\b(?:now|currently)\b', p.question):
        return None
    f = fs[0]
    years, older = [n for n in p.numbers if n not in fs]
    if not years.start < f.start < older.start:
        return None
    if not _has(r'\bin\s*$', p.text[:years.start]) or not re.match(r'\s+years?\b', p.text[years.end:]):
        return None
    if not _has(r'\bwill be\s*$', p.text[years.end:f.start]) or not re.match(r"\s+of [a-z]+'s age\b", p.text[f.end:]):
        return None
    if not re.match(r'\s+years? old\b', p.text[older.end:]):
        return None
    return _answer((older.value+years.value)*f.value-years.value,
                   'Apply the ratio to the future age, then subtract the elapsed years')


def _work_remaining_time(p, fs):
    if len(fs) != 1 or len(p.numbers) != 4 or not _has(r'\bminutes?\b', p.question):
        return None
    f = fs[0]
    total, rate, done = [n for n in p.numbers if n not in fs]
    if not total.start < rate.start < f.start < done.start or rate.value <= 0:
        return None
    if not re.match(r'\s+(?:an? |of an? )hour\b', p.text[f.end:]) or not _has(r'\bin\s*$', p.text[rate.end:f.start]):
        return None
    if not (_unit(p, total) == _unit(p, rate) == _unit(p, done)):
        return None
    if not _has(r'\balready\b', p.text[f.end:done.start]) or not _has(r'\b(?:more|finish|remaining)\b', p.question):
        return None
    return _answer((total.value-done.value)*f.value*60/rate.value,
                   'Remaining work / work per interval x interval duration in minutes')


def _two_ends(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    f = fs[0]
    length, trim = [n for n in p.numbers if n not in fs]
    if not length.start < f.start < trim.start or not re.match(r'\s+that length\b', p.text[f.end:]):
        return None
    if not _has(r'\bon each end\b', p.text[trim.end:len(p.body)]) or not _has(r'\b(?:in all|total|altogether)\b', p.question):
        return None
    return _answer(length.value*(1+f.value)+trim.value*2,
                   'Original length plus proportional length plus the additions at both ends')


def _proportional_projection(p, fs):
    if len(fs) != 1 or len(p.numbers) != 4:
        return None
    f = fs[0]
    money, population, projected = [n for n in p.numbers if n not in fs]
    if not money.start < f.start < population.start < projected.start or money.kind != 'money':
        return None
    if population.value <= 0 or not _has(r'\battend', p.text[f.end:population.start]):
        return None
    if not _has(r'\b(?:would|if)\b', p.question) or not _has(r'\battend', p.text[projected.end:]):
        return None
    if _unit(p, population) != _unit(p, projected):
        return None
    return _answer(money.value/(population.value*f.value)*projected.value,
                   'Revenue per actual attendee x projected attendees')


def _fraction_and_other_part(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    f = fs[0]
    other, whole = [n for n in p.numbers if n not in fs]
    if not f.start < other.start < whole.start or not re.match(r'\s+of the total number of\b', p.text[f.end:]):
        return None
    if not _has(r'\b(?:has|contains|comprises)\s*$', p.text[other.end:whole.start]):
        return None
    if not _has(r'\b(?:total|remaining|other|rest)\b', p.question):
        return None
    # The query must select a third category, rather than either known one.
    known_labels = _words(re.split(r'[,.;!?]', p.text[other.end:])[0])
    ratio_label = _words(re.split(r'[.;!?]', p.text[:f.start])[-1])
    common = _words(p.text[whole.end:len(p.body)])
    if (known_labels | ratio_label)-common & (_words(p.question)-common):
        return None
    return _answer(whole.value*(1-f.value)-other.value,
                   'Whole minus its fractional category minus the other counted category')


def _event_comparisons(problem):
    """An indexed list of events/objects, each with a count or affine relation.

    Labels provide graph nodes, rather than being mistaken for quantities.
    Every non-label quantity must be an anchor, multiplier, offset or duration.
    """
    prepared = _prepare(problem)
    if prepared is None:
        return None
    text = prepared.text.lower()
    text = re.sub(r'\b(twice|thrice|double[ds]?)\b',
                  lambda m: '3 times' if m.group() == 'thrice' else '2 times', text)
    ordinals = ('first', 'second', 'third', 'fourth', 'fifth', 'sixth')
    for i, ordinal in enumerate(ordinals, 1):
        text = re.sub(r'\b'+str(i)+r'(?:st|nd|rd|th)\b', ordinal, text)
    weekday = r'monday|tuesday|wednesday|thursday|friday|saturday|sunday'
    month = r'january|february|march|april|may|june|july|august|september|october|november|december'
    head = (r'(?!(?:of|as|more|less|fewer|the|his|her|their|a|an|and|or|in|on|'
            r'two|three|four|five|six|seven|eight|nine|ten|half)\b)[a-z]+')
    label = (r'\b(?:'+weekday+'|'+month+r')\b|\b(?:'+ '|'.join(ordinals)+
             r') (?:fastest )?'+head+r'\b')
    labels = list(re.finditer(label, text))
    if len(labels) < 3:
        return None
    # All indexed objects must use the same kind of label. Bare day/ordinal
    # references are resolved only after that common kind is established.
    ordinal_labels = [m.group() for m in labels if m.group().split()[0] in ordinals]
    kinds = {s.split()[-1] for s in ordinal_labels}
    if len(kinds) > 1:
        return None
    kind = next(iter(kinds)) if kinds else ''
    if not kind:
        if all(re.fullmatch(weekday, m.group()) for m in labels):
            kind = 'day'
        elif all(re.fullmatch(month, m.group()) for m in labels):
            kind = 'month'
    if kind:
        text = re.sub(r'\bday (one|two|three|four|five|six)\b',
                      lambda m: ordinals[('one','two','three','four','five','six').index(m.group(1))]+' day', text)
        text = re.sub(r'\b(?:this|the first) '+re.escape(kind)+r'\b', 'first '+kind, text)
        text = re.sub(r'\b(?:the )?next '+re.escape(kind)+r'\b', 'second '+kind, text)
    labels = list(re.finditer(label, text))
    aliases = {}
    for m in labels:
        key = m.group().split()[0]
        aliases[m.group()] = 'event'+key
    for phrase in sorted(aliases, key=len, reverse=True):
        text = re.sub(r'\b'+re.escape(phrase)+r'\b', aliases[phrase], text)
    # Restore ordinal references whose noun was elided ("the second dog eats
    # twice as much as the first").
    for phrase, alias in aliases.items():
        first = phrase.split()[0]
        if first in ordinals:
            text = re.sub(r'\bthe '+first+r' one\b', alias, text)
    q = Problem.read(text)
    if q is None:
        return None
    names = sorted(set(aliases.values()))
    if not 2 <= len(names) <= 6:
        return None
    # The event grammar operates on like quantities; per-period measurements
    # can be retained when all quantities use the same common period.
    periods = set(re.findall(r'\b(?:per|a|each|every) (day|week|month|minute|hour)\b', q.body))
    if len(periods) > 1:
        return None
    t = _tokens(q)
    question_start = len(t)
    from ..problem import ASK
    asks = list(ASK.finditer(t))
    if not asks:
        return None
    question_start = asks[-1].start()
    body, query = t[:question_start], t[question_start:]
    clauses = re.split(r'[.;!?]|,?\s+(?:and|while|but)\s+(?=(?:the )?event)|\s+then\s+', body)
    edges, known, sums, used = [], {}, [], set()
    previous = None
    for clause in clauses:
        indices = [int(m.group(1)) for m in re.finditer(r'\bN(\d+)\b', clause)]
        mentions = _mentions(clause, names)
        if not indices:
            # An explicitly stated sum can define an additional event.
            if _has(r'\b(?:sum|combined)\b', clause) and len(mentions) == 3:
                sums.append((mentions[0], mentions[1:]))
            continue
        if not mentions:
            # A count of the listed objects is metadata, not another amount.
            if len(indices) == 1:
                i = indices[0]
                n = q.numbers[i]
                if n.value == len(names) and re.match(r'\s+'+re.escape(kind)+r's\b', q.text[n.end:]):
                    used.add(i)
                    continue
            if not (len(indices) == 1 and not known and not edges and 'eventfirst' in names and
                    _unit(q, q.numbers[indices[0]]) in ('inch','foot','mile','meter','cup','page')):
                return None
            mentions = ['eventfirst']
        subject = mentions[0]
        # A proper fraction after an explicit rise/fall is a proportional
        # change to the previous event, not a new literal event anchor.
        changes = []
        for i in indices:
            if not 0 < q.numbers[i].value < 1:
                continue
            change = re.search(r'\b(?:(?:went|goes?) (down|up)|'
                               r'(decreased|increased)) by N'+str(i)+r'\b',clause)
            if change:
                changes.append((i, -1 if (change.group(1) == 'down' or
                                          change.group(2) == 'decreased') else 1))
        if changes:
            if len(changes) != 1 or len(indices) != 1 or not previous or previous == subject:
                return None
            i,sign = changes[0]
            edges.append((subject,previous,1+sign*q.numbers[i].value,Fraction(0)))
            used.add(i)
            previous = subject
            continue
        factors = [i for i in indices if _has(r'\bN'+str(i)+r'\s+(?:times\s+)?(?:as (?:many|much|long|far)|(?:of )?the (?:number|amount|height|age|length)|the [a-z]+ (?:he|she|they)|that (?:many|number|amount)|of\b)', clause)]
        if factors:
            if len(factors) != 1:
                return None
            i = factors[0]
            pos = re.search(r'\bN'+str(i)+r'\b', clause)
            subjects = _mentions(clause[:pos.start()], names)
            if subjects:
                subject = subjects[0]
            references = _mentions(clause[pos.end():], names)
            reference = references[0] if references else previous
            if reference is None or reference == subject:
                return None
            delta = Fraction(0)
            extra = [j for j in indices if j != i]
            if extra:
                if len(extra) != 1:
                    return None
                j = extra[0]
                adjustment = re.search(r'\bN'+str(j)+r'\s+(?:[a-z]+\s+){0,2}?(more|less|fewer|extra)\b', clause)
                if not adjustment:
                    return None
                delta = q.numbers[j].value*(-1 if adjustment.group(1) in ('less','fewer') else 1)
            edges.append((subject, reference, q.numbers[i].value, delta))
        else:
            if len(indices) != 1:
                return None
            i = indices[0]
            adjustment = re.search(r'\bN'+str(i)+r'\s+(?:[a-z]+\s+){0,2}?(more|less|fewer|older|younger|taller|shorter)\b', clause)
            if adjustment:
                references = _mentions(clause[adjustment.end():], names)
                reference = references[0] if references else previous
                if reference is None or reference == subject:
                    return None
                sign = -1 if adjustment.group(1) in ('less','fewer','younger','shorter') else 1
                edges.append((subject, reference, Fraction(1), sign*q.numbers[i].value))
            else:
                if subject in known:
                    return None
                known[subject] = q.numbers[i].value
        used.update(indices)
        previous = subject
    # Only exact event-count labels may remain in a total query.
    query_group = False
    for i, n in enumerate(q.numbers):
        if i in used:
            continue
        if n.start < len(q.body) or n.value != len(names) or not re.match(r'\s+(?:'+re.escape(kind)+r's|of them)\b', q.text[n.end:]):
            return None
        query_group = True
    if not edges:
        return None
    values = dict(known)
    for _ in names:
        for left, right, scale, offset in edges:
            if right in values:
                value = values[right]*scale+offset
                if left in values and values[left] != value:
                    return None
                values[left] = value
            elif left in values and scale:
                values[right] = (values[left]-offset)/scale
        for left, terms in sums:
            if all(term in values for term in terms):
                values[left] = sum((values[term] for term in terms), Fraction(0))
    if set(values) != set(names) or any(v < 0 for v in values.values()):
        return None
    asked = list(dict.fromkeys(_mentions(query, names)))
    cumulative_growth = _has(r'how tall', query) and _has(r'\b(?:grew|grown|growth)\b', body)
    if _has(r'\b(?:total|altogether|combined|in all|by the end|by [a-z]+)\b', query) or cumulative_growth or query_group:
        result = sum((values[name] for name in (asked if len(asked) > 1 else names)), Fraction(0))
    elif len(asked) == 1:
        result = values[asked[0]]
    else:
        return None
    return _answer(result, 'Resolve each indexed amount from its anchor and explicit comparisons')


def _whole_from_other_categories(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    f = fs[0]
    amounts = [n for n in p.numbers if n not in fs]
    if not all(n.start < f.start for n in amounts) or not _has(r'\b(?:total|altogether|in all|how many)\b', p.question):
        return None
    if not re.match(r'\s+of all (?:the )?([a-z]+)', p.text[f.end:]):
        return None
    labels, bases = [], []
    for n in amounts:
        m = re.match(r'\s+of the ([a-z]+)[^.;]*?\bin ([a-z]+) ([a-z]+)', p.text[n.end:])
        if not m:
            return None
        bases.append(m.group(1))
        labels.append((m.group(2), m.group(3)))
    if bases[0] != bases[1] or labels[0][1] != labels[1][1] or labels[0][0] == labels[1][0]:
        return None
    if not _has(r'\b'+re.escape(bases[0])+r'\b', p.question):
        return None
    return _answer(sum((n.value for n in amounts), Fraction(0))/(1-f.value),
                   'Combined counted categories / their complementary share of the whole')


def _group_local_loss(p, fs):
    if len(fs) != 1 or len(p.numbers) != 4:
        return None
    f = fs[0]
    total, groups, damaged = [n for n in p.numbers if n not in fs]
    if not total.start < groups.start < damaged.start < f.start or groups.value <= 0:
        return None
    if not _has(r'\binto\s*$', p.text[total.end:groups.start]) or not _has(r'\bequally\b', p.text[groups.end:damaged.start]):
        return None
    if not re.match(r'\s+of the '+re.escape(_unit(p, groups))+r's\b', p.text[damaged.end:]):
        return None
    if not _has(r'\b(?:fall|falls|lost|spilled|spill|leaks?)\b', p.text[f.end:len(p.body)]) or not _has(r'\b(?:remain|left)\b', p.question):
        return None
    return _answer(total.value-total.value/groups.value*damaged.value*f.value,
                   'Total stock minus the lost fraction of the affected equal groups')


def _changed_work_time(p, fs):
    if len(fs) != 1 or len(p.numbers) != 4 or not p.question.startswith('how long'):
        return None
    f = fs[0]
    time, work, added = [n for n in p.numbers if n not in fs]
    if not time.start < work.start < f.start < added.start or work.value <= 0:
        return None
    if _unit(p, time) not in ('hour','minute') or _unit(p, work) != _unit(p, added):
        return None
    if not _has(r'\b(?:took|takes)\b', p.text[:time.start]) or not _has(r'\b(?:lost|away|removed)\b', p.text[work.end:f.start]):
        return None
    if not _has(r'\b(?:adding|added|adds?)\b', p.text[f.end:added.start]):
        return None
    return _answer((work.value*(1-f.value)+added.value)*time.value/work.value,
                   'Revised amount of work x original time per unit of work')


def _pace_improvement(p, fs):
    if len(fs) != 1 or len(p.numbers) not in (4,5):
        return None
    f = fs[0]
    amounts = [n for n in p.numbers if n not in fs]
    if len(amounts) == 4:
        label = amounts[-1]
        if label.start < len(p.body) or label.value != 1 or not re.match(r'\s+miles?\b', p.text[label.end:]):
            return None
        amounts.pop()
    laps, recent, prior = amounts
    if not laps.start < f.start < recent.start < prior.start or laps.value <= 0:
        return None
    if not re.match(r'\s+times\b', p.text[laps.end:]) or not re.match(r'\s+of a mile\b', p.text[f.end:]):
        return None
    if not all(re.match(r'\s+minutes?\b', p.text[n.end:]) for n in (recent,prior)):
        return None
    if not _has(r'\b(?:faster|difference)\b', p.question) or not _has(r'\bmile\b', p.question):
        return None
    return _answer(abs(prior.value-recent.value)/(laps.value*f.value),
                   'Difference in finishing times / total race distance')


def _subset_ratio(p, fs):
    if len(fs) != 1:
        return None
    text = re.sub(r'\btwice\b', '2 times', p.text)
    q = Problem.read(text)
    if q is None:
        return None
    t = _tokens(q)
    relation = re.search(r'number of ([a-z]+)[^.;]*?N(\d+) times (?:the )?number of ([a-z]+)', t)
    if not relation or len(q.numbers) != 3:
        return None
    ri = int(relation.group(2))
    factor = q.numbers[ri].value
    fractions = [n for n in q.numbers if '/' in n.raw and 0<n.value<1]
    if len(fractions) != 1:
        return None
    f = fractions[0]
    count = next(n for i,n in enumerate(q.numbers) if i != ri and n != f)
    if not f.start < count.start < q.numbers[ri].start or factor <= 0:
        return None
    a, b = relation.group(1), relation.group(3)
    targets = [word for word in (a,b) if _has(r'\b'+re.escape(word)+r'\b', q.question)]
    if len(targets) != 1 or not _has(r'\b(?:attend|attending|going)\b', q.text[f.end:count.start]):
        return None
    return _answer(count.value*f.value/(1+factor)*(factor if targets[0]==a else 1),
                   'Selected population divided according to the stated two-category ratio')


def _remaining_categories(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    f = fs[0]
    if not re.match(r'\s+that (?:many|number|amount)\b', p.text[f.end:]):
        return None
    part, total = [n for n in p.numbers if n not in fs]
    if not part.start < f.start < total.start or not _has(r'\b(?:other|rest|remaining)\b', p.question):
        return None
    if not _has(r'\b(?:in total|total of|altogether)\b', p.text[f.end:total.start]):
        return None
    return _answer(total.value-part.value*(1+f.value), 'Total minus the counted category and its related category')


def _time_shares(p, fs):
    if not fs or not _has(r'\b(?:minute|net calorie intake)', p.question):
        return None
    t = _tokens(p)
    # Each term must be an explicit fraction of an hour. A repeated frequency
    # belongs to that term, rather than multiplying the entire daily total.
    terms, used = [], set()
    for f in fs:
        i = p.numbers.index(f)
        match = re.search(r'\bN'+str(i)+r'\s+(?:of )?an? hour\b([^.;]*)', t)
        if not match:
            return None
        repeat = re.search(r'\b(twice|thrice|N\d+ times) (?:a|per|each) day\b', match.group(1))
        factor = Fraction(1)
        if repeat:
            if repeat.group(1).startswith('N'):
                j = int(re.search(r'\d+', repeat.group(1)).group())
                factor = p.numbers[j].value
                used.add(j)
            else:
                factor = Fraction(2 if repeat.group(1) == 'twice' else 3)
        terms.append(f.value*60*factor)
        used.add(i)
    amounts = [(i, n) for i, n in enumerate(p.numbers) if i not in used]
    if not amounts and _has(r'\bminutes?\b', p.question):
        return _answer(sum(terms, Fraction(0)), 'Add the daily time spent on each activity, in minutes')
    if len(amounts) == 2 and len(terms) == 1 and _has(r'\bnet calorie intake\b', p.question):
        (_, initial), (_, rate) = amounts
        if not re.match(r'\s+calories?\b', p.text[initial.end:]) or not re.match(r'\s+calories?[^.;]*\bper minute\b', p.text[rate.end:]):
            return None
        return _answer(initial.value-rate.value*terms[0], 'Calories supplied minus minutes of exercise x calories used per minute')
    return None


def solve(problem):
    if any(n.kind == 'percent' for n in problem.numbers):
        return None
    if not (has_fraction(problem.text) or _has(r'\b(?:twice|thrice|double[ds]?)\b', problem.text.lower())):
        return None
    p = _prepare(problem)
    if p is None:
        return None
    # Bare ordinal words in an indexed event are labels, not shares.
    p.numbers = [n for n in p.numbers if not (n.raw in ('third', 'fourth') and
                 _has(r'\b(?:final|last|the)\s*$', p.text[:n.start]) and
                 re.match(r'\s+[a-z]+\b', p.text[n.end:]))]
    fs = [n for n in p.numbers if '/' in n.raw and 0 < n.value < 1]
    if not fs:
        return _mixed_dozen(p) or _event_comparisons(problem)
    for reader in (_stock, _repeated_reduction, _depletion_time, _weekly_pay_share,
                   _population_product, _capacity_share, _area_shares,
                   _successive_transfers, _relative_amount,
                   _remaining_categories, _time_shares, _nested_remainder,
                   _relative_earning_time, _grouped_remainder, _combined_pair,
                   _fixed_money_allocations, _split_recipients, _saving_time,
                   _exam_score, _fractional_increase, _inverse_disjoint,
                   _earnings_gap, _category_graph, _allowance_savings,
                   _related_price_purchase, _proportional_collection_sale,
                   _labelled_parts, _gift_then_output, _occupied_yearly_income,
                   _fractional_travel_time, _grouped_container_share,
                   _people_time_consumption, _listed_comparison_sum,
                   _unknown_last_expense, _capacity_trips, _future_shared_age,
                   _work_remaining_time, _two_ends, _proportional_projection,
                   _fraction_and_other_part, _whole_from_other_categories,
                   _group_local_loss, _changed_work_time, _pace_improvement,
                   _subset_ratio):
        result = reader(p, fs)
        if result is not None:
            return result
    return _named_relations(problem, p) or _event_comparisons(problem)
