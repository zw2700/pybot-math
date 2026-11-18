"""Exact fraction relations and explicitly scoped allocations.

The readers require an identified base, an understood operation for every
quantity, and an explicit requested result. Unsupported stories abstain.
"""
import re
from fractions import Fraction
from dataclasses import replace

from ._fractions_common import (
    _has, _answer, has_fraction, normalize_fractions, normalize_magnitudes,
)
from ..numbers import read_numbers, format_number
from ..problem import Problem, ASK
from .comparisons_r01_a2 import _names, _mentions, _noun
from .counting_and_totals_r00_a1 import _singular
from .counting_and_totals_r02_a2 import _unit, _asked, _conversion
from .percentages_r02_a3 import _nested, _single_subset, _selection, _labels


def _prepare(p):
    text = normalize_magnitudes(p.text)
    text = re.sub(r'\$\.(?=\d)', '$0.', text)
    text = re.sub(r'\ba dozen\b', '1 dozen', text, flags=re.I)
    # Local spelling support; the shared number reader and offsets stay intact.
    text = re.sub(r'\bone and half\b', 'one and a half', text, flags=re.I)
    text = normalize_fractions(text, basic=False)
    text = re.sub(r'\b(twice|thrice|double|triple)\b',
                  lambda m: '2 times' if m.group().lower() in ('twice', 'double') else '3 times', text, flags=re.I)
    return Problem.read(text)


def _tokenize(p):
    t = p.text.lower()
    for i, n in reversed(list(enumerate(p.numbers))):
        t = t[:n.start] + 'Q' + str(i) + t[n.end:]
    return t


def _graph(edges, known):
    nodes = {n for a, b, s, d in edges for n in (a, b)}
    if not 2 <= len(nodes) <= 5:
        return None
    values = {}
    for name, value in known:
        if name in values and values[name] != value:
            return None
        values[name] = value
    for _ in nodes:
        for a, b, s, d in edges:
            if b in values:
                value = s*values[b]+d
                if a in values and values[a] != value:
                    return None
                values[a] = value
            elif a in values and s:
                values[b] = (values[a]-d)/s
    if set(values) != nodes or any(v < 0 for v in values.values()):
        return None
    return values


