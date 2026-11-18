"""What they have told you they spent, and what they ask about it afterwards.

People report money as it goes out - "i spent 300 on food this month", "i paid 80 for the
train", "40 on a takeaway" - and then ask the one question that needs the bot to have kept it:

    i spent 300 on food this month
    how much have i spent      before  I'm not sure about that one, sorry - I'd rather not guess.
                                      A quick search online will get you a solid answer.
                               now     You've told me 300 on food this month. Tell me the rest
                                       and I'll keep a tally.
    how much did i spend on food   before  a cooking tip about shopping with a list
                                   now     You told me 300 on food this month.

Nothing here writes to the store. Every line the person typed is in `memory["turns"]`, so the
tally is read from what they actually said: a spend the store did not file is still a spend they
reported, and a reading that only reads cannot file the wrong thing.

Guards, because a money word is everywhere:

* the person has to be the one spending ("i spent", "we paid", "it cost me"), so a price asked
  about in the world ("how much does a pint cost", "how much is a train to leeds") is left to
  the knowledge base.
* the amount has to be a number in the line, and the thing it went on is what follows "on" or
  "for" ("on food", "for the train"). A line with a number and no thing ("i spent 300") is
  still a spend and is counted, with nothing named.
* an ask is only the ask. "how much have i spent" and "what did i spend on food" are read; a
  line with a spend in it is a report, not a question about one.
"""
import re

# The spend itself: who paid, how much, and what it went on. The amount may carry a pound sign,
# the word "pounds" or "quid", or pence written as a decimal.
_MONEY = r"(\d{1,7}(?:\.\d{1,2})?)"
_CURRENCY = r"(?:\s*(?:pounds?|quid|p\b|gbp))?"
SPENT = re.compile(
    r"\b(?:i|we|he|she|they)(?:'ve|'s|'d)?\s+(?:have\s+|had\s+|already\s+)*"
    r"(?:spent|paid|forked out|shelled out)\s+"
    r"(?:about|around|nearly|almost|just|only|maybe|like|over|under|another)?\s*"
    r"£?\s*" + _MONEY + _CURRENCY + r"\s*(?:(?:on|for|in)\s+)?(.*)$", re.I)
# "it cost me 40", "that cost 12.50": the thing is whatever the chat was about, so nothing is
# named and the spend is still counted.
COST = re.compile(r"\b(?:it|that|this|the\s+[a-z]+)\s+cost\s+(?:me\s+)?(?:about\s+|around\s+|"
                  r"nearly\s+|just\s+|only\s+)?£?\s*" + _MONEY + _CURRENCY + r"\s*(.*)$", re.I)
# "40 on a takeaway" on its own, right after a question about money: the verb is left off, and the
# person is still reporting a spend.
BARE_ON = re.compile(r"^\s*(?:(?:and|then|also|so)\s+)*(?:another\s+)?£?\s*" + _MONEY +
                     _CURRENCY + r"\s+(?:on|for)\s+(.+)$", re.I)

# What is left of the thing: the time it happened is the line's business, not the thing's, and a
# tally reads better without it. "on food this month" is food.
_WHEN_TAIL = re.compile(
    r"\s*\b(?:this|last|next|the)\s+(?:morning|afternoon|evening|night|week|weekend|month|year)\b.*$"
    r"|\s*\b(?:today|yesterday|tonight|already|so far|altogether|in all|last night|"
    r"at the weekend|on saturday|on sunday|on monday|on tuesday|on wednesday|on thursday|"
    r"on friday)\b.*$", re.I)
# "i spent 50 on petrol too": the "too" is the line's, not the thing's.
_TAIL_OFF = re.compile(r"\s*\b(?:too|as well|also|again|though|now|anyway)\b\s*$", re.I)
_TRAILING = re.compile(r"[\s.,;:!?-]+$")

# The ask, in the words people type it: "how much have i spent", "what did we spend on food",
# "how much has that cost me", "what have i spent so far", "how much did i spend altogether".
#
# Only the money they have already spent, so only the first person and only the past: "how much
# do you spend on a new baby present" asks what such a present costs, and "how much do i spend on
# food a month" asks what a usual month comes to. Said back with a tally of what they have told
# the bot neither is answered, and the first of them lost the present-buying answer it had.
ASK = re.compile(
    r"\bhow\s+much\s+(?:have|has|did)\s+(?:i|we)\s+(?:spent|spend|pay|paid)\b"
    r"|\bwhat\s+(?:have|has|did)\s+(?:i|we)\s+spent\b"
    r"|\bhow\s+much\s+(?:has|did)\s+(?:it|that|this)\s+cost\b"
    r"|\bwhat\s+(?:have|did)\s+(?:i|we)\s+spend\b"
    r"|\bhow\s+much\s+(?:money\s+)?(?:have\s+i|did\s+i)\s+(?:spent|spend)\b", re.I)
# "how much did i spend on food": the ask names the thing, so only that thing is counted.
ON_A_THING = re.compile(r"\b(?:on|for)\s+([a-z][a-z' -]{1,30}?)"
                        r"(?:\s+(?:this|last|so far|altogether|in all)\b.*)?\s*[?.!]*\s*$", re.I)
