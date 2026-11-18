"""The plea for a hand, said into a chat that is already a bereavement.

"i dont know what to do" a turn after "my mum died last month" is not a request for a search
result. It is the person asking how to keep going, and the composer had two replies for it that
are the worst lines in the file: the search hedge ("That's beyond what I know well, sorry.
Searching for it will turn up better sources than I can offer") and the nod ("I'm listening - say
more if it helps"). Neither is true of a bereavement, and both send somebody who has just said
they are lost to a search engine.

The line names no death and no subject of its own, so nothing else can read it as part of this
chat: the death is in the turns above. `loss.continues` is what says so, and the words below are
the ones that ask for nothing in particular.

What is replaced is only a reply that left the answer where it was - the nod or one of the two
search hedges (`fallback.NEUTRAL`, `fallback.UNKNOWN`). A reading with something of its own to say
to the line keeps the turn: "i dont know what to do" after "our dog was put down yesterday" is
already answered by the pool that starts with "Keep it small. One phone call, one meal", and that
is better than anything here, so this file stands down the moment the composer has an answer.
"""

import re

from . import fallback, loss

# The plea with nothing in it: the ask word on its own, the verb with nothing after it, or the
# despair said as a state ("im lost", "i dont know what to do"). Each shape is read to the end of
# the line, so a line that names a subject keeps its own answer: "any ideas for what to say" is
# the words ask (loss.ASK_WORDS), "any ideas for the wake sandwiches" is the wake.
TAIL_SO_FAR = '(?:\\s+(?:now|next|then|though|really|at\\s+all|anymore|today|please))*\\s*\\?*\\s*$'

A_PLEA_WITH_NOTHING_IN_IT = re.compile(
    r"^(?:(?:ok|okay|so|right|and|but|well|please|now|honestly|yeah)\s+)*"
    r"(?:"
    # the ask word alone: "any thoughts", "ideas please", "any advice then", "tips", "help"
    r"(?:any\s+)?(?:ideas?|thoughts?|advice|suggestions?|tips?|help)"
    r"\s*(?:please|then|for me)?\s*\?*\s*$"
    # "what do you think", "what would you do", "what should i do now"
    r"|what\s+(?:do|would|should)\s+(?:you|i)\s+(?:think|do|say|suggest)" + TAIL_SO_FAR +
    # "i dont know what to do", "i really dont know what to do now"
    r"|(?:i\s+)?(?:really\s+|just\s+)?(?:dont|don'?t|do not)\s+know\s+what\s+to\s+do"
    + TAIL_SO_FAR +
    # "im lost", "im so lost", "i feel lost"
    r"|(?:im|i'?m|i\s+feel|i\s+am)\s+(?:so\s+|totally\s+|a\s+bit\s+|completely\s+)?lost"
    + TAIL_SO_FAR +
    # "where do i even start", "i dont know where to start"
    r"|(?:where\s+do\s+i\s+(?:even\s+)?start|(?:i\s+)?(?:dont|don'?t|do not)\s+know\s+where"
    r"\s+to\s+start)" + TAIL_SO_FAR +
    # "not sure what to do next", "no idea what to do"
    r"|(?:not\s+sure|no\s+idea)\s+what\s+to\s+do" + TAIL_SO_FAR +
    r")", re.I)

# The replies that put nothing on the table, so replacing one loses nothing: the nod and the two
# search hedges. Every other pool is somebody's answer and stands.
# `TIPS_LINES` is here for the same reason as the two hedges: "any tips" after a death was answered
# "Sure. What have you tried so far? That tells me where to start." Asking a bereaved person what
# they have tried is the bot asking for the context it should not need - this file knows what
# helps in the first days and says it.
NOTHING_OF_ITS_OWN = (fallback.NEUTRAL, fallback.UNKNOWN, fallback.TIPS_LINES)


def _said(text):
    return " ".join(str(text or "").lower().split())


def reply_for(text, reply, memory):
    """A keeping-going line for a plea inside a bereavement, or None."""
    said = _said(text)
    if not said or not A_PLEA_WITH_NOTHING_IN_IT.match(said):
        return None
    if not isinstance(memory, dict) or not str(reply or "").strip():
        return None
    if not fallback._in_a_pool(reply, NOTHING_OF_ITS_OWN):
        return None
    if not loss.continues(memory):
        # The chat is not a bereavement: nothing above says a death, so the plea is an ordinary
        # bare ask and the pools it landed on are the ones every other reader answers.
        return None
    pool = loss.GETTING_THROUGH_REPLIES
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    # None of the pool said twice: a person who asks three ways in a row is asking harder, not
    # asking for the same sentence again, and the four lines here are four different things to do
    # today. Only when every line has been used does the pool come round again.
    already = set(str(turn.get("bot") or "") for turn in turns)
    fresh = [line for line in pool if line not in already] or list(pool)
    return fallback.pick(fresh, memory.get("understood") or {}, said)
