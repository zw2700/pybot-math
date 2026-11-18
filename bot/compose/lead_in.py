"""A lead-in in front of the ask is not part of the ask.

People chain a question onto what was just said, and the word they chain it with is not part of
it: "and", "also", "ok so", "but", "then". Main answers some of those and loses others, because
the reading of a line as a question is anchored at its first word:

    is b&q open on sunday
      -> "The opening hours are the first thing a venue changes and the last thing it tells
          anyone ... Their own page or map listing has the current ones."
    and is b&q open on sunday
      -> "Ask away, I'm listening. What's going on?"

The same ask, two letters in front of it, and the person gets the floor - a line that would fit
any message, which is the one thing this lane exists to keep off their screen. It reads as noise
rather than as a shrug, which is why nothing caught it: the line is not a hedge, so every pool
that stands down for a hedge kept it.

What this module does, and only this: a line whose first words are a lead-in and whose *rest* is
a question, where what the bot would say to the whole line is only the floor or a hedge, is
answered as the question it is - by the same composer, asked about the rest of the line. The
composer is not reimplemented here; `fallback.reply_for` is the one that answers, so the pool the
person gets is the pool they would have got without the two letters in front.

It stands down on everything else:

- a line that is not a question after the lead-in ("and my mum is in hospital", "and it was
  lovely") keeps whatever answered it - stripping the lead-in from a report would make the bot
  answer a question nobody asked;
- a line the bot can already answer keeps its answer: the floor-and-hedge test is what decides,
  so "and can you smell gas" still gets the gas card, and a card is never replaced;
- a line whose stripped ask gets only the floor too ("and what about it") gains nothing, so
  nothing is said;
- a first turn pointing back at nothing ("and what about that") is left to the modules that read
  a conversation that has not started.

The composer is asked twice - once about the whole line, once about the rest - so the rule is
general rather than a list of lead-ins bolted onto one reader: any reader that is anchored at the
first word is covered, and a reader that already tolerates a lead-in gives the same answer both
times and this module stands down.
"""
import copy
import re

from . import fallback
from ..memory import ack

# The words people chain a question on. A chain of them counts ("ok so, and is ..."), and so does
# one with a comma or a full stop after it, because that is how it is typed.
LEAD_IN = re.compile(
    r"^\s*(?:(?:and|but|so|also|plus|then|ok|okay|right|well|oh|ah|now|anyway|still)\b[\s,.!\-]*)+",
    re.I)

# The rest has to be a question in its own right: an auxiliary or a question word first, and
# enough words after it to be an ask rather than a noise ("and is it" is not worth stripping).
A_QUESTION = re.compile(
    r"^(?:is|are|was|were|am|do|does|did|can|could|will|would|should|shall|may|might|"
    r"have|has|had|what|when|where|which|who|whose|why|how)\b", re.I)
FEWEST_WORDS = 3

# The replies that hand the conversation back or merely receive it: the floor ("Ask away, I'm
# listening"), the nod ("Got it. Is there anything you'd like a hand with?") and the receipt
# ("Noted: ..."). These are the lines this lane exists to replace, and a line that is only one of
# them is the evidence that the lead-in cost the person their answer. A card is not in here, so a
# card is never replaced.
THE_FLOOR_OR_A_NOD = re.compile(
    r"^(?:ask away|i'?m listening|i am listening|go on\b|tell me more|say more\b|"
    r"i'?m here\b|take your time|over to you|spill it|i'?m all ears|"
    r"got it\b|noted\b|thanks for telling me|fair enough|right then|okay then|"
    r"sure\b|of course\b|go ahead\b|i'?ll do my best|good luck with it|"
    r"anything else\b|what'?s on your mind|ask me anything)", re.I)


def _only_the_floor_or_a_nod(said):
    """True when the reply is nothing but the floor, a nod or a receipt."""
    text = str(said or "").strip()
    if not text:
        return True
    if fallback.is_a_hedge(text):
        return True
    try:
        if ack.reads_as_a_receipt(text):
            return True
    except Exception:  # noqa: BLE001 - a receipt test that cannot run must not stop the module
        pass
    return bool(THE_FLOOR_OR_A_NOD.match(text))


def _the_rest_after_the_lead_in(line):
    """The question the line asks once the lead-in is off it, or "" when there is no lead-in."""
    match = LEAD_IN.match(line)
    if not match:
        return ""
    rest = line[match.end():].strip()
    if not rest or not A_QUESTION.match(rest):
        return ""
    if len(rest.split()) < FEWEST_WORDS:
        return ""
    return rest


def _a_copy(memory):
    """A copy of memory to ask a question of, the way the runtime makes one for a module."""
    try:
        return {key: value if key == "turns" else copy.deepcopy(value)
                for key, value in memory.items()}
    except Exception:  # noqa: BLE001 - a value that will not copy: share the conversation
        return memory


