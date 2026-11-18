"""A fact asked for "again" is answered from the fact the store kept, not from the words of the ask.

People finish a line with "again" when they mean "the thing I told you": "and whats my target
again", "what was i keeping away from again", "when is my return again". On `9cdc62fe0` all three
were punts in the chat that holds the answer:

    im 14 stone / i want to get to 12 / and whats my target again
        -> That's beyond what I know well, sorry. Searching for it will turn up better sources...
    my daughter is allergic to nuts / what was i keeping away from again
        -> I don't know enough to answer that honestly. A search should sort you out quickly...
    im coming back on the 14th / when is my return again
        -> I'm not sure about that one, sorry - I'd rather not guess. A quick search online...

The fault is not one wording. The store had already **kept** each of these facts under its own key -
`user["plans"]` holds "Get to 12" and "im coming back on the 14th", `others[0]["allergies"]` holds
"nuts" - and every reader in the store looks for the ask's own words in the chat. "target" is not
in "i want to get to 12", "keeping away from" is not in "allergic to nuts", "return" is not in
"coming back", so nothing matched and the turn fell to a search hedge.

So the rule here is the other way round: **an "again" ask is a request for something already kept,
and the kind of thing it asks for picks the key.** A time asked for again is the dated plan they
told us; a thing to avoid asked for again is the allergy the store filed; a target asked for again
is the plan they stated. The words of the ask never have to appear in the line that answered it.

Three things keep it off lines it should not answer:

- **The store's own reading comes first.** `bot/memory/when.py::when_answer` answers "when is my
  flight again" from the words of the ask, and that answer is better than anything said back from a
  key, so this module passes whenever the store can read the time ask at all.
- **A question about the world is not a recall.** "should i eat less again", "what should i do
  again" want advice, and the "again" in them is not pointing at a fact.
- **One dated plan, or none.** A time asked for again is answered only when the chat holds a single
  dated plan. Two dates in the chat and there is no way to tell which one the ask means, so the
  turn is left alone rather than guessed at.
"""

import re

from ..memory import when as when_store

PRIORITY = 7050

# The cue. "again" is the whole of it: it is how a person points back at something already said.
AGAIN = re.compile(r"\bagain\b", re.I)
# An ask, not a statement: the line has to want something back.
AN_ASK = re.compile(r"\b(?:what|whats|what's|when|which|where|who|how much|how many)\b", re.I)
# A question about the world. The "again" in these asks for another go at a decision, not for a
# fact they gave: "should i eat less again" is not asking what they weighed.
NOT_A_RECALL = re.compile(r"\b(?:should|shall|ought|best|better|tips?|advice|recommend\w*|"
                          r"worth|cheapest|easiest|normal|usually|ok|okay|fine|bad|safe|"
                          r"possible|allowed|do i need to|can i|could i|is it)\b", re.I)

A_TIME = re.compile(r"\bwhen\b|\bwhat (?:day|date|time)\b", re.I)
A_THING_TO_AVOID = re.compile(r"(?:keep\w* (?:away|off)|stay\w* (?:away|off)|avoid\w*|allerg\w*|"
                              r"cant have|can'?t have|not allowed|off limits|cant eat|can'?t eat)",
                              re.I)
A_TARGET = re.compile(r"\b(?:target|goal|aim|trying to get to|trying to reach|hoping to get to|"
                      r"hoping for|working towards|saving for)\b", re.I)

# A date said in a plan. The compound forms come first, so "the 12th of june" is said whole rather
# than as "the 12th".
A_DATE = (
    re.compile(r"\b(?:the\s+)?\d{1,2}(?:st|nd|rd|th)\s+(?:of\s+)?(?:jan|feb|mar|apr|may|jun|jul|"
               r"aug|sep|oct|nov|dec)[a-z]*\b", re.I),
    re.compile(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}"
               r"(?:st|nd|rd|th)?\b", re.I),
    re.compile(r"\bnext\s+(?:week|month|year|weekend|monday|tuesday|wednesday|thursday|friday|"
               r"saturday|sunday)\b", re.I),
    re.compile(r"\b(?:the\s+)?\d{1,2}(?:st|nd|rd|th)\b", re.I),
    re.compile(r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", re.I),
    re.compile(r"\b(?:january|february|march|april|may|june|july|august|september|october|"
               r"november|december)\b", re.I),
)


