"""A fact about themselves they gave, asked for again by name, and answered from their own line.

    im looking for a new winter coat
    im a size 12
    my budget is about 100 pounds
    ...
    what size am i again    -> "I don't know enough to answer that honestly. A search ..."
    and whats my budget     -> "Your budget is 100 pounds."

The store has the size the whole time - on the same chat `do you know my size` answers
"You said you're a size 12." - so this is one ask shape reaching nobody, not a fact that was
never kept. The ask is about the person, and the attribute words ("size", "weight", "colour")
are not words in the line that gives them ("im a size 12", "90 kilos"), so no entry about the
world can look it up and no reader of what was said was asked.

The reading here is narrow on purpose, and every part of it is needed:

* the ask has to be about them - `what <attribute> am i`, `whats my <attribute>` - so
  "what size are the boxes" and "what time am i leaving" are untouched;
* the attribute has to be one of the short list below, so a line about anything else passes;
* **and the attribute has to be in one of their own lines.** That is what makes it a recall
  rather than a question about the world: `what size am i` with nothing said before it is
  still the size-conversion card, and `what size am i again` after "my knee hurts" finds
  nothing and the turn stays where it was.

The wording is the store's own restating (`memory_store._told_phrase`), so the fact comes back
in the shape a friend would say it - "You told me you're a size 12." - and never as a quotation
of the line.

The same shape of ask, with the slot named instead of the fact, is answered here too:

    we are going to edinburgh for a long weekend in october
    we want to be near the royal mile
    ...
    did i say when we were going        -> "I don't know enough to answer that honestly."
    did i say where we wanted to stay   -> "That's beyond what I know well, sorry."

The month is in their first line and the area in their second, and the store answers
"what did i say about october" from the same lines. What is missing is the ask that names the
slot: `did i say when ...`, `when did i say ...`, and the same with "where". The slot word says
what kind of value is wanted, and the rest of the ask names the thing it belongs to - so the
line has to hold both a time (for when) or a place (for where) **and** share a word with the
subject of the ask. Nothing else is read: "did i say when the boiler was serviced" with no time
said anywhere passes, and so does every line that is not one of these asks.

The same shape again, with a size instead of a time or a place:

    we're redecorating the kitchen next month
    its small, about 3 by 2 metres
    ...
    and how big is the kitchen     -> "Clear the surfaces, then work clockwise ..." (a cleaning card)

The size is in their second line, said about the kitchen it does not name, and the ask for it
reached a card about cleaning. A measure is read here only with a unit (metres, cm, feet, litres)
so a count ("two cats") and a price ("20 pounds") are not sizes, and the line has to be about the
thing the ask names - or be a line about it alone ("its small, about 3 by 2 metres") directly
after the line that does name it.
"""
import re

from ..memory import repeat

# Above the chatter band, below the memory store: the store's recall of what was said leads the
# turn, and this answers only on lines it passes. It has to be above `answers`, because a
# specialist card that declares the chat's topic takes a line off a generalist underneath it -
# "what size am i again" in a coat chat reached the clothes-size conversion table from there.
PRIORITY = 6900

# The attributes a person gives about themselves and asks for again by name.
THEIRS = ("size", "shoe size", "ring size", "weight", "height", "colour", "color", "budget",
          "age", "brand", "make", "model", "number", "plate", "breed", "name")

# A "whats my ..." that turns out to be a question about the world ("whats my best option") is
# not a recall of a thing they said, so the words that open a question are not a thing.
QUESTION_WORDS = frozenset("""best better option options chance chances odds next plan plans point
    problem issue deal story time day week month year""".split())

ASK = re.compile(r"\bwhat(?:\s+is|\s*'s|s)?\s+(?P<attr>" + "|".join(
    sorted(THEIRS, key=len, reverse=True)) + r")\s+(?:am\s+i)\b", re.I)
OF_MINE = re.compile(r"\bwhat(?:\s+is|\s*'s|s)?\s+my\s+(?P<attr>" + "|".join(
    sorted(THEIRS, key=len, reverse=True)) + r")\b", re.I)
# "again", "now", "these days" are the person saying they have asked before: they say nothing
# about the line, and they are not a new question.
FILLER = frozenset("""again now then today still also please again? so and but ok okay oh""".split())

# The same recall when the thing they ask for is a figure, which is the commonest way a person
# leans on the chat for arithmetic: "my rent is 900 a month" / "whats my rent" and "its 32 a month
# for 20 gig" / "what was i paying". On main both asks fell through - the first to the PAYE card
# ("pay" is a word in the question, so the income-tax entry took it) and the second to a live-price
# hedge ("I can't look up live prices, sorry") that told a person who had just given the price
# that the bot could not find it.
#
# So the attribute words are not a list here: any short thing they name in "whats my <thing>"
# counts, and it is answered only when one of their own lines holds that thing **with a figure in
# it**. "whats my size" with "im a size 12" is the same reading, and "whats my plan for saturday"
# with nothing said about a figure is left alone.
#
# A figure is a number with a currency sign or a period ("32 a month", "£40"), and a line about
# what they earn or save is not a cost - "i earn 2400 a month" must not answer "what am i paying"
# with their salary. The pay-ask itself ("what am i paying", "how much do i pay", "what was i
# paying for it") names no thing of its own, so the newest cost in the chat is the one answered.
A_FIGURE = re.compile(
    r"(?:[\u00a3$\u20ac]\s*\d[\d,.]*"
    r"|\b\d[\d,.]*\s*(?:a|per|each)\s+(?:month|week|year|fortnight|day|week|month)\b"
    r"|\b\d[\d,.]*\s*(?:quid|pounds?|dollars?|euros?|pm)\b)", re.I)
