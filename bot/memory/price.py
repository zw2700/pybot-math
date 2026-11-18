"""A price the person gives, read against the range the bot itself named a turn ago.

"the cheapest quote i got for a new boiler is 2400" / "is that a lot" was answered "Alright then
- good luck with it", and "is that about right" after a boiler service was answered with the
service card again: the range was on the screen, and nothing in the bot read the two figures
together. The knowledge base can price a job it is asked about ("is 400 too much for a roof
repair"), but a follow-up names neither the job nor the question - only "that" - so the subject
and the range both have to come from the answer already given.

What comes back is only ever what the answer said: where the person's figure stands against the
range in it. Nothing here knows what a boiler costs, so a line whose last answer named no money
range is left to the modules that do (this reader returns None).

The ask is a judgement of a figure - "is that a lot", "does that sound right", "is that
expensive" - and not a question about a thing: "how much does a boiler cost" and "when is it
worth it" are answered by the entries, and "is 400 too much for a roof repair" names its subject
and stays with the price entry that owns it.
"""
import re

from ..compose import pick

# The words that ask for a judgement on a figure, without naming the thing priced. "is that a
# lot", "does that sound about right", "is 2400 expensive" - every one of them leans on the
# answer a turn ago for both the subject and the range.
A_PRICE_ASK = re.compile(
    r"\b(?:is|was)\s+(?:that|this|it|(?:that|this)\s+[a-z]+)\s+(?:a\s+lot|expensive|dear|cheap|"
    r"about\s+right|the\s+going\s+rate|the\s+right\s+price|the\s+normal\s+price|normal|"
    r"reasonable|fair|too\s+much|steep|a\s+rip[-\s]?off|overpriced|in\s+line)\b"
    r"|\b(?:does|do|did)\s+(?:that|this|it)\s+(?:sound|seem)\s+(?:about\s+)?(?:right|ok|okay|"
    r"reasonable|fair|normal|expensive)\b"
    r"|\b(?:is|was)\s+(?:that|this|it)\s+(?:the\s+)?(?:going\s+rate|normal|what\s+it\s+should\s+be)\b"
    r"|\bam\s+i\s+being\s+(?:ripped\s+off|overcharged|done)\b"
    r"|\bdid\s+i\s+(?:get|pay)\s+(?:a\s+)?(?:good|fair|bad)\s+(?:price|deal|rate)\b"
    r"|\b(?:is|was)\s+(?:that|this|it)\s+(?:a\s+)?(?:good|fair|bad)\s+(?:price|deal|rate|quote)\b"
    # A doubt said as a statement is the same question: "that sounds like a lot", "that seems
    # expensive", "sounds about right". They come straight after their own quote and the answer
    # said only "Got it - that sounds like a lot" back to them.
    r"|\b(?:that|this|it)(?:'s|s|\s+is|\s+was)?\s+(?:sounds?|seems?|looks?)\s+(?:like\s+)?"
    r"(?:a\s+lot|expensive|dear|steep|a\s+rip[-\s]?off|too\s+much|about\s+right|"
    r"the\s+going\s+rate|the\s+right\s+price)\b"
    # "that's a lot", "thats expensive": the same doubt with the verb elided, which is how most
    # people write it, and it was answered as if they had said something about their day.
    r"|\b(?:that|this|it)\s*(?:'s|s|is|was)\s+(?:(?:very|really|quite|a\s+bit|bit|so|pretty|"
    r"rather)\s+)?(?:a\s+lot|expensive|dear|steep|too\s+much|a\s+rip[-\s]?off|overpriced)\b"
    r"|\b(?:sounds?|seems?|looks?)\s+(?:like\s+)?(?:(?:very|really|quite|a\s+bit|bit|so|pretty)\s+)?"
    r"(?:a\s+lot|expensive|dear|steep|too\s+much|"
    r"about\s+right|the\s+going\s+rate)\b"
    r"|\bhow\s+does\s+that\s+(?:sound|compare)\b"
    r"|\b(?:is|was)\s+(?:that|this|it)\s+(?:more|less)\s+than\s+(?:usual|normal|it\s+should\s+be)\b",
    re.I)

