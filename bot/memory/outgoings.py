"""What comes in and what goes out: "im on 1800 a month and rent is 700".

A person setting out their month says the two figures together, because together they are the one
thing worth knowing: what is left. Nothing in the bot read the pair. Each figure found a card of
its own, or a receipt:

```
im on 1800 a month and rent is 700        -> "Tell the landlord in writing before the next rent
                                              day, and ask the council about a Discretionary
                                              Housing Payment..."   (the arrears card)
i earn 1800 and my rent is 700            -> "Thanks for telling me - I'm here if you want to dig
                                              into any of that."
i take home 1800 and rent is 700          -> "Coming into the UK you can bring 4 litres of
                                              spirits..."   (the duty-free entry, off "take home")
we bring in 2400 and the mortgage is 900  -> "Got it. Is there anything you'd like a hand with?"
rent is 700                               -> the arrears card again, to somebody who is not behind
```

The arrears card is right for "i cant pay my rent" and wrong for "rent is 700". The duty-free card
is right for nothing here at all: the words "take home" found it. The two figures are the line, so
the two figures are what the reply is about.

Three shapes, each answered with arithmetic on the person's own numbers:

* what comes in and what goes out in one line - "im on 1800 a month and rent is 700" - and what is
  left after the rent is the answer;
* the cost on its own after the income was said a turn or two before ("i earn about 1800 a month" /
  "and rent is 900"), which is the same sum with the income read off the chat;
* the income on its own when the chat is already about putting money by ("how much should i save
  each month" / "i earn about 1800 a month"), which is the share of *their* figure rather than the
  share of the example figure the money entry uses.

Nothing is invented: every figure in the reply is one the person gave, or a share the money entry
already uses ("put away 10 to 20 percent of your take-home", "a tenth to a fifth"). What is not a
budget line is left alone - arrears, an eviction notice, a rent that is going up, a tax code, and
every ask ("should i overpay", "how do i budget") belong to the readings that answer them.
"""
import re

# A figure with no money on it at all ("im on 1800", "rent is 700"), and a sum written the way
# people write money: "£700", "700 pounds", "2k". The bare figure is only read beside a word that
# makes it money (`INCOME`, `FIXED_COST`), because on its own it is a count - "2 kids", "3 beds".
SUM = re.compile(
    r"£\s*(?P<marked>\d[\d,]*(?:\.\d+)?)\s*(?P<marked_unit>k|grand|thousand)?"
    r"|(?P<bare>\d[\d,]*(?:\.\d+)?)\s*(?P<bare_unit>k|grand|thousand|pounds?|quid)\b",
    re.I,
)
BARE_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")

