"""A price is asked in many more ways than the live-price row lists.

`fallback.LIVE_KINDS` has had an honest note for a live price for a long time - "I can't look up
live prices, sorry. The seller's site or a price comparison site will have today's figure" - and
three phrasings reached it. Everything else fell through to the search hedge, so a person asking
"what does a tattoo cost" was told to search, one branch away from a reply that says what the bot
cannot see and where the figure is.

The reading is here rather than in `fallback.py` because that file is at the world's size limit and
a reader that has to be added to it is a reader that cannot be filed.

Three shapes, and what each keeps off:
- `PRICE_ASK`, the ask itself in the words people use for it;
- a judgement on an amount (`is that normal`, `is that a fair price`), which needs money in the
  line or in the one before, because "is that normal" alone is as often about a child's speech;
- a job, which no page prices ("two quotes"), rather than a thing on sale.
"""

import re

PRICE_ASK = re.compile(
    # "what does a tattoo cost", "what do tickets cost", "whats the damage"
    r"\bwhat\s+(?:do|does|did|would|will|should|might)\b[^?.!,]{0,36}?\bcost"
    r"|\bwhat(?:'s|s)?\s+(?:the\s+)?(?:cost|price|going\s+rate|damage|ballpark)\b"
    # "how much does a tattoo cost", "how much would that set me back", "how much is a haircut"
    r"|\bhow\s+much\s+(?:does|do|would|will|should|might|can)\b[^?.!,]{0,36}?"
    r"\b(?:cost|charge|set\s+me\s+back|come\s+to)\b"
    r"|\bhow\s+(?:much|expensive)\s+(?:is|are|was|were)\b"
    # "how much should i spend", "how much do you pay for a bike", "how much to expect to pay"
    r"|\bhow\s+much\s+(?:should|shall|ought\s+to)\b[^?.!,]{0,24}?\b(?:spend|pay)\b"
    r"|\bhow\s+much\s+(?:do|would|will)\s+(?:i|we|you)\s+(?:need\s+to\s+)?"
    r"(?:spend|pay|budget|expect)\b"
    r"|\bhow\s+much\s+for\s+(?:a|an|one|the)\b"
    # "is that a normal price", "the going rate", "a fair cost"
    r"|\b(?:fair|normal|reasonable|typical|sensible|going|right)\s+(?:price|rate|money|cost)\b"
    # "roughly how much", "how much in total", "how much altogether"
    r"|\bhow\s+much\b[^?.!,]{0,16}\b(?:roughly|in\s+total|altogether|all\s+in)\b"
    r"|\b(?:roughly|about)\s+how\s+much\b")

# The same ask with the front of it dropped, which is how it is typed on a phone: "ow much is a
# pint of milk", "much does a pint cost". Only at the head of the line, because "that much is a
# stretch" is a judgement and "so much is a stretch" is not a question about a shop.
PRICE_ASK_HEADLESS = re.compile(
    r"^(?:and\s+|but\s+)?(?:ow\s+much|much)\s+(?:is|are|was|were|do|does|would)\b")

# A job is not a listing: "how much would a service cost", "the garage wants 400 for a service".
# No seller's page has that figure, because it depends on who does the work and what they find
# when they open it up, so a comparison site is the wrong place to send somebody.
PRICE_OF_A_JOB = (
    "I can't price a job from here, sorry - it comes down to who does it and what they find when "
    "they open it up. Two quotes will give you a real range, and I can help you weigh them up.",
    "No figure from me on a job like that, sorry: it is a quote rather than a price list. Ring "
    "two firms and compare what each one covers, not just the total.",
)
# A judgement on a job with a figure already in the chat: what settles it is a second quote, and
# the answer says that first rather than opening on what the bot cannot see. The pool above opens
# "I can't price a job from here", which is honest but is the hedge in front of the answer, and a
# person who has just been told 900 quid wants to know how to test that figure.
A_JOB_JUDGED = (
    "A quote is only normal against another one: ring a second firm for the same job and compare "
    "what each one covers, not just the total, because who does it and what they find when they "
    "open it up is why two figures for the same job come out apart.",
    "What tells you whether that figure is normal is a second quote for the same job, in writing, "
    "compared on what each one includes rather than the total alone. The range moves with who does "
    "it and what they find, so the second quote is the only real test of the first.",
)
JOB_WORDS = frozenset("""
plumber plumbing builder builders decorator decorating electrician electrics joiner carpenter
plasterer tiler roofer handyman mechanic garage servicing fitted fitting installation install
labour quote quotes quoted repair repairs service gardener locksmith removals surveyor mot
fix fixing fixed mend mending rewire rewiring replumb
""".split())