def _comparisons(p, return_values=False):
    """Named affine relations, including fractions and chained comparisons."""
    text = _tokenize(p)
    if _has(r'\b(?:per|ago|left|remaining|average|fast|faster|speed|spent|returned)\b', text):
        return None
    names = _names(p.text[:len(p.body)])
    # Days can serve as entities even when they are not sentence subjects.
    names = [n for n in names if n not in ('how', 'what', 'one afternoon')]
    category_relations = []
    if len(names) < 2:
        for m in re.finditer(r'Q(\d+)\s+(?:times\s+)?as (?:many|much) (.+?) as ([a-z ]+?)(?=[.;]|\s+and\s+Q|$)', text):
            a, b = _noun(m.group(2)), _noun(m.group(3))
            if not a or not b or a == b:
                return None
            category_relations.append((a, b))
        names = list(dict.fromkeys(n for pair in category_relations for n in pair))
    if len(names) < 2:
        return None
    cue = list(ASK.finditer(text))[-1]
    body, query = text[:cue.start()], text[cue.start():]
    # Split coordinated subjects, while preserving names on the RHS of a relation.
    start_name = '|'.join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    clauses = re.split(r'[.;!?]|,?\s+but\s+|\s+and\s+(?=(?:(?:his|her|their) (?:friend|cousin|sister|brother) )?(?:' + start_name + r")(?:'s)?\s+(?:has|have|had|is|was|worked|threw|climbed|drove|fell|sees|ate|collected|picked|bought|ran|runs|scored)\b)", body)
    if category_relations:
        clauses = [re.sub(r'^there are ', '', c) for c in re.split(r'[.;!?]|\s+and\s+(?=Q)', body)]
    # An if-clause in the question may contain the numeric anchor.
    clauses += re.split(r'\bif\b', query)[1:]
    edges, used = [], set()
    anchor_subject = None
    previous_subject = None
    for ci, clause in enumerate(clauses):
        mults = list(re.finditer(r'Q(\d+)\s+(?:times\s+)?(?:'
            r'as (?:many|much|old|long)(?:\s+[a-z]+){0,9}?\s+as\s+|'
            r'as long\b\s*|(?:of\s+)?(?:the\s+)?(?:number|amount|age|cost|distance|length|weight|height)(?:\s+of)?\s+|'
            r'(?:of\s+)?that (?:amount|length)\b\s*|what\s+|of\s+)', clause))
        # Elliptic comparisons may omit the final 'as' or 'of'.
        if not mults:
            mults = list(re.finditer(r'Q(\d+)\s+(?:times\s+)?(?:as many [a-z ]+?(?= and|$)|(?:the )?[a-z]+ (?=(?:' + start_name + r') (?:has|have|had)\b))', clause))
        # Match a fraction immediately modifying a named possessive, e.g. half R's age.
        if not mults:
            mults = list(re.finditer(r'Q(\d+)\s+(?=(?:' + start_name + r")(?:'s)\b)", clause))
        adds = [] if mults else list(re.finditer(r'Q(\d+)\s+(?!times\b)(?:[a-z]+\s+){0,2}?(more|less|fewer|older|younger|taller|shorter)\b(?:\s+(?:[a-z]+\s+){0,6}?than\s+)?', clause))
        matches = mults or adds
        for m in matches:
            i = int(m.group(1))
            before, after = clause[:m.start()], clause[m.end():]
            lefts, rights = _mentions(before, names), _mentions(after, names)
            left = lefts[-1] if lefts else previous_subject
            if category_relations:
                category = re.search(r'as (?:many|much) (.+?) as', m.group())
                left = _noun(category.group(1)) if category else None
            if not left:
                return None
            right = rights[0] if rights else None
            # A relative quantity explicitly referring to "that amount" uses
            # the preceding entity; an unqualified "as long" shares the anchor.
            if right is None:
                right = previous_subject if _has(r'\bthat (?:amount|length)\b', m.group()) else anchor_subject
            if not right or left == right:
                return None
            scale, delta = (p.numbers[i].value, Fraction(0)) if mults else (Fraction(1), p.numbers[i].value)
            used.add(i)
            if adds and m.group(2) in ('less', 'fewer', 'younger', 'shorter'):
                delta = -delta
            if mults:
                adjustment = re.search(r'Q(\d+)\s+(?:[a-z]+\s+){0,2}?(more|less|fewer)(?:\s+[a-z]+){0,5}?\s+than\s*$', before)
                if adjustment:
                    di = int(adjustment.group(1))
                    delta = p.numbers[di].value * (-1 if adjustment.group(2) != 'more' else 1)
                    used.add(di)
            if scale <= 0:
                return None
            edges.append((left, right, scale, delta))
            previous_subject = left
        if not matches:
            mentions = _mentions(clause, names)
            if mentions and re.search(r'Q\d+', clause):
                previous_subject = mentions[-1]
                if anchor_subject is None:
                    anchor_subject = previous_subject
    if not edges:
        return None
    nodes = {n for a, b, s, d in edges for n in (a, b)}
    known = []
    for i, n in enumerate(p.numbers):
        if i in used:
            continue
        tok = 'Q' + str(i)
        containing = [c for c in clauses if re.search(r'\b' + tok + r'\b', c)]
        # Explicit count of the queried participants is a label, not an amount.
        if tok in query and not containing and n.value == len(nodes) and _has(r'^\s+(?:people|persons|men|women|of them)\b', text.split(tok)[-1]):
            continue
        # Sentence introductions such as "One Monday" or "One afternoon".
        if n.value == 1 and _has(r'^\s+(?:afternoon|morning|day|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', p.text[n.end:].lower()):
            continue
        if len(containing) == 1 and n.value == len(nodes) and _has(r'^\s+(?:people|persons|players|friends|children)\b', text.split(tok)[-1]) and not _mentions(containing[0], list(nodes)):
            continue
        if len(containing) != 1:
            return None
        clause = containing[0]
        if any(re.search(r'\bQ' + str(j) + r'\b', clause) for j in used):
            return None
        before, after = clause.split(tok)
        owners = _mentions(before, list(nodes))
        if not owners:
            owners = _mentions(after, list(nodes))
        if not owners:
            return None
        owner = owners[-1] if _mentions(before, list(nodes)) else owners[0]
        value = n.value * (12 if _has(r'^\s+dozen\b', after) else 1)
        known.append((owner, value))
    solved = _graph(edges, known)
    if solved is None:
        return None
    if return_values:
        return solved
    requested = re.split(r'\bif\b', query)[0]
    asked = list(dict.fromkeys(_mentions(requested, list(nodes))))
    if _has(r'\b(?:more|less|fewer|difference)\b', requested):
        if len(asked) != 2:
            if _has(r'\b(?:heaviest|largest|greatest|highest|oldest|tallest)\b', requested) and _has(r'\b(?:lightest|smallest|lowest|youngest|shortest)\b', requested):
                return _answer(max(solved.values())-min(solved.values()), 'Largest amount minus smallest amount')
            return None
        answer = solved[asked[0]]-solved[asked[1]]
        if _has(r'\bdifference\b', requested):
            answer = abs(answer)
        elif _has(r'\b(?:less|fewer)\b', requested):
            answer = -answer
    elif _has(r'\b(?:total|together|altogether|combined|in all|sum)\b', requested):
        weekdays = ('monday','tuesday','wednesday','thursday','friday','saturday','sunday')
        span = re.search(r'\bfrom (' + '|'.join(weekdays) + r') to (' + '|'.join(weekdays) + r')\b', requested)
        if span and all(n in weekdays for n in nodes):
            begin, end = (weekdays.index(d) for d in span.groups())
            asked = [weekdays[i % 7] for i in range(begin, begin+(end-begin) % 7+1)]
            if any(d not in solved for d in asked):
                return None
        answer = sum((solved[n] for n in (asked if len(asked) > 1 else nodes)), Fraction(0))
    elif len(asked) == 1:
        answer = solved[asked[0]]
    else:
        return None
    return _answer(answer, '; '.join(n + ' = ' + format_number(solved[n]) for n in sorted(solved)))