# What comes in. `take home` is in here because it is how most people say a net wage, and the
# duty-free entry that answered it was reading those two words rather than the money.
INCOME = re.compile(
    r"\b(?:i|we)(?:'m|m|'re| are)?\s+(?:on|earn|earns|make|makes|bring\s+in|brings\s+in|get|gets)\b"
    r"|\btake[\s-]?home\b"
    r"|\b(?:my|our)\s+(?:pay|wage|wages|salary|pension|income|earnings)\b"
    r"|\bafter\s+tax\b"
    # The other wage in the house: "i make 1200 and my partner makes 800 and the rent is 900" is
    # £2,000 coming in, and only the first of them was read.
    r"|\b(?:partner|husband|wife)\s+(?:earns?|makes?|brings?\s+in|gets?|takes?\s+home)\b",
    re.I,
)
# What goes out, as a fixed cost of the month rather than a price: a rent, a mortgage, the
# childcare, the bills.
FIXED_COST = re.compile(
    r"\b(?:rents?|mortgage|childcare|child\s*care|childminder|nursery|nursery\s+fees|"
    r"school\s+(?:fees|dinners|clubs?)|breakfast\s+club|after[\s-]school\s+club|"
    r"council\s+tax|bills?|utility|utilities|energy|electric(?:ity)?|water|gas|heating|"
    r"broadband|internet|phone|mobile|tv\s+licen[cs]e|car\s+finance|car\s+payment|"
    r"car\s+insurance|loan|loans|repayments?|insurance|commut\w*|travel|fares?|transport|"
    r"petrol|diesel|fuel|parking|tolls?|train\s+fare|season\s+ticket|bus\s+pass|"
    r"subscriptions?|gym|clothes|uniforms?|nappies|food|groceries|shopping|"
    r"car|van|pets?|vets?|vet\s+bills?|medicines?|prescriptions?|dentist|"
    r"child\s+maintenance|maintenance)\b",
    re.I,
)
# A figure and the cost it belongs to, in the other order: "400 goes on childcare", "600 on food
# and 200 on travel". This is the shape people type when they are spending, and it names the thing
# without a list of every cost there is.
AFTER_THE_FIGURE = re.compile(
    r"^\s*(?:a\s+(?:month|week|year|fortnight)\s*)?(?:goes?|went|is\s+spent|are\s+spent)?\s*"
    r"(?:on|for|towards|into)\s+(?P<noun>[a-z][a-z'\-]*)",
    re.I,
)
# Words that fill the phrase rather than name what the money went on: "600 on the two of them"
# names nothing the bot can say back.
NOT_A_COST_NAME = re.compile(
    r"^(?:a|an|the|it|them|that|this|me|us|him|her|his|my|our|their|its|and|or|so|but|if|when|"
    r"top|all|everything|nothing|stuff|things?)$",
    re.I,
)
# A period on the line. The chat's own unit is used when the line has none ("how much should i
# save a month" / "i earn 1800"), because it is the same sum in the unit they are speaking.
MONTH = re.compile(
    r"\b(?:a|per|each|every)\s+month\b|\bmonthly\b|\bpcm\b|\b(?:a|per)\s+4\s+weeks\b", re.I)
WEEK = re.compile(r"\b(?:a|per|each|every)\s+week\b|\bweekly\b", re.I)
YEAR = re.compile(
    r"\b(?:a|per|each|every)\s+year\b|\byearly\b|\bannually\b|\ba\s+year\b|\bp\.?a\.?\b", re.I)

# A rent that is late, behind or under threat is the arrears reading's line, and its card is the
# right answer: "i cant pay my rent", "im behind on the mortgage", "is my rent too high". The sum
# here would be arithmetic about a month that has already gone wrong.
NOT_A_BUDGET_LINE = re.compile(
    r"\b(?:arrears?|behind|overdue|evict\w*|notice|can'?t\s+pay|cant\s+pay|couldn'?t\s+pay|"
    r"not\s+paid|unpaid|short\s+this\s+month|owing|owe|owed|debt|debts|default\w*|bailiff\w*|"
    r"due|going\s+up|went\s+up|go\s+up|gone\s+up|goes\s+up|rising|increas\w*|raise[sd]?|cheaper|"
    r"reduce|reducing|lower|negotiate|"
    r"landlord|housing\s+benefit|universal\s+credit)\b",
    re.I,
)
# An ask is the knowledge base's: "should i overpay my mortgage", "how do i budget", "is 850 too
# much rent". A statement of the two figures is what this reader answers.
AN_ASK = re.compile(
    r"^\s*(?:should|could|can|do|does|is|are|was|were|what|how|when|where|which|why|would|will)\b"
    # An ask tacked onto the sum with a comma is still an ask: "i earn 1800 and my rent is 700, is
    # that enough" wants a view on the figures, not the subtraction it already did in their head.
    r"|[,;]\s*(?:should|could|can|do|does|is|are|was|were|what|how|when|where|which|why|would|"
    r"will)\s+\w"
    r"|\?\s*$",
    re.I,
)
# A figure with a measure after it is not money: "i have a 90 minute commute each way" is a
# journey, and read as money it came out as £1,710 a month left after the commute.
A_MEASURE = re.compile(
    r"^\s*(?:mins?|minutes?|hours?|hrs?|days?|weeks?|months?|years?|miles?|km|kg|bed(?:room)?s?|"
    r"kids?|people|guests?|percent|%)",
    re.I,
)
# A tax code is not a month: "im on 1150L", "1257L". The letters are stuck to the figure, which
# is what tells a code from a sum followed by an article ("1800 a month").
A_CODE = re.compile(r"\b\d{3,}[A-Za-z]{1,2}\b")
# Money put by is not money going out: "rent is 750 and i put 200 aside" has one fixed cost and
# one saving, and counting the 200 as a cost counts the same money twice.
A_HAND_HELD = re.compile(
    r"\b(?:put|set|stick)\s+(?:\u00a3?\d[\d,]*(?:\.\d+)?\s+)?(?:by|aside|away)\b"
    r"|\b(?:save[sd]?|saving|savings|pot|putting\s+by)\b",
    re.I,
)

