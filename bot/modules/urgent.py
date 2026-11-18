"""Someone they look after in trouble wins the turn over a pleasantry, and only that.

`bot/compose/urgent.py` holds the rules and the wording; this module is the proposal, so the
arbiter has something better than the fallback's nod to choose.

It answers in two places, and no others:

- the lines nothing claims, where the fallback would have nodded (a body in trouble is not small
  talk, so it sits above the greeting);
- **in place of the health topic entries**, because a swallowed thing is a poison line and the
  entries get it wrong: `my daughter ate a washing tablet` is screen-time advice on the entries and
  a 999 call here. `ANSWERS_INSTEAD` scopes that to one topic, and the reading is strict - a
  relative and an ingest verb with a chemical, medicine or small object - so nothing else moves.
"""
from ..compose import urgent

# Below zero on purpose: it answers only the lines nothing else claims, and the health takeover
# rides on ANSWERS_INSTEAD, which the arbiter now reads from every band. Above the greeting
# fallback (-1000) so an unclaimed body in trouble is not answered as small talk.
PRIORITY = -900

# Not a topic of its own: it reads a body in trouble, not a subject.
ANSWERS = ()

# In place of the health entries only: a swallowed thing is a poison line before it is advice.
ANSWERS_INSTEAD = ("health",)


def respond(text, memory):
    return urgent.reply_for(text, memory)
