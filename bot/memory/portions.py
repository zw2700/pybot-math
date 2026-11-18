"""A follow-up asking how many the answer in hand feeds is answered by that answer's own count.

    how much pasta for 4 people
      "About 100 g of dry pasta each, so 400 g for four."
    how many does that serve
      "I'm not sure about that one, sorry — I'd rather not guess. A quick search online..."

    how much potato salad for a party
      "About 250 g of potatoes each."
    how many does that feed
      "Cheap party food people actually eat: a big pot of chilli or a pasta bake, garlic bread..."

Both lines are about the answer on the screen: the first answer already says who it is for ("for
four") and the second only says what it is for per person. Nothing read either, so the first fell
to a search hedge and the second to the party-food card, which is a different question.

What this reads is only the counting half of a portion answer, and it says one of two things:

* the answer named the number it works out to ("so 400 g for four", "feeds 6", "serves four"), and
  that number is the answer to the line;
* the answer gives an amount per person and no total ("250 g of potatoes each"), so the line has
  no answer yet: the total depends on how many are coming, and the reply asks for that - and the
  count they answer with is worked out from the figure the answer gave ("about 5 kg for twenty"),
  because a promise to do the sums has to be kept on the next line or it is worse than no promise.

It is narrow on purpose, and returns None for everything else:

* the line has to ask how many the thing in hand feeds or serves, in the words people use for it
  ("how many does that feed", "how many people does that serve") - "how many do i need" is a
  shopping question and belongs to the modules that weigh a shop;
* the answer in hand has to be a portion answer: an amount in grams, kilos, millilitres or cups,
  or a per-person figure. An answer about the number of days a thing keeps, or the number of
  people at a party, is not a portion, and neither is a line about a recipe nobody has asked
  about yet;
* a count the answer gives for something else is not read as the portion: "for 4 minutes" is a
  time, so a figure followed by a unit of time is not the count the answer works out.
"""
import re

from . import history

# The words a person counts people with, as a digit or as a word.
_COUNT = (r"(?:\d{1,3}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|dozen|"
          r"a dozen)")

# How many the thing in hand feeds, asked with the pronoun that stands for the answer.
A_PORTION_ASK = re.compile(
    r"\bhow many\b[^.?!]{0,30}?\b(?:does|do|would|will|can)\s+(?:that|it|this)\s+\w+"
    r"|\bhow many people (?:does|do|will|would)\s+(?:that|it|this)\b"
    r"|\b(?:that|it|this)\s+(?:feeds|serves|makes|does|will do)\s+(?:how many|how much)\b"
    # "how many is that for", "how many people is that enough for", "so thats for how many",
    # "enough for how many": the same question, said from the other end, and all of them need the
    # pronoun because a bare "how many do i need" is a shopping question and not this one.
    r"|\bhow many(?: people| mouths)?\s+(?:is|are|will|would)\s+(?:that|it|this)\b"
    r"|\bhow many(?: people| mouths)?\s+(?:is|are)\s+(?:that|it|this)\s+\w+"
    r"|\b(?:that|it|this)\s+(?:is|are)\s+for\s+how many\b"
    r"|\b(?:enough|good)\s+for\s+how many\b", re.I)

# The count the answer itself works the portion out to, and the per-person figure it gives instead
# of a total.
FEEDS_A_COUNT = re.compile(r"\b(?:feeds|serves|makes)\s+(?P<n>" + _COUNT + r")\b", re.I)
FOR_A_COUNT = re.compile(r"\bfor\s+(?P<n>" + _COUNT + r")\b", re.I)
PER_PERSON = re.compile(r"\b(?:each|per person|apiece|a head|per head|each person|per serving)\b",
                        re.I)

# An amount of food, which is what makes the answer a portion answer at all. A figure followed by
# a unit of time is not one: "roast it for 4 minutes" answers a different question.
# A figure with a unit, read whole: "1.2 litres" is one amount, and reading it from the "2" is how
# a total of 1.2 litres was said back as "the answer puts it at 2 litres". So a figure cannot start
# just after a decimal point.
AN_AMOUNT = re.compile(
    r"(?<![\d.])\d+(?:\.\d+)?\s*(?:g|grams?|kg|kilos?|ml|millilitres?|litres?|l|oz|ounces?|"
    r"lbs?|pounds?|cups?|tablespoons?|tbsps?|teaspoons?|tsps?)\b"
    r"|\bhalf a (?:cup|mug|kilo|pint)\b|\ba (?:cup|mug|kilo|pint)\b", re.I)
