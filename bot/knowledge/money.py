"""Money: saving, borrowing, bills, housing and tax, in everyday plain advice.

The answers lane owns this domain. One Entry per question people really ask ("how do I
save on a small salary", "should I overpay the mortgage", "what is a standing charge"),
keyed by the money thing and what they want to know about it, not by wording. The advice is
the ordinary, careful version: the first thing to check, what usually helps, and when the
right answer is "get free advice" (StepChange, Citizens Advice) rather than a guess.
"""
import datetime
import math
import re

from ..compose.repair import owns_the_deed
from ..memory import history
from ..memory.facts import extract
from .consumer import _a_hotel_room_or_no_home
from .cooking import _crowd
from .geography import _countries_said
from .lifeadmin import _tipping
from .prices import a_price_is_judged
from .lookup import entry
from .technology import APP_ACCOUNT_WORDS, PAID_SERVICES

# "what is a survey" asks what the thing is and "do i need a survey" asks whether to have one.
# The row answered both with "Yes, have one done -", which is not an answer to the definition.
_SURVEY_ADVICE = (
    "Yes, have one done - the lender's valuation is not a survey, and it only tells the lender the "
    "house is worth what it is lending. A RICS level 2 homebuyer report is about £400 to £700 and "
    "a level 3 building survey £600 to £1,500, which is the one for an old or unusual house; "
    "level 1 is around £300 to £500 and is the basics only. Read the report for the things it "
    "says to get checked by a specialist, and get quotes for those before you exchange, because "
    "that is when you can still renegotiate."
)
_THE_SURVEY_ITSELF = (
    "A house survey is a surveyor's inspection of the structure of the house you are buying, and "
    "it comes in levels: a level 1 condition report is the basics only (about £300 to £500), a "
    "level 2 HomeBuyer report is the usual one for a modern house in reasonable order (£400 to "
    "£700), and a level 3 building survey is the one for an old, unusual or visibly tired house "
    "(£600 to £1,500). It looks at the roof, walls, damp, drains and electrics rather than the "
    "decoration, and it is not the mortgage lender's valuation."
)
_WHAT_IT_IS = re.compile(
    r"\b(?:what is|what's|whats|what does|what do|define|definition of|meaning of)\b"
    r"[^.?!]{0,30}\b(?:survey|surveyor|homebuyer|home buyer|report)\b", re.I)
# "which survey should i get" and "how much does a level 3 survey cost" ask about the thing,
# not whether to have one: the levels and their prices are the answer, and the advice opens
# with "Yes, have one done -" because it was written for the whether question.
_WHICH_OR_HOW_MUCH = re.compile(
    # not "difference": "do we have to find the difference ourselves" is about the money after a
    # low valuation, which is the advice, not the levels.
    r"\b(?:which|how much|how many|what level|what sort|what kind|cost|costs|price|"
    r"prices|cheapest)\b", re.I)


def _the_survey(memory, understood):
    """The levels when the line asks what or which or how much, the advice when it asks whether."""
    clean = " ".join(str((understood or {}).get("clean") or "").lower().split())
    if _WHAT_IT_IS.search(clean) or _WHICH_OR_HOW_MUCH.search(clean):
        return _THE_SURVEY_ITSELF
    return _SURVEY_ADVICE



# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("money",)


# "Take home" is the wage as soon as the line is asking about the money, and a border allowance
# when the line names something to carry or says customs at all. The two hats are held in two
# domains - this row and travel's duty-free table - so each asks the same question before it
# answers, and the question is written here once.
_SOMETHING_TO_CARRY = re.compile(
    r"\b(?:wine|wines|beer|beers|spirits|whisky|whiskey|vodka|gin|rum|alcohol|cigarettes?|"
    r"cigs?|tobacco|baccy|perfume|gifts?|presents?|souvenirs?|duty[- ]free|customs|allowances?|"
    r"declare|declaring|declared|border|airport|abroad|overseas|france|spain|portugal|greece|"
    r"italy|ireland|germany|holland|belgium)\b", re.I)


# The ask that makes "take home" the word itself rather than a figure to work out: "what does take
# home mean" is this row's, and "how much more will i take home if i get a rise" is the tax row's.
_ASKS_WHAT_THE_WORD_MEANS = re.compile(
    r"\b(?:take|bring)\s+home\s+(?:mean|means|meaning|definition)\b"
    r"|\bwhat\s+(?:does|do|is|are)\s+(?:that\s+|it\s+)?(?:mean\s+for\s+)?(?:my\s+|the\s+|a\s+)?"
    r"(?:take|bring)\s+home\b"
    r"|\b(?:explain|define|meaning\s+of)\s+(?:the\s+|my\s+|a\s+)?(?:take|bring)\s+home\b", re.I)


def _not_a_customs_line(understood):
    """Keep the pay rows off the allowance question, which wears the same words.

    "how much wine can i take home from france" reaches this row on "take home" and "how", and the
    answer it wants is the customs table in travel.py, so a line that names a thing to carry or a
    customs word is not this row's. The same key is a figure to work out in most other lines -
    "how much more will i take home if i get a rise" is the tax bands' question - so the money
    words carry this row only when the line is asking what the phrase means, or names a payslip.
    """
    text = understood.get("clean") or ""
    if _SOMETHING_TO_CARRY.search(text):
        return False
    if re.search(r"\bpayslips?\b|\bpay\s+slips?\b|\bnet\s+pay\b", text, re.I):
        return True
    return bool(_ASKS_WHAT_THE_WORD_MEANS.search(text))


def _a_first_meeting(text, understood):
    """True when the line is someone introducing themselves, so the welcome is the reply.

    `hi im jess, im saving for a car` says two things: who they are, and what they are saving
    for. The plan is a good one and the welcome is the answer ("Hi Jess - good to meet you, and
    saving for a car sounds like a good one"), so this entry stands aside rather than opening
    with a lecture on standing orders. It stands aside only for a plan, never for a question in
    the same line: `hi im jess, how do i save for a car` still gets the saving answer, because
    that is what was asked. The name comes from the memory owner's own reader, so there is no
    second one to disagree with it.
    """
    if (understood or {}).get("kind") == "question":
        return False
    return bool(extract(text).get("name"))


# Income tax and National Insurance are arithmetic, not opinion: the same few bands answer every
# "what do i take home on X" line, so the reply is worked out from the salary the person typed
# rather than written out for one figure.
# A manners question about a split asks for a view, not a method. Two rows in this file answer a
# split with a method - `split-house` (how a household divides the bills) and `money-and-partner`
# (how a couple shares money) - and both keys are a split verb with a money word, which fits a
# table's bill just as well: "is it rude to split the bill" was answered "split rent by room if
# the rooms differ", and "is it polite to split the bill" with the joint-account advice.
#
# Neither word that the person reached for is the signal, so neither a list of adjectives nor a
# list of phrases is the rule: a phrase list written for "rude to split" also catches "is it rude
# to split the rent", and an adjective list only ever holds the wordings somebody happened to
# type. The rule is the *shape* of the question - a judgement word on a split that names a
# table's bill - with a home word in the line keeping the household rows whatever else it says.
_A_JUDGEMENT_WORD = re.compile(
    r"\b(?:rude|ruder|politest|polite|impolite|cheeky|stingy|tight|mean|weird|strange|normal"
    r"|ok|okay|acceptable|unacceptable|awkward|etiquette|manners|bad\s+form|selfish|generous"
    r"|expected|allowed|supposed|better|worse"
    # the two ordinary ones the list did not hold: "is it fine to split the bill" and "is it
    # wrong to split the bill" are the same question as "is it rude ...", and both were answered
    # with the couple's income split. A judgement word list is only as good as its commonest
    # members, and fine and wrong are two of those.
    r"|fine|wrong|right|fair|off|uncool|childish|petty|stingey)\b")
_A_TABLE_WORD = re.compile(
    r"\b(?:bill|bills|tab|tabs|check|cheque|cost|costs|halves|half|dinner|lunch|meal|meals"
    r"|restaurant|drinks|round|takeaway|takeout|coffee)\b")
# A home's bills are a standing arrangement, so the household rows keep every line that names one:
# the rent, the flat, and the named standing bills (water, energy, broadband) which are a
# household's even when they never say "household".
_HOME_IN_THE_LINE = re.compile(
    r"\b(?:rent|flats?|house|houses|housemate|housemates|flatmate|flatmates|roommate|roommates"
    r"|household|landlord|tenancy|mortgage|deposit|council\s+tax|service\s+charge"
    r"|utilit(?:y|ies)|water|gas|electric|electricity|energy|heating|broadband|wifi|internet"
    r"|tv\s+licen[cs]e|standing\s+order|moving\s+in|bills?\s+between\s+us)\b")


def _a_manners_question_not_a_home_split(understood):
    """True when the line asks whether splitting a table's bill is rude, and names no home."""
    text = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if not text:
        text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if _HOME_IN_THE_LINE.search(text):
        return False
    return bool(_A_JUDGEMENT_WORD.search(text) and _A_TABLE_WORD.search(text))


_PERSONAL_ALLOWANCE = 12570
_BASIC_BAND = 37700          # of taxable income, so the basic rate runs to 50270 a year
_TAX_BANDS = ((_BASIC_BAND, 0.20), (125140 - _PERSONAL_ALLOWANCE - _BASIC_BAND, 0.40))
_TAX_TOP = 0.45
_NI_MAIN_TO = 50270
_SALARY_NUMBER = re.compile(r"£?\s*(\d[\d,]*(?:\.\d+)?)\s*(k\b|grand\b|thousand\b)?", re.I)


def _salary_in(text):
    """The salary a line names, in pounds, or None when it names none.

    "30k" and "30 grand" are 30,000 and "£30,000" is thirty thousand; a bare small number is
    a percentage, an hour's pay or a month, so it is not a salary and the answer falls back to
    the bands."""
    best = None
    for match in _SALARY_NUMBER.finditer(text):
        raw = match.group(1).replace(",", "")
        try:
            value = float(raw)
        except ValueError:
            continue
        if match.group(2):
            value *= 1000
        elif value < 3000:
            continue
        if value >= 1000 and (best is None or value > best):
            best = value
    return int(best) if best else None


def _income_tax_and_ni(income):
    """(income tax, National Insurance) on a salary for one person, England and Wales."""
    allowance = _PERSONAL_ALLOWANCE
    if income > 100000:
        allowance = max(0.0, allowance - (income - 100000) / 2.0)
    taxable = max(0.0, income - allowance)
    tax, left = 0.0, taxable
    for width, rate in _TAX_BANDS:
        part = min(left, width)
        tax += part * rate
        left -= part
        if left <= 0:
            break
    if left > 0:
        tax += left * _TAX_TOP
    ni = 0.0
    if income > _PERSONAL_ALLOWANCE:
        ni += (min(income, _NI_MAIN_TO) - _PERSONAL_ALLOWANCE) * 0.08
    if income > _NI_MAIN_TO:
        ni += (income - _NI_MAIN_TO) * 0.02
    return tax, ni


# The pay a line introduces as its own. The reading is the one "i earn 1200 a month" already goes
# through, so a price is a price: "my car cost 20000" and "i paid 250k for our flat" are not what
# anybody is paid. A household's pay said as somebody else's - "my husband earns 40000" - is not
# the person's own salary either, so the figure has to be theirs by the words in front of it.
_MY_PAY = re.compile(
    r"\b(?:i|we)(?:'m|m|'re|re|'ve|ve)?\s+(?:earn|earns|make|makes|get|gets|take|bring|on|am)\b"
    r"|\b(?:my|our)\s+(?:salary|wage|wages|pay|income)\b", re.I)


def _a_salary_they_said_before(memory):
    """The salary an earlier line gave as their own pay, or 0.

    "i earn 32000" then "how much tax do i pay" was answered "Tell me the salary and I'll work out
    the take-home" - the salary was in the chat, one line up, and the ask was read as a line typed
    on its own. A question about a figure is the same question whenever it is asked, so the pay
    the chat already holds answers it; the newest one wins, because that is the one they stand by.
    """
    for line in reversed(history.the_lines_before(memory, look_back=8)):
        low = line.lower()
        if not _MY_PAY.search(low):
            continue
        if not any(_is_income(low, match) for match in _SALARY_NUMBER.finditer(low)):
            continue
        income = _salary_in(low)
        if income:
            return income
    return 0


def _take_home(memory, understood):
    """What a salary leaves in the bank, band by band."""
    reading = understood or {}
    text = str(reading.get("clean") or reading.get("text") or "").lower()
    income = _salary_in(text)
    if not income:
        income = _a_salary_they_said_before(memory)
    if not income:
        return ("Income tax starts above £12,570 a year: 20 per cent of it up to £50,270, then 40 "
                "per cent, and National Insurance is 8 per cent above £12,570. Tell me the salary "
                "and I'll work out the take-home.")
    tax, ni = _income_tax_and_ni(income)
    take = income - tax - ni
    bands = ("That is the first £12,570 tax free, 20 per cent of the next £37,700"
             if take > 0 and income <= 50270 else
             "That is the first £12,570 tax free, 20 per cent up to £50,270 and 40 per cent above it")
    return ("On £{:,} a year you pay about £{:,.0f} income tax and £{:,.0f} National Insurance, so "
            "you take home roughly £{:,.0f} a month.".format(income, tax, ni, take / 12.0) + " " +
            bands + ", and National Insurance at 8 per cent on pay above £12,570.")
# A body complaint with a length in it - "ive been feeling dizzy for a week should i worry" -
# carries the words this file answers period questions with ("a week", "should", "how much"), and
# the subject is the person's health, not their money: the entries that turn on a period or on a
# sum to put by skip a line that names a symptom or a symptom's kind of question. The health
# modules answer it, and a money answer to a dizzy spell is worse than no answer at all.
# "sick", "tired" and "ill" are left out on purpose: "im sick of being broke" and "im tired of
# paying rent" are money lines, and the guard is here for the body, not for a figure of speech.
_BODY = ("dizzy", "dizziness", "lightheaded", "light headed", "nausea", "nauseous", "vomit",
         "vomiting", "throwing up", "symptom", "symptoms", "cough", "coughing", "sore",
         "soreness", "ache", "aches", "aching", "pain", "pains", "lump", "rash", "bleeding",
         "bleed", "breathless", "fever", "temperature", "headache", "headaches", "migraine",
         "infection", "swollen", "swelling", "cramp", "cramps", "diarrhoea", "constipated",
         "pharmacist", "pharmacy", "doctor", "gp", "hospital", "a&e", "nhs", "111",
         "should i worry", "worth worrying")


_A_THE_HOUSEHOLD = re.compile(r"\bfamily\b|\bcouple\b|"
                              r"\b(?:for|feed(?:ing)?|between)\s+(?:two|three|four|five|six|"
                              r"seven|eight|\d+)\b|"
                              r"\btwo of us\b|\bthe kids\b|\bwe (?:are|'re) a\b|"
                              r"\bhousehold\b|\bpartner\b|\bhusband\b|\bwife\b|"
                              r"\b(?:feed|feeding) us\b")


def _a_week_asked(text):
    """A week named in the line, in the shapes people name it."""
    return bool(re.search(r"\b(?:per|a|each|every)\s+week\b|\bweekly\b|\bin a week\b|"
                          r"\ba week\b|\bweek for food\b", text))


def _a_month_asked(text):
    """A month named in the line, in the shapes people name it."""
    return bool(re.search(r"\b(?:per|a|each|every)\s+month\b|\bmonthly\b|\ba month\b|"
                          r"\bin a month\b", text))


def _food_bill(memory, understood):
    """A cost question gets the going rate first; a saving question gets the plan.

    "how much does a week of food cost for one person" was answered with the cheap week of a
    household that had run short, and "how much should i budget for food" with how to save on a
    shop: both asked for a number. A day, a week and a month each get their own figure, and the
    plan is the answer to "how do i spend less", which is a different question.
    """
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if _ASKS_THE_PRICE.search(text) and _a_month_asked(text):
        if _A_THE_HOUSEHOLD.search(text):
            return ("A couple or a small family spends about 300 to 400 pounds a month on food "
                    "shopping, and about 450 to 550 with lunches and takeaways in it. Frozen veg, "
                    "tinned pulses and own-brand staples are where the month comes down.")
        return ("A single adult spends about 130 to 195 pounds a month on food cooked at home, "
                "so 30 to 45 a week, and about 215 to 300 a month once lunches and a takeaway "
                "are in it.")
    if re.search(r"\b(?:per|a|each|every)\s+day\b|\bdaily\b", text):
        return ("Budget about 10 to 15 pounds a day per person if you cook for yourself and 25 to "
                "35 eating out or taking away, so a week self-catering lands near 70 to 100 "
                "pounds a head.")
    if _a_week_asked(text) and not re.search(r"\bhow do i\b|\bhow can i\b|\bhow to\b", text):
        if _A_THE_HOUSEHOLD.search(text):
            return ("A couple or a family of four spends about 70 to 80 pounds a week on food "
                    "shopping, from about 55 for two cooking from scratch, and about 100 to 130 "
                    "once lunches and a takeaway are in it. A list once a week is what keeps it "
                    "there.")
        return ("A single adult spends about 30 to 45 pounds a week on food cooked at home, and "
                "about 50 to 70 with lunches and a takeaway. A list once a week and two meat-free "
                "dinners is the quickest way to land at the bottom of that.")
    if _ASKS_THE_PRICE.search(text):
        # no period named, but the ask is a figure: the week is the one people mean, so it is
        # given as the going rate and the assumption is said out loud.
        if _A_THE_HOUSEHOLD.search(text):
            return ("A couple or a family of four spends about 70 to 80 pounds a week on food "
                    "shopping, from about 55 for two cooking from scratch, and about 100 to 130 "
                    "once lunches and a takeaway are in it. A list once a week is what keeps it "
                    "there.")
        return ("A single adult spends about 30 to 45 pounds a week on food cooked at home, so "
                "130 to 195 pounds a month. Add about 20 a week if lunches and a takeaway are in "
                "it, and a written list once a week is what keeps the shop at the bottom end.")
    return ("Plan the week around what's already in the cupboard, shop with a list once a week, "
            "and buy own-brand staples (pasta, rice, tins, oats, frozen veg) where the difference "
            "is invisible. Cutting meat to two or three dinners a week is the biggest single "
            "saving for most households.")


def _habit_plan(memory, understood):
    """The habit answer has to lead with the thing the person named.

    "How do i stop buying coffee" was opening with a planned takeaway night, which is the same
    mismatch this entry exists to remove one level up. A coffee or a bought lunch gets the flask
    first; anything else gets the planned night.
    """
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    night = ("Keep one planned night a week for a takeaway and put the money aside for it, so the "
             "rest of the week has nothing to decide.")
    flask = ("Take a flask and a packed lunch in your bag the night before, so the shop stop or the "
             "lunch queue has nothing to decide.")
    rule = ("Put a 24-hour rule on the apps: take the saved card off, so ordering takes effort.")
    week = "A normal week measured first is what makes the total real."
    if re.search(r"\bcoffee|\bcoffees\b|\blunch(es)?\b|\bbrew\b|\bsandwich", text):
        return " ".join((flask, rule, week))
    return " ".join((night, rule, "For the shop coffee, a flask and a packed lunch in your bag the "
                                  "night before does the same job, and " + week[0].lower() + week[1:]))

def _isa(memory, understood):
    """A "how much can i put in" question gets the cap first; a "what is it" gets the wrapper.

    Both answers are short and lead with the thing that was asked, because the ISA is easy to
    explain at length and the length buries the one fact the person wanted.
    """
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    # "can i have more than one isa", "how many isas can i open": the count is not the limit, the
    # shared allowance is, and that is the half people are really asking about.
    if re.search(r"\bhow many isas\b|\bmore than one isa\b|\btwo isas\b|\bseveral isas\b|"
                 r"\banother isa\b|\ba second isa\b|\bopen a second\b|"
                 # two products named in one line ("a cash isa and a stocks and shares isa") is the
                 # same question: can I hold both, and does each get its own allowance
                 r"\bcash isa and\b|\bisa and a\b|\bboth\b|\bsame year\b", text):
        return ("As many as you like: there is no limit on the number of ISAs you hold, only on what "
                "goes into them - £20,000 a year across all of them together in 2025-26. In one "
                "tax year you can pay into one cash ISA and one stocks and shares ISA (plus a "
                "lifetime ISA), and money you move from one provider to another does not use any "
                "allowance at all. So a second account is fine; the shared £20,000 is the number to "
                "watch.")
    if re.search(r"\b(?:allowance|limit|how much|put in|pay in|pay into|a year|per year|reset)\b",
                 text):
        return ("You can pay in up to £20,000 a year across your ISAs in 2025-26, and the "
                "allowance resets each April - check gov.uk for the current figure before you rely "
                "on it. Inside the ISA the interest and growth are not taxed, so a cash ISA only "
                "beats an ordinary savings account if it pays a better rate.")
    if re.search(r"\blifetime isa\b|\blisa\b", text):
        return ("A Lifetime ISA pays a 25% bonus on what you put in - up to £1,000 a year on "
                "£4,000 - and the interest and growth are not taxed. It is only worth it if "
                "the money is for a first home under £450,000, or kept until you are 60; take "
                "it out before then for anything else and you lose the bonus and pay a 25% charge, "
                "so money you might need sooner belongs in a plain ISA or a savings account.")
    # "how do i open an isa" is the paperwork question, not the worth-it one
    if re.search(r"\bopen\b|\bget (?:an|a) isa\b|\bhow do i start\b|\bset up\b", text) and \
            not re.search(r"\bshould\b|\bworth\b|\bbetter\b|\bor\b", text):
        return ("Apply online with a bank, building society or investment platform: you need your "
                "national insurance number, your date of birth and a debit card, and it takes "
                "about ten minutes with the account open the same day. Pick cash if you want it "
                "safe and might need it, stocks and shares if it is for five years or more. To "
                "move an ISA you already have, ask the new provider for a transfer form - never "
                "withdraw it and pay it back in, because that uses up the year's allowance.")
    if re.search(r"\b(?:what|whats|how does|explain|mean|explanation)\b", text) and not re.search(
            r"\b(?:worth|should|better|or)\b", text):
        return ("An ISA is a savings or investment account where the interest and growth are not "
                "taxed. A cash ISA is only worth it if it pays more than an ordinary savings "
                "account, and money you won't touch for five years or more usually grows more in "
                "a stocks and shares ISA; a lifetime ISA adds 25% (up to £1,000 a year) "
                "towards a first home or retirement.")
    # "is a cash isa worth it" and "isa or a savings account" already had a good, direct answer;
    # they keep it word for word, because a definition in front of a comparison buries it.
    return ("A cash ISA is only worth it if it pays more than an ordinary savings account, and "
            "for small amounts the tax-free part barely matters. Money you won't touch for five "
            "years or more usually grows more in a stocks and shares ISA, and a Lifetime ISA adds "
            "25% (up to £1,000 a year) towards a first home or retirement.")

def _over_spending(memory, understood):
    """The money question behind "i spend too much".

    The line names what it is about only sometimes. A takeaway or a coffee has its own row and
    gets there first; a line that names nothing gets the two things that work on any overspend -
    see the month once, then a figure decided in advance instead of an evening's willpower.
    """
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if re.search(r"\bcoffee|\bcoffees\b|\blunch(es)?\b|\btakeaway|\btakeaways\b|"
                 r"\beating out\b|\bdeliveroo\b|\bjust eat\b|\bfast food\b", text):
        return _habit_plan(memory, understood)
    return ("Write down every purchase for a month, or let your banking app sort it into "
            "categories - the surprises are nearly always takeaways, subscriptions and small card "
            "taps. Then decide the figure before the month starts and move it out on payday, "
            "because a number set in advance beats willpower every evening.")


def _late_leg(memory, understood):
    """Who a late or cancelled journey is claimed from: the mode decides it.

    The rail scheme is Delay Repay, and it is only a rail scheme: the same answer was telling
    people to claim it from a bus company and a coach operator, where it does not exist. A flight
    is not this answer either, and the plane words are on this entry's avoid list for it, so the
    travel answer takes those lines.
    """
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    # A sea crossing has its own law, EU 1177/2010, and it is not Delay Repay: standing the rail
    # answer down for "ferry" left the line with a timetable punt, which is no answer at all to a
    # question about compensation.
    if re.search(r"\b(?:ferry|ferries|sea\s+crossing|ferry\s+company|stena|brittany\s+ferries)\b",
                 text):
        return ("A ferry to or from an EU port owes you 25% of the fare if you arrive more than "
                "an hour late and 50% if it is more than two hours, and a cancelled crossing is "
                "your choice of a refund or a rerouting. Ask the operator in writing "
                "within three months and keep the booking and the boarding pass; if they will not "
                "pay, their complaints procedure comes first, then the port authority or a "
                "consumer body.")
    if re.search(r"\b(?:bus|buses|coach|coaches|megabus|national\s+express|stagecoach|"
                 r"arriva|first\s+bus|tram|trams)\b", text):
        return ("Claim it from the bus or coach operator, not a train scheme: they run their own "
                "promise, so send the claim on their website or by post with the ticket, the route "
                "and the time. If a bus did not turn up at all, ask for that fare back and complain "
                "to the local transport authority if they say no; a coach cancelled or over "
                "three hours late is a full refund or a replacement journey, and a missed "
                "connection on one ticket is theirs to sort out.")
    # A ticket nobody used is a refund before it is a delay claim: this answer led with Delay
    # Repay for "i didnt use my train ticket can i get a refund" and "can i get a refund on my
    # train ticket", which is the wrong half of the subject for somebody who never travelled,
    # and travel's `train-refund` - which has the same two halves in the other order - was
    # never reached because this entry's `ask` holds the word "refund".
    if re.search(r"\b(refund|refunds|money back|unused|didn'?t use|didnt use|not use|never used|"
                 r"can'?t go|cant go)\b", text) and not re.search(
                     r"\b(delay|delayed|delays|late|later|missed|cancel+ed|cancel+ation|strike|"
                     r"compensation)\b", text):
        return ("Two different claims, so ask for the right one: a ticket you did not use can be "
                "refunded before travel on most fares, less an admin fee of up to about £10, "
                "though advance tickets are often non-refundable and only changeable. If the "
                "train itself was late or cancelled, that is Delay Repay instead - 15 minutes "
                "late on most operators, claimed on their site within 28 days with the ticket "
                "and the time you arrived.")
    return ("Claim Delay Repay from the train company, not the ticket seller: most pay out for 15 "
            "minutes or more late, and the claim goes in within 28 days on the operator's website "
            "with a photo of the ticket. A season ticket is worked out pro rata, so keep a note of "
            "each delay. If the train was cancelled and you did not travel, you are entitled to a "
            "full refund, and you can claim a refund of the unused part of a flexible ticket at "
            "the ticket office.")


def _car_running_cost(memory, understood):
    """What a car costs to run, with the charging figures when the car is electric."""
    text = (understood or {}).get("clean") or ""
    if any(word in text for word in ("electric", " ev", "ev ", "charged", "charging")):
        return ("Charged at home an electric car is about 3-4p a mile, so £300-£500 a year for "
                "8,000 miles, and public rapid chargers cost three or four times that. Insurance and "
                "tyres are like any other car, servicing is cheaper with no oil or exhaust, and road "
                "tax is £195 now that the exemption has ended.")
    return ("For a small used car, budget about £2,000-£3,000 a year all in: insurance around £500, "
            "fuel £80-£120 a month, road tax from £195, and £400-£600 for MOT, servicing and tyres. "
            "Get an insurance quote before you buy the car, because that one number can decide the "
            "whole budget.")


# "Pay monthly" is a phrase about the car only because a car was named somewhere near it. On its
# own it is a question about an instalment plan - "can i pay monthly" after a council tax rise got
# the car-finance sums ("Buy a three- or four-year-old car with a loan..."), and the same words for
# a gym got the period-exercise card. The row keys "pay monthly" and "monthly", so the two halves
# of its own key satisfied each other and the line never had to say a car. A deal word is the
# other half: a car, a van, a lease, PCP, finance or a loan. The row keeps every line that names
# one ("should i lease or buy a car", "is pcp better than a loan", "can i pay monthly for a new
# car") and stands down for the instalment plan that is about something else.
_A_CAR_OR_A_DEAL = re.compile(
    r"\b(?:car|cars|van|vans|vehicle|vehicles|lease|leases|leased|leasing|pcp|"
    r"contract hire|finance|financed|financing|loan|loans|borrow|outright|dealership|"
    r"garage|motorbike|bike)\b", re.IGNORECASE)


def _a_car_or_a_deal(understood):
    """False when the line asks about paying monthly with no vehicle and no deal in it."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "")
    return bool(_A_CAR_OR_A_DEAL.search(said))


# A rent or a bill named with a figure the person is choosing is a plan, not a debt. On main
# `256b47bd1`, "our rent budget is 900 a month", "we can pay 250 a week rent" and "my budget is
# about 250 a week on rent" were all answered by the arrears card - "tell the landlord in writing
# before the next rent day, and ask the council about a Discretionary Housing Payment" - which is
# advice for somebody who has already missed a payment. "how much rent can we afford on one wage"
# was answered the same way. What decides it is not the word "budget" but whether the line says a
# payment went wrong at all: a figure for a plan has no trouble in it, and every line that says
# the trouble keeps the card.
_A_PAYMENT_GONE_WRONG = re.compile(
    r"\b(?:owe|owes|owed|owing|behind|arrears|arrear|missed|default\w*|late|short"
    r"|cant pay|can't pay|cannot pay|not paid|havent paid|haven't paid|didnt pay|didn't pay"
    r"|cant afford|can't afford|cannot afford|stop paying|stopped paying"
    r"|no money|nothing left|lost my job|lost his job|lost her job|unemployed|redundant"
    r"|struggling|overdrawn|overdraft|debt|debts|notice|evict\w*|bailiff|county court"
    r"|cut off|disconnected|final demand|red letter|worried|scared|frightened)\b")
# Working out what can be paid: a budget, a figure per week or month, or the move it is for.
# A rate is a figure and a period together. The bare words "a week" were enough at first, and on
# a chat that went "i rent, so is it my job or the landlords" -> "i rang them a week ago and nobody
# came" that made a repair nobody turned up for into a figure somebody was working to, so the rent
# question took it and answered a housing-repair line about a third of a take-home pay. Only a
# number with the period after it is a rate; "a week ago" is a time, not a plan.
_A_FIGURE_FOR_A_PLAN = re.compile(
    r"\b(?:budget|budgets|budgeting|up to|can pay|could pay|would pay|how much"
    r"|can we afford|could we afford|can i afford|could i afford"
    r"|\d[\d,.]*\s*(?:pw|pcm|pcw)|pcw|pcm|pw|per week|per month"
    r"|\d[\d,.]*\s*(?:k\b|grand\b|)?\s*(?:a|per|/)\s*(?:week|month|wk|mo)\b"
    r"|(?:a|per)\s*(?:week|month)\s*(?:on rent|rent|for rent|on the rent|between us)\b)")
_A_PLANNING_TO_MOVE = re.compile(
    r"\b(?:thinking of moving|planning to move|going to move|we're moving|were moving"
    r"|moving to|moving in|when we move|looking at (?:flats|houses|places)"
    r"|looking for a (?:flat|house|place)|new (?:flat|house|place|home))\b")


def _a_figure_for_a_plan_is_not_a_debt(understood):
    """True unless the line is working out what it can pay, which is a plan and not arrears.

    "my budget is about 250 a week on rent" is somebody choosing a flat; "i cant pay my rent on
    friday" is somebody in trouble. Both name the rent, and the arrears card had no way to tell
    them apart, so it answered both. The test is the trouble and not the subject: with one of the
    trouble words in the line the card answers as before, and without one a figure somebody is
    working to, or a move they are planning, is enough to stand it aside.
    """
    said = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if not said:
        said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if not said:
        return True
    if _A_PAYMENT_GONE_WRONG.search(said):
        return True
    return not (_A_FIGURE_FOR_A_PLAN.search(said) or _A_PLANNING_TO_MOVE.search(said))


def _a_plan_and_no_trouble(understood):
    """The other half of the same read: the rent question, when nothing has gone wrong yet."""
    return not _a_figure_for_a_plan_is_not_a_debt(understood)


# "my son wants a pension" can be a man of forty, so a bare son or daughter does not make the
# line a child's; the words here cannot be anything but a child.
_A_CHILDS_POT = ("child", "children", "kid", "kids", "grandchild", "grandchildren",
                 "grandson", "granddaughter", "junior", "baby", "newborn", "toddler",
                 "my boy", "my girl", "year old", "years old")


def _pension_for_someone(memory, understood):
    """Paying into a pension that is not your own is two questions: an adult's, where the relief
    goes to them, and a child's, which is a junior SIPP.

    "can i pay into my wife's pension" was answered with the half-your-age contribution rule - a
    confident answer to a different question - and "can i open a pension for my child" got the
    ordinary SIPP card, which never mentions a child. The money is the same 2,880 pounds a year
    either way; what changes is whose pot it is and when it can be touched, so the reply leads
    with whichever of the two the line is about."""
    text = str((understood or {}).get("clean") or "").lower()
    if not text:
        text = " ".join(str(one) for one in (understood or {}).get("words") or ()).lower()
    if any(one in text for one in _A_CHILDS_POT):
        return ("A junior SIPP is the one for a child: you open it in their name, 2,880 pounds a "
                "year from you becomes 3,600 with the 20% top-up, that is the most anyone can put "
                "in for them in a year, and the money stays locked until they are 57 - so it is a "
                "long cheap start rather than a savings account. Grandparents can pay in too, and "
                "the child owns it from eighteen.")
    return ("Yes. Anyone can pay into someone else's pension - a husband or wife, a partner, a "
            "parent - and the tax relief goes to the person whose pension it is, so 2,880 pounds "
            "from you becomes 3,600 in their pot, which is the most that can go in without their "
            "earnings. A basic-rate taxpayer has nothing more to claim; a higher earner claims the "
            "rest back through self assessment. If they are under 18 the pot is a junior SIPP, "
            "locked until they are 57.")


def _pension(memory, understood):
    """A pension question is one of three: is the money safe, when can I get at it, or should I
    pay into one at all.

    "can i take my pension early" was reaching the money-advice pointer, which answers nothing,
    while the workplace answer underneath would have been the wrong subject entirely. The safety
    questions came first, so they keep their answer word for word.
    """
    reading = understood or {}
    text = str(reading.get("clean") or reading.get("text") or " ".join(
        str(w) for w in (reading.get("words") or []))).lower()
    if any(word in text for word in _PENSION_SAFE):
        return ("In a defined-benefit (final salary) scheme the promise is the employer's, and the "
                "Pension Protection Fund steps in for most of it if the company fails. Money in a "
                "defined-contribution pot - the usual workplace kind - is yours and held apart from "
                "the company, so the firm going bust does not touch it; what it is worth moves with "
                "the funds you chose, and cash in a fund is not the same as cash in the bank. Check "
                "the yearly statement for the scheme's name and value, and a free Pension Wise "
                "appointment before you move anything.")
    if re.search(r"\b(?:take|taken|taking|access|cash in|withdraw|withdrawn|draw|early|"
                 r"lump sum|25%|quarter|before i retire|when can i|how early)\b", text):
        return ("Private pension money can usually be taken from 55, rising to 57 for most people "
                "from April 2028, and your scheme itself may set a later age. You get a quarter of "
                "it tax free and the rest is taxed as income as you draw it, so take the smallest "
                "amount you need rather than the lot: what is left has to last longer than you "
                "think, and it is usually better to live on savings first if you can.")
    return ("A workplace pension is free money: you put in 5% and your employer at least 3%, with "
            "tax relief on top. Don't opt out to add a few pounds to your pay packet now, and once "
            "a year check which fund your pot is invested in - the default is often too cautious if "
            "retirement is decades away.")


_OWING = re.compile(r"\b(?:i|we)\s+(?:still\s+)?owe\b|\bowe\s+(?:my|her|him|them|it)\b|"
                    r"\bi\s+(?:still\s+)?(?:borrowed|borrow)\b", re.I)


def _they_owe(memory):
    """True when a recent line said the person asking is the one who owes the money.

    "I owe my sister 200 pounds" then "she keeps asking for it back" is a follow-up where the
    subject is money the asking person owes, so the chase-it-up answer is exactly wrong: the
    debt has a direction, and the direction survives into the next turn.
    """
    if not isinstance(memory, dict):
        return False
    seen = 0
    for turn in reversed(memory.get("turns") or []):
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("user") or "")
        if not said:
            continue
        seen += 1
        if _OWING.search(said):
            return True
        if seen >= 3:
            break
    return False


_MONEY = r"£?\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*(k|grand|thousand)?"

# --- an age is not a sum of money ------------------------------------------------------------
# "im 34 and my back has been sore for a week" was read as somebody with £34 for a week and
# answered "That is £4.86 a day for a week. Buy the staples first - rice, pasta, eggs...", a
# grocery budget for a bad back. The figure in a person frame - "im 34", "she's 8", "my mum is
# 78", "34 years old" - is an age, and only loses that reading when the figure carries money of
# its own: "im 34 and have £200 a week", "my son is 8 and i have 30 pounds to feed us".
_A_PERSON = (
    "i", "im", "i'm", "ive", "i've", "he", "hes", "he's", "she", "shes", "she's", "they",
    "theyre", "they're", "we", "we're", "mum", "mom", "mother", "dad", "father", "son",
    "daughter", "wife", "husband", "partner", "boyfriend", "girlfriend", "nan", "gran",
    "granny", "grandma", "grandad", "grandpa", "brother", "sister", "niece", "nephew",
    "cousin", "friend", "kid", "child", "boy", "girl", "baby", "lad", "lass", "hubby")
# The frame in front of the figure: a person and "is"/"am", or "aged".
_AGE_FRAME = re.compile(
    r"(?:\b(?:my|his|her|our|their)\s+)?\b(?:" + "|".join(_A_PERSON) + r")\s*"
    r"(?:is|are|was|were|am|'s|\u2019s)?\s*$|\baged\s*$", re.I)
# ... and the money that takes the reading back, straight after the figure.
_MONEY_AFTER = re.compile(
    r"\s*(?:£|pounds?\b|quid\b|grand\b|k\b|thousand\b|a\b|per\b|each\b|every\b)", re.I)
# "34 years old", "8 year old son", "34 yr old".
_AGE_AFTER = re.compile(r"\s*(?:years?|yrs?|y/o)\s*(?:old)?\b|\s*(?:st|nd|rd|th)\b", re.I)


def _an_age(text, match):
    """True when the figure at `match` is a person's age rather than a sum of money."""
    after = text[match.end():match.end() + 12]
    if _MONEY_AFTER.match(after):
        return False
    return bool(_AGE_FRAME.search(text[:match.start()]) or _AGE_AFTER.match(after))


def _sums_in(text):
    """Every sum the line names, with an age left out: (value, match) pairs."""
    for match in re.finditer(_MONEY, text or ""):
        if _an_age(text or "", match):
            continue
        value = float(match.group(1).replace(",", ""))
        if match.group(2):
            value *= 1000
        yield value, match


# Money that is going by rather than by towards something: rent, a bill, a habit.
GOING_OUT = ("rent", "mortgage", "bill", "bills", "spend", "spending", "spent", "cost", "costs",
             "pay for", "paying for", "childcare", "nursery", "council tax", "insurance", "fuel",
             "petrol", "diesel", "commuting", "season ticket", "subscription", "subscriptions",
             "fee", "fees", "fare", "fares", "on coffee", "on food", "on shopping", "on drink",
             "takeaway", "takeaways", "smoking", "cigarettes", "gym")
# ... and money that is going towards one: the words that make a monthly figure a rate.
GOING_IN = ("save", "saves", "saving", "saved", "put away", "put by", "put aside", "putting away",
            "putting by", "set aside", "setting aside", "spare", "add to", "adding to",
            "into my savings", "into savings", "savings account", "pay in", "paying in",
            "pay off", "paying off", "overpay", "overpaying", "clear the card", "clearing",
            "towards", "toward", "goes in", "going in", "i can manage", "i could manage",
            "i can do", "i could do", "i can put", "i could put", "i manage")


def _clause_about(text, start, end):
    """The clause the figure sits in, so its direction can be read on its own."""
    left = max(text.rfind(mark, 0, start) for mark in (".", ";", ",", "?"))
    right = [at for at in (text.find(mark, end) for mark in (".", ";", ",", "?")) if at != -1]
    clause = text[left + 1:min(right) if right else len(text)].lower()
    for joiner in (" and ", " but ", " so ", " then "):
        if joiner in clause:
            half = clause.split(joiner)
            for piece in half:
                if re.search(_MONEY, piece):
                    return piece
    return clause


# The sum and the rate word can have a word or two between them and it is still a rate: "we have
# 150 spare a month", "400 left over each month", "50 put by a week". Read with nothing between
# them only, "we have 150 spare a month" was not a rate, so the 150 became the goal the person was
# saving for and the answer offered £100 a month as a way to reach the £150 they had just said
# they put by every month.
#
# A word that starts with a digit is never filler: in "how long to save 5000 at 250 a month" the
# 250 is the rate and the 5000 is what is being saved, and letting the gap eat "at 250" turns the
# goal into the per-month figure. A unit word is never filler either: "2 days a week", "3 hours a
# week" and "2 lb a week" are rates of another quantity, and reading "2 days" as two pounds a week
# answered "how long to build a house at 2 days a week" with "£9 a month is £108 in a year". Those
# rates belong to their own answers (building, exercise, study, weight), so the gap stops at the
# unit.
_UNIT_WORD = (r"(?:days?|hours?|hrs?|minutes?|mins?|weeks?|months?|years?|nights?|times"
              r"|sessions?|miles|km|kilos?|kg|lbs?|stone|stones|litres?|liters?|pints?"
              r"|cups?|eggs?|people|shifts?|pages?|chapters?|lessons?|classes?|meetings?)\b")
BETWEEN_THE_SUM_AND_THE_RATE = r"\s*(?:(?!\d|" + _UNIT_WORD + r")[\w']+\s+){0,2}"


def _per_month(text):
    """What the line puts aside each month, in pounds: "200 a month", "£50 a week" -> £217.

    Only money going towards something counts. "I pay 800 a month rent and I want to save 5000"
    is a rent and a goal, and answering "£5,000 at £800 a month is 7 months" was a confident wrong
    answer to it.
    """
    # "150 spare a month", "50 put by each week": the rate the line names often comes with a
    # word or two in front of the "a month", and without this the sum was read as the goal
    # instead - "we have 150 spare a month" answered "For £150: £100 a month is 2 months."
    match = re.search(_MONEY + BETWEEN_THE_SUM_AND_THE_RATE
                      + r"\s*(?:a|per|each|every)\s*(month|week|fortnight|year)", text)
    if not match:
        return 0
    clause = _clause_about(text, match.start(), match.end())
    if any(word in clause for word in GOING_OUT) and not any(word in clause for word in GOING_IN):
        return 0
    return int(round(_said_a_month(match) * {"month": 1, "week": 52 / 12, "fortnight": 26 / 12,
                                             "year": 1 / 12}[match.group(3)]))


def _said_a_month(match):
    """The sum the user named, in pounds, before it is turned into a month."""
    amount = float(match.group(1).replace(",", ""))
    return amount * 1000 if match.group(2) else amount


def _target(text):
    """The biggest sum the line names that is not the rate the line puts aside."""
    monthly = str(_per_month(text) or "")
    best, biggest = 0, 0
    for amount, match in _sums_in(text):
        # 24 characters, not 14: the words that can sit between the sum and the rate word are
        # cut off before the unit is read at 14, so "80 leftover a week" became the goal.
        if _rate_words(text[match.end():match.end() + 24]):
            # "what about 300 a week" is a rate, not the thing being saved for: taking it as
            # the goal answered "£300 at £1,300 a month is a single month at that rate".
            continue
        if str(int(amount)) != monthly and amount > biggest:
            biggest, best = amount, int(amount)
    return best


def _rate_words(after):
    """True when the words after a figure make it a rate: "a month", "spare a week"."""
    return bool(re.match(BETWEEN_THE_SUM_AND_THE_RATE
                         + r"\s*(?:a|per|each|every|/)\s*(?:month|week|fortnight|year|day)\b",
                         after, re.I))


def _months(amount, target):
    return int(-(-target // amount)) if amount else 0


def _a_month_in_words(text, amount):
    """£200 a month, or "£217 a month (£50 a week)" when the line named another unit."""
    match = re.search(_MONEY + BETWEEN_THE_SUM_AND_THE_RATE
                      + r"\s*(?:a|per|each|every)\s*(month|week|fortnight|year)", text)
    monthly = "£%s a month" % format(amount, ",")
    if not match or match.group(3) == "month":
        return monthly
    said = "£%s %s" % (format(int(_said_a_month(match)), ","),
                       {"fortnight": "a fortnight", "year": "a year"}.get(match.group(3),
                                                                         "a week"))
    return "%s (%s)" % (monthly, said)


def _how_long(months):
    """A number of months as people say it: 1 month, 18 months, 2 years and 3 months."""
    years, rest = divmod(months, 12)
    if months <= 1:
        return "a single month at that rate"
    if months < 24:
        return "%d months" % months
    if rest == 1:
        return "%d months, about %d years and a month" % (months, years)
    if rest:
        return "%d months, about %d years and %d months" % (months, years, rest)
    return "%d months, %d years" % (months, years)


CONSOLIDATE = re.compile(r"\b(?:consolidat\w*|loan to pay|take out a loan|get a loan|"
                         r"balance transfer|0%|zero per cent|transfer it)\b", re.IGNORECASE)


def _pay_off(memory, understood):
    """"Should I take a loan out to pay this off" and "is overpaying worth it" are two questions."""
    line = (understood.get("clean") or understood.get("text") or "") if isinstance(understood, dict) else ""
    if CONSOLIDATE.search(line or ""):
        return ("Only if the new rate is clearly lower and the card stops being used: a "
                "consolidation loan on a card you keep spending on just moves the debt and adds "
                "interest. Check the total repayable rather than the monthly payment, and ask for "
                "the settlement figure on what you owe now, since paying early can carry up to 58 "
                "days' extra interest or an early repayment charge.")
    # The answer has to be about the debt the line named: "is it worth overpaying my mortgage"
    # was answered with a credit card nobody had mentioned, and a card at 20% is not the
    # question when the money is going onto a mortgage at 4%.
    if re.search(r"\bmortgages?\b|\bremortgag", line or "", re.IGNORECASE):
        return ("Overpaying a mortgage almost always saves money, because the interest you save is "
                "your mortgage rate for every year left on the term, and no savings account pays "
                "that after tax. Check the early repayment charge first: most fixes let you "
                "overpay 10% of the balance a year without one, and above that the fee can cost "
                "more than the interest you save. Ask the lender to take the overpayment off the "
                "term rather than the monthly payment unless the lower payment is what you need, "
                "and keep three to six months of bills in savings before you start, since an "
                "overpayment cannot be taken back.")
    if re.search(r"\bloans?\b|\bfinance agreement\b|\bcar finance\b", line or "", re.IGNORECASE):
        return ("Check the settlement figure before you overpay a loan: many carry an early "
                "repayment charge, often 58 days' extra interest or a percentage of what is left, "
                "and if that is bigger than the interest you would save, keep the money in "
                "savings instead. Where there is no charge, overpaying a loan at 8% or more beats "
                "any savings account, so it is the better use of spare money after a small "
                "buffer.")
    return ("Compare the interest you'd save with what the savings earn: a credit card at 20% or "
            "more beats any savings account, so clear that first, and check the early repayment "
            "charge before overpaying a loan or mortgage (most mortgages allow 10% of the balance a "
            "year without one). Keep a small buffer in savings while you do it, so a surprise bill "
            "doesn't put you back on the card.")


def _card_months(balance, payment, apr=20.0):
    """Months to clear a balance at a fixed payment, on a stated APR, by the annuity formula."""
    rate = apr / 100.0 / 12
    if payment <= balance * rate:
        return 0
    return int(-math.log(1 - rate * balance / payment) / math.log(1 + rate)) + 1


HOW_LONG = re.compile(r"\b(?:how long|how many years|when will|how quickly|how fast)\b",
                      re.IGNORECASE)


def _card_payoff(memory, understood):
    """"How long will it take to pay off my card" wants a date, not the minimum-payment talk."""
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "")
    balance = _target(text)
    payment = _per_month(text)
    if HOW_LONG.search(text) and balance and payment:
        months = _card_months(balance, payment)
        if months:
            return ("£%s at 20%% APR on £%s a month is %s, and about £%s in total, mostly "
                    "interest. Every extra £50 a month comes off the end of that, so a pay rise "
                    "or a balance transfer is worth more here than almost anywhere else."
                    % (format(balance, ","), format(payment, ","), _how_long(months),
                       format(payment * months, ",")))
    if HOW_LONG.search(text) and balance:
        # The balance is named but not the payment: show the minimum and a round £100 on the
        # balance they gave, rather than somebody else's £1,000.
        floor = max(25, int(round(balance * 0.025)))
        slow, quick = _card_months(balance, floor), _card_months(balance, 100)
        if slow and quick:
            return ("£%s at 20%% APR on the minimum, about £%s a month, takes %s and costs about "
                    "£%s; at £100 a month it is %s. Paying the minimum keeps the debt alive, so "
                    "fix a standing order for a figure that actually falls."
                    % (format(balance, ","), format(floor, ","), _how_long(slow),
                       format(floor * slow, ","), _how_long(quick)))
    if HOW_LONG.search(text):
        return ("At 20% APR a card barely moves on the minimum, which is 1-3% of the balance: "
                "£1,000 on £25 a month takes five and a half years and costs £1,675, and £50 a "
                "month clears it in just over two. Tell me the balance, the APR and what you can "
                "pay, and I'll give you the month it ends.")
    return ("Pay more than the minimum: it's set at 1-3% of the balance and mostly covers "
            "interest, so the debt barely moves. List the cards by APR, throw spare money at the "
            "dearest one first, and ask about a 0% balance transfer, which buys you a year or "
            "more to clear the rest.")


def _sum_and_unit(text, units):
    """The first sum in the line followed by one of these units: ("a year", "per year")."""
    for match in re.finditer(_MONEY + r"\s*([^.;!?]{0,18})", text):
        tail = " " + match.group(3).lower()
        if any(unit in tail for unit in units):
            amount = float(match.group(1).replace(",", ""))
            return int(amount * 1000 if match.group(2) else amount)
    return 0


# A figure the line introduces as pay is income, not the price of anything: "i earn 25k", "im 29
# and on 34k", "salary is 40k", "take home 2,300". The deposit card read any sum of 20,000 or
# more as the price of a house, so a salary was multiplied by 10% and said back as the deposit
# the person needs - "on £34,000 that is £3,400" - which is a wrong fact said plainly, worse
# than the bare £20,000 card it replaced.
# "we paid 250k for our flat" is a price, not a pay: the bare word "paid" and the bare word "pay"
# both put a figure somebody *paid* on the pay side of the house-deposit reading, so only the
# passive "am/is/are/was/were/been paid" and "gets/got paid" count as pay (bright-plum, msg 75426).
INCOME_BEFORE = re.compile(
    r"(?:\bearn\w*|\bsalar\w*|\bwage\w*|\bincomes?\b|\btake home\b|"
    r"(?:(?:am|is|are|was|were|been|get|gets|got|getting)\s+paid)|"
    r"\bbring(?:ing)? in\b|\bmake\b|\bgot a job\b|"
    r"\b(?:i|we|he|she|they)(?:'?m|'?re|'?s)?\s+(?:am|is|are)?\s*on)"
    r"(?:\s+(?:is|was|of|at|around|about|roughly|approx(?:imately)?|now|still))?\s*[£$€]?\s*$", re.I)
# "34k a year" and "34k pa" are pay even with no word in front of them.
INCOME_AFTER = re.compile(r"^\s*(?:(?:a|per|each|every)\s*(?:year|annum)|pa\b|p\.a\.|"
                          r"a year|a\s+year\b|gross|before tax|after tax)", re.I)


# "im 29 and on 34k": the "on" carries pay only when the figure is written in thousands and
# nothing about a house is what it hangs on. "a deposit on 200000" is a price, and so is
# "a flat on at 180k", so the property words keep the price reading.
INCOME_ON_K = re.compile(r"(?:\band|\bthen|\balso|,|;)\s+on\s*[£$€]?\s*$", re.I)
PRICE_NEAR = re.compile(r"house|home|flat|property|price|deposit|cost|worth|asking|valued|"
                        r"selling|market|rent|mortgage|\bpaid\b", re.I)


def _sum_amount(match):
    amount = float(match.group(1).replace(",", ""))
    return int(amount * 1000 if match.group(2) else amount)


def _is_income(text, match):
    """True when the line gives this sum as pay rather than as the price of anything."""
    before = text[max(0, match.start() - 30):match.start()]
    after = text[match.end():match.end() + 16]
    if INCOME_BEFORE.search(before) or INCOME_AFTER.search(after):
        return True
    if not (match.group(2) and INCOME_ON_K.search(before)):
        return False
    # The clause the figure sits in, not the whole line: with two turns joined the earlier one
    # says "house deposit", which is not what this "on 34k" hangs on.
    clause = re.split(r"[\n.;,]|\band\b|\bbut\b", before)[-1]
    return not PRICE_NEAR.search(clause)


def _income_target(text):
    """The biggest sum the line gives as pay, or 0."""
    best = 0
    for amount, match in _sums_in(text):
        if _is_income(text, match):
            best = max(best, amount)
    return best


def _price_target(text):
    """The biggest sum the line gives as a price: not a rate, and not pay."""
    monthly = str(_per_month(text) or "")
    best = 0
    for amount, match in _sums_in(text):
        if _is_income(text, match):
            continue
        if _rate_words(text[match.end():match.end() + 24]):
            continue
        if str(amount) != monthly and amount > best:
            best = amount
    return best


def _house_deposit(memory, understood):
    """"How big a deposit on a 300,000 house" wants 10% of that price, not of 200,000."""
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "")
    price = _price_target(text)
    if price >= 20000:
        # someone else's price is the whole question: answer with their figure
        return ("Aim for 10%% of the price: on %s that is %s, and 5%% is %s, which costs you "
                "noticeably more in interest over the term. A Lifetime ISA adds 25%% on up to "
                "\u00a34,000 a year towards a first home, and a broker can tell you what you'd "
                "actually be offered before you start looking."
                % ("£" + _comma(price), "£" + _comma(int(price * 0.10)),
                   "£" + _comma(int(price * 0.05))))
    if price >= 1000:
        # a deposit already saved, or a rate, is a different question: pass. A small number is
        # an age or a count, not a deposit - "im 29 and on 34k" was read as a £29 one, which
        # passed the line into the hold instead of answering the salary behind it.
        return None
    pay = _income_target(text)
    if pay:
        # a salary is not a price, so there is no deposit to work out: say what it buys instead
        # of multiplying their pay by 10% and calling it the deposit they need.
        low, high = int(pay * 4), int(pay * 4.5)
        return ("That is a salary rather than a price, so the deposit depends on what you buy: "
                "a lender will usually offer around four to four and a half times your pay, so "
                "%s is roughly a %s to %s mortgage, and 10%% of that is a %s to %s deposit. Aim "
                "for 10%% rather than 5%% if you can - it gets you noticeably better rates - and "
                "a Lifetime ISA adds 25%% on up to \u00a34,000 a year towards a first home."
                % ("£" + _comma(pay), "£" + _comma(low), "£" + _comma(high),
                   "£" + _comma(int(low * 0.10)), "£" + _comma(int(high * 0.10))))
    return ("Aim for 10% of the price: £20,000 on a £200,000 home, and it gets you noticeably "
            "better rates than 5%. A Lifetime ISA adds 25% on up to £4,000 a year towards a first "
            "home, and a broker can tell you what you'd actually be offered before you start "
            "looking.")


# The three sets of bands, as data. England and Northern Ireland share one table (SDLT), Scotland
# has LBTT and Wales has LTT: the names are different taxes, not regional spellings of one, and a
# line that names one of the devolved taxes must not be answered with England's bill.
#
# SDLT is the table that applies from 1 April 2025: the nil band for a home mover doubled to
# 250,000 and the old 2% band went, so a 300,000 home pays 2,500 and a 250,000 one pays nothing.
# LTT in Wales is the table that applies from 1 April 2024: nil to 225,000 and 6% above it, which
# replaced 3% from 180,000. Both governments move these with their budgets, which is why every
# long reply ends by saying so and naming the calculator to check against.
_SDLT = ((0, 250000, 0.0), (250000, 925000, 0.05), (925000, 1500000, 0.10),
         (1500000, None, 0.12))
_LBTT = ((0, 145000, 0.0), (145000, 250000, 0.02), (250000, 325000, 0.05),
         (325000, 750000, 0.10), (750000, None, 0.12))
_LTT = ((0, 225000, 0.0), (225000, 400000, 0.06), (400000, 750000, 0.075),
        (750000, 1500000, 0.10), (1500000, None, 0.12))
# Scotland's first-time relief is not a band table: it is worth at most 600 pounds, because it
# lifts the nil band from 145,000 to 175,000 and the 2% band starts 30,000 higher. It is only
# available while the price is 175,000 or less, so anyone above that pays the ordinary LBTT.
_SLBTT_FIRST_NIL = 175000


def _duty(value, bands):
    """The tax on a price, band by band: each rate applies only to the part inside its band."""
    total = 0.0
    for low, top, rate in bands:
        if top is None:
            top = value
        total += max(0.0, min(value, top) - low) * rate
    return total


def _price_named(text):
    """"2 million" and "1.5m" are prices too, and _target only reads digits."""
    price = _target(text)
    for match in re.finditer(r"\b(\d+(?:\.\d+)?)\s*(million|m)\b", text):
        amount = int(float(match.group(1)) * 1000000)
        if amount > price:
            price = amount
    return price


def _stamp_duty(memory, understood):
    """A price in the line is the price: the tax on a 250,000 home is nothing, not a deposit.

    Two reviewers between them found this answer wrong twice over, and both were right. It first
    used the first-time buyer nil band as the mover nil band, so every mover figure was short;
    then, once the bands were right, it still answered a line naming Wales' land transaction tax
    or Scotland's LBTT with England's bill, which is a wrong tax figure said flatly - worse than
    the shrug it replaced. So: three band tables as data, the nation taken from the line, and
    every figure in the reply a number this code produced.
    """
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "")
    price = _price_named(text)
    first = bool(re.search(r"first[- ]time|first home|first house|first flat|first property|"
                           r"first place|our first", text))
    # A buy-to-let is asked with a price in the line as often as without, and the surcharged bill
    # has to be the first figure said: "nothing to pay" as the headline of a buy-to-let question
    # is the one answer that must never happen.
    second = bool(re.search(r"second home|buy[- ]to[- ]let|buy to let|second property|"
                            r"additional home|additional dwelling|investment property|"
                            r"second house|rental property|landlord", text))
    if re.search(r"scotland|scottish|lbtt|land and buildings|edinburgh|glasgow|aberdeen|"
                 r"dundee|inverness", text):
        return _scottish_duty(price, first, second)
    if re.search(r"wales|welsh|\bltt\b|land transaction tax|cardiff|swansea|newport", text):
        return _welsh_duty(price, first, second)
    return _english_duty(price, first, second)


def _duty_said(amount):
    """A tax figure: "Nothing to pay" rather than "0", and thousands separated."""
    return "Nothing to pay" if amount <= 0 else "\u00a3" + _comma(int(round(amount)))


def _english_duty(price, first, second):
    """SDLT, England and Northern Ireland, from April 2025."""
    def first_time(value):
        if value > 500000:
            return _duty(value, _SDLT)
        return max(0.0, value - 300000) * 0.05

    priced = "\u00a3" + _comma(price) if price >= 20000 else ""
    if price >= 20000 and second:
        extra = price * 0.05
        normal = _duty(price, _SDLT)
        if normal <= 0:
            made = ("nothing to pay in the normal bands, so the whole bill is the 5% surcharge "
                    "on the price")
        else:
            made = ("%s of it is the normal bands and %s is the 5%% surcharge, which is 5 "
                    "percentage points on every band from the first pound"
                    % (_duty_said(normal), _duty_said(extra)))
        return ("%s on a %s second home: %s. It is usually paid "
                "within 14 days of completion and reclaimed if you sell the old home within three "
                "years. Check GOV.UK before you exchange, because the bands move with budgets."
                % (_duty_said(normal + extra), priced, made))
    if price >= 20000 and first:
        if price > 500000:
            return ("%s on a %s first home: the first-time relief stops above \u00a3500,000, so "
                    "this pays the mover bill - nothing to \u00a3250,000, 5%% to \u00a3925,000, "
                    "10%% to \u00a31.5m and 12%% above that. A second home or a buy-to-let adds "
                    "5%% to every band. Check GOV.UK before you exchange, because the bands move "
                    "with budgets." % (_duty_said(_duty(price, _SDLT)), priced))
        return ("%s on a %s first home: a first-time buyer pays nothing up to \u00a3300,000 and 5%% "
                "on the part from \u00a3300,000 to \u00a3500,000, so the bill is the part above "
                "\u00a3300,000 at 5%%. A home mover would pay %s on the same price, and above "
                "\u00a3500,000 the relief goes and this becomes the mover bill."
                % (_duty_said(first_time(price)), priced, _duty_said(_duty(price, _SDLT))))
    if price >= 20000:
        return ("%s on a %s home: nothing up to \u00a3250,000, 5%% on \u00a3250,000 to "
                "\u00a3925,000, 10%% to \u00a31.5m and 12%% above that, so the bill is only what "
                "is above those bands. A first-time buyer pays nothing up to \u00a3300,000 "
                "instead, and a second home or a buy-to-let adds 5%% to every band, which would be "
                "%s here. Check GOV.UK before you exchange, because the bands move with budgets."
                % (_duty_said(_duty(price, _SDLT)), priced, _duty_said(_duty(price, _SDLT) + price * 0.05)))
    if second:
        return ("Add 5% to every band, from the first pound: on a \u00a3250,000 buy-to-let that is "
                "\u00a312,500 instead of nothing, and on a \u00a3400,000 one \u00a327,500 instead "
                "of \u00a37,500. It is paid within 14 days of completion and reclaimed if you "
                "sell the old home within three years.")
    return ("Nothing up to \u00a3250,000 for a home mover, or up to \u00a3300,000 for a "
            "first-time buyer: 5% from \u00a3250,000 to \u00a3925,000, 10% to \u00a31.5m and 12% "
            "above that, and a second home or a buy-to-let adds 5 percentage points to every "
            "band. In Scotland it is LBTT and in Wales it is LTT, with their own bands, and the "
            "bill is paid within 14 days of completion, so check GOV.UK for your price before you "
            "exchange.")


def _scottish_duty(price, first, second):
    """LBTT, Scotland: nil to 145,000, and the first-time relief lifts that to 175,000."""
    def first_time(value):
        # the relief is worth at most 600 pounds and is only available while the price is 175,000
        if value > _SLBTT_FIRST_NIL:
            return _duty(value, _LBTT)
        return 0.0

    priced = "\u00a3" + _comma(price) if price >= 20000 else ""
    if price >= 20000 and second:
        extra = price * 0.08
        normal = _duty(price, _LBTT)
        if normal <= 0:
            made = ("nothing to pay in the LBTT bands, so the whole bill is the 8% Additional "
                    "Dwelling Supplement")
        else:
            made = ("%s of it is the LBTT bands and %s is the 8%% Additional Dwelling Supplement"
                    % (_duty_said(normal), _duty_said(extra)))
        return ("%s on a %s second home in Scotland: %s on the whole price. The supplement is "
                "paid within "
                "30 days of settlement and claimed back if you sell the old home within 36 months, "
                "so check Revenue Scotland's calculator before you bid."
                % (_duty_said(normal + extra), priced, made))
    if price >= 20000 and first:
        if price > _SLBTT_FIRST_NIL:
            return ("%s on a %s first home in Scotland: the first-time relief stops above "
                    "\u00a3175,000, so this pays the full LBTT bill - nothing to \u00a3145,000, "
                    "2%% to \u00a3250,000, 5%% to \u00a3325,000, 10%% to \u00a3750,000 and 12%% "
                    "above that. The relief is worth \u00a3600 at most. An additional home adds "
                    "8%% on the whole price."
                    % (_duty_said(_duty(price, _LBTT)), priced))
        return ("Nothing, on a %s first home in Scotland: first-time buyers pay no LBTT up to "
                "\u00a3175,000 instead of \u00a3145,000. The relief is worth \u00a3600 at most and "
                "stops once the price is over \u00a3175,000, so a \u00a3200,000 first home pays the "
                "ordinary 2%% above \u00a3145,000, which is \u00a31,100." % priced)
    if price >= 20000:
        return ("%s on a %s home in Scotland under LBTT: nothing up to \u00a3145,000, 2%% to "
                "\u00a3250,000, 5%% to \u00a3325,000, 10%% to \u00a3750,000 and 12%% above that. "
                "A first-time buyer pays nothing up to \u00a3175,000 instead, which is worth "
                "\u00a3600 at most, and an additional home adds 8%% on the whole price, which "
                "would be %s here. Revenue Scotland has the calculator to check it against."
                % (_duty_said(_duty(price, _LBTT)), priced,
                   _duty_said(_duty(price, _LBTT) + price * 0.08)))
    return ("In Scotland it is LBTT, not stamp duty: nothing up to \u00a3145,000, 2% to "
            "\u00a3250,000, 5% to \u00a3325,000, 10% to \u00a3750,000 and 12% above that. A "
            "first-time buyer's nil band is \u00a3175,000, worth \u00a3600 at most, an additional "
            "home adds 8% on the whole price, and the bill is due within 30 days of settlement, so "
            "put the price in and check Revenue Scotland's calculator.")


def _welsh_duty(price, first, second):
    """LTT, Wales: nil to 225,000, and no first-time buyer relief at all."""
    priced = "\u00a3" + _comma(price) if price >= 20000 else ""
    if price >= 20000 and second:
        extra = price * 0.05
        normal = _duty(price, _LTT)
        if normal <= 0:
            made = ("nothing to pay in the LTT bands, so the whole bill is the 5% higher rate")
        else:
            made = ("%s of it is the LTT bands and %s is the 5%% higher rate"
                    % (_duty_said(normal), _duty_said(extra)))
        return ("%s on a %s second home in Wales: %s on the whole price. It is due within 30 "
                "days of completion and "
                "reclaimed if you sell the old home within three years, so check the Welsh "
                "Revenue Authority calculator before you exchange."
                % (_duty_said(normal + extra), priced, made))
    if price >= 20000:
        return ("%s on a %s home in Wales under LTT: nothing up to \u00a3225,000, 6%% from there "
                "to \u00a3400,000, 7.5%% to \u00a3750,000, 10%% to \u00a31.5m and 12%% above that. "
                "There is no first-time buyer relief in Wales, and an additional home pays 5%% on "
                "the whole price, which would be %s here. The Welsh Revenue Authority has the "
                "calculator to check it against."
                % (_duty_said(_duty(price, _LTT)), priced,
                   _duty_said(_duty(price, _LTT) + price * 0.05)))
    if second:
        return ("In Wales the surcharge is 5% on the whole price: a \u00a3250,000 second home pays "
                "\u00a314,000 instead of \u00a31,500. LTT itself is nothing up to \u00a3225,000, "
                "6% to \u00a3400,000, 7.5% to \u00a3750,000, 10% to \u00a31.5m and 12% above, and "
                "there is no first-time buyer relief in Wales.")
    return ("In Wales it is LTT, not stamp duty, and it is nothing up to \u00a3225,000: 6% from "
            "there to \u00a3400,000, 7.5% to \u00a3750,000, 10% to \u00a31.5m and 12% above that. "
            "There is no first-time buyer relief, an additional home pays 5% on the whole price, "
            "and the bill is due within 30 days of completion, so check the Welsh Revenue "
            "Authority calculator with your price.")


def _mortgage_afford(memory, understood):
    """"On 32k a year, is 1,500 a month too much" wants the two limits, not what a mortgage is."""
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "")
    income = _sum_and_unit(text, ("a year", "per year", "a yr", "salary", "annum", "earn"))
    payment = _sum_and_unit(text, ("a month", "per month", "monthly", "pcm", "a month"))
    if not income and not payment and "afford" in text:
        # "can we afford a house on one salary" names no numbers at all, and the rule of thumb is
        # the whole answer a person wants before they start viewing flats. "How much can I borrow
        # for a mortgage" is the explainer's line on main, and it stays there.
        return ("Lenders usually cap borrowing at about 4.5 times income, so two salaries of "
                "£25,000 buy roughly £225,000 and a single £30,000 about £135,000 - the deposit "
                "sits on top of that (5% at least, 10% for a decent rate). Two salaries add up, "
                "but childcare, car finance and card limits all come off the total, so run your "
                "own figures through a bank or broker calculator before you view anything.")
    if income and not payment:
        # "On 25k a year, can I get a 300k mortgage" names the loan instead of a payment.
        wanted = _target(text)
        if wanted and wanted != income:
            cap = int(income * 4.5)
            if wanted > cap:
                return ("On £%s a year lenders cap borrowing at about 4.5 times income, so £%s - a "
                        "£%s mortgage is above that on one salary. A joint application, a bigger "
                        "deposit or a much longer term is what closes the gap, and a fee-free "
                        "broker will tell you what lenders would actually offer."
                        % (format(income, ","), format(cap, ","), format(wanted, ",")))
            return ("On £%s a year a £%s mortgage is within the usual 4.5 times income cap of £%s, "
                    "so it comes down to the deposit (5% at least, 10% for a decent rate), your "
                    "credit file and the monthly payment at today's rates. A broker can check all "
                    "three in an afternoon."
                    % (format(income, ","), format(wanted, ","), format(cap, ",")))
        # "can we afford a house on one salary" names no numbers at all, and the rule of thumb
        # is the whole answer a person wants before they start viewing flats.
        return ("Lenders usually cap borrowing at about 4.5 times income, so two salaries of "
                "£25,000 buy roughly £225,000, and a single £30,000 about £135,000 - the deposit "
                "sits on top of that (5% at least, 10% for a decent rate). Two salaries add up, "
                "but childcare, car finance and card limits all come off the total, so run your "
                "own figures through a bank or broker calculator before you view anything.")
    if payment and not income:
        # "Is £1,500 a month too much for a mortgage" names the payment and no salary, so the
        # honest answer is what that payment buys and the share of pay it should be.
        loan = int(payment * (1 - (1 + 0.05 / 12) ** -300) / (0.05 / 12))
        return ("£%s a month is roughly a £%s mortgage at 5%% over 25 years. The usual test is "
                "keeping the payment under about a third of your take-home pay, so £%s a month "
                "wants a net income near £%s, and the deposit (5%% at least, 10%% for a decent "
                "rate) sits on top of the loan."
                % (format(payment, ","), format(loan, ","), format(payment, ","),
                   format(payment * 3, ",")))
    if not income or not payment:
        return None
    cap = int(income * 4.5)
    support = int(payment * (1 - (1 + 0.05 / 12) ** -360) / (0.05 / 12))
    limit = min(cap, support)
    monthly = int(limit * (0.045 / 12) / (1 - (1 + 0.045 / 12) ** -360))
    if support < cap:
        first = ("£%s a month supports a loan of about £%s at 5%% over 30 years, and the payment "
                 "is the limit here rather than the salary: lenders cap borrowing near 4.5 times "
                 "income, which on £%s a year is £%s."
                 % (format(payment, ","), format(support, ","), format(income, ","),
                    format(cap, ",")))
    else:
        first = ("On £%s a year lenders cap borrowing at about 4.5 times income, so £%s - your "
                 "£%s a month would support about £%s, so the salary is the limit, not the "
                 "payment." % (format(income, ","), format(cap, ","), format(payment, ","),
                               format(support, ",")))
    return (first + " Borrowing £%s at 4.5%% over 30 years costs about £%s a month, so keep the "
            "difference for fees, insurance and the months when something breaks."
            % (format(limit, ","), format(monthly, ",")))


# A line asking how long something will take, which a goal already worked out can answer.
ASKS_A_LENGTH = re.compile(r"\bhow (?:long|soon|many (?:months|years|weeks))\b"
                           r"|\bhow much longer\b|\bwhen will i have\b")

# The sums each month this domain works a goal out at, so a second length question gets the next
# sums up instead of the answer the person already has.
# The rates a goal under the smallest one above is saved at, as (rate, months) pairs. The goal
# itself is one month at that rate, which is true and worth reading; half of it is two months,
# which is the choice a person with £100 to find actually has. Only whole sums that read like a
# standing order, so "£25 a month for four months" is offered but "£22.50" never is.
SMALL_GOAL_MONTHS = (1, 2, 4)
# How a short number of months reads in that sentence: "one month at £100 a month, or two at £50"
# is a choice a person can see, where "1 months at £100" is not.
MONTHS_IN_WORDS = {1: "one month", 2: "two months", 3: "three months", 4: "four months"}


def _small_goal_rates(named):
    """The two ways to save a sum below the smallest rate on the list, in months."""
    found = []
    for months in SMALL_GOAL_MONTHS:
        rate = named / months
        if rate != int(rate) or rate < SMALLEST_GOAL:
            continue
        if months > 1 and int(rate) % 5:
            continue
        found.append((int(rate), months))
    return found[:2]


RATES_PEOPLE_SAVE_AT = (100, 250, 500, 750, 1000, 1500)
# The smallest sum that is a goal at all. Below it the figure is a unit of something else ("2
# days a week", "3 hours a week") and answering "For £2: £100 a month is a single month" reads a
# quantity as money. Amounts this small are not saved for in a pot, they are spent.
SMALLEST_GOAL = 20


def _rates_already_given(memory):
    """The sums each month this chat has already shown, read from the answers it gave."""
    given = set()
    for record in (memory or {}).get("entry_answers") or ():
        text = str(record.get("text") or "")
        for rate in RATES_PEOPLE_SAVE_AT:
            if "£%s a month" % format(rate, ",") in text:
                given.add(rate)
    return given


# "If I save 50 a week for a year how much is that" is a multiplication, not a target: the rate
# and the length are both named and nothing is being saved for. The lengths people say, in the
# units the rate is said in.
_DURATION = re.compile(
    r"\b(?:for|in|over|after|within|across)\s+"
    r"(a|an|one|two|three|four|five|six|seven|eight|nine|ten|\d+(?:\.\d+)?)\s*"
    r"(year|years|month|months|week|weeks|fortnight|fortnights)\b", re.I)
_DURATION_WORDS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                   "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
_IN_A_YEAR = {"year": 1, "month": 12, "week": 52, "fortnight": 26}


def _rate_for_a_time(text):
    """(what is put by, how many, unit) for "50 a week for a year", or None.

    Only a rate going towards savings counts, so "i pay 800 rent a month for a year" is not this
    sum. The answer is the arithmetic the person asked for, and the working behind it.
    """
    rate = re.search(_MONEY + r"\s*(?:a|per|each|every)\s*(month|week|fortnight|year)", text)
    if not rate:
        return None
    clause = _clause_about(text, rate.start(), rate.end())
    if any(word in clause for word in GOING_OUT) and not any(word in clause for word in GOING_IN):
        return None
    length = _DURATION.search(text)
    if not length:
        return None
    count = _DURATION_WORDS.get(length.group(1).lower())
    if count is None:
        count = int(float(length.group(1)))
    unit = length.group(2).lower().rstrip("s")
    if count <= 0 or count > 60:
        return None
    return _said_a_month(rate), rate.group(3), count, unit


def _rate_over_time(memory, understood):
    """The total a named rate reaches in a named time, or None when the line names no both."""
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "")
    found = _rate_for_a_time(text)
    if not found:
        return None
    amount, rate_unit, count, unit = found
    # both are turned into how often they happen in a year: 50 a week over 2 years is 104 weeks.
    total = amount * _IN_A_YEAR[rate_unit] * count / _IN_A_YEAR[unit]
    if total < amount:
        return None
    total = int(round(total))
    said = {"week": "a week", "fortnight": "a fortnight", "month": "a month",
            "year": "a year"}[rate_unit]
    length = length_in_words(count, unit)
    working = _working_out(amount, rate_unit, count, unit, total)
    return ("£%s %s for %s is £%s.%s Set the standing order for the day after payday and the "
            "money leaves before you can spend it."
            % (format(int(amount), ","), said, length, format(total, ","),
               (" " + working) if working else ""))


def length_in_words(count, unit):
    if count == 1:
        return "a " + unit
    return "%d %ss" % (count, unit)


def _working_out(amount, rate_unit, count, unit, total):
    """The multiplication said plainly, in the unit the person used, when it is not the same."""
    in_rate_unit = total / amount if amount else 0
    if abs(in_rate_unit - round(in_rate_unit)) < 0.01 and int(round(in_rate_unit)) != count:
        return "That is %d %ss at £%s each." % (int(round(in_rate_unit)), rate_unit,
                                                format(int(amount), ","))
    return ""


def _time_to_save(memory, understood):
    """How long a goal takes at what the line puts aside: the sum people actually want."""
    over_time = _rate_over_time(memory, understood)
    if over_time:
        return over_time   # a rate and a length named: the multiplication, not a target
    text = str(understood.get("clean") or "")
    said = str((understood or {}).get("text") or "")
    amount, target = _per_month(text), _target(text)
    if not amount or amount <= 0:
        # No rate named: how long a goal takes depends on what is being put by, so the sums at
        # the rates people actually save are the honest answer - for a goal this line named
        # itself, and for a length question about a goal the chat has just worked out.
        named = target if (target and _target(said)) else 0
        if not named and ASKS_A_LENGTH.search(text.lower()):
            # The goal is the one the person named themselves a turn or two ago, not the biggest
            # sum in the bot's own answer: "£20,000 on a £200,000 home" would make the house the
            # target and answer a question nobody asked.
            named = _goal_from_user(memory, 0)
        if named > 0:
            # A second "how long will that take" is not the answer they already have: the sums
            # already on the screen are skipped and the next ones up are given.
            skip = set() if _target(said) else _rates_already_given(memory)
            rates = [rate for rate in RATES_PEOPLE_SAVE_AT
                     if rate < named and rate not in skip][:3]
            if not rates and SMALLEST_GOAL < named and not skip:
                # A goal smaller than the smallest sum on the list has an answer too. Said at that
                # sum it restates the goal - "For £100: £100 a month is a single month at that
                # rate" tells a person nothing they did not just say - so the goal itself is the
                # rate for one month, and half of it for two: "one month at £100 a month, or two
                # months at £50". Only whole, tidy sums are offered.
                small = _small_goal_rates(named)
                if small:
                    parts = ["%s at £%s a month" % (MONTHS_IN_WORDS.get(months,
                                                                       "%d months" % months),
                                                    format(rate, ","))
                             for rate, months in small]
                    return ("For £%s: %s. Pick the rate your pay can carry and set the standing "
                            "order for the day after payday, so you never have to decide again."
                            % (format(named, ","),
                               " or ".join(parts) if len(parts) > 1 else parts[0]))
            if rates:
                parts = ["£%s a month is %s" % (format(rate, ","), _how_long(_months(rate, named)))
                         for rate in rates]
                return ("For £%s: %s. Pick the rate your pay can carry and set the standing order "
                        "for the day after payday, so you never have to decide again."
                        % (format(named, ","), ", ".join(parts)))
        return None
    if not target:
        for value in understood.get("numbers") or ():
            if isinstance(value.get("value"), (int, float)) and value["value"] > amount:
                target = int(value["value"])
                break
    if not target or target <= 0:
        target = _goal_from_user(memory, amount)
    if not target or target <= 0:
        target = _goal_already_named(memory)
    if not target or target <= 0:
        # A rate with no goal named: the sums it reaches are the honest answer to "how long",
        # and they are what the person needs to pick a rate against.
        return ("%s is £%s in a year and £%s in five. Say what you are saving for and "
                "the total, and I will work out exactly how long it takes."
                % (_a_month_in_words(text, amount), format(amount * 12, ","),
                   format(amount * 60, ",")))
    months = _months(amount, target)
    after = _how_long(months)
    return ("£%s at %s is %s. A standing order the day after payday does it without you "
            "deciding again, and any interest or pay rise only shortens it."
            % (format(target, ","), _a_month_in_words(text, amount), after))


# A sum an answer says to aim for, as opposed to any other figure it mentions on the way.
AIM_FOR = re.compile(r"\b(?:aim for|aim to save|target|goal|save|saving|save up|put aside|set aside|"
                     r"need|needs|deposit of|deposit is|at least)\b[^.£]{0,24}£([\d,]+)",
                     re.IGNORECASE)


def _goal_from_user(memory, amount):
    """The biggest sum the person themselves named lately, if it is a goal rather than a rate.

    "I'm trying to save 3000 for a trip" then "I'm putting away 200 a month so far" is about the
    3000. Reading the sum out of the bot's own answer instead would take the £600 in its example
    ("£600 by June is about £75 a month") as the goal and answer a question nobody asked.

    A rate is not a goal either, and the words after the figure are what says which it is: "i want
    to save 200 a month" names no goal at all, only a rate. Read as a goal it turned the next
    line, "actually make it 100", into "£200 at £100 a month is 2 months" - the arithmetic for a
    pot of £200 that nobody had named, made out of the rate they were trying to change.
    """
    seen = 0
    for turn in reversed((memory or {}).get("turns") or ()):
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("user") or "")
        if not said:
            continue
        seen += 1
        best = 0
        for value, match in _sums_in(said):
            if _rate_words(said[match.end():match.end() + 24]):
                continue  # a rate they put by, not a pot they are aiming at
            if value > amount and value > best:
                best = int(value)
        if best:
            return best
        if seen >= 4:
            break
    return 0


_MONTHS = ("january", "february", "march", "april", "may", "june", "july", "august",
           "september", "october", "november", "december")


def _named_month(memory):
    """The month the person named lately as a deadline: "I want 500 saved by December"."""
    seen = 0
    for turn in reversed((memory or {}).get("turns") or ()):
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("user") or "").lower()
        if not said:
            continue
        seen += 1
        found = _month_in(said)
        if found:
            return found
        if seen >= 4:
            break
    return ""


def _month_in(text):
    """The deadline month this line names, or Christmas when it says Christmas."""
    low = " " + str(text or "").lower() + " "
    for name in _MONTHS:
        if re.search(r"\b%s\b" % name, low):
            return name
    if "christmas" in low or "xmas" in low:
        return "december"
    return ""


def _save_goal(memory, understood):
    """A goal named in the line gets its own arithmetic, not an example with someone else's sum."""
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "")
    if _a_first_meeting(text, understood):
        return None
    if _target(text) or _per_month(text) or _goal_from_user(memory, 0) or _goal_already_named(memory):
        worked = _time_to_save(memory, understood)
        if worked:
            return worked
    return ("Work backwards from the date you need it: divide the total by the weeks left to get "
            "the weekly figure, then set a standing order for it the day after payday into an "
            "account you don't carry a card for. Any bonus, refund or bill that goes down follows "
            "it in.")


# The words a question about money is made of. A line with none of them is another subject that
# happens to carry "a week", and the saving fallback below used to answer it with a standing
# order: "how many days in a week should i run" got "tell me the total and the date", and so did
# "how much exercise a week is enough" and "how much water a week". A rate and a period of time
# are not a money question on their own - the money has to be in the line.
_MONEY_SUBJECT = re.compile(
    r"[\d£]|\b(?:pounds?|quid|money|cash|save|saves|saving|savings|saved|afford|affordable|"
    r"budget|budgeting|income|salary|wage|wages|pay|paid|payday|earn|earns|earnings|earned|"
    r"spend|spends|spending|spent|cost|costs|costing|bill|bills|debt|debts|loan|loans|"
    r"overdraft|mortgage|rent|invest|investment|pension|account|expenses|outgoings|"
    r"price|prices|priced|cheaper|expensive|put\s+by|put\s+aside|put\s+away|set\s+aside|"
    r"set\s+by|standing\s+order|direct\s+debit|pay\s+off|paying\s+off|"
    # What people save up for is money too: a thread that started at "how much should i put by"
    # goes on with "and a week for the holiday?" and the goal is the only money word in it.
    r"holiday|holidays|christmas|wedding|deposit|house|flat|mortgage|car|van|trip|"
    r"bike|bikes|motorbike|bicycle|scooter|"
    r"emergency|rainy\s+day|fees|tuition|school\s+trip|fund|funds)\b", re.I)


def _put_by(memory, understood):
    """How much to set aside each week for a target that was already named."""
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "")
    over_time = _rate_over_time(memory, understood)
    if over_time:
        return over_time
    goal = _target(text) or _goal_from_user(memory, 0) or _goal_already_named(memory)
    month = _month_in(text) or _named_month(memory)
    weeks = 0
    if month:
        today = datetime.date.today()
        month_no = _MONTHS.index(month) + 1
        year = today.year + (1 if month_no <= today.month else 0)
        # Round the weeks up: a fortnight and a day left is three paydays, not two.
        weeks = -(-(datetime.date(year, month_no, 1) - today).days // 7)
    if goal and weeks >= 2:
        a_week = -(-goal // weeks)
        return ("£%s by %s is about £%s a week over the %s weeks left — a standing order for that "
                "on payday moves it without you deciding again, and any bonus, refund or bill that "
                "goes down only shortens it."
                % (_comma(goal), month.capitalize(), _comma(a_week), _comma(weeks)))
    if goal:
        # A goal with no date still deserves a figure: what the rate the person named does to it.
        worked = _time_to_save(memory, understood)
        if worked:
            return worked
    if _target(text) or _goal_from_user(memory, 0) or _goal_already_named(memory):
        return None  # a sum with no rate and no date: another entry owns that answer
    if not _MONEY_SUBJECT.search(text):
        # A week of something that is not money: "how many days in a week should i run",
        # "how much exercise a week is enough". The entry matched on "a week" and "should", and
        # the answer it gave was about a standing order.
        return None
    # The line names no total, so the answer is the share people are told to aim at rather than
    # a question back: "how much should i put by each week" wants a number to start from.
    return _share_of_pay(text)


def _share_of_pay(text):
    """"How much should i put by each week" names no total, so the answer is the share.

    The line asks for a number and the honest number is the one people are told to aim at: a
    tenth to a fifth of what comes in. Asking for the total first was the old reply, and it
    answers a question nobody asked - they want to know where to start.
    """
    a_week = bool(re.search(r"\b(?:a|per|each|every)\s*week\b|\bweekly\b", text))
    if a_week:
        return ("A tenth to a fifth of what you take home is the usual amount to put by: on "
                "£2,000 a month that is £50 to £90 a week, and a standing order for the day after "
                "payday moves it before you can spend it. If that is too much this month, take the "
                "fixed amount you would not miss and raise it by £5 whenever a bill drops.")
    return ("A tenth to a fifth of what you take home is the usual amount to put by: £200 to £400 "
            "a month on £2,000, in a separate account with a standing order for the day after "
            "payday so it leaves before you can spend it. If that is too much this month, take the "
            "fixed amount you would not miss and raise it by £5 whenever a bill drops.")


# A small repeated purchase is the money question people most often get wrong by counting it
# weekly instead of yearly, so the domain turns a habit into a number: a price and a frequency
# when the line gives them, the going rate for the named thing when it does not.
_NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
                 "eight": 8, "nine": 9, "ten": 10}
_COUNT_WORDS = {1: "once", 2: "twice", 3: "three", 4: "four", 5: "five", 6: "six",
                7: "seven", 8: "eight", 9: "nine", 10: "ten"}

_GOING_RATE = (("coffee", 3.5), ("latte", 3.5), ("cappuccino", 3.5), ("flat white", 3.5),
               ("meal deal", 4.0), ("sandwich", 5.0), ("lunch", 7.0), ("takeaway", 11.0),
               ("takeaways", 11.0), ("deliveroo", 11.0), ("just eat", 11.0), ("snack", 1.5),
               ("cigarettes", 15.0), ("fags", 15.0), ("vape", 6.0), ("pint", 5.5),
               ("beer", 5.5), ("bottle of wine", 7.0))


def _number(word):
    word = str(word).lower()
    if word.isdigit():
        return int(word)
    return _NUMBER_WORDS.get(word, 0)


def _pounds(amount):
    """£3.50 rather than £3.5, and £4 rather than £4.00."""
    return "£%.2f" % amount if round(amount, 2) != int(amount) else "£%d" % amount


# A sum that is to be *spent* on food rather than saved: "i have 20 pound to feed us for a week",
# "we have 30 quid to get us to friday", "what can i make for dinner with no money". All three
# were answered elsewhere - the savings card ("For £50: one month at £50 a month") because a sum
# and a week is how a goal is said, a country because a bare "us" for a week is also how a trip
# is said, and a shrug. The words below are the "make it last" half; the second half is the
# thing the money has to cover, so a line that says when it has to last but not what for is
# left to the row that knows.
# A month with no figure in it: see the guard on the money-to-last row below.
_A_MONTH_NAMED = re.compile(r"\b(?:this|next|every|each|a|the) month\b|\bmonthly\b")
_A_SUM_NAMED = re.compile(r"£|\b\d+\b|\bpounds?\b|\bquid\b|\btenner\b|\bfiver\b")
# ...but a month with no figure in it is only the bare version of the question when the line
# does not say what the money has to cover. "i have no money for food this month", "i have no
# money to feed my kids this month" and "i have nothing for dinner and no money this month" name
# a month and no sum, and they are the food bank's line - standing that row down sent the first
# to the goat-feeding card ("brambles, hedge, leaves, bark"), the second to a cheaper tariff and
# the third to "Got it." The thing to cover is what keeps them where they were.
_A_THING_TO_COVER = re.compile(
    r"\b(?:food|foods|feed|feeding|eat|eating|dinner|tea|supper|lunch|breakfast|meals?|"
    r"groceries|grocery|shop|shopping|supermarket|kids?|children|child|family|families|baby|"
    r"nappies|nappy|formula|rent|bills?|electric|electricity|gas|heating|oil|coal|wood|"
    r"petrol|diesel|fares?|travel|bus|train|school|uniform|clothes|nursery|childcare|"
    r"medicines?|prescription)\b", re.I)


def _a_month_and_no_sum(understood):
    line = understood["clean"]
    if not _A_MONTH_NAMED.search(line) or _A_SUM_NAMED.search(line):
        return True
    return bool(_A_THING_TO_COVER.search(line))


MAKE_IT_LAST = (
    "to last", "make it last", "make it go", "make that last", "to feed us", "to feed me",
    "to feed my", "to feed the", "to feed a family", "to feed a", "feed a family",
    "feed my family", "feed us", "feed four", "feed two", "left for food", "left to spend",
    "to get us to", "to get me to", "to get through", "get us through", "tide us over",
    "tide me over", "til payday", "until payday", "till payday", "til friday", "until friday",
    "till friday", "no money", "no money for food", "nothing for food", "not much money",
    "pound to", "quid to", "pounds to", "for a tenner", "for a fiver", "a tenner", "a fiver",
    "money for food", "food money", "budget for food", "cheap week", "on the cheap",
    # The same ask said with "last" as the verb, which is how most people say it: "how do i make
    # 20 pound last a week", "we have 100 pound left for the month", "how far does 30 pound go".
    "pound last", "quid last", "pounds last", "last a week", "last a fortnight", "last me",
    "last us", "last until", "last till", "pound go", "quid go", "go for food", "left for",
    "left this week", "pound for food", "quid for food", "no food", "nothing to eat",
    "feed 4", "feed 2", "feed 3", "feed people", "feed the family", "feed a family of",
    "for food today", "for food this week",
    # A shop that has to cover a week is the same question said with the week as an owner rather
    # than as a deadline: "i have 20 pounds for a weeks food" went to the savings card and came
    # back as "£20 at £87 a month ... a standing order the day after payday", which is the answer
    # for money being put away, not for money being spent on dinners. The bare "for a week" is
    # NOT added: it also reads "cheap meals for a week", which has its own answer, so the phrase
    # has to carry the figure with it.
    "weeks food", "week's food", "weeks shop", "weeks shopping", "week of food",
    "pounds for a week", "pounds for the week", "quid for a week", "quid for the week",
    "pound for a week", "pound for the week", "tenner for the week", "fiver for the week",
)

# What the money has to cover. "pound", "quid" and "week" are here as well as in the phrases
# above, because "we have 30 quid to get us to friday" says the sum and the deadline and never
# says food at all.
MONEY_TO_COVER = (
    "food", "eat", "eating", "dinner", "dinners", "cook", "cooking", "meal", "meals", "tea",
    "lunch", "breakfast", "feed", "feed us", "pound", "quid", "pounds", "money", "cash",
    "fiver", "tenner", "week", "weekly", "fortnight", "month", "friday", "payday", "spend",
    "spending", "budget", "groceries", "supermarket", "shop", "shopping", "left",
)

# Money that is going on a thing that is not food is not a sum that has to feed anybody:
# "i have 20 pound to spend on a coat" was answered "£20 over a week is £2.86 a day. Buy the
# staples first". The bare money words above cannot tell the two apart, so the object does.
_A_SPEND_ON_A_THING = re.compile(r"\bto spend\b|\bspend (?:it )?on\b|\bspending on\b|"
                                 r"\bspend on\b")
_A_FOOD_WORD = re.compile(r"\b(?:food|eat|eating|dinner|dinners|tea|lunch|breakfast|supper|"
                          r"meal|meals|cook|cooking|feed|groceries|supermarket|shop|shopping|"
                          r"eat|trolley|staples)\b")

# A day to fill rather than a dinner to find: "what should i do this weekend i have no money"
# and "i have a week off and no money" were told to go to a food bank, and the cheap-week staples
# before that. Neither is what was asked - the free-things-to-do answer is, and it is the row
# this one stands down for.
# A birthday, a present or an afternoon out with somebody: a thing to do for a person rather than a
# week to feed. "i have no money for my kids birthday" and "i want to do something nice with my mum
# but i have no money" were both answered "Use a food bank this week rather than going without",
# which is alarming for a birthday and no help with the question that was asked.
_AN_OCCASION_OR_A_TREAT = re.compile(
    r"\bbirthdays?\b|\bpresent\b|\bpresents\b|\bgift\b|\bgifts\b|\bchristmas\b|"
    r"\btreat\b|\bsomething nice\b|\bsomething special\b|\ba day out\b|\bday out\b|"
    r"\btake (?:my|the|her|him|them|us) \w+ out\b|\bout for (?:a|an) "
    r"(?:meal|drink|drinks|coffee|lunch|dinner)\b|\banniversary\b|\bhen do\b|\bstag do\b")

# A birthday with little in the house is its own question, and neither of the cards next door
# answers it. "my sons birthday is coming and i have no money" stood this row down and fell
# through to a card that asks "Lovely. Are you seeing them for it?", and "my kids birthday is
# coming up and money is tight this year" got a savings plan - five pounds a week by standing
# order. What the person needs is how to mark the day with what is there, so the birthday and the
# thin week together are answered here rather than handed on.
_A_BIRTHDAY = re.compile(r"\bbirthdays?\b")
_A_THIN_WEEK = re.compile(
    r"\bno money\b|\bnothing (?:much|left|at all)\b|\bnot much\b|\bbroke\b|\bskint\b|"
    r"\btight\b|\bcheap\b|\bbudget\b|\bcan'?t afford\b|\bcant afford\b|\blittle\b")

_A_BIRTHDAY_WITH_LITTLE = (
    "A birthday with no money in the house is still a birthday - what a child remembers is that "
    "somebody noticed. Bake the cake yourself: a plain sponge is flour, sugar, butter and eggs, "
    "about a pound, and candles on it make it a cake. One present they choose themselves in a "
    "charity shop usually beats three surprises, and a day out that costs nothing - a park, a "
    "beach, a walk with a flask - is the party. Nothing on a credit card for it: a birthday paid "
    "for on plastic is still being paid for at Christmas. Tell me how old they are turning and I "
    "will say what they would like.")

# How much a present should cost is a budget line, and the figures are right for a friend, a
# colleague or a sibling. They are not right for a child's birthday in a thin week:
# "my daughters birthday is next week and i cant afford much" was told that ten to fifteen pounds
# covers a secret santa. The child and the thin week are the two things that make this the
# birthday-to-mark question, so it goes there instead.
_GIFT_BUDGET = (
    "Roughly £10 to £15 covers a secret santa or a colleague, £20 to £30 a friend or a "
    "nephew, £30 to £60 a close friend or a sibling, and £50 to £100 a partner or a "
    "parent. Fix a total for the year before December and divide it per person, and agree a "
    "cap out loud with a group: the number is a budget line, not a measure of how much you "
    "like someone.")

_A_CHILD = re.compile(r"\b(?:son|sons|daughter|daughters|kid|kids|child|children|boy|girl|"
                      r"little one|stepson|stepdaughter)\b")


def _a_gift_budget(memory, understood):
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if _A_BIRTHDAY.search(text) and _A_CHILD.search(text) and _A_THIN_WEEK.search(text):
        return _A_BIRTHDAY_WITH_LITTLE
    return _GIFT_BUDGET


_ASKS_FOR_SOMETHING_TO_DO = re.compile(
    r"\b(?:this weekend|at the weekend|next weekend|weekend|week off|day off|time off|"
    r"holiday|bored|something to do|anything to do|nothing to do|things to do|"
    r"keep (?:the )?kids|entertain|fun|days out|day out)\b")

# A fiver borrowed is not a fiver spent, and nothing to do with how long it lasts.
NOT_SPENT_ON_FOOD = (
    # "a tenner" is in MAKE_IT_LAST, so "how do i work out the change from a tenner" was a
    # sum that has to last, and it was answered with a week of cheap dinners. The change is
    # the other question about a tenner, and the count-up row answers it.
    "change from", "the change", "my change", "count back", "count up", "count out",
    "wrong change", "give change", "giving change", "change should",
    "borrow", "borrowed", "lend", "lending", "loan", "pay back", "paying back", "repaid",
    "owe", "owes", "how long does", "use by", "in the fridge", "freezer burn", "expire",
    "calories", "calorie", "diet", "lose weight", "how long will", "how long do",
)

# One sum in two currencies is an exchange rate, not a budget: "convert 20 pounds to euros" and
# "how much is 300 euros in pounds" both name a second currency, and any money row that reads
# "pounds" as money to spend has to stand down for them.
ANOTHER_CURRENCY = (
    "euro", "euros", "dollar", "dollars", "usd", "eur", "yen", "cents", "currency",
    "exchange rate", "exchange", "convert", "conversion", "to the pound", "to the euro",
)

# Nothing coming in at all is the food bank; a thin week is the plan. "no money", "nothing to
# eat" and "cant afford" say the first; "cheap week" and "skint" say the second.
_ASKS_WHAT_TO_COOK = re.compile(r"\bwhat (?:can|could|should|shall|do) i (?:cook|make|eat|have)|"
                                  r"\bwhat to (?:cook|make|eat)|\bmeal ideas?\b|"
                                  r"\bwhats for (?:dinner|tea|supper)\b")
_SAYS_NOTHING_AT_ALL = re.compile(r"\bno money\b|\bnothing to eat\b|\bnothing for food\b|"
                                  r"\bno food\b|\bcan'?t afford\b|\bcant afford\b|"
                                  r"\bnothing at all\b|\bnothing left\b")

# A week away is not a week of dinners. "cheap week in march", "a cheap week in spain" and
# "cheap week abroad" are travel questions, and the month or the place is what says so: this
# row keeps "cheap week" as a phrase, and it was answering them all with the food bank.
_A_TRIP = re.compile(r"\bholiday|\bholidays\b|\babroad\b|\bflights?\b|\bhotel\b|"
                     r"\b(?:week|weekend|days?)\s+away\b|\bin the sun\b|"
                     r"\b(?:in|for|during|by|next|early|late)\s+"
                     r"(?:january|february|march|april|may|june|july|august|september|"
                     r"october|november|december)\b")

# A budget that is stated rather than worked out: "my budget for food is 40 pound a week" was
# answered "£40 over 7 days is £5.71 a day" when the useful reply is what a week of food costs.
_A_STATED_BUDGET = re.compile(r"\b(?:my|our|the)\s+(?:food\s+)?budget\b|\bbudget for food\b"
                              r"|\bfood budget\b")
# The cost of the week rather than a sum of theirs to divide up: "how much does a week of food
# cost for one person" and "how much should i budget for food" are asking for the going rate,
# and money's food-bill row is where the rate lives.
_ASKS_THE_PRICE = re.compile(r"\bhow much (?:does|do|is|are|would|will)\b|"
                             r"\bhow much should i (?:spend|budget|pay|set aside)\b|"
                             r"\bhow much (?:a|per|each)\b|\bcost of\b|\bcosts?\b|"
                             r"\bwhat does (?:\w+ ){0,4}cost\b|\bhow expensive\b|"
                             r"\bprice of\b|\baverage (?:cost|spend|bill|shop)\b|"
                             r"\bwhat'?s the average\b|\bhow much do (?:you|people)\b|"
                             r"\b(?:good|normal|typical|reasonable|sensible)\s+(?:\w+\s+)?"
                             r"(?:budget|spend|amount to spend)\b|"
                             r"\ba (?:food\s+)?budget (?:for|of)\b|"
                             r"\bwhat should i (?:spend|budget|set aside)\b")
_ASKS_HOW_LONG = re.compile(r"\b(?:last|make it go|get through|get us to|til|until|till|"
                            r"skint|left|cheap|no money|stretch)\b")

# Nothing coming in at all, said as a state rather than as a sum: "i have no money for food this
# week", "nothing left", "i have 0 pounds". A length of time on the line used to be enough on
# its own, so a person with nothing was handed the staples to buy - the one thing they cannot do.
# The food bank is the answer for this shape, and it needs to hear the line say it.
_NO_MONEY = re.compile(
    r"\bno money\b|\bnot got any money\b|\bhav(?:e|ing) n(?:o|ot any) (?:money|cash)\b|"
    r"\bnothing (?:left|at all|to my name)\b|\bnowt\b|\bnada\b|\bzero\b|\b£0\b|"
    r"\b0 pounds\b|\bnothing coming in\b|\bdidnt get paid\b|\bdidn't get paid\b|"
    r"\bbenefits? (?:hasnt|hasn't|havent|haven't) (?:come|been paid)\b|"
    r"\bcant afford (?:any )?food\b|\bcan't afford (?:any )?food\b|"
    r"\bcan't afford to eat\b|\bcant afford to eat\b|\bno food in the (?:house|cupboard)\b|"
    r"\bnothing to eat\b|\bnot eating (?:today|tonight)\b|\bskip(?:ping)? meals?\b")

_CHEAP_DINNERS = ("tomato pasta, lentil dhal, egg fried rice, jacket potato with beans, "
                 "chickpea curry")
# The buy order, because the per-day sum on its own tells nobody what to put in the trolley.
# A receipt question is about the proof of purchase, and money's general refund row answered it
# because the "without a receipt" clause is the one part of the line the reading sets aside:
# "how do i return something without a receipt" got the 30-day faulty-goods law, which never
# mentions a receipt and leaves the actual worry unanswered. shopping's return-without-receipt
# owns that question, so this row stands down for the whole family of proof-of-purchase words -
# a bank or card statement is the other way a person proves a purchase, and "can i return
# something with a bank statement" was the 30-day law on the branch that first added the guard.
# An order confirmation is left out on purpose: "can i return something with an order
# confirmation" is how a delivery not arrived is asked, and the delivery rows own that.
_A_RECEIPT_QUESTION = re.compile(
    r"\b(?:receipt|receipts|proof of purchase|paper slip|bank statement|card statement)\b")


def _a_receipt_question(understood):
    """True when the line is about the proof of purchase, which another row answers."""
    if not isinstance(understood, dict):
        return False
    said = "%s %s" % (understood.get("text") or "", understood.get("clean") or "")
    return bool(_A_RECEIPT_QUESTION.search(said.lower()))


_CHEAP_WEEK = ("Buy the staples first - rice, pasta, tinned tomatoes, lentils, eggs, oats, "
               "potatoes, frozen veg - and build the week from them: " + _CHEAP_DINNERS + ". "
               "A whole chicken does a roast, then sandwiches, then soup, and cooking double "
               "means two days are already done.")

# The figure in a line, as people write it: "£20", "20 pound", "30 quid", "a tenner", "a fiver".
_THE_FIGURE = re.compile(r"£\s*([0-9][0-9,]*(?:\.[0-9]+)?)"
                        r"|\b([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:pounds?|quid|bucks)\b", re.I)
_WORD_FIGURES = (("a tenner", 10), ("tenner", 10), ("a fiver", 5), ("fiver", 5),
                 ("a score", 20))

# How long the money has to last, in days, from the words people use. A named deadline is
# counted from today, because "til friday" said on a Tuesday is three days and not five.
_SPANS = (("a fortnight", 14), ("two weeks", 14), ("a month", 30), ("for the month", 30),
          ("this month", 30), ("a week", 7),
          ("this week", 7), ("ten days", 10), ("a few days", 4), ("the week", 7),
          # last, because "this week" and "a week" are the spans people mean when a day is
          # named as well: "i have 5 pound for food today" is one day and only one.
          ("today", 1), ("tonight", 1))
_DEADLINES = ((("monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
                "sunday"), None),
              ("payday", None), ("the weekend", 5), ("weekend", 5))
_WEEKDAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4,
             "saturday": 5, "sunday": 6}
# A sum and a meal with no length at all: "what can i make for dinner for a fiver" is one dinner
# for however many are eating, and dividing it by a week nobody named answers a question the
# person did not ask.
_A_MEAL = re.compile(r"\b(?:dinner|dinners|tea|lunch|supper|breakfast|cook|cooking|make|"
                     r"meal|meals|eat|eating)\b")

# "feed four for a tenner" is a meal for four people, not a four-person week: the per-head share
# is the figure the person asked for.
_A_HEADCOUNT = re.compile(r"\b(?:feed|for|cook for|serves?)\s+(\d{1,2}|one|two|three|four|"
                          r"five|six|seven|eight|nine|ten|eleven|twelve)\b"
                          r"|\b(\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|"
                          r"eleven|twelve)\s+(?:people|of us|adults|mouths)\b"
                          r"|\bfamily of\s+(\d{1,2}|one|two|three|four|five|six|seven|eight)")
_HEAD_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
               "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}


def _a_headcount_in(text):
    """How many people the line says are eating, or 0 when it says nobody."""
    found = _A_HEADCOUNT.search(text)
    if not found:
        return 0
    said = next((group for group in found.groups() if group), "")
    if said.isdigit():
        return int(said)
    return _HEAD_WORDS.get(said, 0)


def _money_to_last(memory, understood):
    """A sum of money and a length of time: the per-day sum, then the order to buy in.

    "i have 20 pound to feed us for a week" is arithmetic first - 20 over 7 days is 2.86 a day
    - and then a shopping order, because the figure on its own tells nobody what to put in the
    trolley. With no sum at all ("what can i make for dinner with no money") the honest answer
    is the food bank and the meals that cost about a pound a head.
    """
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if _ASKS_THE_PRICE.search(text) and _A_FOOD_WORD.search(text) \
            and not _ASKS_HOW_LONG.search(text) and not _NO_MONEY.search(text) \
            and not _THE_FIGURE.search(text) \
            and not any(phrase in text for phrase, _ in _WORD_FIGURES):
        return None  # a food bill is asked for the going rate, and the food-bill row has it
    if _A_STATED_BUDGET.search(text) and not _ASKS_HOW_LONG.search(text):
        return None  # "my budget for food is 40 pound a week" wants the going rate, not a division
    if _A_SPEND_ON_A_THING.search(text) and not _A_FOOD_WORD.search(text):
        return None  # the money is going on a thing, not on feeding anyone
    if _ASKS_FOR_SOMETHING_TO_DO.search(text) and not _A_FOOD_WORD.search(text):
        return None  # a day to fill, not a week to feed
    if (_A_BIRTHDAY.search(text) and _A_THIN_WEEK.search(text)
            and not _A_FOOD_WORD.search(text)):
        return _A_BIRTHDAY_WITH_LITTLE  # a birthday on nothing is not a week to feed, and not a punt
    if _AN_OCCASION_OR_A_TREAT.search(text) and not _A_FOOD_WORD.search(text):
        return None  # a birthday or an afternoon out, not a week's shopping
    amount = 0
    for match in _THE_FIGURE.finditer(text):
        amount = float((match.group(1) or match.group(2)).replace(",", ""))
        break
    if not amount:
        for phrase, figure in _WORD_FIGURES:
            if phrase in text:
                amount = figure
                break
    if not amount and _A_TRIP.search(text) and not _A_FOOD_WORD.search(text):
        # A week away is travel, unless a sum is named: "we have 300 pound to last a week on
        # holiday" is the arithmetic this row does, and the trip words only say where it goes.
        return None
    days = 0
    named = ""      # the days are the line's own
    assumed = ""    # the days are a guess, so the reply has to say it is one
    for phrase, span in _SPANS:
        if phrase in text:
            days, named = span, phrase
            break
    if not days:
        for phrase, span in _DEADLINES:
            phrases = phrase if isinstance(phrase, tuple) else (phrase,)
            found = next((word for word in phrases if word in text), "")
            if found:
                if span:
                    days, named = span, found
                elif found in _WEEKDAYS:
                    # "til friday" said on a Tuesday is three days, not a fixed four: a named day
                    # is counted from today, which is what the comment above _SPANS says.
                    today = datetime.date.today()
                    days = (_WEEKDAYS[found] - today.weekday()) % 7 or 7
                    named = found
                else:
                    # Payday is another fortnight for most people, but telling somebody their
                    # £20 is £1.43 a day for a fortnight they never mentioned is a fact they
                    # did not give. Said as the guess it is, it still answers the question.
                    days, assumed = 14, "payday"
                break
    heads = _a_headcount_in(text)
    if not amount and _NO_MONEY.search(text):
        # Nothing in and a length to get through: the staples are advice for somebody with a
        # little, so the free route comes first and the cooking comes after it.
        return ("Use a food bank this week rather than going without: the Trussell Trust site "
                "finds the nearest one and a voucher comes from a GP, a school or Citizens "
                "Advice, and it costs you nothing. Have a look in the cupboard before you go - "
                "rice, pasta, oats and tinned beans still make a dinner: " + _CHEAP_DINNERS +
                ".")
    if amount and days == 1:
        return ("%s for a day is not much of a shop: one big dinner cooked in double does two "
                "meals, and the cheapest of them are %s. Buy from that list and nothing else "
                "and the day comes in under the figure." % (_pounds(amount), _CHEAP_DINNERS))
    if amount and days and assumed == "payday":
        return ("If payday is a fortnight off, %s is %s a day. %s"
                % (_pounds(amount), _pounds(round(amount / days, 2)), _CHEAP_WEEK))
    if amount and days and named:
        return ("%s over %d days is %s a day. %s"
                % (_pounds(amount), days, _pounds(round(amount / days, 2)), _CHEAP_WEEK))
    if amount and days:
        return ("%s for %d days is %s a day. %s"
                % (_pounds(amount), days, _pounds(round(amount / days, 2)), _CHEAP_WEEK))
    if amount and heads:
        # "feed four for a tenner" asks for a meal for four people. A week nobody named turned
        # it into £1.43 a day for a family of four, which is not a shop anybody can do.
        return ("%s for %d is %s a head, which is one of these each: %s. If it has to stretch "
                "to a week as well, that is %s a day, and the staples are what make that work: "
                "rice, pasta, lentils, eggs, oats, potatoes, frozen veg."
                % (_pounds(amount), heads, _pounds(round(amount / heads, 2)), _CHEAP_DINNERS,
                   _pounds(round(amount / 7, 2))))
    if amount and _A_MEAL.search(text):
        # One meal for the money, and the arithmetic named as what it would take to stretch it.
        return ("%s is one dinner for two with change, or two for one: %s. It will not cover a "
                "week - tell me how long it has to last and I will work the days out."
                % (_pounds(amount), _CHEAP_DINNERS))
    if amount:
        # A sum and no length: a week is the length people mean, so it is said as an assumption
        # and not as something the person told us.
        return ("If that has to last a week, %s is %s a day. %s"
                % (_pounds(amount), _pounds(round(amount / 7, 2)), _CHEAP_WEEK))
    if days:
        # A deadline and no figure: "im skint til friday wot can i cook" is the cheap week, and
        # the food bank is for the line that says there is nothing coming at all.
        return ("Short until then is the cheap week, and it needs no more than the staples: "
                "buy the staples first - rice, pasta, tinned tomatoes, lentils, eggs, oats, "
                "potatoes, frozen veg - and build the days from them: " + _CHEAP_DINNERS + ".")
    # No sum and no date. "im on a cheap week" and "what can i cook on a cheap week" are the
    # plan, not the food bank: a cheap week is staples plus a list of dinners built on them. The
    # food bank is said only to the line that says there is nothing coming at all, and even then
    # the meals it costs about a pound a head are said with it.
    plan = ("A cheap week is the staples first - rice, pasta, tinned tomatoes, lentils, eggs, "
            "oats, potatoes, frozen veg - and the dinners built on them: " + _CHEAP_DINNERS + ". "
            "Cook double and the week costs less per meal than the ready meals do.")
    if not _SAYS_NOTHING_AT_ALL.search(text):
        return plan
    if _ASKS_WHAT_TO_COOK.search(text):
        # A cooking question with nothing in the house gets the meals first: the food bank is
        # right for somebody who says there is no money at all, but it is not a recipe, and the
        # ask is what to cook. It is still said, after the cooking.
        return ("Cooking with nothing in is the staples and the dinners built on them. " +
                _CHEAP_WEEK + " If there is nothing coming in at all, a food bank is there for "
                "this week and a voucher comes from a GP, a school or Citizens Advice.")
    return ("Use a food bank this week rather than going without: the Trussell Trust site finds "
            "the nearest one, and a voucher comes from a GP, a school or Citizens Advice. About "
            "a pound a head still covers a dinner: " + _CHEAP_DINNERS)


def _habit_cost(memory, understood):
    """"What does a daily coffee cost me a year" is arithmetic, not a lecture on budgeting."""
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    smoking = any(word in text for word in ("smok", "cigarette", "fag", "vape", "vaping"))
    price = _sum_and_unit(text, ("a day", "per day", "each day", "daily"))
    a_day = bool(price)
    monthly = 0
    if not price:
        monthly = _sum_and_unit(text, ("a month", "per month", "monthly"))
    if not price:
        price = _sum_and_unit(text, ("a week", "per week", "each week", "weekly"))
    times = 0
    match = re.search(r"\b(\d+|" + "|".join(_NUMBER_WORDS) + r")\s+(?:days|times|mornings|"
                      r"lunches|coffees|takeaways|pints)\s+(?:a|per|each)\s+week", text)
    if match:
        times = _number(match.group(1))
    elif re.search(r"\bonce\s+(?:a|per|each)\s+week\b", text):
        times = 1
    elif re.search(r"\btwice\s+(?:a|per|each)\s+week\b", text):
        times = 2
    if not price and smoking:
        # Nobody smokes five days a week: a pack is about £15, so it is a daily habit.
        return ("A pack of 20 is about £15 now, so ten a day is roughly £2,700 a year and a pack "
                "a day about £5,500. Stopping is the single biggest bill most smokers can cut, "
                "and a free stop-smoking service through your GP doubles your odds.")
    if not price and re.search(r"\b(?:every|each|a|per)\s+day\b|\bdaily\b", text):
        a_day = True
    if not price:
        price = 0
        for word, going in _GOING_RATE:
            if word in text:
                price = going
                break
        if not price:
            return None
    if monthly:
        year = monthly * 12
        return ("£%s a month is £%s a year. Halving it is £%s back over the year."
                % (_comma(monthly), _comma(year), _comma(year / 2.0)))
    if a_day:
        year, week = price * 365, price * 7
        line = "%s a day is about £%s a year" % (_pounds(price), _comma(year))
        return ("%s, about £%s a week. Cutting two of them a week is £%s back over the year."
                % (line, _comma(week), _comma(price * 2 * 52)))
    if times:
        year = price * times * 52
        when = {1: "once a week", 2: "twice a week"}.get(times) or "%s times a week" % (
            _COUNT_WORDS.get(times, times))
        line = "%s %s is about £%s a year" % (_pounds(price), when, _comma(year))
        if times == 1:
            return "%s, so skipping it every other week is £%s back over the year." % (
                line, _comma(price * 26))
        if times == 2:
            return ("%s. Swapping one a week for something from home is £%s back over the year."
                    % (line, _comma(price * 52)))
        return ("%s. Cutting two of them a week is £%s back over the year."
                % (line, _comma(price * 2 * 52)))
    year = price * 52
    return ("%s a week is about £%s a year, £%s a month. Skip it every other week and it is £%s "
            "back over the year."
            % (_pounds(price), _comma(year), _comma(year / 12.0), _comma(price * 26)))


def _comma(amount):
    return "{:,}".format(int(amount))


# What the shopping for a home-cooked dish comes to, at ordinary supermarket prices. Two tables:
# the dishes people cost by the portion, and the bakes they cost as a whole. The figure is a
# rough one on purpose - a shop has today's price and I do not - but "a chilli for four is about
# £6, so £1.50 a head, and the mince is most of it" is the helpful answer, and "prices move too
# fast for me to know" is not. The shop's own prices change weekly, so the reply says which half
# of the cost it is that can be halved.
_DISH_COST_PORTION = (
    # (names, pounds a head, what the money mostly goes on)
    (("chilli con carne", "chili con carne"), 1.60,
     "the mince is most of it, and a version made with lentils or beans is about half"),
    (("chilli", "chili"), 1.60, "the mince is most of it, and a lentil chilli is about half"),
    (("spaghetti bolognese", "spag bol", "bolognese"), 1.40,
     "the mince is half of it, and the pasta and a tin of tomatoes are the rest"),
    (("lasagne", "lasagna"), 1.70, "the mince and the cheese are most of it"),
    (("cottage pie", "shepherds pie", "shepherd's pie"), 1.50,
     "the mince is half of it and the potatoes are most of the rest"),
    (("fish pie",), 2.00, "the fish is nearly all of it, so frozen fish makes it much cheaper"),
    (("roast chicken", "roast dinner", "sunday roast", "roast"), 2.30,
     "the joint is half of it, and the leftovers make a second dinner"),
    (("curry",), 1.50, "the meat is most of it, and a dhal or chickpea curry is under a pound"),
    (("dhal", "dal", "lentil"), 0.60, "lentils and a tin of tomatoes are nearly all of it"),
    (("soup",), 0.50, "a bag of vegetables and a stock cube is the whole cost"),
    (("pizza",), 0.90, "the flour and the cheese are most of it, and the oven is the rest"),
    (("stew", "casserole"), 1.50,
     "the meat is most of it, and the cheaper cuts come out better in a stew anyway"),
    (("risotto",), 1.00, "the rice is cheap and the parmesan and the wine are the rest"),
    (("stir fry",), 1.25, "the meat is most of it, and frozen veg does the same job for less"),
    (("macaroni cheese", "mac and cheese"), 0.85, "the cheese is most of it"),
    (("sausage and mash",), 1.10, "the sausages are most of it"),
    (("toad in the hole",), 1.10, "the sausages are most of it"),
    (("pancakes",), 0.30, "flour, eggs and milk, and nothing else"),
    (("porridge",), 0.20, "oats and water, so the milk and the fruit are the rest"),
)

_DISH_COST_WHOLE = (
    # (names, pounds for the whole bake, what it makes, what the money goes on)
    (("victoria sponge", "sponge cake", "cake"), 3.50, "an 8-slice sponge",
     "the butter and the eggs are nearly all of it"),
    (("scones",), 1.20, "a dozen scones", "flour, butter and milk are nearly all of it"),
    (("brownies",), 2.80, "a tray of 16", "the chocolate and the butter are most of it"),
    (("bread", "loaf"), 0.55, "a large loaf",
     "a bag of flour and a sachet of yeast make three of them, so the oven is the rest of the "
     "cost"),
)


def _the_dish_named(text):
    """The longest dish name in the line, with its row, or None.

    The longest name wins because "chilli con carne" is a dish and "chilli" alone is mostly a
    spice: a line that names the dish is read as the dish however many shorter names sit inside
    it.
    """
    text = str(text or "").lower()
    best = None
    for names, figure, note in _DISH_COST_PORTION:
        for name in names:
            if re.search(r"\b%s\b" % re.escape(name), text) and (
                    best is None or len(name) > len(best[0])):
                best = (name, False, figure, "", note)
    for names, figure, makes, note in _DISH_COST_WHOLE:
        for name in names:
            if re.search(r"\b%s\b" % re.escape(name), text) and (
                    best is None or len(name) > len(best[0])):
                best = (name, True, figure, makes, note)
    return best


def _money(amount):
    """55p rather than £0.55, and £6.50 rather than £6.5: a shopping figure as people say it."""
    if round(amount, 2) < 1:
        return "%dp" % int(round(amount * 100))
    return _pounds(amount)


def _dish_to_cook_cost(memory, understood):
    """What the shopping for a named dish costs, for the number of people the line says.

    "how much does a chilli cost to make", "how much would a sunday roast cost for 6" and "what
    does a chilli cost per portion" are one question, so one row answers all three: the figure,
    the people in the line, and which part of it is worth cutting.
    """
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "")
    # "is 2 pounds expensive for a loaf of bread" judges the price of the loaf on the shelf, and
    # what the flour and the oven cost to make one is a different question about the same food.
    if a_price_is_judged(text):
        return None
    named = _the_dish_named(text)
    if not named:
        return None
    name, whole, figure, makes, note = named
    caveat = "Shop prices move by the week, so that is the shape of it rather than a quote."
    if whole:
        return ("Ingredients for %s come to about %s, and %s. %s"
                % (makes, _money(figure), note, caveat))
    people = _crowd(text) or 4
    if people < 2:
        people = 4
    # A shopping figure is not a quote: the nearest 10p a head, and the nearest 50p for the shop,
    # are as precise as a supermarket price a week out can be.
    per_head = round(figure, 1)
    total = round(per_head * people * 2, 0) / 2.0
    if people == 4:
        return ("About %s for four, so %s a head: %s. %s"
                % (_money(total), _money(per_head), note, caveat))
    return ("About %s a head, so %s for %s: %s. %s"
            % (_money(per_head), _money(total), _COUNT_WORDS.get(people, people), note, caveat))


def _goal_already_named(memory):
    """The biggest sum in the answers just given: "and at 200 a month?" after "how long will it
    take to save 5000 pounds" is still about the 5000."""
    best = 0
    for record in (memory or {}).get("entry_answers") or ():
        text = str(record.get("text") or "")
        if "takes:" in text:
            sums = re.findall(r"£([\d,]+)", text)
        else:
            # "Aim for 10% of the price: £20,000 on a £200,000 home" names the 20,000 to aim
            # for, not the price of the house.
            sums = re.findall(AIM_FOR, text)
        for found in sums:
            try:
                value = int(found.replace(",", ""))
            except ValueError:
                continue
            best = max(best, value)
    return best


def _rent_deposit(memory, understood):
    back = ("Ask for it back in writing with photos and the inventory attached; if you disagree, "
            "use the scheme's free dispute service instead of arguing with the agent.")
    amount = ("Five weeks' rent is the legal cap in England, so on £1,200 a month expect about "
              "£1,380. ")
    if "how_much" in (understood.get("asks") or ()) or "how many" in str(understood.get("clean")):
        return (amount + "It has to sit in a government-backed protection scheme within 30 days, "
                "and the landlord must tell you which one. " + back)
    return ("Your deposit must be in a government-backed protection scheme within 30 days, and "
            "the landlord has to tell you which one. " + back)


# The retirement row's second key part holds the plainest question openers, "what is" among
# them, so a line that says "retires" and then asks anything at all reached it: "what is a good
# present for a teacher who retires" was answered with the pot to aim for. A present for
# somebody who is retiring is a present question, not a question about money, whatever else
# the line says.
_A_GIFT_OR_A_PARTY = re.compile(
    r"\b(present|presents|gift|gifts|card|cards|flowers|bouquet|voucher|hamper|mug|"
    r"party|leaving do|leaving present|send off|retirement do|speech|toast)\b")


def _not_a_gift(understood):
    """False when the line is about buying or giving something for a retirement."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "")
    return not _A_GIFT_OR_A_PARTY.search(said.lower())


def _retirement(memory, understood):
    """Which retirement question this is: the pot to aim for, the dates, or the years before them.

    "How much do i need to retire" wants a target, "when can i take my pension" wants the dates,
    and "i want to retire at 62" wants both - the gap between the date they named and the date
    each pot opens is the part people are actually asking about.
    """
    text = str((understood or {}).get("clean") or "").lower()
    if not text:
        text = " ".join(str(one) for one in (understood or {}).get("words") or ())
    target = ("A rough target is 25 times what you want to spend each year on top of the state "
              "pension: \u00a310,000 a year beyond it wants a pot of about \u00a3250,000. ")
    if "state pension" in text and ("how much" in text or "forecast" in text
                                   or "check" in text or "record" in text
                                   or "how many years" in text or "years do i need" in text
                                   or "qualifying" in text or "voluntary" in text
                                   or "buy extra" in text or "fill a gap" in text
                                   or "gap in my record" in text):
        return ("The full new state pension is about \u00a311,500 a year, \u00a3230 a week, if you "
                "have 35 years of contributions; each year short pays about a thirtieth less, and "
                "you need at least 10 years to get anything. Check your own record and forecast "
                "at gov.uk/check-state-pension. " + target.replace(
                    "on top of the state pension", "beyond the state pension"))
    if ("when" in text or "what age" in text or "how old" in text or "pension age" in text
            or "take my pension" in text or "draw" in text or "claim" in text) \
            and "how much" not in text and "enough" not in text:
        return ("Private and workplace pension money opens from 55, and 57 from April 2028; the "
                "state pension starts at 66 now and 67 by 2028. There is no fixed retirement age "
                "in law - your employer cannot push you out at 65 unless the job itself has one "
                "written in - so the dates that matter are the ones on your own forecast at "
                "gov.uk/check-state-pension. " + target)
    early = "early" in text or "before i" in text or "as soon as" in text
    ages = [int(found) for found in re.findall(r"\b(\d\d)\b", text)]
    if early or any(age < 66 for age in ages):
        # "can i retire at 55" is a yes-or-no question and gets its yes first; "i want to retire
        # early" is a plan and reads oddly with one, so only the question carries the verdict.
        lead = ("Yes, if you can bridge the gap. " if "yesno" in (understood.get("asks") or ())
                else "")
        return (lead + "Stopping before the state pension is mostly a bridging problem: the "
                "years between the date you want and the date each pot opens have to be paid for "
                "out of something else. Work out that gap first - private money from 55 (57 from "
                "April 2028), the state pension from 66 or 67 - then cover it with savings, an "
                "ISA or part-time work rather than the pension. " + target +
                "The earlier the date, the more years the pot has to carry, so try the sums at "
                "two or three ages and see which one the money actually allows.")
    return (target + "The full new state pension is around \u00a311,500 a year from 66 or 67, "
            "and you can take private pension money from 55 (57 from 2028), so check your "
            "forecast on the government's pension service before you decide anything.")


def _pension_choice(memory, understood):
    """An annuity, drawdown and a lump sum are three ways to take the same pot, and people ask
    which - so the answer names all three and what each one is for."""
    text = str((understood or {}).get("clean") or "").lower()
    if not text:
        text = " ".join(str(one) for one in (understood or {}).get("words") or ())
    if "drawdown" in text:
        return ("Drawdown keeps the pot invested and pays you an income you choose, so it can run "
                "out if the money does badly or you take too much. Take no more than about 4% a "
                "year to begin with, keep three to five years of spending in cash so you are not "
                "selling investments in a bad year, and remember the pot stays yours to pass on.")
    if "annuit" in text:
        return ("An annuity swaps your pot for a guaranteed income for life: you give the insurer "
                "the money and it pays you a set amount whatever happens to markets or how long "
                "you live. Shop around with an adviser or a broker, because the rate varies a lot "
                "between insurers, and tell them about any health problems - they can raise the "
                "income. It is the safe option rather than the generous one; most people now mix "
                "an annuity for the bills with drawdown for the rest.")
    # The fall-through is the tax-free lump sum, and it is the answer to a line that names one
    # of the three. "what does that mean", said after the drawdown card, names none of them and
    # was reaching this row through the chat's topic once the ask words took a definition - plus
    # "mean" - so the guard says the line has to name what it is asking about.
    if not any(word in text for word in ("annuit", "drawdown", "lump", "25%", "tax free",
                                         "tax-free", "cash in", "release", "pension pot",
                                         "pot")):
        return None
    return ("You can usually take 25% of a defined contribution pot tax-free, up to about "
            "\u00a3268,000 in total, and the rest is taxed as income when you take it. So taking a "
            "big lump sum in one year can push you into a higher tax band: spread it over several "
            "years, and leave the rest invested rather than cashing in the whole pot. Defined "
            "benefit or final salary pensions are different - leave those alone unless an adviser "
            "tells you otherwise, because transferring out is rarely a good deal and needs "
            "regulated advice over \u00a330,000.")


def _budget_split(memory, understood):
    return ("Split what actually lands in your account: fixed bills and food first, then move a "
            "set amount to savings the day you're paid, and treat what's left as the spending "
            "money. The 50/30/20 rule (half needs, a third wants, a fifth saved) is a starting "
            "point, not a law; paying yourself first is the part that works.")


# "Pay my card off" and "pay it off faster" say the same thing as "pay off", so the entry that
# answers a debt payoff accepts each of them as one phrase instead of only the adjacent pair.
PAY_OFF = tuple("pay %s off" % thing
                for thing in ("it", "them", "that", "this", "my card", "my loan", "my mortgage",
                              "my debt", "my credit card", "my overdraft", "my balance",
                              "the card", "the loan", "the mortgage", "the debt")) + (
    "pay off", "paying off", "paid off", "overpay", "overpayment", "pay extra", "extra payments",
    "pay early", "paying early", "pay back", "paying back", "early repayment", "clear it",
    "clear the balance", "clear my balance", "settle early",
    # "clear my card" is the same question the "pay it off" forms ask, and it was reaching no
    # row at all: "should i use my savings to clear my card" got a signpost to a money charity
    "clear my card", "clearing my card", "clear the card", "clear my credit card",
    "clear my credit", "clearing my credit card", "clear my debts", "clear the debt",
    # "repay" is the same verb as "pay off": "should i repay my credit card or save" was reaching
    # no row at all and got the signpost to a money charity, while the "pay it off" wording of the
    # same question got the comparison. The favour-between-friends sense is stood down by
    # `overpay`'s own avoid list ("friend", "lent", "owes me").
    "repay", "repaying", "repaid", "repay it", "repay my card", "repay my credit card",
    "repay the card", "repay my loan", "repay my mortgage", "repay my debt", "repay my debts")

# A line that names both sides of the money question without a payoff verb - "credit card or
# savings first", "savings or clear the card", "clear the card or put it in savings" - is the
# overpay comparison. Written as whole phrases because "savings" alone is not it: a line about a
# savings account or a pension is a different subject.
OR_SAVE = (
    "credit card or savings", "card or savings", "savings or credit card",
    "savings or card", "debt or savings", "savings or debt", "or savings first",
    "card or save", "card or saving", "save or clear", "save or pay", "save or overpay",
    "savings or overpay", "savings or pay", "savings or clear", "savings or mortgage",
    "or clear my card", "or clear the card", "pay off or save", "clear the card or save",
    "clear it or save", "or put it in savings", "or pay the card",
)


# "Card balance" and "pay the minimum" are the credit-card rows' words, and a gift card, a voucher
# and a prepaid card carry a balance too: "check my gift card balance" was told about a 0% balance
# transfer, and then about paying more than the minimum, which are confident replies to a question
# nobody asked. Money already on a card is the shop's or the app's to say, and the composer's own
# line answers it honestly (`MY_RECORDS` in bot/compose/fallback.py). Every card row with a balance
# word takes this, so the line reaches the honest answer rather than the next card entry along.
MONEY_ALREADY_ON_A_CARD = (
    "gift card", "gift cards", "gift voucher", "gift vouchers", "voucher", "vouchers",
    # not "store card": in the shops it is a credit account with a balance owed, and "i pay the
    # minimum on my store card and the balance never moves" is the credit-card-debt question
    "loyalty card", "loyalty points", "points", "prepaid",
    "pre-paid", "prepaid card", "travel money card", "e gift card", "egift",
    "left on", "how much is left", "how much left", "how much is on", "how much is there",
    "how much have i got on", "what is left on", "whats left on", "still on it", "remaining",
    "top up", "top it up", "load it", "reload", "check my balance", "balance on my card",
)


# "spent up" and "spent all my money" are the same subject with a different tense: the money has
# gone, and the useful answer is about the days left rather than the month's bills. `bot/modules/
# chat.py` already reads "spent" as money rather than tiredness when one of these follows it, and
# stands its tiredness reply down, so the turn is the knowledge base's - and nothing here answered
# it, so "im spent up this month" got "I'm listening - say more if it helps".
SPENT_UP = ("spent up", "spent it all", "spent all my money", "spent all of it",
            "spent all my wages", "spent my wages", "spent every penny", "spent my pay",
            "spent all my pay", "spent my money")


# A debt that has come due, in the words people use for it: the thing named (a card, an
# overdraft, a loan) with a payment that cannot be made. A card used at a till is the wallet
# question, and technology.py's row stands down for these lines, so the two never meet.
# A bare "minimum", "only paying" or "just paying" is not one of them: paying the minimum every
# month is a debt that is being met, and the answer to it is to pay more rather than to ring
# anybody. The words here are all about a payment that cannot be made or has gone past.
_DEBT_DUE = re.compile(
    r"\b(cant pay|can't pay|cannot pay|cant make|can't make|missed|miss|missing|forgot|"
    r"forgotten|paid late|pay late|paying late|late payment|payment is late|didnt pay|"
    r"didn't pay|not paid|unpaid|behind on|overdue|"
    r"maxed|maxed out|payment plan|interest freeze|default|defaulted|in arrears|"
    r"struggling with|can't afford|cant afford|dont pay|don't pay)\b")
_A_DEBT = re.compile(
    r"\b(card|credit card|store card|overdraft|debt|debts|loan|loans|payment|payments|"
    r"balance|interest|minimum|payday loan|buy now pay later|klarna|clearpay)\b")


def _A_DEBT_IS_DUE(said):
    """A debt with a payment the person says they cannot meet, or one that has gone past."""
    return bool(_A_DEBT.search(said) and _DEBT_DUE.search(said))

# "im 27 and i have no savings at all", "i have nothing saved and im 30", "never saved a penny" -
# a person saying where their money is, with no question in the line. Nothing answered it: on
# 4ab6d475 all three were "Thanks for telling me - I'm here if you want to dig into any of that",
# a shrug at a person who has just said something they may not have said out loud before. The
# money-trouble row is the same shape (a state, not an ask) but a different state: that one is a
# month with no money left, this one is years with nothing put by, and the useful reply is the
# smallest possible start rather than the two calls that free up cash this week.
#
# Keyed on the phrases people use for the state, never the bare word "savings": "how much should i
# have in savings" is the size of the buffer, "is a cash isa worth it" is the account, "save up for
# a house" is a named target, and those have their own rows.
_NO_SAVINGS = (
    "no savings", "nothing saved", "havent saved", "haven't saved", "hasnt saved", "hasn't saved",
    "never saved", "not saved anything", "nothing put by", "nothing put aside",
    "not a penny saved", "zero savings", "no savings pot", "nothing in savings",
    "nothing in my savings", "never had savings", "never been able to save",
    "never able to save", "never managed to save", "cant save", "can't save", "cannot save",
    "unable to save", "no savings whatsoever", "nothing saved up", "havent saved anything",
    "have nothing saved", "got nothing saved", "no money saved", "nothing in the bank",
    "not a penny put by", "no savings at all",
)

# The rate row stands down for a line that says there is nothing being put by, because
# "i earn 1800 a month and cant save anything" is the gap card's line. It must not stand down
# when the line names a rate it *can* save: "i cant save more than 100 a month how long for
# 2000" is a rate question, and the gap card would tell somebody saving £100 a month that
# nothing is put by. A number in the same phrase as "save"/"put by" and a month or a week is
# that rate; the income in "1800 a month" is not, because it is not the number being saved.
_A_SAVING_RATE = re.compile(
    r"\b(?:save|saving|saved|put by|put away|put aside|set aside)\b[^.!?]{0,30}?"
    r"(\d[\d,]*(?:\.\d+)?)\s*(?:k\b|grand\b|thousand\b)?\s*(?:pounds?|quid)?\s*"
    r"(?:a|per|each|/)\s*(?:month|week)\b", re.I)
# "i cant save anything out of 1800 a month" names the income the saving would come out of,
# not a rate being saved, so the amount is not the rate the gap guard is looking for.
_A_RATE_FROM_INCOME = re.compile(
    r"\b(?:on|from|out of|of|with|earn|earns|earned|earning|make|makes|made|paid|salary|wage|"
    r"income)\b(?:\s+(?:my|our|your|his|her|their|the|a|an|some))?(?:\s+[a-z]+){0,2}\s*$",
    re.I)
_GAP_SAYINGS = ("cant save", "can't save", "cannot save", "unable to save",
                "no savings", "nothing put by")


def _the_rate_row_has_a_rate(understood):
    """False for a line that says nothing is saved and names no rate it can save.

    A line with no gap phrase is the rate row's own question as before. A line with a gap
    phrase stays only when it also names a rate it can save, which is the second half of
    "i cant save more than 100 a month how long for 2000".
    """
    said = " %s " % " ".join(str((understood or {}).get("clean")
                                 or (understood or {}).get("text") or "").lower().split())
    if not any(phrase in said for phrase in _GAP_SAYINGS):
        return True
    for match in _A_SAVING_RATE.finditer(said):
        before = said[max(0, match.start(1) - 40):match.start(1)]
        if not _A_RATE_FROM_INCOME.search(before):
            return True
    return False

# A state like this is said in a sentence around it - an age, a "yet", an "at all" - and the
# words that make the sentence are what tell it from the bare subject ("no savings account", which
# is a question about which one to open).
_NO_SAVINGS_WRAPPER = (
    "i", "im", "i'm", "ive", "i've", "we", "we're", "my", "our", "at", "and", "but", "yet", "now",
    "only", "even", "still", "always", "never", "all", "anything", "years", "year", "old",
    "month", "months", "time", "left", "saved", "save", "put", "by", "have", "had", "got",
    "start", "started", "starting", "nothing", "pennies", "penny", "pounds", "seriously",
    "whatsoever", "absolutely", "literally", "really", "just", "anything",
)


def _savings_gap(memory, understood):
    """Nothing put by, at whatever age: the first small sum, and the one question back."""
    said = " ".join(str(word) for word in (understood.get("words") or ())).lower()
    age = ""
    for word in said.split():
        if word.isdigit() and 16 <= int(word) <= 80:
            age = " at %s" % word
            break
    return ("Nothing put by%s is fixable in an afternoon, and the first \u00a3500 does more for you "
            "than any rate: open an easy-access savings account if you have not got one (ten "
            "minutes online), then set a standing order for payday of \u00a310 or \u00a325 - an "
            "amount you will not miss - and leave it alone. Build to \u00a31,000, which covers most "
            "surprises, then to a month of rent, bills and food. What is left each month after "
            "the bills go out?" % age)


# "twice" is a count of money when the line is about money, in whatever order it is said: "the
# payment went through twice" and "the payment is there twice" are the same complaint as "i was
# charged twice", and no phrase list would think of the words people put around the count. What
# has to be kept out is the other sense of "charge", which is a battery: a phone, a laptop, a
# toothbrush. So the count is a word of its own in the row's list and this is the fence. The
# payment words are "charged me", "was charged" and "charged for" rather than a bare "charged",
# because "i charged my laptop twice" carries only the battery.
_CHARGED_A_THING = re.compile(
    r"\b(?:phone|phones|mobile|mobiles|iphone|android|laptop|laptops|tablet|tablets|ipad|"
    r"battery|batteries|toothbrush|toothbrushes|watch|watches|headphones|earbuds|earphones|"
    r"kindle|controller|vape|scooter|charger|chargers|charging|cable|cables|port|ports|"
    r"socket|plug|plugs|mains|usb|power bank|adapter|adaptor|dock)\b", re.IGNORECASE)

_PAYMENT_SAID = re.compile(
    r"\b(?:payment|payments|pay|pays|paid|paying|refund|refunds|refunded|bill|bills|billed|"
    r"billing|statement|statements|account|order|orders|subscription|subscriptions|debit|"
    r"direct debit|standing order|invoice|invoices|receipt|receipts|checkout|transaction|"
    r"transactions|money|chargeback|card|visa|paypal|overcharged|recharged|"
    r"was charged|been charged|got charged|get charged|double charged|"
    r"charged (?:me|us|them|him|her|for the|for my|twice|two))\b",
    re.IGNORECASE)


def _a_payment_count(understood):
    """True when a count of twice is about money, not about charging a thing up."""
    said = " ".join(str(word) for word in ((understood or {}).get("words") or ())).lower()
    if not _CHARGED_A_THING.search(said):
        return True
    return bool(_PAYMENT_SAID.search(said))


# A debt named in the line is not by itself a purse that has run out. "i pay the minimum every
# month on my store card and the balance never moves" names a card, a minimum and a balance and
# says nothing is wrong with the payment, and the debt words above read the "minimum" as a
# missed one: the row answered a debt that is being paid with the script for a payment that
# cannot be made, in place of the pay-more-than-the-minimum answer the line is asking for. The
# row is for a debt in trouble, so it stands down when the debt words in the line are all about
# servicing it and none of them about missing it.
_SERVICING_A_DEBT = re.compile(
    r"\b(pay|pays|paying|paid|minimum|balance|interest|statement|direct debit|"
    r"standing order|repayment)\b")


# Asking the bank to give you an overdraft, or to raise the limit on it, is a question about an
# overdraft rather than a purse that has run dry. `money-trouble` carries "overdraft" in its first
# key group and the pronouns in its second, so "how do i ask my bank about an overdraft" scored two
# parts and was answered with "Two calls free up the most cash fastest" - two cheaper tariffs for a
# question about an overdraft. The phrases below are that shape and they name no state of the
# purse, and the guard only stands this row down: the overdraft rows answer, and a person who says
# they are skint in the same line keeps the purse answer.
_ASKING_FOR_AN_OVERDRAFT = (
    "ask my bank", "ask the bank", "ask our bank", "ask about an overdraft",
    "about an overdraft", "for an overdraft", "get an overdraft", "getting an overdraft",
    "open an overdraft", "set up an overdraft", "arrange an overdraft", "apply for an overdraft",
    "an overdraft application", "overdraft limit", "increase my overdraft",
    "increase the overdraft", "raise my overdraft", "bigger overdraft", "larger overdraft",
    "overdraft with bad credit",
)


def _a_purse_in_trouble(understood):
    """True when the line is a state of the purse or a debt, not a question about an overdraft."""
    said = " ".join(str(word) for word in ((understood or {}).get("words") or ())).lower()
    if any(phrase in said for phrase in _ASKING_FOR_AN_OVERDRAFT):
        return False
    return _a_debt_in_trouble(understood)


def _a_debt_in_trouble(understood):
    """True when a debt named in the line has failed, or nothing in the line is a debt."""
    said = " ".join(str(word) for word in (understood.get("words") or ())).lower()
    if not _A_DEBT.search(said) or _A_DEBT_IS_DUE(said):
        return True
    return not _SERVICING_A_DEBT.search(said)


# A mortgage payment is the one where arrears put the home at risk, so it gets its own sentence
# rather than a card's late fee: the duty to consider an arrangement, and how far off a possession
# actually is.
MISSED_MORTGAGE = ("A missed mortgage payment is an arrears fee of \u00a325 to \u00a335, interest, and "
                   "a mark on your credit file that shows six years - but the real risk is further "
                   "off than it feels. Ring the lender now and ask for a payment arrangement: they "
                   "have to consider one, and arrears only threaten the home after several missed "
                   "months and a court process. Ask too about switching to interest-only for a few "
                   "months or stretching the term, which lowers the monthly payment without a new "
                   "loan. How far behind are you?")


def _missed_payment(memory, understood):
    """What a missed payment costs, and the call that keeps the next one off the file."""
    said = " ".join(str(word) for word in ((understood or {}).get("words") or ())).lower()
    # A payment missed on car insurance is not a late fee on a card: the cover can be cancelled
    # for an unpaid direct debit, and driving without it is an offence. The general answer is
    # right about the fee and wrong about what matters.
    if "insurance" in said or "policy" in said:
        return ("Ring the insurer today and pay it: cover is cancelled after a missed direct debit "
                "once they have chased it, and driving uninsured is an offence with a police fixed "
                "penalty on top of the premium going up. Ask to move the payment date to just after "
                "payday, and check the letters - a cancelled policy on purpose has to be declared "
                "at the next renewal. Is it car insurance or the house?")
    # A payment missed on a mortgage is a different problem from a missed payment made *before*
    # asking for a mortgage: only the first one is about the home.
    if "mortgage" in said and not any(word in said for word in ("application", "apply", "applying",
                                                                "get a mortgage", "getting a mortgage",
                                                                "lender", "afford")):
        return MISSED_MORTGAGE
    # A missed payment and what it does to a mortgage application is asked often, and the answer
    # is not the arrears one: it is how far back a lender looks.
    if "mortgage" in said:
        return ("One late payment is usually not fatal for a mortgage: lenders read the last 12 "
                "months hardest and a single mark with everything else on time is explainable, "
                "especially once it is over a year old. What hurts is a run of missed payments, a "
                "default or a debt arrangement. Get the free reports from Experian, Equifax and "
                "TransUnion first and check nothing is wrong on them, then ask a broker which "
                "lenders take a single missed payment - several do. How recent was it, and was it "
                "a card or a loan?")
    # A fee already charged, and how to get it back, is asked with the word "refund" in it.
    if "refund" in said or "take it back" in said or "get it back" in said:
        return ("Ring and ask for it back, once: say it is the first one, that the payment has since "
                "gone through, and ask them to refund the charge as a goodwill gesture - most card "
                "issuers do it once a year without much argument. Do it in the app's chat or by "
                "email so there is a record, and check the next statement to see it land. If they "
                "say no, ask what their complaint process is; a written complaint gets a different "
                "answer from a call. Was it a card?")
    if any(phrase in said for phrase in _PAYMENT_ALREADY_MISSED):
        return ("Three things follow a missed payment: a late fee, interest from the date you should "
                "have paid, and a mark on your credit file that stays six years - the mark is the "
                "expensive part. Pay what you can today, then ring them and ask them to note the "
                "reason, because a first miss with a reason is treated far more kindly than a run "
                "of them, and the fee is often refunded once you are back on track. Set a direct "
                "debit for at least the minimum so the next one cannot happen. Is it a card or a "
                "loan, and how far behind is it?")
    return ("You get a late fee (\u00a312 on most cards, \u00a325 or so on a loan or mortgage), "
            "interest from the due date, and a late payment recorded on your credit file, which "
            "then shows for six years - the mark matters more than the fee. Ring them before the "
            "date rather than after and ask to move the date or split the payment: an arrangement "
            "agreed before the due date is usually not reported as missed. Cancelling the direct "
            "debit is the worst version, because you lose the payment and pay the bank's charge "
            "too. When is it due, and how much are you short?")


# A payment already gone past, said the ways people say it. Anything else in the row's key is a
# payment still to come, which is the other half of the answer.
_PAYMENT_ALREADY_MISSED = (
    "missed", "i missed", "ive missed", "i've missed", "paid late", "payed late", "paid it late",
    "was late", "is late", "went past", "overdue", "forgot", "forgotten", "didnt pay",
    "didn't pay", "havent paid", "haven't paid", "not paid", "bounced", "bounced back",
    "came back", "behind on", "in arrears", "defaulted", "default", "already missed",
    "went unpaid", "unpaid",
)


def _money_trouble(memory, understood):
    """A month where the money has run out: the two calls that free up cash in ten minutes."""
    said = " ".join(str(word) for word in (understood.get("words") or ())).lower()
    # A card, an overdraft or a payment that cannot be met this month is a debt question, and
    # the answer is a phone call before the date rather than two cheaper tariffs: "i cant pay my
    # credit card this month" was the add-to-wallet row, and "my credit card is 2000 pound and i
    # cant shift it" was a mood line. What the person needs first is that ring them early costs
    # nothing and a missed payment does.
    if _A_DEBT_IS_DUE(said):
        return ("Ring the card company before the payment date, not after: say you cannot make "
                "this month and ask for a payment plan or an interest freeze - they would rather "
                "have something than a missed payment, and it is the missed payment that goes on "
                "your file. Pay what you can, even a token amount, and ask them to confirm the "
                "arrangement in writing. Free debt advice from StepChange or Citizens Advice can "
                "do the call with you. Which card is it, and when is the payment due?")
    if any(phrase in said for phrase in SPENT_UP):
        return ("Spent up before the money comes in is a cash-flow week, not a crisis: write down "
                "what has to be paid before the next payment lands, then ring the one bill that "
                "will move a date, and plan the meals from what is already in the cupboard. What "
                "is left, and how long till you are paid?")
    return ("Two calls free up the most cash fastest: a cheaper energy and mobile tariff, and the "
            "subscriptions and standing orders you have forgotten - usually £20 to £50 a month "
            "between them. If a bill is what has done it, the council will spread council tax "
            "over twelve months instead of ten. Say which bit is tightest and I'll go at that one.")


# --- the money has to reach a date -------------------------------------------------
#
# "i have 20 pounds until friday", "how do i make 30 pounds last a week" and "i have 8 pounds to
# last me till friday" were a search hedge, a diet plan and a chat question between them. The sum
# and the day are both in the line, so the answer does the arithmetic the person is already doing
# in their head - so much a day - and then says what that buys.
_TILL_A_DAY = re.compile(
    r"\b(?:till|til|until|to last|last (?:me|us)|make it to|make it until|make it last|"
    r"get me to|get me through|see me through|stretch|to get by)\b", re.I)

_DAY_NAMED = re.compile(
    r"\b(today|tonight|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"the weekend|next week|a week|the week|this week|the end of the week|end of the week|"
    r"two weeks|"
    r"a fortnight|the fortnight|payday|the end of the month|end of the month|next friday)\b",
    re.I)

_WEEKDAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4,
             "saturday": 5, "sunday": 6}


def _till_when(text):
    """The day the money has to reach, as the line says it, and the days from today."""
    match = _DAY_NAMED.search(text or "")
    if not match:
        return "", 0
    said = match.group(1).lower()
    today = datetime.date.today()
    if said in ("today", "tonight", "tomorrow"):
        return "until %s" % said, 1
    if said in _WEEKDAYS:
        days = (_WEEKDAYS[said] - today.weekday()) % 7
        # "until friday" said on a friday means the next one, which is pay day for most people
        return "until %s" % said.capitalize(), days or 7
    if said in ("the weekend", "the week", "this week", "the end of the week", "end of the week",
                "next week"):
        return "until the end of the week", ((6 - today.weekday()) % 7) or 7
    if said in ("a week", "a fortnight", "the fortnight", "two weeks"):
        return "for a week" if said == "a week" else "for a fortnight", 7 if said == "a week" else 14
    if said == "next friday":
        return "until Friday", ((4 - today.weekday()) % 7) or 7
    # payday and the end of the month are the last day of this month, and the label says which
    # of the two the person said: "i have 20 pounds until the end of the month" answered "until
    # payday" told them a day they had not named.
    last = datetime.date(today.year + (today.month == 12), (today.month % 12) + 1, 1)
    last -= datetime.timedelta(days=1)
    days = max((last - today).days, 1)
    if "month" in said:
        return "until the end of the month", days
    return "until payday", days


def _a_pound(amount):
    """£4, £4.20, 91p - not £4.00, not £4.203, and under a pound the way people say it."""
    if amount < 1:
        return "%dp" % max(int(round(amount * 100)), 1)
    if abs(amount - round(amount)) < 0.05:
        return "£%d" % round(amount)
    return "£%.2f" % amount


_CHEAP_FOOD = ("oats, eggs, bread, rice, pasta, tinned beans and tomatoes, frozen veg and a bag "
               "of bananas come to about £2 a day")

# How many people a food sum has to stretch to. A line about "i" and "my" alone is one person;
# anything wider - "us", "we", "my family", "the kids", "me and my partner" - is more than one,
# and a stated size is taken at its word. It is a guess, but a guess the reply declares ("for
# two") rather than a flat claim that the money "feeds one person properly".
# "us", "we" and "both of us" are two people however the rest of the line reads; a family, a
# household or "the kids" is more than one but nobody said how many, so no number is claimed.
_TWO_OF_US = re.compile(
    r"\b(?:us|we|weve|we're|were|both of us|the two of us|couple|me and my partner|"
    r"me and my wife|me and my husband|me and my boyfriend|me and my girlfriend|our two)\b",
    re.I)
_A_HOUSEHOLD = re.compile(
    r"\b(?:our|ours|family|household|kids|children|child|partner|wife|husband|boyfriend|"
    r"girlfriend|son|daughter|baby|toddler|mum|dad|mother|father|parents|flatmates?|"
    r"housemates?)\b", re.I)
_A_STATED_SIZE = re.compile(
    r"\b(?:family|household|party|group)\s+of\s+(\d+|two|three|four|five|six)\b", re.I)
_NUMBER_WORDS = {"2": "two", "3": "three", "4": "four", "5": "five", "6": "six",
                 "two": "two", "three": "three", "four": "four", "five": "five", "six": "six"}
_A_COUNT = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6}


def _the_mouths(text):
    """How many people the line says the money is for: 1, 2, a stated size, or 0 for "we never
    said how many" (a family, the kids), where the reply names no number rather than guessing."""
    stated = _A_STATED_SIZE.search(text or "")
    if stated:
        size = stated.group(1).lower()
        return _A_COUNT.get(size, 0) or (int(size) if size.isdigit() else 3)
    if _TWO_OF_US.search(text or ""):
        return 2
    if _A_HOUSEHOLD.search(text or ""):
        return 0
    return 1


def _the_number(count):
    """2 -> "two", and a number the table does not hold stays a number."""
    return _NUMBER_WORDS.get(str(count), str(count))


# The days this week's card already answers for: a sum to last until one of these is the same
# question the cheap-week card divides up.
_A_WEEK_DAY_NAMED = re.compile(
    r"\b(?:today|tonight|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"payday)\b", re.I)


def _make_it_last(memory, understood):
    """What a sum of money buys a day until the day the line names."""
    reading = understood or {}
    text = str(reading.get("clean") or reading.get("text") or "")
    amount = 0.0
    for value, _match in _sums_in(text):
        amount = max(amount, value)
    label, days = _till_when(text)
    if amount and days and _A_WEEK_DAY_NAMED.search(text):
        # A sum to last until a weekday is the cheap-week card's line: it does the same division
        # and then says what to buy in what order, and this row answers it with the vaguer half
        # of the same thing. Only the day-name shapes - "how do i make 30 pounds last a week"
        # and "i have 8 pounds to last me till friday" already kept that card, so the three
        # people asking one question get one reply - while "i have 20 pounds until the end of the
        # month" is this row's.
        return None
    if not amount or not days:
        # no sum or no day in the line: the arithmetic this row is for cannot be done, and the
        # row that knows the subject ("how do i write a shopping list for the week") should
        # keep its turn
        return None
    a_day = amount / float(days)
    food_only = bool(re.search(r"\b(?:food|eat|eating|feed|meals?|groceries|shopping)\b",
                               text, re.I))
    if food_only:
        # The mouths the line names, so the reply does not tell somebody feeding a family that
        # the money "feeds one person properly": "i have 20 pounds to feed my family for a week"
        # and "i have 30 pounds to feed us for a week" both said exactly that. A line that says
        # only "i", "me" or "my" is one person; anything wider is divided by the household, and
        # a stated size ("family of four") is taken at its word.
        mouths = _the_mouths(text)
        if mouths == 1:
            return ("%s %s is %s a day on food, which feeds one person properly if you cook. %s "
                    "Do one shop for the whole %s rather than topping up, buy the own-brand "
                    "version of everything on the list, and plan the meals round what is reduced "
                    "at the end of the day."
                    % (_a_pound(amount), label, _a_pound(a_day), _CHEAP_WEEK,
                       "week" if days >= 5 else "stretch"))
        if not mouths:
            return ("%s %s is %s a day on food, which covers the basics for a household if you "
                    "cook. %s Do one shop for the whole %s rather than topping up, buy the "
                    "own-brand version of everything on the list, and plan the meals round what "
                    "is reduced at the end of the day.%s"
                    % (_a_pound(amount), label, _a_pound(a_day), _CHEAP_WEEK,
                       "week" if days >= 5 else "stretch",
                       (" That is tight for more than one, so ring Citizens Advice or the "
                        "council's welfare line this week rather than on the last day: a food "
                        "bank referral, a crisis grant or a payment break on a bill can all land "
                        "in time." if a_day < 3 else "")))
        return ("%s %s is %s a day on food, which is %s a head a day for %s. %s Do one shop for "
                "the whole %s rather than topping up, buy the own-brand version of everything on "
                "the list, and plan the meals round what is reduced at the end of the day.%s"
                % (_a_pound(amount), label, _a_pound(a_day), _a_pound(a_day / mouths),
                   _the_number(mouths), _CHEAP_WEEK, "week" if days >= 5 else "stretch",
                   (" That is tight for %s, so ring Citizens Advice or the council's welfare line "
                    "this week rather than on the last day: a food bank referral, a crisis grant "
                    "or a payment break on a bill can all land in time." % _the_number(mouths)
                    if a_day / mouths < 3 else "")))
    if a_day < 2:
        # Under about £2 a day the cheap-food list is the reply arguing with itself: "oats,
        # eggs, bread, rice, pasta, tinned beans and tomatoes, frozen veg and a bag of bananas
        # come to about £2 a day" is twice what the person has, so it says what one day's money
        # buys instead and goes straight to the help that exists.
        return ("That is %s a day %s. Buy a day at a time and pay cash: a loaf, a bag of rice, "
                "a bag of lentils, eggs and a bag of frozen veg is what that buys, and the bus or "
                "the phone top-up comes last. Under %s a day is the point to ring Citizens Advice "
                "or the council's welfare line today rather than on the last day - a food bank "
                "referral, a crisis grant or a payment break on a bill can all land before then."
                % (_a_pound(a_day), label, _a_pound(3)))
    if a_day < 3:
        return ("That is %s a day %s. Buy a day at a time and pay cash: %s, and the bus or the "
                "phone top-up comes last. Under %s a day is the point to ring Citizens Advice or "
                "the council's welfare line today rather than on the last day - a food bank "
                "referral, a crisis grant or a payment break on a bill can all land before then."
                % (_a_pound(a_day), label, _CHEAP_FOOD, _a_pound(3)))
    if a_day < 15:
        return ("That is %s a day %s. Buy the staples first - rice, pasta, eggs, tinned tomatoes, "
                "beans, frozen veg, oats, bananas, which feeds one person on about £2 to £3 a day "
                "- and do one shop for the whole stretch rather than topping up, because the "
                "top-ups are what eat a small sum. Keep the rest for the bus, the phone and "
                "anything that comes up, and pay by cash or a debit card so a small slip cannot "
                "take the week." % (_a_pound(a_day), label))
    return ("That is %s a day %s, so food is comfortably covered: do one shop for the whole "
            "stretch, cook from the cheap staples rather than buying lunch out, and you will "
            "finish it with money left. Put whatever is spare at the end into the next stretch "
            "rather than spending it, because the week after a long one is the one that bites."
            % (_a_pound(a_day), label))


# The words that make a pension question a safety question rather than a how-it-works one.
_PENSION_SAFE = ("guaranteed", "guarantee", "safe", "protected", "secure", "at risk", "risky",
                 "gone", "lost", "goes bust", "went bust", "go bust", "company fails",
                 "collapse", "collapsed", "scam", "lose", "losing")


_PENSION_MONEY_MOVED = ("bank details", "scammed out", "out of his pension", "out of her pension",
                        "gave my", "gave her", "gave his", "gave the",
                        "sent the money", "transferred", "transfer went", "paid them",
                        "paid in", "money gone", "released", "withdrawn", "moved the money",
                        "already moved", "drained")


def _pension_scam(memory, understood):
    """A pension scam: what to check before signing, or what to do once money has gone."""
    reading = understood or {}
    line = (str(reading.get("text") or "") or " ".join(
        str(w) for w in (reading.get("words") or []))).lower()
    if any(word in line for word in _PENSION_MONEY_MOVED):
        return ("Ring the bank's fraud line now, on the number on the back of the card or from "
                "the bank's own site, and say what was taken and when: a payment still in "
                "transit can often be recalled and the account frozen. Then report it to Action "
                "Fraud on 0300 123 2040 and to the Pensions Advisory Service, and ring the "
                "provider whose name was used, because they can flag the transfer at their end "
                "too. Do all of that today rather than after the weekend.")
    return ("Nobody legitimate cold-calls, emails or knocks about your pension: a call, a free "
            "review, a guaranteed better return or a hurry to move the pot is the shape of a "
            "scam. Check the firm on the FCA register, check the scheme with the Pension "
            "Regulator, and book a free Pension Wise appointment if you are 50 or over, before "
            "you sign anything. Ring your provider on the number on your own paperwork, never "
            "the one the caller gives you, and never move money to a scheme you did not find "
            "yourself.")


def _council_tax(memory, understood):
    """A council tax question, answered in the order the person asked it."""
    reading = understood or {}
    line = (str(reading.get("text") or "") or " ".join(
        str(w) for w in (reading.get("words") or []))).lower()
    # "how do i change the name on my council tax bill" wants the name change, not the discounts
    # list, so the change comes first when that is what was asked.
    if any(w in line for w in ("how much", "how much is", "average", "typical", "cost of",
                              "how expensive")):
        return ("It depends on your band and your council: a band D home in England averages "
                "about 2,200 pounds a year, band A about 1,450, and the bill is split over 10 "
                "months unless you ask for 12. Your council's own site lists every band for your "
                "postcode, and a band A to C property pays far less than the average suggests.")
    if any(w in line for w in ("12 months", "twelve months", "instalments", "installments",
                              "spread", "monthly", "over the year")):
        return ("Yes - councils bill over 10 months by default, and almost all will spread it "
                "over 12 if you ask, which lowers the monthly amount. Ring or use the council's "
                "online account before the first payment date, and if money is tight ask about "
                "the council tax reduction scheme at the same time.")
    # An overpaid bill is money the council owes back, and it is not the shop's 30-day return:
    # "can i get a council tax refund" was answered with faulty-goods law.
    if any(w in line for w in ("refund", "refunds", "money back", "rebate", "credit balance",
                              "in credit", "overpaid")):
        return ("An account in credit is refunded by the council, but only if you ask: ring the "
                "council tax line, say the date you moved out or the discount that was backdated, "
                "and give the bank details the direct debit came from - most councils pay within "
                "a fortnight once the account is closed. Keep the closing bill. If the money has "
                "not come after a month, put the request in writing, then complain to the council "
                "and after eight weeks to the Local Government Ombudsman, which is free.")
    if any(w in line for w in ("name", "address", "in my name", "moving in", "moved in")):
        return ("Use the council's own online form to change the name or address on the bill - or "
                "ring them if you cannot find it - and keep the reference number it gives you. Do "
                "it the week you move: the single person's 25 per cent discount only starts from "
                "the date the council knows you are on your own, and a bill in the wrong name is "
                "how people end up with a missed payment they never saw.")
    # "Is council tax per person" is the question about what the bill is charged on, and it is
    # neither the discount list nor the band: the bill follows the home, and the people only
    # change it through the discounts.
    if any(w in line for w in ("per person", "each person", "per household", "each household",
                               "how many people", "who has to pay", "who pays", "counted",
                               "counts as", "does my partner", "does my flatmate",
                               "count my partner", "counts my partner", "my partner count",
                               "count my flatmate", "two of us", "both of us", "in the house")):
        return ("On the home, not on the people: one bill per household, so two adults in a flat "
                "pay one bill between them, split however you like, not one each. Living alone "
                "gets 25 per cent off, and some adults are not counted at all - full-time "
                "students, apprentices under 25, a live-in carer, and someone with a severe "
                "mental impairment - so a two-adult home where only one counts still gets the "
                "single person's discount. Tell the council who lives there when you move in, "
                "because the discounts only start from the date they know.")
    # "I live alone" is one question and deserves one answer, not a list of five discounts.
    if any(w in line for w in ("student", "students", "in uni", "at uni", "university")):
        return ("Full-time students do not pay council tax, so a household where everyone is a "
                "full-time student is exempt - tell the council and keep the certificate from "
                "your university. One part-time student or one working person on the bill and it "
                "is a discount instead of an exemption. It starts from the date the council knows, "
                "so report it the week you move rather than at the end of the year.")
    if any(w in line for w in ("live alone", "living alone", "on my own", "by myself",
                              "single person", "single occupant", "money off", "discount",
                              "reduction")):
        return ("Living alone gets 25 per cent off the bill, and it is not automatic: ring the "
                "council or use its online account and ask for the single person discount, and it "
                "runs from the date they are told, not the date you moved in. If every other adult "
                "has moved out and one is left, the same 25 per cent applies. If your income is low, "
                "ask about the council's council tax reduction scheme at the same time - that is "
                "separate and can be much bigger.")
    if any(w in line for w in ("empty", "nobody lives", "no one lives", "vacant", "unoccupied")):
        return ("An empty home loses its discounts and can be charged a premium: in England a "
                "property empty for two years or more can carry a 100 per cent premium, and some "
                "councils apply one sooner. Tell the council the date it became empty - a short "
                "spell while it is being sold or done up is usually exempt - and ask what their "
                "rule is, because it differs by council.")
    # A bill that is too high is a complaint about an amount, and "what can i do" asks for the
    # actions in order. The words "what can i do" name nothing, so this line was reaching the
    # posture card - the same shape as a water bill that is "too high", which the water entry
    # learned for the same reason. The band comes first because a wrong band is the only one of
    # the two that is backdated over years.
    if any(w in line for w in ("too high", "so high", "too much", "expensive", "high",
                              "higher", "huge", "massive", "sky high")):
        return ("Check the band first, then the discounts, because a council tax bill is only "
                "'too high' in one of those two ways. Compare your band with identical houses "
                "on the council's valuation list, which is free to challenge through the "
                "Valuation Office and is backdated if they agree, then confirm every discount "
                "you are owed: 25 per cent for one adult, an exemption for a full-time student "
                "household, and - the biggest one, and separate from the 25 per cent - the "
                "council's own council tax reduction scheme if the income is low. Ring the "
                "council tax line and ask them to go through the bill with you; they do it all "
                "day.")
    return ("The two ways a council tax bill is wrong are the band and the discounts. Check the "
            "band against similar houses on your council's valuation list and challenge it with "
            "the Valuation Office if two identical houses differ, which is free. Then check the "
            "discounts: 25 per cent for one adult, none for a full-time student household, and a "
            "reduction scheme if the income is low. Ring the council tax line and ask them to go "
            "through the bill with you; they do it all day.")

_FOOD = re.compile(
    r"\b(restaurant|dinner|dining|lunch|meal|meals|food|drinks|drink|wine|beer|pub|pizza|"
    r"curry|waiter|waitress|tip|tips|pudding|tab|takeaway|brunch|breakfast)\b")

_HOME = re.compile(
    r"\b(flat|flats|flatmate|flatmates|housemate|housemates|house share|houseshare|"
    r"shared house|share house|landlord|landlady|tenancy|tenant|tenants|renting|rent|"
    r"moved in|moving in|our house|the house|my house)\b")

# A line that compares incomes is the couple's question, never a table - unless it also names
# the table. "who pays for dinner when my partner earns more than me" carries the same comparison
# as "who pays what when one earns more" and is still a dinner, and standing down on the
# comparison alone left four dinner lines with the search hedge (sleek-jar on #2464). So the
# stand-down lives in the reply, where both halves of the line can be read at once.
_INCOME_COMPARISON = re.compile(
    r"\b(?:one\s+(?:of\s+us\s+)?earns?\s+more|earns?\s+more\s+than\s+me|earns?\s+way\s+more|"
    r"earns?\s+more|we\s+earn|our\s+incomes?|joint\s+income|60\s*40|moved\s+in)\b")
SPLIT_BILL_REPLY = (
    "Split by what people actually had when the gap is big, drinks usually being the culprit; "
    "even shares are fine and simpler when it isn't. Say what you'd like before the bill "
    "arrives, which is far less awkward than sorting it out at the table.")


def _split_bill(memory, understood):
    """The table answer, or nothing when the line is the couple's income question."""
    reading = understood or {}
    said = " ".join(str(reading.get(key) or "") for key in ("clean", "text")).lower() or " ".join(
        str(word) for word in (reading.get("words") or ())).lower()
    if _INCOME_COMPARISON.search(said) and not _FOOD.search(said):
        return ""
    return SPLIT_BILL_REPLY


def _split_costs(memory, understood):
    """A bill split over dinner, or the bills in a shared home.

    "How do we split the bills" only says which of the two it is from the conversation before
    it: after "I've moved into a flat with two friends" it is a household question, and
    answering it with who-had-the-wine is the wrong answer to a real question.
    """
    reading = understood or {}
    line = str(reading.get("text") or " ").lower() or " ".join(
        str(w) for w in (reading.get("words") or [])).lower()
    # A line that says dinner or restaurant is a restaurant bill whatever the chat was about
    # before it; only a line that leaves it open is read against the conversation.
    if _FOOD.search(line):
        return ("Agree the rule before the bill arrives: split food evenly and let whoever drank "
                "pay for drinks, or use an app that itemises. Say the number out loud before you "
                "order the pudding, because the argument afterwards is almost never about the "
                "money.")
    said = [line]
    for turn in (memory or {}).get("turns") or ():
        if isinstance(turn, dict):
            said.append(str(turn.get("user") or ""))
        else:
            said.append(str(turn))
    if _HOME.search(" ".join(said).lower()):
        return ("Split it by room if the rooms differ, or by income if one of you earns much "
                "more, and agree the rule before the first bill rather than after it. Pay the "
                "house bills from one shared account that each of you tops up on payday, with "
                "the amounts written down, so nobody fronts the lot and nobody has to ask twice.")
    return ("Agree the rule before the bill arrives: split food evenly and let whoever drank pay "
            "for drinks, or use an app that itemises. Say the number out loud before you order the "
            "pudding, because the argument afterwards is almost never about the money.")

CREDIT_SCORE_IS = ("Your credit score is a number worked out from your credit report: what you "
                  "owe, how much of each card limit you use, whether payments arrive on time and how "
                  "long you have held accounts. Experian, Equifax and TransUnion each score it on a "
                  "different scale, and a lender reads the report itself rather than the score, so "
                  "the free report from all three is worth more than the number.")
CREDIT_SCORE_GOOD = ("There is no one good number, because the three agencies score on different "
                     "scales: Experian runs from 0 to 999 and puts roughly 881 to 960 in its good "
                     "band, Equifax scores out of 1,000 and TransUnion out of 710. What a lender "
                     "weighs is the report behind the number - payments on time, card balances "
                     "under about 30% of the limit and no run of new applications - so the band "
                     "matters less than those three.")
# "will missing a payment affect my credit score" is not the how-to-build-one question: the answer
# is what one missed payment does and for how long, which is the thing being asked.
CREDIT_SCORE_MISSED = ("Yes, and it is the mark that hurts most: a missed or late payment is "
                       "recorded against that month on your credit report and stays visible for six "
                       "years, though most of the damage fades within a year of on-time payments. "
                       "Pay it as soon as you can and ask the lender to note the reason, set up a "
                       "direct debit for at least the minimum so it cannot happen again, and keep "
                       "every other payment on time - lenders read the last 12 months hardest. It "
                       "does not reset the six years to start the clock again by paying it off.")

# A shared cost that is not a table has no card of its own, and every neighbouring row claimed
# it: "how do i split a taxi fare" was told to photograph the receipt for the employer, "how do i
# split petrol money" was the payslip budget, and a hotel room and a holiday cottage were both
# answered with who-had-the-wine. The subject in the line decides which of the three answers it
# gets, and nothing here is a dinner, a bill or a shared flat - those keep their own rows.
_SHARED_RIDE = re.compile(
    r"\b(?:taxi|taxis|cab|cabs|uber|ride|rides|fare|fares|parking|"
    r"toll|tolls|minibus)\b")
# A tank of petrol is not a fare: "how should we split the cost of petrol" was answered with
# "whoever was picked up first and dropped last pays most", and nobody is picked up for a tank.
# Fuel is paid for by the miles each person drove, so it gets its own opening.
_SHARED_FUEL = re.compile(
    r"\b(?:petrol|petrol money|diesel|fuel|fuel money|tank of|fill up|filled up|"
    r"mileage|miles|charging|charge point|electric car)\b")
_SHARED_STAY = re.compile(
    r"\b(?:hotel|hotels|room|rooms|cottage|cottages|airbnb|apartment|villa|caravan|"
    r"holiday house|holiday home|house we rented|place we rented|bnb)\b")
# A group holiday is not one bill and not a room: the big things are booked and paid for once,
# and the rest is a kitty. "how do i split the cost of a holiday" and "... of flights" were told
# who had the steak and the wine, because "split the cost" is the etiquette row's phrase.
_SHARED_TRIP = re.compile(
    r"\b(?:holiday|holidays|vacation|flight|flights|trip|trips|weekend away|week away|"
    r"weekend break|city break|abroad|group holiday|group trip)\b")
_SHARED_GIFT = re.compile(
    r"\b(?:present|presents|gift|gifts|collection|whip round|kitty|leaving present|"
    r"birthday present|wedding present|secret santa)\b")
_SPLIT_ASK = re.compile(
    r"\b(?:split|splits|splitting|share|shares|sharing|halves|go halves|between us|"
    r"each pay|per head|per person|fair|fairly|fairest|who owes|who pays|put in|"
    r"contribute|contribution|chip in|how much should|"
    # a whip round is a shared cost with a name of its own, and the word "split" is usually
    # absent from the line: "how do i do a whip round for a present" got a rehearsed speech.
    r"whip round|whip-round|whipp round|collection|collection for|kitty)\b")
# "should I chip in for a leaving present" is a social question - is it expected of me - and
# the mechanics of a collection is the wrong answer to it. The gift rows keep those lines.
_ASKING_IF_EXPECTED = re.compile(
    r"\b(?:should\s+i|should\s+we|is\s+it\s+rude|is\s+it\s+ok|is\s+it\s+okay|"
    r"is\s+it\s+weird|would\s+it\s+be\s+rude|am\s+i\s+expected|do\s+i\s+have\s+to)\b"
    r".*\b(?:chip\s+in|go\s+halves|put\s+in|contribute|pay\s+in)\b"
    r".*\b(?:present|presents|gift|gifts|collection|leaving|birthday|wedding|baby|"
    r"retirement|farewell)\b")


def _share_a_cost(memory, understood):
    """Splitting a ride, a stay or a present: one opening sentence per subject, then the rule."""
    reading = understood or {}
    line = " ".join(str(reading.get(key) or "") for key in ("clean", "text")).lower()
    if not line:
        line = " ".join(str(word) for word in (reading.get("words") or ())).lower()
    if _SHARED_FUEL.search(line):
        return ("Split fuel by the miles each person actually drove, not by who was in the car: "
                "note the odometer when you set off and when you get back, keep the receipt for "
                "the tank, and divide it by the miles rather than by the passengers. Agree before "
                "you set off whether the owner's wear is part of it - tyres and servicing are "
                "already in the driver's own costs, and a passenger is paying for the journey. "
                "One person pays at the pump, the rest send their share the same day, because a "
                "tank remembered a fortnight later is always argued about.")
    if _SHARED_RIDE.search(line):
        return ("Split a fare by the journey each person actually made, not by head: whoever was "
                "picked up first and dropped last pays most, and a taxi app already shows the "
                "breakdown, so screenshot it into the group chat the same night. Say who is "
                "paying the driver before anyone gets in, and let one person book and collect, so "
                "there is a single number to divide rather than three arguments about it.")
    if _SHARED_STAY.search(line):
        return ("Split a shared place by the room and the nights, not by head: a couple in the "
                "double pays more than the person on the sofa bed, and anyone staying three "
                "nights out of seven pays for three. Work the total out per room per night, "
                "round it to something easy, and take the deposits from everyone before the "
                "booking is made so the person whose card it is on is never the one chasing.")
    if _SHARED_TRIP.search(line):
        return ("Book the big things - the flights, the house, the car - to one card and split "
                "those equally, or by room if the rooms differ, then have everyone put the same "
                "amount into a kitty for meals, taxis and tickets. Photograph every receipt and "
                "count the kitty on the last night rather than after you get home, and refund "
                "what is left to the person who paid it in, because a group holiday is a lot of "
                "small shared costs rather than one bill.")
    if _SHARED_GIFT.search(line):
        return ("Fix the amount before anybody is asked, and ask for it once: a whip round works "
                "when the target is a number - 'twenty pounds each, I'll get the vouchers' - and "
                "fails when it is a collection with no total. Buy from one person's card, keep "
                "the receipt and the list of who has paid in the group chat, and cover any "
                "shortfall yourself rather than going round a second time.")
    return ("Say the number before the thing is booked or ordered, then split by what each person "
            "actually had rather than by head, and keep the reckoning in one place - a note in "
            "the group chat or a splitting app - so nobody has to trust their memory. Whoever "
            "pays up front collects, and it is fair to ask the same day rather than a fortnight "
            "later.")


def _shares_a_cost(understood):
    """The shared-cost row's guard: the line has to be about a split, not just name a taxi."""
    reading = understood or {}
    said = " ".join(str(reading.get(key) or "") for key in ("clean", "text")).lower()
    if not said:
        said = " ".join(str(word) for word in (reading.get("words") or ())).lower()
    if _ASKING_IF_EXPECTED.search(said):
        return False
    return bool(_SPLIT_ASK.search(said))
CREDIT_SCORE_STEPS = ("Get your report free from Experian, Equifax or TransUnion, correct "
                     "anything wrong on it, register on the electoral roll and set up a direct "
                     "debit for at least the minimum on every card. Keeping card balances under "
                     "about 30% of the limit and not applying for several things at once does most "
                     "of the rest.")
CREDIT_SCORE_UP = ("A score that has gone up is usually a payment made on time, a card balance paid "
                   "down, an old search dropping off the file, the account getting older, or a "
                   "mistake being put right. Check the free report from Experian, Equifax or "
                   "TransUnion to see what changed, keep the balance under about 30% of the limit, "
                   "and stay on the electoral roll so it keeps climbing.")
CREDIT_SCORE_DROP = ("A drop is nearly always one of five things: a late or missed payment, a card "
                     "balance over about 30% of its limit, a new application and the search that "
                     "comes with it, an account you closed, or a mistake on the file. Then get the "
                     "report free from Experian, Equifax or TransUnion, dispute anything wrong, and "
                     "it usually recovers within a few months of on-time payments.")


def _credit_score(memory, reading):
    """Why a score moved, or how to build one: the same entry, two openings.

    "My credit score has dropped" and "why has my credit rating gone down" were a shrug and the
    free-advice line, because the entry keyed only the question shapes; the change gets its own
    opening sentence and the steps are the same.
    """
    said = " ".join(str((reading or {}).get("clean") or "").lower().split())
    # "what is a credit score" names the thing rather than asking for the steps, and the row
    # above answered it with the improvement paragraph: a person asking what a score is got a
    # to-do list. The definition opens and the steps are not repeated after it, the way the
    # debt-plan rows below read the arrangement the line names. "what is my credit score" is
    # the person's own figure, which the free report answers, so the possessive keeps the
    # steps.
    if "definition" in ((reading or {}).get("asks") or ()) and not re.search(
            r"\b(?:my|our)\b", said):
        if any(word in said for word in ("good", "great", "decent", "healthy", "normal",
                                         "average", "ok")):
            return CREDIT_SCORE_GOOD
        return CREDIT_SCORE_IS
    # A score that went UP is not a score that dropped: the same entry, the other direction, or
    # "my credit score went up" gets the five causes of a fall.
    if any(word in said for word in ("went up", "gone up", "goes up", "go up", "going up",
                                     "rose", "risen", "rises", "increased", "improved",
                                     "jumped up", "climbed")):
        return CREDIT_SCORE_UP
    # "why is" is not a change: it also asks "why is my credit score important", which the
    # causes of a drop do not answer.
    # A missed or late payment is asked as its own question - "will missing a payment affect my
    # credit score", "does a late payment show on my credit file" - and the steps answered it with
    # how to build a score rather than what one missed payment does.
    if any(word in said for word in ("missing a payment", "miss a payment", "missed a payment",
                                     "missed payment", "late payment", "paid late", "pay late",
                                     "payment late", "miss a direct debit", "missed a direct debit")):
        return CREDIT_SCORE_MISSED
    if any(word in said for word in ("dropped", "drop", "drops", "gone down", "went down",
                                     "fallen", "fell", "lower", "decreased", "why has",
                                     "why did", "what happened", "changed", "change")):
        return CREDIT_SCORE_DROP
    return CREDIT_SCORE_STEPS


# The four arrangements, one reply each: a question that names one of them wants that one
# explained. A single paragraph comparing two of them answered "what is a debt relief order"
# with a debt management plan and never said the words "debt relief order" at all - the row was
# right and the reply was about a third thing. The comparison is what the line gets when it
# compares them or names none, because "what is a debt arrangement" is a question about the set.
_DEBT_PLAN_ASKS = (
    ("dro", re.compile(r"\b(?:debt relief orders?|debt relief|dros?)\b")),
    ("trust deed", re.compile(r"\b(?:protected trust deeds?|trust deeds?)\b")),
    ("iva", re.compile(r"\b(?:ivas?|individual voluntary arrangements?)\b")),
    # a debt arrangement scheme is Scotland's own, government-run plan, not a debt management
    # plan with a different name, so it gets its own sentence rather than the same paragraph
    ("das", re.compile(r"\b(?:debt arrangement schemes?)\b")),
    # "debt arrangement scheme" is the Scottish plan above and must not also read as a dmp
    ("dmp", re.compile(r"\b(?:dmps?|debt management plans?|debt management"
                       r"|debt arrangements?(?!\s+schemes?))\b")),
)

_DEBT_PLANS = {
    "dro": ("A debt relief order writes off debts of under about £30,000 if you have little "
            "spare income and nothing much to sell: you pay a £90 fee, apply through a free "
            "adviser, and after a year the debts are gone. It stays on your credit file for six "
            "years, and you cannot get one with savings or a car over the limits."),
    "trust deed": ("A protected trust deed is Scotland's version of an IVA: a trustee takes "
                   "your debts, you pay what you can afford for usually four years, and the rest "
                   "is written off. It is on your credit file for six years and is a formal step, "
                   "so get free advice from StepChange or National Debtline before you sign."),
    "iva": ("An IVA is a formal, binding deal: one affordable payment a month for usually five "
            "years, interest frozen, then the rest is written off. It is on your credit file for "
            "six years and can affect jobs, mortgages and bank accounts, so it is a last resort "
            "after free advice from StepChange or National Debtline."),
    "das": ("The Debt Arrangement Scheme is Scotland's own, and it is free: you pay one monthly "
            "sum to a payment distributor, who splits it between your creditors, the interest is "
            "frozen and no creditor can take action against you while it runs. Nothing is written "
            "off - you repay in full over a longer stretch - so ask a Scottish free adviser to set "
            "it up."),
    "dmp": ("A debt management plan is an informal deal: one monthly sum, split between your "
            "creditors and paid through a free adviser, with the interest usually frozen. Nothing "
            "is written off - you repay it all over a longer stretch - and it shows on your credit "
            "file for six years. It is not binding on them, so ask a free service to set it up."),
    "compare": ("A debt management plan is an informal deal: one monthly sum, split between the "
                "creditors and paid through a free adviser, and it shows on your credit file for "
                "six years. An IVA is formal and binding - fixed payments for usually five years, "
                "then the rest is written off - but it is on your file six years too and can "
                "affect jobs and mortgages. A debt relief order is for smaller debts and a trust "
                "deed is Scotland's IVA; all four want free advice first."),
}


def _debt_plans(memory, understood):
    """The plan the line names, and the comparison when it names two or none.

    One row, because the four are the same question - "what is an X and is it worth it" - and
    different replies, because a person who asks about a trust deed is not asking about a debt
    management plan. Naming a plan is what the first sentence has to do.
    """
    clean = " " + str((understood or {}).get("clean")
                      or (understood or {}).get("text") or "").lower() + " "
    named = [name for name, pattern in _DEBT_PLAN_ASKS if pattern.search(clean)]
    if len(named) == 1:
        return _DEBT_PLANS[named[0]]
    return _DEBT_PLANS["compare"]


_WINDFALL_PLAN = (
    "Take it in this order. First clear any credit card, overdraft or pay-later debt, "
    "because that costs 20% or more a year and no savings account pays that. Second, put "
    "three to six months of essential spending in an easy-access account, so a broken "
    "boiler is an annoyance rather than a loan. Only then think about the long term, and "
    "for money you will not need for five years that usually means a global index tracker "
    "inside a stocks and shares ISA, or a bit more into your pension. A few thousand "
    "pounds is a cushion before it is an investment, so do not lock it into a fixed bond. "
    "If you claim means-tested benefits, check how a lump sum counts before you spend it.")

# A small sum is not a windfall: "i have 20 pounds what should i do with it" is a budgeting
# question about the rest of the week, and handing it the order of operations (a global index
# tracker in a stocks and shares ISA) is the wrong answer to a real question. The line is now
# reachable from the money word alone, so the size the line names decides whether it is this row.
_SMALL_SUM = 300


def _windfall_plan(memory, understood):
    """What to do with a sum the person has, for any sum large enough to plan with."""
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    size = _target(text)
    if size and size < _SMALL_SUM:
        # "20 pounds until friday", "a hundred quid left for the week": money that is about to
        # be spent, not money looking for a home.
        return None
    if not size and _per_month(text):
        # "what should i do with 50 pounds a week" names a rate, not a pot: the saving rows
        # answer how much to put by, and this one would tell somebody on £50 a week to open a
        # stocks and shares ISA.
        return None
    return _WINDFALL_PLAN


# "i need to borrow money" has no "where" in it, so the lender ladder never saw it, and the
# chasing wording of `family.lent-money` answered it instead - telling somebody who wants to borrow
# to ask themselves when they will pay it back. A borrow line is only about money when it says so:
# "can i borrow your drill", "can i borrow a book from the library" and "can i borrow against my
# house" are other questions, and a book or a ladder is not a loan.
_BORROW_ANSWER = (
    "Borrow as little as you can, for as short as you can, from the cheapest place. Your own bank's "
    "personal loan first, asked as a quote, which leaves no mark on your file; compare the APR with "
    "a credit union, which caps interest at 3 per cent a month. A 0 per cent purchase card only "
    "works if you clear it before the offer ends and a payday lender never does. If a loan is "
    "refused, that is the moment to talk to StepChange free rather than borrow more.")

_MONEY_IN_A_BORROW_LINE = (
    "money", "pounds", "cash", "loan", "loans", "bank", "credit", "grand", "overdraft",
    "apr", "interest", "\u00a3", "euro", "dollars", "payday",
    # a fiver or a tenner is the friend's money, not a lender's: "can i borrow a fiver till
    # friday" was getting the personal-loan card, and the small change words are out. A figure
    # of two digits or more still counts on its own, so "can i borrow 50" is this row.
    "borrow 5", "borrow 1", "borrow 2", "borrow 3", "borrow 4", "borrow 6", "borrow 7",
    "borrow 8", "borrow 9")


def _borrow_how(memory, understood):
    """The borrowing answer for a line that is about money, or None for the other B's to borrow."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    words = set(re.findall(r"[a-z\u00a3]+", said))
    if words & set(_MONEY_IN_A_BORROW_LINE):
        return _BORROW_ANSWER
    if re.search(r"\d{2,}", said):
        return _BORROW_ANSWER
    return None


# "im buying a house" said in passing is a person at the start of the biggest purchase of their
# life, and it was answered by handing their own sentence back: "Noted: you're buying a house."
# The row that holds the saving-up answer is the right home for it, but the first step is not the
# same once they are already buying: the deposit is behind them and the lender and the solicitor
# are in front. So the line picks the half.
_ALREADY_BUYING = ("buying a house", "buying a flat", "buying a home", "buying my first",
                   "buying our first", "in the process of buying", "had an offer accepted",
                   "offer accepted", "offer has been accepted", "we've had an offer accepted",
                   "mortgage application", "applying for a mortgage", "just had my offer",
                   "just had our offer", "got a mortgage")
# The half about starting out is the one the row already had; these are the words that say the
# person is still saving, so "how do i start buying a house" keeps the deposit answer even though
# it has "buying a house" in it.
_STILL_SAVING = ("how do i start", "how to start", "where do i start", "start buying",
                 "want to buy", "want to get on", "save up", "saving up", "can i afford",
                 "afford a house", "afford a flat", "what do i need", "get on the ladder",
                 "thinking about buying", "planning to buy",
                 "hoping to buy", "in a few years", "eventually", "one day")
_FIRST_HOME_STEPS = (
    "Sort two things this week: a decision in principle from a lender, which says what they will "
    "lend, about four and a half times your income, and a solicitor who quotes a fixed fee, "
    "because the searches and the paperwork start as soon as an offer is accepted. Then book the "
    "survey before you exchange, and keep at least £2,000 back for it, the searches and the "
    "moving van, since those are spent whether or not the sale goes through.")


_FIRST_HOME_STEPS_SAVING = (
    "Open a Lifetime ISA and put a monthly standing order into it: that adds 25% on up to "
    "£4,000 a year. Keep your credit file clean and find out what you could borrow, about "
    "four and a half times your income, so the deposit is all that is left to save: 10% of "
    "a £200,000 flat is £20,000, or £333 a month for five years.")


# A job on the house is not the house being bought: "how long does it take to clean the house"
# and "how long does it take to tidy the house" were both answered "Open a Lifetime ISA and put a
# monthly standing order into it", because "house" is the buying row's subject and "how long" is
# one of its asks, so a duration question about housework scored on both halves. The job words
# stand the row down; a money word in the same line keeps it, because "how long does it take to
# save for a house" and "how long until i can buy a house" are still its question.
_HOUSE_JOB_WORDS = ("clean", "cleans", "cleaning", "cleaned", "tidy", "tidies", "tidying",
                    "tidied", "hoover", "hoovers", "hoovering", "vacuum", "vacuums",
                    "vacuuming", "dust", "dusting", "scrub", "scrubbing", "mop", "mopping",
                    "bleach", "bleaching", "declutter", "decluttering", "sort out",
                    "sorting out", "fix", "fixing", "repair", "repairs", "repairing",
                    "unpack", "unpacking", "move", "moving in", "moved in", "heat",
                    "heating", "insulate", "insulation", "smell", "smells", "smelly",
                    "damp", "mould", "mold", "garden", "lawn", "fence", "fences",
                    "bins", "bin", "painting", "repaint", "repainting")
_HOUSE_BUYING_WORDS = ("deposit", "save", "saves", "saving", "savings", "saved", "afford",
                       "affords", "affordable", "buy", "buys", "buying", "bought",
                       "purchase", "purchasing", "price", "prices", "cost", "costs",
                       "mortgage", "mortgages", "worth", "lender", "lenders", "loan",
                       "loans", "how much", "stamp duty", "offer", "sold", "sell",
                       "selling", "sell my", "estate agent", "viewing", "viewings")


def _not_a_job_on_the_house(understood):
    """A line about cleaning, mending or heating the house is not a line about buying one."""
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    words = set(re.findall(r"[a-z0-9']+", text))
    if not any(word in words for word in _HOUSE_JOB_WORDS):
        return True
    return any(word in words for word in _HOUSE_BUYING_WORDS) or any(
        phrase in text for phrase in _HOUSE_BUYING_WORDS if " " in phrase)


def _first_home_steps(memory, understood):
    """The saving half, or the buying half, whichever the line is on."""
    clean = understood.get("clean") or ""
    if any(word in clean for word in _STILL_SAVING):
        return _FIRST_HOME_STEPS_SAVING
    if any(shape in clean for shape in _ALREADY_BUYING):
        return _FIRST_HOME_STEPS
    return _FIRST_HOME_STEPS_SAVING


# The side of a gift the line is asking from: money that arrives is the receiver's question, and
# money that leaves is the giver's. Both lines are the same tax answer, said from where they stand.
_GIFT_FROM_WORK = (" from work ", " at work ", " from my job ", " from the job ", " my employer ",
                   " employer gave", " employers gave", " company gave", " my company ",
                   " from the company", " my boss gave", " from my boss", " payroll ",
                   " work gave me", " work gave us", " works christmas", " staff gift",
                   " christmas bonus", " from head office")

_GIFT_ARRIVES = (" from my ", " from our ", " from a parent", " from parents",
                 " from his ", " from her ", " parents give", " parent gives", " parents gave",
                 " give me ", " gave me ", " gives me ", " given to me", " gave us ",
                 " given to us", " gifts me", " gifted me", " being given",
                 " i receive", " receiving", " i get ", " i got ", " left me ",
                 " in my name")


def _the_tax_on_a_gift(memory, reading):
    """Nothing is due on the gift itself, said from the side of the line asking."""
    if _a_claim_that_asks_for_money_first(reading):
        return _prize_answer(memory, reading)
    clean = " %s " % " ".join(str((reading or {}).get("clean") or "").lower().split())
    tail = (" The one tax a gift can touch is inheritance tax, and that is about the giver's "
            "estate rather than about you: a gift made more than seven years before they die is "
            "usually outside it, £3,000 a year is free, £250 per person per year in small gifts is "
            "free, and a wedding gift of up to £5,000 from a parent is free. Gifts out of spare "
            "income, not savings, are free however big they are. Keep a note of the date and the "
            "amount, because the estate has to prove the seven years if it ever comes up, and if "
            "the giver may need care in the next few years, that question is looked at separately "
            "from tax.")
    if any(phrase in clean for phrase in _GIFT_FROM_WORK):
        # A gift from an employer is the one exception, and it is a different tax: trivial
        # benefits of up to £50 are free, a voucher or hamper from work can be a benefit in kind.
        return ("Nothing if it comes from a person, but a present from an employer is the one "
                "exception: a trivial benefit of up to £50 a year is tax free, while a voucher, "
                "gift card or hamper from work can be taxed as a benefit in kind, so ask payroll. "
                "Money given to you by anyone else is not income, so there is nothing to pay and "
                "nothing to declare." + tail)
    if any(phrase in clean for phrase in _GIFT_ARRIVES):
        return ("Nothing. Money somebody gives you is not income, so there is no tax to pay on it "
                "and nothing to declare to HMRC." + tail)
    return ("Nothing at the time: the UK has no gift tax, so giving money away costs neither of "
            "you anything now, and the person who gets it declares nothing." + tail)

def _pip_the_benefit(understood):
    """False when the line's "pip" is an animal's name rather than the benefit.

    The word is a name people give a pet - "we got a kitten called pip last week" - and the
    payment card took it, then read the two turns after it as a claim too. An animal in the
    line, or a naming verb before the word, is what tells the two apart.
    """
    said = understood if isinstance(understood, dict) else {}
    text = str(said.get("text") or said.get("clean") or "").lower()
    if re.search(r"\b(?:cat|cats|kitten|kittens|dog|dogs|puppy|puppies|hamster|rabbit|"
                 r"bunny|bird|birds|parrot|budgie|guinea|ferret|chick|chicks|hen|hens|"
                 r"pet|pets)\b", text):
        return False
    return not re.search(r"\b(?:called|named|name is|nickname)\b[^.?!]{0,12}\bpip\b", text)


# What the tax is, and the gifts that can take an estate below it. Kept as the row's own words so
# `_the_inheritance_tax` can hand back either this or the scam warning below.
_WHAT_INHERITANCE_TAX_IS = (
    "Nothing is due below £325,000, or £650,000 for a married couple who leave everything to each "
    "other, and a home left to children adds up to £175,000 each on top. Gifts are the main lever: "
    "anything given more than seven years before the death is usually outside the estate, £3,000 a "
    "year is always free, and a wedding gift of up to £5,000 from a parent is too. Above the "
    "threshold the rate is 40% and it falls on the estate at death, not on a gift someone made while "
    "alive, so keep a written record of every gift and its date - the estate has to prove the seven "
    "years.")


# ---- which way a debt runs ---- -------------------------------------------------------------
#
# A debt is the one everyday question where the same words are the whole answer from both sides:
# "i owe my brother 500" and "my brother owes me 500" carry the same person, the same verb and the
# same money, and the two scripts are opposites. The rows list the phrasings ("owes me", "ask my
# mate") and so miss the plainest report of all - "should i say something to my mate about the
# money he owes" has no "me" in it anywhere - and the person chasing a debt was read as the one
# who owes it: "I owe you £600, I can do £50 a week."
#
# So the line is read for which way the money runs, and the row answers the side it is on. "owed"
# is money coming to the person (somebody else is the debtor), "owing" is money going out of
# their pocket, and None is a line that does not say.
_DEBT_FIRST = frozenset(("i", "im", "ive", "i've", "we", "weve", "we're", "were"))
_DEBT_THIRD = frozenset((
    "he", "she", "they", "him", "her", "them", "his", "their", "theirs", "hes", "shes",
    "theyll", "he's", "she's", "they'll", "it", "its", "it's",
    "mate", "mates", "friend", "friends", "brother", "brothers", "sister", "sisters", "mum",
    "mam", "dad", "mother", "father", "parents", "son", "daughter", "family", "colleague",
    "colleagues", "neighbour", "neighbours", "neighbor", "landlord", "ex", "partner", "husband",
    "wife", "cousin", "uncle", "aunt", "boss", "flatmate", "roommate", "housemate", "lad", "bloke",
))
_DEBT_OWING = frozenset(("owe", "owes", "owed", "owing", "borrow", "borrows", "borrowed",
                         "borrowing"))
_DEBT_OWED = frozenset(("lend", "lends", "lent", "lending"))
_DEBT_ME = frozenset(("me", "us"))


def a_debt_that_runs_one_way(understood):
    """Which way a debt in the line runs: "owed", "owing", or None when the line does not say.

    The subject of the verb decides, because that is the word the two directions differ in: "i owe
    my brother" and "my brother owes me" are otherwise the same sentence. `lend` flips the sense
    (the one who lends is owed) and `borrow` does not. A verb with no subject in its clause reads
    None, and the row keeps the answer it had.
    """
    clauses = (understood or {}).get("clauses") if isinstance(understood, dict) else None
    if not clauses:
        return None
    for clause in clauses:
        if not clause:
            continue
        for i, word in enumerate(clause):
            if word not in _DEBT_OWING and word not in _DEBT_OWED:
                continue
            subject = next((w for w in reversed(clause[max(0, i - 6):i])
                            if w in _DEBT_FIRST or w in _DEBT_THIRD), None)
            if subject is None:
                continue
            if word in _DEBT_OWED:
                return "owed" if subject in _DEBT_FIRST else "owing"
            return "owing" if subject in _DEBT_FIRST else "owed"
    return None


# The two sides of one row. The debtor's script is what this row always said; the other side is the
# person chasing money somebody else owes, and it is one message, one date and one consequence,
# because asking twice vaguely is what makes it awkward.
_THE_DEBTOR_SCRIPT = (
    "Tell them the amount and the date in one message: \"I owe you £600, I can do £50 a week from "
    "Friday, so it's clear by March.\" Put it on a standing order so it happens without a "
    "conversation every month, and if you cannot pay this month say so before the date, not after "
    "- a small, steady repayment keeps the relationship and the debt honest."
)
_THE_CHASE_SCRIPT = (
    "Say it once, plainly and in writing, and put a date on it: \"You said £200 by the end of the "
    "month - can you do the 30th?\" Naming the amount and a day is a request, not an accusation, "
    "and a message is easier than a face-to-face. If money is tight for them, agree a standing "
    "order of a small amount a week rather than another promise, and say what happens if it slips "
    "- that is what keeps the friendship and the money."
)


def _the_debt_answer(memory, understood):
    """The side of the debt the line is on: theirs to pay, or theirs to chase."""
    if a_debt_that_runs_one_way(understood) == "owed":
        return _THE_CHASE_SCRIPT
    return _THE_DEBTOR_SCRIPT


def _the_inheritance_tax(memory, reading):
    """The threshold, or what the claim really is when the money is asked for before it is released.

    A claim that wants a fee before the money is released holds the tax words too, so it reached
    this row and was told what the threshold is - the one answer that makes paying the "tax" look
    reasonable. The shape is not a tax question at all, and this says so in the first sentence.
    """
    if _a_claim_that_asks_for_money_first(reading):
        return _prize_answer(memory, reading)
    return _WHAT_INHERITANCE_TAX_IS


def _a_claim_that_asks_for_money_first(understood):
    """True when the line is money asked for before an inheritance is released, not a tax question.

    The tax rows own the words "inheritance" and "tax", so a claim that wants a fee before it pays
    out reached the threshold figure and was told nothing is due below £325,000 - the one answer
    that makes paying look reasonable. The scam reading already exists in this file
    (`_a_prize_and_a_bill`), and this asks it the same question, with the probate steps held out
    because there the money really does go out first.
    """
    text = str(((understood or {}).get("clean") or (understood or {}).get("text") or "")).lower()
    if not text or _THE_ESTATE_BEING_WOUND_UP.search(text):
        return False
    return _a_prize_and_a_bill(understood)

_CASH_ON_HAND = re.compile(
    r"\bhow much cash\b|\bcash (?:at home|in the house|on me|in my purse|in my wallet)\b|"
    r"\bkeep (?:some )?cash\b|\bemergency cash\b", re.I)

_CASH_REFUSED = re.compile(
    r"\brefuse[sd]? cash\b|\bcash only\b|\bno cash\b|\bnot tak(?:e|es|ing) cash\b|"
    r"\bwont take cash\b|\bwon't take cash\b|\blegal tender\b|\bmust (?:a shop|they|shops) "
    r"take cash\b", re.I)


def _no_place_named(understood):
    """A line that names a country is the travel-money answer, not the everyday choice.

    "should i take cash or card to spain" wants two cards from different banks and the local
    currency; the envelope-and-protection comparison is the same question with nowhere to go
    (bronze-whistle).
    """
    clean = " ".join(str((understood or {}).get("clean") or "").lower().split())
    return not _countries_said(clean)


def _cash_or_card(memory, reading):
    """Cash or card, said as a choice: the protection is the card's, the limit is the cash's."""
    clean = " ".join(str((reading or {}).get("clean") or "").lower().split())
    if _CASH_REFUSED.search(clean):
        return ("A shop can set its own payment terms, so it can say card only or cash only as "
                "long as it says so before you buy - 'legal tender' only means a court has to "
                "accept it for a debt, which is why a bus or a corner shop can turn down a £50 "
                "note. What it cannot do is take your money and then refuse the only way you can "
                "pay, or refuse you for a protected reason. If it is a service you have no "
                "alternative to, such as a council or an NHS car park, complain in writing and "
                "quote the terms they published.")
    if _CASH_ON_HAND.search(clean):
        return ("Keep about £50 to £100 at home in small notes, and a few pound coins: enough for "
                "a power cut, a taxi or a market stall on a day the card machines are down, and "
                "not so much that losing it hurts. Keep it somewhere dry and not in the obvious "
                "drawer, and top it up when you spend it rather than all at once.")
    return ("Both, for different jobs. A card - credit for anything over £100 - is the one with "
            "protection: Section 75 makes the card company jointly liable when something never "
            "arrives or is not what was sold, and a debit card gives you a chargeback instead. "
            "Cash is the one with a limit: an envelope of notes for the week is spending you can "
            "see run out, which is why it works for people who overspend on the card, and small "
            "shops, markets and tips still run on it. So pay for anything you might have to claim "
            "on by card, and use cash for the everyday spending you want to cap.")



# The plainest way a person says the money is owed, and the one shape that no card keyed: "i
# havent paid my rent" was a chat nod and "i havent paid my phone bill" was "I'm listening",
# while "im behind on rent", "i cant pay my rent" and "i havent paid my rent in two months" all
# reached an answer. A negated payment put the words the tables look for in the wrong key - the
# thing ("rent", "bill", "phone") is in the second key of these rows, and "havent paid" was in
# the table only on `stopping-paying`, which fences out every bill it is said about. So the
# shape is one tuple that the rows naming a thing you pay can pair with.
NOT_PAID = ("havent paid", "haven't paid", "hasnt paid", "hasn't paid", "havent payed",
            "haven't payed", "have not paid", "has not paid", "not paid yet", "didnt pay",
            "didn't pay", "did not pay", "didnt payed", "never paid", "unpaid", "overdue",
            # "i owe rent" is the shortest way of all, and a rent or a bill is never what is
            # owed in a good way.
            "owe rent", "owe the rent", "owe a bill", "owe on the",
            # "short this month" and "missed this month" are deliberately not here: the rent
            # row carries "short this month" already, and in the general debt row the phrase
            # took "money is a bit short this month" - a person saying the week is long, which
            # the composer answers with a question - and turned it into a lecture.
            "missed the payment", "missed a bill")


# The payment-plan answer is said twice: once for a line that names the bill, and once for
# "will i be cut off if i stop paying", which names no bill at all. The words live here so
# that the two rows cannot drift apart.
# A payment-plan answer is written for a supplier: it names the priority services register, the
# Warm Home Discount and a supply that could be cut off. All three are wrong for money owed to a
# person, and "i havent paid the babysitter" reached it on the word "paid" alone, so three hours'
# wages got a lecture about the Warm Home Discount. The test is not which noun follows "paid" but
# whether the line is about a supply at all: the thing supplied has to be named, or the line has
# to say the supply stopped. Anything else that owes money this way is a person, and money owed to
# a person is friends.owe-friend-money.
A_SUPPLIED_THING = re.compile(
    r"\b(?:bill|bills|supplier|suppliers|account|direct debit|tariff|meter|reading|arrears|"
    r"energy|gas|electric|electricity|leccy|water|heating|heat|fuel|broadband|internet|"
    r"phone|mobile|insurance|premium|loan|mortgage|rent|council tax|credit card|catalogue|"
    r"overdraft|tv licence|licence fee|subscription|standing order)\b", re.I)
A_SUPPLY_STOPPED = re.compile(
    r"\b(?:cut off|cut me off|cut us off|switched? (?:me|us) off|switch (?:me|us) off|"
    r"disconnect(?:ed)?|disconnection|defaulted|defaulting|in arrears|behind on my payments?)\b",
    re.I)


def _a_bill_and_not_a_person(understood):
    """True when what has not been paid is something a supplier provides.

    A line that says the supply itself stopped ("will they cut me off") passes without naming
    it, because being cut off is only ever a supplier's doing. A bare "not paid" or "havent
    paid" does not: the thing owed has to be named, or the line is about money owed to a person
    and the script for that is in friends.py.
    """
    said = " ".join(str(word) for word in ((understood or {}).get("words") or ())).lower()
    if not said:
        said = str(((understood or {}).get("clean")
                    or (understood or {}).get("text") or "")).lower()
    if A_SUPPLY_STOPPED.search(said):
        return True
    return bool(A_SUPPLIED_THING.search(said))


PAID_AND_CUT_OFF_REPLY = (
    "Ring the supplier before the next bill, not after, and ask for a payment plan you can "
    "keep to: they have to offer one, and the letters stop while it runs. While you are on "
    "the phone, ask to go on the priority services register if anyone in the house is "
    "disabled, ill or under five, and ask about the Warm Home Discount (£150 off one winter "
    "bill) and any hardship fund the supplier runs. Your council's Household Support Fund "
    "covers bills and food, water's own scheme is WaterSure, and Citizens Advice will make "
    "the calls with you for free. Nothing gets cut off today: that takes a warrant.",
)

# One row answers four shapes of the same question - what a fix is, the difference between the two
# rates, which to take, and whether to take one - and it answered all four with the same
# explanation. "should i get a fixed rate" and "fixed rate or variable" were told what the price
# cap is and never which rate to have, so the first sentence said nothing the person had asked
# for. The verdict is the first sentence for the ask that wants one, and the explanation keeps its
# own opening for the ask that wants that. `wants` is not needed here: `asks` is the reading that
# is already there, and the set below is the shapes, not the words of a line.
_ENERGY_WANTS_THE_VERDICT = frozenset(("yesno", "recommend", "choice", "opinion"))
_ENERGY_VERDICT = (
    "Worth it only if the fix comes in under what the cap is likely to do over its term: a fix "
    "buys certainty, so on a falling cap the certainty is all you are paying for and the variable "
    "rate wins on price. Compare the unit rate and the standing charge against today's cap rather "
    "than the monthly estimate, and check the exit fee before signing.")
_ENERGY_EXPLANATION = (
    "The price cap is a limit on the unit rate and standing charge of a standard variable "
    "tariff, set quarterly, so it moves with the market; a fixed tariff holds your rate for "
    "its term whether prices go up or down. Compare the unit rate and the standing charge "
    "rather than the monthly estimate, and check the exit fee before signing a fix.")


def _energy_tariff(memory, reading):
    """The verdict for a choice or a yes/no about a fix, the explanation for what a fix is."""
    asks = set((reading or {}).get("asks") or ())
    return _ENERGY_VERDICT if asks & _ENERGY_WANTS_THE_VERDICT else _ENERGY_EXPLANATION

# A bare "refund" is two words' work: HMRC's, and the money back for a parcel or a purchase.
# The tax-refund scam row is the only row that reads a bare one, so it asks the line whose refund
# it is. Without this, "my sister got a text about a parcel refund" and "i got a text about a
# delivery refund" left the courier card - the one that names the fee-by-text trick - and got
# HMRC's, which is true of neither. A shop, a courier or an order named beside "refund" means
# the refund is theirs; HMRC named beside it means it is HMRC's.
_NOT_THE_TAX_OFFICES_REFUND = frozenset((
    "parcel", "parcels", "delivery", "deliveries", "courier", "couriers", "postage",
    "royal mail", "evri", "hermes", "yodel", "dpd", "ups", "fedex",
    "order", "orders", "ordered", "shop", "shops", "store", "stores", "retailer",
    "amazon", "asos", "ebay", "argos", "seller", "returns", "returned",
))
_THE_TAX_OFFICE = frozenset(("hmrc", "inland revenue", "tax office"))


def _a_refund_the_tax_office_sent(reading):
    """True when the refund in the line is HMRC's rather than a shop's or a courier's."""
    reading = reading or {}
    words = {str(w).lower() for w in (reading.get("words") or ())}
    if "inland revenue" in str(reading.get("text") or "").lower():
        return True
    if words & _THE_TAX_OFFICE:
        return True
    return not (words & _NOT_THE_TAX_OFFICES_REFUND)



ENTRIES = [
    # --- budgeting and saving ----------------------------------------------------
    # "should i use cash or card" was the shrug on main, and "should i pay with cash or card" was
    # the card-on-a-phone answer about Apple Pay, because that row's key carries "pay" and "card"
    # (bronze-whistle). Naming cash is what makes a line the choice between the two.
    entry("cash-or-card",
          (("cash or card", "cash or a card", "card or cash", "cash or contactless",
            "pay cash", "paying cash", "pay in cash", "paid in cash", "use cash", "using cash",
            "with cash", "in cash", "cash only", "legal tender", "cash at home",
            "cash on me", "emergency cash", "keep cash", "refuse cash", "take cash",
            "keep at home", "keep some cash"),
           ("should i", "better", "which", "or", "worth", "how much", "can i", "can a shop",
            "do i", "is it", "why", "refuse", "keep", "pay", "use")),
          _cash_or_card,
          # A payment phrase is a modifier, not a subject. "in cash", "pay cash", "use cash" and
          # "take cash" sit inside other people's questions - "should i tip in cash", "should i
          # pay cash in hand for a builder", "can a tradesman insist on cash", "do i get money
          # off for paying cash" - and asking for one of them let this row take all of those.
          # What makes a line this row's is the comparison itself, so the ask names the choice
          # and not the way of paying: every line below says cash or card, either, better, which,
          # how much cash, or that cash was refused. A row that keys a phrase needs its ask to
          # key the question the phrase is evidence of.
          ask=("cash or card", "card or cash", "cash or a card", "cash or contactless",
               "or card", "or a card", "instead of card", "instead of cash", "or use cash",
               # "worth" was in this list and it is a mood, not a question: "is it worth paying
               # in cash for a discount" is the ask-for-a-discount line, and "worth" alone let
               # this row take it.
               "better", "which is", "which one", "which should", "how much cash",
               "refuse", "legal tender", "keep at home", "keep some cash", "keep cash",
               "cash on me", "emergency cash", "cash only"),
          # a cash ISA, a cash machine and a cash flow are other questions; so is a card that
          # was lost, which is not a choice about how to pay for the shopping
          avoid=("isa", "cash machine", "atm", "cashback", "cash flow", "cash flow forecast",
                 "lost my card", "stolen", "fraud", "overdraft", "payday", "savings",
                 "cash for a car", "cash buyer",
                 # taking money out of a machine abroad is the travel-money answer, which
                 # names two cards and the local currency: "how do i take cash out abroad" is
                 # not a choice between the two ways to pay for the shopping
                 "abroad", "overseas", "travel", "holiday", "holidays", "withdraw", "cash out",
                 "exchange rate", "foreign currency", "travel money"),
          guard=_no_place_named,
          # no bias: a place named in the line ("should i take cash or card to spain") is the
          # travel-money answer, which names two cards and the local currency, and the choice
          # between the two ways to pay is answered wherever nothing else claims the line
          ),
    entry("save-goal-time",
          (("how long", "how many months", "how many years", "how many weeks", "how soon",
            "when will i have", "at a month", "a month", "a week", "a fortnight"),
           ("save", "saving", "saved", "put away", "goal", "deposit", "afford", "target",
            "towards", "holiday", "have", "at", "if",
            # "there is 100 a month spare" is the same rate as "we have 100 a month spare",
            # and without this word it scored 3 against a bar of 4 and the chat lost the sum.
            "spare", "left over", "leftover")),
          _time_to_save,
          # "how long does it need" after a recipe is asking the cooking time. The goal entry
          # used to answer it through the bare word "need", and a bare verb is not a subject.
          avoid=("cook", "cooking", "oven", "bake", "roast", "boil", "recipe", "mince",
                 "chicken", "pasta", "rice", "journey", "flight", "drive",
                 # a sum to be spent is not a sum being put by: "i have 50 pound to last us a
                 # week" is a food week, and the rate table answered it with months at £50.
                 "to last", "to feed", "for food", "to get us to", "no money for food",
                 # the same sum said as a week somebody has to live on rather than a rate to
                 # save at, with the week owning the shop: "i have 20 pounds for a weeks food",
                 # "20 quid for the week". The food week is the answer, and it says the per-day
                 # figure and what to buy.
                 "for a week", "for a week's", "for the week", "weeks food", "week's food",
                 "weeks shop", "weeks shopping", "week of food",
                 # "how long before boarding should i be at the gate" is a flight clock, and the
                 # gate and the airport are not things anybody saves up for.
                 "gate", "boarding", "airport", "check in", "departure",
                 # "how do i save 300 a month" is a plan, not a length of time, so the bare
                 # "a month" that catches "and at 200 a month?" must not take an instruction.
                 "how do i", "how can i", "how should i", "how could i", "best way",
                 "what is the best", "tips", "start saving", "begin",
                 # "I'm on 2,400 a month, how much of it should I be saving" asks for the
                 # share to save, which is the budget answer, not what the rate adds up to.
                 "how much of it", "how much of my", "how much should i be saving",
                 "how much should i save", "what percentage",
                 # a notice on a contract is a length of time to give, not a savings rate:
                 # "my gym contract says i have to give a month notice" got a savings sum.
                 "gym", "gyms", "membership", "health club", "leisure centre",
                 "cancel", "cancelling", "cancellation", "contract", "contracts",
                 # A week off is a block of free time, not a savings rate, and it is the free-time
                 # and holiday rows' subject: "i have 300 pounds and a week off where should i go"
                 # was worked out as £300 a week for a year, and the question in the line - where
                 # to go - was never read. The same goes for the time-off shapes around it, and
                 # for a how-far question, whose "a week" and "pounds" are a budget and a rate.
                 "week off", "weeks off", "week off work", "days off", "few days off",
                 "time off", "where should i go", "where can i go", "where do i go",
                 "where to go", "how far can i go", "how far will", "how far would",
                 "no idea what to do", "nothing to do"),
          # A person saying they cannot save anything is the gap card's line, not a rate
          # question: "i earn 1800 a month and cant save anything" was told what £1,800 adds
          # up to in five years. The guard keeps the row for a line that names the rate it
          # can save, which the avoid list would have thrown away with the same words.
          guard=_the_rate_row_has_a_rate),
    entry("budget-split", (("split", "divide", "budget", "budgeting", "plan", "make a budget",
                            "work out a budget", "make my money",
                            # the same question asked from the tight end: "how do i live on a low
                            # income", "how do i cope on a low income", "how do i get by". The
                            # second part below carries the money word, so these are only the
                            # ways of saying "manage on what i have".
                            "live on", "live off", "get by", "cope with", "cope on",
                            "make ends meet", "manage on"),
                           ("salary", "wage", "pay", "income", "month", "monthly", "money",
                            "start", "first", "make", "set up", "work out",
                            # "how do i stick to it" names no subject, so the verb has to count.
                            # "how do i split my budget" carries both words in one key part, so
                            # budget and plan repeat here to give the line a second signal.
                            "stick", "stick to", "keep to", "stay on", "follow", "track",
                            "budget", "plan")),
          _budget_split,
          # A plan is not a budget: "what plan should i follow" after a marathon answer is a
          # training plan, and the word "plan" alone cannot tell. The line has to carry a money
          # word of its own for this entry to speak - crisp-coconut's report, #answers 18698.
          ask=("budget", "budgets", "money", "salary", "wage", "wages", "pay", "income",
               "spend", "spending", "saving", "savings", "bills", "rent", "month", "monthly",
               "payday", "afford", "costs", "expenses"),
          # "stick to" is how people say "keep to", and it is also how they say "stick to my
          # revision plan", which is not a money question.
          avoid=("diet", "study", "revise", "revision", "exam", "homework", "gym", "exercise",
                 "training plan", "sleep", "quit smoking",
                 # a couple's money is money-and-partner, not a split of one income.
                 "couple", "couples", "share money", "split finances", "household money",
                 "with my partner", "as a couple",
                 # "help me make a meal plan" is a meal plan: the budget bias must not carry
                 # it off the cooking entry.
                 "meal plan", "meal plans", "meal ideas", "recipe", "recipes", "what to cook",
                 "dinner ideas",
                 # a wedding has its own budget answer, and it is the guest list and the venue:
                 # "how do i plan a wedding on a budget" was answered with the payslip split
                 "wedding", "weddings", "getting married", "bride", "groom", "guest list",
                 "registrar", "venue", "hen do", "stag do"),
          # "help me make a budget" ties with a meal-ideas entry on words alone; the budget is
          # the subject and the meals are not.
          bias=1),
    # The thing people are saving for is usually a purchase, not a "goal": a laptop, a bike, a
    # sofa. Naming it in the ask group is what lets a sum in the same line get its arithmetic.
    entry("save-for-a-thing", (("save", "saving", "save up", "put by", "set aside", "afford"),
                               ("laptop", "phone", "iphone", "bike", "bicycle", "sofa", "couch",
                                "washing machine", "fridge", "freezer", "tv", "television",
                                "tattoo", "console", "playstation", "xbox", "switch", "camera",
                                "watch", "ring", "dress", "suit", "kitchen", "bathroom", "shed",
                                "pram", "pushchair", "motorbike", "van", "furniture", "bed",
                                "mattress", "boiler", "hearing aid", "glasses", "invisalign",
                                "braces", "surgery", "course", "driving lessons",
                                # the same thing by its other everyday names, because the
                                # person says buggy or cotbed and not the shop's word for it
                                "buggy", "buggies", "cot", "cots", "cotbed", "cot bed",
                                "moses basket",
                                "car seat", "high chair", "highchair", "travel cot",
                                "baby monitor", "bouncy chair")),
          _save_goal,
          # "how do i save battery on my phone" and "how do i save money charging my phone" are
          # about the phone lasting the day, not about putting money by for one, and "phone" is
          # in the key because people do save up for one. So the battery and the charging words
          # stay here. "how much should i save for a phone charger" is a saving question that
          # names a charger, so a bare "charger" was what took the saving answer away from it.
          avoid=("battery", "batteries", "battery life", "battery dies", "charge", "charging")),
    entry("save-goal", (("save up", "saving up", "set aside", "put away", "budget for", "save",
                         "saving",
                         # "i'm putting by 300 a month" is the same statement as "i want to save
                         # 200 a month" and it got the stock nod instead: the ask group had
                         # "put away" but not "putting by", so the one line that names its rate
                         # in the way people actually say it never reached the arithmetic.
                         "put by", "putting by", "putting away", "putting aside"),
                        ("holiday", "trip", "summer", "christmas", "goal", "target", "present",
                         "wedding", "car", "month", "monthly")),
          # The money set aside for a trip is not the leave you have left: "i have 5 days holiday
          # saved up from last year" is a carry-over question and this row answered it by
          # working backwards from the date, so the leave words stand it down.
          avoid=("days holiday", "days of holiday", "holiday days", "holidays left",
                 "days leave", "days of leave", "annual leave", "holiday entitlement",
                 "carry over", "carried over", "from last year", "use them", "use the days",
                 "days off", "time off", "left over"),
          reply=_save_goal),
    # "how do i start saving" is plans.saving-plan (the habit, with a standing order on pay day);
    # only the low-income version is left to say something new here.

    # --- a payment that was missed, or is about to be -----------------------
    # "what happens if i miss a credit card payment" was the lost-card answer (the card row reads
    # "miss" as "missing") and "i forgot to pay my credit card" was the add-to-wallet one, on
    # 0f368af. Neither answers what the person asked: what a missed payment costs and what to do
    # about it. The row is keyed on the payment being paid by a person - a card, a loan, an
    # instalment - and on a word that says it failed or is at risk, in any order, so "miss a
    # credit card payment", "i paid my card late", "my payment is overdue" and "i forgot to pay
    # my loan" all reach it. The reply reads which of the two it is: a payment not yet due is a
    # phone call that keeps it off the file, one already missed is the fee, the mark and the fix.
    entry("missed-payment",
          (("payment", "payments", "card", "credit card", "store card", "debit card", "loan",
            "instalment", "installment", "direct debit", "minimum payment", "catalogue", "overdraft",
            # the fee itself is the whole subject of some lines: "do i get charged for paying
            # late" names no card and no payment, and was answered by the payroll row.
            "late fee", "late fees", "paying late", "paid late", "failed"),
           ("miss", "missed", "missing", "late", "overdue", "forgot", "forgotten", "forget",
            "forgetting", "bounced", "bounce", "failed", "fails",
            # not a bare "charge": "its about a charge on my card" is a transaction somebody
            # does not recognise, and this row answered it with a late fee. Every line that
            # means a failed payment says so in its own word - missed, late, overdue, forgot,
            # bounced, failed - and the fee lines say "late fee" or "paying late".
            "refund", "refunded",
            "not paid", "didnt pay", "didn't pay", "havent paid", "haven't paid", "behind on",
            "past due", "due date", "arrears", "default", "paid late", "pay late", "paying late",
            "payment is late", "late payment")),
          _missed_payment,
          # "what happens if i miss a payment" is the same question and money-trouble already
          # answers it; this row is the named payment, so it takes those lines.
          bias=1,
          # A rent, a council tax bill or an energy bill that is missed has its own answer, and
          # a score or a report that a payment is on is the credit-score question.
          avoid=("rent", "landlord", "council tax", "council", "energy", "electric", "gas bill",
                 "water", "broadband", "phone bill", "mortgage arrears", "eviction", "bailiff",
                 "credit score", "credit file", "credit rating", "credit report",
                 "how do i set up", "set up a direct debit", "how much is", "when is my payment",
                 # a card that will not tap is the wallet's, not a payment that failed
                 "wont tap", "won't tap", "not tapping", "declined", "rejected", "refused",
                 # a late wage is money somebody owes you, not a payment you missed: the row
                 # keys "paid late" for the fee question and was taking every wage line with
                 # it - "i got paid late again this month" got "a late fee, interest from the
                 # day you were due", which is the opposite way round.
                 "my pay", "our pay", "my wages", "our wages", "my salary", "our salary",
                 "paid me late", "paid us late", "paid late again", "get paid late",
                 "getting paid late", "got paid late", "was paid late", "were paid late",
                 "been paid late", "paid late every month", "payday again",
                 # and a charge you dispute is money you were charged, not a payment you missed:
                 # "how do i dispute a card charge" keys on card + charge here, and the
                 # chargeback row (section 75, 120 days) is the answer to it
                 "dispute", "disputed", "disputing", "chargeback", "charge back", "section 75",
                 "unauthorised", "unauthorized", "didnt authorise", "didn't authorise",
                 "i didnt buy", "i didn't buy", "never arrived", "overcharged", "twice",
                 # A payment the state owes you is not a payment you missed: "my uc payment is
                 # late" got the late-fee-and-interest card, which is the opposite way round.
                 # The benefit rows answer it (lifeadmin, benefit-payment-not-arrived).
                 "benefit", "benefits", "universal credit", "dwp", "jobcentre", "job centre",
                 "pip", "esa", "tax credits", "child benefit", "hardship payment",
                 # the benefit names people type short
                 "uc", "universal credit payment", "benefit payment", "benefit money")),

    # "im skint this month" is not a plan and not a shrug: it is the one line where a person is
    # telling you the money has run out, and the useful thing is the two calls that take ten
    # minutes. Kept to the shapes people type by hand, because "money is tight" on its own is
    # already answered by the low-income saving plan and must stay there.
    #
    # "broke" is a state only when it is said of the person: "my phone broke" and "my glasses
    # broke" are a thing that broke, and the bare word plus the possessive in the second key
    # sent every one of them to the energy-tariff answer. The state is keyed by the shapes people
    # use for it (the be-form or an adverb in front, a payday after), never by the verb alone, so
    # a possession before "broke" cannot make it a money line. "i broke my phone" was already
    # kept out by the avoid list; this covers the other word order.
    entry("money-trouble",
          (("skint", "im broke", "i'm broke", "i am broke", "we are broke", "we're broke",
            "so broke", "completely broke", "totally broke", "proper broke", "dead broke",
            "flat broke", "always broke", "still broke", "currently broke", "broke till",
            "broke until", "went broke", "gone broke", "going broke", "go broke",
            # not "broke this" / "broke again" / "broke now": those are the verb with an object
            # and a time ("my kettle broke this morning"), and "im broke" already covers the
            # state with a time after it.
            "im poor", "i am poor", "we are poor", "poor this month",
            "hard up", "penniless", "no money", "not got any money",
            "not got enough money", "short of money", "strapped for cash", "on the breadline",
            "cant afford", "can't afford", "cannot afford", "can not afford", "living on very",
            "nothing left", "run out of money", "ran out of money", "running out of money",
            "run out of cash", "ran out of cash",
            # the same subject in the past tense: "im spent up this month", "i spent all my
            # money already", "i spent my wages by tuesday"
            "spent up", "spent it all", "spent all my money", "spent all of it",
            "spent all my wages", "spent my wages", "spent every penny", "spent my pay",
            "spent all my pay", "spent my money",
            # The joke people make when the money runs out early: "i have too much month left at
            # the end of the money" was echoed back at them ("Thanks for telling me"), because no
            # word of it was a phrase this entry knew. The phrase is the whole question.
            "too much month", "month left at the end", "month at the end of the money",
            "end of the money", "any money left", "no money left", "money left",
            "money doesnt stretch", "money doesn't stretch", "pay doesnt stretch",
            "pay doesn't stretch", "wages dont stretch", "wages don't stretch",
            # A card that cannot be paid this month, said the ways people say it. The line
            # reached the add-to-wallet row ("cant pay" and "credit card"), and with "shift"
            # in it reached nothing at all, so a debt of 2000 pounds was answered with a mood
            # line. Naming the debt is the whole of what these phrases do.
            "cant pay my card", "cant pay the card", "cant pay my credit card",
            "cant pay the credit card", "can't pay my card", "can't pay my credit card",
            "cant pay it off", "can't pay it off", "cant pay this month",
            "cant pay it this month", "cant make the payment", "missed a payment",
            "miss a payment", "behind on my card", "behind on the card",
            "maxed out", "maxed my card", "maxed my overdraft", "overdraft",
            "dipping into my overdraft", "in my overdraft", "into my overdraft",
            "living in my overdraft",
            "only paying the minimum", "paying the minimum", "just the minimum"),
           ("i", "im", "i'm", "we", "we're", "my", "our", "this", "month", "week", "payday",
            "money", "everything", "anything", "food", "gas", "electric", "until", "now",
            "moment", "afford", "skint", "broke", "at all", "left", "end of the month",
            # the debt words, so a card, an overdraft or a balance is a purse question too
            "card", "credit card", "debit card", "overdraft", "debt", "debts", "balance",
            "payment", "interest", "minimum", "pound", "quid", "grand")),
          _money_trouble,
          guard=_a_purse_in_trouble,
          # A rent or a bill that cannot be paid has its own answer, and so does a shop, a meal
          # or a night out: those entries say something concrete about the thing itself.
          # "run out before payday" is the weekly-pay question and has its own answer; a Mac
          # that says it has run out of room is not this at all (see devices.py).
          avoid=("before payday", "rent", "landlord", "eviction", "council", "housing", "mortgage", "bill",
                 "bills", "energy", "electric", "gas", "water", "council tax", "food bank",
                 "car", "insurance", "school", "trip", "holiday", "present", "christmas",
                 "wedding", "takeaway", "dinner", "lunch", "shop", "shopping", "groceries",
                 "haircut", "heating",
                 # someone else's empty purse is not this: "he has no money" is a line about
                 # him, and the money answer would be advice handed to the wrong person.
                 "he", "she", "him", "her", "his", "hers", "they", "them", "their",
                 "hes", "shes", "theyve", "hes got", "shes got", "theyve got",
                 "my mum", "my dad", "my son", "my daughter", "my brother", "my sister",
                 "my friend", "my friends", "my mate", "my mates", "my partner",
                 "my husband", "my wife", "my kids", "my children", "my nan", "my gran",
                 "my grandma", "my grandad", "my uncle", "my aunt", "my cousin", "my boss",
                 "my boyfriend", "my girlfriend", "my neighbour", "my neighbour's",
                 # "im not broke" is someone telling you they are all right, so a negation in
                 # front of the word is not the word.
                 "not skint", "not broke", "not poor", "not hard up", "not short of money",
                 "no longer skint", "no longer broke", "isnt skint", "isnt broke",
                 # "broke" is a verb more often than a state: "i broke my phone", "i broke the
                 # boiler", "the car broke down" are things to fix, not a month with no money.
                 # "my glasses broke", "my phone broke", "the boiler broke": the thing before
                 # "broke" matters as much as the words after it, and a repair is not a purse.
                 # ("broken" is not on this list on purpose: it is one form of "broke", so it
                 # would turn "im broke this month" down as well)
                 "glasses", "spectacles", "sunglasses", "snapped", "smashed", "cracked",
                 # a phone battery that drains is the battery answer's line, even when the
                 # person adds that they cannot afford £80 for anything
                 "battery", "batteries", "phone battery",
                 "phone broke", "laptop broke", "screen broke", "boiler broke",
                 "washer broke", "washing machine", "hoover", "vacuum", "kettle", "toaster",
                 "broke the", "broke my", "broke a", "broke it", "broke his", "broke her",
                 "broke down", "broke up", "broke into", "broke out", "broke even",
                 "broke free",
                 # and "poor" is an adjective about a thing as often as about the person: "i have
                 # poor sleep", "my poor back", "poor thing" are not the purse.
                 "poor sleep", "poor back", "poor health", "poor quality", "poor service",
                 "poor weather", "poor appetite", "poor memory", "poor concentration",
                 "poor circulation", "poor eyesight", "poor sight", "poor diet", "poor grammar",
                 "poor thing", "poor you", "poor baby", "poorly",
                 # a gift card or a voucher with money on it is not a purse that has run out:
                 # "is there money left on my gift card" was answered with two cheaper tariffs
                 # (see MONEY_ALREADY_ON_A_CARD)
                 ) + MONEY_ALREADY_ON_A_CARD),
    entry("save-small-salary", (("small salary", "low wage", "low income", "tight", "struggle",
                                 "dont earn much", "don't earn much", "not much money"),
                                ("save", "saving", "savings", "budget", "afford", "money")),
          ("Start absurdly small if that's all there is: £5 a week by standing order on payday. Then "
           "find the money in the bills, a fresh energy comparison, a cheaper mobile or broadband "
           "contract and the subscriptions you forgot about usually free up £20 to £50 a month, and "
           "add whatever they save you."),
          # "I'm on a tight budget, 40 pounds a week for food" then "what should i buy?" is the
          # weekly shop, not the habit of saving: a shopping question is never a saving plan.
          avoid=("food", "food shop", "food shopping", "weekly shop", "groceries", "supermarket",
                 "meals", "cook", "dinner", "dinners", "buy", "buying", "shop", "shopping",
                 "purchase")),
    # "i have 20 pounds until friday" is the same question as "how do i make 30 pounds last a
    # week": a sum, a day, and what it buys between the two. Keyed by the shape rather than by
    # the amount, so every sum gets the arithmetic.
    entry("make-it-last",
          (("pounds until", "pounds till", "pounds to last", "pounds left", "quid until",
            "quid till", "quid left", "money until", "money till", "money to last", "to last",
            "last me", "last us", "make it last", "make it stretch", "make ends meet",
            "see me through", "get me through", "get me to", "tide me over", "only got",
            "i have left", "left for the week", "for the week", "for a week",
            "get paid on", "paid on friday", "paid next week", "waiting to be paid",
            "make 20 pounds", "make 30 pounds", "make 50 pounds", "make it to payday"),
           ("till", "til", "until", "before", "friday", "monday", "tuesday", "wednesday",
            "thursday", "saturday", "sunday", "tomorrow", "today", "tonight", "week",
            "weekend", "payday", "month", "fortnight", "what should i do", "how do i",
            "how can i", "what do i do", "food", "eat", "feed", "meals", "groceries",
            "what can i", "help")),
          _make_it_last,
          bias=3,
          # a pound of weight is not a pound of money, and a week of training is not a week of
          # food: the gym and the diet rows key "pounds" and "week" as well
          avoid=(
                 # the sum and the span that the cheap-week card above already works out well -
                 # "£8 over 4 days is £2 a day" with the staples and the buy order - is not
                 # this row's line: it answers the same sum with less to put in the trolley,
                 # so the lines that reach that card keep their own answer.
                 # days of leave are not a sum of money: "how much leave do i have left, i only
                 # work 4 days a week" was answered with the £3-a-day food card, because "i have
                 # left" and "week" are this row's two words
                 "days leave", "much leave", "leave left", "leave balance", "leave allowance",
                 "annual leave", "days of leave", "days a week", "days off", "holiday entitlement",
                 "last me", "last us", "to last", "pounds left", "quid left", "money left",
                 "left for the week", "left for the month", "left till", "left until",
                 "last a week", "last a month", "last a fortnight", "last the week",
                 "lose", "losing", "lost", "weight", "stone", "kilos", "kg", "lbs", "diet",
                 "slim", "slimming", "calories", "barbell", "dumbbell", "bench", "squat",
                 "deadlift", "lifting", "gym", "run", "running", "walking", "steps",
                 "rent", "landlord", "eviction", "mortgage", "arrears", "mortgage",
                 "save", "saving", "savings", "pension", "invest", "stocks", "isa",
                 "holiday", "wedding", "car", "deposit", "house", "loan", "credit card",
                 "overdraft", "interest", "apr", "wage slip", "income", "salary",
                 "how much is", "how much does", "how much are", "cost", "price",
                 # a bill is a bill: "my energy bill is 200 a month" is not a sum to last
                 "bill", "bills", "energy", "electric", "gas", "council tax", "water",
                 # and money to take abroad is spending money, not money to live on: "how much
                 # spending money should i take for a week" is a travel answer
                 "spending money", "take for", "take on holiday", "abroad", "travel", "trip",
                 "holiday", "hotel", "flight", "currency", "exchange", "euros", "dollars"),
          ask=("i have", "i've got", "ive got", "i got", "got", "only", "how", "what", "make",
               "last", "stretch", "left", "budget", "week", "until", "till")),
    entry("emergency-fund", (("emergency fund", "emergency savings", "rainy day fund",
                              "aside for emergencies", "emergencies", "emergency", "savings",
                              "saved"),
                             ("how much should i", "how much do i", "how much is",
                              # "what is an emergency fund" names the thing and asks what it is,
                              # which is the figure, not a habit to start.
                              "what is", "what is an", "whats", "whats an", "what's an",
                              "how many months", "how big", "start", "build", "need", "size",
                              "save", "keep", "have in savings", "saved",
                              # "is 3k enough of an emergency fund" is the size question with
                              # a number in it, and the word that carries it is "enough"
                              "enough", "cover", "covers", "sufficient")),
          ("Three to six months of essential spending is the usual target, counting rent or "
           "mortgage, bills, food and travel rather than your whole salary. If that feels far off, "
           "aim for £1,000 first in an instant-access account you don't touch for anything else."),
          # Saving for a named thing is that thing's answer: a deposit, a car or a holiday has a
          # price and a date, and "three to six months of spending" is a different question.
          avoid=("house", "flat", "home", "deposit", "car", "holiday", "wedding", "goal",
                 "trip", "mortgage", "for a house", "towards a",
                 # "how much do I need to put by each week" is a rate for a sum already named,
                 # not the size of the buffer.
                 "each week", "per week", "a week", "put by", "put aside",
                 # "do i need to pay tax on my savings" asks about HMRC, not about three months.
                 "tax", "taxed", "taxable", "hmrc", "tax free", "tax-free",
                 # a rate is which account pays well, not how big the buffer should be: "what is
                 # a good interest rate for a savings account" was answered "three to six months
                 # of spending" once the compound-interest row stood down.
                 "interest rate", "interest rates", "rate of interest", "good rate",
                 "good interest", "best rate", "best interest", "which account",
                 "which savings account", "savings account")),
    # A person saying where their money is, with no question in it (see _NO_SAVINGS). Placed
    # before the goal and rate rows so the state wins over the bare word "savings".
    entry("savings-gap", (_NO_SAVINGS, _NO_SAVINGS_WRAPPER),
          _savings_gap,
          # A named target is that target's answer, and the size of the buffer is the
          # emergency-fund card: those say something concrete about the thing asked for.
          avoid=("house", "flat", "deposit", "mortgage", "car", "holiday", "wedding", "trip",
                 "pension", "retirement", "retire", "isa", "lisa", "interest", "rate", "rates",
                 "tax", "taxed", "hmrc", "invest", "investing", "stocks", "shares",
                 # A person with no savings who also owes money is owed the debt-first order,
                 # not a savings start: "what should i do about having no savings" was answered
                 # with the £500-in-an-afternoon card, and the order card is the better answer
                 # because £1,000 in savings while a card runs at 24% is the wrong way round.
                 "debt", "debts", "credit card", "credit cards", "overdraft", "pay later",
                 "klarna", "loan", "loans", "owe", "owed", "borrowed", "interest on",
                 # and the same when the line asks for an order of business rather than
                 # stating where the money is: "what should i do" is the resolve question
                 "what should i do", "what do i do", "what can i do", "where do i start",
                 "which first", "what first", "order",
                 "how much", "how many", "is it worth", "worth it", "which account",
                 "which savings", "best account", "should i put", "how do i open",
                 # another person's savings is a question about them, not advice for the person
                 # typing: "my mum has no savings for retirement" is her pension.
                 "he", "she", "him", "her", "his", "hers", "they", "them", "their",
                 "my mum", "my dad", "my son", "my daughter", "my brother", "my sister",
                 "my friend", "my partner", "my husband", "my wife", "my kids", "my nan",
                 "my gran", "my grandma", "my grandad",
                 # A person who has just lost the wage is owed the job-loss answer, not a
                 # standing order paid out of a payday that has gone: "i lost my job and have no
                 # savings" was told to open a savings account and set up a £50 transfer.
                 "lost my job", "lost his job", "lost her job", "lost the job", "job",
                 "jobs", "redundant", "redundancy", "unemployed", "unemployment", "sacked",
                 "laid off", "jobseekers", "job seekers", "job centre", "job center",
                 "out of work", "between jobs", "no job")),

    entry("save-goal-week", (("each week", "a week", "per week", "put by", "put aside",
                              "saved by", "save by", "have saved", "have 500 saved"),
                             ("how much", "need", "should", "save", "saved", "saving",
                              "goal", "total", "each")),
          _put_by,
          # "a week" and "how much" are all this key needs, so "how many hours a week should i
          # work out", "how much work a week would it be" and "which phrases should i learn
          # before a week in portugal" all got a saving rate. A rate to save toward something
          # is the only line here that names saving or putting money by, so one of those words
          # has to be in it.
          ask=("save", "saving", "saved", "saves", "savings", "put by", "put aside", "set aside",
               "put away", "squirrel away", "squirreling away"),
          # a habit with a price is habit-cost's arithmetic, and the weekly food shop is food's.
          # "saved by 30" is an age to aim for, not a weekly amount for a named sum.
          avoid=("by 30", "by 40", "by 50", "by 35", "by 25", "by 45", "by 55", "my age", "behind",
                 "on track", "coffee", "latte", "lunch", "lunches", "sandwich", "meal deal", "takeaway",
                 "takeaways", "pint", "pints", "beer", "cigarettes", "fags", "smoking", "smoke",
                 "vape", "snack", "snacks", "food", "groceries", "weekly shop", "budget for food",
                 "days a week", "times a week", "should i run", "should i be running",
                 "how many days", "how often",
                 # "what should i pack in hand luggage for a week" carries "a week" and
                 # "should", and it is a packing list, not a saving rate: no saving line says
                 # pack, suitcase or flight.
                 "pack", "packing", "packed", "luggage", "suitcase", "carry on", "hand bag",
                 "flight", "fly", "travel", "abroad", "wear", "outfit", "kit list",
                 # "what should i bring for a week in scotland" and "what should i take with me
                 # for a week" are the same question, and "bring" and "take" are how people put
                 # it. No saving line says bring, take with, or what to take.
                 "bring", "bringing", "brought", "what should i take", "what to take",
                 "what do i take", "take with", "what should i bring", "what to bring",
                 "what do i bring", "what do i need to bring",
                 # "a week" plus "how much" is a many-subject question: how much to train, walk,
                 # swim or drink a week, or a week of night shifts. A weekly sum is only the
                 # answer to a money line, so the other subjects stand this entry down.
                 "train", "training", "walk", "walking", "run", "running", "gym", "exercise",
                 "swim", "swimming", "drink", "drinking", "water", "learn", "learning",
                 "language", "languages", "lessons", "night shift", "night shifts", "nights",
                 "shift", "shifts", "study", "studying", "revision", "screen time", "episodes",
                 # money for a trip is the trip's answer, not a rate of saving: what to take out,
                 # and how much to spend a week somewhere, is the travel question.
                 "spending money", "holiday money", "currency", "euros", "dollars",
                 "take out", "to spend", "spend a week", "spend each week", "week in",
                 "withdraw", "withdrawal",
                 # and a line about a body is answered by the health modules, whatever period
                 # it happens to say ("feeling dizzy for a week, should i worry").
                 _BODY)),
    # A conversion is money, and nothing in the module answered one: "how much is 100 euros in
    # pounds" was the diet plan, because the only row that holds "pounds" is the weight one, and
    # "why is the exchange rate so bad" was nothing at all. The rate cannot be quoted from here -
    # it moves every day and this bot has no clock and no network - so the answer is where the
    # rate comes from and what actually costs the money, which is the fee rather than the rate.
    entry("currency-conversion",
          # The left side is the *other* currency, never "pounds": a conversion always names the
          # currency it is going to, so "how much is 100 pounds in euros" has "euros" in it and
          # "i spend 4 pounds a day on coffee, how much is that in a year" has nothing here. The
          # word "pound" in this key was worse than useless - it put a money word into the
          # vocabulary of every line that weighs something, so "how much is 3 pounds of potatoes"
          # lost its price card to a portion answer and "how much is 1 pound of chicken" to the
          # roasting time. A row must not own a word that is another domain's subject.
          (("euros", "euro", "dollars", "dollar", "currency", "exchange rate", "exchange",
            "convert", "conversion", "sterling", "yen", "cents", "rupees"),
           ("how much", "how many", "much is", "many is", "worth", "rate", "convert", "change",
            "in euros", "in dollars", "against", "strong", "weak", "get for", "would i get",
            "do i get", "buy")),
          ("Exchange rates move every day, so I cannot give you a figure that will still be right "
           "tomorrow: your bank's app or any currency converter has the rate this minute. What "
           "costs more than the rate is the fee on top of it - a normal debit card abroad often "
           "adds about 3% and hides a mark-up in the rate, while a travel card or a bank that uses "
           "the mid-market rate adds nothing on weekdays, and the kiosk at the airport is the worst "
           "rate you will find. For a purchase, pay in the local currency when the machine offers "
           "to convert for you, because that conversion is the seller's own and it is always worse "
           "than your bank's."),
          # a body is weighed in pounds and a bag is limited in kilos: only money lines come here,
          # and the diet plan has its own row for the other reading of the same word.
          # a pound on its own is a sum of money spent on something, so the line also has to name
          # a second currency or ask for a rate: that is what makes it an exchange question.
          ask=("euros", "euro", "dollars", "dollar", "currency", "exchange rate", "exchange",
               "convert", "conversion", "sterling", "yen", "cents", "rupees", "in pounds",
               "in euros", "in dollars", "to the pound", "to the euro", "rate"),
          avoid=("lose", "losing", "lost", "weight", "diet", "dieting", "slim", "kilos", "kilo",
                 "kilograms", "stone", "stones", "how heavy", "baggage", "suitcase", "allowance",
                 "per kilo", "pound of", "pounds of", "flour", "butter", "mince", "roast")),
    entry("track-spending", (("track", "tracking", "monitor", "work out where",
                              # "where does all my money go" is the same question without a verb.
                              "where does my money go", "where does all my money go",
                              "where my money goes", "where does the money go",
                              "where my money went"),
                             ("spending", "expenses", "outgoings", "money", "budget",
                              "go", "goes", "went")),          ("Write down every purchase for a month, or let your banking app sort it into "
           "categories. The surprises are nearly always takeaways, subscriptions and small card "
           "taps, and seeing them once is what makes cutting them easy.")),
    entry("lifetime-isa", (("lifetime isa", "lisa", "lifetime"),
                           ("what", "is", "mean", "explain", "worth", "open", "should i",
                            "should we", "better", "how", "deposit", "house", "home",
                            "first home", "bonus", "25")),
          ("A Lifetime ISA pays 25% on what you put in, up to £1,000 a year, and you can pay in "
           "until you are 50. The money has to go on a first home under £450,000 or wait for "
           "retirement at 60 - take it out for anything else and the 25% charge takes the bonus "
           "back, so it suits deposit money you will not touch for a year, not savings you might "
           "need sooner."),
          bias=2,
          # "is a cash ISA worth it" is the general question, not this one.
          avoid=("cash isa", "stocks and shares isa", "isa allowance", "savings account",)),
    entry("isa", (("isa", "isa or", "lifetime isa", "stocks and shares"),
                  ("savings", "save", "worth", "better", "account", "money", "lifetime",
                   "what", "explain", "mean", "is", "how", "allowance", "limit", "how much",
                   "put in", "pay in", "a year", "reset", "pay into", "open", "worth it",
                   # "can i have a cash isa and a stocks and shares isa" names two products and
                   # asks whether both are allowed: no other word in it is an ask, so it was the
                   # honest pass on main. The count words below are the ask in that line.
                   "can i have", "both", "same year",
                   # "can i have more than one isa" carries no other key word: the count is the ask
                   "more than one", "how many", "two", "several", "another", "second",
                   "number of")),
          _isa, bias=2,
          # a phone's data allowance is the other "how much allowance do i get", and a junior
          # isa is a child's account with its own entry
          avoid=("phone", "data", "mobile", "roaming", "gb", "texts", "minutes", "junior",
                 "child", "children", "kids", "my son", "my daughter",
                 # a premium bond line after an ISA turn is read with the ISA still in the
                 # subject, and "how much" then looks like the allowance question: name another
                 # product and the ISA entry refuses it whatever the reading carries
                 "premium bond", "premium bonds", "lottery", "winnings", "bonds", "bond",
                 # "pension or isa" and "savings or stocks and shares" are choices between two
                 # kinds of home for the money, not a question about what a cash ISA is
                 "pension", "pensions", "or savings", "savings or", "or stocks",
                 "stocks and shares or", "shares or")),
    entry("pension-or-savings",
          (("pension", "pensions", "workplace pension", "private pension", "sipp",
            "auto enrolment", "auto-enrolment"),
           ("savings", "saving", "isa", "better", "worth", "or", "vs", "versus", "instead",
            "rather", "more money in", "pay more in", "extra",
            # "would you recommend a pension" is the same choice asked as a recommendation, and
            # the same goes for the annuity and drawdown row below.
            "recommend", "recommended", "recommendation", "recommendations")),
          ("Into the pension first, as far as the employer's contribution goes: they have to add "
           "at least 3% on top of your 5%, and the tax relief adds another 20% of what you pay, "
           "so nothing a savings account offers comes close. Above that, a stocks and shares ISA "
           "is the more flexible place, because pension money is locked up until 55 (57 from "
           "2028). Keep three to six months of bills in an easy-access account whatever else you "
           "do, and if you are self-employed a private pension or a SIPP gets the same tax relief."),
          # the dates and amounts of a pension, the choices inside one and the age you can take
          # it are their own answers
          # a choice that names both sides is this row, above the savings-account rate and the
          # cash-ISA explainer, which both matched on one side of the choice
          bias=2,
          avoid=("when can i", "what age", "how much do i need", "enough to retire",
                 "tax free", "lump sum", "drawdown", "annuity", "opt out", "state pension",
                 "how much is", "how much will", "forecast", "contribution rates",
                 # a freelancer has no employer to match anything, so the employer-contribution
                 # half of this card is not the answer: self-employed-pension owns that line
                 "freelance", "freelancer", "freelancing", "self employed", "self-employed",
                 "sole trader", "contractor", "my own business", "run my own business")),
    entry("savings-or-investing",
          (("stocks", "shares", "investing", "invest", "stock market", "index fund",
            "tracker fund"),
           ("savings", "saving", "cash", "savings account", "or savings", "or cash",
            "instead of savings", "rather than savings")),
          ("Cash for anything you will need within five years, and a global index tracker inside "
           "a stocks and shares ISA for money you can leave longer: the tracker has grown more "
           "than cash over any twenty-year stretch, but it can be down 20% or 30% for a year or "
           "two, and that is fine only if you do not have to sell. A common split is three to "
           "six months of bills in an easy-access account, then everything above that in the "
           "tracker, added to every month rather than all at once."),
          bias=2,
          # a share of a bill, a folder shared with someone, and a soup are not investments
          avoid=("share my", "share a", "share the", "his share", "her share", "their share",
                 "my share", "our share", "split the", "stock cube", "stock cubes", "soup",
                 "gravy", "broth", "how do i make stock", "chicken stock", "beef stock",
                 "vegetable stock", "crashed", "gone down", "sell my")),    # Interest is taxed as income, and that surprises people, so the allowance gets its own
    # answer rather than the "compare the AER" one.
    entry("savings-tax", (("tax", "taxed", "taxable", "hmrc", "allowance", "tax free"),
                          # "how much is the savings allowance" is the amount of interest you can
                          # take tax free, and it was answered with the phone's data page: the
                          # phrases name the amount so the emergency-fund row cannot take it either
                          ("savings", "saving", "interest", "isa", "allowance",
                           "how much is the savings allowance", "how much savings allowance",
                           "savings allowance", "tax on savings", "savings tax")),
          ("Most people pay no tax on savings interest: the personal savings allowance covers "
           "£1,000 of interest a year if you are a basic-rate taxpayer and £500 if you are higher "
           "rate, and additional-rate payers get nothing. Interest inside an ISA is always tax "
           "free, and anything over the allowance is taxed at your income tax rate."),
          # "allowance" is the shared word, and "how much is the uniform tax allowance" was this
          # answer: the flat rate for a uniform is not a savings question
          avoid=("uniform", "uniforms", "laundry", "work clothes", "work clothing", "overalls"),
          bias=1),
    # "Where should my savings go?" is not the habit and not which account pays most: it is the
    # order to do things in. On main it was the habit script (a standing order and two weeks of
    # tracking), which is an answer to "how do I start saving" asked by someone who has already
    # saved.
    entry("where-savings-go",
          (("my savings", "savings", "saved up", "i have saved", "my money", "spare money",
            "extra money", "money sitting", "sitting in my", "i have a few thousand"),
           ("where", "best place", "put", "keep", "park", "sit", "sitting", "go", "do with",
            "leave it", "long term")),
          ("Put it in this order. First clear any credit card, overdraft or pay-later debt, "
           "because that costs 20% or more a year and nothing safe pays that. Second, build three "
           "to six months of essential bills in an easy-access account - instant access, no "
           "notice, no card, so a broken boiler is an annoyance rather than a loan. Third, money "
           "you will not touch for five years goes into a global index tracker inside a stocks "
           "and shares ISA; anything you will need sooner stays in cash, where the rate is lower "
           "but the money is there. If it is for a first home, a Lifetime ISA adds 25% up to "
           "\u00a31,000 a year, and that is the best return you will get for that goal."),
          # a savings *account* comparison, a lump sum or an inheritance, a tax question and a
          # rate question are all their own answers, and money that is gone needs no plan
          avoid=("account", "accounts", "rate", "rates", "aer", "interest", "tax", "isa",
                 "pension", "lump sum", "inherited", "inheritance", "windfall", "bonus",
                 "gone", "lost", "losing", "stolen", "scam", "fraud", "sofa", "tv", "wardrobe",
                 "picture", "furniture", "plant", "bed", "desk", "car", "debt", "credit card",
                 "overdraft", "loan", "holiday", "christmas", "wedding", "deposit", "house",
                 # money kept safe while away is what to carry and where, not the order to put
                 # savings in: "how do i keep my money safe travelling" took the savings plan
                 "travel", "travelling", "traveling", "abroad", "overseas", "trip", "vacation",
                 "when i travel", "while away",
                 "flat", "mortgage", "rent", "how do i start", "how do i save", "how to save"),
          bias=2),
    entry("savings-account", (("savings account", "savings rate", "easy access", "savings"),
                              # "how" on its own is not an ask: a bare "how" let this entry take
                              # "how long will the saving take", which is the goal's timing
                              ("best", "good", "interest", "rate", "choose", "which",
                               "worth", "compare", "should", "what", "mean", "explain", "open",
                               "work", "account",
                               # "where should i keep my savings" is which account to hold it
                               # in, not the habit of saving. "where" only; a bare "keep" here
                               # answered "where should i keep my bike".
                               "where")),
          ("Compare the AER rather than the headline rate, and pick instant access for money you "
           "might need and a one or two-year fix for money you won't. Watch for a bonus rate that "
           "drops after a year, and keep under £85,000 with one bank so the protection scheme "
           "covers all of it."),
          # "is my savings interest taxed" is a tax question, not a rate question, and
          # "how long will that take" is the goal's arithmetic, not which account to pick.
          avoid=("tax", "taxed", "taxable", "hmrc", "tax free", "tax-free",
                 # a goal's timing, not "how long should I fix this rate for", which is this entry
                 "how long will that take", "how long will it take", "how long does that take",
                 "how long until i have", "how long to save", "how long would it take",
                 # "should i use my savings to clear my card" is the pay-off-or-save
                 # comparison, not which account to open
                 "clear my card", "clear my credit", "pay off my card", "pay off the card",
                 "pay off my credit", "or clear", "card debt", "overpay", "mortgage")),

    # "my savings arent growing" is the question the rate rows never heard: `where-savings-go`
    # answers where to put money and stands down on rates, and `savings-account` wants a comparison
    # word, so the plain statement of a flat account fell to the free-money-advice referral and to
    # "I'm listening". The person already knows the number is flat; what they need is the rate, the
    # switch, and the point at which cash stops being saving and starts being losing.
    entry("savings-not-growing",
          (("savings", "my savings", "savings account", "savings pot", "savings rate",
            "cash isa", "isa", "instant access", "easy access", "emergency fund",
            "interest", "money in the bank", "my money in the bank"),
           ("arent growing", "isnt growing", "not growing", "arent going up", "isnt going up",
            "not going up", "arent earning", "isnt earning", "not earning", "barely earning",
            "hardly earning", "earning nothing", "earns nothing", "pays nothing",
            "paying nothing", "pays next to nothing", "no interest", "rubbish interest",
            "awful interest", "losing value", "losing money", "going backwards",
            "worse than inflation", "behind inflation", "not keeping up", "stagnant",
            "sitting there", "doing nothing", "not worth saving", "no point saving")),
          ("Check what it actually pays: under about 3% while prices rise means the money buys "
           "less each year, whatever the balance says. Move it to an account paying more - a "
           "regular saver or a one-year fix beats a branch account - keep three to six months of "
           "bills in easy access, and put money you will not touch for five years into a global "
           "tracker inside a stocks and shares ISA."),
          # paying debt, a pension, a goal's timing and a named account to compare are other rows
          avoid=("debt", "credit card", "overdraft", "loan", "pay off", "pay it off", "clear my",
                 "mortgage", "pension", "rent", "house", "deposit", "car", "wedding",
                 "how much should i save", "how do i save", "how do i start saving",
                 "save up", "each month", "a month", "per month", "how long", "which account",
                 "best account", "compare", "better account", "should i switch", "worth it",
                 "what is", "whats a", "mean", "explain", "how does")),

    # --- credit and debt ---------------------------------------------------------
    entry("credit-vs-debit", (("credit card", "debit card", "credit or debit",
                               "debit or credit"),
                              ("difference", "between", "versus", "vs", "better", "safer",
                               "which one", "should i use")),
          ("A debit card spends money you already have, straight from your current account; a "
           "credit card borrows from the card company and you pay it back later. Use debit for "
           "everyday spending and a credit card for big purchases or travel, where the extra "
           "protection helps, then clear the full balance each month so it costs nothing."),
          # "is it better to save or clear my credit card" and "should i use my savings to pay
          # off my credit card" name both cards, and the difference between a debit card and a
          # credit card is not the question: the interest on the debt against the interest on
          # the savings is, and that is the overpay comparison. Keep it off this row.
          avoid=("or save", "or saving", "or savings", "or invest", "than saving",
                 "instead of saving", "pay off", "pay it off", "paying off", "clear my card",
                 "clear the card", "clear my credit card", "use my savings", "in savings",
                 "savings", "overpay", "settle early", "minimum payment")),
    # "what is a good interest rate on a credit card" was the pay-more-than-the-minimum answer,
    # which never names a rate at all. A rate question wants the numbers and how to read them.
    entry("card-rate",
          (("credit card", "credit cards", "card", "cards", "store card", "balance transfer"),
           ("interest rate", "interest rates", "rate", "rates", "apr", "good rate", "what rate",
            "typical rate", "typical apr", "low rate", "best rate", "cheapest rate",
            "how much interest", "what interest", "good interest", "bad rate", "0%", "zero per",
            "is 20%", "is 25%", "is 30%")),
          "A normal credit card charges about 20% to 25% APR, a card for people with a thin file "
          "can be 30% or more, and a 0% purchase or balance-transfer deal is the cheap way to "
          "borrow for a set time. The representative APR is only the rate at least 51% of accepted "
          "applicants get, so check the rate you are actually offered before you apply, and add "
          "any annual fee. Paid in full each month, none of it matters - no interest at all.",
          # a minimum payment, clearing the card, which card to get and a balance transfer's
          # length are each their own answer
          avoid=("minimum", "minimum payment", "pay off", "paying off", "clear my card",
                 "clear the card", "clear my credit", "or save", "savings", "which card",
                 "should i get", "apply for", "balance transfer fee", "how long", "worth it",
                 "better than", "vs", "versus", "debit card", "overdraft", "loan")),
    entry("credit-card-debt", (("credit card", "card", "cards", "minimum payment",
                                "pay more than the minimum",
                                # The minimum paid and nothing off the balance, said without the
                                # word card: "i pay the minimum every month", "im paying the
                                # minimum", "we only pay the minimum", "should i pay the minimum
                                # or more". The minimum-payment answer is the whole of what these
                                # lines want, and without a group-one word they reached no entry
                                # and were echoed back at the person.
                                "pay the minimum", "paying the minimum",
                                "pay only the minimum", "only pay the minimum",
                                "just pay the minimum", "just the minimum",
                                "only the minimum", "the minimum every month",
                                "the minimum each month", "minimum or more", "minimum only"),
                               ("pay off", "debt", "minimum", "interest", "clear", "owe",
                                "balance", "quickest", "fastest", "pay more", "only",
                                "pay towards", "pay each month", "pay every month",
                                "pay back", "repay",
                                # the words can sit apart: "pay my credit card off" never says
                                # "pay off", so the debt question had no entry of its own and the
                                # wallet's "card" + "pay" was the only thing that could claim it.
                                "pay my card off", "pay the card off",
                                "pay my credit card off", "pay my debit card off",
                                "pay it off", "installments", "instalments",
                                # A balance that will not come down, said as a thing stuck:
                                # "my credit card is 2000 pound and i cant shift it" reached no
                                # entry at all and was answered with a mood line. It is the
                                # minimum-payment answer, which is why the balance does not move.
                                "cant shift it", "cant shift the balance", "can't shift it",
                                "cant get it down", "cant get the balance down",
                                "wont go down", "doesnt go down", "doesn't go down",
                                "not going down", "barely moves", "hardly moves",
                                "never goes down", "stuck at")),
          _card_payoff,
          # "Should I pay off the card or save it instead" is the overpay question, and it needs
          # the choice, not the minimum-payment lecture.
          avoid=("or save", "or saving", "save or", "saving or", "savings or",
                 "or invest", "vs saving", "than saving", "instead of saving",
                 "or overpay", "or put it in savings",
                 # "i have 3000 in savings, should i pay off my card" is the same comparison the
                 # overpay row makes: the minimum-payment lecture answers a different question.
                 "savings", "in savings", "saving account", "nest egg",
                 # "pay the minimum" is also said about a wage and about a student loan, and
                 # neither is a card: the wage has its own entry and the loan is the debt order.
                 "wage", "wages", "national minimum", "living wage", "employer",
                 "student loan", "student loans", "pension", "child maintenance",
                 # a card with money already on it is not a debt: the gift card and the prepaid
                 # card carry a balance that nobody owes, and the honest reply is the shop's number
                 # rather than a lecture on interest (see MONEY_ALREADY_ON_A_CARD)
                 ) + MONEY_ALREADY_ON_A_CARD),
    # Borrowing to clear a card is its own question: the answer is a comparison of rates, not
    # the pay-more-than-the-minimum lecture or the which-debt-first order.
    entry("consolidate-loan",
          (("loan to pay", "loan to clear", "consolidate", "consolidation", "take out a loan",
            "get a loan", "borrow to pay", "borrowing to pay"),
           ("card", "cards", "credit", "debt", "debts", "balance", "balances", "owe", "owing",
            "pay off", "clear", "clear it", "pay it off", "credit card", "credit cards",
            "card debt", "card debts")),
          _pay_off,
          # a loan for a car, a house or a wedding is a different question, and so is a loan
          # between friends
          avoid=("car", "cars", "house", "flat", "deposit", "wedding", "holiday", "business",
                 "student", "friend", "friends", "mate", "mum", "dad", "brother", "sister",
                 "family", "borrowed off",
                 # "how do i get a loan with bad credit" arrived here on "get a loan" plus
                 # "credit" and was told to check a card rate: that is a different question, and
                 # it has its own row below
                 "bad credit", "no credit", "credit history", "credit score", "credit file",
                 "universal credit", "on benefits", "guarantor", "lender", "lenders",
                 "turned down", "refused")),
    entry("balance-transfer", (("balance transfer", "card balance", "moving my balance",
                                "move my balance", "switch my balance", "interest free card",
                                "zero percent card", "0 percent"),
                               ("worth", "deal", "better", "should", "save", "cheaper", "work",
                                "card")),
          ("A 0% balance transfer is worth it when the fee, usually 1-3% of the balance, is less "
           "than the interest you'd pay over the same months. Set a fixed payment that clears the "
           "balance before the 0% period ends, because the rate jumps to around 20% after it."),
          # "card balance" is also what a gift card and a prepaid card carry, and this row read
          # it as the moving-a-credit-card-balance question: "check my gift card balance" was
          # told about a 0% transfer, and "how much is left on my voucher" the same. A card with money
          # already on it, and a balance already sitting on a card, are not this question.
          avoid=MONEY_ALREADY_ON_A_CARD),
    # The definition was the one overdraft question main could not answer: "how do overdrafts
    # work", "what is an overdraft", "what happens if i go overdrawn" and "is an arranged
    # overdraft cheaper than an unarranged one" all got the honest shrug, while the charges and
    # clearing answers below already name a cost. The first key group is the account going below
    # zero, the second is the asking-to-have-it-explained, and the avoid list hands the cost, the
    # charges and the way out back to the entry under this one.
    entry("overdraft-basics",
          (("overdraft", "overdrafts", "overdrawn", "overdrew", "into the red",
            "go overdrawn", "gone overdrawn", "below zero"),
           ("what is", "what are", "whats", "what happens", "how do they work",
            "how does it work", "how do overdrafts work", "work", "works", "explain",
            "explained", "mean", "means", "understand", "dont understand",
            "don t understand", "difference", "differ", "arranged", "unarranged",
            "unauthorised", "unauthorized", "limit", "basic", "basics", "simple terms",
            "how does an overdraft work",
            # Asking the bank to give you one is the same card: "how do i ask my bank about an
            # overdraft" names no definitional word at all, so it scored one part and the purse
            # row (which carries "overdraft" in both its key groups) took it and answered with
            # two cheaper tariffs. The asking words are the second part of this question.
            "ask my bank", "ask the bank", "ask about", "ask for", "how do i ask", "what do i say",
            "can i get", "how do i get", "get one", "get an overdraft", "arrange", "arranged one",
            "set up", "open one", "apply", "apply for", "increase", "raise my", "bigger")),
          ("An overdraft is a loan from your bank that lets your balance go below zero. You agree a "
           "limit in advance and pay interest or a daily fee for the days you use it, so it is "
           "borrowed money rather than extra money, and it has to be paid back. Arranged means the "
           "limit was agreed with the bank and is the cheaper version; unarranged means you spent "
           "past it, which costs more, can bounce payments and is marked on your credit file. Some "
           "accounts give a small fee-free buffer, usually about £10 to £25, and the cheapest way to "
           "use one of these is to move money across at the start of the month and be back in "
           "credit before the deepest days."),
          avoid=("how much", "cost", "costs", "charge", "charges", "fee", "fees", "get out",
                 "clear", "pay off", "reduce", "avoid", "stop", "deep", "student")),
    entry("overdraft", (("overdraft", "overdrawn", "overdrew", "into the red"),
                        ("get out", "clear", "avoid", "charges", "cost", "fee", "fees", "reduce",
                         "stop", "pay", "deep", "why")),
          ("Arranged overdrafts are charged per day now, so the deepest days cost the most: move a "
           "fixed amount onto it every payday and keep spending within what's left. Ask your bank "
           "for a repayment plan if the balance is large, and think about a basic account with no "
           "overdraft if it keeps happening.")),
    entry("first-credit-card", (("credit card",),
                                ("first", "get", "should", "need", "apply", "best", "one",
                                 "worth", "worth it", "good idea", "good", "worthwhile")),
          ("A credit card is worth having if you clear it in full every month: it builds a credit "
           "history and gives you protection on purchases over £100. Start with a card for bad or "
           "no credit history if that's you, set a direct debit for the full balance each month, "
           "and never use it for cash or to spend money you don't have."),
          # "Should I pay off my credit card or save" is the overpay question, and "which card
          # first" is the debt order: neither one is asking which card to get.
          avoid=("pay off", "pay it off", "or save", "or saving", "clear", "clearing",
                 "minimum", "balance", "overpay", "which debt", "which card first",
                 "debt first", "or invest")),
    entry("credit-score", (("credit score", "credit rating", "credit report", "credit file",
                            "credit history", "build credit", "build my credit",
                            # "build up my credit" said with the up in it, which is how most
                            # people say it: the phrase key missed and the line got the
                            # MoneyHelper card instead of the three steps
                            "build up credit", "build up my credit", "building my credit",
                            "rebuild my credit", "repair my credit",
                            "no credit history", "credit record"),
                           ("improve", "check", "fix", "bad", "better", "free", "build",
                            "start", "how", "good", "what is", "what's", "whats", "range",
                            "average", "number", "raise", "raising", "boost",
                            # the same subject said as a change: "my credit score has dropped" and
                            # "why has my credit rating gone down" were shrugs, so the entry only
                            # answered the question and not the thing that happened
                            # a score that moved either way is the same question in two
                            # directions, and the reply callable reads which one it was
                            "dropped", "drop", "drops", "gone down", "went down", "went up",
                            "gone up", "goes up", "rose", "risen", "increased", "improved",
                            "climbed", "fallen", "fell", "lower", "decreased", "why has",
                            "why did", "what happened", "changed", "change",
                            # a missed or late payment is asked of the score in its own words
                            "affect", "missing a payment", "miss a payment", "missed a payment",
                            "missed payment", "late payment", "paid late", "pay late",
                            # how a score is described rather than what is done to it: "my
                            # credit score is low" was an echo, because "low" was not a key
                            # word and "lower" is a different one
                            "low", "poor", "awful", "rubbish", "terrible", "messed up",
                            "stuck", "none", "nothing",
                            # building one, which is the same steps said as a job to do
                            "build up", "building", "rebuild", "repair", "start from",
                            "getting a", "how do i get")),
          _credit_score,
          # `score` and `good` are also GCSE grade words: the score itself is the subject here.
          bias=1),
    entry("pay-later", (("buy now pay later", "klarna", "clearpay", "pay in three"),
                        ("bad", "worth", "safe", "afford", "miss", "late", "cost", "work",
                         "catch", "risky", "trap", "good", "idea", "ok", "fine")),
          ("It's fine for something you'd buy anyway and can clear on the due date; the trouble "
           "starts when it's used to afford things you couldn't. Missed payments bring late fees "
           "and can show on your credit file, so count each instalment as money already spent.")),
    entry("student-loan", (("student loan", "student loans", "student debt"),
                           ("pay off", "pay it back", "pay back", "repay", "repayment", "worth",
                            "early", "overpay", "what is", "how much", "mean", "explain")),
          ("A student loan pays the tuition fee and the maintenance money while you study, and it "
           "is only paid back through your pay once you earn over the threshold: 9% of what you "
           "earn above about £25,000 a year on plan 5, taken like tax and stopping the month your "
           "pay drops below it. The fee part covers the whole fee, and the maintenance part is "
           "sized to your household income and whether you live at home or away. Repaying early is "
           "rarely worth it, because anything left after 30 to 40 years, depending on the plan, is "
           "written off.")),
    # A grant is money you do not pay back, and the difference from a loan had no card at all:
    # "what is the difference between a grant and a loan", "do i have to pay back a grant" and
    # "what is a bursary" were the honest punt, and "is a scholarship free money" the shrug.
    entry("grant-not-a-loan",
          (("grant", "grants", "bursary", "bursaries", "scholarship", "scholarships",
            "maintenance grant", "student grant", "hardship fund", "hardship grant"),
           ("what is", "what are", "difference", "pay back", "paid back", "repay", "repayment",
            "have to pay", "free money", "need to pay", "is it", "are they", "how do i get",
            "how do i apply", "apply for", "where do i get", "entitled", "eligib", "mean")),
          ("A grant is money you keep; a loan is money you pay back. A bursary or a scholarship is "
           "the same kind of thing as a grant - the university, the council or a charity gives it "
           "and it is not repaid - while a student loan comes out of your pay once you earn over "
           "the threshold. Grants for students are mostly from the university's own hardship fund, "
           "so ask the student advice service in your first week; outside college there are "
           "council welfare schemes, and charities that give one-off grants for a boiler, a bed or "
           "a course. Always ask whether a grant is means tested, what it can be spent on, and "
           "whether it counts against your benefits."),
          # a loan in the line is a different question when it is the borrowing one, and the
          # student loan has its own repayment answer; this row is only the grant side
          avoid=("loan shark", "payday", "interest rate", "apr", "how much can i borrow",
                 "compare", "best loan", "cheapest loan", "guarantor", "car loan",
                 "mortgage", "overdraft", "credit card", "pay off", "overpay",
                 # a grant to start a business is the startup-funding card's question, and
                 # that card answers it better: where the money comes from and what to apply
                 # for first. "grant" alone was enough to win "how do i get a business
                 # grant", which was then told about university hardship funds.
                 "business", "businesses", "company", "companies", "startup", "startups",
                 "start up", "start ups", "new business", "sole trader", "self employed",
                 "self-employed", "small business", "trade", "shop", "enterprise"),
          bias=1),
    # "Where do I go for money advice" asked a source question and got the lender card,
    # because "money" and "where" are the borrow row's own words. Free advice has its own
    # answer: the three free services, what each one is for, and the fact that it is free.
    entry("free-money-advice",
          (("money advice", "advice about money", "advice on money", "advice with money",
            "advice about my money", "debt advice", "advice about debt", "advice on debt",
            "free debt advice", "free money advice", "free advice", "debt charity",
            "debt charities", "who can help", "who do i call", "who do i phone",
            "who should i call", "where can i get advice", "where do i go for advice",
            "where do i go for help", "where do i get advice", "where do i get help",
            "is debt advice free", "is it free", "do i pay for", "should i pay for",
            "debt is out of control", "debts are out of control", "out of control"),
           ("money", "debt", "debts", "advice", "help", "bills", "bill")),
          # Only when the line names money, a debt or a bill: the plain word "help" was a subject
          # of this row as well as an ask, so a line could reach it on its own asking words with
          # nothing of the row's subject in it ("who can help me with the kids" was told where to
          # get free debt advice). `ask` is the mechanism for exactly this. 
          "Don't pay anyone for it: Citizens Advice, StepChange and National Debtline all give "
          "debt advice free, and MoneyHelper is the government's own service. Ring StepChange if "
          "there are several debts and you want a plan written to the people you owe; ring "
          "National Debtline to work it out yourself with someone on the phone; go to Citizens "
          "Advice for a benefit, a bill or a bailiff. Have your income, what you owe and any "
          "letters to hand, and ask them to write the plan down.",
          # borrowing, a bill you cannot pay and being short this month are three other answers,
          # and a bare "debt" here would steal all three
          avoid=("borrow", "borrowing", "loan", "loans", "lender", "lenders", "credit card",
                 "payday", "cant pay", "can't pay", "cannot pay", "cant afford", "can't afford",
                 "behind on", "skint", "broke", "frozen", "scam", "gambling", "payday loan"),
          ask=("money", "debt", "debts", "bill", "bills", "owe", "owed", "owes", "arrears",
               "creditor", "creditors", "overdraft", "out of control")),
    # The plain shapes of the question miss the key: "how do i get out of debt" names no
    # priority word, "how do i clear my debts" reached the UCAS clearing answer in study, and
    # "how do i start paying off my debt" went to overpay with the compare-the-interest answer.
    # The phrases are here so the question that asks what to do next reaches this entry.
    entry("debt-priority", (("debts", "debt", "behind on", "creditors",
                             # the shape a person uses when they want the whole way out, not
                             # the order of one debt: "im in debt and dont know what to do",
                             # "how do i get out of debt", "how do i clear my debts",
                             # "how do i get rid of it", "deal with creditors", "debt free"
                             # NOT "get out of debt" / "out of debt": those words are the
                             # second part's own ("get out", "out of"), and a phrase here that
                             # covers them leaves the entry with one signal, so "how do i get
                             # out of debt" scored nothing and the signpost answered it.
                             "in debt", "debt free",
                             "debt-free", "clear my debt", "clear my debts", "clear the debt",
                             "clear the debts", "pay off my debt", "pay off my debts",
                             "pay it off", "best way to pay", "snowball"),
                            ("first", "priority", "which", "where", "start", "pay",
                             "get out", "out of", "clear", "clearing", "rid", "deal with",
                             "dealing with", "sort out", "sorting out", "pay off",
                             "paying off", "reduce", "manage", "cope with", "handle",
                             # People ask to "get out of debt", to "sort out" it or to
                             # "become debt free" - not for the word "priority". Without
                             # these the line reached the money signpost and a listening
                             # noise instead of the answer that says which debt to pay first.
                             "get out of", "help with", "become debt free", "debt free",
                             "out of control", "what do i do", "how do i", "drowning",
                             # "my debts are piling up" names the subject and the trouble and
                             # still reached the chat echo, so the trouble has its other words.
                             # "the bills are piling up" has no debt word and stays an echo.
                             "piling up", "piling", "mounting", "adding up",
                             "struggling", "cant cope", "can't cope", "where to start",
                             # "im in debt and dont know what to do" reaches neither "what do i
                             # do" nor "where to start", so the not-knowing has its own words
                             "dont know", "don't know", "no idea",
                             # "my debt keeps growing" names the trouble as a trend, which is
                             # the same ask as "the debts are piling up"
                             "growing", "growing every month", "keeps growing", "keeps",
                             "help")),
          ("Pay the debts that keep a roof over your head first: rent or mortgage, council tax, "
           "energy and water, because those escalate fastest. Credit cards and loans come next, "
           "smallest balance first if you need momentum or highest interest first if you want to "
           "pay least. Before anything gets out of hand, one free call to StepChange or Citizens "
           "Advice is worth more than any spreadsheet."),
          # A card's own payoff is the card answer (the minimum payment, the APR), a loan taken
          # out to clear cards is the consolidation answer, a student loan is its own row, and
          # an overpayment against a mortgage or a savings pot is the overpay comparison.
          avoid=("credit card debt", "card debt", "card debts", "minimum payment",
                 "minimum payments", "student loan", "student debt", "student loans",
                 "overdraft", "mortgage", "overpay", "overpaying", "or save", "or saving",
                 "or invest", "loan to pay", "consolidate", "balance transfer",
                 # a line that names where the money would come from is the comparison, not the
                 # order: "can i get a loan to clear my debts", "should i use my savings to pay
                 # off my debt" want the rate and the interest, and the order is the answer to
                 # the ask that names nothing but the debts.
                 "loan", "loans", "borrow", "borrowing", "savings", "consolidation",
                 # a refund, a chargeback and a debt someone else owes you are not your debt
                 "refund", "money back", "chargeback", "shop", "seller", "owe me",
                 "owes me", "lent", "lend", "borrowed off", "friend", "friend's",
                 # a person at the door is the bailiff answer and not being able to pay this
                 # month is the payment-plan answer. The row's bias of 2 let "deal with" and
                 # "pay" pull both back here, and the order to pay is advice for someone still
                 # deciding, not for someone already being called on.
                 "debt collector", "debt collectors", "bailiff", "bailiffs",
                 "cant pay", "can't pay", "cannot pay",
                 # A line with no money in it and a length to get through is the week's
                 # answer (the food bank, the payment plan), not the order to pay the debts
                 # in: "how do i get out of debt when i have no money" was the priority card
                 # the moment the row started answering the bare "get out of debt".
                 "no money", "nothing left", "nothing coming in", "cant afford",
                 "can't afford", "cannot afford", "food bank", "jobseekers",
                 "universal credit", "on uc", "skint", "broke", "nothing in the account"),
          # a way out of the debts, as a whole, is this row even when the words also fit the
          # overpay comparison: "how do i clear my debts" is the order to pay them in, while
          # "should i pay off my debt or save" names both sides and reaches the comparison.
          bias=2),
    # "what is a debt management plan" and "whats the difference between a dmp and an iva" are
    # explainers, and they were both a shrug: the two named plans are the whole question.
    entry("debt-plans", (("debt management plan", "debt management", "dmp", "dmps",
                          "iva", "ivas", "individual voluntary arrangement",
                          "debt relief order", "debt relief", "dro", "protected trust deed",
                          "trust deed", "debt arrangement scheme", "debt arrangement"),
                         ("what", "whats", "what's", "difference", "between", "better",
                          "which", "explain", "how does", "is a", "is an", "mean", "means",
                          "worth it", "should i")),
          _debt_plans,
          # a plan for paying one card off is the payoff answer, not this one
          avoid=("pay off", "pay it off", "paying off", "minimum payment", "which debt first",
                 "overpay", "settle early")),
    # "credit card or savings first", "savings or clear the card", "pay the card or save it" ask
    # the comparison without a payoff verb, so they reached no money row at all and the composer
    # handed back "Toss a coin and see if you're disappointed with how it lands". The two sides
    # of the choice are the subject, so a phrase with both sides is a form of this row.
    entry("overpay", (PAY_OFF + OR_SAVE,
                      ("mortgage", "loan", "debt", "worth", "should", "better", "penalty",
                       "savings", "save", "saving", "card", "interest", "faster", "quicker",
                       "sooner", "early", "ahead", "lump sum", "minimum")),
          _pay_off,
          # "How do I get my friend to pay back a loan" is a favour between two people, not
          # money you could put against your own debt.
          # "repay" is the same verb as "pay off", so it keys this row rather than standing it
          # down; what stood down was the favour-between-friends sense, and that is the words
          # below.
          avoid=("friend", "friends", "mate", "mum", "dad", "brother", "sister", "pay back",
                 "pay it back", "lent", "lend", "lending", "borrowed", "owes me", "owe me",
                 "repay me", "repay him", "repay her", "repay them", "to repay me", "family",
                 # "which is cheaper, a loan or a credit card" is the loan-against-a-card
                 # comparison, not an overpayment: two different questions
                 "loan or a card", "loan or credit card", "loan versus", "loan vs")),

    entry("interest-compounding", (("interest",),
                                ("compound", "compounding", "work", "explain", "grow")),
          ("Interest earning interest: £1,000 at 5% becomes £1,050 after a year, then £1,102.50, "
           "because the second year's 5% is on the larger amount. Left alone at 5%, money roughly "
           "doubles every 14 years; the same works against you on a credit card.")),
    entry("pay-yourself-first", (("nothing left", "anything left", "end of the month", "each month",
                                  "every month", "standing order", "automatic", "automate",
                                  # The answer to "what is left each month?" is a figure, and the
                                  # figure had no entry: "i get about 200 left after the bills"
                                  # right after the savings answer asked for it was a shrug, and
                                  # the same line without "get" got nothing at all. The money
                                  # words below keep "two slices left over" out of it.
                                  "left after the bills", "left after bills",
                                  "left after the rent", "left after rent",
                                  "left over after the bills", "left over after rent",
                                  # the same sum with "this month" instead of "each month":
                                  # "i have 200 left over this month" was a shrug once the
                                  # leftovers rows stopped answering it
                                  "left over this month", "left over a month",
                                  "left over per month", "left this month",
                                  "pay myself first",
                                  # money that is spare rather than named: "i have 150 spare at the
                                  # end of the month" was a nod and "i've got 200 quid spare this
                                  # month, what should i do with it" a search hedge, while the same
                                  # sum said as "left over" was answered. A sum that is spare is a
                                  # sum looking for somewhere to go, and the standing order on
                                  # payday is the answer to it.
                                  # the month phrases and not the bare "spare", and no "left over":
                                  # a left-over sum with no month in it is the windfall ladder's -
                                  # "i have some money left over what now" wants the order to pay
                                  # things off in. And "i have spare money what should i do" stays
                                  # the ladder's too, because a habit card that says "move 25 on
                                  # payday" is the smaller answer to it.
                                  "spare each month", "spare this month", "spare every month",
                                  "spare at the end of the month", "spare at the end of each month",
                                  # the week as the period, and the one-word spelling: a sum left
                                  # over "each week" is the same question as one left over "each
                                  # month", and with the food rows standing down on the period the
                                  # line had nowhere to go but the habit echo ("You have 200
                                  # leftover each week. That's a habit now.")
                                  "left over each week", "left over every week",
                                  "leftover each week", "leftover every week",
                                  "left over each month", "leftover each month",
                                  "left over a week", "leftover a week",
                                  "spare each week", "spare every week",
                                  # a want said flat: "i want to save more money" had no entry of
                                  # its own and work.py's "more money" key sent it to the pay-rise
                                  # meeting. The phrase is the want, not the sum.
                                  "save more money", "saving more money"),
                                 ("saving", "save", "start", "better", "tip", "money", "left",
                                  # the ask shapes a spare sum comes in: "what should i do with it"
                                  "what should i do", "what do i do", "what to do", "with it",
                                  "what now", "where should i put",
                                  # the sum as it is told, with no ask at all: "i have 150 spare
                                  # at the end of the month" is a sum and a month, and the standing
                                  # order is the thing to do with it
                                  "end of the month", "end of each month", "end of every month",
                                  "spare",
                                  # the sum said as a leftover rather than as "spare", and in
                                  # either spelling: with the food rows standing down on "each
                                  # week" the line needed somewhere to land, and a sum left over
                                  # each month is the standing order's question
                                  "leftover", "leftovers", "left over",
                                  "it")),
          ("Move the saving out on payday, not at the end of the month: a standing order for even "
           "£25 the day you're paid works better than saving whatever is left, because nothing is "
           "ever left. Raise it by £5 whenever a bill goes down."),
          # a saving with a named target is that target's answer (the wedding budget, the
          # Lifetime ISA, the advance train fare); this is the habit with no target. `rent` is
          # not here: "i get 150 left after the rent" is the same figure as the bills shape, and
          # with `rent` in this tuple the three rent keys above were stood down by their own row,
          # so the answer to "what is left after the rent" was "Got it." A rent that is the
          # subject of its own question says "rent" and a saving word ("i want to save for a rent
          # deposit", "how much rent can i afford") and is answered by those rows.
          avoid=("pension", "mortgage", "deposit", "loan", "card", "wedding", "holiday",
                 "house", "car", "train", "clothes", "food", "phone", "energy", "heating",
                 "bank", "account",
                 # "spare" is also a part you keep: a spare wheel, a spare key, a spare room and
                 # a spare tyre are things, not money
                 "spare wheel", "spare tyre", "spare tire", "spare key", "spare keys",
                 "spare room", "spare bedroom", "spare part", "spare parts", "spare bulb",
                 "spare battery", "spare rib", "spare ribs", "goes spare", "going spare",
                 "time to spare", "spare time", "an hour to spare")),
    entry("cut-first", (("cut back", "cut out", "cut first", "what to cut", "trim my spending",
                         "cut my spending", "biggest saving", "where can i save",
                         "where should i save", "spending to cut"),
                        ("first", "biggest", "most", "which", "where", "start", "save", "saving",
                         "monthly", "outgoings", "expenses")),
          ("Take the biggest single line first and halve it rather than cutting it out: bought "
           "coffee and lunches are usually the largest and easiest, and going from five a week to "
           "two saves more than cancelling a handful of small subscriptions. Set a weekly limit "
           "for that one thing and stop when it is gone."),
          # "cut" is everywhere - hair, onions, grass - so this needs the spending words too.
          avoid=("hair", "onion", "onions", "grass", "hedge", "wood", "finger", "bread", "slice",
                 "meat", "nail", "nails", "paper", "cable", "wires", "cardboard",
                 # "not cut out for teaching" is a doubt about a person, and "cut out" alone put
                 # the spending card on it. The phrase, not the word, is the spending question.
                 "cut out for", "cut out to")),

    entry("cook-vs-takeaway", (("cook at home", "cooking at home", "cook or takeaway",
                                "takeaway or cook", "eat at home", "ready meal", "ready meals",
                                "meal kit", "takeaway", "takeaways", "take out",
                                # the same question with no takeaway in it: "is it cheaper to
                                # cook from scratch" reached the travel fares table through
                                # "cheapest", and the answer was a coach versus the train
                                "cook from scratch", "cooking from scratch",
                                "cheaper to cook", "cost of cooking", "cooking cost",
                                "home cooked", "home-cooked", "cook my own"),
                               ("cheaper", "cheap", "better", "worth", "or", "vs", "instead",
                                "healthy")),
          ("Cooking from scratch is usually a fifth of the price: a home-cooked portion costs about "
           "£1.50 to £2.50 where a takeaway is £8 to £12, so three swaps a week saves £1,000 a "
           "year. The catch is the waste, so plan the week's meals before you shop and cook double "
           "on the nights you are already at the hob."),
          # "is it cheaper to cook or buy takeaway" ties with the dish follow-ups on the words,
          # and the money in the line is the question, so this answer takes the tie
          bias=2, avoid=("calories", "healthy", "diet", "weight",
                         # "take out" is a phrase people use for anything they take out: insurance,
                         # a warranty, a pension, a loan, the bins, a court order. The row keys it,
                         # so a line that takes something out and asks whether it is worth it got
                         # the cooking-versus-takeaway answer ("is it worth taking out travel
                         # insurance" was £8 to £12 a takeaway for one).
                         "insurance", "insure", "warranty", "extended warranty", "pension",
                         "annuity", "loan", "mortgage", "remortgage", "credit card",
                         "phone contract", "sim only", "gym membership", "subscription",
                         "bins", "bin day", "rubbish", "trash", "recycling", "court order",
                         "restraining order", "licence", "license", "permit", "cash", "savings",
                         # pastry, bread, pasta and a cake "from scratch" are the baking rows
                         "pastry", "bread", "pasta", "cake", "cakes", "biscuits", "sauce",
                         "stock", "mayo", "mayonnaise", "hummus", "pesto", "curry", "yorkshire")),
    entry("dish-cost", (("chilli", "chili", "chilli con carne", "chili con carne", "bolognese",
                         "spag bol", "spaghetti bolognese", "lasagne", "lasagna",
                         "cottage pie", "shepherds pie", "shepherd's pie", "fish pie",
                         "roast", "roast dinner", "sunday roast", "roast chicken",
                         "curry", "dhal", "dal", "lentil", "soup", "pizza", "stew",
                         "casserole", "risotto", "stir fry", "macaroni cheese",
                         "mac and cheese", "sausage and mash", "toad in the hole",
                         "cake", "bread", "loaf", "scones", "brownies", "pancakes",
                         "porridge"),
                        ("cost", "costs", "costing", "cost me", "cost to make",
                         "cost of making", "what does it cost", "how much does it cost",
                         "per portion", "a head", "a portion", "per head", "cheaper to make",
                         "make it myself", "make my own", "price", "prices", "expensive",
                         "afford", "budget")),
          _dish_to_cook_cost,
          # The dish is the subject and the money is the question, so the dish words lead. The
          # lines this answers were answered by other rows: "how much does a chilli cost to make"
          # by the spices card ("chilli" is a spice in its key and "how much" is how an amount of
          # spice is asked), "how much does a home made pizza cost" by the house-price card, and
          # "what does a chilli cost per portion" by "prices move too fast for me to know".
          # "how much chilli powder" has no money word and stays with the spices row, and a
          # takeaway or a restaurant is somebody else's price, not the shopping.
          bias=1,
          avoid=("takeaway", "takeaways", "take out", "takeout", "deliveroo", "just eat",
                 "justeat", "uber eats", "restaurant", "eating out", "eat out", "meal deal",
                 "chippy", "fish and chips", "dominoes", "pizza hut", "pizza express",
                 "mcdonalds", "nandos", "greggs", "cafe", "powder", "flakes", "paste",
                 "jar", "sauce jar", "calories", "frozen", "ready meal", "delivery",
                 "cost of living", "energy", "gas bill", "electric", "oven cost",
                 "how much to charge", "charge for", "sell my", "sell them",
                 "per hour", "wage", "buy a", "buying a", "buy one", "shop bought",
                 # a price said about bread or a dish in a shop is the shops question, not the
                 # shopping list: "a cut on the price of bread" was answered with the loaf here
                 "price of", "price cut", "cut on the price", "price rise", "price cap",
                 "price hike", "went up", "gone up", "going up", "inflation", "on offer",
                 "reduced", "shop price", "supermarket price", "cheaper in the shop")),
    entry("teach-kids-money", (("pocket money", "teach my kids about money",
                                "teach children about money", "teach kids about money",
                                "money with my kids", "kids and money",
                                # the same question asked as explaining rather than as pocket
                                # money: "how do i explain money to my kid" reached nothing
                                "explain money", "explaining money", "understand money",
                                "value of money", "about money to", "money to my kid",
                                "money to my kids", "money to my child", "money to my children",
                                "money to my son", "money to my daughter",
                                "teach my kid about money", "teach my child about money",
                                "teach my son about money", "teach my daughter about money",
                                "teach kids money", "learn about money", "learns about money"),
                               ("how", "much", "should", "start", "age", "when", "old",
                                "give", "explain", "explaining", "teach", "teaching", "learn",
                                "understand", "value", "say", "tell",
                                # The asking, said as a complaint: "my kids keep asking for pocket
                                # money" has no how/much/age in it and was answered with a nod.
                                "ask", "asks", "asking", "asked", "want", "wants", "wanted",
                                "keeps asking", "nagging", "nagging me",
                                # "is pocket money a good idea" is the same question asked as an
                                # opinion, and it reached the fallback that says it does not know.
                                "good", "idea", "worth it", "worth", "works", "work")),
          ("Start pocket money at about six, a small fixed amount on the same day each week, and "
           "let them spend it badly while the sums are still small. Split it into spend, save and "
           "give jars so the saving is visible, and pay extra for jobs beyond the normal helping "
           "rather than docking the basics. Say prices out loud when you shop and name the choice "
           "you are making - \"the small one is £3 or the big bag is £5, which is better value?\" "
           "- and keep it about what money does rather than what it is: what we save for, what a "
           "bill is, and why the card is not free money."),
           # "how do i send money to my son in australia" is a transfer, and the key above holds
           # "money to my son": the far side of the line is what tells the two apart, so the
           # sending words and the countries stand this row down. `travel.send-money-abroad` has
           # the answer.
           avoid=("send money", "sending money", "sent money", "transfer", "transfers",
                  "bank transfer", "abroad", "overseas", "australia", "canada", "usa",
                  "america", "spain", "france", "poland", "romania", "nigeria", "india",
                  "pakistan", "philippines", "ireland", "germany", "currency", "wise",
                  "western union", "paypal"),
           # "my son wants pocket money for the xbox" lost to the Xbox settings card and "she
           # wants pocket money for sweets" to a crumble, because the thing the money is for is
           # also a word in another domain's key. What the money is for is not what is being asked
           # when the line says pocket money, so this row takes the tie.
           bias=2),
    entry("impulse-buying", (("impulse", "tempted", "overspending", "stop spending",
                              "spending money", "keep buying", "buy things",
                              "buying things", "buy too much", "buying too much",
                              "shopping too much", "stop shopping", "keep ordering",
                              "always buying", "buy less", "spend less", "cut back on",
                              "stop buying", "stop ordering", "buying so many",
                              "cut down on", "cut my spending"),
                             ("avoid", "stop", "buy", "buying", "shop", "shopping", "sales",
                              "stuff", "things", "clothes", "clothing", "shoes", "trainers",
                              "makeup", "make up", "skincare", "jewellery", "handbags",
                              "gadgets", "games", "books", "amazon", "ebay", "plants",
                              "not", "dont", "help", "money", "much", "need")),
          ("Use a 24-hour rule: put it on a wishlist and decide tomorrow, because most of the "
           "wanting fades overnight. Take the saved card off the sites you use, and give clothes "
           "and fun a monthly figure on their own card, so the month decides instead of the "
           "evening. Keeping a list of what you already own helps too - the gap that gets bought "
           "into is usually a gap you cannot see."),
          # Food has its own entry below: the planned-night advice is right for a takeaway and
          # nonsense for a pair of shoes, which is what this answer was saying before.
          # A week somewhere is an amount to take, not a habit to break: "how much spending money
          # for a week in rome" matched the phrase in the key and "how much" in the other group,
          # so it got the 24-hour rule. The length and the place make it travel's question.
          avoid=("time", "study", "learn", "practice", "takeaway", "takeaways", "fast food",
                 "coffee", "coffees", "deliveroo", "just eat", "uber eats", "eating out",
                 "lunch", "restaurant",
                 # cutting down on what you eat or drink is not a spending habit: "i need to cut
                 # down on sugar" got the wishlist rule, which says nothing about sugar. The key
                 # holds "cut down on" for clothes and games, so the habits it is not about stand
                 # it down - as whole phrases, because "i keep buying salt and vinegar crisps" is
                 # a spending line and must keep the wishlist answer.
                 "cut down on sugar", "cut down on salt", "cut down on sweets",
                 "cut down on chocolate", "cut down on fizzy", "cut down on snacks",
                 "cut down on crisps", "cut down on alcohol", "cut down on booze",
                 "cut down on drinking", "cut down on caffeine", "cut down on smoking",
                 "cut down on vaping", "cut back on sugar", "cut back on salt",
                 "cut back on alcohol", "cut back on booze", "cut back on drinking",
                 "less sugar", "less salt", "eat less", "eating less", "drink less",
                 "losing weight", "lose weight",
                 "for a week in", "for two weeks in", "for 2 weeks in", "for a fortnight in",
                 "for ten days in", "for 10 days in", "for three weeks in", "for 3 weeks in",
                 "a week in", "a fortnight in", "abroad"),
          # The habit is the question, so the line has to name it or the urge to break one. Every
          # phrase in the key above says so except "spending money", which on its own is a
          # question about an amount: "how much spending money should i take to spain" is
          # travel's, not a wishlist rule.
          ask=("impulse", "tempted", "overspending", "stop spending", "keep buying",
               "buy things", "buying things", "buy too much", "buying too much",
               "shopping too much", "stop shopping", "keep ordering", "always buying",
               "buy less", "spend less", "cut back on", "stop buying", "stop ordering",
               "buying so many", "cut down on", "cut my spending", "too much", "less",
               "avoid", "help", "myself", "stop me",
               # the habit named as a thing that keeps happening, or as one that has got away
               # from them: "i keep spending money on shoes" and "spending money is getting out
               # of hand" were a chat shrug because neither shape was in this list. A bare
               # "spending money" stays out, because that one is an amount to take somewhere.
               "keep spending", "keeps spending", "spending is", "out of hand",
               "getting out of hand", "gone too far")),
    entry("takeaway-habit", (("stop", "cut", "much", "less", "keep", "how do i", "help",
                              "spend", "spending", "waste", "wasting", "save", "saving",
                              "buy", "buying", "ordered", "ordering"),
                             ("takeaway", "takeaways", "fast food", "eating out", "deliveroo",
                              "just eat", "uber eats", "food delivery", "restaurant", "lunch",
                              # a coffee is the money question only when the line says where it
                              # comes from: "how do i cut down on coffee" is about caffeine.
                              "takeaway coffee", "bought coffee", "shop coffee",
                              "buying coffee", "buy coffee", "coffee habit", "coffees a week",
                              "lunches", "packed lunch")),
          _habit_plan,
          # "how do i cut down on coffee" is a caffeine question, not a spending one: this answer is
          # only for a line that says it is about money, or about stopping.
          ask=("stop", "stopped", "stopping", "spend", "spending", "money", "keep buying",
               "keep spending", "keep ordering", "too much", "much", "a week", "a month",
               "cost", "costs", "save", "saving", "waste", "wasting", "out", "budget", "broke",
               "cut back", "cut down", "cutting"),
          # "split a restaurant bill" is the bill, not the habit; the money word it carries is a
          # noun, not an ask.
          avoid=("gambling", "bets", "betting", "porn", "alcohol", "drinking", "smoking",
                 "cigarettes", "vape", "clothes", "shoes", "split", "bill", "paid",
                 # "how do i get coffee out of a white shirt" is a stain, not a habit
                 "shirt", "stain", "stains", "carpet", "sofa", "fabric", "white",
                 # "i already cut the takeaways out" is the success, not the question: a follow-up
                 # saying it is done wants "well done, what next", not the plan again.
                 "already", "gave up", "given up", "no longer", "used to", "managed to")),
    # "i spend too much money" was the phone's screen-time answer: "i spend too much" was in
    # that row's ask list, and "spend" and "much" are key words on both. The phone row now asks
    # for "time"; this is the money question, and a line that names the thing - a takeaway, a
    # coffee - has its own row earlier in this file, so it wins the tie and gets the sharper plan.
    # The fault has a verb of its own and it names no amount: "how do i stop wasting money",
    # "i fritter money away", "i blow my wages every weekend", "my wages are gone by the
    # weekend". None of them says "spend" or "overspend", so the row that answers the question
    # could not see them: two were the search hedge ("Happy to help - tell me what you've got so
    # far"), three the listening noise ("I'm listening - say more if it helps"), "i blow my
    # wages every weekend" was echoed back as a statement of fact, and "my wages are gone by the
    # weekend" was "Thanks for telling me". The object of the verb is what makes a line this
    # row's, so every phrase below carries money in it: a bare "waste" is the bin's word or the
    # food-waste row's, and "i waste so much" alone stays where it was.
    entry("spend-too-much", (("spend too much", "spending too much", "spend so much",
                              "spending so much", "spends too much", "money goes",
                              # the same habit in one word, which is how people say it: "i
                              # overspend every month" was echoed back as a statement of fact
                              # ("You overspend every month. That's a habit now.") and got no
                              # help at all, and the past tense "i overspent again" the same.
                              "overspend", "overspends", "overspending", "overspent",
                              "over spend", "over spending",
                              # the verb of wasting, with its object in the phrase
                              "waste money", "wasting money", "wasted money", "wastes money",
                              "waste my money", "wasting my money", "waste the money",
                              "wasting the money", "waste so much money", "wasting so much money",
                              "waste money on", "wasting money on", "wasted money on",
                              "money to waste", "nothing to waste",
                              # the same complaint in the words people use for it
                              "fritter", "fritters", "frittering", "frittered",
                              "fritter away", "frittering away",
                              "blow my wages", "blow my money", "blowing my money",
                              "blowing my wages", "blows my money", "blown my money",
                              "blow my pay", "blow the lot", "blow it all",
                              "keep blowing", "keep wasting", "keeps wasting",
                              "money disappears", "money just disappears", "money vanished",
                              "money vanishes", "money goes on nothing", "spent on nothing",
                              # the same thing said as a state rather than a verb: "my wages are
                              # gone by the weekend", "there is no money left by payday", "i am
                              # skint by the 20th". Nothing is spent in these, so the row could
                              # not see them at all.
                              "wages are gone", "wages gone", "money is gone", "money gone",
                              # "i have no money left before payday" is the shortage card's, not
                              # this one's: a habit needs a verb of spending, and having nothing
                              # left is where the food bank and the two calls belong
                              "nothing left by", "money left by",
                              "money runs out", "money ran out", "runs out before payday",
                              "skint by", "skint before", "gone by the weekend",
                              "gone by payday", "spent by the"),
                             ("money", "month", "monthly", "each month", "payday", "week",
                              "clothes", "shopping", "shoes", "coffee", "coffees", "lunch",
                              "lunches", "stuff", "things", "everything", "always", "pay",
                              # the wage is money too, and it is how most people say it: "i blow
                              # my wages on nights out" named no money word at all, and "how do
                              # i stop blowing my wages" got the vaguest reply the bot has
                              "wage", "wages", "salary", "wage packet", "payslip", "weekend",
                              "fortnight", "nights out", "night out",
                              # the bare line and the sale rail: "i spend too much" and "i
                              # spend too much in the sales" both name the habit and nothing
                              # else, and without a word here they reached nothing at all and
                              # were answered with "Got it. Is there anything you'd like a hand
                              # with?" - the vaguest reply the bot has for the plainest line.
                              "much", "sales", "sale", "bargains", "bargain")),
          _over_spending,
          # "i spend too much on coffee" is the money question, and the caffeine row answers it
          # with a decaf tip: naming the coffee here is what makes the flask the answer, and the
          # bias settles the tie with that row (both score five, and cooking loads first).
          bias=1,
          ask=("spend", "spending", "spends", "spent", "too much", "so much", "money",
               # the one-word shapes need the word here too, or the row never gets the line
               "overspend", "overspends", "overspending", "overspent",
               # the wasting verbs are asks in their own right: "how do i stop wasting money"
               # names no amount and no month, so the row has to read the verb itself
               "waste", "wasting", "wasted", "fritter", "frittered", "blow my",
               "disappears", "vanishes", "on nothing",
               # the state rather than the verb: "my wages are gone by the weekend" names no
               # spending at all, so the ask has to carry the words it does say
               "wages", "wage", "gone", "left", "skint", "runs out", "ran out"),
          # a bill is an amount owed, not a habit: "i spend too much on my phone bill" wants the
          # provider's retention price, and a debt is the debt rows' question.
          avoid=("bill", "bills", "rent", "mortgage", "debt", "debts", "loan", "loans",
                 "overdraft", "insurance", "childcare", "fuel", "petrol", "time",
                 # a duration is a sum, not a habit: "how long till my money runs out" asks how
                 # many weeks the money buys, and the month's diary does not answer it
                 "how long", "how many weeks", "how many months", "until payday", "till payday",
                 # the thing the money goes on has its own card, and on those lines the card is
                 # the answer: a phone or a broadband line wants the retention price, a train the
                 # advance fare, a laptop the price to pay. Widening this row's key so the bare
                 # line matches made it take those five over - a diary of every purchase is the
                 # vaguer reply when the person has already named the thing.
                 "phone", "phones", "mobile", "mobiles", "broadband", "train", "trains",
                 "rail", "railway", "railcard", "laptop", "laptops", "electricity", "energy",
                 # the food rows answer their own lines better than the month's list does
                 "food", "foods", "groceries", "supermarket")),
    entry("pay-no-budget", (("no budget", "pay freeze", "no money in the pot",
                             "cant afford a rise", "can't afford a rise", "not this year"),
                            ("what if", "says", "said", "say back", "reply", "answer", "then what",
                             "he", "she", "they", "boss", "manager", "what can i do", "can i do",
                             "got told", "told me", "already asked", "asked and")),
          ("Ask what the range is and when the pay is next reviewed, and get that date in "
           "writing. If the pot really is empty, ask for what is not salary — a better title, a "
           "training budget, a day a week at home, or a named figure at a review in six months — "
           "and look around meanwhile, because a freeze at one firm is rarely a freeze across the "
           "market."),
          # A household with no money for a holiday or a course is not a pay conversation.
          avoid=("holiday", "training", "course", "redundancy", "redundant", "sacked", "quit",
                 "food", "week", "month")),
    entry("payday-loans", (("payday loan", "payday loans", "payday", "loan shark",
                            "high cost credit"),
                           ("avoid", "instead", "better", "bad", "get", "should",
                            "worth", "quick", "only", "option", "good", "idea")),
          ("Don't: the annual rate can run past 1,000%. Ask your bank about a small overdraft, a "
           "credit union for a low-cost loan, and a free debt advice service such as StepChange "
           "about grants, payment plans or a breathing space on what you already owe."),
          # a wage that has not arrived is work's unpaid-wages answer: the question is where the
          # money is, not whether to borrow, and "i didnt get paid on payday" was getting the
          # 1,000% warning.
          avoid=("didnt get paid", "did not get paid", "not been paid", "havent been paid",
                 "hasnt paid", "wages are late", "missed payday", "my employer")),
    # Two people who keep arguing about money are asking about the row, not about how to split
    # the bills: "we keep arguing about money" was the mood card ("Annoying. Is it the same
    # every time, or does it vary?") and "me and my mrs keep arguing about money" was the
    # search hedge. The bills entry answers the sum and this one answers the arguing, which is
    # why the row words are the second half of the key and a split question is stood aside.
    entry("money-arguments",
          (("money", "finances", "bills", "spending", "wages", "pay", "income", "debt",
            "debts", "credit card", "overdraft", "savings"),
           ("argue about", "argues about", "arguing about", "argued about", "argument about",
            "arguments about", "row about", "rows about", "rowing about", "rowed about",
            "fight about", "fights about", "fighting about", "keep arguing", "keeps arguing",
            "keep rowing", "keeps rowing", "keep fighting about", "bicker about",
            "bickering about", "always arguing", "constantly arguing", "same argument",
            "same row", "always fighting about", "fall out about", "fell out about",
            # the row named from the other end: "our arguments are always about money" says what
            # every row is about rather than what one of them was
            "always about", "are about", "is about", "arguments are", "rows are")),
          "Argue about two numbers rather than the principle: what has to go out each month for "
          "bills, and how much each of you can spend without asking the other. Write both down "
          "once, look at them on the same day each month for twenty minutes, and let the rest be "
          "each of yours to spend badly - most rows about money are about the pot nobody was "
          "given, not about the bills. Bring one thing to the conversation and leave the last ten "
          "years out of it.",
          # The split question is `money-and-partner`'s, and a family row about money is not a
          # couple's: "my parents argue about money" and "my mum and dad keep arguing about
          # money" wanted the argument answer, but "should my parents split the bills" does not.
          avoid=("how should we split", "should we split", "split the bills", "split our bills",
                 "split the rent", "joint account", "who pays", "pay half", "earn more",
                 "parents", "my mum", "my dad", "mother", "father", "in laws", "in law",
                 "flatmate", "flatmates", "housemate", "housemates", "landlord", "neighbour",
                 "boss", "colleague", "kids", "children", "child", "ex ", "my ex",
                 "hit", "hitting", "scared", "afraid", "frightened", "violent", "violence",
                 "threat", "threatened", "police",
                 # a row that happened is being told rather than asked about as a pattern:
                 # "we had a big row about money last night" is a conversation, and the short
                 # reply it gets now is better than an instruction to argue about two numbers
                 "last night", "yesterday", "this morning", "had a big row", "had a row",
                 "had a massive row", "had a fight", "had an argument")),
    entry("price-per-unit", (("price per unit", "per kilo", "per 100g", "unit price", "bulk",
                              "big pack", "bigger pack", "larger pack", "multipack",
                              "big box", "bulk pack", "stock up",
                              # the thing bought in bulk is the subject of the line, and the
                              # row has to be about it: "is it cheaper to buy washing powder in
                              # bulk" reached this entry and was then dropped for being about a
                              # subject the talk never touched, because the head word of the
                              # line ("powder") was in no key here. These are the packs people
                              # ask this about, not a list of shops.
                              "powder", "washing powder", "detergent", "tablets", "nappies",
                              "nappy", "toilet roll", "loo roll", "kitchen roll", "tins",
                              "cereal", "coffee", "tea bags", "pet food", "cat food",
                              "dog food", "cleaning products"),
                             ("worth", "compare", "cheaper", "better", "buy", "buying",
                              "bigger")),
          ("Compare the price per kilo or per 100g on the shelf label rather than the pack price: "
           "bigger packs are usually cheaper per unit, but not always, and only if you'll finish "
           "them. Food you throw away is the most expensive food in the kitchen.",
           # "tablets" is a dishwasher tablet and a pill as well as a computer, and with "buy"
           # in the ask the row took "should i buy a laptop or a tablet" whole. A choice between
           # two machines is technology's answer, and it is not sold by weight.
           ),
          avoid=("laptop", "laptops", "ipad", "iphone", "phone", "phones", "computer",
                 "computers", "chromebook", "macbook", "tablet computer", "smartphone",
                 "printer", "console", "tv", "television", "monitor")),
    entry("money-and-partner", (("partner", "husband", "wife", "boyfriend", "girlfriend",
                                 "other half", "my oh",
                                 # "how should we split money as a couple" names no partner,
                                 # so the couple itself has to be in the subject side.
                                 "couple", "couples", "share money", "split finances",
                                 "household money", "our money",
                                 # "how should we split the bills" and "should we get a joint
                                 # account" named no partner and reached nothing at all
                                 # "should we split the bills" and "should we get a joint
                                 # account" named no partner and reached nothing at all
                                 "split the bills", "split our bills", "split the rent",
                                 "split our rent", "shared bills", "bills between us",
                                 "joint account", "joint bank account",
                                 # "who pays what when one earns more" names no partner at all,
                                 # only the two incomes, and the table answers were taking it.
                                 "one earns more", "when one earns more", "earns more than me",
                                 "earns way more", "earn more than me", "one of us earns more",
                                 "earns more", "earn more"),
                                ("money", "finances", "bills", "split", "joint", "share",
                                 "account", "pay for", "who pays",
                                 # "he earns more, should i pay half the rent" names no shared
                                 # pot at all, only the rent and the two incomes
                                 # "pay" is not here on purpose: "who pays what when we split
                                 # the bill" is the table question, and this entry took it
                                 # "half" is not here either: it is the only money word a line
                                 # about the partner brings ("my other half is snoring",
                                 # "my oh keeps me awake") because it sits inside the name
                                 # itself, so it took every such line for a bills question.
                                 # The lines that are about bills say "split", "bills", "rent",
                                 # "earns" or "joint" as well, and keep the entry.
                                 "rent", "earn", "earns", "income", "fair")),
          ("Pay in by what each of you earns, not by halves: if one of you takes home 60% of the "
           "joint income, that person covers 60% of the bills. Keep a joint account for rent, "
           "bills and food, keep your own accounts for the rest, and look at it together once a "
           "month rather than arguing over individual receipts."),
          # "how should we split the bills" with no home and no table named is main's routing:
          # the income-share answer. The table-etiquette entry outranks it on the bare words
          # alone, so this one carries a nudge.
          bias=2,
          # "i lied to my wife about the money" names a wife and money and asks about neither:
          # what to do about a thing kept back is the repair, not how to split the bills. The
          # row keeps every line where the money is the subject and the person is not the one
          # who did something (bot/compose/repair.py).
          # Two rules stand this row down: a bill kept back is the repair, and a table's manners
          # question is the judgement row's. The second is the shared rule, not a phrase list:
          # "is it polite to split the bill", "is splitting the bill rude" and "is it ok to split
          # the bill" all reached the joint-account advice because no list held their wording.
          guard=lambda reading: not owns_the_deed(reading)
                     and not _a_manners_question_not_a_home_split(reading),
          # "split the bill" cannot be held out here: every "split the bills" line contains it
          # word for word, and the entry then refused the couple's own question. A bill at a
          # table is kept out by the food words instead, and a group of friends by "with friends".
          avoid=(
                 # splitting the housework is not splitting the money: "how do i split chores
                 # fairly with my partner" was answered "pay in by what each of you earns, not by
                 # halves", which is about money and not about the work
                 "chores", "housework", "washing up", "hoovering", "dishes", "tidying",
                 "tidy up", "who does what", "restaurant", "dinner", "dine", "taxi", "takeaway", "with friends", "with mates",
                 # "share" is in this row's subject side, so "should i turn on location sharing
                 # with my boyfriend" was answered "pay in by what each of you earns, not by
                 # halves". Sharing where you are is not a share of the money: the words below
                 # are the only ones a location line brings, and the bills rows keep theirs.
                 "location", "locations", "live location", "where i am", "where im",
                 "where i'm", "tracking", "track me", "track my phone",
                 # a share of the work is not a share of the money: "how do i get my partner to
                 # do his share" was answered "pay in by what each of you earns, not by halves",
                 # which is the opposite kind of share. The phrases keep a work word with them,
                 # so "how do we split the bills fairly" still keeps this row.
                 "do his share", "do her share", "do their share",
                 "his share of the work", "her share of the work", "share of the work",
                 "help more around", "help out more", "pull his weight", "pulls his weight",
                 "pull her weight", "pull their weight", "around the house", "get my husband to",
                 "get my partner to", "get my wife to",
                 "colleagues", "share the housework",
                 # A table's manners question is the split-bill entry's. The guard stands this
                 # row down for the shape of that question ("is it polite to split the bill",
                 # "is splitting the bill rude"), and these phrases carry the same stand-down
                 # into the ranking, where stood-down rows do not compete at all: without them
                 # "is it rude to split the rent" came back with the joint-account advice
                 # because this row outranked split-house, which is the row that answers it.
                 # A bare "rude" could not be listed - it would stand this entry down on "is it
                 # rude to ask my partner for money", which is exactly what this row answers.
                 "rude to split", "awkward", "etiquette", "first date", "on a date",
                 # a line that names a shared flat or a house share is the household split, not
                 # two people pooling their income: "how do we split the bills in a flat share"
                 # is split-house, and this entry standing down lets it answer.
                 "flat share", "house share", "shared flat", "shared house", "sharing a flat",
                 "sharing a house", "student house",
                 # "how do i share my location with my husband" is a phone setting, not a pot
                 # of money: the partner word alone was enough to pull it here.
                 "share my location", "share location", "share photos", "share a photo",
                 "share pictures", "share my screen", "share a folder", "share a file",
                 "share the wifi", "wifi password", "streaming account", "netflix",
                 # the asking is not the policy: "how do i bring up money with my partner" and
                 # "how do i talk to my partner about money" are how to say it, which
                 # wording.how-to-tell-them answers, and this row answered them with the split
                 "how do i bring", "how do i raise", "how do i tell", "how do i say",
                 "how do i talk", "how do i approach", "bring it up", "bring up the",
                 "raise it with", "talk to my",
                 # An equal share, or a split by room, is not an income question: "split the rent
                 # evenly" and "how do i split the rent three ways" belong to the table answer
                 # ("even shares are fine and simpler"), not to 60/40 by take-home pay.
                 "evenly", "equally", "three ways", "by room", "same size room",
                 "same sized room", "bigger room",
                 # A couple who are ending it are not agreeing how to pay in: "my husband and i
                 # are splitting up" got "pay in by what each of you earns, not by halves". The
                 # separation words are the whole difference, and the row below answers them.
                 "splitting up", "split up", "separating", "separation", "separated",
                 "divorce", "divorcing", "getting a divorce", "broke up", "broken up",
                 "breaking up", "walked out", "left me", "left him", "left her",
                 "he left", "she left", "we are over", "its over between", "it is over between",
                 "no longer together", "not together anymore", "not together any more",
                 # A place rented for a week by a group is a shared holiday, not a couple's
                 # joint account: "how do i split a holiday cottage between 3 couples" was told
                 # to pay in by what each of them earns. The holiday words are the subject, so
                 # they stand this row down and share-a-cost answers.
                 "cottage", "cottages", "airbnb", "villa", "caravan", "holiday cottage",
                 "holiday house", "holiday home", "holiday let", "holiday place",
                 "house we rented", "place we rented", "week away", "3 couples",
                 "three couples", "two couples", "four couples",
                 # The same place a *bill* for one occasion keeps: this row is the household's
                 # ongoing money (rent, bills, food, a joint account), and a bill for a meal, a
                 # night out or a holiday is split by what each person had, not by what each of
                 # them earns. "how do we split the bill for the holiday" was told to "pay in by
                 # what each of you earns, not by halves", which is the rent answer, and the
                 # drinks card is the one that answers it.
                 "the bill for", "bill for the", "bill for a", "the bill on", "bill on the",
                 "holiday", "holidays", "on holiday", "went away", "weekend away",
                 "night out", "for the weekend", "for the trip", "towards the trip",
                 "the meals", "eating out", "pub", "drinks", "round of drinks")),
    # A relationship ending is the one money moment the couple's bills answer must not take.
    # "my husband and i are splitting up" was told to "pay in by what each of you earns, not by
    # halves", and "my wife and i are splitting up what about the house" the same, because the
    # partner word is what that row needs and the split is the opposite of the question.
    entry("separating-money",
          (("splitting up", "split up", "we are separating", "separating", "separation",
            "divorce", "divorcing", "getting a divorce", "filing for divorce", "broke up",
            "broken up", "breaking up", "walked out", "left me", "he left", "she left",
            "left my husband", "left my wife", "left my partner", "we are over",
            "it is over between", "no longer together", "not together any more",
            "not together anymore", "marriage is over", "marriage has ended", "ended it"),
           # the person, so a line about a friend's divorce or a work split does not reach it,
           # and the money, so "we are splitting up the last of the wine" does not either
           ("husband", "wife", "partner", "marriage", "married", "money", "account",
            "accounts", "joint account", "house", "mortgage", "home", "bills", "debts",
            "debt", "finances", "pension", "pensions", "savings", "what about", "who pays",
            "who keeps", "split", "asset", "assets", "afford", "move out", "solicitor")),
          "Get the money apart quietly and early: open a current account in your own name and "
          "have your pay and any benefits go there, then list every joint account, loan, credit "
          "card and direct debit so nothing bounces in your name. Tell the bank you have "
          "separated, keep paying the mortgage or rent until a solicitor says otherwise, and book "
          "the free first session most family solicitors offer before you agree anything.",
          bias=2,
          # two friends, a flat share or a table splitting a bill are not a marriage ending
          # "pension" alone is a retirement question, and a house move is somebody else's row
          avoid=("friend", "friends", "mates", "colleagues", "flatmate", "flatmates",
                 "housemate", "housemates", "landlord", "tenancy", "deposit", "rent arrears",
                 "splitting the bill", "split the bill", "restaurant", "dinner", "taxi",
                 "splitting the cost", "split the cost", "go halves", "state pension",
                 "pension credit", "workplace pension", "how much is the pension",
                 "moving house", "should i move", "divorce rates", "how common is divorce",
                 "is divorce legal", "annulment", "wedding", "getting married")),
    # "should i chip in for a present" was the potato-chip recipe and "how much should i chip in"
    # the boiled-potato times: the word chip is food, a golf shot and a windscreen ding before it
    # is money, and the money sense had no owner at all.
    entry("chip-in",
          (("chip in", "chipping in", "chipped in", "chips in", "chip in for", "chip in towards",
            "chip in toward", "chuck in", "chucking in", "chucked in", "chucks in",
            "whip round", "whip-round", "whipp round", "collection for", "collect for",
            "pool money", "pool the money", "put money towards", "put in for", "go halves",
            "go half", "split the cost", "split the present", "contribute to", "contribution to",
            "everyone chips in", "everyone chucks in", "put a tenner in", "put a fiver in"),
           ("should i", "should we", "how much", "how should", "who", "what", "is it", "do i",
            "do we", "expect", "expected", "ask", "asking", "fair", "awkward", "polite",
            "rude", "present", "presents", "gift", "gifts", "leaving", "do", "leaving do",
            "wedding", "birthday", "colleague", "colleagues", "office", "work", "team",
            "party", "everyone", "money", "cash", "amount", "much", "track", "organise",
            "organising", "collect", "collecting", "sign", "card", "towards", "toward")),
          ("Chipping in is a shared cost split between the people it is for, so the fair default "
           "is the same amount from everybody: whoever is organising works out the total and how "
           "many people are covering it, and the rest pay that share. In practice that is a fiver "
           "or a tenner for an office collection, ten to twenty pounds for a wedding, a big "
           "birthday or a leaving do from people who know them well, and more than that is a "
           "personal choice, not an expectation. If you are the one collecting, ask for a "
           "contribution rather than name a figure for people, keep it private - a link or an "
           "envelope, no list of who gave what - and if the pot comes up short, buy smaller "
           "rather than chase the difference. It is always fine to say no, or to give less, "
           "without explaining why."),
          # every other sense of chip is in this list: the potato, the golf shot, the windscreen,
          # the paint and the plate
          # a chip word in this list would fence out the row's own key, because "chips" reaches
          # "chip": the potato is kept out by the key instead, which needs "chip in" or a
          # contribution phrase, and by the food words that do not begin with chip.
          avoid=("potato", "potatoes", "fries", "crisps", "crisp", "salt and vinegar",
                 "air fryer", "deep fry", "deep fryer", "recipe", "cook", "cooking", "bake",
                 "roast", "frozen", "salty", "oven", "peel", "peeler", "maris piper",
                 "golf", "golf ball", "golf club", "club", "shot", "putt", "putting", "wedge",
                 "green", "bunker", "tee", "swing", "handicap", "driver", "iron", "fairway",
                 "windscreen", "windshield", "paint", "paintwork", "car", "van", "windscreen wipers",
                 "plate", "mug", "cup", "bowl", "glaze", "nail", "tooth", "tile", "worktop",
                 "sink", "table", "wood", "floor",
                 # "should i chip in for a colleague's leaving present" was tried as a fence
                 # here ("should i chip in", "is it rude", the question shape) and taken back
                 # out: "how much should i chip in" is the same words and is this row's own
                 # question, and `tests/test_a_chip_in_is_money.py` went red on it. The etiquette
                 # note stays open in the PR rather than bought with the amount.
                 # The potato is kept out of *this* row by its key, not by a word: a chip recipe
                 # row that reaches a contribution line is fenced in cooking.py instead.
                 # A cost shared away from an office is not a collection: this row gained
                 # "split the cost" and "go halves" while share-a-cost was being written, and
                 # it then answered "how should we split the cost of a hotel room" and
                 # "...of petrol" with the whip-round card. The subject is the difference, so
                 # every ride, stay and tank named here stands the row down.
                 "taxi", "taxi fare", "cab", "uber", "fare", "fares", "minicab",
                 "petrol", "petrol money", "diesel", "fuel", "fuel money", "tank of",
                 "fill up", "filled up", "miles", "mileage", "parking", "toll", "tolls",
                 "hotel", "hotel room", "a room", "the room", "rooms", "airbnb", "villa",
                 "caravan", "cottage", "cottages", "holiday cottage", "holiday house",
                 "holiday home", "house we rented", "place we rented", "week away",
                 "flight", "flights", "holiday", "holidays", "trip", "weekend away",
                 "city break", "abroad")),
    entry("split-bill", (("split the bill", "split a bill", "split it", "share the bill",
                          "who pays", "who owes", "splitting the bill", "restaurant bill",
                          # "how do i split a dinner bill" and "splitting the bill with mates"
                          # name the thing in the middle, so the verb on its own has to count
                          "split the", "split a", "splitting the", "sharing the",
                          # "how do i split" is one phrase worth 3, which is under the minimum
                          # on its own, so the line fell through to a search hedge
                          "how do i split", "how to split",
                          # "who should pay for dinner" is the same question with the verb the
                          # other way round, and none of the phrases above has "should" in it,
                          # so once the funding ladder stopped taking it the line fell through
                          # to a search hedge. A table, a round or a mate's fare is this row.
                          "who should pay", "who should be paying", "who pays for",
                          "pay for dinner", "pay for the meal", "pay for drinks",
                          "pay for the drinks", "pay for lunch", "pay for my mate",
                          "pay for my mates", "pay for my friend", "pay for my friends",
                          "pay for my round", "pay for their", "whose round",
                          "whose turn to pay", "pays for dinner"),
                         # a bare "ways" used to sit in the first part, and its forms reach
                         # "way", so every "what is the best way to ..." line that also said
                         # drinks, dinner or a friend came to the dinner bill: "what is the best
                         # way to keep drinks cold in the car" got "Split by what people actually
                         # had". How many ways it is still counts, from the second part below.
                         # "fair" is not here: "we split the rent 60 40 because i earn more, is
                         # that fair" is the couple question, and this entry answered it with
                         # the dinner split. A table is a food word, a friend or a group.
                         ("friend", "friends", "mates", "colleagues", "dinner", "drinks",
                          "restaurant", "group", "evenly", "awkward", "who pays", "who owes",
                          "pay", "pays",
                          # "split the bill 3 ways" and "split the bill between 4 of us" name no
                          # table and no friend, so the couple's joint-account answer took them:
                          # it matches the same "split the bill" words. The number of ways and
                          # the people are what tells a table apart from a household.
                          "ways", "way", "of us", "between us", "each pay", "go halves",
                          # a bill away from home is still a table: "how do we split the bill on
                          # holiday" named no dinner and no friends, so the couple's 60/40 answer
                          # took it. The holiday is the setting, not the subject.
                          # "holiday" and "trip" are NOT here: a word in this row's own key
                          # cannot also fence it, and "split the cost of a holiday" is not a
                          # table at all - it is share-a-cost's group-trip answer. "on holiday"
                          # is the phrase that means a dinner away from home, and "split the
                          # bill" is in the key already, so the setting still scores.
                          "on holiday", "on our holiday", "on trips", "on a trip",
                          # A bill *for* the holiday is the same table seen from the week
                          # before: "how do we split the bill for the holiday" is what each of
                          # them had while they were away, and with "on holiday" as the only
                          # holiday wording the line reached the couple's income split instead.
                          # The cost of the holiday itself - the flights, the house, the car - is
                          # not a bill and is fenced off below, so share-a-cost keeps it.
                          "for the holiday", "for our holiday", "the holiday bill",
                          "for the trip", "for our trip")),
          _split_bill,
          # A tip is worked out, not split: the tipping answer knows who gets what. Sharing the
          # housework is family's answer (chores-fair), not a bill.
          avoid=("tip", "tips", "tipping", "service charge", "gratuity", "housework", "chores",
                 "cleaning", "laundry", "washing up", "childcare", "workload", "fairly",
                 # a shared flat's bills are lifeadmin's split-bills, not one dinner
                 "housemate", "housemates", "flatmate", "flatmates", "roommate", "roommates",
                 "household", "flat share", "house share", "shared flat", "shared house",
                 "council tax", "electricity", "broadband",
                 # a cost shared away from a table - a taxi, a rented cottage, a whip round - is
                 # share-a-cost's, and "holiday" in the second part used to pull the cottage here
                 "cottage", "cottages", "airbnb", "villa", "caravan", "holiday house",
                 "holiday home", "holiday cottage", "rented a house", "hotel room", "hotel",
                 "whip round", "whip-round", "collection", "uber",
                 # a drink that is wanted cold is the cool-bag question, not a table sharing a
                 # bill: "what is the best way to keep drinks cold in the car" was the dinner
                 # split on "ways". The drink in a bill line is what was ordered, never how
                 # cold it is, so only the cold-shaped phrases stand this row down.
                 # a holiday's big costs are booked once and put on one card, not shared as a
                 # bill: "how do we split the cost of a holiday" and "... of flights" are
                 # share-a-cost's group-trip answer, and the holiday setting above is only here
                 # for a bill that was run up while they were there
                 "cost of a holiday", "cost of the holiday", "cost of a trip", "cost of our trip",
                 "cost of the flights", "the flights", "the house we", "the car hire",
                 "cold drink", "cold drinks", "drinks cold", "drink cold", "keep drinks",
                 "keep the drinks", "keep my drink", "keep your drink", "cool bag", "cool box",
                 # "who pays" is also how a leak, a crash, an injury and an insurance claim are
                 # asked: those are not a table sharing a bill, and they rank this entry as high
                 "leak", "leaking", "leaked", "burst", "garden", "whiplash", "crash",
                 "accident", "injury", "injured", "insurance", "claim", "damage", "damaged",
                 # "who pays to send it back" is the returns postage question, not a shared bill
                 "send it back", "sent it back", "post it back", "postage", "return postage",
                 "returns", "prepaid label", "restocking",
                 # "who pays to send a faulty item back" names neither: the object is a faulty
                 # thing and the verb is sending, and this row's bias of 3 took it off the
                 # returns answer
                 "faulty", "send back", "sending back", "sent back", "item back",
                 "back to the shop", "broken",
                 "repair", "landlord", "deposit",
                 # "cheapest way to pay my energy bill" is a utility bill, not a table: the
                 # word "bill" and a way of paying were enough to get the dinner split.
                 "energy", "energy bill", "gas bill", "electricity bill", "supplier",
                 "direct debit", "standing charge", "tariff", "meter",
                 # paying off a debt is not a bill divided between friends: the debt order and
                 # the overpayment answer own those lines, and this one kept taking them
                 "debt", "debts", "credit card", "overdraft", "payday loan", "pay off",
                 "paying off", "paid off",
                 # a funeral bill is asked the same way as a table bill ("who pays for the
                 # funeral") and is nobody's dinner: whose money it comes out of is the
                 # first-days question, and this row's bias of 3 took it off that answer
                 "funeral", "funerals", "cremation", "burial", "buried", "undertaker",
                 "funeral director", "bereavement", "bereaved", "wake", "the deceased"),
          # a bill at a table is this answer even when "who pays" makes the couple's entry
          # rank just as high: two people living together who split the bills are not at dinner
          bias=3),
    # A shared cost that is not a table: a taxi, a tank of petrol, a rented room, a whip round.
    # Every neighbouring row claimed these. "how do i split a taxi fare" was answered with the
    # employer's expense policy, "how do i split petrol money" with the payslip budget, and a
    # hotel room and a holiday cottage with who-had-the-wine. The subject in the line picks the
    # opening, and the guard keeps the row off a line that only mentions a taxi.
    entry("share-a-cost",
          (("taxi", "taxi fare", "cab", "uber", "fare", "fares", "petrol", "petrol money",
            "fuel", "diesel", "parking", "toll", "tolls",
            "hotel room", "hotel", "a room", "the room", "rooms", "cottage", "airbnb",
            "apartment", "villa", "caravan", "holiday house", "holiday home",
            "present", "presents", "gift", "gifts", "collection", "whip round", "kitty",
            "leaving present", "wedding present", "secret santa",
            "holiday", "weekend away", "trip", "night out",
            # the big things a group holiday is booked on are the flight and the car, and
            # "how do we split the cost of the flights" named neither a stay nor a holiday, so
            # with no key of its own it fell past this row to a search hedge
            "flight", "flights", "car hire", "hire car", "train fare", "train fares"),
           ("split", "splitting", "share", "sharing", "halves", "go halves", "between us",
            "each pay", "per head", "per person", "who owes", "who pays", "chip in",
            "contribute", "contribution", "fair", "fairly", "fairest", "how much should",
            "evenly", "equally")),
          _share_a_cost,
          ask=("how", "what", "should", "split", "splitting", "share", "sharing", "halves",
               "fair", "fairly", "fairest", "who", "much"),
          guard=_shares_a_cost,
          bias=1,
          # A dinner, a bill at a table, a shared flat's bills and a present's price all have
          # their own answers, and this row is not one of them.
          avoid=("bill", "bills", "restaurant", "dinner", "lunch", "drinks", "meal", "meal out",
                 "waiter", "tip", "tips", "tipping", "service charge", "takeaway", "pub",
                 # a tenancy's rent is split-house's, but "rented a cottage" is a stay shared
                 # between friends: the bare word stood this row down for every line that named
                 # what was rented, so the rent words here are the tenancy shapes only.
                 "the rent", "rent is", "rent and", "our rent", "my rent", "monthly rent",
                 "pay rent", "paying rent", "rent with", "split rent", "rent between",
                 "rent money", "rent each",
                 "mortgage", "council tax", "electricity", "gas", "broadband", "water bill",
                 "flatmate", "flatmates", "housemate", "housemates", "roommate", "roommates",
                 "house share", "flat share", "shared flat", "shared house", "student house",
                 "housework", "chores", "cleaning", "laundry", "childcare",
                 "how much does it cost", "how much is a taxi", "taxi fare to",
                 "taxi cost", "cheap taxi", "minicab number", "book a taxi", "airport taxi",
                 "how much should i spend", "how much to spend", "what should i get",
                 "what to buy", "ideas", "expenses", "claim back", "receipt", "reimburs",
                 "mileage", "claim", "tax return", "invoice",
                 "share my location", "share a file", "share photos", "share the wifi",
                 "share a photo", "share a post", "share a link", "screen share")),

    entry("card-declined", (("declined", "card declined", "card got declined", "payment declined",
                              "card rejected", "card not working", "card stopped working"),
                             ("card", "payment", "till", "shop", "checkout", "why", "what", "should",
                              "got", "keeps", "my")),
          ("Ring the number on the back of the card: a decline is usually a security check, a daily "
           "limit or a block the bank can lift in one call. A contactless tap over £100 needs the "
           "PIN, and a hold from a hotel or a petrol pump can freeze money for a few days."),
          avoid=("mortgage", "loan", "application", "credit card application")),

    # A card that will not go through on a bus is not the card-declined answer: the person is at
    # a barrier with a driver waiting, so the first thing is the ride and only then the bank.
    # "take my card" was read as a travel-money line and the foreign card, the bank block and the
    # security check answered the rest, none of which gets anyone home.
    entry("card-on-transport", (("bus", "bus driver", "the driver", "coach", "train", "tube",
                                 "underground", "tram", "metro", "ferry", "ticket machine",
                                 "barrier", "turnstile", "platform", "on the bus"),
                                ("card", "contactless", "tap", "tapped", "declined", "decline",
                                 "wouldnt take", "wouldn't take", "wont take", "won't take",
                                 "didnt work", "didn't work", "not working", "refused",
                                 "says declined", "said declined", "no cash", "would not take")),
          ("Get the ride first: a bus or tram driver will wave you on, station staff let you "
           "through a barrier, and a ticket machine or the operator's app takes another card or "
           "the phone. In a taxi, the meter and a receipt are what a complaint rests on. Then "
           "ring the bank: a daily limit, an offline reader or a block is the usual cause, and a "
           "fare charged twice is the operator's to refund."),
          # "can i use my card on the bus" is a how-do-i-pay question, not a card that has
          # failed, and this answer tells somebody who has not hit a problem yet to get the ride
          # first. The key's second half already says card, so the failure itself is the ask:
          # the line is this row's only when something was refused, declined or did not work.
          ask=("declined", "decline", "wouldnt", "wouldn't", "wont", "won't", "didnt", "didn't",
               "not working", "stopped working", "refused", "would not", "did not", "no cash",
               "failed", "rejected", "says no", "said no"),
          # The card that is lost, the card used abroad, the fare itself and the timetable are
          # all somebody else's question.
          avoid=("abroad", "holiday", "currency", "travel money", "timetable", "next bus",
                 "bus pass", "lost my card", "lost card", "stolen", "train times", "fare",
                 "how much is", "season ticket", "parking", "fine", "top up", "oyster",
                 # a taxi that will not take a card is its own answer (the meter and the council
                 # that licenses it), and it is a better one than this
                 "taxi", "cab", "uber", "minicab", "meter",
                 # A machine that keeps the card is the one transport case where the bank is the
                 # first thing, because anyone holding the card has the pin-free tap on it: the
                 # card that answers "block it and get a new one" is the better answer there.
                 "swallowed", "swallowed my card", "kept my card", "ate my card",
                 "machine kept", "machine swallowed", "still in the machine"),
          bias=2),

    # "how much should i spend on a present" was a shrug: the gift entries all answer what to
    # buy, and none of them answers what it should cost. The money is the question here.
    entry("gift-budget", (("present", "presents", "gift", "gifts", "secret santa", "birthday",
                           "christmas present", "wedding present", "friend", "friends",
                           "colleague", "colleagues", "workmate", "brother", "sister", "sibling",
                           "in laws"),
                          ("how much", "spend", "spending", "spent", "budget", "enough",
                           "too much", "reasonable", "normal", "usual", "afford", "cost", "price",
                           "expensive", "cheap")),
          _a_gift_budget,
          bias=1,
          # what to buy is a different question, and it belongs to the gift entries; a wedding
          # gift has its own usual figure, and Christmas has its own budget entry.
          avoid=("wedding", "weddings", "christmas", "xmas", "what should i get",
                 "what should i buy", "what can i get", "what can i buy", "ideas", "idea",
                 "christmas budget", "afford christmas", "santa list",
                 # the birthday itself has its own answers: the cake, the party, the decorations,
                 # the card and the food are all a "how much for X" question with a much bigger
                 # number in it than a present.
                 "cake", "cakes", "party", "parties", "decorations", "balloons", "card", "cards",
                 "food", "drink", "drinks", "venue", "table", "outfit",
                 # A gift and what tax is due on it is not what a present should cost: "how much
                 # money can i gift without paying tax" was answered with the secret santa figure.
                 "tax", "taxed", "taxable", "tax free", "tax-free", "declare", "hmrc",
                 "inheritance tax", "inheritance", "7 year", "seven year", "seven years")),
    # Giving money away is the commonest money worry there is - a deposit from a parent, a lump
    # sum to a child, a gift before a death - and there was no card for it at all: the word "tax"
    # reached the self-assessment row ("register as self-employed"), the receiver's side reached
    # the row about a parent who keeps buying clothes, and "how much money can i gift without
    # paying tax" reached the secret santa budget. No UK gift tax is the answer, and the one tax
    # a gift can touch is the giver's estate.
    entry("tax-on-a-gift",
          (("gift", "gifts", "gifted", "gifting", "cash gift", "money gift", "present",
            "presents", "birthday present", "christmas present", "money as a present",
            "voucher", "vouchers", "gift card", "gift cards", "hamper", "hampers",
            "gave me", "gave us", "gives me", "given me", "gifted me", "left me", "handed me",
            "give away", "giving away", "gift away", "gifting away", "hand over", "handed over",
            "transfer to my", "transferred to my",
            "gift of money", "give money", "giving money", "give a lump sum", "give a large sum",
            "give my son", "give my daughter", "give my children", "give my kids",
            "give my grandchildren", "give my mum", "give my dad", "give my parents",
            "give my sister", "give my brother", "give my partner",
            "money from my parents", "money from my mum", "money from my dad",
            "money from my nan", "money from my gran", "parents give me", "parents gave me",
            "parents want to give", "wants to give me", "want to give me", "mum gave me",
            "dad gave me", "lump sum from my", "deposit from my parents",
            "deposit from my mum", "deposit from my dad", "house deposit from"),
           ("tax", "taxed", "taxable", "tax free", "tax-free", "tax bill", "gift tax",
            "pay tax", "paying tax", "owe tax", "declare", "declaring", "declare it",
            "hmrc", "report it", "inheritance tax", "iht", "7 year", "seven year",
            "seven years", "195,000", "325,000", "3,000", "3000",
            # A "without" clause is a frame the knowledge layer empties before the keys are
            # read, and only a key that names the frame keeps the whole line: "how much money
            # can i gift without paying tax" lost the words "paying tax" and fell to the
            # secret santa figure.
            "without paying tax", "without tax", "without paying any tax", "without declaring",
            "without paying", "in the will", "in my will", "leave it in the will",
            "leave it in my will", "while i am alive", "while im alive",
            "each year", "per year", "every year", "annual", "annually", "a year")),
          _the_tax_on_a_gift,
          bias=2,
          # the giver's own income is a different question, and so is what a present should
          # cost, what to buy, and a secret santa at work
          avoid=("salary", "wages", "wage", "earn", "earned", "earning", "earnings",
                 "income", "bonus", "overtime", "pension", "pensions",
                 "self employed", "self-employed", "self assessment", "side hustle", "rent",
                 "renting out", "dividend", "dividends", "shares", "sold", "selling",
                 "what should i get", "what should i buy", "what can i get", "ideas", "idea",
                 "how much should i spend", "secret santa", "wife", "husband",
                 "what to buy", "asks for money", "keeps asking", "pocket money")),
    entry("cash-vs-card", (("cash", "envelope", "envelope system", "spending money",
                            "instead of card", "instead of a card", "cash instead",
                            "spend cash", "using cash", "cash out"),
                           ("budget", "help", "better", "control", "way", "spend", "work",
                            "stick", "stick to")),
          ("Cash or a separate spending card caps the damage: fill an envelope for the week, and "
           "when it's empty it's empty. It works because a card makes spending painless, and seeing "
           "the money run out is exactly the feedback a budget needs."),
          bias=1,
          # A card that will not work in a machine is a card fault, not a spending plan.
          # "How much spending money for a week in rome" asks for an amount, not for a way to
          # carry it: travel's day rate is the answer, and this entry was taking every line with
          # "spending money" in it because the phrase is worth three points. Take cash to a place
          # and the day rate answers it too; which of the two to use is still this entry.
          avoid=("cash machine", "atm", "not working", "isnt working", "wont work", "won't work",
                 "declined", "swallowed", "card reader", "chip and pin", "contactless",
                 "spending money", "spending cash")),
    # --- bills -------------------------------------------------------------------
    # "What is the difference between the energy price cap and a fixed tariff" names both things,
    # so "price cap" and "tariff" find it; a bare "difference between" also took "what's the
    # difference between wifi and the internet", which is technology's.
    # "is a fixed rate better than variable" and "fixed rate or variable" name the rate twice over
    # in the same words, and one word may not satisfy two halves of a key: the second half scored
    # nothing, the row fell under MIN_SCORE and a garage's labour rate answered it. The second half
    # is the words a choice between rates is made of.
    entry("energy-tariff", (("tariff", "fixed rate", "variable rate", "price cap", "fix my rate",
                             "fixed tariff", "variable tariff", "on a fixed rate",
                             # The choice said with the bare adjectives: "which is cheaper fixed
                             # or variable" names no "rate" at all, so no row scored it and a
                             # shrug answered it. The pair is the whole question, so it is the
                             # phrase that is keyed rather than the two words apart.
                             "fixed or variable", "fixed vs variable", "variable or fixed",
                             "fix or variable"),
                            ("energy", "fix", "worth", "better", "choose", "cheap", "cheaper",
                             "variable", "fixed", "what", "mean", "means", "explain",
                             "get", "compare", "comparison", "switch", "switching", "supplier",
                             "bill", "bills", "electricity", "gas", "which", "difference",
                             "worth it", "should i")),
          _energy_tariff,
           # A fixed rate on a mortgage, a loan or a savings bond is that product's question: with
           # the words of a choice now in the key, this row took "should i get a fixed rate
           # mortgage" away from fix-or-track.
           avoid=("mortgage", "mortgages", "remortgage", "remortgaging", "home loan", "tracker",
                  "savings", "isa", "bond", "bonds", "loan", "loans", "credit card",
                  # a drill with a fixed or variable speed is the drill's question
                  "drill", "drills", "speed", "speeds", "rpm"),
           # "do I need a fixed tariff" and "should we switch to a fixed tariff" name a fix and an
           # ask about having one, and the switch row keys the same two words; the row that knows
           # the cap is the one that can say whether a fix is worth it.
           bias=1),
    # "how much is gas and electricity a month" was answered with what electricity *is* - the
    # physics entry - and "my gas and electricity is 200 a month" with nothing. Both ask what
    # people pay, which is a number, so it gets the numbers to compare against.
    entry("energy-cost",
          (("gas and electricity", "gas and electric", "electric and gas", "electricity and gas",
            "energy bill", "energy bills", "energy costs", "energy prices", "dual fuel",
            "electricity bill", "gas bill", "for energy", "on energy"),
           ("how much", "a month", "per month", "a year", "per year", "a week", "normal",
            "average", "typical", "is that", "should i be paying", "am i paying", "cost",
            "costs", "expensive", "200", "300", "too much")),
          ("A typical household pays about £140-£150 a month for gas and electricity at the price "
           "cap, so £200 a month usually means a bigger or older house, electric heating, or a "
           "tariff nobody has compared in a while. The figure that decides it is the kWh, not the "
           "monthly estimate: the annual use on your bill against the Ofgem typical figures of "
           "2,700 kWh of electricity and 11,500 kWh of gas tells you whether you are using a lot "
           "or paying a lot."),
          # A bill you cannot pay, a wrong bill, a tariff choice and a way of paying all have
          # their own answers, and so does what electricity is.
          avoid=("cant pay", "can't pay", "cannot pay", "afford", "behind on", "arrears",
                 "debt", "payment plan", "overcharged", "wrong bill", "switched", "switch",
                 "tariff", "fixed deal", "price cap", "standing charge", "direct debit",
                 "prepayment", "what is", "how does", "why does", "what does", "mean")),
    # "how much is a kwh of electricity" was answered with what electricity is, which is the
    # physics of it and not the price: the person has a bill in front of them.
    entry("energy-unit-rate",
          (("kwh", "kw h", "unit rate", "per unit", "price per unit", "cost per unit",
            "a unit of electricity", "a unit of gas", "energy unit"),
           ("what", "how much", "cost", "costs", "price", "is it", "mean", "charge", "average",
            "paying")),
          ("A unit is a kilowatt hour - one kW running for an hour - and under the price cap it is "
           "about 25p for electricity and 6p for gas, on top of a standing charge of roughly 40-60p "
           "a day for each fuel. So a kettle (about 0.1 kWh) costs pennies and an hour of the oven "
           "(about 2 kWh) costs about 50p; your own bill has the exact unit rate and standing "
           "charge, and those two times your annual use give the yearly figure."),
          avoid=("cant pay", "can't pay", "afford", "behind on", "arrears", "debt", "switch",
                 "switched", "tariff", "fixed deal", "prepayment", "meter reading", "smart meter",
                 "what is electricity", "how does electricity"),
          bias=1),
    # "what is the warm home discount" got the debt answer, which is right next door and not the
    # same question: it is a scheme with a fixed amount and an automatic route.
    entry("warm-home-discount",
          # The Winter Fuel Payment and the Cold Weather Payment are different sums with
          # different rules, so they are not in this key: "can i get the winter fuel payment"
          # was answered with the discount, which is a confident wrong answer. They have their
          # own row below. Fuel poverty is a definition, not a scheme, so it hedges.
          (("warm home discount", "warm home"),
           ("what", "how much", "apply", "applying", "eligible", "qualify", "get it", "claim",
            "check", "do i get", "can i get", "worth")),
          ("The Warm Home Discount takes £150 off the electricity bill once, between October and "
           "March, for people on a low income, and most eligible households get it automatically "
           "from their supplier because the government matches the records - check the bill for "
           "the credit and ring the supplier if it is missing. Pension Credit or a low income with "
           "high energy costs is what qualifies you, and the Winter Fuel Payment and Cold Weather "
           "Payment are separate sums paid through the same benefits."),
          # A scheme question said plainly ("what is the warm home discount") ties with the
          # cannot-pay row on score and lost to it on registry order, so this one states itself.
          bias=2,
          avoid=("cant pay", "can't pay", "behind on", "arrears", "debt", "cut off",
                 "prepayment meter", "how do i pay")),
    # Two other winter sums, told apart from the discount above: one is a lump for pensioners,
    # the other is paid per cold spell, and neither is the £150 off an electricity bill.
    entry("winter-fuel",
          (("winter fuel",),
           ("what", "who", "how much", "qualify", "eligible", "get", "paid", "when", "claim",
            "do i get", "can i get", "check")),
          ("The Winter Fuel Payment is a one-off lump each winter for pensioners who get Pension "
           "Credit or another means-tested benefit, paid automatically in November or December, "
           "and it is not the Warm Home Discount. The Cold Weather Payment is a separate sum "
           "again: £25 for each seven-day spell where the temperature where you live stays at 0C "
           "or below, paid within 14 days of the spell."),
          avoid=("cant pay", "can't pay", "behind on", "arrears", "debt", "prepayment meter"),
          bias=1),
    # Told apart from the winter lump, because the lines that ask for it by name were answered
    # with the winter fuel payment, which is a different sum with different rules.
    entry("cold-weather-payment",
          (("cold weather payment", "cold weather payments"),
           ("what", "how much", "qualify", "eligible", "get", "paid", "when", "claim",
            "do i get", "can i get", "check", "am i")),
          ("It is £25 for each seven-day spell where the temperature where you live stays at 0C "
           "or below, paid within 14 days of the spell to people on Pension Credit, income "
           "support, jobseeker's allowance, employment and support allowance or universal credit "
           "with a health element. There is nothing to claim: the payment is automatic, and the "
           "cold weather payment is not the Warm Home Discount or the Winter Fuel Payment."),
          avoid=("cant pay", "can't pay", "behind on", "arrears", "debt", "prepayment meter"),
          bias=1),
    entry("standing-charge", (("standing charge",),
                              ("what", "why", "mean", "high", "pay", "charge")),
          ("It's a fixed daily fee, usually 40-60p a day for each fuel, covering the pipes, meters "
           "and network costs, and you pay it even in a month with no heating on. It varies by "
           "supplier and region, so it's one more line to compare when you switch.")),
    entry("habit-cost", (("coffee", "latte", "cappuccino", "flat white", "meal deal", "sandwich",
                          "lunch", "lunches", "takeaway", "takeaways", "deliveroo", "just eat",
                          "snack", "snacks", "cigarettes", "fags", "vape", "pint", "pints", "beer",
                          "bottle of wine", "smoking", "smoke", "smoker"),
                         ("a year", "in a year", "over a year", "per year", "costing me",
                          "costs me", "adds up", "a day", "every day", "daily", "a week",
                          "a month", "does it cost", "do it cost", "cost over", "the cost of",
                          "what i spend")),
          _habit_cost,
          # the food shop, the meal plan and the takeaway-as-a-meal are other entries' lines
          avoid=("food shop", "weekly shop", "meal plan", "meal ideas", "what can i cook",
                 "budget for food", "per week for food", "christmas", "subscriptions", "switch",
                 # how often to have one, or how much is a safe amount, is a health and food
                 # question, not a money one: "How much coffee a day is too much?" was priced.
                 "should i eat", "how often", "is it bad", "healthy", "is it ok",
                 "is too much", "how much is too much", "much coffee", "caffeine", "how many",
                 "safe", "limit", "units", "calories",
                 # "how much beer can i drink a day" is the weekly-limit question, and this
                 # entry was pricing it at £5.50 a pint because "beer" and "a day" are both in
                 # its key. A question about how much is safe to drink is not a bill.
                 "can i drink", "should i drink", "is it safe to drink", "allowed to drink"),
          # A price needs a cost in the line. "i have 12 cups of coffee a day" and "i drink 16
          # coffees a week" only say how much somebody drinks, and pricing them answers a money
          # question nobody asked; what that amount does to you is the caffeine answer.
          ask=("cost", "costs", "costing", "cost me", "spend", "spends", "spent", "spending",
               "save", "saves", "saving", "savings", "adds up", "afford", "budget", "budgeting",
               "money", "expensive", "worth", "how much", "how much is that", "in a year",
               "a year")),
    # "my water bill is high" and "my water bill has gone up" were a shrug on main, and "my water
    # bill is too high" was answered with a plumber's quote: the complaint words were not in the
    # key at all. They are now, so the bill question is this entry's however it is said.
    entry("water-bill", (("water bill", "water meter", "water rates"),
                         # A bill that went up is `bill-went-up`, which says to ask why, from
                         # which date and for a reading: the rise words were here for a round and
                         # they outscored it, so a water rise got the average bill instead.
                         ("reduce", "save", "lower", "cheaper", "worth", "how", "much", "should",
                          "fit", "fitted", "get",
                          # "my water bill is too high" is the same question, and without these
                          # words it reached the builder's-quote tip in the fallback. "has gone
                          # up" is why it rose, which `bill-went-up` answers better, so the rise
                          # words are not here. "high" on its own, "huge", "massive" and "higher"
                          # were a shrug: "my water bill is high" got "Thanks for telling me" and
                          # "my water bill is huge" only had the amount said back.
                          "too high", "so high", "expensive", "big", "high", "higher", "huge",
                          "massive", "why")),
          # The order matters to main's `TheWaterBillAnswersBeforeItSaysHowBigTheBillIs`: the
          # thing to do comes before the average bill, because "£450" is the size of the
          # problem and the water company is the answer to it. The meter rule of thumb is main's
          # own `choice-worth` wording, kept here because this entry now answers the shapes that
          # entry hands over (`is a water meter cheaper`, `will a water meter save me money`).
          ("Ask your water company to check the reading and the tariff, and for a free meter if "
           "there are more bedrooms than people: that is usually cheaper, and you can switch back "
           "within a year. A typical household bill is around £450 a year, about £38 a month, set "
           "by your region unless you are on a meter, and on a meter showers instead of baths, "
           "full loads and a fixed dripping tap cut the most."),
          # `avoid` is matched as a run of words, so a phrase that ends before the end of the
          # question swallows its own variants: "should i get a water meter" stood this entry
          # down for "should i get a water meter fitted" too, and main's `choice-worth` no longer
          # has that line, so it had no answer at all. The worth shapes are named in full.
          avoid=("should i have a water meter", "should we have a water meter",
                 "do i need a water meter", "can i get a water meter",
                 "a water meter worth it", "worth getting a water meter",
                 "worth having a water meter", "water meter worth installing",
                 "worth fitting a water meter", "worth installing a water meter")),
    entry("bill-dispute", (("says i owe", "said i owe", "claim i owe", "i already paid",
                            "i thought i paid", "i thought id paid", "thought i had paid",
                            "paid it all", "overcharged", "charged twice", "disputed",
                            "wrong bill",
                            # The wrong way round: "my gas bill is wrong" is the same dispute as
                            # "wrong bill", and in that order it got a general Citizens Advice
                            # reply instead of anything about the bill. The fuel is named first so
                            # that a bare "the bill is wrong", which is the restaurant bill,
                            # keeps its answer.
                            "gas bill is wrong", "energy bill is wrong",
                            "electricity bill is wrong", "water bill is wrong",
                            "utility bill is wrong", "my bill is wrong",
                            "gas bill was wrong", "energy bill was wrong", "my bill was wrong",
                            "gas bill looks wrong", "gas bill is way off",
                            # "what do i do about a bill thats wrong" named the bill and the
                            # wrongness and nothing else, and got a shrug: the shapes above all
                            # name the fuel or say "my bill", and no other entry holds the
                            # argument over a bill that is simply wrong. "a" is in each of these
                            # so a restaurant's "the bill is wrong" stays the charge-not-ordered
                            # row, which is the card that names the charge to take off.
                            "a bill thats wrong", "a bill that is wrong",
                            "bill thats wrong", "bill that is wrong",
                            # "can i refuse to pay a charge i think is unfair" is the same dispute,
                            # asked as a right rather than as a wrong figure
                            "refuse to pay", "not paying", "won't pay", "wont pay", "unfair",
                            "not fair", "wrong charge", "missold", "mis-sold", "overcharge"),
                           ("bill", "letter", "energy", "water", "company", "they", "but",
                            "overcharged", "twice", "charge", "charges", "fee", "fees")),
          ("Ask for the bill in writing with the dates and amounts, and send your proof of "
           "payment — bank statement, reference number — in writing too: a dispute is settled on "
           "paperwork, not on the phone. Keep paying what you agree you owe meanwhile, and if it "
           "is energy or water, complain to the company first and then to the free ombudsman."),
          # "it is not fair" is how people say they are cross about anything at all, and with
          # "they" beside it in the key that was enough to answer a rota change with a bill
          # dispute ("actually its not fair, they changed my rota again" -> "Ask for the bill in
          # writing with the dates and amounts"). A dispute needs something disputed in the line:
          # the bill, the charge, the company, or the money owed. The other keys are already a
          # phrase that says so ("says i owe", "charged twice"), so this only holds back the two
          # that are a feeling and a pronoun.
          ask=("bill", "bills", "charged", "charge", "charges", "fee", "fees", "paid", "pay",
               "owe", "owed", "overcharged", "company", "energy", "water", "gas", "supplier",
               "invoice", "statement", "account", "refund", "money", "cost", "amount", "card",
               "direct debit", "bill", "pounds", "quid", "£"),
          # A council tax bill is the lifeadmin answer's job, and it is the better one there:
          # the council's own line, the instalment-by-instalment breakdown, the single-person
          # discount. The word "council" left this entry's key for the same reason.
          avoid=("council tax", "council", "band", "single person discount"),
          bias=1),
    entry("council-tax", (("council tax", "council tax bill", "council tax band",
                           "council tax rebate", "single person discount", "council tax reduction"),
                          ("reduce", "discount", "single", "appeal", "band", "lower", "cheaper",
                           # the bill is charged on the home: "is council tax per person",
                           # "does council tax count my partner" and "how many people pay" ask
                           # what it is charged on, which is neither the band nor a discount
                           "per person", "each person", "per household", "each household",
                           "how many people", "who has to pay", "who pays", "counted",
                           "count my partner", "counts my partner", "does my partner",
                           "does my flatmate", "count my flatmate", "two of us", "both of us",
                           "in the house",
                           "bill", "months", "spread", "instalments", "pay", "money off",
                           "live alone", "alone", "single person", "25", "student", "students",
                           "empty", "how", "change", "name", "wrong", "moved", "move", "much",
                           "tenant", "cut",
                           # A bill that is too high is the same complaint as a water or energy
                           # bill that is too high, and it was answered by the posture card:
                           # "council tax is too high what can i do" got "Most bad posture is the
                           # chair and the sitting still". "high" is the amount and not a height,
                           # and these words are what say so. The rise words are not here on
                           # purpose: "my council tax has gone up a lot" is `bill-went-up`, which
                           # answers the rise better than the size of the bill.
                           "too high", "so high", "too much", "expensive", "high", "higher",
                           "huge", "massive", "sky high",
                           # A name change is a form, not a disputed bill: these phrases are here
                           # so this entry outranks the letter entry main grew for arrears.
                           "change the name", "name on the bill", "name on the account",
                           "in my name", "new name", "change of name",
                           # the money back on the account, so a council tax refund is answered
                           # by the council and not by the shop's 30-day return
                           "refund", "refunds", "money back", "rebate")),
          # Over the year this one entry is asked two different questions, so it answers the one
          # the line actually asks: a name or an address first, the discounts otherwise.
          _council_tax,
          # A disputed bill or a reminder is the letter entry's question, not this one, so this
          # entry lets the letter keep the arrears rows and wins only the ones it asks about.
          bias=1,
          avoid=("return", "self assessment", "self-assessment", "hmrc", "income tax", "tax code",
                 "p60", "p45", "side income", "reminder", "remind", "remind me",
                 "dont let me forget", "don't let me forget", "dont forget to",
                 "don't forget to", "nudge me", "arrears", "summons", "thought i paid",
                 "i thought", "overpaid", "wrong reference", "breakdown", "owe", "owed",
                 "court", "bailiff", "enforcement",
                 # the band of the house has its own answer, with the free valuation list in it
                 "band", "bands")),

    # --- housing -----------------------------------------------------------------
    entry("rent-deposit", (("deposit", "deposits"),
                           ("landlord", "agency", "scheme", "protect", "months", "much", "many",
                            "need", "pay", "worth",
                            # a room in a share is the same deposit question as a flat, and
                            # "how much deposit for a room" was the house-buying card (10% of the
                            # price, £20,000 on a £200,000 home) with nothing about five weeks.
                            "room", "rooms", "flatshare", "flat share", "house share", "houseshare",
                            "share", "flat", "rent", "rental", "renting", "weeks", "week",
                            "tenancy")),
          _rent_deposit,
          # "my landlord wont give my deposit back" is home's deposit-back entry: a debt to be
          # argued, not a sum to be worked out.
          avoid=("house", "home", "buy", "buying", "mortgage", "give", "back", "returned",
                 "return it", "kept", "keep", "keeps", "keeping", "withheld", "not returned",
                 "unfair", "disagree",
                 # a deposit on a car, a sofa, a holiday or a wedding is not a tenancy: with the
                 # bias below this row took "how much deposit for a car" from its own card
                 "car", "cars", "van", "bike", "motorbike", "bicycle", "sofa", "furniture",
                 "holiday", "wedding", "hotel", "booking", "flight", "course", "university",
                 # a deposit being saved towards a house is the buying row's, and "i need to
                 # save for a deposit" reached this one on the strength of the bias below
                 "save", "saving", "save up", "should i have", "i need to save",
                 # a pet deposit is the pet row's rule, and its own answer says why
                 "pet", "pets", "dog", "dogs", "cat", "cats", "animal", "animals",
                 # a deposit being chased or lost is home's deposit-back entry, not a sum
                 "lost", "lose", "wont", "won't", "hasnt", "hasn't", "refuse", "refuses",
                 "refused", "chase", "chasing", "still not", "not answer"),
          # The bias below lifts a line that holds only "deposit" over the bar, so the row
          # needs its own subject as well: a room, a flat, rent, a landlord, a scheme - or the
          # question about the size of it. "i need to save for a deposit" is the buying row's.
          ask=("room", "rooms", "flatshare", "flat share", "house share", "houseshare", "flat",
               "flats", "rent", "rents", "renting", "rental", "tenancy", "tenancies",
               "landlord", "landlords", "agent", "agency", "scheme", "protection", "cap",
               "how much", "much", "equivalent", "weeks", "week", "worth"),
          # the buying-deposit row is keyed on the same two words, and the rent cap is the
          # narrower subject: a room or a flat cannot be bought with a 5% deposit
          bias=2),
    entry("rent-vs-buy", (("rent", "renting"), ("buy", "buying", "better", "worth", "mortgage",
                                                 "instead", "own")),
          ("Buying usually wins if you'll stay five years or more, because the deposit, fees and "
           "stamp duty take about that long to cancel out. Renting is cheaper for shorter stays "
           "and gives you the freedom to move, so the honest answer is how long you plan to stay."),
          # A car, a van, a bike or a sofa is something else you buy while renting: the rent
          # comparison needs a home in it.
          avoid=("car", "cars", "van", "bike", "motorbike", "bicycle", "sofa", "camera",
                 "laptop", "phone", "holiday", "wedding", "furniture",
                 # "my rent is 800 and i want to buy a 20000 car" then "how long will that take"
                 # is the goal's arithmetic, not the rent-versus-buy comparison
                 "how long will that take", "how long does that take", "how long will it take",
                 "how long would that take")),
    entry("first-home-steps", (("house", "flat", "property", "first home", "first house",
                                "first flat", "buy a home", "buying a home", "own home",
                                "housing ladder", "ladder", "deposit", "mortgage"),
                               ("save", "saving", "save up", "saving up", "how do i start",
                                "where do i start", "get started", "start saving", "start to save",
                                "start looking", "begin", "get on", "what do i need",
                                "what do i need first", "steps", "how long", "afford",
                                # "start" as the filler people put before the thing they are
                                # starting: "i want to start buying a house" is this entry's
                                # question, and the property word is what says which home it is,
                                # so the property phrases hold it to the subject.
                                "want to start", "start buying a house", "start buying a flat",
                                "start on the property", "start on the housing ladder",
                                "start on the ladder", "want to buy a house",
                                "want to buy a flat", "want to buy a home", "looking to buy",
                                # the person already buying says so rather than asking: "im
                                # buying a house", "we're in the process of buying a flat". The
                                # property word is still what says it is a home.
                                "buying a house", "buying a flat", "buying a home",
                                "buying my first", "buying our first", "in the process of buying",
                                "had an offer accepted", "offer accepted")),
          _first_home_steps,
          # a renovation, a rental, and a deposit the landlord is holding are other questions
          avoid=("renovate", "renovating", "renovation", "extend", "extension", "decorate",
                 "decorating", "paint", "kitchen", "bathroom", "furniture", "landlord", "tenant",
                 "rent", "renting", "back", "withheld",
                 # "i want to buy a flat screen tv" is a flat adjective and a screen, not a home
                 "flat screen", "flat-screen", "tv", "television", "monitor",
                 # "i want to buy a house but have no deposit" is the deposit question, and
                 # house-deposit answers it: this entry would take it with "want to buy a house"
                 "no deposit", "without a deposit", "havent got a deposit", "haven't got a deposit",
                 "no savings", "deposit is the problem",
                 # "i want to buy a home gym" is a thing for the home, not a home: "buy a home"
                 # is in the key, so the thing after it has to be allowed to say it is furniture
                 # or equipment. A house with a garden or for my family still reaches the steps.
                 # "home bar" stays out: it would fall to the phone-signal answer.
                 "home gym", "home cinema", "home theatre", "home theater", "home office",
                 "home security", "home sauna", "home brew", "home insurance",
                 # "working from home" is where someone is, not a house to buy, and a feeling is
                 # never a buying question: "i have been feeling really lonely since i started
                 # working from home" was answered with a Lifetime ISA.
                 "working from home", "work from home", "wfh", "lonely", "loneliness",
                 "feel", "feeling", "felt",
                 # and the other shapes the same report came in
                 "isolated", "isolation", "on my own", "depressed", "anxious", "miserable",
                 "fed up", "hate", "hates", "unhappy", "bored"),
          # "how long does it take to clean the house" is a duration question about housework,
          # and "how long" is one of this row's asks, so the job words have to stand it aside.
          guard=_not_a_job_on_the_house),
    # --- what to offer for a house ----------------------------------------------
    # Four everyday lines, four different wrong answers: "how much should i offer on a house"
    # was an honest punt, "what should i offer for a house" was a music genre, "how much under
    # asking price should i offer" got a freelancer's letter raising their rate, and "is it
    # worth offering below asking price" got the CamelCamelCamel price-history card. A house is
    # not a shop and an offer on one is not haggling over a sofa: the comparables are sold
    # prices, and the answer is how to find them and what to say.
    entry("offer-on-a-house",
          (("house", "flat", "home", "property", "bungalow", "terraced", "semi", "detached",
            "asking price", "estate agent", "seller"),
           # Every word here has to show that a price is being discussed, because the group
           # above is only the word "house" or "home": bare "offer", "under", "over" and
           # "accept" made this row answer "i feel under pressure at home", "my brother is over
           # at our house all the time", "should i offer to help my mum at home" and my gran's
           # care with the sold-prices card.
           ("offer on", "offer for", "offering on", "offering for", "offer under", "offer over",
            "offer below", "offer above", "make an offer", "put in an offer",
            "how much should i offer", "how much to offer", "what should i offer",
            "how much under", "below asking", "under asking", "over asking", "above asking",
            "asking price", "negotiate", "haggle", "drop my asking", "drop the asking",
            "reduce my asking", "accept my offer", "accept the offer", "accept our offer",
            "accept a lower", "accept anything", "first offer", "second offer", "final offer",
            "gazump", "gazundering", "worth offering")),
          ("Offer against the sold prices, not the asking price: asking prices are hopes, and the "
           "only evidence is what the same sort of house on the same street actually sold for in "
           "the last year, which is free on the Land Registry sold-price site and in Rightmove's "
           "sold-house filter. If those come out 5-10% under the asking price, that is where to "
           "start; if they come out at or above it, offering much under wastes everyone's time. "
           "Put the offer to the agent in writing with the amount, the words \"subject to "
           "contract\", your mortgage agreed in principle and your position (first-time buyer, "
           "no chain, cash). Move in small steps, 2-3% at a time rather than jumping to your "
           "maximum, and treat \"we have other interest\" as a nudge rather than a fact: ask "
           "for it in writing before you pay more for it."),
          # the deposit, the mortgage, a rent and a renovation each have their own answer, and a
          # landlord holding money back is not an offer
          avoid=("deposit", "mortgage", "remortgage", "rent", "renting", "landlord", "tenant",
                 "withheld", "renovate", "renovating", "extension", "offer accepted",
                 "how much is my house worth", "house prices", "stamp duty",
                 # a bare "how much" beside a flat was the whole of the notice question, so the
                 # amount words go and the offer words stay: "how much notice do i give to leave
                 # my flat" was answered with comparables and "subject to contract"
                 "notice", "tenancy", "tenancies", "leave", "leaving", "move out",
                 "moving out", "break clause", "deposit back", "my deposit",
                 # "offer" is also what a shop does, and what a job does
                 "job offer", "job offers", "offer of a job", "salary", "car", "car boot",
                 "sofa", "couch", "shopping", "sale", "discount", "coupon", "voucher",
                 # cover you buy is not an offer you make: "how much does home insurance cost"
                 # read the word "home" and the word "how much" and answered with sold prices
                 "insurance", "insured", "insure", "premium", "premiums", "policy", "policies",
                 "cover", "buildings", "contents"),
          bias=1),
    # "how much should i put down on a house" is the same question as "how big a deposit do i
    # need", and the bare word "deposit" was the whole first key group, so the line missed it.
    entry("house-deposit", (("deposit", "deposits", "put down on", "how much to put down",
                             "down payment"),
                            ("house", "home", "flat", "property", "mortgage", "how much",
                             "how big", "how much is", "save", "first", "buy")),
          _house_deposit, bias=1,
          # "i put down a deposit on a flat" is a tenancy, not a purchase: the money is the
          # landlord's and the question is about getting it back. The tenancy words do that on
          # their own - "put down a deposit" in this fence cancelled the "put down on" the row
          # had just gained, so "i put down a deposit on a house" was left with nothing.
          avoid=("landlord", "agency", "tenant", "back", "rent", "renting",
                 "holding deposit", "tenancy", "tenancies", "let", "letting", "check out")),
    entry("shared-ownership", (("shared ownership", "shared owner", "shared equity",
                                "part buy part rent"),
                               ("what", "is", "how", "works", "mean", "worth", "good", "bad",
                                "buy", "get into", "apply", "deposit", "rent")),
          ("You buy a share, usually 25% to 75%, and pay rent on the rest to the housing "
           "association: the mortgage only covers your share, but the rent and the service charge "
           "come on top, so ask what both are before you offer. You can buy more shares later "
           "(staircasing), and selling is slower because the association finds the buyer. It is "
           "worth it where rents are high and you want to stop renting, and it is a bad deal if "
           "the service charge is steep or the lease is short - check both, and only use a "
           "regulated scheme run by a council or a housing association."),
          # a shared house with friends, and a shared account, are other questions
          avoid=("flatmate", "flatmates", "housemate", "housemates", "with friends", "joint"),
          ask=("shared ownership", "shared owner", "shared equity", "part buy part rent")),
    entry("help-to-buy", (("help to buy", "help-to-buy", "htb"),
                          ("what", "is", "was", "still", "available", "apply", "applications",
                           "ended", "mean", "how", "scheme", "isa", "equity loan")),
          ("Help to Buy in England was an equity loan: the government lent 20% of the price (40% "
           "in London) on a new build, interest-free for five years, and new applications closed "
           "at the end of March 2023. Nothing replaced it as it was - the help that exists now is "
           "shared ownership, First Homes and the mortgage guarantee scheme, and a Lifetime ISA "
           "adds 25% to what you save. A Help to Buy ISA closed to new savers in 2019, but an "
           "existing one can still be used until 2030. Scotland and Wales ran their own schemes, "
           "so check what your country offers now."),
          ask=("help to buy", "help-to-buy", "htb")),
    entry("buying-costs", (("costs of buying", "cost of buying", "extra costs", "hidden costs",
                            "fees when buying", "what else do i have to pay", "how much does it "
                            "cost to buy", "the fees"),
                           ("house", "home", "flat", "property", "buying", "buy", "first home",
                            "first house", "move", "moving")),
          ("On top of the deposit, budget for stamp duty (nothing on most first homes), legal "
           "fees of \u00a31,000 to \u00a31,500, a survey at \u00a3400 to \u00a3700, a mortgage "
           "arrangement fee of \u00a30 to \u00a31,000 if you are not paying it up front in the "
           "rate, and \u00a3500 or so for removals and the searches. On a \u00a3250,000 first "
           "home that is roughly \u00a33,000 to \u00a34,000 of costs beside the deposit, and none "
           "of it can come from the deposit itself."),
          avoid=("renting", "landlord", "tenant", "deposit back", "renovate", "renovation")),
    entry("mortgage-afford", (("mortgage", "mortgages", "house", "flat", "borrow"),
                              ("too much", "afford", "can i borrow", "how much can i borrow",
                               "how much could i borrow", "a year", "salary", "times my income")),
          _mortgage_afford,
          # The numbers are the whole question here: without them this entry passes and the
          # explainer answers.
          bias=2,
          # bare "flat" plus any quantity word is not a mortgage question: "im moving flat next
          # month and ive got too much stuff" reached this answer, and the moving answer is its
          ask=("mortgage", "mortgages", "borrow", "afford", "affordability", "salary", "income",
               "earn", "earnings", "deposit", "house price", "price", "a year", "per year",
               "take home", "can i get", "how much"),
          avoid=("rejected", "refused", "declined", "turned down", "remortgage", "overpay",
                 "fixed rate", "broker", "deposit for")),
    entry("mortgage-basics", (("mortgage", "mortgages", "small deposit", "5% deposit",
                               "5 per cent deposit", "95% mortgage", "95 per cent mortgage",
                               "mortgage with a small deposit", "mortgage with a 5% deposit"),
                              ("what", "how", "works", "much", "need", "apply", "borrow", "deposit",
                               "small", "little", "put down", "raise")),
          ("A mortgage is a loan secured on the home, usually over 25 to 35 years: you put down a "
           "deposit of at least 5% (10% gets much better rates) and borrow the rest. Lenders "
           "usually cap the loan at about 4.5 times your income, so £30,000 a year plus a 10% "
           "deposit buys roughly £135,000. Most people fix the rate for two to five years, and a "
           "fee-free broker will compare the whole market for you, which is worth doing even if "
           "you think you know your bank."),
          # "how do i get a mortgage with a small deposit" tied the tenancy-deposit answer, and
          # the registry reads home before money, so the flat's deposit came back to a mortgage
          # question. This only touches lines with a mortgage word in them.
          bias=1,
          avoid=("rejected", "refused", "declined", "turned down", "denied", "cant get",
                 # "what happens if i miss a mortgage payment" asked what happens, and got what a
                 # mortgage is: a payment that has failed is the missed-payment answer.
                 "miss", "missed", "missing", "cant pay", "can't pay", "not paid", "behind on",
                 "arrears", "late", "overdue", "forgot", "payment",
                 # "how much can i overpay my mortgage" and "what happens if i overpay" are the
                 # overpayment question, and what a mortgage is answers neither.
                 "overpay", "overpaying", "overpayment", "overpayments", "pay off early",
                 "paying off early", "paid off early", "early repayment", "lump sum",
                 "settle early", "underpayment")),
    entry("remortgage", (("remortgage", "remortgaging", "switch my mortgage", "switching mortgage",
                           "switch mortgage", "switch lender", "mortgage deal",
                           "my mortgage rate"),
                          ("worth", "should", "better", "fix", "deal", "rate", "when", "now",
                           "switch", "switching", "how", "do i", "apply", "process")),
          ("Remortgaging is worth it when a new deal beats your current rate by enough to cover the "
           "costs, which are usually £1,000-£2,000, so a drop of about 0.5% or more normally does. "
           "Start looking three to six months before your current deal ends and check the early "
           "repayment charge first.")),
    # "should i fix my mortgage", "fixed or variable", "is a tracker better than a fix" and "how
    # long should i fix for" are one decision, and the bot had no answer to it: two of them went
    # to the free-advice punt, one to a definition, one to garage labour costs and one to a smart
    # watch. The penalty for drifting onto the standard variable rate is the figure that decides
    # it, so it is in the first sentence.
    # A mortgage offer is the lender's yes, and the only thing people ask about it is how long it
    # has left: "how long does a mortgage offer last" was answered with the fixed-versus-tracker
    # card, which is a question about the rate and not about the piece of paper's expiry.
    entry("mortgage-offer-validity",
          (("mortgage offer", "mortgage offers", "the offer", "lenders offer", "lender's offer",
            "offer letter"),
           ("how long", "last", "lasts", "valid", "validity", "expire", "expires", "expiry",
            "run out", "runs out", "months", "how many months", "still good",
            "out of date")),
          ("A mortgage offer usually runs three to six months from the date it is issued, six months "
           "being the common one, and the clock starts when the lender sends it rather than when "
           "you applied. If the purchase is close but not close enough, ask the lender for an "
           "extension before it lapses - most will extend it for a fee or free - and do not "
           "exchange contracts on an offer with only days left on it."),
          bias=2,
          avoid=("energy", "gas", "electricity", "tariff", "job offer", "job", "salary",
                 "pay", "wage", "university", "uni", "school", "college", "house price",
                 "make an offer", "offer on a house", "estate agent")),
    entry("fix-or-track", (("mortgage", "mortgages", "home loan", "tracker"),
                           ("fix", "fixed", "fixed rate", "tracker", "variable", "long",
                            "length", "how long")),
          ("A fix buys certainty and you pay a little more for it, usually a quarter to half a "
           "point over the cheapest tracker, so take the fix if a two point rise would put the "
           "payment out of reach and the tracker if you could absorb that and would rather pay "
           "less now. Five years is the usual middle: long enough to be worth an arrangement fee "
           "of about \u00a3999, short enough not to lock you in if you might move. Check the early "
           "repayment charge before you pick a length, because leaving inside the fix usually "
           "costs one to five percent of what is left on the loan."),
           bias=1,
           # a fixed energy tariff and a mortgage payment that has already gone up are other
           # answers
           avoid=("energy", "gas", "electricity", "tariff", "supplier", "price cap", "bill",
                  "bills", "meter", "fitness", "watch", "wristband", "savings", "isa", "bond",
                  "went up", "gone up", "jumped", "risen", "increased", "cant pay", "can't pay",
                  "missed", "arrears", "struggling",
                  # a fitness tracker, a fund that tracks the market and a term that is already
                  # running are other answers
                  "garmin", "fitbit", "strava", "steps", "fund", "index", "stocks", "shares",
                  "arrange", "arranging", "get a mortgage", "how much")),
    entry("mortgage-rejected", (("mortgage", "mortgage application", "mortgage offer"),
                                ("rejected", "refused", "declined", "turned down", "denied",
                                 "next", "now what", "why")),
          ("Ask the lender why in writing: it's nearly always the credit file, the deposit size or "
           "the affordability sum. Fix errors on your report, save a bigger deposit and use a "
           "whole-of-market broker; don't send several applications at once, because each one "
           "leaves a mark for a few months.")),
    entry("mortgage-broker", (("broker", "mortgage broker", "mortgage adviser", "mortgage advisor"),
                              ("what", "do", "does", "did", "cost", "fee", "worth", "need", "use",
                               "paid", "charge", "should")),
          ("A broker compares deals across the market and checks what a lender will actually offer "
           "you, which matters most if your income is unusual, you're self-employed or your credit "
           "file has a mark on it. Many are paid by the lender, so ask upfront whether they charge "
           "a fee as well, and use one that covers the whole market rather than a single bank.")),

    entry("savings-by-age",
          (("saved", "savings", "save", "saving", "put away", "nest egg"),
           ("by 30", "by 40", "by 50", "by 25", "by 35", "by 45", "by 55", "by 60", "by the time",
            "at 30", "at 40", "by my age", "my age", "behind", "on track", "target", "targets",
            "enough", "should i have", "how much of it", "how much should i be saving")),
          ("Put away 10 to 20 percent of your take-home, and get three to six months of essential "
           "spending in place first: that keeps a lost job from becoming debt. A rough guide after "
           "that is one year's pay by 30, three by 40 and six by 50, so 30k a year means 30k at 30 "
           "and 90k at 40. Save on payday, not at month end."),
          # A Christmas or holiday pot, a deposit and a card balance are all sums with a date or a
          # job of their own, not "am I behind for my age", and the account questions are the
          # bank's.
          avoid=("account", "which bank", "interest rate", "isa", "christmas", "xmas",
                 "december", "holiday", "wedding", "car", "house", "flat", "deposit", "quid",
                 "pay off", "credit card", "overdraft", "loan", "pension",
                 # a line with no age in it stays with the rainy-day fund, where main answers it
                 "emergency fund", "rainy day", "in savings", "months of"),
          # "how much should i have saved by 30" ties with the emergency fund on the words, and the
          # age in the line is what makes it this answer. A line with no age in it stays with the
          # rainy-day fund, which is where main answers it.
          bias=1),
    entry("home-insurance", (("insurance", "home insurance", "contents insurance",
                              "buildings insurance", "house insurance"),
                             ("contents", "buildings", "home", "house", "worth", "need", "much",
                              # "my washing machine broke can i claim on insurance" was reaching
                              # the working-from-home flat rate instead of cover
                              "claim", "broke", "broken", "washing machine", "appliance",
                              "freezer", "flood", "leak", "stolen", "burgled")),
          ("Buildings insurance covers the structure and comes with the mortgage; contents covers "
           "what's inside and is optional but usually worth it. Insure for the cost of rebuilding "
           "or replacing, not the market value, and check the single-item limit before assuming a "
           "bike or laptop is covered. A machine that has simply worn out is not a claim - that is "
           "a repair - while accidental damage cover or a home emergency policy is what pays for a "
           "leak or a boiler that has packed in."),
          # "my washing machine broke can i claim on insurance" tied the working-from-home flat
          # rate, and the registry read that first. Only a line with an insurance word reaches
          # this entry at all, so the bias cannot take anything else.
          bias=1, avoid=("travel", "abroad", "holiday", "pet", "car",
                         # a gap policy is sold with car finance, not with the house, and it has
                         # its own row: this key holds a bare "insurance", so the phrase has to be
                         # kept out or "do i need gap insurance" gets buildings and contents
                         "gap insurance", "gap cover", "gap protection",
                         # an excess is the first part of a claim, not a question about cover
                         "excess",
                         # driving has its own cover: "do i need insurance to drive" names no
                         # car and was answered with buildings and contents
                         "drive", "driving", "on the road", "motorbike", "van insurance",
                         "third party", "fire and theft",
                         # a national insurance number is not cover you buy: "do i need a
                         # national insurance number" and "how much national insurance do i
                         # pay" were both sold home insurance
                         "national insurance", "ni number", "insurance number",
                         # life cover is a different policy with a different question: "do i
                         # need life insurance" was answered with buildings and contents
                         "life insurance", "life cover", "life policy", "life assurance",
                         "term insurance", "term life", "death in service", "die", "died",
                         "death", "funeral")),
    # "do i need life insurance" was answered with buildings and contents cover, and "is life
    # insurance worth it" with a complaint about mis-selling: nothing in the money rows was about
    # the policy that pays out when someone dies. The question people actually ask is whether
    # they need it at all, so the answer starts there and names the figure.
    entry("life-insurance",
          (("life insurance", "life cover", "life policy", "life assurance", "term insurance",
            "term life", "death in service", "death in service benefit"),
           ("do i need", "need", "needed", "how much", "how much cover", "worth it", "should i",
            "what is", "whats", "get", "buy", "arrange", "take out", "cover", "much")),
          ("Cover is for whoever would lose money if you died: a partner, children, a joint "
           "mortgage. Check your workplace pension first, because death in service usually pays "
           "two to four times your pay already. If someone does depend on you, level term cover of "
           "about ten times your income, running until the children are grown or the mortgage "
           "ends, is the usual shape, and it costs less than most people expect. With no "
           "dependants, savings for a funeral are usually enough."),
          # a home policy, a claim and a car policy are the other insurance questions
          avoid=("home", "house", "contents", "buildings", "claim", "excess", "car", "travel",
                 "pet", "national insurance", "ni number", "gadget", "phone")),
    entry("car-insurance", (("car insurance", "insurance",
                             # "whats the cheapest way to insure my car" reached the cheap-meals
                             # entry, because neither half of this key had the verb in it
                             "insure", "insuring", "insured", "to insure a car"),
                            ("cheap", "cheaper", "reduce", "lower", "renewal", "quote",
                             "expensive", "best", "save", "new driver", "just passed",
                             # "how much is car insurance" asked the price and reached nothing
                             "much", "how much", "cost", "costs", "price", "average",
                             "first car", "learner", "young driver", "17", "18",
                             # a move changes the postcode, which changes the premium
                             "move", "moving", "moved", "new address", "new postcode",
                            # "i need to sort out my car insurance" is the buying question,
                            # not the legal-minimum one
                            "sort out", "sort", "arrange", "get", "buy", "take out",
                            "shop around", "insure", "due", "need", "needed",
                            "cheapest", "cheapest way")),
          ("Shop around about three weeks before renewal, comparing a few sites plus a couple of "
           "direct insurers: loyalty is punished. A higher voluntary excess, a named driver, "
           "paying annually instead of monthly and a black-box policy all bring the price down. "
           "A new driver pays £1,500 to £2,500 in the first year, so a telematics policy that "
           "scores your driving is usually the biggest saving there is."),
          avoid=("travel", "holiday", "home", "contents", "pet", "phone", "life",
                 # the animal is what makes it pet insurance, and the line often names the animal
                 # rather than the word "pet": "how much does a dog cost to insure" was answered
                 # with three weeks-before-renewal car advice
                 "dog", "dogs", "puppy", "puppies", "cat", "cats", "kitten", "kittens",
                 "rabbit", "rabbits", "hamster", "horse", "pony", "guinea pig",
                 # the cover the law makes you buy is the entry below, not the price one
                 "minimum", "legal", "legally", "law", "by law", "third party", "third-party",
                 "comprehensive", "fully comp", "compulsory", "required")),
    # "what insurance do i need for a car" reached the GHIC travel card, because "insurance" plus
    # "need" is the travel entry's pair of words. The car is the subject here, so the car words
    # are in the key and the other kinds of insurance are kept out.
    entry("car-insurance-minimum",
          (("car", "cars", "vehicle", "van", "motorbike", "motoring", "scooter", "moped",
            # the law question often names no car at all: "what cover does the law require",
            # "what does third party only cover" and "do i need insurance to drive" reached
            # nothing or the wrong entry, because only a car word opened this one
            "insurance", "cover", "third party", "third-party", "fire and theft"),
           ("minimum", "legal", "law", "by law", "compulsory", "required", "third party",
            "third-party", "comprehensive", "fully comp",
            # the question about the law reads "what insurance do i need for a car", so the
            # asking phrase is part of the key; a bare "need" is the buying question instead
            "do i need", "insurance do i need", "what do i need", "am i required",
            "legally", "by law do i")),
          ("By law you need third-party cover, which pays for other people's injury and damage but "
           "not for your own car. Comprehensive usually costs only a little more over a year, so "
           "for anything but a very cheap car it is the better buy. Breakdown cover is separate, "
           "and declare any modification, because an undeclared one can void the policy."),
          avoid=("travel", "abroad", "holiday", "europe", "spain", "france", "italy", "usa",
                 "home", "contents", "house", "pet", "phone", "life insurance", "boiler",
                 "excess", "renewal", "quote", "cheap", "cheaper", "reduce", "price", "cost",
                 "much", "how much", "claim", "sort out", "shop around", "buy", "take out",
                 "arrange", "compare", "cheapest",
                 # other kinds of insurance are their own answers: this key now holds a bare
                 # "insurance", so the ones that are not about a car have to be kept out
                 "income protection", "critical illness", "health insurance", "dental",
                 "private health", "phone insurance", "contents insurance", "business cover",
                 "public liability", "gadget",
                 # "cover" is a cloth over a plant, a roof over a seat and an insurance policy,
                 # and only the last one is this row: "do i need to cover my plants tonight" was
                 # answered with third-party cover by law.
                 "plant", "plants", "garden", "gardens", "allotment", "frost", "fleece",
                 "greenhouse", "cloche", "seedlings", "tender", "shrubs", "vegetables", "veg",
                 "tomatoes", "lawn", "beds", "flower bed", "hanging basket", "outside",
                 "seat", "car seat", "pram", "buggy", "pushchair", "cot", "letting agent",
                 # gap insurance is sold on the finance of a car, not the cover the law wants
                 "gap insurance", "gap cover", "gap protection")),
    # "do i need breakdown cover" reached nothing at all.
    entry("breakdown-cover",
          (("breakdown", "breakdown cover", "recovery", "break down", "broken down"),
           ("need", "worth", "get", "buy", "cost", "much", "how much", "aa", "rac",
            "green flag", "car")),
          ("Worth it if the car is old or you drive far: one recovery is £100 to £200, so cover at "
           "£40 to £80 a year pays for itself the first time the car will not start. Check whether "
           "your bank account, car insurance or a lease already includes it, and keep the number "
           "in the car rather than in your phone.")),

    # --- pay, tax and pensions ---------------------------------------------------
    entry("tax-return", (("tax return", "self assessment", "side income", "side hustle",
                          "sell on ebay", "selling on ebay", "ebay", "vinted", "depop",
                          "selling things online",
                          # "how much tax do i pay on selling online" named no site and no return,
                          # so it matched nothing once the how-to selling row stopped taking it
                          "selling online", "selling stuff online", "selling on marketplace",
                          "tax on selling", "tax on sales", "tax on the selling"),
                         ("need", "do", "register", "deadline", "how", "when", "declare", "owe")),
          ("You can earn up to £1,000 a year from selling or side work before you have to declare "
           "it, which is the trading allowance. Above that, register for Self Assessment by 5 "
           "October after the tax year ends and file online by 31 January; you pay tax on the "
           "profit, not on everything you took."),
          # "how do i sell on vinted" and "where can i sell things online" tie this row, because
          # both name a site and a question shape; the site words are here for the asking-when
          # question, and the how-to is selling-second-hand below.
          avoid=("how do i sell", "how to sell", "how can i sell", "where can i sell",
                 "where do i sell", "how do i get rid of", "how do i sell off",
                 # "how do i get paid when i sell online" is the listing answer, not the allowance
                 "get paid", "paid when", "paid for it", "buyer", "postage", "post it",
                 "scam", "scams", "scammed", "scammer", "overpaid", "safer", "safe", "safely"),
          # "do i need to declare side income" ties with self-assessment-tax's registration
          # answer, which does not mention the trading allowance this line is asking about
          bias=1),
    # Selling a thing and the tax on the selling are two questions: "do i have to declare" is the
    # row above, "how do i sell it" is this one. The verb is the key on one side and the place or
    # the thing on the other, so "how do i sell my old sofa", "where can i sell things" and "how
    # do i sell on vinted" all reach it; a house, a car and shares are sold through their own rows
    # and name none of these words, so they are left alone.
    entry("selling-second-hand",
          (("sell", "selling", "sold", "sell off", "get rid of", "declutter", "decluttering"),
           ("online", "ebay", "vinted", "depop", "gumtree", "marketplace",
            "facebook marketplace", "car boot", "second hand", "secondhand", "stuff", "things",
            "furniture", "sofa", "settee", "wardrobe", "table and chairs", "old clothes",
            "unwanted", "junk", "clutter", "old toys", "baby things")),
          ("Photograph it in daylight against a plain wall, and price it against what the same "
           "thing actually sold for, not what people are asking. Clothes go on Vinted, furniture "
           "and anything heavy on Facebook Marketplace, an odd one-off on eBay as an auction with "
           "a low start. Take cash, or a transfer that has cleared, before it leaves your hands: "
           "a buyer who sends a courier and overpays is the commonest scam there is."),
          # A house, a car, a phone's trade-in value and shares are all other entries' lines, and
          # "sell by" is a date on a packet rather than a verb.
          avoid=("house", "home", "flat", "mortgage", "car", "van", "motorbike", "shares",
                 "investments", "business", "trade in", "trade-in", "sell by", "use by",
                 "use-by", "estate agent", "landlord", "rent out", "phone", "iphone", "handset",
                 "laptop", "console",
                 # The tax on the selling is the row above, and this one took "how much tax do i
                 # pay on selling online" with a photo-and-price answer. Same fence as card-safe-online.
                 "tax", "taxed", "taxes", "taxable", "declare", "declaring", "declaration",
                 "hmrc", "allowance", "trading allowance", "self assessment", "how much tax",
                 "national insurance", "income",
                 # A smell is not a thing to sell: "how do i get rid of damp smell in a
                 # wardrobe" scored this entry on "get rid of" and the word wardrobe, and got a
                 # photograph-it-and-price-it answer. The smell and the damp have their own rows.
                 "smell", "smells", "smelling", "smelly", "damp", "musty", "mould", "mold",
                 "stink", "stinks", "odour", "odor")),
    # Reading a payslip is this entry; a payslip that came out short, wrong or smaller than last
    # month is `work.payslip-short`, which has the advice about what to do about it. The two are
    # split on the question, not on the noun, and every short-side word here is in the avoid so
    # the split holds whichever entry the registry happens to reach first.
    entry("payslip", (("payslip", "pay slip", "pay slips", "payslips", "payslip line",
                       "payslip lines", "take home pay", "net pay",
                       # the money itself, not the slip: "what does take home mean" and "what
                       # is take home" are questions about gross and net, and the payslip row
                       # is where that is explained
                       "take home", "take-home"),
                      # "what does my payslip show" is a television question to a table that keys
                      # on "show", so the question words are keys here and the bias breaks the tie
                      ("read", "reading", "understand", "explain", "mean", "means", "show", "shows",
                      "say", "says", "does", "did", "what", "which", "where", "how", "line",
                      "lines", "code", "deductions", "net", "gross", "hours", "check",
                      # "why is my payslip a different amount every month" is the reading
                      # question, and "why" is the word that says so
                      "why", "different", "amount", "every month", "varies", "fluctuates")),
          ("Three lines cover most of it: gross is what you earned before anything is taken, net is "
           "what lands in the bank, and the difference is tax, national insurance and pension. "
           "Check the tax code against your HMRC coding notice (1257L is the standard one) and the "
           "hours or overtime against your contract; a deduction you did not agree to, or a code "
           "that is not yours, is a question for payroll rather than your manager, and a wrong "
           "code can be backdated."),
          # a payslip that is short, wrong or smaller is the other entry's: it is a different
          # question, with advice about payroll and evidence, and the two must not compete
          avoid=("emergency", "emergency tax", "emergency code",
                 "smaller", "less than", "less than my salary", "short", "short paid", "missing",
                 "wrong", "error", "errors", "mistake", "add up", "doesnt add up",
                 "doesn't add up", "went down", "gone down", "dropped", "shrank", "shrunk",
                 "not what i expected", "not right", "underpaid", "tax code", "tax codes",
                 "coding notice", "tax-code", "p60", "p45", "national insurance number",
                 "how much tax", "tax rate", "overtime", "too much tax", "overpaid tax",
                 # asking for a copy is not reading one: "how do i get a copy of my payslip"
                 # and "where can i find my payslips" were answered with what gross and net
                 # mean, because this row keys the question words as well as the noun
                 "copy", "copies", "old payslips", "older payslips", "past payslips",
                 "replacement", "from a previous job", "from my old job", "find my payslips",
                 "where are my payslips"),
          bias=1, guard=_not_a_customs_line, explain=True),
    # The copies question, not the reading one: where the payslips are kept and who to ask for
    # the ones that are missing. A payslip that came out short is `work.payslip-short`, and the
    # tax code is `tax-code`, so both stand this row down.
    entry("payslip-copy",
          (("payslip", "pay slip", "payslips", "pay slips", "payslip copy", "payslips for a",
            "old payslips", "past payslips"),
           ("copy", "copies", "old", "older", "previous", "past", "find", "where", "get",
            "obtain", "request", "replacement", "lost", "again", "archive", "portal", "email",
            "emailed", "sent", "backdated", "last year", "hmrc", "from 202", "two years ago")),
          "Ask payroll or HR: digital payslips are usually in the HR or payroll portal, and a "
          "paper one is the stub or a PDF they can email. An employer has to keep the record, so "
          "they can give you a copy of any month you are missing, and a former employer's HR can "
          "usually reissue one. HMRC does not hold payslips, but your personal tax account shows "
          "the pay and tax each employer reported.",
          avoid=("wrong", "short", "less than", "smaller", "tax code", "p60", "p45", "gross",
                 "net", "deduction", "deductions", "mean", "means", "read", "reading", "explain",
                 "understand", "overtime", "difference", "add up", "emergency", "underpaid",
                 "overpaid"),
          bias=2),
    entry("tax-code", (("tax code",),
                       ("wrong", "what", "mean", "check", "letter", "number", "change", "right",
                        "correct",
                        # the statement of it, not a question: "my tax code has changed and i
                        # dont know why" was told to register as self-employed
                        "changed", "changes", "changed to", "different", "why", "higher",
                        "lower", "went up", "went down", "dont know why", "don't know why")),
          ("The number in a tax code is your tax-free allowance divided by ten, so the standard "
           "1257L means £12,570 a year tax free — a different number means an adjustment, for a "
           "company benefit, an untaxed job or an unpaid tax bill. Check the breakdown in the HMRC "
           "app and correct it there; if a K is in the code you're paying tax on something you owe "
           "instead."),
          # an emergency code is the new-starter question, answered where it is read (emergency-tax):
          # the allowance-in-code explainer does not say what to do about this month's pay
          avoid=("emergency", "emergency tax", "emergency code"),
          bias=1),
    entry("pension", (("pension", "pensions"),
                      ("workplace", "start", "what", "how", "much", "employer", "worth", "opt out",
                       "save", "check", "guaranteed", "safe", "protected", "at risk", "gone",
                       "early", "take", "taken", "taking", "access", "cash in",
                       "draw", "withdraw", "lump sum", "25%", "quarter",
                       # "im 28 and thinking about a pension" and "ive been looking into a
                       # pension" name no question word at all, and a person at that point wants
                       # the first thing to do rather than the shrug they were getting
                       "thinking about", "thinking of", "thinking", "looking into", "looking at",
                       "no idea", "where do i start", "about a pension", "about pensions",
                       "thinking about a pension", "thinking about my pension")),
          _pension,
          # the shapes the rows below own are answered there, and this one kept taking them
          # because "pension" is all a line has to say to reach it
          avoid=("how much should i pay", "how much should i contribute", "how much to pay in",
                 "how much should i have", "how much does my employer", "how much does the"
                 " employer", "what is a sipp", "sipp", "auto enrolment", "auto-enrolment",
                 "doesnt offer", "doesn't offer", "no pension at work", "never joined",
                 "not joined", "havent joined", "have to pay into")),
    entry("retire-how-much", (("retire", "retirement", "retiring", "pension pot",
                               "take my pension", "draw my pension", "access my pension",
                               "pension age", "state pension",
                               # the adequacy question asked about the pension itself: "is my
                               # pension enough to live on" and "will my pension be enough" were
                               # both handed the free-advice card, while this row - which says
                               # what an income needs to be - was the answer behind it. The
                               # phrases carry the "enough" sense, so the rate-you-pay row keeps
                               # "how much should i pay in".
                               "my pension enough", "pension be enough", "pension enough",
                               "enough to live on", "live on my pension", "live off my pension",
                               "pension do i need", "pension will i need"),
                              ("how much", "enough", "when can i", "when do i", "what age",
                               "how old", "at 55", "at 60", "at 62", "at 65", "need", "afford",
                               "how do i know", "did i save", "realistic", "early", "retire at",
                               "what is",
                               "check", "forecast", "record", "statement", "should i",
                               "keep working", "now or later",
                               "how many years", "years do i need", "voluntary", "buy extra",
                               "extra years", "qualifying", "gap in my record",
                               # "can i retire before 60" is the same question as "at 55"
                               "retire before", "retiring before", "before 60", "before 65",
                               "before i am 60", "before im 60")),
          _retirement,
          bias=1,
          guard=_not_a_gift,
          avoid=("should i opt out", "workplace pension", "employer", "contribution")),
    entry("pension-taking", (("annuity", "annuities", "drawdown", "lump sum", "cash in my pension",
                               "cash in the pension", "take my pension as", "take the 25%",
                               "tax free lump sum", "pension release"),
                              ("should", "can i", "could i", "worth", "better", "what is", "what are",
                               "how", "or", "vs", "explain", "take", "tax", "taxed", "tax-free",
                               "tax free", "recommend", "recommended", "recommendation",
                               "recommendations",
                               # "what does an annuity mean" is the same ask as "what is an
                               # annuity", and the reading calls it one: `understood["asks"]` is
                               # ["definition", "what"]. The row's ask words did not have a
                               # definition word, so the line reached nothing and, after other
                               # pension turns, the chat offered it no card at all.
                               "mean", "means", "meaning", "definition", "explanation")),
          _pension_choice,
          bias=1,
          # "should i pay more in" and the dates questions are other answers, and so is the
          # other kind of lump sum: "should i take a lump sum from my redundancy" is a
          # redundancy question, and it was getting the 25% tax-free answer.
          avoid=("pay into", "pay more in", "contribution", "contributions", "employer", "opt out",
                 "when can i", "how much do i need", "enough to retire",
                 "redundancy", "redundant", "severance", "settlement", "dismissal",
                 "compromise agreement", "notice pay", "holiday pay", "payout")),
    entry("pension-tax", (("pension", "pensions", "pension pot"),
                          ("tax", "taxed", "taxable", "tax free", "tax-free", "how much tax",
                           "tax on it", "taxman")),
          ("You usually get 25% of a defined contribution pot tax-free, capped at about "
           "\u00a3268,275, and every pound after that is taxed as income at whatever rate you are "
           "on when you take it - so a big withdrawal in one year can be taxed at 40% even if you "
           "are a basic-rate taxpayer in a normal year. Take the tax-free cash in stages, or draw "
           "a smaller amount each year, and check the figure before you press the button: providers "
           "will tell you what tax they have to deduct. State pension is taxable too, even though "
           "nothing is taken out of it when it is paid."),
          bias=1,
          avoid=("council tax", "income tax return", "self assessment", "tax code", "tax credits",
                 "capital gains", "inheritance tax", "stamp duty", "vat", "opt out")),
    entry("pension-on-death", (("pension", "pensions", "pension pot"),
                               ("die", "dies", "death", "inheritance", "inherited", "pass on",
                                "passed on", "beneficiary", "beneficiaries", "next of kin")),
          ("A defined contribution pot is usually outside your estate for inheritance tax and "
           "goes to whoever you have nominated, so the nomination form matters more than your will "
           "- check it is up to date, especially after a divorce or a new partner. If you die "
           "before 75 the beneficiaries normally pay no tax on it; after 75 they pay income tax "
           "at their own rate as they take it out. A final salary or workplace scheme usually pays "
           "a spouse's or dependant's pension instead, and often a lump sum, so ask the scheme for "
           "its rules as well."),
          bias=1,
          avoid=("life insurance", "funeral", "cremation", "burial", "state pension", "bereavement",
                 "grief", "sad", "opt out")),
    entry("invest-starter", (("invest", "investing", "index fund", "index funds", "tracker fund",
                               "stocks and shares", "shares", "stock market",
                               # "how do i buy stocks", "where do i buy stocks" and "how do i
                               # invest in stocks" all fell through: the plural was not a key word
                               # at all, and the last of the three was read as a delivery date
                               # because "in stock" is inside "in stocks".
                               "stocks", "buy stocks", "buy a stock", "shares in"),
                              # "small" is not here: "we have a small shared kitchen" is a
                              # flatshare, and a bare small + shares is not an investing line.
                              # A sum named in the line is what an investing question carries.
                              ("start", "little", "first", "how", "much", "£50", "amount",
                               "a bit", "sum", "thousand", "safest",
                               "beginners", "beginner", "safe", "worth", "should", "should i",
                               # "where do i buy stocks" went to the price-comparison card: the
                               # place is the how-to-invest question, so where and buy count
                               "where", "buy", "buying", "bought",
                               "in shares", "in the market")),
          ("Open a stocks and shares ISA and put a set amount a month into a global index tracker, "
           "which spreads the money over hundreds of companies for a fee of around 0.2%. £50 a "
           "month is plenty to start, and the money wants five years or more untouched, because "
           "the value will fall some years and you need the time to ride it out."),
          bias=1,
          # "shares" also reads as the verb "share", so "how do i share a folder / a doc / a
          # spreadsheet / the wifi password" scored investment words and got the index-fund
          # answer. Held as phrases, because "sharing" is itself a loose form of "shares" and
          # would keep "investing in shares" out.
          avoid=("isa limit", "cash isa", "lifetime isa",
                 # A shop's stock is not a market. `in stock` is not here on purpose: the
                 # reading folds the plural, so "how do i invest in stocks" and "is this in
                 # stock" hold the same phrase, and an avoid word on it stood down the very
                 # line this row should answer. The delivery lines are kept out by the words
                 # that only a parcel uses, and by consumer.delivery-promise asking what
                 # "stock" is in the line.
                 "stock cube", "stock cubes", "make stock", "making stock", "homemade stock",
                 "chicken stock", "beef stock", "vegetable stock", "bones", "carcass", "broth",
                 "simmer", "skim", "stockpot", "gravy", "soup", "recipe", "recipes", "cooking",
                 "back in stock", "out of stock", "restock", "restocking",
                 "delivery", "delivered", "arrive", "arrived", "parcel", "courier", "order",
                 "shop", "shops", "supermarket", "shelf",
                 # "job share", "job-sharing" and "share my job" are a work arrangement, not a
                 # stake in a company: work.py's flexible-hours entry answers them
                 "job share", "job-share", "job sharing", "share my job", "share the role",
                 "share a role",
                 "share my", "share a", "share the", "share photos", "to share", "share it",
                 "photos", "photo", "pictures", "screenshots", "files", "folder", "folders",
                 "location", "wifi", "with my family", "with my friends", "with someone",
                 # "pay his share" is a share of a bill, not shares in a company: the split-the-
                 # bill question, and family.lent-money has the asking-for-it-back answer.
                 "his share", "her share", "their share", "my share", "our share",
                 "pay his", "pay her", "pay their", "split the", "divvy", "chip in",
                 "owe me", "owes me")),
    # "should i sell my shares now the markets crashed" was the hazards-and-999 car crash answer
    # and "my shares have gone down should i sell" was the how-to-start-investing answer: a
    # decision about money already in the market is neither of those.
    entry("sell-shares", (("sell", "sold", "selling", "gone down", "went down", "dropped",
                           "fallen", "crash", "crashed", "lost money", "losing money",
                           "should i hold", "hold or sell", "market crashed",
                           "markets crashed", "market has crashed", "markets have crashed",
                           "market fell", "markets fell", "market drop", "markets dropped"),
                          ("shares", "share", "stocks", "my investments", "my investment",
                           "portfolio", "tracker fund", "index fund", "fund", "investments")),
          ("Need the money within three to five years? Then it should not be in shares at all, "
           "and selling now is right. If you do not, a tracker that has fallen is normal - the "
           "global one fell about 20% in 2020 and came back - and selling after the fall is what "
           "makes the loss real. The exception is one big holding, especially your employer: sell "
           "that down whatever the price."),
          # "should i sell my shares" scores 5 on the how-to-start-investing entry through
          # "shares" and "should", and "my shares have gone down should i sell" ties it exactly,
          # so this one needs the nudge as well as the better words.
          bias=3,
          # "sell" is in a lot of lines that own nothing: a house, a car, a phone, a pram.
          avoid=("house", "flat", "car", "van", "phone", "laptop", "ebay", "vinted", "furniture",
                 "wedding dress", "my business", "old")),
    entry("make-a-will", (("make a will", "write a will", "making a will", "will and testament",
                           "intestate", "my will", "a will", "the will", "without a will",
                           "will cost"),
                          ("how", "cost", "need", "without", "do i", "update", "worth",
                           "cheap", "children", "dies", "died", "write", "much",
                           # "i want to make a will" and "who can witness a will" both got a
                           # probe asking what had stopped it, and "do i need a solicitor to
                           # make a will" the estate answer with no mention of a solicitor
                           "want to", "i want", "should i", "who", "witness", "witnesses",
                           "witnessed", "executor", "executors", "solicitor", "diy", "online",
                           "keep", "store", "sign", "signing", "valid", "get one", "sort out",
                           "cheapest", "cheaper", "much does one")),
          # "do i need a will" is the modal neighbour of "i want to make a will", so the answer
          # opens with whether rather than how, and stays to three sentences: at 671 characters
          # it was four sentences and over the style bar for a line that never asked for the
          # paperwork.
          ("Write one as soon as you own a home, have children or are not married to your "
           "partner: without a will the law decides and an unmarried partner gets nothing. A "
           "simple one is a £20 to £35 form signed in front of two witnesses who are not family "
           "and do not inherit, and it needs redoing after a marriage or a divorce because those "
           "cancel it. Pay a solicitor £150 to £400 for a house abroad, a business, a second "
           "marriage or someone who cannot handle money."),
          # "will" is mostly a verb, so only the phrasings people use when they mean the document
          # are keys above; these keep the modal senses out of the estate answer.
          avoid=("will i", "will it", "will my", "will the", "will you", "will we", "will they",
                 "will she", "will he", "i will", "when will", "how long will", "who will",
                 "what will", "it will", "that will", "will this", "will that",
                 "keep trying", "keep going", "keeps happening", "kept", "sign up", "sign in",
                 "sign a contract", "sign the contract", "sign this")),

    # --- everyday money ----------------------------------------------------------
    entry("freelance-rate", (("freelance", "freelancing", "self employed", "contract rate"),
                            ("price", "rate", "charge", "much", "first", "quote", "set",
                             "day")),
          ("Work out what you need to earn in a year, divide it by the roughly 220 days you can "
           "actually bill, and add about a third for tax, holiday and quiet months: that is your "
           "floor, not your target. Quote per project but work from that day rate, and ask for a "
           "third up front on anything that takes more than a week.")),
    # Tipping is lifeadmin.tipping: one entry for the trade, not a copy here.
    entry("lend-family", (("lend", "lending", "lend money", "borrow money to"),
                          ("family", "brother", "sister", "friend", "son", "daughter", "mum",
                           "dad", "mate", "parents")),
          ("Only lend what you could afford to lose, and say the amount and a date out loud "
           "before any money moves: \"I can do £500, back by March.\" If it's for something "
           "essential like a car, a short written note or a standing order saves the friendship "
           "later.")),
    entry("owe-family", (("owe", "owes", "owe money", "borrowed from",
                          "pay back", "paying back", "pay her back", "pay him back",
                          "pay them back", "pay my sister", "pay my mum", "pay my dad",
                          # "how do i pay my brother back" puts the person inside the phrase, so
                          # neither "pay back" nor "brother" was found and the line got the shrug
                          "pay my brother", "pay my parents", "pay my friend", "pay my mate",
                          "pay back my", "pay back the money", "pay it back to"),
                         ("sister", "brother", "mum", "dad", "mother", "father", "parents",
                          "friend", "mate", "son", "daughter", "family", "in law")),
          _the_debt_answer,
          # Being owed money is the other way round and has its own answer in family.lent-money.
          # Asking for it back is that same question written as a job: "how do i ask a friend to
          # pay back money" carries "pay back" and "friend", the same two words this entry keys,
          # and it was answered with the borrower's script. The asking words are the tell, and
          # family.lent-money has the chasing answer.
          avoid=("owes me", "owe me", "lent", "lend him", "lend her", "can i get it back",
                 "ask a friend", "ask my friend", "ask a mate", "ask my mate", "ask him to",
                 "ask her to", "ask them to", "ask for it back", "ask for the money",
                 "to pay me back", "won't pay", "wont pay", "never pays", "hasn't paid",
                 "hasnt paid", "remind them", "remind him", "remind her", "chase",
                 # asking to borrow is the other side of the same debt and the other row: this
                 # script explains the debt and offers a date, which is what a person says when
                 # they already owe, not when they are plucking up the nerve to ask
                 "how do i borrow", "can i borrow", "could i borrow", "want to borrow",
                 "borrow off", "borrowed off", "borrowing off", "ask to borrow", "lend me")),
    # A break from paying is the lender's to grant, and it has a cost the person has to be told
    # about. Nothing answered it: "how do i get a payment holiday on my loan" was given the 5.6
    # weeks of annual leave (work.holiday-entitlement counted the word "holiday"), and "can i
    # pause my mortgage payments" reached nobody and got the name of a free advice line.
    entry("payment-holiday",
          (# the scheme's own names first, then the plain verbs people use for it
           ("payment holiday", "payment break", "payment pause", "holiday from payments",
            "holiday from my payments", "holiday on my loan", "holiday on my mortgage",
            "holiday on my credit card", "pause", "pausing", "paused", "put on hold",
            # "skip", "reduce" and "lower" are the plain verbs, and they are safe on this side
            # only because the second group has to name the money: "can i skip a credit card
            # payment this month" and "can i reduce my mortgage payments" both reached nobody.
            "skip a payment", "skip payments", "skip a month", "skip the payment",
            "skip", "skipping", "skipped",
            "defer", "deferring", "deferred", "deferral", "take a break", "break from paying",
            "break from payments", "reduce my payments", "lower my payments",
            "reduce", "reducing", "lower", "lowering", "temporarily reduce",
            "interest only", "switch to interest only",
            "spread the payments", "extend the term"),
           # and the money it is a holiday from, so "pause" alone is never this row. "rent" is
           # not here: a rent a person wants lowered is the landlord conversation, not a
           # payment holiday.
           ("mortgage", "mortgages", "remortgage", "loan", "loans", "credit card",
            "credit cards", "overdraft", "repayment", "repayments", "repaying",
            "car finance", "finance", "hire purchase", "debt", "debts", "lender", "bank",
            "payments", "payment")),
          ("Ask the lender before you miss a payment, not after: ring or write, say what has "
           "changed and what you can afford, and ask for a payment holiday, a switch to "
           "interest-only for a while, or a longer term - mortgage lenders have to offer one of "
           "those. Get their agreement in writing. Interest usually keeps building during the "
           "break and is added to the balance, and a holiday can be marked on your credit file, "
           "so ask what it costs first; for a card or a loan, a payment plan is often cheaper "
           "than a holiday."),
          # Money that has already gone wrong is the arrears and payment-plan answer, which is a
          # different script: this row is the ask made before the payment is missed.
          avoid=("cant pay", "cannot pay", "can't pay", "cant afford", "cannot afford",
                 "behind on", "missed a payment", "missed payments", "already missed",
                 "arrears", "default", "defaulted", "bailiff", "evict", "nothing left"),
          bias=1),
    entry("cant-pay", (("owe money", "owe a lot", "owe thousands", "cant pay", "cannot pay",
                        "maxed out", "maxed", "at the limit", "to the limit", "over the limit",
                        "at my limit", "card is full",
                        # "i cant afford my electricity bill" is the same trouble as "i cant
                        # pay it", and it was a sympathy line and nothing else
                        "cant afford", "cannot afford", "can't afford", "afford",
                        "behind on", "nothing left",
                        "struggling to pay", "arrears", "defaulted", "missed a payment",
                        "a way out", "no way out", "cant see a way", "overwhelmed by")
                       # the same report without the "cant": "i havent paid my phone bill" and
                       # "i havent paid my broadband" were both a nod, and the bill is named.
                       + NOT_PAID,
                       ("money", "pay", "back", "rent", "bill", "council", "catalogue", "loan",
                        "debt", "tax", "card",
                        # the bill a person names is often the whole noun: "i cant afford my
                        # electric", "my gas", "the water"
                        "electric", "electricity", "energy", "gas", "water", "phone",
                        "mobile", "broadband", "wifi",
                        # "i'm at my limit every month" says the money is the month, not a card:
                        # without these the row scored three on the phrase alone and the echo
                        # answered. A carer at the end of their tether still matches no group
                        # two word, so "i'm at my limit with my toddler" stays out.
                        "month", "monthly", "every month", "each month", "a month")),
          ("Tell the person or company what you can pay and when, even if it is £10 a "
           "month - a payment plan beats silence, so say it before it snows. Rent, council tax "
           "and energy come before credit cards, and a maxed-out card wants the minimum paid on "
           "the day every month. A free service like StepChange or National Debtline will write "
           "to everyone for you."),
          # Someone working out how to clear a balance is not someone who cannot pay this month:
          # that is the debt-order and overpay question, and it has its own answer.
          # Someone who *can* afford it is working out what to do with the money, not telling
          # you they cannot pay: "i can afford 200 a month towards my debt" wants the order.
          avoid=("pay it off", "pay off", "in one go", "lump sum", "clear it", "which debt",
                 # a device that is failing is not a debt question, even when the line says
                 # what a replacement costs: "my phone battery drains and i cant afford 80
                 # quid" is the battery tip, and it was told to ring the company and pay
                 # what it can
                 "battery", "batteries", "charger", "charging", "drains", "draining",
                 "drained",
                 # Borrowing or saving *to* afford something is a budget question, not this
                 # one: "should i take out a loan to afford a car" is asking the car budget for
                 # a number, and it was told to ring the company and say what it can pay.
                 "to afford",
                 "first", "overpay", "worth it", "can afford", "could afford",
                 "can i afford", "i can afford",
                 # A storage card that is full is a phone or a camera with no room left, not a
                 # credit card at its limit. "my sd card is full" was told to ring the company
                 # and offer a payment plan, and the same words cover a sim, a memory card and
                 # a camera's own card.
                 "sd card", "sdcard", "micro sd", "microsd", "memory card", "storage card",
                 "flash card", "sim card", "data card", "card is full of",
                 "full of photos", "full of videos", "full of pictures"),
          # "how much rent can we afford on one wage" is a plan for a move and was answered by
          # this card's "ring the company and offer a payment plan": see
          # _a_figure_for_a_plan_is_not_a_debt.
          guard=_a_figure_for_a_plan_is_not_a_debt,
          bias=1),
    # A sum that has to last, and the shopping order that makes it last. The savings card was
    # answering "i have 50 pound to last us a week" ("For £50: one month at £50 a month") and the
    # eight cheap foods were only reachable when the line happened to say "skint".
    # The gate is a word about money: "what to feed my family this week" and "how do i get a stain
    # out that has lasted a week" both carry a "last" phrase and an eating or week word, and
    # neither has a sum in it. Every line this row answers names one, or says there is none.
    entry("money-to-last", (MAKE_IT_LAST, MONEY_TO_COVER), _money_to_last, bias=2,
          ask=("pound", "pounds", "quid", "money", "cash", "budget", "tenner", "fiver", "skint",
               "cheap", "cheapest", "food", "£"),
          avoid=NOT_SPENT_ON_FOOD + ANOTHER_CURRENCY,
          # "i have no money this month" says a month and no sum: there is nothing to divide up,
          # and the two calls that free up cash are the answer. "i have no money" on its own is
          # the food bank, and "i have 200 pound to last the month" is the plan, so the month
          # only stands this row down when the line names no sum at all.
          guard=_a_month_and_no_sum),
    entry("food-bill", (("food bill", "food shop", "grocery bill", "supermarket shop",
                         # a supermarket is a food shop: "i spend too much at the supermarket"
                         # fell between this row and the overspending one (which keeps food
                         # off its own line) and reached nobody.
                         "supermarket", "supermarkets",
                         # "how do i spend less on groceries" was a shrug: the plural is how
                         # people say the weekly shop
                         "groceries", "grocery", "groceries bill",
                         "food shopping", "monthly shop", "food budget", "week for food",
                         "a week on food", "food",
                         # feeding a household is the food bill when a figure is asked for:
                         # "how much does it cost to feed a family of four" is the going rate,
                         # and the live-price row was answering it with "I can't look up live
                         # prices". A "how do i feed" line is the cooking, not this row.
                         "feed a family", "feeding a family", "feed the family",
                         "feeding the family", "feed us", "feeding us", "feed four",
                         "feed five", "family of four", "family of five", "family of 6"),
                        ("cut", "reduce", "cheaper", "cheapest", "save", "lower", "much",
                         "halve", "week", "budget", "spend", "feed", "cost", "costs")),
          _food_bill,
          # "food" is in the key, so "what foods lower cholesterol" was a tie this entry won on
          # bias: a word about what to eat for a health reason is somebody else's question.
          # "feed" is in this key for "how much a week do i spend feeding us", and it also caught
          # "should i feed my cat wet or dry food", which is the pets domain's question.
          avoid=("hiking", "camping", "walk", "walking", "trip", "backpacking", "picnic",
                 "cholesterol", "saturated", "statins", "statin", "ldl", "triglycerides",
                 "blood pressure", "blood sugar", "diabetes", "diabetic",
                 "my diet", "anti inflammatory", "antioxidant", "vitamins", "protein",
                 "iron rich", "fibre", "calories in",
                 "cat", "cats", "kitten", "dog", "dogs", "puppy", "pet", "pets"),
          bias=1),
    # Leasing, PCP and a loan against buying are a choice, not a fault: what people want decided
    # is which way the money goes over the years they will actually keep the car. Cars' domain
    # says a line about buying or financing a car is not a fault to mend, and shopping owns the
    # used-car checklist, so the choice itself lives here.
    entry("car-lease-or-buy",
          (("lease", "leasing", "leased", "pcp", "contract hire", "personal contract purchase",
            "hire purchase", "car finance", "finance a car", "on finance", "finance",
            "car loan", "loan for a car", "outright", "pay monthly",
            # "should i lease or buy a car" was reaching the contract-checking entry, because
            # "should i" and "car" both scored and this entry's "lease" only scored two
            "lease or buy", "buy or lease", "lease or buy a car", "lease versus buy"),
           ("car", "van", "buy", "buying", "better", "worth", "cheaper", "monthly", "instead",
            "decide", "choose", "should", "new car", "used car")),
          ("Buy a three- or four-year-old car with a loan if you keep cars five years or more: "
           "£12,000 over five years at 7% is about £240 a month, and at the end it is yours and "
           "still worth £4,000. Lease or PCP only wins if you want a new car every two or three "
           "years and drive under the mileage cap. Compare the total cost, not the monthly: "
           "deposit, payments, any final balloon and the excess-mileage charge."),
          # The standing charges, the faults and the shopping checklist all belong to other
          # entries: a lease line is not an insurance quote, a repair, or a used-car inspection.
          avoid=("insurance", "insure", "quote", "premium", "mot", "repair", "repairs", "fix",
                 "broken", "servicing", "service", "petrol", "diesel", "fuel", "electric",
                 "charging", "tyres", "tyre", "puncture", "battery", "clutch", "brakes",
                 "warning light", "breakdown", "parking", "accident", "sell", "selling",
                 "part exchange", "check", "inspector", "inspection", "test drive", "mileage gap",
                 "van hire", "hire a van", "hire cost",
                 # "how much does it cost to lease a car" is the price of one deal, and the
                 # running-cost answer has the yearly figure for a car you own.
                 "how much does it cost",
                 # Getting out of a deal is its own problem with its own figures (settlement,
                 # voluntary termination, remaining payments), not the choice of how to pay.
                 "get out", "getting out", "cancel", "cancelling", "cancel my", "terminate",
                 "termination", "settlement", "voluntary", "end my", "end the deal",
                 "missed payment", "missed a payment", "arrears", "hand it back early"),
          guard=_a_car_or_a_deal),
    entry("car-running-costs", (("car", "cost to run", "costs to run", "run a car",
                                 "running a car", "cost of running a car"),
                                ("cost", "costs", "runs", "running", "monthly", "afford", "budget",
                                 "expensive", "year", "keep")),
          _car_running_cost,
          # "my car needs a new clutch" / "i cant afford it" is a repair the person cannot pay
          # for, not a shopping comparison.
          avoid=("drive", "parking", "test", "cant afford", "can't afford", "cannot afford",
                 "afford it", "afford the", "afford a repair", "needs a new", "needs new",
                 "broken", "repair", "fix",
                 # A car that will not start is a fault, not a yearly cost to weigh up.
                 "battery", "going flat", "wont start", "won't start", "breakdown", "tyre",
                 # "my car alarm keeps going off" is a fault on the car, not a year of running
                 # costs: the absent "cost" words are not enough, because the row keys on "car".
                 "alarm",
                 # "how much does it cost to run the heating" was priced as a used car
                 "heating", "boiler", "radiator", "radiators", "hot water", "electric heater",
                 "heat pump",
                 # ... and so was "how much does a bath cost to run": the bath and the shower
                 # are rows of the house's own running-cost table now, and a car is not one.
                 "bath", "baths", "bathtub", "shower", "showers", "showering",
                 # "how much does it cost to run a hair dryer" was the third one. A hair dryer
                 # is the only appliance the house's table has no row for, so it gets the honest
                 # shrug rather than a car - and a tumble dryer is not a hair dryer.
                 "hair dryer", "hair drier", "hairdryer", "hair dryers",
                 "tyres", "warning light", "engine light", "overheating", "clutch", "brakes",
                 # "it's 680 this year, was 450 last year" is a renewal that has already gone up,
                 # not a budget for buying and running a car.
                 "renewal", "renew", "quote", "quotes", "premium", "premiums",
                 "this year", "last year", "went up",
                 # "my car bluetooth keeps disconnecting from my phone" is a pairing fault that
                 # happens to share the word "car" and a "keeps": the stereo answer is the one
                 # that has the steps in it, so this entry steps back and lets it through.
                 "bluetooth", "pair", "pairing", "connect", "connecting", "connection",
                 "disconnect", "disconnected", "disconnecting", "carplay", "android auto",
                 "stereo", "head unit", "speaker",
                 # "my car fan keeps running after i switch off" is the cooling fan doing its
                 # job, not a yearly cost to weigh up: cars.py has the fan's own answer.
                 "fan", "fans", "radiator fan",
                 # "i keep water bottles in the car" says what is in the car, not what it costs
                 # to run one: "keep" is one of the ask words here, so a bottle of water had the
                 # yearly budget for a used car. The row stands down for the things people keep
                 # in a car rather than ask the price of running it.
                 "bottle", "bottles", "water bottle", "water bottles", "flask", "thermos",
                 "glovebox", "glove box", "in the boot", "in the glovebox", "in the back seat",
                 "back seat", "car seat",
                 # "how do i keep kids busy in the car" is a journey, and the "keep" of "cost to
                 # keep a car" was enough to price it as a running cost - the child and the
                 # activity in the same line mean travel's car-journey-kids answers it. Phrases,
                 # so a plain "what does it cost to keep a car" keeps this card.
                 "keep kids", "keep the kids", "kids busy", "kids occupied", "keep them busy",
                 "keep them occupied", "entertain the kids", "entertain the children",
                 "entertain the kids", "bored in the car", "busy in the car", "long drive",
                 "long journey", "road trip",
                 # "a long car journey" is not the phrase "long journey", and "keep a toddler
                 # busy" is not "keep kids": the child word next to the activity is what makes
                 # the line a journey, wherever it sits in the sentence.
                 "long car", "in the car", "on the plane", "on a plane", "on the train",
                 "on a train", "on the ferry", "on a ferry", "on the flight", "on a flight",
                 "keep a toddler", "toddler busy", "toddler occupied", "keep a baby",
                 "baby busy", "keep a child", "child busy", "children busy", "kid busy",
                 "keep them amused", "keep them entertained")),
    entry("warranty-rights", (("extended warranty", "warranty", "warranties", "guarantee",
                                "guarantees"),
                               ("worth", "buy", "get", "claim", "claiming", "how do i", "cover",
                                "covered", "broken", "faulty", "stopped working", "washing machine",
                                "appliance", "offer", "run out", "expired")),
          ("Go back to the shop you bought it from with the receipt: the retailer owes you a "
           "repair, replacement or refund for up to six years in England and Wales, and a "
           "guarantee is in addition to that right, not instead of it. Buying an extended "
           "warranty is usually not worth it, since those rights already cover the appliance, and "
           "paying by credit card makes the card company jointly liable over £100 under Section "
           "75. A guarantee covers a fault, not damage: a cracked screen or a dropped phone is an "
           "insurance claim."),
          # "how do i claim on a warranty" was reaching the tax answer by its bare "claim"
          ask=("warranty", "warranties", "guarantee", "guarantees", "extended"),
          # "does my warranty cover a cracked screen" is the cracked-panel answer, which names
          # the price where a repair turns into a replacement
          avoid=("cracked", "crack", "screen", "screens", "panel", "dropped", "smash",
                 "smashed", "water damage", "liquid damage")),
    entry("refund", (("refund", "refunds", "return", "money back"),
                     ("shop", "item", "faulty", "entitled", "bought", "order", "online", "sale",
                      "get", "claim", "ask for", "request", "how do i", "can i")),
          ("For anything faulty you're entitled to a full refund within 30 days of buying it, and "
           "after that to a repair or replacement. Online orders can go back within 14 days of "
           "delivery for any reason if they're unused; in a shop, a change of mind is the shop's "
           "policy, not the law."),
          # a reduced item is lifeadmin's sale-refund, which names the price paid: the general
          # 30-day answer would be true but would miss what the person asked.
          # a tax return is filed, not refunded: the tax answers own those lines
          # an app or a subscription is bought from a store, and the store's own rules
          # decide: technology's app-refund has the steps for that
          # A cancelled flight is a travel question: "how do i claim a refund for a cancelled
          # flight" was getting the 30-day faulty-goods law, which has nothing to do with it.
          avoid=("sale", "sales", "reduced", "clearance", "discount", "bargain", "half price",
                 # asking for the words is wording.ask-for-refund's: "what should i write to ask
                 # for a refund" got the 30-day law, which answers the right and not the letter
                 "what should i write", "what do i write", "what to write", "what do i say",
                 "what to say", "how do i word", "write to ask", "a message asking", "draft",
                 "wording", "letter", "email to",
                 "tax return", "tax returns", "self assessment", "hmrc", "p60", "p800",
                 "tax code",
                 # "how do i claim a tax refund" and "how do i claim a refund of overpaid tax"
                 # were the shop's 30-day law: a tax refund is a different claim entirely, and
                 # the P800/P87 row is the one that answers it.
                 "tax refund", "tax refunds", "refund of tax", "refund of overpaid tax",
                 "tax rebate", "overpaid tax", "overpayment of tax", "income tax",
                 # a fee the bank charged is not faulty goods: "can i ask my bank to refund a
                 # late fee" got the 30-day shop law, and the missed-payment row has the ask.
                 "late fee", "late fees", "late charge", "late payment fee", "late payment charge",
                 "bank charge", "bank charges", "overdraft fee", "overdraft charge",
                 "penalty charge", "penalty fare", "interest charge", "default fee", "arrears fee",
                 # money back on a booking follows the cancellation, not the 30-day law on
                 # goods: "how do i get a refund on a booking" was this answer
                 "booking", "bookings", "reservation", "reservations", "booked",
                 # money that someone took is the bank's question, not the shop's
                 "scam", "scams", "scammed", "fraud", "fraudulent", "conned", "ripped off",
                 "push payment",
                 "app", "apps", "apple", "itunes", "google play", "play store", "app store",
                 "subscription", "in app purchase",
                 "flight", "flights", "airline", "airlines", "plane", "airport", "holiday",
                 "package holiday", "hotel", "train", "trains", "rail", "railway", "coach",
                 "bus", "ferry", "cruise", "concert", "ticket", "tickets",
                 # a show ticket is the ticket entry's: "i can't go to the gig can i get my
                 # money back" was answered with the 30-day faulty-goods law.
                 "gig", "gigs", "festival", "theatre", "theater", "cinema", "match", "stadium",
                 "comedy", "musical", "opera", "ballet", "event", "show", "refund policy",
                 # a journey that went wrong is Delay Repay, and a parcel that never came is
                 # the missing-order answer: both name a refund and neither is the shop rule
                 "tube", "parcel", "parcels", "delivery", "delivered", "courier", "evri",
                 "royal mail",
                 # the council refunds an overpaid bill its own way, and a tax rebate is not a
                 # shop return either
                 "council tax", "council", "rebate", "hmrc rebate",
                 # a deposit is money held, not goods sold: "can i get my money back from a
                 # deposit scheme" was the shop's 30-day law, and the deposit's answer is the
                 # itemised deductions and the protection scheme's dispute service.
                 "deposit scheme", "deposit protection", "tenancy deposit", "holding deposit",
                 "security deposit", "my deposit", "the deposit", "deposit back",
                 "deposit returned", "get the deposit",
                 # a person who did work is a service, not a thing bought: "how do i get my
                 # money back from a builder" is the complaint letter and the small claim, and
                 # the shop's 30-day rule is the wrong answer even when it names money back.
                 "builder", "builders", "plumber", "plumbers", "electrician", "electricians",
                 "roofer", "roofers", "decorator", "decorators", "contractor", "contractors",
                 "tradesman", "tradesmen", "workman", "workmen", "plasterer", "joiner",
                 "tiler", "landscaper", "gardener", "mechanic", "garage",
                 # a credit balance on a utility account is refunded by the utility, not by
                 # the shop's 30-day rule: "can i get a refund from my energy supplier" was
                 # getting the faulty-goods law
                 "energy", "energy supplier", "energy company", "energy bill", "gas bill",
                 "electricity bill", "supplier", "water bill", "credit balance", "in credit",
                 "overpaid", "overcharged",
                 # a tax refund is claimed from HMRC, so the 30-day faulty-goods answer is the
                 # wrong law: "how do i claim a tax refund" was getting it, because "refund" and
                 # "claim" are this entry's keys
                 "tax refund", "tax refunds", "tax rebate", "tax rebates", "overpaid tax",
                 # money back from a site that took it is a card chargeback, not a repair
                 "scam", "scammed", "scam website", "scam site", "fake website", "fraud",
                 "fraudulent", "took my money",
                 # a bank charge is refunded by asking the bank, not by the faulty-goods
                 # route: "how do i get an overdraft fee refunded" was this card, because
                 # "refund" and "get" are its keys
                 "bank charge", "bank charges", "bank fee", "bank fees", "overdraft",
                 "overdraft fee", "overdraft fees", "overdraft charge", "unarranged overdraft",
                 "account fee", "packaged account"),
          # the avoid list above cannot do this job: a "without a receipt" clause is emptied by
          # the reading before any avoid word is tested, so the line arrives here as a plain
          # "how do i return something" and no word of it is left to stand the row down.
          guard=lambda u: not _a_receipt_question(u),
          bias=2),
    # Two everyday banking questions nothing answered: what each kind of regular payment is, and
    # what to do when a card payment goes wrong. Both are the ordinary careful advice, with the
    # escalation named, because "they said no" is the point where people stop.
    # "is it cheaper to pay my energy bill by direct debit" was the hours-of-use answer, and
    # "cheapest way to pay my energy bill" the dinner split: both name a bill and a way of
    # paying, and neither is about how the money leaves the account. A bill word and a paying
    # word are the whole key, so a plain "how do i split the bill" stays with the table.
    # The other half of the bill question: not how to pay it, but what to do when the money is
    # not there. "i cant afford my energy bill" was a feelings line ("what would make today a bit
    # easier"), "help with my energy bill" was the heating-where-you-sit answer, "i cant afford to
    # heat my house" was the mortgage-affordability answer, "will my energy be cut off" was a
    # shrug and "what happens if i dont pay my energy bill" was the cheapest-way-to-pay answer.
    # Those five are one situation, so they are one entry: the ask for help, in the words people
    # use for it, with the schemes named because nobody knows what to ask for.
    entry("cant-afford-a-bill",
          (("cant afford", "can't afford", "cannot afford", "afford", "help paying",
            "help to pay", "help with paying", "help with", "need help", "wants help",
            "cant pay", "can't pay", "cannot pay",
            "dont pay", "don't pay", "didnt pay", "didn't pay", "not paying", "missed a payment",
            "behind on", "instalments", "instalment", "payment plan", "cut off",
            "disconnected", "warm home discount", "hardship fund", "struggling to pay",
            "struggling with",
            # "will they cut me off if i dont pay my electric" was the fuse-box card ("which
            # switch is down before you reset it"), because the line says "cut me off" rather
            # than "cut off" and "electric" rather than "electricity". Stopping is the same
            # situation said the other way round, and it was the cheapest-way-to-pay answer.
            "cut me off", "cut us off", "cut you off", "switch me off", "disconnect me",
            "stop paying", "stopped paying", "not paid", "havent paid", "haven't paid",
            "defaulting", "defaulted"),
           ("energy bill", "gas bill", "electricity bill", "electric bill", "water bill",
            "fuel bill", "heating bill", "energy", "gas", "electricity", "electric", "leccy",
            "water", "heating", "heat", "fuel", "bill", "bills", "meter", "supplier",
            "discount", "grant", "grants", "allowance")),
          PAID_AND_CUT_OFF_REPLY,
          # A bill that is too high, a tariff to change and the way the money leaves the account
          # are three other answers, and each names the same bill.
          avoid=("too high", "too much", "went up", "gone up", "getting higher", "lower",
                 "reduce", "bring down", "save", "saving", "savings", "cheaper", "cheapest",
                 "switch", "switching", "tariff", "tariffs", "deal", "fixed rate", "quote",
                 "compare", "direct debit", "standing order", "estimated", "meter reading",
                 "smart meter", "submit a reading", "how do i pay", "ways to pay",
                 "spread it", "over the year", "budget", "boiler", "new boiler", "repair",
                 "council tax", "rent", "water meter", "free meter", "combi",
                 # a phone, broadband or insurance bill has no Warm Home Discount and no
                 # priority register, so the energy help is the wrong answer to give back
                 "phone", "mobile", "broadband", "internet", "tv licence", "insurance",
                 "loan", "credit card", "catalogue", "overdraft", "childcare", "vet"),
          bias=1),
    # "will i be cut off if i stop paying" names no bill and no fuel, so the row above - which
    # needs an energy word in its second key - could not see it, and the line was the punt. What
    # is being paid is understood, so this row asks only that the line is about paying and about
    # being cut off, and it gives the same answer from the same words.
    entry("stopping-paying",
          (("cut off", "be cut off", "get cut off", "cut me off", "cut us off", "switch me off",
            "switch off my", "disconnect me", "disconnected", "stop paying", "stopped paying",
            "stop paying my", "not paying", "not paid", "havent paid", "haven't paid",
            "havnt paid", "havent payed", "never paid", "defaulted", "defaulting",
            "missed a payment"),
           ("paying", "pay", "paid", "payment", "payments", "bill", "bills", "money", "owe",
            "owes", "arrears", "supplier", "direct debit", "account", "monthly")),
          PAID_AND_CUT_OFF_REPLY,
          # "paid" on its own is not a bill: what has not been paid has to be something a
          # supplier supplies, or the line has to say the supply stopped.
          guard=_a_bill_and_not_a_person,
          # Everything below is a bill somebody can stop paying that is not an energy bill, and
          # each one has an answer of its own: a loan, a pension, a phone, the rent, the council.
          avoid=("pension", "savings", "mortgage", "rent", "landlord", "council tax", "tax",
                 "fine", "fines", "parking", "phone", "mobile", "broadband", "internet",
                 "netflix", "subscription", "subscriptions", "gym", "insurance", "loan",
                 "credit card", "catalogue", "overdraft", "child maintenance", "childcare",
                 "vet", "school", "club", "tv licence", "car", "car insurance",
                 "garden waste", "water meter", "standing order", "stamp duty"),
          bias=1),
    entry("paying-a-bill",
          (("energy bill", "gas bill", "electricity bill", "water bill", "utility bill",
            "utility bills", "my bill", "my bills", "bills are", "direct debit",
            "direct-debit", "prepayment meter", "prepay meter",
            # "cheapest way to pay my gas and electricity" names the two fuels and no bill at
            # all, which is how most people say it out loud. The "or" shapes are not here: "is
            # gas cheaper than electricity" and "is it cheaper to heat with gas or electricity"
            # are the heating-fuel row in home.py, and holding them in this key took the
            # way-to-pay answer to a question about which fuel is cheaper.
            "gas and electricity", "gas and electric", "electric and gas", "electricity and gas"),
           ("pay", "pays", "paying", "payment", "payments", "cheaper", "cheapest", "better",
            "monthly", "weekly", "fortnightly", "instalments", "instalment", "spread",
            "over the year", "payment plan",
            # "electric and gas cheapest way to pay" was the split-the-bill answer: the phrase
            # is what separates paying a supplier from dividing a restaurant bill.
            "way to pay", "ways to pay", "way of paying", "ways of paying")),
          "Paying by direct debit is the cheapest way for most people: suppliers charge less "
          "for it than for cash, card or a prepayment meter, and the Direct Debit Guarantee "
          "means a wrong amount has to be refunded in full and straight away. If the monthly "
          "figure is more than you can manage, ring and ask them to spread the year's use over "
          "twelve months rather than ten, or to move the date to just after payday. Behind on "
          "it, ask for a payment plan you can keep up rather than one big catch-up figure, and "
          "ask what you are owed: the priority services register if you are disabled, ill or "
          "caring for a young child, and the discount schemes for low incomes.",
          # A cheaper tariff is the switching question, and a wrong bill is money's complaint
          # line; a table bill is the split, and the rent or the council tax are their own.
          # The bill a person keeps forgetting, or pays late, is the payment-date card's line: the
          # cheapest way to pay is not what they asked, and "i forgot to pay my energy bill" was
          # answered with the tariff explainer.
          avoid=("forget", "forgets", "forgetting", "forgot", "forgotten", "keep forgetting",
                 "keeps forgetting", "late paying", "paid late", "on time", "missed a payment",
                 "switch", "switching", "tariff", "tariffs", "which supplier", "fixed deal",
                 "standing charge", "meter reading", "smart meter", "wrong", "mistake",
                 "overcharged", "refund", "split", "who pays", "tip", "rent", "council tax",
                 "tax", "phone", "mobile", "broadband", "tv licence", "insurance", "loan",
                 "credit card", "overdraft", "standing order", "difference",
                 # a bill that is too high or that went up is the saving question, not this one
                 # which fuel is cheaper is the heating-fuel row's question, in either word order
                 "gas or electricity", "electricity or gas", "gas or electric", "electric or gas",
                 "cheaper to heat", "cheaper than gas", "cheaper than electricity",
                 "which is cheaper", "heat with gas", "heat with electricity",
                 "too high", "too much", "went up", "gone up", "estimated", "lower",
                 "reduce", "save", "saving",
                 # someone who cannot pay is cant-afford-a-bill's question, not the cheapest way
                 # to pay, and an instalment ask is the plan rather than the method
                 "instalments", "instalment", "payment plan",
                 "cant pay", "can't pay", "cannot pay", "not pay", "cant afford",
                 "can't afford", "cannot afford", "afford", "behind on", "arrears",
                 "debt", "debts", "struggling", "cut off"),
          bias=2),
    # --- missing a payment -------------------------------------------------------
    # "i forgot to pay my credit card bill" was the Apple Pay answer, "i missed a credit card
    # payment" was the lost-card one, "i keep forgetting to pay my rent" was the reading-memory
    # one, and "how do i stop missing payments" was a shrug. Nothing answered the thing itself:
    # the payment that goes out on its own, the reminder, and what one late payment costs.
    entry("pay-on-time",
          # The subject is the payment and the second part is the forgetting, in that order:
          # with "keep forgetting" as the subject, "i keep forgetting to water the plants" and
          # "i keep forgetting to charge my phone" were both answered with a direct debit, and
          # the watering answer and the charger answer are the right ones for those.
          (("bill", "bills", "card", "credit card", "debit card", "payment", "payments",
            "pay", "pays", "paying", "rent", "mortgage", "loan", "council tax", "tv licence",
            "due date", "direct debit", "standing order", "minimum payment", "store card",
            "catalogue", "utilities", "utility bill", "energy bill", "phone bill", "water bill"),
           ("forget", "forgets", "forgetting", "forgot", "forgotten", "keep forgetting",
            "keeps forgetting", "always", "late", "miss", "missed", "missing", "on time",
            "reminder", "remind", "reminded", "overdue", "every month", "each month",
            "monthly", "due", "slip my mind", "slipped my mind", "slipped my head")),
          # The reply has to fit a rent or a council tax as well as a card: it named the bank and
          # a card's capped fee on every bill, which is wrong about someone behind on their rent.
          "Set it to go out on its own and it stops being something you can forget: a direct "
          "debit or standing order, taken the day after payday rather than on the due date, so the "
          "money is there before it is wanted. A phone reminder a week before catches the rest, "
          "and anything you pay by hand is worth a calendar entry every month. If you have missed "
          "one, pay it the same day and ring them: most will move the date, waive the first late "
          "fee or set up a payment plan if you ask before it goes further, and one payment a few "
          "days late matters far less than a run of them. Then check the statement or the account "
          "once a month, because a missed payment shows there first.",
          # A bill you cannot afford is a debt question and a disputed one is the letter's; what
          # this answers is forgetting, lateness, and the payment that runs itself.
          avoid=("cant pay", "can't pay", "cannot pay", "cant afford", "can't afford",
                 "cannot afford", "afford", "struggling", "behind on", "arrears", "summons",
                 "court", "bailiff", "letter", "dispute", "wrong bill", "overcharged", "refund",
                 "chargeback", "says i owe", "how much", "which credit card", "best credit card",
                 "worth it", "interest rate", "apr", "switch", "pay off", "paying off", "paid off",
                 "clear the balance", "in full", "lump sum", "declined", "blocked", "frozen",
                 "lost my card", "stolen", "apple pay", "google pay", "contactless", "wallet",
                 # a card left at home is a lost card, and a bill that is only paid once a year
                 # is not the monthly habit this answers
                 "left my card", "left it at home", "left my wallet", "at home", "once a year",
                 # "again" was the word that made a bill that went up read as a bill you forgot:
                 # "our water bill has gone up again" and "the rent went up again" were answered
                 # with the direct debit, so the increase words are here and "again" is not in
                 # the key at all.
                 "gone up", "went up", "goes up", "going up", "increase", "increased", "rise",
                 "rises", "raised", "raise", "too high", "too much",
                 # a rent that arrives late every month is the arrears answer, which names the
                 # landlord and the housing payment: "my rent payment is late every month" lost
                 # that card to this row. Anything that names the landlord is not a forgetting.
                 "landlord", "rent is late", "rent payment is late", "rents late",
                 "late with my rent", "late with the rent", "late paying rent", "rent day",
                 "housing benefit", "housing payment",
                 # a benefit the state pays the person is not a payment they can forget to
                 # make: "my uc payment is late" and "my benefit payment is late" were told to
                 # set up a direct debit. lifeadmin's benefit-payment-not-arrived has it.
                 "benefit", "benefits", "universal credit", "uc", "pip", "esa", "tax credits",
                 "child benefit", "dwp", "jobcentre", "job centre", "hardship payment",
                 # a subscription you forgot about is a cancellation question, not a payment date
                 "subscription", "subscriptions", "streaming", "netflix", "spotify",
                 "gym membership", "cancel", "cancelling", "unsubscribe", "forgot about",
                 # paying the minimum on a card is a debt question, and it is the one line the
                 # key would otherwise take: "i pay the minimum every month on my store card and
                 # the balance never moves" is nobody forgetting anything
                 "minimum", "balance", "never moves", "not moving", "interest", "apr",
                 "store card balance", "pay the minimum", "only pay",
                 # a budget is the planning question, not a forgotten payment: "how do i budget
                 # when my pay is different every month" was told to set up a direct debit,
                 # which does not plan anything when the amount keeps changing.
                 "budget", "budgets", "budgeting", "make a budget", "how do i budget",
                 "budget when", "pay is different", "pay varies", "pay changes", "variable pay",
                 "irregular pay", "zero hours", "different every month", "different each month",
                 "money is different", "different every week", "weekly pay", "four weekly"),
          bias=1),
    entry("standing-order-vs-direct-debit",
          (("direct debit", "direct debits", "standing order", "standing orders"),
           ("difference", "differ", "different", "which", "what is", "whats", "or", "better",
            "versus", "vs", "cancel", "cancelling", "stopping", "stop", "how do i", "explain",
            # "how to set up a direct debit" has no "how do i" in it and fell through to "I'm
            # not sure about that one", so the two setting-up phrases are asks here as well.
            "how to set up", "set up a direct debit", "set up a standing order")),
          "A direct debit lets the company take the money, and the amount can change, which is why "
          "bills use it; a standing order is a fixed amount you send on a date you set, which is "
          "right for rent, savings or paying a person. You are protected on a direct debit by the "
          "Direct Debit Guarantee, so if they take the wrong amount your bank has to refund it in "
          "full. Cancel both with the bank, in writing or in the app, and cancel a direct debit "
          "with the company too so the paperwork agrees.",
          # a bill that went up and a switching question are not what the payment types are
          avoid=("energy bill", "gas bill", "electricity bill", "water bill", "council tax",
                 "switch supplier", "cheaper tariff", "my bill", "bill went up", "bill is",
                 # moving a payment to another bank is the switch service's answer, not "what
                 # the two kinds are": that line names a new bank and nothing about choosing.
                 "different bank", "another bank", "new bank", "switch bank",
                 "current account switch", "switch service")),
    # Changing one is a different question from what the two kinds are, and nothing answered it:
    # "can i change the direct debit" was a shrug and "how do i cancel a direct debit" got the
    # explanation of what a direct debit is. The answer is the two places to ask plus the
    # guarantee, and a bill that rose is the commonest reason to want to change one.
    entry("standing-order-stop",
          (("standing order", "standing orders"),
           ("change", "changed", "changing", "cancel", "cancelling", "cancelled", "stop",
            "stopping", "pause", "amend", "adjust", "move", "change the date", "amount",
            "reduce", "lower", "increase", "raise")),
          "Cancel or change it yourself at your bank, in the app or in writing: a standing order "
          "is yours to set and stop, so the payee cannot do it for you. Tell whoever you were "
          "paying as well, so a bill paid by standing order does not quietly fall behind, and "
          "remember there is no Direct Debit Guarantee on one - a wrong payment is not refunded "
          "automatically, you have to ask for it back.",
          # what each kind is, and which one suits, is the payment-types entry's question
          avoid=("difference", "differ", "what is the difference", "whats the difference",
                 "versus", "vs", "better", "explain", "which is better"),
          # the payment-types entry explains both kinds and scores on the same words; a line
          # that asks to move or stop one wants the how, so this answer wins the tie.
          bias=2),
    entry("direct-debit-change",
          (("direct debit", "direct debits"),
           ("change", "changed", "changing", "cancel", "cancelling", "cancelled", "stop",
            "stopping", "reduce", "lower", "cut", "increase", "raise", "pause", "amend",
            "adjust", "move", "date", "amount", "too much", "too high")),
          "Change or cancel it at any time: ring the company to move the date or the amount, and "
          "if they will not, tell your bank to cancel it, then confirm with the company so the "
          "paperwork agrees. The Direct Debit Guarantee means the bank has to refund a wrong "
          "payment in full and straight away, so an amount you never agreed is their problem, "
          "not yours. If the bill itself went up, send a real meter reading first - an estimated "
          "one is the usual cause - then ask them to spread the rest of the year instead of "
          "taking it all at once.",
          # the explanation of what each kind is stays with its own entry, and a switching
          # question is about the tariff, not the payment
          avoid=("difference", "differ", "what is the difference", "whats the difference",
                 "versus", "vs", "better", "explain", "switch supplier", "cheaper tariff",
                 "which supplier",
                 # moving the payment to another bank is the switch service's job, and that
                 # answer names the service and moves them all at once
                 "different bank", "another bank", "new bank", "switch bank", "switch banks",
                 "switching bank", "switch account", "current account switch", "switch service",
                 "moved bank", "moving bank"),
          # the payment types' own entry also covers "how do i" and "cancel", so it scores a
          # third word on the same line; the change is the answer when the line asks for it
          bias=3),
    # A payment that bounced is not a payment you want to change and it is not a card that was
    # declined: nothing was taken, so there is no refund to ask for and no card to unblock. The
    # words people use for it - bounced, failed, did not go through, returned, dishonoured - were
    # in no row at all, so "my direct debit bounced" got "Nice one. How did the rest of it go?"
    # and "the payment failed" got a sympathy line. The row answers what happens now: the retry,
    # the fee, the date, and what a second failure costs.
    entry("payment-bounced",
          # the payment itself, not the bill behind it: "rent" is left out on purpose, so
          # "i dont have enough money for my rent" keeps the rent-arrears answer and only a
          # line that names the payment reaches this one
          (("direct debit", "direct debits", "dd", "standing order", "standing orders",
            "payment", "payments", "my payment", "the payment", "instalment",
            "instalments", "installment", "installments"),
           ("bounced", "bounce", "bounces", "bouncing", "failed", "fails", "failing",
            "didnt go through", "didn't go through", "didnt clear", "didn't clear",
            "not gone through", "wont go through", "won't go through", "returned unpaid",
            "returned", "rejected", "refused", "unpaid", "dishonoured", "dishonored",
            "came back", "went back", "not enough money", "no money in the account",
            "not in the account", "short of money in", "dont have enough", "don't have enough",
            "havent got enough", "haven't got enough", "not enough in there",
            "didnt go out", "didn't go out", "not gone out", "hasnt gone out",
            "hasn't gone out", "didnt leave", "didn't leave")),
          ("Nothing left the account, but the company records a missed payment - and on a loan, a "
           "phone contract or a tenancy that is arrears. Ring them before they try again: move the "
           "date to just after you are paid, ask the bank to waive the fee (they usually do the first "
           "time), and keep the account topped up so the retry goes through."),
          # a card that was declined, money taken twice or for the wrong amount, and changing or
          # stopping a payment are all other rows; so are a debt and an email that bounced back
          avoid=("card was declined", "card got declined", "declined", "contactless", "pin",
                 "atm", "cash machine", "twice", "double", "double charged",
                 "charged twice", "wrong amount", "too much", "overcharged",
                 "difference", "differ", "versus", "vs", "explain", "which is better",
                 "change the date", "change the amount", "cancel", "cancelling", "cancelled",
                 "stop paying", "set up", "set it up", "email", "emails", "text", "texts",
                 "message", "messages", "letter came back", "post", "parcel", "ball",
                 "bounced back"),
          bias=1),
    entry("card-chargeback",
          (("chargeback", "section 75", "dispute", "disputed", "disputing", "card payment",
            "paid by card", "paid on my card", "credit card", "debit card", "card company",
            # money back from a seller who took it and did not deliver is what a chargeback is
            # for: "how do i get my money back from a scam website" was getting the 30-day
            # faulty-goods answer, and then the how-to-read-a-link answer
            "scam website", "scam site", "fake website", "website took my money",
            "company took my money", "gone bust",
            # a seller going quiet is what a chargeback waits for, but "reply" is also what a
            # person going quiet does: it only counts next to a word that names the seller, so
            # "the seller on vinted wont reply" is a card payment, while "my ex wont reply to my
            # texts" and "my landlord wont reply to my emails" stay where they were.
            "reply", "replies", "replying", "replied", "ignoring", "ignores", "ignored",
            "unresponsive"),
           ("money back", "refund", "charged twice", "double charged", "never arrived", "not arrived",
            "wrong item", "faulty", "company", "shop", "seller", "sellers", "trader", "retailer",
            "vinted", "ebay", "marketplace", "claim", "ask", "how do i",
            "what can i do", "they say no", "refused", "won't", "wont")),
          "Ask the shop first, in writing, and keep it short: what you bought, when, what went "
          "wrong and what you want back. If they will not play, ring your card provider and say "
          "you want a chargeback: a debit or credit card payment can be reversed when the goods "
          "never arrived, arrived wrong or the seller will not refund, usually up to 120 days from "
          "the payment. Anything over £100 on a credit card is stronger than that, because Section "
          "75 makes the card company jointly liable for the whole purchase.",
          # a card that was lost or stolen, and a scam call, are other answers; so is a debt,
          # which is not a disputed payment - "how do i clear my credit card debt" was being
          # told to ask the shop first
          avoid=("lost my card", "card lost", "stolen card", "card stolen", "frozen card",
                 "scam call", "scam text", "phishing", "fraud", "blocked card",
                 # a card named next to a hire car is the deposit, not a payment to dispute:
                 # "how do i hire a car without a credit card" was told to ask the shop for a
                 # refund, and travel.car-hire is the answer that talks about the card
                 "hire a car", "hire car", "car hire", "rent a car", "rental car", "car rental",
                 "hiring a car", "hired a car",
                 # closing the account, or opening one, is not a dispute about a payment:
                 # "how do i close a credit card account" was answered with the chargeback
                 # letter, and "account" is the word that says so
                 "account", "accounts",
                 # owing the money is not a dispute about it: "how do i clear my credit card
                 # debt" was answered with the chargeback letter

                 "clear my card", "clear my credit", "card debt", "credit card debt",
                 "debt", "debts", "owe", "owing", "minimum payment", "interest", "pay off",
                 "paying off", "savings",
                 # a person who stops answering is not a seller, however the line is worded
                 "ex", "my mate", "a mate", "my friend", "a friend", "mates", "friends",
                 "landlord", "landlady", "boss", "manager", "mum", "dad", "mother", "father",
                 "brother", "sister", "son", "daughter", "husband", "wife", "girlfriend",
                 "boyfriend", "partner", "neighbour", "neighbor", "housemate", "flatmate",
                 "colleague", "coworker", "family", "relatives",
                 # the person on the other side of the counter is treated the same way: a
                 # tenant, a buyer and a customer are not shops that sold you goods, so
                 # "my tenant wont reply about the rent" keeps its Citizens Advice answer
                 "tenant", "tenants", "buyer", "buyers", "customer", "customers",
                 "rent",
                 # a tradesman or a solicitor who stops answering is not a shop that sold goods,
                 # and a courier's claim is not a card payment: "the plumber wont reply to my
                 # messages", "my solicitor wont reply" and "evri has ignored my claim" were all
                 # getting the chargeback letter
                 "solicitor", "lawyer", "council", "plumber", "electrician", "builder",
                 "builders", "tradesman", "tradesmen", "contractor", "roofer", "courier",
                 "evri", "royal mail", "dpd", "hermes", "parcel", "parcels",
                 "ignored my claim", "my claim", "claim for",
                 # going quiet is only a chargeback when the quiet one sold the thing: the
                 # "reply" and "ignored" words also take people and companies the speaker has no
                 # purchase with, and "how do i ignore someone without being rude" was answered
                 # with "ask the shop first"
                 "being ignored", "ignoring me", "ignored me", "ignores me", "ignore someone",
                 "ignoring someone", "without being rude",
                 # asking how to report a site or a scam is not asking for money back from it,
                 # and "ask the shop first" is no answer to that: "how do i report a scam
                 # website" was getting the chargeback letter instead of the read-the-link one
                 "report", "reporting", "reported", "report them", "report it", "report the",
                 "report a scam", "report fraud", "action fraud",
                 # a balance to clear is a debt, not a disputed payment
                 "clear the card", "clear my balance", "clear the balance", "owes", "behind on",
                 "arrears",
                 # a public review is not a payment: "how do i reply to a bad review" was answered
                 # with "ask the shop first", because "reply" and "bad" are this row's words
                 "review", "reviews", "reviewer", "reviewers")),
    # The four things a person does when a shop or a hotel has not held up its end, and the one
    # that was missing entirely: "how do i take someone to small claims" and "how do i make a
    # small claim" were both answered with the homeworker's tax flat rate, because "claim" is a
    # key word on it and "how do i" is another.
    entry("small-claims-online",
          (("small claims", "small claim", "small claims court", "small claims track",
            "county court", "money claim online", "moneyclaims", "sue", "suing", "sued",
            "take to court", "take him to court", "take her to court", "take them to court",
            "take the company to court", "to court", "in court", "court case", "court claim",
            "tribunal"),
           ("how", "start", "file", "filing", "apply", "worth", "cost", "costs", "fee", "fees",
            "someone", "builder", "landlord", "company", "shop", "trader", "owe", "owed",
            "refund", "money", "claim", "claims", "do i", "can i",
            # "how much" is the price of it, and the child benefit row is keyed on that same
            # phrase, so without it here "how much does small claims cost" was a tie the
            # benefit row won.
            "how much", "how much is", "how much does", "how much do", "price", "expensive",
            "charge", "charges")),
          "It is the small claims track of the county court, and it is built for people with no "
          "solicitor: in England and Wales a claim up to £10,000 goes online at "
          "moneyclaims.service.gov.uk, in Scotland it is simple procedure up to £5,000, and in "
          "Northern Ireland small claims up to £3,000. The court fee is on a scale - £35 for a "
          "claim up to £300, rising to about £455 at £10,000 - and you get it back if you win. "
          "Write first: a dated letter before claim saying what is owed, why, and a deadline of "
          "14 days. Most settle at that letter, and the online form is the same work either way.",
          # a tax claim, a benefit and an insurance claim are each their own answer, and the
          # word "claim" alone is far too common to be a key here
          avoid=("tax", "hmrc", "rebate", "pension", "benefit", "benefits", "universal credit",
                 "child benefit", "insurance", "insurer", "expenses", "mileage", "working from "
                 "home", "work from home", "sick pay", "redundancy", "compensation for a flight",
                 "delayed flight")),
    entry("hotel-complaint",
          (("hotel", "hotel room", "guest house", "guesthouse", "bed and breakfast", "b and b",
            "booking", "booking.com", "airbnb", "apartment we booked", "room"),
           ("dirty", "filthy", "unclean", "stained", "smell", "smells", "smelly", "noise",
            "noisy", "not what i booked", "not what we booked", "not as described",
            "gave my room away", "gave our room away", "overbooked", "no room", "wrong room",
            "different room", "cockroaches", "bed bugs", "bedbugs", "mould", "mold", "broken",
            "rude", "complain", "complaint")),
          "Ask at the desk the same day, and name what you want: another room, a clean, or money "
          "off the night. Photograph the room before anyone touches it, and put the complaint in "
          "an email that evening so there is a date on it and a name on the reply. If the hotel "
          "cannot fix it, the booking site or your card is the lever - say the room was not as "
          "described and ask for a partial or full refund, then a chargeback if they refuse. The "
          "hotel's own complaints address and its country's trade body come after that, not "
          "before.",
          # booking a hotel is a different question from the one about the room you are in
          avoid=("how do i book", "cheapest", "cheap hotel", "deals", "where to stay",
                 "how much is a hotel", "book a hotel", "hotel in", "hotels in", "which hotel",
                 "cancel a booking", "cancellation policy", "deposit on a hotel",
                 # the money back from a booking is the refund answer's line: "can i get a
                 # refund from a hotel" was answered on main with the rate-and-cancellation
                 # card, and this row must not take it just because the room is a hotel room.
                 "refund", "refunds", "refunded", "money back", "cancel", "cancelling",
                 "cancellation", "refundable", "get my money",
                 # a smell in a room at home is not a complaint about a hotel: "how do i get
                 # rid of a musty smell in a room" and "how do i air a room that smells damp"
                 # were both answered by the front-desk script because "room" was the only
                 # word the row needed. A damp or musty room is home.py's damp-smell row.
                 # A bare "musty" or "damp" is not here, because a musty holiday let is still a
                 # complaint to the host: "the airbnb smells damp" and "my airbnb smells musty"
                 # lost every answer when these two words stood this row down. What separates the
                 # room at home is the shape of the phrase, which is what consumer.py's own
                 # avoid already lists.
                 # These are shapes of a room at home and nothing else. "room smells of" is
                 # not one of them: "my hotel room smells of damp" is a hotel room and contains
                 # that phrase, so it stood this row down and the line reached nothing.
                 "in a room", "in the room", "in my room", "a room that",
                 "basement", "cellar", "loft",
                 "attic", "bedroom", "living room", "spare room", "kitchen", "bathroom",
                 "wardrobe", "cupboard", "mattress", "carpet", "fridge", "bin",
# being walked is not a dirty room: a guest the hotel has no room for is owed a
                 # room elsewhere at its cost, which travel.py answers, so the room-complaint
                 # card hands those lines over rather than talking about photographs and emails.
                 "overbooked", "over booked", "double booked", "double-booked", "no room",
                 "no rooms", "walked", "walked to", "turned away", "gave my room away",
                 "gave our room away", "lost my booking", "no record of my booking"),
          guard=_a_hotel_room_or_no_home),
    entry("damaged-on-delivery",
          (("sofa", "settee", "couch", "armchair", "wardrobe", "mattress", "bed frame",
            "dining table", "furniture", "delivery", "delivered", "delivery driver",
            "delivery men", "white goods", "fridge freezer", "new fridge", "new cooker"),
           ("damaged", "damage", "dented", "dent", "chipped", "cracked", "scratched",
            "scratches", "broken", "torn", "ripped", "arrived", "arrives", "came damaged",
            "turned up damaged", "faulty", "wrong size", "missing parts", "not what i ordered")),
          "Write it on the delivery note before you sign, photograph it where it stands, and tell "
          "the retailer in writing the same day: something that arrives damaged is not of "
          "satisfactory quality under the Consumer Rights Act, so within 30 days you can reject "
          "it for a full refund or ask for a repair or a replacement. The courier is the "
          "retailer's problem, not yours - your contract is with the shop - and the seller pays "
          "for the return of a damaged item. Keep the packaging and the photos until it is "
          "settled.",
          # a machine that has stopped working is a repair question, and damage to a thing you
          # own is not a delivery
          avoid=("not working", "stopped working", "wont start", "won't start", "wont spin",
                 # a pet scratches furniture and a delivery arrives scratched; the two "scratch"
                 # questions have nothing else in common, and "my cat is scratching the sofa" was
                 # told to write it on the delivery note
                 "cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "puppies", "pet",
                 "pets", "claw", "claws", "clawing", "scratching post", "scratch post",
                 "wont drain", "no power", "leaking", "error code", "fault code", "repair",
                 "engine", "windscreen", "phone", "laptop", "car", "bike", "wall", "ceiling",
                 "floor", "door", "window", "insurance", "claim",
                 # an animal doing the damage is the pets question, not a parcel: "my cat keeps
                 # scratching the sofa" reached this entry on "sofa" + "scratches" and was told
                 # to write it on the delivery note. The animal names, not "scratched" alone,
                 # because a sofa can arrive scratched and that is still a delivery.
                 "cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "pup", "pups",
                 "rabbit", "hamster", "parrot", "budgie", "pet", "pets", "claws",
                 # The animal is often only a name - "Milly keeps scratching the sofa - any
                 # ideas?" has no animal word in it at all, and was still told to write it on the
                 # delivery note. The activity is named by the phrase it comes in instead, which
                 # is the shape a live animal makes: "keeps scratching", "scratching the",
                 # "scratch my". "arrived scratched" is the state a delivery came in and is not
                 # one of these, so it still reaches this entry.
                 "keeps scratching", "started scratching", "is scratching", "was scratching",
                 "scratching the", "scratching my", "scratching our", "scratch the", "scratch my",
                 "scratches the", "scratching up", "scratching at",
                 # and the same shape for a child, which is not a delivery either
                 "toddler", "child", "children")),
    entry("refund-refused",
          (("refund", "money back", "return"),
           ("says no", "said no", "say no", "refused", "refusing", "refuses", "won't", "wont",
            "will not", "declined", "rejected", "no refund", "fight", "complain", "small claims",
            "escalate", "what can i do", "now what")),
          "Put the request in writing and name the law, because most refusals change at that "
          "point: faulty goods must be refunded within 30 days of buying, then repaired or "
          "replaced, and a shop's own returns policy cannot take that away. Ask for a deadlock "
          "letter or the name of their complaints procedure, then use the ombudsman or resolver "
          "scheme for that trade, or the free small claims track for a sum under £10,000. Keep "
          "the receipt, the emails and the dates.",
          # the plain refund question is the entry above, which states the 30-day rule first
          avoid=("how do i get a refund", "am i entitled", "can i return", "how do i return",
                 "within 14 days", "online order", "reduced", "sale",
                 # a payment someone else took is fraud, not a shop refusing a refund
                 "fraud", "fraudulent", "scam", "scammed", "unauthorised", "unauthorized",
                 "didnt authorise", "did not authorise", "hacked", "phishing", "stolen",
                 # a parcel that went missing is the courier's question, not the shop's refusal
                 "returned something", "returned it", "sent it back", "courier", "post office",
                 "tracking", "never arrived",
                 # "return" is the shop's word for giving goods back and the tenant's word for
                 # getting a deposit back: "my landlord wont return my deposit" was answered
                 # "faulty goods must be refunded within 30 days"
                 "landlord", "landlords", "deposit", "deposits", "tenancy", "tenant", "tenants",
                 "letting agent", "flat", "house", "rent", "rented"),
          # a refusal is the later question, and it beats the plain answer when both score
          bias=3),
    entry("wedding-budget", (("wedding", "weddings", "wedding day", "wedding cost"),
                             ("budget", "cost", "save", "cheap", "cheaper", "afford", "average",
                              "much")),
          ("The guest list decides the budget, so fix it first: every ten guests costs roughly "
           "£1,000. A Friday or Sunday out of season, a village hall, a pub or a marquee, and "
           "putting the money into a good photographer rather than a fancy venue is where most "
           "couples find the savings."), bias=1,
          # A single thing's price is its own answer, and only where that thing has a row of
          # its own: "how much do wedding flowers cost" wants the flower numbers, not the
          # guest-list rule, but "how much does a wedding cake cost" has nowhere else to go,
          # so standing down for cake, catering or the dj only turned the rule into a hedge.
          avoid=("ring", "rings", "dress", "dresses", "flowers", "flower", "bouquet",
                 "photographer")),
    entry("save-for-kids", (("junior isa", "child savings", "kids savings", "save for my child",
                            "save for my kids", "save for kids", "save for a child"),
                            ("child", "children", "kid", "kids", "baby", "grandchild", "much",
                             # "what is a junior isa" names its subject and asks nothing else
                             "what", "is", "how", "explain")),
          ("A Junior ISA is the usual choice: up to £9,000 a year, tax free, and the money is "
           "theirs at 18. A regular saver or Premium Bonds keeps it simpler if you'd rather not "
           "lock it away; either way a small standing order you don't notice is what makes it "
           "add up.")),
    # Switching current accounts is lifeadmin.switch-bank-account: one entry for the switch
    # service, not a second copy here.
    entry("rent-afford", (("rent",), ("afford", "how much", "income", "take home", "wages",
                                      "salary", "budget", "how much of",
                                      # The same question is said with the figure and the payer:
                                      # "we can pay 250 a week rent" and "our rent budget is 900 a
                                      # month" reached a punt and a food card, because the only
                                      # word this row had for the plan was "budget". Anyone
                                      # naming what they can pay is asking this question.
                                      "we can pay", "we could pay", "can pay", "could pay",
                                      "we have", "a week", "per week", "pw", "a month",
                                      "per month", "pcm")),
          ("Keep rent to about a third of your take-home pay, and add council tax, energy and water "
           "before you commit. Multiply the rent by 12 and check you can also cover a five-week "
           "deposit and the first month up front, because those two land together."),
          # A food budget that names the rent in passing is the food card's line, not this one:
          # "my budget is about 250 a week on rent" answered with cheap staples before, and the
          # rent is the subject of the question.
          bias=1,
          # The same split as the debt cards, read the other way: this row answers when there is
          # no trouble in the line, and stands aside when there is, so that "i have three kids
          # and cant pay the rent" keeps the arrears card and "how much rent can we afford with
          # two kids" reaches this one. The bare kids and children used to be avoided here, and
          # that took the rent question off a family with children as well - a family asking
          # what a wage will carry is the person this card is written for.
          guard=_a_plan_and_no_trouble,
          avoid=("deposit", "deposits", "landlord", "behind", "cant afford", "can't afford",
                 "arrears", "evict", "eviction", "lost my job", "unemployed", "hungry",
                 "behind on")),
    # An eviction is not the same question as a rent you cannot pay, and the two were one row:
    # "my landlord is evicting me" was told to sort out arrears it never mentioned, and
    # "what is a section 8 notice" got the same paragraph. The notice row opens on the things
    # that decide the answer - is the notice valid, and no court order means no leaving - and
    # the money row keeps the money words (salmon-bell and clean-birch, #5912).
    entry("eviction-notice", (("evict", "evicting", "evicted", "eviction", "evictions",
                               # the notice names itself and nothing else, so it has to carry the
                               # line: "i got a section 21 notice" was an echo before this row.
                               "section 21 notice", "section 21", "s21", "s 21",
                               "section 8 notice", "section 8", "s8", "notice to quit",
                               "eviction notice", "possession order", "notice seeking possession",
                               "notice of possession"),
                              ("notice", "what is", "valid", "writing", "in writing", "how long",
                               "can they", "can my landlord", "can the landlord", "legally",
                               "legal", "rights", "served", "court", "signed", "check",
                               "have to", "does", "do i have to", "should i", "if", "when",
                               "say", "says", "given", "received", "got", "help",
                               # "my landlord is evicting me" asks it with no other word at all,
                               # and the first part has already said this is an eviction, so the
                               # person is the second signal. "my landlord wants me out" is not
                               # here: that line never says evict, and it keeps the money answer.
                               "me", "us")),
          ("An eviction always needs proper notice and a court order, so do not leave before a "
           "court order whatever the letter says. Check the notice is in writing and in the right "
           "form: a section 21 needs at least two months and cannot be served in the first four "
           "months of a tenancy, and a section 8 has to name the ground and the date. Shelter "
           "(0808 800 4444) is free and will check what you have been served; the council's "
           "tenancy team and Citizens Advice will too. If you have also fallen behind on the rent, "
           "tell them that as well, because it changes what you can ask for."),
          # a rent you cannot pay yet is the money answer, which knows about the rent day and
          # the Housing Payment; and a deposit or a repair is its own row.
          avoid=("deposit", "deposits", "boiler", "damp", "mould", "mold", "repair", "repairs",
                 "arrears", "behind on the rent", "behind with the rent", "behind on rent",
                 "short this month", "cant pay", "can't pay", "cannot pay", "no money",
                 "lost my job", "unemployed", "how much notice does my landlord have to give"),
          bias=2),
    # A landlord who wants to come in had no row at all, so the rent-arrears card answered it:
    # "can my landlord just come in when i am out" and "how much notice does my landlord have to
    # give" were both told to ring the council about a Discretionary Housing Payment, and four
    # more visit phrasings got a chat nod or a hedge. The two questions people actually ask are
    # how much notice they get and whether they can say no, so that is the card.
    entry("landlord-visit",
          (("landlord", "landlady", "letting agent", "letting agency", "property manager",
            "the agent", "my agent"),
           ("come in", "come round", "comes round", "coming round", "come over", "comes over",
            "visit", "visits", "visiting", "inspection", "inspections", "inspect", "access",
            "enter", "enters", "entering", "let himself in", "let herself in", "let themselves in",
            "let him in", "let her in", "let them in", "let in", "walked in", "walks in",
            "walk in", "turn up", "turns up", "turned up", "turning up", "unannounced",
            "without asking", "without warning", "kept a key", "keeps a key", "spare key",
            "has a key", "keys to", "viewings", "showing people round", "show people round",
            # "how much notice does my landlord have to give" and "with no notice at all" name
            # the notice and nothing else, so the notice phrases carry the line themselves. A
            # bare "notice" is not here: "my landlord gave me notice" is the eviction row's.
            "how much notice", "what notice", "notice before", "notice to come", "with notice",
            "without notice", "no notice", "24 hours", "twenty four hours")),
          ("At least 24 hours' notice in writing and a reasonable time of day, and you can say no "
           "to a time that does not suit and offer another - the tenancy agreement can promise "
           "more than that but not less, so a clause letting them walk in whenever they like does "
           "not stand. An emergency is the exception: a leak, a fire risk or no heating can be "
           "seen to without asking, and they have to tell you afterwards. If they let themselves "
           "in or turn up unannounced, put it in writing once that you want 24 hours' notice, keep "
           "a note of every visit with the date and time, and if it carries on ring the council's "
           "tenancy relations officer - they deal with harassment by landlords - or Shelter on "
           "0808 800 4444, which is free. A landlord who keeps a key is not breaking the law, but "
           "using it without notice is; do not change the locks without checking your agreement "
           "first, because that can be a breach even when they are the ones at fault."),
          # An eviction notice, a rent that cannot be paid, a repair and a deposit are the rows
          # that own those questions, and they all mention a landlord too.
          avoid=("evict", "evicting", "evicted", "eviction", "section 21", "section 8", "s21",
                 "notice to quit", "possession order", "notice seeking possession",
                 "asking me to leave", "wants me out", "wants us out", "arrears", "behind on",
                 "cant pay", "can't pay", "cannot pay", "deposit", "repairs", "repair",
                 "boiler", "damp", "mould", "mold", "increase the rent", "raise the rent",
                 "rent increase", "hand back the keys", "give the keys back",
                 # The direction of the notice decides, and this row is the landlord's
                 # notice: "how much notice do i give my landlord" is a tenant ending a
                 # tenancy, and it was answered "At least 24 hours' notice in writing and a
                 # reasonable time of day". Every phrase below puts the tenant on the giving
                 # end, so it stands this row down and leaves "how much notice" to it when
                 # the landlord is the one giving that notice.
                 "give notice", "gives notice", "giving notice", "give my notice",
                 "do i give", "notice do i give", "notice i give", "notice i have to give",
                 "notice i need to give", "i have to give", "i need to give",
                 "how much notice do i", "notice to leave", "notice letter",
                 "im leaving", "i'm leaving", "i am leaving", "moving out", "move out",
                 "end my tenancy", "ending my tenancy", "end the tenancy",
                 "ending the tenancy", "end of my tenancy", "surrender the"),
          bias=3),
    entry("rent-arrears", (("rent", "landlord", "arrears"),
                           ("behind", "cant afford", "can't afford", "arrears", "hungry", "kids",
                            "children", "help", "worried", "notice", "lost my job",
                            "unemployed", "money", "out", "wants me", "given me",
                            # a rent that will not stretch is said as "i might not be able to
                            # pay", and those lines had no second word to pair with either.
                            "not be able to pay", "cant pay", "can't pay", "cannot pay",
                            "wont be able to pay", "won't be able to pay", "short this month",
                            "late with the rent", "shortfall", "no money", "pay the rent",
                            "long", "weeks", "months", "pay day", "payday")
                           # "i havent paid my rent" is the plainest way this is said and it was
                           # the one phrasing with no word to pair with the rent. "i owe my
                           # landlord" is the shortest of all, and rent is the one debt that is
                           # never owed in a good way.
                           + NOT_PAID + ("owe", "owes", "owing", "behind with",
                                         "further behind", "in front")),
          ("Tell the landlord in writing before the next rent day, and ask the council about a "
           "Discretionary Housing Payment and that the Housing Element of Universal Credit is paid "
           "straight to them. Shelter (0808 800 4444) is free and will check what you have been "
           "served, and an eviction always needs proper notice and a court order."),
          # "rent" plus "out" is also how a tax question is written, and "do i pay tax on renting
          # a room out" was this answer: the Rent a Room rule is the lodger row's.
          avoid=("tax", "taxed", "taxable", "declare", "lodger", "spare room", "rent a room",
                 "renting a room out", "rent out a room", "renting out",
                 # the notice itself is eviction-notice's question
                 "evict", "evicting", "evicted", "eviction", "section 21", "section 8", "s21",
                 # and the notice a tenant gives is the notice letter, not arrears: "how much
                 # notice do i give my landlord" is a leaving question and was told to ring
                 # Shelter about the rent
                 "give notice", "how much notice", "notice letter", "write a notice",
                 "notice to leave", "im leaving", "i'm leaving", "i am leaving", "moving out",
                 "move out", "hand back the keys", "end of the tenancy", "last month",
                 "possession order", "notice to quit", "eviction notice",
                 # a person asking for the words is not a person telling you about arrears:
                 # "can you help me write a text to my landlord" was this answer, on the
                 # landlord and the "help" of the ask, and the drafting row is the one for it.
                 # What is asked for is the wording whatever the subject is, so "help me write
                 # a letter to my landlord about the arrears" is a draft as well.
                 "help me write", "help me word", "help me draft", "how do i word",
                 "how should i word", "write a text", "write a message", "write an email",
                 "write a letter", "word a text", "word a message", "draft a text",
                 "draft an email", "draft a message", "draft a letter", "put it in words"),
          # A figure somebody is working to is a plan, not a payment that went wrong: see
          # _a_figure_for_a_plan_is_not_a_debt.
          guard=_a_figure_for_a_plan_is_not_a_debt,
          bias=2),
    # "my ex partner wont pay the mortgage" is the commonest joint-debt question there is, and
    # the table had no row for it: it fell to the "free money advice" hedge. The lender does not
    # care who left, so the answer is about the joint liability, not about the relationship.
    entry("joint-mortgage-after-separation",
          (("mortgage", "mortgages"),
           ("ex", "my ex", "ex partner", "ex husband", "ex wife", "former partner", "separated",
            "separation", "split up", "left", "both names", "joint", "in both names",
            "wont pay", "will not pay", "stopped paying", "not paying", "has not paid")),
          ("To the lender you are both still liable for the whole mortgage, so the missed payments "
           "land on your credit file as well: pay what you can now, tell the lender what has "
           "happened, and ask for a payment arrangement on the arrears - a lender will usually "
           "freeze or spread them once it knows. Then claim their share back: write down what "
           "each of you has paid since the split, because that record is what a court works from. "
           "Ask the lender for a transfer of equity into one name only when you can afford the "
           "loan alone; it needs their consent and an affordability check, and a solicitor does "
           "the paperwork. If they will not pay and the house must be sold, a court can order a "
           "sale or the transfer of the share, and free advice from Shelter or Citizens Advice "
           "before you start is worth the call."),
          # a mortgage that is being applied for, or a rate question, is `mortgage-basics`
          avoid=("how much can i borrow", "how much can we borrow", "deposit", "first time",
                 "fixed rate", "variable rate", "remortgage", "overpay", "overpayment",
                 "how long", "which mortgage", "best mortgage", "mortgage deal", "mortgage rates",
                 "mortgage term", "stamp duty", "help to buy"),
          bias=2),
    # A bill shared with an ex is not a bill dispute with a supplier, and it is not the
    # split-the-rent-by-income card either: "my ex wont pay the bills" was answered with "ask for
    # the bill in writing with the dates and amounts, and send y..." (the supplier row), and
    # "my partner and i are splitting up and we have a joint account" got "pay in by what each of
    # you earns, not by halves". Both are the after-a-split money question.
    entry("ex-will-not-pay-the-bills",
          (("my ex", "my exs", "exs", "ex partner", "ex husband", "ex wife", "ex boyfriend",
            "ex girlfriend", "former partner", "my former", "he left", "she left", "we split up",
            "we separated", "since we split", "after we split", "separation", "divorce",
            "divorcing"),
           ("bills", "bill", "the bills", "council tax", "energy", "electric", "gas", "water",
            "broadband", "phone bill", "joint account", "wont pay",
            "will not pay", "stopped paying", "not paying", "has not paid", "owes", "in his name",
            "in her name", "in both names", "his name", "her name", "money")),
          "Whose name is on it decides who owes it. A bill or account in your name is yours to "
          "keep paid whatever you agreed between you, so pay it, then recover their share: send "
          "the bills with a date to pay, then a written request, then a money claim online if it "
          "is under £10,000. If it is in their name, ring the supplier and get your name off it "
          "rather than paying it. A joint account or joint loan keeps you both liable, so agree "
          "in writing who pays what, and take the free advice from Citizens Advice before you "
          "sign anything.",
          avoid=("how do i ask for a pay rise", "how do i claim", "which supplier", "cheapest",
                 # "my ex wont pay the rent" is a tenancy question with an eviction risk in it,
                 # and the renter's card says tell the landlord in writing and ring Shelter; a
                 # confident "whose name is on it decides who owes it" answered a different
                 # question, so the rent and the home are fenced out of this row.
                 "rent", "rents", "landlord", "landlords", "tenancy", "tenancies", "evict",
                 "evicted", "evicting", "eviction", "arrears", "behind on the rent",
                 # a mortgage in both names after a split is its own row and a better answer
                 "mortgage", "mortgages", "remortgage", "transfer of equity",
                 "switch", "compare", "how much is", "how do i read", "meter", "tariff",
                 "how do i pay", "when is the", "how do i split the rent", "what is a break"),
          # the friend-loan row in family.py keys "wont pay" too, and on "my ex wont pay his
          # share of the phone bill" it was answering "ask once, plainly and without an
          # audience" - warm, but it does not say that the name on the account is what decides
          # who owes it, which is the whole answer to a bill
          bias=4),
    entry("joint-account-after-a-split",
          (("joint account", "joint bank account", "our joint account", "shared account",
            "shared bank account", "joint current account", "joint savings"),
           ("split up", "splitting up", "separated", "separation", "my ex", "divorce",
            "divorcing", "break up", "broke up", "he left", "she left", "left me",
            "he has left", "she has left", "he has gone", "she has gone", "has left me",
            "walked out", "moved out", "hes gone", "shes gone",
            "ending", "ended", "leaving", "close", "closing", "freeze", "frozen")),
          "Freeze the joint account today - either of you can ask the bank to, and it stops more "
          "money going out - then open your own current account in the same week and move your "
          "pay and your direct debits across. You are both still liable for an overdraft or a "
          "joint loan on it, so agree in writing who pays what off and tell the bank in writing "
          "that you have separated. Ask Citizens Advice before you sign anything about that debt: "
          "it is free and it is the part people get wrong.",
          avoid=("how do i open", "which bank", "best account", "switch", "overdraft fee",
                 "how much can i save", "interest", "isa"),
          # The income-share row beside this one keys "joint account" and "joint" as well, and it
          # is the right answer to how a couple should share the bills - but on a split it was
          # answering "how do i close a joint account" with "pay in by what each of you earns".
          # This row is the narrower question, so it leans over it.
          bias=4),
    # A landlord is the other side of the same money, and the table only ever answered the
    # tenant: "my tenant has stopped paying rent" got the debt-advice card, "my tenants have not
    # paid rent this month" was told to tell the landlord in writing, "my tenant owes me two
    # months rent" was told about the hours on a payslip, and "my tenant wont pay rent" was told
    # the phone was not set up for contactless. The subject word is the tenant, so only a
    # landlord's line can reach this: a tenant's own line says "my landlord".
    entry("tenant-who-stops-paying",
          (("tenant", "tenants", "lodger", "lodgers"),
           ("not paying", "stopped paying", "not paid", "has not paid", "hasnt paid",
            "will not pay", "wont pay", "owes", "owed", "behind on", "arrears", "overdue",
            "two months rent", "three months rent", "rent", "evict", "section 8", "section 21")),
          ("Write to them today, by letter or email, and keep a copy: what is owed, the dates, and "
           "a date to pay by - that record is the first thing a court or a guarantor asks for. "
           "Offer a payment plan over a few weeks before anything else; it is quicker and cheaper "
           "than possession, and most arrears clear that way. If the rent is two months behind "
           "(eight weeks counts in some tenancies), a Section 8 notice on the arrears ground is "
           "what a court acts on in England: two weeks' notice, then apply for possession if they "
           "still do not pay or leave. Serve it on the right form and keep proof of posting, "
           "because a wrong notice means starting again. Check the deposit is protected in a "
           "scheme, and ring Shelter (0808 800 4444, free) or a landlords' association about the "
           "notice before it goes out."),
          # the tenant's own questions are the landlord rows' and the eviction rows'; this is the
          # landlord asking about the tenant, so anything that says "my landlord" is not this
          avoid=("my landlord", "my landlady", "landlord wont", "landlord will not", "landlord has",
                 "landlord is", "our landlord", "from my landlord", "as a tenant", "i am a tenant",
                 "im a tenant", "i rent", "i am renting", "evict me", "eviction notice from",
                 "notice from my landlord", "wants me out", "housing benefit", "universal credit",
                 "council tax", "rent a room", "spare room"),
          bias=3),
    # "threatening" on its own is not a debt: a threat at work or from a builder is somebody
    # else's problem. The word needs its object ("over", "for", "to send the bailiffs").
    entry("loan-shark", (("loan shark", "loan sharks", "illegal lender", "loan sharking",
                          "unlicensed lender",
                          # A money lender is how the same thing is said outside the
                          # phrase "loan shark", and without these words a person who
                          # writes it falls past this answer altogether.
                          "money lender", "money lenders", "moneylender", "moneylenders",
                          "payday lender", "payday lenders",
                          # The threat needs its object, and part two needs a debt word, so
                          # "at work" and "over the bill" cannot carry a line here. With that
                          # fence up the plain phrasings are safe again: "threatened by" and
                          # "threatening me" with nothing else are how a person says it.
                          "threatening me over", "threatening me for", "threatening me about",
                          "threatened me over", "threatened me for", "threats over",
                          "threats about", "threatening to send the bailiffs",
                          "threatening to send bailiffs", "threatened to send the bailiffs",
                          "threatening me", "threatened me", "threatened by"),
                         ("money", "debt", "debts", "owe", "owed", "borrowed", "borrow",
                          "lender", "loan", "bailiffs", "interest")),
          ("Do not pay: a loan from an unlicensed lender is not enforceable in court. Ring Stop "
           "Loan Sharks on 0300 555 2222 (England) or 0800 074 0878 (Scotland) — it is free and "
           "confidential, they can stop the demanding, and never hand over a bank card or your ID. "
           "Tell someone you trust today, and if you feel unsafe, 999."),
          # A bailiff or a debt collector who is already chasing is `bailiff`'s line: the door and
          # the warrant are what the person needs, and with `threatening me` in the key above this
          # entry was taking "a bailiff is threatening me" to the lender card on bias alone. Only
          # the names of an agent acting now are listed, so "threatening to send the bailiffs"
          # over a loan is still a lender line.
          # `the bailiff` is deliberately not one of these: `avoid` is a plain substring test, so
          # it would also stand this entry down for "they are threatening to send the bailiffs",
          # which is a lender line and has its own test. The shapes below name the agent as the
          # subject, which is the only case where the door answer is the one the person needs.
          avoid=("a bailiff", "bailiff is", "bailiff was", "bailiff came", "bailiff knocked",
                 "bailiffs are", "bailiffs were", "bailiffs came", "debt collector",
                 "debt collectors", "enforcement agent", "enforcement agents"),
          bias=3),
    # A threat from a bailiff or a debt collector is a debt question, not an emergency: the
    # abuse card left it alone and the line fell through to a reflection, so it is answered here.
    entry("bailiff", (("bailiff", "bailiffs", "enforcement agent", "enforcement agents",
                       "debt collector", "debt collectors", "county court judgment", "ccj"),
                      ("threatening", "threatened", "threats", "coming", "come", "knock", "door",
                       "at my door", "take", "take my car", "take my stuff", "seize", "remove",
                       "possessions", "what do i do", "can they", "rights", "let them in",
                       "refuse", "warrant", "court", "police", "call",
                       # the shape of the line when the letters keep coming and the person
                       # wants to know what to do, not what a bailiff is
                       "deal with", "how do i", "help", "letters", "letter", "keep coming",
                       "knocked", "worried", "scared")),
          ("You do not have to let them in, and they cannot push past you: keep the door shut, ask "
           "for their name and the court certificate through the letterbox, and ring the council or "
           "the court that issued the warrant the same day. A bailiff needs a warrant to enter, and "
           "it covers only that debt. For free advice ring National Debtline on 0808 808 4000 or "
           "Citizens Advice before you pay anything."),
          avoid=("tenancy", "landlord", "evict", "school", "parking", "water", "energy")),
    entry("gambling", (("gambling", "gamble", "betting", "bets", "bookmaker", "slots", "casino",
                        "bet"),
                       ("keep", "cant stop", "can't stop", "wages", "wage", "pay", "lose",
                        "losing", "help", "money", "away", "all", "addicted", "stop")),
          ("Ask your bank to block gambling payments today, install GamStop to exclude yourself "
           "from every UK site for five years, and ring GamCare on 0808 8020 133 — free, 24 hours, "
           "they will talk it through without judging. One day at a time, and tell one person who "
           "can hold the money with you."),
          bias=1),
    # --- what a thing is worth, and the charge that is not right ------------
    entry("prepayment-meter",
          (("prepayment meter", "prepayment", "prepay meter", "key meter", "pay as you go meter",
            "coin meter", "smart meter",
            # the forced fit names the meter too, and its own group two words are the ones
            # that line actually holds: a supplier, an energy firm, a fitter
            "put me on a prepayment", "put on a prepayment", "forced prepayment",
            "forced onto prepayment", "forced on a prepayment", "made me have a prepayment",
            "installed a prepayment", "fitted a prepayment", "swapped me to prepayment",
            "prepayment meter without"),
           ("should", "worth", "get", "switch", "change", "better", "what", "how", "about",
            "mean", "cost", "expensive", "back", "remove", "removed", "ask", "take it out",
            "supplier", "suppliers", "energy", "edf", "british gas", "eon", "e.on", "octopus",
            "scottish power", "npower", "fitted", "installed", "swapped", "forced")),
          ("A prepayment meter makes you pay before you use the fuel, so it suits a home where "
           "credit is the risk, but the standing charge is often a bit higher and you lose the "
           "cheapest direct debit tariffs. A supplier can only force one on you for a debt, and "
           "only after writing to you, so ask for a repayment plan instead and for the meter to be "
           "swapped back once the debt is cleared. You can ask your supplier (or any new one) to "
           "swap it for a credit meter once you are in credit and not behind; they cannot charge "
           "you for switching away from a prepayment meter if you ask for it after a debt is "
           "cleared. If you cannot top up, ring the supplier — they must give emergency credit."),
          # a smart meter's own worth-it question and a bill that went up are their own answers
          # A prescription prepayment certificate is a health-cost question that happens to
          # say "prepayment": "how much is a prepayment certificate" was answered with the
          # standing charge on a key meter. The word "certificate" is what is not an energy
          # word, and a prescription in the line says which table the question belongs to.
          avoid=("smart meter", "should i get a smart", "bill went up", "bill is higher",
                 "my bill", "how much do i pay",
                 "certificate", "prescription", "prescriptions", "medicine", "medicines",
                 "dental", "dentist", "glasses", "optician")),
    entry("school-costs",
          (("school", "schools", "daughters school", "sons school", "primary", "nursery"),
           ("trip", "trips", "cost", "costs", "charge", "charges", "normal", "quid", "reasonable",
            "asking for", "uniform", "kit", "money")),
          ("Trips and kit vary by school and by trip, so there is no fixed figure to compare: what "
           "matters is whether the school is asking for it. Voluntary contributions cannot be made "
           "compulsory, and a child cannot be left out of an essential trip over money — ask the "
           "office quietly for help, because most schools hold a fund for exactly this and spend it "
           "discreetly."),
          # "how do i get a stain out of a school uniform" is laundry, not money: the word
          # "uniform" beside "school" was enough to reach the trips-and-kit answer.
          avoid=("stain", "stains", "stained", "mark", "marks", "wash", "washing", "washed",
                 "clean", "cleaning", "remove", "get out", "get off", "shrink", "shrunk",
                 "iron", "ironing", "smell", "smells", "lost", "name tag"),
          bias=1),
    entry("food-bank", (("food bank", "foodbank"),
                        ("how", "use", "referral", "need", "help", "near", "get")),
          ("Food banks give a few days of free food, and most ask for a referral from a GP, school, "
           "Citizens Advice or support worker. Search for \"food bank\" plus your town, or ring "
           "Citizens Advice; some also help with fuel and baby things, and there's nothing to be "
           "embarrassed about.")),
    # The "two months' salary" figure is advertising, and it was reaching the hob-cleaning
    # answer instead. The ask gate is what keeps a kitchen ring out of it.
    entry("ring-cost", (("engagement ring", "wedding ring", "wedding rings", "engagement rings",
                         "ring"),
                        ("spend", "cost", "costs", "much", "budget", "afford", "price", "pay",
                         "save", "worth")),
          ("Spend what you could pay off in a couple of months without borrowing, and treat "
           "\"two months' salary\" as an advert rather than a rule - most people spend a good deal "
           "less, and nobody who matters is keeping score. Buy where resizing is free, put the money "
           "into the band and the cut you can actually see, and add it to your home contents "
           "insurance the day you get it."),
          # "ring" alone is the finger ring as often as it is the kitchen one, and the money
          # words in the key already keep a cleaning question out, so the gate takes the
          # jewellery words as well: "how much should we spend on rings" belongs here and was
          # going to the nuisance-calls card.
          # the nuisance-calls row scores three parts on "how much should we spend on rings"
          # ("rings", "how", "spend") where this row scores two, so the finger-ring row needs
          # the odd point to win the line it owns
          bias=1,
          ask=(("engagement", "wedding", "propose", "proposal", "marry", "married", "bride",
                "ring", "rings", "jewellery", "jewelry", "jeweller", "jewelers", "diamond",
                "carat", "band"),
               ),
          # the kitchen and bathroom rings are other entries' lines, and they carry money words
          # of their own ("how much is a new hob ring")
          avoid=("hob", "hobs", "cooker", "oven", "burner", "hotplate", "air fryer", "onion",
                 "calamari", "washer", "washing machine", "seal", "tap", "shower", "curtain",
                 "doorbell", "door bell")),
    entry("national-insurance", (("national insurance", "ni contributions", "qualifying years",
                                  "state pension age", "ni record"),
                                 ("what", "how", "why", "pay", "paying", "do", "does",
                                  "need", "check", "record", "years", "is", "my",
                                  "missing", "gap", "gaps", "worth")),
          "National insurance is the second tax on your pay, and it buys your state pension: you "
          "need about 35 qualifying years for the full amount, and gaps are worth checking before "
          "you pay anything. Look at your record in your online tax account first - some gaps can be "
          "filled cheaply, others are not worth it, and you can usually only go back six years. "
          "Class 3 voluntary contributions are about 18 pounds a week per missing year.",
          avoid=("payslip line", "deduction on my payslip", "how much is on my payslip",
                 "how much is national insurance", "national insurance rate", "ni rate",
                 "voluntary", "top up", "buy back", "ni number", "national insurance number",
                 "apply for")),
    entry("ni-rate", (("how much is national insurance", "how much national insurance",
                       "national insurance rate", "national insurance rates", "ni rate",
                       "national insurance percentage", "national insurance cost",
                       "how much ni"),
                      ("much", "rate", "rates", "pay", "paid", "cost", "percentage",
                       "percent", "ni", "national insurance")),
          "Employees pay 8 per cent of pay between about 12,570 and 50,270 pounds a year, and 2 per "
          "cent on anything above that; below 12,570 there is nothing to pay. Your employer pays a "
          "separate share on top and it does not come out of your pay. The line on your payslip is "
          "the employee part only, so it should come to roughly 8 per cent of what you earn over "
          "the threshold - if it is nowhere near, ask payroll to check your category letter."),
    entry("ni-number", (("national insurance number", "ni number", "nino",
                         "national insurance card"),
                        # "how do i get a national insurance number" is a phrase, and work.py's
                        # narrower row has one, so this row (which carries the 16th birthday, the
                        # letter and the payslip) was losing its own question to it
                        ("get", "apply", "how", "need", "lost", "find", "where", "new",
                         "without", "never", "received", "havent", "dont have", "do not have",
                         "what", "what is", "mean", "looks like", "format",
                         "how do i", "how do i get", "how do i apply", "where do i get",
                         "apply for")),
          "You get a national insurance number automatically just before your 16th birthday if you "
          "live in the UK, and it arrives as a letter, not a card. If it never came or you have "
          "lost it, it is on any payslip or P60; failing that ring HMRC and ask them to post it out. "
          "If you have just moved to the UK, apply over the phone and you can usually start work "
          "while you wait, as long as you can show you have the right to.",
          # adding entries to a domain lowers the rarity of its shared words, so the answer to this
          # one line is pinned rather than left to a tie
          bias=2),
    entry("voluntary-ni", (("voluntary national insurance", "voluntary contributions",
                            "voluntary ni", "top up my national insurance", "top up my ni",
                            "fill gaps in my national insurance", "fill a gap", "fill gaps",
                            "buy back years", "buy extra years", "gaps in my record",
                            "gap in my record"),
                           ("should", "worth", "how", "pay", "paying", "fill", "buy", "top",
                            "voluntary", "gap", "gaps", "my", "it")),
          "Usually yes, if it is a full missing year inside the six years you can still fill: one "
          "voluntary year costs around 900 pounds and adds roughly 300 pounds a year of state "
          "pension for the rest of your life, so it pays for itself in about three years of "
          "retirement. Check your record in your online tax account first - some gaps are already "
          "covered by credits and cannot be bought - and do not leave it, because the deadline for "
          "older years has moved without warning before.",
          bias=2),
# A split of a home's bills is a how-to, and a split of a dinner bill is a manners question.
# The household row's key - a split verb and a bill or rent word - fits both: "is it rude to
# split the bill" was answered "split rent by room if the rooms differ", and
# `tests.test_ids_are_unique` caught it because opinions' `split-bill-etiquette` wants that line.
# That row already stands down for a house share; this is the other half of the same rule. It is
# written as the *shape* of a manners question ("is it <any word> to split...", "etiquette",
# "awkward", "manners") rather than a list of adjectives, so a wording nobody has typed yet -
# "is it cheeky to split the bill", "is it tight to go halves" - is covered too, and a home word
# in the line keeps the household row.
    entry("split-house", (("split", "share", "sharing", "splitting", "divide", "who pays",
                           "split the household bills"),
                          ("rent", "flat", "flats", "house", "house share", "flat share",
                           "housemate", "housemates", "flatmate", "flatmates", "bills",
                           "household bills", "house bills", "utility bills", "utilities",
                           "energy bills", "council tax", "moving in", "mortgage")),
          "Split rent by room if the rooms differ and by income if one of you earns much more, and "
          "agree it before you sign rather than after. Put the household bills in a separate "
          "account that each of you pays into on payday, with the amounts written down, so nobody "
          "fronts the lot and nobody has to ask twice.",
          # "flat share" is also "shares", and a dividend answer ranks a rent question high: the
          # household split is the answer to the line that names a home, so it wins that tie.
          # A manners question about a table bill is not this row's, whatever its bias.
          guard=lambda reading: not _a_manners_question_not_a_home_split(reading),
          bias=2,
          # no ask gate here: "how do we split the bills" names only the bills, and the gate
          # made the household question fall through to the table-etiquette answer. A restaurant
          # or a takeaway is kept out by its own words instead.
          avoid=("dinner", "restaurant", "meal", "meals", "takeaway", "drinks", "tip", "tips",
                 "pizza", "curry", "who had what", "justgiving",
                 # a cottage rented for a week is a shared holiday, not the household: "how do i
                 # split a holiday cottage between 3 couples" and "we have rented a cottage with
                 # friends" were both told to split the rent by room and by income
                 "cottage", "cottages", "airbnb", "villa", "caravan", "holiday cottage",
                 "holiday house", "holiday home", "holiday let", "rented a house",
                 "house we rented", "place we rented", "holiday place", "week away",
                 # A bill for one occasion is not the household's: "how do we split the bill
                 # for the holiday" is what each of them had on the trip, and this row was
                 # answering it with rent by room and by income once the couple row stood down.
                 # The household keeps every line that names the home, the rent, the utilities
                 # or the bills themselves, which is what this row is for.
                 "the bill for", "bill for the", "bill for a", "the bill on", "bill on the",
                 "holiday", "holidays", "on holiday", "weekend away", "night out",
                 "for the weekend", "for the trip", "towards the trip", "eating out",
                 "the meals", "round of drinks",
                 # "how do i tell my housemate to pay their share" is the ask, not the split:
                 # wording.how-to-tell-them has the sentence to send
                 "how do i tell", "how do i ask", "how do i bring", "how do i raise",
                 "how do i say", "bring it up", "ask them to pay", "tell them to pay",
                 # "how do i split chores with flatmates" is the jobs, not the money:
                 # family.flatmate-chores answers it and this row keeps the bills.
                 "chores", "chore", "cleaning", "washing up", "dishes", "bins", "hoover",
                 "rota", "tidying")),
    entry("payment-jumped", (("payment went up", "payments went up", "payment has gone up",
                              "payment gone up", "payment jumped", "payments jumped",
                              "repayment went up", "repayments went up",
                              "repayments have gone up", "repayment has gone up",
                              "mortgage went up", "mortgage has gone up",
                              "mortgage payments have gone up", "monthly payment went up",
                              "mortgage just went up", "payment just went up",
                              "payments just went up", "repayment just went up",
                              "monthly payment has gone up", "payment has just gone up",
                              "paying more each month"),
                             ("mortgage", "repayment", "repayments", "payment", "payments",
                              "went", "gone", "up", "rise", "risen", "increased",
                              "jumped", "higher", "more", "why", "much", "what", "can",
                              "do", "now", "lender")),
          "Read the lender's letter or app for the new rate and the date it started: a payment "
          "jumps either because your fix has ended and you are on the standard variable rate, or "
          "because a tracker followed the base rate. If the fix has ended, ask a broker for a new "
          "deal now - remortgaging usually takes six to eight weeks and is far cheaper than "
          "drifting. If the new payment is only just too much, ask the lender to extend the term "
          "before you miss anything.",
          avoid=("overpay", "overpayment", "pay off", "deposit", "savings", "credit score",
                 "phone", "mobile", "broadband", "energy", "water", "council", "insurance",
                 "gas", "electricity", "licence", "license")),
    # A P45 is not a P60: it is the form for a job that has ended, and it has its own job to do
    # at the next employer. Keyed together, "what is a p45 and do i need it" was answered with
    # the end-of-year summary, which is the other form.
    entry("p45", (("p45", "p 45", "p45 form", "p45s", "my p45",
                   # the same form said without the number
                   "form from my old job", "form when you leave a job", "tax form when i leave"),
                  ("what", "where", "how", "get", "need", "find", "lost", "ask", "for", "is",
                   "a", "my", "should", "mean", "means", "new job", "new employer", "leaving",
                   "left my job", "start a new job")),
          "A P45 is the form your employer gives you when a job ends: your pay and tax for that "
          "job up to your last day, and your tax code. Hand part 2 to your new employer on your "
          "first day, keep part 1A for yourself, and keep it safe if you are not going straight "
          "into another job, because it is what a tax refund or a self assessment return is "
          "worked out from. Without one you go on a temporary emergency code, so tax comes out "
          "on the whole of your pay until HMRC sorts it - ask payroll for the P45 in writing if "
          "it never arrived.",
          # the end-of-year summary is the other form, and a payslip answers what was paid
          avoid=("p60", "end of year", "self assessment return", "tax return", "payslip",
                 "payslips", "national insurance record", "state pension")),
    entry("p60", (("p60", "p 60", "end of year", "proof of income",
                   "proof of earnings", "tax year"),
                  ("what", "where", "how", "get", "need", "find", "download", "lost", "ask",
                   "employer", "for", "is", "a", "my", "should",
                   # "what does a p60 show" is a tv question to a table that keys on "show"
                   "show", "shows", "say", "says", "contain", "contains", "mean", "means")),
          "A P60 is the one-page summary your employer gives you after 5 April each year: pay, tax "
          "paid, and your tax code. You need it for a mortgage, a visa or a tax return. Ask payroll "
          "or look in your online payslip portal - employers must give it to you by 31 May. If you "
          "have left a job, a P45 is the same idea for the part year, and you hand that to the next "
          "employer. If you cannot get one, HMRC can send you the figures.",
          # the tv table keys on "show", and "what does a p60 show" ties with it on score. The
          # form named is the money answer rather than the spelled-out name, so it wins the tie
          # outright: the name row says what the letters stand for and loses the 31 May deadline
          # and the P45.
          bias=3, avoid=("self assessment", "register", "side income", "side hustle", "landlord")),
    # The definition answers "what is national insurance" and is the wrong answer to a rate
    # question, a number question or a should-I-top-it-up question: those have entries of their
    # own below, and this one steps aside for them.
    # A bill that went up is not a repayment that jumped: the mortgage answer says ask for a new
    # deal, which is the wrong advice for a phone, a water bill or a broadband tariff.
    entry("tax-on-a-rise",
          (("pay rise", "raise", "salary increase", "pay increase", "more pay", "promotion",
            # "if i get a rise" names it without the word pay; bare "rise" is a verb elsewhere
            "get a rise", "got a rise", "gets a rise", "getting a rise", "payrise"),
           ("tax", "taxed", "national insurance", "take home", "take-home", "net pay", "deducted",
            "keep", "worse off", "better off")),
          "You keep most of it: only the part of your pay above each threshold is taxed at the next "
          "rate, so an extra 1,000 costs you 20 to 45 per cent of that 1,000, not of your old pay. "
          "Check the first payslip after the rise - the tax code should have gone up with the pay, "
          "and if it did not, that is what to query with payroll. A salary calculator gives the "
          "exact figure for your own numbers, and pension contributions come off before tax.",
          # asking for the rise, and the payslip itself, are other entries' lines
          # "how do i raise it" about a team's deadlines is not a pay question: a pay or tax word
          # has to be in the line, so "raise" alone cannot pull this answer in.
          ask=("tax", "taxed", "salary", "pay", "wages", "wage", "payslip", "take home",
               "take-home", "national insurance", "income", "gross", "net", "pension",
               "pounds", "earnings"),
          avoid=("how do i ask", "how do i get", "negotiate", "convince", "deserve", "worth",
                 "team", "deadline", "deadlines", "colleague", "colleagues", "project",
                 "payslip line", "my payslip", "p60", "p45", "self assessment", "self-assessment",
                 "tax return", "council tax", "tax code is wrong")),
    entry("bill-went-up", (("went up", "gone up", "has gone up", "have gone up", "jumped",
                            "jumps", "increased", "has increased", "keeps going up",
                            "gone through the roof", "doubled", "higher than usual",
                            "more than usual", "more than before"),
                           ("bill", "bills", "energy", "gas", "electricity", "electric",
                            "water", "broadband", "internet", "wifi", "phone", "mobile",
                            "tv licence", "direct debit", "monthly", "tariff", "council tax",
                            "standing charge")),
          "Ring or log in and ask why it went up and from which date: it is usually the end of a "
          "fixed deal, a meter estimate instead of a reading, or a price rise the supplier has to "
          "tell you about in advance. Give an up-to-date reading, and if the tariff ended, switch "
          "rather than stay on the standard one - for a phone or broadband, ask for the retentions "
          "team and say you are leaving, which is where the discounts are.",
          ask=("bill", "bills", "energy", "gas", "electricity", "electric", "water",
               "broadband", "internet", "wifi", "phone", "mobile", "tv", "licence", "tariff",
               "direct debit", "council tax", "standing charge", "payment", "payments"),
          avoid=("mortgage", "rent", "landlord", "tenancy", "tax return", "discount",
                 # cutting a bill, or a rise you are challenging, is another answer
                 "council tax", "save", "saving", "savings", "cheaper", "cut", "reduce", "lower",
                 "quick ways", "afford", "cant afford", "can't afford", "struggling",
                 "is that allowed", "allowed")),
    entry("tax-return-deadline", (("deadline", "due", "when", "how late", "last date",
                                   "tax return deadline", "self assessment deadline",
                                   "when do i file", "when is the tax return",
                                   "when is the self assessment"),
                                  ("tax return", "self assessment", "self-assessment", "tax year",
                                   "file my return", "filing my return", "file the return")),
          "In the UK the return for a tax year is due by 31 January, about ten months after the "
          "year ends, and the bill is due the same day. If you cannot pay, still file on time: the "
          "late-filing penalty is immediate, while a payment plan with HMRC is something you can ask "
          "for online.",
          # a bill or a band is another question
          # the date first is the answer, and the trading-allowance answer to "self assessment"
          # said everything except the date this line asks for
          bias=2,
          avoid=("council tax", "band", "energy bill", "water bill", "phone bill", "gas bill",
                 "electricity bill", "refund", "rebate")),
    # A machine that keeps a card is not a symptom. "what should i do if my bank card is swallowed
    # by the atm" was answered with the sore-throat remedy, because a card being swallowed and a
    # throat that hurts to swallow are the same verb, and health's sore-throat entry keys on
    # "swallowing". The promise here is the other way round: the wording stays and the *card* is
    # what is answered, so every way of saying the machine kept it gets the bank, not a gargle.
    # "kept", "ate" and "stuck" are the same event as "swallowed", and each one is only a key
    # beside a card, a cash machine or an atm, never as a verb on its own.
    entry("card-in-the-machine",
          (("swallowed my card", "swallowed the card", "swallowed my bank card",
            "swallowed my debit card", "swallowed my credit card", "swallowed by the atm",
            "swallowed by the machine", "swallowed by the cashpoint", "atm swallowed",
            "cashpoint swallowed", "machine swallowed", "machine ate my card",
            "ate my card", "ate my bank card", "ate my debit card", "kept my card",
            "machine kept my card", "atm kept my card", "cashpoint kept my card",
            "card stuck in the atm", "card stuck in the machine", "card stuck in the cashpoint",
            "card stuck in the cash machine", "card stuck in the card reader",
            "card got stuck", "card has got stuck", "card is stuck", "my card is stuck in",
            "card is stuck in the machine", "card got eaten",
            "card was eaten", "card went into the machine", "card got taken by the machine"),
           ("card", "atm", "cashpoint", "cash machine", "machine", "bank", "money", "cash",
            "swallowed", "stuck", "eaten", "ate", "kept", "taken", "what do i")),
          "Ring the bank on the number on the back of another card or in the app and ask them to "
          "block the card the machine kept and post a new one, which takes a few working days: "
          "nothing can be spent on it once it is blocked, and the money in the account is untouched. "
          "If the atm is in a branch wall and the branch is open, staff can open the machine and "
          "hand the card back the same day, so ask. Tell them if the machine showed a balance or "
          "took money without paying out, because that is refunded once they check it, and never "
          "let a stranger help you get the card out or give them your pin.",
          ask=("what", "how", "help", "card", "cash", "money", "back", "now", "bank",
               "ring", "do i", "should i"),
          avoid=("sim card", "memory card", "sd card", "gift card", "birthday card",
                 "christmas card", "loyalty card", "playing card", "card game",
                 "graphics card", "card in the post", "card has not arrived",
                 "pin number forgotten", "someone used my card", "card fraud", "cloned",
                 "account frozen", "scam text", "phishing"),
          bias=2),
    # Scam *texts* belong to technology.scam-text, which knows about 7726 and blocking; this one is
    # about money already moving: a bank call, a link that took a payment, a fee you nearly paid.
    entry("card-fraud", (("someone used my card", "someone spent", "used my card", "my card was used",
                          "card fraud", "card cloned", "cloned my card", "unauthorised",
                          "unauthorized", "fraud on my card", "money taken from my account",
                          "money has gone from my account", "i didnt spend", "i didn't spend",
                          "not me", "contactless", "lost my card", "stolen card", "card stolen",
                          "charged twice", "charged me twice", "double charged", "duplicate charge",
                          "two charges", "charged for something i didnt buy", "bank blocked my card",
                          "card got cloned", "cloned", "money was taken", "money taken",
                          # the same unauthorised payment said the other ways round: a payment
                          # taken twice, a company helping itself, and a charge after a
                          # cancellation. All three were shrugs or the app-store cancel screen.
                          "payment twice", "took a payment twice", "took a payment", "took money",
                          "took money from my account", "took it out", "taken without",
                          "without asking", "without my permission", "without my consent",
                          "they charged me again", "charged me again", "charged me anyway",
                          "charged anyway", "still charging", "cancelled but", "canceled but",
                          "cancelled it and they", "keeps charging", "keep charging"),
                         ("card", "account", "bank", "money", "spent", "charged", "payment",
                          "transaction", "online", "app", "cancel", "block", "freeze", "what do i")),
          "Ring the number on the back of the card, or use the app to freeze it, the moment you "
          "notice - the bank pays back unauthorised payments and you are not liable for them if you "
          "tell them without unreasonable delay. Then ask for the disputed transactions to be "
          "refunded, a new card and a new PIN, and say plainly that you did not make the payments "
          "and did not give anyone your details. Change the password on the email account the card "
          "is registered to, and report it to Action Fraud; if the bank refuses, the free Financial "
          "Ombudsman takes it after eight weeks.",
          # a frozen account is not a stolen card: it has its own entry below
          avoid=("scam text", "text message", "caller", "phone call claiming", "phishing",
                 "parcel fee", "investment", "boiler", "energy", "invoice from", "account frozen",
                 "account got frozen", "froze my account", "frozen my account", "account blocked",
                 "blocked my account", "frozen out", "cant access my money")),

    # A frozen account is the bank's decision, not a card someone else is using, and "freeze the
    # card in the app" is the wrong move on a line like "my bank account got frozen and i dont
    # know why". The answer is who to ring, what they will ask for, and what to do about the
    # direct debits while it is shut.
    entry("frozen-account",
          (("account frozen", "account got frozen", "account has been frozen", "account is frozen",
            "froze my account", "frozen my account", "frozen account", "frozen out",
            "blocked my account", "bank blocked my account", "account blocked",
            "restricted my account", "cant access my money", "can't access my money",
            "cant get my money", "cant use my account", "cant use my money", "bank account frozen"),
           ("bank", "account", "money", "why", "rent", "bills", "salary", "pay", "paid", "know",
            "frozen", "blocked", "unblock", "access", "on my own", "what do i", "what now",
            "cant pay")),
          "Ring the bank's own number - the one on your card, the statement or the app, never a "
          "number from a text or a call you did not make - and ask one question: which team froze "
          "it and why. It is usually a fraud review, an unusual payment, or an ID and address check, "
          "and a branch can clear an ID check the same day with your passport or driving licence "
          "and a bill. Ask what will still go through and which direct debits will bounce, and tell "
          "them if rent or a bill is due. Ask for the reason and a timescale in writing; if it is "
          "still frozen after eight weeks the free Financial Ombudsman takes it.",
          ask=("account", "bank", "money", "frozen", "blocked", "locked", "cant pay", "rent"),
          # a call about a frozen account is the scam-call entry's line, and a stolen card is
          # card-fraud's, so this one only answers the bank's own freeze
          avoid=("someone used my card", "card fraud", "cloned", "unauthorised", "unrecognised",
                 "scam", "text", "phishing", "pin", "cancel my card", "lost my card",
                 "boiler", "energy", "rang me", "called me", "phoned me", "rang asking",
                 "read out", "safe account", "move money", "message saying",
                 "they said they were"),
          bias=2),
    # A bank statement error is a dispute with the bank, and the free route to a person is the
    # formal complaint and then the Ombudsman, which is what people do not know about.
    entry("investment-scam", (("investment scam", "crypto scam", "fake investment",
                               # "X pays 8% a month, guaranteed - is that real?" makes the promise
                               # and asks a separate question, so each half carries its own phrase
                               "is that real", "is it real", "can that be real", "that be real",
                               "sounds too good", "double my money", "double your money", "guaranteed returns", "guaranteed profit",
                               "too good to be true",
                               "trading platform", "bitcoin investment", "someone offering",
                               "cold called about investing", "is this investment", "promising",
                               "percent a month", "percent a week", "percent a year",
                               "per cent a month", "returns guaranteed", "guaranteed return",
                               "investment is a scam"),
                              ("scam", "safe", "legit", "real", "trust", "check", "investment",
                               "invest", "crypto", "bitcoin", "returns", "profit", "money",
                               "guaranteed", "promise", "promised", "percent", "per cent",
                               "double my money", "doubling my money")),
          "Treat any guaranteed return as a scam, full stop: real investments fall as well as "
          "rise, and nobody can promise a percentage. Check the firm on the financial regulator's "
          "register (the FCA in the UK) and its warning list, be suspicious of anyone who found you "
          "by phone, ad or a messaging group, and never send money to a platform a friend of a "
          "friend recommended. If you have already paid in, stop adding money and call your bank "
          "the same day: the first hours are the only ones that get money back.",
          bias=3,
          # "is that real" is how people end a promise they have just quoted, but it ends other
          # quoted things too ("a text saying my parcel is held, is that real"), so this entry only
          # answers when the line is about money being put somewhere
          ask=("investment", "invest", "investing", "crypto", "bitcoin", "returns", "return",
               "profit", "scam", "guaranteed", "percent", "per cent", "trading", "fund", "share",
               "shares", "stock", "stocks", "money"),
          avoid=("isa", "pension", "index fund", "stocks and shares", "how do i start investing",
                 "should i invest", "compound interest")),
    # Arguing about money is a pattern question, and the answer is a shared number and a time to
    # look at it together, not a budget lecture.
    entry("student-finance-apply", (("student finance", "student loan", "maintenance loan",
                                     "tuition fee loan", "tuition fees"),
                                    ("apply", "apply for", "get", "how do i get", "how much",
                                     "when", "where", "reapply", "re-apply")),
          "Apply to Student Finance England (or the equivalent in Scotland, Wales and Northern "
          "Ireland) by the end of May before the course starts, and it does not matter whether "
          "you have a confirmed place yet. The tuition fee loan goes straight to the university; "
          "the maintenance loan is paid into your account in three instalments, and the amount "
          "follows your household income, not your grades. You can reapply every year, and you "
          "only start repaying the April after you leave, once you earn over the threshold."),
    # A rent rise is a notice question before it is a money question: the amount is only allowed
    # if the paperwork is right, and that is the answer people need before they argue about the sum.
    entry("rent-rise", (("rent", "rents", "landlord", "rent increase"),
                        ("went up", "gone up", "going up", "increase", "increased", "raised",
                         "raising", "hike", "more rent", "put my rent up", "raise the rent",
                         "is that allowed", "how much can",
                         # the rise said as news rather than named: "my landlord wont budge"
                         # (a stalemate about the sum), "put rent up without telling me",
                         # "keeps going up", "putting our rent up". None of these are the words
                         # `rent-increase` below keys on, so that entry keeps its own lines.
                         "budge", "wont budge", "without telling me", "keeps going up",
                         "put rent up", "puts rent up", "putting our rent up",
                         "putting my rent up", "wants more",
                         # "my rent is too high" is the same problem seen from the bill
                         "too high", "too much", "negotiate", "cheaper",
                         # "put the rent up" names the rent between the verb and "up"
                         "put the rent up", "raise the rent", "raised the rent",
                         # and the same rise with "up" before the rent: "my landlord keeps
                         # putting up the rent" was read as a job being put off (`habits
                         # .putting-things-off`, whose key has a bare "keep putting") and
                         # answered with "shrink the job until it is almost silly".
                         "putting up the rent", "putting up my rent", "putting up our rent",
                         "puts up the rent", "put up the rent", "put up my rent",
                         "putting the rent up", "puts the rent up", "rent going up",
                         "raising the rent", "put up my rent",
                         # the rise named as a noun, which is how it is raised in a sentence
                         # about what to say to the landlord: "about the rent rise"
                         "rise", "rises", "rising", "rent rise", "rent rises")),
          "Ask for the increase in writing and check the notice: in England and Wales a rent rise "
          "needs a section 13 notice with at least one month's notice and cannot normally happen "
          "more than once a year, and Scotland has its own rules on rent increases in a tenancy. "
          "Then check it against what similar flats nearby are asking, because you can accept it, "
          "negotiate it or challenge it at a tribunal if it is above market rent - and start "
          "paying the new amount only once the notice is correct, keeping the old letters.",
          ask=("rent", "rents", "landlord"),
          # arrears, a lost job and a deposit are other questions with their own answers
          avoid=("behind", "arrears", "cant afford", "can't afford", "evict", "eviction",
                 "deposit", "lost my job", "unemployed", "afford",
                 # a sauce is reduced, a rent is not
                 "reduce", "reducing", "lower my")),
    # Borrowing on a card and borrowing on a loan are different shapes, and people ask the
    # difference as a price question: the answer is when each one is cheaper.
    # "how do i budget when im paid weekly" was a shrug: monthly budgeting advice does not fit a
    # wage that lands every Friday, and weekly pay is what shop, care and agency work mostly is.
    entry("paid-weekly", (("paid weekly", "paid every week", "weekly pay", "paid week to week",
                           "weekly wage", "wages", "paid friday", "payday"),
                          ("budget", "budgeting", "manage", "plan", "money", "afford", "save",
                           "spend", "bills", "month", "stretch", "short", "switch", "switching",
                           "get paid", "how much", "change", "move to", "every week")),
          "Turn your month into weeks before you spend anything: add up the bills that come once "
          "a month, multiply by 12 and divide by 52, and put that amount aside out of every "
          "week's pay into a second account. Rent and the big direct debits come out of that pot, "
          "and the rest of the week's money is yours to spend; put a small amount aside on payday "
          "before the week starts, because it is much harder on Thursday. Keep one week's wage as "
          "a buffer so an early bill never means a borrowed week.",
          ask=("week", "weekly", "friday", "wages", "payday", "paid"),
          # a payday that did not pay is the missing-wage answer, not a lesson in weekly
          # budgeting
          avoid=("didnt get paid", "did not get paid", "havent been paid", "have not been paid",
                 "not been paid", "wages are late", "salary is late", "pay is late")),

    # Working from home costs a little and the tax man allows for it: the flat rate is the answer
    # people want, and "can i claim back tax on working from home" was getting a work-flexibility
    # script instead.
    entry("wfh-tax", (("tax back", "claim tax", "tax relief", "tax rebate", "tax return",
                       "working from home", "work from home", "tax on working"),
                      # The claim has to be in the line. "home" used to be here as well, and it
                      # is in every line that names the topic - "tomorrow im going to work from
                      # home" and "i can work from home twice a week" are a plan and a permission,
                      # not a claim, and both were told to claim £6 a week. The home phrases in
                      # the first part are enough to name the topic; the second part is the ask.
                      ("claim", "back", "rebate", "relief", "deduct", "hmrc", "allowance",
                       # "expenses" is the travel-and-receipts question, which is a work entry:
                       # "how do i claim expenses" was getting this working-from-home flat rate
                       "worth", "tax", "taxes", "taxed", "p87", "self assessment"),
                      ("claim back", "claiming", "always", "can i", "how do i", "much", "each")),
          "Claim the flat rate: HMRC lets you claim £6 a week (£312 a year) for working from home "
          "without keeping a single receipt, and you can go back up to four tax years. If you are "
          "employed, claim online or with form P87; if you already send a tax return, put it in "
          "the employment expenses section. Claim the real extra costs instead (a share of heat, "
          "light and broadband) only if they clearly beat £6 a week, and remember an employer "
          "allowance up to £6 a week is tax-free and needs no claim at all.",
          # The gate is a tax word or a home word, not "claim" and "expenses": those are on every
          # receipts line too, so "how do i claim back expenses at work" came here for the
          # homeworker's flat rate. With the home words here instead, "claim expenses for working
          # from home" answers here and the plain expenses question goes to the work entry.
          ask=(
               # the flat rate is for homeworking, so the line has to say home: "how do i do a tax
               # return" was answered "claim £6 a week for working from home" instead of the
               # self-assessment row, which is the question it asked
               "working from home", "work from home", "from home", "wfh", "homeworker",
               "homeworking", "home office", "allowance",
               # the flat rate has names of its own that never say home: "how do i claim the 6
               # pound a week tax relief" was a diet answer once the gate was home words only
               "flat rate", "6 a week", "6 pound", "six pound", "p87", "employment expenses"),
          # "how do i ask to work from home" is the flexibility question, not the tax one, and
          # claiming expenses back from work is mileage, fares and kit, not the homeworker's flat
          # rate
          avoid=("emergency", "emergency code",
                 "ask to work", "ask my boss", "request", "hybrid", "permission", "allowed to",
                 # "claim expenses" used to be here, and it stood this row down for the one
                 # line it is for: "claim expenses for working from home". The gate above keeps
                 # the receipts lines out instead, because none of them carry a tax or home word.
                 "claim back the money", "expenses claim",
                 "expenses back", "mileage", "milage", "receipts", "fares",
                 "train fare", "uniform", "tools for work", "overnight", "hotel",
                 # a refund for a journey is the travel entry's: "how do i claim a refund on a
                 # train ticket" scored "claim" and "how do i" and got the homeworker's flat
                 # rate, with no tax word in the line at all
                 # a state pension is claimed from the government, not from HMRC: "how do i
                 # claim my state pension" scored "claim" and "how do i" and got this flat rate
                 "pension", "state pension", "annuity",
                 "refund on a train", "refund on the train", "refund for a train",
                 "refund on my train", "money back on my train", "delay repay",
                 "train was cancelled", "train was delayed", "train is late", "train is delayed",
                 "flight was cancelled", "flight was delayed", "my train", "my flight",
                 # "how do i claim a tax refund" is the general question, not the homeworker's
                 # flat rate: the P800 answer covers a refund of any tax paid, and it was losing
                 # to this entry.
                 "tax refund", "tax refunds", "refund from hmrc", "hmrc refund", "refund of tax",
                 "overpaid tax", "overpaid", "p800", "owed tax",
                 # tax-free childcare is the nursery question, and "claim tax" is on both lines
                 "childcare", "child care", "nursery", "nurseries", "childminder",
                 "free hours", "tax free childcare", "tax-free childcare",
                 # "claim" is a bare word in the key, so every benefits line came here: a
                 # £312-a-year homeworker answer to "how do i claim universal credit" is the
                 # kind of wrong reply a person acts on. Single words only, or they are inert.
                 "benefits", "benefit", "universal", "credit", "rebate", "side", "hustle",
                 "freelance", "freelancer", "self", "employed", "sole", "trader", "child",
                 # a claim for VAT, a deposit, an insurance excess or overtime is not the
                 # homeworker's flat rate, and neither is cutting household spending
                 "vat", "deposit", "landlord", "tenancy", "tenant", "insurance", "excess",
                 "overtime", "cut my expenses", "cut expenses", "lower my expenses",
                 "reduce my expenses", "save on expenses",
                 # an insurer's words ("policy", "payout") only appear on insurance lines, and
                 # "claim form" is never a tax claim, so the flat-rate answer steps back
                 # "claim" alone also reaches the travel compensations and a shop guarantee:
                 # "how do i claim delay repay" was told to claim £6 a week for working from
                 # home, and "how do i claim on a warranty" the same. Those are other answers.
                 "insurer", "policy", "payout", "claim form", "claim on",
                 "delay repay", "delayed", "delay", "train", "trains", "rail", "railway",
                 "flight", "flights", "airline", "compensation", "warranty", "warranties",
                 "guarantee", "guarantees", "broken", "faulty",
                 # a benefit is a claim too, and jobseeker's allowance is the one people ask for
                 # by name: "how do i claim jobseekers allowance" was told to claim £6 a week for
                 # working from home, which is money for a different thing entirely
                 "jobseeker", "jobseekers", "jobseeker's", "jsa", "allowance", "dole",
                 "signing on",
                 # and the feeling about working from home is not a claim at all: "i work from
                 # home and feel lonely" was told to claim £6 a week, because "working from home"
                 # is in the gate and there is no tax word to tell the two apart. The loneliness
                 # and routine rows stand this one down, exactly as they do on wfh-focus.
                 "lonely", "loneliness", "lonely and", "isolated", "isolating", "alone",
                 "all day alone", "on my own", "by myself", "never see", "never speak",
                 "never leave", "never talk to", "going mad", "sane", "cut off", "miss people",
                 "missing people", "miss having people", "no one to talk", "nobody to talk",
                 "bored", "boring", "hate working from home", "hate working home",
                 "cant stand working from home", "sad", "depressed", "anxious", "lonely at",
                 # the edges of the day, the children in the house and the desk that never
                 # closes are the routine rows' questions, and they say "working from home" too
                 "switch off", "switching off", "cant switch", "can't switch", "cant stop working",
                 "always working", "no edges", "work late", "working late", "checking email",
                 "cant relax", "can't relax", "cant unwind", "overwork", "overworked",
                 "burn out", "burnt out", "burnout", "tired all the time", "no break",
                 "routine", "structure my day", "get into a routine", "start my day",
                 "kids", "children", "toddler", "toddlers", "baby", "school run",
                 "distractions", "distracted", "interruptions", "interrupted",
                 "concentrate", "concentrating", "concentration", "cant focus", "can't focus",
                 "focus")),
    # PIP is a name card and a payment card, and only the name existed. "when do i get my first pip
    # payment" got "Nothing of yours here to look at, so I can't check that" (a bank figure card
    # reading the word "payment"), "how often is pip paid" and "when is pip paid" got nothing, and
    # "how much is pip a month" got the baby's first-foods card off "how much" and "month". The
    # timing of a benefit is a fact, so it is here rather than left to a search.
    entry("pip-payment",
          (("pip", "pips", "personal independence payment", "personal independence payments"),
           ("when", "paid", "pay", "payment", "payments", "how often", "month", "monthly",
            "week", "weekly", "much", "rate", "rates", "amount", "first", "arrears", "get",
            "start", "started", "date", "backdated", "increase", "rises")),
          "PIP is paid every four weeks, in arrears, into the bank account, and the day is set by the "
          "date on the decision letter rather than a fixed day of the month: the first payment lands a "
          "few weeks after the decision and the four-weekly cycle runs on from there. A job and savings "
          "do not rule you out, and the decision rests on what you can do day to day rather than on the "
          "diagnosis, so anxiety or a bad back counts by how it limits you. There are two parts, daily "
          "living and mobility, each at a standard or an enhanced rate, and you can get one part without "
          "the other. Tell the DWP as soon as anything changes, because a rise is backdated only to the "
          "date they were told, and the rates go up each April - the current figures are on gov.uk.",
          bias=2,
          # The word is also a seed in an apple and a name people give a pet: a line about fruit,
          # a bird or a baby's name is not the benefit.
          avoid=("apple", "apples", "orange", "oranges", "lemon", "lemons", "pear", "pears",
                 "fruit", "seed", "seeds", "raspberry", "cider", "picture", "screen", "monitor",
                 "chicken", "hen", "hens", "chick", "chicks", "incubator", "hatch", "hatching",
                 "bird", "birds", "parrot", "budgie"),
          guard=_pip_the_benefit),
    # "how do i claim benefits" was answering with the homeworker's £6 a week, and once that was
    # held out it fell to a referral - and, right after any money answer, to the answer before it.
    entry("claim-benefits",
          (("claim benefits", "claiming benefits", "universal credit", "child benefit",
            "benefits claim", "claim child benefit", "apply for benefits", "on benefits",
            "benefits", "tax credits", "housing benefit",
            "jobseekers allowance", "jobseeker's allowance", "jobseekers", "new style jsa",
            "jsa", "signing on", "the dole"),
           ("how", "claim", "apply", "get", "start", "can i", "should i", "much", "what",
            "eligible", "qualify", "worth", "online", "am i", "entitled")),
          "Universal Credit is claimed online at gov.uk in one form for everything, and you can "
          "ask for an advance of the first payment on the same call - it is repaid slowly from "
          "later payments, so ask for it rather than borrowing. Have your bank details, housing "
          "costs and childcare costs ready, because the first payment takes about five weeks and "
          "the advance is what covers that gap. Child Benefit is a separate form (CH2) and is "
          "worth backdating: claim within three months of the birth or you lose the money. "
          "Citizens Advice will check what else you qualify for, free.",
          # a claim for expenses back from an employer is the homeworker's question
          avoid=("working from home", "work from home", "tax back", "flat rate", "expenses back",
                 "mileage", "uniform", "tools for work",
                 # "can i get a loan on universal credit" is a borrowing question, not a claim:
                 # it was answered with how to fill in the UC form
                 "loan", "loans", "borrow", "borrowing", "lender", "lenders",
                 # an appeal against a decision is not a claim for the first time, and it
                 # arrived here on the words "benefit" and "decision"
                 "appeal", "appeals", "appealing", "reconsideration", "tribunal",
                 "decision letter", "turned down", "refused my", "rejected my",
                 # "how do i get married" is not a benefits question, and it arrives here with
                 # the previous turn's subject on the end of it ("how do i get married claim
                 # child benefit"): the whole phrases, so a person who is married and asking
                 # about benefits still gets this answer.
                 "how do i get married", "how to get married", "how do i marry",
                 # child benefit is its own claim: its own form, its own rate, its own
                 # high-income charge. This row scores "can i claim child benefit" on a tie
                 # ("child benefit" + "claim") and won it, so the person asking was told how to
                 # claim Universal Credit online. The phrases are fenced, not the bare name, so
                 # a line that asks for both still gets this answer.
                 "claim child benefit", "claiming child benefit", "child benefit claim",
                 "can i claim child benefit", "who can claim child benefit",
                 "qualify for child benefit", "need to claim child benefit",
                 "child benefit if i earn", "child benefit if i'm", "child benefit if im")),
    # "how much tax do i pay on 30000" was answered with a pointer to Citizens Advice, which is
    # the wrong shape of answer for arithmetic: the bands are fixed, so the reply is worked out
    # from whatever salary the line names.
    entry("take-home-pay",
          (("how much tax", "take home", "take-home", "after tax", "net pay", "income tax on",
            "tax on a salary", "tax on my salary", "tax on 30", "tax on 40", "tax on 25",
            "salary after tax", "pay after tax", "what do i take home", "what will i take home",
            "whats my take home", "what is my take home", "how much do i take home"),
           ("salary", "pay", "earn", "earning", "wage", "wages", "year", "annually", "month",
            "monthly", "job", "much", "take", "much tax", "throw")),
          _take_home,
          avoid=("rebate", "refund", "claim back", "overpaid", "self assessment", "tax code",
                 "national insurance", "stamp duty", "council tax", "vat", "capital gains",
                 "dividend", "second job", "two jobs",
                 # "what is take home pay" and "what is net pay" are asking what the words mean,
                 # which is the payslip explainer's job, not a sum about one salary
                 "mean", "means", "meaning", "explain", "explained", "difference",
                 "what is take home", "whats take home", "what's take home",
                 "what is net pay", "what is gross", "what is a payslip",
                 # "how much tax" is the left half of four questions about a thing, not a
                 # salary, and the no-number fallback in _take_home reaches every one of them:
                 # the savings allowance answer, road tax and the rental-income one were all
                 # replaced with the bands. Each names its own thing, so each keeps its row.
                 "savings", "interest", "isa", "car", "cars", "van", "vehicle", "road tax",
                 "rental", "rented", "rented out", "landlord", "property", "buy to let",
                 "inheritance", "pension", "gift", "dividends",
                 # a rise is a change in pay, not a salary to work a year of tax out on: "i got a
                 # pay rise how much tax will i pay" lost the threshold rule to the bands
                 "pay rise", "payrise", "rise", "raise", "bracket", "promotion",
                 "increase", "increased",
                 # a pay packet that came out smaller is a payslip question, not a salary to work
                 # a year of tax out on: "my net pay dropped" and "my take home pay is less" were
                 # both given the bands. `work.payslip-short` is the row that answers a change.
                 "dropped", "drop", "went down", "gone down", "has gone down", "is less",
                 "is lower", "lower than", "shrank", "shrunk", "paid less", "underpaid",
                 "less on it", "short this month", "not the full amount"),
          # the payslip row owns "take home pay" and "net pay" too, and answering "whats my take
          # home pay on 40k" with the gross-and-net explainer is a miss: the line named a
          # salary, so the salary answer leans over it
          bias=2),

    # "do i have to pay tax on a second job" had no answer: the two-jobs question reads as
    # neither tax-rebate nor side-hustle, so it fell to a hedge. The allowance is a per-person
    # thing, which is the one fact that answers every shape of the question.
    entry("two-jobs-tax",
          (("second job", "second jobs", "two jobs", "2 jobs", "another job", "second wage",
            "second income", "second employer", "two employers", "both jobs", "both employers",
            "moonlighting", "extra job"),
           # "payslip" is the payslip entry's own word: using it here made the word common and
           # cost that entry the uniqueness that let it beat the television answer for
           # "what does my payslip show", so this key names the pay, not the slip
           ("tax", "taxed", "taxes", "pay", "allowance", "code", "national insurance",
            "ni", "owe", "more", "how", "do i", "will i", "much")),
          "Your personal allowance is per person, not per job, so one employer uses it and the "
          "second job is taxed at 20% from the first pound. That makes the second payslip look "
          "savage while the total is usually right. If the two together still come to less than "
          "£12,570, claim the overpaid tax back; if both employers are using a full allowance, "
          "HMRC will send a new tax code, and you can ask them to split the allowance if one job "
          "is small. Each job has its own National Insurance threshold, so two part-time jobs can "
          "pay less NI than one full-time one.",
          avoid=("rebate", "refund", "claim back", "overpaid", "self assessment", "side hustle",
                 "overtime", "second home", "second car",
                 # "how do i tell my boss im leaving for another job" names a second job and is
                 # a resignation, not an allowance question
                 "leaving for another job", "leaving my job", "leaving this job",
                 "tell my boss im leaving", "tell my boss i'm leaving", "hand in my notice",
                 "resign", "resigning", "resignation")),

    # The personal allowance itself: "what is the personal allowance" was answering the
    # duty-free table, because "allowance" is the only word the two questions share.
    entry("personal-allowance",
          (("personal allowance", "tax free allowance", "tax-free allowance", "tax free amount",
            "marriage allowance", "tax threshold",
            # the same question asked about earning rather than about the allowance
            "earn before tax", "before tax", "tax free income", "how much can i earn"),
           ("what", "how much", "is", "my", "mean", "means", "change", "changed", "why",
            "wrong", "check", "transfer", "lower", "higher", "raise", "raised")),
          "The personal allowance is £12,570 a year: you pay no income tax on it, and everyone "
          "gets their own, which is why a second job is taxed from the first pound. Above "
          "£100,000 it shrinks by £1 for every £2 you earn, and if one of a couple earns under "
          "it you can move £1,260 of it to the other with Marriage Allowance. Your tax code is "
          "that allowance written in code form: 1257L means the full amount.",
          ask=("personal allowance", "tax free allowance", "tax-free allowance", "tax free amount",
               "marriage allowance", "tax threshold",
               "earn before tax", "before tax", "tax free income", "how much can i earn"),
          # "allowance" is the savings allowance's word too, and its row carries bias=1: the
          # question asked here is the income-tax allowance, so this row leans over it
          bias=2),

    entry("tax-rebate",
          (("tax rebate", "rebate", "overpaid tax", "overpaid", "paid too much tax",
            "paid too much in tax", "overpaid on tax", "tax back", "refund of tax",
            "p800", "tax code refund",
            # the everyday way people say it. "how do i claim a tax refund" names HMRC's own
            # refund, and reached the homeworker's flat rate and the 30-day shop law instead.
            "tax refund", "tax refunds", "refund from hmrc", "hmrc refund"),
           ("how", "get", "claim", "much", "when", "why", "owed", "back", "do i", "can i",
            "think", "paid too much",
            # "i overpaid tax" and "hmrc overpaid me" are the same rebate question stated rather
            # than asked, and stated is how people say it when the letter has just arrived
            "tax", "hmrc", "rebate", "p800", "tax code",
            # "am i due a tax refund" is the same question and was a punt
            "due", "am i", "should i", "did i")),
          "If HMRC owes you, the letter is a P800 and the money comes back by itself once you "
          "confirm your bank details in your online tax account - no agent needed, and anyone who "
          "rings you about a rebate is a scam. If you think it is missing, claim with form P87 "
          "online for work expenses (up to four years back), and for a flat-rate homeworker claim "
          "it is £6 a week. Give it eight weeks before chasing.",
          avoid=("emergency", "emergency tax", "emergency code",
                 "working from home", "work from home", "flat rate", "benefits",
                 "universal credit",
                 # the council's own overpayment is the council's refund, not HMRC's P800
                 "council tax",
                 # the flat rate for a uniform is its own row, and "tax back" is in this key
                 "uniform", "uniforms", "work uniform", "laundry", "work clothes",
                 "work clothing", "overalls", "protective clothing",
                 # a call about a rebate is a scam, not a claim: lifeadmin owns that line
                 "rang me", "called me", "phoned me", "text saying", "message saying",
                 "is this a scam", "by text",
                 # money paid by the employer by mistake is payroll's question, not HMRC's: the
                 # P800 answer tells you to wait for a letter that will never come
                 "at work", "employer", "payroll", "payslip", "paid me twice", "extra in my pay",
                 "my wages", "boss")),
    # A refund that arrives unasked is the commonest tax scam there is, and it had no row of its
    # own: `tax-rebate` stands down on "rang me", "text saying" and "by text" on purpose (a call
    # about a rebate is a scam, not a claim), and `lifeadmin.check-a-scam` stands down on a named
    # medium, so the line fell through to `wording.ask-for-refund` and a person saying "someone
    # rang saying im due a tax refund" was given the cracked-lamp complaint letter. The medium is
    # the point here, not an accident, so this is its own row.
    entry("tax-refund-scam",
          (("tax refund", "tax rebate", "refund of tax", "tax back", "hmrc refund",
            "refund from hmrc", "rebate", "rebate cheque", "owe me tax", "tax owed to me",
            # a bare "refund" counts only with hmrc or the tax office named beside it, which is
            # how "i got an email from hmrc saying i have a refund" and "hmrc text asking me to
            # click a link for my refund" are said; both were reflections before this
            "refund", "refunds"),
           ("text", "texts", "texted", "sms", "whatsapp", "email", "emails", "emailed",
            "message", "messages", "messaged", "rang", "ring", "ringing", "called", "calling",
            "phoned", "phoning", "link", "click", "clicked", "claim", "saying", "says",
            "says im", "saying im", "told me", "sent me", "got a", "asking me", "asking for",
            "hmrc", "tax office", "tax", "inland revenue")),
          "HMRC does not text, email or ring about a refund, and a real one asks nothing of you: "
          "it arrives as a P800 letter or appears in your online tax account and is paid "
          "automatically. Do not use the link or ring the number in the message. Forward the text "
          "to 7726, send the email to phishing@hmrc.gov.uk, and check your account by typing "
          "gov.uk into the browser yourself.",
          # A refund you go and claim is `tax-rebate`'s line, and it says so by asking how, when
          # or whether: this row is a message that arrived and wants something back.
          avoid=("how do i claim", "how do i get", "am i due", "how much", "when will",
                 "did i overpay", "p87", "expenses", "work from home", "uniform",
                 "mortgage interest", "marriage allowance", "self assessment", "tax return",
                 # a refund that has not arrived is a claim question, not a message: those
                 # belong to `tax-rebate` with the P800 and the eight weeks.
                 "where is my", "where is the", "still waiting", "not had", "havent had",
                 "have not had", "how long does", "how long will", "chase", "chasing",
                 "eight weeks", "8 weeks", "overdue",
                 # a letter is the one medium HMRC does use: a P800 about a refund that has
                 # arrived is a real letter, and the "does not text, email or ring" answer
                 # told the person to forward a letter to a phishing address
                 "letter", "letters", "by post", "in the post", "went to the post office",
                 "p800"),
          # a bare "refund" is HMRC's only when no shop or courier is named with it
          guard=_a_refund_the_tax_office_sent,
          bias=1),
    # Emergency tax: the code a new starter or a fresh P45 leaves behind, which is the commonest
    # tax shock there is - it is why a first payslip at a new job looks savage. It is its own
    # question (what is this, is it wrong, do I get it back), not the reading of a payslip and
    # not the homeworker's flat rate, so the four rows it looks like on paper stand down for it:
    # those lines are all the emergency tax question under another part of its name.
    entry("emergency-tax",
          (("emergency tax", "emergency tax code", "emergency code", "emergency basis",
            "month 1 basis", "week 1 basis", "w1m1", "w1 m1"),
           # "why am i on emergency tax" is the commonest shape, and it asks with no verb of its
           # own, so the question words are keys here and the bias breaks ties.
           ("what", "mean", "means", "why", "how", "get", "back", "claim", "refund",
            "rebate", "paid", "paying", "taxed", "tax", "code", "payslip",
            "am i", "stop", "change", "fix", "correct", "long", "much", "check",
            "repaid", "come off", "off my pay", "first payslip", "new job", "started")),
          "Emergency tax means HMRC had no P45 or tax code for you yet, so that month is taxed "
          "as if it were your only one and none of your tax-free allowance goes against it - the "
          "code shows W1, M1 or an X. It usually corrects itself once payroll has your P45 and "
          "HMRC sends the right code, so hand the P45 in and check the code in the HMRC app; if "
          "it is still an emergency code after the next payslip, ring HMRC and they will tell "
          "your employer what to use. Anything overpaid comes back in your pay or as a refund "
          "after the tax year ends.",
          # A rebate someone rings you about is the scam line, and a self assessment bill is a
          # different question about a different kind of tax.
          avoid=("scam", "rang me", "called me", "text saying", "message saying",
                 "self assessment", "self-assessment", "council tax", "side hustle"),
          bias=1),
    entry("card-vs-loan", (("loan", "loans", "personal loan", "borrowing"),
                           ("credit card", "card", "cheaper", "cheapest", "compare", "better",
                            "vs", "versus", "which")),
          "A loan is cheaper for a fixed sum over a fixed time: the rate is set at the start, the "
          "monthly payment never moves and 0% card offers usually end before a big balance is "
          "cleared. A credit card is the better tool for something you can clear in full each "
          "month, because it costs nothing and protects purchases over £100. For £5,000 over two "
          "years, compare the loan's APR with a 0% balance transfer fee plus what the card's rate "
          "becomes afterwards, and never use a card for cash.",
          # "should i take out a loan to pay off my card" is the consolidation question
          avoid=("pay off", "pay it off", "paying off", "consolidate", "clear", "clearing",
                 "student loan", "mortgage"),
          bias=1),

    # What childcare costs and what knocks the price down. The cost is the question people
    # actually ask, and the free hours and tax-free childcare are what they have not heard of.
    entry("childcare-cost",
          (("childcare", "child care", "nursery", "nurseries", "childminder", "childminders",
            "creche", "after school club", "breakfast club", "wrap around care"),
           ("cost", "costs", "how much", "price", "prices", "expensive", "afford", "affordable",
            "cheap", "cheaper", "month", "monthly", "week", "help", "funding", "free hours",
            "free childcare", "pay for", "claim", "money off")),
          "Full-time nursery is roughly £1,000 to £1,500 a month in England, childminders are "
          "usually cheaper, and the help is what brings it down: 15 hours a week free for every "
          "three and four year old (30 if both parents work and earn under £100,000 each), plus "
          "tax-free childcare, which tops up every £8 you pay in with £2 up to £2,000 a year per "
          "child. Ring your council's family information service for the nurseries near you with "
          "places and prices, because it varies enormously by area, and ask about the free hours "
          "before you compare the monthly figures, since most nurseries spread them over the year.",
          avoid=("babysit", "babysitting", "who looks after", "my mum has the kids",
                 "nanny", "child benefit")),

    # Discounts with a student card are a shopping question people ask directly, and the answer
    # is which card to get and that most shops only give it at the till.
    entry("student-discount",
          (("student discount", "student discounts", "student card", "nus card", "nus extra",
            "totum", "unidays", "student beans", "isic", "student oyster", "student railcard"),
           ("get", "how", "where", "best", "worth", "id", "apply", "sign up", "uk", "cheapest",
            "money off", "use")),
          "Get a free UNiDAYS or Student Beans account with your college email, and Totum (the "
          "old NUS card, about £15 a year) if you want the ones that need a physical card; most "
          "big chains give 10%, and plenty give student prices only when you ask at the till, so "
          "ask every time. On top of those, a 16-25 Railcard takes a third off train fares and an "
          "18+ Student Oyster takes 30% off London travelcards.",
          avoid=("tax", "loan", "finance", "maintenance loan", "fees")),

    # "what's a good side hustle for evenings" is a what-should-i-do question, so it wants ideas
    # and the £1,000 allowance, not the Self Assessment dates that tax-return carries.
    entry("side-hustle",
          (("side hustle", "side line", "extra income", "earn extra", "extra money", "second job",
            "evening job", "weekend job", "make some money on the side", "pocket money job"),
           ("evening", "evenings", "weekend", "weekends", "idea", "ideas", "good", "best",
            "start", "what", "how", "quick", "online", "worth", "extra", "any")),
          "Pick the one thing you can already do that people pay for, and sell it in the smallest "
          "packet: tutoring a GCSE subject, fixing bikes, editing CVs, dog walks on the way home, "
          "weekend cover in a bar or care home. Sell to people you can reach this week rather than "
          "building a website, do two or three paid jobs before you spend anything on it, and keep "
          "a record of what you earn: £1,000 a year of side income is tax free (the trading "
          "allowance), and above that you register for Self Assessment.",
          # declaring side income and the tax dates are tax-return's line
          avoid=("declare", "self assessment", "tax return", "register", "owe tax", "ebay",
                 "vinted", "depop")),

    # A pension where nobody matches what you pay in: "is a pension worth it if im self employed"
    # was getting the workplace-pension free-money script, which has an employer in it.
    entry("self-employed-pension",
          (("self employed", "self-employed", "sole trader", "freelance", "freelancer",
            "my own business", "run my own business", "contractor",
            # "set up a pension for myself" reached the cooking-for-one answer
            # "start a pension" and "set up a pension" stay out: someone employed who is
            # starting one wants the workplace answer, and this card read every such line
            "pension for myself", "a pension for myself", "my own pension",
            "personal pension", "private pension", "sipp"),
           ("pension", "pensions", "sipp", "retire", "retirement", "save for later", "pot",
            "worth it", "worth", "start one", "set one up", "how do i save", "save for",
            "nothing going in", "pay myself", "no pension")),
          # "im self employed how do i save for retirement" is this row's question, and the
          # register-as-a-sole-trader row beat it on "self employed" plus a question word: a
          # person asking about retirement has already decided to trade, so this one fits better
          "Nobody adds to it but you, so it is worth it only as a tax deal: open a SIPP or a "
          "personal pension and every £80 you pay in becomes £100 with basic-rate relief (higher "
          "rate claims the rest through Self Assessment), and the money grows free of tax until "
          "you draw it. Put a fixed share of each invoice aside the day it lands - 10% is a "
          "workable start - and keep enough in an ordinary account for a bad month, because you "
          "cannot touch the pension until you are 55. Also check your state pension record: "
          "35 qualifying years gets the full amount, and gaps can be filled cheaply.",
          # the workplace one is the employee's question, and tax returns are their own entry.
          # Not "employer"/"workplace" here: a near-miss against "employed" would kill this entry
          # on its own key word.
          bias=1,
          avoid=("opt out", "auto enrolment", "auto-enrolment", "tax return", "self assessment",
                 # the age it can be drawn at is the taking-the-money question, and this card
                 # answers a line that asked when with what the relief is worth
                 "what age", "at what age", "how old", "when can i", "when do i", "when will i",
                 "draw my", "draw the", "access my", "get at it", "retire at", "retiring at",
                 # whether to go freelance at all is a different question with its own answer,
                 # and "is it worth going freelance" was given the SIPP: the pension is what to
                 # do after you have decided, not how to decide
                 "go freelance", "going freelance", "become freelance", "be freelance",
                 "work for myself", "be my own boss", "go it alone", "leave my job",
                 "should i go", "is it worth going", "worth going freelance")),

    # "should i get income protection insurance" was getting the extended-warranty answer,
    # because both are a "should i buy this" with a "worth" in the line.
    entry("income-protection",
          (("income protection", "critical illness", "sick pay insurance", "permanent health",
            "mortgage protection", "protection insurance"),
           ("worth", "should i", "need", "cost", "costs", "get", "buy", "take out", "how much",
            "any good", "recommend")),
          "Check what your employer pays first: many give six months full pay and half pay after "
          "that, and statutory sick pay alone is about £119 a week, so the gap you are insuring is "
          "the real question. If you have a mortgage or children and only statutory sick pay, "
          "income protection that pays out after 13 or 26 weeks is much cheaper than one that pays "
          "from day one, and a fee-free broker will price both. Skip critical illness cover sold "
          "alongside a mortgage until you have checked it is not already in the deal.",
          avoid=("warranty", "appliance", "boiler", "phone", "gadget", "car")),

    # "what should i do with a bonus" was a shrug: it is an order-of-operations question.
    entry("bonus-money",
          (("bonus", "a bonus", "windfall", "inheritance", "back pay", "tax rebate", "pay out",
            "payout", "extra money"),
           ("what should i", "what do i do", "spend", "save", "pay off", "invest", "use it",
            "best thing", "put it", "do with")),
          "Clear the most expensive debt first - a credit card at 20% beats anything you can earn "
          "- then top the emergency fund back up to a month of essentials, and only then look at "
          "the pension or a stocks and shares ISA, where a lump sum can go in now and grow. Bonus "
          "tax is already taken through PAYE, so there is nothing to declare. Keep a tenth for "
          "something you actually want, or the plan never sticks.",
          ask=("bonus", "windfall", "inheritance", "back pay", "rebate", "payout", "payout"),
          avoid=("warranty", "insurance", "bonus points", "loyalty", "nectar", "clubcard",
                 "bank bonus", "switching bonus")),

    # "how do i stop my card being used online" was answered with what ID to take to a bank,
    # because the line carries "card" and "bank account" words and nothing said safety.
    entry("card-safe-online",
          (("card being used online", "card used online", "card details safe", "my card details",
            "safe to use my card online", "shop online safely", "shopping online safely",
            "save my card", "saved card", "virtual card", "use my card online",
            # "how do i keep my bank card safe online" names no site and no "details", so the
            # phrases above missed it and it went to the bank-account entry.
            "bank card", "card safe online", "bank card safe", "keep my bank card safe",
            # bare "online" is the phrase the shopping-at-home line is asked with, and this
            # entry's other half ("safe", "protect", "how") is what makes the pair.
            "online"),
           ("how", "stop", "safe", "safer", "protect", "prevent", "should", "worth", "worried",
            "scam", "fraud", "risk")),
          "Use a virtual card: most banking apps make a one-off card number in a few taps, so the "
          "shop never holds the real details, and set a low limit on it. Where that is not offered, "
          "one card kept for online only, notifications on for every payment, and the real one "
          "frozen in the app between uses - most let you unfreeze it in seconds. Never save a card "
          "on a site you would not buy from twice, and check the last two digits and the merchant "
          "on any 'confirm this payment' prompt, because that is the step a scam tries to get you "
          "to tap through.",
          # What to carry abroad, and a child's first card, are other entries' questions.
          # Selling something and getting paid for it is the selling row in this file: a line that
          # says sell or buyer is not asking how to keep a card safe.
          avoid=("sell", "selling", "sold", "buyer", "buyers", "listing", "someone used my card", "fraud", "unauthorised", "i lost my card",
                 "lost my card", "money was taken", "cloned", "charged twice", "open a bank",
                 "abroad", "overseas", "travelling", "travel", "holiday", "in spain", "in italy",
                 "in france", "in greece", "in portugal", "in turkey",
                 "kids", "kid", "child", "children", "teenager", "teen", "my son", "my daughter")),

    # "is it worth getting a lodger" and the room-rent tax rule: a plain shrug on main.
    entry("lodger",
          (("lodger", "rent a room", "spare room", "room to rent", "take in a lodger",
            "rent out my spare room",
            # the same rule asked as a tax question, in the words of someone who already lets a
            # room: "do i pay tax on renting a room out" was the landlord's notice answer
            "renting a room out", "renting out a room", "rent out a room", "rent a room out",
            "renting my spare room", "let a room", "letting a room", "room tax"),
           ("worth", "should i", "tax", "how much", "allowed", "legal", "insurance", "much",
            "rules", "charge", "afford",
            # "do i have to declare rent from a lodger" and "is rent from a lodger taxable" were
            # a pointer to Citizens Advice: declaring is the same rule as the allowance
            "declare", "declaring", "declared", "taxable", "tax free", "tax-free", "report")),
          "The Rent a Room scheme makes the first £7,500 a year of rent tax free if you let a "
          "furnished room in the home you live in, and there is nothing to declare below that. "
          "Take a month's rent as a deposit and give a written licence agreement rather than a "
          "tenancy, so it stays easy to end. Tell your home insurer and, if you have one, your "
          "mortgage lender or landlord before anyone moves in.",
          avoid=("landlord", "tenancy", "flat share", "housemate", "buy to let")),

    # Keeping a uniform clean is money the tax office gives back, and the words for it are the
    # words of the washing: "how do i claim uniform tax relief" and "can i claim for washing my
    # uniform" both got the laundry-care answer, which is a good answer to a different question.
    # The claim words have to be in the line, so a plain "how do i wash my uniform" stays care.
    entry("uniform-tax-relief",
          (("uniform", "uniforms", "work uniform", "work clothes", "work clothing", "overalls",
            "protective clothing", "work boots", "laundry", "dry cleaning",
            "washing my uniform", "washing my work clothes", "clean my uniform"),
           # no bare "how" here: with "uniform" in the first group it made "how do i wash my
           # uniform" a tax claim, and the laundering row is the right answer to that one
           ("claim", "claiming", "tax", "allowance", "relief", "back", "rebate", "refund",
            "get back", "much", "can i", "deduct", "expenses", "entitled")),
          "HMRC gives a flat rate for a uniform you have to wear and wash: £60 a year for keeping "
          "it clean, £140 where it wears out quickly, and up to £18 a month for laundry if you "
          "wash a uniform with your employer's logo at home. Claim it on form P87 at gov.uk - it "
          "is free, takes about ten minutes, and you can go back four years, so the first claim is "
          "often a few hundred pounds.",
          # the care questions ("how do i get ink out", "it shrank", "it still smells") are the
          # cleaning row's, and they are the same words as the laundry half of this key
          avoid=("stain", "stains", "shrank", "shrunk", "shrink", "smell", "smelly", "iron",
                 "crease", "ink", "mud", "white", "grey", "dryer", "tumble", "fabric softener",
                 # a load left soaking is the laundry row's question, not a tax claim: "can i
                 # leave the laundry to soak overnight" reached this row on "laundry" + "can i"
                 "soak", "soaks", "soaking", "soaked", "overnight", "in water")),

    # A registry office wedding is the same legal ceremony for a fraction of the price.
    entry("registry-office",
          (("registry office", "register office", "civil ceremony", "town hall wedding",
            "wedding at the registry"),
           ("cost", "cheap", "cheaper", "how much", "better", "should", "worth", "book",
            "ceremony", "much",
            # "how do i get married at a registry office" names the office and asks the how:
            # the fees, the notice and the witnesses are this row's answer, not the guest list.
            "how do i get married", "how do we get married", "how to get married",
            "how do i marry", "how do we marry", "what do i need", "need to", "arrange",
            "witness", "witnesses", "notice", "legal")),
          "It is the same legally binding wedding, minus the venue: in England you give notice at "
          "your local register office (£46 each) and the ceremony at the register office itself "
          "costs about £57, against several hundred for a registrar to come to a hotel. You need "
          "two witnesses, the notice has to be given at least 29 days ahead, and the ceremony can "
          "be as short as you like, so the money can go on the meal or the honeymoon instead.",
          avoid=("divorce", "registry office hours", "birth certificate", "death")),

    # "how much should i give to charity" was the fundraising-page answer.
    entry("charity-giving",
          (("charity", "charities", "donate", "donation", "donations", "give to charity"),
           ("how much", "should i give", "give", "worth", "month", "tax", "gift aid", "much",
            "regular", "budget")),
          "Fix a monthly figure you would not miss - one or two per cent of your take-home pay is "
          "a common rule - and set it as a standing order so it does not cost a decision every "
          "time. Always tick Gift Aid if you are a UK taxpayer: it adds 25% at no cost to you, and "
          "higher-rate payers can claim the difference back. Look the charity up on the Charity "
          "Commission register first, and prefer ones that publish what share of income reaches "
          "the work rather than the fundraising.",
          # "how much should i give to charity" and "how do i raise money for charity" share
          # every word of their keys, so the giving answer wins by bias and the page-and-sponsor
          # answer keeps the lines that name a page, a run or a sponsor.
          bias=1,
          avoid=("fundraising page", "justgiving", "sponsor me", "funeral", "collection")),

    # Under-18s cannot hold an ordinary current account, which is its own question.
    entry("teen-account",
          (("bank account", "current account", "account for my teenager", "account for my son",
            "account for my daughter", "debit card"),
           ("teenager", "teen", "16", "17", "15", "14", "13", "12", "11", "child", "kids",
            "daughter", "son", "my daughter", "my son", "under 18")),
          "At 11 to 15 it is a child account in their name with you as the adult on it, and a "
          "debit card with no overdraft: every high street bank has one free, while the paid apps "
          "charge a few pounds a month for the same thing. At 16 they can open their own account "
          "with a full debit card, and at 18 it becomes an adult account, so check it is not one "
          "that quietly adds an overdraft. Set a standing order for pocket money on the same day "
          "each month, and let them see the balance rather than asking you for it.",
          avoid=("proof of address", "isa", "savings account", "business account")),
    # --- the everyday money asks people send that had no entry --------------
    # A rent rise, a lump sum, a charge you think is unfair, the price of a haircut, a school
    # trip, a tip, a night tariff, an hourly rate, money for a startup, a contract, the minimum
    # wage and the rent in London: each was the search hedge on main, and each is answered by
    # what the thing is and what to do about it, not by a figure the bot cannot check.
    entry("rent-increase", (("rent increase", "put the rent up", "put my rent up",
                             "puts the rent up", "raise the rent", "raising the rent",
                             "increase the rent", "increase my rent", "rent going up",
                             "rent rise", "rent review", "more rent"),
                            ("push back", "refuse", "say no", "negotiate", "disagree",
                             "challenge", "fair", "legal", "fight", "how much", "percent",
                             "per cent", "can i", "allowed", "notice")),
          ("You can push back, in writing. A landlord can only put the rent up by agreement, "
           "under a rent review clause in your tenancy, or with a formal notice - in England a "
           "section 13 notice, at least a month before it starts for a monthly tenancy, and no "
           "more than once a year. If the new figure is above what similar homes nearby are "
           "advertised at, say so, name two or three of them, and offer a lower number in "
           "writing. A notice can be referred to the rent tribunal (28 days in England, and the "
           "tribunal decides the market rent), and it does not apply if your tenancy has a rent "
           "review clause instead. Keep paying the current rent while you argue, so the dispute "
           "stays about the rise and not about arrears."),
          # a deposit, an eviction and a landlord who will not fix anything are other answers
          avoid=("deposit", "evict", "eviction", "section 21", "behind", "arrears", "repair",
                 "damp", "mould", "boiler")),
    # The same question arrives without an inheritance in it: "what should i do with my
    # savings", "i have 3k saved and no idea what to do with it", "i have 10 grand in savings
    # what next". Main sent the first two to the start-saving row, which tells someone who
    # already has the money to track two weeks of spending, and shrugged at the second. The
    # order of steps is the same answer, so it is the same row.
    entry("windfall-small", (("inherited", "inheritance", "lump sum", "windfall", "came into",
                              "left me", "bonus", "compensation", "payout",
                              "savings", "saved", "saved up", "some savings", "in savings",
                              "sat in", "sitting in", "doing nothing", "in my bank",
                              "in the bank", "spare cash", "spare money", "extra money",
                              # the same question with no word for where it came from: "i have
                              # some money, what should I do with it" and "i got some money for
                              # my birthday" both got "That's beyond what I know well"
                              "some money", "some cash", "got some money", "given some money",
                              "a bit of money",
                              # ... and the same question told as a size: "i have 2000 pounds
                              # what should i do with it" named the sum and nothing else, so it
                              # had no key word at all and got the shrug. A unit of money is the
                              # money, and the reply below reads the figure to size it.
                              "pounds", "quid", "grand", "thousand", "thousands",
                              "hundred pounds", "hundred quid", "a few hundred"),
                             # no "save" or "spend" here: a word another entry keys on is a word
                             # whose rarity this entry changes, and the goal-saving answer lost a
                             # turn that way ("and whats the best place to keep it while i save")
                             ("a few thousand", "thousand pounds", "what should i do",
                              "what do i do", "invest", "best thing", "with it",
                              "what now", "what next", "where should i", "what to do",
                              "no idea", "start")),
          _windfall_plan,
          # The size of the buffer and which account to hold money in are other rows, with a
          # number in the question rather than a plan for it.
          avoid=("house", "flat", "mortgage", "will", "probate", "funeral", "died", "death",
                 "how much", "how big", "how many", "enough", "sufficient", "cover", "covers",
                 "which account", "best account", "where should i keep", "where do i keep",
                 "where to keep", "rate", "aer", "interest", "tax", "taxed",
                 # A sum that is owed is not a sum looking for a home: "i have 2000 pounds of
                 # debt what should i do" and "i have a thousand pounds should i pay off my loan"
                 # read the figure and the money word, and the plan's first step (clear the
                 # credit card) is advice about money they do not have. The debt rows answer
                 # both, and they answered both before the sum was a key word.
                 "debt", "debts", "loan", "loans", "owe", "owes", "owing", "pay off",
                 "paying off")),
    entry("haircut-price", (("haircut", "hair cut", "a trim", "barber", "hairdresser"),
                            ("too much", "how much", "price", "cost", "expensive", "normal",
                             "usual", "fair", "worth", "much for")),
          ("Twenty pounds for a basic cut is normal in most of the UK: £12 to £20 at a barber or "
           "a local salon, £25 to £40 for a stylist or in a city centre, and more in London. So "
           "it is not too much unless it is a five-minute clipper cut with no wash. What is worth "
           "checking is what the price includes - a wash, a dry, a student or a weekday rate - and "
           "that the figure you were quoted is the one on the card machine."),
          # "how much do you tip a barber" is the tip question, not the price of a cut: the tip
          # table answers it, and a barber who gets a 20-pound answer is being told about the cut.
          avoid=("dog", "cat", "myself", "home", "grow", "growing", "thinning", "hair loss",
                 "grey", "dye", "colour", "tip", "tips", "tipping", "tipped", "gratuity",
                 "service charge",
                 # "the hairdresser cut too much off" is a complaint about the cut, not a
                 # question about the price: the two halves of this key are both in that line
                 "too much off", "too short", "cut too much", "took too much", "ruined",
                 "butchered")),
    entry("tipping-money", (("should i tip", "do i tip", "do you tip", "need to tip", "have to tip",
                       "tipping", "a tip", "gratuity", "service charge", "tip the",
                       # "how much do i tip a delivery driver" was an honest pass while "do i
                       # tip" reached the table: the price question in front of the tip needs
                       # the floor, and "much" alone ties with the cost rows.
                       "how much do i tip", "how much should i tip", "how much to tip",
                       "much to tip", "much do i tip", "much should i tip",
                       # "how do i work out a tip" asks for the arithmetic, not the norm, and
                       # the waste-site row was taking it for the tip on the other side of town
                       "work out a tip", "work out the tip", "work out a service",
                       "how do i tip", "how to tip"),
                      ("pub", "bar", "restaurant", "cafe", "taxi", "driver", "waiter",
                       "waitress", "hairdresser", "much", "normal", "expected", "rude",
                       "percent", "10", "should i", "do i",
                       # "what is a service charge" is the same table's question, and it was an
                       # honest pass: the second group needs one of these to reach the rows.
                       "what is", "whats", "what's", "compulsory", "optional", "discretionary",
                       "already on", "on the bill", "mean", "means",
                       # a bill in front of the person is the tip question too, and the sum is
                       # what it is worked out on: "how do i work out a tip on 84 pounds" reached
                       # nothing at all, while "how much should i tip on 84 pounds" answered it.
                       "bill", "bills", "the bill", "amount", "total", "on 84", "pounds",
                       "pound", "quid", "euros", "dollars")),
          # The same tip question reached two rows, and this one opened with the pub whatever was
          # asked, so "do you tip a taxi driver" was told about bar service. Both rows now lead
          # with the thing named in the line: the words are one table, in lifeadmin._tipping.
          _tipping,
          # a "tip" is also a hint, and those lines have their own answers
          # and a tip abroad is a different answer, decided by the country: "should i tip in
          # spain" was told to leave nothing in a pub, so the places hand it to travel's row.
          # "tips on" was one of these hint phrases, and the ending table lets "tips" reach the
          # "tip" of "a tip on a bill": the avoid word answered the gratuity line with nothing at
          # all. The hint reading is held by "tips for", "any tips", "top tips" and "tip of",
          # which need the phrase as typed, and a "tip on <something to do>" line reaches no
          # second key word here anyway.
          avoid=("tips for", "any tips", "tip for", "tips to", "top tips", "tip of",
                 "rubbish tip", "the tip",
                 # the place the council runs is not the money for a person: the waste rows have it
                 "council tip", "council dump", "council recycling", "local tip", "the dump",
                 "abroad", "overseas", "holiday", "on holiday", "while i am away",
                 "spain", "spanish", "italy", "italian", "france", "french", "portugal",
                 "greece", "greek", "germany", "german", "europe", "european", "netherlands",
                 "amsterdam", "paris", "rome", "tokyo", "japan", "japanese", "dubai",
                 "america", "american", "usa", "the us", "new york", "florida", "california",
                 "vegas", "mexico", "turkey", "egypt", "thailand")),
    entry("night-tariff", (("economy 7", "economy seven", "night rate", "off peak",
                            "off-peak", "cheap electricity", "night storage"),
                           # no "save", "car" or "charge": each is a key word of another money
                           # entry, and reusing one changes its rarity and so the ranking of a
                           # line that has nothing to do with this one
                           ("worth", "washing", "wash", "dishwasher", "night", "overnight",
                            "cheaper", "timer", "immersion", "off-peak", "night rate")),
          ("Usually yes, if your bill really has a night rate. Economy 7 gives about seven hours "
           "overnight at a lower unit rate - commonly around 00:30 to 07:30, but the hours differ "
           "by supplier and region and are printed on your bill or meter. A wash is roughly 1 to "
           "2 kWh, so at a night rate of 15p against 25p in the day you save 10 to 20p a load: "
           "worth a delay timer on the washing machine and the dishwasher, and it is the same "
           "window for an immersion heater or an electric car, where the saving is much bigger. "
           "The catch is a higher day rate, so if almost all your use is in the evening a "
           "single-rate tariff is usually cheaper."),
          avoid=("storage heater", "boiler", "hot water tank", "meter reading", "switch")),
    # "seed" on its own is a form of "seeds", so "how do i grow a lawn from seed" was answered
    # with how to raise money for a startup: the row matched "seed" and "how", which is every
    # seed-sowing line there is. A seed round is named by its own compound here, and the garden
    # words below are the second fence for a line that says what it is sowing.
    entry("startup-funding", (("raise funds", "raise money", "funding", "investor",
                               "investors", "startup loan", "crowdfunding", "grant",
                               "seed funding", "seed round", "seed money", "seed investment",
                               "seed investor", "seed investors", "pre-seed", "preseed"),
                              ("startup", "start up", "business", "company", "idea", "how",
                               "where", "best way", "should i")),
          ("Take the cheapest money first. Paying customers, then a startup loan - the British "
           "Business Bank backs £500 to £25,000 at a fixed rate through accredited lenders - then "
           "grants and competitions, then angel investors, and an overdraft or invoice finance "
           "last because it costs the most. Raise for 12 to 18 months of runway and a milestone "
           "that makes the next round possible, and keep six months of costs untouched as "
           "reserve. Have three things ready before you talk to anyone: your last 12 months of "
           "figures, a one-page forecast, and how much of the business you are willing to give "
           "away."),
          avoid=("charity", "charity fundraising", "sponsor", "cake sale", "school",
                 # a lawn, a border or a tray of seedlings is the garden's question
                 "lawn", "grass", "turf", "seedling", "seedlings", "sow", "sowing", "sowed",
                 "garden", "allotment", "vegetable", "vegetables", "flower", "flowers",
                 "compost", "greenhouse", "propagator")),
    # "how do i raise money for a new van" was given a JustGiving page: "raise money" plus
    # "how" is every one of these lines, and the thing being bought says which answer it is. A
    # cause is asked for by naming the charity or the sponsor, not by naming a van.
    # "do i need a survey when buying a house", "what about the survey" and "is a structural
    # survey worth it" were answered by the house-sale timeline, by the decision card's trade
    # between two lives and by a shrug: nothing named the survey itself. The lender's valuation
    # is the part people get wrong, so it is in the answer.
    # "what is a survey" asks what the thing is; "do i need a survey" asks whether to have
    # one. The row answered both with "Yes, have one done -", which is not an
    # answer to the definition, so the ask chooses between the two below.
    entry("house-survey", (("survey", "surveys", "surveyor", "structural survey",
                            "building survey", "homebuyer report", "homebuyer survey",
                            "condition report", "valuation", "snagging survey", "snagging"),
                           ("need", "worth", "how much", "cost", "costs", "price", "which",
                            "what", "should", "get", "do i need", "do i have to", "required",
                            # not "difference": "do we have to find the difference ourselves" is
                            # about the money after a low valuation, not about two reports, and
                            # it reached this card that way in a conversation
                            "level", "count as", "instead of", "what level"),
                           ("house", "houses", "flat", "flats", "buying", "buy", "purchase",
                            "purchasing", "mortgage", "offer", "moving", "old", "lender")),
          _the_survey,
          bias=1,
          # a car check, a questionnaire, a workplace survey and a survey of a removals firm are
          # not a survey of the house you are buying
          avoid=("car", "cars", "vehicle", "mot", "tyre", "tyres", "questionnaire", "feedback",
                 # a valuation they have already had is not a survey to book: "the mortgage
                 # valuation came back 5k under our offer" is about the offer, not about a report
                 "came back", "come back", "came in", "under our offer", "under the offer",
                 "under offer", "down valuation", "valued at", "valued below",
                 "staff", "employee", "employees", "colleague", "colleagues", "workplace",
                 "removal", "removals", "movers", "mover", "price comparison", "research",
                 "audience", "readership", "customer", "customers"),
          ),

    entry("money-for-a-big-buy", (("raise money", "raise the money", "raise funds",
                                   "get the money", "find the money", "pay for", "finance",
                                   "borrow", "afford", "save up", "loan"),
                                  # the thing being bought is what decides it: a phrase like
                                  # "how do i" here would score the same as the charity page
                                  ("van", "car", "house deposit", "deposit", "kitchen",
                                   "bathroom", "extension", "sofa", "wedding", "holiday",
                                   "bike", "laptop", "boiler", "new roof", "furniture",
                                   "washing machine", "tumble dryer", "fridge"),
                                  # the money is raised FOR the thing: without this part the
                                  # charity page's bare "how" scored the same as the van did
                                  ("for", "to buy", "buy", "buying", "towards")),
          ("Three rungs, in order. Save what you can each month first, then use a 0 per cent "
           "purchase credit card only if you can clear it inside the 0 per cent window, then a "
           "personal loan - the advertised rate starts around 6 per cent and is cheapest over "
           "7,500 pounds, and only 51 per cent of accepted applicants have to get it. For a "
           "deposit, a lifetime ISA adds 25 per cent to up to 4,000 pounds a year and must be "
           "open a year before you buy, and a 5 per cent deposit is the usual minimum. Price any "
           "car finance as a total: the monthly payment hides the interest. No payday loans."),
          # a service you pay for by the month is a subscription, not a purchase to finance:
          # "how do i stop paying for spotify" was reading "pay for" as buying a thing
          avoid=PAID_SERVICES + (
                 # "she keeps borrowing my car" is about a sister, not a loan: "borrow" is a
                 # money word here, and "car" is in the list of things being bought, so the two
                 # groups alone were enough for three rungs of credit and a personal loan. A
                 # person who keeps taking your things is the family file's line, and the shapes
                 # below only ever describe that.
                 "keeps borrowing", "keeps taking", "borrows my", "borrowing my",
                 "borrowed my", "takes my", "never returns", "never brings it back",
                 "wont give back", "won't give back", "lends out", "keeps using my",
                 # a subscription is not a big buy: "is it worth paying for cloud storage" reached
                 # three rungs of credit on the word "paying", and the tech row has the answer
                 "cloud", "icloud", "google one", "dropbox", "subscription", "subscriptions",
                 "netflix", "spotify", "streaming", "app store", "phone bill",
                 # money that is borrowed FROM someone is the family file's too
                 "off me", "off my", "off a friend", "off my mate",
                 # "redundancy pay for 8 weeks" is the pay a job owes, not a purchase: "pay for"
                 # is one of the names above, so the money a sacking or a redundancy pays out was
                 # reaching three rungs of credit rather than the row that holds the figures
                 "redundancy", "redundant", "severance", "statutory", "laid off",
                 "notice pay", "final wages",
                 "gym", "gyms", "membership", "memberships", "gym membership", "club",
                 "charity", "sponsor", "sponsored", "sponsorship", "fundraiser", "justgiving",
                 "cake sale", "raffle", "marathon", "10k", "half marathon", "school",
                 "school trip", "church", "startup", "start up", "business", "company",
                 "investor", "investors", "seed round", "equity", "shares",
                 # financing a car is the lease-or-buy comparison, which is more specific than
                 # three rungs and names the numbers for it
                 "car finance", "finance a car", "on finance", "car loan", "loan for a car",
                 "pcp", "lease", "leasing", "hire purchase", "contract hire",
                 # "should i buy a car outright or get a loan for it" is that comparison too
                 "outright", "loan for it", "a loan for it", "get a loan for",
                 # what a mortgage is and what it lends you is the mortgage explainer's line
                 "mortgage", "remortgage", "remortgaging",
                 # a check on the thing before you buy it is that check's own card, and "is it
                 # worth paying for an aa check on a car" was answered with three rungs of credit
                 "inspection", "inspections", "checked over", "pre purchase", "pre-purchase",
                 "aa check", "rac check", "vehicle check", "history check", "hpi",
                 "buyers report", "buyer's report", "test drive",
                 "survey", "surveys", "surveyor", "surveyors", "valuation", "snagging",
                 # "should i pay for debt advice" is a source question, and this row read "pay
                 # for" as a thing being bought and answered with three ways to raise the sum
                 "debt advice", "money advice", "advice about money", "advice on money",
                 "advice about debt", "advice on debt",
                 # "do i have to pay for the morning after pill" read "pay for" as a purchase
                 # to finance and answered with three ways to raise the sum: a prescription
                 # charge, a dentist and a test are the health file's lines, not a big buy
                 "pill", "pills", "morning after", "contraception", "plan b", "levonelle",
                 "ellaone", "condom", "condoms",
                 # the NHS item charge has its own card now, and three ways to raise the sum is
                 # the wrong answer to "do i have to pay for a prescription"
                 "prescription", "prescriptions", "pharmacy", "nhs charge", "prepayment",
                 # a price question is the thing's own card: "how much should i pay for a second
                 # hand washing machine" was three ways to raise the money, and the price card
                 # knows the three tiers and what to check before paying
                 "second hand", "second-hand", "used", "refurbished", "reconditioned",
                 "nearly new", "how much should i pay", "what should i pay", "how much is a",
                 "how much does a", "how much for a",
                 # "pay for" also covers who pays at a table, and three rungs is a wrong answer
                 # to that: "who should pay for dinner", "should i pay for my mates taxi" and
                 # "should i pay for my friends ticket" were all told to save, then use a 0 per
                 # cent card, then take a loan. The split and the friend-owes-me rows answer
                 # those; the thing being bought (a kitchen, a car, a deposit) keeps this one.
                 "dinner", "lunch", "meal", "restaurant", "drinks", "round of drinks",
                 "first date", "date night", "taxi", "cab", "mates", "mate", "friends",
                 "friend", "colleagues", "ticket", "tickets", "who should pay", "who pays",
                 "who should be paying", "whose turn", "whose round", "split the bill",
                 "split the cost", "split it", "going halves", "go halves",
                 # "how do i ask my parents for a loan" reads as buying: the loan is between two
                 # people, and the family row is the one that says how to ask for it
                 "parents", "parent", "mum", "mam", "dad", "father", "mother", "brother",
                 "sister", "family", "off my", "off a friend", "off my mate", "lend me",
                 "borrow off",
                 # "how do i stop paying for a subscription" read as buying a thing: a
                 # subscription that will not stop is lifeadmin's row, not three ways to raise
                 # a sum
                 "subscription", "subscriptions", "direct debit", "direct debits",
                 "gym membership", "streaming", "netflix", "spotify", "prime",
                 # a test fee is not a big buy: "how much should i pay for an mot" is the fee
                 # the cars table names, and this row answered it with three ways to raise the
                 # money. The MOT, the fee and the fine are all cars' lines.
                 "mot", "mot test", "mot check",
                 # "do i need to pay for roaming" is a phone service by the day, not a
                 # purchase to finance, and it tied with the roaming row on score and won on
                 # order: it answered with three rungs of credit and a lifetime ISA.
                 "roaming", "roam", "data roaming", "roaming charge",
                 "roaming charges", "roaming pass"),
          # the charity page and the startup row take "raise money" and "how" as readily as this
          # one does, and the thing being bought is the only thing that tells them apart
          bias=1,
          # one of the money words has to be in the line: "how do i save for a house deposit"
          # names the thing and reaches this row without ever asking to raise anything, and the
          # deposit answer is the better one
          # "afford" and "save up" are left out on purpose: "how do i afford a new bike" and
          # "how do i save up for a laptop" already have the work-backwards-from-the-date plan,
          # and it is the better answer to both
          ask=("raise money", "raise the money", "raise funds", "get the money", "find the money",
               "pay for", "finance", "borrow", "loan", "loans")),
    # "Where can I get a loan" is a source question, not a savings plan: the three rungs above
    # say what to do with the money, and this says who lends it. The ask word ("where", "best
    # place", "who") is half the key, so a plain "how do i get a loan" stays with the row about
    # what a loan costs.
    entry("where-to-borrow", (("where", "best place", "who", "which bank", "which lender",
                               "shop around", "cheapest place"),
                              ("loan", "loans", "borrow", "borrowing", "lend", "lender", "money",
                               "credit")),
          ("Your own bank first: ask for a personal loan quote, which is a soft search and leaves "
           "no mark on your file. Then a credit union, which caps interest at 3 per cent a month "
           "and is often the cheapest small loan, and a 0 per cent purchase card only if you can "
           "clear it before the offer ends. Dealer or store finance last, and never a payday "
           "lender: the daily rate can run past a thousand per cent a year."),
          # The line itself has to name borrowing. "money" used to sit in the key with no
          # ask, so a carried word from the turn above was enough: "im trying to save money"
          # then "where do i start" reached this row on the context alone and got loan quotes
          # instead of a savings plan. The source words ("where", "who", "which bank") are
          # half the key, so the ask only has to prove the other half is being asked here.
          # "where can i get money quickly" is the same question without a borrowing word, so
          # the phrases only a borrower uses are spelt out. Bare "money" would not do as the
          # ask: the ask sees the carried words too, which is the bug this guards against.
          ask=("borrow", "borrowing", "loan", "loans", "lend", "lender", "lenders", "credit",
               "money quickly", "money fast", "money now", "money today", "quick cash",
               "fast cash", "cash fast", "cash today"),
          avoid=("student", "student loan", "business loan", "startup", "mortgage", "remortgage",
                 "car finance", "car loan", "pcp", "lease", "leasing", "sorn", "mot")),
    entry("contract-before-signing", (("contract", "agreement", "terms and conditions",
                                       "the small print", "lease", "tenancy agreement"),
                                      ("before signing", "sign", "signing", "revise", "change",
                                       "amend", "negotiate", "check", "read", "get out of",
                                       "should i")),
          ("Ask for it in writing and do not sign the same day. Read the four clauses that cost "
           "people money: what you have to deliver and by when, how and when you get paid and "
           "what happens if they pay late, notice and termination, and who is liable for what. "
           "Mark up the ones you want changed, send the document back with your changes and a "
           "short note saying why, and get anything promised on the phone written in - an email "
           "saying they will cover it is worth more than a friendly call. For a lease, an "
           "employment contract or anything over a few thousand pounds, have someone who does "
           "this read it; a union checks an employment contract free, and Citizens Advice will "
           "look at most others."),
          # "signed" is a form of "sign", so it cannot be an avoid word here: it would turn the
          # entry down on the very line it is for. The ask is the guard instead - a contract
          # before it is signed is a revise, a check or a negotiate - and a line that says the
          # signing already happened carries none of those words.
          ask=("before signing", "before i sign", "before you sign", "revise", "change",
               "amend", "negotiate", "check", "read", "should i", "can i"),
          # "should i lease or buy" is a choice between two ways to pay, not a document to read:
          # the word "lease" plus "should i" reached this entry ahead of car-lease-or-buy.
          avoid=("lease or buy", "buy or lease", "lease vs buy", "buy vs lease", "lease versus",
                 "lease or purchase", "purchase or lease", "or pcp", "pcp or",
                 "already", "cancel", "cancellation", "breach", "break the contract",
                 # "should i lease or buy a car" carries the word lease and asks for a verdict on
                 # the money, which is `car-lease-or-buy`'s question, not a contract to revise
                 "lease or buy", "lease a car", "leasing a car", "buy a car", "buying a car",
                 "or buy", "pcp", "car finance", "car loan", "loan for a car", "hire purchase")),
    entry("minimum-wage", (("minimum wage", "national minimum wage", "minimum pay",
                            "living wage", "hourly minimum"),
                           ("what is", "how much", "per hour", "rate", "entitled", "should i",
                            "owed", "paid", "underpaid", "check", "enforce")),
          ("The rate changes every April, so check today's figure on the National Minimum Wage "
           "page on gov.uk - it is set by age band, lower for under 18s and apprentices and "
           "highest for 23 and over, and the National Living Wage is the 23+ rate. Your pay has "
           "to average at least that for every hour you actually work, including overtime, "
           "training and opening up, and unpaid time that pushes you below it is not allowed. If "
           "your payslip does not add up, HMRC enforces the minimum wage and takes complaints; "
           "keep your hours written down and raise it with your employer in writing first.")),
    entry("london-rent", (("average rent", "rent in london", "rents in london", "london rent",
                           "how much is rent", "rent for a flat"),
                          ("london", "average", "much", "one bed", "one bedroom", "flat",
                           "room", "zone")),
          ("As a rough guide, a one-bedroom flat is about £1,300 to £1,900 a month in outer "
           "London and £1,900 to £2,800 in inner London, with a room in a shared house around £700 "
           "to £1,100. It swings a lot by borough and by how close you are to a Tube line, so "
           "check live listings for the postcode rather than the city average - the ONS Price "
           "Index of Private Rents publishes the current figures by borough, and Rightmove or "
           "Zoopla will show what is actually available today. Budget a month's rent plus five "
           "weeks as a deposit, and check the deposit is protected.")),
    # "how do i claim on my holiday insurance" was answered with the homeworker's £6 a week:
    # "claim" is a bare key word on that entry, and insurance is not a tax claim.
    entry("insurance-claim-before-fix",
          (("insurance claim", "claim on my insurance", "claim on insurance",
            "claim on my holiday insurance", "claim on my travel insurance",
            "claim on my car insurance", "car insurance claim", "make a claim",
            "claiming on insurance", "insurance wont pay", "insurance won't pay",
            "claim was refused", "claim rejected"),
           ("how", "claim", "much", "should", "can i", "will", "pay", "refused", "rejected",
            "wont", "won't", "get", "worth")),
          "Tell the insurer the same day and photograph everything before anything is repaired or "
          "thrown away, because a claim reported late or after the fix is the one they refuse. Have "
          "the policy number, dates and receipts ready, expect the excess off the payout, and never "
          "admit fault to the other side - the insurer handles that. If they refuse or drag it out "
          "eight weeks, complain in writing and then take it free to the Financial Ombudsman.",
          # a house is its own entry, with its own excesses and rules; a car claim and a travel
          # claim are this entry's, because those entries are about the price of the cover. A
          # travel policy used to be fenced off here, which is how "how do i claim on my travel
          # insurance" and "my travel insurance wont pay out" ended up on the free GHIC card.
          avoid=("home insurance", "buildings", "contents", "boiler",
                 "washing machine", "phone", "laptop", "flight",
                 "cancelled flight", "baggage", "working from home", "tax"),
          bias=3),
    # "how do i get my money back from a builder" was answered with the shop's 30-day refund:
    # a person doing work is a service, and the route back is a letter and a small claim.
    entry("builder-dispute",
          (("builder", "builders", "tradesman", "tradesmen", "roofer", "plumber", "electrician",
            "decorator", "contractor", "workman", "the work was not done", "job was not done",
            "paid a deposit and", "took my deposit and"),
           ("money back", "refund", "rip off", "ripped off", "never came back", "not done",
            # "cowboy" is not in this list: "how do i avoid a cowboy builder" is the
            # how-to-pick question, and with this entry's bias the word alone took that line to
            # the small-claims speech. A line that complains names the deposit, the runner or
            # the bad job anyway, so dropping one word costs the complaints nothing.
            "did a bad job", "bad job", "complain", "sue", "small claims",
            "took my money", "unfinished", "half finished", "overcharged", "wont come back",
            "won't come back", "disappeared", "deposit")),
          # The answer comes first: this used to open on what the 30-day shop refund rule is not,
          # so a person asking how to complain was told about a rule that did not apply to them
          # before they were told what to do.
          "Write one complaint that names what was agreed, what was done and what it cost you, "
          "with photos and dates, and a deadline of 14 days to put it right - a builder is a "
          "service, so the shop's 30-day refund rule does not apply, and the letter is what gets "
          "the money back. Pay nothing more meanwhile, then claim through the small claims court "
          "online for anything under £10,000: it costs about £35, needs no solicitor, and most "
          "settle before the hearing. A trader who took a deposit and vanished is a police matter "
          "too - report it as fraud.",
          avoid=("shop", "bought", "online order", "delivery", "parcel", "amazon", "ebay",
                 "car", "garage", "mechanic",
                 # checking a trade before you hire one is not a dispute about work already done:
                 # "how do i check a builder before i pay a deposit" named a deposit and got the
                 # small-claims letter. The complaint lines name the bad job or the disappearing
                 # instead, so the picking asks can stand it down.
                 "how do i check", "how can i check", "how do i know if", "before i pay",
                 "before i book", "before i sign", "before i hire", "should i use",
                 "should i hire", "how do i pick", "how do i choose", "how do i find",
                 "trustworthy", "reputable", "legit", "cowboy"),
          bias=3),
    # "what is the 50 30 20 rule" reached nothing at all.
    entry("budget-rule",
          (("50 30 20", "50/30/20", "503020", "budget rule", "rule for budgeting",
            "how should i split my money", "how much should i save each month",
            "how much should i be saving"),
           ("what", "how", "much", "should", "save", "saving", "split", "rule", "month",
            "monthly", "percent", "percentage", "work", "explain")),
          "Half your take-home on needs (rent, bills, food, transport), 30% on wants (eating out, "
          "clothes, subscriptions) and 20% on saving and paying down debt. Take-home, not salary: "
          "on £2,200 a month that is £1,100, £660 and £440. If rent alone eats more than half, do "
          "not force the split - take the saving 20% out on payday first and fit the rest around "
          "it, and start that 20% at £20 if that is what you can do this month.",
          avoid=("diet", "calories", "protein", "exercise", "gym", "training")),
    # "how much should i spend on a car" reached nothing.
    entry("car-budget",
          (("spend on a car", "car budget", "how much for a car", "how much should i spend on a car",
            "afford a car", "budget for a car", "cheap car", "first car price", "car price"),
           ("how", "much", "should", "spend", "afford", "budget", "price", "cost", "first",
            "cheap", "good", "safe", "buy")),
          "Keep the car itself to about a quarter of your yearly take-home, and count the running "
          "costs before you set the price: insurance, road tax, MOT, tyres, servicing and fuel "
          "usually add £1,500 to £2,500 a year on top. For a first car £3,000 to £6,000 buys "
          "something safe enough - check the MOT history free on gov.uk, take someone who knows "
          "cars, and keep £500 back for the first repair. A cheap car with a big bill waiting is "
          "the expensive choice.",
          # Haggling for one is the price question, with its own entry: this one is about how
          # much car the money buys.
          avoid=("insurance", "lease", "leasing", "finance", "hp", "pcp", "sell", "sell my",
                 "part exchange", "running cost", "petrol", "diesel", "electric",
                 "haggle", "haggling", "bargain", "bargaining", "knock down", "negotiate",
                 "negotiating")),
    # "is it worth paying off my student loan early" was given the description of the loan.
    entry("student-loan-early",
          (("pay off my student loan", "overpay my student loan", "overpay student loan",
            "pay student loan early", "clear my student loan", "student loan early",
            "pay off student debt"),
           ("worth", "should", "early", "overpay", "clear", "pay off", "better", "save",
            "interest", "if i")),
          "Usually no: you repay 9% of what you earn above about £25,000 a year, whatever the "
          "balance, and anything left is written off after 40 years - so on an ordinary salary the "
          "extra money disappears into a debt you were never going to clear. It only makes sense as "
          "a high earner in your forties with a big balance you could clear outright, and even then "
          "check the write-off date first. Put the money into the pension match, a house deposit or "
          "an emergency fund instead.",
          avoid=("mortgage", "credit card", "loan shark", "car loan"),
          bias=3),
    entry("train-delay",
          (("train", "trains", "rail", "railway", "tube", "underground", "bus", "coach",
            "ferry", "ferries"),
           ("delayed", "delay", "late", "cancelled", "canceled", "cancellation", "missed",
            "strike", "refund", "money back", "compensation", "claim", "reclaim")),
          _late_leg,
          ask=("delayed", "delay", "late", "cancelled", "canceled", "missed", "refund", "claim",
               "compensation", "money back", "strike"),
          # buying a ticket, a railcard and where to sit are other questions, and a flight is a
          # different set of rules: "my flight was cancelled can i get my money back" was told to
          # claim Delay Repay from the train company, so the plane words hand it back.
          avoid=("buy", "cheap", "cheapest", "book", "booking", "railcard", "seat", "reserve",
                 "lose my job", "lost my", "sleeper", "freight",
                 "flight", "flights", "flying", "airline", "airlines", "plane", "planes",
                 "airport", "airports", "airfare", "easyjet", "ryanair", "british airways",
                 "jet2", "heathrow", "gatwick", "ba ",
                 # and a fare the employer pays back is an expenses claim, not a delay: "can i
                 # claim my train fare back from work" was told to claim Delay Repay.
                 "from work", "work trip", "business trip", "my employer", "employer",
                 "expenses", "expense", "reimburse", "reimbursement", "receipt", "receipts")),
    # --- what a death costs, and who to complain to -----------------------
    # "how much does a funeral cost" reached nothing at all: the family domain has the grief and
    # lifeadmin has the will, but the price of a funeral is a money question.
    entry("funeral-cost",
          (("funeral", "funerals", "funeral cost", "cremation", "burial", "bury my",
            "cremate", "cost of a funeral", "how much is a funeral", "funeral director",
            "funeral plan", "funeral plans"),
           ("cost", "costs", "much", "price", "pay", "afford", "cheap", "cheapest", "how",
            "what", "help", "who pays")),
          # what to say, what to read and what to write are not what a funeral costs:
          # "how do i write a poem for a funeral" was getting the £4,000 answer
          # (the avoid rows below stay where the money questions are)
          "A basic funeral in the UK is about £4,000 to £5,000 all in, roughly £3,800 to £4,200 "
          "for a cremation and over £5,000 for a burial once the plot and the fees are counted, "
          "and extras like flowers, cars and a wake come on top. Three things cut it: ask two or "
          "three local funeral directors for their full price list (they must give you one), "
          "choose a direct cremation at about £1,500 if there is no service wanted, and check "
          "whether the person had a prepaid plan or a funeral notice in their will. If you are on "
          "a low income, the council's Funeral Expenses Payment covers a bare funeral and can be "
          "claimed from the bereavement service; a surviving partner may also get Bereavement "
          "Support Payment.",
          # grief, the will and what to say to the family are other domains' lines, and so is
          # anything written or read out at the service
          avoid=("died", "passing", "passed away", "grief", "grieving", "sympathy", "condolence",
                 "what do i say", "will", "probate", "wake", "flowers to send",
                 # "what is a good song for a funeral" is the music row's question, not the price
                 "song", "songs", "music", "tune", "hymn", "hymns", "playlist",
                 "poem", "poems", "verse", "rhyme", "eulogy", "speech", "reading", "write a",
                 "write my", "say at", "what to say", "words for", "order of service")),
    # "how do i complain about my bank" was a shrug: the energy and water complaints had answers,
    # and the bank one is the same shape with a different ombudsman.
    # "how do i close my bank account" had no answer of its own: the energy exit-fee card took it,
    # and once that was guarded off the line got a shrug. Closing an account is its own job.
    entry("close-account",
          (("close", "closing", "closed", "shut", "shutting", "get rid of"),
           ("bank account", "current account", "savings account", "building society account",
            "bank", "building society", "account")),
          "Open the new one first and let the Current Account Switch Service move it: the switch "
          "takes seven working days, closes the old account for you and redirects payments for "
          "three years. If you would rather just shut it, clear any overdraft and check nothing is "
          "due in or out, move the Direct Debits and standing orders yourself, then ask in writing "
          "and keep the final statement. A joint account needs both of you to agree.",
          ask=("close", "closing", "closed", "shut", "shutting", "get rid of"),
          # an energy, water, broadband or gym account is a contract with an exit fee, and a credit
          # card, a loan, a pension or an ISA has its own rules: none of them is a bank account.
          # An app account is not a bank account: "how do i close my facebook account" was told to
          # let the Current Account Switch Service move it.
          avoid=("energy", "gas", "electricity", "water", "broadband", "mobile", "phone", "gym",
                 "credit card", "card", "loan", "mortgage", "pension", "isa", "help to save",
                 "business", "company", "subscription", "insurance", "council tax", "rent",
                 # an account somebody held who has died is settled with the death certificate,
                 # not with the switch service
                 "died", "death", "deceased", "bereaved", "widow", "widower", "funeral",
                 # an online account is closed on the site, not with a switch service: "how do
                 # i close my amazon account" was told to open another bank account first. The
                 # names come from one list, with "app" and "online account" alongside them.
                 "app", "apps", "email account", "online account",
                 # a phone-maker and a software company are app accounts too
                 "apple", "microsoft", "icloud", "office 365", "microsoft 365")
                + APP_ACCOUNT_WORDS),

    entry("bank-complaint",
          (("complain about my bank", "complain about a bank", "complain about the bank",
            "complaint about my bank", "complaint about a bank", "complaint about the bank",
            "complain to my bank",
            "my bank is ignoring me", "bank wont help", "bank won't help", "bank refusing",
            "bank complaint", "financial ombudsman", "complain to the bank", "bank charged me",
            "unfair charge", "bank charged"),
           ("how", "complain", "complaint", "ombudsman", "refund", "charge", "charged",
            "ignoring", "refusing", "help", "much", "back")),
          "Complain to the bank first, in the app or by phone, and ask for the complaint reference: "
          "they have eight weeks to give you a final answer. If they have not settled it by then, "
          "or you do not accept what they say, the Financial Ombudsman Service takes it on free and "
          "independently, and you have six months from their final answer to go there. Keep the "
          "dates, the amounts and what you were told each time. A charge you did not agree to, a "
          "fraud the bank refused to refund and a mis-sold product all go the same way.",
          # an insurance claim, an energy bill and a shop refund have their own answers
          avoid=("insurance", "energy", "water", "broadband", "mobile", "shop", "refund for",
                 "guarantee",
                 # "how do i avoid bank charges" and "why did my bank charge me" want the charge
                 # explained and stopped, not the eight-week complaint route: that is the
                 # bank-charges row below, and "bank charged me" is in this key
                 "how do i avoid", "avoid the charge", "avoid bank charges", "avoid charges",
                 "why did my bank charge", "why has my bank charged", "why have i been charged",
                 "stop the charge", "stop being charged"),
          # The generic escalation entry also scores 6 on "how do i complain about my bank":
          # this answer is the one with the complaint reference, the eight weeks and the
          # six-month window, so it has to beat the generic card on its own ground.
          bias=2),
    # A bank charge is not a complaint until the bank says no: "how do i avoid bank charges" and
    # "why did my bank charge me" were both the eight-week complaint route, which is what to do
    # after asking, not before. The kinds of charge are different questions with different fixes,
    # so the answer opens with the statement.
    entry("bank-charges",
          (("bank charge", "bank charges", "bank fee", "bank fees", "overdraft fee",
            "overdraft fees", "overdraft charge", "overdraft charges", "unarranged overdraft",
            "arranged overdraft", "failed direct debit", "direct debit bounced", "bounced payment",
            "bounced direct debit", "monthly account fee", "packaged account", "account fee",
            "card fee", "cash machine fee", "atm fee", "charges on my account", "charged me"),
           ("how do i", "how to", "why", "avoid", "stop", "refund", "waive", "charged",
            "charging", "much", "back", "claim", "reduce", "get out of", "dispute")),
          "Read the name of the charge on the statement first, because they are different "
          "problems: an unarranged overdraft fee, a bounced direct debit, a card fee abroad and a "
          "monthly account fee all have different fixes. Ask for the first one back - banks have "
          "to treat you fairly, and most refund a first unarranged overdraft charge if you ask in "
          "the app or on the phone, before it becomes a complaint. Then stop the next one: turn on "
          "a low-balance text alert, set the direct debit for a day after payday, and check "
          "whether the paid overdraft or the packaged account fee is buying anything you do not "
          "already have, because both can be cancelled. If the bank refuses, ask for the complaint "
          "to be logged and take it to the Financial Ombudsman, which is free.",
          ask=("how do i", "how to", "why", "avoid", "stop", "refund", "waive", "reduce",
               "charged", "charging", "claim"),
          # "how do i get an overdraft fee refunded" was the faulty-goods card, because "refund"
          # is what that card is built on: a named charge outweighs the general refund rule
          bias=1,
          avoid=("insurance", "energy", "water", "broadband", "mobile", "shop", "flight",
                 "council tax", "parking", "scam", "fraud", "loan", "mortgage", "rent",
                 "credit card interest", "late payment")),
    # "what is a credit union" reached nothing, and it is the answer to a loan at 40% APR.
    entry("credit-union",
          (("credit union", "credit unions", "cooperative bank", "co-op bank", "not for profit loan",
            "community bank"),
           ("what", "how", "join", "borrow", "loan", "save", "worth", "better", "use",
            "safe", "find", "difference")),
          "A credit union is a savings and loan club owned by its members, not a bank: it takes "
          "deposits from the people in it and lends only to them, so the interest goes back to the "
          "members instead of to shareholders. Loans are capped by law at 3% a month (42.6% APR), "
          "which is far below a payday lender and often below a doorstep one, and savings are "
          "protected by the same FSCS guarantee as a bank up to £85,000. You join through a common "
          "bond - a workplace, a union, a postcode or a church - and findyourcreditunion.co.uk "
          "lists the ones open to you.",
          avoid=("switch bank", "best bank account", "overdraft", "mortgage", "student loan")),
    # "how do i open a student bank account" had no entry: the teenager's account and the first
    # credit card were both answered and this one was not.
    entry("student-account",
          (("student account", "student bank account", "student current account",
            "student overdraft", "student account overdraft", "bank account for university"),
           ("open", "best", "which", "how", "much", "overdraft", "free", "worth", "get",
            "should", "apply", "choose")),
          "Open it once you have your place confirmed, because the good ones only run while you "
          "are a student: you need your passport or driving licence plus proof of address and the "
          "UCAS or university letter. Choose on the interest-free overdraft, not the free railcard: "
          "£1,500 to £3,000 is normal in the first year, it usually rises each year and then tapers "
          "off about a year after you graduate, when the interest starts. Ask what the rate becomes "
          "after that, keep the account for your student loan and your rent, and open a normal "
          "savings account alongside it for anything you are not spending.",
          avoid=("child", "teenager", "my son", "my daughter", "savings account", "isa",
                 "switch bank")),

    entry("stamp-duty",
          (("stamp duty", "stamp tax", "sdlt", "stamp duty land tax", "land tax",
            "land transaction tax", "land and buildings transaction tax", "lbtt", "ltt"),
           ("what is", "whats", "what does", "how much", "how does", "explain", "mean", "rate",
            "rates", "bands", "band", "pay", "pays", "owe", "cost", "costs", "on", "price",
            "first time",
            "buying", "buy", "house", "home", "flat", "property", "second home", "buy to let",
            "works", "work", "changed")),
          _stamp_duty, bias=1,
          # the deposit, the mortgage and the move are other answers, and a stamp on a letter or
          # a stamp collection is not a tax on a house
          avoid=("deposit", "mortgage", "afford", "save", "saving", "moving", "removals",
                 "rent", "landlord", "council tax", "stamp collection", "postage",
                 "post office", "stamps for", "loyalty")),


    # A state pension is not paid because you reached the age: there is a claim, and the line
    # "how do i claim my state pension" was scoring `claim` and `how do i` and landing on the
    # homeworker's tax relief. It is its own answer, with the years you need and the forecast.
    entry("state-pension-claim", (("state pension", "pension age", "my pension age"),
                                  ("claim", "get", "apply", "when", "how", "age", "qualify",
                                   "start", "receive", "due", "entitled", "go about", "sign up")),
          # "when can i claim my state pension" is a question about the age, so the age is the
          # first thing said: the claim letter is the second half of the same answer.
          "The State Pension starts at 66 now, and 67 for anyone reaching that age from 2028. It "
          "is not automatic: you should get a letter about two months before you get there, and if "
          "it does not come, claim online at gov.uk (Get your State Pension) or ring the Pension "
          "Service. You need 10 qualifying National Insurance years to get anything at all and 35 "
          "for the full new amount, about £11,500 a year, and a forecast at "
          "gov.uk/check-state-pension shows where you stand, because gaps can often be filled "
          "with voluntary contributions.",
          # "when can i claim my state pension" also reaches `retire-how-much` through
          # "state pension" and "when can i", and the amount-in-the-pot answer is a different
          # question from the date you can claim: the date wins.
          bias=3,
          ask=("claim", "get", "apply", "when", "how", "age", "qualify", "start", "receive",
               "due", "entitled", "sign up"),
          # a workplace pension, a pot and a transfer are other answers
          avoid=("workplace", "employer", "opt out", "contribution", "pot", "transfer",
                 "private pension", "how much should i pay",
                 # The date you can claim is this entry's line; the amount, the record and the
                 # number of years are the pot answer's, and each of them carries "state
                 # pension" and a "how" too. They say so in their own words and stand this one
                 # down, because a figure answered with a claiming procedure is a fact answered
                 # with a process: "how much is the state pension" wants the £230 a week, and
                 # "how many years do i need" wants the 35.
                 "how much", "how many years", "years do i need", "record", "forecast",
                 "statement", "projection", "qualifying", "full state pension")),

    # The pension scam is a shape, not a subject: a call, a letter, a "free review", a promise
    # of a better return, and pressure to move the pot quickly. What a person wants is the
    # checks, because the money is usually gone once it moves.
    entry("pension-scam", (("pension", "pensions", "annuity", "annuities", "pension pot",
                            "retirement pot", "sipp"),
                           ("scam", "scams", "scammed", "scammer", "fraud", "fraudster",
                            "phishing", "cold call", "rang me", "rang about", "called me",
                            "called about", "phoned", "a call", "letter", "check", "real",
                            "knocked", "knocking", "doorstep", "called round", "rang her",
                            "called her", "rang him", "called him", "bank details",
                            "gave her bank", "gave his bank", "gave my bank",
                            "sent the money", "paid them", "money gone", "released",
                            "legit", "genuine", "offer", "too good", "pressure",
                            # a transfer is not a scam shape: "should i transfer my final salary
                            # pension" and "how do i transfer my pension to a new provider" are
                            # both questions about doing it, and the warning reads as a refusal
                            # to answer them. The signal words carry the row without it.
                            # the pot being moved is the scam's own shape when nobody asked
                            # how to do it ("someone told me to transfer my pension"), and the
                            # how-to question stands the row down in `avoid` below
                            "transfer my pension", "move my pension", "move the pot",
                            "wants me to", "want me to", "urged", "pushing me",
                            "pressure to move", "pressure to transfer")),
          _pension_scam,
          bias=2,
          ask=("scam", "scams", "scammed", "fraud", "cold call", "rang", "called", "phoned",
               "a call", "letter", "check", "real", "legit", "genuine", "offer", "pressure",
               "knocked", "knocking", "doorstep", "bank details", "gave",
               "money gone", "released", "text", "texted", "wants me to",
               "want me to", "urged", "pushing me",
               # the gate is the asking shape, and the how-to transfer lines that reach it
               # are stood down by `avoid`
               "transfer"),
          # the state pension, a workplace pension and "is my pension safe" (which is the
          # defined-benefit explanation) are other answers
          avoid=("state pension", "workplace", "employer", "opt out", "how much", "when can i",
                 "pension age", "how much is", "is my pension safe", "protected",
                 # checking your own record is the forecast answer's business, not a scam:
                 # "how do i check my pension forecast" has "check" in it and nothing dubious
                 "forecast", "record", "statement", "projection", "qualifying years",
                 # "check" alone is the one word that reads in both directions, and the
                 # check-on-your-own-pot sense is the commoner of the two: "how do i check my
                 # pension", "how do i check my pension pot" and "what is my pension worth"
                 # were all told that nobody legitimate cold-calls about a pension, which
                 # answers a question the person did not ask and leaves theirs unanswered.
                 # The scam keeps the offer shape - a call, a letter, a firm to look up - and
                 # the checking phrases go to the statement answer below.
                 "check my pension", "check my pot", "check my pension pot",
                 "check what my pension", "check how much", "check what i have",
                 "my pension worth", "how much is my pension", "is my pension worth",
                 "how much have i got", "how much is in my pension", "what is my pension worth",
                 # how to do a transfer is a how-to question with an advice answer, and the
                 # scam card in reply reads as a refusal to answer it
                 "how do i transfer", "how to transfer", "how do i move my pension",
                 "should i transfer", "can i transfer", "is it worth transferring",
                 "should i move my pension", "how do i move")),

    # A parent's pension is a family job as much as a money one, and "my mum keeps ringing me
    # about her pension" was taking the boundaries answer - the right script for a parent who
    # rings too much, and the wrong one for a parent with a money worry.
    entry("parent-pension-help", (("mum", "mother", "mam", "dad", "father", "gran", "nan",
                                   "grandma", "grandad", "parent", "parents", "mother in law",
                                   "father in law"),
                                  ("pension", "pensions")),
          "Do three things with them, once, and the phone calls get shorter: their State Pension "
          "forecast at gov.uk/check-state-pension, a free Pension Wise appointment if they are 50 "
          "or over, and a list of every pension they have ever paid into, because old employers' "
          "schemes are the ones people forget. Then agree who handles what, so it is one "
          "conversation instead of a worry every week.",
          # main's `nuisance-calls` keys "keeps ringing", so "my mum keeps ringing me about her
          # pension" was answered with the telephone preference service: this one outranks it
          bias=3,
          ask=("pension", "pensions"),
          avoid=("scam", "scammed", "being scammed", "cold call", "letter", "who is right",
                 "knocked", "knocking", "doorstep", "called round", "rang her", "called her",
                 "rang him", "called him", "bank details", "gave", "paid", "money gone",
                 "released", "text", "fraud")),

    # --- what a separation costs, and what a death leaves behind -----------
    # "how much does a divorce cost" reached nothing: the family domain has the feelings and
    # lifeadmin has the will, but the price of ending a marriage is a money question.
    entry("divorce-cost",
          (("divorce", "divorcing", "separating", "separation", "dissolution",
            "end my marriage", "get divorced"),
           ("cost", "costs", "how much", "price", "expensive", "cheap", "cheaper", "fee",
            "fees", "afford", "lawyer", "solicitor", "court", "process", "start", "file",
            "paperwork", "sort out")),
          "Budget about £600 for the court fee in England and Wales - £593 to apply, and a "
          "further £275 only if a judge has to decide the money - plus £1,000 to £3,000 for a "
          "solicitor on a simple, agreed split, or nothing if you do the forms yourselves. If "
          "you agree everything, a mediator at a few hundred pounds a session is far cheaper "
          "than two solicitors arguing, and the financial consent order that makes the split "
          "final is the part to spend money on, because without it a claim on a pension or a "
          "house can come back years later. Check whether you qualify for help with the fee "
          "before you pay it, and if there is any risk of violence, get advice before you file.",
          # the feelings, the children and the housing are other answers
          avoid=("feel", "feeling", "sad", "cry", "crying", "lonely", "children", "kids",
                 "child", "custody", "access", "who gets the house", "where do i live",
                 "wedding", "getting married", "propose")),
    entry("inheritance-tax",
          (("inheritance tax", "inherit", "inheritance", "iht", "estate", "estates"),
           ("how much", "threshold", "avoid", "reduce", "tax", "owe", "pay", "paying",
            "limit", "rules", "couple", "married", "house", "home", "gift", "gifts", "gifting",
            "seven years", "over")),
          _the_inheritance_tax,
          # a will, a pension and probate are their own answers
          avoid=("will", "probate", "funeral", "pension", "writing a will", "power of attorney")),
]
# Paying for an older person's care is one of the questions families ask most, and main answered
# it with the wrong card twice: "will i have to sell the house to pay for care" and "does the
# council pay for care" both got the savings-and-credit-card ladder, "what help can i get with
# care costs" got the frozen-vegetables answer, and both care-assessment lines were the search
# hedge. The care home's weekly price was already answered, so these two rows are the other half:
# how the council decides what you pay, and how to ask for the assessment that starts it.
# "what help can i get with care costs" is not the same question as "will i have to sell the
# house": one wants what is there to claim, the other wants what the council counts. Both rooms of
# the answer are here, and which one comes first is the ask's job, so the reply reads the line.
_CARE_HELP_WORDS = ("what help", "any help", "help with", "help towards", "entitled",
                    "qualify", "claim", "benefits", "benefit", "support", "contribute",
                    "pay for it", "afford it", "get any money", "anything available")
_CARE_COSTS_MEANS = (
    "The council looks at the person's own income, savings and property, not the family's: in "
    "England, savings over £23,250 means paying the full cost, under £14,250 the council ignores "
    "them, and in between it counts £1 a week of income for every £250 - so a house is not sold "
    "on the first day, and a deferred payment agreement lets the council put a charge on it and "
    "take the money from the estate instead. The house is ignored completely while a husband, "
    "wife or civil partner lives there, and it is always ignored for care in your own home. Ask "
    "for the financial assessment and the care needs assessment in writing, and get the free "
    "check from Age UK or Citizens Advice before signing anything.")
_CARE_COSTS_HELP = (
    "Claim what is paid whatever the savings first, then let the council's assessment do the "
    "rest: Attendance Allowance if the person needs help day to day and is over State Pension "
    "age (PIP daily living below it), Pension Credit and the council tax reduction that comes "
    "with it, and NHS continuing healthcare if the need is mostly health. The council part works "
    "on the person's own money: in England, savings over £23,250 means paying the full cost, "
    "under £14,250 the council ignores them, and in between it counts £1 a week for every £250, "
    "so a house is not sold on the first day and a deferred payment agreement puts a charge on it "
    "and takes the money from the estate instead. Ask for the financial assessment and the care "
    "needs assessment in writing, and get the free check from Age UK or Citizens Advice before "
    "signing anything.")


def _care_costs_answer(memory, reading):
    """What there is to claim, when that is what was asked; what the council counts, otherwise."""
    said = ""
    if isinstance(reading, dict):
        said = str(reading.get("clean") or reading.get("text") or "").lower()
    if any(word in said for word in _CARE_HELP_WORDS):
        return _CARE_COSTS_HELP
    return _CARE_COSTS_MEANS


ENTRIES.append(entry(
    "care-costs-and-the-house",
    (("pay for care", "paying for care", "care costs", "care cost", "care fees", "care home fees",
      "nursing home fees", "council pay for care", "council pays for care", "fund the care",
      "funding for care", "means test", "means tested", "means-tested", "financial assessment",
      "self funding", "self-funding", "sell the house", "sell my house", "sell the home",
      "sell the bungalow", "deferred payment",
      # the "what is there to claim" wording: a bare "claim" would take "can i claim carers
      # allowance for my mum", so the phrase is written with the care in it
      "claim for care", "claim towards care", "claim towards her care", "claim towards his care",
      "claim for her care", "claim for his care", "claim for my mum", "claim for my dad",
      "claim for my mother", "claim for my father", "money towards care", "money towards her care",
      "help towards care", "help with care costs", "help paying for care"),
     ("care", "care home", "nursing home", "home", "help", "pay", "pays", "cost", "costs",
      "how", "what", "will i", "do i", "does", "can we", "afford", "money", "savings",
      "pension", "house", "qualify", "entitled", "who pays", "my mum", "my dad", "my nan",
      "my gran", "my mother", "my father", "mother", "father", "parent")),
    _care_costs_answer,
    # the weekly price of a home, the care itself and a will are other answers
    avoid=("how much", "how much does", "per week", "a week", "weekly", "average cost",
           "care home", "nursing home", "care assessment", "needs assessment", "will",
           "probate", "inheritance tax", "power of attorney"),
    bias=2))
# The way in: the assessment nobody asks for because nobody has told them it exists.
# The key says "carer assessment", not "carers assessment": the plural shares its stem with the
# Carer's Allowance row, and with it in the key "can i get carers allowance for looking after my
# mum" was pulled off that row onto this one, which is a real loss - the allowance is what that
# person asked about. The matcher already reads the plural of a key word, so the singular answers
# "how do i get a carers assessment" and leaves the allowance alone.
ENTRIES.append(entry(
    "care-assessment",
    (("care assessment", "care needs assessment", "needs assessment", "assessment from the "
      "council", "social services", "adult social care", "care package", "help at home",
      "home help", "home care", "carer assessment", "reablement"),
     ("what is", "whats", "how do i", "how to", "how can i", "get", "get one", "ask for",
      "arrange", "apply", "who do i", "where do i", "qualify", "entitled", "mean", "involves",
      "start", "request")),
    "Ring the council's adult social care team and ask for a care needs assessment: it is free, "
    "anyone can ask for one, and it is the door to everything else - help with washing and "
    "dressing, a carer coming in, day centres, equipment, a pendant alarm, and the financial "
    "assessment that decides what is paid. The person has to agree to it, so ask them first and "
    "go with them, and write down the bad days rather than the good ones: what they cannot do "
    "without help, and what happens on a day nobody is there. The decision comes in writing, and "
    "if it says they do not qualify it can be challenged. Ask for a carer's assessment for "
    "yourself in the same call - it is separate, and it is your own support, not theirs.",
    # the money side and the care home are the other row, and a medical assessment is not this
    avoid=("pip", "attendance allowance", "benefit", "benefits", "how much", "means test",
           "means tested", "financial assessment", "sell the house", "care home", "nursing home",
           "nhs", "gp", "hospital", "school", "child", "children", "special needs", "ehcp"),
    bias=2))
# Borrowing had a row for the card-to-loan comparison and for a loan to clear cards, and nothing
# for the plainest form of the question: "how do i get a loan with bad credit", "can i get a loan
# on universal credit" and "how do i get a loan" all reached the "free money advice covers this"
# punt, after the wrong rows were stood down. The row answers the question underneath all three:
# what to compare, and where the cheap end of the market is.
# Money back for a payment that went wrong: the card, the direct debit and the transfer are one
# question with the same two steps, and nobody had a row for it, so "how do i reverse a payment"
# was told how to parallel park and then, once that was fixed, given an honest shrug.
ENTRIES.append(entry(
    "reverse-a-payment",
    (("payment", "payments", "charge", "charges", "transaction", "transactions", "refund",
      "money", "direct debit", "standing order", "subscription", "transfer"),
     # "reverse" is the word people use for it, and it is not a car's word here
     ("reverse", "reversed", "reverse a payment", "reverse a charge", "undo", "undone",
      "get back", "claim back", "claim a refund", "chargeback", "money back", "dispute",
      "disputed", "wrongly", "by mistake", "double charged", "scam", "scammed",
      # A bare "twice" is the count of both a battery and a payment: "i charge my phone twice a
      # day" was handed the chargeback letter because "charge" and "twice" sat in the two lists.
      # The count is the same word either way and it is said before or after the money - "the
      # payment went through twice", "the payment is there twice" - so the row keeps it and the
      # fence is the battery's own words (`_a_payment_count`), not a list of money phrases.
      "twice", "two times", "double",
      "charged twice", "charged me twice", "charge twice", "twice on my card",
      "twice on my statement", "twice on my bill", "twice for the same", "double the charge",
      "two charges", "billed twice", "billing twice", "bill me twice")),
    "Ask the seller first, in writing, and say what went wrong and what you want - most refunds "
    "are done there and it is the step both the card and the bank will ask about. If they will not, "
    "go to your card issuer and use the word chargeback: card rules give you 120 days from the "
    "transaction, or from when the goods should have arrived, and the issuer reverses the payment "
    "while it investigates. A direct debit is faster still - the bank must refund an unauthorised "
    "one straight away and a wrong amount the same day - and a payment sent to the wrong account "
    "is the bank's recall, which works best in the first hours. Keep every message.",
    # a subscription you want to stop, a debt, a wage and a car are other rows, and the parking
    # row owns the other sense of "reverse"
    avoid=("cancel", "cancelling", "cancel my", "stop paying", "subscription i", "debt", "wage",
           "salary", "payslip", "mortgage", "loan", "car", "cars", "parking", "park",
           "diabetes", "hair", "decision", "policy",
           # a deposit is money held, not a payment that went wrong: "can i get my money back
           # from a deposit scheme" is the itemised deductions and the scheme's dispute service,
           # and a chargeback has nothing to do with it
           "deposit", "deposits", "deposit scheme", "tenancy deposit", "holding deposit",
           "security deposit", "damage deposit"),
    bias=1,
    guard=_a_payment_count))

ENTRIES.append(entry(
    "getting-a-loan",
    (("loan", "loans", "lender", "lenders", "borrow", "borrowing", "borrowed", "lend", "lends",
      "lending", "lend me", "guarantor"),
     ("how do i get", "how can i get", "can i get", "get a loan", "getting a loan", "need a loan",
      "want a loan", "take out a loan", "take a loan", "apply", "applying", "application",
      "bad credit", "no credit", "credit history", "credit score", "on benefits",
      "universal credit", "refused", "turned down", "where can i", "will anyone",
      "who will lend", "how do i borrow", "how to borrow", "worth it", "should i")),
    ("Compare the APR and the total repayable rather than the monthly payment: £5,000 at 8 per "
     "cent over three years comes back as about £5,650, and a longer term lowers the payment while "
     "raising that total. Your own bank and a credit union are the cheap end, and a credit union "
     "lends on your circumstances rather than a score, so bad credit is not an automatic no. A "
     "guarantor helps more than a payday lender, where £300 for a month can cost £90; if you are "
     "already behind, StepChange gives free advice before you borrow again."),
    # the card, the mortgage, the car and the student loan each have their own row, and borrowing
    # off your own family is the next row along
    avoid=("credit card", "cards", "card", "overdraft", "mortgage", "car", "cars", "house",
           "flat", "deposit", "wedding", "holiday", "business", "student",
           "consolidate", "consolidation", "payday", "loan shark", "friend", "friends", "mate",
           "mum", "dad", "parents", "brother", "sister", "family", "lent me",
           # "should i overpay my loan" is about a loan already taken out, and how to borrow
           # cheaply answers a question they are past
           "overpay", "overpaying", "overpayment", "pay off early", "paying off early",
           "paid off early", "settle early", "settlement figure", "early repayment")))

# A debt between family is the one where people ask how to say it, and nothing answered: "how do i
# borrow money from my parents" and "should i borrow money from my mum" were both the honest
# shrug while the lender's side of the same debt has had a row for a while.
ENTRIES.append(entry(
    "borrowing-from-family",
    (("parents", "parent", "mum", "mam", "mother", "dad", "father", "brother", "sister",
      "family", "in laws", "in-laws", "grandparents", "gran", "nan", "aunty", "uncle",
      "relatives", "my folks", "folks"),
     ("borrow", "borrowing", "lend", "lending", "loan", "a loan", "some money", "for money",
      "money off", "help me out", "pay back", "repay", "ask", "asking", "off them", "from them",
      "sub me", "borrow off", "borrowed off", "loan off", "lend off", "a loan off",
      "off my mum", "off my dad", "off my parents", "off my brother", "off my sister",
      # "how do i talk to my parents about money" and "how do i bring up money with my parents"
      # were going to the household-bills script, which is written for a partner or a house
      # share ("the broadband comes to 32 a month and your half is 16"), not for a parent.
      "talk about money", "talk money", "about money", "money with", "bring up money",
      "money talk")),
    ("Ask for one defined sum and say when you will pay it back, in a message rather than at the "
     "end of a meal: 'could you lend me £400 until the 28th, and I'll pay £100 a week'. Say what "
     "happens if you miss one, and ask whether they can afford it, because a loan between family "
     "is where the row starts. Put it in writing, and for a big sum sign a simple note with the "
     "amount, the date and the repayments: it protects both of you. Never borrow it for spending."),
    # a parent who keeps asking for money, an inheritance, a care home and a power of attorney are
    # all money-and-family questions with their own rows, not this one
    avoid=("keeps asking", "keeps borrowing", "always asking", "asks me for", "asked me for",
           "wants money", "her rent", "his rent", "their rent", "gambling", "care home",
           # a family row about money is not a loan: "my parents argue about money" is the
           # argument, and the amount-and-date script answers the wrong question there
           "argue", "argues", "arguing", "argument", "row", "rows", "fight", "fighting",
           "shouting", "furious", "divorce", "divorcing", "separated",
           "carer", "power of attorney", "inheritance", "will", "funeral", "benefits",
           "universal credit", "credit score", "pension", "house", "deposit", "wedding")))
# "how do i talk about money with my partner" was a shrug. The bills script answers what to pay
# and the borrowing row is for a parent; the conversation itself - when, what to bring, how to keep
# it from being a row - had no row.
ENTRIES.append(entry(
    "money-talk-partner",
    (("talk about money", "money talk", "money conversation", "conversation about money",
      "talk money", "bring up money", "talk finances", "talk about finances",
      "conversation about finances", "money with my", "money and my partner",
      # only the talking shapes: the split-the-bills and joint-account rows already own money +
      # a partner, and a bare "money" here took "how do i talk to my partner about anything"
      "budget with my", "spend with my", "savings with my", "how do we talk about money"),
     ("partner", "husband", "wife", "boyfriend", "girlfriend", "fiance", "fiancee", "other half",
      "talk", "talking", "conversation", "bring up", "raise", "discuss", "tell", "open up",
      "approach", "ask")),
    ("Pick a calm time, not the moment a bill lands, and put the numbers on the table: what comes "
     "in, what goes out, and what is left. Ask what they want to be true in a year - a deposit, a "
     "holiday, less stress - before you talk about cuts, because a shared goal is what makes the "
     "figures a plan rather than an accusation. Agree one rule you both keep: a joint account for "
     "the bills with a set monthly amount in it, personal accounts for the rest, or everything in "
     "one pot, and whichever it is, both of you can see it. Say what you are worried about in "
     "plain words ('I am scared about the card bill') rather than about them ('you always spend'). "
     "If a debt is already in one name only, say so now: a plan made together is the only kind "
     "that survives a bad month. And if money is being hidden or controlled, that is not a "
     "budgeting problem - talk to someone you trust and to a free adviser."),
    ask=("partner", "husband", "wife", "boyfriend", "girlfriend", "fiance", "fiancee",
         "other half", "how", "what", "should", "when", "help"),
    # a parent asking for money, a joint account's paperwork and a divorce are their own rows
    avoid=("parents", "my mum", "my dad", "my son", "my daughter", "inheritance", "will",
           "divorce", "divorcing", "separated", "care home", "benefits", "universal credit",
           "credit score", "pension", "wedding", "funeral", "business partner",
           # the bills script owns the bills question, and a joint account's paperwork and a
           # "who earns more" argument are not this conversation either
           "split", "splitting", "who pays", "joint account", "separate accounts", "earns more",
           "earn more", "argue", "argues", "arguing", "argument", "shouting",
           # a line with no money in it at all is a relationship question
           "about anything", "about us", "about the kids", "about his mum", "about her mum",
           "stop talking", "wont talk", "won't talk", "refuses to talk",
           # wording.py's household-money script already answers "bring up money" and "talk to
           # my partner about money"; this row is for the shapes that script missed
           "bring up money", "talk to my partner about money", "talk to my husband about money",
           "talk to my wife about money", "talk to my boyfriend about money",
           "talk to my girlfriend about money"),
    bias=1))

def _scam_steps(memory, understood):
    """Reporting a scam and getting money back are the same job in two orders."""
    text = str(((understood or {}).get("clean") or (understood or {}).get("text") or "")).lower()
    money = any(w in text for w in ("money back", "get it back", "refund", "recover", "reclaim",
                                    "lost", "stolen", "took", "taken"))
    # "how do i report a scam" asks for the report first: the money-back reply led with the bank,
    # which is right for money gone and a step behind for a report
    if not money and any(w in text for w in ("report", "reporting", "action fraud", "police",
                                            "tell someone", "where do i")):
        return ("Report it to Action Fraud on 0300 123 2040 or at actionfraud.police.uk - the "
                "police do not take scam reports directly - and tell your bank even so, because a "
                "payment that has not left can still be stopped. Keep every message, phone number "
                "and payment reference: the report needs the sender's details, the date and the "
                "amount. If it came through a text or an app, forward it to 7726 and block the "
                "number.")
    return ("Ring your bank the same day: a transfer can sometimes be stopped before it leaves, "
            "and the reimbursement rules for authorised push-payment scams mean most banks have "
            "to refund you. Then report it to Action Fraud on 0300 123 2040, and keep every "
            "message, phone number and payment reference. Change the password on whatever account "
            "it came through. Never pay anyone who rings offering to get the money back: that is "
            "the same scam running again.")


# Money taken by a scam has its own steps and its own clock, and none of the refund rows have it:
# "how do i get my money back from a scam" was answered with the shops' 30-day faulty-goods law.
ENTRIES.append(entry(
    "money-back-from-a-scam",
    (("scam", "scams", "scammed", "scammer", "scammers", "fraud", "fraudster", "conned",
      "con artist", "ripped off", "ripped me off", "push payment"),
     ("money back", "refund", "recover", "reclaim", "get it back", "back", "lost", "stolen",
      "bank", "report", "what do i do", "how do i", "help", "paid", "transferred", "transfer",
      # what a con takes: "a con artist took my savings" names no ask word, and the loss is the
      # question ("con artist took my savings" was a shrug)
      "took", "taken", "stole", "savings", "wiped out", "cleaned out",
      # "i was scammed out of 500 pounds" was an empathy reply ("that's a lot to carry"),
      # and the amount is the whole reason the bank needs to hear today
      "scammed out of", "conned out of", "out of my account", "out of my savings")),
    _scam_steps,
    # a shop that will not refund and a card payment that went wrong are the chargeback rows, and
    # a scam call about a tax rebate is the fraud line, not the money that has already gone
    avoid=("chargeback", "section 75", "seller", "shop", "retailer", "warranty", "faulty",
           "never arrived", "wrong size", "returns", "scam call", "scam text", "phishing",
           "is this a scam", "text saying", "rang me", "called me", "pension", "bin men",
           # a dish: "chilli con carne", "tacos con queso" and "sin carne" all carry a word the
           # key holds in a longer form - "conned" folds to "con", so a two-letter dish word was
           # read as a man who takes money (see _forms)
           "carne", "con queso", "chilli sin", "non carne",
           # checking a trader before paying is the other direction, and it is not money gone:
           # "how do i tell if a website is a scam" was being told to ring the bank
           "is this shop", "is this site", "is this website", "website is", "site is",
           "shop is", "company is", "trader is", "store is", "legit", "trustworthy",
           "never heard of", "too good to be true", "dodgy", "genuine", "safe to buy",
           "buy from",
           # feeling like a fraud at work is work.py's imposter card, and this key holds the
           # bare "fraud" beside "how do i", so "how do i stop feeling like a fraud" was told
           # to ring the bank about a transfer. The feeling phrases, never the bare word.
           "like a fraud", "feel a fraud", "feeling a fraud", "imposter", "impostor",
           "imposter syndrome", "impostor syndrome", "out of my depth", "found out")))


def _prize_answer(memory, understood):
    """Answer the prize that arrived before the money did."""
    text = str(((understood or {}).get("clean") or (understood or {}).get("text") or "")).lower()
    # "i won a competition i never entered" is the same scam with the proof built in, and the
    # first sentence should say so rather than land on the fee test afterwards
    if any(w in text for w in ("never entered", "did not enter", "didnt enter", "didn't enter",
                              "never applied", "never signed up", "never signed up for",
                              "dont remember entering", "do not remember entering",
                              "never put my name")):
        return ("You cannot win a competition you never entered, so that is a scam: send nothing, "
                "ring nobody, and do not confirm your details to sort out the winnings. Real "
                "lotteries, draws and prize sites publish winners themselves and never ask a "
                "winner for a fee, a delivery charge or bank details first. Keep the message and "
                "report it to Action Fraud on 0300 123 2040, and forward a suspicious text to 7726.")
    return ("Nothing genuine asks you for money first: a fee, a 'release charge', a tax payment or "
            "your bank details before a prize arrives is the whole scam. Send nothing, do not ring "
            "the number in the letter or text, and check the organisation through a number you "
            "find yourself rather than the one they gave you. A real draw publishes its winners "
            "and pays by the method you entered with. Keep everything and report it to Action "
            "Fraud on 0300 123 2040, and forward a suspicious text to 7726.")


# The two shapes that use the same words and are not the scam, kept beside the row that would
# otherwise answer them: a win of the person's own being talked about ("i won a prize and they
# emailed me about it") and a relative's win told by the relative ("my sister texted me that she
# won a prize"). Both are the same patterns `bot/compose/goodnews.py` stands down on, so the
# composer's congratulations and this row agree about the line instead of both reading it.
_ABOUT_THE_WIN = re.compile(
    r"\b(?:about|over)\s+it\b|\bto\s+(?:tell|let)\s+me\b|\bto\s+say\b|\bconfirming\b"
    r"|\bwell\s+done\b|\bcame\s+after\b|\bafterwards\b|\bthe\s+details\b"
    r"|\bto\s+let\s+us\s+know\b", re.I)
_A_RELATIVE_TOLD_ME = re.compile(
    r"\b(?:(?:my|our)\s+)?(?:sister|brother|son|daughter|mum|mam|mother|dad|father|friend|mate|partner|"
    r"husband|wife|colleague|girlfriend|boyfriend|cousin|nan|gran|granny|aunt|uncle|niece|"
    r"nephew|neighbour|neighbor)\b.{0,40}?\b(?:texted|texts|messaged|messages|told|tells|"
    r"called|calls|rang|rings|phoned|phones|wrote|whatsapped|emailed|emails)\b.{0,20}?"
    r"\b(?:me|us)\b", re.I | re.S)


# The order is the tell, the same way it is in the composer: a message that claims a win ("i got a
# text saying i won a prize") is the scam, and a win the person is telling you about, with the
# message that came after it ("i won a prize at work and they emailed me the details"), is not.
_A_WIN = r"(?:won|win|winner|winnings|prize|prizes|jackpot|lottery|competition|sweepstake)"
_A_MEDIUM = (r"(?:text|texts|texted|message|messages|email|emails|letter|letters|call|phone call|"
             r"voicemail|whatsapp|dm|notification)")
_A_MESSAGE_THAT_CLAIMS_A_WIN = re.compile(
    r"\b" + _A_MEDIUM + r"\b(?:(?!" + _A_WIN + r").){0,60}?\b" + _A_WIN + r"\b", re.I | re.S)
_A_WIN_THEN_A_MESSAGE = re.compile(
    r"\b" + _A_WIN + r"\b(?:(?!" + _A_MEDIUM + r").){0,60}?\b" + _A_MEDIUM + r"\b", re.I | re.S)
_ASKS_FOR_SOMETHING_BACK = re.compile(
    r"\b(?:fee|fees|pay|paid|send|transfer|wire|release|admin|processing|clearance|customs|"
    r"bank details|account details|card details|sort code|final notice|get in touch|"
    r"contact us|text them|text back|call them|ring them|reply|respond|confirm your)\b|£",
    re.I)


# A relative's unclaimed inheritance is the third thing the same words are made of: "i got a
# letter saying i have an unclaimed inheritance worth 500,000" is the scam the windfall is
# promised in, so money left by a stranger in a message is a claim too.
# The verb as well as the noun: "a letter saying i inherited 500,000 and must pay a release fee"
# held "inherited", and the pattern held only "inheritance", so the claim never reached the test
# and the threshold figure came back to a person being asked for money first.
_MONEY_LEFT = r"(?:inherit\w*|windfall|unclaimed|bequest|next of kin|beneficiary)"
_A_MESSAGE_THAT_CLAIMS_MONEY = re.compile(
    r"\b" + _A_MEDIUM + r"\b(?:(?!" + _A_WIN + r").){0,60}?\b" + _MONEY_LEFT + r"\b",
    re.I | re.S)
_A_WIN_NAMED = re.compile(r"\b" + _A_WIN + r"\b", re.I)
# The money-left words as a pattern, not as the bare string: `_MONEY_LEFT in text` compares the
# pattern source with the line and is never true, so the branch below was dead for the case it
# was written for (`my inheritance is being held and i must pay a fee`).
_MONEY_LEFT_NAMED = re.compile(r"\b(?:" + _MONEY_LEFT + r")\b", re.I)
# "you have won a lottery you never entered" carries the proof of the scam in the line itself and
# asks for no money, so it is the scam whatever else is in it.
_NEVER_ENTERED = re.compile(
    r"\b(?:never|did not|didnt|didn't|do not|dont|don't)\s+(?:enter|entered|apply|applied|"
    r"sign up|signed up)\b", re.I)


# Money going out, in the words the letters actually use: "i must pay a fee", "a clearance fee to
# receive my inheritance", "before they will release the money", "they want a fee". `tax` is left
# out on purpose: "do i pay tax on an inheritance" is a tax question, and the row that owns it
# answers it. Asking for bank details to pay a win out is the same scam in another wording, and it
# was answered with a transfer app before (`you have inherited 900,000 pounds please send your
# bank details`).
_MONEY_OUT = re.compile(
    r"\b(?:pay|paid|paying|send|sending|wire|transfer|hand over)\b(?:(?!\b(?:it|them)\b).){0,40}?"
    r"\b(?:fee|fees|charge|charges|clearance|deposit|bank details|account details|"
    r"card details|sort code)\b"
    r"|\b(?:fee|fees|charge|charges|clearance|release|held|withheld|deposit|processing|admin|"
    r"bank details|account details|card details|sort code|upfront|up front)\b"
    r"|£", re.I)
# A question about the tax is not the scam even when it holds a figure: "how much inheritance tax
# on a £500,000 estate" is the estate row's question. The scam says what is happening to this
# person, so a line that asks what the tax is, or how much, stands down before the money-out test.
_TAX_ASKED = re.compile(
    r"\b(?:how much|how many|what|whats|what's|when|why|which|is|are|does|do|do i|can i|"
    r"should i|explain|threshold|rate|rules)\b[^.?!]{0,40}\btax\b", re.I)

_BANK_DETAILS_ASKED = re.compile(
    r"\b(?:bank details|account details|account number|sort code|card details|bank account|"
    r"iban|swift)\b", re.I)
_A_WIN_OR_AN_INHERITANCE = re.compile(
    r"\b(?:" + _A_WIN + r"|inherit\w*)\b", re.I)


# A dead person's estate is settled by paying the tax before anything is released, so a line that
# names the probate steps is the estate being wound up and not a claim that wants a fee: the tax
# answer is the answer for it. "my solicitor says i need to pay inheritance tax before they release
# the estate" must not be read as the scam that "before they will release the money" is.
_THE_ESTATE_BEING_WOUND_UP = re.compile(
    r"\b(?:solicitor|solicitors|probate|executor|executors|executrix|conveyancer|"
    r"grant of probate|letters of administration|the estate|my late|"
    r"my (?:father|mother|dad|mum|husband|wife|partner|uncle|aunt|gran|grandad|nan) "
    r"(?:has )?died|died (?:last|in)\b)", re.I)


def _a_prize_and_a_bill(understood):
    """True when the win in the line arrived with money to send before it comes in.

    The key holds the words of the scam - a win, and money going out - and those are also the
    words of ordinary questions: "inheritance" and "tax" together are what "what is inheritance
    tax" is made of, and the row took it and answered a tax question with "Nothing genuine asks
    you for money first" (main, #6898). So the win has to be *claimed*: in a message that
    arrived, or named outright with money asked for beside it. A line that says only what a
    thing is has neither, and stands down to the row that owns it.
    """
    text = str(((understood or {}).get("clean") or (understood or {}).get("text") or "")).lower()
    if not text:
        return True
    if _ABOUT_THE_WIN.search(text) or _A_RELATIVE_TOLD_ME.search(text):
        return False
    if _TAX_ASKED.search(text):
        return False
    if _A_MESSAGE_THAT_CLAIMS_A_WIN.search(text) or _A_MESSAGE_THAT_CLAIMS_MONEY.search(text):
        return True
    if _NEVER_ENTERED.search(text):
        return True
    if _A_WIN_THEN_A_MESSAGE.search(text):
        return bool(_ASKS_FOR_SOMETHING_BACK.search(text))
    # A win or an inheritance named outright is the scam only when the same line asks for money
    # back: "youve won 200,000 send us the release fee" is, and "what is inheritance tax" is not.
    if _BANK_DETAILS_ASKED.search(text) and _A_WIN_OR_AN_INHERITANCE.search(text):
        return True
    if _A_WIN_NAMED.search(text) or _MONEY_LEFT_NAMED.search(text):
        return bool(_MONEY_OUT.search(text))
    return False


# A prize that arrives with a bill attached is the one scam a person reads as good news: "a letter
# says i won a prize but i need to send a fee" was congratulated - "Love that, well done" - because
# the only thing the line shared with the knowledge base was the winning. The mark of the scam is
# the money going out before the prize comes in, so that pair is the key, and the medium (a letter,
# a text, an email, a call) is what comes with it.
ENTRIES.append(entry(
    "prize-that-wants-a-fee",
    (("prize", "prizes", "competition", "competitions", "lottery", "sweepstake", "raffle",
      "jackpot", "winnings", "winner", "won", "win", "selected", "inheritance", "inherit",
      "inherited", "windfall",
      "unclaimed", "prize draw", "draw"),
     ("fee", "fees", "pay", "paid", "payment", "send", "send money", "wire", "transfer",
      "bank details", "account details", "card details", "details", "claim", "claim it",
      "collect", "release", "admin fee", "processing fee", "delivery fee", "clearance",
      "charges", "deposit", "tax", "text saying", "text says", "email saying", "email says",
      "letter says", "letter saying", "letter from", "says i need to", "says i have to",
      # a message about a win rarely uses the word "text" as a noun: "someone texted me that i
      # won a competition", "emailed to say i had won", "told me i had won a holiday"
      "texted", "texted me", "messaged", "messaged me", "emailed", "emailed me",
      "told me i won", "told me i had won", "telling me i won", "telling me i had won",
      "to say i won", "to say i had won", "saying i have won", "saying i had won",
      "says i must", "asking for", "asked for", "asking me to", "they want", "want me to",
      "never entered", "did not enter", "didnt enter", "didn't enter", "whatsapp",
      "final notice", "delivery charge", "customs")),
    _prize_answer,
    # A raffle someone is running, a quiz night, a charity draw and a birthday present are the
    # other half of the same words, and none of them is a message that arrived out of the blue.
    avoid=("how do i run", "how to run", "organise", "organize", "raise money", "fundraiser",
           # the named taxes and gifts are their own rows: "what is inheritance tax", "how much
           # is inheritance tax", "is a gift to my son taxable" are questions about the tax, and
           # the prize row's key holds "inheritance" and "tax" from the windfall scam
           "capital gains", "tax return", "self assessment", "stamp duty",
           "council tax", "national insurance", "tax code", "taxable", "gift tax", "owe tax",
           "charity", "raffle tickets", "sell tickets", "tombola", "quiz", "prizes for",
           "prize for", "birthday", "christmas present", "gift", "gifts", "school fair",
           "cake stall", "hamper", "what should i", "ideas",
           # "inheritance" is in the key because a letter about an unclaimed estate is the same
           # scam, and with "tax" in the second part it took the real questions too: "how do i
           # avoid inheritance tax" and "how much can i give away before inheritance tax" were
           # both told that a fee before a prize is the whole scam. Inheritance tax is the
           # inheritance row's question, and a scam letter never words itself as one.
           "inheritance tax", "iht", "7 year rule", "seven year rule", "avoid inheritance",
           "reduce inheritance"),
    guard=_a_prize_and_a_bill,
    bias=3))

def _transfer_time(memory, understood):
    """Answer the transfer that was asked about first: a UK one, or one going abroad."""
    text = str(((understood or {}).get("clean") or (understood or {}).get("text") or "")).lower()
    # "how long does a chaps payment take" asks about the big same-day payment by name, and the
    # Faster Payments answer would be a different scheme: CHAPS is same-day or next day, not
    # seconds, and it costs money.
    if "chaps" in text:
        return ("CHAPS is the same-day one, for house deposits and car money: sent by about 3pm "
                "on a working day it lands that day, and after that it is the next working day. "
                "It costs £20 to £30 a transfer, the bank may ring you to confirm it, and it is "
                "the wrong scheme to use for a few hundred pounds - Faster Payments is free and "
                "arrives in seconds.")
    if any(w in text for w in ("international", "overseas", "abroad", "another country",
                               "europe", "usa", "america", "australia", "india", "spain")):
        return ("An international transfer takes one to three working days, and it can sit in a "
                "check for longer if the bank wants more detail. Send it before about 4pm on a "
                "working day, because after that it is really being sent tomorrow, and expect a "
                "fee plus a poor exchange rate. A UK transfer is much faster: Faster Payments "
                "lands in seconds, even if the first payment to a new payee can be held a few "
                "hours.")
    return ("A UK transfer over Faster Payments normally lands in seconds and is almost always "
            "there the same day, though a bank can hold the first payment to a new payee for a few "
            "hours while it checks. CHAPS is for big same-day payments and costs a fee. An "
            "international transfer takes one to three working days, and anything sent after "
            "about 4pm is really being sent tomorrow.")


# "how long does a bank transfer take" was the honest shrug, and it is one of the few questions
# where the answer is a number of hours.
ENTRIES.append(entry(
    "bank-transfer-time",
    (("bank transfer", "faster payment", "faster payments", "chaps", "international transfer",
     "transfer", "transfers", "send money", "sent money", "money arrive"),
     ("how long", "long", "take", "takes", "arrive", "arrives", "arriving", "when", "instant",
      "same day", "next day", "hours", "days", "how quickly", "why is it")),
    _transfer_time,
    # the money that never came from a buyer is the selling answer, and money someone took is the
    # scam answer
    avoid=("scam", "scams", "scammed", "fraud", "buyer", "buyers", "sold", "selling", "ebay",
           "paypal", "cheque", "cash", "wages", "salary", "payslip", "benefits", "overseas",
           "abroad", "fees", "fee")))
ENTRIES += [
    # "what is a maintenance loan" is the size of the number and who pays it back, not the form:
    # the application entry above answers the form, and this one answers the amount.
    entry("maintenance-loan",
          # a maintenance grant is not a loan: the amount below is the loan, so the word is left
          # out and a grant question stays unclaimed rather than answered with the wrong number
          (("maintenance loan", "living costs loan", "money for living costs",
            "student living costs", "loan for rent at uni"),
           ("what is", "how much", "how does", "do i get", "will i get", "how big", "enough",
            "cover", "pay back", "repay", "interest", "mean", "mean tested", "means tested",
            "based on", "parents income", "household income")),
          "It is the part of student finance that pays your rent and food, and it is paid to you, "
          "not the university: roughly £10,000 a year if you live away from home outside London, "
          "around £13,000 in London, and less if you live with your parents - check the figure for "
          "your year on gov.uk, because it moves. How much of it you get depends on your household "
          "income, so two people on the same course get different amounts. You repay it only once "
          "you earn over the threshold, then 9% of what is above it, and the balance is written off "
          "after around 40 years.",
          avoid=("apply", "application", "deadline", "when do i apply", "how do i apply"),
          # "how much maintenance loan do i get" ties with the application entry above, which
          # answers the form rather than the amount
          bias=1),
    # The scheme people are sold when a mortgage is out of reach. The answer is what it costs,
    # because the seller never puts that in the headline.
    entry("lease-purchase",
          (("lease purchase", "rent to own", "rent to buy", "buy in instalments", "owner rent",
            "option to buy", "tenancy with option"),
           ("what is", "how does", "worth it", "should i", "good idea", "risky", "safe",
            "scam", "catch", "how does it work", "explain", "help")),
          "It means paying a deposit plus rent now for the right to buy at a set price later, and "
          "the catch is that the right is often the seller's to keep: miss a payment, or the "
          "market moves, and you can lose the deposit and the extras you paid. There is no "
          "regulator for it the way there is for a mortgage, so have the contract read by a "
          "solicitor before you sign anything, and check who holds the deposit. Saving into a "
          "Lifetime ISA, which adds 25% to what you put in, gets you to a mortgage with less risk. "
          "The government's Rent to Buy for a home is a different thing and not this: rent at 80% "
          "of the market rate for five years with the option to buy, through a housing association "
          "- ask your council whether any of it exists where you live.",
          avoid=("car", "van", "lease a car", "pcp", "hire purchase", "phone", "washing machine",
                 "sofa", "furniture", "laptop")),
    # "i need to borrow money" has no "where" in it, so the lender ladder never saw it, and the
    # chasing wording of `family.lent-money` answered it instead - telling somebody who wants to
    # borrow to ask themselves when they will pay it back.
    entry("borrow-how", (("borrow", "borrowed", "borrowing", "a loan", "loan"),
                         ("i need", "i want", "how do i", "how can i", "can i", "could i",
                          "best way", "should i", "is it", "money", "pounds", "quid",
                          "get")),
          _borrow_how,
          # being owed it, lending it out and a student loan are other answers
          avoid=("owe", "owes", "owed", "lent", "pay me back", "pay it back", "pay back",
                 "student loan", "student", "mortgage", "car loan", "car finance", "my friend",
                 "my mate", "my brother", "my sister", "my mum", "my dad", "my son",
                 "my daughter", "off me", "from me", "to me", "off you",
                 # the lender ladder is the answer to a "where" ask and keeps it, and borrowing
                 # from a pension, a renovation and a "worth it" call are other questions
                 "where", "where to", "pension", "renovate", "renovation", "worth",
                 # a car bought on a loan is the car-costs answer, which is about the car
                 "car", "cars", "van", "motorbike",
                 # `getting-a-loan` is the fuller answer to shopping for one - the APR against
                 # the total repayable, a guarantor, bad credit - and it keeps those lines; this
                 # row is only for the borrower's own ask, which had no answer at all
                 "take out a loan", "took out a loan", "get a loan", "getting a loan",
                 "got a loan", "apply for a loan", "loan application", "need a loan",
                 "want a loan", "bad credit", "no credit", "credit score", "credit history",
                 "guarantor", "on benefits", "a loan for",
                 # finishing a loan is the other half of a loan: "can i pay off a loan early"
                 # was main's overpayment answer, and it must keep it
                 "pay off", "paying off", "paid off", "pay it off", "pay off a loan",
                 "early", "earlier", "overpay", "overpayment", "overpaying",
                 "settle", "settled", "settling", "clear it early", "repaid", "repay early",
                 # and getting out of one is a different question again: "how do i get out of a
                 # loan" is the loan's own answer on main and "can i cancel a loan after signing"
                 # is the free advice card's 14-day right to cancel
                 "get out of", "out of", "cancel", "cancelling", "canceling", "cancelled",
                 "canceled", "signed", "signing", "14 days", "cooling off")),

    # --- starting a pension, and the pot already there ------------------------
    # "pension" above answers every pension line with the same three sentences, and on the lines
    # below that was a confident answer to a question nobody asked: "my employer doesnt offer a
    # pension" was told to pay in 5% and get 3% from the employer it had just said has no scheme,
    # "how much should i have in my pension at 30" was told to check the fund, and "what is a
    # sipp" got the shrug. Each shape gets its own row, and each one opens with its own answer.
    entry("pension-work-has-none",
          (("pension", "pensions"),
           ("doesnt offer", "does not offer", "dont offer", "no pension at work", "no scheme",
            "no workplace pension", "no company pension", "none at work", "has no pension",
            "have no pension", "wont offer", "won't offer", "not eligible", "not entitled",
            "never offered", "offer nothing", "never joined", "not joined", "havent joined",
            "didnt join", "never signed up",
            # the refusal itself, which is the same question as no scheme at all
            "wont pay", "won't pay", "wont pay into", "won't pay into", "refuses",
            "refusing", "refused", "stopped paying", "not paying", "hasnt paid",
            "hasn't paid", "wont enrol", "won't enrol", "employer wont", "employer won't",
            "my employer refuses", "my employer stopped")),
          "Ask HR in writing which pension scheme you are in and how to join it: if you are 22 or "
          "over and earn more than 10,000 pounds a year, the duty to enrol you is theirs, and a "
          "flat no is worth challenging rather than accepting. If there really is no scheme, open "
          "a personal pension or a SIPP yourself and pay in what you can - the government adds "
          "20% to what a basic-rate taxpayer puts in, and the years already on your national "
          "insurance record still count towards the state pension.",
          bias=3),
    entry("pension-how-much-in",
          (("pension", "pensions", "pension pot",
            # the employer's share asked with no pension word in the line - the follow-up in a
            # pension conversation, and the duty itself - is still this answer, but only as the
            # whole phrase, so "how much does my employer have to pay me" stays a wage question
            "employer have to put in", "employer has to put in", "employer have to pay in",
            "employer has to pay in", "employer have to contribute", "employer has to contribute"),
           ("how much should i pay", "how much to pay", "how much should i put",
            "how much should i contribute", "how much to contribute", "pay in", "put in",
            "pay into", "put into", "contribution", "contributions", "what percentage",
            "how much does my employer", "how much does the employer", "employer have to pay",
            "percentage", "percent", "pay more in", "increase it", "raise it", "too little",
            # "is 200 a month enough" and "am i paying enough" are the same rate question as
            # "how much should i pay in", and this row already holds the rule of thumb. Only the
            # phrases that carry the paying are here: a bare "enough" is also "enough to live on",
            # which is the retirement-income row's question, not this one.
            "enough for a pension", "enough for my pension", "enough for the pension",
            "enough into my pension", "enough in my pension", "enough going in",
            "enough going into", "am i paying enough", "paying enough",
            "putting in enough", "putting enough in", "contributing enough",
            "should i pay more", "pay more into", "more into my pension",
            # the employer's own share asked on its own: the rate card has the 3% in it, and
            # the line was answered with "that is all I know on it" once the card had been given
            "what does my employer", "what does the employer", "employer have to put in",
            "employer has to put in", "employer have to contribute", "employer has to contribute",
            "employer put in", "employer pay in", "employer contribution", "employer contributions",
            "minimum my employer", "minimum the employer")),
          # the oldest rule of thumb in pensions, and the one a person can act on today
          "Half your age as a percentage of your pay is the rule of thumb for a pension started "
          "now: 5% at 20, 10% at 30, 15% at 40, and your employer's minimum 3% counts towards it, "
          "so someone starting at 30 paying 7% gets to 10% with the employer's share. Aim for "
          "12 to 15% of pay going in altogether once you can, because a pot built late has to "
          "work much harder: money paid in at 25 has about four times as long to grow as money "
          "paid in at 45.",
          bias=3,
          avoid=("doesnt offer", "doesn't offer", "no pension", "sipp", "opt out", "opting out",
                 "state pension", "take", "lump sum", "25%",
                 # "do i have to" is the optional-or-not row below, which answers it with a no
                 "do i have to", "do i need to pay", "must i", "compulsory",
                 # a choice between the pension and the mortgage is the two-sided row's line,
                 # and the rate of pay is not what it asks
                 "mortgage", "pay off", "paying off", "overpay", "overpaying", "or pay",
                 # the rate of pay is not the question on these either: a date, a transfer, the
                 # relief itself, or a pot for somebody else each have their own answer
                 "retire at", "retiring at", "to retire", "before i retire", "transfer",
                 "move my", "moving my", "for my child", "for my children", "for my kids",
                 "for my son", "for my daughter", "tax relief", "tax free", "tax-free",
                 "drawdown", "annuity", "how much tax",
                 # a pot for a named other person is the someone-else row's line: the rate you
                 # should pay into your own pension is not the answer to it
                 "wife", "wifes", "husband", "husbands", "partner", "partners", "spouse",
                 "son", "sons", "daughter", "daughters", "child", "children",
                 "grandchild", "grandchildren",
                 "mum", "mums", "mother", "dad", "dads", "father",
                 "someone else", "someone elses", "somebody else", "on behalf",
                 # an employer who will not pay is the enrol-you row's line: the person is
                 # describing a duty they are owed, not asking for a percentage
                 "employer wont pay", "employer won't pay", "employer refuses",
                 "employer refusing", "employer stopped paying", "employer not paying",
                 "wont pay into", "won't pay into", "refuses to enrol", "refuses to pay",
                 "refusing to pay", "stopped paying into", "not paying into",
                 "wont contribute", "won't contribute",
                 # what can be afforded is the optional-or-not row's line, not the rate, and a
                 # benefit question is not a rate question either
                 "afford", "affording", "benefit", "benefits", "child benefit",
                 "universal credit", "tax credit", "tax credits", "claiming",
                 # a definition ask is not a rate question
                 "what is", "whats a", "what is a", "mean", "means",
                 "defined contribution", "defined benefit", "final salary",
                 # living on the pot is the retirement-income row's line: what a person should
                 # be paying in is not the answer to "is my pension enough to live on"
                 "live on", "live off", "to live", "my pension enough", "pension be enough")),
    entry("pension-pot-size",
          (("pension", "pensions", "pension pot"),
           ("how much should i have", "big enough", "on track", "at 30", "at 35", "at 40",
            "at 45", "at 50", "at 55", "by 30", "by 35", "by 40", "by 50", "benchmark",
            "average pot", "pot size", "typical pot", "supposed to have")),
          "The crude benchmark the industry uses is a multiple of your salary: about your salary "
          "by 30, three times by 40, five times by 50 and seven times by the time you retire at "
          "67, all in the pot rather than paid in. It is a rough guide, not a rule - someone with "
          "a final-salary scheme needs none of it and someone starting at 45 needs more - so the "
          "honest check is the free forecast on gov.uk for the state pension plus your scheme's "
          "own projection of what the pot turns into as an income.",
          bias=3,
          avoid=("state pension", "sipp", "opt out", "take")),
    entry("pension-sipp",
          (("sipp", "sipps", "personal pension", "private pension", "stakeholder pension",
            "self-invested personal pension", "open a pension", "set up a pension",
            "pension myself", "pension of my own"),
           ("what is", "what are", "whats", "how do i", "can i", "should i", "get one",
            "worth", "better", "open",
            "set up", "start", "myself", "self employed", "self-employed", "freelance",
            "charges", "fees", "which", "explain", "means")),
          "A SIPP is a personal pension you open yourself, with the same tax relief as a "
          "workplace one - the government adds 20% to what a basic-rate payer puts in, and higher "
          "earners claim the rest back - but nobody adds an employer contribution and you choose "
          "the funds. It is the usual answer for the self-employed, and for anyone whose employer "
          "adds nothing: a global tracker fund at a total charge under about 0.5% a year is the "
          "plain choice. Only pay into a SIPP after you have taken every employer contribution "
          "going, because that is free money a SIPP cannot match.",
          bias=3,
          # "is a sipp worth it" is the should-I question, not the what-is one, and a child's
          # pot is the junior SIPP row below, because a parent needs the age 57 and the 2,880
          avoid=("state pension", "lump sum", "25%", "take", "drawdown", "annuity",
                 "worth", "worth it", "should i", "good idea", "better than",
                 "child", "children", "kid", "kids", "junior", "son", "daughter",
                 "grandchild", "grandchildren", "baby", "newborn",
                 # an age or a date is the taking-the-money question, not what a SIPP is:
                 # "at what age can i draw my private pension" was answered with the definition
                 "what age", "at what age", "how old", "when can i", "when do i", "when will i",
                 "draw my", "draw the", "access my", "get at it")),
    entry("pension-for-someone-else",
          (("pension", "pensions", "sipp", "pension pot", "pot", "junior sipp"),
           # The pot belongs to somebody else, said either as "my wife's pension" or as
           # "a pension for my child". "i have two kids, how much should i put in my pension" is
           # a rate question about the person's own pot, so the possessives are what decide it.
           ("my wife", "my wifes", "my husband", "my husbands", "my partner", "my partners",
            "my spouse", "my son", "my sons", "my daughter", "my daughters", "my child",
            "my children", "my kid", "my kids", "my mum", "my mums", "my mother",
            "my dad", "my dads", "my father", "my grandchild", "my grandchildren",
            "my grandson", "my granddaughter", "my baby",
            "someone else", "someone elses", "somebody else", "somebody elses", "on behalf",
            "for my wife", "for my husband", "for my partner", "for my son",
            "for my daughter", "for my child", "for my children", "for my kids",
            "for my grandchild", "junior sipp", "childs pension", "child pension",
            "childrens pension", "kids pension", "childs pot", "pension for my daughter")),
          _pension_for_someone,
          # an ask about a pot for a named other person, not the rate to pay into your own
          ask=("pay", "paying", "paid", "pay into", "pay in", "contribute", "contributing",
               "contribution", "contributions", "open", "opening", "set up", "start", "start",
               "fund", "put in", "putting", "top up", "save into", "add to", "invest",
               "worth", "can i", "should i",
               # "what is a junior sipp" is this answer's own definition, and the SIPP card
               # stands down for the word junior
               "what is", "whats", "what are", "mean", "means", "explain"),
          bias=3,
          avoid=("state pension", "lump sum", "25%", "drawdown", "annuity", "take my",
                 "transfer", "opt out", "scam")),
    entry("pension-auto-enrolment",
          (("auto enrolment", "auto-enrolment", "auto enrolled", "auto-enrolled", "opted in",
            "opted into", "automatically enrolled", "enrolled me", "autoenrolment"),
           ("what", "how", "when", "am i", "have i", "do i", "should", "pension", "work",
            "employer", "opt out", "leave", "join")),
          "Auto-enrolment is the law that puts you into your employer's pension without you "
          "asking: it covers everyone from 22 to state pension age earning more than 10,000 "
          "pounds a year, and the minimum is 8% of your pay in total, at least 3% of it from the "
          "employer and the rest from you with tax relief on top. You can leave within the first "
          "month and get your own money back, and any time after that you can stop paying in and "
          "keep the pot - but leaving gives up the employer's 3%, which is a pay cut to get your "
          "own money back sooner.",
          bias=3,
          avoid=("doesnt offer", "doesn't offer", "no pension", "sipp", "state pension")),
    entry("pension-must-i",
          (("pension", "pensions", "auto enrolment", "workplace pension"),
           ("have to", "optional", "compulsory", "obliged", "required to", "must i",
            "must pay", "must join", "can i stop", "can i leave",
            # the same question in the words people use for it: opting out is the choice, and
            # the answer is that it is allowed and what it costs
            "opt out", "opting out", "opted out", "should i opt", "can i opt",
            "leave the pension", "leave the scheme", "stop paying in", "stop paying into",
            "cancel it", "cancel my pension", "get out of the pension")),
          # the answer to "do i have to" is no, and the reason to say yes anyway is the 3%
          "No - paying into a pension is your choice, and all leaving costs is money: your "
          "employer's contribution of at least 3% of your pay, the tax relief the government adds "
          "to yours, and the growth on both over the decades to retirement. Leaving in the first "
          "month gets your own money back; after that the pot stays put and you can rejoin or "
          "restart payments whenever you like, so a tight few months is a reason to pause rather "
          "than to quit.",
          bias=3,
          avoid=("state pension", "sipp", "doesnt offer", "doesn't offer", "no pension",
                 "how much", "what percentage", "percent")),
    entry("pension-too-expensive",
          (("pension", "pensions", "pension contributions", "pension contributions"),
           ("afford", "affording", "cant afford", "can't afford", "too expensive",
            "pay less", "paying less", "reduce", "reducing", "lower", "cut down",
            "pause", "pausing", "stop paying")),
          # what to give up first when the money is short, which is not the scheme itself
          "Pay less rather than stop: your own 5% of pay is what unlocks the employer's 3% and "
          "the tax relief, so drop to that before you leave the scheme, and change it back "
          "whenever a payslip looks better. Stopping altogether costs you the employer's share "
          "and the government's top-up, and it takes a phone call to the payroll team to fix, "
          "so a tight few months is a reason to pay the minimum rather than to come out.",
          bias=2,
          avoid=("state pension", "sipp", "mortgage", "lump sum", "25%")),
    entry("pension-statement",
          (("pension statement", "pension statements", "annual statement", "pension paperwork",
            "pension letter", "statement from my pension", "pension report",
            # seeing what is in the pot is the same question as reading the statement, and it
            # is asked without ever saying "statement": "how do i check my pension", "what is my
            # pension worth", "how much is my pension worth". The phrase has to be the whole
            # ask, not "my pension" with a word beside it: "how much tax do i pay on my
            # pension" and "is a pension worth it" are other answers, and "worth"/"much" in
            # both halves made every one of them this card.
            "check my pension", "check my pension pot", "check my pot",
            "what my pension is worth", "my pension worth", "pension pot worth",
            "much is my pension", "much have i got in my pension",
            "what is in my pension", "whats in my pension", "value of my pension",
            "check what my pension"),
           ("understand", "means", "read", "says", "confusing", "jargon", "explain",
            "what does", "numbers", "add up", "get", "getting", "find", "finding", "where",
            "check", "checking", "worth", "value", "much", "got", "what is", "whats",
            "see", "look", "look up", "look at", "find out", "owed")),
          "An annual pension statement has four numbers worth finding: the pot's value now, what "
          "you and your employer paid in during the year, the charges taken out, and the income "
          "the scheme projects at retirement. Check the charge line first, because 1% a year "
          "sounds small and takes a fifth of a pot over forty years, and a free Pension Wise "
          "appointment will walk through the rest with you if it still does not add up.",
          bias=3,
          # "my pension statement says im at risk" is the safety question, not the paperwork one
          avoid=("state pension", "not growing", "isnt growing", "barely moved",
                 "at risk", "risky", "risk", "safe", "protected", "ppf", "goes bust",
                 # and how much to pay in, taking it, and moving it are their own answers: the
                 # statement card explains the numbers already in the pot
                 "should i pay", "how much should i", "contribute", "contribution", "pay in",
                 "opt out", "take", "taking", "transfer", "lump sum", "25%", "sipp",
                 "on track", "big enough", "should i have", "scam", "fraud", "rang me",
                 # and the state pension forecast is the record answer's, not the pot
                 # statement's: "how do i check my pension forecast" is a gov.uk login
                 "forecast", "record", "qualifying years", "pension age", "gov.uk")),
    entry("pension-not-growing",
          (("pension", "pensions", "pension pot", "pension fund"),
           ("not growing", "isnt growing", "isn't growing", "barely moved", "hasnt grown",
            "hasn't grown", "not gone up", "lost money", "gone down", "dropping", "default fund",
            "charges", "fees", "invested in", "rubbish")),
          "A pot that has barely grown over a year is usually in the scheme's default fund "
          "withdrawn in cash or bonds rather than shares, or paying charges of 1% or more a year "
          "that quietly eat the growth - so find the fund name and the total charge on the yearly "
          "statement first. Over decades a global shares fund has beaten cash by a wide margin, "
          "and a default that is too cautious is the commonest thing wrong with an otherwise "
          "healthy pension; switching funds inside the scheme is free and takes ten minutes.",
          bias=3,
          avoid=("state pension", "take", "lump sum", "25%", "sipp", "opt out", "understand",
                 "means", "confusing")),

    # ---- lines main still shrugged at (measured on 3a6d235) ----
    entry("what-a-sole-trader-is",
          (("sole trader", "sole traders", "sole-trader", "self employed person"),
           ("what is", "whats", "what are", "mean", "meaning", "explain", "define",
            "definition", "is a", "is it")),
          "A sole trader is one person running a business with no company around them: you and "
          "the business are the same, you register with HMRC, file a self assessment and keep "
          "what is left after tax and National Insurance. You can trade under your own name or a "
          "business name, your accounts stay private, and you are personally liable for the "
          "debts - which is the part that matters if the work involves risk. Register as soon as "
          "you start earning more than £1,000 in a tax year, keep every receipt, and put a third "
          "aside for the bill.",
          # a comparison of the two, and the job of being one, are other rows
          avoid=("difference", "should i", "which", "better", "worth", "set up", "become",
                 "be a", "choose", "limited", "ltd", "company", "register a", "how do i",
                 "tax return", "self assessment", "expenses", "invoice"),
          bias=1),
    entry("corporation-tax",
          (("corporation tax", "corp tax", "ct600", "company tax"),
           ("what is", "whats", "how much", "rate", "pay", "owe", "deadline", "when",
            "explain", "mean", "how do i")),
          "Corporation tax is the tax a limited company pays on its profit: 19% on profits up to "
          "£50,000, 25% above £250,000, and somewhere between the two in between. It is worked "
          "out on profit, not on what you take out - salaries and pension contributions are "
          "costs, dividends are paid from what is left after tax. You file a CT600 with accounts "
          "within 12 months of the year end, and pay usually nine months and a day after it. "
          "Allowable costs come off first: stock, tools, software, insurance, mileage, and the "
          "salary you pay yourself.",
          avoid=("self assessment", "sole trader", "personal allowance", "payslip", "paye",
                 "dividend tax", "vat"),
          bias=1),
    entry("what-an-invoice-is",
          (("invoice", "invoices"),
           ("what is", "whats", "mean", "meaning", "definition", "explain", "difference")),
          "An invoice is the bill you send after you have done the work: it asks for a set amount "
          "by a set date and is your record of the sale. Put your name and address, theirs, your "
          "business name and company number or 'sole trader', a number of its own, the date, what "
          "you did with quantity and rate, the total, VAT only if you are registered, the payment "
          "terms such as 'due in 14 days', and the bank details. A receipt is the other way round "
          "- proof of payment after the money arrives - and a quote comes before the work.",
          avoid=("write", "writing", "template", "what should", "what to put", "chase",
                 "unpaid", "not paid", "vat return", "receipt for"),
          bias=1),
    entry("self-employed-expenses",
          (("expenses", "expense", "write off", "tax deductible", "deductible",
            "put through", "claim for", "claim as", "mileage", "claim", "claims",
            "claiming"),
           ("self employed", "self-employed", "sole trader", "sole-trader", "freelance",
            "freelancer", "my business", "business expense", "business expenses")),
          "Anything wholly and necessarily for the work: stock and materials, tools, software "
          "and subscriptions, insurance, bank fees, the business share of your phone and "
          "broadband, travel between jobs (not the commute), and a share of the heating if you "
          "work at home. Keep the receipt and note what it was for. Mileage is 45p a mile for "
          "the first 10,000 miles and 25p after that, instead of the running costs. You cannot "
          "claim your own wages, a suit you also wear out, or the commute - and if you use "
          "simplified expenses for the home you cannot also claim the bills.",
          # the employee's expenses are the `expenses` row's, and a payslip question is not this
          # NOT "employer"/"employee": `_misspelt_avoid` treats a word one edit from a word in
          # the line as a hit, and "employed" is one edit from "employer", so the row fenced
          # its own question off ("what expenses can i claim as self employed" found nothing).
          avoid=("my employer", "p60", "payslip", "uniform", "working from home",
                 "hmrc pay me", "my boss", "redundancy"),
          bias=1),
    entry("need-an-accountant",
          (("accountant", "accountants", "bookkeeper", "bookkeeping", "tax adviser"),
           ("need", "do i", "should i", "worth", "how much", "cost", "do my", "hire",
            "get one", "how do i", "when")),
          "You do not need one as a sole trader if you are happy filing a self assessment, but "
          "most people hire one the first year they go self-employed, because they know what "
          "you can claim and it takes them an hour; £150 to £400 a year for a simple return is "
          "normal. A limited company is a different matter: accounts, a confirmation statement "
          "and a corporation tax return are all due every year, so budget £600 to £1,200 and "
          "keep the paperwork tidy. Ask two for a fixed quote and check they are on a "
          "recognised body, such as ICAEW or ACCA.",
          # a bill owed to one, and the way into the job, are other lines
          avoid=("invoice", "invoices", "unpaid", "not paid", "bill for", "chase",
                 "become", "becoming", "career", "qualify", "qualified", "qualification",
                 "training", "apprenticeship", "degree", "salary", "how much do they earn",
                 "job", "jobs", "gcse", "gcses", "a level", "a levels", "a-levels",
                 "subjects", "be an", "to be a", "university"),
          bias=1),
    entry("pay-yourself-from-a-company",
          (("pay myself", "paying myself", "pay yourself", "take money out of my company",
            "take money out of the company", "salary or dividends", "salary and dividends",
            "director salary", "draw from my company", "pay myself a salary"),
           ("how do i", "how much", "should i", "best way", "what is the best", "how",
            "salary", "dividends", "dividend", "limited company", "my company")),
          "Most small company owners take a small salary up to the personal allowance - about "
          "£12,570 - and the rest as dividends, because that mix pays the least National "
          "Insurance. Run the salary through PAYE even though the tax may be nil: it is what "
          "gives you a year of state pension and counts as your earnings. Dividends come out of "
          "profit after tax, need profit to cover them, and need a board minute and a dividend "
          "voucher on file. Above about £50,000 of profit an accountant usually finds a better "
          "split than the rule of thumb, and pension contributions are the other thing worth "
          "asking about.",
          # the code on the payslip, and the company itself, are other rows
          avoid=("payslip is wrong", "tax code", "p60", "p45", "minimum wage", "set up a",
                 "register", "close my"),
          bias=1),
    entry("what-is-paye",
          # the bare word "paye" cannot be keyed: `_forms("paye")` folds to "pay", so "i owe 800
          # on a card and only paying the minimum" matched it, and avoiding "pay" then fenced the
          # row's own line. The whole phrasings are keyed instead.
          (("what is paye", "whats paye", "how does paye work", "paye mean", "paye system",
            "pay as you earn", "paye tax", "explain paye"),
           ("what is", "whats", "how does it work", "how do i", "explain", "mean", "work",
            "register", "payroll", "employer", "employee")),
          "PAYE is the payroll system: the employer works out income tax and National Insurance "
          "from your tax code, takes them off your pay before it reaches you and sends them to "
          "HMRC, usually by the 22nd of the following month. That is why a payslip shows a gross "
          "figure and the net you actually get. As an employer you register for PAYE before the "
          "first payday; as an employee it is already done for you.",
          avoid=("tax code", "my company", "my own company", "limited company", "dividend",
                 "dividends", "payslip is wrong", "p60", "p45", "minimum wage"),
          bias=1),
    # "does paye come out of my wages" was a search hedge: the row above is keyed on the letters,
    # and the way most people meet PAYE is the deduction on a payslip. A row of its own rather
    # than more phrasings on that one, because "whats paye" has to keep the answer that spells
    # the letters out.
    entry("paye-on-the-payslip",
          (("paye", "paye tax", "pay as you earn"),
           ("come out of my wages", "comes out of my wages", "come out of my pay",
            "comes out of my pay", "taken off my wages", "taken out of my wages",
            "taken off my pay", "taken out of my pay", "deducted from my wages",
            "deducted from my pay", "deducted", "deduction", "before i get paid",
            "before it reaches me", "come off my wages", "comes off my pay")),
          "Yes - PAYE is the tax and National Insurance coming out of your pay before it reaches "
          "you. The employer works both out from your tax code and pays them to HMRC, and what is "
          "left is the net figure on your payslip. The tax code is the bit that decides how much: "
          "1257L is the usual one for one job with no benefits, and if it looks wrong, ask "
          "payroll to check it rather than waiting for a rebate.",
          avoid=("self assessment", "sole trader", "my company", "limited company", "dividend",
                 "payslip is wrong", "tax code", "p60", "p45", "minimum wage"),
          bias=1),
    entry("website-cost",
          # the whole website question was a hedge on main: "how much does it cost to set up a
          # website" even went to the sets-and-reps card, because "set up" is in its key
          (("website", "websites", "web site", "web shop", "online shop", "online store",
            "shopify", "squarespace", "wix", "landing page", "web hosting", "hosting cost",
            # NOT a bare "hosting": "im hosting a barbecue what should i make" is a cooking line
            "how much is hosting", "hosting a website", "website hosting"),
           ("cost", "costs", "how much", "set up", "setting up", "build", "building", "make",
            "need", "start", "cheapest", "hosting", "price", "prices", "do i", "should i")),
          "For a small business the bill is mostly hosting: a domain name is about £10 a year, a "
          "site builder or simple hosting is free to about £20 a month, and a developer charges "
          "£500 to £3,000 for a five-page site. Start with a free page on a builder and pay for "
          "the domain, because the name is the bit you keep; move to better hosting when the "
          "phone rings twice a week. A shop is the expensive part - card fees around 1.5% plus "
          "20p an order, and Shopify from about £25 a month - so sell through an existing "
          "marketplace first and build the shop once you know what people buy.",
          # a fault on the site, an email problem and a design question are other rows
          # "how do i stop websites tracking me" is a privacy question and "how much does it cost
          # to set up a website" is this one: the noun is the same, the ask is not
          avoid=("not working", "broken", "down", "slow", "error", "loading", "login",
                 "log in", "hacked", "virus", "email", "password", "domain name is taken",
                 "tracking", "track me", "tracked", "trackers", "privacy", "cookies",
                 "adverts", "advertising", "blocker", "vpn", "incognito", "search history",
                 "stop websites", "block websites", "dark web",
                 # a site that is blocked, or one somebody wants unblocked, is a fault or a
                 # permission question and no row answers it; the hosting bill is not the answer
                 "unblock", "unblocked", "unblocking", "blocked website", "site is blocked",
                 "websites are blocked", "access to a website", "cant access", "can't access",
                 # a scam shop is a safety line, not a hosting bill: "how do i report a scam
                 # website" and "is an online shop a scam" were both this row's for "website"
                 "scam", "scams", "scammed", "fraud", "fraudulent", "fake", "report",
                 "legit", "legitimate", "trust", "trustworthy", "safe", "refund", "rip off"),
          bias=1),
    entry("business-plan",
          (("business plan", "business plans", "plan for my business", "write a business plan",
            "startup plan", "start up plan", "start-up plan", "plan my business"),
           ("how do i", "how can i", "write", "writing", "what goes in", "what should be in",
            "template", "do i need", "need a", "what is", "whats", "help me")),
          "A business plan for a small business is one page, not forty: what you sell in a "
          "sentence, who buys it and where they are now, what one sale earns you, what it costs "
          "to make or supply it, the fixed costs each month, and the number of sales a month "
          "that covers those costs - that last number is the break-even and it is the only part "
          "anyone reads twice. Add how you will reach the first ten customers and what money you "
          "need before the first sale. Write it in an hour, then change it after a month of "
          "selling, because the version in your head is guessing and the version after ten "
          "customers is not.",
          avoid=("bank account", "vat", "confirmation statement", "directors loan",
                 "tax return", "close my", "invoice", "cash flow"),
          bias=1),
]


# ---- the worry about money that arrives as a question --------------------------------------
# The chat module answers the person who reports the feeling ("im worried about money" gets "say
# the worst case out loud"), and the worry habit row in habits.py deliberately stands down when the
# line names money, because a money question is the money domain's. What was left was nobody: the
# how-to lines and the sleep-at-3am lines were a search hedge or an echo of the line back
# ("i cant stop worrying about money" -> "That sounds like it is still sitting with you").
# So this is the how-to half, in the words people use for it, and the answer is a page, one small
# move and a slot for the worry rather than reassurance. It needs a worry word and a money word,
# so "how do i get out of debt" and "my rent has gone up" keep the cards that answer them.
ENTRIES.append(entry(
    "money-worry",
    (("worry", "worried", "worrying", "anxious", "anxiety", "stress", "stressed", "panic",
      "panicking", "cant stop thinking", "can't stop thinking", "stop thinking", "thinking",
      "keep thinking", "always thinking", "money worries", "awake", "cant sleep", "can't sleep",
      "keep me up", "keeps me up", "kept me up", "not sleeping", "overthinking", "dread"),
     ("money", "bills", "bill", "rent", "mortgage", "debts", "debt", "payday", "afford",
      "income", "salary", "wages", "pay", "overdraft", "credit card", "credit cards",
      "cost of living", "food shop", "fuel", "energy")),
    "Put it on one page tonight, because the unknown is usually bigger than the number: what "
    "comes in each month, what goes out on the things you cannot avoid, and every debt with its "
    "minimum payment and its rate. Then pick the smallest thing you can do this week - a payment "
    "plan with the council or the energy company, or one call to a free debt service (StepChange, "
    "National Debtline or Citizens Advice in the UK), which costs nothing and does not touch your "
    "credit file. Give the worry a fifteen-minute slot in the evening and write one line to take "
    "to it, so it stops arriving at 3am: postponing is the part that trains it. If it is most "
    "days for months, or you cannot sleep for it, that is worth a GP appointment too.",
    # the shape that asks for a method, so a bare report stays with the chat module's warmer reply
    ask=("stop", "stopping", "cant stop", "can't stop", "how do i", "how can i", "help me",
         "what can i do", "deal with", "get rid of", "cope", "keep", "always"),
    # a price, a decision, a repayment and a landlord's letter are other rows, and so is worry
    # about a person
    avoid=("how much", "how many", "should i", "is it worth", "worth it", "lend", "loan",
           "mortgage deal", "remortgage", "invest", "pension", "how do i get out of debt",
           "debt collectors", "bailiff", "bailiffs",
           # a line that names sleep wants the sleep card: it answers the half of the question
           # this row cannot ("get up after twenty minutes of lying there awake")
           # and so does a line that also asks about saving: the saving card answers that half
           "save", "saving", "savings", "save money", "start saving", "budget", "budgeting",
           "get to sleep", "go to sleep", "go back to sleep", "to sleep", "asleep", "sleeping",
           "insomnia", "wake up", "waking up", "lying awake", "bed",
           "my mum", "my mom", "my dad", "my son",
           "my daughter", "my partner", "my husband", "my wife", "my friend", "dog", "cat"),
    bias=2))

# The benefit for an older person who needs help with washing, dressing or being watched over
# was nobody's: "how much is attendance allowance" was answered with the phone's data allowance,
# because "how much" beside "allowance" is all the data card needs, and every other phrasing was
# a punt. It is asked by name ("attendance allowance", the form AA1) or by the person and the
# care ("does my mum get anything for needing help"), so the key has both halves and the money
# words the question always carries. "attendance" alone is school attendance and the work
# register, so the scheme is named as a phrase and never as one word.
# The sentence the attendance allowance card owes a whether-line that asks how the benefit is
# assessed, and the lines that ask something else. "can i claim attendance allowance for my mum" is
# a whether-line on this row too, and it wants who the benefit is for and how to claim; leading it
# with the means test answered a question nobody asked. So the row declares a reading and not a
# shape alone: the sentence leads when the line names the assessment (means testing, savings,
# income, capital) and every other line is left with the card as it is written. Declared whole, to
# its full stop - a lead declared as a sentence's first clause cuts the card at the comma.
_NOT_MEANS_TESTED = ("It is not means-tested, so savings and income do not count, it is tax-free, "
                     "and nobody has to be paid to help you yet")
_ASKS_ABOUT_THE_ASSESSMENT = re.compile(
    r"\bmeans[\s-]?tested?\b|\bnot means\b|\bsavings?\b|\bincome\b|\bcapital\b|"
    r"\bassets?\b|\bcount(?:s|ed)?\s+(?:against|towards|toward|as\s+(?:income|capital))\b",
    re.I)


def _the_assessment_sentence(understood):
    """The means-test sentence for a line that asks how the benefit is assessed, else ""."""
    said = " ".join(str((understood or {}).get("clean")
                        or (understood or {}).get("text") or "").lower().split())
    return _NOT_MEANS_TESTED if _ASKS_ABOUT_THE_ASSESSMENT.search(said) else ""


ENTRIES.append(entry(
    "attendance-allowance",
    (("attendance allowance", "attendance allowence", "attendence allowance",
      "attendance allowances", "aa1", "aa form", "attendance benefit",
      "allowance for being looked after", "allowance for needing help"),
     ("how much", "how many", "what is", "whats", "what are", "claim", "claims", "claimed",
      "claiming", "get", "gets", "got", "qualify", "qualifies", "entitled", "eligible",
      "apply", "worth", "rate", "rates", "weekly", "week", "month", "paid", "pay", "money",
      "benefit", "benefits", "affect", "means tested", "savings", "pension", "help with")),
    "Attendance Allowance is for someone over State Pension age who needs help with personal "
    "care because of an illness or a disability: about £74 a week if the help is needed in the "
    "day or at night, about £110 if it is both (2025-26; the rates move every April). It is not "
    "means-tested, so savings and income do not count, it is tax-free, and nobody has to be paid "
    "to help you yet. Claim on form AA1 - phone the DWP and they will fill it in with you - and "
    "it also unlocks Pension Credit for some people.",
    # "is attendance allowance means tested" and "does it count my savings" ask the sentence
    # about means-testing, which the card holds second because "how much is attendance allowance"
    # wants the figure first. Declared whole, to its full stop: declared as its first clause the
    # lead would cut the card at the comma and leave "so savings and income do not count" out.
    lead=("yesno", _the_assessment_sentence),
    # a bus pass, a blue badge and a Motability car are other schemes, and the school or work
    # register is another "attendance" entirely
    avoid=("bus pass", "blue badge", "motability", "railcard", "school", "schools", "class",
           "register", "registery", "truant", "absence", "absent", "work", "shift", "office"),
    bias=1))

# The P11D is the one work form people are handed with no explanation: the employer files it, it
# carries the benefit, not the wage, and the tax comes out in the code. "what is a p11d" and "what
# is a p11d form" were a search hedge while the P45 and the P60 both had their own answer.
ENTRIES.append(entry(
    "p11d",
    (("p11d", "p11ds", "p11d form", "p11d tax", "benefit in kind", "benefits in kind",
      "company car tax form"),
     ("what is", "whats", "whats a", "mean", "explain", "do with", "for", "need", "tax",
      "company car", "medical insurance", "do i owe", "how much")),
    "A P11D is the form your employer sends HMRC each year to report the benefits in kind - the "
    "perks that are not in your pay: a company car, private medical insurance, a cheap loan, a "
    "phone or a season ticket. You do not fill it in and you are not taxed by the form itself: the value is added "
    "to your income and the tax comes out through your tax code. Keep the copy payroll gives "
    "you, check the figure for a car matches what you thought you paid, and if it is wrong ask "
    "payroll to correct it rather than ringing HMRC.",
    # a P45 and a P60 are the other two work forms and have their own answers, and the student
    # loan, the payslip and the tax return are different jobs
    avoid=("p45", "p60", "payslip", "pay slip", "tax return", "self assessment", "student loan",
           "national insurance", "ni number", "rebate", "refund", "maternity", "sick pay",
           "redundancy", "notice period", "holiday pay", "minimum wage", "timesheet"),
    bias=2))

# Caring for someone is money as well as time, and the benefit for it had no row at all. On main
# "what is carers allowance" and "can i claim anything for looking after her" both reached the
# "I don't know" punt, and "how much is carers allowance" was answered with the mobile-data card,
# because "how much" beside "allowance" is all that card needs. The asking forms people actually
# type are the caring itself plus a money word, so that is what the two halves of the key are.
ENTRIES.append(entry(
    "carers-allowance-money",
    (("carers allowance", "carer allowance", "carer's allowance", "carers credit",
      "carers element", "carer element", "carers benefit", "care allowance",
      "claim for caring", "paid for caring", "paid to care", "pay me to care",
      "money for caring", "full time carer", "i am a carer", "im a carer", "im her carer",
      "im his carer", "carer for my", "caring for my",
      # the phrasing most people write: the caring is named by who it is for, not by the word
      # "carer" at all
      "looking after", "look after", "caring for", "care for my", "care for her",
      "care for him", "cares for"),
     ("claim", "claims", "claimed", "claiming", "how much", "what is", "whats", "what are",
      "paid", "pay", "get paid", "money", "allowance", "benefit", "benefits", "entitled",
      "qualify", "qualifies", "apply", "get any", "anything", "worth", "affect", "help with")),
    ("Carer's Allowance is for someone giving 35 hours a week or more of care to the same person: "
     "about £83 a week, and you can earn up to about £204 a week after tax and still get it (both "
     "figures move every April, so check this year's on gov.uk). The person you care for has to be "
     "getting a disability benefit - Attendance Allowance, the daily living part of PIP, or DLA "
     "middle or higher rate - their savings and income are not part of the test. Claim it even if "
     "you are unsure, since it also gives you National Insurance credits; over State Pension age "
     "the same care is paid through Pension Credit instead. On Universal Credit, tell them you are "
     "a carer as well - the carer element is separate."),
    # the care itself, the care home, the agency and a paid helper are other answers, and so is
    # caring for a child, an animal or a garden
    avoid=("care home", "care homes", "nursing home", "agency", "agencies", "childminder",
           "babysitter", "nursery", "childcare", "respite", "career", "carers coming",
           "carer comes", "dog", "dogs", "cat", "cats", "puppy", "kitten", "pet", "pets",
           "garden", "house", "plants", "allotment", "hen", "hens", "chickens", "horse",
           "kids", "children", "grandchildren", "grandchild", "baby", "newborn", "toddler",
           "my son", "my daughter", "school run"),
    ask=("claim", "claims", "claimed", "claiming", "how much", "what is", "whats", "what are",
         "paid", "pay", "get paid", "money", "allowance", "benefit", "benefits", "entitled",
         "qualify", "qualifies", "apply", "get any", "anything", "worth", "affect", "help with",
         "looking after", "look after", "caring", "carer")))


# A gap policy is sold at the desk when the finance is signed, so the question arrives as "do i
# need" and not as a product name - and every row keyed on the bare word "insurance" was taking
# it: "do i need gap insurance" got buildings and contents, and "is gap insurance worth it" got
# an extended warranty about a washing machine.
ENTRIES.append(entry(
    "gap-insurance",
    (("gap insurance", "gap cover", "gap protection", "gpf"),
     ("what", "what is", "whats", "how", "how does", "does", "work", "works", "do i need",
      "need", "worth", "worth it", "should i", "get", "buy", "take out", "explain", "mean",
      "needed")),
    "Gap insurance pays the difference between what your insurer gives you for a car written off "
    "and what you still owe on the finance, so you are not paying for a car you no longer have. "
    "It is worth having only while the finance is bigger than the car is worth and you could not "
    "clear the rest yourself, and not on a car you own. Buy it from a specialist, not the "
    "dealer, who often charges twice as much.",
    # the car cover itself is `car-insurance-minimum`, the home cover is `home-insurance`, and a
    # warranty on a machine is technology's
    avoid=("third party", "comprehensive", "by law", "legal", "home", "house", "contents",
           "buildings", "boiler", "phone", "pet", "travel", "warranty", "washing machine",
           "appliance", "excess", "renewal", "quote"),
    bias=2))

# PPI was sold alongside almost every loan and card for twenty years, so the question is still
# asked years after the deadline - and a policy is not a shop's clock: "can i still claim ppi"
# was answered with the six years you have to take a faulty thing back.
ENTRIES.append(entry(
    "ppi-refund",
    (("ppi", "ppi claim", "ppi claims", "ppi refund", "ppi compensation", "payment protection "
      "insurance", "payment protection policy"),
     ("claim", "claims", "claimed", "claiming", "reclaim", "reclaims", "refund", "compensation",
      "owed", "owe me", "money back", "get money", "still", "deadline", "dead line", "time limit",
      "too late", "missed", "thing", "worth", "how do i", "can i", "should i", "apply")),
    "The deadline for a new PPI complaint was 29 August 2019, so a policy sold before then "
    "cannot be claimed on now, however the line is worded. Two things are still live: a policy "
    "you are still paying for can be cancelled today, and where the firm has gone bust the free "
    "Financial Services Compensation Scheme may still take it. Anyone texting that you are owed "
    "money and wants a fee up front is running a scam.",
    # "what is ppi" is the glossary line that says what the letters stand for, and a loan, a
    # card or a mortgage payment is its own question
    avoid=("what does ppi stand for", "what is ppi", "what is a ppi", "ppi mean", "loan",
           "card", "mortgage", "insurance quote", "how much is", "cost", "premium"),
    ask=("claim", "claims", "claimed", "claiming", "reclaim", "reclaims", "refund", "compensation",
         "owed", "owe me", "money back", "get money", "still", "deadline", "dead line",
         "time limit", "too late", "missed", "thing", "how do i", "can i", "should i", "apply",
         "worth", "worth it"),
    bias=2))

# --- a word on a contract -------------------------------------------------------------
# Two words a person signs past without knowing: an escrow account on a house purchase and a
# retention on a building job. Both were search hedges on main, and both are definitions with a
# number in them, so each answer says what it is and what to check before signing.
ENTRIES.append(entry(
    "escrow-account",
    (("escrow", "escrow account", "escrow accounts", "held in escrow", "in escrow",
      "money in escrow"),
     ("what is", "whats", "what does", "mean", "means", "how", "why", "safe", "protect",
      "protects", "release", "released", "who holds", "how long", "house", "buying", "sale",
      "deposit", "solicitor", "conveyancer", "builder", "building work", "rent")),
    "An escrow account is a holding account run by a third party - usually a solicitor or a "
    "specialist escrow firm - that keeps money until the thing it is paying for is done. On a "
    "house purchase the deposit sits there between exchange and completion, and on a building job "
    "the payment sits there until the stage is signed off, so neither side can walk off with it. "
    "Ask who holds it, whose name is on the account, what exactly triggers the release and what "
    "happens if the two sides disagree, because money held in a client account at a bank is "
    "protected and money in the firm's own name may not be.",
    # a deposit scheme for a tenancy, a savings account and a pension are their own questions
    avoid=("deposit scheme", "deposit protection", "dps", "tenancy deposit", "savings account",
           "cash isa", "pension", "stocks", "shares", "premium bonds", "interest rate"),
    bias=1))

ENTRIES.append(entry(
    "retention",
    (("retention", "retentions", "retention money", "retention held", "5% retention",
      "3% retention", "money held back"),
     ("what is", "whats", "what does", "mean", "means", "how much", "why", "when", "paid",
      "pay", "release", "released", "building work", "builder", "job", "contract", "invoice",
      "half", "hold back", "held back")),
    "Retention is the slice of a building job's price the client keeps back as insurance that the "
    "snagging gets done - 5% is the usual figure, sometimes 3%. Half of it is released when the "
    "job is finished to the contract's standard, and the other half after a defects period, "
    "usually twelve months, once anything that has gone wrong has been put right. It should say "
    "all of that in the contract, with the date each half is due; if it does not, ask for it in "
    "writing before you start, because a builder who has not read the term will not expect the "
    "last payment to wait a year.",
    # tax retention, a phone retention deal and a customer retention offer are other things
    avoid=("tax", "hmrc", "student loan", "mobile", "phone", "broadband", "contract renewal",
           "loyalty", "customer", "employee", "staff", "records", "documents", "data",
           "bonus", "bonuses", "salary", "pay rise", "job offer", "hiring", "recruit",
           # "retention" is three everyday words this row must not take: the water the body
           # holds ("why do i have water retention" was answering about a building job), a
           # school year ("what is retention in school") and a pond or a drainage basin
           "water", "fluid", "swollen", "ankles", "salt", "kidney", "bladder", "pond",
           "drainage", "suds", "school", "pupil", "pupils", "year group", "grade", "exam"),
    bias=1))
