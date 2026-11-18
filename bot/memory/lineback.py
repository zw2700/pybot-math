"""A detail the person gave earlier, found again from the words of the ask that wants it back.

Late in a chat people ask for a thing they said themselves:

    its on the outside of the knee, just under the bone      (turn 2)
    ...
    and which knee was it                                   -> "You said: it's on the outside
                                                               of the knee, just under the bone"

`bot/memory/recall.py` reads the asks whose subject is a fact the store keeps (a name, a job, a
budget), and the store says that fact back. Every other detail - which side a knee is on, what
subject they are revising, the shift pattern they work - is in no fact key, so those asks were
left to the entries and answered with a card about something else or with a search hedge.

This reads them instead, without filing anything: the person's own lines are in
`memory["turns"]`, so the ask's content words are matched against what they typed, and the line
that carries them is said back. It is deliberately narrow:

* the line has to be a recall ask as people phrase it ("what subject did i say i was revising",
  "which knee was it", "what was my deposit target again", "remind me what i was going to ask
  for"), so a knowledge question ("which knee supports the body") is never this module's;
* a line that is itself a recall ask is never the answer - "what did i say about the days we
  have" is answered from the days, not from an earlier "remind me how many days we have";
* one content word of three letters or more has to be shared, and the words the ask is made of
  ("what", "did", "say", "again") are not content, so "what did i say" on its own finds nothing
  and the line goes to whoever answered it before.
"""
import re

from . import kinds

_KIND_WORDS = ("size", "time", "date", "day", "price", "cost", "number",
                "weight", "height", "dose")
_A_KIND = {
    # "in a medium", "size large" - and the value said on its own when the kind is already known:
    # "actually it was a large" is a size said after the first one.
    "size": re.compile(r"\b(?:in\s+(?:a|an)|size)\s+"
                       r"(xs|s|m|l|xl|xxl|small|medium|large|extra large)\b"
                       r"|\b(?:was|is|its|it's|make\s+it|actually|instead)\s+(?:a\s+)?"
                       r"(xs|xl|xxl|small|medium|large|extra\s+large)\b", re.I),
    # "at 11", "from 6" - and the values that are a time without a preposition in front of them,
    # because nobody says "we said at half two": an am or pm on the figure, a half past, midday.
    "time": re.compile(r"\b(?:at|from)\s+(\d{1,2}(?:[:.]\d{2})?\s?(?:am|pm)?|half\s+\w+"
                       r"|midday|noon|midnight)\b"
                       r"|\b(\d{1,2}(?:[:.]\d{2})?\s?(?:am|pm))\b"
                       r"|\b(half\s+(?:past\s+)?(?:one|two|three|four|five|six|seven|eight"
                       r"|nine|ten|eleven|twelve))\b"
                       r"|\b(midday|noon|midnight)\b", re.I),
    "day": re.compile(r"\b(?:%s)\b" % "|".join(
        ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
         "tomorrow", "tonight")), re.I),
    # A day of the month is one of thirty-one, so an ordinal past the thirty-first is not a
    # date: "its for my dads 70th" is his birthday, and "what date was it again" after "the
    # party is on the 14th" / "actually the 21st" was answered "You said 70th." - the newest
    # ordinal in the chat, read as a day. The range is the whole of the rule: any number from
    # one to thirty-one with an ending on it is a day, and nothing past it is.
    "date": re.compile(r"\b(?:the\s+)?((?:0?[1-9]|[12][0-9]|3[01])(?:st|nd|rd|th))\b"
                       r"|\b(?:in|on)\s+(january|february|march|april|may|june|july|august"
                       r"|september|october|november|december)\b", re.I),
    "price": re.compile(r"(?:£|\$|€)\s?\d[\d,]*(?:\.\d+)?"
                        r"|\b\d[\d,]*(?:\.\d+)?\s?(?:quid|pounds|euros|dollars|grand)\b"
                        r"|\b(?:quoted|paid|charged|cost)\s+(?:me\s+)?(?:£|\$|€)?\s?\d[\d,]*", re.I),
    "weight": re.compile(r"\b\d+(?:\.\d+)?\s?(?:kg|kilos?|stone|st|lbs?|pounds?)\b", re.I),
    "height": re.compile(r"\b\d+(?:\.\d+)?\s?(?:cm|ft|feet|foot|inches|in)\b", re.I),
    "dose": re.compile(r"\b\d+(?:\.\d+)?\s?(?:mg|ml|mcg|micrograms?|g)\b", re.I),
}
# The kinds that answer one of the attribute words in _AN_ATTRIBUTE, so an ask built only from
# those words can be read as a question about that kind.
_A_KIND_FOR_WORD = {
    "size": "size", "time": "time", "date": "date", "day": "day", "birthday": "date",
    "price": "price", "cost": "price", "number": "price", "weight": "weight",
    # "remind me what i paid" names the act, not the word price
    "paid": "price", "pay": "price", "spend": "price", "spent": "price",
    "height": "height", "dose": "dose",
}