# The unit that is there instead of a number of people, read from the text just after the count:
# "for 45 minutes" is a length of time and not a table, and looking for it in the number alone
# ("45") found nothing, so the tea chat's "...for 45 minutes" was answered "That is for 45."
A_TIME_AFTER_A_COUNT = re.compile(
    r"\s*(?:seconds?|secs?|minutes?|mins?|hours?|hrs?|days?|weeks?|months?|years?)\b", re.I)


def _a_time_not_a_portion(said, found):
    """True when the count the answer gives is a length of time, not a number of people."""
    return bool(A_TIME_AFTER_A_COUNT.match(said or "", found.end("n")))

# A count of people said after the answer asked for one: "theres about twenty coming", "20 people",
# "twelve of us", "just the four of us". It has to name who is coming, so a bare figure ("i have 2000
# on a credit card") is not read as a party.
_NUMBER_WORD = (r"(?:\d{1,3}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
                r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|"
                r"forty|fifty|sixty|seventy|eighty|ninety|a hundred|a dozen)")
A_COUNT_OF_PEOPLE = re.compile(
    r"\b(?:about\s+|around\s+|just\s+|only\s+|all\s+)?(?P<n>" + _NUMBER_WORD + r")\s+"
    r"(?:people|guests|of us|adults|coming|mouths)\b"
    r"|\b(?:theres|there are|there will be|we are|were|we have|weve got|make it|make that)\s+"
    r"(?:about\s+|around\s+)?(?P<m>" + _NUMBER_WORD + r")\b", re.I)

# The per-head figure of an answer, as grams, so a count of people can be multiplied out of it.
# A count said with no word for who it is: "so how much for 8" after an answer that weighed one
# person and scaled to a count of its own. The answer in hand already said what is being portioned,
# so the figure alone is the whole of the question - and the answer to it is that answer's own
# per-head figure, worked out for the new number, never the old total said back.
A_BARE_COUNT = re.compile(
    r"^\W*(?:and|so|ok|okay|right|then|but|no|yes|yeah)?[\s,]*"
    r"(?:how\s+much|how\s+many)?[\s,]*(?:is\s+that|would\s+that\s+be|does\s+that\s+make)?"
    r"[\s,]*(?:for|between)\s+(?P<n>" + _NUMBER_WORD + r")\b[\s.?!]*$", re.I)

A_FIGURE_AND_UNIT = re.compile(
    r"\b(?P<n>\d+(?:\.\d+)?)\s*(?P<u>kg|kilos?|g|grams?|ml|millilitres?|litres?|l|oz|ounces?|"
    r"lbs?|pounds?)\b", re.I)

# The clause of the answer that carries the count, when the answer has more than one: "100 g each,
# so 400 g for four" is read for its second half, because that is the one with the number in it.
CLAUSE_EDGE = re.compile(r",\s*so\s+|;\s+|,\s*(?:which|and that)\s+|\.\s+", re.I)


def _the_last_answer(memory):
    """The bot's last line, which is the answer the person is looking at.

    The reach back into the conversation is `bot/memory/history.py`'s one check, not a window
    spelled out here: a module that reads a follow-up out of an earlier turn has to step back over
    the same turns as every other one, and "" is what a chat with no earlier turn gives.
    """
    return history.the_last_answer(memory)


def _the_clause_with_the_count(said, start, end):
    """The sentence or clause of the answer around the count, so the reply can quote the figure."""
    left = 0
    for edge in CLAUSE_EDGE.finditer(said):
        if edge.end() <= start:
            left = edge.end()
        elif edge.start() >= end:
            return said[left:edge.start()].strip(" .")
    return said[left:].strip(" .")


def _the_number(word):
    return " ".join(str(word or "").split()).lower()


_WORDS_FOR_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80,
    "ninety": 90, "a hundred": 100, "a dozen": 12, "dozen": 12,
}


def _as_a_count(word):
    """The number a count was said with, or 0 when it is not one this reads."""
    word = _the_number(word)
    if word.isdigit():
        return int(word)
    return _WORDS_FOR_NUMBERS.get(word, 0)


