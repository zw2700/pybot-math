"""Small affine equation graphs for explicit comparisons.

A comparison contributes an equation between owners, categories or periods. A
known quantity or an explicitly shared total anchors the graph. Every numerical
quantity must have a role; unsupported changes, rates and ambiguous references
are left to other skills.
"""
import re
from fractions import Fraction

from ..numbers import format_number
from ..problem import ASK
from .comparisons_r01_a2 import _equation_graph, _names


_FACTOR = r'(?:twice|double|thrice|triple|quadruple|q\d+ times)'
_MULT = re.compile(
    r'\b(' + _FACTOR + r')\s+(?:'
    r'as (many|much|old|young|long|expensive|big|large|heavy|tall)(.*?)\s+as\s+|'
    r'(younger|older) than\s+|'
    r'(?:the )?(?:number|amount|distance)(?: of| that)\s+|'
    r'(?:the )?(?:money|weight|height|age|bid|price|cost)(?: of)?\s+|'
    r'(?:more )?than\s+|'
    r'what\s+|'
    r'(?=[a-z]+(?:\'s)? (?:age|weight|height|money|bid)\b))')
_ADD = re.compile(r'\b(q\d+)\s+(?!times\b)(?:([a-z]+(?: [a-z]+)?)\s+)?'
                  r'(more|less|fewer|older|younger|heavier|lighter|taller|shorter)'
                  r'\s*(.*?)\s+than\s+')
_SIGN = {'less': -1, 'fewer': -1, 'younger': -1, 'lighter': -1, 'shorter': -1}
_TOTAL = r'\b(?:total|together|combined|altogether|collectively|both|in all|sum)\b'
_VERB = r'(?:has|have|had|is|are|was|were|got|gets|received|receives|sent|sends|sold|sells|costs?|weighs?|owns?|holds?|contain[s]?|deposited|drove|read|reads|did|does|harvested|picked)'


def _has(pattern, text):
    return re.search(pattern, text) is not None


def _tokens(p):
    text = p.text.lower()
    for i, number in reversed(list(enumerate(p.numbers))):
        text = text[:number.start] + 'q' + str(i) + text[number.end:]
    cues = list(ASK.finditer(text))
    if not cues:
        return None
    ask = cues[-1]
    return text[:ask.start()], text[ask.start():]


def _value(token, p):
    return p.values[int(token[1:])]


def _factor(token, p):
    fixed = {'twice': 2, 'double': 2, 'thrice': 3, 'triple': 3, 'quadruple': 4}
    return Fraction(fixed[token]) if token in fixed else _value(token.split()[0], p)


def _indices(text):
    return set(int(i) for i in re.findall(r'\bq(\d+)\b', text))


def _singular(word):
    irregular = {'children': 'child', 'people': 'person', 'men': 'man', 'women': 'woman', 'feet': 'foot', 'teeth': 'tooth', 'inches': 'inch'}
    if word in irregular:
        return irregular[word]
    if word.endswith('ies'):
        return word[:-3] + 'y'
    if word.endswith('s') and not word.endswith(('ss', 'us')):
        return word[:-1]
    return word


def _words(text):
    return set(_singular(w) for w in re.findall(r'[a-z]+', text))


def _category(text):
    text = re.sub(r'^there (?:are|were)(?: of)? ', '', text.strip())
    text = re.sub(r'^(?:(?:the|a|an|his|her|their|its|of|number|amount)\s+)+', '', text.strip())
    text = re.sub(r'^(?:he|she|they|it)\s+' + _VERB + r'\s+', '', text)
    text = re.split(r'\b(?:as|than|from|at|in|on|to|for|with|waiting|that|which|who|go|goes|did|does|do|has|have|had|is|are|was|were|will|put|sent|gives?|costs?|weighs?|drank)\b|[,.;?!]', text)[0].strip()
    text = re.sub(r"'s age$", '', text)
    if (not re.fullmatch(r'[a-z]+(?: [a-z]+){0,3}', text)
            or text in ('he', 'she', 'they', 'it', 'him', 'her', 'them', 'what')):
        return None
    return text


