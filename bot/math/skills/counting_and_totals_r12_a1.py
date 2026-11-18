"""Short counting narratives with explicit inventories and group relations.

Each reader checks the requested unit and accounts for every quantity. Labels
are read from the story, rather than from a vocabulary of people or objects.
"""
import re
from fractions import Fraction

from ..numbers import format_number
from ._counting_common import answer, total, fmt, tokenize, products
from .rates_and_unit_rates_r01_a4 import _convert
from .counting_and_totals_r00_a1 import _singular
from .counting_and_totals_r08_a2 import _unit as _base_unit
from ._counting_groups import container_relations


def has(pattern, text):
    return re.search(pattern, text) is not None


def _unit(tail):
    tail = re.sub(r'^\s*(?:free|total)\s+', ' ', tail)
    short = re.match(r'\s*(kg|g|cm|mm|m|lb|oz)\b',tail)
    if short:
        return {'kg':'kilogram','g':'gram','cm':'centimeter','mm':'millimeter',
                'm':'meter','lb':'pound','oz':'ounce'}[short.group(1)]
    tail = re.split(r'\b(?:how|you|consists|gave|brought|read|if|through|currently|stashed|save)\b',tail)[0]
    return _base_unit(tail)


def _asked(p):
    m = re.match(r'how (?:many|much)\s+(?:(?:more|additional|extra)\s+)?(.*)', p.question)
    return _unit(m.group(1)) if m else ''


def _tails(p):
    return [p.text.lower()[n.end:p.numbers[i+1].start if i+1 < len(p.numbers)
                                else len(p.text)] for i,n in enumerate(p.numbers)]


def _postposed_stock(p):
    """A whole inventory with explicit passive departures and returns."""
    ns = p.numbers
    if not 2 <= len(ns) <= 5 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\b(?:now|left|remaining)\b', p.question):
        return None
    ts = _tails(p)
    unit = _unit(ts[0])
    if not unit or _asked(p) != unit or any(_unit(t) != unit for t in ts):
        return None
    if not re.search(r'\b(?:there (?:are|were)|has|had|holds?|contains?)\s*$', p.body[:ns[0].start]):
        return None
    if has(r'\b(?:each|every|per|more|less|than|half|times|twice)\b', p.body):
        return None
    signs = [1]
    for t in ts[1:]:
        m = re.match(r'\s+[a-z]+\s+(?:are|were|have been|had been)\s+'
                     r'(taken out|removed|returned|brought back|added)\b', t)
        if not m:
            return None
        signs.append(-1 if m.group(1) in ('taken out', 'removed') else 1)
    value = total(n.value*s for n, s in zip(ns, signs))
    work = format_number(ns[0].value)
    for n, s in zip(ns[1:], signs[1:]):
        work += (' + ' if s > 0 else ' - ') + format_number(n.value)
    return answer(value, work)


def _short_stock_ledger(p):
    """One owner's stock, with explicit actions and temporal noun ellipsis."""
    ns = p.numbers
    if not 2 <= len(ns) <= 6 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\b(?:left|remaining|more|now)\b',p.question):
        return None
    if has(r'\b(?:each|every|per|than|fewer|less|half|twice|times|average|ratio|percent|some|rest)\b',p.body):
        return None
    text = p.text.lower()
    start = re.search(r'\b([a-z]+) (has|had|bought|made|collected|harvested)\s*$',text[:ns[0].start])
    if not start:
        return None
    owner = start.group(1)
    ts = _tails(p)
    unit = _unit(ts[0])
    if not unit or unit != _asked(p):
        return None
    queried_owner = re.search(r'\b(?:does|did|will|can) ([a-z]+)\b',p.question)
    if queried_owner and queried_owner.group(1) not in (owner,'he','she','they','it'):
        return None
    additions = r'bought|buys?|found|received|collected|added'
    removals = r'sold|sells?|lost|loses?|used|uses?|ate|eats?|removed|gave away|gives? away'
    events = r'(?:'+additions+'|'+removals+r')'
    previous = None
    signs = [1]
    for i,n in enumerate(ns[1:],1):
        u = _unit(ts[i])
        if u != unit:
            if not re.match(r'\s*(?:[.,;]|(?:last|this|next|on|during|in)\b)',ts[i]):
                return None
        before = text[ns[i-1].end:n.start]
        clause = re.split(r'[.!?;](?:\s|$)',before)[-1]
        event = re.search(r'\b([a-z]+) ('+events+r')(?: another| an additional)?\s*$',clause)
        if event:
            if event.group(1) not in (owner,'he','she','they','it'):
                return None
            previous = event.group(2)
        elif not (previous and has(r'\band\s*$',before) and not has(r'[.!?;](?:\s|$)',before)):
            return None
        signs.append(-1 if re.fullmatch(removals,previous) else 1)
    if -1 not in signs:
        return None
    terms = [n.value*s for n,s in zip(ns,signs)]
    work = format_number(ns[0].value)
    for n,s in zip(ns[1:],signs[1:]):
        work += (' - ' if s < 0 else ' + ')+format_number(n.value)
    return answer(total(terms),work)


def _time_budget(p):
    """Stated trip duration, or a day, less a list of activities."""
    ns = p.numbers
    if not 2 <= len(ns) <= 6 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\b(?:left|free time|spare time|sideline)\b', p.question):
        return None
    ts = _tails(p)
    units = [_unit(t) for t in ts]
    if not units or units[0] not in ('hour', 'minute') or len(set(units)) != 1:
        return None
    if has(r'\b(?:each|every|times|twice|half|than|more|average)\b', p.body):
        return None
    if has(r'\b(?:per|a) day\b', p.body) and has(r'\b(?:free|spare) time\b', p.question):
        budget = Fraction(24 if units[0] == 'hour' else 1440)
        used = ns
    else:
        if not has(r'\b(?:ride|trip|journey|shift|break|game)\b', ts[0]):
            return None
        budget = ns[0].value
        used = ns[1:]
    # Recognize spending time, without treating an arbitrary list as a budget.
    if not has(r'\b(?:spends?|played)\b', p.body[:used[0].start]):
        return None
    if _asked(p) not in (units[0], 'time') and not has(r'^how (?:long|much free time)\b', p.question):
        return None
    return answer(budget-total(n.value for n in used),
                  '{} - ({})'.format(format_number(budget), fmt(n.value for n in used)))


def _group_complement(p):
    """A uniform population split into a named category and its complement."""
    ns = p.numbers
    if len(ns) != 3 or any(n.start >= len(p.body) for n in ns):
        return None
    text = p.text.lower()
    ts = _tails(p)
    units = [_unit(t) for t in ts]
    if not has(r'\b(?:of which|of (?:whom|these))\b', p.body):
        return None
    if has(r'\b(?:more|less|than|half|twice|percent|average|except)\b', text):
        return None
    rel = container_relations(p, _unit, units)
    if rel is None:
        return None
    edges, refs = rel
    if refs or len(edges) != 1:
        return None
    ri, ci = next(iter(edges.items()))
    oi = next(i for i in range(3) if i not in (ri, ci))
    category = re.match(r'\s+of (?:which|whom|these) (?:are|were) ([a-z]+)', ts[oi])
    if not category or _asked(p) == _singular(category.group(1)):
        return None
    if not has(r'^how many (?:of (?:them|these) )?are [a-z]+\?', p.question):
        return None
    a, b, c = ns[ci].value, ns[ri].value, ns[oi].value
    return answer(a*b-c, '{} x {} - {}'.format(*map(format_number, (a,b,c))))


