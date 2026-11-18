"""The shape of the answer, when the bot has not got the fact.

Every line here reached the very end of the composer: no knowledge card claimed it, no route to a
place fitted it, and nothing in the thread named who to ring. What the person got was the search
hedge - "I'm not sure about that one, sorry, I'd rather not guess. A quick search online will get
you a solid answer" - which is true of every line ever typed and tells nobody anything. Pointing
elsewhere is not a reply.

There is one thing the bot still knows about a line like that, and it is the shape of the answer:
a pick wants the thing that decides a pick, a price wants the three things that set a price, "how
long" wants the range and the thing that moves it, "why" wants the causes that are worth ruling
out. None of that is a fact about the person's kitchen, and none of it needs to be: it is what a
friend says while getting to the detail, and it is the difference between "go and look it up" and
"here is what the answer depends on".

`fit.wants` has already read the shape and `bot/modules/intent.py` has written it to
`memory["understood"]["wants"]`, so this reads that and nothing else. Every line has to work on
any subject at all - the subject is the one thing the bot has not got - so no line names the thing
and no line assumes what kind of thing it is. The last step is always the person's own detail, in
one short question, because that is what turns the shape into an answer.

Where a line's own words do name the shape of thing (a job, a bill, a wait), the pool says so; the
word "it" is never used for the subject, because a line about a garden and a line about a debt
would then read the same, and the bot already has pools for subjects it can name.
"""

import re

# The shapes this answers, in the words `fit` uses. A line whose shape is not here keeps whatever
# the composer had, which is right for a `person` (who to ask is a place, and the routes above this
# have already named one) and for `place` and `meaning` (a wrong definition is worse than none).
PICK = "pick"
OPTIONS = "options"
AMOUNT = "amount"
TIME = "time"
STEPS = "steps"
YESNO = "yesno"
VAGUE = "vague"
RECALL = "recall"
PAPERWORK = "paperwork"
REASON = "reason"
ADVICE = "advice"

# A pick between two or more things: the bot cannot say which, and can always say what a pick
# turns on. Every line names the two questions that decide most picks - what it has to do, and
# what it costs to be wrong - and ends on the person's own detail rather than a pointer.
PICK_LINES = (
    "I can't pick for you, but two questions settle most choices like this: which one you would "
    "still choose in a year, and which is cheaper to undo if it turns out wrong. Which way are "
    "you leaning?",
    "There is no right answer I can point you at. What every pick like this comes down to is what "
    "you will use most, and whether the cheaper one is good enough for that. What are you down to "
    "choosing between?",
    "Two ways to choose: the one that is best at the main thing, or the one that is decent at "
    "everything. Most people regret the second. What would it have to be good at?",
)
# When the options are already on the table - "were weighing up a bike or a moped", or the answer
# above listed three series - asking "what are you down to choosing between" is asking for what the
# person just gave. Only the two lines that work on a named pair are left for those turns.
PICK_LINES_NAMED = tuple(line for line in PICK_LINES if "choosing between" not in line)

# The same choice said as "anything else", "any other ideas": the person is asking for options and
# the bot has none to offer, so it says what makes a shortlist good and asks for the ingredients.
OPTIONS_LINES = (
    "I have no list to hand you, and I would rather not invent one. What makes a shortlist worth "
    "anything is that the choices are actually different: one cheap, one that lasts, one that is "
    "least effort. Which of those three are you after?",
    "Nothing in front of me to suggest from. Tell me the two or three things that are fixed - "
    "where, when, how much - and I can say what sort of option fits them. Which is the one that "
    "cannot move?",
    "I can't give you a list without making it up. The useful question is what you would say no to: "
    "once that is settled there are usually only two or three options left. What is a no?",
)

# An amount: a price, a count, a number of weeks off. The rule that holds for all of them is that
# a figure is not a fact to look up, it is arithmetic on measurements the person has - so the reply
# asks for the measurements and offers the sum, which is the one part of this the bot does well. It
# never guesses a figure and it never assumes money, because "how many episodes" and "how much does
# a plumber charge" read the same to the reader that sent them here.
AMOUNT_LINES = (
    "I haven't got a figure for that, and guessing one would be worse than none. A number like this "
    "is worked out from two or three others rather than looked up - give me those and I will do the "
    "sums with you. What have you got to go on?",
    "That is arithmetic more than a fact. Tell me the size of it, how many there are, and what it is "
    "per one, and I will work the total out with the steps shown so you can check them. Which of "
    "those do you have?",
    "No number from me without the figures it comes from - that is what stops it being a guess. "
    "What numbers do you already have?",
)