# The share of a take-home the money entry already says to put by, in the words it uses.
# "rents 850 and i take home 2100" is the rent: the cost is said in the plural, the month is not.
_THE_COST = {"rents": "rent", "bills": "bills", "loans": "loan payments", "repayments": "repayment"}

LOW_SHARE = 0.10
HIGH_SHARE = 0.20

# The sum, then the one step that follows from it. No variant ends with a question: the person has
# just told the bot their month, and a question back makes them do the work.
LEFT = (
    "That leaves {left} after the {named}. Food, travel and the rest come out of that, and whatever "
    "is over at the end is what you can put by.",
    "{left} left after the {named}, then. A standing order for the amount you want to keep, on the "
    "day after payday, takes it out before you can spend it.",
    "So {in_amount} in and {out_amount} out on the {named} leaves {left}. Pick the figure you want "
    "to keep and move it the day you are paid.",
)
# A wage said by the year against a rent said with no period at all: "im on 28000 a year" / "my
# rent is 900". £900 a month, not £900 a year - nobody's rent is £900 a year - so the year is turned
# into a month and both figures are said, rather than £27,100 left, which is what subtracting a
# month's rent from a year's wage came to.
A_YEAR_AND_A_MONTH = (
    "{in_amount} a year is about {a_month} a month, so the {named} leaves {left}.",
    "{in_amount} a year works out at {a_month} a month, and after the {named} there is {left}.",
)
# The one step that follows from the sum, for "what should i do first" asked next.
FIRST_MOVE = (
    "Set the standing order first: choose the figure you want to keep and move it the day after you "
    "are paid, so the month runs on what is left rather than the other way round.",
    "Start with the standing order on payday for the figure you want to keep. Everything else in the "
    "month can move around it.",
)
A_FIRST_ASK = re.compile(
    r"\b(?:what|where)\s+(?:should|do|shall)\s+i\s+(?:do|start|begin)\b[^.?!]*\b"
    r"(?:first|next|now|start)\b"
    r"|\bhow\s+do\s+i\s+(?:start|begin)\b"
    r"|\bwhere\s+(?:do|should)\s+i\s+(?:even\s+)?(?:start|begin)\b"
    r"|\bwhat'?s\s+(?:the\s+)?first\s+(?:step|thing)\b",
    re.I,
)
# The ask that takes the step after the sum has to be about the sum. "what should i do first" and
# "where do i start" point back at the month; "how do i start meditating", asked a turn after the
# sum, is a new subject and a standing order answers the wrong question.
# "whats left", right after the sum: the figure is already on the table, so the line is asking for it
# again rather than about a new subject.
A_LEFT_ASK = re.compile(
    r"\bwhat'?s\s+left\b|\bwhat\s+is\s+left\b|\bwhat'?s\s+left\s+over\b|"
    r"\bhow\s+much\s+(?:is\s+left|left|do\s+i\s+have\s+left|have\s+i\s+(?:got\s+)?left)\b",
    re.I,
)
LEFT_AGAIN = (
    "{left} {unit}, on the figures you gave.",
    "Same sum, on the figures you gave: {left} {unit}.",
)
A_STEP_ASK_POINTS_BACK = re.compile(
    r"\b(?:that|this|it|them|those|these|now|next|first|then|month|months|money|save|saves|saving|"
    r"savings|budget|budgeting|pay|paid|payday|salary|wage|income|rent|bills?|pot|aside|afford)\b",
    re.I,
)
# The income alone, in a chat that is already about putting money by: the share of *their* figure.
A_SHARE = (
    "A tenth to a fifth of {in_amount} is {low} to {high} {period}, which is the usual amount to "
    "put by.",
    "Put by a tenth to a fifth of it: {low} to {high} {period}, out of {in_amount}.",
)


