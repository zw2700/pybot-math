"""Multi-stage comparisons, with explicit references and quantity accounting.

The static reader is shared with the earlier affine skill. This module expands
elliptical references before using that reader, and handles a few distinct
schemas (geometric growth, rates after comparisons, and stock remainders).
"""
import re
from fractions import Fraction

from ..numbers import read_numbers, format_number, _WORD_NUMBER, _DIGIT
from ..problem import Problem, ASK
from .comparisons_r01_a2 import _names
from .comparisons_r03_a4 import _UNITS, _UNIT, _singular
from .comparisons_r04_a3 import _chain, _linear


_FACTOR = r'(?:twice|double|thrice|triple|quadruple|q\d+ times)'
_RELATIVE = r'(?:sister|brother|mother|father|grandmother|grandfather|mom|dad|uncle|aunt)'
_NUMBER = r'(?:' + _DIGIT + '|' + _WORD_NUMBER + ')'
_RAW_FACTOR = r'(?:twice|double|thrice|triple|quadruple|' + _NUMBER + r' times)'


def _raw_factor(raw):
    fixed = {'twice': 2, 'double': 2, 'thrice': 3, 'triple': 3, 'quadruple': 4}
    return Fraction(fixed[raw.lower()]) if raw.lower() in fixed else read_numbers(raw)[0].value


def _tokens(p):
    text = p.text.lower()
    for i, n in reversed(list(enumerate(p.numbers))):
        text = text[:n.start] + 'q' + str(i) + text[n.end:]
    return text


def _ids(text):
    return {int(i) for i in re.findall(r'\bq(\d+)\b', text)}


def _v(token, p):
    return p.values[int(token[1:])]


def _factor(token, p):
    fixed = {'twice': 2, 'double': 2, 'thrice': 3, 'triple': 3, 'quadruple': 4}
    return Fraction(fixed[token]) if token in fixed else _v(token.split()[0], p)


def _answer(value, working):
    if value < 0:
        return None
    return value, working


def _read(text, state=False):
    p = Problem.read(text)
    return _chain(p, return_values=state) if p else None


