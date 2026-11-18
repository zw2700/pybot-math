"""A hopeful aside after the advice: "fingers crossed", "with luck", "hope it works".

People end a turn about a job in hand with a wish, not a question. The bot answered them badly
in three different ways, all of them because the line names nothing to look up:

* "fingers crossed" after the condensation answer reached the health entry about fingers going
  white, and the person who had just been told to open a window was told about Raynaud's;
* "with luck" came back as "The same goes for the luck: use the extractor fan ..." - the detail
  reader took the word as a part of the answer;
* "hope it works" was filed away as a receipt: "Got it - hope it works."

None of those is what a friend says. A friend says the wish back, briefly, warmly, and leaves the
door open: "Fingers crossed. Tell me how it goes." That is the whole reply, so this module has one
pool and no knowledge in it.

The reading is strict, because a line with something of its own in it belongs to whatever answers
that thing:

* the whole line has to be the wish and the fillers around it ("ok fingers crossed", "fingers
  crossed for me", "with any luck", "touch wood", "hope so", "i hope it does the trick"): a line
  that says anything else ("im going to rome, fingers crossed") is left alone;
* a hope about somebody or something named ("hope you feel better", "hope the scan goes well") is
  a wish for a person, not an aside about the plan, so it is left to the greeting, which knows how
  to answer a good wish;
* asking is not hoping: a line with a question mark is a question ("any luck?"), and the answer is
  what they found, not a wish back.

The wish people make most of all is "good luck", and it was the one shape missing: after an answer
it fell past this module to whatever had just answered, which printed the answer again - the
marathon programme came back word for word under "alright then, good luck", "good luck!" and
"right, best of luck". No line of that shape names anything to look up, so it belongs here with
the rest.
"""
import re

# The words that carry no meaning of their own here: the pauses and courtesies around a wish.
# A pause in front of the wish, with the comma people type after it: "right, best of luck" and
# "alright then, good luck" are the same aside as "good luck".
FILLER = (r"(?:(?:ok|okay|well|right|alright|and|so|then|anyway|honestly|please|thanks|ta|ha|"
          r"lol|x)\b[,;\s]+)*")

# The wish itself. Each shape is the whole of what is left of the line once the fillers go.
WISH = re.compile(
    FILLER
    + r"(?:"
      r"(?:good|best\s+of|all\s+the)\s+luck"
      r"(?:\s+(?:with|on|for)\s+(?:it|that|this|them|me|us|"
      r"(?:the|your|my)\s+[a-z']+(?:\s+[a-z']+)?))?"
      r"|all\s+the\s+best(?:\s+(?:with|to)\s+(?:it|that|this|you|them))?"
      r"|(?:keep\s+)?(?:your|my|our)?\s*(?:fingers|fingers and toes|thumbs)(?:\s+(?:and|n)?\s*(?:toes))?"
      r"\s*(?:crossed|are crossed)?(?:\s+for\s+(?:me|us))?"
      r"|(?:with\s+)?(?:any\s+)?luck(?:,?\s+(?:then|anyway))?"
      r"|touch\s+wood"
      r"|heres?\s+hoping"
      r"|(?:hopefully(?:,?\s+(?:then|anyway))?"
      r"(?:\s+(?:that|it|this)(?:\s+(?:works?|does(?:\s+(?:the\s+trick|it|the\s+job))?|"
      r"helps?|is\s+enough|sorts\s+it))?)?)"
      r"|(?:i\s+)?(?:really\s+|do\s+|just\s+)?hope\s+(?:so|it|that|this)"
      r"(?:\s+(?:works?|does(?:\s+(?:the\s+trick|it|the job))?|helps?|goes\s+well|lands|"
      r"is\s+enough|comes\s+off|holds|clears(?:\s+up)?|sorts\s+it))?"
      r")"
    + FILLER
    + r"[!. ]*$",
    re.I,
)

# What is said back, grouped by the wish the person made: their own words in front of it read as
# the same wish coming back, which "Fingers crossed." is and a line about hoping is not. Two ways
# to say each one, so a second wish in the same chat is not the same words again.
GROUPS = {
    # The person's own words come back, so "good luck" is answered with good luck and not with
    # the luck of "with luck" - which read as a remark about the plan rather than a wish.
    "goodluck": (
        "Good luck with it \u2014 tell me how it goes.",
        "Good luck. Say how you get on.",
    ),
    "fingers": (
        "Fingers crossed. Tell me how it goes.",
        "Crossing mine as well. Say how you get on.",
    ),
    "luck": (
        "With luck, then. I would like to hear how it turns out.",
        "With luck. Tell me how it goes.",
    ),
    "wood": (
        "Touch wood. Tell me how it goes once you know.",
        "Touch wood, then. Say how it turns out.",
    ),
    "hope": (
        "Hope so too. Come back and say how it landed.",
        "Hoping with you. Tell me how it goes.",
    ),
}

# The wish the line makes, so the reply comes back in the person's own idiom.
_FINGERS = re.compile(r"\b(?:fingers|thumbs)\b", re.I)
_WOOD = re.compile(r"touch\s+wood", re.I)
_LUCK = re.compile(r"\bluck\b", re.I)


_GOOD_LUCK = re.compile(r"\b(?:good|best\s+of|all\s+the)\s+luck\b|\ball\s+the\s+best\b", re.I)


def _group(line):
    if _GOOD_LUCK.search(line):
        return "goodluck"
    if _FINGERS.search(line):
        return "fingers"
    if _WOOD.search(line):
        return "wood"
    if _LUCK.search(line):
        return "luck"
    return "hope"


# A wish for a named person or thing is the greeting's ("hope you feel better"), not an aside
# about the job in hand.
FOR_SOMEONE = re.compile(r"\bhope\s+(?:you|your|he|she|they|it\s+goes|the|everything)\b", re.I)


def reading(text):
    """Whether the whole line is a hopeful aside about the thing in hand."""
    line = str(text or "").strip()
    if not line or "?" in line:
        return False
    if FOR_SOMEONE.search(line):
        return False
    return bool(WISH.match(line))


def answer_for(text, memory):
    """The brief reply to a hopeful aside, or None when the line is not one."""
    if not reading(text):
        return None
    pool = GROUPS[_group(str(text or ""))]
    if isinstance(memory, dict):
        # Counted in the conversation, so a second wish in the same chat is said a different way:
        # the same three words twice running is the machine STYLE.md rules out, whatever the line
        # above it was.
        count = memory.get("hope_said")
        count = count + 1 if isinstance(count, int) else 1
        memory["hope_said"] = count
        return pool[(count - 1) % len(pool)]
    return pool[0]
