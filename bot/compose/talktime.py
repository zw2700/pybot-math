"""A talk asked for at a time: "can we talk tonight", "can we chat later", "can you keep me company".

Nothing here keeps a diary and there is no clock on this end, and that is the honest half of the
answer. What went wrong on main is the other half: these lines reached the search hedge ("I don't
know enough to answer that honestly. A search should sort you out quickly"), which hands a person
who wants a conversation a page about nothing. A friend offered a time does not say "look it up" -
they say when they are reachable, and ask what it is about.

The reading is narrow on purpose:

  - the ask is a talk word (talk, chat, speak, catch up, a word, a chat, a talk) with a *time* on
    the end and nothing else. The time is what makes it a plan, so `THE_TIME` is a closed list of
    days, parts of a day and points in one, and the anchor needs it to be all that is left. Without
    it "can we talk" keeps its chat line ("Yep, right here - go on.") and "can we talk properly"
    keeps the same one;
  - a thing named after the talk is the thing's own reading, not this one: "can we talk about my
    boiler" and "can we talk tomorrow about the rent" are the boiler and the rent;
  - "can you keep me company" is the same ask with no time on it, and nothing else reads it, so it
    does not have to carry one;
  - harm is never a plan: "can we talk tomorrow, i keep thinking about ending it" belongs to the
    safety cards and the care pools, which are asked first anyway - the fence here means this
    reading can never be the one that answers it.

It is asked early in `_reply_for` (`bot/compose/fallback_chain.py`), before the hedge and before the
pools that answer a thing, and it stands down for any line that names what the talk is about.
"""
import re

from . import fallback

# The words that put a talk at a time. A closed list of days was the wrong shape: it answered a
# third of the lines this reading is for, because people say "sometime", "in the week", "later
# tonight", "when you get a chance", "after work", and a bare "tonight please" with a courtesy in
# front of the question mark. What ends a line here is a *trailing time phrase* - the markers below,
# alone or stacked - rather than a fixed set of strings.
_DAY = (r"(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|today|tomorrow|tonight|"
        r"christmas|the weekend)")
_PART = (r"(?:morning|afternoon|evening|night|daytime|lunchtime|teatime|"
         r"after work|after tea|after dinner|after lunch|after school|after the kids are in bed)")
_A_MARKER = (
    # a day, with or without the part of it: "thursday", "tomorrow evening", "saturday night"
    r"(?:(?:this |next |on |by )(?:" + _DAY + r")"
    r"|(?:" + _DAY + r")(?:\s+(?:" + _PART + r"))?"
    # a part of a day on its own, or with a pointer: "evening", "in the morning", "this afternoon"
    r"|(?:this |in the |in |during the |tomorrow )(?:" + _PART + r")"
    r"|(?:" + _PART + r")"
    # a loose time: "later", "in a bit", "at some point", "sometime", "whenever"
    r"|later(?:\s+on)?|in a (?:bit|minute|while|mo)|in the week|during the week|"
    r"sometime|some time|any time|at some point|at some stage|whenever|"
    r"next week|this week|next month|this month"
    # the clock, which is the commonest way of all and the one the first version left out: "can
    # we talk at 6", "at 7.30", "at 8pm", "at six", "at noon", "in an hour"
    r"|at\s+\d{1,2}(?:[.:]\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.|o'?clock)?"
    r"|at\s+(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|noon|midday|"
    r"midnight|teatime|lunchtime|half\s+\w+|quarter\s+\w+)"
    r"|in\s+(?:a|one|two|three|half\s+an?|an?|\d{1,3})\s+(?:hour|hours|hr|hrs|minute|minutes|"
    r"min|mins)"
    # the ask keeps its own clock: "when you get a chance", "when you're free"
    r"|when you(?:'re| are) free|when you have time|when you get a chance|when you can)"
)
# One marker, or two stacked ("later tonight", "tomorrow evening", "tonight after work"). A third
# adds nothing a person says and would let a longer clause through.
THE_TIME = r"(?:" + _A_MARKER + r"(?:\s+" + _A_MARKER + r"){0,2})"
# One courtesy word is how half of these arrive: "can we talk tonight please".
A_COURTESY = r"(?:\s+(?:please|thanks|thank you|ta))?"