def _choice(shape, line, memory=None):
    """A shape for this line, never the one just used.

    `hash()` of a string is salted per run, so the index comes from the letters; and the ending the
    bot used on the turn before is skipped, because two arithmetic replies in a row that close with
    the same sentence read as one sentence said twice ("the childcare is 400 a month on top").
    """
    was = ""
    if isinstance(memory, dict):
        turns = memory.get("turns") or ()
        if turns and isinstance(turns[-1], dict):
            was = str(turns[-1].get("bot") or "")
    start = sum(map(ord, str(line or ""))) % len(shape)
    for step in range(len(shape)):
        candidate = shape[(start + step) % len(shape)]
        opener = candidate.split("{")[0].strip()
        if not opener or opener[:28] not in was:
            return candidate
    return shape[start]


def _the_names(costs):
    """The costs as one phrase: "rent", "rent and the childcare", "rent, the nursery and the loan"."""
    names = []
    for name, _value in costs:
        name = _THE_COST.get(name, name)
        if name not in names:
            names.append(name)
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return "%s and the %s" % (names[0], names[1])
    return "%s and the %s" % (", ".join(names[:-1]), names[-1])


def _sums(text):
    """(value, start, end) for every figure in the line that can be money.

    Both passes run, not one after the other only if the first found nothing: "i earn 1800 a month
    and my rent is 700 pounds" pairs "700 pounds" with its money word, and stopping there lost the
    1800 and the whole line with it.
    """
    found = []
    taken = []
    for match in SUM.finditer(text):
        value = match.group("marked") or match.group("bare")
        unit = (match.group("marked_unit") or match.group("bare_unit") or "").lower()
        try:
            number = float(value.replace(",", ""))
        except (TypeError, ValueError):
            continue
        if unit in ("k", "grand", "thousand"):
            number *= 1000
        if text[match.end():match.end() + 1].isalpha() or A_MEASURE.match(text[match.end():]):
            continue
        if number >= 20:
            found.append((number, match.start(), match.end()))
            taken.append((match.start(), match.end()))
    for match in BARE_NUMBER.finditer(text):
        if any(start <= match.start() < end for start, end in taken):
            continue
        if text[match.end():match.end() + 1].isalpha() or A_MEASURE.match(text[match.end():]):
            continue
        try:
            number = float(match.group(0).replace(",", ""))
        except ValueError:
            continue
        if number >= 20:
            found.append((number, match.start(), match.end()))
    found.sort(key=lambda item: item[1])
    return found


def _period(text):
    """The unit a figure is said in: "a month" unless the line says a week or a year."""
    if WEEK.search(text):
        return "a week"
    if YEAR.search(text):
        return "a year"
    if MONTH.search(text):
        return "a month"
    return ""


def _units_in(text):
    """The units a line names, as a set: {"a month"}, or {"a month", "a week"} when it mixes two."""
    found = set()
    for pattern, unit in ((MONTH, "a month"), (WEEK, "a week"), (YEAR, "a year")):
        if pattern.search(text):
            found.add(unit)
    return found


