"""One check for what the conversation already holds: is there a line of theirs that carried it?

Two things in this bot depend on the same question, and both used to answer it anew each time it
came up:

* a reply that claims the person has not said something ("You haven't told me how old she is"),
  and
* a recall ask ("how old did i say she was", "what size did i say") that has to find the value
  in the turns behind it.

The claim is the worse of the two. `shes 7 going on 8` was answered "Got it", and a turn later
"how old did i say she was" was answered "You haven't told me how old she is" - a flat
contradiction of the line above it. `mtl-26` gave `shes called jane and shes marrying tom` and
was later told "You haven't told me your sister's name". The reader for the slot had found
nothing, and nothing checked whether the chat held a word for it before saying it did not.

So the check lives here, once: `carried()` answers "which of their lines has a value of this
kind", and `put_right()` is the one gate every store reply goes through - if the reply denies a
thing the chat says, the line is handed back instead of the denial. The kinds are data
(`KINDS`), so a new kind is a line here rather than a rule in each module.

The subject matters only when the claim names one. "You haven't told me how old your daughter is"
has to find a line about the daughter; "how old did i say she was" is a pronoun, and a pronoun
points at the line just said, so the latest line of that kind is the one it means.
"""
import re

from ..compose import pick

# The values a line can carry, as the shape of the value and not the words of the ask: an age is
# a figure or the word old, a size is a figure with a unit or two figures with "by" between
# them, a when is a day or a month or a clock. Kept as families so a new wording of the value
# ("seven", "7", "7 and a half") is read without touching the reply.
MONTHS = (r"january|february|march|april|may|june|july|august|september|october|november|"
          r"december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec")
DAYS = r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|tonight|today"
UNITS = (r"kg|g|l|ml|kilo|kilos|kilogram|kilograms|gram|grams|lb|lbs|pound|pounds|ounce|ounces|"
         r"cm|mm|metre|metres|meter|meters|foot|feet|inch|inches|litre|litres|pint|pints")

KINDS = {
    # an age: a figure, or the words people give it in
    "age": re.compile(r"(?<!year )(?<!size )\b\d{1,3}\b|\b(?:\d{1,2}|one|two|three|four|five|"
                      r"six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|"
                      r"seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|"
                      r"eighty|ninety)\s*(?:years? old|years?|yrs?|yo)\b|\baged?\s+\d", re.I),
    # a name: the word that gives one, and a word after it
    "name": re.compile(r"\b(?:called|named|calls|name(?:'s| is| was)?)\s+[a-z]", re.I),
    # a day, a month, a birthday, a clock: "the 14th", "in june", "at 6am"
    "when": re.compile(r"\b(?:" + MONTHS + "|" + DAYS + r"|\d{1,2}(?:st|nd|rd|th)\b|\d{1,2}"
                       r"(?:[:.]\d{2})?\s*(?:am|pm)\b|\d{1,2}[:.]\d{2})\b", re.I),
    # a size or a weight or a length: "2kg", "3 metres by 4", "size 12"
    "size": re.compile(r"\b(?:\d+(?:\.\d+)?\s*(?:" + UNITS + r")|size\s+\d+|\d+\s*(?:by|x)\s*\d+)",
                       re.I),
    # how often: "three times a week", "every day", "once a month"
    "often": re.compile(r"\b(?:\d+\s+times|once|twice|three times|every\s+(?:day|week|month|"
                        r"morning|night|year)|a\s+(?:day|week|month)|most\s+(?:days|nights|"
                        r"weeks)|alternate)\b", re.I),
    # a sum of money, or a number kept for a plan
    "money": re.compile(r"£\s*\d|\b\d+(?:,\d{3})*\s*(?:pounds?|quid|k\b|grand)|\bbudget\b|"
                        r"\b\d{3,}\b", re.I),
    # a length of time
    "duration": re.compile(r"\b(?:\d+(?:\.\d+)?|an?|one|two|three|four|five|six|seven|eight|"
                           r"nine|ten|twelve|fifteen|twenty|half an)\s*(?:hours?|hrs?|minutes?|"
                           r"mins?|days?|weeks?|months?|years?)\b", re.I),
    # a count of people or things: a number and the things counted, "3 kids", "6 of us", "10
    # people". A bare number is not a count - "250 a month" is a sum, and reading it as a count
    # handed "how many months is that again" back the saving line instead of the sum it asked for.
    "count": re.compile(r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|"
                        r"twelve)\s+(?:(?:of|in)\s+)?(?:[a-z]{2,}s|people|children|men|women|"
                        r"us|them)\b", re.I),
    # a place
    "place": re.compile(r"\b(?:in|at|to|from|live|living|moved)\s+[A-Za-z][a-z]{2,}", re.I),
}

