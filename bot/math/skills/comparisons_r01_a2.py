"""Explicit affine comparisons, with a known amount or a combined total.

Relations are equations between named owners or explicitly compared categories.
All quantities must be accounted for before solving the connected equation graph.
"""
import re
from fractions import Fraction

from ..numbers import format_number
from ..problem import ASK


# Sentence-initial function words are not entity names.
_NOT_NAMES = set(('a an the if when how what there at in on after before together '
                  'this that he she his her they their it its now three two one '
                  'twice thrice double triple both all').split())
_FACTOR = r'(?:twice|thrice|double|triple|Q\d+ times)'


def _names(text):
    names = []
    for m in re.finditer(r"\b[A-Z][a-z]+(?: (?:[A-Z][a-z]+|[A-Z](?![a-z])))*(?:'s)?", text):
        name = re.sub(r"'s$", '', m.group().lower())
        words = name.split()
        while words and words[0] in _NOT_NAMES:
            words.pop(0)
        name = ' '.join(words)
        if name and name not in names:
            names.append(name)
    return names


def _mentions(text, names):
    found = []
    for name in names:
        for m in re.finditer(r'\b' + re.escape(name) + r"(?:'s)?\b", text, re.I):
            found.append((m.start(), name))
    return [name for _, name in sorted(found)]


def _noun(text):
    text = re.sub(r'^(?:the |a |an |number of |amount of )+', '', text.strip())
    if re.match(r'(?:he|she|they|it|his|her|their)\b', text) or re.search(r'\bfor (?:his|her|their)\b', text):
        return None
    text = re.split(r'\b(?:that|who|which|in|at|on|for|to|did|does|do|has|have|had|is|are|was|were|will|as|costs|cost|weighs|weigh|spends|spend)\b|[,.;?!]', text)[0]
    text = text.strip()
    return text if re.fullmatch(r'[a-z]+(?: [a-z]+){0,5}', text) else None


def _factor(token, values):
    return {'twice': Fraction(2), 'thrice': Fraction(3), 'double': Fraction(2),
            'triple': Fraction(3)}.get(token, values[int(token[1:].split()[0])] if token.startswith('Q') else None)


def _equation_graph(edges, known, total):
    """Represent each connected variable as a*x+b, then solve the anchor."""
    nodes = set(n for e in edges for n in e[:2])
    if not 2 <= len(nodes) <= 3:
        return None
    root = sorted(nodes)[0]
    forms = {root: (Fraction(1), Fraction(0))}
    for _ in range(len(nodes)):
        for left, right, scale, offset in edges:
            if right in forms and left not in forms:
                a, b = forms[right]
                forms[left] = (scale*a, scale*b+offset)
            elif left in forms and right not in forms and scale:
                a, b = forms[left]
                forms[right] = (a/scale, (b-offset)/scale)
    if len(forms) != len(nodes):
        return None
    anchors = []
    for node, value in known:
        if node not in forms:
            return None
        a, b = forms[node]
        if not a:
            return None
        anchors.append((value-b)/a)
    if total is not None:
        a = sum(x[0] for x in forms.values())
        b = sum(x[1] for x in forms.values())
        if not a:
            return None
        anchors.append((total-b)/a)
    if not anchors or any(x != anchors[0] for x in anchors):
        return None
    result = {node: a*anchors[0]+b for node, (a, b) in forms.items()}
    if any(v < 0 for v in result.values()):
        return None
    for left, right, scale, offset in edges:
        if result[left] != scale*result[right]+offset:
            return None
    return result


