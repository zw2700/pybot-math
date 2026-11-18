"""A paragraph the chat has had is not printed again in the same words.

Every reader in the answers module frames a repeat it can see - the row handed back a turn ago,
the sentence of it this line names - and each of them compares the answer it would give with the
answer *just above*. What none of them sees is a reply that comes back a few turns later, after a
turn about something else, because the line reached the same row again:

    the slugs are eating my hostas
      Go out after dark with a torch and pick them off, which beats most products; copper tape ...
    how do i get rid of them
      Start with this: Go out after dark with a torch and pick them off.
    changing subject, the lawn needs cutting
      Mow little and often in the growing season ...
    when should i mow it
      Mow little and often in the growing season ...          (the turn above, word for word)
    back to the slugs, when should i put the trap out
      Go out after dark with a torch and pick them off, which beats most products; copper tape ...

A person reading that hears a bot that has stopped listening, and it is the thing a person notices
first in a long chat: the words are not wrong, they are the ones they have already read.

So the framing is done once, for whatever route the reply came by, rather than in each of the
readers above: `bot/memory/again.instead` holds the lead-ins and every guard that says when a
repeat is not one (a figure asked back, a part of the answer the line adds, a lead-in already in
front), and it passes a reply the chat has not had, so this returns exactly what it was given.

Why here and not in the answers module: the answers module is one of four parts, and the same
paragraph can come back through another one (a saving, the store's own reply). The reading is a
property of the chat, not of the part that chose the words, so it lives with the memory.
"""
from . import again


# The words a reply can already open with when a reader in the answers module framed it: the
# static front of every lead-in in `again.FRAMES` ("Same answer, and it covers this:", "Back to
# the tap:"). The guard `again._carries_a_lead_in` reads `topics.REPEAT_LEADS`, which holds three
# of the nineteen, so a paragraph a reader had already framed would be framed a second time here
# ("Same as before: Same answer, and it covers this: ...").
A_LEAD_ALREADY = tuple(frame.split("{")[0].strip().lower()
                       for frame in again.FRAMES if frame.split("{")[0].strip())


def a_paragraph_the_chat_has_had(reply, text, memory):
    """`again.instead(reply)`, or the reply itself when it is new to the chat."""
    if not isinstance(reply, str) or not reply.strip():
        return reply
    try:
        if reply.lower().startswith(A_LEAD_ALREADY):
            # A reader above has already framed it, so a second lead is never stacked on the first
            # - but the framed reply itself can come back word for word, and that is answered.
            return the_same_paragraph_again(reply, memory) or reply
        framed = again.instead(reply, text, memory) or again.already_had(reply, memory)
    except Exception:  # noqa: BLE001 - a turn is never lost to the repeat floor
        return reply
    if not framed:
        return reply
    # The frame the reader would put on it is the frame the turn above already wears, so the
    # paragraph would go out twice behind the same words: say it behind the next lead instead.
    return the_same_paragraph_again(framed, memory) or framed


def the_same_paragraph_again(reply, memory):
    """A reader above framed it, and the chat has had that framed reply word for word.

    The reader's own guard compares the whole reply with the turn above it, so the second time
    the same card reaches the same reader the paragraph goes back out under the same lead - a
    reply that repeats an earlier reply, which is the thing the first frame was there to avoid:

        where do i get the part   -> Same answer, and it covers this: A dripping tap is nearly ...
        do i need to turn the water off -> Same answer, and it covers this: A dripping tap is ...

    So the short of the paragraph goes back behind the next lead in `again.SHORT_AGAIN` - the
    leads other modules recognise as framed ("Same as before:", "As I said:"), which keeps a
    second lead off it - and once those run out the person is asked what went wrong rather than
    being handed the paragraph a fourth time. A reply with no lead-in is left alone here: the
    reader above chose it, and `already_had` had its turn.
    """
    body = again.unframed(reply)
    if not body:
        return None
    mine = again._flat(reply)
    said = 0
    for turn in memory.get("turns") or []:
        if isinstance(turn, dict) and again._flat(turn.get("bot")) == mine:
            said += 1
    if not said:
        return None
    short = again._short(body)
    if not short or again._flat(short) == again._flat(body):
        short = body
    if said >= len(again.SHORT_AGAIN):
        return again.AGAIN_HELP.format(reply=short)
    return again.SHORT_AGAIN[said - 1].format(reply=short)


def then_framed(respond):
    """Wrap a `respond(text, memory)` in the floor, so the module that owns the words is untouched.

    The answers module already rebinds `respond` once at the end of the file (`again.replied`), so
    the floor is applied the same way rather than written into the reader it sits under: the diff
    to a module this busy stays at the file's tail, and the floor is read on its own here.
    """
    def a_reply_framed_as_the_repeat_it_is(text, memory):
        return a_paragraph_the_chat_has_had(respond(text, memory), text, memory)
    return a_reply_framed_as_the_repeat_it_is