# The signs that a figure is money. A bare number is only read as a price when the line marks it
# as one ("quoted 400", "2400 for the boiler", "the cheapest is 2400"): a count, a size and an
# age are figures too, and "i have 2 kids" is not a price.
_PRICE_SYMBOL = re.compile(r"£|\$|€")
_PRICE_WORD = re.compile(r"\b(?:quid|pounds?|pence|euros?|dollars?|grand|notes?|money|"
                         r"cost(?:s|ing)?|costs?|price[sd]?|quoted?|quote[sd]?|charge[ds]?|"
                         r"(?:pay|pays|paying|paid|payed)|wants?|wanting|asking|budget|spent|spend|"
                         r"cheapest|dearest|expensive|cheaper|dearer|fees?|bill|bills|"
                         r"invoice|estimate[d]?|rates?)\b", re.I)
# A figure with a unit on it is a rate, not a price: "£200 to £300 a day" is what a roofer
# charges for a day, and a whole job at £400 is nothing to do with the length of a day.
_AFTER_A_RATE = re.compile(r"\s*(?:a|an|per|each|every)\s+(day|week|month|year|hour|visit|"
                           r"call[-\s]?out|session|night)\b", re.I)
# "up to £90" is a ceiling, not the price of the job: the person's figure being above it says
# nothing about whether they were overcharged.
_A_MONEY_CEILING = re.compile(r"\b(?:up\s+to|no\s+more\s+than|at\s+most|under|below|less\s+than|"
                              r"over|more\s+than|above|at\s+least)\s*$", re.I)
# A range joins two figures; a list does not. "£195, and £400-£600 for MOT" is road tax and then
# a different item, and reading 195 to 400 out of it judged an £800 insurance bill against a band
# the answer never named. The comma before "and" is the mark of a list, so it ends the range there.
# One range of money: "£60 to £120", "2,000-3,000 pounds", "between £150 and £400".
_PRICE_RANGE = re.compile(
    r"(?P<low>£|\$|€)?\s?(?P<low_n>\d[\d,]*(?:\.\d+)?)\s?"
    r"(?:(?:-|–|—|to)\s?|(?<![,])\s+and\s+)"
    r"(?:(?P<high>£|\$|€)\s?)?(?P<high_n>\d[\d,]*(?:\.\d+)?)"
    r"\s?(?P<unit>k\b|pounds?|quid|euros?|dollars?|grand)?", re.I)


def _money(value):
    """The figure as it is said on the screen: 2400 in a range is 2,400."""
    if value >= 1000:
        return "{:,}".format(int(value)) if float(value).is_integer() else "{:,.2f}".format(value)
    return ("%d" % value) if float(value).is_integer() else ("%.2f" % value)


def _a_value(token):
    """A figure as it was written: "2,400" and "2400" are the same number."""
    try:
        return float(str(token).replace(",", ""))
    except (TypeError, ValueError):
        return 0.0


def _the_money_said_back(said, text):
    """A figure keeps the symbol the line wrote; with none written it is the pound it was asked in."""
    said = str(said or "").strip()
    if re.match(r"[£$€]", said):
        return said
    for mark in ("£", "$", "€"):
        if mark in str(text or ""):
            return mark + said
    return "£" + said


def _the_price_said(value):
    """"2400" said back the way it is written: "£2,400".

    The currency is part of the figure when it is said back: a verdict that opens "400 sits inside
    the usual range of £150 to £400" reads as a count beside a price, and every pool below opens
    on the figure.
    """
    return "£" + _money(value)


# A symbol on the range but not on the figure reads as two different moneys in one sentence
# ("The usual range is £150 to £400, and 400 is inside it"), so the figure takes the range's
# symbol when it has none of its own. A word for the money ("2,000 to 3,000 pounds") is left
# where it is: it covers the figure too, and "2,400 is inside it" is what a person would say.
A_PRICE_SYMBOL_ONLY = re.compile(r"[£$€]")