# The ask, as the kind of value it wants back. Ordered: the longer phrase first, because "how
# often" and "how long" both carry "how".
ASKS = (
    (re.compile(r"\bhow old\b|\bage\b|\bhow many years\b"), "age"),
    (re.compile(r"\bwhat(?:'s|s| is| was)?\s+(?:it |they |he |she )?called\b|\bname\b|"
                r"\bcalled\b"), "name"),
    (re.compile(r"\bwhen\b|\bwhat day\b|\bwhat date\b|\bwhat time\b|\bwhich day\b|\bwhat month\b"),
     "when"),
    (re.compile(r"\bhow often\b|\bhow many times\b"), "often"),
    (re.compile(r"\bsize\b|\bhow big\b|\bhow tall\b|\bhow heavy\b|\bhow long is\b|\bhow wide\b|"
                r"\bhow deep\b|\bhow far\b"), "size"),
    (re.compile(r"\bhow much\b|\bbudget\b|\bhow much did i\b|\bwhat did i say i (?:paid|spent)\b"),
     "money"),
    (re.compile(r"\bhow long\b|\bhow many (?:days|weeks|months|years|hours|minutes)\b"), "duration"),
    (re.compile(r"\bhow many\b|\bhow many of\b"), "count"),
    (re.compile(r"\bwhere\b"), "place"),
)

# The things a claim of not knowing can be about, so the subject of the claim is read off the
# denial itself: "You haven't told me how old your daughter is" is about the daughter, "what your
# dog is called" is about the dog.
CLAIM = re.compile(
    r"\b(?:you (?:haven'?t|have not) (?:told|said|mentioned|given)|you'?ve not (?:said|told|"
    r"mentioned)|you never (?:said|told|mentioned)|i don'?t have (?:your|the|their|his|her)\b[^.]*"
    r"\bfrom you|i (?:do not|don'?t) know (?:what|how|when|where|who)\b[^.]*\bsaid)",
    re.I)

# The words that name the value and not the thing it belongs to: "how heavy did i say it was" is
# not about heaviness, and "your sister's name" is about the sister. A subject made only of these
# is no subject at all, which is what tells the reader it may look at the line just said.
VALUE_WORDS = frozenset((
    "heavy", "weigh", "weighs", "weight", "big", "tall", "height", "wide", "deep", "far", "long",
    "length", "size", "old", "age", "aged", "name", "called", "date", "day", "month", "time",
    "often", "times", "cost", "costs", "price", "paid", "spend", "spent", "much", "many", "number",
    "count", "amount", "budget", "how", "what",
))

# A pronoun is not a subject to look for: it points at the line just said.
PRONOUNS = frozenset((
    "i", "me", "my", "we", "us", "our", "you", "your", "he", "him", "his", "she", "her", "they",
    "them", "their", "it", "its", "the", "a", "an", "that", "this", "one", "there",
))
STOP = frozenset((
    "the", "a", "an", "and", "or", "but", "it", "its", "is", "was", "were", "are", "am", "be",
    "to", "of", "for", "in", "on", "at", "by", "with", "about", "again", "said", "say", "saying",
    "told", "tell", "you", "i", "me", "my", "have", "has", "had", "do", "did", "does", "not",
    "what", "when", "where", "which", "who", "how", "many", "much", "old", "size", "long",
    "often", "times", "time", "that", "this", "your", "yours", "called", "name", "names",
    "remember", "remind", "know", "think", "get", "got", "there", "their", "his", "her", "they",
    "them", "we", "our", "us", "one", "ones", "haven", "havent", "isnt", "wasnt", "didnt",
    "dont", "doesnt", "never", "mentioned", "given", "should", "would", "could", "will", "shall",
    "can", "any", "some", "just", "so", "if", "then", "than", "as", "from", "out", "up", "down",
))


