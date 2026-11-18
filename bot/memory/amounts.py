"""A count the person reports, read against the count the last answer named.

Advice names a figure to aim at ("six to eight glasses a day", "about 7,000 to 8,000 steps a day"),
and the next thing people do is say how they are doing against it: "i have about 4 glasses".
Nothing read the two together. The count in the answer is said with how often it is done, which
files it as a rate rather than an amount, so the person's own count of the same thing was answered
with a receipt, a search hedge or a greeting.

The reading here is deliberately narrow:

* the line is a count the person says they do, not a question about an amount (the ask patterns
  own those) and not a count of something else ("i have 3 children");
* the length they give is their own, not spent on something ("2 hours of meetings");
* the answer names one figure of that same thing, a range counting as one ("aim for 30 minutes a
  day, and 60 if you can manage it" is a list of choices, not one figure to aim at);
* and the figure is not the person's own number said back ("four glasses is on the short side").

Then the person is told where they stand, and the turn after can ask for the gap: "how much more do
i need" names nothing of its own, and the counts read one turn earlier answer it.
"""

import re

# A count, as a number or as a word: "4", "4.5", "7,000", "six".
_COUNT = (r"(?:\d[\d,]*(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)")

# What the count is a count of. Only things said the same way on both sides are compared, so the
# table is what the bot talks about in these lines rather than every unit in the language.
# The things this module reads are the things the store reads, and only the ones where the turn
# after the report still answers as it does without it. The store counts glasses, steps, minutes,
# hours, grams, miles and kilometres (`_AMOUNTS` in bot/modules/memory_store.py) and can read a count
# said with how often it is done ("2 sessions a week"), so "how much more do i need" and "is that
# enough" after the report land on the store's own answer, which is the one the person already gets
# on main. Cups, litres, calories and units are left alone: the store has no such family, so a
# report about one of them silences the answer the persona had ("i have about 5 cups" then "is that
# too much" was answered "Sounds good." where main gave the caffeine limit).
_THINGS = (
    ("glasses", r"glasses?"),
    ("steps", r"steps?"),
    ("minutes", r"minutes?|mins?"),
    ("hours", r"hours?|hrs?"),
    ("grams", r"grams?|grammes?|g"),
    ("milligrams", r"milligrams?|mg"),
    ("micrograms", r"micrograms?|mcg"),
    ("kilometres", r"kilometres?|kilometers?|kms?"),
    ("miles", r"miles?"),
    ("sessions", r"sessions?"),
)

# The person says the count as their own: "i have about 4 glasses", "i walk 2000 steps a day".
A_THEIR_OWN = re.compile(r"\b(?:i|we)\b[^.?!]{0,24}?\b(?:have|had|get|got|do|eat|drink|walk|run"
                         r"|take|use|manage|average|track|log|hit|only|now|usually|normally"
                         r"|still|am on)\b", re.I)

# A question about an amount is one of the ask patterns' lines, not a count reported.
A_AN_ASK = re.compile(r"\?|^\s*(?:how|what|which|why|when|where|who|should|can|could|do|does|did"
                      r"|is|are|was|were|will|would|any|got any)\b", re.I)

# A length spent on something else is not a count of their own: "i have 2 hours of meetings today"
# is two hours in a meeting, not two hours of the thing the answer named.
A_A_LENGTH_OF = re.compile(r"\b" + _COUNT + r"\s*(?:hours?|hrs?|minutes?|mins?)\s+of\s+\w", re.I)

_COUNT_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
                8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve"}


def _a_value(word):
    """The number a count says: "4", "7,000", "six". None when it is not a count."""
    word = (word or "").strip().lower().replace(",", "")
    try:
        return float(word)
    except ValueError:
        pass
    return float(list(_COUNT_WORDS.values()).index(word) + 1) if word in _COUNT_WORDS.values() \
        else None