def _the_figure_in_the_range_s_style(mine, said, range_said):
    """The person's figure written the way the range beside it is written."""
    figure = said or _money(mine)
    # "2400" in "The usual range is 2,000 to 3,000 pounds, and 2400 is inside it" is the same
    # price written two ways in one breath.
    figure = re.sub(r"\d[\d,]*(?:\.\d+)?",
                    lambda one: _money(_a_value(one.group(0))), figure)
    mark = A_PRICE_SYMBOL_ONLY.search(str(range_said or ""))
    if mark and not A_PRICE_SYMBOL_ONLY.search(figure):
        return mark.group(0) + figure
    return figure


def _number_tokens(text):
    return [(match.group(0), match.start()) for match in
            re.finditer(r"\d[\d,]*(?:\.\d+)?", str(text or ""))]


def _prices_in(text):
    """[(value, spoken)] for the figures in the line that are marked as money."""
    said = str(text or "")
    found = []
    for token, start in _number_tokens(said):
        value = _a_value(token)
        if not value:
            continue
        before = said[max(0, start - 24):start]
        after = said[start + len(token):start + len(token) + 20]
        marked = bool(_PRICE_SYMBOL.search(before + token + after[:1])) \
            or bool(_PRICE_WORD.search(before)) \
            or bool(re.match(r"\s?(?:quid|pounds|euros?|dollars?|grand|k)\b", after, re.I))
        if not marked:
            continue
        if _AFTER_A_RATE.match(after):
            continue
        # A figure counted in thousands is that many thousands: "a builder quoted me 12 grand for
        # an extension" was read as twelve pounds, and the answer told them "£12 is under the
        # £200 to £350 it usually comes to". The unit word stays in the figure said back, because
        # "12 grand is over the £200 to £350" is what the person wrote and "12,000" is not.
        thousands = re.match(r"\s?(k|grand|thousand)\b", after, re.I)
        spoken = token.strip(" ,")
        if thousands:
            value = value * 1000
            spoken = said[start:start + len(token) + len(thousands.group(0))].strip(" ,")
        found.append((value, spoken))
    return found


def _a_price_at_a_rate(text):
    """Whether the only figures in the line come with a period on them ("£200 to £300 a day")."""
    said = str(text or "")
    figures = [match for match in re.finditer(
        r"(?:£|\$|€)?\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:k|pounds|quid))?", said)]
    if not figures:
        return False
    for match in figures:
        if not _AFTER_A_RATE.match(said[match.end():match.end() + 20]):
            return False
    return True


def _price_ranges_in(text, period=None):
    """[(start, end, low, high, spoken)] for each money range in the answer.

    A range in money is two figures with money on them or a money word beside them, so "10 to 15
    years", "two or three quotes" and "70 to 80 per cent" are not ranges here.

    A range with a period on it ("£200 to £300 a day", "£140 to £150 a month") is only read when
    the person said their figure in the same period: a roofer's day rate says nothing about a whole
    job at £400, and a monthly bill says everything about a bill the person calls monthly.
    """
    said = str(text or "")
    found = []
    for match in _PRICE_RANGE.finditer(said):
        low_token, high_token = match.group("low_n"), match.group("high_n")
        try:
            low = _a_value(low_token)
            high = _a_value(high_token)
        except (TypeError, ValueError):
            continue
        if not low or not high or high <= low:
            continue
        tail = said[match.end():match.end() + 20]
        head = said[max(0, match.start() - 24):match.start()]
        unit = match.group("unit") or ""
        marked = bool(match.group("low") or match.group("high")) \
            or bool(unit and unit.lower() not in ("k",)) \
            or bool(_PRICE_SYMBOL.search(text[max(0, match.start() - 3):match.end() + 3])) \
            or bool(_PRICE_WORD.search(head)) \
            or bool(_PRICE_WORD.search(tail))
        if not marked:
            continue
        # "£200 to £300 a day" is a day rate: the figure the person is comparing is a whole job,
        # unless the person said their own figure by the day too.
        rate = _AFTER_A_RATE.match(tail)
        if rate and (period or "") != rate.group(1).lower():
            continue
        if unit.lower() == "k":
            low, high = low * 1000, high * 1000
        spoken = said[match.start():match.end()].strip()
        spoken = re.sub(r"\s+", " ", spoken).strip(" ,.;:")
        if _A_MONEY_CEILING.search(head):
            # "up to £90" bounds the job, it does not price it: a figure above the ceiling is
            # not outside a going rate, so there is nothing to say about it.
            continue
        found.append((match.start(), match.end(), low, high, spoken))
    return found


