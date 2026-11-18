"""Fraction shares, remaining stocks, and explicit proportional comparisons.

The readers account for all quantities and distinguish a share of the original
whole from a share of what remains. Unsupported relationships are left alone.
"""
import re
from dataclasses import replace
from fractions import Fraction

from ..numbers import read_numbers, format_number, parse_number
from ..problem import Problem, ASK
from .counting_and_totals_r00_a1 import _sentence, _singular
from .comparisons_r01_a2 import _comparisons
from .percentages_r02_a3 import _labels, _opposite


def _has(pattern, text):
    return re.search(pattern, text) is not None


def _answer(value, explanation):
    if value < 0:
        return None
    return value, explanation + ' = ' + format_number(value) + '.'


_DENOMINATORS = {'half': 2, 'halves': 2, 'third': 3, 'thirds': 3,
                 'quarter': 4, 'quarters': 4, 'fourth': 4, 'fourths': 4,
                 'fifth': 5, 'fifths': 5, 'sixth': 6, 'sixths': 6,
                 'seventh': 7, 'sevenths': 7, 'eighth': 8, 'eighths': 8,
                 'ninth': 9, 'ninths': 9, 'tenth': 10, 'tenths': 10}
_NUMERATOR = r'(?:a|one|two|three|four|five|six|seven|eight|nine|ten|\d+)'
_WORD_FRACTION = re.compile(r'\b(' + _NUMERATOR + r')[ -]+(' +
                            '|'.join(sorted(_DENOMINATORS, key=len, reverse=True)) + r')\b')


def _prepare(p):
    text = p.text
    def fraction(m):
        numerator = Fraction(1) if m.group(1).lower() == 'a' else parse_number(m.group(1))
        return str(numerator.numerator) + '/' + str(_DENOMINATORS[m.group(2).lower()])
    text = _WORD_FRACTION.sub(fraction, text.lower())
    text = re.sub(r'\bhalf\b', '1/2', text)
    text = re.sub(r'\bquarter(?=[ -]+(?:hour|of|the)\b)', '1/4', text)
    text = re.sub(r'(\d+/\d+)(?:st|nd|rd|th)\b', r'\1', text)
    # A mixed multiplier is one quantity, even with an explicit "and".
    text = re.sub(r'\b(\d+)\s+and\s+(\d+/\d+)\b', r'\1 \2', text)
    asks = list(ASK.finditer(text))
    if not asks:
        return None
    at = asks[-1].start()
    ns = []
    for n in read_numbers(text):
        before, after = text[:n.start], text[n.end:]
        # An ordinal is an event label; the shared reader also excludes 3rd.
        if n.raw in ('third', 'quarter', 'fourth') and _has(r'\bthe\s*$', before):
            continue
        if n.value == 1 and _has(r'^\s+(?:day|hour|week|month|year)\b', after) and (
                not before.strip() or _has(r'\b(?:in|per|each)\s*$', before)):
            continue
        # A repeated known amount in an if-clause of the question is a reference.
        if n.start >= at and n.value == 1 and _has(r'^\s+of\b', after):
            continue
        if n.start >= at and any(x.value == n.value and
                re.match(r'\s+([a-z]+)', text[x.end:]) and
                re.match(r'\s+([a-z]+)', after) and
                re.match(r'\s+([a-z]+)', text[x.end:]).group(1) ==
                re.match(r'\s+([a-z]+)', after).group(1) for x in ns):
            continue
        if n.start >= at and _has(r'\b(?:remaining|those|these)\s*$', before) and any(
                x.value == n.value and text[x.end:x.end+18] == text[n.end:n.end+18] for x in ns):
            continue
        ns.append(n)
    prepared = Problem(text, text[:at], text[at:], ns)
    from .comparisons_r01_a2 import _names
    prepared.entities = _names(p.text)
    return prepared


def _ratios(p):
    return [n for n in p.numbers if '/' in n.raw and 0 < n.value < 1]


_STOP = set(('a an the of in at to for on with from as by and or but if that those '
             'these them their his her its is are was were be been has have had '
             'do does did will would can could it he she they there each every '
             'total number amount how many much which all only then than now '
             'also some original initially first left remaining rest altogether '
             'combined together entire what more less still came come went go').split())
_VERB_WORDS = {'ate': 'eat', 'eaten': 'eat', 'eats': 'eat', 'spent': 'spend',
               'spends': 'spend', 'gave': 'give', 'given': 'give', 'gives': 'give',
               'sold': 'sell', 'sells': 'sell', 'used': 'use', 'uses': 'use',
               'lost': 'lose', 'loses': 'lose', 'kept': 'keep', 'keeps': 'keep',
               'read': 'read', 'reads': 'read', 'saved': 'save', 'saves': 'save',
               'took': 'take', 'takes': 'take', 'taken': 'take'}


def _words(text):
    return {_VERB_WORDS.get(w, _singular(w)) for w in re.findall(r'[a-z]+', text)
            if w not in _STOP}


def _label(p, rate):
    text = p.text
    tail = re.split(r'[.;!?]|,(?!\d)|\s+(?:and|while|but)\b', text[rate.end:])[0]
    predicate = re.search(r'\b(?:are|is|were|was|have|has|wear|play|bear)\s+(.+)', tail)
    if predicate:
        return predicate.group(1)
    before = re.split(r'[.;!?]|\band\b', text[:rate.start])[-1]
    verb = re.search(r'\b(eats?|ate|spends?|spent|gave|gives?|sells?|sold|uses?|used|'
                     r'keeps?|kept|saves?|saved|loses?|lost|reads?|completed|finished)\b[^.;]*$', before)
    if verb:
        return verb.group(1) + ' ' + re.sub(r'^\s+of\b[^,;]*', '', tail)
    return _labels(text, rate)