_REMOVE = r'\b(?:ate|eats?|eaten|used|uses?|spent|spends?|gave|gives?|given|sold|sells?|drank|drinks?|lost|loses?|donated|donates?|made|make|arrived|shipped|ships?|distributed|distributes?|removed|removes?|are|were|is|was|received|taken|completed|finished|relocated|relocates?|buy|buys|bought|adds?|added)\b'


def _allocations(p):
    """A stock, explicit allocations of its whole or remainder, and a query."""
    ns = list(p.numbers)
    text = p.text.lower()
    # A literal addition changes the base of a subsequent share. This reader
    # treats literal amounts as removals; leave mixed ledgers to another skill.
    if _has(r'\b(?:adds?|added)\b', text):
        return None
    # Elapsed-day labels can repeat the described sequence length.
    if ns and ns[-1].start >= len(p.body) and re.match(r'\s+days?\b', text[ns[-1].end:]) and _has(r'\bafter\s*$', text[:ns[-1].start]):
        stages = len([n for n in ns if 0 < n.value < 1 and n.kind != 'money'])
        labels = set(re.findall(r'\b(first|second|third|fourth|fifth) day\b', p.body))
        if ns[-1].value != stages or len(labels) != stages:
            return None
        ns.pop()
    fractions = [n for n in ns if 0 < n.value < 1 and n.kind != 'money']
    if not fractions or not _has(r'\b(?:left|remain|remaining|rest|not|non-|unspent|unsold)\b', text):
        return None
    if _has(r'\b(?:more|less|than|twice|average|profit|interest)\b', text):
        return None
    if not 2 <= len(ns) <= 6 or any(n.start >= len(p.body) for n in ns):
        return None
    # Establish the initial quantity, optionally from explicit identical groups.
    base, used = None, set()
    amounts = [n for n in ns if n not in fractions]
    if not amounts:
        return None
    first = amounts[0]
    stock_unit = _unit(p, first)
    converted = False
    if first.start < fractions[0].start:
        base, used = first.value * (12 if re.match(r'\s+dozen\b', text[first.end:]) else 1), {id(first)}
        if len(amounts) > 1:
            second = amounts[1]
            middle = text[first.end:second.start]
            tail = text[second.end:]
            if second.start < fractions[0].start and (_has(r'\b(?:each|apiece)\b', re.split(r'[.;]', tail)[0]) or _has(r'\binto\b', middle)):
                base *= second.value
                used.add(id(second))
                stock_unit = _unit(p, second)
    else:
        # "a fraction ... N batches of M each".
        if len(amounts) == 2 and _has(r'\b(?:batches|boxes|packs|groups|bags) of\s*$', text[amounts[0].end:amounts[1].start]) and _has(r'\beach\b', text[amounts[1].end:len(p.body)]):
            base = amounts[0].value*amounts[1].value
            stock_unit = _unit(p, amounts[1])
            used.update(id(n) for n in amounts)
    initial_removed = Fraction(0)
    originals = [n for n in amounts if _has(r'\boriginally\b[^.;]*$', text[max(0, text.rfind('.', 0, n.start)+1):n.start])]
    if len(originals) == 1 and originals[0] != first and len(amounts) == 2:
        base = originals[0].value
        initial_removed = first.value
        used.update(id(n) for n in amounts)
    if len(amounts) >= 2 and re.fullmatch(r'\s+of\s+', text[amounts[0].end:amounts[1].start]):
        base = amounts[1].value
        initial_removed = amounts[0].value
        used.update(id(n) for n in amounts[:2])
    if base is None or base <= 0:
        return None
    remaining, last_part = base-initial_removed, None
    operations = []
    pending = [n for n in ns if id(n) not in used]
    for index, n in enumerate(pending):
        before = text[pending[index-1].end if index else first.end:n.start]
        end = pending[index+1].start if index+1 < len(pending) else len(p.body)
        tail = text[n.end:end]
        if n in fractions:
            if not re.match(r'\s+(?:of|the|that|this|his|her|their|are|were|is|was|have|had)\b|\s*[,.;]', tail):
                return None
            if not _has(_REMOVE, before + ' ' + tail):
                return None
            scope = re.split(r'[.;!?]|\s+and\s+', tail)[0]
            scoped_remaining = _has(r'\b(?:remaining|remainder|rest|what (?:was|is) left|(?:has|have|had) left)\b', scope)
            scoped_original = _has(r'\b(?:original|initial)\b', scope)
            # Further fractions must explicitly name their scope.
            if last_part is not None and not scoped_remaining and not scoped_original:
                return None
            part = (remaining if scoped_remaining else base)*n.value
            credits = list(re.finditer(r'\b(buys?|bought|adds?|added|ate|eats?|used|uses?|spent|spends?|gave|gives?|sold|sells?|drank|drinks?|lost|loses?)\b', before))
            credit = credits and credits[-1].group() in ('buy','buys','bought','add','adds','added')
            if credit:
                remaining += part
            elif last_part is None and _has(r'\b(?:received|receives|got|gets)\s*$', before):
                remaining = part
            else:
                remaining -= part
            last_part = part
            operations.append(('add ' if credit else 'retain ' if last_part == part and remaining == part and _has(r'\b(?:received|receives|got|gets)\s*$', before) else 'subtract ') + format_number(part))
        else:
            # An explicit repeated original amount is a base reference.
            if n.value == base and _has(r'\boriginal\s*$', before):
                continue
            # A per-output consumption converts the final remaining stock.
            if index == len(pending)-1 and _has(r'\b(?:per|each)\b', tail) and _has(r'\b(?:needs?|requires?)\b', before):
                denominator = re.search(r'\b(?:per|each)\s+(?:an? )?([a-z]+)', tail)
                if n.value <= 0 or not denominator or _asked(p) not in (_singular(denominator.group(1)), _singular(denominator.group(1)+'s')):
                    return None
                converted = True
                remaining /= n.value
                if p.question.startswith('how many') and _has(r'\b(?:can|able|whole)\b', p.question) and _asked(p) not in ('second','minute','hour','day','week','month','year','gram','kilogram','pound','ounce','liter','milliliter','meter','centimeter','kilometer','foot','inch','mile'):
                    remaining = Fraction(remaining.numerator // remaining.denominator)
                operations.append('divide by ' + format_number(n.value))
                continue
            if not _has(_REMOVE, before + ' ' + tail) and not _has(r'\band another\s*$', before):
                return None
            if _unit(p, n) != _unit(p, first) and not re.match(r'\s+additional\s+' + re.escape(_unit(p, first)) + r'(?:s|ren)?\b', text[n.end:]):
                return None
            remaining -= n.value
            operations.append('subtract ' + format_number(n.value))
        if remaining < 0:
            return None
    q = p.question
    remainder_query = _has(r'\b(?:left|remain|remained|remaining|not|non-|unspent|unsold|rest)\b', q)
    rest_label = re.search(r'\b(?:the rest|remainder)\b[^.;]*\b(?:make|for|are|is|were|was)\s+(.+?)[.;]', p.body)
    if rest_label and set(re.findall(r'[a-z]+', rest_label.group(1))) & set(q.split()):
        remainder_query = True
    rest_owner = re.search(r"\b([a-z]+) (?:was|is) (?:responsible for the rest|left with what(?:'s| is) left)\b", p.body)
    if rest_owner and _has(r'\b' + re.escape(rest_owner.group(1)) + r'\b', q):
        remainder_query = True
    if _has(r'\b(?:have|has)\b.*\b(?:end|now)\b', q):
        remainder_query = True
    if not remainder_query:
        return None
    source, dest = stock_unit, _asked(p)
    if source == 'hour' and _has(r'\bminutes\b', q):
        remaining *= 60
        operations.append('convert hours to minutes')
    elif not converted and source != dest and source in ('second','minute','hour','day','week','month','year','gram','kilogram','pound','ounce','liter','milliliter','meter','centimeter','kilometer','foot','inch','mile') and dest:
        remaining = _conversion(remaining, source, dest)
        if remaining is None:
            return None
        operations.append('convert to ' + dest)
    return _answer(remaining, 'Start with ' + format_number(base) + '; ' + '; '.join(operations))


def _fixed_budget(p):
    """Several fractions explicitly spent from one original budget."""
    text, ns = p.text.lower(), p.numbers
    fs = [n for n in ns if 0 < n.value < 1 and n.kind != 'money']
    amounts = [n for n in ns if n not in fs]
    if not 1 <= len(fs) <= 3 or len(amounts) != 1:
        return None
    total = amounts[0]
    if _has(r'\b(?:annual|annually|yearly|year)\b', p.question) and _has(r'\b(?:month|monthly)\b', p.body):
        return None
    if _has(r'\b(?:remaining|remainder|what was left|more|less|than|each|per)\b', text):
        return None
    if not all(_has(r'^\s+of (?:his|her|their|the|its|a) (?:budget|money|income|salary|allowance|total)\b', text[n.end:]) for n in fs):
        return None
    if not _has(r'\b(?:spends?|spent|uses?|used|gave|gives?)\b', p.body):
        return None
    rest = re.search(r'\bthe rest\b([^.;]+)', p.body)
    if not rest:
        return None
    stop = set('of his her their the its budget money on for to in is are was were and'.split())
    labels = set(re.findall(r'[a-z]+', rest.group(1))) - stop
    if not labels.intersection(re.findall(r'[a-z]+', p.question)) and not _has(r'\b(?:left|rest)\b', p.question):
        return None
    value = total.value*(1-sum((n.value for n in fs), Fraction(0)))
    return _answer(value, 'Original budget minus its stated allocations')


def _share_gap(p):
    """Keep a fraction and distribute the remainder equally; compare shares."""
    ns, text = p.numbers, p.text.lower()
    fs = [n for n in ns if 0 < n.value < 1 and n.kind != 'money']
    amounts = [n for n in ns if n not in fs]
    if len(fs) != 1 or len(amounts) != 2:
        return None
    if not _has(r'\bkeep\b', p.body) or not _has(r'\b(?:divide|split|distribute)\b.*\b(?:remaining|rest|remainder)\b.*\b(?:among|between)\b', p.body):
        return None
    if not _has(r'\bhow (?:many|much) more\b.*\bthan\b', p.question):
        return None
    total, count = amounts
    # The second amount must explicitly count the recipients.
    unit = _unit(p, count)
    if unit not in ('sibling', 'friend', 'child', 'person', 'worker', 'classmate', 'brother', 'sister') or count.value <= 0:
        return None
    if not re.search(r'\b' + re.escape(unit) + r'(?:s|ren)?\b', p.body[fs[0].end:]):
        return None
    kept = total.value*fs[0].value
    return _answer(kept-total.value*(1-fs[0].value)/count.value, 'Kept share minus one equal share of the remainder')


def _grouped_price_share(p):
    """Identical packages, a unit price, and a stated fraction of the bill."""
    ns, text = p.numbers, p.text.lower()
    fs = [n for n in ns if 0 < n.value < 1 and n.kind != 'money']
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n not in fs and n not in money]
    if len(fs) != 1 or len(money) != 1 or len(counts) != 2:
        return None
    a, b = counts
    if not a.start < b.start < money[0].start < fs[0].start:
        return None
    if not _has(r'^\s+(?:packs?|packages?|boxes|bags|batches)\b', text[a.end:]):
        return None
    if not _has(r'\beach\b', text[b.end:money[0].start]) or not _has(r'\b(?:each|per)\b', text[b.end:money[0].start]):
        return None
    if not _has(r'\b(?:pay|paid|spend|spent|cost)\b', p.question):
        return None
    share = fs[0].value
    payer = re.search(r"\b(?:his|her|their) (?:friend|brother|sister|parent) pays for\s*$", text[:fs[0].start])
    if payer:
        share = 1-share
    elif not _has(r'\b(?:pays? for|pays?|paid)\s*$', text[:fs[0].start]):
        return None
    return _answer(a.value*b.value*money[0].value*share, 'Packages times items per package times unit price times the payable share')


