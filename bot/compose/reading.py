"""A number offered into a thread the bot has just answered.

People answer the bot's advice with the reading they are looking at: "i think my boiler pressure
is low" gets "top the pressure up to between 1 and 1.5 bar", and the next line is "the gauge says
0.5". Main said that line back ("Got it - the gauge says 0.5"), which repeats it and tells no one
anything: the person is holding a number and wants to know whether it is the number.

The answer they are asking about is usually in the bot's own last line, because knowledge entries
state the range somewhere in it ("between 1 and 1.5 bar", "between 0 and 5C", "16-18C"). So this
reads the number, reads the range out of the answer just given, and says which way it is off,
with the step the answer already gave. It answers only a line that is nothing but a reading and
that follows a knowledge answer which really states a range - everything else goes to the modules
that know better.
"""
import re

from ..memory import topics as _topics
from . import verdict as _verdict


# A number, written the way a person writes one off a gauge or a dial: "0.5", "1.5", "8", "39.4",
# "-18". A year is not a reading ("in 1998"), and neither is a number that is part of a date or a
# price, so those are excluded before the reading is read.
NUMBER = re.compile(r"(?<![\w.,])(-?\d+(?:\.\d+)?)(?!\d|[.,]\d)")
# The unit, when the person names one. "the gauge says 0.5" has none, and the answer's own unit
# is what the number is measured in.
UNIT = re.compile(r"(?:\d\s*)?(bar|bars|psi|c|f|celsius|centigrade|degrees|deg|mm|cm|kg|litres?"
                  r"|liters?|ml|watts?|volts?|hours?|hrs?|days?|weeks?|months?|years?|%)\b")
# How a range is written in an answer: "between 1 and 1.5 bar", "1 to 1.5 bar", "0 and 5C",
# "16-18C", "-18 to -20C". The unit is taken from either end, because English puts it once.
RANGE = re.compile(r"(?:between\s+)?(-?\d+(?:\.\d+)?)\s*(?:and|to|--|-|\u2013)\s*(-?\d+(?:\.\d+)?)"
                   r"\s*([a-z%]{1,10})?\b", re.IGNORECASE)
# A unit that makes the range a measurement rather than a count, a time or a price. "3 to 5 days"
# and "20 to 25 minutes" are durations an answer gives, and a number offered into a thread is not
# usually asking to be checked against one.
MEASURED = frozenset(("bar", "bars", "psi", "c", "f", "celsius", "centigrade", "degrees", "deg",
                      "mm", "cm", "kg", "litre", "litres", "liter", "liters", "ml", "watt",
                      "watts", "volt", "volts", "%"))
# The words a line that is only a reading is made of. Anything else in the line is content, and a
# line with content of its own is about something, so it goes to the modules that read it.
CARRIED = frozenset((
    "i", "im", "it", "its", "it's", "the", "my", "we", "is", "was", "were", "are", "be", "been",
    "says", "say", "said", "reads", "read", "shows", "shown", "showing", "gives", "gave", "gets",
    "has", "have", "had", "at", "about", "around", "roughly", "now", "still", "only", "just",
    "currently", "currently", "down", "up", "to", "of", "on", "in", "a", "an", "and", "but",
    "actually", "today", "tonight", "this", "morning", "afternoon", "evening", "gauge", "dial",
    "meter", "thermometer", "display", "screen", "number", "reading", "there", "that", "then",
    "so", "or", "they", "she", "he", "here", "sitting", "sits", "hovering", "by", "from", "door",
    "shelf", "fridge", "freezer", "boiler", "pressure", "temp", "temperature", "room", "house",
    "car", "tyre", "tyres", "tire", "tires", "oven", "probe", "water", "bar", "bars",
    "psi", "c", "f", "deg", "degree", "degrees", "centigrade", "celsius", "mm", "cm", "kg",
    "litre", "litres", "ml", "watt", "watts", "volt", "volts",
))
# A line that is asking something is not a reading being offered.
QUESTION = re.compile(r"\?|\b(?:should|shall|is it|is that|do i|does it|what|why|how|which|"
                      r"when|where|would|could|can)\b")


def _number(clean):
    """(value, unit) for a line that is nothing but a reading, or None."""
    if QUESTION.search(clean):
        return None
    found = NUMBER.findall(clean)
    if len(found) != 1:
        return None
    words = re.findall(r"[a-z']+", clean)
    if not words:
        return None
    for word in words:
        if word not in CARRIED:
            return None
    unit = UNIT.search(clean)
    return float(found[0]), (unit.group(1) if unit else "")


def _range(said):
    """(low, high, unit) for the first measured range in the answer, or None."""
    for found in RANGE.finditer(str(said or "")):
        low, high, unit = found.group(1), found.group(2), (found.group(3) or "").lower()
        if unit in MEASURED:
            low, high = float(low), float(high)
            if low == high:
                continue
            return (low, high, unit) if low < high else (high, low, unit)
    return None


def _say(value):
    """A number as a person writes it: 0.5 stays 0.5, 1.0 is 1."""
    return ("%g" % value)


def _unit(unit):
    """The unit as it is written: "1 to 1.5 bar", "0 to 5C"."""
    if not unit:
        return ""
    if unit in ("c", "celsius", "centigrade"):
        return "C"
    if unit == "f":
        return "F"
    if unit in ("deg", "degree", "degrees"):
        return " degrees"
    return " " + unit


# A count the answer wrote in words. The answers write their ranges in words as often as in
# digits ("most back pain settles in two to six weeks"), and read in digits only an answer like that
# held no range at all: "how long does back pain last" / "is that too long" came back with the
# paragraph again, and the one about bruising came back with the health guard's "Not one I can call
# for you, sorry".
NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90,
}
# Longest first, and closed with a boundary: "twelve to sixteen weeks" was read as "twelve to six"
# with "teen" left over, and that came back as a range of "12 to 6 teen".
WORD_NUMBERS = "|".join(sorted(NUMBER_WORDS, key=len, reverse=True))
# Case does not matter to this one, and it must not: an answer that leads with its range writes "One
# to two weeks for a bruise to fade", and read in lower case only that answer held no range.
WORD_RANGE = re.compile(r"(?:between\s+)?\b(" + WORD_NUMBERS + r")\b\s*"
                        r"(?:and|to|\u2013|-)\s*(" + WORD_NUMBERS + r")\b"
                        r"\s*([a-z%]{1,10})?\b", re.I)


def _word_number(word):
    """A count the answer wrote in words, or None."""
    text = str(word or "").lower()
    return float(NUMBER_WORDS[text]) if text in NUMBER_WORDS else None


# A range of more than one takes the plural, because the answer often writes the unit once and the
# reply quotes it back: "two to five, an hour of good programmes a day" came out as "2 to 5 hour".
PLURALS = {"hour": "hours", "minute": "minutes", "day": "days", "week": "weeks",
           "month": "months", "year": "years", "mile": "miles", "litre": "litres",
           "liter": "liters", "gram": "grams", "calorie": "calories", "step": "steps",
           "hr": "hrs", "min": "mins"}


def _plural(unit, high):
    """The unit as a range of that many of it is written."""
    if high is None or high <= 1:
        return unit
    return PLURALS.get(unit, unit)


# The words that follow a range without naming what it counts: "9 to 10 for hard boiled", "2 to 3
# of them". A range followed by one of these borrows the answer's own unit.
STOP_AFTER = frozenset((
    "for", "of", "a", "an", "the", "in", "to", "and", "or", "at", "on", "with", "but",
    "so", "if", "when", "which", "that", "is", "are", "it", "you", "we", "they", "per",
    "each", "roughly", "about", "around", "plus", "max", "maximum", "minimum", "more",
    "less", "up", "down", "off", "out", "from", "by", "as", "than", "then", "there",
    "this", "these", "those", "his", "her", "their", "your", "my", "our", "its",
))


def _usual_unit(text, before=None):
    """The one measurement the answer keeps using, for a range it wrote without one.

    Only a unit the answer has already used counts (`before` is where the range sits). A unit that
    first appears after the range may belong to another figure: "two to five, an hour of good
    programmes a day" is a range of ages, and borrowing the "an hour" that follows it made it "2
    to 5 hours" of screen time.
    """
    counts = {}
    # From a word boundary, or the "g" of a gauge unit is found in every "boiling" and "peeling"
    # in the answer, and a range of minutes came out as a range of grams.
    for found in re.finditer(r"\b" + DOUBT_UNIT.pattern, str(text or "").lower()):
        if before is not None and found.start() > before:
            continue
        unit = UNIT_ALIAS.get(found.group(1), found.group(1))
        if unit and unit not in MONEY_WORDS:
            counts[unit] = counts.get(unit, 0) + 1
    if not counts:
        return ""
    return max(counts, key=lambda unit: counts[unit])


def _add_measured(spans, low, high, unit, usual, at=None, matched=""):
    """Add one measured span, taking the answer's own unit when the range did not name one."""
    if low is None or high is None:
        return
    if unit not in DOUBT_UNITS:
        unit = usual if usual in DOUBT_UNITS else ""
    if not unit:
        return
    if low == high:
        return
    low, high = min(low, high), max(low, high)
    span = {"low": low, "high": high, "mark": "", "money": False, "unit": unit,
            "text": "%s to %s%s" % (_say(low), _say(high), _unit(_plural(unit, high)))}
    if at is not None:
        span["at"] = at
        span["end"] = at + len(matched) if matched else at
    spans.append(span)


def _same_measure(left, right):
    """True when two unit words measure the same thing (a bar is a bar, a degree is a degree)."""
    warm = frozenset(("c", "celsius", "centigrade", "deg", "degree", "degrees"))
    cold = frozenset(("f", "fahrenheit"))
    span = frozenset(("deg", "degree", "degrees"))
    for group in (warm, cold, span):
        if left in group and right in group:
            return True
    return left[:3] == right[:3]


def _where(value, low, high, unit):
    """Which side of the range the reading is on."""
    if value < low:
        return "below"
    if value > high:
        return "above"
    return "inside"


def _step(said):
    """The first thing the answer told them to do, in the answer's own words."""
    try:
        return _verdict._step(said)
    except Exception:  # noqa: BLE001 - a missing step is not a reason to drop the reading
        return None


# A bare reading shares few words with the entry's keys ("it says 8" after a fridge answer shares
# none), so the answer behind it is read straight from the last turn when that answer was a
# knowledge one and the line is no more than a handful of reading words.
SHORT = 6


def _said(memory, clean):
    """The answer this reading is about: the entry answer the line points at, or the last one."""
    text = _topics.entry_answer(memory, clean)
    if text:
        return str(text)
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns:
        return ""
    last = turns[-1] if isinstance(turns[-1], dict) else {}
    if last.get("module") != "answers":
        return ""
    if len(re.findall(r"[a-z']+", clean)) > SHORT:
        return ""
    said = str(last.get("bot") or "")
    record = memory.get("entry_answer") or {}
    kept = str((record or {}).get("text") or "")
    if kept and not (" ".join(kept.lower().split()[:6]) in " ".join(said.lower().split())):
        return ""
    return said


# An age, said in the words people say it in. Only the first person: "she is 11" is about a
# child and is read by the other readers; this is the person writing about themselves.
AN_AGE = re.compile(
    r"^(?:i'?m|im|i am|ive|i've|i just turned|i turned)\s+\d{1,3}"
    r"(?:\s*(?:years?|yrs?)(?:\s+old)?)?(?:\s+(?:now|this year))?\s*[.!]?$", re.I)


# ------------------------------------------------------------------------------- a figure judged

# A line that only asks whether a figure is a lot, enough or about right: "is that a lot" after a
# quote, "is £2,400 too much", "is 12 a lot" after the hours a child needs, "is 1.5 bar a lot".
# The line names no subject of its own - "that" is whatever the bot has just told them - so the
# subject is the figure, and the yardstick is the range in the answer just given. The answer is
# not invented: it is the comparison with the bot's own range, quoted back, which is the thing the
# person cannot do in their head. A line with no figure, or an answer with no range, is passed on
# rather than guessed at.
LEADING = ("and", "so", "but", "ok", "okay", "alright", "well", "hmm", "umm", "er")
ASKS = frozenset(("is", "was", "were", "are", "would", "will", "does", "do", "did", "should"))
SUBJECTS = ("that", "this", "it", "there", "they", "those")
# What the doubt itself is called. "a lot" and "too much" are the same question from the other
# side, and "enough" is the one that is about a floor rather than a ceiling.
# The doubt words that are only ever about money: a person asking "is that expensive" wants a
# price judged, and a span of years or hours in the answer is not the thing they asked about. The
# deck has "i need a new tyre" / "is that expensive" answered "what figure have you got? the usual
# is 5 to 6 years", which asks for a price against a lifespan.
MONEY_DOUBTS = frozenset((
    "a good price", "a fair price", "a good deal", "expensive", "cheap", "steep",
    "on the high side", "on the low side", "about the going rate", "the going rate",
))
QUANTITY_WORDS = frozenset((
    "a lot", "much", "too much", "too high", "too low", "too little", "about right",
    "about average", "enough", "a good price", "a fair price", "a good deal", "expensive",
    "cheap", "steep", "on the high side", "on the low side", "over the top",
    "about the going rate", "the going rate",
    # "is that average", "is that above average": the same question asked against the middle of
    # the range rather than against the range. Which side it reads as is the figure's job.
    "average", "above average", "below average",
    # A length asked about from one end is the same question as a price asked about from the top:
    # "how long does back pain last" / "is that too long" is a doubt about the answer's own stretch
    # of time. The two words are kept apart from the rest because the side of the range a figure is
    # on says something different for each: a figure over the usual is too long, and one under it is
    # not too short.
    "too long", "too short",
))
# The two doubts that are about a stretch of time rather than a figure: "is that too long" and "is
# that too short". Nothing in the memory store reads them.
TIME_DOUBT = frozenset(("too long", "too short"))
# "is that ok" is the same shape but not the same question: it asks whether the advice stands,
# which is the composer's own verdict (`bot/compose/verdict.py`), so it is a doubt about a figure
# only when the person has named one.
# "is that fair" and "is that right" are the same doubt in the words people use most, and neither
# was read: "the man quoted 250" / "is that fair" was answered with the boiler card again, because
# "fair" is not in the list of quantities and the answers module still had the question it had
# already answered. Both only claim a line when a figure is in hand and an answer gave a range to
# hold it against, so "is that fair" about a rota, with no figure, is left where it was.
DOUBT_WORDS = QUANTITY_WORDS | frozenset(("normal", "reasonable", "ok", "okay", "fine", "fair",
                                          "right"))