# A bare "is it expensive" (or "is that cheap") names no thing at all: the thing is whatever the
# chat has been about, and the chat is as often a country as a boiler. Neither pool above fits - a
# seller's own page is nothing to do with a trip, and "two quotes" is nothing to do with a
# haircut - so a judgement on an unnamed thing says the one thing that is true of every price and
# is the thing that settles it: the same thing, priced in three places.
PRICE_OF_A_THING = (
    "What decides it is the same thing priced in more than one place, and what each one includes: "
    "two or three quotes for the same job tell you whether a figure is normal. Today's prices move "
    "with where you are, so I can't see them from here.",
    "Two or three places, the same thing, and compare what each one includes rather than the total "
    "alone - that is what answers whether a price is fair. The figures themselves move with where "
    "you are and when you go, so they are not mine to see.",
)

# A judgement on an amount somebody has asked for. The words alone are about fairness - "i work
# full time, is that fair on it" is not a price question - so the shape counts only beside money.
PRICE_JUDGEMENT = re.compile(
    r"\bis\s+(?:that|this|it)\s+(?:about\s+)?(?:fair|normal|reasonable|right|about\s+right|"
    r"steep|a\s+lot|too\s+(?:much|dear|expensive))\b")

# The same judgement with the thing being judged said after the word: "is that a normal price",
# "is that a fair rate", "is that a reasonable quote". Those are not requests for a figure - the
# figure is on the page in front of them - so the answer that settles them is that the same thing
# priced in two or three places is what tells you, and for a job, two firms and what each covers.
# Without this the fairness shapes in PRICE_ASK read as a plain price ask and the person got "I
# can't look up live prices, sorry. The seller's site or a price comparison site will have
# today's figure" - which is no answer to "the plumber wants 900 quid, is that a normal price".
A_FAIRNESS_JUDGEMENT = re.compile(
    r"\b(?:fair|normal|reasonable|typical|sensible|going|right|steep|good|ok|decent)\s+"
    r"(?:price|prices|rate|rates|quote|quotation|cost|money|fee|charge)\b"
    r"|\b(?:that|this|it)\s+(?:about\s+)?right\b[^?.!]{0,14}\b(?:price|pay|paid|charge)\b")
# The faces that are money on their own, so no cue is needed: nobody says "is it expensive" about
# anything but a price. "is it expensive" after "im thinking of a hotel in lisbon" was answered
# with the search hedge, and so was "is that expensive to fix" after "the boiler is leaking" -
# the same family as the judgement above, one word apart from it. "they" and "those" are here
# because a plural thing takes them ("are they expensive").
MONEY_JUDGEMENT = re.compile(
    r"\b(?:is|are|isn'?t|aren'?t|was|were)\s+(?:that|this|it|they|those|these)"
    r"(?:\s+[a-z']+){0,2}\s+(?:so|very|really|too|quite|pretty)?\s*"
    r"(?:expensive|pricey|dear|overpriced|costly|cheap|good\s+value)\b"
    r"|\b(?:that|this|it|they|those|these)\s+(?:sounds|seems|looks)\s+(?:so\s+|very\s+|really\s+)?"
    r"(?:expensive|pricey|dear|steep|a\s+lot|overpriced)\b"
    r"|\b(?:expensive|pricey|cheap)\s+(?:to|for)\s+(?:fix|repair|mend|replace|service|run|insure|"
    r"install|fit|clean|heat)\b"
    # a number with a currency on it, and a judgement on it (no \b before the currency: a symbol
    # is not a word character, so the boundary would never fall there)
    r"|(?:[\u00a3$\u20ac]\s?\d+|\b\d+\s?(?:pounds?|quid|euros?|dollars?|bucks))\s+"
    r"(?:a\s+lot|too\s+much|expensive|steep)\b")
A_MONEY_CUE = re.compile(
    r"[\u00a3$\u20ac]|\b\d{2,}\b|\b(?:quid|quotes?|quoted|charged|charges?|price|prices|"
    r"cost|costs|bill|invoice|fee|fees|paid|pay)\b")