def _coin_share(p):
    """A coin collection valued in dollars, a relative share, and added coins."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 3:
        return None
    money, f, added = ns
    if money.kind != 'money' or not 0 < f.value < 1 or added.kind != 'number':
        return None
    coin = re.search(r"^\s+worth of (pennies|nickels|dimes|quarters)\b", text[money.end:])
    if not coin or not re.match(r'\s+(?:that amount|as many)\b', text[f.end:]):
        return None
    if not _has(r'\b(?:finds?|found|gets?|received|adds?)\s*$', text[f.end:added.start]) or not _has(r'\b' + coin.group(1) + r'\b', text[added.end:]):
        return None
    if not _has(r'\b' + coin.group(1) + r'\b', p.question):
        return None
    cents = {'pennies': 1, 'nickels': 5, 'dimes': 10, 'quarters': 25}[coin.group(1)]
    return _answer(money.value*100/cents*f.value+added.value, 'Convert the collection value to coins, take the stated share, then add the found coins')


def _fraction_subsets(p):
    """Reuse subset selection semantics: a fraction and a percent are ratios."""
    ns = p.numbers
    fs = [n for n in ns if 0 < n.value < 1 and n.kind != 'money']
    if not fs or _has(r'\b(?:times|as many|as much|that amount|per|each|more|less|than)\b', p.text.lower()):
        return None
    # A running remainder is a ledger, not a nested category. Likewise a
    # comparison of two named distances is not a share of their combined total.
    if _has(r'\b(?:remaining|remainder|(?:has|have|had) left)\b', p.body):
        return None
    if _has(r'\b(?:distance|amount|number) that [a-z]+ (?:ran|read|has|had|made)\b', p.body):
        return None
    if _has(r'\b(?:triples|tripled|doubles|doubled|increases?|increased|decreases?|decreased)\b', p.body):
        return None
    result = _nested(p, ns)
    if result is not None:
        return result
    if len(fs) != 1 or len(ns) != 2:
        return None
    f = fs[0]
    # It must be a share of a collection, not a physical fractional measure.
    if not re.match(r'\s+(?:of|the|were|are|had)\b', p.text[f.end:].lower()):
        return None
    ratios = [replace(n, kind='percent') if n in fs else
              replace(n, value=n.value*12) if re.match(r'\s+dozens?\b', p.text[n.end:].lower()) else n
              for n in ns]
    return _single_subset(p, ratios)


def _grouped_subset(p):
    """A fraction of an explicitly grouped population or collection."""
    ns, text = p.numbers, p.text.lower()
    fs = [n for n in ns if 0 < n.value < 1 and n.kind != 'money']
    money = [n for n in ns if n.kind == 'money']
    counts = [n for n in ns if n not in fs and n not in money]
    if len(fs) != 1 or len(counts) != 2 or len(money) > 1 or any(n.kind != 'number' for n in counts):
        return None
    a, b = counts
    if not a.start < b.start or _has(r'\b(?:more|less|than|per|times)\b', text):
        return None
    group = _unit(p, a)
    if not group or not (_has(r'\beach ' + re.escape(group) + r'\b', text[a.end:b.start]) or re.match(r'\s+(?:[a-z]+\s+){1,3}each\b', text[b.end:])):
        return None
    rate = fs[0]
    label = _labels(text, rate)
    choice = _selection(label, p.question, p.body)
    if _has(r'\b(?:left|remain|remaining|not)\b', p.question) and _has(r'\b(?:watched|ate|used|sold|gave|drank)\b', text[a.end:]):
        choice = -1
    if _has(r'\b(?:unseated|unoccupied|empty|vacant)\b', label) and _has(r'\b(?:taken|occupied|seated|used)\b', p.question):
        choice = -1
    multiplier = Fraction(1)
    if money:
        price = money[0]
        if not _has(r'\b(?:earn|earned|revenue|make)\b', p.question) or _has(r'\bprofit\b', p.question):
            return None
        if not (_has(r'\b(?:ticket|item|seat|product) costs?\s*$', text[:price.start]) or re.match(r'\s+(?:each|per)\b', text[price.end:])):
            return None
        if not _has(r'\b(?:sold|sells?|sell)\b', label):
            return None
        multiplier = price.value
        choice = 1
    if choice == 0:
        return None
    return _answer(a.value*b.value*(rate.value if choice == 1 else 1-rate.value)*multiplier, 'Groups times quantity per group times the requested share and unit price')


def _fraction_daily(p):
    """Two explicitly daily fractional measurements over separate durations."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) == 5 and ns[-1].start >= len(p.body) and ns[-1].value == 2 and re.match(r'\s+(?:girls|boys|people|of them)\b', text[ns[-1].end:]):
        ns = ns[:-1]
    if len(ns) != 4 or not _has(r'\b(?:together|altogether|total|combined)\b', p.question):
        return None
    terms = []
    for f, days in (ns[:2], ns[2:]):
        if not 0 < f.value < 1 or not re.match(r'\s+days?\b', text[days.end:]):
            return None
        if not _has(r'\b(?:each|per|every|a) day\b', text[f.end:days.start]):
            return None
        unit = re.match(r'\s+of an? ([a-z]+)\b', text[f.end:])
        if not unit or _singular(unit.group(1)) != _asked(p):
            return None
        terms.append(f.value*days.value)
    return _answer(sum(terms, Fraction(0)), 'Sum of each daily quantity times its stated number of days')


