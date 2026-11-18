"""A yes/no about a figure the bot itself gave: "so is eight weeks still right".

The bot had said "Three runs a week gets most people to 5k in about eight weeks", and then the
person asked whether the eight weeks stood. Nothing in the line names a thing of its own - the
thing it is about is the figure in the bot's own answer - so the knowledge base read the words it
could see and answered from a different entry altogether:

    i want to run 5k
      Three runs a week gets most people to 5k in about eight weeks ...
    how long will it take
      Eight weeks.
    im 52 and a bit overweight
      Got it. Is there anything you'd like a hand with?
    so is eight weeks still right
      Ask in writing and name what you want: a refund, a repair, or money for the trouble. (a
      consumer-complaint entry, reached by the words "eight weeks")

The figure is the answer's, and the question is whether it still stands, so the answer is the
figure with the reason the chat already gave for it: "Still right: Three runs a week gets most
people to 5k in about eight weeks." That is also how a friend answers it - they do not go and
look something up, they say where the number came from.

Narrow on purpose:

* the line has to ask (a question mark, or "is/are/does/will" at the front, or "still"/"right");
* the line has to carry a figure - a number and, where it has one, the unit the answer gave it;
* every other word in the line has to be one that names nothing ("so is eight weeks still
  right"), because "is eight weeks right for a puppy" is a question about a puppy;
* the figure has to be in an earlier answer of this chat, and that answer has to say what the
  figure rests on, or there is nothing to hand back;
* a line that takes issue with the answer ("that cant be right") is `bot/memory/doubt.py`'s, and
  a line that is `not` something is a different question, so both are left alone here.
"""
import re

from ..compose import pick

# The units an everyday answer gives a figure with. A unit is compared with its plural folded, so
# "eight weeks" in the answer matches "eight week" in the line.
UNITS = frozenset("""week month day year hour minute second mile km kilo stone pound percent
    session run portion time glass cup litre pint degree inch cm metre gram ml""".split())

# The numbers people write as words. Past twenty the tens are enough: nobody asks whether
# "seventy three weeks" still stands.
NUMBERS = {word: value for value, word in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
    "fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty "
    "ninety hundred".split())}
NUMBERS["couple"] = 2
NUMBERS["few"] = 3
# How often something is done, which is how people say a figure with no digits at all: "is once a
# week right" after "Change the sheets once a week".
NUMBERS["once"] = 1
NUMBERS["twice"] = 2
NUMBERS["thrice"] = 3

# A figure: a digit run or a number word, and the unit right after it when the line gives one.
FIGURE = re.compile(
    r"\b(\d[\d,]*(?:\.\d+)?|" + "|".join(sorted(NUMBERS, key=len, reverse=True)) + r")"
    r"(?:\s+(" + "|".join(sorted(UNITS, key=len, reverse=True)) + r")s?\b)?", re.I)

# A word that names nothing of its own, so a line of these plus a figure is a line about the
# figure. "not", "wrong" and "sure" are left out on purpose: they take issue with the answer, and
# `bot/memory/doubt.py` owns that reading.
NOTHING_NAMED = frozenset("""so and but or then ok okay right still is are was were am that
    this it they those these the a an of in on at for to do does did will would can could should
    my i me you we our yeah yes no anymore any more both quite really actually true correct
    stand stands work works hold holds apply applies changed change mean means all that's its
    it's again now today currently nowadays even just also too much very bit little""".split())

# The line has to ask. A question mark is one way; the others are the openers and the words that
# only make sense as a question about a figure ("is eight weeks right", "are five a day still ok").
QUESTION_OPENING = re.compile(
    r"^\W*(?:(?:so|and|but|ok|okay|then|right|oh|also|now)\W+)*"
    r"(?:is|are|was|were|does|do|did|will|would|should|can|could)\b", re.I)
ASKING = re.compile(r"\b(?:still|right|correct|true|ok|okay|the same|sure)\b|\?", re.I)

# A line longer than this is carrying something of its own, however much of it reads as filler.
MOST_WORDS = 9

