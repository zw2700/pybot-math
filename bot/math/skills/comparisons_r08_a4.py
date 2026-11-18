"""Comparison chains with explicit final operations.

Reuse the exact affine reader after resolving local ellipsis. Separate readers
compose a solved chain with sharing, a stock balance, a unit rate, or an age
event. Unexplained numeric tokens and ambiguous references cause abstention.
"""
import re
from fractions import Fraction

from ..numbers import read_numbers, format_number
from ..problem import ASK, Problem
from .comparisons_r01_a2 import _names
from .comparisons_r03_a4 import _singular, _words
from .comparisons_r04_a3 import _MULT, _cat, _linear, _mentions
from .comparisons_r05_a6 import (
    _read, _NUMBER, _RAW_FACTOR, _tokens, _ids, _v, _factor, _FACTOR,
)
from .comparisons_r06_a2 import _adapt

_AMOUNT = r'(?:[$£€]\s*)?' + _NUMBER


def _answer(value, working):
    return (value, working) if value >= 0 else None


def _parts(text):
    cues = list(ASK.finditer(text))
    return (text[:cues[-1].start()], text[cues[-1].start():]) if cues else (text, '')


def _normalize(text):
    # A sibling's age at a child's birth is their constant age difference.
    pattern = (r'\bWhen (?:he|she) was born (?:his|her) (?:elder |older |younger )?'
               r'(?:sister|brother) ([A-Z][a-z]+) was ('+_NUMBER+r') years? old')
    def birth(m):
        prior = re.split(r'[.;]',text[:m.start()].strip().rstrip('.;'))[-1]
        names = _names(prior)
        if len(names) != 1:
            return m.group()
        return m.group(1)+' is '+m.group(2)+' years older than '+names[0].title()
    text = re.sub(pattern,birth,text)
    text = _adapt(text)
    text = re.sub(r'(?<=\d)(?=(?:cm|mm|kg)\b)', ' ', text, flags=re.I)
    text = re.sub(r'\b((?:this|last|next) (?:month|year|week)),',r'\1',text,flags=re.I)
    # These predicates describe one counted amount per actor.
    text = re.sub(r'\b(?:throws?|threw|tosses|tossed|picks?|picked|rained|watched|biked|catches|caught|hides|hid)\b', 'had', text, flags=re.I)
    text = re.sub(r'\bfarther than\b', 'more than', text, flags=re.I)
    text = re.sub(r'\bpurchased\b', 'bought', text, flags=re.I)
    text = re.sub(r'\b(more|less|fewer) in (?:money|number) than\b', r'\1 than', text, flags=re.I)
    text = re.sub(r'\bBetween them\b,?\s*', 'Together, ', text, flags=re.I)
    # Preserve the aggregation cue when ASK splits the final question.
    text = re.sub(r'Together,\s*(how many [^?]+)\?', r'\1 in total?', text, flags=re.I)
    text = re.sub(r'\bI (bought|had|have)\b', r'Narrator \1', text)
    text = re.sub(r'\bneeds? (' + _AMOUNT + r') more to have (' + _RAW_FACTOR +
                  r') (?:the )?amount of money that\b',
                  r'has \1 fewer than \2 as much as', text, flags=re.I)
    text = re.sub(r'\bneeds? ('+_NUMBER+r') more ([a-z]+(?: [a-z]+)?) to have ('+_RAW_FACTOR+r') as many as\b',
                  r'has \1 fewer than \3 as many \2 as',text,flags=re.I)
    # A relative clause after a direct quantity retains the direct owner.
    text = re.sub(r'\b([A-Z][a-z]+) has (' + _AMOUNT + r'), which is\b',
                  r'\1 has \2. \1 has', text)
    text = re.sub(r'\b([A-Z][a-z]+) had ('+_AMOUNT+r') ([a-z]+) which is ('+_AMOUNT+r') (more|less|fewer) than what ([A-Z][a-z]+) had\b',
                  r'\1 has \2 \3. \1 has \4 \5 \3 than \6',text)
    text = re.sub(r'\b(' + _RAW_FACTOR + r') more ([a-z]+(?: [a-z]+){0,2}?) than\b',
                  r'\1 as many \2 as', text, flags=re.I)
    text = re.sub(r'\b(' + _RAW_FACTOR + r') more than\b',
                  r'\1 as much as', text, flags=re.I)
    # A repeated relation with no subject uses the subject of the first one.
    text = re.sub(r'\b([A-Z][a-z]+) (has|had) ([^.;]+?) and (' + _RAW_FACTOR + r') as much as\b',
                  r'\1 \2 \3. \1 \2 \4 as much as', text)
    # "That distance" has a literal previous actor as antecedent.
    names = _names(text)
    pattern = r'\b(' + _RAW_FACTOR + r') that distance\b'
    def distance(m):
        prior = text[:m.start()]
        boundary = max(prior.rfind('.'), prior.rfind(' and '))
        actors = _mentions(prior[:max(0, boundary)].lower(), names)
        return m.group(1) + ' as much as ' + actors[-1].title() if actors else m.group()
    text = re.sub(pattern, distance, text, flags=re.I)
    # Explicit anonymous age roles are entities, rather than possessors of one
    # named age. Capitalization just supplies labels to the existing reader.
    if re.search(r'\bas old as\b', text, re.I):
        for kin in ('mother', 'father', 'daughter', 'son'):
            text = re.sub(r'\b(?:a|the|her|his) ' + kin + r'\b', kin.title(), text, flags=re.I)
    return text


def _adapted(p):
    text = _normalize(p.text)
    body, query = _parts(text)
    instruction = re.search(r'[.?]\s*Use [A-Z] to represent [^?.]+[.]?\s*$',query)
    if instruction and not read_numbers(instruction.group()):
        query = query[:instruction.start()]+'?'
    if re.search(r'\bdid we (?:buy|collect|pick|find)\b', query, re.I):
        query = query.rstrip(' ?') + ' in total?'
    if re.search(r'\bcan they use\b', query, re.I):
        query = query.rstrip(' ?') + ' in total?'
    # A count in the query labels exactly the solved participants.
    label = re.search(r'\bthe (' + _NUMBER + r') (?:pick|collect|have|buy|bought|had)\b', query, re.I)
    if label:
        state = _read(body + ' How many are there in total?', True)
        if not state or read_numbers(label.group(1))[0].value != len(state):
            return None
        query = query[:label.start()] + 'they ' + query[label.end():]
    # An enumerated introduction is a label only when it lists all graph nodes.
    intro = re.match(r'[^.;!?]+:\s*([^.;!?]+)[.;]\s*', body)
    if intro and len(read_numbers(intro.group())) == 1:
        listed = set(_names(intro.group(1)))
        state = _read(body[intro.end():] + ' How many are there in total?', True)
        if state and listed == set(state) and read_numbers(intro.group())[0].value == len(state):
            body = body[intro.end():]
    # Placing named objects together on a scale explicitly asks their sum.
    scale = re.search(r'\bput (.+?) on the scale\b', query, re.I)
    if scale and re.search(r'\bscale\b', query, re.I):
        state = _read(body + ' How many are there in total?', True)
        asked = _mentions(scale.group(1).lower(), state or {})
        if state and len(set(asked)) >= 2 and not read_numbers(query):
            return sum((state[n] for n in set(asked)), Fraction(0)), 'Add the weights of the objects placed on the scale.'
        return None
    return _read(body + query) if body+query != p.text else None