def _comparisons(p):
    values = p.values
    if any(n.kind == 'percent' for n in p.numbers) or len(values) > 5:
        return None
    # Time shifts, rates and transactions need other schemas.
    if re.search(r'\b(?:ago|from now|per|each|every|sold|owes|remaining|left|average|faster|fast)\b', p.body):
        return None
    names = _names(p.text)
    text = p.text.lower()
    for i, n in reversed(list(enumerate(p.numbers))):
        text = text[:n.start] + 'Q' + str(i) + text[n.end:]
    # Work on clauses, keeping a shared subject for coordinated comparisons.
    # Number replacement changes offsets; locate the question by its cue instead.
    cues = list(ASK.finditer(text))
    if not cues:
        return None
    cue = cues[-1]
    body, query = text[:cue.start()], text[cue.start():]
    if re.search(r'\b(?:more|less|fewer|difference|older|younger|percent|average|ratio|remaining|left)\b', query):
        return None
    trailing_total = re.search(r'(?<=[.;])\s*(together|combined|altogether),?\s*$', body)
    if trailing_total:
        query = trailing_total.group(1) + ' ' + query
        body = body[:trailing_total.start()]
    body = re.sub(r'([a-z]+),? who ([a-z]+)', r'\1. \1 \2', body)
    clauses = re.split(r'[.;!?]|,?\s+and\s+(?=[a-z]+ (?:has|is|spends|runs))|\s+but\s+|\s+and\s+(?=Q\d+ (?:fewer|more|less))', body)
    edges, used = [], set()
    subject = None
    for clause in clauses:
        # An optional additive adjustment precedes the multiplicative relation.
        mult = re.search(r'(?:(Q\d+)\s+(?:[a-z]+\s+){0,2}?(more|less|fewer)\s+(?:[a-z]+\s+){0,5}?than\s+)?(' + _FACTOR + r')\s+(?:as (many|much|old|long)\s*(.*?)\s+as\s+|(?:the )?(?:number|amount) of\s+|more than\s+)', clause)
        add = None if mult else re.search(r'(Q\d+)\s+(?!times\b)(?:\w+\s+){0,3}?(more|less|fewer|older|younger|higher|lower)\b(.*?)\bthan\s+', clause)
        match = mult or add
        if not match:
            mentioned = _mentions(clause, names)
            if mentioned:
                subject = mentioned[-1]
            continue
        before, after = clause[:match.start()], clause[match.end():]
        if not _mentions(before, names) and subject and (not before.strip() or re.match(r"\s*(?:it|he|she|that(?:'s)?)\b", before)):
            before = subject + ' ' + before
        left_names, right_names = _mentions(before, names), _mentions(after, names)
        if left_names and right_names:
            left, right = left_names[-1], right_names[0]
            owning = re.search(r"([a-z]+)(?:'s)? (?:has|have|had|ate|picked|bought|runs|is)\b", after)
            if owning and owning.group(1) in right_names:
                right = owning.group(1)
        elif mult and mult.group(4) in ('many', 'much') and mult.group(5):
            left, right = _noun(mult.group(5)), _noun(after)
        elif mult and mult.group(1) and re.search(r'\b(?:more|less|fewer)\s+(.+?)\s+than', match.group()):
            left = _noun(re.search(r'\b(?:more|less|fewer)\s+(.+?)\s+than', match.group()).group(1))
            right = _noun(after)
        elif add:
            category = re.search(r'\b(?:more|less|fewer)\s+(.+?)\s+than', match.group())
            left = left_names[-1] if left_names else _noun(re.sub(r'^.*?\b(?:the)\s+', '', before))
            right = right_names[0] if right_names else _noun(after)
            if category and not right_names:
                left = _noun(category.group(1))
                right = _noun(re.sub(r'^(?:he|she|they) (?:did|does|do|bought|has|have) ', '', after))
        elif left_names and re.search(r'\b(?:he|she|him|her)\b', after):
            alternatives = [n for n in _mentions(clause, names) if n != left_names[-1]]
            if not alternatives:
                return None
            left, right = left_names[-1], alternatives[0]
        else:
            return None
        subject = left
        if not left or not right or left == right:
            return None
        if mult:
            scale = _factor(mult.group(3), values)
            delta = mult.group(1)
            offset = (values[int(delta[1:])] * (-1 if mult.group(2) in ('less', 'fewer') else 1)) if delta else Fraction(0)
        else:
            scale = Fraction(1)
            delta = add.group(1)
            offset = values[int(delta[1:])] * (-1 if add.group(2) in ('less', 'fewer', 'younger', 'lower') else 1)
        if scale <= 0:
            return None
        for token in re.findall(r'Q(\d+)', match.group()):
            used.add(int(token))
        edges.append((left, right, scale, offset))
    if not edges:
        return None
    nodes = set(n for edge in edges for n in edge[:2])
    known, total = [], None
    for i, value in enumerate(values):
        if i in used:
            continue
        token = 'Q' + str(i)
        # No quantities in the question are silently ignored.
        if token in query:
            return None
        containing = [c for c in clauses if re.search(r'\b' + token + r'\b', c)]
        if len(containing) != 1:
            return None
        clause = containing[0]
        heads = {node.split()[0] for node in nodes}
        if len(heads) == 1 and value == len(nodes) and re.search(r'\bthere (?:are|were)\s+' + token + r'\s+' + re.escape(next(iter(heads))) + r's\b', clause):
            continue
        total_cue = re.search(r'\b(?:total|sum|together|altogether|combined|collectively|in all)\b', clause)
        mentioned = [node for node in nodes if re.search(r'\b'+re.escape(node)+r"(?:'s)?\b", clause)]
        # Joint possession is also a stated total: "A and B have 40 ...".
        joint = len(mentioned) == len(nodes) and re.search(r'\band\b.*\b(?:have|spend|spent|bought|take home)\b', clause)
        listed_total = len(mentioned) == len(nodes) and re.search(r'\bincluding\b', clause)
        implicit_total = not mentioned and re.search(r'\bthere (?:are|were)\b', clause)
        # 'Nora has 12 beads in total' is Nora's anchor, not a joint sum.
        shared_total = total_cue and not (len(mentioned) == 1 and mentioned[0] in names)
        if shared_total or joint or implicit_total or listed_total:
            if total is not None:
                return None
            total = value
            continue
        # Restrict the anchor to a direct, unqualified quantity statement.
        if re.search(r'\b(?:more|less|fewer|times|twice|double|thrice|triple|than)\b', clause):
            # A separate known amount may be in an if-clause after a comparison.
            clause = re.split(r'\bif\b', clause)[-1]
        before = clause.split(token)[0]
        candidates = [node for node in nodes if re.search(r'\b'+re.escape(node)+r"(?:'s)?\b", before)]
        if candidates and any(node in names for node in candidates):
            owners = _mentions(before, names)
            if not owners or owners[-1] not in nodes:
                return None
            known.append((owners[-1], value))
        elif len(candidates) == 1:
            known.append((candidates[0], value))
        else:
            after = clause.split(token)[-1]
            candidates = [node for node in nodes if re.search(r'\b'+re.escape(node)+r'\b', after)]
            if len(candidates) != 1:
                return None
            known.append((candidates[0], value))
    solved = _equation_graph(edges, known, total)
    if solved is None:
        return None
    asked = [node for node in nodes if re.search(r'\b'+re.escape(node)+r"(?:'s)?\b", query)]
    if not asked:
        for node in nodes:
            unique = set(node.split()) - set(w for other in nodes if other != node for w in other.split())
            if any(re.search(r'\b'+re.escape(w)+r'\b', query) for w in unique):
                asked.append(node)
    if re.search(r'\b(?:total|together|altogether|combined|collectively|both|sum)\b', query):
        answer = sum((solved[node] for node in (asked if len(asked) > 1 else nodes)), Fraction(0))
    elif len(asked) == 1:
        answer = solved[asked[0]]
    else:
        return None
    working = '; '.join('{} = {}'.format(node, format_number(solved[node])) for node in sorted(nodes))
    return answer, working + '.'


def solve(problem):
    return _comparisons(problem)
