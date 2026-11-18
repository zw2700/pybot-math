"""A line that says something is coming and has not said it yet: "one more thing", "quick one".

These lines carry no subject of their own. Nothing has been asked, so there is nothing to answer,
and nothing to search for either - main answered "one more thing" with a knowledge entry about
studying ("Test yourself instead of rereading") because "one" and "thing" are words in the base,
and "another thing" with "Another thing — I'll remember that.", which files away a line that has
said nothing at all. A friend says go on. Anything more is invented: the person has not said what
the thing is.

So the whole line has to be the hand-off and nothing else. "quick one, how do i descale a
kettle" names the thing after the comma and keeps whatever answers it, and a hand-off with a
subject ("one more thing about the boiler") has something in it to go on with.

Read by the arbiter as well as by the composer: the line has no words to match, so the module
that answered last would otherwise keep the turn and reply to its own last answer. The composer
says it read this line, and the arbiter asks that before the never-repeat rule (README.md,
"Interface").
"""
import re

from . import pick

# The whole line, once tidied: a hand-off phrase, with any amount of throat-clearing in front of
# it ("oh, and one more thing actually"). Anchored at both ends, so a hand-off that goes on to
# say the thing is not this line.
_FRONT = (r"(?:(?:and|oh|ooh|ok|okay|so|right|ah|er|um|umm|hmm|sorry|also|just|plus|hey|ta|"
          r"anyway|anyways|first|then|actually|also)\b[\s,]+)*")
BACK = (r"(?:\s+(?:actually|too|as well|then|now|first|ok|okay|sorry|thanks|tho|though|"
        r"i think|i suppose|i reckon))?")
_CORE = (
    # "one more thing", "two more questions", "a couple more things"
    r"(?:one|two|three|a couple|a few|couple)(?: more| other| final| last)"
    r" (?:things?|questions?|qs?|asks?|quer(?:y|ies)|bits?|points?|ones?)"
    # "another thing", "another one", "another question"
    r"|another (?:things?|questions?|qs?|asks?|ones?|points?|quer(?:y|ies))"
    # "one last thing", "the next question", "the other thing", "one final ask"
    r"|(?:one |the |a )?(?:last|final|next|other|second) "
    r"(?:things?|questions?|qs?|asks?|ones?|bits?)"
    # "quick one", "a quick question", "quick q"
    r"|a? ?quick (?:ones?|questions?|qs?|asks?|things?|quer(?:y|ies))"
    # "a different question", "a separate one", "an unrelated thing"
    r"|(?:a |one |an )?(?:different|separate|unrelated|side) "
    r"(?:questions?|ones?|asks?|things?|quer(?:y|ies))"
    # "one thing more" - but not "something else", which answers a suggestion already made
    # ("what should i cook with mince" / "something else" wants a second recipe, not room to
    # speak), and not "a thing or two".
    r"|one thing more"
    # the two phrases that are all throat-clearing and nothing else
    r"|before i forget"
    r"|while (?:im|i am) (?:here|at it)"
)

HANDOFF = re.compile(
    "^" + _FRONT + "(?:" + _CORE + ")" + BACK + r"[\s.?!,]*$", re.IGNORECASE)

# A hand-off that names what it is about: "one more thing about the boiler", "another thing about
# the car", "one more question on my pension", "one last thing to do with the mot". These got
# "I'm listening - say more if it helps" and "Got it. Is there anything you'd like a hand with?"
# from the composer's neutral pool, which throws away the one word the person did give, and the
# search hedge is no better: nothing has been asked yet. The reply takes the subject and asks for
# the question about it, which is what the bare pool does when there is no subject to take.
ABOUT = re.compile(
    "^" + _FRONT + "(?:" + _CORE + ")" + BACK + r"[\s,:-]*(?:about|on|to do with|regarding|"
    r"around)\s+(?P<thing>(?:(?:the|my|our|your|his|her|their|its|a|an|this|that)\s+)?"
    r"[\w'-]+(?:\s+[\w'-]+){0,3})[\s.?!,]*$", re.IGNORECASE)
# A subject that only points ("one more thing about it", "about that") says no more than the bare
# hand-off did, so it takes the bare pool rather than being named back at the person.
_POINTS_AT_NOTHING = frozenset((
    "it", "that", "this", "them", "they", "us", "you", "me", "him", "her", "there", "things",
    "thing", "stuff", "everything", "nothing", "something", "anything", "it all", "the lot",
))

# A clause that is a question in its own right ("one more thing about whether i should go") is not
# a subject to say back: the pool above would answer "what about whether i should go?", which is
# the person's own question handed back to them.
_NOT_A_SUBJECT = frozenset((
    "whether", "if", "how", "what", "when", "why", "where", "who", "whom", "which", "that",
    "because", "so", "but", "and",
))

# The subject is the thing the person named, said back so they know it has landed. No line
# promises a fact about it, because nothing has been asked yet.
ABOUT_THE_THING = (
    "Go on — what about {thing}?",
    "Ask away about {thing}.",
    "{Thing} — right. What do you want to know?",
    "What about {thing}? I'm listening.",
)


def reads_as_handoff_about_a_thing(text):
    """The subject a hand-off names ("one more thing about the boiler"), or None."""
    clean = " ".join(str(text or "").lower().split())
    found = ABOUT.match(clean)
    if not found:
        return None
    thing = found.group("thing").strip(" ,.?!:-")
    if not thing or thing.split()[0] in _POINTS_AT_NOTHING:
        return None
    if thing in _POINTS_AT_NOTHING or thing.split()[0] in _NOT_A_SUBJECT:
        return None
    return thing

# Hand-offs that name a question rather than a thing ask for room to ask, and a pool that says
# "what is it?" about a question reads as if the person had been unclear.
_NAMES_A_QUESTION = re.compile(r"\b(?:question|questions|q|qs|ask|asks|query|queries)\b",
                               re.IGNORECASE)

ASK_AWAY = (
    "Ask away.",
    "Sure — what is it you want to know?",
    "Go on, I'm listening.",
    "Yes, ask away — I'm here.",
)

GO_ON = (
    "Go on — what is it?",
    "Sure, go ahead.",
    "I'm listening — tell me.",
    "Yes, what else?",
    "Go ahead, I'm here.",
)


def reads_as_handoff(text):
    """Is the whole line a hand-off with nothing said after it?"""
    return bool(HANDOFF.match(" ".join(str(text or "").lower().split())))


def takes_as_it_comes(text, memory):
    """Read by the arbiter: a hand-off has no words to match, so this module answers it.

    It says yes to every bare hand-off and no to every line that goes on to say something, and it
    says yes to a hand-off that names its subject, which the composer answers by taking it.
    """
    return reads_as_handoff(text) or bool(reads_as_handoff_about_a_thing(text))


def reply_for(text, memory):
    """The reply to a hand-off, or None when the line says something after it."""
    clean = " ".join(str(text or "").lower().split())
    thing = reads_as_handoff_about_a_thing(clean)
    if thing:
        lines = tuple(line.format(thing=thing, Thing=thing[0].upper() + thing[1:])
                      for line in ABOUT_THE_THING)
        return pick(lines, memory, clean)
    if not HANDOFF.match(clean):
        return None
    return pick(ASK_AWAY if _NAMES_A_QUESTION.search(clean) else GO_ON, memory, clean)