def _sharing(p):
    if not re.search(r'\b(?:share[ds]?|split|divide[ds]?)\b.*\bequally\b', p.question):
        return None
    body, query = _parts(_normalize(p.text))
    state = _read(body + ' How many are there in total?', True)
    if not state:
        return None
    group = re.search(r'\b(?:among|between|into) (' + _NUMBER + r') (?:people|friends|groups|parts)\b', query, re.I)
    if group:
        count = read_numbers(group.group(1))[0].value
        if len(read_numbers(query)) != 1:
            return None
    elif re.search(r'\bbetween themselves\b', query, re.I) and not read_numbers(query):
        count = Fraction(len(state))
    else:
        return None
    if count <= 0:
        return None
    return sum(state.values(), Fraction(0))/count, 'Add the compared amounts and divide by the number of equal shares.'


def _age_at_birth(p):
    if not re.search(r'\bwhen (?:he|she|[a-z]+) was born\b', p.question):
        return None
    text = _normalize(p.text)
    body, query = _parts(text)
    event = re.match(r'\s*When ([A-Z][a-z]+) is (' + _NUMBER + r')\b', body)
    if not event:
        return None
    child, age = event.group(1).lower(), read_numbers(event.group(2))[0].value
    body = body[event.end():]
    body = child.title() + ' is ' + format_number(age) + ' years old. ' + body
    # The event supplies an age, rather than an absolute calendar date.
    state = _read(body + ' How old are they in total?', True)
    if not state or child not in state:
        return None
    # Use the core's family aliases to resolve a possessive requested relative.
    from .comparisons_r04_a3 import _prepare
    prepared, display = _prepare(Problem.read(body + query))
    target_query = _parts(prepared)[1].split('when')[0].lower()
    asked = _mentions(target_query, state)
    if len(set(asked)) != 1:
        return None
    return _answer(state[asked[0]]-state[child], 'Subtract the child\'s age from the relative\'s age at the stated event.')


def _period_chain(p):
    """Resolve relative months and repeated actors into period variables."""
    months = 'january february march april may june july august september october november december'.split()
    text = _normalize(p.text)
    body, query = _parts(text)
    dates = list(re.finditer(r'\b(?:'+'|'.join(months)+r')\b', body, re.I))
    # "Next month" has an explicit previously named month.
    next_month = re.search(r'\bthe next month\b', body, re.I)
    if next_month:
        previous = [m for m in dates if m.end() < next_month.start()]
        if not previous:
            return None
        month = months[(months.index(previous[-1].group().lower())+1) % 12]
        body = body[:next_month.start()]+'in '+month+body[next_month.end():]
    if not re.search(r'\b(?:month|year)\b', query, re.I) or len(dates) < 2:
        return None
    # Single actor, each sentence explicitly labels its period.
    names = set(_names(body)) - set(months) - {'in', 'however'}
    if len(names) != 1:
        return None
    owner = next(iter(names))
    sentences = []
    previous = None
    for clause in re.split(r'[.;]', body):
        periods = re.findall(r'\b(?:'+'|'.join(months)+r')\b', clause, re.I)
        if not periods:
            if read_numbers(clause) or re.search(_RAW_FACTOR, clause, re.I):
                return None
            continue
        target = periods[0].lower()
        clause = re.sub(r'\b(?:in|on) '+target+r'\b,?', '', clause, flags=re.I)
        clause = re.sub(r'\b(?:'+re.escape(owner)+r'|he|she)\b', target, clause, flags=re.I)
        clause = re.sub(r'\bhowever,?\s*', '', clause, flags=re.I)
        if previous and re.search(_RAW_FACTOR, clause, re.I) and not re.search(r'\bas\b.*\bas\b', clause, re.I):
            clause = clause.strip()+' as '+previous
        if previous and re.search(r'\b(?:less|more) than in\b', clause, re.I):
            clause = re.sub(r'\bthan in\b', 'than', clause, flags=re.I)
        if not re.search(r'\b'+target+r'\b', clause, re.I):
            return None
        sentences.append(clause.strip())
        previous = target
    return _read('. '.join(sentences)+'. How many are there in total?')


def _remaining_partition(p):
    """An unrelated known category is removed before dividing a ratio total."""
    text = _tokens(p)
    body, query = _parts(text)
    ratios = list(_MULT.finditer(body))
    if len(ratios) != 1 or ratios[0].group(2) != 'many':
        return None
    m = ratios[0]
    left, right = _cat(m.group(3)), _cat(body[m.end():])
    rest = re.search(r'\bthe rest(?: of [^.;]+?)? (?:are|is|were) ([a-z]+)\b', body)
    if not all((left, right, rest)):
        return None
    unit = _words(left) & _words(right)
    first = re.match(r'[^.;]+[.;]', body)
    if not first or len(_ids(first.group())) != 1:
        return None
    total_token = re.search(r'\bq\d+\b', first.group()).group()
    if not (unit & _words(first.group())):
        return None
    known = re.search(r'\b(q\d+) '+re.escape(rest.group(1))+r'\b', body)
    if not known or _ids(total_token+' '+known.group()+' '+m.group()) != set(range(len(p.numbers))):
        return None
    asked = [node for node in (left, right) if (_words(node)-unit) & _words(query)]
    if len(asked) != 1:
        return None
    k = _factor(m.group(1), p)
    if k <= 0:
        return None
    base = (_v(total_token,p)-_v(known.group(1),p))/(1+k)
    return _answer(base*(k if asked[0] == left else 1), 'Remove the known third category, then divide the remainder into the stated ratio.')