def _a_number(value):
    """A count as the reply says it: "two", "1,000"."""
    if value == int(value) and int(value) in _COUNT_WORDS:
        return _COUNT_WORDS[int(value)]
    return "{:,}".format(int(value)) if value == int(value) else str(value)


def _counts(text):
    """Every figure said with a unit of the table, in the order it was said."""
    found = []
    for thing, pattern in _THINGS:
        for match in re.finditer(r"(" + _COUNT + r")\s*(?:-\s*)?(?:" + pattern + r")\b",
                                 text or "", re.I):
            value = _a_value(match.group(1))
            if value is None:
                continue
            found.append({"at": match.start(), "value": value, "thing": thing,
                          "said": match.group(0).strip(" .,!?"),
                          "period": _the_period_at(text, match.end())})
    found.sort(key=lambda item: item["at"])
    return found


def _the_period_at(text, at):
    """The period said right after the figure ending at `at`, as "a day" or "a week"."""
    match = re.match(r"\s*(?:a|an|per|each|every|most)\s+(day|week|night|month)\b",
                     (text or "")[at:], re.I)
    if not match:
        return None
    return "a week" if match.group(1).lower() in ("week", "month") else "a day"


def a_count_they_report(text):
    """{"value", "thing", "said", "period"} for a count the person reports, or None."""
    if not isinstance(text, str) or not text.strip():
        return None
    if A_AN_ASK.search(text) or not A_THEIR_OWN.search(text):
        return None
    if A_A_LENGTH_OF.search(text):
        return None
    found = _counts(text)
    # One figure only: two counts in the line is a comparison of their own ("i do 6000 steps but
    # my wife does 10000") or two things at once, and neither is one count to read.
    if len(found) != 1:
        return None
    return found[0]


def _the_figure_named(answer, thing, mine):
    """The one figure of `thing` the answer names, as {"low", "high", "said", "period"}."""
    pattern = dict(_THINGS).get(thing)
    if not pattern or not answer:
        return None
    # A range is said with "to", a dash, "and" or "or" ("three or four sessions a week is plenty
    # to start" is one range, not the figure four), and a figure said twice in different words is
    # still one figure.
    ranges = list(re.finditer(r"(" + _COUNT + r")\s*(?:to|-|\u2013|and|or)\s*(" + _COUNT + r")"
                              r"\s*(?:-\s*)?(?:" + pattern + r")\b", answer, re.I))
    spans = [match.span() for match in ranges]
    singles = [match for match in re.finditer(r"(" + _COUNT + r")\s*(?:-\s*)?(?:" + pattern
                                              + r")\b", answer, re.I)
               if not any(start <= match.start() and match.end() <= end for start, end in spans)]
    figures = []
    for match in ranges:
        low, high = _a_value(match.group(1)), _a_value(match.group(2))
        if low is None or high is None or low >= high:
            continue
        figures.append({"low": low, "high": high, "said": match.group(0).strip(" .,!?"),
                        "period": _the_period_at(answer, match.end())})
    for match in singles:
        value = _a_value(match.group(1))
        if value is None:
            continue
        figures.append({"low": value, "high": value, "said": match.group(0).strip(" .,!?"),
                        "period": _the_period_at(answer, match.end())})
    # A guideline names one figure or one range. Two figures of the same thing is a list of
    # choices ("30 minutes a day, and 60 if you can manage it"), and picking one would be a guess.
    # The count is of every figure the answer named, before the person's own number is taken out:
    # "A mile is 20 minutes at a brisk walk ... or about 15 minutes if you are pushing it" names
    # two, and dropping the 20 because the person also said 20 would leave the 15 looking like the
    # one figure to aim at - which is how "i do about 20 minutes" became "past the 15 minutes".
    named = len(figures)
    # The answer's own figure, said back to them ("you have 4 glasses"), is not a figure to aim at.
    figures = [figure for figure in figures
               if not (figure["low"] == figure["high"] == mine)]
    if named > 1 and figures:
        return None
    if len(figures) != 1:
        return None
    return figures[0]