def _choice(label, q, body):
    if _has(r"\b(?:not|don't|doesn't|aren't|didn't)\b", q):
        positive = re.sub(r"\b(?:not|don't|doesn't|aren't|didn't)\b", '', q)
        if _opposite(label, positive):
            return 1
        if _words(label) and _words(label) <= _words(positive):
            return -1
        return 0
    if _opposite(label, q):
        return -1
    rest = re.search(r'\b(?:the rest|the remainder|remaining\s+\w+)\s+([^.;!?]+)', body)
    if rest and (_words(rest.group(1)) - _words(label)) & _words(q):
        if _has(r'\b(?:equal|equally|split|divided)\b', rest.group(1)):
            return 0
        return -1
    if _words(label) & _words(q):
        return 1
    return 0


def _fraction_ledger(p, rates):
    """Evaluate an affine stock, or invert it from a known final remainder."""
    q, text, ns = p.question, p.text, p.numbers
    original = _has(r'\b(?:at first|originally|original|initially|start with|begin with|beginning|win)\b', q)
    remainder = _has(r'\b(?:left|remaining|remain|rest|have now|have in the end|at the end)\b', q)
    if not (original or remainder) or not rates:
        return None
    if _has(r'\b(?:as many|as much|times|twice|per|each|every|age|older|younger)\b', text):
        return None
    amounts = [n for n in ns if n not in rates]
    if not amounts or len(amounts) > 4:
        return None
    from .rates_and_unit_rates_r01_a4 import _unit
    units = {_unit(text, n) for n in amounts}
    units.discard('')
    if len(units) > 1:
        return None
    # Every proportional change must describe consuming/removing a share.
    for r in rates:
        clause = _sentence(text, r.start, r.end)
        before = text[max(0, r.start-70):r.start]
        after = text[r.end:]
        if not (_has(r'\b(?:spent|spends?|ate|eats?|used|uses?|lost|loses?|donated|donates?|skipped|gave|gives?|'
                     r'sold|sells?|removed|takes?|took|steal|stole|eaten|consumed)\b', before)
                or _has(r'^\s+of\b[^.;]*\b(?:eaten|used|sold|removed|given away)\b', after)):
            return None
        if not (_has(r'^\s+(?:of|the|his|her|their|its)\b', after) or
                _has(r'\b(?:spent|ate|used|lost|gave|sold)\s*$', before)):
            return None
        if _has(r'\b(?:more|less|than|added)\b', clause):
            return None
    # Stock = a * initial + b. Literal deltas are tracked independently.
    a, b = Fraction(1), Fraction(0)
    start_value = None
    end_value = None
    changes = 0
    for n in ns:
        before = re.split(r'[.;!?]|,(?!\d)|\band\b', text[:n.start])[-1]
        after = text[n.end:]
        if n in rates:
            # Explicit remaining shares compound; a repeated "of it" refers
            # to the originally stated whole rather than a new subtotal.
            recent = text[max(0, n.start-35):n.start] + after.split('.')[0]
            if changes == 0 or _has(r'\b(?:remaining|remainder|rest|what (?:was|is) left)\b', recent):
                a, b = a*(1-n.value), b*(1-n.value)
            else:
                a -= n.value
            changes += 1
            continue
        is_end = _has(r'\b(?:left|remaining)\b', re.split(r'[.;!?]|,(?!\d)', after)[0])
        is_end = is_end or _has(r'\b(?:now|still)\b', before)
        if original and is_end and n.start > rates[-1].end:
            if end_value is not None:
                return None
            end_value = n.value
            continue
        removal = _has(r'\b(?:spent|spends?|ate|eats?|used|uses?|lost|loses?|donated|donates?|skipped|gave|gives?|'
                       r'sold|sells?|removed|takes?|took|steal|stole)\b[^.;]*$', before)
        addition = _has(r'\b(?:added|adds?|bought|buys?|received|receives?|got|gets?|'
                       r'returned|returns?|put in|puts in|spit)\b[^.;]*$', before)
        recipient = re.search(r'\b([a-z]+) (?:gave|gives) (him|her|them) (?:another |an additional )?$', before)
        initial_owner = re.search(r'\b([a-z]+) (?:had|has|collected|bought)\b', text[:ns[0].start])
        if recipient and initial_owner and recipient.group(1) != initial_owner.group(1):
            removal, addition = False, True
        if _has(r'^\s+missing\b', after):
            removal, addition = True, False
        if start_value is None and not original and n.start < rates[0].start and not changes:
            if not _has(r'\b(?:has|have|had|collected|bought|buys?|contains?|holds?|there are|there were|starts?|started)\b', before):
                return None
            start_value = n.value
        elif original and not removal and not addition and n.kind == 'money' and _has(
                r'\b(?:spent|spends)\b', _sentence(text, n.start, n.end)):
            b -= n.value
            changes += 1
        elif removal != addition:
            b += (-1 if removal else 1)*n.value
            changes += 1
        else:
            return None
    if a <= 0:
        return None
    if original:
        if end_value is None or start_value is not None:
            return None
        return _answer((end_value-b)/a, 'Recover the whole from its remaining share')
    if start_value is None:
        return None
    return _answer(a*start_value+b, 'Apply the stated removals and returns to the stock')