def _the_price_they_gave(text, memory):
    """(value, spoken) for the price the person gave, from this line or one of the last three."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    lines = [text] + [str(turn.get("user") or "") for turn in list(reversed(turns or []))[:3]
                      if isinstance(turn, dict)]
    for line in lines:
        marked = _prices_in(line)
        if marked:
            return marked[-1]
        bare = [(value, token) for value, token in
                ((_a_value(token), token.strip(" ,")) for token, _ in _number_tokens(line))
                if value >= 40]
        if not bare:
            continue
        if _PRICE_WORD.search(line):
            # "my boiler service was 250": a figure the line itself puts in money, with no word
            # for the money on it.
            return bare[-1]
        # A figure the newest line names without a money word is still the newest figure in the
        # chat, and a money word two lines back must not reach past it: after "the cheapest quote
        # i got for a new boiler is 2400" and "my boiler service was 250", "is that a lot" is
        # about the 250 they just paid, not the 2,400 quote. That line is the bare reader's, and
        # no line older than it is read here.
        return None, ""
    return None, ""


def _a_bare_price_in_the_thread(text, memory):
    """The price they gave with no unit on it: "my boiler service was 250".

    A bare figure is only read when no line in the thread marked one as money, and the answer
    still has to name a money range near it, so a count or a size is not turned into a price.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    lines = [text] + [str(turn.get("user") or "") for turn in list(reversed(turns or []))[:3]
                      if isinstance(turn, dict)]
    for line in lines:
        if _prices_in(line):
            continue  # that line said its price outright and it was not the one read
        bare = [value for value in (_a_value(token) for token, _ in _number_tokens(line))
                if value >= 40]
        if bare:
            return bare[0], _the_price_said(bare[0])
    return None, ""


def _answers_in(turns):
    """The answers the bot gave, newest first."""
    found = []
    for turn in reversed(list(turns or [])):
        if not isinstance(turn, dict):
            continue
        said = turn.get("bot") or turn.get("reply")
        if isinstance(said, str) and said.strip():
            found.append(said)
    return found


def _the_range_that_is_about_it(answers, price, period=None):
    """(low, high, spoken) for the range in the newest answer that is about this price, or None.

    The answer can name several: a roofer's card names a patch, a flat roof and a whole roof,
    and 400 is the patch. The nearest range wins as long as it is within three times the price -
    a £6,000 re-roof is not read against a £150-£400 patch - and no verdict is given when two
    ranges are within twice as near as each other, because then the answer did not say which job
    the person is being quoted for.

    A figure under every range the answer names, or over every one, is the exception: whichever
    range is picked the verdict is the same, so the answer has said enough and the band nearest
    the figure is the one to name. A 900 quote for a bathroom, against a card of £3,000 to £7,000
    fitted and £8,000 to £12,000 with the plumbing changed, is worth asking about, and no card
    that prices one job in two sizes should leave that unsaid.
    """
    for said in answers[:2]:
        # A card that prices a day of the work cannot judge the price of the whole job: the second
        # range in "£150 to £300 a day for one person, or £200 to £350 for two" has no period on
        # it, so the reader inside the range cannot see that it is a rate and the sentence can.
        found = _the_ranges_that_are_not_rates(said, _price_ranges_in(said, period))
        if not found:
            continue
        bands = [(item[2], item[3], item[4]) for item in found]
        if all(price < low for low, _, _ in bands):
            return min(bands)
        if all(price > high for _, high, _ in bands):
            return max(bands, key=lambda band: band[1])
        scored = []
        for low, high, spoken in bands:
            if low <= price <= high:
                distance = 0.0
            elif price > high:
                distance = price - high
            else:
                distance = low - price
            scored.append((distance, low, high, spoken))
        scored.sort()
        best = scored[0]
        if price > best[2] and price > best[2] * 3:
            continue
        if price < best[1] and price * 3 < best[1]:
            continue
        if len(scored) > 1:
            near, second = scored[0][0], scored[1][0]
            # A range that holds the figure (near is 0) is the answer's verdict, whatever else the
            # card names: "a patch is £150 to £400, a whole roof £5,000 to £15,000" says 400 is
            # the patch. Two ranges the figure is outside both are only read when one is twice as
            # near as the other, because then the card did not say which job is being priced.
            if near and second < near * 2:
                continue
        return best[1], best[2], best[3]
    return None


