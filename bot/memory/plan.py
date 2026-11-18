"""The order in an answer, kept in the chat, so "what next" moves on instead of starting again.

An answer that gives a sequence ("turn the water off at the isolating valve, take the handle off,
and take the old part to a hardware shop") has an order in it, and a person working through it says
"what next" when they have done one step. The chat had no memory of the order, so on main the tap
chat went:

    my bathroom tap drips
    what next   -> Start with this: Turn the water off at the isolating valve under the sink, take
                   the handle off, and take the old part to a hardware shop to match it.
    and then    -> That's as far as I can take it. Say the word and we will go back over a piece.
    what next   -> From just now: Turn the water off at the isolating valve under the sink...

The first step again, then a goodbye closing a job the person is halfway through, then the whole
card back. Two things are the store's: the step handed over is never remembered, so there is no
next one to give; and no module knows the answer has an order at all, so the nudge module decides
it has run out. This module keeps the steps of the answer in hand and the step the chat has
reached, and answers the bare asks that want the following one.

What it does not do: write a step of its own. Every line here is a step the answer already gave, in
the answer's own words, in the answer's own order. The reading is `repeat._the_steps`, the same one
the "what else" readers use, so a sentence this module hands over is a sentence another reader in
the package would have called a step too.

The cursor is kept under `memory["steps"]` - the key the conversation lane's doc lists - as the
answer it belongs to and how many of its steps have been handed over. It is not `memory["plan"]`
because the person's own plan is `user["plan"]`, and one name for two things is how a store starts
answering about the wrong one. It starts again when the
answer changes, because a step count from the last answer is about a different job.
"""
import copy
import re

from ..compose import pick
from . import repeat

# The asks that mean "the next one" and nothing else. Each has to be the whole line, so a line that
# adds anything of its own is a question of its own and every other module keeps it: "and then what
# about the washer" names a thing, and "what next for the boiler" names a subject.
CARRY_ON = re.compile(
    r"^(?:(?:ok|okay|right|so|yeah|yes|alright|and|then|well|ah)\s+)*"
    r"(?:and\s+then|then\s+what|what\s+next|what\s+now|next|and\s+after\s+that|after\s+that|"
    r"and\s+next|go\s+on|carry\s+on|keep\s+going)\s*[.?!]*$", re.I)

# The first step is not the next one: nothing of the answer has been done yet, so the opening says
# where to begin rather than carrying on from a step that has not happened.
FIRST_LEADS = (
    "Start with this: {step}.",
    "Begin here: {step}.",
    "The thing to do first: {step}.",
    "Do this bit first: {step}.",
)

# A first step that is the answer's ingredient list ("500g strong white flour, 7g dried yeast, 10g
# salt and 350ml warm water, kneaded for 10 minutes") says what goes in and what is done with it, so
# "Start with this: 500g strong white flour" reads as though a weight were something to do. The frame
# names the mix instead.
AMOUNTS_LEADS = (
    "First up: {step}.",
    "Begin with the mix: {step}.",
    "Start with what goes in: {step}.",
)

# A step that already opens on the instruction ("Start with run-walk: one minute of easy jogging,
# two minutes of walking") needs no frame of its own: "Start with this: Start with run-walk" says the
# same thing twice. The answer's own opening is the frame then, and the step is handed over bare.
_OPENS_ON_THE_INSTRUCTION = re.compile(
    r"^(?:start(?:\s+(?:with|by|off))?|begin(?:\s+(?:with|by))?|first(?:ly)?|to\s+start|"
    r"the\s+first\s+thing)\b(?:[,:]|\s)", re.I)

# Said after the first step, once: how many there are in all. It is the one thing the person needs
# before they start that the answer does not make easy to count ("ask the ward three things today
# ... take in their glasses ... check the visiting times"), and it is worth a sentence of its own
# for a plainer reason as well - a long first step handed over behind a frame is the answer's own
# words, and the arbiter (rightly) passes over a reply that is the last answer again with a nod in
# front. Naming the count gives the line something of its own to say.
# The count is the bot's own reading of the answer, never a claim about what the answer holds: the
# step reader passes a sentence over when it opens on a participle or a condition ("Leaving the door
# and drawer open between washes is what stops the smell coming back"), and "there are two steps in
# all" was then said over an answer with a third step in it (steward-merry-zebra, #8087). "I make it
# two steps" is true of the reading either way.
_COUNTS = {2: "I make it two steps.", 3: "I make it three steps.",
           4: "I make it four steps.", 5: "I make it five steps."}