# A duration: a range is honest, and naming what moves a thing from one end of the range to the
# other is the part the bot can do without knowing the subject.
TIME_LINES = (
    "I don't know the size of the job, so any time I gave you would be a guess. Most things like "
    "this are minutes for the small version and a day or more for the big one, and which one you "
    "have is the whole question. How big is it?",
    "That depends on what somebody finds once they start, which is why nobody will give you a firm "
    "number before they look. Ask for the usual time and add half again. Who is doing it?",
    "No honest number from me without knowing the size and who does it. If it is the simple "
    "version it is quick; if anything has to be taken out first it is not. What has to happen?",
)

# A yes or a no: the bot cannot give the verdict, and can give the test a friend would use - what
# it costs if it goes wrong, whether it can be undone, and who else carries it. All three hold for a
# decision about a person, a purchase or a plan, which is the whole range this catches.
YESNO_LINES = (
    "I can't say yes or no to that honestly. The test I would use is the worst that happens if it "
    "goes wrong, and how easily you could undo it. If both are small, it is worth a try - how bad "
    "is the worst case?",
    "That is yours to weigh, and I don't have the details to weigh it for you. It comes down to "
    "what you would lose, how likely that is, and whether you could put it back. What would you "
    "lose at worst?",
    "No verdict from me on this one - I would be guessing. Say what would make you change your "
    "mind, and if nothing would, that is your answer already. What would change it?",
)

# Why something happens: the bot names the usual causes rather than one, because the way to tell
# them apart is what else is going on at the same time.
REASON_LINES = (
    "I don't know this one well enough to say why, and a made-up reason is worse than none. Cases "
    "like it usually have two or three causes, and the way to tell which is yours is what else "
    "happens at the same moment. What else have you noticed?",
    "No cause I could name honestly. The reliable way to find one is to change a single thing at a "
    "time and see whether it goes away - two changes at once tells you nothing. What have you "
    "tried?",
    "I would be guessing at the reason. Whatever it is, it will have a before and after: what was "
    "different the first time it happened?",
)

# What the person might do: the bot has no answer, and the shape of the answer is the person's own
# leaning, which is worth asking for rather than handing back a search.
ADVICE_LINES = (
    "I can't tell you what to do here - I haven't got the details, and it is yours to decide. "
    "Which is the option you keep coming back to? I will argue the other side properly.",
    "No advice worth the name from me on this. The question that usually settles it is the one you "
    "would regret not asking. Which is it?",
    "I don't know enough to say what is right. Put it into one sentence - the choice, and what it "
    "costs - and I will help you look at it from the outside. What is the choice?",
)


# A line with no subject in it at all: "and now?", "what next?", "what should i think about". There
# is no shape of answer to give because there is no thing being asked about, and a search hedge is
# the one reply that cannot help - nobody types "and now?" into a search box. What a friend does is
# say they have lost the thread and ask which bit, which is the one question that can turn the line
# into something answerable. Each line still ends on that question and says nothing invented.
VAGUE_LINES = (
    "Give me a little more and I'll answer that part properly - what are you after?",
    "Happy to keep going - which part do you want next?",
    "That one is too open for me to answer well, and a guess would waste your time. Which bit "
    "matters most?",
    "One more line and I'll have something useful for you. What are you after now?",
)
# Only the forms that carry no subject with them. "where do i start" is not here: main answers that
# one itself, and a job with parts is the steps shape, not a lost thread.
_A_VAGUE = re.compile(
    r"^(?:and|so|ok|okay|right|well|hmm|um)?\s*,?\s*(?:now\s+what|what\s+now|now)\b[\s?!.]*$"
    r"|^what should i (?:think about|be doing(?: now)?|do next|do first)\b[\s?!.]*$"
    r"|^what do i do now\b[\s?!.]*$")

_WHAT_TO_DO_WITH = re.compile(r"\bwhat (?:should|shall|do|would|can|will) (?:i|we) (?:do|use|put)\b"
                               r"[^?.!]{0,20}?\b(?:with|about)\b")
