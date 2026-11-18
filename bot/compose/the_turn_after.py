"""The turn after an honest limit: the same question about another day, or "can you just check".

The composer has a pool for the things it cannot see - today's opening hours, the prices in the
shops, the weather, the roads - and each line in those pools says what the bot cannot do and where
the answer is. Both readings here are the *next* line of that exchange, and both reach the search
hedge today:

    is the library open today      "I can't check today's opening hours, sorry. The venue's own
                                    page or its map listing shows them, holidays included"
    and tomorrow                   "I'm not sure about that one, sorry - I'd rather not guess.
                                    A quick search online will get you a solid answer"

    whats the weather like today   "I can't check the forecast from here, sorry. A weather app..."
    can you check for me           "That's beyond what I know well, sorry. Searching for it will
                                    turn up better sources than I can offer"

The person has not changed the subject and has not asked anything new. "And tomorrow" is the same
question about another day, and "can you check for me" is the same request put straight back. A
friend says the same thing again - the times are on the venue's page, and tomorrow's are no
exception - and does not send somebody off to search when they were just told where to look.

Three guards keep this from taking a turn that has an answer of its own:

  - the reply just given has to be one of the composer's honest limits - a live pool's line, or one
    of the three plain ones (`CANNOT_ANYTHING`, `CANNOT_SEE_ANYTHING_LINES`, `CANNOT_YOUR_OWN`) -
    so a bare "and tomorrow" after a joke, a card or a piece of advice changes nothing at all;
  - a bare day has to be the hours limit that was just given, nothing else (`BARE_DAY`);
  - a request to check either names nothing at all ("can you just check") or names the thing the
    limit just refused, by the same words the composer's own pool uses for it ("can you check the
    price for me" after the price limit). A line naming anything else has a subject of its own and
    is answered before this reading is asked (`CHECK_REQUEST`, `COVERS`).

Nothing here is a new fact and no pool is new: the reply is one of the composer's own lines,
chosen the way it chooses any other. `bot/modules/greeting.py` asks this only where it would
otherwise have replaced a hedge, so a line with a card of its own never reaches the reading.
"""
import re

from . import fallback, fallback_data

# A bare day, with the words people put in front of it: "and tomorrow", "what about next week",
# "on bank holidays", "christmas day". The part of the day is optional because "christmas day" and
# "and monday morning" are the same ask; the anchor at both ends is what makes it bare.
BARE_DAY = re.compile(
    r"^(?:and|or|also|what\s+about|how\s+about|what\s+if|and\s+what\s+about|so)?\s*"
    r"(?:(?:on|for|at)\s+)?(?:the\s+)?(?:bank\s+holiday\s+)?(?:(?:next|this|that)\s+)?"
    r"(?:monday|tuesdays?|wednesdays?|thursdays?|fridays?|saturdays?|sundays?|"
    r"weekends?|weekly|tomorrow|today|tonight|week|month|"
    r"christmas|boxing\s+day|new\s+year|easter|half\s+term|bank\s+holidays?|holidays?)"
    r"(?:\s+(?:day|morning|afternoon|evening|lunchtime|night))?[\s.?!]*$")

# The bot asked to do the thing it has just said it cannot, wherever the words sit in the line:
# "can you just check", "could you look it up for me", "just google it". What may follow it is
# decided below, by whether the line names the thing the limit just refused.
CHECK_REQUEST = re.compile(
    r"\b(?:can|could|would|will)\s+(?:you|u|ya)\s+(?:just\s+|please\s+|maybe\s+|quickly\s+|"
    r"quick\s+)*(?:check|look\s+(?:it|that|this)?\s*up|look|search|google|find\s+(?:it\s+)?out|"
    r"see)\b"
    r"|\bjust\s+(?:check|look\s+it\s+up|look|google\s+it|google|search)\b"
    r"|\b(?:check|look\s+it\s+up|search|google)\s+(?:it|that|this)?\s*for\s+me\b")