def _flat_partition(p):
    """One fraction and another counted category, asking for the rest."""
    ns, text = p.numbers, p.text.lower()
    fs = [n for n in ns if 0 < n.value < 1 and n.kind != 'money']
    counts = [n for n in ns if n not in fs]
    if len(fs) != 1 or len(counts) != 2:
        return None
    if _has(r'\b(?:each|per|times|more|less|than|remaining)\b', p.body):
        return None
    rest = re.search(r'\b(?:the |all of the )?rest\b([^.;]*)', p.body)
    if not rest:
        return None
    label_words = set(re.findall(r'[a-z]+', rest.group(1))) - set('are is were was all except for that of the and'.split())
    if not label_words.intersection(p.question.split()) and not _has(r'\b(?:rest|left|remaining)\b', p.question):
        return None
    totals = []
    for n in counts:
        prefix = re.split(r'[.;!?]', text[:n.start])[-1]
        if _has(r'\b(?:has|have|had|picked|collected|bought)\s*$', prefix) and not _has(r'\b(?:except|rest|gave|sold|used)\b', prefix):
            totals.append(n)
    if len(totals) != 1:
        return None
    total = totals[0]
    other = counts[1] if counts[0] == total else counts[0]
    if _unit(p, total) != _unit(p, other):
        # "except for N that are green" elides the repeated object noun.
        if not (_has(r'\bexcept for\s*$', text[:other.start]) and re.match(r'\s+that (?:are|were)\b', text[other.end:])):
            return None
    if not re.match(r'\s+of\b', text[fs[0].end:]):
        return None
    return _answer(total.value*(1-fs[0].value)-other.value, 'Whole minus its fractional category minus the other counted category')