def _a_word(word):
    """A word that can be the subject of a claim: not a pronoun, not a verb of saying, and not a
    contraction ("haven't" is the claim itself, not a thing it is about)."""
    return (word not in STOP and word not in PRONOUNS and word not in VALUE_WORDS
            and len(word) > 2 and "'" not in word)

# The words a hand-back is written with. STYLE.md's plain register: their line, in their words,
# said once - it is theirs, not the bot's.
HAND_BACK = (
    "You said: \"{line}\".",
    "That one you did say: \"{line}\".",
    "You told me: \"{line}\".",
)


def _turns(memory):
    turns = (memory or {}).get("turns")
    if not isinstance(turns, list):
        return []
    return [turn for turn in turns if isinstance(turn, dict)]


def said_lines(memory):
    """What the person said, oldest first, as (turn number, line).

    The turn being answered is not in `memory["turns"]` yet, so this is the conversation so far.
    Numbered from one because that is how the deck and the person talk about turns.

    A question of theirs is not a line that says anything: asked `do i have a brother` after
    `do i have any brothers or sisters`, handing the question back is worse than the store's
    honest "you haven't told me about a brother yet". So an ask they typed is skipped here -
    the bot's reply to it is a line they can be answered from, not their own question.
    """
    said = []
    for number, turn in enumerate(_turns(memory), 1):
        line = str(turn.get("user") or "").strip()
        if not line or QUESTION.match(line) or line.endswith("?"):
            continue
        said.append((number, line))
    return said


def kind_of(text):
    """The kind of value this line asks for, or None.

    Read off the ask, not the subject: "how old did i say she was" and "what size did i say" are
    the same question about different values, and the reader below is the same for both.
    """
    low = " ".join(str(text or "").lower().replace("\u2019", "'").split())
    if not low:
        return None
    for pattern, kind in ASKS:
        if pattern.search(low):
            return kind
    return None


# A rate, not a length of time: "£250 a month" is a sum per month, and read as a duration it
# answered "how many months is that again" with the saving line instead of the sum it asked for.
A_RATE = re.compile(r"\b(?:\d[\d,.]*|one|two|three|four|five|six|seven|eight|nine|ten|eleven|"
                    r"twelve)\s*(?:times?\s*)?(?:a|an|per|/|each|every)\s*(?:month|week|year|day|"
                    r"hour)\b|£?\s*\d[\d,.]*\s*(?:pounds?|quid|grand|k)?\s*(?:a|an|per|/|each|"
                    r"every)\s*(?:month|week|year|day|hour)\b", re.I)
A_TIMED_KIND = ("duration", "count")


def carries(kind, line):
    """Whether this line holds a value of that kind."""
    pattern = KINDS.get(kind or "")
    if not pattern:
        return False
    said = str(line or "")
    if kind in A_TIMED_KIND:
        said = A_RATE.sub(" ", said)
    return bool(pattern.search(said))


def _about(text):
    """The words a claim names as its subject, none of them pronouns."""
    words = re.findall(r"[a-z']+", " ".join(str(text or "").lower().split()))
    return [word for word in words if _a_word(word)]


def _said_words(text):
    """The words of a line that could name the thing it is about, longest first."""
    words = re.findall(r"[a-z']+", " ".join(str(text or "").lower().split()))
    out = []
    for word in words:
        if len(word) > 1 and word not in STOP and word not in PRONOUNS \
                and word not in VALUE_WORDS and "'" not in word and word not in out:
            out.append(word)
    return out


