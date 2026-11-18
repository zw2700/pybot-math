"""A birthday already on file, and the line that asks what to do for it.

"my sister turns 30 on saturday" is stored as a person with an age and a day still to come
(`memory["others"]`, `{"who": "sister", "age": 30, "turns": "on saturday"}`). The next line,
"i want to plan something", asks for a plan for exactly that, and on main the store was not read
at all: the line got a question back ("Good thing to take on. What's the first step from where
you are?") or a plan for a plain Saturday ("Pick two things and put them in the diary by Friday:
... a market on a Saturday morning"). Neither is a 30th, and the person had already said whose
day it was.

So this reads the occasion the store holds and answers for it: the one thing worth booking, the
one thing worth doing today, and the reason. Nothing is invented about the person - only their
name for them, the age and the day they gave - and the plan is the ordinary one that works for a
group at short notice (a table with a time on it, the guest list told today).

Two gates, so it cannot take a turn it does not know:

* the line asks for a plan and names nothing else ("i want to plan something", "any ideas",
  "what should we do", "help me sort something out"). A line that carries its own subject
  ("how do i plan my diet", "i want to plan the route", "ideas for tea") is somebody else's,
  because what it is about is on the line and not in the store.
* the store holds exactly one person with an age and a day still to come. Two is not one thing
  to plan, and an age with no day ("my mum is 70") is a fact rather than a date.
"""
import random
import re

# A day still to come, as the store keeps it: the day words people use for a birthday. A figure
# on its own ("3rd") counts only with a month or a day word beside it, because "30" is the age.
_DAY_TO_COME = re.compile(
    r"\b(?:on\s+)?(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"tonight|tomorrow|today|this weekend|this saturday|the weekend|"
    r"next week|next weekend|next month|next year|"
    r"in \d+ (?:days?|weeks?|months?)|"
    r"\d{1,2}(?:st|nd|rd|th)? (?:of )?(?:january|february|march|april|may|june|july|august|"
    r"september|october|november|december)|"
    r"(?:january|february|march|april|may|june|july|august|september|october|november|"
    r"december)(?: \d{1,2}(?:st|nd|rd|th)?)?|"
    r"(?:on )?the \d{1,2}(?:st|nd|rd|th))\b")

# The lines that ask for a plan for the thing in hand rather than about the world. A plan verb or
# a plan noun, or the everyday "something nice for it" phrasing.
_ASKS_FOR_A_PLAN = re.compile(
    r"\b(?:plan|plans|planning|arrange|arranging|organi[sz]e|organi[sz]ing|ideas?|"
    r"something|anything|celebrate|throw (?:her|him|them|a)|do (?:for|to mark))\b|"
    r"\b(?:what|how) (?:should|shall|can|could) (?:we|i) do\b|\bwhat do (?:we|i) do\b")

# A subject of its own: a noun the plan would be about, other than the person the day is for.
# "i want to plan a surprise" is still this occasion; "i want to plan my diet" is not.
_OWN_SUBJECT = re.compile(
    r"\b(?:diet|workout|exercise|training|budget|money|finances?|meals?|food|tea|dinner|"
    r"lunch|breakfast|shopping|garden|shed|loft|move|moving|house|holiday|trip|route|journey|"
    r"revision|study|work|job|business|wedding|funeral|birth|baby|contract|rota|shift|"
    r"packing|pack|list|calendar|week|month|year|term)\b")

# "what day", "when is", "what shall we call it": a question about the plan, not a request for
# one. The occasion is already known, so a when/where ask is answered from the store, not here.
_NOT_A_PLAN_ASK = re.compile(
    r"\b(?:what day|which day|when is|when's|where is|where's|how old|what time|who is|"
    r"how much|how many|why|what do you mean|what did you mean)\b"
    # "what could we do that she would actually like" is a question about what the person likes,
    # and the store keeps no preferences, so the plan stands aside rather than book a table for
    # somebody who does not want a fuss.
    r"|\bwould (?:actually |really )?(?:like|love|enjoy|prefer|want)\b")