def _share(p, rates):
    """One counted whole/part and one or two explicitly described shares."""
    amounts = [n for n in p.numbers if n not in rates]
    if len(amounts) != 1 or not 1 <= len(rates) <= 2:
        return None
    text, q = p.text, p.question
    if any(re.match(r'\s+(?:more|less|fewer)\b', text[r.end:]) for r in rates):
        return None
    if (_has(r'\b(?:together|combined)\b', text[:amounts[0].start]) and
            _has(r'\b(?:distance|amount|number) that [a-z]+ (?:ran|read|has|had|made)\b', p.body)):
        return None
    if _has(r'\b(?:times|twice|thrice|double|triple|as many|as much|age|older|younger|more than|less than|per|each)\b', text):
        return None
    amount = amounts[0]
    if any(_has(r'^\s+of\b[^.;!?]*\b(?:that|which) [a-z]+ (?:picked|collected|has|had|bought|made)\b',
                text[r.end:]) for r in rates):
        return None
    labels = [_label(p, r) for r in rates]
    choices = [_choice(label, q, p.body) for label in labels]
    known_after = re.split(r'[.;!?]|,(?!\d)|\band\b', text[amount.end:])[0]
    known_before = re.split(r'[.;!?]|,(?!\d)|\band\b', text[:amount.start])[-1]
    known_words = _words(known_after + ' ' + known_before)
    known = [i for i, label in enumerate(labels) if _words(label) & known_words]
    # A nested second share has a different denominator, so it is handled
    # explicitly rather than treated as another share of the original whole.
    nested = len(rates) == 2 and _has(
        r'^\s+of (?:the remaining|the rest|those|these|them)\b',
        text[rates[1].end:])
    if nested:
        return None
    if len(rates) == 2:
        if amount.start < rates[0].start and not known and all(c == -1 for c in choices):
            return _answer(amount.value*(1-sum((r.value for r in rates), Fraction(0))),
                           'Whole minus the stated disjoint shares')
        # Recover a common whole from one labelled share, then select the other.
        if len(known) != 1:
            return None
        target = [i for i, c in enumerate(choices) if c == 1]
        whole = amount.value/rates[known[0]].value
        if not target and all(c == -1 for c in choices) and _has(r'\b(?:the rest|the remainder)\b', p.body):
            return _answer(whole*(1-sum((r.value for r in rates), Fraction(0))),
                           'Recover the whole and remove the other stated shares')
        if len(target) != 1 or target[0] == known[0]:
            return None
        return _answer(whole*rates[target[0]].value, 'Known part / its share x requested share')
    rate, label, choice = rates[0], labels[0], choices[0]
    if not choice and not _has(r'\b(?:total|altogether|original|at first|start|entire|all)\b', q):
        return None
    # A counted category (rather than a total) fixes the inverse direction.
    if amount.start > rate.end and known:
        if _has(r'\b(?:total|altogether|in all)\b', known_after + ' ' + known_before):
            return None
        whole = amount.value/rate.value
        return _answer(whole if not choice else whole*(1-rate.value) if choice == -1 else amount.value,
                       'Recover the whole from the counted share')
    if amount.start > rate.end and _opposite(label, known_after + ' ' + known_before):
        whole = amount.value/(1-rate.value)
        return _answer(whole*rate.value if choice == 1 else whole if not choice else amount.value,
                       'Recover the whole from the complementary share')
    if not choice:
        return None
    # Only an explicit of-relation or a predicate can identify a population share.
    tail = text[rate.end:]
    if not _has(r'^\s+(?:of|the|his|her|their|are|were|is|was)\b|^\s+[a-z]+\s+(?:are|have|is|has)\b', tail):
        return None
    return _answer(amount.value*(rate.value if choice == 1 else 1-rate.value),
                   'Whole x requested fraction')


def _split_share(p, rates):
    if len(rates) != 1 or len(p.numbers) != 3:
        return None
    r = rates[0]
    amounts = [n for n in p.numbers if n != r]
    if not _has(r'\b(?:each|per)\b', p.question):
        return None
    counts = [n for n in amounts if _has(r'\b(?:into|among|between)\s+(?:the )?(?:remaining )?$|\b(?:into|among|between)\s*$', p.text[:n.start])
              and (_has(r'^\s+equal\b', p.text[n.end:]) or
                   _has(r'\b(?:evenly|equally)\b', _sentence(p.text, n.start, n.end)))]
    if len(counts) != 1 or counts[0].value <= 0:
        return None
    base = next(n for n in amounts if n != counts[0])
    if base.start > r.start or not _has(r'^\s+of\b', p.text[r.end:]):
        return None
    choice = _choice(_label(p, r), p.question, p.body)
    if not choice and _has(r'\bremaining\b', p.question) and _has(r'\bthe rest\b', p.body):
        choice = -1
    if not choice:
        return None
    return _answer(base.value*(r.value if choice == 1 else 1-r.value)/counts[0].value,
                   'Whole x selected share / equal groups')


def _summed_stock_share(p, rates):
    """A common stock listed as several counts, then one share is removed."""
    if len(rates) != 1 or not 3 <= len(p.numbers) <= 5:
        return None
    r = rates[0]
    amounts = [n for n in p.numbers if n != r]
    if any(n.start > r.start for n in amounts) or len(p.entities) > 1:
        return None
    if _has(r'\b(?:each|every|per|times|total|more|less|fewer)\b', p.text[:r.start]):
        return None
    if not _has(r'\b(?:sold|sells?|shares?|gave|gives?|ate|eats?|used|uses?)\s+(?:only )?$', p.text[:r.start]):
        return None
    from .rates_and_unit_rates_r01_a4 import _unit
    units = []
    for n in amounts:
        measure = re.match(r'\s+(kg|grams?|pounds?|liters?|litres?|ounces?|g|ml)\b', p.text[n.end:])
        units.append(_singular(measure.group(1)) if measure else _unit(p.text, n))
    if not units[0] or len(set(units)) != 1:
        return None
    choice = _choice(_label(p, r), p.question, p.body)
    if not choice:
        return None
    return _answer(sum((n.value for n in amounts), Fraction(0))*(r.value if choice == 1 else 1-r.value),
                   'Combined stock x requested share')


