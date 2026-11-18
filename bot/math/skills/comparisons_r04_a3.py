"""Conservative multi-stage comparisons between named amounts.

Each understood relation supplies an exact affine equation. Known amounts and
explicit totals anchor the equations, including independently anchored groups.
Unexplained quantities, inconsistent equations and ambiguous queries abstain.
"""
import re
from fractions import Fraction

from ..numbers import read_numbers, format_number, _DIGIT, _WORD_NUMBER
from ..problem import ASK, Problem
from .comparisons_r01_a2 import _names
from .comparisons_r03_a4 import (
    _category, _category_mentions, _singular, _words, _periods, _UNIT, _UNITS,
)

_FACTOR = r'(?:twice|thrice|double|triple|quadruple|q\d+ times)'
_MULT = re.compile(
    r'\b(' + _FACTOR + r'|equally|q\d+(?= as (?:old|long|heavy|tall)\b))\s+(?:'
    r'as (many|much|old|long|heavy|tall)(.*?)\s+as\s+|'
    r'(?:older|larger|more) than\s+|'
    r'(?:the )?(?:number|amount|age|weight|height|length|cost|price|score)(?: of| that)?\s+|'
    r'(?:the )?money\s+|(?:this|that) amount\b\s*|'
    r'(?=[a-z]+(?:\'s|\')? (?:age|weight|height|size)\b))')
_ADD = re.compile(r'\b(q\d+)\s+(?!times\b)(?:[a-z]+\s+){0,2}?'
                  r'(more|less|fewer|older|younger|heavier|lighter|taller|shorter)\s*(.*?)\s+than\s+')
_VERB = r'(?:has|have|had|is|are|was|were|made|makes?|read|reads|bought|buys?|sold|sells?|owns?|contains?|costs?|weighs?|collected|picked|received|got|scored|planted|wears?|earned|earns?|grew|grows?)'
_TOTAL = r'\b(?:total|together|combined|altogether|collectively|both|in all|sum)\b'
_RELATIVE = r'(?:mom|dad|mother|father|sister|brother|grandmother|grandfather|daughter|son)'
_MINUS = {'less', 'fewer', 'younger', 'lighter', 'shorter'}
_MONTHS = 'january february march april may june july august september october november december'.split()
_CONTEXT = set('currently also during then finally from for of over under once each find calculate assuming another together'.split())


def _has(pattern, text):
    return re.search(pattern, text) is not None


def _indices(text):
    return {int(i) for i in re.findall(r'\bq(\d+)\b', text)}


def _events(text):
    return _periods(text) + re.findall(r'\b(?:' + '|'.join(_MONTHS) + r')\b', text)


def _mentions(text, names):
    """Longest mentions win so a relative is distinct from its possessor."""
    if not names:
        return []
    pattern = r'\b(?:' + '|'.join(re.escape(n) for n in sorted(names, key=len, reverse=True)) + r")\b(?:'s)?"
    return [re.sub(r"'s$", '', m.group()) for m in re.finditer(pattern, text)]


def _cat(text):
    text = re.sub(r'^(?:there (?:are|were)(?: of)? |the population of )', '', text.strip())
    text = re.split(r'\b(?:while|but)\b', text)[0]
    text = re.split(r'\band (?:the )?rest\b', text)[0]
    text = re.sub(r'\b(?:ones?|that|did|made|read|bought|sold)\b.*$', '', text).strip()
    cat = _category(text)
    return ' '.join(_singular(w) for w in cat.split()) if cat else None


def _factor(token, values):
    fixed = {'twice': 2, 'double': 2, 'thrice': 3, 'triple': 3, 'quadruple': 4, 'equally': 1}
    return Fraction(fixed[token]) if token in fixed else values[int(token[1:].split()[0])]


def _shift(text, values):
    m = re.search(r'\b(?:in|after) (q\d+) (?:more )?(years?|months?)\b|\b(q\d+) (years?|months?) (from now|ago)\b', text)
    if not m:
        implicit = re.search(r'\b(last|next) year\b', text)
        return (Fraction(-1 if implicit.group(1) == 'last' else 1), set()) if implicit else (Fraction(0), set())
    token = m.group(1) or m.group(3)
    unit = m.group(2) or m.group(4)
    value = values[int(token[1:])] / (12 if unit.startswith('month') else 1)
    return value * (-1 if m.group(5) == 'ago' else 1), _indices(m.group())


def _expand_event_references(body):
    """An omitted comparison reference may refer to the preceding named period."""
    pattern = r'\b(' + _FACTOR + r') as (many|much|long)([^.;,]*?)(?=[.;,]|\s+and\s+|$)'
    def expand(m):
        if _has(r'\bas\b', m.group(3)):
            return m.group()
        start = max(body.rfind('.', 0, m.start()), body.rfind(',', 0, m.start())) + 1
        current = _events(body[start:m.start()] + m.group(3))
        if len(set(current)) != 1:
            return m.group()
        previous = [e for e in _events(body[:m.start()]) if e != current[0]]
        if not previous:
            return m.group()
        return m.group().rstrip() + ' as ' + previous[-1]
    return re.sub(pattern, expand, body)


