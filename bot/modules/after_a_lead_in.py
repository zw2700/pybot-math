"""The ask behind a lead-in: "and is b&q open on sunday" is the same question as without it.

People chain a question onto the turn before it, and the word they chain with is not part of the
ask. Some of the readers in the composer are anchored at the first word of the line, so the same
ask with `and` in front of it stops reading as a question at all:

    is b&q open on sunday
      -> "The opening hours are the first thing a venue changes and the last thing it tells
          anyone ... Their own page or map listing has the current ones."
    and is b&q open on sunday
      -> "Ask away, I'm listening. What's going on?"

Not a hedge, which is why nothing caught it: every pool that stands down for a hedge kept it.
This module takes that turn - a lead-in, a question after it, and a whole-line reply that is only
the floor or a nod - and answers it with what the composer says about the ask itself. Priority is
just above the small talk (300), which is the pool the floor line comes from, and below the
modules that answer for themselves (350 and up), so nothing that knows the subject loses a turn.

It is additive: the rule lives in `bot/compose/lead_in.py` and the composer is asked twice rather
than patched, so no frozen file is touched.
"""
from ..compose import lead_in

PRIORITY = 320  # above chat and their_pastime (300), below said_back (350) and the rest


def respond(text, memory):
    return lead_in.the_answer_the_lead_in_hid(text, memory)