def _related_price(p, rates):
    """One known price and a second price explicitly proportional to it."""
    if len(rates) != 1 or len(p.numbers) != 2:
        return None
    r = rates[0]
    amount = next(n for n in p.numbers if n != r)
    if amount.kind != 'money' or amount.start > r.start:
        return None
    if not re.match(r'\s+the (?:price|cost) of\b', p.text[r.end:]):
        return None
    if not _has(r'\b(?:total|together|altogether|both)\b', p.question):
        return None
    if not _has(r'\b(?:paid|cost|costs|price)\b', p.text[:amount.start]):
        return None
    return _answer(amount.value*(1+r.value), 'Known price plus the proportional second price')


def _grouped_inverse_share(p, rates):
    """A counted share used in equal groups; recover the original whole."""
    if len(rates) != 1 or len(p.numbers) != 3:
        return None
    if not _has(r'\b(?:originally|at first|original)\b', p.question):
        return None
    r = rates[0]
    if not _has(r'\b(?:use|uses?|used)\s*$', p.text[:r.start]):
        return None
    amounts = [n for n in p.numbers if n != r]
    count, rate = amounts
    if not r.start < count.start < rate.start:
        return None
    noun = re.match(r'\s+([a-z]+(?: [a-z]+)?)', p.text[count.end:])
    if not noun:
        return None
    before = _sentence(p.text, rate.start, rate.end).split(rate.raw)[0]
    each = re.search(r'\beach ([a-z ]+?) (?:uses?|needs?|requires?|contains?)\s*$', before)
    if not each or not _words(each.group(1)) & _words(noun.group(1)):
        return None
    return _answer(count.value*rate.value/r.value, 'Counted groups x amount per group / used share')


def _interval_schedule(p, rates):
    """A fractional interval, daily operating time, and a count of days."""
    if len(rates) != 1 or len(p.numbers) != 3:
        return None
    r = rates[0]
    if not _has(r'\bevery\s*$', p.text[:r.start]):
        return None
    interval = re.match(r'[- ]+(hour|minute)\b', p.text[r.end:])
    if not interval:
        return None
    amounts = [n for n in p.numbers if n != r]
    operating, days = amounts
    per_day = re.match(r'\s+(hours?|minutes?) (?:a|per|each|every) day\b', p.text[operating.end:])
    if not per_day or not _has(r'^\s+days?\b', p.text[days.end:]):
        return None
    if not _has(r'^how many\b', p.question):
        return None
    conversion = Fraction(1)
    if interval.group(1) == 'minute' and per_day.group(1).startswith('hour'):
        conversion = Fraction(60)
    elif interval.group(1) == 'hour' and per_day.group(1).startswith('minute'):
        conversion = Fraction(1, 60)
    return _answer(operating.value*days.value*conversion/r.value,
                   'Operating time / interval x days')


def _fractional_stocks(p, rates):
    """Add measured fractional stocks, then divide by a matching daily use."""
    if len(p.numbers) != 3 or len(rates) != 3:
        return None
    if not _has(r'^how many days\b', p.question):
        return None
    units = [re.match(r'\s+of (?:a|the) ([a-z]+)\b', p.text[n.end:]) for n in rates]
    if not all(units) or len({m.group(1) for m in units}) != 1:
        return None
    if not _has(r'\b(?:uses?|consumes?|needs?)\s*$', p.text[:rates[-1].start]):
        return None
    if not _has(r'\bper day\b', p.text[rates[-1].end:]):
        return None
    if not _has(r'\b(?:has|have|had)\b', p.text[:rates[0].start]):
        return None
    return _answer((rates[0].value+rates[1].value)/rates[2].value,
                   'Combined stocks / daily use')


def _transfer_explicit_share(p, rates):
    """An explicitly counted fractional gift and another counted stock/gift."""
    if len(rates) != 1 or len(p.numbers) != 3:
        return None
    r = rates[0]
    amounts = [n for n in p.numbers if n != r]
    before_count = [n for n in amounts if n.start < r.start]
    after_count = [n for n in amounts if n.start > r.end]
    if len(before_count) != 1 or len(after_count) != 1:
        return None
    other, base = before_count[0], after_count[0]
    if not re.fullmatch(r'\s+of (?:the |his |her |their )?', p.text[r.end:base.start]):
        return None
    if not _has(r'\b(?:give|gave|gives)\b', p.body):
        return None
    # Owner names are grammatical references, never object-specific vocabulary.
    from .comparisons_r01_a2 import _mentions
    names = p.entities
    asked = [name for name in names if _has(r'\b'+re.escape(name)+r'\b', p.question)]
    if len(asked) != 1:
        return None
    mentioned = _mentions(p.text[:r.start], names)
    if not mentioned:
        return None
    giver = mentioned[-1]
    if giver == asked[0]:
        if not _has(r'\b(?:saved|gives?|gave)\b', p.text[:r.start]):
            return None
        value = base.value*(1-r.value)+other.value
    else:
        stock_clause = p.text[:other.start]
        if not _has(r'\b'+re.escape(asked[0])+r' (?:has|had|have)\s*$', stock_clause):
            return None
        if not _has(r'\b(?:gave|gives?) (?:them )?to (?:her|him|'+re.escape(asked[0])+r')\b', p.text[base.end:]):
            return None
        value = other.value+base.value*r.value
    return _answer(value, 'Retained stock plus the incoming gift')


