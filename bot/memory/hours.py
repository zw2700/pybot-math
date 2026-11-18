"""The turn after the hours: does that get easier, how do I stop, how do I plan.

The bot has just answered a line about the week somebody works - "i start at six so im up at
five", "i work from home now" - and the next line asks the thing that follows from it:

```
i start at six so im up at five / does that get easier
  before: That's beyond what I know well, sorry. Searching for it will turn up better sources

i work from home now / i never know when to stop
  before: Got it. Is there anything you'd like a hand with?
```

Both are the same failure: the bot forgets the week it was just talking about and answers the
follow-up as if the line before had never been said. So the family the hours line named is kept
for one turn in `memory["hours"]`, and the follow-up is answered from it - an early start is
answered about the going to bed, working from home about the day having no end.

The rule is narrow on purpose:
* the hours have to be the turn before this one, so a "does that get easier" three turns later,
  after something else entirely, is not this conversation's question;
* the line has to be one of the three things people actually ask after saying their hours - will
  it get easier, how do I switch off, how do I plan around it - and nothing else;
* a death in the last few turns, a body that hurts, bad news or a feeling all keep their own
  answers, whatever was said about the hours before them;
* it never fires on the same line twice, and the pools are chosen off the line, so two people who
  both say "i work nights" do not get the same sentence back.
"""
import re

from ..compose import pick

# Written by bot/memory/ack.py when it answers a line about the hours: the family that line
# named, and the turn it was said on.
HOURS_KEY = "hours"

# The family in the words a sentence can use for it.
FAMILY_NAMES = {
    "nights": "nights",
    "early": "an early start like that",
    "late": "a finish that late",
    "long": "shifts that long",
    # A week with two jobs and a rota in it are both spread, and only one of them moves, so the
    # words here cannot say "rota": the person who said "i work two jobs" never mentioned one.
    "spread": "a week laid out like that",
    "home": "working from home",
}

EASIER_ASK = re.compile(
    r"\b(?:does|do|will|would|is|did)\s+(?:that|it|this|they)\s+(?:ever\s+|eventually\s+)?"
    r"(?:get|gets|be|become|gets)\s+(?:any\s+)?(?:easier|better|any easier)\b"
    r"|\b(?:will|do)\s+i\s+(?:ever\s+)?get (?:used to|over)\s+(?:it|them|that)\b"
    r"|\b(?:it|that|this|they)\s+(?:ever\s+)?gets?\s+(?:any\s+)?easier\b"
    r"|\b(?:does|will) (?:that|it|this) (?:ever )?stop\b", re.I)
STOP_ASK = re.compile(
    r"\b(?:i|we)\s+(?:never|can'?t|cant|don'?t|dont|just can'?t)\s+(?:ever\s+)?"
    r"(?:know when to stop|switch off|stop|wind down|log off)\b"
    r"|\bhow do i (?:switch off|stop|wind down|log off)\b"
    r"|\b(?:hard|impossible) to switch off\b", re.I)
PLAN_ASK = re.compile(
    r"\b(?:its|it is|it'?s|that is)\s+(?:so\s+)?hard to plan\b"
    r"|\b(?:i|we)\s+(?:can'?t|cant|never)\s+plan\b|\bnever know my week\b"
    r"|\bhow do i plan\b|\bimpossible to plan\b", re.I)

# Will it get easier: the answer is about how long the hard part lasts and what actually changes.
EASIER_TAIL = (
    "It does, and the change is in the sleep rather than in the work: {hours} only start to sit "
    "right once the going to bed moves with them, and that takes a week or two rather than a "
    "night.",
    "Yes, in stages. The first fortnight with {hours} is the worst of it, and what is still hard "
    "a month in is worth taking to a doctor, because that part is not the adjustment any more.",
    "It gets easier. The body is not the slow part - the evenings are, and those only settle once "
    "they have a fixed edge at both ends.",
)
# How to stop: an end put on the clock, not on the work. These two say nothing about the kind of
# week, because "a time that stops working from home" is not a sentence.
STOP_TAIL = (
    "Then put the end on the clock rather than on the work: a time that finishes the day whatever "
    "is still undone, because the work never runs out by itself.",
    "Take the last hour back deliberately. It is easier to protect a slot than a mood, and a day "
    "with no end will take every open minute it is given.",
)
# How to plan: keep the two or three fixed things, let the rest be found.
PLAN_TAIL = (
    "Plan less and keep it fixed: two or three things a week that cannot move is all a plan should "
    "hold, and the rest of the week is better left loose.",
    "Keep the sleep and one day off in the same place every week. Those two are what the rest of "
    "the week hangs on, and they hold even when the week moves under them.",
)

KINDS = (("easier", EASIER_ASK, EASIER_TAIL),
         ("stop", STOP_ASK, STOP_TAIL),
         ("plan", PLAN_ASK, PLAN_TAIL))

# Words that take the line away from the hours whatever it says: a death, a body that hurts, bad
# news, a feeling on its own. It is the same set bot/memory/ack.py keeps the hours out for.
AWAY = re.compile(
    r"\b(?:die|died|dies|dying|death|dead|kill|killed|suicide|funeral|hospital|ambulance|"
    r"bleeding|blood|chest|breathless|sore|pain|hurts|aching|ill|sick|diagnosed|cancer|"
    r"redundant|sacked|fired|dumped|divorce|miss|miss him|miss her)\b", re.I)
FEELING = re.compile(
    r"\b(?:sad|lonely|alone|awful|terrible|horrible|miserable|hopeless|worthless|hate myself|"
    r"cant cope|can'?t cope|breaking down|crying|anxious|depressed|scared|worried sick)\b", re.I)

MOST = 12
LOOK_BACK = 1


def note(memory, family):
    """Keep the family of week the hours line named, for the turn after it."""
    if not isinstance(memory, dict) or not family:
        return
    turns = memory.get("turns")
    turn = len(turns) if isinstance(turns, list) else 0
    memory[HOURS_KEY] = {"family": str(family), "turn": turn}


def remembered(memory):
    """The family named on the last turn, or None when the hours are older than that."""
    held = memory.get(HOURS_KEY) if isinstance(memory, dict) else None
    if not isinstance(held, dict):
        return None
    turns = memory.get("turns")
    if not isinstance(turns, list):
        return None
    if held.get("turn") != len(turns) - LOOK_BACK:
        return None  # the hours were said longer ago than the turn before this one
    family = str(held.get("family") or "")
    return family if family in FAMILY_NAMES else None


def answer_for(text, memory):
    """A reply to the follow-up about the hours just said, or None when this is not one."""
    if not isinstance(text, str):
        return None
    clean = " ".join(text.split())
    if not clean or len(clean.split()) > MOST:
        return None
    if AWAY.search(clean) or FEELING.search(clean):
        return None
    family = remembered(memory)
    if not family:
        return None
    for _kind, pattern, pool in KINDS:
        if not pattern.search(clean):
            continue
        # "does that get easier" is a question and "i never know when to stop" is a statement,
        # and both are the same follow-up, so neither shape decides anything here.
        return pick(pool, memory, clean).format(hours=FAMILY_NAMES[family])
    return None
