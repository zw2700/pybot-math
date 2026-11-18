"""Small, explicitly scoped fraction compositions.

Readers identify a whole, the base of each share, and the requested category.
Unexplained numbers and ambiguous scopes cause abstention. Arithmetic stays exact.
"""
import re
from dataclasses import replace
from fractions import Fraction

from ..numbers import read_numbers, format_number
from ..problem import Problem, ASK
from ._fractions_common import has_fraction, _answer, _has
from .counting_and_totals_r00_a1 import _singular
from .fractions_of_a_quantity_r03_a3 import _words, _label, _choice, _share
from .fractions_of_a_quantity_r03_a2 import _comparisons, _prepare as _graph_prepare
from .fractions_of_a_quantity_r11_a4 import _prepare, _fractions, _relations
from .comparisons_r01_a2 import _equation_graph


_TIME = {'second': Fraction(1), 'minute': Fraction(60),
         'hour': Fraction(3600), 'day': Fraction(86400)}


def _tail(p, n):
    return p.text[n.end:].lower()


def _clause(text):
    return re.split(r'[.;!?]|,(?!\d)', text)[0]


def _anaphoric_time(p, fs):
    if len(fs) != 1 or len(p.numbers) != 2:
        return None
    f = fs[0]
    amount = next(n for n in p.numbers if n != f)
    if amount.start > f.start or not re.match(r'\s+of that (?:time|amount of time)\b', _tail(p, f)):
        return None
    unit = re.match(r'\s+(minutes?|hours?|seconds?|days?)\b', _tail(p, amount))
    if not unit or not _has(r'\b'+_singular(unit.group(1))+r's?\b', p.question):
        return None
    if not _has(r'\b(?:total|altogether|in all)\b', p.question):
        return None
    return _answer(amount.value*(1+f.value), 'Original time plus the fractional additional time')


def _rest_categories(p, fs):
    """Whole minus counted categories, then a share of the explicit rest."""
    if len(fs) != 1 or not 3 <= len(p.numbers) <= 5:
        return None
    f = fs[0]
    amounts = [n for n in p.numbers if n != f]
    if any(n.start > f.start for n in amounts):
        return None
    before = re.split(r'[.;!?]', p.text[:f.start].lower())[-1]
    if not _has(r'\b(?:from|of|among) (?:the )?(?:rest|remaining)\b', before):
        return None
    if not re.match(r'\s+of (?:them|those|these)\b', _tail(p, f)):
        return None
    if _has(r'\b(?:per|each|times|more|less|twice)\b', p.text.lower()):
        return None
    total = amounts[0]
    unit = re.match(r'\s+(?:(?:different|total) )?([a-z]+)', _tail(p, total))
    if not unit or _singular(unit.group(1)) not in _words(p.question):
        return None
    # Later counts must explicitly refer to members of that whole.
    if not all(re.match(r'\s+of (?:them|those|these)\b|\s+in\b', _tail(p, n)) for n in amounts[1:]):
        return None
    predicate = re.search(r'\b(?:are|were|is|was)\s+(.+)', _clause(_tail(p, f)))
    if not predicate or not _words(predicate.group(1)) & _words(p.question):
        return None
    return _answer((total.value-sum((n.value for n in amounts[1:]), Fraction(0)))*f.value,
                   'Remove the counted categories, then take the stated share of the rest')