# The words in an ask that are not the thing: "how much did i spend on food this month" asks
# about food, and "so far" is the ask talking about itself.
_ASK_FILLER = frozenset("""
so far altogether in all in total total now this month week year today all
""".split())


# The things people report money on, in the broader words an ask reaches for. "40 on a takeaway"
# is money on food; "how much did i spend on food" counts it, and "how much did i spend on petrol"
# does not. Only these families are shared, so the two never blur into "money on anything".
CATEGORIES = (
    ("food", ("food", "groceries", "grocery", "shopping", "supermarket", "takeaway", "takeaways",
              "restaurant", "eating out", "lunch", "dinner", "breakfast", "brunch", "coffee",
              "snack", "snacks", "meal", "meals", "pizza", "curry", "chinese", "milk", "bread",
              "veg", "fruit", "meat", "booze", "beer", "wine")),
    ("petrol", ("petrol", "fuel", "diesel", "petrol station", "gas")),
    ("travel", ("train", "trains", "bus", "buses", "travel", "transport", "taxi", "uber", "tube",
                "train fare", "flights", "flight", "coach", "parking")),
    ("bills", ("bills", "bill", "electric", "electricity", "water", "council tax", "rent",
               "mortgage", "broadband", "internet", "phone", "gas bill", "energy")),
    ("kids", ("kids", "children", "childcare", "school", "nursery", "childminder")),
)

def _amount(number):
    """The figure as the person typed it: 300, 12.50."""
    return (number or "").strip()


def _the_thing(rest):
    """The thing the money went on, in the words the person used, or ""."""
    rest = (rest or "").strip()
    if not rest:
        return ""
    rest = re.split(r"[,;.]", rest)[0]
    # "we spent 60 at the pub" is 60 on the pub, not "60 on at the pub": the place and the thing
    # are said with the same little word, and only one of them reads in a tally.
    rest = re.sub(r"^(?:at|in|on|for)\s+", "", rest, flags=re.I) if rest.lower().startswith(
        ("at ", "in ")) else rest
    rest = _WHEN_TAIL.sub("", rest)
    rest = _TAIL_OFF.sub("", rest)
    rest = _TRAILING.sub("", rest).strip()
    return rest if len(rest) > 1 else ""


# A line can report more than one spend: "i paid 80 for the train and 12.50 on lunch" is two.
# It is cut where a figure starts a new clause, so "40 on food and drink" stays one spend and
# keeps its whole thing.
_TWO_SPENDS = re.compile(r"(?=[,;]\s*(?:and\s+)?£?\d|\s+and\s+£?\d)", re.I)


# A bill said as a fact about itself rather than as a spend: "my rent is 780 a month", "the council
# tax is 150". The money goes out all the same, and an ask about that thing was answered with a
# denial over a line that had just given the figure: "my rent is 780 a month" then "what did i
# spend on rent" said "You haven't told me what you spent on rent."
#
# Only a thing the store has a family for counts, so a budget ("my budget is 300") and a thing
# bought ("my car is 5000") are not money that has gone out of anything.
_SAID_AS_A_COST = re.compile(
    r"\b(?:my|our|the)\s+([a-z][a-z' -]{1,24}?)\s+(?:is|are|comes? to|works out at)\s*"
    r"£?(\d[\d,]*(?:\.\d{1,2})?)\s*(k|p|pounds?|quid|gbp)?\b", re.I)
# A person is not a bill: "the kids are 6 and 9" is two ages, and the reader above took the six as
# money that went on kids, so a tally a turn later read "You had 90 and 6 on kids has gone, so 84
# is left." Nobody had spent anything. A figure with no money marker in it, on a thing that is one
# of the people in their life, is an age, and so are two figures in a row ("6 and 9").
_PEOPLE = frozenset("""
kid kids child children baby babies toddler boy boys girl girls lad lass son sons daughter
daughters twin twins nephew niece grandchild grandchildren grandson granddaughter mum mom
dad stepson stepdaughter
""".split())
_TWO_FIGURES = re.compile(r"^\s*(?:,|and|&|or)\s*\d{1,3}\b")


# The same bill said from the paying side: "i pay 95 a month for my phone", "we pay 1200 rent every
# month". The figure and the thing are both there, but said in the order people use when they are
# telling you what something costs them, and neither reader above saw it - "i pay 95 a month for my
# phone" then "how much is my phone bill" went to the phone-resale card. Only a thing the store has
# a family for counts, as above, so "i pay 30 a month for the gym" is not a bill.
_A_PERIOD = r"(?:a|an|per|each|every)\s+(?:month|week|fortnight|year)"
_PAY_FOR = re.compile(
    r"\b(?:i|we)\s+pay\s+(?:about|around|just|only|roughly|like\s+)?£?(\d[\d,]*(?:\.\d{1,2})?)"
    r"\s*(k|p|pounds?|quid|gbp)?\s+" + _A_PERIOD +
    r"\s+(?:for|on)\s+(?:my|our|the)?\s*([a-z][a-z' -]{1,24})", re.I)
