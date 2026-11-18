"""A named thing they tried after advice, said back as a question about whether it helped.

"my back hurts" is answered with what usually helps, and the next line - "i tried a hot bath" - is
not news and not a new question: it is where they are with the advice, and the thing a friend says
to it is whether it did anything. The bot said "Good to hear. What was the best bit?", which reads a
remedy that has just been tried as a good time they had.

This reader answers the line only when all four of these hold, so nothing else is taken:

- the line is an attempt at something, said as a person does ("i tried", "ive just tried", "i took",
  "i used", "we gave it a go"), and it names the thing ("a hot bath", "some paracetamol");
- it carries no verdict of its own ("it didnt help", "no better", "that helped", "it made it
  worse"), because a report on the answer is `bot/memory/tried.py`'s line;
- the thing is a thing and not a pronoun - "i tried that" is the answer's own steps, not this;
- the turn before was advice (`answers` or `safety`), and the chat has a problem in it, so a happy
  "i tried the new thai place" after a where-to-eat answer is left where it was.

Everything else is passed on, unchanged, to the modules that were going to answer it.
"""
import random
import re

# An attempt at one named thing. The object is read from the line, and the rest of the line is
# kept for the verdict read below, so "i tried a hot bath and it didnt help" is not this reader's.
ATTEMPT = re.compile(
    r"^\W*(?:(?:and|but|so|oh|ok|okay|well|right|alright)\s+)?"
    r"(?:i|i've|ive|i'd|we|we've|weve)\s*"
    r"(?:have\s+|had\s+|just\s+|already\s+|also\s+|finally\s+)?"
    r"(?P<verb>tried|took|used|gave|been using|been trying)\s+(?P<thing>.+)$")

# A thing a person says they tried, capped so a whole sentence of news is not read as one.
A_THING_LEADS = re.compile(
    r"^(?:a|an|the|some|my|his|her|their|our|that|this|one|two|three)\b", re.I)

# The words that make the line a report on the advice rather than an attempt: with one of these
# the turn belongs to `bot/memory/tried.py` (it worked, it did not, it made things worse).
VERDICT = re.compile(
    r"\b(?:did\s?n'?t|does\s?n'?t|not|no|never|helped|helps|worked|works|better|worse|"
    r"relief|eased|eases|nothing|useless|pointless|yet|again|still)\b", re.I)

# Pointing words are the answer's own steps, and the reader for those lines already exists.
POINTING = frozenset("""that this it them those these everything all anything something
nothing""".split())

# A problem in the chat is what advice is advice about: without one, "i tried" is a new experience
# ("i tried the new thai place") and the reply it had is the right one.
A_PROBLEM = frozenset("""hurt hurts hurting hurtful pain painful ache aches aching achy achey sore
ill sick illness unwell cough coughing cold flu headache migraine fever temperature back knee
shoulder neck ankle wrist hip throat stomach belly tooth toothache ear earache rash itch itchy burn
burnt sprain sprained stiff stiffness swelling swollen dizzy faint sleep
sleeping slept insomnia wake waking wakes sneeze sneezing blocked stuffy running congestion
bleeding bleed cut bruise bruised lump dizzy nausea sick vomit diarrhoea constipated constipation heartburn
reflux bloat bloated cramp cramps period contractions
dripping drips leaking leaks leaked leak broken broke cracked squeaks squeaking squeak clogged
blocked banging rattling stuck jammed seized mould mildew damp stains stained smell smells
wont won'ts starts start starting
freezing freezes frozen slow slowly crashing crashes crashed glitching lagging laggy dropping
drops disconnects restart reboots overheating""".split())

ADVICE_MODULES = frozenset(("answers", "safety"))

# What a friend says when they hear the thing was tried: the question is whether it did anything,
# and the thing is named so the reply is about their line and not about remedies in general.
ASK_IF_IT_HELPED = (
    "Did the {thing} take the edge off, or nothing?",
    "{Thing} - did that do anything?",
    "And did the {thing} make a difference?",
    "{Thing} - any help at all?",
    "How did the {thing} go - anything, or no difference?",
)

LEADS = re.compile(
    r"^(?:and|but|so|oh|ok|okay|well|right|alright)\s+", re.I)

# Words that are not the thing even when they follow the verb, so the sentence reads.
NOT_THE_THING = frozenset("""to for at in on with about of it that this""".split())