# The plan itself, in the order a person does it: one thing booked, one thing said today, and the
# reason. `{day}` is the whole phrase - "your sister's 30th on Saturday", "your 40th next month",
# "your birthday on 3rd May" - so a day kept without an age still reads as a sentence.
PLANS = (
    "For {day}, book the one thing that needs a table or a ticket, because "
    "everything else on the night can be decided on the spot. Then send the time and place to "
    "everyone you want there today, so nobody is left waiting to hear.",
    "Get one firm thing in the diary for {day} first - a table for the group at "
    "seven, or tickets - and keep the rest of it loose. Send the details round today; a birthday "
    "falls apart at the 'so what are we doing' stage, not on the night.",
    "The thing that makes {day} work is one booking with a time on it: a table at "
    "seven, then somewhere with music after. Text the people you want there today with both, and "
    "ask them who else they would want in the group.",
    "For {day}, put a time on it and tell people today: a table booked for seven, "
    "and a second place to go after that needs no booking. Ask what they would actually like to "
    "eat first, so the booking is somewhere they want rather than somewhere free.",
)

# A child's birthday is a different plan: a hall or a slot to book, the whole class or the close
# friends, and a cake that is ordered rather than a table that is booked.
CHILD_PLANS = (
    "For {day}, book the thing that fills up first - a hall, a soft play slot, a "
    "bowling lane - and send the invitations the same day, because a children's party is decided "
    "by who can come. Order the cake when you book, so it is not the thing left to Friday.",
    "Get the slot booked for {day} before you think about anything else: the "
    "weekend ones go first. Then ask them which two friends matter most, invite those and a few "
    "more, and keep it to two hours - that is as long as a party that size lasts.",
    "For {day}, one booked place and a short guest list beats a big plan: a hall or "
    "a soft play slot for two hours, food that is easy to hand round, and a cake ordered today. "
    "Ask the parents to stay if the children are small.",
)

# Short notice needs a smaller plan: a day or two out, nothing new can be booked for a group.
_SOON = re.compile(r"\b(?:tonight|tomorrow|today|this weekend|this saturday|in \d+ days?)\b")
SOON_PLANS = (
    "It is close, so keep it small and certain for {day}: book a table for the "
    "people who can actually come, tell them the time today, and let the rest be drinks after. "
    "A short-notice birthday works on who turns up, not on the plan.",
    "For {day}, ring the place rather than booking online - a table for six at "
    "short notice is usually a phone call - and send one message with the time and the address "
    "to everyone today.",
)


def _ordinal(age):
    """30 -> "30th", 21 -> "21st", 22 -> "22nd", 23 -> "23rd"."""
    if 10 <= age % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(age % 10, "th")
    return "%d%s" % (age, suffix)


def _whose(who):
    """"sister" -> "your sister's"; a name is said as it is: "Jess" -> "Jess's"."""
    who = str(who or "").strip()
    if not who:
        return ""
    low = who.lower()
    if low.startswith(("your ", "my ")):
        low = low.split(" ", 1)[1]
    # A name is the person's own word for somebody, so it is said back as it was typed, without
    # the "your" that belongs to a relation; the relation is lower case in the store.
    if who[:1].isupper():
        return who + "'s"
    return "your " + low + ("'" if low.endswith("s") else "'s")


# A month with no day in it is said with "in": "my 50th is in June" and not "on June".
_A_MONTH_ON_ITS_OWN = re.compile(
    r"january|february|march|april|may|june|july|august|september|october|november|december")

# The age a birthday line gives when the store kept it as words rather than a number:
# "my daughters birthday is next month she turns 7" is kept as `{"who": "daughter", "birthday":
# "next month she turns 7"}`, and "im turning 40 next month" as the plan text alone.
# A day in the person's own words is a birthday only when the line says so: "im going to rome in
# october" has a month in it and is a trip, and the plan for it is not a party.
_BIRTHDAY_IN_PLAN = re.compile(
    r"\b(?:birthday|bday|turning|turns?|\d{1,2}\s*-?\s*(?:this|next)\s*(?:month|week|year))\b"
    r"|\b(?:i'?m|im|i am) (?:\d{1,2}|turning \d{1,2})\b|\bmy \d{1,2}(?:st|nd|rd|th)\b")

_TURNS_AGE = re.compile(r"\bturns? (\d{1,2})\b|\bturning (\d{1,2})\b"
                        r"|\bmy (\d{1,2})(?:st|nd|rd|th)\b"
                        r"|\b(\d{1,2})(?:st|nd|rd|th)\s+(?:birthday|bday)\b")


