"""A thing of theirs in a state that wants doing, and nobody in the line.

"the grass is long", "the car is dirty", "the windows are filthy", "my shoes are worn out" and
"my coat is tatty" were all answered with the composer's receipt - "Thanks for telling me - I'm
here if you want to dig into any of that" - which says nothing back about the thing the person has
just handed over and asks nothing about it either. A friend looks at the thing with them: how bad
it is, whether it is a quick job, where they would start.

The reading is the shape `my/our/the <thing> is <state>`, where the state is one of the adjectives
that says the thing wants doing rather than that it has gone wrong (`trouble` has the gone-wrong
ones: broken, cracked, leaking). It stands down for a body part, for a person, and for anything the
line says the person feels - those have answers of their own - and it is asked only on a receipt,
so a card, an entry or any other reply keeps the turn.
"""
import re

from .fallback_data import BODY_PARTS

# The states that say the thing wants doing. A thing gone wrong is `trouble`'s to read, and a
# thing that is simply old is not a job ("my bike is old" already gets the offer of a hand).
A_STATE = frozenset((
    "long", "overgrown", "dirty", "filthy", "grimy", "mucky", "tatty", "shabby", "scruffy",
    "worn out", "worn", "messy", "untidy", "dusty", "faded", "rusty", "grim", "cluttered",
    "piled up", "manky", "minging", "grubby",
))

# A state in the past is the day's account and not a job still to do: "my night shift was long",
# "the meeting was long" are what happened, and they are read by the day pools. Only the present
# tense is a thing sitting in front of the person.
# Somebody in the line is a person with a day of their own, not a thing to look at: "my son is
# tired", "my mum is worn out", "the kids are messy" are about them.
A_PERSON = frozenset("""
mum mom mam dad father mother son daughter child children kid kids baby toddler boy girl husband
wife partner boyfriend girlfriend brother sister mate mates friend friends nan granny grandma
grandad grandpa aunt uncle cousin neighbour neighbor boss colleague client cat dog puppy kitten
puppies rabbit hamster horse hens chickens bird birds fish
""".split())

# What the person feels is the line's subject and not the thing: "im sick of it being dirty",
# "im fed up with the mess". The feeling words are the ones the mood pools already read.
A_FEELING = frozenset("""
sick tired fed up had enough annoyed angry cross sad upset stressed worried depressed
embarrassed ashamed guilty lonely done exhausted shattered
""".split())

THE_THING_IS = re.compile(
    r"^(?:the|my|our|your|his|her|their)\s+(?P<thing>[a-z]+(?:\s+[a-z]+)?)\s+"
    r"(?:is|are|looks|seems|gets|got)\s+(?:a bit |a little |really |very |so |quite |"
    r"proper |right |pretty |well )?(?P<state>worn out|piled up|[a-z]+)\s*$", re.I)

A_THING_WANTS_DOING = (
    "How bad is it — something you can do in an hour, or has it got away from you?",
    "What's the job on it? I'll work the next step out with you.",
    "Tell me how bad it is and I'll work out where to start.",
    "Right. How long has it been like that?",
    "Where would you start with it?",
)


def reads(text, memory=None):
    """The thing the line hands over, when it is in a state that wants doing."""
    flat = " ".join(str(text or "").lower().split())
    if not flat or len(flat.split()) > 8:
        return None
    if any(word in A_FEELING for word in flat.split()):
        return None
    found = THE_THING_IS.match(flat)
    if not found:
        return None
    state, thing = found.group("state"), found.group("thing")
    if state not in A_STATE:
        return None
    if any(word in A_PERSON or word in BODY_PARTS for word in thing.split()):
        return None
    return thing


def pool(text, memory=None):
    if not reads(text, memory):
        return None
    return A_THING_WANTS_DOING
