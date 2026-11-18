"""One exact grammar for quantities parsed alone or extracted from prose."""
import re
from fractions import Fraction


SMALL = dict(zip(
    'zero one two three four five six seven eight nine ten eleven twelve thirteen '
    'fourteen fifteen sixteen seventeen eighteen nineteen'.split(), range(20)))
TENS = dict(zip('twenty thirty forty fifty sixty seventy eighty ninety'.split(), range(20, 100, 10)))
SCALES = {'hundred': 100, 'thousand': 1000, 'million': 1000000, 'billion': 1000000000}
_ONES = r'(?:' + '|'.join(word for word, value in SMALL.items() if 0 < value < 10) + r')'
_UNDER100 = (r'(?:(?:' + '|'.join(TENS) + r')(?:[ -]+' + _ONES + r')?|'
             + '|'.join(sorted(SMALL, key=len, reverse=True)) + r')')
_GROUP = r'(?:' + _ONES + r'[ -]+hundred(?:[ -]+(?:and[ -]+)?' + _UNDER100 + r')?|' + _UNDER100 + r')'
_WORD_NUMBER = _GROUP + r'(?:[ -]+(?:billion|million|thousand)(?:[ -]+(?:and[ -]+)?' + _GROUP + r')?)*'
_DIGIT = r'(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)'
_SCALED_DIGIT = _DIGIT + r'[ -]+(?:' + '|'.join(SCALES) + ')'
_CARDINAL = r'(?:' + _SCALED_DIGIT + '|' + _DIGIT + '|' + _WORD_NUMBER + ')'

# English ordinal spelling is regular apart from these stems. "Second" alone
# is not a denominator: a count of seconds denotes time, not halves.
_IRREGULAR = {'one': 'first', 'two': 'second', 'three': 'third', 'five': 'fifth', 'eight': 'eighth',
              'nine': 'ninth', 'twelve': 'twelfth'}
_ORDINALS = {
    _IRREGULAR.get(word, word[:-1] + 'ieth' if word.endswith('y') else word + 'th'): word
    for word, value in dict(SMALL, **TENS, **SCALES).items() if value > 0
}
FRACTIONS = {word: dict(SMALL, **TENS, **SCALES)[cardinal]
             for word, cardinal in _ORDINALS.items() if cardinal not in ('one', 'two')}
FRACTIONS.update({word + 's': value for word, value in list(FRACTIONS.items())})
FRACTIONS.update({'half': 2, 'halves': 2, 'quarter': 4, 'quarters': 4})
_ORDINAL = r'(?:' + '|'.join(sorted(_ORDINALS, key=len, reverse=True)) + r')'
_SIMPLE_DENOMINATOR = r'(?:' + '|'.join(word for word in _ORDINALS if word not in ('first', 'second')) + ')'
_ORDINAL_DENOMINATOR = r'(?:(?:' + _WORD_NUMBER + r')[ -]+(?:and[ -]+)?' + _ORDINAL + '|' + _SIMPLE_DENOMINATOR + ')'
_DENOMINATOR = r'(?:halves|half|quarters?|' + _ORDINAL_DENOMINATOR + 's?)'
_BARE_FRACTION = r'(?:half|halves|thirds?|quarters?|fourths?)'
# Singular ordinals describe labels ("64 seventh graders"); a fraction uses
# a unit numerator or a plural denominator. Digit counts of halves/quarters
# are ambiguous object counts, so only explicit ordinal denominators join them.
_WORD_FRACTION = (r'(?:(?:' + _WORD_NUMBER + r')[ -]+(?:halves|quarters|' + _ORDINAL_DENOMINATOR + r's)|'
                  + _DIGIT + r'[ -]+' + _ORDINAL_DENOMINATOR + r's|'
                  + r'(?:one|1|an?)[ -]+' + _DENOMINATOR + '|' + _BARE_FRACTION + ')')