# A figure with no money in it is not a price. Earning and saving were the first two ("i earn 2400
# a month" is not what they pay; "i spend 200 a month on food" is what they pay, so spending is not
# here); what is done for a length of time is the same shape and was read
# as a cost - "i work 40 a week" then "what am i paying" answered "You told me you work 40 a week",
# and "i eat 5 a day" then "how much is it" the same. The doing words are here; `hour`, `train`
# and `bus` are not, because "i pay 12 an hour for the cleaner" and "my season ticket is 200 a
# month for the train" are real costs.
NOT_A_COST = re.compile(
    r"\b(?:earn|earns|earned|earning|salary|wage|wages|take[- ]home|save|saves|saved|saving"
    r"|work|works|worked|working|shift|shifts"
    r"|eat|eats|ate|eating|drink|drinks|drank|drinking"
    r"|run|runs|ran|running|walk|walks|walked|walking|swim|swims|swam|swimming"
    r"|sleep|sleeps|slept|sleeping|study|studies|studied|studying|read|reads|reading)\b", re.I)
PAY_ASK = re.compile(
    r"\b(?:what|how\s+much)\b[^.!?]*?\b(?:am|was|are|were|do|did)\s+i\b[^.!?]*?"
    r"\b(?:pay|paying|paid|cost|costs|costing)\b", re.I)
# "how much is it" is the same ask with the thing elided, and it is only read when the line just
# before it named a figure: on its own it is a price question about the world.
COST_ASK = re.compile(r"^\W*(?:and\s+|so\s+|ok\s+|okay\s+)?how\s+much\s+(?:is|was)\s+it\b", re.I)
WHATS_MY = re.compile(r"\bwhat(?:\s+is|\s*'s|s)?\s+my\s+(?P<attr>[a-z][a-z' -]{1,24}?)\b", re.I)


def _their_attribute(low):
    """The attribute they are asking after, or "" when the line is not that ask."""
    for pattern in (ASK, OF_MINE):
        match = pattern.search(low)
        if match:
            return " ".join(match.group("attr").lower().split())
    return ""


def _stem(word):
    """The word with a plural or a participle taken off, so "colour" and "colouring" match."""
    word = str(word or "").lower().strip("'")
    for suffix in ("ing", "ed", "es", "s"):
        if len(word) > len(suffix) + 3 and word.endswith(suffix):
            return word[:-len(suffix)]
    return word


def _names(tokens, attribute):
    """True when every word of the attribute is one of these tokens, in any of its forms."""
    stems = {_stem(token) for token in tokens}
    return all(_stem(word) in stems for word in attribute.split())


def _the_phrase_of_theirs(attribute, memory, needs_a_figure=False):
    """The newest thing they said about this attribute, said back, or "".

    Their own asks are skipped: "what size am i" a turn earlier has the word in it and states
    nothing, and reading it back would answer the question with the question. The first line
    that states a fact with the attribute in it is the one answered from.

    `needs_a_figure` is for the ask that wants a number: the line only answers it when it holds
    one, so a line about the thing and nothing else passes.
    """
    turns = (memory or {}).get("turns") if isinstance(memory, dict) else None
    if not turns:
        return ""
    for turn in reversed(turns):
        line = (turn or {}).get("user") or ""
        if not line:
            continue
        if not _names(re.findall(r"[a-z']+", line.lower()), attribute):
            continue
        if needs_a_figure and not (A_FIGURE.search(line) and not NOT_A_COST.search(line)):
            continue
        phrase = _phrase(line)
        if not phrase or not _names(re.findall(r"[a-z']+", phrase.lower()), attribute):
            # A question, or a restating that drops the attribute ("my colouring is warm,
            # autumn" comes back as "autumn"): neither answers a question about the attribute.
            continue
        return phrase
    return ""


def _a_cost_line(line):
    """True when this line of theirs names a figure for something they pay."""
    line = str(line or "")
    return bool(line) and bool(A_FIGURE.search(line)) and not NOT_A_COST.search(line)


def _the_newest_cost(memory):
    """The newest thing they said with a figure in it, said back, or ""."""
    turns = (memory or {}).get("turns") if isinstance(memory, dict) else None
    if not turns:
        return ""
    for turn in reversed(turns):
        line = (turn or {}).get("user") or ""
        if _a_cost_line(line):
            return _phrase(line)
    return ""


def _the_cost_just_before(memory):
    """The figure said on the line before this one, said back, or "".

    For "how much is it", which names nothing of its own: only the line immediately before it can
    be the it, and with no figure there the ask is a price question about the world.
    """
    turns = (memory or {}).get("turns") if isinstance(memory, dict) else None
    if not turns:
        return ""
    line = (turns[-1] or {}).get("user") or ""
    return _phrase(line) if _a_cost_line(line) else ""


def _phrase(line):
    """The line as a fact about them, in the store's own words."""
    from . import memory_store  # local: the store imports this package's parts at load time
    try:
        return memory_store._told_phrase(line)
    except Exception:  # noqa: BLE001 - a restating that fails answers nothing
        return ""


CONTRACTIONS = (("you are", "you're"), ("you have", "you've"), ("it is", "it's"),
                ("that is", "that's"), ("i am", "i'm"))


