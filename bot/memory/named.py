"""A follow-up that names one thing takes the ask before it with it.

"my mum is coming to stay" / "what should i cook" / "and a pudding" is a person carrying on the
same request about a new thing: what they want is pudding ideas. The knowledge base has the
answer ("ideas for pudding" gives the crumble), but the line on its own names a pudding and asks
nothing, so nothing in it is answerable and the turn fell to the small talk: "Thanks for telling
me - I'm here if you want to dig into any of that", which is the one reply a follow-up must not
get.

This reads the line as the ask it carries: the thing it names, put back into the request the
previous line made. The rule is narrow on purpose:

* the line must be a thing and nothing else - an optional "and"/"or"/"also"/"plus" or
  "what about"/"how about" in front, then a short noun phrase, with no verb, no question of its
  own and no word pointing back at the last subject ("and what about it", "and how long");
* the line just before it must have asked for suggestions ("what should i cook", "what can i
  make", "any ideas"), because that is the ask a thing can be carried into;
* the phrase it hands back is "ideas for <thing>", and the caller uses it only when the line
  itself has no answer of its own - so a line that answers today still answers tomorrow.
"""
import re

from . import holds as earlier
from .topics import carried_topic as the_carried_topic, is_ack, subject as the_subject
from ..compose import trouble
from ..compose.badnews import reads_as_bad_news
from ..understanding import kinds

# A line that opens on one of these carries the last answer on rather than reacting to it:
# "we got a puppy last week" / "and at night" is the follow-up the night answer is for, and it
# read as an acknowledgement because the word "night" is a greet word.
CONTINUES = re.compile(r"^\s*(?:and|or|plus|also|but|then)\b", re.I)


def _answers_the_bot(text):
    """True when the line is a short reply to the bot's last turn, not a continuation of it."""
    return bool(is_ack(text)) and not CONTINUES.match(str(text or ""))


# The lead-ins that say "the same ask, this other thing": they carry nothing of their own.
LEAD = re.compile(r"^\s*(?:(?:and|or|also|plus|ok|okay|then|so)\b[\s,]*)*"
                  r"(?:(?:what|how)\s+about\s+|and\s+what\s+about\s+|what\s+of\s+)?", re.I)
# The articles and quantifiers a thing is said with: "a pudding", "some bread", "the cake".
QUANT = re.compile(r"^\s*(?:a|an|the|some|any|another|one|two|three|more|other)\s+", re.I)
# A line that opens with one of these is asking something of its own, not naming a thing. The
# wh-words are read with the "s" people type without an apostrophe ("wheres my keys", "hows it
# done"), because "wheres the remote" is a where-question and not the name of a thing: read as a
# bare thing it was asked of the film answer and the film list came back as "Nothing separate for
# the remote - it is the same advice: *Groundhog Day* for comedy...".
ASKING = re.compile(r"^\s*(?:(?:what|how|where|when|which|who|why)(?:'s|s)?\b|"
                    r"(?:can|could|should|do|does|did|is|are|was|were|have|has|will|would|"
                    r"shall|may|might)\b)", re.I)
# Words that point back at the last thing instead of naming a new one: those are the follow-ups
# `topics` and the composer already answer ("what should i do with them").
POINTS_BACK = frozenset("""it its it's them they that this these those there one ones
him her his hers their theirs he she""".split())
# A word that asks for an answer names what the person wants, not what the line is about, so it
# is not a thing to carry into the ask before it. "how long do i boil an egg" / "any tips" became
# "what about tips", which is a line about tipping, and the person got the restaurant table: the
# words here are the same plea the composer answers with "what have you got so far", and no
# knowledge entry that happens to key one of them is what the person asked about. "ideas" and
# "hints" are the same ask in other words: after "i need to save money", "any hints" was written
# out as "what about hints" and the turn came back as "I'm listening - say more if it helps".
ASKS_FOR_AN_ANSWER = frozenset("""tip tips advice suggestion suggestions pointer pointers
recommendation recommendations trick tricks guidance idea ideas hint hints""".split())
# A verb, so the line is a sentence of its own: "and my mum is coming", "and it hurts".
VERBS = frozenset("""is are was were am be been being have has had do does did done
will would shall should can could may might must
go going goes went come coming comes came get getting got make making made
take taking took need needs needed want wants wanted like likes liked
know knows knew think thinks thought feel feels felt hurt hurts hurting
eat eats eating ate drink drinks drinking work works working play plays playing
happen happens happened start starts started stop stops stopped try tries tried
give gives gave put puts keep keeps kept buy buys bought sell sells sold
live lives lived move moves moved stay stays stayed visit visits visited
rain rains raining snow snows snowing""".split())
# A line that takes something back names nothing new: "im going to lisbon in may" / "forget the
# whole trip" is the person dropping the trip, and read as a bare thing it went to the knowledge
# base as "what about forget the whole trip" and came back with the memory-science entry ("Most
# forgetting is not a lost file ..."). The store is the part that knows how to drop a subject,
# so these lines are left to it.
TAKES_BACK = frozenset("""forget forgets forgot forgetting drop drops dropped dropping
scratch scratches scratched strike strikes struck remove removes removed delete deletes deleted
cancel cancels cancelled canceling bin bins binned ignore ignores ignored discard discards
discarded""".split())
# A suggestion ask: the request a named thing can be carried into.
ASKED_FOR_IDEAS = re.compile(
    r"\b(?:what|which)\s+(?:should|could|can|shall|would)\s+(?:i|we)\s+"
    r"(?:cook|make|do|have|eat|get|buy|watch|read|wear|give|bring|take|serve|bake|plan)\b|"
    r"\b(?:what|which)\s+(?:do|did)\s+(?:i|we)\s+(?:cook|make|have|eat)\b|"
    r"\bwhat\s+(?:can|could)\s+(?:i|we)\s+(?:cook|make|have|eat|do|get)\b|"
    r"\bany\s+(?:ideas?|suggestions?)\b|\bideas?\s+for\b|"
    r"\bwhat\s+would\s+you\s+(?:suggest|recommend|cook|make|do)\b|"
    r"\bsuggest(?:ions?)?\s+(?:for|something)\b", re.I)
# The longest a thing can be and still be a thing: a noun phrase, not a clause.
MOST_WORDS = 4
# A first-person word, or the word the correction is spoken with: "no i said to my landlord" is
# a correction about a sentence, and the food behind the "no" is not a food at all.
SAID_NOT_A_FOOD = frozenset("""i me we us you he she they it its said says say saying meant
means mean asking asked told tell telling sorry actually really""".split())
# A courtesy after the "no" is the person answering the bot, not an empty shelf: "no thanks",
# "no ta", "no cheers". Read as a food it turned the commonest way of turning an answer down into
# a kitchen question, and "no thanks" after the film list or the tap answer came back as "Quick:
# tuna pasta in 15, chickpea curry in 25, or a lentil dhal" - dinner offered to someone who had
# just said no to it. Nothing is cooked without a thank-you, so the word is not a thing.
A_THANK_YOU = frozenset("""thanks thank thankyou thank-you thx ta cheers mate love hun""".split())
# A part never opens on a preposition: "of the food", "in rome" is the ask without its noun.
PREP = frozenset(("of", "in", "on", "at", "for", "from", "with", "about", "to", "by"))


def _previous_ask(memory):
    """The line the person put before this one, when it asked for suggestions."""
    turns = [t for t in (memory or {}).get("turns") or [] if isinstance(t, dict)]
    if not turns:
        return ""
    said = str(turns[-1].get("user") or "")
    return said if ASKED_FOR_IDEAS.search(said) else ""


# The lead-ins that can come before a line that takes something back without changing what it is:
# "and forget the chicken", "ok, drop it".
TAKE_BACK_LEAD = re.compile(r"^\s*(?:(?:and|or|so|ok|okay|now|then)\b[\s,]*)*"
                            r"(?:(?:please|just|actually)\s+)*", re.I)
# The whole-line retractions that name nothing at all: "take that back", "never mind".
TAKE_BACK_WHOLE = ("take that back", "takes that back", "never mind", "scratch that", "forget it",
            "forget that", "forget about it", "drop it", "drop that")


def takes_back(text):
    """True when the line is the person taking something back off the record.

    "forget the chicken", "drop the whole trip", "take that back", "never mind": the line gives no
    fact and asks nothing, so its reply is an acknowledgement rather than an answer. A reader that
    hands the last thing said back - "say that again", "repeat that" - has nothing to repeat in it,
    and handing it back twice ("Sure - Got it - forget the chicken.") is worse than the answer
    before it.
    """
    said = " ".join(str(text or "").strip().lower().split())
    if not said:
        return False
    rest = TAKE_BACK_LEAD.sub("", said).strip(" .,;:!?")
    if not rest:
        return False
    if rest.startswith(TAKE_BACK_WHOLE):
        return True
    # What is taken back is named in a few words ("forget the whole trip"); longer than that and
    # the verb is doing its ordinary work ("drop the kids at school at eight").
    if len(rest.split()) > 6:
        return False
    first = re.split(r"[\s,]+", rest, 1)[0].strip(".,;:!?")
    return first in TAKES_BACK


# The frames an ask about one thing is said with. They carry nothing of their own: what is left
# after them is the thing the line is about. One list rather than one pattern per wording, because
# "who is emma" and "tell me about emma" are the same question - the chat holds Emma, and the
# person wants what it holds - and main answered the first and punted on the second, the third and
# the fourth ("what about emma", "do you remember emma", "remind me who emma is").
THE_ASKING = (
    re.compile(r"^\s*(?:and|also|so|ok|okay|but|then|well|oh)\b[\s,]*", re.I),
    re.compile(r"^\s*(?:can|could|would)\s+you\s+(?:please\s+)?", re.I),
    re.compile(r"^\s*(?:please\s+)?(?:tell|remind|show)\s+me\s+(?:again\s+)?"
               r"(?:about|of|who|what)\s+", re.I),
    re.compile(r"^\s*(?:tell|remind)\s+me\s+", re.I),
    re.compile(r"^\s*(?:anything|something|more|a\s+bit)\s+about\s+", re.I),
    re.compile(r"^\s*(?:what|how)\s+about\s+", re.I),
    # "same for my daughter", "same as my son": a person named as the next one of the same kind,
    # which the store already answered by saying the noun back ("Noted: your daughter.").
    re.compile(r"^\s*same\s+(?:for|as)\s+", re.I),
    re.compile(r"^\s*what\s+of\s+", re.I),
    re.compile(r"^\s*(?:do|did)\s+you\s+(?:remember|know|recall)\s+(?:about\s+|the\s+)?", re.I),
    re.compile(r"^\s*(?:what\s+is|what's|whats|what)\s+", re.I),
    re.compile(r"^\s*who(?:'s|s| is| was)\s+", re.I),
)
# The words a question is ended with, which say nothing about the thing asked about.
THE_ASKING_TAIL = re.compile(
    r"\s+(?:again|then|though|please|now|too|already|anyway|honestly|is|was|are|were)\s*$", re.I)
# The same ask with the verb at the end: "remind me who emma is", "who my sister is". The
# "who" frame below only knows the other order ("who is emma"), and with the verb last the
# whole line stayed in one piece and named nothing.
WHO_X_IS = re.compile(r"^(?:(?:and|also|so|ok|okay|then)\s+)?who\s+(?P<thing>.+?)\s+(?:is|was)\s*$",
                      re.I)
# The longest a thing asked about can be: a name, or a relation and its article ("my sister").
MOST_WORDS_ASKED_ABOUT = 3
# A person pointed at rather than named. "him" and "her" and "them" are not things, so the checks
# below threw them away and the line that says only one of them named nobody: "what about him"
# after "my son jack is 6" reached the search hedge.
POINTED_AT = frozenset(("him", "her", "them", "they", "that one", "this one", "those two",
                        "the two of them", "both of them", "the pair of them"))


# A word that makes what is left a sentence rather than a thing: "what is pasta" leaves "is
# pasta" and "i like pasta" was never framed at all, and neither is a thing asked about.
THE_ASKING_VERB = re.compile(
    r"^\s*(?:is|are|was|were|am|be|been|being|do|does|did|should|could|would|will|shall|can|may|"
    r"might|must|have|has|had)\b", re.I)


def the_one_asked_about(text):
    """The one thing a framed line asks about: "tell me about emma" -> "emma".

    The asking is taken off the front, one frame at a time, and what is left has to be a thing
    and nothing else: "who is meg on eastenders" leaves "meg on eastenders", which is a programme
    and not a name the chat holds, so it is not handed back. This only says what the line is
    about; whether the chat holds it is for the caller to check.
    """
    said = " ".join(str(text or "").replace("\u2019", "'").split()).strip(" ?!.,;:")
    if not said:
        return ""
    last_verb = WHO_X_IS.match(said)
    if last_verb:
        said = last_verb.group("thing").strip(" ?!.,;:")
    changed = True
    while changed:
        changed = False
        for frame in THE_ASKING:
            new = frame.sub("", said, count=1).strip(" ?!.,;:")
            if new and new != said:
                said = new
                changed = True
        trimmed = THE_ASKING_TAIL.sub("", said).strip(" ?!.,;:")
        if trimmed and trimmed != said:
            said = trimmed
            changed = True
    if said.lower() in POINTED_AT:
        return said
    if len(said.split()) > MOST_WORDS_ASKED_ABOUT:
        return ""
    if THE_ASKING_VERB.match(said):
        return ""
    if any(word.lower() in VERBS for word in said.split()):
        return ""
    if not _looks_like_a_thing(said):
        return ""
    return said


def thing(text):
    """The thing the line names on its own ("pudding", "a starter"), or "".

    The line has to be that and nothing else: an ask of its own, a verb, a word pointing back at
    the last subject, or a word that asks for advice all mean the line is not a bare name.
    """
    said = " ".join(str(text or "").strip().split())
    if not said or len(said.split()) > MOST_WORDS + 4:
        return ""
    if ASKING.match(said):
        # "what about a pudding" is the one exception: the ask is the lead-in, not a question.
        if not re.match(r"^\s*(?:what|how)\s+about\b", said, re.I):
            return ""
    rest = LEAD.sub("", said)
    rest = QUANT.sub("", rest.strip(" .,;:!?"))
    rest = rest.strip(" .,;:!?")
    if not rest:
        return ""
    words = [w for w in re.split(r"[\s,]+", rest) if w]
    if len(words) > MOST_WORDS:
        return ""
    for word in words:
        bare = word.lower().strip(".,;:!?")
        if (bare in POINTS_BACK or bare in VERBS or bare in TAKES_BACK
                or bare in ASKS_FOR_AN_ANSWER
                or bare in ("what", "how", "why", "when")):
            return ""
        if not re.search(r"[a-z]", bare):
            return ""
    if not _looks_like_a_thing(" ".join(words)):
        return ""
    return " ".join(words)


def _looks_like_a_thing(phrase):
    """A thing, not a sentence: it must not be a bare pronoun or a word with a digit in it, and it
    must have at least one word of real length (a name or a noun, not "a bit")."""
    words = phrase.split()
    if not words:
        return False
    if any(re.search(r"\d", word) for word in words):
        return False
    return any(len(re.sub(r"[^a-z]", "", word.lower())) >= 3 for word in words)


# The naming word: the frame a name is put right in ("no its called tim", "sorry, she's called
# dana"), and never part of the name itself. It is also what tells a correction of a name apart
# from a thing the kitchen has not got: a food is not "called" anything, and reading "no hes
# called max" as a missing food turned the line into "what can i make without hes called max",
# which the dish table answered with the cold-calling entry.
NAME_WORD = re.compile(r"\b(?:called|named|names?)\b|name'?s", re.I)
# The words that can stand between the naming word and the name itself ("his names not dana",
# "the name is jake"), and the ones a name can trail ("call him max instead").
IN_FRONT_OF_THE_NAME = frozenset("is not was isnt aint it its really actually".split())
AFTER_THE_NAME = frozenset("instead now then actually please ok okay".split())


def carries_a_name(text):
    """True when the line, or a value from it, is said with the naming word in it."""
    return bool(NAME_WORD.search(str(text or "")))


def the_name_in(value):
    """The name a value carries, or "" when the value is not said with the naming word.

    A correction says the name inside the frame that names it - "no its called tim" hands over
    "called tim" - and the frame is not part of the name: kept whole, the cat was filed as
    "Called tim" and said back as "I'll call the cat Called tim". Only a value with the naming
    word in it is touched, so an ordinary value ("tim", "tree nuts") is handed back untouched
    by the caller, which is the turn's own value and not this reader's.
    """
    text = " ".join(str(value or "").replace("\u2019", "'").split())
    if not carries_a_name(text):
        return ""
    words = text.split()
    for index, word in enumerate(words):
        bare = word.strip(".,!?;:").lower()
        if bare not in ("called", "named", "name", "names", "name's"):
            continue
        rest = [one for one in words[index + 1:]
                if one.strip(".,!?;:").lower() not in IN_FRONT_OF_THE_NAME]
        while rest and rest[-1].strip(".,!?;:").lower() in AFTER_THE_NAME:
            rest.pop()
        if rest:
            return " ".join(rest).strip(" .,!?;:")
        return ""
    return ""


# The question the bot asks when a new animal or a new person turns up without a name. A line
# that answers it is the answer to that question and nothing else: "hes called biscuit" a turn
# after the bot asked is the puppy's name, and the biscuit is not something in the kitchen.
A_NAME_ASK = re.compile(
    r"\bwhat(?:'s|s| is| are| was)?\s*(?:it|its|he|she|they|them|the|your|his|her|their)?\s*"
    r"(?:called|named)\b"
    r"|\bwhat(?:'s|s| is)?\s+(?:its|his|her|their|your)\s+names?\b"
    r"|\bwhat\s+do\s+(?:you|they)\s+call\b", re.I)