def _subject(text):
    starts = list(re.finditer(r'\b(?:price|cost|number|amount) of (?:the )?', text))
    if starts:
        text = text[starts[-1].end():]
    predicate = re.search(r'\s+' + _VERB + r'\s*(?:currently\s*)?$', text)
    return _category(text[:predicate.start()]) if predicate else None


def _clauses(body):
    clauses = []
    boundary = re.compile(r'(?:,?\s+and\s+|,\s*)(?=(?:in q\d+ years )?[a-z]+(?: [a-z]+){0,3}? (?:' + _VERB + r'|will|can)\b)|,?\s+and\s+(?=(?:the )?(?:price|cost) of\b)|,?\s+and\s+(?=' + _FACTOR + r'|q\d+ (?:more|less|fewer)\b)')
    for sentence in re.split(r'[.;!?]|\s+but\s+', body):
        start = 0
        for match in boundary.finditer(sentence):
            prefix = sentence[start:match.start()]
            # "A, B and C have ..." is one joint subject. Only split
            # coordination after the preceding clause has a predicate.
            if _has(r'\b' + _VERB + r'\b', prefix) or _MULT.search(prefix) or _ADD.search(prefix):
                clauses.append(prefix.strip())
                start = match.end()
        clauses.append(sentence[start:].strip())
    return [c for c in clauses if c]


def _periods(text):
    return re.findall(r'\b(?:(?:this|last|next|previous) (?:week|month|year|day)|monday|tuesday|wednesday|thursday|friday|saturday|sunday|today|yesterday)\b', text)


def _future(text, p):
    match = re.search(r'\b(?:in|after) (q\d+) years?\b', text)
    return (_value(match.group(1), p), _indices(match.group())) if match else None


def _relative_query(body, query, nodes, names):
    """Resolve "Ada's sister" from an explicitly introduced named relative."""
    relatives = r'(?:sister|brother|mother|father|daughter|son|grandmother|grandfather)'
    for target in nodes & set(names):
        for m in re.finditer(r"\b([a-z]+(?:'s)?|her|his) (" + relatives + r') ' + re.escape(target) + r'\b', body):
            owner = m.group(1)
            if owner in ('her', 'his'):
                prior = set(_mentions(body[:m.start()], nodes & set(names))) - {target}
                if len(prior) != 1:
                    continue
                owner = next(iter(prior)) + "'s"
            if _has(r'\b' + re.escape(owner + ' ' + m.group(2)) + r'\b', query):
                return [target]
    return None


def _group_label(value, token, text, nodes, query=False):
    """Recognize a count labeling the modeled variables, not an amount."""
    if value != len(nodes):
        return False
    after = text.split(token, 1)[-1]
    if _has(r'^\s+of them\b', after):
        return True
    enumeration = re.match(r'\s+[a-z]+\s*[:,]\s*(.+)$', after)
    if enumeration and len(set(_mentions(enumeration.group(1), nodes))) == len(nodes) and not _has(r'\b'+_VERB+r'\b', enumeration.group(1)):
        return True
    noun = re.match(r'\s+([a-z]+)\b', after)
    if not noun:
        return False
    head = _singular(noun.group(1))
    if _has(r'\bof (?:the )?$', text.split(token, 1)[0]) and head not in _UNITS:
        return True
    # "two bowls" identifies "first bowl" and "second bowl"; "two
    # ponds" identifies "pond A" and "pond B", regardless of the noun.
    if all(head in _words(node) for node in nodes):
        return True
    if query and _has(r'\bthe '+token+r' [a-z]+s\b', text) and _has(_TOTAL+r'|\bdifference\b', text):
        return head not in _UNITS and head not in ('year', 'month')
    return False


def _expand_parallel(body):
    """Make the reference explicit in "some X and three times as many Y"."""
    pattern = (r'\b(some|q\d+) ([a-z]+(?: [a-z]+){0,4}?) and (' + _FACTOR +
               r') as (many|much) ([^.;]+)')
    def expand(m):
        if _has(r'\bas\b|\bq\d+\b', m.group(5)):
            return m.group()
        return '{} {}. {} as {} {} as {}'.format(*m.groups(), m.group(2))
    return re.sub(pattern, expand, body)


