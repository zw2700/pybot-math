"""Explicit group arithmetic, stock changes, and repeated schedules.

Readers account for every numeric span and require the requested unit to
agree with the relations. Unsupported modifiers or unknown scopes abstain.
"""
import re
from fractions import Fraction

from ..numbers import format_number
from ._counting_common import answer, total, products
from ._counting_groups import container_relations
from .counting_and_totals_r02_a2 import _noun
from .rates_and_unit_rates_r01_a4 import _convert
from ._money_common import _singular
from .counting_and_totals_r00_a1 import _different_owner
from .counting_and_totals_r08_a2 import _matches_label


def has(pattern, text):
    return re.search(pattern, text) is not None


def noun(tail):
    tail = re.sub(r'^\s*(?:more|fewer|extra|additional|total)\s+', ' ', tail)
    tail = re.split(r'\b(?:brought|donate[sd]?|donations|floated|rotten|'
                    r'kept|borrowed|earned|scored|lasted|along|free|'
                    r'walks?|runs?|trains?|doing|training|needs?|'
                    r'invites?|asks?|help|longer|shorter)\b', tail)[0]
    return _noun(tail)


def asked(p):
    m = re.match(r'how (?:many|much)\s+(.*)', p.question)
    if not m:
        m = re.search(r'(?:total|combined) (?:number|amount) of\s+(.*)', p.question)
    return noun(m.group(1)) if m else ''


def suffixes(p):
    text = p.text.lower()
    return [text[n.end:p.numbers[i+1].start if i+1 < len(p.numbers)
                 else len(p.body)] for i, n in enumerate(p.numbers)]


def expression(values, op=' + '):
    return op.join(format_number(v) for v in values)


def _group_ledger(p):
    """Compose explicit per-group edges with loose stock and local removals."""
    ns, text = p.numbers, p.text.lower()
    if _different_owner(p):
        return None
    if not 3 <= len(ns) <= 8 or any(n.start >= len(p.body) or n.kind != 'number' for n in ns):
        return None
    if any(0 < n.value < 1 and re.match(r'\s+of\b',text[n.end:]) for n in ns):
        return None  # A share of a stock is not another stock entry.
    if has(r'\b(?:times|twice|thrice|half|percent|average|ratio|than|'
           r'longer|shorter|some|another|dozen|per day|every day)\b', p.body):
        return None
    ts = suffixes(p)
    units = [noun(t) for t in ts]
    target = asked(p)
    if not target:
        return None
    # An elided count noun in a coordinated list inherits the previous noun.
    for i in range(1, len(ns)):
        if not units[i] and re.match(r'\s*[.,;]', ts[i]):
            units[i] = units[i-1]
    relations = container_relations(p, noun, units)
    parents, references = relations if relations is not None else ({}, set())
    for i in range(1, len(ns)):
        before = text[ns[i-1].end:ns[i].start]
        after = re.split(r'[.!?;](?:\s|$)', ts[i])[0]
        # N people brought M objects each; N groups, each with M objects.
        if (has(r'\b(?:brought|bring|donate[sd]?|earned|scored|have|has|had)\s*$', before)
                and has(r'\beach(?:\s+(?:on|in|at|for|to)\b|\s*$)', after)
                or has(r'\beach\s+(?:with|having|holding|containing)\s*$', before)):
            if i in parents and parents[i] != i-1:
                return None
            parents[i] = i-1
        if (has(r'\bwith\s*$', before)
                and (has(r'\beach(?:\s+(?:on|in|at|for|to)\b|\s*$)', after)
                     or has(r'\bin a '+re.escape(units[i-1])+r'\b',after))):
            parents[i] = i-1
        # M objects for each of the N groups (allow intervening ownership).
        if has(r'\b(?:for|from|in) each of\b[^.;!?]*$', before):
            parents[i-1] = i
    active = set(range(len(ns))) - references
    if relations is None and not parents and has(r'\b(?:each|every|per)\b',p.body):
        return None
    terms = products([n.value for n in ns],
                     {i: (j, Fraction(1)) for i,j in parents.items()}, active=active)
    if terms is None or any(units[i] != target for i,_,_ in terms):
        return None
    label_problem = p.__class__(p.text,p.body,
                               re.sub(r'^(how many) fewer\b',r'\1',p.question),ns)
    if any(not _matches_label(label_problem,ts[i]) for i,_,_ in terms):
        return None
    for i,_,_ in terms:
        if i not in parents and i-1 in parents:
            middle = text[ns[i-1].end:ns[i].start]
            if (units[i] == units[i-1] and has(r'\band\s*$',middle)
                    and not has(r'[.!?;]',middle)):
                return None  # Coordinated contents may share the earlier rate.
    removal_query = has(r'\b(?:left|remaining|remain|without|not|sold|sell|lose|now)\b', p.question)
    if has(r'\b(?:more|fewer|difference)\b', p.question) and not removal_query:
        if len(terms) != 2 or not parents:
            return None
        return answer(abs(terms[0][1]-terms[1][1]),
                      '|(' + terms[0][2] + ') - (' + terms[1][2] + ')|')
    if len(terms) > 1:
        group_units = {units[j] for j in parents.values()}
        selected = {u for u in group_units if u and has(r'\b'+re.escape(u)+r'(?:s|es)?\b',p.question)}
        if selected and selected != group_units:
            return None  # A query about one group cannot combine its peers.
    values, work = [], []
    previous_sign = None
    for i, value, working in terms:
        before = text[ns[i-1].end if i else 0:ns[i].start]
        clause = re.split(r'[.!?;](?:\s|$)|\b(?:and|but|while)\b', before)[-1]
        tail = re.split(r'[.!?;](?:\s|$)', ts[i])[0]
        remove = has(r'\b(?:lost|loses?|ate|eats?|sold|sells?|borrowed|'
                     r'gave|gives?|took|taken|removed|used)\b', clause)
        incoming = has(r'\b(?:gave|gives?) (?:him|her|them|me|us)\s*$',clause)
        if incoming:
            remove = False
        remove = remove or has(r'\b(?:rotten|broken|have a hole|has a hole|'
                               r'are borrowed|were borrowed|will be kept|'
                               r'(?:are|were) taken out|(?:are|were) sold)\b', tail)
        threshold = has(r'\b(?:at least|minimum)\s*$', clause) and has(r'\blose\b', p.question)
        add = has(r'\b(?:has|have|had|bought|received|there are|there were|'
                  r'made|collected|donate[sd]?|earned|scored|brought|started with)\b', clause)
        add = add or has(r'\b(?:are |were )?brought back\b',tail)
        add = add or incoming
        coordinated = before
        # Group contents inherit the event associated with the group count.
        if i in parents:
            j = parents[i]
            context = text[ns[j-1].end if j else 0:ns[j].start]
            add = add or has(r'\b(?:there are|there were|has|have|had|brought|earned|donate[sd]?)\b', context)
            coordinated = context
            if removal_query and has(r'\b(?:needs?|requires?)\s*$',clause):
                remove = True
        if remove or threshold:
            if not removal_query:
                return None
            sign = -1
        elif add:
            sign = 1
        elif previous_sign is not None and has(r'\band\b|,', coordinated) and not has(r'[.!?;]', coordinated):
            sign = previous_sign
        else:
            return None
        if sign > 0 and i and i not in parents and has(r'\b(?:in total|total of|altogether)\b',clause):
            return None  # An aggregate observation can overlap prior stock.
        if not removal_query and has(r'\b(?:rest|kept|remaining|left)\b', p.body):
            return None
        previous_sign = sign
        values.append(sign*value)
        work.append((' - ' if sign < 0 else ' + ') + '(' + working + ')')
    if not parents and not any(v < 0 for v in values):
        return None
    return answer(total(values), ''.join(work).lstrip(' +'))