def _mentions(line, words):
    """Whether the line mentions any of these words, in any of its forms.

    "how often did i say i go" has to find "im going three times a week", so a plural, a
    possessive and the -ing and -ed forms all count as the word itself. The word has to start a
    new word, so "go" does not find "dog", and "a dog walk every day" is not about the gym.
    """
    low = " ".join(str(line or "").lower().split())
    for word in words:
        if re.search(r"\b" + re.escape(word) + r"(?:s|es|'s|ing|ed)?\b", low):
            return True
    return False


def kinds_for(kind, ask):
    """The kinds a value asked for could be in, the likeliest first.

    "how much" is a sum far more often than an amount, but it is an amount when the chat said the
    thing in grams or litres: "i usually do 500g of mince for 4" then "and how much mince was that"
    was handed the search hedge while the 500g was two turns up. A weight or a volume is a size,
    so the money kind is followed by the size kind and nothing else changes.
    """
    if kind == "money" and re.search(r"\bhow much\b", str(ask or ""), re.I):
        return ("money", "size")
    return (kind,)


def carried(memory, kind, about=(), window=None, prefer=(), after=0):
    """The latest line of theirs that carried a value of this kind, or None.

    `about` is the subject a claim named: a line has to mention it, else nothing of that kind
    counts. `prefer` is what the ask itself named ("what size did i say the chicken was" is about
    the chicken): a line that says one of those words wins over one that only carries the value,
    so a chat that has said both "three times a week" and "every day" answers the gym question
    with the gym line. `after` leaves out the lines before a turn, which is how a pronoun is
    followed back to what it points at.
    """
    lines = said_lines(memory)
    if window:
        lines = lines[-window:]
    if after:
        lines = [pair for pair in lines if pair[0] > after]
    hits = [(number, line) for number, line in lines if carries(kind, line)]
    if not hits:
        return None
    if about:
        for number, line in reversed(hits):
            if _mentions(line, about):
                return number, line
    if prefer:
        best, best_number, best_line = 0, None, None
        for number, line in hits:
            score = sum(1 for word in prefer if _mentions(line, (word,)))
            if score >= best:
                best, best_number, best_line = score, number, line
        if best:
            return best_number, best_line
    if about:
        # The thing named is not in any line of this kind, so there is nothing here about it.
        return None
    return hits[-1]


def _pointing_back(memory, about):
    """Whether a line of the chat names what the ask names, so the ask is pointing at it.

    "back to the bedroom, what size was it again" names the bedroom and the chat has the bedroom,
    so the one size line in the chat is what it means. "and remind me where we said wed stay"
    names staying and the chat never said it, so the one place line in the chat is not that.
    """
    if not about:
        return False
    return any(_mentions(line, about) for _, line in said_lines(memory))


def carried_alone(memory, kind):
    """The one line of the chat that carries a value of this kind, when there is exactly one.

    A chat that has said one size and nothing else has answered "what size was it again" whatever
    the ask calls the thing - the wallpaper chat's "back to the bedroom, what size was it again" is
    about the 3 metres by 4 it gave a few turns before. Two values of the kind and there is nothing
    to hand back, so nothing is guessed.
    """
    hits = [line for _, line in said_lines(memory) if carries(kind, line)]
    return hits[0] if len(hits) == 1 else None


def hand_back(line, memory=None, text=""):
    """Their own line, quoted, in the plainest words there are for it."""
    low = " ".join(str(line or "").split())
    if not low:
        return None
    return pick(HAND_BACK, memory or {}, low + " " + str(text or "")).format(line=low)


def a_claim(reply):
    """The part of a reply that claims the person never said something, or None."""
    found = CLAIM.search(str(reply or ""))
    if not found:
        return None
    return str(reply)[found.start():]


# A line that asks for something back: the cues that make it a recall ask and not a question of
# its own. Kept narrow - "again" alone is a request to hear the whole answer, which the repeat
# readers own.
# "what size was it again", "how long again" and "back to the bedroom, what was it": the cue can
# be the "again" alone, because the kind of value asked for is checked separately.
RECALL = re.compile(r"\b(?:did i (?:say|tell|mention)|what did i say|what was it i said|"
                    r"remind me|what did we say|how did i say|again)\b", re.I)


