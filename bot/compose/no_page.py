"""How to handle a person or a day of their own: there is no page, so name the parts.

Three lines from the fallback census, all the same shape:

    how do i handle christmas        -> "I don't know enough to answer that honestly. A search
    how do i manage my mum           ->  should sort you out quickly"
    how do i sort my life out        -> the same hedge

A search cannot answer any of them, and that is not a gap in the search: how to handle Christmas
depends on the money, the days and who is in the room, and how to manage somebody's mum depends
on the mum and on the person asking. There is nothing written down to go and read. The hedge is
worse than useless here - it sends a person looking for a page that does not exist.

What a friend does is the one thing that is always true: say the ask is too big for one answer,
name the two or three parts it is really made of, and ask which one to take first. That is a
question a person can answer in four words, and it turns a shrug into a conversation.

Three kinds, and only these:
  - "person"   - a person of theirs ("how do i deal with my ex", "how do i manage my mum")
  - "occasion" - a named day or season ("how do i handle christmas", "how do i get through
                 half term")
  - "whole"    - no thing at all ("how do i sort my life out", "how do i get through the week")

It never invents the answer, and it never guesses at a thing it was not asked about: an ask with
no "handle/deal with/manage/cope with/get through/sort out" in it is left alone, so every how-to
with a real method (`how do i clean the filter`, `how do i drain the pasta`) and every body or
dose question (`how do i manage the pain`) keep the reply they have.
"""
import re

# A thing to handle has to be named as one of these; without one the line is a how-to with a
# method behind it, which is the knowledge base's.
DOING = re.compile(
    r"\bhow\s+(?:do|can|could|should|would)\s+(?:i|we|you)\s+"
    r"(?:handle|deal\s+with|cope\s+with|manage|get\s+through|get\s+past|"
    r"sort\s+(?:[\w']+\s+){0,3}out|live\s+with|put\s+up\s+with|survive)\b", re.I)

# The thing being handled, when it is a person of theirs.
FEMALE = (r"(?:mum|mom|mam|mummy|mother|sister|daughter|wife|"
          r"girlfriend|nan|nana|grandma|granny|aunt|aunty|niece|stepmum|stepmother)")
MALE = (r"(?:dad|daddy|father|brother|son|husband|boyfriend|"
        r"grandad|granddad|grandpa|uncle|nephew|stepdad|stepfather)")
PLURAL = (r"(?:kids|children|parents|in-laws|brothers|sisters|twins|boys|girls|neighbours|"
          r"neighbors)")
PERSON = re.compile(
    r"\b(?:handle|deal\s+with|cope\s+with|manage|live\s+with|put\s+up\s+with|survive|sort\s+out)"
    r"\s+(?P<who>(?:my|our|his|her|their)\s+(?:" + FEMALE + r"|" + MALE + r"|" + PLURAL
    + r")(?:\s+in\s*-?\s*law)?"
    r"|my\s+ex|her\s+ex|his\s+ex|the\s+ex|my\s+partner|the\s+kids|the\s+children)\b", re.I)

# A day, a season or a whole stretch: the thing people say they cannot face.
OCCASION_WORDS = (r"christmas|xmas|the\s+holidays|half\s+term|the\s+summer\s+holidays|"
                  r"birthdays?|the\s+birthday|a\s+birthday|the\s+wedding|a\s+wedding|"
                  r"mother'?s\s+day|father'?s\s+day|new\s+year|new\s+years\s+eve")
# A day with a table and a guest list is one kind of problem; a week with no school in it is
# another, and "whose place is it at" is nonsense about half term.
STRETCH_WORDS = re.compile(r"\b(?:half\s+term|the\s+holidays|the\s+summer\s+holidays|"
                           r"the\s+school\s+holidays|the\s+week\s+off)\b", re.I)
OCCASION = re.compile(
    r"\b(?:handle|deal\s+with|cope\s+with|manage|get\s+through|get\s+past|sort\s+out|"
    r"live\s+with|survive)\s+(?:the\s+|a\s+|my\s+|this\s+)?(?P<what>" + OCCASION_WORDS + r")\b",
    re.I)

