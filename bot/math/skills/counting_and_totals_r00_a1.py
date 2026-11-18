"""Small, explicit schemas for combining, removing and grouping quantities.

Every schema checks both the relation and the requested unknown. Unsupported
relations are deliberately left for other skills rather than guessed.
"""
import re
from fractions import Fraction

from ..numbers import format_number
from ._counting_common import answer as _result


def _has(pattern, text):
    return re.search(pattern, text, re.I) is not None


def _f(value):
    return format_number(value)


def _sentence(text, start, end):
    """Sentence boundaries, excluding decimal points."""
    left = list(re.finditer(r'[.!?;](?:\s|$)', text[:start]))
    right = re.search(r'[.!?;](?:\s|$)', text[end:])
    return text[left[-1].end() if left else 0:end + right.start() if right else len(text)]


def _comparative_total(p):
    if any('/' in n.raw and 0 < n.value < 1 and
           re.match(r'\s+(?:more|less|fewer)\b', p.text[n.end:], re.I)
           for n in p.numbers):
        return None
    if any(n.kind == 'percent' for n in p.numbers):
        return None  # a relative difference is not an additive count
    if len(p.numbers) != 2 or not (_has(
            r'\b(total|combined|together|altogether)\b', p.question)
            or _has(r'\band\b.{0,30}\b(?:more|fewer)\b', p.body)):
        return None
    # A known quantity and a difference: A + (A +/- difference).
    text = p.text.lower()
    diffs = []
    for i, n in enumerate(p.numbers):
        tail = text[n.end:n.end + 65]
        match = re.match(r'\s+(?:\w+\s+){0,3}?(more|fewer|less|taller|shorter)\b', tail)
        if match:
            diffs.append((i, -1 if match.group(1) in ('fewer', 'less', 'shorter') else 1))
    if len(diffs) != 1:
        return None
    i, sign = diffs[0]
    delta, base = p.numbers[i].value, p.numbers[1-i].value
    explicit_total = _has(r'\b(?:total|combined|together|altogether)\b', p.question)
    if not explicit_total:
        if _different_owner(p):
            return None
        # Coordinated categories are only combined when the query asks for
        # their shared whole, rather than naming just one category.
        difference_noun = re.match(r'\s+(?:more|fewer|less)\s+([a-z]+)', text[p.numbers[i].end:])
        base_unit = _unit(text, p.numbers[1-i])
        if difference_noun and _singular(difference_noun.group(1)) != base_unit:
            asked = re.match(r'how many\s+([a-z]+)', p.question)
            if asked and _singular(asked.group(1)) in (base_unit, _singular(difference_noun.group(1))):
                return None
    if sign < 0 and delta > base:
        return None
    # Exclude changes over time: "had 20, bought 5 more" is addition,
    # while a comparative needs "than", "fewer", or an explicit second period.
    if not _has(r'\bthan\b|\bfewer\b', text):
        return None
    if _has(r'\b(?:times|twice|thrice|double|triple|quadruple|half|percent|each|per|average|ratio)\b', text):
        return None
    return _result(2 * base + sign * delta,
                   '{0} + ({0} {1} {2})'.format(_f(base), '+' if sign > 0 else '-', _f(delta)))


def _two_test_average(p):
    if len(p.numbers) != 2 or not _has(r'\baverage\b', p.body):
        return None
    if not (_has(r'\bfirst (?:test|exam)\b', p.body)
            and _has(r'\bsecond (?:test|exam)\b', p.question)):
        return None
    if not _has(r'\b(?:grade|score|mark)\b', p.question):
        return None
    average = None
    for i, n in enumerate(p.numbers):
        if _has(r'average.{0,25}$', p.body[max(0, n.start-40):n.start]):
            average = i
    if average is None:
        return None
    a, first = p.numbers[average].value, p.numbers[1-average].value
    return _result(2*a-first, '{} x 2 - {}'.format(_f(a), _f(first)))


