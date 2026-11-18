""""Is it worth it" - the number to weigh, and the page that has the number.

"is it worth fixing", "is the castle worth the money", "are gore tex ones worth it": the composer
has no card behind them, because none is a question about a fact. The person wants a verdict, and
a verdict without the price, the quote or the hours is a guess. Main answered them with the search
hedge, which helps least of all: a search returns other people's verdicts and cannot know what the
repair costs in their town, or what the ticket price is.

STYLE.md's "Not knowing, honestly" has the shape that does help: say what the bot cannot see, name
the one place that has the figure, and stay with the person for the rest. So each family here says
what decides it (the quote against a replacement, the price against the use, the price against how
long you would stay), where that number comes from, and the one question the bot can act on. No
price, no deadline and no verdict is written here - the bot can see none of them.

It is a last resort. `bot/modules/greeting.py` asks it after the composer and only when the
composer's reply is a hedge, so a line any card answers never reaches it. It reads five shapes and
returns None on everything else, including a watched or read thing, a job, a course, a move, a
relationship, money trouble and anything medical or in a safety thread - those have readers of
their own, and a wrong card here would be worse than the hedge it replaced.
"""
import re

from . import fallback, pick

# --- the asks ------------------------------------------------------------------------------
# A thing of theirs that has broken: the number is the quote, weighed against a replacement.
# People drop the g: "worth gettin it fixed", "worth fixin". Every verb here is written with both
# endings, because the ask is the same word either way and only one of them is typed properly.
FIX_OR_REPLACE = re.compile(
    r"\bworth (?:fix(?:ing|in)|mend(?:ing|in)|repair(?:ing|in)|servic(?:ing|in)|descal(?:ing|in)|"
    r"clean(?:ing|in)|a service|the service|replac(?:ing|in)(?: it| them)?|"
    r"get(?:ting|tin) it (?:fixed|repaired|serviced|seen to|looked at)|a repair|the repair)\b")
# Somebody coming out to do the work: the number is the quotes, in writing, on the same job.
A_TRADE = re.compile(
    r"\bworth (?:getting someone (?:in|out|round)|getting a (?:plumber|electrician|builder|"
    r"roofer|joiner|painter|decorator|gardener|handyman|mechanic)|getting it (?:done|put in)|"
    r"having someone (?:in|out|round))\b"
    # the work done on a thing of theirs, and the people who do it: a main dealer, a garage
    r"|\bworth (?:getting|having) (?:my|our|the) \w+ (?:rotated|serviced|checked|done|"
    r"replaced|cleaned|fixed)\b"
    r"|\b(?:a|the) (?:main )?(?:dealer|garage|mechanic)\b[^.?]{0,20}\bworth\b")
# A trip with nothing named yet: "whats worth doing there", "anything worth seeing" - the ask is
# for the listings, and the listings for the day are what has them.
A_SUGGESTIONS = re.compile(
    r"\b(?:whats?|what is|what are|anything|something)\b[^.?]{0,20}\bworth "
    r"(?:doing|seeing|a look|the trip)\b|\bworth (?:doing|seeing) there\b")
# A place: the number is the ticket price against how long you would stay.
A_VISIT = re.compile(
    r"\bworth (?:visiting|a visit|the trip|the journey|the drive|going to see|seeing)\b")
PLACE_WORD = re.compile(
    r"\b(?:castle|cathedral|minster|abbey|church|museum|gallery|exhibition|show|tour|"
    r"zoo|safari park|theme park|aquarium|baths|spa|gardens?|park|palace|tower|ruins?|"
    r"monument|attraction|distillery|brewery|stadium|theatre|theater|opera|festival)\b")
# A thing to buy: the number is the price against the use.
A_PURCHASE = re.compile(
    r"\bworth (?:it|the money|the price|buy(?:ing|in)|get(?:ting|tin)|"
    r"paying (?:more|that|extra) for|the extra)\b")
# The small things: a kettle, a toaster, a phone. The repair is a part or a cleaner off a shelf,
# so the number to weigh is the shelf price of a new one against that, not a trade's quote.
A_SMALL_THING = re.compile(
    r"\b(?:kettle|toaster|iron|hoover|vacuum|microwave|phone|mobile|laptop|tablet|ipad|"
    r"printer|blender|air fryer|coffee machine|hair dryer|hairdryer|straighteners|fan|heater|"
    r"keyboard|monitor|headphones|earbuds|watch|remote|shredder|mower|strimmer|treadmill)\b")