def _session_durations(p):
    """Each session type has an explicit duration and weekly frequency."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 4 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\b(?:week|weekly)\b', p.question) or asked(p) not in ('hour','minute'):
        return None
    if has(r'\b(?:more|less|fewer|than|half|twice|average)\b', p.body):
        return None
    ts = suffixes(p)
    rates = []
    for a,b in ((0,1),(2,3)):
        # Both orders: D hours F times a week, or F times a week for D hours.
        if has(r'^\s+times\s+(?:a|per|each|every) week\b', ts[a]):
            freq, dur = a,b
        elif has(r'^\s+times\s+(?:a|per|each|every) week\b', ts[b]):
            freq, dur = b,a
        else:
            return None
        unit = noun(ts[dur])
        value = _convert(ns[dur].value,unit,asked(p))
        if value is None:
            return None
        rates.append(ns[freq].value*value)
    return answer(total(rates), expression(rates))


def _active_daily_duration(p):
    """A rate applies only during the stated daily activity duration."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) not in (2,3) or not has(r'\b(?:each|every) day\b', p.body):
        return None
    ts = suffixes(p)
    m = re.match(r'\s+([a-z]+)\s+(?:per|each|every|a) (second|minute|hour)\b', ts[0])
    if not m or asked(p) != _singular(m.group(1)):
        return None
    if has(r'\b(?:more|less|half|twice|than|lost|remaining)\b', text):
        return None
    if len(ns) == 2:
        duration = re.search(r'\bfor (?:an?|one) (second|minute|hour)\b',p.body)
        if not duration:
            return None
        active = _convert(Fraction(1),duration.group(1),m.group(2))
    else:
        if not has(r'\bfor\s*$',text[:ns[1].start]):
            return None
        active = _convert(ns[1].value,noun(ts[1]),m.group(2))
    last = ns[-1]
    unit = noun(text[last.end:])
    if last.start < len(p.body) or unit not in ('day','week') or active is None:
        return None
    days = last.value * (7 if unit == 'week' else 1)
    return answer(ns[0].value*active*days,
                  expression((ns[0].value,active,days),' x '))


def _interval_output(p):
    """An output during an explicit interval, scaled to a new time span."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 3 or ns[-1].start < len(p.body):
        return None
    a,b,c = ns
    if not has(r'\b(?:during|in|every)\s*$',text[:a.start]):
        return None
    ts = suffixes(p)
    period, result_unit = noun(ts[0]),noun(ts[1])
    duration_unit = noun(text[c.end:])
    if period not in ('second','minute','hour') or asked(p) != result_unit:
        return None
    if has(r'\b(?:more|less|than|left|remaining|half|twice)\b',text):
        return None
    duration = _convert(c.value,duration_unit,period)
    if duration is None or a.value <= 0:
        return None
    return answer(b.value*duration/a.value,
                  '{} x {} / {}'.format(*map(format_number,(b.value,duration,a.value))))


def _weekly_extra(p):
    """A daily amount plus an explicitly additional weekly amount."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 3 or ns[-1].start < len(p.body):
        return None
    ts = suffixes(p)
    if not has(r'\b(?:each|every|per|a) day\b',ts[0]):
        return None
    if not has(r'^\s+more\s+[a-z]+\s+(?:each|every|per|a) week\b',ts[1]):
        return None
    unit = noun(ts[0])
    if noun(ts[1]) != unit or asked(p) != unit or noun(text[ns[-1].end:]) != 'week':
        return None
    a,b,c = (n.value for n in ns)
    return answer((7*a+b)*c,'(7 x {} + {}) x {}'.format(*map(format_number,(a,b,c))))


def _fraction_left(p):
    """A stated fraction remains, so the removed part is its complement."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 2 or any(n.start >= len(p.body) for n in ns):
        return None
    a,b = ns
    if not 0 < b.value < 1 or not has(r'^\s+of (?:the|these|those|his|her|their)\b', text[b.end:]):
        return None
    if not has(r'\b(?:are|were|is|was) left\b|\bremain',text[b.end:len(p.body)]):
        return None
    if not has(r'\b(?:sell|sold|give|gave|remove|removed|lost|use|used)\b',p.question):
        return None
    if has(r'\b(?:each|every|per|more|less|twice)\b',text):
        return None
    return answer(a.value*(1-b.value),'{} x (1 - {})'.format(format_number(a.value),format_number(b.value)))


def _relative_repeated_group(p):
    """One base duration and N sessions each D longer, summed with base."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) not in (2,4) or not has(r'\b(?:longer|late than)\b',p.body):
        return None
    if not has(r'\b(?:total|how long|how much time)\b',p.question):
        return None
    ts = suffixes(p)
    if len(ns) == 2:
        a,d = ns
        if not has(r'\bboth\b',p.body) or not has(r'\beach\b',text[d.end:len(p.body)]):
            return None
        count = Fraction(2)
    else:
        a,n,d,whole = ns
        if whole.start < len(p.body) or whole.value != n.value+1:
            return None
        if not has(r'\beach\b',text[n.end:d.start]):
            return None
        count = n.value
    unit = noun(text[a.end:])
    if unit not in ('minute','hour','second') or noun(text[d.end:]) != unit:
        return None
    return answer(a.value+count*(a.value+d.value),
                  '{0} + {1} x ({0} + {2})'.format(*map(format_number,(a.value,count,d.value))))


_MONTHS = 'january february march april may june july august september october november december'.split()


def _monthly_growth(p):
    """Repeated doubling/tripling between explicitly named calendar months."""
    if len(p.numbers) != 1 or p.numbers[0].start >= len(p.body):
        return None
    text = p.text.lower()
    m = re.search(r'\b(doubled|tripled) every month\b',p.body)
    if not m:
        return None
    starts = [i for i,w in enumerate(_MONTHS) if has(r'\bin '+w+r'\b',p.body)]
    ends = [i for i,w in enumerate(_MONTHS) if has(r'\b(?:in|of|for) '+w+r'\b',p.question)]
    if len(starts) != 1 or len(ends) != 1 or ends[0] <= starts[0]:
        return None
    if asked(p) != noun(text[p.numbers[0].end:]) and not has(r'\bproduction\b',p.question):
        return None
    factor = 2 if m.group(1) == 'doubled' else 3
    steps = ends[0]-starts[0]
    value = p.numbers[0].value
    return answer(value*factor**steps,'{} x {}^{}'.format(format_number(value),factor,steps))