def _the_value(phrase):
    """The fact without the frame: "your budget is about 100 pounds" -> "about 100 pounds"."""
    for pattern in (r"^you(?:'re| are| were) (.+)$", r"^you(?:'ve| have) (.+)$",
                    r"^your .+? is (.+)$", r"^your (.+)$",
                    # a cost they gave with the thing elided: "its 32 a month for twenty gig",
                    # "you pay 32 a month for your phone"
                    r"^it(?:'s|s) (.+)$", r"^you (?:pay|paid) (.+)$",
                    r"^(?:it )?costs? (.+)$"):
        match = re.match(pattern, phrase)
        if match:
            return match.group(1).strip().rstrip(".")
    return ""


# The slot words: "did i say when we were going", "when did i say we were going", and the
# same for "where". Only the two slots with a value that can be read off a line - a time and a
# place - are read here; a slot with no word for it is left to whatever answers it now.
WHEN_ASK = re.compile(
    r"\b(?:did|do)\s+(?:i|we)\s+say\s+when\b(?P<rest>.*)"
    r"|\bwhen\s+did\s+(?:i|we)\s+say\b(?P<rest2>.*)"
    r"|\bwhen\s+(?:was|is)\s+it\s+(?:that\s+)?(?:i|we)\s+said\b(?P<rest3>.*)", re.I)
WHERE_ASK = re.compile(
    r"\b(?:did|do)\s+(?:i|we)\s+say\s+where\b(?P<rest>.*)"
    r"|\bwhere\s+did\s+(?:i|we)\s+say\b(?P<rest2>.*)", re.I)

MONTHS = ("january february march april may june july august september october november "
          "december").split()
WEEKDAYS = "monday tuesday wednesday thursday friday saturday sunday".split()
TIME_WORDS = frozenset(MONTHS + WEEKDAYS + """weekend tonight tomorrow today morning
afternoon evening night midday noon christmas easter summer winter spring autumn""".split())
# "next week", "in three weeks", "at 7", "7.30pm": a time said as a span or a clock rather
# than a name out of the list above.
TIME_SPAN = re.compile(
    r"\b(?:next|last|this)\s+(?:week|month|year|summer|winter|spring|autumn)\b"
    r"|\bin\s+(?:about\s+)?\d+\s+(?:days?|weeks?|months?|years?)\b"
    r"|\b\d{1,2}(?:[.:]\d\d)?\s*(?:am|pm)\b|\bat\s+\d{1,2}\b", re.I)
# A place said with the preposition that makes it one: "near the royal mile". Read only after
# these words, so "we want to be there" and "in october" are not places.
PLACE = re.compile(
    r"\b(?:near|next to|close to|round the corner from|opposite)\s+"
    r"(?P<place>[a-z][a-z'\u2019]*(?:\s+[a-z][a-z'\u2019]*){0,3})", re.I)
# The words an ask about a slot is built out of: what is left is the subject it belongs to.
# The ask for a size: "how big is the kitchen", "how big did i say the kitchen was", "what size
# tin did i say", "how wide was it". The ask about the person themselves ("what size am i") is
# not this one - that is a fact of theirs, answered by the attribute reader below.
SIZE_ASK = re.compile(
    r"\b(?:how\s+(?:big|large|wide|long|tall|high|deep)"
    r"|what\s+(?:size|dimensions?|measurements?)"
    r"|how\s+many\s+(?:metres|meters|feet|foot|ft|centimetres|centimeters|cm"
    r"|square\s+(?:metres|meters|feet)))\b(?P<rest>[^?.!]*)", re.I)
# "how big should the tin be for 8 people" is advice about a tin, not a size they gave, so a line
# with one of these words in it is left to whatever answers it now.
SIZE_ADVICE = re.compile(r"\b(?:should|shall|would|could|can|might|will|need|needs|enough"
                         r"|recommend|best)\b", re.I)
# A measure as people write it: "3 by 2 metres", "20cm", "12 square metres", "1.5 litres". The
# unit is what makes it a size, so "two cats" and "20 pounds" are not read as one.
A_SIZE = re.compile(
    r"(?P<measure>\b\d+(?:[.,]\d+)?\s*(?:by|x|\u00d7)\s*\d+(?:[.,]\d+)?\s*"
    r"(?:m|metres?|meters?|ft|feet|foot|cm|centimetres?|centimeters?|inches|inch)\b"
    r"|\b\d+(?:[.,]\d+)?\s*(?:square|sq)\s*(?:metres?|meters?|feet|foot|ft|m)\b"
    r"|\b\d+(?:[.,]\d+)?\s*(?:m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|foot"
    r"|inches|inch|litres?|liters?|ml)\b)"
    r"(?P<after>\s+[a-z][a-z'-]*)?", re.I)
# A figure they gave, asked for again by the word for it: "what was my salary again" after
# "its 32k a year". The salary word is not in the line that gives the figure, so nothing reads
# it, and the ask reached a card about a German phrase. A per-year amount is read only for the
# words that mean a yearly figure, and every other money word has to be in the line itself.
SALARY_WORDS = ("salary", "pay", "wage", "wages", "income", "earnings")
MONEY_WORDS = SALARY_WORDS + ("budget", "price", "cost", "rent", "savings", "deposit")
# The word for the figure can carry a qualifier: "whats my current salary", "my annual salary",
# "my real wage", "my hourly pay". The ask is the same one, and without the qualifier read the
# figure is in the store and the turn answers "I only know what you tell me, and you've not said
# what your current salary is" - a denial of a line said one turn earlier.
MONEY_QUALIFIER = (
    "current", "currently", "annual", "annually", "monthly", "weekly", "hourly", "yearly",
    "real", "actual", "actually", "basic", "gross", "net", "total", "usual", "normal",
    "present", "own",
)
MONEY_ASK = re.compile(
    r"\bwhat(?:'s| is| was|s)?\s+(?:my|our|their|his|her)\s+"
    r"(?:(?:" + "|".join(MONEY_QUALIFIER) + r")\s+)?(?P<what>" + "|".join(
        sorted(MONEY_WORDS, key=len, reverse=True)) + r")\b"
    r"|\bhow much\s+(?:was|is|were|did\s+(?:i|we)\s+say)\s+(?:my|our|the|their|his|her)\s+"
    r"(?:(?:" + "|".join(MONEY_QUALIFIER) + r")\s+)?(?P<what2>"
    + "|".join(sorted(MONEY_WORDS, key=len, reverse=True)) + r")\b", re.I)
