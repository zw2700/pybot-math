"""The place an answer is kept, read from the line above when the follow-up names no kind of its own.

`fallback_data.the_place_the_answer_is_kept` turns a line into the place its answer is kept -
their own account, a shop's stock, an official rule, a timetable, an airline's baggage terms -
from the words on that line. It is read inside the composer only for a line that is about to get
the plain hedge, and it asks the line to name its own kind, because a wrong place is worse than
no place.

A follow-up does not name its kind. "im on benefits" then "can i save anything", "one bag is 23
kilos" then "and the kids, do they get one each", "is a backpack ok as hand luggage" - the noun
is one line up, where the person already said it, and the bot had just answered that line. Those
turns came out as "I'm not sure about that one, sorry - I'd rather not guess. A quick search
online will get you a solid answer": a pointer with nothing in front of it, to a person whose own
words name the place.

So the kind is read from the conversation as well as from the line: a short follow-up that names
no kind of its own takes the kind from the person's own last line, and the reply is that kind's
own line - the limit in a few words, then where the answer lives, then what the bot can do with
it. Only the person's own lines are read for it: the bot's answer to the turn above names half
the kinds in the table on its way past ("a pharmacist will answer that one" is a shop as well as
a medicine), and inheriting a warranty from it put "the maker's page has the cover" in front of
"will it be alright" about a phone dropped in the sink.

This runs at the end of the hedge gate, after every reader that can answer a line of its own, so
a line with an answer of its own - a rule, a timetable, a medicine, a person to ring - never
reaches it. It returns None when the thread names no kind either, and the composer's own hedge
stands.
"""
import re

from .fallback_data import THE_PLACE_ASK, UNKNOWN, the_place_the_answer_is_kept

# The three lines in `fallback_data.UNKNOWN`: the plain pointer, with nothing of its own on it.
# Other pools are hedges too - `a_place_nobody_can_see` opens "No first-hand knowledge of that one
# here, so no verdict from me. What it comes down to is how it works..." - and those already say
# what they know before they point, so replacing one with this file's line made the turn worse.
PLAIN_HEADS = tuple(line[:40] for line in UNKNOWN)

# A line that leans on the turn above rather than naming its own subject: "and the kids, do they
# get one each", "what about the morning of", "do i need to renew it", "can we share the
# allowance". The and/also/so openers are the mark of it; the rest are short asks that open with
# a question word and carry no subject of their own.
LEANING = re.compile(
    r"^(?:(?:and|also|so|but|ok|okay|then|plus)\b"
    r"|\W*(?:what|how|where|when|who|which|is|are|do|does|can|could|should|shall|will|would|"
    r"have|has|did)\b)", re.I)

# And this short, on its own, is not a new subject: it is the same one asked from another side.
# Anything longer carries enough words to name its own kind, or to have moved on.
SHORT = 11

# The words a follow-up asks *with*: the grammar of a question, the pronouns that stand in for the
# thing, the quantifiers, and the light verbs that say what to do with it. A follow-up may take the
# kind one line up only when it is made of these - otherwise it brings a thing of its own and the
# kind above it is coincidence. "is it ok to give water" one line after a benefit line was sent to
# Citizens Advice, and to the airline's baggage rules after a bag line: "water" is the thing asked
# about, and neither place has it. Same for "put this in the oven" and "put seed down".
ASKING = frozenset("""
a an the and or but so then if is are was were be been being am do does did done have has had
i you we they he she it me us them him her my your our their its this that these those there
what which who whom whose where when why how whether
can could would should shall will may might must need needs needed
one ones each both either any some all more most much many few less least other else also too
still just only again ever never not no yes ok okay please thanks
long far often soon old big heavy quick fast early late near
to of in on at for from with about into over under up down out off back by as than
itn t ll re ve don doesnt didnt isnt arent wasnt wont cant couldnt shouldnt wouldnt
get gets got give gives gave put puts take takes keep keeps save saves share shares use uses
buy buys pay pays book books order orders renew renews change changes try tries go goes come
comes help helps tell tells say says ask asks know knows work works start starts stop stops
do make makes fix fixes clean cleans wash washes cut cuts add adds pour pours boil boils
cook cooks freeze freezes store stores wear wears eat eats drink drinks run runs walk walks
wait waits ring rings call calls check checks send sends bring brings
anything something everything nothing anyone someone anyone nobody none somewhere anywhere
elsewhere whichever whatever whenever however lot lots bit bits piece pieces way ways
""".split())

# A method ask - "how do i clean it", "whats the best way to freeze it" - names the kind of answer
# it wants in its first words, and that answer is a method, not the place the last answer's kind
# kept. Its words are the asking words, so without this it took the place above: "my order hasnt
# come" then "how do i clean it" inherited the account (white-peach, #12543).
A_METHOD = re.compile(
    r"^\W*(?:how\s+(?:do|can|could|should|would|shall)\s+(?:i|you|we)\b|how\s+to\b"
    r"|(?:what|whats|what'?s)\s+the\s+(?:best|easiest|quickest|right)\s+way\b"
    r"|the\s+(?:best|easiest|quickest|right)\s+way\s+to\b)", re.I)

