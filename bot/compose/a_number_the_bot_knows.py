"""A person asking for a phone number gets the number the bot already knows.

"whats the number for the samaritans", "whats the number for 111", "childline number",
"how do i ring acas" - on main every one of those is answered by the same sentence:

    "No directory here, sorry. A map app search for the name shows the address and the
     number, and the place's own page has the hours."

That is the right route for a shop or a surgery, whose number only a directory has. It is the
wrong route for a national line, because the bot already states those numbers in its own cards:

    116 123        Samaritans, free, any hour   (bot/modules/safety_cards.py, science.py, ...)
    0808 2000 247  the domestic abuse helpline  (bot/modules/carers_turn.py)
    0300 123 1100  ACAS                         (bot/knowledge/work.py)
    111            NHS, free, any hour          (bot/modules/... many)
    988            the US crisis line          (bot/knowledge/crisis_replies.py)
    999 / 112       the emergency number        (bot/compose/verdict.py)

So this adds no fact. It reads the asking, finds which of the lines the person named, and says
that number with the one thing that makes it usable (whether it is free, and whether it is open
any hour). A person in trouble should not be sent to a map app for the Samaritans, and this is
the turn they are most likely to type.

Nothing here guesses a number, and a line that names a shop, a surgery or a person - whose
number nobody in the tree knows - gets None, so the directory route keeps it.
"""

import re

# The number, then what makes it usable. Every number below is stated elsewhere in the tree, and
# the words after it are the ones the tree uses for it: nothing is filled in here.
LINES = (
    (("samaritans", "samaritan"),
     "Samaritans is 116 123 - free, any hour."),
    (("domestic abuse helpline", "domestic violence helpline", "national domestic abuse helpline",
      "refuge", "womens aid", "women's aid"),
     "The domestic abuse helpline is 0808 2000 247 - free, any hour, and they will plan the next "
     "step with you."),
    (("acas",),
     # 0300 is a national-rate number, not a free one: the card that says "free" is wrong, and a
     # promise about money before someone rings is the one thing not to repeat from it.
     "ACAS is 0300 123 1100, charged at your usual rate, and they will tell you where you stand "
     "on a work problem."),
    (("nhs 111", "111", "nhs direct"),
     "NHS 111 is on 111 - free, any hour, and they will say what to do about a symptom and where "
     "to go."),
    (("988",),
     "988 is the crisis line in the US - free, any hour, and you can call or text it."),
    # A map-app line is the worst thing to hand somebody who asked for the emergency number, and
    # the tree already says what the number is for ("999 or 911, say where you are and what has
    # happened").
    (("999", "911", "112", "emergency services"),
     "Ring 999 - or 911, or 112 - and say where you are and what has happened."),
)

# The asking. A number is wanted, and the line says so: "whats the number for X", "X number",
# "how do i ring X", "do you have a number for X". The captured part is the thing whose number is
# wanted, and it has to be one of the lines above.
ASKS = (
    re.compile(r"(?<![a-z])(?:what(?:'s|s| is)?\s+the\s+|what\s+is\s+the\s+|the\s+|whats\s+|what\s+)?"
               r"(?:phone\s+|telephone\s+)?number\s+(?:for|of|to)\s+(.{2,60})$"),
    re.compile(r"(?<![a-z])(?:do you have|have you got|any idea of)\s+(?:a\s+|the\s+)?"
               r"(?:phone\s+)?number\s+(?:for|of|to)\s+(.{2,60})$"),
    re.compile(r"(?<![a-z])(?:how do i|how can i|how to|where do i|can i|do i)\s+"
               r"(?:ring|call|phone|dial|contact|reach)\s+(.{2,60})$"),
    re.compile(r"(?<![a-z])(?:what(?:'s|s| is)?\s+the\s+)?(?:phone\s+)?number\s+(?:for\s+)?"
               r"(.{2,40}?)\s+again$"),
    re.compile(r"^(.{2,40}?)(?:'s|s)?\s+(?:phone\s+)?number$"),
    re.compile(r"^(.{2,40}?)\s+(?:phone\s+)?number\s*\?*$"),
    # The same ask after something else has been said first: "i need to talk to someone, whats the
    # samaritans number", "we've had a letter, whats the number for acas". The words before the
    # comma are not the thing whose number is wanted, so the last few words before "number" are
    # what gets read.
    re.compile(r"(?<![a-z])([a-z][a-z' ]{1,40}?)\s+(?:phone\s+)?number\s*[?!.]*$"),
)

# The national lines whose number the tree does not state. They are still not a place to look up:
# a helpline is answered on its own page, and a map app would give the branch that answered the
# phone once. So the route names the page to take, and says it has no number itself, which is the
# true part.
NO_NUMBER_HERE = (
    (("childline",), "I don't have Childline's number here. A search for 'childline' brings up "
                     "their own page, and the free number is on it."),
    (("alcoholics anonymous", "al anon", "alanon"),
     "I don't have Alcoholics Anonymous's number here. A search for 'alcoholics anonymous' "
     "brings up their own page, and a local meeting line is on it."),
    (("mind", "shelter", "stepchange", "age uk", "ageuk", "victim support", "cruse",
      "nspcc", "rethink"),
     "I don't hold that number. Their own page is where it lives - a search for the name brings "
     "it up, and a helpline's number is the one on it (a map app would only give you a branch)."),
)

# A number already given in the last few turns is not given again: saying the same sentence twice
# reads worse than the pointer, and the person can see it above.
_REPEAT_TURNS = 3