def _fraction_age_shift(p, rates):
    """One explicit age ratio and an equal passage of years for both owners."""
    if len(rates) != 1 or len(p.numbers) != 3:
        return None
    r = rates[0]
    left = re.search(r'\b([a-z]+) (?:is|will be)\s*$', p.text[:r.start])
    right = re.match(r"\s+(?:the age of ([a-z]+)|([a-z]+)'s age)\b", p.text[r.end:])
    if not left or not right:
        return None
    right_name = right.group(1) or right.group(2)
    amounts = [n for n in p.numbers if n != r]
    durations = [n for n in amounts if _has(r'\bin\s*$', p.text[:n.start]) and
                 _has(r'^\s+years?\b', p.text[n.end:])]
    if len(durations) != 1:
        return None
    duration = durations[0]
    age = next(n for n in amounts if n != duration)
    if not _has(r'^\s+years? (?:old|now)\b', p.text[age.end:]):
        return None
    if duration.start > r.end and _has(r'\b'+re.escape(left.group(1))+r'\b', p.question):
        return _answer(age.value*r.value+duration.value, 'Current proportional age plus elapsed years')
    if duration.start < r.start and _has(r'\bnow\b', p.question) and _has(r'\b'+re.escape(right_name)+r'\b', p.question):
        return _answer((age.value+duration.value)/r.value-duration.value,
                       'Recover the compared future age and subtract elapsed years')
    return None


def _original_share(p, rates):
    if len(rates) != 2 or len(p.numbers) != 3:
        return None
    known = next(n for n in p.numbers if n not in rates)
    first, requested = rates
    if requested.start < len(p.body) or not _has(r'^\s+(?:of )?(?:her |his |the )?original\b', p.text[requested.end:]):
        return None
    if not _has(r'\b(?:left|remaining)\b', _sentence(p.text, known.start, known.end)):
        return None
    if not _has(r'\b(?:spending|spent|used|using|gave|lost)\b', _sentence(p.text, first.start, first.end)):
        return None
    return _answer(known.value/(1-first.value)*requested.value,
                   'Known remainder / remaining share x requested original share')


def _probability_category(p, rates):
    if len(rates) != 1 or not 3 <= len(p.numbers) <= 5:
        return None
    r = rates[0]
    if not _has(r'\b(?:chance|probability)\b', p.body):
        return None
    unknown = re.search(r'\bsome ([a-z ]+?)(?:[.;,!?]|$)', p.body)
    if not unknown or not _words(unknown.group(1)) & _words(p.question):
        return None
    known = [n for n in p.numbers if n != r]
    if any(n.start > r.start for n in known):
        return None
    from .rates_and_unit_rates_r01_a4 import _unit
    category_head = _singular(unknown.group(1).split()[-1])
    if any(_unit(p.text, n) != category_head for n in known):
        return None
    descriptors = [_words(re.split(r'[.;,!?]|\band\b', p.text[n.end:])[0]) for n in known]
    distinct = _words(unknown.group(1)) - set.union(*descriptors)
    # The distinguishing category must label both the probability and query.
    probability_clause = _sentence(p.text, r.start, r.end)
    if not distinct & _words(probability_clause) & _words(p.question):
        return None
    if not all(re.match(r'\s+[a-z]+(?: [a-z]+)?', p.text[n.end:]) for n in known):
        return None
    return _answer(sum((n.value for n in known), Fraction(0))*r.value/(1-r.value),
                   'Other categories x requested share / complementary share')


def _split_then_share(p, rates):
    if len(rates) != 1 or len(p.numbers) != 3:
        return None
    r = rates[0]
    amounts = [n for n in p.numbers if n != r]
    total, groups = amounts
    if not total.start < groups.start < r.start or groups.value <= 0:
        return None
    if not _has(r'\b(?:evenly|equally) (?:split|divided|distributed) into\s*$', p.text[:groups.start]):
        return None
    if not _has(r'^\s+of\b', p.text[r.end:]):
        return None
    unit = re.match(r'\s+([a-z]+)', p.text[groups.end:])
    if not unit:
        return None
    singular = _singular(unit.group(1))
    if not _has(r'\b(?:took|takes|gets|received|uses) (?:a|one) '+re.escape(singular)+r'\b', p.text[groups.end:r.start]):
        return None
    if _choice(_label(p, r), p.question, p.body) != 1:
        return None
    return _answer(total.value/groups.value*r.value, 'Whole / equal groups x used fraction')


def _share_after_removal(p, rates):
    if len(rates) != 1 or len(p.numbers) != 3:
        return None
    r = rates[0]
    amounts = [n for n in p.numbers if n != r]
    total, removed = amounts
    if not total.start < removed.start < r.start:
        return None
    if not _has(r'^\s+of (?:what is left|what was left|the (?:remaining|rest))\b', p.text[r.end:]):
        return None
    actor = re.search(r'\b([a-z]+) (?:eats?|ate|uses?|used|takes?|took)\s*$', p.text[:r.start])
    if not actor or not _has(r'\b'+re.escape(actor.group(1))+r'\b', p.question):
        return None
    if not _has(r'\b(?:eats?|ate|uses?|used|takes?|took|removed|gave|sold)\s*$', p.text[:removed.start]):
        return None
    if _has(r'\b(?:left|remaining|rest)\b', p.question):
        return None
    return _answer((total.value-removed.value)*r.value, 'Remaining quantity x requested share')


def _costed_share(p, rates):
    """An initial fixed expense and a priced fraction of the remaining money."""
    if len(rates) != 1 or len(p.numbers) != 3:
        return None
    if not _has(r'\b(?:at first|originally|start with|begin with)\b', p.question):
        return None
    r = rates[0]
    amounts = [n for n in p.numbers if n != r]
    spent, cost = amounts
    if spent.kind != 'money' or cost.kind != 'money' or not spent.start < r.start < cost.start:
        return None
    if not _has(r'\bspent\s*$', p.text[:spent.start]):
        return None
    if not _has(r'^\s+of (?:the |his |her )?(?:remaining money|money (?:he|she|they) had left)\b', p.text[r.end:]):
        return None
    if not _has(r'\bcost\s*$', p.text[:cost.start]):
        return None
    return _answer(spent.value+cost.value/r.value, 'Fixed expense plus the whole of the priced share')


