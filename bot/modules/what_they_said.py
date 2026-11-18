"""What somebody else said is a thing the person told the bot, and the chat says it back.

    we got quoted 400 for the fence
    what did they quote me                    before  I'm not sure about that one, sorry - a
                                                      quick search online will get you an answer
                                              now     You said 400.

    i told the garage about the noise and they said bring it in tuesday
    what did the garage say                   before  a card about getting the price in writing
                                              now     You said bring it in tuesday.

    i need a new boiler, british gas said 3 grand
    what did they say it would cost           before  the whole boiler card
                                              now     You said 3 grand.

The person is not asking about the world in any of these. They are asking for something they said
earlier in this chat, and the reply is in the chat: the line where somebody else was quoted, and,
when the ask names a figure, the figure out of that line.

`bot/memory/lineback.py` answers the recall asks that are about the person's own facts ("what did
i say my budget was"). This module is the same reading one step out - what a builder, a garage, a
vet or a child said - and it is here rather than in that module because the ask names no fact of
the person's own to look up: what it needs is the last line where the person quoted somebody.

The two things that were missing everywhere, and are the whole of the change:

- **A pronoun is not a detail.** Read as content, "they" in "what did they quote me" was the one
  word the ask had to share with a line, so it matched nothing and the turn went to a search
  hedge. The people words and the modals ("would", "could", "will", ...) are scaffolding in these
  asks in the same way "i" and "my" are, and come off before anything is matched.
- **A quote is a price.** "what did they quote me" names the kind of answer it wants - a figure -
  in the words people use for a builder's figure, so the figure is said back rather than the whole
  line.

It answers only these asks and passes on everything else: a line with no earlier turn behind it,
a line that names no speaker and no kind of answer, and a chat where the last thing said was a
question rather than somebody being quoted all keep the turn they had.
"""
import re

from ..memory import lineback

# In the recall band (README, "Routing"): a question about what this chat already holds is not a
# question about the world, so the card that fits its words does not answer a question nobody
# asked. It sits above the store's own readers (7000), because a fact the person gave about
# themselves is that store's to say, and this line is about somebody else's words.
PRIORITY = 7060

# The ask, in the words people use for it: "what did they quote me", "what did the garage say",
# "what did they say it would cost", "what did the vet say", "remind me what they said",
# "what did she tell you".
_A_THIRD_PARTY_ASK = re.compile(
    # The bare `[a-z]+` is for "what did the vet say" said as "what did vet say", and it must not
    # take "what did i say" (the store's own recall ask, `lineback.is_a_recall_ask`) or "what did
    # you say" (the bot's own last line): those are somebody else's to answer.
    r"\bwhat\s+did\s+(?:they|he|she|them|it|the\s+[a-z]+"
    r"|(?!(?:i|we|you|my|our)\b)[a-z]+)\s+"
    r"(?:say|said|tell\s+(?:you|me)|told\s+(?:you|me)|quote|quoted|charge|charged|offer"
    r"|offered|reckon|reckoned|suggest|suggested|text|texted|come\s+back\s+with|wants?)\b"
    r"|\bwhat\s+(?:did|have|has)\s+(?:they|he|she)\s+(?:said|told\s+(?:you|me))\b"
    r"|\bremind\s+me\s+what\s+(?:they|he|she)\s+(?:said|say|told\s+you|quoted|wanted)\b",
    re.I)

# The scaffolding of the ask: the people, the modals and the words that only point back. None of
# them is a detail, so none of them is what the ask shares with a line.
_NOT_A_DETAIL = frozenset("""
what which who whom whose when where why how say said saying says tell told telling mention
mentioned quote quoted quotes charge charged offer offered reckon suggested text texted remind
me my our we us i you your it its that this these those was were is are be been being did do does
done about of to the a an and or for with in on at by as if so but not any some please just really
thing things one ones kind sort name called exact exactly already again
they them their theirs he him his she her hers
would could should shall will may might must can cant cannot itll id
""".split())

# The kind of answer an ask wants when it names one, in the words people use for it. A quote is a
# price: "what did they quote me" and "what did it cost" are the same question about a figure.
_A_KIND = {
    "cost": "figure", "costs": "figure", "price": "figure", "quote": "figure",
    "quoted": "figure", "charge": "figure", "charged": "figure", "offer": "figure",
    "offered": "figure", "pay": "figure", "paid": "figure", "much": "figure", "many": "figure",
    "number": "figure",
}

# Somebody other than the person speaking: "the garage said", "they told me", "she reckoned".
# Never "i told" or "we asked": those are the person's own act, and what they said or asked is not
# somebody else's words - "i told my boss i was quitting" is the person's line, not the boss's.
_SOMEBODY_SPOKE = re.compile(
    r"\b(?!i\b|we\b)(?:they|he|she|the\s+[a-z]+|[a-z]+)\s+"
    r"(?:said|says|say|told|tells|quoted|asked|charges?|offer(?:s|ed)?|reckons|thinks|texted|called"
    r"|wants)\b", re.I)

# A figure with the way people write money: "400", "3 grand", "£2,000", "1.5k".
_A_FIGURE = re.compile(
    r"(?:£|\$|€)\s?\d[\d,.]*\s?(?:k\b|m\b)?"
    r"|\b\d[\d,.]*\s?(?:k\b|grand\b|thousand\b|quid\b|pounds?\b|p\b)"
    # A figure written bare is still the figure: "we got quoted 400 for the fence" is answered
    # "You said 400." rather than with the whole line said back.
    r"|\b\d[\d,.]*\b", re.I)