# An ask about something the person already said is a callback, not a shape: "what year is he going
# into again", "what was the name of it", "remind me what i said". The thread holds the answer, and
# a pool about the size of a job or the two things a pick turns on is off the subject - it reads as
# a confident wrong frame, which is worse than the hedge it replaced. A callback is answered (or
# not) by the store, so nothing here answers it.
_A_WHAT_WAS_IT = re.compile(
    r"^\s*(?:and\s+|so\s+)?(?:what|which)\s+(?:was|is|were|are)?\s*(?:the\s+)?(?:year|one|name|number|date"
    r"|day|time|age|colour|color"
    r"|brand|make|model|price|word|thing)\b"
    r"|\bwhat\b[^?.!]{0,24}?\b(?:did|do) (?:i|we) (?:say|tell|mention)\b"
    r"|\bremind me\b|\bwhat did (?:i|we|he|she|they|you) (?:say|tell|decide|choose|pick)\b"
    r"|\b(?:what|which)\b[^?.!]{0,30}?\bagain\b")
# The line says itself that it is about something they told the bot: "as i said", "remind me",
# "again". Without one of these (or a thread) "what time is it" is a question about the world, not
# a callback.
_A_THEY_SAID_SO = re.compile(r"\b(?:i|we)\s+(?:say|said|say\s+it|told\s+you|mention|mentioned)\b"
                             r"|\bagain\b|\bremind\s+me\b")
# "How many days a week should i do to start" is a frequency, not a job whose size has to be
# guessed: the duration pool reads like decorating, and the composer or the advice card is better.
_A_FREQUENCY = re.compile(r"\bhow (?:many|often)\b[^?.!]{0,24}?\b(?:days|nights|times|weeks|months|"
                          r"years)\b[^?.!]{0,12}?\b(?:a|per|each)\b")
# The pick pools answer a question, and the question has to be at the front of the line: "and they
# want it in overnight which is awkward" is a problem being reported, and the "which" in it is a
# relative clause. The ask is read at the start, so a remark cannot slip in on a word buried later.
_AN_ASK_AT_THE_FRONT = re.compile(r"^(?:ok\s+|okay\s+|and\s+|so\s+|but\s+|also\s+)?(?:which|what|"
                                  r"should|shall|would|could|can|do|did|is|are|am|i|we|im|i'm|were|"
                                  r"we're|cant|can't|help|how|any|got)\b")
_WHICH_I_NEED = re.compile(r"\bwhich\b[^?.!]{0,24}?\b(?:do|would|will|should|shall)\s+(?:i|we)\s+"
                           r"(?:need|use|get for|ask for|call)\b")

# An ask about something the person already said, when the store has not answered it: "what subject
# did i say i was revising", "and what was the mileage again", "remind me what i said about the
# deposit". The world cannot help here and a search is the one thing that cannot know, so the
# honest reply is that this is a question about the chat, and one line back gets the fact. No line
# claims the bot never heard it - the store may have it and its reader may have missed - so each
# asks for it again and promises to use it.
RECALL_LINES = (
    "That is one for between us rather than a search - say it once more and I will answer from "
    "what you tell me. What was it?",
    "I would rather have it from you than guess: say it again and I will hold on to it. Which one "
    "was it?",
    "Say it once more and I will keep it this time, then answer straight from that. What was it?",
)

# A date on something of theirs - "and when does it run out" after a renewal, "when does my
# warranty expire", "when do i need to renew my pass". Nothing on the open web holds it and a
# search is a dead end: the date is printed on the thing itself, in the confirmation or their
# account. So the reply says where it is and asks what it says, which also keeps the thread.
PAPERWORK_LINES = (
    "That one is on the paperwork, not out where I can see it - the renewal date sits near the "
    "policy number on the letter or in your account online. What does it say?",
    "The date is in their hands rather than mine: it is on the notice they last sent you, beside "
    "the reference number. Have you still got it?",
    "I can't see your own documents, so the date is on the letter or in the app under the plan. "
    "What date does it give?",
)
_LINES = {
    PICK: PICK_LINES,
    OPTIONS: OPTIONS_LINES,
    AMOUNT: AMOUNT_LINES,
    TIME: TIME_LINES,
    YESNO: YESNO_LINES,
    VAGUE: VAGUE_LINES,
    RECALL: RECALL_LINES,
    PAPERWORK: PAPERWORK_LINES,
    REASON: REASON_LINES,
    ADVICE: ADVICE_LINES,
}

# A thread with somebody ill, dying, grieving or in danger is not a place for "the two questions
# that settle most choices". Those turns belong to the care modules, and this stands down rather
# than talk about decision criteria over the top of them.
_HEAVY = re.compile(
    r"\b(?:died|dying|death|funeral|cancer|hospice|hospital|miscarr\w*|suicide|kill myself|"
    r"abuse|assault|overdose|relapse|diagnos\w*|terminal)\b")