def _in_grams(figure, unit):
    """A per-head figure as grams, so the sums stay in one unit; 0 for a unit this cannot weigh."""
    unit = unit.lower()
    if unit in ("kg", "kilo", "kilos"):
        return figure * 1000.0
    if unit in ("g", "gram", "grams"):
        return figure
    if unit in ("oz", "ounce", "ounces"):
        return figure * 28.35
    if unit in ("lb", "lbs", "pound", "pounds"):
        return figure * 453.6
    # A millilitre of a sauce is close enough to a gram for a party, and the word used is "about".
    if unit in ("ml", "millilitre", "millilitres", "l", "litre", "litres"):
        return figure * (1000.0 if unit in ("l", "litre", "litres") else 1.0)
    return 0.0


def _counts_people(said, found):
    """True when a per-person word counts people rather than the parts of a recipe.

    "About 250 g of potatoes each" weighs one person. "about 175g of each for three medium eggs"
    weighs the butter, the sugar and the flour, and answering "for 8" out of it would say a person
    eats 1.4 kg of cake mix. The word is the same, so the little word in front of it decides.
    """
    if found.group(0).lower() != "each":
        return True
    before = (said or "")[:found.start()].rstrip().lower()
    return not before.endswith(("of", "in", "for", "with"))


def _the_per_head_figure(said):
    """The grams one person gets, as the answer says it, or 0 when it does not weigh one person.

    The figure is read from the clause the per-person word is in, not from the answer as a whole:
    "About 75 g of dry rice each, so 300 g for four" weighs one person at 75 g, and taking the
    first figure of the answer only happens to agree with that.
    """
    said = said or ""
    for found in PER_PERSON.finditer(said):
        if not _counts_people(said, found):
            continue
        head = said[:found.start()]
        clause = head[max(head.rfind("."), head.rfind(","), head.rfind(";")) + 1:]
        for figure in reversed(list(A_FIGURE_AND_UNIT.finditer(clause))):
            grams = _in_grams(float(figure.group("n")), figure.group("u"))
            if grams:
                return grams
        for figure in A_FIGURE_AND_UNIT.finditer(said):
            grams = _in_grams(float(figure.group("n")), figure.group("u"))
            if grams:
                return grams
    return 0.0


def _a_total(grams):
    """A total weight said the way a person says one: whole kilos above a kilo, grams below."""
    if grams >= 1000:
        kilos = round(grams / 1000.0, 1)
        text = ("%g" % kilos)
        return text + " kg"
    return "%g g" % round(grams)


def the_portion_answer(memory):
    """The answer in hand when it is a portion answer, or "" when it is about something else."""
    said = _the_last_answer(memory)
    if not said:
        return ""
    # The answer has to be a portion answer: an amount of food, or a per-person figure. A line
    # about how long a thing keeps is not one, and this module says nothing about it.
    if not (AN_AMOUNT.search(said) or PER_PERSON.search(said) or FEEDS_A_COUNT.search(said)):
        return ""
    return said


def an_ask(text, memory):
    """True when this line asks how many the portion answer in hand feeds.

    This is the reading the arbiter asks for before the knowledge entries propose anything: the
    party-food card is a good card and an answer to a different question, so the line that asks
    what the answer in hand feeds is this module's, whatever else proposed. Kept side-effect free
    so the claim and the reply cannot disagree.
    """
    if not A_PORTION_ASK.search(text or ""):
        return False
    said = the_portion_answer(memory)
    if not said:
        return False
    # The claim is only made where this module has a reply: an amount with no count and no per-head
    # figure ("about 2.5 litres of paint") is not a portion of food, and standing the knowledge base
    # down there would leave the line to the shrug.
    counted = FEEDS_A_COUNT.search(said) or FOR_A_COUNT.search(said)
    if counted and not _a_time_not_a_portion(said, counted):
        return True
    # An amount per person is only this module's line when it can be weighed: a price card that
    # happens to say "check what each one includes" has a per-person word and no figure, and
    # claiming it only took the line away from the module that would have answered it.
    return bool(PER_PERSON.search(said) and _the_per_head_figure(said))