# The answer the chat already gave, and how far back to look for the sentence that says what the
# figure rests on. A figure is often given bare first ("Eight weeks.") and explained a turn or two
# before that, which is where the reason is.
LOOK_BACK = 5
# A sentence this short is the figure on its own and says nothing about why.
SHORTEST_REASON = 6
MOST_REASON_WORDS = 45

SENTENCE = re.compile(r"(?<=[.!?])\s+")

# The figure with the reason the chat gave for it. The reason is the bot's own sentence, because
# the reason is a fact about the world and the bot has already said which one it used.
STANDS = (
    "Still right: {reason}",
    "That has not changed: {reason}",
    "Yes - and that is where it comes from: {reason}",
)

# The same when the chat never said what the figure rests on: the figure is all the answer there
# is, and saying it back is the honest reply rather than a card about something else.
CONFIRMS = (
    "Still right - {figure}.",
    "Yes, {figure} is still the number.",
    "That holds: {figure}, as before.",
)


def _number(word):
    word = str(word or "").strip(".,").lower()
    if not word:
        return None
    if word.replace(",", "").replace(".", "").isdigit():
        return float(word.replace(",", ""))
    return float(NUMBERS[word]) if word in NUMBERS else None


def _figures(text):
    """[(value, unit or "", where it starts, where it ends)] for the figures in a line."""
    found = []
    for match in FIGURE.finditer(str(text or "")):
        value = _number(match.group(1))
        if value is None:
            continue
        unit = (match.group(2) or "").lower().rstrip("s")
        found.append((value, unit, match.start(), match.end()))
    return found


def _names_the_figure(text, value, unit):
    """True when this text gives the same figure, with the same unit where the line names one.

    A line that says "nine hours" is not answered by an answer's bare "9" ("9 to 10 for hard
    boiled"): the unit is what a figure means, and matching the number alone would confirm a
    length the chat never gave.
    """
    for other, other_unit, _, _ in _figures(text):
        if other != value:
            continue
        if unit and unit != other_unit:
            continue
        return True
    return False


def _the_line_asks_about_a_figure_and_elsewhere_nothing(text):
    """The (value, unit) the line asks about, or None when it names something of its own."""
    line = " ".join(str(text or "").lower().replace("\u2019", "'").split())
    if not line or len(line.split()) > MOST_WORDS:
        return None
    if not (QUESTION_OPENING.search(line) or ASKING.search(line)) or not ASKING.search(line):
        return None
    figures = _figures(line)
    if len(figures) != 1:
        # No figure is not this reader's, and two are a comparison ("is eight weeks or twelve
        # closer") rather than a check of the one the answer gave.
        return None
    value, unit, start, end = figures[0]
    rest = (line[:start] + " " + line[end:]).split()
    for word in rest:
        word = word.strip(".,!?;:")
        if word in NOTHING_NAMED or word.rstrip("s") in UNITS or word in ("a", "an", "per",
                                                                          "each", "every"):
            continue
        # A word that names something of its own is the line's subject, and the figure is then a
        # detail of it rather than the thing asked about.
        if word.rstrip("'s") in NOTHING_NAMED:
            continue
        return None
    return value, unit, line[start:end].strip()


def _the_chat_gave_it(memory, value, unit):
    """True when one of the bot's own recent answers gives this figure with this unit."""
    if not isinstance(memory, dict):
        return False
    turns = memory.get("turns")
    if not isinstance(turns, list):
        return False
    return any(_names_the_figure(str(turn.get("bot") or ""), value, unit)
               for turn in turns[-LOOK_BACK:] if isinstance(turn, dict))