def _stock_balance(p):
    """Fully understood allocations are subtracted from a separate stock."""
    text = _normalize(p.text)
    body, query = _parts(text)
    # A condition on the question is part of the allocation description.
    conditional = re.split(r'\bif\b', query, maxsplit=1, flags=re.I)
    if len(conditional) == 2:
        query = conditional[0]
        body += '. '+conditional[1].rstrip(' ?')+'.'
    if not re.search(r'\b(?:left|remaining|put in|keep|kept|give away)\b', query, re.I):
        return None
    first = re.match(r'[^.;!?]+[.;]\s*', body)
    if not first or len(read_numbers(first.group())) != 1 or re.search(_RAW_FACTOR, first.group(), re.I):
        return None
    stock = read_numbers(first.group())[0]
    noun = re.match(r'\s+([a-z]+)', first.group()[stock.end:], re.I)
    if not noun or not (_words(noun.group(1)) & _words(query)):
        return None
    if not re.search(r'\b(?:has|had|baked|were|contains?|bought)\b', first.group(), re.I):
        return None
    remainder = body[first.end():]
    # Allocate quantities to the recipients, not to the giver.
    remainder = re.sub(r'\b(?:he|she) gave ('+_NUMBER+r') ([a-z]+) to ([A-Z][a-z]+)',
                       r'\3 has \1 \2', remainder, flags=re.I)
    remainder = re.sub(r',\s*('+_NUMBER+r') ([a-z]+) to ([A-Z][a-z]+)',
                       r'. \3 has \1 \2', remainder)
    remainder = re.sub(r'\b(?:he|she) gave ('+_RAW_FACTOR+r') as many ([a-z]+) as (?:he|she) gave ([A-Z][a-z]+) to ([A-Z][a-z]+)',
                       r'\4 has \1 as many \2 as \3', remainder, flags=re.I)
    remainder = re.sub(r',?\s*kept some [^.;\d]+?(?=[.;])', '', remainder, flags=re.I)
    remainder = re.sub(r'\b(?:removes?|removed)\b', 'has', remainder, flags=re.I)
    # A directly stated allocation can be independent of the comparison
    # component, e.g. a fixed gift to a third recipient.
    clauses = re.split(r'[.;]', remainder)
    related = set(_names(' '.join(c for c in clauses if re.search(_RAW_FACTOR, c, re.I)
                                or re.search(r'\b(?:more|less|fewer)\b', c, re.I))))
    extra, retained = {}, []
    for clause in clauses:
        direct = re.fullmatch(r'\s*([A-Z][a-z]+) has ('+_AMOUNT+r') ([a-z]+)\s*', clause)
        if direct and direct.group(1).lower() not in related:
            if direct.group(1).lower() in extra or _singular(direct.group(3)) != _singular(noun.group(1).lower()):
                return None
            extra[direct.group(1).lower()] = read_numbers(direct.group(2))[0].value
        else:
            retained.append(clause)
    state = _read('. '.join(retained)+' How many are there in total?', True)
    if not state:
        return None
    goal = re.search(r'\b(?:left with only|left with|have only) ('+_NUMBER+r')\b', query, re.I)
    if read_numbers(query) and (not goal or len(read_numbers(query)) != 1):
        return None
    desired = read_numbers(goal.group(1))[0].value if goal else Fraction(0)
    return _answer(stock.value-sum(state.values(), Fraction(0))-sum(extra.values(), Fraction(0))-desired,
                   'Subtract all the compared allocations and the requested final reserve from the starting stock.')


def _post_loss(p):
    """A named owner's explicit loss follows a static comparison graph."""
    text = _normalize(p.text)
    body, query = _parts(text)
    loss = re.search(r'\b([A-Z][a-z]+) (?:lost|released) ('+_NUMBER+r') ([a-z]+(?: [a-z]+)?)\b', body, re.I)
    if not loss or not re.search(r'\b(?:altogether|total|left|now|bring home)\b', query, re.I):
        return None
    owner = loss.group(1).lower()
    amount = read_numbers(loss.group(2))[0].value
    reduced = body[:loss.start()]+body[loss.end():]
    state = _read(reduced+' How many are there in total?', True)
    if not state or owner not in state or state[owner] < amount or read_numbers(query):
        return None
    state[owner] -= amount
    asked = set(_mentions(query.lower(), state))
    if re.search(r'\b(?:more|less|fewer|difference)\b',query,re.I):
        if len(asked) != 2:
            return None
        a,b = (state[n] for n in asked)
        return abs(a-b), 'Apply the explicit loss, then compare the two updated amounts.'
    if len(asked) == 1:
        return state[next(iter(asked))], 'Apply the comparison, then subtract the explicit loss.'
    if len(asked) > 1 or re.search(r'\b(?:altogether|total|together|bring home)\b', query, re.I):
        return sum((state[n] for n in (asked or state)), Fraction(0)), 'Apply the comparisons and loss, then add the requested owners.'
    return None


def _birth_year(p):
    if not re.search(r'^what year\b.*\bborn\b', p.question):
        return None
    text = _normalize(p.text)
    body, query = _parts(text)
    date = re.search(r'\bIn ('+_NUMBER+r'),', body)
    if not date:
        return None
    year = read_numbers(date.group(1))[0].value
    if year.denominator != 1 or not 1000 <= year <= 9999:
        return None
    names = _names(body)
    asked = set(_mentions(query.lower(), names))
    if len(asked) != 1 or read_numbers(query):
        return None
    owner = next(iter(asked))
    body = body[:date.start()]+body[date.end():]
    result = _read(body+' How old is '+owner+'?')
    return _answer(year-result[0], 'Subtract the age at the stated calendar year from that year.') if result else None


