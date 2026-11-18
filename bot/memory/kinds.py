"""The kind of detail a line asks for, and the earlier line of theirs that gives that kind.

`bot/memory/lineback.py` is the one check for "is there an earlier turn this line is about", and
its readers are matched on the words an ask shares with their lines. A whole family of asks shares
no word with the line that answers them:

    the plumber is coming tuesday at 10                              what time again
    its a worcester bosch, about six years old                       and what make is the boiler
    its a dulox one, the blue tin                                     what colour was it
    we paid 28 pounds for it                                          how much was it again

The ask names the *kind* of detail it wants - the time, the make, the colour, the price - and the
line gives that kind without ever using the word. So the question underneath is not "which line
shares a word with this ask" but "does an earlier line of theirs hold the kind of detail this line
asks for, about the thing this line names (or, when it names nothing, about anything the chat has
been on)".

This module is the table for that question and nothing else: it reads, and never decides a reply.
`bot/memory/lineback.py` asks it last, after the readers that match on words, and says the line
back in its own voice.
"""
import re

# The words an ask uses for one kind of detail. A kind that is asked for is only answered from a
# line that gives that kind, so "how much is the boiler" is not answered by the boiler's make.
ASKS = (
    ("time", re.compile(
        r"\b(?:what|which)\s+(?:time|hour)\b|\bthe\s+(?:time|hour)\b|"
        r"\b(?:what\s+time|the\s+time|the\s+hour)\s+(?:again|was\s+it|is\s+it|did\s+i)\b|"
        r"\bo'?clock\b", re.I)),
    ("day", re.compile(
        r"\b(?:what|which)\s+(?:day|date)\b|\bthe\s+(?:day|date)\b|"
        r"\b(?:what|which)\s+(?:day|date)\s+(?:again|was\s+it)\b", re.I)),
    ("when", re.compile(r"^\W*(?:and\s+|also\s+)?when\b|\bwhen\s+(?:again|was\s+it|is\s+it)\b",
                        re.I)),
    ("make", re.compile(
        r"\b(?:what|which)\s+(?:make|brand|model|manufacturer)\b|"
        r"\b(?:make|brand|model)\s+(?:again|is\s+it|was\s+it)\b", re.I)),
    ("price", re.compile(
        r"\bhow\s+much\b|\b(?:what|which)\s+(?:price|cost)\b|\bthe\s+(?:price|cost)\b|"
        r"\b(?:what|how\s+much)\s+did\s+(?:i|we|you)\s+pay\b|"
        r"\bhow\s+much\s+(?:again|was\s+it|did\s+i)\b", re.I)),
    # "how long" is how long a thing takes as often as how long it is: "how long for" in a cooking
    # chat asks for the roasting time, and the answer is not the weight of the bird they gave.
    ("duration", re.compile(r"\bhow\s+long\b", re.I)),
    ("size", re.compile(
        r"\b(?:what|which)\s+size\b|\bhow\s+(?:big|tall|wide|heavy|far)\b|"
        r"\b(?:what|which)\s+size\s+(?:again|was\s+it)\b", re.I)),
    ("age", re.compile(r"\bhow\s+old\b|\b(?:what|which)\s+age\b", re.I)),
    ("colour", re.compile(r"\b(?:what|which)\s+colou?r\b|\bcolou?r\s+(?:again|was\s+it|is\s+it)\b",
                          re.I)),
    ("place", re.compile(r"\bwhere\b|\b(?:what|which)\s+(?:place|town|city|airport)\b", re.I)),
    ("name", re.compile(
        r"\b(?:what|which)\s+(?:name|make\s+is\s+it\s+called)\b|\bwho\s+(?:made|makes|built)\b|"
        r"\bwhat'?s\s+it\s+called\b|\bwhat\s+was\s+it\s+called\b", re.I)),
)