def _nested_shares(p, rates):
    """Two shares with an explicitly linked base, forward or inverse."""
    if len(rates) != 2 or len(p.numbers) != 3:
        return None
    first, second = rates
    amount = next(n for n in p.numbers if n not in rates)
    text, q = p.text, p.question
    second_base = re.match(r'\s+(?:of|the (?:size|length|height|weight) of)\s+(?:the )?(.+?)(?:\s+(?:are|is|have|has|went|go|wear|play|where|who)\b|[.;,!?])',
                           text[second.end:])
    label = _label(p, first)
    # The first proportional comparison may name its subject before the ratio.
    subject = re.split(r'[.;!?]|,(?!\d)|\band\b', text[:first.start])[-1]
    predicate = re.sub(r'\b(?:is|are|has|have|that|creates?|makes?)\b', '', subject)
    nested = bool(second_base and _words(second_base.group(1)) & _words(label))
    if second_base and _has(r'^\s+the (?:size|length|height|weight) of\b', text[second.end:]):
        nested = bool(_words(second_base.group(1)) & _words(predicate))
    # Repeating the same original denominator with different destinations
    # describes disjoint allocations, not a fraction of the preceding share.
    bases = [re.match(r'\s+of ((?:the|his|her|its|their) [a-z]+)\s+(?:in|for|to)\b',
                      text[r.end:]) for r in rates]
    if all(bases) and bases[0].group(1) == bases[1].group(1):
        nested = False
    if not nested:
        return None
    factor = first.value*second.value
    if amount.start < first.start:
        second_label = _label(p, second)
        # A category predicate or the second comparison's subject identifies
        # the final selected group.
        subj2 = re.split(r'[.;!?]|,(?!\d)|\band\b', text[:second.start])[-1]
        second_words = _words(second_label) - _words(second_base.group(1))
        first_predicate = re.search(r'\b(?:are|is|were|was)\s+([^,.;!?]+)', text[first.end:second.start])
        if first_predicate and _words(first_predicate.group(1)) & _words(q) and not second_words & _words(q):
            return _answer(amount.value*first.value, 'Whole x first selected share')
        if second_words & _words(q):
            if _opposite(second_label, q):
                factor = first.value*(1-second.value)
            return _answer(amount.value*factor, 'Whole x first share x nested share')
        if _has(r'^\s+the (?:size|length|height|weight) of\b', text[second.end:]):
            if (_words(subj2)-_words(subject)) & _words(q):
                return _answer(amount.value*factor, 'Whole x both comparison factors')
        return None
    if amount.start > second.end and _has(r'\b(?:total|altogether|entire|original)\b|\bin (?:the|a|an) [a-z]+\b', q):
        known = re.split(r'[.;!?]|,(?!\d)', text[amount.end:])[0]
        if not _words(_label(p, second)) & _words(known):
            return None
        return _answer(amount.value/factor, 'Known nested part / both shares')
    return None


def _remaining_split(p, rates):
    if len(rates) != 1:
        return None
    r = rates[0]
    amounts = [n for n in p.numbers if n != r]
    # Exclude a repeated count of the same recipients in the question.
    if len(amounts) == 3 and amounts[-1].start >= len(p.body) and amounts[-1].value == amounts[-2].value:
        amounts = amounts[:-1]
    if len(amounts) != 2 or not _has(r'\b(?:divided|split|shared|distributed)\b', p.body):
        return None
    base, groups = amounts
    if not base.start < r.start < groups.start or groups.value <= 0:
        return None
    if not _has(r'\b(?:rest|remaining|remainder)\b', p.text[r.end:groups.start]):
        return None
    if not _has(r'\b(?:evenly|equally|equal)\b', p.body):
        return None
    if not _has(r'\b(?:one|each|per)\b', p.question):
        return None
    return _answer(base.value*(1-r.value)/groups.value, 'Remaining share / equal recipients')


def _grouped_share(p, rates):
    """Explicit group capacity times group count times one selected share."""
    if len(rates) != 1 or len(p.numbers) != 3:
        return None
    r = rates[0]
    # Multiplying a count by a per-period rate yields an amount, not a time.
    if p.question.startswith('how long'):
        return None
    if _has(r'\bas (?:many|much)\b', p.body):
        return None
    if _has(r'\b(?:every|each|per)\s*$', p.text[:r.start]):
        return None
    amounts = [n for n in p.numbers if n != r]
    if _has(r'\b(?:more|less|fewer|left|remaining|original)\b', p.question):
        return None
    for rate, count in (amounts, amounts[::-1]):
        unit = re.match(r'\s+([a-z]+)', p.text[count.end:])
        if not unit:
            continue
        group = _singular(unit.group(1))
        before = _sentence(p.text, rate.start, rate.end).split(rate.raw)[0]
        after = re.split(r'[.;!?]', p.text[rate.end:])[0]
        per_group = _has(r'\beach ' + re.escape(group) + r'\b', before)
        per_group = per_group or _has(r'\b(?:per|each|a|every) ' + re.escape(group) + r'\b', after)
        if not per_group or group not in _words(p.body):
            continue
        choice = _choice(_label(p, r), p.question, p.body)
        if _has(r'^\s+full\b', p.text[r.end:]):
            choice = 1
        if choice != 1:
            continue
        return _answer(rate.value*count.value*r.value, 'Group count x capacity per group x selected share')
    return None