def _the_day(when):
    """Just the day phrase out of a birthday line, as the reply says it.

    "my daughters birthday is next month she turns 7" keeps the whole clause in the store, and
    the reply needs "next month" from it and not the clause; "3rd may" is said with an "on" in
    front because a reply reads "your birthday on 3rd May" and not "your birthday 3rd May".
    """
    when = " ".join(str(when or "").lower().split())
    found = _DAY_TO_COME.search(when)
    if not found:
        return ""
    phrase = _DAY_SAID.sub(_cap, found.group(0).strip())
    if _A_MONTH_ON_ITS_OWN.fullmatch(phrase.lower()):
        return "in " + phrase
    if not phrase.startswith(("on ", "in ", "next ", "this ", "the ", "tomorrow", "tonight",
                              "today", "monday", "tuesday", "wednesday", "thursday", "friday",
                              "saturday", "sunday")):
        phrase = "on " + phrase
    return phrase


def _the_age(text):
    """The age a birthday line states, "she turns 7" / "turning 40", or None.

    A figure on its own is not an age here: "my birthday is on the 3rd of May" has a 3 in it and
    the person is not three.
    """
    found = _TURNS_AGE.search(text or "")
    if not found:
        return None
    for group in found.groups():
        if group:
            age = int(group)
            if 1 < age < 120:
                return age
    return None


# How many turns back the birthday can be and still be what a bare "any ideas" is about. The
# store keeps a person for the whole conversation, so without this a plan ask twenty turns later
# about something else - "we are thinking of getting a puppy" / "any ideas" - is planned for a
# birthday from the start of the chat. A bare ask is about what was just said.
_STILL_TALKING_ABOUT = 6


def _said_how_long_ago(memory, who=None, markers=""):
    """Turns since the line that filed this birthday, or None when nothing filed it."""
    turns = memory.get("turns") if isinstance(memory.get("turns"), list) else []
    now = len(turns) - 1
    best = None
    for entry in memory.get("facts_log") or []:
        if not isinstance(entry, dict) or not isinstance(entry.get("turn"), int):
            continue
        value, text = entry.get("value"), str(entry.get("text") or "")
        if who is not None:
            if entry.get("key") != "other" or not isinstance(value, dict):
                continue
            if str(value.get("who") or "").lower() != str(who).lower():
                continue
        else:
            if entry.get("key") not in ("plan", "plans", "other", "people", "birthday"):
                continue
            if markers and not markers.search(text.lower()):
                continue
        gap = now - entry["turn"]
        best = gap if best is None else min(best, gap)
    return best


# The people a birthday is for when the store kept the plan and not the person. "my sons 5th
# birthday is next weekend" is filed as the plan alone, so the person has to come off the line
# itself, and a plan addressed to the wrong person is the one thing this cannot get wrong: a
# birthday read as the person's own told them "For your birthday next weekend, put a time on it"
# about their son's fifth.
RELATIONS = frozenset((
    "mum", "mom", "mam", "mother", "dad", "father", "son", "daughter", "boy", "girl", "baby",
    "kid", "child", "husband", "wife", "partner", "boyfriend", "girlfriend", "sister", "brother",
    "friend", "mate", "nephew", "niece", "cousin", "aunt", "auntie", "uncle", "nan", "granny",
    "gran", "grandma", "grandad", "grandpa", "boss", "colleague", "neighbour", "neighbor",
    "flatmate", "housemate", "lass", "lad", "fella", "eldest", "youngest", "twins",
))

# A word that stands for a relation rather than naming one: "my other half" is a partner and "my
# little one" is a child, and "your half's 40th" is not something anyone says.
_SPOKEN_FOR = {"half": "partner", "one": "child"}

# "my son's 5th birthday", "my sons birthday", "my friend birthday", "my boy turns 5".
# A person is often named with a word in front of them - "my best friend", "my little boy", "my
# older sister" - and the word that places them is the last one before the day. Without it the
# reader fell through to the person's own record and said "your 30th" about a friend.
_MINE_BEFORE_THE_DAY = re.compile(
    r"\bmy\s+(?:[a-z]{2,12}\s+){0,2}"
    r"(?P<who>(?!(?:is|are|was|will|turns?|turning)\b)[a-z]{2,12})(?:'s|s)?\s+"
    r"(?:(?:is|are)\s+)?(?:\d{1,2}(?:st|nd|rd|th)\s+)?"
    r"(?:birthday|bday|turns?\b|turning\b)")