# "can you keep me company" is the same ask with no time on it, and nothing else in the deck reads
# it - on main it was the search hedge - so it does not have to carry one.
A_COMPANY_ASK = re.compile(
    r"^(?:hi|hiya|hey|hello|so|ok|okay|and|but|just|right)?[,!. ]*"
    # "keep me company" is how a person says it, so the modal in front is optional.
    r"(?:(?:can|could|will|would|do)\s+(?:you|u)\s+(?:please\s+)?)?"
    # "stay with me tonight" is the same ask as "keep me company", and it is how someone on
    # their own says it.
    r"(?:(?:keep|stay)\s+me\s+company|stay\s+with\s+me)"
    r"(?:" + A_COURTESY + r"|\s+(?:" + THE_TIME + r")" + A_COURTESY + r")?\s*[?.!]*$")
A_TALK_AT_A_TIME_ASK = re.compile(
    r"^(?:hi|hiya|hey|hello|so|ok|okay|and|but|just|right|um|er)?[,!. ]*"
    r"(?:(?:can|could|shall|should|would|will)\s+(?:we|you|u|i)\s+(?:please\s+)?"
    r"(?:talk|chat|speak|catch up|have a word|have a chat|have a talk)"
    r"(?:\s+(?:to|with)\s+(?:you|u|me))?"
    r"|i\s+(?:want|need|would like|wanna|have)\s+to\s+(?:talk|chat|speak)\s+to\s+(?:you|u))"
    r"\s+"
    + THE_TIME + A_COURTESY +
    r"\s*[?.!]*$")
# A talk asked for about somebody else's trouble is the safety and the care pools' line, not this
# one: "can we talk tomorrow, i keep thinking about ending it" is not a plan for a chat.
A_TALK_AT_A_TIME_HARM = re.compile(
    r"\b(?:kill myself|end it|end my life|suicid|self harm|hurt myself|overdose|\bdie\b|"
    r"\bdying\b|dead|funeral|died|cancer|hospital|ambulance|999|911)\b")

# No diary, no clock, and the offer is the talk itself. Six lines so a person who asks twice is not
# handed the same sentence back, and none of them names a time of its own: the person said
# "tomorrow morning", so a line that answers "tonight" contradicts them, and one that answers
# "tomorrow" claims a diary nothing here keeps.
A_TALK_AT_A_TIME = (
    "I can't hold a time or remind you - no diary and no clock on this end. The chat doesn't mind "
    "when you come back, so start now or whenever suits: what's it about?",
    "Nothing here books a slot or rings you, so a time is the one thing I can't keep. What I can do "
    "is talk it through now and pick it up again when you come back. What did you want to say?",
    "There's no diary on this end, so I can't promise to be there at a set time - but nothing here "
    "closes either, so the thread keeps its place. What's on your mind?",
    "I can't put anything in a diary or set a reminder, and I would rather say that than nod along. "
    "What I can do is start now and keep the thread for whenever you come back. What's up?",
    "No clock here, so any hour is all the same to me, and the conversation stays where we leave "
    "it. What did you want to talk about?",
    "I can't save a slot or bring it up again, sorry - but the chat is here at any hour of the day "
    "and keeps its place. What's going on?",
)


def answer_for(text, memory=None):
    """The honest line for a talk asked for at a time, or None when the line is something else."""
    said = memory if isinstance(memory, dict) else {}
    clean = " ".join(str(text or "").lower().split())
    if not clean:
        return None
    if not (A_TALK_AT_A_TIME_ASK.match(clean) or A_COMPANY_ASK.match(clean)):
        return None
    if A_TALK_AT_A_TIME_HARM.search(clean):
        return None
    return fallback._choose(A_TALK_AT_A_TIME, said, clean)
