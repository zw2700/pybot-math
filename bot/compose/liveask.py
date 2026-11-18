"""A decision that turns on live information: the one-tap check, then the weighing.

The composer's live note is the honest answer to "what time does the shop close today" - it says
the bot cannot see live hours and names the page that can - and it is the wrong answer on its own
to "should i go before it shuts". That line asks for a decision, and the decision turns on the one
thing the bot cannot see, so a reply that only says where to look leaves the question on the floor:

    should i take a coat tomorrow
    No live weather here, sorry. A forecast app or site will tell you in one tap, and the averages
    are worth a look for a trip later in the year.

Nothing in that is wrong and nothing in it is an answer. STYLE.md's "Not knowing, honestly" has
the shape that is: say what the bot cannot see, name the one place that knows, and stay with the
person for the rest of it. So the kind's own check is kept, in one step, and the weighing is handed
back in words the person can answer:

    I can't see the weather from here, sorry. A weather app has the next few days in one tap, with
    the feels-like temperature. Nobody can call that but you - say what you'd lose either way and
    I'll lay both out with you.

What is written here is where each kind of live information is found and how a decision is offered;
no fact about the world is added, because the bot was asked precisely the thing it cannot see.

This is a last resort: `bot/modules/greeting.py` asks it after the composer, and it stands down
unless the composer's reply is one of its own live notes (`fallback.LIVE_KINDS`), so a line the
composer answers with anything else - or a line any entry or module answered - never reaches it.
Adding the note rather than replacing it would be the safer-looking change and the worse one: two
tips at the end of one reply ("a forecast app will tell you in one tap" ... "a weather app has the
next few days in one tap") reads as a machine talking to itself.
"""
import re

from . import fallback, pick

# The decision, said as a comparison the person can finish: what is at stake either way. "Then
# it's your call" says plainly that the bot is not going to pretend to decide, which is the honest
# half of an answer to "should i", and the question at the end is the one thing the bot can do
# without knowing the weather.
LIVE_DECIDE = (
    "I can't see the {kind} from here, sorry. {check} Then it's your call, and I can help you "
    "weigh it: what would each way cost you?",
    "I can't see the {kind} from here, sorry. {check} Nobody can call that but you \u2014 say what "
    "you'd lose either way and I'll lay both out with you.",
)
# Where each kind of live information is found in one step, said plainly enough to use, and the
# word for the kind so the decision line can name what the bot cannot see. One row per pool in
# `fallback.LIVE_KINDS`; a kind with no row here keeps the note alone.
LIVE_CHECK = {
    "weather": ("A weather app has the next few days in one tap, with the feels-like temperature.",
                "weather"),
    "hours": ("The venue's own page or its map listing has today's hours, holiday changes and "
              "all.", "opening times"),
    "prices": ("What it costs turns on which one it is, where you buy it and the day, and the "
               "seller's own site has today's figure.", "prices"),
    "news": ("A news site has the latest.", "news"),
    "travel": ("The operator's app or a journey planner has the next one and any disruption.",
               "times or delays"),
}
# What makes the line a decision rather than an ask for the reading: the shapes a person uses to
# put a choice on the table and ask to be helped with it. "whats the weather like tomorrow" and
# "is it open today" are none of these and keep the note alone.
LIVE_DECIDE_ASKS = re.compile(
    r"\b(?:should i|shall i|is it worth|is it better|would it be better|do i need|do you think "
    r"i should|what would you do|not sure|unsure|dont know|do not know|no idea|cant decide|"
    r"torn between|in two minds|whether to|if i can)\b")
# Every note the composer has for a live kind, with the kind each one belongs to. A reply that is
# not one of these is somebody else's answer and is left alone - including a live note for a kind
# this file has no check for.
NOTE_KIND = {line: kind for kind, _phrases, pool in fallback.LIVE_KINDS for line in pool}
# The apostrophes people type and the ones the pools spell: "don't know" and "cant decide" are the
# same ask, so the line is read with the marks taken out.
NO_MARK = re.compile(r"['\u2019`]")


def answer_for(text, memory=None, reply=""):
    """The check and the weighing for a decision about live information, or None.

    `reply` is what the composer has already said. Only one of its live notes is replaced, so the
    file can neither take a turn off a better answer nor answer a line nobody asked a decision
    about.
    """
    kind = NOTE_KIND.get(str(reply or "").strip())
    if not kind:
        return None
    check, word = LIVE_CHECK.get(kind, ("", ""))
    if not check:
        return None
    said = NO_MARK.sub("", str(text or "").lower())
    if not LIVE_DECIDE_ASKS.search(said):
        return None
    options = tuple(line.format(check=check, kind=word) for line in LIVE_DECIDE)
    read = memory.get("understood") if isinstance(memory, dict) else None
    return pick(options, read, said)