# The words a bare answer to that question can be said with ("just biscuit", "biscuit i think").
JUST_A_NAME = re.compile(
    r"^\W*(?:(?:its|it's|hes|he's|shes|she's|theyre|they're|just|actually|his|her)\s+)*"
    r"(?P<name>[A-Za-z][A-Za-z'-]{1,20})"
    r"(?:\s+(?:i think|we think|for now|so far|anyway|probably))*\W*$")
# Words that answer the question without being a name: "still deciding", "no idea", "a boy".
NOT_A_NAME = frozenset("""
no yes yeah nah not none nothing unknown undecided idea clue sure maybe dont dontnot doesnt
still deciding thinking undecided wait later him her them they it he she that this one
puppy dog cat kitten rabbit hamster boy girl friend mate son daughter baby kid
""".split())


def asked_for_a_name(memory):
    """Whether the bot's own last line asked what the new animal or person is called."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for turn in reversed(turns or []):
        if isinstance(turn, dict) and str(turn.get("bot") or "").strip():
            return bool(A_NAME_ASK.search(" ".join(str(turn["bot"]).split())))
    return False


def the_name_given(text, memory=None):
    """The name this line hands over in answer to the bot's own "what's it called", or "".

    Only when the bot asked. "biscuit" on its own is the food in the kitchen in any other
    conversation, and "hes called biscuit" a turn after "What's its name?" is the answer to that
    question: the reply has to take the name up, not open a new subject with it. Read from the
    bot's own line in memory["turns"], so a bare name said unprompted is left alone.
    """
    said = " ".join(str(text or "").replace("\u2019", "'").split())
    if not said or not asked_for_a_name(memory):
        return ""
    framed = the_name_in(said)
    if framed:
        return framed
    found = JUST_A_NAME.match(said)
    if not found:
        return ""
    name = found.group("name")
    if name.lower() in NOT_A_NAME:
        return ""
    return name


# A line that says a food is not in the kitchen, in any of the plain ways people say it. The
# food can carry a word or two of its own ("any", "a", "the"), and the line can open with the
# "and"/"but" a follow-up is said with.
# A participle followed by one of these is a span of time, not a thing the kitchen is out of:
# "i havent slept in three days", "i havent eaten for a week", "all week". A participle with an
# object after it ("i havent seen the doctor", "i havent paid the rent") is left alone - some of
# those lines have a good answer on main, and the appointment one is the example of it.
SPAN_WORDS = frozenset(("in", "for", "since", "over", "all"))
NOT_GOT = re.compile(
    r"^\s*(?:(?:and|but|also|plus|oh|sorry|actually)\b[\s,]*)?"
    r"(?:"
    r"(?:(?:i|we)\s+)?(?:dont|don't|do not|didnt|didn't|did not|havent|haven't|have not|"
    r"hasnt|hasn't|has not)\s+(?:(?P<holding>got|get|have|had|buy|bought)\s+)?"
    r"|(?:there\s+is\s+|theres\s+|there's\s+|i\s+have\s+|we\s+have\s+)?no\s+"
    r")"
    r"(?:any\s+|a\s+|the\s+|some\s+)?(?P<food>[a-z][a-z '-]{1,24}?)\s*(?:left|in|at all)?\s*$",
    re.I)


# The words that turn a "dont" about food into something other than an empty shelf. "i dont eat
# fish" and "i dont like shellfish" are about what goes on the plate and "we dont eat much fish"
# is how often, so the line is the diet's or the dislike's, and the answer is that said back. Only
# a line that says the kitchen has none of it is the dish table's. Without this the food was read
# as "eat fish" and the line was handed over as "what can i make without eat fish", which the
# dish table answered with a cod traybake to a person who had just said they do not eat fish.
NOT_A_SHELF = frozenset("""
eat eats eating ate eaten like likes liked liking love loves loved fancy fancies enjoy enjoys
enjoyed want wants wanted need needs needed use uses used drink drinks drinking stomach stomachs
touch touches much many""".split())


def _not_got(text, memory=None):
    """The food this line says they have not got, in the line's own words.

    "i dont have any cheese" a turn after a frittata said "cheese on top is worth it" is a limit
    on that idea, and the answer to it is the same dish without the cheese. Said with no idea on
    the table at all, it is still a question about the kitchen: the dish table answers "what can
    i make without cheese", and a line it has no dish for falls through to the acknowledgement.
    A line about eating a food rather than about having it is not this reader's (NOT_A_SHELF).
    """
    match = NOT_GOT.match(" ".join(str(text or "").split()))
    if not match:
        return ""
    food = match.group("food").strip()
    if carries_a_name(food):
        # "no hes called max" is a name put right, not a food that is missing: a thing in the
        # kitchen is never "called" anything, and read as a food the line became "what can i
        # make without hes called max" - a question the dish table answered with the entry about
        # cold callers. The store's own correction reader is what the line is for, so the
        # kitchen stays out of it.
        return ""
    if not _looks_like_a_thing(food):
        return ""
    # A participle after a helper is the line's own verb: the closed class is imported here so
    # this module keeps its import block to the two names it has always had.
    from ..understanding.normalize import IRREGULAR_PARTICIPLES

    words = food.lower().split()
    if any(word in NOT_A_SHELF for word in words):
        return ""
    after = words[1] if len(words) > 1 else ""
    if (not (match.groupdict().get("holding") or "").strip()
            and words[0] in IRREGULAR_PARTICIPLES and (not after or after in SPAN_WORDS)):
        # "i havent slept in three days" is the verb of the line, not a food the kitchen is out
        # of, and the food list above could not have kept up with it: it names eating and
        # drinking and nothing else. Read as a shelf, the line went to the dish table as "what
        # can i make without slept in three days". A participle straight after "haven't" is the
        # sentence's own verb, so the whole shape is out - "i havent seen the doctor", "i havent
        # paid the rent", "i havent gone anywhere" were all a recipe for something without them.
        return ""
    if any(word in POINTS_BACK for word in words) or ASKING.match(food):
        return ""
    # The food is a thing, not the sentence the thing was said in. "no" opens a correction as
    # often as it opens a missing ingredient - "no i said to my landlord", "no i meant tomorrow",
    # "no i said the plumber" - and the whole clause used to be taken as the food, so the dish
    # table answered a correction with "Quick: tuna pasta in 15, a frittata in 20". A first-person
    # word or a word about the saying is the clause, not the ingredient: "said" and "meant" are
    # not in VERBS because they say nothing about the kitchen, and they are the commonest way a
    # correction names nothing at all.
    if any(word in SAID_NOT_A_FOOD for word in food.lower().split()):
        return ""
    if any(word in A_THANK_YOU for word in food.lower().split()):
        # "no thanks" is a refusal of the answer above, not a shelf with the thanks missing.
        return ""
    if len(food.split()) > MOST_WORDS:
        return ""
    return food


def _said_the_food(memory, food):
    """True when the answer on the table is one this food was part of."""
    said = _last_reply(memory).lower()
    return bool(said) and bool(re.search(r"\b" + re.escape(food.lower()) + r"", said))


def _last_reply(memory):
    """What the bot said on the turn before this one, or ""."""
    return earlier.last_reply(memory)
# A follow-up can name a part of the subject instead of a new thing: "and its population",
# "what about the food", "and the weather there". The subject is what the chat is on ("im going
# to spain"), so the line asks about a part of it, and nothing on its own answers a line that
# asks nothing: it fell to "Got it - the weather like." Read back as the question the knowledge
# base files by ("population of spain", "food of rome") the part reaches the entry that knows it.
# The longest a part can be: a noun phrase ("car insurance", "swimming pool"), not a clause.
PART_WORDS = 4
# A part is named with an article or a possessive, never bare: "the food", "its population".
# A bare noun ("and shoes") names a thing of its own, so it is not a part of the last subject.
PART_LEAD = re.compile(r"^\s*(?:the|its|it's|their|his|her|a|an|any|more|some|this|that|these|"
                       r"those)\b", re.I)


def the_thing_named(memory):
    """The thing the person named as the chat's subject ("washing machine"), or "".

    `the_subject` reads the newest turn's words, and a turn about a part of the thing is not the
    thing: after "my washing machine smells" / "i clean the filter" the subject reads "filter",
    and a line asking about another part of the machine has nobody to belong to. What the person
    named is still the machine, so a reader that has to own a part asks with this.
    """
    return _the_thing_they_named(memory)


def about_the_thing(text, memory, owner=""):
    """The part of the subject this line asks about, written as a question, or "".

    `owner` writes the part under that thing instead of the newest turn's subject: a caller that
    finds the part reaches nothing under the last turn's words tries the thing the person named.
    The subject itself is never owned by a part, so a line naming it still reads as no part.

    "and its population" with the chat on Spain -> "population of spain"; "what about the food"
    in Rome -> "food of rome". Empty for anything that is not that shape: a question of its own,
    a verb, a thing carrying the previous ask (that is `follow_up`'s job), a part with no
    subject to belong to, or a line that names the subject itself.
    """
    said = " ".join(str(text or "").strip().split()).strip(" .!?")
    if not said or len(said.split()) > PART_WORDS + 5:
        return ""
    if ASKING.match(said) and not re.match(r"^\s*(?:what|how)\s+about\b", said, re.I):
        return ""
    if follow_up(text, memory):
        return ""  # the thing it names carries the ask before it, which is a better reading
    rest = LEAD.sub("", said).strip(" .,;:!?")
    # A part is said with an article or a possessive in front of it: "the food", "its
    # population", "a taxi". A bare noun is a thing of its own ("and what about shoes?"), which
    # is `follow_up`'s or nobody's, never a part of the last subject.
    if not PART_LEAD.match(rest):
        return ""
    rest = QUANT.sub("", rest).strip(" .,;:!?")
    words = [word.strip(".,;:!?") for word in re.split(r"[\s,]+", rest) if word.strip(".,;:!?")]
    if not words or len(words) > PART_WORDS:
        return ""
    part = []
    for word in words:
        bare = word.lower()
        if bare in POINTS_BACK:
            continue  # "its", "there": the subject itself, not a part of it
        if bare in VERBS or bare in ("what", "how", "why", "when", "where", "which", "who"):
            return ""
        if not part and (bare in PREP or bare in ("another", "more", "other")):
            return ""
        part.append(word)
    if not part or not _looks_like_a_thing(" ".join(part)):
        return ""
    if set(part[0].lower().split()) & {"what", "how"}:
        return ""
    thing_said = str(owner or "").strip() or the_subject(memory)
    if not thing_said:
        return ""
    said_words = {word.lower() for word in " ".join(part).split()}
    if said_words & {word.lower().strip(".,;:!?") for word in thing_said.split()}:
        return ""  # the line names the subject itself: it is not asking about a part of it
    return " ".join(part) + " of " + thing_said


# A line that asks the measure again about a new one: "my boiler is broken" / "how long will it
# take" / "and a new one fitted?" The third line is a question about a job - how long the fitting
# takes - and nothing in it names the job: the measure is the one asked a turn earlier and the
# thing is the one on the table. On its own the line reaches the entry that answers "how long will
# a new one take" for a boiler's age, which is not the question, so it is written as the question
# it is ("how long does it take to fit a new boiler") and the knowledge base answers that.
A_MEASURE_AGAIN = re.compile(r"^\s*(?:and|or|also|plus|what\s+about|how\s+about)\b[\s,]*", re.I)
A_FITTING = re.compile(r"\b(?:fit|fits|fitting|fitted|swap|swaps|swapping|installs?|installed|"
                       r"installation|replac(?:e|es|ed|ing)|replacement)\b", re.I)
WANTS_A_NEW_ONE = re.compile(
    r"\b(?:a|an|the)\s+new\s+(?:one|boiler|machine|shower|radiator|oven|fridge|dishwasher|"
    r"washer|dryer|cooker|hob|combi|heating|system)\b|\bnew\s+one\b|\breplac\w+\b|"
    r"\b(?:fit|fits|fitting|fitted|swap|swaps|swapping|install|installs|installed)\b", re.I)
ASKED_THE_MEASURE = re.compile(r"\bhow\s+long\b", re.I)
# How long the thing lasts is a different question from how long the job takes, and the line that
# asks it says so: "how long does a new boiler last" keeps the answer it has.
_THE_LIFE = re.compile(r"\b(?:last|lasts|lasting|lasted|years?|old|lifespan|life\s*span|"
                       r"expectancy|cost|costs|price|much)\b", re.I)
# The thing as the person said it: "my boiler", "our washing machine", "the kitchen tap".
NAMED_A_THING = re.compile(
    r"\b(?:my|our|the|his|her|this)\s+((?:[a-z][a-z-]*\s+){0,2}[a-z][a-z-]*)\s+"
    r"(?:is|was|are|were|keeps|kept|has|had|stopped|broke|breaks|failed|went|wont|won't|isnt|"
    r"doesnt|doesn't|needs|makes|sounds|smells)\b", re.I)
NOT_THE_THING_ITSELF = frozenset("""
broken broke dead leaking leak faulty failed failing cracked blocked jammed stuck gone kaput
dodgy unreliable stopped working old new bad worse better fine ok okay good rubbish
""".split())


def _the_thing_they_named(memory):
    """The thing on the table as the person named it ("boiler", "washing machine"), or ""."""
    turns = [row for row in (memory or {}).get("turns") or [] if isinstance(row, dict)]
    for turn in turns[-3:][::-1]:
        said = " ".join(str(turn.get("user") or "").lower().split())
        for match in NAMED_A_THING.finditer(said):
            words = [word for word in match.group(1).split()
                     if word not in NOT_THE_THING_ITSELF and len(word) > 2]
            if words:
                return " ".join(words[-2:])
    return ""


def a_measure_asked_again(text, memory):
    """The measure question this line asks again about a new one, or "".

    Two shapes, and both are questions about a job with a time in it:

    - the line only adds to the turn before, and that turn asked how long: "my boiler is broken" /
      "how long will it take" / "and a new one fitted?". The measure is the one from the turn
      before and the thing is the one on the table.
    - the line asks it with the words of its own: "my boiler is 15 years old" / "how long does it
      take to fit a new one". "one" points back at the boiler.

    Only the shape is read here. Whether the knowledge base has a fitting row for that thing is
    the caller's question, and the caller keeps the answer only where it beats the line on its
    own. A line that asks how long the thing LASTS, or what it costs, is that other question and
    is left alone.
    """
    said = " ".join(str(text or "").strip().split()).strip(" .!?")
    if not said or len(said.split()) > 12:
        return ""
    if A_MEASURE_AGAIN.match(said) and len(said.split()) > 8:
        return ""
    if _THE_LIFE.search(said):
        return ""
    if not WANTS_A_NEW_ONE.search(said):
        return ""
    adds_on = bool(A_MEASURE_AGAIN.match(said))
    if adds_on and not (A_FITTING.search(said) or ASKED_THE_MEASURE.search(said)):
        # "and a new one" on its own is not the job asked about: the line has to name the fitting
        # ("and a new one fitted?") or ask the measure again ("and how long will a new one take").
        return ""
    if not adds_on and not ASKED_THE_MEASURE.search(said):
        return ""
    turns = [row for row in (memory or {}).get("turns") or [] if isinstance(row, dict)]
    if not turns:
        return ""
    if adds_on:
        before = " ".join(str(turns[-1].get("user") or "").lower().split())
        if not ASKED_THE_MEASURE.search(before):
            return ""
    thing = _the_thing_they_named(memory)
    if not thing:
        return ""
    return "how long does it take to fit a new " + thing


# A goal somebody is working on, said the way people say it, and the length question that comes
# straight after it. The two together are one question - how long until the goal shows - and the
# knowledge base holds the answer to it:
#
#   im trying to get fit before my wedding / how long will it take
#     before: That's beyond what I know well, sorry. Searching for it will turn up better sources
#   im trying to lose weight before my holiday / how long will it take
#     before: Tell the organiser within 28 days of getting home: that's the deadline in the
#             Package Travel Regulations
#
# Both come from the deadline on the end of the aim: "before my wedding" made the wedding the
# subject, and "before my holiday" made the holiday the subject, so the length question was put
# to the wrong thing. An aim is what the person is doing, and the date on the end of it is when
# they want it done by, not what the question is about.
A_GOAL = re.compile(
    r"^\s*(?:(?:so|ok|okay|and|also|well|right|yeah|hi|hello)[, ]+)*"
    r"(?:i'?m|im|i am|we'?re|we are|i'?ve been|ive been|i have been)\s+"
    r"(?P<how>trying|aiming|hoping|learning)\s+"
    # A figure is part of the aim as often as a word is - "run a 10k", "do 20 lengths" - so the
    # aim is spelled with digits in it. Without this the whole reader stood down on the commonest
    # way of naming a running aim, and "how many weeks of training will that take" after one went
    # to the travel packing list ("training" folds onto "train").
    r"(?P<what>(?:to\s+|for\s+)?[a-z0-9][a-z0-9 '\-]{2,60}?)\s*[.!]*$", re.I)

# The verb the person said the aim with, kept in front of it so the rewritten question is the one
# the knowledge base has: "im learning to drive" asks how long it takes to learn to drive, not how
# long it takes to drive.
GOAL_VERB = {"trying": "", "aiming": "", "hoping": "", "learning": "learn to "}

# The other way people ask the same length: as the state they are aiming at, with no verb to it -
# "how long until i'm fit", "how long till i am slimmer". The clause names the aim's outcome, so it
# is only used when those words are the aim's own, and the aim is what the question is put to.
OUTCOME_ASK = re.compile(
    r"\bhow\s+long\s+(?:until|till|before)\s+(?:i'?m|i\s+am)\s+(?P<state>[a-z][a-z '\-]{2,30})\s*[.!?]*$",
    re.I)
# The verb an aim starts with, which the outcome clause leaves out: "get fit" / "i'm fit".
AIM_VERB = frozenset("get getting be been become becoming feel feeling look looking stay".split())

# The clause that says when it should be done by. It is kept out of the aim, because it names a
# date rather than the thing being done, and it is the clause that pulled the length question
# over to the wedding or the holiday in the first place.
A_DEADLINE_CLAUSE = re.compile(
    r"\s+(?:before|by|until|till|ahead\s+of|in\s+time\s+for)\s+.*$", re.I)

# A line that asks nothing but the length: "how long will it take", "how long does that take",
# "how soon will i see a difference", "how many weeks". Every word has to be one of these, so a
# line with a subject of its own ("how long does it take to learn guitar") is not this reader's.
LENGTH_WORDS = frozenset("""
how long soon many much weeks week months month days day years year hours hour will would does do
did it that this take takes taken be is till until before from now to see notice seeing a an the
difference differences result results normally usually roughly about actually and so but ok okay
then expect should could might start any go going i ill we
""".split())


# The words that make an aim a feeling rather than a thing to do, however it is said.
DISTRESS = frozenset("""
cry crying cried sob sobbing weep weeping tears sad sadder unhappiest unhappy depressed
depression anxious anxiety anxiousness panic panicking grieve grieving grief bereaved bereavement
die dying died death dead funeral bury mourning mourn miss missing hurt hurting pain ache aching
suicide self lonely alone""".split())


def _a_length_ask(text):
    """True when the line is a length question and nothing else."""
    words = re.findall(r"[a-z']+", " ".join(str(text or "").lower().split()))
    if not words or len(words) > 8:
        return False
    if not re.search(r"\bhow\s+(?:long|soon|many\s+(?:weeks|months|days|hours|years))\b",
                     " ".join(words)):
        return False
    return all(word in LENGTH_WORDS for word in words)


# The word the length ask may use for the activity itself instead of naming the aim again: "how
# many weeks of training will that take" after "im hoping to run a 10k by the summer" is the same
# question as "how many weeks will that take". The person has said what they are working at on the
# line before, so this line only has to say how much of it there is - and without these words the
# line read as a line about travel ("training" folds onto "train", and the packing list for a train
# journey answered it) or as a search hedge.
ACTIVITY_WORDS = frozenset("""
training practise practice practices lesson lessons session sessions class classes study studying
revision revising prep preparation coaching drills workout workouts
""".split())


def _a_length_ask_of_the_aim(text):
    """A length question about the aim on the line before, however the activity is named.

    Wider than `_a_length_ask` by the activity words above and by "of", which is how the activity
    is joined to the length ("how many weeks of training"). It is only ever asked when the turn
    before is an aim in the person's own words, so the width costs nothing on a line with no aim
    behind it.
    """
    words = re.findall(r"[a-z']+", " ".join(str(text or "").lower().split()))
    if not words or len(words) > 10:
        return False
    if not re.search(r"\bhow\s+(?:long|soon|many\s+(?:weeks|months|days|hours|years))\b",
                     " ".join(words)):
        return False
    return all(word in LENGTH_WORDS or word in ACTIVITY_WORDS or word == "of" for word in words)


# The words an entry's own key uses when it answers a length. The rewritten question is only
# worth taking the turn when the entry it reaches is an entry about a length: "get flexible"
# reaches the flexible-working request, "train for a triathlon" reaches the card about trains,
# and "write a book" reaches what a yellow card means, so those aims stand down and the line
# is answered as it was before.
LENGTH_KEY_WORDS = frozenset("""
long soon weeks week months month years year hours hour days day minutes minute
""".split())

# A length stated in the answer itself: "two to three weeks", "45 hours", "about six months". A
# hyphenated compound is a name rather than a stretch of time, so "a three-month trial" is not a
# length anybody asked how long of.
A_LENGTH_STATED = re.compile(
    r"\b(?:\d{1,4}|a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen"
    r"|twenty|thirty|forty|fifty|sixty)\s+(?:to\s+\w+\s+)?"
    r"(?:seconds?|minutes?|hours?|days?|weeks?|months?|years?)\b", re.I)


# A pace stated in the answer: "half a kilo a week", "300 to 500 calories a day". A progress
# question ("how fast can i lose weight") is answered with a rate rather than a total, and the
# rate is the length the person asked for - how long each kilo takes. Only the shape
# "<a figure> a week" counts, so "a day off" and "a three-month trial" are not paces.
A_PACE = re.compile(
    r"\b(?:a|an|one|two|three|four|five|half\s+a|\d[\d,]*(?:\s*to\s*\d[\d,]*)?)"
    r"\s+[a-z][\w-]*(?:\s+[a-z][\w-]*){0,2}?\s+(?:a|per|each)\s+"
    r"(?:week|month|day)\b", re.I)


def _answers_a_pace(ask, memory):
    """True when the rewritten ask reaches an entry that answers with a rate of progress."""
    found = _the_entry(ask, memory)
    if found is None:
        return False
    return bool(A_PACE.search(str(getattr(found, "reply", "") or "")))


def _the_entry(ask, memory):
    """The knowledge entry the rewritten ask reaches, or None."""
    try:
        from ..knowledge.lookup import find  # lazy: the memory store needs no facts
        from ..understanding import understand

        return find(understand(ask, memory))
    except Exception:  # noqa: BLE001 - a lookup that fails is not an answer
        return None


def _answers_a_length(ask, memory):
    """True when the rewritten ask reaches an entry that answers a length."""
    found = _the_entry(ask, memory)
    if found is None:
        return False
    reply = str(getattr(found, "reply", "") or "")
    if not A_LENGTH_STATED.search(reply):
        return False
    for part in getattr(found, "key", ()) or ():
        for phrase in (part if isinstance(part, tuple) else (part,)):
            if set(str(phrase).lower().split()) & LENGTH_KEY_WORDS:
                return True
    return False


def _the_length_entry_about(ask, memory, aim_words):
    """True when the ask reaches an entry that states a length and is about the aim itself.

    `_answers_a_length` also asks that the entry be *keyed* on a length word, which is how a
    question about the length of a job is told from one about the job. An entry can answer a
    length without a length word in its key - the 10k training entry is keyed on "10k" and
    "training" and opens "a 10k takes about ten weeks" - so the entry is matched to the aim by a
    word they share instead.
    """
    found = _the_entry(ask, memory)
    if found is None:
        return None
    if not A_LENGTH_STATED.search(str(getattr(found, "reply", "") or "")):
        return None
    keyed = set()
    for part in getattr(found, "key", ()) or ():
        for phrase in (part if isinstance(part, tuple) else (part,)):
            keyed |= set(str(phrase).lower().split())
    if not keyed & set(w for w in aim_words if len(w) > 1):
        return None
    return found


def _answers_a_length_about(ask, memory, aim_words):
    """True when the ask reaches an entry that states a length about the aim itself."""
    return _the_length_entry_about(ask, memory, aim_words) is not None


def _an_aim_before_the_side_question(turns, memory):
    """The last aim in the chat, when the turn before was not one, or "".

    Only read when the turn before this one answered with no length and no rate. "my boiler is
    broken" / "how long will it take" is "Ten minutes" and a recipe answer is "40 minutes": there
    the thing on the table has a length of its own, so the question is its and the aim is left
    alone. A lunch suggestion says nothing about how long a stone takes to lose, so the question
    goes back to the aim the person set - three turns is as far as it looks, because a plan that
    old is another conversation.
    """
    said = " ".join(str((memory or {}).get("last_answer") or "").lower().split())
    if A_LENGTH_STATED.search(said) or A_PACE.search(said):
        return ""
    for row in reversed([r for r in turns[:-1] if isinstance(r, dict)][-3:]):
        line = " ".join(str(row.get("user") or "").strip().split())
        if line and A_GOAL.match(line):
            return line
    return ""


def _the_aim_and_its_length_question(text, memory):
    """The length question this line asks about the aim on the line before, and whether the aim
    carried a deadline: (ask, deadline), or ("", False).

    The aim is the turn before this one, said as their own ("im trying to get fit before my
    wedding"), with the deadline clause taken off it. The question handed back is that aim put
    into the length ask the knowledge base answers - "how long does it take to get fit". An aim
    on a deadline is often a change of pace rather than a job to finish, so the question is tried
    the other way round too ("how fast can i lose weight"), and that is the form that reaches an
    answer stating a rate.
    """
    outcome = OUTCOME_ASK.search(" ".join(str(text or "").lower().split()))
    if not _a_length_ask(text) and not _a_length_ask_of_the_aim(text) and not outcome:
        return "", False
    turns = [row for row in (memory or {}).get("turns") or [] if isinstance(row, dict)]
    if not turns:
        return "", False
    before = " ".join(str(turns[-1].get("user") or "").strip().split())
    if not before:
        return "", False
    match = A_GOAL.match(before)
    if not match:
        # The aim was set before a side question, and the side question's answer says nothing
        # about how long it takes: "im trying to lose a stone" / "what should i eat for lunch" /
        # "how long will it take" answered the lunch a second time. A standing aim is still the
        # aim, and it is the thing a bare length question is about.
        before = _an_aim_before_the_side_question(turns, memory)
        if not before:
            return "", False
        match = A_GOAL.match(before)
        if not match:
            return "", False
    if re.search(r"\bhow\s+(?:long|soon|many)\b", before, re.I):
        return "", False  # the line before already asked the length: not an aim, a question
    verb = GOAL_VERB.get(match.group("how").lower(), "")
    what = re.sub(r"^to\s+", "", match.group("what"), flags=re.I)
    deadline = bool(A_DEADLINE_CLAUSE.search(what))
    goal = A_DEADLINE_CLAUSE.sub("", what).strip(" .,;:-")
    words = goal.split()
    if not 1 <= len(words) <= 6:
        return "", False
    if not re.search(r"[a-z]{3}", goal):
        return "", False
    # A grief, a body that hurts or a feeling is not an aim, and the length question after one of
    # those is not the aim's either: those turns have their own answers. The aim alone is read,
    # because "lose weight" and "lose a stone" are aims and the word "lose" is a loss word too.
    if any(word in DISTRESS for word in re.findall(r"[a-z']+", goal.lower())):
        return "", False
    if outcome:
        # "how long until i'm fit" is the aim's own outcome, or it is a length about something
        # else and the aim has nothing to do with it.
        state = re.sub(r"\s+", " ", outcome.group("state")).strip()
        if state != re.sub(r"^(?:" + "|".join(sorted(AIM_VERB)) + r")\s+", "", goal.lower()):
            return "", False
    aim = (verb + goal).lower().strip()
    # The person named the activity the aim is made of ("how many weeks of training will that
    # take"), and the entry for that activity is the one that answers how long the aim takes. The
    # plain form is asked second because it is read as the length of the thing itself when the
    # thing has a length of its own: "how long does it take to run a 10k" is the race time, not
    # the training plan.
    activity = [w for w in re.findall(r"[a-z']+", " ".join(str(text or "").lower().split()))
                if w in ACTIVITY_WORDS]
    if activity:
        # The line as it stands may already reach the answer: "how many weeks of training will
        # that take" reaches the training plan, and rewriting it only loses it to the entry keyed
        # on the length of the thing itself. The rewrite is for the lines that do not - the same
        # question with "and" in front of it reached the packing list for a train journey.
        as_it_stands = " ".join(re.findall(r"[a-z']+", " ".join(str(text or "").lower().split())))
        if _answers_a_length_about(as_it_stands, memory, goal.lower().split()):
            return "", deadline
        # The aim said with its own verb ("run a 10k") and with the verb taken off ("a 10k") both
        # reach an entry, and they are different entries: the first states a length the answer
        # above may already have given, the second is the plan for the whole thing. The one whose
        # answer adds something is the one taken.
        said = str(turns[-1].get("bot") or "").strip().lower()
        for with_the_activity in ("how long does " + activity[0] + " for " + aim + " take",
                                  "how long does " + activity[0] + " for "
                                  + re.sub(r"^[a-z]+\s+", "", aim) + " take"):
            found = _the_length_entry_about(with_the_activity, memory, goal.lower().split())
            if found is None:
                continue
            reply = str(getattr(found, "reply", "") or "").strip().lower()
            if reply and reply[:70] in said:
                continue
            return with_the_activity, deadline
    asked = "how long does it take to " + aim
    if _answers_a_length(asked, memory):
        return asked, deadline
    # An aim is often a change of pace rather than a job to finish, and the length it is asked
    # for is how long each kilo or each week of it takes: "im trying to lose a stone" / "how long
    # will it take" is answered where the rate is ("half a kilo to a kilo a week"), and that entry
    # is reached by the pace form of the question. It was read only where the aim carried a
    # deadline, so the same aim with none on it was answered with the food entry the side question
    # had left on the table.
    paced = "how fast can i " + (verb + goal).lower()
    if _answers_a_pace(paced, memory):
        return paced, deadline
    if _answers_a_pace(asked, memory):
        return asked, deadline
    return "", deadline


def a_goal_measured(text, memory):
    """The length question this line asks about the aim on the line before, or "".

    The caller keeps the answer only where it beats the line on its own, so a bare "how long will
    it take" that today reaches an entry still reaches it.
    """
    return _the_aim_and_its_length_question(text, memory)[0]


def a_length_about_an_aim_on_a_deadline(text, memory):
    """The length question about the aim, when the aim named a deadline, or "".

    A bare "how long will it take" names nothing of its own, so the knowledge base answers about
    whatever subject the chat left in memory - and with an aim on a deadline that subject is the
    deadline: "im aiming to get fit before the holiday" makes "holiday" the subject, and the
    length question then gets the package-travel rules. The aim is the thing they are asking
    about, so where it carried a deadline this question is taken before the line's own read, and
    not only where the line reaches nothing.
    """
    asked, deadline = _the_aim_and_its_length_question(text, memory)
    return asked if deadline else ""



# The people who answer the bot with "no thanks", and the words they pad it with. Nothing here
# names a thing, so the line carries no ask: read as one, "no thanks though" asked the kitchen
# for "ideas for no thanks though".
NO_THANKS = re.compile(
    r"^\s*(?:no|nope|nah|not)\b[\s,]*(?:"
    r"th(?:anks|ank\s+you|anks\s+you|x)|ta|cheers|mate|love)\b"
    r"[\s,]*(?:(?:though|then|but|anyway|really|at\s+all|so|ok|okay|very\s+much|any)\b[\s,]*)*"
    r"[.!]*\s*$", re.I)


def _no_thanks(text):
    """True when the line turns the answer down and names nothing of its own."""
    return bool(NO_THANKS.match(" ".join(str(text or "").split())))


def follow_up(text, memory):
    """The ask this line carries ("ideas for pudding"), or "" when it carries none."""
    aim = a_goal_measured(text, memory)
    if aim:
        return aim  # "how long will it take" after "im trying to get fit before my wedding"
    again = a_measure_asked_again(text, memory)
    if again:
        return again  # "and a new one fitted?" after "how long will it take"
    # The same ask with one food taken back out of it: the dish answer already given is about to be
    # given again without the thing they have not got (bot/knowledge/cooking.py, _best_dish).
    missing = _not_got(text, memory)
    if missing:
        ask = _previous_ask(memory)
        if ask:
            if _said_the_food(memory, missing):
                return ask.rstrip(" .,!?") + " without " + missing
            return ""
        # Nothing is on the table yet, so the line is the kitchen question: the dish table
        # answers it when it knows a dish without that food, and passes on it when it does not.
        return "what can i make without " + missing
    if _answers_the_bot(text):
        return ""  # "lol" and "nice" answer the bot; they name nothing to ask about
    if _no_thanks(text):
        return ""  # "no thanks", "no thanks though": a refusal names nothing to ask about
    if trouble.reads_as_trouble(text):
        # "im in pain" after the condensation answer named "pain", was read as a part of that
        # answer, and came back as "Nothing separate for pain - it is the same advice: use the
        # extractor fan ...". A line about the person's own body is not a bare thing carried by
        # the last turn, whatever noun is in it, so nothing is asked about it here and the
        # composer answers the line it was given.
        return ""
    if BARE_ANOTHER.match(text or ""):
        # "what else" after a request for suggestions is the same ask as "anything else": a
        # second pick, with nothing named. It carries no noun of its own, so the ask written from
        # the words of the line is empty and the turn went to the repeat frame ("Same as before:
        # ...") or the punt ("That's most of what I know on it"). Written as the bare ask, the
        # entries hand over the pick they have not made yet.
        return "ideas for anything else" if _previous_ask(memory) else ""
    said = thing(text)
    if not said:
        return ""
    if not _previous_ask(memory):
        return ""
    return "ideas for " + said


# A line that asks for a second pick and names nothing of its own: "what else", "what else is on",
# "anything else you'd suggest", "another one". The lead-ins and the short tail are the ways people
# say it; a line with anything else in it names something and is read by `thing` as before.
BARE_ANOTHER = re.compile(
    r"^\s*(?:(?:and|or|so|ok|okay|right|well|but|then|now|hmm|ha)\b[\s,]*)*"
    r"(?:(?:what|anything|something)\s+else|any\s+others?|"
    r"another\s+(?:one|idea|option|film|book|recipe|suggestion|pick|show))"
    r"(?:\s+(?:(?:is|are)\s+on|on|works?|then|tonight|now|please|for\s+me|"
    r"(?:would\s+)?you(?:'d)?\s*(?:would\s+)?(?:suggest|recommend|have|got)|do\s+you\s+have))*"
    r"\s*[.!?]*\s*$", re.I)


# The words that ask what the bot makes of what it has just said, and name no subject of their
# own: "honest view?", "honest opinion", "and your thoughts?". Read as a thing to be about they
# turn the view ask into a second thing-ask, and the answer comes back framed as that thing
# ("The same goes for the honest view: ...") or about the wrong one of two options ("should i get
# a cat or a dog" / "honest view?" was handed the litter tray and the bowls). The subject of a
# view ask is the answer already given, which is the composer's to read (bot/compose/fallback.py,
# the view reader): so the thing-ask here names nothing and stands down.
VIEW_FRAME = frozenset("""view opinion take takes thinking thoughts tuppence""".split())
# The words that only say how bluntly it is wanted, not what about.
VIEW_MANNER = frozenset("""honest real quick true actual blunt personal own full proper same
plain straight""".split())
# The words that only join the ask to what came before it ("and your thoughts?", "the same").
# Two words are deliberately not here. "second" would make "should i get a cat or a dog" / "the
# second" - the person picking one of the two - fall to the stock line. "in" would make "in full"
# a line with nothing to be about, and the repeat-ask reader does not claim it, so the answer
# already on the screen is never said again (see the PR).
VIEW_POSSESSIVE = frozenset("your my our the a an and also plus too then".split())


def names_nothing_to_be_about(said):
    """True when the thing a follow-up names is only the person asking for a view.

    "honest view" and "your thoughts" name the ask, not a subject: every word of them is doing
    that and nothing else is left, so there is no thing for the earlier turn to be about.
    """
    words = [word for word in re.findall(r"[a-z']+", str(said or "").lower())
             if word not in VIEW_POSSESSIVE]
    return bool(words) and all(word in VIEW_FRAME or word in VIEW_MANNER for word in words)


# The words a line can be built from and still be nothing but the way they feel: "just", "a
# bit", "so", the little verbs of saying what they are (be, feel) and the manners of a line.
FEELING_FILLER = frozenset("""
a an the just only bit little so really very quite too still today tonight now thanks thank
thankyou you im i m am is are was were be been feeling feel feels felt and but yeah well of
about kind sort
""".split())
# The feelings that are a phrase rather than one word, so the words inside them ("out", "up",
# "in") are not read as a subject of their own. The words are the drafting module's, which keeps
# the one list of the feelings a person names in a line; it is imported inside the function
# because it reads the store back, and the store is being built when this module is.
FEELING_SAID_AS_A_PHRASE = (
    "wiped out", "done in", "dead on my feet", "run down", "no energy", "knackered out")


def _only_how_they_feel(text, memory):
    """True for a line whose whole content is how the person says they feel.

    "just tired", "im so shattered", "feeling low": the reading says the feeling (its `emotion`)
    and every other word in the line is a filler or the feeling's own adjective, so there is no
    thing in it to ask about. A question, or a feeling with anything else in the line, is not
    this: "why am i so tired" and "im tired all the time" are the entry's own questions.

    A feeling said straight after a knowledge answer is not small talk either: it is about the
    answer's subject ("the baby woke up five times last night" / "im shattered"), and the
    answer's own follow-up ("any tips") is read from that answer. Standing down there read the
    card's step as gone and the next ask came back as "what have you tried so far".
    """
    if not isinstance(memory, dict):
        return False
    read = memory.get("understood")
    if not isinstance(read, dict) or not read.get("emotion"):
        return False
    turns = memory.get("turns") or ()
    if turns and isinstance(turns[-1], dict) and turns[-1].get("module") == "answers":
        # The answer above is about a thing, and the feeling is the person's word for how that is
        # going, so the thing is still in hand - and so is the step out of that answer.
        return False
    low = " ".join(str(text or "").lower().split())
    if not low or "?" in low or str(read.get("kind") or "") == "question":
        return False
    from ..compose.draft import FEELING as feeling_words, FEELING_PHRASES
    for phrase in tuple(FEELING_PHRASES) + FEELING_SAID_AS_A_PHRASE:
        low = low.replace(phrase, " ")
    words = re.findall(r"[a-z']+", low)
    if not words:
        return False
    return not [word for word in words
                if word not in FEELING_FILLER and word not in feeling_words]


def about_it(text, memory):
    """The question a bare thing carries after a turn about something ("what about frosting").

    "im making a cake" / "frosting" is a person asking about the frosting of the cake they are
    making, and the knowledge base has an entry for it. On its own the line names a thing and
    asks nothing, so `follow_up` above stands aside - its previous turn was not a request for
    ideas - and nothing else reads it as a question: the lookup finds nothing, and the turn comes
    back as "I'm listening - say more if it helps." The thing they named is what the turn is
    about, so that is the question asked. Only where the lookup answered nothing at all, so no
    line that answers today moves.
    """
    if _answers_the_bot(text):
        return ""  # "lol" and "nice" answer the bot; they name nothing to ask about
    if trouble.reads_as_trouble(text):
        return ""  # a line about the person's own body is not a bare thing (see `follow_up`)
    # A line judging the answer just given as doable ("sounds doable", "easy enough") names no
    # thing for the chat to be about, and read as one it came back as "The same goes for the
    # sounds doable: ..." - the judgement said back as if the person had named a part of the job.
    # Asked of the composer's own reading so the two cannot disagree about what the line is.
    from ..compose import fallback
    if fallback.reads_as_a_judgement(text):
        return ""
    # A line that only says how they feel names no thing to be asked about: "hi" / "not much
    # really" / "just tired" was read as the bare thing "just tired", asked as "what about just
    # tired" and answered with the entry for constant tiredness - two weeks of sleep hygiene
    # where the chat module has a warm line for the same word ("that kind of tired needs an
    # early night, not more coffee"). The reading's own emotion is the test, and a feeling with
    # anything else in the line ("im tired of the commute", "im tired all the time") keeps its
    # thing, because those lines carry a subject of their own.
    if _only_how_they_feel(text, memory):
        return ""
    # A correction says the last thing again with an opener in front of it ("sorry, four
    # brothers" after "i have three brothers"), and the thing is the value, not the opener: with
    # the opener still in the line, the thing asked about was "sorry four brothers", which the
    # apology row answers - the person putting a fact right was told how to apologise. Only the
    # opener a person punctuated goes, so "sorry i snapped at her" keeps every word (see
    # `facts.without_the_correction_opener`).
    from . import facts
    corrected = facts.without_the_correction_opener(text) or text
    said = thing(corrected)
    if not said:
        return ""
    turns = [turn for turn in (memory or {}).get("turns") or [] if isinstance(turn, dict)]
    if not turns:
        return ""
    was = " ".join(str(turns[-1].get("user") or "").lower().split())
    if not was or was == " ".join(str(text or "").lower().split()):
        return ""  # the first thing said, or the same words again: nothing to be about
    if names_nothing_to_be_about(said):
        return ""
    return "what about " + said


# A measure ask that points back instead of naming the thing: "how long should it be", "how much
# would that cost", "how many do i need". Nothing in the line says what it is about, so the entry
# matcher reads the newest detail word in the topic instead of the subject the chat is on: after
# "im thinking of getting a dog" / "it would be for the kids", "how much would that cost" reached
# the child bus fares. Written about the subject ("how much would the dog cost") it reaches the
# entry that knows it. Where there is no answer at all the same line is asked of the whole
# knowledge base, which is the search hedge ("I don't know enough to answer that honestly"):
# after "my sister is getting married in june" / "im worried about the speech", "how long should
# it be" is the length of a wedding speech.
MEASURE_ASK = re.compile(
    r"\b(?:how\s+(?:long|much|many|often|big|far|heavy|hot|warm|expensive)|"
    r"what\s+temperature)\b", re.I)
# An ask about how long until the person is *somewhere* with the thing, which is a measure ask
# with a competence in it rather than a measure alone: "how long until im good at it", "how long
# until i can play it", "how long to get good at it". Without this the line names a word the
# measure shapes do not hold ("good", "play", "can"), so it was left alone and the entry matcher
# read whatever the topic's newest word fit: after "i want to learn guitar" the ask was answered
# by the language-hours row (600 hours to hold a conversation in Spanish), while the same ask
# written out ("how long until im good at guitar") reaches the guitar row. What the competence
# words say is how they want to be, not what the chat is about, so they are allowed in the line
# for exactly as long as the line is this shape and no longer.
PROGRESS_ASK = re.compile(
    r"\bhow\s+long\b(?=[^.!?]*\b(?:until|till|before)\b)"
    r"|\bhow\s+long\s+(?:does\s+it\s+take\s+)?(?:to\s+)?(?:get|be|become)\s+"
    r"(?:good|any\s+good|decent|ok|okay|fluent|better)\b", re.I)
# The doing the person named, in the form the competence is said with: "good at running",
# "good at cycling", never "good at the run". An article turns a bare verb into another noun - "the
# run" is the diarrhoea row and "the cycle" is the menstrual one - so a verb the plan named as a
# doing is written with -ing, which is also the only English there is ("good at the running" is
# not a sentence anyone writes).
A_GERUND = re.compile(r"^[a-z]{4,}ing$")
# How the plan said the doing: "learn to run 5k", "start running", "learning to cycle". The verb
# the person used is what makes the subject word a doing rather than a thing - "guitar" is a
# thing however it is learned, "run" is the doing itself. Learning a thing takes no "to" ("im
# learning spanish"), so only "learn to <verb>" counts there.
A_DOING_NAMED = re.compile(
    r"\b(?:learn|learning|learnt)\s+to\s+(?P<doing>[a-z]{3,})\b"
    r"|\b(?:start|starting|started|try|trying|tried|practise|practising|practice|practicing|"
    r"how\s+to)\s+(?P<also>[a-z]{3,})\b", re.I)
# A figure on the doing: "run 5k", "walk 10k". Not part of the competence - how long a 5k takes to
# run is a different question from how long until you can run one.
A_FIGURE_ON_THE_END = re.compile(r"^\d+[a-z]{0,2}$", re.I)


def a_figure_on_the_doing(memory, word):
    """The figure the plan put on the doing ("run 5k"), or "" when the plan named none."""
    if not word:
        return ""
    said = _the_plan_said(memory, word)
    if not said:
        return ""
    words = re.findall(r"[a-z0-9']+", said)
    for index, one in enumerate(words[:-1]):
        if one == word.lower() and A_FIGURE_ON_THE_END.match(words[index + 1]):
            return words[index + 1]
    return ""


def is_a_progress_ask(text):
    """Whether the line asks how good, how fluent or how far along the doing is.

    Read from the asking alone, so the answer side can tell a progress ask (which the subject has
    already been written into as a doing) from the other measures that point back.
    """
    return bool(PROGRESS_ASK.search(str(text or "")))


def _the_doing(word, memory):
    """The doing the plan named, written as the competence is said with it, or "".

    "im learning to cycle" / "how long until im good at it" points at cycling, and the point of
    writing it in is that the entry for cycling is reached. Written behind an article it is another
    word entirely ("the cycle"), and left bare ("the run") the same. Only a word the plan named as
    a doing is turned this way: a thing stays as it is, because "good at the guitar" is right and
    "good at guitaring" is not.
    """
    said = _the_plan_said(memory, word)
    if not said or not word:
        return ""
    word = word.lower()
    named = False
    for found in A_DOING_NAMED.finditer(said):
        doing = found.group("doing") or found.group("also") or ""
        if doing == word:
            named = True
            break
        if doing.endswith("ing") and doing[:-3].rstrip("n") == word.rstrip("n"):
            named = True
            break
    if not named:
        named = the_doing_the_plan_named(word, memory)
    if not named:
        return ""
    # The doing alone, with no figure on it: "running 5k" reaches the row that answers how long a
    # 5k *takes to run*, where the bare doing reaches the row that answers how long it takes to be
    # able to. The plan's own figure is not part of the competence, and writing it in turns a
    # right answer into a wrong one.
    return _the_ing(word)


# The plan's own words say whether a word is a thing or a doing: "i want to run 5k" names run as
# a doing, "i want to learn guitar" names guitar as a thing. It is the aim and the "to" that tell
# them apart, and only the verbs that take a doing that way: "going to spain" has the "to" of a
# place, so "going" is not one of them.
A_PLAN_TO_THE_DOING = re.compile(
    r"\b(?:want|wants|wanting|wanted|hope|hoping|hoped|plan|planning|planned|aim|aiming|aimed|"
    r"intend|intending|learn|learning|learnt|try|trying|tried|would\s+like|would\s+love)"
    r"\s+to\s+%s\b", re.I)


# The ask about getting good at it, which is the one the doing was made for: "how long until im good
# at running" reaches the row that says how long it takes to be able to, and the figure the plan
# named is not part of the competence. Every other length ask about the same plan ("how long until i
# can do it", "how long does that take") is about doing the whole thing, figure and all.
A_HOW_GOOD = re.compile(
    r"\b(?:good|better|best|fluent|confident|comfortable|competent|proficient|capable|skilled|"
    r"decent|mastered|able\s+to|any\s+good)\b", re.I)


def the_doing_the_plan_named(word, memory):
    """True when the plan named this word as something to do ("want to run") and not a thing."""
    said = _the_plan_said(memory, word)
    if not said or not word:
        return False
    return bool(re.search(A_PLAN_TO_THE_DOING.pattern % re.escape(word.lower()), said, re.I))


def _the_plan_said(memory, word):
    """What the person said the plan in, looking back a few turns, or "".

    The topic has already been narrowed to the thing by the time a follow-up is read ("run"), so
    the words that say it was a doing ("learn to run 5k") are in the turn before: the newest user
    line that names the word is the plan.
    """
    turns = [row for row in ((memory or {}).get("turns") or []) if isinstance(row, dict)]
    said = []
    for row in turns[-4:]:
        line = " ".join(str(row.get("user") or "").lower().split())
        if line and word.lower() in re.findall(r"[a-z0-9']+", line):
            said.append(line)
    topic = " ".join(str(the_subject(memory) or "").lower().split())
    if topic:
        said.append(topic)
    return " | ".join(said)


def _the_ing(word):
    """The -ing form of a bare verb: "run" -> "running", "cycle" -> "cycling"."""
    if not word or word.endswith("ing"):
        return word
    if len(word) > 3 and word.endswith("e") and word[-2] not in "aeiou":
        return word[:-1] + "ing"
    if len(word) <= 5 and re.search(r"[^aeiou][aeiou][bdgklmnprst]$", word):
        return word + word[-1] + "ing"
    return word + "ing"
# The competence and the ask to be somewhere: how good, how fluent, and which of the things they
# will be able to do with it. None of them names the subject, so the pointing word still does.
PROGRESS_WORDS = frozenset("""
good any decent ok okay fine fluent confident comfortable competent proficient proficiently
better well able capable mastered skilled basics basic conversational conversation
play playing speak speaking read reading write writing hold manage manage use using
get getting become becoming at it to be can could will would until till before by
im i'm i am then actually really genuinely properly roughly about
""".split())
# What a measure ask is made of: the asking, the measure, and the pointing back. A line with a
# content word of its own beyond these names something, and writing the subject into it would be a
# guess about a line that already says what it is about.
# The measure's own verb: "how long will it take", "how long does it last", "how much does it
# cost". Without these the line reads as naming something of its own and the subject is never
# written in, so a fault ("my boiler is broken") got the search hedge instead of the time a repair
# takes. They say nothing about what is being measured, so they are the asking, like "how long".
MEASURE_VERBS = frozenset("""
take takes taking took last lasts lasting cost costs costing
be being been get gets getting got happen happens happening""".split())
MEASURE_WORDS = frozenset("""
how what long much many often big far heavy hot warm expensive temperature time times
second seconds minute minutes hour hours day days week weeks month months year years
cost costs costing price prices charge charges worth pay pays spend spends need needs
a an the per
i me my mine we our us you your should would will shall can could do does did be is are was were
has have had having
it its them they that this these those there one ones
""".split())
# A feeling in the subject is not the thing the chat is about: "im worried about the speech" has
# the subject "worried speech", and the subject a measure ask wants is the speech.
# How a thing is, not which thing it is: "my boiler is broken" has the subject "boiler broken",
# and the thing a measure ask is about is the boiler, not the broken. Left in, the ask was written
# as "how long will the broken take" - which reaches nothing - and the person got the search hedge
# where the time a repair takes was filed under the boiler.
A_FAULT = frozenset("""
broken broke bust busted stopped dead leaking leaky faulty failed failing cracked blocked
jammed stuck gone kaput dodgy unreliable""".split())
NOT_THE_THING = frozenset("""
worried worry worries worrying anxious anxiety scared afraid nervous stressed stress upset angry
annoyed sad unhappy happy excited tired exhausted confused unsure lost stuck glad pleased
thinking thought considering planning hoping wanting looking interested keen trying dreaming
weighing wondering
""".split())
# A verb of buying is not the thing bought: "what do i need to buy for a puppy" has the topic
# subject "buy" (the noun "puppy" is behind a preposition), and a measure ask written about it
# asked "how much does the buy cost", which reaches nothing, so "and how much does one cost"
# was the search hedge where the puppy's price row was the answer. When the subject is only a
# verb like this, the noun is taken from the person's own line instead.
A_GETTING = frozenset("""
buy buys buying get gets getting purchase purchases purchasing pick picks picking choose chooses
choosing order orders ordering
""".split())

# A follow-up that names only one aspect of the thing the chat is on: "the cost", "and the price",
# "what about the upkeep", "and the food". Nothing in the line says what the aspect is an aspect
# of, so the lookup matches the aspect alone: "and the cost" after "were adopting a rescue cat"
# reached the pet-cost entry, whose opening is the price of a puppy, and "the price" reached
# nothing at all and came back as the search hedge. Written as the question about the subject the
# chat is on ("how much does the cat cost") both reach the entry that knows the animal in front of
# them. The shapes are the questions the entry matcher already answers well, one per aspect, and
# an aspect with no good shape here is left to the readers below.
ASPECT_ASKS = (
    (frozenset("cost costs price prices expense expenses upkeep costing".split()),
     "how much does the {thing} cost"),
    (frozenset("food feeding feed diet".split()), "what do i feed the {thing}"),
)
# "What do I feed it" is a question about an animal and nonsense about anything else - asked of
# Lisbon it reached the city guide, which answers a question nobody asked. The shape is used only
# where the subject is a living thing that is fed.
FED_THINGS = frozenset("""
dog dogs puppy puppies cat cats kitten kittens rabbit rabbits bunny bunnies guinea pig pigs hamster
hamsters gerbil gerbils rat rats mouse mice ferret ferrets parrot parrots budgie budgies bird birds
fish goldfish chicken chickens hen hens cockerel horse horses pony ponies tortoise tortoises
snake snakes lizard lizards gecko geckos tortoise degu degus chinchilla chinchillas
""".split())
# The words a follow-up is dressed in. They carry no meaning, so what is left when they are taken
# off is the aspect, and a line with anything else in it says what it is about and is somebody
# else's job.
ASPECT_FILLERS = frozenset("""
and so or but also then ok okay well what about how the a an any more of
""".split())
# The aspects themselves. They are never the thing the chat is about: "and the cost" after the
# price of a cat is a second aspect of the cat, not a new subject called cost.
ASPECT_NOUNS = frozenset().union(*(nouns for nouns, _ in ASPECT_ASKS))


# The doing in progress: the line before names what the person is in the middle of ("im cooking
# pasta"), and the length ask after it leans on that doing rather than on anything of its own.
IN_PROGRESS = re.compile(
    r"\b(?:im|i'm|i am|we're|we are|hes|he's|shes|she's|theyre|they're|ive|i've)\b"
    r"(?:\s+(?:still|also|just|been|busy|now))*\s+"
    r"((?:[a-z']+\s+){0,6}?[a-z]{2,}ing\b[^.?!,]*)", re.I)
def _the_doing_in_hand(memory):
    """The doing in progress in the line before this one: "learning to drive", or ""."""
    for turn in reversed((memory or {}).get("turns") or []):
        if not isinstance(turn, dict):
            continue
        said = " ".join(str(turn.get("user") or "").split())
        if not said:
            continue
        found = IN_PROGRESS.search(said)
        return found.group(1).strip(" ,;:-") if found else ""
    return ""


# The length ask the same way: how long the doing in progress takes, with the pronoun standing for
# it. "how long on the hob" and "how long does it take" name nothing but the ask (and, sometimes,
# where the doing happens), so the entry matcher has no subject to match: "im cooking pasta" /
# "how long on the hob" was answered by the food-safety row ("Bin it, I'm afraid. Pasta left out
# for more than 2 hours ...") because the only words in the line are pasta's and left out's.
THE_LENGTH_FOR_IT = re.compile(
    r"^(?:and\s+|so\s+|ok\s+|okay\s+|then\s+|also\s+|roughly\s+|about\s+)?"
    r"(?:how\s+long|how\s+much\s+time|how\s+many\s+(?:hours|minutes|days|weeks|months))"
    r"[^.?!]{0,24}$", re.I)
# A length ask with a length of its own ("how long after the cast", "in 2 hours") is a different
# question, and one that already has the words to reach its entry.
LENGTH_NOT = re.compile(r"\b(?:until|till|before|after|ago|since|between|every|each"
                        r"|\d+\s*(?:h|hr|hrs|hours?|minutes?|days?|weeks?))\b", re.I)
# The words a line made of the ask alone can also hold, and still be the same question about the
# doing: the measuring verbs, how long it is "supposed" to take, and the small words of a place.
LENGTH_FILLERS = frozenset("""
supposed going go went spent took long should will would does do did i you we they it that this
is are be last for about of
""".split())


# A journey is not a doing whose length this ask is about. "im going to rome" is a trip, and the
# question written from it - "how long does it take to going to rome" - reaches the Roman Empire,
# whose row has "rome" and "how long" in it: "im going to rome" / "how long do i need" came back
# "The Roman Empire in the west lasted about 500 years ...". How long a trip needs is how many days
# the stay is, and the city's own row answers that.
JOURNEY = re.compile(r"^(?:going|go|goes|heading|off|flying|travelling|traveling|visiting|moving|"
                     r"coming|leaving|driving|walking|cycling)\b", re.I)


def the_duration_for_the_doing(text, memory):
    """The length ask written about the doing in progress, or "" when the line is not that ask.

    "im cooking pasta" / "how long on the hob" is one question: what the pasta needs on the heat.
    Written with the doing in it ("how long does it take to cooking pasta") it reaches the entry
    that knows - dried pasta is 8 to 12 minutes - where the line on its own reaches the row about
    pasta left out of the fridge. Only the shape is read here; whether the doing's entry then
    answers it is the caller's question, and a place word ("on the hob") is dropped rather than
    kept, because "cooking pasta on the hob" is what reaches the left-out row. The "to ... -ing"
    is not English, and it is never shown to anybody: it is tested by which entry it reaches, and
    it is the wording that takes both pasta (8 to 12 minutes) and rice (1 part to 1.5, 12
    minutes) to the cooking rows.
    """
    said = " ".join(str(text or "").split()).strip(" .!?,")
    if not said or len(said.split()) > 8:
        return ""
    if not THE_LENGTH_FOR_IT.match(said) or LENGTH_NOT.search(said):
        return ""
    for word in re.findall(r"[a-z']+", said.lower()):
        if word in MEASURE_WORDS or word in MEASURE_VERBS or word in POINTS_BACK:
            continue
        if word in LENGTH_FILLERS or word in PLACE_WORDS:
            continue
        if word in PLACE_PREPOSITIONS or word in PLACE_ARTICLES:
            continue
        return ""
    doing = _the_doing_in_hand(memory)
    if not doing or len(doing.split()) > 7 or JOURNEY.match(doing):
        return ""
    if _the_place_belongs_to_the_doing(said, doing, memory):
        return ""
    return "how long does it take to " + doing


def _the_place_belongs_to_the_doing(said, doing, memory):
    """True when the line's place is not the doing's place, so the doing cannot answer it.

    The place is dropped from the written ask, which is safe only where the doing is the thing
    that is done in it: "how long on the hob" after "im cooking pasta" is the pasta's time on the
    heat. A place ask is written about whatever the doing in hand is, though, and the doing can be
    something else entirely: after "im learning to drive", "how long in the oven" was written out
    as "how long does it take to learning to drive" and the person asking about an oven was told
    how many lessons it takes to pass a driving test.

    The understanding engine reads the kind of thing a place is, and every knowledge domain
    declares the kinds of thing it answers (`bot.knowledge.by_topic`), so an entry whose domain
    does not answer the place's kind of thing is an answer to a different question: cooking is a
    kind the pasta entry answers, so "on the hob" is the pasta's place, and a kitchen is not a
    kind the driving entry answers.

    The reading is of the place the line names, not of the line: the engine's `topic` for a length
    ask carries the doing in hand along with the line ("how long does that take" after "im
    planning to retrain as a plumber" reads `maths-and-numbers` here and `home-and-diy` in
    another chat), so asking it which kind of thing the line is about refused a rewrite that is
    right - the plumber's own length answer - on every chat whose doing scored a house or a DIY
    topic (bronze-camera, #9963). A line that names no place of its own is not asking about one,
    so nothing is refused. Where either reading is missing nothing is refused either, which
    leaves the caller's own checks as they are.
    """
    from ..knowledge import by_topic  # lazy: the knowledge base imports this package
    from ..understanding import understand  # lazy, as everywhere else in this module
    from .topics import _entry  # lazy: this module is imported from there
    place = str((understand(said, memory) or {}).get("subject") or "")
    if not place:
        # "how long does that take" names no place, so the doing's own entry cannot be answering
        # the wrong question: it is the only thing the line can be about.
        return False
    item = _entry("how long does it take to " + doing)
    if item is None:
        return False
    domain = str(getattr(item, "domain", "") or "")
    if not domain:
        return False
    kind = str((understand(place, memory) or {}).get("topic") or "")
    if not kind:
        return False
    return kind not in by_topic().get(domain, ())


def _the_aspect_asked(low, thing):
    """The question shape for a line that names only an aspect ("the cost"), or ""."""
    rest = [word for word in low if word not in ASPECT_FILLERS]
    if len(rest) != 1:
        return ""
    for nouns, shape in ASPECT_ASKS:
        if rest[0] not in nouns:
            continue
        if "{thing}" in shape and shape.startswith("what do i feed") and thing not in FED_THINGS:
            continue
        return shape
    return ""


# "When is the best time to do it" names the job and points back at the thing the chat is on.
# Written out with the thing in place of the pointing word - "when is the best time to do
# courgette plants" - it is the question the knowledge base has a row for, where the line on its
# own only reaches the answer the person was given a turn ago. The shape is a quality of time and
# a job, and the job has to be vague ("do", "get", "sort") for this to be the pointing word that
# names the thing rather than a thing of the line's own.
BEST_TIME_TO_DO = re.compile(
    r"^(?:when|what)(?:'s|s| is| was)?\s+(?:the\s+)?"
    r"(?:best|right|good|ideal|safest|cheapest|easiest)\s+"
    r"(?:time|month|week|season|day|part)\s+(?:to|for)\s+(?P<rest>.+)$", re.I)
POINTS_AT_A_THING = frozenset("it its them that this these those one ones".split())
A_VAGUE_JOB = frozenset("""do doing get getting go going make making start starting sort sorting
    prep prepare preparing deal dealing have""".split())
# "When is the best time to do it" leaves the job to the line before it, which is where the person
# said what the job is: "the hedge needs cutting back" is a cut, "should i move them" is a move.
# The gerund or past form is stemmed, and a bare verb is read after the word that asks for it.
A_BARE_JOB = re.compile(r"\b(?:should|could|would|can|shall|will|to)\s+(?:i\s+|we\s+|you\s+)?"
                        r"([a-z]{3,})\b", re.I)
NOT_THE_JOB = frozenset("""i me my we you your the a an and but so if of for in on at it its
    that this them they he she there here not no yes please thanks need needs want wants have
    has had do did does am is are was were be been got get going want trying""".split())


def _the_job_before(memory):
    """The job the line before named, as a bare verb: "the hedge needs cutting back" -> "cut"."""
    turns = [row for row in ((memory or {}).get("turns") or []) if isinstance(row, dict)]
    if not turns:
        return ""
    said = " ".join(str(turns[-1].get("user") or "").lower().split())
    for word in reversed(re.findall(r"[a-z']+", said)):
        if len(word) < 4 or word in NOT_THE_JOB:
            continue
        if word.endswith("ing") or (word.endswith("ed") and len(word) > 4):
            stem = word[:-3] if word.endswith("ing") else word[:-2]
            if len(stem) > 3 and stem[-1] == stem[-2] and stem[-1] not in "lsz":
                stem = stem[:-1]
            if len(stem) > 2 and stem not in NOT_THE_JOB:
                return stem
    found = A_BARE_JOB.search(said)
    if found and found.group(1) not in NOT_THE_JOB:
        return found.group(1)
    return ""


def the_best_time_to_do_it(text, understood, memory=None):
    """The ask written out with the thing it points at, or "".

    Only the ask that names nothing but a job and a word pointing back: "when is the best time to
    do it", "what is the best day to plant them". The thing is the one the reading resolved the
    pointing word to ("courgette plants"), so the line becomes the question about it. A line that
    names a thing of its own ("when is the best time to plant tomatoes") is already that question
    and is left alone, and so is one that points at nothing.
    """
    said = " ".join(str(text or "").split()).strip(" .!?")
    if not said or len(said.split()) > 14:
        return ""
    found = BEST_TIME_TO_DO.match(said)
    if not found:
        return ""
    words = re.findall(r"[a-z']+", found.group("rest").lower())
    if not any(word in POINTS_AT_A_THING for word in words):
        return ""
    if any(word not in POINTS_AT_A_THING and word not in A_VAGUE_JOB and len(word) > 2
           for word in words):
        return ""
    ref = (understood or {}).get("ref") if isinstance(understood, dict) else None
    target = ""
    for word in ("it", "they", "them", "that", "this", "those", "these"):
        said_target = " ".join(str((ref or {}).get(word) or "").split())
        if said_target and said_target.lower() not in POINTS_AT_A_THING:
            target = said_target
            break
    if not target:
        return ""
    rest = found.group("rest")
    # A job the ask could not name is the one the line before it named: "when is the best time to
    # do it" after the hedge needs cutting back asks when to cut it. "to do hedge" reached the
    # planting row and answered about bare-root trees.
    job = re.match(r"(\w+)", rest)
    if job and job.group(1).lower() in A_VAGUE_JOB:
        before = _the_job_before(memory)
        if not before:
            # The job is "do" and the line before named none: there is no question here to write
            # out, and "to do lavender" reached the herbs card and answered about rosemary.
            return ""
        if before:
            # The vague job goes out and the verb of the line before goes in, with the thing in
            # place of the pointing word: "to do it" after the hedge needs cutting back -> "to cut
            # hedge".
            rest = rest[job.end():].strip()
            rest = re.sub(r"\b(?:it|its|them|that|this|those|these|one|ones)\b", target,
                          rest, count=1, flags=re.I)
            return "when is the best time to " + before + " " + rest
    head = said[:found.start("rest")]
    # The pointing word is where the thing goes: "to do it" -> "to do courgette plants".
    rest = re.sub(r"\b(?:it|its|them|that|this|those|these|one|ones)\b", target,
                  rest, count=1, flags=re.I)
    return head + rest


def _only_the_measure(low):
    """Whether a line is nothing but the asking, the measure and a bare doing, so it points back.

    A line with a noun of its own says what it is about and is somebody else's job; these are the
    words that leave it with nothing of its own ("how many times a week", "how often should i go").
    """
    return all(word in MEASURE_WORDS or word in LIGHT_DOING or word in PLACE_WORDS
               or word in PLACE_PREPOSITIONS or word in PLACE_ARTICLES
               or (index + 1 < len(low) and (word, low[index + 1]) in PLACE_PAIRS)
               for index, word in enumerate(low))


def about_the_subject(text, memory):
    """The measure ask written about the subject of the chat, or "".

    "how long should it be" and "how much would that cost" name nothing: they point back at what
    the chat is on, and the entry matcher has only the topic's newest words to go on. Written with
    the subject in, the same line reaches the entry that knows it - "how much would the dog cost",
    "how long should the speech be". Only the shape is read here (a measure ask, a word pointing
    back, and nothing else of its own); whether the line then reaches an entry is the caller's
    question, and the caller uses the answer only where it beats the line on its own.
    """
    said = " ".join(str(text or "").strip().split())
    said = said.strip(" .!?")
    said = _without_and_at_the_start(said)
    if not said or len(said.split()) > 12:
        return ""
    low = [word.lower().strip(".,;:!?") for word in said.split()]
    timed = the_duration_for_the_doing(said, memory)
    if timed:
        # The doing in progress is the subject of the ask, and the ask has no subject of its own
        # ("how long on the hob" after "im cooking pasta").
        return timed
    said_the_thing = subject_word(memory)
    asked = _the_aspect_asked(low, said_the_thing)
    if asked:
        return asked.format(thing=said_the_thing) if said_the_thing else ""
    if not MEASURE_ASK.search(said):
        return ""
    place = _the_place_phrase(low)
    if not place and not any(word in POINTS_BACK for word in low) and not _only_the_measure(low):
        # "how many times a week" and "how often" have no pronoun to point back with and are still
        # about the thing in hand: there is nothing else they could be about. They reach no entry
        # on their own, so the turn after "i want to start running" was the run-walk paragraph a
        # second time, framed "Same as before:", when the how-often answer is a card of its own
        # ("Three runs a week is plenty to start..."). A measure ask that names anything of its
        # own is turned away by the loop below, so only the asking and the measure get here.
        return ""
    # A thing that has stopped working is asked about differently from a thing they are planning
    # ("my boiler is broken" / "how long will it take" is the repair's clock, where "how long does
    # it take" on its own belongs to whatever the chat is about). Only there do the measure's own
    # verb and a connective in front count as the asking rather than as words of their own.
    faulty = a_faulty_thing(memory)
    while faulty and low and low[0] in _A_CONNECTIVE:
        low = low[1:]
    # Everything else in the line has to be the asking and the measure, or the line says what it
    # is about and this is somebody else's job. A place is the exception, and only a place: "how
    # long in the microwave" names where the thing is done, not what it is, so it points back at
    # the thing the chat is on just as "it" does.
    # A bare doing is only allowed where there is no pronoun to point back with. "how long does
    # it take" has one, and the "it" is what the doing belongs to: read with the subject written
    # into it ("how long does the cycle take") a chat about learning to cycle reached the
    # menstrual cycle card.
    bare = not any(word in POINTS_BACK for word in low)
    progress = bool(PROGRESS_ASK.search(said))
    for index, word in enumerate(low):
        if word in MEASURE_WORDS or word in POINTS_BACK or (bare and word in LIGHT_DOING):
            continue
        if word in PLACE_WORDS:
            continue
        if faulty and word in MEASURE_VERBS:
            continue
        if progress and word in PROGRESS_WORDS:
            continue  # "good", "until", "can play": how they want to be, not what about
        if word in PLACE_PREPOSITIONS or word in PLACE_ARTICLES:
            continue
        if index + 1 < len(low) and (word, low[index + 1]) in PLACE_PAIRS:
            continue  # "air" in "the air fryer", where the place is two words
        return ""
    said_the_thing = subject_word(memory)
    if place:
        # The topic is already the place by the time this runs (topics.note has kept it as the
        # newest record), so the thing comes from the line before, which is what the place ask is
        # about.
        in_hand = _the_thing_in_hand(memory, said) or said_the_thing
        if not in_hand:
            return ""
        return _about_the_thing_in_the_place(low, place, in_hand, said, memory)
    if not said_the_thing:
        return ""
    if low and len(low) < len(said.split()):
        # The connectives in front of the asking are not part of the question.
        said = " ".join(said.split()[-len(low):])
    if not any(word in POINTS_BACK for word in low):
        # No pronoun to write the thing into, so the thing goes on the end, which is the form the
        # entry is keyed to ("how many times a week running", "how often running").
        return said + " " + said_the_thing
    written = "the " + said_the_thing
    doing = _the_doing(said_the_thing, memory) if progress else ""
    if (doing and not A_HOW_GOOD.search(said)
            and a_figure_on_the_doing(memory, said_the_thing)
            and re.search(r"\bhow\s+long\b", said, re.I)):
        # The figure the plan put on the doing makes two questions of it - how long until you can
        # run one, and how long a 5k takes to run - and the written-in line takes the second:
        # "how long until i can do running" reached the run-walk schedule and stopped answering how
        # long. The plan's own timeline is the answer to the competence, so the line stands.
        return ""
    if doing or (progress and A_GERUND.match(said_the_thing)):
        # "how long until im good at the running" is not English, and the article reaches other
        # entries on the way: "the runs" is the diarrhoea row and "the cycle" is the menstrual one,
        # so a question about getting better at cycling came back as a question about periods, and
        # one about a 5k plan as what to eat after a stomach bug. The doing is written the way the
        # competence is said with it, with the figure it was named with: "good at running 5k".
        written = doing or said_the_thing
    return re.sub(r"\b(?:it|that|this|they|them|those|these|one|ones)\b",
                  lambda found: written, said, count=1, flags=re.I)


# "and in the microwave", "then on the hob": a follow-up opening on a joining word is the same ask
# as the one without it, and the joining word is not a thing of its own.
_AND_AT_THE_START = re.compile(r"^(?:and|then|also|so)\s+", re.I)


def _without_and_at_the_start(said):
    return _AND_AT_THE_START.sub("", said, count=1)


# The places a thing is done in, and the little words that put it there: "how long in the oven"
# after the method for a potato, "how long on the hob" after the porridge. A place says nothing
# about *what* is being asked about, and read on its own it reaches the entry about the appliance -
# "how do i cook rice" / "how long in the microwave" was answered with how long a microwave lasts.
PLACE_WORDS = frozenset("""
oven hob microwave grill grillpan airfryer fryer pan saucepan pot steamer slowcooker cooker kettle
toaster barbecue bbq fridge freezer dishwasher washingmachine dryer radiator sink bath
""".split())
# The places people write as two words: "the slow cooker", "the air fryer". The second word is in
# PLACE_WORDS and the first is not, so the phrase has to keep both or the written line asks about
# "the fryer", which is a chip pan.
PLACE_PAIRS = frozenset({("slow", "cooker"), ("air", "fryer"), ("grill", "pan"),
                         ("pressure", "cooker"), ("rice", "cooker"), ("tumble", "dryer")})
# A measure ask points back through a bare doing as well as through a pronoun: "how many times a
# week should i go" names the asking and nothing to ask it about, so the doing is the chat's own.
LIGHT_DOING = frozenset("""go goes going do does doing get take use try keep start""".split())
PLACE_PREPOSITIONS = frozenset("in on at into under over".split())
PLACE_ARTICLES = frozenset("the a an my our your their".split())
# A place ask continues something being done: "how do i cook rice" / "how long in the microwave",
# "im roasting a chicken" / "how long in the oven". The place is where the doing happens and the
# thing in hand is what is being done. After a line that does no doing - "my microwaves broken",
# "how long does a microwave last" - the place is the subject of the chat, and the line is a
# question about the appliance.
# The doing of a thing, in the form the person said it: the place ask that follows keeps the doing,
# because "how long does it take to reheat rice in the microwave" is a different question from
# "how long does it take to cook rice in the microwave", and the entry that answers it is different.
BASE_DOING = ("cook", "bake", "roast", "boil", "fry", "grill", "steam", "make", "prepare",
              "reheat", "heat", "store", "keep", "freeze", "defrost", "warm")


def _the_forms(base):
    forms = {base, base + "s", base + "ing", base + "ed"}
    if base[-1] in "aeiou":
        forms.add(base[:-1] + "ing")
    elif base.endswith("y"):
        forms |= {base[:-1] + "ies", base[:-1] + "ied"}
    elif base[-1] not in "aeiouwxy":
        forms |= {base + base[-1] + "ing", base + base[-1] + "ed"}
    return forms


DOING_BASE = {form: base for base in BASE_DOING for form in _the_forms(base)}
DOING = frozenset(DOING_BASE)


def _the_doing_word(text):
    """The doing in the line, in its plain form ("reheating" -> "reheat"), or ""."""
    for word in str(text or "").split():
        bare = word.lower().strip(".,;:!?")
        if bare in DOING_BASE:
            return DOING_BASE[bare]
    return ""


def _a_doing_word(text):
    return bool(_the_doing_word(text))


def _what_the_chat_is_on(memory, this_line):
    """The line before this one: what the person said, or the record the chat was left on."""
    mine = " ".join(str(this_line or "").lower().split())
    for turn in reversed((memory or {}).get("turns") or []):
        if not isinstance(turn, dict):
            continue
        was = str(turn.get("user") or "")
        if not was.strip() or " ".join(was.lower().split()) == mine:
            continue
        return was
    record = (memory or {}).get("topic")
    if isinstance(record, dict) and record.get("text"):
        return str(record["text"])
    return ""


def _the_thing_in_hand(memory, this_line):
    """The thing the line before this one is about: "rice" out of "how do i cook rice"."""
    was = _what_the_chat_is_on(memory, this_line)
    for word in reversed([part for part in re.split(r"[^a-z']+", was.lower()) if part]):
        if len(word) < 3 or word in MEASURE_WORDS or word in PLACE_WORDS:
            continue
        if word in DOING or word in POINTS_BACK or word in PLACE_PREPOSITIONS:
            continue
        return word
    return ""


def _the_place_phrase(low):
    """The place the line names with its preposition and article ("in the microwave"), or ""."""
    for index, word in enumerate(low):
        if word not in PLACE_WORDS:
            continue
        first = index
        if index and (low[index - 1], word) in PLACE_PAIRS:
            first = index - 1
        start = first
        while start and (low[start - 1] in PLACE_PREPOSITIONS or low[start - 1] in PLACE_ARTICLES):
            start -= 1
        return " ".join(low[start:index + 1])
    return ""


def _about_the_thing_in_the_place(low, place, said_the_thing, this_line, memory):
    """The ask about the place, written about the thing it is done to, or "".

    "how do i cook rice" then "how long in the microwave" is a question about the rice, in the
    microwave. Read on its own words the place is the only thing the line names, so it reaches the
    entry about the appliance and the person asking about their rice is told how long a microwave
    lasts. Written about the thing - "how long does the rice take in the microwave" - it reaches the
    entry that knows, and the answer is the ten minutes on full power they wanted.
    """
    if said_the_thing in PLACE_WORDS:
        return ""  # the thing in hand is the place itself: "my microwaves broken"
    doing = _the_doing_word(_what_the_chat_is_on(memory, this_line))
    if not doing:
        return ""
    measure = []
    for word in low:
        if word in PLACE_WORDS or word in PLACE_PREPOSITIONS or word in PLACE_ARTICLES:
            break
        if word in POINTS_BACK:
            break
        measure.append(word)
    if not measure or ("how" not in measure and "what" not in measure):
        return ""
    if measure != ["how", "long"]:
        # A place ask that asks how long is the one the appliance entry steals: the length of a
        # thing's doing is nowhere in "how long in the microwave", so it is read as how long the
        # microwave lasts. The other measures are answered by the place's own entry well ("what
        # temperature in the oven" gets the fan-oven rule), and writing the thing in only moves
        # them onto a card about the thing.
        return ""
    written = "how long does it take to " + doing + " " + said_the_thing + " " + place
    if not _the_rewrite_earns_its_place(" ".join(low), written, memory):
        return ""
    return written


def _the_rewrite_earns_its_place(alone, written, memory):
    """Whether writing the thing into the place ask beats asking the place on its own.

    The two asks have to reach different cards, and the card the thing finds must not be the one
    that has just answered. "how long in the oven" after the roasting method reaches that method
    again, and the person gets "Nothing separate for the oven - it is the same advice: 30 to 40
    minutes" where today they get the figure itself. A card already on the screen is never worth
    reaching a second time.
    """
    from .topics import _entry  # lazy: this module is imported from there
    was = _entry(alone)
    became = _entry(written)
    if was is None or became is None or became is was:
        return False
    last = (memory or {}).get("last_answer")
    if isinstance(last, dict) and last.get("id") and last.get("id") == getattr(became, "id", None):
        return False
    return True


# A line that reports where a thing in hand stands - what state it is in, what is left of it -
# without naming it: "its on 4% and the charger is at work" after a phone that drains, "it still
# smells" after a carpet. A report is not a question, so nothing in the knowledge base is reached:
# the line names no subject of its own and the entry matcher has nothing to go on, so the turn came
# back as the report said back at the person ("Got it — it's on 4%."). Written with the thing in
# hand in it ("my phone is on 4%") the same report reaches the entry that answers it. Only the shape
# is read here; whether the written-in line reaches an entry that knows the thing is the caller's
# question, and the caller's guard.
STATE_WORDS = frozenset("""
still now already again left gone flat empty full broken dead stuck worse better okay ok
smells smell stinks stinking works working not never
""".split())
# A figure with its unit: "4%", "2 hours", "half a bottle". A report is mostly a measurement.
A_FIGURE = re.compile(r"\b(?:\d+(?:\.\d+)?\s*(?:%|percent|hours?|minutes?|days?|weeks?|litres?|"
                      r"liters?|kilos?|kg|metres?|miles?|pounds?))\b", re.I)
# A place the thing is in, said without naming the thing: "the charger is at work".
A_PLACE = re.compile(r"\b(?:at|in|on|under|behind)\s+(?:work|home|the office|the car|the garage|"
                     r"the kitchen|the shed|the loft|the shop|the hotel|my bag|my pocket|my desk)"
                     r"\b", re.I)


def _thing_in_hand(memory):
    """The thing the last answer was about, in one word ("phone", "carpet"), or "".

    `subject_word` reads the noun a measure ask is about, and it takes the last content word of the
    topic phrase: after "my phone battery drains fast" it gives "fast", which is what the line
    says about the phone rather than the phone. A report is about the thing the answer on the
    screen was about, and that answer's own key words say it: the topic's words in the order the
    person said them, kept where the answer is keyed on one. Words are compared by their opening,
    because a key holds one form of a word ("drains") and the line another ("drain").
    """
    topic = memory.get("topic") if isinstance(memory, dict) else None
    said = (topic or {}).get("words") if isinstance(topic, dict) else None
    if not isinstance(said, list) or not said:
        return subject_word(memory)
    answer = memory.get("last_answer") if isinstance(memory, dict) else None
    keys = [str(word).lower() for word in ((answer or {}).get("keys") or ())]
    subject_keys = _the_answers_own_subject(answer)
    # The entry's own subject words come first, because they are what the answer is about: the
    # phone-drain answer is keyed on "battery" and "charge", and "fast" is only how the phone
    # behaves. Where the answer's subject was not kept, any key word will do, and the last one
    # wins - English puts the thing at the end of the phrase ("red wine out of a carpet" is
    # about the carpet).
    found = []
    for wanted in (subject_keys, keys):
        for word in reversed(said):
            bare = str(word).lower().strip(".,;:!?")
            if len(bare) < 3 or bare in NOT_THE_THING or bare in STATE_WORDS:
                continue
            if bare in found:
                continue
            if _only_a_particle(bare, (topic or {}).get("text") or ""):
                continue
            if any(key[:4] == bare[:4] for key in wanted):
                found.append(bare)
    if not found:
        only = subject_word(memory)
        return [only] if only else []
    return found


def _only_a_particle(word, text):
    """True when every time the text says the word, it is the particle of a phrasal verb.

    "i keep waking up at 3am and cant get back to sleep" is about the sleep, and the "back" in it
    follows "get". Read as the thing in hand it wrote "my back is been about three weeks now" for
    the follow-up "its been about three weeks now", and the sore-back-for-a-week card answered a
    line about sleep with a paragraph about a body nobody had mentioned. A word the person says as
    a thing of its own ("my back is sore") is not touched: only a word that never appears without
    a verb in front of it is left out.
    """
    said = " " + " ".join(str(text or "").lower().split()) + " "
    found = list(re.finditer(r"\b" + re.escape(word) + r"\b", said))
    if not found:
        return False
    for match in found:
        before = said[:match.start()].split()
        if not before:
            return False
        last = before[-1].strip(".,;:!?()")
        # A gerund or a participle is a verb in this position too ("waking up", "saved up"), and
        # the verb lists keep only some of their forms.
        if not (last in kinds.VERBISH or last in kinds.VERB_FORMS
                or last.endswith(("ing", "ed"))):
            return False
    return True


def _the_answers_own_subject(answer):
    """The subject words of the entry the answer came from ("battery", "charge"), or ()."""
    entry_id = (answer or {}).get("id") if isinstance(answer, dict) else ""
    if not entry_id:
        return ()
    try:
        from ..knowledge import entries as all_entries
        for item in all_entries():
            if getattr(item, "id", "") == entry_id and item.key:
                first = item.key[0]
                parts = first if isinstance(first, (tuple, list, frozenset, set)) else (first,)
                return tuple(str(part).lower() for part in parts if isinstance(part, str))
    except Exception:  # noqa: BLE001 - the answer's own words are a fallback, not a requirement
        return ()
    return ()


def reported_states(text, memory):
    """The line with the thing in hand written in where it points back, and its neighbours.

    "its on 4% and the charger is at work" is about the phone the chat is on, and the person is
    telling the bot where it stands rather than asking anything. The line names its state, not its
    subject, so the knowledge base cannot reach an answer; with the subject in it the same line
    does. Empty unless three things hold, so a line that says what it is about is left alone:

    - it points back ("it", "its", "they") rather than naming a subject;
    - it reports something (a figure, a state word, or where the thing is);
    - the chat is on a thing, and the line does not name that thing itself.

    A line can hold more than one thing for the "it" to be ("red wine out of a carpet" is the
    carpet when something still smells, and the wine when something has stained), and nothing here
    can tell which the person means: the read is only a rewrite, and the caller takes the first
    one that reaches an answer the conversation has not already had.
    """
    said = " ".join(str(text or "").strip().split()).strip(" .!?")
    if not said or len(said.split()) > 16:
        return []
    low = [word.lower().strip(".,;:!?()") for word in said.split()]
    if not any(word in POINTS_BACK for word in low):
        return []
    # A question is not a report: "how long will it take" and "should i charge it overnight" are
    # read by the ask readers, and a report is what is left when the line asks nothing.
    if ASKING.match(said) or MEASURE_ASK.search(said):
        return []
    things = _thing_in_hand(memory)
    if not things:
        return []
    reported = bool(A_FIGURE.search(said) or A_PLACE.search(said)
                    or {word for word in low} & STATE_WORDS)
    if not reported:
        return []
    reads = []
    for thing in things:
        if thing in low:
            continue  # the line names this thing itself: it says what it is about
        # "its on 4%" is "it is on 4%", so the thing written in takes the "is" with it: "my phone
        # is on 4%". A line that says "it" alone keeps its own verb.
        written = re.sub(r"\b(?:its|it's)\b", "my " + thing + " is", said, count=1, flags=re.I)
        written = re.sub(r"\b(?:it|they|them|their)\b", "my " + thing, written, count=1,
                         flags=re.I)
        if written not in reads:
            reads.append(written)
    return reads


# A practice the person keeps with the thing in hand, said without naming it: "i feed them every
# week" after tomato plants, "i water it daily" after a fern. Like a state report, the line names
# no subject of its own, so the entries that answer it are out of reach and the turn came back as
# the practice said back at the person ("Got it — you feed them every week."). Written with the
# thing in it the same line reaches the entry that knows it (garden.tomato-feed says when to start
# and how often).
CARE_VERBS = frozenset("""
feed feeds feeding fed water waters watering watered repot repotting repotted prune prunes
pruning pruned deadhead deadheading deadheaded stake staking staked mulch mulching mulched
mist misting misted thin thinning thinned aerate aerating
""".split())
# How often they do it. A care line with no frequency says almost nothing on its own ("i water it")
# and is left to the small talk, so a period is part of what makes a practice.
A_HOW_OFTEN = re.compile(
    r"\b(?:every|each|once|twice|three times|a|per|daily|weekly|fortnightly|monthly|yearly|\
annually|regularly|sometimes|usually|often|january|february|march|april|may|june|july|august|\
september|october|november|december|spring|summer|autumn|winter)\b", re.I)
# Whose feeding it is: "i feed the kids every day" and "i feed the dog twice a day" name their own
# object, so the thing in hand is not what the line is about.
CARE_NOT_THE_THING = frozenset("""
baby babies child children kid kids toddler toddlers mum mom dad daddy mummy son sons daughter
family dog dogs cat cats puppy puppies kitten kittens fish rabbit hamster guinea bird birds
parrot chickens hen hens horse horses me myself us everyone everybody
""".split())


# Where a thing stands or is kept, rather than the thing itself. A word in this set is a word of
# the answer on the screen ("where should i put it" is answered with the window and the light), and
# it is no name for the thing standing there: "i have a fern on the windowsill" / "i water it every
# day" was read as "windowsill water every day", which reaches nothing, so the fern itself never got
# written in.
WHERE_IT_STANDS = frozenset("""
windowsill window sill shelf table bench desk worktop counter sideboard floor carpet rug patio
balcony garden greenhouse conservatory kitchen bathroom bedroom lounge hall hallway garage shed
attic loft cellar porch utility laundry nursery study room house home flat pot pots tub tray
basket fridge freezer oven hob grill cupboard cupboard drawer desk
""".split())


def _the_persons_own_words(memory):
    """The words the person used for the thing in hand, as they spelled them, best first.

    `_thing_in_hand` hands back the topic's words, and a topic is kept as stems: the thing after
    "im growing tomatoes in the greenhouse" is "tomatoe", which no entry is keyed on, and by the
    time the practice is read the topic is the practice line itself ("feed every week"), which
    names no thing at all. So the thing is read from the answer on the screen - its own subject
    words first, then its keys - and the spelling is taken from the person's own earlier line, kept
    only where it matches that thing by its opening. Words that are the practice rather than the
    thing ("feed", "every", "week") are dropped: written in front of a practice, a verb reaches
    whatever entry fits it ("growing feed every week" reached the houseplant-feed card).
    """
    answer = memory.get("last_answer") if isinstance(memory, dict) else None
    # The answer's own subject words, and nothing else. Its keys are the whole card's vocabulary,
    # verbs included ("growing", "water"), and a verb taken for the thing writes a read that
    # reaches whatever card is keyed on that verb: "growing feed weekly" is the houseplant-feed.
    wanted = list(_the_answers_own_subject(answer))
    turns = (memory or {}).get("turns") if isinstance(memory, dict) else None
    own = []
    for turn in reversed(turns or ()):
        for word in re.split(r"[^A-Za-z']+", str((turn or {}).get("user") or "").lower()):
            if len(word) > 3 and word not in own:
                own.append(word)
    found = []
    for source in (wanted, [str(word).lower() for word in _thing_in_hand(memory)]):
        for key in source:
            for word in own:
                if len(word) < 4 or word in found or word in _NOT_THE_PRACTICE:
                    continue
                if (word in NOT_THE_THING or word in MEASURE_WORDS or word in STATE_WORDS
                        or word in WHERE_IT_STANDS):
                    continue  # a place is where the thing is, not the thing: "windowsill" is
                    # a word of the light answer, and it is no name for the fern on it
                if key[:4] == word[:4]:
                    found.append(word)
        if found:
            break
    if found:
        return found
    # Where the answer on the screen names no subject of its own (a greeting, say), the topic's
    # words are the last resort, and a place is not a thing: "i have a fern on the windowsill" kept
    # "windowsill" first, whose read reached no entry, so the fern itself never got written in.
    return [str(word).lower() for word in _thing_in_hand(memory)
            if len(str(word)) > 3 and str(word).lower() not in _NOT_THE_PRACTICE
            and str(word).lower() not in WHERE_IT_STANDS]


# Words that are how often or when, or the frame of the line, rather than the thing it is about.
_NOT_THE_PRACTICE = frozenset("""
every each once twice three times week weeks day days month months year years morning
mornings evening evenings night nights daily weekly fortnightly monthly regularly sometimes
usually often spring summer autumn winter january february march april may june july august
september october november december about around roughly usually also still just really
""".split()) | CARE_VERBS


# A line that states something about the person and asks nothing: "im 34 and self employed" after
# "pension", "for a 7 year old" after "birthday party", "we live in a flat with no garden" after
# "rescue dog". It names no subject of its own, so the knowledge base cannot reach it and the turn
# came back as the fact said back at the person ("Got it. Is there anything you'd like a hand
# with?"). Written with the subject in it ("pension im 34 and self employed") the same line reaches
# the entry that needs both halves: the pension one for the self employed.
PERSON_OPEN = re.compile(
    r"^\W*(?:(?:and|but|so|oh|also|well|yeah|yep|ok|okay|right|alright)\W+)*"
    r"(?:i|im|i'?m|i'?ve|ive|i'?d|id|we|we'?re|were|we'?ve|me|us|she|he|they|there"
    r"|it|its|it'?s|they're)\b",
    re.I)
# A fact said without the person at all: "for a 7 year old", "with two kids", "on the morning",
# "just the mornings", "10 grand less". A preposition or a determiner in front is what makes it a
# fact about the thing rather than a new subject.
FACT_OPEN = re.compile(
    r"^\W*(?:(?:and|but|so|oh|also|well|yeah|yep|ok|okay|right|alright|nothing|just)\W+)*"
    r"(?:for|with|on|in|at|by|near|from|about|only|mostly|usually|mainly|every|each)\b", re.I)
# The words a stated fact is carried on rather than made of: they say who it is about and how it
# hangs on the sentence, and a row keyed on one of these is keyed on nothing.
FACT_FILLER = frozenset("""the and but for with about only just even also very really quite
    still now then than that this these those there their them they she her his him its it
    was were been being have has had does did doing get got going make made more most some any
    im ive id you your my our me us we i am is are not no yes like want need know think""".split())
# A time on its own says when the trouble happens, not what it is: "usually in the morning" after a
# banging boiler reached the no-heat card, which knows the morning and nothing about the noise.
# The fact has to name something besides the time.
TIMES_ONLY = frozenset("""morning mornings evening evenings night nights afternoon afternoons
    weekend weekends weekday weekdays day days week weeks month months winter winters summer
    summers autumn spring springtime sometimes always usually mostly mainly normally lately
    recently today tonight tomorrow""".split())
# A joining word says how two halves of a sentence hang together, not what either is about: "i can
# do about 2k before i have to walk" after a running question was put in front of the run and
# reached the cardio-before-weights card, which took the subject "running" from the chat and the
# word "before" from the fact, and answered a session-order question nobody asked.
JOINING = frozenset("""before after until till while when whenever since once if because cause
    though although whereas unless during without within between through across along around
    behind below beside beyond onto upon than""".split())
# How long a stated fact can be. A longer line says something of its own, and the small talk or a
# knowledge entry answers it as it stands.
FACT_MOST_WORDS = 14
# A line that weighs two things is asking which, not stating what: "i dont know whether to say
# anything or just keep my head down" after a boss reached nothing on main and reached a coaching
# line here, when the line is a question the chat should answer as it stands.
A_CHOICE = re.compile(
    r"\bwhether\b|\bwhat\s+to\b|\bhow\s+to\b|\bwhat\s+i\s+should\b|\bif\s+i\s+should\b|"
    r"\bnot\s+sure\s+(?:if|whether|what|how)\b", re.I)
# A count of people says who is in the house, not what the thing in hand is. "i have two kids"
# after "i want to buy a bike" was put in front of the bike and answered with how to size a
# child's saddle, when the person was buying a bike for themselves and had only mentioned the
# kids. So a fact made of a number and a person is a fact about the household, and it says
# nothing about the thing the chat is on.
COUNT_WORDS = frozenset("""one two three four five six seven eight nine ten eleven twelve
    couple few several many lot lots""".split())
PEOPLE_WORDS = frozenset("""kid kids child children boy boys girl girls son sons daughter
    daughters baby babies toddler toddlers teen teens teenager teenagers grandchild
    grandchildren person people adult adults flatmate flatmates housemate housemates""".split())
# The verbs a person says a want with. The chat is on the thing they named ("i want to buy a bike"),
# and "buy" in front of a fact reads as the subject ("buy we rent" reached the rent-or-buy-a-house
# card). The noun is what an entry is keyed on.
NOT_THE_SUBJECT = frozenset("""buy buying bought choose choosing chose pick picking want wanted
    wanted need needed get getting got looking look looked find finding""".split())

# A pronoun is not a noun an entry is keyed on, and it is not the thing the chat is about
# either: "she lives alone since my dad died" left "her" as the subject, and the next line was
# rewritten "her but it is wearing me down a bit", which reached the weaning row on "a bit" and
# answered a grown woman's tiredness with lumps for a baby. `it` is already dropped for being
# short; these are the ones that are long enough to survive the length test.
_NOT_A_PRONOUN = frozenset("""
he she him her his hers them they their theirs himself herself themselves
""".split())


def stated_about_the_person(text, memory):
    """The line rewritten with the subject of the chat in front of it: ["pension im 34 ..."].

    Empty unless four things hold, so a line that says what it is about is left alone:

    - it is short and asks nothing ("how long will it take" is the ask readers' line);
    - it states a fact rather than a feeling: it opens on the person ("im ...", "we ...", "my
      ...") or on a preposition ("for a ...", "with ..."), or it says a figure;
    - the chat is on a subject, and the line does not name that subject itself;
    - the subject is a thing the knowledge base keeps an entry about, which is the caller's
      question: the read is only a rewrite.

    The subject goes in front ("pension im 34 and self employed") because the entry is keyed on
    the subject and the fact, in that order of importance, and the line's own wording is kept:
    the person's words are what the entry for that pairing is keyed on.
    """
    said = " ".join(str(text or "").strip().split()).strip(" .!?")
    if not said or len(said.split()) > FACT_MOST_WORDS:
        return []
    if "?" in str(text or "") or ASKING.match(said) or MEASURE_ASK.search(said):
        return []
    if A_CHOICE.search(said):
        return []
    if _a_place_of_its_own(memory):
        # A line that says where they are names a thing of its own, so it is not a fact about the
        # subject on the table: "how do i get rid of ants" / "i live in bristol" was rewritten
        # with the ants in front ("ants i live in bristol"), which reached the ant entry and
        # answered an ant's lifespan instead of the news about Bristol. The reading says the line
        # named a place, and a place is a subject the next line can lean on ("what's it like
        # there?"), which is what a topic is for - so the reader stands down and the line is
        # answered as the line it is.
        return []
    low = [word.lower().strip(".,;:!?()") for word in said.split()]
    if not (PERSON_OPEN.match(said) or FACT_OPEN.match(said) or A_FIGURE.search(said)):
        return []
    named = [word for word in low if len(word) > 2 and word not in TIMES_ONLY
             and word not in FACT_FILLER]
    if not named:
        return []
    # who is in the house is not what the thing is (see COUNT_WORDS)
    if all(word in PEOPLE_WORDS or word in COUNT_WORDS for word in named):
        return []
    # The subject phrase can be a sentence's worth ("boiler banging", "cat weeing mat"), and only
    # the noun in it is what an entry is keyed on. One word per candidate, because a read that
    # reaches a word-mate of the phrase is not an answer about the thing (the reason
    # `care_reports` writes one word in).
    reads = []
    for word in subject_words(memory, text):
        if word in low:
            continue  # the line names this one itself, so it says what it is about
        written = " ".join((word + " " + said).split())
        if written not in reads:
            reads.append(written)
    return reads


def _a_place_of_its_own(memory):
    """True when the reading found a place named in this line."""
    read = memory.get("understood") if isinstance(memory, dict) else None
    if not isinstance(read, dict):
        return False
    for found in read.get("entities") or ():
        if isinstance(found, dict) and found.get("type") == "place":
            return True
    return False


def subject_words(memory, text=""):
    """The nouns the chat is on, best first: ["boiler"], ["pension"], ["cat", "mat"].

    `the_subject` is the phrase the conversation is about, which on a statement is the sentence
    itself ("my boiler is banging"). On a line the store has already noted as the topic ("usually
    in the morning" after a boiler) that phrase is this very line, so the subject before it is
    read instead: `the_carried_topic` is the record of what the chat was on before this line.
    The words a knowledge entry is keyed on are the nouns in it, so the verbs ("banging",
    "weeing"), the pointing words and the words that say nothing ("my", "is") are dropped, and
    what is left is tried in the order the chat said it.
    """
    from ..understanding import kinds  # noqa: PLC0415 - only when a fact is on the table
    was = ""
    if text:
        record = the_carried_topic(memory, text)
        was = str((record or {}).get("text") or "") if isinstance(record, dict) else ""
    said = " ".join(str(was or the_subject(memory) or "").split()).lower()
    out = []
    for word in re.split(r"[^a-z0-9]+", said):
        if len(word) < 3 or word in out:
            continue
        if word in NOT_THE_THING or word in MEASURE_WORDS or word in STATE_WORDS:
            continue
        if word in _NOT_A_PRONOUN:
            continue
        if word in kinds.VERBISH or word in kinds.VERB_FORMS or word in NOT_THE_SUBJECT:
            continue
        out.append(word)
    return out[:4]


def care_reports(text, memory):
    """The line rewritten with the thing in hand in front of it: ["tomatoes feed every week"].

    One read only, for the best word for the thing. Every word that might be the thing also
    reaches entries of its own, and a second read is a second chance to reach a word-mate:
    "chillies feed weekly" was answered from "growing feed weekly", because the houseplant-feed
    card is keyed on "growing" and "feed" and says nothing about chillies. The first word is the
    one the answer on the screen is about, so it is the only one written in.

    Empty unless four things hold, so a line that says what it is about is left alone:

    - it names a practice (a care verb) and how often, and is short;
    - it points back ("them", "it") or says nothing else that names an object;
    - it names no one of its own ("i feed the kids every day" is about the kids);
    - the chat is on a thing, and the line does not name that thing itself.

    The rewrite puts the thing first ("tomatoes feed every week") rather than in the subject's
    place ("i feed my tomatoes every week"), because "feed" with "my" in front of the object
    reads as meals for the household and the meal-plan entry takes it. Which of the reads answers
    is the caller's question, and the caller's guard.
    """
    said = " ".join(str(text or "").strip().split()).strip(" .!?")
    if not said or len(said.split()) > 12:
        return []
    low = [word.lower().strip(".,;:!?()") for word in said.split()]
    if not any(word in CARE_VERBS for word in low):
        return []
    if not A_HOW_OFTEN.search(said):
        return []
    # A question is not a practice: "how often should i feed them" is read by the ask readers.
    if ASKING.match(said) or MEASURE_ASK.search(said):
        return []
    if any(word in CARE_NOT_THE_THING for word in low):
        return []
    # The practice without the person and without the pronoun: "i feed them every week" is
    # "feed every week", and the thing goes in front of it.
    rest = re.sub(r"^\s*(?:i|we|im|i'm|ive|i've)\s+", "", said, flags=re.I)
    for word in sorted(POINTS_BACK, key=len, reverse=True):
        rest = re.sub(r"\b" + re.escape(word) + r"\b", "", rest, count=1, flags=re.I)
    rest = " ".join(rest.split())
    if not rest:
        return []
    things = _the_persons_own_words(memory)
    if not things or things[0] in low:
        return []  # nothing to write in, or the line names the thing itself and says what it is about
    return [" ".join((things[0] + " " + rest).split())]


# The little words a person puts in front of the asking: "and how long will it take".
_A_CONNECTIVE = frozenset("and so but also then ok okay please".split())


def a_faulty_thing(memory):
    """True when the chat is on a thing that has stopped working, not on a plan about one.

    "my boiler is broken" / "how long will it take" is a question about the repair, and the entry
    that knows the answer is filed under the boiler *and* the repair, so a measure ask carrying the
    thing alone reaches nothing. Only the line's own words decide: a fault said of the thing, with
    nothing being planned about it ("im thinking of getting a new boiler" is a plan, and the price
    of a new one is what that person wants).
    """
    said = " ".join(str(the_subject(memory) or "").split()).lower()
    if not said:
        return False
    if _the_answer_gave_a_time(memory):
        # The reply just before this line said how long its own steps take ("The checks take ten
        # minutes."), so "how long will that take" is asking about those steps: the clock is
        # already in the chat, and the repair the fault row knows is not what is being asked.
        return False
    return any(word in A_FAULT for word in re.split(r"[^a-z]+", said))


# A length of time in a reply already given ("ten minutes", "a couple of hours", "2 days").
_A_TIME_IN_A_REPLY = re.compile(
    r"\b(?:\d+|an?|one|two|three|four|five|ten|fifteen|twenty|thirty|forty|forty-five|fifty|"
    r"sixty|ninety|half an|a couple of|a few)\s*"
    r"(?:second|seconds|minute|minutes|hour|hours|day|days|week|weeks|month|months|year|years)\b",
    re.I)


def _the_answer_gave_a_time(memory):
    """Whether the reply just before this line said how long something takes."""
    turns = (memory or {}).get("turns") or []
    if not turns:
        return False
    return bool(_A_TIME_IN_A_REPLY.search(str(turns[-1].get("bot") or "")))


def the_thing(memory):
    """The phrase naming the thing the chat is on, without the words for how it is, or "".

    "my washing machine has stopped" is on the subject "washing machine stopped", and the thing is
    the washing machine. A measure ask written with one word of it ("how long will the machine
    take") reaches the row about how long machines last, where the phrase reaches the row filed for
    the washing machine's repair: an entry keyed on a phrase is only reachable with the phrase.
    """
    said = " ".join(str(the_subject(memory) or "").split()).lower()
    if not said:
        return ""
    kept = [word for word in re.split(r"[^a-z0-9]+", said)
            if word and word not in A_FAULT and word not in NOT_THE_THING
            and word not in MEASURE_WORDS and word not in ("the", "and", "for", "with")]
    return " ".join(kept[:4])


def subject_word(memory):
    """The thing the chat is on, in one word ("speech", "dog"), or "".

    `topics.subject` is the phrase the conversation is about ("worried speech", "getting a dog"),
    and the noun in it is the last content word that is not a feeling and not the verb of getting
    it. The thing is what a measure ask is asked about, so the noun is what is needed, not the
    phrase.
    """
    said = " ".join(str(the_subject(memory) or "").split()).lower()
    found = _the_noun_in(said)
    if found and all(word in A_GETTING for word in found):
        # The subject is the verb of buying rather than the thing ("buy" for "what do i need to
        # buy for a puppy"). The noun is in the person's line behind its preposition, so read
        # that line: the follow-up's "one" is the puppy, and the price row is about the puppy.
        newest = (memory or {}).get("topic") if isinstance(memory, dict) else None
        own = str((newest or {}).get("text") or "") if isinstance(newest, dict) else ""
        found = _the_noun_in(" ".join(own.split()).lower())
    if found and found[-1] in PLACE_WORDS:
        # The topic is the place the person asked about ("how long in the microwave") and the thing
        # they are asking about is the one the line before it is on ("how do i cook rice"). The
        # place is where it is done, not what it is.
        before = _the_record_before(memory)
        if before:
            found = _the_noun_in(" ".join(str(before.get("text") or "").split()).lower()) or found
    return found[-1] if found else ""


def _the_noun_in(said):
    if not said:
        return []
    return [word for word in re.split(r"[^a-z]+", said)
            if len(word) > 2 and word not in NOT_THE_THING and word not in MEASURE_WORDS
            and word not in A_FAULT
            and word not in ("the", "and", "for", "with", "some", "any", "new")]


def _the_record_before(memory):
    """The record the chat was on before the newest one, while it is the same conversation."""
    records = [record for record in ((memory or {}).get("topics") or [])
               if isinstance(record, dict) and record.get("text")]
    newest = (memory or {}).get("topic")
    now = str((newest or {}).get("text") or "")
    for record in reversed(records):
        if str(record.get("text") or "") != now:
            return record
    return None


# A line that says what the subject is for, not a thing of its own: "it would be for the kids",
# "it is for my daughter". The measure ask that follows is still about the subject.
A_PURPOSE = re.compile(
    r"\b(?:it|that|this|they|them|he|she)\s+(?:would\s+be|is|are|was|were)\s+(?:for|to\s+be)\b|"
    r"\b(?:for|with)\s+(?:the|my|our|his|her|their|a|an)\b", re.I)
# Words that end a line but are not the thing it is about.
NOT_A_THING_END = frozenset("""
not never no yes ok okay thanks thank please too also very really much many more less
good bad fine same sure well now then again already still just today tomorrow yesterday
week month year morning evening night day weekend ever yet either
one two three four five six seven eight nine ten eleven twelve
""".split())


def a_newer_thing(memory, word):
    """The thing the line just before the ask said they need, or "".

    "my car failed its mot" / "it needs a new spring" / "how much would that cost" is a question
    about the spring: the subject the chat opened with is the MOT, and the price of the test is not
    what is being asked. An English line puts the thing it is about at its end, so the last word of
    the line before the ask is the newer thing, when it is a noun of its own and not what the
    subject is for ("it would be for the kids" leaves the subject standing).
    """
    turns = [turn for turn in (memory or {}).get("turns") or [] if isinstance(turn, dict)]
    if not turns or not word:
        return ""
    last = " ".join(str(turns[-1].get("user") or "").lower().split()).strip(" .!?")
    if not last or A_PURPOSE.search(last):
        return ""
    tail = last.split()[-1].strip(".,;:!?")
    if (len(tail) < 4 or tail in VERBS or tail in NOT_A_THING_END or tail in POINTS_BACK
            or tail in A_FAULT):
        # "my boiler is broken" ends on how the thing is, not on a second thing they need: read as
        # the newer thing it hid the boiler, and the measure ask after it reached nothing.
        return ""
    if tail in ASPECT_NOUNS:
        return ""  # an aspect of the thing, not a thing of its own
    if tail == word or word in tail or tail in word:
        return ""
    return tail


# A trip is planned a part at a time. The place is in the chat ("im going to rome for three days
# in may") and the next line asks about one part of it ("and where should i eat", "where should i
# stay", "how many days", "what about the food"). The question filed for the two together is the
# one that knows - "where should i stay in rome" is the card about where to stay - and asked bare
# the line reached whatever the topic's newest words fit: "where should i stay" was answered with
# the day trips out of Rome, and "and where should i eat" with the same paragraph again.
#
# The part word picks the question, and only the part word: a line with a content word of its own
# names something ("where should i eat in florence") and is left to the ordinary paths.
A_TRIP_PART = (
    (re.compile(r"\b(?:stay|staying|hotel|hotels|accommodation|sleep|sleeping|hostel|hostels)\b"),
     "where should i stay in {place}"),
    (re.compile(r"\b(?:eat|eats|eating|food|restaurant|restaurants|dinner|lunch|breakfast|drink|"
                r"drinks|bar|bars|cafe|cafes|coffee|pizza|gelato)\b"),
     "where should i eat in {place}"),
    (re.compile(r"\b(?:see|sights|sightseeing|visit|visiting|museum|museums|gallery|galleries|"
                r"ruins|tour|tours)\b"),
     "what should i see in {place}"),
    (re.compile(r"\b(?:days?|long enough|enough time|how long)\b"),
     "how many days in {place}"),
    # No row for getting around: "how do i get around" already reaches the city's transport card
    # from the place in memory ("in rome: a ticket is EUR1.50..."), and asking the rewritten
    # question instead picked the rail card filed under "rome" - a worse answer to a line that
    # was already answered. The parts above are the ones main gets wrong, not the ones it gets
    # right.
    # The month is the whole of a common follow-up ("is it expensive" then "and in august"), and
    # the guide's when-to-go card answers it for the city on the screen: it names every month and
    # says which are good. "may" and "march" are left out because each is an ordinary word too
    # ("it may be expensive"), and a month named on its own is never a hedge in their case.
    (re.compile(r"\b(?:when|month|months|season|weather|climate|temperature|"
                r"january|february|april|june|july|august|september|october|november|december|"
                r"spring|summer|autumn|winter)\b"),
     "when should i go to {place}"),
    # What the trip costs, and nothing more specific: "whats lisbon like" / "and the food like
    # there" / "is it expensive" left the cost question without a city, and the household
    # shopping plan answered it. Last in the list, because a line that names a part of the trip
    # asks about that part: "how much is a coffee" is about coffee, which the eating card knows,
    # and it only becomes a money question when nothing else in the line fits.
    (re.compile(r"\b(?:expensive|pricey|cost|costs|costing|afford|budget|spend|"
                r"how much)\b"),
     "is {place} expensive"),
)

# The words an elliptical ask is made of. Anything else in the line is a thing of its own.
_ASK_FILLER = frozenset("""
a an the and but or so also then too now ok okay please about for to in on at of it that this
i we you me us my our your there here any some much many more most best good worth should could
would can will do does did is are was were be been get got have has had going go stay stay
some anywhere somewhere place places area areas neighbourhood neighborhood part parts spot spots
nice pleasant decent good best spot
what where which how when why who whats like tell me info advice recommend recommends
recommendation recommendations suggest suggestion suggestions
need needs needed want wants wanted enough require required take takes give gives
one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen
sixteen seventeen eighteen nineteen twenty couple few several
""".split())

# The line that named the place has to be a trip: "i live in leeds" puts a place in the chat and
# is not one, so the part ask after it is about something else entirely.
_GOING_AWAY = re.compile(
    r"\b(?:going|go|goes|off|heading|trip|trips|holiday|holidays|travel|travelling|traveling|"
    r"visit|visiting|fly|flying|flight|flights|weekend|weekends|break|away|abroad|booked|booking|"
    r"planning|thinking about|considering|looking at)\b", re.I)


def _the_trip_place(memory):
    """The place the chat is going to, in the person's own spelling, or ""."""
    known = (memory or {}).get("user")
    if not isinstance(known, dict):
        return ""
    places = [str(place).strip() for place in (known.get("places") or []) if str(place).strip()]
    if not places:
        return _the_place_the_bot_just_named(memory)
    place = places[-1]
    said = place.lower()
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    named_at = -1
    for index in range(len(turns) - 1, -1, -1):
        line = " ".join(str(turns[index].get("user") or "").lower().split())
        if not re.search(r"(?<![a-z])" + re.escape(said) + r"(?![a-z])", line):
            continue
        # The newest line that named it decides: a later "i live in rome" is a home, not a trip.
        if not _GOING_AWAY.search(line):
            return ""
        named_at = index
        break
    if named_at < 0:
        plan = " ".join(str(known.get("plan") or "").lower().split())
        if not (said in plan and _GOING_AWAY.search(plan)):
            return ""
    # A card the bot gave after that line is the place the chat is on now: "we're going to italy in
    # june" makes Italy the trip, then the answer to "rome and florence probably" is the Florence
    # card, so "how many days would we need" is the days of Florence and not of the country.
    card, card_at = _the_opening_place_at(memory)
    if card and card_at > named_at:
        return card
    return place
    # No line called it a trip, but the bot's last answer is a card about that place: "tell me
    # about lisbon" is answered by the Lisbon card, which opens "In Lisbon:". The chat is on the
    # city all the same, so the part ask after it ("is it expensive", "where should i eat") is
    # about Lisbon. A place the person lives in is not that chat, and the words for a home keep
    # this from turning "i live in rome" into a holiday.
    card = _the_place_the_bot_just_named(memory)
    if card and said in card.lower():
        return place
    return ""


# A home is not a place you are going to: "i live in rome" followed by "is it expensive" is a
# question about living there, and the holiday day rate is the wrong answer.
_LIVING_THERE = re.compile(
    r"\b(?:live|lives|lived|living|moved|moves|moving|relocate|relocated|relocating|grew up|"
    r"born|home|hometown|my flat|my house)\b", re.I)


_A_TIME_WORD = frozenset((
    "january", "february", "march", "april", "may", "june", "july", "august", "september",
    "october", "november", "december", "spring", "summer", "autumn", "winter", "the morning",
    "the evening", "the afternoon", "the end", "the meantime", "general", "fact", "short",
    "total", "terms", "the", "a", "an", "its", "their", "addition", "practice", "reality",
))


def _the_opening_place(memory):
    """The place a card on the screen opens on, or "".

    A card about one place says so in its first words: "In Lisbon: Alfama on foot...", "In Rome
    the cheap meal is pizza al taglio...". That is the bot naming the place the whole answer is
    about, which is as good as the person naming it for reading the next line.
    """
    return _the_opening_place_at(memory)[0]


def _the_opening_place_at(memory):
    """(the place a card on the screen opens on, the turn it came on), or ("", -1)."""
    turns = (memory or {}).get("turns")
    if not isinstance(turns, list) or not turns:
        return "", -1
    # The newest card wins, and a card is not always the last thing said: "whats lisbon like" is
    # the guide, then "is it expensive" is the day rate, then "and in august" is still Lisbon.
    for back, turn in enumerate(reversed(turns)):
        if not isinstance(turn, dict):
            continue
        opening = re.match(r"\s*in\s+(.{2,40}?)(?=[,:.!?]|\s(?:the|a|an|is|it|you|we)\b)",
                           str(turn.get("bot") or ""), re.I)
        if not opening:
            continue
        place = opening.group(1).strip()
        # A time word is not a place: "In May, Lisbon is warm" opens on the month.
        if place.lower() in _A_TIME_WORD:
            continue
        # Neither is a thing the card happens to start with: a card can open "In the fridge,
        # on a plate on the bottom shelf: ..." or "In a hot pan, ..." and mean an object. A place
        # is a name, so it is written without an article in front of it and with its capital:
        # "how should i thaw mince" then "is it expensive" was answered "A fridge freezer is
        # about 25p a day", a price for the appliance, where the question was about the mince.
        if re.match(r"(?i)(?:the|a|an|your|my|his|her|their|our|this|that)\b", place):
            continue
        if not place[:1].isupper():
            continue
        return place, len(turns) - 1 - back
    return "", -1


def _the_place_the_bot_just_named(memory):
    """The place on the card the bot just gave, when no line in the chat named one.

    "tell me about lisbon" names no trip - there is no going, no week, no booking - so the store
    files no place and the food-and-cost follow-ups after the card lost the city: "and the food
    like there" / "is it expensive" got the household shopping plan. The card itself says which
    city the chat is on. A line that puts the person at home keeps this out: "i live in rome"
    followed by "is it expensive" is not a holiday, and the card is what answers "what's it like
    there" anyway.
    """
    place = _the_opening_place(memory)
    if not place:
        return ""
    for turn in (memory or {}).get("turns") or []:
        if isinstance(turn, dict) and _LIVING_THERE.search(str(turn.get("user") or "")):
            return ""
    return place


def a_part_of_the_trip(text, memory):
    """The line as the question it asks about the place the chat is on, or "".

    See A_TRIP_PART: "and where should i eat" after a trip to Rome is "where should i eat in
    rome", and the card filed for that question is the one that answers it.
    """
    place = _the_trip_place(memory)
    if not place:
        return ""
    said = " ".join(str(text or "").lower().split()).strip(" .!?")
    if not said or len(said.split()) > 8:
        return ""
    part = ""
    words = set()
    earliest = None
    for pattern, asked in A_TRIP_PART:
        found = set(pattern.findall(said))
        if not found:
            continue
        # The part the line leads with is the part it asks about: "how many days should i stay" is
        # the number of days, and the "stay" in it comes after the days; "where should i stay for
        # three days" is where, and the days come after the stay. The first pattern that matches
        # would read the first as a where-to-stay ask and leave "days" as a word of its own.
        at = min(found_.start() for found_ in pattern.finditer(said))
        if earliest is None or at < earliest:
            part = asked
            earliest = at
            words = set(re.split(r"[^a-z]+", " ".join(found))) | found
    if not part:
        return ""
    for matched in words:
        # "i want to stay in a hostel" names the kind of place they have already picked, so it is
        # not asking where to stay in this city: the article in front of the part word makes the
        # word a thing rather than a category ("somewhere to stay" and "any hotels" have none).
        if re.search(r"\b(?:a|an)\s+" + re.escape(matched) + r"\b", said):
            return ""
    for word in re.split(r"[^a-z']+", said):
        if len(word) < 3 or word in _ASK_FILLER or word in words:
            continue
        if word in ("day", "days") and part.startswith("how many days"):
            continue
        return ""
    return part.format(place=place.lower() if place.isupper() else place)

def asks_a_part_of_the_trip(text, memory):
    """True when the line asks about a part of the trip, whether it names the place or not.

    "how many days do i need" after the card for a city is the days question for that city, and
    the trip reader writes it out ("how many days in berlin") for the entry that answers it. The
    same question with the city already in it - "how many days in berlin" as the person first
    typed it, or as the reader wrote it - is the same ask, so the place can also come out of the
    line before the rest is read as the part.
    """
    if a_part_of_the_trip(text, memory):
        return True
    place = _the_trip_place(memory)
    said = " ".join(str(text or "").lower().split())
    name = place.lower()
    if not name or name not in said:
        return False
    return bool(a_part_of_the_trip(said.replace(name, " "), memory))


# A line that rules a food out of the dish being made is not a move to that food: "i have no
# eggs" after a cake is the cake without eggs, and "no butter left" is the butter the cake is
# short of. The food there is an ingredient, and the dish is still the one in hand.
LIMIT = re.compile(
    r"\b(?:no|not|dont|doesnt|didnt|havent|isnt|without|ran out|run out|only got|only have|"
    r"short of|lacking|instead|left)\b", re.I)


def the_food_it_is_about(understood, memory):
    """The food the conversation has moved to, when a bare line's "it" is that food.

    "i burnt the rice" then "can i still eat it" is a question about the rice, and the store
    holds it: the understanding engine has already read what the bare line leans on, and that
    is `leans_on.subject`. The knowledge base's own scan for a dish does not know it - a food
    with no plan of its own (rice, pasta, potatoes) is skipped over - so it hands back the last
    dish it heard of, which after this chat is a cake two turns back, and the cake's "3 days in
    a tin" is a keeping fact about the wrong food.

    Two things stop it. The line naming the food itself means the entries can read it as it
    stands, so nothing has to be put back in. And the line the food came from ruling it out of
    the dish ("i have no eggs", "no butter left for the cake") is a limit on the dish, not a
    move to another one: the dish is still in hand.
    """
    if not isinstance(understood, dict) or not isinstance(memory, dict):
        return ""
    record = understood.get("leans_on")
    if not isinstance(record, dict):
        return ""
    food = " ".join(str(record.get("subject") or "").split()).lower()
    if not food:
        return ""
    line = " ".join(str(understood.get("clean") or understood.get("text") or "").split()).lower()
    if not line or food in line:
        return ""  # the line names it: the entries reach it on their own
    raised = " ".join(str(record.get("text") or "").split()).lower()
    if raised and LIMIT.search(raised):
        return ""  # a limit on the dish, not a move to the food
    return food
