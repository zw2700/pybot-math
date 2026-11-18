"""Buying things: laptops, shoes, bikes, mattresses, gifts and whether a deal is real.

The answers lane owns this domain. Each Entry says what actually matters when choosing,
in the order it matters, and what to check before handing over money.
"""
import re

from ..compose import pick
from ..memory import newborn, people
from ..understanding import topics as reading
from .lookup import (PRESENT_ASK, PRICE_COMPARED, a_food_is_being_kept, a_price_not_a_loan,
                     about_them, asks_where, asks_where_a_shop_answers, entry)

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("shopping", "money", "technology")


_GIFT_ANYONE = ("Buy into what they already do: a good version of something they use every "
                "week (a proper kitchen knife, warm socks, decent coffee), a voucher for a place "
                "they go anyway, or a day out the two of you share. Tell me what they do at the "
                "weekend and I'll narrow it down.")


# A person the chat has already talked about, and a taste of theirs. When both are on file the
# gift answer that knows them should keep the turn: "its my mums 80th next month | she loves
# gardening | what could i get her" belongs to the gardening entry, and this generic one was
# taking it and asking what she does at the weekend the chat had just said.
PERSON_WORDS = frozenset("""mum mother dad father sister brother nan nana grandma grandad granny
    son daughter wife husband partner friend mate flatmate boyfriend girlfriend colleague aunt
    uncle cousin stepmum stepdad he she they him her his hers their stepmother stepfather""".split())
TASTE_WORDS = frozenset("""loves love likes like enjoys enjoy keen into fond obsessed collects
    plays does goes went favourite favorite hobby hobbies garden gardening cooks cooking bakes
    baking fishing reads reading runs running knitting sewing cycling walking football music
    books films plants allotment""".split())


# How people write a person and a taste: "my mums birthday", "shes into gardening", "my sister
# loves it". The list holds the plain word, so a plural, a possessive or a contraction has to come
# back to it, or "shes into gardening" says no taste at all and the cold card answers a chat that
# just said what she likes.
_FOLD = (("'s", ""), ("s'", ""), ("s", ""), ("'", ""))


# Where each shop sits on price, kept as data: a shop named in the line is looked up here rather
# than by a keyword list per shop, so one row answers every "is X cheaper than Y" shape. The ranks
# are the order of a like-for-like basket of own-brand staples, cheapest first; prices move month
# to month, which is why the answer says where each shop sits rather than quoting a figure.
# name, the ways people type it, the rank, what it is in a sentence, why it sits there, and how to
# say it next to a shop it is being compared with.
SUPERMARKETS = (
    ("Aldi", ("aldi",), 0, "the cheapest of the big names",
     "own-brand staples run roughly a fifth less than at Tesco or Sainsbury's, on a smaller range "
     "with few named brands",
     "has the cheaper staples and a smaller range"),
    ("Lidl", ("lidl",), 0, "one of the two cheapest of the big names",
     "own-brand staples run roughly a fifth less than at Tesco or Sainsbury's, with a strong "
     "bakery and few named brands",
     "is level on price and stronger on the bakery"),
    ("Farmfoods", ("farmfoods",), 0, "cheap for frozen food",
     "the frozen and branded boxes are cheap and the fresh food is thin",
     "is cheaper on frozen and thinner on fresh"),
    ("Asda", ("asda",), 1, "usually the cheapest of the big four",
     "a like-for-like basket comes out cheapest at Asda, and it price-matches Aldi and Lidl on "
     "the basics",
     "price-matches Aldi on the basics and runs more brands"),
    ("Iceland", ("iceland",), 1, "cheap for frozen food",
     "frozen and ready meals are cheap and everything else is dearer",
     "is cheaper on frozen and dearer on the rest"),
    ("Morrisons", ("morrisons", "morrison"), 2, "mid-priced",
     "it sits with Tesco and Sainsbury's, and is often the cheapest of the big four on fresh meat "
     "and fish",
     "is close on price with better fresh meat and fish"),
    ("Tesco", ("tesco", "tescos"), 2, "mid-priced",
     "its Aldi Price Match holds the basics at Aldi's price, and the rest of the basket costs more",
     "holds the basics at Aldi's price and costs more for the rest"),
    ("Sainsbury's", ("sainsburys", "sainsbury's", "sainsbury"), 2, "mid-priced like Tesco",
     "the basics are price-matched to Aldi and the brands are what cost more",
     "matches the basics and costs more for the brands"),
    ("Ocado", ("ocado",), 3, "M&S food delivered",
     "it is priced like M&S rather than like a discounter",
     "is priced like M&S"),
    # "co-op" is two words by the time a row reads the line ("co", "op"), so both spellings are
    # here: "is co-op expensive" reached no row at all until the spaced one was
    ("The Co-op", ("co-op", "co op", "coop", "co operative", "cooperative"), 3, "a convenience shop",
     "it is dearer than the big four on almost everything, so it is a top-up shop",
     "is dearer, which is what the convenience buys"),
    ("Waitrose", ("waitrose",), 4, "one of the two dearest",
     "it runs around 10-20% more than Tesco on the same basket, and the fresh food is better",
     "costs more and is better on fresh food"),
    ("M&S", ("marks and spencer", "marks spencer", "m and s", "m&s", "marks & spencer"), 4,
     "the dearest of the big names",
     "it runs around 10-20% more than Tesco on the same basket, and the ready meals are why "
     "people go",
     "costs more, and the ready meals are why people go"),
)

_CHEAPEST_TAIL = (" It is one of the cheapest places to do a full shop, though the range of "
                  "brands is smaller, so anything specific may need a second stop.")
_MIDDLE_TAIL = (" The basics are price-matched to the discounters, so it is the brands in the "
                "trolley that make the difference: a basket of own-brand staples will be cheaper "
                "at Aldi or Lidl.")
_DEAR_TAIL = (" For a cheaper basket on the same list, the discounters save around a fifth and "
              "Asda or Tesco most of the rest.")


_QUALITY_WORDS = ("good", "quality", "as good", "better", "worse", "taste", "tasty", "nicer",
                  "fresh")


def _supermarket_quality(named):
    """How shops compare on quality, which is a different answer from how they compare on price.

    Each shop's own line from the table leads, because "is farmfoods any good" is about frozen
    food and a thin fresh range rather than about the rank, and no card here names its own list of
    staples: the coeliac rewrite in `cooking.py` turns a listed "pasta" into "gluten-free pasta",
    which would have this row claim the discounters sell the same food as everyone else.
    """
    named.sort()
    if len(named) >= 2:
        cheap, dear = named[0], named[-1]
        if cheap[0] < dear[0]:
            return ("On quality they are close on the staples: most own-brand basics are made in "
                    "the same "
                    "factories as the named ones, so the store cupboard is the same food under a "
                    "different label. It shows in the fresh food and the range - %s %s, where %s "
                    "%s. For a full shop the cheaper one is fine; for a specific ingredient, or "
                    "for a weekend meal, the dearer one earns it." %
                    (cheap[1], cheap[4], dear[1], dear[4]))
        return ("On quality they are closer than on price: the basics are the same food under a "
                "different label, so what you pay for is the fresh food and the range - %s %s, "
                "and %s %s." % (cheap[1], cheap[4], dear[1],
                                 _without_the_same_opening(cheap[4], dear[4])))

    rank, name, sentence, why, contrast = named[0]
    # The tail never names what the row's own `why` has already named: the first version said
    # "the ready meals" after M&S's `why` had said it, and "the brands are thin" after Farmfoods'
    # had said that, so the card read as though it were repeating itself.
    if rank >= 4:
        return ("%s is %s: %s. The extra money goes on the parts of the shop the staples do not "
                "cover, not on the basics, which are the same items under a different label, so a "
                "full shop there costs more for much the same basket." % (name, sentence, why))
    if rank <= 1:
        return ("%s is %s: %s. None of that makes the staples worse: most own-brand basics come "
                "from the same factories as the named ones, so the saving is on the same food, and "
                "a basket built on ingredients rather than ready-made versions of them misses the "
                "weakest part." % (name, sentence, why))
    if rank == 3:
        # Ocado and the Co-op are not price-matched to anyone, so the middle sentence's
        # "price-matched price" would be a claim about them that is not true, and what the extra
        # buys there is the delivery and the hours
        return ("%s is %s: %s. Much the same as the rest on quality: the basics are the same "
                "items, and what the extra buys is convenience." % (name, sentence, why))
    return ("%s is %s: %s. Much the same as the rest on quality: the basics are the same items at "
            "a price-matched price, and what it adds is range and fresh food." %
            (name, sentence, why))


# A range is not a price. "is aldi good for gluten free" and "is waitrose good for organic" ask
# what a shop stocks, and a verdict on the basket is an answer to a different question. The row's
# own `avoid` holds these words, but in a chat the module hands a follow-up straight to the entry
# that answered the turn before, without scoring the new line again, so the guard has to stand
# inside the reply too - and against the line the person just typed, not the reading it was
# carried on.
_RANGE_WORDS = ("gluten", "free from", "free-from", "freefrom", "vegan", "vegetarian",
                "dairy free", "dairy-free", "nut free", "nut-free", "allergy", "allergies",
                "allergic", "coeliac", "celiac", "organic", "halal", "kosher", "good for",
                "fine for", "ok for", "okay for", "any good for", "better for", "stock",
                "stocks", "sell", "sells", "range of", "own brand")


def _without_the_same_opening(first, second):
    """The second shop's clause with the words the first has already used taken off the front.

    Two shops on the same rank both "cost more", so the sentence said it twice ("M&S costs more,
    and the ready meals are why people go, and Waitrose costs more and is better on fresh food").
    """
    for lead in ("costs more, and ", "costs more and ", "costs more, ", "costs more "):
        if first.startswith("costs more") and second.startswith(lead):
            return second[len(lead):].strip()
    return second


# The same name sells groceries and half a dozen other things. "is tesco mobile any good" and
# "does tesco bank do a good current account" were answered with "Tesco is mid-priced: its Aldi
# Price Match holds the basics at Aldi's price", which is the grocery basket and not the thing
# asked about. A shop's name is not a subject on its own: only the basket is.
_SERVICE_WORDS = ("mobile", "broadband", "internet", "wifi", "phone", "phones", "sim", "sim only",
                  "telly", "tv", "bank", "banking", "current account", "savings account",
                  "insurance", "insure", "credit card", "loan", "mortgage", "tariff", "energy",
                  "gas and electric", "electricity", "petrol", "diesel", "fuel", "travel money",
                  "currency", "holiday", "holidays", "package holiday", "phone contract")


def _a_service_not_a_basket(line):
    """True when the line is about something a shop sells besides food."""
    return any(word in line for word in _SERVICE_WORDS)


def _the_turn_just_typed(memory):
    """The words of the line the person has just sent, whatever reading carried the entry here."""
    from ..memory import recent

    turns = recent(memory, 1)
    return str(turns[-1].get("user") or "") if turns else ""


_SHOP_ASK = ("should", "shall", "would", "worth", "better", "cheaper", "cheapest", "which",
             "what about", "instead of", "or ", "vs", "versus", "good", "decent", "ok")


def _a_statement_about_where_i_shop(typed):
    """True when the line just says where they shop, with no question about it.

    "i shop at asda" and "i do my shopping at asda" are the two ways people tell you their shop,
    and both were answered with a price card ("Tesco is mid-priced"). A question in front of the
    same words - "should i shop at asda or tesco", "is asda good for the weekly shop" - has one of
    the asking words in it, and that is the whole difference.
    """
    if not any(phrase in typed for phrase in ("i shop at", "i shop in", "i get my shopping")):
        return False
    return not any(word in typed for word in _SHOP_ASK)


def _supermarket_cheapest(memory, understood):
    """Where the shops named in the line sit on price, or None when the line names none."""
    typed = _the_turn_just_typed(memory).lower()
    if any(word in typed for word in _RANGE_WORDS):
        # what a shop stocks is not where its prices sit
        return None
    # only what this line said names a shop: the reading folds the last turn's words into
    # `words` for a follow-up, so a "so where should i do the big shop" after a two-shop question
    # was told the tie sentence about shops it had not mentioned. With no shop named here, the
    # no-shop ranking is the right answer and it does say where to go
    line = _said_line(understood).lower().replace("\u2019", "'")
    if any(word in line for word in _RANGE_WORDS):
        return None
    if _a_service_not_a_basket(line):
        return None
    if _a_statement_about_where_i_shop(line):
        # "i shop at asda" is telling you something, not asking which shop is cheaper; the
        # same words behind "should i" or "shall i" are the question, and an asking word in the
        # line is the whole difference. This reads `line`, the reading's own text, and not the
        # turn before it: on a follow-up ("i shop at asda" -> "is that expensive") the words the
        # new turn leans on are the ones in hand, and the new turn is a question.
        return None
    named = []
    for name, spellings, rank, sentence, why, contrast in SUPERMARKETS:
        if any(spelling in line for spelling in spellings):
            named.append((rank, name, sentence, why, contrast))
    if named and any(word in line for word in _QUALITY_WORDS):
        return _supermarket_quality(list(named))
    if not named:
        return ("Aldi and Lidl are the cheapest of the big names for own-brand staples, around a "
                "fifth less than Tesco or Sainsbury's. Asda is usually the cheapest of the big "
                "four, Morrisons, Tesco and Sainsbury's come next and price-match Aldi on the "
                "basics, and Waitrose and M&S are the dearest. A convenience shop - the Co-op, a "
                "corner shop - costs more again, so it is for a top-up, not the weekly shop.")
    named.sort()
    if len(named) >= 2:
        cheap, dear = named[0], named[-1]
        if cheap[0] == dear[0]:
            # a tie is its own sentence: welding one shop's "it sits with Tesco" onto the other
            # shop's name read as though Sainsbury's were a third shop
            return ("%s and %s are level on price, so pick on what you cook: %s %s, and %s %s. "
                    "Go to whichever is nearer." %
                    (cheap[1], dear[1], cheap[1], cheap[4], dear[1], dear[4]))
        return ("%s is the cheaper of the two: %s. %s %s." %
                (cheap[1], cheap[3], dear[1], dear[4])) + (
                " Check the price per 100g on the shelf label rather than the pack size, because "
                "the price match only covers the basics." if cheap[0] >= 2 else "")
    rank, name, sentence, why, contrast = named[0]
    tail = _CHEAPEST_TAIL if rank <= 1 else _MIDDLE_TAIL if rank == 2 else _DEAR_TAIL
    return "%s is %s: %s.%s" % (name, sentence, why, tail)


def _fold(word):
    """The word as the lists spell it, with a plural, a possessive or a contraction taken off."""
    if word in PERSON_WORDS or word in TASTE_WORDS:
        return word
    for cut, join in _FOLD:
        if word.endswith(cut) and word[: -len(cut)] + join in PERSON_WORDS | TASTE_WORDS:
            return word[: -len(cut)] + join
    return word


def _the_words(line):
    """The words of a line as the person and taste lists spell them."""
    return {_fold(word) for word in re.findall(r"[a-z']+", str(line or "").lower())}


def _said_line(understood):
    """The line being answered, as text: the reading carries it, and an entry only gets the dict."""
    if not isinstance(understood, dict):
        return ""
    return str(understood.get("text") or understood.get("clean") or "")


def _knows_a_taste(memory, understood=None):
    """True when a line said who the person is and something they like, this one or a recent one."""
    from ..memory import recent

    lines = [str(turn.get("user") or "") for turn in recent(memory, 8)]
    said = _said_line(understood)
    if said:
        lines.append(said)
    for line in lines:
        words = _the_words(line)
        if words & PERSON_WORDS and words & TASTE_WORDS:
            return True
    # Not "a hobby in one line and a relation in another": "ive got into gardening | what should i
    # get my mum" is the asker's own hobby, and reading it as the mother's is worse than the cold
    # card. A pronoun carries the person ("shes into gardening"), and a relation carries it ("my
    # sister loves gardening"), so one line holding both is the signal.
    return False


# A tenner buys two different lists. Grown-ups get the good version of something they already
# use; children get something they can open and play with before lunch. The words are only read
# here, so a stocking filler at an office secret santa keeps the adult list.
CHILD_WORDS = ("kid", "kids", "child", "children", "childrens", "childs", "toddler", "toddlers",
               "baby", "babies", "boy", "boys", "girl", "girls", "teenager", "teenagers", "teen",
               "teens", "grandchild", "grandchildren", "grandson", "granddaughter", "niece",
               "nephew", "son", "sons", "daughter", "daughters", "school age", "year old",
               "year old")

CHEAP_ADULT = (
    "Spend it on something consumable and a notch better than the everyday: a good candle, "
    "decent coffee or tea, a nice bar of chocolate, a scratch card, seeds and a pot, a "
    "paperback you would actually recommend, or a really good pair of socks. £10 goes a "
    "long way on any of those and nothing needs a size or a taste test; if the group has a "
    "joke running, a silly gift that gets a laugh beats an expensive one that gets a polite "
    "smile. Keep the receipt.")

CHEAP_CHILD = (
    "For a child, spend it on things they use up or grow out of: bubble mix, a big sticker book, "
    "a colouring pad with good pens, bath crayons, play dough, a torch, a pack of cards, or a "
    "small Lego set on offer. Nothing needs a size and batteries are the only trap, so check the "
    "box. Socks, gloves and a book they will actually read are the safe last-minute ones.")


CHEAP_TEEN = (
    "For a teenager, a tenner is best spent on one thing they pick themselves: a voucher for the "
    "cinema or a shop they already use, phone credit, decent earphones or the cable they keep "
    "losing, or a game they can play with friends. Ask what they are into and buy the small "
    "version of that: the money goes further on one thing they want than on three they do not.")


def _gift_cheap(memory, understood):
    # The age is read before the words of the line, because a named relation says nothing about
    # how old the person is: "my niece is 15 in july" then "cheap present ideas for my niece" was
    # the child list - bath crayons and play dough for a fifteen-year-old - since this row read
    # the word "niece" and never the age the chat had already given it.
    age = _an_age_in_the_line(understood)
    if age is None:
        age = people.the_age_of_the_person_they_mean(memory, understood)
    if age is not None:
        if age < 13:
            return CHEAP_CHILD
        if age < 20:
            return CHEAP_TEEN
        return CHEAP_ADULT
    clean = understood.get("clean") or ""
    for word in CHILD_WORDS:
        if re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", clean):
            return CHEAP_CHILD
    return CHEAP_ADULT

def _the_tastes(memory, understood=None):
    """The hobbies the chat named, as INTEREST_GIFTS spells them, newest line first.

    The last few lines and the reading's own subject both count: "shes into gardening" a turn
    before the ask is what makes "what should i get her" a question about a gardener, and a line
    that names the hobby itself ("a present for someone into fishing") is the same fact.
    """
    from ..memory import recent

    said = []
    lines = [str(turn.get("user") or "") for turn in recent(memory, 4)]
    here = _said_line(understood)
    if here:
        lines.append(here)
    for turn in reversed(lines):
        # The newest line that names a hobby is the person in hand: "my dad is into fishing" then
        # "what should i buy him" is a present for a fisherman, and the gardening two lines up is
        # somebody else in the same chat.
        for word in re.findall(r"[a-z']+", turn.lower()):
            name = _fold(word)
            for candidate in (name, name + "ing"):
                if candidate in INTEREST_GIFTS and candidate not in said:
                    said.append(candidate)
        if said:
            return said
    return said


def present_known(interests=(), memory=None, understood=None):
    """A present for a taste the chat already told us, with no price named.

    The picks come from INTEREST_GIFTS, the same table the budget answers read, so one row here
    covers every hobby in it instead of a row per hobby: the point of the answer is that it names
    the thing they do rather than a safe list that would suit anyone. The sentence is written the
    way the person rows are, with `about_them` sorting out he, she or they from the line.
    """
    wanted = _interest_phrase(interests)
    picks = []
    for interest in interests or ():
        for item, price in INTEREST_GIFTS.get(str(interest).lower(), ()):
            if item not in [name for name, _ in picks]:
                picks.append((item, price))
    if not picks:
        return None
    picks.sort(key=lambda pair: pair[1])
    named = ["%s (%s)" % (item, _money(price)) for item, price in picks[:3]]
    listed = named[0] if len(named) == 1 else ", ".join(named[:-1]) + " or " + named[-1]
    sentence = ("For someone into %s: %s. Buy the one {they} will actually use rather than three "
                "{they} might, and put a real message in the card." % (wanted, listed))
    if memory is None and understood is None:
        return sentence
    return about_them(sentence)(memory or {}, understood or {})


# A limit in the line: the money rows answer that one and name the figure.
PRICE_SAID = re.compile(r"\u00a3|\d+\s*(?:pounds?|quid)\b|\bunder\s+\d|\bbudget\b", re.IGNORECASE)
# The same question without a figure in it: "cheap present ideas for my nephew" asks what a tenner
# buys as surely as "under a tenner" does, and it is the cheap-gift row that knows both lists.
# "is that a weird gift" asks whether a present is a good one, not for a list of presents: a row
# that answers it with the list it has just given is repeating itself at a question it did not
# read. The verdict is somebody else's turn, so these rows stand down.
A_VERDICT_WORD = (r"(?:weird|odd|tacky|rude|appropriate|all\s+right|ok|okay|too\s+much|"
                  r"too\s+little|too\s+expensive|too\s+cheap|wrong|enough|worth\s+it|"
                  r"worth\s+the\s+money|a\s+good\s+(?:present|gift|idea)|"
                  r"a\s+bad\s+(?:present|gift|idea))")
A_VERDICT_ON_A_PRESENT = re.compile(
    r"\b(?:is|would|will|was)\s+(?:(?:that|it|this|a|an|my|the)\s+)?[^?.!]{0,40}?"
    r"\b" + A_VERDICT_WORD + r"\b", re.I)

# The thing a verdict is about: "would a scooter be too much" names the scooter between the verb
# and the verdict, and it is that thing the answer has to be about.
A_VERDICT_THING = re.compile(
    r"\b(?:is|would|will|was)\s+(?:(?:that|it|this)\s+)?"
    r"([^?.!,]{2,30}?)\s+(?:be\s+)?(?:" + A_VERDICT_WORD + r")\b", re.I)

# A verdict ask about a present the store already put on the table is answered, not repeated:
# "my nephew is 5 in june" / "what can i get them" / "would a scooter be too much" was told
# "Everything about a scooter is in what I said above", which is the list again in other words.
# When the thing named is one of the picks for the age the chat holds, the honest answer is yes,
# with the one thing that matters about it: at that age the cheap one is the right one anyway.
VERDICT_YES = (
    "No, that is a good pick at {age}: {thing} gets used every day, and the plain one with room "
    "to grow beats the flashy one.",
    "Not at all - at {age} {thing} is exactly the kind of present that gets used. Plain and "
    "sturdy is the right call there.",
    "That sounds right to me: at {age}, {thing} is a good present, and asking the parents what "
    "they already have too much of saves you buying the second one.",
)
# Money is what "too much" usually means, so a verdict with a price in it is answered about the
# spend rather than about the taste: "would the scooter be too expensive" is a person weighing a
# present against their wallet, not asking whether a five-year-old likes scooters.
MONEY_VERDICT_YES = (
    "No need to spend much: at {age} {thing} is a good present, and the plain one is the one that "
    "gets used, so the extra money buys nothing the child will notice.",
    "No, and cheap is right here: at {age} {thing} gets used hard, and the basic version lasts as "
    "long as the expensive one.",
)
A_VERDICT_ABOUT_MONEY = re.compile(
    r"\b(?:too\s+expensive|too\s+cheap|expensive|cost|costs|price|pricier|worth\s+it|spend|"
    r"spending|afford|afford\s+it)\b", re.I)
# A card is not a present, and the turn after a present list is very often about the card: "my
# nephew is 5 in june" / "what can i get them" / "and what about a card" was told the present list
# again, under a "Same as before" lead, and the turn ended on a search punt. A card has its own
# answer and it is the same answer whoever the present was for.
A_CARD_IS_NOT_A_PRESENT = re.compile(
    r"\bcard(?:s)?\b", re.I)
# A card that is not the card you write in: a bank card, a SIM, a memory card, a store card. The
# line after a present list that says one of these is about the money or the phone, not the
# present, so the card words are not its answer.
NOT_THAT_CARD = re.compile(
    r"\b(?:bank|debit|credit|sim|sd|memory|store|loyalty|id|payment|graphics|smart|gift)\s*"
    r"cards?\b|\bcard\s+(?:declined|blocked|number|details|payment|reader|machine)\b", re.I)
CARD_AFTER_A_PRESENT = (
    "The card is the part people keep: two lines in your own words - one thing they did that you "
    "still think about, and a wish - beats anything printed inside it.",
    "A card is worth the five minutes. One specific line about them, no joke off the shelf, and "
    "your name at the bottom, because that is the bit they keep.",
    "Write the card yourself rather than signing a printed one: name the thing you like about "
    "them and what you hope for them, and stop there.",
)


def the_card_after_a_present(understood, memory=None, line=None):
    """The words for the card, when the turn after a present list asks about the card.

    The line typed is read in preference to the reading, because on a follow-up the reading can
    be the earlier line the turn leans on: "and what about a card" after a present ask arrives
    here as "what can i get them", which names no card at all.
    """
    said = line if isinstance(line, str) and line.strip() else _said_line(understood)
    if not A_CARD_IS_NOT_A_PRESENT.search(said or "") or NOT_THAT_CARD.search(said or ""):
        return None
    return pick(CARD_AFTER_A_PRESENT, memory or {}, said)


A_CHEAP_ASK = re.compile(
    r"\b(?:cheap|cheaper|cheapest|inexpensive|budget|tenner|fiver|stocking\s+fillers?|"
    r"stocking\s+filler|secret\s+santa|small\s+gifts?|small\s+presents?|little\s+gifts?|"
    r"under\s+a\s+(?:tenner|fiver|ten|five))\b", re.I)


# A present for somebody with a condition is still a present: "what should i get my sister who
# doesnt drink alcohol" was told the weekly units limit, "gift for my brother whos vegetarian" got
# a chickpea curry and "present for someone with a nut allergy" got the nut-free dinner list. The
# condition describes the person, not the thing to cook or the limit to keep, so the gift rows take
# the line and say what the condition changes about the pick. One table, read by every gift row.
GIFT_FOR_A_CONDITION = (
    # (the words that say it, the sentence to add, and what an answer must not go on recommending)
    (("doesnt drink", "doesn't drink", "does not drink", "not drinking", "non drinker",
      "non-drinker", "nondrinker", "teetotal", "teetotaller", "sober", "given up drinking",
      "given up alcohol", "gave up drinking", "stopped drinking", "off the drink",
      "no alcohol", "cant drink", "can't drink", "cannot drink", "not a drinker"),
     "Keep the alcohol out of it, even in a hamper: a good alcohol-free bottle (Lyre's or "
     "Seedlip), a proper coffee or a loose-leaf tea set, or a voucher for a meal out.",
     ("a decent bottle of what he already drinks, ",
      "a decent bottle of what he already drinks",
      "a little of something she loves to eat, ",
      "a bottle of what she already drinks, ")),
    (("vegetarian", "veggie", "vegan", "plant based", "doesnt eat meat", "doesn't eat meat",
      "no meat", "pescatarian"),
     "And buy into the vegetarian side of it: a good vegetarian cookbook, a voucher for a veggie "
     "restaurant, or a decent olive oil and a spice set rather than a hamper of pate.",
     ()),
    (("diabetic", "diabetes", "on a diet", "dieting", "watching sugar", "no sugar",
      "cutting out sugar", "blood sugar"),
     "Keep the sugar out of it: no chocolates or biscuit hamper - a magazine or audiobook "
     "subscription, or something for a hobby they already have, works better.",
     ("chocolates", )),
    (("coeliac", "celiac", "gluten free", "gluten-free", "dairy free", "dairy-free",
      "lactose", "allergy", "allergic", "allergies", "nut allergy", "intolerance"),
     "And nothing that might hold what they cannot eat: a voucher, a plant, or something for a "
     "hobby beats a hamper or a box of chocolates.",
     ()),
)


def not_a_present(understood):
    """False when the line is asking what to give somebody, so a condition row stands down.

    Public: the rows a condition word also reaches - the weekly alcohol limit, the vegetarian
    dinner, the nut-free list - carry `guard=not_a_present`, because "present for someone with a
    nut allergy" is a present and not a dinner.
    """
    return not reading.gift_ask(understood)


# The people a line can name. A condition said two turns ago belongs to whoever that turn named,
# so it is only carried to a present ask that names nobody ("what should i get her"): "my dad is
# diabetic" followed by "what should i get my sister" is the sister's present.
_PRESENT_PEOPLE = ("mum", "mom", "mother", "dad", "father", "sister", "brother", "son", "daughter",
                   "wife", "husband", "partner", "grandad", "grandma", "nan", "granny", "aunt",
                   "uncle", "cousin", "friend", "mate", "colleague", "coworker", "boss",
                   "neighbour", "neighbor", "teacher", "carer", "nurse", "stepmum", "stepdad",
                   "boyfriend", "girlfriend", "teenager", "child", "baby")


def _the_condition_in(text):
    """(the sentence to add, the phrases to take back out) for a condition named in this text."""
    text = " " + str(text or "").lower() + " "
    for phrases, sentence, drop in GIFT_FOR_A_CONDITION:
        if any(phrase in text for phrase in phrases):
            return sentence, drop
    return None


def _the_condition_gift(understood, memory=None):
    """What the person's condition changes: the sentence to add, and what to take back out.

    A present for somebody who has given up drinking must not go on to recommend a bottle, so the
    table carries the phrases an answer says that the condition rules out.

    The condition is often said a turn earlier - "my mum has just given up drinking", then "what
    should i get her for christmas" - so the last two things the person said are read as well, but
    only for a line that names nobody: a line naming its own person is that person's present.
    """
    line = str(_said_line(understood) or "")
    found = _the_condition_in(line)
    if found is None:
        low = " " + line.lower() + " "
        if not any(" " + word + " " in low or " " + word + "s " in low
                   for word in _PRESENT_PEOPLE):
            turns = (memory or {}).get("turns")
            if isinstance(turns, list):
                earlier = " ".join(str(turn.get("user") or "") for turn in turns[-2:]
                                   if isinstance(turn, dict))
                found = _the_condition_in(earlier)
    return found or ("", ())


def _present_answer(text):
    """A written present answer that still reads the condition the person was described by.

    The rows for a named person (a dad, a mum) are one good paragraph each, and the condition is
    in the line rather than in the taste table, so they pass through the same note the generic
    rows do.
    """
    def reply(memory, understood):
        return _with_the_condition(text, understood, memory)
    return reply


def _the_thing_a_verdict_is_about(line):
    """The present a verdict ask names, without the little words around it."""
    found = A_VERDICT_THING.search(str(line or ""))
    if not found:
        return ""
    # The article the person used is kept, because the answer says the thing back the way they
    # said it: "a scooter gets used every day", "duplo gets used every day".
    thing = " ".join(found.group(1).split())
    # A verdict that names no thing of its own ("is that a weird gift") is about the present the
    # last answer offered: this row says nothing about it and the line keeps its answer.
    thing = re.sub(r"^(?:(?:that|it|this)\s+)+", "", thing, flags=re.I)
    if thing.lower() in ("a", "an", "the", "my", "some", "a gift", "a present", "that", "it",
                         "this", "them", "they"):
        return ""
    if not thing or not re.search(r"[a-z]{3}", thing, re.I):
        return ""
    return thing


def _the_only_age_in_the_store(memory):
    """The age of the one person the chat holds an age for, or None.

    A verdict ask names no person - "would a scooter be too much" is about the present the last
    answer was for - so the person is read off the chat instead: when the store holds the age of
    exactly one person, that is who the present is for. Two ages and there is no saying which,
    and the answer stands down rather than judging the wrong child's present.
    """
    ages = []
    for entry in (memory or {}).get("others") or ():
        if isinstance(entry, dict) and people._with_an_age(entry):
            ages.append(people._age(entry))
    # A group the chat said the age of ("theyre 5 in june") is the same news as one person's age,
    # and the present the last answer listed was for them.
    held = (memory or {}).get("their_age")
    if isinstance(held, dict) and people._with_an_age(held):
        ages.append(people._age(held))
    if len(ages) == 1 and ages[0] is not None:
        return ages[0]
    return None


# The words a thing can be said with that are never the thing itself: a limit is said in hours and
# days ("is an hour of cartoons a day too much for a 3 year old"), and the age row's own grammar
# is full of them ("for that age", "every day").
NOT_THE_THING = frozenset("""
that this they them their there here what have has had with from your yours been being every
each some more most much only also just like both other another same sure back over into than
then age ages day days hour hours week weeks month months year years time times little bit
lot lots thing things present present gift gifts idea ideas kind sort
""".split())


def _a_pick_for_that_age(pool, thing):
    """True when the thing named is one of the picks the age's row already puts on the table."""
    if not pool or not thing:
        return False
    thing = re.sub(r"^(?:a|an|the|my|some)\s+", "", thing.strip(), flags=re.I)
    words = [word for word in re.findall(r"[a-z]+", thing.lower())
             if len(word) > 2 and word not in NOT_THE_THING]
    if not words:
        return False
    low = pool.lower()
    return any(re.search(r"\b" + re.escape(word) + r"s?\b", low) for word in words)