# "how much salt in bread" / "and how much for a bigger loaf": in a cooking chat the next "how
# much" is more of the recipe, not a shop price.
FOOD_SAID_BEFORE = re.compile(
    r"\b(?:flour|salt|sugar|bread|loaf|loaves|dough|batter|yeast|rice|pasta|butter|milk|eggs?|"
    r"cheese|mince|meat|chicken|beef|pork|lamb|fish|potato(?:es)?|onions?|carrots?|tomato(?:es)?|"
    r"vegetables?|stock|oats|noodles|lentils|beans|yoghurt|yogurt|sauce|spices?|pepper|garlic|"
    r"cake|biscuits?|pastry|porridge|soup|curry|roast|recipe|oven|bake|baking|loaf tin)\b")
A_PRICE_WORD = re.compile(
    r"\b(?:cost|costs|price|prices|priced|charge|charges|charged|quid|cheapest|expensive|cheaper|"
    r"pound|pounds|dollars?|euros?|fee|bill)\b|[\u00a3$\u20ac]")

# A dose, a portion, a length of time, a rate to save at and the bot's own fee are all asked with
# the same words as a price: "how much calpol can i give", "how much rice for four", "how much
# longer will it take", "how much should i put away each month".
NOT_A_PRICE = re.compile(
    r"\b(?:dose|dosage|ml|millilitres?|mg|tablets?|capsules?|spoons?|teaspoons?|calpol|"
    r"paracetamol|ibuprofen|nurofen|medicine|medication|painkillers|insulin|vitamin\s+[a-z])\b"
    # a quantity, weighed or shared out, rather than a price
    r"|\bhow\s+much\s+(?:longer|time|sleep|salt|sugar|fibre|protein|water|sun|light|noise|"
    r"space|of)\b"
    r"|\bhow\s+(?:much|many)\s+(?:is|are|of)\s+(?:a|an|one|two|\d+)?\s*"
    r"(?:grams?|grammes?|kilos?|ounces?|cups?|tablespoons?|handfuls?|portions?|servings?)\b"
    r"\s*(?:[?.!]|$)"
    r"|\b(?:rice|pasta|mince|potato(?:es)?|meat|chicken|cheese|flour|sugar|butter|milk|"
    r"lentils|beans|oats|noodles|batter|yoghurt|yogurt)\b[^?.!,]{0,18}\b(?:each|per\s+person|"
    r"per\s+head|for\s+(?:two|three|four|five|six|seven|eight|\d+))\b"
    # feeding a household for a week is a food bill with a going rate, not a shop's price:
    # "how much does it cost to feed a family of four" got "I can't look up live prices", and
    # money's food-bill row has the figure.
    r"|\bfeed(?:ing)?\b[^?.!,]{0,30}\b(?:family|families|kids|children|household|of us|"
    r"for us|four|five)\b"
    r"|\bwhat (?:does|do) (?:a|the) (?:week|month)(?:'s)? (?:food|shop|groceries|shopping)\b"
    # a rate to save at, not a price to pay
    r"|\b(?:should|shall|can|could|do|does)\b[^?.!,]{0,24}\b(?:save|saving|savings|"
    r"put\s+(?:away|by|aside)|overpay|pay\s+off|pay\s+down)\b"
    # fairness, which is not money: "is that fair on it", "is that fair to say"
    r"|\bis\s+(?:that|this|it)\s+(?:about\s+)?(?:fair|right)\s+(?:on|of|to|for|that)\b"
    r"|\bfair\s+enough\b"
    # the bot's own fee
    r"|\b(?:you|u)\s+charge\b")


# A balance is not a price. "How much is left on my gift card", "how much is on my travel card",
# "how much have I got left on my account" are the card's or the account's own number, and nobody
# shops around for it, so the price note is the wrong note. "How much is a gift card" is a price
# and stays in. The carrier word keeps it off "how much is on at the cinema" and "how much is in a
# pint of milk", which are the live-price and the quantity questions they look like.
BALANCE_ASK = re.compile(
    r"\bhow\s+much\s+(?:is|are|was|were|have|has)\b[^?.!,]{0,32}?\b(?:left|remaining)\b"
    r"|\bhow\s+much\s+(?:is|are|was|were)\s+(?:on|in)\s+(?:my|our|the|your|their)\b"
    r"|\b(?:left|remaining)\s+(?:on|in)\s+(?:my|our|the|your)\b"
    r"|\bmoney\s+(?:left|remaining)\b")
