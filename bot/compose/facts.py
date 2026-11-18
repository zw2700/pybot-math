"""A card is not the date the person has already given.

"when do we fly" and "when is my dentist appointment" ask for a fact the person has told the bot,
and the memory store hands the fact straight back - "In July.", "You're at the dentist on
tuesday." Both were answered by a knowledge card that read the subject and none of the date: the
airport check-in card for the flight, and "ring practices near you and ask whether they take new
NHS patients" to somebody who already has an appointment.

So the reading is two questions, kept apart here and put together by the arbiter: does the line ask
*when* about the thing, and does a reply carry the date? A card that answers a different question
than the one asked then stands down, and nothing else about it changes.
"""
import re

from ..memory import narrow

# The asks that want a date back: "when do we fly", "when is my dentist appointment", "what time is
# my train", "which day do we fly", "what date is the concert". The word in the asking place has to
# be one that asks for a fact about the thing - "when should i plant tomatoes" and "when can i take
# the plaster off" are questions about doing something, and they keep their cards, so a modal
# (should, can, could, would, might) in that place stands this reading down.
WHEN_ASK = re.compile(
    r"^\W*(?:(?:and|so|but|ok|okay|oh|ah|right|well|yes|yeah|hi|hey|please|then|now|quick"
    r"|sorry|also)\W+)*"
    r"(?:when|what\s+time|what\s+day|which\s+day|what\s+date|which\s+date)\s+"
    r"(?:is|are|was|were|do|does|did|will|shall|have|has|am)\b", re.I)

# A question about the right moment to do something is a how-to, not an ask for a date: "when is
# the best time to plant tomatoes" wants the gardening card, and a store line that happens to hold
# a month is not its answer.
HOW_TO_MOMENT = re.compile(
    r"\b(?:best|good|right|ideal|worst)\s+time\b|\btime\s+to\s+"
    r"(?:plant|sow|prune|book|go|start|take|give|use|apply|cut|paint|ring)\b", re.I)

# `narrow.has_a_date` wants a day of a month, a weekday, a clock with am/pm or a year. The answer
# to "what time is my train" can be written "At 7." with no am or pm, so a clock time is counted
# here too - but **a month on its own is not**: "In July." is not the answer to "when is my
# flight", where the honest card ("the time is on your ticket") is better than the month the
# person already knew they were going.
A_MONTH = re.compile(
    r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?"
    r"|aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b", re.I)
A_CLOCK = re.compile(
    r"\b(?:at|by|around|about|from|until|till)\s+\d{1,2}(?::\d{2})?\s*"
    r"(?:am|pm|a\.m|p\.m|o'?clock)?\b", re.I)

# A fact is a fact, not a paragraph: a store reply that has grown into an answer of its own is not
# the date the person asked for, and it does not need this rule to win.
MOST_WORDS = 45


def asks_for_a_when(text):
    """Whether the line asks when something is, rather than how to do it."""
    if HOW_TO_MOMENT.search(text or ""):
        return False
    return bool(WHEN_ASK.search(text or ""))


def holds_a_date(text):
    """Whether a reply carries a date, a weekday or a clock time.

    `narrow.has_a_date` already knows what a written date looks like, and it counts a bare number
    only when it is not money, so "over £150,000" is not read as a date here either.
    """
    said = text or ""
    return bool(narrow.has_a_date(said) or A_CLOCK.search(said))


# The words a date is written in, so two replies can be asked whether they name the same one. A
# weekday, a month, a written day of a month, a clock and a year: the same kinds `holds_a_date`
# counts, spelled out here because `narrow.has_a_date` only answers yes or no.
DATE_TOKEN = re.compile(
    r"\b(?:mon|tues?|wed(?:nes)?|thur?s?|fri|sat(?:ur)?|sun(?:day)?)(?:day)?\b"
    r"|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b"
    r"|\b\d{1,2}(?:st|nd|rd|th)\b"
    r"|\b\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m|p\.m|o'?clock)\b"
    r"|\b(?:19|20)\d{2}\b", re.I)


def _date_words(text):
    return {word.lower().rstrip(".") for word in DATE_TOKEN.findall(text or "")}


def the_same_date(one, two):
    """Whether two replies name the same date, so a card that carries it needs no help."""
    first = _date_words(one)
    return bool(first and first & _date_words(two))


def the_fact_asked_for(text, reply):
    """Whether this reply is the date the line asked for."""
    if not asks_for_a_when(text):
        return False
    if len((reply or "").split()) > MOST_WORDS:
        return False
    return holds_a_date(reply)