def _normalise(text):
    """Lossless syntactic expansions; no amounts or people are invented."""
    # Sentence capitalization does not make an adjective an owner name.
    text = re.sub(r'\b([A-Z][a-z]+) ([a-z]+) (are|were|weigh|cost|contain)\b',
                  lambda m: m.group(1).lower() + ' ' + m.group(2) + ' ' + m.group(3), text)
    # Shared head in "the green and blue chairs combined".
    text = re.sub(r'\b(the )?([a-z]+) and ([a-z]+) ([a-z]+) combined\b',
                  r'\1\2 \4 and \3 \4 combined', text, flags=re.I)
    text = re.sub(r'\b(?:the )?same number of (.+?) as\b',
                  r'equally as many \1 as', text, flags=re.I)
    text = re.sub(r'\b(?:the )?amount of time\b', 'amount', text, flags=re.I)
    text = re.sub(r'\b(worked|works|ran|runs|places|placed|can place)\b', 'had', text, flags=re.I)
    text = re.sub(r'\b(?:uses|used)\b', 'has', text, flags=re.I)
    # Explicit packages supply a measured quantity (count times package size).
    package = r'\b(' + _NUMBER + r') (' + _NUMBER + r')[- ](pound|ounce|kilogram|gram|foot|yard)[ -]([a-z]+) of ([a-z]+)'
    def measured(m):
        a, b = read_numbers(m.group(1))[0].value, read_numbers(m.group(2))[0].value
        unit = 'feet' if m.group(3).lower() == 'foot' else m.group(3) + 's'
        return str(a*b) + ' ' + unit + ' of ' + m.group(5)
    text = re.sub(package, measured, text, flags=re.I)
    text = re.sub(r'\bbrought\b', 'had', text, flags=re.I)
    # Modal verbs do not change the counted quantity.
    text = re.sub(r'\b(?:had|has) for\b', 'had', text, flags=re.I)
    text = re.sub(r',?\s+while\s+', '. ', text, flags=re.I)
    text = re.sub(r'(?<=[.;])\s*And\s+', ' ', text)
    text = re.sub(r'\bhow many (.+?) (?:are|were) (?:in|on|at) [^?]+\?', r'how many \1?', text, flags=re.I)
    if re.search(r'\bat the end of the season\b', text, re.I):
        text = re.sub(r'^[^.;]+\bevery (?:week|day)[.;]\s*', '', text, flags=re.I)
    text = re.sub(r'\b(?:had won|has won|won)\b', 'had', text, flags=re.I)
    text = re.sub(r'\b(longer|shorter) than\b', lambda m: 'more than' if m.group(1).lower() == 'longer' else 'less than', text, flags=re.I)
    text = re.sub(r'\bhow many (' + _UNIT + r') (longer|shorter) (.+)',
                  lambda m: 'How much ' + ('more' if m.group(2).lower() == 'longer' else 'less') + ' ' + m.group(3), text, flags=re.I)
    text = re.sub(r'\b(' + _RAW_FACTOR + r') their (monday|tuesday|wednesday|thursday|friday|saturday|sunday) earnings\b',
                  r'\1 as much as \2', text, flags=re.I)
    text = re.sub(r'\b(' + _RAW_FACTOR + r') the total number of ([a-z]+) (.+?) received\b',
                  r'\1 as many \2 as \3 combined', text, flags=re.I)
    # Direct anchors can themselves contain explicit arithmetic.
    def numeric_anchor(m):
        a, b = read_numbers(m.group(2))[0].value, read_numbers(m.group(5))[0].value
        value = b-a if m.group(4).lower() in ('less', 'fewer') else b+a
        return m.group(1) + ' has ' + str(value) + ' ' + m.group(3) if value >= 0 else m.group()
    text = re.sub(r'\b([A-Z][a-z]+) has (' + _NUMBER + r') ([a-z]+(?: [a-z]+)?) (less|fewer|more) than (' + _NUMBER + r')\b', numeric_anchor, text)
    def purchased_anchor(m):
        total, price = read_numbers(m.group(2))[0].value, read_numbers(m.group(3))[0].value
        return m.group(1) + ' had ' + str(total/price) + ' ' + m.group(4) if price > 0 else m.group()
    text = re.sub(r'\b([A-Z][a-z]+) spent (\$\s*' + _DIGIT + r') on (\$\s*' + _DIGIT + r') ([a-z]+)\b', purchased_anchor, text)
    # A known age followed by a comparison keeps the same subject.
    text = re.sub(r'\b([A-Z][a-z]+) is (' + _NUMBER + r') and is\b', r'\1 is \2 years old. \1 is', text)
    text = re.sub(r'\b(' + _RAW_FACTOR + r") ([A-Z][a-z]+)'s money\b", r'\1 as much as \2', text)
    text = re.sub(r'\bas ([A-Z][a-z]+) and ([A-Z][a-z]+) (?:has|have) together\b', r'as \1 and \2 combined', text)
    appositive = (r'\b([A-Z][a-z]+) (has|had|got) (' + _NUMBER + r') ([a-z]+(?: [a-z]+)?),\s*('
                  + _NUMBER + r') ([a-z]+(?: [a-z]+)?) (more|less|fewer) than\b')
    text = re.sub(appositive, r'\1 \2 \3 \4. \1 has \5 \6 \7 than', text)
    def joint(m):
        fragments = re.split(r'\s+but only\s+', m.group(3))
        return '. '.join(owner + ' has ' + part for owner in (m.group(1), m.group(2)) for part in fragments)
    text = re.sub(r'\b([A-Z][a-z]+) and ([A-Z][a-z]+) each have ([^.;]+)', joint, text)
    text = re.sub(r'(\d+/\d+)(?:st|nd|rd|th)? as many\b', r'\1 times as many', text, flags=re.I)
    text = re.sub(r'\bas the combined number of ([^.;]+?) and ([^.;]+?)(?=[.;])',
                  r'as \1 and \2 combined', text, flags=re.I)
    # Both sides of an equality may be scaled sums. Move the left scale to
    # the right before the ordinary named-owner equation reader sees it.
    scaled_sum = r'\b(' + _RAW_FACTOR + r') (?:the )?sum of (.+?) (?:is|equals) (' + _RAW_FACTOR + r') (?:the )?(?:number|amount) of ([^.;?,]+)'
    def sum_relation(m):
        left, right = _names(m.group(2)), _names(m.group(4))
        if len(left) != 2 or len(right) != 1:
            return m.group()
        if not _raw_factor(m.group(3)):
            return m.group()
        k = _raw_factor(m.group(1)) / _raw_factor(m.group(3))
        return '{} has {} times as many items as {} and {} combined'.format(
            right[0].title(), str(k), left[0].title(), left[1].title())
    text = re.sub(scaled_sum, sum_relation, text, flags=re.I)
    text = re.sub(r'\bhas just turned (' + _NUMBER + r')\b', r'is \1 years old', text, flags=re.I)
    # A reciprocal age relation ("three times younger") uses the same
    # conventional ratio as "one third as old".
    def younger(m):
        k = read_numbers(m.group(1))[0].value
        return str(1/k) + ' times as old as' if k > 0 else m.group()
    text = re.sub(r'\b(' + _NUMBER + r') times younger than\b', younger, text, flags=re.I)
    text = re.sub(r'\b[Tt]he age of ([A-Z][a-z]+) is equal to (.+?) the sum of the ages of (.+?) and ([A-Z][a-z]+)\b',
                  r'\1 is \2 as old as \3 and \4 combined', text)
    text = re.sub(r"\b([A-Z][a-z]+)' (?=(?:(?:older|younger) )?" + _RELATIVE + r'\b)', r"\1's ", text)
    text = re.sub(r'\b([A-Z][a-z]+) who is\b', r'\1. \1 is', text)
    # Parallel counts omit a reference only when the preceding count supplies
    # the category in the very same clause.
    parallel = (r'\b(' + _NUMBER + r') ([a-z]+(?: [a-z]+){0,2}?) and '
                r'(twice|thrice|' + _NUMBER + r' times) as (many|much) ([a-z]+(?: [a-z]+){0,2}?)(?=[.;])')
    text = re.sub(parallel, r'\1 \2. \3 as \4 \5 as \2', text, flags=re.I)
    # Repeated predicate in a coordinated pair of comparisons.
    text = re.sub(r'\b(the number of [a-z]+ is) ([^.;]+?) and (' + _NUMBER + r' times (?:more than|as many as))',
                  r'\1 \2. \1 \3', text, flags=re.I)
    # A pronoun in a dated age clause retains the preceding sole named owner.
    sentences = re.split(r'(?<=[.;])\s+', text)
    for i in range(1, len(sentences)):
        prior_names = _names(sentences[i-1])
        if len(prior_names) == 1:
            sentences[i] = re.sub(r'^(' + _NUMBER + r' years? ago,?\s*)(?:he|she)\b',
                                  prior_names[0].title() + r' \1', sentences[i], flags=re.I)
    text = ' '.join(sentences)
    # One named family owner, with repeated unnamed relatives.
    cues = list(ASK.finditer(text))
    primary = _names(text[:cues[-1].start()] if cues else text)
    if len(primary) == 1:
        possessor = r'(?:her|his|their|' + re.escape(primary[0]) + r"'s)"
        relatives = list(dict.fromkeys(m.group(1).lower() for m in re.finditer(
            r'\b' + possessor + r' (?:older |younger )?(' + _RELATIVE + r')\b', text, re.I)))
        for i, relative in enumerate(relatives):
            label = 'Kin' + chr(97+i)
            text = re.sub(r'\b' + possessor + r' (?:older |younger )?' + relative + r'\b', label, text, flags=re.I)
        text = re.sub(r'\b(' + _RAW_FACTOR + r') (?:his|her) age\b',
                      lambda m: m.group(1) + ' as old as ' + primary[0].title(), text, flags=re.I)
        if re.search(r'\b(?:old|older|younger|age)\b', text, re.I):
            text = re.sub(r'\bthan (?:him|her)\b', 'than ' + primary[0].title(), text, flags=re.I)
    text = re.sub(r'\bhow many years (older|younger)\b', r'how much \1', text, flags=re.I)
    # "B had twice that amount" explicitly refers to the preceding owner.
    names = _names(text)
    pattern = r'\b(twice|thrice|double|triple|\d+(?:\.\d+)? times) that amount\b'
    def previous(m):
        clause_start = max(text.rfind('.', 0, m.start()), text.rfind(' and ', 0, m.start()))
        prior = [(hit.start(), name) for name in names for hit in re.finditer(
            r'\b' + re.escape(name) + r'\b', text[:max(0, clause_start)], re.I)]
        if not prior:
            return m.group()
        return m.group(1) + ' as much as ' + max(prior)[1].title()
    text = re.sub(pattern, previous, text, flags=re.I)
    # A target shortfall is an additive negative offset.
    text = re.sub(r'\b(needs?) (.+?) more ([a-z]+) to have (.+?) as many \3 as\b',
                  r'has \2 fewer than \4 as many \3 as', text, flags=re.I)
    text = re.sub(r'\bneeds? (' + _NUMBER + r') more ([a-z]+) to have the same number as\b',
                  r'has \1 fewer \2 than', text, flags=re.I)
    # Commas introduce a repeated subject for appositive comparisons.
    text = re.sub(r'\b([a-z]+),? which had\b', r'\1. \1 had', text, flags=re.I)
    # "Three times that many X" refers to a named amount or to the count
    # immediately before it. Require a literal local antecedent.
    that_many = r'\b(' + _RAW_FACTOR + r') that many ([a-z]+(?: [a-z]+){0,2}?)(?=[,.;]|\s+and\s+[A-Z])'
    def many(m):
        prefix = text[:m.start()]
        boundary = max(prefix.rfind('. '), prefix.rfind(', '), prefix.rfind(' and '))
        older = prefix[:max(boundary, 0)]
        names = _names(older)
        if names:
            return '{} as many {} as {}'.format(m.group(1), m.group(2), names[-1].title())
        nums = read_numbers(prefix)
        if not nums:
            return m.group()
        category = re.match(r'\s+([a-z]+(?: [a-z]+){0,2}?)[,.;]\s*$', prefix[nums[-1].end:])
        if not category:
            return m.group()
        return '{} as many {} as {}'.format(m.group(1), m.group(2), category.group(1))
    text = re.sub(that_many, many, text, flags=re.I)
    # A trailing past date with "was" scopes the whole age comparison.
    text = re.sub(r'\b([A-Z][a-z]+) was ([^.;]+?) (' + _NUMBER + r') years? ago(?=[.;])',
                  r'\3 years ago, \1 was \2', text)
    text = re.sub(r'\ba decade ago\b', '10 years ago', text, flags=re.I)
    return text