# The two things being weighed are already said - "were weighing up a bike or a moped", or an
# answer that just listed three series. A pool that asks which two things are in the running is
# asking the person to say again what is on the screen, so only the lines that work on a named pair
# are offered for those turns. "or" between two words is the whole test: it is how a pair of options
# is written, and a line with no pair in it has none.
_TWO_THINGS = re.compile(r"(\w[\w'-]*)\W{0,2}\s+or\s+\W{0,2}(\w[\w'-]*)")
# The words that are not one of the options when "or" joins two clauses rather than two things.
_NOT_AN_OPTION = frozenset("""i we you he she it they me us them him her my our your their this that
these those there then so if and but not no yes is are was were do does did can could will would
should shall may might have has had get got go going put take make""".split())


def _the_two_things_are_on_the_table(understood, memory):
    """True when the person or the bot has already said what the choice is between."""
    said = [str(understood.get("clean") or understood.get("text") or "")]
    # Four turns back, not one: an answer that listed three series is still the thing being
    # chosen between two turns later ("its only 2 hours" ... "which one should we start with").
    for turn in (memory.get("turns") or [])[-4:]:
        if isinstance(turn, dict):
            said.append(str(turn.get("user") or ""))
            said.append(str(turn.get("bot") or ""))
    for text in said:
        for left, right in _TWO_THINGS.findall(text.lower()):
            if left not in _NOT_AN_OPTION and right not in _NOT_AN_OPTION:
                return True
    return False


# A bare "how many episodes" after the bot has just named the series is a fact about that series,
# not a sum: the count is written down on the page for it, and asking the person to supply the
# numbers would be asking them for the answer. The same goes for a weight, a price or a length of
# anything already named - so the reader stands down and leaves the line to the rest of the chain.
_HOW_MANY = re.compile(r"^(?:and\s+|so\s+|but\s+)?how\s+(?:many|much)\s+(?:\w+\s+){0,2}?(\w{3,})")
_NOT_THE_THING = frozenset("""more time long often far big much many old new good bad early late
soon quick long worth often""".split())


def _the_figures_are_in_the_thread(memory):
    """The person has already given the numbers, so a reply asking for them is a daft reply."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    for turn in turns[-2:]:
        for source in (str(turn.get("user") or ""), str(turn.get("bot") or "")):
            if re.search(r"\d", source):
                return True
    return False


def _the_bot_just_said_a_lot(memory):
    """The previous answer gave the person something to work with, not just a line back."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    for turn in reversed(turns[-2:]):
        bot = str(turn.get("bot") or "")
        if len(bot.split()) >= 25:
            return True
    return False


def _a_count_of_the_thing_just_named(clean, memory):
    match = _HOW_MANY.match(str(clean or "").lower().strip())
    if not match:
        return False
    word = match.group(1)
    if word in _NOT_THE_THING:
        return False
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-4:]
    if not turns:
        return False
    for turn in reversed(turns):
        for source in (str(turn.get("bot") or ""), str(turn.get("user") or "")):
            if re.search(r"(?<![a-z])" + re.escape(word.rstrip("s")) + r"[a-z]{0,2}(?![a-z])",
                         source.lower()):
                return True
    return False


# `wants` reads the shape of the whole line, and it is right about most lines. Where it can be
# caught being wrong is a duration: "how far ahead should i start packing" carries "how far" and is
# read as an amount, and a pool about the measurements a figure comes from is nonsense for a date.
# A line with a time word in it wants a time, whatever the reader called it.
_A_TIME_WORD = re.compile(r"\b(?:how\s+far\s+ahead|how\s+soon|how\s+long|how\s+quick|"
                          r"when\s+should|what\s+time)\b")
# A time asked about the world is a fact, not a job's duration: "when does the season start" is on
# the fixture list, "how far ahead should i book" is the firm's policy, and neither is a range like
# a decorating job's. Only the duration of something the person is about to do gets the pool
# ("how long does it take the paint to dry", "when should i start").
_A_FACT_ABOUT_TIME = re.compile(
    r"\bwhen (?:does|do|did|will) (?:the|it|they|this|that|a|my|his|her|your)\b"
    # A "when" with somebody or something else as its subject is that thing's calendar, not the
    # person's job: "when does term end" is the council's page, "when does the bus go" is the
    # timetable. "when do i/we" keeps the pool, because that is a job of their own to start.
    r"|\bwhen (?:does|do|did|will)\s+(?!i\b|we\b|you\b)\w"
    r"|\bwhen (?:does|do) it\b"
    r"|\bwhat time (?:does|do|is|are|will)\b"
    r"|\bhow far (?:ahead|in advance)\b"
    r"|\bhow long (?:before|in advance)\b"
    r"|\b(?:should|do|can) i (?:need to )?book\b")