def _rate_after_chain(p):
    """A single explicit item conversion applied to a compared total count."""
    text = _normalize(p.text)
    body, query = _parts(text)
    rate = re.search(r'\beach ([a-z]+) (?:has|had|contains?|weighs?|costs?) ('+_AMOUNT+r') ([a-z]+)\b', body, re.I)
    recipe = re.search(r'\bneeds? ('+_NUMBER+r') ([a-z]+) to make ('+_NUMBER+r') ([a-z]+)\b', body, re.I)
    if rate:
        factor = read_numbers(rate.group(2))[0].value
        input_unit, output_unit = rate.group(1).lower(), rate.group(3).lower()
        start, end = rate.span()
    elif recipe:
        denominator = read_numbers(recipe.group(3))[0].value
        if denominator <= 0:
            return None
        factor = read_numbers(recipe.group(1))[0].value / denominator
        input_unit, output_unit = recipe.group(4).lower(), recipe.group(2).lower()
        start, end = recipe.span()
    else:
        return None
    other_words = _words(body[:start]+body[end:])
    input_matches = (_singular(input_unit) in other_words or
                     input_unit.endswith('f') and input_unit[:-1]+'ve' in other_words)
    if _singular(output_unit) not in _words(query) or not input_matches:
        return None
    # Remove only the rate's complete sentence. Every other quantity must be
    # understood by the affine reader, including any period labels.
    sentence_start = body.rfind('.', 0, start)+1
    sentence_end = body.find('.', end)
    if sentence_end < 0:
        sentence_end = len(body)
    sentence = body[sentence_start:sentence_end]
    if len(read_numbers(sentence)) != len(read_numbers(body[start:end])):
        return None
    reduced = body[:sentence_start]+body[sentence_end+1:]
    state = _read(reduced+' How many are there in total?', True)
    if not state:
        return None
    labels = read_numbers(query)
    if labels:
        label = re.search(r'\bin ('+_NUMBER+r') (?:months|days|weeks)\b', query, re.I)
        if not label or len(labels) != 1 or labels[0].value != len(state):
            return None
    return sum(state.values(), Fraction(0))*factor, 'Add the compared item counts, then apply the stated amount per item.'


def _paired_rate(p):
    text = _tokens(p)
    body, query = _parts(text)
    ratio = re.search(r'\b([a-z]+) can [a-z]+ ('+_FACTOR+r') as fast as ([a-z]+)\b', body)
    rate = re.search(r'\b([a-z]+) (?:wrote|made|produced|read|completed) (q\d+) ([a-z]+) in (q\d+) (hours?|minutes?)\b', body)
    duration = re.search(r'\bin (q\d+) (hours?|minutes?)\b', query)
    if not all((ratio,rate,duration)) or rate.group(1) != ratio.group(3):
        return None
    if not re.search(r'\b(?:together|total|combined)\b', query):
        return None
    if _singular(rate.group(3)) not in _words(query):
        return None
    used = _ids(ratio.group()+' '+rate.group()+' '+duration.group())
    label = re.search(r'\bthe (q\d+) (?:write|make|produce|read|complete)\b', query)
    if label and _v(label.group(1),p) == 2:
        used.update(_ids(label.group()))
    if used != set(range(len(p.numbers))):
        return None
    unit_scale = {'hour': Fraction(60), 'minute': Fraction(1)}
    base_time = _v(rate.group(4),p)*unit_scale[_singular(rate.group(5))]
    time = _v(duration.group(1),p)*unit_scale[_singular(duration.group(2))]
    if base_time <= 0:
        return None
    return _v(rate.group(2),p)/base_time*(1+_factor(ratio.group(2),p))*time, 'Add the two production rates and multiply by the shared duration.'


def _scaled_basket(p):
    text = _tokens(p)
    body, query = _parts(text)
    factor = re.search(r'\b('+_FACTOR+r') as much as (?:what )?([a-z]+) spent\b', query)
    if not factor or not re.search(r'\b(?:budget|spend|pay)\b', query):
        return None
    if re.search(r'\b(?:each|per|every|change|discount|less|more)\b', body):
        return None
    quantities = [n for n in p.numbers if n.start < len(p.body)]
    if len(quantities) < 2 or any(n.kind != 'money' for n in quantities):
        return None
    if _ids(factor.group()) | _ids(body) != set(range(len(p.numbers))):
        return None
    owner = factor.group(2)
    purchase = re.search(r'\b'+re.escape(owner)+r' (?:buys|bought|purchased)\b', body)
    if not purchase or any(n.start < purchase.start() for n in quantities):
        return None
    # All prices must be costs of this owner's explicitly described basket.
    if not re.search(r'\bcosts?\b', body[purchase.end():]):
        return None
    return sum((n.value for n in quantities),Fraction(0))*_factor(factor.group(1),p), 'Add the listed prices, then apply the requested spending multiplier.'


def _matching_shortfall(p):
    if not re.search(r'\bneed\b.*\badd\b', p.question):
        return None
    body, query = _parts(_normalize(p.text))
    state = _read(body+' How many are there in total?', True)
    if not state or read_numbers(query):
        return None
    mentions = _mentions(query.lower(),state)
    if len(set(mentions)) == 2:
        source, target = mentions[0], mentions[-1]
    elif len(set(mentions)) == 1 and re.search(r'\b(?:she|he)\b',query,re.I):
        anchors = list(re.finditer(r'\b([A-Z][a-z]+) (?:currently )?has ('+_AMOUNT+r')\b',body))
        if not anchors:
            return None
        source, target = anchors[-1].group(1).lower(), mentions[0]
    else:
        return None
    if source not in state or target not in state or source == target:
        return None
    return _answer(state[target]-state[source], 'Subtract the current collection from the target collection.')