def the_verdict_on_a_present(memory, understood):
    """A yes to a verdict ask about a pick the age row already listed, or None to stand down."""
    line = _said_line(understood)
    if not A_VERDICT_ON_A_PRESENT.search(line):
        return None
    thing = _the_thing_a_verdict_is_about(line)
    held = _an_age_in_the_line(understood) or people.the_age_of_the_person_they_mean(
        memory, understood) or _the_only_age_in_the_store(memory)
    if not held:
        return None
    pool = _gift_for_an_age(held)
    if not thing:
        return None
    if not _a_pick_for_that_age(pool, thing):
        # A thing this age row never offered is not ours to judge: a wrong yes on a verdict is
        # worse than letting the line reach whoever else can answer it.
        return None
    age = str(int(held)) if float(held) == int(held) else str(held)
    if held < 1:
        age = "a baby"
    elif held == 1:
        age = "one"
    pool_of_words = MONEY_VERDICT_YES if A_VERDICT_ABOUT_MONEY.search(line) else VERDICT_YES
    return pick(pool_of_words, memory, line).format(age=age, thing=thing)


def _gift_row(fallback):
    """A generic gift answer that names the hobby when the chat has already said one.

    Every "what should i get her" row ends the same way when it knows nothing: a safe list and a
    note to buy into what they are into. When the chat has just said what they are into, the
    picks for that hobby are the answer, and INTEREST_GIFTS already holds them, so the rows share
    this instead of each learning the table.
    """
    def reply(memory, understood):
        verdict = the_verdict_on_a_present(memory, understood)
        if verdict:
            return verdict
        if A_VERDICT_ON_A_PRESENT.search(_said_line(understood)):
            return None
        if not reading.gift_ask(understood):
            # "my sister loves gardening" is a fact about her, not a request for a present.
            if A_CARD_IS_NOT_A_PRESENT.search(_said_line(understood)):
                # The turn after a present list is often about the card, and a card is not
                # another present: "my nephew is 5 in june" / "what can i get them" /
                # "and what about a card" was told the coffee-and-mug list again, and in the
                # chats where the row had no picks it was a search punt where main said
                # something. The card has its own answer; this row is not it.
                return None
            return fallback
        if PRICE_SAID.search(_said_line(understood)):
            # A price with a figure in it is the money rows' question: they answer with the
            # figure and this row would list good coffee and woolly socks instead.
            return None
        if A_CHEAP_ASK.search(_said_line(understood)):
            # "cheap present ideas for my nephew" asks what is possible for a tenner, and this
            # row was taking it and listing good coffee and woolly socks, which is not what a
            # tenner buys a child. The cheap row is the answer - and it has to be here as well
            # as in its own entry, because "cheap christmas present ideas" reaches this generic
            # row (the word "ideas" is the ask), and standing down alone left that line with no
            # answer at all: it was a search punt for a whole evening.
            cheap = _gift_cheap(memory, understood)
            return _with_the_condition(cheap, understood, memory) if cheap else None
        if not _knows_a_taste(memory, understood):
            # "my sister had her baby on tuesday", "a girl, 7lb 2oz", "what should i get them":
            # the thread is a newborn, and the list written for a grown-up nobody is not what a
            # person asking about a baby wants.
            baby = _the_newborn_present(memory, understood)
            if baby:
                return _with_the_condition(baby, understood, memory)
            # The chat may already know how old the person is: "my nephew is 5 in june" then
            # "what can i get them" is a five-year-old's present from the store, not the safe
            # list for a grown-up and not a search punt.
            pool = _gift_for_an_age(
                _an_age_in_the_line(understood)
                or people.the_age_of_the_person_they_mean(memory, understood))
            if pool:
                return _with_the_condition(pool, understood, memory)
            if _only_a_them_says_who(understood):
                # "what should i get them" with nobody in the store is the ask the "her" row has
                # always answered ("buy into what they already do"), and this row only knows a
                # person through the store: with nothing kept it has nothing to add, so the
                # older answer stands rather than being replaced by another generic list.
                return None
            return _with_the_condition(fallback, understood, memory)
        if PRICE_SAID.search(_said_line(understood)):
            # A limit in a line that also names the hobby is the money rows' question, and their
            # answer has the figure in it: "i need a present for a mate who likes coffee, nothing
            # over 25 pounds" was answered with coffee at three prices, none of them the
            # twenty-five asked for. With no hobby named the limit is not theirs, so the text stays.
            return None
        picks = present_known(_the_tastes(memory, understood), memory, understood)
        return _with_the_condition(picks or fallback, understood, memory)
    return reply


PLURAL_ONLY = re.compile(r"\b(?:them|they|theirs|their)\b", re.I)
# The plural words as PERSON_WORDS spells them: a line whose only person is one of these is a
# line about somebody the store has to hold, because the line did not say who.
PLURAL_WORDS = frozenset("they them their theirs".split())


def _only_a_them_says_who(understood):
    """True when the only person the line names is "them", so the store is the whole answer."""
    if not PLURAL_ONLY.search(_said_line(understood)):
        return False
    return not (_the_words(_said_line(understood)) & (PERSON_WORDS - PLURAL_WORDS))


def _the_newborn_present(memory, understood):
    """The present for a baby the chat is already talking about, or None."""
    if not newborn.the_thread_has_a_new_baby(memory, understood):
        return None
    return _gift_for_an_age(0.5)


def _with_the_condition(text, understood, memory=None):
    """A present answer, plus what the person's condition changes about the pick."""
    if not text:
        return text
    note, drop = _the_condition_gift(understood, memory)
    if not note or note.lower() in str(text).lower():
        return text
    answer = str(text)
    for phrase in drop:
        answer = answer.replace(phrase, "")
    return answer.rstrip() + " " + note


def _gift_anyone(memory, understood):
    # `her`/`him` and a giving verb are not a gift on their own: "should i get her a taxi" and
    # "what do i get him for his cough" reach this entry through the same three words as "what
    # could i get her". The reading decides - one rule, asked here as well as in the boost - and
    # an entry that declines gets its turn to a lower one instead of answering.
    if not reading.gift_ask(understood):
        return None
    if _knows_a_taste(memory, understood):
        # The chat has already said who she is and what she likes, so the picks for that hobby are
        # the answer, not the safe list an answer written for nobody has to give. The rows written
        # for a person (`gift-mum-garden`, `gift-dad-fishing`) outscore this one and keep their
        # turn; this is for the hobbies they do not cover.
        picks = present_known(_the_tastes(memory, understood), memory, understood)
        if picks:
            return picks
        # A taste the table does not price (a person who loves their dog) still beats the cold
        # card asking what they do at the weekend the chat has just answered.
        return None
    # The chat may already know how old the person is: "my son is 4" then "what should i get him
    # for his birthday" is a four-year-old's present, and the age is in the store, not in the
    # line. This used to answer with the grown-up list (a kitchen knife, decent coffee) because
    # only an age said in the same line was read.
    held = people.the_age_of_the_person_they_mean(memory, understood)
    pool = _gift_for_an_age(held) or _the_newborn_present(memory, understood)
    if pool:
        return _with_the_condition(pool, understood, memory)
    if people.a_child_the_chat_is_about(memory, understood):
        # A child of the family with no age on file: "my son starts school in september" then
        # "what should i get him" is a five-year-old's present, not the kitchen knife and decent
        # coffee the list for a person nobody knows anything about has to give.
        return _with_the_condition(CHILD_GIFT, understood, memory)
    return _with_the_condition(_GIFT_ANYONE, understood, memory)


def _laptop_general(memory, understood):
    return ("Get 16GB of RAM and a 512GB SSD if the budget stretches, 8GB and 256GB if it doesn't, "
            "and a 13 or 14 inch screen for carrying about. Don't pay for a graphics card unless "
            "you game or edit video; a good screen and keyboard matter far more day to day.")


# A gift answer only when the line is actually asking for one: "my dad loves fishing" is not.
GIFT_ASK = ("gift", "present", "get", "got", "buy", "christmas", "birthday", "60th", "70th",
            "80th", "idea", "for my", "for his", "for her")

# Someone who has just lost the person is not shopping for them.
LOSS = ("died", "death", "passed away", "funeral", "buried", "grief", "grieving",
        "bereavement", "widow", "miss her", "miss him", "miss mum", "miss dad")

# Nor is someone who is injured or in hospital. "For my dad" plus a bare "get" would otherwise read
# "my dad fell and cant get up" as a present request, so every gift entry carries both tuples.
CRISIS = ("fell", "fall", "fallen", "floor", "cant get up", "can't get up", "cannot get up",
          "hospital", "ambulance", "unresponsive", "not breathing", "collapsed", "stroke",
          "chest pain", "in a coma")
# Choosing a thing is only a question when the line is choosing. "need", "help", "one" and
# "new" are in the keys below because they carry the asking, not the subject: on their own they
# let "my laptop needs a new battery" and "I need to fill in a pdf on my laptop" get the buying
# advice. Every entry that answers a choice says which choosing words make it one.
CHOOSING = (("pick", "picking", "choose", "choosing", "choice"),
            ("buy", "buying", "get a", "getting a", "shopping",
             # "i need a new laptop mainly for writing" says what the thing is for, which is a
             # choosing line; a bare "need" is a fault ("my laptop needs a new battery"), so only
             # the shapes that ask for a thing count.
             "need a", "need some", "want a", "looking for a"),
            ("which", "what should i", "what to look for", "look for", "recommend",
             "recommendation", "suggestion",
             # "i need a new laptop but i dont know what to get" is the line the entry exists
             # for, and no other choosing word is in it: a reviewer found it getting a shrug.
             "what to get", "which to get", "what to buy", "which to buy", "dont know what",
             "don't know what", "not sure what", "not sure which", "which laptop", "laptop to get",
             "what laptop"),
            ("worth", "worth it", "best", "spend", "budget", "upgrade", "replace"),
            # asking what to look for in the machine is a choosing line, not a fault: a reviewer
            # found `need` alone was no longer enough for "how much ram do i need"
            ("how much ram", "how much memory", "how much storage", "what specs", "specs",
             "processor", "how fast",
             # "what size laptop do i need to do my accounts" asks the same thing by size.
             "what size", "how big", "screen size"))


# A person is only half of a gift question: "how do i get my sister to move out" names the sister and
# says get, so the person entries ask for the shapes that actually ask what to buy.
PERSON_ASK = ("gift", "present", "presents", "what should i get", "what should i buy",
              "what can i get", "what can i buy", "what to get", "what to buy",
              "what would you get", "what would you buy", "what do i get", "what do i buy",
              # "what do you get a 15 year old" and "what do you buy a 10 year old" are the same
              # question in the second person, and they were punting: every shape above names
              # I or nothing, and the age rows key on the person.
              "what do you get", "what do you buy", "what do you give", "what do you get them",
              "what do you buy them", "what to get them", "what should i bring",
              # "what can i give my friend for her birthday" is the same question and it was
              # answering with the "my friend forgot my birthday" line, because both name a
              # friend and a birthday and only the shape of the ask tells them apart. The bare
              # verb is not in this list: "how do i give feedback to a colleague" names a
              # colleague and says give, and it is not a present question.
              "what can i give", "what to give", "what should i give", "what could i give",
              "what do i give", "what would you give")

# The age in "what should i get a 60 year old", so one row can answer a 4-year-old's present
# and a 60th without reading the toddler list out to a grown man. Reported three times (board
# 8981, 10517, 17323) before this: the row never read the number.
TODDLER_GIFT = (
    "For a toddler, one thing they will use every day beats a pile of toys: a set of chunky "
    "blocks, a ball, a book with flaps to lift, or a scooter they will still fit next year. Ask "
    "the parents what they already have too much of, and buy the batteries with it.")
CHILD_GIFT = (
    "For that age, one thing they will use every day beats a pile of toys: a scooter, duplo, "
    "sticker and activity books, or a decent football. Ask the parents what they already have "
    "too much of, and buy the batteries with it. Wrap it in something they can play with "
    "afterwards.")
TEEN_GIFT = (
    "For a teenager, money or a voucher beats a guess, and headphones, gaming credit, a hoodie "
    "from a shop they like or a ticket to something are the safe few. Ask them once, buy the "
    "thing they named, and keep the change in a card with a real message in it.")
GROWN_GIFT = (
    "For that age, buy something they would use every week and would not buy themselves: good "
    "coffee or tea, a bottle of what they already drink, a voucher for a place they like, or a "
    "book by an author they follow. One useful thing beats a pile of small ones.")


# Every row that answers "what can I get them" gives a list of things to buy, and the turn after
# it is very often about the other half of the present: "and what about a card", "should i wrap
# it". A card is not a present, so the gift rows have nothing new to say about it and would hand
# the same list back - the card's own words answer instead. The openings are read off the rows
# themselves, so a row rewritten here is still recognised.
def _openings(*pools):
    out = []
    for pool in pools:
        for row in ((pool, ) if isinstance(pool, str) else pool):
            if isinstance(row, str) and len(row.strip()) > 20:
                out.append(" ".join(row.split())[:28])
    return tuple(out)


PRESENT_OPENINGS = _openings(
    TODDLER_GIFT, CHILD_GIFT, TEEN_GIFT, GROWN_GIFT, _GIFT_ANYONE, CHEAP_ADULT, CHEAP_CHILD,
    CHEAP_TEEN)


def a_present_was_answered(memory):
    """Whether the answer on the screen is one of the present lists, rather than talk around one."""
    from ..memory import last_bot
    said = " ".join(str(last_bot(memory) or "").split())
    if not said:
        return False
    return any(opening in said for opening in PRESENT_OPENINGS)


# An age is not a present question either: "how do i plan a birthday party for a 6 year old".
AGE_ASK = ("gift", "presents", "present", "what should i get", "what should i buy",
           "what can i get", "what can i buy", "what to get", "what to buy",
           "what would you get", "what would you buy", "what do i get", "what do i buy",
           "what do you get", "what do you buy", "what do you give", "what do you get them",
           "what do you buy them", "what to get them",
           "what can i give", "what to give", "what should i give", "what do i give")

# What an everyday appliance is good for, who it is not for, and the price of being wrong. Keyed
# on the machine, so every way of asking "is X worth it" reaches the same trade: "is an air fryer
# worth it", "should i get a slow cooker", "are bread makers worth the money". The answer says what
# it does well and who should skip it, because "worth it" depends on the person, and a verdict
# without the condition is a guess.
APPLIANCE_VALUE = (
    (("air fryer", "air fryers", "airfryer"),
     "An air fryer is a small oven that blows hot air fast: chips, roast veg and salmon in 10 to 15 "
     "minutes with a spoon of oil. Worth it for one or two people who hate heating a big oven; skip "
     "it for four, since a 4-litre basket is one tray. £50 to £80 is plenty."),
    (("slow cooker", "slow cookers"),
     "A slow cooker is worth it if you are out all day: load it before work and cheap cuts are "
     "tender by dinner. Skip it if you want anything crisp or fast. A £30 one cooks the same as "
     "a £100 one."),
    (("pressure cooker", "instant pot", "pressure cookers"),
     "A pressure cooker is worth it if you cook beans, stews or tough meat from scratch: a beef stew is 40 minutes "
     "instead of two hours, and dried beans are 25. Skip it for anything quick or crisp, and know "
     "that it is a big pan to store. A 6-litre one suits most kitchens."),
    (("bread maker", "bread machine", "bread makers"),
     "A bread maker is not worth it for most people: skip it unless you eat a loaf a day, since it "
     "takes three to four hours for a small loaf with a soft crust, and a £15 tin in a hot oven "
     "makes better bread. It earns its space only if you want the dough made overnight with no "
     "hands."),
    (("dishwasher", "dishwashers"),
     "A dishwasher is worth it for three or more people: it uses less water than washing up by hand "
     "and saves about half an hour a day. Skip it if you live alone and cook little, since filling "
     "it takes a week. Check the noise (under 45dB) if the kitchen is also the living room, and a "
     "45cm slimline model fits a small kitchen."),
    # The heat pump dryer is asked about by name often enough that it needs its own row: the row
    # below it answered "should i get a heat pump tumble dryer" with the general dryer trade.
    (("heat pump dryer", "heat pump dryers", "heat pump tumble dryer", "heat pump tumble drier",
      "heat pump drier", "heat pump condensing dryer"),
     "A heat pump dryer is worth it if you dry two or more loads a week: it uses about half the "
     "electricity of a vented one, roughly 25p a cycle against 60p, so 150 to 200 pounds more up "
     "front pays back in about two years. It runs cooler, so a load takes an hour longer, and the "
     "fluff filter and condenser want clearing often. Skip it if you dry rarely, if the room is "
     "cold, or if you have nowhere to empty the water."),
    (("tumble dryer", "tumble dryers"),
     "A tumble dryer is worth it if you have no outside space or a house full of laundry: a heat-pump dryer costs more "
     "(£350 up) but uses about half the electricity of a vented one. Skip it if you have a "
     "garden and an airer: it is the most expensive way to dry clothes."),
    # The buying question for the things people ask about in the same breath as the ones above,
    # and everyone of them was a shrug: "should i get a smart thermostat", "is a humidifier worth
    # it", "is a mattress topper worth it", "should i get a fan", "is a video doorbell worth it",
    # "is a robot mower worth it" and "is a water filter jug worth it" all came back "That's your
    # call, not mine". A water softener was worse than that: it was answered by the fabric
    # softener row, which is a different machine in a different room.
    (("smart thermostat", "smart thermostats", "heating thermostat", "nest thermostat",
      "hive thermostat", "tado", "thermostatic radiator valve", "thermostatic radiator valves",
      "trv", "trvs"),
     "A smart thermostat is worth it if the house is empty in the day: about £50 to £100 a year "
     "off a gas bill, so £150 to £250 fitted pays back in two to three years. Skip it if someone "
     "is home all day, or if the heating is already set to come on only when you are in: turning "
     "the flow temperature down and putting thermostatic valves on the radiators gets much of the "
     "saving for a fraction of the price."),
    (("water filter jug", "water filter jugs", "filter jug", "brita", "water filter"),
     "A water filter changes the taste and takes out the chlorine, and a plumbed-in one under the "
     "sink is the same job done once instead of every jug: neither softens hard water nor takes out "
     "much else. Worth it if your tap water tastes of "
     "chlorine and you drink it cold all day, at about £20 for the jug and £4 a month for cartridges. "
     "A jug of tap water left in the fridge overnight does most of the same for nothing, so try "
     "that first."),
    (("humidifier", "humidifiers"),
     "A humidifier is worth it in one dry room, usually a bedroom with the heating on and the "
     "windows shut, if you wake with a dry throat or nosebleeds, or have a cold. Skip it in a room "
     "that has damp on the walls or condensation on the glass, because adding moisture makes that "
     "worse, and clean it every week: a dirty humidifier sprays mould into the air. £30 to £60 for "
     "a cool-mist one."),
    (("mattress topper", "mattress toppers", "bed topper"),
     "A mattress topper is worth it if the mattress is sound but too firm, or you want it softer: "
     "5cm of memory foam or a wool topper costs £60 to £120 and changes the feel for a fraction of "
     "a new mattress. It will not fix a mattress that sags, is over about eight years old or gives "
     "you backache, and a topper on a bad mattress is £100 spent on the wrong thing."),
    (("water softener", "water softeners", "water softening"),
     "A water softener is worth it in a hard water area if scale is a daily nuisance: kettles, "
     "shower screens and the washing machine stop furring up, and the boiler keeps its efficiency. "
     "It is about £1,000 to £2,000 fitted plus £100 to £150 a year in salt, so it is a family and "
     "hard-water answer rather than a flat one. A filter jug does not soften water, and a magnetic "
     "or electronic conditioner does not take the calcium out."),
    (("robot mower", "robot mowers", "robot lawn mower", "robotic mower"),
     "A robot mower is worth it for a flat, open lawn with no narrow gaps: it cuts a little every "
     "day, so the grass stays tidy and there is no grass to collect. It costs £500 to £1,500 and "
     "most need a boundary wire laid round the edge. Skip it for a small lawn, a steep slope, or one "
     "full of bulbs and toys."),
    (("video doorbell", "video doorbells", "ring doorbell", "doorbell camera"),
     "A video doorbell is worth it if parcels go missing or you cannot hear the door from where you "
     "work: £50 to £120, and stored clips usually need a subscription of £2 to £4 a month unless you "
     "take a local-storage model. Wired is more reliable than battery. Point it at your own path and "
     "door rather than the pavement, and if you rent, ask before drilling."),
    # A heater with a fan in it is not a fan, and the two were one word: "should i get a fan
    # heater" was about to be told that moving air cools you. The longer name is read first, so
    # this row wins the line that says both.
    (("fan heater", "fan heaters", "electric heater", "electric heaters", "oil filled radiator",
      "convector heater", "space heater", "halogen heater"),
     "A fan heater is worth it for one room for twenty minutes, not for a whole evening or a whole "
     "house: cheap to buy at £20 to £40 and dear to run, since 2kW is about 60p an hour on current "
     "electricity prices. For a room you sit in, an oil-filled radiator is silent and "
     "holds the heat after it clicks off, and heating the person beats heating the room: a throw, "
     "a hot water bottle and warm socks are free after the first winter."),
    (("fan", "fans", "electric fan", "tower fan", "pedestal fan", "desk fan", "floor fan",
      "standing fan", "cooling fan"),
     "A fan does not cool the air, it moves it, and moving air over your skin is enough to feel a "
     "few degrees cooler, so it is worth it for sleeping in a hot room: a tower or pedestal fan at "
     "£25 to £60 is much quieter than a cheap one, and it costs a penny or two an hour to run. Put "
     "it in the window at night to pull cool air in, and skip portable air conditioning unless the "
     "room is also humid, since that is the expensive way round."),
    (("robot vacuum", "robot hoover", "robot vacuums"),
     "A robot vacuum is worth it as a daily top-up on hard floors and one level, not as a deep "
     "clean: skip it if the floor has stairs, thick rugs or a trail of cables and toys, since it "
     "will not get them and you still empty it. Best value in a house with a pet that sheds."),
    (("dehumidifier", "dehumidifiers"),
     "A dehumidifier is worth it in a flat that steams up and grows black mould on the window frames: a 10 to 12 "
     "litre one dries washing indoors and stops the mould, which costs more to fix than the machine. "
     "Skip it if the damp is a leak or a broken gutter, since that needs fixing at the source."),
    (("coffee machine", "bean to cup", "coffee machines"),
     "A coffee machine is worth it if you drink two coffees a day at home: a £150 bean-to-cup pays for itself in "
     "about three months against buying them out. Skip it if you have one coffee a day: a £30 "
     "filter machine with fresh ground coffee tastes better than a cheap pod machine, and the pods "
     "are the expensive part."),
    (("stand mixer", "kitchenaid", "stand mixers"),
     "A stand mixer is worth it if you bake most weeks: it creams butter and kneads dough for you and lasts decades. "
     "Skip it if you bake a few times a year: a £15 hand mixer does the same job and lives in a "
     "drawer."),
    (("meal kit", "meal kits", "recipe box", "hello fresh", "gousto"),
     "A meal kit is worth it for the decision taken away, not the food: about £5 a portion and "
     "no waste. Skip it if you already cook, since the same dinner is £1.50 a portion from a "
     "supermarket. Try two boxes and cancel."),
    (("kindle", "e reader", "ereader", "e-reader"),
     "A Kindle is worth it if you read in bed or travel: a Paperwhite is readable in the dark, holds "
     "hundreds of books and the battery lasts weeks. Skip it if you mostly read at home: library "
     "ebooks through Libby or BorrowBox are free on a phone, and paper is better for anything with "
     "maps or photos. Buy last year's model, not the newest."),
    (("noise cancelling headphones", "noise cancelling headphone", "noise cancelling"),
     "Noise cancelling headphones are worth it if you commute by train, plane or sit in a loud "
     "office: over-ear ones cut the engine noise that earbuds let through. About £70 to £120 "
     "is the sweet spot, and last year's model sounds the same as the new one for half the price. "
     "Skip them for a quiet room or for cycling, where hearing traffic matters."),
    (("fitness tracker", "fitness trackers", "fitbit"),
     "A fitness tracker is worth it for steps and sleep, not for the heart-rate number: a £25 band "
     "counts steps and sleep well, and a watch ten times the price adds mostly a screen and GPS. Skip "
     "it if you already walk enough and know it, since most people stop looking after a month."),
    (("smart watch", "smart watches", "apple watch"),
     "A smart watch is worth it if you want notifications, contactless payment and a run tracker on "
     "your wrist without getting your phone out. Skip it if you only want steps, where a £25 band "
     "does the same. An iPhone pairs best with an Apple Watch, an Android with a Wear OS watch or a "
     "Garmin."),
    (("standing desk", "standing desks", "sit stand desk"),
     "A standing desk is worth it if you sit for eight hours and your back aches, and the useful part "
     "is changing position rather than standing all day: a £25 riser on the desk you have does most "
     "of it. Skip the motorised ones unless you know you will raise them, and stand for 20 minutes at "
     "a time rather than the afternoon."),
    (("weighted blanket", "weighted blankets"),
     "A weighted blanket is worth it if the feeling of weight settles you: about 10% of your body "
     "weight is the usual guide, and it helps some people fall asleep and does nothing for others. "
     "Skip it for a toddler, or for anyone who could not push it off, and try one under a duvet "
     "before spending £60."),
    (("steam cleaner", "steam cleaners", "steam mop"),
     "A steam cleaner is worth it for hard floors, tiles and grout, and the bathroom: it lifts grease "
     "with no chemicals and the water is free after the machine. Skip it on laminate, unsealed wood "
     "and anywhere the moisture can get under the floor, and skip it for carpets, where a hire "
     "machine once a year is cheaper than owning one."),
    # a cleaner is a person hired to clean, so the article is part of the name: "which vacuum
    # cleaner should i get" and "is an oven cleaner worth it" name machines, not a hire, and
    # "cleaners" on its own is one of those cleaners, so the plural needs its own words
    (("a cleaner", "the cleaner", "my cleaner", "our cleaner", "cleaners worth",
      "cleaning lady", "cleaning service", "housekeeper"),
     "A cleaner is worth it if two hours back at the weekend matter more than £15 to £20 an "
     "hour: two hours a fortnight covers a flat. Go through an agency with insurance, agree in "
     "writing what is included and be in the first time. Skip it while you are paying off a debt."),
    (("food processor", "food processors", "kitchen machine"),
     "A food processor is worth it if you chop a lot of onions or make pastry: it does in a minute "
     "what a knife takes ten. Skip it if you cook simply, since it is heavy to wash up for one job. "
     "A £40 one chops as well as a £200 one."),
    (("air purifier", "air purifiers"),
     "An air purifier is worth it in a bedroom if you have hay fever, a cat or a sealed window: a "
     "HEPA filter on low all night changes how you sleep. Skip it for damp, which needs a "
     "dehumidifier, and check the replacement filters are cheap before you buy."),
    (("heated airer", "heated clothes airer", "heated drying rack", "heated clothes horse"),
     "A heated airer is worth it if you dry clothes indoors in winter: about 6p an hour against 50p "
     "or more for a tumble dryer, and it does not shrink anything. Skip it if you have a garden and "
     "dry outside in summer, and buy the larger winged one so a full wash fits on it. A cover cuts "
     "the drying time by half."),
    (("electric blanket", "electric blankets", "heated blanket"),
     "An electric blanket is worth it for a cold bedroom: 20 minutes before bed costs pennies and "
     "beats heating the room all evening. Skip it if it would be on all night, since a hot water "
     "bottle does the same for nothing, and replace one over ten years old."),
    (("microwave", "microwaves"),
     "A microwave is worth it for reheating, porridge, scrambled eggs and defrosting, not for cooking a meal from "
     "scratch: skip it if you want to roast or bake, since an oven does that better. A basic 800W "
     "one is enough; pay more for a bigger turntable and easier controls, not for modes nobody "
     "uses."),
)

# The same trade for the bigger things people weigh up, where the maths decides it: a season
# ticket pays off at a certain number of days a week, a car at a certain mileage. Keyed on the
# thing, so "is a gym membership worth it" and "should i join a gym" reach the same answer.
CHOICE_VALUE = (
    # The thing here is an action rather than a noun, so the phrase carries the ask: "should i
    # go to the gym", "should i bother going to the gym" and "should i go back to the gym" were
    # the you-decide punt while "should i join a gym" got the trade. A bare "go to the gym" would
    # take "how often should i go to the gym" and "i went to the gym and my back hurts", which are
    # other rows' lines, so the ask is part of the name.
    (("gym membership", "gym memberships", "join a gym", "joining a gym", "gym worth",
      "should i go to the gym", "should i go to gym", "shall i go to the gym",
      "should i go back to the gym", "should i go to the gym again",
      "should i bother going to the gym", "should i bother with the gym",
      "should i bother with a gym", "should i start going to the gym",
      "is it worth going to the gym", "worth going to the gym",
      "any point going to the gym", "should i go to the gym or"),
     "A gym is worth it if the door is within ten minutes of you and you will go twice a week: the "
     "walk decides it, not the equipment. Skip it if the nearest one is a drive away, and pay "
     "monthly rather than a year up front. A £20 leisure-centre one you use beats a £60 "
     "one you dread."),
    # A heat pump dryer is a different machine with different numbers, and the row below it
    # answered "is a heat pump dryer worth it" with the boiler trade: "the grant covers a few
    # thousand, the running cost is close to gas". A dryer is bought outright and runs on
    # electricity, so it needs its own row, and the phrase "heat pump dryer" outranks "heat pump".
    (("heat pump dryer", "heat pump tumble dryer", "heat pump drier", "heat pump tumble drier",
      "heat pump dryers", "heat pump condensing dryer"),
     "A heat pump dryer is worth it if you dry two or more loads a week: the cycle uses about half "
     "the electricity of a vented one, roughly 25p against 60p, so it pays back its extra 150 to "
     "200 pounds in about two years. It runs cooler and slower, so a load takes two hours and more, "
     "and it needs the fluff filter and condenser cleared often. Skip it if you dry rarely or have "
     "nowhere for the waste water, and never buy one without a heat pump if the room is cold."),
    (("heat pump", "heat pumps"),
     "A heat pump is worth it if you are replacing the boiler anyway and the house is insulated: the "
     "grant covers a few thousand, the running cost is close to gas, and it heats a well-insulated "
     "home steadily rather than in bursts. Skip it in a draughty house with no wall or loft "
     "insulation, since the insulation comes first and pays back faster."),
    (("electric car", "electric cars", "ev "),
     "An electric car is worth it if you can charge at home and do under about 200 miles a week: "
     "home charging is roughly 3p a mile against 15p for petrol, and there is almost no servicing. "
     "Skip it if you cannot charge at home, or if you regularly do long motorway runs, where public "
     "charging costs nearly as much as fuel."),
    (("smart meter", "smart meters"),
     "A smart meter is worth having: your supplier fits one free, and the in-home display shows "
     "what the kettle and the heating cost as you use them. Ask for a second-generation (SMETS2) one "
     "so it keeps working if you switch supplier. It will not cut the bill on its own."),
    (("water meter", "water meters"),
     "A water meter usually saves money if there are more bedrooms than people: the rule of thumb is "
     "that you pay less on a meter when there are fewer of you than rooms. Check the bill estimate "
     "first, and remember you can go back to an unmetered bill within the first year in England and "
     "Wales if it costs you more."),
    (("season ticket", "season tickets"),
     "A season ticket pays off at about three days a week: below that, the flexible or weekly "
     "options are usually cheaper. Work out the yearly cost against 40 weeks of daily returns "
     "before you commit, and check whether a part-time or flexi season covers the days you "
     "actually travel."),
)

# The question has to be about buying one, or the repair rule and the how-to entries answer it.
APPLIANCE_ASK = ("worth", "worth it", "worth the money", "should i get", "should i buy",
                 "do i need", "need one", "shall i get", "good buy", "any good", "is it good",
                 # "what is a good cheap dehumidifier" and "what is a good cheap slow cooker" ask
                 # which to have, and the worth-it words were the only ones this gate knew. The
                 # running-cost row stands down on the same words now, so without these two the
                 # buying question fell to the meal-cost row and was a shrug.
                 "a good", "good cheap", "good and cheap", "the best", "best one",
                 "buy", "buying", "getting", "get one",
                 # "should i use a weighted blanket" is the same choice as "is it worth it", and
                 # it was the decision module's shrug because the ask was "should i use"
                 "should i use", "should we use", "should i try", "is it ok", "is it safe",
                 # Going somewhere is the ask for the gym, the one thing in this table named by an
                 # action: "should i go to the gym" and "should i go back to the gym" carried no
                 # word from this list, so the you-decide punt answered them while "should i
                 # bother going to the gym" got the trade through the bare "bother". The thing
                 # still has to come from the row's own key, so this kills no other line.
                 "should i go", "shall i go", "should we go", "should i start", "should i bother",
                 "is it worth going", "worth going",
                 "would you", "will it help", "does it help",
                 # The same question asked the way people ask about a buy: "would you recommend
                 # a heat pump", "do you recommend a dehumidifier". The verb is the ask, so the
                 # row still needs the thing from its own key.
                 "recommend", "recommended", "recommendation", "recommendations",
                 # The same question with the machine named instead of "it": "will a dehumidifier
                 # help" and "does a dehumidifier help with damp" carry no worth-it word at all,
                 # so the table's own dehumidifier answer never saw them and they went to a
                 # trade's shrug. "will a" is only an ask, so the entry still needs a name from
                 # its own key: "will a plumber help" reaches nothing here.
                 "will a", "will an", "does a", "does an", "would a", "would an",
                 "will my", "does my", "would my",
                 # The same question asked as a doubt about spending at all: "any point in a
                 # dehumidifier", "is a standing desk a waste of money". Neither carries a
                 # worth-it word, so both were the decision module's shrug while the row that
                 # holds the answer sat one word away.
                 "any point in", "any point to", "point in a", "point in an", "point in",
                 "point to", "point of a", "point of an", "waste of money",
                 "wasting money", "money well spent", "bother with", "bother")