# No thing at all: the person's whole life, or a stretch of it. The words can come after the
# doing rather than straight after it ("sort my life out", "get through another week of it"), so
# this is a plain search over a line that has already been read as one of the doings.
WHOLE = re.compile(
    r"\b(?:it\s+all|everything|my\s+life|life|the\s+week|the\s+month|the\s+days|"
    r"all\s+of\s+it|another\s+week|the\s+whole\s+thing)\b", re.I)

# A body is the GP's, a dose is a pharmacist's, and neither is a thing to be asked which part
# of it to take first. Every pool here hands work back; a body ask needs a person, not a plan.
BODY = ("pain", "ache", "hurts", "hurting", "sore", "symptoms", "dose", "dosage", "tablets",
        "meds", "medication", "antibiotics", "insulin", "bleeding", "bleed", "rash", "lump",
        "breath", "breathing", "chest", "sleep", "insomnia", "withdrawal", "detox", "alcohol",
        "drinking", "grief", "grieving", "bereavement", "suicidal", "self harm", "panic")

# A job in the world has a method in the knowledge base; so does a word for a thing to buy. And a
# how-to that names the doing itself ("how do i get through to the council") is a phone call.
NOT_THIS = re.compile(
    r"\b(?:clean|cleaning|fix|fixing|fit|fitting|wire|wiring|bleed\s+the|install|assemble|"
    r"unblock|drain|paint|paint\s+over|plumb|tile|grout|service|reset|reinstall|"
    r"renew|apply|book|claim|fill\s+in|cancel|return|refund|"
    r"get\s+through\s+to|get\s+(?:to|in\s+touch\s+with))\b", re.I)

PROSE = {
    "person": (
        "There's no way to handle a person whole, so take one behaviour: the thing {who} will "
        "keep doing, and what you'll do when it happens again. Say it once, at a calm moment, "
        "about the time together rather than about {them} ('I need to be home by nine'), and keep "
        "that time shorter than feels natural - it is the part that helps most. Where the answer "
        "has to come from someone professional, the GP surgery and Citizens Advice are the two "
        "doors.",
        "Nobody has written the page for {who}, but the working part is the same for everyone: "
        "pick the one thing that actually goes wrong, say it plainly once, and decide beforehand "
        "what you'll do if it happens again. Shorter stretches together, with something to do, "
        "work better than a long one you both dread. A carers' helpline or your GP surgery will "
        "take the specific version.",
        "What usually helps is to stop trying to change {who} and change the shape of the time "
        "together instead: shorter, with something to do, one subject you can both stand, and one "
        "warm ordinary thing in it. Say your limit once, in advance, rather than in the moment. If "
        "it needs a professional - money, a diagnosis, a social worker - Citizens Advice and the "
        "GP surgery are where to ask.",
    ),
    "occasion": (
        "There's no one answer for {what}, because it is really three questions: what you can "
        "spend, whose place it is at, and which people you can't be in a room with. Settle the "
        "first two this week and the third gets much smaller. If money is the tight part, the "
        "budgeting pages at Citizens Advice walk through it free.",
        "Most of {what} comes down to money, place and who is in the room, so take them in that "
        "order: a figure you can spend without flinching, where it happens, and the one or two "
        "people you'd rather not sit next to. Then pick one thing you actually want from the day "
        "and protect it - that is what makes it feel like yours.",
        "Most of {what} is settled by three things: the money, the days themselves, and who is in "
        "the room. Fix a budget first, then decide the days, and shorten the part with the people "
        "you find hard. Citizens Advice goes through the money side free if it is the tight bit.",
    ),
    "stretch": (
        "With {what}, it is mostly about days rather than plans: pick two of them for something "
        "out of the house, leave the rest loose, and line up the one thing that gets everyone up "
        "in the morning. Ask whoever might help - a grandparent, a friend - this week rather than on the "
        "Monday, and your council lists the free activities by area.",
        "What makes {what} work is a shape to the days: mornings out, afternoons quiet, and "
        "screens at a stated time rather than an argument. Decide the two days you'll go "
        "somewhere and check the free stuff now - the council's holiday pages and the local "
        "leisure centre are where those lists are.",
        "Nobody gets {what} perfect, but the days go better with the mornings fixed: somewhere to "
        "be by ten, lunch sorted the night before, and one calm thing for the afternoon. The rest "
        "can be loose. If money is the tight part, the council's free-activity lists and Citizens "
        "Advice are the two places to look.",
    ),
    "whole": (
        "That is too big to answer as one thing, so start with the load: write down everything "
        "that's on you, then mark the two that make the rest worse - for most people that is "
        "money and sleep. Fix one of those this week with the smallest real step, a budget you "
        "can see or a bedtime you keep. If it is money, housing or a benefit, Citizens Advice "
        "will go through your actual numbers free.",
        "Nobody can hand you the whole of that, but the order is the same for most people: "
        "sleep, money, then the thing you keep putting off. Pick the loudest one, take the "
        "smallest real step this week, and tell one person what you're doing - that is what "
        "keeps it moving. Your GP is the right next stop if it is your mood as much as the "
        "practical side.",
        "The honest version is that there is no plan for all of it at once, but there is an "
        "order: sleep, money, then one thing you can finish. Write the list, cross off what is "
        "not actually yours to do, and pick one item small enough to do this week. Your GP or "
        "Citizens Advice are where the parts that need a professional go.",
    ),
}