def _owner_categories(p):
    if re.search(r'\btogether have\b.*\b(?:more|less|fewer)\b', p.body):
        return None  # A joint amount cannot be assigned to one owner.
    """An exact graph whose variables are (owner, object) pairs.

    Independent direct counts are retained as anchored variables, so an actor
    can own different amounts of several objects without merging those amounts.
    """
    body, query = _parts(_tokens(p))
    names = _names(p.text)
    if re.search(r'\b(?:each|per|every|lost|gave|old|older|younger|percent)\b',body):
        return None
    mult = r'\b('+_FACTOR+r') as many (.+?) as\s+'
    add = r'\b(q\d+) (?!times\b)(?:([a-z]+(?: [a-z]+){0,4}?) )?(more|less|fewer)(?: (?!than\b)([a-z]+(?: [a-z]+){0,5}?))? than\s+'
    relations = []
    for m in re.finditer(mult,body):
        relations.append((m,True))
    for m in re.finditer(add,body):
        if not any(a.start() <= m.start() < a.end() for a,_ in relations):
            relations.append((m,False))
    if len(relations) < 2:
        return None
    equations, nodes, used = [], set(), set()
    prior_subject = None
    def category(text):
        return _cat(re.split(r'\b(?:into|through|on|in|at|from)\b',text)[0])
    for m,is_mult in sorted(relations,key=lambda item:item[0].start()):
        start = max(body.rfind('.',0,m.start()),body.rfind(';',0,m.start()),body.rfind(' but ',0,m.start()))+1
        before = body[start:m.start()]
        # A coordinator followed by a new named subject changes the owner;
        # a bare second multiplier keeps the preceding comparison's owner.
        segments = re.split(r',?\s+and\s+',before)
        local = segments[-1]
        owners = _mentions(local,names)
        left = owners[-1] if owners else prior_subject
        rights = _mentions(body[m.end():].split('.',1)[0],names)
        obj = category(m.group(2) if is_mult else (m.group(4) or m.group(2) or ''))
        if not left or not rights or not obj or left == rights[0]:
            return None
        a,b = (left,obj),(rights[0],obj)
        k = _factor(m.group(1),p) if is_mult else Fraction(1)
        d = Fraction(0) if is_mult else _v(m.group(1),p)*(-1 if m.group(3) in ('less','fewer') else 1)
        equations.append(({a:Fraction(1),b:-k},d)); nodes.update((a,b));used.update(_ids(m.group()))
        prior_subject = left
    categories = {obj for _,obj in nodes}
    for i,n in enumerate(p.numbers):
        if i in used:
            continue
        token = 'q'+str(i)
        hit = re.search(r'\b'+token+r'\b',body)
        if not hit or re.search(r'\b'+token+r'\b',query):
            return None
        start = max(body.rfind('.',0,hit.start()),body.rfind(';',0,hit.start()))+1
        prefix = body[start:hit.start()]
        owners = _mentions(prefix,names)
        if not owners or not re.search(r'\b(?:has|had|have|bought|picked|tosses|throws|owns|collected)\b',prefix):
            return None
        raw_object = re.split(r'\band\b|[.;,]',body[hit.end():])[0]
        obj = category(raw_object)
        if not obj:
            return None
        matches = [c for c in categories if _words(c) == _words(obj)]
        obj = matches[0] if len(matches) == 1 else obj
        node = (owners[-1],obj)
        nodes.add(node);equations.append(({node:Fraction(1)},n.value));used.add(i)
    state = _linear(equations,nodes)
    asked = set(_mentions(query,names))
    if not state or len(asked) != 1:
        return None
    owner = next(iter(asked))
    queried_objects = [c for c in categories if _words(c) <= _words(query)]
    if len(queried_objects) == 1:
        key = (owner,queried_objects[0])
        return (state[key], 'Solve the comparison for the requested object.') if key in state else None
    if not re.search(r'\b(?:total|together|objects|items|all together)\b',query):
        return None
    return sum((v for (actor,cat),v in state.items() if actor == owner),Fraction(0)), 'Solve the separate object comparisons and add the requested owner\'s amounts.'


def _ratio_of_remainder(p):
    body, query = _parts(_tokens(p))
    if not re.search(r'\b(?:remaining|remainder)\b',body):
        return None
    ratios = list(_MULT.finditer(body))
    if len(ratios) != 1 or ratios[0].group(2) != 'many':
        return None
    ratio = ratios[0]
    left, right = _cat(ratio.group(3)), _cat(body[ratio.end():])
    if not left or not right:
        return None
    prefix = body[:ratio.start()]
    quantities = sorted(_ids(prefix)-_ids(ratio.group()))
    if len(quantities) != 2 or _ids(body+query) != _ids(ratio.group()) | set(quantities):
        return None
    # A whole followed by an explicitly identified subset.
    first = re.search(r'\b(?:there were|there are|had|has) (q\d+) ([a-z]+)',prefix)
    subset = re.search(r'\b(q\d+) of them were ([a-z]+)',prefix)
    if not first or not subset or first.start() >= subset.start():
        return None
    asked = [node for node in (left,right) if _words(node) & _words(query)]
    if len(asked) != 1:
        return None
    k = _factor(ratio.group(1),p)
    if k <= 0:
        return None
    base = (_v(first.group(1),p)-_v(subset.group(1),p))/(1+k)
    return _answer(base*(k if asked[0] == left else 1),'Remove the known subset, then divide the remaining total according to the comparison.')


def _dated_gifts(p):
    text = _normalize(p.text)
    body, query = _parts(text)
    days = r'(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)'
    if len(re.findall(r'\b'+days+r'\b',body,re.I)) < 2:
        return None
    changed = re.sub(r'\bgave (?:him|her|them)\b','had',body,flags=re.I)
    if changed == body:
        return None
    # The dates, not the sender, distinguish these received amounts.
    return _read(changed+query)


def _age_reach(p):
    text = _normalize(p.text)
    body, query = _parts(text)
    m = re.search(r'^how many years will (.+?) (?:age be|be|turn) ('+_NUMBER+r')\s*\?',query,re.I)
    if not m or len(read_numbers(query)) != 1:
        return None
    state = _read(body+' How old are they in total?',True)
    asked = _mentions(m.group(1).lower(),state or {})
    if not state or len(set(asked)) != 1:
        return None
    return _answer(read_numbers(m.group(2))[0].value-state[asked[0]],'Subtract the current age from the requested future age.')


def _group_remainder(p):
    text = _normalize(p.text)
    body, query = _parts(text)
    first = re.match(r'[^.;]+[.;]\s*',body)
    if not first or len(read_numbers(first.group())) != 1 or not re.search(r'\btotal\b',first.group(),re.I):
        return None
    group = set(_names(first.group()))
    if len(group) < 3:
        return None
    state = _read(body[first.end():]+' How many are there in total?',True)
    requested = set(_mentions(query.lower(),group))
    if not state or len(requested) != 1 or group-set(state) != requested or read_numbers(query):
        return None
    return _answer(read_numbers(first.group())[0].value-sum(state.values(),Fraction(0)),
                   'Subtract the solved group members from their stated combined total.')


def _compared_group(p):
    """Equal-sized ordinary members and one member compared to one or all."""
    text = _tokens(p)
    body, query = _parts(text)
    # A group of other owners, each with the same known amount.
    collective = re.search(r'\bother (q\d+) [a-z]+ have (q\d+) ([a-z]+)(?: of [a-z]+)? each\b',body)
    individual = re.search(r'\b(q\d+) other members\b[^.;]*?\brun (q\d+) ([a-z]+)\b',body)
    base = collective or individual
    if not base:
        return None
    ratios = list(re.finditer(r'\b('+_FACTOR+r') as (?:many|much)(?: [a-z]+){0,4}? (?:as|than)\b',body))
    if len(ratios) != 1:
        return None
    ratio = ratios[0]
    count, amount = _v(base.group(1),p),_v(base.group(2),p)
    if count <= 0 or count.denominator != 1:
        return None
    used = _ids(base.group()+' '+ratio.group())
    group_noun = re.search(r'other q\d+ ([a-z]+) have',body).group(1) if collective else 'members'
    # Repeated group sizes and the requested combined group size are labels.
    for i in set(range(len(p.numbers)))-used:
        token = 'q'+str(i)
        if re.search(r'\b'+token+r' (?:other )?'+re.escape(group_noun)+r'\b',text):
            expected = count+1 if token in query else count
            if p.values[i] != expected:
                return None
            used.add(i)
    if used != set(range(len(p.numbers))):
        return None
    k = _factor(ratio.group(1),p)
    if collective and re.search(r'\bcombined\b',body[:base.start()]):
        answer = count*amount*(1+k)
    elif individual and re.search(r'\bas any member\b',body):
        answer = (count+k)*amount
    else:
        return None
    return _answer(answer,'Add the equal amounts in the ordinary group and the explicitly compared member.')