# What a line looks like when it gives that kind of detail: the figures and words that carry it.
# These are shapes, not subjects: "at 10", "tuesday", "its a ford focus", "£40", "called milo".
GIVES = {
    "time": re.compile(
        r"\b(?:at|by|around|about|from|until|till|before|after)\s+\d{1,2}(?::\d\d)?"
        r"(?:\s*(?:am|pm|a\.m\.|p\.m\.))?\b|"
        r"\b\d{1,2}(?::\d\d)?\s*(?:am|pm)\b|\b(?:noon|midday|midnight)\b|"
        r"\b(?:half|quarter)\s+(?:past|to)\s+\w+|\bo'?clock\b", re.I),
    # A day, not a month: "we are off to spain in august" answers "when", and a day asked for with
    # "what day is it" against that line is the calendar, not the trip.
    "day": re.compile(
        r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
        r"mon|tues|tue|weds|wed|thurs|thu|fri|sat|sun|tomorrow|today|tonight|"
        r"weekend|next\s+(?:week|month|year)|this\s+week|"
        r"the\s+\d{1,2}(?:st|nd|rd|th)|\d{1,2}(?:st|nd|rd|th)\s+(?:of\s+)?[a-z]+)\b", re.I),
    "make": re.compile(
        r"\b(?:it'?s|its|it\s+is|i\s+got|we\s+got|i\s+bought|we\s+bought|they\s+installed)\s+"
        r"(?:a|an)\s+[a-z][\w-]*(?:\s+[a-z][\w-]*)?", re.I),
    "price": re.compile(
        r"[£$€]\s*\d|\b\d[\d,.]*\s*(?:pounds?|quid|euros?|dollars?)\b|"
        r"\b(?:costs?|cost\s+me|paid|paying|charges?|quote[ds]?)\b|"
        r"\b\d[\d,.]*\s*(?:pounds?|quid|euros?|dollars?)\s+a\s+(?:month|week|year)\b", re.I),
    "size": re.compile(
        r"\b\d+(?:\.\d+)?\s*(?:mm|cm|m|metres?|meters?|feet|foot|ft|inches|inch|in|kg|kilos?|"
        r"grams?|g|stone|lb|lbs|litres?|liters?|miles?|ml)\b|\bsize\s+\w", re.I),
    # An age is said of someone, and the words after it say which: "a 4 year old", "three years in
    # now" and "aged 45" are ages, "the 6 year old can do too" is a person with "can" after the
    # number, so the phrase has to end there.
    "age": re.compile(
        r"\b(?:\d{1,3}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|"
        r"fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)\s*(?:years?|months?|weeks?)"
        r"\s*(?:old)?\s*(?=$|[.,;!?]|\b(?:and|or|in|now|so)\b)|\baged\s+\d", re.I),
    "place": re.compile(
        r"\b(?:in|at|from|to|near|outside|inside|via)\s+(?!night|morning|afternoon|evening|"
        r"all|least|once|times?|moment|end|same|other|top|bottom|front|back|side|way|case|fact|"
        r"past|future|total|order|general|particular|short|full|half|the\s+(?:end|moment|same|"
        r"other|top|bottom|front|back|side|way|case|fact|total|order))[a-z][\w'-]+", re.I),
    # "when was it again" is the time or the day, whichever the chat holds, so the two day shapes
    # and the two time shapes are tried as one kind.
    "when": re.compile(
        r"\b(?:at|by|around)\s+\d{1,2}(?::\d\d)?(?!\d)|\b\d{1,2}\s*(?:am|pm)\b|"
        r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|today|tonight|"
        r"next\s+week|this\s+week)\b", re.I),
    "colour": re.compile(
        r"\b(?:red|blue|green|yellow|black|white|grey|gray|brown|pink|purple|orange|beige|"
        r"cream|navy|silver|gold|teal|turquoise|maroon|olive|grey|charcoal)\b", re.I),
    "name": re.compile(
        r"\b(?:called|named)\s+[a-z]|\bname'?s?\s+[a-z]|\b(?:it'?s|its)\s+[A-Z]", 0),
}

