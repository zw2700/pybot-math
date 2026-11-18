"""Explicit fractional quantities, inverse stocks and small relation graphs.

Every reader establishes the role of each quantity and the requested part.
Unresolved scopes, units, transactions and extra quantities cause abstention.
"""
import re
from fractions import Fraction

from ..numbers import read_numbers, format_number
from ..problem import Problem, ASK
from ._fractions_common import has_fraction, normalize_fractions, _answer, _has
from .counting_and_totals_r00_a1 import _singular
from .comparisons_r01_a2 import _equation_graph, _mentions, _NOT_NAMES
from .fractions_of_a_quantity_r03_a3 import _words
from .counting_and_totals_r01_a3 import _unit as _count_unit


_LOSS = r'\b(?:ate|eats?|used|uses?|spent|spends?|gave|gives?|sold|sells?|took|takes?|lost|loses?|removed|donated|drank|eaten)\b'
_GAIN = r'\b(?:bought|buys?|added|adds?|received|receives?|got|gets?)\b'


def _prepare(problem):
    # Number normalization is local: original offsets and other skills stay intact.
    text = re.sub(r'\b(mr|mrs|ms|dr)\.\s*', '', problem.text, flags=re.I)
    text = re.sub(r'\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten) and half\b',
                  r'\1 and a half', text, flags=re.I)
    text = normalize_fractions(text)
    text = re.sub(r'\b(twice|double|doubled|thrice|triple|tripled)\b',
                  lambda m: '2 times' if m.group().lower() in ('twice', 'double', 'doubled') else '3 times', text, flags=re.I)
    asks = list(ASK.finditer(text))
    if not asks:
        return None
    at = asks[-1].start()
    ns = read_numbers(text)
    ns = [n for n in ns if not (n.raw.lower() in ('third', 'fourth', 'quarter') and
          re.search(r'\b(?:the|first|second|and)\s*$', text[:n.start], re.I) and
          re.match(r'\s+(?:day|month|year|hour|round|group|house|car|studio|dose|issue)\b', text[n.end:], re.I))]
    return Problem(text, text[:at].lower(), text[at:].lower(), ns)


def _tokens(p):
    text = p.text.lower()
    for i, n in reversed(list(enumerate(p.numbers))):
        text = text[:n.start] + 'Q' + str(i) + text[n.end:]
    return text


def _fractions(p):
    return [n for n in p.numbers if '/' in n.raw and 0 < n.value < 1 and n.kind != 'money']


def _comparison_clauses(text, names):
    """Split coordinated predicates while retaining joint subjects."""
    owner = '(?:'+'|'.join(re.escape(n) for n in names)+')'
    verbs = r'(?:has|have|had|is|was|made|caught|collected|picked|played|earned|ran)'
    subject = r'(?:the (?:length|size|age|number) of )?'+owner+r"(?:'s)?(?: [a-z]+){0,3}? "+verbs
    clauses = []
    for sentence in re.split(r'[.;!?]|\bwho\b',text):
        pieces = re.split(r',?\s+and\s+(?='+subject+r'\b)',sentence)
        current = pieces[0]
        for piece in pieces[1:]:
            if re.search(r'\b'+verbs+r'\b',current):
                clauses.append(current)
                current = piece
            else:
                current += ' and '+piece
        clauses.append(current)
    return clauses


def _unit(p, n):
    m = re.match(r'\s+(?:of (?:an? |the )?)?(?:(?:more|new|additional|total) )?([a-z]+)', p.text[n.end:].lower())
    return _singular(m.group(1)) if m else ''


def _inverse_stock(p, fs):
    """Recover a whole through affine gains and losses and a final remainder."""
    if not fs or not _has(r'\b(?:at first|to start|start with|begin with|originally|initially|beginning)\b', p.question):
        return None
    text = p.text.lower()
    if _has(r'\b(?:each|every|per|times|as many|as much|more than|less than)\b', text):
        return None
    amounts = [n for n in p.numbers if n not in fs]
    if not amounts or len(amounts) > 3 or any(n.start >= len(p.body) for n in p.numbers):
        return None
    final = amounts[-1]
    first_owner = re.search(r'\b([a-z]+) (?:has|had|have|lost|spent|ate|used|bought)\b',text[:fs[0].start])
    final_owner = re.search(r'\b([a-z]+) (?:has|had|have)\s*$',text[:final.start])
    if final_owner and final_owner.group(1) not in ('he','she','they'):
        if not first_owner or first_owner.group(1) != final_owner.group(1):
            return None
    final_clause = re.split(r'[.;!?]', text[:final.start])[-1] + text[final.end:].split('.')[0]
    if final.start < fs[-1].end or not _has(r'\b(?:left|remaining|rest|in the end)\b', final_clause):
        return None
    units = {_unit(p, n) for n in amounts}
    # Different stock nouns can be synonyms in prose; do not infer that here.
    if len(units) > 1:
        return None
    a, b = Fraction(1), Fraction(0)
    for index, n in enumerate(p.numbers):
        if n == final:
            continue
        before = text[p.numbers[index-1].end if index else 0:n.start]
        after = text[n.end:p.numbers[index+1].start if index+1 < len(p.numbers) else len(p.body)]
        if n in fs:
            verbs = list(re.finditer(_LOSS+'|'+_GAIN,before))
            gain = bool(verbs and _has(_GAIN,verbs[-1].group()))
            if gain and not _has(r'\b(?:left|remaining|rest)\b',after):
                return None
            if not (gain or _has(_LOSS, before)) or not re.match(r'\s+(?:of|the|his|her|their)\b', after):
                return None
            if n != fs[0] and not _has(r'\b(?:remaining|rest|remainder|left)\b', after):
                return None
            factor = 1+n.value if gain else 1-n.value
            a, b = a*factor, b*factor
        else:
            loss, gain = _has(_LOSS, before), _has(_GAIN, before)
            if not loss and not gain and _has(r'\band\s*$', before) and _has(r'^\s+more\b', after):
                loss = True
            if loss == gain:
                return None
            b += n.value * (-1 if loss else 1)
    if a <= 0:
        return None
    return _answer((final.value-b)/a, 'Undo the stated stock changes and fractional removals')