def _corrected_count(p):
    if len(p.numbers) != 3 or not _has(r'\b(?:really|actually|actual)\b', p.question):
        return None
    over, missed, counted = [], [], []
    for n in p.numbers:
        before = p.body[max(0, n.start-45):n.start]
        if _has(r'double[- ]counts?\s*$', before):
            over.append(n.value)
        elif _has(r'(?:misses|missed|did not count)\s*$', before):
            missed.append(n.value)
        elif _has(r'counted\s*$', before):
            counted.append(n.value)
    if len(over) == len(missed) == len(counted) == 1:
        return _result(counted[0]-over[0]+missed[0], '{} - {} + {}'.format(
            _f(counted[0]), _f(over[0]), _f(missed[0])))
    return None


def _sum_and_difference(p):
    """Two disjoint groups, their combined count and the difference."""
    if len(p.numbers) != 2:
        return None
    text = p.text.lower()
    for i, n in enumerate(p.numbers):
        relation = re.match(r'\s+(more|fewer)\s+([a-z]+)\s+than\s+([a-z]+)', text[n.end:])
        if not relation:
            continue
        direction, first, second = relation.groups()
        # A count of one named category is a known base, not a combined
        # total. A question naming both categories asks for their sum.
        if (_unit(text, p.numbers[1-i]) in (_singular(first), _singular(second))
                or (_has(r'\b' + first + r'\b', p.question)
                    and _has(r'\b' + second + r'\b', p.question))):
            return None
        if not _has(r'\b(?:there are|there were|total|altogether|combined)\b', p.body):
            return None
        if _has(r'\b' + first + r'\b', p.question):
            sign = 1 if direction == 'more' else -1
        elif _has(r'\b' + second + r'\b', p.question):
            sign = -1 if direction == 'more' else 1
        else:
            return None
        total = p.numbers[1-i].value
        if total < n.value:
            return None
        return _result((total+sign*n.value)/2, '({} {} {}) / 2'.format(
            _f(total), '+' if sign > 0 else '-', _f(n.value)))
    return None


def _goal_less_groups(p):
    """A target amount minus repeated equal contributions."""
    if len(p.numbers) != 3 or not _has(r'\b(?:more|remaining)\b', p.question):
        return None
    text = p.text.lower()
    goal, size, groups = [], [], []
    for n in p.numbers:
        sentence = _sentence(text, n.start, n.end)
        if _has(r'\b(?:wants? to|aims? to|goal|target|needs? to)\b', sentence):
            goal.append(n.value)
        elif _has(r'\b(?:holds?|can hold|capacity|contains?)\b', sentence):
            size.append(n.value)
        elif _has(r'\b(?:refills?|filled|fills?|empties|empty|drinks?)\b', sentence) and _has(
                r'^\s+times\b', text[n.end:]):
            groups.append(n.value)
    if len(goal) == len(size) == len(groups) == 1:
        return _result(goal[0]-size[0]*groups[0], '{} - {} x {}'.format(
            _f(goal[0]), _f(size[0]), _f(groups[0])))
    return None


def _remaining_periods(p):
    """Goal minus completed work, divided by work done per asked-for period."""
    text = p.text.lower()
    period = re.match(r'how many (days|weeks|months|hours)\b', p.question)
    if not period or len(p.numbers) < 3:
        return None
    unit = _singular(period.group(1))
    rates, goals, completed = [], [], []
    for n in p.numbers:
        sentence = _sentence(text, n.start, n.end)
        if _has(r'\b(?:every|each|per|a)\s+' + unit + r'\b', sentence):
            rates.append(n.value)
        elif _has(r'\b(?:requires?|required|needs?|goal|target)\b', sentence):
            goals.append(n.value)
        elif _has(r'\b(?:completed|already|done|finished)\b', sentence):
            completed.append(n.value)
        else:
            return None
    if len(rates) != 1 or len(goals) != 1 or not completed or rates[0] <= 0:
        return None
    answer = (goals[0] - sum(completed, Fraction(0))) / rates[0]
    return _result(answer, '({} - ({})) / {}'.format(
        _f(goals[0]), ' + '.join(map(_f, completed)), _f(rates[0])))