def _ordinal_comparisons(p):
    """Treat explicitly indexed objects or days as comparison-graph entities."""
    text = p.text
    lower = text.lower()
    labels = ('first', 'second', 'third', 'fourth', 'fifth')
    present = [w for w in labels if _has(r'\b(?:the|his|her|their|on|in) ' + w + r'\b', lower)]
    if len(present) < 2 or present != list(labels[:len(present)]):
        return None
    # Ordinals here must identify the same repeated category (or bare 'one').
    heads = []
    for w in present:
        m = re.search(r'\b' + w + r' ([a-z]+)', lower)
        if m and m.group(1) != 'one':
            heads.append(m.group(1))
    if not heads or len(set(heads)) != 1:
        return None
    if _has(r'\blast\b', lower):
        index = len(present)
        if index >= len(labels):
            return None
        text = re.sub(r'\blast\b', labels[index], text, flags=re.I)
        present.append(labels[index])
    # A leading count of the indexed objects is an explicit enumeration.
    first_pos = min(re.search(r'\b' + w + r'\b', text, re.I).start() for w in present)
    initial = [n for n in read_numbers(text[:first_pos]) if n.value == len(present)]
    if len(initial) == 1:
        n = initial[0]
        if re.match(r'\s+' + re.escape(heads[0]), text[n.end:].lower()):
            text = text[:n.start] + 'several' + text[n.end:]
    aliases = {w: w.capitalize()+'item' for w in present}
    text = re.sub(r'\b(' + '|'.join(present) + r')\b', lambda m: aliases[m.group().lower()], text, flags=re.I)
    text = re.sub(r'(' + '|'.join(aliases.values()) + r') one\b', r'\1', text)
    text = re.sub(r',\s*(?:and\s+)?the (' + '|'.join(aliases.values()) + r')', r'. \1', text)
    if _has(r'\ball\b', p.question) and not any(_has(r'\b' + w + r'\b', p.question) for w in present):
        text = text.rstrip(' ?') + ' in total?'
    q = Problem.read(text)
    if q is None:
        return None
    return _combined_comparisons(q) or _comparisons(q)


