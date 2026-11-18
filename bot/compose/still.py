"""A nudge after an answer is not the end of the conversation.

A person who says "and" or "go on" after being told what to do is still in it. On main that line
is read as the conversation closing, or as an echo of the answer's first sentence:

    my knee is sore when i run / and            "Alright then - good luck with it."
    my knee is sore when i run / and            "Thanks for telling me - I'm here if you want..."
    how do i clean my oven / and then           "That's the one: Make a paste of bicarbonate..."
    i want to start running / and               "Alright then - good luck with it."

The first two close a conversation the person is still in, and the third hands back the sentence
they have just read. This module does not hand anything back: an answer that is already in front of
them has been read, so repeating it as "the other part" is the bot talking to itself. What a nudge
gets instead is the honest end of the answer, with the offer that is missing from a goodbye - the
person can go back over any part of it.

So the three faults are answered with one rule: **nothing is ever repeated, and the turn is not
closed.** That is why the reading here is small. It has to know a nudge from a line with a subject
("and the radiator" is a question about the radiator), and it has to know that there was an answer
behind it that gave something to do; everything else stands down and the floor answers as it did
before.

The wording lives next to the reading in `bot/compose/still.py`, and `bot/modules/nudge.py` gives
it a band of its own, because a nudge has to be answered before the chat module's goodbye.
"""
import re

from . import fallback, verdict
from ..memory import another

# What a nudge is made of once a conversation's own words are taken out of it: a word that only
# says "go on", with any "ok"/"so" in front of it, and nothing else in the line.
# "what else", "anything else" and "more" are not here: #3409 (`asks_for_more`) owns them, and one
# line with two owners is settled by band rather than by who is better at it.
# "go on", "go ahead", "carry on" and "keep going" are not here either: after an answer with no
# rest the floor already has an honest end line for them ("I have given you all of it. If you say
# what is still not working I'll take it from there"), and this module's own end line was the one
# row a whole-deck comparison had moving the wrong way. A line the bot already answers well is not
# a line to claim.
#
# "next", "what next" and "then what" are not here for a sharper reason: they are not only a nudge.
# After a how-to answer the composer hands out the answer's next step - `how do i cook rice / next`
# gets "Start with this: Rinse it until the water runs clear ...", which is a real step the answer
# had not given yet, and after a joke "what next" asks for another joke. Both are better than any
# end line, and both were lost while this module claimed those four words.
NUDGES = frozenset((
    "and", "then", "and then", "the rest", "and the rest",
))
# The words that sit in front of a nudge without being one, so "ok and then" is still a nudge.
LEADING = frozenset(("ok", "okay", "right", "well", "so", "yes", "yeah", "and", "but", "then",
                     "alright", "cool", "great", "thanks", "ta", "ah", "oh"))
# A line this short that ends on a question is the floor asking the person back, not an answer.
SHORT_BACK = 120
# An answer that opens by taking in a hard thing ("Sorry to hear that. A walk and someone to talk
# to ...") is not a list that is finished with: "that's as far as I can take it" is a cold thing to
# say to a person who has just said they feel flat, and a nod is what the turn after one gets.
SYMPATHY_OPEN = ("sorry to hear", "so sorry", "i'm sorry", "im sorry", "that sounds", "awful",
                 "that's tough", "thats tough", "that's such", "thats such", "how awful")
# The honest end of an answer, with the way back in that a goodbye does not have. Nothing here
# repeats a word of the answer: the answer is on the screen, and reading it out again is the fault
# this module exists to remove.
STILL_END = (
    "That's the lot of it from me on that one. Say if you want to go back over any part of it.",
    "That's everything I have on it, and it is all above. Which bit do you want to unpick?",
    "That's the whole of it as far as I know. Is there a part of it you are unsure about?",
    "Nothing more from me on that one - it is all said. Anything in it worth going over?",
    "That's as far as I can take it. Say the word and we will go back over a piece of it.",
)


