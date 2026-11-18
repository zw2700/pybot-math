"""A question about the person's own record is answered by the store, even when it holds nothing.

"Where did i park?" -> "You haven't told me where you parked." Nobody else can answer a question
about the person's own life: the store is the only part of the bot that could, and the store
saying it holds nothing is the whole of the answer there is. `bot/compose/fit.py` reads those
words as a shrug - `PUNT` opens "you haven't told me ..." - so the reply that is exactly right for
the line was counted a miss for every shape, and the answer the person needed (that the bot has
nothing on record, and would like to be told) lost its credit to nothing.

The fence is the one the store's own sentence gives us:

  * only the fact shapes a question about their own record can ask for - a pick, a method, a
    reason or a few ideas is the bot's own judgement, and "You haven't told me what you like" is
    a question back rather than the pick that was asked for;
  * the sentence has to be the opening one, so a paragraph that carries the words somewhere past
    the middle is not credited;
  * no "?" anywhere in the reply: a question back is not an answer, whatever it says before it;
  * a short reply, so the store's own one-liner is what is being read.

It is a module rather than a line in `bot/compose/fit.py` only because the foot of that file is
where every arm of the swarm lands at once and a change there is refused while main moves. It
wraps `fit.gives` once, at import, and saves the function it wrapped; `bot/modules/arbiter.py`
and `bot/compose/lead.py` both call `fit.gives` by attribute, so both see this check. Every
reading it does not name is the one `fit.gives` gives.
"""
import re

from ..compose import fit

# The shapes a question about the person's own record can ask for: a time, an amount, a place, a
# person, a meaning, a yes or no. The rest are the bot's own judgement, and the store holding
# nothing is not an answer to them.
ON_RECORD = frozenset((fit.TIME, fit.AMOUNT, fit.PLACE, fit.PERSON, fit.MEANING, fit.YESNO))

# The store's own sentence, in the words it uses: "You haven't told me where you parked.",
# "You haven't said who's going with you.", "You haven't mentioned what you weigh."
NOT_ON_RECORD = re.compile(
    r"\b(?:you|ye) (?:have not|haven'?t) (?:said|told|mentioned|let me know)\b", re.I)

# The store's sentence is one line. A longer reply that happens to carry it is a paragraph about
# the line, and the paragraph may be prose that gives nothing.
LONGEST = 180

_gives_before_this_module = fit.gives


def gives(reply, want, line=None):
    """`fit.gives`, with the store's own "i hold nothing about that" counted as the answer."""
    got = _gives_before_this_module(reply, want, line)
    if got is True or want not in ON_RECORD:
        return got
    text = " ".join(str(reply or "").split())
    if "?" in text or len(text) > LONGEST:
        return got
    if not NOT_ON_RECORD.search(fit.first_sentence(text)):
        return got
    return True


# Teaching the module the wider reading is the whole of this file: the two places that ask the
# check (`bot/modules/arbiter.py` and `bot/compose/lead.py`) read `fit.gives` by attribute.
fit.gives = gives