# The shapes people use to ask for something said earlier. Each one names the thing it wants
# after it, which is the part the words below are taken from.
ASKS_BACK = re.compile(
    # "what subject did i say i was revising", "what did i tell you the apr was"
    # Only the past tense: "what do i say to them" is asking for advice about a letter, not for
    # something they said, and the deck has 36 of those.
    r"\b(?:what|which|who|when|where|how\s+\w+)\b[^?!]{0,40}?"
    r"\bdid\s+i\s+(?:say|said|tell\s+you|told\s+you|mention|mentioned)\b"
    # "which knee was it", "what was it i said they reckon i owe"
    r"|\b(?:what|which)\s+(?:[a-z']+\s+){1,3}?(?:was|is|were)\s+it\b"
    # "what was my deposit target again", "what's my budget again"
    r"|\bwhat(?:'s|\s+is|\s+was)\s+my\s+(?:[a-z']+\s+){1,3}?again\b"
    # "remind me what i was going to ask for"
    r"|\bremind\s+me\s+(?:what|which|when|where|who|how\s+many|how\s+much)\b"
    # "what did i say about the boiler"
    r"|\bwhat\s+did\s+i\s+say\b"
    # "what was i going to ask for", "what were we going to do"
    r"|\bwhat\s+(?:was|were|am|is)\s+(?:i|we)\s+going\s+to\s+\w+"
    # "what was it he was nervous about" - the thing they said, with the person who said it
    r"|\bwhat\s+(?:was|is)\s+it\s+(?:he|she|they|we|i|you)\b"
    # "how much burger meat did i say i needed" - a quantity, whatever it is made of
    r"|\bhow\s+(?:much|many)\b[^?!]{0,25}?\bdid\s+i\s+(?:say|said|need|want|ask)\b", re.I)

# An ask can name the attribute it wants back rather than the thing: "what did i tell you his
# age was" wants his age, and the line the words happened to match was "hes been limping on his
# back leg". When the ask names an attribute and the chosen line does not carry it, the answer
# is another reader's or nobody's, and a search hedge is better than the wrong line.
_AN_ATTRIBUTE = re.compile(
    r"\b(?:age|ages|old|size|name|price|cost|weight|height|colour|color|birthday|date|time|"
    r"number|address|surname|title)\b", re.I)

# The words a recall ask is built from, which say nothing about the thing wanted: "what subject
# did i say i was revising" wants the subject, and "which knee was it" wants the knee.
_THE_ASK = frozenset("""
what which who whom whose when where why how remind me again say said saying says tell told
telling mention mentioned i you my our we us it its that this these those was were is are be
been being did do does done about of to the a an and or for with in on at by as if so but not
any some please just really thing things one ones kind sort name called exact exactly already
""".split())

# Words that carry no detail on their own, so a shared one of these is not the match: "what was
# i going to ask for" shares "going" and "ask" with half of a chat, and "which city did i say
# first" shared "first" with "its our first trip without the kids".
_VAGUE = frozenset("""
go going went get got getting do doing done make making take taking put thing things way bit
lot time now then well good bad sure really quite maybe first last next other another same
back again more most much many little big small old new long short like want wanted need
""".split())

