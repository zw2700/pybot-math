"""A statement that names something the person is weighing deserves more than a receipt.

People do not always arrive with a question. Half of the turns that reach the bot are somebody
thinking out loud about a thing they are about to decide:

    im looking at an electric blanket for the winter
    we are looking at a venue for the wedding
    im going for an interview at a bank
    its for a warehouse supervisor role

Every one of those named a real thing, and the bot answered with the same three words each time:

    Got it. Is there anything you'd like a hand with?
    Thanks for telling me - I'm here if you want to dig into any of that.
    I'm listening - say more if it helps.

The three receipts in `fallback_data.NEUTRAL` are the right answer to "the dog did a funny thing
today". They are the wrong answer to somebody standing in front of a decision, because the person
has said which decision and the bot has said nothing about it. STYLE.md's "Not knowing, honestly"
gives the shape that works: the part the bot does know, said plainly, then one question.

The part it knows here is not a fact about the thing - it has never seen the blanket, the venue or
the job - it is what that *kind* of decision turns on, which is true of every one of them: what
happens after you pay, which round of interviews, how many people are coming. So this file reads
the kind off the words the person used, names their thing back to them, gives the two or three
things that settle that kind of decision, and asks the one question a friend would ask next. It
names no price, no model and no date, because those are the facts it does not have.

Two rules kept it honest while it was written. Nothing is answered unless the line names a thing:
"its a diesel" and "its a supermarket" are left alone, because the kind cannot be read off them and
a frame for the wrong kind is worse than the receipt. And the kind has to be one of the three the
file knows (`bought`, `job`, `event`); anything else - a symptom, a move, a person - belongs to a
module that reads it properly, so the receipt stands rather than a guess.

It is a last resort: `bot/modules/greeting.py` calls it only where the reply it already has is one
of the three receipts, so any card, any entry and any real answer all keep the turn.
"""
import re

from . import pick

# The three receipts this file replaces, from `fallback_data.NEUTRAL`. A reply that is not one of
# them is somebody's answer and is left alone.
RECEIPTS = (
    "got it. is there anything you'd like a hand with?",
    "thanks for telling me \u2014 i'm here if you want to dig into any of that.",
    "i'm listening \u2014 say more if it helps.",
)

# What the person does with the thing: "looking at", "thinking about", "going for". A bare
# "looking for my keys" is a search, not a purchase, so the buying arm wants an article after it.
_WEIGHING = (r"(?:looking at|looking into|thinking about|thinking of|considering|weighing up|"
             r"deciding on|deciding between|going for|applying for|trying for|after)")
_WEIGH = re.compile(
    r"^\s*(?:so|and|but|ok|okay|well|oh|right)?\s*"
    r"(?:(?:i'?m|im|i am|we'?re|we are|she'?s|he'?s|they'?re|my (?:wife|husband|partner|mum|dad|"
    r"son|daughter|friend))\s+)?"
    r"(?:still\s+|also\s+|just\s+|now\s+|actually\s+)?"
    + _WEIGHING + r"\s+(?P<thing>[a-z0-9' -]{3,45}?)\s*$")
# "deciding between two laptops", "torn between a boiler and a heat pump": the person has already
# narrowed it to a kind, so the frame for that kind is exactly what they need.
_DECIDING = re.compile(
    r"\b(?:deciding|torn|choosing|stuck) (?:between|over)\s+(?:a|an|two|three|some|the)?\s*"
    r"(?P<thing>[a-z0-9' -]{3,45}?)\s*$")
# "looking for a new boiler", "looking for somewhere to stay" - the buying read of "looking for".
_LOOKING_FOR = re.compile(
    r"\b(?:looking for|shopping for|hunting for|asking about|going to see|getting a quote for|"
    r"getting quotes for)\s+(?:a|an|some|a new|new|some new)\s+(?P<thing>[a-z0-9' -]{3,45}?)\s*$")