# A line that opens on a back-reference is a detail of the thing the line before it named.
BACK_REF = re.compile(
    r"^\W*(?:(?:and|but|so|oh|also|well|yeah|yep|ok|okay|right|alright)\W+)*"
    r"(?:it'?s|its|it\s+is|they'?re|they\s+are|that'?s|there'?s|there\s+are|"
    r"it\s+was|was|is|are)\b", re.I)

# A lead-in is not part of the ask: "and what time again", "ok so where was it".
LEAD = re.compile(
    r"^\W*(?:(?:and|but|so|oh|also|well|yeah|yep|ok|okay|right|alright|sorry|hmm|hi|hiya|hey|"
    r"hello|now|then|again|quick\s+one|mate)[ ,.!-]+)*", re.I)

# The words of the ask that are its own frame, never a thing a line is about.
FRAME = frozenset("""
a an the and but so or if my our your their his her its it this that these those of to in on at
for with from about again was were is are am be been being do does did done have has had
what which who whom whose when where why how much many long old big tall wide heavy far
time hour day date make brand model manufacturer price cost size age number place town city
airport name called colour color count weight height length say said tell told mention mentioned
pay paid paying cost costs costed charge charged spend spent buy bought
i we you me us them they he she
just only even ever before already first last next other another else more most still yet now
please pls can could would will shall may might should must cant cannot dont doesnt didnt
remember recall forget forgot know knew knews remind mind think thought reckon guess
go goes going went gone come comes coming came been
one ones thing things stuff kind sort like
""".split())


# A line that asks for a kind of detail and names nothing else is a recall only when it says so
# ("what time again", "the make", "when was that"). Without that or a named thing, "what time is
# it" is the clock and "how much is it" is a price, and the chat's own line is not the answer.
A_RECALL_SAID = re.compile(
    r"\b(?:again|before|earlier|was\s+(?:it|that)|did\s+(?:i|we|you)|have\s+i|you\s+know|tell\s+me|"
    r"remind(?:ed)?\s+me|the\s+(?:time|hour|day|date|make|model|brand|price|cost|size|name|"
    r"place|colour|color|number))\b", re.I)


# A question is what they asked, never a line that gives a detail.
A_QUESTION = re.compile(
    r"\?\s*$|^\W*(?:what|which|who|whom|whose|when|where|why|how|is|are|was|were|do|does|did|"
    r"can|could|should|would|will|shall|have|has|am|any|remind|tell\s+me)(?:'?s)?\b", re.I)


# Kinds a line may ask for without naming anything, because the ask is the whole ask: "how much
# was it", "how old is it", "what make is it". "what time is it" and "what day is it" are the clock
# and the calendar, not a detail of theirs, and a place or a name asked with nothing named is about
# the world ("where is that", "what is it called") with shapes loose enough to find a line that is
# no place at all, so all five want the line to name a thing or to say it is asking again.
UNNAMED_KINDS = frozenset("price colour size age make".split())


# A line that asks what to do ("where should we stay", "where do i grow them", "how much can i
# save") is asking for advice, not for a detail they gave, even when it names the thing the chat is
# about. The store's own readers answer those with the card that fits.
# The other end of a plan: "when does my job finish" against "i start my new job on monday" asks
# for the date the thing ends and is handed the date it begins. One line answers for one end.
AN_END = re.compile(r"\b(?:end|ends|ending|finish|finishes|finishing|last|lasts|leaves|leaving|"
                    r"close|closes|closing)\b", re.I)
A_START = re.compile(r"\b(?:start|starts|starting|started|begin|begins|beginning|began|"
                     r"open|opens|opening)\b", re.I)


def _the_other_end(ask, line):
    """Whether the ask and the line are about different ends of the same plan."""
    asking_end = bool(AN_END.search(ask))
    asking_start = bool(A_START.search(ask))
    if asking_end == asking_start:
        return False
    return bool(A_START.search(line)) if asking_end else bool(AN_END.search(line))


ASKS_WHAT_TO_DO = re.compile(
    r"\b(?:do|does|should|can|could|would|shall|will|might)\s+(?:i|we|you)\b", re.I)


def _flat(text):
    return " ".join(str(text or "").lower().split())