def _dozen_contents(p):
    """Dozens of containers, with an explicit content per container."""
    ns = p.numbers
    if len(ns) != 2 or any(n.start >= len(p.body) for n in ns):
        return None
    ts = _tails(p)
    dozen = re.match(r'\s+dozen\s+([a-z]+)\b', ts[0])
    if not dozen or not re.search(r'\beach '+re.escape(_singular(dozen.group(1)))+
                                  r' (?:contains?|holds?|has)\s*$', ts[0]):
        return None
    if _asked(p) != _unit(ts[1]) or has(r'\b(?:left|more|less|than|lost|sold)\b',p.text.lower()):
        return None
    a,b = p.values
    return answer(a*12*b, '{} x 12 x {}'.format(format_number(a),format_number(b)))


def _restated_group(p):
    """An explicitly repeated group count in the question is a reference."""
    ns = p.numbers
    if len(ns) != 3 or ns[2].start < len(p.body) or ns[0].value != ns[2].value:
        return None
    ts = _tails(p)
    u0, u1, u2 = (_unit(t) for t in ts)
    if not u0 or u0 != u2 or u0 == u1 or _asked(p) != u1:
        return None
    token = tokenize(p)
    if not has(r'\beach '+re.escape(u0)+r' (?:consists of|contains?|requires?|needs?|has) Q1\b', token):
        return None
    if has(r'\b(?:more|less|than|left|half|twice|extra|remaining)\b',token):
        return None
    return answer(ns[0].value*ns[1].value, '{} x {}'.format(*map(format_number,p.values[:2])))


def _parts_mixture(p):
    """A recipe lists parts; one ingredient's amount fixes the scale."""
    ns = p.numbers
    if not 3 <= len(ns) <= 7 or any(n.start >= len(p.body) for n in ns):
        return None
    ts = _tails(p)
    labels = []
    for t in ts[:-1]:
        m = re.match(r'\s+parts? (?:of )?([a-z]+(?: [a-z]+)*?)(?=,| and\b|[.;])',t)
        if not m:
            return None
        labels.append(m.group(1))
    unit = _unit(ts[-1])
    known = re.match(r'\s+[a-z]+ of ([a-z]+(?: [a-z]+)*?)(?=[.,;])',ts[-1])
    if not known or labels.count(known.group(1)) != 1 or _asked(p) != unit:
        return None
    if has(r'\b(?:more|less|half|twice|left|percent|each|per)\b', p.body):
        return None
    i = labels.index(known.group(1))
    if ns[i].value <= 0:
        return None
    parts = total(n.value for n in ns[:-1])
    return answer(ns[-1].value*parts/ns[i].value,
                  '{} x ({}) / {}'.format(format_number(ns[-1].value),fmt(n.value for n in ns[:-1]),format_number(ns[i].value)))


def _recipient_list(p):
    """A stated count of givers followed by that many explicit gifts."""
    ns = p.numbers
    if not 3 <= len(ns) <= 8 or ns[0].start >= len(p.body) or any(n.start < len(p.body) for n in ns[1:]):
        return None
    if ns[0].value != len(ns)-1 or not has(r'\b(?:people|friends|relatives|members)\b',p.body[ns[0].end:]):
        return None
    ts = _tails(p)
    requested = _asked(p)
    if not requested or any(_unit(t) != requested for t in ts[1:]):
        return None
    text = p.text.lower()
    for i,n in enumerate(ns[1:],1):
        if not re.search(r'\b[a-z]+ (?:gave|gives?|brought|brings?|donated)\s*$',text[ns[i-1].end:n.start]):
            return None
    if has(r'\b(?:each|more|less|than|left|half|twice|not)\b',p.question):
        return None
    return answer(total(n.value for n in ns[1:]),fmt(n.value for n in ns[1:]))


def _attendance_list(p):
    """Disjoint seated/standing counts at one event, queried as attendance."""
    ns = p.numbers
    if not 2 <= len(ns) <= 6 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'^how many (?:people |persons )?(?:attended|were present|were there)\b',p.question):
        return None
    if has(r'\b(?:each|every|per|more|less|than|half|left|total|including)\b',p.body):
        return None
    ts = _tails(p)
    for i,t in enumerate(ts):
        # A shared postposed predicate may apply to an adjacent coordinated list.
        if re.match(r'\s+[a-z]+\s+and\s*$',t) and i+1 < len(ns):
            continue
        if not re.match(r'\s+[a-z]+ (?:are|were) (?:seated|standing|present)\b',t):
            return None
    return answer(total(p.values),fmt(p.values))


def _collection_duration(p):
    """Combine acquisitions, then apply time per one collected item."""
    ns = p.numbers
    if not 4 <= len(ns) <= 7 or any(n.start >= len(p.body) for n in ns):
        return None
    ts = _tails(p)
    time = _unit(ts[-2])
    unit = _unit(ts[0])
    if time not in ('day','hour','minute') or ns[-1].value != 1 or _unit(ts[-1]) != unit:
        return None
    if _asked(p) != time or not has(r'\b(?:collection|all|entire|whole)\b',p.question):
        return None
    if not re.match(r'\s+[a-z]+ to [a-z ]+\s*$',ts[-2]):
        return None
    if has(r'\b(?:each|every|per|half|twice|than|fewer|less|lost|sold|away)\b',p.body):
        return None
    text = p.text.lower()
    if not re.search(r'\b(?:has|had|started (?:off |out )?with)\s*$',text[:ns[0].start]):
        return None
    for i,n in enumerate(ns[1:-2],1):
        before = text[ns[i-1].end:n.start]
        if not re.search(r'\b(?:gave (?:him|her|them)|received|bought|collected|found)\s*$',before):
            return None
        if _unit(ts[i]) != unit and not re.match(r'\s+more\s+(?:at|from|for)\b',ts[i]):
            return None
    return answer(total(n.value for n in ns[:-2])*ns[-2].value,
                  '({}) x {}'.format(fmt(n.value for n in ns[:-2]),format_number(ns[-2].value)))