# How the step after that is introduced. Each says where the step sits rather than what it is ("the
# next bit", "once that is done"), so it is read as the answer going on and not as a new idea: a
# friend working through the same job says "then take the handle off", never "here is a thought".
LEADS = (
    "Next: {step}.",
    "Then: {step}.",
    "The next bit: {step}.",
    "Once that is done: {step}.",
    "The step after that: {step}.",
)

# Said when every step of the answer has been handed over. It names the end of the answer rather
# than where the person is, because the bot does not know how far they have got: "you have all of
# that answer now" is true of somebody who has started and somebody who has not, and asking which
# bit they are on is the one thing that lets the next reply be about their step and not the first.
DONE = (
    "There is nothing after that bit that I can pick out. The last of it is: {step}. Where have "
    "you got to?",
    "That is the last step I can pick out of it: {step}. Say where you are and I'll help with the "
    "rest.",
    "I have nothing more to hand you after: {step}. Tell me which bit you are on.",
)

# And the same again when they ask once more. An answer that has run out is the one case where
# saying so is the whole reply: the person asked for the next step and there is not one, and gluing
# a frame onto the sentence just given ("Of all of that, this is the bit I would not skip: tell me
# how it goes") is the same fault this module fixes, from the other end.
FINISHED = (
    "That is every step I can pick out of it - nothing left of what I can hand you. Tell me how it "
    "went.",
    "There is nothing after that I can pick out. Say what happened and we will go from there.",
    "Nothing more I can pull out of that answer. How did it go?",
)

# Answers that are not a job to work through, however many sentences open on a verb. A condolence
# card ("let people help you") and an emergency line are read by a person in a state, not with a
# spanner in hand: "what next" there is not asking for the second step of anything, and the warm
# short answer they already get is the right one.
NOT_A_JOB = ("loss", "grief", "safety")

# How far back a plan is still the plan. A step count from four turns ago is about a job the chat
# has left; the answer in hand is then something else and starts its own. Three turns covers the
# one in between: "my bathroom tap drips" / "what next" / "ive already turned the water off".
WHILE_IT_LASTS = 3

# The words that hold a sentence together rather than naming the thing to be done. "turn the water
# off" and "ive already turned the water off" share "the" and "off" and are not the same step
# ("take the handle off" shares "off" with it too); "water" and "handle" are what say which step
# somebody means.
_NOT_THE_THING = {"take", "have", "with", "that", "this", "what", "when", "them", "they", "your",
                  "from", "into", "just", "like", "some", "then", "than", "also", "once", "done",
                  "make", "over", "will", "back", "again", "away", "each", "every", "about",
                  "after", "before", "under", "while", "there", "here", "been", "being"}


# A line that says the person has already had a go at something. The bare "i tried that" is read by
# `repeat`'s tried pools; this reads the line that names what was tried.
_HAD_A_GO = re.compile(r"\b(?:tried|trying|already|gave it|had a go|no luck|used)\b", re.I)


def _the_thing_named(text):
    """The words in a line that name a thing to be done, without the grammar around them."""
    return {word for word in re.findall(r"[a-z']+", str(text or "").lower())
            if len(word) > 3 and word not in _NOT_THE_THING}


def _tried(step, memory):
    """True when a line just before this one reports having done this very thing already.

    `repeat._they_say_they_tried` reads the same reports but counts any two shared words, and "the"
    and "off" are two: "ive already turned the water off" made it skip "take the handle off" as
    done. Here only the words that name the thing count, so a step is skipped when the person named
    it and not when the two sentences share their grammar.
    """
    mine = _the_thing_named(step)
    if not mine:
        return False
    for turn in (memory.get("turns") or [])[-3:]:
        if not isinstance(turn, dict):
            continue
        line = str(turn.get("user") or "")
        if not _HAD_A_GO.search(line):
            continue
        if mine & _the_thing_named(line):
            return True
    return False


