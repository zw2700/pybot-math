"""The reply to a safety question about a thing of theirs.

The second turn of a thread about something in the house: "boiler dripping water" / "is it safe
to keep it on tonight", "the plug socket is cracked" / "can i still use it", "my heater smells of
burning" / "can i leave it on overnight", "my laptop charger is frayed" / "is it safe to keep
using it", "is the kettle safe to leave on". Before this reading those reached the repeat frame
("That was the whole of my answer on it. Tell me which part to take further and I will"), the
search shrug ("That's beyond what I know well, sorry") and "I'm not sure about that one, sorry -
I'd rather not guess". None of the three is a reply to somebody standing next to a dripping
boiler asking whether to leave it on overnight.

The person is asking one thing - do I stop using it tonight - and its answer does not depend on
the make: what makes a thing a stop is a burning smell, sparks, or a plug or socket hot to the
touch, with water near the electrics as the same kind of tell; failing those it can wait for the
morning. Every line says both halves, because "is it safe" is a yes or no.

Two things keep this reading narrow. The thing has to be one with a plug, a flame or water in it,
named in this line or in the line before, so a knee, a child with a temperature and a question
about what to cook are left alone. And the knowledge module is asked first: where its card names
the same thing ("a charger that is warm is normal", "what makes a boiler unsafe is..."), the card
keeps the turn and this reading says nothing. That is the same rule as #6308's bare doubt - an
entry takes the turn on a word of the subject, not on a word of the line.

When the bot's own last reply has already ruled ("don't use it again until it has been checked"),
the answer is that ruling said once, not a fresh test and not a shrug.

This lives in its own file because `bot/compose/fallback.py` is within 3.4 kB of the 1 MiB the
world will upload, and a reading of this size cannot go in it. The caller owns everything wider:
`fallback._reply_for` decides when the composer is allowed to speak at all, and picks the line.
"""
import copy
import re

from ..memory import last_bot, last_user

# "is it safe", "is it dangerous", "can i still use it", "can i leave it on overnight", and the
# same ask with the thing in the middle of it ("is the kettle safe to leave on").
ASK_IF_A_THING_IS_SAFE = re.compile(
    r"\bis\s+(?:it|that|this|they)\s+(?:safe|dangerous|a\s+(?:fire\s+)?(?:risk|hazard))\b"
    r"|\bis\s+it\s+(?:safe|alright|ok|okay)\s+to\s+(?:use|keep|leave|run|plug|carry\s+on)\b"
    r"|\bis\s+(?:the|my|our)\s+[a-z']{3,20}\s+(?:safe|dangerous|a\s+(?:fire\s+)?(?:risk|hazard))\b"
    r"|\bcan\s+i\s+(?:still\s+)?(?:use|keep|leave|run|plug)\s+(?:it|this|that)\b"
    r"|\bcan\s+(?:it|that|this)\s+be\s+(?:used|left|kept)\b", re.I)

# The things whose answer this reading knows: anything with a plug, a flame or water in it. The
# set is the guard as much as the match - "is it safe to keep food in" about a freezer is this
# reading's, "is it safe to take ibuprofen" is the health cards'.
A_THING_THAT_PLUGS_IN = frozenset("""
    boiler heater charger plug socket cable lead extension kettle toaster oven hob grill
    microwave fridge freezer washing machine washer tumble dryer dishwasher immersion shower
    radiator thermostat lamp light lights fan dehumidifier laptop phone mobile tablet
    hairdryer straighteners iron blanket fire chimney gas electrics wiring fuse
    """.split())

# A question about using a thing again is only this reading's when something in the thread makes
# it a safety question. A safety word in the line itself is enough ("is the kettle safe to leave
# on"); otherwise the line before has to describe a fault of a kind that could bite - cracked,
# frayed, sparking, hot, a burning smell, water where the electrics are. Without this, the shape
# "can i still use it" took turns it had no business in: "my laptop is slow" / "can i still use
# it" is the slow-laptop card's (yes, and here is what to trim), "i got a new phone" / "can i keep
# it" is about the old phone, and "my son is a football fan" / "can i leave it on" is nothing of
# the sort (round-umbrella, #8437).
A_SAFETY_WORD = re.compile(
    r"\b(?:safe|safely|unsafe|dangerous|danger|risk|risky|hazard|hazardous|fire|"
    r"electrocut\w*|shock|shocks|shocking)\b")

# How the thing was described in the line before, when the line before is what makes this a
# safety question: "the plug socket is cracked" / "can i still use it". "slow", "noisy", "old"
# and "new" are not here on purpose - those are faults an answer can work with, not fires.
A_FAULT_DESCRIBED = re.compile(
    r"\b(?:cracked|cracking|frayed|fraying|exposed|bare|sparks?|sparking|smoking|smokes|"
    r"smelt|smells?|burning|burnt|scorched|melting|melted|toasted|hot|overheat\w*|"
    r"buzzing|buzzes|fizzing|tripping|trips|dripping|drips|leaking|leaks|leak|wet|damp|"
    r"loose|live|popped|banging|loud\s+bang)\b")

# What makes a thing a stop-using-it-tonight, and what can wait for the morning.
A_SAFETY_TEST_LINES = (
    "The test with {thing} is a burning smell, sparks, or heat you would not leave the room "
    "with: any of those and switch it off at the wall and leave it until somebody has looked at "
    "it. None of them and it will keep until the morning.",
    "Three things make {thing} a no for tonight - a burning smell, sparks, or a plug or socket "
    "that is hot to the touch. Any of those, off at the wall and not again until it has been "
    "looked at. If it is only a noise or a drip, it can wait for the morning.",
    "Nothing about {thing} needs deciding tonight unless it smells of burning, or water is "
    "anywhere near the electrics: then switch it off at the wall and have it looked at. "
    "Otherwise leave it be and ring somebody in the morning.",
    "Keep it plain with {thing}: if it smells of burning or the socket is hot, off at the wall "
    "and no more of it tonight. A drip or a rattle can wait for the morning - bowl under it, "
    "nothing electrical near it.",
)