def _relative_transaction(p):
    """Resolve a comparison graph before removing a fraction of one holding."""
    text = p.text.lower()
    fs = [n for n in p.numbers if 0 < n.value < 1 and n.kind != 'money']
    if len(fs) != 1 or not _has(r'\b(?:left|remain|remaining|have|has)\b', p.question):
        return None
    f = fs[0]
    prefix = text[:f.start]
    event = re.search(r'\b([a-z]+) (?:then )?(?:spends?|gives?|gave|loses?|uses?|eats?|sells?|sold)\s*$', prefix)
    if not event or not re.match(r"\s+(?:of (?:his|her|their|it|that)|his |her |their )", text[f.end:]):
        return None
    actor = event.group(1)
    if actor in ('he','she','they','it') or not _has(r'\b' + re.escape(actor) + r'\b', p.question):
        return None
    end = re.search(r'[.;,]|\bif\b', text[f.end:len(p.body)])
    cut = f.end+end.start() if end else len(p.body)
    body = p.text[:event.start()] + p.text[cut:len(p.body)]
    reduced = Problem.read(body + ' How many does ' + actor.capitalize() + ' have?')
    if reduced is None:
        return None
    result = _comparisons(reduced)
    if result is None:
        return None
    return _answer(result[0]*(1-f.value), 'Resolve the initial holding from the comparisons, then retain the unspent share')


