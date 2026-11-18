"""The shape a line asks for, where `fit.wants` reads it as something else.

`fit.wants` reads the question words of a line and the kinds of thing it names, and for three
everyday asks it lands on a shape that is not the one the person is owed. Each is read from the
person's own words, and nothing else comes back changed.

A money verb after "what should i" is read as a method, because the chain reads a `what should i`
as "how do I". The money verb is what makes it a question of how much:

    what should i tip my hairdresser        -> amount
    what should i spend on my mums birthday -> amount

"what should i spend it on" is the other way round: the money is in hand and the person wants the
thing to spend it on, so the `it` keeps it a pick, and that `it` is the whole difference from
"what should i spend on my mum".

And a present asked for by who or what it is for asks nothing the chain can see: "present for a new
puppy", "gifts for kids under a tenner" carry no question word, so the shape was left unset and the
reply was never checked against the ask at all. A present asked for is a few things to choose
between.

The last line of each arm is the one that names alternatives: "what should i pay my landlord first
the rent or the gas bill" has a money verb and an object, and is still a pick, because a line that
puts two things either side of an `or` is asking which. That is read as a stand-down rather than a
pick: the chain has already read it, and nothing here overrides a reading it did not come for.

It is read after `fit.wants`. The present arm only fills a shape the chain left unset; the two
money arms read the line themselves and stand down on a line that names alternatives.
"""
import re

from bot.compose.fit import AMOUNT, OPTIONS, PICK

# "pay" needs an object, because "what should i pay off first" is the order of the debts and that is
# a method; "spend on" is fenced from "spend it on", which is the pick below.
MONEY_VERB_ASK = re.compile(
    r"\bwhat should (?:i|we) (?:tip\b|spend (?:on)(?! it)\b|budget for\b|"
    r"pay (?:for|a|an|my|the|him|her|them)\b)", re.I)
SPEND_IT_ON = re.compile(
    r"\bwhat (?:should|shall|do) (?:i|we) (?:spend|put) it (?:on|into|in)\b", re.I)
# The "for" is what makes a present an ask: a bare "i still need a present" says nothing about who
# or what for, and the question back it gets ("What kind of present do you usually go for?") is not
# a few things to choose between.
PRESENT_LOOKING = re.compile(r"\b(?:present|gift|pressie)s?\b[^?.!]{0,20}?\bfor\b", re.I)
# A note to write about a present is not a present to buy ("thank you letter for a present"), money
# back for one is not either ("i want a refund for a present i dont like"), and a present already
# given or being given ("my mum keeps buying gifts for the kids", "i got a present for my sister")
# is news rather than an ask.
NOT_A_PRESENT_ASK = re.compile(
    r"\b(?:thank(?:s| you)|refund|receipt|return(?:ed|ing)?|"
    r"buying|bought|got|gave|given|giving|keeps)\b", re.I)
# Two things either side of an "or" is a choice, whatever the verb: "what should i pay my landlord
# first the rent or the gas bill" is a pick, and no money verb makes it a figure.
ALTERNATIVES = re.compile(r"\bor\b", re.I)


def _names_alternatives(line, match):
    """Whether the clause the money verb is in puts two things either side of an `or`.

    Read clause by clause, so an `or` in a later sentence ("what should i tip a hairdresser? or is
    ten percent rude") does not take the ask away. Standing down rather than answering `PICK`,
    because the chain has already read the line and this is the arm for a line it read as a method.
    """
    window = line[max(0, match.start() - 80):match.end() + 80]
    seat = match.start() - max(0, match.start() - 80)
    spent = 0
    for part in re.split(r"[,;:?.!]", window):
        if spent <= seat <= spent + len(part):
            return bool(ALTERNATIVES.search(part))
        spent += len(part) + 1
    return bool(ALTERNATIVES.search(window))


def _the_line_once(understood):
    """The line as the person typed it, once.

    `fit._said` piles the reading's own copies of the line together - `norm`, `norm_text`, `clean`
    and `text` - which is right for a word searched anywhere and wrong for a shape read from the
    head of the line or the end of it.
    """
    for key in ("plain", "text", "clean"):
        value = understood.get(key)
        if isinstance(value, str) and value.strip():
            return " ".join(value.lower().replace("\u2019", "'").split())
    return ""


def the_shape_it_asks(understood, want):
    """`want`, corrected for the three asks above; every other line comes back as it was read."""
    if not isinstance(understood, dict):
        return want
    line = _the_line_once(understood)
    if not line:
        return want
    if SPEND_IT_ON.search(line):
        return PICK
    money = MONEY_VERB_ASK.search(line)
    if money and not _names_alternatives(line, money):
        return AMOUNT
    if want is None and PRESENT_LOOKING.search(line) and not NOT_A_PRESENT_ASK.search(line):
        return OPTIONS
    return want