_QUESTION = re.compile(r"^\s*(?:what|which|who|when|where|why|how|should|shall|can|could|would"
                       r"|do|does|did|is|are|was|were|will|have|has|am)\b", re.I)

# The words a person uses to hand on what somebody said, and what comes after them: in "i told the
# garage about the noise and they said bring it in tuesday", the answer is "bring it in tuesday".
# Said back on its own it is the quoted words; the whole line said back buries them in the person's
# own framing ("i told the garage about the noise and ...").
_REPORTING_VERB = re.compile(
    r"\b(?P<who>(?:[a-z]+\s+)?[a-z]+)\s+"
    r"(?:said|says|telling\s+me|told\s+me|tells\s+me|reckoned|texted|quoted|charged|offered"
    r"|asked|wants|wanted|asks|needs|went)\b\s+(?:that\s+)?"
    r"(.+)$", re.I)

# The subjects that are the person speaking, whose own words are not somebody else's report.
_THE_PERSON = frozenset(("i", "we", "me", "us", "im", "ive", "id"))

# A figure with the way people write money, and a unit that makes a figure a length rather than a
# price ("the car is 3 years old" is not a quote of 3).
_A_MONEY = re.compile(r"[£$€]|\b\d[\d,.]*\s?(?:k|m|grand|thousand|quid|pounds?|p)\b", re.I)
_A_UNIT_AFTER = re.compile(
    r"^\s*(?:years?|yrs?|months?|weeks?|days?|hours?|hrs?|minutes?|mins?|miles?|km|kilometres?"
    r"|kilograms?|kg|stone|feet|foot|inches|times?|percent|%|o'?clock)\b", re.I)


def _details(text):
    """The content words of a line, as flat words: what it says that is not scaffolding."""
    return {word.strip("'") for word in re.findall(r"[a-z']+", str(text or "").lower())
            if word.strip("'") not in _NOT_A_DETAIL and len(word.strip("'")) > 1}


def _the_kind_of_answer(said):
    """The kind of answer the ask names - "figure" for a price - or "" when it names none."""
    for word in re.findall(r"[a-z']+", str(said or "").lower()):
        kind = _A_KIND.get(word.strip("'"))
        if kind:
            return kind
    return ""


def _the_last_somebody_spoke(said, memory):
    """The last earlier line where the person quoted somebody, or None."""
    wanted = _details(said)
    kind = _the_kind_of_answer(said)
    for line in reversed(lineback.the_lines(memory)):
        if _QUESTION.search(line) or lineback.is_a_recall_ask(line):
            continue  # an ask for the thing is not the thing
        if not _SOMEBODY_SPOKE.search(line):
            continue
        # An ask that names the speaker or the subject ("what did the vet say") shares that word
        # with the line it wants. An ask that names only the kind of answer ("what did they say
        # it would cost") does not have to: the figure in the line is the answer to it.
        if kind or not wanted or (wanted & _details(line)):
            return line
    return None


def _the_reported_clause(line):
    """What somebody else said, when the line hands it on in a clause, or "".

    Only a verb whose subject is somebody other than the person reports somebody else's words:
    "i told my boss i was quitting" and "i asked for a raise and got told no" say what the person
    did, not what the boss said, and the clause after them is the person's own line.
    """
    clause = ""
    for match in _REPORTING_VERB.finditer(line):
        who = match.group("who").split()[-1].strip("',")
        if who in _THE_PERSON:
            continue
        clause = match.group(2).strip()
    clause = clause.rstrip(" .!?,")
    # "the vet asked for 60" hands on "for 60"; the figure is the thing said, not the preposition.
    clause = re.sub(r"^(?:for|to|about|of|at)\s+(?=(?:£|\$|€)?\s?\d)", "", clause, flags=re.I)
    words = clause.split()
    if not words or len(words) > 14:
        return ""  # a long tail is the rest of the line, not the thing that was said
    if _QUESTION.search(clause) or not re.search(r"[a-z0-9]", clause, re.I):
        return ""
    return clause


def _the_figure_the_line_gave(line):
    """The figure in the line that answers an ask for a price, or "".

    A bare number is a price only when it is the only figure in the line: "we got quoted 400 for
    the fence" is one, and "the car is 3 years old and they said bring it in tuesday" is an age.
    Where the ask names a price and the line holds more than one figure, the money one is the
    answer, and a line with two of them says nothing for certain.
    """
    figures = [found for found in _A_FIGURE.finditer(line)
               if not _A_UNIT_AFTER.match(line[found.end():])]
    money = [found for found in figures if _A_MONEY.search(found.group(0))]
    if len(money) == 1:
        return money[0].group(0).strip()
    if not money and len(figures) == 1:
        return figures[0].group(0).strip()
    return ""


def respond(text, memory):
    said = lineback.flat(text)
    if not said or not _A_THIRD_PARTY_ASK.search(said):
        return None
    line = _the_last_somebody_spoke(said, memory)
    if not line:
        return None
    if _the_kind_of_answer(said) == "figure":
        figure = _the_figure_the_line_gave(line)
        if figure:
            return "You said " + figure + "."
    clause = _the_reported_clause(line)
    if clause:
        return "You said " + clause + "."
    # Nothing was handed on in a clause and no figure was quoted: the line is the person's own act
    # ("i told my boss i was quitting") or a figure that is a length, so saying it back is the bot
    # repeating their line at them. The turn goes back to whoever answers the line itself.
    return None