def _words(line, length=2):
    """The words of a line worth matching on, stemmed the way people vary them."""
    out = set()
    for word in re.findall(r"[a-z][a-z'\-]*", _flat(line)):
        word = word.strip("'-")
        if len(word) < 3 or word in FRAME:
            continue
        out.add(word)
        if len(word) > 4 and word.endswith("s"):
            out.add(word[:-1])
    return out


def _mentions(line, wanted):
    """Whether the line names one of the words, in the shape a line would hold it."""
    have = _words(line)
    flat = _flat(line)
    for word in wanted:
        if word in have or word in flat:
            return True
        if len(word) > 4 and word[:-1] in have:
            return True
    return False


def _their_lines(memory):
    """Every line of theirs in the chat, oldest first, without their own questions.

    Their question is what they asked, not something they told: quoting it back answers a question
    with the same question ("what size chicken now" came back as You said: "what size chicken do i
    need"). A count asked for is left out of the table for the same reason: how many of something
    is worked out from the facts on file, and the line that carries one of the figures is not the
    count that was asked for.
    """
    turns = memory.get("turns")
    if not isinstance(turns, list):
        return []
    out = []
    for turn in turns:
        if isinstance(turn, str):
            continue
        if not isinstance(turn, dict):
            continue
        line = " ".join(str(turn.get("user") or "").split())
        if not line or A_QUESTION.match(line):
            continue
        out.append(line)
    return out


def the_kind_asked(text):
    """The kinds of detail the line asks for, in the order the table reads them."""
    low = _flat(text)
    return [kind for kind, pattern in ASKS if pattern.search(low)]


def the_line_that_gives(text, lines):
    """The earlier line of theirs that holds the kind of detail the line asks for, or None.

    Returned as a small reading - `{"line": ..., "kind": ...}` - so the caller phrases it. Nothing
    comes back when no earlier line of theirs gives that kind, which is what keeps a question about
    the world ("how much does a new boiler cost", in a chat that never gave a price) out of it.
    """
    kinds = the_kind_asked(text)
    if not kinds:
        return None
    lines = [line for line in (lines or []) if line and not A_QUESTION.match(line)]
    if not lines:
        return None
    low = LEAD.sub("", _flat(text))
    # A statement is not an ask: "sorry saturday i got the day wrong" is them putting a day right,
    # and read as an ask it found the day they had just changed.
    if not A_QUESTION.match(low):
        return None
    # A line that asks what to do ("where should we stay", "how much can i save") wants advice,
    # not a detail they gave, even when it names the thing the chat is about.
    if ASKS_WHAT_TO_DO.search(low):
        return None
    # What the line names, besides its own frame: "what make is the boiler" names the boiler.
    named = {word for word in re.findall(r"[a-z][a-z'\-]*", low)
             if word not in FRAME and len(word) > 2}
    # An ask that names nothing is answered when it says it is asking again ("what time again",
    # "the make"), or for a kind the ask itself carries ("how much was it", "how old is it"). A
    # place or a name asked with nothing named is about the world, and those shapes are loose.
    asking_again = bool(A_RECALL_SAID.search(low))
    if not named and not asking_again and not any(kind in UNNAMED_KINDS for kind in kinds):
        return None
    for kind in kinds:
        gives = GIVES.get(kind)
        if gives is None or (not named and not asking_again
                             and kind not in UNNAMED_KINDS):
            continue
        for index in range(len(lines) - 1, -1, -1):
            line = lines[index]
            if not gives.search(line):
                continue
            if _the_other_end(low, line):
                continue
            # The line names nothing of its own: any earlier line that gives the kind is the one,
            # because the chat has no other place the detail could have come from.
            if not named or _mentions(line, named):
                return {"line": line, "kind": kind}
            # A detail line is about the thing the line before it named: "its a worcester bosch"
            # says nothing about a boiler until you read the line above it.
            if index and BACK_REF.match(line) and _mentions(lines[index - 1], named):
                return {"line": line, "kind": kind}
    return None