def the_last_answer(memory):
    """The bot's last line in this chat, or "" when there is none."""
    for turn in reversed((memory or {}).get("turns") or []):
        if isinstance(turn, dict) and turn.get("bot"):
            return str(turn["bot"])
    return ""


def the_answer_in_hand(memory):
    """The whole answer the last line was a step of, or "" when the last line is not one of its
    steps.

    A step handed over is one sentence of the answer ("Start with this: Turn the water off at the
    isolating valve under the sink. There are three steps in all."), so a module that reads the
    bot's last line to find what the answer says next sees an answer with nothing after it:
    "ive already turned the water off" after that line found no step left and asked how it went,
    where the answer still had two more. The plan keeps the whole answer, so this hands it back
    and the readers of the last answer (bot/memory/already.py) read the answer, not one step of it.
    """
    plan = (memory or {}).get("steps") if isinstance(memory, dict) else None
    if not isinstance(plan, dict):
        return ""
    answer = str(plan.get("answer") or "").strip()
    if not answer:
        return ""
    last = " ".join(the_last_answer(memory).split()).strip()
    if not last:
        return ""
    if last == " ".join(str(plan.get("said") or "").split()).strip():
        return answer
    return answer if _our_own_line(last, plan) else ""


def _module_of_last(memory):
    """The module that answered the last line, or "" when the chat has not recorded one."""
    for turn in reversed((memory or {}).get("turns") or []):
        if isinstance(turn, dict) and turn.get("bot"):
            return str(turn.get("module") or "")
    return ""


def _last_user(memory):
    """The person's last line in this chat, or "" when there is none."""
    for turn in reversed((memory or {}).get("turns") or []):
        if isinstance(turn, dict) and turn.get("user"):
            return str(turn["user"])
    return ""


def _a_cut_at_a_colon(step):
    """A step cut off at a colon with a fragment after it is the step above the colon.

    "Cut the distance and the speed for a week or two: most running knee" is how the shared reader
    splits "Cut the distance and the speed for a week or two: most running knee pain settles in a
    few weeks." - the sentence after the colon is the reason, and its subject was taken for the
    next instruction. What is above the colon is a step of its own and a friend hands that over;
    what is below it is half a sentence.
    """
    head, sep, tail = step.partition(": ")
    if sep and len(tail.split()) < 5:
        return head.strip()
    return step


def steps_of(answer):
    """The instructions in an answer, in the order it gives them, and only when there are two.

    One instruction is not a sequence: "put a hot water bottle on it" has nothing after it, and a
    "what next" after that answer wants more of the thinking, not a second step that is not there.
    Returning [] leaves those turns to the readers that already answer them.
    """
    steps = [step for step in (_a_cut_at_a_colon(step) for step in repeat._the_steps(answer))
             if step]
    steps = _the_amounts_first(answer, steps)
    if len(steps) < 2:
        return []
    return steps


# A weight or a volume, which is what an ingredient list is made of.
AMOUNTS = re.compile(r"\b\d+(?:\.\d+)?\s*(?:g|kg|ml|l|oz|lb|tsp|tbsp|teaspoons?|tablespoons?)\b",
                     re.I)


def _the_amounts_first(answer, steps):
    """An answer that opens with what goes in has its first piece of work in that sentence.

    "500g strong white flour, 7g dried yeast, 10g salt and 350ml warm water, kneaded for 10 minutes
    until smooth and stretched. Leave it somewhere warm for an hour..." is the bread answer, and the
    shared reader passes the first sentence over: it opens on the amounts rather than on a verb. A
    person halfway through the loaf who says "what next" then got "Leave it somewhere warm", and
    the dough was never made. The sentence is the answer's own words and its own first step, so it goes
    in front, and only when the reader did not already take a step from it.
    """
    first = repeat.SENTENCE.split(str(answer or "").strip())[0].strip()
    if not first or len(AMOUNTS.findall(first)) < 2:
        return steps
    if not re.search(r"\b[a-z]{3,}ed\b", first.lower()):
        return steps  # a list of what the answer talks about, with nothing yet done with it
    if steps and steps[0].lower()[:40] in first.lower():
        return steps  # the reader's first step is this sentence already
    return [first.rstrip(".")] + list(steps)


