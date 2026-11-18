"""The first fortnight with a newborn: the cord, going out, cluster feeding, the birth weight.

These rows were built inside `bot/knowledge/family.py` and moved out here, unchanged, because that
file is at the publisher's 1 MiB ceiling: a file over it cannot be uploaded at all, so a change to
it has to make it smaller. The domain is the baby itself rather than the family in general - the
news, the cord stump, the first trip out, the evening that never ends, the weight at birth - and
every row stands down for the question that is really about a temperature, a feed, a nappy, a cot,
a jab or a name, which keeps its own card.

The guard matters more than usual: `the-first-fortnight` is the fallback for the news and the age,
so it must take itself out of the running when the line is something else (a follow-up that names
nothing, an older baby, somebody else's baby) rather than answer "Congratulations" and leave the
real question with nothing.
"""
import re

from .lookup import entry

# The topic this domain answers, so the arbiter knows it is the specialist for a line about a
# newborn. `family.py` declares the same topic for the rest of the family cards.
ANSWERS = ("family-and-parenting",)

ENTRIES = []


# --- the first fortnight with a newborn ---------------------------------------------------
# "my baby was born last week" was answered "That's great news. Congratulations!" and nothing
# else, and "my baby is 5 days old" with "Thanks for telling me". Every baby row here wants an
# age in months, a food, a symptom or a night's sleep, and a five-day-old is none of them. The
# first fortnight has its own short list of questions - the cord, going out, the day-five check,
# the small weight loss, the evening that never ends - so one table answers them, keyed on what
# is being asked rather than on how it is worded.
_THE_FIRST_FORTNIGHT = (
    "Congratulations. The first fortnight is mostly feeding and sleep: eight to twelve feeds in "
    "24 hours, six or more wet nappies a day, and the midwife comes on day five for the heel-prick "
    "blood spot test. The cord drops off in about a week to a fortnight, and the birth weight, "
    "down by up to a tenth in the first days, is back by two weeks. Ring the midwife or 111 the "
    "same day if the baby is too sleepy to feed, has fewer wet nappies, or looks yellow.")

_CORD = (
    "The cord stump dries out and drops off on its own between about five days and a fortnight - "
    "clean and dry, water only, no cream or powder, and fold the nappy below it so air gets to "
    "it, and let it come away rather than pulling. A little bleeding at the very end is normal; a "
    "red, hot or smelly patch around the base, or pus, is a call to the midwife the same day. If "
    "it is still there at three weeks, mention it.")

_OUT_AND_ABOUT = (
    "You can take a newborn out from the first day: a pram or a sling, one more layer than you "
    "are wearing, and out of direct sun. Keep them out of crowded rooms and away from anyone with "
    "a cough or a cold for the first six weeks, and take the pram rather than passing a newborn "
    "round a room. Go out after a feed and you get the long sleep for it.")

_CLUSTER_FEEDING = (
    "An evening of non-stop feeding is cluster feeding, and it is normal in the first weeks: it "
    "is not a sign your milk is short, it is how the supply is built. Keep them on, swap sides, "
    "and get someone else to take them for an hour once they settle so you can sleep. A baby who "
    "is having six or more wet nappies a day and gaining along their line is getting enough - the "
    "scales at the clinic settle it better than the length of a feed.")

_BIRTH_WEIGHT = (
    "The average baby weighs about 3.5 kg (7 lb 8 oz) at birth, and anything from 2.5 to 4.5 kg "
    "is normal, so 3 kg (6 lb 10 oz) is a common and perfectly normal size. The figure to watch "
    "is the change: up to a tenth of it can go in the first few days, and it is back to birth "
    "weight by two weeks. A baby who has not got back to it by then is seen again, so keep the "
    "weigh-in appointments.")

# A weight said in a chat where a baby was just born is a birth weight, and the answer is the
# range: "she weighed 3 kilos" was "Got it. Is there anything you'd like a hand with?"
_WEIGHT_SAID = re.compile(
    r"\b(?:weighed|weighs|weight|kilos?|kg|pounds?|lbs?)\b|\b\d+(?:\.\d+)?\s*(?:kilo|kg|lbs?|"
    r"pounds?)\b", re.I)
_DAYS_OLD = re.compile(r"\b(\d{1,2})\s+days?\s+old\b", re.I)
_WEEKS_OLD = re.compile(r"\b(\d{1,2})\s+weeks?\s+old\b", re.I)
_A_NEWBORN_WORD = re.compile(
    r"\b(?:newborn|newborns|newly born|just born|born last week|born yesterday|born this week|"
    r"born a week ago|first week|first fortnight|first few weeks|just had a baby|"
    r"just had the baby|had the baby|had our baby|gave birth|given birth|"
    r"born on (?:mon|tues|wednes|thurs|fri|satur|sun)day|born this morning|born today|"
    r"born at (?:the|home)|home birth)\b", re.I)