def _weekday_categories(p):
    """Count explicitly enumerated weekdays in two production categories."""
    ns = p.numbers
    if len(ns) not in (1,2) or not has(r'\b(?:week|weekly)\b',p.question):
        return None
    if len(ns) == 2 and (ns[1].start < len(p.body) or ns[1].value != 1):
        return None
    text = p.text.lower()
    tail = text[ns[0].end:len(p.body)]
    if not has(r'^\s+[a-z]+\s+per day\b',tail) or asked(p) != noun(tail):
        return None
    weekdays = r'(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)s?'
    groups = re.findall(r'\bon ('+weekdays+r'(?:\s*,?\s*(?:and\s+)?'+weekdays+r')*)\s*,',p.body)
    if len(groups) != 2:
        return None
    counts = [len(re.findall(weekdays,g)) for g in groups]
    if has(r'\b(?:more|fewer|difference)\b',p.question):
        value = abs(counts[0]-counts[1])*ns[0].value
    elif has(r'\b(?:total|in all|altogether)\b',p.question):
        value = sum(counts)*ns[0].value
    else:
        return None
    return answer(value,'Daily amount times the requested number of days')


def _invited_companions(p):
    """Two invited groups, each bringing the same number of companions."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 3 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\beach of\b[^.;!?]*\bbring\s*$',text[:ns[2].start]):
        return None
    units = [noun(t) for t in suffixes(p)]
    if not all(units) or len(set(units)) != 1:
        return None
    if not has(r'\binvites?\b',text[:ns[0].start]) or not has(r'\balong\b',text[ns[2].end:len(p.body)]):
        return None
    if asked(p) not in ('person','people') or not has(r'\b(?:going|attend|coming|party|event)\b',p.question):
        return None
    a,b,c = (n.value for n in ns)
    return answer((a+b)*(1+c),'({} + {}) x (1 + {})'.format(*map(format_number,(a,b,c))))


def _block_array(p):
    """Identical walls/arrays whose three dimensions are counted in blocks."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) not in (4,5) or any(n.start >= len(p.body) for n in ns):
        return None
    dims = ns[-3:]
    labels = []
    for n in dims:
        m = re.match(r'\s+([a-z]+)\s+(long|high|deep|wide|tall)\b',text[n.end:])
        if not m:
            return None
        labels.append((_singular(m.group(1)),m.group(2)))
    if len({u for u,d in labels}) != 1 or len({d for u,d in labels}) != 3 or asked(p) != labels[0][0]:
        return None
    groups = ns[:-3]
    if len(groups) == 2:
        if groups[0].value != groups[1].value or not has(r'\beach of the\s*$',text[:groups[1].start]):
            return None
    elif not has(r'\beach\b',text[groups[0].end:dims[0].start]):
        return None
    vals = [groups[-1].value] + [n.value for n in dims]
    result = Fraction(1)
    for v in vals:
        result *= v
    return answer(result,expression(vals,' x '))


def _return_trip_times(p):
    """The same distance traversed at two directional speeds."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 3 or ns[-1].start < len(p.body):
        return None
    if not has(r'\bup\b',p.body) or not has(r'\bdown\b',p.body) or not has(r'\bup and down\b',p.question):
        return None
    if not has(r'^how long\b',p.question):
        return None
    rates = []
    for n in ns[:2]:
        m = re.match(r'\s+([a-z]+)\s*(?:/|per\s+)(second|minute|hour)\b',text[n.end:])
        if not m:
            return None
        rates.append((_singular(m.group(1)),m.group(2)))
    if rates[0] != rates[1] or noun(text[ns[2].end:]) != rates[0][0]:
        return None
    if min(n.value for n in ns) <= 0:
        return None
    a,b,d = (n.value for n in ns)
    return answer(d/a+d/b,'{0} / {1} + {0} / {2}'.format(*map(format_number,(d,a,b))))


def _inverse_category_sum(p):
    """A named owner has a multiple of another owner's two category counts."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 3 or any(n.start >= len(p.body) for n in ns):
        return None
    a,b,c = ns
    m = re.search(r'\b([a-z]+) (?:bought|has|owns|collected)\s*$',text[:a.start])
    relation = re.match(r'\s+times (?:more|as many) (.+?) than ([a-z]+)\.',text[a.end:])
    if not m or not relation or a.value <= 0:
        return None
    owner, other = m.group(1),relation.group(2)
    if not has(r'\b'+owner+r' (?:bought|has|owns|collected)\s*$',text[a.end:b.start]):
        return None
    if not has(r'\b'+other+r'\b',p.question) or has(r'\b'+owner+r'\b',p.question):
        return None
    if not has(r'\b(?:total|altogether|in all|and)\b',p.question):
        return None
    if any(not has(r'\b'+re.escape(noun(text[n.end:]))+r'(?:s|es)?\b',p.question) for n in (b,c)):
        return None
    return answer((b.value+c.value)/a.value,
                  '({} + {}) / {}'.format(*map(format_number,(b.value,c.value,a.value))))


def _priced_categories(p):
    """Two explicitly named item prices and their matching sold counts."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 4 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\b(?:how much money|total (?:cost|price|sales))\b',p.question):
        return None
    prices = {}
    for i,n in enumerate(ns[:2]):
        if not has(r'^\s+dollars? each\b',text[n.end:]):
            return None
        before = text[ns[i-1].end if i else 0:n.start]
        m = re.search(r'\b([a-z]+) at\s*$',before)
        if not m:
            return None
        prices[_singular(m.group(1))] = n.value
    if len(prices) != 2 or not has(r'\bsold\s*$',text[ns[1].end:ns[2].start]):
        return None
    terms = []
    for n in ns[2:]:
        unit = noun(text[n.end:])
        if unit not in prices:
            return None
        terms.append(n.value*prices.pop(unit))
    if prices:
        return None
    return answer(total(terms),expression(terms))


def _dozen_ledger(p):
    """A singular dozen is a counted group, including a coordinated stock."""
    if not has(r'\b(?:a|one) dozen\b',p.body):
        return None
    from ..problem import Problem
    expanded = re.sub(r'\b(?:a|one) dozen\b','12',p.text,flags=re.I)
    updated = Problem.read(expanded)
    return _group_ledger(updated) if updated else None


def _named_comparison_chain(p):
    """Resolve named inventories linked by explicit additive comparisons."""
    ns, text = p.numbers, p.text.lower()
    if not 3 <= len(ns) <= 5 or not has(r'\b(?:total|altogether|combined|in all|average)\b',p.question):
        return None
    if has(r'\b(?:each|per|times|twice|half|percent|lost|gave|sold)\b',p.body):
        return None
    counts, pending, used, group_sizes = {}, [], set(), []
    unit = ''
    for i,n in enumerate(ns):
        if n.start >= len(p.body):
            if re.match(r'\s+(?:of them|have|people|friends)\b',text[n.end:]):
                group_sizes.append(n.value)
                used.add(i)
                continue
            return None
        before = text[ns[i-1].end if i else 0:n.start]
        m = re.search(r'\b([a-z]+) (?:has|have|had|collected|owns?)\s*$',before)
        if not m:
            # Putting all the counted objects in a single container is storage.
            if n.value == 1 and has(r'\ball their\b[^.;!?]*\bin\s*$',before):
                used.add(i)
                continue
            return None
        owner = m.group(1)
        tail = text[n.end:ns[i+1].start if i+1 < len(ns) else len(p.body)]
        tail = re.sub(r'\b(?:mr|mrs|ms|dr)\.\s*','',tail)
        u = noun(tail)
        if unit and unit != u or not u:
            return None
        unit = u
        rel = re.match(r'\s+(more|fewer|less)\s+[a-z ]+?\s+than ([a-z]+)\b',tail)
        if rel:
            pending.append((owner,rel.group(2),n.value*(-1 if rel.group(1) != 'more' else 1)))
        elif not counts:
            counts[owner] = n.value
        else:
            return None
        used.add(i)
    if len(used) != len(ns) or not pending:
        return None
    for unused in range(len(pending)):
        for owner,ref,diff in pending:
            if ref in counts:
                counts[owner] = counts[ref]+diff
    if len(counts) != len(pending)+1 or min(counts.values()) < 0:
        return None
    if any(size != len(counts) for size in group_sizes):
        return None
    if asked(p) != unit and not has(r'\baverage number of '+unit+r's?\b',p.question):
        return None
    value = total(counts.values())
    work = expression(counts.values())
    if has(r'\baverage\b',p.question):
        value /= len(counts)
        work = '('+work+') / '+str(len(counts))
    return answer(value,work)


def _parallel_interval_rates(p):
    """Several explicit output/interval pairs over one common duration."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) not in (5,7,9) or not has(r'\b(?:total|altogether|combined|both)\b',p.question):
        return None
    if has(r'\b(?:more|less|than|left|lost|remaining|twice|half)\b',text):
        return None
    span = ns[-1]
    if not has(r'\b(?:for|in)\s*$',text[:span.start]):
        return None
    duration_unit = noun(text[span.end:])
    if duration_unit not in ('second','minute','hour'):
        return None
    terms = []
    unit = asked(p)
    for i in range(0,len(ns)-1,2):
        a,b = ns[i:i+2]
        if noun(text[a.end:b.start]) != unit or not has(r'\bin\s*$',text[a.end:b.start]):
            return None
        period = noun(text[b.end:])
        duration = _convert(span.value,duration_unit,period)
        if duration is None or b.value <= 0:
            return None
        terms.append(a.value*duration/b.value)
    return answer(total(terms),expression(terms))