def _adapted_chain(p):
    if re.search(r'\b[a-z]+ [A-Z] (?:has|contains|holds)\b',p.text):
        return None  # Letter-labelled containers need their own quantity graph.
    text = _normalise(p.text)
    scale = Fraction(1)
    # Convert only the requested output unit; intermediate comparisons share a unit.
    asks = list(ASK.finditer(text))
    if not asks:
        return None
    ask = asks[-1]
    body, query = text[:ask.start()], text[ask.start():]
    query = re.sub(r'\bthe (' + _NUMBER + r') (?:received|bought|collected|earned|scored)\b', r'the \1 have', query, flags=re.I)
    if not re.search(r'\b(?:age|old|older|younger)\b', query, re.I):
        query = re.sub(r'\bin (' + _NUMBER + r') (days|weeks|months)\b', r'over \1 \2', query, flags=re.I)
    opening = re.match(r'[^.;!?]+[.;]\s*', body)
    if opening and not read_numbers(opening.group()) and re.search(r'\beach bought a\b', opening.group(), re.I):
        body = body[opening.end():]
    unit_matches = []
    for n in read_numbers(body):
        m = re.match(r'\s+(' + _UNIT + r')\b', body[n.end:], re.I)
        if m:
            unit_matches.append(_singular(m.group(1).lower()))
    dest = re.search(r'\b(?:how (?:many|much)|in) (' + _UNIT + r')\b', query, re.I)
    output_unit = dest.group(1).lower() if dest else None
    if output_unit in ('ounce', 'ounces'):
        output_unit = 'oz'
    if dest and unit_matches and len(set(unit_matches)) == 1:
        source = unit_matches[0]
        target = _singular(dest.group(1).lower())
        if _UNITS[source][0] != _UNITS[target][0]:
            return None
        scale = _UNITS[source][1] / _UNITS[target][1]
        query = query[:dest.start(1)] + source + query[dest.end(1):]
    def finish(result):
        value, working = result[0]*scale, result[1]
        if output_unit:
            noun = re.match(r'how much (?:more |less )?([a-z]+)(?:,| in\b)', p.question)
            subject = ' of ' + noun.group(1) if noun else ''
            working += ' The result is {} {}{}.'.format(format_number(value), output_unit, subject)
        return value, working
    result = _read(body + query)
    if result is not None:
        return finish(result)
    # An introductory count can label an explicitly enumerated set of measured
    # objects. Remove it only when the solved graph has precisely that size.
    intro = re.match(r'[^.;!?]+[.;]\s*', body)
    if intro:
        ns = read_numbers(intro.group())
        if len(ns) == 1 and re.search(r'\b(?:different|colored)\b', intro.group(), re.I):
            state = _read(body[intro.end():] + ' How many are there in total?', True)
            if state and ns[0].value == len(state):
                result = _read(body[intro.end():] + query)
                if result is not None:
                    return finish(result)
    return None