def reply_for(text, memory):
    """The reply to a line asking how many the answer in hand feeds, or None."""
    if not A_PORTION_ASK.search(text or ""):
        return None
    said = the_portion_answer(memory)
    if not said:
        return None
    counted = FEEDS_A_COUNT.search(said) or FOR_A_COUNT.search(said)
    if counted and not _a_time_not_a_portion(said, counted):
        number = _the_number(counted.group("n"))
        clause = _the_clause_with_the_count(said, counted.start(), counted.end())
        amount = AN_AMOUNT.search(clause)
        if amount:
            # "so 400 g for four" is the answer to the line, and it is what a friend would say:
            # the number it is for and the figure the answer worked out, without saying "for four"
            # twice.
            return ("That is for " + number + " - the answer puts it at "
                    + " ".join(amount.group(0).split()) + " in total.")
        return "That is for " + number + "."
    if PER_PERSON.search(said):
        # An amount per person is not a total, so the line cannot be answered until they say how
        # many are coming. Asking for that is the one question that follows from the answer, and
        # the figure is kept so the sums can be done on the line they answer with: a promise to
        # work the total out is only worth making if it is kept, so with no figure to weigh there
        # is no promise.
        grams = _the_per_head_figure(said)
        if not grams:
            return ("That is per person, so it goes up with however many you are feeding.")
        memory["portion"] = {"grams": grams, "turn": len(history.turns_before(memory))}
        return ("That is per person, not a total - say how many you are feeding and I will work "
                "the total out for you.")
    return None


# A count the person has changed their mind about: "make it 6 not 4", "6 not 4", "actually 8".
# The same sum as a bare count, said with the correction in it - and the number to work from is the
# one they mean now, which is never the one the answer in hand already scaled to.
_A_NEW_COUNTS = (
    re.compile(r"\b(?:make it|make that|we are|were|we'll be|we will be|there are|theres|"
               r"there's)\s+(?P<n>" + _NUMBER_WORD + r")(?:\s+not\s+(?P<old>" + _NUMBER_WORD + r"))?",
               re.I),
    re.compile(r"\b(?P<n>" + _NUMBER_WORD + r")\s+not\s+(?P<old>" + _NUMBER_WORD + r")\b", re.I),
    re.compile(r"\b(?:actually|no|sorry|oh|hang on)\s+(?P<n>" + _NUMBER_WORD + r")\b", re.I),
    re.compile(r"^\W*(?:and\s+|so\s+)?(?P<n>" + _NUMBER_WORD + r")\s+"
               r"(?:people|of us|guests|adults)\b", re.I),
)


_A_NUMBER_ANYWHERE = re.compile(r"\b(?:" + _NUMBER_WORD + r")\b", re.I)
_A_UNIT_AFTER = re.compile(r"\s*(?:kg|kilos?|grams?|g\b|ml|millilitres?|litres?|l\b|oz|ounces?|"
                           r"lbs?|pounds?)", re.I)


def _is_an_amount_not_a_count(text, found):
    """True when the figure is an amount they want rather than a number of people.

    "how much rice for 8 people" / "make it 500g instead" is a person changing the amount and not
    the company: reading 500 as a count gave "about 37.5 kg in total for 500".
    """
    tail = (text or "")[found.end("n"):]
    return bool(_A_UNIT_AFTER.match(tail))


def _says_two_counts(text, found):
    """True when the line works out a count of its own - "3 kids and 2 adults" - and not this one.

    A sum of two groups is answered by the module that adds them up (375 g for five), and reading
    the first number alone answers a question nobody asked.
    """
    if found.groupdict().get("old"):
        return False
    return len(_A_NUMBER_ANYWHERE.findall(text or "")) > 1


def _the_new_count(text):
    """The count a correction names, as the line says it, or None."""
    for pattern in _A_NEW_COUNTS:
        found = pattern.search(text or "")
        if found and _as_a_count(found.group("n")):
            if _is_an_amount_not_a_count(text, found) or _says_two_counts(text, found):
                return None
            return found
    return None


A_CONFIRMATION = re.compile(
    r"\b(?:confirmed|confirm|yes|yep|yeah|yup|exactly|right|correct|thats right|that's right|"
    r"spot on|sure|indeed|definitely|probably|maybe)\b", re.I)


def _is_a_digit(word):
    return str(word or "").strip().isdigit()


def _the_count_they_gave(text):
    """The count the person answered the ask with, as (count, the word they used), or (0, "").

    The reply before it asked how many are coming, so a number on this line is the answer - and a
    person answers in their own words: "so thats twenty confirmed" and "yep twenty" name nobody at
    all, and the who-word the first reading needs is not there. A figure in digits with nothing
    confirming it is left alone, because "i have 2000 on a credit card" is not a party.
    """
    text = text or ""
    found = A_COUNT_OF_PEOPLE.search(text)
    if found:
        word = found.group("n") or found.group("m")
        count = _as_a_count(word)
        if count and count <= 500:
            return count, word
    for found in _A_NUMBER_ANYWHERE.finditer(text):
        word = found.group(0)
        count = _as_a_count(word)
        if not count or count > 500:
            continue
        if _is_a_digit(word) and not A_CONFIRMATION.search(text):
            continue
        return count, word
    return 0, ""