# A smart meter is three questions wearing one name. "Is one worth it" is the CHOICE_VALUE row
# ("smart meter"), so what is left here is the meter you already have: how to read it, and what to
# do when it stops sending. Both were a hedge or an echo before this.
_METER_FAULT = ("blank", "stopped", "broken", "faulty", "dead", "warning", "error", "gone",
                "connect", "sending", "signal", "wrong", "wtong")
_METER_READ = ("read", "reading", "readings", "button", "show", "shows", "find", "mean", "means",
               "numbers", "figure", "figures", "kwh")


def _smart_meter_how(memory, understood):
    said = str(understood.get("text") or understood.get("clean") or "").lower()
    words = understood.get("words") or []
    if any(word in said for word in _METER_FAULT) or "not working" in said:
        return ("Ring your supplier and say the meter or its display has stopped - it is their "
                "equipment, so fixing it is free, and it is usually a firmware update or a new "
                "display they send out. Photograph the reading on the meter itself before you ring, "
                "and send them a reading weekly until it is sorted, so you are not billed on an "
                "estimate in the meantime.")
    if any(word in _METER_READ for word in words):
        return ("Press the button marked A (some meters say B) until the screen shows a number with "
                "kWh after it - that is your reading, and the one the supplier wants. On a smart "
                "meter the in-home display shows it too, and with a single-rate tariff it is the "
                "only number that matters; a two-rate one shows day and night separately, so send "
                "both.")
    return ""


# An action named in a decision is not a thing with a price. "should i go to the gym" is the
# gym's trade, but the moment the line names an occasion or a state - "with a fever", "when im
# tired", "every day", "with a bad shoulder" - the question is that occasion's, and the card that
# knows it is one line away in the same tree: the neck rule for a fever, the rest-day rule for
# every day, the tiredness card. Those occasions are endless, so the test is not a list of them.
# It is the words the line has left once its own name and the ask are taken out: grammar only, or
# the action row steps aside and lets the card that names the occasion answer.
_DECISION_WORDS = frozenset((
    "a", "an", "the", "i", "me", "my", "we", "us", "our", "you", "your", "it", "its", "im",
    "ive", "id", "is", "are", "was", "were", "am", "do", "does", "did", "doing", "done", "be",
    "been", "being", "should", "shall", "would", "will", "can", "could", "may", "might", "must",
    "worth", "any", "point", "in", "to", "of", "for", "at", "on", "with", "and", "or", "so",
    "if", "that", "this", "these", "those", "then", "than", "now", "today", "tomorrow",
    "tonight", "later", "still", "just", "really", "actually", "honestly", "though", "again",
    "back", "go", "goes", "going", "went", "get", "gets", "getting", "got", "bother",
    "bothering", "start", "starting", "started", "try", "trying", "buy", "buying", "join",
    "joining", "one", "ones", "thing", "things", "time", "times", "not", "no", "yes", "ok",
))
# The names in these tables that are an action rather than a thing: "go to the gym", "start at
# the gym". Only those are held to a bare line, because a thing with a price ("is a cleaner worth
# it", "is a season ticket worth it") is asked about the thing however much else is going on.
_ACTION_NAME = re.compile(r"\b(go|going|went|start|starting|bother|bothering|try|trying)\b")


def _bare_decision(said, name, ask):
    """Whether the line asks about `name` and names no occasion of its own."""
    rest = said
    for phrase in (name,) + tuple(ask):
        phrase = phrase.strip()
        if phrase:
            rest = re.sub(r"\b" + re.escape(phrase) + r"\b", " ", rest)
    return all(word in _DECISION_WORDS for word in re.findall(r"[a-z0-9']+", rest))


def _longest_match_named(said, table):
    """The longest name the line holds, and the reply it belongs to."""
    best, longest, found = None, -1, ""
    for names, reply in table:
        for name in names:
            name = name.strip()
            if len(name) > longest and re.search(r"\b" + re.escape(name) + r"\b", said):
                best, longest, found = reply, len(name), name
    return best, found


def _longest_match(said, table):
    """The row whose name covers the most of the line: "steam cleaner" is not "a cleaner"."""
    best, longest = None, -1
    for names, reply in table:
        for name in names:
            name = name.strip()
            if len(name) > longest and re.search(r"\b" + re.escape(name) + r"\b", said):
                best, longest = reply, len(name)
    return best


# A trader with a quote in front of you is a different conversation from a shop with a price tag:
# the levers are the materials, the dates and the deposit, not a display model.
_TRADER_WORDS = ("builder", "builders", "plumber", "plumbers", "electrician", "electricians",
                 "decorator", "decorators", "plasterer", "plasterers", "roofer", "roofers",
                 "joiner", "joiners", "tiler", "tilers", "carpenter", "carpenters", "gardener",
                 "gardeners", "tradesman", "tradesmen", "trade", "contractor", "contractors",
                 "quote", "quotes", "quotation", "quotations", "day rate", "labour", "estimate")


def _haggle(memory, understood):
    """The price question, said to a shop or said to a trader.

    A shop has a price tag and a margin, so the ask is one question, the display model and the
    readiness to walk away. A trader has a quote and a diary, so it is the materials, the dates
    and the deposit. STYLE asks for the answer first, and it is not the same sentence for both.
    """
    reading = understood if isinstance(understood, dict) else {}
    said = " ".join(str(part) for part in (
        reading.get("clean"), reading.get("text"), " ".join(reading.get("words") or ()))).lower()
    if re.search(r"\brude\b|\bawkward\b|\bembarrass", said):
        return ("No - asking once is normal in a market, a car boot sale, a small independent shop "
                "or on anything big like a sofa, and in a chain with price tags it is still fine "
                "to ask. One question, then take the answer and either buy or leave: asking twice "
                "or arguing after a no is the part that gets awkward.")
    if any(word in said for word in _TRADER_WORDS):
        return ("Get three written quotes first, then ask each trader the same question: what "
                "would bring that down? Supplying the materials, being flexible on dates so the "
                "job fills a gap in their diary, and paying a deposit up front are the three that "
                "work. Compare the quotes line by line rather than on the total, and treat one "
                "miles under the others as a warning: the extras come later.")
    return ("Ask once, cheerfully, once you have picked the thing - \"is there anything you can "
            "do on the price?\" - then stop talking and be ready to walk away: silence and a "
            "customer who will leave are what move a price. Take the display model or last "
            "season's colour, offer to pay in full today, check the online price so they can "
            "match it, and never say your maximum. At a market or car boot sale, offer about two "
            "thirds and settle in the middle.")


# The words that make a line a question about a dryer rather than about the pump in the house.
_DRYER_WORDS = ("dryer", "dryers", "drier", "driers", "tumble dryer", "tumble drier")

def _choice_value(memory, understood):
    """The maths for the bigger thing the line names, or None when it names none of these."""
    reading = understood if isinstance(understood, dict) else {}
    said = " ".join(str(part) for part in (
        reading.get("clean"), reading.get("text"), " ".join(reading.get("words") or ()))).lower()
    row, name = _longest_match_named(said, CHOICE_VALUE)
    # The action rows only answer a bare line: see _DECISION_WORDS. A fever, a cold, every day and
    # "when im tired" are their own cards, and this row was taking all four.
    if row is not None and _ACTION_NAME.search(name) and not _bare_decision(said, name, APPLIANCE_ASK):
        return None
    # "heat pump or condenser dryer which should i buy" is a question about a dryer, and the
    # longest name the line holds is "heat pump", which is the boiler's row: it was told the
    # grant covers a few thousand and the running cost is close to gas. A dryer word makes it
    # the dryer's trade, because a heat pump in a house is never asked for beside a dryer.
    if row is not None and any(word in said for word in _DRYER_WORDS):
        for names, answer in CHOICE_VALUE:
            if any("dryer" in name or "drier" in name for name in names):
                return answer
    return row


def _appliance_value(memory, understood):
    """The trade for the appliance the line names, or None when it names none of these."""
    reading = understood if isinstance(understood, dict) else {}
    said = " ".join(str(part) for part in (
        reading.get("clean"), reading.get("text"), " ".join(reading.get("words") or ()))).lower()
    return _longest_match(said, APPLIANCE_VALUE)


# A small thing bought at a shop down the road, and the kind of shop that has it. "where can i
# buy a stamp" is a where question with a short answer, and the price-comparison advice next door
# is written for a model, a warranty and a "was £500" tag: it made every one of these a lecture on
# the price of an appliance. Keyed on the thing so the row names the place rather than describing
# how to shop, and the longest name wins ("birthday card" is not "card" alone).
EVERYDAY_WHERE = (
    (("stamp", "stamps", "postage", "first class", "second class", "signed for",
      "recorded delivery"),
     "Any post office counter has them, and so do most supermarkets, corner shops and newsagents. "
     "A book of 12 costs less per stamp than singles, and Royal Mail's own site will post a book "
     "out if you are not going past a counter."),
    (("birthday card", "birthday cards", "christmas cards", "christmas card", "greetings card",
      "greetings cards", "card shop", "cards"),
     "A card shop, a supermarket or a petrol station will have one, and the supermarket's own "
     "range is two pounds rather than four. If it is a big one, buy it this week rather than the "
     "day before - the good ones go first."),
    (("envelope", "envelopes", "stationery", "wrapping paper", "note paper", "printer paper",
      "pens", "a pen", "felt tips", "sellotape", "sticky tape", "glue", "a folder"),
     "A stationery shop or the back-to-school aisle of a supermarket has it, and for a batch "
     "envelopes or a box of paper an office supplier is cheaper and delivers. A card shop sells "
     "envelopes on their own if you only need a few."),
    (("sleeping bag", "sleeping bags", "tent", "rucksack", "camping gear", "camping stove",
      "walking boots"),
     "An outdoor shop is where the real ones are: Decathlon for the cheap end, Go Outdoors or a "
     "proper mountaineering shop for the rest. A charity shop or a car boot sale often has a "
     "decent sleeping bag for a tenner, and a borrowed one for a first trip is better than buying."),
    (("paint", "paintbrush", "paintbrushes", "roller", "dust sheet", "dust sheets",
      "undercoat", "primer"),
     "A decorator's merchant rather than a chain for the paint itself: the trade brands cover "
     "better, cost less and they will mix a colour to a sample. For one room, a DIY shop for the "
     "brushes, trays and sheets is fine, and cheap brushes are the false economy - they shed."),
    (("batteries", "battery", "light bulb", "lightbulb", "bulb", "fuse", "plug",
      "extension lead"),
     "A supermarket, a hardware shop or a pound shop has them. Take the old one with you, or "
     "photograph the numbers printed on it, because the size is the thing people get wrong: a "
     "bulb needs its fitting and its wattage, a battery its number, a fuse its amps."),
    (("boxes", "moving boxes", "cardboard boxes", "bubble wrap", "packing tape"),
     "A supermarket will give you banana boxes free if you ask at the customer desk, and a "
     "removal firm sells proper double-walled ones for a few pounds each. Ask on a Monday, "
     "before the delivery cages are taken back."),
)


# "the light bulb in the loft" is a place the thing already is, not a shop that sells it.
_INSIDE = re.compile(r"\b(?:in|inside|under|behind|on top of|on)\s+"
                     r"(?:the|my|our|your|their|his|her)\s+([a-z'\u2019]+)")
_MINE = re.compile(r"\b(?:my|our)\b")
_SHOP_PLACES = frozenset("""
    shop shops store stores supermarket supermarkets online internet ebay amazon argos
    town city high street market sale sales chemist chemist's counter department
    """.split())


# The things the table above names, as one key part: the ask is what makes it a where-line and
# the thing is what makes it this row's, which is the same two signals every row here needs.
_THE_EVERYDAY_THINGS = tuple(sorted({name for names, _ in EVERYDAY_WHERE for name in names}))


def _everyday_where(memory, understood):
    """Where a small everyday thing is bought, or None when the line names none of them.

    "where can i buy a stamp" is a where question with a short answer - a post office counter -
    and the price-comparison advice is written for something with a model, a warranty and a
    "was £500" tag, which a stamp, a card and a sleeping bag do not have. One table, read by one
    row, so a new everyday thing is a line here rather than a row of its own.
    """
    reading = understood if isinstance(understood, dict) else {}
    said = " ".join(str(part) for part in (
        reading.get("clean"), reading.get("text"), " ".join(reading.get("words") or ()))).lower()
    if not said:
        return None
    # "where can i find the light bulb in the loft" and "where do i find the batteries in the
    # remote" use a buying verb to ask where the thing already is, and a shop is the wrong
    # answer: the row stands down when the line puts the thing inside a place that is not a shop.
    inside = _INSIDE.search(said)
    if inside and inside.group(1) not in _SHOP_PLACES:
        return None
    # "where do i find my tent poles" is asking where the poles already are: a thing the person
    # owns is not a thing to buy, and the buying words alone cannot tell the two apart.
    if "find" in said.split() and _MINE.search(said):
        return None
    return _longest_match(said, EVERYDAY_WHERE)


def _gift_for_an_age(age):
    """The present pool for an age in years, or None when there is no age to go on."""
    if age is None:
        return None
    if age < 1:
        return ("Under a year, buy the boring things the parents will use: clothes in the size for "
                "three to six months ahead, a pack of muslins, a board book, or a soft ball. Skip "
                "anything that needs batteries or a cot to hang it from, and skip newborn sizes, "
                "because everyone buys those and the baby grows out of them in a fortnight.")
    if age >= 20:
        return GROWN_GIFT
    if age >= 13:
        return TEEN_GIFT
    return TODDLER_GIFT if age <= 2 else CHILD_GIFT


# The age said as the birthday coming: "turning 7", "turns 5 on friday", "turning 30 in may".
# "turn 2 left at the roundabout" is not an age, so the bare verb is out and only the two forms a
# birthday is said in are read.
TURNING = re.compile(r"\b(?:turning|turns)\s+(?P<age>\d{1,3})\b", re.I)


def _an_age_in_the_line(understood):
    """The age the line itself says, in years, or None.

    A baby is asked for in months ("what do you get a 6 month old"), and "for her 9th birthday"
    says the age in the day as plainly as "a 9 year old" does.
    """
    for number in (understood or {}).get("numbers") or []:
        if number.get("unit") == "months":
            return number.get("value") / 12.0
        if number.get("unit") == "years":
            return number.get("value")
    # "my son is turning 7 next week and i have no idea what to get him" says the age in the verb,
    # and a number with no unit after "turning"/"turns" is that many years: the line was answered
    # with whatever else it matched - a meal-planning card - because the age was never read.
    line = " ".join(str((understood or {}).get("clean") or "").lower().split())
    turning = TURNING.search(line)
    if turning:
        age = int(turning.group("age"))
        if 0 <= age <= 120 and any(number.get("value") == age
                                   for number in (understood or {}).get("numbers") or []):
            return age
    return None


# The words a line uses for a child when it is buying them something. The by-age row keyed only
# on "4 year old" and every other shape of the same fact - "my lad, hes 4 yr old", "my niece,
# shes 6", "my son for his 5th birthday", "my daughter who is 8" - fell through to the grown-up
# list, which offers a four-year-old good coffee and woolly socks. So the row takes the person
# and reads the age itself; the age is what decides which pool answers.
CHILD_PEOPLE = ("son", "daughter", "child", "children", "kid", "kids", "niece", "nephew",
                "grandson", "granddaughter", "grandchild", "grandchildren", "boy", "girl",
                "boys", "girls", "lad", "lads", "lass", "little one", "youngest", "eldest",
                "stepson", "stepdaughter", "godson", "goddaughter", "toddler",
                "schoolboy", "schoolgirl")
# "baby" is left out on purpose: a present for a new baby is its own question (gift-new-baby),
# and a baby named by its age is read from the months in the line.


def _a_child_is_the_one_they_buy_for(understood):
    """True when the person the present is for is a child, with no age in the line.

    The by-age row answers a line that says the age, and the person row answered every other
    line with the grown-up list - so "what should i get my nephew", "a present for my grandson"
    and "what should i get my child" were offered good coffee, a mug and woolly socks. The
    person is enough to know that list is wrong; only the age can choose the right one, so this
    decides which of the two answers the person row gives, not whether it answers.
    """
    words = _the_words(_said_line(understood))
    if words & set(CHILD_PEOPLE):
        return True
    return bool(words & {"teenager", "teenagers", "teen", "teens", "teenage",
                         "schoolkid", "schoolkids", "schoolboy", "schoolgirl"})


def _the_person_row(adult, child):
    """The person row, with the answer a child's present gets instead of the grown-up list.

    Both answers keep everything else the row does - the hobby the chat has named, the age the
    store already holds, the price and the cheap ask - because those are what make it a good
    answer; only the last-resort list is swapped.
    """
    grown_up = _gift_row(adult)
    young = _gift_row(child)

    def reply(memory, understood):
        chosen = young if _a_child_is_the_one_they_buy_for(understood) else grown_up
        return chosen(memory, understood)
    return reply


# What a child's present can still be without an age. The bands are the ones the age pools use,
# said plainly, so the person has something to act on and a reason to answer with the age.
CHILD_PRESENT = ("For a child the age is most of the answer, so it is worth asking. Under three, "
                 "something to push, stack or post. Four to seven, something to build, draw or "
                 "dress up. Eight to eleven, a kit or a game with real pieces. Twelve and up, "
                 "money towards one thing they have chosen. With no age to go on, a good book and "
                 "a small craft set is the safe pair, and paper and ribbon do the rest.")


# An age said any way a person says it: a figure, a figure with a year or a month, a word
# (`a two year old`), an ordinal (`his 5th birthday`) or the word for the band (`a teenager`).
# Nineteen is the last of the ordinals here on purpose: `her 60th` and `his 40th` name a
# grown-up's birthday in the older rows' own words, and those lines stay with the person row.
_AGE_WORDS = ("one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen"
              "|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen")
_AN_AGE = r"(?:\d{1,3}|" + _AGE_WORDS + r")"

_A_CHILDS_AGE = re.compile(
    r"\b(?:"
    # "4 yr old", "8 year-old", "6 months old", "a two year old"
    r"" + _AN_AGE + r"\s*(?:yr|yrs|year|years|yr-old|year-old)\s*(?:old|ole)?\b"
    r"|" + _AN_AGE + r"\s*months?\b"
    # "hes 4", "she is 6", "aged 8", "turning 3", "who is 17", "my son is 17", "she is two"
    r"|\b(?:hes|shes|he's|she's|he is|she is|who is|that is|is|aged|age|turning)\s*"
    r"" + _AN_AGE + r"\b"
    # "his 5th birthday", "her 13th"
    r"|\b(?:1[0-9]|[1-9])(?:st|nd|rd|th)\b"
    # a teenager or a toddler with no figure in the line is still a known band
    r"|\b(?:toddler|toddlers|preschool|preschooler|newborn|new born|teen|teens|teenager"
    r"|teenagers|teenage)\b"
    r")")


# The same ages as a number the row can choose a pool with: "hes 17", "his 17th" and "a two year
# old" are read here because the understanding keeps a figure only when the line gives it a unit,
# and a present for a seventeen-year-old still needs the pool for teenagers rather than the one
# for four-year-olds.
_SAID_AS_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
                  "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
                  "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
                  "eighteen": 18, "nineteen": 19}

_AN_AGE_SAID = re.compile(
    r"\b(?:(?P<years>" + _AN_AGE + r")\s*(?:yr|yrs|year|years|yr-old|year-old)\b"
    r"|(?P<months>\d{1,2}|" + _AGE_WORDS + r")\s*months?\b"
    r"|(?:hes|shes|he's|she's|he is|she is|who is|that is|is|aged|age|turning)\s*"
    r"(?P<near>" + _AN_AGE + r")\b"
    r"|(?P<ordinal>1[0-9]|[1-9])(?:st|nd|rd|th)\b)")


def _an_age_given(said):
    """The number of years a matched age says, counting a word as a number."""
    if said.isdigit():
        return int(said)
    return _SAID_AS_WORDS.get(said)


def _an_age_said_in_the_line(line):
    """The age a line gives, as a number of years, or None when it gives none."""
    found = _AN_AGE_SAID.search(str(line or "").lower())
    if not found:
        return None
    if found.group("months"):
        months = _an_age_given(found.group("months"))
        return months / 12.0 if months else None
    for name in ("years", "near", "ordinal"):
        if found.group(name):
            age = _an_age_given(found.group(name))
            return float(age) if age is not None else None
    return None


def _names_a_childs_age(line):
    """True when the line gives an age at all, however it says it.

    "4 yr old", "hes 4", "his 5th birthday", "aged 8", "a two year old" and "6 months old" are
    one fact, and it is the fact that decides which present pool answers. The row keyed only on
    the literal "4 year old", so every other shape fell through to the grown-up list, which
    offers a four-year-old good coffee and woolly socks. A grown-up named by an ordinal birthday
    ("her 60th", "my son for his 30th") does not match, so the person row keeps those.
    """
    if isinstance(line, dict):
        # the shape is offered the whole reading, and the memory in it carries the last age said;
        # only the line itself can say this one's age.
        line = line.get("clean") or line.get("text") or ""
    text = str(line or "").lower()
    return bool(_A_CHILDS_AGE.search(text))


def _this_row_answers_the_line(line):
    """True when the age row is the one to answer, and not the person row standing beside it.

    Two questions look alike and are not: "what should i get my niece, shes 6" is an age
    question, and "what should i get my niece for her birthday" is not - the child list the
    person row already holds is the right answer there, and an age pool would be a guess. So a
    line that names a child and gives no age stands this row down.

    A line that gives no figure and names no child stands it down on nothing: that is the turn
    after this row answered ("he likes lego and football", "budget 30 quid"), and the answer
    the person already got carries on from it. A guard that asked again for an age refused
    that turn and the chat fell to a neighbour instead - the adult-sport card on "football",
    the budget bands on "40" - so the memory keeping this row's keys is what makes the narrow
    guard the only safe one.
    """
    if isinstance(line, dict):
        # only the line itself: the memory in a reading carries the last age said, and that is
        # the age of the turn before, not this one.
        line = line.get("clean") or line.get("text") or ""
    text = str(line or "").lower()
    if not text:
        return False
    named = _a_child_is_named(text)
    if not _A_CHILDS_AGE.search(text):
        return not named
    age = _an_age_said_in_the_line(text)
    if named and age is not None and age > 19:
        return False        # "my son is 30 what should i get him" is the person row's
    return True


def _a_child_is_named(text):
    """True when the line names a child of someone (see CHILD_PEOPLE)."""
    words = re.findall(r"[a-z']+", str(text or "").lower())
    for person in CHILD_PEOPLE:
        if " " in person:
            if person in text:
                return True
        elif person in words:
            return True
    return False


def _gift_by_age(memory, understood):
    """A present for a named age: a toddler, a teenager and a 60-year-old want different things.

    The row used to answer every "for a X year old" with scooters and duplo. The age is already
    read off the line, so one entry can pick the right pool instead of treating a grown-up
    birthday as a child's.
    """
    low = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    # the reading keeps an age only when the line gives the figure a unit, so "my son, hes 17"
    # and "his 5th birthday" arrive here with nothing: the line itself is read for those, and a
    # present for a seventeen-year-old still goes to the teenager pool rather than the one for
    # four-year-olds.
    chosen = _gift_for_an_age(_an_age_in_the_line(understood)
                              or _an_age_said_in_the_line(low))
    if chosen:
        return chosen
    # "what should i buy a teenager" names no number, and the toddler and the teenager are both
    # worth reading off the word: the child list was answering all three.
    if re.search(r"\b(?:toddler|toddlers|preschool|preschooler|baby|babies)\b", low):
        return TODDLER_GIFT
    if re.search(r"\b(?:teen|teens|teenager|teenagers|teenage)\b", low):
        return TEEN_GIFT
    return CHILD_GIFT


def _the_age_row(memory, understood):
    """The age row, and the card the next turn asks about instead of another present."""
    card = the_card_after_a_present(understood, memory)
    if card:
        return card
    return _gift_by_age(memory, understood)


_WATCH_SMART = ("smart watch", "smartwatch", "smart watches", "smartwatches", "apple watch",
                "garmin", "fitbit", "galaxy watch", "fitness watch", "watch for running",
                "watch for steps", "track my steps", "track my sleep")
_WATCH_PLAIN = ("For a first proper watch, a plain quartz from Casio or Timex at £40 to £150 keeps "
                "better time than anything dearer; a mechanical watch is for people who enjoy "
                "them, not for accuracy. Look for a sapphire crystal if you can, 50m water "
                "resistance and a strap you can change yourself. What will you mostly wear it "
                "with?")
_WATCH_SMART_SAY = ("Buy for the battery first: most smartwatches last a day or two, so one that "
                    "lasts a week changes how you use it. A fitness band at £40 to £80 covers "
                    "steps, sleep and notifications; pay £200 to £300 only if you want a screen and "
                    "apps on your wrist, and expect the step and heart-rate numbers to be rough "
                    "rather than medical. Is it for exercise, notifications, or looks?")


# The lines that spend "watch" as the verb of a film, a series or a match. "watching" is a
# form of "watch", which is this entry's own key word, so "is it worth watching the wire"
# scored as a wristwatch question and got the quartz-and-sapphire answer; the ask word
# "worth" made it worse by fitting both questions. The verb is the difference, and a line
# that watches something is never a line about buying one.
_WATCH_VERBS = ("watching", "watched", "to watch", "worth watching", "worth a watch",
                "watch it", "watch on", "should i watch", "binge")
# "Watch for" is the phrasal verb - look out for - and never the thing on a wrist, whatever
# follows it: a question word ("any idea what i should watch for"), nothing at all, or the thing
# being watched for ("watch for swelling"). Read as the noun, a knee that clicks going upstairs
# followed by "any idea what i should watch for" got "a plain quartz from Casio or Timex" - the
# comedy answer, in the middle of a question about a body.
_WATCH_VERB_SHAPE = re.compile(
    r"\bwatch\s+(?:out\b"
    r"|for\s*(?:$|[?.!,;]"
    r"|\b(?:what|how|when|if|that|anything|something|signs?|symptoms?|changes?|it|them|"
    r"him|her|me|us|you)\b))")


def _watch_help(memory, understood):
    """A wristwatch is not a film, and a smartwatch is a different question from a first watch."""
    # Each form of the line on its own, not joined: the shape of "watch for" is read at the end
    # of a line, and a word after it that came from another field would hide that.
    forms = [str((understood or {}).get(key) or "").lower()
             for key in ("clean", "norm_text", "norm")]
    said = " ".join(forms)
    if any(word in said for word in _WATCH_SMART):
        # A smartwatch named off its own words keeps its answer even when the line has the verb in
        # it: "a watch for running" is a thing to buy, "watch for steps" is what a band does.
        return _WATCH_SMART_SAY
    if any(word in said for word in _WATCH_VERBS):
        return None
    if any(_WATCH_VERB_SHAPE.search(form) for form in forms):
        return None
    return _WATCH_PLAIN


# --- a present with a price on it ----------------------------------------------------
# "what should i get my dad for his 60th, under 40 quid" asks a different question from the same
# line without the limit: the answer has to be things that cost that much, or the limit was never
# heard. The same goes for a limit given as a follow-up ("what about under 40 quid"). The picks
# live here as data, one row per interest and one per band, so every gift entry can answer with
# them and there is no copy of the advice per recipient.
INTEREST_GIFTS = {
    "fishing": (("a float and hook kit", 12), ("a decent tackle box", 30),
                ("a landing net", 25), ("a good folding chair for the bank", 40)),
    "angling": (("a float and hook kit", 12), ("a decent tackle box", 30),
                ("a landing net", 25), ("a good folding chair for the bank", 40)),
    "tackle": (("a float and hook kit", 12), ("a decent tackle box", 30)),
    "gardening": (("good gloves that fit", 12), ("a decent trowel", 20),
                  ("secateurs", 30), ("a voucher for the nearest garden centre", 25)),
    "garden": (("good gloves that fit", 12), ("a decent trowel", 20),
               ("secateurs", 30), ("a voucher for the nearest garden centre", 25)),
    "plants": (("a good houseplant in a proper pot", 15), ("a nice watering can", 25)),
    "allotment": (("good gloves that fit", 12), ("secateurs", 30),
                  ("a voucher for the nearest garden centre", 25)),
    "cooking": (("a decent chef's knife", 35), ("a good olive oil and a nice tin", 20),
                ("an apron and a decent wooden spoon", 15)),
    "baking": (("a good loaf tin", 12), ("a set of measuring spoons and a decent vanilla", 12)),
    "reading": (("a paperback they would not pick themselves", 10),
                ("a book token", 20), ("a nice bookmark and a good bar of chocolate", 8)),
    "books": (("a paperback they would not pick themselves", 10),
              ("a book token", 20)),
    "music": (("a record or CD they would not buy", 20), ("a voucher for a record shop", 25)),
    "running": (("a head torch", 20), ("good running socks", 15), ("a decent water bottle", 15)),
    "cycling": (("a good bike light set", 25), ("a decent multi-tool", 20)),
    "football": (("a club shirt", 45), ("good socks and a proper ball", 25)),
    "films": (("a cinema voucher", 20), ("a good film on disc", 12)),
    "photography": (("a decent camera strap", 20), ("a good memory card", 20)),
    "knitting": (("a skein of good wool", 15), ("a decent set of needles", 20)),
    "sewing": (("a good pair of fabric scissors", 20), ("a decent seam ripper and pins", 12)),
    "coffee": (("good ground coffee", 15), ("a decent cafetiere", 25),
               ("a nice mug and a bag of good beans", 20)),
    "tea": (("a proper loose-leaf tea and a strainer", 15), ("a nice mug and good tea", 18)),
    "gaming": (("a voucher for the shop they use", 25), ("a good headset", 35)),
    "birdwatching": (("a decent pair of binoculars", 45), ("a bird book for their area", 15)),
    "diy": (("a good screwdriver set", 25), ("a decent tape measure", 12)),
}

# The picks when the limit is all we know: one thing that gets used, not three that might.
PRESENT_BANDS = (
    (10, "Under {money}, buy one small thing properly rather than three cheap ones: a bar of the "
         "good chocolate, a decent paperback, a nice bar of soap, or good coffee."),
    (20, "For under {money}, buy one thing they will use this month: a decent paperback, good "
         "chocolate, a jar of something they like, or a small plant in a proper pot."),
    (40, "For under {money}, one good thing beats three safe ones: a decent thermos, woolly socks "
         "and a book, good olive oil and a nice tin, or a voucher for something they already do "
         "at the weekend."),
    (100, "Under {money} you can buy an experience rather than an object: two cinema tickets and "
          "dinner, a day out they would not book themselves, or a decent bottle with a good "
          "glass to drink it from."),
)
PRESENT_OVER = ("At {money} there is room for the proper version of something they use every day "
                "and would not spend on themselves - a good bag, a decent pair of boots, or the "
                "thing they have been putting off - and a real message in the card.")


# Said when the limit is all we know and no hobby was named: the person's own interests beat any
# list of safe presents, so the band names the move rather than pretending to know them.
BUY_INTO = (" If you know what they are into, buy into that instead: secateurs for a gardener, "
            "a head torch for a runner, a knife for someone who cooks.")


def _money(amount):
    """A price the way people write it: whole pounds stay whole."""
    try:
        amount = int(round(float(amount)))
    except (TypeError, ValueError):
        return ""
    return "\u00a3%d" % amount


def _interest_phrase(interests):
    """"fishing", "fishing and gardening", "fishing, gardening and baking" - and no he or she."""
    named = [str(word) for word in interests if word]
    if not named:
        return ""
    if len(named) == 1:
        return named[0]
    return ", ".join(named[:-1]) + " and " + named[-1]


def present_within(money, interests=()):
    """A present at a price: the picks that fit under it, or one good thing at that money.

    The interest comes from the conversation ("he likes fishing" a turn earlier), so the limit is
    answered about the same person the earlier answer was about, and it is never said back with a
    pronoun that might be wrong.
    """
    wanted = _interest_phrase(interests)
    fits = []
    for interest in interests or ():
        for item, price in INTEREST_GIFTS.get(str(interest).lower(), ()):
            if price <= money and (item, price) not in fits:
                fits.append((item, price))
    fits.sort(key=lambda pair: -pair[1])
    if fits:
        listed = ", ".join("%s (%s)" % (item, _money(price)) for item, price in fits[:2])
        if money >= 40 and fits[0][1] < money / 2:
            # The budget is generous for this interest: name the picks that fit and say so, rather
            # than pretending a £20 book token is what £100 was asked for.
            return ("%s is plenty for someone into %s: %s, and the rest towards something they "
                    "have been putting off." % (_money(money), wanted, listed))
        return ("%s or less, for someone into %s: %s. Buy the one thing they will actually use "
                "rather than three they might, and put a real message in the card."
                % (_money(money), wanted, listed))
    if not money:
        return PRESENT_OVER.format(money="that")
    for band, advice in PRESENT_BANDS:
        if money <= band:
            return _with_buy_into(advice.format(money=_money(money)), interests)
    return _with_buy_into(PRESENT_OVER.format(money=_money(money)), interests)


