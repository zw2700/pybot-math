"""Whether their money is enough: a price read against the price band the answer named.

"is that enough" is about an amount the person gave, and the answer that priced the thing has the
figure in it. Money is the amount people ask it about most, and the one the answer writes as a
band of prices rather than a number to reach:

    what coat should i get for winter
    -> Pick the coat by the weather you are actually out in: ... £80 to £150 buys a padded coat
       that lasts a decade, £150 to £250 a waterproof shell that does not leak at the shoulders.
    i have 80 pounds, is that enough
    -> £80 is inside the £80 to £150 that answer named, and that buys a padded coat that lasts a
       decade.

    i have 200 pounds to spend on a bike
    -> £400 to £700 buys a dependable new commuter, and £150 to £300 buys a sound second-hand one.
    is that enough
    -> £200 is inside the £150 to £300 that answer named, and that buys a sound second-hand one.

On main those two chats got "I'm not sure about that one, sorry - I'd rather not guess." and
"Alright then - good luck with it.", because the amounts the store reads in
`bot/modules/memory_store.py` (`_AMOUNTS`) are all a unit that follows the count, and a price is
written with the mark in front ("£200") or the word behind ("200 pounds"), so it was in no family
at all and the two numbers were never read together. `bot/modules/memory_store.py` is the module
that answers "is that enough", and it calls `against_the_bands` from there.

Fences, each a test in `tests/test_a_purse_against_the_price_band.py`:

* a band has to hold their money, or be the cheapest one above it - the one they cannot reach;
  money over every band is left to the answer that named them, which usually says what more money
  buys ("£900" after a Rome answer whose best line is the daily cost);
* a band stated as a rate is the cost of a day, not the price of the thing ("£55 to £95 a day per
  person"), so it is passed over;
* the figure can be in the ask ("is 40 pounds enough") or in their own line just before it, and
  the band can be in the answer one turn back, because a line that only says how much they have is
  answered by the store asking what it has to stretch to;
* a price named alone, with no band, is not stood against ("You have 500 pounds for a laptop -
  good, and everything I suggest will be within it");
* only pounds and quid are read, so the reply never puts a pound sign on somebody's euros.
"""
import re

# A price as people write it: the mark in front, the word behind.
_A_MONEY = re.compile(
    r"\u00a3\s*(?P<mark>\d+(?:,\d{3})*(?:\.\d+)?)"
    r"|(?P<word>\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:pounds?|quid|gbp)\b",
    re.I,
)
# Two prices with a range between them, in either of the ways a price is written. A range of
# figures with no money mark on it is somebody else's amount - a sleep answer's "seven to nine" -
# so the mark or the word has to be on the band for it to be money.
_A_MONEY_BAND = re.compile(
    r"\u00a3\s*(?P<a1>\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:to|and|or|-|\u2013)\s*\u00a3?\s*"
    r"(?P<a2>\d+(?:,\d{3})*(?:\.\d+)?)"
    r"|(?P<b1>\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:to|and|or|-|\u2013)\s*"
    r"(?P<b2>\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:pounds?|quid)\b",
    re.I,
)
# Where the clause a band is written with ends: it says what that band buys ("buys a sound
# second-hand one") and the next band, or the next sentence, is a new clause.
_A_CLAUSE_END = re.compile(r"[.!?;]|\s+-\s+|\u2014|,\s+(?:and|or|but|so)\s+|,\s+")
# A clause that opens with a verb is said of the band ("buys a sound second-hand one"); one that
# does not is a list of what the band is for ("a close friend or a sibling"), and the two are tied
# to the price in different words.
_A_VERB_FIRST = re.compile(
    r"^(?:buys?|covers?|gets?|is|are|was|were|will|goes?|holds?|pays?|takes?|does|fits?|lasts?|"
    r"means|comes?|makes?|gives?|finds?)\b", re.I)
# A band the answer states as a rate is not the price of the thing the person is buying: "Rome is
# about £55 to £95 a day per person" is a daily cost, and a purse of £60 is neither inside it nor
# outside it. Only a band that prices the thing itself is stood against their money.
_A_RATE_BAND = re.compile(
    r"^\s*(?:\(?\s*)?(?:a|per|each|every)\s+(?:day|night|week|month|person|head|hour)\b", re.I)