# A figure a year: "32k", "32k a year", "£32,000 a year", "45,000 per annum".
A_PER_YEAR = re.compile(
    r"\b\d+(?:\.\d+)?\s*k\b(?:\s*(?:a|per)\s*(?:year|annum))?"
    r"|\u00a3?\s?\d[\d,]{3,}\s*(?:a|per)\s*(?:year|annum)\b", re.I)
# Any money said on a line, for the words that are not about a year.
A_MONEY = re.compile(
    r"(?:\u00a3\s?\d[\d,]*(?:\.\d\d)?"
    r"|\b\d[\d,]*(?:\.\d+)?\s*(?:pounds?|quid|dollars?|euros?|grand)\b"
    r"|\b\d[\d,]{2,}\b)"
    r"(?:\s*(?:a|per)\s*(?:month|week|year|fortnight))?", re.I)
SLOT_STOP = frozenset("""i we you me us my our it its the a an to be been being was were are is
am do did does say said about that this of for in on at and but so then just again please oh ok
okay actually""".split())

# The attribute the ask names and the value the chat gave in other words. "what did i tell you his
# age was" names the age, and the line that gives it is "hes a labrador, 9": the word "age" is in
# the question and never in the answer, which is why the attribute reader above cannot find it and
# the turn was answered "I don't know enough to answer that honestly." The same shape is said the
# other way round - "how old did i say he was" - and with the person's own age.
AGE_ASK = re.compile(
    r"\b(?:what|how\s+old)\b[^.?!]{0,40}?\b(?:did|do)\s+i\s+"
    r"(?:say|tell\s+you|told\s+you|think|thought|mention|mentioned)\b[^.?!]{0,30}?\b(?:age|old)\b"
    r"|\bwhat\s+(?:was|is)\s+(?P<whose>his|her|their|my|our|its)\s+age\b"
    r"|\bhow\s+old\s+(?:did|do)\s+i\s+(?:say|tell\s+you|told\s+you|think|mention)\b", re.I)
# "how often did i say i go", "how many times a week did i say": the frequency they gave, asked
# for by name when the line that gave it says "three times a week" ("often" is in neither).
OFTEN_ASK = re.compile(
    r"\bhow\s+often\b[^.?!]{0,30}?\b(?:did|do)\s+i\s+(?:say|tell\s+you|told\s+you|mention)\b"
    r"|\bhow\s+many\s+times\b[^.?!]{0,30}?\b(?:did|do)\s+i\s+(?:say|tell\s+you|mention)\b"
    r"|\bhow\s+often\s+(?:was|is)\s+it\b[^.?!]{0,12}?\bagain\b", re.I)
# A number a person or an animal can be, said as a clause of its own: "hes a labrador, 9",
# "im 42 and want to lose a stone". Only the number as a clause counts - a figure with a unit or
# a thing after it is a different fact ("6 of us", "40 a week", "2 kids") - because the age is
# what nobody says with the word "age" in it.
AN_AGE_CLAUSE = re.compile(
    r"(?:^|[,;]|\bis\b|\bwas\b|\bim\b|\bi'm\b|\bam\b|\b-\s*)\s*(?P<n>\d{1,3})\s*"
    r"(?=$|[,.;!?]|\s+and\b|\s+but\b)",
    re.I)
# A line about a person or a pet is where an age clause belongs. "theres 6 of us" is a count
# of people, not somebody's age, so a line counting them is passed over.
SOMEBODY = re.compile(
    r"\b(?:i|im|i'm|me|myself|he|she|him|her|his|they|them|their|my|our"
    r"|son|daughter|lad|girl|boy|kid|kids|baby|toddler|mum|mom|dad|husband|wife|partner|brother"
    r"|sister|nan|gran|grandad|dog|cat|pup|puppy|labrador|retriever|terrier|shepherd|spaniel"
    r"|collie|hound|mutt|rabbit|hamster|horse)\b", re.I)
A_COUNT_OF_PEOPLE = re.compile(r"\b\d+\s+(?:of\s+us|people|adults)\b", re.I)

# The frequency they gave, as they said it. Only the shapes a person uses for a habit they keep,
# so a date ("twice in june") and a count of something ("3 times a day" for pills) are not habits
# the ask is about unless the ask is that one.
A_HABIT_SAID = re.compile(
    r"\b(?:(?:once|twice|three|four|five|six|seven|eight|nine|ten|\d+)\s+times?\s+"
    r"(?:a|per|each)\s+(?:day|week|month|year)"
    r"|(?:once|twice)\s+(?:a|per)\s+(?:day|week|month|year)"
    r"|every\s+(?:day|week|weekend|morning|evening|night)"
    r"|most\s+(?:days|weeks|mornings|evenings)|\bdaily\b)", re.I)