def _pounds(value):
    """£1,100 / £180.50 - the mark on, and the figure the way people write it."""
    if abs(value - round(value)) < 0.005:
        return "£%s" % format(int(round(value)), ",")
    return "£%s" % format(round(value, 2), ",.2f")


def _with_unit(value, unit):
    """"£1,100 a month", or "£1,100" when the line never said which month it is."""
    figure = _pounds(value)
    return "%s %s" % (figure, unit) if unit else figure


def _in_phrase(text, start, end, pattern, span=18):
    """Whether `pattern` runs around the figure, over it: "put 200 aside" has the 200 inside it."""
    return bool(pattern.search(text[max(0, start - span):end + span]))


def _near(text, start, end, pattern, before=30, after=30):
    """Whether `pattern` sits within those characters of the figure, either side of it."""
    return bool(pattern.search(text[max(0, start - before):start])) or \
        bool(pattern.search(text[end:end + after]))


def _the_nearest(line, cue, sums, after=20, before=6):
    """The sum a word is talking about: the first one after it, else the last one before it.

    "i take home 1800 and rent is 700" has two figures, and the one the income words are about is
    the one they are next to - 1800. A window on both sides and no order to it took the rent, and
    then the sum came out as the same figure twice: £1,300 left after the rent, out of £850.
    """
    best = None
    for value, start, end in sums:
        gap = start - cue.end()
        if 0 <= gap <= after:
            distance = gap
        else:
            gap = cue.start() - end
            if not 0 <= gap <= before:
                continue
            distance = gap
        if best is None or distance < best[0]:
            best = (distance, value, start, end)
    return best


def _the_incomes_in_the_line(line, sums=None):
    """[(value, start, end)] for every figure the line calls money coming in."""
    if not line or not INCOME.search(line) or A_CODE.search(line):
        return []
    if sums is None:
        sums = _sums(line)
    found = []
    seen = []
    for cue in INCOME.finditer(line):
        nearest = _the_nearest(line, cue, sums, after=20, before=8)
        if not nearest:
            continue
        _distance, value, start, end = nearest
        if start in seen:
            # Two income words about one figure: "my salary - i earn 1800 a month" is one wage.
            continue
        seen.append(start)
        found.append((value, start, end))
    return found


def the_income_in_the_line(text):
    """(value, period) for "im on 1800 a month" and "i take home 1800", or None.

    Every wage the line names is money coming in. "i make 1200 and my partner makes 800 and the
    rent is 900" is a household of £2,000; reading only the first wage left £800 of it off the
    month and said "£300 left after the rent".
    """
    line = str(text or "")
    if not line:
        return None
    incomes = _the_incomes_in_the_line(line)
    if not incomes:
        return None
    return sum(value for value, _start, _end in incomes), _period(line)


def _the_cost_the_figure_is_for(line, start, end):
    """The cost a figure belongs to, or "" when nothing beside it says money is going out.

    Either order: "rent is 700" and "the childcare is 400" name the cost before the figure, while
    "400 goes on childcare" and "600 on food" name it after. The nearest cost word wins, so a line
    with two of them - "rent is 700 and food is 300" - puts each figure with its own word.
    """
    before = line[max(0, start - 26):start]
    after = line[end:end + 26]
    best = None
    for match in FIXED_COST.finditer(before):
        distance = len(before) - match.end()
        if best is None or distance < best[0]:
            best = (distance, match.group(0).lower())
    for match in FIXED_COST.finditer(after):
        distance = match.start()
        if best is None or distance < best[0]:
            best = (distance, match.group(0).lower())
    if best:
        return best[1]
    on_shape = AFTER_THE_FIGURE.match(after)
    if on_shape and not NOT_A_COST_NAME.match(on_shape.group("noun")):
        return on_shape.group("noun").lower()
    return ""