def _words(text):
    """The words worth comparing two sentences on: short ones are the grammar, not the subject."""
    return {word for word in re.findall(r"[a-z']+", str(text or "").lower()) if len(word) > 3}


def _stems(text):
    """Words for comparing two lines on their subject: the endings are the grammar, not the thing.

    "ive already turned the water off" and "turn the water off at the isolating valve" are about the
    same valve, and only a stem makes "turned" and "turn" the same word. Four letters and up:
    "the", "and" and "off" are in every answer, and a shared "the" would make any two lines look
    like the same job.
    """
    return {word[:5] for word in re.findall(r"[a-z']{4,}", str(text or "").lower())}


def _the_same_job(answer, plan):
    """True when the last thing the bot said is still about the steps in hand.

    Between two asks the chat can say something else about the same job: "i tried the plunger" is
    answered with the later part of the answer, and that line has no sequence of its own, so a
    reader that only looked at the answer in hand would start the whole thing again. Overlap is
    what tells the two apart - a job's later part shares the words of its steps, and a reply about
    something else shares none of them.
    """
    said = _words(answer)
    if not said:
        return False
    for step in plan.get("steps") or []:
        if _words(step) & said:
            return True
    return False


def _the_same_topic(memory, plan):
    """True while the chat is still on the subject the steps belong to.

    Between two asks the bot can answer a line of its own about the same job - "ive already turned
    the water off" is answered "Then that's the first thing done" - and that answer shares none of
    the words of the steps. What the person said about the job is what says the steps in hand are
    still the steps: a chat that has moved on to the boiler shares nothing with the tap, and the
    tap's order is not its order.
    """
    here = _stems(_last_user(memory)) | _stems(the_last_answer(memory))
    if not here:
        return False
    about = set()
    for step in plan.get("steps") or []:
        about |= _stems(step)
    topic = plan.get("topic")
    about |= _stems(topic.get("text") if isinstance(topic, dict) else "")
    return bool(here & about)


def _said_in(answer, plan):
    """How far into the steps the last bot line got, so a step it already said is not said again."""
    said = _words(answer)
    if not said:
        return 0
    reached = 0
    for at, step in enumerate(plan.get("steps") or []):
        if _words(step) & said:
            reached = at + 1
    return reached


def _our_own_line(answer, plan):
    """True when the last thing the bot said is a step this module handed over.

    The step handed over becomes the bot's last line, so on the next turn the answer in hand *is*
    that step and it has no sequence in it. Without this the cursor would be thrown away after
    every step and the chat would start the answer again - which is the fault this module exists
    to fix, arrived at from the other side.
    """
    said = " ".join(str(answer or "").split()).strip()
    if not said:
        return False
    for step in plan.get("steps") or []:
        flat = " ".join(step.split())
        if flat and flat.lower() in said.lower():
            return True
    return False