def _related_remainder(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    f = fs[0]
    part, total = [n for n in p.numbers if n != f]
    if not part.start < f.start < total.start:
        return None
    if not re.match(r'\s+as many\b', _tail(p, f)):
        return None
    rest = re.search(r'\bthe rest (?:are|is|were) ([^.;!?]+)', p.body)
    if not rest or not _words(rest.group(1)) & _words(p.question):
        return None
    if _has(r'\b(?:per|each|more|less|than|twice)\b', p.text.lower()):
        return None
    # The later whole must repeat the counted stock noun.
    part_words = _words(_clause(_tail(p, part)))
    unit = re.match(r'\s+([a-z]+)', _tail(p, total))
    if not unit or _singular(unit.group(1)) not in part_words:
        return None
    return _answer(total.value-part.value*(1+f.value), 'Whole minus the counted part and its proportional companion')


def _listed_categories(p, fs):
    """A count of named categories is metadata, verified against the list."""
    if len(fs) != 2 or len(p.numbers) != 4:
        return None
    count = p.numbers[0]
    if count in fs or count.start > fs[0].start:
        return None
    listing = re.match(r'\s+(?:[a-z]+\s+){0,3}?(?:colors|colours|types|kinds|categories)\b[^:.;]*:\s*([^.;]+)', _tail(p, count))
    if not listing:
        return None
    labels = [s.strip() for s in re.split(r',\s*(?:and\s+)?|\s+and\s+', listing.group(1)) if s.strip()]
    if count.value != len(labels) or any(not re.fullmatch(r'[a-z]+(?: [a-z]+){0,2}', s) for s in labels):
        return None
    q = replace(p, text=p.text.lower(), numbers=p.numbers[1:])
    return _share(q, fs)


def _inverse_cash(p, fs):
    """Invert an affine cash ledger; additional fixed spending follows its share."""
    if not fs or not _has(r'\b(?:at first|originally|initially|start with|begin with)\b', p.question):
        return None
    amounts = [n for n in p.numbers if n not in fs]
    if not amounts or not all(n.kind == 'money' for n in amounts):
        return None
    if _has(r'\b(?:per|each|times|more|less|as much|as many)\b', p.text.lower()):
        return None
    final = amounts[-1]
    text = p.text.lower()
    if final.start < fs[-1].end or not _has(r'\b(?:left|remaining)\b', _clause(text[max(0, text.rfind('.',0,final.start)+1):])):
        return None
    if any(n.start >= len(p.body) for n in p.numbers):
        return None
    first_owner = re.search(r'\b([a-z]+) (?:spent|spends?|used|uses?|gave|gives?|donated)\b',text[:fs[0].start])
    final_owner = re.search(r'\b([a-z]+) (?:was|is|has|had) (?:left with )?\s*$',text[:final.start])
    if final_owner and final_owner.group(1) not in ('he','she','they'):
        if not first_owner or final_owner.group(1) != first_owner.group(1):
            return None
    a, b = Fraction(1), Fraction(0)
    previous = 0
    for n in p.numbers:
        if n == final:
            continue
        before = text[previous:n.start]
        after = text[n.end:]
        if n in fs:
            if not _has(r'\b(?:spent|spends?|used|uses?|gave|gives?|donated)\b', before):
                return None
            if not re.match(r'\s+of (?:his|her|their|the) (?:remaining )?money\b', after):
                return None
            if n != fs[0] and not _has(r'^\s+of (?:the |his |her |their )?remaining\b', after):
                return None
            a, b = a*(1-n.value), b*(1-n.value)
        else:
            if not (_has(r'\b(?:spent|spends?|used|uses?|gave|gives?|donated)\b', before)
                    or _has(r'\band (?:an? )?(?:additional|another|extra)\s*$', before)):
                return None
            b -= n.value
        previous = n.end
    if a <= 0:
        return None
    value = (final.value-b)/a
    return _answer(value, 'Undo the fractional and fixed spending; original money in dollars: '+format_number(value))


def _comparison_language(problem, p, fs):
    """Normalize equivalent measure phrases for the existing relation graph."""
    text = p.text
    text = re.sub(r'\btimes that (?:size|weight|height)\b', 'times that amount', text, flags=re.I)
    text = re.sub(r'\b(?:the )?size of\b', 'the length of', text, flags=re.I)
    # A possessive object can be the subject of a measurement anchor.
    text = re.sub(r"\b([A-Z][a-z]+)'s (?:[a-z]+\s+){1,3}?(?:weighs|measures)\b", r'\1 has', text)
    if text == p.text:
        return None
    q = Problem.read(text)
    if q is None:
        return None
    return _comparisons(_graph_prepare(q)) or _relations(_prepare(q), _fractions(_prepare(q)))


def _named_subset(problem, p, fs):
    """Resolve an owner's whole from comparisons, then select its category."""
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    f = fs[0]
    text = p.text
    tail = re.match(r"\s+of ([A-Za-z]+)'s ([a-z]+) (?:are|were|is|was) ([^.;!?]+)", text[f.end:])
    if not tail or not _words(tail.group(3)) & _words(p.question):
        return None
    start = text.rfind('.', 0, f.start)+1
    if text[start:f.start].strip():
        return None
    if any(n.start >= f.end for n in p.numbers if n != f):
        return None
    owner, stock = tail.group(1), tail.group(2)
    if not _has(r'\b'+re.escape(owner.lower())+r'\b', p.question):
        return None
    q = Problem.read(text[:start]+' How many '+stock+' does '+owner+' have?')
    if q is None:
        return None
    values = _comparisons(_graph_prepare(q), return_values=True)
    if not isinstance(values, dict) or owner.lower() not in values:
        return None
    return _answer(values[owner.lower()]*f.value, 'Resolve the owner\'s whole, then take the requested category share')


def _rate_volume(p, fs):
    """Events per time x fractional volume per event x a measured duration."""
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    f = fs[0]
    rate, duration = [n for n in p.numbers if n != f]
    if not rate.start < f.start < duration.start:
        return None
    event_rate = re.match(r'\s+([a-z]+) per (second|minute|hour)\b', _tail(p, rate))
    measure = re.match(r'\s+(?:of (?:an? )?)?(liters?|litres?|milliliters?|ounces?|grams?)\b', _tail(p, f))
    elapsed = re.match(r'\s+(seconds?|minutes?|hours?)\b', _tail(p, duration))
    if not event_rate or not measure or not elapsed:
        return None
    if not _has(r'\b(?:volume|amount|'+_singular(measure.group(1))+r's?)\b', p.question):
        return None
    # A verb linking an event to its volume is required, not two unrelated rates.
    if not _has(r'\b(?:by|each|every)\b', p.text[rate.end:f.start].lower()):
        return None
    if not _has(r'\b(?:in|over|for)\s*$', p.text[:duration.start].lower()):
        return None
    seconds = {'second': Fraction(1), 'minute': Fraction(60), 'hour': Fraction(3600)}
    factor = seconds[_singular(elapsed.group(1))]/seconds[event_rate.group(2)]
    return _answer(rate.value*f.value*duration.value*factor, 'Events per period x volume per event x duration in matching periods')


def _package_measure(p, fs):
    """Counted equal weights plus packaging, priced or stamped per unit weight."""
    if len(fs) != 2 or len(p.numbers) != 4:
        return None
    count, first, second, rate = p.numbers
    if fs != [first, second] or count.value.denominator != 1:
        return None
    text = p.text.lower()
    units = [re.match(r'\s+(?:of (?:an? )?)?(ounce|pound|gram|kilogram|liter|litre)s?\b', _tail(p,n)) for n in fs]
    if not all(units) or units[0].group(1) != units[1].group(1):
        return None
    if not _has(r'\b(?:weigh|weighs|weighing)\s*$', text[:first.start]) or not _has(r'\beach\b', text[first.end:second.start]):
        return None
    if not _has(r'\b(?:weigh|weighs|weighing)\s*$', text[:second.start]):
        return None
    per = re.match(r'\s+([a-z]+) per '+units[0].group(1)+r'\b', _tail(p,rate))
    if not per or _singular(per.group(1)) not in _words(p.question):
        return None
    return _answer((count.value*first.value+second.value)*rate.value, 'Combined contents and package weight x required count per weight unit')


def _enumerated_split(p, fs):
    if len(fs) != 2 or len(p.numbers) != 3 or fs[0].value+fs[1].value != 1:
        return None
    base = next(n for n in p.numbers if n not in fs)
    if base.start > fs[0].start:
        return None
    if not _has(r'\bthe other\s*$', p.text[:fs[1].start].lower()):
        return None
    split = re.match(r'\s+(?:are|is) (?:split|divided|shared) (?:evenly|equally) (?:between|among) ([^.;!?]+)', _tail(p,fs[1]))
    if not split:
        return None
    labels = re.split(r',\s*(?:and\s+)?|\s+and\s+', split.group(1))
    if len(labels) < 2 or not all(re.fullmatch(r'[a-z]+(?: [a-z]+){0,2}', s.strip()) for s in labels):
        return None
    selected = [s for s in labels if _words(s) & _words(p.question)]
    if len(selected) != 1:
        return None
    return _answer(base.value*fs[1].value/len(labels), 'Whole x share assigned to the equal groups / number of groups')


def _inverse_category_ratio(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    f = fs[0]
    ratio, part = [n for n in p.numbers if n != f]
    if not ratio.start < f.start < part.start or ratio.value <= 0:
        return None
    text = p.text.lower()
    source = re.search(r'\bfor every ([a-z ]+?), there are\s*$', text[:ratio.start])
    larger = re.match(r'\s+([a-z]+(?: [a-z]+)?)(?=,|[.;])', _tail(p,ratio))
    scope = re.match(r'\s+of the ([a-z ]+?) (?:are|were) ([^.;,]+)', _tail(p,f))
    if not source or not larger or not scope:
        return None
    if _words(larger.group(1)) != _words(scope.group(1)):
        return None
    target = _words(source.group(1)) - _words(larger.group(1))
    if not target or not target <= _words(p.question):
        return None
    known = _words(_clause(_tail(p,part)))
    label = _words(scope.group(2))
    if not label or not label <= known:
        return None
    return _answer(part.value/f.value/ratio.value, 'Counted subset / its share / ratio of the larger category to the requested category')


def _listed_progress(p, fs):
    if len(fs) != 1 or not 4 <= len(p.numbers) <= 10:
        return None
    f = fs[0]
    amounts = [n for n in p.numbers if n != f]
    count, parts = amounts[0], amounts[1:]
    if count.value != len(parts) or any(n.start > f.start for n in parts):
        return None
    text = p.text.lower()
    if not _has(r'\b(?:left|still|remaining)\b', p.question):
        return None
    if not _has(r'\b(?:read|completed|finished)\b',text[:count.start]):
        return None
    if not _has(r'\brespectively\b',text[parts[-1].end:f.start]) or not re.match(r'\s+of the way through\b',_tail(p,f)):
        return None
    # All list entries except the last must be comma/and separated literals.
    if not all(re.fullmatch(r'\s*,?\s*(?:and\s*)?',text[a.end:b.start]) for a,b in zip(parts,parts[1:])):
        return None
    unit = re.match(r'\s+([a-z]+)',_tail(p,parts[-1]))
    if not unit or _singular(unit.group(1)) not in _words(p.question):
        return None
    completed = sum((n.value for n in parts),Fraction(0))
    return _answer(completed*(1-f.value)/f.value, 'Sum the completed parts, recover the whole, then subtract the completed amount')


def _category_addition(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    total, f, added = p.numbers
    if fs != [f] or not re.match(r'\s+of (?:the|his|her|their)\b', _tail(p,f)):
        return None
    text = p.text.lower()
    if not _has(r'\b(?:gives?|gave|buys?|bought|gets?|got|receives?|received)\b',text[f.end:added.start]):
        return None
    if _has(r'\b(?:each|per|times|twice|more than|less than|left|remaining)\b',text):
        return None
    label = _words(_label(replace(p,text=text),f))
    unit = re.match(r'\s+([a-z]+)',_tail(p,total))
    if not unit:
        return None
    distinctive = label - {_singular(unit.group(1))}
    added_words = _words(_clause(_tail(p,added)))
    if not distinctive or not distinctive <= added_words or not distinctive <= _words(p.question):
        return None
    return _answer(total.value*f.value+added.value, 'Original category share plus the new members of that category')


def _money_sum_share(p, fs):
    if len(fs) != 1 or not 3 <= len(p.numbers) <= 6:
        return None
    f = fs[0]
    amounts = [n for n in p.numbers if n != f]
    if any(n.kind != 'money' or n.start > f.start for n in amounts):
        return None
    text = p.text.lower()
    if not re.match(r'\s+of (?:his|her|their|the) total (?:savings|earnings|income)\b', _tail(p,f)):
        return None
    if not _has(r'\b(?:spend|spent|spends)\b', p.question):
        return None
    if _has(r'\b(?:per|each|times|lost|gave|paid|cost)\b',text[:f.start]):
        return None
    if not _has(r'\b(?:saves?|saved|earns?|earned|makes?|made)\b',text[:amounts[0].start]):
        return None
    value = sum((n.value for n in amounts),Fraction(0))*f.value
    return _answer(value, 'Combined savings x fraction spent; dollars: '+format_number(value))


def _time_remainder(p, fs):
    """A measured duration less a list of measured component durations."""
    if not any(n.value.denominator > 1 for n in p.numbers) or not 3 <= len(p.numbers) <= 9:
        return None
    if not _has(r'\b(?:rest|instead of|remaining|left)\b',p.body+' '+p.question):
        return None
    measured = []
    for n in p.numbers:
        unit = re.match(r'[- ]+(?:of (?:an? )?)?(seconds?|minutes?|hours?|days?)\b',_tail(p,n))
        if not unit:
            return None
        measured.append((n,_TIME[_singular(unit.group(1))]))
    # Exactly one larger-unit whole, and components all in a common smaller unit.
    largest = max(u for n,u in measured)
    wholes = [(n,u) for n,u in measured if u == largest]
    parts = [(n,u) for n,u in measured if u != largest]
    if len(wholes) != 1 or not parts or len({u for n,u in parts}) != 1:
        return None
    target = re.search(r'\b(seconds?|minutes?|hours?|days?)\b',p.question)
    if not target:
        return None
    whole, scale = wholes[0]
    seconds = whole.value*scale-sum((n.value*u for n,u in parts),Fraction(0))
    return _answer(seconds/_TIME[_singular(target.group(1))], 'Total duration minus the stated component durations, converted to the requested time unit')


def _per_person_cost(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    f = fs[0]
    money = [n for n in p.numbers if n.kind == 'money']
    if len(money) != 1:
        return None
    price = money[0]
    count = next(n for n in p.numbers if n not in (price,f))
    text = p.text.lower()
    if not price.start < f.start < count.start or not _has(r'\bcost\b',p.question):
        return None
    measure = re.match(r'\s+(?:of )?(?:an? )?([a-z]+)\b',_tail(p,f))
    if not measure:
        return None
    unit = _singular(measure.group(1))
    if not _has(r'\b(?:an?|per|each) '+re.escape(unit)+r'\b',text[price.end:f.start]):
        return None
    if not _has(r'\beach person (?:needs?|uses?|requires?|consumes?)\s*$',text[:f.start]):
        return None
    if not (_has(r'\bfamily of\s*$',text[:count.start]) or re.match(r'\s+(?:people|persons|members)\b',_tail(p,count))):
        return None
    value = price.value*f.value*count.value
    return _answer(value, 'Number of people x quantity per person x price per unit; dollars: '+format_number(value))


def _hypothetical_stock(p, fs):
    """Removing a gives f times the stock that adding b would give."""
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    removed, f, added = p.numbers
    if fs != [f] or not _has(r'\b(?:how many|how much)\b',p.question):
        return None
    text = p.text.lower()
    if not _has(r'\b(?:taking|take|removing|remove)\s*$',text[:removed.start]):
        return None
    if not _has(r'\baway would leave\s*$',text[removed.end:f.start]):
        return None
    if not re.fullmatch(r'\s+as many[^.;!?]*\bas if\s+',text[f.end:added.start]):
        return None
    if not re.match(r'\s+were added\b',_tail(p,added)):
        return None
    return _answer((removed.value+f.value*added.value)/(1-f.value), 'Solve initial stock minus removal = fraction x (initial stock plus addition)')


def _subdivision(p, fs):
    """Equal repeated cuts change piece count, not the quantity of material."""
    text = p.text.lower()
    ns = [n for n in p.numbers if n.raw.lower() not in ('halves','quarters')]
    if len(fs) != 2 or len(ns) != 3 or ns[0] in fs:
        return None
    count = ns[0]
    if count.value.denominator != 1 or not _has(r'\b(?:pieces|parts)\b',p.question):
        return None
    if not all(_has(r'\b(?:tears?|tear|torn|cuts?|cut|split|splits)\b', text[count.end:f.start])
               and re.match(r'\s*(?:[,.;]|then\b|$)',_tail(p,f)) for f in fs):
        return None
    if not all(_has(r'\bin\s*$',text[:f.start]) for f in fs):
        return None
    if any((1/f.value).denominator != 1 for f in fs):
        return None
    return _answer(count.value/fs[0].value/fs[1].value, 'Starting pieces x equal subdivisions at each cutting stage')


def _restated_share_split(p, fs):
    if len(fs) != 2 or len(p.numbers) != 4 or fs[0].value+fs[1].value != 1:
        return None
    total, first, rest, groups = p.numbers
    if fs != [first,rest] or groups.value <= 0:
        return None
    text = p.text.lower()
    if not _has(r'\bthe other\s*$',text[:rest.start]):
        return None
    if not _has(r'\b(?:puts?|split|divided|places?) into\s*$',text[rest.end:groups.start]):
        return None
    label = re.match(r'\s+(?:[a-z]+ )?([a-z]+)',_tail(p,groups))
    if not label or _singular(label.group(1)) not in _words(p.question) or not _has(r'\beach\b',p.question):
        return None
    return _answer(total.value*rest.value/groups.value, 'Retained share / number of equal containers')


def _inverse_sum_comparison(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    f = fs[0]
    a,b = [n for n in p.numbers if n != f]
    if not a.start < b.start < f.start:
        return None
    text = p.text.lower()
    if not _has(r'\badded to\b',text[a.end:b.start]) or not _has(r'\bwill be\s*$',text[b.end:f.start]):
        return None
    comparison = re.match(r'\s+(?:of )?the number of ([a-z]+) ([a-z]+) (?:saw|has|had|owns?|collected)\b',_tail(p,f))
    if not comparison or not _has(r'\b'+re.escape(comparison.group(2))+r'\b',p.question):
        return None
    if _singular(comparison.group(1)) not in _words(p.question):
        return None
    return _answer((a.value+b.value)/f.value, 'Combined counted amounts / fraction of the compared whole')


def _entity(phrase):
    """A noun phrase serving as an explicitly compared subject or object."""
    phrase = re.split(r'[,.;!?]',phrase)[0].strip().lower()
    phrase = re.sub(r"^[a-z]+'s\s+", '', phrase)
    phrase = re.sub(r'^(?:(?:and|if|then|the|a|an|their|his|her|its|our)\s+)+','',phrase)
    middle = re.match(r'([a-z]+) in the (middle|center|centre) of\b',phrase)
    if middle:
        phrase = middle.group(2)+' '+middle.group(1)
    phrase = re.split(r"\b(?:that|which|who|in|on|at|for|with|to|from|has|have|had|is|was|are|were|can|did|does|do)\b|[,.;!?]",phrase)[0].strip()
    if not re.fullmatch(r'[a-z]+(?: [a-z]+){0,3}',phrase):
        return None
    if phrase.split()[0] in ('he','she','it','they','there','what','how'):
        return None
    return ' '.join(_singular(w) for w in phrase.split())


def _noun_relations(p, fs):
    """A connected graph of explicitly compared objects or measured parts."""
    ns = [n for n in p.numbers if not (n.raw.lower() in ('third','fourth') and
          re.match(r'\s+(?!of\b|as\b|the\b|that\b)[a-z]+',_tail(p,n)))]
    text = p.text.lower()
    for i,n in reversed(list(enumerate(ns))):
        text = text[:n.start]+'Q'+str(i)+text[n.end:]
    asks = list(ASK.finditer(text))
    if not asks:
        return None
    body,query = text[:asks[-1].start()],text[asks[-1].start():]
    if _has(r'\b(?:per|each|every|spent|gave|sold|ate|left|remaining|ago)\b',body):
        return None
    relation = re.compile(r'Q(\d+)\s+(?:times\s+)?(?:'
        r'as (?:many|much|high|long|large|big)(?: [a-z]+){0,6}? as\s+|'
        r'the (?:number|amount) of [a-z]+ (?:as|of)\s+|'
        r'(?:of )?the (?:length|size|capacity|height|weight|amount|number)(?: of [a-z]+)? of\s+|'
        r'(?:of )?the (?:length|size|capacity|height|weight) of\s+)')
    edges, used = [],set()
    for m in relation.finditer(body):
        clause = re.split(r'[.;!?]|,?\s+and\s+',body[:m.start()])[-1]
        # The final predicate introduces the subject of this comparison.
        subject = re.match(r"(.+?)\s+(?:has|have|had|is|was|are|were|that's|costs?|measures?|scores?|scored)\b",clause.strip())
        if not subject:
            return None
        left_phrase = subject.group(1)
        # A part can be introduced as the object of a possession verb.
        part = re.search(r"\b(?:has|have|had) (.+?) that's\s*$",clause)
        if part:
            left_phrase = part.group(1)
        left = _entity(left_phrase)
        right = _entity(body[m.end():])
        if left and right and ' ' not in right and ' ' in left and _has(
                r'^(?:first|second|third|fourth|fifth|longest|shortest|largest|smallest)$',right):
            right += ' '+left.split()[-1]
        if not left or not right or left == right:
            return None
        i = int(m.group(1))
        if ns[i].value <= 0:
            return None
        edges.append((left,right,ns[i].value,Fraction(0)))
        used.add(i)
    if not edges or not any(ns[i] in fs for i in used):
        return None
    nodes = {v for edge in edges for v in edge[:2]}
    if not 2 <= len(nodes) <= 3:
        return None
    def mentions(s):
        # Singular/plural noun forms are lexical variants of the same label.
        words = ' '.join(_singular(w) for w in re.findall(r'[a-z]+',s))
        return [node for node in nodes if _has(r'\b'+re.escape(node)+r'\b',words)]
    known,total = [],None
    for i,n in enumerate(ns):
        if i in used:
            continue
        token = 'Q'+str(i)
        at = text.index(token)
        before = re.split(r'[.;!?]',text[:at])[-1]
        after = _clause(text[at+len(token):]).split(' and ')[0]
        head = re.match(r'\s+([a-z]+)\b',after)
        node_heads = {node.split()[-1] for node in nodes}
        if n.value == len(nodes) and head and (_singular(head.group(1)) in node_heads or
                head.group(1) in ('members','objects','parts','people')):
            continue
        if n.start >= len(p.body):
            return None
        if _has(r'\b(?:total|together|combined|overall|altogether)\b',before+' '+after):
            if total is not None:
                return None
            total = n.value
            continue
        owners = mentions(before)
        if not owners and _has(r'\bfor\b',after):
            owners = mentions(after)
        if len(owners) != 1 or _has(r'Q\d+',before+after):
            return None
        known.append((owners[0],n.value))
    values = _equation_graph(edges,known,total)
    if values is None:
        return None
    asked = mentions(query)
    if not asked and _has(r'\b(?:total|together|combined|in all|both)\b',query):
        return _answer(sum(values.values(),Fraction(0)), 'Add the measured objects after resolving their proportional relationships')
    if len(asked) != 1:
        return None
    if _has(r'\b(?:together|combined|in all|both)\b',query):
        return None
    return _answer(values[asked[0]], 'Resolve the measured objects from their proportional relationships')


def _anaphoric_companion(p, fs):
    if len(fs) != 1 or len(p.numbers) != 2:
        return None
    f = fs[0]
    base = next(n for n in p.numbers if n != f)
    if base.start > f.start or not _has(r'\b(?:total|altogether|in all|together|everything)\b',p.question):
        return None
    tail = _clause(_tail(p,f))
    if not re.match(r'\s+(?:as (?:many|much)\b|of that\b|that (?:amount|many|much)\b)',tail):
        return None
    if _has(r'\b(?:as|than|per|each|every|left|remaining)\b', re.sub(r'^\s+as (?:many|much)\b','',tail)):
        return None
    if _has(r'\b(?:each|per|every|times|twice|more than|less than)\b',p.text.lower()):
        return None
    return _answer(base.value*(1+f.value), 'Counted amount plus its stated fractional companion')


def _saving_periods(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    rate,f,goal = p.numbers
    if fs != [f] or rate.kind != 'money' or goal.kind != 'money':
        return None
    text = p.text.lower()
    period = re.match(r'\s+(?:per|each|every|a) (day|week|month|year)\b',_tail(p,rate))
    if not period or not _has(r'\b'+period.group(1)+r's\b',p.question):
        return None
    if not _has(r'\b(?:earns?|makes?|paid)\s*$',text[:rate.start]) or not _has(r'\bsave\s*$',text[rate.end:f.start]):
        return None
    if not re.match(r'\s+of (?:his|her|their) (?:monthly|weekly|daily|yearly|annual)?\s*(?:earnings|salary|pay|income)\b',_tail(p,f)):
        return None
    if not _has(r'\b(?:worth|costs?|priced at|goal of)\s*$',text[f.end:goal.start]):
        return None
    if rate.value <= 0:
        return None
    return _answer(goal.value/(rate.value*f.value), 'Savings goal / amount saved per period')


def _retained_cash(p, fs):
    if not 1 <= len(fs) <= 4 or len(p.numbers) != len(fs)+1:
        return None
    initial = p.numbers[0]
    if initial.kind != 'money' or initial in fs or not _has(r'\b(?:left|remaining)\b',p.question):
        return None
    text = p.text.lower()
    value = initial.value
    previous = initial.end
    for i,f in enumerate(fs):
        if not _has(r'\b(?:spent|spends?|used|uses?|gave|gives?)\s*$',text[previous:f.start]):
            return None
        if not re.match(r'\s+(?:of )?(?:(?:the|his|her|their) )?(?:money|amount|remaining|rest)\b',_tail(p,f)):
            return None
        if i and not _has(r'\b(?:left|remaining|rest)\b',_clause(_tail(p,f))):
            return None
        value *= 1-f.value
        previous = f.end
    return _answer(value, 'Retain the complementary share after each stated expenditure; dollars: '+format_number(value))


def _exhausted_stock(p, fs):
    """All of an unknown stock used: one share and counted other uses."""
    if len(fs) != 1 or not 3 <= len(p.numbers) <= 6:
        return None
    f = fs[0]
    counts = [n for n in p.numbers if n != f]
    if any(n.start < f.start for n in counts):
        return None
    text = p.text.lower()
    if not _has(r'\b(?:redeemed|spent|used|gave away|sold) all\b',text[:f.start]):
        return None
    if not re.match(r'\s+of (?:them|those|these)\b',_tail(p,f)):
        return None
    units = [re.match(r'\s+([a-z]+)',_tail(p,n)) for n in counts]
    if not all(units) or len({_singular(m.group(1)) for m in units}) != 1:
        return None
    if _singular(units[0].group(1)) not in _words(p.question):
        return None
    previous = f.end
    for n in counts:
        if not _has(r'\b(?:spent|used|gave|sold) (?:another )?\s*$',text[previous:n.start]):
            return None
        previous = n.end
    return _answer(sum((n.value for n in counts),Fraction(0))/(1-f.value), 'Counted other uses / complementary share of the exhausted stock')


def _production_remainder(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    rate,count,f = p.numbers
    if fs != [f] or not _has(r'\b(?:left|remaining)\b',p.question):
        return None
    text = p.text.lower()
    per = re.match(r'\s+([a-z]+) (?:per|a|each|every) (day|week|month|year)\b',_tail(p,rate))
    if not per or not re.match(r'\s+'+per.group(2)+r's\b',_tail(p,count)):
        return None
    if _singular(per.group(1)) not in _words(p.question):
        return None
    if not _has(r'\b(?:sells?|sold|uses?|used|gave|gives?|ate|eats?)\s*$',text[count.end:f.start]):
        return None
    if not re.match(r'\s+of (?:the|those|these|his|her|their) '+re.escape(per.group(1))+r'\b',_tail(p,f)):
        return None
    return _answer(rate.value*count.value*(1-f.value), 'Production per period x number of periods x retained share')


def _relative_expense(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    expense,f,budget = p.numbers
    if fs != [f] or expense.kind != 'money' or budget.kind != 'money':
        return None
    text = p.text.lower()
    if not _has(r'\b(?:left|remaining)\b',p.question) or not re.match(r'\s+of that\b',_tail(p,f)):
        return None
    if not _has(r'\b(?:paid|spent|cost)\s*$',text[:expense.start]):
        return None
    if not _has(r'\b(?:at the beginning|at first|initially|originally|to start)\b',_clause(_tail(p,budget))):
        return None
    value = budget.value-expense.value*(1+f.value)
    return _answer(value, 'Starting money minus the original and proportional expenses; dollars: '+format_number(value))


def _action_subset(p, fs):
    if len(fs) != 2 or len(p.numbers) != 3:
        return None
    base = next(n for n in p.numbers if n not in fs)
    if base.start > fs[0].start:
        return None
    tails = [_clause(_tail(p,f)) for f in fs]
    first = re.search(r'\bwent ([a-z]+)\b',tails[0])
    second = re.match(r'\s+of the ([a-z]+) went ([a-z]+)\b',tails[1])
    if not first or not second:
        return None
    def root(word):
        return re.sub(r'(?:ing|ers?|s)$','',word)
    if root(first.group(1)) != root(second.group(1)) or first.group(1) == second.group(2):
        return None
    if not _has(r'\b'+re.escape(second.group(2))+r'\b',p.question):
        return None
    return _answer(base.value*fs[0].value*fs[1].value, 'Whole x first activity share x second activity share within that group')


def _measured_loss_output(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    stock,output,f = p.numbers
    if fs != [f]:
        return None
    text = p.text.lower()
    unit = re.match(r'\s+(cups?|pounds?|ounces?|liters?|litres?|gallons?|grams?|kilograms?)\b',_tail(p,stock))
    if not unit:
        return None
    head = _singular(unit.group(1))
    if not re.match(r'\s+(?:of )?an? '+head+r'\b',_tail(p,f)):
        return None
    if not _has(r'\b(?:steals?|stole|uses?|used|spills?|spilled|loses?|lost)\s*$',text[output.end:f.start]):
        return None
    if not _has(r'\beach '+head+r'\b',text[stock.end:output.start]):
        return None
    result_unit = re.match(r'\s+([a-z]+)',_tail(p,output))
    if not result_unit or _singular(result_unit.group(1)) not in _words(p.question):
        return None
    return _answer((stock.value-f.value)*output.value, 'Remaining measured material x output per unit of material')


def _grouped_inverse_remainder(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    count,each,f = p.numbers
    if fs != [f] or not _has(r'\b(?:original|at first|initially)\b',p.question):
        return None
    text = p.text.lower()
    if not _has(r'\b(?:taking|took|takes?|ate|eat|used|use)\s*$',text[count.end:each.start]):
        return None
    if not _has(r'\beach\b',text[each.end:f.start]) or not re.match(r'\s+of the original amount left\b',_tail(p,f)):
        return None
    unit = re.match(r'\s+([a-z]+)',_tail(p,each))
    if not unit or _singular(unit.group(1)) not in _words(p.question):
        return None
    return _answer(count.value*each.value/(1-f.value), 'Counted use / complementary share to recover the original stock')


def _fractional_unit_price(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    f,price,budget = p.numbers
    if fs != [f] or price.kind != 'money' or budget.kind != 'money' or price.value <= 0:
        return None
    text = p.text.lower()
    measure = re.match(r'\s+of (?:an? )?(pound|ounce|kilogram|gram|liter|litre|gallon|meter|metre)\b',_tail(p,f))
    if not measure or not _has(r'\bcosts?\s*$',text[f.end:price.start]):
        return None
    if not _has(r'\b'+measure.group(1)+r's\b',p.question) or not _has(r'\bbuy\b',p.question):
        return None
    return _answer(budget.value*f.value/price.value, 'Budget / price per measured fraction x quantity in that fraction')


def _purchase_companion(p, fs):
    if len(fs) != 1 or len(p.numbers) != 2:
        return None
    f,amount = p.numbers
    if fs != [f] or not _has(r'\bbefore the purchase\b',p.body) or not _has(r'\bafter the purchase\b',p.question):
        return None
    text = p.text.lower()
    relation = re.match(r'\s+the ([a-z]+) (?:he|she|they) bought\b',_tail(p,f))
    if not relation or not re.match(r'\s+'+relation.group(1)+r'\b',_tail(p,amount)):
        return None
    return _answer(amount.value*(1+f.value), 'Previous proportional holding plus the incoming purchase')


def _combined_price_ratio(p, fs):
    if len(fs) != 1 or len(p.numbers) != 2:
        return None
    total,f = p.numbers
    if fs != [f] or total.kind != 'money':
        return None
    text = p.text.lower()
    if not _has(r'\bbought\b[^.;]*\band\b[^.;]*\bfor\s*$',text[:total.start]):
        return None
    if not re.match(r'\s+the (?:price|cost) of\b',_tail(p,f)):
        return None
    if not _has(r'\b(?:it|that) is\s*$',text[len(p.body):f.start]):
        return None
    value = total.value*f.value/(1+f.value)
    return _answer(value, 'Combined price x requested price ratio / sum of price ratios; dollars: '+format_number(value))


def _fractional_capacity(p, fs):
    if len(fs) != 1 or len(p.numbers) != 2:
        return None
    total,f = p.numbers
    if fs != [f] or total.value <= 0:
        return None
    text = p.text.lower()
    container = re.search(r'\beach ([a-z]+) can (?:only )?(?:contain|hold|carry)\s*$',text[:f.start])
    if not container or _singular(container.group(1)) not in _words(p.question):
        return None
    stock = re.match(r'\s+([a-z]+)',_tail(p,total))
    if not stock or not re.match(r'\s+of the '+stock.group(1)+r'\b',_tail(p,f)):
        return None
    count = 1/f.value
    return _answer(Fraction(-(-count.numerator//count.denominator)), 'Whole / fraction of the whole held by each container, rounded up to whole containers')


def _needed_yield(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    goal,f,yield_per = p.numbers
    if fs != [f] or yield_per.value <= 0:
        return None
    text = p.text.lower()
    if not re.match(r'\s+of the [a-z]+ will be lost\b',_tail(p,f)):
        return None
    per = re.search(r'\beach ([a-z]+)(?: [a-z]+){0,4}? (?:provide|provides|yield|yields|produce|produces)\s*$',text[f.end:yield_per.start])
    if not per or not _words(per.group(1)) <= _words(p.question):
        return None
    labels = [re.match(r'\s+(?:[a-z]+\s+)?([a-z]+)\b',_tail(p,n)) for n in (goal,yield_per)]
    if not all(labels) or labels[0].group(1) != labels[1].group(1):
        return None
    count = goal.value/(yield_per.value*(1-f.value))
    return _answer(Fraction(-(-count.numerator//count.denominator)), 'Required output / output per survivor / surviving share, rounded up to whole producers')


def _past_companion(p, fs):
    if len(fs) != 1 or len(p.numbers) != 3:
        return None
    f,added,now = p.numbers
    if fs != [f]:
        return None
    text = p.text.lower()
    relation = re.match(r'\s+as many ([a-z]+) as ([a-z]+) yesterday\b',_tail(p,f))
    if not relation or _singular(relation.group(1)) not in _words(p.question):
        return None
    if not _has(r'\b(?:found|added|bought|received)\s*$',text[f.end:added.start]):
        return None
    reference = _singular(relation.group(2))
    if not re.match(r'\s+(?:more )?'+reference+r's?\b',_tail(p,added)):
        return None
    if not re.match(r'\s+'+reference+r's? now\b',_tail(p,now)):
        return None
    return _answer((now.value-added.value)*f.value, 'Undo the addition to the reference category, then apply the earlier comparison')


def _scaled_group_count(p, fs):
    """Each counted group holds a share of the number of groups."""
    if len(fs) != 1 or len(p.numbers) != 2:
        return None
    base,f = p.numbers
    if fs != [f] or base.value.denominator != 1:
        return None
    text = p.text.lower()
    group = re.match(r'\s+([a-z]+)\b',_tail(p,base))
    relation = re.match(r'\s+times as many ([a-z]+) as the number of ([a-z]+)\b',_tail(p,f))
    if not group or not relation or _singular(group.group(1)) != _singular(relation.group(2)):
        return None
    if not _has(r'\beach '+_singular(group.group(1))+r'\b',p.body):
        return None
    if _singular(relation.group(1)) not in _words(p.question) or not _has(r'\btotal\b',p.question):
        return None
    return _answer(base.value*base.value*f.value, 'Number of groups x items per group computed from the stated proportional comparison')


def _equal_groups_and_smaller(p, fs):
    """A whole split into equal large groups and one proportional small group."""
    if len(fs) != 1 or len(p.numbers) != 4:
        return None
    total,groups,f,repeated = p.numbers
    if fs != [f] or groups.value != repeated.value or groups.value <= 0:
        return None
    text = p.text.lower()
    if not _has(r'\b(?:identically[ -]sized|equal[ -]sized|identical)\b',text[groups.end:f.start]):
        return None
    target = re.search(r'\binto the ([a-z]+)\b[^.;]*$',text[:f.start])
    if not target or not _has(r'\b'+target.group(1)+r'\b',p.question):
        return None
    relation = re.match(r'\s+as many ([a-z]+) as (?:he|she|they) (?:placed|put) in each of the\s*$',text[f.end:repeated.start])
    unit = re.match(r'\s+(dozen )?([a-z]+)\b',_tail(p,total))
    if not relation or not unit or _singular(unit.group(2)) != _singular(relation.group(1)):
        return None
    whole = total.value*(12 if unit.group(1) else 1)
    return _answer(whole*f.value/(groups.value+f.value), 'Whole x relative small-group size / sum of all relative group sizes')


def solve(problem):
    if not has_fraction(problem.text) or any(n.kind == 'percent' for n in problem.numbers):
        return None
    # In mixed time expressions the unit can precede the fractional component.
    text = re.sub(r'\b(?:an?|one) (hour|day|minute) and a half\b',
                  r'1 1/2 \1s',problem.text,flags=re.I)
    prepared = replace(problem,text=text) if text != problem.text else problem
    p = _prepare(prepared)
    if p is None:
        return None
    fs = _fractions(p)
    if not fs:
        return _time_remainder(p,fs)
    for reader in (_anaphoric_time, _rest_categories, _related_remainder,
                   _listed_categories, _inverse_cash, _rate_volume,
                   _package_measure, _enumerated_split, _inverse_category_ratio,
                   _listed_progress, _category_addition, _money_sum_share,
                   _time_remainder, _per_person_cost, _hypothetical_stock,
                   _subdivision, _restated_share_split, _inverse_sum_comparison,
                   _anaphoric_companion, _saving_periods, _retained_cash,
                   _exhausted_stock, _production_remainder, _relative_expense,
                   _action_subset, _measured_loss_output,
                   _grouped_inverse_remainder, _fractional_unit_price,
                   _purchase_companion, _combined_price_ratio,
                   _fractional_capacity, _needed_yield, _past_companion,
                   _scaled_group_count, _equal_groups_and_smaller):
        result = reader(p, fs)
        if result is not None:
            return result
    return (_named_subset(problem,p,fs) or _comparison_language(problem,p,fs)
            or _noun_relations(p,fs))