def _category_remainder(p):
    """A stated whole minus a fully solved set of compared categories."""
    if not re.search(r'\brest\b', p.body):
        return None
    text = _normalise(p.text)
    ask = list(ASK.finditer(text))[-1]
    body, query = text[:ask.start()], text[ask.start():]
    rest = re.search(r'\b(?:the )?rest(?: of [^.;,]+?)? (?:are|were|is) ([a-z]+(?: [a-z]+){0,2})', body, re.I)
    if not rest:
        # "the rest picture books".
        rest = re.search(r'\bthe rest ([a-z]+(?: [a-z]+){0,2})', body, re.I)
    if not rest:
        return None
    rest_words = {_singular(w.lower()) for w in rest.group(1).split()}
    if not rest_words <= {_singular(w) for w in re.findall(r'[a-z]+', query.lower())}:
        return None
    # Whole must be a direct initial count, with the queried count noun.
    first = re.match(r'[^.;!?]+[.;]\s*', body)
    if not first:
        return None
    ns = read_numbers(first.group())
    if len(ns) != 1 or re.search(r'\b(?:more|less|times|twice|each|per)\b', first.group(), re.I):
        return None
    if not re.search(r'\b(?:has|have|had|contains?|holds?|there are|there were|bought|collected)\b', first.group(), re.I):
        return None
    unit = re.match(r'\s+([a-z]+)', first.group()[ns[0].end:])
    query_words = {_singular(w) for w in re.findall(r'[a-z]+', query.lower())}
    if not unit or _singular(unit.group(1)) not in query_words:
        return None
    remainder = body[first.end():].replace('non-', 'non')
    rest_clause = r'(?:,?\s*and\s+|[.;]\s*)?(?:if )?(?:the )?rest[^.;]*[.;]?'
    if any(read_numbers(m.group()) for m in re.finditer(rest_clause, remainder, re.I)):
        return None
    remainder = re.sub(rest_clause, '', remainder, flags=re.I)
    state = _read(remainder.rstrip(' ,') + '. How many are there in total?', True)
    if not state or len(state) < 2:
        return None
    result = ns[0].value - sum(state.values(), Fraction(0))
    return _answer(result, '{} minus the compared categories.'.format(format_number(ns[0].value)))


def _geometric(p):
    """A fixed multiplier at every step, queried as a last value or a sum."""
    text = _tokens(p)
    layers = re.search(r'\b(q\d+)[ -]layer\b', text)
    layer_ratio = re.search(r'\beach layer (?:having|has) (' + _FACTOR + r') as many [^.;]+ as the layer above it\b', text)
    if layers and layer_ratio and re.search(r'\btop layer is a single\b', text):
        if _ids(layers.group()+' '+layer_ratio.group()) != set(range(len(p.numbers))):
            return None
        n, k = _v(layers.group(1), p), _factor(layer_ratio.group(1), p)
        if n.denominator == 1 and 1 <= n <= 100 and k > 0:
            return sum((k**i for i in range(int(n))), Fraction(0)), 'Sum the layer sizes from the single top item.'
        return None
    growth = re.search(r'\b(?:each|every) (?:of the )?(?:following|subsequent|remaining)[^.;]*?\b(?:twice|double[sd]?|triple[sd]?|q\d+ times)\b', text)
    if not growth:
        growth = re.search(r'\bevery time\b[^.;]*?\b(twice|q\d+ times) as fast as the previous\b', text)
    if not growth:
        return None
    f = re.search(r'\b(twice|double[sd]?|triple[sd]?|q\d+ times)\b', growth.group())
    raw = f.group(1)
    k = Fraction(2 if raw.startswith('doubl') or raw == 'twice' else 3) if not raw.startswith('q') else _factor(raw, p)
    used = _ids(growth.group())
    for m in re.finditer(r'\bprevious (q\d+)\b', text):
        if _v(m.group(1), p) == 1:
            used.update(_ids(m.group()))
    if k <= 1:
        return None
    if re.search(r'\bhow many times faster\b', p.question):
        remaining = set(range(len(p.numbers))) - used
        if len(remaining) != 1:
            return None
        n = p.values[next(iter(remaining))]
        if n.denominator != 1 or not 1 <= n <= 100:
            return None
        return k**(int(n)-1), 'Apply the growth factor between consecutive items.'
    # Explicit final ordinal is a sequence length, not a separate amount.
    ordinal = re.search(r'\bafter (?:the )?(\d+)(?:st|nd|rd|th) (day|week|month)\b', text)
    if not ordinal:
        return None
    n = int(ordinal.group(1))
    if not 1 <= n <= 100 or not re.search(r'\b(?:total|spend|altogether|in all)\b', p.question):
        return None
    remaining = set(range(len(p.numbers))) - used
    if len(remaining) != 1:
        return None
    base = p.values[next(iter(remaining))]
    return base*sum((k**i for i in range(n)), Fraction(0)), 'Sum the geometrically increasing amounts.'


def _age_priced(p):
    """An expense proportional to current age, after an age comparison."""
    text = _tokens(p)
    m = re.search(r'\b(?:expense|bill|cost)[^.;]*?\b(?:equal to )?(q\d+) times (?:her|his|their) age(?: now)?\b', text)
    if not m or not re.search(r'\b(?:expense|bill|cost)\b', p.question):
        return None
    first_end = p.text.find('.')
    if first_end < 0 or _ids(text.split('.', 1)[0]) != _ids(m.group()):
        return None
    owners = _names(p.text[:first_end])
    if len(owners) != 1:
        return None
    body = p.text[first_end+1:len(p.body)]
    result = _read(body + ' How old is ' + owners[0].title() + ' now?')
    if result is None:
        return None
    k = _v(m.group(1), p)
    return _answer(k*result[0], result[1] + ' Multiply the current age by ' + format_number(k) + '.')


def _capacity_profit(p):
    """Lost output times profit per item times the requested time span."""
    text = _tokens(p)
    current = re.search(r'\b(?:produce|make) (q\d+) ([a-z]+) (?:a|per|each) day\b', text)
    cost = re.search(r'\bcosts? (q\d+) to (?:produce|make) each ([a-z]+)\b', text)
    markup = re.search(r'\bsell (?:them|it) for (' + _FACTOR + r') as much\b', text)
    demand = re.search(r'\bcould sell (q\d+) ([a-z]+) (?:a|per|each) day\b', text)
    if not all((current, cost, markup, demand)) or not re.search(r'\b(?:lose|loses|loss)\b', p.question):
        return None
    if len({_singular(current.group(2)), _singular(cost.group(2)), _singular(demand.group(2))}) != 1:
        return None
    if _ids(current.group()+cost.group()+markup.group()+demand.group()) != set(range(len(p.numbers))):
        return None
    duration = 7 if re.search(r'\b(?:a|per|each) week\b', p.question) else 1 if re.search(r'\b(?:a|per|each) day\b', p.question) else None
    if duration is None:
        return None
    result = (_v(demand.group(1), p)-_v(current.group(1), p))*_v(cost.group(1), p)*(_factor(markup.group(1), p)-1)*duration
    return _answer(result, 'Unmet daily demand times profit per item times the number of days.')


