"""Shared exact arithmetic and local normalization for proportional readers.

Normalization recognizes number grammar, never story vocabulary. Callers still
have to establish the base, units and requested operation for every quantity.
"""
import re
from fractions import Fraction

from ..numbers import TENS, SCALES, _WORD_NUMBER, _DIGIT, read_numbers, parse_number, format_number


def _has(pattern, text):
    return re.search(pattern, text) is not None


def _answer(value, explanation):
    if value < 0:
        return None
    return value, explanation + ' = ' + format_number(value) + '.'


def normalize_magnitudes(text):
    """Expand digit/scale combinations while retaining currency symbols."""
    scales = '|'.join(SCALES)
    return re.sub(r'(?<![\w.])(' + _DIGIT + r')\s+(' + scales + r')\b',
                  lambda m: format_number(parse_number(m.group(1)) *
                                          SCALES[m.group(2).lower()]), text, flags=re.I)


# Ordinal spellings are a closed linguistic vocabulary, unlike story nouns.
_ORDINALS = dict(zip(
    'first second third fourth fifth sixth seventh eighth ninth tenth eleventh '
    'twelfth thirteenth fourteenth fifteenth sixteenth seventeenth eighteenth '
    'nineteenth'.split(), range(1, 20)))
_DENOMINATORS = {'half': 2, 'halves': 2, 'quarter': 4}
_DENOMINATORS.update({w: n for w, n in _ORDINALS.items() if n >= 3})
for _word, _value in TENS.items():
    _DENOMINATORS[_word[:-1] + 'ieth'] = _value
    for _ordinal, _unit in _ORDINALS.items():
        if _unit < 10:
            _DENOMINATORS[_word + ' ' + _ordinal] = _value + _unit
_DENOMINATORS.update({w + 'th': n for w, n in SCALES.items()})
_DENOMINATOR = '|'.join(re.escape(w).replace(r'\ ', '[ -]+') +
                        ('' if w == 'halves' else 's?')
                        for w in sorted(_DENOMINATORS, key=len, reverse=True))
_CARDINAL = r'(?:\d[\d,]*|' + _WORD_NUMBER + r')'
_NUMERATOR = r'(?:' + _CARDINAL + r'|an?)'
_WORD_FRACTION = re.compile(r'\b(' + _NUMERATOR + r')[ -]+(' +
                            _DENOMINATOR + r')\b', re.I)
_FRACTION_CUE = re.compile(r'\b(?:half|halves|thirds?|fourths?|quarters?|'
                           + _DENOMINATOR + r')\b|\d+\s*/\s*\d+', re.I)


def has_fraction(text):
    return _FRACTION_CUE.search(text) is not None


def normalize_fractions(text, basic=True):
    """Canonicalize named fractions, including compound numerators/denominators.

    Readers using the shared number parser can retain its basic spellings.
    Other readers need slash notation to distinguish shares from whole counts.
    Bare ordinals are left alone: an eleventh day is a label, not a share.
    """
    if basic:
        # Preserve the shared parser's mixed-number interpretation before a
        # compound cardinal can consume its numerator ("one hundred and two thirds").
        for number in reversed(read_numbers(text)):
            if ' and ' in number.raw.lower() and number.value.denominator > 1:
                value = str(number.value)
                if number.kind == 'money':
                    value = next(c for c in number.raw if c in '$£€') + value
                text = text[:number.start] + value + text[number.end:]

    def fraction(match):
        numerator, denominator = match.groups()
        key = re.sub(r'[ -]+', ' ', denominator.lower())
        if key not in _DENOMINATORS:
            key = key[:-1]  # plural denominator
        divisor = _DENOMINATORS[key]
        if not basic and divisor <= 4:
            return match.group()
        value = Fraction(1) if numerator.lower() in ('a', 'an') else parse_number(numerator)
        return str(value.numerator) + '/' + str(divisor)

    text = _WORD_FRACTION.sub(fraction, text)
    if basic:
        text = re.sub(r'\bhalf\b', '1/2', text, flags=re.I)
        text = re.sub(r'\bquarter(?=[ -]+(?:hour|of|the)\b)', '1/4', text, flags=re.I)
        # A whole followed by an explicit fractional part is one number.
        text = re.sub(r'\b(' + _CARDINAL + r')\s+and\s+(\d+/\d+)\b',
                      lambda m: str(parse_number(m.group(1))) + ' ' + m.group(2),
                      text, flags=re.I)
    return re.sub(r'(\d+/\d+)(?:ths?|rds?|nds?|st)\b', r'\1', text, flags=re.I)