def _mentions(text, labels):
    found = []
    for label in labels:
        for m in re.finditer(r'\b' + re.escape(label) + r"(?:'s)?\b", text):
            found.append((m.start(), label))
    return [label for _, label in sorted(found)]


def _category_mentions(text, nodes):
    # A distinguishing word allows "female members" to anchor "females".
    words = _words(text)
    found = []
    for node in nodes:
        unique = _words(node) - set(w for other in nodes if other != node for w in _words(other))
        if unique and unique <= words:
            found.append(node)
    return found


def _result(answer, working):
    if answer < 0:
        return None
    return answer, working + '.'


def _graph(p):
    if re.search(r'\bneed\b.*\badd\b', p.question):
        return None
    if re.search(r'\b(?:share[ds]?|split|divide[ds]?)\b.*\bequally\b', p.question):
        return None
    if re.search(r'\bnot\b', p.question):
        return None
    # A kinship phrase denotes a distinct owner, and a quantity after "some"
    # anchors its explicit category rather than the first mentioned category.
    if (re.search(r'\bhas some [a-z]+,', p.body) or
            re.search(r'\b(?:his|her) (?:sister|brother|mother|father|mom|dad)\b', p.body)
            and not re.search(r'\b(?:old|age|ages|years?)\b', p.body)):
        return None
    if re.search(r'\btimes (?:the )?(?:number|amount) of [a-z]+(?: [a-z]+){0,2} as [a-z]+\b', p.body):
        return None
    # Relative clauses identify subgroups or distinct objects, not a single
    # variable for the actor or the common head noun.
    if re.search(r'\bas those who\b|\bnumber of [a-z]+(?: [a-z]+)? [A-Z][a-z]+ (?:washed|cooked|picked|found)\b', p.text):
        return None
    # Experience comparisons need the elapsed years on both sides, just as
    # age does. The later comparison adapter supplies that age interpretation.
    if re.search(r'\byears? of experience\b', p.text, re.I):
        return None
    parts = _tokens(p)
    if parts is None or any(n.kind == 'percent' for n in p.numbers) or len(p.numbers) > 7:
        return None
    body, query = parts
    measurements = []
    for n in p.numbers:
        unit = re.match(r'\s+(' + _UNIT + r')\b', p.text[n.end:].lower())
        if unit:
            measurements.append(_UNITS[_singular(unit.group(1))])
    if len(set(measurements)) > 1:
        # This graph has one unit per variable. Conversion is handled by the
        # explicit measured-comparison schema rather than mixing units here.
        return None
    body = re.sub(r'(?<=[a-z])-(?=[a-z])', ' ', body)
    query = re.sub(r'(?<=[a-z])-(?=[a-z])', ' ', query)
    if not _has(_FACTOR + r'|\b(?:more|less|fewer|older|younger|heavier|lighter) than\b', body):
        return None
    if _has(r'\b(?:per|every|each|average|rate|ratio|remaining|remains|gave away|loses|lost|spent|spends|removed|discount|percent)\b', body):
        # "Each square meter needs ..." describes a ratio of materials, not
        # repeated amounts, but is otherwise an ordinary category comparison.
        body = re.sub(r'\beach square (?:meter|foot|yard) needs\b', 'the surface needs', body)
        if _has(r'\b(?:per|every|each|average|rate|ratio|remaining|remains|gave away|loses|lost|spent|spends|removed|discount|percent)\b', body):
            return None
    names = _names(p.text)
    body = _expand_parallel(body)
    used_labels, display_labels = set(), {}
    for m in list(re.finditer(r'\b(period|grade|class|room|group|team|pond) (q\d+)\b', body + query)):
        token = m.group(2)
        value = _value(token, p)
        if value.denominator != 1 or value < 0:
            return None
        # Label numbers identify variables and never enter arithmetic.
        label = m.group(1) + ' label' + ''.join(chr(ord('a') + int(d)) for d in str(value))
        names = [n for n in names if n != m.group(1)]
        names.append(label)
        display_labels[label] = m.group(1) + ' ' + format_number(value)
        body = body.replace(m.group(), label)
        query = query.replace(m.group(), label)
        used_labels.update(_indices(token))
    for m in re.finditer(r'\b(?:first|second|third) [a-z]+\b', body):
        if m.group() not in names:
            names.append(m.group())
    for name in names:
        # A second "as" is sometimes omitted before a named possessor:
        # "twice as much money Ada has".
        body = re.sub(r'\bas (many|much) ([a-z]+) (' + re.escape(name) +
                      r') (has|had|have)\b', r'as \1 \2 as \3 \4', body)
        body = re.sub(r'\bas old (' + re.escape(name) + r')\b', r'as old as \1', body)
    # Capitalised context words are harmless unless used as equation variables.
    clauses = _clauses(body)
    edges, used = [], used_labels
    subject = None
    age = bool(_has(r'\bage|\byears? old|\bas (?:old|young)\b|\byounger|\bolder', body))
    age_context = Fraction(0)
    for clause in clauses:
        matches = list(_MULT.finditer(clause))
        add_matches = list(_ADD.finditer(clause)) if not matches else []
        if len(matches) + len(add_matches) > 1:
            return None
        if not matches and not add_matches:
            if _has(_FACTOR, clause):
                return None
            future = _future(clause, p) if age else None
            if future:
                age_context = future[0]
            ns = _mentions(clause, names)
            if ns:
                subject = ns[-1]
            continue
        match = (matches or add_matches)[0]
        before, after = clause[:match.start()], clause[match.end():]
        mult = bool(matches)
        if not mult and _has(_FACTOR, clause):
            return None
        offset = Fraction(0)
        relation_text = match.group()
        if mult:
            scale = _factor(match.group(1), p)
            if match.group(2) == 'young' or match.group(4) == 'younger':
                if not scale:
                    return None
                scale = 1 / scale
            delta = re.search(r'\b(q\d+)\s+(?:[a-z]+\s+){0,2}?(more|less|fewer)\s*(?:[a-z]+\s+){0,4}?than\s*$', before)
            if delta:
                offset = _value(delta.group(1), p) * _SIGN.get(delta.group(2), 1)
                relation_text += delta.group()
                before = before[:delta.start()]
            suffix = re.search(r'\s+(minus|plus)\s+(q\d+)\b', after)
            if suffix:
                offset += _value(suffix.group(2), p) * (-1 if suffix.group(1) == 'minus' else 1)
                relation_text += suffix.group()
                after = after[:suffix.start()]
            middle = match.group(3) or ''
        else:
            scale = Fraction(1)
            offset = _value(match.group(1), p) * _SIGN.get(match.group(3), 1)
            middle = match.group(4) or match.group(2) or ''
        left_names = _mentions(before, names)
        right_names = _mentions(after, names)
        middle_names = _mentions(middle, names)
        # Periods are separate amounts even when the same person owns both.
        left_period = _periods(before + ' ' + middle)
        right_period = _periods(after)
        if left_period and right_period:
            left, right = left_period[-1], right_period[0]
        elif (left_names or middle_names) and right_names:
            left = middle_names[-1] if middle_names else left_names[-1]
            right = right_names[0]
            # A grouped reference requires an explicit group variable, not one
            # arbitrarily chosen member of "A and B combined".
            if len(set(right_names)) > 1:
                return None
        elif age and (left_names or subject) and _has(r'\b(?:he|she|him|her|his)\b', after):
            left = left_names[-1] if left_names else subject
            alternatives = [n for n in left_names if n != left]
            if not alternatives:
                alternatives = [n for n in names if n != left and _has(r'\b'+re.escape(n)+r'\b', body[:body.find(clause)])]
            if len(alternatives) != 1:
                return None
            right = alternatives[0]
        elif not left_names and subject and right_names and _has(r'^\s*(?:he|she|it)\b', before):
            left, right = subject, right_names[0]
        else:
            left, right = _category(middle), _category(after)
            if not mult and middle.strip() in ('expensive', 'heavy', 'tall', 'long'):
                left = _subject(before)
            if mult and not left:
                left = _subject(before)
            if not mult and not left:
                left = _subject(before)
            if not left or not right:
                return None
        if left == right or scale <= 0:
            return None
        if age:
            left_time, right_time = _future(before, p), _future(after, p)
            if left_time:
                age_context = left_time[0]
                # At a shared future date, A+t = k*(B+t)+d.
                right_current = _has(r'\b(?:today|currently|now|current age)\b', after)
                right_years = right_time[0] if right_time else (Fraction(0) if right_current else left_time[0])
                offset += scale*right_years-left_time[0]
                used.update(left_time[1])
                if right_time:
                    used.update(right_time[1])
            elif right_time:
                # A is compared with B's future age: A = k*(B+t)+d.
                offset += scale*right_time[0]
                used.update(right_time[1])
            elif _has(r'\bat that time\b', before):
                right_years = Fraction(0) if _has(r'\b(?:today|currently|now|current age)\b', after) else age_context
                offset += scale*right_years-age_context
        edges.append((left, right, scale, offset))
        used.update(_indices(relation_text))
        subject = left
    if not edges:
        return None
    nodes = set(n for edge in edges for n in edge[:2])
    if not 2 <= len(nodes) <= 3:
        return None
    known, total = [], None
    # Ages given in the future are anchors at that date; the graph represents
    # current ages. A difference of ages remains constant at a shared date.
    shifted_values = {}
    query_shift = Fraction(0)
    query_scale = Fraction(1)
    purchase = re.search(r'\bfor (q\d+) (.+?)[?.]*$', query)
    if purchase and _has(r'\b(?:costs?|price)\b', body) and _has(r'\b(?:pay|cost|spend)\b', query):
        bought = _category_mentions(purchase.group(2), nodes)
        if len(bought) != 1:
            return None
        query_scale = _value(purchase.group(1), p)
        used.update(_indices(purchase.group(1)))
    if age:
        for clause in clauses:
            past = re.search(r'\b(q\d+|a|an) years? ago\b', clause)
            if past:
                numbers = _indices(clause) - used - _indices(past.group())
                if len(numbers) != 1 or _MULT.search(clause) or _ADD.search(clause):
                    return None
                index = next(iter(numbers))
                years = _value(past.group(1), p) if past.group(1).startswith('q') else Fraction(1)
                shifted_values[index] = p.values[index] + years
                used.update(_indices(past.group()))
            shift = re.search(r'\b(?:in|after) (q\d+) years?\b', clause)
            if shift:
                if (_MULT.search(clause) or _ADD.search(clause)) and _indices(shift.group()) <= used:
                    continue
                numbers = _indices(clause) - used - _indices(shift.group())
                if len(numbers) == 1 and not _has(_FACTOR, clause):
                    index = next(iter(numbers))
                    shifted_values[index] = p.values[index] - _value(shift.group(1), p)
                    used.update(_indices(shift.group()))
                elif _has(r'years? (?:older|younger) than', clause) and not _has(_FACTOR, clause):
                    used.update(_indices(shift.group()))
                else:
                    return None
        shift = re.search(r'\b(?:in|after) (q\d+) years?\b', query)
        if shift:
            query_shift = _value(shift.group(1), p)
            used.update(_indices(shift.group()))
    for i, value in enumerate(p.values):
        if i in used:
            continue
        token = 'q' + str(i)
        if _has(r'\b'+token+r'\b', query):
            if _group_label(value, token, query, nodes, query=True):
                continue
            return None
        containing = [c for c in clauses if _has(r'\b'+token+r'\b', c)]
        if len(containing) != 1:
            return None
        clause = containing[0]
        # A conditional anchor can follow the relation in the same sentence.
        local = re.split(r'\bif\b', clause)[-1] if 'if ' in clause else clause
        before, after = local.split(token, 1)
        if _group_label(value, token, local, nodes):
            continue
        if _has(r'\b(?:more|less|fewer|twice|double|triple|times)\b', before):
            return None
        owners = _mentions(before, nodes & set(names))
        cats = _category_mentions(after, nodes - set(names))
        periods = [node for node in nodes if node in _periods(local)]
        explicit_total = _has(_TOTAL, local) or _has(r'\bbetween\b.*\bof them\b', local)
        joint = len(set(_mentions(local, nodes))) == len(nodes) and _has(r'\band\b.*\b(?:have|had|got|received|sold|shared|split)\b', local)
        category_joint = len(_category_mentions(after, nodes - set(names))) == len(nodes) and _has(r'\band\b', after)
        joint = joint or category_joint
        local_cats = _category_mentions(local, nodes - set(names))
        single_anchor = len(set(owners)) == 1 or len(local_cats) == 1
        if (explicit_total and not (single_anchor and not joint)) or joint:
            if total is not None:
                return None
            total = value
        elif periods and len(periods) == 1:
            known.append((periods[0], value))
        elif owners:
            known.append((owners[-1], shifted_values.get(i, value)))
        elif len(cats) == 1:
            known.append((cats[0], value))
        else:
            before_cats = _category_mentions(before, nodes - set(names))
            places = _mentions(after, nodes & set(names))
            if len(places) == 1 and _has(r'\b(?:in|at|of)\b', after):
                known.append((places[0], value))
            elif len(before_cats) == 1:
                known.append((before_cats[0], value))
            else:
                return None
    solved = _solve_graph(edges, known, total)
    if solved is None:
        return None
    relative = _relative_query(body, query, nodes, names)
    # Asking for the cost of an assembly concerns all its components. The
    # extended comparison reader can sum those; a mentioned component alone
    # does not identify the requested cost.
    if _has(r'\bcost to (?:plant|build|make|assemble)\b', query):
        return None
    if relative is None and _has(r"'s (?:sister|brother|mother|father|daughter|son|grandmother|grandfather)\b", query):
        return None
    named = relative or _mentions(query, nodes & set(names))
    asked = list(set(named)) if named else _category_mentions(query, nodes)
    children = (_has(r'\bchildren\b', query) and
                {_singular(n) for n in nodes} == {'son', 'daughter'})
    if (_has(_TOTAL, query) and len(asked) != 1) or children or (_has(r'\bshared\b', query) and _has(r'\bshared\b.*\bbetween\b', body)):
        if query_shift:
            return None
        answer = sum((solved[n] for n in (asked if len(asked) > 1 else nodes)), Fraction(0))
    elif _has(r'\bdifference\b|\bhow (?:many|much) (?:more|fewer|less)\b', query):
        pair = asked if len(asked) == 2 else list(nodes)
        if len(pair) != 2 or query_shift:
            return None
        a, b = (solved[n] for n in pair)
        answer = abs(a - b)
    elif len(asked) == 1:
        answer = (solved[asked[0]] + query_shift) * query_scale
    else:
        return None
    return _result(answer, '; '.join('{} = {}'.format(display_labels.get(n, n), format_number(solved[n])) for n in sorted(nodes)))


