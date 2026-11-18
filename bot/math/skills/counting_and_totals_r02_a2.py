"""Compositional counting with explicit groups, changes, and unit conversions.

Relations, rather than the number of quantities, determine every operation.
All quantities must participate, and ambiguous group references cause abstention.
"""
import re
from fractions import Fraction

from ..numbers import format_number
from .counting_and_totals_r00_a1 import _singular
from .rates_and_unit_rates_r01_a4 import _rates, _convert, _sentence


_STOP = set(('and or but of in on at for to from with as by than before after during '
             'that which who while when are is was were will would can could '
             'has have had each per every a an the more extra additional then '
             'takes take fit fits holds hold contains contain makes make does '
             'do did he she they it his her their this these those used use '
             'reserved occupied dedicated weighing weighs weigh yields yield '
             'gets get left remaining altogether combined now total wide tall '
             'long high deep thick bought sold received requires require needs '
             'need called stayed were not picked drop brought taken folded scored read written waiting').split())
_TIME = {'second', 'minute', 'hour', 'day', 'week', 'month', 'year'}
_METRIC = {'liter': ('volume', 1000), 'milliliter': ('volume', 1),
           'kilogram': ('mass', 1000), 'gram': ('mass', 1),
           'meter': ('length', 100), 'centimeter': ('length', 1),
           'kilometer': ('length', 100000)}


def _has(pattern, text):
    return re.search(pattern, text) is not None


def _noun(tail):
    tail = re.sub(r'^\s*(?:of\s+)?(?:(?:the|his|her|their)\s+)?', '', tail)
    tail = re.sub(r'^(?:pieces|pairs) of\s+', '', tail)
    words = []
    for m in re.finditer(r'[a-z]+|[^\s-]', tail):
        word = m.group()
        if word in _STOP or not word.isalpha():
            break
        word = _singular(word)
        words.append(word)
        if word in _TIME or word in _METRIC or word in ('foot', 'inch', 'mile', 'mph'):
            break
        if len(words) >= 4:
            break
    return words[-1] if words else ''


def _unit(p, n):
    return 'dollar' if n.kind == 'money' else _noun(p.text.lower()[n.end:])


def _asked(p):
    m = re.match(r'how (?:many|much)\s+(?:(?:more|additional|extra|remaining|total)\s+)*', p.question)
    if m:
        return _noun(p.question[m.end():])
    m = re.search(r'(?:total|combined) (?:number|amount) of\s+', p.question)
    return _noun(p.question[m.end():]) if m else ''


def _conversion(value, source, dest):
    v = _convert(value, source, dest)
    if v is not None:
        return v
    if source in _METRIC and dest in _METRIC and _METRIC[source][0] == _METRIC[dest][0]:
        return value * Fraction(_METRIC[source][1], _METRIC[dest][1])
    return None


def _answer(value, expression):
    if value < 0:
        return None
    return value, expression + ' = ' + format_number(value) + '.'


def _quantity_list(p):
    """Exclude only an explicit enumeration of the following measurements."""
    ns = list(p.numbers)
    if ns and _has(r'^\s+(?:different )?(?:bottles|containers|measurements)\b', p.text.lower()[ns[0].end:]):
        if _has(r'\bfollowing\b', p.body[ns[0].end:]) and ns[0].value == len(ns)-1:
            ns = ns[1:]
    return ns


def _converted_sum(p):
    ns = _quantity_list(p)
    asked = _asked(p)
    if not asked or not 2 <= len(ns) <= 8 or not _has(r'\b(?:total|altogether|combined|in all)\b', p.question):
        return None
    if _has(r'\b(?:each|every|per|than|left|remaining|more|less|fewer|half|twice|lost|sold|gave|used)\b', p.text.lower()):
        return None
    values = [_conversion(n.value, _unit(p, n), asked) for n in ns]
    if any(v is None for v in values) or not any(_unit(p, n) != asked for n in ns):
        return None
    return _answer(sum(values, Fraction(0)), ' + '.join(map(format_number, values)))