def reply_for(text, memory):
    """The question about the thing they tried, or "" when this is not that line."""
    said = " ".join(str(text or "").lower().split())
    if not said:
        return ""
    match = ATTEMPT.match(said)
    if not match:
        return ""
    thing = _the_thing(match.group("thing"), match.group("verb"))
    if not thing:
        return ""
    # The verdict words are read after the thing, so "i tried the freezer" keeps the thing and a
    # "it didnt help" on the end of the line goes to the module that hands over the next step.
    if VERDICT.search(match.group("thing")[len(thing):] or ""):
        return ""
    if not _a_problem_was_spoken_of(memory) or not _advice_was_given(memory):
        return ""
    options = [_fill(template, thing) for template in ASK_IF_IT_HELPED]
    return _fresh(options, memory)


def _the_thing(rest, verb):
    """The named thing they tried, without the article, as the words a sentence can carry."""
    said = str(rest or "").lower()
    # The thing ends where the sentence turns: "a hot bath and it didnt help" is an attempt and a
    # verdict, and the verdict is the other module's line.
    said = re.split(r"\b(?:but|so|then|though|because|again|twice|afterwards)\b", said)[0]
    said = re.split(r"\band\b(?=\s+(?:it|its|it's|they|i|we|now|still|nothing|didnt|doesnt|"
                    r"no\b|the\s+\w+\s+(?:did|helped|worked)))", said)[0]
    words = re.findall(r"[a-z0-9']+", said)
    if not words or words[0] in POINTING or words[0] in NOT_THE_THING or words[0] == "to":
        return ""
    # "we gave it a go" names nothing new; "we gave the ice pack a go" does.
    if verb == "gave":
        if words[-2:] != ["a", "go"] and words[-2:] != ["a", "try"]:
            return ""
        words = words[:-2]
    words = words[:5]
    # Only the article and the possessive come off the end; a preposition does not, because it can
    # be half of the thing ("turning it off and on").
    while words and words[-1] in ("a", "an", "the", "some", "my", "our", "their"):
        words.pop()
    while words and words[0] in ("a", "an", "the", "some", "my", "our", "their", "his", "her",
                                 "of", "that", "this"):
        if len(words) < 2:
            return ""
        words = words[1:]
    if words and words[0] in ("of",):
        words = words[1:]
    return " ".join(words)


def _advice_was_given(memory):
    """Whether the chat holds an answer for them to be partway through.

    Read over the last few turns, not just the one before: "i tried a hot bath" then "i tried a
    heat pad" is a second attempt at the same advice, and the turn in between is this module's own
    question, which is not advice of its own.
    """
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)] \
        if isinstance(memory, dict) else []
    for turn in turns[-4:][::-1]:
        module = str(turn.get("module") or "")
        if module in ADVICE_MODULES:
            return True
        # A module that does not say which part answered still gave advice when its reply carries
        # the advice a person acts on: "try", "keep", "see a GP" and so on.
        reply = str(turn.get("bot") or "").strip()
        if re.search(r"\b(?:try|trying|keep|rest|ice|see (?:a|your) (?:gp|doctor))\b",
                     reply.lower()):
            return True
        # A question about the thing in their hands is the chat being with them on it, and the
        # attempt is the answer to it: "my laptop keeps freezing" / "how long has it been like
        # that?" / "i tried restarting it".
        if reply.endswith("?"):
            return True
    return False


def _a_problem_was_spoken_of(memory):
    """Whether the last few turns have a problem in them, which is what an attempt is at.

    Read over the last few turns rather than all of them: an attempt three turns after a problem
    that has been answered and moved on from is a new experience ("i tried the thai place"), and
    the reply it already had is the right one.
    """
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)] \
        if isinstance(memory, dict) else []
    words = set()
    for turn in turns[-3:]:
        words.update(re.findall(r"[a-z']+", str(turn.get("user") or "").lower()))
    return bool(words & A_PROBLEM)


def _fill(template, thing):
    """The template with the thing in it, capitalised where it opens the sentence."""
    return template.format(thing=thing, Thing=thing[:1].upper() + thing[1:])


def _fresh(options, memory):
    """An option that has not just been said, so the same question does not come twice."""
    said = " ".join(str(turn.get("bot") or "") for turn in (memory.get("turns") or [])
                    if isinstance(turn, dict)) if isinstance(memory, dict) else ""
    unseen = [option for option in options if option.lower() not in said.lower()]
    pool = unseen or list(options)
    return random.Random(len(memory.get("turns") or []) if isinstance(memory, dict) else 0).choice(pool)
