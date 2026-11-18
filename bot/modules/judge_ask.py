"""A line asking whether this bot judges people is answered, not searched.

"do you judge people" and "do you judge people by their past" were answered "That's beyond what I
know well, sorry. Searching for it will turn up better sources than I can offer" - an answer about
a search engine for a question about the bot. "are you judging them" the same. Nobody owned it:
the about-the-bot reader stops short of the judging word, and the composer's own judging pool is
written for the person being told ("Not judging, no. Say it plainly"), not for a question about
people in general.

The reading is narrow on purpose, and it is a floor. On today's main the composer already answers
the plain plea to the bot ("dont judge me", "will you judge me", "please dont judge me for it") and
the person who holds the judgement ("i feel like everyone is judging me", "my mum would judge me"),
so this module is not asked about them at all: it reads only the bot being asked what it makes of
people, and it asks the composer first, so a line the composer answers whole keeps its turn.

Anything else stands down and goes on to whatever answered it before: a thing being judged ("dont
judge the cake by its look", "do you judge a book by its cover"), a court ("the judge said i have to
go to court"), a standard of judgement with no people in it ("judging by the weather"), and somebody
else holding the judgement ("are people judging me").
"""
import re

from ..compose import fallback
from . import greeting

# A floor module: above `greeting` (-1000), which is what answers these lines with the search
# hedge, and below everything with an answer of its own - `answers` (0), `chat` (300), the store,
# the topics and the safety band. Nothing here is worth a turn that had a card behind it.
PRIORITY = -500

# The bot being asked what it makes of people: "do you judge people", "do you judge people by
# their past", "would you judge someone for that", "are you judging them", "do you judge a person
# by their past", "dont judge people". The bot is the one being asked, so the subject is "you".
JUDGE_PEOPLE_ASK = re.compile(
    r"\b(?:will|would|do|did|are|r|can|could)\s+(?:you|u)\s+"
    r"(?:just\s+|really\s+|actually\s+|even\s+|ever\s+|not\s+)?judg\w*\s+"
    r"(?:(?:a|the|other)\s+)?"
    r"(?:people|person|persons|someone|somebody|anyone|anybody|folk|folks|others|them|him|her)"
    r"\b"
    r"|\b(?:dont|do not|never)\s+judg\w*\s+"
    r"(?:(?:a|the|other)\s+)?(?:people|anyone|anybody|someone|somebody|person|folk|folks)\b",
    re.I)

# A thing named after the verb is the thing being judged, not people: "dont judge the cake by its
# look", "do you judge my cake", "the judge said i have to go to court". An article is only a thing
# when a thing follows it - "do you judge a person by their past" is still people.
JUDGE_A_THING_NOT_PEOPLE = re.compile(
    r"\bjudg\w*\s+(?:the|this|that|it|my|his|its)\b"
    r"|\bjudg\w*\s+(?:a|an)\s+(?!person\b|people\b|human\b|child\b|kid\b|man\b|woman\b"
    r"|guy\b|girl\b|boy\b|teen\w*\b)\w+",
    re.I)
# "judging by the weather", "judged on looks": the standard of judgement with no people in it.
# "do you judge people by their past" is not this - there the people are the object, and the past
# is how the question says they are judged.
JUDGE_BY_A_STANDARD = re.compile(r"\bjudg(?:ing|ed)\s+(?:by|on|from)\b", re.I)

# Somebody else holds the judgement: "i feel like people are judging me", "my mum would judge me".
# The person is not asking the bot what it makes of people, and answering "I try not to" answers a
# question nobody asked.
JUDGE_SOMEONE_ELSE = re.compile(
    r"\b(?:everyone|everybody|people|they|them|someone|somebody|nobody|no one|parents|friends|"
    r"family|colleagues|strangers|relatives|neighbours)\b(?:\s+\w+){0,3}\s+judg\w*"
    r"|\b(?:my|his|her|their|our|your)\s+(?:\w+\s+){0,2}judg\w*"
    # the same third person typed as a contraction
    r"|\b(?:she|he|they|it|shell|hell|theyll|theyd|shed|shes|hes)\b(?:\s+\w+){0,3}\s+judg\w*"
    r"|\b(?:the|a|my|his|her|our|their|your)\s+(?:\w+\s+){0,2}to\s+judg\w*\s+(?:me|us)\b",
    re.I)

PEOPLE_LINES = (
    "I try not to. Nobody gets a verdict off me - what people tell me stays here. What's on your "
    "mind?",
    "No. I've no interest in scoring people - say whatever you came to say.",
    "I don't, no. Whatever you tell me I take as it comes, so where are we starting?",
)

EMPTY_HEADS = (
    "got it", "noted:", "thanks for telling me", "i'm listening", "i am listening",
    "that's your call", "that sounds like a lot", "sorry, i don't know", "i don't know enough",
)


def _says_nothing(said):
    """True when a reply is one of the pools that tell the person nothing."""
    said = str(said or "")
    if not said:
        return True
    if fallback._is_a_hedge(said):
        return True
    return said.lower().startswith(EMPTY_HEADS)


def _the_composer_says_nothing(text, memory):
    """True when the composer's own answer for this line is a nod, a receipt, a hedge or an echo.

    The composer reads the thread and answers most judging lines better than a reassurance pool
    ("i feel like a bad mum, dont judge me" gets the card about saying the one thing plainly), so
    its answer is asked first and this module only fills the turns where it says nothing at all.
    """
    for reply in (greeting.respond(text, memory), fallback.reply_for(text, memory)):
        if reply and not _says_nothing(reply):
            return False
    return True


def reads_it(text):
    """True for the lines this module reads whole: the bot asked what it makes of people."""
    said = " ".join(str(text or "").lower().split())
    if not said:
        return False
    if not JUDGE_PEOPLE_ASK.search(said):
        return False
    return not (JUDGE_A_THING_NOT_PEOPLE.search(said) or JUDGE_BY_A_STANDARD.search(said)
                or JUDGE_SOMEONE_ELSE.search(said))


def respond(text, memory):
    """One of the people lines, never the one the bot has just said, or None."""
    # The reading is asked first and it is cheap: the composer is only run for a line this module
    # would answer, not on every turn. (@quick-iguana)
    if not reads_it(text):
        return None
    if not _the_composer_says_nothing(text, memory):
        return None
    turns = (memory or {}).get("turns") or []
    last = str(turns[-1].get("bot") or "") if turns else ""
    start = sum(ord(ch) for ch in " ".join(str(text or "").lower().split()))
    for step in range(len(PEOPLE_LINES)):
        line = PEOPLE_LINES[(start + step) % len(PEOPLE_LINES)]
        if not last or line[:24] not in last:
            return line
    return PEOPLE_LINES[start % len(PEOPLE_LINES)]