def _scaled_square_perimeter(p):
    text = _tokens(p)
    if not re.search(r'\bsquare\b.*\bperimeter\b',text) or not re.search(r'\bone side of the square\b',p.question):
        return None
    ratio = re.search(r'\bperimeter is ('+_FACTOR+r') as large as a rectangular\b',text)
    length = re.search(r'\blength of (q\d+) ([a-z]+)\b',text)
    width = re.search(r'\bwidth of (q\d+) ([a-z]+)\b',text)
    if not all((ratio,length,width)) or length.group(2) != width.group(2):
        return None
    used = _ids(ratio.group()+' '+length.group()+' '+width.group())
    one_side = re.search(r'\b(q\d+) side\b',text)
    if one_side and _v(one_side.group(1),p) == 1:
        used.update(_ids(one_side.group()))
    if used != set(range(len(p.numbers))):
        return None
    return (_v(length.group(1),p)+_v(width.group(1),p))*2*_factor(ratio.group(1),p)/4,'Find the rectangular perimeter, apply the ratio, and divide the square perimeter by four.'


def _number_equation(p):
    text = _tokens(p)
    m = re.search(r'\bnumber, when multiplied by (q\d+), is (q\d+) (less|more) than ('+_FACTOR+r') (q\d+)\b',text)
    if not m or _ids(m.group()) != set(range(len(p.numbers))) or not re.search(r'\bwhat is the number\b',p.question):
        return None
    divisor = _v(m.group(1),p)
    if divisor <= 0:
        return None
    value = _factor(m.group(4),p)*_v(m.group(5),p)+_v(m.group(2),p)*(-1 if m.group(3) == 'less' else 1)
    return _answer(value/divisor,'Evaluate the stated numeric expression and undo multiplication of the unknown number.')


def _spent_chain(p):
    if not re.search(r'\bspent\b',p.body) or not re.search(r'\b(?:total|altogether|combined)\b',p.question):
        return None
    if re.search(r'\b(?:left|remaining|gave|lost|earned|received|discount|each|per)\b',p.body):
        return None
    body, query = _parts(_normalize(p.text))
    body = re.sub(r'\bspent\b','had',body,flags=re.I)
    body = re.sub(r'(?<=\d) If\b','. If',body)
    return _read(body+query)


def _labelled_group(p):
    body, query = _parts(_normalize(p.text))
    label = re.search(r'\b('+_NUMBER+r') (?:friends|people|children)\b',body,re.I)
    if not label:
        return None
    names = set(_names(body))
    if len(names) < 2 or read_numbers(label.group(1))[0].value != len(names):
        return None
    body = body[:label.start()]+'people'+body[label.end():]
    return _read(body+query)


def _inverse_expenses(p):
    text = _tokens(p)
    m = re.search(r'\bcost (q\d+) which was (q\d+) (more|less) than ('+_FACTOR+r') the amount\b',text)
    if not m or _ids(m.group()) != set(range(len(p.numbers))):
        return None
    if not re.search(r'\b(?:spent|spend) altogether\b',p.question):
        return None
    k = _factor(m.group(4),p)
    if k <= 0:
        return None
    known, offset = _v(m.group(1),p), _v(m.group(2),p)*(-1 if m.group(3) == 'less' else 1)
    base = (known-offset)/k
    return _answer(base+known,'Undo the additive adjustment and multiplier, then add the two expenses.') if base >= 0 else None


def _age_event_prefix(p):
    # A preceding "When he is ..." scopes the age question that follows it.
    text = _normalize(p.text)
    body, query = _parts(text)
    event = re.search(r'\bWhen (he|she|[A-Z][a-z]+) is ('+_NUMBER+r') years? old,?\s*$',body)
    if not event or not query.lower().startswith('how old') or read_numbers(query):
        return None
    prior = body[:event.start()]
    names = _names(prior)
    if event.group(1).lower() in ('he','she'):
        original_names = _names(p.text)
        if len(original_names) != 1:
            return None
        owner = original_names[0]
    else:
        owner = event.group(1).lower()
    state = _read(prior+' How old are they in total?',True)
    if not state or owner not in state:
        return None
    from .comparisons_r04_a3 import _prepare
    prepared, _ = _prepare(Problem.read(prior+query))
    asked = _mentions(_parts(prepared)[1].lower(),state)
    if len(set(asked)) != 1:
        return None
    elapsed = read_numbers(event.group(2))[0].value-state[owner]
    return _answer(state[asked[0]]+elapsed,'Advance both ages to the date described before the question.')


def _overlap(p):
    text = _normalize(p.text)
    body, query = _parts(text)
    shared = re.search(r'[^.;]*?\b(?:They|they) share ('+_NUMBER+r') ([a-z]+)[.;]?',body)
    if not shared or not re.search(r'\bcombined (?:list|group|total)\b',p.question,re.I):
        return None
    if not _words(shared.group(2)) & _words(body[:shared.start()]):
        return None
    state = _read(body[:shared.start()]+body[shared.end():]+' How many are there in total?',True)
    if not state or len(state) != 2 or read_numbers(query):
        return None
    overlap = read_numbers(shared.group(1))[0].value
    if overlap > min(state.values()):
        return None
    return sum(state.values(),Fraction(0))-overlap,'Add the two counts and subtract the shared members once.'