def _the_reason_behind(memory, value, unit):
    """The bot's own sentence that gives this figure and says what it rests on, or ""."""
    if not isinstance(memory, dict):
        return ""
    turns = memory.get("turns")
    if not isinstance(turns, list):
        return ""
    for turn in reversed(turns[-LOOK_BACK:]):
        said = str(turn.get("bot") or "") if isinstance(turn, dict) else ""
        if not said or not _names_the_figure(said, value, unit):
            continue
        # The first sentence that carries the figure and enough words to be a reason: the answer
        # leads with the figure and what it rests on, and a sentence later in the paragraph is
        # usually about something else that happens to hold the same number ("the health
        # guideline is 150 minutes ... which is three 50-minute sessions").
        for sentence in SENTENCE.split(said):
            sentence = sentence.strip()
            words = sentence.split()
            if not (SHORTEST_REASON <= len(words) <= MOST_REASON_WORDS):
                continue
            if _names_the_figure(sentence, value, unit):
                return sentence
    return ""


def the_figure_asked_about(text, memory):
    """(value, unit, phrase, reason) when the line asks whether a figure of the chat stands.

    `reason` is "" when the chat gave the figure and never said what it rests on: the answer is
    then the figure itself, said back as the thing that has not changed.
    """
    asked = _the_line_asks_about_a_figure_and_elsewhere_nothing(text)
    if not asked:
        return None
    value, unit, phrase = asked
    if not _the_chat_gave_it(memory, value, unit):
        # The figure is not the chat's: "is nine hours right" after an egg answer is a new
        # question about the world, and the answer to it is not "that holds".
        return None
    return value, unit, phrase, _the_reason_behind(memory, value, unit)


# --- "does that change the time?" -------------------------------------------------------------

# A change the person has just made ("actually its a veggie one, no mince") and then a question
# about whether it moves something of the answer they were given. The line names no figure and no
# thing: the time it asks about is the one in the chat's own answer, so the readers that want a
# figure in the line all pass on it and the knowledge base reaches for something else entirely.
CHANGE_ASK = re.compile(
    r"\b(?:does|do|will|would|should|did)\b[^.?!]{0,24}?"
    r"\b(?:change|affect|alter|make (?:a|any) difference to|matter (?:to|for)|impact)\b", re.I)
# The thing the change might move, and the units an answer gives it in. Only attributes with a
# figure in the chat's answer are answered here: "does that change the plan" has no figure to
# hand back, and guessing is worse than the hedge it already gets.
ATTRIBUTES = {
    "time": ("minute", "hour", "day", "week", "month"),
    "long": ("minute", "hour", "day", "week", "month"),
    "temperature": ("degree",),
    "heat": ("degree",),
}
ATTRIBUTE_WORDS = re.compile(
    r"\b(?:the|my|our|its)\s+(" + "|".join(ATTRIBUTES) + r"|cooking time|oven time|time)\b",
    re.I)
# A line about a machine's clock is a setting, not the chat's answer: "does that change the time on
# the boiler" is asking how to set a timer.
A_SETTING = re.compile(r"\b(?:boiler|thermostat|programmer|clock|timer|heating|timer\s+on)\b", re.I)
# The figure in the chat's own answer, with its unit: "35 to 40 minutes in the oven", "180C". A time
# written in two parts is one figure and is read as one ("1 hour 40 minutes"), because the minutes
# alone are the tail of it and not the answer.
# "1 hour 40 for a 2kg bird" says the minutes without the word: the compound arm takes it, as
# long as what follows is not a weight or a measure ("1 hour 250g" is not a time and a half).
FIGURED = re.compile(
    r"\b(\d[\d,.]*(?:\s*(?:to|or|-)\s*\d[\d,.]*)?)\s*(hours?|hrs?)\s+(\d[\d,.]*)\s*"
    r"(minutes?|mins?)?\b(?!\s*(?:g|kg|ml|cl|lb|lbs|oz|cm|degrees?)\b)"
    r"|\b(\d[\d,.]*(?:\s*(?:to|or|-)\s*\d[\d,.]*)?)\s*"
    r"(minutes?|mins?|hours?|hrs?|days?|weeks?|months?|degrees?|C\b|\u00b0C)", re.I)
UNIT_FAMILY = {"minute": "time", "min": "time", "hour": "time", "hr": "time", "day": "time",
               "week": "time", "month": "time", "degree": "temperature", "c": "temperature",
               "°c": "temperature"}