BALANCE_CARRIER = re.compile(
    r"\b(?:card|cards|voucher|vouchers|account|balance|wallet|gift|pass|pot|points|credit)\b")


def _a_balance_ask(clean):
    """True when the line asks what is already on a card or in an account, not what one costs."""
    return bool(BALANCE_ASK.search(clean) and BALANCE_CARRIER.search(clean))


# A sum against a period is not a price to look up: "is 900 a month doable", "is 1200 a month
# affordable", "can i do it on 300 a month", "is 200 a week enough to live on". Nothing is being
# sold, so no seller's page answers it and "two quotes" is nonsense - the answer turns on their
# rent, their travel, their bills, which nobody but they can see. So the reply says which sum
# settles it and asks for the half it does not have.
A_BUDGET_ASK = re.compile(
    # "is 900 a month doable", "would 250 a week be enough"
    r"\b(?:is|would|will)\b[^?.!,]{0,14}?(?:[\u00a3$\u20ac]\s?)?\d[\d,]*(?:\.\d+)?\s*"
    r"(?:a|per|/)\s*(?:month|week|fortnight|year)\b[^?.!,]{0,28}"
    r"\b(?:enough|doable|affordable|liveable|livable|realistic|feasible|manageable|possible|"
    r"ok|okay|alright)\b"
    # "is it doable on 900 a month", "would that be affordable on 250 a week"
    r"|\b(?:is|would|will)\s+(?:it|that|this)\s+(?:be\s+)?(?:doable|affordable|enough|realistic|"
    r"manageable|feasible)\b[^?.!,]{0,14}?(?:[\u00a3$\u20ac]\s?)?\d[\d,]*\s*"
    r"(?:a|per)\s*(?:month|week|fortnight|year)\b"
    # a sum five figures in "k" is money on its own: "is 30k a year enough to live on"
    r"|\b(?:is|would|will)\b[^?.!,]{0,14}?\d+(?:\.\d+)?\s?k\b[^?.!,]{0,28}"
    r"\b(?:enough|doable|affordable|liveable|livable|realistic|feasible|manageable)\b"
    # "can i do it on 300 a month", "could we live on 1200 a month"
    r"|\bcan\s+(?:i|we|you)\s+(?:do\s+(?:it|this|that)|live|manage|afford|survive|cope|get\s+by)"
    r"\b[^?.!,]{0,20}?\d[\d,]*\s*(?:a|per)\s*(?:month|week|fortnight|year|day)\b"
    # "live on 200 a week", "is it enough to live on"
    r"|\blive\s+on\s+(?:[\u00a3$\u20ac]\s?)?\d[\d,]*\s*(?:a|per)\s*(?:week|month|year)\b"
    r"|\benough\s+to\s+live\s+on\b"
    r"|\bget\s+by\s+on\s+(?:[\u00a3$\u20ac]\s?)?\d[\d,]*\s*(?:a|per)\s*(?:week|month)\b")

# "Are they worth 120 pounds", "is it worth 300", "are they worth it". A figure is named, so the
# question is whether that figure buys the thing, and what settles it is the same thing priced
# elsewhere for the same job. The bare "is it worth the money" is deliberately not here: it names
# no figure and no thing, and main already answers it from the money-decision pool, which speaks
# about the person's own money instead of sending them shopping.
WORTH_AN_AMOUNT = re.compile(
    r"\bworth\s+(?:[\u00a3$\u20ac]\s?\d{2,}|\d+(?:\.\d+)?\s*(?:pounds?|quid|euros?|dollars?|bucks)\b"
    r"|\d{3,}\b)"
    r"|\bworth\s+(?:the|that|this|its|their|his)\s+(?:price|cost)\b")
# "Are they worth it" carries no money of its own and is as often about an effort as a purchase,
# so it needs the money somewhere: in the line ("worth it for the money"), or in what the person
# said one turn before ("they want 120 for it").
WORTH_IT = re.compile(
    r"\b(?:are|is|was|were)\s+(?:they|those|these|it|that|this)\s+worth\s+it\b")