def _shared_contents(p):
    """Sum explicitly labelled group counts before applying a shared rate."""
    ns, text = p.numbers, p.text.lower()
    if not 3 <= len(ns) <= 6 or any(n.start >= len(p.body) for n in ns):
        return None
    if has(r'\b(?:more|less|fewer|than|lost|left|remaining|half|twice|percent|average)\b',text):
        return None
    rate = ns[-1]
    intro = re.search(r'\beach ([a-z]+) (?:has|have|contains?|holds?|needs?)\s*$',text[:rate.start])
    if not intro or noun(text[rate.end:]) != asked(p):
        return None
    group = _singular(intro.group(1))
    counts = []
    extra = []
    for i,n in enumerate(ns[:-1]):
        u = noun(text[n.end:])
        if u == group:
            counts.append(n.value)
        else:
            extra.append((i,n,u))
    # An opening count of two parent groups, then "one ... the other".
    if extra:
        if len(extra) != 2 or [i for i,n,u in extra] != [0,1]:
            return None
        if extra[0][1].value != 2 or extra[1][1].value != 1 or extra[0][2] != extra[1][2]:
            return None
        if len(counts) != 2 or not has(r'\bthe other\b',p.body):
            return None
    if len(counts) < 2:
        return None
    return answer(total(counts)*rate.value,'('+expression(counts)+') x '+format_number(rate.value))


def _cycle_count(p):
    """Each repeated turn has an active duration and a stated rest duration."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 3 or ns[-1].start < len(p.body):
        return None
    if not has(r'\bbefore\b[^.;!?]*\banother turn\b',p.body) or not has(r'\bturns\b',p.question):
        return None
    a,b,c = ns
    unit = noun(text[a.end:])
    if unit not in ('second','minute','hour') or noun(text[b.end:]) != unit:
        return None
    duration = _convert(c.value,noun(text[c.end:]),unit)
    if duration is None or a.value+b.value <= 0:
        return None
    cycles = duration/(a.value+b.value)
    # Only complete cycles fit this reading, including their stated rest.
    return answer(Fraction(cycles.numerator//cycles.denominator),
                  '{} / ({} + {})'.format(*map(format_number,(duration,a.value,b.value))))


def _speed_difference(p):
    """One journey's distance and two travel durations imply two speeds."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 3 or not has(r'\bdifference\b.*\bspeed\b',p.question):
        return None
    if not has(r'\bsame trip\b',p.body):
        return None
    a,b,d = ns
    if noun(text[a.end:]) != 'hour' or noun(text[b.end:]) != 'hour' or noun(text[d.end:]) not in ('mile','kilometer','km'):
        return None
    if min(a.value,b.value) <= 0:
        return None
    return answer(abs(d.value/a.value-d.value/b.value),
                  '|{0} / {1} - {0} / {2}|'.format(*map(format_number,(d.value,a.value,b.value))))


def _opposite_motion(p):
    """Two travellers leave the same location in opposite directions."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 3 or not has(r'\bopposite directions\b',p.body) or not has(r'\bsame (?:spot|place|point)\b',p.body):
        return None
    if not has(r'\bdistance between\b',p.question):
        return None
    rates = []
    for n in ns[:2]:
        m = re.match(r'\s+([a-z]+) per (hour|minute|second)\b',text[n.end:])
        if not m:
            return None
        rates.append((_singular(m.group(1)),m.group(2)))
    if rates[0] != rates[1]:
        return None
    d = _convert(ns[-1].value,noun(text[ns[-1].end:]),rates[0][1])
    if d is None:
        return None
    a,b = (n.value for n in ns[:2])
    return answer((a+b)*d,'({} + {}) x {}'.format(*map(format_number,(a,b,d))))


def _money_shortfall(p):
    """Two desired purchases, savings and a gift, queried as money lacking."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 4 or not has(r'\b(?:lack|short|need|missing)\b',p.question):
        return None
    units = [noun(text[n.end:]) for n in ns]
    if len(set(units)) != 1 or units[0] not in ('euro','dollar','pound'):
        return None
    if not has(r'\b(?:wants? to buy|needs? to buy)\b',text[:ns[0].start]):
        return None
    if not has(r'\bsavings\b',text[ns[2].end:ns[3].start]) or not has(r'\bgiving (?:him|her|them)\s*$',text[:ns[3].start]):
        return None
    a,b,c,d = (n.value for n in ns)
    return answer(a+b-c-d,'{} + {} - {} - {}'.format(*map(format_number,(a,b,c,d))))


