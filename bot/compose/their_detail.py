"""A detail the person adds to the subject is answered by the question it implies.

A conversation goes: the bot answers, and the person adds a thing about it rather than asking
again.

    **User:** im doing the food for a party
    **Bot:** ...
    **User:** theres eight of us at home
    **Bot:** Got it - there's eight of you at home.

    **User:** im sorting a trip for the summer
    **User:** were off to rome in september
    **Bot:** Got it - you are off to rome in september.

There is no question in the line, so nothing looks anything up, and the store says the line back.
The knowledge base does answer the question the detail implies, and it answers it well:

    "how much food for eight people"                       -> about 300 g each, 2.4 kg for eight
    "what should i know before a trip to rome in september" -> the Colosseum with a timed ticket
    "what can i cook for a vegetarian"                      -> chickpea curry, in 25 minutes
    "what do i need to know before buying an electric blanket" -> 20 minutes before bed

So this reads the kind of detail, writes the question that kind implies out of the person's own
words, and puts it to the knowledge base. Nothing is invented: every word of the reply comes from
a card that the implied question reached. If the knowledge base has nothing for the implied
question the module returns None and the line keeps whatever the composer had.

It runs where nothing better does: it replaces a receipt only, in greeting, which is what said
these lines back. A card, an entry or a light remark keeps its own turn.
"""
import re

from ..compose import fallback

# A statement, not an ask. A line with a question mark is read by the modules above this one, and
# one that opens on a wh-word, or on an auxiliary with a subject after it, is an ask with its
# subject left out ("what about my nan though", "can i freeze it") - a different job.
ASKS = re.compile(
    r"^\W*(?:how|what|whats|what's|which|when|where|who|why)\b"
    r"|^\W*(?:is|are|was|were|do|does|did|can|could|should|would|will|have|has|had|am)\s+"
    r"(?:i|you|we|they|it|that|this|there|he|she|any|my|your|his|her|their|the|a|an)\b"
    r"|\b(?:what|how|which|who|when|where) about\b", re.I)

# A diet the whole dish has to fit round: "hes vegetarian", "no dairy", "gluten free". Only the
# diet a dish is planned round, not the one food a person does not eat: `what can i cook without
# cheese` is not a question the knowledge base is keyed for, so it lands on a general dinner card -
# "no cheese though" over a frittata came back with mince and cabbage - and a card about another
# dish is worse than the receipt it replaced. A missing card is a job for the knowledge base, not
# for a reader here.
DIET_WORD = re.compile(
    r"\b(?P<diet>vegan|vegetarian|coeliac|celiac|dairy[- ]free|gluten[- ]free|pescatarian)\b", re.I)
# How many people the dish is for. A headcount is not a budget: "theres five of us at home" is the
# number of portions, and the card that answers it wants the same number.
COUNT = re.compile(
    r"\b(?:there(?:'?s| is| are)\s+)?(?P<n>\d+|one|two|three|four|five|six|seven|eight|nine|ten)"
    r"\s+(?:of us|people|adults|kids|children|guests|coming|more|extra|others|mouths)\b", re.I)
NUMBER = {"one": "one", "two": "two", "three": "three", "four": "four", "five": "five", "six": "six",
          "seven": "seven", "eight": "eight", "nine": "nine", "ten": "ten"}
# A place they are going to, and the month if they said it: "were off to lisbon in may".
GOING = re.compile(
    r"\b(?:off|going|heading|away|flying|driving|travelling|traveling)\s+to\s+"
    r"(?P<place>[a-z][a-z' -]{2,24}?)(?:\s+(?:in|on|for|next|at)\b|$)", re.I)
MONTH = re.compile(
    r"\b(january|february|march|april|may|june|july|august|september|october|november|"
    r"december|spring|summer|autumn|winter)\b", re.I)
# A thing they are turning over buying or starting: "im looking at an electric blanket".
CONSIDERING = re.compile(
    r"\b(?:looking at|thinking (?:of|about)|considering|about to (?:buy|get|order)|"
    r"going to (?:buy|get|order)|planning (?:to get|on getting))"
    r"\s+(?:an\s+|the\s+|some\s+|a\s+)?"
    r"(?P<thing>[a-z][a-z' -]{2,30}?)(?:\s+(?:for|in|because|to|but)\b|[.,!?]|$)", re.I)