# "i pay 1200 rent every month" puts the thing before the period, which is the other order people
# use, and the one the reader above has no place for.
_PAY_THING = re.compile(
    r"\b(?:i|we)\s+pay\s+(?:about|around|just|only|roughly|like\s+)?£?(\d[\d,]*(?:\.\d{1,2})?)"
    r"\s*(k|p|pounds?|quid|gbp)?\s+(?!a\s+|an\s+|the\s+|per\s+)([a-z][a-z' -]{2,24}?)\s+"
    + _A_PERIOD, re.I)


def _a_bill(text):
    """The money a line says a thing of theirs costs, or None."""
    for pattern, amount_group, thing_group, currency_group in (
            (_SAID_AS_A_COST, 2, 1, 3), (_PAY_FOR, 1, 3, 2), (_PAY_THING, 1, 3, 2)):
        match = pattern.search(text)
        if not match:
            continue
        thing = (match.group(thing_group) or "").strip(" .,")
        if not _family(thing):
            continue
        if not match.group(currency_group) and _an_age_not_a_bill(match, thing, pattern):
            continue
        return {"amount": _amount(match.group(amount_group)), "thing": thing}
    return None


def _an_age_not_a_bill(match, thing, pattern):
    """Whether a cost said as a fact is really somebody's age."""
    if pattern is not _SAID_AS_A_COST:
        return False
    if set(thing.lower().split()) & _PEOPLE:
        return True
    return bool(_TWO_FIGURES.match(match.string[match.end():] or ""))


def _one(text):
    """The spend one clause reports, or None."""
    match = SPENT.search(text)
    if match:
        return {"amount": _amount(match.group(1)), "thing": _the_thing(match.group(2))}
    match = COST.search(text)
    if match:
        return {"amount": _amount(match.group(1)), "thing": _the_thing(match.group(2))}
    match = BARE_ON.match(text)
    if match:
        return {"amount": _amount(match.group(1)), "thing": _the_thing(match.group(2))}
    return _a_bill(text)


# People type the pronoun without its apostrophe far more often than with it - "ive spent 40 on
# food", "weve got 20 till friday" - and every reader here was written against the apostrophe, so
# the most ordinary spelling of a spend was not a spend at all: "ive spent 40 on food" was answered
# "You haven't told me what you've spent yet", and "ive got 20 till friday" / "how much have i got
# left" got a search hedge where "i've got" got the sum. So the apostrophe is put back before any
# of the readers sees the line. Only the pronoun forms, which have no other reading: "id" is left
# alone because it is a card as often as it is "i'd".
_PLAIN = re.compile(r"\b(ive|weve|theyve|youve|hes|shes|im)\b", re.I)
_PLAIN_BACK = {"ive": "i've", "weve": "we've", "theyve": "they've", "youve": "you've",
               "hes": "he's", "shes": "she's", "im": "i'm"}


def _plain(text):
    """The line with the pronoun contractions spelled the way the readers expect."""
    return _PLAIN.sub(lambda m: _PLAIN_BACK[m.group(1).lower()], text)


def readings(line):
    """Every spend a line reports, in the order they were said."""
    text = _plain(" ".join(str(line or "").split()))
    if not text or "?" in text:
        return []
    found = []
    for clause in _TWO_SPENDS.split(text):
        spend = _one(clause)
        if spend:
            found.append(spend)
    return found


def reading(line):
    """The first spend a line reports, as {"amount": "300", "thing": "food"}, or None.

    Only the person's own money counts, and only where the amount is in the line.
    """
    found = readings(line)
    return found[0] if found else None


def the_lines(memory, text=None):
    """Every line the person has said this chat, oldest first, with `text` last if given."""
    lines = []
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for turn in turns if isinstance(turns, list) else ():
        said = str((turn or {}).get("user") or "") if isinstance(turn, dict) else ""
        if said.strip():
            lines.append(said)
    if text and (not lines or lines[-1] != text):
        lines.append(str(text))
    return lines


def the_spends(memory, text=None):
    """What they have said they spent, oldest first: [{"amount", "thing", "line"}]."""
    found = []
    for line in the_lines(memory, text):
        for spend in readings(line):
            spend["line"] = line
            found.append(spend)
    return found


# The other asking of the same thing: the present tense. "how much do i spend on water" asks what
# water usually costs, which is the knowledge base's question - until the chat already holds a bill
# for water, and then the person means the figure they gave a line or two back:
#
#   my water is 40 a month / how much do i spend on water
#     now   You told me 40 on water.
#
# Reading it only where a bill for that very thing is on record keeps the habit question where it
# was, so "how much do i spend on food a month" with no bill behind it is still not the bot's to
# answer, and neither is "how much do you spend on a present".
PRESENT_ASK = re.compile(
    r"\bhow\s+much\s+(?:do|does)\s+(?:i|we)\s+(?:spend|pay)\b"
    r"|\bwhat\s+(?:do|does)\s+(?:i|we)\s+spend\b"
    r"|\bhow\s+much\s+(?:is|are|was|were)\s+(?:my|our)\b", re.I)