# A count of something that comes in a series or on a packet is printed somewhere: the episode count
# is on the series page, the tablet count on the box. The amount pool asks what a figure is built
# from, which is true of a total the person has to work out and false of a tally they can read off,
# so only a count of the person's own job gets it.
_A_STORED_COUNT = re.compile(
    r"\bhow many (?:episodes|seasons|chapter|chapters|pages|tracks|songs|albums|volumes|parts|"
    r"instalments|films|series|books|tablets|doses|rounds)\b"
    r"|\bhow many \w+ (?:are|were) there\b")
# Yes or no is two different questions. "Should I take it" is a decision, and the test for a
# decision - what happens if it goes wrong, how easily could you undo it - is a real answer. "Do I
# need a drill for the wall straps" is a lookup, and that test is nonsense against it: the drill is
# in the manual and in the wall. Only the decision yes/no gets the pool; the lookup keeps the
# composer's answer.
# A fit state is the exception, not the rule. "ok", "safe", "still good" said of a thing in the
# thread is how somebody asks whether that thing is still in a usable state ("is the rest still ok"
# about a joint whose stuffing burnt), and a test written for a decision is nonsense against it: the
# answer is a fact about the food, not a thing to weigh. So the state words are excluded explicitly,
# and everything else the reading calls a yes/no gets the pool once there is a thread to lean on -
# a wording nobody has typed yet is then answered by the reading rather than by this word list.
_A_FIT_STATE = re.compile(
    r"\b(?:ok|okay|alright|all\s+right|fine|safe|sound|sound\s+enough|still\s+good|still\s+ok|still\s+fine|"
    r"gone\s+off|gone\s+bad|in\s+date|off|spoiled|spoilt|edible|contaminated|damaged|broken|worn|leaking)\b")
_A_POINTS_AT_A_THING = re.compile(r"\b(?:it|that|this|those|these|they|them|the|mine|ours)\b")
# "Is it dying", "has it gone off", "is it cooked yet": a yes/no that leans on the thread and asks
# about the state of the thing in it is a fact about that thing, not a choice to weigh. What makes
# a leaning line a decision is a word asking for a verdict on it - worth, enough, too many, better,
# help, work - and a line with none of those is asking what condition something is in.
_A_VERDICT_WORD = re.compile(
    r"\b(?:worth|enough|too\s+many|too\s+much|better|worse|help|helps|work|works|risk|safe|"
    r"okay|ok|fine|point|bother|afford|matter|matters)\b")
_A_DECISION = re.compile(r"\b(?:should\s+(?:i|we)|shall\s+(?:i|we)|is\s+it\s+worth|worth\s+it|"
                         r"worth|do\s+you\s+think|would\s+(?:i|we)|am\s+i\s+better|enough|"
                         r"too\s+much|too\s+many|better\s+off|bother|afford|for\s+that"
                         # "Would a second one help", "does another dog help": the thing is named
                         # and the ask is whether it is worth doing, which is a decision with no
                         # first person in it. Only help and "be better/good" are read this way -
                         # a thing that needs a part ("would the straps need a drill") is a lookup
                         # and keeps the composer's answer.
                         r"|(?:would|will|does|do|did|could|can)\s+(?:a|an|another|one|two|the)"
                         r"\b[^?.!]{0,25}?\b(?:help|be\s+(?:better|good|worth))\b)")
# "And when does it run out" after a renewal, "when does my warranty expire", "when do i need to
# renew my pass": a date on a thing of theirs. `_A_FACT_ABOUT_TIME` stands those down as world
# facts, which is right for "when does the season start" and wrong here - the difference is whose
# thing it is, so the possessive or the thread decides.
_A_WHOSE_THING = re.compile(r"\b(?:my|our|mine|his|her|their)\b")
_A_DATE_ON_IT = re.compile(r"\b(?:when|what\s+date)\b[^?.!]{0,30}?\b(?:run\s+out|runs\s+out|expire|"
                           r"expires|renew|renews|renewal|end|ends|due|"
                           r"give\s+notice|notice\s+period)\b|\b(?:when|what\s+date)\b"
                           r"[^?.!]{0,24}?\b(?:do|should)\s+(?:i|we)\s+(?:need\s+to\s+)?renew\b")