# A nudge after a condolence is not a request for the rest of a list: the answer above was never a
# list, and closing the turn on it - "that's the lot of it" - is a cold way to leave a person who
# has just said the worst thing in their week. The line that fits is the invitation, and it says
# nothing about the answer at all. Two pools, because "say more about them" is right after a death
# and wrong after a bad day.
STILL_AFTER_A_LOSS = (
    "No rush on any of it. If you want to say more about them, I am here for that.",
    "Take your time - nothing here needs finishing. Say more about them whenever you like.",
    "That's all from me, and there is no hurry. I am still here if you want to talk about them.",
)
STILL_AFTER_A_HARD_DAY = (
    "No rush with it. I am still here if you want to say more about how things are.",
    "Nothing to finish here - take your time. Say more whenever you want to.",
    "That's all from me for now, and no hurry at all. I am here if you want to keep going.",
)
# The modules that answered a death, and the two that answered an emergency. An emergency is not
# an invitation to talk it through - the line there is the one that keeps somebody safe.
SORROW_MODULES = ("loss", "grief")
HARD_MODULES = ("safety", "urgent")


def _flat(text):
    return " ".join(str(text or "").lower().replace("\u2019", "'").split())


def _is_a_nudge(flat):
    """True for a line that only says "go on", with any "ok"/"so" in front of it taken off."""
    if not flat or len(flat.split()) > 4:
        return False
    words = [w.strip(".,!?;:-") for w in flat.split()]
    if " ".join(w for w in words if w) in NUDGES:
        return True  # "then what" is whole before any "then" is taken off the front
    while len(words) > 1 and words[0] in LEADING:
        words = words[1:]
    words = [w for w in words if w]
    return " ".join(words) in NUDGES


def _ours(said):
    """True for a line this module wrote: the floor's end line is not the answer."""
    low = str(said or "").lower()
    for template in STILL_END:
        head = template.split("{")[0].strip().lower()
        if head and low.startswith(head):
            return True
    return False


def _answer_behind(memory):
    """Whether the last thing the bot said gave the person something to do, and what it was.

    The walk back goes over this module's own end lines, nods and sign-offs, and stops at a
    condolence or an emergency: "that's the lot of it" is not a thing to say after either, and a
    line like that is not a list of steps to be finished with. A question the bot asked is not an
    answer either - a nudge after it is a person thinking, not a person asking for more of a list.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    # A hedge is not an answer: "should i see someone" on its own is met with "Can't call that one
    # for you, sorry", and "that's as far as I can take it" claims knowledge the bot never had.
    # The rule is the one the rest of the composer already uses for the same thing.
    try:
        if fallback._hedged_recently(memory):
            return ""
    except Exception:  # noqa: BLE001 - a reading that fails stands down
        return ""
    walked = list(reversed(turns or []))
    for index, turn in enumerate(walked):
        if not isinstance(turn, dict):
            return ""
        if turn.get("module") in verdict.UNREADABLE:
            return ""
        # The floor's own line is not an answer. "should i see someone" on its own is met with
        # "Can't call that one for you, sorry", and an end line after it claims knowledge the bot
        # never had. The greeting band is the floor by construction, so the name is the test.
        #
        # But the floor is also where the composer says its own readings - a "why" answer, the
        # rest of an answer - and those are answers, so the name alone is too broad. A floor line
        # with an answer behind it continues that answer, and a nudge goes on with it: "my boiler
        # is noisy / why / and" was told "Sounds good." because the walk stopped one turn short of
        # the boiler card (cream-flag's #5203 and this lane, on main 7be1764e). A goodbye with
        # nothing behind it still stops the walk.
        said = turn.get("bot")
        if not isinstance(said, str) or not said.strip() or _ours(said):
            continue
        if turn.get("module") == "greeting":
            # A floor line that ends on a question is the composer asking the person back, and a
            # nudge after it is a shrug, not a request for the rest: "my laptop is slow / why"
            # was met with "I'd be guessing at the reason ... Which part of that do you want the
            # why for?" and "and" after it is not owed an end line.
            if said.strip().endswith("?"):
                return ""
            if not _continues_an_answer(walked[index + 1:]):
                return ""
            continue
        # An answer that ends by asking the person something has not finished, however long it
        # is: "im worried about my mum" was answered "... What's the happening with her?" and a
        # nudge after that question was told there was nothing more. Whoever asked does not get to
        # disown the question, so the turn above is not an answer and this module stands down.
        if said.strip().endswith("?"):
            return ""
        if _flat(said).startswith(SYMPATHY_OPEN):
            return ""
        # The other half of an answer handed back is an answer: `my knee hurts when i run` /
        # `and then` gave "If you only do one thing from that answer: Ice after a run ...", and a
        # nudge after that is a person asking for more of the same answer, so this module has
        # something to finish. Without this the turn above was read as no answer at all and the
        # second ask was left to the chat module repeating the answer's opening sentence.
        if turn.get("module") == "memory_store" and _a_hand_back(said):
            return said
        # An answer that gave something to do, and also one that gave a list of things to watch,
        # read or try: both are finished with "that's the lot of it", and a nudge after a list is
        # still a person asking for more of it. A one-line nod is neither.
        return said if (verdict._steps(said) or len(re.split(r"(?<=[.!?]) ", said.strip())) > 1) \
            else ""
    return ""


def _continues_an_answer(behind):
    """True when one of the turns behind this floor line is an answer with something in it.

    The raw test, not `_answer_behind`: this asks only whether the floor line was spoken for an
    answer at all, so a question the bot asked and a sympathy opener are answers here - the walk
    carries on and `_answer_behind` applies its own tests to whichever line it lands on.
    """
    for turn in behind:
        if not isinstance(turn, dict) or turn.get("module") in ("greeting",) + tuple(verdict.UNREADABLE):
            continue
        said = turn.get("bot")
        if isinstance(said, str) and len(said.split()) >= 5:
            return True
    return False


def _a_hand_back(said):
    """True when the memory store's line is part of an answer rather than a nod of its own.

    The store writes both kinds: "If you only do one thing from that answer: Ice after a run and
    run on softer ground..." hands over a sentence of the answer, while "Got it - they're 4 and 7"
    is a nod. Only the first is something a nudge can be the end of, and the test is the length it
    hands over rather than the lead in front of it, because the lead-in list is the store's to
    change and this module should not keep a copy of it.
    """
    text = str(said or "")
    try:
        from ..memory import repeat
        parts = [part.strip() for part in repeat.SENTENCE.split(text.strip()) if part.strip()]
    except Exception:  # noqa: BLE001 - a reading that fails treats the line as a nod
        return False
    return bool(parts) and len(parts[0].split()) >= 6


def _sorrow_behind(memory):
    """Whether the last thing the bot said was a condolence, and which kind: "loss", "hard" or "".

    Read off the turn itself and not off the answer's worth: a death answered by the loss module,
    or any answer that opens by taking the hard thing in. An emergency is neither - "say more
    whenever you want to" is the wrong line while somebody is waiting for an ambulance.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return ""
    try:
        if fallback._hedged_recently(memory):
            return ""
    except Exception:  # noqa: BLE001 - a reading that fails stands down
        return ""
    last = turns[-1]
    if not isinstance(last, dict):
        return ""
    module = last.get("module")
    if module in HARD_MODULES:
        return ""
    if module in SORROW_MODULES:
        return "loss"
    said = last.get("bot")
    if isinstance(said, str) and _flat(said).startswith(SYMPATHY_OPEN):
        return "hard"
    return ""


