"""Read quantities without floating point or rewriting their source offsets."""
import re
from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction


SMALL = dict(zip(
    'zero one two three four five six seven eight nine ten eleven twelve thirteen '
    'fourteen fifteen sixteen seventeen eighteen nineteen'.split(), range(20)))
TENS = dict(zip('twenty thirty forty fifty sixty seventy eighty ninety'.split(), range(20, 100, 10)))
SCALES = {'hundred': 100, 'thousand': 1000, 'million': 1000000, 'billion': 1000000000}
FRACTIONS = {'half': 2, 'halves': 2, 'third': 3, 'thirds': 3,
             'quarter': 4, 'quarters': 4, 'fourth': 4, 'fourths': 4}
_ONES = r'(?:one|two|three|four|five|six|seven|eight|nine)'
_UNDER100 = (r'(?:(?:' + '|'.join(TENS) + r')(?:[ -]+' + _ONES + r')?|'
             + '|'.join(sorted(SMALL, key=len, reverse=True)) + r')')
_GROUP = r'(?:' + _ONES + r'[ -]+hundred(?:[ -]+(?:and[ -]+)?' + _UNDER100 + r')?|' + _UNDER100 + r')'
_WORD_NUMBER = _GROUP + r'(?:[ -]+(?:billion|million|thousand)(?:[ -]+(?:and[ -]+)?' + _GROUP + r')?)*'
_DIGIT = r'(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?'
_FRACTION_WORD = r'(?:half|halves|thirds?|quarters?|fourths?)'
_TOKEN = re.compile(
    r'(?<![\w])(?:[$£€]\s*)?(?:'
    + _WORD_NUMBER + r'\s+and\s+(?:a|' + _WORD_NUMBER + r')\s+' + _FRACTION_WORD + r'|'
    + _DIGIT + r'\s+' + r'\d+/\d+' + r'|'
    + _DIGIT + r'(?:\s*/\s*\d+)?|'
    + r'(?:' + _WORD_NUMBER + r'|a)' + r'[ -]+' + _FRACTION_WORD + r'|'
    + _FRACTION_WORD + r'|' + _WORD_NUMBER
    + r')(?:\s*(?:%|percent\b))?(?!\d)', re.I)


@dataclass(frozen=True)
class Number:
    value: Fraction
    start: int
    end: int
    raw: str
    kind: str = 'number'


def _cardinal(words):
    total, group = 0, 0
    for word in words:
        if word == 'and':
            continue
        if word in SMALL:
            group += SMALL[word]
        elif word in TENS:
            group += TENS[word]
        elif word == 'hundred':
            group = (group or 1) * 100
        elif word in SCALES:
            total += (group or 1) * SCALES[word]
            group = 0
        else:
            raise ValueError('Not a cardinal number')
    return Fraction(total + group)


def parse_number(text):
    """Digits, money, percent (as a ratio), cardinal words and simple fractions."""
    clean = re.sub(r'[$£€,]', '', text.lower()).strip()
    percent = clean.endswith('%') or clean.endswith('percent')
    clean = re.sub(r'\s*(?:%|percent)$', '', clean).strip()
    mixed_words = re.fullmatch(r'(.+) and (a|.+) (' + _FRACTION_WORD + ')', clean)
    if mixed_words:
        whole, numerator, denominator = mixed_words.groups()
        value = _cardinal(whole.replace('-', ' ').split()) + (
            Fraction(1) if numerator == 'a' else _cardinal(numerator.replace('-', ' ').split())
        ) / FRACTIONS[denominator]
    elif re.fullmatch(r'\d+\s+\d+/\d+', clean):
        whole, part = clean.split()
        value = Fraction(whole) + Fraction(part)
    elif re.fullmatch(r'\d+(?:\.\d+)?(?:\s*/\s*\d+)?', clean):
        value = Fraction(clean.replace(' ', ''))
    else:
        words = clean.replace('-', ' ').split()
        if words[-1] in FRACTIONS:
            numerator = Fraction(1) if len(words) == 1 or words[:-1] == ['a'] else _cardinal(words[:-1])
            value = numerator / FRACTIONS[words[-1]]
        else:
            value = _cardinal(words)
    return value / 100 if percent else value


def read_numbers(text):
    """Return Number records, with offsets into the original text.

    Ordinals (1st, second, etc.) are intentionally excluded: they usually label
    events rather than count things. Skills can interpret those labels locally.
    """
    found = []
    for match in _TOKEN.finditer(text):
        raw = match.group()
        suffix = text[match.end():]
        if raw[-1].isalpha() and suffix[:1].isalnum():
            continue
        if raw[-1].isdigit() and re.match(r'(?:st|nd|rd|th)\b', suffix, re.I):
            continue
        kind = 'percent' if re.search(r'%|percent', raw, re.I) else (
            'money' if re.search(r'[$£€]', raw) else 'number')
        try:
            found.append(Number(parse_number(raw), match.start(), match.end(), raw, kind))
        except (ValueError, ZeroDivisionError):
            continue
    return found


def format_number(value):
    """Whole numbers stay whole; decimals are calculated from exact fractions."""
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    with localcontext() as context:
        context.prec = 16
        return format(Decimal(value.numerator) / Decimal(value.denominator), 'f').rstrip('0').rstrip('.')