# The same ask with the thing said as a bill they own: "i pay 95 a month for my phone" then
# "how much is my phone bill" was answered with the phone-resale card. The possessive names the
# thing, and only a bill for that very thing on record is answered, so "how much is my house
# worth" in a chat that holds a water bill is still the world's question.
A_POSSESSIVE_ASK = re.compile(
    r"\bhow\s+much\s+(?:is|are|was|were)\s+(?:my|our)\s+([a-z][a-z' -]{1,30}?)\s*[?.!]*\s*$",
    re.I)


def _named(thing, wanted):
    """Whether a spend went on the very thing the present-tense ask names.

    Stricter than `_about`, which shares a family: "how much do i spend on water" is the water
    bill they gave, not the electricity one that sits in the same family of bills.
    """
    thing, wanted = (thing or "").lower().strip(), (wanted or "").lower().strip()
    if not thing or not wanted:
        return False
    if wanted in thing or thing in wanted:
        return True
    return bool(wanted.rstrip("s")) and wanted.rstrip("s") in thing


def _about(thing, wanted):
    """Whether the thing a spend went on is the thing the ask names.

    The ask often reaches for a broader word than the spend did: "40 on a takeaway" is money on
    food, and "12.50 on lunch" is too, so "how much did i spend on food" counts both. Only the
    words in one family are shared, so "how much did i spend on petrol" is still just petrol.
    """
    thing, wanted = thing.lower(), wanted.lower().strip()
    if not wanted:
        return True
    if not thing:
        return False
    if wanted in thing or thing in wanted or (
            wanted.rstrip("s") and wanted.rstrip("s") in thing):
        return True
    return not _family(thing).isdisjoint(_family(wanted))


def _family(thing):
    """The words one spend and one ask can both be named by: a broad name and its members."""
    words = set()
    low = thing.lower()
    for name, members in CATEGORIES:
        if name in low or any(member in low for member in members):
            words.add(name)
            words.update(members)
    return words


def the_total(spends):
    """The spends added up, as a figure that reads like the ones they typed."""
    total = 0.0
    for spend in spends:
        try:
            total += float(spend.get("amount") or 0)
        except (TypeError, ValueError):
            continue
    if not total:
        return ""
    if abs(total - round(total)) < 0.005:
        return str(int(round(total)))
    return "%.2f" % total  # money keeps its pence: "52.50", not "52.5"


def _listed(spends):
    """"300 on food and 40 on the train"."""
    parts = []
    for spend in spends:
        thing = spend.get("thing")
        parts.append(spend["amount"] + (" on " + thing if thing else ""))
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def answer(text, memory):
    """The reply for "how much have i spent" and its many wordings, or None."""
    said = " ".join(str(text or "").split())
    if not said:
        return None
    past = bool(ASK.search(said))
    present = bool(PRESENT_ASK.search(said)) and not past
    if not past and not present:
        return None
    wanted = ""
    on = ON_A_THING.search(said)
    if on:
        wanted = " ".join(word for word in on.group(1).split()
                          if word.lower() not in _ASK_FILLER)
    if present:
        # Read only where the thing named has a bill behind it; every other present-tense ask is
        # a habit question and stays with the knowledge base.
        if not wanted:
            mine = A_POSSESSIVE_ASK.search(said)
            if mine:
                wanted = " ".join(word for word in mine.group(1).split()
                                  if word.lower() not in _ASK_FILLER)
        if not wanted:
            return None
        spends = [spend for spend in the_spends(memory, said)
                  if _named(spend.get("thing") or "", wanted)]
        if not spends:
            return None
    else:
        spends = the_spends(memory, said)
    if wanted:
        spends = [spend for spend in spends if _about(spend.get("thing") or "", wanted)]
        if not spends:
            return ("You haven't told me what you spent on " + wanted +
                    ". Tell me and I'll keep a tally.")
        if len(spends) == 1:
            return "You told me " + _listed(spends) + "."
        return ("You've told me " + _listed(spends) + " - " + the_total(spends) +
                " on " + wanted + " in all.")
    if not spends:
        return ("You haven't told me what you've spent yet. Tell me the sums as they go out "
                "and I'll keep a tally.")
    if len(spends) == 1:
        return ("You've told me " + _listed(spends) + ". Tell me the rest and I'll keep a "
                "tally.")
    return ("You've told me " + _listed(spends) + " - " + the_total(spends) + " in all.")


# What is left. The other half of a tally is the money they said they had: "i've got 20 till
# friday", "my budget is 300 a month", and then the sums that went out. The ask is a sum too, and
# without this it was answered with the cheap-week advice or a search hedge.
#
#   i've got 20 till friday / i spent 6 on lunch / how much have i got left
#     before  Short until then is the cheap week, and it needs no more than the staples...
#     now     You had 20 and 6 has gone on lunch, so 14 is left.
#
# The money they have is read only where the line is about money: the figure carries a pound
# sign or a currency word, or what follows it is the scope it has to last ("till friday", "for
# the week", "left"). "i've got 2 kids" and "i've got 3 brothers" are not money.
# The size word a figure is written with is part of the figure. "my budget is 6 thousand" is six
# thousand, and a bot that files the 6 tells the person their 9000 quote is covered by it: the sum
# is right and only the reading of the words is wrong, which is why it hid - it shows up in the one
# turn where the figure is the whole answer. One pattern for the two ways of saying what they have,
# so both read the same suffixes and both read them as the figure they meant.
_HELD_SCALE = r"(\s*(?:k\b|thousand\b|grand\b|p\b|pounds?|quid|gbp))?"