def _the_said_total(grams, count, count_word, old_word=None):
    """The total and the per-head figure, with the number corrected said back.

    A correction that is not read back is not answered: "make it twenty not ten" after the ask got
    a total for twenty and no sign that the ten was dropped.
    """
    if old_word:
        return ("Not " + _the_number(old_word) + " - " + _the_number(count_word) + ": about "
                + _a_total(grams * count) + " in total, at " + _a_total(grams) + " a head.")
    return ("About " + _a_total(grams * count) + " in total for " + _the_number(count_word)
            + " - that is " + _a_total(grams) + " a head.")


def _a_total_for_a_bare_count(text, memory):
    """The same sum, when the line gives the number and the answer in hand gave the rest.

    "how much rice for 4 people" is answered "About 75 g of dry rice each, so 300 g for four", and
    the next line is "so how much for 8". The person has not named rice again, but the answer on the
    screen has: it weighed one person and scaled to a count, so a bare number is the new count and
    the figure is its own per-head one. The reply works the sum out for the number asked, because
    saying the old total back is the one answer that is certainly wrong.
    """
    found = A_BARE_COUNT.search(text or "") or _the_new_count(text)
    if not found or _is_an_amount_not_a_count(text, found) or _says_two_counts(text, found):
        return None
    said = _the_last_answer(memory)
    if not said or not any(_counts_people(said, found) for found in PER_PERSON.finditer(said)):
        return None
    grams = _the_per_head_figure(said)
    if not grams:
        return None
    count = _as_a_count(found.group("n"))
    if not count or count > 500:
        return None
    old_word = found.groupdict().get("old")
    return _the_said_total(grams, count, found.group("n"), old_word)


def a_bare_count_to_fill(text, memory):
    """True when the line is a bare count answering the per-head figure the answer in hand gave."""
    if not isinstance(memory, dict):
        return False
    found = A_BARE_COUNT.search(text or "") or _the_new_count(text)
    if not found or _is_an_amount_not_a_count(text, found) or _says_two_counts(text, found):
        return False
    said = _the_last_answer(memory)
    if not said or not any(_counts_people(said, found) for found in PER_PERSON.finditer(said)):
        return False
    if not _the_per_head_figure(said):
        return False
    count = _as_a_count(found.group("n"))
    return bool(count) and count <= 500


def a_count_to_fill(text, memory):
    """True when this line answers the question the reply before it asked about a portion."""
    if not isinstance(memory, dict):
        return False
    portion = memory.get("portion")
    if not isinstance(portion, dict) or not portion.get("grams"):
        return False
    if len(history.turns_before(memory)) - int(portion.get("turn") or 0) > 1:
        return False
    return bool(_the_count_they_gave(text)[0])


def the_total_for(text, memory):
    """The total a count of people makes of the figure the answer gave, or None.

    A line that names how many are coming, said on the turn after the reply asked for it, is the
    other half of the same question: "how much potato salad for a party" (250 g a head) / "how many
    does that feed" / "theres about twenty coming" is a person finishing the sum the bot said it
    would do. Nothing else reads it - the count has to name who is coming, and the ask has to be
    the turn before - so a figure on a line of its own stays whatever it was about.
    """
    if not isinstance(memory, dict):
        return None
    portion = memory.get("portion")
    if not isinstance(portion, dict) or not portion.get("grams"):
        return _a_total_for_a_bare_count(text, memory)
    # Only the turn directly after the ask: two lines later the person has moved on, and the count
    # belongs to whatever they are saying now.
    if len(history.turns_before(memory)) - int(portion.get("turn") or 0) > 1:
        memory.pop("portion", None)
        return None
    count, said = _the_count_they_gave(text)
    if not count:
        return None
    memory.pop("portion", None)
    corrected = _the_new_count(text or "")
    old_word = (corrected.groupdict().get("old") if corrected is not None else None)
    return _the_said_total(float(portion["grams"]), count, said, old_word)