# A detail said back is a thing, not a figure or a date: "how old did i say she was" and "what
# did i say the race was" want a number or a name out of the line, and the readers for counts,
# ages and dates say those back. Matching one of them by a shared word quotes the wrong line
# ("and how old did i say she was" was answered with "is she old enough to understand a chart").
_NOT_A_DETAIL = re.compile(
    r"\bhow\s+(?:old|many|much|long|often|far|heavy|tall)\b"
    r"|\bwhat\s+time\b|\bwhat\s+(?:day|date)\b|\bwhen\b", re.I)

_SHORT_WORD = 3

# A line of the person's that is itself a question is not a detail they gave, so it is not what a
# recall ask is answered with: "remind me what salary i told you" was answered with "what should i
# say if they ask what salary i want", the question they had asked, instead of the figure they
# then gave. The one ask that wants a question back is the intention, because how a person says
# what they meant to ask is by asking it.
_QUESTION = re.compile(r"^\s*(?:what|which|who|when|where|why|how|should|shall|can|could|would"
                       r"|will|do|does|did|is|are|am|have|has|if|any)\b|\?\s*$", re.I)
_INTENTION = re.compile(r"\b(?:was|were|am|is|going)\s+(?:i\s+)?(?:going\s+)?to\s+"
                        r"(?:ask|say|do|tell|mention)\b|\bwhat\s+(?:i\s+)?was\s+going\s+to\b",
                        re.I)


def flat(text):
    """The line as typed, with the spacing evened out."""
    return " ".join(str(text or "").split())


def _words(text):
    return [word.strip("'") for word in re.findall(r"[a-z']+", flat(text).lower())]


def _stem(word):
    """A crude shared stem, so "revising" answers "revise" and "shifts" answers "shift"."""
    for suffix in ("ing", "ies", "es", "ed", "s"):
        if len(word) > len(suffix) + _SHORT_WORD and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def about(text):
    """The content words of a recall ask, as stems: what the line wants said back."""
    return {_stem(word) for word in _words(text)
            if word not in _THE_ASK and word not in _VAGUE}


# An ask that names the attribute and nothing else is a recall ask in other words: "what size
# again", "the size i said", "what day was it again". The attribute words come from the kind table
# below, so a kind added there is asked about in all these ways without a new rule.
ASKS_BACK_A_KIND = re.compile(
    r"\b(?:what|which)\s+(?:%(kind)s)\b[^?!]{0,22}?\bagain\b"
    r"|\bthe\s+(?:%(kind)s)\s+(?:(?:that\s+)?(?:i|we)\s+(?:said|gave|told\s+you|mentioned)"
    r"|again)\b"
    # the attribute named with the person's own past act: "how much did i pay", "what did i pay".
    r"|\b(?:did|have)\s+(?:i|we)\b[^?!]{0,30}?\b(?:%(kind)s)\b"
    # "how much was it again" is the same ask with the thing left out
    r"|\bhow\s+(?:much|many)\b[^?!]{0,25}?\bagain\b" % {"kind": "|".join(sorted(_A_KIND_FOR_WORD))},
    re.I)


# The attribute named with "i said" is an ask only if the person is not telling the value: "the
# size i said was big" names the size and then says it, so it is a statement and the readers must
# leave it alone. The same words as a question - "the size i said, what was it" - still ask.
_A_TELLING = re.compile(r"^\s*(?:was|is|were|are|should\s+be|came\s+in|goes|needs|will\s+be)\b",
                        re.I)

# An ask about the person's own past act, with the attribute named anywhere in it: "what size did
# i get" says the attribute before the verb, "how much did i pay" says how much instead.
_A_PAST_ACT = re.compile(r"\b(?:did|have)\s+(?:i|we)\b", re.I)


def _a_kind_named(text):
    """The first attribute word the line names, or None."""
    for word in _words(text):
        if word in _A_KIND_FOR_WORD:
            return word
    return None