def _relative_daily_output(p):
    """Combine two daily/hourly outputs, one described by a difference."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) not in (2,4) or not has(r'\bmore\b[^.;!?]*\bthan\b',p.body):
        return None
    differences = [i for i in (0,1) if re.match(r'\s+more\s+',text[ns[i].end:])]
    if len(differences) != 1:
        return None
    di = differences[0]
    diff,base = ns[di],ns[1-di]
    base_unit = noun(text[base.end:])
    diff_unit = noun(text[diff.end:])
    if not base_unit or not diff_unit or base_unit == diff_unit:
        return None
    period = re.search(r'\b(?:per|every|each) (day|hour)\b',p.body[:ns[1].end+100])
    if not period:
        return None
    denom = period.group(1)
    for i in (0,1):
        tail = text[ns[i].end:ns[i+1].start if i+1 < len(ns) else len(p.body)]
        if not has(r'\b(?:per|every|each) '+denom+r'\b',tail):
            return None
    if not (all(has(r'\b'+re.escape(u)+r'(?:s|es)?\b',p.question) for u in (base_unit,diff_unit))
            or has(r'\bproducts\b',p.question) and has(r'\bproduce[sd]?\b',text)):
        return None
    if len(ns) == 2:
        if denom != 'day':
            return None
        months = [i for i,w in enumerate(_MONTHS) if has(r'\bin '+w+r'\b',p.question)]
        if len(months) != 1 or months[0] == 1:
            return None  # February needs the year.
        periods = Fraction((31,28,31,30,31,30,31,31,30,31,30,31)[months[0]])
    else:
        c,d = ns[2:]
        if denom != 'hour' or noun(text[c.end:]) != 'day' or noun(text[d.end:]) != 'hour':
            return None
        if not has(r'^\s+hours? a day\b',text[d.end:]):
            return None
        periods = c.value*d.value
    return answer((2*base.value+diff.value)*periods,
                  '(2 x {} + {}) x {}'.format(*map(format_number,(base.value,diff.value,periods))))


def _transfer_then_ratio(p):
    """A transfer precedes a ratio; recover the recipient's initial stock."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 3 or not has(r'\b(?:at first|initially|originally)\b',p.question):
        return None
    a,b,k = ns
    first = re.search(r'\b([a-z]+) had\s*$',text[:a.start])
    recipient = re.match(r'\s+of them to ([a-z]+)\.',text[b.end:])
    relation = re.match(r'\s+times (?:more|as many) [a-z ]+?than ([a-z]+)\.',text[k.end:])
    if not first or not recipient or not relation or recipient.group(1) != relation.group(1):
        return None
    if not has(r'\bgave\s*$',text[a.end:b.start]) or not has(r'\bnow '+first.group(1)+r' has\s*$',text[b.end:k.start]):
        return None
    if not has(r'\b'+recipient.group(1)+r'\b',p.question) or asked(p) != noun(text[a.end:]) or k.value <= 0:
        return None
    return answer((a.value-b.value)/k.value-b.value,
                  '({0} - {1}) / {2} - {1}'.format(*map(format_number,(a.value,b.value,k.value))))


def _multiple_comparative_total(p):
    """A multiple of two inventories, one stated as a difference from the other."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 3 or any(n.start >= len(p.body) for n in ns):
        return None
    diff,base,k = ns
    if not has(r'^\s+more [a-z ]+? than\b',text[diff.end:base.start]):
        return None
    if not has(r'\bwho has\s*$',text[diff.end:base.start]):
        return None
    if not has(r'^\s+times the number of\b[^.;!?]*\bboth\b',text[k.end:len(p.body)]):
        return None
    if noun(text[diff.end:]) != noun(text[base.end:]) or asked(p) != noun(text[base.end:]):
        return None
    return answer((diff.value+2*base.value)*k.value,
                  '({} + 2 x {}) x {}'.format(*map(format_number,(diff.value,base.value,k.value))))


def _two_owner_average(p):
    """An average of two owners' totals with a shared contextual group count."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 5 or not has(r'\baverage number of\b',p.question):
        return None
    base,n,diff,n2,two = ns
    if two.start < len(p.body) or two.value != 2 or n.value != n2.value:
        return None
    if not has(r'\bthe same\s*$',text[diff.end:n2.start]):
        return None
    if noun(text[n.end:]) != noun(text[n2.end:]):
        return None
    unit = noun(text[base.end:])
    if noun(text[diff.end:]) != unit or not has(r'\baverage number of '+re.escape(unit)+r's?\b',p.question):
        return None
    m = re.match(r'\s+(fewer|more)\b',text[diff.end:])
    if not m:
        return None
    other = base.value+diff.value*(1 if m.group(1) == 'more' else -1)
    if other < 0:
        return None
    return answer((base.value+other)/2,'({} + {}) / 2'.format(format_number(base.value),format_number(other)))


def _container_detail(p):
    """One outer container followed by a complete inventory of inner groups."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 5 or ns[0].value != 1:
        return None
    if not has(r'\bbought\s*$',text[:ns[0].start]):
        return None
    if not has(r'\bthere are\s*$',text[ns[0].end:ns[1].start]):
        return None
    if not has(r'^\s+(?:[a-z]+\s+){0,3}[a-z]+ of\b',text[ns[0].end:]):
        return None
    from ..problem import Problem
    # The descriptive opening is excluded only after recognizing its scope.
    remainder = text[ns[1].start:]
    updated = Problem.read('There are '+remainder)
    return _group_ledger(updated) if updated else None


def _neither_category(p):
    """Complement of the union of two explicitly overlapping categories."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 4 or any(n.start >= len(p.body) for n in ns):
        return None
    q = re.search(r'\bneither ([a-z]+) nor ([a-z]+)\b',p.question)
    overlap = re.search(r'\bboth ([a-z]+) and ([a-z]+)\b',text[ns[-1].end:len(p.body)])
    if not q or not overlap or set(q.groups()) != set(overlap.groups()):
        return None
    if not has(r'\b(?:out of|total|has|have|there are)\b',text[:ns[0].start]):
        return None
    identified = []
    for n in ns[1:3]:
        tail = re.split(r'[.;,]',text[n.end:])[0]
        labels = [label for label in q.groups() if has(r'\b'+re.escape(label)+r'\b',tail)]
        if len(labels) != 1:
            return None
        identified.extend(labels)
    if set(identified) != set(q.groups()):
        return None
    a,b,c,d = (n.value for n in ns)
    if not 0 <= d <= min(b,c) or max(b,c) > a:
        return None
    return answer(a-b-c+d,'{} - {} - {} + {}'.format(*map(format_number,(a,b,c,d))))