# A thing named in the line itself: "is it worth getting a rice cooker" after a boiler question is
# a rice cooker. When the line names what it is about, the thread must not decide for it.
A_NAMED_THING = re.compile(
    r"\bworth (?:get(?:ting|tin)|buy(?:ing|in)|having|paying [^.?]{0,14}for|a|an) "
    r"(?:a|an|the|some) "
    r"(?!new\b|another\b|one\b|it\b)\w+")
# "or shall i get a new one", "a new one instead": a replace ask with no verb of its own.
A_REPLACE_WORD = re.compile(
    r"\b(?:a new one|new one instead|replace|replacing|get another|bin it|throw it out)\b")
# A thing a trade does fix, so the number is a quote even when the line says "a new one instead":
# "the boiler is 8 years old" then "is it worth getting a new one" is not a shelf price.
A_APPLIANCE = re.compile(
    r"\b(?:boiler|washing machine|dishwasher|tumble dryer|fridge|freezer|oven|hob|"
    r"central heating|radiators?|immersion|water tank|car|van|motorbike|bike|bicycle|roof|"
    # a rice cooker and a slow cooker sit on a shelf; the oven and the hob are fitted
    r"(?<!rice )(?<!slow )cooker|"
    r"gutter|window|door|fence|drive|patio|damp|shower|toilet|tap|sink|chimney)\b")
# Money already named against a thing that has a second-hand market: "is that car worth 4000",
# "my bike is worth 300". That is not the shelf price of a new one against the use, and it is not
# a trade's quote either - it is what that exact thing would sell for, and the ones that have sold
# are the only figures that say. A money figure counts with or without the sign, but two bare
# digits are usually a model number or an age, so it needs three or a decimal point.
A_MONEY = re.compile(r"£\s?\d[\d,]*(?:\.\d{2})?|\b\d[\d,]{2,}(?:\.\d{2})?\b")
# The things with a used market, where "what it is worth" is a resale figure rather than a price.
A_RESALE_THING = re.compile(
    r"\b(?:car|van|motorhome|campervan|caravan|bike|bicycle|motorbike|scooter|moped|"
    r"guitar|violin|cello|piano|keyboard|drum ?kit|amp|amplifier|watch|jewellery|jewelry|"
    r"ring|gold|silver|coins?|antiques?|furniture|sofa|table|wardrobe|"
    r"console|playstation|xbox|nintendo|switch|camera|lens|drone|telescope|"
    r"sewing machine|mower|ride on|tractor|boat|kayak|canoe|surfboard|"
    r"phone|iphone|laptop|macbook|tablet|ipad|pc|desktop|gpu|graphics card|"
    r"tools?|drill|saw|welder|compressor|generator)\b")
# A thing they own, or a used one described by its age or mileage: "is my old golf worth 1200",
# "is a 2015 fiesta with 90000 miles worth 3500". A car is worth a valuation even when the model
# name is one no list here has.
A_MINE = re.compile(r"\b(?:my|our)\b")
A_USED_MARK = re.compile(
    r"\b(?:miles|mileage|second ?hand|used|pre-owned|reg|registration|\d{4} reg|"
    r"\d+ years old|year old|old|vintage|antique)\b")
# The money ask that is not the word "worth": a person selling or being offered a figure asks
# whether it is about right - "is 6000 about right", "is 250 too cheap", "should i accept 500".
A_SALE_ASK = re.compile(
    r"\b(?:about right|too cheap|too much|too little|fair price|a fair|that fair|is that fair|"
    r"good price|a good|should i (?:accept|take|sell)|worth)\b")
# A price being argued about for something new, or a quote for work: other pools own those.
A_NEW_PRICE = re.compile(
    r"\b(?:paying|pay|buy|buying|get|getting|a new one|new|brand new|extra|more|deal|offer|"
    r"quote|quotes|someone|trade|garage|dealer|repair|fix|service|servicing)\b")

# A refusal they are thinking of arguing with: the number is the time it takes.
AN_APPEAL = re.compile(
    r"\bworth (?:appealing|challenging|disputing|arguing|taking it further|fighting)\b")