def _the_plans(memory):
    """What the store kept as their plans, oldest first, newest last."""
    user = (memory or {}).get("user") or {}
    plans = [plan for plan in (user.get("plans") or []) if isinstance(plan, str) and plan.strip()]
    latest = user.get("plan")
    if isinstance(latest, str) and latest.strip() and latest not in plans:
        plans.append(latest)
    return [" ".join(plan.split()) for plan in plans]


def _the_allergies(memory):
    """[(who, what)] the store filed for the people in the chat, newest last."""
    out = []
    for one in (memory or {}).get("others") or []:
        if not isinstance(one, dict):
            continue
        who = str(one.get("who") or "").strip()
        for what in one.get("allergies") or []:
            what = str(what or "").strip()
            if what:
                out.append((who, what))
    return out


def _the_date_in(plan):
    """The date a plan carries, in the words the plan says it, or None."""
    for pattern in A_DATE:
        match = pattern.search(plan)
        if match:
            return " ".join(match.group(0).split())
    return None


def _the_time_asked_again(text, memory):
    """The one dated plan the chat holds, said back, or None."""
    # The store can read the ask's own words - "when is my flight again" - and that reply is the
    # better one, so this module stays out of its way.
    try:
        if when_store.when_answer(text, memory):
            return None
    except Exception:  # noqa: BLE001 - the store's reader must never lose this line
        return None
    dated = [date for date in (_the_date_in(plan) for plan in _the_plans(memory)) if date]
    if len(dated) != 1:
        return None
    return "You said " + dated[0] + "."


def _the_thing_to_avoid_asked_again(text, memory):
    """The allergy the store filed, said back, or None."""
    allergies = _the_allergies(memory)
    if not allergies:
        return None
    who, what = allergies[-1]
    if who:
        return what.capitalize() + " - your " + who + " is allergic to them."
    return what.capitalize() + "."


# How a plan is said as the thing a target asks for: the person's own "i want to get to 12" is
# "to get to 12" once the asking is off it, and a plan the store kept with the asking already gone
# ("Get to 12") is the same shape.
PLAN_OPENS = ("i want to ", "i wanna ", "i'm trying to ", "im trying to ", "i am trying to ",
              "i'm hoping to ", "im hoping to ", "i am hoping to ", "i hope to ", "to ")
# The word the ask used for the thing, so the reply names what was asked about rather than a
# generic "plan": "what was my goal again" is answered about their goal.
THE_WORD_ASKED = (("goal", "goal"), ("aim", "aim"), ("target", "target"), ("plan", "plan"))


def _the_noun_asked(text):
    """The person's own word for the thing they asked about again."""
    low = " ".join(text.lower().split())
    for word, noun in THE_WORD_ASKED:
        if re.search(r"\b" + word + r"s?\b", low):
            return noun
    return "plan"


def _a_name(plan):
    """Whether the word the plan opens on is somebody's or something's name, so it keeps its capital."""
    first = plan.split()[0] if plan.split() else ""
    return bool(re.search(r"\b(?:vauxhall|ford|toyota|nissan|bmw|audi|honda|ikea|argos|"
                          r"january|february|march|april|may|june|july|august|september|october|"
                          r"november|december|monday|tuesday|wednesday|thursday|friday|saturday|"
                          r"sunday)\b", first, re.I)) and first[:1].isupper()


def _the_target_asked_again(text, memory):
    """The plan they stated, said back under the word they used for it, or None."""
    plans = _the_plans(memory)
    if not plans:
        return None
    plan = plans[-1]
    low = plan.lower()
    for opener in PLAN_OPENS:
        if low.startswith(opener):
            plan = plan[len(opener):]
            break
    noun = _the_noun_asked(text)
    # "Get to 12" keeps its capital when it opens a line and loses it inside one; a name keeps it.
    if plan[:1].isupper() and not plan[:2].isupper() and not _a_name(plan):
        plan = plan[0].lower() + plan[1:]
    return "You said your " + noun + " is to " + plan.rstrip(".!?") + "."


def respond(text, memory):
    """The fact the store kept for the kind of thing the line asks for again, or None."""
    if not isinstance(text, str) or not isinstance(memory, dict):
        return None
    low = " ".join(text.lower().split())
    if not AGAIN.search(low) or not AN_ASK.search(low) or NOT_A_RECALL.search(low):
        return None
    if A_TIME.search(low):
        return _the_time_asked_again(text, memory)
    if A_THING_TO_AVOID.search(low):
        return _the_thing_to_avoid_asked_again(text, memory)
    if A_TARGET.search(low):
        return _the_target_asked_again(text, memory)
    return None