def _number_equation(p, rates):
    """An explicit additive adjustment to a fraction of an unknown number."""
    if len(rates) != 1 or len(p.numbers) != 3:
        return None
    if not re.fullmatch(r'what is the number[?. ]*', p.question):
        return None
    r = rates[0]
    amounts = [n for n in p.numbers if n != r]
    if not amounts[0].start < r.start < amounts[1].start:
        return None
    between = p.text[amounts[0].end:r.start]
    if not re.fullmatch(r'\s+(?:more|less) than\s*', between):
        return None
    if not re.fullmatch(r'\s+of a number is\s*', p.text[r.end:amounts[1].start]):
        return None
    delta, target = (n.value for n in amounts)
    return _answer((target-delta if 'more' in between else target+delta)/r.value,
                   'Remove the additive adjustment and divide by the fraction')


def _added_share(p, rates):
    """Recover an old stock after adding an amount and removing part of it."""
    if len(rates) != 1 or len(p.numbers) != 3:
        return None
    if not _has(r'\b(?:originally|original|at first|start)\b', p.question):
        return None
    r = rates[0]
    amounts = [n for n in p.numbers if n != r]
    added, final = amounts
    if not added.start < r.start < final.start:
        return None
    if not _has(r'\b(?:added|adds|put)\b[^.;]*$', p.text[:added.start]):
        return None
    if not _has(r'^\s+of\b[^.;]*\b(?:added|adds|put in)\b', p.text[r.end:]):
        return None
    if not _has(r'\b(?:took out|removed|takes out)\b', p.text[added.end:r.start]):
        return None
    if not _has(r'\b(?:now|left|remaining)\b', _sentence(p.text, final.start, final.end)):
        return None
    return _answer(final.value-added.value*(1-r.value), 'Final stock minus the retained part of the addition')


def _comparative_increase(p, rates):
    """A fraction more/fewer than one counted group, optionally combined."""
    if len(rates) != 1:
        return None
    r = rates[0]
    relation = re.match(r'\s+(more|fewer|less)\s+([a-z]+)\s+than\b', p.text[r.end:])
    if not relation:
        return None
    amounts = [n for n in p.numbers if n != r]
    # "One ... another ..." labels two observers, not an extra quantity.
    if len(amounts) == 2 and amounts[0].raw == 'one' and _has(r'\banother\b', p.body):
        amounts = amounts[1:]
    if len(amounts) != 1 or amounts[0].start > r.start:
        return None
    unit = re.match(r'\s+([a-z]+)', p.text[amounts[0].end:])
    if not unit or _singular(unit.group(1)) != _singular(relation.group(2)):
        return None
    if not _has(r'\b(?:both|combined|total|together|altogether)\b', p.question):
        return None
    factor = 2+r.value if relation.group(1) == 'more' else 2-r.value
    return _answer(amounts[0].value*factor, 'Original group plus the fractionally changed group')


def _loss(p, rates):
    if len(rates) != 1 or len(p.numbers) != 2 or not _has(r'\bloss\b', p.question):
        return None
    r = rates[0]
    amount = next(n for n in p.numbers if n != r)
    if not _has(r'^\s+of (?:the )?(?:cost|expenses|price)\b', p.text[r.end:]):
        return None
    if not _has(r'\b(?:payments|revenue|income|received)\b', p.text[:r.start]):
        return None
    if not _has(r'\b(?:expenses|cost)\b', _sentence(p.text, amount.start, amount.end)):
        return None
    return _answer(amount.value*(1-r.value), 'Cost minus the fraction recovered in revenue')


def _simple_comparison(p, rates):
    """Scale one known category, optionally asking for both categories' sum."""
    if len(rates) != 1 or len(p.numbers) != 2:
        return None
    r = rates[0]
    amount = next(n for n in p.numbers if n != r)
    tail = p.text[r.end:]
    m = re.match(r'\s+as (?:many|much)\s+(.+?)\s+as\s+([^.;!?]+)', tail)
    if not m:
        return None
    left = re.split(r'\b(?:to|for|when|in)\b', m.group(1))[0]
    right = re.split(r'\bif\b|,', m.group(2))[0]
    known = re.split(r'[.;!?]|,(?!\d)', p.text[amount.end:])[0]
    # Matching the count's unit to a category establishes which side is known.
    lu, ru = _words(left), _words(right)
    common = lu & ru
    known_l, known_r = bool((lu-common) & _words(known)), bool((ru-common) & _words(known))
    if known_l == known_r:
        return None
    base = amount.value/r.value if known_l else amount.value
    selected = base*r.value
    if _has(r'\b(?:total|altogether|together|combined|both)\b', p.question):
        return _answer(base+selected, 'Known category plus the proportional category')
    ql, qr = bool((lu-common) & _words(p.question)), bool((ru-common) & _words(p.question))
    if ql and not qr:
        return _answer(selected, 'Base category x stated fraction')
    if qr and not ql:
        return _answer(base, 'Known share / stated fraction')
    return None


def _sum_then_fraction(p, rates):
    """Two categories in one container, compared with a second container."""
    if len(rates) != 1 or len(p.numbers) != 3:
        return None
    r = rates[0]
    amounts = [n for n in p.numbers if n != r]
    if any(n.start > r.start for n in amounts):
        return None
    m = re.search(r'\b(?:there are|contains?|holds?)\b[^.;!?]*?\bin (?:the |a )?([^.;!?]+)', p.body[:r.start])
    relation = re.match(r'\s+as many\s+([a-z]+)\s+as (?:the )?([^.;!?]+)', p.text[r.end:])
    if not m or not relation:
        return None
    if not (_words(m.group(1)) & _words(relation.group(2))):
        return None
    between = p.text[amounts[0].end:amounts[1].start]
    if not _has(r'\band\b', between) or _has(r'\b(?:each|per|every)\b', p.text):
        return None
    # The queried container must be the subject of the comparison.
    prefix = re.split(r'[.;!?]', p.text[:r.start])[-1]
    distinct = _words(prefix) - _words(relation.group(2))
    if not distinct & _words(p.question):
        return None
    return _answer(sum((n.value for n in amounts), Fraction(0))*r.value,
                   'Combined contents x stated fraction')