# The doubt words that are a whole line on their own ("a bit much", "too much?"). The ones left out
# are a nod back ("ok", "fine", "normal") or a comparison that needs its own verb ("about average"),
# and those are the conversation's, not a figure's.
BARE_DOUBTS = QUANTITY_WORDS - {"much", "about average"}
# The same doubt in the other words people use, mapped to the doubt word it is. Each one is read
# only after the verb at the front of the line, so a word here is never claimed on its own.
WORD_ALIAS = {
    # The degree said on the word: "too dear", "a bit much", "quite a lot".
    "too expensive": "expensive", "too dear": "expensive", "too pricey": "expensive",
    "too cheap": "cheap", "a bit much": "too much", "bit much": "too much",
    "a bit steep": "steep", "a bit dear": "expensive", "a bit pricey": "expensive",
    "a bit expensive": "expensive", "quite a lot": "a lot", "loads": "a lot",
    "loads of money": "a lot",
    # Being charged over the odds, in the words people use for it: "is that overpriced",
    # "am i being ripped off", "did i get done".
    "overpriced": "expensive", "pricey": "expensive", "dear": "expensive",
    "a rip off": "expensive", "rip off": "expensive", "ripoff": "expensive",
    "a ripoff": "expensive", "ripped off": "expensive", "ripping me off": "expensive",
    "get ripped off": "expensive", "got ripped off": "expensive", "i get ripped off": "expensive",
    "i got ripped off": "expensive", "i was ripped off": "expensive",
    "i am being ripped off": "expensive", "overcharged": "expensive",
    "overcharging me": "expensive", "i was overcharged": "expensive",
    "been overcharged": "expensive", "get overcharged": "expensive",
    "get done": "expensive", "i got done": "expensive", "overpaying": "expensive",
    "paying too much": "too much", "over the odds": "expensive", "a con": "expensive",
    "excessive": "too much", "unreasonable": "too much", "exorbitant": "too much",
    "having a laugh": "expensive", "taking the mick": "expensive", "having me on": "expensive",
    "daylight robbery": "expensive", "a joke": "expensive",
    # The comparison and the price-fairness shapes: the same doubt asked about the middle of the
    # range rather than about the top. "right" on its own is deliberately not here - "is that
    # right" is a check of what the bot just said, and the module that answers a check owns it.
    "how does that compare": "about right", "in the ballpark": "about right",
    "in line": "about average", "in line with what youd expect": "about average",
    "in line with what youd pay": "about average", "the normal price": "about average",
    "normal price": "about average", "a normal price": "about average",
    "price about right": "about right", "what it should cost": "about right",
    "sound about right": "about right", "sounds about right": "about right",
    "look about right": "about right", "looks about right": "about right",
    "cost that much": "too much", "that much": "too much", "this much": "too much",
    # A figure with the person's own word for where it sits: "60 seems high", "45 feels low".
    # Which side it is, is the figure's job.
    # The same "is it a lot" in the words that mean "no complaint": "is 8 pounds acceptable for a
    # cinema ticket" and "is 4 pounds alright for a chicken" were read as a line with no doubt in
    # it, so the price question went to whichever card named the subject - the minutes in the oven,
    # or a paragraph about published rates - while the range was one lookup away.
    "acceptable": "about right", "alright": "about right", "all right": "about right",
    "sensible": "about right", "much good": "about right", "fair enough": "about right",
    "high": "too high", "low": "too low",
}
# The words that only say what the doubt is about, so they come off the end before the doubt word
# itself is read: "is that a lot of money", "is that too much to pay".
TAILS = ("really", "then", "though", "to me", "i think", "for that", "for it", "for one",
         "to pay", "to spend",
         "of money", "of it", "like that", "in total", "altogether", "for what it is",
         "for what they are", "for the size of it")
# The tag people hang on the end of a doubt ("bit much isnt it", "expensive isnt it", "too much
# eh"). It is the asking half of the line, not part of what is doubted.
TAG_ASK = re.compile(
    r"[\s,]+(?:is(?:nt|n't)?\s+(?:it|that|this|they)|innit|aint\s+it|eh|"
    r"dont\s+(?:you|ya)\s+think|do\s+you\s+think|wouldnt\s+you\s+say)[\s?!.]*$")
# The thing a figure is for, said in the same line: "is £40 a lot for a haircut", "is 1200 too
# much for a boiler", "is 25 a lot on a hair cut". The doubt then needs no answer before it: the
# range it is judged against is the one the knowledge base gives for that thing, and the person
# has named it themselves. Only a figure they brought with them counts, because "is that a lot
# for a haircut" is holding up a number the reader does not have.
FOR_THE_THING = re.compile(
    r"\s+(?:for|on)\s+(?P<thing>(?:(?:a|an|the|my|our) )?[a-z][a-z' -]{1,40})$", re.I)
# A price the knowledge base writes as a range: "A cut is usually £15 to £35 in a salon".
FOR_THE_ARTICLE = re.compile(r"^(?:a|an|the|my|our) ", re.I)
# Words that point back at something already said instead of naming it: the subject of "for a
# new one" is the thing in the answer above, and its range is the one to judge the figure by.
POINTING_AT_SOMETHING = frozenset((
    "one", "ones", "them", "it", "that", "this", "those", "these", "same",
))
POINTING_ONE = re.compile(r"\b(?:one|ones)$")
# A number at the front of the line, which is how the figure arrives when the person quotes it:
# "is 12 a lot", "is £2,400 too much", "is 1.5 bar about right".
FIGURE = re.compile(r"(?:(?P<mark>[£$€])\s?)?(?P<number>\d[\d,]*(?:\.\d+)?)")
# The units a doubt can be judged in. A reading is a measure, money is a price, and the hours a
# child sleeps are a stretch of time - all three are figures a person holds up against a range
# the answer gave. ("5 to 10 minutes" as a step is not: the person is not asking whether 12
# minutes of stirring is a lot.)
DOUBT_UNITS = frozenset((
    "bar", "bars", "psi", "c", "f", "celsius", "centigrade", "degrees", "deg", "mm", "cm", "kg",
    "g", "grams", "litre", "litres", "liter", "liters", "ml", "watt", "watts", "volt", "volts",
    "%", "hour", "hours", "hr", "hrs", "minute", "minutes", "min", "mins", "day", "days",
    "week", "weeks", "month", "months", "year", "years", "mile", "miles", "km", "kcal",
    "calories", "steps", "degrees",
))
# The doubts that place a figure in a range ("is that too low", "is that a lot", "is that on the
# low side"). "is that enough" and "is that normal" are about the thing itself, and the memory store
# reads the figure that came with them, so the answer's own turn is not read for those: "i drink 2
# litres of water a day" is the store's figure and not one to place.
PLACES_A_FIGURE = QUANTITY_WORDS - {"enough"}

# A gauge reading is never a bare number: a temperature ("55 to 60C") or a pressure ("1 to 1.5
# bar") is a property of the thing, not an amount the person is holding up, so a bare number is
# not placed against one. "my heating bill was 200 a month" then "is that too much" came back
# "Yes, a bit much - 55 to 60C is the usual." A figure the person gave in a unit of its own ("is 1
# bar a lot", "my boiler pressure is 0.4 bar") is read by the unit branch, which is untouched.
A_GAUGE_UNIT = frozenset((
    "c", "f", "celsius", "centigrade", "deg", "degree", "degrees", "bar", "bars", "psi"))

# The unit the doubt's own figure is in, when it names one: "is 80 pounds a lot", "is 8000 steps
# enough", "is 1.5 bar a lot". Money is a unit here too - the answers write a price either way -
# and the unit words `UNIT` does not need (the readings it reads are gauges) are here.
PER_UNIT = re.compile(r"(?:an?|per|each)\s+(?=(?:bar|psi|degrees?|hours?|hrs?|minutes?|mins?|"
                        r"days?|weeks?|months?|years?|miles?|km|kilos?|kg|litres?|steps)\b)")
DOUBT_UNIT = re.compile(
    r"(bar|bars|psi|c|f|celsius|centigrade|degrees|deg|mm|cm|kg|kilos?|kilograms?|grams?|g|"
    r"stone|stones|lb|lbs|litres?|liters?|ml|pints?|watts?|volts?|%|hours?|hrs?|minutes?|mins?"
    r"|days?|weeks?|months?|years?|miles?|km|k|kcal|calories?|steps|pounds?|quid|dollars?|"
    r"euros?|bucks?|pence)\b")
# The ways people write the same unit, so a figure named in one is judged against a range in the
# other: "3k" against "3 km", "90 kilos" against "80 to 95 kg".
UNIT_ALIAS = {"kilo": "kg", "kilos": "kg", "kilogram": "kg", "kilograms": "kg", "k": "km",
              "stone": "stone", "stones": "stone", "lb": "lb", "lbs": "lb", "pint": "pints"}
MONEY_WORDS = frozenset(("pound", "pounds", "quid", "dollar", "dollars", "euro", "euros",
                         "buck", "bucks", "pence"))
# A price range as the answers write it: "£1,800 to £3,000", "£45-£80", "usually 50 to 80 pounds".
# A range with neither a mark nor a money word on it is a measure or a stretch of time, not a
# price, so it is left to the measured range below.
MONEY_RANGE = re.compile(
    r"(?:(?P<mark>[£$€])\s?)?(?P<low>\d[\d,]*(?:\.\d+)?)\s*"
    r"(?:to|and|\u2013|-|--)\s*(?:(?P<mark2>[£$€])\s?)?(?P<high>\d[\d,]*(?:\.\d+)?)"
    r"\s*(?P<word>" + "|".join(sorted(MONEY_WORDS)) + r")?\b")
# A year is not a figure somebody asks to have judged ("is 1998 a lot"), and neither is a figure
# that is the age they just said ("im 52" / "is that ok").
YEAR = 1900
NEXT_YEAR = 2100


def _the_figure_in_the_doubt(rest):
    """(value, money, unit, rest) for a figure and its unit at the front of a doubt, if any.

    "12 a lot", "£2,400 too much", "1.5 bar about right", "8000 steps enough".
    """
    found = FIGURE.match(rest)
    if not found:
        return None, False, "", rest, False
    value = float(found.group("number").replace(",", ""))
    rest = rest[found.end():].strip()
    unit = ""
    # "is 45 an hour normal", "is 90 a month a lot": the unit is said with an article, and the
    # figure is a rate rather than a measure ("120 a month" is not 120 months).
    rate = bool(PER_UNIT.match(rest))
    if rate:
        rest = rest[PER_UNIT.match(rest).end():].strip()
    measured = DOUBT_UNIT.match(rest)
    if measured:
        unit = measured.group(1).lower()
        unit = UNIT_ALIAS.get(unit, unit)
        rest = rest[measured.end():].strip()
    money = bool(found.group("mark"))
    if unit in MONEY_WORDS:
        money, unit, rate = True, "", False  # "is 80 pounds a lot" is a price
    return value, money, unit, rest, rate


