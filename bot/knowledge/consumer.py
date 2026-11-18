"""Consumer rights and complaints: refunds, faults, delays and the next step.

The answers lane owns this domain. People bring the everyday fights with shops, airlines,
tradespeople and companies: something broke, a parcel never came, the flight was cancelled,
the policy says no. Each Entry is keyed by the problem, not by the wording, and answers with
the rule, the number and what to actually do next. Advice is UK law in plain words, because
that is where the replies are checked; elsewhere the mechanism is usually a local consumer
body, so a reply names the step rather than guessing a foreign statute.
"""
import re

from .lookup import entry, saving_for_a_trip, TOOTH_OUT

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
# Every one of them is already answered by another domain, so this file adds knowledge without
# taking a single line away from anyone.
ANSWERS = ("shopping", "money", "home-and-diy", "technology", "geography-and-travel", "fitness")

# Every cancellation answer ends the same way, because the complaint that follows a cancellation
# is nearly always the same one: a payment went out after the date the company confirmed. The
# bank's direct-debit indemnity is the fastest route back, so it is written once here.
# One way of saying "money left my account that should not have" is the mistake of overpaying:
# overpaid, paid twice, double paid, paid too much. The words are one tuple because the same
# wording is the duplicate-charge card for a shop, the recall card for a payment that went astray
# and the overpayment card for a person or a trader, and a new way of saying it should reach all
# three at once.
PAID_BY_MISTAKE = ("overpaid", "overpay", "overpaying", "overpayment", "paid twice",
                   "paid it twice", "paid the same again", "double paid", "double-paid",
                   "double payment", "paid too much", "paid over the odds", "paid again",
                   "sent it twice", "sent the same payment", "went out twice",
                   "taken twice", "took it twice", "pays twice",
                   # the same mistake with the payee in the middle: "i paid the plumber twice",
                   # "i paid a tradesman too much". The phrase cannot span the words, so the
                   # mistake word is keyed on its own and the payee is the second signal.
                   "twice", "too much", "again", "double")

AFTER_CANCEL = (" If a payment goes out after the date they confirmed, ring the bank and ask for "
                "the direct debit indemnity, which has to put it back, and keep the email that "
                "shows the date you cancelled.")


# The 30-day ladder, and the reversal of proof that comes with the first six months. The
# reversal is only worth saying while it applies: a laptop two years old gets the rest of the
# ladder and no noise about a rule that ran out.
FAULTY_REPLY = ("Faulty goods are the retailer's problem, not the maker's: take it back to the "
                "shop with the receipt or a bank statement and say you are rejecting it, which "
                "means a full refund within 30 days of buying. After that they get one repair or "
                "replacement, and if that fails or takes too long, a price reduction or a refund.")
SIX_MONTH_REVERSAL = (" In the first six months the shop has to prove the fault was not there "
                      "when it sold it.")
SIX_MONTH_PASSED = (" After six months it is you who has to show the fault was there when it was "
                    "sold, so keep the receipt and any repair reports.")

_AGE_COUNTS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
               "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
               "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
               "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
               "couple": 2, "few": 3}


def _age_in_months(reading):
    """How old the line says the thing is, in months, or None if it does not say."""
    words = reading.get("words") or ()
    for i, word in enumerate(words):
        if word not in ("month", "months", "year", "years", "yr", "yrs"):
            continue
        before = words[i - 1] if i else ""
        count = _AGE_COUNTS.get(before)
        if count is None:
            digits = "".join(ch for ch in before if ch.isdigit())
            count = int(digits) if digits else None
        if count is None:
            continue
        return count * 12 if word.startswith("yr") or word.startswith("year") else count
    return None


# A device that has gone is still a device, so a line that names one is read by the kitchen as
# well: "my oven is broken" is an appliance that is missing, and cooking.without has the meal
# that needs none. Which of the two the person wants is in the rest of the line - "i want to
# bake a cake but my oven is broken" wants the cake, "my oven is broken, can i get a refund"
# wants the money - and the kitchen answer only exists for the first, so it decides.
KITCHEN_QUIET = ("money back", "refund", "refunds", "send it back", "take it back",
                 "took it back", "return it", "return them", "returned it", "replacement",
                 "repair", "repaired", "repairs", "mend", "regulations", "consumer rights",
                 "my rights", "sold faulty", "not fit for purpose", "trading standards",
                 "ombudsman", "chargeback", "charge back", "small claims", "compensation",
                 "warranty", "guarantee", "who pays", "entitled")


# The words that make a mark on something the shop's problem rather than a housekeeping one: the
# thing is new, it has just come, or it is going back. "how do i get a stain out of a mattress"
# and "my shoes are stained" have none of them, and they want the cleaning answer; "my new sofa
# is stained", "my sofa turned up stained" and "i want to return a sofa that is stained" have
# one, and they want the ladder.
_A_MARK_ON_ANYTHING = re.compile(r"\bstain(?:ed|s|ing)?\b", re.I)
_A_BUYING_LINE = re.compile(
    r"\b(?:new|brand new|brand-new|just bought|just got it|just had it|only had it|bought|"
    r"buying|arrived|arrives|arrive|came(?!\s+out\s+of\b)|came out of the box|turned up|turn up|delivered|"
    r"delivery|out of the box|from new|return|returns|returned|returning|refund|refunds|"
    r"refunded|money back|replace|replacement|reject|rejected|warranty|guarantee|"
    r"shop|shops|store|stores|retailer|seller|sold|described|listed as|as described|"
    r"faulty|damaged|"
    # "can i take stained shoes back", "my dress has a stain on it can i take it back": taking the
    # thing back is the person saying what they want, and it is the commonest way to say it about
    # clothes and shoes. `money back` was the only back in the list, so the row handed these to the
    # cleaning card - a cloth and no answer to the ask.
    r"take\s+(?:\w+\s+){0,3}back|took\s+(?:\w+\s+){0,3}back|"
    r"send\s+(?:\w+\s+){0,3}back|sending\s+(?:\w+\s+){0,3}back|"
    r"sent\s+(?:\w+\s+){0,3}back|bring\s+(?:\w+\s+){0,3}back|"
    r"brought\s+(?:\w+\s+){0,3}back|"
    r"back to the shop|back to the store|"
    r"wear and tear|not fit for purpose)\b", re.I)


# "Came out" is a thing leaving something, not a thing arriving: "the stain came out of my shirt"
# and "my dress came out of the wash with a stain" were read as buying lines - the bare word
# `came` was in the list above - and answered with the refund ladder instead of the cleaning
# card. "Came out of the box" is still an arrival, and it is in the list above on its own.

# An arrival and a mark in one line: "my sofa arrived with a scratch", "the telly turned up
# dented", "my new phone came with a cracked screen". The delivery card has the note-it-on-the-
# delivery-note answer, and the refund ladder is for a thing that went wrong later.
_IT_ARRIVED = re.compile(
    r"\b(?:arrived|arrives|arrive|arriving|came|came out of the box|come|comes|coming|"
    r"turned up|turn up|turning up|delivered|delivery|on delivery|out of the box|"
    r"when it came|when it arrived)\b", re.I)
_A_MARK_THAT_CAME_WITH_IT = re.compile(
    r"\b(?:scratch|scratches|scratched|scrape|scrapes|scraped|dents?|dented|chip|chipped|"
    r"dinged|cracks?|cracked|smashed|damaged|damage|mark|marks|marked)\b", re.I)


# A judgement on a figure the person has already said: "is that too much", "was that a fair
# price", "is 900 reasonable", "does that sound about right". The figure itself may be said in
# the same line or in the one before, which is why this reads the shape of the ask and not the
# number: the number is `bot/memory/price.py`'s business, and it reads the same words
# (`judged()`), so a line of this shape belongs there rather than to the overpayment card.
_A_FIGURE_JUDGED = re.compile(
    r"\b(?:is|was|isn'?t|wasn'?t|does|did|would)\s+"
    r"(?:that|this|it|£\s?\d[\d,.]*|\d[\d,.]*)\s+"
    r"(?:about\s+|roughly\s+|really\s+|actually\s+|sound\s+|seem\s+)?"
    r"(?:too\s+(?:much|dear|expensive|high|steep)|fair|normal|reasonable|sensible|steep|"
    r"a\s+lot|about\s+right|right|ok|okay|good|decent)\b",
    re.I)


def _not_a_figure_judged(understood):
    """Whether the line is asking whether a figure they have is a normal one.

    The overpayment row is keyed on a mistake word beside a payee, and its mistake words include
    `too much` and `twice`, which are also how people ask whether a price is high or how often
    something is done. A judgement on a figure is the price reader's question - it answers with
    the usual range for the thing - so this row stands down for it. A statement of the mistake
    is not this shape: "i paid the plumber too much" has no figure being judged and keeps the
    card, which is the line the row was written for.
    """
    text = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if not text:
        text = str((understood or {}).get("clean") or (understood or {}).get("text") or "")
    return not _A_FIGURE_JUDGED.search(text)


def _a_mark_that_came_with_it(understood):
    """Whether the mark is the delivery's rather than a fault found later.

    `scratch`, `dented` and `chipped` sit in BROKEN beside `damaged`, because a mark that came
    with the thing is the shop's complaint either way. Which card answers it is the difference
    between a note on the delivery note and the six-month reversal: "my sofa arrived with a
    scratch" wants the first, "my sofa is scratched" is a fault like any other. The arrival word
    is what tells them apart, so a line with both hands the ladder back.
    """
    text = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if not text:
        text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    return not (_IT_ARRIVED.search(text) and _A_MARK_THAT_CAME_WITH_IT.search(text))


def _a_stain_a_shop_answers_for(understood):
    """Whether a line with a stain in it is about the thing being bought rather than cleaned.

    "stained" sits beside "damaged" and "scratched" in BROKEN because a mark that came with the
    thing is the same complaint as a phone that will not switch on. On its own, though, the word
    is just as often a housekeeping question - "there is a stain on my sofa", "how do i get a
    stain out of a mattress", "my shoes are stained" - and the ladder's answer ("take it back to
    the shop and say you are rejecting it") is nonsense for a sofa somebody has had a year. The
    two are told apart by whether the line says the thing is new, has just come, or is going
    back, so the row asks this first. A line with no stain in it is not this guard's business.
    """
    text = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if not text:
        text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if not _A_MARK_ON_ANYTHING.search(text):
        return True
    return bool(_A_BUYING_LINE.search(text))


# A line that asks how to do something to the thing already in the person's hand is a method
# question about something they own, not a claim against the shop. "how do i get a scratch off my
# phone screen" was answered with the reject-it-within-30-days ladder, which nobody asks of a
# two-year-old phone. The `avoid` list above spells out the asks it knew ("how do i remove",
# "how do i clean", "how do i repair") and a list of phrasings cannot hold every one of them, so
# the shape of the ask is the guard: a how-to with nothing about buying the thing in the line keeps
# its own answer, and a how-to that names the buying keeps the ladder ("how do i get a refund",
# "how do i return shoes i bought online that dont fit").
_A_HOW_TO_ASK = re.compile(
    r"\b(?:how do i|how can i|how to|how do you|how would you|what'?s the best way|"
    r"what is the best way|best way to|any tips|any advice|what should i use)\b|"
    # the same ask stated as a question about what is possible: "my phone screen is scratched,
    # can i fix it", "my phone screen is scratched can it be repaired". These read as a claim to
    # the ladder ("scratched" is in BROKEN) and are a method question about the thing in the
    # person's hand, exactly like the how-tos above. Only the pronoun object is here: "can i fix
    # a scratch on my watch face" names a thing the bot has no card for, and the honest punt is
    # no better than the ladder it would replace, so that line is left as it is.
    r"\b(?:can (?:i|you|we) (?:fix|repair|mend|save) (?:it|this|that|them|these|those|mine)|can "
    r"it be (?:fixed|repaired|mended|saved)|is it (?:fixable|repairable)|is there a way to "
    r"(?:fix|repair|mend) (?:it|this|that))\b", re.I)


# Whether to mend the thing or swap it is a decision about a thing the person owns, and the
# ladder answers a different question (what the shop owes). "my phone screen is smashed, replace
# or repair" and "my washing machine is broken, repair or replace" were both told to take it back
# inside 30 days, which is not what someone with a two-year-old phone is asking. Both word orders
# are here, because "replace or repair" and "repair or replace" are written about equally.
# "theyre saying its my fault" names no shop and no thing, and the blame could be a partner's:
# the row answers when the line names the shop or the thing it is about.
_A_A_SHOP_OR_A_THING = re.compile(
    r"\b(?:shops?|stores?|retailers?|sellers?|company|currys|argos|amazon|ebay|john lewis|"
    r"screwfix|phones?|laptops?|tvs?|telly|screens?|coat|coats|shoes|trainers|jumper|jumpers|"
    r"dress|dresses|watch|watches|hoover|machines?|washing machine|dishwasher|fridge|freezer|"
    r"oven|kettle|items?|product|products|goods|warranty|guarantee|receipt|refund|faulty|"
    r"broken|wear and tear|worn out)\b", re.I)


def _the_shop_or_the_thing_is_named(understood):
    """False for a blame with no shop and no thing in it: that is not a sale yet."""
    text = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if not text:
        text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    return bool(_A_A_SHOP_OR_A_THING.search(text))


_A_REPAIR_OR_REPLACE = re.compile(
    r"\b(?:repair or replace|replace or repair|fix or replace|replace or fix|fix it or buy|"
    r"repair it or buy|repair or buy|mend or replace|replace or mend|or a repair|"
    r"cheaper to repair|cheaper to replace|worth a repair|worth repairing|worth replacing|"
    r"should i (?:repair|fix|mend|replace)|(?:repair|fix|mend|replace) it or|new one or)", re.I)


def _not_a_how_to_about_their_own_thing(understood):
    """False for a how-to that says nothing about buying, selling or the rights."""
    text = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if not text:
        text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if not _A_HOW_TO_ASK.search(text):
        return True
    return bool(_A_BUYING_LINE.search(text))


_A_SAVING_ACT = re.compile(r"\b(save|saves|saving|savings|saved|save\s+up|saving\s+up|"
                            r"put\s+away|putting\s+away|stash|stashing|set\s+aside|"
                            r"how\s+do\s+(?:i|we)\s+(?:save|get)|best\s+way\s+to\s+save|"
                            r"quickest\s+way\s+to\s+save)\b")
_A_DEPOSIT_PAID = re.compile(r"\b(paid|pay|paying|payments?|bought|buying|by\s+card|"
                             r"credit\s+card|debit\s+card|section\s+75|s75|chargeback|"
                             r"refund|money\s+back|dealer|shop|seller|company|landlord)\b")


def _not_saving_for_a_deposit(understood):
    """False when the deposit is a savings goal rather than a payment already made."""
    text = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if not text:
        text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if not _A_SAVING_ACT.search(text):
        return True
    return bool(_A_DEPOSIT_PAID.search(text))


def _not_a_repair_or_replace_decision(understood):
    """False when the line is deciding whether to mend the thing or buy a new one."""
    text = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if not text:
        text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    return not _A_REPAIR_OR_REPLACE.search(text)


# An old machine being weighed up for repair or replacement is the lifespan table's question, and
# the clock row kept answering it: "my washing machine is 8 years old and noisy, should i replace
# it" got six years of shop rights. The guard above reads the shape of the ask, and the row it
# guards is the ladder a shop owes; this one hands over only a machine that table has a row for -
# a phone, a laptop and a telly are weighed up by their own answers, and standing the clock down
# for them swapped one wrong card for another ("my telly is 7 years old, should i replace it" was
# answered with the screen-time hours for a five year old).
_A_MACHINE_THAT_WEARS_OUT = re.compile(
    r"\b(?:washing\s+machine|washer|tumble\s+dryer|tumbler|dishwasher|fridge\s+freezer|fridge|"
    r"freezer|oven|cooker|stove|hob|microwave|boiler|dryer|white\s+goods?|appliances?)\b", re.I)
# and a claim on an old machine is still this row's question: "can i still claim for a six year
# old washing machine" is what the clock is for.
_A_CLAIM_ON_IT = re.compile(
    r"\b(?:claim|refund|reject|rights|warrant\w*|guarantee|receipt|shop|retailer|seller|"
    r"entitled|obliged|sold\s+as\s+described)\b", re.I)


def _not_an_old_machines_repair_decision(understood):
    """False when an old machine in the house is being weighed up for repair or replacement."""
    if _not_a_repair_or_replace_decision(understood):
        return True
    text = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if not text:
        text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if _A_CLAIM_ON_IT.search(text):
        return True
    return not _A_MACHINE_THAT_WEARS_OUT.search(text)
# A deposit held on a table, a slot or an appointment is not a deposit held on a house, and the
# tenancy rows answer the house. "can i get my deposit back" on its own is a tenancy, so the two
# booking rows ask this first: a person asking about a booking names the place or the thing they
# booked, and a person asking about a flat names nothing of the sort.
_A_PLACE_THAT_TAKES_BOOKINGS = re.compile(
    r"\b(tables?|bookings?|reservations?|restaurants?|slots?|haircuts?|barbers?|salons?|"
    r"hairdressers?|garages?|viewings?|dinner|meals?|lunch|massages?|nails|spa|cafe|pub)\b")


def _a_place_that_takes_bookings(understood):
    """Whether the line names something a booking is taken for, rather than money held on a home.

    "can i get my deposit back" was this row's while it keyed "deposit" and "back" alone, and the
    answer - cancel in writing, the notice they set - is nonsense for a landlord. The tenancy
    answer is the right one there, and it is a different row.
    """
    text = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if not text:
        text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    return bool(_A_PLACE_THAT_TAKES_BOOKINGS.search(text))


# "cancelled my booking" is two different lines: the place doing it to you, and you doing it. The
# first is "the restaurant cancelled my booking" and the second is "i need to cancel my booking",
# which the words alone put on the same entry because "cancel" and "cancelled" share a stem.
_I_AM_THE_ONE_CANCELLING = re.compile(
    r"\b(how do i|how can i|how to|how do we|i need to|i want to|i have to|i would like to|"
    r"i forgot to|i forgot|should i|we need to|we want to|we have to|can i|do i need to|"
    r"id like to|i am going to|im going to)\b.{0,24}"
    r"\b(cancel|can/ ?cel|cancelling|canceling|call off|calling off|change|move|reschedule|"
    r"postpone|switch)\b")


def _they_are_the_ones_cancelling(understood):
    """Whether the line is about the place calling the booking off rather than the person.

    "i need to cancel my booking" and "i forgot to cancel my booking" were both told "if they
    cancel, the deposit comes back", which answers a question the person had not asked. The row
    answers the other direction, so a line where the person is the one cancelling stands it down.
    """
    text = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if not text:
        text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    return not _I_AM_THE_ONE_CANCELLING.search(text)


# A machine that dies gives up with nothing after it: "my laptop gave up", "my old hoover packed
# in". The same words with an object are a habit the person has stopped - "i gave up smoking 2
# years ago", "i gave up sugar last year", "i packed in the booze" - and all of those were told
# to take the goods back to the shop, because "gave up" and "packed in" are in BROKEN for a
# machine that dies. The object is what tells the two apart, read off the whole line rather than
# the phrase: a device that dies names nothing after it, and a person quitting names what they
# quit. A word after the phrase that is neither an activity nor anything anybody quits ("my car
# gave up on me", "the tv gave up the ghost", "my laptop gave up last week") is the device dying
# again, so the ladder keeps those lines.
_GIVES_UP = re.compile(
    r"\b(?:gave|give|given|gives|giving)\s+up\b|\b(?:packed|packs|packing)\s+in\b")
# The owner of the habit, which sits between the phrase and what was given up: "i gave up my
# morning coffee", "she packed in the cigarettes".
_BEFORE_THE_OBJECT = frozenset("the a an my his her their our your its this that these those "
                               "all any some it him them me us".split())
# What people quit, beyond the activities said with an "-ing" word. Closed, because a word here
# stands the refund ladder aside: nothing a person owns is in it, so "i gave up the old kettle"
# and "i gave up my car" stay with the row that can see the thing.
_WHAT_PEOPLE_QUIT = frozenset("""sugar meat dairy gluten caffeine alcohol booze fags cigs
cigarettes tobacco nicotine chocolate sweets carbs bread pasta rice cheese butter milk salt
takeaways takeaway drink diet weed dope vaping vegan car cars van motorbike bike""".split())


def _the_device_gave_up(understood):
    """False when the line's dying phrase is a habit the person gave up instead.

    Read off the whole line, because neither word decides on its own: "gave up" is a machine
    dying, "gave up smoking" is a person quitting, and the word after the phrase says which.
    """
    words = [str(one).lower() for one in ((understood or {}).get("words") or ())]
    if not words:
        text = str((understood or {}).get("clean") or (understood or {}).get("text") or "")
        words = text.lower().split()
    if not words:
        return True
    # A thing named anywhere in the line keeps the refund answer: whatever else it says, the line
    # is about something that has gone wrong with what they bought.
    if any(word in THINGS for word in words):
        return True
    hit = _GIVES_UP.search(" ".join(words))
    if hit is None:
        return True
    after = " ".join(words)[hit.end():].split()
    while after and after[0] in _BEFORE_THE_OBJECT:
        after.pop(0)
    if not after:
        return True
    object_word = after[0]
    if object_word == "ghost":
        return True                      # "the tv gave up the ghost"
    if object_word.endswith("ing") and len(object_word) > 4:
        return False                     # smoking, drinking, eating, biting, vaping
    return object_word not in _WHAT_PEOPLE_QUIT


def _not_a_kitchen_or_a_stopped_machine(understood):
    """The guards on the faulty-goods entry: any one of them hands the line back."""
    return (_not_a_kitchen_ask(understood) and _a_machine_that_stopped(understood)
            and _the_device_gave_up(understood)
            and _a_stain_a_shop_answers_for(understood)
            and _not_the_flats_own_appliance(understood)
            and _a_mark_that_came_with_it(understood)
            and _not_a_how_to_about_their_own_thing(understood)
            and _not_a_repair_or_replace_decision(understood)
            and _a_brake_cable_repair_ask(understood))


# A room in somebody's own home is not a hotel room. The bad-room entry keys the bare word
# "room", because "the room was filthy" and "our room smelled of damp" are how people describe
# a hotel room they are standing in - and it then took lines with no hotel in them at all:
# "how do i get rid of damp smell in a room" and "why does my room smell musty" were both told to
# photograph it and complain at reception. What this row answers is a room that came with a
# booking, so a line that says the booking keeps it, and a line that says the home keeps the
# home's own answer.
HOTEL_ROOM_WORDS = (
    "hotel", "hotels", "guest house", "guesthouse", "b and b", "bed and breakfast",
    "airbnb", "villa", "apartment", "suite", "holiday let", "cottage", "chalet", "hostel",
    "resort", "booked", "booking", "reception", "check in", "checkin", "check out",
    "checkout", "we stayed", "stayed at", "our stay", "the stay", "per night", "a night",
    "on holiday", "abroad", "sea view", "balcony", "package",
)
# The words that put the room in somebody's own home: the possessive ("my room", "our flat"),
# the damp the landlord should be told about, or the spare part of a house. Not the bare
# "room" - that is the word this row exists for - and not a bare "damp" either: "our room
# smelled of damp" is a complaint about a hotel room people have just walked into.
HOME_ROOM_WORDS = (
    "my room", "my bedroom", "my flat", "my house", "my home", "my place", "my living room",
    "our flat", "our house", "our home", "our place", "landlord", "tenancy", "tenant",
    "rented", "renting", "council house", "bedroom", "cellar", "basement", "attic",
    "hallway", "landing", "conservatory", "garage", "damp patch", "damp course",
    "rising damp", "damp proof",
    # the default when a line names no side at all is the hotel, so the rooms of a home have to
    # be listed or they fall through to the complaint: "the wet room smells" was answered by the
    # front-desk script, because a wet room is a room and nothing here said "home"
    "wet room", "shower room", "en suite", "ensuite", "spare room", "box room", "utility room",
    "utility", "boxroom", "sitting room", "dining room", "spare bedroom", "guest bedroom",
)
# ...or the line is asking how to fix the damp, which is the home's question whatever room it
# names: "how do i dry out a damp room" and "how do i get rid of damp smell in a room".
_A_DAMP = ("damp", "musty", "mould", "mold", "condensation", "smell", "smells", "smelling")
_A_FIX = ("get rid of", "dry out", "dry a", "dry the", "dry it", "treat", "fix", "stop",
          "cure", "sort out", "deal with", "how do i", "how to", "prevent", "clean")


def _a_hotel_room_or_no_home(understood):
    """Whether a bad-room line is a room that came with a booking."""
    text = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if not text:
        text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    # "en suite" holds the hotel's word "suite" inside it, so the room is read before the words
    # that would call it a booking: "the en suite smells" was the front-desk script
    if any(phrase in text for phrase in ("en suite", "ensuite", "wet room", "shower room")):
        return False
    if any(phrase in text for phrase in HOTEL_ROOM_WORDS):
        return True
    if any(phrase in text for phrase in HOME_ROOM_WORDS):
        return False
    if any(word in text for word in _A_DAMP) and any(word in text for word in _A_FIX):
        return False
    # A room with no word either way stays here: "the room was filthy" is the complaint that
    # this row exists for, and a home line that this cannot tell from a hotel one is better
    # answered by the complaint card than by whatever row the bare word "room" reaches next.
    return True


# --- a fridge on the blink is not a refund yet -------------------------------------------
#
# The spoiled-food row keys "fridge" for the food inside it, and it also keys "warm", for the
# food that went warm while the appliance was off. "Why does food go warm in the fridge" is the
# opposite question - the box itself is not cold - and it was answered with "photograph the
# inside of the fridge and the shop owes you a repair", which is the letter you write after the
# food is binned. The fault row in home.py has the thermometer answer, so this row hands those
# lines back. The shapes are the words that make the fridge the subject; a person holding the
# food says "the food went warm", which is still this row.
FRIDGE_IS_THE_QUESTION = (
    "go warm", "goes warm", "going warm", "gone warm", "getting warm", "gets warm", "grew warm",
    "too warm", "not cold", "isnt cold", "is not cold", "is it cold", "feels warm", "feels cold",
    "is warm", "is cold", "partially warm", "slightly warm", "half warm", "barely cold",
    "temperature", "thermometer",
    "not cooling", "not freezing", "stopped getting cold", "not getting cold",
    # and the cooling ask, which is about putting something in rather than a fault at all:
    # "should i put warm food in the fridge" and "can i put warm food in the fridge" were
    # reaching this row's "warm" key, and the answer is what freshness.cool-before-fridge says.
    "put warm", "put hot", "put a warm", "put a hot", "putting warm", "putting hot",
    "warm food in", "hot food in", "still warm", "let it cool", "leave it to cool",
    "cool before", "cooling before", "cool it first", "cool first",
)


# A line about the warm fridge that also asks who pays is this row's own question, whatever else
# it says: "fridge is warm and everything inside is ruined can i claim" is the ruined-food letter,
# not the thermometer. With the fridge shape standing the row down, that line fell to
# travel.py's cold-drinks row, because a "can" is a can of drink as well as the modal.
THE_CLAIM = (
    "claim", "claims", "claimed", "claiming", "refund", "refunded", "money back", "compensat",
    "who pays", "insurance", "insured", "ruined", "ruin", "wasted", "waste", "threw it out",
    "threw it all away", "thrown out", "binned it", "bin it all", "go off", "went off",
    "spoiled", "spoilt", "off food",
)


# The words that make a spoiled-food line a question about money rather than a fault to find.
THE_MONEY = (
    "claim", "claims", "claimed", "claiming", "refund", "refunded", "money back", "compensat",
    "who pays", "insurance", "insured", "reimburse", "get my money", "paid for", "pay for",
)


# A bottle or tub of fresh dairy that has turned is its own question, and this row is about who pays when the
# appliance has failed: "the milk in my fridge smells off but the date is fine" was answered with a
# photograph of the fridge and a repair claim, which is the wrong worry entirely. A food named
# with nothing wrong with the appliance stands this row down, and the card that owns that food
# answers instead. "Fridge is warm and the milk smells off" keeps this row, because the appliance
# word is there.
_FOOD_NAMED = re.compile(
    r"\b(?:milk|yoghurt|yogurt|cream|creme fraiche|creme fresh|soured cream|sour cream)\b")
_APPLIANCE_TROUBLE = re.compile(
    r"\b(?:warm|warming|warmed|broke|broken|power|electricity|fuse|thawed|defrosted|ruined|"
    r"stopped|cut|leaking|not cold|isnt cold|isn't cold|door left|left open)\b")


def _not_the_fridge_asking_why(understood):
    """False when the line is about the fridge being warm rather than the food in it.

    Unless it also asks who pays for the food: that is this row's question even when the fridge
    is the thing that is warm.
    """
    text = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if not text:
        text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    # Only a line that asks who pays is the ruined-food letter. "fridge not cold food ruined"
    # says the food is ruined and asks nothing about money, and what that person needs is the
    # thermometer and the door seal, so the fault row keeps it.
    if any(phrase in text for phrase in THE_MONEY):
        return True
    if _FOOD_NAMED.search(text) and not _APPLIANCE_TROUBLE.search(text):
        return False
    return not any(phrase in text for phrase in FRIDGE_IS_THE_QUESTION)


def _not_a_kitchen_ask(understood):
    """Whether this is the refund answer rather than the what-can-i-cook-now answer.

    The kitchen answer is written for a person whose appliance has gone and who still has to
    eat or bake, and it is the better reply to "i want to bake a cake but my oven is broken" -
    which was getting the refund ladder, because an oven that has broken is an oven the kitchen
    has not got. A line that asks about the money is not one it answers, so the ladder keeps
    every right question and hands back only the cooking ones.
    """
    from .cooking import without as _without_an_appliance

    text = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if not text:
        text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if any(phrase in text for phrase in KITCHEN_QUIET):
        return True
    return not (_without_an_appliance(understood) or "").strip()


def faulty_goods_reply(memory, reading):
    """The refund ladder, with the six-month reversal only while it is still the rule."""
    months = _age_in_months(reading)
    if months is not None and months > 6:
        return FAULTY_REPLY + SIX_MONTH_PASSED
    return FAULTY_REPLY + SIX_MONTH_REVERSAL


_CANCEL_WORDS = ("cancel", "cancelled", "canceled", "cancelling", "canceling", "quit",
                 "left it", "left the")


_FLAT_FEE_WORDS = ("restocking fee", "restocking", "handling fee", "return fee", "return fees",
                   "collection fee", "re stocking fee")


# A bag that is broken at home is not a claim at an airline's baggage desk: the desk, the PIR
# reference and the 7 and 21 day limits only exist for a bag that was checked in. The entry's
# key is a thing ("baggage", "suitcase", "bags", "case") beside a state ("broken", "ripped",
# "lost"), and both halves are ordinary on their own, so "my bag is broken" and "the zip on my
# bag broke" were answered with the airport. Travel has to be said in the line for the airline
# to be the right desk; "baggage" and "luggage" say it by themselves, and a suitcase or a bag
# that never arrived or went missing does too.
TRAVEL_SAID = ("airport", "airports", "flight", "flights", "airline", "airlines", "plane",
               "planes", "flying", "fly", "flew", "terminal", "carousel", "baggage reclaim",
               "baggage hall", "check in", "check-in", "checked in", "checked bag",
               "boarding", "connection", "stopover", "abroad", "overseas", "holiday",
               "holidays", "trip", "travel", "travelling", "traveling", "easyjet", "ryanair",
               "british airways", "jet2", "wizz", "tui", "virgin atlantic", "pir")

# The travel words that are the whole question: a bag or luggage that has not turned up is the
# airline's, wherever the person is standing when they type it.
GONE_MISSING = ("lost", "missing", "delayed", "didnt arrive", "didn't arrive", "never arrived",
                "went missing", "gone missing", "stolen", "damaged", "smashed", "crushed",
                # a bag that never came out on the belt is the airline's wherever the person is
                # standing when they type it, so the guard lets these through too
                "never came out", "didnt come out", "didn't come out", "didnt come off",
                "didn't come off", "never turned up", "didnt turn up", "didn't turn up",
                "still not arrived")

# The bag that came off the belt. "My case came out with a broken wheel" is the airline's bag,
# and the line says it as what the bag did rather than where it was, so none of the travel words
# above catches it: "came out" only counts here, where the words beside it are already a bag and
# a fault, so "the stain came out" and "my tooth came out" never reach this guard.
CAME_OFF_THE_BELT = ("came out", "come out", "came back", "came off the plane", "off the plane",
                     "came off the belt", "on the belt", "off the carousel", "reclaim",
                     "trolley", "hold luggage", "checked luggage")


# A holiday booked with an employer is not a holiday booked with a tour operator, and the two
# answers are opposites: "my boss keeps cancelling my holiday" was told what a cancellation charge
# costs the person doing the cancelling, and "my boss wont let me take my holiday" was told to ask
# for a figure for the closed pool. Booked leave is the work rows' line.
EMPLOYER_WORDS = ("boss", "manager", "managers", "employer", "employers", "hr", "human resources",
                  "my work", "work wont", "work won't", "by work", "because of work", "work cancelled",
                  "work has cancelled", "work said no", "company i work for", "annual leave",
                  "booked leave", "my leave", "day off", "days off", "time off", "rota",
                  "shift", "shifts", "my contract", "my job")


def _the_employer_is_who_stopped_it(understood):
    """Whether the leave here is booked with an employer rather than a travel company."""
    if isinstance(understood, dict):
        text = " ".join(str(one) for one in (
            understood.get("clean"), understood.get("text"), understood.get("raw"),
            " ".join(str(word) for word in (understood.get("words") or ()))))
    else:
        text = str(understood or "")
    text = " " + " ".join(text.lower().replace("'", "").replace(",", " ").split()) + " "
    # a flight or a hotel means it is a real holiday, whatever else the line says
    for word in ("flight", "flights", "airline", "airport", "hotel", "resort", "package",
                 "abroad", "tour operator", "travel agent", "booking reference", "atol"):
        if " %s " % word in text:
            return False
    return any(" %s " % word in text for word in EMPLOYER_WORDS)


# The break clause is the tenancy's own question, and it holds the word "notice" because the
# clause names how much the clause itself takes. The notice the tenant writes to end the tenancy
# is a different question with its own row, and the two meet on the same words. Who is giving the
# notice is the tell: "how much notice do i need to give my landlord" is the tenant's letter, and
# "can my landlord stop me moving out early" and "my landlord says i cant leave early" are the
# clause, so the row stands down on the giving and never on the landlord.
_THE_NOTICE_IS_GIVEN = re.compile(
    r"\b(?:give|gives|giving|gave)\b[^.?!]{0,30}\b(?:notice|keys)\b|"
    r"\bnotice\b[^.?!]{0,25}\b(?:to give|i give|do i give|before i (?:go|leave|move)|"
    r"letter|in writing)\b", re.I)


# ...and the letter is written TO the landlord, so the line has to name them as well. The tenancy
# words alone are not enough: "how much notice do i give to leave my flat" is the clause and has no
# landlord in it, and standing this row down for it left the hedge answering.
_NAMES_THE_LANDLORD = re.compile(r"\blandlords?\b|\blandlady\b|\bletting agents?\b", re.I)


def _the_notice_is_theirs_to_give(understood):
    """False when the line is the notice the tenant writes, which is the leaving-letter row."""
    if not isinstance(understood, dict):
        return True
    text = str(understood.get("clean") or understood.get("text") or "")
    return not (_THE_NOTICE_IS_GIVEN.search(text) and _NAMES_THE_LANDLORD.search(text))


def _not_a_leave_question(understood):
    """False when it is leave from work: the work rows answer that one."""
    return not _the_employer_is_who_stopped_it(understood)


def _a_bag_at_the_airport(understood):
    """Whether the airline's baggage desk is the right place to send this bag.

    It answers a bag that was on a plane: the line says travel, or it says a bag is gone (lost,
    missing, never arrived), or the thing named is "baggage" or "luggage", which are travel
    words themselves. A bag that has broken at home keeps its own answer, because a zip that
    went in a doorway is not a PIR reference.
    """
    text = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if not text:
        text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    text = " " + " ".join(text.replace(",", " ").replace(".", " ").split()) + " "
    if any(" %s " % word in text for word in TRAVEL_SAID):
        return True
    if any(" %s " % phrase in text for phrase in CAME_OFF_THE_BELT):
        return True
    if "baggage" in text or "luggage" in text:
        return True
    return any(" %s " % word in text for word in GONE_MISSING)


def _return_costs_reply(memory, understood):
    """Who pays to send it back, unless a flat fee is the question.

    A restocking or handling fee charged on a return is a different sentence from who pays the
    postage, so a line that names one gets that rule first."""
    text = ""
    if isinstance(understood, dict):
        text = " ".join((str(understood.get("clean") or ""), str(understood.get("text") or ""),
                         str(understood.get("raw") or ""),
                         " ".join(str(w) for w in (understood.get("words") or ())))).lower()
    if any(phrase in text for phrase in _FLAT_FEE_WORDS):
        return ("A flat restocking or handling fee on a return is not allowed - they can only "
                "deduct for damage you caused - and on a faulty or misdescribed item the retailer "
                "pays the postage too. Write asking for the full price back, say it is going back as "
                "faulty, and ask for a prepaid label or a collection; if they keep the fee, the card "
                "provider can charge back that amount.")
    return ("Faulty, misdescribed or simply not what you ordered: the retailer pays to get it back, "
            "so ask for a prepaid label or a courier collection rather than posting it yourself, and "
            "say in the email that it is going back as faulty. On a change of mind bought online you "
            "pay the return delivery unless their terms promised free returns, and a restocking fee "
            "is not allowed.")


# "i dont like it" and "not what i expected" are the two mind shapes that only mean goods when
# the line also says something was bought: alone they are what a person says about a recipe, a
# film or the weather. The rest of the mind words ("i changed my mind", "i wish i hadnt bought")
# carry the purchase in the phrase itself.
_MIND_LIKE = re.compile(
    r"\b(?:dont|don't|do not|didnt|didn't|dont really)\s+(?:\w+\s+){0,2}like\s+"
    r"(?:it|them|this|that|these|those)\b|\bnot what i expected\b|\bnot what i thought\b",
    re.IGNORECASE)
_A_PURCHASE_TRACE = re.compile(
    r"\b(?:bought|buy|buying|order|ordered|shop|shops|store|online|website|internet|"
    r"receipt|tags|packaging|box|return|refund|exchange|delivered|delivery|courier|"
    r"dress|shirt|top|blouse|jumper|coat|jacket|trousers|jeans|shorts|skirt|shoes|boots|"
    r"trainers|sandals|sofa|settee|chair|table|desk|bed|mattress|wardrobe|shelf|shelves|"
    r"hoover|vacuum|cooker|oven|fridge|freezer|dishwasher|washing machine|tumble dryer|"
    r"phone|tablet|laptop|computer|tv|telly|headphones|carpet|rug|curtains|blinds|lamp|"
    r"bag|handbag|watch|ring|gift|present|item|thing i|pair of)\b", re.IGNORECASE)


def _mind_is_about_goods(understood):
    """True unless the only mind in the line is a taste, with nothing bought named beside it."""
    text = " " + str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower() + " "
    if not _MIND_LIKE.search(text):
        return True
    return bool(_A_PURCHASE_TRACE.search(text))


def _described_reply(memory, understood):
    """Goods that are not what they were said to be, in the two shapes people send.

    A fabric or a colour that is not as advertised, and a thing sold as new that was used, a
    shop's display model or a refurb. Both are misdescription under the same Act, but the first
    sentence a person needs is different, so the line picks it."""
    text = ""
    if isinstance(understood, dict):
        text = " ".join((str(understood.get("clean") or ""),
                         str(understood.get("text") or ""),
                         str(understood.get("raw") or ""))).lower()
        text += " " + " ".join(str(w).lower() for w in (understood.get("words") or ()))
    if any(phrase in text for phrase in _WAS_USED_WORDS):
        return ("Sold as new but used, opened, a shop's display model or a refurb is a "
                "misdescription, so you can reject it for a full refund and you do not have to take "
                "a discount or a credit note: write to the shop saying what you were sold and what "
                "arrived, with photos of the wear, the serial number and the box. Do it inside 30 "
                "days, keep the listing that said new, and if they refuse, a card chargeback or "
                "Section 75 over £100.")
    return ("Goods have to match their description: a sofa sold as leather that is vinyl, a jumper "
            "labelled 100% cotton that is not, a colour nothing like the photo. That is a "
            "misdescription under the Consumer Rights Act 2015, so you can reject it for a full "
            "refund and do not have to accept a credit note. Say in writing what you were told and "
            "what arrived, with photos, and give them 14 days; if they refuse, a card chargeback or "
            "Section 75 over £100.")


_WAS_USED_WORDS = ("refurbished", "refurb", "instead of new", "not new", "sold as new",
                   "ex display", "ex-display", "display model", "shop soiled", "opened box",
                   "used one", "second hand one", "second-hand one", "was used", "already used",
                   "brand new but")

# "they said", "he said", "the label" and "but its" are pronouns, not a complaint about goods.
# On their own they reached this row on any second product word: "he said his phone died" and
# "my laptop screen went black but its still on" were both told about the Consumer Rights Act.
# A description is only the subject when the line names what it should have been - a material,
# a colour, a size, a photo, or a refurb - so the row stands down when none of these is there.
_DESCRIBED_WORDS = frozenset((
    "leather", "wool", "cotton", "silk", "linen", "fabric", "material", "vinyl", "polyester",
    "plastic", "colour", "color", "shade", "size", "photo", "photos", "photograph",
    "photographs", "picture", "pictures", "description", "advert", "advertisement",
    "refurbished", "refurb", "fake", "counterfeit", "genuine", "used", "new",
    # the property that was promised counts as the description too: "waterproof" and
    # "non-stick" are as much a claim about the goods as "leather" is
    "waterproof", "showerproof", "windproof", "unbreakable", "heatproof", "fireproof",
    "nonstick", "non-stick", "stainless", "solid", "oak", "wooden", "wood", "metal",
    "steel", "aluminium", "aluminum", "copper", "brass", "gold", "silver", "glass",
    "ceramic", "bamboo", "rubber", "marble", "granite", "stone", "pure", "organic",
    "vegan", "vegetarian", "gluten", "unsweetened", "sugarfree", "sugar-free", "diet",
    "washable", "breathable", "insulated",
))
_DESCRIBED_PHRASES = ("as described", "not as described", "as advertised", "as new",
                      "sold as", "described as", "advertised as", "listed as", "not what",
                      "the label said", "label said", "the ad said", "the listing",
                      "the description", "second hand", "second-hand", "ex display",
                      "ex-display", "display model", "shop soiled", "opened box", "brand new",
                      "knock off", "not real", "not genuine", "grey import")


# "how do i invest in stocks" is the shares question, and this row took it: the reading folds
# "stocks" onto "stock", so a delivery key that holds "in stock" sees a stake in a company as a
# parcel on its way. The words cannot be fenced off with `avoid` either, because the same folding
# makes an avoid word "stocks" stand the row down on "is this in stock" and "when will it be back
# in stock" (measured: both lost the promise-date card). So the line itself is asked what its
# "stock" is: beside an investing word it is a share, and the delivery row stands down.
_A_STAKE_IN_A_COMPANY = re.compile(
    r"\b(?:invest|invests|invested|investing|investment|investments|share price|shares|"
    r"stock market|stock exchange|dividends?|portfolio|broker|brokerage|trading|"
    r"buy stocks?|sell stocks?|buy shares|sell shares|holdings)\b")


def _stock_is_not_a_parcel(understood):
    """False when the line's "stock" is a share in a company rather than goods on a shelf."""
    if not isinstance(understood, dict):
        return True
    text = " ".join((str(understood.get("clean") or ""), str(understood.get("text") or ""),
                     str(understood.get("raw") or ""))).lower()
    return not _A_STAKE_IN_A_COMPANY.search(text)


def _a_description_is_named(understood):
    """Whether the line names what the goods should have been, not just a pronoun and a product."""
    if not isinstance(understood, dict):
        return True
    words = {str(word).lower() for word in (understood.get("words") or ())}
    if words & _DESCRIBED_WORDS:
        return True
    text = " ".join((str(understood.get("clean") or ""), str(understood.get("text") or ""),
                     str(understood.get("raw") or ""), " ".join(words))).lower()
    return any(phrase in text for phrase in _DESCRIBED_PHRASES)


_SALE_TAG_WORDS = ("sale", "reduced", "clearance", "discount", "end of line", "last one",
                   "it was cheap", "bargain")


def _shop_return_reply(memory, understood):
    """Bringing something back to a shop, with the sale-tag excuse only when they raise it.

    A jumper in the wrong size is the shop's own policy on a change of mind. A shop that says
    "it was in the sale" is using a tag as a reason, and that needs the one extra sentence."""
    text = ""
    if isinstance(understood, dict):
        text = " ".join((str(understood.get("clean") or ""),
                         str(understood.get("text") or ""),
                         str(understood.get("raw") or ""))).lower()
        text += " " + " ".join(str(w).lower() for w in (understood.get("words") or ()))
    reply = ("In a shop, bringing something back because you changed your mind is the shop's own "
             "policy, not a right: 28 days for an exchange is common, and a bank statement usually "
             "does instead of a receipt. Faulty is different - 30 days to reject it for a full "
             "refund, and no returns sign can take that away.")
    if any(word in text for word in _SALE_TAG_WORDS):
        reply += (' A sale tag changes none of it, so "it was reduced" is not a reason to refuse a '
                  'faulty one.')
    return reply


_SERVICES_KINDS = (
    # (words that pick the kind, the sentence that kind needs). The words are whole words: a
    # "dress" in "hairdresser" is not a garment.
    (("groomer", "groomers", "grooming", "dog", "dogs", "cat", "cats", "puppy", "pet", "pets",
      "vet"), (),
     "A groomer that nicks or cuts an animal owes the vet bill, so get the vet to write down "
     "what it treated."),
    (("garment", "garments", "suit", "suits", "dress", "dresses", "coat", "coats", "jacket",
      "jackets", "trousers", "tailor", "tailors"),
     ("dry cleaner", "dry cleaners", "dry cleaning", "dry-clean", "laundrette", "alterations"),
     "A dry cleaner that shrank or stained a garment owes what it costs to replace, not the "
     "cleaning fee."),
    (("repair", "repaired", "repairs", "screen", "watch", "laptop", "washer", "hoover",
      "lawnmower", "mower"),
     ("repair shop", "phone repair", "the shop repaired"),
     "A repair that came back worse is the repairer's bill to put right, and a part they broke is "
     "their cost, not yours."),
)

_SERVICES_HAIR_WORDS = ("hair", "haircut", "haircutting", "barber", "salon", "nails", "nail",
                        "manicure", "pedicure", "tattoo", "eyebrow", "eyebrows", "waxing", "waxed",
                        "lashes", "cut", "trim", "colour", "dye")


def _services_ruined_reply(memory, understood):
    """A job done badly, with the sentence that job needs.

    The same entry answers a haircut, a dry cleaner, a repair and a groomer, and what each of
    those owes is different: a garment is what it costs to replace, a repair is the repairer's
    bill, an animal is the vet's. A cut or a tattoo cannot be undone, so that kind is told to get
    a second opinion in writing first."""
    text = ""
    if isinstance(understood, dict):
        text = " ".join((str(understood.get("clean") or ""),
                         str(understood.get("text") or ""),
                         str(understood.get("raw") or ""))).lower()
        text += " " + " ".join(str(w).lower() for w in (understood.get("words") or ()))
    words = set(re.findall(r"[a-z']+", text))
    reply = ("Photograph it straight away and ask for a refund the same day: you paid for the job "
             "done with reasonable care, and a botched one breaks that. Put the request in writing "
             "with 14 days to answer; if they refuse, Money Claims Online costs about £35.")
    for tokens, phrases, sentence in _SERVICES_KINDS:
        if words & set(tokens) or any(phrase in text for phrase in phrases):
            return reply + " " + sentence
    if words & set(_SERVICES_HAIR_WORDS):
        return reply + (" Get a second salon to write down what is wrong and what putting it "
                        "right would cost, because a cut, a colour or a tattoo cannot be undone.")
    return reply + (" A second opinion in writing - another salon, another repairer or the vet - "
                    "is the evidence that wins it.")


_PHONE_WORDS = ("phone", "call", "ring", "rang", "hold", "hang", "hung", "helpline",
                "customer service", "call centre", "call center", "transferred")


_PENSION_STOPPED_WORDS = ("not paid", "hasnt been paid", "hasn't been paid", "not been paid",
                          "havent been paid", "haven't been paid", "havent had", "haven't had",
                          "didnt get", "didn't get", "stopped", "short", "less than",
                          "not receiving", "missing payment", "underpaid")


# Several old pots is its own ask: nothing has gone missing, and the person wants to gather
# them up. "ive got three old ones" says it with an anaphor - "ones" is the pension the line
# already named - so the phrase is keyed beside "old pension".
_PENSION_SEVERAL_WORDS = ("old ones", "old one", "three old", "two old", "four old", "five old",
                          "several old", "a few old", "several pensions", "multiple pensions",
                          "a few pensions",
                          "a few old", "several old", "three pensions", "two pensions",
                          "four pensions", "five pensions", "several pots", "several schemes",
                          "a few schemes", "transfer my pensions", "move my pension")
# The verb that says the person already knows they have more than one, whatever the count:
# "should i combine my old pensions" is the same ask as "ive got three old ones".
_PENSION_COMBINE_WORDS = frozenset(("combine", "combining", "combined", "consolidate",
                                   "consolidating", "consolidated", "merge", "merging", "merged",
                                   "amalgamate", "amalgamating"))


# A follow-up on the number itself: "is that a lot", "is that normal", "how many is normal".
_A_COUNT_FOLLOW_UP = re.compile(r"\b(?:is|was) that (?:a lot|many|normal|usual|ok|okay|bad|"
                                r"too many|a problem)\b|\bhow many (?:is|are) (?:normal|usual|"
                                r"typical)\b|\bis (?:that|three) (?:a lot|normal|many)\b", re.I)


def _pension_reply(memory, understood):
    """A payment that has stopped is not a lost scheme.

    "My pension hasnt been paid" and "how do i trace an old pension" are two different first
    moves: one is a phone call to the scheme or the payroll, the other is the tracing service.
    The line picks which comes first rather than opening with the tracer for both. Several old
    pots covers neither, and has its own first move: the tracer finds them, then a statement
    from each decides whether any of them is worth leaving alone."""
    text = ""
    if isinstance(understood, dict):
        text = " ".join((str(understood.get("clean") or ""), str(understood.get("text") or ""),
                         str(understood.get("raw") or "")))
        text += " " + " ".join(str(w) for w in (understood.get("words") or ()))
    text = text.lower()
    if any(phrase in text for phrase in _PENSION_STOPPED_WORDS):
        return ("Ring the scheme, or the payroll if you are still working, and ask why the payment "
                "stopped or came up short: they have to tell you and put it right, and most are "
                "sorted on that call. Ask for it in writing, give them eight weeks, then the "
                "Pensions Ombudsman is free and can order the money paid. If it is the State "
                "Pension, ring the Pension Service instead, and check your forecast on gov.uk for "
                "the date and amount it should be.")
    asked = " ".join(str((understood or {}).get(k) or "")
                     for k in ("clean", "text", "norm_text", "plain")).lower()
    if _A_COUNT_FOLLOW_UP.search(asked):
        last = ""
        turns = [t for t in (memory or {}).get("turns") or [] if isinstance(t, dict)]
        if turns:
            last = str(turns[-1].get("bot") or "").lower()
        if "old pots" in last or "old pensions" in last:
            return ("Three or four is normal - most people build one up at every job they leave. "
                    "What is worth a look is the fee each pot charges and whether any of them has "
                    "a guaranteed benefit, so ask each provider for a statement before you decide "
                    "to move anything.")
    words = set(re.findall(r"[a-z']+", text))
    if any(phrase in text for phrase in _PENSION_SEVERAL_WORDS) \
            or words & _PENSION_COMBINE_WORDS:
        return ("Three or four old pots is normal, and none of it is lost money: give each "
                "employer's name to the free Pension Tracing Service, then ask every provider for "
                "a statement - the value, the fees and any guaranteed benefits. Check those "
                "guarantees before you move anything, because a final-salary promise is usually "
                "lost in a transfer.")
    return ("Start with the free Pension Tracing Service if you have lost track of an old scheme: "
            "give it the employer's name and it returns the provider's details, then ask that "
            "provider in writing for a statement. For the State Pension, your forecast on gov.uk "
            "shows the date and the amount, and if a payment is missing complain to the scheme "
            "first and then to the free Pensions Ombudsman.")


# A row ending on the phone, which is not a shop ignoring a customer.
_SOMEONE_PUT_THE_PHONE_DOWN = re.compile(
    r"\b(?:put|puts|putting)\s+the\s+phone\s+down\b|\bhung up on me\b|\bhung up on him\b")
_SELLING_WORDS = re.compile(
    r"\b(?:shop|store|seller|retailer|company|order|orders|ordered|refund|refunded|delivery|"
    r"delivered|bought|buy|purchase|purchased|item|product|warranty|guarantee|receipt|invoice|"
    r"customer service|call centre|call center|supplier|marketplace|app)\b")


def _seller_ignoring_reply(memory, understood):
    """A seller who will not answer, in a letter or on the phone.

    The same entry answers a shop that ignores emails and a company whose call centre keeps
    cutting the line: the letter is the step that wins either way, and a phone line needs the
    call log on top of it."""
    text = ""
    if isinstance(understood, dict):
        text = " ".join((str(understood.get("clean") or ""),
                         str(understood.get("text") or ""),
                         str(understood.get("raw") or ""))).lower()
        text += " " + " ".join(str(w).lower() for w in (understood.get("words") or ()))
    # The word phone is not a call centre. "she put the phone down on me" and "he hung up on me"
    # are the end of a row, and the person's worst minute of the evening was answered with a
    # letter template about an order. The fence is the seller: nothing to do with a purchase in
    # the line, nothing for this card to say.
    if _SOMEONE_PUT_THE_PHONE_DOWN.search(text) and not _SELLING_WORDS.search(text):
        return None
    reply = ("Write one email that sets out the order, the fault and what you want, and give them "
             "14 days to answer: that email is what a card company or a court reads. If the "
             "silence continues, ask your card provider for a chargeback, or Section 75 over £100 "
             "on a credit card.")
    words = set(re.findall(r"[a-z']+", text))
    if words & set(_PHONE_WORDS) or "customer service" in text:
        reply += (" Keep a note of every call - the date, the number and who you spoke to - "
                  "because that log is what the ombudsman reads next.")
    return reply


def _fee_reply(memory, understood):
    """A fee sprung at the checkout, or a fee for a booking that never happened.

    Both are the same entry - money taken that was never agreed - but the first move is
    different: a drip-priced fee is disputed for being hidden, a cancellation or no-show fee is
    disputed because there was nothing to charge for."""
    text = ""
    if isinstance(understood, dict):
        text = " ".join((str(understood.get("clean") or ""),
                         str(understood.get("text") or ""),
                         str(understood.get("raw") or ""))).lower()
        text += " " + " ".join(str(w).lower() for w in (understood.get("words") or ()))
    if any(phrase in text for phrase in _DELIVERY_FEE_WORDS):
        return ("Delivery it said was free is not a charge you agreed to, so ask for it back: "
                "quote the page or the email that said free delivery, give them 14 days, and keep "
                "the order confirmation. If they will not refund it, the card provider can charge "
                "back that amount, and the Citizens Advice consumer helpline passes it to Trading "
                "Standards.")
    if any(phrase in text for phrase in _NEVER_HAPPENED_WORDS):
        return ("A fee for something that never happened is not owed: write to them and say when "
                "you cancelled or that you never booked it, ask for the charge back and for any "
                "no-show marker on your account to be removed. Keep the email and the date. If it "
                "came off a card, the card provider can charge back a fee you did not agree to, "
                "and for a gym or a salon the next step is their complaints procedure and then "
                "the trade body that covers them.")
    return ("The price you were shown has to include anything you have to pay, so a booking, admin "
            "or card fee sprung at the last screen is not something you owed: ask the company for "
            "it back in writing, say what total you were quoted, and point out the fee was not part "
            "of it. If they will not refund it, dispute that amount on the card, and report the drip "
            "pricing to Trading Standards through the Citizens Advice consumer helpline, which "
            "passes it on.")


# A fee named in the line and answered with "A booking fee is..." names the wrong fee back, so
# these have their own opening. Order matters: the longest phrase wins ("administration fee"
# before "admin fee"), so a person who wrote the long one is quoted it.
_OTHER_FEE_WORDS = ("administration fee", "admin fee", "service fee", "processing fee",
                    "convenience fee", "handling fee", "card fee", "transaction fee",
                    "surcharge")

_CANCEL_FEE_WORDS = ("cancellation fee", "cancellation charge", "cancelation fee",
                     "cancelation charge", "no show fee", "no-show fee", "failure to appear")

_LATE_FEE_WORDS = ("late fee", "late payment fee", "late charge", "late payment charge",
                   "charged for being late", "fee for paying late")


def _fee_kind_reply(memory, understood):
    """The plain ask about a named fee: what it is, whether it comes back, whether it is allowed.

    The same row answers four fees and each has its own first sentence, because "A booking fee is
    a charge for arranging the booking" is the wrong answer to "what is a late fee"."""
    text = ""
    if isinstance(understood, dict):
        text = " ".join((str(understood.get("clean") or ""),
                         str(understood.get("text") or ""),
                         str(understood.get("raw") or ""))).lower()
        text += " " + " ".join(str(w).lower() for w in (understood.get("words") or ()))
    if any(phrase in text for phrase in _LATE_FEE_WORDS):
        return ("A late fee is what you agreed to pay for paying after the due date, and it has to "
                "be in the terms you signed up to and no more than a fair estimate of the cost to "
                "them. If it was never in the terms, or it is far bigger than the debt, ask for it "
                "back in writing; for a bill or a loan the next step is the company's complaints "
                "then the energy or financial ombudsman, which is free.")
    if any(phrase in text for phrase in _CANCEL_FEE_WORDS):
        return ("A cancellation or no-show fee is what the terms said you would pay for cancelling "
                "late or not turning up, and it has to be a fair estimate of what they lost - so "
                "the same fee whatever notice you gave, or a fee when you gave plenty, is the kind "
                "to challenge: ask which term it comes from, then go to their complaints, Trading "
                "Standards through Citizens Advice, or the card provider.")
    for phrase in _OTHER_FEE_WORDS:
        if phrase in text:
            article = "an" if phrase[0] in "aeiou" else "a"
            return (f"{article.capitalize()} {phrase} is a charge added on top of the thing you are "
                    "buying rather than "
                    "payment for the thing itself, and it has to be inside the total price you are "
                    "shown before you pay - not added at the last screen. Ask what it covers before "
                    "you agree to it, and if you were quoted a price without it, ask them to take "
                    "it off: a fee that was never disclosed is not one you owed, and the card "
                    "provider can charge it back if they will not refund it.")
    if "cleaning fee" in text:
        return ("A cleaning fee is a fixed charge a host adds for the changeover between guests, "
                "and it belongs in the price you are shown before you book rather than arriving at "
                "checkout. It is not a fine: ordinary mess after a normal stay is what it covers, "
                "and extra can only be asked for damage or for something the listing warned about.")
    return ("A booking fee is a charge for arranging the booking rather than for the thing itself - "
            "a venue's or an agent's cut, or a platform's fee for running the site - and it has to "
            "be inside the total price you are shown before you pay, not added at the last screen. "
            "It is usually kept when you cancel even where the rest is refundable, so read what the "
            "terms say it covers before you pay; a fee that only appeared at checkout, or one "
            "charged for a booking that never happened, you can ask back and then dispute on the "
            "card.")


_TRIAL_WORDS = ("free trial", "trial period", "a trial", "the trial", "signed up for a trial",
                "signed up to a trial", "free for a month", "free for 30 days")


_DELIVERY_FEE_WORDS = ("delivery charge", "delivery fee", "charged for delivery", "free delivery",
                       "postage charge", "shipping fee", "postage was free", "delivery was free")


_NEVER_HAPPENED_WORDS = ("never booked", "didnt book", "didn't book", "never made",
                         "didnt make", "didn't make", "never happened", "no show",
                         "did turn up", "i was there", "never signed", "never asked",
                         "didnt ask", "didn't ask", "never went", "didnt go", "didn't go",
                         "cancelled in time", "canceled in time", "in advance", "with notice",
                         "gave notice", "i cancelled", "i canceled", "i did cancel")


def _renewed_reply(memory, understood):
    """A renewal nobody warned about, or a payment taken after the person cancelled.

    Both are the same entry: the company kept taking money it should not have. Which of the two
    a person is asking decides the first thing they can do, so the line picks the opening."""
    words = set()
    if isinstance(understood, dict):
        words = {str(w).lower() for w in (understood.get("words") or ())}
        words.update(str(understood.get("clean") or "").lower().split())
    text = " ".join((str(understood.get("clean") or "") if isinstance(understood, dict) else "",
                     " ".join(str(w).lower() for w in ((understood.get("words") or ())
                                                      if isinstance(understood, dict) else ()))))
    if any(phrase in text.lower() for phrase in _TRIAL_WORDS):
        return ("A free trial that charges you at the end has to tell you so before you sign up, "
                "with the price and the date it ends: if it did not, say the charge was not agreed, "
                "cancel in writing the same day and ask for the money back. A subscription bought "
                "at a distance can be cancelled within 14 days for a full refund, and if they will "
                "not pay, the card provider can charge it back.")
    if words & set(_CANCEL_WORDS):
        return ("A cancellation stands from the day you gave it, so a payment taken after that "
                "date has to come back: send the cancellation again in writing, ask for the "
                "confirmation and the date they logged it, and ask for the money taken since. "
                "Give them 14 days, then your card provider can charge it back with the email as "
                "proof. If they keep charging, ask them to remove your card details.")
    return ("A company that renews you has to warn you before it does, and a policy sold at a "
            "distance can be cancelled within 14 days of the renewal date, so ask for the renewal "
            "notice and the money back in writing, quoting the date it renewed. If they never sent "
            "a reminder, say so, cancel in writing the same day and keep the email: a charge you "
            "did not agree to is also a card chargeback, and over £100 on a credit card it is "
            "Section 75.")


BROKEN = ("faulty", "broken", "defective", "not working", "stopped working", "doesn't work",
          # a bare "my new phone is faulty" is the whole of the problem in two words: the matcher
          # wants two key words covered, so the phrase is the key that carries it
          "is faulty", "is broken", "was faulty", "arrived faulty", "came faulty",
          "doesnt work", "went wrong", "fault", "broke",
          # a machine dies as often as it breaks: "my laptop is two years old and the screen died"
          "died", "dead", "packed in", "gave up", "conked out",
          # a new sofa that turns up damaged is the same complaint as a phone that will not
          # turn on: what was bought is not what arrived
          # a stain is the shop's when it came with the thing. The word stays in this list -
          # "my new sofa is stained" and "i want to return a sofa that is stained" carry no
          # arrival word at all, and a list of phrases cannot reach them - and the guard below
          # asks whether the line is a buying one.
          "damaged", "damage", "scratched", "dented", "chipped", "stained",
          # a thing comes apart as often as it breaks
          "fell apart", "falling apart", "came apart", "coming apart", "fell to bits",
          # Soft goods do not break, they split, tear and come apart at the seam: "my new shoes
          # have split" and "my sons school shoes have split" carried one key of the two this
          # entry needs and were answered "I'm listening - say more if it helps". The bare
          # "split" and "torn" are the widest words in this list, so the guards below carry the
          # other senses (a bill split, a torn muscle, a ripped-off customer).
          "split", "splitting", "has split", "have split", "torn", "tore", "tearing",
          "ripped", "ripping", "seam", "seams", "came undone", "come undone", "coming undone",
          "soles", "sole came off", "soles have come", "heel came off", "worn through",
          "worn a hole", "hole in it", "hole in them", "holes in it", "holes in them",
          "keeps breaking", "keeps going wrong",
          # the shop's cut-off line: "ive had it too long" is about the fault, so the ladder
          # and the six-month reversal are the answer, not the age
          "had it too long", "had it for too long", "had it too long ago", "too long ago",
          "too late to complain", "too late now", "says its too old", "says its too late")

# The thing that breaks. A bare "my new phone is faulty" carries one key word and asks the
# refund question with nothing else in the line, so the thing itself is the second signal:
# the entry then answers "my washing machine is broken" as well as "broke after 6 months".
THINGS = ("sofa", "settee", "mattress", "furniture", "armchair", "wardrobe", "sideboard",
          "cooker", "oven", "fridge", "freezer", "dishwasher", "tumble dryer", "kettle",
          "phone", "mobile", "laptop", "computer", "pc", "tablet", "ipad", "iphone", "tv",
          "television", "headphones", "earbuds", "kettle", "toaster", "microwave",
          "washing machine", "washer", "tumble dryer", "dishwasher", "fridge", "freezer",
          "vacuum", "hoover", "printer", "camera", "watch", "console", "playstation", "xbox",
          "speaker", "monitor", "sofa", "settee", "mattress", "chair", "boots", "trainers",
          "shoes", "coat", "jacket", "dress",
          # the soft goods a person buys and returns: a seam gives way at six weeks as easily as a
          # kettle dies, and none of these was a key this entry could see
          "shoe", "boot", "trainer", "sandals", "slippers", "jumper", "cardigan", "hoodie",
          "shirt", "blouse", "jeans", "trousers", "skirt", "leggings", "shorts", "pyjamas",
          "dressing gown", "socks", "sock", "tights", "scarf", "gloves", "glove", "raincoat")

# A machine that has stopped is not yet a dispute: "my kettle is broken" wants the fuse, the
# socket and the door switch, which home's machine card gives along with the six-year claim
# against the shop. This entry answers the same line with the ladder alone, so it stands down
# while the line names one of these and says nothing about buying it. A phone, a laptop and a
# television are not here: the machine card is written about appliances.
MACHINES = ("oven", "cooker", "hob", "fridge", "freezer", "fridge freezer",
            "washing machine", "washer", "tumble dryer", "dryer", "dishwasher",
            "kettle", "toaster", "microwave", "vacuum", "hoover", "coffee machine",
            "sewing machine", "lawnmower", "mower", "machine", "appliance")

# Words that put the purchase, or the age of the thing, in the line: those are the lines the
# rights answer is about, and the ones it keeps.
_PURCHASE_IN_THE_LINE = frozenset("""
    bought buy buys buying sale sold seller retailer retailer's shop shops store stores
    receipt receipts refund refunds refunded return returns returned returning replace
    replaced replacement replacements repair repaired repairing repairs reject guarantee
    guarantees guaranteed warranty warranties ordered order orders online amazon argos
    currys ebay delivered delivery delivered new secondhand second-hand used
    month months week weeks year years day days
    money rights entitled consumer legally claim claims compensate compensation
    pay paid pays owed owe trading standards ombudsman court sue
    """.split())


def _not_a_buy_or_repair_choice(understood):
    """False when the line is deciding what to spend on a machine they already own.

    "should i get a new boiler or repair this one" and "should i replace my old boiler or repair
    it" were both answered with the 30-day refund ladder, because `repair` and `or` are in the key
    and no shop, receipt or claim is anywhere in the line: the question is the money rule for a
    machine that has worn out (`home.py`'s `repair-or-replace`), not a remedy against a seller.
    A line that does name the shop side keeps this row, so "my boiler broke after a month, can i
    get a refund or a repair" is still the ladder's.
    """
    reading = understood if isinstance(understood, dict) else {}
    text = " ".join(str(one) for one in (reading.get("words") or ())).lower()
    if not text:
        text = str(reading.get("clean") or reading.get("text") or "").lower()
    if not _A_MACHINE.search(text) or not _BUY_OR_MEND.search(text):
        return True
    return bool(_A_CLAIM_AGAINST_A_SELLER.search(text))


# The machines people decide to repair or replace: the same list home's rule answers for, and
# a machine is what makes this a spend decision rather than a claim about goods.
_A_MACHINE = re.compile(
    r"\b(?:washing machine|washer|tumble dryer|dryer|dishwasher|fridge|freezer|oven|cooker|"
    r"hob|microwave|vacuum|hoover|boiler|kettle|toaster|mower|lawnmower|strimmer|machine|"
    r"appliance|white goods|laptop|computer|phone|tv|television|washer dryer)\b")
# One side of the decision and the other in one line, in either order, with no shop in it.
_BUY_OR_MEND = re.compile(
    r"(?:\bnew\b|\breplac|\bbuy|\bbuying|\bscrap|\bupgrade)"
    r"[^.?!]{0,40}?(?:\brepair|\bfix|\bmend)"
    r"|(?:\brepair|\bfix|\bmend)[^.?!]{0,40}?(?:\bnew\b|\breplac|\bbuy|\bscrap|\bkeep)")
# Anything that puts a shop, a receipt or a claim in the line: those lines keep the ladder.
# The name is its own: `_A_SHOP_CLAIM` further down is the brake-cable guard's list, and it counts
# "new" as a shop word, which would have kept the ladder on "should i get a new washing machine or
# repair the old one" - the very line this fence is for.
_A_CLAIM_AGAINST_A_SELLER = re.compile(
    r"\b(?:refund|refunded|refunds|money back|shop|store|retailer|seller|sold|receipt|warranty|"
    r"guarantee|rights|entitled|consumer|insist|claim|compensation|reject|faulty|delivered|"
    r"order|ordered|bought|bought it|they|the company)\b")


def _a_machine_that_stopped(reading):
    """False for a machine the line says has stopped, with nothing about buying it in the line."""
    words = [str(one).lower() for one in (reading.get("words") or ())]
    line = " ".join(words) or str(reading.get("clean") or "").lower()
    if not any(word in line for word in MACHINES):
        return True
    return any(word in _PURCHASE_IN_THE_LINE for word in words)
# A washing machine in a rented flat is the landlord's repair, and the line that says so need
# not say "tenant" or "landlord": "the washing machine in my flat has been broken for 2 weeks"
# is a tenancy repair, while "my new tv in my flat broke after a month" is the refund ladder. The
# home phrase cannot be an avoid word, because the tv's line carries it too, so the reading
# decides: the flat's own appliance is the landlord's job and this row stands down for it.
_RENTED_HOME = re.compile(
    r"\b(?:in (?:my|the|our) flat|in my (?:rented|house share)|rented (?:flat|house|home)|"
    r"my (?:landlord|landlady|letting agent)|we rent|i rent|i'?m renting|im a tenant|"
    r"i'?m a tenant|housing association|the flat is rented)\b")
# The appliances that come with a home. A tv, a laptop, a phone or a sofa does not: those are
# bought, and the shop owes the repair or the refund however the home is described.
_FITTED_TO_THE_FLAT = re.compile(
    r"\b(?:washing machines?|washer|tumble dr(?:yer|iers)|dryer|dishwashers?|ovens?|cookers?|"
    r"hobs?|boilers?|radiators?|heating|hot water|fridges?|freezers?|showers?|toilets?|"
    r"extractor fan|immersion heater)\b")


# A line that names the shop, the receipt or a refund is asking about a thing they bought,
# whatever home it stands in: "my washing machine in my flat broke after a month, can i get a
# refund" is the ladder's line, and the washing machine being in a flat does not change who sold
# it. `_A_BUYING_LINE` above is that list already, and it is what tells a stain from a claim too,
# so the flat's appliance guard reuses it rather than keeping a second copy of the same words.


def _not_the_flats_own_appliance(understood):
    """False when the thing that broke came with a home the person rents."""
    text = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if not text:
        text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if not _RENTED_HOME.search(text):
        return True
    if _A_BUYING_LINE.search(text):
        return True
    return not _FITTED_TO_THE_FLAT.search(text)

# Pain is not a complaint by itself: only pain put on somebody's work is. The dental rows answer
# the mouth's own trouble ("my teeth hurt", "my gums are sore", "my filling hurts"), and this row
# answers what went wrong with the treatment. The key cannot tell them apart - it holds the bare
# pain words - so the line is read as a whole here.
_GRIEVANCE = ("complain", "complaint", "botched", "went wrong", "made it worse", "refund",
              "money back", "overcharg", "charged", "charge", "bill", "invoic", "rude",
              "failed", "not happy", "unhappy", "didnt agree", "did not agree", "quoted",
              "quote was", "hurt me", "hurts me", "hurting me", "hurt my", "hurts my",
              "in pain after", "left me in pain", "hurt after", "hurts after", "painful when",
              "after the dentist", "after my dentist", "after the filling", "after the crown",
              "since the dentist", "after he", "after she", "wrong tooth", "pulled the wrong",
              "extra tooth", "more than i", "not what i", "wrong crown", "wrong filling",
              "wrong shade", "wrong colour", "wrong color", "put in the wrong",
              "damaged my", "chipped my tooth", "scratched my", "took out the wrong",
              "fell out after", "came out after", "came off after", "broke after",
              "failed after", "went wrong after", "come loose after")


def _dentist_grievance(understood):
    """True when the line is about the treatment, false when it is about the tooth."""
    said = str((understood or {}).get("text") or "").lower()
    return any(word in said for word in _GRIEVANCE)


# "what is a holding deposit" wants the thing defined and "can the agent keep my holding deposit"
# wants the three reasons it can be kept: one row, read both ways rather than one text that
# answers neither question first.
_HOLDING_KEPT = ("A holding deposit is capped at one week's rent and the agent has to give it back "
                 "within seven days if the tenancy does not go ahead, unless you gave false "
                 "information, you failed the right-to-rent check, or you backed out. Ask in "
                 "writing for the reason and the date it will be repaid, copy in the agent's "
                 "complaints procedure, and if it stays with them it is the council's trading "
                 "standards team that enforces the rule.")
_HOLDING_WHAT = ("A holding deposit is the small sum that takes a place off the market while the "
                 "checks are done: in England it is capped at one week's rent, it has to be "
                 "repaid within seven days once you have signed, and the only reasons it can be "
                 "kept are false information in your application, a failed right-to-rent check, "
                 "or you backing out.")


def _holding_deposit(memory, understood):
    said = " " + " ".join(str((understood or {}).get(key) or "").lower()
                          for key in ("clean", "text", "norm_text")) + " "
    if any(word in said for word in (" keep ", " keeps ", " kept ", " keeping ",
                                     " withholding ", " refuse ", " not back ",
                                     " not return ", " won't return ")):
        return _HOLDING_KEPT
    return _HOLDING_WHAT


# The card below answers four conditions in one breath, and it opened on the same first sentence
# for all of them: "can i return something i opened" and "can i return a dress without tags" were
# both told about wearing something once (thanks @frank-cart). STYLE.md asks for the asked thing
# first, so the condition the line names is read out of it and that sentence leads; the rest of
# the card follows unchanged.
_MIND_A_TRIED_ON_ITEM = ("For a change of mind online you have 14 days from delivery to send it "
                         "back as long as you have only tried it on; in a shop it is their policy, "
                         "and the tags help.")

_CONDITION_LEAD = {
    "tags": ("Tags missing doesn't cancel your rights if the item turns out to be faulty, and a "
             "shop that asks for the tags on a change of mind is asking for goodwill rather than "
             "relying on the law. " + _MIND_A_TRIED_ON_ITEM),
    "opened": ("Opening it doesn't cancel your rights: unboxing something to look at it is not "
               "using it, and a faulty item can go back opened. " + _MIND_A_TRIED_ON_ITEM),
    "slept": ("A mattress or anything else you have slept in is usually exchange-only once used, "
              "unless the fault is theirs - a fault always takes it back, used or not."),
    "worn": ("Wearing something once doesn't cancel your rights if it turns out to be faulty, and "
             "that includes shoes worn outside for an evening. " + _MIND_A_TRIED_ON_ITEM),
}


def _which_condition(said):
    """Which condition of a thing the line names: tags, opened, slept, or worn."""
    words = said.split()
    said = " %s " % " ".join(words)

    def has(*items):
        return any(" %s " % item in said for item in items)

    if has("tag", "tags", "label", "labels", "tagged") and has(
            "without", "no", "missing", "lost", "off", "ripped", "removed", "cut"):
        return "tags"
    if has("tag", "tags") and not has("worn", "wore", "slept"):
        return "tags"
    if has("opened", "opening", "unopened", "box", "packaging", "packet", "seal", "sealed",
           "unwrapped", "wrapper", "shrink wrap", "shrinkwrap"):
        return "opened"
    if has("slept", "slept", "mattress", "bed", "duvet"):
        return "slept"
    return "worn"


def _condition_reply(memory, understanding):
    """The returns card for a thing that has been worn, opened, slept on or has no tags."""
    said = str((understanding or {}).get("clean") or (understanding or {}).get("text") or "").lower()
    return _CONDITION_LEAD[_which_condition(said)]


# A bicycle brake cable is a part, and asking how hard it is to fit is a repair question, not
# a claim against a shop. The line that asks says only "how hard is it to replace", and the
# subject comes from the turn before, so the words are read from both. The ladder keeps the
# line when it also says what it wants from the shop - a refund, a return, a fault claim - which
# is the difference between "how hard is it to replace" and "can i get a refund".
_A_BICYCLE_CABLE = re.compile(r"\bbrake cables?\b", re.I)
_A_REPAIR_ASK = re.compile(
    r"\b(?:how hard|how easy|how do i|how to|how can i|where do i|what do i need|"
    r"fix|fixing|repair|repairing|replace|replacing|mend|change|fit|fitting|"
    r"do it myself|diy)\b", re.I)
_A_SHOP_CLAIM = re.compile(
    r"\b(?:refund|refunds|return|returns|returned|reject|rejecting|faulty|fault|"
    r"shop|retailer|seller|receipt|warranty|guarantee|money back|new|brand new|"
    r"bought|buying|arrived|delivered|replacement)\b", re.I)


# A row whose question is asked both ways round cannot owe one standing sentence. The
# change-of-mind row answers "can i return shoes i bought online" with a yes and "is it too late
# to send these back" with a no and its condition; a plain "Yes" on the second reads as "yes, too
# late" against a card that says there are 14 days. So the row declares a function of the line,
# the way cold-vs-flu's verdict is, and not a fixed string.
_TOO_LATE = re.compile(
    r"\btoo late\b|\bhave i left\b|\bleft it\b|\bout of time\b|\bmissed (?:it|the|my)\b")
_STILL_TIME = re.compile(
    r"\bstill time\b|\bcan i still\b|\bcan we still\b|\bam i still\b|\bstill able\b")


def _change_of_mind_verdict(understood):
    """The sentence the change-of-mind row owes, read off which way round the line asks."""
    text = str((understood or {}).get("text") or "").lower()
    if _TOO_LATE.search(text):
        return "No, not if it is within 14 days"
    if _STILL_TIME.search(text):
        return "Yes, if it is within 14 days"
    return "Yes"


def _a_brake_cable_repair_ask(understood):
    """Whether a bicycle brake cable line is a repair question rather than a shop claim.

    "my bike brake cable snapped" is answered by the bike cable card, but the follow-up "how
    hard is it to replace" carries only the subject from the turn before, and "replace" is one
    of the words the faulty-goods ladder is keyed on: the person was told to take the cable
    back to the shop with the receipt. A line with a brake cable in it that asks how to fit one
    belongs to the repair card; one that asks for a refund, a return or a replacement keeps the
    ladder. A line with no bicycle cable in it is not this guard's business.
    """
    if not isinstance(understood, dict):
        return True
    above = str(((understood.get("leans_on") or {}).get("text")) or "")
    said = str(understood.get("clean") or understood.get("text") or "")
    text = (above + " " + said).lower()
    if not _A_BICYCLE_CABLE.search(text):
        return True
    if not any(word in text for word in ("bike", "bicycle", "cycle", "pushbike")):
        return True
    return bool(_A_SHOP_CLAIM.search(text)) or not _A_REPAIR_ASK.search(text)


# A stretch of waiting is the second signal a tracking line needs, and people say it as a number:
# "tracking says in transit for 5 days" was the same two words twice ("in transit"), which is one
# signal and scored nothing, while "since tuesday" is a word and scored. Read as a shape, every
# way of giving the wait counts - "for 5 days", "for two weeks", "for a fortnight".
_A_WAIT = re.compile(r"\b(?:for\s+)?(?:\d+|a|an|one|two|three|four|five|six|seven|eight|"
                     r"nine|ten|a few|several)\s+(?:days?|weeks?|months?)\b"
                     r"|\b(?:a|one|two|three)\s+fortnight\b", re.I)


def _a_stretch_of_waiting(said):
    """True when the line says how long the parcel has been sitting where it is."""
    return bool(_A_WAIT.search(str(said or "")))


ENTRIES = [
    # --- faulty goods and refunds ---------------------------------------------
    entry("faulty-goods", (BROKEN,
                           ("refund", "return", "replace", "repair", "reject", "money back",
                            "shop", "store", "retailer", "bought",
                            # "my washing machine broke after 6 months" asks the same question
                            # without naming a shop: the age of the thing is the other way in.
                            "months", "weeks", "years") + THINGS),
          faulty_goods_reply,
          # "refused"/"policy" were here to keep a "no refunds" sign out of this entry, but a
          # slip guard in the matcher reads "refuse" as a misspelling of "refused" and then
          # drops the entry for the whole line: the sign entry answers those lines instead.
          avoid=("leg", "arm", "ankle", "wrist", "bone", "rib", "ribs", "toe", "tooth", "teeth",
                 "collarbone", "broken heart", "is it worth",
                 # a scratch is a blemish and the right to reject is for a fault: "my watch glass
                 # is scratched" was told to take it back to the shop 30 days after buying. A
                 # blemish that arrived with the goods is the arrival card's line ("came
                 # scratched", "arrived scratched"), so the word alone stands this row down.
                 "scratch", "scratches", "scratched", "scuff", "scuffs", "scuffed",
                 "hairline", "how do i polish", "polish out", "polished out", "buff out",
                 # "broke" is in BROKEN because a thing that broke is the shop's problem, and
                 # "months" is in the key because the age of the thing is the other way in, so
                 # "we are broke this month" and "i am broke this month" were both told to take
                 # something back to the shop. The money sense of the word is the person's own
                 # pocket, and the phrasing that says so is these: a thing that broke names
                 # itself or when it happened ("broke this morning", "broke after two months"),
                 # never "broke this month" or "broke till payday".
                 # the ending sense of "broke" is two people's, not a thing's: "i broke up with
                 # my girlfriend of 6 years" was told to take it back to the shop and claim
                 # against the retailer for six years, because "broke" is in BROKEN and "years"
                 # is in the ask. Nothing that broke up is a thing that broke.
                 "broke up", "break up", "breaking up", "split up", "dumped me", "got dumped",
                 "are broke", "am broke", "im broke", "be broke", "broke till",
                 "broke until", "broke every", "skint", "money is tight", "short of money",
                 "short this month", "cant afford", "cannot afford", "can not afford",
                 "afford to", "no money",
                 # a stain is a cleaning job, not a fault: "how do i get a stain out of my
                 # trainers" was told to reject the goods under the Consumer Rights Act, because
                 # "stained" is in BROKEN and "trainers" is one of THINGS. The words that ask
                 # how to get it out are what tell the two apart, and "arrived stained" or "came
                 # stained" keeps the complaint it belongs to.
                 # a habit that broke is not a thing that broke: "i keep breaking my streak
                 # after a week" was told to take it back to the shop, because "broke" is in
                 # BROKEN and "weeks" is in this row's key. The subject here is the person's own
                 # effort, and the habit row answers it. Phrases and nouns that name a habit,
                 # never a bare "break", which is the goods' word.
                 "streak", "streaks", "my habit", "the habit", "my diet", "my routine",
                 "my new years resolution", "new year resolution", "my resolution to",
                 "dry january", "my sobriety", "my gym",
                 "how do i get a stain", "how do i get the stain", "how do i get this stain",
                 "how do i get that stain", "how do i get the mark", "how do i get ink",
                 "get the stain out", "get a stain out", "get this stain out", "get it out of",
                 "stain out of", "stain off", "stain from my", "mark out of", "mark off",
                 "how do i remove a stain", "how do i remove the stain", "how to remove a stain",
                 "remove a stain", "remove the stain", "remove this stain", "lift the stain",
                 "how do i clean a stain", "how do i clean the stain", "clean a stain",
                 "clean the stain", "cleaning a stain", "how do i clean", "how do i wash",
                 "how to clean", "how to get the stain", "spot clean", "dry clean",
                 "stained how do i clean", "is stained how do i", "stained what do i do",
                 # a zip that will not close is a repair, which clothing.stuck-zip answers in
                 # full: "the zip on my jacket is broken" was getting the faulty-goods ladder,
                 # which tells someone to take a jacket back rather than how to close it
                 "zip", "zips", "zipper", "zippers",
                 # money back on a booking is not money back on a thing you bought: "how do i
                 # get a refund on a booking" was this ladder, which is about a broken kettle
                 "booking", "bookings", "reservation", "reservations", "double booked",
                 # an animal clawing the furniture is the animal's question: "my kitten is
                 # scratching the furniture" reached this ladder on "furniture" and was told
                 # about rejecting faulty goods
                 "cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "puppies",
                 "rabbit", "hamster", "parrot", "budgie", "pet", "pets",
                 "scratching the", "scratches the", "scratch the", "keeps scratching",
                 # "how do i get a refund" is the steps, which the refund entry gives in full;
                 # "can i get a refund for X" is the entitlement question, which is this answer
                 # a how-to on something you already own is a repair, not the refund ladder:
                 # main's wider damage words ("chipped", "stained", "scratched") sent "how do i
                 # repair a chip in a wooden table" and "how do i get salt stains off my leather
                 # boots" to the retailer's problem. The ladder is for a thing that went wrong,
                 # not for a job with a second verb in it.
                 # a plate of chips is not a chipped thing: "chips" is the same word family as
                 # "chipped", so the cooking words stand this row aside and the chip card
                 # answers. The claim lines name the thing that is chipped, never the chips.
                 "oven chips", "frozen chips", "chip shop", "make chips", "cook chips",
                 "chips in the oven", "chips in the air fryer", "homemade chips",
                 "air fryer chips", "chips and", "salt and vinegar",
                 "how do i get out", "how to get out", "stains off", "stains out", "stain off",
                 "stain out", "get the stains", "get the stain",
                 "how do i repair", "how do i fix", "how to repair", "how to fix",
                 "how can i repair", "how can i fix", "how do i get the", "how do i get out",
                 "how do i get off", "how do i get rid", "how do i remove", "how to remove",
                 "how do i clean", "how do i polish", "how do i fill", "how do i touch up",
                 "how do i get a refund", "how do i get my refund", "how do i get my money back",
                 "how to get a refund", "how do i claim a refund",
                 # a line about the warranty is the warranty row's ("a manufacturer's guarantee
                 # sits on top of your rights") and this ladder was taking it on the word
                 # "warranty" alone: "my washing machine is still under warranty and broken"
                 "warranty", "guarantee", "out of warranty", "under warranty", "still covered",
                 "extended warranty", "ran out", "expired",
                 # the same is true when the ask is for the words: "what should i write to ask
                 # for a refund" wants the message, which wording.ask-for-refund has
                 "what should i write", "what do i write", "what to write", "what do i say",
                 "what to say", "how do i word", "write to ask", "a message asking",
                 "draft a", "wording",
                 # "my marriage broke down" is not a product, and a boiler or a radiator that
                 # breaks is the home's line: those answers are better than a refund ladder
                 "marriage", "relationship", "broke up", "break up",
                 # a freezer or fridge that broke and took the food with it is the food
                 # claim: "my freezer broke and spoiled all my food" wanted both, and the
                 # refund ladder said nothing about the food
                 "spoiled the food", "ruined the food", "spoiled all my food",
                 "all the food", "the food went off", "food in it went off",
                 # a thing that does not fit is a change of mind, not a fault: "can i return
                 # shoes i bought online if they dont fit" is the 14-day right
                 "doesnt fit", "doesn't fit", "does not fit", "dont fit", "didnt fit",
                 "didn't fit", "wrong size", "too small", "too big", "not my size",
                 # a private seller is buyer beware, not the shop's refund ladder: the
                 # second-hand entry owns "i bought a used car privately and it broke"
                 "privately", "private seller", "private sale", "private car sale",
                 "off a mate", "from a mate", "from a friend",
                 # and a marketplace is a private seller too: "bought from facebook
                 # marketplace and it doesnt work" was told to take it back to the shop
                 "marketplace", "facebook", "fb marketplace", "gumtree", "vinted", "depop",
                 # an animal did the damage, so nothing was faulty: "my kitten keeps scratching
                 # the sofa" reached this row on "scratched" + "sofa" and was answered with the
                 # refund ladder. The same guard #5048 put on damaged-on-delivery.
                 "cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "pup", "pups",
                 "rabbit", "hamster", "parrot", "budgie", "pet", "pets", "claws",
                 "shpock", "preloved", "car boot", "boot sale", "off my mate", "off a friend",
                 # a person or a pet dies, or a body part breaks: those lines belong to the
                 # bereavement and health answers. The relationship words alone are not enough -
                 # "my son bought a game and it doesn't work" is a faulty product.
                 "passed away", "who died", "he died", "she died", "they died",
                 "grandmother died", "grandfather died", "granddad died", "grandad died",
                 "grandma died", "grandpa died", "granny died", "nan died", "nana died",
                 "mother died", "father died", "mum died", "mom died", "dad died",
                 "wife died", "husband died", "partner died", "son died", "daughter died",
                 "brother died", "sister died", "baby died", "friend died", "dog died",
                 "cat died", "pet died", "died last week", "died last month", "died last year",
                 "recently died", "has died", "had died", "died of", "died in",
                 "funeral", "bereave", "pet", "dog", "cat",
                 "hip", "knee", "shoulder",
                 # the other senses of the soft-goods words above. A bill split between friends, a
                 # person torn between two things, a muscle torn at the gym and a customer
                 # ripped off are none of them a faulty product, and "how do i mend" is a mending
                 # job on something old rather than a claim on something new.
                 "split up", "split the", "split a", "split it", "split between", "split my",
                 "split shift", "split shifts", "split the bill", "split the cost", "we split",
                 "sharing", "share the", "divide the", "torn between", "torn about", "torn over", "torn on", "torn muscle",
                 "torn ligament", "torn acl", "torn cartilage", "torn tendon", "torn calf",
                 "torn hamstring", "torn meniscus", "split lip", "split ends", "ripped off",
                 "ripped out", "ripped up", "ripped jeans", "ripped at the", "ripped a",
                 "how do i mend", "how to mend", "how do i sew", "how to sew", "darn it",
                 "darn the", "patch it", "patch the", "stitch it", "stitch the", "iron it",
                 "iron on", "iron-on", "take it in", "take them in", "let it out", "hem it",
                 "how do i fix", "how can i fix", "how do i repair", "how can i repair",
                 "how do i stop it", "keeps splitting", "keeps tearing", "keeps ripping",
                 # a bare "back" is a body part and also half of "money back", which is the
                 # refund line itself: the body is spelled out instead
                 "back pain", "bad back", "sore back", "aching back", "lower back",
                 "back ache", "my back", "neck", "wrist", "spine", "finger",
                 "thumb", "jaw", "nose", "cheek", "eye", "eyes", "hand", "foot", "feet",
                 "heart attack", "stroke", "cancer", "hospital", "operation", "surgery",
                 "fell over", "fell down", "fell off the", "is ill", "is sick",
                 "boiler", "central heating", "radiator", "radiators", "thermostat",
                 # A home you rent is the landlord's card, not the shop's: the fixture came with
                 # the flat, so "the heating has been broken for 3 weeks, what are my rights" and
                 # "the washing machine in my flat has been broken for 2 weeks" were told to take
                 # it back to the shop with the receipt. `home.landlord-repairs` has the letter.
                 "heating", "hot water", "no heating", "no hot water", "tenant", "tenants",
                 "i rent", "renting", "renter", "letting agent", "in my flat",
                 "rented flat", "came with the flat", "the flat came with",
                 "immersion", "fuse box", "wiring", "roof", "gutter", "gutters",
                 "window", "windows", "door", "doors", "lock", "locks", "toilet", "tap", "taps",
                 "sink", "drain", "drains", "landlord", "council",
                 # a fixture and a rented home are the landlord's to repair, and the fault is
                 # told as a length of time: "the heating has been broken for 3 weeks, what
                 # are my rights" took the refund ladder on "broken" + "weeks", as did
                 # "the washing machine in my flat has been broken for 2 weeks" and "i rent
                 # and the oven has been broken for weeks". A thing they bought is still the
                 # shop's ("my cooker broke 3 months ago and the shop wont help").
                 "heating", "hot water", "no hot water", "tenant", "tenants", "i rent",
                 "im renting", "i'm renting", "we rent", "renting", "letting agent",
                 # A home is not a tenancy: "my laptop in my house is broken and i want a
                 # refund" and "my new tv in my flat broke after a month" are things the person
                 # bought, and they keep the shop's answer. Only the words that say they rent
                 # stand the ladder down.
                 "worth repairing", "worth replacing", "worth fixing", "should i replace",
                 "should i repair", "repair it or replace", "fix it or replace",
                 # car glass is the windscreen entry's answer, whether the line asks the price
                 # or the rights: "windscreen chip repair or replace" and "should i get my
                 # windscreen chip repaired" were both given the reject-it-in-30-days ladder
                 # for a chip in a windscreen, which nobody takes back to a shop. The words
                 # name the glass itself: a bare "windscreen" also covers a wiper, a washer
                 # pump and a jet, and "the windscreen washer pump is faulty can i get it
                 # replaced" is a part that was bought and went wrong, which is the ladder
                 "windscreen chip", "chipped windscreen", "chip in the windscreen",
                 "chip in my windscreen", "stone chip", "windscreen crack",
                 "cracked windscreen", "windscreen repair", "repair the windscreen",
                 "replace the windscreen", "windscreen replacement", "windshield",
                 "should i upgrade", "upgrade", "new one",
                 # the customer broke it, in the shop or at home: that is the damage answer
                 "i broke", "my child broke", "my son broke", "my daughter broke", "kid broke",
                 "accidentally broke", "accidentally knocked", "knocked over", "knocked it",
                 "dropped it", "dropped my", "i damaged", "damaged it myself", "spilled",
                 "do i have to pay", "must i pay", "have to pay for",
                 # an appliance that has broken is also a "what can i cook" line: the oven,
                 # fridge or microwave going is how the person explains why dinner is a
                 # problem, and the cooking answer is the one they asked for
                 "what can i make", "what can i cook", "what can we cook", "what can i eat",
                 "what should i cook", "whats for dinner", "what's for dinner", "for dinner",
                 "for tea tonight", "to cook", "to eat tonight", "recipe",
                 # the reading that puts the subject back turns "what can i make" into
                 # "what should i make for microwave broken", so the other wordings count too
                 "what should i make", "what could i make", "what shall i make",
                 "what do i make", "make for dinner", "make tonight")
                 # a mark on something you wear is a laundry or leather job, and the cleaning rows
                 # answer it. This is the statement shape of it - "there is a stain on my shoe",
                 # "my trainers have got a mark on them" - which names no ask to read, and the
                 # complaint shape keeps the ladder ("my new shoes arrived stained").
                 + tuple("stain on my " + thing for thing in
                         ("shoe", "shoes", "trainers", "boots", "boot", "coat", "jacket",
                          "dress", "trousers", "jeans", "shirt", "top", "jumper", "suit"))
                 + tuple(thing + " is stained" for thing in
                         ("shoe", "trainers", "coat", "jacket", "dress", "shirt", "trousers",
                          "jeans", "jumper"))
                 + tuple("mark on my " + thing for thing in
                         ("shoe", "shoes", "trainers", "boots", "coat", "jacket", "dress")),
          # a symptom on its own is a repair question, not a rights question: "my laptop
          # keyboard has stopped working" and "my phone died" want the fix, and technology's
          # entries answer them. The line has to say what it wants - a right, a shop, or how
          # old the thing is - before this entry takes it.
          # "broken", "broke", "went wrong", "packed in" and the rest of the bare fault words
          # used to be here, and they are on the key as well, so any "my X is broken" line
          # was this answer: "my phone broke", "my oven is broken", "my phone is broken can
          # it be fixed" all lost their repair card to it. A fault has to be said with a
          # right, a shop, an age or something new beside it before this entry takes it.
          ask=("faulty", "fault", "defective", "damaged", "damage",
               # how it arrived is damage, not a repair: "my watch is scratched", "the sofa
               # came dented" - nothing here says the thing has stopped working
               "scratched", "dented", "chipped", "stained",
               # and a thing that has come apart is faulty as sold: no repair row answers "my
               # coat fell apart at the seam" or "my boots fell apart", and the choice is
               # between this answer and a punt, so these four stay as well
               "fell apart", "falling apart", "came apart", "coming apart",
               "refund", "return", "replace", "reject", "money back", "send it back",
               # a thing that is new, or has just arrived, is the shop's problem however the
               # fault is worded: "my brand new phone is broken" is not a repair question
               "new", "brand new", "arrived", "delivered", "just bought", "only had it",
               "first day", "first time", "came yesterday", "still boxed",
               "shop", "store", "retailer", "bought", "purchase", "receipt", "warranty",
               "guarantee", "consumer", "my rights", "entitled", "legally", "allowed",
               "must they", "have to", "who pays",
               "month", "months", "week", "weeks", "year", "years", "ago", "days"),
          # a broken thing is this answer even when another domain reads "shop" and "refund"
          # as a missing parcel: the tie goes to the fault. Money's general `refund` entry
          # (the 30-day rule in one line) now sits beside this domain and wins a bare
          # "can i get a refund for X" on its bias, and the retailer is the answer here. Three
          # is the least that wins those lines and it still leaves a used car to buyer-beware.
          bias=3,
          # Four lines this ladder must not take: the kitchen ask that explains itself with the
          # appliance (cooking.without answers those), a machine that has simply stopped, which
          # home's machine card opens with the fuse and the socket and closes with the six-year
          # claim against the shop, a mark on something the person has had a while, which is a
          # cleaning job rather than a complaint, and the flat's own appliance, which is the
          # landlord's repair. "the washing machine in my flat has been broken for 2 weeks" took
          # the ladder on "broken" and "weeks" while the tv in the same flat must keep it.
          guard=_not_a_kitchen_or_a_stopped_machine),    entry("broke-it-in-a-shop", (("broke", "broken", "knocked over", "dropped", "damaged",
                                  "spilled", "spilt", "trod on", "smashed"),
                                 ("in a shop", "in a store", "in the supermarket", "on the shelf",
                                  "on display", "must i pay", "do i have to pay", "have to pay",
                                  "pay for it", "pay for the", "owe")),
          "You owe for damage only if you were careless, and even then only what it actually cost "
          "the shop: an accident on its own is not a debt, so you can politely decline to pay. If "
          "you do offer, offer the cost price rather than the shelf price, ask for it in writing, "
          "and never pay cash on the spot to a member of staff. Retailers can claim on their own "
          "insurance, and a shop that threatens the police over a dropped jar is bluffing.",
          # "in a shop" is the sentence that makes it damage, so no ask list is needed; the
          # avoid list keeps a faulty product bought somewhere out of it.
          avoid=("faulty", "refund", "return", "warranty", "guarantee", "bought it", "my tv",
                 "washing machine", "laptop", "phone broke"),
          # "i broke a glass in a shop do i have to pay" is the line this row was written for and
          # it lost twice: to the price of spectacles, because "glass" is "glasses" to that row,
          # and to money's four rungs, because the ask is "do i have to pay". Two key words on a
          # line that names an accident in a shop is as clear as this gets, so the tie goes here.
          bias=2),
    # A shop that blames the buyer: "the shop says i damaged it but i didnt" is not a parcel that
    # never arrived, "the shop says i broke it" was answered with a week of cheap dinners, and
    # "they say its wear and tear" got the shrug. The thing people are stuck on is the argument
    # about who caused the fault, and the law settles it: for six months the shop has to prove the
    # fault was not there when it sold it. The blame can arrive in any word - damaged, broke, wear
    # and tear, my fault, not covered, was fine when it left - so the second group is the claim
    # itself, not one wording of it.
    entry("shop-blames-me",
          (("shop", "shops", "store", "retailer", "seller", "company", "they", "them",
            "bought it", "bought this", "where i bought", "the place i bought",
            # the claim can come first and name no shop at all - "theyre saying its my fault" and
            # "currys say i damaged the screen" - so the claim is a first-half word too, and the
            # fault word is then the second half of the line
            "says i", "said i", "say i", "says id", "said id", "says its", "said its",
            "says that i", "said that i", "claims i", "claimed i", "claims that i",
            "reckons i", "reckon i", "reckoned i", "insists i", "insist i", "insisted i",
            "insisting i", "accused me", "accuses me", "accusing me", "blames me",
            "blaming me", "blamed me", "wear and tear", "worn out", "my fault",
            "my own fault", "not my fault", "misused", "abused it", "not covered",
            "user damage", "physical damage", "caused by you", "was fine when",
            "wasnt like that", "wasnt me", "not our fault", "dont believe", "dont accept"),
           ("damaged", "damage", "damaged it", "damaged the", "broke", "broken", "broke it",
            "broke the", "ruined", "ruined it", "screen", "phone", "laptop", "tv", "coat",
            "shoes", "jumper", "dress", "wash", "washed", "machine", "item", "goods", "product",
            "fault", "faulty", "warranty", "shop", "store", "retailer", "says i", "said i",
            "wear and tear", "my fault", "it went", "went wrong")),
          ("In the first six months the shop has to prove the fault was not there when it sold "
           "it, so \"you damaged it\" is a claim it has to back up, not one you have to answer: "
           "put it in writing, say you are rejecting it as not of satisfactory quality, and ask "
           "for a full refund. Inside 30 days you can insist on the refund; after that they get "
           "one repair or replacement, and if that fails or drags on you can ask for the money "
           "back or a price reduction. Wear and tear is only a defence for something plainly "
           "used hard - a zip that went on a month-old coat is not that. Keep the receipt, the "
           "photos and the emails, and the small claims track is free online for anything under "
           "\u00a310,000."),
          # the accident in the shop is the other question: there the person agrees they did it
          # and asks whether the shop can make them pay for it
          avoid=("in a shop", "in a store", "in the supermarket", "on the shelf", "on display",
                 "do i have to pay", "must i pay", "have to pay", "pay for it", "owe",
                 # "what is wear and tear" asks what the phrase means, not for a way through
                 # a shop's refusal: the definition is not this row's question
                 "what is wear and tear", "what does wear and tear mean",
                 "what counts as wear and tear", "what is classed as wear and tear",
                 "whats wear and tear",
                 # a tenancy deposit, a policy and a car dealer have their own answers
                 "landlord", "landlords", "letting agent", "deposit", "tenancy", "flat", "rent",
                 "insurance", "policy", "warranty", "car", "dealer", "garage", "van", "mot"),
          guard=_the_shop_or_the_thing_is_named,
          bias=2),
    # How long you have is the question people ask once the thing is a few years old, and it is
    # the one the 30-day ladder never answers: the clock, the reversal of proof and the six-year
    # limit are the answer. It also stops "the fridge is five years old can i still claim" from
    # reaching the home-working flat rate, where "years" and "claim" met.
    entry("goods-aged", (("years old", "year old", "months old", "years back", "how long do i have",
                          "how long have i got", "how long ago", "time limit", "still claim",
                          "six years", "six-year", "five years", "four years", "three years",
                          "two years", "who has to prove", "prove the fault",
                          "burden of proof"),
                         ("refund", "claim", "rights", "repair", "replace", "reject", "faulty",
                          "broke", "broken", "shop", "retailer", "warranty", "guarantee",
                          "sale of goods")),
          "The clock runs from the day you bought it, and a warranty has nothing to do with it: you "
          "can claim against the shop for up to six years in England, Wales and Northern Ireland "
          "and five in Scotland. Within 30 days you can reject it for a full refund, after that "
          "they get one repair or replacement, and for the first six months the shop has to prove "
          "the fault was not there when it sold it. Keep the receipt and put the claim in writing "
          "with photos.",

          # cooking times, a parcel in transit, a claim on a policy and a car dealer's used car
          # are other answers, and "how long do leftovers last" is not a shop's problem
          avoid=("how long do i cook", "how long to cook", "how long do i bake", "how long in the",
                 "how long do i boil", "how long to boil", "how long does it take", "how long will",
                 "how long until", "how long before", "how long should i wait", "leftovers",
                 "how long does it last", "how long can i keep", "use by", "refrigerate",
                 "car", "mot", "dealer", "garage", "van", "tyre", "house", "rent", "boiler",
                 "pension", "mortgage", "tax", "benefits", "insurance", "warranty cover",
                 # A payment protection policy is not a shop's clock: "can i still claim ppi"
                 # was answered with the six years you have to take a faulty thing back.
                 "ppi", "payment protection",
                 # the ending sense of "broke", as above: a relationship of six years is not a
                 # six-year warranty, and "broke" plus "years" is what joined the two
                 "broke up", "break up", "breaking up", "split up", "dumped me", "got dumped",
                 # The age is half of a repair-or-replace decision, so "my dishwasher is 9 years
                 # old new one or repair it" is the repair table's question and not the clock's:
                 # the same weighing-up words that keep the ladder off it keep this row off it.
                 "or repair it", "or repair this", "or fix it", "or fix this", "or mend it",
                 "new one or", "or a new one",
                 # and with the repair first: "my dishwasher is 9 years old should i repair it or
                 # get a new one" is the same decision, and the age is the half of it that says
                 # replace, so the clock has nothing to add.
                 "repair it or", "fix it or", "repair this or", "fix this or"),
          # the same decision said any other way is read as a shape, not as another phrase in
          # this list: the age is only half of the question, and the lifespan table answers it
          guard=_not_an_old_machines_repair_decision,
          bias=3),
    entry("no-refunds-sign", (("no refunds", "no returns", "refund policy", "returns policy",
                               "exchange only", "can't return", "cant return",
                               # "can a shop refuse a refund" is this entry's question, and a
                               # refusal is the same problem whatever word the shop used
                               "refuse a refund", "refused a refund", "refuse to refund",
                               "refused to refund", "allowed to refuse", "right to refuse",
                               "credit note", "voucher instead", "exchange instead",
                               # how you paid is not a reason to refuse
                               "because i paid", "paid by card", "paid on my card",
                               "paid with my card", "paid by debit"),
                              ("shop", "store", "sign", "says", "policy", "refused", "allowed",
                               "legal", "faulty", "offered", "offering", "insisted", "insists",
                               "exchange", "voucher", "card",
                               # "they want to give me a credit note" names no shop and no
                               # policy: the offer itself is the second half
                               "want to give", "want to offer", "giving me", "gave me a credit",
                               "offered me", "trying to give", "only offered")),
          "A shop cannot refuse a refund for faulty goods, whatever the sign says: under the "
          "Consumer Rights Act you can reject it for a full refund within 30 days, then claim a "
          "repair or replacement. A credit note is an offer, not a right, and how you paid is no "
          "excuse either. If they still will not, ask your card provider for a chargeback and quote "
          "their refusal.",

          # a refund that is late is the timing answer, not this one
          avoid=("still no refund", "still waiting", "still hasn't", "still hasnt", "waiting",
                 "how long", "weeks ago", "days ago", "chase", "when will", "when should",
                 # a shop that has folded is not a shop refusing: there is nobody at the till,
                 # and the card company is the way to the money
                 "gone bust", "went bust", "gone under", "closed down", "ceased trading",
                 "in administration", "administrators", "liquidated", "liquidators",
                 "no longer trading", "shut down"),
          # money's refund-refused entry answers the same "am I allowed to be refused" from the
          # generic side, and the sign in the shop is what this one quotes
          bias=3),
    entry("wont-take-back", (("take back", "won't take", "wont take", "refused to take",
                              "wouldn't take", "wont refund", "won't refund"),
                             ("shop", "store", "back", "jumper", "shirt", "shoes", "item",
                              "return", "refund")),
          "If it's faulty they have to take it back, whatever their returns policy says: ask for a "
          "refund, or a repair or replacement if they refuse. For a change of mind, their own "
          "returns terms decide, so check what you agreed to when you bought it.",
          # "ticketmaster wont refund a rescheduled gig" is the ticket rules, not the returns
          # terms, and a travel agent who keeps the money for a holiday is the package rules
          avoid=("gig", "concert", "ticket", "tickets", "festival", "show", "event", "match",
                 "theatre", "holiday", "travel agent", "package holiday", "flight", "airline",
                 "hotel", "train", "bus", "coach", "ferry", "insurance", "policy", "energy",
                 "broadband", "phone",
                 # a meal out is not an item on a returns policy: the restaurant answer has the
                 # manager, the bill and the card dispute
                 "restaurant", "cafe", "café", "takeaway", "waiter", "waitress", "dish",
                 "meal", "pub meal", "menu", "chef", "kitchen")),
    entry("refund-or-repair", (("refund", "money back", "repair", "replacement"),
                               ("or", "have to", "entitled", "choice", "which", "choose",
                                "either", "insist", "insists", "demand", "demanding",
                                "force me", "make me", "must i", "refuse", "can they",
                                "not a repair", "instead of a repair",
                                "instead of a replacement", "reject it",
                                # the offer a shop makes instead of the refund is the same
                                # question: "they want to repair it instead of refund me"
                                "instead of refund", "instead of a refund", "instead of refunding",
                                "rather than refund", "rather than a refund", "only a repair",
                                "only offer a repair", "only offering a repair")),
          "In the first 30 days you choose: a full refund, a repair or a replacement, and the shop "
          "can't force a repair on you. After 30 days the shop gets one attempt at a repair or "
          "replacement, and if that fails you can claim a refund.",
          ask=("insist", "demand", "force", "make me", "must i", "refuse", "can they", "or",
               "have to", "entitled", "choice", "choose", "which", "either", "not a repair",
               "instead of a repair", "instead of a replacement",
               "instead of refund", "instead of a refund", "instead of refunding",
               "rather than refund", "rather than a refund", "only a repair",
               "only offer a repair"),
          avoid=("how long", "when", "days", "week", "late", "waiting", "worth", "upgrade",
                 "new one", "new battery",
                 # a refund sent back to a card that is closed is that entry's question
                 "old card", "card is closed", "card was closed", "card closed",
                 "expired card", "different card", "new card", "lost my card",
                 # a credit note offered instead of the money is the refusal answer's line:
                 # "a credit note is an offer, not a right" is what that entry says
                 "credit note", "voucher", "exchange instead", "offered me a credit",
                 # "is it cheaper to repair my phone or replace it" is a cost question: the
                 # repair-or-replace table answers it, this entry answers what you are owed.
                 "cheaper", "cost of", "repair shop", "myself",
                 # cancelling your own holiday is the cancellation answer, not this one:
                 # "i have to cancel my holiday can i get my money back"
                 "cancel my holiday", "cancel my trip", "cancel my booking",
                 "have to cancel", "need to cancel", "want to cancel", "how do i cancel",
                 # "new phone or repair mine", "should i buy a new phone or repair mine": the
                 # buy-versus-repair answer is the repair table's, not the refund ladder's.
                 "buy a new", "buy new", "buying a new", "or buy", "repair mine", "or replace",
                 "replace it",
                 # The same weighing-up stated the other way round: "should i get a new boiler or
                 # repair this one". The words that make it a decision are the repair word after
                 # the "or" - "or repair this", "or fix it" - and none of the shop's own words
                 # (refund, insist, force) are in such a line, so it is the repair table's.
                 "or repair it", "or repair this", "or repair that", "or fix it", "or fix this",
                 "or mend it", "or mend this",
                 # "new car or keep repairing it" is a spend-more-or-spend-less question about
                 # something you already own: nothing here is being rejected for a refund
                 "new car", "keep repairing", "keep fixing", "or keep", "or scrap", "scrap it",
                 # the same weighing-up about a car: "should i repair or sell my car" and "fix
                 # it or sell it" are the repair table's, not the shop's ladder
                 "repair or sell", "or sell it", "sell it or", "fix or sell", "or fix the car",
                 # The decision has two word orders and the list could only see the phrase it was
                 # given: "my phone screen is smashed, replace or repair" and "does my phone need
                 # a new screen or a repair" were told what the shop owes, which is not what
                 # someone with a smashed screen of their own is asking. "or replace" was here
                 # alone, and "replace" comes first about as often as it comes second. "repair or
                 # replacement", the rights phrasing, keeps this entry: the matcher ends a phrase
                 # at a word boundary, so "replacement" is not "replace".
                 "repair or replace", "replace or repair", "fix or replace", "replace or fix",
                 "mend or replace", "replace or mend", "or a repair", "new screen or",
                 "screen or a repair", "repair or a new", "new one or a repair"),
          # The buy-versus-repair decision about a machine they own is home's money rule, not the
          guard=_not_a_buy_or_repair_choice,
          # "can i insist on a refund" is the remedy question, and money's general refund
          # answer (a bare 30-day rule) now ranks above it: which remedy you get is the ask.
          bias=3),
    entry("not-as-described", (("as new", "advertised as", "described as", "sold as", "listed as",
                               "said it was", "told me it was", "claimed it was", "as described",
                               "not what it said", "not what the listing", "fake", "counterfeit",
                               "copy", "knock off", "not genuine", "not real leather",
                               "grey import",
                               # the everyday shape of the same complaint: "i was told the sofa was
                               # leather and its not", "the label said 100 percent cotton but its
                               # not", "the ad said it was wool and its polyester". None of these
                               # named a listing, so all three were echoes.
                               "was told", "told me the", "told me my", "the label", "the ad said",
                               "the advert", "the listing said", "the description said",
                               "not what", "but its not", "but it isnt", "but it isn't",
                               # the same complaint stated flatly: "they said leather but its
                               # vinyl", "the shop said wool but it was polyester"
                               "they said", "he said", "she said", "the shop said",
                               "but its", "but it was", "but its actually", "not leather",
                               "not wool", "not cotton", "not silk", "fake leather",
                               "not the colour", "not the color", "not that colour",
                               "wrong colour", "wrong color", "wrong shade", "wrong size",
                               "wrong material", "wrong fabric",
                               # the photograph is the description too: "the colour is different
                               # to the photo", "nothing like the picture on the website"
                               "different to the photo", "different from the photo",
                               "different to the picture", "different from the picture",
                               "different to the photos", "different from the photos",
                               "nothing like the photo", "nothing like the photos",
                               "nothing like the picture", "nothing like the pictures",
                               "not like the photo", "not like the picture",
                               "not like the pictures", "colour is different",
                               "color is different", "colour was different",
                               "different colour", "different color",
                               "darker than the photo", "lighter than the photo",
                               # a used or shop-worn thing sold as new is the same lie:
                               # "they sent me a refurbished one instead of new"
                               "instead of new", "not brand new", "sold as new", "said it was new",
                               "ex display", "ex-display", "display model", "shop soiled",
                               "opened box", "used one", "second hand one", "second-hand one",
                               # the flat shape of it, with no "sold as": "they sent me an item
                               # that was used", "the phone i was sent has been used"
                               "was used", "been used", "already used", "used item",
                               "looks used", "sent me a used", "sent me an item that was used",
                               "item that was used", "has been used"),
                              ("phone", "laptop", "bag", "handbag", "jacket", "coat", "watch",
                               "shoes", "trainers", "item", "product", "bought", "seller", "shop",
                               "headphones", "tablet", "console", "boots", "dress",
                               # furniture, fabric and fit are the same rule: the goods have to
                               # match the description
                               "sofa", "settee", "armchair", "chair", "table", "wardrobe", "bed",
                               "mattress", "curtains", "blinds", "rug", "carpet", "furniture",
                               "jumper", "cardigan", "blanket", "bedding", "material", "leather",
                               "wool", "cotton", "silk", "linen", "fabric", "colour", "color",
                               "shade", "size", "description", "advert", "label", "quality",
                               "instead", "brand new")),
          _described_reply,
          guard=_a_description_is_named,
          avoid=("used car", "car dealer", "mot", "mileage", "how can i tell", "how do i check",
                 "is it real", "how do i spot", "how to spot",
                 # buying advice about a refurb is another answer, but one sold AS new is this
                 # one, so the words are pinned to the buying question
                 "buy a refurbished", "buying refurbished", "get a refurbished",
                 "refurbished worth", "should i get a refurbished",
                 "second hand worth", "second hand car", "should i buy", "worth it",
                 # a job advert with no pay on it is a question about the job, not about goods:
                 # "the advert doesnt say the pay" was told about the Consumer Rights Act,
                 # because "advert" is a description word and nothing said what was described
                 "the pay", "say the pay", "says the pay", "salary", "salaries", "wage", "wages",
                 "job advert", "job ad", "the job", "vacancy", "vacancies", "the role pays",
                 "what it pays", "how much it pays", "hourly rate", "per hour", "the hours",
                 "shift", "shifts", "rota")),
    entry("manufacturer-blame", (("manufacturer", "maker", "brand", "warranty department"),
                                 ("have to", "must", "go to", "send it", "right", "says", "refund",
                                  "repair", "said")),
          "No: your contract is with the shop you paid, so the shop has to deal with a faulty "
          "product even when a maker's warranty is involved. If they keep saying \"go to the "
          "manufacturer\", ask for that in writing and quote the Consumer Rights Act."),
    entry("worn-return", (("worn", "wore", "used it", "tags off", "opened it", "slept on",
                           "slept in", "mattress", "used once", "worn once", "wore it once",
                           "worn it once", "wore them once", "out once", "wore it", "worn it",
                           "i opened", "opened the box", "opened the packet",
                           "opened the packaging",
                           # the condition is said as what is missing as often as what was done
                           # to it: "can i return a dress without tags"
                           "without tags", "no tags", "tags on", "tags still on",
                           "without the tags", "without packaging", "without the box"),
                          ("return", "refund", "matter", "still", "shop", "online", "exchange",
                           # "can i take back a dress i wore once" left the key on "take back"
                           # and the line was answered with the customs allowance for bringing
                           # goods into the country
                           "take back", "take it back", "take them back", "bring it back",
                           "bring them back", "send it back", "send them back", "give it back",
                           "return it", "return them")),
          _condition_reply,
          # "can i return a mattress i slept on" is a used-good question, and money's general
          # refund answer now outranks it: the condition is what decides this one
          bias=2),
    entry("refund-timing", (("refund", "money back", "still no refund", "no refund yet"),
                            ("how long", "when", "waiting", "still", "late", "chase", "days",
                             "weeks", "returned", "sent it back", "chased")),
          "A refund must reach you within 14 days of the shop agreeing to it, or of getting the "
          "goods back, and it goes to the original payment card. If it's late, send one written "
          "chaser with the dates, then ask your card provider for a chargeback.",
          # "i returned it and still no refund" is this entry, so the parcel and ticket words are
          # the ones to keep out, not "returned"
          # whether a missing receipt stops the refund is return-without-receipt's question:
          # "i dont have a receipt can i still get a refund" was this card, which answers when
          # the money arrives and not whether the shop can refuse
          avoid=("receipt", "receipts", "proof of purchase",
                 "train", "flight", "plane", "builder", "hotel", "gym", "deposit",
                 "never arrived", "hasn't arrived", "hasnt arrived",
                 # "they wont refund me at all" is the right to a refund, not how long it takes
                 "wont refund", "won't refund", "wont give me a refund", "won't give me a refund",
                 "refused to refund", "refuses to refund", "refusing to refund",
                 "says no refund", "said no refund", "wont give my money back",
                 "won't give my money back"),
          bias=1),
    entry("refund-online", (("return", "send back", "cancel", "refund"),
                            ("online", "internet", "ordered", "delivered", "post", "parcel",
                             "bought online",
                             # the right said as a refusal: "i cancelled within 14 days and they
                             # wont refund" is this window, not how long a refund takes
                             "within 14 days", "inside 14 days", "in the 14 days",
                             "14 day window")),
          "Anything bought online, by phone or by post can be cancelled within 14 days of it "
          "arriving, then sent back within 14 days, with the refund due 14 days after that. "
          "Bespoke items, perishables and opened hygiene products are the usual exceptions.",
          # a parcel that comes back to the person who sent it is not a return to a shop: that
          # line is about the carrier and the reason on the label, and "the parcel i sent was
          # returned to me" was answered with the 14-day cancellation right.
          # "returned to sender" is the buyer's line - the parcel is on its way back and the
          # tracking says so - and the returns card is what answers it. Only the sender's own
          # "returned to me" is held out here.
          avoid=("returned to me", "came back to me", "come back to me",
                 "i sent", "i posted", "sent it", "posted it")),
    entry("consumer-return-window", (("return", "returns", "send back", "send it back", "take back",
                             "take it back", "money back", "refund",
                             # "how long do i have to take something back" says the object in
                             # between, and it was answered with "whichever date it is, three
                             # things settle it" - the right answer was already here
                             "take something back", "take that back", "take the thing back",
                             "bring it back", "give it back", "have it back", "swap it"),
                            ("how long", "how many days", "how much time", "time limit",
                             "how long do i have", "how long have i got", "how long can i",
                             "how long to", "go back with", "take it back by",
                             "deadline", "return window", "returns window", "refund window",
                             "time window",
                             "window to return", "window for a return", "window for returns",
                             "window for returning", "days do i have", "until when", "by when")),
          "Online, by phone or by post you have 14 days from the day it arrives to tell them you "
          "are cancelling and 14 more to send it back, with the refund 14 days after that. In a "
          "shop it is their own returns policy that sets the window for a change of mind - 28 days "
          "is common, and often just an exchange or credit note - but a faulty item is different: "
          "30 days to reject it for a full refund, whatever the sign says.",
          ask=("how", "what", "is", "do", "can", "my", "when"),
          avoid=("tax return", "return to work", "return my call", "return the book",
                 "library", "return home", "flight", "voucher")),
    entry("gift-return", (("gift", "present"),
                          ("return", "refund", "exchange", "unwanted", "wrong size", "receipt")),
          "Shops only have to refund an unwanted gift if their own policy says so, so check the "
          "receipt: many give an exchange or credit note within 28 days. A faulty gift is "
          "different, and whoever bought it can claim a repair or refund.",
          # "shop says i need the receipt to refund a gift" reaches both the lost-receipt answer
          # and wording's ask-for-refund ("says" reads as say), so this needs two points to win
          bias=2),
    entry("warranty", (("warranty", "guarantee", "warranties", "guarantees"),
                       ("phone", "laptop", "washing machine", "appliance", "repair", "replace",
                        "claim", "shop", "expired", "ran out", "says", "out of",
                        # "what is a warranty" and "what does a guarantee cover" ask for the
                        # word, and the bare noun reached nothing: the other words here all need
                        # a product or a fault beside them, and the person who asks what the
                        # word means has neither. Spelled out as phrases so "what should i do
                        # about my warranty" keeps whatever answer it has.
                        "what is a warranty", "whats a warranty", "what is the warranty",
                        "what is a guarantee", "whats a guarantee", "what is the guarantee",
                        "warranty mean", "guarantee mean")),
          "A warranty is a bonus on top of your rights, not a swap for them: in the UK the "
          "retailer has to sort out a faulty product for up to six years (five in Scotland). "
          "Go to the shop first and keep the maker's warranty as the backup.",
          # "should i take out a warranty on my new washing machine" is a buying question:
          # shopping.py already answers it better than a rights line would.
          avoid=("should i take", "should i buy", "should i get", "take out", "worth it",
                 "extra cover", "add on", "extended warranty",
                 # cover that was mis-sold, or that excludes the very thing it was for, is a
                 # complaint about the sale: missold-cover has the firm and the ombudsman
                 "missold", "mis-sold", "misselling", "cancel my warranty", "cancel the warranty",
                 "lied", "doesnt cover", "doesn't cover", "does not cover", "never agreed",
                 "waste of money", "didnt need", "didn't need", "sold me")),
    entry("missold-cover", (("warranty", "warranties", "extended guarantee", "guarantee",
                             "insurance", "cover", "service plan", "care plan", "protection plan",
                             "payment protection", "breakdown cover", "boiler cover",
                             "appliance cover", "add on", "add-on", "ppi"),
                            ("missold", "mis-sold", "misselling", "lied", "lie", "fobbed",
                             "said it covered", "told me it covered", "doesnt cover",
                             "doesn't cover", "does not cover", "no good", "worthless",
                             "useless", "waste of money", "pointless", "cancel", "refund",
                             "never agreed", "didnt need", "didn't need", "did not need",
                             "didnt ask", "didn't ask", "pressured", "not what i was told",
                             "not what i paid for",
                             # the plainest way people put it names the wish, not the need:
                             # "i was sold a warranty i didnt want" was an "I'm listening" while
                             # "didnt ask" and "pressured" both reached this card
                             "didnt want", "didn't want", "did not want", "sold me",
                             "sold it to me", "made me take", "forced to take")),
          "Cover sold alongside something is insurance: you can cancel it and get the premium back "
          "within 14 days, and a firm that sold you cover that did not do what you were told owes "
          "the money back - complain in writing, then to the Financial Ombudsman, which is free and "
          "can order the refund. Check what it excludes before you cancel, because a fault in the "
          "thing itself is already the retailer's job.",

          # a warranty claim, a fob-off about the maker and a question about buying cover are all
          # their own entries: this one is only about how the cover was sold
          avoid=("should i", "worth it", "is it worth", "do i need", "claim on my warranty",
                 "claim on the warranty", "make a claim", "says it doesnt cover",
                 "says it doesn't cover", "shop says my warranty", "go to the manufacturer",
                 "manufacturer", "my boiler is broken", "boiler broken", "no hot water",
                 "pet", "pets", "dog", "cat", "vet", "house insurance", "home insurance",
                 "buildings insurance", "contents insurance", "travel insurance",
                 "car insurance", "motor insurance", "phone insurance"),
          bias=3),
    entry("used-car-dealer", (("car", "van", "vehicle", "motor", "suv", "estate", "mileage",
                              "odometer", "clocked", "written off"),
                              ("dealer", "dealership", "forecourt", "car supermarket",
                               "trade seller", "trader", "from a garage", "car shop", "salesman",
                               "sales man", "mileage", "odometer", "clocked", "lies", "lied",
                               "written off", "cat s", "cat n")),
          "A dealer has to sell a car that is as described, of satisfactory quality and fit to "
          "drive: you can reject it for a full refund within 30 days of collecting it, and in the "
          "first six months the dealer has to prove the fault was not there when it sold it. Put it "
          "in writing and stop driving it if it is unsafe. 'Sold as seen' does not remove those "
          "rights, and the Motor Ombudsman is free.",

          ask=("i", "my", "the", "we", "bought", "buy", "should", "can", "is"),
          avoid=("how much is", "should i buy", "which car", "best car", "what car",
                 "insurance", "finance", "how do i sell", "part exchange", "mot", "tyre",
                 "brakes", "battery", "clutch", "service", "how many miles", "what mileage",
                 "good mileage", "fuel economy", "mpg")),
    entry("second-hand-private", (("second hand", "used", "private seller", "marketplace",
                                   "facebook", "fb marketplace", "car boot", "ebay", "gumtree",
                                   "vinted", "shpock", "boot sale", "used car",
                                   "second hand car", "second-hand car",
                                   # a friend or a mate is a private seller even without the
                                   # words "second hand": "i bought it off a mate and it broke"
                                   "off a mate", "from a mate", "off a friend", "from a friend"),
                                  ("faulty", "broken", "broke", "fell off", "refund", "rights",
                                   "problems", "went wrong", "not as described", "misdescribed",
                                   "doesnt work", "doesn't work", "stopped working",
                                   # the fault after the sale, not the checklist before it
                                   "broke after", "broke down", "broke a week", "packed in",
                                   "went wrong after", "problems since",
                                   # the fault is often a noun in the line, not a verb:
                                   # "the second hand car i bought has a fault"
                                   "fault", "has a fault", "has faults", "needs work",
                                   "needs repairing", "problems with it", "not what i was told",
                                   # the fault is as often the damage in the advert as a verb:
                                   # "got a bike off facebook marketplace and the frame is cracked"
                                   "faulty", "cracked", "crack", "dented", "scratched",
                                   "chipped", "snapped", "fell apart", "damaged",
                                   "not working", "wont work", "won't work", "never worked")),
          "Buying privately is buyer beware: the item only has to match its description, so "
          "there's no right to a refund when it later breaks. From a dealer or shop the full "
          "30-day rejection right applies, and paying by card adds your bank as a route.",
          # "i bought a used car and it broke after a week" is this answer, not the buying
          # checklist: the words fit both, and this one is about the fault you already have
          bias=2,
          # a dealer, a forecourt or a trade seller is the 30-day right, not buyer beware
          avoid=("dealer", "dealership", "forecourt", "garage", "showroom", "trade seller",
                 "trader", "car supermarket")),

    # --- money back when someone else is at fault ------------------------------
    entry("credit-card-claim", (("credit card", "credit card company", "section 75", "s75",
                                  "deposit", "paid up front",
                                 "paid upfront"),
                                ("refund", "went bust", "gone bust", "never arrived",
                                 "what is", "how does it work", "does it cover", "cover",
                                 "covers", "mean",
                                 "didn't arrive", "didnt arrive", "faulty", "fraud", "claim",
                                 "chargeback", "protection", "vanished", "stopped trading",
                                 "closed down", "liquidated", "administration", "deposit")),
          # "how do i claim section 75" used to get the rule and nothing to do with it. The
          # definition leads, because "what is section 75" asks for it; the claiming step is
          # the half a person cannot work out from the name, so it comes after.
          "Pay over £100 on a credit card and the card company is jointly liable if the seller "
          "folds or the goods never turn up: that's Section 75, up to £30,000, and it works for "
          "deposits too. To claim, write to the card company saying you are claiming under "
          "Section 75, with the date, the amount, the seller and what went wrong; if they refuse, "
          "the Financial Ombudsman is free.",
          avoid=("owe", "owing", "minimum payment", "paying off", "pay it off", "debt",
                 "balance", "interest",
                 # a deposit held by a landlord is the tenancy answer: "claim back my deposit"
                 # matched "deposit" and "claim" here and got the Section 75 rule
                 "landlord", "landlady", "tenancy", "tenant", "letting agent", "rent",
                 "moving out", "moved out", "end of my tenancy", "flat"),
          # A deposit that has not been paid yet is a savings goal, not a card payment: "what is
          # the best way to save for a house deposit" matched "deposit" and "what is" here and
          # was told about Section 75. It is a guard and not an avoid word, because an avoid
          # phrase is read loosely - any of its words, in any order - so "house deposit" stands
          # the row down for "how much is a house deposit" as well, and the rows that answer the
          # savings question stopped winning the line at all.
          guard=_not_saving_for_a_deposit),
    entry("duplicate-charge", (("charged twice", "charged me twice", "double charged",
                                "duplicate charge", "two payments",
                                # taken twice from a card or an account, rather than charged
                                "taken twice", "took it twice", "took it twice out",
                                "took the money twice", "money taken twice", "money twice",
                                "two times", "debited twice", "charged two times",
                                "taken out twice", "double payment",
                                "twice from my card", "twice from my account",
                                "twice from my bank", "paid twice"),
                               ("order", "online", "bank", "card", "back", "refund", "shop",
                                "app", "company", "same thing", "same day", "payment",
                                "payments", "bill", "account", "meal", "restaurant", "pub",
                                "takeaway",
                                # "they took the money twice" names nothing but the money
                                "money", "cash", "twice", "two times")),
          "Send the company the two payment references and ask for the duplicate to be reversed, "
          "in writing, with a 14-day deadline. If it isn't back by then, ask your card provider for "
          "a chargeback and send them the same evidence.",
          # a card or a payment has to be in the line: someone using the card is the unauthorised
          # payment answer, and a bill that is simply high is the money domain's
          avoid=("stolen", "lost my card", "someone used", "fraud", "suspicious", "unauthorised",
                 "unauthorized", "pin", "contactless", "how much", "why is my bill",
                 # a payment the person never made is not a duplicate of one they did
                 "didnt make", "didn't make", "not me", "never made", "i didnt authorise",
                 "i didn't authorise", "i didnt pay", "i didn't pay",
                 # a till that charged twice is the shelf-price answer's own line
                 "supermarket", "till", "checkout", "in the shop", "at the shop",
                 # two payments the person owes and has not made are missed ones, not duplicate
                 # ones: "i missed two payments on my catalogue" was told to ask for the duplicate
                 # to be reversed, and money's missed-payment row answers that line.
                 "missed", "miss", "overdue", "late", "forgot", "forgotten", "behind on",
                 "arrears", "not paid", "havent paid", "haven't paid", "cant pay", "can't pay"),
          bias=2),
    entry("chargeback", (("chargeback", "wrong amount"),
                         ("bank", "card", "debit", "credit", "ask", "claim", "back",
                          "what is", "whats a", "how does", "how do", "work", "works",
                          "explain", "mean")),
          "Ask your bank for a chargeback: it reverses a card payment for goods that never came, "
          "arrived damaged or were not what was described. Most banks take claims up to 120 days "
          "from the payment, and it's the route for debit cards under £100."),
    entry("parcel-missing", (("parcel", "package", "delivery", "order", "courier", "locker",
                              "inpost", "parcel box", "pick up point",
                              # who brought it is named instead of the thing: "the driver left it
                              # with a neighbour without asking" was only sympathy, because no
                              # word of the line was a parcel.
                              "driver", "the driver", "delivery driver", "courier driver",
                              "postman"),
                             ("not arrived", "never arrived", "lost", "missing", "didn't arrive",
                              "didnt arrive", "late", "tracking", "delivered", "stolen",
                              "stole", "stolen it", "nicked", "someone took", "taken from",
                              "left in the bin", "in the bin", "in a bin", "in the recycling",
                              "in a bush", "behind the bin", "thrown in",
                              "hasnt come", "hasn't come", "still waiting", "still not here",
                              "still not arrived", "no sign of it", "no code", "code",
                              "cant collect", "can't collect", "cant open", "can't open",
                              # the plainest way it is said: "ordered two weeks ago still nothing"
                              "still nothing", "nothing yet", "no sign", "never came",
                              "never come", "never turned up", "havent got it", "haven't got it",
                              "havent had it", "still hasnt", "still hasn't", "still not got",
                              "where is it", "where is my", "weeks ago", "days ago",
                              # "the courier left it with a neighbour and now it's gone"
                              "neighbour", "neighbours", "neighbor", "left it with",
                              "left it next door", "next door", "with a neighbour")),
          "Until a parcel reaches you it's the retailer's responsibility, not yours: tell them "
          "it hasn't arrived and ask for a replacement or refund. If they stall, ask your card "
          "provider for a chargeback, and report a \"delivered\" parcel you never got the same day.",
          # the door, the wall and the car are not the parcel: "the delivery driver damaged my
          # front door" was the missing-parcel answer, when the parcel is in the hall
          # the verb matters as much as the object: "the parcel was left at my door" is still a
          # missing parcel, and only a driver who damaged the place is not
          avoid=("damaged my door", "damaged the door", "damaged my wall", "damaged the wall",
                 "damaged my gate", "damaged my fence", "damaged my hedge", "damaged my drive",
                 "damaged my house", "damaged my car", "damaged my front",
                 "knocked my wall", "knocked my gate", "knocked my fence",
                 "knocked my hedge", "knocked my wall", "scraped my car", "scraped my gate",
                 "hit my car", "hit my gate", "hit my wall", "dented my car",
                 "drove into my", "crashed into my", "drove over my",
                 # The seller is not the buyer: "tell the retailer" is advice for the person
                 # waiting, and these lines are the sender's own - "can i track a parcel i
                 # sent", "i sent a parcel and the tracking has not updated", "i sold
                 # something on ebay and it got lost" - which lifeadmin's claim answers.
                 "i sent", "we sent", "i posted", "we posted", "i shipped", "i sold",
                 "parcel i sent", "parcel i posted", "the one i sent", "i have sent",
                 "i've sent", "my buyer", "buyer says")),

    # A line about the tracking page names no parcel at all, and the page is where a person looks
    # first: "tracking hasnt moved", "the tracking hasnt updated in a week", "it says out for
    # delivery since tuesday" and "the tracking number doesnt work" were a "I'm listening - say
    # more if it helps." or the whole missing-parcel speech. The status phrasing is a key word
    # here as well as the page, so the same thing said without the word "tracking" is still this
    # row, and the answer is about the page rather than about the parcel being lost.
    entry("tracking-not-moving", (("tracking", "track and trace", "a tracking", "the tracking",
                                   "my tracking", "tracking page", "tracking number",
                                   "courier app", "the app says", "the website says",
                                   "out for delivery", "in transit", "at the depot",
                                   "been scanned", "no scan"),
                                  ("not moved", "hasnt moved", "hasn't moved", "not updated",
                                   "hasnt updated", "hasn't updated", "no movement",
                                   "no update", "stuck", "not changed", "nothing since",
                                   "same for", "since monday", "since tuesday", "since friday",
                                   "for a week", "for days", "for three days", "for 3 days",
                                   "for two days", "out for delivery", "in transit",
                                   "at the depot", "not working", "doesnt work", "doesn't work",
                                   "invalid", "not recognised", "not recognized", "wrong number",
                                   "no information", "still says")),
          # Two sentences, not four: a longer answer leaves sentences over, and the follow-up to
          # it ("what do i do") was given one of them - "Keep a screenshot of each update." - as
          # though that were the answer.
          "The tracking page belongs to the courier, but the parcel is still the seller's to "
          "deliver: ask the shop in writing for the current status and a new date, quoting the "
          "order number and the day it last moved, and keep a screenshot of each update. Once the "
          "promised date has passed, or the page has not moved for a week or more, ask for a "
          "replacement or a refund; if the number is not recognised, ask them for the right one, "
          "because that is theirs to fix.",
          shape=(_a_stretch_of_waiting,),
          bias=1,
          # "says" is in the ask because the page is quoted: "tracking says in transit for 5
          # days" names no other framing word, and the row was passed over for that alone.
          ask=("my", "the", "it", "its", "i", "we", "they", "is", "does", "has",
               "says", "said", "saying"),
          # a parcel they sent is the seller's side of it (see parcel-missing), a damaged one is
          # the damage card, and "track" on its own is a spending or a cycle question
          avoid=("i sent", "we sent", "i posted", "we posted", "i sold", "my buyer",
                 "buyer says", "damaged", "broken", "smashed", "battery", "lost my job",
                 "interview", "my spending", "my period", "my cycle", "track my steps")),

    # a driver who damages the place is not a missing parcel or a damaged one: the parcel
    # arrived, and what is broken is the wall, the gate or the car
    entry("courier-damage", (("delivery driver", "delivery man", "courier", "delivery van",
                              "postman", "post office van", "delivery company"),
                             ("damaged", "knocked", "hit", "scraped", "dented", "crashed",
                              "drove into", "broke", "smashed", "took out", "went into",
                              "reversed into", "clipped")),
          "A courier that damages your property owes the repair, and so does the shop that booked "
          "them: photograph it the same day, write down the tracking number, the company and the "
          "van's registration, and send the claim to the delivery company in writing with 14 days "
          "to answer. If they stall, chase the retailer who arranged the delivery, and if a van "
          "hit your car report it to the police as well as your insurer.",
          # a damaged parcel is the goods, and a parcel that never came is the missing parcel
          avoid=("my parcel", "the parcel", "my order", "the order", "my package", "my item",
                 "the item", "arrived damaged", "came damaged", "box", "packaging")),

    # A licensed taxi has to run the meter, and the council that plates the car is the body that
    # gives the money back. An app or a minicab is a quoted price, so it is disputed where it was
    # booked. Asking what a taxi costs is a travel question, so a fare question passes on it.
    entry("taxi-fare", (("taxi", "cab", "minicab", "mini cab", "private hire", "uber", "taxi driver",
                         "hackney", "black cab", "the driver",
                         # "he charged me double to the airport" names no taxi at all
                         "from the airport", "to the airport"),
                        ("too much", "overcharged", "long way", "longer way", "longer route",
                         "took a long", "scenic", "ripped off", "refused to take", "wouldnt take",
                         "wouldn't take", "no meter", "wouldnt put the meter", "didnt use the meter",
                         "wouldnt use the meter", "wouldn't use the meter", "wont use the meter",
                         "meter was off", "no meter on", "didnt put it on the meter",
                         "charged me", "wont give a receipt", "fixed price", "extra charge",
                         "charged me double", "double the fare", "twice the fare",
                         "ripped me off", "overcharged me", "refused to take")),
          "A licensed taxi has to run the meter, so a fare that is not on it is a complaint to the "
          "council that licenses the car: note the plate or licence number, the time and the route, "
          "and complain the same week. A minicab or an app should have quoted the price before you "
          "got in, so dispute it in the app first. Keep the receipt, because the council can make "
          "the driver hand the money back.",
          # what a taxi costs and how to book one is the travel domain's answer
          avoid=("how much is a taxi", "how much does a taxi", "taxi from the airport",
                 "taxi to the airport", "book a taxi", "cheapest", "cheap taxi",
                 "how do i book", "how far", "how long does the taxi",
                 # how to avoid all this is the travel domain's advice, not a complaint loop:
                 # "how do i avoid getting ripped off by a taxi abroad" was sent to the council
                 "avoid", "how do i not", "how to not", "before i get in", "should i tip",
                 "is it safe")),

    # --- travel ----------------------------------------------------------------
    # The entry is the Delay Repay bands, so it is keyed on the delay, not on any request for
    # money back: "how do i get a refund for a train ticket" names no delay, and the full answer
    # for it (an unused ticket AND Delay Repay) is travel's `train-refund`.
    entry("consumer-train-delay", (("train", "train company", "rail", "delay repay"),
                          ("delay", "delayed", "late", "cancelled", "compensation",
                           "delay repay")),
          ("Claim Delay Repay from the train company: most pay 25% for 15 to 29 minutes late, 50% "
           "for 30 to 59 and 100% for an hour or more. Keep your ticket or booking email and claim "
           "online within 28 days.",
           "Delay Repay is the one to ask for: 25% of the ticket back for 15 to 29 minutes, 50% "
           "for 30 to 59, and all of it for an hour or more. Most companies take claims online up "
           "to 28 days after the journey, and a scan of the ticket is enough."),
          # A late train in the middle of a story is not a claim: "the train was late so i
          # missed my interview" wants a hand with the interview, not a Delay Repay form, so the
          # entry only answers when the line actually asks for something back.
          ask=("claim", "compensation", "refund", "money back", "delay repay", "entitled",
               "owed", "rights", "can i get", "anything i can do", "what can i do")),
    # A late train has Delay Repay; a bus that keeps being cancelled had nothing, so "the bus has
    # been cancelled three mornings running and i've been late twice, how do i complain" was a
    # shop complaint ("what you bought, when, what went wrong") that names nobody a bus passenger
    # can write to. The route for a bus is the operator first, then the watchdog and the Traffic
    # Commissioner, and the same answer covers a bus driver and a stop that is never served.
    entry("bus-service-complaint",
          (("bus", "buses", "bus company", "bus operator", "bus driver", "bus stop",
            "bus route", "bus service", "the bus", "my bus", "coach", "coach company",
            "school bus", "shuttle"),
           ("complain", "complains", "complaining", "complaint", "complaints", "who do i",
            "report", "refund", "compensation", "cancelled", "canceled", "cancellation",
            "keeps getting cancelled", "keeps being cancelled", "always late", "late again",
            "never turns up", "didnt turn up", "didn't turn up", "never came", "reliable",
            "unreliable", "missed three", "late twice", "who to", "what can i do")),
          ("Complain to the bus operator first, in writing, with the route number, the stop, the "
           "date and the time of each failure: their customer services address is on the "
           "timetable or their website, so ask for a reply within 10 working days and keep the "
           "reference. If it goes on, a passenger body takes it up free - Bus Users UK outside "
           "London, London TravelWatch inside it - and the Traffic Commissioner registers repeated "
           "failures, which is what actually moves a timetable. A route the council pays for goes "
           "to the council's transport team as well, because they hold the contract.",
           "Put it in writing to the operator with the route, the stop and the dates, and give "
           "them 10 working days: most refund or explain from that letter alone. If nothing "
           "changes, Bus Users UK (or London TravelWatch in London) takes cases for free, and the "
           "Traffic Commissioner is who registers a service that keeps failing - a route the "
           "council funds also goes to their transport team, who can call the operator in."),
          # The row answers the asking, not the grumbling: "the bus was late again" is the
          # existing claim card's question, which says how to claim it back, and the first draft
          # of this row took it, and took "funny that the bus never came" from the small talk.
          ask=("complain", "complains", "complaining", "complaint", "complaints", "who do i",
               "who to", "who can i", "how do i complain", "report it", "report the bus",
               "raise a complaint", "make a complaint", "what can i do about", "who should i",
               "is there anyone", "anyone i can"),
          # a bus or coach as a way to get somewhere is the travel domain's question, and a
          # loyalty card question is not a service complaint
          avoid=("cheapest", "cheap coach", "how much is", "how much does", "ticket price",
                 "day ticket", "return ticket", "timetable", "what time", "when does the bus",
                 "how do i get to", "how far", "journey", "megabus", "national express",
                 "bus pass", "apply for", "concession", "lost property", "left my bag",
                 "book a coach", "book a bus", "how long is the coach", "airport coach"),
          bias=1),
              entry("hotel-cancel", (("hotel", "booking", "guest house", "airbnb"),
                           ("refund", "cancel", "non-refundable", "non refundable", "charged",
                            "money back")),
          "A non-refundable rate usually means no cash back, but ring the hotel and ask to move "
          "the date instead: many will with notice, and it costs nothing to ask. If you booked "
          "through a site, that site holds the cancellation, not the hotel.",
          # a subscription answer used to win "hotel charged me for a room i cancelled" because
          # "cancel" is the strongest word in it; naming a hotel makes this the better answer
          # a filthy room or a room that is not as booked is the room answer, not this one
          avoid=("filthy", "dirty", "unclean", "smells", "smelly", "bed bugs", "cockroaches",
                 "no hot water", "not what we booked", "mould", "mold", "stained",
                 "cleaning fee", "cleaning charge", "service fee", "minibar",
                 # "booking" alone is not a hotel: a cancelled festival or a cancelled gig and
                 # its booking fee is an event ticket, and this card was taking it
                 "festival", "gig", "concert", "artist", "band", "match", "theatre", "comedy",
                 "event", "booking fee", "booking fees", "airline", "flight", "train",
                 "restaurant", "table", "haircut", "appointment", "viewing", "tradesman"),
          bias=1),
    entry("hotel-room-bad", (("hotel", "room", "guest house", "b and b", "apartment", "villa",
                              "sea view", "balcony", "terrace", "suite", "holiday let",
                              "cottage",
                              # a holiday let is a booking you complain about, not a home to
                              # air out: "the airbnb smells damp" is the host's line, and the
                              # home damp-smell row stands down for airbnb by name
                              "airbnb", "air bnb", "air-bnb", "holiday home", "holiday cottage",
                              "self catering"),
                              ("filthy", "dirty", "unclean", "smell", "smelly", "bed bugs",
                               "cockroaches", "no hot water", "not what we booked", "mould",
                               "mold", "stained", "noise all night", "disgusting",
                               "nothing like the photos", "not like the photos",
                               "nothing like the pictures", "not like the pictures",
                               # what the room looked at is the same complaint: a view sold and
                               # not given, a car park instead of the sea
                               "sea view", "no view", "view of the", "overlooked",
                               "paid for a view", "car park instead", "wasnt what we paid for",
                               "wasnt what i paid for", "not what i paid for",
                               "photos", "pictures", "view", "overlooked", "advertised",
                               "as advertised", "as described",
                               # a room that is not the one booked is the same complaint, and
                               # people say it by naming the room they should have had
                               "different room", "wrong room", "one i booked", "one we booked",
                               "gave me a different", "gave us a different", "a different room",
                               "moved us to", "overbooked", "smaller room", "no window",
                               "not the room")),
          "Photograph it and complain at reception, or to the host if it is a holiday let, before "
          "you unpack, and ask to be moved or cleaned: a room that is not what was advertised is "
          "a breach of the booking, so you can ask for a refund for that night, and a partial "
          "refund for a spoiled stay. If the hotel "
          "will not, claim from the site you booked with and then your card company, quoting what "
          "the listing promised.",
          # a booking you want to cancel is the cancellation answer
          ask=("refund", "money back", "compensation", "complain", "complaint", "can i",
               "what can i", "entitled", "claim", "photos", "pictures", "move us", "moved",
               "upgrade", "nothing like", "view", "paid for", "instead",
               # a plain statement of the fault is the same complaint, and it wants the same
               # next step: "my hotel room was filthy", "the balcony overlooked a building site"
               "filthy", "dirty", "bed bugs", "smell", "mould", "no hot water", "overlooked",
               "building site", "wasnt what", "wasn't what", "not what we booked",
               "noise all night", "noisy",
               # the plain statement of it, with no ask word in the line at all
               "different room", "wrong room", "one i booked", "one we booked", "gave me a",
               "gave us a"),
          bias=1,
          # a room that smells of damp in somebody's own home wants the home's answer, not this
          guard=_a_hotel_room_or_no_home,
          avoid=("cancel it", "want to cancel", "non refundable", "non-refundable", "move the date",
                 # choosing a hotel is a booking question, not a complaint about one: "hotel with
                 # a sea view in cornwall" was being told to photograph the room in reception
                 "hotel with a", "hotel with the", "hotels with", "a hotel with", "hotels in",
                 "a hotel in", "hotel deals", "i need a hotel", "i want a hotel", "we want a hotel",
                 "looking for a hotel", "find a hotel", "recommend a hotel", "which hotel",
                 "where to stay", "somewhere to stay",
                 # a smell in a room at home is a damp question, not a complaint about a
                 # hotel: "how do i get rid of a musty smell in a room" and "how do i air a
                 # room that smells damp" were both answered with "photograph it and complain
                 # at reception" because "room" and "smell" are all this key needed. money.py's
                 # hotel-complaint grew the same avoid words for the same reason.
                 # A bare "musty" or "damp" is deliberately NOT here: a musty hotel room is
                 # still this card's line ("the hotel room smells musty" wants the desk). What
                 # is here is the shape of the room at home, where the damp is the subject:
                 # "how do i get rid of a musty smell in a room" and "how do i air a room that
                 # smells damp" were both answered with "photograph it and complain at
                 # reception", because "room" and "smell" are all this key needed.
                 "in a room", "in the room", "in my room", "a room that", "room that smells",
                 "room smells of",
                 "basement", "cellar", "loft", "attic", "bedroom", "living room",
                 "spare room", "kitchen", "bathroom", "wardrobe", "cupboard", "mattress",
                 "carpet", "carpets", "bin", "at home", "my house", "my flat", "my room",
                 "our house", "our flat", "whole house", "the house", "the flat")),
    entry("holiday-refund", (("package holiday", "package", "holiday", "travel agent",
                              "tour operator", "cruise", "booking"),
                             ("refund", "money back", "wont refund", "won't refund", "cancelled",
                              "cancel", "went into administration", "went bust", "went under",
                              "folded", "atol", "collapsed")),
          "If the organiser cancels the package you are owed a full refund within 14 days, and if "
          "they cancel inside 14 days of leaving you can claim compensation on top. The organiser "
          "named on the booking owes it, not the hotel: ask in writing, then the card company, "
          "which is jointly liable over \u00a3100. An ATOL certificate pays for a replacement holiday or "
          "your money back when the company goes under.",

          # leave a boss cancelled is not a package that collapsed
          guard=_not_a_leave_question,
          # the room that was not as described is a different fight, and the 28-day deadline a
          # third one
          avoid=("how long", "time limit", "deadline", "too late", "ruined", "dirty", "filthy",
                 "sick", "pool was closed", "not as described",
                 # a ticket for a gig, a festival or a match is not a package holiday, even
                 # though it is "booked" and then cancelled: "the festival was cancelled do i
                 # get the booking fee" was answered with the ATOL refund
                 "festival", "gig", "concert", "band", "artist", "match", "theatre", "comedy",
                 "booking fee", "booking fees", "ticket",
                 # your own change of mind is the other question, answered below
                 "want to cancel", "wont to cancel", "need to cancel", "have to cancel",
                 "how do i cancel", "how can i cancel", "im ill", "i am ill", "cant go",
                 "can't go", "change my mind", "changed my mind"),
          bias=1),
    # a package holiday is one contract, so the organiser changing the hotel or the dates is a
    # change you can refuse: it is neither a cancellation nor a bad room
    entry("holiday-changed", (("package holiday", "package", "holiday", "holiday booking",
                               "tour operator", "travel agent", "cruise", "hotel", "resort",
                               "villa", "apartment", "all inclusive", "abroad"),
                              ("changed our hotel", "changed the hotel", "swapped our hotel",
                               "different hotel", "moved us", "moved to another hotel",
                               "changed our flight", "changed the flight", "changed the time",
                               "changed the dates", "changed the date", "changed the resort",
                               "changed our room", "changed the room", "changed the itinerary",
                               "different flight", "different dates", "different resort",
                               "hotel was changed", "was changed at the last minute",
                               "changed at the last minute", "given a different hotel",
                               "given another hotel", "put in a different hotel",
                               "swapped at the last minute")),
          "Moving you to another hotel, resort or date is a significant change: you can refuse it "
          "and take a full refund within 14 days, or accept it and ask for the price difference "
          "back plus about 20 to 30 percent of the price for what you lost. Put that in writing to "
          "the organiser, not the hotel, and name the Package Travel Regulations; ABTA or the CAA "
          "can take the complaint.",

          avoid=("went bust", "folded", "went under", "administration", "cancelled our holiday",
                 "cancelled the holiday", "cancel my holiday", "how do i cancel",
                 "want to cancel", "how much", "worth it", "should i book", "when should i book",
                 "dirty", "filthy", "not as described", "ruined", "storm", "flight was delayed"),
          bias=2),
    # the mirror of holiday-refund: the company cancelling is a refund, but the person
    # cancelling is a different answer, and it used to get the organiser-cancels text
    entry("holiday-cancel-mine", (("package holiday", "package", "holiday", "holiday booking",
                                   "trip", "travel agent", "tour operator", "cruise"),
                                  ("want to cancel", "wont to cancel", "need to cancel",
                                   "have to cancel", "how do i cancel", "how can i cancel",
                                   "can i cancel", "im ill", "i am ill", "cant go", "can't go",
                                   "change my mind", "changed my mind", "not going", "called off",
                                   "cancel it", "cancel the holiday", "cancel my holiday",
                                   "cancel my trip", "cancel my booking")),
          "Tell the operator in writing as soon as you know, because the cancellation charge is set "
          "by how close you are to leaving: most scales lose the deposit weeks out and the whole "
          "price in the last week or two, so ask for their scale in writing. If you are ill, travel "
          "insurance pays, with a doctor's note and a call before you cancel. Cheaper routes: "
          "transfer it to someone else, or move the date for a fee.",

          bias=2,
          # a holiday the boss took back is the leave rows' answer
          guard=_not_a_leave_question,
          # what the company did, and other people's cancellations, are different answers
          avoid=("they cancelled", "they cancel", "company cancelled", "organiser cancelled",
                 "airline cancelled", "flight was cancelled", "went bust", "went under",
                 "folded", "administration", "atol", "wedding", "venue", "hotel booking",
                 "broadband", "gym", "phone", "insurance")),
    entry("holiday-ruined", (("package holiday", "holiday", "hotel", "resort", "cruise"),
                             ("ruined", "not as described", "nothing like",
                              "not like the photos", "photos", "pictures", "advertised",
                              "dirty", "filthy", "closed",
                              "building site", "building work", "scaffolding", "works next door",
                              "noise", "noisy", "wasnt as described", "wasn't as described",
                              "complaint", "complain", "compensation", "sick",
                              "misleading", "refund", "money back", "wont refund",
                              "won't refund", "cancelled", "wont let me",
                              # coming home early is the same spoiled holiday, and a storm that
                              # closes the resort is not the holidaymaker's fault
                              "cut short", "came home early", "came back early", "storm",
                              "left early", "sent home", "washed out")),
          ("Complain in writing to the rep while you're there and to the company when you're back, "
           "and photograph what's wrong: that record is what a claim rests on. A package holiday "
           "has to match what was advertised, so a closed pool or a filthy room is a price "
           "reduction or compensation, not bad luck.",
           "You can ask for a specific figure rather than \"compensation\": what the closed pool "
           "or the filthy room cost you, with photos and the dates. The organiser has to put it "
           "right, and if they refuse, the free travel ombudsman or the small claims court is the "
           "next step."),
          guard=_not_a_leave_question),
    entry("holiday-deadline", (("package holiday", "package", "holiday", "hotel", "tour operator"),
                               ("time limit", "how long", "deadline", "too late", "28 days",
                                "still claim")),
          "Tell the organiser within 28 days of getting home: that's the deadline in the Package "
          "Travel Regulations, and claims after it get much harder. Keep the photos, receipts and "
          "any emails with the rep, and name the organiser you booked with, not the hotel.",
          # "i need 2000 for a holiday how long will it take to save" is a sum by a date, and
          # "holiday" with "how long" here is a claim deadline instead. Nobody saves 2000 towards
          # a claim.
          guard=saving_for_a_trip),

    # --- companies, bills and contracts ---------------------------------------
    # A heavy thing left on the pavement is a delivery that was not finished, and what was
    # promised in the checkout is the test - not a right to have anything carried anywhere.
    entry("delivery-upstairs", (("delivery", "delivery man", "delivery driver", "courier",
                                 "delivery company", "the driver", "van"),
                                ("upstairs", "up the stairs", "inside the house", "into the house",
                                 "into my flat", "to the door", "wouldnt bring", "wouldn't bring",
                                 "wont bring", "won't bring", "refused to bring", "wouldnt carry",
                                 "wouldn't carry", "refused to carry", "wouldnt take it in",
                                 "wouldn't take it in", "left it in the hall", "room of choice",
                                 "two man", "two men", "one man")),
          "What the checkout promised is what you paid for: if it said room of choice, upstairs or "
          "inside, a driver who will not bring it in has not finished the delivery, and the seller "
          "has to send someone who will or refund the delivery charge. Say it in writing the same "
          "day with a photo of where it was left, and do not drag a heavy item yourself - a "
          "damage you caused lifting it is the fight you want to avoid.",
          # a parcel left out and taken or soaked is the missing or damaged parcel's answer
          avoid=("stolen", "stole", "taken from", "went missing", "in the rain", "soaking",
                 "wet through", "over the fence", "over the gate", "thrown")),

    entry("damaged-delivery", (("arrived damaged", "damaged", "smashed", "cracked", "broken in",
                                "broken", "broke", "arrived broken", "damaged in the post",
                                # a mark that came with the delivery is the same complaint as a
                                # smashed box: "my sofa arrived with a scratch" is the note-it-on-
                                # the-delivery-note answer, not the refund ladder. The arrival word
                                # is in the second half of the key, so a scratch found later is
                                # still the shop's under faulty-goods.
                                "scratch", "scratched", "scraped", "dented", "chipped", "chip",
                                "stained", "marked", "dinged",
                                "threw", "thrown", "over the fence", "in the rain", "left outside",
                                "on the doorstep", "on the step", "soaking", "wet through",
                                "trodden on"),
                               ("delivery", "parcel", "courier", "order", "arrived", "post",
                                "driver", "box", "arriving",
                                # "my fridge came dented" and "my sofa came with a scratch" say
                                # the same thing as "arrived" does
                                "came", "come with", "comes with", "came with", "turned up",
                                "turns up", "turn up")),
          "Photograph the damage before you unpack further and tell the retailer the same day: they "
          "owe you a replacement or refund, and the courier's insurance is their problem, not "
          "yours. Don't sign for anything marked damaged without noting it.",
          # a parcel that was left outside and then taken was never delivered to you, so the
          # theft is the missing-parcel answer, not the damaged-goods one
          avoid=("stolen", "stole it", "thief", "thieves", "someone took", "taken from",
                 "went missing", "porch pirate", "nicked",
                 # a meal that arrives cold is not a damaged parcel: "the fish and chips arrived
                 # cold" reached this row once "chip" was a key word here, because the matcher
                 # reads "chips" as the same word. The food answers own those lines.
                 # ("chips" alone cannot be the word here: it reads as "chip" too, and a chip
                 # off a table edge that came with the delivery is this row's line.)
                 "fish and chips", "chip shop", "fish and", "takeaway", "take away", "take-away",
                 "deliveroo",
                 # a pet scratches furniture and a delivery arrives scratched: the same fenced
                 # pair money's damaged-on-delivery carries, because "how do i get my cat to use
                 # a scratch post" carries the word "post" and "my cat keeps scratching the new
                 # sofa" carries the mark itself. Nothing about an animal is a damaged parcel.
                 "cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "puppies", "pet",
                 "pets", "claw", "claws", "clawing", "scratch post", "scratching post",
                 "just eat", "uber eats", "pizza", "curry", "kebab", "burger", "meal",
                 "arrived cold", "came cold", "gone cold", "food", "groceries", "supermarket")),
    entry("complain-formally", (("complain", "complaint", "complain about", "complain to"),
                                ("company", "shop", "service", "provider", "bill", "refund",
                                 "them", "no response", "ignoring", "supermarket", "retailer",
                                 "store", "business")),
          "Complain in writing, say what you want (a refund, a repair, an apology) and give them "
          "14 days. If that fails, ask for a final response or deadlock letter and take it free "
          "to the relevant ombudsman; keep every email and reference number."),
    entry("ombudsman", (("ombudsman", "financial ombudsman", "deadlock letter"),
                        ("how", "claim", "complain", "free", "worth", "long", "escalate",
                         "point", "use", "do", "any good", "what", "which", "what is")),
          "The ombudsman is free for you and binding on the company: give the firm 8 weeks, or ask "
          "for a deadlock letter, then send the ombudsman your complaint and the final response. "
          "Financial disputes go to the Financial Ombudsman Service, and you keep the right to go "
          "to court instead."),
    entry("consumer-bank-complaint", (("bank", "bank account", "building society", "current account",
                              "savings account", "app bank"),
                             ("complain", "complaint", "closed my account", "close my account",
                              "frozen", "blocked", "unfair", "charged me", "charges", "fees",
                              "refused", "messed up", "ombudsman", "customer service")),
          "Complain to the bank in writing first and keep the date: it has 8 weeks to give you a "
          "final answer, and often answers sooner. If you are not happy, the Financial Ombudsman "
          "Service is free and its decision binds the bank, and you keep the right to go to court "
          "instead. A bank closing your account has to give notice and tell you why, unless that "
          "would tip off a criminal.",

          # the ombudsman itself, a transfer that went to the wrong place and a card dispute
          # are their own answers
          avoid=("ombudsman", "deadlock", "transfer", "scam", "fraud", "suspicious",
                 "identity", "loan", "mortgage", "overdraft", "interest rate")),
    entry("gym-cancel", (("gym", "leisure centre", "fitness class"),
                         ("cancel", "cancelling", "cancellation", "contract", "membership",
                          "stop paying", "quit", "closed", "closed down", "shut down",
                          "went bust", "keeps charging me", "still charging me",
                          "charged me after", "took another payment", "after i cancelled",
                          "after i quit", "after i joined")),
          "Cancel in writing, by email, and keep the date you sent it: most gyms want a month's "
          "notice, so email the branch rather than telling the desk. If a payment went out after "
          "you cancelled, ask your bank for a direct debit indemnity, which has to put it back. "
          "Joined online? You have 14 days to cancel, and moving away or injury usually gets you "
          "out early. If the gym has closed, ask for the unused months.",

          # "is a gym membership worth it?" is a budgeting question, not a cancellation.
          # bias: the worth-it entry shares the word "gym", so keep this one ahead of the
          # older cancel-gym advice entry for the steps
          bias=2,
          ask=("cancel", "cancelled", "cancelling", "cancellation", "quit", "leave", "left",
               "get out", "end", "stop paying", "joined", "closed", "shut", "bust",
               "charging", "payment"),
          # "my gym is closed on sundays" is the opening times, not a contract
          avoid=("closed on", "open on", "opening hours", "open at", "what time", "closes at",
                 "sundays", "is it open",
                 # "how do i cancel my gym membership" is lifeadmin's cancel-gym answer, which
                 # already gives the notice, the form and the direct debit: this entry is for
                 # the money that went out after a cancellation and a gym that has closed
                 "how do i cancel", "how do i cancel my", "how to cancel", "how do i quit",
                 "how do i leave", "how do i end", "how to get out", "how do i get out",
                 "how can i cancel", "can i cancel",
                 # "is that a good idea?" wants the advice, not the steps: the budgeting answer
                 # weighs it and only then says how to cancel
                 "good idea", "bad idea", "is it worth", "worth it", "should i cancel",
                 "worth cancelling", "shall i cancel", "should i join", "worth joining",
                 "is joining", "is a gym worth")),
    entry("consumer-gym-worth-it", (("gym", "gym membership", "leisure centre", "fitness class"),
                           ("worth it", "worth", "good idea", "should i cancel", "shall i cancel",
                            "is it worth", "bad idea", "waste of money", "keep paying")),
          "Weigh it by cost per visit: at £40 a month, going 40 times a year is £12 a session and "
          "going 12 times is £40. If that number makes you wince, freeze the membership for a "
          "month or two if the contract allows it, or cancel and pay per class for a while, then "
          "see whether you miss it. Check the notice period and any joining fee before you decide, "
          "because a year's contract is not worth it if you would rather spend the money elsewhere.",
          # the steps to cancel and the money already taken are the gym-cancel answer
          ask=("worth", "good idea", "bad idea", "should i", "shall i", "waste of money",
               "keep paying"),
          avoid=("how do i cancel", "keeps charging", "still charging", "after i cancelled",
                 "after i quit", "refund", "closed", "went bust", "shut down", "direct debit")),
    entry("insurance-refused", (("insurance", "insurer", "policy"),
                                ("refused", "rejected", "won't pay", "wont pay", "dispute",
                                 "complain", "claim refused", "not covered", "isn't covered", "isnt covered", "declined")),
          "Ask for the refusal in writing with the policy clause they're relying on, then complain "
          "formally and quote the wording back. After 8 weeks, or a final response, the free "
          "Financial Ombudsman Service can review it, and its decision binds the insurer."),
    entry("consumer-parking-ticket", (("parking ticket", "pcn", "penalty charge", "parking fine", "clamped"),
                             ("appeal", "challenge", "dispute", "wrong", "unfair", "pay", "paid",
                              "contest")),
          "Don't ignore a parking ticket: an informal challenge inside 14 days keeps the 50% "
          "discount open, and paying in that window gets it. Photos of the sign, the bay and the "
          "ticket you bought decide it, so send them on the council's own form, never through a "
          "paid appeals firm. If that is refused, make a formal representation within 28 days of "
          "the Notice to Owner; the independent tribunal named on the notice is then free and "
          "cancels plenty of these.",
          # a "parking charge notice" is the private car park's invoice, a different system with
          # a different appeal body: that answer owns it
          avoid=("parking charge notice", "parkingeye", "apcoa", "popla", "private car park",
                 "private parking", "anpr", "supermarket car park", "retail park")),
    entry("builder-unfinished", (("builder", "plumber", "electrician", "tradesman", "roofer",
                                  "decorator", "workman"),
                                 ("bad", "shoddy", "unfinished", "won't come back", "wont come back",
                                  "never came back", "paid", "deposit", "didn't finish",
                                  "didnt finish", "half done", "half finished", "walked off",
                                  "stopped turning up", "left it",
                                  # "the builder started the job and left" says the trader is
                                  # gone in the plainest way there is, and without these shapes
                                  # the line matched no complaint at all and got a follow-up
                                  # question about the first week of a job nobody is doing.
                                  "and left", "left the job", "left halfway", "left halfway through",
                                  "left it half", "walked out", "walked away", "downed tools",
                                  "halfway through", "partway through", "started the job",
                                  # "how do i complain about a builder" names no fault yet: the
                                  # complaint is the problem, and this is who answers it.
                                  "complain", "complaint", "report them")),
          "Put the complaint in writing, list what's wrong and ask for it fixed within 14 days "
          "before paying anything more. If they don't, report them to Trading Standards through "
          "Citizens Advice and use the small claims court for what you've lost.",
          # "can i fix that myself or do i need a plumber" wants help with the job, not a claim
          # against a trader, so this answers only lines that ask about the botched work.
          ask=("complain", "complaint", "refund", "money back", "court", "unfinished",
               "never came back", "won't come back", "wont come back", "walked off", "rights",
               "didn't finish", "didnt finish", "took my money", "half done", "half finished",
               "stopped turning up", "what can i do", "shoddy", "bad job", "botched",
               "bodged", "cowboy", "and left", "left the job", "left halfway", "walked out",
               "walked away", "downed tools", "halfway through", "partway through",
               "started the job", "half finished", "never finished"),
          # a deposit that vanished before any work is the deposit answer, not this one
          avoid=("never came back", "vanished", "did a runner", "never started", "never turned up",
                 "how much", "should i pay", "how big")),
    entry("builder-deposit", (("deposit", "paid up front", "paid a deposit", "took my money",
                               "took the money", "paid him", "paid them", "advance"),
                              ("builder", "plumber", "roofer", "electrician", "decorator",
                               "tradesman", "workman", "repair man", "repairman", "gas engineer",
                               "boiler man", "never came back", "vanished",
                               "disappeared", "never started", "never turned up", "did a runner")),
          "Never pay the balance: ask in writing for the deposit back within 14 days, saying what "
          "was agreed and what was not done. If it is not back, report it to Trading Standards "
          "through Citizens Advice and start a Money Claims Online case, which is the same route as "
          "any unpaid debt and costs from about £35. A deposit paid by card over £100 can also be "
          "claimed from the card company.",
          # the deposit has to be gone before this answers: "how much deposit should i pay"
          # is the quotes question, and the question words are too common to be an avoid
          ask=("never came", "never started", "never turned up", "vanished", "disappeared",
               "did a runner", "never did", "paid him", "paid them", "refund", "money back",
               "court", "lost my", "took my", "took the", "wont give", "won't give", "keeps my"),
          # a builder who came and did it badly is the unfinished answer, not this one
          avoid=("half done", "half finished", "left it", "unfinished", "did a bad job",
                 "shoddy", "snagging", "not fixed", "still leaking",
                 # a seller on a marketplace who takes the money is the PayPal dispute, not a
                 # tradesman who never came back
                 "paypal", "ebay", "vinted", "depop", "marketplace", "seller", "shop", "store"),
          bias=1),
    entry("car-repair-bill", (("garage", "mechanic", "car repair", "mot", "servicing", "dealer",
                               "workshop"),
                              ("didnt authorise", "didn't authorise", "did not authorise",
                               "unauthorised", "without asking", "didnt agree", "didn't agree",
                               "did not agree", "never agreed", "extra work", "overcharged",
                               "more than the quote", "made it worse", "stripped", "bill",
                               "charged me", "wont give", "won't give", "holding my car",
                               "faulty repair", "again")),
          "A garage has to give you a written estimate and get your agreement before the work, and "
          "ask again before any extra job. If it did work you did not agree to, you only owe the "
          "price you agreed: write and say which jobs you authorised, ask for the bill to be "
          "corrected and for the old parts back. If they will not release the car, the Motor "
          "Ombudsman and Trading Standards through Citizens Advice can take it.",

          ask=("can", "do", "should", "must", "is", "are", "my", "they", "the", "how", "what"),
          # a fault to diagnose, a price to weigh and an MOT fail sheet are other answers
          avoid=("how much", "how do i check", "should i buy", "worth", "noise", "warning light",
                 "fail sheet", "advisory", "what does it mean"),
          # lifeadmin's tradesperson-complaint reads "overcharged" from the other side, and this
          # is the garage's bill, so the estimate rule stays with the garage
          bias=2),
    entry("find-a-tradesman", (("plumber", "electrician", "builder", "tradesman", "roofer",
                                "decorator", "handyman", "locksmith", "someone to fix",
                                "someone to do", "gas engineer", "boiler engineer",
                                # the register's own name for the trade, which people use instead
                                # of "gas engineer": "where do i find a gas safe engineer" was the
                                # gas shut-off lever on main, because the line says "gas" and
                                # "where" and nothing named the trade this row knows
                                "gas safe engineer", "gas safe registered", "gas safety engineer",
                                "heating engineer"),
                               ("find a good", "find a reliable", "good one", "how do i find",
                                "how do i choose", "how do i pick", "which one", "who can i trust",
                                "recommend", "recommended", "trustworthy", "reliable",
                                # a "where" in front of the trade is the same question as the "how
                                # do i find" form, and it lost to the gas shut-off row for want of
                                # it: "where do i find a gas safe engineer" got the meter lever
                                "where do i find", "where can i find", "where to find",
                                "find a", "find me a", "find someone",
                                "not a cowboy", "avoid a cowboy", "get someone in",
                                "should i use", "should i hire", "can i trust", "to use",
                                "a good one",
                                # "anyone know a good plumber" and "i need a good electrician" are
                                # the same question in the words people use for it, and both were
                                # answered elsewhere: the first with "a plumber will spot it in
                                # minutes", the second with "Worth doing. What would you like help
                                # with first?"
                                "know a good", "know of a good", "know any good",
                                "anyone know", "need a good", "want a good",
                                "looking for a good", "after a good", "in need of a good",
                                "can anyone recommend",
                                # the adjective on its own, because the understanding reads
                                # "i'm looking for ..." as a way of asking and drops it: what is
                                # left of "looking for a good roofer" is "good roofer". The trade
                                # word is still needed in the first half, so a bare "good" cannot
                                # reach this row; the praise that mentions a trade is fenced below.
                                "good")),
          "Ask two people who have had work done for a name, then check the trade body register "
          "before you call: Gas Safe for anything on gas, NICEIC or NAPIT for electrics, and the "
          "Federation of Master Builders for a bigger job. Get three written quotes that name a "
          "price, a start date and what is included, ask for the public liability insurance "
          "certificate, and pay a small deposit on a card rather than cash up front.",
          bias=2,
          # the ask gate wants a word that makes the line a question, and the words people
          # actually use for this one - "anyone know a good plumber", "looking for a good
          # roofer", "need a good electrician" - have none of the original ones in them.
          ask=("how", "what", "where", "who", "can", "should", "is", "any", "my", "i",
               "anyone", "anybody", "know", "knows", "looking", "need", "needs", "want",
               "wanted", "recommend"),
          # a drip, a fault and a finished job gone wrong are other answers
          avoid=("leaking", "leak", "dripping", "boiler is", "no hot water", "no heating",
                 "went wrong", "did a bad job", "half done", "unfinished", "noise", "smell",
                 "quote higher", "overcharged",
                 # the praise and the complaint are about the job, not about how to pick one
                 "did a good job", "done a good job", "good job", "bad job",
                 # "my plumber is good" is a compliment, and a compliment wants a listener
                 "is good", "was good", "so good", "very good", "really good", "brilliant")),
    # "how do i check an engineer is gas safe" reached the oven-dial card on main, and "is my
    # plumber registered" reached the shrug. The check itself is one lookup, and it is the answer
    # whether the trade is gas, electrics or a builder, so the row asks about the checking rather
    # than about finding somebody.
    entry("check-a-trade", (("gas safe", "gas safe register", "gas safe card", "gas safe engineer",
                            "gas safety", "gas engineer", "gas safe registered",
                            "registered engineer", "licence card", "license card",
                            "registration number", "registration",
                            # electrics and building have their own registers, and the check is
                            # the same lookup by a different name
                            "niceic", "napit", "part p", "competent person scheme"),
                           ("check", "checked", "checking", "how do i know", "how can i tell",
                            "is he", "is she", "is my", "are they", "genuine", "real",
                            "qualified", "qualification", "legit", "legitimate", "fake",
                            "card", "number", "verify", "registered", "register",
                            "how do i find out", "can i trust")),
          "Ask to see their registration card before they start and check the number on the "
          "register yourself: Gas Safe for anything on gas, NICEIC or NAPIT for electrics, and the "
          "competent person scheme for a builder. On the Gas Safe card the photo and the licence "
          "number should match the person in front of you, and the card lists which work they are "
          "registered for - boilers, cookers and fires are separate tickets. A gas certificate "
          "signed by somebody who is not on the register is not worth the paper.",
          bias=2,
          # a service, a price and a fault are the other rows: this one is only about proving who
          # the person is before the work starts
          avoid=("how much", "price", "cost", "quote", "service my", "service the",
                 "serviced", "how often", "certificate", "boiler is", "leaking", "smell",
                 "no hot water", "no heating", "did a bad job", "went wrong", "overcharged",
                 "recommend", "recommended",
                 # the check the landlord owes and the record it leaves are the certificate's
                 # question, not this one: "can i do the gas safety check myself" is about the
                 # duty, and this row answers who the person in front of you is
                 "gas safety check", "gas check", "gas safety record", "certificate")),
    entry("auto-renewal", (("renewed", "renewal", "auto renewed", "automatically renewed",
                            "rolled over", "rolled into", "subscription", "annual policy",
                            "charged again", "took the money again", "insurance", "policy",
                            "my cover", "membership",
                            # a free trial that charges at the end is the same money taken
                            # without a clear yes: "i was signed up for a trial and charged"
                            "free trial", "trial period", "a trial", "the trial",
                            "signed up for a trial", "signed up to a trial"),
                           ("without telling", "without asking", "didnt agree", "didn't agree",
                            "did not agree", "never agreed", "no warning", "didnt tell",
                            "didn't tell", "not told", "never told", "didnt know", "didn't know",
                            "auto renewed", "automatically renewed", "renewed itself",
                            "surprised", "unexpected", "out of the blue", "cant afford",
                            "can't afford", "want it back", "cancel", "refund",
                            "charge", "charged", "charging", "money back", "took money",
                            "still charged", "still charging", "kept charging", "keeps charging",
                            "still taking", "took it again", "took the money",
                            "cancelled it", "cancelled my")),
          _renewed_reply,
          # lifeadmin's car-insurance-renewal names a car policy from the price side: a renewal
          # nobody told you about is this question whatever the cover was for
          bias=3,
          ask=("my", "i", "they", "it", "can", "do", "should", "how", "what"),
          avoid=("gym", "phone contract", "broadband", "energy", "car insurance", "how do i cancel",
                 "when does my", "passport", "visa", "licence", "mot", "car tax", "library",
                 "went up", "gone up", "has gone up", "increased", "increase", "price hike",
                 "more than last year", "too expensive", "cheaper elsewhere")),
    entry("dentist-complaint", (("dentist", "dental", "dentistry", "orthodontist",
                                 "hygienist", "practice manager", "my filling", "my crown",
                                 "my tooth", "my teeth", "treatment plan", "braces"),
                                ("complain", "complaint", "complain about", "botched",
                                 "went wrong", "made it worse", "refund", "money back",
                                 "charge", "charged", "bill", "rude",
                                 # Pain is not a complaint by itself: only pain put on
                                 # somebody's work is. "my teeth hurt", "my filling hurts" and
                                 # "my braces hurt" are the mouth's own trouble and belong to
                                 # the dental rows, which is why the bare pain words are not here
                                 # and these frames take their place.
                                 "hurt me", "hurts me", "hurting me", "hurt my", "hurts my",
                                 "in pain after", "left me in pain", "hurt after the",
                                 "hurts after the", "painful when he", "painful when she",
                                 "failed", "not happy", "unhappy",
                                 # a crown or a filling that failed soon after the work is a redo,
                                 # and that is the complaint: the phrase carries the "after", so
                                 # a filling that has simply come out stays with the dental card
                                 "fell out after", "came out after", "came off after",
                                 "broke after", "failed after", "went wrong after",
                                 # "loose", "hurts", "came out" and "broke" were here, and they
                                 # are symptoms, not grievances: with bias 4 they took "my tooth
                                 # feels loose" and "my filling came out" away from the dental
                                 # cards that answer them. A complaint says what went wrong with
                                 # the treatment ("botched", "refund", "charged"), not what the
                                 # tooth is doing now.
                                 # work that came away or was done wrong: "my crown fell out
                                 # after a week" is a redo, not a tooth to look after, and the
                                 # tooth the dentist chipped is damage they did
                                 "fell out after", "came out after", "came off after",
                                 "broke after", "wrong crown", "wrong filling", "wrong tooth",
                                 "wrong shade", "put in the wrong", "chipped my tooth",
                                 "damaged my",
                                 # the bill, not the price list: "i was overcharged at the
                                 # dentist" was the private-fees answer
                                 "overcharged", "overcharged me", "charged more",
                                 "charged too much", "more than quoted", "quoted me",
                                 "quote was", "bill was higher", "didnt agree to",
                                 # the dentist did it and it hurt: "my dentist hurt my tooth"
                                 # is a grievance about the work, while "it hurts when i bite"
                                 # is the tooth's own state and belongs to the dental cards
                                 "hurt", "hurts", "painful", "agony")),
          "Complain to the practice manager first, in writing, and ask for the treatment plan, the "
          "notes and an itemised invoice. NHS treatment goes on to the NHS complaints team at your "
          "local integrated care board; private treatment goes free to the Dental Complaints "
          "Service, which can refund fees within 12 months. Work you did not agree to is not owed, "
          "so say so in the same letter, and photograph the tooth before anyone touches it.",

          bias=4,
          ask=("my", "i", "they", "the", "can", "do", "should", "how", "what"),
          # A letter is for work that was done wrong, so the row answers only when the line
          # says something went wrong with the treatment. The bare pain words are back in the
          # key (they are how "my dentist hurt my tooth" is put), which means the same key
          # also reaches "my teeth hurt" and "my filling hurts" - a tooth that needs seeing,
          # not a grievance. A list of those forms is never complete ("gums hurt", "my crown
          # is sore"), so the test is on the whole line instead.
          guard=_dentist_grievance,
          avoid=("toothache", "tooth hurts", "how much do braces", "how much does a filling",
                 "how often should i", "vet", "nurse", "doctor", "gp", "hospital",
                 # "charge" is in the key because a bill is what a complaint is about, and it
                 # took the price list with it: "how much does a dentist charge" and "what do
                 # dentists charge" were sent the complaints letter when the person wanted to
                 # know what a check-up costs before they book. The price ask is the cost rows'
                 # question, so it stands this row down.
                 "how much does a dentist", "how much does the dentist", "how much do dentists",
                 "how much is a dentist", "what do dentists charge", "what does a dentist charge",
                 "how much do you charge", "price list", "what are the fees", "private fees",
                 "how much for a",
                 "registration", "register with", "find a dentist", "nhs dentist taking",
                 # A state of the tooth is not a complaint about the work: the key holds
                 # "my tooth" and "my crown" beside "loose", "fell out", "came out" and
                 # "broke", so "my crown is loose" and "my tooth is loose" got the complaints
                 # letter instead of the dentist-this-week card. What to do about the tooth
                 # is the dental rows' answer; a letter is for work that was done wrong.
                 "crown is loose", "crown came off", "crown fell off", "crown come off",
                 "tooth is loose", "tooth has come loose", "teeth are loose", "teeth is loose",
                 "hole where",
                 # The pain of your own mouth is not a complaint about anyone's work either,
                 # and neither is work that has come away: the key holds "my teeth", "my
                 # tooth" and "my filling" beside "hurt", "hurts", "pain" and "fell out",
                 # so "my teeth hurt" and "my filling hurts" got the complaints letter while
                 # "my tooth hurts" got the dentist. What to do about the mouth is the dental
                 # rows' answer, and a letter is for work that was done wrong. The tooth rows
                 # already disown "tooth hurts"; this is the same veto for the plural and for
                 # the filling, and for the state of it having come out.
                 "filling fell out", "filling has fallen out",
                 "filling came out", "filling came loose", "filling came away",
                 "filling is loose", "filling feels loose", "filling has come out",
                 "filling come out", "filling is chipped", "filling chipped",
                 # A tooth that has just come out is a wound with its own answer, and the key
                 # here holds "my tooth", "my teeth" and "hurt": "the gap where my tooth was
                 # hurts with cold water" got the letter to the practice manager.
                 #
                 # A tooth that twinges is not a complaint either: "my filling hurts when i
                 # drink something cold" is the sensitive-teeth answer or the extraction one,
                 # and the letter is for work that was done wrong.
                 "sensitive", "sensitive teeth", "hurts when i", "hurts when", "hurts if",
                 "cold drink", "cold drinks", "something cold", "anything cold", "cold water",
                 "hot drink", "hot drinks", "biting on", "chewing on", "twinge", "twinges",
                 # braces hurt on purpose, and the soreness card that says how long it
                 # lasts is the answer: "my braces hurt" is not a grievance about the
                 # treatment
                 "braces hurt", "braces are sore", "braces ache", "braces are aching",
                 "braces were tightened", "after each tighten", "after tightening",
                 "got my braces", "braces went on", "braces put on"
                 ) + TOOTH_OUT),
    entry("renewal-rise", (("renewal", "renewed", "renewing", "auto renewal", "auto-renewal",
                            "my insurance", "my policy", "my cover", "my premium",
                            "home insurance", "car insurance", "pet insurance", "contents"),
                           ("went up", "gone up", "has gone up", "increased", "increase",
                            "price hike", "more than last year", "too expensive", "expensive",
                            "cheaper elsewhere", "double", "doubled", "40 percent", "50 percent",
                            "by a third", "rise", "risen", "hiked", "jumped")),
          "A renewal is a new quote, not a bill, so start three weeks early and compare two or "
          "three others: the same cover is often \u00a3100 to \u00a3200 cheaper elsewhere. For home and motor "
          "insurance the renewal price cannot be higher than a new customer would pay for the same "
          "cover, so say so in writing if it is. Ring to cancel before the renewal date, and ask "
          "for the annual price rather than monthly.",

          ask=("my", "i", "the", "it", "can", "do", "should", "how", "what", "why"),
          avoid=("gym", "phone contract", "broadband", "energy bill", "energy prices",
                 "switch", "landlord", "tenancy", "deposit", "passport", "visa", "licence",
                 "library", "season ticket", "subscription",
                 # "i want to cancel my car insurance because its too expensive" has already
                 # decided; the steps to leave the policy are the answer, and this one is the
                 # should-i-switch answer
                 "want to cancel", "i want to cancel", "can i cancel", "how do i cancel",
                 "cancel my car insurance", "cancel my insurance", "cancel my policy"),
          # lifeadmin's car-insurance-renewal answers the car policy from the price side, and a
          # renewal that went up is the comparison question whatever the cover is for
          bias=2),
    entry("extra-item-sent", (("came twice", "came twice over", "sent twice", "sent me two",
                               "sent me three", "sent two", "an extra", "extra one", "double order",
                               "duplicate order", "didnt order", "didn't order", "never ordered",
                               "did not order", "unsolicited", "more than i ordered",
                               "two of them", "two arrived", "two of the same",
                               "same thing twice", "twice over",
                               # "they sent me a bill for something i never ordered": the bill
                               # came with the thing nobody asked for, and it was the bill words
                               # that kept this row away
                               "never asked for", "didnt ask for", "didn't ask for",
                               "did not ask for", "never signed up", "didnt sign up",
                               "didn't sign up", "never agreed to", "didnt agree to",
                               "didn't agree to", "never subscribed", "didnt subscribe",
                               "didn't subscribe", "not mine", "isnt mine", "wasnt mine",
                               "wasn't mine", "never bought"),
                              ("parcel", "delivery", "delivered", "order", "ordered", "item",
                               "came", "sent", "arrived", "pay", "keep", "return", "charge",
                               "charged", "invoiced", "two of the same", "same thing twice",
                               "bill", "billed", "invoice", "money", "payment", "card")),
          "Something you did not order is unsolicited: you do not have to pay for it and you do not "
          "have to send it back, and a bill for it is not owed. Do tell them in writing, keep the "
          "parcel unopened where you can, and say you will keep it unless they collect it at their "
          "own cost within a date you set - that is decent and it also gives you a record if they "
          "later try to charge you.",
          # a charge on a bill for something you did not have is the bill entry's: this one is
          # about goods that turned up twice
          avoid=("charged twice", "double charged", "duplicate charge", "two payments",
                 "hotel", "minibar", "mini bar", "room service", "restaurant", "meal",
                 "taxi", "haircut", "builder", "garage", "vet", "landlord",
                 # a bill with no parcel and no goods word is a bill question: this row is about
                 # the thing that turned up, so it needs a goods or money word from the line
                 "energy bill", "gas bill", "electricity bill", "water bill", "council tax",
                 # "my manager keeps giving me the late shift and i never asked for it" is a
                 # rota question, and "never asked for" belongs to the work rows here.
                 "manager", "boss", "shifts", "shift", "rota", "overtime", "employer",
                 "supervisor", "colleague", "hr", "night shift", "late shift"),
          bias=2),
    entry("delivery-promise", (("in stock", "in stock when", "delivered by", "delivery date",
                                "delivery day", "delivery slot", "supposed to be delivered",
                                "supposed to arrive", "promised", "estimated delivery",
                                "when will it arrive", "when will my order", "when will my parcel",
                                "said it would arrive", "said it would be delivered",
                                "said it would come", "coming tomorrow", "coming today",
                                "should arrive", "on time",
                                "wont deliver", "won't deliver", "refuse to deliver",
                                "refused to deliver", "will not deliver", "not delivering",
                                "stopped delivering"),
                               ("stock", "deliver", "delivered", "delivery", "arrive", "parcel",
                                "package", "order", "courier", "date", "friday", "monday",
                                "tuesday", "wednesday", "thursday", "saturday", "sunday",
                                "yesterday", "today", "tomorrow", "next week", "this week",
                                "two weeks", "shop")),
          "A date they gave you is part of the deal: if it slips, ask in writing for the new date "
          "and say you will cancel if that one is missed, and once it passes, or 30 days if there "
          "never was one, you can cancel for a full refund including delivery. Keep the message "
          "that promised the day, and a thing sold as in stock when it was not is a misleading "
          "claim for Trading Standards.",

          guard=_stock_is_not_a_parcel,
          avoid=("damaged", "broken", "smashed", "lost", "stolen", "wrong address", "left in",
                 "left with", "already arrived", "has arrived", "was delivered but",
                 # people are not parcels: "the in laws come tomorrow" reached this row on
                 # "come" + "tomorrow" and was told about cancelling for a full refund. The
                 # delivery lines name a parcel, an order or a thing; these name who is coming.
                 # A relation or a way of staying is the word that makes a line domestic.
                 # The person words a delivery line uses too - "someone", "people",
                 # "everyone", "friends", "children", "the kids" - are not here: @civil-bear
                 # measured "the courier said someone would come tomorrow" losing the
                 # promise-date card to them on an earlier head, and a bare day phrase is
                 # what a promise date is, so the day stays out of this fence as well.
                 "in laws", "in-laws", "inlaw", "inlaws", "mother in law", "father in law",
                 "parents", "mum", "dad", "family", "relatives", "guests", "visitors",
                 "to stay", "stay with", "staying", "come to dinner", "coming for dinner",
                 "come for dinner", "for dinner", "for lunch", "visiting",
                 # The person words only as domestic phrases: "my friends are coming tomorrow"
                 # and "someone is coming to stay" read as a visit, while the bare words do not,
                 # because "the courier said someone would come tomorrow" is the same bare
                 # word and a promise date.
                 "friends coming", "friends are coming", "friends staying",
                 "the kids are coming", "kids are coming", "children coming",
                 "children are coming", "someone coming", "someone is coming",
                 "people coming", "people are coming", "everyone coming"),
          bias=1),
    entry("late-delivery", (("delivery", "parcel", "package", "order", "courier", "next day",
                             "delivery date", "arrived late", "came late"),
                            ("late", "took ages", "still waiting", "never turned up",
                             "missed the date", "after the date", "days late", "weeks late",
                             "compensation", "goodwill", "guaranteed", "next day delivery",
                             # the promise they made, said as a number of days
                             "said 3 days", "said three days", "said 2 days", "said two days",
                             "said a week", "said next day", "said it would be",
                             "been a week", "been two weeks", "been three weeks", "been a month",
                             "its been a week", "it's been a week", "took a week",
                             "took two weeks",
                             # the promise was a day, and the day went by
                             "named day", "named delivery", "a named", "paid extra",
                             "didnt come", "didn't come", "not come", "no sign of it",
                             "no show", "booked a slot",
                             "time slot", "delivery slot")),
          "A late parcel is a broken promise, not a broken item: if it has not arrived by the date "
          "you agreed, or 30 days if you agreed none, you can cancel for a full refund, but money "
          "for the delay itself comes only with a guaranteed service such as next-day delivery. "
          "Claim in writing with the order number and the date it should have come, and ask for "
          "the delivery charge back.",
          bias=1,
          ask=("my", "i", "it", "its", "they", "we", "the", "can", "do", "should", "how",
               "what", "is"),
          avoid=("damaged", "broken", "smashed", "lost my job", "interview", "wedding", "funeral")),
    entry("care-agency", (("care agency", "home care", "care company", "care visits", "carer",
                           "carers", "domiciliary", "care provider"),
                          ("cancelled", "didnt turn up", "didn't turn up", "no show", "charged me",
                           "billed", "not given", "missed", "invoice", "refused", "hours",
                           "wont refund", "won't refund", "still charging")),
          "You pay for the care actually given: a cancelled or missed visit comes off the invoice, "
          "and the agency has to show the visit log and timesheet it is billing from. Ask for both "
          "in writing, name the visits you were charged for and say you dispute that part of the "
          "bill. Council-funded care goes to the council's commissioning team; a private agency "
          "that will not credit you is a complaint to the Care Quality Commission.",

          bias=1,
          ask=("my", "the", "i", "we", "they", "charged", "billed", "cancelled"),
          avoid=("care home", "career", "i dont care", "i don't care", "how do i care for",
                 "app", "subscription")),
    entry("care-home-fees", (("care home", "nursing home", "residential home", "care home fees",
                              "my mum's care", "my dad's care"),
                             ("fees", "fee", "cost", "costs", "going up", "gone up", "increase",
                              "risen", "went up", "rise", "bill", "charged", "top up",
                              "top-up", "afford", "paying")),
          'Ask for the increase in writing, with the date it starts and the reason: a home cannot '
          'put the price up whenever it likes. If the council pays part of it, any top-up has to be '
          'agreed by you in writing and is voluntary, so ask the council to arrange your care at '
          "its own rate instead. Complain to the home first and then the council's adult social "
          'care team, and ask about a deferred payment agreement so the house is not sold in a '
          'hurry.',
          bias=1,
          ask=("my", "the", "i", "we", "mum", "dad", "mother", "father"),
          avoid=("how do i choose", "which care home", "should i put", "how much does a care home",
                 "is a care home", "dementia", "career", "home care", "carer")),
    entry("care-home-cost", (("care home", "nursing home", "residential home", "care home fees",
                              "a care home"),
                             ("how much", "cost", "costs", "price", "per week", "a week",
                              "a year", "average", "afford", "expensive", "fees", "fee")),
          "A residential home is about \u00a3800 a week and a nursing home \u00a31,100 to \u00a31,400, so \u00a342,000 "
          "to \u00a373,000 a year, and it swings a lot by area. The council only helps once savings and "
          "property are under \u00a323,250, so ask for a financial assessment in writing, and a deferred "
          "payment agreement means the house is not sold while you are alive. If the need is health "
          "rather than social care, ask the GP about NHS continuing healthcare.",

          bias=2,
          ask=("how much", "cost", "price", "afford", "expensive", "average", "fees",
               "fee", "a week", "per week", "a year", "much"),
          avoid=("how do i choose", "which care home", "should i put", "is a care home",
                 "good", "dementia", "career", "home care", "carer", "nhs", "funding",
                 "going up", "gone up", "increase", "risen", "went up", "top up")),
    # a callout fee buys the visit, not the fix: charging for work nobody did is what the
    # trader can never do, and it is not the quote entry's fight
    entry("callout-charge", (("callout", "call out", "call-out", "engineer", "plumber",
                              "electrician", "tradesman", "locksmith", "drain", "pest control",
                              "appliance", "washing machine", "boiler", "oven", "fridge",
                              "inspection", "survey", "callout fee", "call out fee",
                              # the trade as people name him: "the boiler man charged me for a
                              # visit and didnt fix it" is the fee row, and the phrase carries
                              # the weight that beats the shop card's plain "refund"
                              "boiler man", "boiler engineer", "gas engineer", "boiler service",
                              "came out to look", "came out and looked", "charged me for a visit",
                              "charged for a visit", "charged me for coming out"),
                             ("nothing was done", "nothing done", "didnt do anything",
                              "didn't do anything", "did nothing", "no work", "didnt fix",
                              "didn't fix", "couldnt fix", "could not fix", "just looked",
                              "only looked", "charged for", "wont refund", "won't refund",
                              # the money of the visit, in the shapes people write it in: the
                              # line that names the fee is about the fee whichever way round the
                              # words come, and the plain "refund" is the shop's own key
                              "refund the callout", "refund the fee", "refund the visit",
                              "refund on the callout", "refund of the callout", "refund my callout",
                              "refund on the fee", "refund of the fee", "refund the callout fee",
                              "refund of the callout fee", "refund on the callout fee",
                              "refund on the visit", "refund of the visit",
                              "refund on the charge", "refund of the charge",
                              "callout fee refunded", "callout refunded", "fee refunded",
                              "visit refunded", "charge refunded",
                              "money back on the callout", "money back for the callout",
                              # and the plain question about the fee, with no refund in it: "can a
                              # trader charge a callout fee" and "does a callout fee cover the
                              # repair" are what this card answers, and they were left with
                              # nothing at all while the key only listened for a dispute
                              "charge a callout", "charge for a callout", "charge a fee",
                              "charge for the visit", "charge a visit", "callout fee cover",
                              "callout fee include", "callout fee count", "can they charge",
                              "can a trader charge", "can a plumber charge",
                              "can an engineer charge",
                              # "a callout fee" as well as "the": a key phrase that pins the
                              # article only reads half the ways people write it
                              "refund on a callout", "refund of a callout",
                              "refund for a callout", "refund on a callout fee",
                              "refund of a callout fee", "refund for a callout fee",
                              "money back on a callout", "money back for a callout",
                              "the callout fee back", "the fee back", "the visit back",
                              "callout fee refundable", "fee refundable",
                              "visit refundable", "charge refundable",
                              "cover the repair", "cover the visit", "cover the callout",
                              "cover a repair", "covers the visit", "includes the repair")),
          "A callout fee pays for the visit, and a trader can only charge for what you agreed and "
          "what they did: if you were billed for a repair nobody made, or a second visit for the "
          "same fault, ask for that part back in writing and say what you agreed before they came. "
          "Keep the invoice and the text that set the price. If they will not move, a card "
          "chargeback, and Money Claims Online from about \u00a335.",

          avoid=("garage", "car", "mot", "van", "tyre", "how much is a callout",
                 "how much should", "should i", "is it worth", "quote", "estimate",
                 "how do i find", "find a plumber", "find an electrician",
                 # a policy that may pay is the insurance answer, but "does a callout fee cover
                 # the repair" is this card's own question, so the bare "cover" went
                 "covered by", "covered under", "cover it", "cover me", "cover this",
                 "cover the cost",
                 "insurance cover", "home cover", "warranty",
                 "insurance", "boiler is broken", "boiler not working", "my boiler",
                 "energy", "broadband", "leak"),
          bias=2),
    entry("withheld-work", (("photographer", "wedding photos", "photos", "photographs", "survey",
                             "drawings", "plans", "report", "certificate", "my files", "my footage"),
                            ("wont give", "won't give", "never got", "never received", "not given",
                             "refuses to send", "refuses to give", "hasnt sent", "hasn't sent",
                             "holding my", "withholding", "keeps my")),
          "What you paid for is yours once the work is done, so put the request in writing and give "
          "them 14 days: name what you are owed, the date and what you paid. A photographer or a "
          "designer cannot keep the files as security for a bill they never sent you, and a surveyor "
          "or an architect has to hand over the report or drawings. If nothing comes, a letter before "
          "claim and Money Claims Online cost from about £35 and settle most of these.",
          bias=1,
          ask=("i", "my", "the", "we", "paid", "i paid"),
          avoid=("deposit back", "passport", "driving licence", "birth certificate", "car",
                 "garage", "insurance", "landlord", "landlady", "claim", "refund")),
    entry("wrong-item", (("wrong item", "wrong thing", "wrong colour", "wrong color",
                          "sent me the wrong colour", "sent me the wrong color",
                          "sent the wrong colour", "sent the wrong color",
                          "delivered the wrong colour", "wrong shade", "wrong colour one",
                          "wrong model", "wrong product", "sent me the wrong", "not what i ordered",
                          "not what i asked for", "instead of the", "instead of a",
                          "instead of my", "sent the wrong size"),
                         ("refund", "replacement", "money back", "send it back", "order", "delivered",
                          "arrived", "return", "item", "sent", "got", "came", "parcel")),
          "The wrong thing is not what you bought, so the shop owes you what you ordered or your "
          "money back, and it pays the return postage: ask in writing for the right one to be sent "
          "with a collection of the wrong one, and keep the packing slip. If they will not, that is a "
          "card chargeback with the order and the photo of the label.",
          bias=1,
          ask=("my", "the", "i", "they", "sent", "arrived"),
          avoid=("ordered the wrong size", "i ordered the wrong", "wrong size for me",
                 "getting the wrong size", "wrong person", "wrong number", "wrong address",
                 "wrong password", "i sent the wrong", "instead of a repair", "refund instead",
                 "wrong account", "ebay", "paypal")),
    # A box that comes with one of the two in it is not a wrong item and not a lost parcel: the
    # second one is owed. "i ordered 2 and only got 1" was an echo.
    entry("short-order", (("ordered two", "ordered 2", "ordered three", "only got one",
                           "only got 1", "only one arrived", "only one came", "one is missing",
                           "one was missing", "two missing", "missing from my order",
                           "missing from the box", "missing from the parcel", "item missing",
                           "items missing", "half my order", "short delivery", "part of my order",
                           # the box that came with nothing in it: "the box was empty when it
                           # arrived", "there was nothing in the parcel" were acknowledgements
                           "box was empty", "box was empty when", "parcel was empty",
                           "package was empty", "empty box", "nothing in the box",
                           "nothing in the parcel", "nothing inside", "was empty when"),
                          ("order", "parcel", "box", "delivery", "arrived", "came", "sent",
                           "got", "paid for", "shop", "seller", "refund", "send")),
          "You paid for the lot, so the rest is still owed: photograph the box and the packing "
          "slip, then write and say exactly what is missing and ask for it to be sent or for that "
          "part refunded. If they will not, ask the card provider to charge back the missing "
          "amount, with the order email as proof.",
          ask=("my", "the", "i", "we", "got", "arrived"),
          # a parcel that never came, a wrong item and a damaged one are their own answers
          avoid=("never arrived", "never came", "nothing arrived", "wrong item", "wrong size",
                 "damaged", "broken", "faulty", "return postage")),
    entry("return-costs", (("post it back", "post back", "send it back", "sent it back",
                            "send a faulty", "send back", "sending back", "item back",
                            "send a faulty item back",
                            "return postage", "postage", "returns postage", "returns label",
                            "prepaid label", "return it", "returns", "returning it",
                            "restocking fee", "restocking", "return fee", "return fees",
                            "handling fee", "cancellation fee", "collection fee",
                            "who pays for the return", "cost of returning", "return cost"),
                           ("own cost", "my own cost", "at my cost", "who pays", "pay for it",
                            "pay for the", "me to pay", "have to pay", "they want me",
                            "they told me", "charged me", "wont pay", "won't pay", "refund",
                            "fee", "fees", "cost", "costs", "charged")),
          _return_costs_reply,
          bias=1,
          ask=("my", "i", "they", "the", "it", "can", "do", "should", "who", "how"),
          # how long a refund takes, and a refund that has not come, are the timing entry's: this
          # one answers who pays to send it back and what fee they can take off.
          avoid=("is late", "late refund", "still no refund", "still waiting", "been waiting",
                 "how long", "overdue", "weeks ago", "not arrived yet", "hasnt come back",
                 "hasn't come back",
                 "parcel never", "never arrived", "hasnt arrived", "hasn't arrived",
                 "not arrived", "flight", "hotel", "tenancy", "deposit", "gym", "insurance",
                 "warranty", "car", "vets", "vet bill", "school", "council")),
    # The mind-changing words are the reason for a return, not the way the thing was bought, and
    # they were in the channel's key: "i changed my mind about the job offer", "about university"
    # and "about going to the wedding" all got the 14-day returns card. The channel is what this
    # row answers, so the channel is all that is left in this half of the key.
    entry("change-of-mind", (("bought online", "ordered online", "bought it online", "online",
                              "website", "on the internet", "catalogue", "amazon",
                              "by post", "mail order", "ordered it", "i ordered", "we ordered",
                              "delivered", "courier", "click and collect"),
                             ("changed my mind", "dont want it", "don't want it", "dont like it",
                              "don't like it", "not what i expected", "decided against",
                              "send it back", "return it", "return", "refund", "exchange",
                              "keep it", "send back", "doesnt suit me", "doesn't suit me",
                              "doesnt fit me", "doesn't fit me",
                              # the reason is often said as a plain fact with no return word in
                              # the line: "i bought a dress online and it does not fit"
                              "does not fit", "doesnt fit", "doesn't fit", "dont fit", "dont fits",
                              "didnt fit", "didn't fit", "wrong size", "not my size",
                              "too small", "too big")),
          "Buying at a distance gives you 14 days from the day it arrives to change your mind, for any "
          "reason and without giving one: tell them in writing, send it back within 14 days of that, "
          "and the refund comes within 14 days of the goods or your proof of posting, including the "
          "standard delivery cost. You pay the return postage unless their terms say otherwise, and "
          "personalised, perishable or opened hygiene items are the exceptions.",
          # a general "can i get a refund" answer in another domain scores two key words on these
          # lines too: the 14-day right is the specific one, so it takes the tie
          bias=2,
          ask=("i", "my", "we", "can", "bought", "ordered"),
          avoid=("faulty", "broken", "doesnt work", "doesn't work", "gift", "present",
                 "damaged", "not arrived", "care home", "they sent", "sent me the wrong",
                 "sent the wrong", "gym", "membership", "tenancy", "landlord", "car insurance",
                 "holiday", "flight", "hotel booking", "vet", "school",
                 # a shop that refuses a change-of-mind return is its own answer
                 "shop", "in a shop", "in store", "the shop", "retailer"),
          # "can i return shoes i bought online if they dont fit" is a yes/no question, and the
          # card answered it with the 14-day rule and never said yes. The row is asked both ways
          # round, so the sentence is `_change_of_mind_verdict`'s rather than a fixed "Yes".
          lead=("yesno", _change_of_mind_verdict)),
    # "i changed my mind" was answered as a distance sale whether or not anything had been
    # bought by post: "i changed my mind about the hoover" told someone about the 14-day right
    # when the hoover may have come from a shop. This row answers the mind alone, both ways.
    entry("mind-changed-thing",
          (("changed my mind", "change my mind", "changed our minds", "change our minds",
            "changing my mind", "dont want it anymore", "don't want it anymore",
            "decided against it", "gone off it", "not what i expected", "dont like it",
            "don't like it", "dont want it now", "don't want it now", "dont want the",
            "don't want the", "wish i hadnt bought", "wish i hadn't bought",
            "shouldnt have bought", "shouldn't have bought", "buyers remorse"),
           # The key needs a second part to reach the line at all: a row of whole phrasings and
           # nothing else scores below the floor and never answers. These are the words every
           # line of this kind carries, so the second part only says "and the line keeps
           # talking", while the plan words in `avoid` are what decide it is not a purchase.
           ("i", "my", "we", "our", "it", "the", "this", "that", "about", "a", "and", "so",
            "now", "still"),
           # A return word is the second thing these lines say, and it is what lifts the row over
           # the faulty-goods ladder on "ive changed my mind can i return it": nothing was wrong
           # with the thing, so the 30-day fault answer is not the one.
           ("return", "returns", "return it", "refund", "money back", "send it back",
            "send back", "take it back", "take back", "exchange", "keep it", "shop",
            "store", "online", "bought", "ordered", "receipt", "tags", "packaging")),
          "Changed your mind? Bought online, by phone or by post, you have 14 days from the day it "
          "arrives to say so and another 14 to send it back, for any reason, and the refund covers "
          "the standard delivery. Bought in a shop there is no automatic right, so it comes down "
          "to their policy - take it back with the receipt and the tags on and ask for a refund, "
          "and a goodwill credit note is a fair answer if the policy says no.",
          # A change of mind about a plan is not a return, and the mind words alone were giving
          # the 14-day card to "i changed my mind about the job offer", "about university" and
          # "about going to the wedding". Anything that names something other than goods stands
          # this row down, and the rows that answer plans take the line instead.
          avoid=("faulty", "broken", "doesnt work", "doesn't work", "stopped working", "damaged",
                 "not arrived", "never arrived", "sent me the wrong", "sent the wrong",
                 "sold as new", "described as", "advertised as", "gym", "membership", "tenancy",
                 # not "deposit" on its own: "i put a deposit on a car and changed my mind" is
                 # the classic distance-sale withdrawal, and the tenancy words below cover the
                 # rent meaning
                 "landlord", "tenancy deposit", "holding deposit", "holiday", "flight", "hotel", "vet", "school", "council",
                 "insurance", "job", "offer", "university", "college", "course", "degree",
                 "wedding", "house", "flat", "mortgage", "moving", "move out", "name", "baby",
                 "pregnancy", "career", "haircut", "hair", "tattoo", "piercing", "colour",
                 "color", "paint", "kitchen", "bathroom", "extension", "renovation", "garden",
                 "dog", "puppy", "kitten", "cat", "pet", "restaurant", "booking", "table",
                 "dinner", "menu", "meal", "recipe", "film", "movie", "book", "series",
                 "game", "ticket", "gig", "train",
                 # a car or a bike is bought, and most often on finance or by post: "i changed my
                 # mind about the car" and "i put a deposit on a car and changed my mind" were
                 # standing the returns card down and reaching "Nice one. How did the rest of it
                 # go?", which is no answer at all. They keep the both-ways card.
                 "doctor", "dentist", "operation", "treatment", "diet",
                 # a place the chat is holding ("i changed my mind about the coast") is a plan
                 # taken back, which the conversation store answers, not a purchase
                 "coast", "beach", "seaside", "cottage", "campsite", "camping", "abroad",
                 # "i keep changing my mind" is how someone describes being unable to decide,
                 # not a purchase, and the returns card was the answer to it.
                 "keep changing", "keeps changing", "keep on changing", "always changing",
                 "cant decide", "can't decide", "i keep", "i always",
                 # a line that says how it was bought is the distance answer's, which gives the
                 # letter, the 14 days to post it and the chargeback in full
                 "online", "by post", "mail order", "catalogue", "website", "amazon",
                 "click and collect", "ordered", "delivered", "courier", "order number"),
          # "i dont like it" on its own is a follow-up after a recipe, a film or a suggestion -
          # the thing liked is whatever was just talked about, and no purchase is in the line.
          # The mind is about goods only when something bought is named with it.
          guard=_mind_is_about_goods,
          bias=2),
    # With the returns card standing down on a plan, "i changed my mind about the job offer" was
    # left to the chat pools and came back as "Good to hear. What was the best bit?" - a cheer for
    # a decision the person is uneasy about. The mind about a plan gets one honest short answer.
    entry("mind-taken-back-plan",
          (("changed my mind", "change my mind", "changed our minds", "change our minds",
            "changing my mind", "decided against it", "gone off the idea",
            "dont want to do it", "don't want to do it", "backing out", "turning it down"),
           ("job", "offer", "university", "college", "course", "degree", "apprenticeship",
            "wedding", "house", "flat", "mortgage", "moving", "move", "emigrating", "relocating",
            "holiday", "trip", "flight", "hotel", "booking", "restaurant", "table", "dinner",
            "party", "venue", "name", "colour", "color", "paint", "kitchen", "bathroom",
            "extension", "renovation", "loft", "garden", "shed", "gym", "membership",
            "haircut", "hair", "tattoo", "piercing", "career", "coursework", "wedding dress",
            # a place is a plan too, and "i changed my mind about the coast" was answered with
            # "Good to hear. What was the best bit?" once the returns card stood down
            # getting a pet is a plan as often as it is a purchase, and the arrival date moves
            "getting a dog", "getting a cat", "getting a puppy", "the dog", "the puppy",
            "the kitten", "the puppy training", "a dog", "a puppy",
            "coast", "beach", "seaside", "cottage", "campsite", "camping", "caravan", "abroad",
            "resort", "island", "city break", "destination", "the trip", "our trip",
            "the plan", "the idea")),
          "What changed your mind? If you already said yes to it, say so early and in one short "
          "line to whoever is expecting you - a change of heart is easier to take than a silence, "
          "and you do not need a reason they will approve of, only the one that is true.",
          avoid=("faulty", "broken", "refund", "return it", "should i return", "send it back",
                 # Backing out of a house purchase is a legal question, not a message to send:
                 # "can i back out of buying a house" was told to say so early and in one short
                 # line. The sale's own rows answer it, and every other plan keeps this card.
                 "buying a house", "buying a flat", "buying a property", "house purchase",
                 "purchase of a house", "exchange contracts", "contracts exchanged",
                 "after exchange", "deposit", "gazumping",
                 "receipt", "tags", "faq", "online", "shop", "store", "keep changing",
                 "keeps changing", "i keep", "i always", "cant decide", "can't decide",
                 # something already paid for is goods, whatever it is: the returns card and the
                 # distance card answer that, not this one
                 "bought", "i paid", "ordered", "delivered", "the receipt", "warranty"),
          bias=1),
    entry("shop-return", (("return", "returns", "take it back", "take back", "exchange",
                           "swap it", "bring it back", "refund", "credit note", "voucher back"),
                          ("in a shop", "in store", "in the shop", "from the shop",
                           "bought in a shop", "bought it in a shop", "high street",
                           "for a bigger size", "for a smaller size", "different size",
                           "another size", "credit note", "without a receipt",
                           # the fit is the reason half the time, and the line often carries no
                           # return word: "my top doesnt fit can i take it back to the shop"
                           "doesnt fit", "doesn't fit", "does not fit", "dont fit", "didnt fit",
                           "didn't fit", "wrong size", "too small", "too big", "not my size",
                           # "i was told i cant return it because its sale" is the in-shop
                           # change of mind with a sale tag used as the excuse; the sale rule
                           # itself stays lifeadmin's sale-refund row
                           "because its sale", "because it was in the sale",
                           "because its in the sale")),
          _shop_return_reply,
          bias=1,
          ask=("can", "i", "my", "the", "do", "what", "is", "how"),
          avoid=("online", "website", "amazon", "ebay", "paypal", "faulty", "broken",
                 "doesnt work", "parcel", "delivery", "flight", "hotel", "gym", "tenancy",
                 "landlord", "car", "library", "tax return", "school", "voucher expired")),
    entry("doesnt-fit", (("sofa", "wardrobe", "table", "armchair", "bed", "mattress", "furniture",
                          "dishwasher", "cooker", "fridge freezer", "tumble dryer"),
                         ("doesnt fit", "doesn't fit", "wont fit", "won't fit", "too big",
                          "too wide", "wont go through", "won't go through", "through the door",
                          "up the stairs", "wont go in", "won't go in")),
          "Measure the gap and the doorway before you argue, and take the legs or the door off if "
          "that is all that is stopping it: most sofas come apart at the back. Bought online or over "
          "the phone, you have 14 days to cancel and they have to collect a bulky item, though they "
          "can charge for that if the terms say so; bought in a shop, a return is their own policy, "
          "and something made to your measurements has no right to one.",
          bias=1,
          ask=("my", "the", "it", "i", "we"),
          avoid=("how do i cook", "recipe", "how long do i cook", "defrost", "washing machine is leaking")),
    entry("meal-complaint", (("restaurant", "cafe", "takeaway", "deliveroo", "just eat", "pub meal",
                              "waiter", "waitress", "the meal", "my meal", "my food", "meal",
                              "meals", "my dinner", "my lunch", "the dish", "cold meal",
                              "cold food", "lukewarm"),
                             ("complain", "complaint", "refund", "cold", "raw", "undercooked",
                              "not what i ordered", "wrong order", "hair in", "sent it back",
                              "wrong dish", "wrong meal", "wrong food", "brought the wrong",
                              # the ask is usually the sending back rather than the word
                              # complain: "how do i send food back in a restaurant" reached a
                              # search hedge, and "how do i complain about a cold meal" was read
                              # as somebody ill with a cold, because it says "a cold" and "meal".
                              "send it back", "send the food back", "send food back",
                              "too cold", "off", "disgusting",
                              # bad service is a complaint about the meal out too, and the answer
                              # says what to ask for when it is the service rather than the food
                              "rude", "ignored us", "ignored me", "slow service",
                              "bad service", "awful service", "service charge",
                              # food past its date, or spoiled, is the same complaint as food
                              # served cold: "the restaurant gave me out of date food" and "the
                              # cafe gave me mouldy food" had no answer at all, because the only
                              # card holding the date words is the shop's refund one and that
                              # stands down for a restaurant.
                              "out of date", "past its date", "past the date", "past its use by",
                              "past the use by", "past its sell by", "use by", "sell by",
                              "mouldy", "mould", "moldy", "stale", "sour", "gone bad",
                              "went off", "gone off",
                              # what a restaurant does with a dish you have sent back
                              "take it back", "take my food back", "take the food back",
                              "wont take", "won't take", "wouldnt take", "wouldn't take",
                              "gave me my money back")),
          "Say it at the table before you pay and ask for that dish to come off the bill; for a "
          "takeaway, ring the restaurant the same day rather than the app. Cold, raw or the wrong "
          "meal is not what you ordered, so photograph it and dispute that amount on the card if "
          "they will not take it off. Bad service gets the manager there and then and the service "
          "charge off; a hygiene problem goes to the council's environmental health team.",


          ask=("my", "the", "i", "we"),
          # a general "complain, then escalate to the ombudsman" answer also scores on these
          # lines: the bill is what a bad meal is about, so this takes the tie
          bias=1,
          avoid=("food poisoning", "how do i cook", "recipe", "how long do i cook", "i want to cook",
                 "book a table", "how do i complain to the council",
                 # "gone off" is in this row's keys as a spoiled dish, and with a person's
                 # possessive it is the other meaning: "ive gone off my food" is an appetite that
                 # has gone, not a meal to send back, and it was answered "ask for that dish to
                 # come off the bill"
                 "off my food", "gone off my food", "gone off her food", "gone off his food",
                 "gone off their food", "off her food", "off his food", "off their food",
                 "lost my appetite", "lost his appetite", "lost her appetite", "loss of appetite",
                 "no appetite", "appetite",
                 # the food in your own kitchen is a shelf-life question, and the date words
                 # above would otherwise let this card answer a fridge: "my chicken is out of
                 # date" and "is my milk past its date" belong to the keeping rows next door
                 "my fridge", "in the fridge", "out of the fridge", "my cupboard",
                 "in the cupboard", "my freezer", "in the freezer", "i bought", "i've bought",
                 "supermarket", "the shop", "from the shop", "packet", "use by date on",
                 "still ok", "still good", "safe to eat", "can i eat", "can i still eat",
                 "bin it", "keep it", "how long", "can i freeze",
                 # and a plain statement about the food in the house is not a meal out:
                 # "my food is out of date" and "my food went mouldy" were an echo before, and
                 # the date words above would have handed them to the restaurant card
                 "is out of date", "went mouldy", "has gone mouldy", "is mouldy",
                 "smells off", "tastes off",
                 # keeping your own food cold is the lunchbox row's question, not a complaint:
                 # "how do i keep my food cold at work" was answered with the send-it-back
                 # script because it says "my food" and "cold" and nothing else in it counts
                 "keep my food", "keep the food", "keep food", "keep my lunch", "keep it cold",
                 "keep it cool", "keep it warm", "cold at work", "cool bag", "ice pack",
                 "lunchbox", "lunch box", "packed lunch")),
    # --- the rest of a meal out ---------------------------------------------
    # The complaint is the dish; these are the other things a person brings back from a table.
    # "What do i say if the bill is wrong" reached a search hedge, "how do i ask for the bill"
    # a Citizens Advice line, "is it rude to ask for a doggy bag" the lost-luggage steps (a
    # suitcase is a bag too) and "what do i do if the restaurant is fully booked" nothing at all.
    entry("meal-bill-wrong",
          (("bill is wrong", "wrong bill", "bill was wrong",
            "bill seems wrong", "bill seems high", "bill is too high", "bill is higher",
            # the same complaint said of a place: "the bill at the restaurant was too high" matched
            # no phrase here, so the fuel row's "bill" and "high" took it and answered with the
            # boiler. "bill at the" only ever means the one on a table - a bare "bill was too high"
            # was tried and gave "my bill was huge" to the table instead of the fuel, so the
            # place words are the whole widening.
            "bill at the", "bill at a", "bill at our",
            "extra on the bill", "too much on the bill", "extra items", "not on the menu",
            "asked to pay for", "they added", "extra charge on the"),
           ("bill", "restaurant", "meal", "pub", "bar", "cafe", "drinks", "dinner", "lunch",
            "waiter", "waitress", "table", "check", "receipt")),
          "Ask for the itemised bill while you are still at the table, not the card slip, and "
          "point at the line: 'sorry, we didn't order the garlic bread' is enough and they will "
          "reprint it. A service charge you were not told about comes off the same way, because "
          "it is discretionary rather than law. If you have already paid, a short email to the "
          "manager with the date and the receipt gets it refunded, and a card payment can be "
          "disputed if they refuse.",
          # every other bill has its own row, and "ask for the itemised bill" is nonsense for a
          # gas bill, a phone contract or a hotel minibar charge.
          avoid=("energy", "electricity", "gas", "water", "broadband", "internet", "phone",
                 "mobile", "council tax", "credit card", "card bill", "store card", "invoice",
                 "salary", "wage", "tax", "vet", "dentist", "doctor", "hospital", "repair",
                 "garage", "mot", "builder", "plumber", "landlord", "rent", "lease", "hotel",
                 "minibar", "airbnb", "cleaning fee", "leasehold", "management charge",
                 # "my heating bill is too high" was told to ask for the itemised bill at the
                 # table: the household fuels are all fenced here and the fuel a boiler burns is
                 # called "heating", which was not in the list. The heating card has the answer,
                 # so the same words go in as `bill-becomes-law` carries.
                 "heating", "heating oil", "boiler", "boilers", "radiator", "radiators",
                 "kwh", "heat pump", "wood burner", "log burner", "storage heater")),

    entry("ask-for-the-bill",
          (("ask for the bill", "get the bill", "ask for the check", "get the check",
            "pay the bill", "pay the check", "pay at the table", "settle the bill",
            "pay our bill", "bring the bill", "card machine", "pay for the meal"),
           ("bill", "restaurant", "waiter", "waitress", "table", "card", "cash", "meal",
            "dinner", "pub", "bar", "cafe", "check", "pay")),
          "Catch the waiter's eye as they pass and say 'could we get the bill when you have a "
          "moment' - short and polite, and it says you are ready without rushing them. Check it "
          "before you tap, then pay at the table on the card machine. Say up front if you want it "
          "split: most machines take two cards, and it is easier before the slip is printed.",
          avoid=("energy", "electricity", "gas", "water", "broadband", "internet", "phone",
                 "mobile", "council tax", "credit card", "card bill", "invoice", "salary",
                 "wage", "tax", "landlord", "rent", "lease", "vet", "dentist", "doctor",
                 "hospital", "repair", "garage", "mot", "builder", "parking", "fine",
                 "hotel", "minibar", "taxi", "train", "flight",
                 # the same hole as `meal-bill-wrong`: "pay my heating bill" was the card machine
                 "heating", "heating oil", "boiler", "radiator", "radiators", "kwh",
                 "heat pump", "wood burner", "log burner", "storage heater")),

    entry("taking-food-home",
          (("doggy bag", "doggybag", "doggy-bag", "take the rest home", "take my leftovers home",
            "take the leftovers home", "box up the rest", "box the rest", "leftovers box",
            "take it home with me", "ask to take", "take my food home", "take home the rest",
            "take the leftovers", "take food home", "box to take", "a box to take",
            "takeaway box", "take away box", "take out box"),
           # "how do i ask for a doggy bag" is the commonest way the question is typed and the
           # row could not hear it: it names the bag and nothing else, so the second half - which
           # wanted a restaurant word - was empty. The asking is the restaurant, so the asking
           # counts. The dog, the bin and the cake in the avoid below are still not this row.
           ("restaurant", "meal", "food", "leftovers", "waiter", "waitress", "dinner",
            "rude", "polite", "ok", "okay", "normal",
            "ask", "asking", "asked", "how do i", "can i", "is it")),
          "Ask - 'could you box up what's left?' is normal, and most places say yes, though here "
          "it is their choice rather than your right. Get it into the fridge within two hours and "
          "eat it within a day or two, reheating it once until it is piping hot.",
          # a dog, a bin and a cake are all "taking it home" in words and none of them is this.
          avoid=("dog", "dogs", "puppy", "cat", "pet", "poo", "bin", "compost", "cake", "bake",
                 "recipe", "freezer bag", "ice cube", "patient", "hospital")),

    # Asking the staff for something is its own small skill and the bot had no row for it.
    # Eleven typed lines were a hedge or a card about something else: "how do i ask for a smaller
    # portion at a restaurant", "can i ask for a takeaway box at a restaurant", "how do i ask for
    # tap water at a restaurant" (the sink-and-tap cleaning card), "is it rude to ask for tap
    # water" (a plumber), "how do i ask for no onion in a restaurant" (how to soften an onion),
    # "how do i ask for the sauce on the side" (start a business), "how do i ask for a doggy bag"
    # (a search hedge), "how do i ask for a different table", "how do i ask for a highchair",
    # "how do i ask if a dish has nuts in it" and "how do i ask a dish without dairy" (the
    # dairy-swap card). The object goes first in the key, as it does in the bill rows, because
    # the ask is the same whatever is being asked for.
    entry("asking-at-a-table",
          (("smaller portion", "small portion", "half a portion", "starter portion",
            "half portion", "portion is too big", "too much food",
            "different table", "another table", "move table", "move tables",
            "highchair", "high chair", "baby chair", "booster seat",
            "tap water", "just water", "water for the table",
            "no onion", "without onion", "no cheese on", "hold the cheese", "no mayo",
            "no dressing", "sauce on the side", "sauce separate", "sauce in a dish",
            "dressing on the side", "dressing separate", "on the side please",
            "without the sauce", "extra sauce",
            "napkins", "take the plate", "clear the plates", "the plate away",
            # a cake asked about *in* a restaurant is still a table question - cakeage, a
            # candle, carrying it in - so the phrase carries the table with it and the bare
            # "birthday cake" stays out of this half (see the note below)
            "cake to a restaurant", "cake at a restaurant", "cake in a restaurant",
            "bring a cake", "bring our own cake", "our own cake", "cakeage",
            "candle in the cake"),
           # The asking is what makes it a table question. A bare "how do i" or "can i" in
           # this half was enough for "can i drink the tap water in turkey" and "can i brush my
           # teeth with the tap water" to be told to ask for a highchair. What is NOT in the
           # first half is the birthday cake: "how do i order a birthday cake from a bakery" and
           # "where do i order a birthday cake" were the bakery and the two-layer sponge cards,
           # and "order" in this half turned all four of those into a table question. A cake is
           # a thing to buy or bake, not a thing to ask a waiter for.
           ("ask", "asking", "asked", "rude", "polite", "awkward", "embarrassing",
            "restaurant", "waiter", "waitress", "server", "waiting staff", "order",
            "menu", "meal", "eat out", "eating out", "pub", "cafe")),
          "Ask in one short sentence when you sit down or when you order - 'could we have a "
          "highchair?', 'no onion in the pasta please', 'a table away from the door if you have "
          "one' - and it needs no explanation or apology beyond please and thanks; staff would far "
          "rather be asked than find you unhappy later. Kitchens do 'on the side' and smaller "
          "portions all the time and neither costs anything, so ask for 'a starter portion of the "
          "main' when the menu sells the dish both ways. Tap water is free and comes without a "
          "fuss, and the answer to almost all of it is to ask early, because 'we have already "
          "started cooking it' is the only real no.",
          # the onion row, the tap washer row and the baking rows all own their own words: this
          # is the asking at a table, so it stays out of the kitchen and out of the plumbing
          avoid=("chop", "chop it", "soften", "caramelise", "saute", "boil", "recipe", "bake",
                 "baking", "oven", "soup", "curry recipe", "pickle",
                 "tap washer", "dripping tap", "limescale", "boiler", "plumber", "sink",
                 "washing up", "dishwasher", "mains water", "water pressure", "hard water"),
          # "on the side" is a side hustle to the business row, so a dish asked for separately
          # has to outrank it: "how do i ask for the sauce on the side" was "sell something
          # before you register anything".
          bias=2),

    # An allergy said at a table is a different sentence from a preference, and the bot was
    # answering "how do i ask if a dish has nuts in it" with a search hedge.
    entry("asking-about-allergens-at-a-table",
          (("nut allergy", "allergic to", "allergy", "allergens", "asking about nuts",
            "has nuts", "contain nuts", "nuts in it", "no dairy", "dairy free", "without dairy",
            "gluten free", "coeliac", "celiac", "shellfish", "sesame"),
           ("restaurant", "waiter", "waitress", "server", "chef", "kitchen", "menu", "dish",
            "order", "ask", "asking", "takeaway", "eating out", "curry house", "cafe", "pub",
            "hotel", "buffet", "school dinner", "canteen")),
          "Say the word allergy rather than preference, name the dish, and ask them to check with "
          "the kitchen: 'I'm allergic to nuts - can you check the curry paste?' A server who says "
          "they will ask the chef is the answer you want, and one who guesses is the reason to "
          "order something else, because the fryer, the chopping board and the sauce are where it "
          "hides. For coeliac, ask about the fryer and the bread separately and ask to see the "
          "allergen folder, which every UK chain keeps and has to give you.",
          # a reaction already happening is an emergency, and the swaps at home are the cooking
          # rows: this is the sentence to say across a table
          avoid=("throat", "swollen", "swelling", "cant breathe", "can't breathe", "rash",
                 "vomiting", "ambulance", "999", "a&e", "epipen", "anaphylaxis",
                 "recipe", "bake", "baking", "substitute", "swap", "swaps", "instead of milk",
                 "at home", "cake recipe")),

    entry("table-fully-booked",
          (("fully booked", "fully-booked", "no table for", "no tables left"),
           ("restaurant", "table", "booking", "dinner", "lunch", "meal", "pub",
            "bistro", "waiting list", "waitlist", "cancellation", "cancellations")),
          "Ask to go on the waiting list and to be rung if a table frees up, and ask about eating "
          "at the bar, which most places allow when the room is full. Ring back at about five in "
          "the afternoon: that is when the day's cancellations are known and the tables are "
          "released. If it is a birthday or an anniversary, say so - it gets you further than "
          "arguing does.",
          # the words of a full restaurant are the words of a full hotel, train, class and
          # campsite, and every one of those has its own answer.
          avoid=("hotel", "flight", "flights", "train", "ticket", "tickets", "holiday",
                 "doctor", "dentist", "gp", "appointment", "vet", "theatre", "show", "concert",
                 "taxi", "campsite", "camping", "ferry", "class", "classes", "course", "lesson",
                 "swimming", "gym", "viewing", "viewings", "flat", "house", "wedding", "party",
                 "conference", "meeting", "test", "court", "spa")),

    entry("holding-deposit", (("holding deposit", "holding fee", "holding payment", "reservation fee",
                               "estate agent", "letting agent"),
                              ("kept", "keep", "keeps", "not back", "refund", "return", "retained",
                               "gone", "withholding", "pocketed",
                               # "what is a holding deposit" names the thing and asks what it
                               # is: the second signal was a verb of keeping
                               "what", "whats", "what's", "is a", "is it", "mean", "means",
                               "explain", "much", "how much", "how much is")),
          _holding_deposit,
          bias=2,
          # "what is a holding deposit" asked what the thing is and the gate wanted "my" or "the",
          # so the question went to the credit-card chargeback answer
          ask=("my", "the", "i", "we", "kept", "keep", "what", "whats", "what's", "is a",
               "explain", "mean", "means"),
          avoid=("how much", "how do i rent", "admin fee", "deposit back from the landlord")),
    entry("hotel-bill", (("hotel", "minibar", "room service", "hotel bill", "my room bill",
                          "airbnb", "holiday let", "the host", "cleaning fee", "service fee"),
                         ("charged me for", "charged me a", "never used", "never had", "not mine",
                          "wont remove", "won't remove", "wrong charge", "extra charge",
                          "charged my card", "cleaning fee", "cleaning charge")),
          "Ask for the itemised bill, or the listing for a holiday let, and dispute the line in "
          "writing the same day: a charge has to be something you actually had or agreed to, and "
          "they have to show the signed docket or the term you accepted. If it came off the card "
          "you gave at check-in, that is a wrong amount your bank can charge back, and somewhere "
          "that ignores you is a complaint to the site you booked with.",
          bias=1,
          ask=("my", "the", "i", "they", "charged"),
          avoid=("cancel", "non refundable", "move the dates", "filthy", "dirty", "overbooked",
                 "how much", "should i", "what is a")),
    entry("water-leak", (("leak", "leaking", "water meter", "the meter", "burst pipe",
                          "pipe burst", "water pipe", "supply pipe", "pouring water"),
                         ("turning", "keeps running", "still running", "running with", "taps off",
                          "all the taps", "under the floor", "hidden", "who pays", "have to pay",
                          "my bill", "underground", "in the garden", "garden", "outside",
                          "make me pay", "pay for the leak", "pay for it", "my fault", "burst",
                          "front garden", "driveway", "lawn")),
          "Turn the stopcock off first, then ring the water company: it is responsible for the pipe "
          "up to the boundary stop valve, and most companies give a one-off leakage allowance that "
          "writes off the extra water when the leak was hidden, so ask for it by name. A plumber "
          "finds and fixes the pipe on your side, and keep the receipt and the photos of the meter.",
          ask=("my", "the", "it", "i", "we", "should", "do"),
          avoid=("gas", "energy", "electric", "boiler", "radiator", "roof", "dripping tap",
                 "how do i fix", "how do i stop", "washing machine", "dishwasher", "toilet",
                 "how much does a plumber"),
          # money's split-the-bill answer reads "who pays" and "garden" as a restaurant table:
          # a leak under the garden is the water company's pipe, so this entry keeps it
          bias=5),
    entry("water-bill-high", (("water bill", "water bills", "water company", "water meter", "metered",
                           "on a meter",
                           "water charges", "sewerage", "water rates", "thames water",
                           "severn trent", "yorkshire water", "anglican water", "united utilities"),
                          ("huge", "high", "so much", "gone up", "double", "more than usual",
                           "wrong", "estimated", "estimate", "leak", "dispute", "complain",
                           "cant afford", "can't afford", "meter reading", "overcharging",
                           "enormous", "lower", "reduce", "cheaper", "too much")),
          "Ring the water company and ask for the bill to be checked against your meter reading, "
          "because an estimated bill built on last summer's hosepipe is the usual cause: read the "
          "meter yourself and give them the number. If the meter is turning with all the taps off "
          "you have a leak, and most companies cut the bill for a hidden leak once, so ask about "
          "their leakage allowance; if it stalls, the Consumer Council for Water is free.",
          avoid=("energy", "electric", "electricity", "gas", "gas bill", "smart meter", "broadband",
                 "council tax", "leak in the roof",
                 # "has gone up" is why the bill rose, which money's bill-went-up answers better
                 "gone up", "went up", "has risen", "rise", "why is my water bill",
                 "radiator", "boiler", "hot water", "drinking water", "water the plants",
                 "how much water should i drink"),
          bias=1),
    entry("lost-repair", (("repair", "repairs", "in for repair", "being repaired", "mending",
                           "service", "servicing", "my laptop", "my phone", "my watch", "my bike",
                           "my camera", "my hearing aid", "my sewing machine"),
                          ("lost", "gone missing", "cant find", "can't find", "never came back",
                           "hasnt come back", "hasn't come back", "vanished", "no sign of it",
                           "went missing", "they lost")),
          "A shop holding your goods for repair has to look after them, and if it loses one it owes "
          "you what it would cost to replace, not the repair fee: put it in writing with the make, "
          "model and what you paid, and ask for their insurance details. If they will not settle, "
          "the free route is a letter before claim and then Money Claims Online, from about £35.",
          bias=2,
          # the goods have to be in for repair for the shop to owe anything: "i lost my phone"
          # on its own is the find-it answer, and the item words below are only the other half
          ask=("repair", "repairs", "repaired", "repairing", "in for repair", "being repaired",
               "mending", "servicing", "service"),
          avoid=("boiler", "washing machine", "fridge", "lost my job", "lost my temper",
                 "how much does a repair cost", "should i repair",
                 # lost somewhere, not lost by the repairer: the hotel and the find-it answers
                 "hotel", "hostel", "guest house", "in the room", "on the train", "on the bus",
                 "in a taxi", "at the airport", "on the beach", "in the pub")),
    entry("digital-content", (("download", "downloads", "digital", "ebook", "e book", "kindle",
                               "software", "game key", "online course", "course i bought",
                               "streaming", "in app", "audiobook", "online subscription"),
                              ("doesnt work", "doesn't work", "wont work", "won't work", "rubbish",
                               "useless", "not what", "nothing like", "refund", "money back",
                               "broken", "waste of money", "wont open", "won't open", "crashes",
                               "wrong item", "cant access", "can't access")),
          "Digital content has to work and be as described, so you can ask for a repair or a "
          "replacement first, and a price reduction or your money back if that fails or is not "
          "possible. Ask the seller who took the payment, not the platform, put it in writing with "
          "the order number, and if they refuse a card payment can go to your bank as a chargeback.",
          avoid=("wifi", "broadband", "printer", "how do i download", "how do i install",
                 "free", "password", "phone", "laptop", "app store", "how do i set up",
                 "which app", "best app")),
    entry("pension-missing", (("pension", "pensions", "state pension", "workplace pension",
                               "annuity", "my pension pot", "final salary"),
                              ("missing", "not paid", "stopped", "wrong", "cant find", "can't find",
                               "lost", "havent had", "haven't had", "didnt get", "didn't get",
                               "short", "less than", "how do i claim", "trace", "old pension",
                               "forgotten", "not receiving", "hasnt been paid", "hasn't been paid",
                               "not been paid",
                               # "i need to sort out my pension, ive got three old ones" names the
                               # pension and then says the rest with "ones": nothing is missing,
                               # and the pots answer is the right one for it. "sort out" alone is
                               # not keyed, because "how do i sort out my pension" is the
                               # workplace row's line and the tracer is a wrong first move there.
                               "old ones", "old one", "several pensions", "a few pensions",
                               "multiple pensions", "what do i do with", "consolidate",
                               "consolidating", "combine", "combining", "merge")),
          _pension_reply,
          # "my pension hasnt been paid" is the scheme's question, and work.unpaid-wages (a pay
          # packet) carries bias=2 and was winning it: the Ombudsman answer is the right one.
          bias=3,
          avoid=("how much should i save", "how much do i need to retire", "retire early",
                 "pension credit", "inheritance",
                 # stopping work is when the state pension starts, not a payment that went
                 # missing: "if i stop work at 62 what happens to my state pension" and "what if
                 # i stop work before pension age" were both sent to the tracing service.
                 "stop work", "stopping work", "before pension age", "pension age",
                 "retirement age", "what happens to my state pension",
                 # "how do i sort out my state pension" asks for the age and the claim, and
                 # `state-pension-claim` answers it: this row is only a scheme that has lost or
                 # stopped paying something.
                 "sort out my state pension", "sort my state pension", "claim my state pension",
                 "state pension age", "state pension forecast",
                 # and a pension through an employer is joined, not traced
                 "at work", "workplace pension", "company pension", "auto enrolment",
                 "auto-enrolment", "my work pension")),
    entry("seller-ignoring", (("seller", "shop", "company", "retailer", "trader", "the site",
                               # the phone is the same silence: "i cant get through to customer
                               # service", "they keep putting the phone down on me"
                               "customer service", "call centre", "call center", "helpline",
                               "phone line", "the phone down", "hanging up", "hung up"),
                              ("wont answer", "won't answer", "ignoring", "no reply",
                               "not replying", "stopped replying", "ghosted", "not answering",
                               "wont respond", "won't respond", "cant get hold of",
                               "can't get hold of", "never answers", "ghosted",
                               "cant get through", "can't get through", "keep putting",
                               "put the phone down", "keeps putting", "cuts me off",
                               "cut me off", "on hold", "no one answers", "nobody answers",
                               "keeps hanging up", "hang up on me", "hangs up on me",
                               "passed around", "transferred me")),
          _seller_ignoring_reply,
          avoid=("car seller", "house seller", "estate agent", "landlord", "how do i sell",
                 "sell my", "my job", "job interview", "energy", "supplier", "broadband",
                 "phone contract", "water", "council", "bill", "rent")),
    entry("paypal-refund", (("paypal", "pay pal", "ebay", "ebay purchase", "marketplace"),
                            ("nothing", "never arrived", "not as described", "scam", "refund",
                             "dispute", "wrong item", "wrong thing", "wrong one", "damaged",
                             "seller wont", "seller won't", "sent the wrong", "different to",
                             # a seller who goes quiet after the money is the same dispute
                             "disappeared", "vanished", "ghosted", "stopped replying",
                             "wont answer", "won't answer", "wont reply", "won't reply",
                             "took my money", "never sent", "no item", "never came",
                             "never turned up", "didnt arrive", "didn't arrive")),
          "Open a dispute in PayPal's Resolution Centre within 180 days of paying, then escalate it "
          "to a claim if the seller does not answer: PayPal decides and refunds from the seller's "
          "money. On eBay, use the Money Back Guarantee in your purchase history first, and if the "
          "payment came off a card as well, your bank can still do a chargeback.",
          avoid=("bank transfer", "how do i send money", "fees", "how does paypal work")),
    entry("booking-cancelled-mine", (("venue", "wedding venue", "wedding", "hall", "village hall",
                                      "function room", "caterer", "marquee", "band", "dj",
                                      "photographer", "party", "birthday party", "christening"),
                                     ("i want to cancel", "i need to cancel", "we want to cancel",
                                      "we need to cancel", "i cancelled", "we cancelled",
                                      "i had to cancel", "we had to cancel", "cancel the venue",
                                      "cancel our wedding", "cancel the wedding", "postpone",
                                      "postponed", "keeps my deposit", "kept my deposit",
                                      "keeping my deposit", "keeps the deposit", "kept the deposit",
                                      "wont refund my deposit", "won't refund my deposit",
                                      "wont give my deposit back", "deposit back", "call it off",
                                      "called it off", "called off the wedding")),
          "A venue or caterer can only keep what your cancellation has actually cost them - the "
          "staff booked and the date they could not re-let - and they have to try to re-let before "
          "charging you, so ask for a written breakdown and the rest of the deposit back. If you "
          "cancelled because of something they did wrong, or a reason the contract names, the "
          "deposit comes back in full. Then a card chargeback, and Money Claims Online.",

          avoid=("they cancelled", "venue cancelled", "they have cancelled", "went bust",
                 "went under", "folded", "closed down", "double booked", "pulled out",
                 "never ran", "never started", "not started", "no longer trading"),
          bias=2),
    entry("venue-cancelled", (("venue", "wedding venue", "hotel venue", "conference", "party venue",
                               "photographer", "caterer", "wedding dress", "marquee", "course",
                               "training course", "night class"),
                              ("cancelled", "canceled", "called off", "closed down", "went bust",
                               "pulled out", "double booked", "refund", "deposit back", "deposit",
                               "already paid", "money back", "never ran", "never started")),
          "A cancelled booking means your deposit back in full, and a course that never ran owes "
          "the whole fee: ask in writing for it, with the date you paid. Add what you can show "
          "you lost on the replacements - the venue, the dress, the caterer - and ask for their "
          "insurer's name. If they will not pay, use a chargeback on the card or Money Claims "
          "Online, from about £35.",
          avoid=("gig", "concert", "festival", "ticket", "match", "theatre", "flight",
                 "how much deposit", "how much should i pay", "when should i book",
                 "how do i learn", "what course", "free course", "which course",
                 # the person cancelling is a different fight: their own deposit is
                 # booking-cancelled-mine
                 "i want to cancel", "i need to cancel", "we want to cancel", "we need to cancel",
                 "i cancelled", "we cancelled", "i had to cancel", "we had to cancel",
                 "postpone", "postponed", "keeps my deposit", "kept my deposit",
                 "keeping my deposit", "keeps the deposit", "kept the deposit",
                 "wont refund my deposit", "won't refund my deposit")),
    entry("food-spoiled", (("fridge", "freezer", "fridge freezer", "power cut", "power went off",
                            "electricity went off", "fuse box"),
                           ("food spoiled", "food went off", "food is off", "food gone off",
                            "thawed", "defrosted", "ruined the food", "spoiled", "spoilt",
                            "spolit", "had to throw it all away", "thrown it all away",
                            # "warm" alone is the wrong word: "something warm for dinner" and
                            # "the kitchen is warm" are said with a fridge in the line and no
                            # fault in it. The food going warm is the phrase that is the fault.
                            "went warm", "gone warm", "getting warm", "warm again",
                            # The other way a person says the fault is by the smell, and a line
                            # that says it has a fridge in it and nothing else about a fault:
                            # "the fridge is warm and the milk smells off" fell to the
                            # bottle-warming card once the bare "warm" left this list.
                            "smells off", "smelt off", "smells funny", "smells bad",
                            "gone sour", "curdled", "gone off", "off the milk",
                            # and the shape a person uses when they are asking who pays, with
                            # the damage said as "ruined" rather than "spoiled": "fridge is
                            # warm and everything inside is ruined can i claim" matched no
                            # key word in this half of the row, so the drain-hole card
                            # answered it and then the thermometer one.
                            "ruined", "ruin", "is ruined", "all ruined", "everything ruined",
                            "everything inside", "all the food", "warm and")),
          "Photograph the inside of the fridge and list what was in it before you clear up: if the "
          "appliance broke, the shop owes you a repair or replacement under the same 30-day and "
          "six-year rights as anything else, and the spoiled food is a separate loss you can ask "
          "them for. Most home insurance also pays for spoiled food after a breakdown or a power "
          "cut, usually up to a few hundred pounds with an excess.",
          bias=1,
          guard=_not_the_fridge_asking_why,
          ask=("my", "the", "it", "and", "food", "all"),
          avoid=("how do i freeze", "how long can i keep", "how do i defrost", "icing up",
                 "how to clean", "setting", "temperature", "energy use", "how long does")),
    entry("builder-quotes", (("builder", "plumber", "electrician", "tradesman", "roofer",
                              "decorator", "workman"),
                             ("quote", "estimate", "insured", "insurance", "cash", "upfront",
                              "up front", "deposit", "references", "check", "trustworthy",
                              "cowboy", "rip off", "ripped off", "vet", "reliable")),
          "Ask for three written quotes, a public liability insurance certificate and two phone "
          "numbers for recent jobs. Never pay cash up front: a small deposit on a card is fine, "
          "because a card payment over £100 gives you a claim against the card company too. A "
          "quote that names a start date, a price and what is included is the thing that keeps the "
          "job straight.",
          # a finished job gone wrong is the unfinished answer, and a drip is the plumbing one
          ask=("quote", "estimate", "insured", "insurance", "cash", "upfront", "up front", "deposit",
               "references", "check", "trust", "cowboy", "rip off", "ripped off", "vet",
               "how do i", "should i", "worth", "reliable"),
          avoid=("unfinished", "half done", "won't come back", "wont come back", "didn't finish",
                 "didnt finish", "refund", "complain", "complaint", "court", "took my money",
                 "leak", "leaking", "dripping", "no heating", "boiler", "blocked", "fuse")),
    entry("above-the-quote", (("more than the quote", "more than quoted", "higher than the quote",
                               "over the quote", "above the quote", "more than they quoted",
                               "more than agreed", "wants more money", "charging me more",
                               "charged me more", "extra on the bill", "added to the bill",
                               "on top of the quote", "quote went up", "price went up",
                               "didnt agree to", "didn't agree to", "didnt agree", "never agreed",
                               "work i didnt have", "work they didnt do", "work that wasnt done",
                               "work i never had", "didnt do the work", "never did the work",
                               "didnt have", "didnt need", "never had",
                               # a job promised free and then billed is the same "only what you
                               # agreed": "i was told the repair was free and they charged me"
                               "said it was free", "said it would be free", "told me it was free",
                               "told me it would be free", "told it was free", "free of charge",
                               "supposed to be free", "meant to be free", "said it was included",
                               "said the repair was free", "told the repair was free",
                               "told me the repair was free", "told me the repair would be free",
                               "said the job was free", "told me the job was free"),
                              ("quote", "quoted", "estimate", "agreed", "bill", "billed",
                               "invoice", "charged", "charging", "plumber", "builder",
                               "electrician",
                               "vet", "dentist", "dental", "tradesman", "workman", "job",
                               "treatment", "filling", "check up", "crown", "extraction",
                               "paid")),
          "A trader can only charge what you agreed, and extra work needs your agreement before it "
          "is done: ask for an itemised invoice, pay the agreed amount, and put in writing that you "
          "dispute the rest. If the money has already gone, ask for the difference back in writing "
          "and give them 14 days, then a card chargeback or Money Claims Online. At a dentist, vet "
          "or clinic, ask for the itemised bill and the plan you signed.",

          # before the work starts the question is how to hire: three quotes is that answer
          ask=("more than", "higher than", "over the", "above the", "wants more", "charging me",
               "billed me", "then billed", "billed for",
               "charged me", "extra", "went up", "didnt agree", "didn't agree", "never agreed",
               "on top of", "didnt have", "didnt do", "never did", "wasnt done"),
          avoid=("garage", "car repair", "mot", "how do i find", "how do i choose",
                 "should i get", "three quotes", "how many quotes",
                 # a shop's shelf price is the till question: the price displayed is the price
                 # you pay, which is a different sentence from a trader's quote
                 "shelf price", "price on the shelf", "the shelf", "till", "supermarket",
                 "price tag", "marked price", "menu", "checkout"),
          # "the vet bill is higher than the quote" also reads as a pet-costs line: a bill that
          # has already gone above the quote is this question, and the vet paragraph says what
          # to ask for, so the tie goes here, and a vet's bill above the price quoted is also a
          # pet-costs line: a bill that has already gone over is this question
          bias=3),
    entry("charged-what-i-didnt-order", (("didnt order", "didn't order", "didnt ask for",
                                          "didn't ask for", "didnt want", "didn't want",
                                          "never ordered", "not ordered", "service charge",
                                          "cover charge", "auto gratuity", "discretionary",
                                          "added a tip", "added to my bill", "on my bill",
                                          "on the bill", "added to the bill"),
                                         ("charged", "charge", "bill", "restaurant", "waiter",
                                          "waitress", "till", "checkout", "receipt", "paid",
                                          "menu", "takeaway", "tip", "hotel", "pub", "cafe")),
          "You do not have to pay for something you did not order: say so before you pay and ask "
          "for it to come off the bill, and a discretionary service charge can come off too. If "
          "you have paid already, ask for it back on the card in writing - a refund is due within "
          "14 days - and keep the bill for a chargeback if they refuse.",
          # a parcel that is not what was ordered is the wrong item, not a line on a bill, and a
          # charge added to a hotel bill (the minibar) is the hotel's bill answer
          avoid=("parcel", "delivered", "arrived", "sent me", "order number", "instead of the",
                 "instead of a", "instead of my",
                 "hotel", "minibar", "mini bar", "guest house", "b and b",
                 # "is a service charge the same as a tip" is not a bill to argue about: the
                 # line asks what the charge is, and the tip table says what it is, that it is
                 # discretionary and that asking for it to come off is allowed. This row is
                 # for a charge already added and not wanted.
                 "same as a tip", "same as the tip", "same as tipping", "is it a tip",
                 "a tip or", "is a service charge a tip", "service charge a tip",
                 "what is a service charge", "whats a service charge",
                 "what does service charge mean", "difference between", "should i tip",
                 "how much do i tip", "how much should i tip"),
          # money's bill-dispute entry answers "can i refuse to pay" from the paperwork side; a
          # service charge added to a restaurant bill is this question
          bias=2),
    entry("repair-taking-too-long", (("taking ages", "taking so long", "taking too long",
                                       "taking forever", "took 3 weeks", "took three weeks",
                                       "took a month", "took two months", "for three weeks",
                                       "for a month now", "for a month", "for two months",
                                       "for six weeks", "for a week now", "for weeks now",
                                       # what the shop says it will take, in words rather than
                                       # digits: "the shop says the repair will take six weeks"
                                       "will take", "going to take", "will be ready",
                                       "says it will", "two weeks", "three weeks", "four weeks",
                                       "five weeks", "six weeks", "eight weeks", "a month",
                                       "two months", "three months",
                                       "still not fixed",
                                       "still not repaired", "still waiting for the repair",
                                       "has had my", "have had my", "still has my",
                                       "still got my"),
                                      ("repair", "repaired", "repairing", "fixing", "fixed",
                                       "shop", "garage", "laptop", "phone", "watch", "bike",
                                       "weeks", "month", "months")),
          "A repair has to be done within a reasonable time: put a deadline in writing, 14 days, "
          "and say that if it is not ready you will collect the item and want the repair price "
          "back. Keep a copy, and ask for the item back in writing so there is a record of the "
          "date. If the shop still holds it after that, a card chargeback or Money Claims Online "
          "recovers what you paid.",
          # a lost repair, a bill above the estimate and a car are other answers
          # a repair has to be the subject: "i have had this cough for a month" and "my laptop
          # battery has been bad for a month" are not a shop holding the thing
          ask=("repair", "repairing", "repaired", "fixing", "fixed", "shop", "garage",
               "had my", "has my", "still has", "still got", "waiting for"),
          avoid=("lost", "lose", "gone missing", "car", "mot", "boiler", "quote", "quoted",
                 "how long does", "how long do", "should i repair", "worth repairing")),
    # the same fault coming back after a repair is not another repair: the shop has had its one
    # attempt, and the choice of a refund or a price reduction is the customer's again
    entry("repair-failed", (("repair", "repaired", "repairing", "fix", "fixed", "fixing",
                             "mended", "service", "serviced", "shop", "store",
                             "been back", "sent it back", "took it back"),
                            ("twice", "again", "second time", "third time", "still broken",
                             "still not working", "still doesnt work", "still doesn't work",
                             "still faulty", "same fault", "same problem", "keeps breaking",
                             "keeps going wrong", "broke again", "broken again", "gone wrong again",
                             "back in the shop", "back to the shop", "went again")),
          "One repair is the shop's go at it, not an endless supply: if the same fault comes back, "
          "you can refuse another repair and ask for a refund or a price reduction instead, "
          "because a repair has to be done properly and within a reasonable time. Send that in "
          "writing, list both repair dates and what went wrong each time, and keep the receipts. "
          "Within six months of buying, the shop has to prove the fault is not theirs.",
          # a repair that is slow, a repair that came back worse and a shop that lost the thing
          # are different answers, and a car's service is the garage's
          avoid=("taking", "still waiting", "waiting for", "lost", "gone missing", "worse",
                 "scratched", "quote", "quoted", "estimate", "how long", "car", "mot",
                 "garage", "van", "boiler", "washing machine", "cough")),
    entry("private-parking-charge", (("private car park", "private parking",
                                      "parking charge", "parking charge notice", "pcn",
                                      "parkingeye", "apcoa", "euro car parks", "anpr",
                                      "popla", "ias appeal", "overstayed", "overstay",
                                      "camera in the car park", "car park fine",
                                      "supermarket car park", "retail park", "leisure park",
                                      "hotel car park", "private land", "private property",
                                      "landowner"),
                                     ("fine", "notice", "appeal", "letter", "paid", "debt",
                                      "court", "keeper", "windscreen", "ticket", "tickets")),
          "A private car park's 'fine' is a parking charge notice: an invoice from the company, not "
          "a council ticket, and ignoring it is how it becomes a court claim. Appeal to the "
          "operator inside 28 days with photos and the signs as they were, and if they turn you "
          "down they must give you a code for a free appeal to POPLA or the IAS. Overstaying is "
          "only chargeable if the signs were clear and the amount is a genuine estimate of their "
          "loss.",

          # a council ticket on the street or in a council car park is the parking-ticket answer
          ask=("private", "parking charge", "pcn", "popla", "anpr", "overstayed", "overstay",
               "camera", "parkingeye", "apcoa"),
          # the council's ticket is lifeadmin's table and it reads "pcn" too: the private
          # company's invoice is this answer, so the tie goes here
          bias=1,
          avoid=("council", "traffic warden", "yellow line", "double yellow", "residents bay",
                 "bus lane", "congestion charge", "ulez", "tow", "towed", "clamped")),
    entry("return-lost-in-post", (("sent it back", "sent it back and", "returned it and",
                                    "return never arrived", "return got lost", "return is lost",
                                    "says it never arrived", "says they never got it",
                                    "never received my return", "lost my return",
                                    "proof of postage", "returned it by post"),
                                   ("returned", "return", "posted", "post office", "courier",
                                    "tracking", "postage", "never arrived", "never got it",
                                    "never received", "didnt arrive")),
          "Who carries the risk depends on how you sent it: with the retailer's own returns label "
          "or a collection they arranged, the parcel is theirs from the moment it is handed over, "
          "so send the proof of postage and ask for the refund within 14 days. With your own "
          "courier you carry the risk until it arrives, so claim on that courier's insurance and "
          "keep the receipt. Either way do not reorder until they answer in writing.",
          # a parcel that never came to you is the missing parcel, and a repair is the shop's
          ask=("sent it back", "returned", "return", "posted", "postage"),
          avoid=("never arrived today", "my parcel", "my order", "not delivered to me",
                 "where is my order", "repair", "in for repair")),
    entry("booking-something", (("book a table", "book a meal", "book a meal out",
                                "book a restaurant", "book a dinner", "book a lunch",
                                "book a haircut",
                                "book a viewing", "book a taxi", "book a takeaway",
                                "book an appointment", "book my appointment", "reserve a table",
                                "reservation", "a table for", "table for two", "table for four",
                                "table for 4", "table for 2", "book a slot", "book online",
                                "a table free", "table free", "any tables", "is there a table",
                                "table available", "tables available", "space for two",
                                "get a table",
                                # "how do i book a restaurant" names the restaurant, not the
                                # table, and the football card in sport.py was taking it
                                "book a restaurant", "restaurant booking",
                                "restaurant reservation", "restaurant for", "book lunch",
                                "book dinner", "book a meal out",
                                # "do i have to book in advance" and "can i just turn up" ask
                                # whether a booking is needed, which is this row's answer and
                                # not a book to read: the books row keys "book" and was taking
                                # "can i just turn up or do i need to book"
                                "do i need to book", "do i have to book", "need to book",
                                "have to book", "needs booking", "book in advance", "book ahead",
                                "booking needed", "booking required", "need a reservation",
                                "just turn up", "turn up or", "walk in", "walk in or",
                                "have to reserve", "must i book",
                                # A booking that is already made is asked about, not described,
                                # and it has an answer of its own: "is my booking confirmed" gets
                                # "the booking lives with them - the email has the time" from the
                                # status row. So no phrase for it here: "booking confirmed",
                                # "booking reference" and "booking number" scored this row over
                                # that one and answered a completed booking with how to ring and
                                # book a table.
                                ),
                               ("book", "booking", "reserve", "reservation", "table", "restaurant",
                                "haircut", "barber", "viewing", "flat", "taxi", "appointment",
                                "tonight", "tomorrow", "friday")),
          # This row answers a table, a viewing and a haircut alike, so it says what all three
          # want and then the one thing that differs. It used to end "A table is usually held 15
          # minutes, so say if you will be late" for a haircut.
          "Ring them rather than using the app if you can: say the day, the time and what it is "
          "for, and ask which card holds the booking and what a cancellation costs before you give "
          "the details. Get a text confirmation in writing. A table is usually held 15 minutes, so "
          "say if you will be late and mention anything that matters - a birthday, a highchair, a "
          "wheelchair; for a haircut or a viewing, ask for the quieter part of the week, when they "
          "can move you. For a table tonight, ring back at lunchtime, when tables come free.",

          # the thing booked, not the booking of it: a cancelled gym, hotel or flight is its own
          # answer, and so is a refund or a fault
          ask=("book", "booking", "reserve", "reservation", "table", "how do i", "can i"),
          avoid=("cancel", "cancelled", "refund", "faulty", "broken", "deposit back",
                 "went bust", "wont refund", "complaint", "complain", "insurance", "flight",
                 "hotel", "gym", "tenancy", "lease", "lost my booking", "lost the booking",
                 # a ferry, a boat and a train are booked somewhere else: the table answer's
                 # "a table is held 15 minutes" is not about them
                 "ferry", "boat", "train", "coach", "cruise", "parking",
                 "lost our booking", "lost my table", "booking was lost", "gave my table away",
                 "they lost")),
    # Moving or dropping a booking is asked about a table, a chair or a slot, and the words
    # "booking" and "booked" are the referee's and a hotel rate's: "how do i change a booking"
    # was a yellow card, "i cant make my booking what do i do" the same, "how do i cancel a
    # restaurant booking" a flight refund, and "how do i cancel a hair appointment" how to wash
    # hair. A restaurant, a hairdresser and a garage all work the same way, so one answer covers
    # them: the notice in the terms is what decides, and moving the date is what keeps a deposit.
    # A booking the other side called off is not a booking you want to move: "the restaurant
    # cancelled my booking" was a refund for a package holiday, and "my barber cancelled on me"
    # was the neutral nod. They owe the deposit back and the same standard elsewhere, and the
    # first thing to do is get it back in writing.
    # "how do i confirm my booking" was answered with the notice you need to cancel. A
    # confirmation is a different thing: it is theirs to send, and it is not a booking until it
    # arrives with a reference on it.
    entry("confirm-a-booking",
          (("confirm", "confirmed", "confirmation", "chase", "chasing", "no confirmation"),
           ("booking", "bookings", "table", "restaurant", "reservation", "appointment",
            "haircut", "barber", "slot", "garage", "viewing")),
          "Ring them and ask them to send the confirmation while you are on the phone: a booking "
          "is only held once they have said yes in writing, with the date, the time and a "
          "reference. If nothing has come back, ring rather than email, and check the spam folder "
          "first - most confirmations arrive within a few minutes of the call.",
          avoid=("flight", "hotel", "train", "tonight", "how do i book", "how to book",
                 "cancel", "cancelled", "change", "move", "refund"),
          ask=("how do i", "how can i", "should i", "do i need", "where is", "i havent"),
          bias=2),
    # "how do i get a refund on a booking" was the faulty-goods card, which is about a broken
    # kettle. Money back on a booking follows the cancellation, so it starts with the notice.
    entry("refund-on-a-booking",
          (("refund", "refunded", "money back", "get my money", "paid a deposit",
            "deposit back", "keep my deposit"),
           ("booking", "bookings", "deposit", "table", "restaurant", "haircut", "barber",
            "appointment", "slot", "garage", "reservation")),
          "Cancel in writing first, because the refund follows the cancellation: say the booking "
          "and the date, ask what the notice was and what they are keeping. A deposit is normally "
          "returned inside the notice they set, on the card you paid with, and a chargeback is "
          "what is left if they stop answering - so keep the confirmation and the messages.",
          # a broken thing, a holiday, a tenancy and a service nobody did are other answers
          avoid=("faulty", "broken", "stopped working", "kettle", "phone", "laptop", "tv",
                 "washing machine", "shop", "online order", "warranty", "guarantee", "package",
                 "holiday", "flight", "hotel", "train", "never turned up", "didnt turn up",
                 # a tenancy deposit is its own body of law and its own rows
                 "landlord", "tenancy", "letting", "letting agent", "rent", "flat", "house",
                 "moving out", "moved out", "end of the tenancy", "agent", "gym", "membership",
                 "utility", "energy", "council tax", "insurance"),
          ask=("how do i", "can i", "should i", "what do i", "am i entitled"),
          # money.py's 30-day law on goods keys a bare "refund" and carries its own weight, so a
          # booking deposit has to match it or the kettle law answers
          bias=3,
          guard=_a_place_that_takes_bookings),
    entry("cancelled-by-them",
          (("cancelled my booking", "cancelled our booking", "cancelled my table",
            "cancelled our table", "cancelled the booking", "cancelled on me",
            "cancelled on us", "cancelled at short notice", "gave our table away",
            "no record of my booking", "no record of our booking", "lost my booking",
            "lost our booking", "turned us away", "cancelled my appointment"),
           ("restaurant", "table", "booking", "haircut", "barber", "salon", "garage",
            "appointment", "slot", "dinner", "meal")),
          "If they cancel, the deposit comes back and they should find you the same thing "
          "elsewhere at their cost: ring, then put it in writing - the booking, the date, what you "
          "paid - and ask what they are offering. Keep the confirmation and the messages, because "
          "a chargeback on the card needs them. If you are out of pocket on something booked "
          "around it, say the figure in the same message.",
          # the booking nobody kept, the job nobody came to do and a train's refund are elsewhere
          avoid=("never turned up", "didnt turn up", "no show", "package", "holiday", "flight",
                 "hotel", "train", "late", "delayed"),
          ask=("cancel", "cancelled", "what can i do", "what do i do", "should i"),
          bias=2,
          guard=_they_are_the_ones_cancelling),
    # "they want a deposit for a table is that normal" was only nodded at, and "can they keep my
    # deposit if i cancel" was a card about a partner who keeps cancelling. A deposit is ordinary
    # at a busy place; what matters is the deadline in the terms.
    entry("deposit-on-a-booking",
          (("deposit", "deposits", "card to hold", "card details", "card hold"),
           ("table", "booking", "restaurant", "slot", "keep", "kept", "refund", "back",
            "normal", "usual", "why", "want", "asking", "asked", "lose", "forfeit")),
          "A deposit held on a table or a slot is normal at a busy place, and it is usually "
          "refundable if you cancel inside the notice they set - a day or two for most "
          "restaurants, longer for a big table. Ask, before you pay, what the deadline is and "
          "whether it comes off the bill, and get that in a reply rather than on the phone.",
          # money held on a job, a tenancy and a holiday are other answers
          avoid=("tenancy", "lease", "landlord", "letting", "rent", "job", "builder", "plumber",
                 "kitchen", "bathroom", "windows", "roof", "car", "van", "skip", "flight",
                 "holiday", "package", "hotel", "gym", "house", "flat", "mortgage", "energy"),
          ask=("is it normal", "normal", "can they", "should i", "why", "how much", "can i get",
               "do i have to"),
          bias=2,
          guard=_a_place_that_takes_bookings),
    # A haircut or a massage you have to book first: "how do i book a haircut appointment" was
    # the first slot at a GP surgery, and "i want to book my first ever massage" was the table.
    entry("book-a-slot",
          (("haircut", "hair cut", "hair appointment", "barber", "barbers", "hairdresser",
            "salon", "nails", "manicure", "pedicure", "waxing", "massage", "facial",
            "hair colour", "colour appointment"),
           ("book", "booking", "appointment", "get in", "walk in", "walk-in", "slot",
            "waiting list", "availability", "reschedule", "change")),
          "Ring them or use their own online booking rather than a message, and take a weekday "
          "morning or the start of the week if you can: those are the quiet slots and the ones "
          "they can move. Say what you want and roughly how long for - a trim or a colour, a "
          "massage, a set of nails - and ask the price before they start. A barber will usually "
          "take a walk-in on a weekday afternoon.",
          avoid=("doctor", "gp", "surgery", "dentist", "dental", "nhs", "hospital", "clinic",
                 "blood test", "prescription", "111", "physio", "optician", "vet"),
          ask=("book", "how do i", "how can i", "where do i", "reschedule", "change"),
          bias=1),
    # last-minute etiquette: "is it rude to cancel last minute" was a card about a partner who
    # keeps cancelling, because "cancellations in a row" is the only reading the tables had.
    entry("calling-off-late",
          # The row is about calling a booking off, so the calling off has to be in the line. The
          # key began with the bare word "rude" beside a venue, which is how "is it rude to leave
          # my phone at dinner" and "is it rude to be on my phone at dinner" were answered "give
          # as much notice as you can - a day is plenty for a table". A manners question about a
          # dinner is not a cancellation, and no venue word can tell the two apart.
          (("cancel", "cancelled", "canceled", "cancelling", "canceling", "call off",
            "calling off", "called off", "no show", "not turning up", "not turn up",
            "last minute", "late notice", "short notice", "drop out", "pull out",
            "dont turn up", "don't turn up"),
           ("rude", "ok", "okay", "polite", "wrong", "fine", "should i", "booking", "table",
            "haircut", "barber", "dinner", "restaurant", "appointment", "meal", "party",
            "cancel", "cancelled", "cancelling", "call off", "calling off", "no show",
            "not turning up", "last minute", "late notice", "short notice")),
          "Give as much notice as you can - a day is plenty for a table, 24 hours for a haircut, "
          "and longer for a big group - and ring rather than not turning up. A call keeps the "
          "goodwill and usually the deposit, and a place that knows in time can fill the table.",
          avoid=("partner", "husband", "wife", "boyfriend", "girlfriend", "relationship",
                 "wedding", "funeral", "flight", "hotel", "train"),
          ask=("is it rude", "rude", "should i", "is it ok", "is it okay", "do i need to"),
          bias=2),
    entry("move-a-booking",
          (("booking", "bookings", "reservation", "reservations", "table booking",
            # "a table" alone is not here: "how do i move a table upstairs" is a piece of
            # furniture going up a stairwell, so the restaurant sense has to be named
            "table reservation", "restaurant table", "my table", "our table",
            "hair appointment", "haircut",
            "barber", "slot", "deposit", "double booked", "booking reference"),
           ("cancel", "cancelled", "canceled", "cancelling", "canceling", "call off",
            "called off", "change", "changed", "changing", "move", "moved", "moving",
            "reschedule", "rescheduled", "postpone", "postponed", "bring forward",
            "wrong date", "wrong day", "wrong time", "cant make", "cannot make", "can't make",
            "dont want to go", "don't want to go", "no longer", "not going to make",
            "give my table away", "change the time", "change our time", "get out of")),
          "Look at the terms on your confirmation, because the notice they ask for is what decides "
          "it: most restaurants, hairdressers and garages want a day's notice and will move you to "
          "another day free, while a deposit on a table or a slot is usually what buys the first "
          "one. Ask in writing with the date, the time and the booking reference, and ring as well "
          "if it is within 24 hours - a phone call is what gets a deposit moved rather than kept. "
          "If they will not move it, ask what the deposit was held for and whether a friend can "
          "take the slot, since a booking nobody used and a table nobody turned up for are not the "
          "same thing.",
          # a flight, a train, a hotel or a club is its own contract with its own answer, and a
          # booking in football is a card
          ask=("cancel", "change", "move", "reschedule", "postpone", "wrong", "deposit", "how",
               "can i", "what do i"),
          avoid=("flight", "flights", "flight only", "airline", "airport", "fly", "flying",
                 "train", "trains", "rail", "ferry", "coach", "hotel", "hotels", "hostel",
                 "b and b", "airbnb", "cottage", "campsite", "pitch", "holiday", "package",
                 "gym", "tenancy", "lease", "landlord", "letting", "yellow card", "red card",
                 "referee", "sent off", "booked for", "football", "match", "player", "penalty",
                 "dentist", "doctor", "gp", "surgery", "practice", "hospital", "clinic",
                 "nurse", "midwife", "nhs", "optician", "physio", "scan", "x-ray", "referral",
                 "blood test", "prescription", "vet", "insurance", "lost my booking",
                 # a booking fee is what a ticket costs, and a cancelled gig is travel's
                 # event-ticket-refund: "the festival was cancelled do i get the booking fee" was
                 # this row on the words "booking" and "cancelled"
                 "booking fee", "festival", "festivals", "gig", "gigs", "concert", "concerts",
                 "ticket", "tickets", "event", "events", "show", "theatre", "cinema",
                 "lost the booking", "they lost", "went bust", "covid",
                 # "move out" and "moving house" are the tenancy's words: "how do i get my
                 # deposit back when i move out" was answered as a restaurant table, and the
                 # deposit rows are the ones that answer a flat.
                 "move out", "moved out", "moving out", "move in", "moved in", "moving in",
                 "moving house", "moved house", "end of tenancy", "deposit scheme",
                 "renting", "rented", "my flat", "the flat", "our flat", "house deposit"),
          # a flight refund, a referee's card and a hotel rate all key the same words and carry
          # their own weight, so this row has to match them or it never gets the line: "i need
          # to cancel my booking" is a table or a garage, not a non-refundable hotel rate
          bias=2),
    entry("no-one-turned-up", (("never turned up", "didnt turn up", "never showed up",
                                "never showed", "never came", "no one came", "nobody came",
                                "didnt come", "didnt show", "no show", "didnt do the job",
                                "never did the job", "never got the service",
                                "service i never got", "paid for nothing", "never happened"),
                               ("paid", "pay", "deposit", "booked", "booking", "plumber",
                                "cleaner", "tradesman", "builder", "electrician", "gardener",
                                "service", "job", "appointment", "course", "lessons", "tutor",
                                "skip", "van",
                                # the person who was coming to fix a machine is a job nobody
                                # came to do too: "the washing machine repair man never turned
                                # up" was answered with the plug fuse and the door switch, which
                                # is what to check when nobody is coming at all
                                "repair man", "repairman", "handyman", "boiler man",
                                "gas engineer", "appliance repair", "locksmith", "removals",
                                "pest control", "roofer", "decorator")),
          "A job nobody came to do is a debt they owe you: put it in writing - what was booked, "
          "the date, what you paid - and ask for the money back within 14 days. If they will not "
          "pay, a card chargeback, Section 75 over £100, then Money Claims Online for about £35 "
          "with no solicitor. Never pay the balance of a job that has not been done, and keep the "
          "messages.",
          # a parcel, a train and a clinic are other answers, and hiring comes before the booking
          ask=("never", "didnt", "no one", "nobody", "paid", "booked", "deposit"),
          avoid=("parcel", "delivery", "courier", "train", "bus", "flight", "airline", "doctor",
                 "dentist", "hospital", "how do i find", "should i pay", "pay up front",
                 "upfront", "lost", "how much should i pay")),
    entry("overcharged-till", (("overcharged", "charged twice", "charged me twice",
                                "double charged", "wrong price", "price at the till",
                                "charged more", "charged me more", "less than they charged",
                                "price on the shelf", "shelf price", "price tag",
                                "marked price", "the ticket said", "different price"),
                               ("shop", "till", "bill", "back", "refund", "supermarket",
                                "restaurant", "cafe", "pub", "menu", "meal", "receipt",
                                "bar", "takeaway", "charged", "charges", "charging")),
          "If the bill charges more than the shelf price or the menu, ask for the difference back: "
          "the price displayed is the price you pay. If they refuse, keep the receipt and a photo "
          "of the label or the menu, complain in writing, then use a chargeback or the small "
          "claims court.",
          # a phone, broadband or energy bill is not a till: those are contracts, not shelf prices
          avoid=("energy", "electricity", "gas", "water", "council tax", "phone", "mobile",
                 "broadband", "internet", "landline", "rent")),
    entry("refund-old-card",
          (("refund", "refunded", "money back", "my money"),
           ("old card", "card is closed", "card closed", "card was closed", "closed my card",
            "card expired", "expired card", "old debit card", "card i paid with",
            "card has been cancelled", "card was cancelled", "cancelled my card",
            "different card", "new card", "lost my card", "card has changed")),
          "A refund goes back to the card you paid with, not to a different one, and it still "
          "works on a closed card: the money lands in the account behind it, so ring the bank and "
          "tell them one is coming. If the account itself is closed they will take it in and pass "
          "it on, sometimes for a fee. If it has not arrived 14 days after the shop says it paid, "
          "ask them for the acquirer reference and raise a chargeback with your card company.",
          # "can i get a refund to a different card" is a method question; the timing of a late
          # refund and the entitlement are other entries.
          avoid=("how long", "late", "still waiting", "not arrived", "how do i ask",
                 "am i entitled", "how much")),
    entry("gift-card-shop-closed",
          (("gift card", "gift cards", "gift voucher", "voucher", "credit note"),
           ("shop closed", "shop has closed", "closed down", "went bust", "gone bust", "folded",
            "in administration", "administrator", "ceased trading", "expire", "expired",
            "expiry", "ran out", "worth", "left on it", "no good", "refuse", "wont take")),
          "A gift card is an unsecured debt of the shop, so if it folds you are near the back of "
          "the queue: register your claim with the administrator the same week, with the card and "
          "the receipt. If you bought the gift card on a credit card for over \u00a3100, the card "
          "company is jointly liable under Section 75, and a chargeback can recover a debit card "
          "payment from the last 120 days. If the chain is only wobbling, spend it now.",

          ask=("shop", "closed", "bust", "folded", "administrat", "expire", "expired", "refuse",
               "wont take", "worth", "use it", "spend", "balance", "left on it"),
          # a voucher offered instead of a refund is the refusal answer's line, and a gift receipt
          # is the gift-return one.
          avoid=("instead of a refund", "instead of refund", "offered me a credit",
                 "gift receipt", "return a gift", "exchange")),
    # A shop that stops trading leaves the person holding a receipt with nobody at the till. The
    # contract survives but the money has to come from the card or from the administrator, and
    # "no refunds" is not the answer to it: "i paid for a wedding dress and the shop closed
    # down" was getting wedding-clothes advice, and "the sofa shop has gone bust" a shrug.
    entry("shop-gone-bust",
          (("went bust", "gone bust", "went under", "gone under", "closed down",
            "company closed", "company has closed", "company went", "the business closed",
            "business has closed", "closed for good", "shut up shop", "has closed",
            "gone out of business", "went out of business", "ceased trading", "stopped trading",
            "no longer trading", "closed its doors", "folded", "shut down",
            "in administration", "into administration", "administrators", "liquidated",
            "liquidation", "liquidators", "called in the administrators"),
           ("paid", "pay", "ordered", "order", "bought", "deposit", "paid up front",
            "paid in advance", "goods", "sofa", "furniture", "kitchen", "dress", "suit",
            "repair", "never got", "havent got", "haven't got", "not arrived",
            "never arrived", "was meant to", "to be delivered", "to be made", "shop",
            # "i paid for a course and the company closed" names the company, not a shop, and a
            # course fee is money in front like any other
            "course", "course fee", "courses", "training", "tuition", "the company",
            "company closed", "company has closed", "the business",
            # "the company went into administration owing me money" names no goods
            "money", "owed", "owing", "owes me", "owe me", "refund", "my money")),
          'Your contract does not die with the shop, but there is nobody at the till to serve it: '
          'the money comes from your card provider, or from the administrator. Paid by credit card '
          'and over £100? Say Section 75; on a debit card, or under £100, ask for a chargeback '
          'within 120 days of the payment, with the receipt and the order email. Register as a '
          'creditor with the administrator too, which is free but usually pays pence in the pound.',
          # a gift card, a package holiday, a cancelled wedding venue, a gym and a closed bank
          # account are each their own answer, and going to court is a later step
          avoid=("gift card", "gift voucher", "voucher", "credit note",
                 # how the payment was made is the card answer's own question, and it says more
                 "credit card", "debit card", "section 75", "s75", "chargeback",
                 "holiday", "package", "flight", "airline", "atol", "travel agent", "cruise",
                 "hotel", "venue", "wedding venue", "gym", "leisure centre", "landlord",
                 "tenancy", "rent", "bank account", "broadband", "energy", "small claims",
                 "take them to court", "sue"),
          bias=2),
    # Food bought past its use-by date is a refund and a report, not a meal to complain about at
    # the table: "the shop sold me an out of date sandwich" was getting a meal-planning answer.
    entry("out-of-date-food",
          (("use by", "use-by", "out of date", "past its date", "past the date", "sell by",
            "expired", "mouldy", "moldy", "mould", "mold", "gone off", "went off", "smells off",
            "smelled off", "green bread", "best before"),
           ("sandwich", "sandwiches", "milk", "chicken", "meat", "yoghurt", "yogurt",
            "bread", "cheese", "salad", "food", "supermarket", "tesco", "asda",
            "sainsbury", "morrisons", "aldi", "lidl", "coop", "waitrose", "packet")),
          "Take it back to the shop with the packet and the receipt and ask for the money back, "
          "and keep the packet: selling food past its use-by date is an offence, so if the shop "
          "is not bothered, report it to the council's environmental health team with a photo of "
          "the label and the date. A use-by date is about safety, so do not eat it, while a "
          "best-before date is only about quality: that one is a refund and nothing worse.",
          # The row is a purchase complaint, so the line has to say it was bought: a loaf that
          # keeps going mouldy on the shelf is the keeping answer next door, and the loose
          # "my"/"i"/"the" ask let it through. "my bread always goes mouldy before i finish it"
          # was a refund; the date words stay, because "my milk went off before the date" is a
          # complaint about a shop even when no shop is named.
          # The refund is for food you bought, so a purchase is the ask. "date", "opened" and
          # "yesterday" were in this list and they are the kitchen's words, not the shop's: "is
          # my milk past its date" and "i opened the yoghurt and it was off" named a date or a
          # packet and got the refund card, whatever the shelf-life rows next door said. The
          # date phrases score nine on their own, so the row cannot be left to the ranking.
          ask=("bought", "buy", "buys", "bought it", "sold", "sell", "shop", "shops",
               "supermarket", "store", "tesco", "asda", "sainsbury", "morrisons", "aldi",
               "lidl", "coop", "waitrose", "refund", "money back", "return", "returns",
               "receipt", "receipts", "take it back", "take back", "take the food back",
               "purchase", "purchased", "delivered", "order", "ordered", "online", "paid",
               "charged", "expired", "expires", "went off before"),
          # a meal out, food that spoiled in a power cut and being ill afterwards are other
          # answers, and a cooking question is not a shop's problem
          avoid=("restaurant", "cafe", "takeaway", "meal", "eat out", "menu", "chef",
                 "waiter", "food poisoning", "sick after", "power cut", "fridge", "freezer",
                 "how do i cook", "recipe", "how long", "leftovers",
                 # a guarantee that has run out is the warranty answer, whatever it says about
                 # a date: "the shop says my guarantee has expired" is not a sandwich
                 "guarantee", "warranty", "warranties", "extended warranty",
                 # whether it is still good to eat is the cooking answer, not the shop's: "how
                 # long does milk last after opening" and "my bread has gone mouldy can i still
                 # eat it" both belong to the food-safety entries next door
                 "how long", "last", "still ok", "still good", "safe to eat", "can i eat",
                 "can i still eat", "still eat", "is it ok", "is it safe", "keep it",
                 "storing", "store it", "how do i store", "bin it",
                 # "how do i stop my bread going mouldy" is a keeping question, and it was a
                 # refund: the spoilage word is in the key and "bread" is too, so a line that
                 # asks how to prevent the spoiling has to stand this row down. The verbs of
                 # prevention, not the states: "mouldy" itself is in the key above.
                 "keep", "keeps", "keeping", "fresh", "fresher", "freshen", "stop", "stops",
                 "prevent", "preventing", "longer", "lasts", "soften"),
          bias=2),
    # A takeaway that never came is a missing order, not a bad meal: the restaurant can refund it
    # in a minute and the app is the slower route.
    entry("takeaway-missing",
          (("takeaway", "take away", "just eat", "justeat", "deliveroo", "uber eats",
            "food delivery", "delivery app", "dominoes", "domino's", "pizza", "curry",
            "kebab", "chinese", "fish and chips", "the restaurant"),
           ("never arrived", "never came", "didnt arrive", "didn't arrive", "not arrived",
            "never turned up", "never showed up", "still waiting", "still not here",
            "no food", "never got it", "havent got it", "haven't got it", "never got my",
            "an hour ago", "two hours ago", "three hours ago", "cancel my order")),
          "Ring the takeaway itself rather than tapping at the app: the restaurant can remake it or "
          "refund you in a minute. If they will not, use the missing-item report in the app the "
          "same day, with a photo of what did arrive, and dispute that amount on the card as a "
          "chargeback if the refund does not come. You do not pay for food you never got, and a "
          "driver who never came is the app's problem, not yours.",

          ask=("my", "the", "i", "we", "it", "order"),
          # a cold or wrong dish is the meal complaint, a supermarket delivery is a parcel, and a
          # recipe has nothing to do with either
          avoid=("cold", "wrong order", "wrong dish", "raw", "undercooked", "recipe",
                 "how do i cook", "book a table", "supermarket", "parcel", "courier"),
          bias=1),
    # A fee added at the last screen, or on top of the price that was quoted, is not something the
    # person owed: "i was charged a booking fee i wasnt told about" was getting hotel-rate advice.
    entry("unexpected-fee",
          (("booking fee", "admin fee", "administration fee", "service fee", "processing fee",
            "card fee", "surcharge", "hidden fee", "hidden charge", "extra fee",
            "extra charge", "handling fee", "convenience fee", "drip pricing",
            # a fee for something that never happened: "charged a cancellation fee for a table
            # i never booked", "a no-show fee for an appointment i did turn up to"
            "cancellation fee", "cancellation charge", "cancelation fee", "no show fee",
            "late fee", "cleaning fee",
            # a delivery charge on an order that said free delivery is the same surprise
            "delivery charge", "delivery fee", "shipping fee", "postage charge",
            "charged for delivery", "free delivery"),
           ("wasnt told", "wasn't told", "not told", "didnt know", "didn't know",
            "not in the price", "on top of the price", "at the end", "at checkout",
            "surprise", "unexpected", "hidden", "added", "added on", "charged me",
            "i never agreed", "never agreed to",
            "never booked", "didnt book", "didn't book", "never made", "didnt make",
            "didn't make", "never happened", "did turn up", "i was there", "never signed",
            "never asked for", "didnt ask", "didn't ask", "charge", "charged",
            "i cancelled", "i canceled", "in time", "in advance", "with notice",
            "gave notice")),
          _fee_reply,
          ask=("my", "the", "i", "we", "they", "it", "added", "charged"),
          # a hotel bill, an energy bill, a bank charge and a letting agent's fee are each their
          # own answer, and a flight or holiday has its own fees and taxes
          avoid=("hotel", "minibar", "room service", "energy", "gas bill", "electricity",
                 "water bill", "bank", "overdraft", "flight", "airline", "holiday",
                 "letting agent", "tenancy", "landlord", "rent", "pension", "tax"),
          bias=1),
    # "what is a booking fee" and "is a booking fee refundable" were a punt either way, while the
    # surprise-fee row above answers only the fee that was sprung on somebody. The definition and
    # the refund question are the plain ask, and they name the fee itself with no "wasnt told".
    entry("booking-fee",
          (("booking fee", "booking fees", "booking fee back", "admin fee", "administration fee",
            "service fee", "service fees", "cleaning fee", "convenience fee", "processing fee",
            "cancellation fee", "cancellation charge", "cancelation fee", "cancelation charge",
            "no show fee", "no-show fee", "late fee", "late charge", "late payment fee",
            "late payment charge", "transaction fee", "handling fee"),
           ("what is", "whats", "what are", "what does", "why", "refundable", "non refundable",
            "refunded", "not refunded", "get it back", "get my", "legal", "allowed", "can i",
            "do i pay", "do you pay", "should i pay", "have to pay", "how much", "explain",
            "mean", "means", "worth it")),
          _fee_kind_reply,
          ask=("my", "the", "i", "we", "it", "is", "are", "a"),
          # a fee for something that never happened or was never disclosed is the row above, and a
          # ticket, a flight, a hotel rate or a tenancy has its own fees
          avoid=("never told", "wasnt told", "wasn't told", "never booked", "never happened",
                 # a fee somebody is already disputing is the surprise-fee row's line: "why am i
                 # being charged a booking fee" wants what to do about it, not a definition
                 "why am i being charged", "why have i been charged", "why was i charged",
                 "why am i charged", "why do i have to pay", "charged a fee i",
                 "ticket", "concert", "gig", "festival", "flight", "airline", "hotel",
                 "holiday", "tenancy", "landlord", "letting", "letting agent", "agent",
                 "rent", "energy", "bank",
                 # a card fee abroad is exchange-rate advice for the travel-card row, and an
                 # admin fee on a payslip or in a wage packet is a deduction, not a booking:
                 # "how much is a card fee abroad", "why is there an admin fee on my payslip" and
                 # "how much is the admin fee for a letting agent" were all told what a booking fee
                 # is, because `admin fee` and `how much` reach this key on their own.
                 "abroad", "overseas", "currency", "exchange rate", "atm", "cash machine",
                 "payslip", "pay slip", "wages", "salary", "deduction", "deductions"),
          bias=1),
    entry("order-cancelled-by-shop",
          (("shop", "store", "retailer", "seller", "company", "amazon", "argos", "currys",
            "john lewis", "very", "littlewoods", "online shop", "website", "they"),
           ("cancelled my order", "cancelled the order", "cancelled our order",
            "cancelled my delivery", "called off my order", "called off the order",
            "cancelled it", "cancelled and", "out of stock", "cannot fulfil", "cant fulfil",
            "cannot supply", "cant supply", "wont honour", "wont honour my order",
            "refused to honour")),
          "If the shop cannot supply what you ordered the money comes back in full, and you are not "
          "asking a favour: a shop that cancels owes a full refund within 14 days, delivery "
          "included, and one that cannot say when stock is back owes it as soon as you cancel. Ask "
          "in writing with the order number; if they stall, your card provider can charge the "
          "payment back with that email as proof.",

          # a flight, a holiday, a booking, an appointment and a repair are each their own answer;
          # so is a delivery that is merely late, which is a date promised and not yet met
          avoid=("flight", "airline", "holiday", "hotel", "package", "venue", "concert", "ticket",
                 "wedding", "train", "ferry", "coach", "appointment", "dentist", "doctor",
                 "hospital", "haircut", "hairdresser", "table", "restaurant", "takeaway",
                 "booking", "deposit", "faulty", "broken", "damaged", "late", "delayed",
                 "hasnt arrived", "hasn't arrived",
                 "still waiting",
                 "not arrived", "when will", "tracking"),
          bias=3),
    entry("price-rise", (("price rise", "bill went up", "price went up", "prices went up",
                          "went up mid contract", "raised my bill", "increased my bill",
                          "put my bill up", "bill has gone up", "bill keeps going up",
                          "price goes up", "prices go up", "rises mid contract"),
                         ("contract", "broadband", "phone", "internet", "provider", "plan",
                          "tariff", "mid contract", "leave", "cancel", "get out")),
          "A mid-contract rise that was not in the terms you signed is a change you can refuse: "
          "tell them in writing within 30 days of the notice that you are leaving, on that date, "
          "and you owe nothing after it. A rise written into the contract has to follow the "
          "wording exactly, and they must tell you personally in advance, not on the website.",
          # a rise is the subject itself, so it needs no ask word; "why" is the bill-size answer
          # a bill that is simply high or odd is the money domain's answer
          avoid=("why", "compare", "cheaper", "save money", "worth it", "energy", "gas",
                 "electric", "electricity", "water", "rent",
                 # a phone, broadband or telly bill that went up is the retention-price card's
                 # question, and this one was taking "my phone bill went up again" from it
                 "phone bill", "mobile bill", "broadband bill", "internet bill", "tv bill",
                 "sky bill", "landline bill"),
          bias=2),
    entry("broadband-cancel", (("broadband", "fibre", "internet", "internet provider", "wifi",
                                "router"),
                               ("cancel", "cancelling", "switch", "leave", "end", "get out",
                                "provider", "moving house", "keep charging", "keeps charging",
                                "still charging", "charged after", "charging me")),
          "Find the end date of your minimum term on the bill: out of contract it is 30 days' "
          "notice, in contract you owe the rest unless the price went up mid-term or the line does "
          "not work. Ask for the cancellation date and the final bill by email, and switch to the "
          "new provider the same day. If a payment still goes out after the date they confirmed, "
          "ask the bank for the direct debit indemnity.",

          # "how do i cancel my broadband" is the same shape as a phone contract, but a PAC code
          # and a mobile number are not part of it, and a broadband bill is not a phone bill
          ask=("cancel", "cancelling", "cancellation", "switch", "get out", "can i leave",
               "how do i", "how can i"),
          # a bill that is wrong is a complaint, not a cancellation; the phone is not a broadband
          avoid=("complain", "complaint", "ombudsman", "dispute", "not working", "keeps dropping",
                 "slow", "unusable"),
          bias=1),
    entry("phone-cancel", (("phone contract", "mobile contract", "phone", "mobile", "sim",
                            "pay as you go"),
                           ("cancel", "cancelling", "end", "leave", "get out", "switch",
                            "move house", "stop paying")),
          "Find the end date of your minimum term on the bill first: out of contract you give 30 "
          "days' notice, in contract you owe the rest unless the price went up mid-term or the "
          "service does not work. Ask for the cancellation date and the final bill by email, keep "
          "paying by direct debit until that final bill is settled, and ask for a PAC code if you "
          "want to keep the number.",
          # "how do i cancel my phone contract" is not a complaint: the deadlock-letter entry
          # below answers disputes, and this one answers leaving.
          # the ask has to be about leaving, not just the word "leave": "is it bad to leave
          # my phone charging overnight" is a battery question, not a contract one.
          ask=("cancel", "cancelling", "cancellation", "get out", "switch", "stop paying",
               "can i leave", "how do i leave", "end my contract", "end the contract",
               "how do i", "how can i"),
          avoid=("complain", "complaint", "unfair", "deadlock", "ombudsman", "dispute",
                 "broadband", "fibre", "wifi", "router", "internet",
                 "they won't", "they wont", "charged me", "not working", "unusable", "fault",
                 "died", "died in", "passed away", "bereavement", "charging", "charge overnight",
                 "battery", "screen")),
    entry("broadband-speed", (("slower than advertised", "slower than promised",
                                "slower than i pay for", "slower than i should",
                                "not getting the speed", "not the speed i pay for",
                                "guaranteed speed", "guaranteed minimum", "minimum speed",
                                "half the speed", "pay for 100", "pay for 200", "pay for 500",
                                "below what", "way below", "not as fast as", "much slower",
                                "500mb", "900mb"),
                               ("broadband", "internet", "wifi", "wi fi", "fibre", "mbps", "mb",
                                "provider", "sky", "virgin", "bt", "talktalk", "vodafone",
                                "plusnet", "contract", "speed")),
          "Test it with a cable into the router and keep the numbers: the speed at sign-up is a "
          "guaranteed minimum, and under Ofcom's code the provider has 30 days to fix it once you "
          "report it falling short on three days running. Send those readings in writing as a "
          "complaint, and if it is not fixed you can leave without a penalty and claim back the "
          "shortfall. Unresolved after 8 weeks, the Communications Ombudsman is free.",

          ask=("slower", "speed", "mbps", "minimum", "guaranteed", "half", "not getting",
               "100mb", "500mb"),
          # a cancellation, a repair question and a wifi problem in the house are other answers
          avoid=("how do i cancel", "how can i cancel", "cancel my", "cancel the",
                 "whole house", "booster", "mesh", "extender", "how do i fix",
                 # a wifi that drops out is the home diagnosis, not a contract remedy
                 "keeps dropping", "dropping out", "drops out", "keeps cutting out")),
    entry("mobile-contract", (("broadband", "phone contract", "mobile contract", "internet provider",
                               "provider"),
                              ("cancel", "complaint", "complain", "slow", "not working", "charge",
                               "fee", "leave", "contract")),
          "Complain to the provider first and ask for a deadlock letter if it isn't fixed; phone "
          "and broadband disputes then go free to an independent ombudsman. If the service is "
          "unusable and you're in contract, most providers have to let you leave without a fee.",
          # A contract to close after a death is a bereavement question, not a complaint: the
          # death entry answers it, and a "deadlock letter" reply would be cold and wrong.
          avoid=("died", "passed away", "funeral", "bereave", "we lost", "lost my", "when she",
                 "when he", "estate", "probate",
                 # "how do i cancel her phone contract" after a death in the chat is the
                 # bereavement entry's job, or a warm hedge: a complaint letter is not.
                 "her contract", "his contract", "their contract", "her phone", "his phone",
                 "her account", "his account", "her mobile", "his mobile")),
    entry("cancel-after-a-death", (("died", "passed away", "passed", "bereavement", "funeral",
                                    "death", "probate", "estate",
                                    # "my late mother" is the same line without the word died
                                    "my late", "late mother", "late father", "late mum",
                                    "late dad", "late husband", "late wife", "late partner"),
                                   ("contract", "phone", "bill", "bills", "account", "cancel",
                                    "close", "energy", "bank", "subscription", "mobile", "broadband")),
          # A phone, energy or bank account in someone's name is closed through that company's
          # bereavement team, from the date of death, with no early-exit fee.
          ("Most companies have a bereavement team: ring them, say the account holder has died and "
           "they close the account from the date of death without an early-exit fee, and they can "
           "usually stop the bills from that day. Send the death certificate when they ask; with a "
           "phone or energy account you can ask them to move the number or the supply to you "
           "instead. Sorry you have to deal with this on top of everything else."),
          # A device dies too: "my phone died last night" is a flat battery, not a bereavement.
          avoid=("phone died", "phone's died", "battery died", "laptop died", "car died",
                 # the same question in the tense people use for a dead handset:
                 # "my phone has died" was this card, with a bereavement team for a flat battery
                 "phone has died", "phone is dead", "phone has died on me", "handset has died",
                 "handset died", "battery has died", "laptop has died", "car has died",
                 "it has died", "it just died", "it died last night", "has died on me",
                 # "i got my daughter a phone and it died": the subject of "died" is "it", and
                 # the thing is what the line is about.
                 "and it died", "it just died", "and it dies",
                 "engine died", "died on me", "died on the way", "died laughing", "died down",
                 # a living relative's account is a normal cancellation, not this
                 "wants to", "asked me to", "she wants", "he wants", "is moving", "moving abroad"),
          bias=1),

    # --- the money and the paperwork ------------------------------------------
    entry("tenancy-early", (("tenancy", "tenancy agreement", "lease", "renting", "tenant",
                             # "what is a break clause" was answered by the grammar card ("A
                             # clause is a group of words with its own verb and subject"), and
                             # "how much notice do i give to leave my flat" was a shrug: both name
                             # the thing itself and no tenancy word at all.
                             "break clause", "notice period", "notice to leave",
                             "notice to quit", "give notice", "notice", "leave my flat",
                             "leave the flat", "move out early", "leaving early"),
                            ("end early", "leave early", "get out", "break clause", "surrender",
                             "move out", "break the lease", "break my lease", "break my tenancy",
                             "get out of my lease", "end the tenancy",
                             "moving out early", "early", "before the end", "leave",
                             "get out of it", "can i go",
                             # "what is the notice period on a tenancy" names the tenancy in the
                             # subject and nothing the row held: the tenancy words are the second
                             # signal when the subject is the notice itself
                             "tenancy", "tenancies", "tenant", "tenants", "lease", "flat",
                             "flats", "renting",
                             # and the notice the other way round: "how much notice must a
                             # landlord give a tenant" is the same right read from the tenant's
                             # side, and the reply already says who gives what
                             "landlord", "landlords", "landlady")),
          "Read your tenancy for a break clause first: it is the term that lets either side end "
          "the tenancy before the fixed term is up, and it names the date it can be used and how "
          "much notice it takes, often two months. Without one the landlord only has to agree if "
          "you cover the rent until a new tenant moves in, so offer to find one and put that in "
          "writing - you cannot usually just hand back the keys. On a rolling monthly tenancy in "
          "England you give one month's notice and the landlord gives two, and it has to end on "
          "the day the rent is due.",
          # The row is about leaving before the end, so one of those words has to be there: the
          # tenancy words alone made it answer "what is a tenancy agreement", which is the
          # definition question and belongs to lifeadmin's tenancy-copy.
          guard=_the_notice_is_theirs_to_give,
          ask=("break", "notice", "leave", "leaves", "leaving", "early", "end", "ends",
               "ending", "surrender", "move out", "moving out", "get out", "getting out",
               "can i go", "before the end", "give up"),
          # "nobody would notice if i left early" was taken by this row on the word "left":
          # a line about going unnoticed is not a question about a tenancy.
          avoid=("nobody would notice", "no one would notice", "nobody notices",
                 "no one notices", "if i left", "i left early", "leaves early",
                 "left the house",
                 "deposit", "boiler", "repairs", "landlord won't", "landlord wont", "evict",
                 "eviction", "section 21", "damp", "mould", "problems", "complaint",
                 # writing to the landlord to say you are going is the notice letter, not the
                 # break clause: "how much notice do i need to give my landlord before moving
                 # out" was this row on the words "notice" and "moving out".
                 "notice letter", "im leaving on", "i am leaving on", "hand back the keys",
                 # "do i need to tell the council when i move out" is the moving-house list,
                 # not an argument with the landlord about the fixed term
                 "council", "council tax", "gp", "doctor", "royal mail", "redirect",
                 "change of address", "meter", "meters", "bins")),
    entry("consumer-insurance-claim", (("insurance", "insurer", "policy", "contents cover", "buildings cover",
                               "home insurance", "contents insurance", "burgled", "burglary",
                               "broken into"),
                              ("claim", "claiming", "how do i", "water leak", "flood", "burgled",
                               "burglary", "stolen", "damage", "fire", "house", "home", "flat",
                               "what do i do")),
          "Tell the insurer as soon as you can, before you throw anything away: keep the damaged "
          "item, take photos, and photograph anything that proves what it was worth. They send a "
          "loss adjuster for anything large, and the first thing they check is whether you said "
          "yes to the right cover, so have the receipts or the bank statements ready.",
          avoid=("national insurance", "ni number", "nino", "insurance number", "national insurance number",
                 "refused", "won't pay", "wont pay", "rejected", "not paying", "turned down",
                 "car insurance", "pet insurance", "travel insurance", "gym", "phone insurance",
                 "health insurance", "cheapest", "compare", "worth it",
                 "how much is", "how much does", "how much would", "quote", "quotes",
                 # a policy document is a thing to read and revise, not a claim to make
                 "revise", "revising", "read", "reading", "write", "writing", "essay", "exam",
                 "document", "documents", "renew", "renewal", "quote", "compare",
                 # a premium that went up after a claim asks about the price, not the claim
                 "premium went up", "premium has gone up", "put my premium", "premium up",
                 "no claims", "no-claims", "went up after")),
    entry("consumer-car-hire", (("car hire", "hire car", "rental car", "car rental", "rental company",
                        "hire company", "excess", "hire deposit", "rental deposit"),
                       ("damage", "damaged", "scratch", "scratched", "dented", "charged",
                        "deposit", "excess", "claim", "photo", "photos", "not returned")),
          "Photograph every panel, the wheels, the roof and the fuel gauge before you drive off, "
          "and walk round it on video: a hire company that charges for damage later has to show the "
          "damage was not there when the car went back. Pay with a credit card, because a charge "
          "over £100 gives you a claim against the card company, and ask for the damage report and "
          "their photos in writing before you dispute it.",
          # choosing a hire car is a different question, and the price comparison answer owns it
          avoid=("best", "cheap", "cheapest", "compare", "worth it", "which car", "book early",
                 "abroad", "under 25", "young driver"),
          bias=2),
    entry("holiday-theft",
          # a bag taken by a thief on holiday is not the airline's baggage claim, and it is not a
          # shrug either: the police report is what the insurer and the consulate both want.
          (("stolen", "stole", "robbed", "robbery", "mugged", "mugging", "pickpocket",
            "pickpocketed", "pickpockets", "snatched", "theft", "someone took", "taken from my"),
           ("holiday", "holidays", "abroad", "overseas", "beach", "hotel", "hotel room", "resort",
            "vacation", "trip", "travelling", "traveling", "while away", "in greece", "in spain",
            "in italy", "in turkey", "in france", "in portugal", "in egypt", "in mexico")),
          "Report it to the local police the same day and ask for a written report with a crime "
          "number: insurers and the consulate both want one, and some forces will not give it "
          "later. Then ring your insurer's 24-hour line, cancel any cards that were in the bag, and "
          "if the passport has gone book an emergency travel document at the nearest consulate. "
          "Keep receipts for what you had to buy.",

          ask=("stolen", "stole", "robbed", "robbery", "mugged", "mugging", "pickpocket",
               "pickpocketed", "snatched", "theft", "someone took", "taken from my"),
          avoid=("airline", "baggage desk", "at the airport", "carousel", "flight", "check in",
                 "check-in", "left luggage", "lost property", "locker",
                 # a thing taken from a hotel room is the hotel's own liability card, which has
                 # the £50 an item rule, the safe-keeping receipt and the crime reference in it:
                 # the police-report-and-insurer card is for a bag taken out in the street
                 "hotel room", "from my hotel", "in my hotel", "the hotel room", "room safe",
                 "hotel safe",
                 # a stolen passport is the emergency-document answer's line, which says what to
                 # do about the passport first and the police report second
                 "passport", "passports"),
          # it ties with the airline's baggage entry and the lost-card entry word for word, and
          # a thief on holiday is neither of those questions
          bias=2),
    entry("broken-bag", (("bag", "bags", "handbag", "suitcase", "rucksack", "backpack",
                          "holdall", "buggy", "pushchair", "pram"),
                         ("broke", "broken", "snapped", "split", "torn", "ripped", "ripping",
                          "came apart", "come apart", "fell off", "hanging off",
                          "wont zip", "won't zip", "wont close", "wont do up",
                          "stuck", "sticking", "jammed", "zip", "strap", "lining", "wheel",
                          "wheels", "handle", "hole")),
          "A zip, a strap, a lining or a wheel is usually a repair rather than a replacement: a "
          "cobbler, a luggage repair shop or a pram and nursery repairer puts in a new zip or "
          "strap for much less than the thing cost, and a slider that has split often only needs "
          "a new slider. If you bought it in the last six months the shop that sold it has to "
          "repair or replace it, because the fault is assumed to have been there when it was "
          "sold; after that, look at the maker's warranty, because bags, suitcases and prams are "
          "often covered for their zips and wheels for several years.",
          # the airport and the airline own their own bags: a bag that was on a plane is the
          # baggage desk's, and a bag that has gone is a claim, not a repair
          avoid=("airport", "flight", "flights", "airline", "airlines", "plane", "carousel",
                 "checked in", "checked bag", "boarding", "travel", "holiday", "holidays",
                 "abroad", "overseas", "trip", "lost", "missing", "stolen", "delayed",
                 "compensation", "pir",
                 # buying one, choosing one or packing one is a different question
                 "how do i pack", "packing", "which bag", "what bag", "best bag", "worth it",
                 "buy a bag", "buying a bag", "how much is a bag", "should i get",
                 # "bag" is the word for a bin liner and a tea bag as well as one you carry, and
                 # "split" is what a bag of sugar does: a list of these reached a cobbler's
                 # answer, so the bag in this row has to be a thing with a zip, a strap or a wheel
                 "bin bag", "bin bags", "bin liner", "bin liners", "rubbish bag", "rubbish sack",
                 "tea bag", "tea bags", "teabag", "teabags", "carrier bag", "carrier bags",
                 "shopping bag", "plastic bag", "freezer bag", "sandwich bag", "sandwich bags",
                 "doggy bag", "piping bag", "hot water bottle", "bag of", "bags of",
                 "sugar", "flour", "rice")),
    entry("baggage-lost", (("baggage", "luggage", "suitcase", "bags", "case", "rucksack",
                            "buggy", "pushchair", "pram", "wheelchair",
                            # "bag" in the singular: "my bag came out torn at the airport" is the
                            # same bag as "my bags were damaged", and the guard is what keeps a
                            # bag that broke at home away from the baggage desk
                            "bag", "holdall", "duffel", "duffle", "travel bag", "flight bag"),
                           ("lost", "missing", "delayed", "didn't arrive", "didnt arrive",
                            "never arrived", "damaged", "stolen", "compensation", "broke",
                            "broken", "smashed", "ripped", "crushed",
                            # What the person watches at the belt: "my suitcase never came out"
                            # was a shrug, because the row wanted "didnt arrive".
                            "never came out", "didnt come out", "didn't come out",
                            "didnt come off", "didn't come off", "never turned up",
                            "didnt turn up", "didn't turn up", "not on the carousel",
                            "still not arrived", "went missing",
                            # how a bag comes back off the belt, rather than that it is gone:
                            # torn, torn open, cracked, and the wheel or the handle left behind
                            "torn", "tore", "torn open", "ripped open", "split", "split open",
                            "cracked", "ruined", "wrecked", "wheel", "wheels", "handle", "zip",
                            "came apart")),
          "Report it at the airport before you leave, at the airline's baggage desk: you get a PIR "
          "reference, and nothing is paid without one. Then claim in writing - 7 days for damage, "
          "21 for a delay - and the airline owes up to about £1,300 per passenger, plus what you "
          "had to spend on essentials with the receipts.",
          avoid=("pack", "packing", "packed", "hand luggage only", "carry on", "carry-on",
                 "bus", "coach", "train", "ferry", "ship", "cruise", "taxi",
                 "hotel", "hostel", "left luggage", "left it in",
                 # a bag taken by a thief is the holiday-theft answer, not the airline's
                 "robbed", "pickpocket", "pickpocketed", "mugged", "mugging", "snatched",
                 "theft", "someone took"),
          # a bag that has broken at home is not a claim at an airline's baggage desk
          guard=_a_bag_at_the_airport),
    entry("hotel-lost-property", (("hotel", "hostel", "guest house", "b&b", "bed and breakfast",
                                   "guesthouse", "the room", "reception", "my room"),
                                  ("lost", "missing", "went missing", "gone missing", "stolen",
                                   "disappeared", "left it behind", "left behind",
                                   "cant find", "can't find",
                                   # a thing taken out of the room is the same claim, and
                                   # people say it with "took": "someone took my wallet from my
                                   # hotel room" was a shrug
                                   "took", "taken", "stole", "stole it", "nicked", "pinched")),
          "Report it to reception in writing the moment you notice and ask for a copy of the "
          "report. A hotel in England and Wales is only liable for up to \u00a350 an item and \u00a3100 in "
          "all, and only for their carelessness, so valuables are covered only if you handed them "
          "in for safe keeping and got a receipt. If something was taken from the room, get a crime "
          "reference and claim on your travel or home insurance.",

          bias=1,
          ask=("my", "the", "i", "we", "lost", "stolen"),
          avoid=("how do i find a hotel", "book a hotel", "how much is a hotel", "airline",
                 "airport", "flight", "cancelled", "noise", "dirty", "parking",
                 "check in", "check out", "left luggage",
                 # "took" is also what a hotel does with money: a deposit it keeps or a
                 # payment it takes twice is the refund answer, not this one
                 "deposit", "deposits", "payment", "paid twice", "charged", "charge",
                 "bill", "refund", "overcharged")),
    entry("consumer-app-refund", (("app", "apps", "app store", "google play", "in app purchase",
                          "subscription i never", "game"),
                         ("charged", "charge", "refund", "money back", "downloaded", "bought",
                          "purchase", "ordered by mistake", "didn't buy", "didnt buy",
                          "never downloaded", "never ordered", "cancel")),
          "Ask the store, not the app: Apple and Google both refund accidental and unwanted "
          "purchases themselves, and the app can only point you back at them. Use the store's "
          "report-a-problem page, name the order and say whether a child made the purchase, and "
          "ask within 14 days. If the store says no, a card chargeback is the next step.",
          # a phone game that is broken is faulty goods, and a subscription to cancel is a
          # cancellation with its own steps
          avoid=("faulty", "broken", "doesnt work", "doesn't work", "not working", "stopped working",
                 "wont load", "wont open", "crash", "crashes", "kids", "child", "son", "daughter",
                 "i want to cancel", "how do i cancel", "cancel my subscription",
                 # asking how to install or choose an app is not a billing question
                 "how do i download", "how do i install", "how do i set up", "how do i update",
                 "which app", "best app", "how do i use")),
    entry("card-swallowed", (("cash machine", "atm", "hole in the wall", "cashpoint"),
                             ("ate my card", "swallowed", "kept my card", "took my card",
                              "no cash", "didnt give", "didn't give", "no money", "wrong amount",
                              "didnt come out", "didn't come out")),
          "Ring the number on the machine or your bank straight away and tell them the machine "
          "kept the card: the bank cancels it and sends a new one, usually within a week. If the "
          "machine took the card but did not give the cash, say that too, because the account "
          "often still shows the withdrawal and the bank has to correct it.",
          bias=1),
    entry("tradesman-damage", (("plumber", "electrician", "builder", "roofer", "tradesman",
                                "installer", "decorator"),
                               ("flooded", "damaged", "damage", "broke", "leak", "leaking",
                                "ruined", "cracked", "made it worse", "messed up")),
          "Photograph everything before it is cleared up and tell the tradesman in writing the "
          "same day, with the cost of putting it right: most have public liability insurance, and "
          "that is what pays. If they are not insured or deny it, your own home insurance may cover "
          "it and claim it back from them, and Money Claims Online takes the rest.",
          # a job left half done is the unfinished-job answer
          avoid=("half done", "half finished", "walked off", "never came back", "didnt finish",
                 "didn't finish", "unfinished", "deposit", "quote", "how much"),
          bias=1),
    entry("bank-transfer-scam", (("bank transfer", "transferred", "paid by transfer", "sent the money",
                                  "faster payment", "wire", "transfer"),
                                 ("scam", "scammed", "fraud", "fake", "never arrived", "didn't arrive",
                                  "didnt arrive", "got nothing", "back", "refund", "recover",
                                  # nobody says "scam": they say the seller went quiet with the
                                  # money. "i paid by bank transfer and they vanished" was a shrug.
                                  "vanished", "disappeared", "gone", "went quiet", "ghosted",
                                  "stopped replying", "stopped answering", "wont answer",
                                  "won't answer", "wont reply", "won't reply", "blocked me",
                                  "took my money", "never sent", "no item", "never came",
                                  "never turned up", "not as described", "nothing back")),
          "Ring your bank's fraud line the same day and say the payment was a scam: since October "
          "2024 UK banks have to refund authorised push-payment fraud up to £85,000, with £100 off "
          "the top, and speed is what decides these claims. Report it to Action Fraud too, give "
          "the police the reference, and keep every message from the seller.",
          avoid=("should i", "is it safe", "safe to", "is it legit", "legit", "cheap flights",
                 # money sent to the wrong account by mistake is a recall, not a scam
                 "wrong account", "wrong bank account", "wrong sort code", "wrong number",
                 "wrong person", "mistaken", "by mistake", "accidentally", "by accident")),
    # "is this shop a scam" was a shrug and "is this online shop trustworthy" a search hedge,
    # because every scam row in the pack starts after the money has gone. Checking a trader before
    # you pay is its own job: the same four checks answer it whichever way the doubt is worded.
# A web address is its own question: "is this website a scam" and "how do i know if a website is
# fake" are answered better by the lookalike-domain advice - hover the link, read the real
# address, rnicrosoft.com - than by a checklist for a trader you are about to pay. The shop card
# is for the shop, the store, the company or the trader; a bare website or site with no trader in
# the line stands it down. (Reviewer's point on this PR: the shop card had taken the phishing
# shapes.)

    # Money sent to the wrong account by mistake is a recall, not a scam: nothing was stolen, so
    # the crime route does not fit, and "i transferred money to the wrong account" was getting
    # the send-money-abroad answer about exchange rates.
    entry("wrong-account-transfer",
          (("wrong account", "wrong bank account", "wrong sort code", "wrong account number",
            "wrong person", "mistaken payment", "paid the wrong", "transferred to the wrong",
            "sent it to the wrong", "sent them to the wrong", "typed the wrong",
            "by mistake", "accidentally transferred", "accidentally sent",
            "accidentally paid", "mistake with the account"),
           ("money", "transfer", "transferred", "bank", "payment", "paid", "sent",
            "faster payment", "account", "sort code", "recipient")),
          "Ring your bank the same day and ask them to recall it: a faster payment cannot be pulled "
          "back, so your bank has to ask the receiving bank, which needs the recipient's "
          "permission. Ask them to write to the other bank anyway and to give you their details for "
          "a claim, and if the recipient will not hand it back, a money claim online is the route "
          "with the refusal in writing. Never pay anyone who offers to get it back: that is the "
          "recovery scam.",


          # a payment made to a scammer is the fraud answer, and sending money abroad is a
          # different question about rates and fees
          avoid=("scam", "scammed", "fraud", "fake", "never arrived", "didnt arrive",
                 "didn't arrive", "seller", "sent money abroad", "send money abroad",
                 "abroad", "holiday", "currency", "exchange rate", "wise", "revolut",
                 "euro", "dollars",
                 # an email sent to the wrong person is the undo-send window, and it scores the
                 # same on "sent" and "wrong person" as money does
                 "email", "e-mail", "mail", "gmail", "outlook", "attachment", "letter",
                 # "i sent it to the wrong address" is an email or a parcel, not a bank recall
                 "address", "addresses", "parcel", "card"),
          # the undo-send entry has three key parts to this one's two, so a tie on the words is
          # decided against the money answer: one point more keeps the recall where it belongs
          bias=4),
    # An overpayment is stated, not asked, and every row that handles money paid by mistake is
    # keyed on the mistake being sent to the wrong place or taken twice: "i overpaid a builder"
    # and "i accidentally overpaid a friend" got a chat nod, and "i paid the builder too much"
    # got his day rate. Whoever holds the money decides the answer - the shop keeps the
    # duplicate-charge card, payroll the overpaid-at-work card, HMRC the rebate - so this one is
    # for the person or the trader who has been paid too much.
    entry("overpaid-someone",
          (PAID_BY_MISTAKE,
           # the payee, not the payment: "the invoice was paid twice" names nobody, and the
           # duplicate-charge card is the right answer for a bill nobody can be asked about.
           # A payee is the person or the trade who was paid, and the money itself is not one:
           # "money" and "back" were in this list, so the mistake words took a spending habit
           # ("i spend too much money", "... on clothes", "... every month") and answered it
           # with the letter asking for £400 back from a plumber who was never mentioned. The
           # paid-twice cards name the money anyway ("i sent the money twice" is the
           # duplicate-charge card), so nothing is lost by standing these two words down.
           ("builder", "plumber", "electrician", "roofer", "tradesman", "trade", "decorator",
            "landlord", "landlady", "letting agent", "friend", "mate", "relative", "supplier",
            "vet", "garage", "mechanic", "cleaner", "gardener", "contractor", "installer",
            "driver", "rent", "deposit", "him", "her", "them", "someone", "somebody")),
          "Ask for it back in writing today, naming the amount and the date: \"I paid the £400 "
          "invoice on Tuesday and sent it again on Thursday by mistake - please can you refund "
          "the second one.\" Most people and most trades refund or credit it once they are asked "
          "plainly, and the message is the date you can prove. If they will not, ask your bank to "
          "recall the payment while it is recent and a money claim online takes the rest; never "
          "pay anyone who offers to get it back for you.",
          # an overpayment to an employer, to HMRC or to a shop has its own card, and a payment
          # that went astray is a recall rather than an overpayment
          avoid=("employer", "payroll", "payslip", "pay slip", "at work", "my pay", "salary",
                 "wages", "boss", "hmrc", "tax", "council tax", "universal credit", "benefit",
                 "pension", "child benefit",
                 "shop", "company", "online", "order", "subscription", "restaurant", "pub",
                 "takeaway", "till", "checkout", "supermarket", "seller", "charged twice",
                 "duplicate", "card",
                 # what a trader charged is a price question, and a shop's bill is the
                 # duplicate-charge card: this row is for money the person sent themselves
                 "charged", "charge", "charges", "overcharged",
                 # "twice" is in this key as the mistake word, and it is also how people say
                 # how often they wrote, rang or were visited: "i emailed him twice" was asked
                 # for its money back. The payment has to be the doing, so those verbs stand
                 # the row down.
                 "email", "emailed", "e-mail", "text", "texted", "message", "messaged",
                 "phone", "phoned", "ring", "rang", "called", "wrote", "letter", "letters",
                 "invite", "invited", "reminded", "remind", "asked", "told", "came", "come",
                 "visit", "visited", "appointment", "appointments", "booked",
                 # a price someone regrets is a price question ("i paid too much for my car"
                 # is whether the car was worth it), and an overpayment is money that should
                 # come back to the person who sent it
                 "too much for", "was it worth", "worth it",
                 # owing money is not paying it: "i owe the plumber money again" is a bill
                 # coming round, and the letter tells them to ask for a refund they never
                 # paid. The row is for money that has already gone out.
                 "owe", "owes", "owed", "owing", "on account", "bill", "invoice",
                 "quote", "quoted", "says", "wants", "wanted", "estimate", "estimated",
                 "wrong account", "wrong person", "wrong number", "wrong sort code",
                 "scam", "scammed", "fraud", "vanished", "never arrived"),
          # a rate card names the trade as well, and a person who has just overpaid one wants
          # the money back rather than the day rate
          bias=3,
          # "is that too much" is the commonest way to ask whether a price is high, and the
          # words are the row's own mistake word beside a payee, so a judgement on a figure
          # already said read as an overpayment: "i paid 120 for a plumber to fix a leak, is
          # that too much" was told to ask for a £400 invoice back, and so was "my builder
          # says 12 grand, is that too much". Whether the line is a judgement on a figure is
          # the reading's question, not a word list's, so it is asked here.
          guard=_not_a_figure_judged),
    entry("food-poisoning", (("food poisoning", "sick after eating", "bad food", "off food",
                              "food was off", "ill after eating", "ill after", "poorly after",
                              "made me ill", "made me sick", "gave me food poisoning"),
                             ("restaurant", "takeaway", "meal", "cafe", "pub", "wedding",
                              "chicken", "kebab", "buffet", "ate",
                              # the complaint shapes name where they ate rather than a dish
                              "eating out", "eat out", "ate out", "went out for", "meal out")),
          "Report it to the council's environmental health team the same day: they inspect the "
          "kitchen, and that report is what makes a claim stick. Keep the receipt, the packaging "
          "and any leftovers, and get a doctor to record it if you are still unwell. Claim in "
          "writing for the days you lost and for the illness, first from the restaurant and then "
          "through the small claims court, which has a three-year limit.",
          avoid=("how long", "how many days", "medicine", "rehydrate", "what should i eat",
                 "should i eat", "treatment", "diarrhoea for", "my stomach",
                 # the danger named as the thing to avoid is a cooking question, not a claim:
                 # "how do i defrost a chicken without giving myself food poisoning" is
                 # chicken-defrost's, and this board was answering it with the council letter
                 "defrost", "defrosting", "thaw", "thawing", "thawed", "reheat", "reheating",
                 "freezer", "frozen", "left out", "shelf life", "store", "storing", "storage",
                 "avoid", "avoiding", "avoid getting", "without giving", "prevent",
                 "prevention", "cross contamination", "not get", "how do i stop",
                 "how do i cook", "cook it", "cooking", "safe to eat", "still safe"),
          # a line that names the restaurant it got the illness from has this card's answer -
          # report it, keep the evidence, claim - and cooking's eat-when-ill is for the person
          # who wants to know what to eat now, so the two sit on the same bias and this key,
          # which names the meal, wins the tie
          bias=1),
    entry("noise-neighbour", (("neighbour", "neighbor", "neighbours", "flat above", "next door",
                               "building work", "music", "dog barking", "council", "environmental health",
                               # The complaint is often made without saying whose noise it is:
                               # "who do i complain to about noise", "how do i report noise". The
                               # phrasings are whole ones and "noise" is never one of them, so a
                               # line about quietening a room keeps the answer it had.
                               # "a noise complaint" on its own took "how do i get a noise
                               # complaint sorted", which is the council-route answer
                               # (where_it_answers): the phrase is the making of one, not the
                               # thing to hand to a particular service.
                               "about noise", "noise nuisance",
                               "report a noise complaint", "log a noise complaint",
                               "make a noise complaint", "raise a noise complaint",
                               "noise complaint about", "noise complaint to the council",
                               "noise pollution", "report noise", "report the noise",
                               "reporting noise", "complain about noise", "complain about the noise",
                               "complaint about noise",
                               # What the council does about it is the same question, and the
                               # name of the power they use is how people ask it: "how do i get
                               # a noise abatement notice" and "what is a statutory nuisance"
                               # were a shrug. The words are whole ones, so a line about the
                               # notice a landlord served on a tenant stays in the housing rows.
                               "abatement notice", "noise abatement", "abatement",
                               "statutory nuisance"),
                              ("noise", "noisy", "loud", "banging", "building work", "6am", "early",
                               "at night", "all night", "every night", "party", "complain",
                               "complaint", "report")),
          "Keep a short diary for two weeks: date, time, what it was, how long. Then ring the "
          "council's environmental health team, who must look into a statutory nuisance and can "
          "serve an abatement notice. Builders are usually held to about 8am to 6pm on weekdays "
          "and Saturday mornings, so a 6am start is worth reporting.",
          avoid=("my neighbour", "neighbour is", "leaves", "pets", "cat", "dog", "parking",
                 "hedge",
                 # a spoiled holiday, a hotel and a flight are the travel answers
                 "holiday", "hotel", "resort", "abroad", "flight", "cruise", "package",
                 # "i loved the party next door last night" is a good night, not a nuisance
                 "loved", "love the", "enjoyed", "good night", "great night", "fun", "thanks",
                 "invited", "wedding", "birthday",
                 # A colleague is not a neighbour and a council is not who you ring about a desk:
                 # "my coworker plays music out loud all day" was answered with the two-week
                 # diary and the abatement notice, because bare "music" and "loud" met here.
                 "colleague", "colleagues", "coworker", "coworkers", "co-worker", "co-workers",
                 "workmate", "workmates", "teammate", "teammates", "team mate", "team mates",
                 "at work", "at my desk", "open plan", "in the office", "the office",
                 "classroom", "in class", "library", "on the train", "on the bus",
                 "my flatmate", "flatmate", "flatmates", "roommate", "roommates",
                 "housemate", "housemates",
                 # Asking how to say it is a different question from who to tell: "help me word
                 # a note to the neighbours about the noise" wants the words, which the row that
                 # says to talk to them gives.
                 "word a note", "word the note", "word a letter", "wording", "wording a",
                 "write to them", "write a note", "note to the neighbours", "note to my neighbour",
                 "letter to the neighbours", "what should i say", "how do i say")),
    # A nuisance is not only noise. "who do i tell about the smell from the farm", "who do i
    # report a smell to" and "the bonfire smoke is coming into our garden every night" were all
    # a shrug: the noise row is where the council's nuisance powers are written down, and a
    # smell is the same statutory nuisance served with the same abatement notice. The subjects
    # here are whole phrases ("smell from", "smoke coming from") so the ordinary smell lines -
    # a fridge, a bin, a drain under the sink, a car - keep the answers they had.
    entry("a-nuisance-from-a-place",
          (("smell from", "smells from", "smell coming from", "smells coming from",
            "smell of sewage", "sewage smell", "smells like sewage", "stink from",
            "stinks from", "odour from", "odor from", "chemical smell", "smoke from",
            "smoke coming from", "bonfire smoke", "bonfire next door", "farm smell",
            "smell from the farm", "smell from the factory", "dust from", "nuisance from",
            "smell nuisance", "smell complaint", "report a smell", "report the smell",
            "complain about the smell", "complain about a smell", "smell and noise",
            "smoke and noise", "statutory nuisance", "smoke is coming", "smoke blowing",
            "smoke drifts", "smell is coming"),
           # the second half is deliberately loose, because the first half is whole phrases only:
           # a line that says "smell from" or "smoke from" is about that nuisance whatever the
           # rest of the sentence does, and the ordinary smells are stood down by `avoid` below.
           ("report", "reporting", "who do i", "who to", "tell", "complain", "complaint",
            "nuisance", "environmental health", "council", "how do i", "get it stopped",
            "stop it", "abatement notice", "next door", "neighbour", "neighbours",
            "there is", "there's", "is coming", "coming from", "coming into", "keeps coming",
            "every night", "all night", "every day", "all the time", "cant open", "can't open",
            "fed up", "sick of", "notice it", "noticed it", "again tonight")),
          "Report it to the council's environmental health team, who handle smoke, smells, dust "
          "and fumes from a farm, a factory, a takeaway or a building site: ring them or use the "
          "online form with the address and the times it happens, and keep a diary for a week or "
          "two. If it is bad enough they must look into it as a statutory nuisance and can serve "
          "an abatement notice, so ask for the case reference. Nothing in ten working days means "
          "chasing it and asking for it to be logged as a formal complaint; after their final "
          "reply the Local Government Ombudsman takes it on free.",
          avoid=("my fridge", "the fridge", "freezer", "bin", "bins", "bin bag", "kitchen",
                 "sink", "drain", "plughole", "washing machine", "dishwasher", "toilet",
                 "my house smells", "my flat smells", "my room smells", "damp", "mould",
                 "car", "van", "caravan", "cooker", "oven", "cooking", "food", "milk",
                 "meat", "chicken", "cigarette", "vape", "smoke alarm", "smoke detector",
                 "my breath", "urine", "stool", "vagina", "discharge", "wound",
                 "my feet", "my mouth", "my nose", "get rid of the smell",
                 # a bonfire you are having, and the rules for one, are the garden's question
                 "my bonfire", "have a bonfire", "bonfire night", "fireworks",
                 # the gas board is the safety answer, never a nuisance letter
                 "gas leak", "smell gas", "smell of gas", "gas smell", "carbon monoxide")),
    # both halves have to name an injury: "how do i claim X" is a way of asking, not a subject,
    # and a bare "claim" in the first half made this entry answer every benefit, deposit and
    # warranty question that happened to say "claim"
    entry("injury-claim", (("whiplash", "injury", "injured", "accident", "crash", "hurt in",
                            "knocked off my bike", "slipped on", "slipped in", "fell over",
                            "fell down the", "tripped over"),
                           ("claim", "compensation", "sue", "solicitor", "payout", "who pays",
                            "how do i claim", "can i claim", "wasnt my fault", "wasn't my fault",
                            "injured", "whiplash")),
          "See a doctor and get the injury on record first, because a claim rests on medical "
          "evidence. Then tell the other side's insurer in writing and keep the photos, the "
          "witness names and the receipts. Small whiplash claims go through the official claims "
          "portal on a fixed tariff, so a no-win-no-fee solicitor costs you nothing to ask about.",
          avoid=("work", "workplace", "gym", "exercise", "sport", "training", "dog", "cat",
                 "insurance quote",
                 # "how do i claim on my travel insurance" is a policy question; the injury
                 # answer's first line (see a doctor) is the wrong half of that
                 "insurance", "policy", "cover", "covered", "travel", "holiday", "abroad",
                 "trip", "flight", "hotel",
                 # a benefit, a refund or a warranty is not an injury claim
                 "benefits", "universal credit", "pip", "esa", "child benefit", "tax credits",
                 "refund", "warranty", "guarantee", "pension", "compensation for a flight",
                 # the money back for a deposit, a benefit, sick pay or mileage is its own
                 # answer: those lines say "claim" and nothing about an injury
                 "deposit", "landlord", "tenancy", "benefit", "sick pay", "mileage",
                 "expenses", "childcare", "stolen", "amazon", "small claims")),
    entry("hotel-overbooked", (("hotel", "booking", "guest house", "room", "reception"),
                               ("overbooked", "no room", "turned away", "walked", "double booked",
                                "not available", "cancelled my booking", "moved us",
                                # they gave the room to someone else and lost the booking
                                "gave away", "gave my room", "gave our room", "gave the room",
                                "no record", "lost my booking", "lost our booking",
                                # thrown out of a room that was paid for
                                "kicked out", "kicked us out", "thrown out", "threw us out",
                                "asked to leave", "told to leave", "told us to leave",
                                "made us leave", "evicted", "evict us")),
          "A paid booking is a contract, so the hotel has to put you somewhere comparable at their "
          "cost, or give the money back and pay for what the move cost you. Ask for the alternative "
          "in writing while you are still at the desk, keep the taxi and phone receipts, and claim "
          "from the hotel, then the booking site. Only a real breach - damage, a noise complaint, "
          "too many people - lets them end the stay.",

          # The matcher folds word forms, so "booking" and "booked" are one form and "double
          # booking" is "double book": a diary clash reached this row on "double booking" alone and
          # was told to photograph the room and complain at reception. A person double booking
          # themselves, their clients or their meetings is the one doing the booking, and the
          # answer for them keeps one diary; a hotel double books the guest.
          avoid=("cheap", "worth it", "should i book", "when to book", "how far in advance",
                 "myself", "clients", "things", "meetings",
                 # the same diary clash said with the table named instead of the person: "i
                 # double booked the restaurant" and "i double booked a table" were told to
                 # photograph the room and complain at reception. What is double booked is the
                 # telling word - a room or a hotel is this row's, a table, a dinner or a
                 # dentist is a diary with two of the same in it.
                 "restaurant", "restaurants", "table", "tables", "dinner", "lunch",
                 "breakfast", "drinks", "dentist", "doctor", "haircut", "barber",
                 "salon", "clinic", "work", "shift", "shifts", "swimming",
                 "playdate", "babysitter", "childcare"),
          # The word "room" is this row's key and it is also the space in a kitchen: "i have no
          # room in my kitchen" was sent the overbooking card while "no room in my kitchen" got
          # the storage answer. Which room the line is about is the rest of the sentence, and the
          # test below already reads it for the bad-room card.
          guard=_a_hotel_room_or_no_home),
    entry("car-hit-parked", (("hit", "crashed", "smacked", "damaged", "scraped"),
                             ("parked", "parked car", "my car", "drove off", "drove away",
                              "no note", "hit and run", "someone hit")),
          "Report it to the police within 24 hours if the other driver drove off, and get a crime "
          "reference number. Then tell your own insurer even if you are not claiming, because the "
          "policy usually requires it, and see whether the car park or a nearby house has CCTV "
          "before it is overwritten.",
          avoid=("hit the gym", "hit it off", "hit the shops", "hit the road")),
    entry("car-insurance-sold", (("car insurance", "policy", "insurance"),
                                 ("sold", "selling", "selling my car", "sell my car", "got rid",
                                  "scrapped", "part exchange", "new car")),
          "Don't just cancel it: tell your insurer the date you sold the car and either move the "
          "policy to the new one or cancel, and you get the unused months back minus a fee, "
          "usually £25 to £50. Send the V5C to the DVLA with the buyer's details on the day, or "
          "you stay liable for the tax and the fines.",
          avoid=("claim", "refused", "cheapest", "compare", "quote", "black box", "young driver")),
    # --- money and contracts ---------------------------------------------------
    entry("unauthorised-payment", (("unauthorised", "unauthorized", "didnt authorise",
                                    "didn't authorise", "did not authorise", "without my permission",
                                    "without asking", "without my consent", "without telling me", "without permission",
                                    "money went out", "money left my account",
                                    "someone used my card", "my card was used", "card was used",
                                    "cloned my card", "card cloning", "identity theft",
                                    "my card was cloned", "card was cloned", "card cloned",
                                    "someone cloned", "money taken from my account",
                                    # a payment the person never made is this, not a duplicate
                                    "i didnt make", "i didn't make", "i did not make",
                                    "didnt make that payment", "never made", "not me",
                                    "i didnt spend", "i didn't spend", "i never bought",
                                    "i never ordered", "i never paid",
                                    # a direct debit or a subscription set up without a yes is
                                    # the same unauthorised payment, and it was being answered as
                                    # a trader charging more than the quote
                                    "set up a direct debit", "set up a dd", "set up a subscription",
                                    "never agreed to a direct debit", "never agreed to the direct debit",
                                    "direct debit i never", "direct debit i didnt",
                                    "direct debit i didn't", "subscription i never"),
                                   ("money", "account", "card", "payment", "paid", "transaction",
                                    "taken", "took", "went out", "gone out", "charged", "debit")),
          "Tell your bank or card company the same day and use the word unauthorised: it has to "
          "be refunded in full by the end of the next working day, and the bank can refuse only if "
          "it can show you were grossly negligent or handed the money over. Ask for a new card, "
          "report it to Action Fraud for a crime reference, and if the bank stalls, complain and "
          "the Financial Ombudsman takes it free after eight weeks.",
          avoid=("scam text", "text message", "email says", "phone call", "paid by transfer",
                 "bank transfer", "transfer the money",
                 # a bank that closes or freezes an account is a complaint about the bank, not
                 # a payment taken without a yes: "without telling me" read as the fraud line
                 "closed my account", "closed my bank", "closed the account", "shut my account",
                 "account was closed", "frozen my account",
                 "froze my account", "blocked my account", "account was frozen",
                 # a card used abroad while the person still has the card in their hand is
                 # card fraud, and money.py's card-fraud row says what to do about it
                 "another country", "abroad", "overseas", "i still have the card",
                 "still have my card", "still got my card", "used in another",
                 # a direct debit that went up is the billing answer, not a payment nobody
                 # agreed to: "the energy company put my direct debit up without asking" read
                 # as fraud, and so would "my direct debit went up without telling me"
                 "put my direct debit up", "put the direct debit up", "put my dd up",
                 "direct debit went up", "direct debit has gone up", "direct debit increase",
                 "increased my direct debit", "increased my dd", "raised my direct debit",
                 "raised my dd", "raised the direct debit", "put it up without",
                 # setting a payment up is not a payment taken without a yes. The key carries
                 # "set up a direct debit" for "a direct debit set up without my permission",
                 # and with it the how-to was answered with the card-fraud card: "how do i set
                 # up a direct debit" was told to ring the bank about an unauthorised payment.
                 # The how-to shapes stand this row down, and the payment-types rows answer.
                 "how do i set up", "how to set up", "how do i start", "how to start",
                 "how do i arrange", "i want to set up", "i want to start", "want to set up",
                 "set up a direct debit for", "set up a standing order for",
                 "set up a payment plan"),
          # money's general refund answer reaches "how do i get a refund for an unauthorised
          # transaction" too, and the bank's same-day route is what that line is asking for
          bias=3),
    entry("services-ruined", (("hairdresser", "hairdressers", "barber", "salon", "hair salon",
                               # "she cut my hair too short" names the hair, not the person: the
                               # second key group still has to name what went wrong
                               "my hair", "cut my hair", "my haircut", "the haircut", "highlights",
                               "blow dry", "blow-dry",
                               "nails", "manicure", "pedicure", "tattoo", "eyebrows", "waxing",
                               "dry cleaner", "dry cleaners", "dry cleaning", "tailor",
                               "alterations", "car wash", "valet", "repair", "repairs",
                               "repair shop", "phone repair", "the shop repaired",
                               # a groomer that nicks the animal is the same botched job, with a
                               # vet bill on top: "my dog groomer cut my dog" was getting grooming
                               # advice about knots
                               "groomer", "groomers", "dog groomer", "pet groomer", "grooming salon"),
                              ("ruined", "messed up", "butchered", "burnt my", "burnt it",
                               "damaged", "wrong", "refund", "complain", "compensation",
                               "cut my dog", "cut my cat", "cut my pet", "nicked my dog",
                               "nicked my cat", "hurt my dog", "hurt my cat", "injured my dog",
                               "injured my cat", "vet bill", "nicked", "a cut", "cut on",
                               "came back with", "cut the dog", "cut the cat",
                               "gone wrong", "awful", "fix it", "chipped my", "shrank",
                               "shrunk", "stained", "came back worse", "worse than before",
                               "made it worse", "now its worse", "now it's worse",
                               "is worse", "worse now", "screen is worse", "came back broken",
                               "broke it", "broken it", "botched", "money back", "my money",
                               "made my", "worse",
                               # "the hairdresser cut too much off" asked for a price answer:
                               # "hairdresser" and "too much" are the price entry's two halves,
                               # and nothing here said the cut was wrong
                               # a repairer that scratched or dented the thing made it worse
                               # even though it works: "the repair shop scratched my watch" was
                               # the faulty-goods ladder, which is about the thing, not the job
                               "scratched", "scratches", "scuffed", "dented", "came back scratched",
                               "cut too much off", "took too much off", "too much off",
                               "cut it too short", "cut too short", "cut my hair too short",
                               "chopped too much off", "chopped too much")),
          _services_ruined_reply,
          avoid=("how much", "how often", "should i cut", "what haircut", "which haircut",
                 "style", "grow", "hair loss", "thinning", "dandruff", "shampoo", "tip",
                 # a repair you do yourself in the wood is the wood card's, not a botched job:
                 # "how do i repair a chip in a wooden table" reached this row on "repair" plus
                 # "chipped", and the answer was the refund ladder for a tradesman
                 "wooden", "veneer", "worktop", "furniture", "sideboard", "skirting",
                 # the same shape of line about a small thing nobody repairs for you:
                 # "how do i repair a chipped mug" reached this row on "repair" plus "chipped"
                 # and was told to photograph a botched job. A mug, a plate or a chair is not a
                 # service, and the thing's own answer (or the shop's) is the useful one. The
                 # things a service really does handle - a watch, a phone, a coat, a dress - are
                 # not in the list.
                 "mug", "mugs", "cup", "cups", "plate", "plates", "bowl", "bowls", "glass",
                 "glasses", "kettle", "toaster", "saucepan", "pan", "pans", "chair", "chairs",
                 "stool", "shelf", "shelves", "cutlery", "teapot", "vase", "lamp", "mirror",
                 # how to groom an animal at home is a pet-care answer, not a claim
                 "how do i groom", "how to groom", "how do i cut", "how often should i groom",
                 "matted", "knots", "brush my dog", "brush my cat", "cut my nails",
                 "clip their nails", "clipping nails", "trim the nails", "nails grow",
                 "boiler", "washing machine", "dishwasher", "fridge", "freezer", "car engine",
                 "mot", "tyre", "brakes",
                 # a chip in the windscreen is a question about repairing glass, not a botched
                 # job: "is it worth repairing a stone chip in my windscreen" had "repairing"
                 # and "chipped" by form and got the services-ruined refund card
                 "stone chip", "chip in the windscreen", "chip in my windscreen",
                 "chip in the windshield", "chip in my windshield", "windscreen chip",
                 "windshield chip", "windscreen is chipped", "windscreen has a chip",
                 # painting your own nails is the polish row, not a complaint: "nails" and
                 # "chipped"/"chipping" are enough for this entry to take "how do i stop my
                 # nail polish chipping", which is a how-to and not a botched manicure
                 "polish", "nail polish", "nail varnish", "stop it chipping",
                 "stop my nail polish chipping",
                 # wanting your money instead of a repair is the refund ladder's line, not a
                 # botched job's: "i want a refund not a repair"
                 "not a repair", "instead of a repair", "refund or repair", "repair or replace",
                 "accept a repair", "who chooses", "insist on a refund", "demand a refund",
                 # a shop that offers a repair instead of the refund is the shop's-choice
                 # question, and its second half is the word "refund" itself
                 "instead of refund", "instead of a refund", "instead of refunding",
                 "rather than refund", "rather than a refund", "want a refund", "want my money",
                 "refund me instead", "i want a refund",
                 # a claim needs someone who did the job. Bleach at home that went wrong is the
                 # hair-colour repair card's question, and "my hair is damaged from bleach" was
                 # reading as a complaint about a salon that was never named. A line that does
                 # name the hairdresser ("the salon bleached my hair and it snapped") keeps the
                 # claim, so the bare word "bleach" is not held out, only the home-job shapes.
                 "from bleach", "bleach at home", "bleached it at home", "box dye",
                 "box colour", "box color", "did it myself", "done it myself",
                 "dyed it myself", "bleached it myself",
                 # a repair the council or a landlord owes is not a job you paid a shop for:
                 # "how do i complain about a repair the council wont do" was told to photograph
                 # a botched job and ask for a refund of money nobody had paid. The council's
                 # own rows and the landlord rows answer those lines.
                 "council", "the council", "councils", "housing association", "social housing",
                 "council house", "council flat", "landlord", "landlords", "letting agent",
                 "my flat", "my house", "my home", "my boiler", "the boiler", "the heating",
                 "my heating", "damp", "mould", "mold", "leak", "leaking"),
          # "the dry cleaner shrank my dress" is reached by a cleaning entry too (how to care
          # for the garment), and a garment already ruined is this question: the tie goes here.
          # A refund for ruined hair is also reached by money's general refund answer.
          bias=3),
    entry("letting-agent-fees", (("letting agent", "letting agents", "letting agency",
                                  "estate agent", "estate agents", "agent"),
                                 ("fee", "fees", "charged me", "charging me", "admin fee",
                                  "referencing", "reference fee", "inventory fee", "check out fee",
                                  "for nothing", "extra charge", "said it was free")),
          "Most fees charged to tenants were banned in England in June 2019: no admin, referencing, "
          "credit check, inventory, guarantor or check-out fee, and the only payments an agent can "
          "ask for are rent, a deposit capped at five weeks' rent, a holding deposit of one week, "
          "and a default for a late payment or a lost key in writing. Ask for the money back and "
          "name the fee; the council's trading standards team enforces the ban.",

          avoid=("deposit", "deducted", "deduction", "withheld", "boiler", "repair", "gas safety",
                 "inspection", "selling", "buying", "valuation", "viewing", "rent arrears")),
    entry("direct-debit-rise", (("direct debit", "direct debits", "dd payment", "monthly payment",
                                 "standing order"),
                                ("gone up", "went up", "put it up", "put up", "put my",
                                 "put our", "raised", "increased", "increase", "rises",
                                 "too much", "higher", "doubled", "much more", "huge")),
          "Ask them to show you how the figure was worked out, in writing, and give a meter "
          "reading: an estimate built on last year's use is the usual reason, and the reading fixes "
          "it the same day. You never have to accept a figure you cannot afford - ask for a payment "
          "plan or to pay for what you use - and if the amount was wrong or taken early the Direct "
          "Debit Guarantee makes your bank refund it.",

          ask=("why", "how", "can", "should", "do", "what", "my", "they", "it"),
          # how a direct debit works, and what one is, are money questions
          avoid=("set up a direct debit", "how do i set up", "what is a direct debit",
                 "cancel my direct debit", "switch", "rent", "landlord", "tenant", "gym",
                 "membership", "phone", "broadband", "water")),
]