def _the_unit_beside(line, end):
    """The period said right after a figure: "900 a month" is a month, "900" says nothing."""
    tail = line[end:end + 16]
    for pattern, unit in ((MONTH, "a month"), (WEEK, "a week"), (YEAR, "a year")):
        match = pattern.search(tail)
        if match and not tail[:match.start()].strip(" ,-"):
            return unit
    return ""


def the_costs_with_units_in_the_line(text):
    """[(name, value, unit)] for the costs the line names, each with the period it was said in.

    "and rent is 900" is one. "rent is due on the 2nd" names none, and "rent is 750 and i put 200
    aside" is one cost and one pot, so the pot is not read as a cost.

    Every figure that is not the income comes off, not just the last one: "i earn 2000 and rent is
    700 and food is 300" left £1,300 when only the rent was counted, and the food was gone from the
    sentence, which is the one thing a money answer cannot do. A figure nothing in the line
    explains - neither the income nor a cost - takes the whole reading with it: half a sum is worse
    than none.
    """
    line = str(text or "")
    if not line:
        return []
    sums = _sums(line)
    incomes = set(start for _value, start, _end in _the_incomes_in_the_line(line, sums))
    found = []
    for value, start, end in sums:
        if start in incomes:
            continue
        # Money put by is not money going out: "rent is 750 and i put 200 aside" is one cost and
        # one saving, and counting the 200 as a cost counts the same money twice.
        if _in_phrase(line, start, end, A_HAND_HELD):
            continue
        name = _the_cost_the_figure_is_for(line, start, end)
        if not name:
            return []
        found.append((name, value, _the_unit_beside(line, end)))
    return found


def the_outgoings_in_the_line(text):
    """[(name, value)] for the costs the line names with a figure beside them, all of them."""
    return [(name, value) for name, value, _unit in the_costs_with_units_in_the_line(text)]


def _there_is_memory(memory):
    """Whether the chat has said anything before this line.

    The runtime writes memory["turns"] after the turn, so during a first line there is nothing
    behind it: a reply built on the chat needs the chat, and on the first line only the line itself
    can answer.
    """
    if not isinstance(memory, dict):
        return False
    for turn in memory.get("turns") or []:
        if not isinstance(turn, dict):
            continue
        if str(turn.get("user") or "").strip() or str(turn.get("bot") or "").strip():
            return True
    return False


def _the_income_before(memory):
    """(value, period) from the two lines before, when this one says only what goes out.

    "i earn about 1800 a month" / "and rent is 900": the second line is the first with the income
    off the screen, and it was answered "Got it - rent is 900." Only the two lines before, so an
    income said ten turns ago in another subject is not brought back as this month's.
    """
    if not isinstance(memory, dict):
        return None
    seen = 0
    for turn in reversed(list(memory.get("turns") or [])):
        line = turn.get("user") if isinstance(turn, dict) else None
        if not isinstance(line, str) or not line.strip():
            continue
        seen += 1
        if seen > 2:
            return None
        income = the_income_in_the_line(line)
        if income:
            return income
    return None


def _the_costs_before(memory):
    """[(name, value)] for the costs the two lines before named with a figure.

    "we bring in 2400 a month and the mortgage is 900" / "the nursery is 600 on top": the second
    line is not a fresh month with only a nursery in it. Read on its own the sum came out as £1,800
    left, which is £600 more than the person has - the first line's mortgage had gone off the
    screen. What is already off the month stays off it, and the names of both are said.
    """
    if not isinstance(memory, dict):
        return []
    found = []
    seen = 0
    for turn in reversed(list(memory.get("turns") or [])):
        line = turn.get("user") if isinstance(turn, dict) else None
        if not isinstance(line, str) or not line.strip():
            continue
        seen += 1
        if seen > 2:
            break
        found = the_outgoings_in_the_line(line) + found
    return found