def _prepare(p):
    """Resolve possessive kinship phrases without merging people with relatives."""
    text = p.text
    # A date after an age belongs to that anchor. Put it before the owner so
    # it cannot be mistaken for a date on the question or another comparison.
    _NUMBER = r'(?:' + _DIGIT + '|' + _WORD_NUMBER + ')'
    text = re.sub(r'\ba year ago\b', '1 year ago', text, flags=re.I)
    text = re.sub(r'\b([A-Z][a-z]+|he|she) will be (' + _NUMBER +
                  r')(?: years? old)? in (' + _NUMBER + r') years?\b',
                  r'In \3 years, \1 will be \2 years old', text)
    cues = list(ASK.finditer(text))
    if cues:
        cut = cues[-1].start()
        if re.fullmatch(r'how old will [A-Za-z]+ be\s*\?', text[cut:], re.I):
            dates = list(re.finditer(r'\b(?:in|after) (' + _NUMBER + r') years?\b', text[:cut], re.I))
            if len(dates) == 1:
                text = text[:cut] + text[cut:].rstrip(' ?') + ' in ' + dates[0].group(1) + ' years?'
    text = re.sub(r'\bas many times as many\b', 'as many', text, flags=re.I)
    primary = _names(text)
    aliases = {}
    if not primary:
        return text, aliases
    # A pronoun possessor is safe only with one unambiguous named family owner.
    family_owners = set(m.group(1).lower() for m in re.finditer(
        r"\b([A-Z][a-z]+)'s " + _RELATIVE + r'\b', text))
    if len(primary) == 1:
        family_owners.add(primary[0])
    owner = next(iter(family_owners)) if len(family_owners) == 1 else None
    pattern = r"\b(" + '|'.join(re.escape(n) + "'s" for n in primary) + r'|her|his) (?:older |younger |little |big |oldest |youngest )?(' + _RELATIVE + r')\b'
    def relative(m):
        possessor = m.group(1).lower()
        if possessor in ('her', 'his'):
            if owner is None:
                return m.group()
            possessor = owner + "'s"
        # An explicitly named relative already has its own entity label.
        if re.match(r'\s+[A-Z][a-z]+\b', text[m.end():]):
            return m.group()
        label = possessor + ' ' + m.group(2).lower()
        if label not in aliases:
            aliases[label] = 'Relative' + chr(97 + len(aliases))
        return aliases[label]
    text = re.sub(pattern, relative, text, flags=re.I)
    return text, {v.lower(): k for k, v in aliases.items()}


def _linear(equations, nodes):
    """Solve a small, fully determined exact system and check every equation."""
    nodes = sorted(nodes)
    if not 2 <= len(nodes) <= 8:
        return None
    rows = [[coeff.get(n, Fraction(0)) for n in nodes] + [value]
            for coeff, value in equations]
    pivot_rows = {}
    row = 0
    for col in range(len(nodes)):
        pivot = next((i for i in range(row, len(rows)) if rows[i][col]), None)
        if pivot is None:
            continue
        rows[row], rows[pivot] = rows[pivot], rows[row]
        scale = rows[row][col]
        rows[row] = [v/scale for v in rows[row]]
        for i in range(len(rows)):
            if i != row and rows[i][col]:
                scale = rows[i][col]
                rows[i] = [a-scale*b for a, b in zip(rows[i], rows[row])]
        pivot_rows[col] = row
        row += 1
    if any(not any(r[:-1]) and r[-1] for r in rows) or len(pivot_rows) != len(nodes):
        return None
    result = {n: rows[pivot_rows[i]][-1] for i, n in enumerate(nodes)}
    return result if all(v >= 0 for v in result.values()) else None


