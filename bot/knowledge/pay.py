"""The words on a payslip: gross, net, take home, PAYE, and the student loan.

Two numbers sit at the top of a payslip and most of what people ask about pay is the
difference between them. "What is net pay" had a card; "what is gross pay", "is gross before
tax", "does gross include tax", "gross vs net", "what does take home mean", "salary before
tax", "does paye come out of my pay" and "does student loan come out of my wages" did not -
they met a shrug, the duty-free allowance, the income-tax rates, or "that is an order to work
out, not a taste to pick".

So the three questions are keyed on what the line is about rather than on the phrase the
knowledge base happened to have:

- `gross-and-net`, keyed on the two words people use and the pay they are about, so one row
  answers every wording, and the reply leads with the half of the pair that was asked about.
- `paye-taken-from-pay`, because an acronym asked about as a deduction from pay is the same
  question as the acronym asked by name, and the name row only answers the name.
- `student-loan-taken-from-pay`, for the same reason: the money row answers whether it is
  worth paying off early, which is a different question from what comes off this month.

The avoid lists are what keeps them narrow: "this soup is gross", "gross misconduct", "net
worth", "net weight", "net zero", a fishing net and a netball are not pay, and "income tax",
"tax code", "how much tax on 30k", "minimum wage" and "a week" each have their own answer.
"""

from .lookup import entry



# The two numbers on a payslip, as words. Gross is before anything is taken, net is what lands in
# the bank, and "take home" is how most people say net. The phrases are here so a line that uses
# the phrase ("take home pay", "net of tax") matches whichever half of the pair it names, and the
# bare words are what the guard and the reply read.
_GROSS_WORDS = ("gross", "gross pay", "gross salary", "gross income", "gross wage",
                "gross wages", "gross earnings", "before tax", "pre tax", "pre-tax", "pretax",
                "before deductions", "before its taxed", "before it is taxed")
# "does the salary include tax" and "does the offer include tax" name neither word of the pair:
# the pay the line is about is the salary, the wage, the money on the offer. These are the words
# for a pay figure somebody has been quoted, and they only reach this row when the line also asks
# whether tax is in it (see the second group of the key), so "how much tax on my salary" keeps the
# income-tax row.
_QUOTED_PAY_WORDS = ("salary", "salaries", "wage", "wages", "pay", "income", "earnings",
                     "pay packet", "the offer", "the advert", "the job advert", "the money",
                     "20k", "25k", "30k", "35k", "40k", "45k", "50k", "60k", "20,000", "25,000",
                     "30,000", "35,000", "40,000", "50,000")
_NET_WORDS = ("net", "net pay", "net salary", "net income", "net wage", "net wages",
              "net earnings", "net of tax", "net of tax pay", "after tax", "after-tax",
              "after deductions", "take home", "take-home", "takehome", "take home pay",
              "take-home pay", "takehome pay", "what lands in the bank", "in my hand",
              "in my pocket")
_PAY_WORDS = ("pay", "paid", "salary", "salaries", "wage", "wages", "income", "earnings",
              "pay packet", "paypacket", "payslip", "pay slip", "monthly pay", "weekly pay",
              "hourly pay", "my gross", "my net", "the gross", "the net", "a gross", "a net",
              "take home", "take-home", "takehome")
# The question the line is asking of the pair, in the order the reply answers it.
_GROSS_AND_NET_COMPARED = ("difference", "different", "vs", "versus", "or", "between",
                           "compare", "compared", "which is", "same", "higher", "bigger",
                           "more than", "less than")
_GROSS_AND_NET_INCLUDES = ("include", "includes", "included", "quoted", "advertised", "advert",
                           "offer", "offered", "the number on the advert", "the figure")

_GROSS_AND_NET_THREE = (
    "Gross is what you earned before anything is taken, net (or take-home) is what lands in the "
    "bank, and the difference is income tax, National Insurance and any pension you pay in. A pay "
    "figure is always quoted gross unless it says take-home, so a job advertised at £30,000 is "
    "about £2,000 a month in your hand on a standard code, and less if you pay into a pension. "
    "Check the tax code against your HMRC coding notice (1257L is the standard one): a wrong code "
    "is the usual reason a wage comes out short.")
_GROSS_AND_NET_GROSS = (
    "Gross is your pay before anything is taken out of it: the number in the job advert, on the "
    "contract and at the top of the payslip, before income tax, National Insurance and pension. "
    "What actually lands in your bank is net, or take-home, and the gap between them is those "
    "deductions - about a fifth of it on an ordinary wage. So a salary quoted at £30,000 is gross "
    "unless it says take-home.")
_GROSS_AND_NET_NET = (
    "Net, or take-home, is what lands in your bank after income tax, National Insurance and any "
    "pension have come off. Gross is the number before those - the one in the advert and on the "
    "contract - so the two differ by the deductions on the payslip. If the net figure is less than "
    "you expected, check the tax code first: a wrong one is the commonest reason.")