def _periodic_loss(p):
    """A starting stock minus a constant loss during an explicit duration."""
    text = p.text.lower()
    if not _has(r'\b(?:weight|weigh|left|remaining|have)\b', p.question):
        return None
    if _has(r'\b(?:loss|lost|lose|loses)\b', p.question):
        return None
    start, loss, duration = [], [], None
    time_index = None
    for i, n in enumerate(p.numbers):
        sentence = _sentence(text, n.start, n.end)
        if n.start >= len(p.body):
            if _unit(text, n) in ('year', 'month', 'week', 'day'):
                time_index = i
        elif _has(r'\b(?:start|initially|originally|beginning)\b', sentence):
            # In a sentence containing both values, use the nearest preceding
            # loss verb to distinguish loss from initial stock.
            before = text[max(0, n.start-35):n.start]
            if _has(r'(?:lost|loses?)\s*$', before):
                loss.append(n.value)
            else:
                start.append(n.value)
        elif _has(r'(?:lost|loses?)\s*$', text[max(0, n.start-35):n.start]):
            loss.append(n.value)
    rate = re.search(r'\b(?:every|each|per|a)\s+(month|week|day)\b', p.body)
    if len(start) != 1 or len(loss) != 1 or not rate:
        return None
    time = re.search(r'\bafter\s+(a|an|one|\d+)\s+(year|month|week|day)s?\b', p.question)
    if not time:
        return None
    count = Fraction(1) if time.group(1) in ('a', 'an', 'one') else Fraction(time.group(1))
    conversions = {('year', 'month'): 12, ('week', 'day'): 7}
    if time.group(2) == rate.group(1):
        duration = count
    elif (time.group(2), rate.group(1)) in conversions:
        duration = count * conversions[(time.group(2), rate.group(1))]
    if duration is None or len(p.numbers) != 2 + (time_index is not None):
        return None
    return _result(start[0]-loss[0]*duration, '{} - {} x {}'.format(
        _f(start[0]), _f(loss[0]), _f(duration)))


def _unit(text, number):
    match = re.match(r'\s*[- ]?([a-z]+)', text[number.end:])
    if match and match.group(1) in ('more', 'extra', 'additional'):
        match = re.match(r'\s+(?:more|extra|additional)\s+([a-z]+)', text[number.end:])
    return _singular(match.group(1)) if match else ''


def _mixed_daily_rates(p):
    """An individual daily rate plus a group with another daily rate."""
    if len(p.numbers) != 3 or not _has(r'\b(?:per|a|each) day\b', p.question):
        return None
    text = p.text.lower()
    if _has(r'\b(?:more|less|fewer|than|twice|half|left)\b', text):
        return None
    units = [_unit(text, n) for n in p.numbers]
    for rate_index, n in enumerate(p.numbers):
        if not _has(r'\beach\s+(?:\w+\s+){0,2}$', text[max(0, n.start-30):n.start]):
            continue
        partners = [i for i, unit in enumerate(units) if i != rate_index and unit == units[rate_index]]
        if len(partners) != 1:
            continue
        other_index = partners[0]
        count_index = next(i for i in range(3) if i not in (rate_index, other_index))
        if count_index >= rate_index:
            continue
        if not all(_has(r'^\s+\w+\s+(?:a|per|each) day\b', text[p.numbers[i].end:])
                   for i in (rate_index, other_index)):
            continue
        rate, other, count = n.value, p.numbers[other_index].value, p.numbers[count_index].value
        return _result(count*rate+other, '{} x {} + {}'.format(_f(count), _f(rate), _f(other)))
    return None


def _both_per_group(p):
    """'Both members of each group' contributes two per group."""
    if len(p.numbers) != 2 or _has(r'\b(?:more|fewer|than|left|not|only)\b', p.text):
        return None
    relation = re.search(r'\bboth ([a-z]+) of each [a-z]+\b', p.body)
    if not relation or not _has(r'\b' + relation.group(1) + r'\b', p.question):
        return None
    if not _has(r'\bthere (?:are|were)\b', p.body):
        return None
    a, b = p.values
    return _result(2*(a+b), '({} + {}) x 2'.format(_f(a), _f(b)))


