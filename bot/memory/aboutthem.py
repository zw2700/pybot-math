"""An ask about a person in the chat, written out with the age the store keeps for them.

"my son is 5" then "how much sleep does he need" was answered with the adult figure - seven to
nine hours, coffee at three, how you feel by mid-afternoon - because a line whose subject is a
pronoun names no age for the knowledge base to read, and the sleep entries are keyed on the age
("how much sleep does a 5 year old need" is the ten-to-thirteen answer). The store knew the age
all along: it filed it on the turn before.

So the ask is written out as the question a person would ask if they were talking to someone who
could not see their family: the pronoun becomes "a 5 year old". Only a child, and only when the
store holds the age: an adult's sleep, water and bedtime are the figures the adult entries already
give, so there is nothing to write out and no answer to change.
"""
import datetime
import re

from . import topics
from .facts import HE, SHE

# A pronoun standing for the person: "he", "his bedtime", "she needs", "their room".
PRONOUN = re.compile(r"\b(?P<own>his|her|their)\s+(?P<thing>[a-z][a-z' -]{0,20})"
                     r"|\b(?P<who>he|she|they)\b"
                     r"|\b(?P<obj>him|her|them)\b", re.I)

# An ask about the age itself is the store's question, and it is answered already ("how old is
# he", "what age is she"): writing the age into it asks the knowledge base to look up the number
# it just gave.
THEIR_AGE = re.compile(r"\bhow\s+old\b|\bwhat\s+age\b|\bhow\s+big\b|\btheir\s+age\b|\bhis\s+age\b"
                       r"|\bher\s+age\b", re.I)

# Only an ask for a figure or a time: the answers that are wrong for a child without the age are
# the measured ones ("how much sleep", "how many hours", "when should he go to bed", "what time"),
# and every one of them is keyed on the age. An ask about what to do ("should he have a nap",
# "what should i do about his bedtime") is answered by a row that already fits any child, and
# writing the age into it pulled the sleep-hours row over the nap one.
ASKS = re.compile(r"\bhow\s+(?:much|many|long|often|early|late)\b|\bwhat\s+time\b"
                  r"|\bwhen\s+(?:is|are|do|does|will|can)\b", re.I)

# An age the line already gives needs nothing written into it.
GIVEN = re.compile(r"\b\d{1,3}\b|\ba\s+(?:one|two|three|four|five|six|seven|eight|nine|ten|"
                   r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen)\b", re.I)

# The person is a child this young: the child entries answer by age, and the adult ones answer
# for everybody else. An adult's own age does not change what the knowledge base says.
CHILD_AGE = 18

# A child under two is kept in months, not years: the store files "my daughter is 6 months old"
# as `months: 6`, and an ask about her is written out as "a 6 month old" rather than as an age
# of nought years.
BABY_MONTHS = 24
SPOKEN = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight",
          9: "nine", 10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen",
          15: "fifteen", 16: "sixteen", 17: "seventeen"}


def _the_child(text, memory):
    """(how old the child is, written out, and the person) or (None, "")."""
    said = str(text or "")
    if not said or not isinstance(memory, dict):
        return None, ""
    if THEIR_AGE.search(said) or GIVEN.search(said) or not ASKS.search(said):
        return None, ""
    if "?" not in said and not topics._leads_a_question(said):  # noqa: SLF001 - its own reader
        return None, ""
    found = PRONOUN.search(said)
    if not found:
        return None, ""
    word = (found.group("who") or found.group("own") or found.group("obj") or "").lower()
    if word == "she" or word == "her":
        fits = SHE
    elif word == "he" or word == "his":
        fits = HE
    else:
        fits = SHE | HE  # "their" fits whoever the store has
    for entry in _people(memory):
        who = str(entry.get("who") or "").strip().lower()
        if not who or who not in fits:
            continue
        months = entry.get("months")
        if isinstance(months, int) and 0 < months < BABY_MONTHS:
            # A baby is kept in months, and an age of nought years says nothing: the sleep, milk
            # and food rows are keyed on the age, so "how much should she be sleeping" needs "a
            # 6 month old" in it.
            return "%s month old" % SPOKEN.get(months, str(months)), who
        age = entry.get("age")
        if isinstance(age, int) and 0 < age < CHILD_AGE:
            return "%s year old" % SPOKEN.get(age, str(age)), who
    return None, ""


def _people(memory):
    """The person the chat was last about first, then everybody the store keeps a fact about."""
    found = []
    person = memory.get("person")
    if isinstance(person, dict) and person.get("who") and (
            person.get("age") is not None or person.get("months") is not None):
        found.append(person)
    for entry in memory.get("others") or ():
        if isinstance(entry, dict):
            found.append(entry)
    return found


def with_the_age(text, memory):
    """The line asked about a child of that age: "how much sleep does he need" -> "how much
    sleep does a 5 year old need". The line itself when there is no child in it."""
    how_old, _who = _the_child(text, memory)
    if not how_old:
        return ""
    said = str(text)
    found = PRONOUN.search(said)
    if not found:
        return ""
    if found.group("own"):
        # "his bedtime" is "a 5 year old's bedtime": the thing belongs to the child, so the ask
        # is about the bedtime of a child that age.
        thing = found.group("thing").strip()
        written = said[:found.start()] + "a %s's %s" % (how_old, thing) + said[found.end():]
    else:
        written = said[:found.start()] + "a " + how_old + said[found.end():]
    written = " ".join(written.split())
    return written if written != said else ""