def _measured_group_sum(p):
    """Two groups, each yielding/measuring an explicit measured amount."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 4 or any(n.start >= len(p.body) for n in ns):
        return None
    if has(r'\b(?:more|less|than|remaining|left|half|twice|percent)\b',text):
        return None
    unit = noun(text[ns[1].end:])
    if unit != noun(text[ns[3].end:]) or unit not in ('foot','meter','inch','kg','kilogram','gram','pound','ounce','liter'):
        return None
    measure_query = has(r'\btotal (?:mass|weight|length|volume)\b',p.question)
    if asked(p) != unit and not measure_query:
        return None
    for i in (1,3):
        middle = text[ns[i-1].end:ns[i].start]
        if not has(r'\bthat (?:each )?(?:measure|measures|give|gives|produce|produces)\s+(?:an average of\s+)?$',middle):
            return None
    a,b,c,d = (n.value for n in ns)
    return answer(a*b+c*d,'{} x {} + {} x {}'.format(*map(format_number,(a,b,c,d))))


def _per_person_list(p):
    """Named participants each consume every category in an explicit list."""
    ns, text = p.numbers, p.text.lower()
    if not 3 <= len(ns) <= 7 or not has(r'\btotal\b',p.question):
        return None
    before = text[:ns[0].start]
    m = re.search(r'^([a-z]+) and ([a-z]+) each (?:eat|consume|buy|bought|have|need)\s*$',before)
    if not m:
        return None
    count = ns[-1]
    if count.start < len(p.body) or count.value != 2:
        return None
    if has(r'\b(?:more|less|than|left|remaining|half|twice)\b',p.body):
        return None
    for n in ns[:-1]:
        u = noun(text[n.end:])
        if not u or not has(r'\b'+re.escape(u)+r'(?:s|es)?\b',p.question):
            return None
    vals = [n.value for n in ns[:-1]]
    return answer(total(vals)*2,'('+expression(vals)+') x 2')


def _average_multiple(p):
    """An explicit multiple of a stated group's arithmetic mean."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) < 4 or not has(r'\btimes (?:higher|as high|as much|larger|as many)\b[^.;!?]*\baverage\b',p.body):
        return None
    factor = ns[0]
    if factor.start >= len(p.body):
        return None
    # Repeated group-size references must agree with the measurements listed.
    measures = []
    labels = []
    for n in ns[1:]:
        tail = text[n.end:]
        if noun(tail) in ('inch','foot','meter','point','kilogram','pound','second','minute'):
            measures.append(n)
        else:
            labels.append(n)
    if not measures or not labels or any(n.value != len(measures) for n in labels):
        return None
    label_units = {noun(text[n.end:]) for n in labels}
    if len(label_units) != 1 or label_units & {'year','month','day','hour','minute','second'}:
        return None
    units = {noun(text[n.end:]) for n in measures}
    if len(units) != 1 or not has(r'^how (?:high|many|much|long)\b',p.question):
        return None
    vals = [n.value for n in measures]
    return answer(total(vals)/len(vals)*factor.value,
                  '('+expression(vals)+') / '+str(len(vals))+' x '+format_number(factor.value))


def _daily_pace_sum(p):
    """Several stated distances, then an explicit distance/time pace."""
    ns, text = p.numbers, p.text.lower()
    if not 4 <= len(ns) <= 10 or any(n.start >= len(p.body) for n in ns):
        return None
    a,b = ns[-2:]
    if not has(r'\bat a pace of\s*$',text[:a.start]):
        return None
    if not has(r'\bin\s*$',text[a.end:b.start]) or a.value <= 0:
        return None
    unit = noun(text[a.end:])
    if not unit or any(noun(text[n.end:]) != unit for n in ns[:-2]):
        return None
    requested = re.search(r'\btotal number of (hours?|minutes?|seconds?)\b',p.question)
    if not requested:
        return None
    pace = _convert(b.value,noun(text[b.end:]),_singular(requested.group(1)))
    if pace is None:
        return None
    vals = [n.value for n in ns[:-2]]
    return answer(total(vals)/a.value*pace,
                  '('+expression(vals)+') / '+format_number(a.value)+' x '+format_number(pace))