HELD = re.compile(
    r"\b(?:i|we)(?:'ve|'d|\s+have|\s+had)?\s+(?:only\s+|just\s+)?(?:got\s+|have\s+)?"
    r"(?:only\s+|just\s+|about\s+|around\s+|maybe\s+|like\s+)*£?\s*" + _MONEY +
    _HELD_SCALE + r"(.*)$", re.I)
BUDGET_HELD = re.compile(
    r"\b(?:my|our)\s+budget(?:\s+is|'?s|\s+of)?\s+(?:only\s+|just\s+|about\s+|around\s+|"
    r"maybe\s+)?£?\s*" + _MONEY + _HELD_SCALE, re.I)
# "my savings are 1500" puts the savings first and the figure after, which the reader below does
# not see: the money is the subject of the line, not something they said they have.
SAVINGS_HELD = re.compile(
    r"\b(?:my|our)\s+(?:savings|saving)\s+(?:are|is|stand\s+at|come\s+to)\s+(?:only\s+|"
    r"just\s+|about\s+|around\s+|maybe\s+)?£?\s*" + _MONEY +
    # "2k" is two thousand and this reader would say two, so a short form is left to nobody
    # rather than answered with the wrong figure.
    r"(?!\s*(?:k|p)\b)", re.I)
# "im on a budget of 200 a month" is the same budget the other way round: the possessive is left
# off and the figure follows a phrase instead, which the budget reader above does not see.
ON_A_BUDGET = re.compile(
    r"\b(?:i|we)(?:'m|'re|'ve)?\s+(?:on|working\s+to|sticking\s+to|sticking\s+with)\s+a\s+"
    r"budget\s+of\s+(?:only\s+|just\s+|about\s+|around\s+|maybe\s+)?£?\s*" + _MONEY +
    r"(\s*(?:k\b|p\b|pounds?|quid|gbp))?", re.I)
# "theres about 90 left" leaves the holder out, and every reader above asks who has the money:
# "i have", "my budget", "my savings", "on a budget". The person says it the way a friend does
# when the sum is the whole of what they know about their money, and the ask that follows ("how
# much have i got left") then found nothing and told them they had never said a budget. What
# makes it money and not a count is the scope at the end - "left", "remaining", "to last" - which
# is the same scope `HELD` reads after the figure, and the reason "there's 2 kids at home" is not
# a fund. The scope is a lookahead here rather than a group, because the sum ends at those words.
THERE_LEFT = re.compile(
    r"\bthere(?:'s|s|\s+is|\s+are|\s+was)\s+(?:only\s+|just\s+|about\s+|around\s+|"
    r"maybe\s+|like\s+|still\s+|nearly\s+)*(?:a\s+)?£?\s*" + _MONEY +
    r"(\s*(?:k\b|p\b|pounds?|quid|gbp))?(?=\s*(?:left|remaining|to\s+last)\b)", re.I)
# A figure with a scope after it is money only when nothing else in the line owns the count.
# People count things with exactly this shape - "i made 12 buns and theres 5 left", "theres 2
# left in the shop", "weve got 3 left of the paint" - and a "how much have i got left" ask is
# about money, so those lines must not file a fund. What gives a count away is the thing being
# counted: a figure with its own noun ("12 buns"), the scope written as "left of the paint" or
# "left in the shop", or a plural noun in the clause before the figure. Nothing here touches a
# figure the person holds of nothing in particular, which is the line this reader is for.
# The thing counted, when the figure says it: "12 buns", "2 kids". A currency word after the
# figure is the money itself and not a thing counted - "theres 10 pounds left" is a tenner - so
# those are read out of the count.
_A_COUNTED_NOUN = re.compile(r"\b\d+\s+([a-z]{3,}(?:s|es))\b", re.I)
_A_CURRENCY_PLURAL = ("pounds", "quid", "euros", "dollars", "bucks", "pence", "pennies",
                      "cents", "sterling")
# "left of the paint", "left in the shop", "left over from the shop": the scope names the thing
# counted. A period after the scope is the time the money has to last and not a count of
# anything - "theres 30 left for the week" is a budget - so periods are read out of it.
_A_TIME_SCOPE = (r"(?![ \t]*(?:" + "|".join((r"week", r"weekend", r"month", r"day",
                                            r"days", r"year", r"fortnight", r"holiday",
                                            r"holidays", r"term", r"morning", r"evening",
                                            r"night", r"month\s+end")) + r")\b)")