# "we have 900 a month after rent" then "is that doable": the sum is one turn back, and the
# judgement on it is the same question as "is 900 a month doable" asked the short way.
A_BARE_BUDGET_JUDGEMENT = re.compile(
    r"\b(?:is|would|will)\s+(?:that|this|it)\s+(?:be\s+)?(?:doable|affordable|realistic|enough|"
    r"manageable|feasible|possible|ok|okay|alright)\b"
    # "is 1200 doable", with the money already in the chat
    r"|\b(?:is|would|will)\s+(?:[\u00a3$\u20ac]\s?)?\d[\d,]*\s+(?:be\s+)?(?:doable|"
    r"affordable|enough|realistic|manageable|feasible|possible)\b")
A_MONEY_NEARBY = re.compile(
    r"[\u00a3$\u20ac]|\b\d{3,}\b|\b(?:money|quid|price|prices|cost|costs|pay|paid|paying|"
    r"pounds?|dollars?|euros?|bucks|cheaper|cheap|expensive|value)\b")

A_BUDGET_IS_THEIR_OWN_SUM = (
    # The person got a pointer and a question and nothing they could use; a friend leads with the
    # part they know. What is known here is which costs decide a month and where each figure is
    # written down - housing, council tax and energy are the three that are fixed for the year,
    # and the band is on the council's own site. Then the sum, then the one thing the bot cannot
    # see from here.
    "Housing, council tax and energy are the three that decide whether a month stretches, and the "
    "first two are fixed for the year - your council's site has your band and what it comes to. "
    "Add those, take them off the figure, and what is left is what has to cover food and travel. "
    "I can't see your bills from here, so tell me if the rent is already inside that figure.",
    "Most of a month goes on housing, council tax, energy and food. The first three are written "
    "down somewhere - the band is on your council's site and the energy figure is on the bill - "
    "and food you can judge from one week's shop. Put those against it and the rest is "
    "arithmetic; the bills are the part I can't see, so I can't do that sum from here.")


def _bounded(phrase):
    return re.compile(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])")


def _has(clean, phrases):
    return any(_bounded(phrase).search(clean) for phrase in phrases)


def the_price_reply(clean, phrases, before, options):
    """The honest note for a price, or None when the line is not asking for one.

    `phrases` are the wordings `fallback.LIVE_KINDS` already lists for the row, `before` is the
    person's previous line (a judgement usually comes one turn after the amount), `options` is
    that row's own pool.
    """
    if NOT_A_PRICE.search(clean) or _a_balance_ask(clean):
        return None
    if before and FOOD_SAID_BEFORE.search(before) and not A_PRICE_WORD.search(clean):
        return None
    if A_BUDGET_ASK.search(clean) or (A_BARE_BUDGET_JUDGEMENT.search(clean)
                                     and A_MONEY_NEARBY.search(before or "")):
        return A_BUDGET_IS_THEIR_OWN_SUM
    judged = bool(MONEY_JUDGEMENT.search(clean) or PRICE_JUDGEMENT.search(clean)
                  or A_FAIRNESS_JUDGEMENT.search(clean))
    worth = bool(WORTH_AN_AMOUNT.search(clean)) or bool(
        WORTH_IT.search(clean)
        and (A_MONEY_NEARBY.search(clean) or A_MONEY_NEARBY.search(before or "")))
    asked = (_has(clean, phrases) or PRICE_ASK.search(clean) or worth
             or PRICE_ASK_HEADLESS.match(clean)
             or (judged and (A_MONEY_CUE.search(clean) or A_MONEY_CUE.search(before)
                             or MONEY_JUDGEMENT.search(clean))))
    if not asked:
        return None
    # The trade is as often the turn before as this one: "the plumber wants 900 quid" then "is
    # that a normal price" named no trade at all, so the job pool was never reached and the
    # person was sent to a seller's page for a quote from a plumber.
    if _has(clean, JOB_WORDS) or (judged and _has(before or "", JOB_WORDS)):
        # "is that a normal price" after "the plumber wants 900 quid" is a judgement on a figure
        # the person already has, so the answer starts with what tests it, not with what the bot
        # cannot see. A plain "how much does a tiler charge" keeps the pool above.
        return A_JOB_JUDGED if judged else PRICE_OF_A_JOB
    if judged or worth:
        # A judgement on a price rather than a request for a figure: what settles it is the same
        # thing priced in three places, and the line usually names no thing at all.
        return PRICE_OF_A_THING
    return options