def _reward_schedule(p):
    """Every N completed items earns a reward, with a production schedule."""
    ns = p.numbers
    if len(ns) != 3 or any(n.start >= len(p.body) for n in ns):
        return None
    ts = _tails(p)
    text = p.text.lower()
    if not re.search(r'\bfor every\s*$',text[:ns[0].start]):
        return None
    unit = _unit(ts[0])
    if not unit or _unit(ts[1]) != unit or ns[0].value <= 0:
        return None
    rate = re.match(r'\s+[a-z]+ (?:a|per|each) (day|week|month)\b',ts[1])
    if not rate or _unit(ts[2]) != rate.group(1):
        return None
    rewards = re.findall(r'\b(?:a|an) (?:free )?([a-z]+) (?:at|for|from)\b',ts[0])
    if _asked(p) not in [_singular(word) for word in rewards]:
        return None
    if has(r'\b(?:than|more|less|half|twice|left|remaining)\b',text):
        return None
    value = ns[1].value*ns[2].value/ns[0].value
    return answer(Fraction(value.numerator//value.denominator),
                  '{} x {} / {}'.format(*map(format_number,(ns[1].value,ns[2].value,ns[0].value))))


_DAYS = ('monday','tuesday','wednesday','thursday','friday','saturday','sunday')
_DAY_ALIASES = {day:day for day in _DAYS}
_DAY_ALIASES.update({day[:3]:day for day in _DAYS})


def _weekly_named_days(p):
    """A fixed amount on an explicit list of weekly days; find completion time."""
    ns = p.numbers
    if len(ns) != 2 or any(n.start >= len(p.body) for n in ns):
        return None
    ts = _tails(p)
    first_unit = re.match(r'\s+([a-z]+)\b',ts[0])
    if not first_unit or _singular(first_unit.group(1)) != _unit(ts[1]) or _asked(p) != 'week':
        return None
    schedule = re.match(r'\s+[a-z]+\s+([a-z, ]+)[.;]',ts[0])
    if not schedule or has(r'\b(?:except|more|less|than|half|twice|per|total|together|combined)\b',p.body):
        return None
    labels = [x for x in re.split(r'\s*(?:,|\band\b)\s*',schedule.group(1).strip()) if x]
    if not all(x in _DAY_ALIASES for x in labels):
        return None
    if len(labels) < 2 or len(set(_DAY_ALIASES[x] for x in labels)) != len(labels):
        return None
    if ns[0].value <= 0:
        return None
    value = ns[1].value/(ns[0].value*len(labels))
    return answer(value,'{} / ({} x {})'.format(format_number(ns[1].value),format_number(ns[0].value),len(labels)))


def _excluded_categories(p):
    """Two inventories each have a labelled subset excluded from the total."""
    ns = p.numbers
    if len(ns) != 4 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\bneither\b.+\bnor\b',p.question):
        return None
    token = tokenize(p)
    first = re.search(r'\b(?:has|have|had) Q0 ([a-z]+) and Q1 ((?:pairs? of )?[a-z]+)',token)
    if not first:
        return None
    labels = [_unit(re.sub(r'^pairs? of ','',first.group(i))) for i in (1,2)]
    if len(set(labels)) != 2:
        return None
    exclusions = []
    for i in (2,3):
        m = re.search(r'Q'+str(i)+r" of (?:[a-z]+'s|the|his|her|their) ([a-z]+) are ([a-z]+)",token)
        if not m or _unit(m.group(1)) != labels[i-2]:
            return None
        exclusions.append(m.group(2))
    if not all(has(r'\b'+re.escape(x)+r'\b',p.question) for x in exclusions):
        return None
    if not all(has(r'\b'+re.escape(label)+r'(?:s|es)?\b',p.question) for label in labels):
        return None
    if has(r'\b(?:each|per|more|less|than|half|twice)\b',p.body):
        return None
    a,b,c,d = p.values
    if c > a or d > b:
        return None
    return answer(a+b-c-d,'({} - {}) + ({} - {})'.format(*map(format_number,(a,c,b,d))))


def _label(text):
    return ' '.join(_singular(w) for w in re.findall(r'[a-z]+',text)
                    if w not in ('the','a','an','his','her','their'))


def _labelled_ratio(p):
    """An explicit A:B ratio and a measured amount of one labelled category."""
    ns = p.numbers
    if len(ns) != 3 or any(n.start >= len(p.body) for n in ns):
        return None
    token = tokenize(p)
    ratio = re.search(r'\b([a-z]+(?: [a-z]+)?) and ([a-z]+(?: [a-z]+)?) '
                      r'in the ratio(?: of)? Q0\s*:\s*Q1\b',token)
    if not ratio:
        ratio = re.search(r'\bratio of ([a-z]+(?: [a-z]+)?) to ([a-z]+(?: [a-z]+)?) '
                          r'(?:in [a-z ]+ )?is Q0\s*:\s*Q1\b',token)
    if not ratio:
        ratio = re.search(r'\b(?:the )?([a-z]+) outnumber (?:the )?([a-z]+) Q0 to Q1\b',token)
    if not ratio or min(p.values) <= 0:
        return None
    labels = [_label(x) for x in ratio.groups()]
    known = re.match(r'\s+([a-z]+(?: [a-z]+)?)(?= on\b|[.;,])',p.text.lower()[ns[2].end:])
    query = re.match(r'how many ([a-z]+(?: [a-z]+)?) (?:did|does|do|are|were|will)\b',p.question)
    if not known or not query:
        return None
    have, want = _label(known.group(1)),_label(query.group(1))
    if want not in labels or have == want:
        return None
    if has(r'\b(?:more|less|left|remaining|gave|lost|sold|half|twice)\b',token):
        return None
    a = ns[labels.index(want)].value
    if have in labels:
        b = ns[labels.index(have)].value
    elif has(r'\bthere are Q2\b|\btotal of Q2\b',token):
        b = ns[0].value+ns[1].value
    else:
        return None
    return answer(ns[2].value*a/b,'{} x {} / {}'.format(*map(format_number,(ns[2].value,a,b))))


def _companions_remainder(p):
    """A fixed total task, less the stated work by each of N companions."""
    ns = p.numbers
    if len(ns) != 3 or any(n.start >= len(p.body) for n in ns):
        return None
    token = tokenize(p)
    start = re.search(r'\b([a-z]+) and Q0 ([a-z]+) (?:are|have) to ([a-z]+) Q1\b',token)
    if not start:
        return None
    owner,groups,action = start.groups()
    if not has(r'\b(?:his|her|their) '+re.escape(groups)+r' each '+re.escape(action)+r' Q2\b',token):
        return None
    ts = _tails(p)
    if not _unit(ts[1]) or _unit(ts[1]) != _unit(ts[2]) or _asked(p) != _unit(ts[1]):
        return None
    if not has(r'\b'+re.escape(owner)+r'\b',p.question) or not has(r'\b'+re.escape(action)+r'\b',p.question):
        return None
    if has(r'\b(?:more|less|than|half|twice|per)\b',p.body):
        return None
    count,goal,rate = p.values
    return answer(goal-count*rate,'{} - {} x {}'.format(*map(format_number,(goal,count,rate))))


def _passive_contents(p):
    """Singular containers filled with contents, linked to counted containers."""
    ns = p.numbers
    if not 2 <= len(ns) <= 5 or has(r'\b(?:more|less|than|left|half|twice|except|lost|sold)\b',p.text.lower()):
        return None
    token = tokenize(p)
    ts = _tails(p)
    units = [_unit(t) for t in ts]
    if not all(units):
        return None
    edges = {}
    for m in re.finditer(r'\b(?:a|an|each|every) ([a-z]+) is filled with Q(\d+)\b',token):
        group,i = _singular(m.group(1)),int(m.group(2))
        counts = [j for j,u in enumerate(units) if j != i and u == group]
        if len(counts) != 1 or i in edges:
            return None
        edges[i] = (counts[0],Fraction(1))
    terms = products(p.values,edges)
    if not edges or terms is None or len(terms) != 1 or units[terms[0][0]] != _asked(p):
        return None
    return answer(terms[0][1],terms[0][2])


def _measured_stock(p):
    """Measured stock and explicit sales, with recipients outside the stock."""
    ns = p.numbers
    if not 2 <= len(ns) <= 6 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\b(?:not sold|unsold|left|remaining)\b',p.question):
        return None
    ts = _tails(p)
    units = [_unit(t) for t in ts]
    aliases = {'kg':'kilogram','g':'gram','m':'meter','lb':'pound'}
    units = [aliases.get(u,u) for u in units]
    if units[0] not in ('kilogram','gram','liter','pound','ounce','meter') or len(set(units)) != 1 or _asked(p) != units[0]:
        return None
    token = tokenize(p)
    if not has(r'\b(?:harvested|bought|had|has|collected) Q0\b',token):
        return None
    if has(r'\b(?:each|every|per|half|twice|than|more|less)\b',token):
        return None
    previous = False
    for i,n in enumerate(ns[1:],1):
        prefix = p.text.lower()[ns[i-1].end:n.start]
        prefix = re.sub(r'\b(?:mr|mrs|ms|dr)\.', '', prefix)
        clause = re.split(r'[.!?;]\s|\band\b',prefix)[-1]
        if has(r'\b(?:sold|used|lost|removed)\s*$',clause):
            previous = True
        elif not (previous and has(r'\band\s*$',prefix) and not has(r'[.!?;]\s',prefix)):
            return None
    return answer(ns[0].value-total(n.value for n in ns[1:]),
                  '{} - ({})'.format(format_number(ns[0].value),fmt(n.value for n in ns[1:])))


def _task_duration_difference(p):
    """Compare two explicit durations to finish the same task."""
    ns = p.numbers
    if len(ns) != 2 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\b(?:faster|slower|longer|shorter)\b',p.question):
        return None
    ts = _tails(p)
    units = [_unit(t) for t in ts]
    requested = _asked(p)
    if requested not in ('second','minute','hour') or not all(u in ('second','minute','hour') for u in units):
        return None
    if not all(has(r'\bto finish\b',t) for t in ts):
        return None
    if has(r'\b(?:per|each|every|half|twice|more|less|times)\b',p.body):
        return None
    a,b = (_convert(n.value,u,requested) for n,u in zip(ns,units))
    return answer(abs(a-b),'|{} - {}|'.format(format_number(a),format_number(b)))


def _mass_item_count(p):
    """A measured stock divided by the stated mass of a single item."""
    ns = p.numbers
    if len(ns) != 2 or any(n.start >= len(p.body) for n in ns):
        return None
    token = tokenize(p)
    item = re.search(r'\b(?:a|an) (?:[a-z]+ )?([a-z]+)(?: of [a-z ]+)? weighs Q0\b',token)
    if not item or _asked(p) != _singular(item.group(1)):
        return None
    ts = _tails(p)
    scales = {'g':Fraction(1),'gram':Fraction(1),'kg':Fraction(1000),'kilogram':Fraction(1000)}
    units = [_unit(t) for t in ts]
    if not all(u in scales for u in units) or ns[0].value <= 0:
        return None
    if not has(r'\b(?:box|bag|stock|received|has|bought)\b',token.split('Q0',1)[1]):
        return None
    if has(r'\b(?:more|less|than|half|twice|each|every|per|lost|sold)\b',token):
        return None
    a,b = ns[1].value*scales[units[1]],ns[0].value*scales[units[0]]
    value = a/b
    if value.denominator != 1:
        return None
    return answer(value,'{} / {}'.format(format_number(a),format_number(b)))


def _cut_grouped_measure(p):
    """Several rolls/containers of a measure, cut into equal measured pieces."""
    ns = p.numbers
    if len(ns) != 3 or any(n.start >= len(p.body) for n in ns):
        return None
    text = p.text.lower()
    middle = text[ns[0].end:ns[1].start]
    if not re.fullmatch(r'\s+[a-z]+ of\s+',middle):
        return None
    measure = r'(?:m|cm|mm|meters?|centimeters?|millimeters?|feet|foot|inches|yards?)'
    ts = _tails(p)
    a = re.match(r'\s*('+measure+r')\b',ts[1])
    b = re.match(r'\s*('+measure+r')\s+([a-z]+)\b',ts[2])
    if not a or not b or _singular(a.group(1)) != _singular(b.group(1)) or _asked(p) != _singular(b.group(2)):
        return None
    if not has(r'\bcuts? (?:it|them|the [a-z]+) into\s*$',ts[1]):
        return None
    if has(r'\b(?:more|less|than|half|twice|lost|used|left|per|each)\b',p.body) or ns[2].value <= 0:
        return None
    value = ns[0].value*ns[1].value/ns[2].value
    if value.denominator != 1:
        return None
    return answer(value,'{} x {} / {}'.format(*map(format_number,p.values)))


def _daily_production_contents(p):
    """Daily acquired objects have an explicit number of contents per object."""
    ns = p.numbers
    if len(ns) != 3 or any(n.start >= len(p.body) for n in ns):
        return None
    ts = _tails(p)
    rate = re.match(r'\s+([a-z]+) (?:every|per|each|a) day for\s*$',ts[0])
    unit = _singular(rate.group(1)) if rate else ''
    if not unit or _unit(ts[1]) != 'day':
        return None
    if not has(r'\beach '+re.escape(unit)+r' (?:gives? (?:him|her|them)|yields?|contains?|has)\s*$',ts[1]):
        return None
    if _asked(p) != _unit(ts[2]) or not _asked(p):
        return None
    if has(r'\b(?:more|less|than|half|twice|left|remaining|lost|sold|except)\b',p.body):
        return None
    value = ns[0].value*ns[1].value*ns[2].value
    return answer(value,fmt(p.values,' x '))


def _daily_shared_consumption(p):
    """Repeated after-school/daily servings together consume one stock."""
    ns = p.numbers
    if not 3 <= len(ns) <= 5 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'^how many days\b.*\blast\b',p.question):
        return None
    ts = _tails(p)
    unit = _unit(ts[-1])
    if not unit or any(_unit(t) != unit for t in ts):
        return None
    for t in ts[:-1]:
        if not re.match(r'\s+[a-z]+ (?:after school|(?:a|each|every|per) day)\b',t):
            return None
    if not has(r'\b(?:there are|contains?|has)\s*$',p.body[ns[-2].end:ns[-1].start]):
        return None
    if has(r'\b(?:more|less|than|half|twice|left|except)\b',p.body):
        return None
    used = total(n.value for n in ns[:-1])
    if used <= 0:
        return None
    return answer(ns[-1].value/used,'{} / ({})'.format(format_number(ns[-1].value),fmt(n.value for n in ns[:-1])))