def _combined_period_rate(p):
    """Several regular days, one multiple-sized day, then a payment per unit."""
    text = _tokens(p)
    base = re.search(r'\b(q\d+) ([a-z]+) (?:a|per|each) day for the first (q\d+) days\b', text)
    extra = re.search(r'\b(' + _FACTOR + r') as many ([a-z]+) as every other day combined\b', text)
    rate = re.search(r'\b(q\d+) per ([a-z]+)\b', text)
    if not all((base, extra, rate)) or not re.search(r'\bhow much\b', p.question):
        return None
    noun = _singular(base.group(2))
    priced = _singular(rate.group(2))
    if _singular(extra.group(2)) != noun or priced not in (noun, noun[:-2] if noun.endswith('or') else noun):
        return None
    if _ids(' '.join((base.group(), extra.group(), rate.group()))) != set(range(len(p.numbers))):
        return None
    result = _v(base.group(1), p)*_v(base.group(3), p)*(1+_factor(extra.group(1), p))*_v(rate.group(1), p)
    owner_object = re.search(r"\b[a-z]+'s ([a-z]+)\b", p.body)
    subject = owner_object.group(1) if owner_object else _singular(base.group(2))
    return _answer(result, '{} income: {} dollars.'.format(subject.capitalize(), format_number(result)))


def _age_difference(p):
    """A future third age compared to the invariant difference of two ages."""
    text = _tokens(p)
    relation = re.search(r'\b(?:in|after) (q\d+) years,? their age difference will be (q\d+) years (less|more) than ([a-z]+)(?:\'s)? age\b', text)
    if not relation or not re.search(r'\bhow old\b', p.question):
        return None
    owner = relation.group(4)
    if not re.search(r'\b' + re.escape(owner) + r'\b', p.question):
        return None
    # Remove just the fully read comparison sentence; solve the two original
    # ages with the same exact equation reader as ordinary comparisons.
    original = p.text
    start = max(original.rfind('.', 0, p.numbers[int(relation.group(1)[1:])].start), 0)
    end = original.find('.', p.numbers[int(relation.group(2)[1:])].end)
    if end < 0:
        return None
    reduced = original[:start] + '. ' + original[end+1:len(p.body)]
    state = _read(_normalise(reduced) + ' How old are they in total?', True)
    if not state or len(state) != 2:
        return None
    a, b = state.values()
    sign = 1 if relation.group(3) == 'less' else -1
    result = abs(a-b) + sign*_v(relation.group(2), p)-_v(relation.group(1), p)
    return _answer(result, 'The age difference stays constant; undo the offset and the future time shift.')


def _labelled_chain(p):
    """Numbered members of an explicitly counted homogeneous group."""
    text = p.text
    intro = re.match(r'[^.;!?]+[.;]\s*', text)
    if not intro:
        return None
    ns = read_numbers(intro.group())
    if len(ns) != 1 or ns[0].value.denominator != 1 or not 2 <= ns[0].value <= 8:
        return None
    head = re.match(r'\s+([a-z]+)\b', intro.group()[ns[0].end:], re.I)
    if not head:
        return None
    noun = _singular(head.group(1).lower())
    body = text[intro.end():]
    labels = list(re.finditer(r'\b' + re.escape(noun) + r' (' + _NUMBER + r')\b', body, re.I))
    if not labels:
        return None
    identities = {read_numbers(m.group(1))[0].value for m in labels}
    if identities != set(Fraction(i) for i in range(1, int(ns[0].value)+1)):
        return None
    def label(m):
        i = int(read_numbers(m.group(1))[0].value)
        return 'Member' + chr(96+i)
    body = re.sub(r'\b' + re.escape(noun) + r' (' + _NUMBER + r')\b', label, body, flags=re.I)
    body = re.sub(r'\bfinished it\b', 'had', body, flags=re.I)
    # A measured total over all participants is explicit in a relay.
    if re.search(r'\brelay\b', intro.group(), re.I) and re.search(r'\bfinish (?:the )?relay\b', p.question):
        ask = list(ASK.finditer(body))[-1]
        body = body[:ask.start()] + ' How many seconds did they have in total?'
    return _read(_normalise(body))


def _allocated_stock(p):
    """Compared work allocations against a stock evenly shared by the workers."""
    if not re.search(r'\b(?:left|remain|remaining)\b', p.question) or not re.search(r'\b(?:evenly|equally)\b', p.body):
        return None
    body = p.text[:len(p.body)]
    for cut in re.finditer(r'(?<=[.;])\s+', body):
        prefix, tail = body[:cut.end()], body[cut.end():]
        ns = read_numbers(prefix)
        if not 2 <= len(ns) <= 3 or not re.search(r'\b(?:divide|divides|divided|share|shares|shared)\b', prefix, re.I):
            continue
        state = _read(_normalise(tail) + ' How many are there in total?', True)
        if not state or not all(n.value == len(state) for n in ns[1:]):
            continue
        if any(n.kind == 'money' or not re.search(r'\b(?:for|among|between|to|of)(?: (?:his|her|their|the|these|those))?\s*$', prefix[:n.start], re.I)
               or re.match(r'\s+(?:' + _UNIT + r'|dollars?|cents?)\b', prefix[n.end:], re.I) for n in ns[1:]):
            continue
        unit = re.match(r'\s+([a-z]+)', prefix[ns[0].end:])
        if not unit or _singular(unit.group(1)) not in {_singular(w) for w in re.findall(r'[a-z]+', p.question)}:
            continue
        result = ns[0].value-sum(state.values(), Fraction(0))
        return _answer(result, 'Subtract all completed allocations from the original stock.')
    return None


def _lost_measure(p):
    """Compared amounts of weight lost are static measures, not balances."""
    if not re.search(r'\b(?:pounds?|kilograms?|grams?|ounces?)\b.*\blose\b', p.question):
        return None
    if not re.search(r'\b(?:total|in all|altogether)\b', p.question):
        return None
    text = re.sub(r'\blost\b', 'had', p.text, flags=re.I)
    return _read(_normalise(text))