def _minimum_gap(p, rates):
    if len(rates) != 1 or len(p.numbers) != 3:
        return None
    if not _has(r'\bmore\b', p.question) or not _has(r'\b(?:need|grow|reach|minimum)\b', p.question):
        return None
    r = rates[0]
    if not re.match(r'\s+(?:the )?(?:height|length|weight) of\b', p.text[r.end:]):
        return None
    amounts = [n for n in p.numbers if n != r]
    goals = [n for n in amounts if _has(r'\b(?:minimum|required|requires?|at least)\b',
                                     _sentence(p.text, n.start, n.end))]
    if len(goals) != 1:
        return None
    goal = goals[0]
    base = next(n for n in amounts if n != goal)
    gu = re.match(r'\s+([a-z]+)', p.text[goal.end:])
    bu = re.match(r'\s+([a-z]+)', p.text[base.end:])
    if not gu or not bu or gu.group(1) != bu.group(1):
        return None
    return _answer(goal.value-base.value*r.value, 'Required amount minus current proportional amount')


def _pair_price(p, rates):
    """A stated combined price of two items and a price ratio between them."""
    if len(rates) != 1 or len(p.numbers) != 2:
        return None
    r = rates[0]
    amount = next(n for n in p.numbers if n != r)
    if amount.kind != 'money':
        return None
    pair = re.search(r'\b(?:bought|buys|purchased) (?:a |an |the )?([a-z]+) and (?:a |an |the )?([a-z]+) for\s*$',
                     p.text[:amount.start])
    relation = re.match(r'\s+(?:the )?(?:price|cost) of (?:the |a |an )?([a-z]+)', p.text[r.end:])
    if not pair or not relation:
        return None
    first, second = pair.groups()
    right = relation.group(1)
    if right not in (first, second):
        return None
    left = second if right == first else first
    if not _has(r'\b' + re.escape(left) + r'\b', p.question[:max(0, r.start-len(p.body))]):
        return None
    return _answer(amount.value*r.value/(1+r.value), 'Combined price x fraction / (1 + fraction)')


def _comparison(p, rates):
    """Reuse the shared comparison graph after spelling out fraction factors."""
    if not rates and not any('/' in n.raw for n in p.numbers):
        return None
    text = p.text
    # Retain capitalization for the shared reader's owner detection.
    # Names in the original are restored by the caller before this reader.
    text = re.sub(r'(?P<f>\d+(?:\s+\d+/\d+|/\d+)?)\s+(?:the )?(?:age|size|height|length|weight|price|cost|speed) of\s+',
                  r'\g<f> times as old as ', text)
    text = re.sub(r'\bas big as\b', 'as much as', text)
    text = re.sub(r'(?P<f>\d+/\d+)\s+(?=as (?:many|much|old|long)\b|the (?:number|amount) of\b)',
                  r'\g<f> times ', text)
    text = re.sub(r'(\d+/\d+) of (?:the )?([a-z ]+?) (?:that|which) ([A-Za-z]+) (picked|collected|has|had|bought|made)\b',
                  r'\1 times as many \2 as \3 \4', text)
    # "a third more" means the original amount plus one third of it.
    def increase(m):
        r = Fraction(m.group(1))
        return str(1+r) + ' times as many ' + m.group(2) + ' as '
    text = re.sub(r'(\d+/\d+) (?:times )?more ([a-z ]+?) than ', increase, text)
    text = re.sub(r'\b(\d+(?:\s+\d+/\d+|/\d+)?) times older than\b', r'\1 times as old as', text)
    if text == p.text:
        return None
    parsed = Problem.read(text)
    if parsed is None:
        return None
    return _comparisons(parsed)


def solve(problem):
    if _has(r"^(?:i(?: am|'m)|we(?: are|'re))\s+(?:trying|learning|wondering)\b", problem.text.lower()):
        return None
    if any(n.kind == 'percent' for n in problem.numbers):
        return None
    p = _prepare(problem)
    if p is None:
        return None
    rates = _ratios(p)
    if not rates and not any('/' in n.raw for n in p.numbers):
        return None
    readers = (
        _summed_stock_share, _related_price, _grouped_inverse_share,
        _interval_schedule, _fractional_stocks, _transfer_explicit_share,
        _fraction_age_shift, _original_share, _probability_category,
        _number_equation, _costed_share, _share_after_removal, _split_then_share,
        _nested_shares, _remaining_split, _grouped_share, _added_share,
        _comparative_increase, _loss, _fraction_ledger, _split_share,
        _simple_comparison, _sum_then_fraction, _minimum_gap, _pair_price, _share,
    )
    for rule in readers:
        result = rule(p, rates)
        if result is not None:
            return result
    # Restore names after normalization without changing their spelling.
    from .comparisons_r01_a2 import _names
    text = p.text
    entities = _names(problem.text)
    possessions = re.findall(r"\b(?:his|her|their|[a-z]+'s) ([a-z]+) (?:is|was|has)\b", p.body)
    for noun in possessions:
        owners = set(re.findall(r"\b([a-z]+)'s "+re.escape(noun)+r'\b', p.body))
        if len(owners) <= 1:
            entities.append(noun)
    for name in entities:
        text = re.sub(r'\b' + re.escape(name) + r'\b', name.title(), text)
    return _comparison(replace(p, text=text), rates)