def _a_number(word):
    """The number a figure stands for, or 0 when it is not one."""
    word = (word or "").strip().lower()
    if re.fullmatch(r"\d+(?:,\d{3})*(?:\.\d+)?", word):
        return float(word.replace(",", ""))
    return 0.0


def _money_in(text):
    """Every price in the line, in the order it was said."""
    found = []
    for match in _A_MONEY.finditer(text or ""):
        value = _a_number(match.group("mark") or match.group("word"))
        if value:
            found.append(value)
    return found


def _the_money(value):
    """A price written the way money is written: "\u00a31,500", "\u00a32.50" - never "\u00a31500.0"."""
    if float(value).is_integer():
        return "\u00a3{:,}".format(int(value))
    return "\u00a3%.2f" % value


def _the_words_after(answer, at):
    """The clause the answer puts after a price band, or "" when it puts none worth repeating."""
    rest = (answer or "")[at:]
    cut = _A_CLAUSE_END.search(rest)
    words = (rest[:cut.start()] if cut else rest).strip(" ,;:-")
    if not words or len(words.split()) > 12:
        return ""
    # Another price in the clause is the next band, and a figure in it is a count, not a thing.
    if "\u00a3" in words or any(re.fullmatch(r"\d[\d,]*\.?\d*", one) for one in words.split()):
        return ""
    return words


def _money_bands(answer):
    """Every price band the answer names: (low, high, the clause it is written with)."""
    bands = []
    for match in _A_MONEY_BAND.finditer(answer or ""):
        first = match.group("a1") or match.group("b1")
        second = match.group("a2") or match.group("b2")
        low, high = _a_number(first), _a_number(second)
        if not (low and high) or low >= high:
            continue
        if _A_RATE_BAND.match((answer or "")[match.end():]):
            continue
        bands.append((low, high, _the_words_after(answer, match.end())))
    return bands


def against_the_bands(text, turns):
    """Where their money stands against the price bands of the last answer, or None.

    The figure is read from the ask first ("is 40 pounds enough"), and from their own lines just
    before it when the ask only says "is that enough". A band that holds their money is the
    answer, said with the clause the answer wrote for that band, so the reply carries what the
    price buys rather than the price twice.
    """
    theirs = _money_in(text)
    if not theirs:
        for turn in reversed(list(turns or [])[-3:]):
            if not isinstance(turn, dict):
                continue
            theirs = _money_in(str(turn.get("user") or ""))
            if theirs:
                break
    if not theirs:
        return None
    mine = theirs[-1]
    # The answer that priced the thing can be the one before the last: a line that only says how
    # much they have ("i have 200 pounds to spend") is answered with the store asking what it has
    # to stretch to, and the band is in the answer above that. Two turns back is as far as the
    # purse is read, so the band is still about the thing they are asking about.
    for turn in reversed(list(turns or [])[-2:]):
        answer = str(turn.get("bot") or "") if isinstance(turn, dict) else ""
        bands = _money_bands(answer)
        if bands:
            break
    else:
        return None
    spoken = _the_money(mine)
    inside = [band for band in bands if band[0] <= mine <= band[1]]
    if inside:
        low, high, after = inside[0]
        said = "%s to %s" % (_the_money(low), _the_money(high))
        if not after:
            return "%s is inside the %s that answer named." % (spoken, said)
        if _A_VERB_FIRST.match(after):
            return "%s is inside the %s that answer named, and that %s." % (spoken, said, after)
        return "%s is inside the %s that answer named: %s." % (spoken, said, after)
    # No band holds it: the cheapest one above their money is what they cannot reach, and saying
    # so is the answer to "is that enough".
    above = sorted((band for band in bands if band[0] > mine), key=lambda band: band[0])
    if not above:
        return None
    return "%s is under the %s that answer named." % (
        spoken, "%s to %s" % (_the_money(above[0][0]), _the_money(above[0][1])))