_A_SCOPE_OF_A_THING = re.compile(
    r"\b(?:left|remaining)\s+(?:over\s+)?(?:of|in|on|from|at|for)\s+"
    r"(?:the|a|an|my|our|his|her|their|this|that)" + _A_TIME_SCOPE, re.I)
# Plural words that are the money itself, or the time it has to last, rather than things counted:
# "things are tight this month and theres about 90 left" is still money.
_A_MONEY_PLURAL = ("things", "days", "weeks", "months", "years", "minutes", "hours",
                   "pounds", "quid", "euros", "dollars", "pence", "savings", "notes",
                   "coins", "bills", "pennies", "payments", "leftovers")
_A_PLURAL = re.compile(r"\b([a-z]{4,}(?:s|es))\b", re.I)


def _a_count_of_a_thing(text):
    """True when the figure in the line counts something, so it is not money of theirs."""
    for noun in _A_COUNTED_NOUN.findall(text):
        if noun.lower() not in _A_CURRENCY_PLURAL:
            return True
    if _A_SCOPE_OF_A_THING.search(text):
        return True
    before = text.split("there", 1)[0] if "there" in text else ""
    for word in _A_PLURAL.findall(before):
        word = word.lower()
        if word in _A_MONEY_PLURAL or word.endswith("ss"):
            continue
        return True
    return False


# The scope the money has to last, which is what makes a plain figure money: "till friday", "for
# the week", "left", "this month". A gift is not a budget - "i got 20 for my birthday" is money
# that came in, and it is not what a "what's left" ask is about.
_HELD_SCOPE = re.compile(
    r"^\s*(?:left|till|until|to\s+last|this\s+(?:week|month|payday)|for\s+the\s+(?:week|month)|"
    r"a\s+(?:week|month)\b|the\s+(?:week|month)\b|"
    # "i've got 3000 saved", "put by", "in savings": a figure with one of these after it is money
    # of theirs that is waiting, which is what a "how much is left" ask is about. These are money
    # words, the same test the rest of the guard uses, so "i've got 2 kids" is still not money.
    r"saved|put\s+(?:by|away|aside)|set\s+aside|in\s+(?:the\s+bank|savings|an?\s+account)|"
    r"in\s+the\s+building\s+society)", re.I)

# The ask: "how much have i got left", "what's left", "how much is left of that", and the
# affordability question, which is the same sum with a comparison in it.
LEFT = re.compile(
    r"\bhow\s+much\s+(?:is\s+|was\s+)?(?:(?:have|has|do|does|did)\s+(?:i|we)\s+)?"
    r"(?:got\s+|have\s+)?(?:left|remaining)\b"
    r"|\bwhat(?:'s| is|s)\s+(?:left|remaining)\b"
    r"|\bwhat\s+(?:have|do)\s+(?:i|we)\s+(?:got\s+)?(?:left|remaining)\b"
    r"|\bhow\s+much\s+(?:of\s+)?(?:it|that|the\s+[a-z]+)\b[^?]{0,20}\b(?:left|remaining)\b"
    # The same ask written as a recall of what they said: "and how much did i tell you i had
    # left", "what did i say i had left". The store's recall frames read the line as a question
    # about the chat, and the sum is in the chat, so the ask has to be in this reader too or the
    # person who checks the bot remembers nothing about money they gave it a turn before.
    r"|\b(?:how\s+much|what)\s+did\s+(?:i|we)\s+(?:tell\s+you|say)\b[^?]{0,30}"
    r"\b(?:left|remaining)\b", re.I)
AFFORD = re.compile(
    r"\bcan\s+(?:i|we)\s+afford\s+(.*)$"
    r"|\bis\s+there\s+enough\s+(?:left\s+)?(?:for|to)\s+(.*)$"
    r"|\b(?:do|have)\s+(?:i|we)\s+(?:have|got)\s+enough\s+(?:left\s+)?(?:for|to)\s+(.*)$"
    r"|\benough\s+left\s+for\s+(.*)$"
    r"|\b(?:is|was|will|would)\s+(?:that|this|it)\s+(?:be\s+)?enough\s+(?:for|to)\s+(.*)$", re.I)


def _figure(value):
    """A sum of money the way the person's own figures read: 20, 14, 37.50."""
    value = float(value or 0)
    if abs(value - round(value)) < 0.005:
        return str(int(round(value)))
    return "%.2f" % value  # money keeps its pence: "37.50", not "37.5"


def _with_scale(number, word):
    """A figure with the size word written after it: "6 thousand" -> "6000", "2k" -> "2000".

    Pence ("50p") and plain pounds are left exactly as typed: only the size words multiply, so
    the one thing this changes is the figure a person meant when they said how much they had.
    """
    word = (word or "").strip().lower()
    if not (word.startswith("k") or word.startswith("thousand") or word.startswith("grand")):
        return number
    try:
        value = float(number) * 1000
    except (TypeError, ValueError):
        return number
    return str(int(round(value))) if abs(value - round(value)) < 0.005 else number