CHANGE_REPLIES = {
    "time": (
        "No - {figure} was the time and it stays that. What changed is what goes in it, not how "
        "long it takes.",
        "That does not move it: {figure}, same as before.",
        "Same time - {figure}. The swap changes what is in it, not how long it is in for.",
        "The time holds: {figure}. It is the dish that sets it, not the filling.",
        "No change there - {figure}, and that is the figure to cook to.",
    ),
    # The heat is not the time, and a sentence about minutes after "does that change the
    # temperature" reads as the bot not hearing the question.
    "temperature": (
        "The heat holds: {figure}, same as before.",
        "No change to the heat - {figure}, and that is the oven to cook it at.",
        "Same heat - {figure}. The swap changes what goes in the dish, not the oven.",
        "That does not move it: {figure}, the heat it was already to be cooked at.",
    ),
}


# Where the swap did move the figure, the reply says so and gives the new one. "That does not move
# it" is a claim, and handed back beside a figure the swap's own answer introduced it is false.
CHANGE_REPLIES_MOVED = {
    "time": (
        "That moves it: {figure} now, not the time from before.",
        "It does - {figure} for this version.",
        "Yes - {figure}. The swap changes how long it takes.",
        "It does move it: {figure}, so cook to that instead.",
    ),
    "temperature": (
        "The heat moves too: {figure} for this version.",
        "It does - {figure} now, not the oven from before.",
        "Yes, the heat changes: {figure}.",
    ),
}


def _in_minutes(number, unit):
    """A time figure as a number of minutes, so "1 hour 40 minutes" beats "20 minutes"."""
    value = _number(number)
    if value is None:
        return 0.0
    unit = unit.lower().rstrip("s")
    if unit in ("hour", "hr"):
        return value * 60
    if unit == "day":
        return value * 1440
    if unit == "week":
        return value * 10080
    if unit == "month":
        return value * 43200
    return value


def _the_best(candidates, family):
    """The figure to hand back: the whole time rather than a rate, and the first temperature."""
    if not candidates:
        return ""
    if family == "temperature":
        return candidates[0][2]
    # "About 20 minutes per 500g plus 20 minutes at 190C, so a 2kg bird takes roughly 1 hour 40
    # minutes": the answer gives the rate first and the total last, and the total is the figure
    # the person is asking whether it still holds.
    best = max(candidates, key=lambda found: _in_minutes(found[0].split()[0], found[1]))
    return best[2]


def _figures_in_answer(said, family):
    """The figures one answer gives for this attribute, as [(value, unit, as said)]."""
    candidates = []
    for match in FIGURED.finditer(str(said or "")):
        if match.group(1):
            whole = (f"{match.group(1)} {match.group(2).lower()} {match.group(3)} "
                     f"{(match.group(4) or 'minutes').lower()}")
            minutes = (_in_minutes(match.group(1), "hour")
                       + _in_minutes(match.group(3), "minute"))
            if family != "time":
                continue
            candidates.append((str(minutes), "minute", whole))
            continue
        unit = match.group(6).lower().rstrip("s")
        if UNIT_FAMILY.get(unit) != family:
            continue
        figure = f"{match.group(5)} {match.group(6).lower()}"
        if unit in ("c", "\u00b0c"):
            figure = f"{match.group(5)}C"
        candidates.append((match.group(5), match.group(6).lower(), figure))
    return candidates


def _the_same_figure(one, other):
    """True when two figures are the same one: "12 to 15 minutes" and "12-15 minutes"."""
    return re.sub(r"\D", "", str(one or "")) == re.sub(r"\D", "", str(other or ""))


# The words that are about the answer rather than about what is in the dish. Two answers share a
# subject word when they are about the same thing ("rice" then "brown rice"), and the swap's figure
# is then this dish's; with nothing in common the second answer is a card about something else.
NOT_THE_SUBJECT = frozenset("""minute minutes hour hours second seconds day days week weeks
    month months degree degrees oven ovens tray tins pan pans tin dish dishes cook cooking cooked
    bake baked roast roasted about until when then they this that with from your yours each every
    before after while total same time times heat high medium low fan""".split())