# The same request with nothing else in the line at all: "and", "so", "ok" and a please are not a
# subject, so the line is the request put straight back and the limit is the whole answer.
CHECK_REQUEST_ALONE = re.compile(
    r"^\s*(?:(?:and|so|ok|okay|well|but|then|cool|right|please)\s+)*"
    r"(?:(?:can|could|would|will)\s+(?:you|u|ya)\s+)?"
    r"(?:just\s+|please\s+|maybe\s+|quickly\s+|quick\s+)*"
    r"(?:check|look\s+(?:it|that|this)?\s*up|look|search|google|find\s+(?:it\s+)?out|see)"
    r"(?:\s+(?:it|that|this|for\s+me|then|now|again|please))*[\s.?!]*$")

# A word of four letters or more that a pool uses for its own subject ("opening hours", "price
# of"). The words a line shares with the pool just refused are the test for "the same thing".
SHORT_WORDS = ("open", "shut", "cost", "time", "road", "news", "bus", "car", "hot", "cold",
               "won", "jam", "tube")


def _the_limit_just_given(memory):
    """The lines and phrases of the pool the reply just given came from, or (None, ()).

    Only the pools that say what the bot cannot do: the live ones (times, prices, the roads, the
    weather) and the three plain ones. Read from the composer's own data, so a pool that grows or
    is reworded is followed here without a second list to keep in step.
    """
    try:
        said = str(fallback.last_bot(memory) or "").strip()
    except Exception:  # noqa: BLE001 - memory that cannot be read claims nothing
        return None, ()
    if not said:
        return None, ()
    for kind, phrases, options in fallback_data.LIVE_KINDS:
        for line in options:
            head = str(line)[:40]
            if head and said.startswith(head):
                return options, tuple(str(one) for one in phrases)
    for pool in (fallback.CANNOT_ANYTHING, fallback.CANNOT_SEE_ANYTHING_LINES,
                 fallback.CANNOT_YOUR_OWN):
        for line in pool:
            head = str(line)[:40]
            if head and said.startswith(head):
                return pool, ()
    return None, ()


def _the_hours_pool():
    """The composer's honest lines for a venue's opening hours, or ()."""
    for kind, _phrases, options in fallback_data.LIVE_KINDS:
        if kind == "hours":
            return options
    return ()


def _words_of(phrases):
    """The words a pool names its subject with, four letters or more, and the short ones too."""
    words = set()
    for phrase in phrases:
        for word in re.findall(r"[a-z]+", phrase.lower()):
            if len(word) >= 4 or word in SHORT_WORDS:
                words.add(word)
    return words


def the_day_after(text, memory):
    """"And tomorrow" straight after the honest hours line is the same question, another day."""
    clean = str(text or "").strip().lower()
    if not BARE_DAY.match(clean):
        return None
    hours = _the_hours_pool()
    if not hours:
        return None
    just, _phrases = _the_limit_just_given(memory)
    if not just or just != hours:
        return None
    return fallback._choose(hours, memory, clean)


def asked_to_check(text, memory):
    """"Can you just check" straight after the limit is the same limit, said in other words."""
    clean = str(text or "").strip().lower()
    if not CHECK_REQUEST.search(clean):
        return None
    just, phrases = _the_limit_just_given(memory)
    if not just:
        return None
    if not CHECK_REQUEST_ALONE.match(clean):
        # Something is named: it has to be the thing the limit just refused, in the pool's own
        # words, or the line is an ask with a subject of its own.
        covered = _words_of(phrases)
        if not covered:
            return None
        if not any(word in re.findall(r"[a-z]+", clean) for word in covered):
            return None
    return fallback._choose(just, memory, clean)


def answer_for(text, memory):
    """The turn after an honest limit, or None when this is not that turn."""
    return the_day_after(text, memory) or asked_to_check(text, memory)