# --- what is theirs, and nothing here answers -----------------------------------------------
# A job, a course, a move, a relationship, a person: the verdict is about their life, not a price.
THEIR_OWN_LIFE = re.compile(
    r"\b(?:job|jobs|offer|career|course|degree|uni|university|college|apprenticeship|"
    r"relationship|marriage|him|her|them|us|we|we're|being friends|staying friends|"
    r"moving|move house|emigrat\w*|quitting|going part time|full time|office|"
    r"redundancy|settlement|watching|reading|the book|the film|the series|netflix)\b")
# A pet is a cost every month rather than a price once, and the pets' own cards answer it.
A_LIVING_THING = re.compile(
    r"\b(?:goldfish|fish|dog|puppy|cat|kitten|rabbit|hamster|guinea pig|horse|pony|pet|"
    r"reptile|lizard|snake)\b")
# Money trouble, a body, or an emergency: other readers own those.
STAND_DOWN = re.compile(
    r"\b(?:afford|cant afford|can't afford|owe|owed|debt|debts|arrears|loan|overdraft|"
    r"bleed\w*|bloods?|pain|ache\w*|sore|lump|rash|symptom\w*|doctor|gp|hospital|111|999|"
    r"scan|x-?ray|surgery|pregnant|baby|pension|annuity|retire\w*|im \d\d already)\b")

# --- the replies ----------------------------------------------------------------------------
# The quote against the replacement: the garage or the repair shop gives the first free, and what
# else is likely to go is what usually turns "fix it" into "not worth it".
A_FIX_REPLY = (
    "Whether it is worth fixing comes down to the quote against what a replacement would cost, "
    "and a garage, a repair shop or the engineer for that trade will give you that figure "
    "for nothing. Ask them what else is "
    "likely to go in the next year or two as well - that is usually what decides it. How old is "
    "it, and what else has gone wrong lately?",
    "That one is the quote against a new one, and nobody can call it without the quote. Every "
    "garage, repair shop or engineer for that trade will price the work for free, and it is "
    "worth asking what they would "
    "check next while it is in. What would you do with it if you did not fix it?",
)
# A small thing: the shelf price of a new one against the part or the cleaner and an hour.
A_SMALL_THING_REPLY = (
    "These are the ones where the two sums sit close together: a new one off the shelf against "
    "the part or the cleaner and an hour of your own time. The shop's page has the new price, and "
    "the maker's page or a repair video for that exact model names what the part is. How old is "
    "it, and does it still do the job apart from that?",
    "Nothing here can price either side of that, and for something this size the two prices are "
    "usually nearer than people expect: the shelf price of a new one against the part and an "
    "hour of your own time. The shop's page has the one; the maker's page or a parts site has "
    "the other. What is it doing wrong?",
)
# For a trip with nothing named: the listings for the day have the times and the prices, and the
# newest reviews say whether each one was worth the trip.
A_DAY_OUT_REPLY = (
    "I cannot see what is on near you, so the listings for the day are the first stop - the "
    "venue's own page has the times and whether it needs booking, and the newest reviews say "
    "whether people thought it was worth the trip. What sort of day are you after - a walk, "
    "something indoors, or food?",
    "Nothing here can see what is on there, and a guess at a name would be worthless. Start from "
    "what is on that day and check each place's own page for the price and the hours; the recent "
    "reviews are what tell you if it was worth the trip. Outside or indoors?",
)
# The quotes, in writing, on the same job.
A_TRADE_REPLY = (
    "That comes down to the quotes: two or three of them, in writing, for the same job, and what "
    "each one leaves out. Ask what is not included as well as what is, since that is where the "
    "cheap quote earns its money back. How big is the job?",
    "Nobody here can price work in your area, and one quote is a price rather than a market. Two "
    "or three written quotes for the same job, and the same question to each about what they would "
    "not do, tells you what it is worth. What needs doing?",
)
# The ticket price against how long you would stay.
A_VISIT_REPLY = (
    "Only you can weigh that, and it comes down to the ticket price against how long you would "
    "stay. The place's own page has the price and the opening times, and the newest reviews are "
    "the ones that say how long people actually spend inside. What else is on the list that day?",
    "That is the price against the time, and nothing here can see either. Its own page carries "
    "the ticket price and the hours; the recent reviews say whether people were in and out in an "
    "hour. Are you going for the place itself, or to fill a day?",
)
# The price against the use.
A_PURCHASE_REPLY = (
    "Whether it is worth it comes down to the price against how much you would use it, and that "
    "part is yours. The shop's or the maker's page has the price and the spec; reviews from the "
    "last few months are the ones that say what it is like once the newness wears off. What would "
    "you use it for most?",
    "Nobody can price that for you from here. What decides it is the price against the use: its "
    "own page has the figure, and the recent reviews are where the faults show up. How often "
    "would you use it?",
)
# Money named against a thing with a used market: the figure is what that thing sells for, and
# the sold ones are the only figures that say. Asking prices are what people hope for.
A_VALUATION_REPLY = (
    "What a thing like that is worth is set by the ones that actually sold, not the ones still "
    "up for sale: condition, age and whatever needs doing all move it, and sold or completed "
    "listings for the same model are the figures that count, with a dealer's trade-in price as "
    "the other end of it. What is it, and what sort of state is it in?",
    "That figure is a market rather than a fact, so the ones that sold are what answers it - the "
    "same model, close to the same condition, on the sold or completed listings, and a second "
    "source such as a dealer's trade-in offer to check it against. What condition is it in?",
)
# A refusal they could argue with: the cost is the time, and the letter says how.
AN_APPEAL_REPLY = (
    "There is little to lose but the time, and the letter itself says how to ask for a review and "
    "by when - that date is the thing to find first. Citizens Advice will go through the ground "
    "you have for free, and they are quicker than the appeal is. What reason did they give?",
    "That is usually worth the letter it takes, and the decision letter says how to challenge it "
    "and by when. Citizens Advice or the scheme named at the bottom of the letter will check "
    "whether you have a ground for it, free. What did they say the reason was?",
)