def _the_slot_ask(low):
    """("when", "where" or "size", the subject words of the ask) or ("", set()) for a line
    that asks after no slot at all."""
    for slot, pattern in (("when", WHEN_ASK), ("where", WHERE_ASK)):
        match = pattern.search(low)
        if match:
            rest = next((group for group in match.groups() if group), "")
            return slot, _the_subject(rest)
    # The three attributes the chat gives without ever naming them: an age said as a number, how
    # often they do something, and how many of them there are.
    for slot, pattern in (("age", AGE_ASK), ("often", OFTEN_ASK), ("off_with", OFF_WITH_ASK)):
        if pattern.search(low):
            return slot, set()
    if _their_attribute(low):
        # "what size am i again" is a fact about them, not a size of something.
        return "", set()
    match = SIZE_ASK.search(low)
    if match and not SIZE_ADVICE.search(low):
        return "size", _the_subject(match.group("rest"))
    match = MONEY_ASK.search(low)
    if match:
        what = next((group for group in match.groups() if group), "").lower()
        return "money:" + what, set()
    return "", set()


def _the_subject(rest):
    """The words the ask names the thing by: "when we were going" -> {"go"}."""
    return {_stem(word) for word in re.findall(r"[a-z']+", rest.lower())
            if word not in SLOT_STOP}


def _a_time(line):
    """The time said in this line, as they said it, or "".

    The month or the day comes first: "a long weekend in october" is about october, and the
    "weekend" in it says less. A span ("next week", "at 7") is read before a loose word
    ("weekend", "morning"), because a span is what the person meant when they gave both.
    """
    low = line.lower()
    named = [word for word in re.findall(r"[a-z'\u2019]+", low) if word in MONTHS + WEEKDAYS]
    if named:
        return named[0].capitalize()
    span = TIME_SPAN.search(low)
    if span:
        return " ".join(span.group(0).split())
    for word in re.findall(r"[a-z'\u2019]+", low):
        if word in TIME_WORDS:
            return word
    return ""


def _a_place(line):
    """The place said in this line with its preposition - "near the royal mile" - or ""."""
    match = PLACE.search(line)
    if not match:
        return ""
    place = " ".join(match.group("place").split())
    if not place or {_stem(word) for word in place.split()} <= SLOT_STOP:
        return ""
    return " ".join(match.group(0).split())


def _a_size(line, subject):
    """The size said in this line, as they said it, or "".

    The noun the ask names is carried with the measure when the line puts it there: "a chocolate
    sponge in a 20cm tin" is "20cm tin", which is what a person would say back.
    """
    for match in A_SIZE.finditer(line):
        measure = " ".join(match.group("measure").split())
        after = (match.group("after") or "").strip().lower()
        if after and subject and _stem(after) in subject:
            return measure + " " + after
        return measure
    return ""


# The way a line is said when it is about the thing the line before named rather than a new one.
PRONOUN_LINE = re.compile(r"^\s*(?:its|it is|it's|that's|thats|theres|there's|theyre|they are"
                          r"|hes|shes|were|we are)\b", re.I)


def _the_size_recall(subject, lines):
    """The size of the thing the ask names, from their own lines, or ""."""
    for index in range(len(lines) - 1, -1, -1):
        line = lines[index]
        value = _a_size(line, subject)
        if not value:
            continue
        said = {_stem(word) for word in re.findall(r"[a-z']+", line.lower())}
        if subject:
            if said & subject:
                return value
            older = lines[index - 1] if index else ""
            if PRONOUN_LINE.match(line) and subject & {_stem(word)
                                                      for word in re.findall(r"[a-z']+", older.lower())}:
                # "its small, about 3 by 2 metres" right after "we're redecorating the kitchen":
                # the line says where the size belongs by following the one that named it.
                return value
            continue
        if len(lines) - index <= 2:
            # No noun in the ask ("how big is it"): only a measure said in the last two lines.
            return value
    return ""


def _the_money_recall(what, lines):
    """The figure they gave for this money word, as they said it, or ""."""
    for line in reversed(lines):
        low = line.lower()
        said = {_stem(word) for word in re.findall(r"[a-z']+", low)}
        if what in SALARY_WORDS:
            match = A_PER_YEAR.search(line)
            if match:
                return " ".join(match.group(0).split())
            continue
        if _stem(what) not in said:
            # "what was the price" is only answered from a line that says the price.
            continue
        match = A_MONEY.search(line)
        if match:
            return " ".join(match.group(0).split())
    return ""



# An attribute asked for again with nothing named beside it: "and what size did i say", "how short
# did i say it was", "what time did i say". Every reader above wants the thing the attribute
# belongs to, and on these lines there is none - the thing it belongs to is the chat itself. So
# the value is looked for in their own lines, newest first, and the line that holds it is the
# answer, in the store's own idiom ("You said: ..."). What comes back has to be a value of the
# kind the ask named, so "how long did i say it was" after a walk finds no length and the turn is
# left alone.
SAID_ASK = re.compile(
    r"^(?:and\s+|so\s+|but\s+|also\s+|oh\s+|ok\s+|okay\s+)?"
    r"(?:(?:what|which)\s+(?P<attr>[a-z][a-z' -]{1,20}?)\s+"
    r"(?:did|do|have)\s+(?:i|we)\s+(?:say|give|mention|tell\s+you)"
    r"|how\s+(?P<how>[a-z]+)\s+did\s+(?:i|we)\s+say)"
    r"\b[^?.!]*$", re.I)

# The value of each kind, as people write it. A kind is only read when the ask names it, so a
# "how long" ask never lands on a price and a "what size" ask never lands on a day.
# The single letters are whole tokens, not `\b` words: an apostrophe is a word boundary, so `i'm`
# held an `m` and `it's` an `s`, and "i'm going to spain in june" answered "what size did i say"
# with "You said m." - which is worse than the wrong card it replaced.
SIZE_VALUE = re.compile(
    r"(?:(?<![\w'])(?:xs|s|m|l|xl|xxl|xxxl)(?![\w'])"
    r"|\b(?:small|medium|large|extra\s+large"
    r"|size\s+\d{1,2}|(?:a\s+)?\d{1,2}\s*(?:-|to)\s*\d{1,2})\b)", re.I)