def _with_buy_into(advice, interests=()):
    """The band, plus the one line a band cannot know: buy into what they are already into."""
    return advice if interests else advice + BUY_INTO


def present_less(interests=()):
    """"Anything cheaper?": the dearest pick under a tenner, or the small-things band."""
    wanted = _interest_phrase(interests)
    fits = []
    for interest in interests or ():
        for item, price in INTEREST_GIFTS.get(str(interest).lower(), ()):
            if item not in [name for name, _ in fits]:
                fits.append((item, price))
    if fits:
        # The cheapest thing that is still that interest: for a reader it is a paperback at a
        # tenner, for a cyclist a multi-tool at twenty. A smaller version of the right idea beats
        # a cheaper thing about nothing.
        fits.sort(key=lambda pair: pair[1])
        item, price = fits[0]
        return ("Cheaper than that: %s (%s) is the small version of the same idea for someone into "
                "%s, and a good one beats something bigger and cheaper." % (item, _money(price),
                                                                            wanted))
    return ("Cheaper than that: go for the small version of the same idea - a good bar of "
            "chocolate, a decent paperback, nice soap, or a packet of good coffee - and let the "
            "card do the rest.")


# The coat answer for the weather the line names, in the order the line is read: a filler says
# down or synthetic, a town coat says wool, and a shell says rain. A line that names none of them
# gets the choice, because that is what it is asking.
_COAT_KINDS = (
    (("down", "puffer", "padded", "padding", "quilted", "synthetic", "insulated",
      "insulation"),
     "Down is the warmest for its weight and packs down small, so look for 600 fill power or "
     "more and it will last a decade, but it insulates badly once it is wet. Synthetic padding "
     "costs about half as much, is heavier and bulkier, and still keeps you warm when damp, "
     "which suits a wet winter better than down unless you want it for real cold."),
    # A coat for an occasion is a town coat whatever the weather is doing: "how do i pick a coat
    # for a wedding in winter" got the choice of shell and puffer, which answered a question
    # about walking.
    (("wedding", "funeral", "christening", "interview", "smart", "formal", "dress code", "party",
      "office", "town", "work"),
     "For anything smart - a wedding, a funeral, a winter interview - a wool or wool-blend coat "
     "is the answer: it hangs properly over a dress or a suit, and a mid-calf length in navy, "
     "grey, camel or black goes with everything. Check that it closes over the jacket you will "
     "wear underneath and try it on in the shoes you will be standing in, because a heavy coat "
     "pushes the shoulders up."),
    (("wool", "woollen", "woolen", "duffle", "tweed", "overcoat"),
     "A wool coat is warm, smart enough for town and fine in a shower, but it gets heavy once "
     "it is soaked and wants dry cleaning rather than a wash. Check the lining and the buttons, "
     "buy it loose enough for a jumper under it, and keep it for the days you are not out in "
     "the rain."),
    (("waterproof", "rain", "shell", "gore", "storm", "wet"),
     "For rain, a waterproof shell with taped seams (Gore-Tex or similar) at £150 to £250 "
     "outlasts three cheap ones: check the hood, the zip and the seams under the arms, and try "
     "it on over a jumper. A shower-resistant jacket is fine for a dash to the shops and no good "
     "for a wet walk."),
    # The question of whether to spend at all: "is it worth getting a proper coat" wants a yes
    # and a figure, not the choice of shell and puffer.
    (("worth", "expensive", "spend", "how much", "cheaper", "budget", "value", "price"),
     "Yes, if it is one you will wear for years: a coat is the piece of clothing where the money "
     "shows, and £80 to £150 buys a padded coat that lasts a decade, £150 to £250 a waterproof "
     "shell that does not leak at the shoulders. Cheap coats cost more in the end because the "
     "zip goes and the seams soak through, so buy the best you can in a plain colour you will "
     "still wear in five years."),
)

# What to look at in the fitting room, apart from the weather the coat is for. It is its own
# answer because a chat about a coat asks it as its own question ("what should i look for"), and
# the same paragraph told twice in a row is no answer the second time.
_COAT_CHECK = ("Check the hood stays up in wind, the zip works with gloves on, the seams are taped "
               "and there is room for a jumper underneath. Look at the lining where it rubs under "
               "the arm and at the stitching on the pockets: those are the two places a cheap coat "
               "shows itself first.")
# The height a person gives ("im about 5 foot 4") is a coat-length question, and answering it is
# better than reading the coat paragraph back at them.
_HEIGHT = re.compile(r"\b(\d)\s*(?:foot|feet|ft|')\s*(\d{1,2})\b")


def _coat_to_buy(memory, understood):
    """The coat for the weather the line names, or the choice between them when it names none."""
    reading = understood if isinstance(understood, dict) else {}
    said = " ".join(str(part) for part in (
        reading.get("clean"), reading.get("text"), " ".join(reading.get("words") or ())
    )).lower()
    tall = _HEIGHT.search(said)
    if tall:
        feet, inches = tall.group(1), tall.group(2)
        total = int(feet) * 12 + int(inches)
        # A coat sits from the shoulder to the knee or the thigh, and that is about half the
        # person's height: short enough to walk in, long enough to keep the legs warm.
        low, high = int(total * 0.42), int(total * 0.50)
        return ("At %s foot %s, look for a coat about %d to %d inches from the shoulder - mid-thigh "
                "on you - so it keeps your legs warm without swamping you. Check the sleeve ends "
                "at your wrist bone with your arms down, and try it on over the thickest jumper "
                "you own." % (feet, inches, low, high))
    for words, reply in _COAT_KINDS:
        if any(re.search(r"\b" + re.escape(word), said) for word in words):
            return reply
    generic = ("Pick the coat by the weather you are actually out in: a waterproof shell for "
               "rain, down or padded for cold and dry, wool for town. £80 to £150 buys a padded "
               "coat that lasts a decade, £150 to £250 a waterproof shell that does not leak at "
               "the shoulders.")
    if _mentions_coat_check(said):
        # The fitting-room part on its own once the choice has been given: a chat that asks
        # "what should i look for" after "i need a new winter coat" wants the checklist, and the
        # same paragraph twice in a row answers nothing the second time.
        return _COAT_CHECK if _coat_said_already(memory) else generic + " " + _COAT_CHECK
    return generic


# The parts of a coat a line asks about when it wants the fitting-room answer rather than the
# weather one: "what should i look for", "how should it fit", "how long should it be".
_COAT_CHECK_WORDS = ("look for", "look out for", "check", "what should i", "fit", "fits", "long",
                     "length", "short", "tall", "size", "sizing", "cuff", "hood", "sleeve",
                     "sleeves", "quality", "warm enough")


def _coat_said_already(memory):
    """True when the coat choice has already been given in this conversation."""
    from ..memory import last_bot

    said = str(last_bot(memory) or "").lower()
    return ("buys a padded coat" in said or "pick the coat by the weather" in said
            or "waterproof shell with taped seams" in said)


_NAMED_BY_PRONOUN = {"her", "him", "them", "hers", "his", "theirs"}


def _nobody_named_by_pronoun(understood):
    """False when the line names the person by pronoun, so the pronoun rows keep their line."""
    if not isinstance(understood, dict):
        return True
    words = understood.get("words") or understood.get("norm") or ()
    return not _NAMED_BY_PRONOUN.intersection(str(word).lower() for word in words)


def _mentions_coat_check(said):
    return any(re.search(r"\b" + re.escape(word), said) for word in _COAT_CHECK_WORDS)

# "do i need to keep the receipt" and "do i need to keep receipts" were answered by a row this
# change deletes, and the tax retention card took them: somebody asking whether the slip matters
# for a return was told to keep invoices for five years after the filing deadline. The keep shape
# answers on the return row again, and a length or a tax word still stands it down, because that
# is the record-keeping card's line.
_KEEP_RECEIPT_RE = re.compile(
    r"\b(?:how long|how many|years?|months?|decades?|tax return|self assessment|expense claim|"
    r"expenses claim|employer|for work|at work|work expenses)\b")


def _not_a_length(understood):
    """True unless the line is about keeping papers for a length or for tax, which is another card."""
    if not isinstance(understood, dict):
        return True
    said = ("%s %s" % (understood.get("text") or "", understood.get("clean") or "")).lower()
    return not _KEEP_RECEIPT_RE.search(said)



def _the_bag_is_not_packaging(understood):
    """Whether the line is asking about the bag rather than about the food in it.

    "Why does bread go mouldy in a plastic bag" names a plastic bag and a loaf, and the loaf is
    the question. A line that does name a keeping question about a food is the food's, so this
    row stands down for it.
    """
    return not a_food_is_being_kept(understood)

def _the_place_not_the_shop(understood):
    """A line about going to a place is not a question about the shop of the same name.

    "what should i pack for iceland", "packing for a trip to iceland" and "what should i pack for
    iceland in october" were all answered "Iceland is cheap for frozen food ... one of the
    cheapest places to do a full shop": the country, read as the shop. The row keys on the shop
    names in the table and asks with "should i", so a country in the line was enough, and Iceland
    is the one name in the table that is also a place people travel to. A line that says what is
    being taken, or that asks about the trip itself, is the travel lanes' question and this row
    stands down. One that names a price or a shop as well keeps the row, because "is iceland
    cheaper than asda" and "is iceland as good as farmfoods" are about the shop.
    """
    said = " " + (understood.get("clean") or understood.get("text") or "").lower() + " "
    going = (" pack", " packing", " trip", " travel", " travelling", " traveling", " flight",
             " fly", " holiday", " holidays", " visit", " visiting", " hotel", " weather",
             " things to do", " airport", " tourist", " sightseeing", " northern lights",
             " what to wear", " what to take", " what to see", " in october", " in november",
             " in december", " in january", " in february", " in march")
    # A holiday line also carries the words a shop line uses - "is iceland good with kids" and
    # "how many days should i spend in iceland" were both told where the shop sits on price,
    # because "good" is a quality word and neither line has a trip word in it at all. So a
    # handful of phrases that only make sense about a place stand the row down whatever else the
    # line says; a price or a shop in the line is otherwise enough to keep it.
    place = (" with kids", " with children", " with a family", " with the family", " with a baby",
             " how many days", " how long", " best time to", " when to go", " worth visiting",
             " things to do", " it worth going", " reykjavik", " blue lagoon", " golden circle",
             " whale watching", " northern lights", " hire car", " car hire", " road trip",
             " visa", " what to pack", " what to wear", " is it safe", " safe to")
    price = (" cheap", " cheaper", " price", " prices", " quality", " fresh", " value",
             " compare", " comparison", " expensive", " basket", " groceries", " supermarket",
             " shop")
    if any(word in said for word in place):
        return False
    if any(word in said for word in going) and not any(word in said for word in price):
        return False
    return True


