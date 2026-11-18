"""Sums about pay and time: what a month leaves you, and what a figure is in another period.

The arithmetic half of the money domain, in its own table because the two rules are one: a sum
the person typed, with a period on it, is a question about that sum. `bot/knowledge/money.py`
owns the ordinary advice; this file owns the rows that do the sum - one adult's month against
what the person has, and a figure said in one period asked in another.

Both rows read the figure and the period from the line and answer with the number. Both use a
`guard`, never a `return None` inside the reply, because a row that wins the words and then says
nothing leaves the line with no answer at all.
"""
import re

from .lookup import entry
from .money import _MONEY, _clause_about, _income_tax_and_ni, _per_month, _salary_in


def _living_not_a_bill(text):
    """"the cost of living" and "living costs" name the thing asked about, not money going out.

    `_per_month` reads a bill out of the line, and reading these as one made "would 1200 a month
    cover living costs" lose its figure and get the costs with an ask for a figure it already had.
    """
    for name in ("cost of living", "costs of living", "living costs", "living cost"):
        text = text.replace(name, "living")
    return text


ANSWERS = ("money",)

# "is 1,200 a month enough to live on", "can i get by on 300 a week" and "is 30k a year enough to
# live on" were answered with the budget-splitting card, the "I'm not sure about that one" punt or
# the "prices move too fast for me" punt. The question is arithmetic: what lands each month
# against what one adult's fixed costs come to. Those costs are the same few numbers whoever is
# asking, so the row reads the sum the person typed, turns a salary into take-home pay, and does
# the subtraction - which is the part a friend does out loud.
_LIVING = ("enough to live on", "enough to live", "enough to get by", "enough to survive",
           "to live on my own", "to live alone", "to live in london", "to live on your own",
           "enough money to live", "money to live on", "cost of living", "living costs",
           "afford to live", "live on", "live off", "survive on", "get by on",
           "need to live", "left to live on")
# A bare coping word carries no subject of its own: "is 1,200 enough for a week in spain" is a
# holiday, "how much exercise a week is enough" is not about money at all and "can we afford a
# house on one salary" is the mortgage. So these words only count beside a figure, and only when
# the line names no subject of its own - `_a_month_of_life`, below, is that test.
_COPING = ("enough", "get by", "manage", "survive", "cope", "cover", "afford",
           "live off", "stretch to", "left over")
_ENOUGH_TO_LIVE = _LIVING + _COPING
# ... and it is asked about a sum, so the line has to say what kind of figure it means. Without
# this part "what do hedgehogs live on" and "can i live off my savings" are the same words.
# ... and the figure has to be a monthly figure. A sum with no period on it is a price, and a
# price beside "enough" is about a thing and not about a month: "i have 80 pounds, is that enough"
# after "what coat should i get for winter", "i have 2000 pounds, is that enough" after a boiler
# and "i have 400 pounds, is that enough" after a laptop were all given one adult's monthly costs.
# So "pounds", "quid", "£", "rent", "bills" and "budget" are not in this part any more; a period
# word, a salary word or the living-alone phrasing has to be there.
_A_MONTH_OF_IT = ("a month", "per month", "each month", "monthly", "a week", "per week",
                  "each week", "weekly", "a year", "per year", "each year", "yearly", "annual",
                  "salary", "wage", "wages", "income", "take home",
                  # living on your own is one adult's month, and the same subtraction: "how much
                  # does it cost to live on your own" was answered "prices move too fast for me"
                  "on my own", "on your own", "by myself", "by yourself", "living alone",
                  "live alone")
# A line can also ask what the figure is, with no figure in it, and then the row answers with the
# costs and asks for the sum. Only these asks count: "how do i live on a low income" is a request
# for advice, not for a verdict on a figure, and the budget card answers it better.
_ASKS_WHAT_IS_NEEDED = ("how much does a single person need", "how much does someone need",
                        "how much do i need", "how much money do i need",
                        "how much money does it take", "what do i need to live",
                        "how much does it cost")