def _bundle_ratio(p):
    body, query = _parts(_tokens(p))
    ratio = re.search(r'\b('+_FACTOR+r') (?:the )?number of (.+?) and (.+?) ([a-z]+) (?:bought|has|had)\b',body)
    if not ratio or not re.search(r'\btotal\b',query):
        return None
    names = _names(p.text)
    start = body.rfind('.',0,ratio.start())+1
    lefts = _mentions(body[start:ratio.start()],names)
    if not lefts or ratio.group(4) not in names:
        return None
    left,right = lefts[-1],ratio.group(4)
    remaining = set(range(len(p.numbers)))-_ids(ratio.group())
    if len(remaining) != 2 or read_numbers(p.question):
        return None
    cats = (_words(ratio.group(2)),_words(ratio.group(3)))
    owner = None; amounts = []
    for i in sorted(remaining):
        token = 'q'+str(i); hit = re.search(r'\b'+token+r'\b',body)
        if not hit:
            return None
        local_start = body.rfind('.',0,hit.start())+1
        actors = _mentions(body[local_start:hit.start()],names)
        noun = re.split(r'\band\b|[.;,]',body[hit.end():])[0]
        if not actors or not cats[len(amounts)] <= _words(noun):
            return None
        if owner is not None and owner != actors[-1]:
            return None
        owner = actors[-1];amounts.append(p.values[i])
    requested = set(_mentions(query,names))
    k = _factor(ratio.group(1),p)
    if k <= 0 or len(requested) != 1 or owner not in (left,right):
        return None
    target = next(iter(requested))
    if target == owner:
        return None
    if (owner,target) == (left,right):
        answer = sum(amounts,Fraction(0))/k
    elif (owner,target) == (right,left):
        answer = sum(amounts,Fraction(0))*k
    else:
        return None
    return answer,'Add the explicitly compared bundle and apply the ratio in the requested direction.'


def _pooled_comparison(p):
    """A comparison to an explicitly pooled collection with several kinds."""
    raw = _normalize(p.text)
    body, query = _parts(raw)
    first = re.match(r'[^.;]+[.;]\s*',body)
    if not first:
        return None
    quantities = read_numbers(first.group())
    if len(quantities) < 2 or not re.search(r'\band\b',first.group()):
        return None
    if re.search(r'\b(?:each|per|every|times|more|less|fewer)\b',first.group(),re.I):
        return None
    if not re.search(r'\bas many (?:items|objects|animals|things|pieces) as\b',body,re.I):
        return None
    owners = _names(first.group())
    if len(owners) != 1 or any(n.kind == 'percent' for n in quantities):
        return None
    rest = body[first.end():]
    reference = re.search(r'\bas many ([a-z]+) as\b',rest,re.I)
    if not reference or owners[0] not in rest.lower():
        return None
    replacement = owners[0].title()+' has '+format_number(sum((n.value for n in quantities),Fraction(0)))+' '+reference.group(1)+'. '
    # Possessive possessions retain the owning actor as the amount's label.
    rest = re.sub(r"\b([A-Z][a-z]+)'s [a-z]+",r'\1',rest)
    return _read(replacement+rest+query)


def _repeated_compared_items(p):
    text = _tokens(p)
    body, query = _parts(text)
    if not re.search(r'\b(?:total|combined|trip|spend solving)\b',query):
        return None
    ratio = re.search(r'\b('+_FACTOR+r') (?:that long|as long)\b',body)
    if not ratio:
        return None
    # One ordinary event, then N events each taking K times its duration.
    first = re.search(r'\b(?:took|takes) (q\d+) (minutes?|hours?|weeks?)\b',body)
    others = re.search(r'\b(?:did|does) (q\d+) [a-z]+ that each (?:took|takes)\b',body)
    if first and others and _ids(first.group()+' '+others.group()+' '+ratio.group()) == set(range(len(p.numbers))):
        return _v(first.group(1),p)*(1+_v(others.group(1),p)*_factor(ratio.group(1),p)),'Add the first duration and the repeated longer durations.'
    # N equal short items and one last item K times as long.
    size = re.search(r'\b(q\d+) of them are (q\d+) (minutes?|hours?) each\b',body)
    total = re.search(r'\b(?:buys|bought|has) (q\d+) ([a-z]+)\b',body)
    last = re.search(r'\bthe last (q\d+) is\b',body)
    if not all((size,total,last)):
        return None
    used = _ids(size.group()+' '+total.group()+' '+last.group()+' '+ratio.group())
    if used != set(range(len(p.numbers))) or _v(last.group(1),p) != 1 or _v(total.group(1),p) != _v(size.group(1),p)+1:
        return None
    return _v(size.group(2),p)*(_v(size.group(1),p)+_factor(ratio.group(1),p)),'Add the equal short items and the explicitly longer last item.'


def _extra_profit(p):
    text = _tokens(p)
    if not re.search(r'\bmore profit\b',p.question):
        return None
    cost = re.search(r'\bcost[^.;]*? (q\d+) more than\b',text)
    sale = re.search(r'\bsells for ('+_FACTOR+r') as much as\b',text)
    base = re.search(r'\bother [a-z]+, which sell at (q\d+) each\b',text)
    if not all((cost,sale,base)) or _ids(cost.group()+' '+sale.group()+' '+base.group()) != set(range(len(p.numbers))):
        return None
    return _answer((_factor(sale.group(1),p)-1)*_v(base.group(1),p)-_v(cost.group(1),p),
                   'Subtract the extra construction cost from the increase in selling price.')


def _aggregate_episode(p):
    text = _tokens(p)
    body, query = _parts(text)
    last = re.search(r'\b('+_FACTOR+r') the number (?:she|he|they) (?:got|found|collected) from the first (q\d+) days\b',body)
    if not last or not re.search(r'\bhow many\b',query):
        return None
    prior = sorted(_ids(body[:last.start()])-_ids(last.group()))
    if len(prior) < 2 or _v(last.group(2),p) != len(prior):
        return None
    if set(prior) | _ids(last.group()) != set(range(len(p.numbers))):
        return None
    if not re.search(r'\b(?:found|collected|got)\b',body[:last.start()]):
        return None
    return sum((p.values[i] for i in prior),Fraction(0))*(1+_factor(last.group(1),p)), 'Add the early episodes, apply the multiplier to their combined amount, and add all episodes.'