# When the bot's own last answer has already ruled, the next turn is the same ruling said once.
A_RULING_ALREADY = ("off at the wall", "unplug", "don't use it", "do not use it",
                    "stop using it", "turn it off", "switch it off", "ring 999", "call 999",
                    "get out")
# The ruling said again, and nothing else in it. Every one of these opened on the night - "Not
# tonight, no", "that does not change overnight" - because the question this reading was written
# for is the overnight one. The rule is read on every safety question, though, and a person who
# asked "is it safe to keep using it" at ten in the morning was told "Not tonight, no. A thing
# that has been switched off for a fault...": a night they had not mentioned, and a thing switched
# off that they had not switched off. The ruling is the whole of it, so the ruling is the whole of
# the reply.
A_SAFETY_ALREADY_RULED = (
    "No - the answer above still stands: it stays off until somebody has looked at it.",
    "Same answer as before: not used again until it has been checked.",
    "That has not changed: off, and looked at before it goes back on.",
)


def reply_for(clean, memory):
    """The lines for a safety question about a thing of theirs, or None.

    None wherever somebody else has the better answer: a knowledge card that names the thing the
    question is about, and a thing that is not one of the above (a body, a person, a food).
    """
    text = " ".join(str(clean or "").lower().split())
    if not text or not ASK_IF_A_THING_IS_SAFE.search(text):
        return None
    thing = _the_thing_on_the_table(text, memory)
    if not thing:
        return None
    if not (_a_safety_word(text) or _the_thing_is_described_faulty(memory, thing)):
        return None
    card = _the_answers_have_this(text, memory)
    if card and (thing in card.lower() or not _a_shrug(card)):
        return None
    if the_bot_already_ruled(memory):
        return A_SAFETY_ALREADY_RULED
    return tuple(line.format(thing="the " + thing) for line in A_SAFETY_TEST_LINES)


def _a_safety_word(clean):
    """True when the line itself asks about safety rather than only about using a thing."""
    return bool(A_SAFETY_WORD.search(str(clean or "").lower()))


def _the_thing_is_described_faulty(memory, thing):
    """True when the line before describes the thing as faulty in a way that could bite.

    The fault has to be beside the thing: "my heater smells of burning" is, "my laptop is slow"
    is not, and a fault word from an unrelated line further back is not either.
    """
    said = " ".join(str(last_user(memory) or "").lower().split())
    if not said or not thing or thing not in said:
        return False
    return bool(A_FAULT_DESCRIBED.search(said))


def _a_shrug(reply):
    """True when an answer to this line says the bot cannot answer it.

    A card that names the thing keeps the turn, and so does any answer of its own: the only reply
    this reading takes the turn from is one that sends the person off to search.
    """
    said = str(reply or "").lower()
    return any(phrase in said for phrase in (
        "i don't know enough", "i do not know enough", "beyond what i know", "rather not guess",
        "not sure about that one", "i'm not sure about that", "search should sort", "quick search",
        "search online", "better sources", "can't call that one", "cant call that one"))


def _the_thing_on_the_table(clean, memory):
    """The appliance a follow-up safety question is about, or "" when there is not one.

    Read from the line itself ("is the boiler safe to leave on") and, failing that, from the
    thing the person named in the line before ("boiler dripping water" / "is it safe to keep it
    on tonight"). The last one found is the thing the question is about: "the plug socket is
    cracked" is about the socket, and the words before it are how it is being described.
    """
    for text in (clean, last_user(memory)):
        found = [word for word in re.findall(r"[a-z']{3,20}", str(text or "").lower())
                 if word in A_THING_THAT_PLUGS_IN]
        if found:
            return found[-1]
    return ""


# The harm the ruling was for, which is what makes an answer a ruling rather than a step. Every
# how-to says "unplug it first" and many say "switch it off at the wall", so the stopping word on
# its own is not enough: the answer has to say what the stopping is for. "unplug it and wipe the
# screen with a damp microfibre" is a step, and the doubt after it is about the step; "Stop using
# it and replace it ... can shock you or start a fire" is a ruling.
A_DANGER_SAID = re.compile(
    r"\b(?:fires?|flames?|smoke|shocks?|shocking|electrocut\w*|burns?|burnt|scorch\w*|"
    r"unsafe|kills?|fatal|explodes?|explosion|catch(?:es)? fire)\b")


def the_bot_already_ruled(memory):
    """Whether the bot's own last reply told the person to stop using the thing, and why not to.

    Read by the verdict reading too, so an answer that ruled a thing unsafe is not followed by an
    all-clear ("Ordinary on its own, yes") about the same thing. The harm has to be in the same
    answer: a how-to says "unplug it first" of everything in the house.
    """
    said = str(last_bot(memory) or "").lower()
    if not any(phrase in said for phrase in A_RULING_ALREADY):
        return False
    return bool(A_DANGER_SAID.search(said))


def _the_answers_have_this(clean, memory):
    """The knowledge module's own answer to this line, or None.

    Asked with the conversation behind it, because the card for "is it safe to leave it plugged
    in" is built from the charger the line before named. A card that does not mention the thing
    on the table is not an answer to this question: the freezer in the garage reached the card
    about a car's brakes.
    """
    try:
        from ..modules import answers

        said = answers.respond(clean, copy.deepcopy(memory if isinstance(memory, dict) else {}))
    except Exception:  # noqa: BLE001 - a card that cannot be read is no card
        return None
    return said if isinstance(said, str) and said.strip() else None