# "its for a warehouse supervisor role", "its for a wedding", "its an electric blanket": the second
# turn of somebody who has just changed the subject to the thing itself.
_ITS_FOR = re.compile(
    r"^\s*(?:and\s+|oh\s+|well\s+)?(?:it'?s|its|they'?re|the one i want is)\s+"
    r"(?:for|to be for)\s+(?:a|an|the|our|my|some)\s+(?P<thing>[a-z0-9' -]{3,45}?)\s*$"
    r"|^\s*(?:and\s+|oh\s+|well\s+)?(?:it'?s|its)\s+(?:a|an)\s+(?P<bare>[a-z0-9' -]{3,45}?)\s*$")

# The kinds the file can speak about, as the words that can end the name of a thing: "a winter coat"
# is a coat, "an electric blanket for the winter" is a blanket, and "3 bed with a garden" is not a
# bed - a house, and this file has no business reading it. Every word is a whole word of the
# phrase, because "a medium egg from the fridge" matched "fridge" and got the buying frame once.
KINDS = {
    "job": ("job", "role", "position", "interview", "apprenticeship", "placement", "internship",
            "secondment", "promotion", "shift"),
    "event": ("wedding", "venue", "party", "birthday", "funeral", "christening", "anniversary",
              "reception", "celebration", "gathering", "conference", "shower", "bash"),
    "bought": ("boiler", "blanket", "car", "van", "bike", "bicycle", "laptop", "computer",
               "phone", "mobile", "tablet", "mattress", "sofa", "settee", "chair", "table",
               "desk", "pram", "pushchair", "cot", "seat", "washer", "machine", "fridge",
               "freezer", "oven", "cooker", "dishwasher", "dryer", "vacuum", "hoover", "kettle",
               "tv", "television", "monitor", "printer", "watch", "coat", "jacket", "boots",
               "boot", "tent", "caravan", "scooter", "mower", "lawnmower", "trimmer",
               "dehumidifier", "fryer", "microwave", "radiator", "pump", "panel", "burner"),
}
# What kind each word is, and its plural.
_KIND_OF = {}
for _kind, _words in KINDS.items():
    for _word in _words:
        _KIND_OF[_word] = _kind
        _KIND_OF[_word + "s"] = _kind

# Lines this file has no business reading. A symptom, a body word, a bill, a person or a legal
# question is read properly by another module and the receipt is the smaller fault there.
NOT_A_DECISION = re.compile(
    r"\b(?:pain|ache|hurts?|hurting|blood|bleeding|lump|rash|doctor|gp|nurse|hospital|surgery|"
    r"symptom|dose|doses|tablet|tablets|antibiotic|prescription|period|pregnant|pregnancy|"
    r"rent|rent arrears|evict\w*|deposit|landlord|council tax|benefits?|universal credit|"
    r"salary|wage|wages|payslip|court|solicitor|police|dead|died|dying|divorce|"
    r"my (?:mum|dad|son|daughter|husband|wife|partner|friend|brother|sister|baby))\b")

# A line that asks instead of telling is another module's: "what do you think of a wood burner" is
# a verdict ask, and it has its own reader (`a_place_nobody_can_see`).
ASKS = re.compile(r"^\s*(?:so|but|and|ok|okay)?\s*(?:what|which|how|when|where|who|why|is|are|"
                  r"was|were|do|does|did|can|could|should|would|will|shall|am)\b")

_OPENERS = ("a", "an", "the", "some", "my", "our", "a new", "new", "some new", "your", "his",
            "her", "their", "any")

# A thing said back to the person: the article has to agree, and a phrase the person already
# put an article on keeps its own.
_VOWELS = frozenset("aeiou")


def _plain(text):
    return re.sub(r"\s+", " ", str(text or "").lower().replace("\u2019", "'")).strip()


def _bare(phrase):
    said = _plain(phrase).strip(" .,!?-")
    for opener in sorted(_OPENERS, key=len, reverse=True):
        if said.startswith(opener + " "):
            said = said[len(opener) + 1:]
            break
    return said.strip(" .,!-")