# A number ask that leans on the one before it: "whats the number for the samaritans" and then
# "and for childline", "what about acas", "childline?". The word "number" is not said again,
# because the person is still in the last question. Nothing is carried unless the bot's own last
# turn was one of the answers above, so "and for childline" after some other subject keeps the
# turn it had.
AND_THE_NEXT = re.compile(
    r"^(?:and|also|what about|how about|whats|what is|what's)\b[\s,]*(?:the\s+|a\s+)?"
    r"(?:number\s+(?:for|of)\s+)?(?:for\s+|of\s+)?(.{2,40})$")
A_BARE_NAME = re.compile(r"^[a-z][a-z' ]{1,30}$")

# "whats the samaritans number again" - a person asking again is not being answered twice, and a
# hedge is the worst reply to give them: the bot said the number three turns ago, so it repeats it.
ASKS_AGAIN = re.compile(r"\b(?:again|what was (?:it|that)|remind me|one more time|i missed (?:it|that))\b")


def _said_before(memory):
    """The line this module gave on the last turn, if that is what the last turn was, else ""."""
    replies = [reply for reply in _replies(memory) if reply]
    if not replies:
        return ""
    last = replies[-1]
    for _names_, said in LINES + NO_NUMBER_HERE:
        if last == " ".join(str(said).split()):
            return said
    return ""


def _carried_thing(text):
    """The thing a line that only points back at the last question is asking about, or ""."""
    line = " ".join(str(text or "").lower().replace("\u2019", "'").split()).strip(" ?!.,")
    found = AND_THE_NEXT.match(line)
    if found:
        return found.group(1).strip(" ?!.,'\"")
    if A_BARE_NAME.match(line):
        return line
    return ""



# "sorry, whats the samaritans number again" is the same ask as "whats the samaritans number":
# the word in front is an apology and the word behind is politeness, and both are stripped before
# the ask is read, because the asks are shaped round the ask itself.
_IN_FRONT = re.compile(r"^(?:sorry|hi|hello|hey|ok|okay|oh|so|and|also|er|um)\s*[,!.]\s*")
_BEHIND = re.compile(r"\s*\b(?:again|please|one more time|now|thanks|thank you)\b\s*[?!.]*$")


def _asked_about(text):
    """The thing whose number is wanted, cleaned of trailing punctuation, or ""."""
    line = " ".join(str(text or "").lower().replace("’", "'").split())
    line = line.strip(" ?!.,")
    line = _IN_FRONT.sub("", _BEHIND.sub("", line)).strip(" ?!.,")
    if not line:
        return ""
    for ask in ASKS:
        found = ask.search(line)
        if found:
            thing = found.group(1).strip(" ?!.,'\"")
            thing = re.sub(r"^(?:the|a|an)\s+", "", thing)
            if thing:
                return thing
    return ""


def _names(thing, names):
    """True when the thing wanted is one of the names, as a whole word or a whole phrase.

    Whole words, because "refuge" is inside "refugees" and "111" inside "1111": the number asked
    about has to be the one named, not a word that holds it.
    """
    for name in names:
        if re.search(r"(?<![a-z0-9])" + re.escape(name) + r"(?![a-z0-9])", thing):
            return True
    return False


def _replies(memory):
    """What the bot said on each turn, whichever shape the store keeps a turn in.

    The store keeps a turn as a dict in some builds and as a (user, bot) pair in others, so reading
    only the dict shape made both the guard below and the "asked again" reader above silently never
    fire - the fault that let "sorry, what was it again" be answered with a hedge.
    """
    out = []
    for turn in (memory or {}).get("turns") or ():
        if isinstance(turn, dict):
            out.append(" ".join(str(turn.get("bot") or turn.get("reply") or "").split()))
        elif isinstance(turn, (list, tuple)) and len(turn) >= 2:
            out.append(" ".join(str(turn[1] or "").split()))
        else:
            out.append("")
    return out


def already_said(number, memory):
    """True when the bot has said this number in the last few turns."""
    said = str(number).replace(" ", "")
    for reply in _replies(memory)[-_REPEAT_TURNS:]:
        if said and said in reply.replace(" ", ""):
            return True
    return False


def not_a_number(reply):
    """True when the reply the bot is about to send holds no number at all.

    "i need to talk to someone, whats the samaritans number" was answered "Worth doing. What would
    you like help with first?" - a question about the person's day when they asked for a crisis
    line. A reply with no digit in it cannot be the answer to a number asked for, so the number the
    bot knows is given instead. It only matters for the lines above, which are few and named.
    """
    return not re.search(r"\d", str(reply or ""))


def answer_for(text, memory=None):
    """The number, when the person asked for one this bot knows. None for everything else."""
    line = " ".join(str(text or "").lower().split())
    again = bool(ASKS_AGAIN.search(line))
    before = _said_before(memory)
    thing = _asked_about(text)
    if not thing and before:
        thing = _carried_thing(text)
    if thing:
        for names, said in LINES:
            if not _names(thing, names):
                continue
            number = re.search(r"\d[\d ]{2,}", said)
            if number and already_said(number.group(0), memory) and not again:
                return None
            return said
        for names, said in NO_NUMBER_HERE:
            if _names(thing, names):
                return said
    if before and again:
        # Nothing is named that this module knows, and the line asks again about the last one:
        # "sorry, what was it again" one line after the number, which is the same question.
        return before
    return None