def _conversion(p):
    """A quantity and an explicit equality between two counting units."""
    if len(p.numbers) != 3:
        return None
    text = p.text.lower()
    ns = p.numbers
    for i in range(2):
        first, second = ns[i:i+2]
        between = text[first.end:second.start]
        if not re.fullmatch(r'\s+[a-z]+\s+(?:is|equals|contains|holds)\s+', between):
            continue
        source_unit, target_unit = _unit(text, first), _unit(text, second)
        other = ns[next(j for j in range(3) if j not in (i, i+1))]
        asked = re.match(r'how many\s+([a-z]+)', p.question)
        if not asked or first.value <= 0 or second.value <= 0:
            return None
        query_unit = _singular(asked.group(1))
        if _unit(text, other) == target_unit and query_unit == source_unit:
            return _result(other.value*first.value/second.value, '{} x {} / {}'.format(
                _f(other.value), _f(first.value), _f(second.value)))
        if _unit(text, other) == source_unit and query_unit == target_unit:
            return _result(other.value*second.value/first.value, '{} x {} / {}'.format(
                _f(other.value), _f(second.value), _f(first.value)))
    return None


def _singular(word):
    irregular = {'feet': 'foot', 'children': 'child', 'people': 'person',
                 'men': 'man', 'women': 'woman', 'mice': 'mouse',
                 'bus': 'bus', 'buses': 'bus'}
    if word in irregular:
        return irregular[word]
    if word.endswith('ies'):
        return word[:-3] + 'y'
    if word.endswith(('ches', 'shes', 'sses', 'xes', 'zzes')):
        return word[:-2]
    return word[:-1] if word.endswith('s') and not word.endswith('ss') else word


def _group_rate(p):
    """Find a per-group quantity and the count of those groups by their unit.

    Examples of grammar, independent of the particular nouns:
    N objects in each container; G containers; each container holds N objects.
    """
    text = p.text.lower()
    # A numbered measurement adjective is a container capacity, not a
    # count of containers to multiply ("bottles of N-liter water").
    # Leave the conversion to the rate skills.
    if any(re.match(r'-(?:liters?|litres?|milliliters?|gallons?|ounces?|pounds?|grams?|kilograms?)\b',
                    text[n.end:]) for n in p.numbers):
        return None
    # A quantity "in each of N containers" is itself a rate. Do not
    # mistake it for loose items when another per-container rate follows.
    if _has(r'\beach of\b', text):
        return None
    numbers = p.numbers
    # A fractional comparison describing items per group is not itself an
    # independently stated per-group quantity.
    if any(n.value < 1 for n in numbers) and _has(r'\btimes as (?:many|much)\b', text):
        return None
    if (not 2 <= len(numbers) <= 4 or any(n.kind != 'number' for n in numbers)
            or _has(r'\b(?:week|month|year|ratio|average|than|twice)\b', text)):
        return None
    # An unquantified contribution per component needs an additional relation.
    if _has(r'\b(?:a|an) [a-z]+(?: of [a-z]+)? for each\b', text):
        return None
    pairs = set()
    for match in re.finditer(r'\b(?:each|per)\s+(?:of (?:the|his|her)\s+)?([a-z]+)', text):
        group = _singular(match.group(1))
        if group in ('day', 'week', 'month', 'year'):
            continue  # handled separately, with explicit time conversion
        sentence = _sentence(text, match.start(), match.end())
        same = [i for i, n in enumerate(numbers)
                if _sentence(text, n.start, n.end) == sentence]
        if not same:
            continue
        # The rate is the quantity closest to 'each <group>' in this sentence.
        ri = min(same, key=lambda i: min(abs(numbers[i].end-match.start()),
                                       abs(numbers[i].start-match.end())))
        counts = [i for i, n in enumerate(numbers) if i != ri and _unit(text, n) == group]
        if counts:
            # Later extra groups are handled as an addition below.
            pairs.add((ri, counts[0]))
    if len(pairs) != 1:
        return None
    ri, ci = next(iter(pairs))
    rate, count = numbers[ri].value, numbers[ci].value
    asked = re.match(r'how many\s+([a-z]+)', p.question)
    # This schema multiplies in the rate's original units. Let a rate skill
    # handle a requested conversion such as minutes per item to total hours.
    if asked and _singular(asked.group(1)) in ('second', 'minute', 'hour'):
        source = _unit(text, numbers[ri])
        if source in ('second', 'minute', 'hour') and source != _singular(asked.group(1)):
            return None
    if (asked and _singular(asked.group(1)) == _unit(text, numbers[ci])
            and _unit(text, numbers[ci]) != _unit(text, numbers[ri])):
        return None
    others = [i for i in range(len(numbers)) if i not in (ri, ci)]
    if not others:
        if _has(r'\b(?:left|more|fewer|less|average|ratio|not)\b', p.question):
            return None
        return _result(rate * count, '{} x {}'.format(_f(count), _f(rate)))
    if len(others) != 1:
        return None
    oi = others[0]
    other = numbers[oi].value
    sentence = _sentence(text, numbers[oi].start, numbers[oi].end)
    if (oi < ri and oi != ci and _unit(text, numbers[oi]) == _unit(text, numbers[ci])
            and _has(r'\b(?:sold|bought|made|collected)\b', text)
            and not _has(r'\b(?:left|more|remaining|not)\b', p.question)):
        return _result((count+other)*rate, '({} + {}) x {}'.format(_f(count), _f(other), _f(rate)))
    if _has(r'\b(?:more|not (?:be )?placed|not (?:be )?packed)\b', p.question) and _has(
            r'\b(?:total|wants|aims|needs|goal)\b', sentence):
        return _result(other-rate*count, '{} - {} x {}'.format(_f(other), _f(count), _f(rate)))
    if _has(r'\b(?:not occupied|empty|vacant|unused|unoccupied)\b', sentence) and _has(
            r'\b(?:taken|occupied|used|filled)\b', p.question):
        return _result(rate*count-other, '{} x {} - {}'.format(_f(count), _f(rate), _f(other)))
    if _has(r'\b(?:extra|additional|more|left|remaining)\b', sentence) and not _has(
            r'\b(?:more|not|left|remaining)\b', p.question):
        # Additional groups change the group count; additional individual items
        # change the product. A remainder asks for the original total.
        if _unit(text, numbers[oi]) == _unit(text, numbers[ci]):
            return _result((count+other)*rate, '({} + {}) x {}'.format(_f(count), _f(other), _f(rate)))
        if _unit(text, numbers[oi]) == _unit(text, numbers[ri]):
            return _result(count*rate+other, '{} x {} + {}'.format(_f(count), _f(rate), _f(other)))
    return None