# A thread that is planning a trip: "we are in cornwall for a week" then "is the eden project
# worth it" is a place, whatever the name looks like, and the price against the time is the shape.
A_TRIP = re.compile(
    r"\b(?:trip|holiday|weekend away|day out|visiting|on our way|travel(?:l)?ing to|"
    r"staying in|booked (?:a|the)|half term|bank holiday|\b(?:in|to) [a-z]+ for (?:a|the) "
    r"(?:week|weekend|few days|fortnight|day)\b|\b(?:going|off) to [a-z]+ (?:next|this) week\b"
    # "i want to go to edinburgh castle", "thinking about a weekend in york": the going is the
    # trip, and a place named after it is what the money is for. A trip to the doctor, the tip or
    # the shops is not one of these.
    r"|\b(?:weekend|week|few days|day|break|holiday|time) (?:in|at) [a-z]"
    r"|\b(?:think(?:ing)? about|fancy|planning) (?:a|the) (?:trip|weekend|visit|day out)"
    r")")
# "i want to go to edinburgh", "heading off to rome": the destination is the trip. The places
# people go anyway are not, and they are what makes this shape worth reading at all.
A_GOING = re.compile(
    r"\b(?:go|goes|going|went|head(?:ing)?|off|fly|flying|drive|driving|travel\w*|get) to "
    r"(?:the |a |my |our )?([a-z][a-z']*)")
GOING_ANYWAY = frozenset((
    "the", "a", "my", "our", "work", "bed", "school", "college", "uni", "town", "shop", "shops",
    "supermarket", "gym", "bank", "loo", "toilet", "pub", "doctor", "doctors", "dentist", "dentists",
    "hospital", "surgery", "pharmacy", "chemist", "tip", "dump", "office", "vets", "vet", "park",
    "post", "library", "council", "court", "airport", "station", "bus", "train", "sleep", "home",
    "sleep", "it", "them", "hell", "potty", "bath", "shower", "kitchen", "garage", "garden",
    "loft", "attic", "cellar", "skip", "bin", "bins", "charity", "car", "van", "motorway",
))


# Trouble with a person, and a body: "my marriage is on the rocks" then "is it worth fixing" is
# not a garage, and "my back keeps going" then the same line is a body. The line alone cannot tell,
# so the thread is read for the two things a repair question shares with them - and both stand the
# module down, which keeps the bot's own line. Merely naming a person is not trouble ("my sister
# lives in cork" then "is it worth going for a week" is still a trip), so the words here are the
# trouble itself, or a part of the body beside something wrong with it.
A_TROUBLE_THREAD = re.compile(
    r"\b(?:marriage|on the rocks|fell out|not speaking|row(?:ed)? with|split up|divorce|"
    r"relationship|cheating|affair|he left|she left|walked out|last legs)\b")