# A bag on a plane or a train, a seat, an allowance: the airline's own booking terms decide it and
# the fare decides those, so no search settles "can we share the allowance". The table above has
# no entry for it, and the line that asks it usually has the words in it.
BAGGAGE = re.compile(
    r"\b(?:baggage|luggage|hand luggage|cabin bag|carry[- ]on|hold bag|checked bag|holdall"
    r"|suitcase|allowance|weight limit|kilos?|kilograms?|oversize|oversized|extra bag"
    r"|bag drop|legroom)\b", re.I)
BAGGAGE_POOL = (
    "That is your airline's rather than mine, sorry - the allowance is set by the fare, so two "
    "people on the same plane can have different ones. Your booking's own page shows the kilos "
    "you have paid for, and adding a bag before the airport is always the cheaper way. Tell me "
    "what it says and I'll help you pack to it.",
    "The airline sets that and the fare decides it, sorry, so it is your booking that answers it: "
    "open it and look for the baggage line rather than the airline's general page. Bring me the "
    "figure and I'll help you fit everything in.",
    "I can't call that one - it belongs to the ticket rather than to the plane, sorry. Your "
    "booking shows what you have paid for and the desk weighs it to the kilo; tell me the number "
    "and I'll help you sort the rest.",
)


def _turns(memory):
    return [t for t in (memory or {}).get("turns") or [] if isinstance(t, dict)]


def _clean(text):
    return " ".join(str(text or "").lower().split())


def _without_plurals(line):
    """The line with the s taken off every word, so a table written in the singular reads it.

    The table's own words are singular where people are not - `\\bbenefit\\b` is "on benefit" and
    the person says "im on benefits", `\\border\\b` is one order and they say "my orders" - and a
    kind missed by a letter is a hedge for the whole turn. Whole words only, so "orders" becomes
    "order" and "passport" stays "passport".
    """
    words = []
    for word in line.split():
        if len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
            words.append(word[:-1])
        else:
            words.append(word)
    return " ".join(words)


def is_the_plain_hedge(said):
    """True when the reply is the plain pointer and not one of the hedges that already say more."""
    return str(said or "")[:40] in PLAIN_HEADS


def _inheritable(pool):
    """Whether this kind's own line can stand on a kind borrowed from the turn above.

    The officials' pool is written for a council's page ("the council's own page, or the number on
    the letter"), which is the right place only where the person said council: borrowed for a
    passport renewal it sent them to the wrong office. The rest name a place that belongs to the
    kind itself - their own account, the operator's app, a pharmacist, a free advice service - so
    borrowing them is safe.
    """
    return not any("council" in line.lower() for line in pool)


def _the_kind(line, borrowable=False):
    """The kind a line names itself, as the table or this file knows it."""
    for said in (line, _without_plurals(line)):
        pool = the_place_the_answer_is_kept(said)
        if pool:
            if borrowable and not _inheritable(pool):
                continue
            return pool
        if BAGGAGE.search(said):
            return BAGGAGE_POOL
    return None


def answer_for(text, memory=None):
    """The place this follow-up's answer is kept, or None when the thread names no kind."""
    line = _clean(text)
    if not line:
        return None
    if the_place_the_answer_is_kept(line):
        # It names a kind the composer's own reading has already used, so the turn is not here.
        return None
    if BAGGAGE.search(line):
        # A kind the table has no entry for, and one the composer cannot answer: the fare decides
        # the allowance, so the booking is the only place with it.
        return BAGGAGE_POOL
    if not LEANING.search(line):
        return None
    if A_METHOD.search(line):
        # It asks how, which is a kind of answer of its own and not the one above.
        return None
    said = [w for w in re.split(r"[^a-z']+", line) if w]
    if len(said) > SHORT:
        return None
    if any(word not in ASKING for word in said):
        # It brings a thing of its own, so the kind one line up is coincidence.
        return None
    turns = _turns(memory)
    if not turns:
        return None
    near = [turns[-1].get("user")]
    if len(turns) > 1 and LEANING.search(_clean(turns[-1].get("user"))):
        # Two lines back is the same thread only when the line between them was itself a lean on
        # it ("my order hasnt come" / "and how long" / "is that from the shop"), because a leaning
        # line names no subject of its own. A line with a subject in it starts a new subject, so
        # the line before it is not the thing this follow-up is about: "my order hasnt come" /
        # "nice weather today" / "how much is it" borrowed the account (white-peach, #12543).
        near.append(turns[-2].get("user"))
    for said in near:
        said = _clean(said)
        if not said or said == line:
            continue
        pool = _the_kind(said, borrowable=True)
        if pool:
            return pool
    return None