ENTRIES = [
    # Buying wine is a shopping question, not a cooking one: "whats a good cheap wine" was a
    # shrug, while the pairing, the sauce and the open-bottle lines belong to cooking.py. The row
    # says what to look for on the label, so it answers the cheap bottle however it is asked for.
    entry("wine-pick", (("wine", "wines", "red wine", "white wine", "rose", "prosecco",
                         "supermarket wine", "red", "fizz", "champagne"),
                        ("cheap", "cheaper", "good", "nice", "decent", "best", "pick", "choose",
                         "buy", "buying", "recommend", "bargain", "tenner", "budget", "bottle",
                         "bottles", "supermarket", "worth", "shopping for"),
                        # the choosing itself is a third signal: "how do i pick a decent bottle
                        # of red" is a buying question even without the word wine in it
                        ("pick", "picking", "which", "choose", "choosing", "buying", "recommend",
                         "looking for", "under a tenner", "good value", "worth buying")),
          "Buy the shop's own-label bottle from a named region rather than a brand at the same "
          "price: a \u00a37 C\u00f4tes du Rh\u00f4ne, Rioja or Chianti from the supermarket's own range usually "
          "beats a \u00a37 brand, because you are paying for the wine and not the label. On a red, look "
          "for the words reserva, crianza or a named village; for a white, Picpoul, Muscadet and an "
          "own-label Albari\u00f1o are the safest cheap buys, and a screw cap keeps it fresher. Skip the "
          "half-price 'was \u00a312' bottles - the plain \u00a36 to \u00a39 rows are where the value is. For "
          "fizz, the word Valdobbiadene on a prosecco, or a Cr\u00e9mant instead of champagne, gets you "
          "the same evening for a third of the price.",
          # a wine word has to be in the line somewhere: the choosing words alone reached
          # "which toothbrush should i buy", and the bottle is the thing being bought
          ask=("wine", "wines", "red", "white", "rose", "prosecco", "fizz", "champagne",
               "bottle", "bottles", "merlot", "rioja", "shiraz", "pinot", "chardonnay"),
          # a pairing, a sauce, an opened bottle, a gift or a spill is not this question
          avoid=("goes with", "go with", "pair", "pairing", "with lamb", "with steak", "with fish",
                 "with chicken", "sauce", "stew", "deglaze", "cook", "cooking", "recipe",
                 "open bottle", "opened", "keeps", "keep", "freeze", "leftover", "how long",
                 "gift", "present", "birthday", "christmas", "units", "calorie", "calories",
                 "pregnan", "breastfeed", "allergy", "sulphite", "stain", "carpet", "spill",
                 "hangover", "how many",
                 # "red" and "white" are the wine words only when something is being bought: a
                 # red cabbage, red meat or a white sauce is a cooking question
                 "cabbage", "meat", "beef", "onion", "onions", "pepper", "peppers", "lentil",
                 "lentils", "bean", "beans", "rice", "curry", "good for you", "healthy",
                 "healthier", "vitamin", "vitamins", "iron", "protein", "sugar", "salt",
                 # a red or a white thing that is not a drink: paint, a shirt, a wall
                 "paint", "paintwork", "primer", "wall", "walls", "ceiling", "shirt", "shirts",
                 "dress", "dresses", "curtain", "curtains", "sofa", "sofas", "shoes", "trainers",
                 "socks", "jumper", "bedding", "sheet", "sheets", "ink", "printer")),
    # --- laptops and phones ------------------------------------------------------
    # "should i buy apple care for my laptop" is a device question, not the appliance warranty
    # in money.py: the answer is what the plan covers and what the repair costs without it.
    entry("applecare", (("apple care", "applecare", "apple care plus", "applecare plus",
                         "protection plan"),
                        ("laptop", "macbook", "mac", "iphone", "ipad", "phone", "device", "worth",
                         "buy", "get", "cancel", "need", "should i")),
          "Worth it mainly for accidental damage on a Mac or an iPhone: a screen repair is around "
          "£100 to £300 without it, and the plan covers two incidents a year with an excess of "
          "roughly £25 to £79 depending on the device. Skip it if your home contents insurance or "
          "the card you paid with already covers the device; the free one-year warranty covers "
          "faults, never drops.",
          bias=1),
    # A device out of warranty still has the shop on the hook, and the lines that said so got an
    # "ugh, that's a lot to carry" reply before this: the retailer owes a repair or replacement
    # for up to six years in England, Wales and Northern Ireland, five in Scotland.
    entry("warranty-claim",
          (("warranty", "guarantee", "extended warranty", "out of warranty", "still covered"),
           ("claim", "broke", "broken", "faulty", "fix", "fixed", "repair", "replace",
            "replacement", "expired", "ran out", "run out", "cover", "covered",
            "receipt", "shop", "store", "currys", "argos", "john lewis", "back", "money")),
          "Claim from the shop you bought it from, not the warranty: in the UK the retailer owes "
          "you a repair or replacement for up to six years in England, Wales and Northern Ireland "
          "(five in Scotland), and a manufacturer's guarantee sits on top of that rather than "
          "replacing it. Put it in writing with the order number, the fault and the date, and ask "
          "for a repair, a replacement or a refund in that order. Out of warranty, ask anyway: a "
          "goodwill repair is common, and the card you paid with may carry its own cover.",
          # the appliance that is worth repairing, and a car's parts guarantee, are other answers
          avoid=("boiler", "washing machine", "fridge", "freezer", "oven", "dishwasher", "tumble",
                 "car", "van", "tyres", "service", "mot", "parts", "engine")),
    entry("laptop-pick", ("laptop", ("pick", "buy", "choose", "recommend", "good", "need", "new",
                                     "one", "help", "look for", "what to look for", "specs",
                                     "spec", "ram", "memory", "storage", "upgrade", "upgrading",
                                     "upgrad",
                                     # "not sure which laptop to get" asks the question with
                                     # no word from the list above; `ask` is what keeps these
                                     # three from answering a line about a laptop that is broken
                                     "which", "what", "get")),
          _laptop_general, ask=CHOOSING,
          avoid=("battery", "cracked", "screen", "keyboard", "keys", "charger", "charging",
                 "slow", "fan", "loud", "hot", "overheat", "crash", "freeze", "virus",
                 "wont", "won't", "broken", "repair", "fix", "pdf", "form", "password",
                 "reset", "install",
                 # "take my laptop out at security" is an airport line, not a buying one.
                 "security", "airport", "tray",
                 # "which laptop did you like best" asks the bot about itself, not for advice
                 "did you", "you like", "your favourite", "your favorite")),
    # "Is it worth upgrading the memory?" is not "which laptop should I buy": a person who
    # already owns the machine wants to know whether the part is worth buying, and a laptop
    # entry that met the line through "upgrade" in CHOOSING gave them buying advice instead.
    entry("laptop-upgrade", ("laptop", ("upgrade", "upgrading", "upgrad", "more ram",
                                        "more memory")),
          ("Yes, if you keep running out of memory: going from 8GB to 16GB is the upgrade that "
           "shows up most, and it is £30 to £60 if the laptop has a slot you can open. Check the "
           "model takes a stick first, because many thin ones are soldered, and a bigger SSD helps "
           "more than RAM if the drive is the thing that is always full."),
          ask=(("upgrade", "upgrading", "upgrad", "more ram", "more memory"),), bias=2,
          avoid=("which laptop", "buy a laptop", "new laptop", "replace my laptop",
                 # a disk is a different part with a different answer: "should i upgrade my
                 # laptop to an ssd" was getting the memory one.
                 "ssd", "ssds", "hard drive", "hard disk", "disk")),
    entry("laptop-creative", ("laptop", (("video editing", "video edit", "editing", "gaming",
                                          "games", "photoshop", "architecture", "cad", "design",
                                          "3d", "render", "blender"))),
          ("For video editing, gaming or CAD you do need a dedicated graphics card: look for 16GB "
           "of RAM (32GB for 4K video) and a screen that covers 100% sRGB. Expect to pay £900 to "
           "£1,300, and check the weight before you commit to carrying it."), bias=1),
    entry("laptop-student", ("laptop", ("student", "uni", "university", "school", "cheap", "budget",
                                        "essays", "coursework")),
          ("For essays, video calls and Netflix, almost anything current works: 8GB RAM, a 256GB "
           "SSD and a 14 inch screen, around £400 to £550. A Chromebook is fine if everything lives "
           "in Google Docs, but avoid it for a course that needs Windows software."), bias=1),
    entry("phone-refurbished", (("phone", "iphone", "android", "handset", "mobile"),
                                ("refurbished", "used", "second hand", "cheap", "new")),
          ("A refurbished phone is a good way to save 30 to 50%: buy from a seller who grades the "
           "condition and gives a 12-month warranty, and check the battery health figure. Avoid "
           "anything sold as \"for parts\" or with an iCloud lock."),
          # "new" is also how people say "I have just got a new phone", which is a transfer
          # question, not a buying one, so the entry only answers a line that asks about buying.
          ask=("buy", "buying", "bought", "worth", "cheap", "cheaper", "refurbished", "refurb",
               "used", "second hand", "secondhand", "recommend", "should i get", "pay", "price",
               # the shapes that ask for a new handset without using "buy"
               "need a", "need some", "want a", "budget", "afford", "spend", "looking for"),
          # "should i get a new phone or fix this one" asks about the phone in the person's hand,
          # so the repair-or-replace entry answers it, not the one about buying a replacement.
          avoid=("fix", "fixing", "repair", "repairing", "broken", "cracked", "wont charge",
                 "not charging", "battery drains")),

    # --- shoes and clothes -------------------------------------------------------
    # "what should I look for in a new phone" is a buying question about a new handset, which the
    # refurbished entry deliberately keeps away from. "new" is not in the key: "I have just got a
    # new phone" is a transfer question, so the buying words are the ones that say "buy".
    entry("phone-pick", (("phone", "iphone", "android", "handset"),
                         ("buy", "buying", "choose", "choosing", "look for", "look out for",
                          "best", "worth", "recommend", "which", "upgrade", "buying one")),
          ("Spend on the battery and the update years, not the camera: a mid-range phone at £250 to "
           "£400 lasts as long as a flagship if the maker promises four or five years of security "
           "updates (Samsung, Google and Apple do; many cheap brands promise two). Get at least "
           "128GB, check the battery is 5,000mAh or more, and make sure it takes a physical SIM as "
           "well as an eSIM if you travel."),
          # A phone with something wrong with it is the other modules' line, not a buying one.
          avoid=("battery", "batteries", "charge", "charging", "screen", "cracked", "crack",
                 "lost", "lost it", "water", "wet", "hot", "slow", "storage", "full",
                 "transfer", "wont turn on", "turn on", "screenshot", "print", "repair",
                 "fix", "broken", "move", "wifi", "everything")),
    entry("running-shoes", (("running shoes", "running trainers", "trainers", "shoes", "runners"),
                            ("expensive", "worth", "running", "run", "jog", "jogging", "marathon",
                             "parkrun", "5k", "10k", "pay", "price")),
          ("For running, yes: a proper pair makes a real difference to your knees, and a running "
           "shop will watch you run and fit you for £90 to £130. Replace them every 500 to 800km, "
           "or when the midsole feels flat."), bias=1,
          # A personal trainer is a person, not a pair of trainers.
          avoid=("personal trainer", "dog trainer", "a trainer", "gym trainer", "trainer at",
                 # a cheap pair of school shoes is a buying question, not a running one; the
                 # money words alone used to bring every "cheap shoes" line here. The school is
                 # the subject, not the child: "my son needs running shoes" is still a running
                 # shoe, and a child word alone took that card away from every parent.
                 "school", "schools", "nursery", "uniform", "plimsolls",
                 # a pair that is already wet asks how to dry it, not which pair to buy:
                 # "how do i dry my running shoes" was this row, because "running" and "shoes"
                 # are the key and "dry" is not in it
                 "dry", "drying", "dried", "soaked", "soaking", "newspaper", "radiator",
                 "washing machine", "smelly", "smell", "clean them", "clean my")),
    # "where can i buy cheap school shoes" was answered with the running-shoe card ("For running,
    # yes: ... £90 to £130"), because the only buying word a school-shoe line ever says - cheap,
    # afford, spend - was also a running-shoe word. A parent asking where to buy has a question
    # of its own, and the fitting answer next door is about the size, not the shop.
    entry("shoes-buy-cheap",
          # The school shoe itself is the key, and the money words are not: a parent asking
          # "what school shoes for a 5 year old" or "school shoes for a teenager" has the same
          # question as the one asking where to buy cheap ones, and both were a hedge and an
          # echo while the row waited for "cheap". The bare "shoes" and "trainers" came out with
          # them: they are the running and the standing rows' words, and the money words alone
          # brought "personal trainer prices" here.
          (("school shoes", "school shoe", "school trainers", "school footwear",
            "shoes for school", "school uniform shoes", "uniform shoes", "kids shoes",
            "kids trainers", "kids school shoes", "childrens shoes", "children's shoes",
            "nursery shoes", "reception shoes", "plimsolls"),
           # The money words are not the only way to ask: "what school shoes for a 5 year
           # old" and "school shoes for a teenager" are the same buying question and were a
           # hedge and an echo while the row waited for "cheap".
           ("cheap", "cheapest", "afford", "where", "shop", "shops", "buy cheap", "buying",
            "buy", "price", "prices", "cost", "spend", "pairs", "pair of", "pair",
            "year old", "old", "age", "teenager", "teen", "boys", "girls", "september",
            "start school", "starting school", "back to school", "which",
            # not a bare "what" or "shoes": "and what about shoes", a follow-up to a running
            # answer, would match on those two words and get a child's school card
            "what school", "what kind of school", "which school")),
          ("Cheap is fine if the fit and the sole are right: supermarket own-brands are £10 to "
           "£25, and an outlet or the January sales gets a good pair at £25 to £35 rather than "
           "£50. Check for a thumb's width at the toe, room across the widest part and a sole you "
           "can bend - a school-age child will need the next size in four to six months."),
          # "my son needs new school shoes" and "my kids shoes are too small" are the fitting
          # answer's lines: they are about the size, and the size words are kept out here.
          avoid=("too small", "too tight", "fit", "fits", "fitting", "size", "sizes", "measure",
                 "blister", "blisters", "rub", "rubs", "rubbing", "hurt", "hurts", "hurting",
                 "sore", "uncomfortable", "smelly", "smell", "clean", "polish", "scuff",
                 "repair", "split", "return", "refund", "lost", "wet", "muddy", "new",
                 "running", "run", "jog", "jogging", "marathon", "parkrun", "5k", "gym",
                 "wedding", "work", "safety", "steel toe", "heels",
                 # a person who trains somebody is not a pair of shoes, and these words were
                 # in the running row's avoid alone, so they fell through to this one
                 "personal trainer", "personal trainers", "dog trainer", "dog trainers",
                 "gym trainer", "trainer at", "a trainer", "pt session"),
          bias=1),
    entry("shoes-standing", (("shoes", "trainers", "boots"),
                             ("standing", "walking", "comfortable", "all day", "work", "feet")),
          ("For standing all day, prioritise a cushioned sole, room at the toes and a snug heel, "
           "and buy at the end of the day when your feet are at their biggest. Two pairs worn "
           "alternately last far longer than one."),
          # Walking is this entry's subject, but a squeak or a creak is the noise question.
          # A spot of mould or a smell is not a question about comfort: "there is mould on my
          # walking boots" was this card on main, and the row for mould on fabric wants it.
          avoid=("squeak", "squeaks", "squeaking", "squeaky", "creak", "creaking", "noise",
                 "noisy", "mould", "moulds", "mold", "molds", "mouldy", "moldy", "mildew",
                 "mildewy", "musty", "mustiness", "smell", "smells", "smelly", "damp", "spores")),
    entry("coat-worth", (("coat", "jacket", "raincoat", "parka", "puffer", "anorak", "duffle",
                          "overcoat", "shell"),
                         ("worth", "expensive", "buy", "buying", "waterproof", "warm", "warmest",
                          "good", "look for", "look out for", "choose", "choosing",
                          "pick", "pick out", "last", "lasts", "which", "what", "best",
                          "material", "fabric", "winter", "cold", "wind", "rain", "spend",
                          "cheap", "budget", "price", "under", "quid", "recommend", "need",
                          "get")),
          _coat_to_buy,
          # "warm" and "jacket" are also how a fault is reported, and the buying answer cannot help;
          # a coat for a child is clothing's own row, which knows about car seats and prams
          avoid=("zip", "zipper", "broken", "broke", "torn", "tear", "tore", "hole", "holes",
                 "ripped", "rip", "seam", "seams", "stuck", "lost", "leak", "leaks", "leaking",
                 "wet inside", "damp", "child", "children", "kid", "kids", "son", "daughter",
                 "toddler", "baby", "babies", "pram", "pushchair", "buggy", "car seat",
                 "boy", "girl", "year old",
                 # whether a coat is needed today is a forecast question: "do i need a coat
                 # tonight" answered with how to choose one
                 "tonight", "today", "tomorrow", "right now", "this morning", "this afternoon",
                 "this evening", "weather", "forecast", "cold out", "chilly out", "warm out",
                 "raining", "rain today", "umbrella",
                 # a coat that already has something wrong with it is a wash, a stain or a
                 # repair: "how do i get a stain out of a wool coat" was answered with how to
                 # choose one
                 "stain", "stains", "stained", "mark", "marks", "dirty", "dirt", "mud", "grease",
                 "wash", "washing", "clean", "cleaned", "cleaner", "sponge", "brush",
                 # keeping a coat through the summer is the storage card, not this one: "how do i
                 # store a winter coat" has "winter coat" and "how do i", which is enough for the
                 # buying row, and the answer to it is moths and a breathable bag
                 "store", "stores", "stored", "storing", "storage", "put away", "pack away",
                 "packed away", "put it away", "away for the summer", "until next winter",
                 "till next winter", "moths", "moth", "cedar", "vacuum bag", "garment bag",
                 "dry clean", "dry-clean", "dry cleaning", "dry-cleaned")),

    # --- bikes -------------------------------------------------------------------
    entry("bike-second-hand", ("bike", ("second hand", "used", "check", "buy", "before", "worth",
                                        "choose", "choosing", "look for", "look out for")),
          ("Check the frame for cracks and dents around the welds, spin both wheels to see if they "
           "wobble, and test the brakes and gears on a ride. Ask for the frame number and check it "
           "against a stolen-bike register before you pay; a service costs £50 to £95, so leave "
           "room in the budget."),
          # a bike that is already yours and slipping is a repair question, not a buying one
          avoid=("gears", "gear", "slip", "slips", "slipping", "chain", "brakes", "brake",
                 "puncture", "punctures", "tyre", "tyres", "wheel", "wheels", "rusty", "rust",
                 "squeak", "squeaks", "squeaking", "click", "clicking", "noisy"),
          bias=1),
    entry("bike-kids", ("bike", ("child", "kid", "kids", "age", "size", "grow")),
          ("Go by inside leg, not age: a child should be able to put both feet flat on the ground "
           "with the saddle at its lowest. A bike one size up with the seat down is safer than an "
           "oversized one they can't control, and balance bikes beat stabilisers.")),
    # teaching is not sizing: "how do i teach my son to ride a bike" used to land on the inside-leg
    # answer above, which never tells you how to teach anybody anything
    entry("learn-to-ride", (("ride", "riding", "pedal", "pedalling", "cycle", "cycling"),
                            ("teach", "teaching", "learn", "learning", "child", "kid", "kids",
                             "son", "daughter", "toddler", "stabilisers", "balance bike",
                             # "i cant ride a bike" is the same ask as "how do i learn", and an
                             # adult saying they never learnt got the listening reply
                             "cant", "can't", "cannot", "never learnt", "never learned")),
          ("Take the pedals off and drop the saddle until both feet reach the ground, then let them "
           "push along and coast with their feet up - a child who can balance for five seconds can "
           "ride, and an adult learning does the same on a bike with the saddle low. Hold the back of "
           "the saddle, not the handlebars, when they first pedal, and let go without saying so. "
           "Twenty minutes at a time beats an afternoon, and a flat, empty car park beats a narrow "
           "pavement."),
          # "how do i get rid of a verruca on my sons foot" is not a child learning to ride: the
          # loose match on "rid" and "son" was enough to answer it with a bike lesson
          avoid=("verruca", "verrucas", "wart", "warts", "foot", "feet", "itch", "itchy",
                 "sore", "hurts", "pain", "blister", "blisters", "toe", "toes", "nail",
                 "nails", "skin", "rash")),

    # --- home kit ----------------------------------------------------------------
    entry("office-chair", (("office chair", "desk chair", "chair"),
                           ("cost", "much", "price", "spend", "decent", "budget", "pay",
                            "worth", "good", "buy", "choose", "look for", "look out for",
                            # "would you recommend an office chair" is the buying question, and
                            # the verb is the ask, so the thing still comes from the key.
                            "recommend", "recommended", "recommendation", "recommendations")),
          ("About £100 to £200 buys a decent one: adjustable height and armrests, a seat you can set "
           "to the right depth, and a five-year guarantee on the gas strut. Cheaper chairs lose "
           "their height and wobble within a year; a used Steelcase or Herman Miller for the same "
           "money is the better buy if you can sit in it first."),
          # a high chair is the baby's, not the desk's: "how much is a high chair" was answered with
          # the height adjustment and the gas strut, because the key is the bare word "chair"
          avoid=("high chair", "highchair", "high chairs", "baby", "babies", "child", "children",
                 "kid", "kids", "toddler", "booster", "nursery")),
    entry("frying-pan", (("frying pan", "pan", "wok"),
                         ("buy", "cost", "much", "price", "best", "good", "decent", "non-stick",
                          "nonstick", "replace", "choose", "look for", "look out for")),
          ("£25 to £40 buys a good non-stick one: a thick base, a metal handle you can finish in "
           "the oven, and no rivets inside where food catches. Cheap non-stick dies in a year or "
           "two, so either buy mid-price and expect to replace it, or spend a bit more on carbon "
           "steel and season it."),
          # A pan to clean is not a pan to buy: the bare "pan" in the key above met "what is the
          # best way to clean a burnt pan" through "best" and "pan" and answered it with £25 to
          # £40 buys a thick base. The burnt pan's own rows hold the bicarbonate answer, so this
          # one stands down for anything that says the pan is burnt or stuck. It is still the
          # buying answer for "what is the best pan to buy" and "which frying pan should i buy".
          avoid=("burnt", "burned", "burnt on", "burnt bits", "burned bits",
                 "clean a pan", "clean the pan", "clean my pan", "clean a frying pan",
                 "clean the frying pan", "scour", "scrub", "burnt food",
                 "stuck to the bottom", "stuck on the bottom", "bottom of the pan")),
    entry("mattress-buy", ("mattress", ("buy", "buying", "choose", "choosing", "firm", "soft",
                                        "best", "good", "replace", "cost", "much", "price",
                                        "decent", "spend", "which", "need", "look for",
                                        "look out for", "pick", "picking", "back",
                                        # "what mattress should i get" is the commonest way
                                        # the question is typed, and neither "get" nor
                                        # "should" was in the ask, so it was a hedge beside a
                                        # row that answers "do i need a new mattress"
                                        "get", "getting", "should",
                                        # a budget is the commonest way to ask the question:
                                        # "is a cheap mattress ok" has no other buying word in it
                                        "cheap", "cheaper", "budget")),
          ("Spend your budget on support, not springs: a medium-firm pocket-sprung or foam mattress "
           "suits most people, and you should lie on it for 15 minutes in the shop. Buy somewhere "
           "with a 100-night trial, and replace it every 8 to 10 years."),
          # cleaning.py's mattress-clean carries bias=1 and ties on "how much should a decent
          # mattress cost" ("how" vs "cost"), so a buying line came back with a stain answer. The
          # avoid is the other half: "best way to clean a mattress" names a cleaning word and is
          # theirs, whatever "best" scores here.
          # turning one over is home.py's `mattress-flip`, not a purchase: "do i need to turn
          # my mattress over" names "need", which is a buying word here, and a turning question
          # is not a buying one
          avoid=("clean", "cleaning", "stain", "stains", "smell", "smells", "wash", "washing",
                 "vacuum", "wet", "accident", "bedbugs", "bed bugs",
                 "turn", "turning", "turned", "flip", "flipping", "flipped", "rotate",
                 "rotating", "rotation", "head to foot", "two sided", "sag", "sagging",
                 "saggy", "dip", "dips", "lumpy", "worn out",
                 # "back" is a buying word here (support for a bad back), and it is also how a
                 # person reports their own: "i carried a mattress up two flights and my back is
                 # sore" was told to spend its budget on support rather than springs. Only the
                 # carrying itself stands this row down - "my back is stiff every morning, should
                 # i get a new mattress" is exactly the buying question, and a fence of "my back
                 # is" took it off this card.
                 "carried", "carrying", "lifted", "lifting", "hauled", "dragged", "shifted",
                 "sack truck", "up the stairs", "up two flights",
                 # a topper is its own row with its own answer, and "should i get a mattress
                 # topper" now reaches this ask through "get" and "should"
                 "topper", "toppers", "mattress topper", "mattress toppers", "protector",
                 "mattress protector"),
          bias=2),
    entry("washing-machine", ("washing machine", ("buy", "choose", "choosing", "best", "good",
                                                 "need", "size", "look for", "look out for",
                                                 "recommend", "which washing machine",
                                                 "what washing machine")),
          ("Get an 8kg drum for a family, a 1,400 spin speed and the best energy rating you can "
           "afford: the running cost over ten years beats the purchase price difference. Measure "
           "the gap and the door before you order, and check the warranty length."),
          # "need" and "washing machine" are also what a broken machine's owner types: "i need my
          # washing machine fixed, it won't drain" was getting the buying guide. A machine that
          # leaks, drains or will not spin is home.py's question, so those words pass here.
          avoid=("leak", "leaks", "leaking", "leaked", "drain", "drains", "draining", "drained",
                 "spin", "spins", "spinning", "broken", "broke", "fix", "fixed", "fixing",
                 "repair", "repairs", "not working", "stopped working", "wont start",
                 "won't start", "noise", "noisy", "banging", "stuck", "error", "smell", "smells")),
    entry("furniture-second-hand", (("sofa", "furniture", "table", "wardrobe"),
                                    ("second hand", "used", "buy", "check", "charity")),
          ("Second-hand furniture is the best value there is, and charity shops and Freecycle are "
           "the places to look. Check for woodworm holes, sagging cushions and smoke smell, and "
           "measure your door and stairs before you collect anything big."),
          # "buy" is the borrowing word here, and it is in every shopping line: a washing powder
          # is not a sofa, and this row answered "is it cheaper to buy washing powder in bulk"
          # with second-hand furniture when the talk had moved on from a cat
          avoid=("washing", "laundry", "detergent", "powder", "washing powder", "soap", "bleach",
                 "cleaner", "cleaners", "nappies", "toilet roll", "loo roll", "kitchen roll",
                 "coffee", "tea bags", "cereal", "tins", "pet food", "food", "drink", "sauce")),
    entry("is-the-deal-real", (("sale", "deal", "deals", "discount", "offer", "offers",
                               "bargain", "price drop", "price cuts", "reduced"),
                               # "really", "legit" and "check" are the words people put round a
                               # price they are suspicious of, and none of them is "real":
                               # "how do i check if a deal is really a deal" reached nothing at
                               # all, which is the one answer a shopper cannot use.
                               ("real", "really", "worth", "genuine", "good", "actually",
                                "check", "too good")),
          ("Check the price history before believing a sale: CamelCamelCamel does it for Amazon and "
           "Keepa for many shops, and a \"was £200\" tag that was £200 for one week tells you "
           "nothing. Compare the unit price (per kg or per wash) rather than the pack price."),
          # a house or a flat is not a shop: "is it worth offering below asking price" was this
          # card's price-history answer, and the offer question has its own row in money.py
          avoid=("house", "houses", "flat", "property", "asking price", "estate agent",
                 "below asking", "under asking", "mortgage", "seller", "landlord")),
    # "how do I use reviews without getting fooled by fake ones" is an everyday shopping question:
    # a shop's star rating is not evidence, and the two- and three-star reviews are where the real
    # information is.
    entry("reviews-fake", (("review", "reviews", "rating", "ratings", "stars"),
                           ("fake", "fooled", "fool", "trust", "reliable", "believe", "real",
                            "genuine", "sponsored", "paid", "honest")),
          ("Read the two- and three-star reviews first: they say what actually goes wrong, while "
           "five-star ones are often written the day the thing arrived. Then check whether the "
           "reviews are spread over months or all landed in one week (a burst is bought), look for "
           "the line that says the purchase was verified, and search the product name with "
           "\"problem\" or \"broke\" to find the complaints. A brand-new product with hundreds of "
           "glowing reviews is the one to distrust most.")),
    # Writing a review of a shop, a restaurant or a thing you bought was answered by whatever else
    # in the line owned the word "review": "how do i leave a bad review" got the appraisal answer,
    # "how do i write a review online" got the card-safety one, and "where do i leave a review for
    # a restaurant" got the shrug. The keys here are all phrases, never the bare word, so a work
    # review ("how do i prepare for my review") is still the appraisal's line.
    entry("review-leave",
          (("leave a review", "leave reviews", "leaving a review", "write a review",
            "writing a review", "post a review", "leave a rating", "leave feedback",
            "leave a bad review", "write a bad review", "leave a negative review",
            "1 star review", "one star review", "edit a review", "change a review",
            "review i left", "review a product", "review a restaurant", "review a shop",
            "review a hotel", "review a company", "where to leave a review",
            # what makes one useful is the same question from the other end, and both were
            # a shrug: "how do i write a good review", "what makes a good review"
            "good review", "good reviews", "helpful review", "honest review",
            "useful review", "what makes a good review"),
           ("how", "should", "where", "can", "worth", "want", "going to", "do i",
            "what makes", "what counts as",
            "google", "amazon", "tripadvisor", "trustpilot", "yelp", "product",
            "restaurant", "shop", "hotel", "star", "online", "bad")),
          ("Leave it where people look, and where the business will see it: the order page for an "
           "online shop (that is the one the seller can answer), Google Maps for a cafe, shop or "
           "restaurant, TripAdvisor for a hotel. Three or four lines beat a rant - what you bought, "
           "when, what went wrong, and what you want - and give the stars you actually mean, since "
           "a 2 with a fair paragraph is read and a 1 with none is not. Post within a week or so "
           "while the details are checkable, keep the order number and any photos, and you can edit "
           "or delete your own review later from your account."),
          avoid=("reply", "replies", "reply to", "respond", "responding", "answer a",
                 "apologise", "apologize", "removed", "remove", "taken down", "delete",
                 "my app store", "subscription", "subscriptions", "chargeback",
                 "appraisal", "performance review", "my boss", "my manager", "at work",
                 # feedback to a person is the work row's question, not a review of a purchase:
                 # "how do i leave feedback for a colleague" was answered with where to post one,
                 # and the shop owner's own line ("a customer left a one star review") is the
                 # removal row's, not the customer's
                 "colleague", "colleagues", "coworker", "co-worker", "teammate", "team",
                 "staff", "employee", "employees", "the team", "my team", "presentation",
                 "customer", "customers", "my business", "my shop", "my restaurant")),
    # The other direction, and the one that used to get the appraisal answer too: the shop or the
    # person a review was left about asking for it to come down.
    entry("review-taken-down",
          (("review removed", "review taken down", "remove a review", "delete a review",
            "get a review removed", "get a bad review removed", "bad review removed",
            "bad review taken down", "bad review of my business", "review about my business",
            "negative review", "unfair review", "can i report a review", "report a review",
            # the shop or the site the review sits on is named in the line: "how do i get a bad
            # review of my shop taken down", "how do i get a review of my restaurant deleted",
            # "a customer left a one star review"
            "review of my shop", "review of my business", "review of my restaurant",
            "review of my company", "review of my cafe", "review of our shop",
            "a customer left", "review on my", "review for my", "one star review",
            "1 star review"),
           ("how", "can", "someone", "business", "shop", "restaurant", "customer",
            "customers", "left", "got", "google", "tripadvisor", "amazon", "report",
            "remove", "removed", "taken", "take down", "down", "delete", "deleted",
            "untrue", "lies", "defamatory", "slander", "my shop", "my business")),
          ("Only the platform can take a review down, and only when it breaks their rules: no proof "
           "of purchase, abuse, the wrong business, or a rant about something else. Open the review, "
           "use its report button and pick the rule it breaks, and keep a screenshot. If the platform "
           "says no, ask once more with the order number as proof of what really happened, and reply "
           "once in public with the fix - readers weigh that calm reply more than the complaint. Never "
           "offer a refund or a freebie for a good review or a deletion: that breaks the rules itself "
           "and can cost the listing its stars."),
          avoid=("how do i reply", "reply to a bad review", "respond to a review",
                 "apologise to a customer", "appraisal", "performance review", "my boss",
                 "my manager")),
    # "Where is the cheapest place to buy a fridge" was a plate of lentil chilli: `cheapest`
    # is one of the dinner-idea shapes and `fridge` one of its carriers, so the kitchen answered
    # a purchase question. Buying a thing is a shopping question about the same decision as
    # `is-the-deal-real`, so it is answered here and the kitchen passes on the buying words.
    # The second group is the thing being bought, and the bare verbs "buy" and "bought" cannot
    # be it: they are the words the ask above already holds, so any "where can i buy <anything>"
    # was the same as "where can i buy a fridge" and got the price-history lecture about a
    # "was £500" tag. "where can i buy a stamp", "where can i buy a birthday card" and "where
    # can i buy envelopes" were all answered with it, and each wanted a kind of shop. The row
    # still answers every line that names the thing, which is what the price advice is about.
    entry("where-to-buy-cheapest",
          (("cheapest", "cheapest place", "cheapest shop", "where to buy", "where can i buy",
            "where should i buy", "where do i buy", "best place to buy", "best price",
            "who sells", "where sells",
            # "where do i get a tumble dryer" and "where can i get a freezer" ask the same
            # question as "where can i buy": the verb "get" kept them out of the answer.
            "where do i get", "where can i get", "where to get", "where should i get"),
           # the things the price answer is written for: `lookup.PRICE_COMPARED` is the same
           # list the verdict rows test before they stand aside from a place question, so the
           # answer and the stand-aside cannot drift apart
           ("get one",) + PRICE_COMPARED),
          "Compare the exact model across two or three shops, and check its price history first: a "
          "\"was £500\" tag is often a week old. For appliances the cheapest safe route is usually "
          "refurbished or graded stock with a real warranty, or ex-display if you ask. Buy at the "
          "end of the season or when a new model lands, and pay by credit card over £100 for the "
          "extra protection.",
          # A where-line is this row's only when the thing is one it compares and the line is
          # not about a part of one: the verdict rows ask `lookup.asks_where_a_shop_answers` the
          # same question before they stand aside, so the stand-aside and this answer agree.
          guard=lambda understood: (not asks_where(understood)
                                    or asks_where_a_shop_answers(understood)),
          # food shopping is `bulk-buying`, and a machine that is broken is a repair question
          avoid=("groceries", "grocery", "weekly shop", "food shop", "supermarket", "milk",
                 "meat", "vegetables", "dinner", "meal", "meals", "recipe", "recipes",
                 "broken", "not working", "stopped working", "wont start", "won't start",
                 "repair", "repairs", "fix", "faulty", "leaking", "leaks", "error code",
                 # a thing with its own buyer's guide keeps it: "cheapest place to buy a laptop"
                 # wants the RAM, not a lecture on price comparison
                 "sofa", "furniture", "table", "wardrobe", "laptop", "phone", "iphone",
                 "android", "tablet", "mattress", "washing machine", "washer dryer",
                 "running shoes", "trainers", "coat", "jacket", "office chair", "frying pan",
                 "bike",
                 # and the ones main already has a real answer for, even when it is not a
                 # buyer's guide: "where to buy a used car" wants the MOT history, "where to buy
                 # a printer" the mono-laser-for-a-hundred answer. Told to me by good-jaguar.
                 # not bare "car": "where can i buy a car seat" is a pram-shaped line and the
                 # buying answer is right for it. The used-car lines name a car to buy.
                 "used car", "secondhand car", "second hand car", "new car", "cheap car",
                 "car for sale", "printer",
                 # A pram is a place question with its own buying answer, and it is second-hand:
                 # the key above lists "pram" as a thing whose price to compare, which is the
                 # wrong advice for it. The word alone took the row, so the baby kit's stand-down
                 # is here: "where can i buy a pram" is the second-hand row's line.
                 "pram", "prams", "contact lenses", "contact lens", "glasses frames",
                 # What the guides above have in common is a real answer of their own. The
                 # dishwasher, the kettle and the air fryer had only a verdict on owning one
                 # ("a dishwasher is worth it for three or more people"), which is not a place,
                 # so a where-question with one of them in it was told the verdict and this row
                 # stepped aside. A model is still the other question: "which dishwasher is the
                 # cheapest to run" wants the running cost, not a shop.
                 "which", "to run", "running cost", "cost to run", "per year", "a year",
                 "energy", "electricity", "water use", "uses", "efficient",
                 # a descaler is bought to clean a kettle, and its own rows say how to use it
                 "descaler", "descale", "descaling", "limescale",
                 # The answer is about comparing a model, a price history and a warranty, so a
                 # living thing or an edible has no business here: "where can i buy cheap plants"
                 # was a florist answer and "where to buy a christmas tree" a hedge. Told to me
                 # by sleek-yarn.
                 "plant", "plants", "flower", "flowers", "tree", "trees", "seed", "seeds",
                 "bulbs", "shrub", "bush", "houseplant", "hanging basket", "compost",
                 "chicken", "chickens", "fish", "eggs", "fruit", "veg", "vegetables")),
    # "where can i buy a stamp" got the price-comparison lecture, which is written for a model,
    # a warranty and a "was £500" tag; "where can i buy a birthday card" got it too, and the
    # enveloped one went to the row about addressing an envelope. Each of these is a where
    # question with a short answer, and the answer is a kind of shop rather than a price, so one
    # row reads one table. The ask is the key and the table decides, so a "where can i buy" line
    # that names something not in it passes to the row that knows better (the fridge keeps the
    # price answer, the pram keeps the second-hand one).
    entry("where-to-buy-everyday",
          (("where can i buy", "where do i buy", "where to buy", "where can i get",
            "where do i get", "where can i find", "where do i find", "best place to buy",
            "best place to get", "who sells", "where sells"),
           _THE_EVERYDAY_THINGS),
          _everyday_where,
          # A fuse in a boiler is the engineer's, and a colour code is a question about paint that
          # is already on the wall.
          avoid=("boiler", "boilers", "consumer unit", "fuse box", "fuse board", "trip switch",
                 "rcd", "colour code", "color code", "paint code", "code for the paint")),
    # "how do i haggle in a shop" was an honest pass, and so were haggling tips, bargaining at a
    # market, asking for a better price and asking a tradesman for a lower one: no entry claimed
    # the price conversation at all. The question words are the second group, so the three-word
    # lines reach it ("how do i haggle"), and the thing words are there too, so a quote or a sofa
    # is enough to pair with them.
    entry("haggle-price",
          (("haggle", "haggling", "haggled", "bargain", "bargaining", "bargained", "negotiate",
            "negotiating", "negotiation", "talk them down", "money off", "discount", "discounts",
            "lower price", "better price", "cheaper price", "best price", "price down"),
           ("how", "is", "it", "can i", "should i", "do i", "is it", "you", "my", "what", "tips",
            "rude", "worth",
            "price", "prices", "shop", "shops", "market", "car boot", "boot sale", "sofa",
            "mattress", "builder", "builders", "plumber", "tradesman", "tradesmen", "quote",
            "quotes", "deal", "cheaper", "down", "washing machine", "fridge", "car")),
          _haggle,
          # a used car from a dealer is the car-buying answer, which checks the car first; a
          # bargain that is not real is the deal entry; and a discount code online is neither
          # The second group has question words in it ("how", "is", "my", "what"), which is what
          # makes "how do i haggle" and "when should i book a hotel" reach these rows at all, so
          # the lines that only share a word with a price come out here instead: a council tax
          # bill, an energy bill and a train ticket are fixed prices with a complaint route, not
          # a stall; selling something is the selling answer; and "is this a bargain" asks for a
          # judgement on a deal rather than a way to push a price.
          avoid=("used car", "second hand car", "dealership", "test drive", "mileage", "car dealer",
                 "real bargain", "actually a bargain", "good bargain", "is it worth", "worth it",
                 "voucher", "vouchers", "promo code", "discount code", "coupon", "coupons",
                 "student discount", "loyalty", "clubcard", "nectar", "cashback",
                 "what is a bargain", "whats a bargain", "is this a bargain", "is that a bargain",
                 "a real bargain", "such a bargain", "bargain hunter",
                 "council tax", "energy", "bill", "bills", "gas", "electric", "electricity",
                 "water bill", "train", "trains", "rail", "railcard", "bus", "buses", "flight",
                 "flights", "house", "houses", "mortgage", "offer on a house", "estate agent",
                 "sell", "sells", "selling", "sold", "ebay", "vinted", "gumtree", "insurance",
                 # "negotiate" in the key with "how"/"my" in the question group is two matching
                 # words on any salary line, so a pay rise was told to ask once, cheerfully,
                 # because shops have room on sofas. A salary is negotiated with evidence and a
                 # meeting, and work.py owns it.
                 "salary", "salaries", "pay rise", "payrise", "raise", "wages", "wage",
                 "job offer", "new job", "promotion", "appraisal", "interview",
                 # "how do i negotiate a flexible working request" was told to ask once,
                 # cheerfully - the word "negotiate" plus "how" is all this row needs. Hours and
                 # a boss belong to work.py.
                 "flexible", "flexible working", "flexible hours", "hours", "boss", "manager",
                 "employer", "employers", "employee", "work from home", "wfh", "part time",
                 "full time", "shift", "shifts", "rota", "annual leave", "holiday entitlement",
                 "redundancy", "union", "colleague", "colleagues", "hr",
                 # a rent rise and a tenancy are negotiations, but with a landlord and a notice
                 # period, not a stall: "can i negotiate my rent" was told to ask once, warmly,
                 # and have somewhere cheaper to point at.
                 "rent", "rents", "rent increase", "rent rise", "landlord", "landlords",
                 "tenancy", "tenancies", "lease", "deposit", "section 13",
                 # a mobile or broadband contract is a haggle in name only: the answer is a
                 # refurbished handset and a SIM-only deal, which technology.py owns, and
                 # "how do i negotiate a mobile contract" was getting the sofa-and-mattress card.
                 "mobile", "phone", "phones", "handset", "sim", "sim only", "tariff",
                 "contract", "contracts", "broadband", "tv licence", "gym", "gym membership",
                 "insurance quote",
                 # a new car is the car-buying answer too, which has its own move - talk to the
                 # salesperson, go at the end of the month, bring a rival quote - and main gives
                 # it. "new car" and "buy a car" rather than a bare "car", which would take
                 # "can you haggle at a car boot sale", a line this row should answer
                 # (steward-free-daisy, #3394)
                 "new car", "new cars", "brand new car", "buy a car", "buying a car",
                 "car finance"),
          # "money off" is a discount on a thing; "money off my mum" is a loan from a person. The
          # rule is `lookup.a_price_not_a_loan`, so every price row gets it from one place.
          guard=a_price_not_a_loan),
    # "is aldi cheaper than tesco" and "which supermarket is cheapest" were a search hedge or a
    # shrug: the order of the shops is a fact, so it is a table of shops kept as data and one
    # entry reads the names out of the line. No live prices - the answer says where each sits and
    # what to compare, which is what a person is asking.
    entry("supermarket-cheapest",
          (("aldi", "lidl", "asda", "tesco", "sainsburys", "sainsbury's", "morrisons", "waitrose",
            "marks and spencer", "marks and spencers", "m and s", "m s", "ms", "marks & spencer",
            "co-op", "co op", "coop", "iceland", "farmfoods",
            "ocado",
            "supermarket", "supermarkets", "groceries", "weekly shop"),
           ("cheaper", "cheapest", "expensive", "compare", "comparison", "best value",
            "better value", "which is", "worth switching", "switch", "price", "prices",
            "value for money", "or",
            # "should i shop at lidl or tesco" and "is waitrose worth it" name a shop and no price
            # word, and a bare "or" is a stop word by the time a row reads the line, so the ask has
            # to be spelled out: shopping at, worth it, as good, quality
            "shop at", "shopping at", "worth it", "worth shopping", "as good", "good quality",
            "quality", "which shop", "which one",
            # a question about how good a shop is asks with these, and the row never reached
            # "is aldi good" or "is waitrose better than tesco" without them in the second part
            "good", "better", "worse", "fresh", "fresher", "taste", "tasty", "nicer",
            "worth", "worth the money",
            # the choosing words are part of the question, not decoration: "help me decide
            # between aldi and tesco" names two shops and got one position of the key, which
            # score() reads as a line that only passes by ("should i shop at aldi or tesco" is
            # the same shape and the same fix)
            "decide", "deciding", "choose", "choosing", "pick", "between", "should i",
            "shall i", "should we", "shop at", "shopping at")),
          _supermarket_cheapest,
          # the ask is what makes the line a comparison, and a row with an ask word missing never
          # reaches the line at all: "is waitrose better than tesco" and "is aldi fresher than
          # tesco" scored nothing until "better" and "fresher" were here, and "should i shop at
          # lidl or tesco" nothing until the bare "or" was
          # "should i shop at lidl or tesco" is the commonest way this is asked and it reached
          # nothing: "shop at" is spent on the key, a bare "or" is a stop word, so the ask was
          # empty and score() returned 0. The asking words below are the ones a comparison is
          # put in: should i, shall i, help me decide.
          ask=("cheaper", "cheapest", "expensive", "compare", "comparison", "best value",
               "better value", "better", "worse", "as good", "fresh", "fresher", "which",
               "which is", "which shop", "which one", "worth", "worth it", "switch",
               "prices", "price", "value", "quality", "good", "shop at", "shopping at", "or",
               "vs", "versus", "instead of",
               "should i", "shall i", "should we", "should", "decide", "deciding", "choose",
               "choosing", "pick", "help me"),
          # the weekly-shop money answer is a meal plan, and a complaint about a shop is the
          # refund row's: neither is a question about which shop is cheaper
          # the shop name in the line may be the place people travel to, so the trip lines are
          # not this row's: `_the_place_not_the_shop` reads them off
          guard=_the_place_not_the_shop,
          avoid=("meal plan", "meal planning", "meal prep", "what should i cook", "recipes",
                 "food waste", "waste food", "refund", "refunds", "complaint", "complain",
                 "delivery", "deliveroo", "just eat", "substitute", "out of stock",
                 "parking", "opening hours", "open today", "nearest",
                 # a loyalty card is not a basket, fuel is not groceries, and a free-from range
                 # is its own question: "is it worth getting a tesco clubcard", "is tesco petrol
                 # cheaper" and "is aldi good for gluten free" were all told where the shop sits
                 # on price
                 "clubcard", "club card", "loyalty", "loyalty card", "nectar", "reward points",
                 "petrol", "fuel", "diesel", "gluten", "free from", "free-from", "vegan",
                 "vegetarian", "coeliac", "celiac", "dairy free", "nut free", "allergy",
                 "organic", "halal", "kosher", "any good for", "good for", "fine for", "ok for",
                 "okay for", "meal deal",
                 # a person's own basket is a money question with their numbers in it, not a
                 # ranking: deck row `spry-16` lost "would a weekly shop be cheaper" and the turn
                 # after it to this row, and a statement is not a comparison at all
                 # the shape that asks about their own basket is "would a weekly shop be
                 # cheaper", not the word "shop": "so where should i do the big shop" is a where
                 # question and the ranking answers it
                 "my weekly shop", "would a weekly shop", "is a weekly shop cheaper",
                 "cheaper to do a weekly shop", "my shopping", "i do my shopping",
                 "too expensive", "my basket",
                 # "i shop at aldi" is a statement, but "should i shop at aldi" is the commonest
                 # way this question is asked and it contains the same three words, so the fence
                 # cannot live here: _supermarket_cheapest reads the ask in front of it instead.
                 "shop at the", "shopping at the", "i always shop", "i only shop")
                 # and the same name sells phones, broadband and mortgages, which is not the
                 # basket at all: "is tesco mobile any good" was answered with the grocery price
                 + _SERVICE_WORDS),
    entry("bulk-buying", (("supermarket", "shopping", "groceries"),
                          ("cheaper", "save", "save money", "bulk", "value", "budget")),
          ("Compare the price per 100g on the shelf label, not the pack size: bigger packs are "
           "often, but not always, cheaper. Own-brand staples (rice, pasta, tinned tomatoes, oats) "
           "are usually the same product, and the savings there pay for the things you care about.")),

    # --- gifts -------------------------------------------------------------------
    entry("gift-dad-fishing", (("fishing", "fish", "tackle", "angling"),
                               ("dad", "father", "grandad", "stepdad", "gift", "present")),
          about_them("{they} {has} told you what {they} {likes}, so buy into it: a decent "
                      "tackle box, or a float and hook kit if {they} {is} starting out, fits any "
                      "budget and gets used. Add one small thing {they} wouldn't buy {self} - a "
                      "box set of the old films {they} {loves}, a decent flask - and a card that "
                      "says why. One thing {they} will actually use beats three safe ones."),
          avoid=LOSS + CRISIS, bias=2, ask=GIFT_ASK),
    # The second part of a gift entry is the ask, never a bare verb and never an occasion word.
    # "get" and "buy" are in half the lines that are about nothing of the sort - "my dad cant get
    # out of bed", "my mum cant get up the stairs", "my dad is coming for christmas" - and the
    # entries above need a hobby word beside the ask, so this one has to hold its own: a gift noun
    # or a gift-shaped frame, exactly as GIFT_ASK reads, but phrases here so that the bare verb
    # cannot carry the entry on its own.
    entry("gift-dad", (("dad", "father", "grandad", "stepdad"),
                       ("gift", "gifts", "present", "presents", "60th", "70th",
                        "what to get", "what to buy", "what should i get", "what should i buy",
                        "what can i get", "what can i buy", "what do i get", "what do i buy",
                        "gift ideas", "present ideas", "christmas ideas", "birthday ideas",
                        "ideas for a gift", "ideas for a present",
                        "christmas present", "christmas gift", "fathers day", "father's day",
                        "get him", "get her", "buy him", "buy her",
                        # "what should i give my dad for his birthday" is answered off the
                        # occasion word: a bare "give" here also fits "how do i give my dad his
                        # medicine", which is not a present
                        "what to give", "what should i give", "what can i give")),
          _present_answer(
           "Go consumable and a notch better than he'd buy himself: good coffee, a decent bottle "
           "of what he already drinks, or a voucher for something he already does at the weekend. "
           "If he insists he wants nothing, replace one small thing he has been putting off - a "
           "wallet, a torch, a decent belt - and add a card that says why. One thoughtful thing "
           "beats three safe ones."),
          # a speech is a toast, not a present: "i have to give a speech at my dads 70th" is not
          # a gift question, and the gift entry was outscoring write-a-toast on the round number
          # a speech is a toast, not a present: "i have to give a speech at my dads 70th" is not
          # a gift question, and the gift entry was outscoring write-a-toast on the round number.
          # The words inside a card are not a present either: "message for my dads fathers day
          # card" is a wording job.
          avoid=LOSS + CRISIS + ("speech", "toast", "best man", "maid of honour", "few words",
                                 "card", "cards", "message", "messages", "write", "writing",
                                 "what do i say", "what to write", "what do i write"),
          bias=1),
    entry("gift-mum-garden", (("garden", "gardening", "plants", "allotment", "garden centre"),
                              ("mum", "mother", "nan", "grandma", "gift", "present")),
          about_them("{they} {has} told you what {they} {likes}, so buy into it: good gloves "
                      "that fit properly, a decent trowel, a bag of good compost, or a voucher "
                      "for the nearest garden centre. Add one small thing {they} would not buy "
                      "{self} and a card that says why."),
          avoid=LOSS + CRISIS, bias=2, ask=GIFT_ASK),
    entry("gift-mum", (("mum", "mother", "nan", "grandma"),
                       ("gift", "gifts", "present", "presents", "mother's day", "mothers day",
                        "what to get", "what to buy", "what should i get", "what should i buy",
                        "what can i get", "what can i buy", "what do i get", "what do i buy",
                        "gift ideas", "present ideas", "christmas ideas", "birthday ideas",
                        "ideas for a gift", "ideas for a present",
                        "christmas present", "christmas gift",
                        "get her", "get him", "buy her", "buy him",
                        "what to give", "what should i give", "what can i give")),
          _present_answer(
           "Make something she uses every week a bit nicer: a proper thermos, a voucher for the "
           "place she likes, a photo book of the family, or a little of something she loves to "
           "eat. Experience gifts work well for someone who already has everything."),
          avoid=LOSS + CRISIS),
    # "present for someone with a nut allergy" names nobody the other rows know: `someone` is out
    # of `gift-her` because "should i get someone in" is a plumber, so the ask itself is the row,
    # and `_gift_anyone` asks the reading first, which is what keeps the plumber out.
    entry("gift-someone", ("present for someone", "present for somebody", "gift for someone",
                           "gift for somebody", "presents for someone", "gifts for someone",
                           "present for anyone", "gift for anyone", "get someone something",
                           "get somebody something"),
          _gift_anyone, avoid=LOSS + CRISIS),
    # A present for someone who is leaving or retiring names a person no other gift row knows, so
    # the line went to the row whose key happened to fit: "what is a good present for a teacher who
    # retires" was answered with the pot to aim for at retirement, because "what is" is in that
    # row's key and "retires" in its first part. The occasion is one question and the gift is
    # another, so this row owns the pair, and the specific rows (a mum, a dad, someone ill) still
    # win when the person in the line is theirs.
    entry("gift-leaving-work",
          (("retiring", "retires", "retired", "retirement", "leaving present", "leaving do",
            "leaving work", "leaves work", "last day at work"),
           ("present", "presents", "gift", "gifts", "gift ideas", "present ideas",
            "what to get", "what to give", "what to buy", "what do i get", "what do i give",
            "what do i buy", "what should i get", "what should i give", "what should i buy",
            "what can i get", "what can i give", "what can i buy", "what is a good present",
            "what is a good gift", "get them", "get her", "get him", "buy them", "give them")),
          # A leaving present is about the change rather than the job, so this is not the general
          # list: what they now have time for, one good thing from the team, and the card with a
          # real line from everybody, which is the part people keep.
          _present_answer(
           "A leaving present is about what comes next rather than the job: something for the "
           "thing they will now have time for - a book, a course, a voucher for the garden centre "
           "or the cinema, a decent bottle for the first Friday. If the team is chipping in, "
           "\u00a310 to \u00a315 each buys one good thing, which beats five fillers, and the card "
           "everyone signs with one real memory each is the part people keep. Ask first whether "
           "they want a fuss at all: some people would rather have a pint after work."),
          avoid=LOSS + CRISIS + (
              # a present for a mum, a dad or a partner is their own row's answer, and this one
              # would only repeat the general list over the top of it
              "mum", "mother", "dad", "father", "nan", "grandma", "grandad", "granny",
              "sister", "brother", "aunt", "uncle", "wife", "husband", "partner",
              "son", "daughter", "baby", "child",
              "speech", "toast", "few words", "card", "cards", "message",
              "what do i say", "what to write", "what do i write"),
          bias=1),
    entry("gift-hospital", (("hospital", "ward", "in hospital", "hospital bed", "hospice",
                             "in a hospice", "hospice bed",
                             "having an operation", "operation", "surgery", "recovering",
                             "in recovery"),
                             # A gift needs a gift-shaped ask. The bare verbs claimed "i got a
                             # hospital parking ticket" and "can i take my mum to hospital".
                             ("gift", "present", "presents", "idea", "ideas",
                              "what to get", "what should i get", "what can i get",
                              "what do i get", "what to buy", "what should i buy",
                              "what can i buy", "what do i buy", "what to bring",
                              "what should i bring", "what can i bring", "what do i bring",
                              "what to take", "what should i take", "what can i take",
                              "what do i take", "what do you buy", "what would you buy",
                              "what do you get", "what would you get",
                              "what do you bring", "what would you bring",
                              "what do you take", "what would you take",
                              "what should i get them", "what can i get them",
                              "flowers", "ok to bring", "is it ok to bring",
                              "get her", "get him", "get them",
                              "get my mum", "get my dad", "get my nan",
                              "buy her", "buy him", "buy them",
                              "bring her", "bring him", "bring them",
                              "take her", "take him", "take them",
                              "visit", "visit her", "visit him",
                              "see her", "see him", "cheer", "cheer her", "cheer him")),
          ("Small things they can use lying in bed: a long phone cable and a charged power bank, "
           "earphones, a puzzle book or a magazine, a decent lip balm, a light blanket, or a "
           "printed photo of the family to put on the locker. Skip flowers on most wards and skip "
           "food unless you know the diet. Ask the ward what is allowed before you bring it in, "
           "and go when you can stay a while - the visit is the gift."),
          # a bare "visit" in the key claims "visiting hours at the hospital", which is a
          # question about the time, and family.hospital-visiting-hours answers it
          avoid=("visiting hours", "visiting times", "visiting time", "when can i visit",
                 "what time can i visit", "when can we visit", "when can you visit",
                 "what time can you visit", "can i visit", "can we visit", "is it ok to visit",
                 "ok to visit", "should i visit", "let visitors in", "visitors allowed",
                 "visitors in"),
          bias=2),
    # A present for somebody who is ill at home was the one gift nobody answered: "what can i
    # give someone who is ill" was a search hedge, and "what can i bring someone with flu" was
    # the wedding plus-one. It is not the hospital answer - the ward rules, the flowers and the
    # food are a different set - so this row stands down for a ward and takes the days in bed.
    entry("gift-someone-ill",
          (("ill", "sick", "poorly", "unwell", "flu", "a cold", "chest infection", "virus",
            "lurgy", "man flu", "recovering", "getting over", "in bed", "off work ill",
            "was in hospital", "out of hospital", "had an operation", "after an operation"),
           PERSON_ASK + ("cheer her up", "cheer him up", "cheer them up", "cheer up",
                         "take round", "bring round", "something to take round",
                         "what can i bring", "what to bring", "what do i bring",
                         "what can i take round", "anything i can", "anything we can")),
          ("Something that makes a day in bed easier: a flask of soup with bread, a box of their "
           "favourite tea, a magazine or puzzle book, and a link to a film you know they like. "
           "Offer one specific thing at one specific time - \"I'll leave soup on the step on "
           "Thursday\" - because \"let me know if you need anything\" is the thing a poorly "
           "person never does. Skip flowers and skip food you do not know they can face."),
          # A medicine question names the illness and asks in the same shape ("what can i give
          # my son for a fever"), and a dose is the pharmacist's, not a present.
          avoid=(
                 # The row takes "anything i can" as a present ask, and that also reads a remedy
                 # question: "anything i can do about a cold" and "anything i can do about the
                 # flu" were told what to put in a flask and take round. Nothing anybody brings
                 # is the answer to "what can i do about <an illness>", so that shape stands the
                 # row down and the illness keeps its own answer.
                 "do about", "anything i can do", "what can i do",
                 "dose", "doses", "medicine", "medication", "paracetamol", "ibuprofen", "calpol",
                 "syrup", "painkiller", "painkillers", "how much", "how many", "fever",
                 "temperature", "rash", "vomiting", "diarrhoea", "cough", "coughs", "sore throat",
                 "is it normal", "see a doctor", "how long", "hospital", "ward", "a and e",
                 "999", "111", "symptom", "symptoms",
                 # "give" plus a symptom is the medicine question, and it is a parent's most of
                 # all: "my son is unwell what can i give him" was the child-illness card on main
                 # and the sick-day present here. A present is asked for by the person, not by
                 # the illness, so a line that names what to give *for* stands down.
                 "for a fever", "for a cough", "for the cough", "for a temperature",
                 "for the pain", "for a cold", "for flu", "for the flu", "for a sore throat",
                 "for a headache", "for sickness", "my son", "my daughter", "my child",
                 "my baby", "my kid", "my kids", "my toddler", "my boy", "my girl",
                 # "what can i bring someone with flu" is a present, so the fence is the person
                 # who has it ("he has the flu"), not the phrase "with flu" on its own.
                 "has the flu", "had the flu", "has flu", "is in bed ill") + LOSS + CRISIS,
          bias=1),
    entry("gift-person", (("sister", "brother", "friend", "friends", "mate", "cousin", "aunt",
                           "uncle", "colleague", "coworker", "boss", "manager", "neighbour",
                           # "what can i get my wife for her birthday" named nobody the present
                           # rows knew: `gift-her` reads "her" as the person, and here "her" is
                           # only the birthday's, so the line fell through to a party card.
                           "wife", "husband", "partner",
                           # A son or a daughter with no age in the line is still a person to
                           # buy for, and so are the children a present is bought for by name:
                           # "what should i get my nephew" matched no row at all while the store
                           # may already know the age. "them" is how the same ask is written when
                           # the chat has just said who they are.
                           "son", "daughter", "child", "children", "kid", "kids", "niece",
                           "nephew", "grandson", "granddaughter", "grandchild", "grandchildren",
                           "godson", "goddaughter", "godchild", "stepson", "stepdaughter",
                           "neighbor", "teacher", "carer", "nurse", "stepmum", "stepdad", "them"),
                          ("gift", "present", "get", "got", "buy", "birthday", "christmas",
                           "30th", "40th", "50th", "idea", "ideas")),
          _the_person_row("Pick something they would use every week and would not buy "
                          "themselves: good "
                    "coffee and a proper mug, woolly socks, a decent notebook, or a voucher for "
                    "the thing they always say they will do. If you know what they are into, buy "
                    "into it - a good knife for someone who cooks, a head torch for a runner, "
                    "secateurs for a gardener - and put a real message in the card, which does "
                    "half the work.",
                    CHILD_PRESENT),
          avoid=LOSS + CRISIS, bias=2, ask=PERSON_ASK),
    entry("gift-child-age", (("year old", "years old", "year-old", "yr old", "yrs old",
                              "month old", "months old", "aged", "toddler",
                              "preschool", "school age",
                              # a teenager with no age in the line is still a year band, and the
                              # row that reads the age is the one that knows what to do with it
                              "teenager", "teenagers", "teen", "teens", "teenage")
                             # the person a present is for says whose age it is, and every shape
                             # of "hes 4" - "my lad, hes 4 yr old", "my niece, shes 6", "my son
                             # for his 5th birthday" - was reaching the grown-up list, which
                             # offers a four-year-old good coffee and woolly socks
                             + CHILD_PEOPLE,
                             ("gift", "present", "get", "got", "buy", "birthday", "christmas",
                              "1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th",
                              "10th", "11th", "12th", "idea", "ideas")),
          _the_age_row,
          # the row names an age, which is the shape the age pools are chosen by: the age decides
          # the pool, and the pools already have the grown-up one past nineteen. There is no
          # guard on the age shape - a guard that asked again whether the age is a child's made
          # the row refuse the line it had just answered, and the follow-up after it was read
          # against the wrong entry.
          shape=(_names_a_childs_age,),
          # a row that names both the person and the age says more than the person row does, so
          # it is the one to answer where both fit.
          # no guard on the age shape: the memory keeps the answering row's keys, so the turn
          # after this one ("he likes lego and football", "budget is about 40") arrives here
          # too, and a guard that asked again for an age made this row refuse it and sent the
          # follow-up to a neighbour - the adult-sport card on "football", the budget bands on
          # "40". A cheap present is the tenner row's question, and that row reads the age
          # itself, so the budget words stand this row down instead.
          # ("budget" is not one of them: the turn after a present often answers with a budget,
          # and that turn is still this row's to take - the ack the person got on main.)
          # Money asked for as the present is the voucher row's question, and the answer to it
          # is the same sentence this row already gave for a teenager: taking the turn again
          # repeats it ("Everything about money is in what I said above"), where the voucher
          # row has the reason a card is not a cop out.
          avoid=LOSS + CRISIS + ("cheap", "cheaper", "cheapest", "inexpensive",
                                 "tenner", "fiver", "stocking", "small", "money", "cash",
                                 "voucher"),
          guard=_this_row_answers_the_line,
          bias=3, ask=AGE_ASK),
    # A present for a new baby is the one gift question nothing answered: "what should i get for a
    # new baby" was reaching the newborn-care lines ("your health visitor will talk it through")
    # and "gift for a new baby" the grown-up gift advice, which tells you to buy good coffee.
    entry("gift-new-baby",
          (("new baby", "newborn", "new born", "baby shower", "new arrival", "baby that has",
            "friend had a baby", "given birth", "just had a baby",
            # whose baby it is decides whether there is a present in the line at all: "my mate
            # had a baby what do i buy" was reaching the grown-up gift advice about coffee and a
            # mug, and "im going to see a newborn next week" the packing-for-a-week list. These
            # name somebody else having the baby, which is the only way a person ends up buying
            # something for one.
            "had a baby", "had her baby", "had the baby", "mate had a baby",
            "sister had a baby", "brother had a baby", "wife had a baby",
            "wifes had a baby", "wife has had a baby", "partner had a baby",
            "daughter had a baby", "son had a baby", "colleague had a baby",
            "coworker had a baby", "neighbour had a baby", "neighbor had a baby",
            "she had a baby", "they had a baby", "someone had a baby"),
           # the buying shapes are left out on purpose: "what do you buy a newborn" is the
           # parent's essentials list (baby-plan has the car seat and the cot), not a present
           ("gift", "gifts", "present", "presents", "what should i get", "what do i get",
            "what can i get", "what to get", "what do you get", "take to", "take round", "bring",
            # "what should i send", "what to take" and "get her something" are the same ask in
            # the verbs people actually use for a present they are not handing over themselves
            "what should i send", "what to send", "what do i send", "what do i bring",
            "what should i bring", "what to bring", "what should i take", "what to take",
            "what do i take", "what can i take", "get her something", "get him something",
            "get them something", "something for the baby", "something for her",
            "something for him",
            "idea", "ideas")),
          ("Buy the boring things that get used up: clothes in the three to six month size, a "
           "pack of muslins, a board book, or a voucher for a meal they do not have to cook. Skip "
           "newborn sizes (everyone buys them and the baby outgrows them in a fortnight), skip "
           "toys (a baby cannot hold one) and skip anything big, since they have no room. Offer "
           "to hold the baby while they sleep: that is the thing they actually want."),
          # the newborn-care lines name a baby and say get ("how do i get a new baby to sleep"),
          # and a care question is not a present
          avoid=("health visitor", "fever", "temperature", "feeding", "feed", "sleep", "jaundice",
                 "rash", "crying", "will not stop", "wont stop", "weaning", "milk", "nappy",
                 "nappies", "cord", "weight", "is it normal", "how do i", "what if",
                 # a present is the answer for the shower; the FOOD for it is the kitchen's,
                 # and "baby shower food ideas" was answered with the muslins list. Only the
                 # food ask stands this row down, so "what do you get for a baby shower" keeps
                 # the present it had
                 "shower food", "food ideas", "food for a shower", "food for the shower"),
          bias=2),
    # A present for a pet is the one gift question nothing answered, and it is asked every
    # December: "what should i get my cat for christmas" was answered "Keep the new cat in one room
    # with a litter tray and water", "what do i buy my puppy for his first christmas" with the
    # puppy kit list, and "present for a new puppy" with the two-dogs introduction. The pet rows
    # teach you how to look after an animal, so they carry PRESENT_ASK in their avoid and this row
    # takes the present.
    entry("gift-for-a-pet",
          (("cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "puppies", "pup",
            "rabbit", "rabbits", "bunny", "hamster", "gerbil", "guinea pig", "guinea pigs",
            "budgie", "parrot", "horse", "pony", "tortoise", "pet", "pets"),
           # A present has to be asked for, and the animal has to be the one it is for. The bare
           # shopping shapes are not enough on their own: "the dog's lead is broken what should i
           # buy" is a replacement lead, and it was read as a present for the dog. So the ask is
           # the gift nouns, an occasion, or the animal named as the owner - "get my cat", not
           # "get". Nothing that names a person either: "my dog is scared of my husband, how can
           # we get him to trust him" is a behaviour question, not a present.
           ("gift", "gifts", "present", "presents", "gift idea", "gift ideas", "present idea",
            "present ideas", "christmas present", "christmas gift", "birthday present",
            "birthday gift", "stocking", "christmas ideas", "presents for",
            "for christmas", "for his christmas", "for her christmas", "for its christmas",
            "for his birthday", "for her birthday", "for its birthday", "for their birthday",
            # the whole asking frame, ending in the animal: "what should i get my cat". A bare
            # "get my" or "for my" is half the care questions in the deck - "how do i get my dog
            # to come to me" is recall and "find a new home for my dog" is rehoming
            "what should i get my", "what can i get my", "what do i get my",
            "what should i buy my", "what can i buy my", "what do i buy my",
            "what should i get for my", "what to get my", "what to buy my")),
          ("For a pet, buy the comfort they use every day rather than another toy: a cat wants a "
           "warm bed by a radiator, a scratch post tall enough to stretch up on, or a food-puzzle "
           "ball; a dog wants a long-lasting chew it only gets on the day, a snuffle mat, or a "
           "spare lead for the car. A rabbit or a guinea pig wants a bigger hidey house and a "
           "chew stick, and a box with a blanket in it is famously the best present of all. Keep "
           "chocolate, grapes, raisins and anything with xylitol away from a dog, and skip the "
           "novelty toys they will ignore by Boxing Day."),
          # the care questions name a pet and often a shopping verb too: "what should i get my cat
          # to eat" and "what do i get my dog for his coat" are not presents
          avoid=LOSS + CRISIS + (
              "to eat", "eat", "eats", "eating", "feed", "feeds", "feeding", "food", "diet",
              "drink", "drinks", "water", "litter", "poo", "wees", "wee", "sick", "ill",
              "poorly", "vet", "vets", "limp", "limping", "pain", "hurt", "wont eat",
              "will not eat", "not eating", "off her food", "off his food", "diarrhoea",
              "vomiting", "scratching", "chewing", "barking", "biting", "training", "train",
              "walk", "walks", "walking", "to stop", "stop it", "behaviour", "behaving",
              "shampoo", "coat", "flea", "fleas", "worm", "worming", "neutered", "spay",
              # buying a thing for the animal is a different question with its own answer:
              # "should i buy a harness for my dog" is the harness card and "the dog's lead is
              # broken what should i buy" is a replacement lead, not a present
              "should i buy", "worth it", "is it worth", "need a", "harness", "lead", "collar",
              "muzzle", "crate", "carrier", "litter tray", "to sleep in", "to sleep on",
              # this row is a present for the animal. "gift for a dog lover" and "present for
              # someone who has a cat" name a person who owns one, and the person is the one
              # getting the present, so those stay with the grown-up gift rows.
              "lover", "lovers", "someone who has", "somebody who has", "who has a", "who has an",
              "who owns", "owner", "owners", "anyone who", "person who",
              # "presents" is also the word for what a cat drags in, and there the animal is
              # the one giving, not getting: "my cat keeps bringing dead mice in as presents"
              # was answered "buy the comfort they use every day rather than another toy",
              # where the hunting row has the answer. The giving words hold this row off and
              # leave those lines where they were.
              "bringing", "brings", "bring in", "brings in", "brought in", "brought me",
              "dead", "mice", "mouse", "bird", "birds", "vole", "voles", "rat", "rats",
              "hunting", "hunted", "killed", "caught", "cat flap"),
          bias=3),

    # "ive got a wedding in june and i have to do a speech" is a speech, not a present: the bare
    # verbs "get", "got", "give" and "bring" made every wedding anyone mentions a gift question,
    # and the present words are what actually ask for one.
    entry("gift-wedding", (("wedding", "registry", "marrying", "married"),
                           ("gift", "gifts", "present", "presents", "registry", "money", "buy",
                            "buying", "spend", "spending", "idea", "ideas", "what should i get",
                            "what do i get", "what can i get", "what to get", "what shall i get",
                            "get them", "get her", "get him", "give them", "give her", "give him",
                            "bring")),
          ("About £50 is the usual gift from a friend, £100 or more from a close friend or when "
           "the two of you go as a couple; what you can afford beats the table you are given. "
           "Check the registry next, since most couples list what they actually need, and a "
           "contribution to the honeymoon beats a guess. If there is no list, money in a card "
           "with a real note is never wrong, and one small thing for their home lands better "
           "than something big and impersonal. Say yes to the registry rather than worry about "
           "being original."),
          # A wedding you are going to gets a gift; a wedding you are planning is news, and the
          # memory lane answers it ("we are getting married next year" is not a gift question).
          # A thank-you card about a wedding present is the note to write, not a shopping
          # question: the present is already given, so the amount is the wrong answer. Only the
          # writing shapes are here, because "thanks - what should i get for a wedding" still
          # wants a gift.
          avoid=LOSS + CRISIS + ("getting married", "getting wed", "get married", "we are engaged",
                                 "engaged", "engagement", "planning", "venue", "guest list",
                                 # the tax on a present is money.py's gift card: "do i have to
                                 # pay tax on a wedding present from my parents" was answered
                                 # with the usual amount for a friend
                                 "tax", "taxed", "taxable", "tax free", "declare", "hmrc",
                                 "our wedding", "my wedding", "save the date",
                                 "thank you card", "thank you letter", "thank you note",
                                 "thank you message", "thank you wording",
                                 # "wedding music ideas" is the music, not the present
                                 "music", "song", "songs", "playlist", "band", "dj",
                                 "first dance", "aisle",
                                 # and the rest of the wedding that is not a present, which is
                                 # the same rule as the music above: the row keys "ideas" and
                                 # "what should i get", and those are ways of asking about
                                 # anything at a wedding - "wedding food ideas for 60 guests"
                                 # was answered with how much to spend on a present. Food, the
                                 # flowers, the photographs and the readings each have a card
                                 # of their own to answer with.
                                 "food", "menu", "menus", "catering", "caterer", "buffet",
                                 "meal", "eat", "feed", "canapes", "hog roast", "supper",
                                 "drinks", "food ideas", "flowers", "florist", "bouquet",
                                 "buttonhole", "photographer", "photographs", "photos",
                                 "readings", "vows", "order of the day", "what time"),
          bias=3, ask=GIFT_ASK),
    entry("gift-anniversary", ("anniversary", ("gift", "present", "ideas", "idea", "what to get",
                                               "what should i get", "what should we do")),
          ("Go for something shared rather than an object: dinner somewhere she has mentioned, a "
           "night away, or a small thing tied to a memory you both have. Write a card that says why, "
           "and it will beat anything expensive and impersonal.")),
    # Main's `gift-person` answers a named person ("my sister", "my boss") with a gift noun or
    # an asking frame. This one adds the pronoun: "my sister is called Meg" then "what should i
    # get her for her birthday", where the line names only `her` or `him`.
    # "someone"/"anyone" are out: "should i get someone in" is a plumber. "them" is here because
    # the reading tells the two people from the thing - `gift_ask` is True for "what should i get
    # them" and False for "what could be causing them" (a headache) and "should i get them in"
    # (a plumber) - and `_gift_anyone` stands down when the reading says no. Leaving it out on
    # the words alone sent the commonest way of asking for two people to the punt:
    #   what should i get them  ->  I don't know enough to answer that honestly.
    # "they" is the same person as the subject ("what should i get they" is not said, but "what
    # should i get them, they just had a baby" is), and the chat naming a baby is what makes it
    # the baby rather than the parents.
    # "what do i get my husband for his 50th" named the person in the possessive and reached
    # nothing; "what can i give my daughter for her birthday" used "give" and reached the party
    # row. The reading inside _gift_anyone keeps "his exam" and "give my toddler calpol" out, so
    # the key can afford the possessives and the give words.
    entry("gift-her", (("her", "him", "his", "their", "them", "they"),
                       # "whats a good present for him" names the present and the person and no
                       # buying verb; the noun phrase is the ask in that shape. Bare "present" is
                       # not in the key because "i gave him a present" is not this question.
                       ("get", "got", "buy", "bought", "give", "gives", "giving", "gave",
                        "present for", "presents for", "gift for", "gifts for")),
          _gift_anyone,
          # A present already bought is a report, not a request for ideas: "i bought a present
          # for him" and "i gave him a present" share the noun phrase with the question but are
          # about a purchase that has happened. "buy"/"get"/"give" are still the asks.
          avoid=LOSS + CRISIS + ("bought him", "bought her", "bought them", "gave him",
                                 "gave her", "gave them", "i bought", "i gave",
                                 "already bought", "already got", "have bought"),
          # A present owed is said without a question: "i still havent got her anything",
          # "nothing for him yet". The reading already decides whether it is a gift (this entry
          # stands down when it is not), so the asking words only have to let the line in.
          ask=("what", "which", "should", "could", "would", "any", "idea", "ideas", "suggest",
               "recommend", "stuck", "christmas", "birthday", "anniversary", "present",
               "gift", "still", "yet", "havent", "anything", "nothing")),
    entry("gift-generic", (("present", "gift"),
                           ("idea", "ideas", "stuck", "no idea", "what should", "suggest",
                            "for my", "for a", "for his", "for her", "christmas",
                            # "whats a good present" names the thing and the judgement and
                            # nothing else: every word above wanted an idea, a person or a
                            # question, so the plainest way of asking fell through all of them
                            # and got "I don't know enough to answer that honestly". A judgement
                            # word is what such a line has instead.
                            "good", "best", "nice", "any", "decent")),
          _gift_row("Pick something they'd use every week and wouldn't buy themselves: good "
                    "coffee and a proper mug, woolly socks, nice soap, a book about something "
                    "they care about. If you know what they do at the weekend, buy into that "
                    "instead - a voucher for the pool, the cinema or a class. Something "
                    "consumable and slightly better than usual is the safest bet for someone you "
                    "don't know well."),
          # "what should i say when someone gives me a gift i dont like" is the thanks, not the
          # buying: the row shared only the words "gift" and "what should" with it, and it
          # answered a question nobody had asked (see `thanks-for-a-gift` in wording.py).
          avoid=("say thank", "say thanks", "what do i say", "what should i say", "what to say",
                 "thank you for", "thank them", "thanks for the", "giving me", "gave me",
                 "got me", "i dont like", "i don't like", "dont like it", "don't like it",
                 "hate it", "returns", "return it", "regift"),
          # the pronoun rows answer "whats a good present for him", and they read the age and
          # the taste out of the chat where this card says one thing to everybody: the card is
          # for the ask that names nobody, so it stands down as soon as the line says who.
          guard=_nobody_named_by_pronoun),

    # Is it lazy to give a voucher? Six ways of asking it - "is a voucher a cop out", "are gift
    # cards lazy", "is cash a rude present", "can i give money instead of a gift", "is it ok to
    # give a voucher", "are gift cards a bad present" - were all the search shrug, and "can i give
    # money instead of a gift" was answered about a pay rise. The thing given opens the row and
    # the judgement closes it, so a gift card that expired stays with the consumer row.
    entry("gift-money", (("voucher", "vouchers", "gift card", "gift cards", "gift voucher",
                           "gift vouchers", "cash", "money", "banknote", "banknotes",
                           "tenner in a card", "a tenner in a"),
                          # the judgement, said as a question about the thing: not the bare
                          # "ok" or "fine", which is what every follow-up in a chat says
                          # ("ok what if they say no" was answered with this card once the
                          # conversation's money was in the line)
                          ("cop out", "lazy", "rude", "cheeky", "impersonal", "tacky",
                           "boring", "unoriginal", "lame", "bad present", "bad gift",
                           "good present", "good gift", "nice present", "acceptable present",
                           "ok present", "okay present", "ok gift", "okay gift", "fine present",
                           "instead of a gift", "instead of a present", "give money",
                           "giving money", "give cash", "giving cash", "give a voucher",
                           "give a gift card", "gift", "present", "presents", "sensible",
                           "safe bet")),
          "A voucher is not a cop out - a vague one is. Make it specific: a card for somewhere "
          "they already go (the cinema, a bookshop, the garden centre, their favourite cafe), or "
          "for a thing rather than a shop, and write on the card what you would do with it. Cash "
          "is fine too, and nobody is insulted by it: 'I did not know which one you wanted, so put "
          "it towards it' is the whole note. What reads as lazy is the generic card for a shop they "
          "never go in, handed over with nothing written on it - and a small thing plus a voucher "
          "beats both.",
          # an expired card, a shop that has folded and a refund are the consumer row's, and how
          # much to put in an envelope is the wedding gift row's. Money already on a card is the
          # balance question and not this one: the card is named in the key as the thing given,
          # so "how much is left on my gift card" and "check my gift card balance" were answered
          # with the etiquette of giving one (see the balance row in bot/knowledge/money.py, which
          # stood down on the same words). What is left on a card is the shop's or the app's to
          # say, and the composer's own line answers it honestly.
          avoid=("expired", "expire", "expires", "expiry", "run out", "ran out", "refund",
                 "refunded", "went bust", "has closed", "closed down", "cashback", "atm",
                 "withdraw", "withdrawal", "borrow", "borrowed", "lend", "lending",
                 "loan", "pay rise", "salary", "wage", "bank transfer", "wedding",
                 "christening", "how much money should i give", "how much should i spend",
                 "how much is usual", "tax", "voucher code", "discount code", "coupon",
                 "balance", "left on", "how much is left", "how much left", "how much is on",
                 "how much is there", "how much have i got",
                 "top up", "top it up", "load it", "reload", "remaining", "still valid")),

    # A tenner is the whole question: a secret santa, a stocking filler and "cheap present
    # ideas" all ask what is possible at that price, and the generic gift row answers "what
    # would I buy them" without ever looking at the money. The price words are in the key and
    # the gift words in the ask, so a cheap day out and a cheap meal stay with their own rows.
    entry("gift-cheap", (("secret santa", "santa", "stocking filler", "stocking fillers",
                          "tenner", "under a tenner", "under 10", "under ten pounds",
                          "under a fiver", "cheap present", "cheap gift", "small gift",
                          "little gift", "cheap ideas",
                          # "stocking filler ideas for my kids" and "small gifts for children"
                          # were getting the adult list - a candle, coffee, a scratch card, a
                          # paperback - which no child can use. The child words are in the key
                          # only so the price row can tell which of its two lists to give.
                          "stocking filler for kids", "gifts for kids", "gift for kids",
                          "gifts for children", "gift for children", "presents for kids",
                          "presents for children", "kids presents", "childrens presents",
                          "little gift for a child"),
                         ("idea", "ideas", "gift", "gifts", "present", "presents", "get",
                          "got", "buy", "bought", "under", "cheap", "what", "suggest",
                          "suggestion", "suggestions", "christmas",
                          # "secret santa at work and the limit is a tenner" is a budget, said
                          # with "limit": with only the gift word it scored one part and the
                          # turn went to a telling-a-child-off card that keyed a bare "limits"
                          "limit", "limits", "spend", "spending",
                          # ... and what the child is called counts as the asking frame too,
                          # so "cheap present ideas for my nephew" is this row's as well
                          "child", "children", "kid", "kids", "toddler", "toddlers", "boy",
                          "girl", "son", "daughter", "niece", "nephew", "grandchildren",
                          "grandchild", "teenager")),
          _gift_cheap,
          # A point of bias for the cheap child lines: "cheap present ideas for a child" and
          # "cheap present ideas for my nephew" were the generic gift list, which is coffee, soap
          # and socks. A named grown-up is still the person row's caller, because those words are
          # in `avoid` below.
          bias=1,
          # the money question is a budget, and the free day out is a day out: neither is a gift
          avoid=("how much", "budget", "day out", "days out", "meal", "meals", "dinner",
                 "food", "eat", "cook", "cooking", "recipe", "recipes", "holiday",
                 "days out with the kids", "something to do", "things to do", "cinema tickets",
                 # a named person keeps the row for that person: "what do you get a friend for
                 # secret santa" is a present question about a friend first, and the price only
                 # decides when nobody is named
                 "friend", "friends", "mate", "mates", "colleague", "colleagues", "workmate",
                 "mum", "mother", "nan", "grandma", "dad", "father", "grandad", "sister",
                 "brother", "husband", "wife", "partner", "boyfriend", "girlfriend",
                 "teacher", "neighbour", "neighbor", "cousin", "auntie", "uncle")),

    # "what do you get someone who has everything" is not a "what should I buy" question: the
    # person has the objects already, and the row that answers a present for a parent ends its
    # reply by saying so. The lines that say it are their own key, so nothing else moves.
    entry("gift-has-everything", (("has everything", "who has everything", "wants nothing",
                                   "needs nothing", "hard to buy for", "impossible to buy for",
                                   "doesnt want anything", "does not want anything",
                                   "says they want nothing", "want for nothing"),
                                  ("gift", "gifts", "present", "presents", "get", "got",
                                   "buy", "bought", "idea", "ideas", "what", "christmas",
                                   "birthday", "suggest", "suggestions",
                                   # "he has everything already" is the same statement as the
                                   # question, made as a follow-up to an answer that offered
                                   # things to buy. Without "already" it reached the turn-down
                                   # reader and came back as "Both then: ...".
                                   "already")),
          ("Go for time and something used up rather than another object: a meal or a night away "
           "somewhere they have mentioned, tickets to something on their list, a lesson in a thing "
           "they keep talking about, or a very good version of a daily thing - coffee, olive oil, "
           "socks - with a note saying why you picked it. Someone who wants for nothing is short "
           "of time and good consumables, not of things."),
          bias=1,
          # a person who has nothing is not this question, and neither is a bereavement or a
          # hospital stay
          avoid=("nothing to eat", "no money", "cant afford", "food bank", "hospital", "ward",
                 "dying", "died", "funeral", "grief", "grieving", "cancer", "care home",
                 "job", "rent", "benefits",
                 # When the line names the person, the row for that person answers it and
                 # already ends by naming the someone-who-has-everything case: "my dad has
                 # everything and i dont know what to buy" is better answered with coffee and a
                 # bottle than with a lesson they never asked for.
                 "mum", "mother", "nan", "grandma", "granny", "dad", "father", "grandad",
                 "stepdad", "sister", "brother", "husband", "wife", "partner", "boyfriend",
                 "girlfriend", "colleague", "workmate", "teacher", "neighbour", "neighbor",
                 # A message in the card is words to write, not a present to buy: "birthday card
                 # message for someone who has everything" was answered with coffee, olive oil
                 # and socks. The buy words stay, so "what do i get someone who has everything"
                 # is still this row.
                 "write", "writing", "written", "card message", "card say", "card says",
                 "what to say", "the message", "message in", "words")),

    entry("used-car", (("used car", "second-hand car", "second hand car", "buying a car",
                        "car for sale"),
                       ("used", "second hand", "buy", "buying", "check", "seller", "inspector",
                        "deposit", "mot", "mileage", "history")),
          ("Ask how long they've owned it and why they're selling, then check the MOT history "
           "online for gaps and advisories before you look at the paint. On the drive, listen for "
           "knocks over bumps and make sure every gear and switch works; pay for an inspection on "
           "anything over a couple of thousand, and never send a deposit before you've seen the car "
           "and the V5 in their name."),
          # How to pay for the car is a different question with a different answer: the lease-or-
          # buy entry owns it, and "lease or buy a car" was the used-car checklist.
          avoid=("lease", "leasing", "leased", "pcp", "contract hire", "hire purchase",
                 "finance", "on finance", "car finance", "car loan", "loan for a car",
                 "monthly payment", "monthly payments", "per month", "rent or buy")),

    # Checking a car's past is its own question, and its words were nobody's: "how do i check a
    # car history before buying" reached the essay card on "history", "how do i check mileage on
    # a used car" the mileage-allowance row, "how do i do an hpi check" and "how do i check a car
    # is not stolen" nothing at all, and "how do i check if a car has been in an accident" the
    # search hedge. The subject is the car, and the second signal is the part of its past being
    # looked into, so one answer covers every way of asking it.
    entry("car-history-check",
          (("car", "cars", "vehicle", "van", "motor", "hpi", "motorbike", "v5c", "v5",
            "log book", "history check", "vehicle check", "hpi check"),
           ("car history", "vehicle history", "history check", "history on", "hpi",
            "hpi check", "been in an accident", "in an accident", "any accidents",
            "written off", "write off", "write-off",
            "clocked", "mileage on", "the mileage", "outstanding finance", "finance on it",
            "finance outstanding", "not stolen", "is stolen", "been stolen", "stolen",
            "v5", "v5c", "log book", "vin", "previous owner", "previous keepers",
            "before buying", "genuine", "real", "fake", "forged", "verify", "legit",
            "history")),
          # "should i get an hpi check" and "is a vehicle history check worth it" are yes/no
          # questions, so the yes comes first; the two figures are the reason for it.
          ("Yes, two checks cover it, one free and one about fifteen pounds. Put the number plate into "
           "gov.uk's MOT history page first: every test since 2005, the mileage at each one, and "
           "the gaps and repeated advisories that a tidy advert hides. Then buy a full history "
           "check - HPI, the AA or Total Car Check - which tells you about outstanding finance, a "
           "stolen record, an insurance write-off and a mileage discrepancy. Before you pay, match "
           "the VIN on the windscreen to the V5C, check the V5C is in the seller's name at the "
           "address you are standing at, and walk away from anything that does not line up."),
          bias=2,
          ask=("check", "checks", "checking", "checked", "history", "safe", "genuine", "real",
               "trust", "verify", "make sure", "before", "buy", "buying", "worth", "how do i",
               "is there", "does it", "has it", "can i", "should i"),
          # A crash you were in is an insurance and repair question, not a car you are thinking of
          # buying: "my car has been in an accident" and "i crashed the car" are not this row.
          avoid=("insurance", "claim", "claims", "payout", "write it off", "my car", "our car",
                 "i crashed", "crashed", "i hit", "scratch", "scratched", "dented", "repair",
                 "repairs", "garage", "bodywork", "injury", "injured", "hurt", "police",
                 "crash", "bump", "no claims", "excess", "premium", "quote", "renewal",
                 "sell my", "selling my", "part exchange", "trade in", "trade-in",
                 # a family or a medical history is not a car's: a loose "history" is a wide
                 # word, and every one of those lines says so with one of these
                 "family", "medical", "health", "symptoms", "heart", "cancer", "mental",
                 "doctor", "gp", "hospital",
                 # ...and "the history of the car" is a question about the past of the whole
                 # industry, not a car you are about to buy: six lines said "history of", "long
                 # history" or "history month" and got the MOT page they never asked for
                 "history of", "long history", "history month", "the history")),

    # A write-off category is a fact people ask about by name, and the dealer-rights card was
    # taking it: "is a cat s car safe to buy" is not a complaint about a car you already own.
    entry("write-off-category",
          (("cat s", "cat n", "cat c", "cat d", "cat a", "cat b", "category s", "category n",
            "category c", "category d", "write off", "write-off", "written off",
            "insurance write off", "write off category", "kill the car"),
           ("car", "van", "vehicle", "buy", "buying", "bought", "safe", "worth", "should i",
            "what", "mean", "means", "difference", "between", "explain", "any good", "avoid",
            "insure", "insurance", "cheaper", "value", "sell")),
          ("Both mean an insurer wrote the car off instead of repairing it, and both are legal to "
           "buy and drive once the repair has been signed off. Cat N is non-structural damage - "
           "usually a stolen-and-recovered car, a bump or flood - and cat S is structural damage "
           "that was pulled straight again. (Cat A and B are breaker-only and must never go back on "
           "the road.) An S car is worth less than an N, both are worth noticeably less than a "
           "clean one, and both are harder to insure and to sell on: ask for the damage photos and "
           "the repair invoice, have an inspection done, and get an insurance quote on the "
           "registration before you commit."),
          bias=2,
          # A crash you were in, and a car your insurer has just written off, are the accident and
          # claim rows' questions: this is only the category you are being sold.
          avoid=("crashed", "crash", "i hit", "accident", "claim", "claims", "payout",
                 "my insurance", "the insurance", "other driver", "police", "repair it",
                 "repairs", "garage", "injury", "injured", "hurt")),
    entry("used-car-seller", (("seller",),
                              ("ask", "question", "questions", "happy", "know", "check", "car",
                               "hpi", "history")),
          ("Ask how long they've owned it and why they're selling, whether it's ever been in an "
           "accident, what the mileage is, when the cambelt or chain was last done, and whether "
           "the service history and V5 are both in their name. Ask to see it at their home rather "
           "than a car park: it tells you how the car has been kept, and it's where a private "
           "seller's story tends to come apart.")),

    # "whats a good first car for a new driver" was answered with Karl Benz in 1885 (history's
    # invented-the-car row), and with that fenced off it became the search hedge or the
    # petrol-or-electric trade. The used-car checklist below is about checking a car you have
    # found, not about choosing the first one.
    entry("first-car",
          (("first car", "new driver", "learner driver", "car for a new driver",
            # the learner's own words: "whats a good car for a learner" was the search hedge
            # while the first-car card answered the same question asked about a new driver
            "car for a learner", "learner car", "car for a learner driver"),
           ("good", "best", "buy", "buying", "recommend", "cheap", "what", "which", "how do i",
            "should i", "advice", "get", "start")),
          "Small, petrol, and as dull as you can bear: a hatchback like a Corsa, Fiesta, Polo or "
          "Yaris with a small engine. Check two things before the car itself - the insurance "
          "group, because a 1.0-litre in a low group can cost half what a bigger car costs to "
          "insure, and the MOT history on gov.uk for gaps and advisories. Spend under half your "
          "budget on the car and keep the rest for insurance, tax and the first repair, and avoid "
          "anything modified, since insurers charge more for it.",
          bias=2,
          avoid=("i passed my test", "passed my driving test", "taxi", "van", "motorbike",
                 "insurance quote", "how much is insurance", "tyre", "tyres", "battery", "oil")),

    entry("used-car-inspection",
          # "is a used car inspection worth it" is the inspection card's question, and the words
          # that ask it are a check on a car by name: the AA's, the RAC's, an HPI history check,
          # a vehicle check, a buyer's report. Read without them the row tied with the
          # repair-or-scrap rule ("Money against value...", which is about the car's own repairs)
          # and with the general "how do I find the money" card, and both are answers to other
          # lines.
          (("inspection", "inspections", "inspecting", "checked over", "pre purchase",
            "pre-purchase", "aa check", "rac check", "vehicle check", "vehicle inspection",
            "history check", "hpi", "hpi check", "buyers report", "buyer's report"),
           ("worth", "pay", "paying", "car", "cars", "need", "should", "cost", "costs",
            "how much", "money", "expensive", "bother", "any point", "get one",
            "get it checked", "get checked")),
          # the figure comes first because the same card answers "how much is a pre purchase
          # inspection", and the yes still opens it for "is a car inspection worth it"
          ("Yes, and about a hundred to two hundred pounds: a pre-purchase inspection from the AA, "
           "RAC or a good local garage costs that on anything over about two thousand pounds, and "
           "it catches the hidden faults a test drive can't. Book it after you've seen the car and "
           "agreed a price in principle, and walk away if the seller won't allow one."),
          # "is an inspection worth it" is answered better by the inspection line than the general
          # used-car one, and the two tie on the words.
          bias=1),

    # "how much does a used car cost" and "is 3000 too much for a used car" were answered with the
    # inspection card (it states money, so the price filter let it through) and "how much is a new
    # car" with the honest "I can't look up live prices". What a car costs at each age is a figure
    # a friend knows, and it is the thing that decides every other question about a car.
    entry("used-car-price", (("used car", "second-hand car", "second hand car", "secondhand car"),
                            ("how much", "cost", "costs", "price", "prices", "spend", "pay",
                             "budget", "afford", "expensive", "cheap", "too much")),
          "A used car is about £2,000 to £4,000 for 10 to 15 years old and 80,000 miles or more, "
          "£5,000 to £8,000 for 5 to 8 years old, and £9,000 to £14,000 for 3 to 5. Whatever the "
          "price, check the MOT history free on gov.uk and keep £500 back for the first repair.",
          ask=("how much", "cost", "price", "spend", "pay", "budget", "expensive", "much"),
          bias=2,
          # the price of a car is not the price of running one, insuring it, fixing it, renting
          # one, or of a bike, a van or a caravan
          avoid=("insurance", "insure", "tax", "fuel", "petrol", "diesel", "running",
                 "service", "servicing", "repair", "repairs", "fix", "mot", "tyre",
                 "tyres", "lease", "leasing", "finance", "rent", "rental", "hire",
                 "sell", "selling", "worth", "trade in", "part exchange", "haggle",
                 "bike", "bicycle", "van", "caravan", "motorbike", "scooter", "taxi",
                 "train", "parking", "clamp", "first car", "learner", "good", "best",
                 "weigh", "weight", "run", "running costs", "wash", "valet", "battery",
                 "clutch", "breakdown", "new", "brand new", "brand-new")),

    # "how much is a new car" was answered with the honesty line, and the used bands are the wrong
    # shape for it: the new price, and what it loses, is the thing the person is weighing up.
    entry("new-car-price", (("new car", "brand new car", "brand-new car"),
                            ("how much", "cost", "costs", "price", "prices", "spend", "pay",
                             "budget", "afford", "expensive", "cheap", "worth")),
          "A new small car starts around £18,000 and a new family car around £28,000, and either "
          "loses a fifth to a third of that in the first year, most of it in the first hour. A "
          "two or three year old version of the same car is about half the new price, which is "
          "why that age is where most people buy.",
          ask=("how much", "cost", "price", "spend", "pay", "budget", "expensive", "worth"),
          bias=2,
          avoid=("used", "second hand", "secondhand", "insurance", "insure", "tax", "fuel",
                 "petrol", "diesel", "running", "service", "servicing", "repair", "fix",
                 "mot", "tyres", "lease", "leasing", "finance", "rent", "hire", "sell",
                 "selling", "trade in", "part exchange", "haggle", "bike", "van", "caravan",
                 "weigh", "weight", "wash", "valet", "breakdown", "first car", "good",
                 "best", "electric", "ev", "hybrid")),

    # "flowers or a plant" is a choice, not a request for gardening advice: the garden words are on
    # the avoid list so "how do i grow flowers from seed" stays with the garden domain.
    entry("flowers-or-plant", (("flowers", "flower", "bouquet", "plant", "orchid", "houseplant"),
                               # no "birthday" (cake-plan's key word) and no "party": both are rare
                               # elsewhere, and a shared rare word costs those entries a rank point
                               ("or", "instead", "better", "gift", "present", "get", "buy",
                                "thank", "sorry")),
          ("Flowers, most of the time: go to a florist rather than a garage and ask for what is in "
           "season, and a mixed bunch is always safe. A plant lasts years and is the better present "
           "for someone who likes looking after things, but give an orchid or a houseplant only to "
           "a person who will remember to water it."),
          # note: no "planting" here - its loose form is "plant", which would veto the question
          avoid=("garden", "gardening", "grow", "growing", "seed", "seeds", "soil",
                 "compost", "lawn", "prune", "allergic", "dying", "wilt",
                 "cheaper", "cheapest", "price", "cost", "online", "delivery", "sale",
                 # "how do plants get water up their stems" is botany, and "get" is in this key,
                 # so the words of that question keep it out: nobody buys a bouquet with stems
                 # in mind.
                 "water", "watering", "stem", "stems", "roots", "root", "drink", "drinking",
                 "leaves", "leaf", "yellow", "yellowing",
                 # "plant" is the verb as well as the present, so "plant a tree ... or ..." reached
                 # this answer: "should i plant a tree now or wait till spring" was a bunch of
                 # flowers. A spade in the line is the garden domain's question.
                 "tree", "trees", "shrub", "shrubs", "hedge", "hedges", "bulbs", "sow", "sowing",
                 "plant out", "planting out", "when to plant",
                 # how a plant feeds itself is botany, not a present: "how do plants get their
                 # food" and "how do plants get energy" were a bunch of flowers, because "plant"
                 # and "get" carry the key on their own.
                 "photosynthesis", "make food", "makes food", "their food", "own food", "food for",
                 "energy", "sunlight", "carbon dioxide", "chlorophyll", "feed", "feeds",
                 "feeding", "fertiliser", "fertilizer",
                 # a mouldy pot is a plant that is unwell, not a present: "how do i get rid of
                 # mould in a plant pot" was a bunch of flowers, because "plant" and "get" carry
                 # this key on their own. The garden rows answer every one of these.
                 "mould", "mold", "mouldy", "moldy", "mildew", "fungus", "fuzzy", "furry",
                 "rot", "rotting", "repot", "repotting", "gnat", "gnats",
                 # "my houseplant is looking sorry for itself" is a plant that is unwell, not a
                 # present: "plant" and the "sorry" of a sorry-gift read as a bunch of flowers.
                 # What is left of the gift question - "flowers or a plant", "should i get her
                 # flowers" - says none of these, so it keeps this answer.
                 "sorry for itself", "look sad", "looks sad", "looking sad", "unhappy",
                 "miserable", "sulking", "drooping", "droopy", "limp", "floppy",
                 # a plant that has stopped flowering is a garden question, and "get" is in
                 # this key: "how do i get my cactus to flower" was a bunch of flowers.
                 # "flowering" cannot be one of these words: its loose form is "flower", which is
                 # a form of "flowers", so it vetoed every line that says flowers - "flowers or
                 # chocolates" and "should i get her flowers or a plant" were left with no answer
                 # at all. "in flower" and "not flowering" say it without the bare form.
                 "cactus", "cacti", "cactuses", "succulent", "succulents",
                 "to flower", "flower again", "flowers again", "in flower", "bloom", "blooms",
                 "blooming", "blossom", "buds", "no flowers", "not flowering", "won't flower",
                 "wont flower", "died", "dies", "repot", "repotting")),
    entry("appliance-worth",
          (("air fryer", "air fryers", "airfryer", "slow cooker", "slow cookers", "pressure cooker",
            "instant pot", "bread maker", "bread machine", "dishwasher", "dishwashers",
            "tumble dryer", "tumble dryers", "robot vacuum", "robot hoover", "dehumidifier",
            # the kind of dryer people buy now, said by name: the table in this file already had
            # the heat pump row and the row's key did not, so "is a heat pump dryer any good"
            # reached no answer at all, and "are heat pump dryers any good" got the generic
            # trade in a tumble dryer.
            "heat pump dryer", "heat pump dryers", "heat pump drier", "heat pump tumble dryer",
            "heat pump tumble drier", "heat pump condensing dryer", "vented dryer",
            "vented tumble dryer", "condenser dryer", "condenser tumble dryer",
            "coffee machine", "bean to cup", "stand mixer", "microwave", "microwaves",
            "food processor", "kitchen machine", "air purifier", "heated airer",
            "meal kit", "meal kits", "recipe box", "hello fresh", "gousto", "kindle", "e reader",
            "ereader", "noise cancelling headphones", "noise cancelling",
            "fitness tracker", "fitness trackers", "fitbit", "smart watch", "smart watches",
            "apple watch", "standing desk", "standing desks", "sit stand desk",
            "weighted blanket", "weighted blankets", "steam cleaner", "steam cleaners",
            "steam mop", "cleaner", "cleaners", "cleaning service",
            "housekeeper",
            "heated clothes airer", "heated drying rack", "electric blanket",
            "heated blanket",
            # the same buying question for the things people ask in the same breath; a water
            # softener is here because its words took the fabric softener row instead
            "smart thermostat", "thermostat", "water filter jug", "water filter", "filter jug",
            "humidifier",
            "mattress topper", "bed topper", "water softener", "robot mower", "robot lawn mower",
            "video doorbell", "ring doorbell", "fan", "fans", "tower fan", "pedestal fan",
            "fan heater", "electric heater", "oil filled radiator", "space heater"),
           ("worth", "worth it", "worth the money", "should i", "do i need", "need", "buy",
            "buying", "get", "getting", "good", "any good", "value", "money",
            "recommend", "recommended", "recommendation", "recommendations",
            # The same buy question asked as a doubt about spending at all: "any point in a
            # dehumidifier", "any point in a standing desk", "is a weighted blanket a waste of
            # money". The second signal has to sit in the key, not only in the row's ask list,
            # because a line's two signals come from two parts of the key: with the ask phrase
            # alone the row still scored 0 and the decision module shrugged.
            "any point in", "any point to", "point in", "point to", "point of",
            "waste of money", "wasting money", "money well spent", "bother with", "bother",
            # the help shape, so "will a dehumidifier help" scores as the question it is
            "help", "help with", "helped")),
          _appliance_value,
          ask=APPLIANCE_ASK,
          # a machine they already have, that is faulty, is the repair rule's question
          # A watch you wear answers better from technology's smart-watch entry (battery life,
          # iPhone pairing) than from the appliance checklist - but only the lines about wearing
          # it. Holding out the watch names themselves took "is a smart watch worth it" off the
          # worth-it answer it belongs to, so the guard is the shapes that make it a how-does-it
          # -work question.
          avoid=("battery life", "battery", "charge", "charging", "pair", "pairing",
                 "pairs with", "sync", "syncs", "syncing", "steps", "step count",
                 "heart rate", "companion app", "notifications", "fitness tracker",
                 "fitness watch",
                 "my ", "our ", "broken", "broke", "repair", "repairing", "fix", "fixing",
                 "leaking", "noisy", "not heating", "wont", "won't", "error", "fault",
                 "warranty", "guarantee", "manual", "clean", "cleaning", "descale",
                 "how do i", "how to",
                 # Asking for the food, not the machine: "recommendations for slow cooker recipes"
                 # and "recommend a slow cooker recipe" want something to cook in it, and the
                 # worth-it rule only says whether to buy it. The phrases are about cooking, not
                 # the bare word, because "recipe box" and "meal kit" are the same table's names
                 # and a bare "recipes" folded onto them and took "is a recipe box worth it" off
                 # its own answer.
                 "recipes for", "recipe for", "recipes with", "recipe with", "recipe ideas",
                 "recipe idea", "cooker recipe", "cooker recipes", "fryer recipe",
                 "fryer recipes", "maker recipe", "maker recipes", "cook recipe",
                 "cook recipes", "what to cook", "what can i cook", "meal ideas",
                 "dinner ideas", "to cook in", "cook in a", "cook in an", "cook in it",
                 "cook with it", "something to cook"),
          # Whether a machine is worth having is not where to get one. This row is keyed on the
          # appliance name and the bare verbs "buy" and "get", so it claimed the place questions
          # first ("where can i buy a cheap air fryer" was told it is worth it for two people,
          # "where to buy a slow cooker" that it suits someone out all day), and the shopping
          # domain's buying row never got its turn.
          guard=lambda understood: not asks_where_a_shop_answers(understood),
          bias=1),
    entry("choice-worth",
          # The gym is the one thing here named by an action, so its keys are the action phrases:
          # "should i go to the gym", "should i bother going to the gym" and "should i go back to
          # the gym" were the you-decide punt while "should i join a gym" got the trade. The ask
          # list is what keeps this safe - a line that reports going to the gym has no "should i"
          # in it - and the frequency avoids keep the routine questions out of the trade.
          (("gym membership", "gym memberships", "join a gym", "joining a gym",
            "go to the gym", "go the gym", "going to the gym", "back to the gym",
            "bother going to the gym", "bother with the gym", "bother with a gym",
            "start going to the gym", "start at the gym",
            "heat pump",
            "heat pumps", "electric car", "electric cars", "season ticket", "season tickets",
            "smart meter", "smart meters", "water meter", "water meters"),
           ("worth", "worth it", "worth the money", "should i", "shall i", "shall we",
            "should we", "do i need", "buy", "buying",
            "get", "join", "joining", "pay", "paying", "better", "off",
            "recommend", "recommended", "recommendation", "recommendations",
            # the doubt about spending, which is the same question: "any point in a heat pump",
            # "would a heat pump be a waste of money"
            "any point in", "point in", "point to", "waste of money", "money well spent")),
          _choice_value,
          ask=APPLIANCE_ASK,
          # a thing with its own answer is not this: insurance, a warranty, uni, a mortgage
          avoid=("insurance", "warranty", "uni", "university", "degree", "mattress", "inspection",
                 # how often to go is the routine's question ("three sessions a week"), and how
                 # busy a gym is or what to do there are other rows again: this one is only
                 # whether it is worth it
                 "how often", "how many times a week", "how many times a month", "how regular",
                 "how busy", "what time", "what should i do", "what to do at",
                 "how do i", "how to", "tax", "lease", "hire purchase", "prices", "price",
                 "cost per", "how much",
                 # the meter you already have: reading it, or one that has stopped, is smart-meter-how
                 "read", "reading", "blank", "display", "sending", "signal", "stopped", "faulty",
                 "not working",
                 # "should i get a water meter fitted" is the water bill's question - the reply
                 # there says who fits it and when it pays - while "is a water meter worth it" is
                 # this one's. The fitting words tell them apart, and they are written as phrases
                 # about the meter: a bare "install" or "fitted" also struck "is it worth
                 # fitting a water meter", which is this row's own question, and handed it to the
                 # bill answer.
                 # "installed" and "installation" are deliberately not here: "is it worth
                 # having a water meter installed" asks this table's question in the past
                 # participle, and the words that make it a job are fit and fitting.
                 "meter fitted", "meter fitting",
                 "fit the meter", "fit a meter", "fitting the meter", "fitting a meter",
                 "install the meter", "install a meter", "installing the meter",
                 "installing a meter", "installation of the meter", "installation of a meter"),
          bias=1),
    # "what is a smart meter" is the definition, and it was a shrug: the how entry wants a word
    # about reading it or a fault, and the worth entry wants "should i". Two other questions wear
    # the same name - is one worth it, and what happens when they fit yours - and each has its row.
    entry("smart-meter-what",
          (("smart meter", "smart meters", "in home display", "in-home display"),
           ("what is", "whats", "what are", "what does", "what do", "explain", "definition",
            # how it works is the in-home-display answer's question, not the definition's
            "mean", "means", "work out")),
          "A smart meter is the gas and electricity meter that sends your readings to your supplier "
          "itself, so nobody has to read it and the bill is based on what you used rather than an "
          "estimate. It comes with a small display for the kitchen that shows what you are spending "
          "as you use it. It is free from your supplier and it does not change your tariff.",
          # what one is worth, and the one in the hall that has stopped, are their own answers
          avoid=("worth", "worth it", "should i", "any good", "good buy", "read", "reading",
                 "blank", "stopped", "faulty", "broken", "not working", "display is",
                 "fitted", "fitting", "install", "installed", "installation", "appointment"),
          bias=1),
    # "theyre fitting a smart meter next week" was echoed back: the fitting is a visit to get
    # ready for, and the worth entry stands down on the meter-fitted words on purpose.
    entry("smart-meter-fitting",
          (("smart meter", "smart meters", "meter", "meters"),
           ("fitting", "fit one", "fit mine", "fit my", "fit a", "fit the", "fitted", "install",
            "installed", "installation", "appointment", "coming round", "coming to", "engineer",
            "next week", "next month", "on the day", "switch over", "swapping", "change my meter",
            "upgrade")),
          "Clear the cupboard the meters are in and take a photo of the readings first, because "
          "the old ones go with the fitter. Someone over 18 has to be in, and it takes about an "
          "hour per fuel; the gas and electricity go off for a few minutes each. The fitter should "
          "leave the in-home display set up and working, and the old meters away - if a display "
          "is not showing, ring the supplier rather than living with it.",
          ask=("smart meter", "smart meters", "meter", "meters"),
          # a meter that is broken, or one you are deciding about, is not the fitting visit
          avoid=("worth", "worth it", "should i", "broken", "faulty", "not working", "blank",
                 "leaking", "water meter", "parking", "electricity bill", "read my"),
          bias=1),
    entry("smart-meter-how",
          (("smart meter", "smart meters", "in home display", "in-home display"),
           ("read", "reading", "readings", "button", "blank", "stopped", "faulty", "broken",
            "working", "display", "sending", "signal", "connect", "wrong", "show", "shows",
            "mean", "means", "numbers")),
          _smart_meter_how,
          # "how do i read my smart meter" and "my smart meter display is blank" are the meter in
          # the hall, not a buying decision, so the worth answer above stands down on them
          avoid=("worth", "worth it", "should i", "good buy", "any good"),
          bias=1),
    # "whats a good watch to buy" was answered with a film for tonight, because "watch" is the
    # verb of the film question and the film table is a big thing. A wristwatch is a purchase.
    entry("watch-buy", (("watch", "watches", "wristwatch", "wrist watch", "smartwatch",
                         "smart watch", "apple watch", "garmin", "fitbit", "casio", "timex",
                         "seiko", "normal watch", "ordinary watch", "mechanical watch",
                         "analogue watch", "analog watch"),
                        ("buy", "buying", "get", "getting", "new", "which", "recommend", "worth",
                         "good", "first", "choose", "choosing", "spend", "spending", "best",
                         "pick", "should", "vs", "versus", "or")),
          _watch_help,
          ask=("buy", "buying", "get", "getting", "new", "which", "recommend", "worth", "good",
               "first", "choose", "choosing", "spend", "spending", "best", "pick", "should"),
          # a film, a series or a match is watched, not bought, and a watch that has stopped is a
          # repair question rather than a shopping one
          avoid=("tonight", "film", "films", "movie", "movies", "series", "tv", "programme",
                 "program", "show", "netflix", "episode", "stream", "streaming", "cinema",
                 "box set", "match", "game", "football", "stopped", "broken", "broke", "fault",
                 "repair", "strap", "battery", "not working", "screen", "loses time", "fast",
                 "slow",
                 # the verb of the film question: "whats good to watch" is watch + good, which is
                 # this entry's key and ask, and no word above was in the line.
                 "to watch", "watch tonight", "watch on", "whats on", "watch it",
                 # the same verb with no film word anywhere in the line: "what should we watch
                 # next", "what should i watch", "whats worth watching". Each is a modal, a
                 # subject and the verb, which a wristwatch question never says.
                 "should i watch", "should we watch", "shall i watch", "shall we watch",
                 "can i watch", "can we watch", "i watch", "we watch", "worth watching"),
          bias=2),
    entry("buy-a-vacuum", (("hoover", "hoovers", "vacuum cleaner", "vacuum cleaners", "vacuums"),
                           ("buy", "buying", "look for", "choose", "choosing", "best", "worth",
                            "which", "recommend", "new")),
          "Check the weight and the cord length before anything else, because the best vacuum is "
          "the one you will actually push round the house. A bagged machine holds its suction and "
          "suits anyone with allergies; a bagless one is cheaper to run but needs emptying over a "
          "bin. A cordless is a quick-clean tool and rarely enough on its own in a carpeted house, "
          "so try one for weight and check the filters can be washed.",
          avoid=("robot", "car", "flask", "seal", "bags for", "washing machine")),
    # A price match is never automatic: the retailer sets the rules, so the answer is how to make
    # the claim stick in the five minutes you have at the till.
    entry("price-match",
          (("price match", "price match it", "match the price", "match a price", "price promise",
            "price guarantee", "cheaper elsewhere", "cheaper in another shop", "cheaper online",
            "found it cheaper", "same thing cheaper", "beat the price", "beat it by"),
           ("can i", "will they", "do they", "ask", "get", "how", "shop", "store", "retailer",
            "online", "till", "checkout", "worth", "any point", "does", "you", "they", "it",
            "elsewhere", "i found")),
          "Ask at the till before you pay, because almost no retailer matches a price after the "
          "sale. Have the competitor's page open on your phone with the exact model, the price and "
          "the date, and check the small print first: most promises exclude marketplace and "
          "third-party sellers, sale and clearance prices, membership prices, vouchers and "
          "mis-priced listings. Some chains match online prices only against their own website, and "
          "a few knock off the difference rather than the whole amount. If the assistant says no, "
          "ask for the manager and ask which rule you missed - a written promise on the wall is "
          "worth quoting.",
          avoid=("flights", "hotel", "insurance", "energy", "broadband", "mobile", "mortgage",
                 "train", "supermarket", "petrol"),
          # "my phone is cheaper online" is a remark; the claim is worth making only when asked
          ask=("do", "does", "can", "will", "should", "how", "worth", "found", "ask", "try")),
    # The online-or-shop question is a returns question, not a saving question.
    entry("online-or-in-store",
          (("buy online", "buying online", "buy it online", "order online", "order it online",
            "in store", "in the shop", "in a shop", "in person", "go to the shop", "collect",
            "click and collect", "online or in store", "online or in the shop",
            "online or shop", "shop or online"),
           ("cheaper", "cheap", "better", "should i", "worth", "or", "which", "safer", "returns",
            "return", "rights", "guarantee", "warranty", "problem")),
          "Buying online gives you a 14-day right to change your mind from the day it arrives, and "
          "you only pay the return postage unless the shop says otherwise; buying in a shop gives "
          "you no right to change your mind at all, only the shop's own policy. That is the real "
          "difference, not the price. So for anything you might not keep - clothes, a mattress, "
          "furniture in a colour you have not seen - order online and check the returns page before "
          "you pay. For something you need today, or want to try first, buy in the shop and ask "
          "what their returns policy is in writing.",
          avoid=("flight", "hotel", "train", "ticket", "insurance", "car insurance", "energy",
                 "broadband", "mobile phone contract", "grocery", "food shop")),
    entry("bag-charge",
          (("bag charge", "bag charges", "charge for bags", "carrier bag", "carrier bags",
            "plastic bag", "plastic bags", "5p bag", "10p bag", "bag for life", "reusable bag",
            "pay for bags", "pay for a bag", "bags cost",
            # the complaint shape, not the question shape: the card's own last line is what to
            # do about it ("say so at the till and it comes off"), and "i was charged for a bag
            # at the till" was an "I'm here if you want to dig into any of that"
            "charged for a bag", "charged for bags", "charged me for a bag",
            "charged me for bags", "a bag at the till", "charge me for a bag"),
           ("why", "how much", "have to", "must i", "do i", "charge", "cost", "free", "law",
            "shop", "supermarket", "still", "tax", "gone up",
            "till", "checkout", "charged me", "i was", "didnt ask", "didn't ask")),
          "Shops in the UK have to charge for single-use carrier bags, and the money goes to good "
          "causes rather than to the shop, which is why the charge exists at all: it is there to cut "
          "how many bags are thrown away, and it works. A bag for life is the cheap way round it - "
          "most supermarkets replace it free when it finally splits - and small paper bags for loose "
          "fruit and veg are usually free and are not the charge. If you are charged for a bag you "
          "did not ask for, say so at the till and it comes off.",
          avoid=("hand luggage", "airline", "flight", "carrier bag levy ireland", "bin bag",
                 "vacuum", "hoover", "sleeping bag", "tea bag", "bags for",
                 # a bag charged for on a shop's own account is still unordered goods, and that
                 # line has an owner: "they charged me for a bag i didnt want" is the refund of
                 # something nobody ordered, not the carrier-bag levy. "didnt ask" stays out, so
                 # "charged me for a bag i didnt ask for" is still this card's own last line.
                 "didnt want", "didn't want", "did not want", "didnt need",
                 "not ordered", "didnt order", "did not order"),
          # a plastic bag a loaf came in is not a carrier bag to pay for: "why does bread go
          # mouldy in a plastic bag" was told the 10p charge and the bag for life.
          guard=_the_bag_is_not_packaging),
    entry("complain-about-a-shop",
          (("complain about a shop", "complaint about a shop", "complain about a store",
            "complain to a shop", "complain to the shop", "complain about a purchase",
            "complain about the service", "bad service", "rude staff", "complaint about",
            "complain about a company", "escalate a complaint", "ombudsman", "small claims",
            "trading standards", "resolver", "complain", "complains", "complained", "complaint",
            "complaints"),
           ("how", "how do i", "shop", "store", "retailer", "company", "where", "next",
            "still not", "nothing happened", "no reply", "ignored", "refund", "money back")),
          "Complain to the shop first, in writing, and keep it to facts: what you bought, when, what "
          "went wrong, what you want and by when. Use email or the online form rather than the phone "
          "so there is a record, and give them 14 days. If they do not fix it, escalate inside the "
          "company - ask for the complaints procedure and the name of the person dealing with it - "
          "then go outside: Citizens Advice or Trading Standards for a legal point, the relevant "
          "ombudsman for a service, and the small claims track for money you are owed. Card payment "
          "is your spare lever: a claim under section 75 over 100 pounds, or a chargeback under it.",
          avoid=("landlord", "council", "council tax", "nhs", "hospital", "dentist", "school",
                 # "how do i complaint about a doctor" was told to complain to the shop: the
                 # NHS complaints entry is the one that owns a doctor, a GP and a surgery
                 "doctor", "doctors", "gp", "surgery", "nurse", "clinic", "consultant",
                 "midwife", "treatment", "care home", "care homes",
                 # A builder, a plumber or a decorator is not a shop, and "what you bought" is
                 # the wrong frame for one: "how do i complain about a builder" was answered with
                 # "complain to the shop first" while main's Citizens Advice line was the answer.
                 "builder", "builders", "tradesman", "tradesmen", "plumber", "plumbing",
                 "electrician", "decorator", "painter", "contractor", "rogue trader",
                 "teacher", "boss", "employer", "bank", "energy", "broadband", "mobile",
                 # a complaint about a manager or a colleague is a work complaint, not a shop
                 # one: "how do i raise a complaint about my manager" was told to complain to
                 # the shop first. "boss" and "employer" were already here; "manager" is the
                 # word people actually use.
                 "manager", "managers", "management", "colleague", "colleagues", "coworker",
                 "co-worker", "hr",
                 # an insurer is not a shop either: "how do i write a letter of complaint to my
                 # insurer" was told what to say about "what you bought"
                 "insurer", "insurers", "insurance", "policy", "claim", "claims",
                 "flight", "airline", "train", "hotel", "delivery", "parcel", "neighbour",
                 "neighbor", "noise", "my ex", "family", "restaurant", "takeaway", "cafe",
                 "coffee shop", "pizza", "meal", "my order", "food order",
                 "wrong order", "courier")),
    # --- the receipt you have not kept, and the refund you are waiting for -----
    # "i lost the receipt can i still return it" was answered; "can i take something back without a
    # receipt" was not, so the question is keyed on the framing as well as the word.
    entry("return-without-receipt",
          (("receipt", "receipts", "proof of purchase", "no receipt", "without a receipt",
            "gift receipt", "lost the receipt", "lost my receipt", "bank statement",
            "card statement"),
           ("return", "returns", "returning", "refund", "refunds", "exchange", "back",
            "take it back", "take back", "without", "lost", "need", "still",
            # the slip itself, kept or not: "do i need to keep the receipt". Only the
            # "need to keep" shape: "should i keep my receipts" and "how long should i keep
            # receipts" are the record-keeping card's, as they were before this change.
            "need to keep")),
          "You do not need the paper slip. Proof of purchase can be a bank or card statement showing "
          "the payment, an order confirmation email, a photo of the receipt or a gift receipt, and a "
          "shop that can see the purchase on its own system cannot insist on the paper. For anything "
          "faulty your claim is against the shop, not the maker: a full refund within 30 days, then "
          "repair or replacement, and in England, Wales and Northern Ireland up to six years to "
          "claim (five in Scotland) - a statement from your bank proves it just as well. If you are "
          "returning something because you changed your mind, there is no such right in a shop at "
          "all, so you are on their returns policy; ask the manager politely what proof they will "
          "accept, and if the goods were faulty and they still refuse, say you are going to Citizens "
          "Advice and put the claim in writing.",
          # a tax return, an expense claim and a read receipt are not this question
          avoid=("read receipt", "read receipts", "blue tick", "blue ticks", "delivery",
                 "parcel", "courier", "wan", "rent", "landlord", "tenant", "tenancy"),
          guard=_not_a_length,
          # "refund" in money.py is the rights answer and also keys "get"/"how do i"; a line that
          # says receipt is this question, so it wins the tie.
          bias=1),
    # "how do i get a duplicate receipt" was the employer-expenses policy card ("check the policy
    # before you spend") and "can i get a receipt emailed to me" was the newsletter unsubscribe.
    # A person asking for a copy wants to know the shop can produce one and what proves the
    # purchase in the meantime; neither of those cards says either thing.
    entry("a-copy-of-the-receipt",
          (("receipt", "receipts", "till receipt", "proof of purchase", "vat receipt",
            "bank statement", "card statement"),
           ("copy", "duplicate", "replacement", "another", "reprint", "print", "printed",
            "emailed", "email", "didnt give", "didn't give", "never gave", "not given",
            "no receipt", "ask for", "asked for", "can i get", "how do i get", "cash")),
          "Any shop can print or email another copy, because it can find the sale from the date, "
          "the time on the till roll and the last four digits of your card, so ask at the till "
          "and say roughly when you paid. If it cannot, a card or bank statement showing the "
          "payment is proof of purchase for a return, and a photo of the paper slip in your phone "
          "covers most warranties and expenses. Ask for a VAT receipt when you pay if you need to "
          "reclaim the VAT, since an ordinary till receipt often has no VAT number on it.",
          # what a missing receipt means for a return is return-without-receipt's question, and
          # keeping receipts for tax or for an employer's expenses is the policy card's
          avoid=("tax return", "self assessment", "hmrc", "expenses", "expense", "employer",
                 "keep", "keeping", "how long", "read receipt", "delivery", "parcel", "courier",
                 # a charity's receipt is Gift Aid's, not the shop's
                 "donation", "donations", "charity", "gift aid",
                 # a rent receipt is the tenancy's: the landlord gives it, not a till
                 "rent", "landlord", "tenant", "tenancy"),
          bias=1),
    entry("refund-how-long",
          (("refund", "refunds", "refunded", "money back", "returns money"),
           ("how long", "long", "when", "how many days", "days", "waiting", "take", "takes",
            "not had", "still", "not received", "chase", "chasing")),
          "Usually three to five working days on a card, and up to 14 days is still normal for "
          "online returns once the shop has the item back. Cash comes back at the till straight "
          "away, PayPal is often a day or two, and a card refund can take a full statement period to "
          "show because the bank holds it after the shop has paid it. If nothing has appeared after "
          "14 days, send the shop a short written request with your order number and the date you "
          "returned it, then take it to your card provider, who can raise a chargeback.",
          # what a refund is for (faulty, sale, a holiday) is another entry's question
          avoid=("faulty", "broken", "sale", "flight", "airline", "train", "hotel", "holiday",
                 "deposit", "rent", "landlord", "council", "tax", "ticket", "concert", "course",
                 "how do i get", "entitled", "can i get"),
          bias=1),
]