A_BODY_THREAD = re.compile(
    r"\b(?:back|knee|hip|shoulder|ankle|wrist|neck|spine|leg|arm|foot|stomach|chest|tooth|"
    r"teeth|blood|skin|eye|ear|throat|joint)\b[^.?]{0,24}"
    r"\b(?:hurt\w*|ache\w*|sore|pain\w*|keeps? going|bad|injur\w*|stiff|swollen|ill|"
    r"infection|broke\w*)\b")
A_DEAL_THREAD = re.compile(
    r"\b(?:tariff|supplier|energy|switch(?:ing)? (?:supplier|tariff|deal)|fixed for two years|"
    r"pension|annuity|retire\w*|isa|savings account|mortgage deal)\b")
# The people who are paid for their time rather than a thing on a shelf: their page has no price.
# A course is not a thing with a used market or a page with a figure: "is it worth the money"
# after a part-time degree wants a different answer entirely, so the valuation stands down.
A_STUDY = re.compile(
    r"\b(?:degree|uni|university|masters|phd|doctorate|course|courses|college|apprenticeship|"
    r"tuition|fees|a level|a levels|night class|night school|qualification|diploma|student)\b")
A_PAID_PERSON = re.compile(
    r"\bworth (?:getting|having|seeing|using) (?:a|an|the) (?:personal )?(?:trainer|coach|tutor|"
    r"cleaner|accountant|lawyer|solicitor|dentist|plumber|electrician|carer|nanny|"
    r"childminder|therapist|counsellor)\b")
# "it isnt worth it" on its own is not a question about a price - it is how despair sounds, and
# the safety readers own that line.
NOT_AN_ASK = re.compile(
    r"^\s*(?:(?:it|is|was|itnt|isnt|isn t|wasnt|this|that|really|still|even|then|though|just|"
    r"life)\s+)*worth (?:it|the (?:bother|effort|pain|hassle)|anything)\s*[.!]?$")
# What somebody else said about it, and a line that has already decided against: neither is a
# question about a price, and the second is how despair sounds.
A_REPORT = re.compile(
    r"\b(?:says?|said|reckons|thinks|told me)\b[^.?]{0,30}\bworth\b|\bnot worth\b")


def _a_destination(said):
    """A place they say they are going to, and not one of the errands."""
    for word in A_GOING.findall(said):
        if word not in GOING_ANYWAY and len(word) > 2:
            return word
    return ""


def _a_trip_in_the_thread(memory):
    turns = [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)]
    said = " ".join(str(t.get("user") or "") for t in turns[-4:]).lower()
    return bool(A_TRIP.search(said))


def _the_thread(memory, back=2):
    """The last turn or two of the person's own lines - the subject this ask is about.

    Two, not four: "my marriage is on the rocks" then "is it worth fixing" is a marriage, but the
    same thread two turns later ("is it worth getting a rice cooker") is a rice cooker, and a guard
    that reads four turns keeps standing down on a subject the person has already left.
    """
    turns = [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)]
    return " ".join(str(t.get("user") or "") for t in turns[-back:]).lower()