def _daily_groups(p):
    if _has(r'\bper (?!second\b|minute\b|hour\b|day\b|week\b|month\b|year\b)[a-z]+', p.body):
        return None
    """An explicit daily amount times an entity count and a duration."""
    text = p.text.lower()
    if any(re.match(r'-(?:liters?|litres?|milliliters?|gallons?|ounces?|pounds?|grams?|kilograms?)\b',
                    text[n.end:]) for n in p.numbers):
        return None  # A capacity conversion must precede a daily total.
    # A subdaily rate needs a dimensional conversion before multiplying by
    # daily operating time; leave it to a skill which reads that rate.
    if _has(r'\b(?:per|each|every|a|an) (?:second|minute|hour)\b', p.body):
        return None
    if _has(r'\b(?:kwh|kilowatt)\b',p.question):
        return None  # Power must be converted to the requested energy unit.
    if not _has(r'\b(?:a|per|each|every) day\b', p.body):
        return None
    if _has(r'\b(?:more|less|left|lost|loses|increase|decrease|than|but|not|back|round trip)\b', text):
        return None
    numbers = p.numbers
    duration = None
    duration_index = None
    match = re.search(r'\b(?:in|for|during)\s+(?:a|one)\s+week\b', p.question)
    if match:
        duration = Fraction(7)
        for i, n in enumerate(numbers):
            if n.start >= len(p.body) and n.value == 1:
                duration_index = i
    else:
        for i, n in enumerate(numbers):
            if n.start >= len(p.body) and _unit(text, n) == 'day':
                duration, duration_index = n.value, i
    if duration is None:
        return None
    used = [n for i, n in enumerate(numbers) if i != duration_index]
    if len(used) not in (1, 2) or any(n.kind != 'number' for n in used):
        return None
    if len(used) == 2 and not (_has(r'\beach\b', p.body) or _has(
            r'\b(?:has|have|uses|owns|keeps)\b', p.body)):
        return None
    daily_amounts = 0
    for i, n in enumerate(used):
        end = used[i+1].start if i+1 < len(used) else len(p.body)
        segment = text[n.end:end]
        if _has(r'\b(?:a|per|each|every) day\b', segment):
            daily_amounts += 1
    if daily_amounts != 1:
        return None
    answer = duration
    for n in used:
        answer *= n.value
    expression = ' x '.join([_f(n.value) for n in used] + [_f(duration)])
    # A repeated daily duration is still measured in its original unit.
    # Convert it when the question asks for a different time unit.
    asked_time = re.match(r'how many (seconds?|minutes?|hours?)\b', p.question)
    if asked_time:
        scale = {'second': 1, 'minute': 60, 'hour': 3600}
        source = [_unit(text, n) for n in used if _unit(text, n) in scale]
        if len(source) != 1:
            return None
        target = _singular(asked_time.group(1))
        factor = Fraction(scale[source[0]], scale[target])
        answer *= factor
        if factor != 1:
            expression = '(' + expression + ') x ' + _f(factor)
    return _result(answer, expression)