LENGTH_VALUE = re.compile(
    r"\b(?:long|short|shoulder[- ]length|past\s+(?:my\s+)?shoulders|bob|crop|pixie"
    r"|just\s+(?:above|below)\s+\w+|\d+\s*(?:cm|inches|inch))\b", re.I)
WEIGHT_VALUE = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:kg|kilo|kilos|kilograms|st|stone|stones|lbs?|pounds)\b", re.I)
AGE_VALUE = re.compile(
    r"\b(?:\d{1,2}\s*(?:years?\s*old|yr|yrs)?|aged\s+\d{1,2})\b", re.I)
COLOUR_VALUE = re.compile(
    r"\b(?:red|blue|green|black|white|grey|gray|brown|beige|cream|navy|pink|purple|orange"
    r"|yellow|gold|silver|teal|turquoise|burgundy|maroon|khaki|olive|charcoal)\b", re.I)

# The ask word, and the kind of value it is asking for.
VALUE_KINDS = {
    "size": SIZE_VALUE, "shoe size": SIZE_VALUE, "ring size": SIZE_VALUE,
    "colour": COLOUR_VALUE, "color": COLOUR_VALUE,
    "weight": WEIGHT_VALUE, "age": AGE_VALUE,
    "length": LENGTH_VALUE, "hair": LENGTH_VALUE,
}
HOW_KINDS = {
    "short": LENGTH_VALUE, "long": LENGTH_VALUE, "tall": LENGTH_VALUE,
    "big": SIZE_VALUE, "large": SIZE_VALUE, "small": SIZE_VALUE,
    "heavy": WEIGHT_VALUE, "old": AGE_VALUE,
}


def _the_value_kind(attribute, how):
    """The pattern a line has to hold to answer this ask, or None."""
    attribute = " ".join(str(attribute or "").lower().split())
    if attribute:
        if attribute in VALUE_KINDS:
            return VALUE_KINDS[attribute]
        if attribute in ("time", "day", "date", "month", "year", "week"):
            return _a_time
        if attribute in MONEY_WORDS or attribute in ("price", "cost"):
            return lambda line: A_MONEY.search(line)
        return None
    return HOW_KINDS.get(" ".join(str(how or "").lower().split()))


# Their own questions are not a statement of a value: "can i exchange it for a large" holds the
# word "large" and is not the size they gave ("a medium", two turns earlier).
THEIR_QUESTION = re.compile(
    r"^\W*(?:what|whats|what's|how|when|where|which|who|why|can|could|should|shall|would|will"
    r"|does|do|did|is|are|was|were|have|has|any|anything|tell\s+me|remind\s+me)\b", re.I)


def _the_line_that_says_it(text, memory):
    """Their own line that holds the value asked for, or "".

    Read newest first, and only the lines of theirs that are not themselves asks: reading back
    "what size did i say" a turn later would answer the ask with an ask.
    """
    low = " ".join(str(text or "").lower().split())
    match = SAID_ASK.match(low)
    if not match:
        return ""
    kind = _the_value_kind(match.group("attr"), match.group("how"))
    if kind is None:
        return ""
    turns = (memory or {}).get("turns") if isinstance(memory, dict) else None
    if not turns:
        return ""
    for turn in reversed(turns):
        line = " ".join(str((turn or {}).get("user") or "").split())
        if not line or not (kind(line) if callable(kind) else kind.search(line)):
            continue
        if THEIR_QUESTION.match(line) or SAID_ASK.match(line.lower()):
            continue
        if _their_attribute(line.lower()):
            continue
        return line
    return ""


def _the_values_the_kind_takes(text, line):
    """Every value of the kind the ask names that their line holds, as they said it.

    One value is the answer on its own - "i ordered a coat in a medium" answers "what size did i
    say" with "medium", which is what the store's own reader says - and more than one leaves the
    ask ambiguous ("long and curly, past my shoulders"), so the line itself is the safest answer.
    """
    low = " ".join(str(text or "").lower().split())
    match = SAID_ASK.match(low)
    if not match:
        return []
    kind = _the_value_kind(match.group("attr"), match.group("how"))
    if kind is None:
        return []
    if callable(kind):
        value = " ".join(str(kind(line) or "").split())
        return [value] if value else []
    found, seen = [], set()
    for hit in kind.finditer(line or ""):
        value = " ".join(hit.group(0).split())
        key = _stem(value)
        if value and key not in seen:
            seen.add(key)
            found.append(value)
    return found


def _the_value_said(text, memory):
    """The reply for an attribute asked for again with nothing named beside it, or None.

    The store answers the asks it files a fact for - "how old did i say he was" is "Your son is
    14." - and a quotation of the line is a worse answer than that, so this reader only speaks
    when the store has nothing to say, and it says the value in the store's own voice whenever
    one value is what the ask was for.
    """
    line = _the_line_that_says_it(text, memory)
    if not line:
        return None
    from .memory_store import respond as _the_store_says
    if _the_store_says(text, memory):
        return None
    values = _the_values_the_kind_takes(text, line)
    said = values[0] if len(values) == 1 else line
    reply = 'You said: "' + said + '"' if len(values) != 1 else "You said " + said + "."
    last = _the_last_reply(memory)
    if reply.lower().rstrip(".") in last.lower():
        # This very answer is the last thing said: saying it again in the same words reads as a
        # machine, so the second time says it is the same answer.
        return "Still the same: " + said
    return reply