def _doubt(text):
    """The doubt in a line that only asks whether a figure is a lot or enough, else None.

    {"word": "a lot", "value": 2400.0 or None, "money": bool, "unit": "bar" or ""}
    """
    line = " ".join(str(text or "").lower().split()).strip(" ?!.,;")
    # A greeting in front of the doubt is how people open a message: "hiya, is 1200 a lot for a
    # boiler" was a search hedge for a figure the answer is one lookup away.
    line = re.sub(r"^(?:(?:good )?(?:hi|hiya|hey|hello|morning|afternoon|evening|yo)\b[ ,!.]*)+",
                  "", line)
    line = re.sub(r"^(?:(?:and|so|but|ok|okay|alright|well|hmm|umm|er)[ ,]+)+", "", line)
    line = TAG_ASK.sub("", line).strip(" ?!.,;")
    # "60 seems high", "45 feels steep to me": the person's own figure with their own doubt on it,
    # said as an impression rather than asked. It is the same question, so it is read as one - the
    # figure at the front, the asking put back in front of it.
    impression = re.match(r"(?P<figure>[£$€]?\s?\d[\d,]*(?:\.\d+)?)\s+"
                          r"(?:seems|seemed|feels|felt|looks|sounds)\s+(?P<rest>\S.*)$", line)
    if impression:
        line = "is %s %s" % (impression.group("figure").replace(" ", ""),
                             impression.group("rest").strip())
    # The figure first and the doubt after it: "4 pounds for a chicken is that a lot", "80 is that
    # too much", "30 quid for a haircut is that reasonable". The same question with its parts in
    # the other order, so it is rebuilt as one - and the rebuild is what the range is looked up
    # for. A figure followed by a period is a rate ("20 a month is that a lot") and is left alone,
    # because "for a month" is not a thing to price.
    turned = re.match(r"(?P<figure>[£$€]?\s?\d[\d,]*(?:\.\d+)?)\s*(?:pounds?|quid|euros?|"
                      r"dollars?)?\s*(?:for\s+(?!a\s+(?:day|week|month|year|hour)\b)"
                      r"(?P<thing>[a-z][\w' ]{0,40}?))?\s*[-,]?\s*(?:is|was|would)\s+"
                      r"(?:that|this|it)\s+(?P<word>a lot|too much|expensive|reasonable|ok|okay|"
                      r"alright|fine|fair|about right|steep|dear|pricey|cheap)\b", line)
    if turned:
        thing = (turned.group("thing") or "").strip()
        line = "is %s %s%s" % (turned.group("figure").replace(" ", ""), turned.group("word"),
                               (" for " + thing) if thing else "")
    # The same opinion with the figure further along the line: "one bloke said 4200 which seems
    # high". The figure is the value and the word after the verb is the doubt, so nothing has to
    # be rebuilt - it is read here and returned.
    opinion = re.search(r"(?P<figure>[£$€]?\s?\d[\d,]*(?:\.\d+)?)(?P<between>[^0-9]{0,24}?)"
                        r"\b(?:seems|seemed|feels|felt|looks|sounds)\s+(?P<word>"
                        r"high|low|steep|expensive|cheap|dear|pricey|a lot|too much|too high|"
                        r"too low|about right|about average|a rip off|loads)\b", line)
    if opinion:
        word = WORD_ALIAS.get(opinion.group("word"), opinion.group("word"))
        value = float(opinion.group("figure").replace(",", "").replace("£", "")
                      .replace("$", "").replace("€", "").strip())
        money = bool(re.search(r"[£$€]", opinion.group("figure")))
        if word in DOUBT_WORDS and not (
                value is not None and YEAR <= value <= NEXT_YEAR and value % 100
                and not money):
            return {"word": word, "value": value, "money": money, "unit": "", "subject": "",
                    "rate": False}
    # "thats expensive", "its too much", "that is a lot": the copula is said as a statement,
    # which is the same question with the asking left to the tone.
    verb = re.match(r"(?:is|was|were|are|would|will|does|do|did|should|isn'?t|isnt|aren'?t|arent|"
                    r"that's|that is|thats|it's|it is|its|this is|am i being|am i|are they|"
                    r"are we being|have i been|did i)\b", line)
    if not verb:
        # "a bit much", "expensive", "too much" - the doubt said with no verb at all. Only the
        # words that carry a doubt on their own: "ok" and "fine" are a nod, not a question.
        bare = WORD_ALIAS.get(line, line)
        if bare in BARE_DOUBTS:
            return {"word": bare, "value": None, "money": False, "unit": "", "subject": "",
                    "rate": False}
        return None
    rest = line[verb.end():].strip()
    value, money, unit = None, False, ""
    # "thats expensive", "its too much": the line states the doubt instead of asking it, so the
    # thing doubted is left to the conversation and no figure has to be named here.
    stated = verb.group(0) in ("that's", "that is", "thats", "it's", "it is", "its", "this is",
                               "am i being", "am i", "are they", "are we being", "have i been")
    if stated or re.match(r"(?:that|this|it|there|they|those)\b", rest):
        rest = re.sub(r"^(?:that|this|it|there|they|those)\b", "", rest).strip()
        value, money, unit, rest, rate = _the_figure_in_the_doubt(rest) if stated else (
            None, False, "", rest, False)
    else:
        value, money, unit, rest, rate = _the_figure_in_the_doubt(rest)
        # "did i get ripped off", "am i being overcharged": a doubt said after a verb that names no
        # figure. The words that are left are the whole doubt, so the lookup below reads them.
    rest = re.sub(r"^(?:be|being|really|actually|roughly)\s+", "", rest).strip()
    changed = True
    while changed and rest:
        changed = False
        for tail in TAILS:
            if rest.endswith(" " + tail):
                rest = rest[: -len(tail)].strip()
                changed = True
    # The thing the figure is for comes off the end before the doubt word is read: "is £40 a lot
    # for a haircut" holds the same doubt as "is £40 a lot", and it says what to judge it against.
    subject = ""
    for_thing = FOR_THE_THING.search(rest)
    if for_thing and value is not None:
        thing = " ".join(for_thing.group("thing").strip().lower().split())
        short_thing = FOR_THE_ARTICLE.sub("", thing)
        if short_thing not in POINTING_AT_SOMETHING and not POINTING_ONE.search(short_thing):
            # "is 300 quid a lot for a new one" points at a thing spoken about already, and the
            # thing it points at is the answer above it, so it is left to be judged on that.
            subject = thing
        rest = rest[: for_thing.start()].strip()
    rest = WORD_ALIAS.get(rest, rest)
    if rest not in DOUBT_WORDS:
        return None
    if (value is not None and YEAR <= value <= NEXT_YEAR and value % 100
            and not money and not unit):
        return None  # a year is not a figure anybody asks to have judged ("is 1998 a lot")
    return {"word": rest, "value": value, "money": money, "unit": unit,
            "subject": subject, "rate": rate}


def _doubt_ranges(said):
    """(money, measured) spans the answer states, each a dict of its two ends and its own words.

    An answer often holds more than one ("raw chicken keeps 1 to 2 days, cooked chicken 3 days",
    "£1,800 to £3,000, and £3,000 to £4,500 with the pipework"), so every range is kept and the
    one the figure falls in is the one it is judged against.
    """
    text = str(said or "")
    money, measured = [], []
    for found in MONEY_RANGE.finditer(text):
        if not (found.group("mark") or found.group("mark2") or found.group("word")):
            continue  # a range with no money on it is a measure or a stretch of time
        low = float(found.group("low").replace(",", ""))
        high = float(found.group("high").replace(",", ""))
        if low == high:
            continue
        low, high = min(low, high), max(low, high)
        mark = found.group("mark") or found.group("mark2") or "£"
        money.append({"low": low, "high": high, "mark": mark, "money": True, "unit": "",
                      "at": found.start(),
                      "text": "%s to %s" % (_money(low, mark), _money(high, mark))})
    for found in RANGE.finditer(text):
        unit = (found.group(3) or "").lower()
        if unit not in DOUBT_UNITS:
            continue
        low = float(found.group(1).replace(",", ""))
        high = float(found.group(2).replace(",", ""))
        if low == high:
            continue
        low, high = min(low, high), max(low, high)
        measured.append({"low": low, "high": high, "mark": "", "money": False, "unit": unit,
                         "at": found.start(), "end": found.end(),
                         "text": "%s to %s%s" % (_say(low), _say(high), _unit(unit))})
    for found in WORD_RANGE.finditer(text):
        _add_measured(measured, _word_number(found.group(1)), _word_number(found.group(2)),
                      (found.group(3) or "").lower(), _usual_unit(text, found.start()),
                      at=found.start(), matched=found.group(0))
    measured = [span for span in measured if not _an_age(text, span)]
    measured.sort(key=lambda span: span.get("at", 0))
    return money, measured


# "a one to three year old", "kids of 5 to 7 years old": the range is how old somebody is, not how
# long anything lasts, and it is written in the same words a stretch of time is. Read as a stretch,
# "how long does a toddler sleep" (answered "a one to three year old sleeps 11 to 14 hours") then
# "is that too long" was judged against the child's age: "No - 1 to 3 years is the normal spread."
# A range with "old" straight after it is an age and no yardstick for a duration.
AN_AGE_AFTER = re.compile(r"^[\s,|\-]{0,3}(?:years?|months?|weeks?|days?)?\s*olds?\b", re.I)


def _an_age(text, span):
    """True when the range is somebody's age ("one to three year old"), not a stretch of time."""
    end = span.get("end")
    if not isinstance(end, int):
        return False
    return bool(AN_AGE_AFTER.match(text[end:end + 24]))


def _money(value, mark="£"):
    """A price as a person writes it: 2400 is £2,400."""
    body = "{:,}".format(int(value)) if float(value).is_integer() else "{:,.2f}".format(value)
    return "%s%s" % (mark, body)


# The verdicts, in the order the three sides of a range want them. The range is quoted every
# time: it is the whole reason the reply can answer at all, and it is the bot's own facts.
# A doubt that says "too much" or "a lot" is a worry, so a figure inside the range is a No.
# "is 12 a lot" was answered "Yes, that is in the normal range: 11 to 14 hours", which agrees
# with the worry and argues with its own range in the same sentence; "is 120 a lot" after a coat
# answer saying £80 to £150 got the same Yes. The words that ask the question from the other
# side are the ones that need it: "is that about right", "is that a fair price" and "the going
# rate" are already the answer, so they keep the plain one.
TOO_MUCH_WORDS = frozenset(("a lot", "much", "too much", "too high", "expensive", "steep",
                            "over the top", "on the high side"))
ABOUT_RIGHT = (
    "That is about right - {span} is the usual.",
    "That sits inside the {span} that is usual for it.",
    "Right in the usual range: {span}.",
)
NOT_TOO_LITTLE = (
    "No, that is about right - {span} is the usual.",
    "No, you are inside it: the usual is {span}.",
)
NOT_TOO_MUCH = (
    "No, that is about right - {span} is the usual.",
    "No, that is fine: the usual is {span}.",
    "No - {span} is the usual, so you are inside it.",
)
ON_THE_HIGH_SIDE = (
    "That is on the high side: the usual is about {span}.",
    "Yes, a bit much - {span} is the usual.",
)
# The same three sides of the range for a length, where "that is on the low side" answers a worry
# the person does not have: "ive had a cough for 6 days" / "is that too long" got "That is on the
# low side - the usual is about 2 to 3 weeks", which agrees with the range and reads as a fault in a
# cough that is under the usual. A length under the usual is not too long, and one over it is not too
# short.
NOT_TOO_LONG = (
    "No - {span} is the usual, and that is under it.",
    "No, that is short of the usual {span}.",
)
# The figure at the top of the range is not under it, and "not long" said to a length that *is* the
# long end of the usual reads as a fault in the thing that is fine: at 3 weeks in "2 to 3 weeks" the
# person is at the end of the usual, not short of it.
NOT_TOO_LONG_INSIDE = (
    "No, that is inside the usual {span}.",
    "No - {span} is the usual, and that sits inside it.",
)
NOT_TOO_SHORT = (
    "No, that is not too short - {span} is the usual.",
    "No - {span} is the usual, so there is plenty of room there.",
)
ON_THE_LONG_SIDE = (
    "Yes, that is on the long side - the usual is {span}.",
    "Yes, that is longer than the usual {span}.",
)
ON_THE_SHORT_SIDE = (
    "Yes, that is on the short side - the usual is {span}.",
    "Yes, that is shorter than the usual {span}.",
)
# The same side of the range asked from the other end: "is 3500 about right" is not a worry, so a
# figure above the usual is a No. "Yes, a bit much" was said to it, which agrees with a question
# nobody asked.
ABOVE_THE_USUAL = (
    "No, that is on the high side: the usual is about {span}.",
    "No - {span} is the usual, so that is above it.",
)
ENOUGH = (
    "Yes, that is enough - the usual is {span}.",
    "That is plenty: the usual is {span}.",
)
# The low side, asked as a worry, keeps the same Yes the high side gives: "is that too low" wants
# "Yes", and "No, that is under the usual" agrees with nobody. The question has two parts - the
# side the doubt's own word asks about, and the side the figure is on - and the frame answers
# both: "is that too high" at a figure under the range is a No that points the other way, and
# "is that about right" is not a question about a side at all, so a figure under the range is a
# plain No. One frame set for all three said "Yes, a bit low" to "is that too high".
ON_THE_LOW_SIDE = (
    "That is on the low side - the usual is about {span}.",
    "Yes, a bit low - {span} is the usual.",
)
# Asked whether the figure is about right, or about the high side, and it is under the range. The
# frames are the ones the single set already had for these two questions, in the same order, so
# only the "too low" lines change wording: those frames answer them.
THE_LOW_SIDE_FOUND = (
    "That is on the low side - the usual is about {span}.",
    "No, that is under the {span} that is usual.",
)
UNDER_THE_USUAL = (
    "That is a little short - the usual is {span}.",
    "No, that is under the {span} it needs.",
)
MORE_THAN_ENOUGH = (
    "Yes, more than enough - the usual is {span}.",
    "That is plenty: {span} is the usual.",
)


# The words that make a later range a dearer version of the same job rather than a different
# thing: "£1,800 to £3,000, and £3,000 to £4,500 **if** the pipework has to change". Where the
# range that follows is introduced this way, the answer leads with the usual and that is the
# yardstick the person is asking about.
_SAME_JOB = re.compile(r"\b(?:if|when|with|unless|once|where|should)\b", re.IGNORECASE)


# A leading range that prices a day, an hour or a visit is not the price of the whole job, so a
# later range that holds the figure is the job's own price: "a roofer is usually £200 to £300 a
# day... a patch is £150 to £400".
_A_RATE = re.compile(r"^\s*(?:a|an|per|each)\s+(?:day|hour|week|month|visit|year|sq\s?m)\b",
                     re.IGNORECASE)

# The words that say nothing about which tier of a price is meant. Everything else in a range's
# own clause is what that tier is for ("in London", "a flat roof on a garage", "second-hand"), and
# a person who says one of those words has put themselves in that tier.
_SAYS_NOTHING_ABOUT_THE_TIER = frozenset("""
a an the and or but if when with without for of in on at to from by as so also plus than then
is are was were be been being it its this that these those there here his her their your our my
one ones some any more most less much many about around roughly usually normally typically per
each over under near up down out off just only too very quite really still even
""".split())