# "how do i pick a good olive oil" was a hedge: it is a choosing question, which is this
# domain's job, and the answer is a short list of things that are on the label.
ENTRIES.append(entry(
    "olive-oil-pick",
    (("olive oil", "olive oils", "extra virgin", "extra virgin olive oil", "evoo"),
     ("pick", "choose", "choosing", "buy", "buying", "best", "good", "which", "worth",
      "supermarket", "brand", "bottle", "tin", "cheap", "expensive", "difference", "use",
      "cooking", "kitchen")),
    "Look for \"extra virgin\" and a harvest date, not a best-before: oil is a fruit juice and it "
    "fades, so the newest pressing tastes best. A dark glass bottle or a tin keeps it that way, "
    "and a peppery catch at the back of your throat means the good bitter polyphenols are still "
    "there. Spend on the bottle you use raw - dressing, bread, a finished dish - and use a cheaper "
    "olive oil or a plain oil for roasting and frying. \"Light\" on the label means light in taste, "
    "not in calories.",
    # an oil that is not for the kitchen, and a tree to grow, are not this question
    #
    # A bottle question can also be a baking one: "can i use olive oil in a cake" and "can i use
    # olive oil instead of butter in a cake" are about what the oil does in the tin, and the
    # cooking rows answer those (the baking row, and the swap table for the "instead of" shape).
    # Without this the bottle advice took both, and the rarity of "olive oil" once a second row
    # keyed it was enough to take the swap line from the swap table.
    avoid=("car", "cars", "engine", "motorbike", "bike", "hair", "skin", "essential oil",
           "olive tree", "grow", "fryer", "deep fat", "chip pan", "paint", "lamp",
           "cake", "cakes", "sponge", "muffin", "muffins", "loaf", "loaves", "brownies",
           "brownie", "traybake", "tray bake", "carrot cake", "chocolate cake", "banana bread",
           "pastry", "shortbread", "biscuits", "cookies",
           # "is olive oil good for you" is the diet verdict in nutrition.py, and this row's ask
           # already held "good", so the bottle advice answered a question about health.
           "good for you", "good for me", "good for us", "bad for you", "bad for me", "healthy",
           "unhealthy", "fattening", "calorie", "calories", "cholesterol", "heart",
           # ...and whether a bottle is any good in a hot pan is the cooking-oil row's line:
           # "can i use olive oil for frying" is a pan question, not a shopping one
           "fry", "fries", "frying", "deep fry", "roasting", "roast potatoes"),
    ask=("pick", "choose", "choosing", "buy", "buying", "best", "good", "which", "worth",
         "supermarket", "brand", "difference", "use", "cooking")))

