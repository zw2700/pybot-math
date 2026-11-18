"""Money nobody explains out loud: when the state pension starts, and what it pays.

The state pension is one number in two forms - the age it starts and the years behind it - and
the money domain answers neither: "what is a state pension" got the workplace-pension answer and
"when do i get my state pension" got a MoneyHelper pointer, which is the question restated. The
figures change every April, so each answer gives the current figure and where the live one is.

This is a domain of its own because it is the one money table that nothing else shares: the
budget, the house deposit, the order to clear debts, a credit file and a mortgage are money.py,
and a private pension is money.py too, so this file says where it stops.
"""
import re

from .lookup import a_thing_has_stopped, entry

# The same topic as money.py and lifeadmin.py: the answers module already declares it.
ANSWERS = ("money",)


def _state_pension(memory, understood):
    """Two questions, both about a number: when it starts, and how much.

    A "when" line leads with the age, and the amount follows; a line about retiring early gets
    one more sentence, because stopping work and claiming are not the same event and people mix
    them up more than they mix up anything else here.
    """
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    record = ("Your record is on gov.uk under \"check your National Insurance record\": it lists "
              "each year and whether it counts, and gaps can often be filled by paying voluntary "
              "contributions.")
    asks_record = bool(re.search(r"\brecord\b|\bcheck\b.*\b(?:national insurance|\bni\b)", text))
    when = ("The state pension starts at 66 now, and at 67 for anyone reaching that age from 2028, "
            "with 68 to come later, so check your own date on gov.uk. It is not automatic: a letter "
            "should come about two months before, and if it does not, claim it on gov.uk or by "
            "phone.")
    # The figure leads, because "how much is the state pension" was answered with the years of
    # contributions and the amount came after twenty words of it. The amount, the year and the
    # number of years behind it are one sentence, in the order a person reads them out.
    years = ("The full new state pension is about £230 a week, £11,500 a year, in 2025-26, on 35 "
             "qualifying years of National Insurance; each year short pays about a thirtieth less, "
             "and you need at least 10 years to get anything at all.")
    # The line that counts the years it already has ("i have 10 years of national insurance, will
    # i get a pension") is asking about the record, not the date: leading with the age answers a
    # question it did not ask. A line that names a year or asks when keeps the age first.
    counted = re.search(r"\b\d+\s*years?\b|\bhow many years\b|"
                        r"\byears? of (?:national insurance|ni)\b|\bqualifying\b", text)
    asks_when = re.search(r"\bwhen\b|how old|what age|\bdate\b|\bretir(?:e|ing|ement)\b", text)
    # "how much is the state pension" is the amount, and it was getting the age: a line that asks
    # how much leads with the money, and only a line that asks when or at what age leads with the
    # date. Neither is a guess at the other.
    asks_amount = re.search(r"\bhow much\b|\bamount\b|\bper week\b|\ba week\b", text)
    if asks_record and not asks_when:
        reply = record + " " + years + " " + when
    elif (asks_amount or counted) and not asks_when:
        reply = years + " " + when
    else:
        reply = when + " " + years
    if re.search(r"\bretir(?:e|ing|ement)\b|\bstop(?:ping)?\s+work", text):
        reply += (" Stopping work and claiming it are two different things, so retiring early is a "
                  "question about your own money rather than about the pension.")
    return reply


ENTRIES = [
    entry("state-pension",
          # no bare "my pension" here: a workplace or personal pension is a different account
          # with different rules (contributions, a tax-free lump sum, access from 55), and
          # "can i take 25% of my pension tax free" would get this answer, which knows nothing
          # about any of it. A confident wrong answer is worse than the referral main gives.
          # no bare "retire": "can i retire at 60" and "how much do i need to retire" are the
          # retirement-target answer in money.py, which carries the pot size and the access age.
          # A line about stopping work while the state pension is in the line is the mix-up this
          # entry exists for, so "want" is here for "i want to stop work at 62".
          (("state pension", "pension age", "retirement age", "national insurance record",
            "national insurance years", "ni years", "ni record", "pension forecast",
            "qualifying years", "my state pension", "stop work", "stopping work",
            # "i have 10 years of national insurance will i get a pension" was answered by the
            # extended-warranty entry, on the word "insurance": the bare phrase has to be here,
            # spelled as a person says it, for the entry to own the line at all. "what is
            # national insurance" stays out of it (bare "national insurance" is not in the group)
            # because that line already has its own answer in money.py.
            "years of national insurance", "national insurance contributions",
            "ni contributions", "years of ni", "national insurance so far",
            # "how many years until i can retire" is the age question in other words, and it
            # reached the honest pass: the bare "years until" would take a mortgage question too,
            # so only the retirement wording is here.
            "until i retire", "until i can retire", "until retirement",
            "how long until i retire", "years until i retire",
            "stop working", "stopping working"),
           ("when", "how old", "what age", "how much", "how long", "how many years",
            "do i get", "qualify", "check",
            "forecast", "how many", "get", "am i", "will i", "can i", "should i", "want",
            "what happens", "what")),
          # the two questions are "when" and "how much", so both get their figure rather than a
          # pointer to one: an answer that only says "check gov.uk" is the question restated
          _state_pension,
          # a workplace pension, a contribution and opting out are the money.py entries; a
          # choice between saving and paying off debt is not a question about the state pension
          # either; and the private-pension lines - money in, money out early, the tax-free lump
          # sum - now have their own answer in money.py and must not be taken back by this one
          avoid=("workplace", "opt out", "opting out", "contribution", "contribute",
                 "contributing", "pay in", "put in", "paying in", "auto enrolment",
                 "auto-enrolment", "scheme", "should i pay", "join", "put it in", "or save",
                 "save it", "pension or", "put away", "invest", "worth", "debt", "pay off",
                 "pay it off", "save or", "overdraft", "loan", "tax free", "tax-free",
                 "lump sum", "25%", "take my pension", "take it early", "take my pot", "pot",
                 "draw down", "drawdown", "private pension", "personal pension", "sipp",
                 # "how can i retire early" is the bridging question in money.py, which works out
                 # the years between the date they want and the date each pot opens. The state
                 # pension's age is not the answer to it, and the bare "retire early" key made
                 # this entry take the line and hand back the age.
                 "how can i retire", "how do i retire", "how can i retire early",
                 "retire early", "retiring early"),
          # "my oven has stopped working" carries "stop working", which is the phrase for somebody
          # stopping work, and this card then told a person with a dead oven when the state pension
          # starts. A machine that stopped is the plug and the fuse; the guard keeps this entry for
          # the lines where what stopped is the person's own working life.
          guard=lambda understood: not a_thing_has_stopped(understood)),
]