def _cohort_stock(p):
    """Two cohorts take compared per-person amounts from a common stock."""
    if not re.search(r'\b(?:left|remained|remaining|remain)\b', p.question):
        return None
    text = _tokens(p)
    whole = re.search(r'\b(?:there were|there are|had) (q\d+) ([a-z]+(?: [a-z]+)?) in\b', text)
    people = re.search(r'\b(q\d+) people (?:lined up|came|arrived)\b', text)
    comparison = re.search(r'\bfirst (q\d+) people each took (' + _FACTOR + r') as many ([a-z]+(?: [a-z]+)?) as each of the last (q\d+) people took\b', text)
    anchor = re.search(r'\blast (q\d+) people each took (q\d+) ([a-z]+(?: [a-z]+)?)[,.;]', text)
    if not all((whole, people, comparison, anchor)):
        return None
    if comparison.group(3) != whole.group(2) or anchor.group(3) != whole.group(2):
        return None
    a, b = _v(comparison.group(1), p), _v(comparison.group(4), p)
    if a+b != _v(people.group(1), p) or b != _v(anchor.group(1), p):
        return None
    if _ids(' '.join(m.group() for m in (whole, people, comparison, anchor))) != set(range(len(p.numbers))):
        return None
    taken = (a*_factor(comparison.group(2), p)+b)*_v(anchor.group(2), p)
    return _answer(_v(whole.group(1), p)-taken, 'Subtract both cohort allocations from the stock.')


def _individual_prices(p):
    """Compared inventories sold at separately stated per-item prices."""
    if not re.search(r'\bhow much\b', p.question):
        return None
    text = p.text[:len(p.body)]
    names = _names(text)
    namepat = '|'.join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    if not namepat:
        return None
    prices, sold_objects = {}, []
    pattern = (r'\b(' + namepat + r') will sell ([^.;$]+?) for (\$\s*' + _DIGIT + r') each\b')
    def consume(m):
        key = m.group(1).lower()
        if key in prices:
            prices[key] = None
        else:
            prices[key] = read_numbers(m.group(3))[0].value
        sold_objects.append(_singular(m.group(2).split()[-1].lower()))
        return ''
    reduced = re.sub(pattern, consume, text, flags=re.I)
    if len(prices) < 2 or any(v is None for v in prices.values()):
        return None
    explicit_objects = set(sold_objects) - {'it', 'them'}
    if len(explicit_objects) == 1:
        referent = next(iter(explicit_objects))
        sold_objects = [referent if noun in ('it', 'them') else noun for noun in sold_objects]
    units = set()
    for n in read_numbers(reduced):
        tail = re.match(r'\s+([a-z]+(?: [a-z]+){0,2})', reduced[n.end:], re.I)
        if tail and not re.match(r'(?:times|more|less|fewer)\b', tail.group(1), re.I):
            units.update(_singular(w.lower()) for w in tail.group(1).split())
    if not all(noun in units for noun in sold_objects):
        return None
    state = _read(_normalise(reduced) + ' How many are there in total?', True)
    if not state or set(state) != set(prices):
        return None
    result = sum((state[n]*prices[n] for n in state), Fraction(0))
    return _answer(result, 'Sum each inventory multiplied by its own unit price.')


def _timed_owners(p):
    """Compared per-minute rates followed by explicit individual durations."""
    if not re.search(r'\b(?:combined|total|altogether)\b', p.question):
        return None
    text = p.text[:len(p.body)]
    split = re.search(r'\bIf\b', text)
    if not split:
        return None
    rates, schedule = text[:split.start()], text[split.end():]
    names = [re.sub(r'^and ', '', n) for n in _names(rates)]
    namepat = '|'.join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    if not namepat:
        return None
    pattern = r'\b(' + namepat + r') (?:does|works|worked|runs|performs)(?: [a-z-]+){0,4}? for (' + _NUMBER + r') (minutes?|hours?)\b'
    durations = list(re.finditer(pattern, schedule, re.I))
    if len(durations) < 2 or len(read_numbers(schedule)) != len(durations):
        return None
    base = re.search(r'\b(' + _NUMBER + r') ([a-z-]+) in (' + _NUMBER + r') (minutes?|hours?)\b', rates, re.I)
    if not base:
        return None
    if any(_singular(base.group(2).lower()) not in {_singular(w.lower()) for w in re.findall(r'[a-z-]+', m.group().split(' for ')[0], re.I)} for m in durations):
        return None
    source_unit = _singular(base.group(4).lower())
    q, duration = read_numbers(base.group(1))[0].value, read_numbers(base.group(3))[0].value
    if duration <= 0:
        return None
    rates = rates[:base.start()] + str(q/duration) + ' ' + base.group(2) + rates[base.end():]
    rates = re.sub(r'\bper ' + source_unit + r'\b', '', rates, flags=re.I)
    rates = re.sub(r'\bcan (?:perform|do)\b', 'had', rates, flags=re.I)
    state = _read(_normalise(rates) + ' How many are there in total?', True)
    times = {}
    for m in durations:
        name, value = m.group(1).lower(), read_numbers(m.group(2))[0].value
        unit = _singular(m.group(3).lower())
        if name in times:
            return None
        times[name] = value*_UNITS[unit][1]/_UNITS[source_unit][1]
    if not state or set(times) != set(state):
        return None
    result = sum((state[n]*times[n] for n in state), Fraction(0))
    return _answer(result, 'Sum each rate multiplied by its individual duration.')


def _repeated_containers(p):
    """Compared container capacities, filled an explicit number of times."""
    repeat = re.search(r'\bafter (' + _NUMBER + r') trips each\b', p.question)
    if not repeat or not re.search(r'\b(?:pail|bucket|container|bottle|tank)s?\b', p.body):
        return None
    count = read_numbers(repeat.group(1))[0].value
    body = p.text[:len(p.body)]
    # The opening describes filling the vessels; measurements start at "if".
    begin = re.search(r'\bIf\b', body)
    if not begin or read_numbers(body[:begin.start()]):
        return None
    body = body[begin.end():]
    body = re.sub(r"\b([A-Z][a-z]+)'s (?:pail|bucket|container|bottle|tank) holds\b", r'\1 has', body)
    body = re.sub(r"\b([A-Z][a-z]+)'s holds\b", r'\1 has', body)
    body = re.sub(r"\b([A-Z][a-z]+)'s is\b", r'\1 has', body)
    body = re.sub(r"\b([A-Z][a-z]+)'s\b", r'\1', body)
    result = _read(_normalise(body) + ' How much do they have in total?')
    if result is None:
        return None
    return _answer(result[0]*count, result[1] + ' Multiply the combined capacity by the trip count.')


