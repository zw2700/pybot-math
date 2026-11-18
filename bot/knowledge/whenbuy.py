"""When to buy things: the month a mattress, a sofa, a car or a coat is cheapest.

A "when" question is not a "which one" question. "When is the best time to buy a mattress" was
answered with how to choose a mattress, "when should i buy a new car" with how to pick a car and
"when is the best time to buy a winter coat" with what to look for in a coat: fluent, about the
same object, and no answer to the question that was asked. The choosing rows in
bot/knowledge/shopping.py are about the object and this domain is about the calendar, so a line
that asks the calendar question reaches a row here.

Each row is an item, the weeks it is actually cheap, and the one thing that catches people out.
The facts are the retail calendar everybody can check: the January sales, the Black Friday week
at the end of November, the end of a season for the things that season sells, and the quiet
months at a car dealer. Where a "sale" price is not a real discount - mattresses, most of all -
the row says so instead of pretending.
"""
import re

from .lookup import asks_where_a_shop_answers, entry

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("shopping", "money")

# The calendar a line has to be asking about: a time word is what makes it a when question, and
# "prices drop" and "sell off" are timing words even without one ("will tv prices drop").
# The words are the ask, never the noun it is about. "month" and "months" were in this list and
# a noun is not a question: "a bit short this month" and "my phone bill is 30 a month" say what
# they pay or how long the money has to last, and the calendar is no answer to either. What asks
# when is the ask around the noun ("what month", "which month", "cheapest month", "good month"),
# and the time words below that are a date on their own ("january", "black friday").
TIME_ASK = ("when", "what month", "which month", "what time of year", "time of year",
            "best time", "best month", "cheapest time", "cheapest month", "right time",
            "good time", "good month", "month to buy", "time to buy", "when to buy", "what time",
            "black friday", "january",
            "january sales", "sell off", "price drop", "prices drop", "go down", "come down",
            "going down",
            # "how do i get the best deal on a car" is a cheaper-price question with no time
            # word in it, and the answer is the end of the quarter; "what is a good deal on a
            # phone" is the same word asked the other way round and is not this row, so only
            # the asking-to-pay-less half is here.
            "get the best deal", "get a better deal", "get a good deal", "get the cheapest",
            "get a cheaper")

# Every phrase above is written singular, and people say the ask in either number: "which months
# are cheapest for a tv" and "are sofas cheaper in the summer months" are the ask this row exists
# for, and with whole words only they matched nothing, so the calendars stood down and the lines
# fell through to whatever else their words reached (a drill card, a sofa price). One `s?` on the
# last word of each phrase covers both numbers, and it covers the next noun added to the list too.
TIME_ASK_SHAPE = tuple(re.compile(" " + re.escape(phrase) + "s? ") for phrase in TIME_ASK)

# A bare "when" is as often a relative clause as a question: "my phone gets hot when charging",
# "when it rains" and "when i'm 40" carry the word and ask nothing about the calendar, and the
# phone's calendar row answered the first of those with the month to buy a handset. So when
# "when" is the only time word in the line, one of these asking shapes has to be there too.
WHEN_ASKING = ("when is", "when are", "when was", "when's", "when should", "when shall",
               "when can", "when could", "when do ", "when does", "when did", "when will",
               "when would", "when to buy", "when to get", "when to sell", "when in the year",
               "when is the best", "when is a good", "when is the cheapest")

# "sale" and "cheapest" are the same question with the answer half in it ("when are the sales",
# "when is a mattress cheapest"), but on their own they are just as often "is this price real":
# "is a discount mattress worth it" is a price-history question and the calendar is no answer to
# it, so a price word has to have a time word beside it before the row answers.
PRICE_ASK = ("sale", "sales", "cheapest", "cheaper", "cheap", "discount", "discounts", "deal",
             "deals", "half price")

WHEN_ASK = TIME_ASK + PRICE_ASK

# A bare period is a noun, not a question: "a month", "after 6 months", "next month" say how long
# or when something is paid. But the same period inside a preposition, beside a word of comparing,
# is the comparison turned into a question - "are sofas cheaper in the summer months", "are phones
# cheaper at christmas" - and that is the calendar. So the period names are kept out of TIME_ASK
# and count only in that shape, which is why "my car costs 200 a month, is that cheap" is not a
# when question: nothing sits in front of its period.
PERIOD_NOUNS = ("month", "months", "week", "weeks", "weekend", "weekends", "summer", "winter",
                "spring", "autumn", "christmas", "easter", "season", "seasons", "year", "years")
