"""A saving goal carries its own arithmetic, and the sum is a follow-up waiting to happen.

People say the goal before they say the date: "i want to save 2000 pounds" and then "by june".
Both lines on their own name nothing to work out - a goal is a statement, and a date is a date -
so neither reached the money entry, and the chat module answered the goal with "start with the
smallest version of it, not the whole thing", which is advice about a habit and says nothing
about money; the date after it got "got it - is there anything you'd like a hand with".

The two lines are one question, and the knowledge base already knows how to answer it: the sum,
the date and the weeks left give the weekly figure. This module reads that question:

* a saving goal with a sum in it is that question, with the date if the line carries one;
* a line that is only a date ("by june", "actually make that by april") is the same question
  about the sum the person named a turn or two ago;
* nothing else is a saving question, so every other line passes.

What it hands back is a plain question in the person's own terms, which `bot/modules/answers.py`
answers from `bot/knowledge/money.py`.
"""
import re

# The words that make a line about putting money by, and the words that make a sum a goal rather
# than the price of something they are buying ("i want to save 200 on my car insurance" is not a
# goal, so a sum followed by "on" or "off" is a saving on a bill, not a pot).
# "putting by" is the phrase, but people put the money inside it - "im putting 300 a month by for
# a deposit" - and the word order broke the reader, so the sum went with it and the line read as a
# rate about nothing. The object is allowed a few words, not a clause.
SAVING = re.compile(r"\b(?:save|saves|saving|saved|savings|saving up|putting by|putting away|"
                    r"putting\b[^.?]{0,18}?\b(?:by|away|aside)|put\b[^.?]{0,18}?\b(?:by|away|aside)|"
                    r"setting aside|stashing|put by|put away|set aside|stash|pot|fund)\b", re.I)
# A sum of money, with the way people write it: "£2,000", "2000 pounds", "2k", "2 grand".
SUM = re.compile(r"(?:£|\$|\u20ac)\s*(\d[\d,]*(?:\.\d+)?)\s*(k|grand|thousand)?"
                 r"|\b(\d[\d,]*(?:\.\d+)?)\s*(k|grand|thousand|pounds|quid|euros|dollars|bucks)\b",
                 re.I)
# A sum that is a price or a saving on a bill rather than a pot: "save 200 on my insurance",
# "save 50 off the bill", "save 20 a month on it".
NOT_A_POT = re.compile(r"\s*(?:on|off|from|for)\s+(?:my|the|our|a|an|each|every|it)\b|"
                       r"\s*a\s+(?:month|week|year)\s+(?:on|off|from)\b", re.I)
# A goal with no unit on it ("i need to save 3000"), but not a rate ("put by 150 a month") and not
# a sum that already carried a unit of its own, which `SUM` reads above.
BARE_FIGURE = re.compile(r"\b(\d{3,7})\b(?!\s*(?:k|grand|thousand|pounds|quid|euros|dollars|"
                         r"bucks)\b)(?!\s*(?:a|per|each)\s+(?:month|week|year|fortnight))", re.I)
MONTHS = ("january", "february", "march", "april", "may", "june", "july", "august",
          "september", "october", "november", "december")
# The dates people give a saving goal that are not a month: "by christmas" is December, "by
# easter" April, "by next summer" June, "by the end of the year" December. A month table on its
# own leaves the commonest deadline of all - Christmas - unanswered, so these stand in for the
# month they fall in. The last one is what is left of "by the end of the year" once the lead has
# taken "the end of".
NAMED_WHEN = (("christmas", "december"), ("xmas", "december"), ("new year", "december"),
              ("hogmanay", "december"), ("halloween", "october"), ("valentine", "february"),
              ("easter", "april"), ("black friday", "november"), ("spring", "march"),
              ("summer", "june"), ("autumn", "september"), ("fall", "october"),
              ("winter", "december"), ("the year", "december"))
WHEN_WORDS = "|".join(MONTHS) + "|" + "|".join(word for word, _month in NAMED_WHEN)
# The ways a date is said: "by june", "before april", "for april", "until christmas".
# The "end of" is kept as part of the date, because it changes which day is meant: said in
# mid-November, "by the end of december" is 51 days away and "by december" is 21. The words were
# dropped here, so the money entry counted to the first of the month and answered a saving goal
# with "it is one pay packet" when the person had seven weeks.
END_OF = r"(?:(?:at\s+)?the\s+end\s+of\s+|end\s+of\s+)?"
DATE = re.compile(r"\b(?:by|before|until|till|for|in|at the end of|end of)\s+" + END_OF +
                  r"(?:next\s+|this\s+|early\s+|late\s+)?(" + WHEN_WORDS + r")\b", re.I)
# A correction of the date said a turn or two ago: "actually make that by april", "no, by june".
CORRECTING = re.compile(r"^\s*(?:(?:actually|no|sorry|nope|rather|instead|oh)\b[\s,]*"
                        # A correction that names its subject first: "actually its 20 thousand",
                        # "no thats 20000". The figure is the whole of what follows, so the
                        # pronoun-verb is part of the correction and not of the sum.
                        r"(?:(?:its|it's|it\s+is|it\s+was|thats|that's|that\s+is)\b[\s,]*)?|"
                        r"(?:make|change)\s+(?:that|it)\s+(?:to\s+)?|i\s+mean\b[\s,]*)*", re.I)
# What a line that is nothing but a date looks like once the correction and the lead are taken off.
# A relative one is the same date as "the end of <month>" said without a month: "by the end of
# next month" names no month at all, so neither pattern above matched it and the line kept the
# rate table the money entry gives a goal with no date in it.
END_OF_RELATIVE = re.compile(r"\b(?:by|before|until|till|in time for|for|in|at the end of|end of)"
                             r"\s+(?:at\s+)?the\s+end\s+of\s+(next\s+month|this\s+month|"
                             r"next\s+week|this\s+week|next\s+year|this\s+year|"
                             r"(?:the\s+)?(?:summer|winter|spring|autumn|fall))\b", re.I)
BARE_END_OF_RELATIVE = re.compile(r"^\s*(?:by|before|until|till|for|in)?\s*(?:at\s+)?the\s+end\s+of"
                                  r"\s+(next\s+month|this\s+month|next\s+week|this\s+week|"
                                  r"next\s+year|this\s+year)"
                                  r"\s*[.!,]?\s*$", re.I)
BARE_DATE = re.compile(r"^\s*(?:by|before|until|till|for|in)?\s*(?:at\s+|the\s+)?(?:end\s+of\s+)?"
                       r"(?:next\s+|this\s+|early\s+|late\s+)?(" + WHEN_WORDS + r")\s*[.!,]?\s*$",
                       re.I)
# Money already in the pot is not the goal: "i saved 50 pounds this month" and "i put by 50 last
# month" report what is there, and a date answered on them invents a goal nobody named. The saving
# verb has to point forward - "want to save", "need to save", "saving for" - so a line that only
# looks back, or carries an "already / so far / this month" marker and no intent, names no goal.
ALREADY = re.compile(r"\b(?:already|so far|to date|up to now|last (?:month|year|week)|"
                     r"this (?:month|year|week))\b", re.I)
INTENT = re.compile(r"\b(?:want|wants|wanted|need|needs|needed|hope|hoping|plan|planning|aim|aiming|"
                    r"going to|gonna|would like|like to|love to|trying to|goal|target)\b", re.I)
PAST_SAVING = re.compile(r"\b(?:saved|have\s+saved|had\s+saved|managed\s+to\s+save)\b", re.I)
# Money they already hold is not money they are aiming at. "my savings are 4000", "we have got 2
# grand in savings" and "my savings pot has 3000 in it" all say what is in the pot, and read as a
# goal the bot tells someone how many months it would take to save what they already have. The
# figure is held in the pot, so the pot word and a have-word sit beside each other, or the sum is
# said to be *in* one.
HELD = re.compile(r"\b(?:in|into)\s+(?:(?:my|the|our|a|an)\s+)?(?:savings?|pot|fund|account)\b"
                  r"|\bin\s+it\b"
                  r"|\b(?:savings?|pot|fund)\b[^0-9]{0,14}\b(?:is|are|was|were|has|have|holds|"
                  r"sits\s+at|stood\s+at|sat\s+at|of)\b", re.I)


def _a_sum(text):
    """The sum of money in the line, as a plain number, or None."""
    line = text or ""
    for match in SUM.finditer(line):
        figure = match.group(1) or match.group(3) or ""
        unit = (match.group(2) or match.group(4) or "").lower()
        if not figure:
            continue
        if NOT_A_POT.match(line[match.end():]):
            continue  # a saving on a bill, not a pot
        try:
            value = float(figure.replace(",", ""))
        except ValueError:
            continue
        if unit in ("k", "grand", "thousand"):
            value *= 1000
        if value < 20:
            continue  # "save 5 pounds a week" is a habit, not a goal
        return int(round(value))
    # A goal written without its unit: "i need to save 3000", "im saving for 5000". People leave
    # the pounds off when the saving word is already in the line, and the whole chat then had no
    # goal to work with. A rate ("put by 150 a month") is not a pot, and a year is not a sum.
    for match in BARE_FIGURE.finditer(line):
        try:
            value = int(match.group(1))
        except ValueError:
            continue
        if value < 100 or 1990 <= value <= 2100:
            continue
        if NOT_A_POT.match(line[match.end():]):
            continue  # the same saving on a bill, said without the unit
        return value
    return None


def _a_date(text):
    """The date the line puts the goal in, in the person's own words ("june", "christmas"), or "".

    The word is kept as they said it so the answer can use it back - "\u00a3500 by Christmas" reads
    better than "\u00a3500 by December" - and `_month_of` turns it into a month to count with.
    "The end of" is kept with it: it names the last day of the month rather than the first, and
    the two are a month apart.
    """
    relative = END_OF_RELATIVE.search(text or "")
    if relative:
        return "the end of " + " ".join(relative.group(1).lower().split())
    match = DATE.search(text or "")
    if not match:
        return ""
    word = match.group(1).lower()
    said = match.group(0).lower()
    if "end of" in said:
        return "the end of " + word
    return word


def _month_of(when):
    """The month a date falls in, so a named one can be counted: "christmas" is December."""
    word = str(when or "").lower().strip()
    if word.startswith("the end of "):
        # "the end of december" is December, counted to its last day by the money entry.
        word = word[len("the end of "):].strip()
    if word in ("next month", "this month"):
        # "next month" has no month name in it, so it is counted from today: December said in
        # November, or November itself for "this month".
        import datetime

        step = 1 if word == "this month" else 2
        return MONTHS[(datetime.date.today().month + step - 2) % 12]
    if word in MONTHS:
        return word
    for name, month in NAMED_WHEN:
        if name in word:
            return month
    return ""


# A sum on top of another sum is one pot: "i want to save another 2000 on top of the 1000 i have"
# is £3,000, and read as either half it answers about money they are not asking about.
TOGETHER = re.compile(r"(?:£\s*)?(\d[\d,]*(?:\.\d+)?)\s*(k|grand|thousand)?\s*(?:pounds?|quid)?\s*"
                      r"(?:on\s+top\s+of|plus|alongside|as\s+well\s+as|and\s+another|together\s+with)"
                      r"\s*(?:the\s+|my\s+|our\s+)?(?:£\s*)?(\d[\d,]*(?:\.\d+)?)\s*"
                      r"(k|grand|thousand)?", re.I)


def _two_sums_added(line):
    """The two sums the line adds together, or 0 when it names only one."""
    found = TOGETHER.search(str(line or ""))
    if not found:
        return 0
    total = 0
    for figure, unit in ((found.group(1), found.group(2)), (found.group(3), found.group(4))):
        try:
            value = float(figure.replace(",", ""))
        except (TypeError, ValueError):
            return 0
        if (unit or "").lower() in ("k", "grand", "thousand"):
            value *= 1000
        total += int(round(value))
    return total if total >= 20 else 0


# The pot and the rest of it said in one line. "i have 1000 saved already and want another 2000"
# is £3,000 in all, with £2,000 still to find, and the second sum is what the arithmetic is about.
# Read as either half the answer is about a pot the person is not asking about: the £1,000 they
# already hold (how long to save what they have), or £2,000 with the £1,000 ignored.
HELD_SAID = re.compile(r"(?:£\s*)?(\d[\d,]*(?:\.\d+)?)\s*(k|grand|thousand)?\s*"
                       r"(?:pounds?|quid)?[^.!?]{0,40}?"
                       r"\b(?:saved|put\s+by|set\s+aside|put\s+aside|in\s+savings|in\s+the\s+pot)\b",
                       re.I)
FURTHER_SAID = re.compile(r"\b(?:another|a\s+further|an\s+extra|extra|more)\b\s*(?:£\s*)?"
                          r"(\d[\d,]*(?:\.\d+)?)\s*(k|grand|thousand)?", re.I)


def _pounds(figure, unit):
    """A figure written as people write it ("2", "2k", "2 grand") as a number, or 0."""
    try:
        value = float(str(figure or "").replace(",", ""))
    except (TypeError, ValueError):
        return 0
    if (unit or "").lower() in ("k", "grand", "thousand"):
        value *= 1000
    return int(round(value)) if value >= 20 else 0


