"""Everyday life admin: the paperwork and the small emergencies nobody has told you about.

The answers lane owns this domain. These are not facts about the world but moves: who to tell
when you move, what to do first when the bank card has gone, how to get a passport that is
late, what to say when a takeaway arrives cold. Entries are keyed by the situation, not by
wording, so "who do i tell when i move" and "i need to change my address" reach the same
advice.

This file deliberately holds only what the other domains leave out. Refunds, faulty goods,
missing parcels and complaint letters are the consumer domain (consumer.py); the landlord,
the deposit and the neighbour are home.py; a bill that has gone up and a subscription are
money.py. Every one of those lines would otherwise have two tables answering it and one of
them losing, so here the entries stop where those files start.

Advice that depends on a country's law is written as the move plus where the rule lives, never
as one country's rule stated as fact: the bot says to check your own country's guidance and
names who can act (the council, the passport office, your bank), because a confidently wrong
legal answer is worse than a pass.
"""
import re

from .health import NO_DRUGS
from .lookup import A_HOURS_ASK, IMPROVE, a_price_not_a_loan, entry
from .technology import APP_ACCOUNT_WORDS

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
# Every id here is already declared by another domain, so adding this file changes no routing.
ANSWERS = ("home-and-diy", "shopping", "money")

_NAME_DIVORCE = ("divorce", "divorced", "divorcing", "decree absolute", "decree nisi",
                 "maiden name", "back to my", "go back to my")
_NAME_CHILD = ("child", "children", "son", "daughter", "my kid", "my kids", "teenager",
               "under 16", "under 18", "parental responsibility")


# drain guard
_A_STREET_PLACE = re.compile(
    r"\b(?:street|streets|road|roads|gully|gullies|gully|pavement|pavements|kerb|curb|"
    r"highway|highways|verge|manhole|drain cover|lay-?by)\b")
_THE_DRAIN = re.compile(r"\b(?:drain|drains|drainage|gully|gullies)\b")
_ASKS_WHO = re.compile(r"\b(?:who do i|who should i|who can i|who to call|who to ring|"
                       r"who do i ring|who do i call)\b")


def _council_owns_the_drain(understood):
    line = " ".join(str((understood or {}).get("clean")
                        or (understood or {}).get("text") or "").lower().split())
    if not _THE_DRAIN.search(line):
        return True
    if _A_STREET_PLACE.search(line):
        return True
    return not _ASKS_WHO.search(line)


# Everything a complaint can be asked with and still name nobody: the ask, the pronouns and the
# glue. What is left over is the subject, and a line with a subject in it is answered by the row
# that subject belongs to.
_ONLY_THE_ASK = re.compile(
    r"\b(?:who|whom|whose|do|does|did|i|im|i'm|we|you|to|can|could|should|shall|would|will|how|"
    r"where|what|whats|what's|when|if|is|are|was|be|been|it|its|it's|this|that|these|those|them|"
    r"they|there|my|our|your|a|an|the|and|but|or|so|then|just|really|actually|please|make|making|"
    r"put|raise|raising|register|registering|start|starting|go|goes|going|get|getting|complain|"
    r"complains|complaining|complaint|complaints|complainabout|about|with|of|in|on|at|for|from|"
    r"want|wants|wanted|need|needs|like|tell|report|reporting|someone|somebody|anyone|anybody|"
    r"somewhere|somewhere|right|thing|things|sort|sorted|formal|officially|official|properly|now|"
    r"help|me|us|him|her|have|has|had|not|no|bad|badly|same|again|still|more|up|down|out|off)\b")


def _a_complaint_with_no_subject(understood):
    """True only for a complaint that names nothing to complain about: "who do i complain to".

    The row is the shape of a complaint - write it down, say what you want, then the ombudsman
    for whoever it turns out to be - so it is only right when the line names nobody. Every word
    that could be a subject is left out of `_ONLY_THE_ASK`, and a line with one word left over
    is stood down here and answered by the row that word belongs to, which is what keeps "who
    do i complain to about noise" on the noise answer and "about a parcel" on the consumer one.
    """
    line = " ".join(str((understood or {}).get("clean")
                        or (understood or {}).get("text") or "").lower().split())
    if not re.search(r"\bcomplain", line):
        return False
    return not _ONLY_THE_ASK.sub(" ", line).strip()


def _change_name(memory, understood):
    """A marriage, a divorce and a child are three different routes to a new surname, and one
    answer that starts with the marriage certificate is wrong for the other two."""
    said = (understood.get("norm_text") or understood.get("text") or "")
    if any(word in said for word in _NAME_CHILD):
        return ("To change a child's name, everyone with parental responsibility has to agree, or "
                "a court decides if they will not: one parent's deed poll is not enough while the "
                "child is under 16. Ask the other parent in writing first, keep the reply, and get "
                "advice before you pay anyone. At 16 and 17 they can make their own deed poll.")
    if any(word in said for word in _NAME_DIVORCE):
        return ("A divorce does not change your name by itself: the decree absolute proves the "
                "divorce, and you use it with a deed poll - the free one, signed by two witnesses - "
                "to go back to your old name. Keeping the married name is allowed too. Then tell the "
                "passport office, the DVLA, your bank, HMRC, the council, your GP and your employer.")
    return ("After a marriage or civil partnership the certificate is your proof, and you can use "
            "the new name straight away: send it to the passport office, the DVLA, your bank, HMRC, "
            "the council, your GP and your employer, because nothing updates itself. Any other "
            "change needs a deed poll - the free one, signed by two witnesses, is accepted "
            "everywhere, so skip the firms that charge to print it.")


# A parcel that has not shipped and one already on its way are the same rule led with a
# different half. "how do i cancel an order that has already been dispatched" opened "If it has
# not been dispatched, ...", which answers the line it is not; the order is picked off the line.
_CANCEL_SENT = ("dispatched", "sent", "shipped", "arrived", "delivered", "delivery", "coming",
                "on its way", "out for delivery", "already", "turned up", "comes anyway")
# "can i send it back if i change my mind" is the return window, not the cancellation, even
# though "change my mind" is in the entry's own key.
_CANCEL_RETURN = ("send it back", "send back", "take it back", "return it", "return", "returns",
                  "get a refund", "money back", "changed my mind", "change my mind")

_CANCEL_AT_WAREHOUSE = ("Cancel it on your account page or by ringing with the order number, and "
                        "ask for the cancellation in writing - a cancelled order that still ships "
                        "is the commonest version of this.")
_CANCEL_WINDOW = ("Anything bought online has 14 days from delivery to change your mind, whatever "
                  "the shop's own page says, and another 14 days to send it back.")
_CANCEL_REFUSE = "If the parcel comes anyway, refuse the delivery rather than opening it."
_CANCEL_REFUND = ("If they will not refund, a card chargeback or Section 75 through your bank is "
                  "the next step.")


def _cancel_order_reply(memory, understood):
    """Lead with the half the line is about: the return window once it is out, the cancellation
    while it is not, and the refund only as the last sentence."""
    said = (understood.get("norm_text") or understood.get("text") or "")
    if any(word in said for word in _CANCEL_SENT):
        return " ".join((_CANCEL_WINDOW, _CANCEL_REFUSE, _CANCEL_REFUND))
    if any(word in said for word in _CANCEL_RETURN):
        return " ".join((_CANCEL_WINDOW, _CANCEL_REFUND))
    return " ".join((_CANCEL_AT_WAREHOUSE, _CANCEL_REFUSE, _CANCEL_REFUND))


# --- who gets what for carrying the bag -------------------------------
# A tip is not one number: "do you tip a taxi driver" was answered "In a pub, nothing: you order
# and pay at the bar", which is the pub's line first and the asker's second. The thing being
# tipped is in the line, so it picks the first sentence, and the general answer is only for a
# line that names nobody.
_TIP_TAXI = ("taxi", "cab", "uber", "minicab", "black cab")
# The round: a postman, a milkman, a bin crew. Nothing is owed and everybody knows it, but a
# card at Christmas is what the question is really about, and "do you tip the bin men" reached
# no answer at all.
_TIP_ROUND = ("postman", "postmen", "postie", "postwoman", "milkman", "milk man", "bin men",
              "binmen", "bin man", "refuse collector", "refuse collectors", "rubbish collector",
              "recycling crew", "dustmen", "dustman")
_TIP_DELIVERY = ("delivery", "deliveroo", "just eat", "uber eats", "dominos", "courier",
                 "takeaway driver", "food delivery", "pizza guy", "pizza delivery",
                 "delivery guy", "delivery driver", "delivery man", "delivery rider")
_TIP_RESTAURANT = ("restaurant", "waiter", "waitress", "waiting staff", "table service",
                   "meal out", "eat out", "dinner out", "lunch out")
_TIP_PUB = ("pub", "bar", "bartender", "barman", "barmaid", "pint", "at the bar")
_TIP_HAIR = ("hairdresser", "barber", "salon", "haircut", "hair cut", "blow dry", "stylist",
             "nail technician", "nails done", "manicure", "pedicure", "beautician", "waxing",
             "massage", "spa")
# A trade quotes a price for the job, so there is nothing to tip on top of it.
_TIP_TRADES = ("plumber", "electrician", "builder", "decorator", "joiner", "carpenter",
               "plasterer", "tiler", "gardener", "mechanic", "fitter", "engineer",
               "gas engineer", "boiler man", "handyman", "roofer", "scaffolder", "odd job man")
# Work where the tip is expected, because the pay is low or the time is the product.
_TIP_TATTOO = ("tattoo", "tattoos", "tattooist", "piercing", "piercings", "piercer")
_TIP_MOVERS = ("mover", "movers", "removal men", "removal firm", "removals", "moving men",
               "man and van", "man with a van", "sofa delivered")
_TIP_GUIDE = ("tour guide", "guide", "coach driver", "tour", "excursion", "walking tour",
              "driver guide")
_TIP_HOTEL = ("hotel", "housekeeping", "porter", "concierge", "bellboy", "maid")
# A cleaner is not a hotel cleaner: the person who does your house is paid by the hour and a tip
# is not part of it, so "should i tip my cleaner" cannot take the hotel's pound-a-night line.
_TIP_CLEANER = ("cleaner", "cleaners", "my cleaner", "house cleaner", "nanny", "nannies",
                "babysitter", "baby sitter", "childminder", "au pair")
_TIP_CAFE = ("cafe", "cafes", "coffee", "teashop", "tea room", "barista", "starbucks", "costa",
             "pret", "coffee shop", "coffee van")
_TIP_LEASEHOLD = ("leasehold", "ground rent", "estate charge", "estate charges",
                  "block of flats", "management fee", "management company", "service charge on",
                  "flat", "flats", "freeholder", "lease")
# The tip that is a place rather than money: the household waste site. A phrase rather than the
# bare word, so "should i tip the driver" and "how much do you tip at the tip" are not caught by
# the same rule - and "the tip" is what everybody calls the place.
_TIP_THE_PLACE = ("the tip", "to a tip", "to the tip", "a tip run", "tip run", "the dump",
                  "local tip", "recycling centre", "recycling center", "household waste",
                  "household waste site", "civic amenity", "the skip", "a skip",
                  "to the dump", "the tip's")

_TIP_ABROAD = ("america", "american", "usa", "the us", "united states", "japan", "japanese",
               "tokyo", "kyoto", "france", "paris", "spain", "italy", "rome", "portugal",
               "greece", "germany", "netherlands", "amsterdam", "mexico", "thailand", "turkey",
               "dubai", "india", "canada", "australia", "ireland", "abroad", "overseas",
               "europe", "in the states",
               # A city names the country as well as the country's name does, and "how much do
               # you tip in new york" was the UK rule: the travel table has the US one.
               "new york", "nyc", "las vegas", "vegas", "florida", "california", "los angeles",
               "san francisco", "miami", "chicago", "boston", "seattle", "washington", "texas",
               "hawaii", "orlando", "toronto", "vancouver", "sydney", "melbourne", "brisbane",
               "perth", "auckland", "bali", "phuket", "singapore", "hong kong", "seoul",
               "lisbon", "barcelona", "madrid", "berlin", "munich", "florence", "venice",
               "athens", "crete", "malta", "cyprus", "croatia", "dubrovnik", "prague", "vienna",
               "zurich", "geneva", "brussels", "copenhagen", "stockholm", "oslo", "helsinki",
               "warsaw", "budapest", "istanbul", "egypt", "morocco", "brazil", "argentina",
               "peru", "cuba", "jamaica", "barbados", "maldives", "sri lanka", "vietnam",
               "cambodia", "malaysia", "indonesia", "philippines", "qatar", "israel", "jordan",
               "kenya", "iceland", "norway", "sweden", "denmark", "finland", "poland", "czech",
               "austria", "switzerland", "belgium")


# One theft, one answer: a snatched bag, a pickpocketed wallet and a hand gone into a pocket
# all want the same order of jobs, and the shows the same words whether they said where.
STOLEN_BAG = (
    "Cancel and block first, in this order: freeze every card in your bank's app, ask your "
    "network to bar the phone, then report it to the police on 101 for a crime reference number, "
    "which your insurance will ask for. If your keys and address were both in the bag, get the "
    "locks changed rather than hoping, and tell the bank you are worried about your address too. "
    "Most home insurance covers a bag taken away from home, and most policies want to hear "
    "within a few days.")

# Away from home the order changes: a police report in the country you are in is what the insurer
# and the embassy both ask for, and 101 does not exist abroad. The line has to name the trip.
AWAY = ("abroad", "overseas", "on holiday", "holiday", "vacation", "foreign country",
        "another country", "in spain", "in france", "in italy", "in greece", "in portugal",
        "in turkey", "in mexico", "in thailand", "in india", "in the usa", "in america",
        "in canada", "in australia", "in dubai", "in egypt", "in morocco", "interrailing")
STOLEN_BAG_AWAY = (
    "Report it to the police where you are and get a written report - a copy in English if you "
    "can - because your travel insurer and any replacement passport both ask for one. Then freeze "
    "the cards in your bank's app, have your network bar the phone, and ring your embassy or "
    "consulate if the passport went with it. Take photos of the report on your phone; paper gets "
    "lost.")


def _stolen_bag(memory, understood):
    """The same theft, but a bag taken abroad is reported to a different police force."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    return STOLEN_BAG_AWAY if any(word in said for word in AWAY) else STOLEN_BAG


# A theft of something that is not a bag has the same first job - a report and a crime reference
# number - and then one thing that depends on what went, because a bike has a frame number and a
# parcel may never have been the person's to insure. The table below names the thing; the reply
# that is not about a bike, a tool or a parcel is the general one.
STOLEN_THING_BIKE = (
    "Report it the same day - 101 or the police's own online form - and give the frame number, "
    "which is stamped under the bottom bracket and is what the police and any insurer check a "
    "found bike against. Then list it as stolen on BikeRegister or 529 Garage, because a bike "
    "that turns up is matched through them, and ring your home contents insurer: most policies "
    "cover a bike taken away from home if it was locked to something fixed, and the claim wants "
    "the report number and the receipt or a photo. Watch the local selling sites for a few days.")

STOLEN_THING_TOOLS = (
    "Report it on 101 the same day and keep the crime reference number, then ring the insurer of "
    "the van and any separate tools cover: tools carried for work are often on a different policy "
    "to the vehicle, and both want a list with serial numbers, photos and receipts. Photograph "
    "the broken lock or window before anything is repaired, tell the employer if the tools were "
    "theirs, and ask the insurer before replacing a big-ticket tool, because some settle at the "
    "trade price.")

STOLEN_THING_PARCEL = (
    "Until a parcel reaches you it is the retailer's problem, not yours: tell them it never "
    "arrived, or that it was left outside and taken, and ask for a replacement or a refund - you "
    "did not choose the courier. Photograph the empty doorstep and the tracking page, check with "
    "the neighbours and anywhere a courier hides things first, and if the retailer refuses, a "
    "card chargeback is the next step, since a card payment protects you for goods not received. "
    "Ask the retailer to send the next one to a locker or with a signature.")

STOLEN_THING_GEAR = (
    "Report it on 101 and keep the crime reference number, then ring your home contents insurer: "
    "an item taken from the house, the car or a bag is usually covered, and the claim wants the "
    "serial number or a photo and the receipt. For a laptop, camera or watch, sign out of the "
    "accounts on it remotely and change the password on your main email, because that is the key "
    "to everything else. If it was taken in a burglary, do not tidy up before the police or the "
    "insurer have seen it.")

_STOLEN_THINGS = (
    (("bike", "bikes", "bicycle", "bicycles", "cycle", "cycles", "e-bike", "ebike"),
     STOLEN_THING_BIKE),
    (("tool", "tools", "toolbox", "tool bag", "toolbag", "drill", "drills", "kit"),
     STOLEN_THING_TOOLS),
    (("parcel", "parcels", "package", "packages", "delivery", "deliveries"),
     STOLEN_THING_PARCEL),
)


def _the_stolen_thing(memory, understood):
    """What was taken decides the reply: a bike, a tool, a parcel, or the general one."""
    said = " " + str((understood or {}).get("clean") or
                      (understood or {}).get("text") or "").lower() + " "
    for names, reply in _STOLEN_THINGS:
        if any(" " + name + " " in said or " " + name + "s " in said for name in names):
            return reply
    return STOLEN_THING_GEAR


_THE_SUM_IN_A_TIP_LINE = re.compile(r"(?:£|\$|\u20ac)?\s*(\d+(?:\.\d+)?)",
                                     re.I)


def _a_sum(value):
    """A pound figure said the way a person would write it: 84, 8.40, 1,020."""
    if value >= 100 or abs(value - round(value)) < 0.005:
        return "\u00a3%d" % round(value)
    return "\u00a3%.2f" % value


def _whole_pounds(low, high):
    """The whole pounds inside a range, said the way a person would: "9 or 10", "10"."""
    first, last = int(low) + (1 if low > int(low) else 0), int(high)
    if first > last:
        return "about %s" % _a_sum(round((low + high) / 2.0))
    if first == last:
        return _a_sum(first)
    return "%s or %s" % (_a_sum(first), _a_sum(last))


def _the_bill_amount(said):
    """The sum a tip line is worked out on, or None when it names none.

    A number in the line is usually the bill, but it is a percentage in "how much is a 15 percent
    tip", a count in "tip for 4 people" and an hour in "a tip at 8", and none of those is a sum.
    """
    for match in _THE_SUM_IN_A_TIP_LINE.finditer(said):
        try:
            value = float(match.group(1))
        except (TypeError, ValueError):
            continue
        after = said[match.end():match.end() + 12].strip()
        if re.match(r"(?:percent|%|people|of us|pints|drinks|hours?|oclock|o.clock)\b", after):
            continue
        if value < 5:
            continue
        return value
    return None


def _tipping(memory, understood):
    """The tip for the thing the line names, in the first sentence."""
    said = ((understood or {}).get("norm_text") or (understood or {}).get("text") or "").lower()
    words = set(re.findall(r"[a-z']+", said))

    def has(group):
        for phrase in group:
            if " " in phrase:
                if phrase in said:
                    return True
            elif phrase in words:
                return True
        return False

    # A service charge on a leasehold flat, a block of flats or an estate is a maintenance charge
    # paid to the landlord, not a tip on a bill, and it has its own answer.
    if has(_TIP_LEASEHOLD):
        return ""
    # Tipping abroad is a country-by-country answer (travel has the table), so a line that names
    # another country is not this one: "should i tip in japan" is not the UK rule.
    if has(_TIP_ABROAD):
        return ""
    if "service charge" in said and not has(_TIP_HAIR + _TIP_TAXI + _TIP_DELIVERY):
        return ("A service charge is a tip that the restaurant has already added to the bill, "
                "usually 10 to 15 percent, and it is discretionary rather than law: you can ask "
                "for it to be taken off or reduced, and they have to show it as a separate line. "
                "If it is on there, that is the tip and you do not leave another.")
    if has(_TIP_HAIR):
        return ("A pound or two, or round it up: a hairdresser or barber usually keeps the change "
                "and a salon is fine with nothing, so ten percent is generous rather than "
                "expected. It is the same on card or in cash, and nobody will chase you for it.")
    if has(_TIP_TAXI):
        return ("Round up, or ten percent on a fare: a couple of pounds on a twelve pound ride is "
                "plenty, and paying the meter exactly is fine too. Taxi drivers here are not paid "
                "on tips the way they are in the States.")
    if has(_TIP_ROUND):
        return ("Not the rest of the year: a postman, a milkman or a bin crew is paid a wage and "
                "nothing is expected. At Christmas a card with a note, or a fiver in it for a crew "
                "you know, is the usual thank you and is optional - and for a postman a card "
                "matters more than the money.")
    if has(_TIP_DELIVERY):
        return ("Nothing is expected: the delivery fee is not a tip, and most drivers see none of "
                "it, so a pound in the app or in cash is a nice extra rather than something you "
                "owe. Round up if the weather is filthy.")
    if has(_TIP_TRADES):
        return ("No: a plumber, an electrician or a builder quotes a price for the job, and that "
                "price is the whole of it. A tip is not expected and can read as odd, so the "
                "thing worth doing instead is offering a tea and paying on time.")
    if has(_TIP_TATTOO):
        return ("Ten to fifteen percent is the going rate, and more on a big piece that ran over "
                "its time: the artist's time is the product, and a tip is the usual thank you. "
                "Cash is still welcome even where the studio takes cards.")
    if has(_TIP_MOVERS):
        return ("Ten to twenty pounds each for a hard day, a long carry or a lot of stairs, and "
                "a round of cold drinks if they will not take cash. Agree it between you before "
                "they start rather than handing money over at the door.")
    if has(_TIP_GUIDE):
        return ("Ten percent on a booked tour or transfer, and the same on a coach excursion "
                "where the guide is not the driver. On a free walking tour the tip is the pay, so "
                "ten to fifteen is the norm and a fiver is not an insult.")
    if any(word in said for word in ("wedding", "reception", "hen do", "stag do")):
        return ("Nothing is owed to the venue: a service charge on a wedding bill is worth "
                "asking about when you book, and it is often 10 to 12 percent. The people who "
                "do get something are the band, the photographer and the bar staff on the night, "
                "and the venue usually passes a bar tip on if you ask.")
    if has(_TIP_RESTAURANT):
        return ("Ten to twelve and a half percent is the norm, and check the bill first: if a "
                "service charge is already on it, that is the tip and you add nothing. If the "
                "service was poor, ask for it to come off before you pay.")
    if has(_TIP_PUB):
        return ("In a pub, nothing: you order and pay at the bar, so there is no table service to "
                "tip. Round up a pound if food was brought to your table, and never feel you have "
                "to.")
    if has(_TIP_CAFE):
        return ("A pound in the jar or nothing at all: a cafe is the one place a tip is entirely "
                "optional, and the person behind the counter does not expect it either way.")
    if has(_TIP_HOTEL):
        return ("A pound or two a night for the cleaner, left with a note or at reception, and a "
                "pound or two for a porter who carries your bags. It is a thank you rather than "
                "part of the price, so nothing is fine too.")
    if has(_TIP_CLEANER):
        return ("Not a tip: pay the hourly rate you agreed, on time, and give a Christmas bonus "
                "or a paid day off rather than loose change each visit. The same goes for a nanny "
                "or a babysitter - round the evening up to the next hour instead.")
    bill = _the_bill_amount(said)
    if bill is not None:
        # "how do i work out a tip on 84 pounds" is arithmetic, not the norm: the person has a
        # bill in front of them and wants the figure. Ten to twelve and a half percent is the
        # range the answer above gives, so it is worked out on the sum the line names.
        low, high = bill * 0.10, bill * 0.125
        answer = ("On %s, ten percent is %s and twelve and a half is %s, so %s to %s"
                  % (_a_sum(bill), _a_sum(low), _a_sum(high), _a_sum(low), _a_sum(high)))
        if high - low >= 2:
            answer += ", and %s is what people leave" % _whole_pounds(low, high)
        return (answer + ". Check the bill for a service charge first, because that is the tip "
                "and you add nothing on top.")
    return ("It is fine not to tip in the UK: wages do not depend on it the way they do in the "
            "States. Ten to twelve and a half percent in a restaurant, once you have checked the "
            "service charge, a couple of pounds to a taxi, and a pound or nothing in a cafe, a pub "
            "or a hairdresser.")


# The things a carrier can lose. The guard below does not depend on this list - see there -
# but it is what the row is about, and the next reader will want it. A bare "i sent" is not a
# postal claim: "i sent an email and it never arrived", "i sent a text", "i sent a message"
# and "she never replied" all reach the claim row through the sender's own verb, and it
# answers them with proof of posting. So the row runs only when the line names something a
# carrier carried, or a sale, and stands down for a medium that is not posted at all.
_POSTED_THING = (
    "parcel", "parcels", "package", "packages", "packet", "packets", "parcel post",
    "letter", "letters", "card", "cards", "birthday card", "christmas card",
    "cheque", "cheques", "check", "passport", "documents", "paperwork", "certificate",
    "present", "presents", "gift", "gifts", "item", "items", "box", "boxes", "envelope",
    "post office", "royal mail", "parcelforce", "parcel force", "courier", "evri", "hermes",
    "dpd", "yodel", "ups", "fedex", "postage", "recorded delivery", "signed for",
    "special delivery", "first class", "second class", "tracked", "tracking",
    # a thing sold and sent is still posted: the buyer is the one waiting
    "ebay", "vinted", "depop", "etsy", "marketplace", "buyer", "sold", "sale",
)
# Not posted, and each has its own answer: an email bounces, a text is not delivered.
_NOT_POSTED = " email e-mail text texts sms dm dm'd whatsapp message messages messaged inbox facebook ".split()


def _a_posted_thing(understood):
    """True unless the thing sent is a medium that is never posted.

    The fence is the medium, not a list of postal objects: "i sent it on monday and it still
    hasnt arrived yet" is a parcel more often than anything else and has no object at all, so
    requiring one lost it, while an email, a text and a message always name themselves.
    """
    said = " ".join(str((understood or {}).get(key) or "")
                    for key in ("clean", "norm_text", "text")).lower()
    if not said:
        return True
    return not any(word in said for word in _NOT_POSTED)


# A passport is not a parcel: the postal claim pays the posting cover and says nothing about the
# document, and the card main gave a missing passport abroad ("contact your embassy") is the
# wrong card for one posted at home. So the same row answers both, and the document picks the
# words. @swift-lizard found the loss: "i posted my passport and it went missing" had the
# police-and-embassy card and the claim took it away.
_PASSPORT_CLAIM = (
    "Report it to HM Passport Office as soon as you know it is gone, so it is cancelled and "
    "cannot be used, and report it to the police as well - keep the crime reference. If you "
    "need to travel soon, ask the Passport Office about an emergency travel document or the "
    "fast-track service rather than waiting for a new one. The carrier's claim covers only "
    "what the posting cost, not the passport fee, so start the replacement the same day."
)
_PARCEL_CLAIM = (
    "Find the proof of posting - the receipt from the counter or the drop-off, or the emailed "
    "label and its barcode - because that is what a claim rests on. Then open a claim with the "
    "carrier you handed it to, not the shop: Royal Mail keeps a lost item claim open from 10 "
    "working days after posting up to 80 days, and pays what the service covers - about \u00a320 "
    "on standard with proof of posting, \u00a350 on Signed For, more on Special Delivery, so "
    "check the cover before you count on it. Put the value and receipts in the claim, and if "
    "the item was tracked, add the tracking number to it. A card or a letter goes the same way."
)


def _claim_reply(memory, understood):
    """The claim, or the document route when the thing that went missing is a passport."""
    said = " ".join(str((understood or {}).get(key) or "")
                    for key in ("clean", "norm_text", "text")).lower()
    if "passport" in said or "passport office" in said or "travel document" in said:
        return _PASSPORT_CLAIM
    return _PARCEL_CLAIM

# The rules a passport photo has to meet. Every photo line still needs them, so they are written
# once and closed with what the person asked for.
_PASSPORT_PHOTO_RULES = (
    "The photo is the part that gets an application sent back: plain light background, no glasses, "
    "mouth closed and a neutral face, taken in the last month, with no shadow on the face. An "
    "online form wants a square digital file rather than a photo of a print, and the size rule is "
    "on your government's site.")

# Where a passport photo is taken. A booth is the quick one, and the shop that checks it is what a
# parent of a small child wants, because a baby's photo is the one that gets sent back.
_PASSPORT_PHOTO_PLACES = (
    "A photo booth is the quickest: about £5 to £8 for a strip, and most are in a supermarket, a "
    "station or a big chemist. A chemist, a camera shop such as Snappy Snaps or Timpson, or a "
    "Post Office takes them for £8 to £12 and checks the photo as it goes, which is worth it for "
    "a baby. Whichever you use, the photo still has to be a plain light background, no glasses, "
    "mouth closed, taken in the last month.")

# A phone photo is the free route, and it is what most people do now for an online application.
_PASSPORT_PHOTO_AT_HOME = (
    "Yes - for an online application a phone photo is fine and it is what most people do: stand "
    "them against a plain light wall in daylight, so the background is bare, with no flash and no "
    "shadow, get someone else to take it from about arm's length at the height of the face, keep "
    "the shoulders in, and crop it square. The form tells you whether it passes before you pay, so "
    "take a few and use the best.")

# What a photo costs, in the same figures the places answer gives: two answers that name two
# prices for a Post Office read as a mistake.
_PASSPORT_PHOTO_PRICE = (
    "About £5 to £8 for a strip of four from a booth, and £8 to £12 in a chemist, a camera shop "
    "or a Post Office, where it is checked as it is taken. A digital code for an online "
    "application is usually included; a passport office's own service costs more again because "
    "the fee is for the check.")

# The words that ask for a place, a price, or the phone in your hand rather than the rules. "Where"
# is the ask that came back with the rules for years, and it is the one the person typed.
_PHOTO_WHERE = re.compile(r"\bwhere\b|\bnear me\b|\bnearest\b|\bshop\b|\bshops\b|"
                          r"\bget (?:it|them|one|a photo|photos?|my photo) (?:taken|done|made)\b|"
                          r"\bbooth\b|\bpost office\b")
# The explicit price ask is read before the place words, because "how much does a passport photo
# cost at the post office" is a price question with a shop named in it, and the shop word must not
# take it. Bare "cheap" and "expensive" come after the place, so "where can i get a cheap one" is
# still answered with where.
_PHOTO_PRICE = re.compile(r"\bhow much\b|\bcost\b|\bcosts\b|\bprice\b|\bprices\b|"
                          r"\bcharge\b|\bcharges\b|\bfee\b|\bfees\b")
_PHOTO_CHEAP = re.compile(r"\bcheap(?:est)?\b|\bexpensive\b|\bafford\b")
# "my phone" rather than a bare "phone": a photo line with no where or price word should not be
# read as a phone-photo ask just because it says phone somewhere.
_PHOTO_AT_HOME = re.compile(r"\bmyself\b|\bat home\b|\bmy own (?:passport )?photo\b|"
                            r"\bown (?:passport )?photo\b|\bdo my own\b|\bmy phone\b|"
                            r"\bon my phone\b|\bwith my phone\b|\bphone camera\b|"
                            r"\bselfie\b|\bphotograph (?:it|them) myself\b")


def _the_photo_answer(text):
    """The passport photo line answered in the form it was asked: where, how much, or the rules.

    Every photo line came back with the rules, because the branch below read the word "photo" and
    nothing else. "Where can i get a passport photo" and "how much does a passport photo cost"
    are their own questions, and the person typing them already knows a photo is needed: they
    want the place or the price. Each answer still closes with the rule that decides whether the
    photo is used, because that is what saves a second trip.
    """
    if _PHOTO_PRICE.search(text):
        return _PASSPORT_PHOTO_PRICE
    if _PHOTO_WHERE.search(text):
        return _PASSPORT_PHOTO_PLACES
    if _PHOTO_AT_HOME.search(text):
        return _PASSPORT_PHOTO_AT_HOME
    if _PHOTO_CHEAP.search(text):
        return _PASSPORT_PHOTO_PRICE
    return _PASSPORT_PHOTO_RULES


def _passport_queue(memory, understood):
    """Applying for, renewing or photographing a passport: what it takes and how long to allow."""
    text = understood.get("clean") or ""
    if re.search(r"\bphotos?\b|\bphoto rules\b|\bpictures?\b", text):
        return _the_photo_answer(text)
    # A passport that has gone is a renewal. One that runs out later is the six-month rule, which
    # is the row below this one: "runs out in june and we fly in september" wants what other
    # countries ask for on arrival, not to be told it has expired.
    if re.search(r"\bhas expired\b|\bexpired\b|\bout of date\b|\bran out\b|"
                 r"\bhas run out\b", text):
        return ("An expired passport cannot be extended, so that is a renewal: apply now rather "
                "than at the airport, because the old one is cancelled before the new one is "
                "issued. You need the old passport, a recent digital photo and payment, and it is "
                "up to ten weeks, so do not book anything you cannot cancel until the new one is "
                "in your hand.")
    # A passport that runs out later is a renewal to start now, and the trip it clashes with is
    # the six-month rule: "my passport runs out in june and we fly in september" wants both.
    # "expires in october" and "expires in 3 months" are the same shape as "expires soon", and
    # they were falling through to the generic how-to-apply text below: widening the first
    # alternative to any "expires in/on/at/next" keeps the six-month rule on all of them.
    if re.search(r"\bexpires? (?:in|on|at|next)\b|\bexpires? soon\b|\bexpiring\b|\bruns out\b|"
                 r"\bout in (?:january|february|march|april|may|june|july|august|september|"
                 r"october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\b",
                 text):
        return ("Start the renewal now rather than waiting for it to lapse: allow up to ten "
                "weeks, and check the rule for where you are going, because most countries want "
                "six months left on your passport beyond the day you come back. Do not book "
                "anything you cannot move until the new one is in your hand.")
    # A passport for a child is the same application plus the child's own papers.
    if re.search(r"\b(?:my|our) (?:son|daughter|child|boy|girl|baby|kid|kids|children)\b|"
                 r"\bchild'?s passport\b|\bbaby'?s passport\b", text):
        return ("A child's first passport is its own application: you need their birth certificate "
                "and the other parent's details as well as a photo and payment, and both people "
                "with parental responsibility usually have to be accounted for. Apply once you "
                "have the certificate, because that is the thing that holds it up, and allow up "
                "to ten weeks.")
    # How long a passport lasts is not how long getting one takes: "how long is my passport
    # valid for" was answered "allow up to ten weeks", which is a wrong number rather than a
    # hedge. Ten years for an adult, five for a child, and the six-month rule on top.
    if re.search(r"\bvalid (?:for|until|till)\b|\bhow long (?:is|are)\b[^?]*\bvalid\b|"
                 # "how many years", "how long does it last" and "when does it expire" are the
                 # lifetime question. Bare "last" is not: "i lost my passport last year" and "i
                 # flew last week" are the lost-passport and flight questions, and a `\blasts?\b`
                 # alternation matched "last year" and gave them the ten-year rule (the deck chat
                 # `single-4725`). The lifetime branch keeps the words that mean a lifetime.
                 r"\bhow many years\b|"
                 r"\blast(?:s|ed)?\b(?!\s(?:year|night|week|weekend|month|summer|winter|spring|"
                 r"autumn|christmas|time|sunday|monday|tuesday|wednesday|thursday|friday|"
                 r"saturday))|\bexpires? after\b|"
                 # "when does it expire" is the same question as "how long is it valid for",
                 # and it was answered from the top of this row - how to apply, allow ten
                 # weeks - at the one moment it matters. A follow-up a turn after a renewal
                 # question got "Ten weeks." instead, which is the processing time.
                 r"\bwhen (?:does|do|will|did)\b[^?]*\bexpire\b|\bexpiry date\b|"
                 r"\bexpires?\b|\bexpiring\b", text):
        return ("Ten years for an adult passport and five for a child's, counted from the issue "
                "date, and a renewal keeps the same number. That is how long it lasts, not how "
                "long it takes: most countries also want six months left on it beyond the day "
                "you come back, so check the dates against the trip before you book anything.")
    # In a hurry is the fast routes, not the ten weeks: "how do i get a passport urgently" was
    # answered "check the processing time", which is the wrong half of the answer.
    if re.search(r"\burgent(?:ly)?\b|\bquickly\b|\bquick\b|\basap\b|\bhurry\b|"
                 r"\brush\b|\bfast track\b|\bfast\b|\btomorrow\b|\bnext week\b|"
                 r"\bthis week\b|\bin a (?:few )?days\b|\bemergency\b", text):
        return ("The fast routes are a one-week fast-track application and a premium appointment "
                "at a passport office for a same-day decision, and both cost more than the "
                "standard fee. Take your old passport, a photo and proof of the travel date to an "
                "appointment, or send them with a fast-track application, and check the fee and "
                "the wait on your government's passport site first rather than ringing round.")
    # The ask that is only about time leads with the time: "how long does it take to get a
    # passport" was answered with the papers first and the wait in the third sentence.
    if re.search(r"\bhow long\b|\bwait(?:ing)?\b|\bsoon\b|\bprocessing\b", text):
        return ("Allow up to ten weeks for a standard application, and treat that as the planning "
                "figure rather than a promise: check the current wait on your government's "
                "passport site, because it moves with the season. If you need it sooner, that "
                "site sells a faster service and a premium appointment - pay for it, keep the "
                "reference, and do not book anything you cannot move until the passport is in "
                "your hand.")
    return ("Apply or renew through your government's passport service, online if it allows it: "
            "you need your current or most recent passport, a recent digital photo and payment, "
            "and the old passport goes back by post if they ask for it. Allow up to ten weeks, "
            "and do not book travel until the new one is in your hand - the fee and the current "
            "wait are on that site, because both change.")


# "what is a tenancy agreement" is the definition question and "where is my copy" is the right to
# one: the two share a subject and want different answers, so the row reads which was asked.
_TENANCY_DEFINITION = ("A tenancy agreement is the contract between you and the landlord: the rent "
                       "and what it includes, how long the tenancy runs, the notice each side "
                       "gives, the deposit and which protection scheme holds it, and who repairs "
                       "what. Read it before you sign, especially the break clause and any fees, "
                       "and keep your copy - your landlord has to give you one, along with the "
                       "deposit protection certificate, the gas safety certificate and the energy "
                       "performance certificate.")


def _tenancy_copy(memory, understood):
    said = " " + " ".join(str((understood or {}).get(key) or "").lower()
                          for key in ("clean", "text", "norm_text")) + " "
    if any(mark in said for mark in (" what is ", " whats ", " what's ", " explain ",
                                     " what does ", " mean ", " means ")):
        return _TENANCY_DEFINITION
    return ("Your landlord has to give you a copy of the tenancy agreement, so ask in writing - a "
            "text or email is enough - and keep it. Ask in the same request for the deposit "
            "protection certificate, the gas safety certificate and the energy performance "
            "certificate: none of those are optional. If they still will not, your council's "
            "tenancy relations officer can put pressure on, and the deposit scheme will confirm "
            "whether it was protected.")


# "fine" is a mood a dozen times for every time it is a fine: "got there early and it was fine",
# "she was fine until we got engaged", "the seal is fine, i mean the little filter". The row below
# is for the noun, so a line that uses the word as an adjective and names no court, no money and
# no letter keeps whatever else answers it.
_FINE_AS_A_MOOD = re.compile(
    r"\b(?:was|is|are|were|be|been|feels?|seems?|looks?|doing|perfectly|absolutely|totally|"
    r"that's|thats|it's|its|i'm|im|all|still|quite|just)\s+"
    r"(?:all\s+|quite\s+|absolutely\s+|perfectly\s+|totally\s+|just\s+|very\s+|really\s+"
    r"|so\s+)?fine\b")

# The words that make it the noun again whatever else the line says: a court, a payment, a
# summons. "my notice is 4 weeks so thats fine" names the letter and still is not a fine.
_FINE_IS_THE_NOUN = ("court", "summons", "magistrate", "magistrates", "prison", "jail",
                     "bailiff", "bailiffs", "enforcement", "plead", "pleading", "guilty",
                     "unpaid", "unpaid fine", "didnt pay", "didn't pay", "havent paid",
                     "haven't paid", "cant pay", "can't pay", "cannot pay", "arrears",
                     "council tax", "liability order", "single justice", "mc100", "means form",
                     "instalments", "installments", "fine to pay", "pay the fine",
                     "fine in the post", "fixed penalty", "prosecution", "sentenced")

# The adjectives that actually showed up before "fine": a china plate, a mess, a line, the print,
# an old time. The list is of the adjective readings we have seen, and an unseen word after
# "fine" stays the noun, so a fine that got bigger or came through the door keeps its answer.
_FINE_ADJECTIVE_AFTER = frozenset((
    "china", "cup", "set", "plate", "mess", "line", "print", "time", "day", "night", "week",
    "weekend", "morning", "afternoon", "evening", "weather", "wine", "dining", "art", "arts",
    "meal", "food", "restaurant", "view", "old", "big", "little", "small", "good", "great",
    "point", "detail", "hair", "tooth", "thanks", "thank", "bit", "piece", "work", "state",
    "thing", "fella", "lad", "woman", "man", "people", "city", "drive", "walk", "example",
    "opportunity", "job", "idea", "gesture", "balance", "line", "specimen", "fellow",
    # the mood follows the word too: "i am fine with it", "fine about the court thing",
    # "fine as it is", "fine by me", "fine for now"
    "with", "about", "as", "by", "doing", "too", "now", "enough"))


def _a_fine_is_a_paper(line):
    """True when at least one "fine" in the line is the noun, not a known adjective."""
    for match in re.finditer(r"\bfine\b(?:\s+([a-z0-9']+))?", line):
        word = match.group(1)
        if word is None or word not in _FINE_ADJECTIVE_AFTER:
            return True
    return False


# A feeling in front of a form is not the form. The topic can arrive through a pronoun ("she
# has anxiety about it", four turns into a chat about a daughter starting secondary school), and
# the row then answers the worry with a deadline. A guard and not another avoid word: an avoid
# word joins the vocabulary the whole registry is scored against, and a word added here moved
# unrelated lines off their own rows.
_A_FEELING_ABOUT_IT = re.compile(
    r"\b(?:anxiety|anxious|worried|worry|worries|nervous|scared|frightened|afraid|upset|"
    r"crying|cries|panicking|dreading|dread)\b", re.I)


# The card is a form, so it needs a question about the form. Once the chat has said "secondary
# school" the topic follows the conversation, and then any line that only mentions the school
# reached it: "we live about 2 miles from the school" got the admissions deadline, and so did
# "the school has a buddy system apparently". What the card is for is the word below - applying,
# a deadline, an appeal, a place, a refusal - so a line without one is somebody talking about
# their school, not asking how to get in.
_AN_ASK_ABOUT_A_PLACE = re.compile(
    r"\b(?:apply|applying|applied|application|applications|admission|admissions|appeal|appeals|"
    r"appealing|appealed|register|registering|registration|enrol|enroling|enrolling|enrolment|"
    r"waiting list|deadline|deadlines|catchment|refused|rejected|placed|placing|place|places|"
    r"offer|offers|offered|"
    # The plainest way a person says a school said no: "the school said no what do we do" is a
    # refusal, which is exactly what this card is for (it even says a refusal is appealed), and
    # with only the word "refused" in the key it fell to the complaint card.
    r"said no|turned down|didnt get in|didn't get in|no place|no places|not offered|"
    r"didnt get a place|didn't get a place)\b", re.I)


def _the_line(understood):
    """The line the user typed, from whichever field the reading carries it in."""
    reading = understood or {}
    return str(reading.get("clean") or reading.get("text") or "") or " ".join(
        str(one) for one in (reading.get("words") or ()))


def _an_ask_about_a_place(understood):
    """Whether the line asks about a place rather than saying something about a school."""
    text = _the_line(understood)
    if _A_FEELING_ABOUT_IT.search(text):
        return False
    return bool(_AN_ASK_ABOUT_A_PLACE.search(text))


def _the_fine_is_the_noun(understood):
    """True unless the line is using "fine" as an adjective with nothing about a court in it."""
    line = " " + re.sub(r"[^a-z0-9' ]+", " ",
                        str(understood.get("clean") or understood.get("text") or "").lower()) + " "
    # "fined" and "fines" are the penalty itself, whatever the letter after "fine" suggests: the
    # mood guard below used to match the "fine" inside them and stand the court row down, so
    # "i got fined" was answered with "Noted: you got fined." instead of the court notice.
    if re.search(r"\bfined\b|\bfines\b", line):
        return True
    if _FINE_AS_A_MOOD.search(line):
        return any(word in line for word in _FINE_IS_THE_NOUN)
    return _a_fine_is_a_paper(line) or any(word in line for word in _FINE_IS_THE_NOUN)


# A bigger voluntary excess is a price lever, not a claim: "does a bigger voluntary excess really
# save much" asked what the cover costs and was answered with how to report a claim. The claim
# card keys on "excess", so it stands down when the line asks whether the excess saves money.
_EXCESS = re.compile(r"\bexcess(?:es)?\b|\bpremium\b", re.I)
# The shape that asks what the lever costs: the excess or premium comes first and a price word
# follows it ("does a bigger excess really save much", "is a higher excess cheaper", "bigger
# excess worth it"). "can i reduce my excess" puts the price word in front, which is a question
# about the size of the excess rather than about what it saves.
_EXCESS_PRICE_ASK = re.compile(
    r"\bexcess(?:es)?\b[^.?!]{0,70}\b(?:save|saves|saving|saved|cheaper|cheap|worth|reduce|lower)\b"
    r"|\bpremium\b[^.?!]{0,70}\b(?:save|saves|saving|saved|cheaper|cheap|lower)\b", re.I)
# A line with a claim or a loss in it is the claim card's, even when it also asks what the
# excess costs: "my claim was refused, can i reduce my excess" is about the refused claim.
_A_CLAIM_OR_LOSS = re.compile(
    r"\bclaim\w*|\bdamag\w*|\baccident\w*|\bcrashed\b|\bstolen\b|\bflood\w*|\bleak\w*"
    r"|\bwrite off\b|\bpayout\b|\brefused\b|\bnot covered\b", re.I)


def _the_excess_is_a_price_question(understood):
    text = understood.get("clean") or understood.get("text") or ""
    return not (_EXCESS.search(text) and _EXCESS_PRICE_ASK.search(text)
                and not _A_CLAIM_OR_LOSS.search(text))


# The dictionary row in money_words.py owns "an excess", "insurance excess" and "policy excess";
# this row must not answer those lines too. A price or a loss in the line is the premium answer
# or the claim card's, and "my"/"our" asks for the figure in their own policy, read off the
# schedule. Anything outside the definition's own vocabulary is another subject that happens to
# use the word ("what is excess baggage", "an excess charge on my phone bill").
_EXCESS_DICTIONARY_PHRASE = re.compile(
    r"\ban excess\b|\binsurance excess\b|\bpolicy excess\b|\bdeductible\b", re.I)
_EXCESS_DEFINITION_WORDS = frozenset((
    "what", "whats", "what's", "is", "are", "was", "an", "a", "the", "does", "do", "did",
    "mean", "means", "meaning", "definition", "define", "explain", "explained", "tell", "me",
    "about", "of", "on", "in", "please", "exactly", "actually", "how", "work",
    "works", "excess", "excesses", "voluntary", "compulsory", "insurance", "insurer",
    "insurers", "policy", "policies", "cover", "covered", "premium", "home", "house", "car",
    "buildings", "contents", "travel", "motor", "pet", "health", "dental", "joint", "family",
    "landlord", "tenant", "van", "bike", "motorcycle", "holiday", "trip"))


def _the_excess_is_what_it_means(understood):
    """True when the line asks what a voluntary or compulsory excess is, and not the dictionary row's.

    The dictionary row answers a line that says "an excess", "insurance excess" or "policy excess",
    so this one stands down for it rather than shadowing the same answer. It also stands down for
    a price question ("does a bigger voluntary excess save much"), a claim or loss, and "my"/"our"
    (the figure in their own policy is read off the schedule). A word outside the definition's own
    vocabulary means the subject is something else ("what is excess baggage"), so only a line that
    says nothing but the ask and the policy words gets the answer.
    """
    text = understood.get("clean") or understood.get("text") or ""
    if _EXCESS_DICTIONARY_PHRASE.search(text):
        return False
    if _EXCESS_PRICE_ASK.search(text) or _A_CLAIM_OR_LOSS.search(text):
        return False
    words = re.findall(r"[a-z0-9']+", text.lower())
    if not words or any(word in ("my", "our") for word in words):
        return False
    return all(word in _EXCESS_DEFINITION_WORDS for word in words)


ENTRIES = [
    # --- the address everyone still has ------------------------------------
    entry("moving-address",
          (("change my address", "change of address", "i've moved", "ive moved", "just moved",
            "we've moved", "weve moved", "moving house", "moving in", "new address",
            "after moving", "i moved", "when i move", "new postcode",
            # the insurance that changes when you move is this list, not a claim on it:
            # "how do i change my car insurance when i move" was the damage and excess answer
            "car insurance", "my insurer", "my insurance company", "change my policy"),
           ("address", "who do i tell", "tell", "update", "redirect", "post", "bank", "council",
            "doctor", "dentist", "licence", "license", "insurer",
            # a move is where the changes are asked for: "how do i change my car insurance
            # when i move" names no other word of this key
            "change", "changing", "changed", "update")),
          "Tell the places that fine you or bill you first: the tax office or council, the bank, "
          "your insurer, the driving licence people and your employer's payroll. Then the doctor, "
          "dentist, school and any subscriptions. A mail redirect for three months catches what "
          "you forgot, and it is cheaper than a missed letter.",
          # The move names the change, so this answer beats the claim-and-excess one on a line
          # that asks what changes when you move.
          bias=1,
          # Telling the children about a move is not the address list, and "tell" is in the key:
          # "how do I tell my kids we're moving house" has to reach the answer about the children.
          avoid=("van", "removal", "packing", "boxes", "how much does it cost", "man with a van",
                 "kids", "kid", "children", "child", "son", "daughter", "explain", "upset",
                 # "my insurer" is in the key for the move, so a complaint about the insurer
                 # has to be told apart: that one belongs to escalate-complaint
                 "complain", "complaint", "complaining", "ombudsman", "refused to pay",
                 "they said no", "won't pay", "wont pay")),

    # --- a takeaway that arrived wrong --------------------------------------
    entry("wrong-or-cold-food",
          (("complain", "complaint", "wrong order", "missing item", "cold", "raw", "soggy"),
           ("restaurant", "meal", "takeaway", "delivery", "order", "food", "pizza", "dish",
            "burger", "curry")),
          "Say it while you are still there, politely and once: most places will replace the dish "
          "or take it off the bill rather than argue. For a delivery, photograph it and use the "
          "app's help page the same day. If a restaurant refuses, a short email to the manager "
          "with the date and branch works better than a long complaint.",
          # a frozen pizza that came out soggy is a cooking problem, not a takeaway to complain
          # about: nobody to say it to, and the fix is a hotter oven.
          avoid=("recipe", "cook", "bake", "how long", "freezer", "reheat",
                 "frozen pizza", "frozen pizzas",
                 # "is a raw food diet ok for dogs" is the pet's food, not a takeaway to complain
                 # about: this row was taking the line on `raw` and `food`.
                 "dog", "dogs", "puppy", "puppies", "cat", "cats", "kitten", "kittens",
                 "pet", "pets", "rabbit", "hamster", "raw food diet", "raw feeding",
                 # the same is true when the person is making the thing: "how do i make pizza
                 # dough that is not soggy" and "why is my pizza soggy" were told to ask for
                 # the manager. A complaint is about food somebody else cooked.
                 "make", "making", "made", "homemade", "from scratch", "dough", "oven",
                 "my own", "recipe for", "why is my", "why does my", "why has my",
                 # "my pizza base is soggy" was the takeaway complaint, and there is nobody to
                 # complain to about the one in your own oven: the pastry row owns it.
                 "base", "pizza base", "soggy bottom", "bottom of the", "pastry", "blind bake")),
    # --- the card in your wallet -------------------------------------------
    entry("card-lost",
          (("card", "bank card", "debit card", "credit card", "wallet", "cash machine", "atm"),
           ("lost", "lose", "losing", "gone", "missing", "stolen", "someone used", "fraud",
            "fraudulent", "can't find", "cant find", "left my card", "left my wallet",
            "left it in")),
          "Freeze the card in your bank's app first: most let you unfreeze it, so it costs nothing "
          "if the card turns up. Then order a replacement and read through the last few "
          "transactions. Report anything you don't recognise the same day; you are usually not "
          "liable for spending after you tell the bank.",
          # A card you owe money on is not a card you have lost: the debt answers are money's.
          avoid=("owe", "owed", "pay off", "pay it off", "paying", "balance", "minimum",
                 "interest", "clear",
                 # the second group reads "miss" as "missing", so "what happens if i miss a
                 # credit card payment" and "i missed a credit card payment what now" were a card
                 # lost and frozen. A payment in the line makes it a debt question.
                 "payment", "payments", "miss a payment", "missed a payment", "missed payment",
                 "missed my payment", "missed the payment", "missing a payment", "late payment",
                 "paid late", "overdue", "due date", "arrears", "behind on", "default",
                 "forgot to pay", "forgetting to pay", "didnt pay", "didn't pay", "unpaid",
                 "keep forgetting", "on time")),

    # --- a bag stolen rather than mislaid ---------------------------------
    # "My bag was snatched" is not "I lost my bag": the order of what to do is cancel, block,
    # report, and then the keys and the address if they were in it. Keyed on the container so a
    # snatched handbag, purse, backpack and suitcase all reach it, and on the ways people write
    # a theft, which are not the words for losing something.
    entry("bag-stolen",
          (("bag", "handbag", "purse", "wallet", "backpack", "rucksack", "suitcase", "holdall",
            "satchel", "briefcase", "tote", "pocket"),
           ("stolen", "snatched", "snatch", "pickpocketed", "pickpocket", "nicked", "mugged",
            "robbed", "thieves", "someone stole", "someone took", "took my bag", "gone missing",
            "went missing", "picked my pocket", "pocket was picked", "went in my pocket")),
          _stolen_bag,
          # a misplaced bag is a different problem, the phone has its own row, and a theft with a
          # person threatened in it belongs to the safety answers, not here.
          avoid=("left my bag", "left it on", "lost my bag", "found a bag", "where did i put",
                 "forgot my bag", "phone", "mobile", "bicycle", "bike", "motorbike", "my car",
                 "my van", "burgled", "burglary", "broke in", "at knifepoint", "knife", "gun",
                 "attacked", "hit me", "held me", "chased", "how much", "insurance claim",
                 "claim on my", "worth", "fell out", "garden", "plant", "seed", "tea bag",
                 # a bag lost or taken in a hotel room is the hotel's own liability card: the
                 # £50 an item rule and the safe-keeping receipt are what that line wants, not
                 # the freeze-your-cards list, which is for a bag taken out in the street
                 "hotel room", "in my hotel", "from my hotel", "at my hotel", "the hotel room",
                 "room safe", "hotel safe", "left in the room"),
          bias=1),

    # --- something that is not a bag was taken -----------------------------
    # A bike, a parcel, a tool and a laptop taken are the same first job with one thing after it,
    # and none of them was answered: "my bike was stolen" was told how to lock a bike, "someone
    # stole my parcel" was the meeting-speech card on the word "claim", and "my tools were
    # stolen from my van" was a plain acknowledgement. The container rows above own a bag, a
    # wallet and a pocket; this row owns what was inside or beside them.
    entry("a-thing-was-stolen",
          (("bike", "bikes", "bicycle", "bicycles", "cycle", "cycles", "e-bike", "ebike",
            "parcel", "parcels", "package", "packages", "delivery", "deliveries",
            "tool", "tools", "toolbox", "tool bag", "toolbag", "drill", "drills",
            "laptop", "laptops", "macbook", "tablet", "ipad", "camera", "cameras",
            "jewellery", "jewelry", "watch", "watches", "ring", "rings", "necklace",
            "earrings", "gold", "silver", "kit", "gear", "stuff", "things", "present",
            "presents", "gift"),
           ("stolen", "stole", "stoles", "thief", "thieves", "theft", "nicked", "pinched",
            "snatched", "robbed", "burgled", "burglary", "broke in", "broken into",
            "gone missing", "went missing", "someone took", "someone took it",
            "took my", "took it", "was taken", "were taken", "has been taken",
            "been stolen", "was stolen", "got stolen", "is stolen", "half inched")),
          _the_stolen_thing,
          # a bag, a purse and a pocket are the row above, a phone has its own, and how to keep a
          # bike from being taken is the lock's question rather than this one.
          avoid=("wallet", "purse", "handbag", "backpack", "rucksack", "bag", "bags",
                 "suitcase", "holdall", "pocket", "phone", "mobile", "iphone", "android",
                 "passport", "card", "cards", "bank card", "debit card", "credit card",
                 "motorbike", "motorcycle", "scooter", "moped", "my car", "car was",
                 "van was", "catalytic", "number plate", "keys", "how do i stop",
                 "how can i stop", "how to stop", "stop it being", "being stolen", "getting stolen",
                 "get stolen", "prevent", "keep it safe", "best lock", "which lock",
                 "what lock", "how do i lock", "how to lock", "at knifepoint", "knife", "gun",
                 "attacked", "hit me", "held me", "threatened", "chased", "followed me",
                 "found a", "i found", "someone gave me",
                 # a parcel that has not turned up is the delivery row's, which says the retailer
                 # owes the replacement: this row is for one that was taken, not one that is late
                 "doorstep", "never arrived", "not arrived", "hasnt arrived", "hasn't arrived",
                 "didnt arrive", "didn't arrive", "no sign of", "tracking"),
          bias=2),

    # --- who gets what for carrying the bag -------------------------------
    entry("tipping",
          (("tip", "tipping", "tips", "gratuity"),
           ("how much", "should i", "supposed to", "expected", "normal", "rude", "enough",
            "hairdresser", "barber", "waiter", "waitress", "restaurant", "taxi", "driver",
            "delivery", "takeaway", "bartender", "bar", "percent", "%", "cash",
            # Who the money goes to is half the question, and a job word here is what makes
            # "do you tip a tattooist" two words of this table rather than one: the tip word
            # alone is a single match, so the line used to reach no answer at all. A trade is
            # the exception and has its own row in home, where the line's own topic lands.
            "tattoo", "tour guide", "mover", "movers", "wedding", "hotel", "housekeeping",
            "cafe", "coffee", "barista", "nails", "massage", "spa", "porter", "concierge",
            "cleaner", "cleaning lady", "nanny", "babysitter", "takeaway driver",
            # The person who brings it is named in as many ways as there are couriers: "do you
            # tip the courier" reached no row at all, because the tip word alone is one match
            # and the key wanted a second one. The delivery reading below already answers it.
            "courier", "couriers", "postman", "postie", "parcel", "parcels", "delivery rider",
            "amazon driver", "the driver", "postie", "milkman", "bin men", "dustmen",
            # "is a service charge the same as a tip" is a tip question with the charge's name in
            # it, and the reading below answers it: the charge is the tip, already added.
            "service charge", "discretionary", "optional")),
          _tipping,
          # This is the at-home answer, so a line that names another country passes: the travel
          # table has the country-by-country one, and 10 to 15 percent is the wrong first
          # sentence for Japan, France or the States.
          # The list of places is the same one the function passes on, so a city added there is
          # not answered here by accident.
          _TIP_ABROAD + ("in us", "states",
                         # the tips of a thing are not money for a person, and "white tips on my
                         # nails" reached this row through the nail-technician key word
                         # (polite-cord, #answers)
                         "tips of", "at the tips", "white tips", "brown tips", "split ends",
                         "dry tips", "fingertips", "finger tips", "nail polish", "toenails",
                         "cuticles")
          # The other "tip" is the place rubbish goes: "should i go to the tip or is there a
          # collection" was answered "it is fine not to tip in the UK", and "do i need to book
          # the tip" got the restaurant rule. The waste domain has the site's own row, so a line
          # that says the place is not this one. The bare word stays, because the ask words it
          # needs ("should i", "how much") are the ones a tipping question uses: "should i tip
          # the bin men" has no "the tip" in it at all.
          + _TIP_THE_PLACE),

    # --- the child on their own --------------------------------------------
    entry("home-alone-kids",
          (("home alone", "on their own", "on his own", "on her own", "left alone",
            "leave them alone", "unsupervised", "babysitting age", "latchkey"),
           ("kid", "kids", "child", "children", "son", "daughter", "how old", "old enough",
            "age", "school", "year old")),
          "There is no single age: what matters is whether they can get help, know what to do if "
          "something goes wrong and can reach you. Check your country's or area's guidance, since "
          "some give an age, and start with short daytime trips. A neighbour who knows them and a "
          "phone they can answer matter more than the number.",
          # "how do i get my 4 year old to sleep on his own" is a bedtime question with
          # "on his own" in it, not a question about leaving a child unsupervised, so the sleep
          # words stand this entry down and the bedtime entries answer it.
          avoid=("dog", "cat", "pet", "plant", "house", "car",
                 "sleep", "sleeps", "sleeping", "asleep", "bed", "beds", "bedtime", "cot",
                 "crib", "nap", "naps")),

    # --- paperwork with a queue --------------------------------------------
    entry("passport-how-long",
          ("passport", ("how long", "renew", "renewal", "apply", "applying", "application",
                        "expire", "expires", "expired", "wait",
                        # the same thing said without the word expire: a passport that has run
                        # out or gone out of date is still a renewal.
                        "ran out", "runs out", "run out", "has run out", "out of date",
                        "expires soon",
                        "time", "fast track", "urgent", "processing",
                        # "how do i get a passport quickly" is the same question asked in a
                        # hurry: quick, soon and asap are the words people use for it
                        "quickly", "quick", "fast", "asap", "soon", "soonest", "hurry",
                        "rush",
                        # "i need a new passport" and "how do i get a new passport" name the
                        # job and none of the words above: new, get and need are the asking
                        "new", "new one", "get", "getting", "need", "needed", "first",
                        "first one", "paperwork", "documents", "what do i need", "bring",
                        # how long it lasts, and the photo rules, are answered inside the
                        # queue, so those words are in the key rather than the avoid
                        # "lasts" is not on its own here: it stems to "last", and "i lost my
                        # passport last year can i still fly" was taken by this row on it. The
                        # whole phrases below say the same thing without catching a lost one.
                        "valid", "how long is a passport", "how long does a passport last",
                        "how long does my passport last", "how long a passport lasts",
                        "photo", "photos")),
          _passport_queue,
          # "what do i need for a passport application" was the before-you-go countdown, which
          # says to check the six months and book what sells out and never says how to apply, so
          # this row has to win the tie rather than draw it.
          bias=1,
          # a passport that has run out is told rather than asked ("my passport has expired"),
          # and that line still wants the answer, so the expiry itself counts as the asking.
          ask=("how", "what", "do i", "can i", "should i", "need", "much", "long", "where",
               "when", "expired", "expires", "expiring", "has expired", "ran out", "runs out",
               "run out", "out of date", "soon"),
          # "how do i get a passport quickly" is the same question asked hurriedly, and the
          # words people use for that are quick, soon and asap, not only urgent and fast track
          # a photo is the photo rules, not the queue, so that line is not answered here
          avoid=("lost", "lose", "losing", "stolen", "stolen passport", "missing",
                 "lost passport", "visa", "id card",
                 "where should i keep", "keep it safe", "keep safe",
                 # "does my passport need 6 months left" is the rule on arrival, and it lost its
                 # answer to the how-to-apply text: any line that says how much time is left is
                 # the travel rule's question, not this row's.
                 "6 months", "six months", "months left", "months on it", "months remaining")),
    entry("pothole-report",
          (("pothole", "potholes", "hole in the road", "road surface", "kerb", "sunken drain",
            "street light", "street lamp", "pavement"),
           ("report", "reporting", "complain", "complaint", "fix", "fixed", "claim", "damage",
            "who do i", "where do i", "how do i", "council", "tyre", "tire", "wheel", "dented",
            "dent", "broken", "not working", "out", "dark")),
          "Report it to the highways team of the council that owns that road - not the police or "
          "the parish - using the map form on their website: drop a pin, add a photo and keep the "
          "reference number it gives you, because a fixed reference is what makes the next report "
          "count and it is the first thing a claim asks for. Street lights, kerbs and pavements go "
          "to the same team. If it damaged a tyre or a wheel, use the council's own claims form "
          "with the repair invoice and two quotes: the council can defend itself by showing it "
          "inspected the road on schedule, so your earlier reference is the strongest thing you "
          "hold.",
          avoid=("pothole in my tooth", "tooth", "teeth", "gum", "gums", "dentist", "filling"),
          bias=2),
    entry("passport-arrived-late",
          (("passport", "driving licence", "licence", "visa"),
           ("not arrived", "late", "delayed", "still waiting", "weeks", "months", "chasing")),
          "Chase it through the route you applied by, with the reference number and the date the "
          "application was received, rather than a general enquiry line. Ask for it to be marked "
          "urgent if travel is booked and send proof of the booking. Keep the reference in the "
          "email thread so nobody has to start the story again.",
          avoid=("how long", "renew", "expire", "runs out", "valid for", "enough time",
                 "months left")),
    entry("passport-child",
          ("passport", ("baby", "babies", "child", "children", "kid", "kids", "infant",
                        "newborn", "toddler", "under 16", "under five", "under 5")),
          "A child's passport is applied for by someone with parental responsibility, with the "
          "child's birth certificate, a photo showing the whole face and a countersignature where "
          "the form asks for one. In the UK use the online service and send the old passport if "
          "there is one. A child's passport lasts five years, and standard processing takes a few "
          "weeks, so do not book flights until it is in your hand.",
          ask=("how", "apply", "get", "need", "needs", "renew", "where", "can", "should",
               "do i", "what"),
          # register-a-birth names "baby" too, which took the rarity of the word away from this
          # entry and dropped it into a tie with passport-how-long on "how do i apply for a
          # passport for my baby": the child's passport is the answer that line wants.
          avoid=("dog", "cat", "pet", "lost passport", "stolen passport", "visa"), bias=1),

    # --- the record of your birth ------------------------------------------
    entry("birth-certificate-copy",
          (("birth certificate", "birth certificates", "birth cert", "long birth certificate"),
           ("copy", "copies", "certified", "order", "ordering", "replacement", "get one",
            "where do i", "how do i", "lost")),
          "Order a certified copy from the office that holds the record, not a photocopy of your "
          "own: in the UK that is the General Register Office online, about £12.50 for a standard "
          "copy with more for a fast one, and it arrives in a few days. Passport and licence "
          "applications want the certified version, so keep the one they send you flat in the "
          "folder with your other documents.",
          avoid=("name", "change my name", "christening", "baptism", "how long")),

    # --- the licence in the drawer -----------------------------------------
    entry("licence-renewal",
          (("driving licence", "driving license", "photocard", "licence", "license"),
           ("renew", "renewing", "renewal", "renewed", "runs out", "expires", "expired",
            "how long", "take", "waiting", "arrived", "how much", "photo", "online", "drive while",
            "being renewed",
            # "out of date" is how most people say expired, and it named no renew word, so
            # "my driving licence is out of date" found nothing here at all.
            "out of date", "out of date now", "past its date", "ran out", "still valid",
            "still in date", "is it valid")),
          "Renew it online on the driving agency's site (gov.uk in the UK) with a new photo: it costs "
          "about £14 to £17 and usually arrives within a week. You can normally keep driving while "
          "the renewal is being processed, under what is called section 88, as long as your doctor "
          "has not told you to stop and the licence was not taken away rather than simply expired.",
          # a TV licence, a dog licence and a fishing licence are renewed somewhere else
          avoid=("insurance", "tax", "mot", "provisional", "points", "penalty", "address",
                 "car", "van", "bike", "tv", "television", "dog", "fishing", "rod")),

    # A licence that has gone is a different job from the one that has run out: there is no
    # renewal date to give, there is a replacement to order, and if it was stolen there is a
    # police report to make first. "i lost my driving licence" and "my driving licence was
    # stolen" had no answer at all beyond a sympathy line, and "i need a replacement driving
    # licence" reached the joint-replacement timeline, which said when it could drive again
    # after the operation.
    entry("licence-lost",
          (("driving licence", "driving license", "photocard", "licence", "license"),
           ("lost", "lose", "losing", "mislaid", "misplaced", "cant find", "can't find",
            "cannot find", "gone missing", "stolen", "was stolen", "has been stolen",
            "replacement", "damaged", "torn", "washed", "name change", "change my name",
            "changed my name", "new address", "moved house", "change of address")),
          "Order a replacement through the driving agency's site (gov.uk in the UK): about £20, "
          "a new photo and it usually arrives within a week, and a change of name or address is "
          "free. If it was stolen, tell the police first and keep the crime reference, because a "
          "licence in someone else's hands is identity theft - and tell the agency it was stolen "
          "rather than lost. You can usually keep driving while a replacement is being processed "
          "as long as you have applied and your doctor has not told you to stop.",
          avoid=("renew", "renewal", "expires", "expired", "runs out", "insurance", "tax",
                 "mot", "provisional", "points", "penalty", "tv", "television", "dog",
                 "fishing", "rod", "birth certificate")),

    # --- the tariff nobody reads -------------------------------------------
    # --- the tyre on the drive ----------------------------------------------
    entry("tyre-flat",
          (("tyre", "tyres", "tire", "tires", "puncture", "spare wheel"),
           ("flat", "puncture", "change", "changing", "blown", "blowout", "spare", "jack",
            "blow", "wobble", "hisssing", "hissing", "burst", "shredded", "bulging",
            "bulge", "needs changing", "needs replacing", "off the rim",
            # the word "puncture" is in both parts, so a line whose only key word is "puncture"
            # covered one word and scored nothing ("i got a puncture what do i do" got the shrug).
            # The phrase that names the trouble covers those extra words, so the line scores.
            # What is never a key word here is a phrase that only names the asking: "what should
            # i do", "do i do", "got a", "have a" are the same words in every other answer's
            # follow-up, and a group made of them answers a bare "what should i do" with a wheel
            # change ("im always tired" / "what should i do" got exactly that). No bare "help":
            # "i need help with my tyres" names no symptom, and the answer is a wheel change that
            # may not be the problem. No bare "fix" or "repair" either: "should i fix the tyre
            # or scrap the car" and "can i repair a puncture myself" are asking whether it can be
            # mended, and the wheel change is the wrong job for them.
            "got a puncture", "got a flat", "have a puncture", "have a flat", "blow out",
            "blew out", "went down",
            # the ask bound to the thing: "what should i do about my tyre" names the tyre twice
            # over, so it scores on the subject without any help from the asking.
            "about my tyre", "about my tyres", "about the tyre", "about the tyres",
            "about my puncture", "about the puncture")),
          "Pull over somewhere safe, hazards on, handbrake on. Loosen the wheel nuts a quarter "
          "turn before you jack it up, because they will not move in the air. Jack at the "
          "handbook's point, swap the wheel, nuts finger tight, lower it, tighten in a star "
          "pattern. Keep to 50mph on a spacesaver. A hole in the tread can be repaired; a cut in "
          "the sidewall cannot.",
          # the mending questions sit beside the wheel change but are a decision, not a job:
          # worth it or not, plug it or scrap it, what a slow leak means.
          # bare "change" is in the key, so the lifetime question ("how do i know when to change
          # my tyres") scored here and got the jack and the wheel brace. How long a set lasts is
          # tyre-life's answer; this entry keeps the tyre that is flat now.
          avoid=("pressure", "bar", "psi", "mot", "insurance", "bike", "bicycle", "car seat",
                 "seat belt", "child seat", "skipping", "skip", "scrap", "scrapping",
                 "worth fixing", "worth repairing", "trade in", "slow puncture",
                 "when to change", "when should i change", "when do i change", "how often",
                 "how long do", "how many miles", "how old", "replace my tyres",
                 "replace the tyres", "replacing my tyres", "new tyres", "need new tyres",
                 "worn", "wear", "tread", "legal", "bald", "years"), bias=1),
    entry("tyre-blowout-moving",
          (("tyre", "tyres", "tire", "tires", "puncture", "wheel", "blowout", "blow out",
            "blew out", "burst", "exploded"),
           ("motorway", "dual carriageway", "dual-carriageway", "hard shoulder", "fast lane",
            "middle lane", "outside lane", "slip road", "at speed", "doing 70", "70mph",
            "at 70", "at 60", "at 50", "mph", "while driving", "driving home", "was driving",
            "driving along", "on the m1", "on the m4", "on the m5", "on the m6", "on the m11",
            "on the m25", "on the m40", "on the m60", "on the m62")),
          "Get left and off the carriageway if you still can, then hazards on. Everyone out of "
          "the doors on the left, behind the barrier, and well back from the car: never stand "
          "between it and the traffic, and never change a wheel on a motorway. Leave the warning "
          "triangle in the boot. Ring 999 if you are stuck in a live lane.",
          avoid=("pressure", "bar", "psi", "mot", "insurance", "before a long drive"),
          bias=2),
    entry("hard-shoulder-stuck",
          (("hard shoulder", "live lane"),
           ("im on", "i'm on", "stuck", "stranded", "waiting", "what do i do", "how long",
            "is it safe", "safe", "now",
            # a report about the shoulder is the same question as being on it: "the hard shoulder
            # had glass on it" was answered with the ganglion-cyst card, and the day pool then
            # congratulated them on their day. The shoulder is the dangerous part of the road
            # however it is mentioned.
            "had", "has", "was", "were", "glass", "debris", "rubbish", "tyre", "puncture",
            "blew", "blowout", "stopped", "stop", "pull over", "pulled over", "broken glass")),
          "Stay behind the barrier, not beside the car, and keep a coat on: the hard shoulder is "
          "the most dangerous part of the road. Ring 999 if you cannot get behind the barrier or "
          "you are in a live lane, then your breakdown service. Wait for the recovery truck to "
          "reach you rather than walking up the verge to a sign.",
          bias=2),
    entry("energy-switch",
          (("energy", "electricity", "gas and electric", "supplier", "tariff", "energy bill",
            "energy prices"),
           ("switch", "switching", "change supplier", "compare", "cheaper", "fixed", "deal",
            "shop around", "worth it",
            # leaving is the same question as switching: what does it cost and how long
            "leave", "leaving", "get out", "exit fee", "exit fees", "without a fee",
            "cancel my contract")),
          "Have a recent bill ready, because the comparison needs your usage in kWh rather than "
          "pounds. Then pick a fixed deal and let the new supplier do the switch: it takes about "
          "three weeks, your old supplier contacts you rather than the other way round, and there is "
          "a 14-day cooling-off period. Check the exit fee on your current tariff first, since that "
          "is the only cost a switch can carry.",
          avoid=("boiler", "radiator", "meter reading", "standing charge", "cant afford",
                 "can't afford", "bill went up", "bill is too high", "direct debit", "pay by",
                 "payment plan", "prepayment", "pay as you go"),
          bias=1),

    # --- the price someone will take, and the coat that was reduced --------
    # The price, not the policy on reduced goods: people ask this about sofas, phones, cars
    # and market stalls, and every one of them is the same two sentences - ask a person with
    # authority, name a number you have seen elsewhere, and be ready to walk away.
    # Ringing about a price is not the same as haggling at a till, and it is not the shop
    # discount answer either. A renewal, a tariff or a contract is renewed at a price somebody
    # on a phone can move, so the useful answer is the call itself: which team to ask for, what
    # to say, and what to write down. "and can i just ring them and ask for a better price",
    # straight after the car insurance renewal answer, was getting the cold-calls card.
    entry("ring-about-a-price",
          (("better price", "lower price", "cheaper price", "cheaper deal", "better deal",
            "money off", "knock it down", "reduce my bill", "lower my bill", "lower the price",
            "bring the price down", "bring it down", "haggle", "haggling", "negotiate",
            "negotiating",
            # the same ask with no price word in it: people say "ring them about the bill" and
            # "get a lower premium", and "can i call them about my bill" was reaching nothing
            "lower premium", "cheaper premium", "reduce my premium", "lower my premiums",
            "about my bill", "about the bill", "about my renewal"),
           ("bill", "bills", "renewal", "premium", "premiums", "tariff", "contract",
            "subscription", "subscriptions", "insurance", "broadband", "energy", "supplier",
            "provider", "company", "insurer", "ring", "ringing", "call", "calling", "phone",
            "phone them", "ask", "asked", "speak to", "talk to", "them")),
          "Ring and ask for the retentions or cancellations team, because that is the line "
          "allowed to move a price: say \"I've had a cheaper quote at \u00a3X - what can you do?\" "
          "Have that quote in front of you, be ready to say you will switch, and ask what the new "
          "price ties you into. Write down the date, the name of the person and what they "
          "promised, and check the first bill; if you are still in contract there may be an exit "
          "fee, and it is only worth paying if the saving beats it.",
          # things that are not a price on a bill: water is metered, tax and fines are set, a
          # refund or a fault is its own question, and a car or a sofa is haggled for in person
          avoid=(# a shop's discount is the till answer, not a retentions team: "how do i ask for
                 # a discount" is the market and the ex-display model, so these stand down
                 "discount", "discounts",
                 # two people arguing about the bills is not a call about a price: "we keep
                 # arguing about the bills" reached this row on "about the bill" and got told to
                 # ask for the retentions team
                 "arguing about", "argue about", "argued about", "argument about",
                 "arguments about", "row about", "rows about", "keep arguing",
                 "keeps arguing", "always arguing", "constantly arguing",
                 "car", "cars", "dealer", "dealership", "forecourt", "garage", "garages",
                 "repair", "repairs", "mechanic", "sofa", "fridge",
                 "washing machine", "water", "water bill", "council tax", "tax", "fine",
                 "parking", "refund", "faulty", "wrong size", "money back", "benefit",
                 "pension", "ticket", "prescription", "rent", "mortgage", "mortgage payment",
                 "landlord", "cold call", "cold calls", "nuisance", "spam"),
          # "can i haggle my broadband down" ties with the till answer on "haggle" plus a generic
          # ask word, and the thing being haggled is a bill, so it wins the tie.
          bias=1),

    entry("ask-a-discount",
          (("discount", "discounts", "money off", "lower price", "cheaper price", "price down",
            "knock down", "knock the price", "haggle", "haggling", "haggling down",
            "bargain", "bargaining", "negotiate the price", "reduce the price", "sale price"),
           ("ask", "asked", "asking", "get", "how", "should i", "can i", "worth", "rude",
            "ok to", "acceptable", "market", "stall", "sofa", "kitchen", "phone")),
          "Ask the person who can say yes, not the till: \"is there anything you can do on the "
          "price?\" Have a number and somewhere cheaper to point at, and ask about ex-display or "
          "last season's colour. At a market or on a big ticket offer about 10 per cent under, "
          "ready to walk away; a shop that cannot move can often throw in delivery instead.",
          # A bill is not a price list, and a refund on something reduced is a different question.
          # A car is priced by the car-budget entry and haggled for below: both need a number in
          # the answer, which a shop's discount question does not.
          avoid=("car", "cars", "dealer", "dealers", "dealership", "forecourt", "garage",
                 "bill", "bill too", "energy", "gas", "electric", "council tax", "rent",
                 "fare", "fares", "train", "bus", "parking", "fine", "refund", "return",
                 "faulty", "wrong size", "money back", "ticket", "prescription", "tax",
                 "benefit", "pension", "council", "student discount", "nhs discount",
                 # "how do I know if a sale price is actually a bargain" asks whether the price is
                 # real, not whether it can be talked down, and the shopping table answers it with
                 # the price history. Asking here was telling a shopper to haggle at the till.
                 "actually a bargain", "real bargain", "genuine bargain", "good bargain",
                 "is it a bargain", "price history", "actually a good price",
                 "is the sale real", "a fake sale",
                 # A renewal, a tariff, a premium or a contract is a price on a bill, and it is
                 # moved on the phone rather than at a till: ring-about-a-price answers those,
                 # and "can i ask my insurer for a lower price" was getting "ask the person who
                 # can say yes, not the till" and a market stall.
                 "renewal", "renewals", "insurer", "insurers", "insurance", "premium",
                 "premiums", "tariff", "tariffs", "contract", "contracts",
                 "subscription", "subscriptions", "supplier", "providers"),
          # "money off" is in the key and it also reads as "money off my mum". The words that tell
          # a discount from a loan are the same for every row that reads a price, so the test is
          # `lookup.a_price_not_a_loan` and not a phrase list here.
          guard=a_price_not_a_loan),

    # "should i haggle on a car price" is not a shop discount: the money rule of thumb and the
    # haggling both belong in the answer, and neither entry had both.
    entry("haggle-a-car",
          (("haggle", "haggling", "bargain", "knock down", "knock the price", "negotiate",
            "negotiating", "money off", "cheaper", "lower price", "come down"),
           ("car", "cars", "dealer", "dealers", "dealership", "forecourt", "price", "prices")),
          "Talk to the salesperson, not whoever greets you, and go at the end of the month when "
          "the targets are close: get a rival dealer's price for the same car in writing and ask "
          "them to beat it. Keep the car itself to about a quarter of your yearly take-home, and "
          "settle that price before anyone mentions your part-exchange or a monthly payment.",
          # a car that will not start, insurance, finance and running costs are other questions
          avoid=("insurance", "lease", "leasing", "finance", "hp", "pcp", "sell", "sell my",
                 "part exchange", "running cost", "petrol", "diesel", "electric", "wont start",
                 "won't start", "battery", "mot", "tax", "repair", "warning light",
                 # and a bill is not a car. "how do i negotiate a lower price on my bill" was
                 # matching on "negotiate" plus "price" and getting a dealer's forecourt advice:
                 # the price word came from the bill, not from anything for sale.
                 "bill", "bills", "renewal", "premium", "premiums", "tariff", "energy",
                 "electricity", "gas", "broadband", "phone", "mobile", "rent", "mortgage",
                 "subscription", "subscriptions", "council tax", "water"),
          # "should i borrow money off my nan for a car" was this row's forecourt script: asking a
          # relative for the money is the borrowing rows' question, not the dealer's.
          guard=a_price_not_a_loan),

    # A coat bought in the sale is the policy question, not the haggle: a shop cannot refuse a
    # refund just because the item was reduced.
    entry("sale-refund",
          (("sale", "in the sale", "reduced", "clearance", "discount"),
           ("refund", "return", "returns", "returnable", "return it", "money back", "exchange",
            "faulty",
            # "i bought it in the sale can i take it back" and "can i take a sale item back"
            # name the ask as taking it back, not as returning it. The first group still has to
            # have a sale word, so a plain "can i take it back" is somebody else's line.
            "take it back", "take back", "take a sale item back", "bring it back", "item back")),
          "Sale items carry the same rights as full-price ones: faulty means a refund, repair or "
          "replacement, and a shop cannot refuse just because the item was reduced. If you simply "
          "changed your mind, the shop's own returns policy decides in store; anything bought "
          "online gives you 14 days to cancel from the day it arrives, sale or not.",
          avoid=("house", "flat", "car", "van", "bike", "stock", "shares", "because")),

    # "how long do i have to return something" is the window, not the policy on sale goods.
    entry("return-window",
          (("return", "returns", "returning", "send it back", "send back", "take it back",
            "take back", "money back", "change of mind", "changed my mind"),
           ("how long", "how many days", "how much time", "days", "window", "time limit",
            "limit", "deadline", "still", "can i", "am i able", "allowed", "when")),
          "Faulty goods: 30 days to return them for a full refund, then repair or replacement "
          "instead. Bought online or by post: 14 days from delivery to change your mind, and "
          "another 14 to send it back, you paying the postage unless it is faulty. In a shop, a "
          "change of mind is whatever their policy says, so check the receipt.",
          # The window is the question. "Can i get my money back" on something that broke after
          # a year is the consumer-rights answer, which the shopping domain owns.
          ask=("how long", "how many", "days", "weeks", "month", "window", "time limit",
               "deadline", "still", "limit"),
          avoid=("car", "house", "flat", "van", "bike", "holiday", "flight", "train", "stock",
                 "library", "hire", "rent", "borrow", "book", "ticket", "parcel", "library book",
                 "broke", "broken", "faulty after", "months", "years", "guarantee", "warranty")),

    # The window has a name, and people ask for the name: "what is a cooling off period" was a
    # shrug even once the returns row knew the shapes. This row is the same 14 days said as a
    # right, so it leads with the days rather than with faulty goods.
    entry("cooling-off",
          (("cooling off", "cooling-off", "cooling off period", "cooling-off period",
            "cooling off law", "distance selling", "right to cancel",
            # the same 14 days said as the mistake rather than the right: "i ordered the wrong
            # size, can i send it back" wants the window, not the shop's own policy
            "wrong size", "wrong colour", "wrong color", "doesnt fit", "doesn't fit",
            "regret buying", "bought online", "bought it online", "ordered online",
            "ordered it online"),
           ("what is", "whats", "what's", "what does", "how long", "how many", "days",
            "cover", "covers", "apply", "applies", "entitled", "rights", "right",
            "return", "send", "cancel", "order", "online", "bought", "buying", "shop")),
          "Fourteen days from the day it arrives on anything bought online, by phone or by post - "
          "no reason needed - and another 14 days to send it back, with the return postage at "
          "your cost unless the item is faulty. It does not cover personalised or perishable "
          "goods, sealed hygiene items once they are opened, or a service you asked them to start "
          "straight away, and in a shop there is no cooling-off right at all: only their own "
          "returns policy.",
          bias=1),

    # A cancelled order is its own question: nothing is faulty and nothing has been delivered,
    # so the return window and the sale-goods answer both miss it ("can i cancel an order i just
    # placed" was a shrug, "i want to cancel my order" an echo of the line back).
    entry("cancel-order",
          (("cancel", "cancelled", "canceled", "cancelling", "canceling", "stop the order",
            "change of mind", "changed my mind", "change my mind", "dont want it",
            "don't want it",
            "no longer want", "cooling off", "cooling-off"),
           ("order", "orders", "my order", "online order", "purchase", "purchased", "bought",
            "buy online", "online", "delivery", "deliver", "dispatched", "click and collect",
            "click collect", "parcel", "item", "items", "shop", "seller", "retailer",
            # "can i send it back if i change my mind" is a change of mind with no order word
            # in it, so the act of sending it back is the second part here.
            "send it back", "send back", "take it back", "return it", "returns")),
          _cancel_order_reply,
          avoid=("gym", "membership", "energy", "electricity", "gas", "broadband", "internet",
                 "supplier", "tariff", "insurance", "phone", "mobile", "sim", "contract",
                 "lease", "tenancy", "rent", "landlord", "subscription", "netflix", "spotify",
                 "tv licence", "direct debit", "standing order", "court order", "prescription",
                 "repeat prescription", "appointment", "doctor", "dentist", "hospital",
                 "flight", "flights", "hotel", "train", "ticket", "holiday", "booking",
                 "restaurant", "table", "takeaway", "take away", "pizza", "deliveroo", "uber eats",
                 "just eat", "taxi", "uber", "job", "interview", "shift", "plans", "wedding",
                 # a faulty item is the return window's question, not a cancellation
                 "faulty", "broken", "stopped working", "damaged", "not working", "wrong size",
                 "doesnt fit", "doesn't fit")),
    # --- getting out of a contract ------------------------------------------
    # "am i stuck in a contract" was answered by the out-of-a-rut entry ("change one thing you
    # do on autopilot") and "i signed up for a 12 month contract and want out" by "I'm
    # listening". The named ones - gym, phone, broadband, tenancy - keep their own rows below;
    # this is the contract that names no product, and the rules are the same for all of them.
    entry("stuck-in-a-contract",
          (("stuck in a contract", "stuck in my contract", "stuck with a contract",
            "tied into a contract", "tied in for", "tied to a contract",
            "get out of my contract", "get out of a contract", "break my contract",
            "break a contract", "leave my contract", "leave a contract",
            # "cant get out of" on its own reads every line about being shut in: "i cant get out
            # of the house" and "cant get out of bed" were answered with the exit fee, and the
            # first of those is a low-mood line. The phrase needs the thing being left.
            "cant get out of my contract", "cant get out of a contract",
            "cant get out of the contract", "cant get out of this contract",
            "can't get out of my contract", "can't get out of a contract",
            "can't get out of the contract", "can't get out of this contract",
            "want out of my contract", "want out of the contract",
            "exit fee", "early termination",
            "early exit fee", "signed a contract", "signed up for 12 months",
            "signed up for 18 months", "signed up for 24 months", "signed up for two years",
            "12 month contract", "18 month contract", "24 month contract", "two year contract",
            "minimum term"),
           ("contract", "contracts", "stuck", "month", "months", "year", "years", "leave",
            "cancel", "exit", "end", "out", "legal", "allowed", "can i", "how do i",
            "what can i do", "worth it", "fee", "fees", "penalty")),
          "Read the term and the exit fee first: a minimum term normally lets you leave early "
          "for a set fee, often a share of what is left, and anything signed online or over the "
          "phone has a 14-day cooling-off period. Then ask in writing whether it can be "
          "transferred, downgraded or paused instead of cancelled, and if they refuse, the free "
          "ombudsman for that industry will look at it after eight weeks.",
          # The gym, the phone, the broadband and the tenancy each have their own row with the
          # numbers in it, and a car or a lease is finance, not a membership.
          avoid=("gym", "gyms", "membership", "phone", "mobile", "broadband", "internet",
                 "energy", "gas", "electricity", "supplier", "tenancy", "tenancies", "lease",
                 "landlord", "rent", "insurance", "car", "cars", "finance", "mortgage",
                 "loan", "mobile phone", "sim")),
    # "how do i quit the gym" is the membership, not a job: the work domain answers a job quit
    # with "tell your manager first", which is why the gym words are in the first key group here.
    # "how do i cancel my broadband" was a shrug and "i want to cancel my energy contract" got the
    # gym's notice period, because "contract" plus "cancel" is how every account is worded. The
    # answer is shared because the rules are: the minimum term first, then who does the switching.
    entry("cancel-utility",
          # A bare "account" is not a utility: it took "how do i close my amazon account",
          # "how do i close a credit card account" and "how do i close my gym account" and told
          # them to photograph the meter. The utility says its own name; a closing line still
          # reaches this row through it ("how do i close my energy account").
          (("energy", "gas", "electricity", "electric", "broadband", "internet", "water",
            "supplier", "suppliers", "utility", "utilities"),
           ("cancel", "cancelling", "cancellation", "get out of", "end my", "ending", "leave",
            "terminate", "notice", "switch away", "close")),
          "Read the minimum term and the exit fee before you do anything, because an early exit can "
          "cost most of what is left on the contract. Ring or write to cancel, ask for the final "
          "bill and give a meter reading on the day - a photograph of the meter is enough - and "
          "keep the date and the name of whoever you spoke to. Do not cancel an energy account "
          "before the switch: sign up with the new supplier and it takes over on a set date. For "
          "broadband, send the router back if it was theirs, or they bill you for it. Then check "
          "the next two statements, because an account that keeps billing after it was cancelled "
          "is the commonest complaint there is.",
          # "my water is hard and leaves marks" was a contract: "leaves" is the row's own key
          # word, so the hardness words hold it off and the water rows answer it.
          avoid=("hard water", "hard", "hardness", "chalky", "limescale", "scale", "scaled",
                 "soft water", "softener", "kettle", "shower head", "marks", "stains",
                 "taps", "tap", "leaves marks", "safe to drink", "bad for you",
                 "gym", "gyms", "membership", "memberships", "leisure centre", "health club",
                 "job", "my job", "staff", "interview", "rent", "tenancy", "landlord",
                 # a bank account has no meter and no supplier: "how do i close my bank account"
                 # was being told to photograph the meter on the day the contract ends
                 "bank", "building society", "savings", "current account", "isa", "overdraft",
                 "phone", "mobile", "sim", "netflix", "tv licence", "union", "insurance",
                 # a website or an app account has no meter, no minimum term and no supplier to
                 # ring: "how do i close my facebook account" was told to photograph the meter
                 # before the contract ended. The technology rows answer those, so a named
                 # platform stands this one down.
                 # an account held by somebody who has died is settled with the death
                 # certificate, and the register-death row answers that errand: the exit fee and
                 # the meter reading here are nonsense for it.
                 "died", "death", "deceased", "bereaved", "widow", "widower", "funeral",
                 "how much is", "should i cancel", "worth it", "good idea")
                + APP_ACCOUNT_WORDS),

    # A contract that has run out is the moment to move, and the answers did not have it for
    # anything but a phone: "my broadband contract has ended" reached `cancel-utility` and was
    # told how to cancel an account, and "i am out of contract with my broadband" reached nothing
    # at all. `cheap-phone-deal` already answers the phone lines, so this one leaves the phone and
    # the mobile alone and takes the ones nothing else covers.
    entry("out-of-contract",
          (("out of contract", "contract is up", "contract is ending", "contract has ended",
            "contract ended", "contract runs out", "contract expires", "contract is over",
            "contract finished", "end of my contract", "minimum term is up", "term is up",
            "term has ended", "fixed term has ended", "fixed term is up", "deal has ended",
            "deal is ending", "no longer in contract", "not in a contract", "rolling contract",
            "rolling monthly", "contract ends", "contract is done", "contract is finished",
            "contract has run out", "contract done"),
           # the service is what has to be named, and "tv" is left out on purpose: a key word is
           # split on its spaces, so "tv contract" would still make "tv" a second lifeadmin key
           # word, and the rarity point `tv-licence` earns on "tv" is what beats `screen-time`'s
           # "how much" - "how much is a tv licence" came back as the screen-time answer. The
           # same goes for "renewal", which `tv-licence` also keys.
           ("broadband", "internet", "fibre", "wifi", "router", "energy", "gas", "electricity",
            "electric")),
          "Do nothing and you roll onto the standard price, the dearest one, so ring your supplier "
          "this week: get one rival's price first, then ask for retentions and say you are out of "
          "contract and have a cheaper quote - they usually keep you below the standard price. If "
          "they will not move, switch, giving the notice your contract asks for, usually 30 days, "
          "and getting the end date in writing: a switch that starts early can carry a fee.",
          # a workplace contract, a tenancy and a gym are each their own question, and a contract
          # that has *ended* is not one being cancelled or renewed at a price
          avoid=("job", "my job", "work", "employer", "zero hours", "hours", "shift", "shifts",
                 "sacked", "redundant", "redundancy", "notice period", "holiday",
                 "tenancy", "tenants", "landlord", "rent", "lease", "mortgage", "house",
                 "buying a house", "gym", "gyms", "membership", "phone", "mobile", "iphone",
                 "handset", "sim only", "sim-only",
                 # an insurance renewal has its own card, and it is about the price of cover
                 "insurance", "insurer", "premium", "premiums", "car", "cars",
                 # a line about a fee they are being asked for is the early-exit card's: the term
                 # may not really be over, and "do nothing and you roll onto the standard price" is
                 # the wrong moment for it ("my broadband contract ended and they want me to pay")
                 "want me to pay", "wants me to pay", "asking me to pay", "charging me",
                 "charged me", "owe", "owes", "exit fee", "termination fee", "penalty",
                 # when the line leads with the price going up, the price-rise card is the better
                 # answer: it names the PAC code, the 20 to 30 per cent retention price and the
                 # social tariff, and it already says a contract that has run out is free to leave
                 "price went up", "went up", "gone up", "goes up", "going up", "increase",
                 "increased", "rise", "rises", "rising", "more expensive", "put up"),
          # `cancel-utility` is an entry earlier in this file and a line with "has ended" scores
          # the same on both, so the tie goes to the card about a contract that has run out
          bias=1),

    entry("cancel-gym",
          (("gym", "gyms", "leisure centre", "health club", "membership", "memberships",
            "contract", "contracts"),
           # "how do i close my gym membership" was a hedge: the row asked for "cancel" and the
           # person said "close". The gate is the gym word, so the verb can be any of them.
           ("cancel", "cancelling", "cancellation", "get out of", "quit", "leave", "stop paying",
            "pause", "freeze", "end it", "notice", "close", "closing", "end", "ending", "stop",
            # "stop paying for a gym i dont use" names no cancel word at all, and the money
            # domain's three rungs for a big purchase answered it
            "dont use", "don't use", "do not use", "never use", "not using", "never go",
            "dont go", "don't go", "stopped going", "wasting", "stop the payments",
            "stop paying them", "getting out")),
          "Cancel in writing and keep the date you sent it: most gyms and clubs want a month's "
          "notice, and the contract you signed says how much and whether there is a fee. Email the "
          "branch or use their cancellation form rather than telling the desk, then check the next "
          "two statements; if they keep charging past your notice date, ask your bank to reverse "
          "the direct debit and show them the email.",
          # "membership" and "contract" alone also fit a phone, a club or a union, so the
          # place has to be named; "how do i cancel my phone contract" was getting this answer.
          # A blocklist of the other places is the wrong way round - it misses the network nobody
          # thought to list - so the gate is the other way: a gym word has to be in the line.
          ask=("gym", "gyms", "leisure centre", "health club", "membership", "memberships",
               "personal trainer", "squash club", "golf club", "swim club", "dance class",
               "fitness class", "climbing wall"),
          avoid=("job", "my job", "work there", "staff", "manager", "interview", "apply",
                 # an employment contract is not a membership: "my contract says i have to give
                 # 3 months notice" was getting the gym cancellation
                 "employer", "employment", "employee", "resign", "resignation",
                 "notice period", "salary", "colleague",
                 "how much is", "joining fee", "should i join", "worth joining",
                 # "and i want to cancel my gym membership, is that a good idea" is asking for
                 # advice, not the steps
                 "good idea", "worth it", "a good idea", "should i cancel",
                 "join", "joining", "joined", "sign up", "signing up", "trial",
                 "phone", "mobile", "sim", "broadband", "internet", "tv", "netflix", "union",
                 # a network's name is a phone contract even when the line says only "o2":
                 # "how do i get out of my contract with o2" was getting the gym's notice period
                 "o2", "vodafone", "giffgaff", "voxi", "tesco mobile", "sky mobile",
                 "airtime", "pac code", "pac",
                 # "cancel my energy contract" matched on "contract" and got the gym's notice
                 # period; an energy, water or broadband account has its own entry below
                 "energy", "gas", "electricity", "electric", "water", "supplier", "tariff",
                 "insurance", "council tax", "subscription",
                 "car insurance", "insurance", "magazine", "gym class", "personal trainer")),
    entry("post-times",
          (("post", "post office", "letter", "parcel", "package", "first class", "second class",
            "signed for", "special delivery"),
           # "arrive" is in the key because "when will my parcel arrive" is this entry's own
           # question; the word is in a missing parcel too, and what separates them is that
           # the timetable line asks for a time, which the ask below requires. It is done with
           # ask rather than with an avoid phrase because inside this domain alone "didnt" is
           # repaired to a lifeadmin word, which breaks every avoid phrase that spells it.
           ("how long", "how many days", "take", "takes", "delivery", "days", "wait",
            "in the post", "posted", "arrive", "arrives", "arriving", "delivered",
            "deliver", "get here", "get there")),
          "In the UK, second class is 2 to 3 working days and first class is the next working "
          "day; a courier parcel is usually next day, and nothing is guaranteed unless you pay "
          "for tracked 24 or special delivery. Post before the last collection time on the board "
          "outside the post office, because a late drop counts as the next day.",
          # A parcel that has gone missing or not turned up needs the seller, not the timetable.
          # The times here are UK inland ones, so post going abroad is a different question.
          avoid=("lost", "missing", "where is", "hasn't arrived", "hasnt arrived", "not arrived",
                 "tracking", "damaged", "refund",
                 # "my parcel never arrived" is the same missing-parcel question as "hasnt
                 # arrived", and the tense alone was letting it reach the timetable
                 "never", "didn't arrive", "didnt arrive", "has not arrived", "no sign",
                 "still waiting", "late", "delayed", "held up",
                 # A label or a printer is how you send it, not when it arrives
                 "label", "labels", "printer", "print", "qr code", "without the label",
                 # "how long should a cover letter be" is a question about a page count, and
                 # the timetable read it as post going in an envelope
                 "cover letter", "covering letter", "covering email", "letter of application",
                 "application letter", "cv", "curriculum vitae", "personal statement",
                 # Junk mail is volume, not a delivery time: "i get so much spam in the post
                 # these days" is not a question about second class.
                 "spam", "junk", "junk mail", "flyers", "leaflets", "leaflet", "mailshot",
                 "abroad", "australia", "america", "canada",
                 "spain", "france", "germany", "italy", "india", "china", "japan", "overseas",
                 "international", "customs"),
          # "delivered" is not in this ask on purpose: "my parcel says delivered but there is
          # nothing here" is a missing parcel, not a question about the timetable.
          ask=("when", "how long", "how many days", "how many working days", "how soon",
               "how many", "days", "working days", "take", "takes", "wait", "delivery",
               "first class", "second class")),
    # A parcel you sent that never arrived is the opposite of one you are waiting for: there is no
    # shop to chase and no chargeback, and the person is the sender. Main answered it with the
    # recipient's card - "until a parcel reaches you it's the retailer's responsibility" - which
    # is the wrong side of the counter, and "i posted a birthday card and it never arrived" was
    # sent to the birthday-card answer.
    # A sender asking about the tracking was getting the packing card, and once the buyer's rows
    # stood down for the sender's own words it was getting a shrug. The number on the receipt is
    # the same number a claim rests on, so the two questions are one row apart.
    entry("track-a-parcel-i-sent",
          (("tracking", "tracked", "track", "track it", "track and trace", "track my parcel",
            "tracking number", "tracking page"),
           ("i sent", "we sent", "i posted", "we posted", "i shipped", "my buyer", "i sold",
            "parcel i sent", "parcel i posted", "the one i sent", "label", "receipt")),
          "Look it up on the carrier's own site with the number on the counter receipt or the "
          "emailed label - not the shop's app, which only shows what the carrier told it. The "
          "number is also what a claim rests on, so keep it. If the page has not moved at all for "
          "10 working days, Royal Mail treats the item as lost and the claim starts then.",
          ask=("how", "can i", "where", "what", "should i", "do i", "track", "tracking",
               "not updated", "hasnt updated", "hasn't updated", "checked", "check"),
          # a buyer who denies receiving it while the scan says delivered is a dispute, not a
          # tracking question: the answer is the delivery scan, the proof of posting and the
          # marketplace's own dispute process, and this row cannot say that.
          avoid=("never arrived", "hasnt arrived", "hasn't arrived", "says delivered",
                 "claims it", "claims never", "wants a refund", "dispute", "chargeback")),

    entry("parcel-i-sent-went-missing",
          (("i sent", "i posted", "we sent", "we posted", "i have sent", "i've sent",
            "sent a parcel", "posted a parcel", "sent a package", "posted a package",
            "sent it", "posted it", "sent a card", "posted a card", "sent a letter",
            "posted a letter", "sent a present", "posted a present", "sent a gift",
            "sent back", "sent off",
            # selling one is still sending one, and the buyer is the one waiting: "my ebay buyer
            # says the parcel never arrived" was answered from the buyer's side, telling the
            # seller to contact the seller.
            "i sold", "sold it on", "sold something", "my buyer", "buyer says", "buyer is",
            "the buyer", "on ebay", "on vinted", "on depop", "marketplace",
            # a claim is made against the carrier by name
            "royal mail", "parcel force", "parcelforce",
            # a bare "post office" is a place, not a claim: "can i do it at the post office"
            # after a name change was answered with the proof of posting and the claim form.
            "post office said", "post office says", "post office told me",
            "at the post office it", "post office claim"),
           ("lost", "missing", "never arrived", "never came", "not arrived", "didnt arrive",
            "didn't arrive", "never got there", "never turned up", "didnt turn up",
            # people write the contraction with no apostrophe, and "i posted a parcel and it
            # hasnt arrived" was falling through to the buyer's card without these.
            "hasnt arrived", "hasn't arrived", "has not arrived", "still not arrived",
            "hasnt come", "hasn't come", "has not come", "still hasnt", "still hasn't",
            "hasnt turned up", "hasn't turned up", "not turned up", "never showed up",
            "didnt come", "didn't come",
            "didn't turn up", "gone missing", "no sign", "nothing came", "not come",
            "compensation", "claim", "claiming", "refund", "damaged", "broken", "stolen",
            # a parcel coming back to the person who sent it is not a claim: the returns and
            # the address cards answer it, and "a parcel i sent came back" was given the claim
            # form. Those words are in the avoid list below instead.
            "lost in the post", "post office",
            "royal mail", "courier", "evri", "hermes", "dpd", "yodel", "ups",
            # a bare "parcel" is not a fault: with `posted a parcel` loose in the first half it
            # took "how do i post a parcel" and "how should i post it" - the parcel was still in
            # the person's hands - and answered them with the claim form. Every line that belongs
            # here says what went wrong, and those words are above.
            )),
          _claim_reply,
          ask=("how", "what", "can i", "should i", "do i", "claim", "compensation", "lost",
               "missing", "never", "didnt", "didn't",
               # the gate is what hid the contractions: "i posted a parcel and it hasnt
               # arrived" had both key words and no ask word, so it fell to the buyer's card.
               "arrived", "come", "came", "turned", "showed", "hasnt", "hasn't", "has not",
               "havent", "haven't", "still", "not"),
          bias=2,
          # the parcel you are waiting for is the shop's, and a present you are choosing, a card
          # you are writing and a letter you are drafting are other answers. So are a delivery
          # timetable, a returns label and the price of postage.
          # "arrived yet" was here and it was the wrong way round: the buyer's lines ("my parcel
          # hasnt arrived yet") never reach this row because the first half wants the sender's
          # own words, while "i sent a parcel and it has not arrived yet" is the sender and was
          # pushed back to the buyer's card by it.
          avoid=("still waiting", "waiting for", "waiting on", "order",
                 "ordered", "retailer", "seller", "shop", "bought", "delivery", "delivered to me",
                 "what do i write", "what should i write", "write in", "message for",
                 "present for", "gift for", "card for", "letter to", "how long", "how much",
                 # "royal mail lost my parcel" says nothing about who posted it, and the person
                 # waiting has the buyer's answer: tell the seller. Only the sender's own words
                 # ("i sent", "i posted") hold this row.
                 "lost my parcel", "lost my order", "lost my package", "my parcel got lost",
                 # the buyer's line: a carrier telling you it delivered is the seller's problem,
                 # and "the post office said it was delivered but nothing came" is not a claim.
                 "said it was delivered", "says it was delivered", "said delivered",
                 "says delivered", "marked as delivered", "says it has been delivered",
                 "cost", "price", "label", "return a parcel", "return the parcel",
                 "returning", "send a parcel", "pack", "weigh", "wrap",
                 # nothing has gone missing on these: "can i post a parcel on a sunday" is
                 # whether the counter is open, and "how do i complain to royal mail" is the
                 # complaint letter while "how do i write a complaint letter to royal mail"
                 # keeps its own card.
                 "sunday", "saturdays", "saturday", "bank holiday", "post office open",
                 "open on", "closes", "closed", "complain", "complaint", "complaining",
                 # posting something abroad is customs, not a missing item
                 "abroad", "overseas", "international", "customs", "america", "spain",
                 "france", "europe", "australia", "canada", "usa",
                 # it came back: why is on the label, and the returns and address cards answer
                 # that. A claim is for something that did not arrive at all.
                 "came back", "come back", "sent back", "returned", "returned to sender",
                 "being returned", "return to sender", "came back to me"),
          # an email, a text or a message is not posted, and "i sent an email and it never
          # arrived" was answered with proof of posting and a claim form.
          guard=_a_posted_thing),
    # What it costs to post is the question people ask before they pack it, and it was answered
    # with how to weigh and pack one: "how much does it cost to post a parcel" reached the
    # how-to-send card and then, once that stood down, nothing at all.
    entry("postage-cost",
          (("how much does it cost", "how much is it to", "how much to post", "cost to post",
            "cost of postage", "postage cost", "price of postage", "postage price",
            "cheapest way to post", "cheapest way to send", "how much postage",
            "much does it cost to post", "much does it cost to send"),
           ("post", "posting", "postage", "parcel", "parcels", "package", "letter", "letters",
            "send", "sending", "royal mail", "courier", "post office", "first class",
            "second class", "large letter", "signed for", "special delivery")),
          ("It goes on weight and size, not distance: Royal Mail prices a letter and a large "
           "letter off the thickness, and a parcel off its weight and whether it fits a small, "
           "medium or large box. A small parcel by second class is a few pounds, first class a "
           "pound or two more, Signed For a couple more again, and anything over 2 kg is usually "
           "cheaper with a courier - put the weight and size into the Royal Mail price finder or "
           "ask at the counter, and take a photo of the scales. Prices change every April."),
          ask=("how much", "cost", "costs", "price", "cheapest", "much does it", "what does"),
          bias=2,
          # going abroad, a return, and a parcel that never arrived are their own answers
          avoid=("abroad", "overseas", "international", "customs", "america", "spain", "france",
                 "europe", "return", "returns", "refund", "lost", "missing", "never",
                 "damaged", "track", "how long", "days", "weigh it", "pack it",
                 # money is not posted: "whats the cheapest way to send money to poland" holds
                 # the phrase "cheapest way to send" and was answered with Royal Mail's prices.
                 # The transfer is `travel.send-money-abroad`.
                 "money", "cash", "euros", "dollars", "funds", "transfer", "transfers",
                 "bank transfer", "currency", "paypal", "wise", "western union")),
    # Sending one is not the timetable and not the returns window: "how do i send a parcel" was
    # a shrug, and "can i take a parcel back to the post office without the label" was answered
    # with the fever rules. The useful facts are the scale, the label you do not need to print,
    # and the proof of postage.
    entry("send-parcel",
          (("parcel", "parcels", "package", "packages", "returns label", "return label",
            "postage"),
           ("send", "sending", "sent", "post", "posting", "post office", "return", "returning",
            "send it back", "send back", "label", "print", "printer", "qr", "weigh", "weight",
            "scales", "tracked", "track", "drop off", "parcel shop", "courier", "pack", "wrap",
            "address")),
          "Weigh it on kitchen scales, pack it so it cannot move, and write the address on the "
          "parcel itself as well as the label. You do not need a printer: most retailers email a "
          "QR code you show at a post office counter or a parcel shop, and the shop prints the "
          "label there. Keep the proof of postage until the money is back, because a return that "
          "goes missing is the sender's word against the shop's without it.",
          ask=("parcel", "parcels", "package", "packages", "returns label", "return label",
               "postage label", "label for a return"),
          # how long post takes is the timetable entry, a parcel that never arrived is the
          # seller's, and anything going abroad has customs in it. A parcel going back is the
          # seller's too: "how do i return a parcel to the post office" was told how to send one.
          avoid=("how long", "arrive", "arrives", "arrived", "days", "late", "delayed",
                 "lost", "missing", "never", "not arrived", "tracking number", "refund",
                 # the price of postage, the tracking of a parcel already sent, and a parcel
                 # left somewhere are each a different question: "how much does it cost to post
                 # a parcel" was told how to weigh and pack one, and "the courier left my parcel
                 # somewhere i cant find" the same.
                 "how much", "cost", "costs", "price", "cheapest", "expensive", "much does it",
                 "left my parcel", "left it", "left the parcel", "somewhere", "cant find",
                 "can't find", "wrong address", "wrong house", "neighbours", "neighbour",
                 "track a parcel", "track my parcel", "track the parcel", "where is my parcel",
                 "track my", "where is my", "where is the",
                 "return a parcel", "return the parcel", "return it", "returning a parcel",
                 "returning the parcel", "returns a parcel", "send it back to", "send a parcel back",
                 "damaged", "abroad", "overseas", "international", "customs", "america",
                 "australia", "spain", "france", "germany", "delivery driver", "courier van")),
    entry("switch-bank-account",
          (("bank account", "current account", "bank"),
           ("switch", "switching", "switched", "move", "moving", "change", "changing")),
          "Use the free current account switch service: pick the new bank, and it moves your "
          "direct debits, standing orders and salary, closes the old account and forwards stray "
          "payments for three years - seven working days, and the switch guarantee covers any "
          "charges if something goes wrong. Compare the new account's overdraft and monthly fee "
          "first, because a free account that charges for an overdraft costs more than one with a "
          "fee and none.",
          # A phone, an energy supplier and a broadband deal all get switched, and this answer
          # would tell someone to move their direct debits to a bank.
          avoid=("phone", "mobile", "sim", "broadband", "internet", "energy", "supplier",
                 "electricity", "gas", "tv", "netflix", "insurance", "job", "career", "school",
                 "doctor", "dentist", "side", "sides", "shelf",
                 # a bank that rings you about your money is the scam call, not the switch
                 "rang", "rang me", "called me", "safe account", "pin", "read out",
                 "fraud", "scam", "asked me to move")),
    entry("open-bank-account",
          (("bank account", "current account", "savings account", "open an account", "bank"),
           ("open", "opening", "need", "documents", "id", "proof", "switch", "switching",
            "online", "student")),
          "Take photo ID and proof of address dated within the last three months - a bank "
          "statement, utility bill or council letter - and you can usually open one online in ten "
          "minutes with a selfie and a photo of the ID. To move an existing account, use the free "
          "current account switch service: it moves your direct debits, standing orders and salary "
          "within seven working days and forwards stray payments for three years.",
          # A business account wants different documents (a certificate of incorporation or a
          # UTR), so the personal list is not the answer to that one.
          # "should i open an isa or a savings account" is a choice between two products, which
          # the ISA and savings entries answer; this entry is only the paperwork for opening one
          avoid=("close", "closing", "overdrawn", "fraud", "scam", "loan", "mortgage", "joint",
                 "isa", "isas", "lifetime isa", "business", "company", "sole trader",
                 "self employed", "self-employed",
                 "limited company", "ltd", "partnership",
                 # Keeping a card safe is money.py's card-safe-online, not the documents list:
                 # "how do i keep my bank card safe online" carries "bank" and "online" and was
                 # answered with photo ID.
                 "bank card", "my bank card", "card safe", "keep my card", "my card safe",
                 "card details", "card being used", "used online",
                 # a child's account is opened by the parent with the child's details, and a
                 # student account wants a UCAS letter, so the plain list is not those answers
                 "child", "children", "my son", "my daughter", "kids", "teenager", "under 18",
                 "junior", "student",
                 # a bank holiday is not a bank: "is the tip open on bank holiday monday" was
                 # answered with photo ID and proof of address, on "bank" and "open" alone. The
                 # hours phrases stand it down for the rest ("whats open on bank holiday monday").
                 "bank holiday", "bank holidays") + A_HOURS_ASK),

    # --- the small obligations with a form behind them ----------------------
    entry("tv-licence",
          (("tv licence", "tv license", "television licence", "television license", "tv licences",
            "licence fee", "license fee"),
           ("cancel", "cancelling", "stop paying", "refund", "no tv", "don't watch", "dont watch",
            "never watch", "moved out", "do i need", "need one", "still need",
            # the licence that is not paid, is overdue, or has run out
            "paid", "pay", "paying", "owe", "overdue", "late", "letters", "fine", "ran out",
            "expired", "how much", "cost", "price", "buy",
            # renewal is the ask people make of a licence that has run out
            "renew", "renewing", "renewal", "renewed", "runs out", "expires")),
          "About £175 a year, in one go or by direct debit, and you need it for live TV on any "
          "channel or for BBC iPlayer, not for streaming like Netflix. It is free at 75 with "
          "Pension Credit, half price if you are blind. If it has run out, renew in the TV "
          "Licensing account before the letters start; if you no longer need it, cancel there and "
          "ask for a refund of unused months.",
          # A driving licence, a DBS check and a dog licence are other paperwork entirely.
          avoid=("driving", "driver", "car", "van", "lorry", "motorbike", "mot", "dbs", "dog",
                 "alcohol", "premises", "fishing", "road tax"),
          ask=("cancel", "refund", "stop paying", "do i need", "do i have to", "have to have",
               "need one", "need a", "still need", "how much is", "cost",
               "paid", "pay", "owe", "overdue", "late", "letters", "fine", "ran out",
               "expired", "price", "buy",
               # "i need to renew my tv licence" is the same ask of a licence that has run out
               "renew", "renewing", "renewal", "renewed", "runs out", "expires")),
    # "what age do you have to be to vote" was answered with the biology of ageing, because the
    # word "age" is in the key of that row and nowhere else. It is the plainest register question
    # there is, so it gets its own card, and the number in it leads.
    entry("voting-age",
          (("vote", "votes", "voting", "vote at 16", "vote at 17", "vote at 18",
            "register to vote", "election"),
           ("age", "how old", "old enough", "old do you have", "how old do i have",
            "old to vote", "16", "17", "18", "years old", "year olds")),
          # The first sentence has to carry both numbers and the word "vote": asked again as
          # "and can i vote at 16" the same card is narrowed to the sentence the line shares
          # words with, and the register sentence - "closes 12 working days before a vote" - was
          # the only one with "vote" in it, so the second turn was that fragment on its own.
          "Eighteen to vote in a general election in England, Wales and Northern Ireland, and 16 "
          "in Scotland and Wales for the Scottish Parliament and the Senedd. You have to be on "
          "the electoral register as well, which is a separate step from turning 18, so register "
          "as soon as you can - it takes about five minutes online and closes 12 working days "
          "before a vote.",
          avoid=("who should i vote", "who do i vote", "should i vote", "who to vote",
                 "brexit", "tory", "labour", "green party", "lib dem",
                 # the history of the vote is the history rows' question, not this one
                 "when did", "suffragette", "suffragettes", "suffrage", "1918", "1928",
                 "women get", "women got", "women win"),
          # the register card shares the word "vote" and says how to get on the roll; a line that
          # names an age is this card's, and the number is the first thing it says
          bias=2),
    entry("register-to-vote",
          (("register to vote", "voting register", "electoral register", "electoral roll",
            "how do i vote", "can i vote", "register for voting"),
           ("register", "sign up", "how", "where", "deadline", "missing", "not on", "moved",
            "change my address", "can i", "am i")),
          "Register online at the government's register to vote service: it takes about five "
          "minutes and needs your date of birth, address and National Insurance number. Do it "
          "again after every move - the register does not follow you - and the deadline is 12 "
          "working days before an election. The same page has a check for whether you are on it, "
          "and being on it also helps your credit score.",
          # Who to vote for is an opinion, and a result already in is a different question.
          avoid=("who should i vote", "who do i vote", "should i vote", "who to vote", "brexit",
                 "tory", "labour", "green party", "lib dem", "my mp", "election result", "poll")),
    # "what do i need to rent a flat" was the search hedge: the tenancy rows cover ending one, the
    # deposit and a copy of the agreement, and nothing covered the start of one.
    entry("rent-a-flat",
          (("rent a flat", "renting a flat", "rent a house", "renting a house", "rent a place",
            "renting a place", "flat to rent", "house to rent", "flats to rent",
            "rent somewhere", "renting for the first time", "first flat", "find a flat",
            "looking for a flat", "looking for a house to rent", "move out of my parents",
            "move out", "what do i need to rent", "need to rent"),
           ("need", "needs", "what do i need", "what do you need", "how do i", "how much",
            "deposit", "afford", "start", "first time", "checklist", "documents",
            "what to do", "where do i start", "guarantor", "references", "fees")),
          "Budget for the deposit (five weeks' rent, and it has to be held in a protection scheme), "
          "the first month up front and the bills, then have ready: photo ID and proof of address, "
          "three months of payslips or a guarantor, and a reference from a previous landlord. In "
          "England most letting agent fees are banned, so you should only pay rent, the deposit "
          "and a holding deposit. Read the tenancy agreement before you sign it.",
          # a deposit coming back, a repair, a rent rise and ending a tenancy are the other rows
          avoid=("deposit back", "my deposit", "get my deposit", "withheld", "notice", "evict",
                 "eviction", "repair", "broken", "damp", "mould", "rent rise", "increase",
                 "arrears", "landlord wants", "landlord is", "landlord has", "end my tenancy",
                 "leave early", "break clause", "mortgage", "buy a house", "buying a house",
                 "council house", "housing benefit", "universal credit",
                 # telling a landlord you are going is the notice letter: "i want to move out
                 # how do i tell my landlord" was answered with the deposit and payslip list
                 "tell my landlord", "tell the landlord", "how do i tell", "how to tell")),
    # A tenant's reference is the same noun as a job reference and was answered with a hedge:
    # "will my landlord give me a reference for a flat" got "Citizens Advice answers tenant
    # questions free". The asker, what is asked and what to do when the landlord says no are
    # what the person actually wants.
    entry("landlord-reference",
          (("landlord", "landlady", "letting agent", "letting agency", "my agent"),
           ("reference", "references", "referee", "letter from", "written")),
          "Ask in writing and make it easy: a short message naming the address, the dates you "
          "rented and asking whether they will confirm that rent was paid on time. Landlords "
          "usually just verify dates, rent and that the property was left in good order, so "
          "you can offer your bank statements or a rent statement alongside it. If they say no "
          "or go quiet, an employer or a previous letting agent will do, and a guarantor "
          "covers the gap.",
          avoid=("mortgage", "buying a house", "house price", "job", "employer", "cv",
                 "interview", "sacked", "reference letter", "character reference"),
          bias=2),

    entry("tenancy-copy",
          (("tenancy agreement", "copy of my tenancy", "copy of the tenancy",
            "tenancy contract", "renting agreement", "assured shorthold"),
           ("copy", "get", "landlord", "never gave", "hasn't given", "hasnt given", "lost",
            "where", "asked for", "won't give", "wont give", "never got", "didn't get",
            "didnt get", "not had", "never had", "no copy",
            # "what is a tenancy agreement" was the break-clause card, because the break clause
            # row holds "tenancy" too: the person asking what the thing is names no landlord
            "what", "whats", "what's", "is a", "is it", "explain", "mean", "means")),
          _tenancy_copy, bias=1,
          # The deposit coming back, notice to leave, and a rent rise are their own questions.
          avoid=("deposit back", "my deposit", "get my deposit", "withheld", "notice", "evict",
                 "section 21", "rent increase", "raise the rent", "end the tenancy", "break the",
                 "sign", "signing", "check before", "should i sign")),
    # "do i need a gas safety certificate" was a search hedge. The duty is the landlord's and it
    # runs on a clock, so the row says who owes it, how often, and what the tenant should have
    # been handed - and it stands down for the boiler service that a homeowner buys instead.
    entry("gas-safety-certificate",
          (("gas safety certificate", "gas safety check", "gas certificate", "gas safety record",
            "cp12", "landlord gas certificate", "gas safety inspection",
            # the same paper by what it is for: a renter asking what the landlord owes them
            "landlord gas safety", "gas check"),
           ("need", "needs", "needed", "do i", "does my landlord", "landlord", "have to",
            "must", "required", "require", "law", "legal", "how often", "every year",
            "annual", "when", "who pays", "who is responsible", "responsible", "tenant",
            "renting", "rented", "rent property", "what is", "whats", "what's", "explain",
            # the do-it-myself ask, which is the same duty seen from the other side
            "myself", "yourself", "ourselves")),
          "In a rented home the landlord must have the gas appliances and flues checked every 12 "
          "months by a Gas Safe registered engineer and give you a copy of the record within 28 "
          "days of the check - it is their duty and their cost, and a copy should be there when "
          "you move in. You cannot do the check yourself - only a Gas Safe registered engineer can "
          "sign the record - and a home you own needs no certificate by law, so a yearly boiler "
          "service is the thing to book instead.",
          # a price, a repair and a carbon monoxide alarm are their own questions, and the boiler
          # service is what somebody in their own home actually buys
          avoid=("alarm", "detector", "monoxide", "price", "cost", "how much", "boiler service",
                 "service my boiler", "service the boiler", "my boiler", "my cooker", "my hob",
                 "broken", "fault", "smell", "leak", "buy a house", "selling my house",
                 "sell my house", "landlord won't", "landlord wont", "refusing")),
    # A bus lane, clean air zone or congestion notice is a council penalty too, but the daily
    # charge questions ("do i have to pay the congestion charge?") are not this answer.
    entry("bus-lane-fine",
          (("bus lane", "bus gate", "bus lane fine", "bus lane ticket", "clean air zone",
            "ulez", "low emission zone", "congestion charge fine", "congestion zone fine"),
           ("appeal", "appealing", "contest", "challenge", "wrong", "unfair", "got one",
            "got a", "fine", "ticket", "pcn", "pay", "should i pay", "dispute")),
          "The council has to show photographs with the time, the place and the signs, so ask for "
          "the evidence and check whether the sign or the markings were clear. You have 28 days to "
          "appeal and usually 14 to pay at the reduced rate, and appealing inside that window "
          "keeps the discount. If they refuse, the free independent adjudicator is worth using: "
          "the Traffic Penalty Tribunal outside London, London Tribunals inside it.",
          # The charge itself is a price question, not an appeal.
          avoid=("do i have to pay", "how much is", "how much does", "is my car", "can i drive",
                 "what is the charge", "zone charge", "daily charge", "sign up", "register my car",
                 "discount for", "exempt")),
    # A speeding notice is a letter with a deadline that people try to ignore, and the deadline
    # is where it turns from three points into six. "how do i appeal a speeding fine" was a search
    # on main, and the parking and bus-lane rows stand down on the word on purpose.
    entry("speeding-notice",
          (("speeding", "speeding fine", "speeding ticket", "speeding letter", "caught speeding",
            "speed camera", "speed van", "speed trap", "notice of intended prosecution",
            "fixed penalty", "speed awareness", "speed awareness course", "section 172"),
           ("appeal", "appealing", "contest", "challenge", "dispute", "fight", "wrong", "unfair",
            "should i pay", "do i pay", "have to pay", "what do i do", "what should i do",
            "got one", "got a letter", "got caught", "just got", "received", "how much",
            "how many points", "points", "course", "ignore", "not sure", "wasnt me",
            "wasn't me", "someone else", "not my car", "court", "court date", "magistrates",
            "magistrates court", "court hearing", "court summons",
            # the letter itself, however the person words getting it
            "what happens", "what happens now", "happens now", "now what", "got",
            "got in the post", "in the post", "arrived", "what is it", "what does it mean",
            "how serious")),
          "Answer the letter within 28 days and name who was driving: ignoring it is the expensive "
          "path, because it is six points and up to £1,000 instead of three and £100. If you were "
          "driving, take the speed awareness course where it is offered - no points, about £100 - "
          "and pay the fixed penalty if not. The notice has to reach the registered keeper within "
          "14 days of the offence, so if it is much later than that, say so in your reply.",
          # whether the limit was fair, and a ticket from a private car park or a bus lane, are
          # other answers: this is the letter about speed
          avoid=("parking", "parking ticket", "bus lane", "bus gate", "ulez", "congestion",
                 "council tax", "private", "supermarket", "airport", "mot", "insurance cost",
                 "how much is my insurance", "speeding up my laptop", "speeding up my computer",
                 # a price question wants the number first: "how much does a speeding course
                 # cost" was the 28-day letter, whose price is in the fourth sentence
                 "how much does", "how much do", "how much are", "how much is a",
                 "how much is the", "cost", "costs", "price", "price of", "cheapest"),
          # "court" and "magistrates" are in this row's key as well as the witness and jury rows',
          # which costs it the rare-word point the school definition of speed did not lose, so
          # the row that answers the letter has to be the one asked for it
          bias=2),
    # A court date is a day out of someone's week, a letter to answer and a truth to tell, and
    # none of it is what the person expects to know already: "im a witness in a trial next week"
    # was "Sorry to hear that. What would help most right now?" and "i got a jury summons" was
    # "Ugh, that's a lot to carry". The day itself is the answer, not the worry.
    entry("court-witness",
          (("witness", "witness summons", "witness statement", "give evidence", "giving evidence",
            "go to court as a witness", "court as a witness", "called as a witness",
            "appearing as a witness"),
           ("court", "trial", "summons", "witness", "magistrates", "crown court", "jury",
            "next week", "next month", "what happens", "what do i do", "what should i do",
            "do i have to go", "do i have to", "have to", "how long", "nervous", "scared",
            "worried", "day off", "time off")),
          "You will get the court's letter with the date, the time and which court, and you do "
          "have to go: reply to it, and tell them straight away if the date cannot work. Take the "
          "letter and your statement on the day, plan to be there all day even if you are "
          "finished by lunch, and tell the usher when you arrive. A solicitor will go through "
          "your statement with you before you are called, and when you are in the box you say "
          "what you remember and say plainly when you do not remember. Claim the expenses and "
          "the loss of earnings afterwards.",
          # a crash the person saw is the crash answer's, and a crime is a report to the police:
          # what this row has is the day at court
          avoid=("crash", "crashed", "accident", "police", "report it", "stolen", "insurance",
                 "hit and run", "smash", "damaged", "whiplash",
                 # a day in court about a motoring charge is the notice's answer, not the day's:
                 # the points, the 28 days and the course are what that person needs first
                 "speeding", "speed ticket", "ticket", "parking", "penalty", "fine", "fined",
                 "driving", "drink driving", "licence", "license", "mot", "insurance claim",
                 "council tax", "summons for", "non payment", "not paid"),
          bias=4),
    # Jury service is the other letter from a court, and it is the one people ask how to get out
    # of: ten days, waiting, an employer that has to let them go and an allowance that pays them.
    entry("jury-service",
          (("jury", "jury service", "jury duty", "juror", "jurors", "jury summons",
            "on a jury", "called for jury service", "called up for jury"),
           ("summons", "called", "call", "reply", "how long", "what happens", "what do i do",
            "do i have to", "defer", "deferral", "exempt", "excused", "excuse", "get out of",
            "work", "employer", "boss", "pay", "paid", "lost earnings", "expenses",
            "two weeks", "how many days", "days", "next week", "next month", "this month",
            "next year", "coming up", "soon")),
          "Jury service is usually about ten working days, so plan on two weeks at the court, and "
          "most of it is sitting and waiting rather than being on a case. Reply to the summons, "
          "and if those dates cannot work ask to defer once - inconvenient dates alone do not get "
          "you out, but a serious illness or being someone's only carer does. Your employer has "
          "to give you the time off, and you claim travel and a loss-of-earnings allowance.",
          # the verdict and the sentence are the trial's, not the summons'
          avoid=("guilty", "verdict", "sentence", "sentencing", "deliberating", "we found",
                 "i am on a jury", "i am a juror", "witness", "evidence"),
          bias=4),
    # A fine the person did not pay is the third letter from a court, and the frightening part is
    # the prison word in it: what they do with the letter in the next fortnight is the answer.
    entry("unpaid-fine-court",
          (("fine", "fines", "unpaid fine", "court fine", "court summons", "summons for a fine",
            "single justice procedure", "single justice notice", "magistrates fine",
            "council tax summons", "liability order", "i didnt pay", "didnt pay", "not paid",
            "havent paid", "cant pay", "cannot pay", "arrears"),
           ("court", "summons", "letter", "prison", "jail", "bailiffs", "enforcement",
            "what do i do", "what should i do", "what happens", "plead", "pleading", "guilty",
            "not guilty", "reply", "respond", "ignore", "payment", "installments",
            "instalments", "afford", "means form", "mc100", "means",
            # the letter, however the person words getting it
            "notice", "procedure notice", "got", "got in the post", "in the post", "arrived",
            "what is it", "what does it mean", "how serious", "frightening")),
          "Reply to the court instead of ignoring it: the form with the letter takes a plea and a "
          "statement of your income, and the court sets a fine you can pay in instalments from "
          "that. Nobody is jailed for a first missed payment - the prison warning is about not "
          "replying at all - and if you cannot pay what was set, ask the court to look at your "
          "means again rather than skipping it. A council tax summons is not a criminal record, "
          "and paying before the hearing usually stops the extra costs.",
          # the motoring and parking notices have their own answers with the points and the
          # discount in them, and a fine for something that is not this letter is not this row
          avoid=("speeding", "speed", "parking", "pcn", "bus lane", "ulez", "congestion",
                 "tv licence", "how much is", "how much does", "what is a fine",
                 "how much are fines", "library", "how do i pay a fine", "where do i pay"),
          # a mood word is not a fine, and a best mate saying "it was fine" is not a court date
          guard=_the_fine_is_the_noun,
          bias=3),
    entry("energy-complaint",
          (("energy supplier", "energy company", "electricity company", "gas company",
            "my supplier", "energy provider", "electricity supplier", "gas supplier"),
           ("complain", "complaint", "complaining", "ombudsman", "overcharged", "wrong bill",
            "not replying", "won't reply", "wont reply", "ignoring", "refund", "dispute")),
          "Complain to the supplier in writing and ask for a deadlock letter if they will not fix "
          "it: after eight weeks, or straight away with that letter, the Energy Ombudsman takes "
          "the case free and can order a refund or compensation. Keep the bills, the readings and "
          "the dates you called. If a direct debit you did not agree to has been taken, tell your "
          "bank as well.",
          # Switching to a cheaper tariff, a bill that went up, and a meter question are not
          # complaints, and this answer would send those to the ombudsman.
          avoid=("switch", "switching", "cheaper", "tariff", "deal", "fixed", "went up",
                 "gone up", "increase", "estimate", "reading", "smart meter", "prepayment",
                 "moving house", "i'm moving", "im moving")),
    # A supplier going bust and a credit balance are the two energy facts people ask about in a
    # panic, and main answered both with a listening line or the shop-refund card ("can i get a
    # refund from my energy supplier" -> "For anything faulty you're entitled to a full refund
    # within 30 days"). Each is a fact, so each is a card of its own.
    entry("energy-credit-refund",
          # The first group is the money already paid over and nothing else. "my energy" and
          # "my supplier" used to be here, and with the account word below and the bias they
          # made this card the answer to "how do i close my energy account" and "how do i cancel
          # my energy contract", which are the contract's exit fee and not a refund. The thing
          # the money is with belongs in the second group, where every energy line is entitled
          # to it; the ask is the refund word in this one.
          (("in credit", "credit balance", "credit on my account", "credit back", "credit owed",
            "refund", "refunded", "money back", "owe me", "overpaid", "overpaying",
            "gave me back", "balance back", "paid too much"),
           # the phrases carry the phrase weight, which is what beats the shop card on "refund"
           ("energy supplier", "energy company", "energy bill", "gas bill", "electricity bill",
            "my energy", "my supplier", "energy", "electric", "electricity", "gas", "supplier",
            "provider", "bill", "account", "direct debit", "monthly")),
          "Ask for it back: a credit balance is your money, and a supplier has to refund it when "
          "you ask if the account is closed or after a price change, so ring or email with a "
          "final reading and your bank details, and keep the closing bill. If you are still with "
          "them, ask for the direct debit to come down instead, because a big credit means you "
          "have been paying more than the year needs.",
          # the shop-refund card was answering this on its "refund" key, and a bill that is
          # wrong or has risen is bill-went-up's: this card is the money already paid over
          avoid=("wrong", "wrong bill", "estimated", "estimate", "reading", "meter reading",
                 "too high", "so high", "gone up", "went up", "increase", "increased",
                 # "my electricity bill jumped" is why it rose, not money already paid over
                 "jumped", "jump", "jumps", "doubled", "double", "risen", "rise", "higher",
                 "sky high", "through the roof",
                 "cant afford", "can't afford", "cut", "reduce", "cheaper", "switch",
                 # a complaint about the supplier, and a smart meter offered or wanted, are
                 # both their own answers: this card is the balance already paid over
                 "complain", "complains", "complaint", "complaining", "ombudsman", "deadlock",
                 "ignoring", "ignored", "not replying", "dispute", "smart meter", "smart",
                 "wants", "wanted", "offered", "install", "fitting", "appointment",
                 "shop", "bought", "buy", "return", "returns", "item", "parcel", "delivery",
                 "order", "product", "warranty", "online", "train", "ticket", "flight", "hotel",
                 "holiday", "concert", "insurance", "tax", "hmrc", "council tax", "deposit",
                 "landlord", "tenancy", "rent",
                 # A direct debit the supplier has just put up is the rise card's line, which
                 # has the notice, the new figure and the guarantee in it: this card is money
                 # already paid over, and "put my direct debit up" was being read as that.
                 "put my direct debit up", "put the direct debit up", "direct debit up",
                 "put my dd up", "dd up", "raised my direct debit", "raise my direct debit",
                 "raised the direct debit", "raised my dd", "direct debit went up",
                 "direct debit has gone up", "increased my direct debit", "increased my dd"),
          bias=1),
    entry("energy-supplier-bust",
          (("gone bust", "went bust", "gone under", "ceased trading", "collapsed", "insolvent",
            "in administration", "administration", "stopped trading", "closed down",
            "supplier of last resort"),
           ("energy", "electric", "electricity", "gas", "supplier", "company", "provider",
            "my supplier", "my energy")),
          "Nothing to do but take a reading: Ofgem moves your supply to a new supplier within "
          "days without you doing anything, and any credit balance is protected and comes across "
          "with you. Keep the direct debit open until the new supplier writes, take a meter "
          "reading and a photo of today's balance, and sign nothing until the switch is "
          "confirmed - if the new tariff is worse, you can switch again for free.",
          # a bank, a shop or an airline going bust is another answer
          avoid=("bank", "shop", "retailer", "airline", "travel", "holiday", "wedding",
                 "restaurant", "brewery", "builder", "business", "my company", "employer"),
          bias=1),
    entry("work-from-home-council",
          (("work from home", "working from home", "working from the flat", "work from the house",
            "home office"),
           ("council", "council tax", "business rates", "tell", "do i need", "declare",
            "inform", "register")),
          "Working from home as an employee does not change your council tax or need a business "
          "rate, so there is nothing to tell the council. It only becomes business rates if part "
          "of the home is used mainly for the business - a shop, a workshop with customers calling "
          "- and most kitchen-table businesses stay on council tax anyway. Do tell your insurer if "
          "you keep stock or see customers.",
          # The how-to-work-from-home lines are about focus and the boss, not the council.
          avoid=("concentrate", "focus", "distracted", "productive", "productivity", "boss",
                 "manager", "employer says", "should i", "worth it", "lonely", "routine",
                 "dress", "kids", "children", "childcare")),

    # --- money: the everyday asks the knowledge base had nothing for ---------
    # The general money answers - a payslip that changed, cooking from scratch, takeaway habits, a
    # council tax rise, the card-versus-savings choice, a rent rise, the credit/debit difference -
    # are `bot/knowledge/money.py`'s entries (#1193). One meaning, one table: not repeated here.
    #
    # These two are the shapes money.py does not cover: whether a particular gym is worth its fee,
    # and the awkward bill split where the group earns different amounts.
    entry("split-bill-fairly",
          (("split the bill", "splitting the bill", "share the bill", "divide the bill",
            "who pays", "who should pay"),
           ("fairly", "fair", "earn", "earns", "earning", "different amounts", "more than me",
            "less than me", "awkward", "one person", "someone always", "always pays", "mates",
            "friends", "group")),
          "Agree the rule before the bill lands, not over it: usually even thirds and the person "
          "who earns most offers to cover the drinks, or everyone pays for what they had. Say it as "
          "a rule rather than about a person - \"shall we just split it three ways?\" - and whoever "
          "holds the card takes transfers the same day, service charge included. The discomfort "
          "comes from not saying it, not from the amount.",
          bias=1,
          ask=("fairly", "fair", "awkward", "earn", "earns", "earning", "different amounts",
               "more than me", "less than me", "always pays", "one person"),
          # An ordinary "how do i split a bill between friends" is money.py's, and it is answered
          # well; only the fairness question comes here.
          avoid=("moved in", "move in", "live together", "living together", "girlfriend",
                 "boyfriend", "partner", "wife", "husband", "flatmate", "flatmates", "housemate",
                 "housemates", "tenant", "rent",
                 # "who pays what when one earns more" is the couple's income split, and "even
                 # thirds" is wrong for two people. The income words hand it to money's
                 # money-and-partner, which is the answer that fits.
                 "one earns more", "when one earns more", "earns more", "earn more",
                 "earns way more", "earn way more", "income", "salary", "wage", "wages")),
    # The question is asked as an opinion as often as a sum: "i pay 42 a month and go twice a week,
    # is that daft" is the same arithmetic as "is my gym worth it", so the opinion words are in the
    # second key group rather than a separate entry. The frequency words stay out on purpose:
    # "i go twice a week, is that enough" is how-often-exercise's question, not this one.
    entry("gym-worth-it",
          (("gym", "gym membership", "membership"),
           ("worth it", "worth", "cost", "much", "cheaper", "value", "waste", "daft",
            "paying", "rip off", "rip-off", "money")),
          "Divide the monthly fee by the visits you actually make. £40 a month is good value at "
          "eight visits (£5 a session) and poor at two (£20), which is usually cheaper as pay-as-"
          "you-go or a council leisure card. If you want to keep it, book the sessions in the "
          "calendar like appointments - the fee is not the problem, the unused month is.",
          bias=1,
          avoid=("cancel", "cancelling", "cancellation", "cancel my membership", "contract",
                 "notice period", "direct debit", "joined", "join a gym", "personal trainer",
                 # someone at the gym asking about training keeps the training answer
                 "protein", "muscle", "cardio", "weights", "lifting", "diet", "calories",
                 "beginner", "routine", "exercises", "supplements", "sore", "how often",
                 # a frequency question is about training, not about money
                 "enough", "how many times", "too often",
                 # "how much is my membership" asks the price, not whether it is worth it
                 "my gym membership", "how much do i pay", "how much am i paying")),
    entry("budget-how",
          (("budget", "budgeting", "spending plan", "money plan", "budget planner",
            "monthly budget",
            # the job is named without the word budget: "i need to sort out my money", "how do i
            # get on top of my finances". Each is a phrase the budget word stands in for.
            "sort out my money", "sort my money out", "sort out my finances",
            # The plainest way people name the job, and it reached nothing: "i want to be better
            # with money" was the chat module's "i want to X" pool ("Be better with money - fair
            # enough. What's stopped it happening so far?") and "how can i be better with money"
            # was a shrug and a search offer. There is no separate question behind the words: the
            # worksheet below is the answer to being better with money, said any of these ways.
            "better with money", "better at money", "good with money", "good at money",
            "with my money", "handle money", "money under control", "in control of my money",
            "control of my money", "money sorted out", "on top of my money",
            "sort my finances out", "sort my money", "my finances", "my money sorted",
            "get on top of my money", "get on top of my finances", "money in order",
            "finances in order", "get my money in order",
            # "whats a good budget for a family of four" was the cheaper-dinners row, because
            # "budget" and a family of four is also how a cheap meal is asked for
            "a good budget", "good budget", "family budget", "household budget",
            "budget for a family", "budget for a household", "budget for a family of four",
            "budget for a family of five"),
           # The words a person uses when they want the worksheet and never name it as one:
           # "help me with my budget", "i need to sort my money out".
           # "my" is an ask word too, and has to be: "my budget is a mess", "my budget never
           # works" and "i want to sort my budget out" are how-to lines. #2951 left "my" out of
           # this list so that a stated amount and a what's-my read would stop getting the
           # worksheet, and that took the answer off six real lines. The two that are not asks -
           # a value given and a value read back - stand down in answers `_store_keeps_the_line`
           # instead, which is where a fact about the line belongs.
           ("how", "make", "build", "start", "write", "set", "set up", "plan", "monthly",
            "my", "need", "better", "stick", "track", "first", "simple", "proper", "help",
            "sort out", "work out", "figure out", "in order", "get on top of",
            "what", "whats", "should", "spend", "spending", "family of four", "family of five",
            "family of three", "household", "four", "five")),
          "Write down what comes in each month, then what goes out in two piles: the fixed ones "
          "(rent, bills, travel, debt) and the ones you decide week by week (food, going out, "
          "clothes). What is left is what you can save or throw at a debt, and if the piles add "
          "up to more than comes in, cut from the weekly ones first because that is where the "
          "slack is. The 50/30/20 shape - half on needs, a third on wants, a fifth on saving - is "
          "a starting point, not a rule, and a notes app you check every Sunday beats a clever "
          "spreadsheet you never open.",
          # a present budget, a wedding, or the cheapest way to buy one thing are other answers
          avoid=("christmas", "xmas", "wedding", "birthday", "presents", "gifts", "holiday",
                 "how much does", "cheapest", "car insurance",
                 # "how much is my budget" asks for the number back, and the answer is the store's
                 # ("Your budget is 400 pounds"). These phrases used to say it here; now `answers`
                 # hands any stated or asked-back value to the store itself
                 # (`_store_keeps_the_line`), which also catches what this list could not: "my
                 # budget is a mess" and "my budget is out of control" are statements with no
                 # value in them, and were being avoided as if they were reads.
                 "much is my budget",
                 # "is it better with money or card" is a payment-method question, and the new
                 # "better with money" key was taking it. The wage is the pair of words, so the
                 # payment words are named and the worksheet steps aside for them.
                 "or card", "by card", "cash or card", "card or cash", "contactless",
                 "debit card", "apple pay", "google pay", "by cash", "in cash")),
    entry("christmas-budget", (("christmas", "xmas", "festive season"),
                               ("budget", "save", "saving", "spend", "spending", "presents",
                                "gifts", "cost", "afford", "money", "overspend",
                                "overspending", "too much", "spent")),
          "Fix a total you can pay for in cash this month, divide it by the people you buy for, "
          "and write the cap next to each name before you open a browser. Buy in October, agree a "
          "secret santa with the adults, and shop for food from a list in early December: the "
          "overspend is nearly always late presents and a trolley filled in a panic.",
          # A present question is a present question: without an ask for a money word, "presents"
          # and "gifts" also put "christmas present for my sister" here instead of gift-person.
          ask=("budget", "budgeting", "save", "saving", "spend", "spending", "spent", "cost",
               "costs", "afford", "money", "overspend", "overspending", "too much",
               "how much"),
          avoid=("turkey", "roast", "dinner", "tree", "decorations", "cake", "when is"),
          bias=1),

    # Probate is asked as a timing question ("how long does probate take") and as a what-do-i-do
    # question, and the honest answer is the same: the inheritance tax return is the long pole.
    entry("probate-how-long",
          (("probate", "grant of probate", "letters of administration", "executor",
            "executors", "administer the estate"),
           ("how long", "long", "take", "takes", "time", "apply", "applying", "wait", "weeks",
            "months", "do i need", "need", "start", "process", "cost", "solicitor", "myself")),
          "In England and Wales a straightforward estate usually gets probate six to twelve weeks "
          "after you send the forms. The long pole is the inheritance tax return: over the 325,000 "
          "pound threshold the IHT400 comes first and can add months. Apply yourself through the "
          "government probate service when the will is simple; a solicitor earns the 1,500 to 3,000 "
          "pounds if there is a house, a business or a disagreement.",
          # a funeral, a wake and a will that is being argued over are all other answers
          avoid=("funeral", "cremation", "burial", "ashes", "wake", "flowers", "sympathy",
                 "condolence")),

    # --- the first days after a death --------------------------------------
    # The practical errand, not the grieving: "what do i say", "i keep crying" and the funeral
    # itself are other answers, so those words stand this one down.
    entry("register-death",
          # "register" alone must not carry it, or "how do i register to vote" becomes this
          # answer, so the second group is the death side of the question and "death" is one of
          # its words: register + death is the two signals the matcher wants.
          (("register", "registering", "registered", "registration", "registrar",
            "register office", "tell us once", "death certificate", "death certificates",
            "medical certificate", "report a death",
            # "who do i tell when someone dies" and "how do i close my late father's account" are
            # the same errand as registering it: the registration is where the Tell Us Once code
            # comes from, and nothing else in the tables answers either line.
            # the plainest shape of all names no paperwork: "what do i need to do when someone
            # dies" and "what are the first things to do when someone dies" were a stall about
            # agreements and a hedge, because registration words were the only key.
            "someone dies", "somebody dies", "someone has died", "somebody has died",
            "when someone dies", "when somebody dies", "a death in the family",
            "death in the family", "someone close to me dies", "after a death",
            "first things to do", "what to do first",
            "who do i tell", "who to tell", "who do i need to tell", "who should i tell",
            "close my late", "his accounts", "her accounts", "their accounts",
            "close his account", "close her account", "close their account"),
           ("death", "deaths", "died", "dying", "passed away", "certificate", "certificates",
            "office", "documentation", "paperwork", "account", "accounts", "bank", "bills",
            "council", "benefits", "pension", "pensions", "utilities", "dies")),
          "The doctor or coroner gives you the medical certificate; then you register the death at "
          "the local register office, within five days in England and Wales. Take that certificate, "
          "their birth certificate and NHS number. You leave with the death certificates for the "
          "bank and insurers, and a Tell Us Once code that tells the tax office, council and "
          "benefits at once. Scotland and Northern Ireland differ, so ask the register office.",
          # grief, the funeral and the will are separate answers
          avoid=("cry", "crying", "grief", "grieving", "miss him", "miss her", "miss them",
                 # what to say to someone who has been bereaved is the condolence card's, and
                 # the phrase "when someone dies" is in both lines
                 "what do i say", "what to say", "say to", "saying to", "sympathy card",
                 "condolence", "condolences", "card say",
                 "funeral", "cremation", "burial", "ashes", "wake", "sympathy", "condolence",
                 "eulogy", "probate", "will", "sorry for your loss",
                 # a birth, a marriage and the electoral roll are other registrations
                 "birth", "born", "marriage", "married", "vote", "voting", "electoral")),

    # -- whose money pays for a funeral -------------------------------------
    # "Who pays for a funeral" is not "who pays for dinner": the answer is where the money comes
    # from, and the day it is asked the person does not know that the estate settles the bill
    # first or that the council will bury somebody with no money at all. It is here, beside the
    # registration, because it is asked in the same week and by the same person. The cost of the
    # funeral, the help with paying it and the arrangements themselves are other answers.
    entry("who-pays-for-the-funeral",
          (("funeral", "funerals", "cremation", "burial", "buried", "undertaker",
            "funeral director", "funeral directors", "the deceased", "the estate",
            # the wake is the same bill, and it is asked the same way ("who pays for the wake").
            # Only the phrases: "wake" on its own is a baby, a night's sleep and a funeral tea.
            "the wake", "at the wake", "the wake food", "the wake reception"),
           ("who pay", "who pays", "who paid", "who is paying", "who should pay", "who covers",
            "who is responsible", "whose responsibility", "who is liable", "liable",
            "pay", "pays", "paid", "paying", "afford", "affords", "cant afford",
            "can't afford", "invoice", "invoiced", "the bill", "bill",
            "claim it back", "claim the money back")),
          "The bill comes out of the estate before anything is shared out, so the money the "
          "person left pays for their own funeral. The person who signs the funeral director's "
          "form is the one who owes it if the estate cannot cover it, and a bank will often pay "
          "the funeral director straight from the account on an invoice. If there is no money at "
          "all the council has to arrange and pay for a basic funeral, and the DWP funeral "
          "expenses payment covers part of the bill for people on certain benefits.",
          bias=3,
          # what a funeral costs, the help with paying it, the arrangements, the wake food and
          # the flowers are all other answers
          avoid=("how much", "expensive", "cheaper", "cheapest", "compare", "or burial",
                 "or cremation", "what should i wear", "arrange", "arranging", "plan the",
                 "planning", "sandwiches", "buffet", "catering", "flowers", "eulogy", "speech",
                 "condolence", "sympathy", "sorry for your loss", "cry", "crying", "grief",
                 "missing", "miss him", "miss her")),

    # "Do I need a funeral director", "can I do a funeral myself": the row that plans a funeral
    # (family.py) needs a planning word and the money rows need a cost word, so the question of
    # whether anyone has to be paid to do it fell through to a search hedge. It is a legal and
    # practical fact, not a plan or a price, so it lives here beside the registration.
    entry("funeral-without-a-director",
          (("funeral", "funerals", "cremation", "crematorium", "burial", "memorial",
            "funeral director", "funeral directors", "undertaker", "undertakers",
            "direct cremation", "diy funeral"),
           ("do i need", "do we need", "must i", "must we", "have to", "has to", "can i",
            "can we", "myself", "ourselves", "on my own", "on our own", "without",
            "needed", "required", "allowed", "legally", "law", "possible", "instead")),
          "No - in England and Wales you can arrange a funeral yourself; nobody has to be paid to "
          "do it. What the crematorium or cemetery needs is the paperwork: the death registered, "
          "the registrar's green certificate (or the coroner's order if there was a post-mortem), "
          "and a signed application form from whoever is arranging it. Ask the crematorium or the "
          "council's bereavement office what their form and fee are before you decide, because the "
          "fee is the same either way and the director's charge is the part you would be saving. A "
          "direct cremation, no service and no mourners, is the cheapest version of the same thing "
          "and you can buy it from a director for about a thousand pounds.",
          bias=2,
          # the cost of a funeral, help with paying for one, and the three decisions of planning
          # one are each other answers, and this row is only about whether a director is required
          avoid=("cost", "costs", "price", "much", "pay", "pays", "paid", "afford", "help with",
                 "dwp", "claim", "grant", "fund", "budget", "plan", "planning", "arrange",
                 "arranging", "organise", "organizing", "where do i start", "cannot afford")),

    # A name is admin, not paperwork for one occasion: after a marriage, after a divorce, or by
    # deed poll when nothing has happened at all. "how do i change my name after marriage" was a
    # shrug, and so was the plain "how do i change my name".
    entry("change-name",
          (("change my name", "change her name", "change his name", "change our name",
            "change the name", "name change", "deed poll", "new surname", "new name",
            "double barrelled", "double-barrelled", "take his name", "take her name",
            "maiden name", "surname change", "childs surname", "child's surname",
            "change my surname", "change my last name", "change my family name",
            "change my childs name", "change my sons name", "change my daughters name",
            "change my kids name", "change his surname", "change her surname"),
           ("married", "marriage", "wedding", "civil partnership", "divorce", "divorced",
            "how do i", "can i", "do i need", "passport", "driving licence", "dvla", "bank",
            "surname", "child", "children", "daughter", "son", "born", "after", "name",
            "i want", "want to", "is it possible")),
          _change_name,
          # naming a baby, a pet, a band or a wifi network is a different question; so is moving
          # house
          avoid=("what should i name", "what to name", "name my", "name for my", "name ideas",
                 "good name", "cat", "kitten", "dog", "puppy", "rabbit", "band", "wifi",
                 "sourdough", "starter", "business", "company", "username", "email",
                 "change my address", "change of address", "moved house", "moving house")),

    # --- the letters that arrive and scare people ---------------------------
    # A parking ticket is the one piece of paper where doing nothing is the expensive option
    # and where the 14-day discount quietly disappears, so the deadline leads the answer.
    entry("parking-ticket",
          (("parking ticket", "parking tickets", "parking fine", "pcn", "penalty charge",
            "parking notice", "parking charge notice", "ticket on my car", "windscreen ticket",
            "clamped", "clamp"),
           ("appeal", "appealing", "contest", "contesting", "challenge", "dispute", "fight",
            "wrong", "unfair", "not fair", "should i pay", "do i pay", "worth", "got",
            "got one", "just got", "received", "two minutes", "what do i do",
            "what should i do", "on my own street", "outside my", "on my car", "this morning",
            "yesterday")),
          "Pay or appeal within 14 days: most councils take 50% off if you pay in that window, and "
          "appealing inside it keeps the discount open. Photograph the sign, the bay markings and "
          "where the car was, then appeal online to the council named on the ticket. If they "
          "refuse, the free adjudicator cancels a good share - the Traffic Penalty Tribunal "
          "outside London, London Tribunals inside it. Never ignore one: it ends with bailiffs.",
          # A ticket from a private car park, a supermarket or an airport is a different animal:
          # its appeal goes to POPLA or the IAS, the deadlines differ, and council advice given
          # confidently to a private notice is a wrong answer, not a vague one.
          avoid=("private", "supermarket", "airport", "retail park", "hospital", "hotel",
                 "train station", "station car park", "council tax", "speeding", "bus lane",
                 "congestion", "parking permit", "resident permit", "parking space",
                 "my neighbour", "blocked in")),
    # Anyone can ring and claim to be the bank; the only safe instruction is to end the call and
    # ring the number printed on the card, so that is the first sentence.
    entry("bank-scam-call",
          (("scam", "scams", "scammed", "scammer", "phishing", "fraud", "fraudster",
            "cold call", "cold caller", "suspicious text", "suspicious email", "text saying",
            "message saying", "email saying", "account is blocked", "account blocked",
            "account is locked", "account has been locked", "unusual activity",
            "account at risk", "they froze", "frozen my account",
            # The call in the words people use for it, with no scam word anywhere in the line:
            # "someone from my bank rang asking me to move money" is the whole question.
            "rang asking", "rang me asking", "called asking", "called me asking",
            "phoned asking", "phoned me asking", "asked me to move", "asked me to confirm",
            "asked for my pin", "asked me for my pin", "asked for my details",
            "confirm my pin", "my pin", "safe account", "move money to a safe",
            "read out a code", "read out my code", "gave them my details"),
           ("bank", "barclays", "lloyds", "natwest", "hsbc", "santander", "halifax",
            "monzo", "starling", "nationwide", "they said", "said they were", "was that",
            "is that", "is it one", "someone rang", "someone called", "rang me", "called me",
            "my account", "my card", "read out", "code", "text", "email", "message")),
          "No real bank rings to ask you to move money, read out a code, or give your PIN, even "
          "when the account is at risk. Hang up, wait a few minutes, then ring the number on the "
          "card and check whether anyone tried to contact you. If money has gone, ring the bank's "
          "fraud line: some transfers can be recalled and you are not in trouble. Report it to the "
          "fraud service for your country.",
          avoid=("gym", "subscription", "energy", "supplier", "parcel", "delivery", "ebay",
                 "facebook", "marketplace", "ticket", "holiday", "rental", "landlord",
                 "builder", "roof", "damp", "someone to fix", "was that a scam charge",
                 # This answer is about a phone call ("no real bank rings..."), and it was the one
                 # an email got, because "scam" and "email" are both in its key and the mail words
                 # are common in this domain, so it outranked the email answer. A scam email is a
                 # different question: the sender address, the link, the account behind it.
                 "email is a scam", "scam email", "phishing email", "is this email",
                 "email looks", "the email says", "an email saying", "email saying",
                 "sender address", "inbox", "attachment", "suspicious email", "fake email")),
    # A bin is a small thing that people put off for months; the free replacement is the fact
    # worth leading with, and buying your own is the mistake the last line prevents.
    entry("new-bin",
          (("bin", "bins", "wheelie bin", "wheelie", "rubbish bin", "recycling bin",
            "bin lid", "food waste bin"),
           ("new", "replacement", "replace", "broken", "stolen", "cracked", "damaged",
            "missing", "order", "buy", "cost", "how much", "ring the council", "council")),
          "Ring your council's waste line or use the form on their website: a broken or stolen bin "
          "is usually replaced free, and a missing or wrong-sized one costs about £20 to £50. Say "
          "which bin it is, your address and what happened; a replacement normally turns up in a "
          "couple of weeks. Don't buy and use your own unless they tell you that you can, because "
          "most rounds will not empty an unofficial bin.",
          avoid=("how often", "collection day", "bin day", "what goes in", "recycling",
                 "food waste", "smell", "overflowing", "full", "rats", "foxes", "neighbour",
                 "flats", "skip", "garden waste", "compost",
                 # a bin that was not emptied is not a bin to replace: the missed collection is a
                 # report to the council, not an order for a new bin
                 "missed", "not collected", "wasnt collected", "wasn't collected",
                 "didnt collect", "didn't collect", "did not collect", "not emptied",
                 "wasnt emptied", "wasn't emptied", "not been collected", "not been emptied",
                 "left behind", "left it", "drove past", "skipped my", "wasnt taken",
                 "wasn't taken", "not taken", "didnt take", "didn't take", "not picked up",
                 "wasnt picked up", "wasn't picked up", "not been picked up")),
    # A collection that did not happen is a report, and it is free: the commonest bin question
    # there is had no answer of its own, so "my bin wasnt collected" was "I'm listening".
    entry("missed-collection",
          (("bin", "bins", "wheelie bin", "wheelie", "recycling", "refuse", "food waste",
            "garden waste", "rubbish", "bin men", "binmen", "bin lorry",
            # "the lorry didnt come" names the thing that fails to arrive as often as the crew do
            "lorry", "the crew", "collection crew"),
           ("missed", "not collected", "wasnt collected", "wasn't collected", "didnt collect",
            "didn't collect", "did not collect", "not emptied", "wasnt emptied",
            "wasn't emptied", "not been collected", "not been emptied", "left behind",
            "drove past", "skipped my", "only took half", "half emptied", "still full",
            "still there", "hasnt been", "hasn't been",
            # "the bin men didnt come" is the same report said as a person who never turned up,
            # and it was an acknowledgement: the key names "bin men" but nothing here said the
            # crew failed to arrive, so no two parts of the line met.
            "didnt come", "didn't come", "didnt turn up", "didn't turn up", "never came",
            "never turned up", "no one came", "nobody came", "no one turned up",
            "nobody turned up", "didnt arrive", "didn't arrive", "didnt show", "didn't show",
            # "the recycling wasnt taken" is the same report in the other verb
            "wasnt taken", "wasn't taken", "not taken", "didnt take", "didn't take",
            "not picked up", "wasnt picked up", "wasn't picked up", "not been picked up",
            # a complaint about the bins is this report in the asking words: "how do i complain
            # about the bin collection" was "ask in writing and name what you want: a refund, a
            # repair, or money for the trouble", which is a company complaint, and the first
            # thing to do about a bin that was not emptied is ring the council the same day.
            # The first part already names the bins, so the complaint words cannot reach here
            # on their own.
            "complain", "complains", "complaining", "complaint", "complaints")),
          "Report it to the council the same day: a missed bin is free to report, the form is on "
          "their waste page, and most rounds come back within two working days. Leave the bin out "
          "at the kerbside where they can reach it, note the date and any reference, and if it "
          "happens twice photograph the full bin and note when the lorry came past - a repeat miss "
          "is usually a round that changed and nobody told you.",
          # a bin that is broken, stolen, too small or not ordered yet is the replacement card's,
          # and the smell, the rats and the lid are the cleaning and repair questions
          avoid=("new", "replacement", "replace", "broken", "stolen", "cracked", "damaged",
                 "order", "buy", "cost", "how much", "smell", "smells", "stinks", "maggots",
                 "flies", "rats", "mice", "fox", "foxes", "seagull", "seagulls", "lid", "cover",
                 "how often", "what goes in", "overflowing", "what time", "which bin",
                 "what day", "what can i put"),
          bias=2),
    # Council tax letters are almost always about a name, a discount or a payment matched to the
    # wrong reference, so the answer names those three and asks for it in writing.
    entry("council-tax-letter",
          (("council tax", "council tax bill", "council tax account", "council tax letter",
            "council tax arrears"),
           ("name", "in my name", "change the name", "not on", "taken off", "owe", "owed",
            "arrears", "paid it", "thought i paid", "reminder", "summons", "wrong",
            "check", "breakdown", "discount", "single person", "moved out",
            "died", "widowed", "husband", "wife", "partner", "housemate")),
          "Ring the council tax line and ask for it in writing. Most of these letters are a "
          "payment to the wrong reference, a discount never applied, or a bill for a name or date "
          "that has changed. Ask for a breakdown instalment by instalment and check it against "
          "your bank. If you now live alone, ask for the 25% discount backdated; if the bill is "
          "right, ask to spread the arrears.",
          # The amount of council tax, a band question for a house you are buying, and the bill
          # as an example of a cost are all other answers.
          avoid=("how much is", "how much will", "band a", "band b", "band c", "band d",
                 "how much do i pay", "per month", "student", "students", "empty",
                 "second home", "holiday let", "business rates", "buying a house", "rent",
                 "budget",
                 # a bill charged on the home rather than on people is the council tax row's
                 # question: "does my partner have to pay council tax" was read as a disputed
                 # letter and got "ask for a breakdown instalment by instalment".
                 "per person", "per household", "does my partner", "does my flatmate",
                 "have to pay", "who has to pay", "who pays", "how many people",
                 # a bill the person cannot pay is the arrears card's question, not the letter's
                 "cant pay", "can t pay", "cannot pay", "not paid", "havent paid", "haven t paid",
                 "forgot", "forgot to pay", "missed a payment", "behind on", "behind with",
                 "payment plan", "payment arrangement", "arrangement", "overdue",
                 "struggling", "cant afford", "can t afford")),
    # A letter nobody has told you how to read is its own job. Every row here passed the bare
    # line - the writing rows want a "how", the council tax row wants a word about the bill, the
    # payslip and pension rows want their own paper - so "i cant understand this letter" was read
    # back to the person as news, and "how do i understand this letter" was answered with how to
    # *write* one. What a person needs is where to look on the page and who will explain it free.
    entry("a-letter-i-cannot-follow",
          (("letter", "letters", "official letter", "paperwork", "form", "notice", "notices",
            "decision letter", "letter they sent", "letter they sent me", "letter i got",
            "letter from the council", "letter from the dwp", "letter from the bank",
            "letter from the hospital", "letter from the school", "letter from hmrc",
            "letter from the jobcentre", "letter about my benefits", "letter about my claim"),
           ("understand", "dont understand", "don t understand", "cant understand",
            "can t understand", "cannot understand", "doesnt make sense",
            "does not make sense", "dont make sense", "cant make sense", "can t make sense",
            "make sense", "make of it",
            # "i dont get this letter" is "i dont understand it", not "no letters arrive": the
            # phrases carry the letter, so "i dont get any letters from them" stays out.
            "dont get this letter", "dont get the letter", "dont get this one",
            "cant get my head round", "cant get my head around",
            "makes no sense", "confusing", "confused", "jargon", "cant follow", "dont follow",
            # "what it says", never a bare "says": on a follow-up the whole chat is joined and
            # "a letter saying i owe 400" then answered a question about the amount with a card
            # about reading the letter.
            "what does it mean", "what it means", "what it says", "what the letter says",
            "what does this letter mean", "what does the letter mean",
            "plain english", "explain it", "explain this",
            "help me read", "hard to read", "cant work out", "what am i meant to do")),
          "Find three things before you read the rest: who sent it, the date, and the line in bold "
          "that says what they want and by when. Copy the reference number at the top too, because "
          "it is the first thing they ask for when you ring. If a paragraph still makes no sense, "
          "ring the number printed on the letter and say it plainly - \"I have your letter and I "
          "do not understand what you need me to do\" - then ask them to email you the answer so "
          "you have it in writing. Ringing costs nothing and no deadline is ever hurt by asking, "
          "but the deadline itself does pass, so ring before it even if the only thing you say is "
          "that the letter is unclear. Citizens Advice will read it through with you for free, and "
          "for benefits or debt ask the council or them about a welfare rights worker.",
          # A letter you cannot follow is not a letter you want written: the writing rows own the
          # "how do i write", and a complaint, a resignation or a thank-you note is a different
          # job with its own answer.
          avoid=("write", "writing", "written", "draft", "reply", "respond", "complain",
                 "complaint", "appeal", "put in writing", "or write", "word it", "wording",
                 "template", "cover letter", "resignation", "thank you", "thanks", "love",
                 "birthday", "christmas", "apology", "apologise", "condolence", "sick note",
                 "reference", "cv", "speech", "eulogy",
                 # the paper with its own row: a pension statement, a payslip, a council tax bill,
                 # an energy bill and a bank statement are all read for a named number
                 "pension", "payslip", "pay slip", "council tax", "gas", "electric",
                 "electricity", "energy", "water", "broadband", "phone bill", "mobile bill",
                 "credit card", "bank statement", "statement", "invoice", "receipt",
                 # and the ones that are about a thing going wrong rather than the reading of it
                 "notice period", "redundancy", "eviction", "court", "summons", "fine",
                 "parking ticket", "penalty", "missed", "late", "overdue", "arrears",
                 "havent paid", "haven t paid", "didnt pay", "cant pay", "cannot pay")),
    # "I am behind with my council tax" is not a letter to read, it is a payment problem, and
    # every existing row passed it: the letter wants a name, date or reference, the band row wants
    # a band, and the reduction row wants a discount. Name the two steps a person actually has to
    # take - an affordable arrangement before it escalates, and a means hearing if it already has.
    entry("council-tax-arrears",
          (("council tax", "council tax bill", "council tax account", "council tax arrears",
            "council tax payment plan",
            # once the bill is the subject people say "the council": "how do i set up a payment
            # plan with the council". The phrases carry the payment with them, because a bare
            # "the council" is a bin round a council job and a wage slip as often as a bill
            "payment plan with the council", "plan with the council", "pay the council",
            "paying the council", "payments to the council", "arrangement with the council",
            "arrange with the council", "council payment arrangement",
            "council tax payment arrangement",
            # "can the council take money from my wages" never says "council tax"; these
            # phrases carry "council", so a bare "council" cannot pull in a bin row or a council
            # job, and "can they take it out of my wages" on its own is not this entry's question.
            "council take money from my wages", "council take it from my wages",
            "council take it out of my wages", "council take money out of my wages",
            "council take money from my pay", "council take it from my pay"),
           ("behind", "behind on", "behind with", "cant pay", "can't pay", "cannot pay",
            "owe", "owed", "havent paid", "haven't paid", "didnt pay", "didn't pay", "not paid",
            "arrears", "payment plan", "take money from my wages", "wages", "earnings",
            "attachment of earnings", "summons", "liability order", "court", "bailiff",
            "bailiffs", "struggling",
            # the ways people say it without the word "arrears"
            "forgot", "forgot to pay", "missed", "missed a payment", "late", "late payment",
            "overdue", "dont pay", "don t pay", "not pay", "stop paying", "arrangement",
            "payment arrangement", "instalments",
            # "i cant afford my council tax" is the same statement as "i cant pay it", and it
            # was the one shape the cant-pay row had fenced off without this row saying it: the
            # negative forms, not a bare "afford", because "can i afford my council tax" is a
            # budget question and belongs to the Citizens Advice card.
            "cant afford", "can t afford", "cannot afford", "can't afford", "not afford")),
          "Ring the council tax line before the next payment date and ask for an affordable "
          "payment plan: most councils will spread the arrears over the rest of the year, and an "
          "arrangement made before a summons is far cheaper than one made after it. Ask for a "
          "full breakdown of the bill and for Council Tax Reduction if your income is low. If it "
          "has already gone to a summons or a liability order, do not ignore it: contact the "
          "council and the court, ask for a means hearing, and get free advice from Citizens "
          "Advice. Once a liability order is made the council can ask for an attachment of "
          "earnings or deductions from benefits, but the court has to leave you enough to live on.",
          bias=1,
          # The amount, the band and a discount are other questions; so is a letter about a name
          # or a date, which the letter entry answers better.
          avoid=("how much is", "how much will", "band a", "band b", "band c", "band d",
                 "how much do i pay", "per month", "single person", "discount", "student",
                 "students", "empty", "second home", "holiday let", "business rates",
                 "buying a house", "rent", "budget", "change the name", "name on the bill",
                 "moved out", "moved in", "died", "widowed",
                 # A letter that names an amount is the letter entry's question: it says the
                 # three things a wrong bill usually is (a payment to the wrong reference, a
                 # discount never applied, a name or date that has changed) and to ask for it in
                 # writing, which is what a person holding a letter needs first. This row keeps
                 # the payment problem - "i owe council tax", "behind", "cant pay", "summons".
                 "got a letter", "i got a letter", "a letter saying", "letter says",
                 "letter saying", "bill says", "bill saying", "says i owe", "saying i owe")),
    # "can they make me pay it all at once" is the second half of the arrears question, and no
    # row answered it: it carries its subject over from the turn before ("i owe council tax from
    # 2 yrs ago"), and the arrears row is fenced off by its own letter guard, because the carried
    # words include "letter saying i owe" as if the person had typed them. The best the bot could
    # do was the write-to-the-council card about potholes. So the lump-sum question is a row of
    # its own, keyed on the ask rather than on the fence: what the council can and cannot do when
    # someone cannot pay the whole balance.
    entry("council-tax-in-one-go",
          (("council tax", "council tax arrears", "council tax bill", "council tax account",
            "council tax debt", "arrears"),
           ("all at once", "in one go", "in one payment", "lump sum", "one lump", "make me pay",
            "force me to pay", "can they force", "have to pay it all", "pay it all",
            "demand it all", "the whole amount", "whole balance", "full amount", "in full",
            "cant pay it all", "cannot pay it all", "cant pay that", "no way to pay it all")),
          "Not in one go, no. Councils take arrears in instalments, and the thing to ask for is "
          "a payment arrangement you can keep: ring the council tax line, say what is left after "
          "rent, food and bills, and ask them to hold any action while it is set up. They will "
          "want a breakdown of your income and can turn down an offer that looks too low, but "
          "they cannot take it from your wages or benefits until a court has made a liability "
          "order.",
          bias=1,
          # Another debt's arrears are that debt's answer, and the band, the discount and the
          # amount are other questions.
          avoid=("rent", "mortgage", "credit card", "loan", "overdraft", "energy", "gas",
                 "electric", "electricity", "water", "phone", "broadband", "council house",
                 "band a", "band b", "band c", "band d", "how much is", "how much do i pay",
                 "single person", "discount", "student", "students", "empty", "second home",
                 "business rates", "budget", "instalments")),
    # The band is a value judgement about the house, not a payment query: the free check against
    # the neighbours' bands is the step people do not know exists.
    entry("council-tax-band",
          (("council tax band", "council tax bands", "my band", "which band", "what band",
            "band is my house", "band for my house", "band is my flat", "band a", "band b", "band c",
            "band d", "band e", "band f", "band g", "band h"),
           ("challenge", "challenging", "wrong", "too high", "appeal", "appealing", "change",
            "check", "reduce", "lower", "neighbour", "neighbours", "neighbor", "neighbors",
            "correct", "dispute", "overpaying", "is it right", "right", "house", "home", "flat",
            "property", "bungalow")),
          "Check your neighbours' bands first: the valuation list is free online, and two "
          "identical houses on different bands is the evidence a challenge needs. In England and "
          "Wales you have six months from moving in; ask the council which route applies if that "
          "has passed. A challenge can raise the band as well as lower it, so ring the council "
          "about a wrong bill before you go to the valuer.",
          avoid=("music", "song", "tickets", "gig", "wedding band", "reception", "rubber band",
                 "band practice", "my son's band"),
          # "my council tax band is wrong" ties with the letter row on the same two words, and a
          # wrong band is this question, so it wins the tie
          bias=1),
    # Raising money for a charity place is a plan question: the page, the target and who to ask,
    # not the race itself (that is the training entry in plans.py).
    entry("charity-fundraising",
          (("raise money", "fundraise", "fundraising", "sponsor", "sponsorship", "fundraiser",
            "charity", "justgiving", "donations"),
           ("how", "how do i", "charity", "run", "marathon", "10k", "walk", "cycle", "swim",
            "sponsored", "page", "target", "should i")),
          "Pick one page and one line: JustGiving and GiveWheel are free, take the fee from Gift "
          "Aid, and let people give in two taps. Set a public target (100 to 500 pounds for a local "
          "run), say what the charity does in a sentence, and name the date. Ask thirty people for "
          "twenty pounds rather than everyone for anything, and ask your employer to match. Post "
          "weekly, and thank each donor by name.",
          # the training plan, the race day and the cause's medical advice are other answers
          avoid=("train", "training", "plan", "week", "pace", "8 weeks", "12 weeks", "eat",
                 # A job in a charity shop is a job, not a sponsored run: "how do i get a job in a
                 # charity shop" was told to start a JustGiving page.
                 "job", "jobs", "apply", "applying", "application", "vacancy", "vacancies",
                 "hiring", "employment", "career", "salary", "paid work", "shop job",
                 "volunteer", "volunteering",
                 "shoes", "blister", "cramp", "tax", "tax return", "self employed", "hmrc",
                 # a business raising money is not a sponsored run: "how do i raise money for my
                 # startup" was getting the JustGiving page because "raise money" and "how"
                 # carried it
                 "startup", "start up", "start-up", "business", "company", "investor",
                 "investors", "seed funding", "seed round", "shares", "equity", "customers",
                 "revenue", "profit", "invoice", "invoices",
                 # Giving a thing away is not raising money for a charity: "how do i donate old
                 # clothes to charity" and "how do i donate a bike" were both handed the
                 # JustGiving page, because "donate" and "charity" are in the key. The rubbish
                 # domain answers where the thing goes.
                 "donate", "donated", "donating", "donation", "donations", "give away",
                 "giving away", "gave away", "clothes", "furniture", "books", "toys", "bike",
                 "bikes", "bicycle", "mattress", "sofa", "charity shop", "charity shops")),
    # The rise is the one council tax question the letter and band entries both pass: nothing is
    # wrong with the bill, and the band is not in question, so the person wants to know who sets
    # the number and when it changes. "How much is council tax" asks for the number, so that one
    # gets the average bill first and the timing after it.
    entry("council-tax-rise",
          (("council tax", "council tax bill", "my council tax"),
           ("rise", "rising", "rises", "gone up", "going up", "increase", "increased",
            "more", "why", "why has", "much", "when", "this year", "next year",
            "bill arrived", "letter", "twelve", "ten", "instalments", "monthly", "allowed",
            "legal", "cap", "percent",
            # the rise said with "put" and "up" apart: "the council keeps putting the council tax
            # up" reached nothing, because the key had "going up" and no "put".
            "putting up", "puts up", "put up", "keeps putting", "keeps putting up")),
          "The amount is set once a year by your council and the bill lands in April: a draft in "
          "February, first payment in April. Most of a rise goes on social care and bins, and "
          "councils get less government money than they used to. There is no cap on a year's rise. "
          "If you live alone, claim the 25% single-person discount; you can also pay over twelve "
          "months instead of ten.",
          # Another bill that went up, a band question, and a discount query all say "council
          # tax" or "more" too, and each has its own answer.
          avoid=("water", "gas", "electric", "electricity", "energy", "broadband", "phone",
                 "income tax", "rent", "mortgage", "parking", "planning", "redundancy", "gig",
                 "band", "bands", "band a", "band b", "band c", "band d", "band e", "band f",
                 "band g", "band h", "stain", "stains", "carpet", "wood", "floor", "taxi",
                 "student", "students", "empty", "second home", "business rates")),
    # "How much is council tax" asks for a number and the rise answer gives it a timetable, so the
    # one figure worth carrying is its own entry: the band D average, then where your own is.
    entry("council-tax-amount",
          (("council tax", "council tax bill", "council tax cost"),
           ("much", "how much", "cost", "average", "typical", "roughly")),
          "The average band D bill in England is about £2,171 a year for 2025-26. Yours is set by "
          "your council and your band, so the exact figure is on your bill. If it is more than you "
          "expected, check the band and the 25% single-person discount, and ask to pay over twelve "
          "months rather than ten.",
          avoid=("band", "bands", "up", "challenge", "appeal", "discount", "alone", "student",
                 "students", "empty", "second home", "wrong", "cant", "can't", "pay", "rise",
                 "rises", "rising", "gone up", "went up", "going up", "increase", "increased",
                 "backdated", "exempt", "reduction")),



    # "should i rent or buy" is `opinions.rent-buy`. What that entry does not answer is the
    # same question asked as "is it worth buying a house" - it needs a rent word on one side and
    # a buy word on the other - so only that shape comes here.
    entry("house-worth-buying",
          (("house", "houses", "flat", "property", "home"),
           ("worth buying", "worth it", "worth the money", "better to buy", "worth it to buy")),
          "Judge it on the years, not the price: buying beats renting once you stay about five "
          "years, because fees, the buying tax and moving need years of payments to earn back. "
          "Compare the mortgage plus service charge, insurance and repairs against the rent, and "
          "count the deposit as money you cannot move.",
          ask=("worth", "should", "better", "or"),
          # a car, a holiday let and a cheaper option of anything are other answers
          avoid=("car", "cars", "van", "bike", "holiday", "weekend", "cheaper", "which one",
                 "rent or buy", "deposit", "afford", "how much", "mortgage rate", "remortgage")),
    # --- the everyday admin nothing answered ---------------------------------
    # Each of these was a shrug on main ("I don't know enough to answer that honestly", or a
    # Citizens Advice pointer that names no step). They are the small tasks people put off, so
    # each answer is the first move and the time limit.
    entry("parcel-redelivery",
          (("parcel", "parcels", "package", "parcel delivery", "delivery", "courier"),
           ("redeliver", "redelivery", "re-deliver", "missed", "missed the delivery",
            "card through the door", "while i was out", "when i was out", "collect", "depot",
            "pick it up", "left a card", "not in", "wasnt in", "wasn't in", "reschedule")),
          "The card through the door has a reference on it: put that into the courier's app and "
          "choose another day, a neighbour, or a local shop, usually free. Royal Mail keeps a "
          "parcel 18 days before sending it back and most couriers about a week, so book it within "
          "a couple of days. Collecting in person needs the card and photo ID with the address.",
          # a parcel that never came, and a delivery that is just slow, are other answers
          avoid=("never arrived", "not arrived", "hasnt arrived", "hasn't arrived", "missing",
                 "lost", "how long does", "how long do", "first class", "second class", "abroad",
                 "international", "customs", "post office price", "stamp")),
    entry("car-insurance-renewal",
          (("car insurance", "insurance renewal", "car insurance renewal", "my insurance"),
           ("renew", "renewal", "renewing", "cheaper", "shop around", "compare", "auto renew",
            "auto-renew", "automatically", "went up", "gone up", "increase", "price", "quote",
            "switch", "cancel")),
          "Shop around about three weeks before the renewal: the same cover is often £100 to £200 "
          "cheaper elsewhere, because insurers raise the price for people who stay. Check the "
          "excess, the mileage and the named drivers on every quote, since a wrong mileage can "
          "void a claim. Do not let it auto-renew before the new policy starts: driving uninsured "
          "is a £300 fixed penalty and six points.",
          # a car that will not start, an MOT and a breakdown are other answers
          avoid=("mot", "tax", "breakdown", "wont start", "won't start", "battery", "tyre",
                 "claim", "accident", "windscreen", "written off", "no claims", "no-claims")),
    # Not a bare "junk": "how do i stop spending money on junk" is a shopping question with a
    # "stop" in it, and it was reaching this answer. Every line this is the answer to names the
    # mail it arrives in.
    entry("stop-junk-mail",
          (("junk mail", "junk email", "junk post", "junk letter", "junk letters", "spam",
            "leaflets", "flyers", "mailshots", "marketing",
            "post", "letterbox", "letter box", "through the door"),
           ("stop", "stops", "stopping", "reduce", "less", "get rid", "opt out", "unsubscribe",
            "so much", "loads", "lots", "delivering", "keeps coming", "keep coming",
            "through the door")),
          "Two free registrations cut most of it: the Mail Preference Service for addressed post, "
          "and a 'no junk mail' sticker on the letterbox for the leaflets; the Telephone Preference "
          "Service for cold calls, though it takes about a month. Email anyone else and say you "
          "withdraw consent. Mark email as spam rather than unsubscribing, because that trains the "
          "filter on everything from that sender.",
          # a letter that has not arrived, and a form in the post, are other answers
          # A bare "spam" is not an email word: "i get so much spam in the post these days" is the
          # letterbox, and the bare word stood this row down so the line got an echo of itself.
          avoid=("email", "emails", "e-mail", "inbox", "spam email", "spam emails",
                 # and a text is the 7726 answer: "how do i stop spam texts" was this row the
                 # moment the bare "spam" came out of the avoid.
                 "text", "texts", "sms", "text message", "text messages", "mobile",
                 # and a call is the block-the-number answer: "how do i stop spam calls" was
                 # this row once the bare "spam" came out of the avoid.
                 "call", "calls", "caller", "callers", "ringing",
                 "hasnt arrived", "hasn't arrived", "still waiting", "how long does", "first class",
                 "second class", "redeliver", "parcel", "package", "form", "application",
                 "post office", "post a letter", "post this", "post it", "send a letter",
                 "send it", "stamp", "delivery",
                 # a phone call wants the block-the-number answer, which is a better first move
                 "cold call", "cold calls", "nuisance call", "nuisance calls", "phone",
                 # and an inbox wants the filter answer below, not the letterbox one: "how do i
                 # stop spam emails" was getting the Mail Preference Service and a sticker
                 "email", "emails", "e-mail", "e-mails", "inbox", "gmail", "outlook", "hotmail",
                 "spam email", "spam emails", "junk email", "junk emails", "phishing")),
    entry("end-tenancy-early",
          # a rental agreement is the same question as a tenancy, and it was the one word the
          # key did not have: "how do i end a rental agreement early" fell through to a punt
          # while "how do i end a tenancy agreement" was answered.
          (("tenancy", "tenancy agreement", "lease", "rental", "rental agreement", "renting",
            "contract"),
           ("end", "ends", "ending", "early", "leave", "leaving", "quit", "break",
            "break clause", "get out of", "move out early", "before the end", "cancel",
            "surrender", "give notice")),
          "Read the break clause first: a fixed term often lets you leave after six or twelve "
          "months with two months' written notice. Without one you owe the rent until the term ends "
          "unless the landlord agrees, so ask in writing and offer to cover the re-letting costs, "
          "usually cheaper than paying to the end. Never post the keys back and stop paying: the "
          "debt follows you.",
          # "contract" and "renting" are the two words a phone, a gym and a tenancy share, and a
          # blocklist of the other places is the wrong way round: it misses the one nobody listed.
          # The gate is the other way, the way `cancel-gym` now does it - a tenancy word has to be
          # in the line. Without it "how do i get out of my contract" got the break clause.
          ask=("tenancy", "tenancies", "lease", "leases", "rental", "rentals", "renting", "rent",
               "flat", "house", "landlord",
               "propery", "property", "assured shorthold", "ast", "room", "studio", "bungalow",
               "furnished", "deposit", "agents", "letting"),
          # a deposit, a repair and a copy of the agreement are other answers
          avoid=("deposit", "boiler", "repair", "broken", "damp", "mould", "copy",
                 "landlord wants", "landlord is", "landlord has", "increase", "rent rise",
                 "evict", "eviction", "section 21", "notice to quit", "arrears",
                 # "how do i cancel her phone contract" got the tenancy break clause, because
                 # "cancel" and "contract" are on both lines: a phone, a gym or a lease is not
                 # this entry's, and the contract words alone are not a tenancy
                 "phone", "mobile", "sim", "broadband", "gym", "car insurance",
                 # and a tenancy never names a mobile network, which is how "get out of my
                 # contract with o2" was landing here
                 "o2", "vodafone", "giffgaff", "voxi", "tesco mobile", "sky mobile",
                 "airtime", "pac code", "phone contract", "mobile contract", "sim contract")),
    # Telling the landlord you are going is not the same question as getting out early, and the
    # two answers that had these lines were both about something else: "how do i tell my landlord
    # im leaving" got the job offer card ("not until you have a written offer you would accept"),
    # and "how much notice do i give my landlord" got the housing benefit card. The key needs the
    # landlord's own word, because "how do i end my tenancy" is the break-clause card above and
    # has no landlord in it, and the leaving word has to be there, because "how do i tell my
    # landlord about a repair" is the repair row's line.
    entry("tell-the-landlord-im-leaving",
          (("landlord", "landlords", "landlady", "letting agent", "letting agents"),
           ("notice", "notices", "leaving", "leave", "leaves", "move out", "moving out",
            "hand back the keys", "give the keys back", "last month", "end of the tenancy",
            "quit")),
          "Put it in writing, dated, and keep a copy: say you are leaving on the date your notice "
          "runs out - a month on a rolling tenancy in England, two on a fixed term with a break "
          "clause - and that it should end on the day the rent is due. Ask them to confirm the "
          "end date in writing, and book the deposit return, the final meter readings and the "
          "council tax move for that day.",
          ask=("notice", "leaving", "leave", "move out", "moving out", "hand back the keys",
               "last month", "quit"),
          # a landlord who is stopping them, evicting them, or refusing something wants the
          # rights answer, and a repair, a deposit or a rent rise is its own row
          avoid=("stop me", "can my landlord", "does my landlord have to", "refuse", "refuses",
                 "wont let me", "won't let me", "evict", "eviction", "section 21", "section 8",
                 "deposit", "deposits", "repair", "repairs", "broken", "boiler", "damp", "mould",
                 "mold", "leak", "leaking", "heating", "rent rise", "increase the rent", "raise the",
                 "arrears", "behind with", "sell the flat", "sell the house", "pets", "a cat",
                 # notice in the other direction is the tenant's rights, not the tenant's
                 # letter: "how much notice must a landlord give a tenant" was told to write and
                 # date their own notice
                 "give me", "give a tenant", "give their tenant", "to a tenant", "to the tenant",
                 "must a landlord", "does my landlord", "has my landlord", "landlord has to give",
                 "landlord give me", "landlord must",
                 "a dog", "housemate", "flatmate", "sublet", "buying it", "buy the flat")),
    entry("child-bank-account",
          (("bank account", "savings account", "current account", "account", "bank"),
           ("child", "children", "my son", "my daughter", "kids", "kid", "teenager", "teen",
            "under 18", "junior", "young", "11 year old", "12 year old", "13 year old",
            "14 year old", "15 year old", "16 year old")),
          "Up to about 11 it is a savings account in the child's name that you run; from 11 most "
          "banks open a current account with a contactless card and no overdraft. At 16 they can "
          "take it over; at 18 it is theirs alone, so teach the card habits first. A junior ISA is "
          "the other half: £9,000 a year, tax-free, locked until 18.",
          # a business or a student account wants different documents
          avoid=("business", "company", "sole trader", "self employed", "self-employed", "student",
                 "overdrawn", "joint", "loan", "mortgage", "switch", "switching",
                 "close", "closing", "proof of address")),
    entry("register-with-a-dentist",
          (("dentist", "dental", "nhs dentist", "dental practice", "teeth"),
           ("register", "registering", "sign up", "new", "find", "none", "take nhs",
            "taking nhs", "nhs", "appointment", "check up", "check-up", "moved")),
          "Ring practices near you and ask straight out whether they take new NHS patients, "
          "because the lists open and close. If none do, ring 111: they can find an urgent NHS "
          "appointment within 24 hours, and you do not have to be registered anywhere to be seen. "
          "An NHS check-up is £27.40 in England, and a dental school or a community clinic is "
          "cheaper still.",
          # pain, a broken tooth and a cost question are other answers
          # a length is another: "how long does a dentist appointment last", "how long does a
          # check up at the dentist take" and "how long does it take to register with a dentist"
          # were all answered with how to find a practice that takes new patients, because the
          # word "appointment" is in this key and no word says the line wants a time. The times
          # - the visit's length, and the wait - are written in the dentist appointment answer,
          # so this card stands down for every shape that asks for one. The words held out are
          # the ASK, not the noun: "the waiting list is two years, what can i do" and "the
          # dentist waiting list is months" are complaints about access and want this card, so
          # "wait", "waiting" and "waiting list" must never appear here - only "how long",
          # "how soon", "how many minutes" and "last"/"lasts", which are the shape of a length
          # question and nothing else.
          # A line about being frightened of the dentist is nerves, not registration:
          # "i'm nervous about a dentist appointment tomorrow" was getting the NHS list answer
          avoid=(
                 "how long", "how soon", "how many minutes", "last", "lasts",
                 # "teething problems with the new car" is a new thing finding its feet, and
                 # "teething" is a form of "teeth" to the word matcher, so this entry answered a
                 # new car, a new boiler and a new job with "ring practices near you ... whether
                 # they take new NHS patients". The phrase, not the bare word, is what to hold
                 # out: "my teeth are yellow" must still read.
                 "teething problems", "teething problem", "teething troubles", "teething issues",
                 "pain", "hurts", "hurting", "toothache", "abscess", "broken tooth", "chipped",
                 "knocked out", "bleeding", "how much", "cost", "price", "free", "whitening",
                 "braces", "filling",
                 # a line about being frightened of the dentist is nerves, not registration
                 "nervous", "scared", "afraid", "frightened", "terrified", "dread", "anxious",
                 "anxiety", "phobia", "hate the dentist", "fear",
                 # a complaint about an NHS dentist is not a request to register: the health
                 # complaint entry owns it, and both entries were matching the word "nhs"
                 "complain", "complaining", "complaint", "complaints",
                 # giving an appointment up is not registering for one: "how do i cancel a
                 # dentist appointment" was answered with the find-a-practice steps, which sent
                 # the person to ring 111 for a dentist they already had
                 "cancel", "cancelling", "canceling", "cancelled", "canceled", "reschedule",
                 "rebook", "postpone", "call off")),
    # Giving an appointment back is a different job from getting one, and the practice's own
    # notice period is what the answer is about: the key needs the giving-up word and the thing
    # given up, and everything else a person cancels has its own entry.
    entry("cancel-an-appointment",
          (("cancel", "cancelling", "canceling", "cancelled", "canceled", "reschedule",
            "rescheduling", "rebook", "rebooking", "postpone", "postponing", "call off"),
           ("appointment", "appointments", "dentist", "dental", "doctor", "gp", "surgery",
            "practice", "clinic", "hospital", "hygienist", "optician", "physio", "chiropodist",
            "chiropractor", "scan", "x-ray", "xray", "check up", "checkup", "slot")),
          "Ring as soon as you know, not on the morning: a day's notice lets the practice hand "
          "your slot to someone on its waiting list, and 24 hours is the notice most of them ask "
          "for. Use the text reminder or the NHS app if the practice has one, and rebook in the "
          "same call so you keep your place. For a hospital appointment ring the number printed "
          "on the letter rather than the main switchboard, and ask them to move it rather than "
          "cancel it. A missed hospital appointment costs the NHS about £120, and a surgery can "
          "take someone off its list after repeated no-shows.",
          # a subscription, a flight, a table and a friend who keeps flaking are other entries,
          # and a job interview is rebooked by talking to the interviewer
          avoid=("subscription", "subscriptions", "membership", "gym", "contract", "insurance",
                 "policy", "direct debit", "flight", "flights", "train", "hotel", "holiday",
                 "wedding", "party", "dinner", "plans", "flatmate", "landlord", "interview",
                 "friend", "mate", "cancelled on me", "cancels on me", "keeps cancelling",
                 "keeps canceling", "last minute", "refund", "charged", "order", "delivery",
                 "parcel", "broadband", "mobile", "netflix", "prime", "magazine",
                 # nerves about an appointment is not giving one up
                 "nervous", "scared", "afraid", "frightened", "dread", "anxious")),
    entry("repeat-prescription",
          (("prescription", "prescriptions", "repeat prescription", "medication", "medicine",
            "tablets", "inhaler", "pills"),
           ("repeat", "order", "reorder", "re-order", "again", "how do i", "how long",
            "running out", "run out", "pharmacy", "collect", "request")),
          "Order it about a week before you run out: a GP needs two working days and the pharmacy "
          "one or two more. Use the NHS app or the surgery's online service, or drop the slip in at "
          "the pharmacy and let them order it. Ask for two months if you are going away; only the "
          "GP can restart a repeat that was stopped.",
          # a new symptom, and a medicine question about doses, are other answers. Nor is this a
          # line about an animal: "how do i give my cat a pill" and "how do i get my dog to take
          # his medicine" were told to order a repeat from the GP a week before running out.
          avoid=("dog", "dogs", "puppy", "puppies", "pup", "cat", "cats", "kitten", "kittens",
                 "rabbit", "rabbits", "hamster", "guinea pig", "pet", "pets", "the vet", "vet",
                 "dose", "dosage", "overdose", "side effect", "side effects", "missed a dose",
                 "double dose", "antibiotic", "antibiotics", "paracetamol", "ibuprofen",
                 "how many can i take", "is it safe", "with alcohol", "pregnant",
                 # emergency contraception is a 72-hour question, not a repeat order: "how do i
                 # get the morning after pill" was told to order a week before running out
                 "morning after", "morning-after", "emergency contraception", "unprotected sex",
                 "condom", "condoms", "plan b", "ellaone", "levonorgestrel", "ulipristal",
                 # how to get a tablet down is not how to get more of them
                 "swallow", "swallowing", "with water", "can't swallow", "cant swallow",
                 # a tablet you wipe is not a tablet you swallow: "how do i clean a tablet screen"
                 # was told to order a repeat prescription a week before running out, and so was
                 # "how do i stop my kid being on his tablet all day" - a child on a tablet is a
                 # screen question and the only word this row needs is the one in "tablets"
                 "on his tablet", "on her tablet", "on their tablet", "on the tablet",
                 "on a tablet", "on my tablet", "his ipad", "her ipad", "the ipad", "an ipad",
                 "cartoons", "youtube",
                 "screen", "screens", "tablet screen", "clean", "cleaning", "cleaned", "wipe",
                 "wiping", "smudge", "smudges", "fingerprint", "fingerprints", "greasy",
                 "scratch", "scratches", "cracked",
                 # a tablet that will not start is not a medicine either: "how do i reset my
                 # tablet" was told to order a repeat prescription a week before running out.
                 # The faults a device has are never the words on a repeat slip.
                 "reset", "resetting", "restart", "restarting", "reboot", "rebooting",
                 "turn on", "turns on", "turn it on", "wont turn on", "won't turn on",
                 "wont start", "won't start", "charging", "charger", "battery", "update",
                 "updates", "updating", "sync", "syncing", "frozen", "froze", "stuck",
                 # "how do i get rid of a headache without tablets" and "i need painkillers for a
                 # sore back" are remedy questions: the word "tablets" plus "how do i" was enough
                 # to be told to order a repeat a week before running out.
                 "headache", "headaches", "head ache", "pain", "painkiller", "painkillers",
                 "get rid", "remedy", "remedies", "sore", "hurts", "ache", "aching",
                 "symptom", "symptoms",
                 # "how do i sleep better without tablets" and "how do i lower my blood pressure
                 # without pills" are the same remedy question with a medicine word in them: a
                 # line that has already ruled the tablets out is not asking how to order more.
                 # "how do i dispose of medicines" was answered with this row as well, and a
                 # medicine on its way to the bin is not one to reorder.
                 "dispose", "dispose of", "throw away", "throw out", "bin", "binned", "flush",
                 "recycle", "take back", "hand back", "unused", "out of date", "expired",
                 "past their date", "past the date") + NO_DRUGS),
    entry("sick-note",
          (("sick note", "fit note", "sick note from the doctor", "doctors note", "med3",
            "self certificate", "self-certify", "off work", "signed off"),
           ("how do i", "how long", "do i need", "need", "get", "work", "employer", "boss",
            "seven days", "7 days", "after", "more than", "weeks", "statutory")),
          "For the first seven calendar days you need no note at all: fill in the self-certificate "
          "your employer gives you. After that a GP fit note covers you, and you can ask by phone "
          "or online rather than in an appointment; it can say you may be fit for work with reduced "
          "hours or lighter duties. Hospital doctors, nurses and physios can issue one too.",
          # statutory sick pay and being too ill to work at all are other answers
          avoid=("statutory sick pay", "ssp", "how much", "pay", "money", "sacked", "dismissed",
                 "capability", "long term", "long-term", "disabled", "pip",
                 # an injury is not a note question: "how long off work with a broken wrist" wants
                 # the healing time, and "off work" was the only thing this row needed
                 "broken", "broke", "fracture", "fractured", "cast", "plaster", "sprain",
                 "sprained", "operation", "surgery", "recovery", "recover", "heal", "healing"),
          # A leave line carries every word the sickness line does not need: "i'm off work next
          # week", "off work on friday", "taking next week off work" and "booked a week off work
          # in june" all had `work` in the second group, so the fit-note card told a person going
          # to the seaside to fill in the self-certificate. What the card is about is the illness
          # and the paper: one of those words has to be in the line for this to be its answer.
          ask=("sick", "ill", "illness", "unwell", "poorly", "invalid", "injury", "injured",
               "pain", "hurts", "hurting", "sore", "bad back", "flu", "cold", "covid", "virus",
               "bug", "operation", "surgery", "hospital", "admitted", "note", "notes",
               "certificate", "certify", "signed", "sign", "med3", "doctor", "doctors", "gp",
               "employer", "boss", "hr", "seven", "7", "how long", "do i need", "statutory",
               "ssp", "stress", "stressed", "depression", "depressed", "anxiety", "anxious",
               "burnout", "recovering", "recovery", "maternity", "paternity", "pregnant",
               "bereavement", "carer", "caring for")),
    # --- certificates and family admin: the paper every family needs once ---
    # Each of these was a shrug on main 62831b8 ("I don't know enough", "That's beyond what I
    # know well"), and each has one office that issues it, one form and one figure.
    entry("register-a-birth",
          (("birth", "baby", "born", "register", "registration", "certificate"),
           ("register", "registration", "registering", "how do i", "certificate", "office",
            "deadline", "how long", "when")),
          "Register the birth within 42 days at the register office for the district where the "
          "baby was born, and book the appointment online: you need the date and place of birth, "
          "and both parents' names, places of birth and jobs. The short certificate is free; the "
          "full one, which is the one a passport application needs later, costs about £12.50.",
          avoid=("birthday", "birth control", "pill", "pregnant", "pregnancy", "labour", "due",
                 "contractions", "waters", "death", "died", "marriage", "stillbirth",
                 # "baby" plus an ask word makes a baby-care line a registration question. The
                 # words above cover the ones main already knew; what is still the card's on
                 # main 9ea3406 is the washing and the settling - "how do i bathe my baby",
                 # "how do i give my baby a bath", "when can i bath my baby", "how do i swaddle
                 # my baby", "how do i soothe my baby", "how do i top and tail my baby" and
                 # "how do i clean my babys umbilical cord" all answer "Register the birth
                 # within 42 days at the register office". A care verb is another entry's job,
                 # so it stands this one down; the office, the form and the deadline stay its
                 # own, and every "how do i register a birth" line still finds the card.
                 "bathe", "bathing", "bath", "bathed", "swaddle", "swaddling", "soothe",
                 "soothing", "top and tail", "umbilical", "umbilical cord", "colic", "colicky",
                 "spitting up", "reflux",
                 # the general form of the same thing: "how do i care for my baby" and "how do
                 # i look after a newborn" are the health visitor's question, and the office,
                 # the form and the 42 days answer a question nobody asked
                 "care for", "caring for", "care of", "look after", "looking after",
                 # a hiccup is baby care too, and "how do i stop baby hiccups" was landing on
                 # the register office: the baby word made it a registration line
                 "hiccup", "hiccups", "hiccupping",
                 # and the wind: "how do i stop my baby being windy" was a registration line,
                 # because the baby word plus "how do i" reached this key
                 "wind", "winds", "windy", "winding", "winded", "burp", "burps", "burping",
                 "trapped wind", "gripe", "gripes", "gripe water",
                 # washing is the other half of the same problem: "how do i wash baby clothes"
                 # and "how do i get stains out of baby clothes" answered "Register the birth
                 # within 42 days", and baby-clothes-wash holds those now. "how do i clean a
                 # baby bath" goes back to the bath-cleaning answer.
                 "wash", "washing", "washed", "laundry", "clothes", "stain", "stains",
                 "clean", "cleaning", "baby bath", "baby bath tub",
                 # getting married is not a birth to register, and "how do i get married" is
                 # read as a follow-up to whatever came before it: after a birth certificate
                 # the previous subject put the words "birth" and "certificate" back into the
                 # line and this entry answered it.
                 "married", "marry", "marrying", "wedding", "divorce", "divorced", "husband",
                 "wife", "engaged", "engagement", "propose", "proposing",
                 "miscarriage", "adoption", "adopt", "surrogate", "born early", "premature",
                 "feeding", "nappy", "sleep", "cot", "pushchair", "pram", "passport", "gp",
                 # the registration is paperwork, so a line about the baby's body or its care is a
                 # different question: "how do i stop my baby crying at night", "how do i get my
                 # baby to take a bottle" and "how do i stop my baby grinding her teeth" all came
                 # back "Register the birth within 42 days" on main (2026-11-06), because the keys
                 # are only "baby" and "how do i".
                 "teeth", "tooth", "gums", "teething", "grind", "grinds", "grinding",
                 "crying", "cries", "cry", "bottle", "formula", "breast", "breastfeeding",
                 # a baby's nails, hair and skin are care, not paperwork
                 "nail", "nails", "fingernail", "fingernails", "toenail", "toenails",
                 "scratch", "scratches", "scratching", "mittens",
                 "haircut", "hair", "cradle cap", "cradle", "nappy rash", "navel",
                 "colic", "reflux", "wind", "rash", "fever", "temperature", "vomiting",
                 "wean", "weaning",
                 # a dummy is a baby-care question, not paperwork: "how do i stop my baby using
                 # a dummy at night" answered "Register the birth within 42 days", since the
                 # keys are only "baby" and "how do i"
                 "dummy", "dummies", "pacifier", "dummy at night", "using a dummy",
                 "stop using a dummy",
                 "doctor", "dentist", "surgery", "practice", "vote", "voting", "electoral roll",
                 "car", "van", "insurance", "phone", "sim", "business", "company",
                 # travelling with a baby is a travel question: "how do i travel with a baby"
                 # came back "Register the birth within 42 days" as soon as the bus pass stopped
                 # taking it, because the keys are only "baby" and "how do i".
                 "travel", "travelling", "traveling", "trip", "holiday", "flight", "fly",
                 "flying", "abroad", "hotel", "airport", "packing", "car seat",
                 # the register office is not HMRC: "how do i register as self employed" was
                 # reaching this entry on the strength of "register"
                 "self employed", "self-employed", "sole trader", "freelance", "freelancer",
                 "hmrc", "tax", "tax return", "vat", "utr", "trading", "invoice", "invoices",
                 "national insurance", "payslip", "payroll"),
          # The avoid list above is one baby-care question short every time somebody thinks of a
          # new one: "how do i introduce a new baby to a toddler" and "how do i prepare my
          # toddler for a new baby" were both told to register the birth, because the keys are
          # only "baby" and "how do i", and "introduce" is not a care word anybody had thought
          # to write down. So the paperwork words are asked for instead, and no list has to keep
          # up: the office, the form and the deadline are what this row is about.
          ask=("birth", "born", "register", "registered", "registering", "registration",
               "registrar", "certificate", "paperwork", "form", "deadline", "42 days",
               "office", "notify", "tell anyone", "announce", "register the birth")),
    entry("child-benefit",
          (("child benefit", "benefit", "benefits", "claim"),
           ("child benefit", "children", "child", "claim", "how much", "much", "worth",
            "entitled", "eligible")),
          "Claim child benefit as soon as the birth is registered: one parent claims for all the "
          "children, on the HMRC app or on form CH2, and it can be backdated three months. It pays "
          "about £26 a week for the first child and about £17 for each one after. Over £60,000 "
          "adjusted net income the high-income charge takes some of it back and by £80,000 it has "
          "taken all of it, but claim anyway: that is what gives you the National Insurance "
          "credits.",
          avoid=("how do i get married", "how to get married", "how do i marry",
                 "universal credit", "housing benefit", "pip", "esa", "jobseekers", "tax credit",
                 "working tax", "carer", "disabled", "disability", "maternity pay", "paternity",
                 "statutory", "free school meals", "council tax", "reduction", "atm", "bank",
                 "fraud", "appeal", "child benefit letter", "stopped")),
    # "my child benefit has stopped" reached nothing (this row stands itself down on "stopped",
    # and the Universal Credit row wants a claim word the line never says), so the person got a
    # question about their child's behaviour instead. A stopped payment is its own question.
    entry("child-benefit-stopped",
          (("child benefit",),
           ("stopped", "stopped coming", "not paid", "havent been paid", "hasn't been paid",
            "has not been paid", "not been paid", "no payment", "missed payment", "missed a payment",
            "cut off", "suspended", "gone down", "why has", "why have", "been stopped",
            "stopped getting", "nothing this month", "come through", "come in this month",
            "not come", "didnt come", "didn't come", "no money")),
          "Ring the Child Benefit Office rather than assume it is gone: payments stop when a child "
          "turns 16 unless they stay in approved education or training, when a review form from "
          "HMRC goes back unanswered, or when the address or the person claiming is out of date. "
          "Look for a review or renewal letter first, return it, and ask for it to be backdated - "
          "it is usually restored from the date it stopped. If they say no, ask for the decision "
          "in writing and appeal within a month.",
          # stopping or cancelling it on purpose is a different question, and a line about being
          # paid for work is not this row's either
          avoid=("how do i stop", "how to stop", "how do i cancel", "how to cancel", "cancel my",
                 "opt out", "stop claiming", "claim universal credit", "universal credit",
                 "child turns 16", "still in education"),
          # the row only ever matches a line that names child benefit and a stopped payment, and
          # both it and the Universal Credit row score "child benefit stopped what do i do" - the
          # tie has to go to the row about the stopped payment.
          bias=3),
    entry("marriage-certificate",
          (("marriage", "married", "wedding", "certificate"),
           # The ask words ("how do i", "get", "need") cannot stand in the second group: with
           # them there, one word of the subject plus the words every question carries was
           # enough, so a follow-up widened with the conversation's subject became a
           # certificate order ("my ex husband will be at my daughters wedding" / "how do i
           # keep it civil" reached "how do i keep the wedding civil"). The second group is a
           # certificate word, and `ask` holds the line to a question about it.
           ("certificate", "certificates", "copy", "copies", "certified", "replacement",
            "lost", "order", "ordering", "replace", "replacing")),
          "Order a certified copy from the register office where the marriage was registered, or "
          "from the General Register Office online, giving the date, the place and both full names "
          "as they are on the day. It is about £12.50 and it comes in about a week; ask for the "
          "certified copy rather than the decorative one if it is for a passport or a visa.",
          avoid=("divorce", "divorced", "separated", "separation", "annul", "widow", "widowed",
                 "death", "died", "birth", "proposal", "propose", "proposing", "venue", "guest",
                 "guests", "dress", "speech", "vows", "photographer", "catering", "honeymoon",
                 "anniversary", "day", "gift", "ring", "rings", "change my name",
                 "name change", "deed poll", "budget", "cost", "cheap",
                 # getting married is giving notice and booking a registrar, not a copy of the
                 # certificate: "how do i get married" was a shrug on main and must stay one
                 # rather than become a certificate order
                 "get married", "getting married", "how do i marry", "how to get married",
                 "give notice", "notice of marriage", "registrar", "book the venue",
                 "save", "afford", "plan", "planning", "afford it", "money towards"),
          ask=("how", "where", "can", "could", "need", "needs", "get", "got", "do i", "what",
               "want", "find", "lost", "missing", "damaged", "torn", "replacement",
               "replace", "ordered", "receive", "arrive", "arrives")),
    entry("blue-badge",
          # the badge is the thing; bare "parking" is a skill ("parallel parking always gets
          # me") far more often than it is a badge question, so it is not a key word here
          (("blue badge", "badge", "disabled", "disability"),
           ("blue badge", "disabled", "disability", "apply", "application", "eligible",
            "qualify", "qualifies", "get", "how do i", "cost", "much")),
          "Apply to your council, not the NHS: the qualifying benefits are the higher rate of the "
          "mobility part of DLA, or 8 points or more on the moving around part of PIP, plus a few "
          "conditions such as being registered blind. You upload a photo, proof of address and the "
          "benefit letter, the council may book an assessment, the fee is up to £10 and a badge "
          "lasts up to three years and takes about six to eight weeks.",
          avoid=("parking ticket", "parking fine", "parking charge", "penalty", "appeal",
                 "parking permit", "resident permit", "car park", "clamped", "clamp", "towed",
                 "radar key", "blue light", "blue tack", "disabled toilet", "consultation",
                 "name badge", "badge on", "another car", "someone else's car", "borrow",
                 "park on", "double yellow", "parking bay", "outside my house", "residents bay",
                 "resident bay", "bay outside", "bus pass", "bus", "railcard",
                 # parking as a skill, not as a badge: "parallel parking always gets me"
                 "parallel park", "reverse park", "parking test", "parking lesson",
                 "park in a tight space", "tight space", "parking always", "cant park",
                 "can't park", "my parking", "parking practice", "parking manoeuvre",
                 "freedom pass")),
    # A disabled person's pass is the other half of the scheme and it had no row of its own: the
    # older person's row holds the word "disabled" in its `avoid` (because a line about a disabled
    # pass is not an age question), so five lines fell between the two rows and every one was a
    # shrug - "how do i get a disabled bus pass", "can i get a bus pass if im disabled", "do i get
    # free bus travel if im disabled", "is there a bus pass for disabled people", and a parent's
    # "my mum is disabled can she get a bus pass". A companion travelling free with someone who
    # cannot travel alone had no answer either, and got the older person's card.
    entry("disabled-bus-pass",
          (("disabled", "disability", "disabled person", "disabled persons", "disabled people",
            "blind", "partially sighted", "visually impaired", "deaf", "hard of hearing",
            "wheelchair", "wheelchair user", "learning disability", "learning difficulties",
            "carer", "companion", "cannot travel alone", "cant travel alone"),
           ("bus pass", "pass", "passes", "bus", "buses", "travel", "free travel", "free",
            "concessionary", "apply", "apply for", "get", "how do i", "entitled", "qualify",
            "eligible", "renew")),
          "A disabled person's bus pass is a council scheme and it costs nothing to apply. You "
          "qualify if you are blind or partially sighted, deaf, or cannot walk without help or can "
          "only walk a short way without severe pain, and also with a learning disability or if a "
          "driving licence was refused on medical grounds. Apply to your council with a photo, "
          "proof of address and evidence of the disability, and it gives free travel on local "
          "buses at any time rather than from 9.30am. In London it is the Freedom Pass, and a "
          "companion travels free with you on it if you cannot travel alone.",
          ask=("bus", "buses", "pass", "passes", "travel", "free", "concessionary", "freedom pass",
               "carer", "companion", "apply", "get", "entitled", "qualify", "eligible", "renew"),
          # a blue badge is the parking scheme and has its own row, and a railcard, a taxi card
          # and a Motability car are other schemes with other answers
          # "carer" is in the key because a carer may travel free with the pass holder, so a
          # carer's allowance or a benefit question needs fencing out, and so does buying a
          # wheelchair: the scheme answers neither, and a confident wrong card is worse than the
          # shrug the line had before.
          avoid=("blue badge", "badge", "parking", "park", "railcard", "rail", "train", "trains",
                 "taxi", "taxi card", "motability", "car", "cars", "wheelchair repair",
                 "scooter", "mobility scooter", "ramp", "radar key", "toilet", "toilets",
                 "carer allowance", "carers allowance", "carer's allowance", "allowance",
                 "allowances", "benefit", "benefits", "pip", "universal credit", "tax credit",
                 "get a wheelchair", "buy a wheelchair", "need a wheelchair", "hire a wheelchair",
                 "wheelchair accessible", "powerchair"),
          bias=1),
    # The key's first group used to hold the bare word "travel", so any how-to that said travel
    # reached it: "how do i keep my money safe travelling", "how do i get a travel card" and
    # "how do i travel with a baby" all got the older person's bus pass. The group now names the
    # scheme itself, and "concessionary travel" is one phrase so a line that names only the scheme
    # still has two words of the key. The second group keeps the question's own words ("apply",
    # "how do i"): score() needs two different words, and once "pass" is counted by the first
    # group they are what carry "how do i get a freedom pass". The people are named here, not the
    # word "travel": "free bus travel for pensioners" reaches it on "pensioners", while "do kids
    # travel free on buses" is about a child's fare and is left alone.
    entry("bus-pass",
          # The thing is the scheme, not the word "travel": a bare "travel" in a key that also
          # holds the asking words ("how do i", "get") reached every travelling question there
          # is. The key names the scheme and the people it is for, and the gate makes a scheme
          # word or an age compulsory, so a line that only says travel ("how do i use a bus",
          # "how do i get a travel card", "how do i travel cheaply in europe") cannot reach it.
          (("bus pass", "pass", "passes", "bus", "bus travel", "concessionary travel",
            "concessionary", "concession", "freedom pass", "older person", "travel"),
           ("bus pass", "pass", "concessionary", "concessionary travel", "free travel",
            "freedom pass", "free", "pension", "pensioner", "retired", "over 60", "60",
            # the ask's own words still count towards a score, and a bare "pass" is only one
            # word: "how do i apply for a pass" and "how do i renew my pass" need one more,
            # and the gate is what keeps them from reaching a bus nobody asked about
            "apply", "get", "how do i", "renew", "senior")),
          "In England you apply for the older person's bus pass through your council once you "
          "reach the state pension age for a woman born on the same day, and it is free travel on "
          "local buses from 9.30am to 11pm on weekdays and all day at weekends. Send a photo and "
          "proof of age and address; a disabled person's pass has no time restriction, and either "
          "arrives in about three weeks.",
          # what must be in the line at all: the scheme, an age, or the free travel it gives.
          # Without it "how do i use a bus" scored on "bus" and "how do i" and got the pass.
          ask=("pass", "passes", "pension", "pensioner", "pensioners", "retired", "retire",
               "60", "65", "66", "67", "free", "freedom pass", "concession", "concessionary",
               "older person", "state pension"),
          avoid=("bus timetable", "bus route", "bus fare", "bus lane", "bus stop", "bus driver",
                 # money on a trip is the travel lane's: "how do i keep my money safe
                 # travelling" was answered with the older person's pass, because travel and
                 # "how do i" are all the two lines had in common
                 "safe", "safely", "keeping my", "money belt", "pickpocket", "theft", "wallet",
                 "coach", "train", "railcard", "season ticket", "school bus", "bus number",
                 # "pass" the verb, not the noun: "i keep getting passed over" and "passed up for
                 # promotion" are about a job, and the row answered them with the bus pass. The
                 # idiom is a phrase, so a line that really does name a pass is untouched.
                 "passed over", "passed up", "pass over", "pass up", "passed me over",
                 # "travel" is the word that borrowed this answer for a travel-insurance line,
                 # and a claim on a travel policy is not a free bus ride
                 "insurance", "travel insurance", "ehic", "ghic", "health card", "abroad",
                 "claim on", "holiday insurance", "travel policy", "excess", "payout", "insurer",
                 "passed my", "pass my", "pass the", "pass an", "passed the", "pass exam",
                 # a student pass, a scholar's pass and a work pass are other schemes
                 "student", "students", "scholar", "university", "college", "work pass",
                 "staff pass", "season",
                 "skip the bus", "my son", "my daughter", "disabled", "blind", "wheelchair",
                 # a child on a bus is the child-bus-travel answer: under-fives ride free and
                 # 5 to 15 pay a fare, which the older person's scheme does not say
                 "child", "children", "kids", "kid", "under 5", "under five", "my kids",
                 "school child", "school children", "family", "families",
                 # "pass" is an exam as well as a ticket, and the gate takes "pass" plus the
                 # ask's own "how do i": the theory test and every revision question reached
                 # the bus pass until these words stood the scheme down
                 "theory", "theory test", "driving test", "driving theory", "exam", "exams",
                 "revise", "revision", "multiple choice", "hazard perception",
                 # and a country or a long trip is travel-cheaply and flights, not a bus pass
                 "europe", "abroad", "flight", "flights", "hotel", "holiday", "hostel",
                 "interrail", "cheap travel", "travel cheap", "travel cheaply", "cheaply",
                 # "pass" is a ball passed in a game: "how do i improve my pass in volleyball"
                 # was the older person's scheme, on "pass" and "how do i" alone. The sport is
                 # what fences it - "passing" alone cannot, because its own forms include the
                 # row's key word "pass" and that stands the whole scheme down.
                 "volleyball", "basketball", "netball", "rugby", "football", "soccer",
                 "hockey", "cricket", "handball", "gaelic", "the ball", "pass the ball",
                 "my pass in")),
    entry("school-place",
          (("school", "place", "admission", "admissions", "apply"),
           ("school place", "school places", "admission", "admissions", "apply", "application",
            "reception", "year 7", "secondary", "primary", "nursery", "appeal", "register",
            "registering", "enrol", "enrolment")),
          "Apply through your council's school admissions service, not to the school: the deadline "
          "is 31 October for a secondary place and 15 January for a primary or reception place, and "
          "you list several schools with the one you most want first. An application after the "
          "deadline is only looked at once everyone else has been placed, and if you are refused "
          "you appeal to the school's admission authority, which is usually the council.",
          guard=_an_ask_about_a_place,
          avoid=("school run", "school holidays", "term dates", "uniform", "bullying", "bullied",
                 "homework", "teacher", "exam", "exams", "gcses", "a levels", "fees",
                 # the council form is for a school: "how do i apply for a university place" is
                 # UCAS, and it reached this card on "apply" and "place"
                 "university", "uni", "ucas", "personal statement", "degree", "undergraduate",
                 "masters", "college course", "student loan", "further education",
                 "private school", "home school", "school dinner", "packed lunch", "school bus",
                 "start school", "nervous about school", "refuses to go", "school report",
                 "nursery", "nurseries", "childminder", "childminders", "day care", "daycare",
                 "pre-school", "preschool", "creche", "playgroup")),

    # --- the paper chase: a claim, a complaint and the proof someone asks for ------------
    # These lines all named the thing they wanted and still got the shrug or the wrong answer:
    # "how do i claim on my insurance" got nothing, "how do i complain to the ombudsman" got
    # nothing, and "how long does a refund take" fell on the sale-refund rule about faulty goods.
    # A warranty claim is in `shopping.py` with the rest of the consumer-rights answers.
    # The excess is also a price lever, and the claim card keyed on "excess" answered "does a
    # bigger voluntary excess really save much" with how to report a claim. A question about
    # changing the excess is a question about the premium, so it has its own answer.
    entry("voluntary-excess",
          (("excess", "excesses", "voluntary excess"),
           ("insurance", "insurer", "policy", "premium", "cover", "car", "home", "buildings",
            "contents", "save", "saves", "saving", "cheaper", "cheap", "worth", "reduce",
            "lower", "bigger", "higher", "increase", "raise")),
          "A bigger voluntary excess does cut the premium, but by less than most people expect: "
          "moving from £100 to £250 often takes £20 to £80 off a year, and the next £250 usually "
          "saves less again. Ask the same insurer for the quote at two or three excess levels and "
          "weigh the yearly saving against what you would pay on a claim, because the excess is "
          "what you find on the day. Do not set it higher than you could pay at short notice, and "
          "check that a lease or finance agreement does not cap it.",
          ask=("save", "saves", "saving", "cheaper", "cheap", "worth", "reduce", "lower",
               "bigger", "higher", "increase", "raise"),
          avoid=("claim", "claiming", "claimed", "damage", "accident", "crashed", "stolen",
                 "flood", "leak", "write off", "payout", "not covered", "refused"),
          bias=1),
    entry("insurance-claim",
          (("insurance", "insurer", "insurers", "home insurance", "contents insurance",
            "travel insurance", "car insurance", "buildings insurance"),
           ("claim", "claiming", "excess", "payout", "pay out", "pay", "pays", "paid",
            "stolen", "flood", "leak", "damaged", "accident", "crashed", "write off",
            "how do i", "what do i do", "do i need to", "will they", "not covered",
            "wont pay", "won't pay", "refused", "refusing", "declined", "turn down", "turned down")),
          "Tell the insurer before you fix or replace anything: most policies want the damage seen "
          "first, and repairing early turns a claim into a negotiation. Photograph everything, keep "
          "receipts and quotes, and report a theft to the police for a crime number. Ask what the "
          "excess is before you go ahead, because a claim smaller than the excess costs you money, "
          "and claim on one policy only when two could cover it.",
          guard=_the_excess_is_a_price_question,
          avoid=("cancel", "cancelling", "renewal", "renew", "cheaper", "cheap", "cheapest",
                 "compare", "quote", "worth it", "how much is insurance", "life insurance",
                 "pet insurance", "shop around", "average price", "reduce my", "lower my",
                 # leaving one insurer for another is a claim on nobody: "how do i switch car
                 # insurance" was answered with "tell the insurer before you fix or replace
                 # anything", which is the claim answer
                 "switch", "switching", "switch insurer", "change insurer", "change insurance")),
    # "who do i complain to" names nobody at all, and it was a shrug on main: the answer that
    # helps is the shape of a complaint - put it in writing, say what you want, then the
    # ombudsman for whoever it turns out to be. The guard is what makes that safe: the row
    # answers only when the line has no subject left in it, so "who do i complain to about
    # noise", "... about a parcel" and "... about the damp" keep the rows those subjects belong to
    # (the first draft of this row was `escalate-complaint` with "who do i" added, and it took
    # all three of them - three deck chats got a company letter instead of their own answer).
    entry("a-complaint-with-no-subject",
          (("complain", "complains", "complaining", "complaint", "complaints",
            "complain about", "make a complaint", "raise a complaint"),
           ("who do i", "who to", "who can i", "where do i", "how do i", "who should i",
            "i want to", "want to", "need to", "can i", "complain", "complaint", "formal",
            "help", "rights")),
          "Ask in writing and name what you want: a refund, a repair, or money for the trouble. "
          "Once eight weeks pass, or they send a final response you disagree with, take it to "
          "the ombudsman for that industry - Financial for a bank or insurer, Energy for a "
          "supplier, Communications for broadband and phones, and the Local Government Ombudsman "
          "for a council - which is free and needs no lawyer. Keep the date of every call and "
          "letter: the timeline is the case.",
          guard=_a_complaint_with_no_subject),
    # The dictionary row for "deductible" answers "an excess", "insurance excess" and "policy
    # excess". It does not answer "a voluntary excess", "a compulsory excess" or a bare "what does
    # excess mean", which used to be a search hedge or the how-to-claim card. This is the other
    # half of the same word, and it stands down whenever the dictionary row's own phrase is in the
    # line, so the two never compete and the dictionary answer is never shadowed.
    entry("the-excess-is-what-you-pay",
          (("excess", "excesses", "voluntary excess", "compulsory excess"),
           ("what is", "what are", "what does", "whats", "what's", "meaning", "mean",
            "explain", "definition", "define", "tell me about", "how does", "how do")),
          "An excess is the first part of any claim you pay yourself: if the repair is £900 and "
          "your excess is £250, the insurer pays £650. Every policy has a compulsory excess and "
          "you can usually add a voluntary one on top in return for a lower premium. It applies "
          "to each claim rather than each year, so two separate claims mean paying it twice; the "
          "schedule says the amount and whether it comes off the payout or goes to the repairer.",
          guard=_the_excess_is_what_it_means,
          bias=3,
          ),
    entry("escalate-complaint",
          (("complain", "complaint", "complain about", "ombudsman", "deadlock letter",
            "final response", "still not fixed", "not been fixed", "no reply", "not replying",
            "eight weeks", "escalate", "take it further", "take this further"),
           ("company", "supplier", "bank", "banks", "insurer", "insurance", "broadband", "phone",
            "mobile",
            "energy", "water", "council", "shop", "airline", "holiday", "hotel", "gp",
            "doctor", "hospital", "escalate", "next", "further", "formal", "written",
            # "how do i complain to the ombudsman" names no company: the words of the question
            # itself have to carry the second signal.
            "ombudsman", "complain", "complaint", "how do i", "how to", "what can i do",
            "help", "rights", "take it further", "take this further", "further",
            # The ask for the route is the same question as the act of complaining, and it was
            # the one shape this row could not read: "who do i complain to about a bus driver"
            # reached the coach-pricing card instead, which answered a question nobody asked.
            "who do i", "who should i", "who can i", "who to complain", "who do i complain",
            "where do i complain"),
           # The ombudsman line names no company at all, so the phrase has a part of its own:
           # "how do i complain to the ombudsman" has to reach the answer that names which
           # ombudsman, not the shop complaint that mentions one on the way past.
           ("to the ombudsman", "the ombudsman", "which ombudsman", "ombudsman about")),
          "Ask in writing and name what you want: a refund, a repair, or money for the trouble. "
          "Once eight weeks pass, or they send a final response you disagree with, take it to the "
          "ombudsman for that industry - Financial for a bank or insurer, Energy for a supplier, "
          "Communications for broadband and phones - which is free and needs no lawyer. Keep the "
          "date of every call and letter: the timeline is the case.",
          # a complaint about a neighbour, a boss or a partner is not a company complaint, and
          # neither is an argument between two people: "how do i stop an argument escalating"
          # was reaching the ombudsman
          avoid=("neighbour", "neighbors", "neighbours", "landlord", "boss", "manager",
                 "husband", "wife", "partner", "friend", "family", "noise", "dog", "child",
                 "school", "teacher", "argument", "arguments", "argue", "argues", "arguing",
                 "row with", "rows with", "row", "rows", "squabble", "squabbling",
                 "bickering",
                 # a supplier complaint already has its own entry, with the deadlock letter
                 "energy supplier", "energy company", "energy ombudsman", "my supplier",
                 "electricity", "gas bill", "not replying",
                 # a bank complaint has its own entry too, with the eight weeks and the
                 # Financial Ombudsman; this generic one was taking the bank lines
                 "bank", "banks", "my bank",
                 # a bad meal is settled at the table, off the bill: the consumer answer has
                 # the service charge, and this one was taking "complain about a restaurant meal"
                 "restaurant", "restaurants", "meal", "meals", "waiter", "waitress", "cafe",
                 "takeaway", "service charge", "restaurant meal",
                 # a complaint about a person's care is about that surgery or ward, not a
                 # company that sells you something
                 "doctor", "doctors", "gp", "dentist", "nurse", "hospital", "surgery",
                 "practice", "consultant", "midwife", "care home",
                 # a builder or a plumber is not covered by any of these ombudsmen: that
                 # complaint goes to a trade body or small claims, so keep the honest answer
                 "builder", "builders", "tradesman", "tradesmen", "plumber", "electrician",
                 "roofer", "decorator", "contractor", "garage", "mechanic",
                 # a bin, a pothole or a street light is a service the council runs, and the
                 # report of that fault has its own answer: "i want to complain to the council
                 # about the bins" was the ombudsman card here, and the council's nuisance
                 # line before this branch added a row in front of it.
                 "bin", "bins", "bin bag", "bin bags", "wheelie", "wheelie bin", "recycling",
                 "bin collection", "missed bin", "not collected", "refuse collection",
                 "litter", "fly tipping", "flytipping", "fly-tipping", "pothole", "potholes",
                 "street light", "street lights", "graffiti", "dog fouling",
                 # a decorator made this list and a painter did not, so "how do i complain about
                 # a painter" was told to take it to the Financial or Energy ombudsman: a person
                 # doing work on your house has no ombudsman at all, and `tradesman-bad-job`
                 # has the written-complaint and small-claims answer. The trade noun is what
                 # carries it: an adjective alone - "botched", "shoddy", "bad job", "cowboy" -
                 # is said about a bank as readily as a builder, and as an avoid it would stand
                 # this entry down for "how do i complain about a botched repair from my bank".
                 "painter", "painters", "plasterer", "plasterers", "tiler", "tilers",
                 "joiner", "joiners", "workman", "workmen", "fitter", "fitters",
                 "landscaper", "landscapers", "installer", "installers", "snagging",
                 # the first letter to a company is `complaint-letter`'s; this entry is what
                 # you do after they have not answered
                 "company", "companies", "shop", "store", "retailer", "hotel", "holiday",
                 # "airline" was here and "flight" was not, so "how do i complain about a
                 # delayed flight" reached this entry through "complain" and "how do i" and
                 # then stood itself down, and the flight bands answer it
                 "airline", "airlines", "flight", "flights", "plane", "airport",
                 # a complaint about a person at work is the work domain's
                 "colleague", "colleagues", "coworker", "co-worker", "employee", "staff",
                 "hr", "human resources", "my team", "appraisal",
                 # a bad meal or a bad room is settled at the table, off the bill: the
                 # consumer answer has the service charge and the environmental health route
                 "restaurant", "cafe", "takeaway", "meal", "service charge", "my food",
                 "restaurant meal",
                 # money.py answers the bank step by step, with the Financial Ombudsman and the
                 # six-month window: a bank is not the generic eight-weeks letter
                 "about my bank", "to my bank", "to the bank", "my bank", "bank complaint")),
    # "how do i write a letter to the council" reached a "Citizens Advice covers this free"
    # line, and "how do i report a pothole" and "how do i report fly tipping" reached nothing at
    # all - the fly tip even got the fruit flies, because a gnat is a fly and the cider vinegar
    # answer keys the word. The everyday ask here is not the letter but who to tell: the
    # department, the facts they can act on and the record that gets it fixed. The company
    # complaint stands down for a council on purpose, so this row is the one home for it. A
    # letter to the town hall or to an MP is the wording domain's, and this row does not key it.
    entry("report-a-problem-to-the-council",
          (("council", "councils", "town hall", "local authority", "environmental health",
            "pothole", "potholes", "fly tipping", "fly-tipping", "fly tip", "fly-tip",
            "street light", "streetlight", "streetlights", "graffiti", "dog fouling",
            "dumped rubbish", "abandoned car", "broken pavement", "blocked drain",
            "street drain", "road drain", "drain in the street", "drain in the road",
            "blocked gully", "gully", "gullies", "drain cover",
            "dead animal", "public bin", "litter bin"),
           # the ask words here are the ones that mean "tell someone with the power to fix it".
           # A bare "how do i" or "clear" is not one of them: "how do i clear a blocked drain"
           # is the trap under the sink, and this row was taking it on those two words alone
           # (the household row scored 4 on "drain" and "blocked" and this one scored 6). The
           # shapes that really are a report - "how do i report a blocked drain on my street",
           # "who do i tell about the fly tipping", "get the pothole fixed" - all keep a word
           # from this list, so the row still answers them.
           ("report", "reporting", "who do i", "who", "tell", "get fixed",
            "fix", "fixed", "complain", "complaint", "come out",
            "come and", "log it", "raise it")),
          "Send it to the right department and give them what they need to act on it: the street "
          "or address, the date, a photo or reference number, and what you want done - potholes, "
          "pavements and street lights to highways, fly-tipping, bins, graffiti and dog fouling to "
          "environmental health, a repair in a council house to the repairs line with your "
          "tenancy number. Use the online form or email so there is a record, keep a copy and "
          "note the date. If nothing happens in ten working days, chase it and ask for it to be "
          "logged as a formal complaint; after their final reply the Local Government Ombudsman "
          "takes it on free.",
          # a council tax band, a blue badge and a school place are their own questions, and a
          # letter to the council or to an MP is the wording domain's
          avoid=("council tax", "band", "council house", "council flat", "school place",
                 "school admission", "parking permit", "blue badge", "housing benefit",
                 "council tax reduction", "recycling", "what goes in", "letter", "email to",
                 # a president or a school council is an office, not a repair: "who is the school
                 # council president" was this row once the American president's row stopped
                 # answering it, and neither answer is right for it
                 "president", "school"),
          guard=_council_owns_the_drain),
    # "who is my mp" cannot be answered from memory - it depends on where the person lives - but
    # the checker can, and pointing at it with the postcode is the honest answer. The councillor
    # is the same lookup for anything the council owns, which is most of the list above.
    entry("find-your-mp-or-councillor",
          (("my mp", "who is my mp", "mp for", "my member of parliament", "find my mp",
            "my councillor", "local councillor", "who is my councillor", "find my councillor",
            "my ward"),
           ("who", "which", "find", "look up", "contact", "email", "written to", "get hold of",
            "how do i", "how to")),
          "Put your postcode into the parliament.uk \"find your MP\" page, or theyworkforyou.com, "
          "and it gives the MP for your address with their email and constituency office. Your "
          "councillor for the ward is on your council's own site under your postcode, and they are "
          "the faster route for bins, housing and roads - the MP is for benefits, visas and "
          "anything a government department has to answer."),
    # The phrased copy of this row, and the one that answers: "how do i get proof of id",
    # "will they accept a council tax bill as proof" and "what counts as proof of address" all
    # reach it, where the broad row below reaches the list that office accepts but not the
    # question. It had the same id as the broad row - one id, two rows, which is a duplicate
    # entry and a red test - so it keeps its own name here and both shapes are left in place.
    entry("proof-of-address-phrased",
          (("proof of address", "proof of id", "utility bill", "bank statement",
            "proof i live", "proof of residency", "id documents", "prove my address",
            "prove the address", "prove your address"),
           ("get", "need", "needed", "how", "what", "accepted", "will they accept", "car",
            "passport", "licence", "rent", "council", "bank", "job", "school")),
          "Bank statements and utility bills count because they carry your name, address and a "
          "date, and most places want one from the last three months. A paper copy beats a phone "
          "screenshot. If everything is in someone else's name, ask the council for a council tax "
          "letter or order a certified copy of the electoral roll. Check the list that office "
          "accepts before you go.",
          avoid=("lost", "stolen", "renew", "renewal", "passport application", "visa",
                 "driving test", "pet", "dog", "cat",
                 # the broad row's guards, kept: a change of address, a redirect and a
                 # proofread are not this question
                 "change of address", "change my address", "update my address", "moving house",
                 "moved house", "redirect", "parcel", "delivery", "proofread", "homeless",
                 "no fixed", "ip address", "email address", "address book")),
    entry("proof-of-address",
          (("address", "proof", "statement", "bill"),
           ("proof", "prove", "proving", "address", "statement", "bill", "bank", "utility",
            "council tax", "tenancy", "letter", "show", "documents", "document", "need")),
          "For most things a bank statement, a utility bill or a council tax bill from the last "
          "three months, with your name and the address on it, is exactly what they want; a "
          "driving licence counts for some and not others, so ask which two they accept, and a "
          "paper copy beats a phone screenshot. If nothing is in your own name, ask the council "
          "for your entry on the electoral roll, or your GP or landlord for a letter on headed "
          "paper.",
          # "how do i get a statement from my bank" wants the bank's own app, not the list of
          # things that count as proof: the gate asks for the proof words.
          ask=("proof", "proofs", "prove", "proving", "proven", "address", "addresses", "id",
               "identification", "documents", "document", "counts as", "count as", "accepted"),
          avoid=("change of address", "change my address", "update my address", "moving house",
                 "moved house", "redirect", "parcel", "delivery", "proofread", "passport",
                 "visa", "homeless", "no fixed", "ip address", "email address", "address book")),
    # --- the paper chase: a claim, a complaint and the proof someone asks for ------------
    # These lines all named the thing they wanted and still got the shrug or the wrong answer:
    # "how do i claim on my insurance" got nothing, "how do i complain to the ombudsman" got
    # nothing, and "how long does a refund take" fell on the sale-refund rule about faulty goods.
    # A warranty claim is in `shopping.py` with the rest of the consumer-rights answers.
    # "how do i write a letter to the council" reached a "Citizens Advice covers this free"
    # line, and the pothole, the bin, the street light and the noise report are the commonest
    # letters people ever write: the department, the facts and the record are what get them
    # answered. The company complaint above stands down for a council on purpose, so this row is
    # the one home for a letter to the town hall.
    entry("write-to-the-council",
          (("council", "councils", "town hall", "local authority", "environmental health",
            "fly tipping", "fly-tipping", "fly tip", "fly-tip"),
           ("write", "writing", "letter", "email", "complain", "complaint", "report", "ask",
            "pothole", "potholes", "noise", "bin", "bins", "rubbish", "fly tipping", "fly-tipping",
            "graffiti", "street light", "streetlight", "pavement", "road", "damp", "housing",
            "how do i", "how to")),
          "Put it in writing to the right department and give them the facts they can act on: the "
          "address or street, the date, a photo or reference number, and what you want done - "
          "potholes and pavements to highways, noise, bins and fly-tipping to environmental "
          "health, a repair in a council house to the repairs line with your tenancy number. Use "
          "the online form or their email so there is a record, keep a copy and note the date. If "
          "nothing happens in ten working days, chase it and ask for it to be logged as a formal "
          "complaint; after their final reply the Local Government Ombudsman takes it on free.",
          # a council tax band, a blue badge and a school place are their own questions
          avoid=("council tax", "band", "council house", "council flat", "school place",
                 "school admission", "parking permit", "blue badge", "housing benefit",
                 "council tax reduction", "recycling", "what goes in",
                 # "how do i apply for a job at the council" was told to write about a pothole:
                 # a job with the council is work's question, not the town hall letter
                 "job", "jobs", "job at", "apply", "applying", "application", "vacancy",
                 "vacancies", "interview", "career", "salary", "person specification")),
    # The MP's letter is a different ask: not the department that fixes the pothole but the
    # person who can chase a department for you, and people write it about benefits,
    # immigration, HMRC and the council. Keyed on the member rather than on any one problem.
    entry("write-to-your-mp",
          (("mp", "my mp", "mps", "member of parliament", "house of commons", "constituency"),
           ("write", "writing", "letter", "email", "contact", "ask", "complain", "help",
            "how do i", "how to")),
          "Write to your MP with your full name and address so they can see you are their "
          "constituent, and say what you want them to do: the problem in two or three lines, the "
          "reference numbers, and what you have already tried. Email the constituency office or "
          "write to the House of Commons - both work, and a letter is kept on file. They can "
          "chase a government department, HMRC, the Home Office or the council, and they usually "
          "reply in a few weeks; for bins, housing and roads your councillor is the faster route.",
          # a political question is not a letter, and the voting facts have their own entry
          avoid=("election", "elections", "vote", "voting", "party", "prime minister", "tory",
                 "labour", "lib dem", "green party", "who is my mp", "what does my mp do",
                 # naming the member is the write-to-them row; finding out who it is is the
                 # postcode check below
                 "find my mp", "find your mp", "look up my mp", "mp for my")),
    # "who is my mp" cannot be answered from memory - it depends on where the person lives - but
    # the checker can, and pointing at it with the postcode is the honest answer.
    entry("find-your-mp",
          (("my mp", "who is my mp", "mp for", "my member of parliament", "find my mp"),
           ("who", "which", "find", "look up", "contact", "email")),
          "Put your postcode into the parliament.uk \"find your MP\" page, or theyworkforyou.com, "
          "and it gives the MP for your address with their email and constituency office. Their "
          "contact details are also on the council's website, and a library or Citizens Advice "
          "will look it up if you would rather ask someone."),

    entry("self-assessment-tax",
          (("self assessment", "tax return", "self employed", "sole trader", "freelance",
            "side income", "side hustle", "hmrc",
            # "how do i sort out my taxes" names the thing to be done, not the form: without
            # these the line scored nothing and got a hedge, and "council tax" is in the avoid
            # list below, so the words "tax" and "taxes" only ever mean income tax here
            "tax", "taxes", "my taxes", "income tax", "pay tax", "tax bill", "tax form",
            # the money from the second job is the ordinary way people name undeclared
            # income: "i owe tax on a side job", "i need to declare extra income" and "i do a
            # bit of cash in hand" named no row at all, or named the contract one.
            "side job", "side jobs", "extra income", "extra earnings", "cash in hand",
            "cash jobs", "undeclared income", "a bit of cash"),
           ("how", "fill", "file", "filing", "do", "deadline", "when", "pay", "owe", "register",
            "sort out", "first time", "start", "started", "quarterly", "records", "receipts",
            "declare", "declaring", "declaration", "undeclared", "declare it")
           + IMPROVE),
          "Register as self-employed with HMRC as soon as you start, then file online by 31 January "
          "after the tax year ends; the deadline to register the first time is 5 October. Keep "
          "every invoice and receipt as you go, because expenses cut the bill, and put a quarter of "
          "each payment aside so January is no surprise. Side income under £1,000 a year needs no "
          "return.",
          avoid=("student loan", "pension", "council tax", "benefits", "universal credit",
                 "vat", "dividend", "rent a room",
                 # a tax *code* is asking what the number on the payslip means, not how to
                 # register: "how do i check my tax code" was sent here to start a business
                 "tax code", "tax codes", "coding notice", "my code",
                 # "hmrc" is in the key because registering is the HMRC question, and that made
                 # "do i need to tell hmrc i moved house" a self-employment answer: a move is the
                 # address list's question, not a registration one.
                 "moved house", "moving house", "move house", "change of address",
                 "change my address", "changed my address", "new address", "tell hmrc i moved",
                 "update my address",
                 # a boss paying someone in cash is an employee paid off the books, not a sole
                 # trader: "my boss pays me cash in hand" is about the employer, and "register as
                 # self-employed" is the wrong instruction for them
                 "my boss", "the boss", "my employer", "my manager", "my company",
                 "pays me", "paid me", "pays my", "paid my", "pays us", "paid us",
                 # and the other side of the same coin: someone asking whether they may pay
                 # their staff that way is asking about the employment, not about registering
                 "pay someone", "paying someone", "pay staff", "paying staff", "pay my staff",
                 "pay them cash", "paying cash",
                 # the tax paid on savings is the savings card's, not a registration: "tax" and
                 # "pay tax" are in the key above so that "how do i sort out my taxes" reaches
                 # this row, and that also pulled "should i pay tax on my savings" off the
                 # personal savings allowance and onto self-assessment, where it has no answer
                 "savings", "my savings", "savings account", "savings interest", "tax on savings",
                 "on my savings", "interest on", "premium bonds", "isa", "cash isa",
                 "stocks and shares",
                 # a tax code is a question about the code, not about registering: "how do i
                 # check my tax code" was told to register as self-employed, because "tax" is in
                 # the key above and "check" is one of its question words
                 "tax code", "tax codes", "coding notice", "tax-code", "1257l",
                 # A gift and the tax on it is not income the person earned: "should i pay tax
                 # on a birthday present" and "do i need to declare a gift to hmrc" were both
                 # sent here to register as self-employed. The gift card in money.py answers them.
                 "gift", "gifts", "gifted", "cash gift", "money gift", "gift of money",
                 "birthday present", "7 year rule", "seven year rule",
                 # "tax" and "taxes" are in the key, so the purpose of tax and a tax explained
                 # to a child both came here and were told to register with HMRC: neither is a
                 # form to fill in, and `what-tax-pays-for` answers them
                 "explain", "explain tax", "explain taxes", "explain income tax",
                 "to my kid", "to my child", "to a child", "to my teenager", "to a teenager",
                 "why do we have", "why do we pay", "what is the point of", "whats the point of",
                 "what do taxes pay for", "what does tax pay for", "where does my tax go",
                 "what is tax", "whats tax", "what are taxes")),
    # The purpose of tax, and tax explained to a child or a teenager. Both are everyday asks
    # that reached the self-employment registration, which is a form to fill in and answers
    # neither question.
    entry("what-tax-pays-for",
          (("tax", "taxes", "income tax", "taxation"),
           ("what is the point", "whats the point", "why do we have", "why do we pay",
            "what does it pay for", "what do taxes pay for", "where does my tax go",
            "what is tax", "whats tax", "what are taxes", "explain", "explain tax",
            "explain taxes", "to my kid", "to my child", "to a child", "to my teenager",
            "to a teenager", "for a kid", "for kids")),
          ("Income tax and national insurance pay for the things nobody can buy alone: the NHS, "
           "schools, roads, the state pension, the police, and benefits for people who cannot "
           "work. It comes out of your pay before you see it, in bands: the first £12,570 a "
           "year is tax free, then 20p in the pound up to £50,270 and 40p above that. For a "
           "child: everyone chips in a little so the hospitals and roads work for all of us."),
          # a tax return, a refund, council tax and a tax code are the other questions, and a
          # tax on a product is shopping's
          avoid=("return", "self assessment", "refund", "rebate", "council tax", "tax code",
                 "hmrc", "owe", "overdue", "late", "penalty", "vat", "stamp duty", "savings",
                 "dividend", "pension", "vehicle tax", "road tax")),
    entry("standing-order",
          (("standing order", "direct debit", "recurring payment", "monthly payment",
            "automatic payment"),
           ("set up", "cancel", "stop", "block", "how", "difference", "what is", "between",
            "wrong", "taken", "missing", "returned")),
          "A standing order is yours: a fixed amount on a fixed date, set up and cancelled in your "
          "banking app, and the payee cannot create one. A direct debit is the other way round - "
          "you give permission and the company takes what it has told you it will, and the Direct "
          "Debit Guarantee means the bank must refund an unauthorised one in full. To stop one, "
          "tell the bank and the company.",
          avoid=("rent", "landlord", "mortgage", "salary", "wage", "bill too high", "went up",
                 "overcharged", "scam", "fraud",
                 # "how do i set up a direct debit" was answered with the standing-order card,
                 # which compares the two and never says how to start one. The direct-debit row
                 # in money.py does, so the how-to phrases stand this row down.
                 "set up a direct debit", "set up the direct debit", "set up my direct debit",
                 "set up a dd", "start a direct debit", "start the direct debit")),
    entry("house-sale-time",
          (("house sale", "sell my house", "selling my house", "sell a house", "selling a house",
            "sell the house", "selling a flat", "sell a flat", "selling the flat",
            "house buying", "buying a house", "buying my first flat", "house purchase",
            "purchase of a house", "completion", "chain",
            "solicitor", "conveyancing",
            # The week that matters is exchange to completion, and asking about it named neither
            # "house" nor "sale": "when do we exchange contracts" was a search hedge, "when will
            # we complete" the same, and "when do we get the keys" was the sport row asking for a
            # date. Every one of these is the sale, so they are the row's own words now.
            "exchange contracts", "exchange of contracts", "contracts exchanged",
            "exchange and completion", "exchange date", "completion date",
            "when do we exchange", "when will we exchange", "when we exchange",
            "after exchange", "before exchange", "on exchange",
            "when do we complete", "when will we complete", "when we complete",
            "complete on the house", "complete on the flat", "completion statement",
            "get the keys", "get my keys", "get our keys", "keys to the house",
            "keys to the flat", "house keys",
            "move in date", "moving in date"),
           ("how long", "how many weeks", "how many months", "time", "take", "takes", "wait",
            "when", "slow", "stuck", "delayed", "months", "weeks", "same day", "same week",
            "exchange date", "completion date")),
          "From an accepted offer, eight to twelve weeks is normal, and a chain adds a few weeks "
          "per link. Searches and the freeholder's pack are what drag, not the mortgage offer, so "
          "ask the solicitor how the searches are going and agree a target completion date in "
          "writing. Nobody is bound until contracts are exchanged, so do not hand in notice on a "
          "rented place, and budget for the survey, legal fees and stamp duty.",
          avoid=("rent", "renting", "tenancy", "landlord", "council tax", "mortgage rate",
                 "how much", "price", "worth", "stamp duty", "declutter", "packing",
                 # "do i need a survey when buying a house" is the survey's own card: the one
                 # word "when" in this row's ask list was enough to answer it with a timeline
                 "survey", "surveys", "surveyor", "surveyors", "valuation", "snagging",
                 # Backing out is not a question about how long the week is: "can the seller pull
                 # out after exchange" and "can they change their mind after exchange" want to
                 # know what binds them, and the timeline answered neither. `house-sale-binding`
                 # owns those words now, so this row stands down on them.
                 "pull out", "pulls out", "back out", "backs out", "change their mind",
                 "changes their mind", "changed their mind", "gazump", "gazumping",
                 "gazumped", "legally bound", "binding")),
    # Whether anyone can still walk away is a different question from how many weeks the week
    # takes, and it is the one people actually ask at the worst moment: "can the seller pull out
    # after exchange", "can they change their mind after exchange", "what happens if the seller
    # pulls out". The answer is the exchange, so the row is keyed on the backing out and on the
    # sale, and the timeline keeps every question that is only about time.
    entry("house-sale-binding",
          (("pull out", "pulls out", "pulling out", "back out", "backs out", "backing out",
            "change their mind", "changes their mind", "changed their mind", "changing their mind",
            "gazump", "gazumped", "gazumping", "walk away", "legally bound", "binding"),
           ("sale", "sale agreed", "house", "flat", "property", "offer", "offer accepted",
            "exchange", "exchanged", "contracts", "contract", "completion", "deposit",
            "buying a house", "seller", "buyer")),
          "Exchange is the moment the sale becomes legally binding: after that neither side can "
          "simply walk away, and if the seller refuses "
          "to complete you can sue for the deposit back and your costs, or press for the sale to go "
          "through. Before exchange either of you can pull out for any reason and owes nothing but "
          "their own legal fees - which is exactly the window a seller uses to take a better offer, "
          "and that is gazumping. So the practical answer is to push to exchange as soon as the "
          "searches are back, and to keep the deposit small until then.",
          avoid=("how long", "how many weeks", "how many months", "how soon", "weeks", "months",
                 "how much", "price", "worth", "survey", "surveyor", "packing", "declutter",
                 "rent", "renting", "tenancy", "landlord", "council tax", "mortgage rate")),
    # "how do i budget" and "how do i read my payslip" are `money.py`'s: a budget split and the
    # "how do i budget" and "how do i read my payslip" are `money.py`'s: a budget split and the
    # three payslip lines are already answered there, and a second copy here would fight them.
    # The alarm a person wears is not the alarm on a phone: "how much do those pendant alarms
    # cost" was answered by the snooze entry ("put the alarm across the room"), which is the wrong
    # answer to a question about a falls alarm and the money for it. The part words are only the
    # worn kind, so an alarm clock, a smoke alarm and a car alarm stay with their own answers.
    entry("pendant-alarm-cost",
          (("pendant alarm", "pendant alarms", "personal alarm", "personal alarms", "telecare",
            "lifeline", "careline", "panic alarm", "panic button", "falls alarm",
            "care alarm", "alarm pendant", "alarm for my mum", "alarm for my dad",
            "alarm for my mother", "alarm for my father", "wandering alarm"),
           ("cost", "costs", "how much", "price", "prices", "cheap", "cheapest", "month",
            "monthly", "a week", "rent", "renting", "hire", "buy", "buying", "worth it",
            "subscription", "pay", "paying", "free", "grant")),
          "Buying one is about £50 to £150, then £5 to £15 a month for the monitoring; renting is "
          "usually £10 to £20 a month with nothing up front. Ring adult social care at the council "
          "before you buy anything: most run a telecare service (Lifeline, Careline) from about £3 "
          "to £7 a week, and a falls assessment can bring that down or make it free. Ask about a "
          "key safe too.",
          # "put the alarm across the room" is the snooze entry's and it keys on the same bare
          # word, so the care alarm has to outscore it rather than push it away: the snooze entry
          # answers a plain "how much is a smoke alarm" too, and that line is not this one.
          bias=2),
    # The question people ask before the price: whether to get one at all. It is the same family
    # of words, and without a row it was the search hedge, so it answers the decision and leaves
    # the prices to `pendant-alarm-cost`.
    #
    # "they", not "she": the line may name a mum, a dad or a nan, and the row cannot tell which.
    entry("pendant-alarm-worth-it",
          (("pendant alarm", "personal alarm", "telecare", "lifeline", "careline", "panic alarm",
            "panic button", "falls alarm", "care alarm", "alarm pendant",
            "alarm for my mum", "alarm for my dad", "alarm for my mother",
            "alarm for my father", "wandering alarm"),
           ("should we get", "should i get", "get her", "get him", "get my mum", "get my dad",
            "do we need", "does she need", "does he need", "worth getting", "any good",
            "good idea", "recommend", "sensible", "help her", "help him", "keep her safe",
            "keep him safe", "safer", "better than")),
          "Ring adult social care at the council first: most run a telecare service for about £3 a "
           "week, and a falls assessment can bring the price down or make it free. Ask for that "
           "assessment as well, because grab rails by the stairs, a key safe for the ambulance crew "
           "and a strength and balance class prevent more falls than an alarm catches. The pendant "
           "only helps if it is worn, day and night, and if someone rings back when it goes off, so "
           "check who answers before you choose one.",
          bias=2),
    # --- a card that will not pay -------------------------------------------
    entry("card-wont-pay",
          # Not the word "declined": main's card-declined entry answers that one, and this row
          # is for the lines it does not reach - a card that will not go through, a card the
          # bank has frozen. The bank-card phrases, not the bare word: a memory card, a gift
          # card and a library card all stop working, and none of them wants the bank's number.
          (("bank card", "debit card", "credit card", "my card", "card payment",
            "card at the till", "card was", "card got", "card keeps", "card is",
            "card wouldn't", "card wont", "card won't"),
           ("frozen", "not working", "doesn't work", "doesnt work", "keeps failing",
            "wouldn't go through", "wont go through", "won't go through", "being held",
            "on hold", "declined again")),
          "Open the bank's app before you argue at the till: a block for an unusual payment is the "
          "usual cause and you can lift it there, and you can check the balance and the daily "
          "limit while you are in. If the app shows nothing, ring the number on the back of the "
          "card - a fraud review only they can clear. Carry a second way to pay while it is "
          "sorted.",
          avoid=("lost", "stolen", "difference", "maxed", "pay off", "interest", "abroad",
                 "holiday", "travel", "memory", "sd", "sim", "gift", "loyalty", "library",
                 "membership", "business card", "card machine", "playing card", "id card",
                 "key card", "birthday", "christmas", "nintendo", "console",
                 "declined", "rejected")),

    # --- one form, one office, one deadline --------------------------------------------
    # "how do i get a passport urgently" and "how do i register as self employed" were both
    # shrugs on main, and "how do i appeal a benefit decision" was answered by the how-to-claim
    # entry, which sends a person who has already been refused back to the form they filled in.
    entry("passport-fast-track",
          ("passport", ("urgent", "urgently", "fast", "fast track", "fast-track", "quick",
                        "quicker", "this week", "next week", "in a hurry", "premium",
                        "same day", "expedite")),
          "The one-week Fast Track service is the usual answer: apply online and pay the extra for "
          "the faster service, or book a Premium appointment at a passport office for a decision "
          "the same day, which costs more again. Both want your old passport and a photo, and the "
          "appointment wants proof of the travel date. Check the fee on the passport site first.",
          avoid=("lost", "stolen", "child", "baby", "renew", "expire", "how long", "visa",
                 "driving licence")),
    entry("register-self-employed",
          (("self employed", "self-employed", "sole trader", "freelance", "freelancer",
            "freelancing", "start my own business", "go it alone", "hmrc", "utr"),
           ("register", "registering", "registration", "how do i", "how to", "tell hmrc",
            "start", "starting", "set up", "deadline", "when")),
          "Register as a sole trader with HMRC once you start trading, and at the latest by 5 "
          "October after the end of your first tax year. Do it online at gov.uk: HMRC posts a UTR "
          "number, which every tax return and invoice needs. Then file by 31 January and pay Class "
          "2 and Class 4 National Insurance through the return.",
          # a limited company and a VAT registration are different forms, and paying yourself
          # from a company is not the sole-trader question
          avoid=("limited company", "ltd", "vat", "paye", "payroll", "employees", "hiring",
                 "pension", "invoices", "tax return", "self assessment", "self-assessment",
                 "how much tax", "national insurance", "hobby", "side hustle", "dividend",
                 "dividends", "company car", "expenses",
                 # "tell hmrc" is in the key because registering is a thing you tell HMRC, and
                 # that made "do i need to tell hmrc i moved house" a sole-trader answer: a move
                 # is the address list's question.
                 "moved house", "moving house", "move house", "change of address",
                 "change my address", "changed my address", "new address", "update my address")),
    entry("benefit-decision-appeal",
          # "frozen" is how people say a benefit stopped paying: "my tax credits got frozen"
          # reached a gadget card, because the one verb in the line was the freezer's.
          (("appeal", "appeals", "appealing", "challenge", "mandatory reconsideration",
            "reconsideration", "tribunal", "decision", "stopped", "cut off", "suspended",
            "sanction", "frozen", "froze", "froze my", "underpaid", "overpaid",
            "reduced", "cut my", "cut", "lowered", "stopped paying"),
           # tax credits are a benefit paid through HMRC's systems, and the person holding the
           # letter asks the same question as a universal credit one. They were missing from this
           # group, so "my tax credits have been stopped" was a Citizens Advice hedge.
           ("benefit", "benefits", "universal credit", "pip", "esa", "decision", "letter",
            "turned down", "refused", "rejected", "sanction", "sanctioned", "award",
            "tax credit", "tax credits", "child tax credit", "working tax credit",
            "tax credit award")),
          "Ask for a mandatory reconsideration within one month of the decision letter: ring the "
          "number on it, then put the request in writing and ask for the statement of reasons and "
          "the evidence used. Add a letter from your GP, employer or landlord if it helps. If "
          "it is still wrong, appeal to the tribunal within one month of the reconsideration "
          "notice - it is free, and you can ask for a phone hearing.",
          # claiming for the first time, and a benefit that was stopped, are other lines
          avoid=("how do i claim", "how to claim", "claim benefits", "claiming benefits",
                 "apply for benefits", "am i entitled", "do i qualify", "how much",
                 "child benefit", "how do i stop", "stop my", "cancel my",
                 "stopped claiming", "rent", "council tax", "housing", "school appeal",
                 "parking", "ticket", "planning", "immigration", "visa", "grade", "exam",
                 # an appeal against a tax decision is HMRC's, not the benefits one. Written as
                 # the taxes themselves: a bare "tax" also threw out "my tax credits got frozen",
                 # which is the benefits row's own question.
                 "hmrc", "self assessment", "self-assessment", "tax return",
                 # not "taxed": the avoid matcher stems it to "tax", so it stood down every
                 # line that says "tax credits" as well. A line with no benefit in it cannot
                 # reach this row anyway - the second key group has to match too.
                 "income tax", "tax bill", "tax code", "paye", "vat",
                 "corporation tax", "capital gains", "inheritance tax", "tax year",
                 "tax rebate", "tax refund", "p60", "p45")),
    # "the amount is wrong" is the same question as "it was stopped", and it needs its own row:
    # "wrong" is also how people describe a letter ("i sent the wrong letter", "the date on the
    # letter is wrong"), so it cannot sit in the row above, whose subject group holds "letter"
    # and "decision". Here the subject group is only the benefits themselves.
    entry("benefit-award-wrong",
          (("wrong", "incorrect", "miscalculated", "miscalculation", "not right"),
           ("benefit", "benefits", "universal credit", "pip", "esa", "tax credit", "tax credits",
            "child tax credit", "working tax credit", "tax credit award", "award")),
          "Ask for a mandatory reconsideration within one month of the decision letter: ring the "
          "number on it, then put the request in writing and ask for the statement of reasons and "
          "the evidence used. Add a letter from your GP, employer or landlord if it helps. If "
          "it is still wrong, appeal to the tribunal within one month of the reconsideration "
          "notice - it is free, and you can ask for a phone hearing.",
          avoid=("letter", "letters", "rent", "council tax", "housing", "parking",
                 "ticket", "immigration", "visa")),
    # A late return is not a parcel coming back: "my tax return is late" was answered with the
    # order-not-arrived card ("contact the seller first rather than the courier"), because
    # "return" and "late" are both in that entry's key. The two words that make it a tax line are
    # the ones this row keys, and the penalty dates are what the person is actually asking about.
    entry("tax-return-late",
          (("tax return", "tax returns", "self assessment", "self assessment tax",
            "self-assessment", "my taxes", "hmrc"),
           ("late", "overdue", "missed the deadline", "missed the date", "deadline passed",
            "miss the deadline", "miss the date", "missed the cut off", "still not filed",
            "late filing", "filed late", "what happens if", "what happens now",
            "havent filed it yet", "haven't filed it yet")),
          "File it now, even if you cannot pay: the \u00a3100 penalty for being a day late is charged "
          "whatever you do next, and it grows from there - \u00a310 a day after three months, then "
          "5% of the tax or \u00a3300 at six months and again at twelve - so the sooner it is in the "
          "smaller the bill. Interest runs on any tax unpaid after the deadline. If you cannot pay "
          "it, ring HMRC and ask for time to pay: a payment plan is agreed over the phone and it "
          "stops the collection letters.",
          # the parcel that comes back and the refund are the shop's question, and a tax credit
          # renewal is a benefits one
          avoid=("parcel", "parcels", "order", "orders", "delivery", "courier", "shop",
                 "seller", "amazon", "refund", "return it", "send it back", "tax credit",
                 "tax credits", "child benefit", "council tax", "parking")),
    # An appeal against a tax decision is HMRC's own two steps - a review, then the tribunal -
    # and it is not the benefits one: "how do i appeal a tax decision" was told to register as
    # self-employed, because "tax" reached that row and nothing claimed the appeal.
    entry("tax-decision-appeal",
          (("appeal", "appeals", "appealing", "appeal against", "challenge", "challenging",
            "dispute", "disputing"),
           ("tax", "taxes", "hmrc", "tax decision", "tax bill", "tax return", "penalty",
            "penalty notice", "fine", "self assessment", "self-assessment", "paye",
            "vat", "income tax", "late filing")),
          "Ask HMRC for a review first: within 30 days of the decision letter, write to the address "
          "on it saying you disagree and why, and include the figures, dates and any evidence - "
          "HMRC must look at it again and answer it in writing. If the review goes against you, "
          "appeal to the First-tier Tribunal (Tax) within 30 days of that answer: it is free, "
          "independent of HMRC, and most appeals are settled on the papers or by phone. Ask for "
          "the decision to be paused while you appeal so it is not collected in the meantime.",
          # a benefit appeal, a council tax appeal, a parking ticket and a planning application
          # all have their own steps, and the tax credit words keep the benefits rows first
          avoid=("benefit", "benefits", "universal credit", "pip", "esa", "tax credit",
                 "tax credits", "child benefit", "council tax", "parking", "ticket",
                 "planning", "visa", "immigration", "grade", "school", "exam", "housing")),
]

from .costs import time_entries
# A haircut is an appointment with a length, and life admin is where the appointments live.
ENTRIES += time_entries("haircut")

# "how do i complain about a builder" got a Citizens Advice hedge, and the entries that do handle
# a complaint are about one company (an energy supplier, a shop) or about whether to hire someone
# at all. A tradesperson who did a bad job is a shape of its own, and the steps are the same for
# every trade.
TRADE_NAMES = ("builder", "builders", "plumber", "plumbers", "electrician", "electricians",
               "roofer", "roofers", "decorator", "decorators", "painter", "painters",
               "plasterer", "plasterers", "tiler", "tilers", "joiner", "carpenter", "gardener",
               "landscaper", "handyman", "contractor", "tradesman", "tradesperson", "workman",
               "mechanic", "garage", "fitter", "installer")

ENTRIES.append(entry(
    "tradesperson-complaint",
    (TRADE_NAMES,
     ("complain", "complaint", "complain about", "bad job", "rubbish job", "poor job", "botched",
      "bodged", "cowboy", "cowboys", "unfinished", "never finished", "never came back",
      "wont come back", "won't come back", "took my money", "ripped me off", "rip off",
      "overcharged", "guarantee", "warranty", "not doing it", "wont fix", "won't fix",
      "refund", "small claims", "trading standards", "did a runner", "went bust",
      # the complaint is often just what the work looks like: a wall left in a state, a
      # plastered wall that is not flat
      # "how do i report a dodgy builder" is the same complaint in the plainest words: "report"
      # is how the question is put, and "dodgy" is what the work or the trader is called.
      "dodgy", "report", "reporting",
      "made a mess", "mess of", "terrible job", "awful job", "dreadful job", "badly",
      "uneven", "patchy", "streaky", "left a mess", "ruined", "came out wrong")),
    "Put it in writing before anything else: say what is wrong, what you want - it fixed, or your "
    "money back - and give a deadline of 14 days, by email so there is a record. If they are in a "
    "trade body, its free dispute service can step in; otherwise send a letter before action and "
    "use the small claims court, which is cheap and settles most of these. Photograph the work and "
    "keep the quotes, texts and receipts, and pay any balance on a card so the bank can help.",
    # whether to hire them, what a fair price is and how to find a good one are other questions,
    # and an energy supplier, a shop or a landlord is a complaint with its own answer
    avoid=("reputable", "trustworthy", "find a", "find me", "recommend", "recommendation", "best",
           "how much should", "how much does", "quote", "quotes", "price", "cheapest", "cheap",
           "energy", "supplier", "electricity", "gas bill", "broadband", "shop", "supermarket",
           "landlord", "letting agent", "council", "bank", "insurance", "airline", "holiday",
           "employer", "boss", "colleague",
           # choosing one is the other question, and "how do i avoid a cowboy builder" was
           # landing here on the word "cowboy": the picking answer ("written quote, proof of
           # insurance") is what that line wants, so this entry stands down for it.
           "avoid", "how do i check", "check a", "checking a", "choose", "choosing", "vet",
           "legit", "trustworthy", "what to ask",
           # and "how do i spot a cowboy builder" is asking the same picking question, which the
           # comment above already says: spotting one is how to avoid one
           "spot a", "spot one", "how do i spot", "how can i tell", "what should i ask",
           "before i hire", "before i pay",
           # "report" is also the document a trade sends you, so the senses that make it one
           # stand this entry down: a report card, an annual report, the report they wrote.
           "report card", "the report", "a report", "report says", "report shows", "report from",
           "annual report", "school report", "survey report", "written report")))

# "how long should i keep tax records" reached a Citizens Advice hedge, "how long do i keep
# payslips" the gross-and-net explanation and "how long do i keep my accounts" a punt: nothing
# owned the paper you keep after the work is done. The rule belongs to the record, not to the
# tax question, so one entry holds every kind of paper and names each in a clause of its own.
#
# The key needs a record word AND a keeping word, because "keep" on its own is a fridge
# question ("how long do i keep cooked rice") and "records" on its own is not one either.
_KEEP_PAPER = ("records", "record", "receipts", "receipt", "invoices", "invoice", "payslips",
               "payslip", "paperwork", "documents", "accounts", "bank statements", "statements",
               "wage slips", "p60", "p45", "p11d")
_KEEP_TIME = ("how long", "how many years", "keep", "keeping", "kept", "throw away", "throwing",
              "bin", "shred", "shredding", "get rid", "years", "dispose", "stop keeping")

ENTRIES.append(entry(
    "record-keeping",
    (_KEEP_PAPER, _KEEP_TIME),
    "Five years after the 31 January filing deadline is the rule for anything a tax return "
    "touches: keep the invoices, receipts and bank statements that long, and 6 years if you run "
    "a limited company. Keep payslips, contracts and pension letters for as long as you are in "
    "the job and a year after, keep a receipt while the guarantee or warranty still runs, and "
    "shred anything with your name, address or account number on it before it goes in the bin.",
    # where a record is made is another entry's question, and an item that goes off is a
    # freshness question with its own answer
    # a personal statement is a piece of writing, not a record to keep: "how long should a
    # personal statement be" was this card, which answers a length question about a tax return
    avoid=("personal statement", "personal statements", "ucas", "cv", "resume",
           "witness statement", "police", "statement to the", "insurance claim", "medical record",
           "school record", "criminal record", "record deal", "world record", "personal best",
           "keep a food diary", "keep a journal", "keep a diary", "keep a routine", "keep a habit",
           "keep a secret", "keep a promise", "keep the change", "keep a pet", "keep chickens",
           # keeping an account safe is the passwords answer, and this row answered it with how
           # long to keep tax paperwork because "accounts" is a paper word here
           "safe", "secure", "securely", "hacked", "hacker", "password", "passwords", "log in",
           "login", "sign in", "two factor", "2fa", "phishing", "online accounts",
           "keep bees", "keep a dog", "keep a cat", "keep a plant", "keep a houseplant",
           "keep leftovers", "keep cooked", "keep rice", "keep chicken", "keep eggs", "keep milk",
           "keep bread", "keep meat", "keep fish", "keep cheese", "keep wine", "keep beer",
           "keep fruit", "keep vegetables", "in the fridge", "in the freezer", "out of the fridge",
           "in the cupboard"),
    bias=1))


# "what is the difference between a will and probate" was a shrug, and the probate entry beside it
# only answers the timing ("how long does probate take"). What probate is, and why a will needs it,
# is a fact about the world and belongs here.
ENTRIES.append(entry(
    "what-probate-is",
    (("probate", "grant of probate", "letters of administration"),
     ("what is", "whats", "what are", "mean", "means", "explain", "difference", "differ",
      "vs", "versus", "do i need", "why do i need", "why is", "needed", "what does it do",
      "what does that mean", "tell me about")),
    "A will says who gets what; probate is the court's written confirmation that it was the last "
    "will and that the executor may act on it. You need it before selling or transferring a house, "
    "closing accounts and paying what the estate owes; banks pay out small balances without it, and "
    "anything held jointly or in trust usually passes without it. A straightforward estate gets the "
    "grant six to twelve weeks after the forms go in.",
    # the timing question, the funeral and the grieving are other answers
    avoid=("how long", "how many weeks", "how many months", "how soon", "waiting", "waited",
           "delay", "delayed", "funeral", "cremation", "burial", "ashes", "wake", "flowers",
           "sympathy", "condolence", "crying", "died", "death", "passed away"),
    # the word "will" alone is too common to key on, so this asks for probate first and a
    # question about it second, and the "will" in the line does the rest
    bias=1))

# Three money-and-law questions that got a hedge ("I'm not sure about that one") or a
# Citizens Advice number. Each is a settled procedure with a name, a cost and a wait, and a
# friend who has done it gives those three things first.
ENTRIES.append(entry(
    "power-of-attorney",
    (("power of attorney", "lasting power of attorney", "power of attourney", "lpa",
      "attorney", "deputyship", "deputy", "court of protection"),
     ("how do i", "set up", "setting up", "arrange", "apply", "application", "cost", "much",
      "need", "needed", "register", "registering", "what is", "who can", "when", "mental",
      "capacity", "dementia", "cant make decisions", "cannot make decisions", "stroke")),
    "There are two lasting powers of attorney and most people want both: one for money and "
    "property, one for health and welfare. They only work if the person makes and registers them "
    "while they can still follow what they are signing; each goes to the Office of the Public "
    "Guardian for about £82 and takes 8 to 12 weeks. If capacity has gone it is too late: the "
    "family must apply to the Court of Protection to be a deputy, which is slower and dearer.",
    avoid=("divorce", "custody", "child", "immigration", "visa", "criminal", "court date",
           "tribunal", "claim", "sue", "solicitor cost", "how much do solicitors"),
    ask=("how", "what", "set", "apply", "register", "cost", "need", "when", "who")))

ENTRIES.append(entry(
    "what-is-a-trust",
    (("trust", "trusts", "in trust", "will trust", "family trust", "trust fund",
      "trustee", "trustees"),
     ("what is", "what are", "what does", "do i need", "should i", "set up", "setting up",
      "how does", "worth it", "cost", "for my children", "inherit", "inheritance", "house",
      "money", "tax", "care fees", "avoid")),
    "A trust is a legal box: a trustee holds money or a house for someone else and must use it only "
    "for them. People use one to keep savings or a house out of inheritance tax or care fees, or to "
    "leave money to a disabled relative without handing it over. Most families do not need one, "
    "because a will can hold a child's inheritance in trust until 18 - and a trust costs money to "
    "set up and run, with its own tax return. Ask a solicitor for a fixed quote.",
    avoid=("trust me", "dont trust", "don't trust", "doesnt trust", "doesn't trust", "trust my",
           "trust him", "trust her", "trust them", "trustworthy", "can i trust", "should i trust",
           "trust a builder", "trust the", "national trust"),
    ask=("what", "how", "do", "should", "is", "worth", "set")))

ENTRIES.append(entry(
    "council-house",
    (("council house", "council flat", "council housing", "housing association",
      "social housing", "housing register", "homechoice", "choice based lettings",
      "council property"),
     ("how do i", "get one", "get a", "apply", "application", "waiting list", "how long",
      "bid", "bidding", "points", "band", "banding", "eligible", "qualify", "need one",
      "homeless", "evicted", "nowhere to live")),
    "You apply to the council where you live, not the one you would like to live in, and join "
    "its housing register: most run a website where you bid on the week's adverts, and offers go "
    "by band, meaning how urgent your need is, and then by how long you have waited. Most "
    "councils also want a local connection, which is living or working in the area or close "
    "family there, and the wait without priority is often years, so bid every week and keep the "
    "reference. If you are homeless tonight or have been asked to leave within 56 days, ring the "
    "council's housing options team the same day and say those words, because that duty is "
    "assessed straight away. A housing association's own list is a second, separate application "
    "worth making.",
    avoid=("buy", "buying", "mortgage", "rent", "renting privately", "landlord", "deposit",
           "sell", "selling", "price", "worth", "how much is", "council tax", "council flat on",
           "shared ownership"),
    ask=("how", "get", "apply", "waiting", "bid", "band", "eligible", "qualify", "need")))

# --- the end of a marriage ------------------------------------------------
# The procedure, not the decision. `thinking-about-divorce` in family.py answers the line that is
# still weighing it up, and it stands down for exactly these shapes by name ("divorce papers",
# "divorce form", "how much does", "cost of"), because a cost or a form is not a verdict. Nothing
# took them: "how do i get a divorce", "how much does a divorce cost", "how long does a divorce
# take", "can i get divorced without a lawyer" and "how do i start divorce proceedings" were all
# the search floor, and "how do i apply for a divorce online" was told to use a virtual card,
# because "online" plus "apply" is the card-safe row's shape.
ENTRIES.append(entry(
    "divorce-procedure",
    (("divorce", "divorced", "divorcing", "divorce papers", "divorce form", "divorce forms",
      "divorce application", "dissolution", "dissolve the marriage", "end the marriage legally"),
     ("how do i", "how to", "apply", "applying", "file", "filing", "start", "started",
      "how long", "take", "takes", "online", "form", "forms", "papers", "paperwork",
      "court", "process", "steps", "qualify", "separated", "separation", "begin", "begun")),
    ("In England and Wales you apply to the family court yourself, online, and you do not need a "
     "solicitor to do it: the application says the marriage has broken down and, since April "
     "2022, why is not asked. It costs \u00a3593, you can ask the court to make your ex pay half, "
     "and there is a discount if you are on a low income. Nothing happens quickly - 20 weeks "
     "after the application you can apply for the conditional order, then six weeks and a day "
     "later for the final order, so about seven months at the shortest. Deal with the money and "
     "the house in a separate financial order, because the divorce itself divides nothing, and "
     "get that agreed before the final order, not after. Scotland goes through the sheriff court "
     "and has a cheaper simplified divorce if there are no children under 16 and little to "
     "share."),
    ask=("how", "apply", "file", "start", "long", "online", "form", "papers", "paperwork",
         "court", "steps", "qualify"),
    # the decision to do it is the other row, and a person saying it out loud is not asking for
    # the form: "i want a divorce", "my wife wants a divorce", "should i get divorced" all stay
    # with `thinking-about-divorce` and the chat module
    avoid=("should i", "thinking about", "thinking of", "worth saving", "save my marriage",
           "unhappy", "not happy", "want a divorce", "wants a divorce", "wanted a divorce",
           "i want a divorce", "affair", "cheating", "cheated", "tell the kids", "tell our kids",
           "tell my children", "how do i tell", "how do we tell", "who gets the house",
           # the money is `divorce-cost`'s question, and it answers it with the budget a person
           # actually needs: this row says the fee and the discount and leaves the rest alone
           "how much", "cost", "costs", "fee", "fees", "cheaper", "cheapest", "afford",
           "solicitor", "lawyer", "legal aid",
           "custody", "child arrangements", "access", "prenup", "pre-nup", "pension",
           "settlement", "splitting the assets", "assets", "children", "kids",
           # an anniversary or a wedding is not the end of anything
           "anniversary", "wedding", "getting married", "engaged", "marry", "married"),
    bias=1))


# --- a message or an offer a person does not trust -----------------------------------------
# The commonest way of asking is the shortest: "is this a scam", "does this look like a scam",
# "i think this is a scam". All of those were a search hedge, because every scam row in the
# knowledge base is keyed on a medium - a call, a text, an email - and the line that names no
# medium had nothing to match. The medium rows answer "is this text a scam" well and keep it:
# this row stands down the moment one of those words is in the line.
# The answer is a move, not a description: check it through a route you found yourself, never
# through the number or link the message gave you, because a scam is a thing that works by
# being the only voice you hear. Then the three marks of one, and where to go once money is out.
# "con" is a word of its own only when it is the thing the person is asking about. It is also
# half of three ordinary phrases, and on main `ca53889` "is it cheaper to run a fan or the air con"
# was answered with this row: check it through a route you found yourself, and never through the
# number the message gave you. There was no message.
_CON_IS_ANOTHER_WORD = re.compile(
    r"\bair[\s-]?con(?:dition\w*|s)?\b"
    r"|\bcon\s+(?:carne|queso)\b"
    r"|\bpros (?:and|&) cons\b|\b(?:the )?cons? of\b|\bcons and pros\b"
    r"|\bcon\s?air\b|\bkitchen con\b", re.I)


def _con_is_the_question(understood):
    """False when "con" in the line belongs to air con, con carne or a list of pros and cons."""
    text = " ".join(str((understood or {}).get("clean") or "").lower().split())
    if not re.search(r"\bcons?\b|\bconned\b", text):
        return True
    if re.search(r"\bconned\b", text):
        return True
    return not _CON_IS_ANOTHER_WORD.search(text)


ENTRIES.append(entry(
    "check-a-scam",
    (("scam", "scams", "scammer", "scammers", "scamming", "scammed", "con", "cons", "conned",
      "con artist", "fraud", "fraudulent", "fraudster", "phishing", "fake", "faked",
      "dodgy", "suspicious", "too good to be true", "rip off", "rip-off", "ripped off",
      "legit", "legitimate", "genuine", "trustworthy", "trust"),
     ("is this", "is it", "is that", "this is", "that is", "looks like", "looked like",
      "sounds like", "sounds", "seems like", "seems", "think this", "think it is",
      "think its", "am i being", "how do i know", "how can i tell", "how to tell",
      "worried", "not sure if", "wondering if", "but it feels", "too good",
      "good to be true", "something off", "doesnt feel right", "does not feel right",
      "doesnt add up", "does not add up")),
    "Don't act on it yet: check it through a route you found yourself, the number on your card "
    "or bill or the company's own app, and never through a number or link the message gave you, "
    "because a scam works by being the only voice you hear. The marks of one are being hurried, "
    "being asked to keep it secret, and being asked to move money, read out a code, or pay in a "
    "way you would not normally use: a gift card, a payment app, or a transfer to a person. No "
    "real bank, tax office or courier asks for any of those. If you have already paid or given "
    "details, ring your bank the same day, because some transfers can be recalled and you are "
    "not in trouble; keep the message and report it to the fraud service for your country, or "
    "forward a suspicious text to 7726 in the UK.",
    # A named medium is a better question with its own answer - the bank call, the phishing
    # email, the text - and so is a parcel, a builder, a holiday or a job offer. A dish called
    # con carne is not a con.
    avoid=("call", "calls", "called", "ring", "rang", "ringing", "phone", "phoned",
           "text", "texts", "sms", "email", "emails", "message", "messages", "letter",
           "link", "attachment", "website", "site", "app", "marketplace", "ebay", "gumtree",
           "vinted", "facebook", "instagram", "whatsapp", "parcel", "delivery", "courier",
           "landlord", "builder", "roofer", "roof", "damp", "plumber", "trade", "tradesman",
           "holiday", "rental", "booking", "flight", "job", "job offer", "interview",
           "recruiter", "romance", "dating", "tinder", "investment", "invest", "crypto",
           "bitcoin", "pension", "energy", "supplier", "gym", "subscription", "insurance",
           "ticket", "fine", "tax rebate", "hmrc", "bank", "reader", "carne", "con queso",
           "sin carne", "dog", "puppy", "breeder", "mould", "mold", "washer", "boiler",
           # a counterfeit question is about a thing being real, not about money going out
           "authentic", "authenticity", "counterfeit", "rolex", "designer", "handbag",
           "sneakers", "trainers", "gucci", "chanel", "omega",
           # a review that is fake is a shopping question about the reviews, not a scam message:
           # "how do i know if a review is fake" was answered with the scam card, because
           # "fake" is this row's word and "how do i know" is its other half
           "review", "reviews", "reviewer", "reviewers", "rating", "ratings", "stars"),
    bias=2,
    # the "con" in "air con" is a cooler, not a swindle
    guard=_con_is_the_question))
# After the money has gone the question is not "is this a scam", it is "what do I do now", and
# nothing answered it. On main `ca53889` a person saying "i think ive been conned" was told
# "Good to hear. What was the best bit?", and "i got scammed" and "my mum got scammed" were both
# "Ugh, that's a lot to carry" - a chat reflection in the one moment a person needs the phone
# number of their bank. The move comes first: call the bank today, on the number on the card.
_SOMEONE_ELSE_WAS_SCAMMED = re.compile(
    r"\bmy (?:mum|mom|dad|nan|gran|grandma|grandad|grandpa|brother|sister|son|daughter|"
    r"husband|wife|partner|friend|neighbour|neighbor|aunt|uncle|mother|father)\b"
    r"|\b(?:he|she|they) (?:was|were|got|has been|have been)\b", re.I)


def _scammed_already(memory, understood):
    """Whoever was caught out is the one who rings the bank, and the card says whose phone call
    it is: "i got scammed" is the person's own bank, "my mum got scammed" is hers."""
    clean = str((understood or {}).get("clean") or "")
    if _SOMEONE_ELSE_WAS_SCAMMED.search(clean):
        return ("Get them to ring their bank today, on the number on the back of their card, and "
                "say it was a scam: a transfer can sometimes be stopped or recalled, and nobody "
                "is in trouble for reporting it. Report it as well - Action Fraud in the UK, or "
                "your country's fraud service - and keep every message, number and receipt, "
                "because the report needs them. Then change the password on any account they "
                "touched, and expect a follow-up call from someone pretending to be the bank: no "
                "real bank asks for a code, a password or a transfer, so hang up and ring back on "
                "the number they already know.")
    return ("Ring your bank today, on the number on the back of your card, and tell them it was a "
            "scam: a transfer can sometimes be stopped or recalled, and you are not in trouble "
            "for reporting it. Then report it - Action Fraud in the UK, or your country's fraud "
            "service - and keep every message, number and receipt, because the report needs them. "
            "Change the password on any account they touched, and expect a follow-up call from "
            "someone pretending to be the bank: no real bank asks for a code, a password or a "
            "transfer, so hang up and ring back on the number you know.")


ENTRIES.append(entry(
    "scammed-already",
    (("conned", "scammed", "scam", "scams", "fraud", "fraudster", "ripped off", "ripoff",
      "took my money", "taken my money", "stole my money", "stolen my money",
      "money gone", "fake", "phishing"),
     # a line that says it has happened, in the words people use for it: the person is the
     # subject ("i got", "i was", "ive been") or a relative is ("my nan", "my dad")
     ("i got", "i was", "ive been", "i have been", "i think ive", "i think i have",
      "they took", "they have taken", "someone", "my mum", "my mom", "my dad", "my nan",
      "my gran", "my grandma", "my grandad", "my grandpa", "my brother", "my sister",
      "my son", "my daughter", "my husband", "my wife", "my partner", "my friend",
      "got done", "been had", "out of my account", "out of my bank")),
    _scammed_already,
    bias=1,
    # asking before anything has happened is `check-a-scam` and the medium rows, and a named
    # medium (a call, a text, a letter) has its own answer that is more use than this one
    avoid=("is this", "is it", "is that", "should i", "does this", "do you think", "worth it",
           "how do i know", "how can i tell", "before i", "would this", "might be", "could be",
           "looks like", "sounds like", "seems like", "not sure if", "worried",
           "phone", "called", "call", "text", "texts", "sms", "email", "emails", "message",
           "messages", "letter", "link", "website", "site", "app", "marketplace", "ebay",
           "gumtree", "facebook", "instagram", "whatsapp", "parcel", "courier", "builder",
           "roofer", "plumber", "landlord", "holiday", "booking", "job", "interview",
           "investment", "invest", "crypto", "bitcoin", "pension", "energy", "supplier",
           "insurance", "ticket", "fine", "hmrc", "tax rebate", "bank", "carne", "con queso")))


# A parcel going abroad is a customs form and a weight band, not a walk to the counter. On main
# `85d8420` "how do i send a parcel to spain" reached nothing at all, and "how much does it cost to
# post a parcel to spain" was answered with the daily budget for a holiday in Spain, because the
# destination row keys on a country and a cost and nothing in it knows what a parcel is.
POSTED_TO = ("spain", "france", "italy", "portugal", "germany", "netherlands", "ireland",
             "greece", "poland", "romania", "usa", "america", "canada", "australia",
             "new zealand", "japan", "china", "india", "pakistan", "bangladesh",
             "philippines", "nigeria", "kenya", "ghana", "south africa", "dubai", "uae",
             "brazil", "mexico", "turkey", "morocco", "egypt", "europe", "eu")

ENTRIES.append(entry(
    "parcel-abroad",
    (("parcel", "parcels", "package", "packages", "letter", "letters", "send", "sending",
      "sent", "post", "posting", "postage", "courier", "shipping",
      # the form itself is the question in "what do i write on a customs form", which has no
      # parcel word in it at all
      "customs form", "customs label", "cn22", "cn23", "fill in a customs", "customs declaration"),
     ("abroad", "overseas", "international", "customs", "customs label", "customs form",
      "cn22", "cn23", "declaration", "duty", "import tax", "outside the uk") + POSTED_TO),
    ("A letter or a card just needs the right stamp and the full address; a parcel needs a "
     "customs form, at the counter a CN22 (a CN23 once the value is over a few hundred pounds), "
     "naming what is inside, its weight and its value - "
     "that is what the receiving country works its duty and tax out from, so write the truth "
     "rather than gift. Price goes by weight band: a small parcel to Europe is roughly £10 to "
     "£20 and outside Europe more, so weigh it first and compare a courier once it is over 2kg. "
     "Nothing perishable, no loose lithium batteries by air, and alcohol and perfume only "
     "within the limits."),
    # money is not posted, and the UK post office questions have their own rows
    avoid=("money", "cash", "transfer", "bank", "euros", "dollars", "refund", "return",
           "returns", "tracking", "track", "how long", "days", "lost", "missing", "damaged",
           "email", "text", "message", "whatsapp", "invoice", "tax return")))


# --- the words on a will, a deed and a court form ------------------------------
# A dozen words a person meets once, in a letter or a solicitor's email, all of which were the
# honest pass on main ("what is an executor", "what is a deed poll", "what is a statutory
# declaration"), and one of which was worse: "what is a county court judgment" was answered by the
# bailiff card, which is what happens *after* one. Each row defines the word in its first sentence
# and says what it means for the person reading the letter, which is the whole of what is safe to
# say without knowing their case. The keys are the words; the ask is the definition shape only, so
# "how do i get probate" and "how do i change my name" keep their own answers.
_LEGAL_WORDS = (
    (("intestate", "intestacy", "died intestate", "dies intestate",
      # "who inherits if there is no will" names the situation rather than the word, and the
      # answer is the same one: the law's fixed shares.
      "no will", "without a will", "died without a will"),
     "If someone dies intestate they died without a valid will, so the law decides who gets what. In "
     "England and Wales a spouse or civil partner gets the personal possessions and the first "
     "£322,000, with the rest shared with the children; partners who were not married get nothing "
     "without a will. The court appoints an administrator where a will would have named an executor."),
    # The paper that says what the rent is and who fixes the boiler. lifeadmin already answers
    # "can i get a copy of my tenancy agreement" and the early-exit question, and neither of them
    # is what a person asking "what is a tenancy agreement" wants.
    (("tenancy agreement", "tenancy contract", "renting agreement", "assured shorthold",
      "ast tenancy", "shorthold tenancy"),
     "A tenancy agreement is the contract between you and the landlord: it sets the rent, how "
     "long the tenancy runs, who pays which bills, who repairs what, and whether you can have a "
     "pet or sublet. An assured shorthold tenancy is the ordinary kind for a private renter in "
     "England - a fixed term (often 12 months) and then a rolling monthly one - and since 2019 "
     "the landlord must give you the government's How to Rent guide and a current gas safety "
     "certificate before you move in. It is a contract, so read the clauses on repairs and "
     "notice before you sign, and keep a copy: the landlord has to provide one."),
    # "will" alone is the auxiliary verb in "what will the weather be like", so the noun is keyed
    # as the phrases it appears in; the plural "wills" is safe on its own.
    (("a will", "the will", "my will", "his will", "her will", "their will", "your will",
      "last will", "last will and testament", "wills", "write a will", "make a will"),
     "A will says who gets what when you die, and who sorts it out - the executor. It only counts "
     "if it is signed and witnessed by two people who are not beneficiaries, and the last valid one "
     "wins, so tell the executor where it is kept. Without one the law shares the estate out by "
     "fixed rules, which may not be what you would choose."),
    (("executor", "executors", "executrix"),
     "An executor is the person named in a will to carry it out: register the death with the will, "
     "apply for probate, value the estate, pay the debts and inheritance tax, then share out what is "
     "left. You can be one without any legal training, and many people do it themselves; a "
     "solicitor is worth paying for if there is a house, a business or a disagreement."),
    (("beneficiary", "beneficiaries"),
     "A beneficiary is a person or an organisation named to receive something - in a will, an "
     "insurance policy or a pension. Being named in a will does not override a pension or insurance "
     "form, so the nomination held by the pension firm is what pays out, and it is worth checking "
     "after a divorce or a death."),
    (("next of kin",),
     "Next of kin means your nearest relative, and hospitals and banks ask for it as the person to "
     "ring. It does not give that person the right to make decisions for an adult: medical "
     "decisions are the doctor's with the patient, and money decisions need lasting power of "
     "attorney. A partner who is not married can be next of kin if you say so in writing."),
    (("deed poll", "change my name deed poll"),
     "A deed poll is the one-page document you sign to change your own name: it costs nothing to "
     "write yourself, and enrolling it with the Royal Courts of Justice for about £42 makes it "
     "easier for banks and passport offices to accept. You can use the new name straight away; the "
     "passport, driving licence and bank are the ones to change first."),
    (("statutory declaration", "statutory declarations"),
     "A statutory declaration is a written statement that you sign in front of a solicitor or a "
     "magistrate and swear is true - commonly used to prove a change of name, a lost document or a "
     "fact you cannot evidence another way. It is not free: a solicitor charges about £5 to £15 "
     "for the signature, and you need to take the wording with you."),
    (("solicitor", "solicitors", "lawyer", "lawyers"),
     "A solicitor is a lawyer who advises you and prepares the documents: a house purchase, a will, "
     "a dispute, a crime. In England and Wales they must be regulated by the SRA or the Law Society "
     "and carry insurance, which is what to check on the firm's number before you pay. The first "
     "appointment is often free, and a fixed fee is normal for a will or a conveyance."),
    (("ccj", "ccjs", "county court judgment", "county court judgements",
      "county court judgments"),
     "A CCJ is a county court judgment: a court has ruled that you owe someone money, and the "
     "judgment appears on your credit file for six years. Pay it in full within a month of the "
     "post arriving and you can ask the court to remove it; after that it is marked satisfied, "
     "which still shows. If you cannot pay, apply to the court to pay by instalments rather than "
     "ignore it, because ignoring it is what leads to bailiffs."),
    (("affidavit", "affidavits"),
     "An affidavit is a written statement of evidence that you swear in front of a solicitor or "
     "court officer. Most of the places that used to ask for one now accept a statement of truth, "
     "which you sign without the fee - so ask which one the form really wants before you pay for a "
     "signature."),
    (("notary", "notaries", "notary public"),
     "A notary public is a lawyer who certifies documents for use in another country: they check "
     "who you are, watch you sign, and seal it so the foreign authority accepts it. Banks and "
     "embassies abroad usually ask for it, it costs £50 to £150 a document, and a solicitor can "
     "find you one."),
    (("lien", "liens"),
     "A lien is a legal claim that a lender or a tradesman holds on your property until a debt is "
     "paid: a mortgage is a lien on the house, and a garage can keep your car until its bill is "
     "settled. It does not usually change who owns the thing, but it can stop a sale, so a letter "
     "mentioning one is worth answering."),
)
LEGAL_DEFINITION_ASKS = ("what", "whats", "what is", "what are", "mean", "means", "meaning",
                         "define", "definition", "explain", "called", "who inherits", "who gets",
                         "who gets what", "who inherits what")


def _legal_word(first=None, second=None):
    """The word the line asks about, defined in the first sentence.

    The reply is called with the reading and sometimes only with the memory, so whichever of the
    two carries the reading is the one read: a row that raises on the calling convention is a row
    that is never reached.
    """
    understood = None
    for candidate in (first, second):
        if isinstance(candidate, dict) and "words" in candidate:
            understood = candidate
        elif isinstance(candidate, dict) and isinstance(candidate.get("understood"), dict):
            understood = candidate["understood"]
    words = [str(word).lower() for word in ((understood or {}).get("words") or ())]
    text = " ".join(words)
    for keys, reply in _LEGAL_WORDS:
        for key in keys:
            if (" " in key and key in text) or key in words:
                return reply
    return None


ENTRIES.append(entry(
    "legal-word",
    (tuple(key for keys, _ in _LEGAL_WORDS for key in keys), LEGAL_DEFINITION_ASKS),
    _legal_word,
    bias=1,
    # a will that is being read out, a name change to ask about at the bank, and a lawyer in a
    # storyline are other answers; this row is only the meaning of the word
    avoid=("how do i", "how can i", "should i", "can i", "do i need", "help me", "what can i do",
           "free", "cheap", "cost", "costs", "price", "near me", "recommend",
           "film", "movie", "book", "series", "episode", "song", "game"),))
# "what should i check when viewing a flat" was a shrug on main, and "what questions should i ask
# when viewing a flat" was the job-interview card ("Ask what the first three months look like"),
# because "questions to ask" is the interview row's own phrase. A viewing is a body of advice
# nobody had written down, and it is the turn before a deposit is paid.
VIEWING_FLAT = (
    "A viewing is about what a photo hides. Press the wall behind the bed and under the window for "
    "damp, look at the ceiling for a brown ring, run the hot tap and time how long it takes, and "
    "ask how old the boiler is. Go back in the evening for noise and parking. Ask what the rent "
    "includes - bills, council tax, broadband - whether the deposit goes into a protection scheme, "
    "how long the tenancy runs and what the break clause says. Anything promised out loud, a "
    "repair or a new mattress, get it in a text or email before you pay.")
A_VIEWING = ("viewing", "viewings", "view a flat", "view the flat", "view a room",
             "view the house", "look round", "look around", "look at a room", "looking at a room",
             "looking at a flat", "looking round", "questions to ask", "what to check",
             "what to look for", "what should i look for",
             "what should i check", "before i move in", "before i sign", "room in a flatshare",
             "room in a house share", "before i pay the deposit")
NOT_A_VIEWING = (
    # a hotel, a car and a job have viewings and questions too, and none of them is a tenancy
    "hotel", "hotels", "holiday", "villa", "airbnb", "car", "cars", "van", "camper",
    "interview", "job", "jobs", "recruiter", "employer", "salary", "promotion",
    "tv", "telly", "viewing figures", "houseplant", "plants", "funeral", "wedding venue",
    "school", "nursery", "care home", "buy", "buying", "mortgage", "offer",
    # the deposit coming back is its own question, argued rather than checked
    "deposit back", "get my deposit back", "kept my deposit", "withheld",
    # "honest view?" after a landlord turn is somebody asking what I think, not a viewing:
    # the word "view" is both, and only the phrases below say which one it is
    "honest view", "your view", "my view", "point of view", "any views", "views on",
    "view of it", "view on it", "what do you think")
ENTRIES.append(entry(
    "viewing-a-flat",
    (A_VIEWING,
     ("flat", "flats", "room", "rooms", "house", "houses", "home", "property",
      "house share", "house-share", "flatshare", "place",
      "landlord", "letting agent", "letting agency", "agent", "tenant", "tenancy", "rent",
      "renting", "rented", "moving in", "move in", "move into")),
    VIEWING_FLAT,
    # the words are said either way round: "viewing a flat" and "flat viewing" both name it
    ask=("viewing", "viewings", "view", "look round", "look around", "check", "questions",
         "ask", "before i", "room in", "moving in", "move in"),
    avoid=NOT_A_VIEWING,
    bias=2))


# --- a pile of paperwork is a system, not a task -------------------------------------------
# "how do i sort out my paperwork" was "That's beyond what I know well": nothing in the base was
# about the pile itself, only about the particular letter in it.
ENTRIES.append(entry(
    "sorting-the-paperwork",
    (("paperwork", "documents", "papers", "receipts", "forms", "bills and letters",
      "pile of letters", "pile of post", "paper", "letters"),
     ("sort out", "sort", "sorting", "organise", "organize", "organising", "file", "filing",
      "shred", "keep", "keeping", "where to put", "what to do with", "pile", "piles",
      "mountain", "start", "system", "box", "folder")),
    "One folder or box for each thing you actually have to keep — tax, home, car, health — and one "
    "tray for this month. Open the post standing up, over the bin, and deal with each letter once: "
    "pay it, file it, or ring the number on it, because a second read is how the pile grows. Shred "
    "anything with your name and an account number on it. Bank statements, bills and payslips you "
    "can download do not need keeping; keep the last six months at most, and anything you have not "
    "needed for a year goes in a labelled box in the loft rather than the drawer.",
    # A named document has its own answer (the passport, the tax return, the P60, the MOT), and a
    # letter that needs a reply is the complaint's or the debt's, not the pile's.
    avoid=("passport", "birth certificate", "marriage certificate", "driving licence",
           "licence", "visa", "will", "probate", "tax return", "self assessment", "p45",
           "p60", "payslip", "payslips", "universal credit", "benefits", "council tax",
           "mot", "insurance claim", "claim", "complaint", "complaints", "final demand",
           "red letter", "debt", "bailiff", "court", "fine", "pc", "nip", "speeding",
           "ucas", "student loan", "school", "nursery", "cover letter", "cv", "job application",
           "post office", "postage", "stamp", "post a", "posting", "parcel", "parcels",
           "hoard", "hoarding", "never throw anything away", "shed", "loft is full")))

# --- the library ---------------------------------------------------------
# A library card is a card nobody thinks of as an account, so every question about it was read
# as something else: "does my library card need renewing" reached the opening-hours note,
# "how do i renew my library book" reached the subscription-cancellation card ("cancel from the
# place you pay"), "can i return a library book late" reached the parcel-return card, and
# "my library book is overdue" reached nothing at all. Four everyday errands are one subject
# here: joining and renewing the card, and borrowing, renewing and returning the books.
#
# The card and the loan are two rows because they answer different questions and a person asks
# for one of them: the card is about the person (join, renew, lost, the app), the loan is about
# the thing (how long, how many, renew it, overdue, the drop box). Each row stays away from the
# other's words as well as from the hours ask, which a map listing answers better than a card
# with no branch in it ever could.
ENTRIES.append(entry(
    "library-card",
    (("library card", "library membership", "library account", "library ticket",
      "join the library", "join a library", "library near", "my library", "the library",
      "public library", "libraries"),
     ("renew", "renewing", "renewal", "renewed", "expired", "expire", "expires", "run out",
      "ran out", "out of date", "out of date", "join", "joining", "sign up", "signed up",
      "get a card", "get one", "membership", "member", "lost", "misplaced", "stolen",
      "ebook", "ebooks", "e-book", "e-books", "audiobook", "audiobooks", "kindle",
      "app", "online", "register", "registering", "need to bring", "what do i need",
      "how do i get", "moved", "moving", "just moved", "new address",
      "new here", "proof of address", "no address", "from abroad", "temporary")),
    "Free to join: take the card or the form and something with your name and address on it - a "
    "bill, a driving licence, a bank statement - to any branch, or join on your council's library "
    "website and collect the card there. A card lapses after a year or two without use and "
    "renewing it is free at the desk or online; a lost one is a couple of pounds to replace. "
    "The same card gets you the ebooks and audiobooks, through the Libby or BorrowBox app with "
    "your card number and PIN, and nothing you borrow that way needs returning.",
    # The hours ask has an answer of its own that a library card cannot give, and a subscription
    # is the row that "renew" belongs to when the thing being renewed is paid for.
    avoid=("open", "opening", "hours", "opening hours", "opening times", "closed", "shut",
           "sunday", "bank holiday", "subscription", "netflix", "spotify", "disney",
           "amazon prime", "kindle unlimited", "audible", "gym", "gym membership", "insurance",
           "car", "parking", "council tax", "bin", "bins", "recycling", "tenancy", "passport",
           "driving licence renewal", "visa", "prescription", "book a", "booking", "hotel",
           "restaurant", "table", "flight", "train", "cinema", "doctor")))

# The loan is the other half of the same card: how long a book is kept, how many at once,
    # renewing it, and what happens when it is late. "Can i return a library book late" and "my
    # library book is overdue" are the most common of these and both used to reach a card about
    # parcels.
#
# One subject, several questions: how long a loan is, how many at once, how to reserve one,
# whether it can be renewed, what a late one costs and what a lost one costs. The single
# paragraph below answered all six with the first of them, so "how many books can i borrow"
# was told three weeks and "can i reserve a book" was told about fines. Each kind now gets the
# sentence it asked for, and the order of the readings matters: a renewing question that also
# says "how many times" is a renewal, not a count of books.
_LIBRARY_RENEW = re.compile(
    r"\brenew(?:s|ed|ing|al|als)?\b|\bextend(?:ed|ing)? (?:the |my )?(?:loan|borrowing|book)"
    r"|\bkeep (?:it|them) (?:for )?(?:another|longer)", re.I)
_LIBRARY_COUNT = re.compile(
    r"\bhow many\b|\bat (?:a|one) time\b|\bat once\b|\bhow many items\b", re.I)
_LIBRARY_RESERVE = re.compile(
    r"\breserv(?:e|es|ed|ing|ation|ations)\b|\brequest(?:s|ed|ing)?\b"
    r"|\bput (?:a|the|it) (?:on )?hold\b|\bon hold\b|\bwaiting list\b", re.I)
_LIBRARY_LOST = re.compile(
    r"\blost\b|\bcan'?t find\b|\bcannot find\b|\blose\b|\bdamag\w*\b|\bchewed\b"
    r"|\btorn\b|\btore\b|\bspill\w*\b|\bspilt\b|\bruined\b|\bsoaked\b|\bgot wet\b"
    r"|\bstained?\b|\bscribbl\w*\b|\bdropped it in\b|\bleft it on the (?:bus|train)", re.I)
_LIBRARY_LATE = re.compile(
    r"\boverdue\b|\blate\b|\bfines?\b|\bblocked\b|\bsuspended\b|\bcharged? (?:for|me)\b"
    r"|\bwhat happens if (?:it|its|it's) late\b", re.I)
_LIBRARY_RETURN = re.compile(
    r"\breturn(?:s|ed|ing)?\b|\bdrop (?:it |them )?(?:off|box)\b|\bletterbox\b"
    r"|\bafter hours\b|\boutside the branch\b", re.I)
_LIBRARY_HOW_LONG = re.compile(
    r"\bhow long\b|\bhow many (?:weeks|days)\b|\bdue back\b|\bwhen is it due\b"
    r"|\bhow much time\b", re.I)


def _the_library_loan(memory, reading):
    """The library's answer to the question the line asked about its loan.

    Six questions share one subject, and answering the wrong one is what this row did before:
    "how many books can i borrow from the library" got the loan length, and "can i reserve a
    book at the library" got the fines. The reading is the ask, in the order a person means it:
    renewing, then how many, then reserving, then a lost or damaged copy, then a late one, then
    returning it, and only then the length of the loan itself.
    """
    said = " %s " % " ".join(str(((reading or {}).get("clean")
                                or (reading or {}).get("text") or "")).lower().split())
    if _LIBRARY_RENEW.search(said):
        return (
            "Renew it online, in the library's app or by phone, before the date falls: most "
            "libraries allow two or three renewals unless somebody has reserved the book, and "
            "the renewal is what to try first because it costs nothing and stops a fine. Where "
            "the renewals have run out, ask at the desk - a librarian can usually override it "
            "for one more if nobody is waiting.")
    if _LIBRARY_COUNT.search(said):
        return (
            "About a dozen at a time at most libraries, twenty at the big city ones, and a "
            "child's card is usually half that - the number is on the card's page or at the "
            "desk, and it counts everything, so a DVD or a jigsaw uses one of the dozen. "
            "Reference books and anything in the local-history room never leave the building.")
    if _LIBRARY_RESERVE.search(said):
        return (
            "Reserve it from the library's own catalogue or at the desk and it comes to your "
            "branch when it is free - nothing at most libraries and a small charge at some. "
            "You get an email or a text when it arrives and a week or so to collect it, so "
            "choose the branch you actually use, and ask for a book that is on the shelf "
            "elsewhere in the county now rather than waiting for a copy to come back.")
    if _LIBRARY_LOST.search(said):
        return (
            "Tell the desk as soon as you know: a lost or damaged book is charged at the "
            "replacement price, not the cover price and not a fine, and staff can often renew "
            "it once more to give you time to find it. If it turns up, the charge is refunded "
            "at most libraries, and a book damaged by a child or a dog is the same conversation "
            "- say what happened, because a librarian decides, not a rule.")
    if _LIBRARY_LATE.search(said):
        return (
            "Renew it first, online or by phone, because that costs nothing and clears most of "
            "it. Where a book is late, most councils have dropped the daily fine altogether and "
            "simply block the card until it comes back; where there is one it is pennies a day "
            "and capped, and a child's card is never charged. Take it back and tell the desk - "
            "they can usually unfreeze the card there and then.")
    if _LIBRARY_RETURN.search(said):
        return (
            "Returns go in the drop box inside or outside the branch, so a book can go back at "
            "midnight, and the date it is checked in is the date it came back, not the date "
            "somebody got round to it. Where there is no drop box, any branch in the same "
            "council will take it - it does not have to go back where it came from.")
    return (
        "Three weeks is the usual loan, and most libraries renew it two or three times online or "
        "by phone unless somebody has reserved it, which is the difference between a three-week "
        "book and one you can keep for two months.")
ENTRIES.append(entry(
    "library-loan",
          (("library book", "library books", "book i borrowed", "books i borrowed",
            "borrowed book", "borrowed books", "borrowed a book", "library loan",
            "the book from the library", "library", "libraries",
            # a hold is a reservation, and the phrase itself has to be a key word or the
            # book-subject card takes it: "can i put a library book on hold" reached that
            "on hold at the library", "hold a library book", "put a book on hold",
            "put a library book on hold", "a book on hold"),
           ("overdue", "late", "late back", "return late", "returning late", "back late",
            "fine", "fines", "charge", "charges", "renew", "renewing", "renewal", "renewed",
            "reserve", "reserved", "reservation", "request", "how long", "how many",
            "keep it", "keep them", "borrow", "borrowing", "return", "returning", "drop off",
            "drop box", "letterbox", "after hours", "closed", "damaged", "lost",
            # a copy that has been spoiled is the same question as one that was lost or late
            "damage", "tore", "torn", "spilled", "spilt", "ruined", "chewed", "got wet",
            "scribbled", "dropped it")),
          _the_library_loan,
          ask=("how long", "how many", "how much", "fine", "fines", "renew", "renewed",
               "late", "overdue", "return", "returns", "returning", "back", "borrow",
               "borrowing", "keep", "keep it", "drop off", "drop box", "lost", "where",
               "what happens", "can i", "am i", "is there",
               # a copy that has been damaged is the same question as a copy that was lost, and
               # "my library book got damaged" reached nothing at all while it was missing here
               "damaged", "damage", "torn", "ruined", "chewed", "spilled", "dropped",
               "got wet", "scribbled",
               # reserving is a question about the loan too: "how do i reserve a library book"
               # and "can i put a library book on hold" were read as nothing at all
               "reserve", "reserved", "reservation", "hold", "on hold", "request",
               "how do i", "how can i", "take out", "including", "include"),
          avoid=("opening hours", "opening times", "join", "joining", "sign up", "membership",
                 "ebook", "ebooks", "audiobook", "audiobooks", "app", "kindle",
                 "shop", "shopping", "order", "refund", "courier", "seller", "amazon",
                 "parcel", "delivery", "tracking", "post office", "stamp", "hotel", "flight",
                 "train", "table", "restaurant", "hire", "car", "van", "bike", "bicycle",
                 "dvd", "video game", "tool", "tools", "carpet cleaner")))

# A sanction is its own benefit question, and it is asked with one word: "they sanctioned me",
# "how long does a sanction last", "what is a sanction". The appeal row is keyed on "sanction"
# too, but it needs a second key word from the decision words, so a line that only says the
# sanction reached nothing at all - a shrug, or "Sorry to hear that. What would help most?".
ENTRIES.append(entry(
    "benefit-sanction",
    (("sanction", "sanctioned", "sanctioning", "sanction letter", "they sanctioned me",
      "got sanctioned", "been sanctioned", "on a sanction",
      # the failure that earns one, said the way people say it
      "missed my appointment", "missed my work coach", "missed the appointment",
      "missing an appointment", "missed an appointment", "missed appointments",
      "didnt turn up to", "didnt go to my appointment", "sanctioned for"),
     ("what", "whats", "how long", "how many", "last", "lasts", "long", "why", "how", "help",
      "money", "benefit", "benefits", "universal credit", "uc", "jobcentre", "job center",
      "work coach", "hardship", "advance", "end", "lifted", "stopped", "cut", "days", "weeks",
      "months",
      # "they sanctioned me" says the subject and nothing else, and the row is the answer to it:
      # the sanction words count on both sides so the bare statement is not left to a shrug.
      "sanction", "sanctioned", "sanctions")),
    "A universal credit sanction cuts your standard allowance for a set number of days: 7 for a "
    "first missed appointment, up to 28 for repeats, and 91 days up to three years for leaving a "
    "job. Check the letter for the dates it runs between, then ask for a reconsideration if the "
    "decision is wrong and a hardship payment if the money has gone: repayable, and there for "
    "exactly this.",
    # the appeal against the decision is the row above, and a question about the claim itself is
    # not about a sanction
    avoid=("appeal", "appeals", "appealing", "mandatory reconsideration", "tribunal",
           "reconsideration", "how do i claim", "how to claim", "am i entitled", "do i qualify",
           "migrating", "migration", "move to universal credit",
           # a sanction in the ordinary sense: approval, or a council's
           "approved", "approval", "sanctioned by the council"),
))

# "my payment hasnt come through", "my benefit hasnt been paid this month", "my universal credit
# didnt go in": every one of them got an echo or "I'm listening - say more if it helps". A payment
# that has not arrived is the commonest benefit question there is, and the answer is the same
# whether it is universal credit, PIP, ESA or tax credits.
ENTRIES.append(entry(
    "benefit-payment-not-arrived",
    # "money" on its own is fenced rather than removed: "my money hasnt come through" is what a
    # person says when the payment they live on has not landed, and taking the word out of the key
    # left it with nothing at all - an acknowledgement is worse than a card that names the letter.
    # The wage words in `avoid` are what keep it off a payslip line.
    (("benefit", "benefits", "universal credit", "uc", "pip", "esa", "tax credits",
      "child benefit", "payment", "payments", "allowance", "money"),
     ("havent been paid", "havent had it", "hasnt been paid", "hasnt come through",
      "hasnt arrived", "havent received", "not received", "didnt go in", "did not go in",
      "didnt arrive", "not arrived", "still waiting", "late", "overdue", "missing",
      "hasnt gone in", "havent gone in", "not gone in", "didnt go through",
      "not gone through", "nothing in my account", "no money", "not been paid")),
    "Check the online account and the award letter first: a change of circumstances, bank details "
    "that failed or a sanction all stop a payment showing, and the letter says which. Ring the "
    "number on the latest letter the same day and ask why, and ask for a hardship payment if "
    "there is nothing coming in - it is repayable from future awards. Keep a note of who you "
    "spoke to and when.",
    # a parcel, a wage and a bill are not a benefit payment, and "payment" is in the key
    avoid=("parcel", "parcels", "delivery", "courier", "tracking", "order", "orders", "refund",
           "seller", "amazon", "ebay", "shop", "shopping", "wages", "salary", "pay slip",
           "payslip", "employer", "overtime", "bonus", "invoice", "client", "freelance",
           "rent", "landlord", "mortgage", "bill", "bills", "energy", "council tax", "water",
           "broadband", "phone bill", "loan", "credit card", "card payment",
           "direct debit", "standing order", "overdraft", "pension", "insurance", "dividend",
           # "money" is in the key, so every line about money that is not a benefit payment has
           # to be held out: wages, a payslip, a shift and a boss are the wage row's, and "my
           # money hasnt come through" after a week's work is a wage that did not arrive.
           "wages", "wage", "payday", "shift", "shifts", "hours worked", "my boss", "my manager",
           "my employer", "payroll", "self employed", "self-employed"),
))

# --- the name of a process is a subject in itself ------------------------------------
# "how do i ask for a mandatory reconsideration" and "what is a hardship payment" were both
# shrugs, and both are named processes rather than anything the person has to explain. The rule:
# a line that names one of these processes is a benefit question even when it does not name the
# benefit, so the process word is the subject and the ask is the second group. The appeal row
# above needs a benefit word beside its subject ("how do i appeal a benefit decision" answers,
# "how do i ask for a mandatory reconsideration" did not), which is the right fence for "appeal"
# and the wrong one for a name only the benefit system uses.
_ASKED_ABOUT_A_PROCESS = ("how", "how do i", "how to", "what", "what is", "whats",
                          "request", "apply", "applying", "write", "writing", "when",
                          "deadline", "time limit", "long", "do i", "can i", "start", "first",
                          "much", "get", "repay", "repayable", "amount", "turn", "wrong")

ENTRIES.append(entry(
    "benefit-reconsideration",
    (("mandatory reconsideration", "reconsideration", "tribunal"), _ASKED_ABOUT_A_PROCESS),
    "A mandatory reconsideration is the benefit office looking at its own decision again. Ask "
    "within one month of the decision letter: ring the number on it, then put the request in "
    "writing and ask for the statement of reasons. If it is still wrong, appeal to the tribunal "
    "within one month of that notice - free, and you can ask for a phone hearing.",
    # a tribunal is also where a housing, employment, parking or school case goes, and none of
    # those is the benefit office's; a line that already names the benefit is the appeal row's,
    # which goes on to say what evidence to send with it
    avoid=("universal credit", "benefit", "benefits", "tax credit", "tax credits", "pip", "esa",
           "overpaid", "overpayment", "underpaid", "sanction", "sanctioned",
           "housing", "eviction", "rent", "landlord", "council", "parking", "ticket", "school",
           "exam", "grade", "university", "planning", "immigration", "visa", "employment",
           "dismissal", "unfair", "tax", "hmrc", "child arrangement", "contact order",
           # an employment tribunal is about an employer, and the line names the employer
           "employer", "boss", "manager", "sacked", "dismissed", "redundancy", "redundant",
           "wages", "wage", "pay slip", "payslip", "contract of employment")))

ENTRIES.append(entry(
    "hardship-payment",
    (("hardship payment", "hardship"), _ASKED_ABOUT_A_PROCESS),
    "A hardship payment is extra universal credit, up to 60% of your standard allowance for the "
    "month, for when a sanction or a delay has left you short of rent, heating or food - and it is "
    "taken back out of later awards. Ask in your journal or at the jobcentre the same day, and ask "
    "the council about the Household Support Fund meanwhile.",
    # a hardship fund is a grant from a university or an energy supplier, and neither is the DWP's.
    # A council's own hardship or welfare-assistance payment is not universal credit either: "do i
    # get hardship from the council" was told the 60% of standard allowance rule, which is the
    # wrong fund said with confidence. The council words hold the row out of those lines.
    avoid=("hardship fund", "hardship grant", "university", "student", "students", "energy",
           "supplier", "water", "council tax", "rent arrears", "charity", "grant",
           "council", "from the council", "local authority", "discretionary", "welfare",
           "welfare assistance", "household support", "household support fund"),
    bias=1))
