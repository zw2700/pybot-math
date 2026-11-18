"""A recap asked for with the wrapper still on it is still the recap.

Main reads the recap as the whole line: "what were we talking about", "what were we saying",
"where were we". People say it with the reminder wrapper still on, with a word in front, or
with the place instead of the words:

    remind me what we were talking about
    remind me where we got to
    back to my question
    where were we up to
    what were we looking at
    what were we just saying

None of those is the line the store's gate reads, so the store hands the turn on and the
punting modules answer: "That's a job in the world and I can't reach one", "Searching for it
will turn up better sources", "That's beyond what I know well, sorry". The person asked what
the two of you were on and got a shrug from a bot that had just been told.

Nothing new is said here. The gate is wider, so the store's own recap is reached on those
lines and the answer is the store's ("You said you have a washer and a spanner. Want to
carry on?"). It proposes at the recall band because that is what the line is: a question about
the conversation, not about the thing its words name. A line that ends on the ask only - "what
we were talking about was the roof" - is a statement, so every shape here has to end the line.
"""
import re

from . import memory_store

# The store's own answer is the recall answer, so this sits in the same band rather than over
# it: where the store's gate reads the line, this module says nothing (see `respond`).
PRIORITY = 7000

# Every shape ends on the ask: a wrapper in front is still the ask, but a clause that carries on
# after it is a statement about the conversation, and the store answers those as what they are.
WANTED_AGAIN = re.compile(
    r"\bwhat (?:were|are|was) (?:we|i|you) (?:just )?(?:talking|chatting|saying|on) about\b|"
    r"\bwhat (?:were|are|was) (?:we|i|you) (?:just )?saying\b|"
    # The reminder wrapper comes off the line before it reaches us, so this is the bare
    # "what we were talking about" - with nothing after it but the end of the line (or a word
    # that points back, which is still the ask).
    r"\bwhat we were (?:just )?(?:talking|chatting|saying) about"
    r"(?=\s*(?:[?.!,]|$|again\b|earlier\b|before\b|just now\b))|"
    r"\bwhat we were (?:just )?saying(?=\s*(?:[?.!,]|$|again\b|earlier\b|before\b))|"
    # The same recap said with the place instead of the words: "where were we up to",
    # "where i got to", "where we left off".
    r"\bwhere (?:were we|are we)(?=\s*(?:[?.!,]|$|up to\b|now\b|at\b))|"
    r"\bwhere (?:i|we) (?:were|was|are|got to|left off|ended up)\b"
    r"(?=\s*(?:[?.!,]|$|up to\b|now\b|again\b))|"
    # And with what we were doing: "what were we looking at", "what were we doing".
    r"\bwhat (?:were|was) (?:we|i) (?:looking at|doing)\b"
    r"(?=\s*(?:[?.!,]|$|again\b|earlier\b|before\b))|"
    r"\bwhat we were (?:just )?(?:looking at|doing)\b"
    r"(?=\s*(?:[?.!,]|$|again\b|earlier\b|before\b))|"
    # "back to my question", "back to the question", said after an aside.
    r"\bback to (?:my|your|the) question\b(?=\s*(?:[?.!,]|$))")


def _recap_shape(text, memory):
    """The line, folded, when it is a recap main's own gate does not read, else ""."""
    try:
        low = memory_store._folded(text, memory)
    except Exception:  # noqa: BLE001 - a line that cannot be read keeps the ordinary answer
        return ""
    if not low or not WANTED_AGAIN.search(low):
        return ""
    # No handing back to the store on the lines its own gate says it reads: its reminder-wrapper
    # pattern ("remind me what", "remind me where") matches the line and its recap reader still
    # does not answer it, so deferring here was the shrug it was meant to remove. The two
    # candidates say the same thing where both are made, and the store's band is the front one.
    return low


def ASKS_ABOUT_THE_CHAT(text, memory):
    """This line asks about the conversation, whatever topic its words happen to name."""
    return bool(_recap_shape(text, memory))


def _not_a_recap(text, memory):
    """True when a line is about the conversation rather than about the world it names.

    The store's own reading, widened by the shapes this module adds: a recap ask said back
    beside the thing we were on is the machine reading its own question out - "back to my
    question" came back as "You said remind you where you were" - so the newest line that is
    one of these is never the thing the chat is on, and never a thing the chat said.
    """
    try:
        return bool(memory_store._about_this_chat(text, memory)) or bool(
            _recap_shape(text, memory))
    except Exception:  # noqa: BLE001 - an unreadable line is simply not the filter's business
        return False


def _the_recap(memory, low):
    """The thing we were on and the ask, said back in the person's own words."""
    from ..memory import thread
    said = thread.last_said(memory, _not_a_recap)
    thing = thread.about(memory, _not_a_recap)
    if thing and not memory_store._a_thing(thing):
        thing = None
    ask = thread.last_ask(memory, _not_a_recap,
                          not_before=thread.topic_index(memory, _not_a_recap))
    if thing and ask:
        options = ["We were on " + thing + " \u2014 you asked " + ask + ". Want to carry on?",
                   "Still on " + thing + ": you asked " + ask + ".",
                   "The last thing we got into was " + thing + ", and you asked " + ask + "."]
    elif ask and said:
        options = ["You said " + said + ". You asked " + ask + ". Want to carry on?",
                   "You said " + said + " - and you asked " + ask + ".",
                   said[:1].upper() + said[1:] + ". Your question was " + ask + "."]
    elif ask:
        options = ["You asked " + ask + ". Want to carry on?", "You were asking " + ask + "."]
    elif said:
        options = ["You said " + said + ". Want to carry on?", "You last said " + said + ".",
                   "You'd told me " + said + ".", "Last thing you said was " + said + "."]
    elif thing:
        options = ["We were on " + thing + ".", "Still " + thing + "."]
    else:
        return ""
    return _fresh(options, memory)


def _fresh(options, memory):
    """An option that is not the line the bot has just said.

    A recap is short and made of the same few words as the last one, so a second ask in a row
    can land on the same sentence - "where were we up to" straight after "what were we just
    saying" - and the arbiter passes over a reply that only repeats the bot's last turn. Varying
    the words is the module's job, so the last line said is dropped here before the pick.
    """
    try:
        last = str(memory_store.last_bot(memory) or "").strip()
    except Exception:  # noqa: BLE001 - without the history every option is allowed
        last = ""
    fresh = [option for option in options if option.strip() != last] or options
    return memory_store._vary(fresh, memory)


def respond(text, memory):
    """The recap itself, on the shapes the store's own gate does not read."""
    low = _recap_shape(text, memory)
    if not low:
        return None
    try:
        if memory_store._about_the_bot_here(memory):
            # "what were you saying" about the bot itself is the bot's line, not the chat's.
            return None
        said = _the_recap(memory, low)
    except Exception:  # noqa: BLE001 - a reader that cannot answer leaves the turn as it was
        return None
    return said or None