def _subjects(said):
    return {word for word in re.findall(r"[a-z]{4,}", str(said or "").lower())
            if word not in NOT_THE_SUBJECT}


def _about_the_same_thing(one, other):
    """True when two answers are about the same thing, so a figure in the second is this dish's."""
    return bool(_subjects(one) & _subjects(other))


# A different way of cooking is not a swap of one thing for another: a slow cooker chicken at 6 to
# 8 hours is the same bird and a different time, and "that does not move it" about it is false.
# Nothing here knows the new method's time, so the reader stays out of the way.
A_METHOD_CHANGE = re.compile(
    r"\b(?:slow cooker|crock ?pot|pressure cooker|instant pot|air ?fryer|microwave|steam\w*|"
    r"sous ?vide|barbecue|bbq|grill\w*|poach\w*|deep[- ]?fr(?:y|ied|ying)|boil\w*|"
    r"on the hob|in the oven instead|oven instead)\b", re.I)


def _a_figure_for(memory, family):
    """(figure, moved) - the figure to hand back, and whether the swap moved it.

    The swap is the last thing the person said, so the newest answer is the answer to it, and the
    one before is the answer that set the plan going. Where they give the same figure, or the
    answer to the swap gives none, the plan's figure holds. Where they give different figures about
    the same thing - "im making rice" then "im using brown rice instead", 10 to 12 minutes against
    25 to 30 - the swap did move it, and handing back the new figure while saying "same as before"
    would have a person cook raw rice. Where the second answer is a card about something else ("im
    roasting a chicken" / "theres no foil" answered with a dhal) its figure is not this dish's, and
    the reader says nothing rather than guess.
    """
    if not isinstance(memory, dict):
        return "", False
    turns = memory.get("turns")
    if not isinstance(turns, list):
        return "", False
    answers = [str(turn.get("bot") or "") for turn in turns[-2:] if isinstance(turn, dict)]
    if not answers:
        return "", False
    plan = _the_best(_figures_in_answer(answers[0], family), family)
    swapped = (_the_best(_figures_in_answer(answers[1], family), family)
               if len(answers) > 1 else "")
    if not swapped:
        return plan, False
    if not plan:
        # Nothing was said before the swap, so the only figure in reach is the one the swap's own
        # answer gives, and it is the plan now.
        return swapped, True
    if _the_same_figure(swapped, plan):
        return plan, False
    if _about_the_same_thing(answers[0], answers[1]):
        return swapped, True
    said = str(turns[-1].get("user") or "") if isinstance(turns[-1], dict) else ""
    if A_METHOD_CHANGE.search(said):
        return "", False
    # The answer to the swap is about something else and gives no figure for this dish: the figure
    # the plan was given still stands, and it is the chat's own.
    return plan, False


# A change of size or quantity is not a swap: a bigger lasagne for six takes longer than one for
# four, and "that does not move it" would then be wrong. The change is one of the last few lines.
# There has to be a swap to ask about, and only a swap: "my sister is coming with her two kids so
# its eleven now" is a change of size, and a leg of lamb for eleven takes longer. The words below
# are the ones a substitution is made of - the thing swapped out, or the thing swapped in.
A_CHANGE = re.compile(
    r"\b(?:instead|rather than|without|swap\w*|switch\w*|replace\w*|substitut\w*|veggie|"
    r"vegetarian|vegan|gluten|dairy|free from|omitted|skipped|cut out|left out|leave out|"
    r"made it with|no [a-z]+)\b", re.I)


def _a_change_was_made(memory):
    """True when one of the last few lines of theirs swaps something for something else."""
    if not isinstance(memory, dict):
        return False
    said = [str(turn.get("user") or "") for turn in (memory.get("turns") or [])
            if isinstance(turn, dict)]
    return any(A_CHANGE.search(line) for line in said[-3:])


QUANTITY = (r"(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|"
            r"twenty|thirty|\d+)")