_THEIR_THINGS = re.compile(r"\b(?:polic(?:y|ies)|insurance|contract|warranty|guarantee|mot|lease|"
                           r"tenancy|licence|license|passport|membership|subscription|pass|"
                           r"agreement|cover|plan|booking|reservation|permit|filing|return)\b")
# "Is that enough for two" is not a decision, and the yes/no pool's "what would you lose at worst"
# is nonsense against a portion: whether a quantity covers a need is worked out from what the need
# is (a portion size, a room's area, a tank's capacity), so the figure-shaped pool is the one that
# fits. It is read whatever the reader called the line, because "enough" is a decision word.
_AN_ENOUGH_ASK = re.compile(r"\b(?:is|are|will|would|do|does|did)\b[^?.!]{0,15}?\benough\b")
# A duration asked about a paper in the thread is a date to be read off it, not a job whose time
# nobody can know before starting: "my car insurance is up for renewal in march" ... "ok and when
# does it run out" is on the policy, and the pool that says "ask for the usual time and add half
# again" is about a trade's day. The document is the answer, so the pool stands down for it.
# A bare ask for a pick is read as a next step when there is nothing to name yet - "what should i
# go for" has no subject, so the only shape in it is the choosing. The pool that says what a pick
# turns on is the right one for it, and a line with something to do in it ("what can i do in class
# tomorrow") has a verb that is not in this list and keeps the composer's own answer.
_A_PICK_ASK = re.compile(r"^(?:ok\s+|and\s+|so\s+)?(?:what|which)\s+(?:should|shall|do|would|can)"
                         r"\s+(?:i|we)\s+(?:go\s+for|pick|choose|get|buy|start\s+with|have)\b")
# A yes/no typed with a first step in it is still a yes/no, but only when the line opens with the
# ask: "should we take him to training classes". "what should i see" carries "should i" inside it
# and is not a decision - on a cat thread ("he's two now") it means "what should I look out for",
# and the yes/no pool's "what would you lose at worst" is nonsense against it.
_A_STRAIGHT_YESNO = re.compile(r"^(?:ok\s+|and\s+|so\s+)?(?:should|shall|do|does|did|would|will"
                               r"|is|are|can|could)\s+(?:i|we|it|that|this)\b")
# A method asked for as a first step is a figure to work out, not a job with parts: "how do i work
# out what we can afford", "how do i figure out how much paint to buy". The shape that helps is
# what the figure is built from, so those lines are read as an amount whatever the reader called
# them. Only working out a number is read this way - "how do i work out my rota" is still steps.
_A_WORK_OUT = re.compile(r"\bhow (?:do|does|would|can|could|shall) (?:i|we)\b[^?.!]{0,30}?"
                         r"\b(?:work|figure|sort)\s+out\b"
                         # "how do i know/tell" is only a figure when the thing asked about is a
                         # quantity; "how do i tell if the cassette is worn" is a diagnosis and
                         # the composer's own order-of-checks answer is what it wants.
                         r"|\bhow (?:do|would|can|could) (?:i|we) (?:know|tell|estimate|budget)\b"
                         r"[^?.!]{0,30}?\b(?:much|many|cost|costs|afford|price|budget|total)\b")
_ON_PAPER = re.compile(r"\b(?:polic(?:y|ies)|renewal|insurance|contract|agreement|licence|license|"
                       r"passport|warrant(?:y|ies)|booking|ticket|statement|invoice|receipt|"
                       r"letter|form|certificate|account|mortgage|tenancy|lease|quote|"
                       r"registration|mot|v5c)\b")
# A bare "what should i visit" after the bot has just given a paragraph about Edinburgh is a question
# about Edinburgh, and the paragraph already holds the answer. A frame about how to choose is worse
# than nothing there, so the pool stands down and the composer's own readers get their turn.
_BARE_ASK = re.compile(r"^(?:ok\s+|and\s+|so\s+)?(?:what|which|where|whats|what's)\s+"
                       r"(?:should|shall|do|can|could|would)\s+(?:i|we)\s+"
                       r"(?:visit|see|do|go|eat|drink|get|buy|put|pick|choose|start|try|book)\b")

# A line that leans on the thread - "does that change the cake", "is that enough", "how far ahead" -
# is a question about the thing in the conversation, and a generic frame about what a choice costs
# is off the subject. The thread's readers own those turns, so this stands down for them.
_LEANS_ON_THE_THREAD = re.compile(
    r"^(?:and\s+|so\s+|but\s+|ok\s+)?(?:does|do|did|is|are|was|were|will|would|can|could|"
    r"should)\s+(?:that|this|it|they|those|these)\b")