FEMALE_WORDS = tuple(re.findall(r"[a-z-]+", FEMALE))
PLURAL_WORDS = tuple(re.findall(r"[a-z-]+", PLURAL))


def _bare(text):
    return re.sub(r"\s+", " ", (text or "").strip()).strip(" .!,").lower()


def _who(match):
    """The person as they were named, and the pronoun that goes with them."""
    phrase = (match.group("who") or "").strip()
    # the person says "my mum"; the bot says "your mum". "the kids" is "your kids" too.
    phrase = re.sub(r"^(?:my|our|the)\s+", "your ", phrase)
    words = [w for w in re.findall(r"[a-z-]+", phrase.lower())]
    them = "them"
    if not any(w in PLURAL_WORDS for w in words):
        if any(w in FEMALE_WORDS for w in words):
            them = "her"
        elif any(w in ("ex", "partner") for w in words):
            them = "them"
        else:
            them = "him"
    return phrase, them


# The ask is about the person or the day itself, not about a job you do with them: "how do i
# handle the kids at bath time" has a method (and a bath), and the tail is what says so. So the
# line has to end after the thing it is about, give or take a word about the circumstances.
TAIL_OK = frozenset((
    "", "on my own", "on my own now", "by myself", "alone", "now", "anymore", "any more",
    "these days", "at the moment", "this year", "this time", "again", "all of it",
    "and my job", "and work",
))


def _tail_ok(match, line):
    tail = line[match.end():].strip(" .!,")
    # "when she's like that", "when he's been drinking" is the circumstance, not a task: the ask
    # is still about the person.
    return tail in TAIL_OK or tail.startswith("when ")


def reads(text):
    """The kind of ask this is - "person", "occasion", "whole" - or None."""
    line = _bare(text)
    if not line or not DOING.search(line):
        return None
    if NOT_THIS.search(line):
        return None
    if any(re.search(r"\b" + word + r"\b", line) for word in BODY):
        return None
    person = PERSON.search(line)
    if person and _tail_ok(person, line):
        return "person"
    occasion = OCCASION.search(line)
    if occasion and _tail_ok(occasion, line):
        if STRETCH_WORDS.search(line):
            return "stretch"
        return "occasion"
    if WHOLE.search(line):
        return "whole"
    return None


def reply_for(text, memory=None):
    """The parts it is made of and the one question back, or None when this is not the ask."""
    kind = reads(text)
    if not kind:
        return None
    turns = len([t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)])
    line = PROSE[kind][turns % len(PROSE[kind])]
    if kind == "person":
        who, them = _who(PERSON.search(_bare(text)))
        return line.format(who=who, them=them)
    if kind in ("occasion", "stretch"):
        what = OCCASION.search(_bare(text)).group("what")
        said = line.format(what=what)
        # a filled-in day wears a capital when it opens the sentence ("Half term is ...")
        return said[0].upper() + said[1:]
    return line