def _grouped(p):
    """Join count -> per-group quantities, with dimensional time conversions."""
    ns = p.numbers
    text = p.text.lower()
    if _has(r'\bother (?:days|weeks|months|hours)\b', p.question):
        return None  # A stated whole minus completed groups needs subtraction.
    if not 3 <= len(ns) <= 8 or any(n.kind != 'number' for n in ns):
        return None
    if _has(r'\b(?:than|fewer|half|twice|double|percent|average|ratio|except|not)\b', text):
        return None
    units = [_unit(p, n) for n in ns]
    if not all(units):
        return None
    body_problem = p.__class__(p.text[:len(p.body)], p.body, p.question, ns)
    rates = dict(_rates(body_problem, ns))
    for i in range(1, len(ns)):
        if (units[i] in _TIME and _has(r'\bon each of\s*$',
                                     text[ns[i-1].end:ns[i].start])):
            rates[i-1] = units[i]
    for i, n in enumerate(ns):
        if i and re.match(r'\s+[a-z]+ each\b', text[n.end:]):
            rates[i] = units[i-1]
        if _has(r'\bon each day\b', _sentence(text, n)) and units[i] != 'day':
            rates[i] = 'day'
    for i, n in enumerate(ns):
        sentence = _sentence(text, n)
        local = [j for j, k in enumerate(ns) if _sentence(text,k) == sentence]
        if len(local) == 2 and _has(r'\bevery day\b', sentence):
            first, second = local
            if units[first] == 'hour' and units[second] == 'week':
                rates.pop(second, None)
                rates[first] = 'day'
    for i,n in enumerate(ns):
        m = re.search(r"\b([a-z]+) (?:are|is) all\s*$", text[:n.start])
        if m and units[i] in _TIME:
            rates[i] = _singular(m.group(1))
    # Relative clauses: N crates that each contain M objects.
    for i in range(1, len(ns)):
        middle = text[ns[i-1].end:ns[i].start]
        if re.fullmatch(r'\s+[a-z]+(?:\s+that)?\s+each\s+(?:contain|contains|hold|holds|have|has|makes?|produces?|eats?|bakes?)\s+', middle):
            rates[i] = units[i-1]
    # Multiword group names in "N roses in each table decoration".
    for i, n in enumerate(ns):
        end = ns[i+1].start if i+1 < len(ns) else len(p.body)
        suffix = re.split(r'[.!?;](?:\s|$)', text[n.end:end])[0]
        m = re.search(r'\b(?:per|each|every)\s+([a-z]+(?:\s+[a-z]+){0,2})', suffix)
        if m:
            group = _noun(m.group(1))
            if group:
                rates[i] = group
    if _has(r'\beach day\b', p.question):
        for i,n in enumerate(ns):
            m = re.search(r'\beach ([a-z]+) (?:eats?|produces?|makes?)\s*$', text[:n.start])
            if m:
                rates[i] = _singular(m.group(1))
    if not rates:
        return None
    parents = {}
    for ri, denominator in rates.items():
        # Join only an explicit unit or an exact time-unit conversion.
        candidates = [ci for ci in range(len(ns)) if ci != ri and
                      _conversion(Fraction(1), units[ci], denominator) is not None]
        local = [ci for ci in candidates if _sentence(text, ns[ci]) == _sentence(text, ns[ri])]
        if len(local) == 1:
            candidates = local
        if len(candidates) > 1:
            exact = [ci for ci in candidates if units[ci] == denominator]
            chained = [ci for ci in candidates if ci in rates]
            if len(exact) == 1:
                candidates = exact
            elif len(chained) == 1:
                candidates = chained
        if len(candidates) > 1:
            local = [ci for ci in candidates if _sentence(text, ns[ci]) == _sentence(text, ns[ri])]
            if len(local) == 1:
                candidates = local
        if len(candidates) != 1:
            return None
        ci = candidates[0]
        parents[ri] = (ci, _conversion(Fraction(1), units[ci], denominator))
    consumed = {ci for ci, factor in parents.values()}
    roots = [i for i in range(len(ns)) if i not in consumed]
    if not roots:
        return None
    # A remaining duration in a rate's denominator needs that same rate.
    # Converting bare days to hours would count the whole day as work.
    if any(i not in parents and units[i] in rates.values() for i in roots):
        return None
    seen = set()

    def evaluate(i, visiting):
        if i in visiting:
            raise ValueError('cyclic relation')
        seen.add(i)
        v, expression = ns[i].value, format_number(ns[i].value)
        if i in parents:
            ci, factor = parents[i]
            c, e = evaluate(ci, visiting | {i})
            v *= c * factor
            expression = '(' + e + ') x ' + expression
            if factor != 1:
                expression += ' x ' + format_number(factor)
        return v, expression

    try:
        terms = [(i,) + evaluate(i, set()) for i in roots]
    except ValueError:
        return None
    if len(seen) != len(ns):
        return None
    asked = _asked(p)
    # Disjoint group totals, possibly converting the final output unit.
    if not _has(r'\b(?:lost|sold|sells|gave|gives|ate|used|left|remaining|away)\b', text):
        converted = [_conversion(v, units[i], asked) for i, v, e in terms]
        if any(v is None for v in converted):
            # A collective noun is allowed only if the question explicitly
            # identifies every source container, and all sources are paired.
            if len(terms) < 2 or len(parents) != len(terms) or not _has(r'\btotal\b', p.question):
                return None
            if any(not re.search(r'\b' + re.escape(units[ci]) + r'(?:s|es)?\b', p.question)
                   for ci in consumed):
                return None
            converted = [v for i, v, e in terms]
        if len(terms) > 1:
            mentioned = {ci for ci in consumed if re.search(r'\b'+re.escape(units[ci])+r'(?:s|es)?\b', p.question)}
            if mentioned and mentioned != consumed:
                return None
            query = re.sub(r'^how (?:many|much)\s+(?:(?:total|more)\s+)?', '', p.question)
            query_label = _label(query)
            if len(query_label) > 1 and all(v is not None for v in [_conversion(Fraction(1),units[i],asked) for i,v,e in terms]):
                if any(_label(text[ns[i].end:]) != query_label for i,v,e in terms):
                    return None
        if len(terms) > 1 and not _has(r'\b(?:total|altogether|together|combined|in all)\b', p.question):
            return None
        expressions = []
        for (i, v, expression), result in zip(terms, converted):
            factor = _conversion(Fraction(1), units[i], asked)
            if factor is not None and factor != 1:
                expression = '(' + expression + ') x ' + format_number(factor)
            expressions.append(expression)
        return _answer(sum(converted, Fraction(0)), ' + '.join(expressions))
    # One known grouped stock followed by explicit amounts removed and left.
    grouped = [term for term in terms if term[0] in parents]
    if len(grouped) != 1 or any(units[i] != asked for i, v, e in terms):
        return None
    gi, stock, expr = grouped[0]
    adjustments = []
    for i, v, e in terms:
        if i == gi:
            continue
        sentence = _sentence(text, ns[i])
        if _has(r'\b(?:used|eaten|sold|gave|lost|left|remaining)\b', sentence):
            adjustments.append((v, e))
        else:
            return None
    if len(adjustments) < 1 or not _has(r'\b(?:left|remain|remaining|used|sold|eaten)\b', p.question):
        return None
    return _answer(stock-sum(v for v, e in adjustments), expr+' - ('+' + '.join(e for v, e in adjustments)+')')