def is_a_recall_ask(text):
    """Whether the line asks for something said earlier in this chat.

    One check for every memory-based reply. The shapes that name what they want said back
    (`what did i say about the boiler`), the shapes that name the attribute and say `again`
    (`what size again`, `the size i said`), and the attribute named with the person's own past act
    (`what size did i get`, `how much did i pay`) are all this one question.
    """
    flat_text = flat(text)
    if ASKS_BACK.search(flat_text):
        return True
    named = ASKS_BACK_A_KIND.search(flat_text)
    if named and not _A_TELLING.match(flat_text[named.end():]):
        return True
    if not _A_PAST_ACT.search(flat_text):
        return False
    return bool(_a_kind_named(flat_text) or re.search(r"\bhow\s+much\b", flat_text))


def _the_last_reply(memory):
    """The bot's own last line, in the same shape as the person's lines."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for turn in reversed(turns if isinstance(turns, list) else ()):
        if isinstance(turn, dict) and flat(turn.get("bot")):
            return flat(turn.get("bot"))
    return ""


def the_lines(memory):
    """The person's own lines this chat, oldest first, without the line being answered."""
    said = []
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for turn in turns if isinstance(turns, list) else ():
        if not isinstance(turn, dict):
            continue
        line = flat(turn.get("user"))
        if line:
            said.append(line)
    return said


def _the_best_line(wanted, lines, questions=False):
    """The earlier line that carries most of what the ask is about, or None."""
    best = None
    for place, line in enumerate(lines):
        if is_a_recall_ask(line):
            continue  # an ask for the thing is not the thing: it was never the answer
        if _QUESTION.search(line) and not questions:
            continue  # a question they asked is not a detail they gave
        shared = wanted & about_any(line)
        if not shared:
            continue
        longest = max(len(word) for word in shared)
        if longest < _SHORT_WORD:
            continue
        score = (len(shared), longest, place)
        if best is None or score > best[0]:
            best = (score, line)
    return best[1] if best else None


def about_any(text):
    """Every stem the line carries, content word or not: what it can be found by."""
    return {_stem(word) for word in _words(text)
            if word not in _THE_ASK and len(word) >= _SHORT_WORD}


# "my deposit target is 800" carries one value, and quoting the whole line back to say it reads
# like a form being read out. When the line is a possessive statement with a value after it, the
# value is the answer: "You said 800." The store keeps most of these itself and says the figure
# in its own short words; this is for the ones it drops ("deposit target" is no fact key).
_A_MY_VALUE = re.compile(r"\bmy\s+(?:[a-z']+\s+){0,3}?(?:is|was)\s+(?P<value>[^.;,?]+?)\s*$",
                         re.I)
# What a value looks like at its start: a figure, or a phrase that names the thing ("a samsung",
# "on the 14th", "the blue one"). "the house is really damp in the back bedroom" is a sentence
# about a house, not a value, and said back as its tail it read "You said really damp in the back
# bedroom" - so a line like that is quoted whole instead.
_A_VALUE_START = re.compile(r"^(?:[0-9]|a\b|an\b|the\b|on\b|in\b|at\b|for\b|about\b)", re.I)

# An attribute names the kind of answer, not the words of the line: "my coat came in a medium"
# has no "size" in it, so "what size did i say" found no line about a size and answered as if
# nothing had been said. Each kind has the shape its value takes, read from the line, and the
# value is said back in the store's own voice ("You said medium.").
# A value is the value, not the verb that introduced it: "quoted 300" is said back as "300".
_A_VALUE_VERB = re.compile(r"^(?:quoted|paid|charged|cost|costs|size|in\s+(?:a|an)|at|from)\s+",
                           re.I)


# "what day is it", "what time is it": the calendar and the clock. The words are the shape of an ask
# for something said earlier ("what day is it again"), so one without "again", "before" or a thing
# named is read as the ask about today, and the reader for a kind leaves it alone.
# Only the present tense: "which day was it" is the day they gave, said back.
_A_THE_CALENDAR = re.compile(r"^\W*(?:what|which)\s+(?:day|date|time)\s+is\s+it\s*\??$", re.I)
_A_SAID_AGAIN = re.compile(r"\b(?:again|before|earlier|did\s+(?:i|we)|have\s+i|you\s+know|"
                           r"tell\s+me|remind)", re.I)