WHOSE = r"(?:of us|people|guests?|kids?|portions?|slices|servings?|adults?|children)"
A_SIZE_CHANGE = re.compile(
    r"\b(?:bigger|larger|smaller|double|doubled|halve|halved|batch|twice as|half as)\b"
    # "more"/"extra"/"less" and a bare "for" are not a size on their own: "i swapped the mince for
    # mushrooms" is the commonest way to say a swap, and it was standing the reader down.
    r"|\b(?:more|extra|less|fewer)\s+" + WHOSE + r"\b"
    r"|\bfor\s+" + QUANTITY + r"\b"
    r"|\bfor\s+(?:\w+\s+)?" + WHOSE + r"\b"
    r"|\b(?:feed|feeding|cooking for)\s+(?:" + QUANTITY + r"|" + WHOSE + r")\b"
    r"|\b" + QUANTITY + r"\s*" + WHOSE + r"\b"
    r"|\b(?:there will be|there are|its|it's|so its|so it's|now)\s+(?:one|two|three|four|five|"
    r"six|seven|eight|nine|ten|eleven|twelve|twenty|\d+)\b", re.I)


def _a_change_of_size(memory):
    """True when the change the person just made was a size or a quantity."""
    if not isinstance(memory, dict):
        return False
    said = [str(turn.get("user") or "") for turn in (memory.get("turns") or [])
            if isinstance(turn, dict)]
    return any(A_SIZE_CHANGE.search(line) for line in said[-3:])


def the_change_asked_about(text, memory):
    """(attribute, figure, moved) when the line asks whether a change moves a figure, else None.

    Narrow on purpose: the line has to ask with does/will/would, has to name the attribute with
    "the"/"my" in front of it, has to be about nothing else, and the chat has to hold a figure for
    that attribute in one of its own answers. A line about a machine's clock is a setting.
    """
    line = " ".join(str(text or "").lower().replace("\u2019", "'").split())
    if not line or len(line.split()) > MOST_WORDS + 3:
        return None
    if not CHANGE_ASK.search(line) or A_SETTING.search(line):
        return None
    if _a_change_of_size(memory) or not _a_change_was_made(memory):
        return None
    named = ATTRIBUTE_WORDS.search(line)
    if not named:
        return None
    word = named.group(1).lower()
    if word in ("time", "cooking time", "oven time", "long"):
        attribute, family = "time", "time"
    elif word in ("temperature", "heat"):
        attribute, family = "temperature", "temperature"
    else:
        return None
    # Every other word has to name nothing: "does that change the time for a chicken" asks about a
    # chicken, and the answer is that chicken's time, not this chat's.
    rest = line[:named.start(1)] + " " + line[named.end(1):]
    for word_ in rest.split():
        word_ = word_.strip(".,!?;:")
        if not word_ or word_ in NOTHING_NAMED or word_ in ("that", "this", "it", "which"):
            continue
        if word_ in ("change", "changed", "changes", "affect", "affects", "alter", "alters",
                     "impact", "matter", "difference", "make", "makes", "made", "a", "an",
                     "any", "to", "for", "the", "on", "of", "in", "with", "much", "long",
                     "time", "cooking", "oven"):
            continue
        return None
    figure, moved = _a_figure_for(memory, family)
    if not figure:
        return None
    return attribute, figure, moved


def change_reply(text, memory):
    """The reply to "does that change the time?" - the chat's own figure, handed back."""
    found = the_change_asked_about(text, memory)
    if not found:
        return None
    attribute, figure, moved = found
    line = " ".join(str(text or "").lower().split())
    pools = CHANGE_REPLIES_MOVED if moved else CHANGE_REPLIES
    pool = pools.get(attribute) or pools["time"]
    return pick(pool, memory, line).format(figure=figure)


def reply_for(text, memory):
    """The reply to a yes/no about a figure the bot gave, or None for every other line."""
    found = the_figure_asked_about(text, memory)
    if not found:
        return None
    _, _, phrase, reason = found
    line = " ".join(str(text or "").lower().split())
    if not reason:
        return pick(CONFIRMS, memory, line).format(figure=phrase)
    return pick(STANDS, memory, line).format(reason=reason)