def _the_slot_recall(text, memory):
    """The reply for a line that asks after a slot of what they said, or None."""
    low = " ".join(str(text or "").lower().split())
    if not low:
        return None
    slot, subject = _the_slot_ask(low)
    if not slot:
        return None
    turns = (memory or {}).get("turns") if isinstance(memory, dict) else None
    if not turns:
        return None
    if slot in ("age", "often", "off_with"):
        value = ""
        if slot == "age":
            value = _the_age_they_gave(turns, low)
        elif slot == "often":
            value = _the_habit_they_gave(turns)
        else:
            value = _the_off_with_they_gave(turns)
        return _the_slot_reply(value, memory) if value else None
    if slot.startswith("money:"):
        lines = [str((turn or {}).get("user") or "") for turn in turns]
        value = _the_money_recall(slot.split(":", 1)[1], lines)
        return _the_slot_reply(value, memory) if value else None
    if slot == "size":
        lines = [str((turn or {}).get("user") or "") for turn in turns]
        value = _the_size_recall(subject, lines)
        return _the_slot_reply(value, memory) if value else None
    for turn in reversed(turns):
        line = (turn or {}).get("user") or ""
        if not line:
            continue
        value = _a_time(line) if slot == "when" else _a_place(line)
        if not value:
            continue
        said = {_stem(word) for word in re.findall(r"[a-z']+", line.lower())}
        if subject and not (said & subject):
            # A time said in a line about something else is not an answer to this ask: "i go
            # to the gym on a monday" is not when the boiler was serviced.
            continue
        return _the_slot_reply(value, memory)
    return None
# "and what was i off with again": the thing they were off sick with, which the chat said as
# "ive been off sick since monday with a chest infection". The words "off" and "with" are in the
# ask and nowhere in the line that gives it, so nothing could look it up.
OFF_WITH_ASK = re.compile(
    r"\bwhat\s+(?:was|is)\s+i\s+off\b|\bwhat\s+did\s+i\s+say\s+i\s+was\s+off\b"
    r"|\bwhat\s+was\s+i\s+off\s+(?:sick\s+)?with\b", re.I)
# The illness named after "with" in a line about being off: "off sick since monday with a chest
# infection". Only the tail of the line, and only after a word that says they were off, so
# "i went with my sister" names nobody's illness.
OFF_WITH_SAID = re.compile(
    r"\b(?:off\s+(?:sick|work|ill)|been\s+off|signed\s+off)\b[^.?!]*?\bwith\s+"
    r"(?P<thing>an?\s+)?(?P<what>[a-z][a-z' -]{3,30})\s*$", re.I)


def _the_age_they_gave(turns, low):
    """The age said as a number of its own, with the owner from the ask, or "".

    The newest line that gives one is the one answered from, and a line that counts people
    ("theres 6 of us") is not an age: the number has to stand as a clause of its own.
    """
    whose = "their"
    named = re.search(r"\b(his|her|their|my|our|its)\b[^.?!]{0,12}?\b(?:age|old)\b", low, re.I)
    if named:
        whose = named.group(1).lower()
    else:
        said_of = re.search(r"\b(he|she|they)\b", low, re.I)
        if said_of:
            whose = {"he": "his", "she": "her", "they": "their"}[said_of.group(1).lower()]
    if whose == "my":
        whose = "your"
    for turn in reversed(turns):
        line = str((turn or {}).get("user") or "")
        if not line or A_COUNT_OF_PEOPLE.search(line) or not SOMEBODY.search(line):
            continue
        found = AN_AGE_CLAUSE.search(line)
        if not found:
            continue
        number = found.group("n")
        if not (0 < int(number) < 121):
            continue
        # "my son is 7" is answered by naming him, the way the store does it: "your son is 7"
        # says whose age it is, where "his age was 7" leaves the person to work that out.
        named_person = re.search(
            r"\b(?:my|our)\s+(?P<who>[a-z]+)\s+(?P<was>is|was)\s+" + re.escape(number) + r"\b",
            line, re.I)
        if named_person:
            return "your " + named_person.group("who").lower() + " " + named_person.group("was").lower() \
                + " " + number

        if whose in ("their", "its") and re.search(r"\b(?:i|im|i'm|am)\b", line, re.I):
            return "your age was " + number  # their own age, said about themselves
        if whose == "your":
            return "your age was " + number
        return whose + " age was " + number
    return ""


def _the_off_with_they_gave(turns):
    """What they said they were off sick with, or ""."""
    for turn in reversed(turns):
        line = str((turn or {}).get("user") or "")
        if not line:
            continue
        found = OFF_WITH_SAID.search(line)
        if found:
            thing = " ".join(found.group("what").lower().split())
            article = "an " if (found.group("thing") or "").strip().lower() == "an" else "a "
            return "you were off with " + article + thing
    return ""


def _the_habit_they_gave(turns):
    """How often they said they do it, as they said it, or ""."""
    for turn in reversed(turns):
        line = str((turn or {}).get("user") or "")
        if not line:
            continue
        found = A_HABIT_SAID.search(line)
        if found:
            return " ".join(found.group(0).lower().split())
    return ""


def _the_slot_reply(value, memory):
    """The slot value as a friend says it, never as the same sentence twice."""
    reply = "You said " + value + "."
    if reply.lower() in _the_last_reply(memory).lower():
        return "Still " + value + "."
    return reply


def _the_last_reply(memory):
    turns = (memory or {}).get("turns") if isinstance(memory, dict) else None
    if not turns:
        return ""
    return str((turns[-1] or {}).get("bot") or "")