def _solve_graph(edges, known, total):
    solved = _equation_graph(edges, known, total)
    if solved is not None or known or total is not None:
        return solved
    # Two independent comparisons may themselves anchor the amounts:
    # A = B + d and A = k*B imply (k-1)*B = d.
    for i, (left, right, scale, offset) in enumerate(edges):
        for a, b, k, d in edges[i+1:]:
            if (a, b) == (right, left) and k:
                a, b, k, d = b, a, 1/k, -d/k
            if (a, b) == (left, right) and scale != k:
                anchor = (d-offset)/(scale-k)
                return _equation_graph(edges, [(right, anchor)], None)
    return None


def _unlabelled_equation(p):
    """An explicit affine expression equal to a known number, solve its base."""
    parts = _tokens(p)
    if parts is None:
        return None
    body, query = parts
    pattern = (r'^\s*(q\d+) (less|more) than (' + _FACTOR + r') '
               r'(?:the )?number of (.+?) (?:is|equals) (q\d+)\s*[., ]*$')
    m = re.fullmatch(pattern, body)
    if not m or _indices(m.group()) != set(range(len(p.numbers))):
        return None
    category = _category(m.group(4))
    if not category or not (_words(category) & _words(query)):
        return None
    scale = _factor(m.group(3), p)
    if scale <= 0:
        return None
    offset = _value(m.group(1), p) * (-1 if m.group(2) == 'less' else 1)
    answer = (_value(m.group(5), p) - offset) / scale
    return _result(answer, '({} - ({})) / {}'.format(format_number(_value(m.group(5), p)), format_number(offset), format_number(scale)))