def _the_kind_asked(said):
    """The kind of value the ask is about, when the ask is about the attribute and nothing else."""
    if _A_THE_CALENDAR.search(said) and not _A_SAID_AGAIN.search(said):
        return None
    words = {word for word in _words(said) if word in _A_KIND_FOR_WORD}
    if not words:
        # "how much was it again" names no attribute: a quantity asked that way is a price.
        if not re.search(r"\bhow\s+much\b", said) or about(said):
            return None
        return "price"
    # "what size did i say" is about the size itself; "what size was the coat" has a subject of
    # its own, and the coat's size belongs to whoever answers about coats.
    if about(said) - {_stem(word) for word in words}:
        return None
    return _A_KIND_FOR_WORD[sorted(words)[0]]


def _a_value_of_the_kind(kind, lines):
    """The last value of that kind the person gave, said back, or None when they gave none."""
    pattern = _A_KIND.get(kind)
    if not pattern:
        return None
    for line in reversed(lines):
        match = pattern.search(flat(line))
        if not match:
            continue
        groups = [group for group in match.groups() if group]
        value = (groups[0] if groups else match.group(0)).strip(" .,;")
        value = _A_VALUE_VERB.sub("", value).strip(" .,;")
        if re.search(r"[a-z0-9]", value) and len(value.split()) <= 4:
            return value
    return None


def _the_value(line):
    """The value of a "my <thing> is <value>" line, or None when the line is not that shape."""
    match = _A_MY_VALUE.search(flat(line))
    if not match:
        return None
    value = match.group("value").strip()
    if not re.search(r"[a-z0-9]", value) or len(value.split()) > 6:
        return None
    return value if _A_VALUE_START.match(value) else None


def _carried(line, wanted):
    """The sentence of the line that carries what the ask is about, for a long line."""
    if len(line) <= 120:
        return line
    parts = re.split(r"(?<=[.!?;])\s+|,\s+(?=and\b|but\b)", line)
    holding = [part for part in parts if wanted & about_any(part)]
    return holding[0].strip(" ,.;") if holding else line


def _the_value_of_the_kind(said, lines, memory):
    """The value of the attribute the ask names, when the ask names the attribute and nothing else.

    This is the reader that needs no word in common with the line: "what size did i say" and the
    earlier "my coat came in a medium" share nothing, and the answer is still medium.
    """
    kind = _the_kind_asked(said)
    if not kind:
        return None
    value = _a_value_of_the_kind(kind, lines)
    return "You said " + value + "." if value else None


# A figure is the answer to "how much <thing> did i say" rather than the line that holds it: a
# cooking line is four sentences long and the person wants "1.5 kg", not the whole of it. A unit is
# what makes a number a figure they gave for a thing, so "about twelve" for a barbecue still gets no
# answer from here - naming a count of people as the meat would be a wrong answer.
_A_FIGURE = re.compile(
    r"[\u00a3$\u20ac]\s?\d[\d.,]*"
    r"|\b\d[\d.,]*\s?(?:%|g|kg|grams?|kilos?|ml|cl|litres?|liters?|pints?|oz|lbs?|tbsp|tsp"
    r"|cups?|mugs?|slices?|sheets?|hours?|hrs?|minutes?|mins?|days?|weeks?|months?|years?"
    r"|miles?|km|metres?|meters?|pounds?|quid|dollars?|euros?|degrees?)\b", re.I)
_AN_AMOUNT_ASKED = re.compile(r"\bhow\s+(?:much|many)\b", re.I)


def _the_figure_for_a_thing(said, lines, memory):
    """The figure they gave for the thing the ask names, when the ask is "how much <thing>".

    "how much mince did i say i needed" has no kind of its own - mince is not a size or a time -
    so the kind table cannot answer it, and the line itself is the wrong answer because the figure
    is buried in it. The last line that carries the thing and a figure is the one they mean.
    """
    if not _AN_AMOUNT_ASKED.search(said):
        return None
    wanted = about(said) - _VAGUE
    if not wanted:
        return None
    for line in reversed(lines):
        if not wanted & about_any(line):
            continue
        found = _A_FIGURE.search(line)
        if found:
            return "You said " + found.group(0).strip().rstrip(" .,") + "."
    return None