def _net_points_rounds(p):
    """A final score plus a stated loss recovers awarded points per round."""
    ns = p.numbers
    if len(ns) != 4 or any(n.start >= len(p.body) for n in ns):
        return None
    token = tokenize(p)
    rate = re.search(r'\bawarded Q0 ([a-z]+) if [a-z]+ win Q1 ([a-z]+)',token)
    if not rate or ns[1].value != 1 or ns[0].value <= 0:
        return None
    if not has(r'\bends? up with Q2 '+re.escape(rate.group(1))+r'\b',token):
        return None
    if not has(r'\blost Q3 '+re.escape(rate.group(1))+r'\b',token) or _asked(p) != _singular(rate.group(2)):
        return None
    if has(r'\b(?:more|less|than|half|twice|each|every)\b',p.body):
        return None
    return answer((ns[2].value+ns[3].value)/ns[0].value,
                  '({} + {}) / {}'.format(*map(format_number,(ns[2].value,ns[3].value,ns[0].value))))


def _repeated_action_average(p):
    """Each of several named participants supplies one score for one action."""
    ns = p.numbers
    if not 2 <= len(ns) <= 8 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\baverage\b',p.question):
        return None
    owners = set()
    actions = set()
    text = p.text.lower()
    for i,n in enumerate(ns):
        m = re.search(r'\b([a-z]+) ([a-z]+) (?:a|an)\s*$',text[ns[i-1].end if i else 0:n.start])
        if not m or m.group(1) in owners or m.group(2) in ('has','had','is','was','were'):
            return None
        if not re.match(r'\s*[.;]',text[n.end:]):
            return None
        owners.add(m.group(1));actions.add(m.group(2))
    if len(actions) != 1 or has(r'\b(?:more|less|than|half|twice|each|per)\b',p.body):
        return None
    if not has(r'\bscore\b',p.question):
        return None
    return answer(total(p.values)/len(ns),'({}) / {}'.format(fmt(p.values),len(ns)))