# What the answer is told, in the pool that fits it: the range, and the figure they gave. The
# words are the answer's own, so nothing here adds a price the bot did not say.
A_PRICE_INSIDE = (
    "That is about right. The usual range is {aim}, and {price} is inside it.",
    "Yes, {price} is in the right range - the answer there put it at {aim}.",
    "{price} sits inside the usual range of {aim}, so that is the going rate.",
)
A_PRICE_OVER = (
    "That is above the going rate of {aim}, so it is worth checking what is behind it.",
    "{price} is over the {aim} the usual price comes to, so it is worth a second quote.",
    "That is on the high side: the range is {aim}, and {price} is above it.",
)
A_PRICE_UNDER = (
    "That is below the usual {aim}, so check what it covers - a part, a deposit, or the "
    "whole job.",
    "{price} is under the {aim} it usually comes to, so check what the quote leaves out.",
    "That is cheap against the {aim} the answer named, so make sure the price covers the job.",
)


# A card that prices more than one job can have the figure over one band and under the next, and
# then it has said something exact: the figure falls in the gap, and which job they had decides
# whether it is fair. Both bands are named here, so the verdict stands on its own.
A_PRICE_BETWEEN = (
    "{price} is over the {below} and under the {above}, so it depends which of those you had.",
    "{price} falls between the {below} and the {above} - which of those you had decides whether "
    "it is fair.",
)


def _the_between_verdict(mine, said, below, above, memory):
    """The verdict for a figure that falls between two bands the card prices, or None."""
    price = _the_figure_in_the_range_s_style(mine, said, below)
    line = pick(list(A_PRICE_BETWEEN), memory, "between" + str(mine))
    if not line:
        return None
    try:
        return line.format(price=price, below=below, above=above,
                           Price=price[:1].upper() + price[1:])
    except (KeyError, IndexError, ValueError):
        return None


def _the_verdict(mine, said, low, high, spoken, memory, own=False):
    """The judgement said in the answer's own words: inside, above or below its range.

    `own` is the card this turn earns, which the person does not see when the verdict takes its
    place: the words that point back at an answer on the screen are left out, so nothing says
    "the answer there" about a card that was never shown.
    """
    price = _the_figure_in_the_range_s_style(mine, said, spoken)
    if low <= mine <= high:
        pool, told = A_PRICE_INSIDE, "inside"
    elif mine > high:
        pool, told = A_PRICE_OVER, "over"
    else:
        pool, told = A_PRICE_UNDER, "under"
    lines = list(pool)
    if own:
        stood = [line for line in lines if "the answer" not in line]
        lines = stood or lines
    line = pick(lines, memory, told + str(mine))
    if not line:
        return None
    try:
        return line.format(aim=spoken, price=price,
                           Price=price[:1].upper() + price[1:])
    except (KeyError, IndexError, ValueError):
        return None


# A figure asked about in the same line as the thing it prices: "is 45 too much for a haircut",
# "was 250 a fair price for a service". The subject is named and the figure sits right before the
# verdict word, so the card this line earns is the card for the thing priced and its range is the
# range to judge the figure against - no answer a turn ago needed.
A_PRICE_ASK_WITH_THE_THING = re.compile(
    r"\b(?:is|was)\s+(?P<figure>[^,.?!]{0,40}?)\s*(?:too\s+much|a\s+lot|expensive|dear|steep|"
    r"a\s+rip[-\s]?off|about\s+right|reasonable|fair|the\s+going\s+rate|the\s+normal\s+price|"
    r"the\s+right\s+price|(?:a|an)\s+(?:good|fair|reasonable|normal|ok|okay)\s+(?:price|deal|"
    r"rate|quote))\b",
    re.I)