_GROSS_AND_NET_INCLUDES_REPLY = (
    "No: a quoted salary or wage is gross, before tax, unless the advert or the offer says "
    "take-home. So £30,000 a year is about £2,000 a month after income tax and National Insurance "
    "on a standard code, and less if you pay into a pension. Ask for the figure in writing and "
    "check whether a pension is included, because that changes what you actually get.")


def _about_pay(understood):
    """Gross or net is about pay: a bare "gross" is also the word for disgusting.

    A pay word, "net", "take home", or the tax the pair is always about is what makes the line a
    payslip question. "this is gross", "gross misconduct" and "gross negligence" have none of
    them and are left where they were.
    """
    text = " %s " % " ".join(str((understood or {}).get("clean")
                                 or (understood or {}).get("text") or "").lower().split())
    says_gross = any(" %s " % word in text for word in _GROSS_WORDS)
    says_net = any(" %s " % word in text for word in _NET_WORDS)
    if any(ch.isdigit() for ch in text) and not any(
            " %s " % word in text for word in ("include", "includes", "included", "include tax",
                                               "includes tax", "tax included", "before or after",
                                               "after or before")):
        # A number in the line is a figure to work from - "i take home 2100", "i earn 2400 take
        # home", "rents 850 and i take home 2100" - and a definition does not do the sums: the
        # line is a budget or a rate question and belongs to the row that has one. The exception
        # is the figure whose meaning is being asked: "is 30k before or after tax" and "does the
        # 30k include tax" are the pair question with a number attached.
        return False
    if says_gross and says_net:
        # the two words together are the question: "gross vs net" needs no other word to be one
        return True
    if says_gross or says_net:
        return any(" %s " % word in text for word in _PAY_WORDS) or any(
            " %s " % word in text for word in ("tax", "taxed"))
    # Neither word of the pair: the pay is named on its own, so the line has to be asking whether
    # tax is in that figure - "does the salary include tax" - or "the advert doesnt mention the
    # pay" would come here for a definition instead of the asking-for-a-range answer.
    if not any(" %s " % word in text for word in _QUOTED_PAY_WORDS):
        return False
    if not any(" %s " % word in text for word in ("tax", "taxed")):
        return False
    return any(" %s " % word in text for word in ("include", "includes", "included", "taxed",
                                                  "before", "after", "quoted", "advertised"))


def _gross_or_net(memory, understood):
    """The half of the pair the line asked about, or the two together."""
    text = " %s " % " ".join(str((understood or {}).get("clean")
                                 or (understood or {}).get("text") or "").lower().split())
    says_gross = any(" %s " % word in text for word in ("gross", "gross pay", "gross salary",
                                                        "gross income", "before tax", "pre tax",
                                                        "pre-tax", "pretax"))
    says_net = any(" %s " % word in text for word in ("net", "net pay", "net income", "after tax",
                                                      "take home", "take-home", "takehome",
                                                      "take home pay", "net of tax"))
    if says_gross and says_net:
        return _GROSS_AND_NET_THREE
    if (" before or after " in text or " after or before " in text
            or " gross or net " in text or " net or gross " in text):
        # "is 30k before or after tax" is the comparison, whichever half came first
        return _GROSS_AND_NET_THREE
    if any(" %s " % word in text for word in _GROSS_AND_NET_COMPARED) and says_gross:
        return _GROSS_AND_NET_THREE
    if any(" %s " % word in text for word in _GROSS_AND_NET_INCLUDES):
        return _GROSS_AND_NET_INCLUDES_REPLY
    if says_net:
        return _GROSS_AND_NET_NET
    if says_gross:
        return _GROSS_AND_NET_GROSS
    # The guard has already said the line is about the pair, so there is always an answer: the
    # two together is the safe one when neither word is spelled out ("is the salary after tax").
    return _GROSS_AND_NET_THREE