def _on_paper(line, memory):
    """True when a paper named in the line or the last few turns holds the date or the figure.

    A policy's renewal date, a licence's expiry, a bill's total: the person has the document and
    the answer is printed on it. Nothing here is a job whose length or cost is being weighed, so
    a shape pool that asks what the figure is built from is off the subject.
    """
    said = [str(line or "")]
    for turn in (memory.get("turns") or [])[-4:]:
        if isinstance(turn, dict):
            said += [str(turn.get("user") or ""), str(turn.get("bot") or "")]
    return any(_ON_PAPER.search(text.lower()) for text in said if text)


def _the_thing_is_theirs(memory):
    """True when the thread has a thing of their own in it that a date could belong to.

    "ok and when does it run out" carries no noun at all, so the noun has to come from what they
    said: "my car insurance is up for renewal in march". A bare "when does the season start" after
    nothing of theirs stays a world fact.
    """
    if not isinstance(memory, dict):
        return False
    for turn in (memory.get("turns") or [])[-3:]:
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("user") or "").lower()
        if _A_WHOSE_THING.search(said) and _THEIR_THINGS.search(said):
            return True
    return False


def _the_thread_is_heavy(memory):
    for turn in (memory.get("turns") or [])[-3:]:
        if not isinstance(turn, dict):
            continue
        if _HEAVY.search(str(turn.get("user") or "").lower()):
            return True
    return False


def the_shape_without_the_fact(understood, memory=None):
    """The pool for the shape of answer this line wants, or None when it wants none of these.

    The shape is the one the intent module already wrote; a line with no shape of its own is left
    to the composer, because there is nothing about it the bot could say that would be true.
    """
    if not isinstance(understood, dict):
        return None
    want = understood.get("wants")
    line = str(understood.get("clean") or understood.get("text") or "").lower()
    # The two readings this file corrects are corrected before the shape is looked up, because a
    # shape with no pool of its own ("steps") would otherwise be dropped on the way in.
    if want == STEPS and _A_PICK_ASK.match(line.strip()):
        want = PICK
    # A figure worked out is asked for before the decision words are read: "how do i work out what
    # we can afford" carries "afford", which is a decision word, and the shape that helps is what
    # the figure is built from rather than what would change their mind. "should we take him to
    # training classes" is read as steps and is a plain yes/no.
    if want == STEPS and _A_WORK_OUT.search(line):
        want = AMOUNT
    elif want == STEPS and _A_STRAIGHT_YESNO.match(line.strip()):
        want = YESNO
    if want == AMOUNT and _A_TIME_WORD.search(line):
        want = TIME
    # A date on something of theirs is on the thing itself, not out on the open web: "and when does
    # it run out" after a renewal, "when does my warranty expire", "when do i need to renew my
    # pass". Whose thing it is decides it - "when does the season start" is still a world fact and
    # still stands down, which is what the next block is for.
    if _A_DATE_ON_IT.search(line) and (_A_WHOSE_THING.search(line) or _the_thing_is_theirs(memory)):
        want = PAPERWORK
    # A frequency is not a job's size; a remark with no ask in it is not a choice.
    if want in (AMOUNT, TIME) and _A_FREQUENCY.search(line):
        return None
    if (want in (PICK, OPTIONS) and not _AN_ASK_AT_THE_FRONT.match(line.strip())
            and not _TWO_THINGS.search(line)):
        return None
    # A date or a lead time is a fact somebody else holds; a count of a series is printed on it.
    elif want in (TIME, AMOUNT) and _A_FACT_ABOUT_TIME.search(line):
        return None
    if want == AMOUNT and _A_STORED_COUNT.search(line):
        return None
    # A callback is a question about this chat, not about the world: no pool of facts applies, and
    # the search hedge is the one reply that cannot know. The recall pool asks for it again.
    # Only on a chat with nothing in it yet, and only when the line itself points back ("i said",
    # "remind me", "again"): once there is a thread, the store is the reader for "what did i say",
    # and a bot holding the conversation must not ask for it again. That is the whole difference
    # between a first line and the tenth.
    _turns = memory.get("turns") if isinstance(memory, dict) else None
    if _A_WHAT_WAS_IT.search(line) and _A_THEY_SAID_SO.search(line) and not _turns:
        want = RECALL
    elif _A_WHAT_WAS_IT.search(line) and _turns:
        # In a thread the store is the reader for a callback, and its answer is the fact itself.
        return None
    # A line that carries no subject of its own gets the one question that can give it one.
    if _A_VAGUE.match(line.strip()):
        want = VAGUE
    # "Which trade do i need" is a lookup for the right kind of person or part, not a choice
    # between two things on the table: the pick pool's "what would it have to be good at" reads as
    # a decision about a purchase. The composer answers these, and a better card belongs in the
    # knowledge base rather than in a fallback.
    if want in (PICK, OPTIONS) and _WHICH_I_NEED.search(line):
        return None
    # "and then what do i do with the rest" is a next step, not a choice: the pick pool's two
    # questions about a purchase are off the subject, and asking what to do with something is the
    # composer's job. A pick between two things says which, what, or which one.
    if want in (PICK, OPTIONS) and _WHAT_TO_DO_WITH.search(line):
        return None
    if want not in _LINES:
        return None
    if _the_thread_is_heavy(memory or {}):
        return None
    if memory and memory.get("turns"):
        # A yes/no that leans on the thread is still the same decision, and the yes/no pool asks
        # the person what would change their mind rather than naming the thing again: "we have two
        # cars" / "is that too many" is a line the pool can answer without knowing what "that" is.
        if want != YESNO and _LEANS_ON_THE_THREAD.match(line.strip()):
            return None
        if want in (PICK, STEPS, OPTIONS) and _BARE_ASK.match(line.strip()) \
                and _the_bot_just_said_a_lot(memory):
            return None
    if want == YESNO and _AN_ENOUGH_ASK.search(line):
        want, pool = AMOUNT, _LINES[AMOUNT]
        return pool
    if want == YESNO and _A_FIT_STATE.search(line) and _A_POINTS_AT_A_THING.search(line):
        return None
    if want == YESNO and _LEANS_ON_THE_THREAD.match(line.strip()) \
            and not _A_VERDICT_WORD.search(line):
        return None
    if want == YESNO and not _A_DECISION.search(line) \
            and not (memory and memory.get("turns")):
        return None
    if want in (AMOUNT, TIME) and _on_paper(line, memory or {}):
        return None
    if want in (AMOUNT, TIME) and _the_figures_are_in_the_thread(memory or {}):
        return None
    pool = _LINES.get(want)
    if want == PICK and _the_two_things_are_on_the_table(understood, memory or {}):
        pool = PICK_LINES_NAMED
    if _a_count_of_the_thing_just_named(understood.get("clean") or understood.get("text"),
                                        memory or {}):
        return None
    return pool