def _held_in(line):
    """The money one line says they have, as a figure, or None."""
    text = _plain(" ".join(str(line or "").split()))
    if not text or "?" in text:
        return None
    match = BUDGET_HELD.search(text) or ON_A_BUDGET.search(text) or SAVINGS_HELD.search(text)
    if match:
        return _with_scale(match.group(1), match.group(2))
    match = THERE_LEFT.search(text)
    if match and not _a_count_of_a_thing(text):
        return _with_scale(match.group(1), match.group(2))
    match = HELD.search(text)
    if match:
        currency, tail = (match.group(2) or "").strip(), match.group(3) or ""
        if not currency and "£" not in match.group(0) and not _HELD_SCOPE.match(tail):
            return None
        if not currency and "£" not in match.group(0) and _a_count_of_a_thing(text):
            return None
        return _with_scale(match.group(1), match.group(2))
    return None


def the_held(memory, text=None):
    """The money they last said they had this chat, as {"amount", "line"}, or None."""
    found = None
    for line in the_lines(memory, text):
        amount = _held_in(line)
        if amount is not None:
            found = {"amount": amount, "line": line}
    return found


def _a_thing_to_buy(said):
    """The thing an affordability ask names, in the words they used: "a takeaway", "new shoes"."""
    match = AFFORD.search(said)
    if not match:
        return ""
    thing = next((group for group in match.groups() if group), "")
    thing = re.split(r"[,.!?;]", " ".join(thing.split()))[0]
    thing = _TAIL_OFF.sub("", _TRAILING.sub("", thing)).strip()
    thing = re.sub(r"^(?:it|that|one|anything)\b", "", thing).strip()
    return thing if 1 < len(thing) < 40 else ""


# The price a thing is said with: "a 200 coat", "a coat for 200", "£200 shoes", "200 quid". A
# bare number in front of a singular noun is a price ("a 200 coat"); in front of a plural it is a
# count ("10 tickets"), and a count is not money.
A_PRICE = re.compile(
    r"£\s*(?P<sigil>\d[\d,]*(?:\.\d{1,2})?)"
    r"|(?P<word>\d[\d,]*(?:\.\d{1,2})?)\s*(?:pounds?|quid|gbp)\b"
    r"|(?:for|under|about|around)\s+(?P<ask>\d[\d,]*(?:\.\d{1,2})?)"
    r"|(?P<bare>\d[\d,]*(?:\.\d{1,2})?)\s+(?P<item>[a-z][a-z'-]*)\b", re.I)


def _the_price(thing):
    """The price a thing is named with, or None: "a 200 coat" -> 200.0.

    The affordability question is a comparison, so the half people leave out has to be read out of
    the line: without it the reply says a thing is covered by money it was never checked against.
    """
    match = A_PRICE.search(str(thing or ""))
    if not match:
        return None
    for group in ("sigil", "word", "ask"):
        value = match.group(group)
        if value:
            return float(value.replace(",", ""))
    item = match.group("item") or ""
    if item.endswith("s") and not item.endswith("ss"):
        return None  # "10 tickets" is a count, not a price
    value = float((match.group("bare") or "0").replace(",", ""))
    return value if value >= 10 else None  # "a 2 litre milk" is a size, not a price


def _bare_thing(thing):
    """The thing without the little word in front of it: "a holiday" -> "holiday"."""
    return re.sub(r"^(?:a|an|the|some|my|our|any)\s+", "", str(thing or "").strip(), flags=re.I)


# The words a line uses to ask for the sum and nothing else. A line with a thing in it ("how much
# is left of the paint") is not a money ask, so on a first line it is left to the module that knows
# about paint.
_ASK_WORDS = frozenset("""a an and any afford affordt can could do does did enough for get got
have has how i is it its left me much my of much's remaining some that the there this to was we
what what's whats will would you your im i'm we're t left-over""".split())


def _only_the_ask(said):
    """True when the line is the sum asked and nothing else: "how much is left", "can i afford it"."""
    words = [word.strip(".,!?;:'\"").lower() for word in str(said or "").split()]
    return not [word for word in words if word and word not in _ASK_WORDS]


def _nothing_before(memory, text):
    """True when this line is the first thing said in the chat."""
    return len(the_lines(memory, text)) <= 1


# "and if i spend 20 more", "what if i spend 50", "if i spend another 30 what then": the sum with
# one more spend in it. The line says if, so nothing has gone out of it and the tally must not file
# it - but the arithmetic on their own figures is the only useful answer, and it was a receipt of
# nothing ("Got it - if you spend 20 more") or a savings essay instead.
A_WHAT_IF = re.compile(
    r"\b(?:what\s+)?if\s+(?:i|we)\s+(?:spend|blow|use\s+up|spend\s+up)\s+"
    r"(?:another\s+|a\s+further\s+|just\s+)?£?\s*(?P<amount>\d[\d,]*(?:\.\d{1,2})?)"
    r"(?P<currency>\s*(?:k\b|p\b|pounds?|quid|gbp))?(?P<tail>.*)$", re.I)
# "if i spend 20 minutes on it" is a length of time, not money, and the same figure in the sum
# reader would be answered as 20 pounds.
A_LENGTH_NOT_MONEY = re.compile(
    r"^\s*(?:hours?|hrs?|minutes?|mins?|days?|weeks?|months?|years?|nights?|times?)\b", re.I)