PERIOD_PREPOSITION = ("in", "at", "over", "during", "for")
COMPARING = ("cheaper", "cheapest", "best", "deal", "deals", "discount", "discounts", "sale",
             "sales", "half price", "price drop", "prices drop")


def _a_period_beside_a_comparison(line):
    """True when a period named after a preposition is being compared: "cheaper in the summer months"."""
    words = line.split()
    if not any(word in COMPARING for word in words) and not any(
            phrase in line for phrase in ("half price", "price drop", "prices drop")):
        return False
    for at, word in enumerate(words):
        if word not in PERIOD_NOUNS:
            continue
        if any(before in PERIOD_PREPOSITION for before in words[max(0, at - 3):at]):
            return True
    return False

# A line can hold a when word and still be about something else: how long a thing lasts, whether
# to repair it, and how to look after it are all "when" lines in shape only. These are the words
# that make it that other question, and the row stands down for them.
NOT_THE_CALENDAR = (
    # "change" is the word people say for replace, and it was the car-buying calendar on
    # "when do i need to change my car oil" and "when should i change my car tyres"
    "replace", "replacing", "replacement", "change", "changes", "changing", "changed",
    "due for", "need a new", "need new",
    # a renewal is a quote with a date on it, not a calendar question about buying the thing:
    # "when do i need to renew my car insurance" was answered "a car is cheapest at the end of a
    # month or a quarter". The insurance rows answer the renewal; the item rows answer the buy.
    "insurance", "insure", "renew", "renews", "renewal", "renewals", "renewing", "policy",
    "policies", "premium", "premiums", "no claims", "auto renew", "auto-renew", "excess",
    "quote", "quotes", "cover", "covers", "mot", "tax", "service", "servicing",
    "last", "lasts", "lasting", "long does", "how often",
    "clean", "cleaning", "wash", "washing", "repair", "repairs",
    "warranty", "guarantee", "return", "refund",
    "delivery", "deliver", "install", "installation", "measure", "measuring", "size", "firm",
    "soft", "cheap one", "second hand", "secondhand", "used", "sell", "selling", "selling my",
    # a thing that is playing up is not a calendar question, and "when" is the only word the two
    # share: "my car takes ages to start when its cold" was answered "a car is cheapest at the
    # end of a month or a quarter". The fault rows own those lines.
    "start", "starts", "starting", "started", "wont start", "takes ages", "takes a while",
    "slow to", "stalls", "stalling", "cut out", "cuts out", "misfire", "flat", "leak", "leaks",
    "leaking", "noise", "noisy", "smell", "smells", "warning light", "dashboard",
    "rid of", "dispose", "tip", "recycle",
    # hiring a van for a move is not the day to buy one: the car row's words include "van", so
    # "when should i book the van" was answered "a car is cheapest at the end of a month or a
    # quarter", which is a different question about a different spend. The hire words are the
    # move's, and cars.van-hire answers them.
    # The bare hires stay out of this list: "hire" on its own is car hire's line, and taking it
    # out of the calendar left "when should i hire a car" with no row at all and "is it cheaper
    # to hire a car" with the removals quote. The move says its own phrases.
    "book the van", "book a van", "book the removals",
    "hire a van", "hire the van", "hiring a van", "hired a van", "van hire", "removals",
    "man with a van", "moving house", "moving flat",
    # running a machine is the hour question, not the calendar: "when is the best time to run
    # the dishwasher" is the tariff row's line, and it was answered "white goods are cheapest on
    # Black Friday". What is bought is not what is switched on.
    # the bare verbs too: "when is the best time to put the washing machine on" takes the item's
    # own words out of the line before this list is read, so the phrase "put on" is no longer
    # contiguous and only the verb is left to see.
    "run", "runs", "running", "put", "turn", "switch", "use", "switch on",
    "switching on", "leave it on", "left on",
    # A part of the thing, or something bought for it, is not the thing: "when should i buy a new
    # laptop battery", "a sofa cover", "a mattress topper" and "a phone contract" are all repair,
    # dressing or tariff questions, and the calendar of the whole object answers none of them.
    "cover", "covers", "topper", "protector", "sheet", "sheets", "battery", "batteries",
    "charger", "case", "spare", "part", "parts", "filter", "filters", "bulb", "bulbs",
    "contract", "sim", "sim only", "upgrade", "pay monthly", "accessory", "accessories",
    # a car seat, a cot and a pram are baby kit, and the car calendar is no answer for them
    "seat", "seats", "car seat", "cot", "cots", "pram", "buggy", "highchair", "pushchair",
    # putting the tree up and taking it down are not buying it
    "take down", "taken down", "taking it down", "put up", "put it up", "putting up", "decorate",
    "decorating", "trim the tree",
    # "is a discount mattress worth it" and "what is a good deal on a phone" ask whether the
    # price is real, and the answer is the price history, not the month: the sale words are in
    # the key, so the price-reality words are what stand the row down and keep it for the person
    # who asks when
    "worth it", "worth the", "worth buying", "good deal", "real deal", "good price", "fair price",
    "good buy", "rip off", "rip-off", "ripoff", "overpriced", "too expensive",
    # a car that wants servicing is the servicing question, not the dealer's calendar month:
    # "when should i get my car serviced" is every 12 months or 10,000 miles, and the end of the
    # quarter is the answer to when to *buy* one
    "service", "serviced", "servicing", "mot", "mot test", "mot due", "service interval",
    "servicing interval",
    # "a bit short this month" is money, not the summer rail: the matcher folds word forms, so
    # the "shorts" of the summer row is the "short" of a tight month, and the time phrase then
    # claimed the turn. "short of money this month", "money is a bit short this month" and "we
    # are short this month" all got the summer-clothes calendar. A line about money being short
    # is the money rows' question, whatever month it names.
    "short this month", "short this week", "short till", "short until",
    "short of money", "short on money", "short of cash", "short on cash", "short of funds",
    "a bit short", "bit short", "money is short", "moneys short", "money's short",
    "money is a bit short", "money is tight", "money is a bit tight", "tight month",
    "running short", "running a bit short",
    # a line about cooking the thing is not a line about the week it is cheap: "what time should
    # i put a chicken in the oven" was the white-goods calendar on the word "oven" alone. The
    # stand-down words here must not name the object, or the row they are for strips them (see
    # _the_care_words, which drops a word the row's own item is spelt with) - so the cooking
    # verbs and what is being cooked, never "oven".
    "cook", "cooks", "cooking", "cooked", "roast", "roasting", "bake", "baking", "baked",
    "defrost", "defrosting", "thaw", "thawing", "preheat", "preheated", "simmer", "boil",
    "boiling", "season", "seasoning", "recipe", "chicken", "turkey", "joint of", "gas mark",
    "degrees", "temperature",
)