# The plan the store kept sometimes drops the "my": "friends birthday on friday", "daughters
# birthday party next weekend". The possessive is what says whose day it is, so it is read on its
# own when the "my" is gone.
_A_POSSESSIVE_BEFORE_THE_DAY = re.compile(
    r"\b(?P<who>[a-z]{2,12})(?:'s|s)\s+(?:\d{1,2}(?:st|nd|rd|th)\s+)?(?:birthday|bday|turns?\b)")

# Somebody is named before the day but not in a shape that can be placed - "my neighbour's friend
# birthday", "my sister in law birthday", "my other half turns 40". A plan addressed to "your
# birthday" is the wrong person, so these stand aside instead of guessing. The age shape counts
# too: "my eldest turns 10" names somebody who is not the person typing, and "your 10th" is the
# one thing that must not be said.
_A_NAME_BEFORE_THE_DAY = re.compile(
    r"\bmy\s+[a-z]{2,12}(?:'s|s)?\b[^.!?]{0,24}\b"
    r"(?:birthday|bday|turn(?:s|ing)?\s+\d{1,2}\b)")

# Somebody else's day, named as theirs and not ours to be told about.
_SOMEONE_ELSES_DAY = re.compile(r"\b(?:his|her|their|its)\s+(?:birthday|bday)\b")


def _the_person(said):
    """Who the birthday is for, read off the line: "son" for "my sons 5th birthday", else None.

    Empty string means somebody is named and cannot be placed: "my flatmate's birthday" is not a
    person this can address, and "your birthday" would be the wrong person, so the plan stands
    aside instead.
    """
    low = " ".join(str(said or "").lower().replace("\u2019", "'").split())
    if _SOMEONE_ELSES_DAY.search(low):
        return ""
    for shape in (_MINE_BEFORE_THE_DAY, _A_POSSESSIVE_BEFORE_THE_DAY):
        found = shape.search(low)
        if not found:
            continue
        who = found.group("who").strip("'")
        if who in _SPOKEN_FOR:
            return _SPOKEN_FOR[who]
        if who in RELATIONS:
            return who
        if who.endswith("'s") and who[:-2] in RELATIONS:
            return who[:-2]
        if who.endswith("s") and who[:-1] in RELATIONS:
            return who[:-1]
        return "" if _A_NAME_BEFORE_THE_DAY.search(low) else None
    return "" if _A_NAME_BEFORE_THE_DAY.search(low) else None


def _the_recent_age(memory, upto=6):
    """The one age said over the last few turns: "shes turning 8" after the plan was filed.

    The plan the store keeps is the line that named the day, so an age said on a later turn
    ("im trying to sort out my daughters birthday party next weekend" / "shes turning 8") is only
    there. Two different ages in the window are not one birthday, so nothing is read.
    """
    ages, turns = set(), 0
    for last in reversed(memory.get("turns") or []):
        if not isinstance(last, dict):
            continue
        turns += 1
        if turns > upto:
            break
        text = str(last.get("user") or "").lower()
        for found in _TURNS_AGE.finditer(text):
            age = next((g for g in found.groups() if g), "")
            if age:
                ages.add(int(age))
    if len(ages) == 1:
        age = ages.pop()
        if 1 < age < 120:
            return age
    return None


def _the_occasion(memory):
    """The one birthday the store holds with a day still to come, else None.

    Two shapes, one reading. Somebody else's day is a person in `memory["others"]` with the age
    and the day kept apart ("my sister turns 30 on saturday") or together in the birthday text
    ("my daughters birthday is next month she turns 7"). The person's own is their own record, and
    "im turning 40 next month" reaches it as a plan in their own words, with no figure filed
    beside it, so the figure is read out of that plan.
    """
    if not isinstance(memory, dict):
        return None
    told = ""
    for last in reversed(memory.get("turns") or []):
        if isinstance(last, dict) and last.get("user"):
            told = str(last.get("user"))
            break
    met = []
    for one in memory.get("others") or []:
        if not isinstance(one, dict) or one.get("pronoun"):
            continue
        who = one.get("who") or _the_person(told)
        if not who:
            continue
        age, when = one.get("age"), _the_day(one.get("turns"))
        if not when:
            # The day and the age in one string: "birthday": "next month she turns 7".
            birthday = str(one.get("birthday") or "")
            when = _the_day(birthday)
            if when:
                age = _the_age(birthday)
        if not when:
            continue
        if isinstance(age, bool) or not isinstance(age, int) or not 1 < age < 120:
            age = None
        gap = _said_how_long_ago(memory, who=who)
        if gap is not None and gap > _STILL_TALKING_ABOUT:
            continue
        met.append(("another", who, age, when))
    mine = memory.get("user") if isinstance(memory.get("user"), dict) else {}
    if not met and mine:
        plans = mine.get("plans") if isinstance(mine.get("plans"), list) else []
        said = " ".join(str(p) for p in plans[-1:]) or str(mine.get("plan") or "")
        when = _the_day(said) if _BIRTHDAY_IN_PLAN.search(said) else ""
        # The day comes from the plan and the person may be in either: "im trying to sort out my
        # daughters birthday party next weekend" is the plan, and "any ideas" is the ask.
        who = _the_person(said + " " + told) if when else None
        if when and who == "":
            return None  # somebody is named and cannot be placed: not the person typing
        if when:
            age = mine.get("age")
            if isinstance(age, bool) or not isinstance(age, int) or not 1 < age < 120:
                age = _the_age(said) or _the_recent_age(memory)
            gap = _said_how_long_ago(memory, markers=_BIRTHDAY_IN_PLAN)
            if gap is None or gap <= _STILL_TALKING_ABOUT:
                met.append(("you", who or None, age, when))
    return met[0] if len(met) == 1 else None