def _they_named_the_tier(qualifier, mine):
    """Whether the person's own words name what a later range is for ("in London", "a whole roof")."""
    if not mine:
        return False
    spoken = set(re.findall(r"[a-z']+", str(mine).lower()))
    for word in re.findall(r"[a-z']+", str(qualifier or "").lower()):
        if len(word) < 3 or word.isdigit() or word in _SAYS_NOTHING_ABOUT_THE_TIER:
            continue
        if word in spoken or word.rstrip("s") in spoken:
            return True
    return False


def _the_range_for(value, spans, said, mine=""):
    """The range the figure is about among several, or None to keep the answer's leading one.

    An answer often names several prices: some are tiers of the same job ("£1,800 to £3,000, and
    £3,000 to £4,500 if the pipework has to change") and some are different jobs ("a patch is £150
    to £400, a flat roof on a garage £1,500 to £3,000, a whole roof £5,000 to £15,000"). A quote
    that falls in a later *tier* is above the usual, which is the question asked. A quote that
    falls in a range for another job is about that job: "i got quoted 400 to fix the roof" is the
    patch, and read against the roofer's £200 to £300 a day it came back "Yes, a bit much".

    A later range that is *dearer* than the one the answer leads with is a special case of the same
    thing - "£4 to £5.50 in most pubs and £6 to £7.50 in London" - and the answer leads with what
    most people pay, so it wins the figure only when the person's own words put them in it
    ("we're in london this weekend, is 7 a lot") or when the leading range is a rate. A £6 pint
    read against the London price came back "No - £6 to £7.50 is the usual, so you are inside it"
    for somebody who had said nothing about London.
    """
    if value is None or len(spans) < 2:
        return None
    if spans[0]["low"] <= value <= spans[0]["high"]:
        return None  # inside the range the answer leads with: that is the usual being asked about
    text = str(said)
    apart = []
    for place, span in enumerate(spans[1:], 1):
        before = text[spans[place - 1]["at"] + len(spans[place - 1]["text"]):span["at"]]
        end = span["at"] + len(span["text"])
        # Only the words attached to the range itself: the qualifier that makes it a dearer version
        # ("£3,000 to £4,500 with new pipework") trails it, and the next clause is about something
        # else ("£150 to £300 buys a sound second-hand one - a rigid 1990s bike **with** slick
        # tyres is the best value").
        after = text[end:spans[place + 1]["at"] if place + 1 < len(spans) else len(text)]
        after = re.split(r"[.;:!?]| - |\band\b", after, 1)[0]
        # The qualifier that makes a range a dearer version of the same job can come before it
        # ("and £3,000 to £4,500 if the pipework has to change") or after it ("£3,000 to £4,500
        # with new pipework"), so both sides of the range are read.
        if not (_SAME_JOB.search(before) or _SAME_JOB.search(after)):
            apart.append((span, before + " " + after))
    for span, qualifier in apart:
        if not span["low"] <= value <= span["high"]:
            continue
        if (span["high"] > spans[0]["high"] and not _they_named_the_tier(qualifier, mine)
                and not _A_RATE.match(text[spans[0]["at"] + len(spans[0]["text"]):])):
            continue     # a dearer variant of the same thing, and they have not said which one
        return [span]
    return None


def _the_person_words(memory, line=""):
    """The line and the last few things the person said, as one string.

    A later range in an answer can be a special case of the same thing ("£6 to £7.50 in London"),
    and only the person's own words say whether it is their case.
    """
    words = [str(line or "")]
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for turn in list(turns or [])[-3:]:
        if isinstance(turn, dict):
            words.append(str(turn.get("user") or ""))
    return " ".join(words).lower()


def _the_span(doubt, said, mine=""):
    """The span the figure is judged against, or None when the answer states none it can be."""
    money, measured = _doubt_ranges(said)
    # The figure may be bare ("is 12 a lot", "2400" said the turn before), and then the answer
    # decides what it is a figure of: a price range makes it a price, a measured or timed range
    # makes it that. Where the answer holds both, the range the figure falls in is the one meant,
    # and a price is the fallback (a figure somebody asks to have judged after a quote is a quote).
    if doubt["money"]:
        spans = _the_range_for(doubt["value"], money, said, mine) or money
    elif doubt["unit"]:
        # A figure named in a unit is only judged against a range in that same measurement: "is 3
        # days a lot" against an answer about hours is not a comparison at all.
        spans = [span for span in measured if _same_measure(doubt["unit"], span["unit"])]
        if doubt.get("rate"):
            # "is 45 an hour normal" is about the hourly price the answer gave - "lessons are
            # usually £30 to £45 an hour" - not about the 40 to 50 hours somebody needs. A rate
            # is the price the answer put that unit after.
            priced = [span for span in money if re.search(
                re.escape(span["text"]) + r"\s*(?:an?|per|each)?\s*"
                + re.escape(doubt["unit"]) + r"s?\b", said, re.IGNORECASE)]
            if priced:
                spans = priced
    else:
        measured = [span for span in measured if span["unit"] not in A_GAUGE_UNIT]
        # A bare figure ("is 100 enough", "2400") carries no mark and no unit, so the answer
        # decides what it is a figure of - and the answer leads with the thing that was asked
        # about, so the kind whose first range comes earlier in the text is the one it is a
        # figure of. "A proper pair ... fits you for £90 to £130. Replace them every 500 to
        # 800km" is a price first and a distance after, so £100 is a price and is enough; read
        # as measured, it was a hundred kilometres against 500 to 800, and it was "a little
        # short".
        both = sorted(money + measured, key=lambda span: span["at"])
        inside = [span for span in both if doubt["value"] is not None
                  and span["low"] <= doubt["value"] <= span["high"]]
        if inside and money and measured:
            # The answer holds both kinds of range, and the one the figure falls in says what the
            # figure is of: "£2,000 to £3,000 fitted, and a boiler lasts 10 to 15 years" with
            # 3000 in hand is a price, and 12 is the years.
            spans = [inside[0]]
        else:
            # The range the figure falls in is what it is about when it is a range for another
            # job; otherwise a price is the fallback and the answer leads with the thing it was
            # asked about (a figure held up after a quote is a quote).
            spans = _the_range_for(doubt["value"], both, said, mine) or money or measured
        if not money and doubt["value"] is not None and spans and (
                doubt["value"] > spans[0]["high"] * 10
                or doubt["value"] * 10 < spans[0]["low"]):
            # A bare figure only means a measure when it could be one: a price held up after an
            # answer about a boiler's life is not 3000 years.
            return None
    if not spans:
        return None
    # An answer that named several sums of money for different parts of the same thing ("£2,000
    # to £3,000 a year all in: insurance around £500, fuel £80 to £120 a month") is not a yardstick
    # for a figure far below all of them: £900 of insurance is not measured against the £2,000
    # total, and telling them they are "on the low side" of it would be wrong.
    if len({(span["low"], span["high"]) for span in spans}) > 1 and \
            doubt["value"] is not None and doubt["value"] * 2 < spans[0]["low"] and \
            not any(span["low"] <= doubt["value"] <= span["high"] for span in spans):
        return None
    # A figure past every range the answer names takes the range it is nearest to: whichever one is
    # picked the verdict is "high" (or "low"), so the answer has said enough, and the dearest range
    # is the one a quote above them all is about. "15000 for a new bathroom" against "£3,000 to
    # £7,000 fitted, and £8,000 to £12,000 with the bath moved" was read against the first, so a
    # quote over both tiers looked like twice the top of a range that answer never put it in.
    if doubt["value"] is not None and len(spans) > 1:
        value = doubt["value"]
        if value > max(span["high"] for span in spans) or \
                value < min(span["low"] for span in spans):
            return min(spans, key=lambda span: max(span["low"] - value, value - span["high"],
                                                  0.0))
    # The first range of that kind is the one the answer leads with - "usually £1,800 to £3,000,
    # and £3,000 to £4,500 if the pipework has to change" - so that is the usual being asked
    # about. A figure that falls in a later tier is judged against the usual and reads as high,
    # which is the question they asked ("is 3500 too much" was answered "it sits in the £3,000 to
    # £4,500 it should be, so it is fine", which argues with them).
    return spans[0]


# The words that name the low side of the range. The high side is `TOO_MUCH_WORDS`, which was
# already read here: a doubt that names one side is answered by that side's frame, and a doubt
# that names neither ("about right", "a fair price", "the going rate") is answered by the range.
TOO_LITTLE_WORDS = frozenset(("too low", "too little", "cheap", "on the low side"))


def _the_side_asked(word):
    """Which side of the range the doubt's own word asks about, or None when it names neither."""
    word = str(word or "").strip().lower()
    if word in TOO_MUCH_WORDS:
        return "high"
    if word in TOO_LITTLE_WORDS:
        return "low"
    return None


def _the_side_decides(options, doubt, value, low, high, low_side, found_side):
    """The frames the doubt's own word asks for, on the side the figure is on.

    A doubt has two parts - the side its own word asks about, and the side the figure is on - and
    a verdict has to answer both. "is that too high" at a figure under the range is a No that
    points the other way (`found_side`), "is that too low" at the same figure is a Yes
    (`low_side`), and a doubt that names no side ("about right", "a fair price", "the going
    rate") is answered by the range: the frames the range gave it, which are `found_side` when the
    figure is under it and `options` otherwise.
    """
    if doubt["word"] == "enough" or doubt["word"] in TIME_DOUBT:
        return options
    asked = _the_side_asked(doubt["word"])
    if low <= value <= high:
        return NOT_TOO_LITTLE if asked == "low" else options
    if value < low:
        return low_side if asked == "low" else found_side
    return options


def _judged(doubt, said, mine=""):
    """The verdict on the figure in the answer's own range, or None when nothing can be judged."""
    value = doubt["value"]
    if value is None:
        return None
    span = _the_span(doubt, said, mine)
    if span is None:
        return None
    low, high, span_text = span["low"], span["high"], span["text"]
    if doubt["word"] in TIME_DOUBT:
        long = doubt["word"] == "too long"
        if low <= value <= high:
            options = NOT_TOO_LONG_INSIDE if long else NOT_TOO_SHORT
        elif value > high:
            options = ON_THE_LONG_SIDE if long else NOT_TOO_SHORT
        else:
            options = NOT_TOO_LONG if long else ON_THE_SHORT_SIDE
    elif low <= value <= high:
        if doubt["word"] == "enough":
            options = ENOUGH
        elif doubt["word"] in TOO_MUCH_WORDS:
            options = NOT_TOO_MUCH
        else:
            options = ABOUT_RIGHT
    elif value > high:
        if doubt["word"] == "enough":
            options = MORE_THAN_ENOUGH
        elif doubt["word"] in TOO_MUCH_WORDS:
            options = ON_THE_HIGH_SIDE
        else:
            options = ABOVE_THE_USUAL
    else:
        options = UNDER_THE_USUAL if doubt["word"] == "enough" else ON_THE_LOW_SIDE
    options = _the_side_decides(options, doubt, value, low, high,
                                ON_THE_LOW_SIDE, THE_LOW_SIDE_FOUND)
    line = _verdict.pick(list(options), {"turns": [{"bot": span_text}]}, span_text)
    line = line.format(span=span_text, value=_money(value, span["mark"] or "£"))
    # What the answer said that money buys, when the verdict ends on the range itself: "£150 to
    # £300 buys a sound second-hand one" is the difference between a verdict and an answer a
    # friend would give, and it is the answer's own words about its own range.
    aside = _the_band_aside(said, span_text)
    if aside:
        line = _with_the_aside(line, span_text, aside)
    return line


# The clause right after a range says what that money buys: "£150 to £300 **buys a sound
# second-hand one** - a rigid 1990s mountain bike ...". Only a verb opens it, so a clause that
# goes on to price something else ("in most pubs", "depending on where you are") is not an aside.
_BUYS = re.compile(
    r"^(?:buys|gets you|gets|gets a|pays for|fits|covers|includes|holds|lasts|makes|gives|"
    r"comes to|is|are|will)\b", re.I)
# Where a clause after the range stops being about it: the sentence ends, or the answer turns to
# another price ("and £8,000 to £12,000 with the bath moved"), another place or another subject.
_ASIDE_ENDS = re.compile(r"[,.;:()]|\s+\band\s+(?:£|\d)|\s+\u2014\s+|\s+-\s+|\s+but\s+", re.I)


def _the_band_aside(said, span_text):
    """What the answer says the range buys, or "" - the clause after the range, when it has one."""
    said = " ".join(str(said or "").split())
    if not said or not span_text:
        return ""
    found = said.find(span_text)
    if found < 0:
        return ""
    after = said[found + len(span_text):]
    end = _ASIDE_ENDS.search(after)
    clause = (after[:end.start()] if end else after).strip()
    if not clause or len(clause) > 70:
        return ""
    if not _BUYS.match(clause):
        return ""
    return clause.rstrip(" .,;:")


def _with_the_aside(line, span_text, aside):
    """The verdict with the answer's own clause on the end, when the verdict ends on the range."""
    body = line.rstrip()
    if not body.endswith(span_text + "."):
        return line
    return body[:-1] + ", which " + aside + "."


# How far back the answer being judged may be. The doubt usually comes straight after it, but a
# bare "2400" between the two is common ("how much does a boiler cost" / "2400" / "is that a
# lot"), so the answer is found by walking back over the last few turns rather than only the last.
LOOK_BACK = 3


# How far apart two sums can be and still be about the same thing. A price and a rate are not the
# same thing however carefully both are priced: "cheapest so far is 2600" after a card of £1,800
# to £3,000 is a figure for the boiler, and the card the turn after - "gas heating is about 60p an
# hour... five hours a day is £2 to £3" - is not a range for it, so 2,600 read against it came
# back "No, that is on the high side: the usual is about £2 to £3". A hundred times either way
# keeps every real overcharge (2,000 for a £400 to £700 bike is the same league) and drops a rate
# held up against a price.
SAME_LEAGUE = 100.0