# Physical conversion factors, independent of the story's objects.
_UNITS = {
    'second': ('time', Fraction(1)), 'minute': ('time', Fraction(60)),
    'hour': ('time', Fraction(3600)), 'day': ('time', Fraction(86400)),
    'week': ('time', Fraction(604800)), 'ounce': ('mass', Fraction(1)),
    'pound': ('mass', Fraction(16)), 'inch': ('length', Fraction(1)),
    'foot': ('length', Fraction(12)), 'yard': ('length', Fraction(36)),
    'gram': ('metric_mass', Fraction(1)), 'kilogram': ('metric_mass', Fraction(1000)),
    'centimeter': ('metric_length', Fraction(1)), 'meter': ('metric_length', Fraction(100)),
    'kilometer': ('metric_length', Fraction(100000)),
}
_UNIT = r'(?:seconds?|minutes?|hours?|days?|weeks?|ounces?|pounds?|inches|inch|feet|foot|yards?|grams?|kilograms?|centimeters?|meters?|kilometers?)'


def _mixed_unit_sum(p):
    """A measured amount and an explicitly different amount, asked in one unit."""
    if len(p.numbers) != 2 or not _has(_TOTAL, p.question):
        return None
    if _has(r'\b(?:per|each|every|times|twice|double|half|percent|average|daily|weekly|monthly|yearly)\b|\b(?:a|an) (?:day|week|month|year|night)\b', p.body):
        return None
    requested = re.search(r'\b(?:how (?:many|much)|in) (' + _UNIT + r')\b', p.question)
    if not requested:
        return None
    dest = _UNITS[_singular(requested.group(1))]
    units, delta = [], []
    for i, n in enumerate(p.numbers):
        if n.end > len(p.body):
            return None
        tail = p.text[n.end:].lower()
        unit = re.match(r'\s+(' + _UNIT + r')\b', tail)
        if not unit:
            return None
        measure = _UNITS[_singular(unit.group(1))]
        if measure[0] != dest[0]:
            return None
        units.append(n.value*measure[1]/dest[1])
        adjustment = re.match(r'\s+(more|less|fewer|longer|shorter|heavier|lighter|taller) than\b', tail[unit.end():])
        if adjustment:
            delta.append((i, _SIGN.get(adjustment.group(1), 1)))
    if len(delta) != 1:
        return None
    i, sign = delta[0]
    base, change = units[1-i], units[i]
    if base + sign*change < 0:
        return None
    answer = 2*base + sign*change
    return _result(answer, '{} + ({} {} {}) {}'.format(format_number(base), format_number(base), '+' if sign > 0 else '-', format_number(change), requested.group(1)))


def solve(problem):
    # A multiplier on a combined left side must not be discarded while
    # reading the comparison on the right side.
    if re.search(r'\b(?:twice|thrice|double|triple|\w+ times) (?:the )?sum of\b', problem.body):
        return None
    # Unnamed possessive relatives are people, not object categories. The
    # extended comparison skill resolves these references explicitly.
    relatives = set(re.findall(r'\b(?:her|his|their) (sister|brother|mother|father|grandmother|grandfather)\b', problem.body))
    if len(relatives) > 1:
        return None
    for rule in (_mixed_unit_sum, _unlabelled_equation, _graph):
        result = rule(problem)
        if result is not None:
            return result
    return None