# The figure tied to the thing it prices: "120 for a plumber", "250 for a boiler service",
# "300 on a new boiler". Without one the price in the line is not attached to the card's subject.
_A_PRICE_FOR_THE_THING = re.compile(r"\b(?:for|on)\s+(?:a|an|the|my|our|your|his|her|their|this|"
                                    r"that)?\s*[a-z]", re.I)

# The words a price ask of that shape is made of, so what is left of the line is the thing priced.
_ASK_WORDS = {
    "much", "lot", "expensive", "dear", "steep", "rip", "off", "right", "reasonable", "fair",
    "going", "rate", "normal", "price", "prices", "good", "ok", "okay", "deal", "quote", "quoted",
    "cost", "costs", "costing", "charge", "charged", "charges", "paid", "pay", "paying", "payed",
    "was", "is", "did", "does", "do", "for", "to", "the", "a", "an", "and", "on", "of", "in",
    "it", "that", "this", "me", "my", "we", "i", "at", "just", "only", "about", "bit", "little",
    "total", "altogether", "bill", "quid", "pounds", "pound", "euro", "euros", "dollar", "dollars",
    "worth", "sound", "sounds", "seem", "seems", "again", "too", "get", "got", "all", "so",
}


def _the_thing_priced(text):
    """The thing the line prices ("a haircut"), or "" when the line names no thing at all."""
    left = _PRICE_SYMBOL.sub(" ", str(text or ""))
    left = re.sub(r"\d[\d,.]*", " ", left).lower()
    words = [word for word in re.findall(r"[a-z']+", left) if word not in _ASK_WORDS]
    return " ".join(words)


def _the_price_they_mean(text, memory):
    """(value, spoken) for the figure the line is asking a judgement on, or (None, "")."""
    mine, said = _the_price_they_gave(text, memory)
    if not mine:
        mine, said = _a_bare_price_in_the_thread(text, memory)
    return mine, said