def _values(kind, text):
    """The values of a kind one line carries, as plain words, for telling two lines apart."""
    pattern = KINDS.get(str(kind or ""))
    if pattern is None:
        return set()
    low = " ".join(str(text or "").lower().split())
    out = set()
    for match in pattern.finditer(low):
        piece = " ".join(re.sub(r"[^a-z0-9. ]", " ", match.group(0)).split())
        if piece:
            out.add(piece)
    return out


def _the_line_the_ask_names(text, memory):
    """The line a recall ask means, when it names the thing that line is about.

    `how often did i say i go` names the gym, so the dog walk said after it is not the line meant.
    Only an ask about their own words or habit can name a line this way; every other line is the
    store's to answer as it likes, and None says so.
    """
    low = " ".join(str(text or "").lower().replace("\u2019", "'").split())
    if not (RECALL.search(low) or their_own_words(low)):
        return None, (), None
    kind = kind_of(low)
    named = _said_words(low)
    if not kind or not named:
        return None, named, None
    return kind, named, carried(memory, kind, (), prefer=named)


def gives_the_named_value(text, memory, reply):
    """Whether the reply gives the value of the line the ask names, not another line's value."""
    kind, named, found = _the_line_the_ask_names(text, memory)
    if not found:
        return False
    return bool(_values(kind, reply) & _values(kind, found[1]))


def another_line_was_asked_for(text, memory, reply):
    """True when a recall ask that names something was answered from a different line.

    A recall ask says which line it means: `how often did i say i go` is about the gym, not about
    the dog walk said after it. The store answered that line with "You also walk the dog every
    day." - a line of the right kind, and not the one the ask named - so a reply that hands back
    the line the ask names is the answer to the question that was asked. A reply that gives the
    value the named line gives is answering from that line, however few of its words it repeats:
    `and when does he start again` was answered "In September." and that is the same September.
    """
    kind, named, found = _the_line_the_ask_names(text, memory)
    if not found:
        return False
    if _mentions(str(reply or ""), named):
        return False
    return not gives_the_named_value(text, memory, reply)


HAND_BACKS = re.compile(r"^(?:You said|That one you did say|You told me)\b", re.I)


def a_misquoted_line(reply, memory, ask=""):
    """The line to hand back when the reply quotes a line that does not carry what was asked.

    `what day did i say my appointment was` was answered "You said: \"i finally got my hospital
    appointment through\"" - a real line of theirs, quoted back, with no day in it at all, while
    `its on the 12th of march at half nine` sat two turns up. A quotation is only an answer when
    the line it quotes carries the kind of value the ask is asking about; when another line does,
    that line is the answer and this returns it.
    """
    text = str(reply or "")
    if not HAND_BACKS.match(text):
        return None
    quoted = re.search(r'"([^"]{2,300})"', text)
    kind = kind_of(ask)
    if not quoted or not kind:
        return None
    if _values(kind, quoted.group(1)):
        return None
    found = carried(memory, kind)
    if not found:
        return None
    if " ".join(found[1].lower().split()) == " ".join(quoted.group(1).lower().split()):
        return None
    return hand_back(found[1], memory, a_claim(text) or "")