def _spoken(phrase):
    """The phrase the way a person says it: the store writes contractions out."""
    # "its 32 a month" is "it is" said short: a phrase of theirs that opens with it has no
    # possessive to keep ("its name is Rufus" is filed under the name, never as a bare "its").
    phrase = re.sub(r"^its\b", "it's", str(phrase or ""))
    for full, short in CONTRACTIONS:
        phrase = re.sub(r"\b" + full + r"\b", short, phrase)
    return phrase


PAY_ASK_WORDS = frozenset((
    "how", "what", "much", "many", "do", "did", "does", "i", "im", "my", "the", "a", "an", "is",
    "was", "are", "were", "for", "of", "to", "in", "on", "at", "it", "that", "this", "me", "you",
    "your", "get", "got", "getting", "pay", "paid", "pays", "paying", "payment", "payments",
    "wage", "wages", "salary", "salaries", "earn", "earns", "earned", "earning", "make", "makes",
    "made", "making", "take", "home", "takehome", "and", "or", "per", "plus", "now", "again",
    "current", "currently", "exact", "exactly", "actual", "actually", "latest", "today", "so",
    "far", "have", "has", "had", "been", "like", "think", "about", "guess", "roughly", "all",
    "just", "really", "total", "figure", "number", "amount", "sum", "much", "there", "then",
))


def _the_ask_names_something_new(low, memory):
    """True when the ask names a thing not one of their own lines ever mentioned.

    "how much do i pay for rent" names the rent, and nothing in the chat is about rent, so the
    wage they gave is a figure for something else. "how much is my phone bill" names the phone
    bill, which the chat does hold, and that figure is the answer they want.
    """
    turns = (memory or {}).get("turns") if isinstance(memory, dict) else None
    said = set()
    for turn in turns or ():
        line = str((turn or {}).get("user") or "").lower()
        said |= {_stem(word) for word in re.findall(r"[a-z']+", line)}
    asked = {_stem(word) for word in re.findall(r"[a-z']+", low)}
    asked -= {_stem(word) for word in PAY_ASK_WORDS}
    return bool(asked - said)


def _the_recall(text, memory):
    """The reply for a line that asks for a fact of theirs by name, or None."""
    low = " ".join(str(text or "").lower().split())
    if not low:
        return None
    said_value = _the_value_said(low, memory)
    if said_value is not None:
        return said_value
    slot = _the_slot_recall(low, memory)
    if slot is not None:
        return slot
    attribute = _their_attribute(low)
    wants_a_figure = False
    if not attribute:
        if PAY_ASK.search(low):
            wants_a_figure = True
        elif COST_ASK.match(low):
            wants_a_figure = True
        else:
            named = WHATS_MY.search(low)
            candidate = " ".join(named.group("attr").split()) if named else ""
            if not candidate or len(candidate.split()) > 3 or candidate.split()[0] in QUESTION_WORDS:
                return None
            attribute = candidate
            wants_a_figure = True
    if attribute:
        phrase = _the_phrase_of_theirs(attribute, memory, needs_a_figure=wants_a_figure)
    elif COST_ASK.match(low):
        phrase = _the_cost_just_before(memory)
    else:
        phrase = _the_newest_cost(memory)
    if not phrase:
        return None
    if (PAY_ASK.search(low) and _the_ask_names_something_new(low, memory)
            and not repeat.the_figure_they_gave(text, memory)):
        # "how much do i pay for rent" and "how much do i get paid for overtime" name a thing none
        # of their own lines mentioned, and the wage is a figure for something else: both were
        # answered "You told me you get paid 2000 a month." - true, and the answer to neither. A
        # pay ask that stays inside what the chat holds ("how much is my phone bill" after "my
        # phone bill is eighteen a month") is read back as before, so the recall is kept.
        return None
    said = _spoken(phrase)
    value = _the_value(said)
    # Asking again on the next turn is the same fact, not a new one: a second copy of the
    # sentence is passed over by the never-repeat rule and the turn falls to a card, so the
    # second time it is said the way a friend says it.
    # "Still 40 a month." is for the second time the recall is asked: the bot's own last reply
    # said the figure back, and a card that happens to hold the same figure is a different answer,
    # so the first recall of a figure said once in the chat says who said it.
    last = _the_last_reply(memory)
    if value and value.lower() in last.lower() and "you told me" in last.lower():
        return "Still " + value + "."
    return "You told me " + said + "."


def takes_as_it_comes(text, memory):
    """True on exactly the lines `respond` answers, and nowhere else.

    The clothes-size card declares the topic a coat chat is read as, and a card that declares
    the line takes it off a module underneath it whatever the bands say (`arbiter._as_it_comes`).
    On these lines the ask is about the person, so nothing about the world can answer it: the
    module says so itself rather than raising `PRIORITY` over every other line it reads.

    The three shapes read off a line that gave the value in other words - an age, a habit, an
    illness - are the exception, and they are not declared. The store keeps those facts itself
    and answers those asks at 7000 in its own words ("how old did i say he was" -> "Your son is
    14."), which is the answer a person already gets; declaring would take that turn off it and
    say "You said his age was 14." only because this module read the same number twice. So the
    new shapes answer only where nothing above them does, which is every line they were written
    for: the ask the store, the cards and the store's own recall all passed on.
    """
    low = " ".join(str(text or "").lower().split())
    slot, _ = _the_slot_ask(low)
    if slot in ("age", "often", "off_with"):
        return False
    return _the_recall(text, memory) is not None


TAKES_AS_IT_COMES = takes_as_it_comes


def respond(text, memory):
    return _the_recall(text, memory)