# A headcount is a detail of a meal only when the turn above was about food. "theres eight of us at
# home" is said about the rent, the noise, the school run and a sleepless night as often as about
# dinner, and reading every one of them as a portion question hands a catering figure to somebody
# who has just said they cannot sleep. Lunch and breakfast are left out on purpose: the tiredness
# card says "no caffeine after lunch", which is a food word on a card that is not about food.
FOOD_WORDS = re.compile(
    r"\b(?:food|cook|cooking|cooked|eat|eats|eating|dish|recipe|meal|meals|menu|portion|"
    r"portions|serves|serving|dinner|roast|bake|baking|ingredient|ingredients|"
    r"cheese|chicken|pasta|rice|soup|salad)\b", re.I)


def _about_food(memory):
    """Whether the turn above was about food, which is what a headcount is a detail of."""
    said = []
    last = memory.get("last_answer") if isinstance(memory, dict) else None
    if isinstance(last, dict) and last.get("reply"):
        said.append(str(last["reply"]))
    for turn in reversed((memory or {}).get("turns") or []):
        if isinstance(turn, dict) and turn.get("bot"):
            said.append(str(turn["bot"]))
            break
    return any(FOOD_WORDS.search(one.lower()) for one in said)


def _asked(kind, detail, line):
    """The question this detail implies, written out of the line's own words, or None."""
    if kind == "dietword":
        return "what can i cook for a %s" % detail
    if kind == "count":
        if detail == "one more":
            return "how much food for one more person"
        return "how much food for %s people" % detail
    if kind == "going":
        month = MONTH.search(line)
        if month:
            return "what should i know before a trip to %s in %s" % (detail, month.group(1).lower())
        return "what should i know before a trip to %s" % detail
    if kind == "considering":
        return "what do i need to know before buying %s" % detail
    return None


def _the_read(clean):
    """The kind of detail this line adds, and the words it names, or (None, None)."""
    if not clean or "?" in clean or ASKS.search(clean.split(",")[0]):
        return None, None
    if len(clean.split()) > 16:
        return None, None
    match = DIET_WORD.search(clean)
    if match:
        return "dietword", match.group("diet").lower()
    match = COUNT.search(clean)
    if match:
        number = match.group("n").lower()
        if re.search(r"\b(?:more|extra|another)\b", clean):
            return "count", "one more"
        return "count", NUMBER.get(number, number)
    match = GOING.search(clean)
    if match:
        return "going", match.group("place").strip()
    match = CONSIDERING.search(clean)
    if match:
        thing = re.sub(r"^(?:(?:buying|getting|ordering)\s+)?(?:a|an|the)\s+", "",
                       match.group("thing").strip())
        return "considering", thing
    return None, None


def _a_real_answer(reply):
    """True when the knowledge base answered rather than hedging or filing the line."""
    said = " ".join(str(reply or "").split())
    if len(said) < 40:
        return False
    return not (fallback._is_a_hedge(said) or fallback._in_a_pool(said, (fallback.NEUTRAL,)))


def _said_already(memory):
    """Every line the bot has said in this conversation, in its flat form."""
    turns = (memory or {}).get("turns") if isinstance(memory, dict) else None
    said = []
    for turn in turns or []:
        if isinstance(turn, dict) and turn.get("bot"):
            said.append(" ".join(str(turn.get("bot")).split()))
    return said


def reply_for(text, memory):
    """The knowledge base's answer to the question this detail implies, or None."""
    clean = " ".join(str(text or "").lower().split())
    kind, detail = _the_read(clean)
    if not kind:
        return None
    if kind == "count" and not _about_food(memory):
        # A number of people is a portion question only over a meal: see FOOD_WORDS.
        return None
    question = _asked(kind, detail, clean)
    if not question:
        return None
    from ..modules import answers
    try:
        # The implied question is put to the entries on its own. Asking it with the conversation
        # behind it lets the never-repeat rule answer the second question with the reply to the
        # first ("Same answer, and it covers this: ..."), which is the filler this module exists
        # to replace. What has been said is checked below instead.
        reply = answers.respond(question, {})
    except Exception:
        return None
    if not _a_real_answer(reply):
        return None
    if kind in ("going", "considering"):
        # The card has to name the thing the person named, or it is a card about something else -
        # a question written by the bot can reach a near-miss entry.
        words = [word for word in re.findall(r"[a-z']{4,}", detail)]
        said = str(reply).lower()
        if words and not any(word in said for word in words):
            return None
    if " ".join(str(reply).split()) in _said_already(memory):
        # The card has been said already: saying it again is worse than the receipt.
        return None
    return reply