_A_SUM_A_MONTH = _A_MONTH_OF_IT + _ASKS_WHAT_IS_NEEDED
# The same question the other way round: "how much do i need to earn to live on my own" and
# "what salary do i need to live alone" were answered by a run-club card and the free-advice
# pointer. The bank balance is a net figure, so the answer is the gross salary that leaves it.
_EARN_ENOUGH = ("need to earn", "earn to live", "earn enough", "salary do i need",
                "salary would i need", "wage do i need", "how much do i need to earn",
                "what do i need to earn")
_LONDON = re.compile(r"\blondon\b|zone [12]|inner city", re.I)


def _the_gross_for(net_a_month):
    """The salary that leaves about this much in the bank, rounded up to the next £100."""
    gross = int(net_a_month * 12)
    for _ in range(40):
        tax, ni = _income_tax_and_ni(gross)
        if (gross - tax - ni) / 12.0 >= net_a_month:
            return int(-(-gross // 100) * 100)
        gross += 100
    return gross


def _a_months_costs(london):
    """What one adult's month costs, in the few numbers a friend would say."""
    if london:
        return ("In London the same month is roughly £2,000, nearly all of it rent: a one-bed is "
                "£1,300 to £1,900 there before the bills.")
    return ("Outside London one adult needs roughly £1,200 a month: rent £600 to £900, council tax "
            "about £180, energy about £145, food £150 to £200, and about £100 for broadband, phone "
            "and travel.")


_A_FIGURE = re.compile(_MONEY, re.I)


def _a_month_of_life(understood):
    """True when the line is about a month of ordinary life and not about one purchase.

    A figure in the line is what the row is about. With one, a living phrase answers on its own. A bare coping word does not: with only "enough", "afford" or "cover" in
    it, the line could be a holiday ("is 1,200 enough for a week in spain"), a mortgage ("can we
    afford a house on one salary") or something that is not money at all ("how much exercise a
    week is enough"). Those need a figure in the line and a reading that names no other subject -
    the understood topic is money or nothing - which is the difference between "is 60k a year
    enough" and a week in Spain. A guard, not a `return None` in the reply: a row that has won
    the words and then says nothing leaves the line with "I'm listening".
    """
    reading = understood if isinstance(understood, dict) else {}
    text = " " + str(reading.get("clean") or reading.get("text") or "").lower() + " "
    if _A_FIGURE.search(text):
        # a figure is the thing the row is about, and with it a bare coping word is enough when
        # the reading names no other subject
        if any(phrase in text for phrase in _LIVING):
            return True
        topic = str(reading.get("topic") or "")
        return any(word in text for word in _COPING) and topic in ("", "money")
    # no figure: only a line asking what the figure is gets one adult's month back
    if any(ask in text for ask in _ASKS_WHAT_IS_NEEDED) or _earn_asked(text):
        return any(phrase in text for phrase in _LIVING) or \
            any(word in text for word in _COPING)
    return False


def _earn_asked(text):
    """True when the line asks what to earn rather than what a sum you have will cover."""
    return any(phrase in text for phrase in _EARN_ENOUGH) or bool(
        re.search(r"\b(salary|wage)\b.{0,20}\b(need|needed|require[sd]?)\b", text))


def _enough_to_live_on(memory, understood):
    """A sum beside "enough to live on" is a subtraction, not a lesson in budgeting."""
    reading = understood or {}
    text = " " + str(reading.get("clean") or reading.get("text") or "").lower() + " "
    london = bool(_LONDON.search(text))
    monthly, lead = 0, ""
    if re.search(r"a year|per year|each year|yearly|annual", text):
        salary = _salary_in(text)
        if salary and salary >= 5000:
            tax, ni = _income_tax_and_ni(salary)
            monthly = int(round((salary - tax - ni) / 12.0))
            lead = ("On £{:,} a year you take home about £{:,} a month. "
                    .format(salary, monthly))
    if not monthly:
        monthly = _per_month(_living_not_a_bill(text))
    tight, enough = (1750, 2100) if london else (1050, 1300)
    where = "in London" if london else "outside London"
    if _earn_asked(text):
        return ("You need roughly £%s a year before tax to live on your own %s - about £%s a "
                "month after tax. " % (format(_the_gross_for(enough), ","), where,
                                       format(enough, ","))
                + _a_months_costs(london) + " Both move, so check this year's band and the "
                "price cap.")
    if not monthly:
        return (_a_months_costs(london) + " Tell me the figure you have in mind and I will say "
                "whether it covers the month.")
    if monthly >= enough:
        verdict = ("£%s a month is enough %s, with room to save."
                   % (format(monthly, ","), where))
    elif monthly >= tight:
        verdict = ("£%s a month is enough %s only with a cheap rent - there is little left at the "
                   "end of the month." % (format(monthly, ","), where))
    else:
        verdict = ("£%s a month leaves you about £%s short of what one adult needs %s."
                   % (format(monthly, ","), format(enough - monthly, ","), where))
    return (lead + verdict + " " + _a_months_costs(london)
            + " Both move, so check this year's band and the price cap.")


ENTRIES = []


ENTRIES.append(entry(
    "enough-to-live-on",
    (_ENOUGH_TO_LIVE, _A_SUM_A_MONTH),
    _enough_to_live_on,
    bias=2,
    guard=_a_month_of_life,
    # what a month costs, not the price of one thing, not a deposit, and not a benefit
    avoid=("deposit", "saved", "savings goal", "mortgage", "buy a flat", "buy a house",
           "for food", "on food", "food shop", "for petrol", "on petrol", "universal credit",
           "benefit", "benefits", "carer", "carers", "pension", "abroad", "dog", "dogs", "cat",
           "cats", "pet", "pets", "plants", "my partner", "my husband", "my wife", "my son",
           "my daughter", "family of", "two of us", "kids", "children",
           # a rent question is the rent-afford row's, and a bill is the bill's
           "rent", "deposit", "council tax", "energy bill", "gas bill", "electric bill"),
    ask=("enough", "much", "how do i", "can i", "could i", "will i", "do i", "is it", "would i",
         "need", "get by", "afford", "only", "just", "survive", "manage", "cover")))

# A sum said in one period and asked in another is arithmetic, and nothing answered it: "whats
# 2500 a month a year" was a search hedge, "how much is 2500 a month over a year" and "200 a
# month is how much a year" both got the card about keeping records for five years - "a year"
# beside a figure is also the shape of "how long do i keep this" - and "i pay 900 a month rent,
# whats that a year" got the landlord's letter. The period in the sum's own phrase says which
# period the figure is in; the other period the line names is the one to answer in, and the
# answer is a multiplication.
_A_PERIOD_IN_A_SUM = re.compile(
    _MONEY + r"\s*(?:a|an|per|each|every|/)\s*"
    r"(week|weekly|fortnight|fortnightly|month|monthly|year|yearly|annually|annual)", re.I)
# How many of each period there are in a year, so a sum in any of them can be read as a rate.
_PERIODS_IN_A_YEAR = {"week": 52.0, "weekly": 52.0, "fortnight": 26.0, "fortnightly": 26.0,
              "month": 12.0, "monthly": 12.0, "year": 1.0, "yearly": 1.0,
              "annual": 1.0, "annually": 1.0}
# The period the person wants the answer in, said anywhere but inside the sum's own phrase.
_ANOTHER_PERIOD = re.compile(
    r"\b(?:a|an|per|each|every|over|in|for|of|the)\s*"
    r"(week|fortnight|month|year)\b|\b(yearly|annually|annual|monthly|weekly)\b", re.I)
_EVERYDAY_PERIOD = {"yearly": "year", "annually": "year", "annual": "year",
                    "monthly": "month", "weekly": "week"}
_SAID_AGAIN = {"year": "a year", "month": "a month", "week": "a week",
               "fortnight": "a fortnight"}


def _per_period(text):
    """(sum, its period, the other period asked for) from a line that names both, or None."""
    match = _A_PERIOD_IN_A_SUM.search(text)
    if not match:
        return None
    amount = float(match.group(1).replace(",", ""))
    if match.group(2):
        amount *= 1000
    own = match.group(3).lower()
    own = _EVERYDAY_PERIOD.get(own, own)
    for other in _ANOTHER_PERIOD.finditer(text):
        if other.start() < match.end() and other.end() > match.start():
            continue
        wanted = (other.group(1) or other.group(2) or "").lower()
        wanted = _EVERYDAY_PERIOD.get(wanted, wanted)
        if wanted in ("week", "fortnight", "month", "year") and wanted != own:
            return amount, own, wanted
    return None


# The words that make a second period a figure being asked for rather than a scene being described.
_ASKS_FOR_THE_FIGURE = ("how much", "how many", "whats", "what's", "what is", "what does",
                        "what would", "what will", "comes to", "come to", "convert", "worth",
                        "equivalent", "in a year", "in a month", "in a week", "over a year",
                        "over a month", "a year in total", "a year altogether")


def _two_periods_named(understood):
    """True when the line names a sum in one period and asks for another.

    A guard rather than a `return None` in the reply: a row that has won the words and then says
    nothing leaves the line with no answer at all, which is how "30k a year is how much a month"
    became "I'm listening".
    """
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    return bool(_per_period(text))


def _a_sum_in_another_period(memory, understood):
    """One period's sum worked into another period, with the tax where the sum is pay."""
    reading = understood or {}
    text = str(reading.get("clean") or reading.get("text") or "").lower()
    if any(word in text for word in ("keep", "records", "receipts", "payslips", "statements",
                                     "tax return", "how long", "how many years")):
        # the records rows own "how long do i keep" and say "a year" beside a figure too
        return None
    found = _per_period(text)
    if not found:
        return None
    if not any(ask in text for ask in _ASKS_FOR_THE_FIGURE):
        # a period named beside a sum is not always a conversion being asked for: "i pay 42 a
        # month for the gym and go about twice a week, is that daft" is a verdict, and a rate
        # worked into a week would be a confident answer to a different question
        return None
    amount, own, wanted = found
    annual = amount * _PERIODS_IN_A_YEAR[own]
    value = annual / _PERIODS_IN_A_YEAR[wanted]
    said = "£{:,} {} is £{:,} {}.".format(
        int(round(amount)), _SAID_AGAIN[own], int(round(value)), _SAID_AGAIN[wanted])
    clause = _clause_about(text, 0, len(text))
    if any(word in clause for word in ("earn", "earns", "salary", "wage", "wages", "paid",
                                       "pay", "job")):
        tax, ni = _income_tax_and_ni(int(round(annual)))
        left = annual - tax - ni
        said += (" After tax and National Insurance that is about £{:,} a month, or £{:,} a "
                 "year.".format(int(round(left / 12)), int(round(left))))
    return said


ENTRIES.append(entry(
    "a-sum-in-another-period",
    (("a month", "a week", "a fortnight", "a month", "per month", "monthly", "each month",
      "weekly", "every week", "each week", "a month"),
     ("a year", "yearly", "a yr", "per year", "annually", "annual", "over a year", "in a year",
      "a month", "monthly", "per month", "a week", "weekly", "per week")),
    _a_sum_in_another_period,
    guard=_two_periods_named,
    # the savings rows answer a rate put by ("150 spare a month, whats that a year") and the
    # landlord's rows answer a rent; both name a sum and a period and both are better than a
    # conversion, so this row stands down for their words
    avoid=("spare", "save", "saving", "savings", "put by", "put aside", "put away", "set aside",
           "rent", "landlord", "deposit", "mortgage", "afford", "budget", "cheapest",
           "how long", "records", "receipts",
           # the take-home row owns every line that says what tax does to a salary
           "after tax", "take home", "take-home", "net pay", "tax"),
    bias=2))