def _remember(memory, left, unit):
    """Leave a note that this turn was the month set out, for the line that asks what comes next."""
    if isinstance(memory, dict):
        memory["the_month_set_out"] = {"left": left, "unit": unit}


def _the_pot_in_the_line(text):
    """The figure the line puts by, or 0: "rent is 750 and i put 200 aside"."""
    line = str(text or "")
    for value, start, end in _sums(line):
        # "put 200 aside" has the figure inside the words, so the words are looked for around the
        # figure rather than the figure around the words.
        if _in_phrase(line, start, end, A_HAND_HELD):
            return value
    return 0


def _the_left_again(line, memory):
    """The figure the month left, said again to the line that asks what is left of it."""
    month = memory.get("the_month_set_out") if isinstance(memory, dict) else None
    if not isinstance(month, dict):
        return ""
    left = month.get("left")
    unit = month.get("unit") or "a month"
    if not left or left <= 0:
        return ""
    return _choice(LEFT_AGAIN, line, memory).format(
        left="\u00a3{:,}".format(int(round(float(left)))), unit=unit)


def _the_ask_points_back(line):
    """Whether "where do i start" is about the month or about something else entirely."""
    if A_STEP_ASK_POINTS_BACK.search(line):
        return True
    return len(re.findall(r"[A-Za-z']+", line)) <= 4


def _the_month_was_just_set_out(memory):
    """Whether the turn before this one was the sum, so "what should i do first" has a subject."""
    if not isinstance(memory, dict) or not memory.get("the_month_set_out"):
        return False
    turns = memory.get("turns") or ()
    if not turns or not isinstance(turns[-1], dict):
        return False
    said = str(turns[-1].get("bot") or "")
    return bool(re.search(r"\bleaves \u00a3|\bleft after the\b", said))


def _the_unit_in_the_chat(memory):
    """The unit the chat is speaking in: "how much should i save a month" sets the month."""
    if not isinstance(memory, dict):
        return ""
    for turn in reversed(list(memory.get("turns") or [])[-2:]):
        line = turn.get("user") if isinstance(turn, dict) else ""
        if isinstance(line, str):
            unit = _period(line)
            if unit:
                return unit
    return ""


def _the_chat_is_about_saving(memory):
    """Whether the last two turns were about putting money by."""
    if not isinstance(memory, dict):
        return False
    said = []
    for turn in list(memory.get("turns") or [])[-2:]:
        if isinstance(turn, dict):
            said.append(str(turn.get("user") or ""))
            said.append(str(turn.get("bot") or ""))
    return bool(re.search(r"\b(?:save|saves|saving|savings|put\s+(?:by|aside|away)|budget|"
                          r"deposit|putting\s+by)\b", " ".join(said), re.I))