def _the_line_itself(said, lines, memory):
    """The earlier line that carries what the ask is about, quoted back or said as its value.

    A figure or a date is not a detail said back by quoting a line: "how old did i say she was"
    would quote whichever line shared a word with it, so a kind of value with no reader of its own
    is left to whoever answers for it.
    """
    figure = bool(_NOT_A_DETAIL.search(said))
    if figure and not _the_kind_asked(said):
        return None
    wanted = about(said)
    if not wanted:
        return None
    line = None if figure else _the_best_line(wanted, lines,
                                             questions=bool(_INTENTION.search(said)))
    if figure or not line:
        return None
    # The bot's own last answer already names what the ask is about, so it has said it: the store
    # repeats a short fact on purpose ("my sister is vegan" / "what did i say my sister eats"), and
    # a quote of some other line about the sister is wrong where the short repeat was right.
    named = {_stem(word) for word in _words(said) if _AN_ATTRIBUTE.fullmatch(word)}
    if named and not (named & about_any(line)):
        return None
    answered = about_any(_the_last_reply(memory))
    if wanted & about_any(line) & answered:
        return None
    value = _the_value(line)
    if value:
        return "You said " + value.rstrip(" .") + "."
    return 'You said: "' + _carried(line, wanted) + '"'


# The one check every memory-based reply goes through. Each reader takes the same three things and
# answers or returns None, and a new shape of ask is a new reader in this table rather than another
# branch in the middle of a module. Order matters: the reader that needs no word in common with the
# line goes first, because a word match on the same ask can find a line about the attribute instead
# of its value.
_MEMORY_READERS = (_the_value_of_the_kind, _the_figure_for_a_thing, _the_line_itself)


def _the_kind_they_gave(said, lines, memory):
    """The earlier line that holds the kind of detail this line asks for, said back.

    The readers above are matched on the words an ask shares with their lines, and a whole family
    of asks shares none: "and what make is the boiler" against "its a worcester bosch", "what
    colour was it" against "its a dulux one, the blue tin". The ask names the kind of detail it
    wants and the line gives it without the word. The table for that is `bot/memory/kinds.py`; the
    line it finds is quoted in the voice the other readers use.
    """
    found = kinds.the_line_that_gives(said, lines)
    if not found:
        return None
    return 'You said: "' + found["line"] + '"'



def the_kind_they_gave(text, memory):
    """The earlier line of theirs that gives the kind of detail this line asks for, or None.

    The reading behind `said_back`'s reply, for a caller that has to know whether the chat answers
    the line before it lets something else answer it.
    """
    said = flat(text)
    if not said:
        return None
    if _A_THE_CALENDAR.search(said) and not _A_SAID_AGAIN.search(said):
        return None  # "what day is it" is the calendar, as the readers above have it
    return kinds.the_line_that_gives(said, the_lines(memory))


def an_earlier_turn(text, memory):
    """Is this line asking for something said earlier, and what was said?

    Returns the reply that says it back, or None when the line is not asking that. Every
    memory-based reply in the bot is meant to come through here, so "is there an earlier turn?"
    is one check with one answer rather than a rule in each module.
    """
    said = flat(text)
    lines = the_lines(memory)
    if len(lines) > 1 and lines[-1] == said:
        lines = lines[:-1]  # the line being answered is the last of them
    if not is_a_recall_ask(said):
        # Not every ask for something said earlier names a past act: "and what make is the boiler"
        # is a question about the world in its words and about their own line in what it asks for.
        # That reader runs on its own, so a recall ask never loses the turn to it.
        return _the_kind_they_gave(said, lines, memory)
    for reader in _MEMORY_READERS:
        answer = reader(said, lines, memory)
        if answer:
            return answer
    return _the_kind_they_gave(said, lines, memory)


def reply_for(text, memory):
    """What to say when the line asks again for something the person gave earlier, or None."""
    return an_earlier_turn(text, memory)