def _goal_less_progress(p):
    """One explicit goal less the quantities already on hand or completed."""
    ns = p.numbers
    if not 3 <= len(ns) <= 6 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\b(?:more|remaining|left)\b',p.question):
        return None
    if has(r'\b(?:each|every|per|half|twice|than|fewer|less|average)\b',p.body):
        return None
    ts = _tails(p)
    units = [_unit(t) for t in ts]
    if not units[0] or len(set(units)) != 1 or _asked(p) != units[0]:
        return None
    goals = []
    text = p.text.lower()
    for i,n in enumerate(ns):
        prefix = text[ns[i-1].end if i else 0:n.start]
        if re.search(r'\b(?:needs?|requires?|required [a-z]+ to [a-z]+|goal (?:is|of)|must [a-z]+)\s*$',prefix):
            goals.append(i)
    if len(goals) != 1:
        return None
    gi = goals[0]
    for i,n in enumerate(ns):
        if i == gi:
            continue
        before = text[ns[i-1].end if i else 0:n.start]
        if not has(r'\b(?:has|have|had|swam|ran|walked|made|completed|finished|read|wrote|collected|bought|sold)\s*$',before):
            if not (i and has(r'\band\s*$',before) and not has(r'[.;!?]',before)):
                return None
    other = [n.value for i,n in enumerate(ns) if i != gi]
    return answer(ns[gi].value-total(other),'{} - ({})'.format(format_number(ns[gi].value),fmt(other)))


def _stock_then_contents(p):
    """Remove objects from a stock, then give each survivor an equal content."""
    ns = p.numbers
    if len(ns) != 3 or any(n.start >= len(p.body) for n in ns):
        return None
    ts = _tails(p)
    group = _unit(ts[0]);unit = _unit(ts[2])
    if not group or group != _unit(ts[1]) or not unit or _asked(p) != unit or unit == group:
        return None
    token = tokenize(p)
    if not has(r'\b(?:has|had|bakes?|made|baked|bought) Q0\b',token):
        return None
    if not has(r'\b(?:gives? away|gave away|lost|sold|removed) Q1\b',token):
        return None
    if not has(r'\bremaining\b',p.body):
        return None
    if not has(r'Q2\s+[a-z ]+?\s+(?:on|in|for) each '+re.escape(group)+r'\b',token):
        return None
    if has(r'\b(?:more|less|than|half|twice|per|every)\b',p.body):
        return None
    a,b,c = p.values
    return answer((a-b)*c,'({} - {}) x {}'.format(*map(format_number,(a,b,c))))


def _reverse_postposed_stock(p):
    """Arrivals and departures before a final count; recover the initial count."""
    ns = p.numbers
    if not 3 <= len(ns) <= 6 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\bat the start\b|\b(?:did|does) [a-z]+ start\b',p.question):
        return None
    ts = _tails(p)
    unit = _unit(ts[-1])
    if not unit or _asked(p) != unit or any(_unit(t) != unit for t in ts):
        return None
    if not has(r'\b(?:there are now|now has|now have|there were now)\s*$',p.body[ns[-2].end:ns[-1].start]):
        return None
    if has(r'\b(?:each|every|per|than|half|twice|fewer|less)\b',p.body):
        return None
    changes = []
    for i,t in enumerate(ts[:-1]):
        event = re.match(r'\s+(?:more |new )?[a-z]+ (came in|entered|joined|arrived|left|departed)\b',t)
        if not event:
            return None
        changes.append(ns[i].value*(-1 if event.group(1) in ('left','departed') else 1))
    return answer(ns[-1].value-total(changes),
                  '{} - ({})'.format(format_number(ns[-1].value),fmt(changes)))


def _inverse_work(p):
    """The same task with a new number of workers takes inverse time."""
    ns = p.numbers
    if len(ns) != 3 or ns[2].start < len(p.body):
        return None
    token = tokenize(p)
    first = re.search(r'\bworking together,? Q0 ([a-z]+) can ([a-z ]+?) in Q1 (minutes?|hours?|days?)',token)
    if not first or ns[2].value <= 0 or not has(r'Q2 '+re.escape(first.group(1))+r' working together\b',token):
        return None
    if not has(r'\b'+re.escape(first.group(2))+r'\b',p.question):
        return None
    if _asked(p) != _singular(first.group(3)):
        return None
    if has(r'\b(?:more|less|than|half|twice|per|each|every)\b',p.body):
        return None
    a,b,c = p.values
    return answer(a*b/c,'{} x {} / {}'.format(*map(format_number,(a,b,c))))