# The time units a person counts in, in days. Two ranges written in different units are the same
# measurement, and a figure in one can be held against a range in another: the cough answer says two
# to three weeks and the person says six days.
DAYS_IN = {"minute": 1 / 1440.0, "min": 1 / 1440.0, "hour": 1 / 24.0, "hr": 1 / 24.0,
           "day": 1.0, "week": 7.0, "month": 30.0, "year": 365.0}


def _in_the_unit(value, unit, wanted):
    """`value` counted in `wanted`, when both units count time, or None."""
    mine = DAYS_IN.get(str(unit or "").lower().rstrip("s"))
    theirs = DAYS_IN.get(str(wanted or "").lower().rstrip("s"))
    if mine is None or not theirs:
        return None
    return value * mine / theirs


def _a_stretch_of_time(unit):
    """True when a span's unit counts time: days, weeks and months can be too long, bars cannot."""
    return str(unit or "").lower().rstrip("s") in DAYS_IN


# The verdict on the answer's own usual range when no figure of theirs is on the table: "how long
# does back pain last" / "is that too long". The figure is missing, so the reply gives the yes or no
# about the range itself rather than telling someone who never said where they were that they are
# inside it.
THE_USUAL_NO = (
    "No - {span} is the usual, so it depends how long yours has been going on.",
    "No, that is the usual: {span}. How long has yours been going on?",
    "No - {span} is the normal spread, so say how long yours has lasted and I'll place it.",
)


def _the_usual_is_the_answer(doubt, said):
    """The verdict on the answer's own usual stretch of time, for "is that too long" with no figure.

    "how long does back pain last" answers two to six weeks, and "is that too long" is a question
    about that stretch, not a request to have it said again: the answer came back as "Same as
    before:" with the whole paragraph under it, which repeats it and answers nothing. So the range
    the bot itself just gave is the yardstick, and its own end is the figure held up: "No - 2 to 6
    weeks is the usual for it."

    Only a time doubt comes here. "is that enough" and "is that a lot" ask for the figure instead,
    because the memory store reads their own count against the answer already, and a person who gave
    none is better asked for it than told that a range nobody named a figure for is fine.
    """
    if doubt.get("word") not in TIME_DOUBT:
        return None
    span = _the_span(doubt, said)
    if span is None or span.get("money") or not _a_stretch_of_time(span.get("unit")):
        # "is that too long" about a price is not a question at all: with no stretch of time in the
        # answer there is nothing for it to be too long, and £1,800 to £3,000 read as the usual
        # "spread" answered a question nobody asked.
        return None
    # Both ends are inside the range, so the verdict is the reassuring one and never an accusation
    # about a figure nobody gave.
    return _verdict.pick([line.format(span=span["text"]) for line in THE_USUAL_NO],
                         {"turns": [{"bot": said}]}, span["text"])


# A figure the person wrote in words. People write their own count the way the answers write their
# ranges - "my cough has lasted three weeks", "i get about five hours", "i drink about two litres a
# day" - and FIGURE reads digits only, so every doubt with a word figure in it had nothing in hand.
# Where the count was the answer's own stretch of time the turn still worked ("is that too long"
# answered about the range itself), but a count held against the memory store's reading did not: "i
# get about five hours" / "is that enough" lost the figure and came back with a verdict that did not
# name it, where the store's own sentence - "Five hours is short of the seven to nine hours that
# answer named" - is the better reply and is the one a figure in digits still gets.
A_WORD_FIGURE = re.compile(
    r"\b(" + WORD_NUMBERS + r"|a|an|couple|few)\s+(" + "|".join(
        sorted((re.escape(unit) for unit in DOUBT_UNITS), key=len, reverse=True)) + r")\b", re.I)
WORD_FIGURE_COUNTS = {"a": 1.0, "an": 1.0, "couple": 2.0, "few": 3.0}


def _a_word_figure(said):
    """{value, money, unit} for a figure the person wrote in words, or None.

    The last one in the line, because a line that counts twice is talking about the later count: "a
    week of nights then five days off" holds five days up, not the week before it.
    """
    found = None
    for found in A_WORD_FIGURE.finditer(said or ""):
        pass
    if found is None:
        return None
    word = found.group(1).lower()
    value = _word_number(word)
    if value is None:
        value = WORD_FIGURE_COUNTS.get(word)
    if value is None:
        return None
    unit = UNIT_ALIAS.get(found.group(2).lower(), found.group(2).lower())
    return {"value": value, "money": False, "unit": unit}


def _the_last_figure_in(said):
    """The last figure in one of their lines, in digits or in words, or None."""
    said = str(said or "")
    found = list(FIGURE.finditer(said))
    if found:
        figure = _the_figure_in(said, found[-1])
        if figure:
            return figure
    return _a_word_figure(said)


def _in_the_same_league(value, said):
    """Whether a range in this answer could be about a figure this size."""
    if value is None:
        return True
    money, measured = _doubt_ranges(said)
    spans = money or measured
    if not spans:
        return True
    return any(span["low"] <= value * SAME_LEAGUE and value <= span["high"] * SAME_LEAGUE
               for span in spans)


def _answer_before(memory, value=None):
    """(the knowledge answer, its index) the doubt is about, or ("", -1) when there is none.

    `value` is the figure in hand. The nearest answer with a range in it is the one the doubt is
    about, unless its ranges are in another league from the figure: then the answer the figure is
    about is further back, and the nearest answer that could hold it is the one read. An answer
    whose ranges are all in another league is still better than nothing, so it is the fallback.
    """
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns:
        return "", -1
    elsewhere = ("", -1)
    for back in range(1, min(LOOK_BACK, len(turns)) + 1):
        turn = turns[-back] if isinstance(turns[-back], dict) else {}
        if turn.get("module") != "answers":
            continue
        said = str(turn.get("bot") or "")
        if said and any(found.group(3) or "" for found in RANGE.finditer(said)) or \
                MONEY_RANGE.search(said) or WORD_RANGE.search(said):
            if value is None or _in_the_same_league(value, said):
                return said, len(turns) - back
            if elsewhere[1] < 0:
                elsewhere = said, len(turns) - back
    if elsewhere[1] >= 0 or value is not None:
        return elsewhere
    # No answer gave a range. One that named a single price is still the answer a doubt is about:
    # "how much is an mot" / "is that expensive" had no answer at all, so the knowledge base's card
    # came back as the bare figure "£54.85." with no sentence round it.
    for back in range(1, min(LOOK_BACK, len(turns)) + 1):
        turn = turns[-back] if isinstance(turns[-back], dict) else {}
        if turn.get("module") != "answers":
            continue
        said = str(turn.get("bot") or "")
        if _a_lone_price(said):
            return said, len(turns) - back
    return elsewhere


def _figure_since(memory, after, narrow=False):
    """The last figure the person gave around the answer, or None.

    "Around" because the figure usually comes in the same turn as the answer: the person says
    what they are being charged ("my boiler service is 90 pounds"), the bot answers with the usual
    range, and the next line is "is that a lot". The answer's own turn holds their words, so it is
    read too - and only then the turns after it, which is where a quote given as its own line
    lands ("they want 250" / "is that too much").
    """
    turns = memory.get("turns") or []
    said_before = ""
    if not narrow and 0 <= after < len(turns) and isinstance(turns[after], dict):
        said_before = str(turns[after].get("user") or "")
    if said_before:
        figure = _the_last_figure_in(said_before)
        if figure:
            return figure
    for turn in reversed(turns[after + 1:]):
        said = turn.get("user") if isinstance(turn, dict) else ""
        figure = _the_last_figure_in(said)
        if figure:
            return figure
    # One turn further back: the quote is often given, then the question the bot answered, then
    # the doubt. "cheapest so far is 2600" / "how much do boilers usually cost" / "is that
    # average then" asked where 2600 sits, and the answer's own turn held no figure, so the doubt
    # came back as "What were you quoted?" - a question about a price they had just given.
    if not narrow and after >= 1 and isinstance(turns[after - 1], dict):
        figure = _the_last_figure_in(str(turns[after - 1].get("user") or ""))
        if figure:
            return figure
    return None


# A number that says *when* is not a number that says *how long*. "he keeps getting up at 5" says
# five o'clock, and held against "a two year old needs eleven to fourteen hours" it came back "No,
# that is under the 11 to 14 hours that is usual" - a verdict on a child who wakes at five, not one
# who sleeps five hours. The fence is on the figure, because no comparison is safe while a clock
# time is read as a count.
A_CLOCK_TIME_BEFORE = re.compile(
    r"\b(?:at|by|until|till|til|before|after|past)\s*$", re.I)
A_CLOCK_TIME_AFTER = re.compile(r"^\s*(?:am|pm|a\.m|p\.m|o'?clock)\b", re.I)


def _a_clock_time(said, found, value):
    """Whether this number of the line names an hour of the day rather than a count of anything.

    "at 250" is a sum said without its pound sign, so only a number that could be an hour of the
    day is fenced by the word before it; "5am" and "5 o'clock" say what they are.
    """
    if A_CLOCK_TIME_AFTER.match(said[found.end():]):
        return True
    return 0 < value <= 24 and bool(A_CLOCK_TIME_BEFORE.search(said[:found.start()]))


def _the_figure_in(said, found):
    """{value, money, unit} for one number in the person's line, or None when it is not a figure.

    A year ("1998") and an age ("im 52") are numbers a line uses without asking anything to be
    judged, so they are not figures here. Nor is an hour of the day: "at 5" and "5.30" say when
    something happens, and a unit after the number ("5 hours", "5 weeks") is what makes it a count.
    """
    value = float(found.group("number").replace(",", ""))
    money = bool(found.group("mark"))
    unit = ""
    measured = UNIT.match(said[found.end():].strip())
    if measured:
        unit = measured.group(1).lower()
    if YEAR <= value <= NEXT_YEAR and value % 100 and not money and not unit:
        return None  # a year, not a sum: "is 1998 a lot" (a round 2000 is a price)
    if AN_AGE.match(said.strip().lower()):
        return None
    if not unit and not money and _a_clock_time(said, found, value):
        return None
    return {"value": value, "money": money, "unit": unit}


# A doubt with no figure in it: "how much does a new bathroom cost" is answered with "£3,000 to
# £7,000", and the next line is "is that about right". There is nothing to compare, and the person
# is holding a number they have not been told - their own quote - so the reply asks for it. The
# range is still worth saying, because it is what their number will be judged against.
ASKS_FOR_A_PRICE = (
    "What were you quoted? {span} is the usual, and then I can say whether yours is fair.",
    "What price have you got? {span} is the usual for that, so I can tell you where you sit.",
)
ASKS_FOR_A_FIGURE = (
    "What figure have you got? The usual is {span}, and I'll say which side of it you are on.",
    "What is yours? {span} is the usual for it, so I can tell you where it lands.",
)
# A doubt about a figure the answer itself named: "how many hours do toddlers sleep" is answered
# "a one year old needs 11 to 14 hours", and the next line is "is that a lot". There is no figure
# of the person's to ask for - the only number in the conversation is the one the bot just gave -
# so asking "what figure have you got" asks them for what they were told a turn ago. The answer
# names a range, so the honest reply is that the range is the usual and offers to place their own
# number if they have one. A price is different: there the person is holding a quote they have not
# said yet, which is what ASKS_FOR_A_PRICE is for.
# A price doubt about an answer that named no price at all: "i need a new tyre" is answered with
# how long a tyre lasts, and "is that expensive" is a fair question the answer did not touch. The
# honest reply says so and asks for the number they are holding, rather than judging a lifespan as
# if it were a price.
#
# It must not claim they were quoted, though: a price word in a doubt does not mean the question
# was about a thing with a price on it. "How much should I be saving" / "is that cheap" is a sum to
# put away, and "how long does a fridge last" / "is that the going rate" is a lifespan - nobody is
# holding a quote in either, and telling them what they were quoted invents one. So the ask is for
# a figure they may have, and only a doubt whose answer really named money gets ASKS_FOR_A_PRICE.
NO_PRICE_SAID = (
    "I didn't give you a price there, so I can't call it cheap or dear yet. Tell me the figure you "
    "have in mind and what it is for, and I'll say whether it is fair.",
    "There was no price in what I said, so there is nothing to weigh up yet. Give me the number "
    "and what it is for.",
    "None of that was money, so I can't tell you expensive or not yet. Give me the figure and what "
    "it is for, and I'll say whether it is fair.",
)
# The answer named one price rather than a range: "A car MOT costs up to £54.85 in England...".
# "Is that expensive" then has nothing to hold it against, and the answer did name a price, so the
# reply says the figure back and asks for the one being weighed up. Without this the reading said
# "I didn't give you a price there" over an answer with £54.85 in it, and the knowledge base's own
# card came back as a bare "£54.85." with no sentence round it (@apt-lime, #12204).
A_LONE_PRICE = re.compile(
    r"(?P<mark>[£$€])\s?(?P<amount>\d[\d,]*(?:\.\d+)?)"
    r"|\b(?P<amount2>\d[\d,]*(?:\.\d+)?)\s*(?P<word>" + "|".join(sorted(MONEY_WORDS)) + r")\b")
THE_PRICE_IT_GAVE = (
    "{span} was the only price in that, so there is nothing to call dear yet. What have you been "
    "quoted?",
    "That answer named {span} and no range, so cheap or dear needs a second price. What figure are "
    "you weighing up?",
    "{span} is the figure I gave - one price, no range - so tell me the number you have in mind "
    "and I'll say where it sits.",
)


