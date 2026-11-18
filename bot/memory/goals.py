"""A loss the chat already has the reason for is not a loss that needs checking.

    im trying to lose weight
      -> Change a few things you can keep doing rather than going on a diet ...
    i lost 2 kg
      -> Was that on purpose, or has it been dropping on its own? If it's going without you
         trying, a word with the GP is worth it.                        (main)

That reply belongs to weight coming off by itself, which is worth a word with a doctor. Here the
person said one turn ago that they were trying to lose it, so the answer is a shrug at a plan
working, and the figure said back. Nobody wants to be asked whether their diet was on purpose.

The rule is about the room, not the words: the same line in a chat with no plan to lose weight on
file keeps the check, because there it is unexplained loss. Nothing else changes - "i lost my job"
is still bad news, and "i lost 2 kg" on its own is still the check, because nothing in the chat
says the person wanted to.
"""
import re

# The figure, said the way people say it: a number with its unit, a stone, or "some weight".
A_LOSS = re.compile(
    r"\b(?:i|ive|i have)\s+lost\s+(?P<how>"
    r"half\s+a\s+stone|a\s+stone|"
    r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*"
    r"(?:kilos?|kg|kgs|pounds?|lbs?|stone)|"
    r"(?:some|a\s+lot\s+of)\s+weight|weight)\b", re.I)

# What a plan to lose weight looks like in the store: the store keeps the person's aim in its own
# words ("Lose weight", "on a diet", "getting fit"), so the words of the aim are what is read.
A_PLAN_TO_LOSE = re.compile(
    r"\b(?:lose|losing|lost|slim|slimming|diet|dieting|weight|kg|kilos?|pounds?|lbs?|"
    r"stone|calories|cutting\s+down|get\s+fitter|fitness)\b", re.I)

# A number with its unit glued on is how people type it ("2kg", "5lbs"), and said straight back it
# reads as a typo, so the unit gets its space.
GLUED_UNIT = re.compile(r"(?<=\d)(kgs?|kilos?|pounds?|lbs?|stone)\b", re.I)

# Said twice in a chat, the reply does not ask what is working: the first one already did.
SAID_BACK = (
    "{X} off is a real loss, and slow is the way it stays off. It is on file.",
    "{X} down is the plan working, which is the only thing that matters here.",
    "That is {x2} of the plan doing its job. I'll keep the meals on the lean side when you ask.",
)
FIRST = (
    "{X} off - good going, and at a rate that stays off. What is working so far?",
    "{X} down is real progress: slow enough to keep, which is the part most people miss.",
    "Nice one: {X} off, and no starving yourself for it. Say if you want meal ideas that hold up.",
)

# A question about how the plan is going, asked with nothing else in the line. It is answered
# from the figure the chat holds: "how am i doing" two turns after "i lost 2 kg" came back as the
# diet card again (and, in a chat about a half stone, as an arithmetic card: "Divide it by 2: half
# of 46 is 23..."), which answers a question nobody asked.
HOW_GOING = re.compile(
    r"^(?:so\s+|and\s+|ok(?:ay)?\s+,?\s+)?"
    r"(?:how\s+am\s+i\s+(?:doing|getting\s+on|going)|how\s+(?:is|s)\s+it\s+going|"
    r"how\s+am\s+i\s+getting\s+on|how\s+is\s+the\s+(?:diet|plan)\s+going|"
    r"how\s+much\s+have\s+i\s+lost|how\s+much\s+weight\s+have\s+i\s+lost|"
    r"(?:is|was)\s+that\s+(?:good|ok|okay|alright|any\s+good)\s+(?:going|so\s+far)?|"
    r"am\s+i\s+doing\s+(?:well|ok|okay|alright|it))\s*[.!?]*$", re.I)

PROGRESS_REPLY = (
    "{X} so far, by your own count - and slow is the rate that stays off, so that is going well. "
    "Say if you want the meals tightened up.",
    "{X} down and still going, which is the part most people lose. Nothing to change if it is "
    "still coming off slowly.",
    "You have {x2} off since you started. That is on the good side of the pace, so keep the plan "
    "as it is unless it stalls.",
)

_NUMBER_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
                 8: "eight", 9: "nine", 10: "ten"}


def _tidy(how):
    """"2kg" -> "2 kg", "half a stone" -> "Half a stone"."""
    said = GLUED_UNIT.sub(lambda m: " " + m.group(1), " ".join(str(how or "").split()))
    said = " ".join(said.split())
    return said[:1].upper() + said[1:] if said else said


def _the_plan_to_lose(memory):
    """True when the chat holds an aim to lose weight, in the store's own words."""
    if not isinstance(memory, dict):
        return False
    user = memory.get("user") if isinstance(memory.get("user"), dict) else {}
    said = []
    for key in ("plan", "goal", "aim", "diet"):
        value = user.get(key)
        if isinstance(value, str):
            said.append(value)
    for key in ("plans", "goals"):
        value = user.get(key)
        if isinstance(value, (list, tuple)):
            said.extend(str(item) for item in value)
    return any(A_PLAN_TO_LOSE.search(text) for text in said if text)


def _the_turn_that_said_it(memory):
    """How many times the chat has been told about a loss, this line included."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    seen = 0
    for turn in list(turns or []):
        if isinstance(turn, dict) and A_LOSS.search(str(turn.get("user") or "")):
            seen += 1
    return seen


def the_loss_that_was_the_plan(text, memory):
    """The reply to a loss said in a chat that was already trying to lose it, or ""."""
    match = A_LOSS.search(str(text or ""))
    if not match:
        return ""
    if not _the_plan_to_lose(memory):
        return ""
    how = _tidy(match.group("how"))
    pool = FIRST if _the_turn_that_said_it(memory) <= 1 else SAID_BACK
    turns = memory.get("turns") if isinstance(memory, dict) else None
    reply = pool[len(turns or ()) % len(pool)]
    if "{X}" in reply:
        reply = reply.replace("{X}", how)
    else:
        reply = reply.replace("{x2}", how[:1].lower() + how[1:])
    if isinstance(memory, dict) and isinstance(memory.get("user"), dict):
        # The figure is the chat's own record of the plan working, and the store has no other
        # place for it: what has been lost is not the person's weight, it is progress.
        memory["user"]["progress"] = {"lost": how}
    return reply


def _the_progress(memory):
    """The figure the chat holds for the plan in hand, or ""."""
    if not isinstance(memory, dict):
        return ""
    user = memory.get("user") if isinstance(memory.get("user"), dict) else {}
    progress = user.get("progress") if isinstance(user.get("progress"), dict) else {}
    lost = str(progress.get("lost") or "").strip()
    return lost if lost and lost.lower() not in ("weight", "some weight") else ""


def a_progress_asked(text, memory):
    """The reply to "how am i doing" when the chat holds a figure for the plan, or "".

    Nothing else answers it: without a figure on file the line is a general question about a diet
    and the knowledge base's answer is the right one, so this returns "" and that answer stands.
    """
    if not HOW_GOING.match(" ".join(str(text or "").lower().split())):
        return ""
    lost = _the_progress(memory)
    if not lost:
        return ""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    reply = PROGRESS_REPLY[len(turns or ()) % len(PROGRESS_REPLY)]
    return reply.replace("{X}", lost).replace("{x2}", lost[:1].lower() + lost[1:])