_VERBS = re.compile(
    r'\b(has|have|had|holds?|contains?|there (?:are|were)|baked?|bakes|bought|buys?|'
    r'prepared?|makes?|made|collected?|paints?|painted|picked|harvested|got|gets?|received?|receives|adds?|added|'
    r'sold|sells?|ate|eats?|eaten|gave|gives?|lost|loses?|used|uses|spent|spends|'
    r'burst|broke|broken|removed?|left|deletes?|deleted|aims?|wants?|needs?)\b')
_NEGATIVE = set('sold sell sells ate eat eats eaten gave gives lost lose loses used uses spent spends '
                'burst broke broken remove removed delete deletes deleted'.split())


def _compatible_units(p):
    phrases = []
    stops = set(('and or of in on at for to from with as by than before after during '
                 'that which who while when are is was were will would can could '
                 'has have had each per every a an the more extra additional '
                 'burst broke').split())
    for n in p.numbers:
        words = re.findall(r"[a-z]+(?:&[a-z]+)?(?:'s)?|\d+|[.,;!?]", p.body[n.end:])
        phrase = []
        for word in words:
            if word in stops or not word[0].isalpha() or len(phrase) == 3:
                break
            phrase.append(_singular(word))
        if phrase:
            phrases.append(phrase)
    if not phrases:
        return False
    # Elliptical lists ("red and green balloons") share a noun when one
    # phrase is an adjective appearing in another complete noun phrase.
    longest = sorted(phrases, key=len, reverse=True)
    heads = set()
    for phrase in phrases:
        expanded = next((full for full in longest if len(phrase) == 1 and phrase[0] in full), phrase)
        heads.add(expanded[-1])
    return len(heads) == 1


def _different_owner(p):
    # A transfer changes the giver's stock; it does not answer a question about
    # the recipient's stock. Without resolving pronouns across multiple owners,
    # abstain on a question naming a different person or one of several owners.
    asked = re.search(r'\b(?:does|did|will|can)\s+([A-Z][a-z]+)\b', p.text[len(p.body):])
    owners = set(re.findall(r'\b([A-Z][a-z]+)\s+(?:has|had|have)\b', p.text[:len(p.body)]))
    if asked and owners and owners != {asked.group(1)}:
        return True
    if len(owners) > 1 and not _has(r'\b(?:total|combined|altogether|together|all|they)\b', p.question):
        return True
    return False