def _areas(p):
    """Two explicit rectangles: combine or compare their rectangular areas."""
    text = p.text.lower()
    if not _has(r'\b(?:square|area)\b', p.question):
        return None
    ns = list(p.numbers)
    if len(ns) == 5 and ns[0].value == 2 and _has(r'^\s+rectangles\b', text[ns[0].end:]):
        ns = ns[1:]
    if len(ns) != 4 or len({_unit(p, n) for n in ns}) != 1:
        return None
    for a, b in (ns[:2], ns[2:]):
        middle = text[a.end:b.start]
        tail = text[b.end:b.end+20]
        if not (_has(r'\bby\b', middle) or
                _has(r'\b(?:wide|width)\b', middle) and _has(r'\b(?:tall|long|length|high)\b', tail)):
            return None
    a, b, c, d = (n.value for n in ns)
    if _has(r'\b(?:more|difference|compared)\b', p.question):
        # The ordinal query supplies the direction; do not take an absolute
        # difference when the problem asks for an explicitly signed comparison.
        if not _has(r'\bfirst\b.*\bsecond\b', p.question):
            return None
        return _answer(a*b-c*d, '{} x {} - {} x {}'.format(*map(format_number, (a,b,c,d))))
    if _has(r'\b(?:total|altogether|needed|need)\b', p.question) and _has(r'\b(?:rectangles|roof|shingles|area)\b', text):
        return _answer(a*b+c*d, '{} x {} + {} x {}'.format(*map(format_number, (a,b,c,d))))
    return None


def _category_totals(p):
    """Known category plus named additive comparisons, asking for the whole."""
    ns = p.numbers
    if not 3 <= len(ns) <= 5 or any(n.start >= len(p.body) for n in ns):
        return None
    text = p.text.lower()
    if _has(r'\b(?:each|per|half|twice|times|left|remaining|lost|gave|sold)\b', text):
        return None
    known, relations = {}, []
    heads = set()
    for n in ns:
        tail = text[n.end:]
        m = re.match(r'\s+(more|fewer|less)\s+([a-z ]+?)\s+than\s+(?:(?:the|his|her|their)\s+)?([a-z ]+?)(?=[,.;!?])', tail)
        if m:
            sign, left, right = m.groups()
            left = ' '.join(_singular(w) for w in left.split())
            right = ' '.join(_singular(w) for w in right.split())
            if left.split()[-1] != right.split()[-1]:
                return None
            heads.add(left.split()[-1])
            relations.append((left, right, n.value * (-1 if sign != 'more' else 1)))
        else:
            m = re.match(r'\s+([a-z]+(?:\s+[a-z]+){0,2})(?=[,.;!?])', tail)
            if not m:
                return None
            phrase = ' '.join(_singular(w) for w in m.group(1).split())
            known[phrase] = n.value
            heads.add(phrase.split()[-1])
    if not relations or len(known) != 1 or len(heads) != 1 or _asked(p) not in heads:
        return None
    if not re.match(r'how many\s+'+re.escape(next(iter(heads)))+r'(?:s|es)?\b', p.question):
        return None
    for _ in relations:
        for left, right, delta in relations:
            if right in known:
                if left in known and known[left] != known[right]+delta:
                    return None
                known[left] = known[right]+delta
    nodes = {x for a, b, d in relations for x in (a,b)}
    if set(known) != nodes or any(v < 0 for v in known.values()):
        return None
    return _answer(sum(known.values(), Fraction(0)), ' + '.join(map(format_number, known.values())))


_LEDGER_VERBS = re.compile(r'\b(has|have|had|contains?|contained|bought|buys?|got|received|'
                           r'collected|made|makes?|adds?|added|replaced|having|there are|there were|'
                           r'lost|loses?|ate|eats?|used|uses|gave|gives?|sold|sells?|'
                           r'took|take|remove|removed|reduce|reduced|folds?|folded)\b')
_DEBIT = set('lost loses lose ate eats eat used uses gave gives sold sells took take remove removed reduce reduced folds fold folded'.split())


def _ledger(p):
    ns = p.numbers
    text = p.text.lower()
    if any(0 < n.value < 1 and re.match(r'\s+(?:of|his|her|their|the)\b', text[n.end:])
           for n in ns):
        return None
    if not 3 <= len(ns) <= 10 or any(n.kind != 'number' or n.start >= len(p.body) for n in ns):
        return None
    if not _has(r'\b(?:left|remain|remaining|now|have|has)\b', p.question):
        return None
    if _has(r'\b(?:each|every|per|than|half|twice|double|percent|ratio|average|rest|not)\b', text):
        return None
    units = [_unit(p, n) for n in ns]
    if not all(units):
        return None
    from .counting_and_totals_r00_a1 import _different_owner
    if _different_owner(p):
        return None
    # Scope the question to the initial owner or an unambiguous pronoun.
    owners = re.findall(r'\b([A-Z][a-z]+)\s+(?:has|had|bought|contains)\b', p.text[:ns[0].start])
    asked_owner = re.search(r'\b(?:does|did|will|can)\s+([A-Z][a-z]+)\b', p.text[len(p.body):])
    if asked_owner and (not owners or asked_owner.group(1) != owners[0]):
        return None
    total, expressions, positive, negative = Fraction(0), [], set(), set()
    prior_verb = None
    for i, n in enumerate(ns):
        segment = text[ns[i-1].end if i else 0:n.start]
        suffix = text[n.end:ns[i+1].start if i+1 < len(ns) else len(p.body)]
        passive_removal = _has(r'^\s+(?:[a-z]+\s+){1,3}(?:are|were|was|is) (?:removed|sold|used|lost|taken)\b', suffix)
        verbs = list(_LEDGER_VERBS.finditer(segment))
        if verbs:
            prior_verb = verbs[-1].group()
        elif i and _has(r'[.!?;]', segment):
            if passive_removal:
                prior_verb = 'removed'
            elif _has(r'\bdrop out\b', _sentence(text,n)):
                prior_verb = 'removed'
            else:
                return None
        if not prior_verb:
            return None
        suffix = text[n.end:ns[i+1].start if i+1 < len(ns) else len(p.body)]
        passive_removal = _has(r'^\s+(?:[a-z]+\s+){1,3}(?:are|were|was|is) (?:removed|sold|used|lost)\b', suffix)
        dropout = _has(r'\bdrop out\b', _sentence(text, n))
        sign = -1 if prior_verb in _DEBIT or passive_removal or dropout else 1
        if i == 0 and sign < 0:
            return None
        if sign < 0:
            negative.add(units[i])
        else:
            positive.add(units[i])
        total += sign*n.value
        expressions.append((' - ' if sign < 0 else ' + ')+format_number(n.value))
    if not negative or not negative <= positive:
        return None
    if len(positive) == 1:
        if _asked(p) != units[0]:
            return None
    elif not (_has(r'\b(?:remain|remaining|left)\b', p.question) and positive == negative):
        return None
    return _answer(total, ''.join(expressions).lstrip(' +'))