def _relations(p, fs):
    """Named affine comparisons, with a counted owner or a combined total."""
    if not fs or _has(r'\b(?:per|each|every|ago|when|from now|remaining|left|average|faster|sold|bought|gave)\b', p.body.replace('against each other','')):
        return None
    names = []
    for m in re.finditer(r"\b(?:[A-Z][a-z]+|[A-Z]{2,})(?:'s)?", p.text):
        name = re.sub(r"'s$", '', m.group()).lower()
        if name not in _NOT_NAMES and name not in ('calculate', 'determine') and name not in names:
            names.append(name)
    if len(names) < 2:
        return None
    text = _tokens(p)
    joint_games = set()
    for sentence in re.split(r'[.;!?]',text):
        if (_has(r'\bagainst each other\b',sentence) and _has(r'\bplayed\b',sentence)
                and len(set(_mentions(sentence,names))) == 2):
            joint_games.update(int(i) for i in re.findall(r'Q(\d+)',sentence))
    clauses = _comparison_clauses(text[:list(ASK.finditer(text))[-1].start()],names)
    relation = re.compile(
        r'(?:(Q\d+)\s+(?:[a-z]+\s+){0,2}?(more|less|fewer)\s+than\s+)?'
        r'(Q\d+)\s+(?:times\s+)?(?:'
        r'as (?:many|much|old|long|often)(?:\s+[a-z]+){0,7}?\s+as\s+|'
        r'(?:of\s+)?(?:the\s+)?(?:number|amount|age|size|length|weight|height|cost)(?:\s+(?:of|in))?\s+|'
        r'of\s+(?:what\s+)?|the\s+[a-z]+\s+(?=[a-z]+\s+(?:did|has|had)))')
    edges, used, previous = [], set(), None
    anchors = []
    for clause in clauses:
        if not clause.strip():
            continue
        matches = list(relation.finditer(clause))
        additive = None if matches else re.search(
            r'(Q\d+)\s+(?:[a-z]+\s+){0,2}?(more|less|fewer|older|younger)\s+than\s+', clause)
        if len(matches) > 1:
            return None
        if matches or additive:
            m = matches[0] if matches else additive
            lefts, rights = _mentions(clause[:m.start()], names), _mentions(clause[m.end():], names)
            left = lefts[-1] if lefts else previous
            if not left or not rights or left == rights[0]:
                return None
            scale = p.numbers[int(m.group(3)[1:])].value if matches else Fraction(1)
            delta = Fraction(0)
            if m.group(1):
                delta = p.numbers[int(m.group(1)[1:])].value * (-1 if m.group(2) not in ('more','older') else 1)
            if scale <= 0:
                return None
            edges.append((left, rights[0], scale, delta))
            used.update(int(i) for i in re.findall(r'Q(\d+)', m.group()))
            # An amount in the same relation clause is not a separate anchor.
            if set(map(int, re.findall(r'Q(\d+)', clause))) - used:
                return None
            previous = left
        else:
            mentioned = _mentions(clause, names)
            qs = list(re.finditer(r'Q(\d+)', clause))
            for m in qs:
                anchors.append((int(m.group(1)), clause, mentioned, previous))
            if mentioned:
                previous = mentioned[0]
    if not edges:
        return None
    nodes = {name for edge in edges for name in edge[:2]}
    known, total = [], None
    for i, clause, mentioned, prior in anchors:
        n = p.numbers[i]
        token = 'Q'+str(i)
        if n.value == len(nodes) and re.match(r'\s+(?:boys|girls|people|friends|children)\b', clause.split(token)[1]):
            used.add(i)
            continue
        total_cue = _has(r'\b(?:total|together|combined|altogether|in all|all together)\b', clause)
        if i in joint_games or (total_cue and len(set(mentioned) & nodes) != 1):
            if total is not None:
                return None
            total = n.value
        else:
            owners = [x for x in mentioned if x in nodes]
            owner = owners[0] if len(set(owners)) == 1 else prior if not owners else None
            if owner not in nodes or _has(r'\b(?:more|less|fewer)\b|\btimes\s+(?:as|the|of)', clause.split(token)[1]):
                return None
            known.append((owner, n.value))
        used.add(i)
    if used != set(range(len(p.numbers))):
        return None
    values = _equation_graph(edges, known, total)
    if values is None:
        return None
    asked = list(dict.fromkeys(_mentions(p.question, list(nodes))))
    if _has(r'\b(?:total|together|combined|altogether|in all)\b', p.question):
        value = sum((values[n] for n in (asked if len(asked) > 1 else values)), Fraction(0))
    elif len(asked) == 1:
        value = values[asked[0]]
    else:
        return None
    return _answer(value, 'Solve the stated proportional comparisons')