def _cap(match):
    """A day word said back: "on saturday" reads as a day and not as a stray lower case word."""
    return match.group(0)[:1].upper() + match.group(0)[1:]


_DAY_SAID = re.compile(
    r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|january|february|"
    r"march|april|may|june|july|august|september|october|november|december)\b")


# A plan the line makes for somebody else, or for a thing of its own: "i want to plan something
# for my mum", "can you help me plan a surprise for her". The day on file is not what the line is
# asking about, so the plan stands aside rather than plan the wrong person's birthday.
_ANOTHER_PERSON = re.compile(
    r"\bfor (?:my|our|his|her|their|the) (?:[a-z]+ )?(?:mum|mom|dad|father|mother|sister|brother|"
    r"wife|husband|partner|son|daughter|friend|mate|nan|gran|grandma|grandad|boss|colleague|"
    r"neighbours?|kids?|children)\b")


def _reads_as_a_plan_ask(said, memory):
    """True when the line asks for a plan for the thing in hand and names nothing else.

    A follow-up leans on the turn before it, so "i want to plan something" carries no subject of
    its own and the store is the only place the subject can come from. The subject words are
    looked for only on the line itself: a word the earlier turn used ("my sister turns 30 on
    saturday") is what the store already made of it.
    """
    said = " ".join((said or "").lower().split())
    if not said:
        return False
    words = said.replace("?", " ").replace("!", " ").replace(".", " ").split()
    if len(words) > 10:
        return False
    if not _ASKS_FOR_A_PLAN.search(said):
        return False
    if _NOT_A_PLAN_ASK.search(said):
        return False
    subject = _OWN_SUBJECT.findall(said)
    if subject:
        return False
    if _ANOTHER_PERSON.search(said):
        return False
    return True


def takes_as_it_comes(text, memory):
    """The hook a module declares (`TAKES_AS_IT_COMES`): this line is the plan for the day on file.

    Nothing in the entries knows whose birthday is in the store, so the card that answers a plan
    ask in general plans a plain Saturday - "pick two things and put them in the diary by Friday"
    - and the day the person named is lost. Said only on the lines `reply_for` answers, so every
    other line this module proposes on is settled by the ordinary rules.
    """
    return reply_for(text, memory) is not None


def reply_for(text, memory):
    """A plan for the birthday the store holds, or None for every other line."""
    occasion = _the_occasion(memory)
    if occasion is None:
        return None
    if not _reads_as_a_plan_ask(text, memory):
        return None
    kind, who, age, when = occasion
    if kind == "you":
        whose = _whose(who) if who else "your"
    else:
        whose = _whose(who)
        if not whose:
            return None
    day = " ".join(part for part in (whose, _ordinal(age) if age else "birthday", when) if part)
    if age is not None and age < 16:
        pool = CHILD_PLANS
    elif _SOON.search(when):
        pool = SOON_PLANS
    else:
        pool = PLANS
    # The same conversation asks once, so the choice may as well be steady: it is made from the
    # line and the turns before it, never from the clock.
    turns = memory.get("turns") if isinstance(memory.get("turns"), list) else []
    seed = len(turns) * 7919 + sum(ord(c) for c in " ".join(str(text or "").lower().split()))
    line = random.Random(seed).choice(pool)
    return line.replace("{day}", day)