# "what can i give someone who is moving house" was the six-week moving plan, because every gift
# row in this file keys a person ("friend", "colleague", "mum") or an age and the line names
# neither. A house move is the gift question people actually ask, so it is its own row: the words
# are the move, and the answer is the first night rather than another candle.
ENTRIES.append(entry(
    "gift-house-move",
    (("gift", "gifts", "present", "presents", "what should i get", "what can i get",
      "what do i get", "what to get", "what should i buy", "what can i buy", "what to buy",
      "what can i give", "what should i give", "what to give", "what do i give",
      "what should i bring", "what to bring", "what can i bring", "what do you get",
      "what do you buy", "what do you give", "housewarming present", "housewarming gift",
      "ideas", "idea"),
     ("moving house", "moving home", "moving in", "moving into", "just moved", "moved house",
      "moved in", "new house", "new flat", "new home", "first home", "first flat",
      "housewarming", "house warming", "moving away", "bought a house", "got the keys",
      "new place", "new apartment")),
    ("Buy for the first night, not for the shelves: a takeaway voucher for the evening the boxes "
     "are still out, a box with loo roll, tea, milk, mugs, bin bags, a corkscrew and a phone "
     "charger, or a hot meal you turn up with. A plant, a good bottle or a decent set of tea "
     "towels all last longer than another candle, and a voucher for a hardware shop is the "
     "unromantic one people are pleased about. Ask first whether they want things or help: an "
     "afternoon of unpacking and a trip to the tip is often the present."),
    # the gift has to be said, and it has to be for somebody else: "what should i get for my new
    # flat" and "what do i need to do when i move house" are the move and the plan, not a present
    ask=("gift", "gifts", "present", "presents", "get", "buy", "give", "bring", "take round",
         "ideas", "idea"),
    # "we are moving house in a month" / "i have no idea where to start" is the move plan's
    # question, and "no idea" was the ask word this row keys ("idea"), so the gift card answered
    # a person asking what to do first about their own move. The not-knowing is the plan's, not a
    # present's, however the line words it.
    avoid=LOSS + CRISIS + ("where to start", "where do i start", "where do we start",
                           "where should i start", "where to begin", "where do i begin",
                           "no idea where to start", "dont know where to start",
                           "don't know where to start", "not sure where to start",
                           "my new flat", "my new house", "my new place", "our new house",
                           "our new flat", "my first flat", "my first house", "im moving",
                           "i am moving", "were moving", "we are moving", "i move", "we move",
                           "removals", "van hire", "packing", "council tax", "utilities",
                           "school", "doctor", "deposit", "landlord", "mortgage",
                           "hire a van", "man and van"),
    bias=2))