def _recipe_mixture(p, fs):
    """Two measured ingredients and a scaled volume of their mixture."""
    if len(p.numbers) not in (3, 4) or not fs:
        return None
    ns = list(p.numbers)
    if len(ns) == 4:
        labels = [n for n in ns if n.value == 1 and re.match(r'\s+(?:drink|serving|batch)\b', p.text[n.end:], re.I)]
        if len(labels) != 1:
            return None
        ns.remove(labels[0])
    a, b, total = ns
    if not _has(r'\b(?:recipe|mixture|mix|drink)\b', p.body) or not a.start < b.start < total.start:
        return None
    matches = [re.match(r'\s+(?:of (?:an? |the )?)?(cups?|liters?|litres?|ounces?|grams?) of ([a-z ]+?)(?=\s+and\b|\s+to make\b|[.;,])', p.text[n.end:], re.I) for n in (a,b)]
    if not all(matches) or _unit(p, a) != _unit(p, b):
        return None
    if not re.match(r'\s+(?:total )?'+re.escape(_singular(matches[0].group(1)))+r's?\b', p.text[total.end:], re.I):
        return None
    selected = [n for n, m in zip((a,b),matches) if _words(m.group(2)) & _words(p.question)]
    if len(selected) != 1 or a.value+b.value <= 0:
        return None
    return _answer(total.value*selected[0].value/(a.value+b.value), 'Mixture amount x ingredient fraction of the recipe')


def _measured_per_person(p, fs):
    """A fractional ingredient amount, its density/output and equal servings."""
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    f = fs[0]
    amounts = [n for n in p.numbers if n != f]
    text = p.text.lower()
    # A physical amount per item and an equal split of the items among people.
    per_item = re.match(r'\s+(?:of an? )?([a-z]+) of [a-z ]+? per ([a-z]+)\b', text[f.end:])
    if per_item and _has(r'\b(?:equal number|equally)\b', p.body):
        people = [n for n in amounts if re.match(r'\s+(?:family members|people|persons|children|guests)\b', text[n.end:])]
        stock = [n for n in amounts if _unit(p,n) == _singular(per_item.group(1))]
        if len(people) != 1 or len(stock) != 1 or people[0] == stock[0] or people[0].value <= 0:
            return None
        if not _has(r'\b'+re.escape(_singular(per_item.group(2)))+r's?\b', p.question):
            return None
        return _answer(stock[0].value/f.value/people[0].value, 'Total ingredient / ingredient per item / people')
    # Recipe serves N; f cups, and M grams per cup; query per serving.
    serving = [n for n in amounts if _has(r'\bserves?\s*$', text[:n.start]) and
               re.match(r'\s+(?:people|persons|servings)\b', text[n.end:])]
    if len(serving) != 1 or serving[0].value <= 0 or not _has(r'\b(?:each|per) serving\b', p.question):
        return None
    rate = next(n for n in amounts if n != serving[0])
    measure = re.match(r'\s+(?:(?:of )?an? )?(cup|pound|ounce|liter|litre)\b', text[f.end:])
    if not measure or not _has(r'\bper '+measure.group(1)+r'\b', text[rate.end:len(p.body)]):
        return None
    ru = _unit(p, rate)
    if not _has(r'\b'+re.escape(ru)+r's?\b', p.question):
        return None
    return _answer(f.value*rate.value/serving[0].value, 'Measured ingredient x amount per unit / servings')