def _the_what_if(match, memory):
    """The sum with a spend in it that has not happened, or None."""
    currency = (match.group("currency") or "").strip().lower()
    if currency in ("k", "p"):
        return None  # "spend 2k" is two thousand and this reader would say two
    if A_LENGTH_NOT_MONEY.match(match.group("tail") or ""):
        return None
    amount = float((match.group("amount") or "0").replace(",", ""))
    held = the_held(memory)
    if held is None or amount <= 0:
        return None  # nothing in the chat says what they had, so this is another question
    try:
        had = float(held["amount"])
    except (TypeError, ValueError):
        return None
    spends = the_spends(memory, None)
    left = had - (sum(float(spend.get("amount") or 0) for spend in spends) if spends else 0.0)
    if amount > left:
        return ("Spend " + _figure(amount) + " more and you are " + _figure(amount - left) +
                " over - " + _figure(left) + " is what is left now.")
    if not spends:
        return ("Spend " + _figure(amount) + " of the " + _figure(had) + " you told me you "
                "have and " + _figure(left - amount) + " is left.")
    return ("Spend " + _figure(amount) + " more and " + _figure(left - amount) + " is left.")


def what_is_left(text, memory):
    """The reply for "how much have i got left" and "can i afford a takeaway", or None."""
    said = " ".join(str(text or "").split())
    if not said:
        return None
    what_if = A_WHAT_IF.search(said)
    if what_if:
        # A spend that has not happened is not the ask for the sum, so this comes first: a line
        # with both shapes in it ("and if i spend 20 more, what's left?") is the what-if.
        return _the_what_if(what_if, memory)
    if not (LEFT.search(said) or AFFORD.search(said)):
        return None
    if readings(said):
        return None  # a line with a spend in it is a report, not the ask
    held = the_held(memory)
    if held is None:
        # A first line has no memory behind it, and every reply this module has is about memory:
        # "You haven't told me a budget" names something the person never mentioned, and the hedge
        # that was given instead asked them to search for their own money. The line itself is what
        # there is to answer, so the question is put back with what is needed to answer it.
        if _nothing_before(memory, said) and _only_the_ask(said):
            if AFFORD.search(said) and not LEFT.search(said):
                return ("Afford what, and with what? Tell me the thing and what you've got to "
                        "spend, and I'll do the sum.")
            return ("Left of what? Tell me what you've got and what has gone out of it, and I'll "
                    "do the sum.")
        return None  # nothing in the chat says what they had, so this is another question
    try:
        had = float(held["amount"])
    except (TypeError, ValueError):
        return None
    spends = the_spends(memory, None)
    if spends:
        out = sum(float(spend.get("amount") or 0) for spend in spends)
    else:
        out = 0.0
    left = had - out
    if AFFORD.search(said) and not LEFT.search(said):
        thing = _a_thing_to_buy(said)
        price = _the_price(thing)
        name = _bare_thing(thing)
        named = (thing if re.match(r"(?:a|an|the|some|my|our|any)\s", thing, re.I)
                 else ("the " + name if name else ""))
        cost = ("Tell me the price of " + named if named else "Tell me the price") + \
            " and I'll say whether it fits."
        if spends and left <= 0:
            return ("You had " + _figure(had) + " and " + _listed(spends) + " has gone, so you "
                    "are " + _figure(-left) + " over. " +
                    (thing.capitalize() + " needs more coming in first." if thing
                     else "Tell me if more comes in and I'll work it out again."))
        if price is not None:
            # A price in the line is the whole question, so the answer is yes or no with the
            # figure that makes it so - not a thing declared covered whatever it costs.
            if spends:
                if price > left:
                    return ("No - " + thing + " is more than the " + _figure(left) +
                            " you have left. It wants " + _figure(price - left) + " more.")
                return ("Yes - " + thing + " comes out of the " + _figure(left) + " you have "
                        "left, with " + _figure(left - price) + " spare.")
            if price > had:
                return ("No - " + thing + " is more than the " + _figure(had) + " you told me "
                        "you have. It wants " + _figure(price - had) + " more.")
            return ("Yes - " + thing + " comes out of the " + _figure(had) + " you told me you "
                    "have, with " + _figure(had - price) + " spare.")
        if not spends:
            return ("You told me you have " + _figure(had) + " and nothing has gone out of it "
                    "yet, so anything up to " + _figure(had) + " is covered. " + cost)
        return ("You had " + _figure(had) + " and " + _listed(spends) + " has gone, so " +
                _figure(left) + " is left. " + cost)
    if not spends:
        return ("You told me you have " + _figure(had) + ", and you've not said that any of it "
                "has gone yet.")
    if left <= 0:
        return ("You had " + _figure(had) + " and " + _listed(spends) + " has gone, so you are " +
                _figure(-left) + " over.")
    return ("You had " + _figure(had) + " and " + _listed(spends) + " has gone, so " +
            _figure(left) + " is left.")