# A machine that has failed is a repair or a rights question, not a calendar one, and the words
# people use for the failure are not all "broken": "my washing machine broke after 6 months"
# carried the age ("months"), so the calendar row answered it with the Black Friday price of a
# new one. These are kept apart from the other stand-down words because a line can say both -
# "my fridge died, when should i buy a new one" does want the month - so an explicit buying ask
# outranks the failure.
_HAS_FAILED = ("broken", "broke", "breaks", "breaking", "faulty", "fault", "stopped",
               "not working", "isnt working", "isn't working", "went wrong", "gone wrong",
               "goes wrong", "packed in", "conked out", "died", "dead", "wont start",
               "won't start", "wont spin", "won't spin", "leaking", "months old", "years old")

_BUY_THE_NEXT = ("when should i buy", "when to buy", "when should i get", "when to get",
                 "best time to buy", "when is the best time to buy", "when should i replace",
                 "time to buy a new", "when do i buy", "when can i buy", "when will i buy",
                 "cheapest time to buy")


def _line(understood):
    """The line as words, from the reading, so a row reads the same text the matcher did."""
    reading_ = understood or {}
    text = reading_.get("clean") or reading_.get("norm_text") or ""
    if not text and reading_.get("words"):
        text = " ".join(reading_["words"])
    return " " + str(text).lower() + " "