def answer_for(text, memory):
    """A recall ask nothing else answered: their own line, handed back, when it carries the value.

    "what size did i say", "when did i say we fly" and "how often did i say i go" were handed to
    the search hedge while the size, the date and the number of times were in the line above.
    This is the same check as `put_right`, asked from the other side: the kind comes from the ask,
    and the line comes from the chat.
    """
    low = " ".join(str(text or "").lower().replace("\u2019", "'").split())
    if not low or not RECALL.search(low):
        return None
    kind = kind_of(low)
    if not kind:
        return None
    about = _about(low)
    # Nobody is named in the ask ("what size did i say", "how often did i say i go"), so the line
    # it means is the one that says a word the ask used - the gym line, not a dog walk a turn
    # later - and a chat that names nothing of the kind falls back to the newest line of that kind.
    named = _said_words(low)
    found = carried(memory, kind, about) if about else (
        carried(memory, kind, (), prefer=named)
        or (None if named else carried(memory, kind, (), window=3)))
    if not found and (not named or _pointing_back(memory, about)):
        # "the only line of that kind" answers an ask that points at the chat - one that names
        # nothing ("what size did i say") or names something the chat has said ("back to the
        # bedroom, what size was it again"). An ask that names something the chat never said
        # ("where we said wed stay") is not answered by the one place line in it.
        alone = carried_alone(memory, kind)
        found = (len(said_lines(memory)), alone) if alone else None
    if not found:
        return None
    return hand_back(found[1], memory, low)


# A question that asks for a value of one of those kinds, whatever its wrapper: "how old is she",
# "what size was it", "when do we fly again". Used only when nothing else answered the line, so a
# card or an entry that fits still answers it.
# Their ask, in the shapes people type it: a wh-word, or the auxiliary a yes/no question opens
# with ("do i have a brother" is a question even with no question mark on the end). A line of
# theirs that is a question says nothing to answer a later one from - handing it back ("That one
# you did say: \"do i have any brothers or sisters\"") is worse than saying they have not said.
QUESTION = re.compile(r"^\s*(?:and|so|but|or|oh|also|then)?\s*(?:how|what|when|where|which|who|"
                      r"whose|why|do|does|did|is|are|was|were|am|can|could|should|would|will|"
                      r"shall|have|has|had|any)\b", re.I)


# An ask about what the person themselves said or does is a question about their own earlier
# words, and their line answers it even when the knowledge base has something to say about the
# subject: "how often do i go" after "i go to the gym three times a week" is their three times, not
# the three-sessions-a-week advice card, and "what size did i say the door was" is the 3 metres.
THEIR_OWN_WORDS = re.compile(r"\b(?:(?:did|do|does|have|had|was|were) i (?:say|tell|mention|said|"
                            r"go|use|have|had|get|got|buy|bought|pay|paid|book|pick|choose)|"
                            r"remind me|what was my|what did i|where did (?:i|we) say|again)\b", re.I)


def their_own_words(text):
    """Whether the ask is about something the person themselves said or does."""
    return bool(THEIR_OWN_WORDS.search(" ".join(str(text or "").lower().split())))


# An ask that wants a plan, a guess or a sum worked out is not a recall of a figure already said:
# "how often should i be checking the gauge", "how many portions do i need for 6 people" and "how
# much can i save then" are questions of their own, and the newest line of the kind ("i top it up
# most weeks", "having 6 people over", "im trying to save 300 pounds a month") is not their answer.
# Quoting it back tells the person they already said the thing they are asking about.
NOT_A_RECALL_ASK = re.compile(r"\b(?:should|could|would|will|shall|might|can|may|roughly|maybe|"
                             r"probably|need|needs|got to|have to|havent got|is it worth|better off|"
                             r"do you think|any (?:idea|chance)|recommend)\b", re.I)

# The kinds a plain question is answered from their own line for. A plain "what time should it go
# in" or "how long do i roast it" is a cooking question far more often than a recall, so a value of
# those kinds is handed back only when the ask says it is asking (RECALL: "did i say", "remind me",
# "again"), never on the strength of the kind alone.
NOT_A_PLAIN_ASK = ("when", "duration")