def the_pot_and_the_rest(text):
    """(money already held, money still to find) when the line names both, else (0, 0).

    The two sums are the pot and the rest of it: "i have 1000 saved already and want another
    2000", "theres 500 put by and i want another 1500". Only a line with both is this shape - a
    report of money saved with nothing further named is not a goal at all, and a further sum with
    no pot behind it is an ordinary goal.
    """
    line = str(text or "")
    if not line.strip():
        return 0, 0
    further = FURTHER_SAID.search(line)
    held = HELD_SAID.search(line)
    if not further or not held:
        return 0, 0
    if further.start() < held.start():
        # "another 2000 on top of the 1000 i have" is the other way round, and `_two_sums_added`
        # already reads it.
        return 0, 0
    pot = _pounds(held.group(1), held.group(2))
    rest = _pounds(further.group(1), further.group(2))
    if not pot or not rest:
        return 0, 0
    return pot, rest


# The pot said on a line of its own: "i want to save 3000 for a car" / "i have 1000 saved
# already". The line names no goal, so it is not one; it is how much of the goal is already there.
# Without it the date turn has no pot to work against and the line itself is answered with an echo
# ("Got it - you have 1000 saved already") that tells the person nothing.
POT_REPORTED = re.compile(r"\b(?:this\s+(?:month|year|week)|last\s+(?:month|year|week)|so\s+far|"
                          r"to\s+date)\b", re.I)


# The pot said with the word "already" instead of a saving verb: "i already have 1500", "we have
# got 2000 already". HELD_SAID needs a word like saved or set aside beside the figure, so a line
# whose only saving word is "already" was not a pot at all - and a chat that had said
# "i already have 1500" was told, two turns later, how long the whole 5,000 takes.
ALREADY_HELD = re.compile(r"\b(?:already|so far)\b[^.!?]{0,24}?\b(?:have|has|got|hold|put)\b"
                          r"\s*(?:£\s*)?(\d[\d,]*(?:\.\d+)?)\s*(k|grand|thousand)?\b", re.I)
ALREADY_AFTER = re.compile(r"\b(?:have|has|got|hold)\b\s*(?:£\s*)?(\d[\d,]*(?:\.\d+)?)\s*"
                           r"(k|grand|thousand)?\s*(?:pounds?|quid)?\s+(?:already|so far)\b", re.I)


# A line that says what it is aiming at is not only a pot, even with a "have" in it: "i want to
# have 500 quid saved by december" was read as £500 already held, and the figure-by-a-date answer
# that the rest of the chat needed was lost. The date on the end is the clearest sign of all - a
# pot is money now, so nothing already saved is "by December".
AIM_AT_A_SUM = re.compile(r"\b(?:want|wants|wanting|need|needs|hope|hoping|goal|aim|aiming|plan|"
                          r"planning|trying|like)\b[^.!?]{0,30}?"
                          r"\b(?:have|save|saved|set\s+aside|put\s+by|reach|get\s+to|afford)\b",
                          re.I)
BY_A_DATE = re.compile(r"\bby\s+(?:next\b|the\s+end\b|\d|january|february|march|april|may|"
                       r"june|july|august|september|october|november|december|christmas|"
                       r"spring|summer|autumn|winter|xmas|easter|payday|then\b)", re.I)


def the_pot_said_alone(text):
    """The money the line says is already saved, when the line is only that, else 0."""
    line = str(text or "")
    if not line.strip() or FURTHER_SAID.search(line):
        return 0
    if AIM_AT_A_SUM.search(line) or BY_A_DATE.search(line):
        return 0
    held = HELD_SAID.search(line)
    if held and not POT_REPORTED.search(line):
        if INTENT.search(line) and not re.search(r"\b(?:have|has|got|got\s+\w+)\b", line, re.I):
            return 0
        return _pounds(held.group(1), held.group(2))
    for pattern in (ALREADY_HELD, ALREADY_AFTER):
        found = pattern.search(line)
        if not found:
            continue
        pot = _pounds(found.group(1), found.group(2))
        # A small figure beside "already have" is not a pot: "we already have 2 kids" is a family,
        # and a couple of pounds saved is not a saving plan. Money people hold is said in tens.
        if pot >= 50:
            return pot
    return 0


# The pot as a position rather than a report: "im on 4 thousand", "im at 4k", "ive got 4000
# towards it", "we're up to 3000". A person tracking a goal says where they are, and on main every
# one of these lines was answered by the greeting pool as an echo ("On 4 thousand, then.") while
# the goal beside it - "i need 20 thousand" - went on being the goal still unfilled.
AT_A_FIGURE = re.compile(
    r"\b(?:im|i'?m|i\s+am|we'?re|we\s+are|ive|i'?ve|i\s+have|we'?ve|we\s+have)\s+"
    r"(?:now\s+|only\s+|just\s+|already\s+)?"
    r"(?:on|at|up\s+to|got(?:\s+to)?|onto|standing\s+at)\s+"
    r"(?:about\s+|around\s+|nearly\s+|just\s+)?"
    r"(?:£\s*)?(\d[\d,]*(?:\.\d+)?)\s*(k|grand|thousand)?\b", re.I)


def the_pot_they_are_on(text):
    """The money the line says the person is on their way to, when that is what the line says.

    "im on 4 thousand" against a goal of 20 thousand is £4,000 of the way there. Only a line that
    says nothing but where they are counts: a line naming what they earn ("im 29 and on about
    30k") is a salary, not a pot, and a line naming a goal ("im on 4 thousand a month") is a rate.
    """
    line = str(text or "")
    if not line.strip() or NOT_A_PRICE.search(line) or _a_rate(line):
        return 0
    match = AT_A_FIGURE.search(line)
    if not match:
        return 0
    if NOT_A_POT.match(line[match.end():]):
        return 0
    return _pounds(match.group(1), match.group(2))


# A rate is a figure with "a month", "a week", "each month" after it: the same words as a pot, and
# the two are told apart by what the line is doing with the figure.
A_RATE = re.compile(r"\b(?:a|per|each|every)\s+(?:month|week|year|fortnight|pay\s*day|"
                    r"payday|payslip)\b", re.I)


def _a_rate(line):
    """True when the figure in the line is a rate rather than a sum."""
    return bool(A_RATE.search(str(line or "")))


def _the_pot_they_are_on(memory):
    """The last position the person said they were on towards the goal, or 0."""
    turns = [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)]
    for turn in reversed(turns[-6:]):
        pot = the_pot_they_are_on(str(turn.get("user") or ""))
        if pot:
            return pot
    return 0


# The ask for the gap rather than for a date, a rate or a length: "how far off am i", "how much
# more do i need", "how much have i got left to go". On main "how far off am i" after a pot and a
# goal was answered by the countdown reader as a date - "That's about 3 weeks away - Friday 4
# December" - because "on 4 thousand" had filed the 4th of the month as a date, and the question
# about money got a day of the week.
HOW_FAR_OFF = re.compile(
    # Not "how far along am i": that is the pregnancy question, and it is a different turn.
    r"\bhow\s+far\s+(?:off|away)\b|"
    r"\bhow\s+much\s+(?:more\s+)?(?:do\s+i\s+need|have\s+i\s+(?:got\s+)?left|is\s+left)\b|"
    r"\bhow\s+much\s+(?:more|left)\s+to\s+go\b|"
    r"\bwhat'?s\s+left\s+(?:to\s+go|on\s+it)\b", re.I)


# The goal said as what they need, once the chat has said what they are saving for: "im saving for
# a house deposit" / "i need 20 thousand". The goal reader above wants the saving word on the same
# line as the figure, and people split it - the purpose in one turn, the money in the next - so
# the figure that fills a goal already named is the goal, and the gap question has two figures to
# work between instead of one.
NEED_A_FIGURE = re.compile(
    r"\b(?:need|needs|need\s+to\s+(?:get\s+to|reach|have|save|find)|"
    r"have\s+to\s+(?:find|reach|save)|should\s+have|aiming\s+for|target\s+is)\b", re.I)


def _the_goal_they_need(memory):
    """The sum the chat says they need, when the chat has already said what they save for."""
    turns = [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)]
    lines = [str(t.get("user") or "") for t in turns[-6:]]
    # A rate said beside the thing they are putting by still names the thing: "im putting 300 a
    # month by for a deposit" says both what the money is for and how fast it grows, and read as
    # a line with a figure on it, the purpose was dropped and "i need 20 thousand" had no goal to
    # fill.
    if not any(SAVING.search(line) and (not _a_sum(line) or _a_rate(line)) for line in lines):
        return 0
    for line in reversed(lines):
        if the_pot_they_are_on(line) or the_pot_said_alone(line) or _a_rate(line):
            continue
        if NEED_A_FIGURE.search(line):
            wanted = _a_sum(line)
            if wanted:
                return wanted
    return 0


def asks_how_far_off(text):
    """True when the line asks how far off the goal the person is."""
    return bool(HOW_FAR_OFF.search(str(text or "")))


def the_gap_left(text, memory):
    """The money between the pot and the goal, said back, or "".

    The two figures are the chat's own: the goal it named and the position it last heard. Only
    when both are held and the pot is short of the goal - a gap of nothing is not a gap, and a
    pot past the goal is a different answer ("you're there").
    """
    line = str(text or "")
    if not asks_how_far_off(line) or _a_sum(line) or _a_rate(line):
        return ""
    goal, pot = the_goal_and_the_pot(memory)
    if not goal:
        return ""
    if not pot or pot >= goal:
        # No pot said yet, or the pot already past the goal: both are a different answer, and the
        # gap question is only the gap.
        return ""
    said = _the_gap_said(goal, pot)
    if _the_gap_was_just_said(said, memory):
        return _the_gap_again(goal, pot, memory)
    return said


def _the_gap_said(goal, pot):
    """The two figures side by side: what is left, and how much of it is already there."""
    left = goal - pot
    share = int(round(100.0 * pot / goal))
    return ("£%s to go of £%s - you're £%s in, %d%% of the way there."
            % (format(left, ","), format(goal, ","), format(pot, ","), share))