def _the_period_they_said(text, memory):
    """The period the person put their own figure in - "a month", "a week" - or None.

    A bill of "200 this month" is compared with a range the answer gave "a month"; a quote for a
    whole job is not compared with a roofer's day rate.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    lines = [text] + [str(turn.get("user") or "") for turn in list(reversed(turns or []))[:3]
                      if isinstance(turn, dict)]
    for line in lines:
        found = re.search(r"\b(?:a|an|per|each|every|this|last)\s+"
                          r"(day|week|month|year|hour|night)\b", line, re.I)
        if found:
            return found.group(1).lower()
    return None


# "is that a lot of blood", "is that too much paracetamol": the ask is the same words, but what
# follows names another quantity than money, and a price verdict on a dose question is worse than
# the hedge it would replace. Only the bare asks can take a noun, so the word after the ask is
# read: a money word or a word that starts a phrase ("to pay", "for a plumber", "these days")
# keeps the ask, and anything else leaves the line to the module that knows about blood.
_A_MONEY_AFTER_THE_ASK = {
    "money", "quid", "pounds", "pound", "euros", "euro", "dollars", "dollar", "pence",
    "grand", "notes", "cash", "dosh", "price", "prices", "rate", "rates", "bill", "total",
}
_A_PHRASE_AFTER_THE_ASK = {
    "to", "for", "on", "in", "at", "by", "with", "per", "and", "or", "but", "if", "than",
    "compared", "when", "these", "those", "this", "that", "it", "now", "nowadays", "then",
    "though", "anyway", "honestly", "really", "actually", "do", "does", "did", "should",
    "would", "a", "an", "the", "so", "again", "altogether", "all", "any", "as", "from",
    "about", "worth", "sounds", "seems", "sound", "seem", "overall", "including",
}


def _a_price_ask(text):
    """The ask when it is about a figure, or None when the words after it name another quantity."""
    found = A_PRICE_ASK.search(text)
    if not found:
        return None
    tail = re.sub(r"^\s*of\b", "", text[found.end():], flags=re.I)
    words = re.findall(r"[a-z']+", tail.lower())
    if not words:
        return found
    first = words[0]
    # "that's a lot of work" is a heavy job, not a heavy price: an "of" after the ask names the
    # thing there is a lot of, and only money there keeps it a price.
    if found.group(0).lower().endswith("a lot") and first == "of":
        return found if len(words) > 1 and words[1] in _A_MONEY_AFTER_THE_ASK else None
    if first in _A_MONEY_AFTER_THE_ASK or first in _A_PHRASE_AFTER_THE_ASK:
        return found
    return None


def _a_rate_is_all_the_answer_names(answers):
    """Whether the newest answer prices only a day or an hour of the work, and never the job."""
    for said in answers[:1]:
        found = _price_ranges_in(said)
        if found and not _the_ranges_that_are_not_rates(said, found):
            return True
    return False


def _a_second_quote_is_the_test(memory):
    """What settles a figure for a whole job: the same job priced a second time."""
    from ..compose.prices import A_JOB_JUDGED
    return pick(list(A_JOB_JUDGED), memory, "jobjudged")


def judged(text, memory):
    """A line asking whether a figure they gave is high or low, from the answer already given."""
    if not isinstance(text, str) or not isinstance(memory, dict):
        return None
    if not _a_price_ask(text):
        return None
    turns = memory.get("turns")
    answers = _answers_in(turns)
    if not answers:
        return None
    mine, said = _the_price_they_mean(text, memory)
    if not mine:
        return None
    said = _the_money_said_back(said, text)
    period = _the_period_they_said(text, memory)
    aim = _the_range_that_is_about_it(answers, mine, period)
    if aim is None:
        if not period and _a_rate_is_all_the_answer_names(answers):
            # The answer prices a day or an hour of the work and the figure is the price of the
            # whole job, so there is no range to hold it against - but the person is still asking
            # whether their figure is normal, and the answer to that is the same for every job:
            # a second quote for the same job, compared on what each one covers.
            return _a_second_quote_is_the_test(memory)
        return None
    low, high, spoken = aim
    return _the_verdict(mine, said, low, high, spoken, memory)


def judged_with_the_card(text, answer, memory):
    """A price the line gives for a thing, judged against the range the answer for it names.

    "is 6000 too much for a new boiler" is answered with the card for a new boiler, which says
    what one usually costs - and the person's own figure is never put beside it. Unlike the ask a
    turn later, this one names the thing it prices, so the card this line earns is the right card
    and its range is the range to read.

    Two conditions keep it honest. The line has to name a thing ("is that a lot" prices nothing
    the card can be trusted for, and the answer a turn ago is where that ask belongs), and the
    card has to say one thing about the figure: inside one of its ranges, or above all of them,
    or below all of them. A card that prices several jobs - a cut, a colour, a blow dry - has the
    figure over one and under another, and then it has not said which job is being priced, so
    nothing is claimed here.
    """
    if not isinstance(text, str) or not isinstance(answer, str):
        return None
    asked = A_PRICE_ASK_WITH_THE_THING.search(text)
    if not asked:
        return None
    if not _the_thing_priced(text):
        return None
    tokens = _number_tokens(asked.group("figure"))
    if tokens:
        try:
            mine = _a_value(tokens[-1][0])
        except (TypeError, ValueError):
            return None
        if mine and _AFTER_A_RATE.match(text[tokens[-1][1]:tokens[-1][1] + 12] or ""):
            # "50 an hour": a rate, and the ranges on a card price a whole visit and a day's work
            # side by side, so nothing here says which of them the hourly figure belongs to.
            return None
    else:
        # "i paid 250 for a boiler service, is that a lot": the figure is in this line and the ask
        # only points at it. Only a figure the line marks as money, so "i have 2 kids" is not one,
        # and never a figure from an earlier line - that ask belongs to the answer a turn ago.
        marked = _prices_in(text)
        mine = marked[-1][0] if marked else None
        if not mine:
            return None
        # The figure has to be tied to the thing by a word of its own ("250 for a service"), which
        # is also what keeps a line another module carried along - "im paying 1200 to get the
        # bathroom done, is that reasonable" - out of this reader: the card answers that one and
        # names the thing in it, while a verdict on the figure alone does not.
        if not _A_PRICE_FOR_THE_THING.search(text):
            return None
    if not mine:
        return None
    said = _the_price_said(mine)
    verdict = _the_verdict_against_a_card(mine, said, answer, memory, definite_only=True)
    if verdict:
        return verdict
    # A card often ends on what something smaller costs - a boiler service beside the price of a
    # boiler - and a figure between the two prices the card names then straddles them. The opening
    # sentence is the part that prices the thing the card is about, so it is read on its own
    # before the card is called ambiguous.
    opening = re.split(r"(?<=[.!?])\s", answer.strip(), maxsplit=1)[0]
    if opening != answer:
        verdict = _the_verdict_against_a_card(mine, said, opening, memory)
        if verdict:
            return verdict
    return _the_verdict_against_a_card(mine, said, answer, memory)


# A card can price a day of the work and the person can give the price of the whole job: "a
# builder is usually £150 to £300 a day for one person, or £200 to £350 for two" and "they want
# 12 grand for an extension" are not comparable, and the range alone said "that is above the
# going rate of £200 to £350" about a twelve thousand pound job. The second range in that card
# has no "a day" after it, so the range reader cannot see the rate; the sentence it sits in can.
_A_RATE_IN_THE_SENTENCE = re.compile(
    r"\b(?:a|an|per|each)\s+(?:day|hour|week|month|night|visit|person|load)\b", re.I)


def _the_ranges_that_are_not_rates(answer, ranges):
    """The card's ranges that price the thing, leaving out a rate for a day or an hour of it."""
    kept = []
    for item in ranges:
        start, end = item[0], item[1]
        left = max(answer.rfind(".", 0, start), answer.rfind("\n", 0, start))
        after = [at for at in (answer.find(".", end), answer.find("\n", end)) if at != -1]
        right = min(after) if after else len(answer)
        sentence = answer[left + 1:right]
        if _A_RATE_IN_THE_SENTENCE.search(sentence) \
                and not _AFTER_A_RATE.match(answer[end:end + 20]):
            continue
        kept.append(item)
    return kept