def _money_ledger(p):
    """A budget or card balance, purchases, a relative purchase, and a refund."""
    text, ns = p.text.lower(), p.numbers
    money = [n for n in ns if n.kind == 'money']
    fs = [n for n in ns if 0 < n.value < 1 and n.kind != 'money']
    if len(fs) != 1 or not 3 <= len(money) <= 5 or ns[0] != money[0]:
        return None
    if not _has(r'\b(?:left|remaining|rest|balance)\b', text) or not _has(r'\b(?:money|spend|spent|left|remaining|balance)\b', p.question):
        return None
    f = fs[0]
    if not re.match(r'\s+(?:that (?:amount|much)|of (?:that|the (?:price|cost)))\b', text[f.end:]):
        return None
    if not money[0].start < money[1].start < f.start:
        return None
    extras = [n for n in ns if n not in money and n not in fs]
    for n in extras:
        later = [m for m in money if m.start > n.end]
        if not later or not _has(r'\bcosts?\s*$', text[n.end:later[0].start]):
            return None
        # A stated price of a group is already the price for the whole group.
        if _has(r'\beach\b', text[later[0].end:f.start]):
            return None
    card = _has(r'\b(?:card|credit)\b', p.body) and _has(r'\bbalance\b', p.question)
    if not card and not _has(r'\bthe rest\b', p.body):
        return None
    spent, previous = Fraction(0), money[0]
    for amount in money[1:]:
        prefix = text[previous.end:amount.start]
        if _has(r'\b(?:returned|refund|refunded)\b', prefix):
            sign = -1
        elif _has(r'\b(?:puts?|spent|spends?|costs?|buys?|bought|paid|pays?)\b', prefix):
            sign = 1
        else:
            return None
        spent += sign*amount.value
        previous = amount
    prior = [n for n in money[1:] if n.end < f.start]
    if not prior:
        return None
    spent += prior[-1].value*f.value
    value = money[0].value+spent if card else money[0].value-spent
    return _answer(value, 'Apply the purchases, the relative purchase, and any refund to the opening amount')


def _combined_comparisons(p):
    """A third entity is a stated multiple of two entities' combined amount."""
    text = p.text
    body = text[:len(p.body)]
    markers = list(re.finditer(r'\b(?:combined|sum)\b', body, re.I))
    if len(markers) != 1:
        return None
    m = markers[0]
    start = body.rfind('.', 0, m.start())+1
    end_match = re.search(r'[.;]', body[m.end():])
    end = m.end()+end_match.end() if end_match else len(body)
    clause = body[start:end]
    names = _names(body)
    before = _mentions(body[start:m.start()], names)
    after = list(dict.fromkeys(_mentions(body[m.end():end], names)))
    if not before or len(after) != 2:
        return None
    actor = before[0]
    if actor in after:
        return None
    quantities = read_numbers(clause)
    if quantities:
        if len(quantities) != 1 or not re.match(r'\s+times\b', clause[quantities[0].end:], re.I):
            return None
        factor = quantities[0].value
    elif _has(r'\bsame\b', clause.lower()):
        factor = Fraction(1)
    else:
        return None
    condition = re.split(r'\bif\b', p.question, maxsplit=1)
    anchor = (' If ' + condition[1]) if len(condition) == 2 else ''
    reduced = Problem.read(body[:start] + body[end:] + anchor + ' How many do they have in total?')
    if reduced is None:
        return None
    values = _comparisons(reduced, True)
    if values is None or set(values) != set(after):
        return None
    values[actor] = factor*sum(values.values(), Fraction(0))
    asked = list(dict.fromkeys(_mentions(p.question, list(values))))
    if _has(r'\b(?:total|together|altogether|combined|in all)\b', p.question):
        answer = sum((values[n] for n in (asked if len(asked) > 1 else values)), Fraction(0))
    elif asked == [actor]:
        answer = values[actor]
    else:
        return None
    return _answer(answer, 'Resolve the related amounts, then apply the multiple of their sum')


def _combined_age(p):
    """A relative age and a fraction of the combined ages, with a future shift."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 4:
        return None
    base, delta, f, years = ns
    if not re.match(r'\s+years? old\b', text[base.end:]) or not re.match(r'\s+years? (?:older|younger)\b', text[delta.end:]):
        return None
    if not 0 < f.value < 1 or not re.match(r'\s+(?:their|the) combined age\b', text[f.end:]):
        return None
    if years.start < len(p.body) or not re.match(r'\s+years?\b', text[years.end:]):
        return None
    if not _has(r'\bin\s*$', text[:years.start]):
        return None
    # The query must name the person whose age is the combined-age fraction.
    owner = re.search(r'\b([a-z]+) is\s*$', text[:f.start])
    if not owner or not _has(r'\b' + re.escape(owner.group(1)) + r'\b', p.question):
        return None
    sign = -1 if re.match(r'\s+years? younger\b', text[delta.end:]) else 1
    return _answer((2*base.value+sign*delta.value)*f.value+years.value, 'Apply the fraction to the two combined ages, then add the future years')

def solve(problem):
    # The shared gate runs first. Percentages are handled by the existing skill.
    if problem is None or any(n.kind == 'percent' for n in problem.numbers):
        return None
    if not (has_fraction(problem.text) or _has(r'\b(?:twice|thrice|double|triple)\b', problem.text.lower())):
        return None
    p = _prepare(problem)
    if p is None:
        return None
    for reader in (_ordinal_comparisons, _combined_comparisons, _combined_age, _relative_transaction, _money_ledger, _comparisons, _fixed_budget, _share_gap, _grouped_price_share, _coin_share, _flat_partition, _allocations, _fraction_subsets, _grouped_subset, _fraction_daily):
        result = reader(p)
        if result is not None:
            return result
    return None