def _daily_rates_week(p):
    """A list of daily amounts with the same action, combined for a week."""
    ns = list(p.numbers)
    if not has(r'\b(?:one|a|each|per|every) week\b',p.text.lower()):
        return None
    if _unit(p.text.lower()[ns[-1].end:]) == 'week':
        if ns[-1].value != 1 or _unit(p.text.lower()[ns[-1].end:]) != 'week':
            return None
        ns.pop()
    if not 2 <= len(ns) <= 6 or any(n.start >= len(p.body) for n in ns):
        return None
    if has(r'\b(?:more|less|than|half|twice|left|remaining|except|total)\b',p.body):
        return None
    text = p.text.lower()
    units = [];actions = [];daily = 0
    for i,n in enumerate(ns):
        before = text[ns[i-1].end if i else 0:n.start]
        m = re.search(r'\b([a-z]+) (drinks?|eats?|reads?|makes?|uses?|collects?)\s*$',before)
        if not m:
            return None
        actions.append(m.group(2))
        tail = text[n.end:ns[i+1].start if i+1 < len(ns) else len(p.body)]
        units.append(_unit(tail))
        daily += bool(has(r'\b(?:every|each|per|a) day\b',tail))
    if len(set(actions)) != 1 or daily < len(ns)-1 or daily < 2 or len(set(units)) != 1 or units[0] != _asked(p):
        return None
    amounts = [n.value for n in ns]
    return answer(total(amounts)*7,'({}) x 7'.format(fmt(amounts)))


def _weekly_piecewise_rates(p):
    """Several daily route segments, repeated over an explicit weekday range."""
    ns = p.numbers
    if len(ns) != 4 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\bevery day\b',p.body) or not has(r'\bweek\b',p.question):
        return None
    days = '|'.join(_DAYS)
    span = re.search(r'\bfrom ('+days+r') (?:to|through) ('+days+r')\b',p.body)
    if not span or has(r'\b(?:more|less|than|half|twice|except|back|round trip)\b',p.body):
        return None
    ts = _tails(p)
    terms = []
    for i in (0,2):
        rate = re.fullmatch(r'\s+([a-z]+) per (hour|minute) for\s+',ts[i])
        if not rate or _singular(rate.group(1)) != _asked(p):
            return None
        elapsed = _convert(ns[i+1].value,_unit(ts[i+1]),rate.group(2))
        if elapsed is None:
            return None
        terms.append(ns[i].value*elapsed)
    count = (_DAYS.index(span.group(2))-_DAYS.index(span.group(1)))%7+1
    return answer(total(terms)*count,'({}) x {}'.format(fmt(terms),count))


def _daily_then_remainder(p):
    """A repeated daily collection followed by collecting the leftover stock."""
    ns = p.numbers
    if len(ns) != 3 or any(n.start >= len(p.body) for n in ns):
        return None
    token = tokenize(p)
    rate = re.search(r'\bevery day for Q0 days [a-z]+ ([a-z]+) Q1 ([a-z]+)',token)
    if not rate or _asked(p) != _singular(rate.group(2)):
        return None
    if not has(r'\ball the remaining '+re.escape(rate.group(2))+r',? which were Q2\b',token):
        return None
    if not has(r'\btotal\b',p.question) or has(r'\b(?:more|less|than|half|twice|lost|sold)\b',p.body):
        return None
    a,b,c = p.values
    return answer(a*b+c,'{} x {} + {}'.format(*map(format_number,(a,b,c))))


def _round_trip_days(p):
    """An outbound count or distance, repeated to and from over several days."""
    ns = p.numbers
    if len(ns) != 2 or ns[0].start >= len(p.body) or ns[1].start < len(p.body):
        return None
    if not has(r'\bto and from\b',p.question) or _unit(p.text.lower()[ns[1].end:]) != 'day':
        return None
    unit = _unit(p.text.lower()[ns[0].end:])
    if not unit or _asked(p) != unit or not has(r'\bto\b',p.body[ns[0].end:]):
        return None
    if has(r'\b(?:more|less|than|half|twice|each|per|back|round trip)\b',p.body):
        return None
    a,b = p.values
    return answer(a*2*b,'{} x 2 x {}'.format(format_number(a),format_number(b)))


def _fraction_complement(p):
    """The stated fraction is absent/present; ask for the other population."""
    ns = p.numbers
    if len(ns) != 2 or any(n.start >= len(p.body) for n in ns):
        return None
    a,b = ns
    if not (a.value > 1 and 0 < b.value < 1) or _unit(_tails(p)[0]) != _asked(p):
        return None
    relation = re.match(r'\s+of (?:them|these|the [a-z]+) (?:were|are) (absent|present)\b',p.text.lower()[b.end:])
    if not relation:
        return None
    other = 'present' if relation.group(1) == 'absent' else 'absent'
    if not has(r'\b'+other+r'\b',p.question):
        return None
    if has(r'\b(?:each|per|times|more|less|than|twice|half)\b',p.body):
        return None
    return answer(a.value*(1-b.value),'{} x (1 - {})'.format(format_number(a.value),format_number(b.value)))


def _paired_attendees(p):
    """A total attendance, a stated single subset, and the number of pairs."""
    ns = p.numbers
    if len(ns) != 2 or any(n.start >= len(p.body) for n in ns):
        return None
    if _asked(p) not in ('couple','pair'):
        return None
    ts = _tails(p)
    if not _unit(ts[0]) or _unit(ts[0]) != _unit(ts[1]):
        return None
    if not re.match(r'\s+[a-z]+ attended (?:on their own|alone)\b',ts[1]):
        return None
    if not has(r'\bthere were\s*$',p.body[:ns[0].start]):
        return None
    if has(r'\b(?:more|less|than|half|twice|each|per)\b',p.body):
        return None
    a,b = p.values
    value = (a-b)/2
    if value.denominator != 1:
        return None
    return answer(value,'({} - {}) / 2'.format(format_number(a),format_number(b)))


def _assigned_time_remainder(p):
    """A time assignment less several completed sessions, converting units."""
    ns = p.numbers
    if not 3 <= len(ns) <= 6 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\b(?:complete|finish) the assignment\b',p.question):
        return None
    requested = _asked(p)
    if requested not in ('minute','hour') or not has(r'\bassigned\s*$',p.body[:ns[0].start]):
        return None
    ts = _tails(p)
    converted = [_convert(n.value,_unit(t),requested) for n,t in zip(ns,ts)]
    if any(v is None for v in converted):
        return None
    text = p.text.lower()
    for i,n in enumerate(ns[1:],1):
        if not has(r'\b(?:read|worked|practiced|studied) for\s*$',text[ns[i-1].end:n.start]):
            return None
    if has(r'\b(?:each|every|per|times|half|twice|more|less|than)\b',p.body):
        return None
    return answer(converted[0]-total(converted[1:]),'{} - ({})'.format(format_number(converted[0]),fmt(converted[1:])))


def _duration_omitting_groups(p):
    """A whole duration includes N equal interruptions which are excluded."""
    ns = p.numbers
    if len(ns) != 3 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\bnot counting\b',p.question):
        return None
    ts = _tails(p)
    source = _unit(ts[0]);per = _unit(ts[2]);group = _unit(ts[1])
    if source not in ('minute','hour','second') or per not in ('minute','hour','second'):
        return None
    if not re.match(r'\s+[a-z]+ each\b',ts[2]) or not re.match(r'\s+[a-z]+, which lasted\s*$',ts[1]):
        return None
    if not has(r'\b'+re.escape(group)+r'(?:s|es)?\b',p.question):
        return None
    requested = re.search(r'\bin (minutes?|hours?|seconds?)\b',p.question)
    target = _singular(requested.group(1)) if requested else source
    used = _convert(ns[1].value*ns[2].value,per,target)
    whole = _convert(ns[0].value,source,target)
    return answer(whole-used,'{} - {}'.format(format_number(whole),format_number(used)))


