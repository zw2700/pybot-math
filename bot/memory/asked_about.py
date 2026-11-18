"""The answer this chat already gave, when a later line names the thing it was about.

    i havent slept much          -> Nights like that wear you down ...
    i keep waking at 3           -> Waking in the night is normal - sleep runs in cycles ...
    my head is full              -> The fix is what you do in those minutes ...
    and how do i get some sleep  -> I'm not sure about that one, sorry - I'd rather not guess.

The chat had the sleep answer three turns up and then said it did not know enough. Nothing read
the line: every reader that hands an earlier answer back is reached only when a module *serves*
that answer again, and on this line nothing does - the composer has no card for "some sleep", so
the search hedge is the only candidate left, and it is the one answer that cannot help when the
chat itself holds the answer.

`topics.answer_about` already finds that card: it scores the line's own words against every
`answers` turn in the last six and returns the one they belong to. Nothing asked it on this path.
So this is the asking, and the reply is the sentence of that card which carries the words the
line asked with, said as the return it is - "Back to sleep: ...".

Narrow on purpose:

* it is only ever read in place of a hedge (`bot/modules/greeting.py`), so a line with an answer
  of its own keeps it. That is the same gate the answer-on-screen reader uses;
* the line has to name a thing, a content word the card also names, so a bare "and what should i
  do" - which belongs to every answer that gives a step - is left to the readers that own it;
* the sentence said back may not be one the bot has just said, so this cannot be a repeat dressed
  as a return, and the whole card is never handed over: it is the part that answers the line.
"""
import re

from . import topics

# A sentence break, for cutting the earlier card to the part that answers this line.
SENTENCE = re.compile(r"(?<=[.!?])\s+")

# The lead says the answer is one the chat already has, and names the thing the line asked with,
# so the person can see why they are being given it again. Rotated on the turn count so a chat
# that leans on this twice does not hear the same frame twice.
RETURN = (
    "Back to {thing}: {reply}",
    "Back to {thing} then: {reply}",
    "It is the same answer on {thing}: {reply}",
    "As before on {thing}: {reply}",
)

# A line with more than one content word names no one thing to put in the lead: "what kills the
# ants" is about the ants and the killing, and "As before on kill" is not a thing anybody says. So
# the thing is only named when the line named exactly one, and otherwise the lead says the same
# without it. Nothing else about the reply changes.
RETURN_UNNAMED = (
    "Back to what I said: {reply}",
    "It is the same answer as before: {reply}",
    "As before: {reply}",
    "Back to it: {reply}",
)

# A sentence shorter than this many words carries too little to be an answer on its own ("Yes.",
# "Not always."), so the sentence after it is said with it.
SHORT = 5

# At most this many words of the card, so the reply stays one answer and not the paragraph again.
MOST = 45


def _sentences(answer):
    return [one.strip() for one in SENTENCE.split(str(answer or "").strip()) if one.strip()]


# The asking itself: a question word, or a word that points at the answer rather than naming a
# thing ("so whats left now" is about the money two turns up, and "what" is not a thing any card
# has a sentence about). They are what the line asks with, so they cannot be what ties it to an
# earlier answer - the same reason `topics._answer_about` drops the asking for a figure.
_NOT_A_THING = frozenset("""
what which who whom whose how when where why whether whats
now then again left else next other same other another anything something nothing everything
please thanks ok okay well so and but
""".split())


def _the_words_asked(text):
    """The content words of the line, without the asking: "how do i get some sleep" -> sleep."""
    out = []
    for word in topics.keywords(text):
        if word in topics.ASK_ONLY or word in _NOT_A_THING or word in out:
            continue
        out.append(word)
    return out


# A sentence that opens on one of these is the second half of the one before it ("If you're worn
# out all day too, or it has gone on for weeks, ask a GP"), and said alone it starts in the middle
# of a thought. It is still read when nothing else carries the line's words - the reply is the
# answer it belongs to - but a whole sentence is preferred to it.
_A_CONTINUATION = re.compile(
    r"^(?:if|and|or|but|so|then|also|because|when|while|though|although|plus|that said)\b", re.I)


def _the_part_that_answers(answer, wanted, said_before):
    """The sentence of the card that carries the words the line asked with, and its neighbour."""
    parts = _sentences(answer)
    if not parts:
        return ""
    scored = []
    for index, part in enumerate(parts):
        here = {topics.stem(word) for word in topics.keywords(part)}
        score = len(here & set(wanted))
        stands = 0 if _A_CONTINUATION.match(part) else 1
        scored.append((score, stands, index))
    # A sentence that stands on its own beats one that opens mid-thought with the same words in
    # it, so the return reads as an answer and not as the tail of one.
    scored.sort(key=lambda triple: (-triple[0], -triple[1], triple[2]))
    best = scored[0]
    if best[0] and best[1]:
        index = best[2]
    elif best[0]:
        # The only sentences with the line's words in them open mid-thought ("If you're worn out
        # all day too ... ask a GP"): the card is still about the thing asked, so its own first
        # whole sentence is the answer, not the tail of another.
        index = next((i for i, part in enumerate(parts) if not _A_CONTINUATION.match(part)), best[2])
    else:
        return ""  # the card says none of the words the line asked with
    out = parts[index]
    if len(out.split()) < SHORT and index + 1 < len(parts):
        out = out + " " + parts[index + 1]
    if len(out.split()) > MOST:
        out = " ".join(out.split()[:MOST]).rstrip(" ,;:") + "."
    # The bot may not say the same sentence twice in a row: if this is the one it has just said,
    # nothing is handed back - the hedge is better than the same way twice.
    flat_before = " ".join(str(said_before or "").lower().split())
    if flat_before and " ".join(out.lower().split())[:60] in flat_before:
        return ""
    return out


def the_answer_this_chat_gave(text, memory):
    """The earlier answer of this chat about the thing the line names, as the return it is."""
    if not isinstance(memory, dict):
        return None
    wanted = _the_words_asked(text)
    if not wanted:
        return None
    answer = topics.answer_about(text, memory)
    if not answer:
        return None
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    said_before = str(turns[-1].get("bot") or "") if turns else ""
    part = _the_part_that_answers(answer, wanted, said_before)
    if not part:
        return None
    said = " ".join(part.lower().split())
    just_said = " ".join(str(turns[-1].get("bot") or "").lower().split()) if turns else ""
    if said[:60] and said[:60] in just_said:
        return None  # the sentence just said is not a return, it is the same way twice
    frame = RETURN[len(turns) % len(RETURN)] if len(wanted) == 1 else RETURN_UNNAMED[
        len(turns) % len(RETURN_UNNAMED)]
    return frame.format(thing=wanted[0], reply=part)
