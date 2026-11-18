"""A plan said back on its own, with something to say after it.

"What am i doing this week" is answered out of the store, and when the store holds one plan the
answer is that line and nothing else:

    i have an exam on friday  /  what am i doing this week
      "You have an exam on friday."

It is the right fact and it is the whole reply. A friend told what the week holds says the thing
and then says something with it; reading the plan out and stopping is the person's own sentence
handed back, which is the one thing a reply must not be.

So a single plan gets a short tail. The tail asks about the plan, never about the chat, and it is
left off when the plan is long enough that the line already has a shape of its own. Several plans
need no tail: two sentences read back are a list, and the second is the thing to say after the
first.

Nor does a plan that was said back on the last turn: a repeat is framed as the repeat it is
("Same answer, and it covers this: ..."), and that framing can only see the sentence itself.

Two plans get no tail at all. One that names nothing but the days has no thing for "it" to hold,
and one that is a funeral is not an errand: after a death the reply does not move to the
arrangements unless the person asks.
"""

import re

from . import pick

# Said after one plan: a question about the plan itself, so the person can answer it with the
# thing they were going to say next anyway.
#
# Every one of them has to be true of a plan that has not happened yet. The sentence always
# carries its day ("You start your new job on monday"), and a tail that asks how it is going
# tells a person who is still waiting that the thing is already underway. So the three shapes
# are distinct and all of them look forward: a question about how they feel, a question about
# getting something ready, and nothing at all about how it went.
TAILS = (
    "How are you feeling about it?",
    "Is there anything you need before it?",
    "What do you want to have ready for it?",
)

# A plan that already runs this long is the whole line: another clause after it is a return
# nobody asked for, and every extra clause makes the fact harder to hear.
LONG_PLAN = 78

# The tail asks about "it", so the plan has to name a thing for "it" to be. "You're away next
# week" names nothing but the days, and "How is it going?" after it has no subject: every plan
# word that is one of these leaves the sentence as it is.
PLAN_WORDS = frozenset("""a an the of to on in at for with and or but my your our their his her
its it you i we they he she be been being am is are was were will would can could shall should
may might must going go gone away back off up down out over about around next last this that
these those coming week weeks month months year years day days night nights tomorrow today
tonight soon again still just also too very really quite nearly almost more most less""".split())


# A plan that is a death is not an errand. "My dads funeral is on friday" said back with "Do you
# need anything before it?" moves a bereavement straight to the arrangements, and the one thing a
# reply says after a death is that there is no rush. The plan's own words are enough to know: the
# loss is the whole plan, so nothing is asked about it.
GRIEF_PLAN = re.compile(
    r"\b(?:funeral|funerals|wake|burial|cremation|crematorium|memorial|mourners?|"
    r"viewing|interment|graveside|obsequies|death|deaths|died|dying|passing|passed away|"
    r"grave|remembrance)\b", re.I)


def _is_a_death(said):
    """True when the plan itself is a death, a funeral, or the arrangements around one.

    The arrangements are not the only way a plan names a death: "my mums death anniversary" and
    "my dads death certificate appointment" are both a death with a date on it, and asking what
    to have ready for them is the same misreading as asking it of a funeral.
    """
    return bool(GRIEF_PLAN.search(said))


def _said_on_the_last_turn(said, memory):
    """True when the bot's own last line was this plan.

    The tail is a question the bot puts after its own sentence, so the repeat reading has to
    look through it: the same plan handed back twice in a row is the same answer twice, and
    the turn that says so can only see it if the second one is the sentence on its own.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return False
    last = turns[-1] if isinstance(turns[-1], dict) else {}
    bot = str(last.get("bot") or "").strip()
    return bool(bot) and (bot == said or bot.startswith(said + " "))


def _names_a_thing(said):
    """True when the plan says what it is about, so "it" in the tail has something to hold."""
    return any(word.isalpha() and word.lower() not in PLAN_WORDS
               for word in said.strip(" .").split()[1:])


def with_a_tail(said, memory):
    """The one plan said back, and a short question after it.

    `said` is the sentence the store already built, ending in a full stop. Nothing about the
    plan is added, and the tail asks about the plan rather than saying anything about the world.
    """
    said = str(said or "").strip()
    if not said or len(said) > LONG_PLAN or said.count(".") > 1:
        return said
    if not _names_a_thing(said) or _is_a_death(said):
        return said
    if _said_on_the_last_turn(said, memory):
        return said
    return said + " " + pick(list(TAILS), memory, said)