def _route_repetitions(p):
    """An outbound and inbound leg, or an explicit return along the same way."""
    ns = p.numbers
    if len(ns) not in (2,3) or any(n.start >= len(p.body) for n in ns):
        return None
    ts = _tails(p)
    unit = _unit(ts[0])
    if unit not in ('mile','kilometer','meter','foot','block') or _unit(ts[1]) != unit or _asked(p) != unit:
        return None
    if has(r'\b(?:more|less|than|half|twice|per|each|every)\b',p.body):
        return None
    if len(ns) == 2:
        if not has(r'\b(?:came|comes|went|goes|walked|walks) home the same (?:way|route)\b',p.body):
            return None
        count = Fraction(2)
    else:
        if not has(r'\b(?:rides?|walks?|travels?) home\b',ts[0]) or not has(r'\bto [a-z ]+ and back\s*$',ts[1]):
            return None
        if not re.match(r'\s+times\b',ts[2]):
            return None
        count = ns[2].value
    return answer((ns[0].value+ns[1].value)*count,
                  '({} + {}) x {}'.format(*map(format_number,(ns[0].value,ns[1].value,count))))


def _returned_progress(p):
    """A partial leg is retraced before completing the original whole route."""
    ns = p.numbers
    if len(ns) != 2 or any(n.start >= len(p.body) for n in ns):
        return None
    ts = _tails(p)
    unit = _unit(ts[0])
    if unit not in ('meter','mile','kilometer','foot') or _unit(ts[1]) != unit or _asked(p) != unit:
        return None
    if not has(r'\bdistance between\b',p.body[:ns[0].start]) or not has(r'\btotal\b',p.question):
        return None
    if not has(r'\breturns to (?:his|her|their) (?:house|home),? then goes back\b',ts[1]):
        return None
    if has(r'\b(?:more|less|than|half|twice|each|per)\b',p.body):
        return None
    a,b = p.values
    return answer(a+2*b,'{} + 2 x {}'.format(format_number(a),format_number(b)))


def _time_overheads(p):
    """Per unit of primary time there are additional durations of other tasks."""
    ns = p.numbers
    if not 4 <= len(ns) <= 6 or any(n.start >= len(p.body) for n in ns):
        return None
    token = tokenize(p)
    if not has(r'\bfor every Q0 (?:minute|hour|second)\b',token):
        return None
    if not has(r'\b(?:spends?|takes?|needs?) an additional Q1\b',token):
        return None
    if not has(r'\b(?:total|combined)\b',p.question):
        return None
    units = [_unit(t) for t in _tails(p)]
    if units[0] not in ('minute','hour','second') or len(set(units)) != 1 or ns[0].value <= 0:
        return None
    last_before = token.split('Q'+str(len(ns)-1))[0]
    if not has(r'\bif\b',last_before.split('Q'+str(len(ns)-2))[-1]):
        return None
    if has(r'\b(?:more|less|than|half|twice|per)\b',p.body):
        return None
    value = ns[-1].value*total(n.value for n in ns[:-1])/ns[0].value
    return answer(value,'{} x ({}) / {}'.format(format_number(ns[-1].value),fmt(n.value for n in ns[:-1]),format_number(ns[0].value)))


def _grouped_and_loose_durations(p):
    """N short measured activities and additional ungrouped durations."""
    ns = p.numbers
    if not 3 <= len(ns) <= 6 or any(n.start >= len(p.body) for n in ns):
        return None
    text = p.text.lower()
    if text[ns[0].end:ns[1].start].strip():
        return None
    ts = _tails(p)
    unit = _unit(ts[1])
    if unit not in ('minute','hour','second') or not re.match(r'-(?:minute|hour|second)\b',ts[1]):
        return None
    if any(_unit(t) != unit for t in ts[2:]):
        return None
    if not has(r'^how (?:much time|long)\b',p.question):
        return None
    if has(r'\b(?:more|less|than|half|twice|left|remaining|not)\b',p.body):
        return None
    terms = [ns[0].value*ns[1].value]+[n.value for n in ns[2:]]
    return answer(total(terms),'{} x {} + {}'.format(format_number(ns[0].value),format_number(ns[1].value),fmt(n.value for n in ns[2:])))


def _member_daily_week(p):
    """An explicit rate per member per day, with a member count, over a week."""
    ns = p.numbers
    if len(ns) != 2 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\b(?:per|a|each|every) week\b',p.question):
        return None
    ts = _tails(p)
    relation = re.search(r'\bper ([a-z]+) per day\b',ts[0])
    if not relation or _unit(ts[1]) != _singular(relation.group(1)) or _asked(p) != _unit(ts[0]):
        return None
    if has(r'\b(?:more|less|than|half|twice|left|remaining|except)\b',p.body):
        return None
    a,b = p.values
    return answer(a*b*7,'{} x {} x 7'.format(format_number(a),format_number(b)))


def _fronted_observation(p):
    """An observed output during a duration, scaled to a new duration."""
    ns = p.numbers
    if len(ns) != 3 or ns[2].start < len(p.body):
        return None
    if not has(r'\bduring\s*$',p.body[:ns[0].start]):
        return None
    ts = _tails(p)
    time = _unit(ts[0]);unit = _unit(ts[1])
    if time not in ('minute','hour','day') or _unit(ts[2]) != time or not unit or _asked(p) != unit:
        return None
    if not has(r'\bcan [a-z]+\s*$',ts[0]) or ns[0].value <= 0:
        return None
    if has(r'\b(?:more|less|than|half|twice|each|every|per|left|remaining|increase|decrease)\b',p.text.lower()):
        return None
    a,b,c = p.values
    return answer(b*c/a,'{} x {} / {}'.format(*map(format_number,(b,c,a))))


def _grouped_resource_remainder(p):
    """A stock minus the resources used by an explicit number of groups."""
    ns = p.numbers
    if len(ns) != 3 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\b(?:left|remaining)\b',p.question):
        return None
    ts = _tails(p)
    units = [_unit(t) for t in ts]
    if not all(units) or units[0] != units[2] or units[0] != _asked(p) or units[0] == units[1]:
        return None
    rel = container_relations(p,_unit,units)
    if rel is None or rel != ({2:1},set()):
        return None
    if not has(r'\b(?:has|had|bought|holds?|contains?)\s*$',p.body[:ns[0].start]):
        return None
    if not has(r'\b(?:uses?|needs?|requires?|takes?|use|need)\s*$',ts[1]):
        return None
    if has(r'\b(?:more|less|than|half|twice|lost|sold|per)\b',p.body):
        return None
    a,b,c = p.values
    return answer(a-b*c,'{} - {} x {}'.format(*map(format_number,(a,b,c))))