# An age asked for further ahead: "how old will he be next year", "how old will my son be in 2030",
# "what age will she be in two years". The store keeps one age at one day, so the ask is arithmetic
# on what it keeps rather than a fact to look up, and no entry can answer it: the words reach the
# store's own "you haven't said" card, which is about the chat rather than about the child.
AHEAD_ASK = re.compile(r"\b(?:how\s+old|what\s+age)\s+(?:will|would|is|does)\b", re.I)
AHEAD_TIME = re.compile(
    r"\bnext\s+(?P<next>year|summer|birthday)\b"
    r"|\bthis\s+time\s+next\s+year\b"
    r"|\bin\s+(?P<years>\d{1,2}|a|one|two|three|four|five|six|seven|eight|nine|ten)\s+years?\b"
    r"|\bin\s+(?P<year>(?:19|20)\d\d)\b", re.I)
COUNT = {word: number for number, word in enumerate(
    ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
     "eleven", "twelve"), 0)}
KIN = re.compile(r"\bmy\s+(?:little\s+|big\s+|eldest\s+|youngest\s+)?"
                 r"(?P<who>son|daughter|boy|girl|child|kid|lad|little one)\b", re.I)

# The word the ask uses for a child, and the words the store may have filed that child under: "my
# little girl is 2" is filed as "girl", and the ask a turn later says "my daughter".
KIN_SAME = {"son": ("son", "boy"), "boy": ("boy", "son"), "lad": ("lad", "boy", "son"),
            "daughter": ("daughter", "girl"), "girl": ("girl", "daughter"),
            "child": ("child", "kid", "son", "daughter", "boy", "girl"),
            "kid": ("kid", "child", "son", "daughter", "boy", "girl"),
            "little one": ("little one", "child", "kid", "son", "daughter", "boy", "girl")}


def an_age_ahead(text, memory):
    """The age the child will be at a day further ahead, said back, or None.

    Only for a child whose age the store keeps in whole years: a baby kept in months is a length
    the arithmetic here would get wrong, so its ask is left to whoever knows more.
    """
    said = " ".join(str(text or "").split())
    if not said or not AHEAD_ASK.search(said):
        return None
    when = AHEAD_TIME.search(said)
    if not when:
        return None
    age, words = _the_one_asked_about(said, memory)
    if age is None:
        return None
    years = _the_years_ahead(when)
    if years is None or years < 0:
        return None
    day = _the_day_named(when, years)
    if not day:
        return None
    subject = _the_subject(words)
    verb = (" " if words.startswith("your ") else "") + _the_future(words)
    return "%s%s %s %s." % (subject, verb, _an_age_said(age + years), day)


def _the_years_ahead(when):
    """How many years ahead the ask is, or None when the day it names is one to leave alone."""
    if when.group("next"):
        # "next birthday" and "next summer" name no length: a birthday is a year, a summer is not.
        return 1 if when.group("next").lower() == "year" else None
    if when.group("year"):
        try:
            return int(when.group("year")) - datetime.date.today().year
        except (TypeError, ValueError):
            return None
    count = when.group("years")
    if not count:
        return None
    return int(count) if count.isdigit() else COUNT.get(count.lower())


def _the_day_named(when, years):
    """The day the ask names, said the way a person says it: "next year", "in 2030", "in two years"."""
    if years == 0:
        return "now" if not when.group("year") else "in %s" % when.group("year")
    if when.group("year"):
        return "in %s" % when.group("year")
    if years == 1:
        return "next year"
    return "in %s years" % SPOKEN.get(years, str(years))


def _the_one_asked_about(said, memory):
    """(the age the store keeps, the words the reply uses for that person) or (None, "")."""
    if not isinstance(memory, dict):
        return None, ""
    people = _people(memory)
    named = KIN.search(said)
    if named:
        who_said = named.group("who").lower()
        fits = KIN_SAME.get(who_said, (who_said,))
        for entry in people:
            who = str(entry.get("who") or "").strip().lower()
            if not who or who not in fits:
                continue
            age = entry.get("age")
            if isinstance(age, int) and 0 < age < CHILD_AGE:
                return age, "your " + who_said
        return None, ""
    found = PRONOUN.search(said)
    if not found:
        return None, ""
    word = (found.group("who") or found.group("own") or found.group("obj") or "").lower()
    if word in ("she", "her"):
        fits, said_who = SHE, "she"
    elif word in ("he", "his", "him"):
        fits, said_who = HE, "he"
    else:
        fits, said_who = SHE | HE, "they"
    for entry in people:
        who = str(entry.get("who") or "").strip().lower()
        if not who or who not in fits:
            continue
        age = entry.get("age")
        if isinstance(age, int) and 0 < age < CHILD_AGE:
            return age, said_who
    return None, ""


def _an_age_said(age):
    """An age said the way a person says it: "seven" while a child, "34" after that."""
    if isinstance(age, int) and 0 < age <= 12:
        return SPOKEN.get(age, str(age))
    return str(age)


def _the_subject(words):
    """The words a reply about that person opens with."""
    words = (words or "").strip()
    return words[:1].upper() + words[1:] if words else "They"


def _the_future(words):
    """The verb, joined to the person the way a person says it: "He'll be", "Your son will be"."""
    return "will be" if (words or "").startswith("your ") else "'ll be"