def _arithmetic_series(p):
    """An explicitly constant daily increment, summed for a stated duration."""
    text = _tokens(p)
    first = re.search(r'\bon the first day[^.;]*?\b(?:made|earned|got|collected) (q\d+)\b', text)
    increment = re.search(r'\bevery day after that[^.;]*?\b(q\d+) more than the previous day\b', text)
    duration = re.search(r'\bafter (q\d+) days\b', text)
    if not all((first, increment, duration)):
        return None
    if _ids(' '.join(m.group() for m in (first, increment, duration))) != set(range(len(p.numbers))):
        return None
    n, a, d = _v(duration.group(1), p), _v(first.group(1), p), _v(increment.group(1), p)
    if n.denominator != 1 or n < 1:
        return None
    return _answer(n*(2*a+(n-1)*d)/2, 'Sum the arithmetic sequence of daily amounts.')


def _geometric_threshold(p):
    """First training period whose geometrically growing capacity meets a goal."""
    if not re.search(r'\bhow many (?:total )?(?:days|weeks|months)\b', p.question):
        return None
    text = _tokens(p)
    growth = re.search(r'\beach (day|week|month)[^.;]*?\b(' + _FACTOR + r') as far as the \1 before\b', text)
    base = re.search(r'\b(q\d+) (miles?|kilometers?|meters?|yards?) during the first (?:day|week|month)\b', text)
    if not growth or not base:
        return None
    remaining = set(range(len(p.numbers))) - _ids(growth.group()+' '+base.group())
    if len(remaining) != 1:
        return None
    ni = next(iter(remaining))
    goal_tail = p.text[p.numbers[ni].end:].lower()
    unit = re.match(r'\s+([a-z]+)', goal_tail)
    if not unit or _singular(unit.group(1)) != _singular(base.group(2)):
        return None
    target, current, k = p.values[ni], _v(base.group(1), p), _factor(growth.group(2), p)
    if current <= 0 or k <= 1:
        return None
    n = 1
    while current < target and n < 1000:
        current *= k
        n += 1
    return (Fraction(n), 'Increase the capacity each period until it reaches the goal.') if current >= target else None


def _two_item_purchase(p):
    """Two item counts and a price ratio, with optional cents conversion."""
    if not re.search(r'\bhow much (?:money|does|did|will)\b', p.question):
        return None
    text = _tokens(p)
    counts = re.search(r'\b(?:needs|buys|bought) (q\d+) ([a-z]+(?: [a-z]+)?) and (q\d+) ([a-z]+(?: [a-z]+)?)[.;]', text)
    price = re.search(r'\b(?:a|an|each) ([a-z]+(?: [a-z]+)?) costs? (q\d+)( cents?| dollars?)? each\b', text)
    ratio = re.search(r'\b(?:a|an|each) ([a-z]+(?: [a-z]+)?) costs? (' + _FACTOR + r') as much as (?:the )?([a-z]+(?: [a-z]+)?)[,.;]', text)
    if not all((counts, price, ratio)):
        return None
    singular = lambda s: ' '.join(_singular(w) for w in s.split())
    a, b = singular(counts.group(2)), singular(counts.group(4))
    if singular(price.group(1)) != a or singular(ratio.group(1)) != b or singular(ratio.group(3)) != a:
        return None
    if _ids(' '.join(m.group() for m in (counts, price, ratio))) != set(range(len(p.numbers))):
        return None
    unitprice = _v(price.group(2), p) / (100 if (price.group(3) or '').strip().startswith('cent') else 1)
    result = (_v(counts.group(1), p)+_v(counts.group(3), p)*_factor(ratio.group(2), p))*unitprice
    return _answer(result, 'Multiply each item count by its price and add the two costs.')


def _calendar_growth(p):
    """A fixed monthly multiplier from a stated starting month to an end month."""
    months = 'january february march april may june july august september october november december'.split()
    text = _tokens(p)
    growth = re.search(r'\beach month[^.;]*?\b(' + _FACTOR + r') as much as (?:her|his|their) previous month', text)
    if not growth:
        return None
    used = _ids(growth.group())
    remaining = set(range(len(p.numbers)))-used
    start = [m for m in months if re.search(r'\bin ' + m + r'\b', p.body)]
    end = [m for m in months if re.search(r'\bin ' + m + r'\b', p.question)]
    if len(remaining) != 1 or len(start) != 1 or len(end) != 1:
        return None
    n = (months.index(end[0])-months.index(start[0])) % 12
    return _answer(p.values[next(iter(remaining))]*_factor(growth.group(1), p)**n,
                   'Apply the monthly multiplier for each month after the starting month.')


def _scaled_aggregate(p):
    """A requested multiple of a graph's sum or average."""
    text = p.text
    ask = list(ASK.finditer(text))[-1]
    query = text[ask.start():]
    m = re.search(r'\b(' + _NUMBER + r') times the (average|total|sum)\b', query, re.I)
    if not m or len(read_numbers(query)) != 1:
        return None
    k = read_numbers(m.group(1))[0].value
    query = query[:m.start()] + 'the ' + m.group(2) + query[m.end():]
    result = _read(_normalise(text[:ask.start()] + query))
    return _answer(k*result[0], result[1] + ' Multiply the requested aggregate.') if result else None


def _shared_rate_duration(p):
    """Compare production rates before applying one common duration."""
    query = p.question
    duration = re.search(r'\bin (' + _NUMBER + r') (minutes?|hours?)\b', query)
    if not duration or len(read_numbers(query)) != 1 or not re.search(r'\b(?:total|together|combined| and )\b', query):
        return None
    unit = _singular(duration.group(2))
    if not re.search(r'\b(?:a|per) ' + unit + r'\b', p.body):
        return None
    units = set()
    for n in read_numbers(p.text[:len(p.body)]):
        noun = re.match(r'\s+([a-z]+)', p.text[n.end:], re.I)
        if noun and noun.group(1).lower() not in ('more', 'less', 'fewer', 'times'):
            units.add(_singular(noun.group(1).lower()))
    if not units & {_singular(w) for w in re.findall(r'[a-z]+', query)}:
        return None
    body = p.text[:len(p.body)]
    body = re.sub(r'\b(?:(?:in )?a|per) ' + unit + r'\b', '', body, flags=re.I)
    body = re.sub(r'\bcan [a-z]+\b', 'had', body, flags=re.I)
    state = _read(_normalise(body) + ' How many are there in total?', True)
    if not state:
        return None
    count = read_numbers(duration.group(1))[0].value
    return _answer(sum(state.values(), Fraction(0))*count, 'Add the rates and multiply by the shared duration.')