def _plan_for(memory):
    """The steps in hand and the step the chat has reached, made fresh when the answer changes."""
    answer = the_last_answer(memory)
    plan = memory.get("steps") if isinstance(memory, dict) else None
    if isinstance(plan, dict) and plan.get("steps"):
        if plan.get("answer") == answer or plan.get("said") == answer:
            return plan
        if _our_own_line(answer, plan):
            plan["answer"] = answer  # the same answer, one step further on
            # A line of the answer's own steps said back has moved the chat as far as it names:
            # after "ive already turned the water off" the bot answers "Right - take the handle
            # off, and take the old part to a hardware shop", and the "and then" after it wants
            # what is past those, not the handle again.
            plan["at"] = max(plan.get("at") or 0, _said_in(answer, plan))
            return plan
        turns = len((memory or {}).get("turns") or [])
        # An answer with steps of its own is a new set of steps, however close to the old job it
        # is: "my bathroom tap drips" / "what next" / "my boiler is losing pressure" is not the
        # tap's second step, and a plan kept because both are jobs in the same room hands the
        # handle over to someone filling a boiler. The old plan is only carried on by an answer
        # that brings no steps of its own (a chat reply, a step said back) or the same ones.
        fresh = steps_of(answer)
        if (not fresh or fresh == plan.get("steps")) \
                and turns - (plan.get("turn") or 0) < WHILE_IT_LASTS \
                and (_the_same_topic(memory, plan) or _the_same_job(answer, plan)):
            plan["answer"] = answer
            plan["at"] = max(plan.get("at") or 0, _said_in(answer, plan))
            return plan
    if _module_of_last(memory) in NOT_A_JOB:
        return None
    steps = steps_of(answer)
    if not steps:
        return None
    return {"answer": answer, "steps": steps, "at": 0,
            "turn": len((memory or {}).get("turns") or []),
            "topic": copy.deepcopy(memory.get("topic")) if isinstance(memory.get("topic"), dict)
            else None}


def carry_on(text, memory):
    """The next step of the answer in hand, for a bare "what next" or "and then". Else None.

    The step count is advanced only by this module, and only when it has just handed a step over,
    so the order is the answer's order: the first ask gets the first step, the second the second,
    and a person who says "ive tried the plunger" between two asks has the steps they named
    skipped, which is the whole point of keeping the order rather than searching the answer's words
    again.
    """
    line = str(text or "").strip()
    if not line or not isinstance(memory, dict):
        return None
    if not CARRY_ON.match(line):
        return None
    plan = _plan_for(memory)
    if plan is None:
        return None
    # One turn, one step. Several modules are asked about the same line and the arbiter keeps one of
    # them, so the step has to be read the same way by all of them: a reader later in the same turn
    # gets the answer the first one gave, and only a new line moves the count on.
    here = len(memory.get("turns") or [])
    if plan.get("at_turn") == here and plan.get("said"):
        return plan["said"]
    steps = plan["steps"]
    at = plan.get("at") or 0
    # A step is still to be done if they have not told this chat they did it: "my bathroom tap
    # drips" / "i tried the washer" / "what next" must not hand the washer back.
    while at < len(steps) and _tried(steps[at], memory):
        at += 1
    if at >= len(steps):
        last = steps[-1]
        if plan.get("done"):
            said = pick(FINISHED, memory, line)
        else:
            said = pick(DONE, memory, line).format(
                step=last[0].lower() + last[1:])
        _record(memory, plan.get("answer") or "", steps, at, said)
        memory["steps"]["done"] = True
        return said
    step = steps[at]
    if _OPENS_ON_THE_INSTRUCTION.match(step):
        said = step[0].upper() + step[1:]
        if not said.endswith((".", "!", "?")):
            said += "."
    elif at == 0:
        leads = AMOUNTS_LEADS if AMOUNTS.match(step) else FIRST_LEADS
        said = pick(leads, memory, line).format(step=step[0].upper() + step[1:])
    else:
        # Turned by the step, not picked: two frames running ("The step after that:" and then "The
        # step after that:" again) is the bot repeating itself, and the order of the answer is the
        # one thing here that is not a choice.
        said = LEADS[(at - 1) % len(LEADS)].format(step=step[0].upper() + step[1:])
    if at == 0 and len(steps) in _COUNTS:
        said = f"{said} {_COUNTS[len(steps)]}"
    _record(memory, plan.get("answer") or "", steps, at + 1, said)
    return said


def _record(memory, answer, steps, at, said=""):
    """Remember where the chat has got to, for the next "what next"."""
    turn = len(memory.get("turns") or [])
    before = memory.get("steps") if isinstance(memory.get("steps"), dict) else {}
    same = before.get("steps") == steps
    topic = memory.get("topic")
    memory["steps"] = {"answer": answer,
                      "steps": steps, "at": at, "turn": turn, "at_turn": turn, "said": said,
                      "done": bool(before.get("done")) and same,
                      "topic": before.get("topic") if same and before.get("topic")
                      else (copy.deepcopy(topic) if isinstance(topic, dict) else None)}