def _read_as_its_own_line(rest, memory):
    """The conversation's memory, with the understanding reread for the shorter line.

    Everything in the composer reads `memory["understood"]`, and by the time a module is asked
    that is the reading of the *whole* line - `and is b&q open on sunday` is a statement because
    it opens with `and`. Asking the composer about `is b&q open on sunday` with that reading in
    place gives the same floor line again, which is how the first cut of this module answered
    nothing at all. The reading is redone here for the words that are left, and only that: the
    understanding writes `understood` and nothing else, so no fact is filed twice.
    """
    mine = _a_copy(memory)
    try:
        from ..modules import understand  # noqa: PLC0415 - modules import this package
        understand.observe(rest, mine)
    except Exception:  # noqa: BLE001 - without the reread the composer sees the whole line
        return mine
    return mine


# A line that is already being treated as an emergency keeps the reply it has. The lead-in is not
# part of the ask, so the ask's own answer is the better reply - unless the reply on the table names
# help that has to be called now. Then nothing here goes near it.
NAMED_HELP_NOW = re.compile(
    r"\b(?:999|112|111|ambulance|a&e|casualty|emergency|suicid\w*|overdos\w*|poison\w*|"
    r"bleeding|unconscious|not breathing|chest pain|anaphyla\w*)\b", re.I)


# The words that carry no news on their own. The receipt and the day-shape pools build their lines
# round the person's own words - "{Thing} \u2014 noted.", "{Thing}. Not long now, then." - so a reply
# whose every word is either in the ask or in this set is the ask said back, whatever frame it is
# wearing. Naming the frames one by one would miss the next one; the words they are built from are
# a short list.
NO_NEWS = frozenset("""a an and the i me my we us our you your it its is was were be been being am
are do does did done can could would should will shall may might must have has had having to of in
on at for with from about as that this these those there here then now so but or if not no yes
well oh ah ok okay right sure got noted thanks thank you please just very really quite too also
still any some all more most much many long far off soon quickly quick plenty time times diary
forward looking look round around coming come going go ahead mind anything something nothing else
one ones what whats when where which who why how say said tell told""".split())


def _an_echo_of_the_ask(said, line):
    """True when the reply says nothing the ask did not already say.

    "Is b&q open on sunday \u2014 noted." and "Is b&q open on sunday. Not long now, then." are the
    person's own words in a frame. They are not the floor, so the floor test let them through, and
    in a conversation that is the shape the composer answers a chained ask with: the module stood
    down and the person kept the receipt. A card says something the ask did not ("the opening
    hours are the first thing a venue changes"), and that stays the answer.
    """
    words = re.findall(r"[a-z0-9&']+", str(said or "").lower())
    asked = set(re.findall(r"[a-z0-9&']+", str(line or "").lower()))
    return not [word for word in words if word not in NO_NEWS and word not in asked]


def _a_reply_of_its_own(said):
    """True when the reply says something of its own rather than handing the turn back."""
    return bool(said) and not _only_the_floor_or_a_nod(said)


def the_answer_the_lead_in_hid(text, memory):
    """The reply the ask would have had without the lead-in, or None.

    `memory` is the module's own copy, so the second question is asked of the same conversation.
    The first question gets a copy of its own: a call that reads memory must not leave a trace
    that changes what the second call sees.
    """
    line = " ".join(str(text or "").strip().split())
    rest = _the_rest_after_the_lead_in(line)
    if not rest:
        return None
    whole = fallback.reply_for(line, _a_copy(memory))
    if not _only_the_floor_or_a_nod(whole) and not _an_echo_of_the_ask(whole, line):
        # The bot already answered the whole line with something of its own. It may be another
        # module's card (this one answers above the small talk, so it has to be careful) and this
        # module has no way to see that card, only what the composer says: so it only ever steps in
        # where what the composer has for the whole line is the floor, a nod or a hedge.
        return None
    without = fallback.reply_for(rest, _read_as_its_own_line(rest, memory))
    if not _a_reply_of_its_own(without) or without == whole:
        # The conversation so far is colouring the answer, or the lead-in changed nothing. Either
        # way the ask is asked of the same composer with the turns taken out, which is the reading
        # the bot gives the line on its own: "and is b&q open on sunday" after two turns about a
        # boiler got the day-shape receipt, and the opening-hours card only when nothing was in
        # play. The turns are dropped for this one question and nothing else - the module still
        # stands down unless the answer it finds says something of its own.
        alone = {key: value for key, value in memory.items() if key != "turns"}
        fresh = fallback.reply_for(rest, _read_as_its_own_line(rest, alone))
        if fresh and _a_reply_of_its_own(fresh) and fresh != whole:
            without = fresh
    if not without:
        return None
    if without == whole:
        return None  # the lead-in changed nothing, so there is nothing to put back
    if NAMED_HELP_NOW.search(str(whole or "")) or NAMED_HELP_NOW.search(str(without or "")):
        return None  # an emergency reply is never replaced, and never replaces one
    if not _a_reply_of_its_own(without):
        # The ask on its own would get the floor or the search hedge too, so the lead-in did not
        # cost the person anything that this module could put back. A hedge is the one reply that
        # never helps, and this module must not hand one over.
        return None
    return without