ENTRIES = [
    # Gross and net are two words for the two lines of a payslip, and they are asked about as
    # words far more often than as a payslip: "what is gross pay", "is gross before tax",
    # "does gross include tax", "what does take home mean", "what is net of tax", "gross vs net",
    # "what is net income", "salary before tax". Whichever way it was put, the question is the
    # same - which of the two numbers is which - and on main nine of those were a shrug, the
    # duty-free allowance ("what does take home mean"), the income-tax rates, or "that is an order
    # to work out, not a taste to pick: the messy step before the tidy one". So the row is keyed
    # on the two words and the pay they are about, not on the phrase "net pay", and the reply
    # leads with the half of the pair the line asked about.
    entry("gross-and-net",
          (_GROSS_WORDS + _NET_WORDS + _QUOTED_PAY_WORDS,
           _PAY_WORDS + ("what is", "whats", "what does", "mean", "means", "meaning",
                         "difference", "different", "vs", "versus", "or", "between",
                         "include", "includes", "included", "quoted", "advertised", "advert",
                         "salary", "offer", "compare", "compared", "explain", "which",
                         # "is gross before tax" says neither a pay word nor a question word:
                         # the two words of the pair are the whole of it, so "is" and "does"
                         # count here and the guard is what keeps "this is gross" out
                         "is", "are", "was", "does", "do", "did",
                         # the shape of "does the salary include tax"
                         "include tax", "includes tax", "tax included", "tax on it")),
          _gross_or_net,
          bias=2,
          # "this is gross", "gross misconduct" and "gross negligence" are not pay, and a bare
          # "gross" with nothing about pay beside it is left where it was: the row only stands up
          # when a pay word, "take home" or "net" is in the line with it
          guard=_about_pay,
          avoid=("misconduct", "negligence", "grossly", "grossed out", "gross me out",
                 "gross out", "disgusting", "net worth", "net weight", "gross weight",
                 "drained weight", "net zero", "safety net", "fishing", "netball", "net profit",
                 "net margin", "net asset", "turnover", "butterfly net", "tennis net",
                 "keep net", "net curtains", "moss", "internet", "netflix",
                 # the tax on a salary is the income-tax row, and the pay figures people ask
                 # about in the abstract are the averages row: what is left here is the pair
                 "income tax", "tax code", "tax return", "tax year", "national insurance",
                 "salary sacrifice", "how much tax", "tax on", "tax bracket", "tax bill",
                 "self assessment", "underpaid", "overpaid", "emergency tax", "average salary",
                 "average wage", "median", "minimum wage", "living wage", "payslip",
                 # a rate asked as another rate is a sum - "i get 2400 a month before tax what is
                 # that a week" - not a definition of the pair, and this row does not do sums
                 "a week", "a month", "an hour", "a day", "per week", "per month", "per hour",
                 "what is that a week", "what is that a month")),

    # An acronym asked about as a line on the pay packet. The name rows answer "what is paye";
    # this one answers "does it come out of my wages", which is the question people actually
    # type, and it holds the one thing worth checking - the tax code - without turning into an
    # essay about income tax, which has its own row.
    entry("paye-taken-from-pay",
          (("paye", "paye tax", "pay as you earn"),
           ("come out", "comes out", "comes off", "taken off", "taken out", "taken from",
            "taken from my pay", "deducted", "deducted from", "deduction", "deductions",
            "out of my pay", "off my pay", "out of my wages", "off my wages", "from my pay",
            "out of my salary", "off my salary", "on my payslip", "stop", "stops", "stopped",
            # "do i pay paye" names the letters and asks whether it is taken, with no "comes"
            "pay paye", "paid paye", "do i pay", "am i paying", "paye taken")),
          "Yes: PAYE is the income tax your employer takes out of your pay before it reaches "
          "you, worked out from your tax code each payday and shown on the payslip, so the "
          "number you are paid is already after it. National Insurance comes off the same way, "
          "and a pension or a student loan is listed as its own line. Compare the code on your "
          "payslip with your HMRC coding notice (1257L is the standard one): a wrong code is the "
          "usual reason PAYE takes too much.",
          # a wrong or high figure is the payslip check, and the rates, the return and the
          # self-employed version are their own answers
          avoid=("tax code", "wrong", "too much", "too high", "overpaid", "underpaid", "refund",
                 "rebate", "emergency tax", "tax return", "self assessment", "how much tax",
                 "national insurance", "p60", "p45", "self employed", "cis", "what is paye",
                 "what does paye", "mean", "explain"),
          bias=1),

    # The money row answers "should i pay it off early" and "how much do i repay"; this one is
    # the line on the payslip this month, which the same words do not reach.
    entry("student-loan-taken-from-pay",
          (("student loan", "student loans", "student debt", "student loan repayment",
            "student loan repayments"),
           ("come out", "comes out", "comes off", "taken off", "taken out", "deducted",
            "deduction", "deductions", "out of my pay", "off my pay", "out of my wages",
            "off my wages", "from my pay", "out of my salary", "off my salary", "on my payslip",
            "stop", "stops", "stopped", "pay student loan", "paid student loan",
            "do i pay", "am i paying")),
          "Yes: a student loan comes off your pay like tax, through PAYE, once you earn over the "
          "threshold for your plan - on plan 5 that is 9% of what you earn above about £25,000 a "
          "year (£2,082 a month), shown as its own line on the payslip. Only the part above the "
          "threshold counts, so a low month takes nothing, and it stops by itself when the loan "
          "is paid off. If the figure looks wrong, ask payroll for the plan they have you on: "
          "the wrong plan is the usual cause.",
          # paying it off early, overpaying, writing it off and what the loan is are the money
          # row's questions, and the repayment threshold by plan is their own answer
          avoid=("how much", "how much is", "pay off", "pay it back", "pay back",
                 "repay early", "overpay", "overpayment",
                 "worth", "settle", "write off", "written off", "forgiven", "cancel", "plan 1",
                 "plan 2", "plan 4", "threshold", "what is a student loan", "interest rate"),
          bias=1),
]

ANSWERS = ("money",)
