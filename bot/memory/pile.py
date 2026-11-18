"""How much of a thing the person has, said as the whole line.

A pile is not a day. "ive got too many" after the password answer, "weve got plenty", "i have
got loads" and "ive got about thirty" are all a person telling the bot the size of what they are
holding, and nothing in any of them has happened. The account-of-the-day pool read the "ive" and
the "got" as a past doing and answered every one of them with a warm question about a day that
never took place:

    ive got too many          -> "Good to hear. What was the best bit?"
    weve got plenty           -> "Nice one. How did the rest of it go?"
    ive got none left         -> "How was it, overall?"

What a friend does with a pile is cut it down to a shortlist, because nobody gets through a pile
in one go. That is the one thing that is true of a pile of passwords, a pile of emails, a pile of
photos and a pile of jobs in the loft, so it is what this module says - and then the person has
named the thing, or said which of it matters, and the modules below have something to answer.

The reading is deliberately narrow, and it returns None for everything else:

* the line is the person and their having, then an amount and no doing: "i got too many" is a
  receipt of something that happened ("i got lots of presents") and is left alone, so only
  "i've got", "i have" and their chat-speak spellings fire;
* the amount is a surplus or a size, not a shortage of a thing the answer needs: "i ran out of
  oven cleaner" and "i dont have a plunger" are `bot/memory/limit.py`'s, and they are answered
  from the answer's own steps;
* a day marker or "done" makes it a day again ("i got a lot done today"), and it is passed on;
* the thing, when it is named, has to be a thing that comes in a pile. "too much time on my
  hands" and "too much on" are the shape without the pile, and both have an answer of their own.
"""
import re

from ..compose import pick

# The person and the having. Only the forms that carry possession, never a bare "i got": "i got
# lots of presents" is a thing that happened, and the day pool is right to ask about it.
_A_HAVE = r"(?:i|we)(?:'ve|ve|\s+have)"
# The little words between the having and the amount, in the order a person types them: "ive only
# got a few", "i have still got loads".
_A_FILLER = r"(?:(?:\s+|,\s*)(?:only|just|still|already|now|got|have)){0,3}"
# What a pile is said with. A figure said with a "about" is a size ("ive got about thirty"), and
# the number words are the ones a person says out loud.
_A_NUMBER = (r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|"
             r"twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|a hundred|a dozen|"
             r"hundred|thousand)")
AN_AMOUNT_THEY_HAVE = re.compile(
    r"^\W*(?:(?:oh|well|but|and|so|yeah|yeh|yep|no|nah|ok|okay|god|blimey|honestly|honest)"
    r"[,\s]+)*"
    r"(?:i|we)(?:'ve|ve|\s+have)" + _A_FILLER + r"\s+"
    r"(?P<amount>too\s+(?:many|much)|loads|plenty|lots|a\s+lot|tons|hundreds|thousands|millions|dozens|"
    r"(?:about|around|over|nearly|almost)\s+" + _A_NUMBER + r")"
    r"(?:\s+of\s+(?:them|it|those|these|everything))?"
    r"(?:\s+(?P<thing>[a-z][a-z'-]*(?:\s+[a-z][a-z'-]*){0,3}))?"
    r"\W*$", re.I)

# A pile named by the person is not this module's: "weve got too much stuff" is answered by the
# tidying card, which knows what to do with a houseful, and "ive got too many emails" by the one
# about unsubscribing. Only the pile said without a name of its own - or said back as "of them" -
# is left for this reading, because nothing below it knows what the pile is made of. So the thing
# has to be a back-reference, and any other name passes the line on.
A_BACK_REFERENCE = frozenset((
    "", "them", "it", "those", "these", "everything", "of them", "of it", "of those",
    "of these", "of everything",
))

# The thing in the pile has to be a thing that piles up. A length of time is not one, and neither
# is a list of jobs: "ive got too much time on my hands" and "ive got too much on" are answered by
# the reading that knows what they are about.
NOT_A_PILE = re.compile(
    r"\b(?:time|on|to\s+do|going\s+on|happening|to\s+say|on\s+my\s+plate|on\s+at\s+work)\b", re.I)

# The pile said as a day: "i got a lot done today". The marker and the "done" are what make the
# line about what the person did rather than about what they have, so this reading stands down.
A_DAY = re.compile(
    r"\b(?:today|tonight|last night|yesterday|this morning|this afternoon|this evening|"
    r"at the weekend|this weekend|last weekend|all day|all morning|the other day|done)\b", re.I)

# A whole line that is only the amount said back ("ive got too many of them"), so the thing is the
# one in hand and the module still knows nothing about what it is.
SHORT = 8

# The reply for a pile. Every line takes the pile down to a shortlist, because that is the one
# move that fits a pile of anything; two of them ask which of it matters, and two leave the
# person to name it, so the same line does not come round on a second pile in a row.
A_PILE_TOO_BIG = (
    "Then don't take the whole pile on: the handful that actually matter first, and the rest can "
    "wait until they do.",
    "Start with the ones you actually use and let the rest sit — a pile only gets smaller from "
    "the top. Which of it matters?",
    "That is more than anyone gets through in one go. Which of it would you miss if it went?",
    "Take the shortlist rather than the pile: what are the two or three that really count?",
)


def _the_thing(found):
    return " ".join((found.group("thing") or "").split()).lower()


def reads_the_pile(text, memory=None):
    """The reading, for a caller that wants to know without a reply: True for a pile line."""
    line = " ".join(str(text or "").split())
    if not line or "?" in line or len(line.split()) > SHORT:
        return False
    found = AN_AMOUNT_THEY_HAVE.match(line)
    if not found:
        return False
    if A_DAY.search(line):
        return False
    thing = _the_thing(found)
    if thing not in A_BACK_REFERENCE:
        return False
    if thing and NOT_A_PILE.search(thing):
        return False
    return True


def reply_for(text, memory=None):
    """A reply to a pile, or None for every other line.

    `memory` is the conversation's, and it is passed to `pick` so a pile said twice running is not
    answered with the same sentence twice.
    """
    if not reads_the_pile(text, memory):
        return None
    return pick(A_PILE_TOO_BIG, memory if isinstance(memory, dict) else {}, text)