def _says_it(line, name):
    """True when the line has this word itself, not just a word the matcher's families cover.

    The tables list both forms of everything that comes in two ("tv"/"tvs", "sofa"/"sofas"), so
    asking for the word itself costs nothing. It is here because a family can be a coincidence:
    the family of "telly" is "tell", so "when do i tell work im pregnant" and "when should i tell
    my mum" were answered with the price of a new television. "tell" is not "telly".
    """
    # The plural is the same word as far as this gate is concerned ("when do the sales start for
    # fridges" is the fridge row), so the name and its plural both count.
    forms = {name, name + "s", name + "es"}
    if name.endswith("s"):
        forms.add(name[:-1])
    if any(re.search(r"(?<![a-z])" + re.escape(form) + r"(?![a-z])", line)
           for form in forms):
        return True
    # A mis-typed item is still the item: "when is a matress cheapest" is the mattress calendar
    # question, and requiring the exact spelling sent it to "I don't know enough to answer that
    # honestly". One edit is a slip only on a word long enough for another word not to be the
    # likelier reading, so short names ("tv", "telly", "sofa") stay exact.
    if " " in name or len(name) < 6:
        return False
    for word in line.split():
        word = word.strip(".,!?;:'\"()")
        if len(word) >= 5 and _one_edit_apart(word, name):
            return True
    return False


def _one_edit_apart(typed, name):
    """True when `typed` is `name` with one letter added, dropped or swapped."""
    if abs(len(typed) - len(name)) > 1:
        return False
    if len(typed) == len(name):
        return sum(1 for a, b in zip(typed, name) if a != b) <= 1
    short, long_ = (typed, name) if len(typed) < len(name) else (name, typed)
    return any(long_[:i] + long_[i + 1:] == short for i in range(len(long_)))


def _asks_the_calendar(understood, own=()):
    """True when the line asks when, and is not a how-long/repair/care question wearing a when.

    The row's own item is taken out of the line first: "a washing machine" carries the word
    "washing", which is how a care question is said, and reading it as one would stand the row
    down for every washing-machine line it exists to answer.
    """
    line = _line(understood)
    # The item the row is about has to be in the line as a word. The matcher found the entry
    # through a word family, and a family can reach a line that is about something else.
    if own and not any(_says_it(line, name) for name in own):
        return False
    for name in own:
        line = line.replace(" " + name + " ", " ")
        line = line.replace(" " + name + "s ", " ")
    # a price word is the question only beside a time word: "when are the sales" yes, "is a
    # discount mattress worth it" no - and a line with no time word at all is not this row
    # Whole words only: `_line` pads the line with spaces, and the substring test that used to
    # sit beside this one defeated it - "month" in "a month" is not "what month", and "when" in
    # "whenever" is not an ask either.
    ask = [phrase for phrase in TIME_ASK if phrase in line]
    compared_period = _a_period_beside_a_comparison(line)
    if not (any(shape.search(line) for shape in TIME_ASK_SHAPE) or compared_period):
        return False
    # "when" on its own is the one time word that does not have to be asking anything
    if ask and not [phrase for phrase in ask if phrase != "when"]:
        if not any(phrase in line for phrase in WHEN_ASKING):
            return False
    if (any(phrase in line for phrase in _HAS_FAILED)
            and not any(phrase in line for phrase in _BUY_THE_NEXT)):
        return False
    return not any(phrase in line for phrase in NOT_THE_CALENDAR)


def _avoid_for(own):
    """The care words, less the ones the row's own item is written with.

    "washing machine" is spelt with the word that says a care question ("wash"), and an avoid
    word matches the forms of a word, so a token comparison is not enough: the two are compared
    the way the matcher compares them.
    """
    return tuple(word for word in NOT_THE_CALENDAR
                 if not any(one.startswith(word) or word.startswith(one)
                            for name in own for one in name.split()))


def _whenbuy(reply, own):
    """A calendar row's answer, and None for a line that is not asking the calendar question."""

    def answer(memory, understood):
        if not _asks_the_calendar(understood, own):
            return None
        return reply

    return answer