# Words that open with a vowel letter and take "a": "a used car", "a one bed flat".
_A_NOT_AN = ("used", "unused", "useful", "one", "once", "usual", "uniform", "university", "euro",
             "european", "ubiquitous")


def _as_said(name, head):
    """The thing in the person's own words, with an article only if they gave none."""
    first = name.split()[0] if name.split() else ""
    if first in ("an", "a") or first.isdigit() or first in _POSSESSIVE:
        return name
    if first in ("the", "some", "any"):
        name = " ".join(name.split()[1:])
        first = name.split()[0] if name.split() else ""
        if not name:
            return ""
    if first.isdigit() or first in _POSSESSIVE or _is_plural(head):
        return name
    return _with_article(name)


def _with_article(phrase):
    """"electric blanket" -> "an electric blanket"; "two laptops" stays as it is.

    Every template puts the phrase after a word rather than in the subject of a verb, so a plural
    only has to keep its own shape instead of agreeing with anything.
    """
    said = _bare(phrase)
    if not said or said[0].isdigit() or _is_plural(said.split()[-1]):
        return said
    if said.split()[0] in _A_NOT_AN:
        return "a " + said
    if _is_plural(said.split()[0]) and len(said.split()) == 1:
        return said
    return ("an " if said[0] in _VOWELS else "a ") + said


# Trailing words that are not part of the thing: "its a new boiler apparently", "a job than i
# thought", "a car on saturday". "for" is not one of them, because it usually names the purpose and
# that is the part worth saying back - "an electric blanket for the winter".
_CUTS_HEAD = ("i think", "i reckon", "i suppose", "apparently", "though", "actually", "maybe",
              "probably", "instead", "than", "from", "on", "at", "in", "with", "about", "to",
              "and", "or", "for", "this week", "this weekend", "next week", "next month",
              "for now")
# What comes off the end of the name too, so "its a washer i think" is not said back as
# "a washer i think". Prepositions stay, because "a job at the library" reads well and
# "a car on saturday" is how the person said it.
_CUTS_NAME = ("i think", "i reckon", "i suppose", "apparently", "though", "than i", "and",
              "or", "this week", "this weekend", "next week", "next month", "for now")
# A thing the person already has is not a thing they are choosing: "im thinking of quittin my job",
# "im thinking of selling my car". Only the kinds where owning it is the point - a party for his
# birthday is still a party to arrange.
_ALREADY_HAVE = re.compile(r"\b(?:my|our|mine|your|their)\b")
_POSSESSIVE = ("my", "our", "mine", "your", "their", "his", "her", "its")
_ARTICLES = ("a", "an", "the", "some", "any")


def _is_plural(word):
    return word.endswith("s") and not word.endswith("ss")


def _cut_at(said, cuts):
    low = " " + said + " "
    at = len(said)
    for word in cuts:
        found = low.find(" " + word + " ")
        if -1 < found < at:
            at = found
    return said if at >= len(said) else said[:at].strip()


def _head_and_name(thing):
    """"a second hand bike for commuting" -> ("bike", "a second hand bike")."""
    raw = _plain(thing).strip(" .,!?-")
    said = _bare(raw)
    if not said:
        return "", "", ""
    head_part = _cut_at(said, _CUTS_HEAD)
    head = head_part.split()[-1].strip(".,!?-").lower() if head_part.split() else ""
    # The name keeps the article the person used - "a few jobs" is not "few jobs" - and only the
    # head drops it, because that is the word the kind is read from.
    return head, _cut_at(raw, _CUTS_NAME), head_part