def _the_verdict_against_a_card(mine, said, answer, memory, definite_only=False):
    """The verdict when the card's ranges say one thing about the figure, else None.

    `definite_only` asks for the claim the card makes outright - inside one of its bands, or above
    them all, or below them all - and leaves the gap between two bands to the opening sentence,
    which is the part that prices the thing the card is about rather than what something smaller
    costs. Without it, a boiler at 1,200 came back between the price of a boiler service and the
    price of a boiler.
    """
    ranges = _the_ranges_that_are_not_rates(answer, _price_ranges_in(answer))
    if not ranges:
        return None
    holds = [item for item in ranges if item[2] <= mine <= item[3]]
    if holds:
        _, _, low, high, spoken = holds[0]
        return _the_verdict(mine, said, low, high, spoken, memory, own=True)
    if all(item[2] > mine for item in ranges):
        _, _, low, high, spoken = min(ranges, key=lambda item: item[2])
        return _the_verdict(mine, said, low, high, spoken, memory, own=True)
    if all(item[3] < mine for item in ranges):
        _, _, low, high, spoken = max(ranges, key=lambda item: item[3])
        return _the_verdict(mine, said, low, high, spoken, memory, own=True)
    if definite_only:
        return None
    under = [item for item in ranges if item[3] < mine]
    over = [item for item in ranges if item[2] > mine]
    if under and over:
        near = max(under, key=lambda item: item[3])
        far = min(over, key=lambda item: item[2])
        # The bands of one job sit against each other ("£50 to £100 for a callout, £100 to £200
        # for a day"), so a figure in the gap is over one band and under the next and both are
        # named. A gap wider than the band below is not one job at two sizes: a haircut at £40 is
        # between "£15 to £35" for a cut and "£60 to £150" for colour, and naming both answered a
        # question about a cut with a hedge about two different things. A wide gap is read against
        # the nearer band, which is the thing that was asked about.
        if far[2] - near[3] <= near[3] - near[2]:
            return _the_between_verdict(mine, said, near[4], far[4], memory)
        return _the_verdict(mine, said, near[2], near[3], near[4], memory, own=True)
    return None