# The calendar rows. Each is the item, and the reply leads with the weeks it is cheap.
WHEN_TO_BUY = (
    (("mattress", "mattresses"),
     "The January sales and the Black Friday week are when mattresses are marked down, though most "
     "mattress prices are 'on sale' all year, so compare two or three on firmness rather than on "
     "the percentage off. Buy somewhere with a 60-night trial: ten minutes in a shop tells you "
     "little about how you will sleep."),
    (("sofa", "sofas", "settee", "settees", "couch", "couches", "armchair", "armchairs"),
     "Sofas are cheapest in the January sales and over bank holiday weekends, when the chains run "
     "20 to 30 per cent off. A made-to-order sofa takes six to twelve weeks, so for Christmas you "
     "want to order by early November - and check the delivery date in writing rather than the "
     "one on the website."),
    (("tv", "tvs", "television", "televisions", "telly"),
     "Televisions are cheapest on Black Friday and in the January sales, and again in February to "
     "April, when the year's new models arrive and last year's drop a few hundred pounds for the "
     "same panel. If you do not need this year's model, spring is the quiet bargain."),
    (("washing machine", "washing machines", "tumble dryer", "tumble dryers", "fridge",
      "fridge freezer", "freezer", "dishwasher", "oven"),
     "White goods are cheapest on Black Friday and in the January sales, and the January price on "
     "last year's model usually beats the Black Friday one. Measure the gap and the doorway "
     "before you buy, and check the energy rating: over ten years the running cost matters more "
     "than the purchase price."),
    (("laptop", "laptops", "computer", "computers", "tablet", "tablets"),
     "Laptops and tablets are cheapest on Black Friday, in the January sales, and in the "
     "back-to-school weeks of late August when the makers push student models. A machine whose "
     "replacement has just launched drops the most, so check whether a newer model is out."),
    (("phone", "phones", "mobile", "mobiles", "iphone", "smartphone", "smartphones"),
     "The cheapest month for last year's phone is the one after the new model lands, which is "
     "usually late September to November, and Black Friday adds a further cut. Buying outright "
     "and keeping it four years is nearly always cheaper than the annual upgrade."),
    (("car", "cars", "van", "vans", "motorbike", "motorbikes"),
     "A car is cheapest at the end of a month or a quarter, when a dealer is chasing a sales "
     "target and will move on price, and in the quiet weeks of August and late December. New "
     "plates in March and September make the previous plate's stock cheaper, and a pre-registered "
     "car saves the most of all - just check you are the first registered keeper."),
    # The bare "boots" answered "cheap football boots" with the January sales on winter coats,
    # because a price word and a boot was enough for the calendar. A boot for a pitch and a boot
    # for the snow are two different spends, and only the winter one is a season's end.
    (("coat", "coats", "winter coat", "winter coats", "jacket", "jackets", "winter boots",
      "wellingtons",
      # a ski boot is a winter boot and it is bought in the same January clear-out. Without this
      # the baby-shoe row took "when to buy ski boots" and answered barefoot indoors.
      "ski boots", "ski boot", "skiing", "ski", "snowboard", "snowboarding"),
     "Winter coats and boots are cheapest in the January sales and at the end of the season in "
     "February, when the shops clear the rails for spring. Buy then for next winter, and buy the "
     "best you can afford: a waterproof shell at the higher price outlasts three cheap ones."),
    (("summer clothes", "holiday clothes", "swimwear", "swimsuit", "sandals", "shorts", "sunglasses"),
     "Summer clothes, swimwear and sandals are cheapest in August and early September, when the "
     "shops clear them out for knitwear, so late summer is the moment for next year's holiday. "
     "Sizes go first, so go early in the clearance rather than at the end of it."),
    (("garden furniture", "barbecue", "barbecues", "bbq", "patio", "parasol", "sun lounger"),
     "Garden furniture and barbecues are cheapest at the end of August and in September, when the "
     "season ends and the garden ranges go on clearance - but the choice is picked over by then. "
     "Buy late for price, or in March for choice."),
    (("bike", "bikes", "bicycle", "bicycles"),
     "Bikes are cheapest in September and October as the season ends, and again when next year's "
     "models arrive and the old ones are cleared. A last-year model with the same frame is the "
     "bargain worth having."),
)

# The general question with no item in it: "when are the sales", "when is the best time to buy
# things". One short calendar, because the honest answer is that the year has four sale seasons.
SALES_CALENDAR = (
    "The big retail sales are the January sales (from Boxing Day to the end of January), the "
    "Black Friday week at the end of November, the Easter and August bank holiday weekends, and "
    "the end-of-season clearances - summer things in August, winter things in January and "
    "February. January and Black Friday are the deepest cuts, and the item you want most is the "
    "one worth waiting for rather than buying on impulse at a weaker sale."
)