def _scoped_categories(p, fs):
    """A counted whole and two disjoint categories or an explicit nested subset."""
    if len(fs) != 2 or len(p.numbers) != 3:
        return None
    base = next(n for n in p.numbers if n not in fs)
    text = p.text.lower()
    if _has(r'\b(?:per|each|times|more|less|as many|as much|left|remaining)\b', text):
        return None
    first, second = fs
    tails = [re.split(r'[.;]|\band\b',text[n.end:])[0] for n in fs]
    labels = [re.search(r'\b(?:are|is|have|has)\s+(.+)', t) for t in tails]
    if not all(labels):
        return None
    labels = [m.group(1) for m in labels]
    remainder = re.search(r'\b(?:the )?(?:others|rest) (?:are|is) ([^.;]+)', p.body)
    if remainder and _words(remainder.group(1)) & _words(p.question):
        if not all(re.match(r'\s+(?:are|is)\b',t) for t in tails) or sum((n.value for n in fs),Fraction(0)) > 1:
            return None
        return _answer(base.value*(1-first.value-second.value), 'Whole minus the two disjoint shares')
    # The second share must name the first predicate/category as its base.
    scope = re.split(r'\b(?:are|is|have|has)\b',tails[1])[0]
    first_words = _words(labels[0])
    def stem(w):
        return w[:-3] if w.endswith('ted') else w[:-2] if w.endswith('ed') else w
    shared = {stem(w) for w in first_words} & {stem(w) for w in _words(scope)}
    if not re.match(r'\s+of (?:the|those|these)\b',tails[1]) or not shared:
        return None
    label_words = [{stem(w) for w in _words(label)} for label in labels]
    query_words = {stem(w) for w in _words(p.question)}
    base_clause = re.split(r'[.;]',text[base.end:])[0]
    known_words = {stem(w) for w in _words(base_clause)}
    if all(ws & known_words for ws in label_words) and not any(ws & query_words for ws in label_words):
        return _answer(base.value/first.value/second.value, 'Counted nested subset / both selection fractions')
    if not all(ws & query_words for ws in label_words):
        return None
    # The known count must describe the whole rather than one labelled subset.
    base_tail = re.split(r'[.;,]',text[base.end:])[0]
    if any(_words(label) & _words(base_tail) for label in labels):
        return None
    return _answer(base.value*first.value*second.value, 'Whole x first share x share within that category')


