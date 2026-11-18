"""A line that is only a deadline is a deadline on the plan the chat is already on.

"we want to save 3000 pounds" / "by december" is a person adding the date to a goal they have just
given, and the bot answered "I'm listening - say more if it helps." Nothing in "by december" can
be looked up on its own, so the lookup finds nothing, and every reader that wants a thing named
passes it by. The plan being paced is the one said a turn ago, and the date is the only new fact
in the line.

So the line is read as the plan with the date on it ("we want to save 3000 pounds by december"),
and the entry that answered the goal answers that: the saving entry works the per-month figure out
from the date, where the goal alone gets the general advice. The words of the plan are never
invented - they are the turn before this one, unchanged - and the module passes on everything
else:

* a deadline needs a plan in front of it. "by december" as the first thing said is a fragment,
  and a conversation that opens with it has nothing to pace yet.
* the plan has to be a plan: the line before has to ask for nothing and carry a goal in it ("we
  want to save 3000 pounds", "i need to get the kitchen done"). A date after a question is a
  date for that question's answer, and after a plain statement of fact ("my exam is in june") it
  is not a deadline at all.
* the line has to name nothing but a date. "by december i want to be in a flat" names what they
  want and keeps its own turn.
"""
import re

from . import topics

# The words that make a line a deadline at all, and the date shapes that can follow them. Both
# halves have to be there: "by" on its own ("by the way") is not a deadline, and a date on its own
# is a fact the store already keeps.
DEADLINE = re.compile(
    r"^\s*(?:(?:and|so|but|ok|okay|right|well|also|actually|probably|ideally|hopefully|"
    r"definitely|really|just|maybe)[ ,]+)*"
    r"(?P<lead>by|before|until|til|till|up\s+to|in\s+time\s+for|from)\s+"
    r"(?P<when>.+?)\s*[.!?]*$", re.I)

# The date itself. Every word of it has to be one of these, so "by december i want a flat" and
# "by the way" are both left alone.
WHEN = re.compile(
    r"^(?:"
    r"(?:the\s+)?(?:end|start|beginning|middle)\s+of\s+(?:the\s+)?(?:month|year|week|summer)"
    r"|(?:this|next|the)\s+(?:month|year|week|summer|winter|spring|autumn|christmas|easter|"
    r"new\s+year|payday|weekend)"
    r"|(?:christmas|easter|payday|new\s+year|summer|winter|spring|autumn|nightfall|"
    r"then|tomorrow|tonight|today)"
    r"|(?:a|one)\s+(?:year|month|week|fortnight|couple\s+of\s+(?:weeks?|months?|years?))"
    r"|(?:\d{1,2}|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*"
    r"(?:days?|weeks?|months?|years?|hours?)"
    r"|(?:january|february|march|april|may|june|july|august|september|october|november|"
    r"december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)"
    r"|(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
    r"|\d{1,2}(?:st|nd|rd|th)"
    r")$", re.I)

# A plan a date can pace is a money plan with an amount in it ("we want to save 3000 pounds",
# "we are saving 500 pounds"). A date on anything else is a target for a different kind of answer,
# and the money entries read "run 5k" as five thousand pounds, so the amount has to be written as
# money for this module to touch the turn.
MONEY = re.compile(r"£\s?\d|\b\d+\s?(?:grand|pounds?|quid)\b|\b\d{3,}\b", re.I)

# Words that carry nothing in a plan line: the deadline is added to whatever is left.
FILLER = frozenset("""and so ok okay right well also actually just maybe probably ideally
    hopefully definitely really then now too please thanks""".split())


def the_deadline(text):
    """The date part of a line that is only a deadline ("by december" -> "december"), or ""."""
    if not isinstance(text, str):
        return ""
    found = DEADLINE.match(text)
    if not found:
        return ""
    when = " ".join(found.group("when").lower().split())
    if not when or not WHEN.match(when):
        return ""
    return when


def _a_plan(said):
    """True when the line before is a plan the date can be put on."""
    said = " ".join(str(said or "").lower().split())
    if not said or said.endswith("?"):
        return False
    words = [word for word in topics.words(said) if word not in FILLER]
    if not words:
        return False
    return bool(MONEY.search(said))


def follow_up(text, memory):
    """The plan this deadline belongs to, or "" when the line is not that turn."""
    when = the_deadline(text)
    if not when:
        return ""
    turns = [turn for turn in (memory or {}).get("turns") or [] if isinstance(turn, dict)]
    # The deadline comes right after the plan, or after one line about it ("we want to save 3000
    # pounds" / "we are on about 200 a month" / "by december").
    for turn in reversed(turns[-3:]):
        said = str(turn.get("user") or "")
        if _a_plan(said):
            plan = " ".join(said.strip().rstrip(".!,").split())
            return plan + " by " + when
    return ""