def _the_periods_disagree(mine, theirs):
    """True when the two figures are said on periods that cannot be read against each other."""
    if mine is None or theirs is None:
        return False
    return mine != theirs


def against_the_last_answer(said, answer):
    """The count they reported against the figure the last answer named, or None."""
    if not isinstance(said, dict):
        return None
    figure = _the_figure_named(answer, said.get("thing"), said.get("value"))
    if figure is None:
        return None
    if _the_periods_disagree(said.get("period"), figure.get("period")):
        return None
    if figure["low"] <= 0:
        return None
    return {"thing": said["thing"], "mine": said["value"], "mine_said": said["said"],
            "low": figure["low"], "high": figure["high"], "figure": figure["said"],
            "figure_period": figure.get("period"),
            "a_ceiling": bool(A_CEILING.search(answer or ""))}


def _the_figure_said(against):
    said = "the " + _a_mid_sentence(against["figure"])
    period = against.get("figure_period")
    if period and period not in said:
        said += " " + period
    return said


def _a_mid_sentence(figure):
    """The answer's own figure, written mid-sentence: "six to eight glasses a day"."""
    word = (figure or "").split(" ")[0]
    if word[:1].isupper() and word.lower() in _COUNT_WORDS.values():
        return figure[0].lower() + figure[1:]
    return figure


# A figure the answer frames as a ceiling - "the limit for an adult is 6g", "no more than two
# litres", "around four cups" - so being over it is worth trimming back. A range that is only a
# target is not a ceiling: the water answer says six to eight glasses is plenty, and telling someone
# on ten glasses that they are "past" it as if it were a fault is wrong.
A_CEILING = re.compile(r"\blimits?\b|\bno more than\b|\bat most\b|\bcap(?:ped)?\b"
                       r"|\bsafe (?:limit|amount|upper)\b|\bdo not (?:go )?(?:over|exceed)\b",
                       re.I)


def _the_aim_said(against):
    """The answer's figure, written mid-sentence and said the way the answer said it.

    Two things about this line are read by the turn after it. `_enough_reply` in the store answers
    "how much more do i need" and "is that enough" from the figures in the reply above, and it reads
    a range as the figure to aim at only when the range is followed by its unit: "the six to eight
    glasses", not "the six to eight". It also skips a range said with a rate straight after it
    ("six to eight glasses **a day**"), because a figure said with how often it is done is a rate
    rather than an amount. So the unit stays and the period goes, and the follow-up keeps the
    answer it has on main:

        i have about 4 glasses / how much more do i need
          -> Another two glasses would put you at the six to eight glasses ...

    `the_comparison` is read by a person, so the line goes on to say where that figure comes from
    rather than talking about the bot's own earlier answer.
    """
    said = _a_mid_sentence(against["figure"])
    aim = "the " + said
    period = against.get("figure_period")
    if period and aim.endswith(" " + period):
        aim = aim[: -len(period) - 1]
    return aim


def the_comparison(against):
    """Where the count they reported stands against the figure the answer named."""
    mine, low, high = against["mine"], against["low"], against["high"]
    aim, said = _the_aim_said(against), against["mine_said"]
    if against.get("a_ceiling"):
        # A figure the answer frames as a limit is not a figure to reach: under it is where a
        # person wants to be, and being over it is the one thing worth changing.
        if mine > high:
            return "That is over {}, which is worth trimming back.".format(aim)
        if mine < low:
            return "That is under {}, which is where you want to be.".format(aim)
        return "That is inside {}, which is fine - that is a ceiling, not a target.".format(aim)
    if mine < low:
        return "That is a fair way under {} most people need.".format(aim)
    if mine > high:
        return "That is past {}, which is fine - more than that is no problem.".format(aim)
    return "That is inside {} most people need.".format(aim)