def _converted_comparison_sum(p):
    """Two people's durations combined, compared to a third person's time."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 3 or not has(r'^how many (?:minutes|seconds|hours) more\b',p.question):
        return None
    q = re.search(r'\b([a-z]+) and ([a-z]+) [a-z ]+ than ([a-z]+)\b',p.question)
    if not q:
        return None
    dest = _singular(p.question.split()[2])
    owners, values = [], []
    for n in ns:
        before = re.split(r'[.!?;]|\band\b',text[:n.start])[-1]
        owner = re.search(r'^\s*([a-z]+) (?:studied|worked|practiced|trained)\b',before)
        converted = _convert(n.value,noun(text[n.end:]),dest)
        if not owner or converted is None:
            return None
        owners.append(owner.group(1)); values.append(converted)
    if set(owners) != set(q.groups()):
        return None
    by_owner = dict(zip(owners,values))
    left,right,other = q.groups()
    return answer(by_owner[left]+by_owner[right]-by_owner[other],
                  '{} + {} - {}'.format(*map(format_number,(by_owner[left],by_owner[right],by_owner[other]))))


def _custom_unit_capacity(p):
    """A capacity, occupied amount, and per-item size with explicit conversion."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 4 or not has(r'\balready using\b',p.body):
        return None
    cap,used,size,conv = ns
    if not has(r'\b(?:can|could)\b.*\bstore\b',p.question):
        return None
    unit = re.match(r'\s*([a-z]+)\b',text[cap.end:])
    if not unit or not has(r'^\s*'+re.escape(unit.group(1))+r'\b',text[used.end:]):
        return None
    small = re.match(r'\s*([a-z]+)\b',text[size.end:])
    if not small or not has(r'^\s*'+small.group(1)+r' in (?:a|an|one) '+unit.group(1)+r'\b',text[conv.end:]):
        return None
    item = re.search(r'\b(?:a|an) ([a-z]+) takes up (?:about )?$',text[:size.start])
    if not item or asked(p) != item.group(1) or size.value <= 0:
        return None
    quotient = (cap.value-used.value)*conv.value/size.value
    if quotient < 0:
        return None
    return answer(Fraction(quotient.numerator//quotient.denominator),
                  '({} - {}) x {} / {}'.format(*map(format_number,(cap.value,used.value,conv.value,size.value))))


def _stock_rate_then_requirement(p):
    """Daily production minus a removal, scaled by a per-item requirement."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 4 or any(n.start >= len(p.body) for n in ns):
        return None
    a,days,removed,rate = ns
    if not has(r'\b(?:every day|each day|per day)\b',text[:days.start]):
        return None
    if noun(text[days.end:]) != 'day' or not has(r'\bfor\s*$',text[a.end:days.start]):
        return None
    unit = noun(text[a.end:])
    if noun(text[removed.end:]) != unit or not has(r'\b(?:eats?|ate|lost|sold|used)\s*$',text[days.end:removed.start]):
        return None
    if not has(r'\b(?:remaining|left)\b',p.question) or asked(p) != noun(text[rate.end:]):
        return None
    if not has(r'\b(?:a single|each|one) '+re.escape(unit)+r'\b',text[rate.end:len(p.body)]):
        return None
    rest = a.value*days.value-removed.value
    if rest < 0:
        return None
    return answer(rest*rate.value,'({} x {} - {}) x {}'.format(*map(format_number,(a.value,days.value,removed.value,rate.value))))


def _list_task_time(p):
    """A list of task counts, each taking a stated common duration."""
    ns, text = p.numbers, p.text.lower()
    if not 3 <= len(ns) <= 8 or any(n.start >= len(p.body) for n in ns):
        return None
    duration = ns[-1]
    if not has(r'\beverything\b[^.;!?]*\btakes\s*$',text[:duration.start]):
        return None
    unit = noun(text[ns[0].end:])
    if not unit or any(noun(text[n.end:]) != unit for n in ns[:-1]):
        return None
    dest = asked(p)
    rate = _convert(duration.value,noun(text[duration.end:]),dest)
    if rate is None or dest not in ('hour','minute','second'):
        return None
    vals = [n.value for n in ns[:-1]]
    return answer(total(vals)*rate,'('+expression(vals)+') x '+format_number(rate))


def _tare_rate_stock(p):
    """Empty container mass plus several daily portions minus consumption."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 4 or any(n.start >= len(p.body) for n in ns[:3]):
        return None
    tare,rate,days,removed = ns
    unit = noun(text[tare.end:])
    if unit not in ('gram','kilogram','pound','ounce'):
        return None
    if not has(r'\bempty\b[^.;!?]*\bweighs\s*$',text[:tare.start]):
        return None
    if not has(r'^\s+'+unit+r's? per day\b',text[rate.end:]) or not has(r'\bevery\s*$',text[rate.end:days.start]):
        return None
    if noun(text[days.end:]) != 'day' or noun(text[removed.end:]) != unit:
        return None
    if not has(r'\bate\s*$',text[days.end:removed.start]) or not has(r'\bweigh\b',p.question):
        return None
    return answer(tare.value+rate.value*days.value-removed.value,
                  '{} + {} x {} - {}'.format(*map(format_number,(tare.value,rate.value,days.value,removed.value))))


def _recipe_sum(p):
    """One explicit input/output proportion, followed by disjoint outputs."""
    ns, text = p.numbers, p.text.lower()
    if not 4 <= len(ns) <= 10:
        return None
    a,b = ns[:2]
    input_unit,output_unit = noun(text[a.end:]),noun(text[b.end:])
    if not input_unit or input_unit == output_unit or asked(p) != input_unit or b.value <= 0:
        return None
    if not has(r'\b(?:will make|makes?|produces?|yields?)\s*$',text[a.end:b.start]):
        return None
    if has(r'\b(?:more|less|than|left|remaining|half|twice|each|per)\b',text[b.end:]):
        return None
    for n in ns[2:]:
        if noun(text[n.end:]) != output_unit:
            return None
    vals = [n.value for n in ns[2:]]
    return answer(total(vals)*a.value/b.value,
                  '('+expression(vals)+') x '+format_number(a.value)+' / '+format_number(b.value))


_LENGTH = {'inch': Fraction(1), 'foot': Fraction(12), 'yard': Fraction(36),
           'centimeter': Fraction(1), 'meter': Fraction(100), 'kilometer': Fraction(100000)}


def _length_convert(value,source,dest):
    if source not in _LENGTH or dest not in _LENGTH:
        return None
    imperial = {'inch','foot','yard'}
    if (source in imperial) != (dest in imperial):
        return None
    return value*_LENGTH[source]/_LENGTH[dest]


def _converted_requirement(p):
    """An explicit per-item length, a required item count and current stock."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 4 or ns[0].value != 1:
        return None
    one,rate,count,stock = ns
    if not has(r'^\s+[a-z]+ requires\s*$',text[one.end:rate.start]):
        return None
    if noun(text[one.end:]) != noun(text[count.end:]):
        return None
    dest = asked(p)
    per = _length_convert(rate.value,noun(text[rate.end:]),dest)
    have = _length_convert(stock.value,noun(text[stock.end:]),dest)
    if per is None or have is None or not has(r'\b(?:still need|more|additional)\b',p.question):
        return None
    return answer(per*count.value-have,'{} x {} - {}'.format(*map(format_number,(per,count.value,have))))


def _mixed_height_difference(p):
    """Two heights explicitly written in feet and inches."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 4 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'^how many inches (?:taller|shorter)\b',p.question):
        return None
    if [noun(text[n.end:]) for n in ns] != ['foot','inch','foot','inch']:
        return None
    for i in (0,2):
        if not re.fullmatch(r'\s+feet,?\s*',text[ns[i].end:ns[i+1].start]):
            return None
    a,b,c,d = (n.value for n in ns)
    return answer(abs(12*a+b-12*c-d),
                  '|(12 x {} + {}) - (12 x {} + {})|'.format(*map(format_number,(a,b,c,d))))


def _missing_comparison_part(p):
    """A total contains two linked known parts and one requested unknown."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) not in (3,4) or any(n.start >= len(p.body) for n in ns):
        return None
    diffs = [i for i,n in enumerate(ns) if re.match(r'\s+(?:more|fewer|less)\b',text[n.end:])]
    if len(diffs) != 1:
        return None
    di = diffs[0]
    totals = []
    for i,n in enumerate(ns):
        before = text[ns[i-1].end if i else 0:n.start]
        tail = text[n.end:ns[i+1].start if i+1 < len(ns) else len(p.body)]
        if i != di and (has(r'\b(?:altogether|in total|in all)\b',tail)
                        or has(r'\b(?:total|combined)\b[^.;!?]*$',before)):
            totals.append(i)
    # An explicit count of three named containers, with a stated whole.
    if len(ns) == 4 and ns[0].value == 3 and di > 1:
        if has(r'\blabeled\b[^.;!?]*\bwith\s*$',text[ns[0].end:ns[1].start]):
            totals.append(1)
    if len(set(totals)) != 1:
        return None
    ti = totals[0]
    remaining = [i for i in range(len(ns)) if i not in (di,ti)]
    if len(remaining) == 2:
        if remaining[0] != 0 or ns[0].value != 3:
            return None
        remaining.pop(0)
    bi = remaining[0]
    unit = noun(text[ns[bi].end:])
    if not unit or noun(text[ns[di].end:]) != unit or noun(text[ns[ti].end:]) != unit:
        return None
    if asked(p) and asked(p) != unit:
        return None
    if not has(r'\bthan\b',text[ns[di].end:ns[di+1].start if di+1<len(ns) else len(p.body)]):
        return None
    sign = 1 if re.match(r'\s+more\b',text[ns[di].end:]) else -1
    a,b,d = ns[ti].value,ns[bi].value,sign*ns[di].value
    return answer(a-2*b-d,'{} - ({} + ({} + {}))'.format(*map(format_number,(a,b,b,d))))


def _fraction_after_partition(p):
    """Remove a known category, then complement a fraction of what remains."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 3 or any(n.start >= len(p.body) for n in ns):
        return None
    whole,part,fraction = ns
    if not 0 < fraction.value < 1 or whole.value < part.value or part.value < 1:
        return None
    after = text[fraction.end:len(p.body)]
    rest = re.search(r'\b(?:the )?rest (?:are|have|has) ([a-z]+(?: [a-z]+)?)',after)
    if not rest or not all(has(r'\b'+re.escape(w)+r'\b',p.question) for w in rest.group(1).split()):
        return None
    if not has(r'^\s+of (?:the )?(?:remaining|[a-z]+)\b',after):
        return None
    earlier = text[part.end:fraction.start]
    if not has(r'\b(?:rest|remaining)\b',earlier+after[:after.find('rest')]):
        return None
    return answer((whole.value-part.value)*(1-fraction.value),
                  '({} - {}) x (1 - {})'.format(*map(format_number,(whole.value,part.value,fraction.value))))


def _partition_then_equal_groups(p):
    """Divide a remaining category equally, then compare to a known category."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 4 or not has(r'\bremaining\b[^.;!?]*\bequally into\s*$',text[:ns[-1].start]):
        return None
    whole,a,b,groups = ns
    if not has(r'\bdifference between\b',p.question) or groups.value <= 0:
        return None
    tail = text[groups.end:len(p.body)]
    if not has(r'^\s+groups\b',tail):
        return None
    qlabels = re.search(r'\bbetween (?:the )?(?:number of )?([a-z]+) and ([a-z]+)\b',p.question)
    if not qlabels:
        return None
    known = []
    for n in (a,b):
        label = re.match(r'\s+[a-z]+ ([a-z]+)\b',text[n.end:])
        if label and label.group(1) in qlabels.groups():
            known.append(n.value)
    if len(known) != 1:
        return None
    # The other query label must be one of the explicitly listed new groups.
    new_labels = re.search(r'\b(?:painted|colored|labelled|labeled) them (.+)',tail)
    if not new_labels or not any(has(r'\b'+w+r'\b',new_labels.group(1)) for w in qlabels.groups()):
        return None
    rest = whole.value-a.value-b.value
    if rest < 0:
        return None
    each = rest/groups.value
    return answer(abs(known[0]-each),
                  '|{} - ({} - {} - {}) / {}|'.format(*map(format_number,(known[0],whole.value,a.value,b.value,groups.value))))


def _larger_goal_after_score(p):
    """A competitor's future score plus a desired margin minus one's score."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 4 or not has(r'\bbeat\b[^.;!?]*\bby at least\s*$',text[:ns[2].start]):
        return None
    a,b,margin,extra = ns
    if extra.start < len(p.body) or not has(r'\bscores? another\s*$',text[:extra.start]):
        return None
    if not has(r'^how many more times\b',p.question):
        return None
    if not all(has(r'^\s+times\b',text[n.end:]) for n in (a,b,extra)):
        return None
    return answer(b.value+extra.value+margin.value-a.value,
                  '{} + {} + {} - {}'.format(*map(format_number,(b.value,extra.value,margin.value,a.value))))


def _meal_repetitions(p):
    """An activity after an explicit list of daily meals, over several days."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 2 or ns[-1].start > len(p.body):
        return None
    a,days = ns
    m = re.match(r'\s+(minutes?|seconds?|hours?) after ([a-z]+(?:\s*,\s*| and )[a-z ,]+)\.',text[a.end:days.start])
    if not m or noun(text[days.end:]) != 'day':
        return None
    # These are named daily occasions, rather than arbitrary counted nouns.
    occasions = re.findall(r'\b(?:breakfast|lunch|dinner|supper)\b',m.group(2))
    remaining = re.sub(r'\b(?:breakfast|lunch|dinner|supper|and)\b|[,\s]','',m.group(2))
    if remaining or not occasions or len(set(occasions)) != len(occasions):
        return None
    duration = _convert(a.value,_singular(m.group(1)),asked(p))
    if duration is None:
        return None
    return answer(duration*len(occasions)*days.value,
                  expression((duration,Fraction(len(occasions)),days.value),' x '))


def _category_comparison_chain(p):
    """Resolve qualified categories linked by additive differences."""
    ns, text = p.numbers, p.text.lower()
    if not 3 <= len(ns) <= 7 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\btotal\b',p.question) or has(r'\b(?:times|each|per|half|twice|percent)\b',p.body):
        return None
    unit = asked(p)
    if not unit:
        return None
    counts, pending = {}, []
    for n in ns:
        tail = text[n.end:]
        relation = re.match(r'\s+(more|less|fewer) ([a-z]+) ([a-z]+) than there are ([a-z]+) ([a-z]+)',tail)
        if relation:
            op,label,u,ref,v = relation.groups()
            if _singular(u) != unit or _singular(v) != unit:
                return None
            pending.append((label,ref,n.value*(1 if op == 'more' else -1)))
        else:
            base = re.match(r'\s+([a-z]+) ([a-z]+)\b',tail)
            if not base or _singular(base.group(2)) != unit or base.group(1) in counts:
                return None
            counts[base.group(1)] = n.value
    if not pending:
        return None
    original = len(counts)
    for unused in range(len(pending)):
        for label,ref,diff in pending:
            if ref in counts:
                counts[label] = counts[ref]+diff
    if len(counts) != original+len(pending) or min(counts.values()) < 0:
        return None
    return answer(total(counts.values()),expression(counts.values()))


def _two_category_unfinished(p):
    """Two inventories minus work already done on each category."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 4 or any(n.start >= len(p.body) for n in ns):
        return None
    if not has(r'\bremaining pieces of\b',p.question):
        return None
    units = [noun(text[n.end:]) for n in ns]
    if units[0] != units[2] or units[1] != units[3] or not all(units):
        return None
    before = text[ns[1].end:ns[2].start]
    action = re.search(r'\b(fold|pack|wrap|label|paint)s?\s*$',before)
    if not action or not has(r'\bto '+action.group(1)+r'\b',p.question):
        return None
    if ns[2].value > ns[0].value or ns[3].value > ns[1].value:
        return None
    a,b,c,d = (n.value for n in ns)
    return answer(a+b-c-d,'{} + {} - {} - {}'.format(*map(format_number,(a,b,c,d))))


def _diameter_segments(p):
    """Count equal length objects across a circle's diameter, with conversion."""
    ns, text = p.numbers, p.text.lower()
    if len(ns) != 2 or not has(r'\bcircle\b',p.body):
        return None
    radius,size = ns
    if radius.start >= len(p.body) or size.start < len(p.body):
        return None
    if not has(r'\bradius of\s*$',text[:radius.start]):
        return None
    if not has(r'\bend[ -]to[ -]end\b',p.question) or not has(r'\bacross the diameter\b',p.question):
        return None
    source = noun(text[radius.end:])
    length = _length_convert(size.value,noun(text[size.end:]),source)
    if length is None or length <= 0:
        return None
    count = 2*radius.value/length
    if count.denominator != 1:
        return None  # Rounding a fit requires another explicit assumption.
    return answer(count,'2 x {} / {}'.format(format_number(radius.value),format_number(length)))


def solve(problem):
    if any(n.kind == 'percent' for n in problem.numbers):
        return None
    for reader in (_group_ledger, _session_durations, _active_daily_duration,
                   _interval_output, _weekly_extra, _fraction_left,
                   _relative_repeated_group, _monthly_growth, _weekday_categories,
                   _invited_companions, _block_array, _return_trip_times,
                   _inverse_category_sum, _priced_categories, _dozen_ledger,
                   _named_comparison_chain, _parallel_interval_rates,
                   _shared_contents, _cycle_count, _speed_difference,
                   _opposite_motion, _money_shortfall, _relative_daily_output,
                   _transfer_then_ratio, _multiple_comparative_total,
                   _two_owner_average, _container_detail, _neither_category,
                   _measured_group_sum, _per_person_list, _average_multiple,
                   _daily_pace_sum, _converted_comparison_sum,
                   _custom_unit_capacity, _stock_rate_then_requirement,
                   _list_task_time, _tare_rate_stock, _recipe_sum,
                   _converted_requirement, _mixed_height_difference,
                   _missing_comparison_part, _fraction_after_partition,
                   _partition_then_equal_groups, _larger_goal_after_score,
                   _meal_repetitions, _category_comparison_chain,
                   _two_category_unfinished, _diameter_segments):
        result = reader(problem)
        if result is not None:
            return result
    return None