def _a_lone_price(said):
    """The text of a single price in the answer, when the answer gave one and no range."""
    text = str(said or "")
    money, measured = _doubt_ranges(text)
    if money:
        return ""
    for found in A_LONE_PRICE.finditer(text):
        amount = found.group("amount") or found.group("amount2") or ""
        if not amount:
            continue
        try:
            value = float(amount.replace(",", ""))
        except ValueError:      # noqa: PERF203 - a figure that will not read is not a price
            continue
        if value <= 0:
            continue
        word = (found.group("word") or "").lower()
        if not (found.group("mark") or word) and YEAR <= value <= NEXT_YEAR:
            continue
        return found.group(0).strip()
    return ""


# The answer gave a range of something other than money, and the doubt asked whether it is a lot:
# "how much should i be saving" is answered "3 to 6 months is the usual", and "is that cheap"
# cannot be answered about a stretch of months. The reply names the measure, so the person can see
# the answer was not a price, and then asks for the figure they were asking about.
A_RANGE_THAT_IS_NOT_A_PRICE = (
    "That was a range of {unit}, not a price: {span} is what it said, so cheap or dear does not "
    "come into it. If you are weighing up a figure, tell me it and what it is for.",
    "{span} is a usual range, not a price, so there is nothing there to call expensive. Give me "
    "the figure you are judging and I'll say where it sits.",
)
# The measures a "is that cheap" can be about without being money, written as the sentence needs
# them. An abbreviation is spelled out ("hrs" -> "hours") and a unit this does not know is left to
# NO_PRICE_SAID, which claims no measure at all.
UNIT_WORDS = {
    "hour": "hours", "hours": "hours", "hr": "hours", "hrs": "hours",
    "minute": "minutes", "minutes": "minutes", "min": "minutes", "mins": "minutes",
    "day": "days", "days": "days", "week": "weeks", "weeks": "weeks",
    "month": "months", "months": "months", "year": "years", "years": "years",
    "mile": "miles", "miles": "miles", "km": "kilometres", "calories": "calories",
    "kcal": "calories", "steps": "steps", "g": "grams", "grams": "grams",
    "kg": "kilos", "litre": "litres", "litres": "litres", "liter": "litres",
    "liters": "litres", "ml": "millilitres",
}
THE_RANGE_ITSELF = (
    "That is the range itself: {span} is what it says, so nothing in it is out of the ordinary. If "
    "you have a figure of your own, tell me and I'll say where it sits.",
    "{span} is the usual, so that is the figure to hold next to yours. Give me your own and I'll "
    "place it on the range.",
    "Nothing there was out of the ordinary - {span} is the usual, and that is the figure I gave "
    "you. Tell me your own and I'll judge that one instead.",
)
# A doubt with a side to it. "Is that too low" about a tyre pressure is asking which side of the
# range the thing they described is on, and a reply that answers "rather than something high" has
# read the wrong end of it (@apt-lime, #12204). The span is the same; the side is the line's own.
BELOW_THE_RANGE = (
    "Under {span} would be low, so the bottom of that is what to aim for. Tell me your figure and "
    "I'll say how far under it is.",
    "{span} is the usual, so anything under it is on the low side. What is yours?",
)
ABOVE_THE_RANGE = (
    "Over {span} would be high, so anything at the top of it is fine. Tell me your figure and I'll "
    "say how far over it is.",
    "{span} is the usual, so anything above that is on the high side. What is yours?",
)
# The doubts that name a side: under the usual, or over it. A doubt with no side ("a lot", "about
# right") keeps the neutral reply.
SAID_LOW = frozenset(("too low", "on the low side", "below average", "too little", "not enough",
                      "enough"))
# A word about money is not a side of a range of something else: "is that expensive" over 30 to 35
# psi is not a question about the top of the range, so the money words stay out and that doubt is
# left to the module that has prices.
SAID_HIGH = frozenset(("too high", "on the high side", "above average", "too much",
                       "over the top"))


def asks_for_the_figure(doubt, said):
    """The reply that asks for the figure a doubt is about, or None when it is not that doubt."""
    if doubt["word"] not in QUANTITY_WORDS:
        # "is that ok" asks whether the advice stands, which is the composer's verdict, not a
        # number held up against a range.
        return None
    money, measured = _doubt_ranges(said)
    if doubt["word"] in MONEY_DOUBTS:
        # A price ask is judged by a price, never by a lifespan or a distance.
        spans = money
        if not spans:
            spoken = [span for span in measured if UNIT_WORDS.get(span.get("unit"))]
            if spoken:
                # The answer gave months, years or hours, so the doubt is about the wrong kind of
                # number: say which kind it was instead of inventing a quote.
                span = spoken[0]
                unit = UNIT_WORDS[span["unit"]]
                return _verdict.pick([line.format(span=span["text"], unit=unit)
                                      for line in A_RANGE_THAT_IS_NOT_A_PRICE],
                                     {"turns": [{"bot": said}]}, said)
            single = _a_lone_price(said)
            if single:
                return _verdict.pick([line.format(span=single) for line in THE_PRICE_IT_GAVE],
                                     {"turns": [{"bot": said}]}, said)
            if measured and (doubt["word"] in SAID_LOW or doubt["word"] in SAID_HIGH):
                # A doubt with a side, over a range this file has no word for: "my tyre is a bit
                # soft" / "is that too low" is asking which side of the 30 to 35 psi the softness
                # puts them on, and the range is the figure to say back. A plain "is that
                # expensive" is not this: the answer gave no price at all, and the module that has
                # tyre prices says something better than a line about psi.
                span = measured[0]["text"]
                options = BELOW_THE_RANGE if doubt["word"] in SAID_LOW else ABOVE_THE_RANGE
                return _verdict.pick([line.format(span=span) for line in options],
                                     {"turns": [{"bot": said}]}, said)
            if measured:
                # The answer gave a range of something that is not money and the doubt names no
                # side: "my tyre is a bit soft" / "is that expensive" is better left to the module
                # that has tyre prices than told there was no price in a line about psi.
                return None
            return _verdict.pick(list(NO_PRICE_SAID), {"turns": [{"bot": said}]}, said)
    else:
        spans = money or measured
    if not spans:
        return None
    span = spans[0]
    if span["money"]:
        options = ASKS_FOR_A_PRICE
    elif doubt["word"] in SAID_LOW:
        # The line asks about the low end, so the reply says what low means for this range instead
        # of answering the high end it was not asked about.
        options = BELOW_THE_RANGE
    elif doubt["word"] in SAID_HIGH:
        options = ABOVE_THE_RANGE
    else:
        # No price to ask for: the range in the answer is the only figure either of them has said.
        options = THE_RANGE_ITSELF
    return _verdict.pick([line.format(span=span["text"]) for line in options],
                         {"turns": [{"bot": said}]}, said)


def _doubt_and_answer(clean, memory):
    """(the doubt, the answer it is about, that answer's turn) or None."""
    if not isinstance(memory, dict):
        return None
    doubt = _doubt(clean)
    if not doubt:
        return None
    said, at = _answer_before(memory)
    if not said:
        return None
    if doubt.get("subject") and not _the_answer_is_about(said, doubt["subject"]):
        # A line that names the thing the figure is for is judged on that thing's own range, not on
        # the answer before it: "is £2400 a lot for a boiler with a tank" after a card about boilers
        # is a price question about boilers, and it is the subject's price that settles it. The
        # exception is the answer that is about that very thing: "how much does a haircut cost" /
        # "is 40 a lot for a haircut" is the answer's own £15 to £35, and the range is already on
        # the table, so the line went nowhere and came back "40 only says something next to another
        # price" with the price sitting in the answer above it.
        return None
    return doubt, said, at


def _the_answer_is_about(said, subject):
    """Whether the answer's opening is about the thing the figure in the line is for.

    Only the opening sentence, which is where a price answer names what it is pricing, and only a
    word they share: "a haircut" is the "cut" of "A cut is usually £15 to £35 in a salon".
    """
    words = [word for word in re.findall(r"[a-z']+", _the_opening_sentence(said).lower())
             if len(word) >= 3]
    for word in re.findall(r"[a-z']+", str(subject or "").lower()):
        if len(word) < 3:
            continue
        for there in words:
            if word in there or there in word:
                return True
    return False


def _only_says_that(doubt):
    """True for a doubt word that says "that" and no more ("normal", "ok", "reasonable", "fine").

    These are about the thing being usual or the advice standing, and the memory store reads the
    figure that came with them. "is that normal" after "its gone up to 90 a month" is about the
    bill, not about placing 90 in a range, so the figure read for it stays with main's narrow one:
    the turns after the answer, which is where a quote given as its own line lands ("what does a
    plumber charge" / "I was quoted 300" / "is that normal", still judged). A word that names the
    doubt itself ("is that a lot", "is that enough") reads the answer's own turn and one turn back
    as well, because that is where the price they are being charged usually sits and nothing else
    reads it.
    """
    return doubt.get("word") not in QUANTITY_WORDS


def _the_usuals(subject):
    """The price ranges the knowledge base gives for this thing, or () when it gives none.

    The facts are already written down for "how much does a haircut cost", and the person asking
    "is £40 a lot for a haircut" wants the same range with their own figure placed in it. So the
    subject they named is put to the knowledge base as the price question it is, and the ranges in
    that answer are the yardstick. Nothing is guessed: a subject the base has no price for comes
    back empty, and the line is left to the modules that know better.
    """
    short = FOR_THE_ARTICLE.sub("", " ".join(str(subject or "").split()))
    if not short or len(short.split()) > 4:
        return ()
    try:  # a knowledge base that cannot be imported just means no range
        from ..knowledge import lookup
    except Exception:  # noqa: BLE001 - no facts, no verdict
        return ()
    for question in ("how much does a %s cost" % short, "how much does %s cost" % short,
                     "how much is a %s" % short):
        try:
            found = lookup.find({"clean": question, "words": question.split()})
        except Exception:  # noqa: BLE001 - a lookup that raises answers nothing
            continue
        if found is None:
            continue
        reply = getattr(found, "reply", None)
        if callable(reply):
            try:
                reply = reply({}, {"clean": question, "words": question.split()})
            except Exception:  # noqa: BLE001 - a row that needs a conversation answers nothing
                continue
        money, _ = _doubt_ranges(_the_opening_sentence(reply))
        if money:
            return tuple(money)
    return ()


def _the_opening_sentence(reply):
    """The first sentence of an answer, which is where a price answer states its price.

    The range a verdict is put against has to be the price of the thing asked about, and an answer
    holds other ranges further down that are about something else: the car insurance card has no
    price in its first sentence and "a new driver pays £1,500 to £2,500 in the first year" in its
    third, so reading the whole card made "is 350 a lot for car insurance" a quote for a new driver.
    """
    text = " ".join(str(reply or "").split())
    for mark in (". ", "! ", "? "):
        cut = text.find(mark)
        if cut > 0:
            text = text[:cut]
    return text


# The verdict when the person brought the figure and the subject with them. The range is quoted
# every time, the way the answer-before spelling quotes it: it is the whole reason the reply can
# say anything at all.
RIGHT_FOR_THE_THING = (
    "That is about right for {thing} - {span} is the usual.",
    "Yes, that is in the normal range: {span} is the usual for {thing}.",
)
HIGH_FOR_THE_THING = (
    "That is on the high side for {thing}: the usual is about {span}.",
    "Yes, a bit much for {thing} - {span} is the usual.",
)
# Same rule for a price the person brought with them: "is that too cheap" is a Yes, and the No
# belongs to "is that enough for it", which `SHORT_FOR_THE_THING` holds.
LOW_FOR_THE_THING = (
    "That is on the low side for {thing} - the usual is about {span}.",
    "Yes, a bit low for {thing} - {span} is the usual.",
)
ENOUGH_FOR_THE_THING = (
    "Yes, that is enough for {thing} - the usual is {span}.",
    "That is plenty for {thing}: {span} is the usual.",
)
SHORT_FOR_THE_THING = (
    "That is a little short for {thing} - the usual is {span}.",
    "No, that is under the {span} it needs for {thing}.",
)
THE_LOW_SIDE_FOUND_FOR_THE_THING = (
    "That is on the low side for {thing} - the usual is about {span}.",
    "No, that is under the {span} that {thing} usually costs.",
)


def _judged_on_its_subject(doubt):
    """The verdict on a figure the person brought with them, or None when nothing can judge it."""
    if not doubt or doubt.get("value") is None:
        return None
    if not doubt.get("subject"):
        return None
    if doubt.get("unit"):
        return None  # a measurement is not a price, and every range here is one
    spans = _the_usuals(doubt["subject"])
    if not spans:
        return None
    span = spans[0]
    value, low, high = doubt["value"], span["low"], span["high"]
    enough = doubt["word"] == "enough"
    if low <= value <= high:
        options = ENOUGH_FOR_THE_THING if enough else RIGHT_FOR_THE_THING
    elif value > high:
        options = ENOUGH_FOR_THE_THING if enough else HIGH_FOR_THE_THING
    else:
        options = SHORT_FOR_THE_THING if enough else LOW_FOR_THE_THING
    options = _the_side_decides(options, doubt, value, low, high,
                                LOW_FOR_THE_THING, THE_LOW_SIDE_FOUND_FOR_THE_THING)
    return _verdict.pick([line.format(thing=doubt["subject"], span=span["text"])
                          for line in options], {"turns": [{"bot": span["text"]}]},
                         span["text"])


# A word that points at a thing instead of naming it: "is 4 pounds a lot for one", asked while a
# chicken is on the table, is a question about the chicken.
_POINTS_AT_IT = frozenset("""
    one ones it that this these those them they him her he she thing things
""".split())