def from_the_line(text, memory):
    """The answer a line of theirs holds for this question, when nothing else had one.

    `remind me how old she is` and `how old is she`, two turns after "shes 7 going on 8", were both
    handed the search hedge: the store's slot reader files an age only when it is told whose it is
    ("my daughter is 6"), and nothing read the figure that was on the screen. The kind is read
    from the question and the line from the chat, exactly as `answer_for` does it; the difference
    is only that no recall cue is needed, because the caller has already found that nothing else
    answered.
    """
    low = " ".join(str(text or "").lower().replace("\u2019", "'").split())
    if not low or not QUESTION.match(low):
        return None
    kind = kind_of(low)
    if not kind or kind in NOT_A_PLAIN_ASK:
        return None
    if NOT_A_RECALL_ASK.search(low):
        # A question that wants something worked out is not answered by the last line of that
        # kind: see NOT_A_RECALL_ASK.
        return None
    about = _about(low)
    named = _said_words(low)
    found = None
    for kind in kinds_for(kind, low):
        found = carried(memory, kind, about) if about else (
            carried(memory, kind, (), prefer=named)
            or (None if named else carried(memory, kind, (), window=3)))
        if found:
            break
        if not named or _pointing_back(memory, about):
            alone = carried_alone(memory, kind)
            found = (len(said_lines(memory)), alone) if alone else None
            if found:
                break
    if not found:
        return None
    return hand_back(found[1], memory, low)


def put_right(reply, memory, ask=""):
    """The reply with a false claim of not knowing replaced by their own line, or None.

    One gate, and it is the whole rule: a reply may say the bot does not know a thing only if no
    line of theirs carries it. When one does, the line is handed back - it cannot contradict the
    conversation, and it is the answer they asked for. A claim with nothing behind it in the
    chat is left exactly as it was, because then it is true.
    """
    claim = a_claim(reply)
    if not claim:
        return None
    asked = kind_of(claim) or kind_of(ask)
    kinds = (asked,) if asked else ("age", "name", "when", "size", "money", "often", "duration")
    named = _about(claim)
    # The claim can leave the thing out and the ask can name it ("You haven't told me what you
    # weigh" for "how heavy did i say it was"), so either line can say what to look for.
    subject = named or _about(ask)
    # The claim can name something the ask never did: `what did i say her names age was` in a chat
    # about a dog was answered "You haven't told me how old your partner is", taking the name off
    # the turn three lines up while `shes about 3` was the age they wanted. The name is then the
    # store's guess at the subject rather than the ask's, so the line that answers is not held to
    # coming after it - see the pronoun branch below.
    named_here = bool(named) and _mentions(str(ask or ""), named)
    # A pronoun points at the line just said, so a claim that names nobody only looks at the
    # last few lines: "how old did i say she was" is about the line above it, not about the one
    # figure anywhere in a long chat that happens to be a number.
    window = None if subject else 3
    for kind in kinds:
        found = carried(memory, kind, subject, window=window)
        if found:
            return hand_back(found[1], memory, claim)
        if subject and not named:
            # The claim named nobody and only the ask's own words were left to look for, and they
            # named no line: then the line just said is the one it means. A claim that does name
            # someone ("your sister's name") is not given this, because a line about the dog is
            # not about the sister.
            found = carried(memory, kind, (), window=3)
            if found:
                return hand_back(found[1], memory, claim)
        elif named:
            # No line of this kind names the thing the claim is about, but a line with a pronoun in
            # it may still be about it: "my daughter keeps saying shes too old" then "shes 7 going
            # on 8" is the daughter's age, and "whats my sisters name" after "shes called jane" is
            # her name. Only a line that comes after the thing was introduced counts, so a pronoun
            # about somebody else earlier in the chat is not taken for it, and a line with no
            # pronoun in it at all ("weve got a cat called tilly") is never taken.
            introduced = [number for number, line in said_lines(memory) if _mentions(line, named)]
            found = carried(memory, kind, ("she", "he", "they"),
                            after=max(introduced or [0]) if named_here else 0)
            if found:
                return hand_back(found[1], memory, claim)
    if named and not asked:
        # No kind was named, so there is no telling which value would satisfy the claim: a line
        # that mentions the thing is what the person has, and handing it back beats denying it.
        # When a kind was named and no line carries it ("how old your sister is", with the sister's
        # name but no age anywhere), the denial is true and is left alone.
        for number, line in reversed(said_lines(memory)):
            if _mentions(line, named):
                return hand_back(line, memory, claim)
    return None