def _ratio_budget(p):
    """Divide a known group by a choice ratio, then price both choices."""
    if not re.search(r'\b(?:budget|cost)\b', p.question):
        return None
    text = _tokens(p)
    total = re.search(r'\bhave (q\d+) ([a-z]+)[.;]', text)
    ratio = re.search(r'\b(' + _FACTOR + r') as many ([a-z]+) want ([a-z]+) as ([a-z]+)[.;]', text)
    if not total or not ratio or total.group(2) != ratio.group(2):
        return None
    prices = {}
    used = _ids(total.group()+' '+ratio.group())
    for label in (ratio.group(3), ratio.group(4)):
        match = re.search(r'\beach ' + re.escape(label) + r'(?: [a-z]+)? costs? (q\d+)\b', text)
        if not match:
            return None
        prices[label] = _v(match.group(1), p)
        used.update(_ids(match.group()))
    if used != set(range(len(p.numbers))):
        return None
    k = _factor(ratio.group(1), p)
    if k <= 0:
        return None
    base = _v(total.group(1), p)/(1+k)
    if base.denominator != 1 or (base*k).denominator != 1:
        return None
    result = base*(k*prices[ratio.group(3)]+prices[ratio.group(4)])
    return _answer(result, 'Split the group by the ratio and add the cost of each choice.')


def _material_choice(p):
    """Compare proceeds from using all of one material for either product."""
    if not re.search(r'\bhow much more money\b', p.question):
        return None
    text = _tokens(p)
    first = re.search(r'\b(?:a|an) ([a-z]+(?: [a-z]+)?) takes (q\d+) (' + _UNIT + r') of ([a-z]+) and sells for (q\d+)\b', text)
    second = re.search(r'\b(?:a|an) ([a-z]+(?: [a-z]+)?) takes (' + _FACTOR + r') as much ([a-z]+) and sells for (q\d+)\b', text)
    stock = re.search(r'\bhas (q\d+) (' + _UNIT + r') of ([a-z]+)\b', text)
    if not all((first, second, stock)):
        return None
    if first.group(4) != second.group(3) or first.group(4) != stock.group(3) or _singular(first.group(3)) != _singular(stock.group(2)):
        return None
    if _ids(' '.join(m.group() for m in (first, second, stock))) != set(range(len(p.numbers))):
        return None
    rate, k = _v(first.group(2), p), _factor(second.group(2), p)
    if rate <= 0 or k <= 0:
        return None
    a, b = _v(stock.group(1), p)/rate, _v(stock.group(1), p)/(rate*k)
    if a.denominator != 1 or b.denominator != 1:
        return None
    # The question must ask for the more material-intensive alternative.
    requested = re.search(r'\binto ([a-z]+) instead of ([a-z]+)\b', p.question)
    if not requested or _singular(requested.group(1)) != _singular(second.group(1).split()[0]) or _singular(requested.group(2)) != _singular(first.group(1).split()[0]):
        return None
    result = b*_v(second.group(4), p)-a*_v(first.group(5), p)
    return _answer(result, 'Find the number of products from the whole stock for each choice, then compare the proceeds.')


def _weighted_categories(p):
    """Known per-container outputs, one compared output, and matching counts."""
    text = _tokens(p)
    anchors = list(re.finditer(r'\b(?:a|an) ([a-z]+) of ([a-z]+(?: [a-z]+)?) can (?:create|make|produce) (q\d+) ([a-z]+)\b', text))
    relation = re.search(r'\b(?:a|an) ([a-z]+) of ([a-z]+(?: [a-z]+)?) can (?:create|make|produce) (' + _FACTOR + r') (?:the )?amount of ([a-z]+) compared to ([a-z]+(?: [a-z]+)?)[,.;]', text)
    if not anchors or not relation:
        return None
    unit = relation.group(1)
    output = relation.group(4)
    if any(m.group(1) != unit or m.group(4) != output for m in anchors):
        return None
    rates = {m.group(2): _v(m.group(3), p) for m in anchors}
    if relation.group(5) not in rates or relation.group(2) in rates:
        return None
    rates[relation.group(2)] = rates[relation.group(5)]*_factor(relation.group(3), p)
    used = _ids(' '.join(m.group() for m in anchors)+' '+relation.group())
    result = Fraction(0)
    for label, rate in rates.items():
        count = re.search(r'\b(q\d+) ' + re.escape(unit) + r'(?:s|es) of ' + re.escape(label) + r'\b', text)
        if not count:
            return None
        used.update(_ids(count.group()))
        result += _v(count.group(1), p)*rate
    if used != set(range(len(p.numbers))) or _singular(output) not in {_singular(w) for w in re.findall(r'[a-z]+', p.question)}:
        return None
    return _answer(result, 'Multiply each container count by its output and add all outputs.')


def solve(problem):
    if not re.search(r'\b(?:twice|thrice|double[sd]?|triple[sd]?|quadruple|times|more|less|fewer|older|younger|same number)\b', problem.body):
        return None
    if re.search(r'\btimes more than\b', problem.body):
        return None
    for rule in (_adapted_chain, _category_remainder, _geometric, _age_priced,
                 _capacity_profit, _combined_period_rate, _age_difference,
                 _labelled_chain, _allocated_stock, _lost_measure, _cohort_stock,
                 _individual_prices, _timed_owners, _repeated_containers,
                 _arithmetic_series, _geometric_threshold, _two_item_purchase,
                 _calendar_growth, _scaled_aggregate, _shared_rate_duration,
                 _ratio_budget, _material_choice, _weighted_categories):
        result = rule(problem)
        if result is not None:
            return result
    return None