def _the_thing_the_chat_is_on(memory):
    """The thing the conversation is on, as "a chicken", or "" when nothing says."""
    understood = (memory or {}).get("understood") if isinstance(memory, dict) else None
    if not isinstance(understood, dict):
        return ""
    ref = understood.get("ref")
    if isinstance(ref, dict):
        for key in ("it", "that", "they", "them"):
            thing = str(ref.get(key) or "").strip()
            if thing and thing.lower() not in _POINTS_AT_IT:
                return thing if FOR_THE_ARTICLE.match(thing) else "a " + thing
    return ""


def _the_doubt_with_its_thing(clean, memory):
    """The doubt about the figure, about the thing the chat is on when the line names none.

    "im cooking a chicken" then "is 4 pounds a lot for one" names no thing of its own, and the
    thing on the table is the chicken: the price row for a chicken is what the figure is judged
    against, and without it the reply is a paragraph about shopping around.
    """
    doubt = _doubt(clean)
    if not doubt or doubt.get("value") is None or not doubt.get("money"):
        return doubt
    subject = str(doubt.get("subject") or "").strip()
    if subject and subject.lower() not in _POINTS_AT_IT:
        return doubt
    thing = _the_thing_the_chat_is_on(memory)
    if thing:
        doubt = dict(doubt, subject=thing)
    return doubt


def _its_own_subject_judges_it(clean, memory):
    """True when the line names both a figure and the thing it is for, and the base has a range.

    Only when the answer before it holds no range of its own: a doubt straight after an answer
    with a range in it is judged on that answer first ("how much does a haircut cost" / "is 40 a
    lot for a haircut" is the answer's £15 to £35, not a second lookup), and this is what answers
    the line when there is nothing above it to judge against. Only when the knowledge base does not
    answer the line on its own words: "is 400 enough for a bike" reaches the bike price row, and
    its answer is better than a comparison.
    """
    doubt = _the_doubt_with_its_thing(clean, memory)
    if not doubt or not doubt.get("subject") or doubt.get("value") is None:
        return False
    said, _ = _answer_before(memory if isinstance(memory, dict) else {})
    if said and _the_answer_is_about(said, doubt["subject"]):
        return False     # that answer is the range, and the doubt about it is read above
    if _a_card_answers(str(clean or "")):
        return False
    return _judged_on_its_subject(doubt) is not None


def _a_card_answers(text):
    """Whether the knowledge base answers this line on its own words."""
    try:
        from ..knowledge import lookup
    except Exception:  # noqa: BLE001 - no base means nothing answers it
        return False
    try:
        return lookup.find({"clean": text, "words": text.split()}) is not None
    except Exception:  # noqa: BLE001 - a lookup that raises claims nothing
        return False


def judges_a_figure(clean, memory):
    """True when the line is a doubt this module answers, with an answer it can be judged by.

    This is the claim `bot/modules/chat.py` makes as it comes: the doubt about the answer on the
    table, or a figure the person brought with its own thing ("is 800 enough for a long weekend in
    Lisbon"), which `_its_own_subject_judges_it` answers from that thing's own price row. A figure
    the memory store judges in its own words is claimed too: that sentence is the reply, and the
    claim is what keeps the turn from falling through to a module that says the paragraph again.
    """
    if not isinstance(memory, dict):
        return False
    return (judges_the_figure_on_the_table(clean, memory)
            or _its_own_subject_judges_it(clean, memory))


def judges_the_figure_on_the_table(clean, memory):
    """True when the line is a doubt about the figure the answer on the table already named.

    The narrower claim, and the one `bot/modules/answers.py` stands down for: it is a line whose
    answer is the comparison with the range the bot has just given ("my boiler service is 90
    pounds" / "is that a lot"), and that module's card would say the whole price range over again
    instead of answering. A line that names its own thing is not this: "is 800 enough for a long
    weekend in Lisbon" has a trip row of its own, and the row is better than a verdict here.

    It is narrow on purpose. A
    doubt that only says "that" ("is that enough") may be about a figure the person gave in their
    own words, and the memory store reads a figure that came with a unit against the answer's
    range already (`bot/modules/memory_store.py:_enough_reply`), so a measured figure stays with
    it. What is left is the price the person gave ("my boiler service is 90 pounds", "is that a
    lot"), which nothing else reads - the store's own words for it are "enough", "too much" and
    "about right", and a price held up and called "a lot" fell between the two of them and came
    back as "What were you quoted?", a question about a figure they had just given - and the
    figure named in the doubt itself ("is 3500 too much") or typed between the answer and the
    doubt ("how much does a boiler cost", "2400", "is that a lot").
    """
    return _the_verdict_for_the_table(clean, memory) is not None


# A count that is a frequency, not a measure: "i train 3 times a week" held against an answer in
# weeks is not like held against like, and read as three weeks it told somebody training three times
# a week "That is a little short - the usual is 12 to 16 weeks".
A_RATE_OF_THEIRS = re.compile(
    r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+"
    r"(?:times?|x|runs?|sessions?|workouts?)\s+(?:a|per|each|every)\s+(?:day|week|month|year)\b"
    r"|\btwice\s+(?:a|per|each|every)\s+(?:day|week|month|year)\b", re.I)


def _a_rate_of_theirs(memory):
    """Whether the person's own figure was given as a frequency ("3 times a week")."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return False
    for turn in reversed(turns[-LOOK_BACK:]):
        said = turn.get("user") if isinstance(turn, dict) else ""
        if A_RATE_OF_THEIRS.search(str(said or "")):
            return True
    return False


def _the_verdict_for_the_table(clean, memory):
    """The verdict on the figure the answer on the table named, or None.

    Never the question back, which is a reply but not a verdict: the claim above is this verdict,
    and a line with no figure in it and no answer to say which is not claimed.
    """
    read = _doubt_and_answer(clean, memory)
    if not read:
        return None
    doubt, said, at = read
    if doubt["value"] is None and doubt.get("word") in PLACES_A_FIGURE:
        # A measured figure is the memory store's, and the figure the doubt is about is often in
        # the line the answer answers rather than after it: "my boiler pressure is 1 bar", the
        # boiler card, "is that too low". The answer's own turn is read only where the store read a
        # measurement and the answer states a range in the same unit, so every figure the reading
        # cannot hold against anything stays with the store. See `_figure_of_the_answer`.
        held = _figure_since(memory, at, narrow=_only_says_that(doubt))
        if held and held["unit"]:
            figured = _figure_of_the_answer(memory, at)
            if figured:
                doubt = dict(doubt, **figured)
    if doubt["value"] is None:
        before = _figure_since(memory, at, narrow=_only_says_that(doubt))
        if not before:
            if doubt["word"] in MONEY_DOUBTS:
                # A price doubt with no figure of theirs behind it is about the answer's own
                # price: asked for when there is a range to name, and named back when the answer
                # gave a single figure instead.
                asked = asks_for_the_figure(doubt, said)
                if asked:
                    return asked
            # A time doubt with no figure behind it is a question about the answer's own stretch.
            return _the_usual_is_the_answer(doubt, said)
        if before["unit"] and doubt["word"] in TIME_DOUBT:
            # "ive had a cough for 6 days" / "is that too long": a figure in days held against an
            # answer in weeks is no comparison at all, so it is brought into the answer's unit and
            # judged there rather than handed back to the module that says the paragraph again.
            span = _the_span(doubt, said)
            converted = _in_the_unit(before["value"], before["unit"],
                                     span.get("unit") if span else "")
            if converted is not None:
                return _judged(dict(doubt, value=converted, money=False,
                                    unit=span.get("unit"), rate=False), said)
        if before["unit"]:
            return None
        doubt = dict(doubt, **before)
    moved = _the_answer_about_this_figure(doubt, memory, at)
    if moved is None:
        return None
    said, at = moved
    if not doubt.get("unit") and _a_rate_of_theirs(memory):
        span = _the_span(doubt, said)
        if span is not None and _a_stretch_of_time(span.get("unit")):
            return None     # a frequency of theirs is not a stretch of time to hold against a range
    mine = _judged(doubt, said, _the_person_words(memory, clean))
    if mine is None:
        return None     # nothing in the answer this figure can be held against
    # The memory store's own sentence when the figure is outside the range it read: it names the
    # figure and says what to do about it ("250 is over the £60 to £120 the usual price comes to,
    # so it is worth a second quote"), which this module's verdict would lose.
    return _the_price_verdict(clean, memory) or mine


def _the_price_verdict(clean, memory):
    """The memory store's judgement of the figure on the table, when it is the better reply.

    `bot/memory/price.py` has read a price held up against the answer before it since before this
    module existed, and where the figure is outside the range its pools say so and say what to do
    about it ("250 is over the £60 to £120 the usual price comes to, so it is worth a second
    quote"), in the answer's own words. That is the reply, and the reading stands down for it.

    Only when the figure is *outside* the range: inside it the store's line is "That is about
    right", which does not answer "is that a lot", and the yes or no the person asked for is the
    whole of what is left to say ("No, that is fine: the usual is £60 to £120"). Imported here
    because the store is the memory's and this module is the composer's.
    """
    try:
        from ..memory import price as a_price
    except Exception:  # noqa: BLE001 - no store means no judgement of its own
        return None
    try:
        said = a_price.judged(clean, memory) or None
    except Exception:  # noqa: BLE001 - a judge that raises has said nothing
        return None
    if not said or not _the_store_found_it_outside(clean, memory, a_price):
        return None
    return said


def _the_store_found_it_outside(clean, memory, a_price):
    """Whether the figure the store judged is outside the range it judged it against.

    The store's own reading is asked, so the two never disagree about which range is meant: it is
    the same answer and the same figure. When anything about it cannot be read, the answer is yes,
    because the store's sentence is the one main gives and the reading has nothing better to add.
    """
    try:
        mine, _said = a_price._the_price_they_mean(clean, memory)
        if not mine:
            return True
        answers = a_price._answers_in(memory.get("turns"))
        aim = a_price._the_range_that_is_about_it(
            answers, mine, a_price._the_period_they_said(clean, memory))
        if aim is None:
            return True
        return not aim[0] <= mine <= aim[1]
    except Exception:  # noqa: BLE001 - a reading that moved leaves the store's sentence alone
        return True


def reply_to_a_doubt(clean, memory):
    """The reply to a line that only asks whether a figure is a lot, enough or about right."""
    verdict = _the_verdict_for_the_table(clean, memory)
    if verdict:
        return verdict
    read = _doubt_and_answer(clean, memory)
    if not read:
        if not _its_own_subject_judges_it(clean, memory):
            return None
        return _judged_on_its_subject(_the_doubt_with_its_thing(clean, memory))
    doubt, said, at = read
    if doubt["value"] is not None:
        return None     # a figure with no range to hold it: the modules that know better answer
    before = _figure_since(memory, at, narrow=_only_says_that(doubt))
    if not before or before["unit"]:
        # A measured figure is the memory store's ("2 litres is at the top"), and a doubt with no
        # figure at all is asked for in one.
        return asks_for_the_figure(doubt, said) if not before else None
    return None


def _the_answer_about_this_figure(doubt, memory, at):
    """(the answer, its index) the figure is about, or None when no answer can hold it.

    The answer found first is the newest with a range in it, which is usually the right one. A
    figure in another league from its ranges means the turn in between changed subject, so the
    answer the figure is about is the one back that could hold it, and the figure has to be found
    again around that answer.
    """
    value = doubt.get("value")
    if value is None:
        return None
    said, found_at = _answer_before(memory, value)
    if not said:
        return None
    if found_at == at:
        return said, at
    again = _figure_since(memory, found_at, narrow=_only_says_that(doubt))
    if again:
        doubt.update(again)
    return said, found_at


# ------------------------------------------------- a doubt with nothing to judge it against

# The line is a doubt and nothing behind it states a range. The person has said what they have and
# is asking whether it is a lot:
#
#     its 45 a month                        / is that a lot    -> "Alright then - good luck with it."
#     my electricity is 45 a month for a one bed / is that a lot -> "Alright then - good luck with it."
#     its about 6 miles each way            / is that too far  -> the place advice, and the 6 miles ignored
#
# None of these can be judged: there is no yardstick anywhere in the conversation and the bot cannot
# look one up. What is left is what a friend does - say the figure back, because saying it is most of
# the question, name the one thing that would settle it, and ask for that. Nothing here is invented:
# a price is settled by another price for the same thing, a journey by the time it takes, a stretch
# of time by what else has to fit into it. A line the bot cannot put even a figure to is left alone.
THEIR_FIGURE = re.compile(
    r"(?:(?P<mark>[\u00a3$\u20ac])\s?)?(?P<number>\d[\d,]*(?:\.\d+)?)\s*(?:a|an|per|each)?\s*"
    r"(?P<unit>bar|bars|psi|hours?|hrs?|minutes?|mins?|days?|weeks?|months?|years?|miles?|km|"
    r"kilos?|kg|grams?|g|steps|calories?|kcal|litres?|liters?|ml|pints?|watts?|volts?|degrees?|"
    r"deg|pounds?|quid|dollars?|euros?|bucks?)\b", re.IGNORECASE)
# What makes a figure a bill when it carries no mark and no currency word on it: "my electricity is
# 45 a month" is money because of the noun in front of it, not because of the word "month".
# A figure with no unit at all: "the quote came to 900" / "is that about right". Only taken when
# the line it is in says what the figure is (a bill, a quote, a price), because a number with
# nothing around it could be anything.
THEIR_NUMBER = re.compile(r"(?:(?P<mark>[\u00a3$\u20ac])\s?)?(?P<number>\d[\d,]*(?:\.\d+)?)(?!\d)")
A_BILL = frozenset((
    "bill", "bills", "electricity", "gas", "water", "heating", "rent", "mortgage", "insurance",
    "subscription", "subscriptions", "mobile", "broadband", "wifi", "council", "tax", "paying",
    "pay", "paid", "pays", "cost", "costs", "costing", "quote", "quoted", "price", "priced",
    "charged", "charge", "charging", "fee", "fees", "fare", "fares", "deposit", "debit",
    "invoice", "loan", "instalments", "installments", "monthly", "annual", "saving", "savings",
    "spend", "spends", "spending", "spent", "budget", "budgeting", "shop", "shopping",
))
A_PERIOD = frozenset(("month", "months", "week", "weeks", "year", "years"))
# A sum with no unit and no bill word, where the phrase itself says it is the lot: "its 900 for the
# whole thing", "600 all in". Read as money, so a price doubt about it gets the price answer.
A_MONEY_PHRASE = re.compile(
    r"\b(?:the whole thing|the whole lot|for the lot|all in|altogether|in total|all told|the lot)\b",
    re.IGNORECASE)
A_STRETCH = frozenset(("hour", "hours", "hr", "hrs", "minute", "minutes", "min", "mins"))
A_DISTANCE = frozenset(("mile", "miles", "km"))
# The figure said back the way the person wrote it: "45 a month", "£2,400", "6 miles".
def _figure_words(number, unit, mark=""):
    """The figure as it is said back: 45 with "month" is "45 a month", 6 with "miles" is "6 miles"."""
    text = "%s%s" % (mark, number)
    if not unit:
        return text
    if unit in A_PERIOD and unit in ("month", "week", "year", "day"):
        return "%s a %s" % (text, unit)
    return text + _unit(unit)


A_PRICE_NEXT_TO = (
    "{said} is only high or low next to another figure for the same thing: what you were paying "
    "before, or what somebody else pays for it. What was it before?",
    "{said} needs a second figure beside it - your last one, or what a friend pays - before anyone "
    "can call it a lot. What is the other one?",
)
A_JOURNEY_IS_TIME = (
    "{said} is a real journey. Whether it is too far is about the time it takes you and what you "
    "want to be able to do at the other end - how long does it take?",
    "{said} comes down to the time rather than the miles: easy for one person, a long trip for "
    "another. How long does it take you?",
)
A_STRETCH_OF_TIME = (
    "{said} is only too long against the rest of the day. What else has to fit into it?",
    "{said} - whether that is too much depends on what else the same time has to hold. What else "
    "is in the day?",
)
THE_REST_IS_UNSURE = (
    "{said} is not something I can call a lot from here. What are you comparing it with?",
    "{said} - too much against what? Name the thing you are measuring it against and I will take "
    "it from there.",
)


# A price said as something the person paid, with no unit word: "my haircut was 60", "it cost me
# 60", "i paid 60", "the quote came to 300". The verb is what makes it money - without one, "was 60"
# could be anything, and a doubt about it gets the ask for a second figure rather than a judgement.
A_PRICE_VERB = re.compile(
    r"\b(?:was|were|is|cost|costs|cost me|paid|pay|spent|spend|charged|comes to|came to|"
    r"set me back)\s+(?:me\s+|us\s+)?[\u00a3$\u20ac]?\d", re.IGNORECASE)


def _their_figure(memory, back=1):
    """The last figure the person gave in their own words, as (number, unit, text, money), or None.

    The figure a doubt is about is usually the one they said just before it ("its 45 a month" /
    "is that a lot"), and it is theirs: nothing is read out of the bot's own lines here, because
    the bot's lines are the yardstick and there is no yardstick in this case.
    """
    turns = memory.get("turns")
    if not isinstance(turns, list):
        return None
    seen = 0
    for turn in reversed(turns):
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("user") or "")
        if not said:
            continue
        seen += 1
        if seen > back:
            break
        found = None
        for found in THEIR_FIGURE.finditer(said):
            pass
        if not found:
            # A figure the line explains rather than a unit: "the quote came to 900", or "its 900
            # for the whole thing", where the phrase says the sum is the lot.
            words = set(re.findall(r"[a-z']+", said.lower()))
            if not (words & A_BILL) and not A_MONEY_PHRASE.search(said) and not re.search(
                    r"[\u00a3$\u20ac]", said) and not A_PRICE_VERB.search(said.lower()):
                continue
            for found in THEIR_NUMBER.finditer(said):
                pass
            if not found:
                continue
        value = float(found.group("number").replace(",", ""))
        unit = (found.groupdict().get("unit") or "").lower()
        if YEAR <= value <= NEXT_YEAR and not found.group("mark") and unit not in ("miles", "km"):
            continue  # a year is not a figure anybody asks to have judged
        if AN_AGE.match(said.strip().lower()) or re.search(r"\b(?:years?|yrs?|months?)\s+old\b",
                                                          said.lower()):
            continue  # an age is not a figure anybody asks to have judged
        words = set(re.findall(r"[a-z']+", said.lower()))
        money = bool(found.group("mark")) or unit in MONEY_WORDS or bool(words & A_BILL) or \
            bool(A_MONEY_PHRASE.search(said)) or (not unit and bool(A_PRICE_VERB.search(said.lower())))
        text = _figure_words(found.group("number"), unit, found.group("mark") or "")
        return value, unit, text, money
    return None


# The doubts this reader answers, which is the ones about a ceiling - is this too much - and not
# "is that enough", which asks whether there is enough of something and wants the floor said back.
# "enough" is left where it is answered already (`bot/modules/memory_store.py` says how the figure
# sits against the answer's range, and the knowledge modules say what the amount is for).
# A doubt that says the money out loud is the price reader's line, not this one.
A_MONEY_WORD = re.compile(r"[\u00a3$\u20ac]|\b(?:money|quid|pounds?|dollars?|euros?|bucks?|"
                          r"cost|costs|price|prices|pay|paying|spend|spending|afford)\b", re.I)
# The ceiling said of a distance, a stretch of time or a count is the same question, and it is not
# in `DOUBT_WORDS` - that vocabulary is what `judges_a_figure` claims with, and every line it gains
# is a line another reader loses. This reader keeps its own words.
BARE_CEILING = re.compile(
    r"^(?:and |so |ok(?:ay)?,? )?(?:is|was|were|would|does|do)\s+(?:that|it|this|they|there)?\s*"
    r"(?:really\s+|actually\s+|still\s+)?(?P<word>too (?:far|long|many|much|high)|a lot|"
    r"about right|over the top|expensive|steep)\b", re.I)
# "is that normal" and "is that reasonable" are not here: they ask whether a thing is ordinary,
# which is a question the bot can answer from what it knows ("Yes, that is the usual thing - what to
# keep an eye on is change rather than the thing itself"). A ceiling is about an amount.
A_CEILING = frozenset(("a lot", "much", "too much", "too high", "too many", "too far", "too long",
                       "expensive", "steep", "over the top", "about right", "a good price",
                       "a fair price", "the going rate", "about the going rate"))


# An answer that has already judged the figure is the answer to "is that too long": the card said
# "an hour each way is about where most people stop being fine with it, and past that it is twenty
# hours a week", and the person is asking about the figure that answer was for. Saying the figure
# back and asking what else has to fit in the day is a question where a card had already given a
# threshold, so this reader stands down and lets the readings that use the card answer.
ALREADY_JUDGED = re.compile(
    r"\b(?:about where|most people|any(?:thing|one) (?:over|above|past)|more than about|\
    no more than|up to about|past that|beyond that|on the high side|on the low side|\
    on the dear side|on the cheap side|cheaper than|dearer than|more expensive than|\
    about right|is a lot|isn't a lot|is not a lot|fair price|good price|the going rate|\
    the usual (?:is|rate|range)|the average is)\b", re.IGNORECASE)


def _already_judged(memory):
    """Whether the bot's own last line already put the figure against a threshold."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return False
    for turn in reversed(turns):
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("bot") or "")
        if not said:
            continue
        return bool(ALREADY_JUDGED.search(said))
    return False