def _fraction_progress(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3 or not _has(r'^how many (?:weeks|days|months)\b',p.question):
        return None
    f = fs[0]
    if not _has(r'\b(?:add|adds|increase)\s*$',p.text[:f.start].lower()):
        return None
    unit = re.match(r'\s+of an? ([a-z]+) each (week|day|month)\b',p.text[f.end:].lower())
    if not unit:
        return None
    amounts = [n for n in p.numbers if n != f]
    targets = [n for n in amounts if _has(r'\b(?:reaches?|until|target|goal)\b[^.;]*$',p.text[:n.start].lower())]
    starts = [n for n in amounts if _has(r'\balready\b[^.;]*$',p.text[:n.start].lower())]
    if len(targets) != 1 or len(starts) != 1 or targets[0] == starts[0]:
        return None
    if any(not re.match(r'[- ]+'+unit.group(1)+r's?\b',p.text[n.end:].lower()) for n in amounts):
        return None
    return _answer((targets[0].value-starts[0].value)/f.value, 'Remaining increase / increase per period')


def _fractional_dozen(p, fs):
    if len(p.numbers) != 3 or not _has(r'\bdozens?\b',p.body):
        return None
    amount, one, count = p.numbers
    if amount.value.denominator == 1 or one.value != 1 or count.value <= 0:
        return None
    m = re.match(r'\s+dozens? ([a-z ]+?) to make\s*$',p.text[amount.end:one.start].lower())
    made = re.match(r'\s+([a-z]+)\b',p.text[one.end:].lower())
    if not m or not made or not re.match(r'\s+'+re.escape(made.group(1))+r's?\b',p.text[count.end:].lower()):
        return None
    if not _words(m.group(1)) & _words(p.question):
        return None
    return _answer(amount.value*12*count.value, 'Dozens per item x twelve x number of items')


def _paired_quantities(p, fs):
    """One explicit amount and a second quantity stated relative to it."""
    if len(fs) != 1 or len(p.numbers) != 2:
        return None
    f = fs[0]
    amount = next(n for n in p.numbers if n != f)
    text = p.text.lower()
    if not amount.start < f.start or not _has(r'\b(?:total|altogether|in all|together|combined)\b', p.question):
        return None
    if _has(r'\b(?:per|each|every|off|lost|sold|gave|ate|remaining)\b',text):
        return None
    tail = text[f.end:len(p.body)]
    if re.match(r'\s+that amount(?: of time)?\b',tail):
        if not _has(r'\b(?:minutes?|hours?|days?)\b',text[amount.end:f.start]):
            return None
        factor = 1+f.value
    elif re.match(r'\s+as many\s+[a-z]+',tail):
        # An unqualified "half as many red ..." refers to the preceding count.
        if _has(r'\bas\b',tail[len(re.match(r'\s+as many',tail).group()):]):
            if not re.match(r'\s+as many as (?:the )?(?:number|amount) of\b',tail):
                return None
            factor = 1+1/f.value
        else:
            factor = 1+f.value
    else:
        return None
    return _answer(amount.value*factor, 'Add the counted quantity and its proportional companion')


def _explicit_transfer(p, fs):
    """A recipient's stock and an explicitly counted share of a giver's stock."""
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    f = fs[0]
    initial, base = [n for n in p.numbers if n != f]
    text = p.text.lower()
    if not initial.start < f.start < base.start or not re.fullmatch(r'\s+of (?:the|his|her|their)\s+',text[f.end:base.start]):
        return None
    if not _has(r'\b(?:have|has|had)\b',p.question) or _has(r'\b(?:left|remain|gave|give)\b',p.question):
        return None
    before = text[initial.end:f.start]
    transfer = re.search(r'\b(?:gave|gives?|put)\b',before)
    after_gift = _has(r'\b(?:gave|gives?) (?:them )?to (?:him|her|them)\b',text[base.end:len(p.body)])
    if not after_gift and (not transfer or not (_has(r'\b(?:him|her|them)\b',before[transfer.end():]) or
                            _has(r"\bin [a-z]+'s\b",text[base.end:len(p.body)]))):
        return None
    iu, bu = _count_unit(p,initial), _count_unit(p,base)
    if iu != bu or iu not in _words(p.question):
        return None
    # Resolve the recipient from either a subject holding the initial stock,
    # or a possessive container in the initial stock's clause.
    stock_clause = re.split(r'[.;!?]',text[:initial.start])[-1]+text[initial.end:].split('.')[0]
    owners = re.findall(r'\b([a-z]+) (?:had|has|have)\b',stock_clause)
    owners += re.findall(r"\b([a-z]+)'s\b",stock_clause)
    query_names = re.findall(r'\b([a-z]+) (?:have|has|had)\b',p.question)
    if query_names and query_names[-1] not in ('he','she','they') and query_names[-1] not in owners:
        return None
    return _answer(initial.value+base.value*f.value, 'Recipient stock plus the incoming fractional gift')


def _daily_share(p, fs):
    if len(fs) != 1:
        return None
    f = fs[0]
    text = p.text.lower()
    if len(p.numbers) == 2:
        price = next(n for n in p.numbers if n != f)
        if price.kind != 'money' or not _has(r'\b(?:each|every) (?:day|night)\b',p.body):
            return None
        container = re.match(r'\s+of an? ([a-z]+)\b',text[f.end:])
        if not container or not _has(r'\beach '+re.escape(container.group(1))+r'\b',p.body):
            return None
        if not _has(r'\b(?:spend|cost|pay)\b',p.question) or not _has(r'\b(?:every|per|each) year\b',p.question):
            return None
        return _answer(f.value*price.value*365,'Daily share x price per whole x days in a year')
    if len(p.numbers) == 3 and _has(r'^how many days\b',p.question):
        amounts = [n for n in p.numbers if n != f]
        first, repeated = amounts
        if first.value != repeated.value or repeated.start < len(p.body):
            return None
        if not _has(r'\beach day\b',text[first.end:f.start]):
            return None
        if not re.match(r'\s+of (?:the )?[a-z ]+? (?:he|she|they) bought\b',text[f.end:]):
            return None
        if not _has(r'\bfinish\b',p.question) or _unit(p,first) != _unit(p,repeated):
            return None
        return _answer(1/f.value,'Whole / fraction of the original whole completed per day')
    return None


def _weight_to_dozen(p, fs):
    if len(fs) != 1 or len(p.numbers) not in (2,3) or not _has(r'\bhow many dozen\b',p.question):
        return None
    f = fs[0]
    text = p.text.lower()
    amounts = [n for n in p.numbers if n != f]
    if len(amounts) == 2:
        if amounts[0].value != amounts[1].value or _unit(p,amounts[0]) != _unit(p,amounts[1]):
            return None
        if not _has(r'\bneeds?\s*$',text[:amounts[1].start]):
            return None
    weight = amounts[0]
    unit = re.match(r'\s+of an? ([a-z]+)\b',text[f.end:])
    if not unit or _unit(p,weight) != unit.group(1) or not _has(r'\bweighs?\s*$',text[:f.start]):
        return None
    return _answer(weight.value/f.value/12,'Required weight / weight per item / twelve')


def _age_when_equal(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    f = fs[0]
    text = p.text.lower()
    left = re.search(r'\b([a-z]+) is\s*$',text[:f.start])
    right = re.match(r'\s+as old as ([a-z]+) who is\s*',text[f.end:])
    amounts = [n for n in p.numbers if n != f]
    if not left or not right or not f.start < amounts[0].start < amounts[1].start:
        return None
    if not _has(r'\bwhen (?:he|she) is\b',text[amounts[0].end:amounts[1].start]):
        return None
    if not _has(r'\b'+re.escape(right.group(1))+r'\b',p.question):
        return None
    current = amounts[0].value*f.value
    if amounts[1].value < current:
        return None
    return _answer(amounts[0].value+amounts[1].value-current,'Both people age by the same number of years')


def _group_capacity(p, fs):
    """Equal groups whose capacity is a fraction of a counted larger group."""
    if len(fs) != 1 or len(p.numbers) not in (3,4):
        return None
    f = fs[0]
    text = p.text.lower()
    if not _has(r'\bcapacity\b',p.body) or not _has(r'\bcombined capacity\b',p.question):
        return None
    amounts = [n for n in p.numbers if n != f]
    count, capacity = amounts[:2]
    if not count.start < f.start < capacity.start or not _has(r'\beach\b',text[count.end:f.start]):
        return None
    if len(amounts) == 3 and (amounts[2].value != count.value or amounts[2].start < len(p.body)):
        return None
    group = _unit(p,count)
    if not _has(r'\b'+re.escape(group)+r'(?:s|es)?\b',p.question):
        return None
    if not re.match(r'\s+as much as\b',text[f.end:]):
        return None
    return _answer(count.value*f.value*capacity.value,'Number of groups x fractional capacity of each')


def _restated_remainder(p, fs):
    """An explicit complementary fraction restates the remainder, then a loss."""
    if len(fs) != 2 or len(p.numbers) != 4:
        return None
    base, used = [n for n in p.numbers if n not in fs]
    first, second = fs
    text = p.text.lower()
    if not base.start < first.start < second.start < used.start or first.value+second.value != 1:
        return None
    if not _has(r'\bof the remaining\s*$',text[:second.start]):
        return None
    if not _has(_LOSS,text[base.end:first.start]) or not _has(_LOSS,text[second.end:used.start]):
        return None
    if not _has(r'\bleft\b',p.question) or _unit(p,base) != _unit(p,used):
        return None
    if not re.match(r'\s+of\b',text[first.end:]) or not re.match(r'\s+of\b',text[second.end:]):
        return None
    return _answer(base.value*second.value-used.value,'Remaining share of the original stock minus the later use')


def _stock_then_companion(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3 or not _has(r'\b(?:together|combined|altogether)\b',p.question):
        return None
    f = fs[0]
    first, added = [n for n in p.numbers if n != f]
    text = p.text.lower()
    if not first.start < added.start < f.start or _unit(p,first) != _unit(p,added):
        return None
    if not _has(_GAIN,text[first.end:added.start]) or _has(_LOSS,text[first.end:f.start]):
        return None
    if not re.match(r'\s+as many (?:total )?'+re.escape(_unit(p,first))+r's?\b',text[f.end:]):
        return None
    return _answer((first.value+added.value)*(1+f.value),'Updated stock plus the companion\'s proportional stock')


def _related_price_total(p, fs):
    if len(fs) != 1 or len(p.numbers) != 2:
        return None
    f = fs[0]
    price = next(n for n in p.numbers if n != f)
    text = p.text.lower()
    if price.kind != 'money' or not _has(r'\b(?:both|total|together|altogether)\b',p.question):
        return None
    ref = re.match(r'\s+(?:the )?(?:price|cost) of (?:the |an? )?([a-z]+)',text[f.end:])
    if not ref or not _has(r'\b'+re.escape(ref.group(1))+r'\b[^.;]*$',text[:price.start]):
        return None
    if _has(r'\b(?:off|discount|more|less|each|per)\b',text):
        return None
    return _answer(price.value*(1+f.value),'Price of the reference item plus the proportional item price')


def _fractional_pay(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    f = fs[0]
    amounts = [n for n in p.numbers if n != f]
    hours = [n for n in amounts if re.match(r'[- ]hours?\b',p.text[n.end:],re.I)]
    pay = [n for n in amounts if n.kind == 'money']
    if len(hours) != 1 or len(pay) != 1 or not _has(r'\b(?:salary|pay|earn|earned)\b',p.question):
        return None
    if not _has(r'\b(?:hourly rate|per hour|an hour)\b',p.body):
        return None
    if not f.start < hours[0].start or not re.fullmatch(r'\s+of (?:her|his|their) usual\s+',p.text[f.end:hours[0].start].lower()):
        return None
    return _answer(f.value*hours[0].value*pay[0].value,'Worked fraction x usual hours x hourly pay')


def _loss_then_purchase(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    f = fs[0]
    first, added = [n for n in p.numbers if n != f]
    text = p.text.lower()
    if not first.start < f.start < added.start or _count_unit(p,first) != _count_unit(p,added):
        return None
    if not _has(_LOSS,text[first.end:f.start]) or not _has(_GAIN,text[f.end:added.start]):
        return None
    if not re.match(r'\s+of (?:them|the|his|her|their)\b',text[f.end:]):
        return None
    if not _has(r'\b(?:total|now|after|left)\b',p.question) or not _has(r'\b(?:has|have)\b',p.question):
        return None
    if _has(r'\b(?:each|per|every|times)\b',text):
        return None
    return _answer(first.value*(1-f.value)+added.value,'Retained share plus the new purchase')


def _money_gap(p, fs):
    if len(fs) != 1 or len(p.numbers) != 2:
        return None
    f = fs[0]
    price = next(n for n in p.numbers if n != f)
    if price.kind != 'money' or not price.start < f.start:
        return None
    if not _has(r'^how much more money\b',p.question) or not _has(r'\bneed\b',p.question):
        return None
    if not re.match(r'\s+of that amount\b',p.text[f.end:],re.I):
        return None
    if not _has(r'\b(?:only has|only have|has money for|have money for)\b',p.text[price.end:f.start].lower()):
        return None
    return _answer(price.value*(1-f.value),'Full cost minus the share already available')


def _fraction_difference(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    f = fs[0]
    a,b = [n for n in p.numbers if n != f]
    if f.start < len(p.body) or not re.match(r'\s+(?:of )?(?:the )?difference\b',p.text[f.end:],re.I):
        return None
    if a.kind != b.kind or (a.kind != 'money' and _count_unit(p,a) != _count_unit(p,b)):
        return None
    if _has(r'\b(?:each|per|every|times|more|less)\b',p.body):
        return None
    return _answer(abs(a.value-b.value)*f.value,'Difference of the counted amounts x requested fraction')


def _grouped_time_share(p, fs):
    if len(fs) != 1 or len(p.numbers) not in (3,4):
        return None
    f = fs[0]
    text = p.text.lower()
    amounts = [n for n in p.numbers if n != f]
    count,duration = amounts[:2]
    if not f.start < count.start < duration.start:
        return None
    if len(amounts) == 3 and (amounts[2].value != count.value or amounts[2].start < len(p.body)):
        return None
    period = re.match(r'[- ]minute ([a-z]+)\b',text[duration.end:])
    if not period or text[count.end:duration.start].strip():
        return None
    if not _has(r'^how many minutes\b',p.question) or not _has(r'\b(?:whole|total|all)\b',p.question):
        return None
    label = re.search(r'\bspent on ([a-z ]+)',text[f.end:count.start])
    if not label or not _words(label.group(1)) & _words(p.question):
        return None
    return _answer(count.value*duration.value*f.value,'Number of equal periods x minutes per period x selected share')


def _measurement_scale(p, fs):
    if len(p.numbers) != 3 or not fs:
        return None
    source, actual, requested = p.numbers
    text = p.text.lower()
    if not _has(r'\brepresents?\s*$',text[source.end:actual.start]):
        return None
    if _unit(p,source) != _unit(p,requested) or _unit(p,actual) not in _words(p.question):
        return None
    if source.value <= 0 or not _has(r'\b(?:actual|real)\b',p.question):
        return None
    return _answer(actual.value*requested.value/source.value,'Requested measurement / reference measurement x represented distance')


def _nested_value(p, fs):
    if len(fs) != 2 or len(p.numbers) != 3:
        return None
    price = next(n for n in p.numbers if n not in fs)
    first,second = fs
    text = p.text.lower()
    if price.kind != 'money' or not first.start < second.start < price.start:
        return None
    if not re.match(r'\s+of (?:his|her|their|the) share\b',text[second.end:]):
        return None
    if not _has(r'\b(?:worth|value|cost)\b',p.question) or not _has(r'\b(?:entire|whole)\b',p.question):
        return None
    if not _has(r'\b(?:sold|sell|cost|worth)\b',text[first.end:price.start]):
        return None
    return _answer(price.value/first.value/second.value,'Value of the nested share / both ownership fractions')


def _counted_rest(p, fs):
    if len(fs) != 1 or len(p.numbers) != 2:
        return None
    f = fs[0]
    price = next(n for n in p.numbers if n != f)
    text = p.text.lower()
    if price.kind != 'money' or price.start < f.end or not _has(r'\b(?:original|initial|at first)\b',p.question):
        return None
    rest = re.search(r'\bthe rest on (?:an? |the )?([a-z]+)',text[f.end:price.start])
    if not rest or not _has(r'\b'+re.escape(rest.group(1))+r'\b[^.;]*\bcost\b',text[f.end:price.start]):
        return None
    if not _has(r'\b(?:spent|spends?)\s*$',text[:f.start]):
        return None
    return _answer(price.value/(1-f.value),'Counted cost of the rest / complementary share')


def _enumerated_groups(p, fs):
    if len(fs) != 1 or len(p.numbers) != 2:
        return None
    f = fs[0]
    base = next(n for n in p.numbers if n != f)
    text = p.text.lower()
    if base.start > f.start or not _has(r'\bdivided into equal groups\b',p.body):
        return None
    enum = re.search(r'\beither ([^.;]+)',text[base.end:f.start])
    if not enum:
        return None
    groups = [s.strip(' ,') for s in re.split(r',|\bor\b|\band\b',enum.group(1)) if s.strip(' ,')]
    if not 2 <= len(groups) <= 8 or any(not re.fullmatch(r'[a-z]+(?: [a-z]+){0,2}',g) for g in groups):
        return None
    target = re.match(r'\s+of the (.+?) (?:ones|group)\b',text[f.end:])
    actor = re.search(r'\b([a-z]+) (?:takes?|took|uses?|used)\s*$',text[:f.start])
    if not target or target.group(1) not in groups or not actor or not _has(r'\b'+actor.group(1)+r'\b',p.question):
        return None
    if _has(r'\b(?:left|remaining|rest)\b',p.question):
        return None
    return _answer(base.value/len(groups)*f.value,'Whole / enumerated equal groups x fraction taken from one group')


def _priced_remainder(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    f = fs[0]
    base,price = [n for n in p.numbers if n != f]
    text = p.text.lower()
    if not base.start < f.start < price.start or price.kind != 'money':
        return None
    rest = re.search(r'\bthe rest are ([a-z]+)',text[f.end:price.start])
    if not rest or _singular(rest.group(1)) not in _words(p.question):
        return None
    if not _has(r'\b(?:cost|pay|spend)\b',p.question):
        return None
    if not re.match(r'\s+per '+re.escape(_unit(p,base))+r'\b',text[price.end:]):
        return None
    return _answer(base.value*(1-f.value)*price.value,'Remaining population x stated cost per member')


def _current_proportional_age(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3 or not _has(r'\bnow\b',p.question):
        return None
    f = fs[0]
    age,elapsed = [n for n in p.numbers if n != f]
    text = p.text.lower()
    left = re.search(r'\b([a-z]+) is\s*$',text[:f.start])
    if not left or not _has(r'\b'+left.group(1)+r'\b',p.question):
        return None
    if not re.match(r'\s+(?:the )?age of\b',text[f.end:]) or not f.start < age.start < elapsed.start:
        return None
    if not _has(r'\bwill turn\s*$',text[:age.start]) or not re.fullmatch(r'\s+after\s+',text[age.end:elapsed.start]):
        return None
    if not re.match(r'\s+years?\b',text[elapsed.end:]):
        return None
    return _answer((age.value-elapsed.value)*f.value,'Compared future age minus elapsed years, then apply the current ratio')


def _actor_consumption(p, fs):
    """A counted group collectively consumes one fraction of a stated stock."""
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    f = fs[0]
    base,actors = [n for n in p.numbers if n != f]
    text = p.text.lower()
    if not base.start < actors.start < f.start or not _has(r'\b(?:left|remain|remaining)\b',p.question):
        return None
    if _has(r'\b(?:each|per|every|more|less|than|times)\b',text):
        return None
    if not re.fullmatch(r'\s+[a-z]+\s+(?:eat|ate|use|used|consume|consumed)\s+',text[actors.end:f.start]):
        return None
    tail = re.match(r'\s+of the ([a-z]+)\b',text[f.end:])
    if not tail or _singular(tail.group(1)) != _count_unit(p,base):
        return None
    return _answer(base.value*(1-f.value),'Original stock minus the fraction collectively consumed')


def solve(problem):
    if not has_fraction(problem.text) or any(n.kind == 'percent' for n in problem.numbers):
        return None
    p = _prepare(problem)
    if p is None:
        return None
    fs = _fractions(p)
    for reader in (_inverse_stock, _relations, _recipe_mixture, _measured_per_person,
                   _scoped_categories, _fraction_progress, _fractional_dozen,
                   _paired_quantities, _explicit_transfer, _daily_share,
                   _weight_to_dozen, _age_when_equal, _group_capacity,
                   _restated_remainder, _stock_then_companion,
                   _related_price_total, _fractional_pay, _loss_then_purchase,
                   _money_gap, _fraction_difference, _grouped_time_share,
                   _measurement_scale, _nested_value, _counted_rest,
                   _enumerated_groups, _priced_remainder, _current_proportional_age,
                   _actor_consumption):
        result = reader(p,fs)
        if result is not None:
            monetary = (_inverse_stock, _relations, _daily_share,
                        _related_price_total, _fractional_pay, _money_gap,
                        _fraction_difference, _nested_value, _counted_rest,
                        _priced_remainder)
            money = [n for n in p.numbers if n.kind == 'money']
            if reader in monetary and money:
                # Keep the requested currency and scope in the explanation.
                # The runtime recognises a monetary answer by its units.
                symbol = next((c for c in money[0].raw if c in '$£€'), '$')
                unit = {'$':'dollars','£':'pounds','€':'euros'}[symbol]
                scope = re.search(r'\b(?:for|on)\s+([^?]+)',p.question)
                label = 'Amount for '+scope.group(1).strip() if scope else 'Amount of money'
                value,working = result
                result = value, working+' '+label+': '+format_number(value)+' '+unit+'.'
            return result
    return None