def _ledger(p):
    """A single stock, with explicit additions/removals and no rates/relations."""
    text = p.text.lower()
    if _has(r'\b(?:refill|fill (?:up )?(?:the |an? )?(?:entire )?tank)\b', p.question):
        return None  # Capacity minus remaining stock is a separate calculation.
    if _has(r'\b(?:get|gets|got) off\b', p.body):
        return None  # Postposed boarding/alighting needs a local event reader.
    # A final stated whole after a list of categories overlaps the earlier
    # counts. It belongs to a partition reader, not an additive ledger.
    if len(p.numbers) >= 3 and _has(r'\bif there (?:are|were)\s*$',
                                   p.body[:p.numbers[-1].start]):
        return None
    # Ingredients required to produce something are a recipe, not owned stock.
    if _has(r'\bneeds?\s+[^.;!?]*\bto (?:make|produce)\b', p.body):
        return None
    if _has(r'\b(?:make|produce)\b[^.;!?]*\bfrom\b', p.body):
        return None
    if _has(r'\btotal\b', p.body) and _has(r'\bremaining\b', p.body):
        return None
    if not 2 <= len(p.numbers) <= 5 or any(n.start >= len(p.body) or n.kind != 'number'
                                         for n in p.numbers):
        return None
    # Adjacent quantities such as "three 5-minute talks" describe groups,
    # not separate entries in an additive inventory.
    if any(not text[a.end:b.start].strip() for a, b in zip(p.numbers, p.numbers[1:])):
        return None
    if _has(r'\b(?:each|per|every|times|twice|half|ratio|average|percent|fewer|less|than|'
            r'double|equal|both|same|weighs?|costs?|price|ago|older|younger|taller|spare|'
            r'new|old|a day|a week|rest|remainder|reserved|occupied|dedicated|allocated)\b', text):
        return None
    if any(n.value.denominator != 1 for n in p.numbers):
        return None
    if not _compatible_units(p):
        return None
    if _different_owner(p):
        return None
    query = p.question
    if not _has(r'\b(?:how many|total|altogether|together|combined)\b', query):
        return None
    remaining = _has(r'\b(?:left|remaining|more|need|have|give|gave)\b', query)
    total_events = not remaining
    # A total of sales/production counts those events positively. For remaining
    # inventory, the same sale is a removal from the starting stock.
    queried_sale = _has(r'\b(?:sell|sold|sales)\b', query)
    terms = []
    verbs = list(_VERBS.finditer(p.body))
    for n in p.numbers:
        start = max([m.end() for m in re.finditer(r'[.!?;](?:\s|$)', text[:n.start])] or [0])
        candidates = [m for m in verbs if start <= m.start() < n.start]
        if candidates:
            verb = candidates[-1].group()
        else:
            sentence = _sentence(text, n.start, n.end)
            # A postposed verb, e.g. "three red and two green balloons burst".
            post = list(_VERBS.finditer(sentence))
            if not post:
                return None
            # An unknown earlier action must not inherit a later action's
            # sign ("ordered 8 ... then lost 5"). Leave this to a reader
            # that recognizes that action explicitly.
            if _has(r'\b(?:ordered|purchased|reserved|allocated)\b', sentence):
                return None
            verb = post[-1].group()
        negative = verb in _NEGATIVE
        goal = _has(r'\b(?:aims?|wants?|needs?|goal)\b', text[start:n.start])
        if goal:
            negative = False
        elif queried_sale and not remaining and verb in ('sell', 'sells', 'sold'):
            negative = False
        if total_events and negative:
            return None
        terms.append((-1 if negative else 1, n.value))
    if not any(sign == 1 for sign, _ in terms):
        return None
    # A request for a new total needs additions; a request for a remainder needs
    # a removal or a goal, rather than an unexplained sum of personal facts.
    if remaining and not any(sign < 0 for sign, _ in terms):
        return None
    answer = sum((sign*value for sign, value in terms), Fraction(0))
    expression = ' '.join(('+' if sign > 0 else '-') + ' ' + _f(value) for sign, value in terms)
    return _result(answer, expression.lstrip('+ '))


def solve(problem):
    for rule in (_sum_and_difference, _comparative_total, _two_test_average, _corrected_count,
                 _goal_less_groups, _remaining_periods, _periodic_loss,
                 _mixed_daily_rates, _both_per_group, _conversion,
                 _daily_groups, _group_rate, _ledger):
        result = rule(problem)
        if result is not None:
            return result
    return None