def _chain(p, return_values=False):
    if re.search(r'\banother set\b', p.body):
        return None
    if re.search(r'\bnumber of [a-z]+ to the .+? as (?:it|he|she) did to\b', p.body):
        return None
    if any('/' in n.raw and 0 < n.value < 1 and
           re.match(r'\s+(?:more|less|fewer)\b', p.text[n.end:], re.I)
           for n in p.numbers):
        return None
    if re.search(r'\bneed\b.*\badd\b', p.question):
        return None
    if re.search(r'\b(?:share[ds]?|split|divide[ds]?)\b.*\bequally\b', p.question):
        return None
    if re.search(r'\bnot\b', p.question):
        return None
    if re.search(r'\btimes (?:the )?(?:number|amount) of [a-z]+(?: [a-z]+){0,2} as [a-z]+\b', p.body):
        return None
    if re.search(r'\bas those who\b|\bnumber of [a-z]+(?: [a-z]+)? [A-Z][a-z]+ (?:washed|cooked|picked|found)\b', p.text):
        return None
    text, display = _prepare(p)
    # Coin denominations are count nouns here, not the fraction 'one quarter'.
    text = re.sub(r'\bquarters\b(?!\s+of\b)', 'quartercoins', text, flags=re.I)
    heads = set(re.findall(r'\bas many [a-z]+ ([a-z]+) as\b', text.lower())) - {'ones'}
    if len(heads) == 1:
        text = re.sub(r'\bones\b', next(iter(heads)), text, flags=re.I)
    numbers = read_numbers(text)
    if not 1 <= len(numbers) <= 10 or any(n.kind == 'percent' for n in numbers):
        return None
    units = []
    raw_questions = list(ASK.finditer(text))
    question_start = raw_questions[-1].start() if raw_questions else len(text)
    for number in numbers:
        # Query numbers are checked separately as dates or exact group labels.
        # A label such as "the three days" is not a measurement of rainfall.
        if number.start >= question_start:
            continue
        unit = re.match(r'\s+(' + _UNIT + r')\b', text[number.end:].lower())
        if unit:
            units.append(_UNITS[_singular(unit.group(1))])
    if len(set(units)) > 1:
        return None
    question_unit = re.search(r'\b(?:how many|how much|in) (' + _UNIT + r')\b', p.question)
    if units and question_unit and _UNITS[_singular(question_unit.group(1))] != units[0]:
        return None
    values = [n.value for n in numbers]
    names = [n for n in _names(text) if n not in _CONTEXT and _has(r'\b' + re.escape(n) + r'\b', text.lower())]
    names += [m.group().lower() for m in re.finditer(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+(?: [A-Z][a-z]+)*\b', text)]
    tokenized = text.lower()
    for i, n in reversed(list(enumerate(numbers))):
        tokenized = tokenized[:n.start] + 'q' + str(i) + tokenized[n.end:]
    cues = list(ASK.finditer(tokenized))
    if not cues:
        return None
    body, query = tokenized[:cues[-1].start()], tokenized[cues[-1].start():]
    if _has(_FACTOR + r' (?:the )?sum of\b', body):
        return None
    # A date immediately before the question scopes the requested ages.
    trailing_date = re.search(r'\b(?:in|after) q\d+ years?,?\s*$', body)
    if trailing_date and re.search(r'\b(?:old|older|younger|age|ages|years)\b', query):
        query += ' ' + trailing_date.group().rstrip(' ,')
        body = body[:trailing_date.start()]
    conditional = re.split(r'\bif\b', query, maxsplit=1)
    if len(conditional) == 2:
        query = conditional[0]
        body += '. if ' + conditional[1].rstrip(' ?')
    body = re.sub(r"([a-z]+(?:'s)? (?:number|age|weight|height)) is (greater|less) than (.+?) by (?:exactly )?(q\d+)\b",
                  lambda m: '{} is {} {} than {}'.format(m.group(1), m.group(4), 'more' if m.group(2) == 'greater' else 'less', m.group(3)), body)
    body = _expand_event_references(body)
    body = re.sub(r'\b(costs? q\d+) each\b', r'\1', body)
    body = re.sub(r'\b(?:the )?same age as\b', 'equally as old as', body)
    body = re.sub(r'\bas (many|much) ([a-z ]+?) than\b', r'as \1 \2 as', body)
    age = _has(r'\b(?:age|ages|older|younger)\b|\byears? old\b|\bas old as\b', body)
    # These need a time/transaction/rate model rather than static quantities.
    if _has(r'\b(?:per|each|every|remaining|remains|left|gave|gives|loses|lost|spent|spends|discount|percent|speed|faster|fast|rest|bet|bets|wager|winner|winning)\b', body):
        return None
    if not age and _has(r'\b(?:ago|from now|in q\d+ years|after q\d+ years)\b', body):
        return None
    if _has(r'\bfrom (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday) to\b', body):
        return None
    if _has(r'\b(?:when|until)\b', body + query) and age:
        return None
    if not (_MULT.search(body) or _ADD.search(body)):
        return None
    # A named relative clause has the preceding reference as its subject.
    namepat = '|'.join(re.escape(n) for n in sorted(names, key=len, reverse=True)) or r'(?!)'
    body = re.sub(r'\b(' + namepat + r'),? who\s+', r'\1. \1 ', body)
    boundary = (r'[.;!?]|\s+but\s+|\s+while\s+|,?\s+and\s+(?=(?:(?:his|her|their) (?:[a-z]+ )*?)?(?:' + namepat + r'|he|she|it)\s+' + _VERB + r'\b)|'
                r',\s*(?=(?:the )?[a-z]+(?: [a-z]+){0,4}?\s+' + _VERB + r'\b)|'
                r',?\s+and\s+(?=' + _FACTOR + r'|q\d+|there (?:are|were)\b|the (?:number|amount|price|cost) of\b)|,\s*(?=' + _FACTOR + r'|q\d+)')
    clauses = []
    start = 0
    for cut in re.finditer(boundary, body):
        prefix = body[start:cut.start()]
        temporal_prefix = bool(re.fullmatch(r'\s*(?:(?:in|after) q\d+ (?:more )?(?:years?|months?)|q\d+ (?:years?|months?) ago)\s*', prefix))
        if (_has(r'^[.;!?]|\b(?:but|while)\b', cut.group()) or
                _has(r'\b' + _VERB + r'\b', prefix) or _MULT.search(prefix) or _ADD.search(prefix) or
                _indices(prefix) and not temporal_prefix):
            clauses.append(prefix)
            start = cut.end()
    clauses.append(body[start:])
    clauses = [re.sub(r'^and\s+', '', c.strip(' ,')) for c in clauses if c.strip(' ,')]
    equations, nodes, used = [], set(), set()
    query_shift, query_time = _shift(query, values) if age else (Fraction(0), set())
    used.update(query_time)
    subject = None
    subjects = {}
    relation_clauses = set()
    for ci, clause in enumerate(clauses):
        temporal, time_indices = _shift(clause, values) if age else (Fraction(0), set())
        used.update(time_indices)
        mults = list(_MULT.finditer(clause))
        adds = list(_ADD.finditer(clause)) if not mults else []
        if not mults and not adds and subject:
            # In a sequence of explicitly named amounts, "twice that tall"
            # and "three times as many" refer to the preceding amount.
            prior = subject
            left_names = _mentions(clause, names)
            implicit = re.search(r'\b(' + _FACTOR + r')\s+(?:as (many|much|long|old|tall|heavy)([^.;]*)|that (long|old|tall|heavy))\s*$', clause)
            if implicit and left_names and left_names[-1] != prior and not _has(r'\b(?:as|than|q\d+)\b', implicit.group(3) or ''):
                if implicit.group(4):
                    clause = clause[:implicit.start()] + implicit.group(1) + ' as ' + implicit.group(4) + ' as ' + prior
                else:
                    clause = clause.rstrip() + ' as ' + prior
                mults = list(_MULT.finditer(clause))
        if len(mults) + len(adds) > 1:
            return None
        if not mults and not adds:
            if _has(_FACTOR, clause):
                return None
            mentioned = _mentions(clause, names)
            if mentioned:
                subject = mentioned[-1]
            subjects[ci] = subject
            continue
        relation_clauses.add(ci)
        m = (mults or adds)[0]
        before, after = clause[:m.start()], clause[m.end():]
        mult = bool(mults)
        relation = m.group()
        if mult:
            scale, offset = _factor(m.group(1), values), Fraction(0)
            middle = m.group(3) or ''
            delta = re.search(r'\b(q\d+)\s+(?:[a-z]+\s+){0,2}?(more|less|fewer)\s*(?:[a-z]+\s+){0,3}?than\s*$', before)
            if delta:
                offset = values[int(delta.group(1)[1:])] * (-1 if delta.group(2) in _MINUS else 1)
                relation += delta.group()
                before = before[:delta.start()]
            suffix = re.search(r'\b(plus|minus) (q\d+)\b', after)
            if suffix:
                offset += values[int(suffix.group(2)[1:])] * (-1 if suffix.group(1) == 'minus' else 1)
                relation += suffix.group()
                after = after[:suffix.start()]
        else:
            if _has(_FACTOR, clause):
                return None
            scale = Fraction(1)
            offset = values[int(m.group(1)[1:])] * (-1 if m.group(2) in _MINUS else 1)
            middle = m.group(3)
            # For "10 more dimes than pennies", the category follows 'more'.
        lefts = _mentions(before, names)
        rights = _mentions(after, names)
        left_group, right_group = None, None
        lp, rp = _events(before + ' ' + middle), _events(after)
        if lp and rp:
            left, right = lp[-1], rp[0]
        elif mult and not lp and len(rp) == 2 and _has(r'\bon (?:a |the )?' + re.escape(rp[-1]) + r'\s*$', after):
            left, right = rp[-1], rp[0]
        elif mult and _has(r'\b(?:this|that) amount\b', m.group()) and rp and subject:
            left, right = rp[0], subject
        elif lefts and rights:
            left, right = lefts[-1], rights[0]
            if len(set(rights)) > 1:
                if not _has(r'\b(?:combined|together|altogether|sum)\b', after):
                    return None
                right_group = list(dict.fromkeys(rights))
        elif rights and _has(r'\btogether\b.*\bthey\b', before) and len(nodes) == 2:
            left_group = sorted(nodes)
            left, right = left_group[0], rights[0]
        elif rights and subject and _has(r'^\s*(?:he|she|it)\b', before):
            left, right = subject, rights[0]
        elif lefts and _has(r'\b(?:her|him|he|she)\b', after):
            left = lefts[-1]
            candidates = set(_mentions(body[:body.find(clause)], names)) - {left}
            if len(candidates) != 1:
                return None
            right = next(iter(candidates))
        else:
            left, right = _cat(middle), _cat(after)
            # In "a container has N more items than another container",
            # the subject owns the count. The repeated item noun is the unit.
            # Establish both owners as explicit subjects elsewhere in the
            # narrative before preferring them over category comparisons.
            class_owners = set(re.findall(r'(?:^|[.;]\s*)(?:a|an|the) ([a-z]+) has\b', body))
            owner = re.fullmatch(r'\s*(?:a|an|the) ([a-z]+) has\s*', before)
            if not mult and owner and owner.group(1) in class_owners and right in class_owners and left not in class_owners:
                left = owner.group(1)
            if _has(r'\band\b.*\bcombined\b', after):
                components = re.split(r'\s+and\s+', re.sub(r'\s+combined\b.*$', '', after))
                right_group = [_cat(c) for c in components]
                if not all(right_group) or len(set(right_group)) != len(right_group):
                    return None
                right = right_group[0]
            if not left:
                subj = re.search(r'(.+?)\s+' + _VERB + r'\s*$', before)
                left = _cat(subj.group(1)) if subj else None
            if not left or not right or rights:
                return None
        if left == right or scale <= 0:
            return None
        if age:
            lt, li = _shift(before, values)
            rt, ri = _shift(after, values)
            used.update(li | ri)
            if li:
                # A leading date applies to both people unless the reference
                # explicitly names a present age.
                if not ri and not _has(r'\b(?:now|today|currently|present|current)\b', after):
                    rt = lt
            elif lt and not ri and not _has(r'\b(?:now|today|currently|present|current)\b', after):
                rt = lt
            offset += scale*rt-lt
        lhs = left_group or [left]
        rhs = right_group or [right]
        if set(lhs) & set(rhs):
            return None
        coeff = {n: Fraction(1) for n in lhs}
        coeff.update({n: -scale for n in rhs})
        equations.append((coeff, offset))
        nodes.update(lhs + rhs)
        used.update(_indices(relation))
        subject = left
        subjects[ci] = subject
    if not nodes:
        return None
    node_names = nodes & set(names)
    categories = nodes - set(names) - set(_events(body))
    for i, value in enumerate(values):
        if i in used:
            continue
        token = 'q' + str(i)
        if _has(r'\b' + token + r'\b', query):
            # Counts explicitly describing all queried participants are labels.
            tail = query.split(token)[1]
            if value == len(nodes) and (re.match(r'\s+(?:people|persons|family members|of them|friends|students|children)\b', tail) or
                                        re.match(r'\s+have\b', tail) and _has(_TOTAL, query) or
                                        _has(r'\baverage\b.*\bof (?:the )?' + token + r'\b', query) or
                                        nodes <= set(_events(body)) and re.match(r'\s+(?:days|weeks|months|years)\b', tail)):
                used.add(i)
                continue
            return None
        containing = [(ci, c) for ci, c in enumerate(clauses) if _has(r'\b' + token + r'\b', c)]
        if len(containing) != 1:
            return None
        ci, clause = containing[0]
        # A trailing conditional anchor can share a sentence with a relation.
        local = re.split(r'\bif\b', clause)[-1]
        if ci in relation_clauses and local == clause:
            return None
        if not _has(r'\b' + token + r'\b', local):
            return None
        before, after = local.split(token, 1)
        if (_indices(before) | _indices(after)) - used:
            return None
        temporal, _ = _shift(local, values) if age else (Fraction(0), set())
        if age and re.match(r'\s+months? old\b', after):
            value /= 12
        owners = _mentions(before, node_names)
        if not owners and age and _has(r'\b(?:he|she)\b', before) and subjects.get(ci) in node_names:
            owners = [subjects[ci]]
        cats = _category_mentions(after, categories)
        periods = [n for n in nodes if n in _events(local)]
        joint = list(dict.fromkeys(_mentions(local, node_names)))
        total = _has(_TOTAL, local) and len(joint) != 1 and len(cats) != 1
        if (total or len(joint) > 1) and not _has(r'\b(?:more|less|than|times)\b', local):
            if set(_mentions(local, names)) - nodes:
                return None
            targets = joint if len(joint) > 1 else list(nodes)
            equations.append(({n: Fraction(1) for n in targets}, value-len(targets)*temporal))
        elif len(periods) == 1:
            equations.append(({periods[0]: Fraction(1)}, value))
        elif owners:
            equations.append(({owners[-1]: Fraction(1)}, value-temporal))
        elif len(cats) == 1:
            equations.append(({cats[0]: Fraction(1)}, value))
        elif len(_category_mentions(before, categories)) == 1:
            cat = _category_mentions(before, categories)[0]
            equations.append(({cat: Fraction(1)}, value))
        else:
            return None
        used.add(i)
    if used != set(range(len(numbers))):
        return None
    solved = _linear(equations, nodes)
    if solved is None:
        return None
    if return_values:
        return solved
    asked = list(dict.fromkeys(_mentions(query, node_names)))
    asked_periods = [n for n in nodes if n in _events(query)]
    if not asked_periods and nodes <= set(_events(body)) and _has(r'\bcosts?\b', body) and _has(r'\bspend\b', query):
        context = clauses[-1]
        if _has(r'^if\b.*\b(?:goes|buys|attends)\b', context) and not _indices(context):
            asked_periods = [n for n in nodes if n in _events(context)]
    if asked_periods and nodes <= set(_events(body)):
        asked = asked_periods
    if not asked:
        asked = _category_mentions(query, categories)
    if not asked and categories == nodes:
        common = set.intersection(*(_words(n) for n in nodes))
        noun_query = re.match(r'how (?:many|much) (.+?)(?=\s+(?:are|were|is|was|does|do|did|will|can|would|have|has)\b|[?])', query)
        if noun_query:
            noun = _cat(noun_query.group(1))
            words = _words(noun) if noun else set()
            understood = set.union(*(_words(n) for n in nodes)) | {'total', 'combined', 'all'}
            if words & common and words - understood:
                return None
    average = _has(r'\baverage\b', query)
    aggregate = False
    if not asked and categories == nodes:
        for clause in clauses:
            group = re.search(r'^(.+?)\b(?:contains?|includes?|consists? of)\s+(.+)', clause)
            if group and len(_category_mentions(group.group(2), categories)) == len(nodes):
                aggregate = bool((_words(group.group(1)) - {'a', 'the', 'of'}) & _words(query))
    if not asked and node_names == nodes and _has(r'\btheir team\b', query):
        aggregate = any(set(_mentions(c, node_names)) == nodes and _has(r'\b(?:belong to|on|in) the same team\b', c) for c in clauses)
    if _has(r'\bcost to (?:plant|build|make|assemble)\b', query):
        if not _has(r'\bcosts?\b', body) or not categories == nodes:
            return None
        aggregate = True
    if average:
        if len(asked) == 1:
            return None
        targets = asked if len(asked) > 1 else list(nodes)
        result = sum((solved[n] for n in targets), Fraction(0)) / len(targets) + query_shift
    elif _has(r'\bdifference\b|\bhow (?:many|much) (?:(?:years?|' + _UNIT + r') )?(?:more|less|fewer|older|younger|taller|shorter|heavier|lighter)\b', query):
        if age and len(asked) == 1 and len(nodes) == 2 and _has(r'\bthan (?:him|her)\b', query):
            asked += [n for n in nodes if n not in asked]
        if len(asked) != 2:
            return None
        result = abs(solved[asked[0]]-solved[asked[1]])
    elif (_has(_TOTAL, query) and len(asked) != 1 or aggregate or
          not asked and nodes <= set(_events(body)) and _has(r'\b(?:over|during)\b', query) or
          len(asked) > 1 and set(asked) <= set(_events(body)) and _has(r'\b(?:spend|cost)\b', query) or
          len(asked) > 1 and _has(r'\band\b', query) or
          not asked and categories == nodes and set.intersection(*(_words(n) for n in nodes)) & _words(query)):
        targets = asked if len(asked) > 1 else list(nodes)
        result = sum((solved[n] for n in targets), Fraction(0)) + len(targets)*query_shift
    elif len(asked) == 1:
        result = solved[asked[0]] + query_shift
    else:
        return None
    if age and _has(r'\bmonths? old\b', query):
        result *= 12
    if result < 0:
        return None
    return result, '; '.join('{} = {}'.format(display.get(n, n), format_number(solved[n])) for n in sorted(nodes)) + '.'


def _repeat_with_rate(p):
    """A first episode and a multiple-sized episode at one stated unit rate."""
    text = p.text.lower()
    ns = p.numbers
    if any(n.kind == 'percent' for n in ns):
        return None
    # Tokenization also supports written-number factors.
    for i, n in reversed(list(enumerate(ns))):
        text = text[:n.start] + 'q' + str(i) + text[n.end:]
    factors = list(re.finditer(r'\b(' + _FACTOR + r') as (?:many|much)\b', text))
    if len(factors) != 1:
        return None
    m = factors[0]
    episodes = _has(r'\b(?:last|this|next|first|second|third|previous|yesterday|today)\b', p.body)
    names = _names(p.text)
    references = set(_mentions(text[m.end():].split('.', 1)[0], names))
    initial_names = set(_mentions(text[:m.start()], names))
    if not episodes and not (_has(_TOTAL + r'|\ball the\b', p.question) and references & initial_names):
        return None
    if _has(r'\b(?:less|more|fewer|minus|left|remaining|originally|average|only|sold out)\b', p.body):
        return None
    used = _indices(m.group())
    amounts = [i for i in range(len(ns)) if i not in used]
    if len(amounts) != 2 or any(ns[i].start >= len(p.body) for i in amounts):
        return None
    rate = re.search(r'\beach ([a-z]+)(?: of [a-z]+)? (?:had|has|costs?|holds?|contains?|weighs?|is|was)(?: [a-z]+){0,2}? (q\d+)\b', text)
    if not rate:
        return None
    ri = int(rate.group(2)[1:])
    base = next((i for i in amounts if i != ri), None)
    if ri not in amounts or base is None or ns[base].start >= p.text.lower().find('each '):
        return None
    # The per-item noun must agree with the counted first episode.
    base_tail = p.text[ns[base].end:].lower()
    noun = re.match(r'\s+([a-z]+)', base_tail)
    if not noun:
        return None
    # A counted group may explicitly purchase the priced item (customers buy
    # meals, passengers buy passes, etc.). The object comes from the rate.
    count_matches = _singular(noun.group(1)) == _singular(rate.group(1))
    purchases = (r'\b' + re.escape(noun.group(1)) +
                 r' (?:buy|bought|purchase|purchased|order|ordered) (?:the |some )?' +
                 re.escape(rate.group(1)) + r'(?:s|es)?\b')
    if not count_matches and not _has(purchases, p.body):
        return None
    monetary = ns[ri].kind == 'money'
    tail = p.text[ns[ri].end:].lower()
    unit = re.match(r'\s+([a-z]+)', tail)
    if monetary:
        if not _has(r'\bhow much\b', p.question):
            return None
    elif not unit or _singular(unit.group(1)) not in _words(p.question) or not _has(_TOTAL + r'|\ball the\b', p.question):
        return None
    factor = _factor(m.group(1), [n.value for n in ns])
    if factor <= 0:
        return None
    result = ns[base].value * (1+factor) * ns[ri].value
    return result, '{} x (1 + {}) x {}.'.format(format_number(ns[base].value), format_number(factor), format_number(ns[ri].value))


def _remainder(p):
    """Two compared categories and an explicitly identified leftover category."""
    text = p.text.lower()
    for i, n in reversed(list(enumerate(p.numbers))):
        text = text[:n.start] + 'q' + str(i) + text[n.end:]
    body = text[:list(ASK.finditer(text))[-1].start()]
    if not _has(r'\b(?:rest|absent)\b', body) or any(n.kind == 'percent' for n in p.numbers):
        return None
    ms = list(_MULT.finditer(body))
    if len(ms) != 1 or ms[0].group(2) != 'many':
        return None
    m = ms[0]
    left, right = _cat(m.group(3)), _cat(body[m.end():])
    if not left or not right:
        return None
    rest = re.search(r'\b(?:the )?rest(?: of [^.;]*?)? (?:are|were|is) ([a-z]+)', body)
    absent = _has(r'\ball (?:the )?absent\b', body) and _has(r'\babsent\b', p.question)
    if not absent and (not rest or not (_words(rest.group(1)) & _words(p.question))):
        return None
    remaining = [i for i in range(len(p.numbers)) if i not in _indices(m.group())]
    if len(remaining) != 2:
        return None
    anchors = []
    for i in remaining:
        tail = body.split('q'+str(i), 1)[1]
        cat = _category_mentions(re.split(r'[.;,]', tail)[0], {left, right})
        if len(cat) == 1:
            anchors.append((i, cat[0]))
    if len(anchors) != 1:
        return None
    ai, category = anchors[0]
    total_i = next(i for i in remaining if i != ai)
    if any(p.numbers[i].start >= len(p.body) for i in remaining):
        return None
    total_noun = re.match(r'\s+([a-z]+)', p.text[p.numbers[total_i].end:].lower())
    if not total_noun:
        return None
    stock_unit = _singular(total_noun.group(1))
    shared_unit = _words(left) & _words(right)
    anchor_tail = p.text[p.numbers[ai].end:].lower()
    anchor_object = re.split(r'[.;,]', anchor_tail)[0]
    rest_context = re.search(r'\b(?:the rest|all (?:the )?absent)\b[^.;]*', p.body)
    if (stock_unit not in shared_unit and stock_unit not in _words(anchor_object) and
            (not rest_context or stock_unit not in _words(rest_context.group()))):
        return None
    k = _factor(m.group(1), p.values)
    if k <= 0:
        return None
    base = p.values[ai] / k if category == left else p.values[ai]
    result = p.values[total_i] - base*(1+k)
    if result < 0:
        return None
    return result, '{} - {} x (1 + {}).'.format(format_number(p.values[total_i]), format_number(base), format_number(k))


def _stock_graph(p):
    """Subtract compared allocations from a separately stated whole stock."""
    if read_numbers(p.question):
        return None
    rest_owner = re.search(r'\b([a-z]+) (?:picked up|received|got|has|took) the rest\b', p.body)
    asks_rest = rest_owner and _has(r'\b' + re.escape(rest_owner.group(1)) + r'\b', p.question)
    if not asks_rest and not _has(r'\b(?:left|remain|remaining)\b', p.question):
        return None
    if _has(r'\b(?:percent|each|every|per|after q\d+|sold|gave|lost)\b', p.body):
        return None
    raw_body = p.text[:len(p.body)]
    candidates = []
    for m in re.finditer(r'[^.;!?]+[.;]?', raw_body):
        sentence = m.group()
        ns = read_numbers(sentence)
        if len(ns) != 1 or _has(r'\b(?:twice|times|thrice|more|less|fewer|than)\b', sentence.lower()):
            continue
        if not _has(r'\b(?:has|have|had|contains?|picked|sliced into|cut into|total|bought|collected|found|produced)\b', sentence.lower()):
            continue
        # The whole stock must have the same object as the requested remainder.
        tail = sentence[ns[0].end:].lower()
        noun = re.match(r'\s+([a-z]+)', tail)
        if not noun:
            continue
        unit = _singular(noun.group(1))
        requested_unit = re.match(r'how many ([a-z]+) of (?:the )?([a-z]+)', p.question)
        related_unit = None
        if requested_unit and _singular(requested_unit.group(2)) in _words(sentence.lower()):
            related_unit = _singular(requested_unit.group(1))
        if unit not in _words(p.question) and related_unit is None:
            continue
        reduced_body = raw_body[:m.start()] + raw_body[m.end():]
        if asks_rest:
            reduced_body = re.sub(r'[^.;!?]*\bthe rest\b[^.;!?]*[.;]?', '', reduced_body, flags=re.I)
        # The compared allocations must consume this stock's object.
        amount_units = []
        for number in read_numbers(reduced_body):
            noun_match = re.match(r'\s+([a-z]+)', reduced_body[number.end:].lower())
            if noun_match:
                amount_units.append(_singular(noun_match.group(1)))
        if unit not in amount_units and related_unit not in amount_units:
            continue
        reduced = Problem.read(reduced_body + ' How many are there in total?')
        if reduced is None:
            continue
        part = _chain(reduced)
        if part is not None and 0 <= part[0] <= ns[0].value:
            candidates.append((ns[0].value-part[0], '{} - {}.'.format(format_number(ns[0].value), format_number(part[0]))))
    return candidates[0] if len(candidates) == 1 else None


def _age_event(p):
    """Advance both current ages to an explicitly described age event."""
    if not _has(r'\b(?:old|age|years)\b', p.question) or not _has(r'\b(?:when|would|will)\b', p.question):
        return None
    raw, display = _prepare(p)
    numbers = read_numbers(raw)
    values = [n.value for n in numbers]
    text = raw.lower()
    for i, n in reversed(list(enumerate(numbers))):
        text = text[:n.start] + 'q' + str(i) + text[n.end:]
    ask = list(ASK.finditer(text))[-1]
    body, query = text[:ask.start()], text[ask.start():]
    if _has(r'\b(?:ago|later|months?|in q\d+|after q\d+)\b', body):
        return None
    raw_ask = list(ASK.finditer(raw))[-1]
    reduced = Problem.read(raw[:raw_ask.start()] + ' How old are they now?')
    if reduced is None:
        return None
    state = _chain(reduced, return_values=True)
    if state is None:
        # Two directly stated current ages need no comparison graph.
        names = _names(raw)
        state, used = {}, set()
        namepat = '|'.join(re.escape(n) for n in sorted(names, key=len, reverse=True))
        if not namepat:
            return None
        anchors = list(re.finditer(r'\b(' + namepat + r') (?:is |was )?(?:currently |now )?(q\d+)(?: years? old)?\b', body))
        for m in anchors:
            if re.match(r'\s+(?:as|times|more|less|older|younger)\b', body[m.end():]):
                continue
            state[m.group(1)] = values[int(m.group(2)[1:])]
            used.update(_indices(m.group()))
        if len(state) != 2 or used != _indices(body):
            return None
    if len(state) != 2:
        return None
    requested_text = re.split(r'\bwhen\b', query)[0]
    first_mult = _MULT.search(requested_text)
    if first_mult:
        requested_text = requested_text[:first_mult.start()]
    requested = list(dict.fromkeys(_mentions(requested_text, state)))
    elapsed_query = _has(r'^how many years\b', query)
    if not requested and elapsed_query:
        # A family owner supplies the subject of "she will be ... her sister".
        primary = [n for n in state if n not in display]
        requested = primary if len(primary) == 1 else []
    if len(requested) != 1:
        return None
    matches = list(_MULT.finditer(query))
    if len(matches) == 1:
        m = matches[0]
        left_names = _mentions(query[:m.start()], state)
        right_names = _mentions(query[m.end():], state)
        left = left_names[-1] if left_names else requested[0]
        if right_names:
            right = right_names[0]
        elif _has(r'\b(?:him|her|he|she)\b', query[m.end():]):
            right = next(n for n in state if n != left)
        else:
            return None
        if left == right or _indices(query) != _indices(m.group()):
            return None
        factor = _factor(m.group(1), values)
        fixed_reference = _has(r'\b(?:now|currently|today)\b', query[m.end():])
        if fixed_reference:
            elapsed = factor*state[right]-state[left]
        elif factor != 1:
            elapsed = (factor*state[right]-state[left])/(1-factor)
        else:
            return None
    elif not matches:
        event = re.search(r'\bwhen (.+?) (?:is|turns|will be) (q\d+)\b', query)
        if not event or _indices(query) != _indices(event.group()):
            return None
        owners = list(dict.fromkeys(_mentions(event.group(1), state)))
        if len(owners) != 1:
            return None
        elapsed = values[int(event.group(2)[1:])] - state[owners[0]]
    else:
        return None
    if elapsed < 0:
        return None
    result = elapsed if elapsed_query else state[requested[0]] + elapsed
    return result, 'Advance both ages by {} years.'.format(format_number(elapsed))


def _weekday_span(p):
    """A daily amount for a weekday range plus a compared amount on one day."""
    days = 'monday tuesday wednesday thursday friday saturday sunday'.split()
    day = '(?:' + '|'.join(days) + ')'
    text = p.text.lower()
    for i, n in reversed(list(enumerate(p.numbers))):
        text = text[:n.start] + 'q' + str(i) + text[n.end:]
    body = text[:list(ASK.finditer(text))[-1].start()]
    span = re.search(r'\bfrom (' + day + r') to (' + day + r')\b', body)
    if not span or not (_has(_TOTAL, p.question) or _has(r'\b(?:each|per) week\b', p.question)):
        return None
    comparisons = list(re.finditer(r'\b(' + _FACTOR + r') (?:as (?:many|much)|the amount)\b', body))
    if len(comparisons) != 1:
        return None
    m = comparisons[0]
    other = re.search(r'\bon (' + day + r')\b', body[max(body.rfind('.', 0, m.start()), 0):])
    if not other:
        return None
    count = (days.index(span.group(2))-days.index(span.group(1))) % 7 + 1
    included = {days[(days.index(span.group(1))+i) % 7] for i in range(count)}
    if other.group(1) in included:
        return None
    remaining = set(range(len(p.numbers))) - _indices(m.group())
    if len(remaining) != 1:
        return None
    i = next(iter(remaining))
    if p.numbers[i].start >= len(p.body):
        return None
    # The known amount belongs to the range sentence.
    sentence = body[body.rfind('.', 0, span.start())+1:]
    sentence = sentence.split('.', 1)[0]
    if 'q'+str(i) not in sentence:
        return None
    factor = _factor(m.group(1), p.values)
    if factor <= 0:
        return None
    result = p.values[i]*(count+factor)
    unit = re.match(r'\s+(minutes?|hours?)\b', p.text[p.numbers[i].end:].lower())
    if unit and _singular(unit.group(1)) == 'minute' and _has(r'\bhours?\b', p.question):
        result /= 60
    elif unit and _singular(unit.group(1)) == 'hour' and _has(r'\bminutes?\b', p.question):
        result *= 60
    return result, '{} x ({} + {}).'.format(format_number(p.values[i]), count, format_number(factor))


def _group_rates(p):
    """Two counted groups whose per-member consumption rates are compared."""
    if not _has(_TOTAL, p.question) or any(n.kind == 'percent' for n in p.numbers):
        return None
    text = p.text.lower()
    for i, n in reversed(list(enumerate(p.numbers))):
        text = text[:n.start] + 'q' + str(i) + text[n.end:]
    verb = r'(?:eat|eats|use|uses|need|needs|consume|consumes|produce|produces|make|makes|collect|collects)'
    first = re.search(r'\b(q\d+) ([a-z]+) (?:[a-z]+ ){0,7}?' + verb + r' (q\d+) ([a-z]+) each\b', text)
    second = re.search(r'\b(q\d+) ([a-z]+) ' + verb + r' (' + _FACTOR + r') as much as (?:the )?([a-z]+)\b', text)
    if not first or not second or _singular(first.group(2)) != _singular(second.group(4)):
        return None
    if first.group(2) == second.group(2) or _indices(first.group() + ' ' + second.group()) != set(range(len(p.numbers))):
        return None
    if _singular(first.group(4)) not in _words(p.question):
        return None
    a, rate = (p.values[int(first.group(i)[1:])] for i in (1, 3))
    b = p.values[int(second.group(1)[1:])]
    k = _factor(second.group(3), p.values)
    if k <= 0:
        return None
    return (a+b*k)*rate, '({} + {} x {}) x {}.'.format(format_number(a), format_number(b), format_number(k), format_number(rate))


def _priced_rate(p):
    """Resolve a comparison of daily outputs before applying a unit price."""
    money = [n for n in p.numbers if n.kind == 'money']
    if len(money) != 1 or not _has(r'\b(?:earn|make|income|pay)\b', p.question):
        return None
    price = money[0]
    tail = p.text[price.end:].lower()
    denominator = re.match(r'\s+per ([a-z]+)\b', tail)
    if not denominator:
        return None
    body = p.text[:len(p.body)]
    source = re.search(r'\b([a-z]+) per (day|week)\b', body.lower())
    if not source:
        return None
    source_unit = _singular(source.group(1))
    priced_unit = _singular(denominator.group(1))
    if source_unit != priced_unit and source_unit != priced_unit + 'er':
        return None
    dest = re.search(r'\b(?:per|a|each|every) (day|week)\b', p.question)
    if not dest:
        return None
    boundaries = [0] + [m.end() for m in re.finditer(r'[;!?]|\.(?!\d)', body)] + [len(body)]
    spans = [(a, b) for a, b in zip(boundaries, boundaries[1:]) if a <= price.start < b]
    if len(spans) != 1 or len(read_numbers(body[spans[0][0]:spans[0][1]])) != 1:
        return None
    start, end = spans[0]
    reduced = body[:start] + body[end:]
    reduced = re.sub(r'\b(?:an )?average of\s+', '', reduced, flags=re.I)
    reduced = re.sub(r'\bper (?:day|week)\b', '', reduced, flags=re.I)
    requested = _mentions(p.question, _names(p.text))
    if len(requested) != 1:
        return None
    problem = Problem.read(reduced + ' How many does ' + requested[0] + ' have?')
    if problem is None:
        return None
    quantity = _chain(problem)
    if quantity is None:
        return None
    conversion = Fraction(7 if dest.group(1) == 'week' else 1, 7 if source.group(2) == 'week' else 1)
    result = quantity[0]*price.value*conversion
    return result, '{} x {} x {}.'.format(format_number(quantity[0]), format_number(price.value), format_number(conversion))


def solve(problem):
    for rule in (_chain, _age_event, _weekday_span, _group_rates, _priced_rate, _repeat_with_rate, _remainder, _stock_graph):
        result = rule(problem)
        if result is not None:
            return result
    return None