def _unused_capacity(p):
    """Counted containers have a stated capacity; subtract the current users."""
    ns = p.numbers
    if len(ns) != 3 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\b(?:available|empty|vacant|unoccupied) (?:spaces?|places?|seats?)\b',p.question):
        return None
    ts = _tails(p)
    units = [_unit(t) for t in ts]
    if not all(units) or units[1] != units[2] or units[0] == units[1]:
        return None
    if not re.fullmatch(r'\s+[a-z]+ with a capacity of\s+',ts[0]):
        return None
    if not re.match(r'\s+[a-z]+ each[.;]',ts[1]):
        return None
    if not re.match(r'\s+[a-z]+ were (?:sitting|seated|standing)\b',ts[2]):
        return None
    if has(r'\b(?:more|less|than|half|twice|per|not)\b',p.body):
        return None
    a,b,c = p.values
    return answer(a*b-c,'{} x {} - {}'.format(*map(format_number,(a,b,c))))


def _each_type_contents(p):
    """A stated number of types has known contents and an equal order per type."""
    ns = p.numbers
    # "one with ... the other with ..." enumerates types, rather than
    # supplying an additional quantity of contents or ordered containers.
    if (len(ns) >= 5 and ns[1].value == 1
            and re.fullmatch(r'\s+types of [a-z]+,?\s+',p.text.lower()[ns[0].end:ns[1].start])
            and re.match(r'\s+with\b',p.text.lower()[ns[1].end:])):
        p = p.__class__(p.text,p.body,p.question,ns[:1]+ns[2:])
        ns = p.numbers
    if not 4 <= len(ns) <= 7 or any(n.start >= len(p.body) for n in ns):
        return None
    if ns[0].value != len(ns)-2:
        return None
    token = tokenize(p)
    if not has(r'Q0 types of [a-z]+,?\b',token):
        return None
    ts = _tails(p)
    if not has(r'\bof each type\b',ts[-1]):
        return None
    unit = _asked(p)
    if not unit or any(_unit(t) != unit for t in ts[1:-1]):
        return None
    for i in range(1,len(ns)-1):
        before = token.split('Q'+str(i))[0]
        if not has(r'\b(?:one|other|another) with\s*$',before):
            return None
    if has(r'\b(?:more|less|than|half|twice|left|lost|sold)\b',p.body):
        return None
    return answer(total(n.value for n in ns[1:-1])*ns[-1].value,
                  '({}) x {}'.format(fmt(n.value for n in ns[1:-1]),format_number(ns[-1].value)))


def _ratio_extreme_total(p):
    """The length of the shortest/longest ratio part determines the whole."""
    ns = p.numbers
    if not 4 <= len(ns) <= 8 or any(n.start >= len(p.body) for n in ns):
        return None
    token = tokenize(p)
    ratio = re.search(r'\bratio of (Q\d+(?:\s*:\s*Q\d+)+)',token)
    if not ratio:
        return None
    indices = [int(i) for i in re.findall(r'Q(\d+)',ratio.group(1))]
    if indices != list(range(1,len(ns)-1)) or ns[0].value != len(indices):
        return None
    if not has(r'\bcut into Q0 (?:smaller )?(?:pieces|parts)\b',token):
        return None
    known = re.search(r'\b(shortest|longest|smallest|largest) (?:piece|part) is Q'+str(len(ns)-1)+r'\b',token)
    if not known or not has(r'\b(?:entire|whole|total|before it was cut)\b',p.question):
        return None
    ratios = [ns[i].value for i in indices]
    if min(ratios) <= 0:
        return None
    part = min(ratios) if known.group(1) in ('shortest','smallest') else max(ratios)
    return answer(ns[-1].value*total(ratios)/part,
                  '{} x ({}) / {}'.format(format_number(ns[-1].value),fmt(ratios),format_number(part)))


def _purchases_less_left(p):
    """Elliptical dated purchases and an explicit amount left determine use."""
    ns = p.numbers
    if not 3 <= len(ns) <= 7 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\b(?:eat|use|consume|ate|used|consumed)\b',p.question):
        return None
    ts = _tails(p)
    if not re.match(r'\s+of them left\b',ts[-1]):
        return None
    if not has(r'\bbought\s*$',p.body[:ns[0].start]):
        return None
    for t in ts[:-1]:
        if not re.match(r'\s+on (?:'+'|'.join(_DAYS)+r')\b',t):
            return None
    if has(r'\b(?:each|every|per|more|less|than|half|twice|gave|sold|lost)\b',p.body):
        return None
    bought = [n.value for n in ns[:-1]]
    return answer(total(bought)-ns[-1].value,'({}) - {}'.format(fmt(bought),format_number(ns[-1].value)))


def _combined_event_ratio(p):
    """A for-every event ratio and a known reference amount, asking for both."""
    ns = p.numbers
    if len(ns) != 3 or any(n.start >= len(p.body) for n in ns):
        return None
    ts = _tails(p)
    if not re.fullmatch(r'\s+times for every\s+',ts[0]) or ns[1].value <= 0:
        return None
    reference = re.match(r'\s+times?\s+([a-z ]+?)[.;]\s*if \1\s*$',ts[1])
    if not reference or not re.match(r'\s+times\b',ts[2]):
        return None
    if not has(r'\bboth\b.*\b(?:combined|together|total)\b',p.question) or _asked(p) != 'time':
        return None
    if has(r'\b(?:more|less|than|half|twice|left|remaining)\b',p.body):
        return None
    a,b,c = p.values
    return answer(c*(1+a/b),'{} x (1 + {} / {})'.format(*map(format_number,(c,a,b))))


def solve(problem):
    if any(n.kind != 'number' or n.value < 0 for n in problem.numbers):
        return None
    for reader in (_postposed_stock, _short_stock_ledger, _time_budget, _group_complement,
                   _dozen_contents, _restated_group, _parts_mixture,
                   _recipient_list, _attendance_list, _collection_duration,
                   _reward_schedule, _weekly_named_days, _excluded_categories,
                   _labelled_ratio, _companions_remainder, _passive_contents,
                   _measured_stock, _task_duration_difference, _mass_item_count,
                   _cut_grouped_measure, _daily_production_contents,
                   _daily_shared_consumption, _net_points_rounds,
                   _repeated_action_average, _goal_less_progress,
                   _stock_then_contents, _reverse_postposed_stock,
                   _inverse_work, _daily_rates_week, _weekly_piecewise_rates,
                   _daily_then_remainder, _round_trip_days, _fraction_complement,
                   _paired_attendees, _assigned_time_remainder,
                   _duration_omitting_groups, _route_repetitions,
                   _returned_progress, _time_overheads,
                   _grouped_and_loose_durations, _member_daily_week,
                   _fronted_observation, _grouped_resource_remainder,
                   _unused_capacity, _each_type_contents, _ratio_extreme_total,
                   _purchases_less_left, _combined_event_ratio):
        result = reader(problem)
        if result is not None:
            return result
    return None