_SLASH_FRACTION = r'\d+\s*/\s*\d+(?:st|nd|rd|th)?'
_FRACTION = r'(?:' + _SLASH_FRACTION + '|' + _WORD_FRACTION + ')'
_MIXED = _CARDINAL + r'(?:\s+and\s+' + _FRACTION + r'|\s+' + _SLASH_FRACTION + ')'
_VALUE = r'(?:' + _MIXED + '|' + _FRACTION + '|' + _CARDINAL + ')'
_PREFIX = r'(?:[+-]?(?:[$£€]\s*)?|[$£€]\s*[+-])'
_PERCENT = r'(?:%|percent\b|per\s+cent\b)'
_ORDINAL_LABEL = r'(?:(?:' + _WORD_NUMBER + r')[ -]+(?:and[ -]+)?)?' + _ORDINAL + r'(?!\w)'
TOKEN = re.compile(r'(?<!\w)' + _PREFIX + '(?:' + _ORDINAL_LABEL + '|' + _VALUE + r')(?:\s*' + _PERCENT + r')?(?!\d)', re.I)
_FULL = re.compile(_PREFIX + _VALUE + r'(?:\s*' + _PERCENT + r')?', re.I)
_PARTS = re.compile(r'(' + _CARDINAL + r'|an?)[ -]+(' + _DENOMINATOR + ')', re.I)
_MIXED_PARTS = re.compile(r'(' + _CARDINAL + r')(?:\s+and\s+|\s+(?=\d+\s*/))(' + _FRACTION + ')', re.I)


def _cardinal(text):
    if re.fullmatch(_DIGIT, text):
        return Fraction(text.replace(',', ''))
    if re.fullmatch(_SCALED_DIGIT, text):
        coefficient, scale = re.split(r'[ -]+', text)
        return Fraction(coefficient.replace(',', '')) * SCALES[scale]
    if not re.fullmatch(_WORD_NUMBER, text):
        raise ValueError('Not a cardinal number')
    total, group, previous_scale = 0, 0, max(SCALES.values()) + 1
    for word in text.replace('-', ' ').split():
        if word == 'and':
            continue
        if word in SMALL:
            group += SMALL[word]
        elif word in TENS:
            group += TENS[word]
        elif word == 'hundred':
            group *= 100
        elif word in SCALES:
            scale = SCALES[word]
            if scale >= previous_scale:
                raise ValueError('Number scales must descend')
            total += group * scale
            group, previous_scale = 0, scale
    return Fraction(total + group)


def _denominator(text):
    if text in FRACTIONS:
        return FRACTIONS[text]
    words = text.replace('-', ' ').split()
    words[-1] = _ORDINALS[words[-1].rstrip('s')]
    return _cardinal(' '.join(words))


def _fraction(text):
    if re.fullmatch(_SLASH_FRACTION, text):
        numerator, denominator = text.split('/')
        return Fraction(int(numerator), int(re.sub(r'(?:st|nd|rd|th)$', '', denominator)))
    parts = _PARTS.fullmatch(text)
    if parts:
        numerator, denominator = parts.groups()
        numerator = Fraction(1) if numerator in ('a', 'an') else _cardinal(numerator)
        return numerator / _denominator(denominator)
    return Fraction(1, FRACTIONS[text])


def parse_number(text):
    """Parse one complete quantity; reject incomplete or malformed numbers."""
    clean = text.lower().strip()
    if not _FULL.fullmatch(clean):
        raise ValueError('Not a number')
    percent = re.search(_PERCENT + r'$', clean)
    if percent:
        clean = clean[:percent.start()].rstrip()
    clean = re.sub(r'[$£€]\s*', '', clean)
    sign = -1 if clean.startswith('-') else 1
    clean = clean.lstrip('+-')
    mixed = _MIXED_PARTS.fullmatch(clean)
    if mixed:
        whole, part = mixed.groups()
        value = _cardinal(whole) + _fraction(part)
    elif re.fullmatch(_FRACTION, clean):
        value = _fraction(clean)
    else:
        value = _cardinal(clean)
    return sign * value / (100 if percent else 1)