def _frequency_product(p):
    """An explicit item count, recipients, and a repeated daily/weekly event."""
    text = _tokens(p)
    body, query = _parts(text)
    frequency = re.search(r'\b(twice|thrice) a (day|week)\b',body)
    if not frequency or re.search(r'\b(?:more|less|fewer|as many|as much|lost|left|remaining)\b',body):
        return None
    k = _factor(frequency.group(1),p)
    # A measured message/package sent to N recipients at each occurrence.
    package = re.search(r'\b(q\d+)[ -]([a-z]+) [a-z]+ to (q\d+) (?:different )?([a-z]+)\b',body)
    if package and frequency.group(2) == 'week' and re.search(r'\ba year\b',query):
        if _ids(package.group()) != set(range(len(p.numbers))) or _singular(package.group(2)) not in _words(query):
            return None
        return _v(package.group(1),p)*_v(package.group(3),p)*k*52,'Multiply the amount per recipient, recipients, weekly frequency, and weeks in a year.'
    # N animals/items, each consuming a measured amount at every daily event.
    count = re.search(r'\b(?:has|owns|keeps) (q\d+) ([a-z]+)\b',body)
    portion = re.search(r'\beach (q\d+) (?:eats|uses|needs|consumes) (q\d+) ([a-z]+)\b',body)
    duration = re.search(r'\bfor (q\d+) days\b',query)
    if not all((count,portion,duration)) or frequency.group(2) != 'day' or _v(portion.group(1),p) != 1:
        return None
    if _ids(count.group()+' '+portion.group()+' '+duration.group()) != set(range(len(p.numbers))):
        return None
    if _singular(portion.group(3)) not in _words(query):
        return None
    return _v(count.group(1),p)*_v(portion.group(2),p)*_v(duration.group(1),p)*k,'Multiply the number of consumers, amount per feeding, feedings per day, and days.'


def _compared_event_rates(p):
    text = _tokens(p)
    body, query = _parts(text)
    base = re.search(r'\b([a-z]+) (q\d+) times a (minute|hour|day)\b',body)
    ratio = re.search(r'\b('+_FACTOR+r') as much as (?:her|him)\b',body)
    duration = re.search(r'\bafter (q\d+) (minutes|hours|days)\b',body+query)
    if not all((base,ratio,duration)) or _singular(duration.group(2)) != base.group(3):
        return None
    if _ids(base.group()+' '+ratio.group()+' '+duration.group()) != set(range(len(p.numbers))):
        return None
    if not re.search(r'\bthey\b',query):
        return None
    return _v(base.group(2),p)*(1+_factor(ratio.group(1),p))*_v(duration.group(1),p),'Add the compared event rates and multiply by the elapsed time.'


def _compared_production(p):
    text = _tokens(p)
    body, query = _parts(text)
    count = re.search(r'\b(?:buys|bought|has) (q\d+) ([a-z]+)\b',body)
    growth = re.search(r'\bhas ('+_FACTOR+r') as many ([a-z]+) as (?:he|she) started with\b',body)
    rate = re.search(r'\beach ([a-z]+) (?:lays|makes|produces) (q\d+) ([a-z]+) a day\b',body)
    if not all((count,growth,rate)):
        return None
    if _singular(count.group(2)) != _singular(growth.group(2)) or _singular(rate.group(1)) != _singular(count.group(2)):
        return None
    if _singular(rate.group(3)) not in _words(query) or not re.search(r'\b(?:every|each) week\b',query):
        return None
    used = _ids(count.group()+' '+growth.group()+' '+rate.group())
    date = re.search(r'\bafter (q\d+) years\b',body)
    if date:
        used.update(_ids(date.group()))
    if used != set(range(len(p.numbers))):
        return None
    return _v(count.group(1),p)*_factor(growth.group(1),p)*_v(rate.group(2),p)*7,'Apply the population multiplier, then multiply by daily output and seven days.'


def _two_season_rates(p):
    text = _tokens(p)
    ratio = re.search(r'\b('+_FACTOR+r') as many [a-z]+(?: [a-z]+)? as before\b',text)
    rate = re.search(r'\bcharged (q\d+) [a-z]+(?: [a-z]+)? for the first (q\d+) months\b',text)
    if not ratio or not rate or not re.search(r'\bonce a month\b',text) or not re.search(r'\b(?:entire|whole) year\b',p.question):
        return None
    if _ids(ratio.group()+' '+rate.group()) != set(range(len(p.numbers))):
        return None
    n = _v(rate.group(2),p)
    if not 0 < n < 12:
        return None
    return _v(rate.group(1),p)*(n+(12-n)*_factor(ratio.group(1),p)),'Add the monthly payments before and after the stated price change.'


def _scaled_affine_ages(p):
    text = _tokens(p)
    m = re.search(r'\b(q\d+) (less|more) than (q\d+) times ([a-z]+)\'s age is (q\d+) (less|more) than (q\d+) times ([a-z]+)\'s age\b',text)
    anchor = re.search(r'\b([a-z]+) is currently (q\d+) years old\b',text)
    # Query offsets are tokenized in the full text, not in p.question.
    shift = re.search(r'\b(q\d+) years from now\b',_parts(text)[1])
    if not all((m,anchor,shift)) or anchor.group(1) != m.group(8):
        return None
    if _ids(m.group()+' '+anchor.group()+' '+shift.group()) != set(range(len(p.numbers))):
        return None
    if not re.search(r'\b'+re.escape(m.group(4))+r'\b',p.question):
        return None
    a,b = _v(m.group(3),p),_v(m.group(7),p)
    if a <= 0:
        return None
    d1 = _v(m.group(1),p)*(-1 if m.group(2) == 'less' else 1)
    d2 = _v(m.group(5),p)*(-1 if m.group(6) == 'less' else 1)
    return _answer((b*_v(anchor.group(2),p)+d2-d1)/a+_v(shift.group(1),p),'Solve the scaled age equality, then add the requested future years.')


def solve(problem):
    if not re.search(r'\b(?:twice|thrice|double|triple|times|more|less|fewer|older|younger)\b', problem.text, re.I):
        return None
    if any(n.kind == 'percent' for n in problem.numbers):
        return None
    # A fractional "times more" denotes an increment in the fraction skill;
    # it must not be simplified to the bare multiplier by a syntax adapter.
    if any(n.value < 1 and re.match(r'\s+times more\b',problem.text[n.end:],re.I)
           for n in problem.numbers):
        return None
    for reader in (_sharing, _age_at_birth, _birth_year, _period_chain, _remaining_partition,
                   _rate_after_chain, _paired_rate, _scaled_basket, _matching_shortfall,
                   _owner_categories, _ratio_of_remainder, _dated_gifts, _age_reach,
                   _group_remainder, _compared_group, _scaled_square_perimeter, _number_equation,
                   _spent_chain, _labelled_group, _inverse_expenses, _age_event_prefix,
                   _overlap, _bundle_ratio, _pooled_comparison, _repeated_compared_items,
                   _extra_profit, _aggregate_episode, _frequency_product, _compared_event_rates,
                   _compared_production, _two_season_rates, _scaled_affine_ages,
                   _stock_balance, _post_loss, _adapted):
        result = reader(problem)
        if result is not None:
            return result
    return None
