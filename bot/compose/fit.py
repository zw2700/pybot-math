"""What kind of answer a line wants, and whether a reply gives it.

The understanding engine says what a line is about and which question words it carries
(`memory["understood"]["asks"]`). It does not say what shape of answer the person is owed: a
`how_long` line wants a time, a `where` line a place, a `which` line a pick, a bare `yesno` a
verdict. This module reads that shape from the whole line, and checks a reply for it.

The reading runs once per turn in `bot/modules/intent.py`, which writes
`memory["understood"]["wants"]` before any other observer runs. The check is for the composer and
for `tools/intent.py`: a reply on the right topic that does not answer the question - the story of
what rice is for, for "how long does rice take" - is a miss even though it reads well.

The labels are the lane's fixed list, and a module may return None rather than guess:

    time      a duration or a clock time ........ "about 12 minutes", "by Friday", "1 to 1.5 bar"
    amount    a quantity, price or sum .......... "about 2 kilos", "£3.50", "21 ÷ 3 = 7"
    place     somewhere to go ................... "the post office", "Antarctica"
    person    who to ask ........................ "the vet", "your GP", "Napoleon"
    meaning   what the thing is ................. "An APR is the yearly cost..."
    yesno     a yes or a no ..................... "Yes", "Straight in is fine", "No need"
    pick      which of two or more .............. "Replace it", "Oat milk for coffee"
    steps     what to do, in order .............. "First..., then..."
    options   a few ideas ....................... "one, or two, or three" (not one idea)
    reason    why it happens .................... "because...", "that's why..."
    opinion   what the bot makes of it .......... not checkable by words
    advice    what the person might do .......... not checkable by words
    comfort   an answer to something hard ....... not checkable by words
    answer    anything else ..................... not checkable by words

`wants` reads the shape. `gives` says True when a reply's opening sentence gives that shape,
False when it can say what the reply gives instead (a shrug, or an unmistakable other shape), and
None where words cannot tell - the soft labels above, and an opening the cue list has nothing
for. It is a finder, not a mark: "eight to ten years" is a time without a digit and "straight in
is fine" is a yes without the word yes, so every check is written to be right more often than it
is wrong and to say nothing where it cannot be sure.
"""
import re

# The answer shapes, in the lane's fixed words. Nothing outside this list is written to `wants`.
TIME = "time"
AMOUNT = "amount"
PLACE = "place"
PERSON = "person"
MEANING = "meaning"
YESNO = "yesno"
PICK = "pick"
COMPARE = "compare"
STEPS = "steps"
OPTIONS = "options"
REASON = "reason"
OPINION = "opinion"
ADVICE = "advice"
COMFORT = "comfort"
ANSWER = "answer"

WANTS = (TIME, AMOUNT, PLACE, PERSON, MEANING, YESNO, PICK, COMPARE, STEPS, OPTIONS, REASON,
         OPINION, ADVICE, COMFORT, ANSWER)

# The shapes a check cannot read out of the reply's own words. A condolence or an opinion is a
# reply to the whole line, not a figure or a place, and a word list that tried to grade one would
# be wrong more often than right, so `gives` says None for them and no miss is counted.
SOFT = frozenset((OPINION, ADVICE, COMFORT, ANSWER))

# The kinds of answer understanding's `asks` labels point at, strongest first. Two things to know:
#
# - A line that names two things and asks which is a `pick` before it is anything else: "should i
#   get it repaired or a new one" is the same question as "repair or replace", so `choice` is read
#   before `yesno` even though understanding labels both.
# - `what should i cook tonight` arrives as `steps` (understanding reads the `what should` as a
#   question of method), and that is the understanding lane's to fix, not a second reading here.
ASKED_FOR = (
    (PICK, frozenset(("choice", "compare", "which"))),
    (MEANING, frozenset(("definition",))),
    (PLACE, frozenset(("where",))),
    (PERSON, frozenset(("who",))),
    (REASON, frozenset(("why",))),
    (TIME, frozenset(("how_long",))),
    (AMOUNT, frozenset(("how_much", "how_often"))),
    # Understanding labels any line holding a number as `maths` ("my mums birthday is on the 3rd
    # of may", "half a roast chicken left over"), so a sum is read off a question and no other
    # line is given a figure to answer.
    (AMOUNT, frozenset(("maths",))),
    (OPTIONS, frozenset(("list",))),
    (STEPS, frozenset(("steps", "how"))),
    (PICK, frozenset(("recommend",))),
    (YESNO, frozenset(("yesno",))),
)


# A verdict ask about the person's own case is answered by the rule that settles it: "Money against
# value: if the quote is more than the car is worth ... let it go", "There is no single age: what
# matters is whether they can get help", "A cut needs closing properly if the edges fall apart".
# The person asked whether, and the reply hands them the test their own case falls either side of -
# the answer a friend gives when the honest reply is "that depends on two things only you know". The
# conditional is the mark of it. A shrug that only says "it depends on two things" names no test,
# and a reply that asks the person anything back has given them nothing, whatever it holds.
A_RULE_THAT_SETTLES_IT = re.compile(
    r"\b(?:if|when|whenever|whether|once|until|unless|as long as)\b", re.I)


# An offer is not a test. "I'm here if you want to dig into any of that", "say more if it helps",
# "let me know if that works" all hold the word `if` and none of them says what the person's case
# turns on, so the check credited a reply that gives no verdict at all. The words in front of the
# `if` are what tell an offer from a rule, and "what if" and "as if" are not conditions either.
AN_OFFER_NOT_A_TEST = re.compile(
    r"\b(?:here|happy|around|about|available|back|on hand)\s+if\b"
    r"|\b(?:say|tell me|tell us|let me know|ask|shout|message|write|reply|try)\b[^.]{0,24}?\bif\b"
    r"|\b(?:what|as)\s+if\b", re.I)
# The test has to be followed by the standing it settles: "if it smells sour, bin it", "once it is
# above 38 it is a fever". A condition with nothing on the far side is a hedge, not an answer.
A_STANDING_AFTER_THE_TEST = re.compile(
    r"\b(?:is|are|was|were|means|counts as|needs?|should|worth|too|enough|fine|ok|okay|safe|"
    r"normal|risky|a problem|gets?|lasts?|keeps?|stays?|throw|bin|toss|see (?:a|the|your)|"
    r"ring|call|matters|turns on|decides|depends)\b", re.I)


def _the_rule_settles_it(opening, line, reply=None):
    """True when the reply gives the test the person's case turns on, and asks them nothing.

    The condition has to be in the opening, where a verdict lives. Read over the whole reply it
    credited advice that answers another question: "my mum might come too, is that too much food"
    was told how to set a boundary with a parent, and the `if` in the fifth line of that made it
    an answer to a question about catering.
    """
    text = " ".join(str(reply or opening).split())
    if "?" in text:
        return False
    if AN_OFFER_NOT_A_TEST.search(opening):
        return False
    found = A_RULE_THAT_SETTLES_IT.search(opening)
    if not found:
        return False
    # `once` and `until` mark when a thing ends as often as they mark the test: "four things, all
    # before you book: a passport each ... until it is in your hands" is a list, and read as the
    # test it credited a passport answer to "do i need to treat the whole family". In the first
    # clause they still settle an ask - "once it is opened, a tub keeps about three days" - so only
    # a later `once|until|unless` is refused.
    if found.group(0).lower() in ("once", "until", "unless") and \
            re.search(r"[:;]", opening[:found.start()]):
        return False
    # A condition that opens the reply is a preamble, not the test: "When you get home, take the
    # bins out", "If you are passing the shop, pick up some milk" are jobs wrapped round a
    # `when`/`if`, and the boiler line "When the heating starts, it bangs because air is in the
    # pipes" names a cause rather than a verdict. In the replies that do settle an ask the
    # condition comes after the thing's standing: "Money against value: if the quote is more than
    # the car is worth", "A cut needs closing properly if the edges fall apart", "You are
    # dehydrated if your pee is dark", "It earns its price when it lasts ten years".
    # `once`, `until` and `unless` are not preambles when they open: "Once opened, a tub of
    # tzatziki keeps about 3 days" and "it holds them until about 22kg" are verdicts, and one of
    # them opens on the condition.
    if not opening[:found.start()].strip() and \
            found.group(0).lower() in ("if", "when", "whenever", "whether"):
        return False
    return A_STANDING_AFTER_THE_TEST.search(opening[found.end():]) is not None

# The whole line as people wrote it, for the readings that need more than the `asks` labels.
# The ask-nouns that are plural in the asking, whatever the line says: a tip is never one thing.
A_FEW_THINGS = re.compile(
    r"\b(?:tips?|ideas?|suggestions?|recommendations?|pointers?|hacks?|options)\b", re.I)


def _said(understood):
    parts = []
    for key in ("norm", "norm_text", "clean", "text"):
        value = understood.get(key)
        if isinstance(value, (list, tuple)):
            value = " ".join(str(word) for word in value)
        if isinstance(value, str) and value:
            parts.append(value)
    return " ".join(" ".join(parts).lower().replace("\u2019", "'").split())


# Who the line is about, when the who beside them belongs to them rather than asking for a name.
def _a_who_a_person_owns(understood):
    """True when the who in the line belongs to the person the line is already about.

    "something for my sister who just had a baby", "how do i deal with a boss who shouts":
    understanding has read the sister and the boss as a person of the line, and the who standing
    right after them is the relative pronoun - the ask is a present or for advice, not a name.
    Read as a who-question, 33 of the deck's 349 person wants owed a name no gift or advice reply
    could give, and each of those replies was counted a miss. A who the line opens on, a who that
    asks after a new person ("my daughter wants to know who mozart was") and a who with no
    person before it ("i got whiplash in a crash who pays") still owe the name.
    """
    words = understood.get("words")
    entities = understood.get("entities")
    if not isinstance(words, (list, tuple)) or not isinstance(entities, (list, tuple)):
        return False
    for entity in entities:
        if not isinstance(entity, dict) or entity.get("type") != "person":
            continue
        at = entity.get("at")
        if not isinstance(at, int) or at < 0:
            continue
        after = at + len(str(entity.get("text") or "").split())
        # "my brother whos 30 is coming to stay" writes the relative pronoun as `whos`, and the
        # who standing right after the brother is the brother's, not a question about a stranger.
        word = str(words[after]).lower().strip("'\u2019") if 0 < after < len(words) else ""
        if word.startswith("who") or word == "that":
            return True
    return False


# Two named sides: understanding labels the choice, the comparison or the "which".
PICK_SIDES = frozenset(("choice", "compare", "which"))
# Two named sides are not always a choice to make. "What is the difference between a sprain and a
# strain" comes in as `compare`, but nobody is asking the bot to prefer one: the answer is what
# each of the two is. The same line answered with a pick would be answering a question the person
# did not ask, so the difference questions are read for the meaning and the contrasts are read
# further down by the ordinary side rule ("which is better, the train or the coach" is a pick).
# A difference that is not the object of the question - "does that make a difference", "how long
# until i notice a difference", "my week is different", "a different charger" - is not this ask.
DIFFERENCE = re.compile(
    r"\bwhat(?:['\u2019]?s| is| are| was| were)?\b(?:\s+[\w'-]+){0,3}\s+differences?\b"
    r"|\bhow (?:is|are|does)\b[^.?!]{0,40}\b(?:different|differ)\b\s*(?:from|to)\b"
    r"|^[\W]*(?:the )?differences? between\b", re.I)
# The asks that are a real question of their own, and so beat the yes/no understanding labels on
# any line that opens on an auxiliary. "how long do i boil an egg" and "how much should i save"
# arrive as `how_long`/`how_much` *and* `yesno` (the "do i" is read as the yes/no), and the figure
# is what the person is waiting for. "recommend" is deliberately not here: "is it worth it" is a
# verdict with a recommendation word in it, not a request to pick one of two things. Neither is
# the bare `how` or `maths` label, which are loose: "is that how it works" is a yes/no about the
# bot's last answer, and "can i freeze double cream" carries `maths` for the word "double".
SPECIFIC_ASKS = frozenset((
    "choice", "compare", "which", "definition", "where", "who", "why", "how_long",
    "how_much", "how_often", "list", "steps"))
# Every kind of a thing asked as a menu: "what kinds of coffee are there" asks for the kinds, not
# for what coffee is, and understanding reads the "what" as a definition. The identifying form is
# a different question - "what kind of dog is that" asks what the one in front of them is - so it
# is named here and stood down, rather than left to the reply to sort out.
KINDS_OF = re.compile(
    # The set of kinds asked for as a set: "what kinds of coffee are there", "what types of
    # insulation can i get", "what sorts of food can i freeze", "what kinds of things can go wrong
    # with a boiler". The tail is what makes it a menu - a there-is or a can - because the same
    # words with an "is best" or an "is good with kids" are asking which one kind suits them.
    r"\b(?:what|which) (?:kinds?|types?|sorts?|varieties|styles|brands|makes|models)"
    r"(?: of (?:[\w'-]+ ){0,4})?"
    r"(?:are there|are available|is there|exist|do you|would you|can|could)\b"
    r"|\bwhat (?:are|were) the (?:kinds?|types?|sorts?|varieties|styles)\b"
    r"|\bwhat (?:are|were) (?:my|the|our) (?:options|choices)\b"
    r"|\bwhat (?:options|choices) (?:do i|do we|have i|are there)\b"
    r"|\b(?:any|other|more) (?:options|choices|alternatives)\b"
    r"|\bwhat else (?:is|are) (?:there|out there)\b"
    r"|\bwhat (?:is|are) available\b", re.I)
NOT_KINDS_OF = re.compile(
    r"\bwhat (?:kind|type|sort) of (?:a )?(?:[\w'-]+ ){0,3}(?:is|was|are|were) "
    r"(?:that|this|it|those|these|he|she)\b"
    # Nor is the kind that would suit them a menu of kinds: "what sort of dog would suit that" is
    # asking which one fits the life they have, which is advice about their situation.
    r"|\bwhat (?:kind|type|sort) of (?:[\w'-]+ ){0,3}(?:would|will|should|could|might|suits?|fits?)\b",
    re.I)

# The method asked for as a set of steps: "what are the steps to reset a boiler", "what is the
# process for getting a visa", "step by step for a bookshelf", "what are the stages of buying a
# house". The words "what are the ..." are the same words as a menu of options, so the method is
# read before the menu: the person asked for the order to do things in, not a few ideas to choose
# between, and a reply that lists the kinds available instead is the wrong answer to it.
STEPS_ASK = re.compile(
    r"\bwhat (?:are|is) the steps\b|\bsteps (?:to|for|in)\b|\bstep[- ]by[- ]step\b"
    r"|\bwalk me through\b|\bwhat(?:'s| is) the process\b|\bthe process (?:for|of|to)\b"
    r"|\bhow do i go about\b|\bwhat order\b|\bin what order\b"
    r"|\b(?:the )?(?:best|right|correct|proper) order (?:to|for|in)\b", re.I)
# A count of steps is a figure, not a method: "how many steps a day should i walk", "how many
# steps in a mile", "steps per mile", "10000 steps in miles". The word is the same and the answer
# wanted is a number, so the counted forms are read before the method.
COUNTED_STEPS = re.compile(
    r"\bhow many steps\b|\bsteps? per\b|\bsteps? in (?:a|one) (?:mile|km|day)\b"
    r"|\bstep count\b|\b\d{3,} steps\b", re.I)
# The members of a set asked for by the set's own word: "what are the early signs of dehydration",
# "what are the symptoms of a chest infection", "what are the stages of labour". Understanding
# reads the bare "what are" as a request for the meaning of a word, so the line came out wanting a
# definition - and the reply that lists four signs was charged for not defining anything. The
# answer wanted is the set, which is a menu of things rather than a definition of one.
MEMBERS_ASK = re.compile(
    r"\bwhat (?:are|were) the (?:early |first |main |usual |common |classic |key |warning |"
    r"typical |initial )?(?:signs?|symptoms?|stages?|phases?)\b"
    r"|\bwhat (?:signs?|symptoms?|stages?)\b[^.?!]{0,30}\b(?:should|would|do|can|might) "
    r"(?:i|you|we) (?:look|watch|expect|see)\b"
    r"|\bwhat are the (?:warning|telltale) signs\b", re.I)

# A comparison asks for both sides and then what sets them apart, so it is a shape of its own and
# not a pick: "compare a dehumidifier and a window vac", "gas vs electric hob", "how does a heat
# pump compare with a gas boiler", "what sets a leasehold apart from a freehold", "is a heat pump
# better than a gas boiler". The verdict form of the same question - "is it worth it", "should i
# take the train or the coach" - is asking for a decision, and is read before this by its own ask.
COMPARISON = re.compile(
    r"\bcompare[ds]?\b|\bcomparing\b|\bvs\.?(?=\s|$)|\bversus\b"
    r"|\bdifferences? between\b"
    r"|\bhow (?:is|are|does|do|did) [^.?!]{0,40}\b(?:different|differ|compare)\b"
    r"|\bwhat sets? [^.?!]{0,30}\bapart\b|\bsets? [^.?!]{0,30} apart\b", re.I)
# One thing said to be a comparative of the other is a comparison too - "is a loan cheaper than a
# credit card", "is a plank better than a sit up" - but only when the line is asking something.
# "Some people say its better than butter" and "better than i expected" are the person's own
# remarks, and neither owes both sides back.
COMPARED = re.compile(
    r"\b(?:better|worse|cheaper|dearer|quieter|louder|faster|slower|easier|harder|healthier|"
    r"safer|simpler|tastier|stronger) than\b", re.I)
# The words that make the same two things a decision rather than a survey of them.
NOT_A_COMPARISON = re.compile(
    r"\b(?:should i|shall i|worth (?:it|doing|the)|for me|which should i|which one should i|"
    r"is it better to|would you)\b"
    # The comparing the person does themselves is news, not a request: "i compare myself to my
    # sister all the time" is telling the bot something and owes no comparison back.
    r"|\b(?:i|we) (?:always |still |keep |often |just )?compare\b"
    # "How do i tell the difference" and "how do i compare two mortgages" ask for the method of
    # comparing, which is steps about their own job, not a comparison handed back.
    r"|\bhow (?:do|can|should|would|could) (?:i|we)\b"
    # And "better than i expected" is how the person judges something, not two things put together.
    r"|\b(?:better|worse) than (?:i|we|you|they|she|he) (?:expected|thought|hoped|feared|looked)\b",
    re.I)

# The two things a comparison puts together, in the words the line uses to put them: "between X and
# Y", "X vs Y", "X compared with Y", "X different from Y", "X cheaper than Y". A side stops at the
# joining word, so "between an ssd and an hdd" gives "ssd" and "hdd" and not "ssd and".
_SIDE = r"([\w'-]+(?: (?!and\b|from\b|than\b|vs\b|versus\b)[\w'-]+)?)"
_THE = r"(?:a |an |the )?"
SIDE_PAIRS = (
    re.compile(r"\bbetween " + _THE + _SIDE + r" and " + _THE + _SIDE, re.I),
    re.compile(r"\bcompare[sd]? " + _THE + _SIDE + r" (?:and|with|to) " + _THE + _SIDE, re.I),
    re.compile(_SIDE + r" apart from " + _THE + _SIDE, re.I),
    re.compile(_SIDE + r" (?:vs\.?|versus) " + _THE + _SIDE, re.I),
    re.compile(_SIDE + r" compar(?:e|ed) (?:with|to) " + _THE + _SIDE, re.I),
    re.compile(_SIDE + r" (?:is |are |was |were )?(?:comparable to) " + _THE + _SIDE, re.I),
    re.compile(_SIDE + r" (?:is |are |was |were )?(?:different|differs?) (?:from|to) "
               + _THE + _SIDE, re.I),
    re.compile(_SIDE + r" (?:better|worse|cheaper|dearer|quieter|louder|faster|slower|easier|"
               r"harder|healthier|safer|simpler|tastier|stronger) than " + _THE + _SIDE, re.I),
)
# The words that ask for the two things to be put side by side whatever the line's shape is:
# "compare a dehumidifier and a window vac" is an instruction with no question mark in it.
EXPLICIT_COMPARE = re.compile(
    r"\bcompare[ds]?\b|\bcomparing\b|\bvs\.?(?=\s|$)|\bversus\b|\bdifferences? between\b",
    re.I)


def _names_a_pair(said):
    """True when the line itself names the two things it is about, as a comparison has to."""
    return any(pattern.search(said or "") for pattern in SIDE_PAIRS)


def _asks_about_them(understood, said):
    """True when the line is asking about the pair rather than telling the bot something about it.

    "Hows that different" carries the words of comparing but no pair, and it is a question about
    the bot's own last answer, so it falls through to the follow-up rule and keeps the shape it
    followed. "I think im being underpaid compared to the new guy" names a pair and is still news.
    """
    if understood.get("intent") == "news":
        return False
    return EXPLICIT_COMPARE.search(said or "") or understood.get("kind") == "question"


# A negative that is a request for help, not a question about the bot.
# Who to go to, said with the words of a help ask: "who can help me with my debts".
OPEN_WHO_HELP = re.compile(r"^\W*who\b[^.!?]{0,40}\bhelp\b", re.I)
HELP_ME = re.compile(r"\b(?:can|could|would|will) you help me\b|\bhelp me (?:with|to|out)\b", re.I)
# The fix itself asked for: "whats the fix for a squeaky door", "any cure for hiccups", "the fix
# for a leaky tap", "whats the remedy for a nettle sting". A description of the fault, a price or
# an explanation answers a different question, and the method is what is owed. A yes/no about
# whether a thing can be put right - "is there a cure for osteoarthritis", "can it be fixed" -
# names no fix for the line to be given, so it keeps its yes or no.
FIX_ASK = re.compile(
    r"\b(?:what(?:'?s| is| was)?|any|the|a)\s+(?:quick |easy |simple |cheap |good |real )?"
    r"(?:fix|cure|remedy)\s+(?:for|to)\b"
    r"|\b(?:fix|cure|remedy) for (?:my|the|a|an|this|that)\b"
    # The fault behind a whole situation: "my back hurts sitting all day, whats the fix", "my nan
    # cant hear me on video calls, whats the fix" name the fault in the setting and ask the way out
    # of it at the end, where no "for" follows.
    r"|\b(?:what(?:'?s| is| was)|any)\s+(?:the\s+)?(?:quick |easy |simple |cheap |good |real )?"
    r"(?:fix|cure|remedy)\s*[?.!]*\s*$", re.I)

# The bare ask for help, which is the same request as "help me with": "help me plan a week of
# meals", "help me write a cv", "i need help planning meals", "help me sort out my debts". HELP_ME
# above needs the "with" or the "can you", so these lines were read as asking for nothing and every
# reply passed unseen. What is excluded is a choice, because that is a pick and the pick arms below
# read it: "help me choose a laptop", "help me decide between two jobs".
HELP_ASK_ANY = re.compile(
    # The ask opens the line: "help me plan my week", "ok so help me write a cv", "i need help
    # planning meals". A "help me" further in is describing something else - "should i have a beer
    # to help me sleep" is a yes/no about the beer, and reading it as a steps ask loses the verdict.
    r"^\W*(?:(?:hi|hey|hello|ok|okay|so|right|please|sorry|and)\b[ ,]*)*"
    r"(?:(?:can|could|would|will) you\s+)?"
    r"(?:help (?:me|us)|i need help|i could do with (?:some )?help|give me a hand)\b"
    # A choice is a pick and the pick arms below read it: "help me choose a laptop", "help me
    # decide between two jobs". A thing to say or name is a draft or a few options, not a method:
    # "help me word a text to my neighbour", "help us name our team", "help me come up with a name
    # for our pub quiz team" - reading those as steps flags the good reply a miss.
    r"(?!\s+(?:choose|choosing|pick|picking|decide|deciding|select|selecting|compare|comparing"
    r"|name|naming|word|wording|come up with)"
    r"\b|\s+between\b|\s+which\b)", re.I)
# A help ask that names no task has no method to give: "i need help", "i need help with
# something", "i need help but i dont know what with". The right reply asks what is going on, and
# reading the line as a steps ask scored that reply a miss. What follows the ask is read, because
# the task is what the method is for: "help me plan a week of meals" names one and keeps its steps.
HELP_ASK_NO_TASK = re.compile(
    r"^[\s,.;:!?\-]*(?:(?:with|about|on)\s+(?:something|anything|stuff|it|this|that)\b)?"
    r"[\s,.;:!?\-]*$"
    r"|\b(?:dont|don'?t|do not) know (?:what|where|how)\b|\bnot sure what\b", re.I)
# Where the help is said, for a line the engine has already marked as a help ask: `help_ask` is
# written for "i need help" as well as for "anything i can do about it", and only the first of
# those has a task after it to read.
HELP_WORD = re.compile(
    r"\b(?:help(?: me| us)?|i need help|i could do with (?:some )?help|give me a hand)\b", re.I)


def _a_help_ask_that_names_nothing(said):
    """True when the line asks for help and names no task to be helped with.

    "i need help", "i need help with something", "i need help but i dont know what with" ask for
    help and say nothing about what with, so the reply that asks what is going on is the right one
    and there is no method to give. "anything i can do about it" carries no help word at all and
    keeps its steps.
    """
    match = HELP_ASK_ANY.search(said or "") or HELP_WORD.search(said or "")
    rest = (said or "")[match.end():] if match else (said or "")
    return bool(HELP_ASK_NO_TASK.search(rest))
# A how that wants a figure rather than a method. A length of time - how soon, how early, how
# quickly, how long - is a time; any other measure word ("how much", "how many", "how often",
# "how hot", "how hard") is an amount, and the figure is the answer to all of them. The measure
# word is read from the text because understanding carries only some of them as a label: "how hot
# should the oven be" arrives as a bare `how`, which on its own is a method.
# The person's own how is a method: "how do i cancel my disney plus", "how do i know what size".
HOW_I = re.compile(r"\bhow (?:do|can|could|should|would) i\b", re.I)
# The person weighing their own life against someone else's is not a method for two things:
# "how do i compare myself to others", "how do i compare to my sister".
COMPARE_MYSELF = re.compile(
    r"\bcompar(?:e|ing)\b[^.?!]{0,14}\b(?:myself|ourselves)\b"
    r"|\bcompare\s+(?:to|with)\s+(?:me|my|us|our|him|her|them|others)\b", re.I)
HOW_SOON = re.compile(r"\bhow (?:soon|early|quickly|long)\b", re.I)
# A line that opens "how do i ..." is asking for the method, and a "how long" further in it is the
# word "long" inside the thing asked about: "how do i do long division" and "how do i do long
# multiplication" carry the how_long label off the "long" in the subject, and were read as asking
# for a length of time. The length is asked for when the line opens on it ("how long do i boil an
# egg"), which is why only the method's own opening is read here.
METHOD_OPENS = re.compile(r"^how (?:do|does|did) (?:i|we|you)\b", re.I)
# A dimension asked with "how" wants the measurement, and the size word is the ask: "how thick
# should i slice bread" carries a `should i`, which understanding reads as yes/no, and the reply
# that gave the thickness ("About 1cm to 1.5cm for a sandwich") was called a miss. The same is
# true of every size word below, so they are one list and not a line each.
HOW_MEASURE = re.compile(
    r"\bhow (?:tall|old|big|far|heavy|wide|deep|high|fast|hot|cold|warm|hard|loud|cheap|expensive|"
    r"thick|thin|narrow|broad|shallow|steep|fine|coarse|tight|loose|"
    r"many|much|often)\b", re.I)
# The same shape at the head of the ask, over a wider list of measure words. A measure word
# anywhere in the line can be a word inside a method, so the reading that says the figure is the
# answer only takes a line that opens on the measure: "how thick should i slice bread" is 1cm,
# "how ripe should a banana be" is the colour, "how tight should a bike helmet be" is a finger's
# width under the strap. Each of those carries no measure label, only `how`, so `should` in the
# rest of the line was reading the first as a verdict and the other two as a method.
HOW_MEASURE_HEAD = re.compile(
    r"^how (?:tall|old|big|far|heavy|wide|deep|high|fast|hot|cold|warm|hard|loud|cheap|expensive|"
    r"thick|thin|ripe|tight|loose|full|low|slow|quick|short|small|large|near|soft|firm|dark|"
    r"bright|sharp|rough|smooth|fine|coarse|steep|cool|fresh|dry|wet|salty|sweet|spicy|sour|mild|"
    r"strong|weak|light|stiff)\b", re.I)
# "what does a boiler service cost", "what does a cup of honey weigh": a verb of price or measure
# after "what does" asks for the figure, and understanding reads the "what does" as a definition,
# so the figure that came back read as a miss. Same shape as the how-words above.
WHAT_DOES_MEASURE = re.compile(
    r"\bwhat (?:does|do)\b(?:(?!\bwhat\b)[^?]){0,30}?"
    r"\b(?:cost|costs|charge|charges|weigh|weighs)\b"
    # "what does the whole lot come to" is the total; "what does it mean when birds come to my
    # feeder" is the "come to" of a bird, so this arm is only read where no meaning is asked.
    r"|\bwhat (?:does|do)\b(?:(?!\bwhat\b)[^?]){0,30}?\bcome(?:s)? (?:to|out at|out as)\b"
    # A trade is asked what it charges in the same breath, and with a modal in front: "what do
    # plumbers charge", "what would a plumber charge to look at it", "what should a boiler
    # service cost". Understanding writes no price label in either, so the verb is the price.
    r"|\bwhat (?:do|does|would|will|should|can|could|did) .{0,40}?\b(?:charge|charges|cost|"
    r"costs)\b",
    re.I)

# A price asked for without the verb of price: "whats the going rate for a plumber", "what will
# it set me back to have the tree cut", "what should i expect to pay for a new tyre", "what does
# an mot usually run to". Understanding writes no figure for any of them, and the "what should i"
# spelling of the second is read as a method, so the figure is asked for in other words.
PRICE_IDIOM = re.compile(
    r"\bwhat(?:'s|s| is| was)?\s+the (?:going|current|average|typical|usual) rate\b"
    r"|\bset (?:me|us|you) back\b"
    r"|\bexpect(?:ing)? to (?:pay|spend|be paying)\b"
    r"|\b(?:usually|normally|typically|roughly|about) run(?:s)? to\b", re.I)
# "what can i do this saturday that costs nothing" carries the price verb and asks for things to
# do, so the free one is not a figure asked for.
COSTS_NOTHING = re.compile(
    r"\bcosts? (?:nothing|free|nowt)\b|\bfor free\b|\bthat (?:is|are|will be) free\b"
    # "what can i do at home that doesnt cost much" is a what-to-do with a price in it, not a
    # question about a price: the verb there is negated or followed by "much"/"a lot".
    r"|\b(?:doesn'?t|does not|didn'?t|did not|don'?t|do not|won'?t|will not) costs?\b"
    r"|\bcosts? (?:much|a lot|more|less|too much)\b", re.I)
# A conversion, not a duration: "how long is 100m in feet", "how long is a 5k in miles". The
# answer is a length, so "how long" here asks for an amount however the word "long" reads.
CONVERSION = re.compile(
    r"\bhow long (?:is|are|was)\b[^?]{0,30}?\b(?:in|to|as|into) "
    r"(?:feet|foot|metres?|meters?|miles?|kilometres?|kilometers?|km|yards?|inches|inch|cm|mm)\b",
    re.I)
# The same conversion in an oven's own units, and in any unit at all when the person says the
# figure out loud: "whats 180c in gas mark", "what is 200c in fahrenheit", "whats 200 degrees in
# fan", "convert 180c to f", "whats 500ml in pints". The figure is what has to come back, and the
# line asks for a number rather than the meaning of a word or a method.
CONVERTED_FIGURE = re.compile(
    r"\b(?:what(?:'s| is|s)|whats)\s*\d+(?:\.\d+)?\s*"
    r"(?:c|f|degrees?|deg|gas|ml|l|g|kg|oz|lb|lbs|cm|mm|in|inches|pints?|litres?|liters?|"
    r"ft|feet|foot|metres?|meters?|m|miles?|mi|yards?|yd|km|stone|st)\b"
    r"[^?]{0,25}?\b(?:in|to|into|as)\b"
    r"|\bconvert\s+\d+(?:\.\d+)?\s*(?:c|f|degrees?|deg|ml|g|kg|oz|lb|lbs|cm|mm|in)\b"
    r"[^?]{0,20}?\b(?:in|to|into)\b"
    # the thing counted rather than a unit: "whats 2 eggs in grams", "whats 3 cups in ml".
    r"|\bwhat(?:'s| is|s)?\s*\d+(?:\.\d+)?\s+\w+(?:\s+\w+)?\s+(?:in|to)\s+"
    r"(?:grams?|g|kg|ml|millilitres?|milliliters?|litres?|liters?|ounces?|oz|pounds?|lb|cups?|"
    r"tablespoons?|teaspoons?|degrees?|c|f)\b", re.I)
# A when that opens the question. "when i ring someone my screen goes black" is advice about a
# thing that happens, and "my mum keeps asking when were having kids" is a report, not a when.
# A day, a date or a month is a time too: "what day is that", "what date does it start", "which
# day is it". A line that asks which of several days is *best* is a pick, so the choices are left
# to the pick below.
# A follow-up opens on the join: "and what date is that", "so when is it", "but when should i go".
# The question is the same one, and the join in front of it is not part of it.
LEADING_JOIN = re.compile(r"^(?:(?:and|so|but|then|also|ok|okay|right|now|well)\b[ ,]*)+", re.I)
WHEN_ASKS = re.compile(
    r"^(?:when'?s|when|what time|what day|what date|what month|what year|which day|what weekday) "
    r"(?:should|shall|is|are|was|were|will|would|does|do|did|can|could|to|am|has|have|of|had)\b",
    re.I)
# The asks that open on a time, read from the line rather than the reply: "when should i feed the
# tomatoes", "what time does the tip open". A length of time ("how long does rice take") is not one
# of them - the stage a thing has to be at is not an answer to how long.
ASKS_WHEN = re.compile(
    r"^[\W]*(?:and |so |but |then )?(?:when|what time|what day|what date|what month|what year|"
    r"which day)\b", re.I)
WHICH_DAY_IS_BEST = re.compile(r"\b(?:best|better|rather|prefer|do you think|recommend)\b", re.I)
# An open choice: "what should i cook tonight" wants one thing picked, not the method for it.
# A judgement word in front of a measure asks for the figure: "what's a good time for a half
# marathon", "a normal price for a boiler". The noun picks the check.
# A recommendation asked for with the word what: "whats a good podcast for the car", "wats a gud
# cake", "wots a good cheap pressie", "whats a good breakfast thats quick". `GOOD_FIGURE` below is
# the same shape when a figure is wanted: "what is a good half marathon time".
GOOD_THING = re.compile(
    r"\bwhat(?:'s|s| is| are)\s+(?:a|an|the|some)?\s*(?:really |actually |bit of a )?"
    r"(?:good|great|nice|decent|cheap|budget|quick|easy|simple|sensible|healthy)\b", re.I)
GOOD_WAY = re.compile(r"\b(?:way|method|approach|routine)\b", re.I)
# "whats a good resting heart rate" asks for the figure, not a few ideas, so a measure word in the
# line keeps the figure reading `GOOD_FIGURE` gives it.
GOOD_FIGURE_WORD = re.compile(
    r"\b(?:time|timeframe|rate|age|price|cost|number|amount|weight|height|length|salary|wage|"
    r"dose|dosage|percentage|temperature|speed|distance|size|pressure|humidity|mileage|"
    r"voltage|rent)\b", re.I)
# The table a place keeps its hours in is a time, not the meaning of a word: the words after
# "what are" are times or hours and the answer is on the clock.
WHAT_ARE_TIMES = re.compile(
    r"^\W*(?:(?:so|and|ok|okay|oh|also|right)\s+)*what(?:'s| is| are|s)\b[^?]{0,60}?"
    r"\b(?:opening|visiting|closing|trading|check ?in|check ?out|business|office|term|school|"
    r"library|swimming|bus|train|ferry|flight|shop|bank|tip|pool|gym|leisure|surgery|pharmacy|"
    r"restaurant|pub|museum) ?(?:times|hours|dates)\b", re.I)

# "is that a good price", "is that normal for his age", "is this a good time": the judgement word
# is not a figure the person wants read out, it is the verdict they are asking for, and the price
# or the age in the same line is what the verdict is about. Understanding reads the yes/no and the
# figure both, and the figure was winning.
VERDICT_FRAME = re.compile(
    r"^\W*(?:is|was|are|were|does|do|did)\s+(?:that|this|it|these|those|they)\s+"
    r"(?:a|an|the|too|really|actually|still|about|much)?\s*"
    r"(?:good|normal|average|typical|usual|fair|ok|okay|alright|right|fine)\b", re.I)
GOOD_FIGURE = re.compile(
    r"\b(?:good|average|normal|typical|usual|best) (?:\w+ ){0,3}(?:time|age|price|number|amount|"
    r"cost|salary|wage|rate|temperature|weight|height|speed|distance|size|dose|percentage)\b",
    re.I)
# A judgement in front of a measure is an ask for the figure, and both families are wider than
# the list above: "whats a safe temperature for a fridge" was read as the meaning of a word (the
# reply gives 0 to 5C, and `gives` called it a miss), "whats a good temperature for a fridge" as a
# few to choose from, and "whats the ideal weight for a labrador" as a pick. A judgement word is
# any word that ranks or approves - `safe`, `right`, `ideal`, `healthy`, `recommended` - and the
# measure after it is the set `GOOD_FIGURE_WORD` already names, without the words that are a time
# on the clock rather than a figure. So a judgement about a *thing* keeps the names it wants:
# "whats a safe car" and "a healthy breakfast" match neither half of this.
JUDGED_MEASURE = re.compile(
    r"\b(?:good|average|normal|typical|usual|best|safe|right|ideal|healthy|cheap|correct|"
    r"recommended|sensible|maximum|minimum|perfect|decent|acceptable)\s+(?:\w+\s+){0,3}"
    r"(?:rate|age|price|cost|number|amount|weight|height|length|salary|wage|dose|dosage|"
    r"percentage|temperature|speed|distance|size|pressure|humidity|mileage|rent|voltage)\b",
    re.I)
# A judgement about a time stays a time: "a good time to set off", "the best time to visit".
ON_THE_CLOCK = re.compile(r"\b(?:time|times|hour|hours|minute|minutes)\b", re.I)
# A line that opens on an auxiliary is asking yes or no about the measure, not for its figure:
# "is it safe to lose weight quickly" and "is it normal to lose weight" want the verdict, and
# reading them as a figure would throw that away.
ASKS_YES_OR_NO = re.compile(
    r"^\W*(?:is|are|was|were|am|do|does|did|should|shall|can|could|would|will|may|might|"
    r"have|has|had)\b", re.I)
# A judgement about when, not a figure on the clock: "is it a good time to go to dubai", "is
# january a good time to visit", "would it be a good time to plant bulbs now", "is now a good
# time to buy a house". The words "a good ... time" are the same ones a figure is asked with
# (GOOD_FIGURE), and a yes or no answers this one. The verb in front is what tells them apart: a
# figure is asked with a question word ("what is a good half marathon time"), a judgement with
# is/would/could. "is it a bad time to sell" was already read as a yes/no, so the shape of the
# answer depended on good against bad; it no longer does.
A_GOOD_TIME = re.compile(
    r"(?:^|[,;]\s*|\b(?:and|so|but|then|also)\s+)"
    r"(?:is|are|was|were|would|could|will|do you think it is|do you think its)\b[^.?!]{0,60}?"
    r"\b(?:a|an)\s+(?:good|bad|better|best|ok|okay|fine|safe|alright|decent|terrible|awful|busy|"
    r"quiet)\s+time\b", re.I)
# An idiom of greeting, not a duration: "long time no see, how have you been", "hey, long time no
# speak". Understanding reads the "long" as a how-long, and nothing on the clock answers it.
LONG_TIME = re.compile(r"\blong time (?:no (?:see|speak|hear|talk)\b|since\b)", re.I)
# "how does a lock and key work" asks for the mechanism, which is a meaning; understanding reads
# the bare "how" as a method. Only the thing-works form, so nobody doing the working is caught.
HOW_IT_WORKS = re.compile(
    r"\bhow (?:does|do|did) (?:(?!\b(?:i|you|we|im|me)\b)[\w']+ ){1,4}(?:work|works|working)\b",
    re.I)
# A written thing has a length in words or characters, and its "how long" is that length: the noun
# followed by "be" is what tells it from a length of time.
WRITTEN_THING = re.compile(
    r"\bhow long (?:should |would |will |does |do |can )?(?:a|an|my|our|your|the|this|that)\s+"
    r"(?:[a-z]+\s+){0,2}(?:personal statement|statement|essay|dissertation|thesis|coursework|"
    r"assignment|cover(?:ing)? letter|letter|cv|resume|blog post|post|article|abstract|summary|"
    r"report|review|answer|paragraphs?|chapter|book|story|speech|presentation|email|text|message|"
    r"comment|description|bio|application|proposal|synopsis|blurb|poem|script|personal profile|"
    r"profile)\s+be\b", re.I)
# The things whose "how long" is a length in metres, kilometres or miles. The copula is what
# makes it that - "how long is the nile" is 6,650 km - so "how long does a marathon take" and
# "how long to walk the great wall" keep their duration, and the noun has to be the thing being
# measured rather than one named later in the line ("how long can my baby stay in the pool").
THING_THAT_EXTENDS = re.compile(
    r"\bhow long (?:is|are|was|were|will be|would be) "
    r"(?:(?:the|a|an|my|our|your|this|that)\s+)?(?:[a-z'-]+\s+){0,2}?"
    r"(?:rivers?|nile|amazon|thames|severn|danube|rhine|mississippi|walls?|pitch(?:es)?|"
    r"playing fields?|marathons?|bridges?|tunnels?|canals?|motorways?|roads?|runways?|"
    r"coastlines?|coast|borders?|beaches?|whales?|snakes?|crocodiles?|sharks?|string|"
    r"ropes?|hose|cables?|pools?|tracks?|corridors?|driveways?)\b"
    # The thing has to be the whole of what is measured. Another noun after it is a different
    # thing with a duration of its own - a road trip, a river cruise, a beach holiday - so what
    # may follow is the end of the line, its own name ("of china", "of the garden") or a
    # preposition a length is given in ("in miles"). "how long is a whale pregnant" is the same
    # fault: a state after the thing is a stretch of time, not a length.
    r"(?=\s*(?:[.?!,;:]|$|\s+(?:of|in|on|at|from|to|by)\b))"
    r"(?!\s+(?:pregnant|old|big|tall|wide|deep|long|away|till|until|now)\b)", re.I)
# The person has to do the explaining, saying or answering: that is a method, not a meaning.
HOW_TO_DO = re.compile(
    r"\bhow (?:do|can|could|should|would|will) (?:i|we|you) (?:explain|answer|say|tell|word|"
    r"respond|reply|put it|break it|approach|handle)\b|\bhow to (?:explain|answer|say|tell|"
    r"word|respond|reply|approach|handle)\b", re.I)
# Small talk shaped like a how: it asks nothing of the world.
# "hows things" and "hows u" are the same hello as "how are you", and were read as a method and
# scored a steps miss. A noun that a verb follows is not small talk: "how things work" asks for the
# meaning and keeps its shape.
HOW_ARE_YOU = re.compile(
    r"^(?:(?:hey|hi|hiya|heya|hello|yo)(?: there)?[ ,]+)?how(?:'?s| is| are)?[ ,]+"
    r"(?:you|u|ya|things|tricks|life|are you|are things|is it going|s it going|have you been|"
    r"are we|your (?:day|week|evening|morning|night|head|family))\b"
    r"(?!\s+(?:work|works|worked|working|go|goes|went|change|changes|changed|happen|happens|"
    r"happened|fit|fits|seem|seems)\b)",
    re.I)
# "right ill let you know how it goes", "how did it go", "how was it", "how did the interview
# go": the how is asking how something turned out, and understanding labels every how a method. The
# person wants the bot to hear the result and say something about it, so no figure, no steps and no
# meaning is owed - the reply that came back was a paragraph on how long a boiler lasts, because
# the shape asked for a method sent the composer to the card's own figures. Only the short report
# forms, and only at the end of the line, so "how did it happen" (a reason) and "how was it made"
# (a method) keep their own readings.
HOW_IT_WENT = re.compile(
    r"\bhow\s+(?:did|does|was|were|is|are|'s)\s+"
    r"(?:(?!\b(?:i|you|we|me|us)\b)\w+\s+){0,4}"
    r"(?:go|goes|went|get on|got on|getting on|get along|turn out|turned out|work out|"
    r"worked out)\b(?!\s+\w)"
    r"|\bhow (?:it|that|this|things|everything) (?:goes|went|go|turns out|turned out)\b"
    r"(?!\s+\w)"
    r"|\bhow (?:was|were) (?:it|that|this|things|everything)\b(?!\s+\w)"
    r"|\bhow goes it\b",
    re.I)
# The same report shape asking for the cause instead: "how did it happen", "how did that come
# about". A reason is the answer, and the "how" was read as a method before.
HOW_IT_HAPPENED = re.compile(
    r"\bhow\s+(?:did|does|do)\s+(?:it|that|this)\s+(?:happen|happens|happened|come about|"
    r"came about)\b", re.I)
# A line that opens on a question word or an auxiliary is asking, whatever punctuation it has.
ASKS_OUT_LOUD = re.compile(
    r"^(?:what|which|who|whose|when|where|why|how|is|are|was|were|do|does|did|can|could|should|"
    r"shall|would|will|any|anything|anyone|recommend|suggest|name|give me|tell me|got any)\b",
    re.I)
# A line that asks what a thing costs wants the figure, though understanding reads its "what
# does" as a definition and "price of a pint" as one more thing to define. A standing charge is
# not a cost question, so the price word here is one a thing is measured by, or the verb itself.
COST_ASK = re.compile(
    r"\bwhat (?:does|do|will|would|did|is it going to) .{0,40}\bcosts?\b"
    r"|\bwhat .{0,40}\bcosts?\b"
    r"|\b(?:price|cost|charge|fee)s? (?:of|for)\b", re.I)
# A price asked as a definition: "what is a gym membership a month" and "whats a cleaner an hour"
# are the figure, and a card that explains what a membership is does not answer either.
WHAT_IS_PER = re.compile(
    r"\bwhat(?:'s|s| is)\b[^?]{0,40}\b(?:a|an|per|each|every) "
    r"(?:month|week|year|day|hour|litre|liter|kg|kilo|pint|mile|gb|gigabyte|night|visit|session|"
    r"person|head|class|lesson)\b", re.I)
# The asks a cost line may carry and still be asking the price: a `why` or a `where` in the line
# keeps its own shape, so this is a subset of every other ask, not a list of them.
COST_STANDS_IN = frozenset(("what", "definition", "list", "opinion", "recommend", "question"))
# "what should i be paying", "what should we spend on a holiday", "what should i be earning": the
# ask is a figure. The engine reads a bare "what should i ..." as `steps` whatever verb follows, so
# a price question came through as a method and the reply that answered it was a how-to. The money
# verb is the ask, and what it spends the money on has to be a thing rather than money already
# there - see `MONEY_VERB_NOT_A_PRICE`, which wants a pick or something else instead.
A_FIGURE_OF_A_MONEY_VERB = re.compile(
    r"\bwhat\s+(?:should|shall|do|does|would|can|could|will)\s+(?:i|we|you|they|he|she)\s+"
    r"(?:be\s+)?(?:pay|paying|spend|spending|earn|earning|budget)\b(?!\s+off\b)", re.I)
# What the money verb is said of that is not a price: money already there being divided up
# ("what should i spend it on first", "what should i pay off first") orders things and wants a
# pick, a verb that is not about money at all ("pay attention to", "spend time on", "spend my
# evening doing") wants whatever that asks for, and neither is a figure.
MONEY_VERB_NOT_A_PRICE = re.compile(
    r"\bpay(?:ing)?\s+attention\b"
    r"|\b(?:pay|paying|spend|spending)\s+(?:it|them|this|that|the\s+money|the\s+rest|"
    r"the\s+lot)\b"
    r"|\b(?:pay|paying)\s+off\b"
    r"|\bspend(?:ing)?\s+(?:(?:my|our|your|the)\s+)?(?:time|attention|effort|trouble|energy|"
    r"evening|day|weekend|morning|afternoon|night|holiday|summer|hours|years|life)\b", re.I)
# A sum asked with no question word at all: "subtract 10 percent from 55", "split 120 between 4
# people", "half a cup of rice in grams". Understanding labels the number `maths` and the line is
# a statement, so the figure is the ask even though the line never asks one out loud.
SUM_OUT_LOUD = re.compile(
    r"^(?:subtract|add|multiply|divide|solve|factorise|factorize|work out|convert|split|minus|"
    r"plus|double|halve|times)\b|\bhow much is\b", re.I)
SUM_ASKS = re.compile(
    r"\b(?:\d+|half|quarter|third|two thirds|three quarters|a few)\b.{0,30}\bin "
    r"(?:grams?|gms?|kg|kilos?|kilograms?|ml|millilitres?|litres?|liters?|cups?|ounces?|oz|"
    r"pounds?|lbs?|tablespoons?|tbsp|teaspoons?|tsp|pints?|centimetres?|cm|inches|feet|metres?)\b"
    r"|\b(?:half|a quarter|a third|two thirds|three quarters|three quarters|a fifth) of \d+"
    r"|\bas a percentage\b|\bpercent (?:off|on top)\b|\b\d+\s*(?:%|percent)\b"
    r".{0,25}\b(?:off|tip|on top|between|split)\b"
    r"|\bsplit (?:the )?(?:bill|cost|rent|fare|total|it|\d|\u00a3)", re.I)
# ... unless the figure words are about the bot itself, or the person is really asking whether the
# thing matters. "how much do you know about boilers" and "how much does it matter" want no
# figure. A "do you" alone is not about the bot: "how much do you feed a pig" and "how much do you
# tip a waiter" ask for a figure, so the verb of knowing is what makes the line the bot's own. This
# sits in front of every amount reading below, not only the how-much one, because the label table
# at the bottom maps the same how_much label to a figure.
NOT_A_FIGURE = re.compile(
    r"\bhow (?:much|many) (?:do|did|can|could|would|have) you "
    r"(?:know|remember|understand|recall)\b|"
    r"\bhow (?:much|often) (?:does|do) (?:it|that|this|they) matter\b|"
    r"\bhow much (?:should|do) (?:i|we) (?:worry|care|mind)\b", re.I)
# The two "else" asks. With a thing named after a "with", the person has something to use up and
# wants a few more ideas for it: "what else can i do with leftover rice", "what else should i do
# with a glut of courgettes". Without one, they want one more step out of the answer they were
# just given: "what else can i do", "what else can i try", "ok what else could i do" - the same
# shape as the steps they asked for before. Both were read as asking for nothing at all.
WHAT_ELSE_WITH = re.compile(
    r"\bwhat else (?:can|could|should|shall|do|would) (?:i|we|you)\b[^.!?]{0,25}?\bwith\b", re.I)
WHAT_ELSE_STEPS = re.compile(
    r"\bwhat else (?:can|could|should|shall|do|would) (?:i|we|you) (?:do|try)\b", re.I)
PICK_ONE = re.compile(
    r"\bwhat (?:do|should|shall|can|could) (?:i|we|he|she|they) (?:cook|make|eat|have|drink|watch|"
    r"read|listen to|wear|get|buy|order|play|study|plant|visit|do with|give|bring)\b"
    r"|\bwhat (?:do|should|shall|can|could) (?:my|our|his|her|their) \w+ (?:cook|make|eat|have|"
    r"drink|watch|read|wear|get|buy|order|play|study|plant|visit|give|bring)\b", re.I)
# A thing held up against another asks for a few things to go with it, and no reading below names
# that shape: "what goes with lamb", "what wine with a curry", "what food for a bbq", "what should
# we name the baby" all left `wants` None, so the good replies already given on those turns could
# not be checked at all. A sauce that *goes in* a dish is the recipe, so "what goes in" is not read
# here, and a line reported to the bot ("they said what goes with it") owes no shape of its own.
PAIRING_ASK = re.compile(
    r"\bwhat (?:[\w'-]+ )?go(?:es)? (?:with|alongside|nicely with)\b"
    r"|\bwhat (?:[\w'-]+ )?(?:wine|beer|drink|drinks|food|music|songs?|salad|sides?|dessert|"
    r"cheese|bread|pudding|starter|sauce|film|book|present|gift)s? (?:for|with)\b"
    # "call" is the phone as often as a name, so the thing being named has to be named: "what
    # should i call them" is what to say to them, and "what should i call the landlord about" is
    # the same ask. The rest of the line decides, so the naming ask is the one with neither of
    # those after it - a determiner and a thing, and none of the words that open the other ask.
    r"|\bwhat should (?:i|we) name\b"
    r"|\bwhat should (?:i|we) call (?:my|our|the|his|her|their)\b"
    r"(?![^\n]*?\b(?:about|for|to|if|when)\b)", re.I)
# The same ask with a kind of thing named in front of the verb: "what knife should i buy", "what
# book should i read", "what kind of plant should i get". A want of None means nothing is checked
# at all, so the good picks on these turns passed unseen and the punts did too. The verb still
# decides, and the noun has to be a thing to choose from: a measure ("what time should i get up"),
# an entitlement or a record ("what age do i get my state pension", "what pets do i have") and
# "what else" keep their own reading. A preposition after the "what" opens a different ask - "what
# about flights, should i book early" is a yes/no about the flights - so it is not read here.
# The verb is not what makes it a pick, and a list of verbs missing "use", "do", "paint" or
# "learn" left the same ask reading None: "what shampoo should i use", "what pudding shall i make",
# "what paint should i use on the fence", "what scales should i learn on guitar". Any verb after the
# thing leaves the thing as what is being chosen, so the noun decides and the verb is read as a word.
# A quantity or a record in front of the verb is the ask instead, which is what the guard names -
# "what time should i get up", "what spf should i use", "what budget should i set", "what pets do i
# have". "shall" is the same ask as "should" and was left out of both.
PICK_ONE_OF_A_KIND = re.compile(
    r"\bwhat (?!else\b|about\b|of\b|in\b|on\b|at\b|to\b|from\b|for\b|with\b|by\b|between\b|"
    r"age\b|time\b|date\b|month\b|year\b|day\b|size\b|temp\b|temperature\b|price\b|cost\b|"
    r"amount\b|number\b|help\b|support\b|percentage\b|share\b|"
    r"spf\b|budget\b|salary\b|wage\b|dose\b|dosage\b|calorie\w*\b|weight\b|length\b|height\b|"
    r"depth\b|speed\b|rate\b|fee\b|charge\b|rent\b|tip\b|discount\b|voltage\b|wattage\b|"
    r"qualifications?\b|pets?\b|rights?\b|entitlements?\b|apr\b|interest\b|deposit\b|"
    r"savings?\b)"
    r"(?:(?:kind|sort|type|brand|make) of (?!price\b|cost\b|amount\b|salary\b|budget\b|"
    r"time\b|size\b|weight\b))?"
    r"(?:[\w'-]+ ){1,2}(?:should|shall) (?:i|we) "
    r"[a-z]+\b", re.I)
# A price is also asked as an adjective on the thing: "is paris expensive", "is a plumber costly",
# "will that be expensive to fix" are questions about how much, and the answer a person gets is a
# range. Only the words that mean a lot of money count: "cheap" and "cheaper" compare two things
# and a `than` names them, so those keep their pick.
PRICE_ADJECTIVE = re.compile(
    r"\b(?:is|are|was|were|isn'?t|aren'?t|wasn'?t|weren'?t)\b[^?.!]{0,30}?\b(?:expensive|"
    r"costly|pricey)\b"
    r"|\b(?:will|would|won'?t|wouldn'?t)\b[^?.!]{0,24}?\bbe\b[^?.!]{0,14}?\b(?:expensive|"
    r"costly|pricey)\b", re.I)
# A comparison of two named things is a pick, and a verdict on the value of something is a yes/no:
# "is a cheap mattress worth it" asks whether to buy it, not what it costs.
PRICE_ADJECTIVE_KEEPS = re.compile(
    r"\b(?:than|or|instead|versus|vs|worth|whether|rather)\b", re.I)
# ...and the price word is not the ask when the line asks something else after it: "sky tv is too
# expensive can i cancel" is a remark about their bill and a question about cancelling, and the
# reply people get is the steps for cancelling. A question word with a person after it is another
# question, and the price in front of it is what that question is about.
PRICE_ADJECTIVE_THE_ASK_IS_LATER = re.compile(
    r"\b(?:expensive|costly|pricey)\b[^?.!]{0,30}?\b(?:can|could|should|shall|would|will|do|does|"
    r"did|am|is|are)\s+(?:i|we|you|he|she|they|it)\b", re.I)
# ...and a "why" about the price keeps its reason: "why is everything so expensive", "why is london
# so expensive" want the cause, and the price word in them is what the why is about. Understanding
# labels them `why` plus `yesno` (the line opens on an auxiliary), which is what put them at risk.
PRICE_ADJECTIVE_WHY = frozenset(("why",))
# A line that asks the bot outright what to do about something: "what can i do 4 a sore throat",
# "my baby is constipated, what can i do", "what do i say to my boss", "what do i try first".
# Understanding labels the `what should i do` spelling as steps and leaves the rest of the family
# as a bare `what`, so the whole line is read here and the verb decides: doing, saying, taking or
# trying wants the steps. Something to wear or get is a choice, and `PICK_ONE` above has it, so
# those verbs are not here; `use` is read as `SUBSTITUTE` below instead.
WHAT_TO_DO = re.compile(
    r"\bwhat (?:do|should|shall|can|could|would) (?:i|we) "
    r"(?:do|say|take|try|check|avoid|ask|tell|help|start|stop|keep)\b", re.I)
# The same ask said to the bot rather than about the person: "what do you do about that" is the
# method, and "what would you take to a new baby" is the list of things. The verb tells them apart,
# and the job question ("what do you do for a living") is still about the person, not a method.
WHAT_YOU_DO = re.compile(
    r"\bwhat (?:do|does|would|should|can|could) (?:you|one) (?:do|try)\s+"
    r"(?:about|with|if|when|for|to)\b", re.I)
# The same ask in the person's own voice - "what can i take to a bbq", "what should i bring to an
# interview", "what can i take camping" - is the same list of things. It read `steps` off the verb
# "take" (which is on the what-to-do list) or `pick` off "bring", and a packing list is neither: it
# is the few things to put in the bag, so the second-person and the first-person spellings share
# one reading. A pair is still a pick, and "what should i take for a headache" keeps its stand-down.
WHAT_YOU_TAKE = re.compile(
    r"\bwhat (?:do|does|would|should|can|could|shall) (?:you|one) "
    r"(?:take|bring|pack|give|get|need|buy)\b"
    r"(?! (?:for|to do|to get|to make)\b)"
    # In the person's own voice only the packing verbs: "what should i get my mum" is a pick of
    # one present, where "what should i take to a bbq" is the few things to bring.
    r"|\bwhat (?:do|does|would|should|can|could|shall) (?:i|we) (?:take|bring|pack)\b"
    r"(?! (?:for|to do|to get|to make)\b)", re.I)
# The same ask said from the other side: "what do i need for a camping trip", "what do i need to
# buy for a roast", "what will we need for the baby". It is the list of things the person asked
# for - the shape "what would you take to a new baby" already had - and on its own words it read
# as no ask at all, which was eighty of the deck's lines. The infinitive after the need decides
# which ask it is: what to buy, get, bring, pack or order is the list of things, and what to do,
# know, say or watch out for about the situation is the method, which is read further down.
WHAT_I_NEED = re.compile(
    r"\bwhat (?:do|does|will|would|should|shall|might|can) (?:i|we) "
    r"(?:actually |really |even |truly |possibly |then |now )*(?:need|require)\b"
    r"(?!\s+(?:to\s+)?(?:do|know|say|ask|tell|learn|understand|work|watch|avoid|stop|prevent|"
    r"fix|deal|look|sort|handle|word|phrase)\b)", re.I)
# The infinitive the list above leaves out: "what do i need to do first", "what do i need to know
# before i go", "what will i need to say". The need with a doing verb after it is the method, not
# the list of things, and nothing else reads it: the `what ... need` row stands down on the
# infinitive and the `what do i do` row needs the doing verb straight after the person, so these
# lines came out with no shape at all and any reply at all was as good as any other.
NEED_TO_DO = re.compile(
    r"\bwhat (?:do|does|will|would|should|shall|might|can) (?:i|we) (?:need|require) to\s+"
    r"(?:do|know|say|ask|tell|learn|understand|work|watch|avoid|stop|prevent|fix|deal|look|"
    r"sort|handle|prepare|plan)\b", re.I)
# A figure has a unit named in the question: "what temperature should i cook chicken at", "what
# gas mark for a sponge", "what setting on the oven". Understanding reads the `what` as a
# definition, so the noun is what says a figure is owed.
WHAT_FIGURE = re.compile(
    r"\bwhat (?:temperature|temp|heat|gas mark|setting|speed|depth|size|weight|voltage)\b",
    re.I)
# "what age" is the figure question for a number of years: "my kid wants a phone, what age", "at
# what age do kids stop napping", "what age can a child stay home alone". It is not in the list
# above because the unit is not the word after the `what`: the age is the thing asked about.
WHAT_AGE = re.compile(r"\bwhat age\b", re.I)
# The same choice said as a fragment at the end of a line, with no auxiliary at all: "first day at
# the office, only jeans, what trousers", "smart dinner with the inlaws, what shoes". A bare
# "what <plural noun>" is a thing to pick from; the questions people also type that way - "what
# else", "what next", "what size", "what happens if i leave it" - are excluded by name.
WHAT_THING_FRAGMENT = re.compile(
    r"(?:^|[,;]\s*)what (?!about\b|is\b|are\b|was\b|were\b|if\b|else\b|next\b|now\b|"
    r"size\b|time\b|colour\b|color\b|kind\b|sort\b|type\b|age\b|happens\b|went\b|works\b)"
    r"([a-z]{3,}s)\b\s*[.!?]*\s*$", re.I)
# A remedy asked for with "what helps" is a few things to try, not one method: "what helps a sore
# throat", "what can help with cramps".
WHAT_HELPS = re.compile(
    r"\bwhat (?:helps|can help|might help|will help|would help|works)\b", re.I)
# The infinitive of the same two asks: "what to wear to a wedding", "what to cook tonight", "what
# to do when your boiler leaks". It is how people type the `what should i` family without the
# auxiliary, and on its own the reading found no shape at all, so "what to cook tonight" owed
# nothing while "what should i cook tonight" wanted a pick - one question, two answers. The verb
# decides, as it does above. A line that only reports knowing ("i know what to wear to a wedding")
# asks nothing, so the ask has to open the line or follow a doubt; "i dont know what to cook" is
# that doubt and is still an ask.
# A "what can i bake" ask is answered by a few things to choose from as often as by one thing, so
# the bake is read as a menu rather than a pick: see the arm in `_wants_alone`.
WHAT_TO_BAKE = re.compile(
    r"\bwhat (?:do|should|shall|can|could) (?:i|we|he|she|they) (?:bake|roast)\b"
    r"|\bwhat (?:do|should|shall|can|could) (?:my|our|his|her|their) \w+ (?:bake|roast)\b"
    r"|\bwhat to (?:bake|roast)\b", re.I)
WHAT_TO_OPENS = re.compile(
    r"^(?:so |and |ok |okay |now |also |please |but )?what to\b"
    r"|\b(?:i (?:don'?t|do not) know|not sure|no idea|dunno) what to\b", re.I)
WHAT_TO_PICK = re.compile(
    r"\bwhat to (?:cook|make|eat|have|drink|watch|read|listen to|wear|get|buy|order|play|study|"
    r"plant|visit|give|bring|pack)\b", re.I)
WHAT_TO_STEPS = re.compile(
    r"\bwhat to (?:do|say|write|text|reply|feed|serve|take|try|check|avoid|ask|tell|keep)\b",
    re.I)
# "what do i write in a card", "what should i say when she asks": the ask `WHAT_TO_STEPS` and
# `WHAT_TO_PICK` already read, said with the auxiliary instead of "what to". Both lists ask for a
# `what to <verb>`, so the everyday spelling of the same question read nothing at all and the
# reply was graded a miss for a shape nobody had named. Only the verbs that are asked for by
# name are read this way: "what did i do today" is a recall and "what can i use on a burn" is
# the substitutes, and neither is an ask about a method.
WHAT_I_WRITE = re.compile(
    r"\bwhat (?:do|should|shall|can|could|would) (?:i|we) "
    r"(?:write|say|text|reply|word|phrase|sign)\b", re.I)
# The same for the things that are grown or baked, which are answered by a few to choose from:
# "what can i sow next month", "what should i bake for a birthday" is a menu, not one thing.
# "what should i pack" and "what can i feed a kitten" are left alone: the bot already reads them,
# and the menu check does not credit the bare list it gives ("Passport, the boarding pass on the
# phone and a screenshot of it") where the method check did, so moving them cost 3 replies.
WHAT_I_GROW = re.compile(
    r"\bwhat (?:do|should|shall|can|could|would) (?:i|we) "
    r"(?:grow|sow|plant|batch|bake|roast)\b", re.I)
# Somebody else's question, told to the bot, is a report and not a question of the bot's own:
# "my brother asked me what to do", "she wants to know what she should take".
# A reported question puts its what-clause straight after the asking: "my brother asked me what to
# do", "mum told me what to wear". When other business comes first the what-clause is the person's
# own question: "my friend told me she has breast cancer what do i say" and "theyve asked me to
# come in for a meeting, what do i say" ask the bot for the words, and reading them as a report
# left the commonest way of asking what to say with no shape at all.
REPORTED = re.compile(
    r"\b(?:she|he|they|mum|dad|mom|someone|somebody|my \w+)\b.{0,25}"
    r"\b(?:asked|told|wonder\w*|wants to know|keeps asking)\b\s*"
    r"(?:(?:me|us|him|her|them|that|about|to)\s*){0,2}(?:what|whether|if)\b", re.I)
# What to use in place of a thing the person has not got wants the substitutes, not a method:
# "what can i use instead of mince", "no yoghurt what can i use". What it is used *on* is
# another matter - "what can i use on a burn" - and is left alone rather than guessed at.
SUBSTITUTE = re.compile(
    r"\bwhat (?:do|should|shall|can|could) (?:i|we) use\b(?! (?:for|on|to)\b)"
    # "what can i use instead" is the substitutes; "what should i do instead" is the other method,
    # so `do` is not one of the verbs here.
    r"|\bwhat (?:else )?(?:do|should|shall|can|could) (?:i|we) (?:use|try|have|make)\b"
    r".{0,25}\binstead\b", re.I)
# An ask for what was already said. The first words of it are a yes/no's grammar - "can you
# remind me", "could you say what i asked" - so the engine writes `yesno` beside the recall, and a
# reminder of the person's own line came out as a reply that never said yes or no. The thing asked
# for is in the store, so the shape is the recall and not a verdict. "remind me how to boil an egg"
# and "remind me what to do" are the method asked for again, so a wh-word right before "to" is not
# a recall.
A_RECALL_ASK = re.compile(
    r"\bremind me (?:of |about |that |if |whether )"
    r"|\bremind me (?:what|when|where|who|which|how) (?!to\b)"
    r"|\bwhat (?:did|have) (?:i|we) (?:say|said|ask|asked|tell|told|mention|mentioned)\b"
    r"|\bwhat (?:was|were) (?:my|our) (?:first|last|earlier|original)\b"
    r"|\b(?:what|which) (?:was|is) the (?:first|last) (?:thing|line|question|message) i\b", re.I)
# "what do i have" asks for the list the person already gave, not for a thing to cook or eat;
# "what do i have for dinner" names the thing and is still a choice.
HAVE_RECALL = re.compile(r"^\W*what (?:do|did) i have\b"
                         r"(?! (?:for|on|in the|tonight|to eat|to wear|to drink))", re.I)
# "what do i do for a living" asks about the person's own job, not for a method of doing one.
NOT_STEPS = re.compile(r"\bwhat (?:do|does|did) (?:i|you|we|he|she|they) do for (?:a )?living\b|"
                       r"\bwhat (?:do|does|did) (?:i|you|he|she|they) do for work\b", re.I)
# A line that opens on another question word is that question first, whatever a later clause asks:
# "where do i register my mums death and what do i take" wants the place.
# A negative auxiliary is not a question opener: "cant get to sleep what can i do" and "didnt
# have time to cook dinner what can i do" are the person's own problem and then the ask, and
# understanding writes the contracted form out as two words, so this read them as a question
# about whether and gave the real ask no shape at all.
OTHER_QUESTION = re.compile(r"^\W*(?:where|when|who|whose|which|why|how|is|are|was|were|can|could|"
                            r"should|shall|would|will|does|did)\b(?!\s+not\b)", re.I)
# Understanding reads the "should i" or the "do i" of a measure question as a yes/no as well, so
# "how long should i boil an egg" carries both `how_long` and `yesno`. The measure is the question:
# a yes or a no is the wrong answer to every one of them, and the figure is the answer.
# "i need to register the death": a task the person has to do, asked as a statement, and the
# object is what makes it a task. "i need to get some sleep" is a need, not a task, and reading it
# as one named a miss on the good sleep answer it already got (salmon-llama on #13102). So the
# verbs that carry no task on their own - get, find, move, do, work, set, change: "get organised",
# "do more", "move house" - are read only when the thing after them is named with a determiner or
# a pronoun ("get him tested", "do the forms"), and the verbs that are a job of work are read with
# any object at all ("register the death", "ring the council", "sort out her pension").
NEED_TO = re.compile(
    r"\bi (?:need|have|'ve|have got|got|'ll need|will need) to (?:"
    r"(?:sort|register|ring|call|fill|send|tell|book|apply|arrange|cancel|close|write|deal)\b"
    r"(?:\s+(?:out|up|off|in|on|with|for|about))?\s+[\w'-]+"
    r"|(?:get|find|move|do|work|set|change)\b"
    r"(?:\s+(?:out|up|off|in|to|with|for|about))?\s+"
    r"(?:the|my|his|her|their|our|a|an|this|that|these|those|it|them|him|us|me)\b"
    r")", re.I)
# The same words as a question are a question, and the question has its own shape: "do i need to
# book the pitch before we go" is a yes or a no, and reading its task made it steps, which put a
# passport card in front of somebody packing a tent (a deck chat, `lr-camping-two-kids-01`).
# "what do i need to take" is the list of things, and `WHAT_I_NEED` above is its row.
NEED_TO_ASKED = re.compile(
    r"\b(?:do|does|did|will|would|should|shall|can|could|might|may|must|have)\s+(?:i|we)\s+"
    r"(?:need|have|got|'ve)\s+to\b"
    r"|\b(?:what|which|how|when|where|who|why)\s+(?:\w+\s+)?(?:do|does|did|will|would|should|"
    r"shall|can|could)\s+(?:i|we)\s+(?:need|have|got|'ve)\s+to\b", re.I)
MEASURE_LABELS = frozenset(("how_long", "how_much", "how_often"))
# A line can carry its context and its question in one breath, with no comma between them: "my dad
# died last week how long does probate take", "my boiler is 12 years old what should i replace it
# with". The engine reads the whole line as the news it opens on, every measure reading below is
# skipped, and the line is left owing no shape at all - so the bot answers the news and the
# question goes unanswered. That is the operator's own report (#126866): a line that gives the
# context and then asks, and the context is what gets answered. A question word with an auxiliary
# verb straight after it is that question clause. Only the order of the words tells it apart from
# the same words inside a clause nobody is asking: "i didnt know how long it would take" and "its
# amazing how much room there is" put a noun or a pronoun in between, and neither asks anything.
QUESTION_IN_THE_LINE = re.compile(
    r"\b(?:what|which|where|when|who|whom|whose|why|how)"
    r"\s+(?:do|does|did|should|shall|can|could|will|would|must|is|are|am)\b"
    r"|\bhow (?:long|often|many|much)\s+(?:do|does|did|should|shall|can|could|will|would|must)\b",
    re.I)
# "where do i start" names no place: it is the same ask as "what do i do first", and understanding
# reads its "where" as one. The answer owed is the steps.
WHERE_START = re.compile(
    r"\bwhere (?:do|does|should|shall|can|could|would|will|to) (?:\w+ ){0,3}(?:start|begin)\b"
    r"|\bwhere to (?:begin|start)\b", re.I)
# A thing's origin is not a place: "where does honey come from" is answered by the bees and the
# nectar, "where does paper come from" by wood and pulp - an explanation, not a town. Understanding
# reads the "where" as a place, so the good reply that explains the thing read as a miss for naming
# no place. A person's origin is still a place ("where do you come from", "where does she come
# from"), so only a thing's is read this way.
ORIGIN_ASK = re.compile(r"\bwhere (?:does|do|did) (?:\w+ ){0,3}(?:come from|grow)\b", re.I)
# "what is glass made of", "what are sausages made from": the making of the thing, which is the
# same answer an origin question wants and no `definition` label carries.
MADE_OF = re.compile(r"\bwhat (?:is|are) (?:\w+ ){0,3}made (?:of|from|out of)\b", re.I)
ORIGIN_PERSON = re.compile(r"\bwhere (?:does|do|did) (?:you|they|we|i|he|she|u)\b", re.I)
# A line that asks its own yes or no about the thing it names is a verdict, whatever else its words
# look like: "whats the point of leaving the heating on, does it save money" wants yes or no, not
# the reason the heating is worth having. The whole line decides, not the "point".
ASKS_ITS_OWN_YES_NO = re.compile(
    r"\b(?:does|do|will|would|can|could|should|did|is|are|was|were) "
    r"(?:it|that|this|they|these|those)\b", re.I)
# "where's the point of any of it", "wheres the point in carrying on": despair, not a place.
# Understanding reads the "where" and the safety answer to it read as a miss for naming no place.
WHERE_POINT = re.compile(
    r"\bwhere(?:'s|s| is| was)\b[^?]{0,20}\b(?:the|any) point\b", re.I)
# A person's own whereabouts is a question for memory, not a place the world keeps. "where does she
# live", "where am i", "where was i going", "where's my phone" are answered from what the person
# has said - or honestly, "you haven't mentioned a place yet" - and no place named is not a miss.
WHERE_RECALL = re.compile(
    r"\bwhere (?:am|was) i\b|\bwhere (?:were|are) we\b|\bwhere we (?:left|were|are)\b"
    r"|\bremind me where\b"
    # A knowledge verb and a first person is the person asking the bot to recall their own facts:
    # "do you know where i live", "forgot where i put my keys". A report about somebody else is not
    # this: "my nan had a fall and doesnt know where she is" is a place ask, and the fall card
    # answers it - reading the "knows where she is" as a recall made a right answer a miss. So the
    # other person keeps only the words about where they live.
    r"|\b(?:know|knows|known|tell me|told me|remind|remember|forgot|forget|said)\b[^?]{0,25}\b"
    r"where (?:i|we|you) (?:live|work|are|were|went|put)\b"
    r"|\b(?:know|knows|known|tell me|told me|remind|remember|forgot|forget|said)\b[^?]{0,25}\b"
    r"where (?:he|she|they) (?:live|lives|work|works|stay|stays)\b"
    # One person's street is not a place the world keeps either: "where does john live", "where
    # does she work". The reply "you haven't said" is the answer, and no place named is right.
    # The subject has to be a person, though: a kind of thing with an article is a habitat and a
    # real place question - "where do penguins live" is answered by the penguins card, and reading
    # it as a recall of a fact the bot was never told made that right answer a miss.
    r"|\bwhere (?:does|did) (?!a |an |the )[a-z]{2,}(?: [a-z]{2,})? (?:live|work|stay)\b"
    r"|\bwhere (?:do|does|did) (?:i|you|he|she|we|they) (?:live|work|stay)\b"
    r"|\bwhere (?:do|does|did) (?:my|our|your|his|her|their) \w+(?: \w+)? (?:live|work|stay)\b"
    r"|\bwhere (?:do|does|did) i (?:decide|say|tell|mean|think|go\b[^?]{0,12}\b(?:last|before))"
    # Where the conversation was, not where a thing in the world is: "where did we leave off",
    # "where did we get to". The reply "we're at the beginning" is right and names no place. Only
    # the first person plural: "where do i leave the recycling" is a place ask and stays one.
    r"|\bwhere did we (?:leave off|left off|leave it|left it|get to|got to)\b"
    r"|\bwhere (?:did|do) we (?:get up to|got up to)\b"
    # Where a thing comes from is the fact about the world that `ORIGIN_ASK` reads lower down, not
    # a recall of what the person told the bot: "where does honey come from" wants the bees and the
    # nectar, and this arm answered it with nothing at all. A person's own origin keeps its place
    # reading through the arms above, which name the person.
    r"|\bwhere(?:'s|s| is| are| did i put| have i put| can i find)\b[^?]{0,20}\b"
    r"(?:my|me|our|the)\s+(?:phone|keys|key|wallet|purse|glasses|bag|bags|parcel|nappy|nappies|"
    r"coat|remote|passport|documents|bus pass|ticket|tickets)\b", re.I)
# The same readings for a line that is only that and nothing else: "where i live" alone asks the
# bot to recall it, while "what do i do about a flood warning where i live" is a method. `_said`
# joins every reading the engine kept, so the line sits in it several times and no anchor holds;
# these read the plain line instead.
WHERE_ALONE = re.compile(
    r"^(?:and |so |ok |okay )?where(?:'s|s| is| are) (?:it|that|this)$"
    r"|^(?:and |so |ok |okay )?where (?:i|we|you) (?:live|work)$"
    r"|^where (?:do|does|did) i (?:live|work)$", re.I)


def _whole(understood):
    """The line as the person typed it, for the few readings that need the whole of its shape."""
    for key in ("plain", "text"):
        value = understood.get(key)
        if isinstance(value, str) and value.strip():
            return " ".join(value.lower().replace("\u2019", "'").split())
    return ""

# A where that asks for a suggestion - "where should we eat", "where should we go in october" - is
# still a place ask, and it was tempting to let it go: a few ideas are one way to answer it. They
# are not. Over the 55 such lines in the deck, 47 replies name a place and are right, and the 8 that
# name none are all the same reply, "Decide in this order ... then pick a place whose menu is short"
# - the way to choose instead of anywhere to choose. That is the miss this lane exists to count, so
# the suggestion keeps its place reading and the answers lane has a named target.
# "how do i answer where do you see yourself in five years" is a request for the way to say
# something, and the "where" inside it is the question being quoted.
# ... and the same ask said of somebody else's question: what to say back. Only the first person
# answering ("how do i answer why i left") and the asked-of-you form ("what do you say when they
# ask ..."), because "what would you say to him" and "what do you say about the chewing" are the
# person's own advice to give, not a question to be answered.
HOW_TO_ANSWER = re.compile(
    r"\b(?:how|what) (?:do|should|can|could|would) i (?:answer|reply to|explain|word|phrase)\b"
    r"|\b(?:what|how) (?:do|should|would) you say when they ask\b", re.I)
# A who that shares its line with a measure is not the ask: "who pays what when one earns more"
# wants the rule for the split, and the good reply that gives the rule read as a miss for naming
# no person. A who on its own ("who do i ring about a council tax refund") still owes a name.
WHO_AND_MEASURE = re.compile(r"\bwho\b[^?]{0,40}\b(?:what|how much|how many)\b", re.I)
# A `who` that belongs to a noun is not a who-question: "should i chip in for a present for the
# woman who is leaving" is a yes/no with a relative clause in it, and it was read as a request for
# a person's name, so "Chipping in is a shared cost split between the people it is for..." was a
# miss. The `who` after a noun is the noun's own clause - "the woman who is leaving" is one person,
# not a question about who she is.
# A `who` followed by a pronoun and "am/are/is" is the person talking about themselves, not a
# question about who anyone is: "i dont know who i am now" was read as a request for a name and
# "I'm listening - say more if it helps." was a miss.
WHO_OF_A_PRONOUN = re.compile(r"\bwho (?:i|you|we|they|he|she|it) (?:am|are|is|was|were)\b", re.I)
WHO_OF_A_NOUN = re.compile(
    r"\b(?:the|a|an|this|that|these|those|someone|somebody|anyone|anybody|everyone|everybody|"
    r"no one|nobody|person|people|man|woman|boy|girl|child|kid|friend|colleague|neighbour|"
    r"neighbor|boss|manager|teacher|nurse|doctor|carer|minder|babysitter)\s+who\b", re.I)

# A line that opens on its who asks it, whatever person it names later: "who should i call about
# a neighbour who plays loud music" owes a name, and only the second who is the relative one.
WHO_OPENS = re.compile(r"^\W*(?:(?:and|so|but|then|or|also|now|ok|okay)\s+)?who(?:'s|s|se)?\b", re.I)
# The best way to do a thing is the method for it, not a thing picked: "what's the best way to
# cook rice" was read as a recommendation and answered with a pick. `best` is not the only word
# that judges a way: "what's the easiest way to peel a kiwi" and "the quickest way to chill a
# drink" were read as nothing at all, so the shape was lost and a method read as a miss. The
# judgement word has to be in front of `way`, `method` or `approach`, which is what keeps a
# judgement about a thing ("what is a good price", "a good breakfast") out of it.
BEST_WAY = re.compile(
    r"\b(?:the )?(?:best|good|right|proper|easiest|quickest|simplest|safest|cheapest|fastest) "
    r"(?:way|method|approach) (?:to|of|for)\b", re.I)
# "whats a good present for him", "whats a good tent for two": understanding reads the `what is`
# as a definition and the reply that offers ideas was a miss for not defining the word. Only a
# measure word keeps its own shape, and that is read before this ("what is a good time to go").
# "whats a good salary for a graduate", "whats a good interest rate", "whats a good credit score":
# a measure word asked for with "whats a good" wants the figure. The good-thing reading below turns
# it into a few to choose from, and no card of prices and rates answers a list. A "good tip for a
# first date" is advice and keeps its few ideas, so a tip only counts as money when nothing follows.
GOOD_MEASURE = re.compile(
    r"\bwhat(?:'s|s| is)\s+(?:a |an |the )?(?:really |actually |roughly |sensible |sort of )?"
    r"(?:good|decent|normal|typical|average|usual|realistic|fair)\s+(?:\w+\s+){0,2}"
    r"(?:salary|wage|wages|pay|income|rate|deposit|budget|score|pension|pot|percentage|percent"
    r"|tip(?!\s+(?:for|on|to|about)\b))\b", re.I)


GOOD_ONE = re.compile(r"\bwhat(?:'s|s| is) (?:a |an )?good\b", re.I)
# A thing to give somebody is asked for as a few ideas, not as one thing picked: "im looking for a
# gift for my dad", "i need a present for my sister, shes 30 and into running", "im after a present
# for my mum", "what birthday present". Every reply the deck holds for these lines offers three or
# four things and a rule for choosing between them ("Buy the one she will actually use rather than
# three she might"), which is the shape of `options`; read as one thing to pick, the same reply is a
# miss for taking no side. The gift word alone is not enough - a gift card has a balance and no
# recipient in the line, and "whoever filmed it has a gift" is praise - so the line has to say who
# the thing is for, or ask what to get.
# "give me a film for tonight", "gimme a book with a twist": the article names one thing, so the
# person wants one thing named back and not a definition of it or a few to choose from. The same ask
# with "some" or "a few" wants the few. The verbs are the imperative give, and the two that are the
# same request said politely; "get me" is left out because "get me a human" is a hand-off and not a
# choice.
GIVE_ME_ONE = re.compile(
    r"\b(?:gimme|give me|show me|send me)\s+(?:a|an|one|another)\s+([a-z][a-z'-]*)", re.I)
GIVE_ME_A_FEW = re.compile(
    r"\b(?:gimme|give me|show me|send me)\s+(?:some|a few|couple of|a couple|any)\s+"
    r"([a-z][a-z'-]*)", re.I)
# Ask for a hand-off and the pick is a person to reach, not a thing to choose: "give me a human".
GIVE_ME_NOT_A_THING = re.compile(
    r"\b(?:human|person|somebody|someone|real person|operator|manager)\b", re.I)
# English puts a lot of not-things after the article, and every one of them read as a thing to pick
# once the article was allowed to name one: "give me a minute" is the person thinking, "give me a
# hand" is help, "give me a ring" is a phone call, and "give me a rough idea of the cost" asks how
# much, which main already read as an amount before this arm took it away. None of them is a thing
# on a shelf, so the arm stands down and the reading falls through to the one that fits: the amount,
# the steps, or nothing. "go", "look" and "word" are left out on purpose - "give me a go bag" and
# "give me a look for a wedding" are things a person can want named.
GIVE_ME_AN_IDIOM = re.compile(
    r"\b(?:a|an|one)\s+(?:rough\s+idea|minute|minutes|second|seconds|sec|secs|mo|moment|break|"
    r"chance|ring|rings|shout|call|lift|ride|hand|hands|hint|clue|tip|tips|way|method|reason|"
    r"sign|excuse|rest|try|kiss|discount|picture|photo|image)\b", re.I)
# A thing the bot has to make up is not a thing to pick from: there is no shelf of limericks to
# choose from, so "give me a limerick" owes the verse and not a choice. A thing the world already
# holds many of - a film, a book, an album, a name, a dinner idea - is the pick.
GIVE_ME_MADE_UP = re.compile(
    r"\b(?:limerick|poem|haiku|riddle|joke|story|tale|rhyme|tongue twister|fun fact|"
    r"fact|quiz question|trivia question|general knowledge question|question|example|"
    r"routine|prompt|toast|speech|plan|itinerary|list|recipe)\b", re.I)
# The give has to be the person asking the bot. "they want to give me a credit note", "the shop
# didnt give me a receipt" and "my new glasses give me a headache" all say give me, and none of them
# asks for anything, so the word right before the phrase has to be a lead-in and not a subject.
GIVE_ME_LEAD_IN = frozenset((
    "ok", "okay", "so", "and", "now", "then", "just", "please", "also", "but", "you", "could",
    "can", "would", "will", "hi", "hey", "gimme", "me", "of", "if", "maybe", "alright"))


def _the_give_is_to_the_bot(said, at):
    """Whether the give at `at` is the person asking, and not somebody giving something to them."""
    before = said[:at].split()
    return not before or before[-1] in GIVE_ME_LEAD_IN

A_THING_TO_GIVE = re.compile(r"\b(?:gift|gifts|present|presents|pressie|pressies|"
                             r"stocking filler|secret santa)\b", re.I)
# A person, not a bare article: "i want a refund for a present i dont like" is a shop's policy and
# not a request for ideas, and the bare "for a" was all it took to read it as one. The article is
# allowed in front of the person ("what present for a mum who loves knitting") and so is an age,
# because that is how a present for a child is named.
A_PERSON_TO_GIVE = (r"(?:my|our|his|her|their|him|them|mum|mam|mom|dad|mother|father|sister|"
                    r"brother|son|daughter|nan|nana|grandma|grandad|granny|grandpa|gran|aunt|"
                    r"uncle|cousin|friend|mate|bestie|teacher|colleague|boss|partner|wife|"
                    r"husband|boyfriend|girlfriend|neighbours?|baby|newborn|toddler|child|kid|"
                    r"boy|girl|teenager|nephew|niece|in-laws?|flatmate|housemate|carer|"
                    r"\d+\s*(?:year|yr)s?\s*old)")
GIVING_FRAME = re.compile(
    r"\b(?:for|to)\s+(?:a|an|the)?\s*" + A_PERSON_TO_GIVE + r"\b"
    r"|\bwhat (?:should i |shall i |do i |can i |would you |to )?(?:get|buy|make|give)\b"
    r"|\b(?:idea|ideas|suggest|suggestion|suggestions|recommend|recommendation)\b", re.I)
# A gift card, a gift voucher and a present day are not things to give somebody.
NOT_A_GIVING_THING = re.compile(
    r"\bgift (?:card|cards|voucher|vouchers|wrap|wrapping|box|boxes|receipt|set)\b"
    r"|\bpresent (?:tense|day|perfect)\b|\bgift (?:aid|tax|taxable)\b"
    # A letter or a thank-you note for a present is a thing to write, not a thing to give.
    r"|\b(?:letter|note|thanks|thank you|receipt|return|returns)\b"
    # "my mum keeps buying gifts for the kids" is somebody else's habit, not a thing to go and find.
    r"|\b(?:keeps?|kept|always)\b[^?]{0,25}\b(?:gift|present)s?\b"
    r"|\b(?:buys|bought|gives|gave|brings|brought|receives|received)\b[^?]{0,20}\b(?:gift|present)s?\b",
    re.I)
# "how come the milk curdled" asks the cause, and understanding reads its "how" as a method, so
# the reply that says why read as a miss. "how come" is the everyday "why", never a how-to.
HOW_COME = re.compile(r"\bhow come\b|\bhow is it that\b", re.I)
# "what are the best museums in rome", "what are some good films to watch": a plural after the
# best, or "some/a few", asks for a few to choose from. Understanding reads the "what" as a
# definition and the reply that lists three museums read as a miss for not being a meaning.
BEST_OF_MANY = re.compile(
    r"\bwhat (?:are|were) (?:the )?(?:best|main|top|nicest|cheapest|better)\b"
    r"|\bwhat (?:are|were) (?:some|a few|any)\b"
    r"|\bwhat (?:are|were) (?:the )?\w+ (?:to|for)\b", re.I)
# "is that expensive", "is it pricey to run", "are they cheap": the whole predicate is the price,
# so the answer is the figure and the verdict rides with it - "A car MOT costs up to £54.85 ..." is
# the answer to "is that expensive". Understanding reads the "is it" as a yes/no, and a price
# answer then read as a miss for not opening with yes. Only a pronoun for the subject: "is a cheap
# guitar a waste of money" asks about the waste, not the price.
A_PRICE_ASK = re.compile(
    r"\b(?:is|are|was|were)\s+(?:it|that|this|these|those|they|there|one)\s+"
    r"(?:(?:too|so|really|actually|very|quite)\s+)?"
    r"(?:expensive|pricey|dear|cheap|costly)\b", re.I)
# A comparison ("cheaper than dried"), a worth ("worth it") and an affordability ("can i afford
# it") are verdicts with a reason, not a figure, so they keep their yes/no.
NOT_A_PRICE_ASK = re.compile(r"\bworth\b|\bcheaper than\b|\bmore expensive than\b|\bafford", re.I)
# "what are my rights", "what are my entitlements", "what are our obligations": a possessive asks what
# applies to this person, not what a word means. Understanding reads the "what are" as a definition,
# so the advice the bot gives ("Put it in writing, a text or email is fine, and keep a copy") was
# named a miss for answering the question that was asked. Read before the definition block below,
# and left alone by a line that asks what a thing is called or means.
WHAT_ARE_MINE = re.compile(
    r"\bwhat(?:'s| is| are|s)\b[^?]{0,40}?\b(?:my|our) (?:[a-z]+ ){0,2}"
    r"(?:rights?|entitlements?|obligations?)\b", re.I)

# A question about the person's own facts asks for the fact itself: it is not a definition and not
# a yes or no. "what are my kids called" is the plural of "what is my dog called", which already
# reads as no shape at all - the plural picked up the definition label from its bare "what are",
# so the bot's own recall ("Alice and Tom, you told me") and its honest "you haven't told me about
# your kids yet" were both scored for not defining anything. The same recall said politely was
# read as a yes/no about whether the bot can do it: "can you remind me what i said first" wants
# the words back, and the reply that quotes them was a miss. A "how" is left out on purpose,
# because "remind me how to boil an egg" is the method and "remind me how far it was" is a figure.
# The name of a person or a pet the person owns, asked in the plural. Kept apart from the recall
# below because the answer is a name and never a figure: "what are my kids called" is the plural of
# "what is my dog called", which reads as no shape at all.
MY_THING_CALLED = re.compile(
    r"\bwhat (?:are|is|were|was) (?:my|our)\b[^?]{0,30}?\b(?:called|named)\b", re.I)
# A request to be reminded of what the person said is a recall of their own words, and the words
# coming back are the whole answer. It is not a yes/no about whether the bot can do it, which is
# how "can you remind me what i said first" was read, and it is not a definition either. A "how" is
# left out on purpose: "remind me how to boil an egg" is the method and "remind me how far it was"
# is a figure, and both want the shape they already get.
RECALL_OF_MINE = re.compile(
    r"\bremind(?:ing)? me (?:what|who|which|where|when)\b"
    r"|\bwhat (?:did|do) i (?:say|told you|tell you|tell u|ask|asked|decide|choose)\b"
    r"|\bwhat (?:was|am) i (?:saying|doing|about to say)\b", re.I)

# A meaning is asked for by "what is a p60", "what does a p60 show", "what does it mean", "what do
# you call", "the difference between". Understanding writes `definition` off the word "what does"
# alone, so "what does my sister like" and "what does it cost" arrived as definitions of a word.
ASKS_FOR_MEANING = re.compile(
    r"\bwhat (?:is|are|was|were|'s)\b"
    # "what does engine oil do", "what does a full service include", "what does a p60 show": the
    # thing a subject does, holds or covers *is* what it is, so this is still a meaning ask.
    r"|\bwhat (?:does|do)\b(?:(?!\bwhat\b)[^?]){0,30}?"
    r"\b(?:do|does|include|includes|cover|covers|contain|contains|show|shows|sound like)\b"
    r"|\bwhat do you call\b|\b(?:mean|means|meaning|stand for|stands for|short for)\b"
    r"|\bdifference between\b", re.I)
# A number in front of the word `steps` does not make it a method: it is the unit the person
# walked in. Understanding reads the word as the ask for steps on every line that holds it, so
# "i did 12000 steps today" was a steps question and a good answer to "is 10000 steps a day
# enough" was a miss. Where the steps are counted - a figure in front of the word, a step count,
# or a count of them per day or per mile - the word is a measure, and the shape of the answer is
# whatever else the line asks. A line that does ask how to do it keeps the method, because the
# strong readings below return before this one: "how do i get my step count up", "steps to bleed
# a radiator".
STEPS_ARE_COUNTED = re.compile(
    r"\b\d[\d,]*\s*(?:k\s+)?steps?\b"
    r"|\bsteps? count\b"
    r"|\bsteps? (?:a|per|each|every) (?:day|week|month|hour|mile|km|kilometre)\b", re.I)
# "10000 steps in miles" and "steps per mile" are a conversion: the person knows the count and
# wants the distance, which is the figure, not the walk.
STEPS_AS_A_DISTANCE = re.compile(
    r"\bsteps? (?:in|into|to|per|versus|vs)\s+(?:a |one )?(?:mile|miles|km|kilometre|kilometres|"
    r"kilometer|kilometers)\b"
    r"|\b(?:mile|miles|km|kilometre)s? (?:in|to|from|of) (?:a |one )?\d[\d,]*\s*(?:k\s+)?steps?\b",
    re.I)


# A length of time said as a count of its unit: "how many hours between doses", "how many days
# does a cold last", "how many weeks pregnant am i". Understanding reads the "how many" as
# `how_much` and the shape came out an amount, so the reply was free to give any number at all -
# and "how many hours between ibuprofen doses" was answered with the dose, which is an amount.
# A measure asked in question form: the interrogative followed by a verb ("how much is that",
# "how many do i need", "how long will it take"). A measure followed by a noun is the person
# telling the bot something ("its amazing how much room there is", "i didnt know how long it
# would take") and is not an ask.
HOW_ASK_FORM = re.compile(
    r"\bhow (?:much|many|long|often|soon|far|tall|big|heavy|old|hot|cold)\s+"
    r"(?:is|are|was|were|does|do|did|will|would|can|could|should|shall|much|many|far)\b", re.I)
HOW_MANY_TIME = re.compile(
    r"\bhow (?:many|much) (?:more |longer )?(?:seconds?|secs?|minutes?|mins?|hours?|hrs?|days?|"
    r"weeks?|months?|years?|nights?|time)\b", re.I)
# A length in metres, centimetres or feet with "long" after it is a size, not a length of time: "a
# wall 6m long and 2.5m high", "a 4m long worktop", "a run 3.5 metres long". Understanding labels
# the line `how_long` off the word "long", so "how much paint for a wall 6m long and 2.5m high"
# owed a time and the paint card that gives the figure was scored as answering nothing. The size is
# read here and the label dropped when nothing in the line asks how long it takes; a duration word
# (take, last, hours, days, overnight) keeps the time reading, because "how long does a 6m run take
# to paint" really is a how-long.
A_SIZE_LONG = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:mm|cm|m|km|metres?|meters?|feet|foot|ft|inches?|in|yards?|yds?)\s+"
    r"(?:long|wide|high|deep|tall|thick)\b", re.I)
A_DURATION_WORD = re.compile(
    r"\b(?:take|takes|took|taking|last|lasts|lasted|lasting|keep|keeps|kept|stay|stays|sit|sits|"
    r"wait|waiting|seconds?|secs?|minutes?|mins?|hours?|hrs?|days?|weeks?|months?|years?|"
    r"overnight|fortnight|fortnightly)\b", re.I)


# The phrases that ask for a cause without the word why.
REASON_ASK = re.compile(
    r"\bhow come\b|\bwhat (?:causes|caused|causing|is causing)\b|"
    r"\bwhat(?:'?s| is| was)?\s+(?:causing|making|the cause|the reason)\b|"
    # "what makes thunder", "what makes you sneeze", "what makes my chest hurt" ask for the cause.
    # "what makes soup thick without cream" and "what makes a villain believable" ask how, and a
    # method is the right answer to them, so they are left to the shapes that read how-asks: the
    # question word of a "what makes X <quality>" is "how", not "why".
    r"\bwhat (?:makes|made) (?:you|me|us|people|him|her|them|it|this|that|someone|"
    r"my|your|our|their|his|its)\b|"
    r"\bwhat (?:makes|made) (?:the |a |an )?[a-z']+(?:(?: and| or) (?:the |a |an )?[a-z']+)*\s*$",
    re.I)
# The cause asked as what is wrong, which is how most people put it: "whats wrong with my boiler",
# "what is wrong with my loaf", "what am i doing wrong with my sourdough", "where am i going
# wrong". Understanding carries no shape for any of them - "wrong" is an ordinary word, not a
# question word - so the line owed nothing and a reply naming any shape at all was accepted. A word
# asked about ("what does wrong mean") and a yes/no ("is anything wrong with my boiler") are not
# this ask, and both are kept out.
DOING_WRONG = re.compile(
    r"\bwhat(?:'?s| is| was)?\s+(?:going\s+|gone\s+)?wrong\b"
    r"|\bwhat (?:went|had gone|has gone|have gone) wrong\b"
    r"|\bwhat (?:could|might|may|would) be (?:wrong|making|causing)\b"
    r"|\bwhat (?:am i|are we|did i|did we|have i|have we) (?:do|doing|done|did|get|getting|got|"
    r"have|having|had)\b.{0,25}\bwrong\b"
    r"|\bwhat (?:do i|do we|does he|does she|do they) do wrong\b"
    r"|\bwhere (?:am i|are we|did i|did we|do i|do we) going wrong\b"
    r"|\bwhat(?:'?s| is| was)?\s+(?:the|my|our|his|her|their)\s+(?:problem|trouble|issue|fault)\s+"
    r"(?:with|in)\b", re.I)
# "what does wrong mean", "what is wrong called" - the word itself is the thing asked about.
WRONG_ASKED_ABOUT = re.compile(r"\b(?:mean|means|meaning|meant|called|spell|spelled|word)\b", re.I)
# "remind me what was wrong with my back", "what was wrong with the car again": the person is asking
# for what was already said this conversation, not for a cause, so no cause is owed and a reply that
# looks it up again would be a different answer. A thing asked about in the past tense is the same
# recall, and a cause asked about the present ("whats wrong with my boiler") is not.
WRONG_RECALL = re.compile(
    r"\bremind me\b|\bwhat (?:was|were)\b[^?]{0,30}\b(?:wrong|problem|trouble|issue|fault)\b"
    r"|\b(?:wrong|problem|trouble|issue|fault)\b[^?]{0,20}\bagain\b", re.I)

# "whats the point of a dehumidifier", "any point in solar panels", "point of a warm up": the
# point of a named thing is the reason it is done, and a description of the thing, a price or a
# method answers a different question. The thing is read after the "of"/"in" so that a line about
# the point of nothing in particular is left to the shapes that comfort it.
POINT_ASK = re.compile(
    r"\bwhat(?:'?s| is| was)?\s+the point (?:of|in)\s+(\w+(?: \w+){0,2})"
    r"|^(?:any )?point (?:of|in)\s+(\w+(?: \w+){0,2})", re.I)
# "whats the point of any of it", "i just dont see the point in anything anymore": no thing, so no
# purpose is owed and the line is not read as a reason at all. A measure of a thing - a boiling
# point, a freezing point - is not the point of it either, and is kept out below.
POINT_NOT_A_THING = frozenset("""
    it this that these those anything everything nothing any all carrying carry continuing going
    living life you me us them anymore honestly really now boiling freezing melting smoke
    """.split())


# A bare follow-up, with no question word of its own: "and for brown rice", "what about once it is
# up", "and which of those two". It asks for the same kind of answer about something else, so it
# wants whatever the line before it wanted. Read on its own it is nothing of the kind: "and for
# brown rice?" after "how long does rice take" is a plain ask for the facts of brown rice, and the
# answer it is owed - a time - cannot be checked at all.
FOLLOWUP = re.compile(
    r"^\s*(?:and|so|then|but|ok(?:ay)?[,\s]+(?:and|so)|what\s+about|how\s+about|what\s+if|"
    r"would\s+that|does\s+that|same\s+(?:for|with))\b", re.I)
# A follow-up that asks its own question about the person's own next move is a new question, not
# the last one again: after "is it going to rain tomorrow", "so what do i take with me" is not a
# yes or a no. The verb is the person's own, so the answer shape is theirs too.
NEW_ASK = re.compile(r"\bwhat (?:do|does|should|shall|can|could|will|would) (?:i|we|you)\b", re.I)
# The words a person asks back for their own: "what did i say my budget was", "do you remember
# where i live", "did i say when we were going". The shape of that answer is not a yes/no about
# whether they said it - it is the kind of thing they said, in the kind's own shape: a budget is an
# amount, a name is a person, "when" is a time, "where" is a place. The store answers these from
# the line that carried it (`memory_store._recall_reply`), and the check declined to judge them, so
# a reply that handed them the search hedge or a fresh guess was neither credited nor counted.
RECALL_SAID = re.compile(
    r"\b(?:did|do)\s+(?:i|you)\s+(?:say|said|told|tell|mention|remember)\b", re.I)
# "what do i say when they ask why i left" is the opposite ask - it wants the words to say, not
# what they already said - and "how do i tell my team" is a method for a body. Neither is a recall.
RECALL_NOT = re.compile(
    r"\b(?:what|anything|something)\s+(?:do|does|should|can|could)\s+(?:i|you)\s+(?:say|tell)\b"
    r"|\bhow\s+(?:do|does|can|could|should|would)\s+(?:i|you|we|u|ya)\s+tell\b", re.I)
RECALL_TIME = re.compile(
    r"^(?:when|what\s+time|what\s+date|what\s+day|how\s+(?:long|soon|often)"
    r"|how\s+many\s+(?:weeks|days|months|years|hours|minutes|nights|times))\b", re.I)
RECALL_AMOUNT = re.compile(
    r"^(?:how\s+(?:much|many|old|heavy|tall|far|big)|what\s+age|what\s+size)\b", re.I)
RECALL_PLACE = re.compile(r"^where\b", re.I)
RECALL_PERSON = re.compile(r"^(?:who|what\s+name|(?:her|his|their|my|our)\s+name)\b", re.I)
# The kind named as the thing recalled: "what did i say my budget was", "what did i say her name
# was". The noun carries the shape even though no question word stands in front of it.
RECALL_KIND_NOUN = {
    "budget": AMOUNT, "rent": AMOUNT, "hours": AMOUNT, "shift": AMOUNT, "salary": AMOUNT,
    "wage": AMOUNT, "target": AMOUNT, "apr": AMOUNT, "age": AMOUNT, "size": AMOUNT,
    "name": PERSON, "day": TIME, "date": TIME, "time": TIME,
}
# "did i tell you when" puts the person between the verb and the shape they ask back for.
RECALL_PRONOUN = re.compile(r"^(?:you|me|us|it|that|then)\s+", re.I)
RECALL_KIND_NOUN_ASK = re.compile(
    r"^(?:my|our)\s+(budget|rent|hours|shift|salary|wage|target|apr|age|size|name|day|date|time)\b",
    re.I)


def _recall_wants(said, line=""):
    """The kind of thing a line asks back for ("what did i say my budget was" is an amount), or None.

    The shape is read from the words on either side of the recall verb: "how long did i say i had"
    puts it in front, "did i say when we were going" behind, and "what did i say my budget was"
    names it as the noun of the thing recalled. A shape word further back is not about the recall:
    "what did i say she does when she revises" asks what she does, so only the words right behind
    the verb are read.
    """
    whole = " ".join((line or said).lower().replace("\u2019", "'").split())
    if not whole or not RECALL_SAID.search(whole) or RECALL_NOT.search(whole):
        return None
    for match in RECALL_SAID.finditer(whole):
        after = RECALL_PRONOUN.sub("", whole[match.end():].strip())
        kind = (_recall_kind_in_front(after) or _recall_kind_named(after)
                or _recall_kind_behind(whole[:match.start()]))
        if kind:
            return kind
    return None


def _recall_kind_in_front(after):
    """The kind of thing asked back for, named at the front of the words behind the verb."""
    for pattern, kind in ((RECALL_TIME, TIME), (RECALL_AMOUNT, AMOUNT),
                          (RECALL_PLACE, PLACE), (RECALL_PERSON, PERSON)):
        if pattern.match(after):
            return kind
    return None


def _recall_kind_named(after):
    """The kind named as the thing recalled: "my budget", "her name"."""
    noun = RECALL_KIND_NOUN_ASK.match(after)
    return RECALL_KIND_NOUN[noun.group(1).lower()] if noun else None


# The shape a person names in front of the verb: "how long did i say", "where did i say". Only the
# words right before the verb are read, so a "when" earlier in the line is not the recall's shape.
RECALL_SHAPE_BEFORE = re.compile(
    r"(?:\bwhen|\bwhat\s+time|\bwhat\s+date|\bwhat\s+day|\bhow\s+(?:long|soon|often)"
    r"|\bhow\s+many\s+(?:weeks|days|months|years|hours|minutes|nights|times)"
    r"|\bhow\s+(?:much|many|old|far)|\bwhat\s+age|\bwhat\s+size|\bwhere|\bwho"
    r"|\bwhat\s+name)\s*$", re.I)
RECALL_SHAPE_BEFORE_KIND = (
    (("when", "what time", "what date", "what day", "how long", "how soon", "how often"), TIME),
    (("how many weeks", "how many days", "how many months", "how many years", "how many hours",
      "how many minutes", "how many nights", "how many times"), TIME),
    (("how much", "how many", "how old", "how far", "what age", "what size"), AMOUNT),
    (("where",), PLACE),
    (("who", "what name"), PERSON),
)


def _recall_kind_behind(before):
    """The kind asked in front of the verb: "how long did i say", "where did i say"."""
    match = RECALL_SHAPE_BEFORE.search(before)
    if not match:
        return None
    named = " ".join(match.group(0).lower().split())
    for words, kind in RECALL_SHAPE_BEFORE_KIND:
        for word in words:
            if named == word or named.startswith(word + " "):
                return kind
    return None


def asks_a_follow_up(understood):
    """True when the line is a bare follow-up: it opens on "and"/"what about" and asks nothing new."""
    if not isinstance(understood, dict) or understood.get("asks_a_verdict"):
        return False      # "and is that safe" asks the bot's own last answer a verdict
    said = _said(understood)
    if not FOLLOWUP.search(said):
        return False
    if set(understood.get("asks") or ()) - {"what", "yesno"}:
        return False      # it has a question word of its own: "and how much", "so which is better"
    if NEW_ASK.search(said):
        return False      # "so what do i take with me" asks something new of its own
    kind = understood.get("kind")
    if kind == "question" or said.rstrip().endswith("?"):
        return True
    # "and for brown rice" has no question mark and reads as a statement, but the reading knows it
    # leans on the line before. A short one of those is the same question again; a longer one is
    # the person adding something of their own ("and i also need a bin bag").
    line = str(understood.get("plain") or understood.get("text") or "")
    return kind == "statement" and bool(understood.get("followup")) and len(line.split()) <= 6


# A setting clause in front of the ask does not stop the ask being a time question. "we are getting
# married next year, when should we book the venue" and "got an interview thursday and nothing
# smart fits, what time should i get there" put the scene first, so the "when" that wants a time is
# not at the start of the line and `WHEN_ASKS` - which reads the opening - said nothing, and the
# line came out wanting no shape at all. The ask clause is the last one that opens on a question
# word, so it is read on its own.
_ASK_CLAUSE_SPLIT = re.compile(r"\s*(?:[,;:]|\band\b|\bbut\b|\bso\b|\bthen\b)\s*", re.I)
# A fragment asks too. People type the thing first and the measure after it - "boil an egg how
# long", "rice pudding how long does it keep", "a cup of tea how long to brew", "pulled a muscle
# in my calf how long till i can run" - and none of them is a question by its grammar: no question
# mark, no question word at the opening, so the measure reading was gated on `asking` and these
# came out wanting no shape at all. A measure word that ends the line, or that is followed by its
# own verb, is the ask. What a statement about a duration looks like is kept apart: "i didnt know
# how long it would take", "its amazing how much room there is", "not sure how long it keeps".
_TRAILING_MEASURE = re.compile(
    r"\b(?:how long|how soon|what time)\s*[.?!]*$", re.I)
_MEASURE_THEN_VERB = re.compile(
    r"\b(?:how long|how soon|what time)\s+"
    r"(?:do|does|did|will|would|should|shall|can|could|is|are|was|were|to|till|until|before|"
    # a preposition names what the duration is of, which is how most people say it: "a jacket
    # potato how long in the oven", "a leg of lamb how long per kilo", "a boiled egg how long for
    # hard boiled". The measure is still the ask.
    r"in|on|for|per|at|with|by|after|into|under|over|about|from)\b",
    re.I)
_TALKING_ABOUT_A_LENGTH = re.compile(
    r"\b(?:i|we|you|they|he|she)\s*(?:did ?n[o']t|do ?n[o']t|does ?n[o']t|never)?\s*"
    r"(?:know|knew|realise|realize|remember|wonder|wondered|sure|idea)\b"
    r"|\b(?:amazing|surprising|interesting|funny|odd|strange) how (?:long|soon|much|many|often)\b"
    r"|\bno idea how\b|\bhow long it (?:takes|took|would take|will take)\b", re.I)


def _a_fragment_asks_for_a_time(said):
    """True when a measure word in the line is the ask, even with no question grammar."""
    if _TALKING_ABOUT_A_LENGTH.search(said or ""):
        return False
    return bool(_TRAILING_MEASURE.search(said or "") or _MEASURE_THEN_VERB.search(said or ""))


_ASK_CLAUSE_OPENS = re.compile(
    r"^(?:when|what|which|how|where|who|why|whom|whose|should|shall|can|could|do|does|did|will|"
    r"would|is|are|was|were|am|have|has|had)\b", re.I)


def _the_ask_clause(said):
    """The last clause of a line that opens on a question word, or "" when none does.

    A two-clause line - the scene, then the question - is answered from the question, so the words
    that say what it asks are read there rather than at the opening of the setting.
    """
    parts = [part.strip() for part in _ASK_CLAUSE_SPLIT.split(said or "") if part.strip()]
    if len(parts) < 2:
        return ""
    last = parts[-1]
    return last if _ASK_CLAUSE_OPENS.match(last) else ""


def wants(understood, before=None):
    """The shape of answer the line asks for, or None when the line does not ask for one.

    Read from the whole line's reading, not one keyword. `asks_a_verdict` ("is that bad", "should
    i worry") is a yes/no about the bot's own last answer and comes before every `asks` label;
    `help_ask` ("anything i can do about it") is a bare ask for steps. A question about the bot
    itself ("who are you") wants the bot's own answer and no shape from this list, so it is left
    alone rather than read as a who-question that owes a person's name.
    """
    if not isinstance(understood, dict):
        return None
    # "can you remind me what i asked you first" opens on "can you" and the engine writes the
    # yes/no; the same ask told plainly - "what did i say about the boiler", "what was my first
    # question" - carries no label either way. What the line asks for is the line the person said
    # earlier, which the store answers: neither a yes nor a no is an answer to it, and it is not
    # the question before it asked again either, so no shape is owed.
    if A_RECALL_ASK.search(_said(understood) or ""):
        return None
    own = _wants_alone(understood)
    own = _the_shape_named_outside_the_reading(understood, own)
    if own:
        # The line asks for a shape of its own: "and can i freeze it" after "how long does rice
        # take" is a question about whether, and a time would answer a different question.
        return own
    # A bare noun asked what it is owes a definition, and `_wants_alone` found no shape of its own:
    # "what is nectar", "what is umami", "what is bulgur". Read here, after every ask with a
    # reading of its own and before the follow-up inherits one, so it can only add a shape where
    # there was none: a bare "what is it" after a topic still wants what the topic wants.
    if _a_bare_definition(understood):
        return MEANING
    if before and asks_a_follow_up(understood):
        return before     # nothing of its own, so it is the same question again about something else
    return None

# --- a shape the reading missed, named outright ------------------------------------------------
# A cause already given is a verdict, not a cause to explain again: "is that why im tired",
# "is that why the radiators are cold at the top" ask whether the cause just given is the right
# one, so the yes comes first and the reason after it. Understanding reads the `why` and the line
# owed a cause, so a reply that explained something else again was credited and the verdict the
# person was waiting for was not required.
CONFIRM_CAUSE = re.compile(
    r"(?:^|[;,.]\s*|\b(?:and|so|but|then)\s+)(?:is|was) (?:that|this|it) why\b", re.I)
# "and if they ask why?" sets up a situation rather than asking for a verdict, so the "ask why" in
# it is what happens next and not the question.
IF_IT_HAPPENS = re.compile(r"^\W*(?:and\s+|so\s+|but\s+|then\s+)?if\b", re.I)
# The same ask about the person's own next move: "should i ask why", "should i explain why".
ASK_TO_ASK = re.compile(r"\bshould i (?:ask|explain|check|say|mention|bring up)\s+why\b", re.I)
# A figure named outright is the answer even with no judgement word beside it: "what price should
# i ask", "what number should it be on", "what dose of paracetamol for a 6 year old". The units in
# `WHAT_FIGURE` are the ones a cook or a driver names; these are the money and count ones, and the
# line owed nothing without them, so a reply that gave a figure was neither credited nor blamed.
A_FIGURE_NAMED = re.compile(
    r"\bwhat (?:age|price|cost|number|salary|pay|wage|rate|fee|dose|dosage|amount|percentage|"
    r"percent|discount|charge|quote|score|mark|grade|figure|budget)\b", re.I)
WHAT_TIME_NAMED = re.compile(r"\bwhat time\b", re.I)


def _the_shape_named_outside_the_reading(understood, own):
    """The shape a line names outright, when the reading found none or found a cause instead.

    A reading of the question words is what most lines need. These two are the words that name the
    answer themselves and that no cue list carries: a cause the person has just been given, and a
    figure whose unit is money or a count. Neither is a keyword family - both are read off the
    whole line - and both are kept out of `_wants_alone` because they correct its answer rather
    than add to it, so they run on the shape it returns.
    """
    said = _said(understood) or ""
    if not said:
        return own
    if IF_IT_HAPPENS.match(said):
        return own
    if own == REASON and CONFIRM_CAUSE.search(said):
        return YESNO
    if own in (None, REASON, MEANING) and ASK_TO_ASK.search(said):
        return YESNO
    if own is None and A_FIGURE_NAMED.search(said):
        return TIME if WHAT_TIME_NAMED.search(said) else AMOUNT
    return own



def wanted(memory):
    """The shape of answer this turn asked for, read from the store rather than from a reading.

    `wants` above is the finder: it reads one reading of the line. A module that holds a reading
    of its own is not the turn, though - `answers._ask_a_rewritten_line` swaps `understood` for a
    reading of words the person never typed, and the module underneath then looked at a line that
    asked for nothing. The shape is a fact about the turn, so a module that wants to know which
    answer it owes asks the store: `bot/modules/intent.py` keeps it under `understood["wants"]`,
    and `intent_wants` holds the bare shape for the same turn.
    """
    if not isinstance(memory, dict):
        return None
    read = memory.get("understood")
    if isinstance(read, dict):
        want = read.get("wants")
        if want in WANTS:
            return want
    want = memory.get("intent_wants")
    return want if want in WANTS else None


def _wants_alone(understood):
    """The shape this line asks for on its own words, ignoring the line before it."""
    # A line that asks back for its own detail wants the kind of thing it named, not a yes/no about
    # whether it was said: "what did i say my budget was" an amount, "do you remember where i live"
    # a place, "did i say when we were going" a time. It comes before `about_bot` because the engine
    # hears "you" and a question and reads the line as a question about the bot itself: "do you
    # remember where i live" and "did i tell you when" were both free of any shape that way, and a
    # recall answered with a search hedge was neither credited nor counted.
    asked_back = _recall_wants(_said(understood), _whole(understood))
    if asked_back:
        return asked_back
    if understood.get("about_bot"):
        return None
    if understood.get("asks_a_verdict"):
        return YESNO
    # A "who" question that borrows the words of a help ask still asks for a person: "who can help me
    # with my debts", "who can help me sort out my pension" name who to go to, and `help_ask` (read
    # from the "help me with") was answering them with the steps - a how-to for a question about
    # who. Only an opening "who" counts: "can you help me with a budget" is still the steps, and
    # "what can help with the pain" is not a person.
    if OPEN_WHO_HELP.search(_said(understood)):
        return PERSON
    said = _said(understood)
    # The task a help ask names is read from the line as it was typed: `_said` repeats a short line
    # once per reading it carries, and the words after the help phrase are the whole of the test.
    typed = _whole(understood) or said
    if understood.get("help_ask"):
        return None if _a_help_ask_that_names_nothing(typed) else STEPS
    asks = understood.get("asks")
    asks = set(asks) if isinstance(asks, (list, tuple, set)) else set()
    # A line the engine reads as news is the person telling the bot something, not asking: "my
    # brothers birthday is on the 2nd of june" carries `maths` for the 2nd and "we were thinking
    # italy or spain" carries `choice` for the two countries, and neither owes a figure or a pick.
    # "A birthday to get something for. Any idea what yet?" and "Sounds alright. Anything good in
    # it?" were scored as replies that missed a question nobody asked. Only the two loose labels
    # are dropped: a how-long, a why or a where on a news line is still asked for.
    if understood.get("intent") == "news":
        # A sum said out loud is an ask even when the line is phrased as news: "we split the bill
        # 4 ways on 86 pounds", "me and my partner split the bills". The figure is the question.
        dropped = {"choice"}
        if not (SUM_OUT_LOUD.search(said) or SUM_ASKS.search(said)):
            dropped.add("maths")
        asks -= frozenset(dropped)
    # A statement that only carries the words of a measure is not asking for one: "its amazing how
    # much room there is" and "i didnt know how long it would take" name no figure to go and find.
    # Only a line that asks - a question, or a request like "tell me how long it takes" - owes one.
    # ... and a line that gives its context first and asks in the same breath is asking, whatever
    # the engine called the whole line: the question clause is read on its own (`QUESTION_IN_THE_LINE`).
    asking = (understood.get("kind") == "question"
              or understood.get("intent") in ("question", "request")
              # A measure asked in question form inside a sentence is still asked: "if i save 50 a
              # week for a year how much is that", "i get 15 an hour how much is that a month".
              # The interrogative is followed by a verb, so the line is a question whatever the
              # engine called it, and the figure is what the person is waiting for.
              or bool(HOW_ASK_FORM.search(said))
              or (bool(QUESTION_IN_THE_LINE.search(said))
                  and not REPORTED.search(said)))
    # "how are you" has the word how and asks for no shape at all.
    if HOW_ARE_YOU.match(said):
        return None
    # A report of how something went asks for neither a method nor a figure: see HOW_IT_WENT.
    if HOW_IT_WENT.search(said):
        return None
    if HOW_IT_HAPPENED.search(said):
        return REASON
    # A request for help with a thing is the help itself: "can you help me with a budget" is a
    # steps question, not a yes/no about whether the bot can.
    if HELP_ME.search(said):
        return STEPS
    # The same ask without the "with": "help me plan a week of meals", "i need help planning meals".
    # A help ask that names no task at all is not a steps ask: "i need help" and "i need help with
    # something" are answered by asking what is going on, and that reply is the right one.
    if HELP_ASK_ANY.search(typed):
        return None if _a_help_ask_that_names_nothing(typed) else STEPS
    # A cause asked as what is wrong is read here, before the "where" guards below, because
    # "where am i going wrong" is a cause and its words say where: "whats wrong with my boiler",
    # "what am i doing wrong with my sourdough", "where am i going wrong". Understanding carries
    # no shape for any of them - "wrong" is an ordinary word, not a question word - so the line
    # owed nothing and a reply naming any shape at all was as good as one giving the cause. A word
    # asked about ("what does wrong mean") and a yes/no ("is anything wrong with my boiler") are
    # not this ask and are kept out.
    if asking and not REPORTED.search(said) and DOING_WRONG.search(said) \
            and not WRONG_ASKED_ABOUT.search(said) and not WRONG_RECALL.search(said):
        return REASON

    # "whats the fix for a squeaky door": the method to put it right is the answer, and the fault's
    # explanation or its price is a different answer to a different question.
    if FIX_ASK.search(said) and not re.match(r"\s*(?:is|are|can|could|will|would|do|does)\b", said):
        return STEPS
    # Neither "where do i start" nor "the best way to ..." asks for a place or a pick, whatever
    # their words look like: both want the method.
    if WHERE_START.search(said) or BEST_WAY.search(said):
        return STEPS
    # A task the person says they have to do is a request for the method, not news: "i need to
    # register the death", "i have to sort out her pension", "i've got to ring the council". The
    # engine reads it as a statement and the line is left owing nothing, so the bot answers the
    # sad part and drops the task the person just named. Only a task with a verb after it: "i
    # need a hug", "i have to go" and "i need to sleep" name a feeling or an exit, not a method.
    # And only when the line asks nothing else of its own: "i need to sort dinner, what can i cook
    # for one" asks for a pick, "who do i tell" asks who, "is that fair" asks for a verdict, and an
    # arm that read the task first took all of those for steps and stood the right answer down
    # (salmon-llama on #13102: 8 lines, 4 shapes). The labels that ride on a task's own words
    # without asking anything - the verb of the task itself ("i need to write a letter to my
    # landlord" is steps, and `write` is what the line does not what it wants), a number in it and
    # an "or" of two things - are dropped, as the news reading above drops its two.
    if NEED_TO.search(said) and not NEED_TO_ASKED.search(said) \
            and not (asks - {"maths", "choice", "write"}):
        return STEPS
    # A "where" on the point of something asks for a reason to carry on, and no place answers it.
    if WHERE_POINT.search(said):
        return None
    # A "where" about somebody's own whereabouts, or about where a thing comes from, is not a
    # place the world keeps: it is answered from what the person said ("you haven't mentioned a
    # place yet") or by what makes the thing ("bees make it"). No place named is the right answer.
    if WHERE_RECALL.search(said) or WHERE_ALONE.search(_whole(understood)):
        return None
    if HOW_TO_ANSWER.search(said):
        return STEPS
    # The same figure asked for in other words: "whats the going rate for a plumber", "what
    # should i expect to pay for a new tyre", "what will it set me back". A question word has to be
    # in the line, so "the holiday set me back a fortune" stays the piece of news it is.
    if (PRICE_IDIOM.search(said) and asking
            and re.search(r"\b(?:what|how much)\b", said)):
        return AMOUNT
    # "how come the milk curdled" is a why, not a how-to, and wants the cause.
    if HOW_COME.search(said):
        return REASON
    # A first-person how asks for the method, whatever measure word rides along with it:
    # "how do i plan a long drive" carries `how_long`, "how do i stop getting so many emails"
    # carries `how_much` and "how do i memorise a list quickly" carries `list`, so each of those
    # readings owed the person a figure or a menu instead of the steps they asked for. The engine
    # has already labelled these `steps`; this keeps the label rather than letting a word of the
    # line outrank it. Two things still outrank it: a sum with figures in it ("how do i divide 45
    # by 9" wants the number) and weighing the person's own life against somebody else's ("how do
    # i compare myself to others" is a pick, and so is "how do i compare to my sister").
    if ("steps" in asks and HOW_I.search(said) and not COMPARE_MYSELF.search(said)
            and not (("maths" in asks or "how_much" in asks) and re.search(r"[0-9]", said))):
        return STEPS
    # An overview of the kinds of a thing is a menu, not the meaning of a word and not one idea to
    # take: "what kinds of coffee are there", "what types of insulation can i get", "what are my
    # options for a new phone", "what else is there for a sore throat". The identifying form - "what
    # kind of dog is that" - asks what the one in front of the person is, so it is left to the
    # readings below rather than read as a menu.
    # The method asked for as a set of steps comes first: "what are the steps to reset a boiler"
    # holds the same "what are the ..." as the menu below, and only one of them is the answer.
    if STEPS_ASK.search(said) and not (COUNTED_STEPS.search(said)
                                       and not re.search(r"\bhow (?:do|can|should) i\b", said)):
        return STEPS
    # The signs, symptoms and stages of a thing are the members of a set, not the meaning of the
    # word: "what are the early signs of dehydration" is answered by the four signs, and the reply
    # that listed them was scored for not defining anything.
    if MEMBERS_ASK.search(said):
        return OPTIONS
    if KINDS_OF.search(said) and not NOT_KINDS_OF.search(said):
        return OPTIONS
    # A comparison names two things and wants both of them and what sets them apart, which is a
    # different answer from taking a side: "compare a dehumidifier and a window vac", "gas vs
    # electric hob", "how does a heat pump compare with a gas boiler", "what sets a leasehold apart
    # from a freehold", "is a heat pump better than a gas boiler". A line that names two sides and
    # asks which to take is a pick, so a should-i or a worth asking it keeps the pick below.
    if (COMPARISON.search(said) or COMPARED.search(said)) \
            and not NOT_A_COMPARISON.search(said) \
            and _names_a_pair(said) and _asks_about_them(understood, said):
        return COMPARE
    # Where a thing comes from is how it is made: "where does honey come from" wants the bees and
    # the nectar, and it is the same answer a `what is it` would get. See ORIGIN_ASK.
    if (ORIGIN_ASK.search(said) and not ORIGIN_PERSON.search(said)) or MADE_OF.search(said):
        return MEANING
    # A few to choose from, not the meaning of a word: "what are the best museums in rome". Not
    # when the plural is a price word the line is asking about: "what are the fees for a passport"
    # and "what are the charges for a replacement" match this reading - a plural after "what are
    # the" and a "for" - and were answered with a list to choose from instead of the money.
    if BEST_OF_MANY.search(said) and not (COST_ASK.search(said) and asks <= COST_STANDS_IN):
        return OPTIONS
    # "what are my rights" is a question about the person's situation and wants what to do next,
    # not the meaning of a word.
    if ("definition" in asks and WHAT_ARE_MINE.search(said)
            and not re.search(r"\b(?:called|mean|means|meaning|stand for|stands for)\b", said)):
        return STEPS
    # The name of a pet or a person of their own owes no shape at all: the answer is the name, and a
    # reply that says it has not been told yet answers the question as well as one that gives it.
    if MY_THING_CALLED.search(said):
        return None
    # A definition is owed only when the line asks what a thing is or means; understanding writes
    # the label off the words "what does", which also ask what someone likes and what a thing costs.
    if ("definition" in asks and re.search(r"\bwhat does\b", said)
            and not ASKS_FOR_MEANING.search(said)):
        asks.discard("definition")
    # A statement owes nobody a definition, whatever word it carries: "thanks, that explains the
    # boiler", "that explains the noise". Understanding writes `definition` off "explains", which
    # is not an ask; a line that does ask - "what does that mean", "the difference between" - is
    # left alone.
    if "definition" in asks and not asking and not ASKS_FOR_MEANING.search(said):
        asks.discard("definition")
    # "whats a good podcast for the car", "wats a gud cake", "wots a good cheap pressie": a good or
    # cheap or quick thing is asked for as a few to choose from, not the meaning of a word.
    # Understanding labels the "what" a definition, and the pick the bot gives then reads as an
    # answer to a different question. A good way to do something is the method, not a few ideas.
    # A measure word asked for with "whats a good" wants the figure: "whats a good salary for a
    # graduate", "whats a good interest rate", "whats a good credit score". The reading below hands
    # any good thing a few to choose from, and no card of prices and rates answers a list.
    if GOOD_MEASURE.search(said):
        return AMOUNT
    if GOOD_THING.search(said) and "definition" in asks and not GOOD_FIGURE_WORD.search(said):
        return STEPS if GOOD_WAY.search(said) else OPTIONS
    # The mechanism of a thing is a meaning, and understanding reads its bare "how" as a method:
    # "how does a lock and key work", "how do tides work". Only the "how do/does/did <thing>
    # work" form, never "how do i work out a tip" (a method) and never "how is work" (small talk).
    if HOW_IT_WORKS.search(said) and not re.search(r"\bhow do i\b", said, re.I):
        return MEANING
    # A who the person in the line already owns is the relative pronoun, not the ask:
    # "a present for my sister who just had a baby" wants a present, not the name of a person.
    if "who" in asks and not WHO_OPENS.match(said) and _a_who_a_person_owns(understood):
        asks.discard("who")
    # A who that shares its line with a measure asks for the rule, not the name of a person.
    if "who" in asks and (WHO_AND_MEASURE.search(said) or WHO_OF_A_PRONOUN.search(said)
                          or (WHO_OF_A_NOUN.search(said) and not WHO_OPENS.match(said))):
        asks.discard("who")
    # The "where" of "should i stay where i am" is the pronoun of a clause, not the place the
    # line asks for: it asks whether, and the verdict is what it is owed. A line that asks to be
    # told the place - "can you tell me where it is" - keeps its place.
    # A sum that goes is spending and not a place: "i never know where my money goes", "where does
    # all my money go". The answer is what to do with it, so the method is what is owed.
    if "where" in asks and WHERE_MONEY_GOES.search(said):
        return STEPS
    if "where" in asks and (asks & frozenset(("yesno", "recommend"))) \
            and WHERE_RELATIVE.search(said) and not ASKS_TO_BE_TOLD_WHERE.search(said):
        asks.discard("where")
    # "long time no see" carries the words of a how-long and asks for nothing on the clock.
    if LONG_TIME.search(said):
        asks.discard("how_long")
        asks.discard("how_often")
    # A measure question wants the figure, whatever else its words carry: "how long should i boil
    # an egg" and "how often should i wash the bedding" both read as `how_long`/`how_often` and a
    # yes/no from the "should i", and a yes/no is the wrong answer to either.
    # A conversion of a length asks for a figure in other units: "how long is 100m in feet" is
    # not a question about time, whatever the word "long" says, so it is read before the measure.
    if CONVERSION.search(said) or CONVERTED_FIGURE.search(said):
        return AMOUNT
    # A measure question that is not asking for a measure: "how much do you know about boilers"
    # asks about the bot, and "how much does it matter" asks whether it matters at all. Neither
    # owes a figure, and the how_much label is on both, so the guard stands in front of the
    # reading rather than after it.
    if NOT_A_FIGURE.search(said):
        return None
    if asks & MEASURE_LABELS and asking:
        # A written thing's "how long" is a length in words, pages or characters and not in
        # minutes: "how long should a personal statement be" is the 4,000-character limit,
        # "how long should an essay be" the word count. The noun followed by "be" is what tells
        # it from "how long should i leave it before replying to a text", which is a duration.
        if "how_long" in asks and WRITTEN_THING.search(said):
            return AMOUNT
        # A thing that extends has a length, not a duration: "how long is the nile" is 6,650 km,
        # "how long is a football pitch" 105 metres, "how long is the marathon" 26.2 miles. The
        # noun being measured is what decides, exactly as with the written thing above; the words
        # that last - a flight, a wait, a shift, a course - keep their time.
        if "how_long" in asks and THING_THAT_EXTENDS.search(said):
            return AMOUNT
        # A method whose subject happens to hold the word "long" wants the steps, not a length:
        # "how do i do long division" was scored as a reply that gave no time, because the reply
        # gives the four steps over and over, which is the whole of what was asked.
        if "how_long" in asks and "steps" in asks and METHOD_OPENS.match(LEADING_JOIN.sub("", said)):
            return STEPS
        # A "long" that follows a measurement is a size and not a span: "how much paint for a wall
        # 6m long and 2.5m high", "how much does a 2m long worktop cost". Nothing in either line asks
        # how long the job takes - no take, last, hours or days - so the figure asked for is a
        # quantity or a price and the time reading is dropped. A line that does ask how long the
        # job takes keeps it: "how long does it take to paint a wall 6m long".
        if "how_long" in asks and A_SIZE_LONG.search(said) and not A_DURATION_WORD.search(said):
            if "how_much" in asks or "how_many" in asks or re.search(r"\bhow (?:much|many)\b", said):
                asks.discard("how_long")
                return AMOUNT
            return None
        # "how many hours between doses" is a time and not an amount: the figure is a number of
        # hours. Main keeps its own "how_long" reading and this adds the counted unit to it.
        return TIME if "how_long" in asks or HOW_MANY_TIME.search(said) else AMOUNT
    # A price or a weight asked for with "what does" is the figure, not the meaning of a word:
    # "what does a boiler service cost", "what does a cup of honey weigh", "what do tyres cost".
    if (WHAT_DOES_MEASURE.search(said) and not ASKS_FOR_MEANING.search(said)
            and not COSTS_NOTHING.search(said)):
        return AMOUNT
    # ... and a price asked as a definition wants the figure too.
    if WHAT_IS_PER.search(said):
        return AMOUNT
    if "how" in asks:
        # A how that measures something wants the figure, and understanding reads the word after
        # "how" as a method: "how tall am i" is an amount, "how soon can i fly" a time.
        if HOW_SOON.search(said):
            return TIME
        if HOW_MEASURE.search(said):
            return AMOUNT
        # A line that opens on a measure word wants the figure, whatever "should" makes of the rest
        # of it: see HOW_MEASURE_HEAD.
        if HOW_MEASURE_HEAD.match(LEADING_JOIN.sub("", said)):
            return AMOUNT
        # "how do i explain moving house to my son" is a method; "explain" had it read as a
        # definition, which owes a meaning rather than the steps. It is only a method when the
        # person does the explaining: "explain how wifi works to me" and "how does darts scoring
        # work" want the meaning itself, and a reply that explains it is not a miss.
        if HOW_TO_DO.search(said):
            asks.discard("definition")
    # A fragment that names the measure is asking for it, whatever its grammar.
    if _a_fragment_asks_for_a_time(said):
        return TIME
    # A question that opens on "when" wants a time; a "when" inside a clause does not.
    asked = LEADING_JOIN.sub("", said)
    # A setting clause in front of the ask hid the ask when the ask opened on "when": "i twisted my
    # ankle last week, when can i run again" and "we move in spring, when should i plant tomatoes"
    # wanted none, because "when" was not the line's first word. The engine already marks the ask
    # clause (`understood["focus"]`), so that clause is read as well - a "when" inside the setting
    # ("when i get home i want to change, what should i do") is still not the question asked.
    # `asking` is the ask with the measure word it was said with ("how long do they stay on"),
    # when understanding provides it; `focus` is the same clause without it, which is what every
    # tree has today. Either is the clause the question is in, not the setting.
    focus = understood.get("asking") or understood.get("focus")
    focus_said = (" ".join(str(w) for w in focus) if isinstance(focus, (list, tuple))
                  else focus if isinstance(focus, str) else "")
    if (WHEN_ASKS.match(asked) or WHEN_ASKS.match(LEADING_JOIN.sub("", focus_said.strip()))) \
            and not WHICH_DAY_IS_BEST.search(said):
        return TIME
    # ... and one that says its scene first asks for the same time from its second clause.
    ask_clause = _the_ask_clause(said) if asking else ""
    if (ask_clause and WHEN_ASKS.match(LEADING_JOIN.sub("", ask_clause))
            and not WHICH_DAY_IS_BEST.search(said)):
        return TIME
    # "what are hospital visiting times", "what are the opening times of the tip", "what are the
    # school term dates": understanding reads the "what are" as a definition, so the line came out
    # wanting the meaning of a word. What it wants is on the clock. A line that asks what a thing
    # is *called* still wants the meaning ("what are those times called").
    if WHAT_ARE_TIMES.match(said) and not REPORTED.search(said) and not re.search(
            r"\b(?:called|mean|means|meaning|stand for)\b", said):
        return TIME
    # A good or bad time to do something is a judgement, and a yes or no answers it. It stands in
    # front of the figure below, which reads the same words as a number on the clock.
    if A_GOOD_TIME.search(said):
        return YESNO
    # "what is a good half marathon time" is a figure, and understanding reads its "what" as a
    # definition. A good or average time, age, price or number is the figure that follows.
    if GOOD_FIGURE.search(said) and not VERDICT_FRAME.match(said):
        # A good time is on the clock, and a good price, age, salary or temperature is a figure
        # read out of the world: "whats a good half marathon time" against "whats a good salary
        # for london", which used to fall through to the few-ideas shape and read the figure as a
        # miss for not being a list.
        return TIME if re.search(r"\b(?:time|timeframe)\b", said) else AMOUNT
    # ... and the same ask with a judgement word the list above does not carry: "whats a safe
    # temperature for a fridge", "whats the ideal weight for a labrador", "what is the right
    # tyre pressure for a fiesta". A judgement about a time is left to the reading above, which
    # knows a time from a figure.
    if JUDGED_MEASURE.search(said) and asking and not ON_THE_CLOCK.search(said) \
            and not REPORTED.search(said) and not ASKS_YES_OR_NO.match(LEADING_JOIN.sub("", said)):
        return AMOUNT
    # A good thing is a thing to pick, not a word to define.
    if GOOD_ONE.search(said):
        return OPTIONS
    # A thing to give somebody is a few ideas rather than one thing picked: see A_THING_TO_GIVE.
    # Not when the line asks a verdict, though: "is 20 enough for a secret santa" and "should i chip
    # in for a present for the woman who is leaving" are owed a yes or a no, and a price band that
    # happens to name several things would have scored them green as a list.
    # A thing asked for with an article is one thing to pick, and with "some" it is the few: see
    # GIVE_ME_ONE. Read before the present branch, which owes a list.
    # Only a line that asks: "they wont give me a refund because i paid by card" and "my new
    # glasses give me a headache" are news about a give, not a request for one.
    if asking and not GIVE_ME_NOT_A_THING.search(said) and not GIVE_ME_MADE_UP.search(said) \
            and not GIVE_ME_AN_IDIOM.search(said) and "list" not in asks:
        found = GIVE_ME_A_FEW.search(said)
        if found and _the_give_is_to_the_bot(said, found.start()):
            return OPTIONS
        found = GIVE_ME_ONE.search(said)
        if found and _the_give_is_to_the_bot(said, found.start()):
            return PICK
    if (A_THING_TO_GIVE.search(said) and GIVING_FRAME.search(said)
            and "yesno" not in asks and not NOT_A_GIVING_THING.search(said)):
        return OPTIONS
    # A what-should-i-cook/watch/wear names an open choice and wants one thing picked; the verb
    # is what tells it from "what should i do first", which wants the steps. Understanding already
    # calls a `what should i have` a choice, so the `do` spelling of the same verbs is read here -
    # except a `what do i have`, which is a recall of the list the person already gave.
    # A question that names the unit of the figure it wants owes the figure: "what temperature
    # should i cook chicken at", "what gas mark for a sponge".
    if WHAT_FIGURE.search(said) or WHAT_AGE.search(said):
        return AMOUNT
    # "what helps a sore throat" wants the few things that might work, and "what would you take
    # to a new baby" the list of things: both are a few ideas, not one method, not a definition.
    # The need with a doing verb after it is the method rather than the list, so it is read first.
    if NEED_TO_DO.search(said):
        return STEPS
    if WHAT_HELPS.search(said) or WHAT_YOU_TAKE.search(said) or WHAT_I_NEED.search(said):
        return OPTIONS
    # The same ask said to the bot: "what do you do about that" is the method.
    if WHAT_YOU_DO.search(said):
        return STEPS
    # The same ask said with the auxiliary: "what do i write in a thank you card" is the method
    # `what to write` names, and "what can i sow next month" the menu `what to plant` names. A
    # question somebody else asked is a report, and a line that opens on another question word is
    # that question first.
    if not REPORTED.search(said) and not OTHER_QUESTION.match(said):
        if WHAT_I_WRITE.search(said):
            return STEPS
        if WHAT_I_GROW.search(said):
            return OPTIONS
    # "what can i bake" is answered by a few things to choose from as often as by one thing, and
    # the good replies a person gets - "Scones take 15 minutes, flapjacks 25, a Victoria sponge 40"
    # - were counted a miss when they were read as a pick. The bake is a menu, so it is read as one,
    # and the ask is read whichever way it is written (with or without the auxiliary, and about
    # somebody else: "what should she bake").
    if WHAT_TO_BAKE.search(said):
        return OPTIONS
    # A bare "what <plural noun>" fragment is a choice: "first day at the office, only jeans, what
    # trousers". Read after every reading that names a shape of its own, so a line that is already
    # a menu, a figure or a method keeps the shape it had.
    if WHAT_THING_FRAGMENT.search(said) and not SUBSTITUTE.search(said):
        return PICK
    # "what can i do with a bag of apples going soft" is a uses ask: the things to do with what
    # is in the cupboard, not a pick between two and not one method. It read `pick` off the words
    # "do with", so a single recipe was the pass and a menu of them had to say which to take; the
    # set is what "any ideas for these apples" asks for too. A remark that only says the person
    # does not know what to do with something asks for nothing.
    # A person is not a thing to use: "i dont know what to do with myself" is a person stuck and
    # wants comfort, and "what do i do with him" is about a relationship. Both read as steps or as
    # a pick off the words alone, and either reading scores a good comfort reply a miss.
    if DO_WITH_A_PERSON.search(said):
        return None
    if asking and (WHAT_CAN_I_DO_WITH.search(said) or WHAT_SHOULD_I_DO_WITH.search(said)):
        # Two named sides are the ask whatever the words around them: "what can i do with tea or
        # coffee" is a pick, and the "do with" of it is not a method.
        if asks & PICK_SIDES:
            return PICK
        # "what can i do with it" is what is open to them, a set of ideas; "what should i do with
        # it" and "what do i do with it" are the doing, which is the steps. The modal is the
        # difference, not the thing named: anything goes wrong with mince and anything goes wrong
        # with 3k, and the two asks are still different shapes.
        if WHAT_SHOULD_I_DO_WITH.search(said):
            return STEPS
        return OPTIONS
    # The use-up ask in its "else" form: "what else can i do with leftover rice", "what else can i
    # make with mince", "what else can i do with a glut of courgettes". The person already knows one
    # thing to do with it and wants a few more, so the answer owed is a handful of ideas, not one
    # pick. `PICK_ONE` misses it (the "else" is not one of its openings) and `PICK_ONE_OF_A_KIND`
    # excludes "what else" by design, so those turns asked for nothing at all: every answer passed
    # unseen, a punt as easily as the good ones.
    if WHAT_ELSE_WITH.search(said):
        return OPTIONS
    if WHAT_ELSE_STEPS.search(said):
        return STEPS
    if (PICK_ONE.search(said) or PICK_ONE_OF_A_KIND.search(said)
            or (WHAT_TO_OPENS.search(said) and WHAT_TO_PICK.search(said))):
        return None if HAVE_RECALL.match(said) else PICK
    # "what can i use instead of mince" wants the substitutes, which is a few ideas and not a
    # method, so the instead is read before the steps below.
    if SUBSTITUTE.search(said):
        return OPTIONS
    # Asked what to do, say or try, the person wants the steps, whatever `asks` says: understanding
    # reads the `what should i do` spelling as steps and the rest as a bare `what`. A question
    # somebody else asked, told to the bot, is a report and owes no shape of its own; a job is not
    # a method; and a line that opens on another question word is that question first.
    # A thing held up against another is answered by a few things to go with it, and this is read
    # before the method arms: "what should we name the boat" is not something to do, and the
    # method read has already taken "what should i name" as a set of steps before the pick arm.
    if PAIRING_ASK.search(said) and not REPORTED.search(said):
        return OPTIONS
    if ((WHAT_TO_DO.search(said)
         or (WHAT_TO_OPENS.search(said) and WHAT_TO_STEPS.search(said)))
            and not REPORTED.search(said) and not NOT_STEPS.search(said)
            and not OTHER_QUESTION.match(said)):
        return STEPS
    # A cause asked without the word why wants the reason, and understanding carries `why` only
    # for the word itself: "what causes colic", "what makes thunder", "how come my kettle furs up".
    # A statement about a reason ("work is the reason theyre cutting hours") and a cause somebody
    # else was reported to have asked are not questions here.
    if asking and not REPORTED.search(said) and REASON_ASK.search(said):
        return REASON
    # The point of a named thing is the reason it is worth doing, and nothing else answers it:
    # "whats the point of a warm up", "any point in solar panels". A fragment carries no question
    # word of its own, so this is read without the `asking` test above.
    found = POINT_ASK.search(said)
    if found and not ASKS_ITS_OWN_YES_NO.search(said):
        thing = (found.group(1) or found.group(2) or "").split()
        if thing and thing[0] not in POINT_NOT_A_THING:
            return REASON
    # "worth a go i suppose" carries the "worth" of a recommendation but asks nothing: a line
    # that names no question and does not open on one is a remark, and owes no shape. Neither does
    # a remark that only holds the words of a measure ("no idea how much it costs"). A remark that
    # *closes* by asking whether it is ok or normal is not one: "i only have plain flour is that
    # ok" asks the question in its last three words, which is `TAIL_VERDICT_ASK` read at the end.
    if (asks <= ({"recommend"} | MEASURE_LABELS) and not said.rstrip().endswith("?")
            and not ASKS_OUT_LOUD.match(said)
            and not TAIL_VERDICT_ASK.search(_whole(understood))):
        return None
    # What the difference between two things is wants the two of them explained, not a side taken:
    # "what is the difference between leasehold and freehold" is the pair of definitions, and a
    # pick would be answering something else.
    if DIFFERENCE.search(said):
        return MEANING
    # Two named sides are a pick whatever else the line asks; a yes/no with no second side is a
    # verdict even when understanding also reads the "worth it" as a recommendation.
    if asks & PICK_SIDES:
        return PICK
    # A count of steps is a distance or a number of them, not a method: the word is the unit, so
    # the shape is whatever else the line asks (a verdict for "is 10000 steps a day enough", the
    # figure for "10000 steps in miles", nothing at all for "i did 12000 steps today").
    if STEPS_ARE_COUNTED.search(said) or STEPS_AS_A_DISTANCE.search(said):
        asks.discard("steps")
        if STEPS_AS_A_DISTANCE.search(said):
            return AMOUNT
    # A price asked as an adjective on the thing wants the figure, not a verdict: the reply people
    # get for "is paris expensive" is "about 65 to 110 pounds a day", and a yes/no check reads that
    # as an answer in the wrong shape. The comparison and the value questions are read above.
    # The question after the price is read on the line itself, not on `said`: `_said` repeats the
    # line for each of its spellings, so "is it expensive" comes back as "expensive is it" and the
    # repeat looks like a second question.
    if (PRICE_ADJECTIVE.search(said) and not PRICE_ADJECTIVE_KEEPS.search(said)
            and not PRICE_ADJECTIVE_THE_ASK_IS_LATER.search(_line_text(understood.get("text")))
            and not asks & PRICE_ADJECTIVE_WHY):
        return AMOUNT
    # A yes/no is the weakest reading in the list: understanding labels it on every line that
    # opens on an auxiliary, so "how long do i boil an egg" comes in as `how_long` and `yesno` and
    # "how much should i be saving a month" as `how_much` and `yesno`. The question word is the
    # question; the auxiliary is only the grammar. So a how-long, a how-much, a where, a who, a
    # why, a definition, a list, a steps or a how wins, and a bare yes/no is read only when there
    # is no ask of its own beside it. "is it worth it" keeps its verdict, because `recommend`
    # alone is not one of those asks.
    # The price word is what the why is about, so the cause is the answer: "why is it so
    # expensive to fix a boiler" asks why the fix costs, and `A_PRICE_ASK` below reads the
    # adjective as a request for the figure and answers it with a number.
    if PRICE_ADJECTIVE.search(said) and asks & PRICE_ADJECTIVE_WHY:
        return REASON
    # "is that expensive" wants the price, not a yes: see `A_PRICE_ASK`.
    if A_PRICE_ASK.search(said) and not NOT_A_PRICE_ASK.search(said):
        return AMOUNT
    # "can you remind me what i said first" is the same recall as "what did i say first", which
    # reads as no shape at all; the "can you" only made it polite, and the yes/no it produced named
    # the bot's own quote of their words a miss. Only the yes/no label is dropped: a recall that
    # names a figure - "what did i say the repair cost" - keeps its amount.
    if RECALL_OF_MINE.search(said):
        asks.discard("yesno")
    if "yesno" in asks and not (asks & SPECIFIC_ASKS):
        return YESNO
    # "what does a bathroom cost", "whats the price of a pint": the asks say what the thing is,
    # and the line asks what it costs, so the figure is the answer it wants.
    if COST_ASK.search(said) and asks <= COST_STANDS_IN:
        return AMOUNT
    # A money verb asked with "what" is the figure: "what should i be paying", "what should we
    # spend on a holiday", "what should i be earning". The `steps` label on these comes from the
    # bare "what should i" frame, not from a method, and a how-to is the answer to a different
    # question. Money already there being allocated ("what should i spend it on first") is a pick
    # and is kept out, as is a "how much", which reaches the amount above on its own.
    if A_FIGURE_OF_A_MONEY_VERB.search(said) and not MONEY_VERB_NOT_A_PRICE.search(said):
        return AMOUNT
    if WHAT_CAN_I_DO.search(said) and not asks & PICK_SIDES:
        return STEPS
    for shape, labels in ASKED_FOR:
        if (asks - (frozenset() if asking else MEASURE_LABELS)) & labels:
            # A plural ask-noun asks for a few, not one thing to take: "any tips for getting a
            # toddler to sleep", "any advice for a toddler who won't sleep", "suggestions for a
            # rainy day" arrive as a bare `recommend`, and a pick answers a different question
            # from the two or three the person asked for. One recommendation still gets a pick.
            if (shape == PICK and "recommend" in labels
                    and A_FEW_THINGS.search(said)):
                return OPTIONS
            # A figure in a statement is not an ask: "my shift starts at half 5" is when the
            # person works and "my phone is on 2 percent" is news. Only a question owes a sum,
            # unless the line is a sum said out loud ("split 120 between 4 people").
            if shape == AMOUNT and "maths" in asks and "how_much" not in asks and \
                    understood.get("kind") != "question" and \
                    not (SUM_OUT_LOUD.search(said) or SUM_ASKS.search(said)):
                continue
            return shape
    # A line that says what is in front of the person and then asks whether it is normal, ok or
    # a bad sign is a yes/no: "my temp is 38.5 is that bad", "leftover curry in the fridge is it
    # ok", "my baby poos 5 times a day is that normal", "i only have plain flour is that ok".
    # Read off the ask alone these came back with no shape at all - the question word is in the
    # closing clause and none of the arms above knows the tail - so no reply was ever checked
    # against them. 32 of the 126 deck lines shaped this way were None on main. The tail is the
    # ask only when it closes the line: a "is that ok" in the middle is a setting clause the rest
    # of the sentence answers ("i dont know if that is fine, but the paint is peeling"), which is
    # why this reads `_whole` and not `_said`: `_said` joins the line's `clean` and `text` and so
    # hands back the line twice, and nothing anchored to the end of it can ever match.
    if TAIL_VERDICT_ASK.search(_whole(understood)):
        return YESNO
    return None


# A line that describes a situation and then asks whether it is normal, ok or a bad sign: the
# question is in the closing clause, and `wants` read nothing from it. The adjectives are the ones
# a person actually asks with - "is that normal", "is it ok", "is it worth it", "is that a good
# idea" - and the clause has to end the line, because the same words mid-sentence ("i dont know if
# that is fine, but...") are the setting, not the ask.
TAIL_VERDICT_ASK = re.compile(
    r"\b(?:is|was|are)\s+(?:it|that|this)\s+(?:worth it|worth|ok|okay|fine|right|normal|bad|"
    r"a good (?:idea|plan|buy|choice))[\s.?!]*$", re.I)


# "or" is the mark of a choice offered: two things, take one. A list joined by commas and "and"
# is one plan ("a film, a walk and a call, then tea"), and a colon then a clause is not a choice.
# An answer to a yes or a no rarely opens with yes or no. It says why ("Tea has enough caffeine to
# keep you awake, so after 2pm is too late"), what the thing is, or the figure the yes depended on,
# and every one of those is the answer the person was waiting for. Read without the line, a cause,
# a definition or a figure is evidence about the reply rather than a verdict on it - "Two years'
# service is the line" carries a figure, "Because the seal has gone" carries a cause - so this
# reading is only ever made where the line is known to have asked whether.
#
# It is not made for a reply that tells the person what to do. A method can carry a time or a
# figure as easily as a verdict can, and then the figure belongs to the how-to: "Sort by colour,
# not by kind of garment: dark cottons together on 40" is no answer to "should i run a hot wash
# with vinegar", and "Sow basil indoors from late April" is no answer to "is that ok for the
# plant". Any verb at the front says the reply is a method, not only the ones this file lists, so
# the word after the first is read: a subject there carries a verb with an -s on it ("It varies",
# "Caffeine lasts", "A scrum restarts") and an object does not ("Sow basil", "Sort by colour").
NOT_A_VERB_HEAD = re.compile(
    r"^(?:a|an|the|it|it's|its|there|this|that|these|those|they|them|we|you|i|he|she|both|all|"
    r"some|most|many|one|two|three|four|five|six|seven|eight|nine|ten|from|in|at|on|for|to|with|"
    r"without|after|before|about|around|once|if|when|until|roughly|up|down|by|as|of|no|not|"
    r"nothing|nobody|never|always|usually|often|your|my|our|his|her|their|every|each|another|"
    r"any|much|little|few|several|such|what|who)\b", re.I)


# A reply that offers to do the thing is an answer to "can you", whatever it opens on.
I_OFFER = re.compile(
    r"\b(?:i'll|i will|i can|i'd|we'll|we can|let me|i've|i would)\b", re.I)

# The offer is an answer to a line that asks the bot to do something, and to almost nothing else:
# "I can work things out - sums, plans" is the bot describing itself, "I'd do a bean stew" is a
# recipe, and "I would start here" is advice. 43 of 297 deck replies carry one of those phrases,
# so an ungated offer arm says yes to a seventh of the deck.
ASKS_THE_BOT = re.compile(r"\b(?:can|could|would|will)\s+(?:you|u)\b|\bdo you\b|\bare you\b", re.I)


# A bare count is not the figure a yes rested on: "Two different claims" opens on a number and
# says nothing about how much of anything. The figure that answers a yes or a no carries its unit:
# "60 to 80mg", "78 calories", "three hours", "6 to 7p a unit".
A_UNIT = re.compile(
    r"\d|\b(?:mg|g|kg|ml|l|litres?|liters?|cm|mm|metres?|meters?|feet|foot|inches?|degrees?|c|f|"
    r"hours?|hrs?|minutes?|mins?|seconds?|days?|weeks?|months?|years?|nights?|p|pence|pounds?|"
    r"quid|grams?|calories|kcal|watts?|kw|kwh|amps?|volts?|per\s+cent|%)\b", re.I)


def _an_amount_with_a_unit(opening):
    return bool(_an_amount(opening)) and bool(A_UNIT.search(opening))


# A reply whose subject is a pronoun is about what was just said, so the thing can be named
# anywhere in it: "is coffee keeping me awake" / "It varies with the drink: a mug of instant
# coffee is 60 to 80mg". Any other opening names its own subject first, and that is what the
# reply is about.
POINTS_BACK = re.compile(r"^(?:it|it's|this|that|these|those|they|them|there|its)\b", re.I)

# Words that name nothing: "the" alone made every reply about the line's thing, because an
# opening sentence nearly always has one. "tea", "vet", "dog" and "cat" name things and stay in.
# The four- and five-letter ones are here for the same reason as "the": "with" and "from" in a line
# match a comparison reply as readily as a name does, and "that" and "this" are in every other
# opening.
NOT_A_THING = frozenset((
    "the", "and", "for", "you", "not", "but", "all", "any", "one", "two", "are", "was", "has",
    "had", "how", "why", "who", "did", "may", "can", "its", "our", "per", "via", "yet", "own",
    "off", "out", "too", "get", "put", "use", "let", "now", "far", "lot", "bit", "way", "she",
    "him", "her", "his", "new", "old", "few", "yes", "them", "they", "their", "there", "then",
    "that", "this", "with", "from", "your", "have", "what", "when", "will", "would", "could",
    "should", "about", "into", "over", "just", "only", "even", "still", "much", "many", "some",
    "very", "also", "been", "being", "does", "done", "more", "most", "less", "like", "need",
    "want", "make", "made", "going", "were", "than", "such", "each", "both", "else", "said",
))


def _about_the_thing_the_line_named(opening, said):
    """True when the reply is about something the line named: provenance, not subject.

    A wide reading of a yes or a no - why, what the thing is, the figure the yes rested on, what
    to do about it - is worth nothing when the reply is about something else, and read without
    the line it says yes to nearly any fact-shaped reply: in a paired test "Two to three hours."
    was credited as the verdict for every yes/no line there is, and "Sort by colour, not by kind
    of garment" answered "should i run a hot wash with vinegar".

    The thing has to be named where the reply states its subject - the first five words - unless
    the reply points back with a pronoun ("It varies with the drink, ... 60 to 80mg") or tells the
    person what to do, where the object comes later ("Slice it first, then bag it: bread keeps
    three months" answers "can i freeze bread"). The figure the line asked about counts as well:
    "is 60mg enough" / "60 to 80mg is a mug of instant coffee".
    """
    words = _words(opening)
    wide = bool(POINTS_BACK.match(opening)) or _an_instruction(opening)
    head = set(words) if wide else set(words[:5])
    for word in set(_words(said)):
        if len(word) < 3 or word in _EMPTY or word in NOT_A_THING:
            continue
        if word in head:
            return True
        # A stem must be a word that names something: "add" cut to two is "ad" and then "a", and
        # "young" cut to three is "you", so the reply's own article or pronoun made it the thing
        # the line named. The plural and the participle keep their stem ("eggs" to "egg", "boiling"
        # to "boil"), which is what the stem is for.
        for stem in (word[:-1], word[:-2]):
            if len(stem) < 3 or stem in _EMPTY or stem in NOT_A_THING:
                continue
            if stem in head:
                return True
    return bool(set(re.findall(r"\d+", opening)) & set(re.findall(r"\d+", said)))


# A method opens on any of these, and a method is not a verdict. The list is kept out of
# `INSTRUCTS` because `_the_job_answers` reads that one as "this is the job the line asked
# about", where a wider list turned "Lower eggs into already boiling water" into the answer to
# "can my son eat grapes".
METHOD_VERBS = re.compile(
    r"^(?:lower|brown|mash|crush|sprinkle|grease|steam|blend|scatter|lay|shake|score|chill|thaw|"
    r"reheat|serve|strain|sieve|portion|layer|arrange|thread|screw|hammer|nail|clamp|level|"
    r"preheat|dust|wring|drape|tuck|loop|knot|peg|hoover|vacuum|mop|air|cure|rest)\b", re.I)


def _an_instruction(opening):
    """True when the reply tells the person to do something, which is not a verdict on its own."""
    if (INSTRUCTS.match(opening) or JOB.match(opening) or METHOD_VERBS.match(opening)
            or MEANS_OF.search(opening)):
        return True
    words = _words(opening)
    if len(words) < 2 or NOT_A_VERB_HEAD.match(opening):
        return False
    second = words[1]
    return not (second.endswith("s") and not second.endswith("ss"))


# An options ask: the set of things open to them. It is not the definition of a word, and a
# definition is what the bare "what" makes of the line. "what are my options, tea or coffee" is a
# pick and is left alone.
OPTIONS_ASK = re.compile(
    r"\b(?:what|wat|wot|wats)\s+(?:are|r)\s+(?:my|the|our|his|her|their)\s+"
    r"(?:other\s+|main\s+)?options?\b", re.I)
WHAT_CAN_I_DO = re.compile(r"\bwhat (?:can|could) (?:i|we) do\b", re.I)
# "what can i do with a bag of apples going soft", "what can i do with mince and a tin of
# tomatoes": the uses of what the person already has. It reads as a pick because the labels say
# pick and the thing is left open, but a pick is a choice of two, so one idea credited it and a
# menu of ideas did not say which of them to take.
WHAT_CAN_I_DO_WITH = re.compile(r"\bwhat (?:(?:can|could) (?:i|we)|to) do with\b", re.I)
# ...and the same thing asked as the doing: "what should i do with 3k saved", "what do i do with a
# chicken carcass". The modal is the difference between being open to them and being the method.
WHAT_SHOULD_I_DO_WITH = re.compile(
    r"\bwhat (?:should|shall|do|did|would|might) (?:i|we) do with\b", re.I)
# Every spelling of the same ask, for the reading of a reply: "i dont know what to do with the
# kids", "no idea what to do with 3k". The set of things to do with a thing, and the one worked
# out in steps, are both answers to it.
ANY_DO_WITH = re.compile(r"\bwhat (?:to|(?:can|could|should|shall|do|did) (?:i|we)) do with\b", re.I)
# ...but the thing after "with" has to be a thing. "i dont know what to do with myself" is a
# person stuck, not a thing to use, and it is answered by comfort; the same for "what do i do with
# him". A pronoun for a person is not a thing, so the do-with arms stand down on it.
DO_WITH_A_PERSON = re.compile(
    r"\b(?:do|does|doing) with (?:myself|yourself|himself|herself|ourselves|yourselves|"
    r"themselves|him|her|each other)\b", re.I)


def _do_with_ask(said):
    """True when the line asks what to do with something, however it spells the ask."""
    return bool(ANY_DO_WITH.search(said))

CHOICE = re.compile(r"\bor\b", re.I)

# A line that asks for the words to use, not for the thing they are about: "how do i tell my
# flatmate to do the dishes", "what should i say to my landlord", "i dont know how to tell her".
# Nothing here is about the dishes or the landlord; the answer wanted is a sentence to say.
WORDS_ASK = re.compile(
    r"\bhow (?:do|can|could|should|would) (?:i|we|you) "
    r"(?:tell|say|ask|word|phrase|put it|bring (?:it|this|that) up|raise (?:it|this|that)|mention|approach)\b"
    r"|\bhow to (?:tell|say|ask|word|phrase|bring (?:it|this|that) up|raise (?:it|this|that))\b"
    r"|\bwhat (?:should|shall|do|can|could|would) (?:i|we) "
    r"(?:say|tell|text|write|ask|reply|answer|word it|phrase it)\b"
    r"|\bwhat to (?:say|tell)\b|\bwhat should be said\b"
    r"|\b(?:dont|don't|do not|didnt|didn't|never|no idea) (?:know )?(?:quite |really )?"
    r"(?:how|what) to (?:say|tell|word|phrase|ask)\b"
    r"|\b(?:idk|dunno|no idea) (?:how|what) to (?:say|tell|word|phrase|ask)\b"
    r"|\bhow (?:should|do) i (?:break|ease) it to\b|\bbreak it to\b"
    r"|\b(?:cant|cannot|can't|dont|don't|struggling to) (?:find|think of) (?:the )?(?:right |proper )?words\b"
    # Naming the words wanted is the ask itself, whoever is doing the finding: "can you help me
    # find the right words to tell my dad" is the sentence, not the thing it is about.
    r"|\b(?:find|finding|choose|need|want) (?:the |some )?(?:right |proper |good )?words\b"
    r"|\bwords to (?:say|tell|use)\b|\bhelp me (?:word|phrase|put it)\b",
    re.I)
# A line that asks how to tell one thing from another, or whether a thing is done, is a question
# about the thing whatever else it says: "how do i tell if the potatoes are cooked" wants a knife
# through the potato. Kept apart from the rest of `NOT_WORDS_ASK` because a line that names the
# words ("words to say to my boss about leaving early") is a request for the sentence even when
# a person and a topic follow it, and still not one when the telling in it is a test.
TELLS_A_TEST = re.compile(
    r"\b(?:tell|saying) (?:if|whether|when|apart|the difference|which|how|what|why|where|who)\b"
    r"|\btell me\b|\btell us\b|\btell (?:you|ya)\b"
    # "tell a fracture from a sprain" is a test, and "tell the dog off" is to scold it, not to say
    # anything to it. A bare "how do i tell" with nothing after it asks how to know.
    r"|\btell (?:\w+ ){0,4}\bfrom\b|\btell (?:\w+ ){0,3}\boff\b"
    r"|\btell (?:\w+ ){0,2}\bapart\b"
    r"|\bhow (?:do|can|could|would) (?:i|we|you) tell\s*[?.!]*$"
    # Asking for a thing is a request to the world, not a sentence to say: "how do i ask for a
    # pay rise" wants the case to make, and the ask is named in it rather than somebody asked.
    r"|\bhow (?:do|can|could|should|would) (?:i|we|you) ask (?:for|about)\b", re.I)

# Asking how to tell whether a thing is done, or the difference between two, is a question about
# the thing, and the answer is the test rather than a sentence: "how do i tell if the potatoes
# are cooked" wants a knife through the potato. "Tell me about X" is a fact question too, and a
# translation is the phrase itself, not a way of saying it.
# The arms that hold however the line is put, including when it names the words: a phrase in
# another language is the phrase, not a way of saying it, and "break the ice" is an idiom.
NOT_WORDS_ANYWAY = re.compile(
    r"\b(?:in|into) (?:french|spanish|italian|german|welsh|irish|gaelic|japanese|chinese|portuguese|"
    r"dutch|polish|russian|arabic|hindi|greek|turkish|latin)\b"
    r"|\bbreak (?:the ice|a habit|the bank|a record)\b", re.I)
# A form is filled in and a box is ticked: nobody is being spoken to. "what do i write on a
# customs form" wants the words the form asks for - the value, the description, the country of
# origin - and a card's two lines are a sentence to a person, which is the wrong thing entirely.
# Only the writing verbs are held back, because a form is still something to talk to a person
# about ("how do i tell my boss about the expenses form" is in the person-then-topic arm).
WRITES_A_FORM = re.compile(
    r"\b(?:writ(?:e|ing)|fill(?:ed)? in) (?:(?:\w+) ){0,4}"
    r"(?:form|forms|declaration|customs|invoice|receipt|application|claim\b|return\b|"
    r"questionnaire|box|boxes|field)\b", re.I)
# Writing into a document is not saying something to somebody: the answer to "what should i write
# in my cv" is what goes on the page, and it was answered with a greeting card's two lines because
# the writing in it read as the ask. A card, a letter or a message is addressed to a person and is
# still the words ("what do i write in a card for my husband"), and a cover letter is a document
# however it is addressed, so the message word has to be missing or be the cover letter's own.
WRITES_IN_A_DOCUMENT = re.compile(
    r"\bwrit(?:e|ing|ten)\b[^.!?]{0,30}\b(?:cv|curriculum vitae|cover(?:ing)? letter|journal|diary"
    r"|essay|report|thesis|dissertation|blog|article|minutes|form|declaration|invoice|receipt"
    r"|application|claim|questionnaire|statement|record)\b", re.I)
WRITES_TO_A_MESSAGE = re.compile(
    r"\b(?:card|letter|note|message|e-?mail|text|reply|comment|speech|toast|eulogy"
    r"|announcement|invitation|post)\b", re.I)
A_COVER_LETTER = re.compile(r"\bcover(?:ing)? letter\b", re.I)
# "what should i write" with nothing after it names no person and no document, so there is nothing
# for a sentence to be said to or written in, and the writing card is a better guess than a card.
BARE_WRITE = re.compile(
    r"\bwhat (?:should|shall|do|can|could|would) (?:i|we) write\s*[?.!]*$"
    # "what should i write next" and "what should i write about" name no reader either: the ask is
    # for a subject to write on, which the writing card answers and a card to a person does not.
    r"|\bwrite (?:about|next|something|anything|more)\b", re.I)
NOT_WORDS_ASK = re.compile(
    TELLS_A_TEST.pattern + "|" + NOT_WORDS_ANYWAY.pattern + "|" + WRITES_A_FORM.pattern + "|"
    + BARE_WRITE.pattern + "|" +
    # A person and then a topic after the telling verb is the topic's question, not a request for
    # words: "i dont know how to tell my mum about the move" wants the move, and answering it with
    # how to break a move to the children left the moving card's own answer behind. "Say about" on
    # its own is not this - "what should i say about the gap in my cv" is the words for the gap.
    r"\b(?:tell|talk to|speak to|say to) (?:\w+ ){1,3}about\b", re.I)


# The words named as a thing to hand over - "words to say to my flatmate", "give me the words"
# - are the ask itself, whatever comes after them. The person-then-topic arm below is there for
# "how do i tell my mum about the move", where the move is the question; here the sentence is,
# and "words to say to my boss about leaving early" is a request for the sentence rather than
# for the notice and the tenancy letter the topic words reached on main.
NAMED_WORDS = re.compile(
    r"\bwords to (?:say|use|tell)\b|\bwords for (?:telling|saying|asking)\b"
    r"|\b(?:give|send|hand) (?:me )?(?:the )?words\b"
    r"|\bfind (?:me )?(?:the )?(?:right |proper )?words\b"
    r"|\bput (?:it|this) in(?:to)? words\b|\bhelp me (?:word|phrase|put it)\b", re.I)


def asks_for_words(understood):
    """True when the line asks what to say, rather than what to do about the thing in it.

    The shape of answer is the words themselves, so a card that answers the thing named - how to
    wash up for "how do i tell my flatmate to do the dishes", what bad breath is for "how do i
    tell my friend her breath smells" - is on the right topic and answers a question nobody
    asked. Read from the whole line, and only from an ask: "she said i was rude and i dont know
    what to say" is the same ask, and "how do i tell if the steak is done" is not one at all.
    """
    if not isinstance(understood, dict):
        return False
    said = str(understood.get("plain") or "").strip().lower() or _said(understood)
    if not said or not WORDS_ASK.search(said):
        return False
    if NAMED_WORDS.search(said):
        # A diagnosis or a translation is still not a request for words, even named: "words to
        # tell whether the potatoes are cooked" asks what the test is.
        return not (TELLS_A_TEST.search(said) or NOT_WORDS_ANYWAY.search(said))
    if not understood.get("subject") and understood.get("followup"):
        # "what can i say to her" names nobody and nothing, so it leans on the last turn, and the
        # cards that answer with words are written without knowing what they are about: the
        # subject's own answer is the one that can be right, and the reply says where to start.
        return False
    if WRITES_IN_A_DOCUMENT.search(said) and not (
            WRITES_TO_A_MESSAGE.search(said) and not A_COVER_LETTER.search(said)):
        return False
    return not NOT_WORDS_ASK.search(said)


def gives(reply, want, line=None):
    """True when `reply` gives an answer of kind `want`, False when the check can name what is
    wrong with it, None when words cannot tell.

    A question put back to the person is never an answer, whatever shape the check read out of it:
    see `is_a_question_back`. That test is applied to the credit and not to the whole reply, so it
    can only take a credit away. A reply the cues cannot read stays the "words cannot tell" it was,
    because the check only calls a reply a miss when it can name what the reply is instead, and a
    reply it cannot read is not named.
    """
    answer = _the_shape_a_reply_gives(reply, want, line)
    if answer is True and is_a_question_back(reply, line):
        return False
    return answer


def _the_shape_a_reply_gives(reply, want, line=None):
    """The check itself: the shapes a reply's opening carries, and what it is instead.

    Everything the docstring of `gives` says about a true, a false and a "words cannot tell" is
    about this function.

    Only the opening sentence is read, because STYLE.md asks for the answer in the first sentence
    and a figure buried in the third paragraph of a paragraph about something else is not the
    reply the person got. A method is the one shape read a sentence further, because its opening
    is often the reason: "Sticking is nearly always a wet dough meeting a dry surface. Chill the
    pastry 20 to 30 minutes before rolling." A want this module does not know, or one of the soft
    shapes, is None.

    False is a claim about the reply, so the check only makes it when it can say what the reply
    is instead: a shrug, or an unmistakable other shape - a duration, a figure, a method, a
    named kind of place, a role, what the thing is, a verdict or a named side. A reply in words
    the cue list has nothing for is None, not a miss: "Vinegar does not go off" is the answer to
    "does vinegar go off", and "Granita is fruit juice or coffee" is the answer to "what is
    granita", and neither carries a cue this module knows.
    """
    if want not in WANTS or want in SOFT:
        return None
    # The line comes as the person's own words, and as the reading of them: the tests here hold a
    # reply against what `understand` made of the line, which is how the arms that need the line
    # were written and checked. Reading a dict as text made every one of those arms dead - the
    # pair-up arm never fired on "is a bath better than a shower" - so the two are the same thing
    # here, once, for every arm.
    if isinstance(line, dict):
        line = line.get("text") or line.get("clean") or line.get("plain") or ""
    opening = first_sentence(reply)
    if not opening:
        return None
    # A reply that says the same thing again puts a lead in front of the answer: the memory store
    # repeats the card as "Same answer, and it covers this: Cooked mince keeps 3 days in the fridge
    # ... freezes for 2 to 3 months", and the lead is a frame, not the shape of what follows. The
    # words behind it are the sentence the person read the first time, so they are read here.
    # Only the yes/no reading follows the lead: a repeated figure is not a pick, and "Same as
    # before: About 40 minutes start to finish" is the pick check's known false pass.
    repeat = REPEAT_LEAD.match(opening) if want == YESNO else None
    if repeat and opening[repeat.end():].strip():
        opening = opening[repeat.end():].strip()
        # The card behind the lead is what the person already read, so an instruction in it is a
        # method rather than the yes to this line: "is 95 too much" / "Same answer, and it covers
        # this: Stand them up and feel for a thumb's width ..." is not an answer about the price.
        repeated = True
    else:
        repeated = False
    # "That's beyond what I know" is not a figure, a place or a method, whatever words follow it.
    # But a punt that then names the source holding the answer has done the whole job: a question
    # about the person's own bill, forecast, tracking or bin day has no answer but that one, and
    # "I can't see the tracking from here - the confirmation email has it" was scored a miss for
    # the shape it could not carry. The source is read over the reply rather than the opening,
    # because the punt takes the opening: PUNT is the first claim, the source is the second.
    if is_a_punt(opening):
        head = reply[:400] or ""
        return None if (DIRECTED.search(head) or A_HOLDER.search(head)) else False
    # A sign-off answers no question: see `_a_sign_off`. It is a miss for a yes/no line because the
    # person asked whether and got a warm goodbye, and it is checked before the cue lists, which
    # read "No rush." as a "no" and "Nice one." as a job ("Nice" + a thing).
    if want == YESNO and _a_sign_off(opening):
        # A miss only when the line asked for a verdict: a warm reply is right for a line that was
        # a goodbye or a thank you ("have a good day at work" / "Cheers. Hope it goes well for you
        # too."), which `wants` reads as yes/no by its shape.
        return None if _A_SOCIAL_OPEN.match(_line_text(line) or "") else False
    check = _CHECKS.get(want)
    # A price per hour is not a length: "A dehumidifier is about 7p an hour, and it dries a room by
    # running longer rather than hotter" answered how much, and reading "an hour" out of it credited
    # it as a how-long. The rate phrase is taken off and the time check runs again on what is left,
    # so "£12 an hour, and it takes an hour to warm up" is still a time.
    if want == TIME and _a_money_rate(opening):
        stripped = _without_a_money_rate(opening)
        if stripped != opening:
            return bool(_a_time(stripped))
    if want == STEPS:
        # A method is the one shape the whole reply gives: see `_steps_in`.
        if _steps_in(reply):
            return True
        # The verb a how-to opens on need not be on any list: `IMPERATIVE` reads the shape of an
        # instruction - a verb, then the thing it acts on - and "Name the thing they do that nobody
        # remarks on", "Work down the page one row at a time" are methods the word lists missed
        # while the shape test already knew them. Only a steps-ask reads this, so no other shape
        # can lift a verdict or a figure out of the same reply, and a noun-led statement cannot
        # pass it: "Signal bars drop" and "Rain water in a butt" have a noun second, not a
        # determiner or a pronoun.
        if _imperative(opening):
            return True
    elif want == TIME and line and (STAGE_WHEN.search(opening) or SEASON_WHEN.search(opening)) \
            and ASKS_WHEN.search(_line_text(line)):
        # A when is answered by the stage the thing has to be at: "when should i feed the tomatoes"
        # is told "Start feeding when the first truss of flowers has set fruit". Only a line that
        # asks when reads it this way, because the stage is not a length: "how long can i keep ice
        # in the freezer" was told "Defrost it when the ice is more than about 5mm thick", which
        # is an answer about defrosting the freezer and not about the ice.
        return True
    elif want == REASON:
        # The one check that reads the line as well as the reply: see `_a_reason`. It reads the
        # second sentence too, because a why-answer is told as what happened and then what it was:
        # "why do we have bonfire night" / "In 1605 a group of English Catholics planned to blow up
        # Parliament. The plot was discovered on 5 November, which is why Britain still has bonfire
        # night", "why is my hot water cold" / "Start at the programmer: it is usually on a timer
        # that has slipped. A combi with no hot water but working heating is usually a stuck
        # diverter valve". The cause is in the clause that carries it, wherever the reply puts it.
        if _a_reason(opening, line):
            return True
        # The wider read has to be about the thing the line named, or a "because" anywhere in the
        # second sentence credits any why-line at all: a "why" on its own was answered by "Put a
        # couple of nights away in the middle of the week and keep the fire in", and 5 of the 6
        # credits the unguarded read bought on 3,000 mismatched pairs were that kind of line.
        if line and _names(_opening_two(reply), _line_text(line)) \
                and _a_reason(_opening_two(reply), line):
            return True
    elif want == YESNO:
        # The yes/no check reads the line too, for its two quality arms: see `_a_yesno`.
        if _the_rule_settles_it(opening, line, reply):
            return True
        if _a_yesno(opening, line):
            return True
    elif want == AMOUNT and line and ASKS_AN_AGE.search(_line_text(line)):
        # An age asked for is an age given: see `_an_age_is_given`.
        if _an_age_is_given(opening):
            return True
    elif check and check(opening):
        # A duration is not the money that was asked for. "how much does a new washing machine
        # cost" was answered "Over ten years.", and the answer passed because an amount is any
        # figure: the person still has no price. Only the reply that opens on a time and never
        # names money is failed, so a quantity line keeps every figure it had.
        if (want == AMOUNT and line and _a_price_asked(line)
                and _a_time(opening) and not PRICE_GIVEN.search(opening)):
            return False
        return True
    # The time is often in the sentence after a sentence of framing, and the person still gets
    # their time: "how long does milk last after you open it" was told "If milk smells or tastes
    # sour, bin it, whatever the date says. Once opened, keep milk in the fridge and use it within
    # about 5 days", and "when do puppies stop chewing" was told the redirect first and "Puppies
    # usually grow out of it by seven or eight months" second. Only a how-long or a when reads a
    # sentence on, only a length or a clock or a stage counts there (a range of prices or a "does
    # not go off at all" is the answer to some other question in the sentence after), and never
    # past a sentence that answers with nothing: a punt has already been read out above.
    elif want == TIME and _a_time_a_sentence_on(reply):
        return True
    # An offer to do it is the yes: "Paste the words you want to send and I'll soften them" answers
    # "can you make it shorter".
    if want == YESNO and line and ASKS_THE_BOT.search(_line_text(line)):
        # An offer answers "can you" only when it is about the thing the line asked for:
        # "can you make it shorter" / "I'll soften them" is an answer, "could you add my shift on
        # friday to my calendar" / "I would start here: get a quote" is not.
        if I_OFFER.search(opening) and _about_the_thing_the_line_named(
                opening, _line_text(line)):
            return True
    # The wide read of a yes or a no - the reply says why, what the thing is, the figure the yes
    # rested on, or what to do about it - is only worth anything when it is about the thing the
    # line named. Read without the line it says yes to nearly any fact-shaped reply: "Two to three
    # hours." was credited as the verdict for every yes/no line in a paired test, and "Sort by
    # colour, not by kind of garment" for "should i run a hot wash with vinegar". Nor when the line
    # is the person's own doing and the outcome is what they asked about: "if i set off at 5 will i
    # miss my flight" is not answered by "Leave for the airport three hours before the flight".
    if (want == YESNO and line and not _an_outcome_of_their_own_doing(_line_text(line))
            and _about_the_thing_the_line_named(opening, _line_text(line))):
        if (_a_meaning(opening) or _a_reason(opening) or _a_time(opening)
                or _an_amount_with_a_unit(opening)):
            return True
    # The job the person asked whether to do is the yes, and only ever the yes: it is checked
    # before the clear shapes so a method that answers the line is not read as a method instead.
    # Anything this cannot read falls through to the clear shapes and then to None, so a reply
    # main called "words cannot tell" is not turned into a miss by knowing the line.
    if want == YESNO and line and _the_quality_it_was_asked_about(
            opening, _line_text(line)):
        return True
    if want == YESNO and not repeated and _the_job_answers(opening, line):
        return True
    # The verdict in the sentence after the thing it is about: "is jaundice dangerous" / "Yellow
    # skin ... is jaundice ... See a GP today, not next week - it can be the liver". The person
    # asked whether it is serious, and being told to get it looked at today is the yes. Only the
    # opening is read everywhere else, and this is the one reading followed into the rest of the
    # reply, because "get it checked" is how advice opens once it has said what the thing is.
    if (want == YESNO and not repeated and line and ASKS_IF_SERIOUS.search(_line_text(line))
            and SEEKS_HELP.search(reply)):
        return True
    if want == YESNO and line and _the_thing_is_named_as_what_it_usually_is(opening, line):
        return True
    # A verdict said about the thing rather than as the words yes or no: "is brown bread better
    # than white" / "Wholemeal is the better everyday loaf", "is cycling bad for knees" / "Cycling
    # is one of the kinder things for knees". The words that carry the verdict are not the opening
    # ones, so this reads the whole opening - and only beside the line, because those words credit
    # a reply to a completely different line as readily as the right one: 11 real turns and 11
    # wrong pairings on 755 yes/no turns. The reply naming something the line named is what tells
    # them apart (6 real, 2 wrong), and what it leaves unread stays the "words cannot tell" it was.
    if (want == YESNO and line and VERDICT_ABOUT_IT.search(opening)
            and _names_what_the_line_named(opening, _line_text(line))):
        return True
    # A verdict can be the rule in the sentence after the thing it is about: "can i get a bus pass
    # if im disabled" / "A disabled person's bus pass is a council scheme ... You qualify if ...".
    # Only this reading is followed into the rest of the reply, and only for its own phrase list.
    if want == YESNO and VERDICT_RULE.search(reply):
        return True
    # The same yes/no said about the line's own thing with the no inside it: "Tea does not go off",
    # "Conjunctivitis is not a reason to stay away", "so don't eat it".
    if want == YESNO and _says_no_about_the_asked_thing(opening, line):
        return True
    # "is wholemeal better than white" is a yes/no with a pair in it, and it is answered by
    # picking one: "Wholemeal is the better everyday loaf", "Showering wins on time and water",
    # "iPhone if you want the long updates". Only a line that puts two things up reaches this.
    if want == YESNO and line and _the_side_wins(opening, line):
        return True
    # The no said as the line's own verb denied: "does vinegar go off" / "Vinegar does not go off".
    if want == YESNO and _an_echoed_no(opening, line):
        return True
    # A yes/no about a quantity names no thing for a reply to be about, so the reading above cannot
    # reach it: "is that enough", "is that too far", "is 18 hours too much for a cat" are about a
    # figure from earlier in the chat. What answers them is the person's own figure set against the
    # standard: "15 minutes is short of the 20 minutes that answer named", "2 sessions a week is
    # under the three or four sessions a week that answer named - one more would put you there".
    if (want == YESNO and line
            and _the_figure_against_the_standard(opening, _line_text(line))):
        return True
    # The verdict in the sentence after the figure it rests on, which is where the bot puts it when
    # the sum is the answer's evidence: "20 miles each way is 25 minutes in the car. Doable in a
    # day if you leave early". The line is not needed: the figure and the judgement in the next
    # sentence are the reply to whatever the person asked whether, and a reply that only measures
    # has no judgement to find.
    if want == YESNO and _a_figure_then_the_verdict(opening, reply):
        return True
    # "How long is the Thames" asks how far it runs, not how many hours: the extent of a thing is
    # the length that was asked for, and a reply in kilometres, metres, pages or words answers it.
    # Read only when the line asked an extent, so a size is not read as a time for a duration ask
    # ("how long does rice take" answered "105 metres by 68 metres" is still a miss) and the same
    # reply read with no line at all is left as it was.
    if want == TIME and line and EXTENT.search(opening) and LENGTH_ASKED.search(_line_text(line)):
        return True
    # A pick may name one of the two sides the line offered: "should i get a cat or a dog" /
    # "A dog needs two walks a day". Only the words either side of the "or" are sides, and the
    # reply has to open on one.
    if want == PICK and line and _names_a_side(opening, _line_text(line)):
        return True
    # A pick is often given as an instruction that names the thing: "what shampoo should i use" /
    # "Use an anti-dandruff shampoo with zinc pyrithione or ketoconazole". The instruction is the
    # answer - it names what to use, it does not tell the person how to do a job - so the thing it
    # names is what settles it, and only for a pick.
    if want == PICK and line and _an_instruction(opening) and _names(opening, line):
        return True
    # An options ask can be answered with the one route to take, told as a step rather than as a
    # list: "failed mot what are my options" / "Ring the garage and book a retest", "what are my
    # options" / "Ring the council and ask for a care assessment". The set itself is what the
    # options check credits; this is the doing, and it only counts where the line really asks for
    # the options, so a single idea handed to "any ideas for dinner" is still a miss. Only the
    # verb-first instruction counts, because the looser read would credit any two-word fact.
    if want == OPTIONS and line:
        said = _line_text(line)
        if OPTIONS_ASK.search(said) and (INSTRUCTS.match(opening) or JOB.match(opening)):
            return True
    # A comparison is answered only when both things the line named are in it: "A sprain is a
    # stretched or torn ligament, a strain a torn muscle" compares them, and a reply that names one
    # of the two and never the other has answered half the question.
    both = _names_both_sides(reply, _line_text(line)) if want == COMPARE and line else None
    if both:
        return True
    # And when the missing side is a short name the reply may spell out ("hdd" as "a hard drive"),
    # nothing is claimed against the reply, whatever shape its opening happens to look like.
    if want == COMPARE and both is None:
        return None
    # A why is answered by naming the cause first and what to do about it after a colon: "One
    # channel going funny is the aerial or the box, and every channel is the set: push the aerial
    # lead in". The head of that sentence is the explanation, so the method behind the colon is
    # not a different shape - it is what the person does next. A head that only labels ("Quick:",
    # "Two things:") has no verb in it and is left to the readings below.
    if want == REASON and _head_explains(opening):
        return True
    # A definition names the thing first and then says what it is for: "what is a student loan" /
    # "A student loan pays the tuition fee and the maintenance money while you study". The reply
    # has said what the thing does, which is what the person asked, so it is not a miss for
    # opening on a verb `MEANS` does not list.
    if want == MEANING and line and _defines_the_thing(opening, _line_text(line)):
        return True
    # A definition told in the past tense, tied to the line the way `_defines_the_thing` is: "what
    # is a help to buy isa" / "A Help to Buy ISA was the first-home savings account that added 25%".
    # The shape alone is not a definition - every past-tense sentence with an article after the
    # copula has it ("The film was a mess, honestly", "It was a long day") - so the reply has to
    # name the thing the person asked about, which is what `_names_what_the_line_named` reads and
    # what the yes/no and reason readings already do with a wide pattern (steady-paper, PR 12040).
    if (want == MEANING and line and _a_past_definition(opening)
            and _names_what_the_line_named(opening, _line_text(line))):
        return True
    # Where a thing comes from is answered by naming the source and then what is done with it:
    # "Bees make it: a worker drinks nectar out of flowers", "One bush, Camellia sinensis: the
    # leaves are picked, then wilted", "The juice of sugar cane or of sugar beet, boiled down
    # until the sugar crystallises". The source is the head of the sentence, so the thing the
    # person asked about is often not named at all - which is why the shape readings miss it.
    # Only an origin question is read this way, and only for the head of the reply.
    if want == MEANING and line and (ORIGIN_ASK.search(_line_text(line))
                                    or MADE_OF.search(_line_text(line))) and _an_origin(opening):
        return True
    # An ideas ask is answered by the one idea the bot would take: "what's a good podcast about
    # history" - "*The Rest Is History* is the best all-round history podcast". A pick is what an
    # options ask wants when the reply names one, which ample-bag measured over the 258 deck lines
    # of "what's a good X". A pointer that names nothing is still not an idea ("Try the film you
    # have been meaning to watch" is a job for the person), and a colon list is left to `_options`
    # above, which knows a list of one plan ("One evening: a film, a walk and a call, then tea")
    # from a list of ideas.
    # An ideas ask is answered by the one idea the bot would take: "what's a good podcast about
    # history" - "*The Rest Is History* is the best all-round history podcast". A pick is what an
    # options ask wants when the reply names one, which ample-bag measured over the 258 deck lines
    # of "what's a good X". A pointer that names nothing is still not an idea ("Try the film you
    # have been meaning to watch" is a job for the person), and a colon list is left to `_options`
    # above, which knows a list of one plan ("One evening: a film, a walk and a call, then tea")
    # from a list of ideas.
    # An ideas ask is answered by one idea named, or by a menu of them: a list joined by "or",
    # two or more titles ("*Codenames* (2 minutes to learn), *Ticket to Ride* (a bit longer),
    # *Carcassonne* for a fourth"), or a labelled list - the person asked for things to pick from
    # and that is what they were given. An imperative is the person's own job ("Try the film you
    # have been meaning to watch"), and a colon list is left to `_options` above, which knows a
    # list of one plan ("One evening: a film, a walk and a call, then tea") from a list of ideas.
    if want == OPTIONS and not _imperative(opening) and not VERDICT_OPEN.match(opening) \
            and not LIST_AFTER_COLON.search(opening) \
            and (_a_pick(opening) or CHOICE.search(opening) or _marked_things(opening) >= 2):
        return True
    # A reply that says how many things follow and then lists them is a menu whatever order it is
    # read in: "Three that work with children, easiest first: flapjack (...), fairy cakes (...) and
    # shortbread (...)" was a miss for an options ask because a colon opened it and a sequence word
    # came before the colon. The count is what makes it a menu, and a count of seconds or minutes is
    # a time, not a list of things ("Ninety seconds in this order: ...").
    if want == OPTIONS and COUNTED_LIST.search(opening) and not A_TIME_COUNT.search(opening) \
            and not _an_instruction(opening) and _a_list_of_things(opening):
        return True
    # A steps ask can be answered with the ways to do the thing rather than with one method:
    # "how do i get from vienna airport to the city" / "From Vienna Airport: the S-Bahn S7 to Wien
    # Mitte is 25 minutes for about 4.60, and the City Airport Train is 16 minutes". A list of
    # routes is a steps answer, and it is only read as one beside the line, because `_options`
    # calls any two things joined a menu: "how do i boil an egg" / "Free-range, organic, or from a
    # farmer's market" is not a way to boil an egg and has to stay a miss.
    if want == STEPS and line:
        said = _line_text(line)
        if _options(opening) and _names_what_the_line_named(opening, said):
            return True
    # A uses ask - "what can i do with leftover chicken", "what should i do with 3k" - is answered
    # by one idea, by a menu of them, or by the one idea worked out in steps: "Half a roast chicken
    # is two more meals: strip the meat off the carcass now", "Take it in this order. First clear
    # any credit card". Both shapes are the answer to the same ask, so a line that asks what to do
    # with something is credited with whichever of the two the reply gives.
    if want in (OPTIONS, STEPS) and line and _do_with_ask(_line_text(line)):
        if _options(opening) or _steps_in(reply) or _an_instruction(opening):
            return True
    # A rule that names the side for each case is the verdict, whichever way the person's own facts
    # fall: "Fix it if it is a part and a few pounds; bin it if the repair is half the price of new"
    # answers "is it worth fixing" and "is it worth fixing or shall i get a new one" alike.
    if want in (YESNO, PICK) and _the_rule_names_both_sides(reply):
        return True
    # A few things asked for as things - what to buy, what to take, what to bring - are given as a
    # list of them, in the reply's own words: "Litter tray and litter, two bowls, a scratching
    # post, a carrier, a soft bed and food for its age". `_options` above reads the list only when
    # the reply names it (a colon, an "or", a semicolon); a list laid out as commas and "and" was
    # read as no list at all. A figure often comes first ("About 0.5kg of raw joint for 2... Then
    # potatoes, carrots, parsnips or swede"), so the opening two sentences are read, and a
    # sentence that tells the person to do something is still not a list of things.
    if want == OPTIONS and not _an_instruction(opening) \
            and not VERDICT_OPEN.match(opening) and _three_names(_opening_two(reply)):
        return True
    # The reply is not this shape; is it clearly another one? Only then is it a miss we can name.
    # A yes/no answered by saying where the thing stands has been answered: "is salmon good for
    # you" gets "Oily fish is worth two portions a week", "is it still ok to cook" gets "Cooked
    # food keeps 3 to 4 days in the fridge", "are mushrooms fattening" gets "Mushrooms are about
    # 20 calories per 100g". The clear-shape test below can only name the figure or the method it
    # read in those, and a reply about the thing the line named is not a reply about something
    # else, so this is "words cannot tell" and not a miss. Measured on 188 deck misses: 19 of the
    # 92 verdicts were answers of this shape, and every one of them read right.
    if want == YESNO and _the_same_subject(opening, line):
        return None
    for other, strong in _CLEAR:
        if other == want or (want == STEPS and other in _FIGURES):
            continue
        # A definition is evidence against a figure or a method, and says nothing about a choice:
        # "what can i use instead of chilli powder" is answered by "Paprika is the closest thing
        # to chilli powder", and "which is better, paprika or cayenne" by the same sentence.
        if other == MEANING and want in (PICK, OPTIONS):
            continue
        # A figure at the head of the reply is not a definition of anything the person asked
        # about: the figure is the answer. "74C in the thickest part of the thigh on a digital
        # thermometer, pushed in without touching bone, and the juices run clear; 75C for a moment
        # is the same thing" answers "how can i tell the chicken is done", and its "is the same
        # thing" read as a definition scored the reply as answering a different question. So did
        # "£380 sits inside the usual range of £300 to £800, so that is the going rate" for
        # "does that sound fair", and "20 miles is a real journey..." for "is that too far".
        if other == MEANING and FIGURE_HEAD.match(opening):
            continue
        # An age, a price or a figure is how a yes/no is answered as often as "yes" is: "can i
        # vote at 16" / "Eighteen to vote in a general election", "is a refurbished iphone worth
        # it" / "A refurbished phone is a good way to save 30 to 50%". The figure is the verdict
        # in those, so a figure cannot name a yes/no as the wrong shape.
        if other == AMOUNT and want == YESNO:
            continue
        # A reason opens a method as readily as it answers a why ("Because the old seal has dried
        # out, fit a new one") and it carries a yes or a no with it ("Because it is a small leak,
        # yes"), so it is evidence against a thing to choose, a place, a person, a time, an
        # amount or a definition - and not against those two.
        if other == REASON and want in (STEPS, YESNO):
            continue
        if strong(opening):
            # A hand-off that names the source holding the answer is still not the figure, the
            # place or the method asked for, but it is the answer a fact only that source can
            # settle allows: "Your council's bin-day page will say: put your postcode in and it
            # gives the day for your street" for a bin day, "a weather app or the Met Office page
            # for your postcode has it" for a sunset. None keeps it in place instead of standing
            # it down for a worse candidate, which is what the miss did. Only this last claim is
            # softened: a reply that does give the shape has already returned True above.
            if is_directed(opening):
                return None
            return False
    return None


# A how-do-I-know ask is answered by the sign that settles it, not by a step: "how do i test if
# chicken is cooked" is settled by "74C in the thickest part of the thigh ... and the juices run
# clear", and "how can i tell if its hayfever or a cold" by "The itch is the tell: hayfever
# itches". Neither is an instruction, so the steps reading called both a miss and stood down the
# answer a person most wants. The same is true of the yes/no a person asks about a thing they are
# cooking or making: "is my chicken cooked", "are the sausages ready" and "is my bread done" are
# answered by the test, not by a yes or a no nobody can see from here.
TELL_ASK = re.compile(
    r"\bhow (?:do|can|could|would|will) (?:i|you|we|someone) (?:tell|know|check|spot|test)\b"
    r"[^.!?]{0,30}\b(?:if|whether|when)\b"
    r"|\bhow to (?:tell|know|check|test)\b[^.!?]{0,20}\b(?:if|whether|when)\b"
    r"|\bhow (?:do|can) (?:i|you|we) know when\b",
    re.I)

IS_IT_DONE = re.compile(
    r"\b(?:is|are|will)\b[^?]{0,40}\b(?:done|cooked|ready|risen|proved|proven|set|thickened|"
    r"browned|defrosted|thawed)\b",
    re.I)

# The sign itself, in the two forms a card writes it: a figure with the criterion it is read
# against ("74C ... thickest part ... juices run clear", "95C inside"), or the test put into words
# ("The itch is the tell", "that is how a dry socket reads", "It sounds hollow when you tap the
# base", "they are browned all over"). A keep time is not a sign, so "mushrooms keep about a week
# in the fridge" is not read as one.
THE_SIGN = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:°\s*c|c\b|degrees|°\s*f)\b"
    r"[^.!?]{0,80}\b(?:thickest|centre|center|middle|inside|core|internal|juices|clear|firm|"
    r"soft|springy|opaque|no longer|done|cooked|ready|set)\b"
    r"|\b(?:the|that)\b[^.!?]{0,30}\bis the (?:tell|sign|test|clue|giveaway)\b"
    r"|\bthat is how\b[^.!?]{0,40}\b(?:reads|looks|feels)\b"
    r"|\b(?:when|until|once|by the time)\b[^.!?]{0,90}\b(?:browned|golden|clear|firm|soft|"
    r"springy|opaque|thick|risen|doubled|separat\w*|cracked|loose|tender|flaky|hollow)\b"
    r"|\bsounds? (?:hollow|right|done)\b",
    re.I)


def _a_sign_answers(want, line, reply):
    """True when an ask about how to tell, or whether a thing is done, is answered by the sign."""
    said = str(line or "")
    if want == STEPS:
        if not TELL_ASK.search(said):
            return False
    elif want == YESNO:
        if not IS_IT_DONE.search(said):
            return False
    else:
        return False
    opening = first_sentence(reply)
    if not opening or is_a_punt(opening):
        return False
    return bool(THE_SIGN.search(opening))


_gives_as_read = gives


def gives(reply, wants_, line=None):
    """`gives`, plus the sign that settles a how-do-I-know or is-it-done ask."""
    read = _gives_as_read(reply, wants_, line)
    if read is False and _a_sign_answers(wants_, line, reply):
        return True
    return read


def missing(reply, wants_, line=None):
    """The wants in `wants_` (one label or a list) that `reply` clearly does not give."""
    if isinstance(wants_, str):
        wants_ = [wants_]
    gone = []
    for want in wants_ or ():
        if gives(reply, want, line) is False:
            gone.append(want)
    return gone


def second_sentence(reply):
    """The sentence after the opening one, tidied, or "" when the reply has only one."""
    text = " ".join(str(reply or "").split())
    parts = re.split(r"(?<=[.!?])\s+", text, maxsplit=2)
    return parts[1].strip() if len(parts) > 1 else ""


# A bare noun asked what it is owes a definition: `what is nectar`, `what is a tariff`, `what is
# umami`. Understanding writes the `definition` label off the article, so "what is a tariff" is a
# definition and "what is nectar" is a bare `what` with nothing after it: the plainest question in
# the language carried no ask, `wants` gave it no shape, and a turn with no shape owes nothing - a
# good definition of nectar and a reply about the weather were scored the same, neither a credit nor
# a miss. In the first 2,000 deck first lines sixteen ask a thing what it is in those words.
#
# "What is" opens many other questions, and each group below is a kind rather than a wording:
#   * the bot or the person's own record - "what are you scared of", "what is my postcode";
#   * a pronoun or a preposition - "what is it", "whats in my fridge", "whats for dinner";
#   * an adjective or a participle where a noun would be - "whats nice from a chippy";
#   * a number, which is a sum: the line is read with its numbers spelled out;
#   * a superlative - "what is the smallest country in africa" wants one member of a set;
#   * a value noun - "what is the exchange rate", "what is the wifi password";
#   * a second question in the same line - "what is the ozone layer and why does it matter".
# The "is" has to be there in so many words: without it "what should i pack", "what do i say when
# the dog dies" and "what can i clean with white vinegar" are read as things to define.
BARE_WHAT_AS_IS = re.compile(r"^what(?:'s|s)\b", re.I)
BARE_WHAT_IS_PLAIN = re.compile(r"^what\s+(?:is|are|was)\s+(?P<thing>[^\s,;:]+.*)$", re.I)
BARE_NOT_A_THING_AT_THE_START = re.compile(
    r"^(?:you|u|ur|your|yours|i|im|i'm|my|mine|our|ours|we|us|me|it|this|that|these|those|there|here"
    r"|her|hers|his|their|theirs|its"
    r"|up|on|at|for|with|under|inside|outside|behind|near|next|around|about|in"
    r"|new|nice|good|great|better|best|cheap|cheapest|expensive|wrong|missing|left|leftover"
    r"|easy|easiest|hard|hardest|quick|quickest|simple|simplest|safe|safest|healthy|healthiest"
    r"|popular|common|normal|usual|fast|fastest|slow|slowest|big|biggest|small|smallest"
    r"|right|going|doing|showing|happening|playing|coming|open"
    r"|one|two|three|four|five|six|seven|eight|nine|ten|hundred|thousand|million|half|double)\b"
    r"|^the\s+(?:\w+est|best|worst|most|least|furthest)\b"
    r"|^the\s+(?:new|newest|latest|current|next|other|same|main|real)\b"
    r"|^the\s+(?:time|date|day|capital|price|cost|charge|fee|number|address|name|answer|way"
    r"|point|difference|matter)\b", re.I)
BARE_VALUE_NOUN = re.compile(
    r"^(?:the\s+)?(?:\w+\s+){0,3}(?:rate|rates|price|prices|cost|costs|charge|charges|fee|fees"
    r"|number|numbers|phone|telephone|address|addresses|email|website|opening\s+hours"
    r"|point|points"
    r"|allowance|temperature|password|postcode|pin|score|limit|deadline|budget|balance|total"
    r"|amount|figure|percentage|salary|wage|wages|weight|height|length|width|depth|distance|speed"
    r"|age|population|capacity|mileage)\b", re.I)
BARE_NOT_A_THING_ANYWHERE = re.compile(
    r"\d|\bcalled\b|\bname of\b|\bmeaning of\b|\blike\b|\bwrong\b|\bpower\s+of\b|\btimes\b"
    r"|\bplus\b|\bminus\b|\bdivided\b|\bmultiplied\b|\bpercent\s+of\b|\bsquared\b|\bcubed\b"
    r"|\btodays?\b|\btonights?\b|\btomorrows?\b|\bthis\s+(?:week|weekend|month|year)\b", re.I)
BARE_A_SECOND_QUESTION = re.compile(r"\b(?:why|how|where|when|who|which)\b", re.I)
# "what was the problem with the car again" asks the person's own record back, not what a thing is:
# the words that send the person back to something already said end the phrase.
BARE_A_RECALL = re.compile(r"\b(?:again|earlier|before|yesterday)\s*$|\b(?:i|you)\s+said\b", re.I)
BARE_NOTHING_ASKED = frozenset(("up", "on", "it", "that", "new", "happening", "going on"))


def _a_thing_to_define(phrase, whole):
    """Is this "what is X" asking what X is, rather than one of the other things the words open?"""
    if not phrase or not phrase.strip():
        return False
    if phrase.strip().lower() in BARE_NOTHING_ASKED:
        return False
    if BARE_NOT_A_THING_AT_THE_START.match(phrase):
        return False
    if BARE_VALUE_NOUN.match(phrase) and not re.search(r"\b(?:mean|means|work|works)\b", phrase, re.I):
        return False
    if BARE_NOT_A_THING_ANYWHERE.search(whole):
        return False
    if BARE_A_SECOND_QUESTION.search(phrase):
        return False
    if BARE_A_RECALL.search(phrase):
        return False
    # "What was the Berlin Wall for?" asks what it was for, not what it was.
    if phrase.rstrip().lower().endswith(" for"):
        return False
    return True


def _a_bare_definition(understood):
    """`what is nectar` asks what the thing is: a bare noun carries the ask the label missed."""
    if understood.get("about_bot"):
        return False
    whole = BARE_WHAT_AS_IS.sub("what is", LEADING_JOIN.sub("", _whole(understood)))
    plain = BARE_WHAT_IS_PLAIN.match(whole)
    return bool(plain and _a_thing_to_define(plain.group("thing"), whole))


# A dot after one of these ends a word, not the sentence: "e.g. stands for exempli gratia, Latin
# for for example" opens on that whole clause, and reading the opening as "e.g" left the shape
# cues unread and the answer to "what does e.g. mean" scored None. A title belongs here for the
# same reason ("Dr. Patel says"), and it is never the last word of a sentence.
ABBREVIATION_END = re.compile(
    r"\b(?:e\.g|i\.e|approx|incl|etc|vs|cf|fig|dept|est|ref|tel|mr|mrs|ms|dr|prof)\.$", re.I)
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


# A time said as the answer has a marker in front of it: "use it within about 5 days", "grow out of
# it by seven or eight months", "change them every one to three months", "about 30 minutes for
# pilau". A time that happens to be in the sentence is not the answer, and the words before it are
# what tells the two apart: "a new one is GBP40 to GBP80 and a shop fits it in an hour" is a price
# and a repair, and "because a second read is how the pile grows" is neither. "in" is left out for
# exactly that reason - it is what the repair takes, not what the person asked for.
TIME_LEAD_IN = frozenset((
    "within", "about", "around", "roughly", "approximately", "every", "by", "up", "least", "most",
    "after", "before", "for", "takes", "take", "lasts", "last", "lasted", "keeps", "keep", "needs",
    "need", "expected", "allow", "allows"))


def _a_time_a_sentence_on(reply):
    """True when the sentence after the reply's opening gives a time as its answer."""
    text = " ".join(str(reply or "").split())
    opening = first_sentence(text)
    if not opening:
        return False
    rest = text[len(opening):].lstrip(" .!?")
    following = first_sentence(rest) if rest else ""
    if not following:
        return False
    for pattern in (DURATION, CLOCK, STAGE, NAMED_CLOCK):
        for found in pattern.finditer(following):
            lead_in = following[:found.start()].split()[-4:]
            if any(re.sub(r"[^a-z]", "", word.lower()) in TIME_LEAD_IN for word in lead_in):
                return True
    return False


def first_sentence(reply):
    """The reply's opening sentence, tidied, or "" for an empty reply.

    A full stop inside a figure ("1.5 bar") has no space after it, so it does not end a sentence;
    the split needs the space a real sentence ends with. A full stop after an abbreviation has one,
    so the split skips it and reads on to the sentence the reply really opens with.
    """
    text = " ".join(str(reply or "").split())
    if not text:
        return ""
    for end in SENTENCE_END.finditer(text):
        before = text[:end.start()]
        if ABBREVIATION_END.search(before):
            continue
        return before.strip()
    return text


def _opening_two(reply):
    """The reply's first two sentences, tidied, or "" for an empty reply.

    A short verdict or a figure often opens the reply and the list the person asked for follows in
    the next sentence: "About 0.5kg of raw joint for 2, which is 250g a person. Then potatoes,
    carrots, parsnips or swede". Two sentences and not the whole reply, so a list that has nothing
    to do with the answer cannot make the reply pass.
    """
    text = " ".join(str(reply or "").split())
    if not text:
        return ""
    seen = 0
    for end in SENTENCE_END.finditer(text):
        if ABBREVIATION_END.search(text[:end.start()]):
            continue
        seen += 1
        if seen == 2:
            return text[:end.start()].strip()
    return text


# The words of a sentence that carry on about something rather than name one of the things: "you
# put in 5% and your employer at least 3%" has a comma and an "and" in it and names no item of a
# list, and "a scratching post, a carrier, a soft bed" names three.
NAME_STOP = re.compile(
    r"\b(?:i|you|your|yours|we|our|us|me|my|it|its|they|them|their|he|she|his|her|is|are|was|"
    r"were|be|been|being|do|does|did|have|has|had|can|could|will|would|should|shall|may|might|"
    r"must|if|then|so|but|that|this|these|those|there|here|when|while|because|about|from|with)\b",
    re.I)
# A sequence word between the items of a list splits it into steps: "a film, a walk and a call,
# then tea" is one plan, not three things to bring.
STEPS_INSIDE_A_LIST = re.compile(
    r",\s*(?:then|next|after that|afterwards|finally|lastly)\b", re.I)


def _three_names(text):
    """True when three or more things are named in one run, not prose that has commas in it.

    A list of things is names and joining words and nothing else: "Litter tray and litter, two
    bowls, a scratching post, a carrier". A sentence that carries on about something has a verb or
    a pronoun in it - "you put in 5% and your employer at least 3%, and the tax relief comes on
    top" - and that is prose with commas, not a list. So each run between the verbs and the
    pronouns is read, and three or more short items inside one of those runs is the list. Long
    items are left out: a clause with more than four words in it is a sentence, not a thing.
    """
    plain = " ".join(str(text or "").split())
    if not plain:
        return False
    for clause in re.split(r"(?<=[.!?;:])\s+", plain):
        # A list of things has commas in it. Three words joined by "and" are a sentence about two
        # things: "Small and specific beats big and vague" is not a list of things to bring.
        if clause.count(",") < 2:
            continue
        # A plan is a sequence of jobs, not a list of things: "One evening: a film, a walk and a
        # call, then tea" is one evening and the parts of it. Only a sequence word that sits
        # between the items breaks the list - "then tea" after a comma - because "a soft bed and
        # food for its age, plus a vet visit booked for the first week" is a list with the word
        # "first" inside one of its items. A clause that opens on the sequence word is the rest of
        # a list ("Then potatoes, carrots, parsnips or swede"), so the word is dropped and read on.
        opened = re.sub(r"^[\W]*(?:then|next|after that|afterwards|finally|lastly)\b", "",
                        clause, flags=re.I)
        if STEPS_INSIDE_A_LIST.search(opened):
            continue
        for run in NAME_STOP.split(opened):
            items = [item.strip() for item in re.split(r"\s*,\s*|\s+(?:and|or|plus)\s+", run)]
            items = [re.sub(r"^(?:and|or|plus)\s+", "", item) for item in items if item]
            items = [item for item in items if item]
            # A note after the list does not spoil it: "Litter tray and litter, two bowls, a
            # scratching post, a carrier, a soft bed and kitten food, plus a vet visit booked for
            # the first week" is six things and then a note. A long item in front of the others is
            # the sentence carrying on about something, not a list, so only the last item may run
            # long - "One thing you will actually do at 8pm (a film, a walk, a call), tea, and the
            # phone in another room" is one plan, not four things.
            # An item explained in brackets is a sentence about the thing, not a thing: "One
            # thing you will actually do at 8pm (a film, a walk, a call), tea, and the phone in
            # another room" is one plan for the evening, and the commas inside the brackets are
            # the parts of it.
            if "(" in run:
                continue
            short = [item for item in items if len(item.split()) <= 4]
            trailing = len(items) - len(short) == 1 and len(items[-1].split()) > 4
            if len(short) >= 3 and (len(short) == len(items) or trailing):
                return True
    return False


# ------------------------------------------------------------------------------- the figures

_WORD_NUMBER = (r"(?:\d+(?:[.,]\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|"
                r"twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|"
                r"thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|"
                r"a couple|couple|a few|half|a quarter|a third|a fifth|double|dozen)")
# A duration: a figure and a unit, or one of the phrases that is a time without a figure.
# A length is often qualified: "one to three working days" for a transfer, "two clear days" before
# you can ring them, "a working week". DURATION wanted the unit straight after the number, so three
# everyday answers to a how-long went unread.
_DURATION_QUALIFIER = (r"(?:(?:working|clear|business|banking|bank|calendar|school|full|whole|"
                       r"solid|straight|extra|more|further)\s+)?")
DURATION = re.compile(
    r"(?:" + _WORD_NUMBER + r"|\ba\b|\ban\b)[\s-]*(?:" + _WORD_NUMBER + r"[\s-]*)?"
    + _DURATION_QUALIFIER +
    r"(?:sec|second|min|minute|hr|hour|day|week|fortnight|month|year|night|morning|"
    r"afternoon|evening)s?\b"
    r"|\bovernight\b|\ball day\b|\ball night\b|\bfor a bit\b|\bwithin the hour\b|\bsoon\b|"
    r"\b(?:for|in) (?:days|weeks|months|years)\b|"
    r"\ba (?:full|whole) (?:hour|day|week|month|year)s?\b|"
    # A length said without a figure at all: "give it a couple of days", "several weeks", "a
    # handful of days". "a few days" is already a figure in `_WORD_NUMBER`; the words that need
    # their own place are the ones that take "of" before the unit, and the plural quantifiers.
    r"\b(?:a couple of|a pair of|a number of|a handful of|several|many|numerous)\s+"
    r"(?:sec|second|min|minute|hr|hour|day|week|fortnight|month|year|night|morning|"
    r"afternoon|evening)s?\b|"
    r"\bten minutes\b|\bnext day\b"
    # "A couple of hours usually" is a length of time with an "of" in the middle of it, and the
    # figure-and-unit shape above reads "a couple" as the figure and then finds no unit after it.
    r"|\b(?:a )?couple of (?:secs?|seconds?|mins?|minutes?|hours?|days?|weeks?|months?|years?|"
    r"nights?)\b", re.I)
# The ask an extent answers: "how long is the Thames", "how long is a cricket pitch", "how long
# are the queues at the moment". A duration ask is a different sentence ("how long does rice
# take", "how long should i leave it on") and is answered by `DURATION` as it always was.
#
# "does" and "do" do not say which, and having them here hid a miss: "how long does rice take"
# was read as an extent ask, so a reply of "105 metres by 68 metres" scored True. The verb the
# doing is put with is what tells them apart - take, boil, cook, heal - so an extent is written
# with the copula ("how long is the Thames"), or with the verb a thing's own length goes with
# and nothing else ("how long does the Thames run", "how long does a cricket pitch measure").
LENGTH_ASKED = re.compile(
    r"\bhow (?:long|wide|tall|deep|high|far) (?:is|are|was|were)\b"
    r"|\bhow (?:long|wide|tall|deep|high|far) (?:does|do|did) (?:[\w'-]+ ){0,3}"
    r"(?:run|runs|stretch|stretches|measure|measures|reach|reaches|extend|extends|go|goes)\b",
    re.I)
# "How long is the Thames" asks how far it runs, not how many hours. The extent of a thing is a
# length the same way a duration is, and the reply in kilometres, metres, pages or words answers
# it: "The Thames runs about 346 km", "A cricket pitch is 20.12 metres", "a marathon is 26.2
# miles". Without this reading every one of those answers was a miss on a how-long line - the
# check said the reply gave no time when the reply gave exactly the length that was asked for -
# and the figure head was read as a pick instead ("About 346 km: ..."). Only units that are never
# a duration are here; minutes and hours are `DURATION`'s and stay there.
EXTENT = re.compile(
    r"(?:" + _WORD_NUMBER + r"|\ba\b|\ban\b)[\s-]*(?:[a-z]+[\s-]+){0,3}"
    r"(?:km|kilometres?|kilometers?|miles?|metres?|meters?|yards?|feet|foot|inches?|cm|mm|"
    r"centimetres?|centimeters?|millimetres?|millimeters?|pages?|words?|lines?|songs?|tracks?|"
    r"episodes?|chapters?|metres?|m)\b", re.I)

# A time of day or a date is a time too: "by Friday", "before 9am", "on the 3rd".
CLOCK_SURE = re.compile(
    r"\b(?:mon|tues|wednes|thurs|fri|satur|sun)day\b"
    # A month is a month when it is written as one, and the names are spelled out: `sep`, `dec`
    # and `nov` were matched as prefixes, so "Separate the yolks and whisk the whites" and "6
    # separate ones" were a September, "Decide the date between you first" a December and "Novel
    # ways are rarely better" a November - four replies read as dates. `may` and `march` are read
    # with their case, because they are ordinary words too: "You may need to ring them first" was
    # a date, and so a steps answer failed. A day after one of them ("3 may") is still a date.
    r"|\b(?:january|february|april|june|july|august|september|october|november|december"
    r"|jan|feb|mar|apr|jun|jul|aug|sept|sep|oct|nov|dec)\b\.?"
    r"|\b(?-i:May|March)\b\.?"
    r"|\b(?:may|march)\b\.?\s+\d{1,2}\b"
    r"|\b\d{1,2}\s*(?:am|pm)\b|\bo'clock\b|\bmidday\b|\bmidnight\b|\btonight\b|\btomorrow\b"
    # A time in words answers a when-question just as well: "Text the same evening or the next
    # morning". A part of the day on its own does not: "pour it at the base in the morning"
    # says how to do something, not when.
    r"|\b(?:same|next|this|that) (?:morning|afternoon|evening|night)\b"
    # A clock time said as figures with minutes on them after at/by/until: "At 8.15.", "by 9:30
    # at the latest". A bare hour after a preposition ("you start work at 6", "by 9") is not read
    # here, because it is a count or a surface as often as a clock - "at 5 percent", "at 10
    # litres", "at 3-1 to the away side", "put it on 2 shelves". It is still a time on the passing
    # side, in `NAMED_CLOCK` below: a reply that answers "what time is my train" with "At 6."
    # gives what was asked for, and a reply to some other question is not failed for saying it.
    r"|\b(?:at|by|until|till|before|after|from) \d{1,2}[.:]\d{2}(?![.:]?\d)"
    # A year is a date, and "when did ww1 start" is answered in one: "began in 1914", "the
    # legions left in 410", "from 1948 to 1994", "abolished in 1848". The preposition or the range
    # is what tells a year from a figure: "2000 calories a day" is not a date.
    r"|\b(?:in|since|until|till|from|by|during|after|before) "
    # "in the 1800s" is a decade as much as "in 1914" is a year.
    r"(?:\d{3,4}s?\b|the \d{3,4}s?\b)"
    # A three-or-four figure after a preposition is a quantity as often as a year: "Change the
    # filter at 10 litres, or in 2000 uses" and "Sand it in 180 grit" were both read as dates, and
    # so was a 2000-calorie day. A unit or a count right after it keeps it a measurement.
    r"(?!\s*(?:g|kg|ml|l|p|pence|%|bar|cm|mm|km|m|ft|lb|oz|st|deg|grit|uses?|pages?|words?|"
    r"steps?|calories|kcal|people|guests?|servings?|slices?|eggs?|metres?|meters?|miles?|"
    r"yards?|feet|foot|litres?|liters?|grams?|kilos?|acres?|square|long|wide|tall)\b)"
    r"|\b\d{3,4}\s*(?:ad|bc|b\.c\.)\b"
    r"|\b(?:1[0-9]{3}|20[0-9]{2})\s*(?:-|to|or|and)\s*(?:1[0-9]{3}|20[0-9]{2})\b"
    # "on the 28th", "the 3rd of March": a date said as an ordinal.
    r"|\bthe \d{1,2}(?:st|nd|rd|th)\b|\b\d{1,2}(?:st|nd|rd|th) of (?:jan|feb|mar|apr|may|jun|"
    r"jul|aug|sep|oct|nov|dec)",
    re.I)
# A season answers a when-question too, but so faintly that it is only a pass: "Late spring for
# me: long evenings, everything green" is a pick, and the one season word in it does not make the
# reply a time. Only a season with a preposition or an edge on it ("in early autumn") is strong.
SEASON = re.compile(r"\b(?:spring|summer|autumn|winter)\b", re.I)
CLOCK = re.compile(CLOCK_SURE.pattern + r"|" + SEASON.pattern, re.I)
# A year is as good an answer to "when was the battle of waterloo" as a day is: "from 1837 to
# 1901", "In 1605 a group of English Catholics". A figure that is a count or a price is not a
# date, so a year only counts where a date is being given - after a word that introduces one ("in",
# "from", "since", "by"), at the very start of the reply, or as a decade or a century. "Use 1000
# grit paper" and "A 2024 model is better" are neither, and nor is a figure a unit follows ("in
# 2000 calories", "about 1500 steps"): the unit wins over the year. A count sits in the same
# place and looks like no unit at all - "change the filter in 2000 uses", "in 2000 cycles" - so
# a plural word after the figure keeps it out too. A plural that really follows a year is rare
# in a reply ("in 1945 soldiers came home"); a count after a preposition is common.
NOT_A_YEAR = (
    r"(?!\s*(?:cal|kcal|calorie|step|mile|km|kilomet|metre|meter|gram|g\b|kg|ml|litre|liter|"
    r"watt|lumen|gb|mb|megabyte|pound|dollar|euro|per cent|%)\w*)"
    r"(?!\s+[a-z]{2,}s\b)")
DATE = re.compile(
    r"(?:\b(?:in|from|since|until|till|by|of|during|between|after|before|around|about|circa|"
    r"early|late|mid|and|to)\s+(?:the\s+)?|^)(?:1[0-9]{3}|20[0-2][0-9])\b" + NOT_A_YEAR +
    r"|\b(?:in|from|since|during|of|the|by|until|early|late|mid)\s+(?:\d{4}s|\d{1,2}(?:st|nd|"
    r"rd|th) century)\b", re.I)
# A time is often said as a bare hour or a date rather than as a duration: "You start work at 6",
# "Your driving test is on the 12th", "on Tuesday at 6.30", "by the 3rd of may". DURATION and
# CLOCK both want a unit of time or a named day on its own, so the hour a time word introduces is
# read here as well. Only the passing side uses this: a bare figure is not evidence that a reply
# to some other question is about a clock.
# The hour is said in words as often as in figures: "You go to bed at eleven", "at half past
# six". Only the twelve clock hours are read that way - "at half the price" is not a time.
HOUR_WORD = (r"(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
             r"(?:\s*(?:am|pm|a\.m|p\.m))?")
# Only a clock shape is a clock on its own: a colon or a dot between the figures, an am/pm, an
# ordinal date, or a day of a month. A bare figure or a bare hour word is a clock only after a
# time word that cannot introduce anything else, and only inside the 24 hours of a day - "on one
# side", "on 2 shelves", "about one in five" and "at 5 percent" name no time between them.
CLOCK_ANYWHERE = (
    r"(?:\d{1,2}[:.]\d{2}"
    r"|\d{1,2}\s*(?:am|pm|am\.|pm\.|a\.m|p\.m|o'clock)"
    r"|(?:the\s+)?\d{1,2}(?:st|nd|rd|th)\b"
    r"|(?:the\s+)?\d{1,2}\s+of\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
    r"|(?:half|quarter|ten|twenty|five|twenty-five)\s+(?:past|to)\s+" + HOUR_WORD + r")"
)
_HOUR_24 = (r"(?:[01]?\d|2[0-4])(?![\d:])(?!\.\d)"
            # A scoreline or a ratio is not a clock: "It finished at 3-1 to the away side",
            # "at 2-1 the draw looks generous".
            r"(?!\s*[-\u2013\u2014]\s*\d)"
            # Nor is a share or a measurement: "at 5 percent", "at 10 litres", "change it in 2000
            # uses", "wash it at 40C".
            r"(?!\s*(?:%|percent|per cent|g|kg|ml|l|p|pence|bar|cm|mm|km|m|ft|lb|oz|st|deg|"
            r"metres?|meters?|miles?|yards?|feet|foot|litres?|liters?|grams?|kilos?|calories|"
            r"kcal|acres?|grit|uses?|square|long|wide|tall)\b)")
NAMED_CLOCK = re.compile(
    r"(?:\b(?:at|by|from|until|till|before|after|around|about|on)\s+" + CLOCK_ANYWHERE +
    r"|\b(?:at|by|from|until|till|before|after)\s+(?:" + HOUR_WORD + r"(?!\s+of\b)|" +
    _HOUR_24 + r")"
    r"|(?:half|quarter|ten|twenty|five|twenty-five)\s+(?:past|to)\s+" + HOUR_WORD + r")", re.I)
# "One of the hardest days" is not a quantity: a number word counts wherever it counts a
# thing, and `one of the` is the article of a whole class, not a count.
FIGURE = re.compile(r"\d|\b(?!one of\b)" + _WORD_NUMBER + r"\b", re.I)
# A price, in the words the reply has. "Nothing" is not a price by itself: "Nothing has to be
# decided today" is a condolence and "nothing on your cats in what I keep" is an empty memory, so
# the word counts only where it is what the person pays.
MONEY = re.compile(
    r"[£$€]|\b(?:pence|pounds?|quid|dollars?|euros?|cents?|free)\b"
    r"|^(?:nothing|nil|nowt)\b|\bnothing (?:at all|extra|much|to pay|else|on top)\b"
    r"|\bcosts? nothing\b", re.I)


def _a_figure(opening):
    return bool(FIGURE.search(opening))


# A how-long question is answered by the figure on its own more often than by any word: "and how
# long for a hard boiled one" gets "9 to 10 for hard boiled", and a bare range at the front of a
# reply to a how-long line is minutes or hours, because that is what the line asked for. It only
# counts as the opening, so a figure further in is not mistaken for the answer.
BARE_RANGE = re.compile(
    r"^[^\w]{0,3}(?:about |around |roughly )?(?:\d{1,3}|" + _WORD_NUMBER + r")"
    r"\s*(?:-|to|or|\u2013)\s*(?:\d{1,3}|" + _WORD_NUMBER + r")\b", re.I)

# A stage rather than a length: "waking at night is normal for the first months", "the first few
# weeks are recovery". A when or a how-long question about a baby, a puppy or a new job is
# answered in stages like these, and none of them carries a figure.
STAGE = re.compile(
    r"\b(?:for|in|over|through|during) the first (?:few |couple of |several )?"
    r"(?:days|weeks|months|year|bit)\b|\bthe first (?:few |couple of )?(?:days|weeks|months)\b"
    r"|\b(?:first|1st) birthday\b|\buntil (?:they|he|she) (?:are|is) \w+\b", re.I)
# "Never" is the time a how-long question asked for: "Salt does not go off at all", "it lasts
# indefinitely". Read as the answer rather than as nothing said.
NEVER = re.compile(
    r"\b(?:indefinitely|(?:does not|doesn't|do not|don't|will not|won't|never) "
    r"(?:go(?:es)? off|expire|spoil|perish)|(?:last|lasts|keep|keeps|stay|stays|good) "
    r"(?:good )?(?:for ever|forever|indefinitely))\b", re.I)

# A reply that opens on how often has answered a different question: "Once a year, and a gas
# boiler service is usually GBP60 to GBP120". The whole phrase is read, because "once a year"
# holds "a year" and the duration pattern would take that for a length.
RATE_PHRASE = re.compile(
    r"^(?:once|twice|(?:three|four|five|six|\d+)\s+times|"
    r"every (?:\w+ )?(?:day|week|month|year|morning|evening|night)|"
    r"daily|weekly|monthly|yearly|nightly)"
    r"(?:\s+(?:a|an|per|each|every)\s+(?:day|week|month|year|morning|evening|night))?", re.I)


# A when is answered by the stage a thing has to be at as often as by a date, and in a garden it is
# answered that way more often than not: "Start feeding when the first truss of flowers has set
# fruit", "plant them out once the soil has warmed", "sow as soon as the ground can be worked".
# The condition is the time; the job in front of it is what the person does about it. Only the
# three words that introduce a condition are read, because "after the last frost" and "before the
# risk of frost" are as often the how of a job as its when.
STAGE_WHEN = re.compile(
    r"(?:(?:\bwhen|\bas soon as)\s+(?:the|it|its|they|they're|there|a|your|their)\b"
    r"|\bonce\s+(?:the|it|its|they|they're|there|your|their)\b)"
    r"[^.?!]{0,70}?\b(?:has|have|had|is|are|was|were|shows?|showing|sets?|set|starts?|started|"
    r"reaches?|reached|begins?|begun|appears?|emerges?|sprouts?|sprouted|flowered|flowers|"
    r"warms?|warmed|workable|cooled|cools|dried|dries|firm|ready|grown|thickened|risen)\b",
    re.I)

# A part of the day with an edge on it is a time of day, and answers a when-question: "shut them
# again mid-afternoon so the heat is kept for the night", "pick them first thing in the morning",
# "by late evening". The bare part of the day is not counted (see CLOCK_SURE): "pour it at the base
# in the morning" says how to do something, not when, and the edge word is what makes the
# difference between the two.
EDGED_PART_OF_DAY = re.compile(
    r"\b(?:mid|early|late)[- ]?(?:morning|afternoon|evening|night)\b"
    # "pop out first thing" is a time of day; "the first thing it tells anyone" is not, so the
    # thing the phrase is followed by is what tells the two apart.
    r"|\b(?:first|last) thing\b(?!\s+(?:a|an|the|it|i|you|we|they|he|she|that|this|of|about)\b)"
    r"|\bfirst light\b|\bdaytime\b"
    r"|\b(?:at|by|before|after|until|till|around|about) (?:dawn|dusk|nightfall|sunset|sunrise|"
    r"daybreak)\b|\bend of the (?:day|afternoon|evening)\b", re.I)

# A season named by what is happening in it is the when as much as a month is: "Mow little and
# often in the growing season", "Scarify and aerate in autumn", "water deeply once a week in dry
# spells". The word season does not have to be there - the growing months, a dry spell - and one of
# the four seasons is already in CLOCK. Like STAGE_WHEN this only counts on a line that asks when,
# because "water it in dry spells" is the how of a job and not a length.
SEASON_WHEN = re.compile(
    r"\b(?:in|during|through|throughout|into|over)\s+(?:the\s+)?"
    r"(?:growing|dormant|bare|planting|flowering|nesting|mating|wet|dry|rainy)\s+season\b"
    r"|\b(?:the\s+)?growing months?\b"
    r"|\b(?:in|during)\s+(?:a\s+|the\s+)?(?:dry|wet|cold|warm)\s+spells?\b",
    re.I)

# A time is not always a figure. "No honey at all before the first birthday", "Christmas Day is the
# last posting date", "in the morning, before the heat is on" are all times, and only the words
# that name an occasion with a preposition in front, or a day from the short closed list, count:
# "Beans on toast is a good cheap dinner" is not a time for the word dinner in it.
NAMED_TIME = re.compile(
    r"\b(?:before|after|until|till|by|at|on|from|in|over|during)\s+(?:the\s+)?"
    r"(?:first|second|third|next|last|that|their|his|her)?\s*"
    r"(?:birthday|christmas|easter|new year|weekend|weekday|morning|afternoon|evening|night|"
    r"breakfast|lunch|teatime|tea|dinner|supper|bedtime|school|school night|work|the day|"
    r"arrival|takeoff|checkout|check-in)\b", re.I)
DAY_NAME = re.compile(
    r"\b(?:christmas|easter|new year'?s?|bank holiday|birthday|half term|term time|"
    r"the weekend)\b", re.I)

# A count per day is a rate, not a length: "2000 calories a day is about right" answers *how much*
# and is not the answer to "how long will it take to lose a stone". The count and its rate are
# taken off before the duration is read, so "Run 1500 metres in 20 minutes every day" keeps the 20
# minutes. Only a count of what is used or done reads this way; a count of weight or volume in
# front of "a week" is how fast something changes, which is what a how-long line asked for, so kg,
# grams, litres and pounds stay out of the list.
RATE_OF_A_COUNT = re.compile(
    r"\b\d[\d,.]*\s*(?:cal|kcal|calorie|step|rep|unit|mile|km|kilomet|metre|meter)s?\b"
    r"(?:\s+\w+){0,2}\s+"
    r"(?:a|an|per|each|every)\s+(?:day|week|month|year|morning|evening|night)\b", re.I)


# A length said in minutes without a count in front: "They're usually with you within minutes",
# "leave it in for a few minutes". DURATION wants a figure or an article before the unit, so
# "within minutes" and "a few minutes" were read as no time at all and a real answer to a how-long
# was failed. Only the passing side reads this; the strict reading that fails a reply for naming a
# time stays as narrow as it was.
MINUTES_AS_A_LENGTH = re.compile(
    # "In a minute" and "Back in a minute" mean soon, so `in` and `after` are not read here; a
    # figure before the unit is `DURATION`'s business and was never this arm's.
    r"\b(?:within|for)\s+(?:a few|a couple of|several|a|one|two|three|four|five|ten)\b"
    r"[\s-]*(?:min|minute)s?\b"
    r"|\ba few (?:min|minute)s\b|\bwithin (?:a few |a couple of )?(?:min|minute)s\b", re.I)


# "No fixed time" is an answer to a how-long, not a refusal to give one: "how long do i reheat it
# for" / "No fixed time: reheat it until it is piping hot right through ... A portion takes 2 to 4
# minutes". An apology would not have the "no fixed time" in front of it.
NO_FIXED_TIME = re.compile(
    r"^(?:no|there'?s no|there is no) (?:fixed|set|exact|hard and fast) (?:time|length|deadline)\b",
    re.I)


def _a_time(opening):
    # A time said as a bare hour or a date is a time: "At 8.15", "Your driving test is on the
    # 12th", "by the 3rd of may". NAMED_CLOCK is read here, on the passing side only: a figure
    # with a time word in front is not evidence that a reply to some other question is a clock.
    if NAMED_CLOCK.search(opening):
        return True
    # A part of the day with an edge on it is a time of day: "shut them again mid-afternoon" answers
    # a when, where a bare "in the morning" says how. See EDGED_PART_OF_DAY.
    if EDGED_PART_OF_DAY.search(opening):
        return True
    # A frequency is not a length. "Once a year, and a gas boiler service is usually GBP60" holds
    # "a year", which the duration pattern reads as a length; the rate phrase in front says the
    # reply answered *how often*. So the rate phrase is taken off, and what is left has to carry
    # the duration: "every day for ten minutes" still does, "twice a week" does not.
    said = RATE_PHRASE.sub("", opening, count=1) if RATE_PHRASE.match(opening) else opening
    # "2000 calories a day" is a rate, not a length: the figure carries a count with a rate word
    # after it, so the length is taken off before the duration is read.
    said = RATE_OF_A_COUNT.sub(" ", said) if RATE_OF_A_COUNT.search(said) else said
    # A stage ("in the first few days", "until the first birthday") and a never ("does not go off
    # at all", "keeps indefinitely") answer a how-long as plainly as a duration does.
    if NO_FIXED_TIME.match(said):
        return True
    if (DURATION.search(said) or CLOCK.search(said) or BARE_RANGE.match(said)
            or STAGE.search(said) or NEVER.search(said) or NO_FIXED_TIME.match(said)
            or MINUTES_AS_A_LENGTH.search(said)):
        return True
    # The named time is read from the opening clause only, and never from a reply that opens on
    # the job: "leave it in the oven until the morning" is a method that names a time on the way.
    if INSTRUCTS.match(opening):
        return False
    first_clause = re.split(r"[,;:]", said, maxsplit=1)[0]
    return bool(NAMED_TIME.search(first_clause) or DAY_NAME.search(first_clause)
                or DATE.search(first_clause))


def _a_clear_time(opening):
    """The time readings strong enough to fail a reply to a different question.

    A figure with a unit, an hour on the clock, a weekday, a date, the part of a day named as
    "next morning" are all what a reply is *about*. A bare season is not, and neither is a word
    list; see `_CLEAR`.
    """
    return bool(DURATION.search(opening) or CLOCK_SURE.search(opening)
                or BARE_RANGE.match(opening))



# How often is an amount without a figure: "every day if you can", "twice a week", "daily".
RATE = re.compile(
    r"\b(?:every (?:day|week|month|year|morning|evening|night|"
    r"other (?:day|morning|evening|night))|every few (?:days|weeks)|"
    r"most (?:days|mornings|evenings|nights|weekends)|once|twice|"
    r"three times|daily|weekly|monthly|yearly|nightly|\d+ times)\b", re.I)


# A line that asks how old - "what age should a kid get a phone", "how old is a kitten before it
# can go out". The ask is a figure, so the reply owes a figure, but it owes a figure of years: the
# amount check credits any figure at all, and "Spend £100 to £200 on a used handset" passed as the
# answer to "my kid wants a phone, what age".
ASKS_AN_AGE = re.compile(r"\bwhat age\b|\bhow old\b", re.I)

# The figure an age is given in: a number of years, months or weeks ("12 years old", "around four
# months"); a birthday ("the September after their fourth birthday"); a figure named as an age; a
# bare small number, which is how people write an age ("Most parents wait until about 11 or 12");
# or a spelled number opening the verdict ("Eighteen to vote in a general election"). A price is
# never an age, so a number with a currency sign in front of it does not count, and "two years of
# contract" is a length rather than an age.
_AN_AGE_YEARS = re.compile(
    r"(?:\d+|" + _WORD_NUMBER + r")\s*(?:-\s*)?years?\s*(?:old|of age)\b"
    r"|\b(?:age|aged)\s+(?:of\s+)?(?:\d+|" + _WORD_NUMBER + r")\s*years?\b"
    r"|^(?:\d+|" + _WORD_NUMBER + r")\s*years?\b", re.I)
_AN_AGE_MONTHS = re.compile(
    r"(?:\d+|" + _WORD_NUMBER + r")\s*(?:-\s*)?(?:months?|weeks?)\s*old\b"
    r"|\b(?:about|around|at|by|from|until|till|under|over|aged?)\s+(?:\d+|" + _WORD_NUMBER +
    r")\s*(?:months?|weeks?)\b"
    r"|^(?:\d+|" + _WORD_NUMBER + r")\s*(?:months?|weeks?)\b", re.I)
_AN_AGE_BIRTHDAY = re.compile(r"\b(?:\d+(?:st|nd|rd|th)|[a-z]+(?:st|nd|rd|th))\s+birthday\b",
                              re.I)
_AN_AGE_NAMED = re.compile(r"\b(?:age|aged)\s+(?:\d+|" + _WORD_NUMBER + r")\b", re.I)
_AN_AGE_BARE = re.compile(
    r"(?<![£$€\d.,])\b\d{1,2}\b(?![.,]?\d)"
    r"(?!\s*(?:%|minutes?\b|mins?\b|hours?\b|hrs?\b|days?\b|pounds?\b|pence\b|quid\b|"
    r"times?\b|per\b|each\b|of them\b))", re.I)
_AN_AGE_SPELLED_OPENS = re.compile(
    r"^(?:" + _WORD_NUMBER + r")\b(?=\s*(?:,|to\b|is\b|or\b|and\b|-|\u2013))", re.I)


def _an_age_is_given(opening):
    return bool(_AN_AGE_YEARS.search(opening) or _AN_AGE_MONTHS.search(opening)
                or _AN_AGE_BIRTHDAY.search(opening) or _AN_AGE_NAMED.search(opening)
                or _AN_AGE_BARE.search(opening) or _AN_AGE_SPELLED_OPENS.match(opening))


def _an_amount(opening):
    # An amount is a figure with something to count, or a price. A bare count of things ("three
    # of them") is still a quantity, so the figure alone is enough here; the check says nothing
    # about whether it is the *right* figure, which is the miss a person has to look at.
    return bool(FIGURE.search(opening) or MONEY.search(opening) or RATE.search(opening))


# A price asked for in the line's own words: "how much does a new washing machine cost", "what is
# the price of a train ticket", "how much does a garage charge for a service". The words a price
# shares with something else are not in it: "charge" is a phone charging as often as a fee, and
# "spend" is "how many days should i spend in florence", so "charge" counts only when it takes a
# "for". A bare "how much" is a quantity as often as a price ("how much water", "how much sleep"),
# so the line has to say money before the reply is held to money.
PRICE_ASKED = re.compile(
    r"\b(?:cost|costs|priced?|prices?|pay|pays|paid|charged|charges? for|afford|fees?|quote|"
    r"salary|rent)\b|[\u00a3$\u20ac]|\b(?:pounds|quid|euros?|dollars?|pence|tenner)\b", re.I)
# Money in the reply. Not MONEY itself: that counts "nothing", which is every other reply. A price
# written the short way ("45 to 50p an hour") is money as much as "£" is.
PRICE_GIVEN = re.compile(
    r"[\u00a3$\u20ac]|\b\d+p\b|\b(?:pounds|quid|pence|euros?|dollars?|cents?|free|costs?|"
    r"prices?|charges?|fees?|paid|pay|spend|budget|afford|quote|refund|salary|rent|tenner)\b",
    re.I)


def _a_price_asked(line):
    """True when the line asks what something costs, in a money word of its own."""
    return bool(PRICE_ASKED.search(_line_text(line)))

# A figure that counts a thing you would measure - "two mugs", "one hour", "three pounds" - says
# the reply is about an amount. A spelled number that is only the word in front of an ordinary
# noun does not: "One channel going funny is the aerial or the box" is the cause of a blurry
# screen, and "Barcelona for a city and a beach in one trip" is a place. Both were read as
# amounts and the reply was failed for it. Only the evidence keeps this narrow reading; the
# amount check itself keeps the wide one, because "two eggs" answers "how many eggs".
MEASURED = re.compile(
    r"(?:\d|\b" + _WORD_NUMBER + r")\s*-?\s*(?:minutes?|mins?|hours?|hrs?|days?|weeks?|"
    r"months?|years?|seconds?|secs?|mugs?|cups?|tablespoons?|tbsps?|teaspoons?|tsps?|grams?|"
    r"kilograms?|kg|litres?|liters?|ml|pints?|quarts?|per cent|percent|degrees?|miles?|km|"
    r"metres?|meters?|feet|foot|inches?|times?|pence|pounds?|quid|each|people|servings?)\b",
    re.I)


# A number word at the very start of a reply is the answer to a how-many however short it is:
# "One.", "Two.". The pronoun "one" that ends a noun phrase - "the cheap one", "a new one" - is
# not a figure, and neither the amount reading in `_an_amount` nor `FIGURE` can tell them apart.
A_BARE_NUMBER = re.compile(r"^(?:\d+|" + _WORD_NUMBER + r")\.?$", re.I)


def _a_figure_that_counts(opening):
    """A figure that makes an opening a figure: a digit, a price, a rate, a measured amount, or a
    count that is the whole reply."""
    return bool(_an_amount_to_read(opening) or A_BARE_NUMBER.match(opening.strip()))


def _an_amount_to_read(opening):
    """The amount only as evidence: a digit, a price or a rate, or a number counting a measure."""
    if re.search(r"\d", opening) or MONEY.search(opening) or RATE.search(opening):
        return True
    return bool(MEASURED.search(opening))


# A figure says what a reply is about only when the reply opens on it. The clear reading above
# is evidence, and evidence has to be the answer rather than a passing number: "Lean forward,
# pinch the soft part of the nose and hold for ten minutes" answers "how do i stop a nosebleed"
# with the method and mentions a duration on the way, and "Match the limit to the age: under
# two, video calls and the odd photo only" answers a screen-time question with a rule. Both were
# read as a time and an amount, and so as misses, on a reply that gave what was asked.
#
# So the fallback reads a figure only from the head of the opening, where a duration or a count
# is the whole of the first words. Five words is the width that keeps the figure that *is* the
# answer ("Two years' service is the line", "£60 to £120 once a year") and drops the ones that
# arrive after the reply has already made its point: at three words 32 turns of a 547-turn sweep
# stopped being named misses, at five 27, at eight 26, all of them misses the check could not
# really name and not one a reply that answered the line.
_FIGURE_HEAD = 5


def _figure_at_the_head(opening, pattern):
    """Whether `pattern` matches within the first `_FIGURE_HEAD` words of `opening`."""
    match = pattern.search(opening)
    return match is not None and len(opening[:match.start()].split()) < _FIGURE_HEAD


def _a_clear_time_at_the_head(opening):
    """`_a_clear_time` as evidence: the time has to be where the reply starts."""
    return (_figure_at_the_head(opening, DURATION)
            or _figure_at_the_head(opening, CLOCK_SURE)
            or bool(BARE_RANGE.match(opening)))


# A number written out is a figure when it counts a measure - "two mugs", "one hour", "three
# pounds" - and the word in front of an ordinary noun otherwise: "One channel going funny is the
# aerial or the box" is the cause of a blurry screen and was read as an amount, so a why-answer
# was failed for it. Only the evidence reads it this way; the amount check itself keeps the wide
# reading, because "two eggs" answers "how many eggs" whether or not "eggs" is a measure.
_MEASURE_AFTER = re.compile(
    r"\s*-?\s*(?:minutes?|mins?|hours?|hrs?|days?|weeks?|months?|years?|seconds?|secs?|mugs?|"
    r"cups?|tablespoons?|tbsps?|teaspoons?|tsps?|grams?|kilograms?|kg|litres?|liters?|ml|pints?|"
    r"quarts?|per cent|percent|centigrade|degrees?|miles?|km|metres?|meters?|feet|foot|inches?|"
    r"times?|pence|pounds?|quid|each|people|servings?)\b", re.I)


def _an_amount_at_the_head(opening):
    """`_an_amount` as evidence: the figure has to be where the reply starts, and a number
    written out has to be counting a measure rather than sitting in front of a noun."""
    if _figure_at_the_head(opening, MONEY) or _figure_at_the_head(opening, RATE):
        return True
    match = FIGURE.search(opening)
    if match is None or len(opening[:match.start()].split()) >= _FIGURE_HEAD:
        return False
    if match.group(0)[0].isdigit():
        return True
    return bool(_MEASURE_AFTER.match(opening, match.end()))


# ------------------------------------------------------------------------------- the things

# A place is a kind of place ("the post office", "any chemist", "the app") or its name ("in
# Bristol"). The named kind is what a where-answer almost always gives, and a capital after a
# preposition is a name far more often than it is anything else in the opening sentence. The
# plural is the same place ("across two or three shops", "the big supermarkets"), so the closing
# word boundary allows one, and the same goes for the roles below.
PLACE_WORD = re.compile(
    r"\b(?:shop|store|supermarket|chemist|pharmac|post office|bank|building society|council|"
    r"\bgp\b|doctor'?s|surgery|dentist|library|garage|station|market|website|web site|site|app|"
    r"online|branch|office|centre|center|clinic|hospital|recycling|tip\b|dump|high street|"
    r"department|service desk|desk|reception|kiosk|counter|aisle|dealer|showroom|garden centre|"
    r"petrol station|airport|bus stop|platform|address|tesco|asda|sainsbury|aldi|lidl|morrisons|"
    r"co-op|boots|argos|screwfix|ikea|amazon|ebay|gov\.uk|passport office|dvla|jobcentre|"
    r"citizens advice|charity shop|car boot|facebook marketplace|freecycle|wherever|"
    r"downstairs|upstairs|outside|indoors|in the garden|in the kitchen|in the loft|in the shed|"
    # Where a thing is kept, put or found is a place as much as a shop is, and an answer to
    # "where do i find the model number of my oven" / "on a plate or sticker ... behind the
    # drop-down flap" or "where should i keep my passport" / "in a zipped inside pocket" was
    # graded a miss for it. Nouns of a room and a container only - a place, not a method.
    r"drawer|cupboard|cabinet|wardrobe|shelf|shelves|rack|hook|peg|locker|safe|"
    r"pocket|handbag|backpack|rucksack|suitcase|glove ?box|boot of the car|"
    r"hallway|corridor|landing|garage|shed|loft|attic|basement|cellar|balcony|porch|"
    r"kitchen|bedroom|bathroom|toilet|utility room|airing cupboard|under the sink|"
    r"in the cupboard|in the drawer|on the shelf|in the fridge|in the freezer|in the bin|"
    r"on the wall|on the door|in the hall|by the door|at the back of|at the front of|"
    r"on top of|behind the|under the|next to the|beside the|inside the)"
    r"(?:s|es)?\b",
    re.I)
# A place word is evidence that the reply answers a different question only when it names a place
# to go to: a shop, a website, an office, a room of a building. The room and container nouns added
# for "where do i keep my passport" / "in a zipped inside pocket" are a place answer, but as
# evidence of another shape they are wrong: "There is no safe number of drinks before driving"
# opens on the noun "safe", a gate fix opens on "a hook and eye", "elbow under the ball" and
# "a hutch with a run attached, or a big shed" hit "under the" and "shed", and each of those
# cleared a good amount, steps or yes/no answer into a miss - 13 false misses over the 5,440
# stored replies I grade, and no credit is lost by reading the evidence this way. The wide list
# stays in the place reading itself, where it is the answer rather than the evidence.
PLACE_AS_EVIDENCE = re.compile(
    r"\b(?:shop|store|supermarket|chemist|pharmac|post office|bank|building society|council|"
    r"\bgp\b|doctor'?s|surgery|dentist|library|garage|station|market|website|web site|site|app|"
    r"online|branch|office|centre|center|clinic|hospital|recycling|tip\b|dump|high street|"
    r"department|service desk|desk|reception|kiosk|counter|aisle|dealer|showroom|garden centre|"
    r"petrol station|airport|bus stop|platform|address|tesco|asda|sainsbury|aldi|lidl|morrisons|"
    r"co-op|boots|argos|screwfix|ikea|amazon|ebay|gov\.uk|passport office|dvla|jobcentre|"
    r"citizens advice|charity shop|car boot|facebook marketplace|freecycle|wherever|"
    r"downstairs|upstairs|outside|indoors|in the garden|in the kitchen|in the loft|in the shed)"
    r"(?:s|es)?\b",
    re.I)


# A name is not always capital-then-lowercase: "You're from the UK", "made in the USA", "the EU
# sets it" name a place too, and an all-capitals short word after a preposition is a name far more
# often than anything else. The all-capitals arm takes "the" or no determiner at all, because "of a
# CEO" in a podcast title is a person and not a place, and so is "in a US study".
# A "where" that introduces a relative clause names no place to go: "should i stay where i am",
# "should i leave it where it is", "should i move where my mum is". The line asks whether, and
# the same word is the place understanding reads, so a verdict was scored a miss for naming no
# place. A line that asks to be told the place keeps it: "can you tell me where it is", "do you
# know where the stop cock is".
# The "where" of "where does all my money go" is not a place: the line is about spending, and the
# budget answer that says what to do with it was scored a miss for naming no place. Only a sum and
# a going: "where does the recycling go" and "where does this go" stay places, and so does "where
# does my pension go", which names the provider.
WHERE_MONEY_GOES = re.compile(
    r"\bwhere (?:does|do|did) (?:it all |all )?(?:my|our|the|his|her|your) "
    r"(?:money|pay|wages|salary|income|budget|earnings|time)\b[^?]{0,20}\b(?:go|goes|went)\b"
    r"|\bwhere (?:my|our|the|his|her|your) (?:money|pay|wages|salary|income|budget|time) "
    r"(?:goes|go|went)\b", re.I)

WHERE_RELATIVE = re.compile(
    r"\bwhere\s+(?:i|we|you|he|she|they|it|my|your|our|his|her|their)\b[^?.]{0,20}?"
    r"\b(?:am|is|are|was|were|live|lives|stay|stays|sit|sits|work|works|go|goes)\b", re.I)
ASKS_TO_BE_TOLD_WHERE = re.compile(
    r"\b(?:tell (?:me|us)|know|knows|say|says|shows?|explain|remind|remember|any idea|wonder|"
    r"find|check)\b[^?]{0,25}\bwhere\b", re.I)
PLACE_NAME = re.compile(r"\b(?:in|at|to|from|near|of|round|around|towards)\s+"
                        r"(?:(?:the\s+)?[A-Z]{2,4}(?![A-Za-z])|(?:the\s+|a\s+)?[A-Z][a-z]{2,})")

# ---- the places a reply names without a shop, a branch or a town in sight -------------
# PLACE_WORD and PLACE_NAME above read a place as a counter, a branch, a station or a name with a
# capital in it, and those are the kinds a "where can i buy it" is answered with. A person's own
# where is answered with something else far more often: "wheres my keys" / "the hook by the
# door", a router / "up high, on a shelf", a cat's bed / "the top of a wardrobe, a windowsill",
# a car / "the side streets five minutes further out, the station car park, a park and ride".
# Every one of those named a place and read as naming none, so the check failed the answer it had
# asked for. These are read by `_a_place` alone - never by `_CLEAR`, where a place reading is
# evidence that the reply is *not* the shape asked for, and where a wide reading would turn "put
# it in the cupboard" into a named miss for a time question.
PLACE_KIND = re.compile(
    r"\b(?:shops|stores|supermarkets|pharmacies|station|stations|markets|cafes|cafés|"
    r"booths|branches|clinics|charities|tip|depots|counters|showrooms|kiosks|"
    # the kinds a cheap lunch or a free space is found in, which are nobody's shop
    r"market hall|market halls|food court|food courts|bakery|bakeries|street food|"
    r"food van|food vans|multi storey|multistorey|multi-storey)\b", re.I)
PLACE_AT_HOME = re.compile(
    # the room, the shelf and the street are places in the sense a person means. The plural is
    # the same place: "the side streets", "the drawers", "booths at stations".
    r"\b(?:room|bedroom|bathroom|kitchen|utility|hall|hallway|landing|corridor|garage|loft|"
    r"shed|porch|doorstep|doormat|doorway|door|stairs|staircase|step|floor|corner|"
    r"wardrobe|cupboard|drawer|shelf|shelves|bookcase|bookshelf|mantelpiece|"
    r"windowsill|window sill|bedside|nightstand|bed|sofa|settee|couch|cushion|chair|"
    r"table|desk|hook|peg|pocket|bag|handbag|rucksack|backpack|glovebox|glove box|"
    r"footwell|boot|bin|washing machine|tumble dryer|airing cupboard|"
    r"street|side street|back street|road|car park|park and ride|lay-by|lay by|"
    r"cul-de-sac|estate|alley|alleyway|walkway|underpass|carpark)s?\b"
    # a spot is as often a phrase as a noun: "the end of the sofa", "on top of the fridge"
    r"|\b(?:on|in|under|behind|beside|next to|top of|bottom of|end of)\s+"
    r"(?:the\s+|your\s+|my\s+)?"
    r"(?:sofa|bed|table|desk|stairs|fridge|freezer|counter|shelf|cupboard|wardrobe|"
    r"radiator|window|door|mat|hook|hall|car|boot|pushchair|pram|buggy)s?\b"
    # and the phrase is open-ended, because a spot is anywhere: "behind the little hatch" is
    # where a filter is
    r"|\b(?:behind|under|underneath|beside|next to|on top of|in front of|at the bottom of|"
    r"at the back of|at the front of|at the side of)\s+(?:the\s+|your\s+|my\s+|a\s+)?[a-z]{3,}"
    # a spot given as a position rather than a thing: "up high, out in the open"
    r"|\b(?:in the open|up high|off the floor|in the middle of|away from the (?:wall|floor|heat))",
    re.I)
# A list of places offered as the answer itself, with no preposition before any of them: "Pick by
# what you want from a city: Lisbon for food and a short flight, Seville for heat and tapas, Prague
# or Budapest for the Christmas markets". The answer to a where-question is a list of two or more
# names, so two of them after a colon, a semicolon, a comma, an "or" or an "and" is what is counted.
# One capital is not a list: ": Brown the mince", ", Stop it, undo the tangle" and ": Aim for 10%"
# are a recipe, a step and a budget, and the capital that opens a clause is not a place.
PLACE_NAME_ANY = re.compile(r"(?:(?<=[:;,]\s)|(?<=\bor\s)|(?<=\band\s))[A-Z][a-z]{2,}")
# A calendar word is not a name. "The 14th of June." was read as both a where and a who, because
# June is a capitalised word after "of". The month and day names are the calendar's own, read the
# way `CLOCK_SURE` reads them - a month after a preposition, a weekday, a figure with an ordinal on
# it - and they are taken out of the opening before a place or a person is looked for. A month on
# its own is left alone: it is a capital in the middle of a sentence like any other, and "Opens in
# January" is a when wherever it turns up.
CALENDAR_WORD = re.compile(
    r"\b(?:in|on|of|by|until|till|from|during|after|before|early|late|mid|and|to)\s+"
    r"(?:the\s+)?(?:january|february|april|june|july|august|september|october|november|december"
    r"|jan|feb|mar|apr|jun|jul|aug|sept|sep|oct|nov|dec)\b\.?"
    r"|\b(?:in|on|of|by|until|till|from|during|after|before|early|late|mid)\s+(?-i:May|March)\b\.?"
    r"|\b(?:mon|tues|wednes|thurs|fri|satur|sun)day\b\.?"
    r"|\b\d{1,2}\s*(?:st|nd|rd|th)\b",
    re.I)


# Who to ask: a role is a person in the answer as much as a name is. A who-question about a
# person in the world ("who invented the telephone") wants a name, and the name is a capital in
# the middle of the sentence; the first word of the reply is not counted, because a sentence
# opens with a capital whatever it says.
PERSON_WORD = re.compile(
    r"\b(?:vet|veterinar|doctor|gp|nurse|pharmacist|chemist|dentist|plumber|electrician|"
    r"gas safe|engineer|mechanic|solicitor|lawyer|adviser|advisor|accountant|broker|"
    r"landlord|letting agent|employer|hr|union|citizens advice|council|police|"
    r"someone|somebody|a professional|specialist|consultant|technician|builder|roofer|"
    r"physio|optician|midwife|health visitor|social services|ombudsman|registrar|"
    r"witness|referee|teacher|tutor|your bank|the bank|neighbour|neighbor)(?:s|es)?\b", re.I)
PERSON_NAME = re.compile(r"(?<=[a-z,;(]\s)[A-Z][a-z]{2,}")
# A who is answered with the relation more often than with a name: "whos coming with me" / "A
# friend - that is who you said you were going with", "who is older" / "You're older - 34 to your
# wife's 32". The people in the reply are the answer, whether named as a role or as one of theirs.
PERSON_RELATION = re.compile(
    r"\b(?:mum|mom|mam|dad|mother|father|son|daughter|sister|brother|wife|husband|partner|"
    r"friend|mate|boyfriend|girlfriend|fianc\w*|neighbou?r|boss|colleague|"
    # The person a who is answered with at work is the manager far more often than the boss, and
    # "who do i ask about it" answered "Your manager, in writing" was read as giving no person at
    # all: the role was in none of the words. The words are the roles a manager is named by.
    r"manager|supervisor|team leader|line manager|head of (?:year|department|team)|"
    r"child|kid|baby|"
    r"gran|grandma|grandad|granny|nan|aunt|uncle|cousin|step(?:son|daughter|mum|dad)|"
    r"in-laws?|twins?)\b", re.I)
# A who is often answered with the party and no name at all: "who do i call about a broken lock" /
# "A locksmith, and ask what it costs to open the door", "who do i complain to" / "it is the
# retailer you go back to". The party is a role - someone who does the thing, spelt with the
# endings English gives a doer (-er, -or, -ist, -ian, -ant, -smith, -minder, -wright) - or an office
# that acts as one. A closed list of roles missed the locksmith and the childminder while answering
# for the plumber and the vet, so the shape does the work here, and only the words that wear a
# doer's ending without naming anyone are kept out.
_ROLE_ENDS = r"[a-z]{3,}(?:er|or|ist|ian|ant|smith|minder|wright)"
_ROLE_OFFICES = r"(?:council|company|authority|agency|department|office|service|board|team)"
_NOT_A_ROLE = frozenset((
    "power", "water", "answer", "number", "other", "order", "letter", "paper", "dinner", "offer",
    "cover", "corner", "member", "record", "filter", "computer", "calendar", "character",
))
# The role has to be the reply's subject, not a thing in a list: a who is answered by "<role>, and
# ask ..." or "<role>'s job", and "a list of things" is neither. So the role counts when a comma, a
# possessive or a colon stands behind it, which is how an answer opens on the party.
_PARTY = re.compile(
    r"\b(?:a|an|the|your|our|their|his|her|my)\s+(?:[a-z-]+\s+){0,2}?" + _ROLE_ENDS
    + r"(?=\s*(?:,|'s|:))"
    r"|\b(?:a|an|the|your|our|their)\s+(?:[a-z-]+\s+){0,2}?" + _ROLE_OFFICES + r"\b", re.I)


def _a_party(opening):
    """True when the opening names the party as a role or an office, not as a thing."""
    for found in _PARTY.finditer(opening):
        if found.group(0).split()[-1].lower() not in _NOT_A_ROLE:
            return True
    return False


# "Sue is your childminder." answers "who is sue", and the name opens the sentence - the one
# capital `PERSON_NAME` will not count, because a sentence opens with a capital whatever it says.
# A name is the answer when the sentence goes on to say what the person is to the person asking.
PERSON_NAMED = re.compile(
    r"^[A-Z][a-z]{2,}\s+(?:is|was|'s)\s+(?:your|our|his|her|their)\s+[a-z]+", re.I)
# A who is answered with the name so often that the reply opens on it: "who plays john wick" /
# "Keanu Reeves plays John Wick", "who was henry the eighth" / "Henry VIII (1491-1547) was king of
# England". `PERSON_NAME` will not count a capital at the start of a sentence, so a name is read
# there when a second capital stands right behind it - which is what a person's name does and what
# "About 20 minutes" or "The council empties it" does not.
# The second capital has to be a name word, or the regnal number of one: "Reeves" and "VIII" are,
# and "Vitamin D helps the body absorb calcium" is not - a who about vitamin D was credited with a
# name because a lone capital stood behind the first word. One letter is never a name here.
PERSON_FULL_NAME = re.compile(r"^[A-Z][a-z]{2,}\s+(?:[A-Z][a-z]{2,}|[IVXLC]{2,})\b")

MEANS = re.compile(
    r"\b(?:means|meaning|stands for|is short for|refers to|is when|is what|"
    r"is (?:a|an|the)\s+\w+|are (?:a|an|the)\s+\w+|is called|called|is basically|"
    r"is just|is simply|is the (?:name|word|yearly|total|amount|cost|price|process))\b"
    # A thing that is over, or one told as history, is defined in the past tense: "explain the
    # "what does gracias mean" / "That is Spanish for 'thank you'": a word given in another
    # language is a definition too, and it is said about the English word rather than as
    # "<word> is <word>", so the language and the quoted word are what mark it.
    r"|\b(?:is|are|means)\s+(?:\w+\s+)?for\s+[\"'\u201c\u2018]", re.I)


# "<thing> is a <kind of thing>": "Rice is a staple food in many countries". This one form of
# MEANS turns into a verdict when a pronoun opens it, because the pronoun points back at
# something already named: "That is a real weight, and it sits on sleep" is about the person\u2019s
# own figure and it defines nothing. The rest of MEANS is a word doing the defining - "means",
# "stands for", "is called" - and a pronoun does not change what those say.
MEANS_ARTICLE = re.compile(r"^(?:is|are) (?:a|an|the)\s+\w+", re.I)


# A definition of a verb is said with two infinitives: "To catfish is to invent an online
# identity to draw someone into a relationship", "To reiterate is to say something again".
# Neither half carries an article, so DEFINES misses it and the answer read as a miss.
MEANS_INFINITIVE = re.compile(r"^to\s+\w+\s+(?:is|means)\s+to\s+\w+", re.I)


# "where did i decide to go" -> "You settled on spain." A reply that names what the person chose
# is the where, and the name is in their own spelling, so it carries no capital to go by.
SETTLED_ON = re.compile(
    r"\byou (?:settled on|decided on|went for|opted for|chose|picked|plumped for|said|mentioned|"
    r"told me)\b", re.I)


# A place that is a spot on the thing itself, named with no place word in it: "where is the
# serial number on my fridge" / "It is on a plate or sticker you can read without moving the
# machine: on a boiler, under the case near the pipes, behind the drop-down flap". Every one of
# those is where the thing is, and none is a shop, a named town or a choice the person made, so
# the three readings above saw no place at all. What marks a spot is a preposition of place and a
# determiner: "on a plate", "under the case", "behind the flap", "inside the lid". `where` asks
# nothing else of a reply except a spot or a time, so the time nouns are stopped below.
SPOT_ON_THE_THING = re.compile(
    r"\b(?:in|on|under|underneath|behind|inside|beneath|beside|alongside|next to|on top of|"
    r"just under|just behind|halfway up|partway up)\s+"
    r"(?:the|a|an|its|your|each|either|one)\s+([\w'-]+)", re.I)
# The noun after the preposition is what tells a spot from the same shape used for something else:
# "on a plate", "under the case" and "behind the flap" are where the thing is, while "in a US
# study", "on an iPhone", "on a GBP200,000 home" and "in a bowl, mix the flour" are a source, a
# device, a price and a method. Nothing in the shape separates them, so the parts of a thing are
# named, the way `PLACE_WORD` names the places: a spot on a thing is one of its own parts.
SPOT_PART = frozenset("""
plate plates sticker stickers label labels badge case casing housing shell body flap lid cover
panel door doors seal seals drawer box compartment slot port socket plug valve hose pipe tube
drum filter cartridge cap knob handle handles shelf rack tray trays wand bag packaging manual
leaflet screen dial switch button hinge underside underside base bottom top side sides back
front rear corner edge middle centre center bracket clamp nut bolt screw seam cord cable wire
spout nozzle brush blade bar rim trim guard grille vent clip strap tie
""".split())


# "on the back of the machine", "at the bottom of the box", "in the middle of the lid": the spot
# is the side of the thing, and the side word on its own ("on the back") would be read as a stop
# noun, so the "of" form is matched whole and first.
SPOT_OF_THE_THING = re.compile(
    r"\b(?:on|at|in|under|near)\s+the\s+(?:back|front|top|bottom|side|underside|base|rear|"
    r"middle|centre|center|corner)\s+of\s+(?:the|a|an|its|your)\s+[\w'-]+", re.I)


def _the_spot_a_thing_has(found):
    """The part named after the preposition, or None."""
    if not found:
        return None
    return found.group(1).lower().strip("'-")


def _names_a_spot(opening):
    """True when the reply says where on the thing it is: "on a plate", "under the case"."""
    if SPOT_OF_THE_THING.search(opening or ""):
        return True
    for found in SPOT_ON_THE_THING.finditer(opening or ""):
        if _the_spot_a_thing_has(found) in SPOT_PART:
            return True
    return False


def _a_place(opening):
    opening = CALENDAR_WORD.sub(" ", opening)
    return bool(PLACE_WORD.search(opening) or PLACE_NAME.search(opening)
                or len(PLACE_NAME_ANY.findall(opening)) >= 2 or SETTLED_ON.search(opening)
                or _names_a_spot(opening)
                or PLACE_KIND.search(opening) or PLACE_AT_HOME.search(opening))


def _a_person(opening):
    opening = CALENDAR_WORD.sub(" ", opening)
    if PERSON_RELATION.search(opening):
        return True
    if _a_party(opening) or PERSON_NAMED.search(opening) or PERSON_FULL_NAME.match(opening):
        return True
    return bool(PERSON_WORD.search(opening) or PERSON_NAME.search(opening))


# The plainest definition in English is "<thing> is <description>", with no article and no
# "means": "Granita is fruit juice or coffee", "Carbohydrates are one of the main food groups",
# "Your mum is vegetarian". A pronoun before the verb is not a definition - "It is fine" is a
# verdict about something already named.
# "That is a real weight, and it sits on sleep" is a judgement about something already named,
# not a definition of it: the pronoun points back, and the opinion adjective is what the
# sentence predicates. A pronoun on its own is not enough - "It is the period when a club can
# register new players" answers "what is a transfer window", and "a period when..." is a kind,
# not an opinion. Only the adjectives a person uses to judge a thing are listed.
A_JUDGEMENT = re.compile(
    r"^\s*(?:it|that|this|they|these|those|there|he|she|you|we|i)\s+(?:is|are|was|were)\s+"
    r"(?:a|an|the)\s+(?:real|good|nice|fine|great|bad|big|small|awful|lovely|honest|fair|"
    r"decent|brilliant|rubbish|terrible|wonderful|amazing|perfect|silly|daft|sad|happy|"
    r"serious|proper|big|tough|hard|easy|common|rare)\s+\w+", re.I)


DEFINES = re.compile(
    # `do`/`did`/`does` are in the list because "Did you mean your son?" is a clarification
    # question, not a definition, and `mean` is now a defining verb here.
    r"^(?!\s*(?:it|that|this|they|these|those|there|he|she|i|we|you|what|which|here|so|and|but|"
    r"do|did|does|don'?t|doesn'?t|didn'?t)\b)"
    # A definition is usually the thing and then `is`, but not always: "A cone has one circular base
    # and a curved side that comes to a point", "A solid has a fixed shape and a fixed volume", "A
    # cylinder has two flat circular ends". `has` is how a thing is described by what it carries, and
    # the check read those two answers to "what is a cone" and "what is a solid" as misses. Only
    # when `gives` already knows the line asked for a meaning, so a has-sentence elsewhere is
    # untouched, and the opening cannot be `it has` - the lookahead above drops that. A `has to`
    # or `have to` is an obligation, not a thing's parts: "An odometer has to be working for the
    # MOT" answers a rule about one, and it is not what the thing is.
    # `mean` is the other verb a definition uses, and it is the plural that says it when the line
    # named two things: "what is a write off car" / "Both mean an insurer wrote the car off instead
    # of repairing it". The `has to` obligation is what the lookahead below drops, so it is kept on
    # `has`/`have` alone: "To reiterate is to say something again" is a definition, and an `is to`
    # that follows the subject is how one is said.
    # Both verbs sit inside one group so the lookahead above guards both of them: with `has|have`
    # outside it, "They have a thick coat" and "That has a hook on the back" were read as
    # definitions, and the pronoun subject is exactly what makes a sentence something other than
    # what the thing is (spare-juniper, #13159).
    r"(?:[\w'\u2019-]+(?:\s+[\w'\u2019-]+){0,4}\s+(?:is|are|mean|means)\b"
    r"|[\w'\u2019-]+(?:\s+[\w'\u2019-]+){0,4}\s+(?:has|have)\b(?!\s+to\b))", re.I)


# A thing defined by what it does: "what is a food bank" / "Food banks give a few days of free
# food, and most ask for a referral". The subject and its verb are the opening, so this is read
# from the first few words only - "both give you a crisp base" inside a method is not a meaning.
MEANS_BY_DOING = re.compile(
    r"^(?:\w+ ){0,3}(?:give|gives|provide|provides|let|lets|allow|allows|help|helps|names)\s+"
    r"(?:you|a|an|some|free|people|anyone)\b", re.I)


# A mechanism is a meaning told as the thing's parts and what they do: "A pin-tumbler lock has
# pairs of pins resting across the plug", "A hiccup is a sudden spasm of the diaphragm".
MECHANISM = re.compile(
    r"\bis how\b|\bworks? by\b|\bworks? like\b|\bworks? because\b|"
    r"^(?:(?:the|a|an)\s+[\w'\u2019-]+(?:\s+[\w'\u2019-]+){0,3}\s+|it\s+)"
    # A `has to` is an obligation, not a thing's parts: "An odometer has to be working for the MOT"
    # answers a rule about one, and it is not what the thing is.
    r"(?:has|have)(?!\s+to\b)|(?:uses|consists of|contains|comes from|breaks|pulls|pushes|turns|"
    r"carries|draws|"
    r"sucks|lifts|heats|cools|reacts|sends|absorbs|filters|"
    # what a mechanism is asked about is often told as the thing doing its job: "A fridge moves
    # heat out of the inside and dumps it at the back", "A spring stores energy by bending steel",
    # "It fills the drum, tumbles the clothes through hot water and pumps it away".
    r"moves|moved|stores|dumps|spins|tumbles|bends|drives|releases|fills|pumps|blows|burns|"
    r"melts|freezes|bounces|blocks|traps|spreads|grows|charges|recharges|squeezes|stretches|"
    r"swings|shakes|rotates|grinds|crushes|mixes|separates|holds|held|takes in|gives out)\b",
    re.I)


# A thing's origin told as the source and then what is done with it. See the ORIGIN_ASK arm in
# `gives`. The source is the subject, so `make it` is how the sentence says which thing it is
# about; a colon at the head names the source and opens the process; and a participle after the
# source ("boiled down until", "picked, then wilted") is the same telling.
SOURCE_MAKES = re.compile(
    r"^(?:\w[\w'\u2019-]*[ ,]+){1,6}(?:make|makes|made|lay|lays|laid|grow|grows|produce|produces|"
    r"give|gives)\s+(?:it|them)\b", re.I)
SOURCE_COLON = re.compile(r"^(?!\s*(?:it|that|this|there|they|you|we|i)\b)"
                          r"[\w'\u2019,()/-]+(?:\s+[\w'\u2019,()/-]+){1,7}:\s*\w", re.I)
SOURCE_MADE = re.compile(
    r"^[\w'\u2019,()-]+(?:\s+[\w'\u2019,()-]+){0,12},\s*(?:boiled|crushed|heated|picked|shorn|"
    r"wilted|dried|melted|grown|laid|dug|pressed|cooked|washed|cut|made|then|and then)\b", re.I)


# The source named and then doing its thing is the same telling without the colon or the
# participle: "Rain soaks into the ground and runs into rivers, and your tap water is drawn from
# a river". The verbs are the ones a material's own process is told with.
SOURCE_DOES = re.compile(
    r"^[\w'\u2019-]+(?:\s+[\w'\u2019-]+){0,3}\s+(?:soaks|runs|flows|comes|grows|forms|makes|"
    r"gives|produces|holds|carries|falls|melts|boils|ferments|rots|breaks|builds|lays)\b", re.I)


# "Flour, water, salt and yeast. The yeast gives off gas..." - the list of what the thing is made
# of, with no verb at all, is the answer to what it comes from.
SOURCE_LIST = re.compile(
    r"^(?!\s*(?:it|that|this|there|they|you|we|i)\b)[\w'\u2019-]+(?:,\s*[\w'\u2019-]+){2,}"
    r"(?:\s+and\s+[\w'\u2019-]+)?\b", re.I)


def _an_origin(opening):
    return bool(SOURCE_MAKES.match(opening) or SOURCE_COLON.match(opening)
                or SOURCE_MADE.match(opening) or SOURCE_DOES.match(opening)
                or SOURCE_LIST.match(opening))


# A definition says what the thing is, not how good it is. "That is a real weight, and it sits on
# sleep" is a verdict about a weight, and `MEANS` read "is a real" as "is a <thing>" and called it a
# definition. A subject that points at something already said - "that", "it", "this", "they" - with
# an opinion after the copula is a judgement, so the opinion is read before the copula is trusted.
# A named subject is not affected: "A student loan is a real debt" is still read by the shapes that
# name the thing, and "That's a type of pasta" says what the thing is, not what it is worth.
_OPINION_OF_THE_THING = re.compile(
    r"^(?:that|this|it|they|these|those|he|she|you|we)(?:'s|\u2019s| is| are| was| were)\s+"
    r"(?:a|an)\s+(?:real|proper|genuine|right|good|great|big|small|huge|little|nice|fair|tough|"
    r"hard|easy|lovely|brilliant|terrible|awful|total|complete|classic|common|usual|rare|"
    r"dangerous|safe|useful|useless|important|serious|key|major|minor|main|whole|full|"
    r"big|decent|solid|mucky|filthy|messy)\b", re.I)

# A definition told in the past tense: "explain the cold war" / "The Cold War was the long
# standoff between the United States and the Soviet Union". The article after the copula is what
# keeps "The pan was hot" out of it, and the subject before it is what keeps the rest: the same
# shape is every sentence about a pronoun or a dummy subject - "That was the whole of my answer on
# it", "Once there was a tortoise that could not sleep", "looked into even when IT WAS A one-off".
# A possessive is no better ("my answer was a mess"), because the thing the line named is the
# thing defined, never the speaker's.
PAST_DEFINES = re.compile(r"\b(?:was|were)\s+(?:a|an|the)\s+[a-z][\w'\u2019-]*", re.I)
NOT_A_SUBJECT = re.compile(
    r"(?:^|[^\w'\u2019-])(?:it|that|this|there|these|those|he|she|they|we|you|i|who|which|"
    r"what|one|none|everyone|someone|anyone|nobody|nothing|something|anything|everything|"
    r"my|your|his|her|its|our|their|mine|yours|theirs)$", re.I)


def _a_past_definition(opening):
    """True when the reply opens by defining a thing in the past tense. A pronoun or a dummy
    subject is never the thing being defined, so the words before the copula are read first."""
    found = PAST_DEFINES.search(opening)
    if not found:
        return False
    subject = re.split(r"[.;:!?,()\u2014]", opening[:found.start()])[-1].strip()
    if NOT_A_SUBJECT.search(subject):
        return False
    # the speaker's own thing is not the thing the line named: "My answer was a mess"
    return not re.match(r"(?:my|your|his|her|its|our|their|mine|yours|theirs)\b", subject, re.I)


def _a_meaning(opening):
    if _OPINION_OF_THE_THING.match(str(opening or "").strip()):
        return False
    if MECHANISM.search(opening):
        return True
    if MEANS_BY_DOING.match(opening) or MEANS_INFINITIVE.match(opening):
        return True
    if DEFINES.match(opening):
        return True
    hit = MEANS.search(opening)
    if hit is None:
        return False
    # The article form after an opinion is a judgement about the thing named, not a definition.
    if MEANS_ARTICLE.match(hit.group(0)) and A_JUDGEMENT.match(opening):
        return False
    return True


# ------------------------------------------------------------------------------- the shapes

# A verdict opens on the yes or the no itself: "Yes...", "No need...", "Straight in is fine",
# "It's fine", "You can", "Not worth it". The opening word is read, then a short list of frames
# that answer the yes/no without the words yes or no; anywhere past the opening a "not" or a
# "fine" is usually a detail, so the inside check is the opening's first clause only.
VERDICT_OPEN = re.compile(
    r"^(?:yes|yeah|yep|yup|no|nope|nah|not|never|don'?t|do not|doesn'?t|avoid|skip|sure|"
    r"definitely|absolutely|probably|usually|generally|normally|often|mostly|sometimes|"
    r"better|best|fine|safe|okay|ok|"
    r"it'?s|it is|that'?s|that is|they'?re|there'?s no|you'?re|you (?:can|could|should|don'?t|"
    r"do not|does not|did not|won'?t|can'?t|shouldn'?t|need|want|have to|must)|"
    # A no is often the other action named instead: "i left my chicken out overnight can i still
    # cook it" / "Bin it, I'm afraid."
    r"bin|throw|chuck|toss|dump|discard|refrain|"
    r"none|nothing|straight|warm|cold|plain|just|"
    # "is my data safe with you" / "Private to this chat.": the answer is the word for the thing
    # being kept to itself, and it is said instead of a yes.
    r"private|confidential|anonymous|between us)\b", re.I)
# A verdict said in the first person: "I would. Switch it off and leave it off", "I wouldn't
# bother with a new one", "I'd wait until the spring". The bot answers a should-I question this
# way a lot, and the yes or the no is in the first two words, so the rest of the sentence can be
# the reason or the method. Not "I would only repeat myself", which says nothing about the doing.
FIRST_PERSON_VERDICT = re.compile(
    r"^i (?:would|wouldn'?t|do|don'?t|will|won'?t)\b(?!\s+(?:only|just|rather|say that))"
    r"|^i'?d (?:say|skip|wait|hold off|bother|not bother|avoid|keep|leave|go for|get|change|"
    r"stick with|try)\b", re.I)


# The verdict said by confirming the figure or the plan the person restated: "Still right: lid
# on, bring it to the boil", "That's right", "Exactly". The confirmation is the yes, and a reply
# that opens on it has answered the "is 12 minutes right" it was asked. A bare "Right," is left
# out: it opens a new subject as often as it agrees, and a check that reads it as a yes hides
# the turns that have no answer.
ECHO_VERDICT = re.compile(
    r"^(?:(?:still|that'?s|that is|you'?re|you are|absolutely|dead) right|correct|exactly|"
    r"spot on)\b", re.I)
# A judgement said as a position in a band rather than as "yes": "is it normal that a 5 year old
# cant write his name" / "Late but still inside normal, and worth a light touch rather than a
# push", "is my blood pressure ok" / "120 over 80 is inside the normal range", and the no the same
# way - "outside the normal range for a first tooth". Nothing else reads it: "inside normal" is not
# "is normal", and the band is the whole of what was asked. Read on its own as well as inside
# `VERDICT_INSIDE`, because the band is also how the bot judges a figure it has just worked out.
VERDICT_BAND = re.compile(
    # Inside, within or outside - not over or under, which are how a condition is described rather
    # than how a thing is judged: "Under normal circumstances it should reach 60C" is a statement
    # about the boiler's working, not the answer to "is my boiler working". A condition is ruled
    # out wherever it follows, because "within normal use" is the same statement.
    r"(?:inside|within|outside)\s+(?:the\s+|well\s+)?"
    r"(?:normal|usual|average|expected|recommended|accepted|healthy)\b"
    r"(?!\s*(?:use|uses|conditions?|circumstances?|operation|working|service|wear|load))"
    # A band is also named with the range words, and there the prepositions above and below are the
    # judgement itself: "just above the recommended range", "outside the band".
    r"|(?:inside|within|outside|above|below|over|under)\s+the\s+"
    r"(?:range|band|limits?)\b"
    r"|(?:above|below|over|under)\s+the\s+(?:normal|usual|recommended|expected)\b"
    r"|within reach\b", re.I)
# A judgement is a verdict without the words yes or no: "Spotting blood for the first day is
# normal", "it suits most kitchens", "the cheap one works". The first clause only, because a
# "fine" in the second half is a detail rather than the answer.
VERDICT_INSIDE = re.compile(
    r"\b(?:yes|no need|not really|not worth|worth it|isn'?t worth|a bad idea|a good idea|"
    # "A washing machine is worth repairing while the quote is under half the price of a new one",
    # "Worth having it looked at today". The worth is said about the doing rather than as "worth
    # it", and it is still the verdict the person asked for.
    r"\bworth (?:repairing|fixing|doing|buying|getting|having|paying|spending|keeping|servicing|"
    r"replacing|renewing|hiring|installing|the money|the effort|a go)\b"
    # "A non-refundable rate usually means no cash back" answers "can I get a refund" with the
    # verdict inside the rule rather than at the front of it.
    r"|\bmeans (?:no|yes|not)\b|"
    # "Marmite keeps for years", "an unopened tub keeps about a week past the date": the answer
    # to "does it go off" is how long it keeps, so the keeping is the verdict.
    r"\b(?:keeps?|lasts?) (?:for|until|about|roughly|easily|well|a couple|a few|a good|\d)\b|"
    # The two quality arms stay out of this list: a quality word names whatever noun is nearest,
    # so both need the line as well as the reply. See `_the_quality_answers`.
    r"harmless|safe|fine|okay|avoid|go ahead|of course|by law|make sure|only|"
    # "is that a sign of anything" / "Some forgetting is ordinary with age": the ordinary is the
    # verdict, and it is the word people use for it.
    r"is (?:normal|common|usual|typical|expected|ordinary|fine|safe|okay|harmless|allowed|legal)|"
    # "Lisbon is good with children if you take the trams": a verdict said about a fit.
    r"is (?:good|fine|ok|okay|great|safe|bad) (?:with|at|for|in)\b|"
    r"is (?:usually|normally|generally|probably|often) (?:just |fine|normal|harmless|safe|okay)|"
    # "is it cheaper to buy a whole chicken than pieces" / "A whole chicken is nearly always the
    # cheaper way to buy chicken": the verdict is which side comes out better, named as the
    # quality the line asked about. It is the yes, said as a comparison.
    r"\bis (?:almost |nearly )?(?:always |usually )?the (?:cheaper|cheapest|better|best|quicker|"
    r"quickest|easier|easiest|safer|safest|simpler|simplest) (?:way|option|choice|bet|buy|route|"
    r"one)\b|\b(?:works? out|comes? out|turns? out) (?:cheaper|cheapest|better|best|quicker|"
    r"easier|safer)\b|"
    r"suits|works well|works fine|no harm|nothing wrong|nothing to worry|"

    r"you'?ll be fine|it depends|not (?:a problem|necessary|needed|allowed)|"
    # The verdict often comes after the condition it applies to: "Under an hour you do not need to
    # carry anything", "for a week, you don't need to do anything". It is one clause, so the answer
    # is in it.
    r"(?:do not|does not|don'?t|doesn'?t) need\b|"
    # A no is often the verb of the question negated rather than the word "no": "does vinegar go
    # off" / "Vinegar does not go off: it keeps for years", "would a voucher be lazy" / "A voucher
    # is not a cop out". Present tense only, and no bare imperatives: "Don't crowd the pan" is
    # advice rather than a verdict and stays unread.
    r"(?:is|are|does) not\b|\b(?:isn'?t|aren'?t|doesn'?t)\b|"
    # A judgement said with the adjective instead of a yes: "smoked cannabis is harmful", "it
    # is unhealthy, but", "salt is fine in small amounts". The bot answers "is it bad for me"
    # with the verdict word itself far more often than with "yes", and the verdict is there.
    r"harmful|unhealthy|healthy|bad for|good for|not good for|risky|dangerous|unsafe|not safe|"
    r"a lot|too much|too late|not enough|plenty|worth (?:a go|doing)|the one to (?:pick|avoid))\b"
    # A judgement said as a position in a band rather than as "yes": "is it normal that a 5 year
    # old cant write his name" / "Late but still inside normal, and worth a light touch rather
    # than a push", "is my blood pressure ok" / "120 over 80 is inside the normal range", and the
    # no the same way - "outside the normal range for a first tooth". Nothing above reads it:
    # "inside normal" is not "is normal", and the band is the whole of what was asked.
    # The band is a judgement too - see `VERDICT_BAND`. It is spliced in because the arm is read on
    # its own as well, for the sentence after a figure the bot has just worked out.
    r"|" + VERDICT_BAND.pattern + r"",
    re.I)
# A yes said as what the thing itself is: "is passive smoking bad for children" / "Secondhand
# smoke is a real risk, not a smell: it carries the same tar, carbon monoxide and carcinogens".
# The word the line asked about is a harm, and the reply names the thing as one rather than saying
# "yes", which is the verdict said the other way round. The qualifier is what makes it a verdict:
# "is a real risk", "is a serious hazard", "is a major problem" name what the thing is, while
# "there is a risk either way" and "that carries a risk" weigh something instead.
A_HARM_IS_WHAT_IT_IS = re.compile(
    r"\b(?:is|are|was|were) (?:a|an) (?:real|serious|genuine|proper|major|big|known|health|"
    r"significant|grave) (?:risk|hazard|danger|problem|no-no)\b", re.I)
# A judgement of the thing asked about, said with the quality the line asked for instead of a
# yes: "is google maps free" / "Google Maps is free", "is new york good with children" / "New York
# is great with children who can keep going". Both this and `IT_HELPS` name whatever noun is
# nearest - "is it worth appealing the ticket" / "The form is free to download" is about the form
# - so both are read against the line in `_the_quality_answers` rather than counted on their own.
QUALITY_IS = re.compile(
    r"\bis (?:really |very |always |usually )?(?:great|good|fine|perfect|brilliant|lovely|ideal|"
    r"free|cheap|easy|worth it|worthwhile)\b", re.I)
# "does white noise work for babies" / "so it helps most in a shared or noisy room", "should i use
# a white noise machine" / the same reply: the pronoun stands for the thing asked about, and it is
# the yes when the line is asking whether that thing is any good.
IT_HELPS = re.compile(r"\b(?:it|this) (?:really |usually |often )?(?:helps?|works?)\b", re.I)
_WORKING = re.compile(r"\b(?:work|works|working|worked|help|helps|helping|use|using|used|worth|bother|good)\b", re.I)
# The subject of a quality said without naming the thing again: "so it is fine", "they are cheap".
_PRONOUN_SUBJECT = frozenset(("it", "this", "that", "they", "these", "those", "he", "she"))


def _the_quality_is_about_the_thing(clause, line):
    """True when the subject of "is great/free/cheap" is the thing the line asks about.

    A quality word is a verdict about whatever noun is nearest, and the nearest noun is often the
    wrong one: "is it worth appealing the ticket" / "The form is free to download, but the appeal
    usually loses" answers with a quality of the form. So the subject of the quality has to be the
    thing the line named, or the pronoun standing in for it ("so it is fine" after "is it ok").
    """
    found = QUALITY_IS.search(clause)
    if not found:
        return False
    subject = clause[:found.start()].strip()
    if not subject:
        # "Fine for a week in the fridge": the quality opens the sentence with nothing before it.
        return True
    words = _words(subject)
    if words and words[-1] in _PRONOUN_SUBJECT:
        return True
    said = _line_text(line)
    if not said:
        return True
    named = {w for w in words if len(w) >= 4 and w not in _EMPTY}
    return not named or any(w in said for w in named)


def _the_tail_says_what_it_is_about(clause, line):
    """True when the verdict in the setup's tail is said about the thing the line asked about.

    A tail verdict counts when the clause says what it judges: "is my mince gone off" / "Red meat
    is more forgiving than chicken: a grey-brown colour on the outside of a chop is just air and it
    is fine". "should i pop it" / "A smooth lump on the back of the wrist is usually a ganglion
    cyst: harmless, often smaller after a few weeks" says a quality of nothing - the thing is
    harmless, but the reply never says the blister is - and that is a wrong reply, not a verdict
    (young-latch's find).

    A named subject is not enough on its own, because the tail is often a detail rather than the
    verdict: "can i put my glasses in the washing machine" / "... load it so a hand fits flat on
    top of the pile - a packed drum does not rinse" matched the negation in "a packed drum does
    not rinse", "is it worth buying a diesel now" / "There is no fixed figure: the forecourt sign
    is the only price that matters" matched "only", and "is that normal" / "... quotes ... tell
    you whether a figure is normal" matched "is normal" while naming a test rather than giving
    one. So the subject has to be the pronoun standing in for the line's thing, or a word the line
    named, the same reading the quality arms use.
    """
    found = VERDICT_INSIDE.search(clause)
    if not found:
        return False
    subject = clause[:found.start()].strip()
    if not subject:
        return False
    words = _words(subject)
    if words and words[-1] in _PRONOUN_SUBJECT:
        return True
    said = _line_text(line)
    if not said:
        return True
    named = {w for w in words if len(w) >= 3 and w not in _EMPTY}
    return bool(named) and any(_the_same_word(w, said) for w in named)


# "is it normal that a 5 year old cant write his name", "is it safe to ...", "is it worth it",
# "is this ok": the line asks about one quality by name, and the reply is the answer when it uses
# that same word, whatever the construction. "Late but still inside normal, and worth a light
# touch rather than a push" answers the line above and never says "it is", so `QUALITY_IS` - which
# wants a copula - read it as no quality at all, and the reply was called a pick because of the
# "rather than" behind it. Only the word the person asked about counts, six words in, so a reply
# that praises a different quality does not travel on this.
ASKS_ABOUT_A_QUALITY = re.compile(r"\b(?:is|are|was|were|isn'?t|aren'?t)\b", re.I)
_QUALITIES = ("worth it", "worthwhile", "normal", "typical", "ordinary", "common", "okay", "ok",
              "safe", "alright", "legal", "allowed", "healthy", "necessary", "essential", "fine")
_QUALITY_SAID = {q: re.compile(r"\b%s\b" % re.escape(q), re.I) for q in _QUALITIES}
_THE_VERDICT_IS_EARLY = 12


def _the_quality_it_was_asked_about(opening, said):
    """True when the line asked "is it <quality>" and the opening says <quality> of it.

    The word has to be near the head of the reply, where the verdict lives: "worth fixing, and
    cheap" is the answer to "is it worth fixing", while a "worth" in a closing aside is not.
    """
    # "is that normal", "is it safe": the line names no thing for the reply's quality to be read
    # against, so the reply's own subject is the line's thing. The subject guard has nothing to
    # compare in these lines and was refusing every reply.
    named = {w for w in _words(said)
             if len(w) >= 4 and w not in _EMPTY and w not in NOT_A_THING
             and w not in {x for q in _QUALITIES for x in q.split()}}
    if not named and said and ASKS_ABOUT_A_QUALITY.search(said):
        asked = " ".join(_words(opening)[:_THE_VERDICT_IS_EARLY])
        return any(_QUALITY_SAID[q].search(asked) for q in _QUALITIES)
    if not said or not ASKS_ABOUT_A_QUALITY.search(said):
        return False
    head = " ".join(_words(opening)[:_THE_VERDICT_IS_EARLY])
    for quality in _QUALITIES:
        found = _QUALITY_SAID[quality].search(head)
        if not (found and _QUALITY_SAID[quality].search(said)):
            continue
        if quality in _QUALITY_OF_A_THING and not _the_quality_is_said_of_the_thing(
                head, found.start(), said):
            continue
        return True
    return False


# "worth it" is said of doing the thing, not of a noun: "is a pension worth it" / "Nobody adds to
# it but you, so it is worth it only as a tax deal" is the verdict whatever the opening names. The
# adjectives are said of a thing, so they are the ones the subject is read for.
_QUALITY_OF_A_THING = frozenset(q for q in _QUALITIES if q not in ("worth it", "worthwhile"))
# The copulas a quality is said with: "a lively dog is normal", "it was fine", "it isn't safe".
_COPULA = frozenset(("is", "are", "was", "were", "isnt", "arent", "wasnt", "werent", "be", "feels",
                     "feel", "looks", "look", "seems", "seem", "sounds", "sound", "gets", "stays"))


def _the_quality_is_said_of_the_thing(head, at, said):
    """True when the quality at `found` is said of the line's own thing.

    A quality word is a verdict about whatever the nearest noun is, and the nearest noun is
    sometimes another thing altogether: "my cat is flat out all day, is that normal" / "Dogs need
    a walk every day, so a lively dog is normal" is a quality of a dog, and the check read it as
    the verdict for a question about a cat. The same words with a pronoun for the subject - "so
    they are normal" - say the quality of whatever "they" is, so the reply also has to name
    something the line named before that counts.

    A quality with no copula in front of it is the verdict itself and is left alone: "Late but
    still inside normal, and worth a light touch rather than a push" answers "is it normal that a
    5 year old cant write his name" and names no subject at all.
    """
    words = head[:at].split()
    if not words or words[-1] not in _COPULA:
        return True
    subject = [w for w in words[:-1] if w.isalpha()]
    if not subject:
        return True
    if subject[-1] in _PRONOUN_SUBJECT:
        return bool(said) and _about_the_thing_the_line_named(head, said)
    if not said:
        return True
    return any(w in said for w in subject[-2:])


# The quality in `VERDICT_INSIDE` names whatever noun is nearest, exactly like the two quality arms,
# and the nearest noun is sometimes another thing: "my cat is flat out all day, is that normal" was
# credited by "After a long walk or a big day that is normal, so let him sleep it off". The rest of
# the arm - the worth, the keeping, the "means no", the "no need" - says nothing about a subject,
# so only this alternative is read against the line.
VERDICT_INSIDE_QUALITY = re.compile(
    r"\bis (?P<q>normal|common|usual|typical|expected|fine|safe|okay|harmless|allowed|legal)\b",
    re.I)


def _the_verdict_is_inside(clause, line):
    """`VERDICT_INSIDE`, with a bare quality read against the thing the line names."""
    found = VERDICT_INSIDE_QUALITY.search(clause)
    if found is None:
        return bool(VERDICT_INSIDE.search(clause))
    at = clause.index(found.group("q"), found.start())
    if _the_quality_is_said_of_the_thing(clause, at, line or ""):
        return True
    rest = clause[:found.start()] + " " + clause[found.end():]
    return bool(VERDICT_INSIDE.search(rest))


def _the_quality_answers(clause, line):
    """The two quality arms, read against the line: see `QUALITY_IS` and `IT_HELPS`."""
    if _the_quality_is_about_the_thing(clause, line):
        return True
    return bool(IT_HELPS.search(clause) and _WORKING.search(_line_text(line)))


# A hedge is not an answer of any kind. These openings borrow the words of a shape ("it is...",
# "the steps...") while saying that the bot has nothing, so no check may count them.
PUNT = re.compile(
    r"^(?:i'?m not sure|i am not sure|i don'?t know|i do not know|i can'?t|i cannot|can'?t call|"
    r"that'?s beyond|that is beyond|that'?s all|that is all|there is no more|"
    r"beyond what i know|not mine to|not a call|not one i can call|a quick search|searching for|"
    r"i'?d rather not|"
    r"you haven't told me|that'?s a good question|good question|no idea|not something i|"
    # "No figure from me on that, sorry: it moves with where you are and when you go" says the bot
    # has nothing, and it opens on "No", so it read as a verdict on every yes/no line and as a
    # method on every "how do i" one. Whatever shape word it borrows is the same shrug.
    r"no (?:figure|number|price|answer|idea|verdict|view|opinion|guess) from me|"
    # The same shrug with any noun after it: "No verdict from me on that one yet" is the bot saying
    # it has nothing, in the one word this list did not know, and it read as the verdict on "is
    # that bad". And a reply that asks the person to say the question again has answered nothing:
    # "Say what you are asking about and I'll answer it properly rather than guess" was credited as
    # a yes or a no. Only the asking form counts - "Say the short version" and "Say the one thing
    # that matters first" are the answer itself.
    # ...the asking form only: the punt is "Say what you are asking about and I'll answer it
    # properly rather than guess", where what has to be said is the person's own question.
    # "Say what they did and what it was worth to you: \"Thank you for the cover, it made the
    # difference\"" is the answer to "what do i write in a thank you card", an instruction about
    # somebody else's words, and the bare "say what" read it as the bot having nothing to give.
    r"say (?:what (?:you(?:'?re| are)? (?:asking|after|on about|worried about|unsure)|"
    r"you mean|you want to know|has you (?:asking|wondering))|which|that again|more|me more|"
    r"a bit more)\b|"
    r"tell me (?:what|which|more) (?:you|has|is|part)\b|"
    # "No first-hand knowledge of that one here, so no verdict from me" is the same shrug with the
    # bot's own knowledge as the noun, and it opens on "No", so it read as the verdict on a yes/no
    # line. The "no" is about what the bot has, not about the thing they asked.
    r"no (?:first[- ]hand )?(?:knowledge|idea|clue) (?:of|on|about|here|from me)\b|"
    # "Nothing in that says how serious it is. The step above is what moves it" is the bot saying it
    # has nothing to go on - the same shrug as "I don't know" - and it opens on "Nothing", so
    # `VERDICT_OPEN` read it as the verdict "no" on every yes/no line. The word "nothing" opens real
    # answers too ("Nothing to worry about" is a yes), so only the nothing *about what was said* is
    # the punt: it has to be about that, this or what you said, and it has to be saying, telling or
    # showing something.
    r"^nothing (?:in|about) (?:that|this|it|what you (?:said|told me|described))\b"
    r"[^.!?]{0,60}?\b(?:say|says|said|tell|tells|told|show|shows|showed|suggest|suggests|"
    r"indicate|indicates|go on)\b|"
    r"^nothing here (?:to go on|that (?:says|tells))\b|"
    # "Hard to put a scale on it. Doing the thing above is what makes the difference" is a refusal
    # with no words of its own to read a shape from: the bot is saying it cannot grade the thing.
    r"^hard to (?:put a (?:scale|number) on|say how|judge|tell how|gauge)\b|"
    r"i'?m not sure (?:what|how|which|whether|where) to|i'?m not sure without)", re.I)
# The same shrug in the shape's own clothes: a hand-off, or an admission that there is nothing more
# to say. These open the way a verdict does - "That's ...", "It's ..." - so `VERDICT_OPEN` counted
# them as one, though none of them says what to do. "That's your call, not mine" answers a
# "should i ..." with no verdict at all, "That's one for your GP rather than me" hands the question
# to somebody else, and "That is everything I have on that one, so I would only repeat myself" says
# the bot is out of things to say. The trick is not to add a word to the verdict list but to say
# that no shape may be read out of them, which is what `PUNT` is for.
HANDOFF = re.compile(
    r"^(?:(?:that'?s|that is|it'?s|it is) (?:your|a) call(?![a-z])|"
    r"not (?:a )?call (?:i|we) (?:can|could|would)|"
    r"(?:that'?s|that is) (?:one|a question|something) for (?:your|a|the)\b|"
    r"(?:that'?s|that is) (?:everything|all) i (?:have|know)\b|"
    # "That is not mine to answer, but I would ask them plainly rather than sit guessing" answers a
    # yes/no with no verdict and names why: it is not the bot's to call. The word after "not" is
    # what it will not do, so anything of that kind is the same shrug as "that's your call".
    r"(?:that'?s|that is|it'?s|it is) not (?:mine|for me) to (?:answer|say|tell|call|judge)\b|"
    r"i would only repeat myself|nothing more i can (?:say|add|tell)\b|"
    r"(?:that'?s|that is) not for me to|"
    # The judgement handed back: "Whether it is worth it comes down to the price against how much
    # you would use it, and that part is yours", "Only you can weigh that, and it comes down to the
    # ticket price against how long you would stay", "That is yours to weigh rather than mine".
    # Each one borrows the verdict's own words - "worth it", "comes down to" - and gives none, so
    # every "is it worth it" line read as answered when the bot had handed it back. The reply is
    # the same shrug as "that's your call", in a longer coat.
    r"whether (?:it|that|they|this|[0-9]+|[a-z]+) (?:is|are|was|will be|would be) "
    r"(?:worth|a lot|too much|too long|too far|any good|safe|normal|fine)\b|"
    # The figure held up against another: "Hold 120 against one more price for the same thing
    # before you decide; the pair tells you more than any rule of thumb" is the bot saying it
    # cannot call this, in the shape of a rule. "is 120 a lot" read as answered by it.
    r"hold (?:it|that|this|the price|[0-9]+)\b[^.]{0,30}\bagainst (?:one|another|a|other)\b|"
    r"only you can (?:weigh|judge|say|decide|call)\b|"
    r"(?:that'?s|that is|it'?s|it is) yours to (?:weigh|say|decide|call|judge)\b|"
    r"that part(?:'?s| is) (?:yours|up to you)\b|"
    r"(?:i'?ll|i will) leave (?:that|this|it) to (?:your|a|the|somebody|someone)\b)", re.I)


# The honest line of a doubt composer, in its three shapes: "I wouldn't call it a warning sign -
# the answer above is about getting it sorted, and that is the part that matters", "Nothing in that
# says how serious it is. The step above is what moves it", "Hard to put a scale on it. Doing the
# thing above is what makes the difference". Each declines to judge the thing and sends the person
# back to the answer it has already given, so it is a punt whatever shape the line asked for - and
# two of the three open the way a verdict does ("I wouldn't call it...", "Nothing in that..."), so a
# yes/no ask counted them as the verdict and the card that had the figure in it stood down to them.
# Both halves are needed: a real answer can end "and the step above is what moves it" after its own
# verdict, and only the opening that *starts* by declining to judge is the punt.
REFERS_BACK = re.compile(
    r"^\s*(?:i wouldn'?t call|i would not call|nothing in that|hard to|no way to|not something i "
    r"can)\b[^.!?]{0,80}?\b(?:answer|step|thing|doing) above\b", re.I)


def is_a_punt(opening):
    """True when the reply's opening says the bot has nothing to give, in whatever clothes.

    Every shape check asks this first, so a hand-off is never a figure, a place, a method or a
    verdict, whatever words follow it.
    """
    return bool(PUNT.match(opening) or HANDOFF.match(opening)
                or REFERS_BACK.match(opening))

# A hand-off that does give something: the reply names the source that holds the answer, and that
# source is one only the person can open - their council's bin-day page, the Met Office page for
# their postcode, the label in the garment. "Your council's bin-day page will say: put your
# postcode in and it gives the day for your street" is the whole of what anyone can say about a
# bin day, and every shape check read it as a miss because it carries no day. It is not a figure,
# a place or a method either, so it is None: the reply is as good as the question allows, and a
# miss would stand it down for a worse candidate.
SOURCE = (r"(?:page|web ?site|site|app|account|portal|label|packet|packaging|manual|instructions|"
          r"leaflet|paperwork|statement|bill|letter|receipt|booking|policy|schedule|timetable|"
          r"council|gp|doctor|dentist|vet|surgery|pharmacy|provider|supplier|landlord|employer|"
          r"insurer|bank|met office|forecast|meter)")
# The source is named and it carries the answer in the same sentence. A shrug that says "look it
# up" names no source, and a reply that names one has done all it can: naming the source is the
# answer to a question only that source can settle.
DIRECTED = re.compile(
    r"\b(?:your|their|its|the)\b[^.!?]{0,40}\b" + SOURCE + r"\b[^.!?]{0,60}\b(?:will|would|"
    r"should|can|does)\s+(?:say|tell|show|give|have|confirm|list|explain)\b"
    r"|\b" + SOURCE + r"\b[^.!?]{0,40}\b(?:has|have|carries|lists|shows|gives)\s+"
    r"(?:it|them|you|the (?:day|date|time|figure|price|number|amount|answer|rate))\b", re.I)


# A hand-off names the holder the person can open, and the holder carries the thing: "A weather app
# has today's for your postcode", "the reference number they gave you brings it up on their site",
# "their own page or listing has today's". DIRECTED wants the verb and the pronoun in one shape and
# misses those, so the holder itself is read too. What stays a punt is a reply that sends the person
# to a search and nobody in particular - PUNT already owns those words.
A_HOLDER = re.compile(
    r"\b(?:your|their|its|the|a|an)\b[^.!?]{0,30}\b(?:app|e-?mail|bill|statement|account|page|"
    r"web ?site|site|letter|receipt|label|packet|packaging|manual|instructions|paperwork|booking|"
    r"confirmation|tracking|policy|meter|portal|reference number)\b", re.I)


def is_directed(opening):
    """True when the opening sends the person to a source that holds the answer and names it."""
    return bool(DIRECTED.search(opening))


# A question back is not an answer. "When is your birthday?" answered "When is your birthday? You've
# not said, so only you know - tell me and I'll remember it.", and the question was credited as a
# time for it; "what should i wear tonight" was answered "Where are you off to, and how long will you
# be out? That decides more of it than the clothes do." and the question was credited as a pick. The
# person asked and the bot asked them back, so the reply gives nothing, whatever shape it borrows.
#
# Three things keep that from swallowing answers that only look like questions:
#  - a question mark inside a quotation is not the end of a sentence. "can i have the day off on
#    friday" is answered "Yes, if you ask early and name the dates: "Could I take 12-16 May off? ..."
#    and the mark there belongs to the example, not to the reply;
#  - a question that only gives the person's own words back before the answer - "Changed your mind?
#    Bought online, by phone or by post, you have 14 days ..." - is the opening of an answer, so a
#    question whose content words are all in the line is not this;
#  - a restatement of the question ("What is a mortgage? It is a loan ...") is the same test: its
#    words are the line's words, so it is spared with the echo, and a question whose words are not
#    the line's ("How old is he?" for "how old is he" is, but "Is there one thing you can check?")
#    is the one that counts.
_A_QUOTE = "\"\u201c\u201d"
_NOT_A_WORD = frozenset(("you", "your", "yours", "yourself", "yourselves"))
_WORD = re.compile(r"[a-z0-9']+")


def _the_first_sentence(reply):
    """The opening sentence, with a question mark inside a quotation left where it is."""
    quoted = False
    for index, char in enumerate(reply):
        if char in _A_QUOTE:
            quoted = not quoted
        elif not quoted and char in ".!?":
            after = reply[index + 1:index + 2]
            if not after or after.isspace():
                return reply[:index + 1]
    return reply


# The bot saying the answer is the person's own fact and only they can give it: "You've not said, so
# only you know - tell me and I'll remember it", "I only get what you type". This is not the `PUNT`
# family, because "You have not said much, so here is the short version: rest, fluids and time" is
# a real answer that opens the same way, and a punt is a claim about the whole reply.
_NO_WAY_TO_KNOW = re.compile(
    r"(?:you'?ve not said|you haven'?t said|you have not said|only you know|"
    r"tell me and i'?ll remember|i only get what you type|no way for me to know)", re.I)


def _the_echo_question(opening, line):
    """True when the question only hands the person's own words back before answering."""
    said = _WORD.findall((line or "").lower())
    if not said:
        return False
    mine = [word for word in _WORD.findall(opening.lower())
            if len(word) > 3 and word not in _NOT_A_WORD]
    return bool(mine) and all(word in said for word in mine)


def is_a_question_back(reply, line=None):
    """True when the reply's first sentence asks the person something instead of answering."""
    text = (reply or "").strip()
    if not text:
        return False
    opening = _the_first_sentence(text)
    if not opening.rstrip().endswith("?"):
        return False
    if not _the_echo_question(opening, line):
        return True
    # The person's own words handed back, and then the answer. Unless the rest is the same shrug
    # in the shape's clothes: "How old are you? You've not said, so only you know" asks and gives
    # nothing, whatever the question echoed.
    rest = text.strip()[len(opening):].strip()
    if not rest:
        return True
    return bool(is_a_punt(first_sentence(rest)) or _NO_WAY_TO_KNOW.search(rest))
# A line that asks what will happen if the person does something ("will it come back if i just
# wipe it", "if i set off at 5 will i miss my flight") wants the outcome of that action, so doing
# the action for them is not the answer. A line that says what it will do and then asks whether
# ("can i send it back if i change my mind", "should i get a dog if i work full time") is still
# asking whether to, and the job is the answer to that one.
HYPOTHETICAL = re.compile(r"\bif (?:i|we|you)\b", re.I)
OUTCOME_ASK = re.compile(r"^(?:and )?(?:will|would|does|do|did)\b|^if\b", re.I)


def _an_outcome_of_their_own_doing(line):
    """True for "will it break if i leave it", False for "can i send it back if i change my mind"."""
    said = str(line or "")
    return bool(HYPOTHETICAL.search(said) and OUTCOME_ASK.search(said))


# A verdict is often said as a plain statement about the thing asked about, with the no inside it
# rather than at the front: "does tea go stale" / "Tea does not go off, it goes stale", "is
# conjunctivitis a reason to keep her off school" / "Conjunctivitis is not a reason to stay away",
# "is it ok to eat raw chicken past its date" / "... so don't eat it". None of those words is on
# the verdict list, and each of them is the no the person asked for. Both halves are needed - the
# negation, and a name from the line - so "don't crowd the pan" in a method about something else
# is not read as a verdict.
NEGATES = re.compile(r"\b(?:not|n't|never|no longer|nothing|none|nowhere)\b", re.I)
# The shape a no takes when it is said as a fact about the thing: a subject, then "is not", "does
# not", "will not". Only the subject is read, and the line's own thing has to be in it, so "that
# is not the ticket seller" is a no about something else. A sentence end stops the subject, but a
# comma does not: "A cold, a cough or a runny nose is not a reason to stay away" names the cold
# three words before the verb.
SAYS_NO = re.compile(
    r"(?:^|[,;:\u2014-]\s*)(?P<subject>[^,;:.!?]{1,40}?)\s+(?:is|are|was|were|does|do|did|"
    r"will|would|can|could|has|have|needs?|takes?)\s+(?:not|never|n't)\b", re.I)
# And the no said as an order about the line's own verb: "is it ok to eat raw chicken past its
# date" / "Pink chicken ... so don't eat it".
NO_JOB = re.compile(r"\b(?:don'?t|do not|never|avoid|skip|stop|no need to)\s+([a-z]{3,})", re.I)
# A word that says nothing on its own: the negations, and the verbs the questions are made of, so
# "does not" is not a thing the line and the reply have in common.
NOT_A_THING = frozenset((
    "not", "never", "nothing", "none", "does", "doesn", "dont", "don", "did", "didn", "isn",
    "aren", "wasn", "weren", "can", "can’t", "cant", "cannot", "won", "would", "should",
    "could", "have", "has", "had", "need", "needs", "want", "wants", "why", "how", "what",
    "when", "where", "which", "that", "this", "these", "those", "they", "them", "there",
    "their", "your", "you", "and", "but", "for", "with", "into", "from", "about", "just",
    "like", "much", "more", "less", "than", "then", "only", "really", "still", "even"))


def _names_the_lines_thing(opening, said):
    """True when the reply's opening names a thing the line named, by stem and from three letters.

    `_names` wants four letters, which is right for the sides of a pick ("a fiesta or a focus")
    and too long for the everyday nouns a verdict is said about: tea, egg, sun, ice, cat.
    """
    reply = set(_words(opening))
    for word in set(_words(said)):
        if len(word) < 3 or word in _EMPTY or word in NOT_A_THING:
            continue
        if word in reply or (len(word) > 4 and word[:-1] in reply):
            return True
    return False


def _says_no_about_the_asked_thing(opening, line):
    """True when the reply negates the very thing the line asked about.

    "does tea go stale" / "Tea does not go off, it goes stale" is the answer, said as a fact about
    the tea rather than as a verdict word. The subject in front of the no has to name the line's
    own thing, so "not the ticket seller" in a delay-repay answer is not read as a verdict about
    the train. An order about the line's own verb counts too: "so don't eat it" answers "is it ok
    to eat raw chicken past its date".
    """
    said = _line_text(line)
    if not said:
        return False
    # A question back is not the verdict inside it: "do i drive" / "Earlier you said you do not
    # drive - still the case?" restates the line and asks again, and it answers nothing.
    if opening.rstrip('"\u201d ').endswith("?"):
        return False
    for match in SAYS_NO.finditer(opening):
        if _names_the_lines_thing(match.group("subject"), said):
            return True
    asked = set(_words(said))
    for match in NO_JOB.finditer(opening):
        verb = match.group(1)
        if verb in asked or (len(verb) > 4 and verb[:-1] in asked):
            return True
    return False


# A test is a verdict: "are my scones done" / "They are risen and browned on top, and a skewer
# in the middle comes out clean". The test can sit past the first clause, so it is read from the
# whole opening - unlike the judgement words above, which are only the answer when they are the
# first thing said.
# The verdict is sometimes said after the reason for it, and the reason is what the first clause
# reads: "That one is the ordinary kind, so no", "It is a part and a few pounds, so yes". Only a
# connector plus a bare verdict counts, so a judgement in a later clause ("..., and if it smells
# fine you are okay") is still not read as the answer.
TRAILING_VERDICT = re.compile(
    r"[,\-\u2013\u2014]\s*(?:so|then|but|which means|that means|meaning)\s+"
    r"(?:no|yes|nope|not really|definitely not|probably not|of course|not worth it)\b", re.I)

# Being told to get it looked at is the yes to "is it serious": "is jaundice dangerous" / "See a
# GP today, not next week". The words are the ones advice uses once it has said what the thing is,
# so this one is read over the whole reply rather than its opening, and only for a line that asks
# whether the thing is a worry - "should i put ice on a burn" is answered by what to do instead,
# and an instruction in that reply is not a verdict about the danger.
SEEKS_HELP = re.compile(
    r"\b(?:see|ring|call|contact|visit|speak to|talk to|get seen by|book (?:an appointment )?with)\s+"
    r"(?:a|an|the|your|nhs|out of hours)?\s*"
    r"(?:gp|doctor|dentist|vet|111|999|urgent care|walk-in cent(?:re|er)|midwife|health visitor|"
    r"pharmacist|optician|nurse|surgery|hospital)s?\b", re.I)
ASKS_IF_SERIOUS = re.compile(
    r"\b(?:dangerous|serious|a problem|a worry|worrying|worry about|something to worry|"
    r"should i worry|normal|abnormal|a sign of|a concern)\b", re.I)


TEST_IS_THE_VERDICT = re.compile(
    r"comes? out clean|is done when|is ready when|is cooked when|"
    r"when it'?s? (?:firm|golden|clean|set|done)|"
    r"if it (?:looks|feels|comes|smells) (?:done|cooked|firm|golden|clean|set|right)", re.I)


# A permission said as a rule is the yes: "Anything bought online, by phone or by post can be
# cancelled within 14 days of it arriving" answers "can I cancel an order I just placed", and "it
# costs nothing to apply" answers "do i get free bus travel if im disabled". A modal in front of a
# passive is about what may be done, so it is the verdict even when the rule takes most of the
# sentence to reach it - which is why this one is read over the whole opening and not its first
# clause like the rest of `VERDICT_INSIDE`.
PERMISSION_RULE = re.compile(
    r"\b(?:can|cannot|can'?t|could|couldn'?t|may|must|should|need(?:s)? to) be [a-z]+ed\b"
    r"|\bcosts? nothing\b", re.I)

# The job split between the person and a trade is the yes/no answered: "can i replace it myself"
# / "For a fridge, the door seals, the drainage hole at the back and the thermostat are yours, and
# the sealed gas and the compressor are an engineer's job" says yes to the parts named and no to
# the rest, and that is the answer a person with the question wants. It is a split rather than a
# sentence about ownership, so the reply has to name both sides: the part that is the person's own
# ("the seals are yours", "a thermostat is a swap you can do yourself") and the part that is a
# trade's ("an engineer's job", "a gas safe job", "an electrician has to"). Naming the trade side
# with an obligation is the answer on its own - "anything in the consumer unit has to be an
# electrician" is the no - while "the pan is yours to season" names no trade and stays unread.
THEIR_OWN = re.compile(
    r"\b(?:is|are)\s+(?:yours|your own|for you to|one for you|a (?:diy|weekend|home|simple) job)\b"
    r"|\b(?:you|yourself) (?:can|could) (?:do|change|replace|fit|swap|fix|service|repair)\b"
    r"|\byourself\b", re.I)
A_TRADE = re.compile(
    r"\b(?:engineer|electrician|plumber|gas safe|registered|qualified|competent|specialist|"
    r"professional|trade)\w*\b", re.I)
MUST_BE_A_TRADE = re.compile(
    r"\b(?:has|have|needs?|must|should)\s+to\s+(?:be\s+)?(?:done\s+)?by\b"
    r"|\bnot a (?:diy|home) job\b|\b(?:by|get) an? (?:gas safe|registered|qualified)\b", re.I)


def _the_job_is_split(opening):
    """True when the reply divides the job between the person and a trade they would need."""
    if MUST_BE_A_TRADE.search(opening):
        return True
    return bool(THEIR_OWN.search(opening) and A_TRADE.search(opening))


# A decision that turns on the person's own facts is answered by the test that settles it: "Fix it
# if it is a part and a few pounds; bin it if the repair is half the price of new", "Repair it if
# it is under five years old and the fault is the battery, the drive...". The two sides of the rule
# are the two answers, so whichever way the person's case falls they have theirs - that is the yes
# and the no together, and it is what "is it worth fixing" is asking for. Both sides have to be
# said about the same thing, which is why each verb carries its "it": "fix it" and "bin it" are a
# decision, while "keep the room cool" and "throw the water away" are two jobs.
RULE_CONDITION = re.compile(
    r"\b(?:if|when|while|once|until|unless|over about|under about|more than about|"
    r"less than about|half (?:of )?the price)\b", re.I)
RULE_KEEP_IT = re.compile(r"\b(?:fix|repair|keep|mend|service)\s+it\b", re.I)
RULE_DROP_IT = re.compile(r"\b(?:bin|replace|scrap|chuck|throw)\s+it\b", re.I)
# The other side of the pair said as a thing to buy rather than as a verb on the old thing:
# "Repair it while it is under about eight years old and the quote is less than half a new one;
# past that, or with a failed heat exchanger, put the money towards a new boiler". "Repair" is one
# side and "put the money towards a new one" is the other, and a rule that names both sides is the
# pick whichever way each is phrased - so the second side is read as the new thing as well as the
# verb on the old one.
RULE_GO_NEW = re.compile(
    r"\b(?:put (?:the |that )?money towards|go for|buy|get|fit|have|bring in)\b[^.;:]{0,24}"
    r"\b(?:a |the )?new\b|\bbuy new\b", re.I)


# A yes said by echoing the question's own verb: "will it get better" / "It does, and the change is
# in the sleep rather than in the work". Only the auxiliaries that answer a yes/no, because "It was
# 40 pounds" is a figure and "It matters" is not a verdict.
VERDICT_ECHO = re.compile(
    r"^(?:it|that|this|they|these|those|he|she) "
    r"(?:does|do|did|will|would|can|could|should|doesn'?t|don'?t|didn'?t|won'?t|can'?t|"
    r"shouldn'?t)\b"
    # A negative is a verdict whichever person it is said in: "is it too late" / "You would not be
    # late".
    r"|^(?:you|we) (?:would|will|do|did|can|could|should) not\b", re.I)
# travel" / "In England you apply for the older person's bus pass through your council once you
# reach the state pension age", "i live alone, do i get money off" / "Living alone gets 25 per cent
# off the bill", "do you tip at a bar" / "In a pub, nothing ... there is no table service to tip".
# Only phrases that answer a yes or a no on their own are read here.
VERDICT_RULE = re.compile(
    # what the person is entitled to, and how they get it. The contraction counts: "can i return
    # something i bought in a shop" / "For anything faulty you're entitled to a full refund within
    # 30 days" is the yes, and "you're" is how most people's own words write it.
    r"\byou(?:'?re| are) (?:owed|entitled|covered|allowed|within your rights)\b"
    r"|\byou (?:qualify|are owed|are entitled|can claim|claim|can apply|apply for|are covered|"
    r"do not need|don't need|get it|can get one|can have one)\b"
    # the rule told as what the thing gets or costs: "Living alone gets 25 per cent off the bill"
    r"|\bgets? (?:\d[\d,.]*|a|the|half|a third|one) (?:per cent|percent|%)\b"
    # the thing is the wrong one to choose: "so it is the wrong choice if yours are already poor"
    r"|\bis the wrong (?:choice|one|thing|call)\b"
    # nothing is owed: "In a pub, nothing: you order and pay at the bar, so there is no table
    # service to tip"
    r"|\bthere is no (?:table service|need|charge|fee|cost)\b"
    r"|\bnothing to (?:tip|pay|declare|owe|worry about)\b", re.I)
# The verdict often comes after the case it is about: "For running, yes: a proper pair makes a
# real difference", "In this weather, no", "On balance, yes". The person asked whether, and the
# reply says which once it has named the situation. Only the strong half of `VERDICT_OPEN` is read
# after the comma, because a case followed by "warm" or "just" is a step ("In the pan, warm the oil
# first"), not a verdict.
VERDICT_AFTER_A_CASE = re.compile(
    r"^(?:for|in|on|with|at|if|when|unless|after|before)\b[^,.;:!?]{1,40},\s*"
    r"(?:yes|yeah|yep|yup|no|nope|nah|not|never|definitely|absolutely|probably|usually|generally|"
    r"normally|mostly|it'?s|it is|that'?s|that is|you'?re|you (?:can|could|should|don'?t))\b", re.I)
# A comparison answered by naming the winner: "Washing up by hand is the cheaper one", "the dried
# version is the better bet". The person asked which, and the reply says which.
THE_WINNER_NAMED = re.compile(
    r"\bis the (?:cheaper|better|worse|cheapest|best|worst|safer|safest|healthier|healthiest|"
    r"stronger|weaker|easier|harder) (?:one|option|choice|bet|buy|of the two)\b", re.I)


# A verdict said about the thing, in words `VERDICT_INSIDE` does not hold: a comparison against
# the other one ("is the better everyday loaf", "is one of the kinder things for knees", "is a good
# way to save 30 to 50%"), or the yes behind a condition ("If you can make it, go", "if the quote is
# more than the car is worth, let it go"). Both are read over the whole opening and only beside the
# line - see the credit in `gives`. Every arm names the verdict rather than describing the thing:
# "is a decent everyday food" on its own is left unread, since a description with no comparison in
# it is not the answer to a yes/no.
VERDICT_ABOUT_IT = re.compile(
    r"\b(?:is|are|was|were) (?:the|one of the|a) (?:better|best|safest|kindest|cheapest|healthiest|"
    r"easiest|simplest|nicest|worst|strongest|tastiest|kinder|safer|cheaper|healthier|easier)\b"
    r"|\bis a good (?:way|idea|choice|bet|pick|option|buy|start|investment)\b"
    r"|\bis the one (?:to|for|that|you)\b"
    r"|\bworth (?:reading|knowing|having|checking|watching|visiting|seeing|a look|a read)\b"
    r"|\b(?:if|unless|when)\b[^.;]{0,90},\s*(?:then\s+)?(?:go|go ahead|go for it|yes|no|fine|okay|"
    r"safe|skip|skip it|leave it|let it go|do it|take it|avoid it|worth it|try it|"
    r"it'?s (?:fine|okay|safe|worth it)|that'?s (?:fine|okay|safe)|you'?re (?:fine|okay|safe))\b",
    re.I)
# A word long enough to be the thing a line is about rather than a joining word. The naming guard
# below asks whether the reply used one of the line's own words, so a word nearly every line and
# nearly every reply share - "with", "have", "that", "time", "good" - cannot count as the name.
_NAMING_WORD = re.compile(r"[a-z]{4,}")
NAMING_STOP = frozenset("""
that this with have your them when what just like then than also make need from into over been
were will would could should about there their some more most much very only even still well
good best fine time times day days year years work works thing things home back down know want
take keep give goes going said says here where while which whose these those being does doing
done made many each both after before again always never often sometimes usually really quite
rather around without within because since until during other another same different little
small large""".split())


# A name is the same name in the plural: a line asks about "my cat" and the reply answers about
# "cats", which is the same thing said twice. A three-letter name is still a name - cat, dog, pan,
# car, egg, gas, oil, bin, bus - and the words that say nothing are already listed, so the length
# of the word is not what makes it specific; the verdict said about it is.
def _the_same_word(word, text):
    if not word:
        return False
    return bool(re.search(r"\b" + re.escape(word) + r"(?:s|es)?\b", text))


def _names_what_the_line_named(opening, said):
    """True when the reply's first clause uses a word of its own that the line also used.

    The words a line and a reply share because both are English say nothing, so they are dropped
    before the comparison; what is left is the name of the thing that was asked about. The name has
    to sit in the clause that carries the verdict, because that is what the verdict is said about:
    "is a peace lily safe for cats" / "Lilies are the worst plant for cats" names its subject,
    while a word met further along the sentence ("... a year of rent tax free" answering a council
    tax question) is a coincidence of subject matter, not an answer about it.
    """
    words = set(_NAMING_WORD.findall(said.lower())) - NAMING_STOP
    if not words:
        return False
    first_clause = re.split(r"[,;:]", opening, maxsplit=1)[0]
    return any(_the_same_word(w, first_clause.lower()) for w in words)


def _the_rule_names_both_sides(reply):
    """True when the reply settles the decision for each side of a condition.

    "Fix it if it is a part and a few pounds; bin it if the repair is half the price of new" is
    the answer to "is it worth fixing": the person's own case falls one way or the other, and the
    reply has said what to do in both. Read over the whole reply, because the second side is often
    the second sentence ("Rule of thumb: fix it while the part is a few pounds and you can fit it
    yourself. Replace it once the repair costs more than about half of a new one").
    """
    if not reply or not RULE_CONDITION.search(reply):
        return False
    drop = RULE_DROP_IT.search(reply) or RULE_GO_NEW.search(reply)
    return bool(RULE_KEEP_IT.search(reply) and drop)


# The lead a repeat puts in front of the answer it is repeating. It says nothing about the shape of
# what follows, so `gives` reads the sentence behind it as the reply.
REPEAT_LEAD = re.compile(
    r"^(?:same as before|same answer(?:,? and it covers this)?|same as i said|as before|as i said|"
    r"like i said|same thing|same again)\s*[:,]?\s+", re.I)


# A sign-off is the bot closing the chat: "Nice one.", "That's great to hear.", "Hope it works
# out.", "No rush.", "Fair enough.", "Alright then - good luck with it." None of them says whether
# the thing in hand is safe, normal, enough or worth it, so none is the verdict a yes/no line asked
# for. The terse yes words are left out on purpose: "Sure.", "Fine." and "Of course you can." are
# verdicts, and the one thing this must not do is call a yes a miss.
SIGN_OFF_LEAD = re.compile(
    r"^(?:(?:that'?s|it'?s|this is)\s+)?(?:nice|great|lovely|wonderful|perfect|brilliant|"
    r"excellent|fantastic|amazing|awesome|glad|sorry|fair enough|no rush|no worries|sounds? good|"
    r"got it|understood|alright then|good luck|hope|thanks|thank you|of course|cheers)\b", re.I)


# The lines that are a wish, a greeting or a thank you rather than a question about the thing.
# Only used to keep the sign-off reading from calling a warm reply a miss on a warm line.
_A_SOCIAL_OPEN = re.compile(
    r"^(?:have|enjoy|hope|good luck|take care|cheers|thanks|thank you|hi|hello|hey|morning|"
    r"goodnight|bye)\b", re.I)


def _a_sign_off(opening):
    """True when the opening closes the chat instead of answering it.

    Only the part after the sign-off phrase is read for a verdict, so "No worries, it's fine." and
    "Of course you can freeze it" stay the yes they are, while "No rush." and "Fair enough." say
    nothing about the thing.
    """
    match = SIGN_OFF_LEAD.match(opening)
    if not match:
        return False
    rest = opening[match.end():].strip(" \t.,;:!?-\u2014")
    # "Sorry, but you should bin it" is the no: the sign-off is the word in front of it.
    rest = re.sub(r"^(?:but|and|so|though|however|yet|although|still)\b[\s,]*", "", rest, flags=re.I)
    if not rest:
        return True
    return not (_a_yesno(rest) or VERDICT_INSIDE.search(rest) or VERDICT_ECHO.match(rest)
                or VERDICT_RULE.search(rest) or TEST_IS_THE_VERDICT.search(rest)
                or TRAILING_VERDICT.search(rest) or PERMISSION_RULE.search(rest))


# A verdict is often said as where the thing sits on a scale rather than with a yes or a no: "is
# it normal that a 5 year old cant write his name" / "Late but still inside normal, and worth a
# light touch rather than a push", "is 37.8 a fever" / "Borderline at that reading", "is it too
# late to start" / "On the late side, but inside the usual range". The placing is the answer, and
# the words that say it are a position against a normal, a range or a side of it - not the
# adjective on its own, so "on a normal 30C cycle" and "the average household uses" stay unread.
VERDICT_ON_A_SCALE = re.compile(
    r"\b(?:inside|within|outside|past|beyond|above|below|at the top of|at the bottom of)\s+"
    r"(?:the\s+|its\s+)?(?:normal|usual|typical|expected|average|recommended|healthy)"
    r"(?:\s+(?:range|band|limits?|age|window|spread|side))?\b"
    r"|\bon the (?:late|early|young|old|small|large|big|high|low|heavy|light|slow|fast|short|long|"
    r"tricky|tight|generous|easy) side\b"
    r"|\bborderline\b|\bexactly on time\b|\bnothing (?:unusual|abnormal|out of the ordinary)\b"
    r"|\bstill (?:inside|within|in)\b.{0,20}\b(?:normal|range)\b", re.I)


def _a_yesno(opening, line=None):
    if is_a_punt(opening):
        return False
    if FIRST_PERSON_VERDICT.match(opening) or VERDICT_OPEN.match(opening) \
            or ECHO_VERDICT.match(opening) or VERDICT_AFTER_A_CASE.match(opening):
        return True
    if PERMISSION_RULE.search(opening):
        return True
    if _the_job_is_split(opening):
        return True
    if VERDICT_ECHO.match(opening) or VERDICT_RULE.search(opening):
        return True
    first_clause = re.split(r"[,;:]", opening, maxsplit=1)[0]
    if _the_verdict_is_inside(first_clause, line) or TEST_IS_THE_VERDICT.search(opening) \
            or TRAILING_VERDICT.search(opening) or THE_WINNER_NAMED.search(first_clause) \
            or A_HARM_IS_WHAT_IT_IS.search(first_clause) \
            or VERDICT_ON_A_SCALE.search(first_clause):
        return True
    if _the_quality_answers(first_clause, line):
        return True
    if _a_rule_of_its_use(opening, line):
        return True
    # A verdict often comes after the setup that leads to it, and the setup is not the answer:
    # "Red meat is more forgiving than chicken: ... it is fine", "A steady, even sound covers the
    # small noises ..., so it helps most in a shared or noisy room". Only the clause the colon or
    # the `so` introduces is read, not the whole sentence, and only for this shape.
    tail = ""
    if ":" in opening:
        tail = opening.split(":", 1)[1]
    else:
        found = re.search(r",?\s+so\b", opening)
        if found:
            tail = opening[found.end():]
    tail = re.split(r"[,;]", tail, maxsplit=1)[0] if tail else ""
    return bool(tail and (_the_tail_says_what_it_is_about(tail, line)
                          or _the_quality_answers(tail, line)))


# The answer to "is it ok / is it safe" is often the rule of use rather than the word yes: how long
# it keeps, what to keep away from it, how much of it, and what makes it not ok. Six deck lines put
# the same question about a fly spray and every one of them was scored a miss, because the reply
# says *keep the cat out of the room until it has settled* and never says "no, not with a cat".
# The rule is the answer: a person who is told the limit has their verdict.
#
# Read as a limit and not as any advice, which is why every arm below carries the mark of a bound -
# a keeping time, an out-of/away-from, an "unless", a figure with "up to"/"until"/"at a time", or a
# qualified "it is fine". Ordinary advice on a yes/no line ("Put the mince in a bag and freeze it")
# carries none of them and stays the miss it was.
A_LIMIT_ON_ITS_USE = re.compile(
    # how long it keeps: "a cooked dish keeps 3 to 4 days", "lasts about a fortnight"
    r"\b(?:keeps?|lasts?|stays?|stored?|freezes?)\b[^.\d]{0,20}\b"
    r"(?:\d[\d.,]*\s*(?:to|-|or)\s*)?\d[\d.,]*\s*"
    r"(?:days?|hours?|weeks?|months?|years?|fortnights?)\b"
    # what to keep it away from: "keep the cat out of the room", "move it away from the heat"
    r"|\b(?:keep|keeps|kept|take|takes|move|put|leave|shut|block)\b[^.]{0,45}?\b(?:out of|"
    r"away from|well away)\b"
    # a no with its condition: "no soft cheese unless it is cooked until steaming"
    r"|\b\w+\b[^.]{0,30}\bunless\b"
    # a bound stated as a figure: "up to 22kg", "no more than 15 minutes", "under 50 decibels"
    r"|\b(?:up to|no more than|at most|not more than|until about|until they|under about)\b"
    r"[^.]{0,12}?\b\d[\d.,]*\s*(?:kg|kgs|g|grams?|cm|mm|ml|litres?|inches?|years?|months?|"
    r"weeks?|days?|hours?|minutes?|mins?|seconds?|decibels|db|degrees?)\b"
    # a dose of time: "two or three minutes at a time, a few times a day"
    r"|\b\d[\d.,]*\s*(?:to|-|or)\s*\d[\d.,]*\s*(?:minutes?|mins?|hours?|seconds?)\b"
    r"[^.]{0,12}?\bat a time\b"
    # a bound on the window: "within two hours", "reheat it until steaming"
    r"|\b(?:within|inside|reheat(?:ed)?\b[^.]{0,15}?until)\b[^.]{0,20}?"
    r"(?:\d[\d.,]*\s*(?:hours?|minutes?|days?)|steaming|piping hot|boiling)\b"
    # the thing said to be fine, of the thing itself: "it is usually still fine"
    r"|\b(?:it|they|that|this)\b[^.]{0,12}?\b(?:is|are)\b[^.]{0,12}?"
    r"\b(?:fine|safe|ok|okay|alright|harmless)\b", re.I)


# A few of the bounds are the answer on their own, whatever the reply calls the thing: how long it
# keeps, how much of it is too much, how long at a time, and the "no X unless" that carries its own
# condition. Nobody writes "a cooked dish keeps 3 to 4 days" about a question that is not about
# whether the dish is still good, and the cards say "a cooked dish" where the person said "leftover
# curry", so the naming test below cannot be the only door.
A_BOUND_THAT_IS_THE_ANSWER = re.compile(
    r"\b(?:keeps?|lasts?|stored?)\b[^.\d]{0,20}\b(?:\d[\d.,]*\s*(?:to|-|or)\s*)?\d[\d.,]*\s*"
    r"(?:days?|hours?|weeks?|months?|years?|fortnights?)\b"
    r"|\b(?:use|eat|drink|keep|finish|consume)\b[^.]{0,25}?\bwithin\b[^.]{0,15}?"
    r"\d[\d.,]*\s*(?:days?|hours?|weeks?)\b"
    r"|\b(?:no more than|up to|at most)\b[^.]{0,12}?\b\d[\d.,]*\s*(?:kg|kgs|g|grams?|ml|"
    r"units?|decibels|db|degrees?|hours?|minutes?)\b"
    r"|\b\d[\d.,]*\s*(?:to|-|or)\s*\d[\d.,]*\s*(?:minutes?|mins?|hours?|seconds?)\b"
    r"[^.]{0,12}?\bat a time\b"
    r"|\b\w+\b[^.]{0,25}\bunless\b", re.I)


def _a_rule_of_its_use(opening, line):
    """True when the reply answers "is it ok/safe" by giving the rule of use itself.

    A bound that is the answer on its own - a keeping time, a "use it within", a "no more than" -
    settles the question without naming the thing, because the cards name the class ("a cooked
    dish") and the person named one of it ("leftover curry").

    The rest of the bounds have to be on the thing the line asked about, so the reply names a word
    the line named: "keep the cat out of the room" answers the spray line, and "keep the receipt in
    the tin" as the answer to a washing machine line names nothing of it and is not this.
    """
    if A_BOUND_THAT_IS_THE_ANSWER.search(opening):
        return True
    found = A_LIMIT_ON_ITS_USE.search(opening)
    if not found:
        return False
    said = _line_text(line)
    if not said:
        return True
    if _names(found.group(0), said) or _names(opening, said):
        return True
    # The line asks about the thing by pronoun and the reply gives the rule without naming it:
    # "is it ok to eat chicken thats been in the fridge 4 days" / "Cooled within two hours ... a
    # cooked dish keeps 3 to 4 days". Only a line with nothing to name is left to this.
    return not [w for w in set(_words(said)) if _long_enough_a_name(w, 4) and w not in _EMPTY]


# A no often comes as the line's own verb, denied: "does vinegar go off" / "Vinegar does not go
# off", "is it worth it" / "It isn't worth it", "do i need to preheat" / "You don't need to". The
# reply names the question back and denies it, which is the no however the sentence is built.
NEGATED_AUX = re.compile(
    r"\b(?:is|are|was|were|do|does|did|have|has|had|can|could|will|would|should|must|need|"
    r"needs|kills?|harm|hurt|matter|work|works)\s*(?:not|n'?t)\b|\b(?:isn'?t|aren'?t|wasn'?t|"
    r"weren'?t|don'?t|doesn'?t|didn'?t|haven'?t|hasn'?t|can'?t|cannot|won'?t|wouldn'?t|"
    r"shouldn'?t)\b", re.I)

# A verdict can be given as what the thing usually is rather than as a word about it: "is that
# conjunctivitis" / "A red, watery, gunky eye is usually conjunctivitis or an allergy". The subject
# is described rather than named, so every verdict-word list misses it and the reply reads as a
# miss although it answers the line.
USUALLY_IS = re.compile(
    r"\b(?:is|are|was|were)\s+(?:usually|often|nearly always|almost always|mostly|generally|"
    r"typically|most likely|in most cases)\b", re.I)


def _the_thing_is_named_as_what_it_usually_is(opening, line):
    """True when the reply says what the line's own thing usually is: "is that conjunctivitis".

    "A red, watery, gunky eye is usually conjunctivitis or an allergy", "Banging or rumbling when
    the heating starts is usually air or a pump set too fast" answer the line by naming the thing
    it asked about as what the case usually is. The subject is described rather than named, so the
    verdict-word tests find nothing in it, and the reply is a real answer rather than a method.

    The line's own word has to appear after the "is usually", or the sentence is about something
    else: "A cat is usually asleep by then" is not an answer to "is that a good sign".
    """
    said = _line_text(line)
    if not said:
        return False
    found = USUALLY_IS.search(opening)
    if not found:
        return False
    rest = opening[found.end():]
    for word in set(re.findall(r"[a-z][a-z']*", said)):
        if len(word) < 4 or word in _EMPTY or word in NOT_A_THING:
            continue
        if re.search(r"\b%s" % re.escape(word), rest):
            return True
    return False


def _an_echoed_no(opening, line):
    """True when the first sentence denies the line's own words: "Vinegar does not go off".

    The reply has to do both things - carry a denial, and name something the line named - or it
    is not an answer to this line. "It isn't cooked until the skewer comes out clean" denies
    nothing of "are my scones done", so the test-reading is what settles that one.
    """
    said = _line_text(line)
    if not said or not NEGATED_AUX.search(opening):
        return False
    words = set(re.findall(r"[a-z][a-z']*", said))
    named = {w for w in words if len(w) >= 4 and w not in _EMPTY}
    return any(w in opening for w in named)


def _the_job_answers(opening, line):
    """True when the reply does the thing the person asked whether to do.

    A yes/no about doing something is often answered by doing it: "Slice it first, then bag it"
    is the yes to "can i freeze bread", "Strap them in every time" the yes to "do i need to
    strap my toddler in". This is a yes and never a miss: the reply is only counted when it
    opens on a job and the line is asking whether, so a reply this cannot read stays the
    "words cannot tell" it was before.

    Not when the line asks what happens if it does something itself: then the outcome is the
    answer, and "Wipe it off with a mould spray" is no answer to "will it come back if i just
    wipe it". That one is a miss the clear-shape test below makes, on the method it names.

    The price of reading any verb and not a list of them: an instruction about something else
    passes too. "is my butter out of date" / "Rub washing-up liquid into the grease mark", and
    "did you see the match last night" / "Dip your headlights as soon as another car is in sight"
    are misses this calls a fit (rugged-tuna's find in review). Both narrowings I measured cost
    more good replies than they save: requiring the reply to name a word from the line turns 7
    fits into faults ("should he dye it" / "Colour the new growth every four to six weeks"), and
    requiring `PERMISSION` in the line turns 5 ("is it rude to leave a group chat" / "Mute it
    first", "am i getting enough water each day" / "Fill a bottle in the morning"). At 612 shaped
    turns the wide reading takes misses from 150 to 134 and the narrow ones to 137 and 139, so it
    is kept, and the error left is the one that hides a miss rather than the one that invents one.
    """
    if not line or _an_outcome_of_their_own_doing(line):
        return False
    if JOB.match(opening):
        return True
    # The doing is the yes whichever verb says it. JOB carries the verbs the cue list knows, and
    # the deck answers "do i need to see a physio" with "See a physio if the pain has lasted more
    # than a fortnight", and "hotel room was filthy can i get a refund" with "Photograph it and
    # complain at reception". The shape of the opening - a verb and the thing it acts on - is
    # what makes it the job, not the verb being on a list.
    if _imperative(opening):
        return True
    return _the_job_named(opening, _line_text(line))


# A pick names a side or says which one to take. A paragraph that describes one side and stops
# has not picked, and neither has a card that names both things without preferring one.
PREFERS = re.compile(
    # A pick also names the side it took and starts with it: "Replace the dishwasher", "Repair
    # it while the quote is under half". The verb is at the front, so it is what is chosen rather
    # than a step in a method.
    r"^(?:replace|repair|rebuild|service|swap|install|keep|buy|rent|hire|book|order|get|go for|"
    r"go with|take|choose|pick|stick with|read|watch|visit|try|start with|hold off|wait)\b"
    r"|\b(?:better|best|rather|instead|go for|go with|opt for|choose|pick|stick with|"
    r"you (?:mentioned|said|named|had)|you'?re on|"
    r"\b(?:buy|get|fit|install|replace|repair|swap|go for|go with) (?:the|a|an|one|it)\b|"
    r"i'?(?:d| would) (?:go|do|make|cook|have|take|get|pick|choose|suggest|recommend|buy|wear|"
    r"watch|read|order|book|serve|use|say|stay|leave|keep|skip|cancel|wait|ring|call)|"
    r"worth (?:the extra|it)|"
    r"either .{0,40}\bor\b|"
    # A pick said with what it is worth doing: "A dishwasher is worth repairing while the quote is
    # under half the price of a new one" has taken the repair without naming it first.
    r"\bworth (?:repairing|replacing|fixing|doing|keeping|buying|getting|upgrading|waiting|"
    r"swapping|having|sticking with)\b|"
    r"both are|both work|depends on|for (?:a|the) .{0,30}\band\b.{0,30}\bfor\b)\b", re.I)


# A pick can be one noun with no verb at all: "The heat pump.", "Oat milk for coffee", "Lisbon."
# It is a pick only when it is short, opens on a thing rather than on a verdict, and is not a
# hedge; "Nope." and "Can't call that one." are the two ways a short opening is not a pick.
BALD = re.compile(r"^(?:the|a|an|this|that|[A-Z][a-z]+)\b")
# A finite verb makes an opening a statement rather than a bare name: "Small cars hold their
# value well." opens on a thing but says something about it, and that is not a pick.
BALD_VERB = re.compile(
    r"\b(?:is|are|was|were|has|have|holds?|works?|comes?|goes?|keeps?|takes?|lasts?|costs?|"
    r"means|does|do|will|can)\b", re.I)
# A reply that opens on a reason is answering a why, and one that opens on an instruction is
# answering a method. Neither names a thing, so neither is a pick: "Because the seal dries out."
# and "Mix it in a bowl." were both credited as picks by the bare-name arm below, which only
# asked for a capitalised first word.
REASON_OPENS = re.compile(
    r"^(?:because|cos|'cause|that'?s why|that is why|since|so that|which is why)\b", re.I)
# A method opens on its verb and then says what to do with: "Mix it in a bowl", "Stir it in",
# "Preheat the oven first", "Sear it in a hot pan", "Chill the dough". A name does not, because
# the word after a name is a noun: "Oat milk for coffee", "Lisbon for the food". Reading the
# shape rather than the verb keeps the guard general - no list of kitchen verbs to keep up - and
# a determiner in front of the first word keeps "The heat pump" and "A slow cooker" out of it.
A_VERB_THEN_THE_THING = re.compile(
    r"^(?!(?:the|a|an|this|that|these|those|your|my|our|their|his|her|its|some|any|each|every|"
    r"one|two|both)\b)[a-z]+\s+(?:it|them|the|a|an|your|this|that)\b", re.I)


# The thing a reply names before its colon: "Day trips from Dublin: ...". The head is read on its
# own, because it is the pick; the rest is detail.
def _undecorated(head):
    """A head without the asterisks or quotes that set it off: "*Note*" and "Note" are one label."""
    return head.strip().strip("*_\"\u201c\u201d'").strip()


NAMED_HEAD = re.compile(r"^(.{2,70}?):\s", re.S)
# A head that asks, instructs, or labels a list is not a thing named: "How to clean a mattress:
# ...", "Steps to follow: ...", "First: ...".
ASKS_HEAD = re.compile(r"^(?:how|what|why|when|where|which|who|steps?|first|firstly|then|next|to|"
                       r"tldr|quick tips?)\b", re.I)
# A label on its own introduces several things rather than naming one: "Quick: tuna pasta in 15, a
# stew in 25", "Cheap: beans on toast", "While you cook: three albums", "Best: ...". The colon
# there is a heading over a list, so the head is not the answer. sleek-shark found these in PR 7875
# and the two rules are the same rule; a label with words after it is still a thing named ("Cheap
# weeks come from the same eight things: ..."), so only the bare label is refused.
LABEL_HEAD = re.compile(r"^(?:quick|best|cheapest|easiest|fastest|faster|fast|simplest|simple|"
                        r"cheap|easy|options?|ideas?|while you [a-z]+|bonus|top|also|first|firstly|"
                        r"then|next|tip|tips|note|tl;?dr|answer|short answer|in short|verdict|"
                        r"my pick|worth it)\s*$", re.I)
# A label over a list is a pick only when the label names something. "Ten-minute dinners:" and
# "For laughs:" name a thing, so the colon is the reply saying "here is the answer". "Quick:",
# "Cheap:" and "While you cook:" name a hurry, a price or a moment, so what follows is a menu of
# options and none of them is picked: "Quick: tuna pasta in 15, macaroni cheese in 25, or a
# sausage traybake" answers "any ideas for dinner" and not "what should i cook tonight".
# lilac-bell ruled it, as the lane that owns the want. A label that declares the answer itself
# ("my pick", "short answer", "the verdict") does name it, so those are left out of this list and
# keep the pick they open on: "Short answer: the Corolla, or a Civic if you want it to last".
SET_LABEL = re.compile(
    r"^(?:quick|best|cheapest|easiest|fastest|faster|fast|simplest|simple|cheap|easy|options?|"
    r"ideas?|while you [a-z]+|bonus|top|also|first|firstly|then|next|tip|tips|note|worth it)\s*$",
    re.I)
# A head that points back at the last answer names nothing new: "Same as before: About 40 minutes
# start to finish" is the earlier answer repeated, not a pick, and it was the last false pass left
# in a 547-turn sweep. It is the follow-up answering itself, so the reply is a reminder of a shape
# rather than that shape given again.
ECHO_HEAD = re.compile(r"^(?:same as (?:before|last time)|as (?:before|above)|like before|"
                       r"as i said|same|same again|still|unchanged|no change)\s*$", re.I)
# A head that talks about the earlier answer names no thing either: "You've got it:", "I like
# them:", "That's the one:". The label arm already refused these and the *head* arm was the way
# round it, so the two rules are now the same rule: the words after the colon are a comment on the
# last answer rather than a thing picked. "It depends:" is not one of them - a Fiesta for town and
# a Focus for the motorway is still a choice.
BACK_HEAD = re.compile(
    r"^(?:you'?ve got it|you got it|i (?:like|liked|love|prefer) (?:it|them|that|those)|"
    r"that'?s (?:it|right|the one)|this one|as i said|like before|"
    r"same as (?:before|last time))\b", re.I)
# A head that *states* something names no pick: "An air fryer is a small oven: it sits on the
# counter", "It is worth it: bin it". A copula in the head makes it a description, a verdict or a
# comparison, and the pick is the thing before the colon - which is not there. tidy-chalk found
# five of these in review (8195); "It depends: a Fiesta for town" states nothing, so it stays.
STATES_HEAD = re.compile(r"\b(?:is|are|was|were|means|sounds?|seems?)\b|"
                         r"\b(?:it|that|here|there|what)'s\b", re.I)
# ...and a head that frames the answer is not a thing named either: "Here's the thing: you have to
# decide", "Think of it as a sponge: it soaks up the water". The short answer, my pick and best
# bet are different: they say "the answer comes next" without stating anything of their own.
FRAME_HEAD = re.compile(r"^(?:here'?s|think of it|imagine|to be fair|the (?:truth|thing|point|"
                        r"trick|catch|problem|issue|trouble|trouble is)|honest\w*|"
                        r"the way i see it|what you want)\b", re.I)


# A which-question is answered by saying what the difference is: "A marathon is 26.2 miles and a
# half is 13.1, so the full race is exactly twice as far", "40 is the setting for uniform". The
# reply names the side that wins by comparing it, with no "better" anywhere, so the comparative
# itself is the pick.
PICKS_BY_COMPARISON = re.compile(
    r"\b(?:is|are|was|were) (?:the )?(?:longer|shorter|bigger|smaller|taller|wider|deeper|"
    r"heavier|lighter|faster|slower|quicker|cheaper|dearer|pricier|warmer|colder|hotter|newer|"
    r"older|nicer|easier|harder|safer|stronger|thicker|thinner)\b"
    r"|\b(?:is|are) (?:exactly |about |nearly |roughly )?twice as\b"
    # "The rinse bucket is the one that stops the scratches" describes the bucket; it does not
    # pick between the car-wash line's two days. A relative clause after the phrase is what says
    # it is a description ("the one that stops", "the one which fits"), and every pick reads
    # without one: "basmati is the one", "the evening is the one for you", "your vet is the one
    # to ask".
    r"|\bis the (?:one|answer|pick|choice|setting|winner|default)\b"
    r"(?!\s+(?:that|which|who)\b)"
    r"|\bare the thing\b|\bthe thing to (?:get|buy|have|do|go for)\b", re.I)
# A pick given as a case for each side, with the condition that says which is for which:
# "Use the name: 'Dear Ms Okafor' if you know it and it is formal, 'Hello Sam' for anything else."
# The names in quotes are what says it is a case for each side rather than one instruction, so the
# two patterns are read together by `_a_pick`.
PICK_BY_CASE = re.compile(
    r"\bif\b[^:]{0,90}\b(?:for (?:anything|everything) else|otherwise|else)\b"
    r"|\bif not\b", re.I)
QUOTED_NAME = re.compile(r"'[^'\n]{2,40}'|\u2018[^\u2019\n]{2,40}\u2019")


# "I'd do a frittata", "I'd keep the old one": what the bot would do is a pick, whichever verb it
# is about the thing in the line.
WOULD = re.compile(
    r"\bi'd (?:do|make|cook|have|wear|say|keep|buy|book|order|get|take|go|try|use|put)\b", re.I)

# A pick often says who or when it is for first and colons into the list: "Quick: tuna pasta in 15,
# a frittata in 20, or a sausage traybake", "For laughs: *What We Do in the Shadows*...", "Kids,
# about 15 minutes: pasta with butter and cheese, fish fingers or a small roast". The bot's own
# answer to "what should I cook tonight" is written this way, so reading only the part after the
# colon is the difference between a miss and a plain pick. The lead has to be a label rather than
# a fact about the thing ("Hard water is the reason: it carries dissolved calcium" is a why-answer)
# and a frame that points back ("You've got it:", "Same as before:") is not a label either.
LABEL = re.compile(r"^([^:]{1,90}):\s+(\S.+)$")
NOT_A_LABEL = re.compile(
    r"\b(?:is|are|was|were|means?|reason|cause|because|depends?|you'?ve got|same as|as before|"
    r"good question|it'?s|that'?s|there'?s|here'?s|"
    r"^i (?:like|liked|love|prefer) (?:it|them|that|those)|^both|^same)\b", re.I)


def _listed_after(label_lead):
    """True when the words after a lead's colon are a list of things to pick from."""
    if re.search(r"\bor\b", label_lead, re.I) or ";" in label_lead:
        return True
    # "For laughs: *What We Do in the Shadows* (a daft vampire mockumentary), *The Nice Guys*" is
    # a list too, so two commas between named things count; one comma is a sentence in two halves.
    return len(re.findall(r",\s+\S", label_lead)) >= 2


def _marked_things(opening):
    """How many things the opening marks out as things: a title in asterisks or in quotes. The
    reply is pointing at named things rather than describing a method."""
    return len(re.findall(r"\*[^*\n]{2,60}\*", opening)) + len(
        re.findall(r"\u201c[^\u201d\n]{2,60}\u201d|\B\"[^\"\n]{2,60}\"", opening))


# A pick that sets the thing it chose in emphasis: "*Understanding Exposure* by Bryan Peterson".
# The title is the answer, and the words after it say why rather than what the thing is. `_marked_things`
# above counts two or more marked things as a list; this is the same reading for the one thing a pick
# names, so it has to sit on the pick and not on the list. A colon straight after the emphasis is the
# other way a label looks: "*Note*: warm the pan first" sets off what comes next rather than naming a
# thing chosen, so the emphasised span stops counting there.
NAMES_IN_EMPHASIS = re.compile(
    r"^\*{1,2}[^*\n]{2,70}\*{1,2}(?!\*)(?!\s*(?:is|are|was|were|means|refers|describes|comes)\b)"
    r"(?!\s*:)")


def _a_pick(opening):
    if PREFERS.search(opening) or PICKS_BY_COMPARISON.search(opening) or WOULD.search(opening):
        return True
    lead = LABEL.match(opening)
    if lead and not NOT_A_LABEL.search(lead.group(1)) \
            and not SET_LABEL.match(lead.group(1).strip()) and _listed_after(lead.group(2)):
        return True
    # A pick often names the winner instead of preferring it: "A cremation with no service is the
    # cheapest", "Showering wins on time and water". Any superlative does that job, not only the
    # ones on a list, so the shape is the ending: "London City is the closest to the centre", "the
    # second bedroom is the quietest", "a slow cooker is the most forgiving". The word before it
    # may be an adverb of habit ("is usually the cheapest") and it changes nothing. A word that
    # ends in "est" without judging anything - a request form, the west wing, an earnest try - is
    # kept out by name, and a figure cannot reach this path, so a name that is a time is unaffected.
    # The winner is named about a thing in the plural as often as not - "Coaches are the cheapest
    # way between two cities", "Trains are the quickest, but they cost the most" - so the copula
    # is read in every number and tense, as the superlative list below already was.
    if re.search(r"\b(?:is|are|was|were) (?:almost |nearly |usually |often |always |generally |probably |still |"
                 r"quite |about )?(?:the )?(?:(?!(?:request|interest|honest|guest|test|rest|nest|"
                 r"west|east|forest|harvest|protest|suggest|arrest|contest|digest|invest|earnest|"
                 r"chest|crest|tempest|midwest|northwest|southwest|northeast|southeast)\b)"
                 r"[a-z]{3,}est|most [a-z]+|least [a-z]+)\b|"
                 r"\bis the (?:cheapest|dearest|worst|easiest|quickest|safest|hardest|"
                 r"cheaper|better)\b|\bwins?\b(?: on| over| for| by)\b|"
                 # The question asked for a superlative and the reply names the thing that holds
                 # it: "India has the most people", "Lisbon has the cheapest beds".
                 r"\b(?:has|have|holds|gets) (?:the )?(?:most|highest|lowest|fewest|best)\b",
                 opening, re.I):
        return True
    if NAMES_IN_EMPHASIS.match(opening):
        return True
    # A pick is sometimes a case for each side with no word of preference in it: "Use the name:
    # 'Dear Ms Okafor' if you know it and it is formal, 'Hello Sam' for anything else." Two names
    # set off in quotes and a condition that says which is for which is the pick - the same shape
    # `gives` credits for a yes/no ("Fix it if it is a part; bin it if the repair is half the price
    # of new"), which does not reach here because those sides are the line's nouns and these are
    # labels. Without the quotes the head is an instruction ("Use the name:"), which is why the
    # names are what is counted.
    if len(QUOTED_NAME.findall(opening)) >= 2 and PICK_BY_CASE.search(opening):
        return True
    if is_a_punt(opening) or VERDICT_OPEN.match(opening):
        return False
    # A pick often names the thing and then says why: "Day trips from Dublin: Howth for the cliff
    # walk, Malahide castle, and Glendalough", "Something that makes a day in bed easier: a flask
    # of soup with bread", "*Flour Water Salt Yeast* by Ken Forkish for bread: four ingredients".
    # The colon is the reply saying "here is the answer", and the head before it is a thing
    # rather than an instruction or a question: "Fix the wake-up time first: the same hour every
    # day" is advice, "How to clean a mattress: vacuum it" is a method, and both stay misses.
    head = NAMED_HEAD.match(opening)
    if head:
        # The head is read without the marks that set it off: a label is a word, so "*Note*:" and
        # "**Note**:" are the same label as "Note:" and introduce what follows rather than naming
        # a thing chosen.
        named = _undecorated(head.group(1).strip())
        # A head that points back, states, frames or measures is not the thing picked: "Same as
        # before: About 40 minutes start to finish", "An air fryer is a small oven: ...", "Here's
        # the thing: you have to decide", "About 40 minutes start to finish: fry the mince".
        # `BACK_HEAD` is here too, so the head arm and the label arm read the same heads the same
        # way. "Same as before: About 40 minutes start to finish" was already a miss, and
        # "You've got it:" - the same words in a friendlier frame - was still a pick.
        if (ECHO_HEAD.match(named) or BACK_HEAD.match(named) or STATES_HEAD.search(named)
                or FRAME_HEAD.match(named)
                or (bool(re.search(r"\d", named)) and (_a_time(named) or _an_amount(named)))):
            return False
    if (head and not INSTRUCTS.match(_undecorated(head.group(1)))
            and not ASKS_HEAD.match(_undecorated(head.group(1)))
            and not SET_LABEL.match(_undecorated(head.group(1)).strip())):
        return True
    words = opening.rstrip(".!").split()
    # A short opening that is a figure is not a bare name. "About 40 minutes start to finish." opens
    # on a capitalised word, so the name pattern takes it, and then a duration answered a pick -
    # the same for "Roughly 20 minutes", "The 14th", "GBP7.50". The note on the head branch above
    # says a figure cannot reach this path; this is the guard that makes that true of the bald one.
    # The same arm credited a method and a reason, which are the answers to two other questions:
    # "Mix it in a bowl.", "Stir it in.", "Preheat the oven first.", "Try the 14 bus" and
    # "Because the seal dries out." all open on the right kind of word and say nothing about a
    # thing to choose, so an instruction or a reason opening stands down here too.
    return (len(words) <= 6 and bool(BALD.match(opening))
            and not BALD_VERB.search(opening)
            and not INSTRUCTS.match(opening) and not REASON_OPENS.match(opening)
            and not A_VERB_THEN_THE_THING.match(opening)
            and not _a_clear_time(opening) and not _a_figure_that_counts(opening))


# The words that make an opening a method: an ordinal step, a verb doing something to a thing,
# or an instruction with no "first" and no "then" ("Open a Lifetime ISA and put a standing
# order in"). The verb at the very front is the instruction; the same word later is a detail.
DOES = re.compile(
    r"\b(?:first|firstly|then|next|after that|afterwards|finally|lastly|start by|start with|"
    r"begin by|once (?:it|that|you)|step one|step 1|before you|while you|leave it|put it|"
    r"take it|turn it|give it|run it|use a|use the|you (?:could|can|should|need to) (?:try|use|"
    r"start|put|take|run|give|leave|set|check))\b", re.I)
INSTRUCTS = re.compile(
    r"^(?:open|book|ring|call|phone|top|wipe|soak|give|leave|put|take|turn|run|use|set|check|"
    r"clean|wash|rinse|melt|stir|mix|fry|boil|bake|roast|grill|simmer|add|pour|spread|cut|chop|"
    r"slice|peel|grate|whisk|beat|knead|roll|press|heat|cook|drain|freeze|cool|cover|store|keep|"
    r"throw|bin|recycle|replace|repair|fit|fix|install|service|bleed|flush|tie|wrap|apply|ask|tell|"
    r"send|email|visit|go|start|finish|stop|avoid|make|buy|order|measure|weigh|label|file|"
    r"register|report|complain|sign|write|read|watch|listen|carry|hold|stand|sit|wait|test|"
    r"taste|smell|look|choose|pick|swap|follow|keep|get|bring|put|note|note down|squeeze|rub|"
    r"scrape|buff|dab|blot|scoop|trim|mist|sweep|pat|fold|split|delay|aim|try|hook|wedge|prop|"
    r"secure|tape|glue|batch|preheat|defrost|pick over|sort out|go through|block|treat|air|"
    r"cancel|renew|practise|practice)\b",
    re.I)
# A method can also be a sum. "Multiply the decimal by 100 and put a % sign on it" answers "how do i
# convert a decimal to a percentage" as fully as "Fry the onion" answers "how do i make a curry", and
# none of the arithmetic verbs are on INSTRUCTS, so those replies were read as no shape at all -
# neither credited nor blamed, which hides the miss it was built to catch. They are kept in their
# own list rather than added to INSTRUCTS because "divide" and "subtract" are also nouns: on
# INSTRUCTS the word also reaches JOB, and `_opens_on_a_job` then reads "Divide the cost by three"
# as a sentence about a cost. "multiply" is not a noun at all, and "divide" is one only after "the".
A_CALCULATION = re.compile(
    r"^(?:multiply|divide|subtract|convert|work out|work back|add up|share out|multiply out)\b",
    re.I)
# An instruction can also be told as what not to do: "Don't wear white or cream to a wedding".
DOES_NOT = re.compile(r"^(?:don'?t|do not|never|avoid|skip|stop|no need to)\b", re.I)
# The verbs an answer about what to do can open on. INSTRUCTS is the short list a method is read
# by; this is that list plus the everyday body, money and device ones, because a yes/no is just as
# often answered by "Strap them in every time" or "Pay a little each month" as by "Slice it first",
# and widening the method list itself would make every reply that opens on one of them a step.
# "See a GP if it lasts more than a week" is the yes to "should i see someone", and the seeing of
# somebody is the one job `INSTRUCTS` did not carry: it had `visit` and `ring`, not `see`.
JOB = re.compile(INSTRUCTS.pattern.replace(
    r")\b", r"|see|strap|warm|wear|feed|water|brush|rest|drink|eat|sleep|walk|save|pay|spend|charge|"
    r"plug|reset|update|download|print|scan|iron|sand|paint|screw|seal|glue|tape|hang|fold|dry|"
    r"find|"
    r"air|bath|shower|talk|say|reply|text|answer|freeze|chill|cool|defrost|thaw|soak|rinse|"
    r"change|adjust|"
    r"scrub|boil|bake|roast|fry|cook|chop|slice|peel|stir|mix|whisk|season)\b"), re.I)
# A statement opens on the same verb a method does and then says what the thing does: "Rest is what
# it needs", "Warm weather makes it worse", "Dry air helps a lot" all read as a method once the
# opening can be a verb, and none of them tells the person what to do. The words just after the verb
# tell the two apart. Only finite verbs are listed: "Drink plenty of water", "Eat more fibre" and
# "Rest 10 minutes" are methods whose object is a quantity, so a determiner list would lose them.
SAYS_WHAT_IT_DOES = frozenset((
    "is", "are", "was", "were", "am", "makes", "make", "made", "helps", "help", "needs",
    "need", "seems", "happens", "takes", "gives", "keeps", "does", "comes", "goes", "looks",
    "sounds", "stops", "starts", "works", "hurts", "depends", "matters", "causes", "means",
    "prevents", "beats", "lowers", "raises", "reduces", "improves", "eases", "dries", "warms",
    "cools", "stays", "gets",
    # The third person and the base form of the same verbs: a plural subject's verb is as often the
    # one that turns a statement into a statement ("Rest days matter more than you think", "Sleep
    # debt builds up over weeks") and only the forms on the list were refused, so three statements
    # read as methods again. None of these can follow a method's verb before its object - "Rest
    # days" is not the object of "Rest" - so they cost no method.
    "matter", "build", "builds", "vary", "varies", "cost", "costs", "change", "changes",
    "depend"))
# A method does not always open with a verb: "A damp cloth with washing-up liquid takes off most
# marks" is the instruction, and so is anything after a colon that opens on a verb.
# A method told as the routes to it: "Three routes: a council bulky waste collection (usually
# charged), the tip if you can drive it there, or a charity that collects". The head names the
# means and the list after the colon is the way, so the reply answers a how question with no
# instruction verb anywhere. A set of facts about a thing is not one of these, so the head has
# to carry the word for a means.
MEANS_NAMED = re.compile(
    r"^[^:]{0,40}\b(?:routes?|ways?|options?|methods?|approaches?|choices?)\b\s*:", re.I)

MEANS_OF = re.compile(
    r"\b(?:with|using) (?:a|an|some|the)\b.{0,40}\b(?:takes? (?:off|out|away)|lifts?|removes?|"
    r"cleans?|works|does it|gets? (?:rid of|it off))\b"
    r"|:\s*(?:follow|put|take|give|get|ask|ring|call|send|keep|check|book|use|do|start|run|"
    r"leave|try|add|make|go)\b", re.I)


# A method often puts its reason first and the instruction after it: "Streaks are an uneven coat,
# not a bad paint: roll in strips a roller wide and lap the last strip while it is still wet",
# "Sticking is nearly always a wet dough meeting a dry surface, so the fix is less water and more
# flour where the two meet. Chill the pastry 20 to 30 minutes before rolling." Reading only the
# opening clause called both of those a definition, so a how-to answered with its own cause was
# scored as a question the bot had not answered. The instruction after a colon or a semicolon, and
# the sentence after a one-clause reason, are part of the same answer.
#
# A request for information is not one of those instructions: "Happy to. Tell me what's going on
# and we'll take it from there" opens on a nod, and the telling is the person's job, not a step.
WANTS_INFO = re.compile(r"^(?:tell me|say which|let me know|say more)\b", re.I)


def _asks_the_person(said):
    """True when this text asks the person something rather than telling them a step.

    The nod words are read at its head. A question mark counts only in the sentence the text opens
    on, because a method often ends on a question about the person and that does not take the
    method back: "Pick one thing you can finish inside it. Are you on your own?" told them how, and
    "Give it ten minutes. How does it look then?" is a step with a check after it.

    A bare `?` used to be the first alternative of `WANTS_INFO`, and that pattern is only ever
    read with `re.match`, which looks at the start of the text and nowhere else: the alternative
    could only fire on a text beginning with "?", so every reply that ended "...how long is the
    run?" was read as an instruction because the "?" was never looked for. Searching the whole
    text fixes that and goes too far the other way - "Who's in charge?" then cancelled the method
    in front of it - so the mark is read inside the sentence the clause opens on.
    """
    said = " ".join(str(said or "").split())
    if not said:
        return False
    if WANTS_INFO.match(said):
        return True
    return "?" in re.split(r"(?<=[.?!])\s", said, 1)[0]
# A step is an instruction, and an instruction has no subject: the verb comes first and the thing
# it acts on comes straight after - "Chill the pastry 20 to 30 minutes", "Lift it back between the
# posts", "Pump to the range printed on the tyre". A statement puts something else there ("Nuts
# keep 3 to 6 months", "Radiators that are hot", "Sticking is nearly always"), which is how the
# two are told apart without a list of every verb in the kitchen.
NOT_A_VERB = frozenset((
    "the", "a", "an", "this", "that", "these", "those", "it", "its", "it's", "they",
    "you", "your", "we", "our", "i", "my", "me", "he", "she", "his", "her", "there",
    "here", "what", "which", "who", "why", "how", "when", "where", "if", "once", "after",
    "before", "for", "with", "on", "in", "to", "of", "at", "by", "from", "so", "but",
    "and", "or", "also", "then", "never", "always", "most", "some", "all", "every", "any",
    "no", "not", "one", "two", "both", "each", "few", "many", "more", "less", "very"))
IMPERATIVE = re.compile(
    r"^([A-Za-z']+)\s+(?:a|an|the|your|their|its|it|them|these|those|some|one|two|each|every|"
    r"both|all|him|her|me|us|my|out|in|up|down|off|on|away)\b", re.I)


# A verb that hands the person a list of things rather than a job to do: "Take a notebook, a pen,
# your ID and the paperwork they asked for" is the list of things asked for, said as an
# instruction. A step is still a step ("Chop the onions, garlic and ginger" is one job with three
# parts), so only the verbs that introduce things are let through.
THINGS_VERB = re.compile(r"^[^\w]*(?:take|bring|pack|get|buy|grab|carry|put in)\b", re.I)


def _an_instruction(sentence):
    """True when the sentence tells the person to do something that is not fetching things."""
    return bool(_imperative(sentence)) and not bool(THINGS_VERB.match(sentence or ""))


def _imperative(sentence):
    """True when `sentence` is shaped like an instruction: a verb and the thing it acts on."""
    m = IMPERATIVE.match(sentence or "")
    if not m:
        return False
    word = m.group(1).lower().strip("'")
    # "Opening it lets the air out" is a statement about the doing, not an instruction to do it.
    return word not in NOT_A_VERB and not word.endswith("ing")


def _opens_on_a_job(sentence):
    """True when `sentence` is an instruction and not a statement that opens on a verb.

    "Look, it happens" is an aside however the verb list reads it, so an opening that is only the
    verb and then punctuation is not one, and a finite verb within the first few words is the
    sentence's own subject rather than something to act on.
    """
    m = JOB.match(sentence or "")
    if not m:
        return False
    first = re.split(r"[,;:]", (sentence or "")[m.end():], 1)[0]
    words = re.findall(r"[A-Za-z']+", first)[:3]
    if not words:
        return False
    return not any(word.lower() in SAYS_WHAT_IT_DOES for word in words)


# ------------------------------------------------------------------------------- the subject

# The words a line and a reply share without the reply being about the same thing: the question
# words, the helper verbs and the judgement words. NOT_A_VERB holds most of them already.
_NOT_THE_SUBJECT = NOT_A_VERB | frozenset((
    "does", "did", "can", "could", "should", "would", "will", "shall", "was", "were", "are",
    "have", "has", "had", "get", "got", "make", "made", "need", "needs", "want", "wants",
    "like", "likes", "good", "bad", "better", "best", "okay", "fine", "worth", "still",
    "really", "think", "know", "sure", "same", "keep", "keeps", "take", "takes", "mean"))


def _stem(word):
    """The word without the ending that would keep it from matching its other form."""
    for end in ("ing", "ed", "es", "s"):
        if word.endswith(end) and len(word) - len(end) >= 4:
            return word[:-len(end)]
    return word


def _subject_words(text):
    """The words in `text` that name a thing, as stems, with a title left out.

    "Frozen" in "Idina Menzel is the voice of Elsa in Frozen" is the film, not the frozen food
    the line asked about, so a capital in the middle of a reply is a name rather than a subject.
    """
    said = str(text or "")
    words = set()
    for match in re.finditer(r"[A-Za-z']+", said):
        word = match.group(0)
        low = word.lower().strip("'")
        if len(low) < 4 or low in _NOT_THE_SUBJECT:
            continue
        if word[:1].isupper() and match.start() and said[match.start() - 1] not in ".!?":
            continue
        words.add(_stem(low))
    return words


def _the_same_subject(opening, line):
    """True when the reply speaks about the thing the line named.

    Not a claim that the reply answers the line: it is the reason the shape of the reply cannot
    be read against the shape the line asked for, because a yes or a no in words is a statement
    about the thing, and the statement is the one shape that has no cue list.
    """
    if not line:
        return False
    return bool(_subject_words(line) & _subject_words(opening))


def _steps(opening, after=""):
    # A method is one instruction as often as a list, and the verb a person would use is not
    # always on INSTRUCTS: "Find the plasterboard screws instead of hunting for timber" answers
    # "how do i find a stud in a wall" and was read as a reply about something else, because
    # INSTRUCTS is a short list and "find" is not on it. `JOB` is that list plus the everyday
    # verbs, and `_opens_on_a_job` keeps a statement that happens to open on one of them out.
    if (DOES_NOT.match(opening) or DOES.search(opening) or MEANS_OF.search(opening)
            or MEANS_NAMED.match(opening) or _opens_on_a_job(opening)
            or A_CALCULATION.match(opening)):
        return True
    for part in re.split(r"[:;]", opening)[1:]:
        part = part.strip()
        if part and (INSTRUCTS.match(part) or DOES.search(part) or _imperative(part)):
            return True
    if after and not _asks_the_person(after):
        if INSTRUCTS.match(after) or DOES.search(after) or _imperative(after):
            return True
    return False


# The same verb where the reply starts a new clause: "A dripping tap is nearly always a worn
# washer: turn the water off", "The sun does the fading, so block the light", "If it is still
# worrying you, get it looked at today". A step in a written method starts after a full stop, a
# colon or a comma with "then"/"so"/"and" in front, and often nowhere near the opening.
INSTRUCTS_CLAUSE = re.compile(
    r"(?:^|[.:;!?]\s+|,\s+(?:then|so|and|but|just|or)\s+|,\s+)(?P<verb>be|"
    + INSTRUCTS.pattern.split("(?:", 1)[1], re.I)


def _instruction_after_a_clause(text):
    """True when some clause of `text` after the first starts on a method's verb.

    A clause that asks the person for the information is not one of them: "Tell me what's going
    on", "Say which one you are on" is the person's next move, not a step of the answer.
    """
    for m in INSTRUCTS_CLAUSE.finditer(text):
        if _asks_the_person(text[m.start("verb"):]):
            continue
        if m.start() == 0 and not _opens_on_a_job(text):
            # The opening is not a clause after the first one, and a statement that happens to
            # open on a verb is not a method: "Look, it happens", "Rest is what it needs".
            continue
        return True
    return False


def _steps_in(reply):
    """True when the reply gives a method, read over the whole reply and not only its opening.

    Every other shape is the first sentence, because STYLE.md asks for the answer there and a
    figure three paragraphs down is not the reply the person got. A method is the exception: the
    answer to a how question *is* the sequence, so "A dripping tap is nearly always a worn washer:
    turn the water off at the isolating valve" and "Most veg keeps about a week: keep it in the
    fridge drawer" are a method told over two sentences, and the instruction often starts a later
    clause ("Lower eggs into already boiling water: 6 minutes for a runny yolk"). Reading only the
    opening called 114 of 294 good step replies a miss on the deck. A list of dishes with their
    times ("Quick: tuna pasta in 15, a frittata in 20") is a few ideas, not a method, and is left
    to `_options`.
    """
    text = " ".join(str(reply or "").split())
    if not text:
        return False
    if _steps(first_sentence(text), second_sentence(text)):
        return True
    return _instruction_after_a_clause(text)


# A few ideas is more than one: an "or" between two, a numbered list, or two commas and an "and".
# One idea on its own is a pick if anything, and a card that names one thing has not answered
# "any ideas".
# The second idea named as one: "something else that works is a potato curry", "another one is a
# walk round the block", "the other option is a traybake".
NEXT_IDEA = re.compile(
    r"\b(?:something|anything) else\b|\banother (?:one|option|idea|way|approach|thing)\b"
    r"|\balternatively\b|\botherwise\b|\bthe other (?:option|idea|one)|\boption (?:two|2)\b"
    r"|\bsecond option\b", re.I)
# A colon that hands over a list is a few ideas: "In Rome: the Colosseum, the Pantheon, and
# Trastevere". A plan for one evening is not, and what tells them apart is the order: "a film, a
# walk and a call at 8pm, then tea" is one thing after another, so a sequencing word takes it out.
LIST_AFTER_COLON = re.compile(r":\s*\w[^:]*,\s*\w")
# Two things each named with what it is for, with no "or" and no colon to hand the list over:
# "*The Money To The Masses Podcast* is the plain-English one, *Meaningful Money* for pensions and
# savings, and *Moneybox* for news you can use". Each item carries its own use, which is what makes
# it a list of ideas rather than one idea with a long tail. A method that gives a time for one step
# and another for the next ("simmer for 10 minutes, then the beans for 5") is a sequence, so a
# sequencing word takes it out, the same way it takes out a list after a colon.
FOR_A_LIST = re.compile(r"\bfor\b[^,.;:]{2,70},\s*[^,.;:]{0,70}\bfor\b", re.I)
# A "for" that hands out a length of time belongs to a step, not to a thing's use: "firm it for a
# minute, and water it for ten" is a method with a duration on each step. The same "for" in
# "*Meaningful Money* for pensions" says what the thing is good for.
FOR_A_TIME = re.compile(
    r"\bfor\s+(?:about\s+|around\s+|roughly\s+|just\s+|another\s+|a good\s+|"
    r"at least\s+|up to\s+|half an?\s+)?"
    r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|fifteen|twenty|thirty|forty|"
    r"fifty|sixty|ninety|a|an|each|every)\s*-?\s*"
    r"(?:seconds?|secs?|minutes?|mins?|hours?|hrs?|days?|nights?|weeks?|months?|years?|"
    r"while|bit|moment|spell)\b", re.I)
SEQUENCES = re.compile(r"\b(?:then|after that|afterwards|next|finally|once|first)\b", re.I)


# What a comparison says: one side set against the other. The words are the ones people use for
# it - a contrast ("whereas", "unlike", "but"), both of them at once ("both", "either"), or one side
# judged against the other ("cheaper", "quieter", "lasts longer") - and never a bare "and", which
# joins two things in any reply at all.
CONTRAST = re.compile(
    r"\b(?:whereas|unlike|both|either|but|while|the difference|differs?|compared|comparison|"
    r"on the other hand|the other way|instead|rather than)\b"
    r"|\b(?:cheaper|dearer|quieter|louder|faster|slower|easier|harder|bigger|smaller|"
    r"longer|shorter|better|worse|more|less|stronger|weaker|heavier|lighter)\b"
    r"|\bthan\b", re.I)


def _a_comparison(opening):
    """One side of a pair set against the other, in the reply's own words."""
    return bool(CONTRAST.search(opening))


# "Three that work with children, easiest first: ..." counts the things it is about to list, and a
# list of counted things is a menu. "Ninety seconds in this order" counts time, not things.
COUNTED_LIST = re.compile(
    r"\b(?:two|three|four|five|six|a few|several|a couple of|pair of)\b", re.I)
A_TIME_COUNT = re.compile(
    r"\b(?:two|three|four|five|six|a few|several|a couple of)\s+"
    r"(?:seconds?|minutes?|hours?|days?|weeks?|months?|years?|times|per cent|percent)\b", re.I)
# The items after a colon: two commas, or an "and" and a comma, in the same sentence.
_LIST_OF_THINGS = re.compile(r"[^:]{0,200}:\s*[^.]{0,300}", re.I)


def _a_list_of_things(opening):
    """True when a colon in the sentence opens a list of two or more things."""
    found = _LIST_OF_THINGS.search(opening or "")
    if not found:
        return False
    after = found.group(0).split(":", 1)[1]
    return after.count(",") >= 2 or (after.count(",") >= 1 and re.search(r"\band\b", after, re.I))


def _options(opening):
    if re.search(r"\b(?:1\.|1\)|first option|option one|one idea)\b", opening, re.I):
        return True
    # An "or" is the difference between two ideas and the parts of one plan: "a film, a walk and
    # a call at 8pm, then tea" is one evening, and it has no "or".
    if re.search(r"\bor\b", opening, re.I):
        return True
    if ";" in opening:
        return True
    # A second idea handed over as one, and a colon that opens a list: "something else that works
    # is a potato curry", "In Rome: the Colosseum, the Pantheon, and Trastevere". Both are two or
    # more ideas said out loud with no "or" in them.
    if NEXT_IDEA.search(opening):
        return True
    if (FOR_A_LIST.search(opening) and not FOR_A_TIME.search(opening)
            and not SEQUENCES.search(opening)):
        return True
    if LIST_AFTER_COLON.search(opening) and not SEQUENCES.search(opening):
        return True
    # A colon that opens three or more things is a few ideas even when the reply leads with the one
    # that matters: "Fix the wake-up time first: the same hour every day, including after a bad
    # night, a cool dark room, and getting up if you are awake for 20 minutes" is the few things
    # "any tips for getting through the day on no sleep" asked for, and the "first" before the
    # colon kept it out of the arm above. A colon that opens one method's steps is a recipe, not a
    # few ideas - "Courgette and mushroom pasta: fry the mushrooms hard, add the courgette, then
    # toss with pasta" - so what follows a colon and reads as instructions is left alone.
    if LIST_AFTER_COLON.search(opening) and _three_things_after_the_colon(opening):
        return True
    # And two things said side by side with an "and" are the same offer: "Make up the best bed and
    # plan one shared outing a day" answers an ask for ideas with two of them.
    return _two_things_to_do(opening)


# Two or three things to do, said side by side with an "and" between them: "Make up the best bed
# and plan one shared outing a day" is two ideas offered, not one method. Each clause has to open
# on an instruction verb, so "the best bed and breakfast in town" is not this, and a plan said
# with "first"/"then" is a method and is left to the steps arm.
PLAN_VERB = re.compile(r"^(?:plan|block|book|aim)", re.I)


def _two_things_to_do(opening):
    head = re.split(r"\.\s", opening, maxsplit=1)[0].rstrip(".")
    if SEQUENCES.search(head):
        return False
    # Two things in a row is the offer; the tail of the second one ("so the flat is mainly for
    # sleeping") is part of the same sentence and not a third thing, so only the leading run of
    # instruction clauses counts, and it has to be two long.
    found = 0
    for part in re.split(r",?\s+and\s+", head):
        part = part.strip()
        if len(part.split()) < 2 or not (INSTRUCTS.match(part) or PLAN_VERB.match(part)):
            break
        found += 1
    return found >= 2


def _three_things_after_the_colon(opening):
    """True when what follows the first colon is three or more things, not one plan's steps.

    The "first" that a wake-up-time list opens with is the reply picking out the one thing that
    matters, and it is before the colon, so a sequence word after the colon is the only one that
    makes what follows a plan: "One evening: a film, a walk and a call, then tea" is one evening.
    """
    parts = re.split(r":", opening, maxsplit=1)
    if len(parts) < 2:
        return False
    after = parts[1].strip()
    if INSTRUCTS.match(after) or SEQUENCES.search(parts[1]):
        return False
    return len(re.findall(r",\s+\S", parts[1])) >= 2


# A reason is a cause in the opening: "because", "that's why", "the reason", "so that", "due to".
CAUSE = re.compile(
    r"\b(?:because|that'?s why|which is why|the reason|reason is|since|so that|due to|"
    r"comes? from|caused by|it happens|the cause|as a result|is down to|thanks to|"
    r"which means|means that|at which|stems? from|leads? to|that'?s what|"
    r"that is what|this is what|is what makes)\b|, so\b"
    # A why-answer names the cause as the thing itself: "Minced meat goes tough and grainy when it
    # is cooked too long", "Brown, crisp tips are usually the water", "the sun lights up the air
    # so brightly that their faint light is drowned out".
    r"|\b(?:goes?|gets?|turns?|becomes?|comes? out|feels?)\b.{0,40}\b(?:when|if|because)\b"
    r"|\b(?:is|are) (?:usually|often|nearly always|mostly|generally|really|just) the\b"
    # A cause told as what the effect means, with the word that makes it a reading rather than an
    # instruction: "it often means an upset stomach, boredom or a need for fibre". "which means" was
    # already in this list; bare "means" is advice ("this means you should ring the vet"), and the
    # adverb is what makes it a diagnosis.
    r"|\b(?:often|usually|sometimes|mostly|generally|nearly always|probably)\s+means?\b"
    r"|\bso\b.{0,40}\bthat\b"
    # A cause can be named as the thing itself rather than by a joining word: "The colour is the
    # soil rather than the plant", "The green ring is iron from the yolk meeting sulphur ...,
    # which happens when an egg is cooked too long".
    r"|\b(?:is|are|was|were) (?:the|a|an) .{0,50}\b(?:rather than|not)\b"
    r"|\b(?:which |that )?happens? (?:when|if|because)\b"
    # and the cause named as the occasion with the emphasis on it: "That is normal, especially in
    # the first few days or when something new has arrived" answers why a cat hides and was read
    # as no answer. Only the emphasis: a plain "or when you get home" is a method, not the cause.
    r"|\b(?:especially|particularly) (?:when|if|in)\b"

    # The cause named as the process the effect went through, set against what it was not:
    # "Soggy roast potatoes were steamed rather than roasted".
    r"|\b(?:is|are|was|were)\s+\w+ed\s+rather than\b"
    # A change of state named as the effect, and what brings it on: "Food sticks when there is not
    # enough heat or fat", "Wifi fades with distance".
    r"|\b(?:sticks?|stuck|smells?|smelt|tastes?|fades?|squeaks?|clicks?|wobbles?|sags?|leaks?|"
    r"cracks?|burns?|turns?|goes?|gets?|comes? out|feels?|looks?|sounds?|happens?|builds? up|"
    r"collects?|gathers?|settles?|clings?|pools?|spreads?|grows?|stops?|dies?|fails?|drops?|"
    r"floats?|sinks?|rises?|falls?|heats?|cools?|shrinks?|expands?|swells?|warps?|splits?|"
    r"melts?|freezes?|curdles?|separates?|wears?|rots?|wilts?|droops?|curls?)\b"
    r".{0,25}\b(?:when|if|because|with|from)\b"
    # A cause named by its condition needs no joining word at all: "Dense bread is usually
    # under-proved or over-kneaded", "a starter that has stopped rising is usually hungry, cold
    # or both", "the reason is too much water" - the condition itself is the cause.
    r"|\b(?:is|are|was|were|has|have|had)\s+(?:usually|often|normally|mostly|generally|probably|"
    r"most likely|nearly always|just|really|only|simply)?\s*(?:(?:under|over|un)\w+|"
    r"\btoo\b|\bnot\b)\s*\w*\b"
    # "A doughy loaf has not had long enough in the oven, or it did not prove enough": a shortfall
    # said as a plain statement is the cause.
    r"|\b(?:has|have|had|did|does|do|is|are|was|were)\s+not\s+\w+\s+(?:long\s+)?enough\b"
    # A cause told after a comma: "A loaf that collapses rose and then fell back, which is a prove
    # that ran too long".
    r"|,\s*which\s+(?:is|was|means)\b"
    # The cause said as a list of conditions: "is usually hungry, cold or both".
    r"|\b(?:is|are|was|were)\s+(?:\w+\s+)?\w+\s*,\s*\w+\s+or\s+(?:both|so|else)\b"
    # A comparison names the cause by naming what it is not: "most constant tiredness is dull
    # rather than medical", "a musty smell is usually damp rather than dirt".
    r"|\b(?:is|are|was|were)\b[^.;:!?]{0,40}\brather than\b"
    # The cause named as the thing itself, with the ground after it: "Cloudy tea is the minerals
    # in hard water binding with the tannin", "An allergy is the immune system mistaking something
    # harmless for a threat". A noun phrase with a participle on the back of it is the mechanism.
    # The participle has to be the noun's, not an infinitive that happens to end in "-ing":
    # "It is a good idea to ring them first" is advice, and "ring" is not the mechanism.
    r"|\b(?:is|are|was|were)\s+(?:the|a|an)\s+\w+(?:\s+\w+){0,4}\s+(?:(?<!to )\w+ing|\w+ed)\b"
    # "Stale bread is dry, not spoilt", "most of it is habit, not hunger": a condition set beside
    # the one it is not.
    r"|\b(?:is|are|was|were)\s+(?:\w+ly\s+)?\w+\s*,\s*not\b"
    # A cause told as what the thing does to something else: "The Moon's gravity pulls the sea
    # towards it, making a bulge on the near side", "a food - for a threat and releasing
    # histamine, which causes the itch". A participle or a which-clause after a comma is the
    # effect that explains it.
    r"|,\s*(?:making|leaving|causing|giving|sending|turning|setting|which\s+(?:makes|causes|leaves|gives))\b"
    r"|\b(?:which|that)\s+causes?\b"
    # A reason handed over as a numbered set: "Three things keep a fried coating crisp: a dry
    # surface, oil that is hot enough, and air under it". The set has to be named - a word follows
    # the count - because "Two things:" on its own is a label, and what is behind the colon is the
    # method ("Two things: grind it coarser and use cooler water"), which `_head_explains` reads.
    r"|\b(?:one|two|three|four|five|\d+)\s+(?:things|reasons|causes|factors|suspects)\s+\w"
    # Two causes offered side by side name the cause without a joining word: "One channel going
    # funny is the aerial or the box, and every channel is the set".
    r"|\b(?:is|are|was|were)\s+(?:the|a|an)\s+\w+(?:\s+\w+)?\s+or\s+(?:the|a|an)\b"
    # A condition stated flatly after the verb, with the ground after a dash: "Waking in the night
    # is normal - sleep runs in cycles of about ninety minutes".
    r"|\b(?:is|are|was|were)\s+(?:\w+\s+)?\w+\s+[-\u2013\u2014]\s+\w"
    # Two causes beside each other name the cause with no joining word at all: "A suddenly louder
    # exhaust is nearly always a hole or a blown joint", "A smell from a kettle is nearly always
    # scale or water left standing in it".
    r"|\b(?:is|are|was|were)\s+(?:nearly always|usually|often|mostly|always|almost always)?\s*"
    r"(?:the|a|an)?\s*\w+(?:\s+\w+){0,2}\s+or\s+(?:the|a|an)\b"
    # The cause named as what it is instead of, or what it points at: "They take oxygen out of the
    # water instead of the air", "the best evidence points at flies and heat".
    r"|\binstead of\b|\bpoints? (?:at|to)\b"
    # The mechanism named as what the thing is doing, and what it is doing it from: "A cactus that
    # has gone soft is rotting from too much water".
    r"|\b\w+ing\s+(?:from|off|through)\b|\bfrom\s+(?:too|not|lack of|a lack)\b", re.I)


# The commonest why-answer names the cause as what the effect *is*, with no connective at all:
# "The smell is a film of food and bacteria in the overflow", "Lumps are flour that met hot liquid
# without being spread through fat", "A whirr with no cranking is the starter turning". The cause is
# a thing, so the rule asks for a copula and then a word that ties the thing to the effect ("a film
# of", "flour that", "the starter turning", "water at the roots"), three words of slack for "the
# slow build-up of".
#
# This one is read with the line, not the reply alone: on its own it credits a sentence that shares
# nothing with the question ("A whirr with no cranking is the starter turning" is not the cause of a
# sore throat), so the opening has to name a thing the line named. A preposition on the far side of
# a comparison is the other side of it, not the cause: "once it is cooler outside than in" is not a
# why-answer either.
CAUSE_IS = re.compile(
    r"\b(?:is|are|was|were)\s+(?:usually\s+|often\s+|mostly\s+|nearly always\s+|generally\s+)?"
    r"(?:(?:a|an|the)\s+)?[a-z][a-z-]*(?:\s+[a-z][a-z-]*){0,3}\s+"
    r"(?:of|that|which|from|turning|sitting|going|coming|leaving|building|"
    r"(?<!than )(?<!more )(?<!less )\b(?:in|on|at|under))\b", re.I)


# A cause is also told as a plain statement about the thing, with the condition after the verb:
# "A cake sinks when it's underbaked", "The sauce splits if it boils", "Bread goes stale when it is
# kept cold". The verb is any finite one, and the words after the "when" are the cause.
CAUSE_WHEN = re.compile(
    r"\b(?:\w+s|\w+ed|is|are|was|were|gets?|got|goes|go|came|comes)\b\s+(?:when|if|because)\b",
    re.I)


# The cause named as what the effect asks for, with no joining word: "A soggy pastry base wants
# more heat underneath it and less water in the filling", "A slow starter needs a warmer spot".
# The thing is the subject - "you want to add salt and taste it" is an instruction, so the person
# as subject is not this reading.
WANTS_THE_CAUSE = re.compile(
    r"\b(?:wants?|needs?|craves?|is asking for|is crying out for|is begging for)\b", re.I)
WANTS_OF_THE_PERSON = re.compile(
    r"^(?:you|i|we|they|he|she|one|people|somebody|someone)\s+(?:just\s+|really\s+|only\s+)?"
    r"(?:want|wants|need|needs|will want|will need)\b", re.I)


# A mechanism told as the count of things the effect needs: "A cake rises on three things - the air
# you beat in, the bubbles the raising agent makes, and steam - and when one of them is missing the
# cake stays flat". The number and the plural noun are what make it a mechanism; "work on the car"
# names none, and a menu of things to serve is a menu. It is read *after* the imperative guard,
# because "mix on three things: the flour, the eggs and the milk" is a method, not a cause.
A_COUNT_OF_THINGS = re.compile(
    r"\b(?:on|down to)\s+(?:two|three|four|five|several|a few)\s+"
    r"(?:things|reasons|factors|parts|steps|rules)\b", re.I)

# The point of a thing said as its purpose: "the point of it is to pull the water out of the air",
# "its job is to keep the damp down", "the purpose is to keep the noise in". A purpose is the
# reason a thing is done, and it holds no cause word at all.
PURPOSE = re.compile(
    r"\bthe point of (?:it |them |this |that )?(?:is|was)\b"
    r"|\b(?:its|their|his|her) (?:job|point|purpose|use) is\b"
    r"|\bthe (?:point|purpose|job|use) is (?:to|that)\b", re.I)
# The purpose said as the opening clause of the reply: "To be useful with the ordinary things",
# "For keeping the damp down in a cellar". An instruction opens on a verb and is not this.
PURPOSE_TO = re.compile(r"^(?:it is |its |the )?(?:to|for) [a-z]+", re.I)
# Whether a thing is worth its cost or its trouble, said as the merit of it: "worth it if the roof
# faces south", "worth having in any home", "usually yes - spaying cuts the risk".
MERIT = re.compile(
    r"\bworth it\b|\bworth having\b|\bworth doing\b|\bworthwhile\b|\bworth the\b"
    r"|\b(?:usually|generally|probably|mostly) (?:yes|no|worth)\b"
    r"|\b(?:yes|no)\b[^.!?]{0,40}\b(?:if|when|unless|for|in a|as long as)\b", re.I)


def _a_reason(opening, line=None):
    if CAUSE.search(opening):
        return True
    # A purpose answers the point of a thing and a merit answers whether it is worth it: neither
    # carries a cause word, and a description of the thing carries neither.
    # Some whys are answered with the state of the evidence rather than a clean cause, and that
    # is the answer: "why do zebras have stripes" / "Nobody knows for certain, and the best
    # evidence points at flies and heat rather than camouflage". The hedge alone is still a
    # shrug - it is the evidence named after it that makes it the reason the person asked for.
    if (PURPOSE.search(opening) or PURPOSE_TO.match(opening) or MERIT.search(opening)
            or (UNSETTLED.search(opening) and EVIDENCE_SAYS.search(opening))):
        return True
    # A method that names its moment in a "when" is not a cause: "Take it out when the timer goes",
    # "Add the eggs when the water boils". The instruction at the *front* is what tells them apart -
    # not a method further in, because a why-answer often gives the cause and the remedy after it:
    # "A creamy soup curdles when it gets too hot: keep it under a simmer and stir the cream in off
    # the heat". The cause is in the first clause and the remedy does not take it away.
    if INSTRUCTS.match(opening) or DOES_NOT.match(opening):
        return False
    # A head that sends the person on names no cause: "A headache that has gone on for three days
    # or more is one to have looked at: book a GP appointment" is an identification of the thing,
    # and the cause is never said. The same guard already stands on the head before a colon.
    if SENDS_THEM_ON.search(opening):
        return False
    if CAUSE_WHEN.search(opening):
        return True
    # The effect itself says what it wants, and that is the cause: "A soggy pastry base wants more
    # heat underneath it", "A starter that has stopped rising needs a warmer spot". Read only when
    # the reply opens on the thing the line named, because "you want to add salt" is advice about
    # what to do, and a want about anything at all is not a cause.
    # Only with the line in hand: without it the same reading widens the yes/no wide read, where a
    # want about anything at all would pass as a verdict on anything at all.
    if (line is not None and WANTS_THE_CAUSE.search(opening)
            and not WANTS_OF_THE_PERSON.match(opening) and _names(opening, line)):
        return True
    if A_COUNT_OF_THINGS.search(opening):
        return True
    # The effect-is-the-cause form is the one that needs the line: without something named in both
    # it is a sentence about anything. Without a line to compare with, the shape is all there is.
    return bool(CAUSE_IS.search(opening)) and (line is None or _names_the_subject(opening, line))


# The two halves of "nobody knows for certain, and the best evidence points at ...": what is not
# known, and what the evidence does say. Both are needed, so a shrug followed by an opinion is not
# a reason, and an unhedged statement of evidence is left to the cause readings.
UNSETTLED = re.compile(
    r"\b(?:(?:nobody|no one|no-one) (?:really )?(?:knows|is sure|can say|agrees)|"
    r"it is not (?:known|certain|settled|clear)|(?:unclear|unsettled|still debated?|"
    r"a matter of debate|not fully understood))\b", re.I)
EVIDENCE_SAYS = re.compile(
    r"\b(?:evidence|studies|research|the work on it|experts|biologists|historians|"
    r"economists|scientists)\b[\w\s,'\u2019-]{0,40}?"
    r"\b(?:points? (?:at|to)|suggests?|shows?|indicates?|thinks?|suspects?|"
    r"leans? (?:to|towards)|is that)\b|\bbest (?:guess|evidence)\b", re.I)


# The head of a reply before its colon, when that head is a statement rather than a label. A
# cause said as an identification - "<symptom> is <cause>" - is the shape of most why-answers,
# and the fix behind the colon is not a different answer to the same question.
EXPLAINS = re.compile(
    r"\b(?:is|are|was|were|means?|comes? from|happens? (?:when|if|because)|because|"
    r"the reason|"
    # The cause can be the subject of a bringing or a leading verb, with no "because" anywhere:
    # "Cutting down or quitting brings a headache 12 to 24 hours after the last cup", "a loose
    # wire causes the flicker", "mould sets off the cough". The head of a why-answer that says
    # what the cause does to the person is the cause, and the fix after the colon is the answer.
    r"causes?|caused|brings?|brought|leads? to|led to|sets? off|triggers?|gives? you|"
    r"is behind|is down to|stems? from|comes? down to)\b", re.I)


# "<thing> is one to have looked at" is an "is" and not a cause. The head of a why-answer that
# sends the person on ("A headache that has gone on for three days or more is one to have looked
# at: book a GP appointment") reads as an identification of the thing, and the cause is never
# said, so it is not a reason.
SENDS_THEM_ON = re.compile(
    # A bare "to" after "one" is a range as often as it is a job: "gone in one to two weeks" and
    # "one to two hours" are lengths, and only a verb after the "to" says the person has been sent
    # to a thing ("one to have looked at", "one to get checked"). "worth" needs no verb.
    r"\b(?:one|something|a thing|the kind of thing)\s+(?:worth|to (?:have|get|see|go|ring|call|book|"
    r"check|ask|look|speak|talk|keep|take|make|do|be|try|use|buy|find|stop|fix|start|wait|leave|"
    r"stay|read|watch|wash|clean|test|measure|move|change|put|give|send|pay|see))\b|"
    r"\b(?:book|ring|call|see|visit)\s+(?:a|the|your)\s+(?:gp|doctor|vet|dentist|nurse)\b|"
    r"\bappointment\b|\blooked at\b|\bchecked out\b", re.I)


def _head_explains(opening):
    """True when what comes before the colon states the cause, so a method after it is the fix."""
    head = opening.split(":", 1)
    if len(head) < 2:
        return False
    if SENDS_THEM_ON.search(head[0]):
        return False
    return bool(EXPLAINS.search(head[0])) and not _imperative(head[0])


# The readings strong enough to fail a reply for. A duration or a figure, a method, a named kind
# of place, a role, a definition, a verdict frame and a named side are what a reply is *about*,
# so one of them in a reply to a different question is a fault the check can name. The weaker
# readings that pass a reply - a capital after a preposition, a name in the middle of a
# sentence, a "fine" inside the sentence, a bare noun - are left out: "Rome." passes as a place
# and is not evidence that a reply to a how-long question is about a place.
#
# The distinction is not cosmetic. Every widening of a reading makes replies pass, and a wide
# reading used as evidence makes good replies fail: `<thing> is <description>` passes as a
# definition ("On an iPhone it is Settings > Mobile Data..."), but as evidence it failed the
# steps reply that says it, and a why-answer ("The green ring is iron from the yolk..."), and a
# yes/no ("Apples are picked ripe and keep, so judge by feel"). So `_CLEAR` keeps the narrow
# reading of the shape and the checks keep the wide one - the same asymmetry as `_FIGURES`.
# A contrast is not a stated preference. "the cupboard rather than beside the hob" answers "where
# do i keep cooking oil", "contained rather than pruned" answers "how do i stop bamboo taking
# over", "agree it before you sign rather than after" answers a rent sum, and "towards a window
# rather than towards the screen" answers "why are my selfies blurry". The bare "rather" in each
# cleared the shape the line asked for and called a real answer a miss, so the failing side stops
# counting it. The passing side keeps it (`PREFERS`, read with the line): "dry it with a towel
# rather than a hairdryer" is still the pick for "got a stain on the sofa, no idea what from".
_PREFERS_STATED = re.compile(PREFERS.pattern.replace("|rather|", "|", 1), re.I)

# A reply that opens on the reading it gives: "74C", "£40", "20 miles", "two weeks", "half an hour".
FIGURE_HEAD = re.compile(
    r"^[£$\u20ac]?\s?\d|^[\u00bd\u00bc\u00be]|^(?:one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|fifteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|"
    r"a hundred|half a)\b", re.I)


_CLEAR = (
    (TIME, _a_clear_time_at_the_head),
    (AMOUNT, _an_amount_at_the_head),
    (STEPS, _steps),
    (PLACE, lambda opening: bool(PLACE_AS_EVIDENCE.search(opening))),
    (PERSON, lambda opening: bool(PERSON_WORD.search(opening))),
    (MEANING, lambda opening: bool(MEANS.search(opening))),
    (YESNO, lambda opening: bool(VERDICT_OPEN.match(opening))),
    (PICK, lambda opening: bool(_PREFERS_STATED.search(opening))),
    (REASON, lambda opening: bool(REASON_OPENS.match(opening))),
)
# A method opens with its own figure as often as not - "About 50 minutes start to finish. Cook a
# sliced aubergine...", "Lower eggs into boiling water: 6 minutes for a runny yolk" - so a
# duration or a figure says nothing about whether a steps reply is a method. The other way round
# it does: a how-long answered with a method and no figure at all has not given the time.
_FIGURES = frozenset((TIME, AMOUNT))

# The meaning family: what `_a_meaning` reads, and the meaning told with a verb nobody listed. A
# mechanism comes out as "has", "uses", "pumps" or as a plain statement - "A sump pump sits in a
# pit", "Compound interest pays interest on the interest", "Seasons come from the Earth's 23.5
# degree tilt" - and a verb list only ever holds the verbs somebody thought of.
def _a_meaning_or_a_statement(opening):
    """`_a_meaning`, and a meaning said in a verb no list has: see `_a_statement_answers_it`."""
    # A sentence about the answering is not a meaning whichever arm would have credited it: "That
    # is a big question and there is a lot to say" is read as a mechanism by `_a_meaning` because
    # of "there is", so the fence stands in front of both arms rather than inside the statement one.
    if SAYS_NOTHING_ABOUT_IT.match(opening or ""):
        return False
    if _a_meaning(opening):
        return True
    return _a_statement_answers_it(opening)


# A meaning is a statement, whatever verb it is told with. `_a_meaning` knows the mechanisms told
# with a verb somebody wrote down - has, uses, moves, spins, pumps - and the deck's own answers say
# them in verbs nobody listed: "A sump pump *sits* in a pit", "Compound interest *pays* interest on
# the interest", "The Inca empire *ran* along the Andes", "Seasons *come* from the Earth's 23.5
# degree tilt", "A normal resting heart rate *is* 60 to 100". Every one of those was scored a miss,
# with the right answer in front of the person. What makes them a meaning is only that they are
# statements, so this reads the shape rather than the words: see `_a_statement_answers_it`.
def _a_statement_answers_it(opening):
    """True when a meaning ask is answered by a plain statement about something.

    The three other things a first sentence can be are taken out: a job for the person ("Start with
    the router your provider gave you", "Learn to change a tyre"), a question put back ("?"), and a
    shrug ("Nothing from me so far", "That's beyond what I know"). What is left is a sentence saying
    something, and a sentence too short to say anything ("Fine.", "Yes, about right") is left alone.

    A figure on its own is how much, not what a thing is: "how does it work" / "It takes about 50
    to 100ml per kilo a day" is a dose and it is the whole sentence. What joins a thing to a figure
    and makes a statement about the thing is the copula - "A normal resting heart rate for an adult
    is 60 to 100 beats a minute" - or the rest of a sentence around the figure: "The Inca empire ran
    along the Andes from about 1438 to 1533". So a short sentence whose only content is a figure
    needs the copula to count.
    """
    if not opening or opening.rstrip().endswith("?"):
        return False
    if (is_a_punt(opening) or NOTHING_TO_GO_ON.match(opening)
            or SAYS_NOTHING_ABOUT_IT.match(opening) or _an_opening_job(opening)):
        return False
    # Where a thing comes from is its own read, and that one is credited only when the line asked
    # where: "Bees make it: a worker drinks nectar out of flowers" answers "where does honey come
    # from" and is not a meaning of honey. Taking that shape back here without the line would open
    # the same hole from the other side.
    if _an_origin(opening):
        return False
    words = re.findall(r"[A-Za-z0-9'\u2019-]+", opening)
    if len(words) <= 10 and _a_figure(opening) and not COPULA.search(opening):
        return False
    return len(words) >= 5


# The shrug said with "nothing" as the thing the bot has none of, and said about its own side of the
# conversation: "Nothing from me so far.", "There's nothing on my side for 'that' to land on",
# "Nothing to cut down yet", "Nothing in hand to shorten". Each opens like a statement about the
# world, so a statement was read out of them. And the same shrug when the line's "that" has nothing
# to point at: "'That' could be a lot of things and I've none of them in front of me".
NOTHING_TO_GO_ON = re.compile(
    r"^(?:nothing (?:from me|on my side|more from me|in hand|"
    r"to (?:add|say|cut|shorten|go on))\b|"
    r"there (?:is|'?s|isn'?t|'?s not) nothing (?:from me|on my side|more|in hand|"
    r"to (?:add|say|cut|shorten))\b|"
    r"there'?s nothing (?:from me|on my side|more|in hand|to (?:add|say|cut|shorten))\b|"
    r"'?(?:that|it)'? could be (?:a lot|anything|many|loads|one of|several)\b)", re.I)


# A sentence can be about the answer rather than about anything the line named: "I have no idea,
# that one is beyond me", "Nobody really knows for certain", "It varies a lot from person to
# person", "It depends on the person, honestly", "Honestly I could not tell you", "That is not
# something I can help with", "You should ask an adviser about that". Each one is a whole statement
# with a verb in it, so the shape alone read a meaning out of it and a shrug was scored as an answer.
# What they share is that the only thing they are about is the answering - the knower, the question,
# the listener - and never a thing the line named. A remark about the day belongs here too: said
# after "explain the offside rule", "It was a long day at work" says nothing about the rule.
#
# This is the same shrug as "nothing from me", said about knowing instead of about having. Kept to
# the openings that carry no content of their own: "it varies the current to keep the heat steady"
# and "it depends on the setting" are statements about a thing, so only the forms that name the
# person, the question or the answer are read here.
SAYS_NOTHING_ABOUT_IT = re.compile(
    r"^(?:"
    r"(?:honestly,? |well,? )?(?:i|we) (?:have|'?ve) no idea\b|"
    r"(?:honestly,? |well,? )?(?:i|we) (?:do not|don'?t|dont|could not|couldn'?t|can'?t|cannot) "
    r"(?:know|say|tell you|help with (?:that|this|it))\b|"
    r"(?:nobody|no one|no-one|not many people) (?:really )?(?:knows|could say)\b|"
    r"(?:it|that|this) (?:depends|all depends) "
    r"(?:on (?:the person|the individual|who you ask|each person|the person concerned)|, honestly)\b|"
    r"(?:it|that|this) (?:varies|changes|differs) "
    r"(?:a lot |a great deal |a bit )?(?:from person to person|from one person to another|"
    r"between people|by person)\b|"
    r"(?:it|that|this) (?:is|'?s) (?:different|not the same|much the same) "
    r"(?:for everyone|for everybody|for each|for most people)\b|"
    r"(?:it|that|this) (?:is|'?s) (?:a|such a) big question\b|"
    r"(?:it|that|this) (?:is|'?s) not something (?:i|we) can help\b|"
    r"(?:it|that|this) (?:is|'?s|was) beyond (?:me|what i know|my knowledge)\b|"
    r"(?:(?:you|we) (?:should|could|might) |(?:i would |i'?d )?)?(?:ask|speak to|talk to|see|"
    r"check with) (?:an?|your|the) \w+(?: \w+)? about (?:that|this|it)\b|"
    r"(?:it|that) (?:was|has been|is) a (?:long|busy|hard|tough|rough|hectic) "
    r"(?:day|week|morning|night)\b|"
    r"there (?:is|'?s) a lot (?:to say|said)\b|"
    r"(?:it|that) (?:is|'?s) hard to say\b|"
    r"(?:this|that|it) (?:is|'?s) (?:one of those|the kind of) (?:questions|things)\b|"
    r"(?:a|the) (?:quick |short |little )?(?:search|google|look it up)\b"
    r"[^.]{0,30}?\b(?:should|will|would|can)\b|"
    r"(?:no|not a|there'?s no) (?:straight|simple|clear|easy) answer\b"
    r")", re.I)


# The word that joins a thing to its figure: "resting heart rate for an adult is 60 to 100 beats a
# minute", "the winner is whoever finishes with the most points". Without one, a figure on its own
# is a quantity, which answers how much rather than what the thing is.
COPULA = re.compile(r"\b(?:is|are|was|were|means|equals|measures|amounts to)\b", re.I)


# A job is told with the verb and then where it lands as often as with the thing it acts on: "Start
# with the router your provider gave you", "Learn to change a tyre", "Ask about the excess", "Go for
# the two-pack". Widening the instruction test itself would make the same word the yes to every
# yes/no line - an instruction is the doing, and the doing is the yes - so the opening form is asked
# here, where only the meaning read uses it.
A_JOB_LANDS = re.compile(r"^([A-Za-z']+)\s+(?:with|by|at|for|from|into|to|about|through|round|"
                         r"around|over|under|back|\d+|three|four|five|six|seven|eight|nine|ten|"
                         r"a few|several)\b", re.I)


# A list of jobs opens on its place in the list as often as not: "First check your credit file with
# all three agencies, then dispute anything wrong" is the same instruction as "Check your credit
# file", and the ordinal is not what the sentence is about.
AN_ORDINAL_OPENING = re.compile(r"^(?:(?:first|firstly|then|next|after that|finally|lastly|"
                                r"to start|to begin|start by|begin by|step one|step 1)"
                                r"\b[,:]?\s*)", re.I)


def _an_opening_job(opening):
    """True when the sentence opens on a job for the person to do."""
    if _an_instruction(opening):
        return True
    rest = AN_ORDINAL_OPENING.sub("", opening or "")
    if rest != (opening or "") and _an_instruction(rest):
        return True
    match = A_JOB_LANDS.match(rest)
    if not match:
        return False
    word = match.group(1).lower().strip("'")
    return word not in NOT_A_VERB and not word.endswith("ing")


_CHECKS = {
    TIME: _a_time,
    COMPARE: _a_comparison,
    AMOUNT: _an_amount,
    PLACE: _a_place,
    PERSON: _a_person,
    MEANING: _a_meaning_or_a_statement,
    YESNO: _a_yesno,
    PICK: _a_pick,
    STEPS: _steps,
    OPTIONS: _options,
    REASON: _a_reason,
}


def fits(reply, want, line=None):
    """`gives` under the name the lane plan used, for callers that read it that way."""
    return gives(reply, want, line)

# ------------------------------------------------------------------ the readings that need the line
#
# The reply's own words settle most shapes. A few do not, and are read from the question as well
# when `gives` is passed the line: a yes/no answered by doing the job, and a pick that names one
# of two sides. The helpers here take the line as plain text - lower case, one space.

# Words that are in every line and name nothing, so a match on one is not the reply naming the
# thing the person asked about.
_EMPTY = frozenset((
    "about", "after", "again", "before", "being", "could", "doing", "first", "going", "have",
    "just", "like", "make", "much", "need", "only", "really", "should", "still", "than", "that",
    "their", "them", "then", "there", "these", "they", "thing", "this", "those", "want", "what",
    "when", "where", "which", "while", "will", "with", "would", "your", "yours", "from", "into",
))
# A line that asks leave, or asks what it needs to do, is answered by the doing.
PERMISSION = re.compile(
    r"\b(?:can|could|should|shall|may|do|does|did|is it|are they|am i) (?:i|we|you|it|they|my|"
    r"i have to|i need to|we need to)\b|\bdo i need\b|\bis it ok\b|\bis it safe\b|"
    r"\bam i allowed\b|\bi (?:should|must|need to|have to)\b", re.I)
# The same verbs as INSTRUCTS, anywhere in the opening: a reply can put two words in front of the
# verb, or say the job as a purpose first ("To double a recipe double every weight").
JOB_ANY = re.compile(INSTRUCTS.pattern.replace("^(?:", "(?:", 1).replace(
    r")\b", r"|double|halve|split|scale|reheat|refreeze)\b"), re.I)
# The two sides of "a fiesta or a focus": the words either side of the "or", which is the whole of
# what the line offers to choose between.
# A side can be a number: "is 15 or 20 a factor of 30" offers two of them, and a token with a
# digit is a name however short - the same rule the two sides of a comparison are read by.
SIDES = re.compile(r"([a-z0-9']+(?: [a-z0-9']+)?) or ([a-z0-9']+(?: [a-z0-9']+)?)", re.I)
# The same pair said as a comparison rather than a choice: "is porridge better than cereal",
# "would a rescue be better than a puppy". A side is up to three words either side of it.
COMPARATIVE_THAN = re.compile(
    r"([^?.!,;:]{1,40}?)\s+(?:much |a bit |a lot |far |way |any |still )?"
    # The comparative is followed by "than" itself ("cheaper than the oven") or by what it is
    # spent on first ("cheaper to run than a heat pump one", "better value than breasts"), which
    # is how most people say it: two words at most, so a line that merely has an "-er" word and a
    # "than" somewhere later is not read as a pair.
    r"(?:\b(?!rather\b|other\b|fewer\b)\w+er\b|more \w+|less \w+|worse)"
    r"((?:\s+(?!than\b)(?!(?:\w+er|more|less|worse)\b)\w+){0,2})\s+than\b\s*"
    r"([^?.!,;:]{1,40})", re.I)
# "dried beans vs tinned": the same pair with the comparison word between them.
SIDES_VS = re.compile(r"([a-z']+(?: [a-z']+)?)\s+vs\.?\s+([a-z']+(?: [a-z']+)?)", re.I)
# The words that leave a side when the run in front of "better than" is trimmed back: "is a fixed
# rate better than variable" leaves "a fixed rate", and the side is "fixed rate".
SIDE_FILLER = frozenset((
    "a", "an", "the", "is", "are", "was", "were", "would", "will", "do", "does", "did", "which",
    "what", "and", "or", "but", "so", "then", "that", "this", "these", "those", "it", "its",
    "your", "my", "our", "their", "his", "her", "me", "us", "them", "be", "being", "been", "get",
    "gets", "got", "buy", "buying", "have", "has", "had", "should", "shall", "could", "can"))
# What the reply says when it has picked one of the two: the side is better, it wins, take it, or
# it is the one for the person. A reply that says neither of these has not answered the question.
A_SIDE_WINS = re.compile(
    r"\b(?:is|are|was|were) (?:still |usually |often |much |far |a bit )?(?:the )?(?:better|best|"
    r"kinder|healthier|cheaper|safer|stronger|quicker|smarter|more useful)\b"
    r"|\bthe (?:better|best|kinder|healthier|cheaper|safer|stronger|quicker|smarter|easier) "
    r"(?:choice|buy|option|bet|value|start|one|bowl|loaf|plan|pick|of the two)\b"
    r"|\b(?:wins?|won)\b"
    r"|\b(?:take|get|go for|pick|choose|buy|stick with) (?:the|a|an) \w+"
    r"|\bnothing (?:[a-z]+ ){0,4}comes close\b|\bcomes? close\b"
    r"|\bif you (?:want|need|have|are)\b"
    # "Gas is much the cheapest for heat", "A cat, on that one", "the full race is exactly twice as
    # far": the choice said with an intensifier, answered elliptically, or left as the ratio.
    r"|\b(?:much|far|by far|a lot|still|easily) the (?:better|best|cheapest|healthiest|easiest)\b"
    r"|\bon (?:that|this) one\b|\btwice (?:as|the)\b|\bhalf the (?:price|cost|time|weight|size)\b"
    # "A half marathon is 13.1 miles, which is further than a 10k at 6.2 miles": the reply says the
    # comparison itself, between the two sides the line named.
    r"|\b(?:is|are|was|were) (?:much |far )?(?:further|longer|bigger|heavier|lighter|warmer|"
    r"colder|stronger|quicker|faster|cheaper|worse|better) than\b"
    r"|\bthe one (?:to|that|for|I would|id)\b"
    r"|^both\b|\bboth, and\b", re.I)


LINE_TEXT_FIELDS = ("plain", "clean", "text", "norm_text", "norm")


def _line_text(line):
    """The line as plain text: lower case, one space, curly apostrophes straightened.

    Takes the words or the `understood` dict, so a caller may pass either. A dict read with
    `str()` is every field name and its value, and the words of that read - "short", "lines",
    "false" - are what a `_names_what_the_line_named` gate would match: the line's own words are
    all a reply should be measured against.

    The field is the line as the person typed it, in the plain reading: the field `plain` keeps
    the figures and drops the punctuation, and `norm_text` does the opposite, turning "i got a 5
    in my maths mock" into "a five ... | ...", so a reply that says "A 5 is a strong pass" shares
    no word with its own line and the "names what the line named" gate reads the answer as a
    miss. The words a reply is measured against are the words on the screen.
    """
    if isinstance(line, dict):
        for field in LINE_TEXT_FIELDS:
            value = line.get(field)
            if isinstance(value, str) and value.strip():
                line = value
                break
        else:
            line = ""
    return " ".join(str(line or "").lower().replace("\u2019", "'").split())


def _words(text):
    return re.findall(r"[a-z']+", str(text or "").lower().replace("\u2019", "'"))


# The subject of a definition ask: "what is a student loan", "what does a food bank do", "whats a
# standing charge". What follows is cut at the first word that starts a new clause, because the
# thing asked about is the head of the line ("what is a student loan and do i pay it back" asks
# about the student loan).
THE_THING_ASKED = re.compile(
    r"^(?:what'?s|what is|what are|what was|what were|what does|what do|what did|"
    r"how does|how do|tell me about|what about)\s+(?:(?:an|a|the)\b\s*)?(.+)$", re.I)
# Words that end the subject: a new clause, a preposition, or the verb the ask put on it.
_ENDS_THE_THING = frozenset("""
    and or but for in on at to with of from about when while if that which who whom whose how
    why where do does did is are was were be been being mean means meant cost costs worth
    make makes made need needs want wants go goes get gets come comes work works help helps
    take takes give gives happen happens feel feels look looks sound sounds include includes
    cover covers contain contains show shows sit sits stand stands say says called call
    used using made based known named supposed said done grown kept sold eaten worn driven written
    built filled meant
""".split())
_ARTICLE = re.compile(r"^(?:a|an|the|your|my|his|her|their|our|its|this|that|these|those|"
                      r"any|some)\s+", re.I)


# A word that points at something the line has not said is not the thing a reply would name.
_NOT_A_THING = frozenset("""
    i you we they it that this there one someone anyone everyone nobody everything anything
    something nothing people
""".split())


def _the_thing_asked(said):
    """The thing a definition ask is about, as the words the reply would open on: "student loan"
    for "what is a student loan and do i pay it back"."""
    match = THE_THING_ASKED.match(said or "")
    if not match:
        return ""
    words = []
    for word in re.findall(r"[a-z0-9']+", match.group(1).lower().replace("\u2019", "'")):
        if word in _ENDS_THE_THING or word in _EMPTY:
            break
        words.append(word)
        if len(words) == 3:
            break
    # A pronoun is not a thing: "how does it work" and "how do i use a semicolon" name the thing
    # later in the line, or not at all, so nothing is read and the reply is left alone.
    if not words or words[0] in _NOT_A_THING:
        return ""
    # A subject of one short word ("what is a p60", "what is vat") is still a subject.
    if max(len(w) for w in words) < 2:
        return ""
    return " ".join(words)


# A judgement about the thing is a verdict, not what the thing is: "what is porridge" / "Porridge
# is good for you first thing" has not said what porridge is, and the reading below must not pass
# it for a definition just because it opens on the subject.
_JUDGES_THE_THING = re.compile(
    r"^(?:is|are|was|were|should|must|ought|needs?)?\s*(?:be\s+)?(?:not\s+)?(?:good|bad|great|"
    r"fine|okay|ok|"
    r"safe|worth|better|worse|best|worst|useless|rubbish|lovely|nice|amazing|brilliant|terrible|"
    r"awful|really|usually|often|always|never|definitely|probably|a (?:good|bad|great|waste|rip|"
    r"must)|the (?:best|worst|only)|your|a waste|the wrong)\b", re.I)
# Advice about the thing is not what the thing is: "A student loan must be paid back before
# anything else" has said what to do with it, not what it is. A "has to" is the same obligation
# said with `has`, which `_SAYS_WHAT_IT_IS` reads as a thing's parts: "An odometer has to be
# working for the MOT" states a rule and is not what an odometer is.
_ADVISES_THE_THING = re.compile(
    r"^(?:should|must|ought|needs? to|need to|has to|have to|had to)\b", re.I)
# A subject of one short word is a word that starts other things: "what is a gas" / "A gas boiler
# needs servicing once a year" is about a boiler, not about gas. The one-word subject is read
# only when the reply goes straight on to the copula or to a verb that says what the thing does.
_SAYS_WHAT_IT_IS = re.compile(
    r"^(?:is|are|was|were|has|have|had|can|cannot|do|does|did|give|gives|provide|provides|let|"
    r"lets|allow|allows|help|helps|mean|means|refers|comes|runs|works|starts|ends|takes|costs|"
    r"keeps|contains|restarts|pays|holds|covers|makes|sits|stands|forms|happens|moves|lubricates|"
    r"carries|spreads|turns|shows|includes|protects|needs)\b", re.I)


# A one-word subject is defined by what it does whatever the verb is, and the verb is the word
# after the subject with its own object behind it: "A decibel measures how loud a sound is", "A
# thermostat controls when the heating comes on", "A router sends the signal to your devices". The
# object is a wh-word or a determiner, which is what tells a verb from the noun that starts another
# subject: "A gas boiler needs servicing" has "boiler" after "gas", and no verb is a plural noun.
_A_DOING = re.compile(
    r"^\w+s\s+(?:how|what|which|when|where|whether|who|you|it|them|him|her|us|me|the|a|an|"
    r"your|their|its|some|any|each|every|all|only|just)\b", re.I)


# "what is a semicolon for" is answered by what the thing is for: "Use a semicolon to join two
# full sentences that are closely related". The verb comes first and the thing is its object, so
# the subject test below never sees it. The purpose is what makes it the answer - the thing named
# and then "to" or "for" the job it does - so a reply that only mentions the thing is not read.
_PUTS_THE_THING_TO_USE = re.compile(
    r"^(?:use|put|add|place|stick|tie|clip|screw|wear|keep|hold|ride|apply|spread|slide|hang)\b",
    re.I)


def _uses_the_thing(opening, thing):
    """True when the reply opens on the verb for using the thing asked about and gives its job."""
    if not thing or not _PUTS_THE_THING_TO_USE.match(opening):
        return False
    low = opening.lower()
    at = low.find(thing)
    if at < 0:
        return False
    return bool(re.search(r"\b(?:to|for|so)\b", low[at:]))


def _defines_the_thing(opening, said):
    """True when the reply opens on the thing the line asked about and then says what it is or
    does: "what is a student loan" / "A student loan pays the tuition fee and the maintenance
    money while you study". The verb is the reply's own - `MEANS_BY_DOING` knows `give` and
    `provide`, and this reads the rest - so what matters is that the subject comes first and
    something is said about it, not the words it is said with."""
    thing = _the_thing_asked(said)
    if not thing:
        return False
    if _uses_the_thing(opening, thing):
        return True
    head = _ARTICLE.sub("", opening.strip()).lower()
    if not head.startswith(thing + " ") and not head.startswith(thing + "'"):
        return False
    # The space after the subject is stripped before the guard reads it, or " is good value"
    # never matches a pattern that starts on the word itself.
    rest = head[len(thing):].strip()
    if _JUDGES_THE_THING.match(rest) or _ADVISES_THE_THING.match(rest):
        return False
    # A one-word subject is read only when the reply goes straight on to the copula or to a verb
    # that says what the thing does ("A gas has no fixed shape", "A p60 is the summary"); "A gas
    # boiler needs servicing" is about a boiler, however much it starts with the word.
    if " " not in thing and not (_SAYS_WHAT_IT_IS.match(rest) or _A_DOING.match(rest)):
        return False
    return len(rest.split()) >= 3


def _name_words(text):
    """The words of a line or a reply as names, digits and all: `_words` drops "15", "4g" and "b12"
    with every other figure, and a figure can be one of the two things a line offers."""
    return re.findall(r"[a-z0-9']+", str(text or "").lower().replace("\u2019", "'"))


def _long_enough_a_name(word, least=3):
    """A token with a digit is a name however short: "4g", "5g", "15", "dmp" and "b12" all name
    something, where a short word of letters alone is more likely "it", "or" or "my"."""
    return len(word) >= least or any(ch.isdigit() for ch in word)


def _names(opening, said):
    """True when the reply's opening names a thing the line named, by stem: bread / breads,
    freeze / freezing. A word from the line that is not in `_EMPTY` and is long enough to mean
    something."""
    reply = set(_words(opening))
    for word in set(_words(said)):
        if not _long_enough_a_name(word, 4) or word in _EMPTY:
            continue
        if word in reply or word[:-1] in reply or word[:-2] in reply:
            return True
    return False


def _names_the_subject(opening, said):
    """True when the reply's cause-is-the-thing sentence is about something the line named.

    The same job as `_names` beside it, read a little wider, because a why-answer names its
    subject in the reply's own form of the word: "why is my cabbage bitter" is answered "The
    *bitterness* is the sulphur compounds in the leaves", and "why should i neuter my cat" by "a
    spayed *cat* is out of the annual litters". `_names` wants a word of four letters or more and
    matches it by stem, which drops "bitter" against "bitterness" and every three-letter subject
    - cat, dog, car, gas, job - and the two most ordinary why-answers on the deck read as
    sentences about nothing.

    A three-letter word has to be the whole word in the reply, not the start of one, so "car"
    is not read into "care" and "gas" not into "gasket".
    """
    reply = set(_words(opening))
    for word in set(_words(said)):
        if not _long_enough_a_name(word, 3) or word in _EMPTY:
            continue
        if len(word) == 3:
            if word in reply:
                return True
            continue
        if word in reply or word[:-1] in reply or word[:-2] in reply:
            return True
        # The reply's own form of the word: bitter / bitterness, mould / mouldy, ice / iced.
        for said_word in reply:
            if said_word.startswith(word):
                return True
    return False


def _opens_on_the_lines_verb(opening, said):
    """True for a short opening that is the verb a decision in the line named, and nothing else:
    "should i bin it" / "Bin it." or "does that mean i should bin it" / "Bin it, I'm afraid."."""
    words = opening.split()
    if not words or len(words) > 5:
        return False
    first = _words(opening)
    if not first or len(first[0]) < 3:
        return False
    stem = first[0]
    for match in re.finditer(r"\b(?:should|must|need to|have to)\b\s+(?:i\s+)?([a-z]{3,})",
                             said, re.I):
        verb = match.group(1).lower()
        if verb == stem or (verb.startswith(stem[:-1]) and len(stem) > 3):
            return True
    return False


def _trimmed(words):
    """The words of a side without the filler at either end."""
    start, end = 0, len(words)
    while start < end and words[start] in SIDE_FILLER:
        start += 1
    while end > start and words[end - 1] in SIDE_FILLER:
        end -= 1
    return words[start:end]


def _the_pair_up(text):
    """The two things a line puts up to weigh against each other, or None.

    Three ways people ask it: "is wholemeal better than white" and "does a deep bath use more
    water than a shower" (a comparative and "than"), "dried beans or tinned, which is the better
    value" and "which is better, the train or the coach" (an "or"), "dried beans vs tinned".
    """
    clean = " ".join(str(text or "").split())
    found = COMPARATIVE_THAN.search(clean)
    if found:
        # The words a side may not be: an article, a "have", a "is". They are taken off both ends,
        # because the comparative can stand a couple of words away from "than" ("cheaper to run
        # than") and the words either side of that gap are not part of the thing named - "my
        # payslip has less on it than last month" puts no pair up at all.
        left = _trimmed(_words(found.group(1)))
        right = _trimmed(_words(found.group(3)))
        # What the comparative is spent on ("to run", "value") sits between it and "than", and it
        # is not part of the thing named: "does a deep bath use more water than a shower" puts the
        # bath and the shower up, not the bath and "use".
        spent = set(_words(found.group(2)))
        while left and left[-1] in spent:
            left = left[:-1]
        if not left or not right:
            return None
        return (left[-2:], right[:2])
    found = SIDES.search(clean) or SIDES_VS.search(clean)
    if found:
        return (_words(found.group(1)), _words(found.group(2)))
    return None


def _a_side_said_in_the_reply(side, ordered, words):
    """True when the reply says one of the side's own words, in any of the forms people say it in.

    A different question from the one below, which asks about one word of a side: this asks about
    a whole side, and it answers it through that one-word matcher rather than a reading of its own,
    so "Showering" is the shower here as it is in the comparison arms, "cats" is the cat in "a cat"
    and "hay fever" is the hayfever the line named. The floor is three letters, because a
    three-letter name is a name - "is a cat better than a dog" has to be read on "cat" - and every
    word in `_EMPTY` is still skipped.
    """
    for word in side:
        if not _long_enough_a_name(word) or word in _EMPTY:
            continue
        if _a_side_word_is_named(word, ordered, words):
            return True
    return False


def _the_side_wins(opening, line):
    """True when the line weighed two things up and the reply opened on one of them.

    "is a bath better than a shower" / "Showering wins on time and water" is a yes with a reason,
    and so is "is a plank better than a sit up" / "Both, and they do different jobs". The reply
    has to name one of the two sides and say one of the things a choice says, so a reply that
    describes the pair without choosing stays the "words cannot tell" it was.
    """
    pair = _the_pair_up(_line_text(line))
    if not pair:
        return False
    sides = [side for side in pair if side]
    if not sides:
        return False
    ordered = _words(opening)
    words = set(ordered)
    named = any(_a_side_said_in_the_reply(side, ordered, words) for side in sides)
    # "Both, and they do different jobs: ..." weighs the pair itself, and that is a verdict too.
    if not (named or re.match(r"^both\b", opening, re.I)):
        return False
    return bool(A_SIDE_WINS.search(opening))


def _names_a_side(opening, said):
    """A pick of one of two named sides, without the words a pick normally uses: the line says
    "a fiesta or a focus" and the reply opens on the fiesta. Only the words either side of the
    "or" are the sides, so the rest of the line is not mistaken for one."""
    sides = SIDES.search(said or "")
    if not sides:
        return False
    # The side has to be what the reply opens on: "A dog needs two walks a day" picks the dog; a
    # paragraph that mentions the boiler later has not picked anything.
    reply = _name_words(opening)[:3]
    side_words = [word for side in sides.groups() if side for word in _name_words(side)]
    return _a_side_said_in_the_reply(side_words, reply, set(reply))


# The words that are in every line and name nothing: a side is never counted on one of these, so a
# side such as "will" in "the difference between a will and probate" is counted on its own name.
_SIDE_EMPTY = frozenset((
    "the", "and", "but", "not", "for", "with", "your", "you", "our", "its", "it's", "this", "that",
    "these", "those", "what", "which", "from", "into", "than", "then", "are", "was", "were", "has",
    "have", "had", "one", "two", "any", "all", "much", "more", "less", "same",
))


def _a_side_word_is_named(word, ordered, words):
    """True when this one word of a side is said in the reply.

    The same thing is said in the line and in the reply in different shapes, so the match allows
    for the plural (seat/seats), for a verb the reply gives as its stem ("simmering" in the line,
    "a simmer" in the reply, and the other way about), and for a compound the reply spaces out
    ("hayfever" in the line, "hay fever" in the reply). A short name the reply never says, such as
    "dmp", is matched by its initials instead.
    """
    for reply_word in words:
        if reply_word == word:
            return True
        shorter, longer = sorted((reply_word, word), key=len)
        if len(longer) > 4 and longer.startswith(shorter) and shorter[-1:] not in ("s",):
            return True
        if len(shorter) >= 3 and shorter.rstrip("s") == longer.rstrip("s"):
            # The plural either way round: "cats" in the line is "a cat" in the reply.
            return True
    for index in range(len(ordered) - 1):
        if ordered[index] + ordered[index + 1] == word:
            return True
    return _initials_named(word, ordered)


def _initials_named(word, reply_words):
    """A short name spelled out by the reply: "dmp" as "debt management plan", "iva" as "individual
    voluntary arrangement". An acronym is a name the reply may only ever say in full."""
    if not 2 <= len(word) <= 4 or not word.isalpha():
        return False
    for start in range(len(reply_words)):
        pos = 0
        for spoken in reply_words[start:start + len(word)]:
            if pos < len(word) and spoken[:1] == word[pos]:
                pos += 1
        if pos == len(word):
            return True
    return False


def _names_both_sides(reply, said):
    """True when both of the two things the line put together are in the reply, False when one of
    them is missing, None when the missing one is too short to look for.

    The pair is read the way the line words it - "the difference between X and Y", "X vs Y",
    "compare X and Y", "X apart from Y", "X cheaper than Y" - and a side counts when any of its own
    words of three letters or more is in the reply, allowing for the plural (ssd/ssds,
    seater/seats) or for a short name the reply spells out (dmp/debt management plan). The whole
    reply is read rather than the opening, because a comparison is two-part by nature: "An SSD has
    no moving parts ... a hard drive is a spinning disc" is both sides, one in each clause.

    A reply that names one of the two and never the other has answered half the question, but a
    three-letter name is not evidence of anything: "hdd" may be "a hard drive" in the reply, so
    nothing is claimed against the reply on a short name alone.
    """
    said = (said or "").lower().replace("\u2019", "'")
    sides = None
    for pattern in SIDE_PAIRS:
        sides = pattern.search(said)
        if sides:
            break
    # The pair as word lists. A comparative the patterns above do not word ("are cats easier than
    # dogs", "does a deep bath use more water than a shower") is read by the same pair reader that
    # calls the line a comparison in the first place, so every form the reading knows as two
    # things up can be answered here as well - one reader for the reading and for the check.
    pairs = [sides.groups()[:2]] if sides else []
    if not pairs:
        pair = _the_pair_up(said)
        if pair and all(pair):
            pairs = [[" ".join(side) for side in pair]]
    if not pairs:
        # No pair the line words as two things: the reply is not held against anything here.
        return None
    ordered = _words(reply)
    words = set(ordered)
    named, missing = 0, []
    for side in pairs[0]:
        side_words = {word for word in _words(side)
                      if len(word) >= 3 and word not in _SIDE_EMPTY}
        if not side_words:
            continue
        if any(_a_side_word_is_named(word, ordered, words) for word in side_words):
            named += 1
        else:
            missing.append(min(side_words, key=len))
    if named + len(missing) < 2:
        return None
    if named >= 2:
        return True
    if any(len(word) <= 3 for word in missing):
        return None
    return False


def _the_job_named(opening, said):
    """The job the line asked leave for, in a reply whose first word is not one of the verbs the
    cue list knows. Every part is needed: the line asks leave, the reply opens on a job, and the
    reply names the thing the line named. The verb alone answers a question about something else,
    and the name alone is a paragraph that happens to mention it."""
    if not PERMISSION.search(said or ""):
        return False
    if not _names(opening, said):
        # "does that mean i should bin it" / "Bin it, I'm afraid." - the verb is three letters,
        # so the name rule cannot see it, but the line named the verb and the reply opens on it.
        return _opens_on_the_lines_verb(opening, said)
    if _steps(opening):
        return True
    if JOB_ANY.search(" ".join(opening.split()[:12])):
        return True
    # The reply's own first word is the line's verb: "do i need to strap my toddler in" /
    # "Strap them in every time". Short only, because a long paragraph that opens on a word of
    # the line is not an answer by doing.
    if len(opening.split()) > 9:
        return False
    first = _words(opening)
    if not first or len(first[0]) < 4:
        return False
    stem = first[0]
    for word in _words(said):
        if len(word) >= 4 and (word == stem or word.startswith(stem) or stem.startswith(word)):
            return True
    return False

# A method told as a path through a menu: "Windows: Settings > Apps > Installed apps, find it in the
# list and choose Uninstall". The line opens on the path, so no verb list can see it, and it was a
# clear miss on "how do i set my phone to dark mode". One reading: an arrow and, in the same
# sentence, one of the verbs that says what to do when you get there.
PATH_THEN_VERB = re.compile(
    r"(?:>|\u2192|->)\s*\S.{0,120}\b(?:find|choose|select|click|tap|press|open|set|switch|turn|"
    r"tick|untick|check|uncheck|change|remove|delete|add|enable|disable|toggle)\b", re.I)


# The garden and the toolbox: "Sow peas from March to early June, 5cm deep in a wide flat trench"
# and "Prune the roses in late winter, just as the buds start to swell" are methods with no article
# after the verb, so `INSTRUCTS` does not know them. They are read by the method checks alone and
# not added to `INSTRUCTS` itself, because `JOB` - which is `INSTRUCTS` plus the everyday verbs -
# answers a yes/no that opens on any job, and an answer about sowing is not a yes to "is a pension
# better than a savings account": on 2,240 mismatched pairs the wider list invented three.
GARDEN = re.compile(
    r"(?:sow|plant|prune|dig|mow|scarify|weed|mulch|repot|stake|harvest|deadhead|sprinkle|hammer|"
    r"grout|caulk|unblock|unplug)\b", re.I)


# The two openings above are read at the end of the file, and the method check is extended rather
# than edited, so that this change adds lines to `fit.py` instead of rewriting it: the world's
# copy of main moves under every open PR, and an edit lands as a conflict where an addition does
# not. Python resolves both names at call time, so nothing here depends on the order.

# A step can be told as what *not* to do, and not only in the first word of the reply. "A workplace
# pension is free money: you put in 5% and your employer at least 3%, with tax relief on top. Don't
# opt out to add a few pounds to your pay packet now" answers "what should i do about my pension"
# and was read as a reply about something else, because `DOES_NOT` was only ever matched against
# the opening: the negative step is usually the second half of an answer.
# What a friend says before the answer is not a step of it - "don't worry", "don't panic", "don't be
# too hard on yourself" - so a negative that lands on a state of mind is left out.
DOES_NOT_ANYWHERE = re.compile(
    r"(?:^|[.:;!?]\s+|,\s+(?:then|so|and|but|just|or)\s+|:\s+)"
    r"(?:don'?t|do not|never|avoid|skip|no need to)\s+"
    r"(?P<after>[^.;:!?]{0,40})", re.I)
NOT_A_STEP_BUT_REASSURANCE = re.compile(
    r"^(?:worry|panic|fret|stress|beat yourself|mind|bother|overthink|"
    r"be (?:too )?(?:hard|afraid|scared|embarrassed|guilty|silly|worried|shy)|"
    r"feel (?:bad|guilty|silly|stupid)|feel like|let (?:it|that|them)\b)",
    re.I)


def _a_step_told_as_what_not_to_do(text):
    """True when a clause of the reply tells a step in the negative form.

    Read over the whole reply, like the other step shapes: "Mushrooms keep about a week in the
    fridge in a paper bag, never a plastic one ... Don't wash them until you cook them".
    """
    for m in DOES_NOT_ANYWHERE.finditer(text or ""):
        after = m.group("after").strip()
        if not after:
            continue
        if NOT_A_STEP_BUT_REASSURANCE.match(after):
            continue
        return True
    return False

_STEPS_IN = _steps_in


def _steps_in(reply):
    """`_steps_in`, and the two methods a verb list cannot see.

    "Sow peas from March to early June, 5cm deep in a wide flat trench" and "Prune the roses in
    late winter, just as the buds start to swell" have no article after the verb, so `INSTRUCTS`
    does not know them; "Windows: Settings > Apps > Installed apps, find it in the list and choose
    Uninstall" opens on a path. All three are methods, and each was a clear miss on a real turn.
    """
    if _STEPS_IN(reply):
        return True
    text = " ".join(str(reply or "").split())
    if _a_step_told_as_what_not_to_do(text):
        return True
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if GARDEN.match(sentence) or PATH_THEN_VERB.search(sentence):
            return True
    return _words_handed_over(text)


# The words to say, in quotes, are the method for a say-ask: "what do i say to my boss" is
# answered with the sentence itself, and `INSTRUCTS` cannot see it because the reply's verb is
# nobody's - the words are the person's, quoted back for them to use. A reply that opens on a
# quotation is handing them over: "Thinking of you both - hope the year is a good one." That is
# the whole of it. The quote is read only at the opening, and only when there is a sentence inside
# it, so a reply that quotes a word to explain it ("'Sole' means the fish") is not this.
SAID_WORDS = re.compile(
    r"^(?:just |only |maybe |perhaps |something like:? |try:? |say:? |start with:? |"
    r"open with:? |how about:? )?"
    r"\s*[\"'\u201c\u2018\u00ab][^\"'\u201d\u2019\u00bb]{8,}[.!?,]?[\"'\u201d\u2019\u00bb]",
    re.I)


def _words_handed_over(text):
    """True when the reply opens by handing the person the words to say, in quotes."""
    return bool(SAID_WORDS.match(text or ""))

# A rate: money and a time unit with "a", "an", "per" or "each" between them. "7p an hour",
# "£12 an hour", "$20 per hour", "30p a day" all answer how much, not how long - a budget for a
# car that says "£2,000-£3,000 a year" was read as an answer to "how long does it keep".
_MONEY = (r"(?:[£$€]\s*\d[\d,.]*"
          r"|\b\d[\d,.]*\s*(?:p|pence|pennies|quid|pounds?|bucks?|dollars?|euros?|cents?|gbp)\b)")
MONEY_RATE = re.compile(
    _MONEY + r"(?:\s*(?:to|-)\s*(?:[£$€]\s*)?\d[\d,.]*\s*(?:p|pence)?)?"
    r"\s*(?:a|an|per|each)\s+"
    r"(?:sec\w*|min\w*|hour|hr|hrs|day|week|month|year|night|visit|call|session|unit)s?\b", re.I)


def _a_money_rate(opening):
    """True when the reply says a price for a stretch of time, not a length of time."""
    return bool(MONEY_RATE.search(opening))


def _without_a_money_rate(opening):
    """The reply with its price-per-time phrases taken out, so the time check can be asked again."""
    return MONEY_RATE.sub(" ", opening)


# A yes/no that asks about a quantity rather than a thing: "is that enough", "will that be enough",
# "is that too far", "is that too long", "is 18 hours too much for a cat". The thing it asks about
# is a figure from earlier in the chat and the line does not name it, so a reply cannot be matched
# to the line by naming a thing - and on the deck that left ten answered turns called misses: "15
# minutes is short of the 20 minutes that answer named", "30 minutes is inside the 30 to 60 minutes
# that answer named, so you are fine", "3 times a week is at the three sessions a week that answer
# named, so you are there already".
#
# What answers one is the person's own figure set against the standard, and the shape is the figure
# at the head of the sentence with the relation after it. That head is what tells a verdict from a
# reply that only holds a figure near a word like "under": "up to about 3 or 4 pouches of 85g for a
# 4kg cat" and "under two, video calls and the odd photo only" both answer a how-much and say
# nothing about the person's figure, and neither opens on one.
A_QUANTITY_ASK = re.compile(
    r"\b(?:enough|too (?:much|many|far|often|long|hot|cold|big|small|old|young|late|soon|heavy|"
    r"short|thick|thin|deep|tall|high|low|expensive|dear))\b", re.I)
_A_QUANTITY_NUMBER = (r"(?:\d[\d.,]*|one|two|three|four|five|six|seven|eight|nine|ten|eleven|"
                      r"twelve|fifteen|twenty|thirty|forty|fifty|sixty|ninety|hundred|half|"
                      r"a couple|a few|an|a)")
_A_QUANTITY_UNIT = (r"(?:sec|second|minute|min|hour|hr|day|week|month|year|night|kg|kilo|pound|"
                    r"mile|km|litre|pint|cup|gram|ounce|stone|cm|inch|foot|feet|metre|session|"
                    r"time|portion|serving|slice|step|dose|tablet|degree|celsius|unit|item|"
                    r"episode|page|p)s?\b")
_A_QUANTITY_RELATION = (r"(?:under|over|above|below|inside|within|short of|past|at|less than|"
                        r"more than|on the line|clear of|off the|away from)")
_A_FIGURE_AGAINST_THE_STANDARD = re.compile(
    # A short lead-in is allowed, because the reply may be answering a follow-up: "Same as before:
    # Two hours is over the ninety minutes the recipe gives."
    r"\A\s*(?:[^:]{1,45}:\s*)?(?:about|around|just|only|nearly|almost|well|roughly)?\s*"
    r"(?:£\s*\d[\d.,]*|\$\s*\d[\d.,]*|€\s*\d[\d.,]*|"
    + _A_QUANTITY_NUMBER + r"[\s-]*(?:" + _A_QUANTITY_NUMBER + r"[\s-]*)?-?\s*"
    + _A_QUANTITY_UNIT + r")"
    # "2 sessions a week", "3 times a day": the rate the figure is paid at is part of the figure.
    r"(?:\s+(?:a|an|per|each)\s+(?:week|day|month|year|night|hour|session))?"
    r"\s+(?:is|are|comes|sits|lands)\s+(?:the\s+|well\s+|just\s+|a bit\s+|a little\s+)?"
    + _A_QUANTITY_RELATION + r"\b", re.I)


def _the_figure_against_the_standard(opening, said):
    """The verdict a yes/no about a quantity wants, when the reply sets the figure against it."""
    if not A_QUANTITY_ASK.search(said or ""):
        return False
    return bool(_A_FIGURE_AGAINST_THE_STANDARD.match(opening or ""))

# The judgement that opens the sentence after the figure: "That is a short trip - easy to do every
# day", "Doable in a day if you leave early", "Fine for a week in the fridge". The copula arm needs
# an adjective a person judges a plan by, so "That is the temperature the recipe gives" is not read
# as one, and a bare "That is" is what `VERDICT_OPEN` already handles.
VERDICT_AFTER_A_FIGURE = re.compile(
    # Only a word that judges the plan counts. "That is a short time" and "That is a long time"
    # describe the figure the bot has just worked out and say nothing about whether the thing is
    # all right, so they are not read: with the measure words in, any "25 minutes" opening followed
    # by a label of its own length was the verdict on any line at all.
    r"\A(?:that|it|this) (?:is|'s|would be|should be) (?:a |an |quite a |quite |a bit of a )?"
    r"(?:fair|fine|easy|doable|manageable|sensible|reasonable|safe|risky|all right|alright|okay|"
    r"ok|worthwhile|worth it|no bother)\b"
    r"|\A(?:doable|fine|fair|easy|sensible|reasonable|manageable|worth it|worth doing|workable|"
    r"sound|just the job|no bother|all right|alright)\b"
    # Or the judgement anywhere in that sentence, which is where a reply puts it after naming the
    # figure: "That is a short trip - easy to do every day". "Fine" alone only counts when it is
    # followed by the thing it is fine for, so a bare "fine." stays unread.
    r"|\b(?:doable|easy to|easy|manageable|sensible|reasonable|no bother|just the job|"
    r"all right|alright|worth it)\b"
    r"|\bfine (?:to|for|in|if|on|as)\b", re.I)


def _a_figure_then_the_verdict(opening, reply):
    """The verdict in the sentence after the figure it rests on: see `VERDICT_AFTER_A_FIGURE`.

    The reply answers "is that too far" by doing the sum and then judging it - "About 5 minutes in
    the car and 20 minutes on a bike, each way. That is a short trip - easy to do every day" - and
    the figure is the evidence rather than the answer. Only the sentence straight after the
    opening is read, and only when the opening gave a figure or a measure, so a reply that only
    measures stays the miss it was.
    """
    if not opening or not (_a_time(opening) or _an_amount_with_a_unit(opening)):
        return False
    two = _opening_two(reply)
    if not two.startswith(opening):
        return False
    second = two[len(opening):].strip()
    # Searched rather than matched at the start: the judgement may sit after a dash inside the
    # sentence that names the figure ("That is a short trip - easy to do every day"), and the
    # readings that must open the sentence anchor themselves with `\A`.
    return bool(second and (VERDICT_AFTER_A_FIGURE.search(second)
                            or VERDICT_BAND.search(second)))

# The verb and a thing it acts on, for the *opening* of a reply as well as the parts after its
# colon: "Clear the cache rather than the data: on Android it is Settings > Apps ..." is the
# method for "how do i clear my cache" and was read as a reply about something else, because the
# opening was only ever checked against `JOB` (a list of kitchen and repair verbs) and "clear" is
# not on it. The shape is what makes it an instruction, so the shape is read.
#
# A pronoun straight after the verb is a thing only when a particle follows it - "Turn it off",
# "Wipe them down" - because the same slot holds the subject of another verb in a condolence:
# "Sorry it went awful" opens like an instruction and is not one. That reply answers "how did it
# go", and crediting it as a method would hide the small talk behind it. The particle is the open
# set of prepositions and not only the phrasal verbs, because a step says where the thing goes:
# "Attach it to something you already do every day", "Spoon it into the cup and level it",
# "Put it under the sink" were three of the ten real steps a sweep found the arm still missing.
#
# Three shapes take the verb's slot without being one, and each of them was a reply credited as a
# method on the first build of this arm:
#   * a contraction - "That's a lot to be carrying on your own." (to "how do i cope with all
#     this"), "Here's my pick: tuna pasta in 15 minutes", "What's the thing you most want to get
#     right?" - is a subject and an *is*, and the `'s` is what tells it from a verb. A negative
#     imperative ("Don't leave it on") never carried the article this reads anyway.
#   * a well-wishing - "Have a nice day.", "Have a good one.", "Enjoy the rest of your day." - is
#     the sign-off, not the method: it has the article and nothing to do.
#   * a clause with no main clause - "Because the boiler is old.", "Since the shop was shut.",
#     "Although the price is fine.", "Unless the shop says otherwise." - is a fragment, and a step
#     that opens on one of those words carries the comma ("If it still drips, change the washer").
AN_INSTRUCTION = re.compile(
    r"^[A-Za-z']+\s+(?:a|an|the|your|their|its|some|one|two|each|every|both|all|my|these|those)"
    r"(?=\s+[A-Za-z0-9'\u2019\"\u00a3$])"
    r"|^[A-Za-z']+\s+(?:it|them|him|her|me|us)\s+(?:off|on|out|in|up|down|away|over|back|"
    r"through|aside|together|to|into|onto|under|with|for|at|inside|across|around|along|near|"
    r"behind|beside|against)\b", re.I)
CONTRACTION_OPENER = re.compile(r"^[A-Za-z]+['\u2019](?:s|re|ll|ve|d|m)\b", re.I)
A_WELL_WISHING = re.compile(
    r"^(?:and\s+|so\s+)?(?:enjoy|hope (?:you|it|that)|all the best|take care|good luck|"
    r"sleep well|get well|have (?:a|an) (?:nice|good|great|lovely|brilliant|fab|wonderful|happy|"
    r"safe|quiet|lazy|restful|easy|better|fun|relaxing|peaceful))\b", re.I)
A_SUBORDINATE_FRAGMENT = re.compile(
    r"^(?:because|since|although|though|unless|whereas|while|if|when|after|before|as|where)\b",
    re.I)
# A word that opens a reply in the slot a verb would take and is no verb: "Still the same
# problem", "Sorry it went awful", "Maybe the washer". Without this the shape alone read "Still
# the same problem" as a method. A step does open on some of these neighbours - "Just add the
# garlic", "Then wipe it down", "Only use a little" - so only the adverbs and acknowledgements
# that never begin one are here.
NOT_AN_OPENER = frozenset((
    "still", "sorry", "even", "maybe", "perhaps", "honestly", "actually", "obviously",
    "apparently", "probably", "really", "quite", "please", "thanks", "ok", "okay", "well",
    "oh", "ah", "yes", "yeah", "no", "nope", "sure", "fine", "anyway",
    # A feeling, not a job: "Love it to bits." has the verb and the thing the shape asks for.
    "love",
    # Praise is not a job either, and `one` is the thing the shape asks for: "right ill let you
    # know how it goes" was read as a steps ask because "Nice one. Let me know how it goes." has
    # a word in the verb's slot and a determiner in the thing's. Every word below opens a reply
    # and never opens an instruction.
    "nice", "good", "great", "lovely", "brilliant", "perfect", "glad", "congratulations",
    "congrats", "cheers", "smashing", "fab", "wonderful", "grand", "ace", "decent", "super",
    "agreed", "yay", "hurrah", "hooray",
    # A function word opens a sentence in the verb's slot and is no verb. Each of these read a
    # statement as a method: "As a rough guide, an adult dog eats about 2% of his body weight a
    # day", "About a litre a day for a toddler", "Only the platform can take a review down",
    # "Around 20 minutes in the oven". "Only use a little" is a step and is now refused with
    # them - the trade patient-lime measured as 0 genuine methods lost over 1,500 turns.
    "about", "as", "only", "around", "over", "under", "after", "before", "with", "from", "than",
    "like", "at", "in", "on", "to", "of", "for", "by", "up", "down", "out"))

# "Half an hour is 30 minutes." and "Half a cup of coffee is gone in about five hours" are facts
# with a figure in them, and the shape read them as a verb and its thing. `half` is not a word to
# refuse on its own: "Half the plate vegetables or salad, a quarter protein." is a step, and a
# portion is not a unit of measure. So the unit is the thing that decides.
HALF_A_UNIT = re.compile(
    r"^half\s+(?:a|an|the)?\s*(?:hour|hours|minute|minutes|second|seconds|day|days|week|weeks|"
    r"month|months|year|years|cup|cups|glass|glasses|pint|pints|litre|litres|liter|liters|"
    r"kilo|kilos|kilogram|kilograms|pound|pounds|mile|miles|metre|metres|meter|meters|"
    r"inch|inches|teaspoon|teaspoons|tablespoon|tablespoons|tsp|tbsp|degree|degrees)\b", re.I)


def _opens_on_a_job_to_do(sentence):
    """True when the sentence is shaped like an instruction, whatever verb it uses.

    `_opens_on_a_job` reads the verb against `JOB`, a list, so a method that opens on a verb
    nobody thought of ("clear", "unplug", "reinstall") was read as a reply about something else.
    The shape - a verb, then the thing it acts on - is what an instruction is, and `AN_INSTRUCTION`
    reads it without a list. `WANTS_INFO` keeps out a reply that asks the person for the
    information ("Tell me what's going on"), and a word that is no verb, or an -ing, is not one.
    """
    text = str(sentence or "")
    if not AN_INSTRUCTION.match(text) or WANTS_INFO.match(text):
        return False
    if CONTRACTION_OPENER.match(text) or A_WELL_WISHING.match(text.strip()):
        return False
    if A_SUBORDINATE_FRAGMENT.match(text) and "," not in text:
        return False
    if HALF_A_UNIT.match(text):
        return False
    word = re.match(r"[A-Za-z']+", text).group(0).lower().strip("'")
    return (word not in NOT_A_VERB and word not in NOT_AN_OPENER
            and not word.endswith("ing"))

# The hook into the steps reading, kept at the foot of the file on purpose: `_steps` and the region
# above it are the lines every lane edits, and an edit inside it cannot be re-cut onto a main that
# keeps moving under it. Rebinding the reading here gives the same answer, because everything that
# reaches `_steps` looks it up by name (`_steps_in`, `_the_shape_a_reply_gives`, `_CHECKS`).
_steps_by_the_verb_list = _steps


def _steps(opening, after=""):
    """`_steps` by its verb list, and then by its shape: see `_opens_on_a_job_to_do`."""
    return _steps_by_the_verb_list(opening, after) or _opens_on_a_job_to_do(opening)


_CHECKS[STEPS] = _steps
# `_CLEAR` is a tuple built at import, so it holds the old function and has to be rebuilt: it is
# the evidence a reply gave *another* shape, and a method read as a miss for a how-long turns on it.
_CLEAR = tuple((want, _steps) if want == STEPS else (want, check) for want, check in _CLEAR)