def _repeated_schedule(p):
    """A daily list of tasks repeated D days/week over W weeks."""
    ns = p.numbers
    text = p.text.lower()
    if not 4 <= len(ns) <= 7 or not _has(r'\bdoes this\b', p.body):
        return None
    if _has(r'\b(?:more|less|left|than|half|twice|not)\b', text):
        return None
    days, weeks = ns[-2:]
    if not re.match(r'\s+days (?:a|per|each) week\b', text[days.end:]) or _unit(p, weeks) != 'week':
        return None
    tasks = ns[:-2]
    asked = _asked(p)
    converted = [_conversion(n.value, _unit(p,n), asked) for n in tasks]
    if any(v is None for v in converted) or any(n.start >= len(p.body) for n in tasks):
        return None
    value = sum(converted, Fraction(0))*days.value*weeks.value
    return _answer(value, '({}) x {} x {}'.format(' + '.join(map(format_number, converted)), format_number(days.value), format_number(weeks.value)))


def _population_frequency(p):
    """A frequency for one member, multiplied by members and elapsed time."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or _has(r'\b(?:more|less|than|left|not|half|twice)\b', text):
        return None
    rate, population, duration = ns
    relation = re.match(r'\s+times (?:per|each|every|a) (second|minute|hour|day)\b', text[rate.end:])
    subject = re.match(r'\s*(?:if )?(?:a|an) ([a-z]+)\b', text)
    if not relation or not subject or _unit(p, population) != _singular(subject.group(1)):
        return None
    if not _has(r'\b(?:same pace|same rate|each|every)\b', text) or not _has(r'\b(?:combined|total|altogether)\b', p.question):
        return None
    elapsed = _conversion(duration.value, _unit(p,duration), relation.group(1))
    if elapsed is None or not _has(r'\bnumber of times\b|^how many times\b', p.question):
        return None
    return _answer(rate.value*population.value*elapsed, '{} x {} x {}'.format(*map(format_number,(rate.value,population.value,elapsed))))


def _recipe_remaining(p):
    """A stated input/output recipe, completed batches, and remaining capacity."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 4 or not _has(r'\b(?:more|remaining|rest)\b', p.question):
        return None
    a, b, completed, total = ns
    if not _has(r'\b(?:calls for|requires?|needs?)\b', text[a.end:b.start]):
        return None
    if _unit(p,a) != _unit(p,completed) or _asked(p) != _unit(p,a):
        return None
    if _unit(p,b) != _unit(p,total) or min(a.value,b.value) <= 0:
        return None
    if not _has(r'\b(?:bakes?|makes?|made|completed|uses?|used)\b', text[b.end:completed.start]):
        return None
    if not _has(r'\b(?:contains?|has|holds?|bag|supply|total)\b', text[completed.end:total.start]):
        return None
    return _answer(total.value*a.value/b.value-completed.value, '{} x {} / {} - {}'.format(*map(format_number,(total.value,a.value,b.value,completed.value))))


def _comparison_remainder(p):
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or not _has(r'\b(?:keep|kept|left|remaining)\b', p.question):
        return None
    total, base, delta = ns
    if not _has(r'\b(?:shared|gave|gives|give|distributed)\b', p.body):
        return None
    recipient = re.search(r'\b([a-z]+) (?:received|receives|got|gets)\s*$', text[:base.start])
    comparison = re.match(r'\s+(more|fewer|less)\s+([a-z]+)\s+than\s+([a-z]+)\b', text[delta.end:])
    if not recipient or not comparison or recipient.group(1) != comparison.group(3):
        return None
    if _unit(p,total) != _unit(p,base) or _singular(comparison.group(2)) != _unit(p,total) or _asked(p) != _unit(p,total):
        return None
    adjustment = delta.value * (1 if comparison.group(1) == 'more' else -1)
    if base.value + adjustment < 0:
        return None
    return _answer(total.value-base.value-(base.value+adjustment), '{} - {} - ({} {} {})'.format(format_number(total.value),format_number(base.value),format_number(base.value),'+' if adjustment >= 0 else '-',format_number(abs(adjustment))))