def _read(said):
    """(kind, the thing as the person said it) or (None, None)."""
    if not said or ASKS.match(said) or NOT_A_DECISION.search(said):
        return None, None
    thing = None
    match = _WEIGH.search(said) or _DECIDING.search(said)
    if match:
        thing = match.group("thing")
    else:
        match = _LOOKING_FOR.search(said)
        if match:
            thing = match.group("thing")
        else:
            match = _ITS_FOR.search(said)
            if match:
                thing = match.group("thing") or match.group("bare")
    if not thing:
        return None, None
    # "its a bigger job than i thought" is a remark about the work, not a decision about a job.
    if re.search(r"\bthan\b", _plain(thing)):
        return None, None
    head, name, head_part = _head_and_name(thing)
    if not head or not name or len(name.split()) > 6:
        return None, None
    # "im thinking of getting a bike", "im thinking of buying a used car": a thing the person is
    # doing is not a thing they are deciding between, and "a getting a bike" is not a phrase.
    if head.split()[-1].endswith("ing") or name.split()[0].endswith("ing"):
        return None, None
    kind = _KIND_OF.get(head)
    # Only the part before the first preposition counts: "a new sofa for my front room" is a sofa
    # being chosen, "selling my car" is a car being let go.
    if kind in ("job", "bought") and _ALREADY_HAVE.search(head_part):
        return None, None
    if not kind:
        # The kind cannot be read off it, so whoever reads it properly keeps the turn: a frame for
        # the wrong kind reads as a bot that was not listening, which is worse than the receipt.
        return None, None
    return kind, name


_BOUGHT = (
    "With {thing}, what happens after you pay is what decides it: who repairs {it}, what the "
    "guarantee actually covers, and what the running cost is against the price. Get those three in "
    "writing, then compare. What will you be asking of {it}?",
    "For {thing}, the three questions a shop will not put on the label are who repairs {it}, what "
    "the guarantee covers and what the running cost is. Ask all three before you look at the "
    "price. Is it for every day or now and then?",
    "Buying {thing} comes down to use and after-sales: what you will ask of {it}, and who takes "
    "{it} back if something goes wrong. Settle those two and the shopping is the easy part. What "
    "is it for, mainly?",
)

_JOB = (
    "For {thing}, preparation decides more than the day itself: one story for each line of your "
    "CV, and two questions about what the job actually has to deal with. Then ask what the hours "
    "and the first three months look like. Which stage are you at?",
    "Before {thing}, the work that pays is two or three stories you could tell a friend, and one "
    "question you genuinely want answered - the person who asks it is the one they remember. Do "
    "you know who you will be talking to?",
    "With {thing}, find out what the job has to deal with before you decide what to talk about: "
    "the hours, the team, and what happened to the last person in the role. Have you seen the job "
    "description, or just the advert?",
)

_EVENT = (
    "For {thing}, the order that saves arguments is the date, then how many people, then what each "
    "one can cost - places quote by the head and by the day. Settle the first two before you look "
    "at any room, or the room decides them for you. How many are you expecting?",
    "With {thing}, the two numbers to pin down first are how many people and what each of them can "
    "cost, before you fall for a place; the date then follows whatever is left. Roughly how many?",
    "For {thing}, read it backwards: what you can spend, divided by the people coming, is what any "
    "place has to beat. Do that sum before you visit anywhere. How many are coming?",
)

_POOLS = {"bought": _BOUGHT, "job": _JOB, "event": _EVENT}


def pool(line):
    """Every phrasing for the kind of decision the line names, or None."""
    kind, thing = _read(_plain(line))
    if not kind:
        return None
    # The thing goes back into the reply as the person said it, with the article that suits it.
    head, name, _ = _head_and_name(thing)
    said = _as_said(name, head)
    # "im looking at cars" is not "a car": the pronoun has to agree too, so a plural gets "them".
    return tuple(template.format(thing=said, it="them" if _is_plural(head) else "it")
                 for template in _POOLS[kind])


def reads_as_a_receipt(reply):
    """True when the reply is one of the three receipts, with or without a question after it."""
    said = _plain(reply)
    return bool(said) and any(said.startswith(receipt) for receipt in RECEIPTS)


def answer_for(text, memory=None, reply=""):
    """A decision the person has just named, helped with, or None.

    `reply` is what the bot was going to say. Only a receipt is replaced, so a card, an entry, a
    module's own answer and the composer's own line all keep the turn.
    """
    if not reads_as_a_receipt(reply):
        return None
    options = pool(text)
    if not options:
        return None
    return pick(options, memory if isinstance(memory, dict) else {}, text)