# A line that names one of these is another card's question, and the fortnight card would be a
# platitude in its place: a temperature, a feed, a nappy, a cot, a jab, a symptom, a name.
_NOT_THE_FORTNIGHT = (
    "temperature", "fever", "sick", "vomiting", "diarrhoea", "rash", "cold", "cough", "colic",
    "wind", "reflux", "nappy", "nappies", "poo", "sleep", "sleeps", "sleeping", "wont sleep",
    "wont feed", "wont take a feed", "not feeding", "isnt feeding", "breastfeed", "breastfeeding",
    "formula", "milk", "jab", "jabs", "vaccine", "vaccines", "vaccination", "cot", "cot death",
    "pram", "pushchair", "car seat", "bath", "teething", "jaundice", "pillow", "swaddle",
    "swaddling", "dummy", "weaning", "solids", "food", "name", "christening", "gift", "present",
    "visitors", "visiting", "nursery", "childminder", "weight gain", "not gaining", "losing",
    "early", "premature", "twins", "breath", "breathing", "cord around", "crying", "cries",
    "unsettled", "winding", "screen", "test", "hospital", "doctor", "gp", "health visitor",
    # the gear list is what "what do i need" wants, not the fortnight
    "what do i need", "need to buy", "need to get", "what to buy", "what do we need", "buy")


def _the_line_said(understood):
    """The line's own words, lowercased: the reading rewrites some lines and the text is truest."""
    for field in ("text", "clean", "plain"):
        said = (understood or {}).get(field)
        if isinstance(said, str) and said.strip():
            return " ".join(said.lower().split())
    return ""


# Someone else's baby is news, not this card's line: "my sister had a baby last week" wants a
# warm word, and the day-five check is advice for the parent. A partner's baby is the reader's
# own, so "my wife had the baby last week" and "we had a baby" are not in this list.
_SOMEONE_ELSE_BABY = re.compile(
    r"\b(?:my|our)\s+(?:sister|sisters|friend|friends|neighbour|neighbor|colleague|boss|cousin|"
    r"niece|aunt|auntie|daughter-in-law|sister-in-law|brother|brother-in-law|stepdaughter)s?\b"
    r"|\b(?:a friend|her baby|his baby|their baby|she had a baby|she had her baby)\b", re.I)


def _the_line_is_the_news(understood):
    """Whether this line is the news of a new baby, or the age of one, and nothing else.

    A guard rather than a check inside the reply: an entry whose reply returns None has already
    won the line, so the card is gone and the question is left with no answer at all. A guard
    takes the entry out of the running and the next card gets its turn, which is what "what
    should i get them" after a birth needs.
    """
    said = _the_line_said(understood)
    if not said:
        return False
    if re.search(r"\b(?:she|he|they)\s+(?:was|is|were|has been)\b", said) and not re.search(
            r"\b(?:my|our)\b", said):
        # "she was born on friday" is somebody else's news, and the fortnight card is advice
        # written for the parent
        return False
    if _SOMEONE_ELSE_BABY.search(said) and not re.search(
            r"\b(?:my|our)\s+(?:baby|son|daughter|newborn)\b|\bi (?:had|gave)\b", said):
        return False
    if _is_an_older_baby(said):
        # twelve weeks old is not the fortnight: the milestone and feeding cards have that line
        return False
    if any(word in said for word in _NOT_THE_FORTNIGHT):
        # the temperature, the feed, the nappy, the cot, the jab: another card's question
        return False
    return True


def _is_an_older_baby(said):
    """Whether the line gives the baby an age past the first fortnight.

    The card this fences answers with the first fortnight - the cord, the first trip out, the
    weight at birth - so "my baby is 3 weeks old" is past it: the fortnight's own answers read
    as yesterday's news, and the stage and feeding cards have that line.
    """
    days = _DAYS_OLD.search(said)
    if days and int(days.group(1)) > 14:
        return True
    weeks = _WEEKS_OLD.search(said)
    if weeks and int(weeks.group(1)) > 2:
        return True
    return bool(re.search(r"\b(?:[2-9]|1[0-9]|2[0-4])\s+months?\s+old\b", said)) or bool(
        re.search(r"\byears?\s+old\b", said))


def _is_a_newborn(said):
    """Whether the line says an age in days, or in the first two weeks, for a baby."""
    days = _DAYS_OLD.search(said)
    if days and int(days.group(1)) <= 14:
        return True
    weeks = _WEEKS_OLD.search(said)
    if weeks and int(weeks.group(1)) <= 2:
        return True
    return False


def _a_birth_just_happened(memory, understood):
    """Whether a baby was born in the line, or in the turn or two before it."""
    from .family import _BIRTH_IN_THE_CHAT
    said = [_the_line_said(understood)]
    for turn in (memory.get("turns") or [])[-2:] if isinstance(memory, dict) else []:
        if isinstance(turn, dict):
            said.append(str(turn.get("user") or "").lower())
    return bool(_BIRTH_IN_THE_CHAT.search(" ".join(said)))