def _fraction_remainder(p):
    """Remove a count, a fraction of what remains, and a final count."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 4 or not _has(r'\b(?:rest|remaining)\b', p.body):
        return None
    total, removed, fraction, final = ns
    if not 0 < fraction.value < 1 or not _has(r'^\s+of the remaining\b', text[fraction.end:]):
        return None
    if not _has(r'\b(?:dismissed|removed|lost|sold|gave|used)\b', text[removed.end:fraction.start]):
        return None
    # The fraction and the last count must be allocated to other categories;
    # the requested category is explicitly the rest.
    tail = text[final.end:len(p.body)]
    if not _has(r'\b(?:and|while) the rest\b', tail):
        return None
    rest = re.search(r'\bthe rest (?:were |are |was |is )?(?:judged |ruled |called |labelled |labeled )?([a-z]+)', tail)
    if not rest or not _has(r'\b'+re.escape(rest.group(1))+r'\b', p.question):
        return None
    value = (total.value-removed.value)*(1-fraction.value)-final.value
    return _answer(value, '({} - {}) x (1 - {}) - {}'.format(*map(format_number,(total.value,removed.value,fraction.value,final.value))))


def _remaining_proportion(p):
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or not _has(r'\bremaining\b', p.question):
        return None
    total, done, elapsed = ns
    if _unit(p,total) != _unit(p,done) or _unit(p,elapsed) != _asked(p) or done.value <= 0:
        return None
    if not re.fullmatch(r'\s+[a-z]+\s+in\s+', text[done.end:elapsed.start]):
        return None
    if not _has(r'\b(?:read|completed|finished|covered|painted)\b', text[total.end:done.start]):
        return None
    if not _has(r'\b(?:same|that) rate\b', p.text.lower()):
        return None
    return _answer((total.value-done.value)*elapsed.value/done.value, '({} - {}) x {} / {}'.format(*map(format_number,(total.value,done.value,elapsed.value,done.value))))


def _equal_parts(p):
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or not _has(r'\bequal (?:parts|pieces|portions)\b', p.body):
        return None
    total, groups, used = ns
    if _unit(p,groups) not in ('equal', 'part', 'piece', 'portion'):
        return None
    if not _has(r'\b(?:used|uses|gave|sold|removed)\b', text[groups.end:used.start]):
        return None
    if _unit(p,used) not in ('part', 'piece', 'portion') or _unit(p,total) != _asked(p):
        return None
    if not _has(r'\b(?:not used|unused|left|remaining)\b', p.question) or groups.value <= 0:
        return None
    return _answer(total.value*(groups.value-used.value)/groups.value, '{} x ({} - {}) / {}'.format(*map(format_number,(total.value,groups.value,used.value,groups.value))))


def _rate_comparison(p):
    """Two named rates for a shared duration, or one rate for two durations."""
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or not _has(r'\b(?:more|difference)\b', p.question):
        return None
    if _has(r'\b(?:half|twice|percent|remaining|left)\b', text):
        return None
    rates = _rates(p, ns)
    if len(rates) == 2:
        (i, denom), (j, denom2) = rates
        if denom != denom2 or _unit(p,ns[i]) != _unit(p,ns[j]) or _asked(p) != _unit(p,ns[i]):
            return None
        k = next(k for k in range(3) if k not in (i,j))
        duration = _conversion(ns[k].value, _unit(p,ns[k]), denom)
        if duration is None:
            return None
        owners = []
        for ri in (i,j):
            prefix = text[:ns[ri].start]
            matches = list(re.finditer(r'\b([a-z]+) (?:reads?|writes?|runs?|makes?|produces?|earns?|travels?)\s*$', prefix))
            if not matches:
                return None
            owners.append(matches[-1].group(1))
        positions = [p.question.find(owner) for owner in owners]
        if min(positions) < 0 or positions[0] == positions[1]:
            return None
        delta = ns[i].value-ns[j].value if positions[0] < positions[1] else ns[j].value-ns[i].value
        return _answer(delta*duration, '({} - {}) x {}'.format(format_number(ns[i].value if positions[0] < positions[1] else ns[j].value),format_number(ns[j].value if positions[0] < positions[1] else ns[i].value),format_number(duration)))
    if len(rates) == 1:
        ri, denom = rates[0]
        others = [n for i,n in enumerate(ns) if i != ri]
        old, new = others
        if new.start < len(p.body) or old.start >= len(p.body) or _asked(p) != _unit(p,ns[ri]):
            return None
        a = _conversion(old.value,_unit(p,old),denom)
        b = _conversion(new.value,_unit(p,new),denom)
        if a is None or b is None:
            return None
        return _answer((b-a)*ns[ri].value, '({} - {}) x {}'.format(*map(format_number,(b,a,ns[ri].value))))
    return None


def _missing_average(p):
    ns = p.numbers
    text = p.text.lower()
    if len(ns) < 4 or not _has(r'\baveraged?\b', p.body):
        return None
    count, average = ns[-2:]
    if not re.fullmatch(r'\s+averaged\s+', text[count.end:average.start]):
        return None
    if count.value != len(ns)-1 or any(_unit(p,n) != _unit(p,average) for n in ns[:-2]):
        return None
    m = re.search(r'how many(?: [a-z]+)? did ([a-z]+)\b', p.question)
    if not m:
        return None
    if not _has(r'\b'+re.escape(m.group(1))+r' [a-z]+ some\b', p.body):
        return None
    total = count.value*average.value-sum((n.value for n in ns[:-2]),Fraction(0))
    return _answer(total, '{} x {} - ({})'.format(format_number(count.value),format_number(average.value),' + '.join(format_number(n.value) for n in ns[:-2])))


def _allocated_groups(p):
    """A per-group output with several groups allocated to other categories."""
    ns = p.numbers
    text = p.text.lower()
    if not 4 <= len(ns) <= 6 or not _has(r'\b(?:rest|remaining)\b', p.body):
        return None
    count, rate = ns[:2]
    group = _unit(p,count)
    if not group or any(_unit(p,n) != group for n in ns[2:]):
        return None
    if not _has(r'\b(?:in|per|on) each '+re.escape(group)+r'\b', text[rate.end:ns[2].start]):
        return None
    tail = p.body[ns[-1].end:]
    remainder = re.search(r'\b(?:rest|remaining)\b[^.!?]*\b(?:with|for|are|is) ([a-z]+)', tail)
    if not remainder or not _has(r'\b'+re.escape(remainder.group(1))+r'\b', p.question):
        return None
    if any(n.start >= len(p.body) for n in ns):
        return None
    value = (count.value-sum((n.value for n in ns[2:]),Fraction(0)))*rate.value
    return _answer(value, '({} - ({})) x {}'.format(format_number(count.value),' + '.join(format_number(n.value) for n in ns[2:]),format_number(rate.value)))


def _label(phrase):
    """Preserve category adjectives and 'of' complements in container names."""
    words = []
    for word in re.findall(r'[a-z]+|[^\s-]', phrase.strip()):
        if word in ('a','an','the','his','her','their'):
            continue
        if word in _STOP-{'of'} or not word.isalpha():
            break
        words.append(_singular(word))
    return tuple(words)


def _labelled_groups(p):
    """Separate named container types, with an explicit capacity for each."""
    ns = p.numbers
    if len(ns) != 4 or any(n.kind != 'number' for n in ns):
        return None
    text = p.text.lower()
    if _has(r'\b(?:left|remaining|lost|gave|sold|half|twice|percent|average)\b', text):
        return None
    tokenized = text
    for i,n in reversed(list(enumerate(ns))):
        tokenized = tokenized[:n.start]+'Q'+str(i)+tokenized[n.end:]
    capacities = []
    for m in re.finditer(r'\beach ([a-z ]+?) (?:has|have|contains?|contained|holds?|needs?|requires?|takes?)\s+Q(\d+)', tokenized):
        group = _label(m.group(1))
        ri = int(m.group(2))
        if group:
            capacities.append((group, ri))
    for m in re.finditer(r'(?:^|[.;]\s*)([a-z ]+?) (?:contain|contains|hold|holds)\s+Q(\d+)', tokenized):
        group = _label(m.group(1))
        if group:
            capacities.append((group, int(m.group(2))))
    if len(capacities) != 2 or len({g for g,i in capacities}) != 2:
        return None
    used, terms = set(), []
    for group, ri in capacities:
        candidates = [ci for ci,n in enumerate(ns) if ci != ri and _label(text[n.end:]) == group]
        if len(candidates) != 1:
            return None
        ci = candidates[0]
        if ci in used or ri in used:
            return None
        used.update((ci,ri))
        terms.append((group, ns[ci].value*ns[ri].value, '{} x {}'.format(format_number(ns[ci].value),format_number(ns[ri].value))))
    if len(used) != len(ns) or len({_unit(p,ns[ri]) for group,ri in capacities}) != 1:
        return None
    output = _unit(p,ns[capacities[0][1]])
    if _asked(p) != output:
        return None
    if _has(r'\b(?:more|fewer|less|difference)\b', p.question):
        shared = set(terms[0][0]) & set(terms[1][0])
        positions = []
        for group,value,expr in terms:
            unique = set(group)-shared
            hits = [m.start() for w in unique for m in re.finditer(r'\b'+re.escape(w)+r'(?:s|es)?\b',p.question)]
            if not hits:
                return None
            positions.append(min(hits))
        if positions[0] == positions[1]:
            return None
        first,second = terms if positions[0]<positions[1] else terms[::-1]
        if _has(r'\b(?:fewer|less)\b',p.question):
            first,second = second,first
        return _answer(first[1]-second[1],first[2]+' - '+second[2])
    shared = set(terms[0][0]) & set(terms[1][0])
    mentions = [any(re.search(r'\b'+re.escape(w)+r'(?:s|es)?\b',p.question) for w in set(g)-shared) for g,v,e in terms]
    if any(mentions) and not all(mentions):
        return None
    if not _has(r'\b(?:total|altogether|combined|in all)\b',p.question):
        return None
    return _answer(sum((v for g,v,e in terms),Fraction(0)),' + '.join(e for g,v,e in terms))


def _uniform_group_comparison(p):
    ns = p.numbers
    text = p.text.lower()
    if len(ns) != 3 or not _has(r'\bmore\b.*\bthan\b',p.question):
        return None
    a,b,rate = ns
    group = _unit(p,a)
    if group != _unit(p,b) or _asked(p) != _unit(p,rate):
        return None
    denom = re.search(r'\beach ([a-z]+) (?:contains?|contained|has|holds?|held)\s*$',text[:rate.start])
    if not denom:
        return None
    canonical = lambda u: 'pack' if u in ('pack','package') else u
    if canonical(_singular(denom.group(1))) != canonical(group):
        return None
    labels = [_label(text[n.end:]) for n in (a,b)]
    shared = set(labels[0]) & set(labels[1])
    positions = []
    for label in labels:
        hits = [m.start() for w in set(label)-shared for m in re.finditer(r'\b'+re.escape(w)+r'(?:s|es)?\b',p.question)]
        if not hits:
            return None
        positions.append(min(hits))
    if positions[0] == positions[1]:
        return None
    first,second = (a,b) if positions[0]<positions[1] else (b,a)
    return _answer((first.value-second.value)*rate.value,'({} - {}) x {}'.format(*map(format_number,(first.value,second.value,rate.value))))


def _square_remainder(p):
    ns=p.numbers
    text=p.text.lower()
    if len(ns)!=3 or not _has(r'\bsquare\b',p.question) or not _has(r'\b(?:not covered|uncovered|remaining)\b',p.question):
        return None
    side,a,b=ns
    if not _has(r'\bsquare\b.*\bside(?: length)? of\s*$',text[:side.start]):
        return None
    if not re.fullmatch(r'\s+[a-z]+\s+by\s+',text[a.end:b.start]):
        return None
    if len({_unit(p,n) for n in ns})!=1:
        return None
    return _answer(side.value**2-a.value*b.value,'{} x {} - {} x {}'.format(*map(format_number,(side.value,side.value,a.value,b.value))))


def _metric_comparison(p):
    ns=p.numbers
    text=p.text.lower()
    if len(ns)!=2 or not _has(r'\blonger\b.*\bthan\b',p.question):
        return None
    a,b=ns
    asked=_asked(p)
    av,bv=(_conversion(n.value,_unit(p,n),asked) for n in ns)
    if av is None or bv is None or _unit(p,a)==_unit(p,b):
        return None
    # Resolve direction using the named subjects of the two measurements.
    names=[]
    for n in ns:
        prefix=text[:n.start]
        matches=list(re.finditer(r'\b([a-z]+(?: [a-z]+)?) (?:is|measures)\s*$',prefix))
        if not matches:
            return None
        names.append(matches[-1].group(1))
    positions=[p.question.find(name) for name in names]
    if min(positions)<0 or positions[0]==positions[1]:
        return None
    first,second=(av,bv) if positions[0]<positions[1] else (bv,av)
    return _answer(first-second,'{} - {}'.format(format_number(first),format_number(second)))


def _same_amount_group(p):
    ns=p.numbers
    text=p.text.lower()
    if len(ns)!=3 or not _has(r'\bsame amount as (?:her|him)\b',p.body):
        return None
    count,rate,others=ns
    if _unit(p,others) not in ('friend','classmate','colleague','sibling'):
        return None
    if not _has(r'\beach '+re.escape(_unit(p,count))+r' (?:holds?|contains?|has)\s*$',text[:rate.start]):
        return None
    if _unit(p,rate)!=_asked(p) or not _has(r'\b(?:in all|total|together|altogether)\b',p.question):
        return None
    if not _has(r'\band (?:her|his|their) friends\b',p.question):
        return None
    return _answer(count.value*rate.value*(others.value+1),'{} x {} x ({} + 1)'.format(*map(format_number,(count.value,rate.value,others.value))))


def _two_group_balance(p):
    """Two recipes/capacities, a known group count, and a resource total."""
    ns=p.numbers
    if not 4 <= len(ns) <= 6 or any(n.kind!='number' for n in ns):
        return None
    text=p.text.lower()
    tokenized=text
    for i,n in reversed(list(enumerate(ns))):
        tokenized=tokenized[:n.start]+'Q'+str(i)+tokenized[n.end:]
    rates=[]
    for m in re.finditer(r'\b(a|an|each|Q\d+) ([a-z ]+?) (?:requires?|needs?|seats?|holds?|contains?)\s+Q(\d+)',tokenized):
        group=_label(m.group(2))
        ri=int(m.group(3))
        divisor=Fraction(1)
        used={ri}
        if m.group(1).startswith('Q'):
            di=int(m.group(1)[1:])
            divisor=ns[di].value
            used.add(di)
        if divisor<=0 or not group:
            return None
        rates.append((group,ns[ri].value/divisor,_unit(p,ns[ri]),used))
    if len(rates)!=2 or rates[0][0]==rates[1][0] or rates[0][2]!=rates[1][2]:
        return None
    query=re.match(r'how many\s+(.+?)\s+(?:are|does|did|will|can|must|would)\b',p.question)
    if not query:
        return None
    wanted=_label(query.group(1))
    matches=[r for r in rates if r[0]==wanted]
    if len(matches)!=1:
        return None
    unknown=matches[0]
    known=next(r for r in rates if r!=unknown)
    used=rates[0][3]|rates[1][3]
    counts=[i for i,n in enumerate(ns) if i not in used and _label(text[n.end:])==known[0]]
    if len(counts)!=1:
        return None
    ci=counts[0]
    used.add(ci)
    totals=[i for i,n in enumerate(ns) if i not in used and _unit(p,n)==known[2]]
    if len(totals)!=1 or len(used)+1!=len(ns) or unknown[1]<=0:
        return None
    total=ns[totals[0]].value
    if not _has(r'\b(?:total|so that|same time|uses?)\b',text):
        return None
    value=(total-ns[ci].value*known[1])/unknown[1]
    return _answer(value,'({} - {} x {}) / {}'.format(*map(format_number,(total,ns[ci].value,known[1],unknown[1]))))


def _daily_week(p):
    """Combine daily rates for a week, or compose a rate with daily hours."""
    ns=p.numbers
    text=p.text.lower()
    if len(ns) not in (2,3) or not _has(r'\bweek\b',p.question):
        return None
    if _has(r'\b(?:more|less|left|than|half|twice|not|weekday|weekend)\b',text):
        return None
    if len(ns)==3:
        if ns[-1].start<len(p.body) or ns[-1].value!=1 or _unit(p,ns[-1])!='week':
            return None
        ns=ns[:-1]
    body_problem=p.__class__(p.text[:len(p.body)],p.body,p.question,ns)
    rates=dict(_rates(body_problem,ns))
    for i,n in enumerate(ns):
        end=ns[i+1].start if i+1<len(ns) else len(p.body)
        suffix=re.split(r'[.!?;](?:\s|$)',text[n.end:end])[0]
        if _has(r'\b(?:a|each|per|every) day\b',suffix):
            rates[i]='day'
    rates=sorted(rates.items())
    if len(rates)!=2:
        return None
    (i,di),(j,dj)=rates
    asked=_asked(p)
    weekdays=('monday','tuesday','wednesday','thursday','friday','saturday','sunday')
    if any(_has(r'\b'+d+r'\b',p.body) for d in weekdays):
        if di!=dj or di!='day' or _unit(p,ns[i])!=_unit(p,ns[j]) or _unit(p,ns[i])!=asked:
            return None
        terms=[]
        for ri in (i,j):
            end=ns[ri+1].start if ri+1<len(ns) else len(p.body)
            suffix=text[ns[ri].end:end]
            days=[d for d in weekdays if _has(r'\b'+d+r'\b',suffix)]
            span=re.search(r'from ('+'|'.join(weekdays)+r') to ('+'|'.join(weekdays)+r')',suffix)
            if span:
                days_count=(weekdays.index(span.group(2))-weekdays.index(span.group(1)))%7+1
            elif days:
                days_count=len(days)
            else:
                return None
            terms.append(ns[ri].value*days_count)
        return _answer(sum(terms,Fraction(0)),' + '.join(map(format_number,terms)))
    if di==dj=='day' and _unit(p,ns[i])==_unit(p,ns[j])==asked:
        return _answer((ns[i].value+ns[j].value)*7,'({} + {}) x 7'.format(format_number(ns[i].value),format_number(ns[j].value)))
    for ri,denominator,ti,period in ((i,di,j,dj),(j,dj,i,di)):
        if period!='day' or _unit(p,ns[ri])!=asked:
            continue
        duration=_conversion(ns[ti].value,_unit(p,ns[ti]),denominator)
        if duration is not None:
            return _answer(ns[ri].value*duration*7,'{} x {} x 7'.format(format_number(ns[ri].value),format_number(duration)))
    return None


def _time_budget(p):
    """A time allowance minus tasks with explicitly stated durations."""
    ns=p.numbers
    text=p.text.lower()
    if not 3 <= len(ns) <= 8 or not _has(r'\bleft\b',p.question):
        return None
    if _asked(p) not in ('time','minute','hour') or _has(r'\b(?:each|per|every|half|twice|than)\b',text):
        return None
    if _unit(p,ns[0]) not in _TIME or not _has(r'\b(?:has|have|had)\s*$',text[:ns[0].start]):
        return None
    if not _has(r'^\s+(?:hours|minutes) to\b',text[ns[0].end:]):
        return None
    dest=_asked(p)
    if dest=='time':
        dest=_unit(p,ns[1])
    total=_conversion(ns[0].value,_unit(p,ns[0]),dest)
    if total is None:
        return None
    tasks=[]
    for i,n in enumerate(ns[1:],1):
        segment=text[ns[i-1].end:n.start]
        if not _has(r'\btakes?(?: (?:her|him|them))?\s*$',segment):
            return None
        value=_conversion(n.value,_unit(p,n),dest)
        if value is None:
            return None
        tasks.append(value)
    return _answer(total-sum(tasks,Fraction(0)),'{} - ({})'.format(format_number(total),' + '.join(map(format_number,tasks))))


def _pack_sizes(p):
    """N packs of a named category; that category comes in packs of S."""
    ns=p.numbers
    text=p.text.lower()
    if len(ns)!=4 or not _has(r'\b(?:in all|total|altogether)\b',p.question):
        return None
    if _has(r'\b(?:more|less|than|left|sold|used|lost|half|twice)\b',text):
        return None
    tokenized=text
    for i,n in reversed(list(enumerate(ns))):
        tokenized=tokenized[:n.start]+'Q'+str(i)+tokenized[n.end:]
    terms=[]
    used=set()
    for m in re.finditer(r'\b(?:the )?([a-z -]+?) come in (packs|packages|boxes) of Q(\d+)',tokenized):
        label=_label(re.sub(r'^(?:and |the )+', '', m.group(1)))
        ri=int(m.group(3))
        group=_singular(m.group(2))
        ci=[]
        for i,n in enumerate(ns):
            tail=re.match(r'\s+'+re.escape(m.group(2))+r' of ([a-z -]+)',text[n.end:])
            if tail and _label(tail.group(1))==label:
                ci.append(i)
        if len(ci)!=1 or ri in used or ci[0] in used or not label or label[-1]!=_asked(p):
            return None
        used.update((ci[0],ri))
        terms.append((ns[ci[0]].value*ns[ri].value,'{} x {}'.format(format_number(ns[ci[0]].value),format_number(ns[ri].value))))
    if len(terms)!=2 or len(used)!=len(ns):
        return None
    return _answer(sum((v for v,e in terms),Fraction(0)),' + '.join(e for v,e in terms))


def _weekly_goal(p):
    """A daily average over a full week, or beating last week's total."""
    ns = p.numbers
    text = p.text.lower()
    if not 3 <= len(ns) <= 7 or any(n.start >= len(p.body) for n in ns):
        return None
    weekdays = ('monday','tuesday','wednesday','thursday','friday','saturday','sunday')
    wanted = [d for d in weekdays if _has(r'\b'+d+r'\b',p.question)]
    if len(wanted) != 1 or not _has(r'\bweek\b',p.body):
        return None
    if not all(_has(r'\b'+d+r'\b',p.body) for d in weekdays if d != wanted[0]):
        return None
    goal = ns[0]
    prefix = text[:goal.start]
    first = text[goal.end:ns[1].start]
    units = [_unit(p,n) for n in ns]
    if not units[0] or any(u and u!=units[0] for u in units[1:]):
        return None
    if _has(r'\baverage of\s*$',prefix) and _has(r'\b(?:a|per|each) day\b',first):
        target = goal.value*7
    elif _has(r'\blast week\b',prefix) and _has(r'\btotal\b',first) and _has(r'\b(?:beat|beats|exceed)\b',p.question):
        target = goal.value+1
    else:
        return None
    return _answer(target-sum((n.value for n in ns[1:]),Fraction(0)), '{} - ({})'.format(format_number(target),' + '.join(format_number(n.value) for n in ns[1:])))

def solve(problem):
    if any(n.value < 0 or n.kind == 'percent' for n in problem.numbers):
        return None
    for rule in (_converted_sum, _areas, _category_totals, _recipe_remaining, _comparison_remainder, _fraction_remainder, _ledger, _repeated_schedule, _population_frequency, _remaining_proportion, _equal_parts, _rate_comparison, _missing_average, _allocated_groups, _labelled_groups, _uniform_group_comparison, _square_remainder, _metric_comparison, _same_amount_group, _two_group_balance, _daily_week, _time_budget, _pack_sizes, _weekly_goal, _grouped):
        result = rule(problem)
        if result is not None:
            return result
    return None

