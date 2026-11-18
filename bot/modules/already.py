"""A report that the step was already taken is answered with the next turn of the thread.

"someone used my card online" / "i already called the bank" got "Got it. Is there anything
you'd like a hand with?", and a bare "i already called the plumber" got "I'm listening - say
more if it helps." Neither answers the person: they told the bot something they had done, and
what they want is what comes next. The reading is `bot/memory/already.py`, which says which step
it was so the question that follows it fits - "what did they say?" after a call, "is it any
better since?" after a repair.
"""
from ..memory import already

# Above the small talk (chat, 300), which is what answered these lines with a stock nod, and
# below the store (7000) and the safety modules: a fact stated with an "already" is still the
# store's, and an emergency is never this module's.
PRIORITY = 400


def respond(text, memory):
    return already.reply_for(text, memory)


# The report is not an ask, and a knowledge entry reads it as the same question again. So the
# line is claimed as it comes - but only when the step named is one the last answer itself asked
# for. A new ask the entry should still answer is never claimed, and the "ive tried the plunger
# already" shape is left to `repeat`, which hands back the step they have not tried.
TAKES_AS_IT_COMES = already.takes_as_it_comes