# --- choosing the things a house is full of, where the label decides it ----------------------
# "what should i look for in a duvet", "how do i pick a good pillow", "how do i choose a kettle",
# "how do i pick a good suitcase", "how do i choose a new sofa" and "how do i choose a coffee"
# were all a hedge on main, and the pillow one was worse than that: it got the card about washing
# a duvet in a big machine, because "pillow" is in that row's key and nothing answered the
# choosing question. Each row here is a thing, its label or its build, and the few numbers that
# decide it. The ask words are the choosing words the rest of the file uses, never a bare
# "how do i", so a washing, mending or using question stays with its own row.
_CHOOSE_ASK = ("pick", "picking", "choose", "choosing", "choice", "buy", "buying", "bought",
               "best", "good", "decent", "which", "what should i look for", "look for",
               "look out for", "worth", "spend", "budget", "recommend", "recommendation",
               "what to get", "which to get", "what should i get", "need a", "need some",
               "want a", "size", "much", "price", "cost", "cheap", "expensive", "difference",
               # A comparison of two of the same thing is the choosing question, not a
               # difference question: "is a 1 litre kettle better" was a search hedge beside a
               # row that answers "which kettle should i buy", and "is a down duvet better" /
               # "is a cheap mattress worse" were the same gap for every other object here.
               # The difference rows key two *different* things ("a duvet and a quilt"), so a
               # bare "better" beside one object is not theirs.
               "better", "worse", "bigger", "smaller", "cheaper", "dearer")

ENTRIES.append(entry(
    "duvet-choose",
    (("duvet", "duvets", "quilt", "quilts", "continental quilt", "tog"),
     _CHOOSE_ASK),
    "Go by tog: 4.5 for summer, 9 to 10.5 for spring and autumn, 13.5 for winter, or one 10.5 "
    "all year with a 4.5 on top in January. Match the size to the bed - single 135x200cm, double "
    "200x200, king 225x220, super king 260x220 - because a duvet smaller than the bed leaves a "
    "cold edge. Down and feather are warmest for the weight, wool breathes and handles damp best, "
    "and hollowfibre is the cheap washable one; a synthetic duvet goes in a 9kg drum at home, while "
    "down wants a launderette and a tumble dryer with dryer balls to bring the loft back.",
    # a duvet that needs washing, drying, mending or storing is another row's line, and so is the
    # cover you put on it
    avoid=("wash", "washing", "washed", "clean", "cleaning", "dry clean", "dry clean only",
           "dryer", "tumble", "machine", "stain", "stains", "smell", "smells", "smelly",
           "store", "storing", "storage", "put away", "pack away", "summer storage",
           "cover", "covers", "coverless", "sheet", "sheets", "bedding set", "mend", "repair",
           "torn", "rip", "hole", "allergy", "allergies", "asthma", "eczema", "dust mite"),
    bias=2))

ENTRIES.append(entry(
    "pillow-choose",
    (("pillow", "pillows", "pillowcase"),
     _CHOOSE_ASK),
    "Match the pillow to how you sleep: on your side you want a firm, high one that fills the gap "
    "between shoulder and ear, on your back a medium one, and on your front a soft, thin one so "
    "your neck is not cranked up. A pillow that folds in half and stays folded is worn out - most "
    "last two to three years, not ten. Memory foam and latex hold their shape, hollowfibre is cheap "
    "and washable at 60C, and down is soft but needs plumping; a washable protector keeps whichever "
    "you pick clean.",
    # washing, drying, a stain and a sore neck are separate questions, and a pillowcase to sew is
    # not a pillow to buy
    avoid=("wash", "washing", "washed", "clean", "cleaning", "dry clean", "dryer", "tumble",
           "machine", "stain", "stains", "smell", "smells", "smelly", "yellow", "mould", "mold",
           "neck", "stiff neck", "sore", "ache", "aches", "aching", "pain", "hurt", "hurts",
           "sciatica", "migraine", "headache", "sew", "sewing", "make", "making", "pattern",
           "toddler", "baby", "cot", "cushion", "cushions", "throw"),
    bias=2))

ENTRIES.append(entry(
    "kettle-choose",
    (("kettle", "kettles"),
     # "is a 1 litre kettle better" is this row's question with the comparison in it: the
     # comparison words are in _CHOOSE_ASK now, so every object with a choosing row answers
     # "is a bigger one better" / "is a cheap one worse" the same way.
     _CHOOSE_ASK),
    "Get a 3kW one for speed and 1.7 litres for a family, or a 1 litre one if it is mostly you - "
    "a small kettle boiled often costs less than a big one boiled for two cups. A concealed "
    "element and a wide lid make descaling easy, a water-level window on both sides saves "
    "guessing, and temperature settings are worth it only if you make green tea or filter coffee. "
    "Decide stainless steel or glass by looks, then check the minimum fill line: a kettle that "
    "needs half a litre before it will switch on wastes water and power.",
    # a kettle that is broken, limescaled, noisy or being descaled is a fix, not a purchase
    avoid=("descale", "descaling", "limescale", "scale", "fur", "furred", "broken", "not working",
           "stopped", "faulty",
           # "my kettle has gone" and "the element has gone" are the repair row's question, not
           # how to choose one: without these the buying guide answered a kettle that had died.
           "gone", "went", "knackered", "on the blink",
           "leak", "leaks", "leaking", "switch", "element", "noisy", "rattle",
           "boil", "boiling", "boils", "how long", "vinegar", "citric", "bicarbonate",
           "tea", "teapot", "coffee", "cup of tea", "electricity", "energy"),
    bias=2))

ENTRIES.append(entry(
    "suitcase-choose",
    (("suitcase", "suitcases", "cabin bag", "cabin case", "cabin luggage", "hand luggage",
      "carry on", "carry-on", "holdall", "luggage", "case"),
     _CHOOSE_ASK),
    "Start with the airline, because cabin sizes differ: a 55x40x20cm case fits most paid cabin "
    "allowances, while the free underseat bag is around 40x20x25cm, and a bag outside the airline's "
    "own limit is the one thing that gets charged at the gate. Four wheels and a hard "
    "polycarbonate shell survive the hold better, soft bags give and squash into a car; either way "
    "check the empty weight against a 23kg allowance and buy from a brand that covers wheels and "
    "handles for years rather than months. A TSA lock matters only for the US. For a week "
    "away, 40 to 45 litres of cabin case is enough if you pack light and wash a shirt.",
    # a case that is lost, damaged, delayed, packed or being unpacked is another question, and the
    # airline rows own the missing-bag claim
    avoid=("lost", "missing", "delayed", "damaged", "broken", "wheel broke", "zip", "zips",
           "lock stuck", "stolen", "claim", "compensation", "airline", "flight", "pack", "packing",
           "packed", "unpack", "unpacking", "what to take", "what to pack", "holiday packing",
           "storage", "store", "handbag", "handbag", "briefcase", "laptop bag",
           # a phone, a tablet and a pair of glasses are named "case" too, and the suitcase row
           # answered "which phone case should i buy" with cabin sizes
           "phone", "iphone", "mobile", "tablet", "ipad", "laptop", "glasses", "spectacles",
           "hearing aid", "airpods", "earbuds", "camera", "console", "switch case"),
    bias=2))

ENTRIES.append(entry(
    "sofa-choose",
    (("sofa", "sofas", "settee", "couch", "three piece suite", "armchair"),
     _CHOOSE_ASK),
    "Measure the room, the door and the stairs before you fall for one, and keep 60cm of walking "
    "space past it. Then look at the build: a hardwood or beech frame screwed and glued, not "
    "stapled chipboard, and seat cushions of 30 to 35kg foam with a fibre wrap, or feather if you "
    "will plump them daily. Sit on it for ten minutes rather than three, and check the fabric's rub "
    "count - 25,000 for adults, 30,000 and up for children and pets. Made-to-order sofas take six "
    "to twelve weeks, so ask about the return policy before you pay.",
    # a sofa that is dirty, smelly, sagging or being moved is a cleaning, repair or moving job
    avoid=("clean", "cleaning", "washer", "wash", "stain", "stains", "smell", "smells", "pet hair",
           "sag", "sagging", "saggy", "squeak", "squeaks", "broken", "repair", "re-upholster",
           "reupholster", "moving house", "move a sofa", "get it upstairs", "cover", "covers",
           "throw", "throws", "cushion", "cushions", "leather", "scratched"),
    bias=2))

ENTRIES.append(entry(
    "coffee-to-buy",
    (("coffee", "coffees", "coffee beans", "ground coffee", "instant coffee", "filter coffee"),
     ("pick", "picking", "choose", "choosing", "buy", "buying", "best", "good", "decent",
      "which", "what should i look for", "look for", "worth", "roast", "bean", "beans",
      "brand", "supermarket", "grind", "ground", "roasted", "fresh", "strength", "strong")),
    "Look for a roast date, not a best-before: beans are best from a few days to about six weeks "
    "after roasting, and supermarket bags with only a best-before are usually months old. Buy "
    "whole bean and grind per brew - fine for espresso, medium for a filter machine, coarse for a "
    "cafetiere - or ask the shop to grind it for the pot you use. A medium roast suits most "
    "brewing, and about 60g of coffee to a litre of water is the strength to start from. Keep the "
    "bag sealed and in a cupboard, not the fridge.",
    # a cup that is made, brewed, stored or ordered in a cafe is another row's question, and so is
    # whether coffee is good for you
    avoid=("make", "making", "brew", "brewing", "brewed", "cup", "cups", "mug", "machine",
           "machine descale", "descale", "caffeine", "sleep", "anxiety", "good for you",
           "bad for you", "healthy", "pregnant", "pregnancy", "withdraw", "withdrawal", "stop",
           "give up", "quit", "cafe", "cafes", "barista", "shop", "starbucks", "costa",
           "stain", "stains", "grinder", "frother",
           # "which milk is best for coffee" is a question about the milk, and this row
           # answered it with the bag of beans to buy: the milk asked about is not the coffee.
           "milk", "milks", "dairy"),
    bias=2))

ENTRIES.append(entry(
    "rug-choose",
    (("rug", "rugs", "carpet rug", "runner", "runners"),
     _CHOOSE_ASK),
    "Go bigger than feels right: in a living room the rug should reach under the front legs of the "
    "sofa, so about 160x230cm for a small room and 200x290cm behind a three-seater, and a "
    "bedroom rug wants to run at least 60cm past each side of the bed. Wool wears and cleans "
    "better than polyester and does not flatten as fast; a thick underlay makes a cheap rug feel "
    "expensive and stops it creeping. Take the size you are considering and tape it out on the "
    "floor before you buy, and check it can be washed or spot-cleaned.",
    # a rug that is dirty, stained, slipping, curled or being cleaned is another question
    avoid=("clean", "cleaning", "wash", "washing", "stain", "stains", "smell", "smells", "moth",
           "moths", "slipping", "slips", "slides", "curl", "curling", "creases", "shed", "shedding",
           "hoover", "vacuum", "flat", "flattened", "repair", "fringe", "fringes", "lay", "laying"),
    bias=2))

ENTRIES.append(entry(
    "curtains-choose",
    (("curtain", "curtains", "blind", "blinds", "drapes", "curtain rail", "curtain pole"),
     _CHOOSE_ASK),
    "Buy one and a half to twice the window width in fabric, or the curtains hang flat and let "
    "light round the edges, and measure the drop from the pole or track to where you want them to "
    "end - just below the sill, or to the floor for a longer look. A lined curtain keeps heat in "
    "and light out far better than an unlined one, and a thermal lining is worth it in a bedroom. "
    "Eyelet headings slide easily on a pole, pencil pleat gives a fuller look on a track; for "
    "anything over 2m wide, two panels rather than one.",
    # hanging, hemming, washing and mending curtains are separate questions
    avoid=("hang", "hanging", "hem", "hemming", "shorten", "lengthen", "sew", "sewing", "iron",
           "ironing", "wash", "washing", "clean", "cleaning", "dry clean", "stain", "stains",
           "mould", "mold", "damp", "black mould", "repair", "broken", "cord", "track broken",
           "child safety", "blind cord"),
    bias=2))

ENTRIES.append(entry(
    "toaster-choose",
    (("toaster", "toasters"),
     _CHOOSE_ASK),
    "Two slots do for one or two people and four for a family, and the slot width matters more "
    "than the wattage: look for wide slots if you toast bagels, crumpets or thick-cut bread. "
    "Variable browning plus a cancel button is the pair that stops you scraping burnt toast, and a "
    "defrost setting is worth having if you freeze bread. A removable crumb tray and a cord that "
    "tucks away are the two things you will notice every week; anything over about 1,500W toasts "
    "no better than 900W.",
    # a toaster that is broken, smoking, not popping up or being cleaned is a fix
    avoid=("broken", "not working", "stopped", "faulty", "smoking", "smoke", "burnt", "burning",
           "stuck", "wont pop", "won't pop", "pop up", "clean", "cleaning", "crumbs", "crumb tray",
           "repair", "fuse", "element", "sandwich", "toastie", "air fryer", "grill"),
    bias=2))



# The kitchen machines the worth-it table above did not name, kept in their own table so the rows
# and the cue list that reach them are one change in one place. Every one of these came back "I
# don't know enough to answer that honestly", which is the worst answer to a buying question
# because the person is asking for a decision. Two of them were worse than a shrug, because a
# longer phrase carries a shorter name inside it: "is a soda stream worth it" reached the
# streaming subscriptions ("cancel when the series ends") and "is a vacuum sealer worth it" the
# vacuum cleaner and its three-uses-a-week rule of thumb.
KITCHEN_MACHINE_VALUE = (
    (("rice cooker", "rice cookers"),
     "A rice cooker is worth it if rice is a daily thing: it times it, keeps it warm for an hour and "
     "leaves the hob free, and a 40 pound one cooks as well as a 200 pound one. Skip it if you eat "
     "rice twice a month, since a pan with a lid is the same rice in 12 minutes."),
    (("soup maker", "soup makers"),
     "A soup maker is worth it if you make soup most weeks and want one jug and no pan to watch: it "
     "cooks and blends in about 20 minutes. Skip it if you like soup with chunks in it, or cook for "
     "four, because most jugs hold 1.6 litres and the blade takes everything smooth."),
    (("sous vide", "sous vide stick", "sous vide machine", "sous vide cooker"),
     "Sous vide is worth it if you cook steak, chicken breast or eggs to a temperature and do not "
     "mind waiting: a 60 pound stick in a lidded pan holds the water steady for an hour or more, and "
     "nothing overcooks. Skip it if dinner has to be on the table in 20 minutes, where a thermometer "
     "and a hot pan get most of the way."),
    (("dehydrator", "dehydrators", "food dehydrator"),
     "A dehydrator is worth it if you dry things often: herbs, apple rings, jerky or vegetables for "
     "stock, in 4 to 12 hours at 40 to 60C with no oven on. Skip it if that is a twice-a-year job, "
     "since an oven on its lowest setting with the door ajar dries a tray at a time."),
    (("juicer", "juicers"),
     "A juicer is worth it only if you drink juice most mornings: it separates the pulp in seconds, "
     "and cleaning the mesh takes five minutes every time. Skip it if you would rather eat the "
     "fruit, which keeps the fibre the juice leaves behind."),
    (("yogurt maker", "yoghurt maker", "yogurt makers"),
     "A yogurt maker is worth it if you get through a tub a week: a litre of milk makes a litre of "
     "yogurt for about 60p, and it holds the warmth steady for 8 to 12 hours. Skip it if you eat "
     "yogurt now and then, since a flask and a warm cupboard do the same job."),
    (("ice cream maker", "ice cream makers"),
     "An ice cream maker is worth it if you make it more than a few times a summer: the bowl has to "
     "be frozen overnight, so it is never a last-minute thing, and a 40 pound one with a pre-frozen "
     "bowl is fine. Skip it if you would use it twice, where a loaf tin and a fork every half hour "
     "gets close."),
    (("contact grill", "panini press", "sandwich press", "george foreman", "health grill"),
     "A contact grill is worth it if you toast sandwiches or cook chops and vegetables for one or "
     "two: it heats both sides at once and the fat runs off. Skip it if you cook for four, since the "
     "plates take two sandwiches at a time, and skip it if you have a frying pan and a lid."),
    (("electric steamer", "steam cooker", "food steamer"),
     "An electric steamer is worth it if you steam vegetables, dumplings or fish often and like "
     "setting a timer and walking away: the tiers hold a whole dinner over one ring. Skip it if a pan "
     "with a colander and a lid already does it, which for most people it does."),
    (("electric whisk", "hand whisk", "hand mixer", "electric hand whisk"),
     "An electric hand whisk is worth it for anyone who creams butter or whips cream even a few times "
     "a month: about 15 pounds, a minute instead of ten with a fork, and it lives in a drawer. Skip "
     "it only if you bake twice a year."),
    (("mandoline", "mandolines", "mandoline slicer"),
     "A mandoline is worth it if you slice a lot of vegetables thin and even - gratins, slaw, pickles "
     "- and you will use the hand guard every single time. Skip it if you cook for one: a sharp knife "
     "is safer and nearly as quick."),
    (("spiralizer", "spiralizers", "spiraliser"),
     "A spiralizer is worth it only if you really eat courgette or carrot noodles: a 10 pound "
     "hand-held one does it in a minute and the counter-top ones add nothing. Skip it if you would "
     "use it once, where a julienne peeler does the same job and fits in a drawer."),
    (("soda stream", "sodastream", "soda maker", "sparkling water maker"),
     "A soda maker is worth it if you drink sparkling water every day: a gas cylinder makes about 60 "
     "litres for 10 pounds to swap, so it pays for itself in a few months and saves carrying bottles. "
     "Skip it if you drink it now and then, or would mostly use the flavour syrups, which cost more "
     "than supermarket bottles."),
    (("vacuum sealer", "vacuum sealers", "food sealer", "food sealers"),
     "A vacuum sealer is worth it if you buy meat in bulk or freeze portions: it stops freezer burn "
     "and the bags can be boiled, so a batch of chilli reheats in the bag. Skip it if you freeze "
     "little, since a freezer bag with the air pressed out does most of it."),
)

# The worth-it entry above lacked two things for these machines - a row, and their names in its
# cue list - and an entry that matches a line and then finds no row hands it on. Both are added
# here, beside the rows, so a machine named in this block is a machine with an answer.
APPLIANCE_VALUE = APPLIANCE_VALUE + KITCHEN_MACHINE_VALUE
KITCHEN_MACHINE_NAMES = tuple(name for names, _trade in KITCHEN_MACHINE_VALUE for name in names)
for _worth_it_entry in ENTRIES:
    if _worth_it_entry.id == "appliance-worth":
        _worth_it_entry.key = ((_worth_it_entry.key[0] + KITCHEN_MACHINE_NAMES,)
                               + tuple(_worth_it_entry.key[1:]))

ENTRIES.append(entry(
    "sleeping-bag-choose",
    (("sleeping bag", "sleeping bags", "camping bag", "down bag", "mummy bag"),
     _CHOOSE_ASK),
    "Ignore the \"extreme\" number and look at the comfort rating: a 2 or 3 season bag rated to "
    "about 0C comfort covers British camping from spring to autumn, and a 3 season one is the "
    "usual first buy. Down is lighter and packs smaller but useless once wet, synthetic keeps some "
    "warmth damp and is cheaper and washable, and a mummy shape is warmer for its weight than a "
    "rectangular one. The mat under you decides how warm you sleep as much as the bag does, so "
    "spend there too.",
    # a bag that is washed, damp, smelly or stored is another question, and so is sleeping badly
    avoid=("wash", "washing", "clean", "cleaning", "damp", "wet", "smell", "smells", "smelly",
           "mould", "mold", "store", "storing", "storage", "pack", "packing", "stuff sack",
           "zip", "zips", "repair", "torn", "cold at night", "cant sleep", "can't sleep",
           "sleeping badly", "insomnia", "tent", "mat", "airbed", "camping site"),
    bias=2))


# "is it cheaper to buy second hand" was the honest shrug. It is a choosing question with a
# number in it, so it belongs here: what keeps its value, what never to buy used whatever the
# price, and what a person's rights are when it goes wrong.
ENTRIES.append(entry(
    "second-hand-worth-it",
    (("second hand", "secondhand", "second-hand", "pre owned", "preowned", "pre-owned",
      "used", "buying used", "buy used", "charity shop", "car boot", "facebook marketplace",
      "gumtree", "vinted", "ebay", "refurbished", "refurb"),
     ("cheaper", "cheap", "save", "saving", "worse", "worth", "worth it",
      # "should i" on its own was enough to take a follow-up: the row keys on "used", the
      # running answer above says "half of what you used to do", and "how often should i go
      # out" in a running chat came back with this row's buyer-beware sentence. The ask has to
      # carry the buying with it.
      "should i buy", "should i get", "should we buy", "should we get",
      "good idea", "buy", "buying", "or new", "vs new", "instead of new",
      "money", "value", "second hand", "used")),
    "Yes, usually by a third to a half, and the older the thing gets the better the saving: "
    "furniture, bikes, tools, a pram, kids' clothes and kitchen kit lose most of their value in "
    "the first year and then almost nothing. Buy new the things that wear unseen or are used "
    "against your body - a mattress, running shoes, a bike helmet, anything with a safety job "
    "(a car seat, a life jacket, a smoke alarm) - and buy new where a warranty is what you are "
    "really paying for, like a laptop or a washing machine. Check a used phone or laptop's "
    "battery health, ask for the age of a washing machine's drum, and never pay before you see "
    "it. From a shop, second-hand goods carry the same rights as new ones: 30 days to reject it, "
    "then repair or replacement; from a private seller it is buyer beware unless the advert lied.",
    # a car, a bike and a house each have their own row with their own checklist, and the
    # selling side is how to get rid of what you have, not how to buy
    avoid=("car", "cars", "van", "vans", "motorbike", "motorbikes", "vehicle", "mileage",
           "mot", "v5", "bike", "bikes", "bicycle", "cycle", "house", "flat", "mortgage",
           # a phone, a laptop and a tablet already have a refurbished row with the grade, the
           # warranty and the battery check in it, and "is a refurbished phone worth it" had
           # that answer before this row existed: the general answer must not take it
           "phone", "phones", "mobile", "iphone", "android", "laptop", "laptops", "tablet",
           "tablets", "computer", "computer", "console", "games console",
           "sell", "selling", "sold", "sale", "declare", "tax", "to the taxman",
           # A piece of furniture has a card of its own with the checks written down ("check for
           # woodworm holes, sagging cushions and smoke smell"): "is buying used furniture worth
           # it" and "what should i look for when buying a used sofa" both had it, and the
           # general answer does not answer either. The mattress is not here on purpose - main
           # has nothing for "is a used mattress worth it", and this row does.
           "furniture", "sofa", "sofas", "couch", "couches", "settee", "armchair", "armchairs",
           "wardrobe", "wardrobes", "dresser", "sideboard", "sideboards", "bookshelf",
           "bookshelves", "bookcase", "bookcases", "bed frame", "table", "tables", "chairs",
           "cabinet", "cabinets", "chest of drawers",
           # an ask for the checks to make is that row's question, not the cheaper-vs-new one
           "look for", "what should i look for", "what to look for", "what should i check",
           "what to check", "check", "checks", "checking", "checked",
           # a safety question about a marketplace is not a price: "is gumtree safe to buy from"
           # was a punt before this row existed, and a confident "yes, by a third to a half" is
           # an answer to a different question.
           "safe", "safely", "scam", "scams", "scammer", "scammed", "trust", "trustworthy",
           "risky", "risk", "insurance",
           # a watch, a ring and anything collectible are the same case as furniture: the line
           # that begins the topic has a check-the-thing card behind it, and worse, answering
           # it here loses the topic for the follow-up - "is a second hand watch a good buy"
           # then "what should i check" came back with a ganglion cyst instead of the watch
           # checks. A multi-turn conversation must not get worse for one middle turn.
           "watch", "watches", "wristwatch", "clock", "clocks", "jewellery", "jewelry",
           "ring", "rings", "necklace", "bracelet", "earrings", "brooch", "antique",
           "antiques", "collectible", "collectibles", "vinyl", "record", "records",
           "book", "books", "novel", "novels"),
    ask=("cheaper", "worth", "should i", "buy", "buying", "save", "value")))