# The three plain hedges, and the receipts that are not answers either. A hedge that already names
# where the answer lives ("the council's site has the collection day") is a better reply than a
# frame about how to choose, and is left alone.
_A_HEADS = 40


def _a_placeholder(reply, fallback):
    """True when the line says nothing about this turn: a plain hedge or a bare receipt."""
    said = " ".join(str(reply or "").lower().split())
    if not said:
        return False
    if fallback._in_a_pool(reply, (fallback.NEUTRAL,)):
        return True
    return said[:_A_HEADS] in [line.lower()[:_A_HEADS] for line in fallback.UNKNOWN]


def _a_thread_with_a_person_in_trouble(fallback, memory):
    """A worry about somebody's health, a death, a crisis, or a line about the body.

    A general frame about how to weigh a choice is the wrong thing to say to somebody whose mother
    is in hospital, and the bot has readers of its own for those turns.
    """
    for reader in ("_in_a_care_thread", "_in_a_loss_thread", "_in_a_crisis_thread",
                   "_thread_is_about_the_body"):
        try:
            if getattr(fallback, reader)(memory):
                return True
        except Exception:  # noqa: BLE001 - a reader that cannot be asked does not fence
            continue
    return False


def answer_for(text, memory, reply):
    """The pool to say in place of a placeholder reply, or None to leave the reply alone.

    `reply` is the line this turn already has, so this is asked last: after every card, place
    route, gap reader and the composer's own lines. Only a reply that says nothing about the line
    is replaced - one of the three plain hedges or a bare receipt - which is why the shape of an
    answer never stands over a turn the lane can already answer.
    """
    from . import fallback  # noqa: PLC0415 - the composer imports this file's pools, not this

    if not isinstance(memory, dict):
        return None
    understood = memory.get("understood")
    if not isinstance(understood, dict):
        return None
    if not _a_placeholder(reply, fallback):
        return None
    pool = the_shape_without_the_fact(understood, memory)
    if pool is None:
        return None
    if _a_thread_with_a_person_in_trouble(fallback, memory):
        return None
    clean = understood.get("clean") or " ".join(str(text or "").lower().split())
    return fallback._choose(pool, memory, clean)