def _the_rest_is_anothers(clean, memory=None):
    """True when the module that owns the rest of an answer reads this line as asking for it.

    `bot/memory/another.py` is the module that hands back an answer's second half, and it reads a
    carry-on the same way this one does. Where it speaks it is the better answer - it gives the
    rest of the answer where this module can only say there is no rest - so it keeps the line, and
    the reading is asked for at call time rather than copied: whatever that module claims
    tomorrow, this one stands down on, with no second list here to keep in step.

    What is asked is whether it *has* the rest, not whether it reads the line as a carry-on: a
    condolence has no second half in it, and a line that is read as a carry-on anyway is not a
    reason to give up the turn. The loss threads are nudge's own sign-off ("That's all from me,
    and there is no hurry") either way, which is the pool this module leaves to it.
    """
    try:
        return another.other_option(clean, memory) is not None
    except Exception:  # noqa: BLE001 - a reading that fails leaves the line here
        return False


def takes_as_it_comes(text, memory):
    """Only on a nudge with an answer behind it: the line is read whole, and nowhere else."""
    try:
        if _the_rest_is_anothers(text, memory):
            return False
        return bool(_is_a_nudge(_flat(text)) and (_answer_behind(memory) or _sorrow_behind(memory)))
    except Exception:  # noqa: BLE001 - a hook that raises claims nothing
        return False


def reply_for(clean, memory):
    """The honest end of the answer for a nudge that names nothing of its own. Else None."""
    try:
        if not takes_as_it_comes(clean, memory):
            return None
        sorrow = _sorrow_behind(memory)
        pool = {"loss": STILL_AFTER_A_LOSS, "hard": STILL_AFTER_A_HARD_DAY}.get(sorrow, STILL_END)
        return verdict._say(pool, memory, _flat(clean))
    except Exception:  # noqa: BLE001 - a reading that fails answers the line as it did before
        return None