def reply_for(text, memory=None):
    """The reply a line about the month gets, or "" when it is not one.

    A reply only where the arithmetic is the answer: what is left, or the share of a take-home in a
    chat that is already about saving. Everything else - arrears, an ask, a rent that is going up, a
    tax code - keeps the reply it already had.
    """
    line = str(text or "").strip()
    if not line or len(line) > 220:
        return ""
    if A_LEFT_ASK.search(line) and _the_month_was_just_set_out(memory):
        return _the_left_again(line, memory)
    if A_FIRST_ASK.search(line) and _the_month_was_just_set_out(memory) \
            and _the_ask_points_back(line):
        return _choice(FIRST_MOVE, line, memory)
    if NOT_A_BUDGET_LINE.search(line) or AN_ASK.search(line):
        return ""
    # Silly to try to add: "im on 1800 a month and rent is 200 a week" is two units in one line,
    # and a sum across them is a monthly wage minus a weekly rent, which is not a month at all.
    if len(_units_in(line)) > 1:
        return ""
    unit = _period(line)
    income = the_income_in_the_line(line)
    with_units = the_costs_with_units_in_the_line(line)
    costs = [(name, value) for name, value, _said in with_units]
    if not _there_is_memory(memory) and not (income and costs):
        # A reply about the month needs the month. On a first line there is nothing behind it, so
        # only the line itself can answer: "my rent is 900" alone is not a month to sum, an income
        # alone is not a share of a pot the chat has not named, and "what should i do first" has no
        # sum to start from. What main did with those lines is what they get.
        return ""
    if income and not unit:
        # No unit anywhere: "i earn 1800 and my rent is 700" is a month to most people and a week
        # to some, so the sum is said without one - "£1,100 left after the rent" is true either
        # way, and a period invented on the line would be wrong for half the people who type it.
        income = (income[0], _the_unit_in_the_chat(memory))
    own_month = bool(income)
    if not income:
        earlier = _the_income_before(memory)
        if not earlier or not costs:
            return ""
        income = (earlier[0], earlier[1] or unit or _the_unit_in_the_chat(memory))
    value, unit = income
    if costs:
        # The costs the chat said before belong to the month they were said in. A line that sets
        # out a month of its own - its own income and its own rent - is a different month, and
        # adding the earlier house's mortgage to it states a figure that is not theirs: "we bring
        # in 2400 a month and the mortgage is 900" and then "im on 1800 a month and rent is 700"
        # was answered "£200 a month after the mortgage and the rent", nine hundred too low.
        # A continuation has no income of its own ("the childcare is 400 a month on top"), and
        # there the earlier costs are the same month and are kept.
        before = []
        if not own_month:
            before = [cost for cost in _the_costs_before(memory)
                      if cost[0] not in [name for name, _value in costs]]
        costs = before + costs
        cost = costs[-1][1]
        named = _the_names(costs)
        # The period said on the cost itself, if the line said one there: "rent is 200 a week" is
        # a different month from a monthly wage, and "i earn 30000 a year and my rent is 700" has
        # a rent with no period at all, which is a month.
        cost_unit = with_units[-1][2] if with_units else ""
        if len(costs) == 1 and cost_unit and cost_unit != unit:
            return ""
        if unit == "a year" and cost_unit != "a year":
            # To the pound: "£2,333.33 a month" is a spreadsheet, not a person talking.
            a_month = round(value / 12.0)
            left = a_month - sum(cost for _name, cost in costs)
            if left <= 0 or left < a_month * 0.05:
                return ""
            _remember(memory, left, "a month")
            return _choice(A_YEAR_AND_A_MONTH, line, memory).format(
                in_amount=_pounds(value), a_month=_pounds(a_month), named=named,
                left=_with_unit(left, "a month"))
        left = value - sum(cost for _name, cost in costs)
        # Nothing left, or almost nothing, is not a month to plan: that line is about how tight
        # things are, and the money cards answer it better than arithmetic does.
        if left <= 0 or left < value * 0.05:
            return ""
        spent_all = sum(amount for _name, amount in costs)
        pot = _the_pot_in_the_line(line)
        reply = _choice(LEFT, line, memory).format(
            left=_with_unit(left, unit), named=named, in_amount=_pounds(value),
            out_amount=_pounds(spent_all))
        if pot:
            # The pot is not a second cost - it comes out of what is left, and saying so keeps the
            # sum right while answering the "and i put 200 aside" the person added to it.
            reply += " The %s you put by comes out of that." % _pounds(pot)
        _remember(memory, left, unit)
        return reply
    if not _the_chat_is_about_saving(memory):
        # An income on its own is the "what are you weighing it against" line, unless the chat is
        # already about putting money by, where the share of their own figure is the answer.
        return ""
    if not unit:
        return ""
    return _choice(A_SHARE, line, memory).format(in_amount=_pounds(value),
                                         low=_pounds(value * LOW_SHARE),
                                         high=_pounds(value * HIGH_SHARE), period=unit)