def _the_gap_was_just_said(said, memory):
    """True when the bot's own last line was this same sentence.

    The position line and the question after it both want the gap, so asking the question straight
    after the position would hand the person the same sentence twice in a row - the one thing a
    reply must never do.
    """
    turns = [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return False
    return " ".join(str(turns[-1].get("bot") or "").split()) == " ".join(said.split())


def _the_gap_again(goal, pot, memory):
    """The same gap said another way: the length at the rate they settled on, else a restatement.

    A rate the chat has already settled on ("i can put by 300 a month") is the thing that turns the
    gap into a date, which is the next thing a saver wants and not a number they have just read.
    """
    rate = _the_rate_in_the_chat(memory)
    if rate:
        # The length is about the money still to find, and the pot is already in hand: £20,000 at
        # £300 a month is 67 months, but £16,000 is 54, and the 67 argues with the gap just given.
        said = _the_length_at_that_rate(goal - pot, rate, "month", pot)
        if said:
            return said
    return ("Still £%s to go - you've £%s of the £%s in the pot."
            % (format(goal - pot, ","), format(pot, ","), format(goal, ",")))


def the_goal_and_the_pot(memory):
    """(goal, pot) as the chat holds them, the goal from whichever reader knows it. (0, 0) else."""
    goal = (_the_goal_in_the_chat(memory) or _the_goal_said_as_a_price(memory)
            or _the_goal_they_need(memory))
    if not goal:
        return 0, 0
    pot = _the_money_already_held(memory) or _the_pot_they_are_on(memory)
    return goal, pot


def the_pot_position(text, memory):
    """The gap said back when the line reports the position itself, or "".

    "i need 20 thousand" / "im on 4 thousand" is the same pair of figures the gap question asks
    about, said without a question: on its own the line was answered with an echo ("On 4
    thousand, then.") which told the person nothing they had not just typed.
    """
    if not the_pot_they_are_on(text) or asks_how_far_off(text) or _a_sum_that_is_a_goal(text):
        return ""
    if the_pot_said_alone(text):
        # "i have 1000 saved already" is the same fact with a report on it, and that turn has an
        # answer of its own ("£2,000 still to find: ...") which this one must not take away.
        return ""
    goal, pot = the_goal_and_the_pot(memory)
    # The position is in the line being read, and the turn's own line is not in memory["turns"]
    # yet when a reply is chosen, so it is read from the line first.
    pot = the_pot_they_are_on(text) or pot
    if not goal or not pot or pot >= goal:
        return ""
    return _the_gap_said(goal, pot)


def _a_sum_that_is_a_goal(text):
    """True when the line carries a goal of its own, so it is not only a position."""
    line = str(text or "")
    if _a_rate(line):
        return False
    return bool(NEED_A_FIGURE.search(line) and _a_sum(line))


def rate_question_for(amount, when=""):
    """The money question about a sum the module works out itself, or "" - the money still to
    find is not a figure the line names, so the question has to be written for it."""
    if not amount or amount < 20:
        return ""
    if when:
        return ("How much do i need to put by a week to have %s pounds by %s?"
                % (format(amount, ","), _in_the_money_readers_words(when)))
    return "How much do i need to put by a week to have %s pounds?" % format(amount, ",")


def the_money_already_held(memory):
    """Public name for the pot, for the arithmetic outside this module that reads it too."""
    return _the_money_already_held(memory)


def _the_money_already_held(memory):
    """The money the person said is already in the pot, from the last few lines, or 0."""
    turns = [t for t in (memory or {}).get("turns") or () if isinstance(t, dict)]
    for turn in reversed(turns[-6:]):
        line = str(turn.get("user") or "")
        pot, _rest = the_pot_and_the_rest(line)
        if pot:
            return pot
        pot = the_pot_said_alone(line)
        if pot:
            return pot
        # "im on 4 thousand" is the same fact said as a position rather than as a report, and the
        # length and the gap are both about it: read as nothing, the goal was answered as though
        # not a penny of it were already there.
        pot = the_pot_they_are_on(line)
        if pot:
            return pot
    return 0


# The knowledge base says the pot before it says the sums ("For £2,000: £100 a month is 20
# months"). With the pot already said in the lead-in, the opener is the same sum twice.
POT_OPENER = re.compile(r"^For\s+£\s*[\d,]+:\s*")


def without_the_pot_opener(answer):
    """The answer with its "For £2,000: " opener taken off, so a lead-in can say the pot once."""
    return POT_OPENER.sub("", str(answer or ""), count=1)


def _names_a_goal(line):
    """The sum when the line is aiming at money rather than reporting money already put by.

    A line with an aim in it ("i want to save 2000") is always a goal, whatever else it says.
    Without one it is a report of what is in the pot, which is not a goal.
    """
    line = str(line or "")
    added = _two_sums_added(line)
    if added and SAVING.search(line):
        return added
    pot, rest = the_pot_and_the_rest(line)
    if pot and rest and SAVING.search(line):
        # The pot and the rest of it are one goal: "i have 1000 saved already and want another
        # 2000" is £3,000, and read as £1,000 it answers how long to save money they have.
        return pot + rest
    if INTENT.search(line) and SAVING.search(line):
        aim = _a_sum(line)
        if aim:
            return aim
    if not (SAVING.search(line) and _a_sum(line)):
        return 0
    if INTENT.search(line):
        return _a_sum(line)
    if ALREADY.search(line) or PAST_SAVING.search(line) or HELD.search(line):
        return 0
    return _a_sum(line)


# "how long will that take" after a goal and the rates offered is the same question in the other
# unit: asked for the time the person got the rates again, or - when the goal named a purpose
# ("...for a holiday") - the package-travel rules, because the purpose word took the line. A line
# with a figure in it ("how long at 300 a month") is a rate named and is answered elsewhere.
HOW_LONG_ASK = re.compile(
    r"^\W*(?:(?:and|but|so|ok|okay|then|oh|right|yeah)\W+)*"
    r"(?:how\s+long"
    r"(?:\s+(?:will|would|does|do|did|is|to)\s+(?:that|it|this)"
    r"(?:\s+(?:take|be))?"
    r"(?:\s+to\s+(?:save|get)(?:\s+(?:that|it|there|the\s+money))?)?)?"
    r"|how\s+many\s+(?:months|years|weeks)(?:\s+is\s+(?:that|it|this))?"
    r"|how\s+much\s+time(?:\s+(?:will|would|does)\s+(?:that|it|this)\s+take)?)"
    r"\s*[?!.]*\s*$", re.I)


# The same ask in the other shapes people use for it: "how long until i have it", "how long till
# it is saved", "how long to get there". The tail after these words is the person's own way of
# naming the goal, so only the words in front of it have to be recognised - but they have to name
# the goal's side of it ("how long to cook a chicken" is a chicken, not this question).
HOW_LONG_UNTIL = re.compile(
    r"^\W*(?:(?:and|but|so|ok|okay|then|oh|right|yeah)\W+)*how\s+long\s+"
    r"(?:until|till|til|before)\s+(?:i|we|you|it|its|it's|that|this|there)\b"
    r"|^\W*(?:(?:and|but|so|ok|okay|then|oh|right|yeah)\W+)*how\s+long\s+to\s+"
    r"(?:save|have|get|reach|afford|be there)\b", re.I)


# The same question asked from the other end: not how long it takes but when it lands. "when will
# i have enough" and "when will we get there" were answered by the money arithmetic of the chat
# from the figures on the screen, and that answer read the whole goal - so a chat that had already
# been told "£10,800 still to find" was handed "at 400 a month, 15,000 takes about 38 months" on
# its last turn, the pot the person had already saved gone. The length asks above do not match it:
# no "how long" in the line. The words after "when" have to name landing on the goal, so "when
# will i start saving" and "when should i set it up" are not this question.
WHEN_AT_THE_GOAL = re.compile(
    r"^\W*(?:(?:and|but|so|ok|okay|then|oh|right|yeah)\W+)*"
    r"when\s+(?:will|would|can|could|should|might)\s+(?:i|we|you|it|its|it's|that|this)\s+"
    r"(?:have|get|be|reach|afford|save|hit|make|manage)\b", re.I)


def asks_how_long(text):
    """True when the line asks how long the goal takes and names no figure itself."""
    line = " ".join(str(text or "").lower().split())
    if not line or len(line.split()) > 8 or re.search(r"\d", line):
        return False
    return bool(HOW_LONG_ASK.search(line) or HOW_LONG_UNTIL.match(line)
                or WHEN_AT_THE_GOAL.match(line))


def how_long_it_takes(memory):
    """The goal said as a length of time, at the gentle rate and one faster, or "".

    The goal is read from the answer above when the line named a purpose instead of a sum
    ("i want to save 2000 pounds for a holiday"), so the length is about the money that answer
    offered rates for.

    With no rate and no date in the chat yet, "how long will that take" has an answer that is
    already known: the goal at a rate the pay can carry. Handed the options again the line said
    nothing new; handed nothing it got a search hedge.
    """
    if not memory:
        return ""
    previous = _the_line_before(memory)
    goal = _the_goal_in_the_chat(memory)
    # A goal the person priced rather than named ("im saving up for a car" / "the one i want is
    # 2500") is read here only: the other readers of the goal offer rates and dates, and a price
    # is enough for the length but not for those.
    priced = 0 if goal else _the_goal_said_as_a_price(memory)
    if not goal:
        goal = priced
    from_the_answer = False
    if not goal:
        # The goal can also be the one the answer above worked out, when the person's own lines
        # never named it in words this module reads ("i need 5000" is a sum and a need, not a
        # saving word). The pot comes off that goal too: a chat that never said "saving" still
        # said "i already have 1500", and the length it got was for the whole 5,000.
        goal = _the_goal_in_the_answer(memory)
        turns_said = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
        last_bot = str((turns_said[-1] or {}).get("bot") or "") if turns_said else ""
        # An answer that already worked the pot out ("£10,800 still to find: ...") is the money
        # left, not the goal, and taking the pot off it again counts it twice.
        from_the_answer = bool(goal) and "still to find" in last_bot.lower()
    pot = _the_money_already_held(memory) if not from_the_answer else 0
    if goal and 0 < pot < goal:
        # The length is about the money still to find, not the whole goal: "i have 1000 saved
        # already" then "how long will that take" is the £2,000 left, and the answer above
        # ("£2,000 still to find: ...") already said so. Read as the goal it answered with
        # "For £1,000: £750 a month is 2 months", the pot they already hold.
        goal = goal - pot
    else:
        pot = 0
    if not goal or goal < 100:
        return ""
    if previous and _a_length_was_asked(previous):
        # Asked twice: "how long will it take to save 5000" then "how long will that take". The
        # answer above already gave the length at these rates, so saying it again is the repeat
        # the money entry avoids by offering the next sums up.
        return ""
    if _the_rate_in_the_chat(memory) or _the_date_in_the_chat(memory):
        # A rate or a date already in play is answered by the arithmetic on it.
        rate = _the_rate_in_the_chat(memory)
        if rate and goal and priced and not _the_date_in_the_chat(memory):
            # The goal is on the screen only as the price of the thing ("im saving up for a car" /
            # "the one i want is 2500"). The money entry reads goals by the saving words beside
            # the sum, so it has no goal here and answered with the rate line again; the sum and
            # the rate are both known, so the length is arithmetic.
            return _the_length_at_that_rate(goal, rate, "month", pot)
        if rate and rate < goal:
            # The rate in play answers the length, unless the reply just above gave this very
            # figure (the same sum twice is the repeat this module exists to avoid). A rate that
            # came in beside something else ("i earn 1600 a month and i put by 200 a month") was
            # answered with the pay, so its sum was never on the screen and is still owed.
            months = -(-goal // rate)
            said_turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
            last = str((said_turns[-1] or {}).get("bot") or "") if said_turns else ""
            if not re.search(r"\b%d\s+months?\b" % months, last):
                return without_what_was_just_said(
                    _a_rate_against_the_goal(goal, rate, memory), memory)
        return ""
    rate, period = _a_rate_in_another_period(memory)
    if rate:
        # "i can put 100 a week towards it" is a rate in play, and the sums offered below are
        # monthly ones: the length came out "At £100 a month, £1,200 takes 12 months" for someone
        # who said £100 a week, four times too long and arguing with the bot's own "£1,200 at £433
        # a month (£100 a week) is 3 months" a turn earlier. The length is arithmetic on the rate
        # they gave, said in the unit they gave it in.
        return _the_length_at_that_rate(goal, rate, period, pot)
    slow = -(-goal // 100)
    fast = -(-goal // 250)
    income = _the_income_in_the_chat(memory)
    if income:
        # The only money in the chat is what they earn, so the rate has not been said and the
        # options above are already on the screen. Naming the pay is what makes the question
        # answerable, and it is the one thing the person has already done for us.
        said_goal = "the £%s still to find" % format(goal, ",") if pot else (
            "£%s" % format(goal, ","))
        return ("How much of the £%s can you put by each month? At £100 a month %s takes "
                "%s." % (format(income, ","), said_goal, _months(slow)))
    # The rest of a goal is the sum the answer above was about, so it is named rather than an
    # unattached "£2,000" that reads as a different pot from the one on the screen.
    said = ("the £%s still to find takes " % format(goal, ",")) if pot else (
        "£%s takes " % format(goal, ","))
    if fast == slow:
        return ("At £100 a month, " + said
                + "%s. Pick the rate your pay can carry and set the "
                  "standing order for the day after payday." % _months(slow))
    return ("At £100 a month, " + said
            + "%s - or %s at £250 a month. Pick the one your pay can "
              "carry." % (_months(slow), _months(fast)))


def _only_a_date(text):
    """The month when the line is nothing but a date, or ""."""
    bare = (text or "").strip()
    bare = CORRECTING.sub("", bare).strip()
    relative = BARE_END_OF_RELATIVE.match(bare)
    if relative:
        return "the end of " + " ".join(relative.group(1).lower().split())
    match = BARE_DATE.match(bare)
    if not match:
        return ""
    word = match.group(1).lower()
    if "end of" in match.group(0).lower():
        return "the end of " + word
    return word


def is_only_a_date(text):
    """True when the line is nothing but a date ("by june", "by christmas").

    A date on its own is a follow-up, never a subject of its own: "by christmas" after a saving
    goal used to be read as Christmas shopping and answered with a gift budget, and the money
    question it really is never got asked.
    """
    return bool(_only_a_date(text))


def _only_a_sum(text):
    """The sum when the line corrects a figure with nothing but a figure, or 0.

    A correction carries no saving word ("actually make that 1000", "sorry, 1500"), so a chat that
    corrects its goal used to keep answering the sum it had before: the store said "Save 1000 pounds
    - got it" and the date still worked on 500. The line has to be nothing but the figure, or "no,
    1000 a month" would be read as a new pot instead of a rate.
    """
    bare = CORRECTING.sub("", str(text or "")).strip()
    if not bare or len(bare.split()) > 4:
        return 0
    aim = _a_sum(bare)
    rest = re.sub(r"[^a-z]", "", SUM.sub("", bare).lower()).strip()
    if rest:
        return 0  # the line says more than the figure: not a correction of it
    if not aim:
        # A correction often leaves the unit off, because the figure it corrects had one: "i want
        # to save 500 pounds" / "actually make that 1000" is a bigger pot, not a line about
        # nothing. Only a line that is nothing but the figure gets here, so a bare number is safe.
        figure = re.sub(r"[^0-9]", "", bare)
        if len(figure) >= 3 and int(figure) >= 20:
            return int(figure)
        return 0
    return aim


def asks_about_saving(text):
    """True when the line states a saving goal with a sum in it.

    The chat module asks this before it offers a plan: "i want to save 2000 pounds by april" is a
    money question, and "start with the smallest version of it" answers nothing about it.
    """
    return bool(_names_a_goal(text))


def _the_money_still_to_find(memory):
    """The goal less the money already in the pot: what is still to be found.

    "i have 1000 saved already and want another 2000" is a £3,000 goal with £1,000 already there,
    and every figure the person wants next - the monthly rate, the weeks left, the date - is about
    the £2,000 still to find. The whole pot is the goal; the arithmetic is on the rest.
    """
    whole = _the_goal_in_the_chat(memory)
    held = _the_money_already_held(memory)
    if whole and 0 < held < whole:
        return whole - held
    return whole


def _the_goal_in_the_chat(memory):
    """The sum the person said they were saving, from the last few lines, or 0."""
    return _the_goal_named_in_a_line(memory)


def _the_goal_named_in_a_line(memory):
    """The sum a line puts beside a saving word ("im saving 3000 for a car"), or 0."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    for turn in reversed(turns[-6:]):
        line = str(turn.get("user") or "")
        # A corrected sum replaces the one before it, whether or not the correcting line says the
        # word: "i want to save 500 pounds" / "actually make that 1000" / "by december" is a goal
        # of 1,000 by December.
        corrected = _only_a_sum(line)
        if corrected:
            return corrected
        if the_pot_said_alone(line):
            # Money already in the pot is not the goal: "i want to save 3000" / "i have 1000
            # saved already" is a goal of £3,000, and read as the pot the date turn answers about
            # the £1,000 they already have.
            continue
        aim = _names_a_goal(line)
        if aim:
            return aim
    return 0


# The thing being saved for is often priced rather than named as a goal: "im saving up for a car"
# then "the one i want is 2500", or "its a corsa, 2500". No saving word sits beside the sum, so a
# reader that wants one beside it saw no goal at all and answered the length with the rate line
# again: "how long will that take" said "£347 a month (£80 a week) is £4,164 in a year", a repeat
# of the turn before. The price of the thing is the pot when the chat has said what it is saving
# for and never put a sum beside it.
PRICE_WORDS = re.compile(r"\b(?:is|are|was|were|costs?|cost|about|around|at|for|goes for)\b", re.I)
# A pay packet is not the price of the thing: "im 29 and on about 30k" said a sum with a word
# from the price list in it, and read as the goal it made a house deposit a £30,000 pot and the
# length question a hedge about six months. What the person earns is not what they are saving for.
# The price arrives after the thing, with a comma and no price word on it: "its a corsa, 2500".
A_TRAILING_SUM = re.compile(r",\s*£?\s*\d")
NOT_A_PRICE = re.compile(r"\b(?:earn\w*|salary|wages?|income|payslip|paid|pension|"
                        r"before tax|after tax|take home|i'?m\s+\d+|i am\s+\d+|how old)\b", re.I)

def _the_goal_said_as_a_price(memory):
    """The sum said of the thing they are saving for, when no line named a goal, or 0."""
    turns = [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)]
    recent = turns[-6:]
    if not any(SAVING.search(str(t.get("user") or ""))
               and (not _a_sum(str(t.get("user") or "")) or _a_rate(str(t.get("user") or "")))
               for t in recent):
        # Nothing in the chat says what is being saved for without a figure on it, so a price in
        # it is about something else - a repair, a bill - and not the pot.
        return 0
    for turn in reversed(recent):
        line = str(turn.get("user") or "")
        if not line or the_pot_said_alone(line):
            continue
        if the_pot_they_are_on(line):
            # Where they are on the way is not the price of the thing: "i need 1200" / "im at 300
            # towards it" read the position as the goal, so the goal and the pot became the same
            # £300 and the next ask ("how much more do i need") had no gap to work between.
            continue
        if A_RATE.search(line) or A_RATE_ANY_OTHER_PERIOD.search(line):
            continue   # a rate, not a price
        if not (PRICE_WORDS.search(line) or A_TRAILING_SUM.search(line)):
            continue   # a bare figure said of nothing ("2500") is a correction, read elsewhere
        if NOT_A_PRICE.search(line):
            continue   # what they earn is not what they are saving for
        aim = _a_sum(line)
        if aim and aim >= 100:
            return aim
    return 0


# The pot in the answer above. The goal is often not in anything the person typed: "im trying to
# save for a house deposit" says no figure, and the money entry answers "Aim for 10% of the price:
# £20,000 on a £200,000 home". The arithmetic then says it out loud - "£20,000 at £400 a month is
# 50 months" - and that is where the next line's figure comes from. Without it "thats another 40"
# and "how long will it take" have no pot to work against.
A_GOAL_STATED = re.compile(r"(?:\bfor\s+)?£\s*(\d[\d,]*(?:\.\d+)?)\s*(k)?\s*"
                           r"(?::|\bat\s+£|\bis\s+(?:about\s+)?\d)", re.I)


# The length asked loosely, for the line *before* this one: "how long will it take to save 5000"
# names a figure, so `asks_how_long` does not take it, and it is still the same question this line
# is repeating.
A_LENGTH_WAS_ASKED = re.compile(
    r"\bhow\s+long\b|\bhow\s+many\s+(?:months|years|weeks)\b|\bhow\s+much\s+time\b", re.I)


A_LENGTH_SAID = re.compile(
    r"\b(?:in|within|over|inside)\s+(?:the\s+next\s+|the\s+coming\s+)?"
    r"(?:\d[\d,]*|a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|eighteen|"
    r"twenty[-\s]?four|a\s+couple\s+of|a\s+few)\s*"
    r"(?:months?|years?|weeks?)\b"
    r"|\b(?:the\s+)?end\s+of\s+(?:the\s+)?(?:month|year|week)\b", re.I)


def a_length_was_said(line):
    """True when the line names the time it has: "save 10k in 6 months", "5000 in a year".

    A goal and a length are a whole question - the figure to put by each month - and the money
    entry works it out from the line itself. Read as a goal on its own the same line got the
    three rates nobody asked for ("For \u00a310,000: \u00a3100 a month is 100 months, ...").
    """
    return bool(A_LENGTH_SAID.search(str(line or "")))


def _a_length_was_asked(line):
    """True when a line asks how long something takes, however much else it says."""
    return bool(A_LENGTH_WAS_ASKED.search(str(line or "")))


def _the_line_before(memory):
    """The person's line before this one, or "" - the ask a follow-up is repeating."""
    turns = [t for t in (memory or {}).get("turns") or () if isinstance(t, dict)]
    if not turns:
        return ""
    return str(turns[-1].get("user") or "")


def _the_goal_in_the_answer(memory):
    """The pot stated in the bot's last few answers, or 0."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict) and t.get("bot")]
    for turn in reversed(turns[-3:]):
        for found in A_GOAL_STATED.finditer(str(turn.get("bot") or "")):
            try:
                value = float(found.group(1).replace(",", ""))
            except ValueError:
                continue
            if (found.group(2) or "").lower() == "k":
                value *= 1000
            value = int(value)
            if value >= 100:
                return value
    return 0


# Nothing but a new sum, asked after one: "i want to save 2k" / "what about 1k". The smaller pot
# is the same question about a different figure, and read as nothing in particular it went to a
# search hedge while the answer above was already working out "For £2,000: ...".
ANOTHER_SUM = re.compile(
    r"^\s*(?:(?:and|but|so|then|ok|okay)\s+)?(?:(?:what|how)\s+about|and)\s+(?:£\s*)?"
    r"(\d[\d,]*(?:\.\d+)?)\s*(k|grand|thousand|pounds?|quid)?\s*[?!.]*\s*$", re.I)


# The same new pot with the verb left on it: "save 1000" after a goal of 2,000. Read as a rate it
# worked the old pot out at a thousand a month - "£2,000 at £1,000 a month is 2 months" - which is
# arithmetic about a question nobody asked.
A_GOAL_SUM = re.compile(r"^\s*(?:(?:and|but|so|then|ok|okay)\b[\s,]*)*"
                        r"(?:i(?:'d|'ll)?\s+)?(?:will\s+|just\s+|only\s+|need\s+to\s+|"
                        r"want\s+to\s+)?sav(?:e|es|ing)\s+(?:£\s*)?(\d[\d,]*(?:\.\d+)?)\s*"
                        r"(k|grand|thousand|pounds?|quid)?\s*[?!.]*\s*$", re.I)


def another_sum_asked(text, memory):
    """The line read as a saving goal on a new sum, or "".

    Only when the line is that and nothing else, and only when a goal is already in the chat: a
    sum with no question around it after one is the same arithmetic on a different figure.
    """
    found = ANOTHER_SUM.match(str(text or "")) or A_GOAL_SUM.match(str(text or ""))
    if not found:
        return ""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    talked_money = False
    for turn in turns[-2:]:
        line = str(turn.get("user") or "")
        if _only_a_sum(line) or _names_a_goal(line):
            talked_money = True
    if not talked_money:
        return ""
    figure = _a_sum(text)
    if not figure or figure < 100:
        return ""
    return "save £%s" % format(figure, ",")


# A rate the person has already settled on: "if i put by 200 a month". Once they have one, a date
# on its own asks whether that rate gets them there, not for a new weekly figure, and the money
# entry answers the rate they gave.
# A word or two can sit between the sum and the month: "we have 150 spare a month", "200 put by
# each month". The money entry reads the same gap (`BETWEEN_THE_SUM_AND_THE_RATE`), and without it
# here the rate the person settled on was invisible to the length question, which then answered
# the goal at £100 and £250 a month as if no rate had ever been named.
A_RATE = re.compile(r"(?:£\s*)?(\d[\d,]*)\s*(?:pounds?\s+)?(?:[a-z]+\s+){0,2}?"
                    r"(?:a|per|each)\s+month\b", re.I)


def _a_rate_is_settled(memory):
    """True when a rate the person gave is already in the chat."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    for turn in turns[-4:]:
        if A_RATE.search(str(turn.get("user") or "")):
            return True
    return False


# A rate the person gave with a period that is not a month. A_RATE reads a month only, so the
# rate the length question is about can sit in the chat and be invisible here.
A_RATE_ANY_OTHER_PERIOD = re.compile(r"(?:£\s*)?(\d[\d,]*)\s*(?:pounds?\s+)?(?:[a-z]+\s+){0,2}?"
                                     r"(?:a|per|each)\s+(week|fortnight|year)\b", re.I)


# How many months one of each period is, for the "about 6 months" aside.
MONTHS_IN_A = {"week": 12 / 52.0, "fortnight": 12 / 26.0, "month": 1.0, "year": 12.0}


def _the_length_at_that_rate(goal, rate, period, pot=0):
    """The goal at a rate given in weeks, fortnights or years, in that same unit.

    A part payment is another one, so a goal that does not divide exactly rounds up: £1,200 at £50
    a week is 24 weeks, and £1,250 at the same rate is 25 payments.
    """
    count = -(-goal // rate)
    said = ("the £%s still to find takes " % format(goal, ",")) if pot else (
        "£%s takes " % format(goal, ","))
    line = "At £%s a %s, %s%s %s" % (format(rate, ","), period, said, count,
                                    period if count == 1 else period + "s")
    if period == "year":
        return line + "."
    months = int(round(count * MONTHS_IN_A[period]))
    if period != "month" and months >= 2:
        line += " (about %s)" % _months(months)
    return line + "."


def _a_rate_in_another_period(memory):
    """The rate and the period when the person gave one in weeks, fortnights or years."""
    turns = [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)]
    for turn in reversed(turns[-6:]):
        found = A_RATE_ANY_OTHER_PERIOD.search(str(turn.get("user") or ""))
        if not found:
            continue
        try:
            value = int(found.group(1).replace(",", ""))
        except ValueError:
            continue
        if value >= 5:
            return value, found.group(2).lower()
    return 0, ""

# What a month's money is when it is what they are paid rather than what they put by. "i earn
# 1800 a month" is an income, and read as the rate it was one: the goal's length was worked out on
# a wage, or - worse - the length question stood down because "a rate is already in play", and the
# turn ended on "that is everything I have on that one, so I would only repeat myself" to somebody
# who had just been told the bot would work out exactly how long it takes.
INCOME_FRAME = re.compile(
    r"\b(?:earn|earns|earning|earned|paid|salary|wages?|income|take[- ]home|brings?\s+in|"
    r"pension|benefits?|allowance)\b|\b(?:i|we)\s+(?:get|make|bring)\b", re.I)
# The same is true of money that goes out every month: "i pay 800 a month rent and i want to save
# 5000" names the rent, and read as the saving rate it answered the goal at £800 a month - a
# figure that would only be right if the rent were not being paid at all.
OUTGOING_FRAME = re.compile(
    r"\b(?:rent|mortgage|bills?|childcare|nurser(?:y|ies)|loan|debt|overdraft|"
    r"council\s+tax|energy|electric(?:ity)?|gas|heating|insurance|commut(?:e|ing)|"
    r"transport|travel|groceries|food\s+shop|spend(?:ing)?|goes\s+on|paying\s+out|"
    r"outgoings|repayments?)\b", re.I)
# The words that end a clause, so "i earn 1800 a month and i put by 200" keeps its rate.
CLAUSE_EDGE = re.compile(r"[,;.]|\band\b|\bbut\b|\bso\b")


def _is_an_income(line, found):
    """True when the figure in `found` is what the person is paid, not what they put by."""
    before = CLAUSE_EDGE.split(str(line or "")[:found.start()])[-1]
    return bool(INCOME_FRAME.search(before))


def _is_an_outgoing(line, found):
    """True when the figure in `found` is money that goes out each month, not money put by."""
    text = str(line or "")
    return bool(OUTGOING_FRAME.search(text[max(0, found.start() - 40):found.end() + 40]))


def _is_not_a_rate(line, found):
    """True when this figure a month is neither what they put by nor a sum towards a goal."""
    return _is_an_income(line, found) or _is_an_outgoing(line, found)

def _the_income_in_the_chat(memory):
    """The month's money the person says they are paid, or 0.

    Kept apart from the rate because the two answer different questions: the pay is what the
    length question has to ask about ("how much of that can you put by"), and the rate is what it
    can already do the sum with.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    for turn in reversed(turns[-6:]):
        line = str(turn.get("user") or "")
        for found in A_RATE.finditer(line):
            if not _is_an_income(line, found):
                continue
            value = _a_sum_named(found.group(1))
            if value:
                return value
    return 0


# A rate put right: "actually i can do 300 now ive paid the car off" is a new monthly rate and it
# does not say "a month" again, because the month was said once and never changed. Told from the
# wording that corrects something already said, and only ever read where a rate of this chat's own
# is already behind it, so a bare "i can do 300" in a chat about bicycles is still nothing.
A_RATE_PUT_RIGHT = re.compile(r"\b(?:actually|sorry|i meant|meant|make it|make that|no wait|"
                              r"rather than|instead|not)\b", re.I)

# What makes the figure in a correction a rate and not a bill: the person saying they can carry
# it. "actually 300 on food last month was mad" is a bill that has been paid and it is missing
# this word, so it moves nothing.
A_CAN_CARRY_IT = re.compile(r"\b(?:can|could|able|afford|manage|put|save|saving|spare|stretch)\b",
                            re.I)

# The same rate said with the month on it again: "actually make it 200 a month".
A_SUM_A_MONTH = re.compile(r"(?:£\s*)?(\d[\d,]*)\s*(?:pounds?\s+)?(?:a|per|each)\s+month\b",
                           re.I)

# The figure that revision names: one sum, and nothing else that a figure could be about. A goal
# ("actually i need 6000"), a spend ("actually 300 a month on food") or a length ("actually 3
# years") is not the rate coming back.
_OTHER_FIGURE_WORDS = re.compile(
    r"\b(?:need|needs|needed|owe|owes|owed|debt|debts|cost|costs|spend|spent|spending|"
    r"bill|bills|rent|goal|target|total|altogether|towards|toward|"
    r"week|weeks|day|days|year|years)\b",
    re.I)

A_LONE_SUM = re.compile(r"(?<![\d.,£$\u20ac])(\d[\d,]*)(?![\d.,])")

# The figure on its own, after a word that puts something right: "actually its 150", "make that
# 150", "no wait 150", "sorry, 150". The month was said once on the rate before it and never
# changed, so a correction that names no doing and no period is the same rate with a new figure -
# the reading `bot/memory/rates.py` already does for "actually 5 times" after "3 times a week",
# and the one this file was missing: every sum worked out after it used the rate they had left
# behind, and the figure they corrected to was filed as the balance instead.
A_CORRECTION_AND_A_FIGURE = re.compile(
    r"^\W*(?:(?:actually|sorry|no|nope|wait|oh|well|ok|okay|right|hang\s+on)\b\W*){0,3}"
    r"(?:(?:it|its|it's|that|thats|that's|make\s+it|make\s+that|i\s+meant|meant)\b\W*){0,2}"
    r"(?:£\s*)?\d", re.I)

# ...and nothing on the line that says the figure is something other than the rate: a balance, a
# spend, a debt, or a period of its own ("actually its 150 a week" is a different rate, not this
# one with a new figure).
_NOT_THE_RATE = re.compile(
    r"\b(?:on|spent|spending|cost|costs|bill|bills|balance|owe|owes|owed|debt|debts|rent|"
    r"price|paid|pay|total|goal|target|week|weeks|day|days|year|years|times?|hours?)\b",
    re.I)

# The plainest way of putting a rate right is to say no first: "no, 250 a month". The correction
# words above cover the ways of saying it that carry their own verb ("actually", "i meant", "make
# it"), and a person who answers the figure with "no" uses none of them - so the rate they had
# just taken back stayed the rate every sum afterwards was worked out at:
#
#     i can put away 150 a month / no, 250 a month / how long now
#       -> "At 150 a month, 900 takes 6 months."
#
# The sum has to come straight after the "no", with only the month on it, so an answer that
# starts with no and then argues about something else moves nothing: "no, 250 a month on food is
# plenty" is a bill being judged, not the rate the person can carry.
A_NO_THEN_A_RATE = re.compile(r"^\s*(?:no|nope|nah)\b[\s,.!\u2014-]*"
                              r"(?:i\s+(?:can|could)\s+(?:do|manage|put|save|spare)\s+)?"
                              r"(?:£\s*)?(\d[\d,]*)\s*(?:pounds?\s+)?(?:a|per|each)\s+month\b",
                              re.I)

# ...and nothing after it that says the sum is being spent rather than carried: "for the bike" is
# what the rate is for, "on food" is the bill.
A_SPENT_ON = re.compile(r"\b(?:on|spent|spending|costs?|bills?)\b", re.I)


# The plainest correction of all has no verb on it: "actually its more like 300 now". Every way of
# putting a rate right that this file knew carried one ("i can do 300", "make it 300 a month"), so
# a figure corrected like this matched nothing, and every sum afterwards - the length, a week of
# it, the date it lands - used the rate the person had already left behind.
A_MORE_LIKE = re.compile(
    r"\b(?:more\s+like|closer\s+to|call\s+it)\s*(?:£\s*)?\d"
    r"|\b(?:it'?s|its|that'?s)\s+(?:(?:more\s+like|about|only)\s+)?(?:£\s*)?\d[\d,]*\s+now\b",
    re.I)


def _is_a_rate_line(line):
    """True when the line puts money by at a rate, whatever else it says."""
    for found in A_RATE.finditer(str(line or "")):
        if not _is_not_a_rate(str(line or ""), found):
            return True
    return False


def a_rate_put_right(line, before=""):
    """The monthly rate a line puts right, or 0.

    "i can put by 250 a month" / "actually i can do 300 now ive paid the car off" is one rate
    written twice, and the second one is the rate: the car is paid off, so the 250 is old news.
    The sum in the second line often has no "a month" after it, because the month was never in
    question, so `A_RATE` cannot see it - and every sum the chat works out afterwards (the
    length, the figure a week, the date it lands) was worked out at the rate the person had
    already left behind.
    """
    line = str(line or "")
    if (before and A_MORE_LIKE.search(line) and A_RATE_PUT_RIGHT.search(line)
            and _is_a_rate_line(before) and not _OTHER_FIGURE_WORDS.search(line)):
        figures = A_LONE_SUM.findall(line)
        if len(figures) == 1:
            return _a_sum_named(figures[0])
    after_a_no = A_NO_THEN_A_RATE.search(line)
    if after_a_no and not A_SPENT_ON.search(line[after_a_no.end():]):
        return _a_sum_named(after_a_no.group(1))
    if not A_RATE_PUT_RIGHT.search(line) or _OTHER_FIGURE_WORDS.search(line):
        return 0
    with_the_month = A_SUM_A_MONTH.search(line)
    if with_the_month:
        return _a_sum_named(with_the_month.group(1))
    figures = A_LONE_SUM.findall(line)
    if len(figures) != 1:
        return 0
    if not A_CAN_CARRY_IT.search(line):
        # No "i can do" in it: only a correction that names the figure and nothing else is still
        # this chat's rate ("actually its 150"), and one that names a balance, a spend or a
        # period of its own is not.
        if not A_CORRECTION_AND_A_FIGURE.match(line.strip()) or _NOT_THE_RATE.search(line):
            return 0
    return _a_sum_named(figures[0])


def _a_sum_named(figure):
    """One sum as a number, or 0 when it is not a rate anybody could put by."""
    try:
        value = int(str(figure).replace(",", ""))
    except (TypeError, ValueError):
        return 0
    return value if value >= 10 else 0


def _the_rate_in_the_chat(memory):
    """The sum a month the person has settled on, reading the last few lines in order, or 0.

    Read forwards, so the newest word on it wins: a rate put right after a rate is the rate, and
    everything the chat works out from here - the length, the figure a week, the date it lands -
    is worked out on what the person can put by now.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-6:]
    settled = 0
    before = ""
    for turn in turns:
        line = str(turn.get("user") or "")
        for found in A_RATE.finditer(line):
            # Every figure on the line, not just the first: "i earn 1600 a month and
            # i put by 200 a month" is a pay and a rate, and a rent is neither -
            # only what they put by is what the goal is measured against.
            if _is_not_a_rate(line, found):
                continue
            value = _a_sum_named(found.group(1))
            if value:
                settled = value
            continue
        if settled:
            put_right = a_rate_put_right(line, before)
            if put_right:
                settled = put_right
        before = line
    return settled


# "how much a month?" is the last of the three questions - the sum, the date, the rate - and it
# carries neither of the first two, so on its own it reads as nothing in particular and the diet
# entry takes the turn ("i want to save 2000 pounds" / "by june" / "how much a month").
HOW_MUCH = re.compile(r"\bhow\s+(?:much|many)\b[^?.!]{0,24}?\b(?:a|per|each)\s+(?:month|week)\b|"
                      r"\bhow\s+much\s+(?:should|do|would)\s+i\s+(?:put|save|need)\b", re.I)


def _the_date_in_the_chat(memory):
    """The month the goal was put in, from the last few lines, or ""."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    for turn in reversed(turns[-6:]):
        line = str(turn.get("user") or "")
        when = _only_a_date(line) or _a_date(line)
        if when:
            return when
    return ""


def _months_left(when):
    """The months from this one to the month the person named: "by december" said in November is
    one month off, whichever December that is."""
    import datetime

    today = datetime.date.today()
    word = str(when or "").lower()
    if "this month" in word or "this week" in word:
        return 0  # the month in hand has not gone anywhere
    if "next month" in word:
        return 1  # and next month is one month off, not the 12 a named month can be
    month = _month_of(when)
    if not month:
        return 0
    number = MONTHS.index(month) + 1
    year = today.year + (1 if number <= today.month else 0)
    return max((year - today.year) * 12 + (number - today.month), 0)


def _months(n):
    """The length as months, with the years in it once it is over a year.

    "£3,000 at £250 a month is 12 months" makes the person do the counting again; the money entry
    already says "32 months, about 2 years and 8 months", and a length is only useful if it is
    the length they can feel.
    """
    said = "%s month%s" % (format(n, ","), "" if n == 1 else "s")
    if n < 12:
        return said
    years, months = divmod(n, 12)
    parts = []
    if years:
        parts.append("%s year%s" % (format(years, ","), "" if years == 1 else "s"))
    if months:
        parts.append("%s month%s" % (months, "" if months == 1 else "s"))
    return said + ", about " + " and ".join(parts)


def a_date_on_a_settled_rate(text, memory):
    """The answer to a bare date asked after the rate was already chosen, or "".

    Once someone has said what they can put by ("if we put by 150 a month"), a date on its own is
    not a request for a new weekly figure - the money entry would answer it with "£3,000 by
    December is about £700 a week", which argues with the rate they just gave. It asks whether
    that rate gets there by then, and the honest answer puts the two figures side by side: how
    long the rate takes, how far off the date is, and what it would take instead.
    """
    when = _only_a_date(text)
    if not when or not _a_rate_is_settled(memory):
        return ""
    rate, goal = _the_rate_in_the_chat(memory), _the_money_still_to_find(memory)
    return _a_date_on_a_rate(goal, rate, when)


def _a_date_on_a_rate(goal, rate, when):
    """The rate against the month it has to reach: whether it gets there, and what would."""
    left = _months_left(when)
    if not rate or not goal or goal <= rate or left < 1:
        return ""
    months = -(-goal // rate)  # a part month is another payment
    # "the end of next month" is not a name, so it stays lower-case in the middle of the
    # sentence; a month the person named keeps its capital ("December is one month away").
    name = when if when.startswith("the end of ") else when.capitalize()
    goal_text = "£%s" % format(goal, ",")
    rate_text = "£%s a month" % format(rate, ",")
    if months <= left:
        return ("%s at %s takes %s and %s is %s away, so that rate gets you there. Set the standing "
                "order for the day after payday and it looks after itself — a bonus or a refund "
                "just brings the date forward."
                % (goal_text, rate_text, _months(months), name, _months(left)))
    need = -(-goal // left)
    need = int(-(-need // 10) * 10)  # round the figure up to a round sum: £572 reads as £580
    part = min(rate * left, goal)
    return ("%s at %s takes %s and %s is %s away, so it does not get you there — that would take "
            "about £%s a month. At %s you have £%s of it by then; a bonus, a bill that drops or a "
            "later date closes the gap."
            % (goal_text, rate_text, _months(months), name, _months(left), format(need, ","),
               rate_text, format(part, ",")))


# The weekly figure an answer gave a turn or two ago: "£67 a week over the 30 weeks left".
A_WEEK_FIGURE = re.compile(r"£\s*(\d[\d,]*)\s*a\s+week", re.I)


# A yes/no about the plan already in hand: "is that enough", "will 200 a month be enough",
# "does that get me there", "is it enough". The figure in it, when there is one, is the rate the
# chat already holds - the person is not giving a new number, they are asking whether the one on
# the screen does the job.
ASKS_IF_ENOUGH = re.compile(
    r"^\s*(?:(?:and|but|so|ok|okay|right|well)\b[\s,]*)*"
    r"(?:is|will|would|does|do|am\s+i|are\s+we)\s+"
    r"(?:that|this|it|they|we|i|£?\s*\d[\d,]*\s*(?:a|per|each)\s+month|"
    r"(?:putting\s+by|saving|saved)\s+£?\s*\d[\d,]*\s*(?:a|per|each)\s+month)\s+"
    r"(?:be\s+)?(?:enough|do(?:\s+it)?|get\s+(?:me|us)\s+there|get\s+there|cover(?:\s+it)?"
    r"|be\s+enough)"
    # "is that enough salt", "is that enough for a deposit" are about something else in the chat:
    # the yes/no this reads ends on the asking, so nothing may be named after it.
    r"(?:\s+(?:then|though|really|now|do\s+you\s+think|i\s+wonder))?\s*[.!?]*\s*$", re.I)


def asks_if_the_rate_is_enough(text):
    """True when the line asks whether the rate already in the chat does the job."""
    return bool(ASKS_IF_ENOUGH.match(str(text or "")))


def a_yes_no_about_the_rate(text, memory):
    """The verdict on the rate the chat holds, in its short form, or "".

    "i want to save 3000 pounds by christmas" / "i can put by 200 a month" / "is that enough"
    ended in "Sounds good." - the opposite of what the answer a turn earlier had just worked out
    (that the rate does not get there). The sum is already in `_a_date_on_a_rate`; what this line
    wants is the verdict first and the figures behind it, not the same long sentence twice, so
    the date is answered in one line and the figures are only the ones the verdict turns on.
    """
    if not asks_if_the_rate_is_enough(text) or not isinstance(memory, dict):
        return ""
    goal, rate = _the_money_still_to_find(memory), _the_rate_in_the_chat(memory)
    if not goal or not rate:
        return ""
    months = -(-goal // rate)  # a part month is another payment
    when = _the_date_in_the_chat(memory)
    left = _months_left(when) if when else 0
    goal_text = "£%s" % format(goal, ",")
    rate_only = "£%s a month" % format(rate, ",")
    rate_text = "at %s" % rate_only
    if not when or not left:
        # No date to miss: the answer is how long the rate takes, said once, and the date is
        # what the person has to give for a yes or a no.
        return ("%s %s takes %s. Name the month you want it by and I will tell you whether that "
                "is soon enough." % (goal_text, rate_text, _months(months)))
    if months <= left:
        spare = left - months
        room = ("%s month%s to spare" % (spare, "" if spare == 1 else "s")
                if spare else "nothing to spare")
        return ("Yes — %s gets you to %s by %s, %s. Leave the standing order where it is."
                % (rate_only, goal_text, str(when).capitalize(), room))
    part = min(rate * left, goal)
    return ("No — %s you have £%s of %s by %s. The whole %s takes %s at that rate, so the rest "
            "wants more a month or a later date."
            % (rate_text, format(part, ","), goal_text, str(when).capitalize(), goal_text,
               _months(months)))


# The question the verdict above invites: "and how much more a month would do it". The figure it
# asks for is the rate that would reach the goal by the date, less the rate already there.
ASKS_HOW_MUCH_MORE = re.compile(
    r"^\s*(?:(?:and|but|so|ok|okay|right|well)\b[\s,]*)*"
    r"(?:how\s+much\s+(?:more|extra)\s+(?:a|per|each)\s+month"
    r"|how\s+much\s+(?:more|extra)\s+(?:would|do|will)\s+(?:i|we)\s+(?:need|have\s+to))"
    r"\b", re.I)


def asks_how_much_more_a_month(text):
    """True when the line asks what extra a month the goal and the date need."""
    return bool(ASKS_HOW_MUCH_MORE.match(str(text or "")))


def the_extra_a_month_asked(text, memory):
    """The extra a month the date needs, or "" - the question the verdict above invites.

    "so the rest wants more a month or a later date" is an invitation, and "and how much more a
    month would do it" is the natural next line. Unread, it went to the goal's own entry and
    printed the first answer again, word for word, three turns later.
    """
    if not asks_how_much_more_a_month(text) or not isinstance(memory, dict):
        return ""
    goal, rate = _the_money_still_to_find(memory), _the_rate_in_the_chat(memory)
    when = _the_date_in_the_chat(memory)
    if not goal or not rate or not when:
        return ""
    left = _months_left(when)
    if not left:
        return ""
    months = -(-goal // rate)
    if months <= left:
        spare = left - months
        return ("Nothing more — %s already gets you to £%s by %s with %s month%s to spare."
                % ("£%s a month" % format(rate, ","), format(goal, ","), str(when).capitalize(),
                   spare, "" if spare == 1 else "s"))
    need = -(-goal // left)
    need = int(-(-need // 10) * 10)  # a figure to aim at, not a figure to the pound
    more = max(need - rate, 0)
    left_text = "the month that is left" if left == 1 else "the %s left" % _months(left)
    return ("About £%s a month more: £%s a month for %s, rather than the £%s you have. Or give it "
            "longer — at £%s a month the whole £%s takes %s."
            % (format(more, ","), format(need, ","), left_text, format(rate, ","),
               format(rate, ","), format(goal, ","), _months(months)))


def the_same_figure_a_month(text, memory):
    """The rate asked for in months, said in months, when the chat already gave it in weeks, or "".

    "how much a month?" after "£2,000 by June is about £67 a week" asks for the same figure in
    another unit, and working it out again from the goal gives the same sentence a second time.
    Said in months from the figure already on the screen, the line gets an answer of its own.
    """
    if not HOW_MUCH.search(str(text or "")):
        return ""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    for turn in reversed(turns[-4:]):
        found = A_WEEK_FIGURE.search(str(turn.get("bot") or ""))
        if not found:
            continue
        try:
            a_week = int(found.group(1).replace(",", ""))
        except ValueError:
            return ""
        if a_week < 5:
            return ""
        a_month = int(round(a_week * 52 / 12.0 / 10.0)) * 10
        return ("£%s a week is about £%s a month. Set the standing order for the day after payday "
                "and it runs itself — a bonus or a refund only shortens the time."
                % (format(a_week, ","), format(a_month, ",")))
    return ""


# A rate said on its own with no verb on it: "at 300 a month", "300 a month then", "what about
# 250 a month". It is not a rate the person is joining in with (`A_RATE`) and it adds nothing to
# the one already there (`A_RESTATED_RATE`), it replaces it.
A_NEW_RATE = re.compile(r"^\s*(?:(?:and|but|so|then|ok|okay|right)\b[\s,]*)*"
                        r"(?:(?:what|how)\s+about\s+|at\s+|make\s+it\s+)?(?:£\s*)?"
                        r"(\d[\d,]*(?:\.\d+)?)\s*(k)?\s*(?:pounds?\s+)?(?:a|per|each)\s+month"
                        r"\s*(?:then|now)?\s*[.!]*\s*$", re.I)


def a_rate_restated(text, memory):
    """The goal worked out at the rate the line puts in place of the old one, or "".

    "i need to save 3000" / "how long at 200 a month" / "and at 300 a month" is the same question
    with one figure changed, and the rate on its own names neither the goal nor the money word: it
    reached the knowledge entry as a line about nothing and came back as the 200 answer again, the
    closing sentence and all.
    """
    line = str(text or "")
    said = A_NEW_RATE.match(line)
    if not said:
        return ""
    if PAST_SAVING.search(line) or OTHER_POT.search(line):
        return ""
    if _only_a_date(line) or _a_date(line):
        return ""
    try:
        rate = float(said.group(1).replace(",", ""))
    except ValueError:
        return ""
    if said.group(2):
        rate *= 1000
    rate = int(round(rate))
    if rate < 20:
        return ""  # "at 5 a month" is a habit, not a rate towards a goal
    aim = _the_goal_in_the_chat(memory)
    if not aim or rate >= aim:
        return ""
    if rate == _the_rate_in_the_chat(memory):
        # The rate already on the screen is answered where a rate is said back, not worked out
        # again: the person is agreeing with the figure, not asking for it a second time.
        return ""
    return without_what_was_just_said(_a_rate_against_the_goal(aim, rate, memory), memory)


# A rate put in place with a verb but no unit: "what if i put away 300" after the chat has said
# "i've got 200 a month to put away". The unit is in the chat, so the figure is a rate and not a
# new goal - read as a sum it worked the goal 300 out from scratch ("For £300: £100 a month is 3
# months") and answered a question nobody asked.
A_RATE_WITH_A_VERB = re.compile(
    r"^\s*(?:(?:and|but|so|then|ok|okay|right)\b[\s,]*)*"
    r"(?:(?:what|how)\s+about\s+|what\s+if\s+(?:i\s+)?|(?:and\s+)?if\s+i\s+)?"
    r"(?:only\s+)?(?:put|putting|set|setting|pay|paying)\s+(?:(?:away|by|aside|in|up)\s*)?"
    r"(?:£\s*)?(\d[\d,]*(?:\.\d+)?)\s*(k)?\s*(?:pounds?|quid)?\s*"
    r"(?:(?:instead|then|now)\b\s*)?[.!?]*\s*$", re.I)


def a_rate_put_in_with_a_verb(text, memory):
    """The goal at a new rate when the figure comes in without its unit, or "".

    "i've got 200 a month to put away" / "how long until i can afford 5000" / "what if i put away
    300" is one goal and three rates. The third line names no unit, so on its own it is a sum,
    and the money entry read it as the goal - a goal of 300, worked out at rates nobody asked
    about. A rate already in the chat is what makes the bare figure a rate.
    """
    line = str(text or "")
    if not line.strip() or A_RATE.search(line) or A_NEW_RATE.match(line):
        return ""
    if _only_a_date(line) or _a_date(line):
        return ""
    said = A_RATE_WITH_A_VERB.match(line)
    if not said:
        return ""
    if PAST_SAVING.search(line) or OTHER_POT.search(line):
        return ""
    if not _a_rate_is_settled(memory):
        return ""   # with no rate in the chat, a bare sum is a goal and the goal reader has it
    try:
        rate = float(said.group(1).replace(",", ""))
    except ValueError:
        return ""
    if said.group(2):
        rate *= 1000
    rate = int(round(rate))
    if rate < 20:
        return ""
    aim = _the_goal_in_the_chat(memory) or _the_goal_in_the_answer(memory)
    if not aim or rate >= aim:
        return ""
    if rate == _the_rate_in_the_chat(memory):
        return ""
    return without_what_was_just_said(_a_rate_against_the_goal(aim, rate, memory), memory)


# A length asked with the sum in it: "how long until i can afford 5000", "when will i have
# 5,000?", "how many months to save 3000". The figure is the goal, and the rate is the one the
# person already gave - but the line names no rate, so the money entry read it as a goal with
# every rate to choose from and answered with the benchmark list: "For £5,000: £100 a month is 50
# months, £250 a month is 20 months, £500 a month is 10 months", when the chat had said 200 a
# month two lines earlier.
ASKS_A_LENGTH = re.compile(
    r"\bhow\s+long\b|\bhow\s+many\s+(?:months|years|weeks)\b|"
    r"\bwhen\s+(?:will|would|can|do|should)\s+(?:i|we)\b", re.I)


def a_length_at_the_rate_in_the_chat(text, memory):
    """The money question about the goal in the line at the rate already in the chat, or "".

    Written as the question the money entry answers in full ("how long will it take to save 5000
    at 200 a month"), because the sum is the entry's - this reads only that the rate is the
    chat's own and the line did not name another one.
    """
    line = str(text or "")
    if not line.strip() or not ASKS_A_LENGTH.search(line):
        return ""
    if A_RATE.search(line) or A_NEW_RATE.match(line) or A_RATE_WITH_A_VERB.match(line):
        return ""   # a rate in the line is the money entry's own question, read whole
    if _the_date_in_the_chat(memory):
        return ""   # a date in play is answered by the arithmetic on the date
    said = _a_sum(line)
    if not said:
        return ""
    rate = _the_rate_in_the_chat(memory)
    if not rate or rate >= said:
        return ""
    return ("How long will it take to save %s at %s a month?"
            % (format(said, ","), format(rate, ",")))


def a_rate_with_no_date(text, memory):
    """The rate asked for when the goal is in the chat but no date is, or "".

    "how much a month?" with no month named is a question no entry can work out: the rate is the
    sum over however many months they have in mind. Asking for that is the one honest answer, and
    it is better than the figure for the goal alone, which the chat has already had.
    """
    line = str(text or "")
    if not HOW_MUCH.search(line) or _a_sum(line) or _only_a_date(line) or _a_date(line):
        return ""
    aim = _the_goal_in_the_chat(memory)
    if not aim or _the_date_in_the_chat(memory):
        return ""
    return ("£%s is a different rate over six months than over a year, so name the month you want "
            "it by and I will work out what to put by each month — and whether a standing order "
            "gets you there." % format(aim, ","))


def asks_the_rate(text, memory):
    """True when the line asks for the rate and names neither the goal nor the date.

    The money reading of a line has to go before the general one for this shape: "how much a
    month?" is about the goal said two turns ago, and read on its own it is about nothing.
    """
    line = str(text or "")
    if not HOW_MUCH.search(line) or _a_sum(line):
        return False
    if _only_a_date(line) or _a_date(line):
        return False
    return bool(_the_goal_in_the_chat(memory))


# The named days the money entry works out on its own (bot/knowledge/money.py, `_month_in`). Any
# other name this module reads - easter, halloween, "the end of the year" - is handed to it as the
# month it falls in, so the same deadline can be counted by both.
_KNOWN_TO_THE_MONEY_ENTRY = ("christmas", "xmas")


def _in_the_money_readers_words(when):
    """The date as the knowledge base can count it: a named day becomes the month it falls in.

    "The end of" is carried through, because it is the whole of the difference between a goal
    said "by december" and one said "by the end of december", and dropping it asked the money
    entry for a fortnight's saving when there were seven weeks: "i need to save 3000 by the end
    of the year" was answered "£3,000 by december is 20 days away" from the first of the month.
    A season's end is the last day of its last month, which is a date, so "the end of autumn" is
    the end of November rather than the September an autumn starts in.
    """
    word = str(when or "").lower().strip()
    if not word or word in MONTHS or word in _KNOWN_TO_THE_MONEY_ENTRY:
        return word
    if word.startswith("the end of "):
        rest = word[len("the end of "):].strip()
        if rest in ("next year", "this year", "the year"):
            return word  # the money entry reads the last day of that year itself
        season = rest[4:] if rest.startswith("the ") else rest
        month = _THE_END_OF_A_SEASON.get(season) or _in_the_money_readers_words(rest)
        return "the end of " + month if month else word
    for name, month in NAMED_WHEN:
        if name in word:
            return month
    return word


# The last month of each season, for the end of one: the seasons people name are spans, and
# "the end of autumn" is a date at the end of November rather than the September it starts in.
_THE_END_OF_A_SEASON = {"spring": "may", "summer": "august", "autumn": "november",
                        "fall": "november", "winter": "february"}


def rate_question(text, memory):
    """The money question this line really is, or "" when it is not one.

    A goal with a sum is the question, and a date on its own is the same question about the sum
    said a line or two ago - which is the follow-up people actually make: "i want to save 2000
    pounds" / "by june".
    """
    line = str(text or "")
    if not line.strip():
        return ""
    if HOW_MUCH.search(line) and not _a_sum(line):
        # The rate is the question they are asking, and the goal and the date are already said:
        # answer with both of them rather than asking a fourth time.
        aim, when = _the_goal_in_the_chat(memory), _the_date_in_the_chat(memory)
        if not aim:
            return ""
        if when:
            return ("How much do i need to put by a week to have %s pounds by %s?"
                    % (format(aim, ","), _in_the_money_readers_words(when)))
        return "How much do i need to put by a week to have %s pounds?" % format(aim, ",")
    if _names_a_goal(line):
        aim, when = _names_a_goal(line), _a_date(line)
    else:
        when = _only_a_date(line)
        if not when or _a_rate_is_settled(memory):
            return ""
        aim = _the_goal_in_the_chat(memory)
    if not aim:
        return ""
    held = the_pot_and_the_rest(line)[0] or _the_money_already_held(memory)
    if held and 0 < held < aim:
        # The pot is part filled: the question is about the money still to find.
        aim = aim - held
    if when:
        return ("How much do i need to put by a week to have %s pounds by %s?"
                % (format(aim, ","), _in_the_money_readers_words(when)))
    return ("How much do i need to put by a week to have %s pounds?" % format(aim, ","))


# The rate as a statement rather than a question: "im putting by 500 a month" right after a goal
# names the third part of the same question (the goal, the date, the rate) and asks for nothing,
# so no entry answers it. What came back was a clause of the answer above - the three rates with
# no idea which one the person had just chosen - which reads as the bot not listening.
# A rate that puts the money somewhere else: "i put by 500 a month into my pension" is not the
# goal the person named, so the goal's arithmetic would be about a different account.
OTHER_POT = re.compile(r"\s*(?:into|in|towards|toward|for)\s+(?:a|an|my|our|the|his|her|their)\s+"
                       r"[a-z]", re.I)
RATE_GIVEN = re.compile(r"\b(?:putting by|putting away|put by|put away|setting aside|set aside|"
                        r"saving|saved|save|stashing|stash)\b", re.I)
RATE_VERB = re.compile(r"\b(?:putting|put|setting|set|stashing|stash|socking|sock|saving|save)\b",
                       re.I)
# What can be left of "and if i put away 300" once the lead-in and the rate verb are taken off: the
# figure, with the unit if they gave one and a word about where it goes. Anything else means the
# line is about something more specific than a rate.
FILLER_LEAD = re.compile(r"^\s*(?:(?:and|but|so|then|also|ok|okay|well|if|maybe|what\s+if|how\s+about|"
                         r"i|we|i'd|we'd|could|can|would|will|shall|should|might|to|just|try|"
                         r"trying)\b[\s,]+)*", re.I)
BARE_RATE = re.compile(r"(?:£\s*)?(\d[\d,]*)\s*(?:pounds?|quid|aside|away|by|back)?", re.I)


# A rate said with the verb right before the figure and no period on it: "and if i put away 300".
# "save 300" is not one of these - saving is what happens to the pot, putting by is what happens
# every month - so it is read as a goal unless the line is conditional ("and if i save 300").
SAVE_VERB = re.compile(r"^\s*sav(?:e|es|ing)\b", re.I)
CONDITIONAL = re.compile(r"\b(?:if|what\s+if|could|can|would|might)\b", re.I)


def _a_rate_said(line):
    """The sum a month the person says they will put by, and whether they named the period.

    "im putting by 500 a month" names it; "and if i put away 300" right after the goal does not,
    and in a chat about a saving goal the period is a month - nobody puts by 300 a year. Read as a
    goal the line names a different pot ("For £300: £100 a month is 3 months") and works out a
    number about the wrong figure, which is worse than saying nothing.
    """
    found = A_RATE.search(line or "")
    if found:
        try:
            return int(found.group(1).replace(",", "")), True
        except ValueError:
            return 0, False
    if INTENT.search(line or "") or re.search(r"£|\bpounds?\b|\bquid\b", line or "", re.I):
        # "i want to save 1000" and "save 1000 pounds" name a new goal, not a month: the aim is
        # there, or the figure carries its unit.
        return 0, False
    rest = FILLER_LEAD.sub("", str(line or "")).strip(" ,.")
    verb = RATE_GIVEN.match(rest) or RATE_VERB.match(rest)
    if not verb:
        return 0, False
    if SAVE_VERB.match(rest) and not CONDITIONAL.search(line or ""):
        # "save 1000" after "i want to save 2000 pounds" is a smaller pot, not a thousand a
        # month: with no period and nothing conditional about it, the figure is the goal.
        return 0, False
    rest = rest[verb.end():].strip(" ,.")
    match = BARE_RATE.fullmatch(rest)
    if not match:
        return 0, False
    try:
        return int(match.group(1).replace(",", "")), False
    except ValueError:
        return 0, False


def a_rate_for_the_goal(text, memory):
    """The arithmetic for a rate the person states, when the goal is already in the chat, or "".

    "i want to save 2000 pounds" / "im putting by 500 a month" is one question: at that rate the
    goal takes four months. The line names no date, so it is not asked - but the answer is
    arithmetic the person cannot do in their head, and it is the one thing they wanted.
    """
    line = str(text or "")
    if not isinstance(memory, dict) or not line.strip():
        return ""
    if not RATE_GIVEN.search(line) and not RATE_VERB.search(line):
        return ""
    if _only_a_sum(line) or _only_a_date(line):
        return ""
    # A rate and a length named together are the multiplication ("200 a month for a year"), which
    # the money entry answers, so this leaves it alone.
    if re.search(r"\bfor\s+(?:\d|a|an|two|three|four|five|six)", line, re.I):
        return ""
    rate, _period = _a_rate_said(line)
    if not rate:
        return ""
    found = A_RATE.search(line)
    if found:
        tail = line[found.end():]
        if NOT_A_POT.match(tail) or OTHER_POT.match(tail):
            # "we save 500 a month on the mortgage" is a saving on a bill, not 500 towards the pot:
            # the same line the goal's own sum is refused by. And a rate that names a pot of its own
            # ("into my pension") is putting money somewhere else, so the goal's arithmetic would be
            # about a different account.
            return ""
    goal = _the_money_still_to_find(memory)
    if goal <= rate:
        return ""
    when = _the_date_in_the_chat(memory)
    if when:
        # The date is already in the chat, so the question the rate answers is whether it gets
        # there by then - the same side-by-side the date-after-rate turn gets.
        against = _a_date_on_a_rate(goal, rate, when)
        if against:
            return against
    months = -(-goal // rate)  # a part month is another payment
    closing = _a_closer(memory)
    said = ("£%s at £%s a month is %s." % (format(goal, ","), format(rate, ","), _months(months)))
    return said + (" " + closing if closing else "")


# A sum the line adds to the rate rather than names as a new goal: "and if i cut the gym thats
# another 40", "plus 40 a month", "an extra 40 on top". The pot does not change; the rate does, and
# the arithmetic has to be done on the rate it now is. Read on its own the line is a goal of £40
# ("£40 at £400 a month is a single month at that rate"), which answers a question nobody asked.
ADDED = re.compile(r"\b(?:another|extra|plus|more|on\s+top)\b", re.I)
# A rate restated as the total it has become: "so 440 a month", "440 a month then". Nobody says
# this unless the last line changed the rate, so it is answered as the rate it names.
A_RESTATED_RATE = re.compile(r"^\s*(?:(?:and|but|so|then|ok|okay|right)\b[\s,]*)*"
                             r"(?:£\s*)?(\d[\d,]*)\s*(?:pounds?\s+)?(?:a|per|each)\s+month"
                             r"\s*(?:then|now)?\s*[.!]*\s*$", re.I)


def _the_added_sum(line):
    """The sum the line adds to the rate, or 0 when it names none."""
    found = re.search(r"(?:£\s*)?(\d[\d,]*(?:\.\d+)?)\s*(k|grand|thousand)?", line or "")
    if not found:
        return 0
    try:
        value = float(found.group(1).replace(",", ""))
    except ValueError:
        return 0
    if (found.group(2) or "").lower() in ("k", "grand", "thousand"):
        value *= 1000
    value = int(value)
    if value < 5 or value > 5000:
        return 0
    return value


def a_rate_raised(text, memory):
    """The goal worked out again at the rate the line raises it to, or "".

    "i can put by 400 a month" / "and if i cut the gym thats another 40" is the same question at
    £440, and it is the arithmetic the person wants: the months, not the £40 on its own.
    """
    line = str(text or "")
    if not isinstance(memory, dict) or not line.strip():
        return ""
    goal = _the_money_still_to_find(memory) or _the_goal_in_the_answer(memory)
    rate = _the_rate_in_the_chat(memory)
    if not goal or not rate or goal <= rate:
        return ""
    restated = A_RESTATED_RATE.match(line)
    if restated:
        try:
            named = int(restated.group(1).replace(",", ""))
        except ValueError:
            return ""
        if named <= rate or named >= goal:
            return ""
        if _said_a_rate_at(named, memory):
            # The line is the rate the answer above already gave, said back - "£20,000 at £440 a
            # month is 46 months" / "so 440 a month" - so the figures are on the screen and the
            # turn is what to do about them. Saying the same sentence again is worse than nothing.
            return ("That is the rate: put the standing order in for £%s the day after payday and "
                    "the £%s takes care of itself from there."
                    % (format(named, ","), format(goal, ",")))
        return _a_rate_against_the_goal(goal, named, memory)
    if not ADDED.search(line):
        return ""
    if _names_a_goal(line):
        # "i want to save another 2000" names a new pot, not a raise.
        return ""
    added = _the_added_sum(line)
    if not added:
        return ""
    raised = rate + added
    if raised >= goal:
        # A sum that takes the rate past the pot is a new goal, not an addition.
        return ""
    return _a_rate_against_the_goal(goal, raised, memory)


def _said_a_rate_at(rate, memory):
    """True when the bot's last answer already worked the goal out at this rate."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict) and t.get("bot")]
    if not turns:
        return False
    last = str(turns[-1].get("bot") or "")
    return bool(re.search(r"£\s*%s\s*a\s+month" % format(rate, ",").replace(",", ",?"), last))


def _a_rate_against_the_goal(goal, rate, memory):
    """The months the goal takes at this rate, and a closing line the reply above did not use."""
    months = -(-goal // rate)  # a part month is another payment
    said = "£%s at £%s a month is %s." % (format(goal, ","), format(rate, ","), _months(months))
    closing = _a_closer(memory)
    return said + (" " + closing if closing else "")


# Closing lines about where the money goes. Two rates asked in a row ("how long at 200 a month" /
# "and at 300 a month") work out two different numbers and then end with the same sentence both
# times, which is the answer coming back with a fresh figure sewn onto it, so the closer is chosen
# from a pool and the one just used is skipped.
SAVING_CLOSERS = (
    "A standing order the day after payday does it without you deciding again, and any interest or "
    "pay rise only shortens it.",
    "Set it up as a standing order for the day after payday, so the month cannot quietly spend what "
    "the plan needs.",
    "The day after payday is the day to move it, before the rest of the month gets a look at it.",
)


def _a_closer(memory):
    """A closing line the reply just above did not already use, or ""."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict) and t.get("bot")]
    last = str(turns[-1].get("bot") or "").lower() if turns else ""
    said = set(re.findall(r"[a-z']+", last))
    for closing in SAVING_CLOSERS:
        words = [word for word in re.findall(r"[a-z']+", closing.lower()) if len(word) > 3]
        here = sum(1 for word in words if word in said)
        if words and here * 2 >= len(words):
            continue
        return closing
    return ""

# A sentence of an answer that the reply just above already said. Two rates asked in a row ("how
# long at 200 a month" / "and at 300 a month") work out two different numbers and end with the same
# closing sentence both times, so the turn reads as the answer coming back with a fresh figure sewn
# onto it. The figure is what changed, and the tail is the part that did not.
def _a_said_sentence(sentence, said):
    """True when most of the words of this sentence are in the reply above."""
    words = [word for word in re.findall(r"[a-z']+", sentence.lower()) if len(word) > 3]
    if len(words) < 4:
        return False
    here = sum(1 for word in words if word in said)
    return here * 4 >= len(words) * 3


def said_already(reply, memory):
    """True when the first sentence of `reply` is one the answer above already said.

    "we want to save 3000 pounds" / "by december" / "how much should i put by a month" asks the
    same question a second time, and the entry answers it with the same sentence - it is one pay
    packet either way. `without_what_was_just_said` can only take the tail off, because its first
    sentence is normally the part that is new, so the repeat itself has to be recognised here and
    answered in the unit the person asked for.
    """
    first = re.split(r"(?<=[.!?])\s+", str(reply or "").strip())[0]
    if not first:
        return False
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict) and t.get("bot")]
    if not turns:
        return False
    said = set(re.findall(r"[a-z']+", str(turns[-1].get("bot") or "").lower()))
    return bool(said) and _a_said_sentence(first, said)


# The ask that gets the weekly figure off the money entry when the date's own answer is a repeat:
# with no date in the line the entry divides the goal by the weeks left, which is the one number
# the pay-packet answer did not give.
A_WEEK_ASK = "how much should i put by each week"


def _weeks_left(when):
    """The weeks from this one to the month the person named, rounded up: a week left is a week."""
    import datetime

    month = _month_of(when)
    if not month:
        return 0
    today = datetime.date.today()
    number = MONTHS.index(month) + 1
    year = today.year + (1 if number <= today.month else 0)
    days = (datetime.date(year, number, 1) - today).days
    return max(-(-days // 7), 0)


# The monthly figure an answer gives: "£3,000 by june is 206 days away, so about £296 a month".
A_MONTH_FIGURE = re.compile(r"£\s*(\d[\d,]*)\s*a\s+month", re.I)


def a_figure_each_week(memory):
    """The goal divided by the weeks left, said as one figure, or "".

    The last resort for "how much a month" when the answer above already said the goal in months:
    the same requirement said in the unit that comes out of a pay packet is a figure they did not
    have yet, where the sentence they just read again is nothing at all.
    """
    aim, when = _the_money_still_to_find(memory), _the_date_in_the_chat(memory)
    weeks = _weeks_left(when)
    if not aim or weeks < 2:
        return ""
    a_week = -(-aim // weeks)
    # The month figure the answer above gave stands as the lead, so the person hears the number
    # they asked for and the one that comes out of a pay packet in the same breath: "£296 a month
    # is about £67 a week over the 30 weeks left".
    # Only the reply just above counts: three turns back the answer was a list of rates, and the
    # first "£100 a month" in it is not what the goal comes to. The lead has to be the figure this
    # goal and this date were just given in.
    said = None
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict) and t.get("bot")]
    found = A_MONTH_FIGURE.search(str(turns[-1].get("bot") or "")) if turns else None
    if found:
        said = "£%s a month is" % found.group(1)
    if not said:
        said = "£%s by %s is" % (format(aim, ","), str(when).capitalize())
    said += " about £%s a week over the %s weeks left" % (format(a_week, ","), format(weeks, ","))
    closing = _a_closer(memory)
    if closing:
        # The closer is a sentence of its own everywhere else; after a dash it is the rest of this
        # one, so it starts lower case: "£3,000 by April is about £143 a week over the 21 weeks
        # left — a standing order ...".
        return said + " — " + closing[0].lower() + closing[1:]
    return said + "."


def the_figure_a_week(memory):
    """The question that gets the figure each week, or "" when there is nothing to divide."""
    if not _the_goal_in_the_chat(memory) or not _the_date_in_the_chat(memory):
        return ""
    return A_WEEK_ASK


def without_what_was_just_said(reply, memory):
    """`reply` with any sentence of it the reply above already said taken off.

    Only whole sentences go, and never the first: the answer itself is new - the rate is another
    rate - so what is left is the figure with the same closing on it, and the closing is dropped.
    A reply that is one sentence, or that says something wholly new, comes back untouched.
    """
    reply = str(reply or "")
    if not reply or not isinstance(memory, dict):
        return reply
    if "\n" in reply:
        # A poem, a list or a set of steps is laid out line by line, and the lines are the answer:
        # gluing what is left of them together is worse than saying a sentence twice.
        return reply
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict) and t.get("bot")]
    if not turns:
        return reply
    said = set(re.findall(r"[a-z']+", str(turns[-1].get("bot") or "").lower()))
    if not said:
        return reply
    parts = [part for part in re.split(r"(?<=[.!?])\s+", reply.strip()) if part.strip()]
    if len(parts) < 2:
        return reply
    kept = [parts[0]] + [part for part in parts[1:] if not _a_said_sentence(part, said)]
    return " ".join(kept)


# A length asked for something whose price the chat does not have: "i save 50 a month" / "so how
# many weeks until i can buy it". The rate is known and the price is not, so no sum can be worked
# out; the line names no figure at all, so no entry reaches it either, and the person got the
# search hedge on a question about their own saving. What the chat does hold is the rate, so it is
# said as the money it becomes - the part the bot knows - and the one missing figure is asked for.
ASKS_A_LENGTH_FOR_A_THING = re.compile(
    r"\bhow\s+(?:many|long)\b[^?.!,]{0,32}?\b(?:weeks?|months?|years?|days?)\b"
    r"|\bhow\s+long\b[^?.!,]{0,32}?\b(?:until|till|before|to\s+buy|to\s+afford|to\s+get)\b"
    r"|\bwhen\s+(?:can|will)\s+i\s+(?:afford|buy|get)\b", re.I)
# The ask is about buying something: "how many weeks until i can buy it" is this question, and
# "how many weeks until my holiday" is not - the second one is a wait to be counted, not money.
THE_THING_WANTED = re.compile(
    r"\b(?:afford|buy|pay\s+for|save\s+up\s+for|have\s+enough\s+for)\b"
    r"|\bget\s+(?:it|one|ones|them|that|this|another)\b", re.I)
# The thing itself, when it was named: "buy a bike" is a bike, "buy one" is the thing in hand.
A_THING_NAMED = re.compile(r"\b(?:afford|buy|get|pay\s+for)\s+(?:a|an|the|my|our|another|some)?\s*"
                           r"([a-z][a-z'-]{2,})", re.I)
NOT_A_THING = frozenset(("it", "one", "ones", "them", "that", "this", "thing", "stuff", "something",
                         "anything", "enough", "there", "what", "which"))


# Money that leaves the person every month is not money they put by. "my rent is 800 a month"
# then "how long until i can buy a car" was read as a rate and answered "£800 a month is £4,800
# every six months, £9,600 in a year" - the rent, counted as saving, over a question about a car.
# A rate qualifies as money put by when the line or the chat says so ("i save 50 a month", "i can
# put 30 a month aside", "50 a month spare"), and never when the figure is what the money goes on:
# rent, a mortgage, childcare, a payment, a wage.
PUT_BY = re.compile(
    r"\bsav(?:e|es|ed|ing|ings)\b"
    r"|\bput(?:ting)?\b[^.]{0,24}?\b(?:aside|by|away)\b"
    r"|\bset(?:ting)?\b[^.]{0,24}?\baside\b"
    r"|\bspar(?:e|es|ed|ing)\b"
    r"|\bsock(?:ing)?\b[^.]{0,12}?\baway\b"
    r"|\btuck(?:ing)?\b[^.]{0,12}?\baway\b"
    r"|\bsave\s+up\b", re.I)
# What the money goes on, or where it comes from. A line about any of these is a cost or a wage,
# so its figure is not the person's own rate however the chat was going.
MONEY_OUT = re.compile(
    r"\brent\b|\bmortgage\b|\bchildcare\b|\bnursery\b|\bwages?\b|\bsalary\b|\bpay\b|\bpaid\b"
    r"|\bbills?\b|\bloan\b|\binsurance\b|\bcouncil\s+tax\b|\belectricity\b|\bheating\b"
    r"|\bwater\s+bill\b|\bsubscriptions?\b|\bpayment\b|\bpayments\b|\bpaying\b"
    r"|\bcost(?:s|ing)?\b|\bfees?\b|\bfare\b|\bfares?\b|\btax\b", re.I)


def _the_rate_put_by(memory):
    """The sum a month the person put by, from the last few lines, or 0.

    `_the_rate_in_the_chat` reads any monthly figure, because it is only ever reached from a chat
    already about saving. This reader is reached from an ordinary chat - "how long until i can buy
    a bike" is not about saving - so the rate has to be recognisable as money put by, and a cost or
    a wage has to count for nothing.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    window = turns[-6:]
    if not any(PUT_BY.search(str(turn.get("user") or "")) for turn in window):
        return 0
    for turn in reversed(window):
        line = str(turn.get("user") or "")
        found = A_RATE.search(line)
        if not found or MONEY_OUT.search(line):
            continue
        try:
            value = int(found.group(1).replace(",", ""))
        except ValueError:
            continue
        if value >= 10:
            return value
    return 0


def a_length_with_no_price(text, memory):
    """The rate said as the money it becomes, and the price asked for, or "".

    Only when the length is asked and the price is missing: a line with a figure in it is the
    money entry's ("how long until i can afford 600"), and a chat with a goal in it is the
    arithmetic on the goal (`a_length_at_the_rate_in_the_chat`).
    """
    line = " ".join(str(text or "").lower().split())
    if not isinstance(memory, dict) or not line:
        return ""
    if not ASKS_A_LENGTH_FOR_A_THING.search(line) or not THE_THING_WANTED.search(line):
        return ""
    if re.search(r"\d", line):
        return ""  # a price of their own: the money entry works out the sum
    rate = _the_rate_put_by(memory)
    if rate < 10:
        return ""
    if _the_goal_in_the_chat(memory) or _the_goal_in_the_answer(memory):
        return ""  # there is a pot to do the arithmetic on
    six_months, a_year = rate * 6, rate * 12
    said = ("£%s a month is £%s every six months, £%s in a year."
            % (format(rate, ","), format(six_months, ","), format(a_year, ",")))
    named = A_THING_NAMED.search(line)
    thing = ""
    if named and named.group(1).lower() not in NOT_A_THING:
        thing = " " + named.group(1).lower()
    asked = ("What's the%s going for?" % thing) if thing else "What's the price on it?"
    if _already_asked_for_the_price(memory):
        # Asked once already: the figures again with no question is better than the same question
        # twice, and the person can do the rest with them.
        return said + " Tell me the price and I'll do the weeks."
    return said + " " + asked


def _already_asked_for_the_price(memory):
    """True when the answer above already asked what the thing costs."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict) and t.get("bot")]
    if not turns:
        return False
    above = str(turns[-1].get("bot") or "").lower()
    return bool(re.search(r"\bwhat(?:'s| is) (?:the |it |that )?(?:.* )?going for\b"
                          r"|\bwhat'?s the price\b|\bwhat does it cost\b|\bhow much is it\b", above))


def a_price_in_an_answer(text, memory):
    """The arithmetic for a price given in reply to the question "what's it going for?", or "".

    A price on its own line is a sum and nothing else, so read as a goal it would be answered as
    "For £200: £100 a month is 2 months..." - a fresh set of rates for someone who has already
    said what they can put by. It follows a question about the price, so the answer is the sum on
    the rate already in the chat: £200 at £50 a month is four months.
    """
    line = " ".join(str(text or "").lower().split())
    if not isinstance(memory, dict) or not line or len(line.split()) > 7:
        return ""
    price = _a_sum(line)
    if not price or _only_a_date(line) or _a_date(line):
        return ""
    rate = _the_rate_put_by(memory)
    if not rate or rate >= price:
        return ""
    if not _already_asked_for_the_price(memory):
        return ""
    months = -(-price // rate)
    # No closer here: the answer above was the sentence about the rate, so the sum arrives on top
    # of figures already given, and a tip after it read as a second, unrelated piece of advice.
    # The figure is the answer.
    return "£%s at £%s a month is %s." % (format(price, ","), format(rate, ","),
                                           _months(months))