def _is_it_worth_it(text, memory, reply):
    """The number to weigh for a "worth it" the composer hedged on, or None."""
    if not reply or not fallback.is_a_hedge(reply):
        return None
    said = " ".join(str(text or "").lower().split())
    # A sale or an offer names a figure and asks whether it is right, without ever saying "worth".
    if not said or not A_SALE_ASK.search(said) or len(said.split()) > 12:
        return None
    if STAND_DOWN.search(said):
        return None
    # A thing with a used market, and a figure against it, is a valuation before the life guard
    # is asked: "we are selling the caravan, is 6000 about right" has a "we" in it and is a
    # caravan, while "we" in the life guard is a relationship.
    if (A_MONEY.search(said) and not A_NEW_PRICE.search(said)
            and not A_STUDY.search(said + " " + _the_thread(memory))
            and (A_RESALE_THING.search(said)
                 or A_RESALE_THING.search(_the_thread(memory)))):
        return pick(A_VALUATION_REPLY, memory, said)
    if THEIR_OWN_LIFE.search(said):
        return None
    # A course, a degree, a qualification: a price against a life, not against a market, and
    # nothing here can weigh either side of it.
    if A_STUDY.search(said + " " + _the_thread(memory)) and not A_RESALE_THING.search(said):
        return None
    if A_LIVING_THING.search(said) or A_PAID_PERSON.search(said) or NOT_AN_ASK.match(said) or A_REPORT.search(said):
        return None
    around = _the_thread(memory)
    if (A_TROUBLE_THREAD.search(around) or A_BODY_THREAD.search(around)
            or A_DEAL_THREAD.search(around)):
        return None
    if fallback.in_a_safety_thread(memory):
        return None
    # Money already named against a thing that has a used market: "is that car worth 4000" is a
    # valuation, and neither the shelf price nor a quote answers it. Read before the other pools
    # because the figure is the ask, and only when the thing is a resale thing - a sofa yes, a
    # kitchen no - and nothing in the line is asking for a price on something new or work done.
    if (A_MONEY.search(said) and not A_NEW_PRICE.search(said)
            and not A_STUDY.search(said + " " + _the_thread(memory))
            and (A_MINE.search(said) or A_USED_MARK.search(said))):
        return pick(A_VALUATION_REPLY, memory, said)
    if A_TRADE.search(said):
        return pick(A_TRADE_REPLY, memory, said)
    # The thing named decides where the number lives: a kettle's fix is a part off a shelf, and a
    # boiler's is a trade's quote even when the line says "a new one instead". A line that names
    # its own thing is about that thing, so the thread is only read when the line says "it".
    reads_thread = not A_NAMED_THING.search(said)
    small = A_SMALL_THING.search(said) or (reads_thread and A_SMALL_THING.search(around))
    appliance = A_APPLIANCE.search(said) or (reads_thread and A_APPLIANCE.search(around))
    if (small or appliance) and (FIX_OR_REPLACE.search(said) or A_PURCHASE.search(said)
                                 or A_REPLACE_WORD.search(said)):
        return pick(A_SMALL_THING_REPLY if small else A_FIX_REPLY, memory, said)
    if FIX_OR_REPLACE.search(said):
        return pick(A_FIX_REPLY, memory, said)
    if A_TRADE.search(said):
        return pick(A_TRADE_REPLY, memory, said)
    if AN_APPEAL.search(said):
        return pick(AN_APPEAL_REPLY, memory, said)
    if A_SUGGESTIONS.search(said):
        return pick(A_DAY_OUT_REPLY, memory, said)
    # A place the line does not name but the thread does: "i want to go to edinburgh castle" then
    # "is it worth the money" is a ticket, not a shelf price. The place is read from the thread
    # only when the line has no thing of its own, and it is asked before the purchase pool because
    # "worth the money" on its own says nothing about what the money is for.
    a_place = (A_VISIT.search(said) or PLACE_WORD.search(said)
               or _a_trip_in_the_thread(memory)
               or (reads_thread and (PLACE_WORD.search(around) or _a_destination(around))))
    if a_place:
        return pick(A_VISIT_REPLY, memory, said)
    if A_PURCHASE.search(said):
        return pick(A_PURCHASE_REPLY, memory, said)
    return None

# The closing question a pool ends with is the one thing the bot can act on - unless the person
# has just told it. "the kettle is furred up" then "is it worth descaling it or shall i get a new
# one" must not be answered with "What is it doing wrong?".
A_FAULT_ALREADY_SAID = re.compile(
    r"\b(?:furred|scaled|limescale|broken|stopped|stopping|keeps (?:stopping|cutting)|cutting out|"
    r"leaking|leaks|dripping|due (?:a|its) service|due a mot|making a noise|noisy|worn|worn out|"
    r"faulty|patchy|not working|won't|wont|doesn't|doesnt|died|dead|stiff|sticking|squeaking)\b")
LAST_ASK = re.compile(r"\s+(?:What needs doing|What is it doing wrong|How big is the job|"
                      r"What is it doing|What sort of day are you after[^?]*|Outside or indoors|"
                      r"How often would you use it)\?$")


def _with_what_they_said(reply, memory, said):
    """The same reply without its closing question when the person has just answered it."""
    if not reply:
        return reply
    before = " ".join(str(t.get("user") or "") for t in (memory.get("turns") or [])[-2:]
                      if isinstance(t, dict)).lower()
    if A_FAULT_ALREADY_SAID.search(said + " " + before):
        stripped = LAST_ASK.sub("", reply)
        if stripped and stripped != reply and stripped.endswith("."):
            return stripped
    return reply


def is_it_worth_it(text, memory, reply):
    """The pool's reply, minus a question the person has already answered this conversation."""
    said = " ".join(str(text or "").lower().split())
    return _with_what_they_said(_is_it_worth_it(text, memory, reply), memory, said)