def _general_sales(memory, understood):
    """The whole-year calendar, for a line that asks when things are on sale and names no item."""
    if not _asks_the_calendar(understood):
        return None
    return SALES_CALENDAR


def _christmas(memory, understood):
    """A tree is bought in December; the decorations are bought in the January after.

    Both are the same calendar question and the opposite answer, so the line leads: "when should
    i buy a christmas tree" is mid-December, "when are decorations cheapest" is the first week of
    January, and a line that names neither gets both halves in that order.
    """
    if not _asks_the_calendar(understood):
        return None
    line = _line(understood)
    # putting it up and taking it down are the two things people do with a tree that are not
    # buying one, and neither is a calendar question about a price
    doing = any(one in line for one in (" take ", " taken ", " taking ", " put ", " putting ",
                                        " pack ", " packing ", " throw ",
                                        # "when does the christmas tree go up" is the putting-up
                                        # question, and main answers it; only "go up" about a
                                        # price belongs to the calendar, and a price line is not
                                        # a line about a tree
                                        " go up ", " goes up ", " going up ", " gone up ",
                                        " come down ", " comes down ", " coming down "))
    gone = any(one in line for one in (" down ", " up ", " away ", " out "))
    if doing and gone:
        return None
    tree = any(one in line for one in ("tree", "trees", "real tree", "fir"))
    lights = any(one in line for one in ("light", "lights", "fairy", "decorations", "baubles",
                                        "tinsel", "ornaments"))
    if tree and not lights:
        return ("Buy a real tree in mid-December, a week or two before Christmas: a tree cut in "
                "November drops its needles by the big day, so ask the grower when it was cut and "
                "keep it in water. Artificial trees are cheapest in the January sales, so buy the "
                "one you want now and store it.")
    if lights and not tree:
        return ("Christmas lights and decorations are cheapest in the first week of January, at 70 "
                "to 90 per cent off, so buy for next year on the 2nd or 3rd rather than in "
                "November, when the same set is full price.")
    return ("Buy a real tree in mid-December, a week or two before Christmas, from a grower who "
            "will tell you when it was cut; lights and decorations are cheapest in the first week "
            "of January, at 70 to 90 per cent off, for next year.")


ENTRIES = [
    entry("whenbuy-" + words[0].replace(" ", "-"), (words, WHEN_ASK), _whenbuy(reply, words),
          # the choosing rows in the shopping domain answer the object, this row answers the
          # calendar: a line that asks when is not a line about firmness, warranty or the
          # energy rating, so the row stands down for those words
          avoid=_avoid_for(words),
          # A place is not a month. "where is the cheapest place to buy a fridge" and "where can
          # i buy a cheap dishwasher" carry a price word this row is keyed on, so the calendar
          # answered them - a fridge line with a mattress line's January sales, a dishwasher with
          # a washing machine - while the buying answer sat one row below. The guard is the
          # reading's own where plus a thing the price answer is written for, so a place question
          # about such a thing never reaches a calendar row.
          guard=lambda understood: not asks_where_a_shop_answers(understood),
          # "when is the best time to buy a mattress" fits the mattress choosing row as well as
          # this one, and the calendar is the narrower question: the choosing row is still the
          # answer to "which mattress" and to "how long does one last".
          bias=2)
    for words, reply in WHEN_TO_BUY
] + [
    # the tree and the decorations are the same question with opposite answers, and a bare
    # "tree" is a garden question: only the Christmas words are here.
    entry("whenbuy-christmas", (("christmas tree", "christmas trees", "christmas decorations",
                                "christmas lights", "decorations", "fairy lights", "tinsel",
                                "baubles", "ornaments"), WHEN_ASK), _christmas,
          avoid=_avoid_for(("christmas tree", "christmas decorations")),
          guard=lambda understood: not asks_where_a_shop_answers(understood), bias=2),
    entry("whenbuy-sales-calendar",
          (("sale", "sales", "bargains", "discounts", "deals", "black friday", "january sales",
            "clearance", "reductions", "price cuts"),
           ("when", "what month", "which month", "when are", "time of year", "this year",
            "next month", "coming up")),
          _general_sales),
]