def _the_birth_weight(memory, understood):
    """The range a birth weight is normal in, for a weight said in a chat with a new baby."""
    said = _the_line_said(understood)
    if not said or not _WEIGHT_SAID.search(said):
        return None
    if "birth" in said or "at birth" in said:
        return _BIRTH_WEIGHT
    if _DAYS_OLD.search(said) or _WEEKS_OLD.search(said):
        # "my baby is 8 weeks old and weighs 5 kilos" is a growing baby, not a birth weight
        days = _DAYS_OLD.search(said)
        weeks = _WEEKS_OLD.search(said)
        if (days and int(days.group(1)) > 21) or (weeks and int(weeks.group(1)) > 6):
            return None
    if not _a_birth_just_happened(memory, understood):
        return None
    return _BIRTH_WEIGHT



# The fortnight after the birth has its own short list of questions, and each one is a row, so a
# line that asks about the cord is not answered with the platitude about the fortnight and a line
# that says the news is. Everything else a newborn brings - a temperature, a feed, a nappy, a cot,
# a jab - keeps its own card, which is why the last row stands down for all of it.
ENTRIES.append(entry("a-cord-stump",
                     (("cord", "umbilical cord", "cord stump", "belly button", "stump"),
                      ("fall", "falls", "falling", "off", "come off", "comes off", "drop",
                       "drops", "when", "how long", "still on", "heal", "heals", "clean")),
                     _CORD, bias=2))
ENTRIES.append(entry("a-newborn-out-and-about",
                     (("newborn", "baby", "babies", "born", "days old", "weeks old"),
                      ("go out", "going out", "out and about", "outside", "leave the house",
                       "first trip", "take him out", "take her out", "take them out",
                       "take the baby out", "when can we go", "when can i take")),
                     _OUT_AND_ABOUT,
                     # a car seat, a pram and a jab are their own questions
                     avoid=("car", "car seat", "carseat", "pram", "pushchair", "sling",
                            "vaccine", "vaccines", "jab", "jabs", "swim", "swimming"),
                     bias=2))
ENTRIES.append(entry("cluster-feeding",
                     (("baby", "babies", "newborn", "feeding", "feeds", "feed"),
                      ("cluster", "cluster feeding", "constantly", "all evening", "all the time",
                       "all night", "feeds constantly", "feeding constantly", "wants to feed",
                       "non stop", "nonstop", "every hour")),
                     _CLUSTER_FEEDING,
                     # a baby who will not feed, or a supply worry, is the feeding card's line
                     avoid=("wont feed", "won't feed", "not feeding", "isnt feeding",
                            "isn't feeding", "refusing", "refuses", "formula", "supply",
                            "mastitis", "blocked duct", "tongue tie", "losing", "not gaining",
                            "wont take", "won't take", "how often", "how much milk",
                            "how many feeds", "ounces",
                            # a crying or a sleepy baby is the crying list and the sleep card
                            "cries", "crying", "cry", "settle", "settling", "sleep",
                            "sleeps", "sleeping", "waking", "awake", "unsettled", "whingey"),
                     bias=2))
ENTRIES.append(entry("a-birth-weight",
                     (("weighed", "weighs", "weigh", "weight", "kilo", "kilos", "kg", "pounds",
                       "lb", "lbs"),
                      ("birth", "born", "newborn", "baby", "babies", "gave birth", "days old",
                       "last week", "at birth")),
                     _the_birth_weight,
                     # a growing baby's weight is the clinic's line, and a loss is the health
                     # visitor's: this row answers the size at birth, not the gain since
                     avoid=("month old", "months old", "years old", "centile", "percentile",
                            "percent", "%", "gain", "gaining", "put on", "lost", "losing",
                            "dropped", "too much", "too little", "diet"),
                     bias=2))
ENTRIES.append(entry("the-first-fortnight",
                     (("baby", "babies", "newborn", "newborns", "born", "birth", "gave birth"),
                      ("last week", "yesterday", "days old", "weeks old", "day old", "week old",
                       "first week", "first fortnight", "first few weeks", "what happens",
                       "what now", "next", "just had", "born on", "born this", "born a week",
                       "just born", "new arrival")),
                     _THE_FIRST_FORTNIGHT,
                     # the line itself has to say the news or the age: a follow-up that names
                     # nothing ("what should i get them" after a birth) is the present card's
                     guard=_the_line_is_the_news,
                     # a baby in the house is not the complaint in "my partner does nothing at
                     # night": that line is the uneven home load, and it scored the same, so the
                     # complaint words stand this row down
                     avoid=_NOT_THE_FORTNIGHT + ("month old", "months old", "years old",
                                                 "does nothing", "doesnt help", "does not help",
                                                 "wont help", "won't help", "night feeds on my own",
                                                 "no help at night"),
                     bias=1))