def _a_bare_doubt(clean, memory):
    """(value, unit, text, money) for a bare doubt with the person's own figure and no range.

    Bare is the whole of it: the doubt says "that", and the figure is the one the person said the
    turn before ("its 45 a month" / "is that a lot"). A doubt that names its own figure ("is 120
    pounds too much to spend") is not this reader's line - the composer's price check reads it, and
    it says more than this can.
    """
    if not isinstance(memory, dict):
        return None
    doubt = _doubt(clean)
    if doubt is None:
        # "is that too far", "is that too long": the words `_doubt` does not carry.
        said_line = str(clean or "").strip().lower().rstrip("?!. ")
        match = BARE_CEILING.match(said_line)
        if not match:
            return None
        doubt = {"word": match.group("word"), "value": None, "unit": "", "money": False}
    if doubt["word"] not in A_CEILING:
        return None
    if A_MONEY_WORD.search(str(clean or "")):
        # "is that a lot of money" names the money, and the composer's own price check reads it:
        # one more price for the same thing, from another shop or another quote. That is more than
        # this can say, so the line is left to it.
        return None
    said, _at = _answer_before(memory)
    if said:
        return None  # there is a range behind it, and `reply_to_a_doubt` judges against that
    if doubt["value"] is not None:
        return None  # the figure is in the line, so the reading that judges a named figure has it
    if _already_judged(memory):
        return None  # the answer in hand already put this figure against a threshold
    return _their_figure(memory)


def reply_to_a_bare_doubt(clean, memory):
    """The honest reply to a doubt with nothing behind it to judge the figure against."""
    read = _a_bare_doubt(clean, memory)
    if not read:
        return None
    _value, unit, text, money = read
    if money:
        options = A_PRICE_NEXT_TO
    elif unit in A_DISTANCE:
        options = A_JOURNEY_IS_TIME
    elif unit in A_STRETCH:
        options = A_STRETCH_OF_TIME
    else:
        options = THE_REST_IS_UNSURE
    return _verdict.pick([line.format(said=text) for line in options],
                         {"turns": [{"t": text}]}, text)


def reply_for(clean, memory):
    """The reading in the line, checked against the range in the answer just given."""
    if not isinstance(memory, dict):
        return None
    if AN_AGE.match(str(clean or "").strip()):
        # "im 52" said after an answer about a boiler gauge is the person's age, not a reading of
        # the gauge: it came back "52 is over the 1 to 1.5 bar it should be", which is a number
        # compared with a thing it has nothing to do with. An age is a fact about them, and the
        # store says it back as one.
        return None
    judged = reply_to_a_doubt(clean, memory)
    if judged:
        return judged
    # A doubt with a figure and nothing behind it to judge it against ("its 45 a month" / "is that
    # a lot") was answered here by nobody, so it fell to the acknowledgement pools and got "Alright
    # then - good luck with it." The figure said back and the one thing that would settle it goes
    # where the goodbye was.
    bare = reply_to_a_bare_doubt(clean, memory)
    if bare:
        return bare
    read = _number(clean)
    if read is None:
        return None
    value, unit = read
    said = _said(memory, clean)
    if not said:
        return None
    span = _range(said)
    if span is None:
        return None
    low, high, says_unit = span
    # The person's unit and the answer's have to be the same measurement. "the gauge says 0.5" has
    # none, so the answer's is the one the number is in; a bar read against a temperature is not
    # a comparison at all.
    if unit and says_unit and not _same_measure(unit, says_unit):
        return None
    span_text = "%s to %s%s" % (_say(low), _say(high), _unit(says_unit))
    where = _where(value, low, high, says_unit)
    if where == "inside":
        return pick_inside(value, span_text, said)
    step = _step(said)
    if where == "below":
        line = "%s is under the %s it should be" % (_say(value), span_text)
        if step:
            return "%s: %s." % (line, step.rstrip("."))
        return line + " - that is the thing to put right."
    # Over is not under: the fix for a reading that is too high is not the answer's step ("use a
    # thermometer rather than the dial" was handed back as the same fix for a fridge at 8C), so
    # nothing is repeated here beyond the range itself.
    return "%s is over the %s it should be, which is the thing to put right." % (
        _say(value), span_text)


# A reading that is where it should be is good news, and the tiny pool keeps two readings of the
# same thread from being handed the same sentence: "the gauge says 1.2" and "its 4C" are different
# numbers about different things.
INSIDE = (
    "That is where it should be - {span}.",
    "{value} is in the {span} it wants, so nothing to do there.",
    "Spot on: {span} is right for it.",
)


def pick_inside(value, span_text, said):
    options = [line.format(value=_say(value), span=span_text) for line in INSIDE]
    return _verdict.pick(options, {"turns": [{"bot": said}]}, said)


def _figure_of_the_answer(memory, at):
    """The figure in the line the answer was given to, when the answer can hold it.

    "my boiler pressure is 1 bar" is answered with the card that says what the pressure should be
    (1 to 1.5 bar), and the next line is "is that too low". The figure the doubt is about came in
    the line the answer answers, before the doubt, so a read that only looks forward asks the
    person for a figure they have just typed out.

    Only a figure the answer can be held against is read there: a price where the answer states a
    price range, a reading where it states a range in the same unit. A bare number is not put
    against a measured range at all - "my heating bill was 200 a month" under the boiler card put
    200 against "55 to 60C" and came back "yes, a bit much" - so a bare number is only read where
    the answer's own range is a price, which is the only kind of figure it can be there.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not 0 <= at < len(turns):
        return None
    turn = turns[at]
    if not isinstance(turn, dict):
        return None
    said = str(turn.get("user") or "")
    found = list(FIGURE.finditer(said))
    if not found:
        return None
    figure = _the_figure_in(said, found[-1])
    if not figure:
        return None
    money, measured = _doubt_ranges(turn.get("bot"))
    if figure["unit"]:
        if not any(span["unit"] == figure["unit"] for span in measured):
            return None
    elif figure["money"]:
        if not money:
            return None
    elif measured or not money:
        return None
    return figure
