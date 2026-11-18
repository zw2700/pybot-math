"""They ask for what to do next, and the bot has just said it.

The commonest follow-up there is: the bot answers "my washing machine is leaking" with the steps
to take, and the next line is "what do I do?" or "and now?" - or the bot answers "i've got about
400 pounds for a used bike" with what to check, and the next line is "what should I look for?".
Both got a search hedge ("I'm not sure about that one, sorry - I'd rather not guess"), which
reads as if the answer had never been given.

This finds that turn: a question with no thing of its own (every word in it is an ask word), the
answer the bot gave a turn or two ago, and nothing said in between that moved the subject on.
Then the reply is that answer again in short form, not a hedge.

The rule is narrow on purpose:
* the line must name nothing, so "what should i cook tonight" and "how long will it take" never
  come here - they have an answer of their own;
* the bot's own hedges are skipped, never handed back ("I'm not sure about that one" is not an
  answer to repeat);
* only the turns just before this one count, and the answer has to be about the thing the chat
  is still on;
* the answer comes back in its short form, so the long version is never read out twice.
"""
import re

from ..compose import pick
from ..compose.whole import a_whole_cut
from ..understanding import understand
from . import counts, facts, history, limits, narrow, recall, topics

# `helps` and `helped` sit beside `help` because a bare "what helps" is the same ask back as
# "what should i do" and was not read as one: a word boundary leaves "helps" behind as a word
# of its own, so the line named something of its own and every reader that asks "does this
# line name a thing" stood aside. It reached a search hedge ("im tired all the time" / "what
# helps") where `deck/a-bare-ask-that-lost-its-answer` has rows saying a person means the
# doing the answer just gave.
# The words a line can be made of and still ask nothing of its own: a way of asking for what to
# do, look for, try or do next, with no thing named.
ASK = frozenset("""
    what whats how where when which why who
    do does doing done now next then instead else anything something
    look looking start begin fix sort try use get make buy take stop
    should shall can could would will may might have has had
    i me my we you your it its that this these those there
    the a an again more better please tell say said too as well
    go going work help helps helped helping suggest recommend about at on in with
    first begin beginning step steps change advice tip tips thing things
""".split())

# A second list of ask words, kept separate because these are verbs a person asks the bot to do
# *for them* - "what should i check", "what should i ask", "what do i bring". They name nothing:
# the thing they are about is what the chat is already on, which is why "what should i check"
# after "im thinking of buying a used car" wants the answer it was just given. The object has to
# be said for the line to name something: "what should i check on a used car" is not this turn.
ASK_VERB = frozenset("""
    check checking ask asking bring bringing pick picking choose choosing spend spending
    watch watching expect expecting pack packing book booking
    first next step steps part bit
""".split())

# The verb families a line that names nothing can be written with. A follow-up that uses the same
# family as the question before it is asking for that answer again ("i want to cook something
# nice" then "what should i make"); a family the question never used is asking for something new
# ("i want to learn guitar" then "what should i buy" is about the guitar the person has yet to
# buy, not about the learning plan, so the buying entry keeps that turn).
DOINGS = (
    ("make", "makes", "made", "making", "cook", "cooks", "cooked", "cooking", "bake",
     "bakes", "baked", "baking", "prepare", "preparing", "serve", "serving"),
    ("buy", "buys", "buying", "bought", "get", "gets", "getting", "got", "pick", "picks",
     "picking", "choose", "chooses", "choosing", "chose", "shop", "shopping", "spend",
     "spending"),
    ("check", "checks", "checking", "look", "looking", "inspect", "test", "testing",
     "watch", "watching"),
    ("ask", "asks", "asking", "say", "says", "saying", "tell", "telling", "word", "words"),
    ("bring", "bringing", "take", "taking", "pack", "packing", "wear", "wearing"),
    ("try", "tries", "trying", "use", "using", "start", "starting", "begin", "beginning"),
)

# The words for asking what to do at all, with no work named: "what do i do", "and now", "what
# next". They are the shape the repeat module is for, whatever the question before them said.
WHOLE_OF_IT = frozenset("""
    do does doing done next then else now step steps first also more again
""".split())


def _doings(text):
    """The verb families a line asks its work with."""
    words = set(topics.words(text or ""))
    return {i for i, family in enumerate(DOINGS) if words & set(family)}


def asks_for_the_same_work(text, memory):
    """True when a line that names nothing asks for the answer the question before it got.

    This is the test a knowledge answer gives way to: a line like this has no thing of its own,
    so the entry it reaches is a neighbour of the subject rather than the question asked - but
    only when the work is the same work. A new verb is a new question and keeps its own answer.
    """
    if not names_nothing(text):
        return False
    if history.about_the_chat(text):
        # "how did we start?" names nothing and carries a verb this reader knows ("start"), and
        # the question it follows said "im trying to save 3000 pounds for a car", whose "trying"
        # is in the same verb family - so the same-work rule took a question about the chat and
        # answered it "Start with this: pick the rate your pay can carry". A line that asks what
        # was said before is never a request for the answer again: the store recaps it.
        return False
    asked = _doings(text)
    if not asked and not (set(topics.words(text or "")) & WHOLE_OF_IT):
        return False
    whole = bool(set(topics.words(text or "")) & WHOLE_OF_IT)
    for back, question, said in _recent_answers(memory):
        if back > 1 and not _about_the_same_thing(question, said, memory):
            continue
        return whole or bool(asked & _doings(question))
    return False


# Lead-ins: they carry nothing, so a line of them plus ask words still names nothing.
FILLER = frozenset("and so ok okay but well alright right then just maybe perhaps also too "
                   "good best".split())

# A time names no thing: "what should i do tonight" is the same ask as "what should i do", and the
# answer is the answer just given. It was not in the list, so the one word stood the repeat down
# and the person who asked what to do tonight about a child who will not sleep got a search hedge
# a turn after the bot had told them what to do. What the time is never a new subject: a line
# with a real one in it ("what should i cook tonight") still names something and never comes here.
TIME = frozenset("""tonight today tomorrow morning afternoon evening night later soon week
    weekdays weekend month""".split())

# A word for who does the thing is not a thing the line names: "what can i do about it myself"
# and "can i fix it myself" ask exactly what "what can i do about it" asks. The word stood the
# repeat down, so a chat that had been answered - a laptop whose fan had gone loud, with a detail
# said back in between - got "I'm not sure about that one, sorry" a turn after the answer.
SELF = frozenset("myself yourself himself herself itself oneself ourselves yourselves themselves".split())

# Lines that asked something rather than said something, so a bare question cannot be read as
# answering them.
# It has to ask for a way to do something, not for a decision: "should i buy it" and "why" are
# their own kinds of turn, and repeating an answer at them is not what they asked for.
QUESTION = re.compile(r"^\s*(?:and\s+|so\s+|ok\s+|okay\s+|but\s+|well\s+|right\s+)*"
                      r"(?:what|whats|how|where|now|next|then)\b", re.I)


# A lead that says the subject is dropped: "nvm, whats the tax deadline" after a question about
# flexible working was answered with the *second half* of that answer, because the new ask kept
# two words of it. What follows the lead is the whole of the turn, and it is read on its own.
RESET_LEAD = re.compile(
    r"^\s*(?:nvm(?:\s+(?:that|this|it))?|never\s*mind(?:\s+(?:that|this|it))?|nevermind|"
    r"forget\s+(?:it|that|this)|ignore\s+(?:it|that|this)|"
    r"scrap\s+(?:it|that|this)|anyway|anyways|new\s+question|different\s+question|"
    r"changing\s+the\s+subject|change\s+of\s+subject)\b[\s,.:;-]*", re.I)


def without_a_reset(text):
    """The line with a "forget that" lead taken off, so the new ask is read as the whole turn."""
    return RESET_LEAD.sub("", (text or "").strip(), count=1)

# "i don't know what to do" is the bare ask in the first person. It starts with "i", so the
# question lead never matched it and the person who said it - after being told what to do about a
# problem at work, or a parent in hospital - got a pool that answers nothing at all. It names no
# more than "what should i do" does.
LOSS_WORDS = frozenset("""dont know idea sure stuck really not even lost help someone
    thought anymore loss at myself""".split())

AT_A_LOSS = re.compile(
    r"^\s*(?:and\s+|so\s+|ok\s+|okay\s+|but\s+|well\s+|right\s+|honestly\s+)*"
    r"(?:i\s+)?(?:really\s+|just\s+)?(?:don'?t|dont|do not|didn'?t|didnt)\s+"
    r"(?:really\s+)?know\s+(?:what|how|where|who|which|when)\s+"
    r"(?:to\b|next\b|else\b|any\s?more\b|first\b)"
    r"|\b(?:(?:have|got)\s+)?no\s+idea\s+(?:what|how|where)\s+to\b"
    r"|\b(?:not\s+sure|stuck|at\s+a\s+loss)\s+(?:what|how|where)\s+to\b", re.I)

# The modules whose reply is an entry's answer: the knowledge base's, and the store's own when it
# hands an entry back (a repair that keeps the ask, a condition added to a choice).
ANSWER_MODULES = ("answers", "memory_store")

# How long an answer from the store has to be before it is the entry's words rather than a nod.
A_STORE_ANSWER = 120

# A hedge says nothing to repeat: it is what the bot says when it has no answer.
HEDGE = re.compile(r"\b(?:i'?m not sure|i don'?t know enough|that'?s beyond what i know|"
                   r"a quick search|searching for it|i'?d rather not guess|"
                   r"can'?t call that one|not mine to decide|nothing so far|"
                   r"search should sort you out|tell me what you find|"
                   r"what would be most useful|anything you'?d like a hand with)", re.I)

# How the answer comes back the second time: the same thing, minus the paragraph.
LEADS = (
    "You've got it: {said}",
    "That's the one: {said}",
    "It's what I said a moment ago: {said}",
    "Same answer: {said}",
    "From just now: {said}",
)

# One word after an answer is the ask to hear that answer again, and it is the commonest way of
# all to ask: "what?", "huh?", "sorry?", "come again?". The pool above answers an ask that took
# the answer in - "what do i do", "anything else" - with "You've got it:", which says the person
# agreed to something. On a bare ask nobody agreed to anything; they did not catch what was said:
#
#     how do i stop my pasta sticking together / what?
#       "You've got it: Stir it once as it goes in and once more a minute later ..."
#
# So a bare ask is handed the same answer under a lead that offers it again. The two words that
# are also ordinary apologies are the ask only with a question mark ("i got the job" / "sorry" is
# sympathy, not a request to repeat), and every word of the line has to be the ask.
BARE_ASK = re.compile(
    r"^(?:(?:sorry|er|erm|um|uh|oh|ah|ok|okay|and|so|but|wait|hmm|hey)\W+)*"
    r"(?P<word>huh|eh|come again|what was that|what did you say|say what|wha|hm|what|sorry|pardon)"
    r"(?:\s+(?:please|again|then|now|sorry))*\W*$", re.I)
BARE_ASK_NEEDS_A_QUESTION = frozenset("what sorry pardon".split())

SAY_AGAIN_LEADS = (
    "Again: {said}",
    "Sorry, again: {said}",
    "Said again: {said}",
)

# "what would help first", "where do i start", "whats the first thing to change": the person is
# not asking for the answer again, they are asking which part of it to do. Answering with the
# answer's opening sentence tells them the thing they already know, and answering with a search
# hedge disowns the answer given a turn ago - both are the wrong shape for this line.
# What a "that doesnt work" gets: the move past the advice, said in the answer's own words, with
# the report acknowledged rather than ignored.
TRIED_LEADS = (
    "Then it is worth going a step further: {step}",
    "If that is not shifting it, the next move is this: {step}",
    "Right - then the thing that is left is to go further: {step}",
)

# The sentence an answer closes on about who to go to when the advice alone is not enough. It is
# not the same paragraph read out again: it is the next move, and it is the answer's own words.
NEXT_STEP_EMERGENCY = re.compile(
    r"\b(?:999|911|112|a&e|accident and emergency|emergency (?:services|department|room)|"
    r"crisis line|116 123|988|samaritans)\b", re.I)
# The answer being reported on is itself the emergency route, so the step after it can only be
# that route said again. A lesser one - the "pharmacist or a doctor" that closes a pain answer -
# reads as permission to wait when it comes after "ring 999", and that is the one reply a
# frightened person must never get from this bot.
NEXT_STEP = re.compile(r"\b(?:gp|doctor|nurse|pharmacist|chemist|dentist|vet|optician|midwife|"
                       r"health visitor|111|999|911|helpline|a&e|hospital|council|"
                       r"citizens advice|plumber|electrician|engineer|gas safe|mechanic|"
                       r"locksmith|roofer|builder|technician|specialist)\b", re.I)

MOVE_ASK = re.compile(r"\b(?:help|helps|helped|helping|first|start|begin|next|step|steps|"
                      r"change|try|do|advice|tip)\b",
                      re.I)

# "Can i save it", "is it ruined", "can it be fixed": the thing is on the table from the answer
# just given, and what is asked is whether any of that answer still gets it back. It is the same
# ask as "where do i start" and wants the same thing - the answer's own first move, in its own
# words. Without it the line reached nothing: the answer was already on the screen, so the shape
# was handed a search hedge a turn after the bot had said what to do.
PUT_RIGHT = re.compile(
    r"\b(?:save|saved|salvage|salvageable|rescue|rescuable|revive|recover|redeem|fix|fixed|"
    r"repair|ruined|wasted|undo|undoable)\b", re.I)
# The words a put-right ask is made of, and the ones that name something of their own: "can i save
# it" names nothing ("it" is the thing on the table), "can i save money on my heating" names both
# a subject and a goal and is a question of its own.
# The way a put-right ask opens. It is not `QUESTION`, which reads the asks for a thing to do and
# does not carry "can", "is it" or "any chance" - the words these lines are actually made of.
PUT_RIGHT_ASK = re.compile(
    r"^\s*(?:and\s+|so\s+|ok\s+|okay\s+|but\s+|well\s+|right\s+)*"
    r"(?:can|could|can'?t|is|are|will|would|should|does|do|any|anything|is there|any chance)\b",
    re.I)
PUT_RIGHT_WORDS = frozenset("""
    save saved saving salvage salvageable rescue rescuable revive recover recoverable redeem
    fix fixed fixing repair repaired ruined waste wasted undo undoable gone dead done late still
    worth anyway any way ways chance point hope
""".split())

# "and now" is the bare ask for the next move in the same words as "what do i do": said after an
# answer about a sore knee it was handed the whole opening sentence again behind "Same answer:",
# which is the diagnosis they had just read, not the thing to do. It names no more than "what now"
# does, which is already read as an ask for the next step.
AND_NOW = re.compile(r"^\s*(?:and\s+|so\s+|ok\s+|okay\s+|right\s+)?now(?:\s+then)?[\s?.!]*$",
                     re.I)

# The lead for a put-right ask: the answer's move is still there to take, so the reply opens on
# that rather than on "start with this", which reads as a job they have not begun.
PUT_RIGHT_LEADS = (
    "Worth a go: {step}.",
    "Yes, there is something: {step}.",
    "Not too late: {step}.",
    "There is still this: {step}.",
)

# "what can i do with that" is not a move ask. It says "with that" - the thing the last
# answer was about - so it asks what the thing can be used for, and the answer is a dish or a
# use, not the first step of the instructions just given. The move rule heard the bare "do"
# and cut the dish answer to "Add the tinned tomatoes and a pinch of salt". A line that asks
# for a move on the answer says it plain ("what do i do first", "where do i start").
USE_WITH = re.compile(r"\b(?:what|anything)\s+(?:can|could|should|do|would)\s+"
                      r"(?:i|you|we)\s+do\s+with\s+(?:that|this|it|them|those)\b", re.I)

# "what else" asks for the next part of the answer in hand, not for the answer again. Said after a
# step, the whole answer read out is the paragraph they have already had twice, and the first part
# of it is the step they were just given, so the ask is answered with the part of the answer that
# comes next, and the ask after that with the part after that.
NEXT_ASK = re.compile(r"\b(?:what|anything)\s+else\b|\bwhat\s+next\b|\bnext\s+one\b|"
                      r"\bwhat\s+now\b|\bwhat\s+other\b|\band\s+then\b|\band\s+after\s+that\b|"
                      r"\bthen\s+what\b",
                      re.I)

NEXT_LEADS = (
    "Next up: {step}.",
    "The next one: {step}.",
    "Then this: {step}.",
    "After that: {step}.",
)

# The part that comes next can be the reason rather than the doing ("A sore knee is usually a
# strain or the kneecap tracking badly"), and "after that" in front of it promises a step it does
# not have: the second lead says where the line comes from and no more.
ALSO_LEADS = (
    "Also in that answer: {step}.",
    "And this: {step}.",
    "It also said this: {step}.",
    "There is this too: {step}.",
)

# A move is said in the answer's own words, as the thing to do rather than as a claim about the
# subject, so the lead has to be able to take a verb phrase.
MOVE_LEADS = (
    "Start with this: {step}.",
    "The thing to do first: {step}.",
    "I would start here: {step}.",
    "The first thing to do: {step}.",
)

# A lead and a step can say the same thing twice: "The first thing to do: Start with the room you
# walk through most" is one step said as first twice, and so is "Start with this: Start with
# run-walk". Which answers are affected is the answer's business, not the ask's - an entry whose
# step opens on its own "Start with" gets this fault on every start ask - so the rule is here: when
# the step says first itself, the lead may not say it too.
STEP_SAYS_FIRST = re.compile(r"^(?:start|begin|first)\b", re.I)
LEAD_SAYS_FIRST = re.compile(r"\b(?:start|begin|first)\b", re.I)
# What is left for those steps: they mark the one thing to do now without saying where in the
# answer it sits, because the step is already saying that. The answer's own words are what is
# being handed back, so the lead is the half that gives way.
NOW_LEADS = (
    "The one to do now: {step}.",
    "The one I would pick: {step}.",
    "Do this one: {step}.",
)


# Someone who says they do not know what to do is asking to be told one thing to do next, and the
# answer's own step is it. Said plainly, without the "same answer" framing, which reads like a
# complaint that they were not listening.
LOST_LEADS = (
    "Start with this: {step}.",
    "One thing to do first: {step}.",
    "Begin here: {step}.",
    "That's alright. Start with this: {step}.",
)

# The copula is scaffolding around the thing, never part of its name: "it was black mould" names
# the mould, and a confirmation that says "Was black mould, yes." is the scaffolding read as a word.
BE_FORM = frozenset("be been being is are was were am its it's thats that's".split())
# A pronoun points at the thing instead of naming it ("it was it", "that was low heat"), so it is
# scaffolding too - but only at the front, where it replaces the subject of the sentence.
POINTING_AT = frozenset("it that this".split())

# The words that say the person agrees and nothing more, so a line made of the answer plus these
# is the answer said back: "ok so low heat then". They come out of the confirmation.
AGREEING = frozenset("""
ok okay k right yes yeah yep yup got it good cool nice alright oh ah so then just too as well and
but actually honestly really well great perfect thanks cheers course fine sure indeed exactly
""".split())

# The words that agree on their own, as against the ones that only join a line together. "and",
# "but", "so", "then", "too", "as well" and "just" are how a person hangs a second thing onto the
# first, so a line that opens on one of them is asking about something else and is not a yes:
# "and for hard boiled", after the egg times, answers itself with "That's it: for hard boiled.",
# which the person cannot read. Only a word here makes a line an agreement.
AGREEMENT_TAIL = frozenset("""
then too well right ok okay yes yeah yep yup both is
""".split())
AGREES_ON_ITS_OWN = frozenset("""
ok okay k right yes yeah yep yup good cool nice alright great perfect thanks cheers course
fine sure indeed exactly
""".split())

# "got" and "it" are not a yes on their own: they are the commonest verb and pronoun in the
# language, and a line that carries one is usually news, not agreement - "someone else got the
# promotion", "they gave it to someone else", "i got a promotion". Both used to agree on their
# own, and the answer they were matched against came back with the verb taken out of the line:
# "someone else got the promotion" was answered "Someone else the promotion, that's the main
# thing." The set phrases are what agree, so those are matched as phrases.
AGREES_IN_A_PHRASE = re.compile(
    r"\b(?:got|get|gets|that's|thats|is|was|does|did)\s+(?:it|that|this|you)\b", re.I)

# "What should I change first" is not "what should I do first", and a lead-in that answers the
# other one reads as an answer to a question nobody asked: "The first thing I would change: Pasta
# with a sauce" answered "how do i learn to cook / what should i do first". So the lead is picked
# by the ask - one for the thing to do, one for the thing to change.
# "sort" and "try" are not change words: "what should we sort first" after a washing-machine
# answer is the thing to *deal with* first, and "Start by changing this: Run a hot 60C service
# wash" answers a question nobody asked, with a doubled verb (start by changing / run). Anything
# that means "deal with" belongs to the move leads; only change, fix, tackle and improve ask for a
# thing to change.
CHANGE_ASK = re.compile(r"\b(?:change|changed|fix|tackle|improve)\b", re.I)
# Every form has to read in front of an instruction, because the step a knowledge answer gives is
# usually one: "Change this first: Run a hot wash" keeps the ask, where "Start by changing this:
# Run a hot wash" is two verbs in a row that do not fit together.
CHANGE_LEADS = (
    "The first thing I would change: {step}.",
    "What I would change first: {step}.",
    "Change this first: {step}.",
)

# "what else can i do", "anything else i can try": the answer was on the screen and this line
# asks for one more thing out of it, so the reply is the next thing in that answer rather than
# another run at the whole paragraph or a search.
MORE_LEADS = (
    "Also from that answer: {step}.",
    "Another one from it: {step}.",
    "Worth trying as well: {step}.",
    "There is this one too: {step}.",
)

# The verbs an entry can open its instruction on that `verdict`'s list does not carry: entries
# about money say "Track two weeks of what leaves the account", the washing machine says "Run a
# hot service wash". Being off that list dropped the whole sentence and the move ask was handed
# the paragraph again ("where do i start" after "im trying to save money" -> "Same as before:").
# Kept here rather than added to `verdict`'s list so nothing outside the answer-handing-back path
# starts reading these words as an instruction.
MOVE_VERBS = (
    "track", "run", "note", "list", "lift", "simmer", "scrub", "wipe", "weigh", "sort",
    "split", "tip", "pour", "stir", "seal", "label", "spray", "blot", "trim", "tie",
    "cap", "dab", "pick", "chip", "sand", "scrape", "air", "dose", "feed", "renew", "fix",
    "swap out", "cut out", "turn off", "shut", "lock", "charge", "defrost", "descale", "dilute",
    "bring", "anchor", "aim", "count", "hold off", "leave out", "cut back", "write down",
    # The words a step opens on that are not in the composer's imperative list: an instruction is
    # read by its first word, so a verb that is missing here is a step the reader walks past.
    "undo", "unscrew", "screw", "pull", "push", "lift out", "prise", "wiggle", "dry", "brush",
    "vacuum", "mop", "dust", "sweep", "empty", "shake", "tape", "glue", "clamp", "snip",
    "preheat", "grease", "knead", "prove", "dust off", "wash out", "scrub out", "air out",
)

# Where an instruction's verb phrase ends and its detail starts. "Run a hot 60C or 90C service
# wash with a washing-machine cleaner or a cup of bicarbonate of soda" is one sentence and 19
# words, too long to hand over as the thing to do first, and the move is the part before the
# qualifier: "run a hot 60C or 90C service wash".
# An instruction longer than this is a sentence with its detail in it, and the detail comes off at
# the qualifier. Under it the sentence is handed over whole: "put the immersion and any room
# heaters on a timer for the hours you actually use" is 16 words, complete, and better than the
# fragment a cut at 12 words left behind.
STEP_WORDS = 20
# An instruction that carries its own method or its reason after a colon is one step, and it is
# a little longer than a bare one: "start with run-walk: one minute of easy jogging, two minutes
# of walking, repeated for 20 minutes, three times a week" is the whole of what to do.
STEP_WITH_ITS_METHOD = 30
# Past this many words the detail comes off at the qualifier.
CUT_WORDS = 12
# A cut that leaves less than this is not a step, it is the start of one.
SHORT_STEP = 6
# Verbs that are not finished without what comes after them: "put the immersion and any room
# heaters" is not an instruction, it is half of one, so a sentence opening on these is handed
# over whole. The list is short on purpose - a verb that reads as a step on its own is cut.
NEEDS_COMPLEMENT = frozenset("put place set leave keep wrap cover soak spray apply dip store "
                             "hang lay pour fill seal".split())

# Where a long instruction may end: at the reason for it, or the condition on it. The instruments
# and the places stay in ("a service wash **with a washing-machine cleaner**", "**then** undo the
# trap"), because they are what makes the instruction work rather than detail about it.
QUALIFIER = re.compile(r"\b(?:because|so that|which|if|unless|before|after|until|while|when|"
                       r"once|in case|as long as|rather than)\b", re.I)

# An instruction can open on a short phrase before its verb: "Half fill the kettle with equal parts
# water and white vinegar", "Each week add a minute to the jog". A reader that wants the verb first
# passed both over - so the kettle step that says what to put in the kettle was handed over as
# "Boil it and leave it half an hour" (an empty kettle), and the running plan answered "what next"
# with only two of its three steps. The phrase stays in the step: "each week" is what makes it a
# plan.
LEADING_PHRASE = frozenset("""half quarter each every once twice three two four five one times
    day days week weeks month months year years minute minutes hour hours night nights morning
    mornings evening evenings afternoon per in on at for after before during gently slowly
    carefully lightly quickly easily really also just only about""".split())

# An article is part of a leading phrase but never its first word: "once a day take this" opens on
# one, and "the wash itself is about two hours" does not ("the wash" is a subject and its noun is
# the verb).
AN_ARTICLE = frozenset("a an the".split())

# The verb is looked for in the first this many words of the piece, so a sentence that opens on a
# proper leading phrase ("in a hard-water area do it every couple of months") is read as a sentence
# about the answer's subject rather than as a step.
LEADING_PHRASE_MAX = 3


def _the_first_instruction_in_a_long_piece(head, verbs):
    """The first instruction out of a piece too long to hand over whole, else None.

    The answer stops telling the person to do something at the comma where it moves on to what
    will happen ("...and in about eight weeks you will run 20 minutes without stopping"), so the
    words above that comma are the step. Only when they read as an instruction of their own: a
    long piece is still passed over whole when what is above the first comma is not one.
    """
    piece = str(head or "").split(",")[0].strip(" ,;:.")
    words = piece.split()
    if len(words) < SHORT_STEP:
        return None
    if words[0].lower() in verbs or _a_verb_after_a_leading_phrase(piece, verbs):
        return piece
    return None


def _a_verb_after_a_leading_phrase(head, verbs):
    """True when the instruction's verb sits just after a phrase like "each week" or "half"."""
    tokens = [word.strip(" ,-").lower() for word in str(head or "").split()]
    for at in range(1, min(LEADING_PHRASE_MAX + 1, len(tokens))):
        if tokens[at] not in verbs:
            continue
        phrase = tokens[:at]
        if phrase[0] in AN_ARTICLE:
            continue
        if all(word in LEADING_PHRASE or word in AN_ARTICLE for word in phrase):
            return True
    return False


# Words that want a noun after them. A cut in front of one of these leaves the step hanging
# mid-phrase ("keep walking and carry"), so the cut lands after the phrase instead.
OPENERS = frozenset("with in into onto inside on at by from to for of under over through".split())

# Words a step cannot end on: a cut before one of these leaves the instruction without its
# ending ("clear the vents with a can of air and check what is"), so that cut is passed over and
# the next one taken, or the sentence is handed over whole.
DANGLING = frozenset("is are was were be been being am what that which who whom whose how why "
                     "the a an of to for and or but with in on at by from as it its this these "
                     "those his her their my your our there here than then so if even when while "
                     "because unless until plus yet".split())

# A piece of a sentence ends at a colon, a comma, a dash or a semicolon - anything that can put a
# second instruction beside the first. A comma inside a number is not a piece end: "earn more than
# 10,000 pounds a year" was cut at the comma, so the step handed back as the first thing to do
# stopped at "earn more than 10" and the figure was lost ("I would start here: ... earn more than
# 10."). A thousands separator is the one comma that never opens a second instruction.
PIECE_END = re.compile(r":\s|:|(?<!\d),(?!\d)| - |;| \u2014 ")

# A step never opens on the bot asking the person for something: "Tell me the figure you are saving
# towards" is the bot's own request, and handing it back as the thing to do told the person to
# answer their own question.
NOT_A_STEP = re.compile(r"^(?:tell|let|send|give|show|ask|name)\s+(?:me|us)\b", re.I)
# A menu is not the first thing to do: "Scones take 15 minutes, flapjacks 25, a Victoria sponge 40
# and banana bread an hour, so start with whichever time you have, and ripe bananas are the reason
# to make the last one" was handed over whole as the step, and the sentence that follows it is the
# one a person wants ("Weigh everything out before you start").
A_MENU = re.compile(r"\b(?:whichever|whatever|whenever|either|any of them)\b", re.I)

SENTENCE = re.compile(r"(?<=[.!?])\s+")
LEAD_SPLIT = re.compile(r"(?<=[.!?;])\s+")
# A quotation is one unit, whatever punctuation is inside it. An answer that shows the person what
# to write has a full stop and a question mark in it, and both sentence splitters above cut there:
# "Ask early, name the dates and say who covers: "Could I take 12-16 May off? I've arranged cover
# with Priya ..."" was handed back as "Shorter: Ask early, name the dates and say who covers:
# "Could I take 12-16 May off?" - a short answer that stops inside the quotation, and a second ask
# cut the other way, starting mid-quote with the closing mark left on it. A piece whose quotes do
# not pair up is the middle of a quotation, so it is never the short form on its own.
QUOTE_PAIRS = (("\"", "\""), ("\u201c", "\u201d"))
# The short form is a sentence or two, never a paragraph read out twice.
MOST = 240
LEAD_IN = 45

# The answer went unanswered for a turn or two at most.
LOOK_BACK = 3
# A request for less answered two or three times leaves hand-backs behind it, and those are
# skipped when looking for the answer: the window is wide enough to reach back past them to the
# answer they came from, so a fourth ask says there is nothing left instead of "nothing to cut".
LOOK_BACK_FOR_LESS = 6

# A line that opens on an auxiliary is asking something ("and is rice or pasta worse for me"),
# and a question about the thing in play has modules of its own: what was handed back to it was a
# sentence about packed lunches. The repeat's own QUESTION only knows the wh-words, because
# "what do i do" is the one it answers.
ASKS = re.compile(r"^\s*(?:and\s+|so\s+|ok(?:ay)?\s+|but\s+|well\s+|right\s+|also\s+)*"
                  r"(?:is|are|was|were|do|does|did|can|could|should|shall|would|will|"
                  r"have|has|had|am|may|might|must|any|anything|anyone)\b", re.I)

# A sentence where the bot asks the person something is not advice: "he cant stand coriander" was
# handed back "Tell me what is in the fridge and I will pick properly", which is the bot's own
# request said a second time.
ASKING_THEM = re.compile(r"\btell me\b|\blet me know\b|\bwhat(?:'s| is| have you)\b|"
                         r"\bsay which\b|\bwhat about\b", re.I)




# The bot has already said "that is the first step, work down the list" or "what I said above is
# the plan". Saying the answer again after that is the third time, and the chat has been pointed
# back once already. The composer's pointer says the rest of its answer follows from the step in
# its own words ("Ease off running first. The rest of what I said follows from that"), so the
# shapes it writes count here too, or the same paragraph comes back a third time.
REFER_BACK = re.compile(r"\b(?:the list i gave you|what i said (?:above|a moment ago)|"
                        r"down the list|first, then|i said (?:just )?now|same answer|"
                        r"you'?ve got it|that'?s the one|from just now|my answer above|"
                        r"the rest of what i said|the other things i said|first move|"
                        r"follows from (?:that|it)|comes after it)\b", re.I)


# A line that says "you" is asking about the bot itself ("what can you help with"), and the
# answer to that is never the thing the bot was just talking about.
ABOUT_THE_BOT = re.compile(r"\b(?:you|your|you'?re|u|ur)\b", re.I)


# "what should i say" asks for words to use, not for the steps again: the composer has a
# helper that puts the thing in words ("keep it to two sentences: what happened, then what you
# want"), and a repeat of the pay-rise advice takes the turn from it.
WORDS_WANTED = re.compile(r"\b(?:say|tell|write|phrase|word(?:ed|s)?|put\s+it|email|text|message|"
                          r"reply|respond|explain|ask\s+for|apologise)\b", re.I)




# A turn that added a detail to what we were already on, and got its own words back, has not
# moved the chat on. "we want to grow some veg this year" / "we only have a small patio" is the
# same thing twice, and the echo ("Got it - you only have a small patio") is the bot holding the
# detail, not answering it: "what should we start with" after that is still the first question.
# These are the words an echo puts round a line, so what is left of the two is what the person
# actually said.
ECHO_FRAME = frozenset("""got not right ok okay yes noted good to know remember that thats
    ill i you your youre its it and the a an of in on at for with so then anything like hand
    question theres there here me my""".split())
STALL = re.compile(r"\b(?:say more if it helps|go on|keep going|tell me the rest|"
                   r"i'?m with you|i'?m listening|i'?m here if you want|anything you'?d like a "
                   r"hand with|i'?ll remember that|noted|good to know|i'?ve got that|"
                   r"i'?ll keep that in mind)\b", re.I)


def only_said_it_back(line, said):
    """Whether the reply only says the person's own line back, so nothing has been answered.

    The words of the line that name something, less the ones a frame is built from, are nearly
    all in the reply: that is the line said back with a frame around it, which files a statement
    and answers nobody. It is here rather than in `_an_echo` because two readers need it and they
    must agree: the repeat guard below reads it a turn at a time, and the composer's want reader
    (`bot/compose/remark.py`, `a_want_said_back`) uses it to tell a receipt from an answer -
    "Got it — your son wants a tattoo." and "Your son is 16 and wants a motorbike. That explains
    it — no wonder it sits on you." are the same shape, and the shape is what decides it, not the
    frame either one happens to use.
    """
    said = str(said or "").strip()
    if not said:
        return False
    low = said.lower()
    spoken = [w for w in topics.words(str(line or ""))
              if w not in topics.STOPWORDS and w not in ECHO_FRAME and len(w) > 1]
    if not spoken:
        return False
    kept = sum(1 for w in spoken if w in low)
    return len(spoken) >= 2 and kept >= max(2, (len(spoken) * 3) // 4)


def _an_echo(turn):
    """The bot only said the person's own line back, or stalled, so nothing has been answered."""
    said = str(turn.get("bot") or "").strip()
    if only_said_it_back(turn.get("user") or "", said):
        return True
    return bool(said) and bool(STALL.search(said.lower()))


def _names_no_topic(turn):
    """The line was a detail, not a subject of its own: "we only have a small patio" is about the
    garden we are already on, while "my mother in law is coming on sunday" is a new thing."""
    line = str(turn.get("user") or "")
    if not line.strip():
        return False
    try:
        return not (understand(line, None).get("topics") or [])
    except Exception:
        return False


def _only_echoes_between(memory, back):
    """Whether every turn after an answer `back` turns ago was a detail said back, and no more.

    Both halves matter: the bot has to have only echoed the line or stalled, and the line has to
    have named no subject of its own. "we only have a small patio" after the veg answer is the
    same question again, but "my mother in law is coming on sunday" is a new thing, and the roast
    timing is not the answer to it.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    between = turns[len(turns) - back + 1:] if back > 1 else []
    return bool(between) and all(_an_echo(turn) and _names_no_topic(turn) for turn in between)


# "ok then", "alright then", "right then" is a nod that closes the turn, not a bare ask. The
# `then` made it read as "then what?", so the whole answer came back under a lead - "You've got
# it: Take paracetamol or ibuprofen at the dose on the pack and ring a dentist the same day" - to
# somebody who had just said ok. The other thirteen acks ("ok", "right", "cheers", "got it") all
# get a short close, and `then` is the only thing that separated this one from them.
JUST_A_NOD = re.compile(
    r"^\s*(?:ok|okay|alright|all right|right|fine|good|great|cool|cheers|ta|thanks|nice)"
    r"(?:\s+(?:then|thanks|cheers|mate|ok|okay|so))*[\s.,!?]*$", re.I)

# The shape of a bare ask for a way to help that has no question word to be read by: "is there
# anything i can do", "any way of making it easier", "anything that helps", "something that would
# help". The understanding engine reads these (`help_ask`, with the fences that keep a line naming
# a thing of its own out - "is there anything i can do about the mole on my back" is not one), and
# the gate below keeps that reading to the lines that could be one. "something" is the same ask
# said with the other word, and the gate was the only thing that knew only one of them: the engine
# had read "something that would help" as a help ask all along, and the gate turned it away, so a
# person who asked it after an answer got the answers module reading a search for it instead.
HELP_SHAPE = re.compile(
    r"\b(?:any\s?way|anything|something\s+(?:that|which|to)|is there|are there)\b", re.I)
# The same ask with the question in front. The understanding engine's reader knows one word order,
# "anything i can do"; "can i do anything about it" puts the question first and names nothing, and
# read as a statement it got the composer's shrug ("That's most of what I know on it") straight
# after a full answer about the rent - while the same line written "is there anything i can do" was
# handed the answer's own first step. Only the word order is missing, so it is read here, with the
# engine's own fence kept: a thing named after the ask ("...about the mole on my back") is not a
# bare ask for a way in.
HELP_ASK_QUESTION_FIRST = re.compile(
    r"\b(?:can|could|should|shall)\s+(?:i|we)\s+do\s+(?:anything|something)\b"
    r"|\bis\s+there\s+(?:anything|something)\s+(?:i|we)\s+"
    r"(?:can|could|should|might|would)\s+do\b", re.I)
NAMED_AFTER_IT = re.compile(r"\b(?:my|our|his|her|their|your|the|a|an)\s+[a-z]")


def _a_help_ask(text):
    """True when the whole line asks for a way to help and names nothing of its own.

    Three asks that read as one: "is there anything i can do", "any way of making it easier",
    "anything that helps". None of them opens on a question word, so `QUESTION` below never
    matched them and the line went on to be answered as a new question - "any way of making it
    easier" straight after the answer about a toddler who will not settle got "That's most of what
    I know on it", and "is there anything i can do" after the answer about waking at four got the
    same shrug. The person asked for the part of the answer to do, which is what `START_ASK`
    already reads when the line is written "where do i start".

    The reading is the understanding engine's, so its fences hold here too: a negation ("there
    isnt anything i can do"), a thing named after it ("...about the mole on my back") and a line
    that states rather than asks ("anything i can do is never enough") are other turns.
    """
    line = str(text or "")
    if not HELP_SHAPE.search(line):
        return False
    if HELP_ASK_QUESTION_FIRST.search(line) and not NAMED_AFTER_IT.search(line):
        return True
    if a_more_ask(line):
        # "anything else i can do", "anything else that helps": one more thing out of the answer
        # already given, which is `MORE_ASK`'s turn and its own reader's. Read as a help ask it
        # handed the first step of the answer back instead of the next one, so a person who had
        # been given "do not check the clock, keep the light off" asked for another and heard the
        # first one again.
        return False
    return bool(understand(line).get("help_ask"))


def asks_for_the_move(text):
    """True when the line asks which part of the answer in hand to do.

    A start ask ("where do i start", "what should i do first"), a help ask ("is there anything i
    can do") and a how ask with a pronoun in it ("how do i clean it off") are the same turn, so
    every reader that answers one of them answers all three.
    """
    line = str(text or "")
    return bool(says_where_to_start(line) or HOW_IT.search(line) or _a_help_ask(line))


def names_nothing(text):
    """True when the line asks for something without naming anything of its own."""
    if JUST_A_NOD.match(text or ""):
        return False
    lost = bool(AT_A_LOSS.search(text or ""))
    help_ask = _a_help_ask(text)
    if not (QUESTION.match((text or "").strip()) or lost or help_ask):
        return False
    if ABOUT_THE_BOT.search(text or ""):
        return False
    if WORDS_WANTED.search(text or ""):
        return False
    if topics.pairing(text or ""):
        return False
    if help_ask:
        # The engine read the whole line as the ask, and its fences are the ones that know the
        # words of one ("any way", "anything that helps", "is there anything"), so no word list
        # here has to be kept in step with them.
        return True
    return bool(topics.words(text)) and not _names_a_thing_of_its_own(text)


# "what do you think i should do first" asks for the move in the answer in hand and names nothing
# of its own; "think" is what the person wants done with the answer, not a subject. Everything
# else outside the ask's own frame is a thing named.
NOT_A_THING = frozenset((
    "think", "reckon", "want", "suppose", "guess", "even", "actually", "back", "again", "one",
    "ones", "thing", "things", "stuff", "lot", "bit", "kind", "sort", "way", "ways", "time",
    "times", "people", "anyone", "someone", "everything", "anything", "something", "nothing"))


def _names_a_thing_of_its_own(text):
    """The content words of the line that name something, in the ask's own frame left out.

    This is the reading behind `names_nothing`, kept separate because the start asks need the
    same test without the fences around it: "my laptop keeps dropping the wifi in the back room,
    what should i try first" names a laptop, a wifi and a back room, so it is a question about
    those and not a question about the answer just given.
    """
    lost = bool(AT_A_LOSS.search(text or ""))
    said = ASK | ASK_VERB | TIME | FILLER | NOT_A_THING
    if lost:
        said = said | LOSS_WORDS
    return [word for word in topics.words(text or "")
            if len(word) > 2 and word not in said and word not in SELF
            and not word.isdigit() and word not in topics.STOPWORDS]


# A step verb acts on the answer just given rather than naming a subject of its own: "what should
# i delete first" is about the answer on the screen, and the answer's own move is the reply.
# A move a sentence only makes under a condition is not the first thing to do now: "If you get
# them most days, keep a short diary of sleep" is what to do about a pattern, not about the
# headache the person has this afternoon.
CONDITION_CLAUSE = re.compile(r"^\s*(?:if|unless|when|whenever|once|in case|should|as long as)\b",
                              re.I)
# A referral is not a move either: "ask a GP: they can check your bloods" ends a health answer and
# was handed back as the first thing to do for the trouble the person named that turn.
NOT_A_MOVE = re.compile(
    r"^(?:ask|ring|call|see|phone|speak to|talk to|book|visit|check)\b[^.!?]{0,30}\b"
    r"(?:gp|doctor|doctors|dentist|nurse|pharmacist|chemist|optician|vets?|hospital|ae|"
    r"a&e|plumber|electrician|engineer|specialist)\b", re.I)

STEP_VERBS = frozenset("delete remove clear keep pick choose check replace".split())

# The words that make a line ask which of several steps comes before the others.
ORDER = re.compile(r"\b(?:first|next|then|before|after that)\b", re.I)


def asks_to_put_it_right(text):
    """True when the line asks whether the thing on the table can still be put right.

    "can i save it", "is it ruined", "can it be fixed": the thing is the one the answer just
    gave, so nothing about the line is new - it is a question about that answer, and the answer's
    own first move is what it wants. A line that names a subject or a goal of its own ("can i save
    money on my heating", "can i fix my bike") is a question of its own and keeps it.
    """
    line = str(text or "").strip()
    if not PUT_RIGHT.search(line) or not PUT_RIGHT_ASK.match(line):
        return False
    if topics.pairing(line) or ABOUT_THE_BOT.search(line):
        return False
    words = [w for w in topics.words(line) if w not in ASK and w not in FILLER
             and not w.isdigit() and w not in SELF and w not in PUT_RIGHT_WORDS
             and w not in topics.STOPWORDS]
    return not words


def a_step_of_the_same_answer(text):
    """True when the line asks which of the answer's own steps to do first.

    "what should i delete first" after the Mac storage answer carries one content word, and that
    word ("delete") acts on the answer rather than naming a subject of its own, so the answer on
    the screen still answers it. A line that names a thing ("how do i delete a file") is a
    question of its own and keeps it.
    """
    if not ORDER.search(text or "") or not MOVE_ASK.search(text or ""):
        return False
    if topics.pairing(text or "") or ABOUT_THE_BOT.search(text or ""):
        return False
    words = [w for w in topics.words(text) if w not in ASK and w not in FILLER
             and not w.isdigit() and w not in topics.STOPWORDS]
    return bool(words) and set(words) <= STEP_VERBS


def _recent_answers(memory):
    """The bot's own answers in the recent past, newest first, each with the line it answered and
    how many turns ago it was (1 is the turn just before this one)."""
    out = []
    seen_a_card = False
    for back, turn in enumerate(reversed((memory.get("turns") or [])[-LOOK_BACK:]), 1):
        if not isinstance(turn, dict):
            break
        # Only an answer is worth saying again. A stock line, an echo of their own words, a
        # refusal or an emergency reply is not: "what would you do" after "Thanks for telling
        # me - I'm here if you want to dig into any of that" must not be handed that line back.
        if turn.get("module") not in ANSWER_MODULES:
            continue
        said = str(turn.get("bot") or "").strip()
        if not said or HEDGE.search(said) or len(said) < 50:
            continue
        # The store answers some lines with an entry's own words - a swap that keeps the ask, a
        # condition added to a choice - and those are answers to hand back. Its own short lines
        # ("Got it - the front room.") are not, so the length is what tells the two apart: without
        # this, the paragraph after a corrected line was invisible and a follow-up was handed the
        # answer from two turns back instead of the one just given.
        if len(said) < A_STORE_ANSWER and turn.get("module") != "answers":
            continue
        # The bot asking a question is not an answer to hand back: "what would you do?" after
        # "is there one thing that would help?" wants an answer, not the question again.
        if said.rstrip().endswith("?") or QUESTION.match(said):
            continue
        # A trip they have changed moves the answer with it: the weather, the cost and what to
        # see are facts about a place, so an answer about Rome is not the answer to a question
        # about Cornwall ("im off to cornwall next week" / "what should i do there" was handed
        # the Rome weather sentence).
        if topics.about_a_place_they_left_behind(said, memory):
            continue
        out.append((back, str(turn.get("user") or ""), said))
    return out


def _the_answer_about_what_we_are_on(memory, recent):
    """The recent answers that can be handed back, newest first, with the topic in hand first.

    The newest answer is the answer to a follow-up that names nothing of its own, which is right
    while the chat is still on it. Going back to an earlier topic is the case where it is not:
    the conversation is on the boiler again, and the newest answer is about the school places the
    line between them brought up. The store has already made the returned topic current, so an
    answer about some *other* subject is not the answer in hand, and the answer to the topic we
    are on is the one to draw on:

        my boiler keeps losing pressure
        my daughter is 6 and starts school in september
        anyway back to the boiler      -> "Back to the boiler, then. What did you want to know
                                          about it?"
        what should i do first         -> "The thing to do first: Apply through your council by
                                          15 January ..."   (the school places)

    Only answers about the topic in hand are offered when the newest one is about something else;
    when the newest answer *is* about the topic in hand the list is left exactly as it was, so
    every other chat reads as before. The order of the answers about the topic in hand is kept,
    so the newest of those is still tried first, and the guards in `answer_for` still decide
    whether it may be handed back at all.
    """
    here = topics.current(memory)
    # The topic's own words carry what the lines since have added to it ("should i switch" adds
    # `switch` to the broadband), so they are read with the keywords of the line that opened it.
    # Without them the answer to a follow-up that used the topic's own word was not recognised as
    # being about it, and an older answer took its place: "my broadband is 45 a month is that a
    # lot" / "should i switch" (the cancel steps) / "how do i cancel it" was handed the verdict on
    # the £45 instead of the steps to cancel.
    mine = {word for word in topics.keywords(str((here or {}).get("text") or ""))}
    mine |= {str(word).lower() for word in ((here or {}).get("words") or ())}
    if not recent or not mine:
        return recent
    # The newest answer is the answer in hand when it is about the topic, and an answer is what
    # the bot said, not only what the person said: "my broadband is 45 a month is that a lot" /
    # "should i switch" gets the cancel steps, and the "how do i cancel it" after it belongs to
    # that answer even though the line between them never said "broadband". Without the bot's own
    # words, the answer about the person's *line* two turns back wins over the answer about the
    # thing they are asking about now.
    if mine & set(topics.keywords(recent[0][1])) or mine & set(topics.keywords(recent[0][2])):
        return recent
    about_it = [item for item in recent if mine & set(topics.keywords(item[1]))]
    return about_it or recent


def _nothing_but_acknowledgements(back, memory):
    """Nothing has answered since that answer: only acknowledgements of the person's own line.

    "my back hurts" -> the answer, "ive tried stretching" -> "Got it - you've tried stretching",
    "what else can i do": the answer is still the last thing said about it, so a follow-up that
    names nothing of its own is about that answer. A real answer in between (cooking, money)
    means the chat has moved and the older paragraph is not what the line leans on.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if back <= 1 or back > len(turns):
        return True
    for turn in turns[len(turns) - back + 1:]:
        if turn.get("module") == "answers":
            return False
        line = str(turn.get("user") or "")
        if len(line.split()) > 6 and not ATTEMPT.search(line):
            return False
    return True


def _about_the_same_thing(asked, said, memory):
    """The answer belongs to what the chat is still on, not to a subject that has moved."""
    # A line the bot had no answer to does not move the chat on. "i eat takeaway three times a
    # week" was met with "Got it. Is there anything you'd like a hand with?", and the ask for the
    # first move after it is still about the answer two turns back - the bot never answered the
    # detail, so it cannot have left the subject. Without this the ask went to nobody and the
    # person who had just been told what to do about their tiredness got a search hedge.
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if turns and HEDGE.search(str(turns[-1].get("bot") or "")):
        return True
    subject = [w for w in topics.words(topics.subject(memory) or "")
               if w not in topics.STOPWORDS]
    if not subject:
        return True
    # An answer that does not use one word of the line it answered is not an answer about that
    # line, whatever subject that line was on: the knowledge base reached a cheap-food answer for
    # "were redoing our bathroom on a budget", and two turns later the ask for what to spend on
    # first was handed a food step under "I would start here", out of an answer made of rice and
    # lentils. The older turn's own question is about its own subject by construction, so it is
    # the answer's words that decide this, not the question's.
    theirs = {w for w in topics.words(asked) if len(w) > 2 and w not in topics.STOPWORDS}
    mine = {w for w in topics.words(said) if len(w) > 2 and w not in topics.STOPWORDS}
    # The entries behind the answer count as the answer's words. A card written for the person's
    # own words never says them back: "i have slugs everywhere" is answered with "Go out after dark
    # with a torch and pick them off ... copper tape round pots", where slugs are only "them", so
    # the answer looked like one that had nothing to do with the line it answered, and the chat
    # was declared to have moved on after one turn. The entry behind it is keyed on slugs, and the
    # ask that follows is still about that card.
    mine = mine | {w for w in _the_keys_of(said, memory) if len(w) > 2}
    if theirs and not (mine & theirs):
        return False
    broken = set(topics.words(asked)) | set(topics.words(said))
    if broken & set(subject):
        return True
    # A line that reports having a go at the answer ("ive tried stretching") is a line about that
    # answer, even though the word it reports is the word the chat is now on. Without this the
    # attempt in between hid the answer and the next ask got a search instead of the next step.
    mine = {w for w in topics.words(said) if len(w) > 2 and w not in topics.STOPWORDS}
    for turn in (memory.get("turns") or [])[-3:]:
        if not isinstance(turn, dict):
            continue
        line = str(turn.get("user") or "")
        if not ATTEMPT.search(line):
            continue
        if len(mine & {w for w in topics.words(line) if len(w) > 2}) >= 2:
            return True
    return False


def _the_chat_is_still_on(said_before, memory):
    """Whether the thing the chat is on now is still the thing this older answer was about.

    `_about_the_same_thing` asks an older answer whether it is about the line it answered, and a
    knowledge answer is about its own question by construction, so that reading cannot see a
    subject that came in between. "ive started running three times a week" / "i want to lose a
    stone" / "how long will it take" was answered "20 to 30 minutes" - the length of the runs,
    from the answer two turns back - because the only thing the reader compared was the running
    question with the running answer. The line the chat is on says which thing the person is
    asking about now, so a figure said about something else is not handed back.
    """
    topic = memory.get("topic") if isinstance(memory, dict) else None
    now = {w for w in topics.words(str((topic or {}).get("text") or ""))
           if len(w) > 2 and w not in topics.STOPWORDS}
    if not now:
        return True
    then = {w for w in topics.words(said_before) if len(w) > 2 and w not in topics.STOPWORDS}
    return bool(then & now)


def _short(said):
    """The answer the way a friend repeats it: its first sentence, or two when the first is only
    a lead-in, and never more than MOST characters."""
    parts = [p.strip() for p in SENTENCE.split(said.strip()) if p.strip()]
    if not parts:
        return ""
    short = parts[0]
    if len(short) < LEAD_IN and len(parts) > 1:
        short = short + " " + parts[1]
    if len(short) > MOST:
        short = short[:MOST].rsplit(" ", 1)[0].rstrip(",;:") + "..."
    return short


# A knowledge answer sometimes says which of its own pieces is the move: "Half an hour earlier to
# bed, and the same wake-up time every day, is the first thing to change". The sentence names the
# move itself, so the part in front of the "is" is the thing to hand back, in their own words.
FIRST_THING = re.compile(
    r"^(?P<move>.{4,120}?)\s+is\s+(?:the|your|my)\s+(?:first thing|thing to do first|"
    r"best first (?:step|move)|first (?:step|move)|best (?:step|move)|place to start|"
    r"one thing|fix|change|main thing|thing that helps|bit that helps|part that matters)", re.I)


# The prepositions that follow a noun and never an instruction: "water at the front" is about
# water, though `water` is a verb in the list, and handing that back says the diagnosis is the
# step to take. A heading that weighs one way of doing it against another is not the move itself: the thing it
# is weighing in favour of is what follows the colon ("Test yourself instead of rereading: cover
# the page, say or write what you remember").
_WEIGHS_ONE_AGAINST = re.compile(r"\s(?:rather than|instead of)\s", re.I)

# The prepositions that follow a noun and never an instruction: "water at the front" is about
# water, though `water` is a verb in the list, and handing that back says the diagnosis is the
# step to take. "Stop the cycle", "check the hose", "turn it off" are the shape of an instruction.
_AFTER_A_NOUN = frozenset("at in on from of for to with by near under behind over into about".split())


# A sentence that opens on a subject pronoun and runs on is saying how something is, and no
# clause of it is an instruction. The tell is the subject in front of the verb: an instruction has
# none, so a verb-shaped word that has one is the sentence's subject ("water goes in at the mouth"
# is a statement, and "water" is what you do to a plant).
_SUBJECT_OPEN = re.compile(r"^(?:they|it|it's|its|he|he's|she|she's|this|that|that's|these|those"
                           r"|there|there's|we|we're)\b", re.I)
# What a heading in front of a colon may be. Longer than this is a sentence, not a heading.
_EXPLANATION_WORDS = 5


def _explains(sentence):
    """True for a sentence that says how something is, so holds no step of its own."""
    text = str(sentence or "").strip()
    if not _SUBJECT_OPEN.match(text):
        return False
    head = re.split(r":|,|;| - | \u2014 ", text, 1)[0]
    return len(head.split()) > _EXPLANATION_WORDS


def _a_step_comes_after(part):
    """Whether the sentence that explains a fault ends on the step ("..., so clear the vents").

    `_explains` caps a description at its first clause and treats the rest of the sentence as more
    description. A sentence that closes on "so <verb>" is different: everything after the "so" is
    what to do, and skipping it lost the step of answers like "It is cooling itself because it is
    hot, so clear the vents with a can of air".
    """
    text = str(part or "")
    for match in _SO_THE_STEP_FOLLOWS.finditer(text):
        if _opens_an_instruction(text[match.end():]):
            return True
    return False


def _opens_an_instruction(text):
    """Whether a piece of an answer opens on a verb an instruction can open on."""
    from ..compose.verdict import IMPERATIVES

    words = text.strip(" ,.:;").split()
    # "Blot, don't rub" is the same instruction as "Blot": the comma belongs to the sentence, not
    # to the word.
    return bool(words) and words[0].lower().strip(" ,.;:") in IMPERATIVES


# A step cut at its own ", then" must not end on one of these: "ask once, plainly, and" is half a
# sentence, and the half it lost was the instruction.
_HANGS = frozenset("and or but then with to of the a an in on at for is are that this".split())

# What follows the comma in "Blot, don't rub": the answer going on with the same instruction by
# saying what not to do. A negation is an instruction even though it opens on a word that is not
# a verb in the list.
_NEGATES = re.compile(r"^(?:do not|don't|dont|never|avoid)\b", re.I)

# The step often comes as the conclusion of the sentence that explains the fault: "It is cooling
# itself because it is hot, so clear the vents with a can of air". The joining word holds the
# sentence together and is not part of the step, but it is where the step starts, so a reader that
# only opens on a verb walked past it and handed the cause back instead of what to do.
_SO_COMES_THE_STEP = re.compile(r"^(?:and\s+|but\s+)?so\b[,\s]+", re.I)
# The same word in the middle of the sentence, after the part that explains it.
_SO_THE_STEP_FOLLOWS = re.compile(r"[,;]\s*(?:and\s+)?so\b[,\s]+", re.I)
# "so do holidays" is not an instruction: it is agreement with what the sentence just said
# ("Days and months take a capital - so do holidays"). `do` is a verb an instruction can open on
# and the words after it are the subject of the agreement, so the two are told apart by what comes
# after the verb: an instruction names what to do ("do that first", "do the washing", "do both").
_SO_DOES_NOT_ASK_SOMETHING_OF_THEM = re.compile(
    r"^do(?:es)?\b(?!\s+(?:it|that|this|these|those|them|the|a|an|your|my|his|her|their|our|both"
    r"|one|all|more|less|as|so)\b)", re.I)




def _opening_move(part):
    """The instruction a sentence opens with, in the answer's own words, or None.

    Only the start of the sentence counts: an instruction opens on its verb, and a word further
    in is the thing it is about: "Stop the cycle, unplug it and turn the water off" opens on the
    instruction, and "Water at the front is usually the door seal" is about water, though `water`
    is also a verb in the list. A sentence that opens on a fact and then says what to do ("A
    dripping tap is nearly always a worn washer: turn the water off at the valve") hands back what
    follows its colon, and the whole of it, because the steps are the answer.

    A sentence that leads with the plan ("Start with run-walk: one minute of easy jogging") hands
    back what follows its colon too: the lead is the verb, and reading the lead as the move would
    hand back "start with run-walk" and say start twice.
    """
    from ..compose.verdict import IMPERATIVES  # the verbs an instruction can open on

    # A step is often wrapped in one long sentence: "Pack what you use least first - books, spare
    # bedding, the cupboard under the stairs - and keep a 'first night' box out of the van: kettle,
    # mugs, chargers, loo roll, bedding and a change of clothes" is 37 words and it is one step.
    # Handed back whole it is a paragraph said aloud, and the asides are the reason it took two
    # goes to say: the piece before the first dash is the step, and it is read first when it is
    # itself a short sentence. A dash inside a longer instruction ("Stop the cycle, unplug it and
    # turn the water off - the fuse stays live") costs nothing, because the lead is the step.
    lead = re.split(r"\s+[-\u2014]\s+", str(part).strip())[0]
    if lead.strip() and lead.strip() != str(part).strip() and len(lead.split()) <= 12:
        found = _opening_move(lead)
        if found:
            return found

    leads_with_the_plan = bool(re.match(r"(?:start|begin) with\b", part.strip(), re.I))
    pieces = [part] + part.split(":")
    # A sentence that opens on a subject pronoun and runs on is explaining something, so what
    # follows its colon is the rest of the explanation and not a step: "They take oxygen out of
    # the water instead of the air: water goes in at the mouth, passes over the gills" is how a
    # fish breathes, and its tail read on its own is the instruction "Water goes in at the
    # mouth" - what a person asking what to do about a goldfish lying on the bottom of the tank
    # was told to do. A short piece in front of the colon is still a heading ("That's the one:
    # split your time in three"), so the cap keeps those.
    explaining = _explains(part)
    for index, piece in enumerate(pieces):
        if index and explaining:
            continue
        head = _SO_COMES_THE_STEP.sub("", piece.strip(" ,.:;"))
        if topics.RED_FLAG.match(head):
            continue  # a warning is not a move, and handing it back alone scares the person
        words = head.split()
        if not 3 <= len(words) <= 40:
            continue
        # "Blot, don't rub, then dab a little hand sanitiser" is one instruction whose verb the
        # comma sticks to, and reading the word with its comma in it missed the verb and walked
        # on to the next sentence, so "what should i do first" was answered with the second thing
        # in the answer ("rinse with cold water and wash") rather than the first. The comma only
        # comes off when what follows it is another instruction, so a list of nouns that happens
        # to open on a verb word keeps its guard: "Sleep, water and an antihistamine" is one
        # thing among others, not the step.
        first = words[0].lower().strip(" ,.;:")
        if first != words[0].lower() and not _opens_an_instruction(" ".join(words[1:])) \
                and not _NEGATES.match(" ".join(words[1:])):
            # A comma comes off the verb only when the answer goes on with another instruction
            # ("Blot, don't rub"): "water, squash and milk all count" and "dry, gritty eyes are
            # usually the tear film" also open on a word the verb list holds, and reading those
            # as the step handed back a list and a description.
            continue
        if first not in IMPERATIVES:
            # The verb of a "start with X: <steps>" sentence is its lead, so the steps after its
            # colon are instructions even though they open on a measure ("one minute of easy
            # jogging") rather than on a verb.
            if not (leads_with_the_plan and index > 1):
                continue
        elif words[1].lower().strip(" ,.;:") in _AFTER_A_NOUN:
            continue  # "water at the front": a noun the imperative list happens to hold
        elif re.match(r"(?:start|begin) with\b", head, re.I) and ":" in part:
            continue  # the lead itself; what it leads to is the next piece
        elif (_WEIGHS_ONE_AGAINST.search(head) and index + 1 < len(pieces)
              and _opens_an_instruction(pieces[index + 1])):
            # "Test yourself instead of rereading: cover the page" weighs one way against
            # another, so it is a heading and not the move; what follows the colon is. The
            # contrast has to be the whole of the heading for that to hold: in "keep walking ...
            # rather than taking to your bed, and take paracetamol" the contrast is inside the
            # instruction, and the instruction is what is handed back.
            continue
        # "book a GP appointment rather than keep taking painkillers" is one instruction with a
        # contrast on the end; the step is what is in front of the "rather than", and handing the
        # contrast back reads as two steps run together.
        head = re.split(r"\s+rather than\b", head)[0].strip(" ,;:-")
        if len(head.split()) < 2 or topics.RED_FLAG.match(head):
            continue
        # The sentence may carry the step and then the rest of the routine after a ", then " or a
        # semicolon ("Blot, don't rub, then dab a little hand sanitiser into the mark with a cotton
        # bud and blot again"). Sentence splitting cannot see that boundary, so the first step is
        # handed back on its own and the rest of the routine is left where it is - a friend says
        # the first thing once.
        if ":" not in head and ", then " in head:
            # One step and then the next: "Blot, don't rub, then dab a little hand sanitiser into
            # the mark with a cotton bud and blot again" hands back two moves in one line, and a
            # person asked for the first. Only a short lead is cut, and only before ", then": a
            # colon holds the instruction it introduces ("check the obvious one first: signal,
            # then mobile data off for ten seconds" lost the part that fixes it when it was cut
            # there), and a semicolon joins two statements as often as two steps ("water doesn't
            # help; a little sugar and lemon balances the chilli" is not a step when its first
            # half is read alone).
            shorter = head.split(", then ")[0].strip(" ,;:-")
            if (3 <= len(shorter.split()) <= 8 and _opens_an_instruction(shorter)
                    and shorter.split()[-1].lower() not in _HANGS):
                head = shorter
        return head[0].lower() + head[1:]
    return None


def _a_question(said):
    """Whether the sentence asks rather than tells.

    The bot's own question is not a step: a wish to write a book is answered with "tell me what
    you last enjoyed and I'll narrow it down", and handing that back as "Start with this: Tell me
    what you last enjoyed" is the bot asking the person its own question as if it were advice.
    A step never opens on an interrogative, and "do the theory test early" starts on a verb, so
    verbs are not in the list.
    """
    text = str(said or "").strip()
    if text.endswith("?"):
        return True
    return bool(QUESTIONS_THAT_ARE_NOT_STEPS.match(text))


def _a_move(said, questions_are_steps=False):
    """The move in the answer, when it is a move and not the answer with a lead on it.

    A move is one thing to do: "Stop the cycle and turn the water off". `_a_move_in` reads the
    answer for the sentence that says what to do, and on an answer whose opening sentence says
    what to do and how, all season and at what pace, it hands back thirty-five words of it. Said
    under a lead ("That's the one: start where you can already run 5km comfortably and build up
    over about sixteen weeks: three runs a week (one long, two short and easy)...") that is the
    answer again with two words in front of it, and the ask that gets it is the one the answer
    already answered. Past a step's length there is no one thing to do, so this reader stands
    down and the answer comes back as the repeat it is.
    """
    move = _a_move_in(said, questions_are_steps=questions_are_steps)
    if move and len(move.split()) > STEP_WITH_ITS_METHOD:
        return None
    return move


def _a_move_in(said, questions_are_steps=False):
    """The sentence of the answer that tells them what to do, or None.

    `questions_are_steps` is for the reader that hands back what still stands of an answer the
    person has just ruled part of out (`bot/memory/obstacle.py`): the bot's own question is part
    of what stands ("Then skip black pepper - the rest of it stands: tell me what is in the fridge
    and I will pick properly"), where as the first thing to do it is the bot asking itself.

    A knowledge answer either opens with what to do ("Stop the cycle, unplug it and turn the
    water off") or opens with what is true and ends with what to do ("Most bad posture is the
    chair and the sitting still: set the screen so the top of it is at eye level"). The opening
    sentence wins when it is an instruction: it is the first step, and the step is what was asked
    for. Only when the answer opens on a fact is the last instruction the move.
    """
    parts = [p.strip() for p in SENTENCE.split(str(said).strip()) if p.strip()]
    if parts:
        opening = _opening_move(parts[0])
        if opening and (questions_are_steps or not _a_question(opening)):
            return opening
    for part in reversed(parts):
        # A red flag is not a move. A health answer ends with the warning ("Get it looked at if it
        # gives way"), so walking the sentences backwards found the warning first, and a person
        # who has just been told to ice it was met with the A&E sentence alone. The skip is the
        # one `topics` uses for the same reason, so the two paths cannot drift.
        if topics.RED_FLAG.match(part):
            continue
        named = FIRST_THING.match(part)
        if named:
            move = named.group("move").strip(" ,;:")
            if (2 <= len(move.split()) <= 20 and not topics.RED_FLAG.match(move)
                    and (questions_are_steps or not _a_question(move))):
                return move[0].lower() + move[1:]
        head = _opening_move(part)
        if (head and not CONDITION_CLAUSE.match(head) and not NOT_A_MOVE.match(head)
                and (questions_are_steps or not _a_question(head))):
            return head

        if _explains(part) and not _a_step_comes_after(part):
            # The sentence explains how something is, and every clause of it is part of the
            # explanation: a verb-shaped first word in one of them is that clause's subject, not
            # a move ("water goes in at the mouth" is not something to do). The one exception is
            # the conclusion: a sentence that ends "..., so clear the vents" explains nothing
            # after its "so", it tells them what to do.
            continue

        for piece in [part] + part.split(":"):
            # A step is often the second clause of a sentence whose first clause names where to do
            # it: "On a Mac: ... Storage, click the bar and let it finish scanning ... Empty the
            # Bin, clear the Downloads folder". Walking only the first clause of each sentence
            # found no move in a reply made of them, so "what should i delete first" after the
            # storage answer had nothing to hand back.
            from ..compose.verdict import IMPERATIVES  # the verbs an instruction can open on
            # A comma between two digits is a thousands separator, not a clause: "Aim for 10%
            # of the price: £20,000 on a £200,000 home" was cut at the comma inside the number,
            # and the step handed back said "Aim for 10% of the price: £20" - a wrong figure
            # under a lead that presents it as the answer's own words.
            clauses = re.split(r"(?<!\d),(?!\d)| - |;| \u2014 |\. ", piece)
            conditional = False
            # How deep inside a bracket the last clause left the sentence. A comma inside
            # brackets is not a clause boundary: "(weather, air traffic control, a security
            # alert)" was cut at its commas and "air traffic control" was handed back as the
            # step, and "wash cool (30C, or 20C for anything with stretch)" was cut to "wash cool
            # (30C". A clause that opens inside a bracket is part of the aside, not a step.
            in_a_bracket = 0
            for clause in clauses:
                head = clause.strip(" .:;")
                if not head:
                    continue
                opened_inside = in_a_bracket > 0
                in_a_bracket = max(0, in_a_bracket + head.count("(") - head.count(")"))
                if opened_inside:
                    continue
                # "... so clear the vents" is the first clause that starts on the step, and the
                # joining word is not part of it. A conclusion is delimited by the sentence's own
                # comma, so it is a whole step however long the explanation in front of it was.
                a_conclusion = bool(_SO_COMES_THE_STEP.match(head))
                head = _SO_COMES_THE_STEP.sub("", head)
                if not head:
                    continue
                if head.count("(") != head.count(")"):
                    # The other half of the same bracket: the clause after the aside ends on a
                    # ")" and what is left reads as a step when it is the tail of one.
                    continue
                if a_conclusion and _SO_DOES_NOT_ASK_SOMETHING_OF_THEM.match(head):
                    continue
                if CONDITION_CLAUSE.match(head):
                    # The rest of this sentence is what to do in that case, not now.
                    conditional = True
                    continue
                if conditional:
                    continue
                if topics.RED_FLAG.match(head):
                    continue
                if NOT_A_MOVE.match(head):
                    # A referral ends a health answer; it is not the first thing to do.
                    continue
                words = head.split()
                if not 2 <= len(words) <= (STEP_WITH_ITS_METHOD if a_conclusion else 14):
                    continue
                if words[0].lower() not in IMPERATIVES:
                    continue
                if not questions_are_steps and _a_question(head):
                    # "tell me what you last enjoyed and I'll narrow it down" is the bot's own
                    # question: "tell" is an instruction and the sentence is not one.
                    continue
                break
            else:
                continue
            # "Start with run-walk: one minute of easy jogging" already leads; a lead in front of
            # it says start twice, so that sentence is the answer's opening, not a move.
            if re.match(r"(?:start|begin) with\b", head, re.I) and ":" in part:
                continue
            return head[0].lower() + head[1:]

    return None


# A condition that puts the decision on them - "if that sounds fine", "if you can live with
# that", "if you are happy with it" - is the choice itself, not a moment the step waits for.
_A_JUDGEMENT = re.compile(
    r"^\s*(?:when|once|if|as soon as|next time)\b[^,]{0,60}?\b(?:sounds?|feels?|you'?re happy|"
    r"you are happy|you can live with|you'?re ok(?:ay)? with|you are ok(?:ay)? with)\b", re.I)


def _a_conditional_move(said):
    """The answer's step that comes wrapped in its own condition, kept whole, or None.

    An answer often puts the step behind the moment to do it: "When you're ready, ask for one
    line of feedback", "Once it has cooled, press it flat". `_a_move` reads that condition and
    stops, because a step for later is not the step to do first - which is right for "what
    should i do first" and wrong for the person who says they do not know what to do at all:
    there, the conditional step is the one thing the answer has to give them, and repeating the
    answer's opening sentence ("That's disappointing, especially after an interview") says
    nothing they can do. The condition is kept, so the step is not handed over as if it were
    for now.
    """
    parts = [p.strip() for p in SENTENCE.split(str(said).strip()) if p.strip()]
    for part in parts:
        if topics.RED_FLAG.match(part) or NOT_A_MOVE.match(part):
            continue  # a warning or a referral is not a step, whatever it is wrapped in
        match = CONDITION_CLAUSE.match(part)
        if not match:
            continue
        # The dash-clause after a step is why it is done, and a bracket after it is the aside
        # that says the same in different words ("ask for one line of feedback (was there
        # anything I could strengthen?)"): neither is more of the step, and both made a short
        # step too long to be handed back.
        step = re.split(r"\s+[-\u2014]\s+|\s+\(", part.strip())[0].strip(" ,.;:")
        # The condition runs to its comma - "When you're ready, ..." - and the step is what
        # follows it; without a comma the whole clause is one word ("Once cooked, ...") and the
        # step starts after it.
        after = step.split(",", 1)
        rest = (after[1] if len(after) > 1 else step[match.end():]).strip(" ,")
        if not 3 <= len(rest.split()) <= 14:
            continue  # a two-word step is a shrug, not the thing to do
        if not _opens_an_instruction(rest):
            continue  # the condition leads into a fact, not an instruction
        if _A_JUDGEMENT.match(step):
            # "If that sounds fine rather than like a sacrifice, get one" weighs their life up
            # and its step is the decision itself: handed back alone it tells a person at a loss
            # to make up their mind, which is the thing they said they cannot do.
            continue
        if not 4 <= len(step.split()) <= 24:
            continue
        if _explains(step):
            continue
        return step[0].lower() + step[1:]
    return None


def asks_for_more(text):
    """Whether the line asks for the next part of the answer in hand, and says nothing else.

    "what else", "anything else", "and after that" - four words at most, because a line that says
    what it is about ("what else can i do about my nails") has a subject of its own for the
    entries to match. `names_nothing` reads "anything else" as naming something, so this ask needs
    a reading of its own.
    """
    if len(re.findall(r"[a-z']+", str(text or "").lower())) > 4:
        return False
    return bool(NEXT_ASK.search(str(text or "")))


def a_hand_back(said, memory):
    """Whether this bot line was handed back out of an earlier answer rather than being one.

    A step is a clause of the answer it came from, so a turn that holds one is not the answer: what
    to do with "what else" after it is the answer behind it, which `_handed_back` kept. Read off
    what was handed back rather than off a list of lead-ins, so a frame added later is one of these
    too.
    """
    wanted = str(said or "").strip().lower()[:60]
    if not wanted:
        return False
    return any(wanted in str(line or "").lower() for line in (memory.get("repeated") or []))


def _handed_back_last(memory):
    """Whether the bot's last turn was a short form handed back out of an earlier answer."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return False
    return a_hand_back(turns[-1].get("bot"), memory)


def _another_part(said, memory):
    """The next part of the answer in hand and whether it says what to do, else ("", False).

    The answer is walked in order, so "what else" after a step gets the part after the step rather
    than the step again or the whole paragraph. A red flag is not a next step ("Get it looked at
    if it gives way" is what to do in an emergency, not the next thing to try) and neither is a
    sentence that asks the person for something, so both are skipped. A sentence that tells them
    to do something wins over one that only explains, because "what else" asks for the next move -
    but an answer of nothing but explanation still has more in it, so the first part is the
    fallback and the caller says which of the two it got.
    """
    spare = ""
    for part in (p.strip() for p in SENTENCE.split(str(said).strip())):
        part = part.rstrip(" .")
        if len(part.split()) < 4 or len(part) > MOST:
            continue
        if topics.RED_FLAG.match(part) or ASKING_THEM.search(part):
            continue
        if _already_repeated(part, memory):
            continue
        # The lead already says where the part comes from, so a part that opens on a connective
        # reads as one said twice: "After that: Then ask for a specific figure" is "then" twice.
        part = re.sub(r"^(?:and\s+|but\s+|so\s+|then\s+|after\s+that,?\s+|next,?\s+)", "",
                      part, flags=re.I)
        part = re.sub(r"^then\s+", "", part, flags=re.I)
        if len(part) > 110:
            # A sentence that carries its examples in a list after a colon says what to do before
            # it: "Notice the moment you start, and give that hand something else to do: a ring to
            # twist, a pen, a stress ball." The next part is the doing, not the shopping list.
            head = part.split(": ")[0].strip(" ,;")
            if len(head.split()) >= 4:
                # The list under the colon may be further along than the lead-in. The answer gives
                # "Change a few things you can keep doing rather than going on a diet: fill half
                # the plate with vegetables, put protein in every meal ...", and once the first
                # clause of that list has been handed over, the next part is the clause after it -
                # not the lead-in again ("After that: Change a few things you can keep doing rather
                # than going on a diet"), which is a heading read out as a step.
                under = [one.strip(" ,;:") for one in re.split(r",\s+", part.split(": ", 1)[1])]
                under = [one for one in under if one]
                if under and _already_repeated(under[0], memory):
                    for clause in under[1:]:
                        if _says_what_to_do(clause) and not _already_repeated(clause, memory):
                            return clause, True
                    continue
                part = head
                # The cut is taken after the "said already" test above, and the head on its own is
                # the part that was handed back a turn ago: "Fix the wake-up time first" came back
                # as "After that: Fix the wake-up time first." on a "what else", the same
                # instruction twice in a row. What the head contains has been said too.
                if _already_repeated(part, memory):
                    continue
        if _says_what_to_do(part):
            return part, True
        if not spare:
            spare = part
    # An explanatory part is offered only when it was not on the screen already: the answer in hand
    # was read in full a turn ago, so handing its opening sentence back as "one more thing" is the
    # paragraph again with a label in front of it ("my knee hurts" / "what should i do first" /
    # "anything else" -> "There is this too: A sore knee is usually a strain"). Where the doing
    # parts are all spent, the honest "that's the lot I have" is the reply.
    if spare and not _said_in_a_turn(spare, memory):
        return (spare, False)
    return ("", False)


def _said_in_a_turn(short, memory):
    """Whether these words are already in a reply the bot gave, whichever turn it was."""
    said = str(short or "").strip()[:60].lower()
    if not said:
        return False
    for turn in memory.get("turns") or []:
        if isinstance(turn, dict) and said in str(turn.get("bot") or "").lower():
            return True
    return False


def _says_what_to_do(part):
    """True when the sentence tells them to do something rather than saying how things are."""
    from ..compose.verdict import IMPERATIVES  # the verbs an instruction can open on

    words = [w.strip(" ,;:.") for w in str(part).lower().split()]
    orders = bool(re.search(r"\bdo not\b|\bdon'?t\b", str(part), re.I))
    at = next((index for index, word in enumerate(words) if word in IMPERATIVES), None)
    if at is None:
        return orders
    # A verb that comes after the sentence has said how things are is not the doing asked for:
    # "Losing about 0.5 to 1kg a week is the rate that stays off, and the plan that works is the
    # one you would still follow in a year" was handed to a "what else" as the next thing to do,
    # because "follow" is on the list. The copula in front of it makes the sentence a statement
    # about the thing, and a statement is the spare, not the move.
    if any(word in ("is", "are", "was", "were", "means", "sounds") for word in words[:at]):
        return orders
    return True


# The leads that say the line after them was given in this chat already. They are true only when
# it was. An answer is reached again by a line it does not fit ("what should we spend it on first"
# got a cheap-food answer out of a bathroom chat, "what if she just wont start" a caffeine one out
# of a homework chat), and framing that as "It's what I said a moment ago: ..." tells the person
# they already have an answer they never got - worse than a punt, because it is a claim about
# their own conversation that is not true. Where the claim does not hold, the sentence is still
# the best thing to give: it is just given plainly, with nothing said about when it was said.
CLAIMS_IT_WAS_SAID = (
    "it's what i said a moment ago",
    "you've got it",
    "that's the one",
    "same answer",
    "from just now",
    "said again",
    "sorry, again",
    "as i said",
    "again",
)


def _said_in_the_chat(said, memory):
    """True when the chat has already read this wording.

    Checked the way a friend would: the opening of the line, whitespace flattened, against the
    bot's own turns. A short form is a cut of an answer rather than a copy of one, so the opening
    is what has to be found, not the whole line.
    """
    opening = " ".join(" ".join(str(said or "").lower().replace("...", " ").split()).split()[:10])
    if not opening:
        return False
    for turn in memory.get("turns") or []:
        if isinstance(turn, dict) and opening in " ".join(str(turn.get("bot") or "").lower().split()):
            return True
    return False


def _claims_what_it_never_said(reply, memory):
    """The line, with its claim to have said this before taken off when the claim does not hold."""
    line = str(reply or "").strip()
    low = line.lower()
    for head in CLAIMS_IT_WAS_SAID:
        if not low.startswith(head):
            continue
        rest = line[len(head):].lstrip(" :-,\u2014").strip()
        if rest and not _said_in_the_chat(rest, memory):
            return rest[:1].upper() + rest[1:]
        return line
    return line


def _handed_back(memory, reply):
    """Keep the line handed back, so the next bare ask sees it as already said.

    A short form of an answer is not a copy of it (a move is one clause of it), so counting the
    earlier answers alone would let the same clause come back a third time: the turn that handed
    it back has to count as having said it.
    """
    reply = _claims_what_it_never_said(reply, memory)
    kept = memory.get("repeated")
    if not isinstance(kept, list):
        kept = memory["repeated"] = []
    kept.append(reply)
    del kept[:-8]
    return reply


_FRAME_HEADS = []


def _frame_heads():
    """Every lead-in this module can put in front of a line, as the text it opens on.

    Read off the templates rather than listed again, so a pool added later - here or below this
    point in the file - is framed like the rest, and a frame can never be stacked on a frame the
    test does not know about. Found on first use, when the whole module has been read.
    """
    if _FRAME_HEADS:
        return _FRAME_HEADS[0]
    heads = set()
    for value in list(globals().values()):
        if not isinstance(value, (tuple, list)):
            continue
        for item in value:
            if not isinstance(item, str):
                continue
            # A template is a line with a slot in it: "Shorter: {short}". A bare "{short}" is
            # the answer itself and opens on nothing, so it frames nothing.
            head = item.split("{", 1)[0].strip()
            if "{" in item and head:
                heads.add(head.lower())
    _FRAME_HEADS.append(tuple(sorted(heads, key=len, reverse=True)))
    return _FRAME_HEADS[0]


def framed(said):
    """True when this line already has one of this module's hand-back frames on it.

    "i dont follow" after a line that repeat had framed came back as "I said: It's what I said a
    moment ago: ..." - a frame stacked on a frame - because the module that answers "what did you
    mean" only knew its own leads. A line that has already been handed back under a lead is the
    answer's second telling, and framing it again says the same thing a third time.
    """
    line = (said or "").strip().lower()
    return bool(line) and line.startswith(_frame_heads())


def handed_back(memory, reply):
    """The public form of `_handed_back`: a line the bot gave with a lead on it is kept.

    Every module that hands a line over under a frame records it here, so nothing frames it again:
    a frame on a frame is the bot saying the same thing a third time.
    """
    return _handed_back(memory, reply)


def _already_repeated(short, memory):
    """Saying the same paragraph a third time reads worse than moving on: once the answer has
    come back once, another "what now" wants the next step, not the same line again."""
    said = short.strip()[:60].lower()
    if not said:
        return False
    seen = 0
    for turn in memory.get("turns") or []:
        if not isinstance(turn, dict):
            continue
        # Case does not decide whether a sentence has been said: a move is handed back with its
        # first letter lowered, and it is still the same sentence on the screen.
        if said in str(turn.get("bot") or "").lower():
            seen += 1
    # A line handed back a turn ago counts as said: a move is one clause of an answer, so it is
    # not found in the answer it came from.
    for line in memory.get("repeated") or []:
        if said in str(line or "").lower():
            seen += 1
    return seen >= 2


def _handed_back_already(step, memory):
    """True when this very step has already been handed back as the reply, not merely said.

    `_already_repeated` asks whether the words are on the screen, and a step is one clause of the
    answer it comes from, so the answer itself counts as one telling. That is right for a step
    handed back a turn ago; it is wrong for the ask that comes after a paragraph, where the words
    are there and the step never was: "i keep burning the bottom of my pans" / "what am i doing
    wrong" (the answer again, framed) / "how do i clean it off" was answered with a search hedge,
    because the first clause of the pan answer had now been "said" twice and the step once never.
    """
    said = step.strip()[:60].lower()
    if not said:
        return False
    for turn in memory.get("turns") or []:
        if not isinstance(turn, dict):
            continue
        reply = str(turn.get("bot") or "").strip().lower()
        if not reply or said not in reply:
            continue
        # The reply has to be the step rather than a paragraph that carries it: a step is at
        # least a third of the line it is handed back as, and a sentence of a long answer is not.
        if len(said) * 3 >= len(reply):
            return True
    for line in memory.get("repeated") or []:
        if said in str(line or "").lower():
            return True
    return False


# "make it short", "shorter please", "in one line", "tldr": the person is not asking a new
# question, they are asking for the answer they already have with the detail taken out. It names
# nothing of its own, so it is answered from the last answer's own lead - no lookup, and no hedge
# a turn after the bot has just answered properly.
LESS = re.compile(
    r"\b(?:make (?:it|that)|keep it|be|say it|put it|give it to me|give me it)\s+"
    r"(?:a bit |a lot |really |much |nice and )?"
    r"(?:short|shorter|brief|briefer|quick|quicker|snappy|concise)\b"
    r"|\b(?:short|shorter|brief|briefly|concisely)\s+please\b"
    r"|\b(?:shorter|tldr|tl;?dr|summarise|summarize|sum it up|sum up|short version|"
    r"cut it down|cut to the chase|get to the point|skip the detail|less detail|"
    r"in (?:a|one) (?:sentence|line)|one line|just the (?:gist|answer|short version))\b"
    # Asking for the same answer in words they can use is the same request as asking for it
    # shorter, and it is how most people word it: "make it simpler", "in plain english",
    # "explain it like im 5", "no jargon please". None of these asks anything new, and the words
    # gate in `asks_for_less` still holds, so a line that names something of its own keeps its own
    # reading: "can you make a simpler cake" and "how do i make my essay shorter" are not this.
    r"|\b(?:simpl(?:e|er|ify|ified)|in plain (?:english|terms|words)|plain english|"
    r"(?:in )?simple (?:english|terms|words)|no jargon|jargon[- ]free|layman'?s? ?terms?|"
    r"explain (?:it|that)(?: (?:all )?(?:again|to me))? (?:simply|in english|in simple words)|"
    r"put it (?:simply|plainly|in plain (?:english|words))|dumb (?:it|that)? ?down|"
    r"plainly\b|like (?:i'?m|im|i am) (?:5|five))\b",
    re.I)

# The words an ask for less is made of. Anything else in the line names something, and a line that
# names something is its own question: "how do i make my essay shorter" is not this turn.
LESS_WORDS = frozenset("""make made it that keep be say put give me a bit lot really much
    nice short shorter brief briefer briefly quick quicker snappy concise please tldr tl dr
    summarise summarize sum gist answer version cut chase point skip detail details less
    sentence line one just and so ok okay right then now again too long word words
    more fewer condensed simple simpler simply simplify simplified plain english terms words
    jargon free layman laymans explain plainly like im i'm five 5 dumb dumbed easy easier wordy""".split())

# A lead handed back as the short form is the same answer, so it says so and then gets out of the
# way. The bare lead is one of the shapes: "Shorter: ..." on every turn would be a stock line.
LESS_LEADS = (
    "{short}",
    "Shorter: {short}",
    "In short: {short}",
    "Briefly: {short}",
)

# An answer the knowledge base writes can carry a lead of its own, and it is short because of it:
# "Quick: tuna pasta in 15, a frittata in 20, or a salmon traybake if you have 30 minutes." Handing
# that back under this module's lead stacks two promises in front of one answer - "Briefly: Quick:
# tuna pasta in 15 ..." - which is a longer reply than the one it replaced, not a shorter one. The
# label is the answer's, and it says the same thing the lead would, so the lead steps out of the
# way. It is only a label when it is a few words and ends at a colon: "Ask early, name the dates
# and say who covers:" is the opening of an answer, not a name for it.
OWN_LEAD = re.compile(r"^[^:!?.\n]{1,45}:\s")
OWN_LEAD_WORDS = 5


def _a_lead_of_its_own(short):
    """True when the short form already opens with a label of its own ("Quick: ...")."""
    match = OWN_LEAD.match(str(short or ""))
    return bool(match) and len(match.group(0).split()) <= OWN_LEAD_WORDS


# "shorter but keep the timings", "one line, but don't leave out the water ratio": the person
# asks for less and says what the less has to keep. Read as a fresh line it reached the entry for
# softening a message somebody sends ("Softer, same point: \"But keep the timings.\"").
KEEP_CLAUSE = re.compile(
    r"\b(?:but\s+)?(?:keep|keep\s+in|leave\s+in|don'?t\s+(?:leave\s+out|drop|lose)|without\s+"
    r"(?:losing|dropping)|making\s+sure\s+(?:to\s+)?(?:keep|say))\s+(?P<what>.+)$", re.I)
# The requirement is honoured by handing back the sentence that carries it, so a word of it has to
# be a word of the answer, or the answer has to be about numbers at all ("keep the timings" is in
# the minutes, not in the word).
FIGURES = re.compile(r"\b(?:timings?|times?|numbers?|figures?|ratios?|amounts?|quantit(?:y|ies)|"
                     r"temperatures?|degrees?|weights?|measures?|proportions?)\b", re.I)
DIGIT = re.compile(r"[0-9]")


def _kept_clause(text):
    """The words a shorter version has to keep, or "" when the line names none."""
    match = KEEP_CLAUSE.search(" ".join(str(text or "").split()))
    return match.group("what").strip(" .!?,") if match else ""


# "how do i make it shorter" asks how to do something to a thing of theirs - an essay, a wait, a
# queue - and the thing is in what they said the turn before, not in the words of the ask. The
# person who wants less of the answer tells us: "make it shorter", "can you make it shorter". A
# question in this shape that names nothing still names its own verb, so it is not this turn.
HOW_TO = re.compile(
    r"\bhow\b(?:\s+\w+){0,3}\s+(?:do|can|should|would|could|might|shall)\s+(?:i|we|you)\b",
    re.I)


# Words that ask for fewer words on their own, without any of the phrasings `LESS` knows: a person
# who has just been given a paragraph and types "briefly" or "short" has asked for the short version,
# and `LESS` only knew "briefly please" and "make it short". The line still has to be made of
# nothing but these and filler, so a line that names something is never this turn.
BREVITY_WORDS = frozenset("""brief briefly short shorter concise concisely tldr gist sentence
    condensed summarise summarize sum version line""".split())


def asks_for_less(text):
    """True when the whole line, bar what it says to keep, is a request for a shorter answer."""
    clean = " ".join(str(text or "").split())
    if not clean:
        return False
    if HOW_TO.search(clean):
        return False
    asked = KEEP_CLAUSE.sub("", clean) if KEEP_CLAUSE.search(clean) else clean
    said = topics.words(asked)
    left = [w for w in said
            if w not in LESS_WORDS and w not in FILLER and w not in ASK
            and w not in ASK_VERB and w not in topics.STOPWORDS]
    if left:
        return False
    # "briefly", "short", "condensed" on their own: every word of the line is already an ask for
    # less, so one of the words that promises it is the whole of the reason to read it that way.
    if not (LESS.search(clean) or any(w in BREVITY_WORDS for w in said)):
        return False
    # The word has to be what the line is about, not a word in front of a thing it describes: "a
    # short book" asks for a book, and "short hair" is a haircut. Both read as an ask for less
    # until this line, because "book" is a verb the ask lists know and "hair" is a word the
    # topic lists drop - so the last word of the line that is not filler decides.
    settled = [w for w in (said or topics.words(clean))
               if w not in FILLER and w not in topics.STOPWORDS]
    return bool(settled) and (settled[-1] in LESS_WORDS or settled[-1] in BREVITY_WORDS)


# The answer was already one sentence, so there is nothing to take out: say so and give it back
# rather than answering a request for less with "I don't know enough to answer that".
# A request for less that says what it has to keep is answered with the sentence that keeps it.
KEEPING = (
    "Keeping {keep}: {short}",
    "With {keep} in: {short}",
)

ALREADY_SHORT = (
    "That's about as short as it gets: {short}",
    "That is the short version: {short}",
)

# Asked for a short version of a short answer they have already had in pieces: there is nothing
# left to hand back, and reading the answer out again is the one thing a shorter answer is not.
NO_SHORTER_STILL = (
    "That is the short version - there is nothing left in it to take out.",
    "Nothing left to cut: every part of that answer you have now had on its own.",
)

# A request for less on the first turn of a chat names nothing to cut down. The search hedge is
# the wrong answer to it: there is nothing to look up, and "I don't know enough to answer that"
# reads as a refusal to a person who only asked for a shorter one.
NOTHING_TO_CUT = (
    "Nothing to cut down yet - ask me something and I'll keep it short.",
    "Nothing in hand to shorten - ask away and I'll keep it brief.",
)

# Asked twice, the lead is not shorter than the answer any more, so the line is the one sentence
# of it that carries the most: the figure, the step, the condition.
JUST_THIS = (
    "Just this: {short}",
    "The one thing in it: {short}",
)


# A line that opens a chat has nothing in it to cut down, and handing back less of "Hi, good to
# meet you" answers nothing - and the composer speaks as the fallback module, so the greeting's own
# lines carry that module's name too. The one line of the greeting that is an answer is a draft
# handed over inside its own quotation marks ("Here's something you could send: ..."), so the name
# is skipped only when the line holds no draft, and `_the_quotation` is what reads the draft.
WELCOMES = "greeting"


def _recent_lines(memory):
    """The bot's own recent lines that said something, newest first, with how many turns ago.

    Wider than `_recent_answers`: a request for less is about whatever the bot just said, and the
    line can be the small-talk answer as easily as a knowledge one ("i feel a bit low" / "make it
    short"). A greeting, a hedge, a question back and a line too short to have any detail in it
    are all still left out. The count is of lines that said something, not of turns: after two
    hand-backs the answer they came from is still the line in hand, and counting the hand-backs
    would put it out of reach of a third request for less.
    """
    out = []
    for turn in reversed((memory.get("turns") or [])[-LOOK_BACK_FOR_LESS:]):
        if not isinstance(turn, dict):
            break
        said = str(turn.get("bot") or "").strip()
        if not said or HEDGE.search(said):
            continue
        if turn.get("module") == WELCOMES and not _the_quotation(said):
            continue  # a hello has nothing to shorten; a draft it handed over does
        if said in (memory.get("repeated") or []):
            continue  # our own hand-back: saying it again under another lead-in stacks them
        if len(said.split()) < 6 or said.rstrip().endswith("?"):
            # A short answer is still the answer: "About 500 g of chicken each." is what a
            # request for less gets handed back with "that is as short as it gets", and skipping
            # it left the line answered with "nothing to cut down yet" a turn after an answer.
            continue
        out.append((len(out) + 1, said))
    return out


# A sentence ends on its full stop, question mark or semicolon, and the closing quote mark after
# one belongs to it: "week." is the end of the sentence, not a mark inside the next one.
SENTENCE_END = re.compile(r"([.!?;][\"\u201d]?)\s+")


def _sentences(said):
    """The sentences of a line, split only where the line is not inside a quotation.

    A quotation is one unit: an answer that shows the person what to write has a question mark in
    it, and splitting there cut the message in half - "Shorter: Ask early, name the dates and say
    who covers: "Could I take 12-16 May off?" is a short answer that stops inside the sentence it
    is quoting, and the next request cut the other way, starting mid-quote with the closing mark
    left on it. So a boundary only counts once the quotes before it pair up.
    """
    text = str(said or "").strip()
    out, last = [], 0
    for end in SENTENCE_END.finditer(text):
        piece = text[last:end.end()].rstrip()
        if _unbalanced(piece):
            continue
        if piece.strip():
            out.append(piece.strip())
        last = end.end()
    tail = text[last:].strip()
    if tail:
        out.append(tail)
    return out


def _most_condensed(said, memory=None):
    """The one sentence of the answer that carries the most, for a second request for less.

    A sentence already handed back is left out: after "Shorter: <the lead>", the sentence that
    carries the rest of the answer is the one thing they have not read twice, and handing back
    the lead again under a second lead-in is the one thing that makes a short answer longer.
    """
    parts = [p.strip().strip(",;:") for p in _sentences(str(said).strip())]
    parts = [p for p in parts if 4 <= len(p.split()) <= 30 and not topics.RED_FLAG.match(p)]
    parts = [p for p in parts if not _already_repeated(p, memory or {})]
    if not parts:
        # An answer written in long sentences gets its shortest one anyway: a second request for
        # less inside a 31-word sentence is still a request, and the alternative is handing the
        # whole paragraph back under a lead that promises it is short.
        long_parts = [p.strip().strip(",;:") for p in _sentences(str(said).strip())]
        long_parts = [p for p in long_parts if 4 <= len(p.split()) <= 45
                      and not topics.RED_FLAG.match(p)]
        long_parts = [p for p in long_parts if not _already_repeated(p, memory or {})]
        if long_parts:
            return min(long_parts, key=lambda p: len(p.split()))
    if not parts:
        return ""
    return min(parts, key=lambda p: len(p.split()))


# A lead that is still a paragraph is not a shorter answer: "in one line" answered with forty
# words and "Briefly:" in front of them keeps the promise in the wrong direction. The cap is
# generous on purpose - a first sentence of twenty-odd words is a real short answer - so only a
# lead nobody would call short is cut down.
SHORT_ENOUGH = 26
CLAUSE_SPLIT = re.compile(r"(?<=[,;])\s+")
# A clause that ends on one of these was cut off mid-thought: "staying active is what helps most
# and" is not a sentence, and a short answer that stops in the wrong place is worse than a longer
# answer that finishes.
CUT_MID_SENTENCE = frozenset("""and but so or because which that while with rather than to of the
    a an in on for if when as also then it its your my their there""".split())


def _short_enough(cut):
    """The answer's shorter read, trimmed to something a person would call short.

    A short lead is handed back as it is. A long one is cut at its own colon first - the place an
    answer often offers its own summary ("... and staying active is what helps most: keep walking
    ...") - and then at the last clause boundary inside the cap, never ending on a word that
    leaves the sentence hanging.
    """
    cut = str(cut or "").strip()
    if len(cut.split()) <= SHORT_ENOUGH:
        return _ended(cut)
    head = _read_up_to_the_colon(cut)
    if len(head.split()) <= SHORT_ENOUGH:
        return _ended(head)
    parts = [p.strip() for p in CLAUSE_SPLIT.split(head) if p.strip()]
    out = ""
    for part in parts:
        together = (out + " " + part).strip()
        if out and len(together.split()) > SHORT_ENOUGH:
            break
        out = together
    words = out.rstrip(",;").split()
    while words and words[-1].lower().strip(",;") in CUT_MID_SENTENCE:
        words = words[:-1]
    out = " ".join(words).rstrip(",;")
    if len(out.split()) < 6:
        return _ended(head)
    return _ended(out)


def _ended(cut):
    """A short answer cut out of a sentence still ends like a sentence.

    A cut that ends on a quotation needs no full stop of its own when the quoted sentence already
    has one: `... nothing is due that week."" is finished, and a stop after the closing mark says it
    twice.
    """
    cut = str(cut or "").strip().rstrip(",;:")
    if cut[-1:] in ".!?":
        return cut
    if cut[-1:] in "\"\u201d" and cut[-2:-1] in ".!?":
        return cut
    return cut + "."


def _unbalanced(piece):
    """True when a piece opens a quotation it does not close, so it is the middle of one.

    A straight quote is its own mark, so an odd number of them is a quotation left open; the curly
    pair is counted against itself.
    """
    said = str(piece or "")
    for opens, closes in QUOTE_PAIRS:
        if opens == closes:
            if said.count(opens) % 2:
                return True
        elif said.count(opens) != said.count(closes):
            return True
    return False


def _the_quotation(said):
    """The draft the answer handed over inside its own quotation marks, or "".

    "Here's something you could send: \"Hi, basically I want Friday off. Thanks.\"" is a draft with
    a lead in front of it, and asking for less of a message asks for the message: cutting the
    lead leaves the whole draft with a shorter introduction, which is not a short version of it.
    """
    said = str(said or "")
    for opens, closes in QUOTE_PAIRS:
        at = said.find(opens)
        while at != -1:
            end = said.find(closes, at + len(opens))
            if end != -1:
                quote = said[at + len(opens):end].strip()
                # The quote has to be most of the answer: a message to send is the quotation with
                # the bot's own lead in front of it, while advice often carries a quoted example
                # ("Ask in person with one specific thing (\"I get the formula but I can't do the
                # last question\")") and handing that back as "Just this:" is advice cut to the
                # example, which answers nothing.
                if len(quote.split()) >= 4 and len(quote.split()) * 2 >= len(said.split()):
                    return quote
            at = said.find(opens, at + len(opens))
    return ""


def _closing_the_quote(cut, said):
    """The cut, carried on to the end of the quotation it stops inside.

    A short answer may stop inside a quotation as long as it stops after it: "... say who covers:
    \"Could I take 12-16 May off? I've arranged cover with Priya.\"" reads as a whole. When the
    answer has no end for the quotation the cut is left as it is - that is the module below
    saying nothing it can shorten, not a line to invent the rest of.
    """
    cut = str(cut or "").strip()
    whole = str(said or "").strip()
    if not cut or not _unbalanced(cut) or cut not in whole:
        return cut
    rest = whole[whole.index(cut) + len(cut):]
    for end in re.finditer(r"[.!?][\"\u201d]?", rest):
        longer = (cut + rest[:end.end()]).strip()
        if not _unbalanced(longer):
            return longer
    return cut


def _read_up_to_the_colon(said):
    """The sentence, or the part of it before its own colon when that is a shorter read of it."""
    head = str(said).partition(":")[0]
    if head != str(said) and 8 <= len(head.split()) < len(str(said).split()):
        return head.strip()
    return str(said)


def _keeps(said, what):
    """The sentence of the answer that carries what the person said the short version has to keep.

    A word of the requirement first ("the water ratio" is the sentence with the mugs of water in
    it), then the figures when the requirement is about numbers ("keep the timings" is in the
    minutes, and no sentence of the answer has the word "timings" in it). Empty when the answer
    has neither, and then the lead is the short version as before.
    """
    parts = [p.strip() for p in SENTENCE.split(str(said).strip()) if p.strip()]
    words = set(topics.words(what)) - set(topics.STOPWORDS) - {"timings", "timing", "numbers",
                                                               "figures", "details"}
    named = [p for p in parts if words & set(topics.words(p))]
    if named:
        return max(named, key=len)
    if FIGURES.search(what):
        counted = [p for p in parts if DIGIT.search(p)]
        if counted:
            return counted[0]
    return ""


def shorter_for(text, memory):
    """The last answer's own lead, or None when this is not a request for less.

    Three shapes, one per ask, because the second request cannot be answered with the sentence
    the first one just gave: the lead of the answer, then the single sentence of it that carries
    the most, and then the honest "that is the short version". A request for less never changes
    the subject and never looks anything up.
    """
    if not isinstance(memory, dict) or not asks_for_less(text):
        return None
    said_any = ""
    for back, said in _recent_lines(memory):
        if back > 2:
            break
        # A semicolon is where the answer already offered a shorter read of itself ("...; a
        # pressure top-up or a reset usually sorts it"), so the lead can end there too.
        parts = [p.strip().strip(";") for p in _sentences(said)]
        said_any = said_any or said
        lead = parts[0] if len(parts) > 1 else ""
        if lead and len(lead.split()) < 8 and len(parts) > 1:
            lead = parts[1]  # "Sorry to hear that." on its own is not the answer, it is the door
        # An answer written as one long sentence still offers a shorter read of itself at its own
        # colon: "Most back pain is muscular and settles in two to six weeks, and staying active
        # is what helps most: keep walking ...". "Briefly:" in front of all of it is not a shorter
        # answer, it is the answer with a promise in front.
        if not lead:
            lead = _read_up_to_the_colon(str(said)).strip()
        kept = _kept_clause(text)
        if kept:
            # What they said to keep is the short version they asked for: nothing else is.
            carry = _keeps(said, kept)
            if carry:
                return _handed_back(memory, pick(KEEPING, memory, text).format(
                    keep=kept, short=carry))
        # A draft handed over in quotation marks is the thing to give back shorter, and it is
        # already the whole of what to send: the lead in front of it is the bot talking.
        quote = _the_quotation(said)
        if quote and quote.strip() != str(said).strip() \
                and not _already_repeated(quote, memory):
            return _handed_back(memory, pick(JUST_THIS, memory, text).format(short=quote))
        for pool, cut in ((LESS_LEADS, lead),
                          (JUST_THIS, _most_condensed(said, memory))):
            cut = _closing_the_quote(_short_enough(cut), said)
            if not cut or _unbalanced(cut):
                continue
            if cut.strip().lower() == said.strip().lower():
                continue
            if _already_repeated(cut, memory):
                continue
            line = pick(pool, memory, text)
            if line != "{short}" and _a_lead_of_its_own(cut):
                line = "{short}"
            return _handed_back(memory, line.format(short=cut))
    if not said_any:
        return _handed_back(memory, pick(NOTHING_TO_CUT, memory, text))
    if said_any:
        # It is already one sentence: there is nothing to take out, and saying so is a better
        # answer than the search hedge a turn after the bot answered properly.
        one = _most_condensed(said_any, memory)
        if one:
            return _handed_back(memory, pick(ALREADY_SHORT, memory, text).format(
                short=_ended(one)))
        # Every sentence of it has now been read out as the short version, so quoting it again -
        # whole, under a lead that promises it is short - makes the reply longer than the answer
        # it was asked to cut. What is left to say is that there is nothing left.
        return _handed_back(memory, pick(NO_SHORTER_STILL, memory, text))
    return None


# The ask for a length, and the shape of the part of an answer that gives one: "Eight weeks.",
# "about two hours", "3 minutes". A part that is nothing but one of these has everything asked for.
A_LENGTH_ASK = re.compile(r"\bhow\s+long\b|\bhow\s+many\s+(?:days|weeks|months|hours|minutes)\b",
                          re.I)
A_BARE_TIME = re.compile(
    r"^\s*(?:about|around|roughly|usually|at least|up to|only|just|no more than)?\s*"
    r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|"
    r"thirty|forty|fifty|sixty|ninety|half an?|an?)\s*"
    r"(?:to\s+\w+\s*)?"
    r"(?:minutes?|mins?|hours?|hrs?|days?|weeks?|months?|years?)\b", re.I)


def _a_bare_time(part):
    """The part of an answer when it is nothing but the length asked for, else None."""
    if not isinstance(part, str):
        return None
    part = " ".join(part.split()).strip()
    if not part or len(part.split()) > 6 or not A_BARE_TIME.match(part):
        return None
    return part[0].upper() + part[1:]


# How far back an earlier answer is looked in for a length: the answer in hand is turn 1 and the
# detour before it, which is the shape people use.
LENGTH_BACK = 3


# A line that asks what something costs and points at it rather than naming it: "how much is that",
# "what does that cost". The ask word plus a pointer is the whole line - a line that names its own
# thing ("how much is a new boiler") is a question of its own and is left to the module that knows
# about boilers.
A_PRICE_ASK = re.compile(
    r"\bhow\s+much\b|\bhow\s+expensive\b|\bwhat\s+(?:does|do|would|will|did)\s+(?:that|it|this)\s+cost"
    r"|\bwhat\s+(?:is|was)\s+the\s+price\b", re.I)

# The pointer the line uses instead of naming the thing, and the words an ask about a price is
# made of. Anything else in the line is a thing of its own and keeps the ask for the module that
# knows about that thing.
POINTING_BACK = frozenset("that this it those these they them ones one".split())
PRICE_WORDS = frozenset("""
how much many expensive price priced cost costs costing cheap cheaper cheapest usually typical
normally roughly about approximately altogether total altogether pay paying spend spends by for
at a an the per each and so then do does did would will is was are were be be a lot really
here there again any more of on in to get got buy buying round roughly average range
""".split())


def _names_no_thing_of_its_own(text):
    """Whether the line asks about a price without naming what the price is for."""
    words = topics.words(text or "")
    if not words or not any(word in POINTING_BACK for word in words):
        return False
    return all(word in POINTING_BACK or word in PRICE_WORDS or word in topics.STOPWORDS
               for word in words)


def _the_price_the_answer_gave(text, memory):
    """The price the answer in hand stated, when the line asks what that costs, else None.

    "the boiler is old" / "should i get it serviced" ("Once a year, yes: a gas boiler service is
    usually 60 to 120 pounds ...") / "how much is that usually" was answered with the price of a
    new boiler, because the module that knows about boilers took the question and the answer on
    the screen already said the figure. An ask that points at the last answer rather than naming
    its own thing is a question about that answer, and an answer that states one price has
    nothing to choose between: that price is what it says it costs.

    Two prices are two different things ("a patch is 150 to 400, a whole roof 3,000") and the one
    the person means is not known, so an answer with two is left alone.
    """
    part = _the_price_in_hand(text, memory)
    if not part:
        return None
    if _a_length_already_handed(part, memory):
        return None
    return _handed_back(memory, part)


def asks_what_that_costs(text, memory):
    """Whether the line asks the price of the thing the answer in hand has just priced.

    The turn is this reading's in the same way a check of a fact is: the line names nothing of
    its own, so every entry about the word in it ("how much is that usually" after a boiler
    service) answers the ask by pricing its own subject instead of the figure on the screen.
    """
    return bool(_the_price_in_hand(text, memory))


def _the_price_in_hand(text, memory):
    """The bare price the answer in hand gave, when the line asks what that costs, else None."""
    line = str(text or "")
    if not A_PRICE_ASK.search(line) or narrow.kind_of(line) != "money":
        return None
    if not _names_no_thing_of_its_own(line):
        return None
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return None
    last = str(turns[-1].get("bot") or "")
    if not last:
        return None
    found = {" ".join(hit.group(0).lower().split())
             for hit in narrow.SPANS["money"].finditer(last)}
    if len(found) != 1:
        return None
    part = narrow.narrow(last, line)
    if not part or not narrow.SPANS["money"].search(part):
        return None
    part = " ".join(part.split())
    if len(part.split()) > 8:
        return None
    if not part.endswith((".", "!", "?")):
        part += "."
    return part[0].upper() + part[1:]


def _the_time_an_earlier_answer_gave(text, memory):
    """The length an answer further back gave, when the line asks for one and the last one does
    not hold it.

    "i want to run a 5k" ("Three runs a week gets most people to 5k in about eight weeks") /
    "im 45 and havent run since school" ("Come back at about half of what you used to do ...") /
    "how long to train" was met with "That's beyond what I know well, sorry", a search hedge,
    while "eight weeks" sat in the chat two turns back. The answer in hand is the wrong place to
    look: it is about how hard to come back, not how long, and narrowing it gives no length.
    """
    said_line = str(text or "")
    if not A_LENGTH_ASK.search(said_line) or narrow.kind_of(said_line) != "time":
        return None
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if len(turns) < 2:
        return None
    # The answer in hand is the normal place for this: when it can be narrowed to the length, the
    # readers below hand that part back and this one keeps out of it.
    last = str(turns[-1].get("bot") or "")
    if last and _a_bare_time(narrow.narrow(last, said_line)):
        return None
    for back, asked, said in _recent_answers(memory):
        # Two answers back is the case people have: a detour, then the ask. An answer from six
        # turns back is likely a different plan that happens to share a word.
        if back < 2 or back > LENGTH_BACK or not narrow.SPANS["time"].search(said):
            continue
        if not _about_the_same_thing(asked, said, memory):
            continue
        # A length from an older answer is only this line's length when the chat is still on the
        # thing that answer was about: "ive started running three times a week" / "i want to lose
        # a stone" / "how long will it take" was given "20 to 30 minutes", the length of the runs,
        # because the older answer is about its own question by construction and nothing asked
        # whether the subject in between had changed the thing being measured.
        if not _the_chat_is_still_on(asked + " " + said, memory):
            continue
        part = _a_bare_time(narrow.narrow(said, said_line))
        if part and not _a_length_already_handed(part, memory):
            return _handed_back(memory, part)
    return None


def _a_length_already_handed(part, memory):
    """True when this length has been handed back already in this chat.

    Once "Eight weeks." has answered "how long to train", the next length ask in the same chat is
    about a different length: "and how long to recover" was given the same "Eight weeks." - the
    time to reach 5k, handed over as the time to recover from a run, which is a confident wrong
    number where a hedge is honest. A length is spent once it has been handed over.
    """
    kept = memory.get("repeated")
    if not isinstance(kept, list):
        return False
    flat = " ".join(str(part).lower().split()).strip(" .")
    return any(flat == " ".join(str(said).lower().split()).strip(" .") for said in kept)


def _a_what_to_do_answer(memory):
    """True when the answer in hand is itself the answer to "what should i do": a plan, or the
    free time to fill.

    "What can i do with that" is a use ask - a dish, or a purpose for the thing the last answer
    was about - and repeating that answer under a lead is wrong for it. But the pronoun can point
    at the free time that was just planned: "got the day off" / "no plans yet though" / "what
    should i do with it" asks the same thing as "what should i do now", and it reached a search
    hedge. Only the answer in hand's own keys decide it: a recipe's keys name its ingredients and
    a plan's name the event or the free block, in the plans domain's own words.
    """
    from ..knowledge.plans import FREE_TIME  # noqa: PLC0415 - read only when a line asks with
    if not isinstance(memory, dict):
        return False
    answer = memory.get("entry_answer")
    if not isinstance(answer, dict):
        return False
    # Only the words that are the free time itself, or the plan of it. The whole of FREE_TIME is
    # no good here: it holds "long weekend", and "long" is a key of the answer about a journey
    # with children, so "what should we do with them" about the kids was answered with the first
    # clause of the travel answer.
    blocks = {"plan", "plans", "planning", "weekend", "weekends", "bored", "dayoff"}
    for one in FREE_TIME:
        words = [word for word in str(one).lower().split() if len(word) > 3]
        if words and all(word in blocks for word in words):
            blocks.update(words)
    return bool({str(key).lower() for key in (answer.get("keys") or ())} & blocks)


def _a_city_guide_is_the_answer_in_front(memory):
    """True when the reply on the screen is a city's list of places to go.

    A city card is a list of places, not a list of steps, so "what should we do first" after it
    asks which of those places comes first - and the city row answers that itself. Read as a step
    of the card it came back "The thing to do first: Eat lunch at 2pm like locals", which is a
    habit, not the first place. The travel cards are imported here rather than at the top because
    they are the only thing in this module that reads them, and `answers` asks the same question
    of the same helpers (see `_a_city_card_asks_which_first`).
    """
    from ..knowledge import travel  # noqa: PLC0415 - no import cycle at load
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return False
    return travel.a_city_card_is_in_front(turns[-1].get("bot"))


def answer_for(text, memory):
    """The answer they just asked for again, or None when this is not that turn."""
    from ..compose import limit as limit_line  # noqa: PLC0415 - no import cycle at load
    # The card in front is a city's places, and which of them comes first is the city row's own
    # question: this reader would hand back a sentence of the card that reads like a first step.
    if asks_for_the_move(text) and isinstance(memory, dict) \
            and _a_city_guide_is_the_answer_in_front(memory):
        from ..knowledge import travel  # noqa: PLC0415
        if travel.asks_which_one_first(text):
            return None
    # "anything else" is an ask for the next part only where there is a part to give, so it is
    # let past `names_nothing` for the shape below and not for every arm of this function.
    more = asks_for_more(text) and _handed_back_last(memory)
    # The free time just planned is the thing "with it" points at, and the answer to it is the
    # plan again: see `_a_what_to_do_answer`.
    if USE_WITH.search(str(text or "")) and not _a_what_to_do_answer(memory):
        return None
    if WORDING.search(str(text or "")):
        return None  # a line about how to say it is not a line about the last answer
    # The length asked for, when the answer that gave it is further back than the last one: see
    # `_the_time_an_earlier_answer_gave`.
    time_said = _the_time_an_earlier_answer_gave(text, memory)
    if time_said:
        return time_said
    # The price the answer on the screen gave, when the line asks what that costs without naming
    # anything of its own: see `_the_price_the_answer_gave`.
    price_said = _the_price_the_answer_gave(text, memory)
    if price_said:
        return price_said
    # The asks that name nothing of their own and still want the answer in hand: "anything else",
    # "where do i start", "how do i clean it off". Each is read out below by its own reader.
    put_right = asks_to_put_it_right(text)
    if not (names_nothing(text) or a_step_of_the_same_answer(text)) and not (
            more or says_where_to_start(text) or HOW_IT.search(str(text or ""))
            or a_more_ask(text) or put_right):
        return None
    # An ask for an idea is answered by the entries when an entry has an idea of its own to give:
    # "he'll eat pasta and cheese and not much else" / "any ideas" is another dish, and the step
    # this reader hands back is a clause of the dish already given ("Make a quick sauce with a
    # knob of butter"). Where every entry has is the same answer said again, the step is the one
    # thing on the screen the person has not read.
    if IDEAS_ONLY.match(str(text or "")) and _an_entry_answers_it(text, memory):
        return None
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    # The line that asks which part to do first is the one ask that a pointer back has not
    # already answered: "i keep burning the bottom of my pans" / "what am i doing wrong" (the
    # answer again, under a lead) / "how do i clean it off" wants the first clause of that
    # answer and has never had it, so the pointer guard leaves this ask alone.
    which_part = asks_for_the_move(text)
    if turns and not which_part and REFER_BACK.search(str(turns[-1].get("bot") or "")):
        return None
    # A turn that said the answer again with something taken out of it is not a turn after a new
    # answer: the answer behind it is still the one on the table, so an ask for the move after it
    # is answered from the whole answer, not from a fragment of the restatement. "my dog pulls on
    # the lead" / "no treats" / "how do i stop it" was handed "Same answer: Stand still until it
    # slackens" - the step with nothing round it - instead of the training answer it came from.
    if turns and limit_line.restates_the_answer(str(turns[-1].get("bot") or "")):
        return None
    tried = str(turns[-1].get("user") or "") if turns else ""
    wanted = narrow.kind_of(text)
    for back, asked, said in _the_answer_about_what_we_are_on(memory, _recent_answers(memory)):
        # The turn just before this one is the answer they are asking for; anything older is only
        # that answer if the chat has not moved on since. Adding a detail to the same thing and
        # having it said back is not moving on, so the answer behind it still stands: "we want to
        # grow some veg" / "we only have a small patio" / "what should we start with". An
        # acknowledgement of the person's own line is not the chat moving either.
        if (back > 1 and not _about_the_same_thing(asked, said, memory)
                and not _only_echoes_between(memory, back)
                and not _nothing_but_acknowledgements(back, memory)):
            continue
        if _a_new_work(text, asked):
            # "what is an apprenticeship" / "how do i get one": the line carries "get", a doing
            # the answer in hand never used, so this is a new question about the same subject and
            # the knowledge base answers it ("apply to them like jobs, because that is what they
            # are"). Handing the answer back gave the pay line under "Start with this" instead
            # (@blue-hedgehog, @sky-tuna, #6152). A line that asks back at the answer names no
            # doing of its own ("how do i do that", "where do i start") and is untouched.
            return None
        if wanted is not None and not narrow.carries(said, wanted):
            # A line can name nothing and still ask for a particular kind of fact: "how much
            # should i spend" after "im after a new kettle, mine leaks" names no thing, and the
            # answer it would be handed back says what has perished in the kettle and nothing at
            # all about money. Handing the paragraph back is what a person hears as not being
            # listened to - they asked a price and got the fault again. A figure the answer does
            # not carry is not the answer again, so this answer is not the one to give back.
            continue
        nothing_more = False
        if more:
            # Only after a step out of this answer: an answer that was read out in full has its
            # next part taken by the knowledge base's own reader, and the ask there is not the
            # same one. This branch is for the ask that comes after a *short form* of the answer,
            # where that reader is left holding a fragment and re-tells the paragraph instead.
            part, doing = _another_part(said, memory)
            if part:
                leads = NEXT_LEADS if doing else ALSO_LEADS
                return _handed_back(
                    memory, pick(leads, memory, text).format(step=part[:1].upper() + part[1:]))
        if (tried and not QUESTION_MORE.search(tried)
                and (_tried(tried) or _a_step_done(tried, said))):
            later = _later_part(tried, said)
            if later:
                short = _short(later)
                # The later step was already handed back once. On an explicit "what else" that is
                # still the only step left, so saying it under a lead beats the search shrug.
                return _handed_back(memory, _a_lead_and_a_step(
                    _a_lead_for(_the_lead_for(text, short), short, memory, text), short))
            if not a_more_ask(text):
                continue
            # "my back hurts" / "ive tried stretching" / "what else can i do": they named the part
            # they have tried and the rest of this answer is what they are asking for, so the
            # readers below get the answer. Main skipped it here because nothing below used to
            # read a "what else"; with that reader in place, skipping it is the search hedge.
        if a_more_ask(text):
            step = _the_next_step(said, memory)
            if step:
                _wording = step[:1].upper() + step[1:]
                return _handed_back(memory, pick(MORE_LEADS, memory, text).format(step=_wording))
            # "and what else" with no second step to hand over: the paragraph again is not one
            # more thing, so this reader steps aside - the step readers below get the line, and
            # past them an ask for more is not a repeat at all, so the whole answer under a
            # lead-in ("From just now: If you want something easy and good tonight: ...") is the
            # one reply this function must not write. `nothing_more` keeps it from the lead-in at
            # the end, which is where "what can i watch tonight" / "what else" was coming back
            # read out in full.
            nothing_more = True
        if asks_for_the_move(text):
            # "Where do i start" asks which part of the answer to do first, so it is read forwards
            # and the first instruction given, whatever verb it uses. The general reader below
            # walks backwards looking for a step, which gave the third step of a sleep answer.
            step = _the_first_step(said)
            if step and not _handed_back_already(step, memory) \
                    and not _they_say_they_tried(step, memory):
                _wording = step[:1].upper() + step[1:]
                return _handed_back(memory, _a_lead_and_a_step(
                    _a_lead_for(_leads_for(text), _wording, memory, text), _wording))
        if MOVE_ASK.search(text) or put_right or AND_NOW.match(text or ""):
            step = _a_move(said)
            if step is None and AT_A_LOSS.search(text or ""):
                # Nothing to do first, because every step in the answer waits on a moment: the
                # person at a loss is given that step with its moment, not the answer again.
                step = _a_conditional_move(said)
            if step and not _already_repeated(step, memory) \
                    and not _they_say_they_tried(step, memory):
                # Every lead ends on a colon or a full stop, so the step opens a sentence there
                # and takes a capital: "The thing to do first: Stop the cycle." An answer's own
                # wording is kept otherwise - this is the one letter formatting needs.
                said = step[:1].upper() + step[1:]
                if put_right:
                    # "can i fix it" carries no change word but CHANGE_ASK's "fix" would take the
                    # lead meant for what to change, so this ask gets its own.
                    leads = PUT_RIGHT_LEADS
                else:
                    leads = LOST_LEADS if AT_A_LOSS.search(text or "") else _leads_for(text)
                return _handed_back(memory, _a_lead_and_a_step(
                    _a_lead_for(leads, said, memory, text), said))
            # The step has already been handed back once, so this ask is the third time. The
            # composer's pointer at the rest of the answer is the best line when it has one to
            # point at ("Ease off running first. The rest of what I said follows from that"), so
            # the step is offered again rather than the turn stood down from: standing down here
            # left the turns whose answer the composer had no line for with a search hedge, which
            # is worse than the instructions they already have. The arbiter still prefers the
            # composer's line where there is one.
            if step:
                _wording = step[:1].upper() + step[1:]
                return _handed_back(memory, _a_lead_and_a_step(
                    _a_lead_for(_the_lead_for(text, step), _wording, memory, text), _wording))
        if more and not a_more_ask(text):
            # A bare "anything else" with nothing left of the answer to hand over. The paragraph
            # again is not one more thing, so this module stands down and the composer's own line
            # answers it ("That's the lot I have on that one. Tell me which bit isn't landing").
            return None
        if nothing_more:
            # An ask for more with nothing more in this answer is not the answer again: standing
            # down lets the composer's end line say the plain thing, and lets a knowledge entry
            # with a second wording answer the ask itself.
            return None
        short = _short(said)
        if short and not _already_repeated(short, memory):
            leads = SAY_AGAIN_LEADS if _a_bare_ask(text) else _the_lead_for(text, short)
            return _handed_back(memory, _a_lead_and_a_step(
                _a_lead_for(leads, short, memory, text), short))
    return None


_AN_ENTRY_IS_LOOKING = [False]


def _an_entry_answers_it(text, memory):
    """Whether the knowledge base has an idea of its own for this ask, rather than the answer again.

    The entries are asked the way the turn asks them - their own `respond`, on a copy of the
    memory so a probe claims nothing - and a reply that restates the answer in hand (`Same answer,
    and it covers this: ...`, `Nothing separate for suggest - it is the same advice: ...`) is not
    an idea, so it leaves the line to this reader. A reply with something new in it is the better
    answer by a long way, and this reader steps aside for it.

    The lookup is guarded against coming back into itself: `respond` asks this module whether the
    line is a repeat of the answer, and without the guard that question would return here.
    """
    if _AN_ENTRY_IS_LOOKING[0]:
        return False
    _AN_ENTRY_IS_LOOKING[0] = True
    try:
        from ..modules import answers as entries  # noqa: PLC0415 - no import cycle at load
        reply = entries.respond(str(text or ""), dict(memory or {}))
    except Exception:  # noqa: BLE001 - a lookup that fails claims no turn
        return False
    finally:
        _AN_ENTRY_IS_LOOKING[0] = False
    said = _words(reply)
    if not said:
        return False
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)] if isinstance(
        memory, dict) else []
    opening = " ".join(_words(turns[-1].get("bot") if turns else "")[:8])
    if opening and opening in " ".join(said):
        return False  # the entry is the answer in hand, said again
    return True


def _words(text):
    """The words of a line, lowercased, in order: enough to see one line inside another."""
    return re.findall(r"[a-z']+", str(text or "").lower())


def _a_bare_ask(text):
    """True when the whole line is one word asking to hear the last answer again."""
    match = BARE_ASK.match(str(text or "").strip())
    if not match:
        return False
    # "sorry" and "pardon" are the ask only as a question: "sorry" on its own is what a person
    # says to bad news, and the answer to that is not the paragraph above it.
    if match.group("word").lower() in BARE_ASK_NEEDS_A_QUESTION and "?" not in str(text or ""):
        return False
    return True


def _a_lead_and_a_step(lead, step):
    """A lead with the step in it, and one full stop at the end.

    Every lead ends the step with its own "." ("One thing to do first: {step}."), and a step that
    already ended a sentence carries one too: "One thing to do first: Quick: tuna pasta in 15 ...
    for 30 minutes.." is the same sentence closed twice.
    """
    said = str(step or "").rstrip()
    return re.sub(r"\.{2,}$", ".", re.sub(r"\.\.\s+", ". ", lead.format(step=said, said=said)))


# A lead that counts cannot take a step that names more than one: "One thing to do first: Two
# calls free up the most cash fastest" has the lead arguing with the step. When the step opens on
# a number above one, or on a pair, that lead is dropped and another of the same kind taken.
A_COUNT_OF_MORE_THAN_ONE = re.compile(
    r"^\W*(?:two|three|four|five|six|seven|eight|nine|ten|both|a couple|a pair|a few|the two|"
    r"the three)\b", re.I)


def _the_lead_for(text, step=""):
    """Which set of leads this line gets.

    "That's the one:" and "You've got it:" say the person agreed to something. A line that says
    they do not know what to do has agreed to nothing, so it takes the leads written for it, the
    ones that just start them off. Without this, "i am thinking of leaving my husband" then "i
    dont know what to do" was handed "That's the one: Before you decide anything...", which
    answers a question nobody asked.
    """
    leads = LOST_LEADS if AT_A_LOSS.search(str(text or "")) else LEADS
    if A_COUNT_OF_MORE_THAN_ONE.match(str(step or "")):
        leads = tuple(lead for lead in leads if "one thing" not in lead.lower()) or leads
    return leads


def _content(text):
    """The words of a line that name something, in the spelling the two sides can be compared in."""
    return {w for w in topics.words(text or "") if w not in topics.STOPWORDS and len(w) > 2}


def _trouble(text):
    """True when the line is a complaint about the thing still in play, not a fact about it.

    "i cant get my kids to eat veg" is followed by "theyre 4 and 7", and "my dog ate half a bar of
    dark chocolate" by "he's a labrador, about 30 kilos": both are the person handing over what
    the bot asked for, and "Got it - they're 4 and 7" is exactly right. The advice handed back
    instead answers a complaint they did not make. So the line has to say something is still
    going wrong ("cant", "keeps", "still", "worse") before the answer's advice comes back.
    """
    return bool(TROUBLE.search(text or ""))


TROUBLE = re.compile(r"\b(?:can'?t|cant|cannot|won'?t|wont|doesn'?t|doesnt|isn'?t|isnt|"
                     r"keeps?|still|never|again|worse|worst|luck|helping|working|nothing)\b",
                     re.I)

# A thing the person says is their own ("my keys", "our boiler"). When the answer just given never
# names it, the answer is not about the thing the line is about, so there is no part of it to hand
# back: "i keep losing my keys" after a weekend-in-a-city answer was handed the doing part of that
# answer ("One that gets you out of the house - a walk you haven't done..."), which is advice for
# a day out given to somebody looking for their keys. `_trouble` alone cannot tell the two apart -
# "i keep losing my keys" is a complaint about something still going wrong, which is the shape
# that earns the hand-back when the trouble IS the thing the answer was about ("and i honestly
# cant get back off", where the line names no thing of its own).
OWNED = re.compile(r"\b(?:my|our|his|her|their)\s+([a-z]{2,})")


# A limit of somebody else's: what a person in the chat cannot have, cannot eat, or must stay away
# from. It is a fact about a person, which is the store's business, not a detail of the answer just
# given - and handing the answer's advice back for it gives the paragraph the person has just read
# and hears nothing of the limit. After the answer about making a room in a care home theirs
# (a framed photo, their own blanket, a box of their usual sweets) the line "she cant have
# chocolate" came back as that whole paragraph again, sweets and all.
SOMEONE_ELSES_LIMIT = re.compile(
    r"\b(?:he|she|they|him|her|them|mum|mom|mother|dad|father|nan|nana|gran|granny|grandma"
    r"|grandad|grandpa|son|daughter|child|kid|boy|girl|husband|wife|partner|brother|sister"
    r"|friend|baby|toddler|little one)\b[^.!?]{0,60}?"
    r"\b(?:can(?:no|')?t\s+(?:have|eat|drink|take|manage)|cant\s+(?:have|eat|drink|take|manage)"
    r"|cannot\s+(?:have|eat|drink|take)|must\s+not\s+(?:have|eat|drink|take)"
    r"|(?:does|do|did)(?:n'?t|nt|\s+not)\s+(?:eat|drink|like|touch)"
    r"|(?:is|are)(?:n'?t|\s+not)\s+allowed|allergic\s+to|intolerant\s+to|stays?\s+away\s+from"
    r"|has\s+to\s+avoid|cuts?\s+out)\b", re.I)


def _a_thing_of_its_own(line, said):
    """True when the line names a thing as its own that the answer does not mention."""
    named = set(OWNED.findall(str(line or "").lower()))
    if not named:
        return False
    words = set(re.findall(r"[a-z']+", str(said or "").lower()))
    stems = {w.rstrip("s") for w in words}
    return not any(word in words or word.rstrip("s") in stems for word in named)

# A thank-you in front of the line, with the rest of it after a full stop: "cheers. also im skint
# till friday", "thanks. my boiler has packed in". The ack closes the turn the answer belonged
# to, so what follows it opens a new one - it is not a detail on the answer just given. Handed
# back, the person who thanked the bot for the washing-machine fix and then said they were skint
# got the washing-machine fix word for word, which is the thing STYLE.md says never to do twice
# in the same words. Only a courtesy word counts: "ok" and "right" in front of a detail ("ok and
# i honestly cant get back off") are still the same turn being carried on.
ACK_OPENS = re.compile(
    r"^\s*(?:ok(?:ay)?\s+)?(?:thanks|thank you|thankyou|thank u|thx|ty|ta|cheers|cheerz|"
    r"much appreciated|appreciated)\b[^.!?]{0,20}[.!?]+\s*\S", re.I)


# The same ack with a comma after it ("thanks, my back has gone") or at the end of a courtest
# phrase: whatever separates the thank-you from the rest of the line.
ACK_AND_REST = re.compile(
    r"^\s*(?:ok(?:ay)?\s+|right\s+|ah\s+|oh\s+|aw\s+)?"
    r"(?:thanks|thank you|thankyou|thank u|thx|ty|ta|cheers|cheerz|much appreciated|appreciated)"
    r"(?:\s+(?:so|very|much|a lot|again|loads|tonnes))?"
    r"[^a-z0-9]{0,20}"
    r"(?P<rest>[a-z0-9].*)$", re.I | re.S)


def after_an_ack(text):
    """The rest of a line that opens with a thank-you, or "" when it opens with anything else.

    "cheers. also im skint till friday and theres nothing in the fridge" is a thank-you and then
    a line about money; "thanks, that helps" is the thank-you and nothing else. The callers use
    this to read what comes after the courtesy: the knowledge base answers it, and a line that
    only closes the turn has nothing there to answer.
    """
    match = ACK_AND_REST.match(str(text or "").strip())
    if not match:
        return ""
    rest = match.group("rest").strip(" ,.!?;:-\u2014")
    # "thanks love, the boiler is still not firing": the name is said to the bot, not part of the
    # line, so it comes off with the thank-you.
    rest = re.sub(r"^(?:mate|love|pet|hun|hunny|duck|sunshine|chief|fella|sweetheart)\b[,!.]*\s*",
                  "", rest, flags=re.I)
    # A rest that opens with "for" is what the thanks is for, not a line of its own: "thanks for
    # explaining", "thanks for the boiler advice". Read as the line it would be a fragment the
    # knowledge base answers with the advice just given all over again.
    if re.match(r"for\b", rest, re.I):
        return ""
    # What is left has to say something. "thanks, that helps" and "thanks, thats great" are the
    # thank-you and nothing else: read on their own they are words about the answer just given, and
    # the knowledge base would hand back the same paragraph - the red-wine answer said twice
    # because the person said thanks for it.
    named = [word for word in topics.words(rest) if word not in CLOSES_THE_TURN]
    return rest if len(named) >= 2 else ""


# The words a line says thank-you with, and the words a line agrees about it with. What is left
# after they come off is what the person is actually asking about.
CLOSES_THE_TURN = frozenset("""that this it helps helped helping help works worked work working
    does did will would good great fine perfect nice handy useful brilliant lovely amazing awesome
    fantastic ok okay much loads lot lots again everything all so very really too just then now
    know noted needed needs glad cheers thanks please mate love pet
    thats kind kindest thoughtful generous sweet of you""".split())


# A line about the thing going round in their head is about how they are, not a detail of the
# doing: after "ask for a specific figure, with the reason attached" a person says "i keep going
# over it in my head at 2am", and the same sentence handed back word for word answers the pay rise
# and not the 2am. The shapes are the ones people use for trouble that will not leave them alone -
# the head, the mind, being awake - and none of them points at anything in an answer to do.
BROODING = re.compile(
    r"\b(?:"
    r"(?:going|goes|went)\s+(?:over|round|around)\b|"
    r"round\s+in\s+(?:my|our)\s+(?:head|mind)|\bin\s+my\s+head\b|\bon\s+my\s+mind\b|"
    r"(?:cant|can'?t|cannot|keep|keeps|kept)\s+(?:stop\s+)?thinking\b|"
    r"think(?:ing)?\s+about\s+it\b|\bthoughts?\s+(?:racing|going)\b|"
    r"my\s+mind\s+(?:is\s+)?(?:racing|going|spinning)"
    r")", re.I)


def _a_feeling(text):
    """True when the line is about how they are, not about the thing the answer was about.

    "i lost my job last week" is answered with what to check in the offer, and the next line,
    "i cant stop crying", is not a question about the offer: handing back "ask for it in writing
    and don't sign it on the day" reads as if nobody had heard the crying. The feeling words are
    the ones the fallback already reads a bad week by, so the two cannot drift apart. A line about
    the trouble following them about (BROODING) is how they are too, even with no feeling word in
    it: "i keep going over it in my head at 2am" is the part of the evening the answer never
    spoke to.
    """
    from ..compose.fallback import NEGATIVE_CUES

    if BROODING.search(text or ""):
        return True
    return bool(set(topics.words(text or "")) & NEGATIVE_CUES)


def _the_doing(sentence):
    """The doing part of a sentence: what follows a short label, and cut to a length that is a
    reply rather than a paragraph.

    "The fix is what you do in those minutes: do not check the clock, keep the light off, and if
    you are properly awake after about twenty minutes get up and sit somewhere dim ..." is advice
    with a label in front of it; on its own the label says nothing about the sleeping, so the part
    after the colon is what the person gets, with its first letter raised because it now opens
    the reply.
    """
    head, sep, rest = str(sentence).strip().partition(":")
    # A label in front of the advice is dropped ("The fix is what you do in those minutes: ..."),
    # but a sentence that itself opens on a doing is an instruction, not a label: "Check the salt
    # and rinse aid too: running out of either makes everything come out cloudy" is the check, and
    # the part after the colon only says why. Handing back the reason would answer a person who
    # asked for the next step with something to do nothing about.
    if sep and not _opens_a_doing(head) and len(head.split()) <= 12 and len(rest.strip()) >= 20:
        whole = rest.strip()
        whole = whole[0].upper() + whole[1:]
    else:
        whole = str(sentence).strip()
    whole = a_whole_cut(whole, MOST)
    last = whole.rstrip("'\"\u2019\u201d")
    return whole + "." if whole and not last.endswith((".", "!", "?")) else whole


def _the_advice(said):
    """The sentence of an answer that tells them what to do, or None when it tells them nothing.

    "The fix is what you do in those minutes: do not check the clock, keep the light off, and if
    you are properly awake after about twenty minutes get up ..." is the most of an instruction in
    that answer, and it is the part a person who says "i cant get back off" can use. A sentence of
    explanation ("Waking in the night is normal") has nothing to do in it, so it is never picked.
    """
    from ..compose.verdict import IMPERATIVES  # the verbs an instruction can open on

    best, most = "", 1
    for part in [p.strip() for p in SENTENCE.split(str(said).strip()) if p.strip()]:
        if topics.RED_FLAG.match(part) or ASKING_THEM.search(part):
            continue
        words = [w.strip(" ,;:.") for w in part.lower().split()]
        count = sum(1 for w in words if w in IMPERATIVES)
        count += 1 if re.search(r"\bdo not\b|\bdon'?t\b", part, re.I) else 0
        if count > most:
            best, most = part, count
    return best


def the_next_move(memory, text=""):
    """The step after advice the person says did not work, in the answer's own words, or "".

    A report on the advice is answered by the composer, and its pools say "change one thing
    instead" - advice to change, which the person in front of it has already done. When the answer
    itself ends on who to go to if the advice is not enough ("ask a GP", "call a Gas Safe
    engineer"), that sentence is the next move and it is the one thing left to say. Nothing is
    invented here: it is the answer's own closing sentence, said once (a step already repeated
    gets "" and the composer's own line stands).
    """
    for back, asked, said in _recent_answers(memory):
        if back > 1 and not _about_the_same_thing(asked, said, memory):
            continue
        if NEXT_STEP_EMERGENCY.search(said):
            # Nothing is handed back from an emergency answer, and nothing older is reached past
            # it: the composer's own emergency line is the only next move that is true.
            return ""
        step = _next_step(said)
        if step and not _already_repeated(step, memory):
            step = step[:1].upper() + step[1:]
            return pick(TRIED_LEADS, memory, text or "").format(step=step)
        return ""
    return ""


def _next_step(said):
    """The sentence an answer ends on about who to go to, when the advice alone is not enough."""
    sentences = [s.strip() for s in SENTENCE.split(str(said or "")) if s.strip()]
    for sentence in reversed(sentences[1:]):
        if NEXT_STEP.search(sentence):
            return sentence
    return ""


def _later_part(tried, said):
    """The part of one answer that comes after the step the line says it has tried."""
    def shared(part, words):
        return sum(1 for w in _content(part)
                   if any(w == v or (len(w) >= 5 and len(v) >= 5 and w[:5] == v[:5])
                          for v in words))

    parts = [p.strip() for p in SENTENCE.split(str(said).strip()) if p.strip()]
    tried_words = _content(tried)
    best_i, most = -1, 0
    for i, part in enumerate(parts):
        count = shared(part, tried_words)
        if count > most:
            best_i, most = i, count
    if best_i >= 0:
        # The tried step is in the answer: the sentence right after it is the next step, not
        # whatever later sentence happens to share the fewest words (that can be another part of
        # the answer, such as the patio paragraph after the lawn one).
        later = []
        for part in parts[best_i + 1:]:
            if topics.RED_FLAG.match(part) or ASKING_THEM.search(part):
                continue
            if shared(part, tried_words) >= most:
                continue
            doing = _the_doing(part)
            if len(doing) >= 25:
                later.append(doing)
        # Not every later sentence is a step. An answer often puts how long the step takes
        # between the step and the next one ("... clean the filter and the detergent drawer
        # while it runs. The wash itself is about two hours. Leaving the door and drawer open
        # between washes is what stops the smell coming back"), and handing back the timing
        # reads as advice given to someone who asked for the next move. The sentence that opens
        # on a doing is the step; the timing is skipped, and the first qualifying sentence is
        # still the answer when none of them opens on one.
        for doing in later:
            if _opens_a_doing(doing):
                return doing
        return later[0] if later else ""
    # The step is not named in the answer ("ive tried bleach" against a drain answer that says
    # chemical cleaner): the last sentence is the part they have not heard yet.
    best = ""
    for part in parts[1:]:
        if topics.RED_FLAG.match(part) or ASKING_THEM.search(part):
            continue
        doing = _the_doing(part)
        if len(doing) >= 25:
            best = doing
    return best


def _opens_a_doing(sentence):
    """Whether a sentence opens on a doing rather than on its subject.

    "Leaving the door and drawer open between washes is what stops the smell coming back" opens
    on the habit to keep, and "The wash itself is about two hours" opens on the wash: the first
    is something to do, the second is how long the thing they just did takes. The test is the
    first word - an instruction's verb, or the "-ing" form of one, which is how an answer says a
    step that is a habit rather than a one-off.
    """
    from ..compose.verdict import IMPERATIVES

    words = str(sentence).strip(" .,:;").split()
    if not words:
        return False
    first = words[0].lower().strip(".,;:")
    if first in IMPERATIVES or first in MOVE_VERBS:
        return True
    if first.endswith("ing") and len(first) > 4:
        stem = first[:-3]
        bare = [stem, stem + "e"]
        if len(stem) > 2 and stem[-1] == stem[-2]:
            bare.append(stem[:-1])
        return any(candidate in IMPERATIVES for candidate in bare)
    return False


def _the_untried(tried, memory):
    """The later part of the last answer that is not the step they have just tried.

    "my sourdough is flat" / "i tried the starter and it still flopped" used to stand down to a
    filler, but the answer's last sentence is the next diagnosis, not the step they tried. The
    same is true of "ive tried the filter and the drawer": the answer's later sentence - leave the
    door open - is what is left to do. Only a later sentence qualifies: a one-sentence answer has
    no next step to hand back.
    """
    for back, _question, said in _recent_answers(memory):
        if back != 1:
            return None
        best = _later_part(tried, said)
        if best and not _already_repeated(best, memory):
            return _handed_back(memory, best)
    return None


# A line that says the step has already been done is not picking the step out of the answer: it
# is telling the bot the advice did not work. Handing the same step back reads as if nobody had
# listened ("ive tried a hot wash already" got the service-wash sentence again), so the answer
# hands back its later step instead; only the line that asks nothing new stands down.
TRIED = re.compile(r"\b(?:i|we|he|she|they)\s+(?:already\s+)?(?:tried|done)\b|"
                   r"\b(?:i(?:'ve|ve| have)|we(?:'ve|ve| have)|he(?:'s|s| has)|"
                   r"she(?:'s|s| has)|they(?:'ve|ve| have))\s+(?:already\s+)?"
                   r"(?:tried|done|had)\b|\balready\s+(?:tried|done|had)\b|"
                   r"\b(?:tried|done)\s+(?:that|it|this)\b", re.I)
# Only a negation of the attempt itself ("i haven't tried", "never done") keeps the advice.
# A later "it did not work" is the reason to say it was tried, not a claim that it was not.
NOT_TRIED = re.compile(r"\b(?:not|never|havent|hasnt|didnt|haven't|hasn't|didn't)\s+"
                       r"(?:\w+\s+){0,2}(?:tried|done|had)\b", re.I)
# A line that says the step was tried and then asks about another part of the same answer is
# still a follow-up ("ive done the vinegar, how long should i leave the citric acid"). The
# stand-down is only for the line that asks nothing new.
QUESTION_MORE = re.compile(r"\b(?:how|what|when|why|which|should)\b", re.I)


def _tried(text):
    """True when the line says the advice has already been carried out, not that it failed."""
    return bool(TRIED.search(text or "")) and not NOT_TRIED.search(text or "")

def _says_they_agree(clean):
    """Whether the line carries a word that agrees: "ok so low heat then", "low heat, got it".

    A line that happens to sit inside one sentence of the answer word for word is not always an
    agreement: "the washer is old" after the dripping tap answer is the person telling the bot
    something, and saying it back ("Yes - the washer is old.") is the bot parroting them. What
    makes a line an agreement is the word in it that agrees - ok, so, then, got it, right - so
    that is what is asked for.
    """
    words = [word.strip(".,!;:\"'").lower() for word in clean.split()]
    if any(word in AGREES_ON_ITS_OWN for word in words):
        return True
    if AGREES_IN_A_PHRASE.search(clean):
        return True
    # A joining word on its own is not a yes, and the line it starts is often another item
    # altogether ("and for hard boiled", "and a root canal"). The word a person puts after a
    # thing they are agreeing with is the yes: "so low heat then", "low heat as well".
    return len(words) <= 8 and bool(words) and words[-1] in AGREEMENT_TAIL


def _the_thing_they_named(clean, part):
    """The words of the line that are the answer's own, in the person's order: "low heat".

    "ok so low heat then" is the answer's sentence with an agreement round it, and the thing the
    person said is the part of it they named. The agreement words come out, so the reply names the
    thing rather than repeating the agreement back at them. Every other word stays as they said
    it, including one with no stem of its own ("same time every day"), because the line has
    already been matched against the answer and those are the words they chose.
    """
    kept = []
    for word in clean.split():
        bare = word.strip(".,!;:\"'").lower()
        if not bare or bare in AGREEING:
            continue
        # The line has already been matched against the answer, so the words left are the ones
        # the person named: a word with no stem of its own ("same", "every") is still theirs to
        # say back. Only the agreement comes out.
        kept.append(word.strip(".,!;:\"'"))
    # A thing said with the copula in front of it is still the thing: "it was black mould" after
    # the grout answer named the mould, and the confirmation came out as "Was black mould, yes."
    # - the copula capitalised into the reply as if it were part of the name.
    while len(kept) > 1 and kept[0].lower() in BE_FORM | POINTING_AT:
        kept = kept[1:]
    if not kept or len(kept) > 4 or kept[0].lower() in BE_FORM | POINTING_AT:
        return ""
    # A line that opens on a preposition is a detail of the answer rather than a thing it named
    # ("it was in a big pot" after the repotting advice), so there is nothing to say back: the
    # confirmation of it ("In a big pot, yes.") tells the person nothing they did not just say.
    if kept[0].lower() in OPENERS:
        return ""
    return " ".join(kept)


def agreement_with_the_answer(text, memory):
    """The confirmation of a thing the person has just said back, or "" for every other line.

    "ok so low heat then" is answered by `carried_on`, but a second agreement - "low heat, got
    it", a turn later - is answered before that: the answer it agrees with is now two turns back,
    the lookup reads the named thing as the thing to answer about, and the whole paragraph comes
    out again, which is the answer the person has just agreed with. The answer modules call this
    first, the way they call `asks_for_the_same_work`, so the confirmation is what they get.
    """
    clean = (text or "").strip()
    if (not clean or clean.endswith("?") or QUESTION.match(clean) or ASKS.match(clean)
            or len(clean.split()) > 20):
        return ""
    if ABOUT_THE_BOT.search(clean) or WORDS_WANTED.search(clean):
        return ""
    asked = _content(clean)
    if len(asked) < 2:
        return ""
    for back, question, said in _recent_answers(memory):
        if back > 1 and not _about_the_same_thing(question, said, memory):
            continue
        best, shared = "", 0
        for part in [p.strip() for p in SENTENCE.split(said) if p.strip()]:
            if topics.RED_FLAG.match(part) or ASKING_THEM.search(part):
                continue
            count = len(asked & _content(part))
            if count > shared:
                best, shared = part, count
        if shared < len(asked) or not _says_they_agree(clean):
            continue
        named_thing = _the_thing_they_named(clean, best)
        if named_thing:
            return _agreed(named_thing, memory)
    return ""


def _agreed(named, memory):
    """The confirmation of a thing the person said back: "Low heat, yes."

    Every line names the thing, so the pool cannot be read out to anybody else, and the answer
    just given is never one of them.
    """
    low = named[:1].lower() + named[1:]
    up = named[:1].upper() + named[1:]
    return pick([up + ", yes.",
                 "Yes \u2014 " + low + ".",
                 up + " it is.",
                 "That's it: " + low + ".",
                 up + ", that's the main thing."], memory, named)


# A step said in the past tense is a step tried. "i topped it up yesterday", "i did the hot wash",
# "i changed the washer already" report the same news as "ive tried topping it up": the advice did
# not work, and handing it back - or asking "what made you start on that?" - reads as if nobody
# had listened. The gate is the act, not the word (TRIED above only knows the words tried, done
# and had): the past tense has to name a step the answer just gave, so a past tense about anything
# else ("i paid the bill", "i walked to work") is still the person's own news.
DONE = re.compile(
    r"\b(?:i|we|he|she|they)\s+(?:(?:have|had|already|just|finally|now|then|since)\s+)*"
    r"(?P<verb>[a-z]+)\b", re.I)
# The past forms that are not spelled with -ed.
IRREGULAR_PAST = {
    "did": "do", "done": "do", "made": "make", "took": "take", "given": "give", "got": "get",
    "left": "leave", "kept": "keep", "cut": "cut", "put": "put", "set": "set", "ran": "run",
    "bled": "bleed", "hung": "hang", "wore": "wear", "fed": "feed", "found": "find",
    "built": "build", "sent": "send", "spent": "spend", "threw": "throw", "dug": "dig",
    "held": "hold", "lit": "light", "swept": "sweep", "bought": "buy", "caught": "catch",
    "taught": "teach", "told": "tell", "sold": "sell", "froze": "freeze", "drew": "draw",
    "shut": "shut", "spread": "spread", "paid": "pay", "struck": "strike", "shook": "shake",
}
NO_LONGER_TO_DO = frozenset("""not never no havent hasnt didnt doesnt dont wont cant
    haven't hasn't didn't doesn't don't won't can't""".split())


def _the_stems(word):
    """The base verbs an -ed form could have come from ("topped" -> top, "dried" -> dry)."""
    word = str(word or "").lower()
    out = set()
    if word.endswith("ied") and len(word) > 4:
        out.add(word[:-3] + "y")
    if word.endswith("ed"):
        base = word[:-2]
        out.add(base)
        out.add(base + "e")
        if len(base) > 2 and base[-1] == base[-2]:
            out.add(base[:-1])
    elif word.endswith("d") and len(word) > 3:
        out.add(word[:-1])
    return out


def _the_act(word):
    """The step a word names in the past tense, if it is one an instruction can open on."""
    from ..compose.verdict import IMPERATIVES  # the verbs the base says a step with

    base = IRREGULAR_PAST.get(word)
    if base and (base == "do" or base in IMPERATIVES):
        return base
    for stem in _the_stems(word):
        if stem in IMPERATIVES:
            return stem
    return None


# A word that stands in for the answer's thing rather than naming another one: "i topped it up"
# is the boiler, "i bled them" the radiators. The object of a past tense that is one of these
# says nothing new, so the act alone is enough.
STANDS_IN = frozenset("it them that this one ones those these there".split())
# Where the object of a past-tense verb ends: a preposition opens the rest of the line ("i topped
# it up for the second time"), and a time word or a joining word is not the thing done.
OBJECT_END = frozenset("""for to in on at with by from into onto and but then so because when
    while before after again twice once already yesterday today tonight now later still
    earlier this morning evening week month year""".split())


def _the_object(clean, at):
    """The thing a past tense was done to, as words to find in the answer; None if it says none.

    "i topped up my phone" is the phone and not the boiler, "i bled my knee" is the knee and not
    the radiators, so what follows the verb has to be read or the act alone hands back the next
    step of a job the person never did. A pronoun is not a new thing ("i topped it up"), so it
    says nothing and the act is left to decide.
    """
    tail = []
    for word in str(clean or "")[at:].lower().replace(",", " ").split():
        bare = word.strip(" .;:!?()[]\"")
        if not bare or bare in OBJECT_END:
            break
        if bare in STANDS_IN:
            return None
        tail.append(bare)
    said = frozenset(word for word in tail if len(word) > 2 and word not in topics.STOPWORDS)
    return said or None


def _the_steps_done(text):
    """The steps a line reports having done: the act, and the thing it was done to if it names one."""
    acts = set()
    clean = str(text or "")
    for match in DONE.finditer(clean):
        before = clean[:match.start()].lower().split()[-3:]
        if any(w.strip(" ,.;:!?'") in NO_LONGER_TO_DO for w in before):
            continue  # "i havent cleaned the filter" is the step still to do
        act = _the_act(match.group("verb").lower())
        if act:
            acts.add((act, _the_object(clean, match.end())))
    return acts


def _the_answer_gives(said, act):
    """Whether the answer just given is the one that named the step."""
    for word in str(said or "").lower().replace("'", "").split():
        word = word.strip(" ,.;:!?()[]\"")
        if word == act or act in _the_stems(word):
            return True
    return False


def _a_step_done(text, said):
    """True when the line reports doing a step of the answer just given.

    The step is the answer's, not the word list's: "i changed the washer already" is a step when
    the answer said "take the old part to a hardware shop" and not when the chat is about
    something else. A step named by its object rather than its verb ("i did the hot wash") counts
    too, and only for the empty verb - "do" is not a step any answer says, so the word that has to
    be in the answer is the thing done.
    """
    acts = _the_steps_done(text)
    if not acts or not said:
        return False
    given = _content(said)
    for act, thing in acts:
        # "i did the hot wash" names its step by the thing done - "do" is not a verb any answer
        # uses, so the object is the only way in.
        by_object = act == "do"
        if not by_object and not _the_answer_gives(said, act):
            continue
        if thing is None:
            # A pronoun or no object ("i topped it up", "i bled them"): the answer's thing, by
            # the act alone. A bare "i did it" names nothing, so it is not the step.
            if not by_object:
                return True
            continue
        # The act has to be of the answer's thing as well as in its words: "i topped up my
        # phone" after the boiler answer is not the boiler topped up, and handing back the next
        # boiler step tells the person to stop doing something they never did.
        if thing & given:
            return True
    return False


def _the_step_just_given(text, memory):
    """True when the line reports doing a step of the answer one turn back."""
    for back, _question, said in _recent_answers(memory):
        return back == 1 and _a_step_done(text, said)
    return False


# The words that make a line a rejoinder to the answer above rather than a report of its own: the
# person is defending or adding to what they already do ("i do that too", "i go to bed at the same
# time every night though", "but i already walk the dog").
REJOINDER = re.compile(r"\b(?:though|although|already|but|anyway|still|mind you|to be fair)\b",
                       re.I)


def carried_on(text, memory):
    """The reply to a line that picks up a detail of the answer just given, or None.

    "ive been waking up at 4 every night" is answered with the advice - the clock, the light, get
    up after twenty minutes. The next line, "and i honestly cant get back off", names the detail
    they mean and says nothing the answer does not already cover, so the honest reply is the part
    of that answer that speaks to it. What it got was "Thanks for telling me - I'm here if you
    want to dig into any of that", which would fit any message anybody ever sent.

    The rule is narrow on purpose:
    * the line has to name at least two things of its own, and they have to be in one sentence of
      the answer, so a line about something else never comes here;
    * it is a statement, not a question - a question has the modules of its own;
    * only the answer just given counts, or, a turn older, one the chat is still on;
    * a part already handed back once is not handed back again.
    """
    # A reset lead is taken off only when what follows it is a question of its own: "nvm, whats
    # the tax deadline" asks something new, and the old answer must not be searched for it. A
    # detail that refines the old subject ("nvm, i mean the carpet" after a stain) is not a new
    # question, and the answer is what tells the carpet from the stain, so the lead is left on.
    clean = (text or "").strip()
    asked_after = without_a_reset(clean)
    if QUESTION.match(asked_after) or ASKS.match(asked_after):
        clean = asked_after
    if (not clean or clean.endswith("?") or QUESTION.match(clean) or ASKS.match(clean)
            or len(clean.split()) > 20):
        return None
    if ABOUT_THE_BOT.search(clean) or WORDS_WANTED.search(clean):
        return None
    if ASKING_TO_START.search(clean):
        # The line names the stall and asks for the first move: "my daughter has a project about
        # the water cycle" / "she is 8 and keeps putting it off". A sentence of the answer can
        # share the words ("a project is marked on...") without telling them how to begin, and
        # handing that back is the answer they already have. The chat and knowledge readers have
        # a first move for this, so the detail reader stands aside.
        return None
    if ACK_OPENS.match(clean):
        return None  # a thank-you ends the turn: what follows it is a new ask, not this answer
    if limits.names_a_limit(clean):
        # "she cant walk far" is a fact about the person's mum, not a detail of the answer on the
        # screen: the hosting answer says nothing about walking, and handing its first sentence
        # back read the same sentence twice. The composer has a reply for a limit of its own
        # ("She can't walk far - so anything I suggest stays short and flat, with somewhere to
        # sit."), and the limit has to reach it.
        return None
    if not QUESTION_MORE.search(clean) and (_tried(clean) or _the_step_just_given(clean, memory)):
        return _the_untried(clean, memory)
    if isinstance(memory, dict) and (memory.get("understood") or {}).get("routine") \
            and not REJOINDER.search(clean):
        # A routine the person reports names its own subject and says something whole about it:
        # "im trying to lose a stone" / "i walk the dog every day" was handed the diet answer back
        # because a sentence of it happens to say "walk" and "day", and the person's own line went
        # unanswered. The habit tail answers it (bot/memory/ack.py::_plain).
        #
        # A rejoinder is the other case: "i go to bed at the same time every night though" is the
        # person saying the step already given is the one they take, and the answer to it is that
        # step again, so a line that argues with the answer keeps the reader.
        return None
    asked = _content(clean)
    if len(asked) < 2:
        return None
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    # The line that asks which part to do first is the one ask that a pointer back has not
    # already answered: "i keep burning the bottom of my pans" / "what am i doing wrong" (the
    # answer again, under a lead) / "how do i clean it off" wants the first clause of that
    # answer and has never had it, so the pointer guard leaves this ask alone.
    which_part = asks_for_the_move(text)
    if turns and not which_part and REFER_BACK.search(str(turns[-1].get("bot") or "")):
        return None
    for back, question, said in _recent_answers(memory):
        if back > 1 and not _about_the_same_thing(question, said, memory):
            continue
        best, shared = "", 0
        for part in [p.strip() for p in SENTENCE.split(said) if p.strip()]:
            if topics.RED_FLAG.match(part) or ASKING_THEM.search(part):
                continue
            count = len(asked & _content(part))
            if count > shared:
                best, shared = part, count
        if shared < 2:
            # The line names something the answer does not put in words ("and i honestly cant
            # get back off" against "do not check the clock, keep the light off, and if you are
            # properly awake ..."), so there is no sentence to match on. The chat is still on the
            # thing the answer was about, and what a friend does then is say the doing part of it
            # again, which is the sentence with the most telling-them-what-to-do in it.
            best = (_the_advice(said) if back == 1 and _trouble(clean) and not _a_feeling(clean)
                    and not _a_thing_of_its_own(clean, said)
                    and not SOMEONE_ELSES_LIMIT.search(clean) else "")
            if not best:
                continue
        elif shared >= len(asked) and _says_they_agree(clean):
            # Every word of the line is in that one sentence: the person has just said the answer
            # back, as people agree - "ok so low heat then" after "cook them low and slow".
            # Handing the same sentence back is the bot talking to itself: they agreed, they did
            # not ask again. The reply is the confirmation, which is the thing they named and
            # nothing else, so it also cannot be a line that would fit any message.
            named = _the_thing_they_named(clean, best)
            if named:
                return _agreed(named, memory)
        doing = _the_doing(best)
        if len(doing) < 25 or _already_repeated(doing, memory):
            continue
        # No lead in: "do not check the clock, keep the light off, ..." answers the line in its
        # first words, and a stock "that is the bit that counts" in front of it says nothing the
        # person did not already know.
        return _handed_back(memory, doing)
    return None

# The same rules for another reader of that turn (bot/memory/more.py): an ask to carry on needs
# the answer the bot just gave, the same guard that the chat has not moved on, and the same
# memory of what has already been handed back. Exposed rather than copied, so the two readers
# cannot drift apart on what counts as an answer or what counts as said twice.
recent_answers = _recent_answers
same_subject = _about_the_same_thing
said_recently = _already_repeated
handed_back = _handed_back

# A line that names a stall and asks to get going. It is an ask for a step, not a detail of the
# answer just given, so `carried_on` leaves it to the readers that know one: "she is 8 and keeps
# putting it off" after a project answer was handed the sentence about the marking, which is the
# problem already on the screen.
#
# Only a stall about somebody else: "she is 8 and keeps putting it off", "he doesnt know how to
# start". A stall about the person's own plan is a detail of that plan - "how do i boil an egg" /
# "i keep putting it off" wants the cooling step, and "i want to start running" / "i cant get
# started" wants the walk-jog - so a first-person stall keeps the detail reader.
_A_STALL = (r"(?:keeps? putting (?:it |things )?off|puts? (?:it |things )?off"
            r"|putting (?:it |things )?off|keeps? avoiding (?:it|them|this)"
            r"|does not know (?:how|where) to start"
            r"|doesn[\u2019']?t know (?:how|where) to start|not sure (?:how|where) to start"
            r"|can[\u2019']?t get started|cannot get started|has not started|hasn[\u2019']?t started"
            r"|not even started|leaves? it to the last minute|hates? starting)")
ASKING_TO_START = re.compile(
    r"(?:\b(?:he|she|they)\b|\bthe (?:kids?|children)\b"
    r"|\bmy (?:son|daughter|child|kid|boy|girl|mum|mom|dad|father|mother|partner|husband|wife"
    r"|brother|sister|friend|nephew|niece|grandson|granddaughter)\b)"
    r"[^.!?]{0,30}?\b" + _A_STALL + r"\b", re.I)

# A line that asks which part of the answer to do, narrowly: "where do i start", "what should i
# do first", "how do i begin". The wider MOVE_ASK above also catches a plain repeat ("how long
# do i boil them" has the word "do" in it), which wants the answer again, not a step.
# The ask, not the word: "how did we start the fire in the wood burner" is a question about
# something they did, and reading it as "where do i start" handed the step of an unrelated answer
# over. The order that follows is what makes it this ask.
START_ASK = re.compile(r"\b(?:where|how)\s+(?:do|does|should|shall|can|could|would|might|to)\s+"
                       r"(?:(?:i|we|you)\s+)?(?:start|begin)(?:ed|ing)?\b|"
                       r"\bhow do (?:i|we) get (?:started|going)\b|"
                       r"\b(?:do|try|change|fix|sort|put|write|tackle|get)\s+first\b|"
                       r"\bfirst (?:thing|step|move)\b|\bnext step\b", re.I)

# A start/begin that names what it starts is the line's own question, not a lean on the answer in
# hand: "how do i start running" is about running, and the knowledge base has the row for it, but
# read as "where do i start" it was handed the first step of whatever the turn before had said
# (@ochre-mango, #answers). The ask ends at the start, or points back with a pronoun ("start it",
# "start with this") or a word that adds nothing to start ("start again", "start small").
STARTING_WHAT = re.compile(
    r"\b(?:where|how)\s+(?:do|does|should|shall|can|could|would|might|to)\s+"
    r"(?:(?:i|we|you)\s+)?(?:start|begin)(?:ed|ing)?\s+([a-z']+)(?:\s+([a-z']+))?", re.I)

# The words after start/begin that point back at the answer rather than naming a thing to start.
STARTING_BACK = frozenset("""
it this that them these those one again over now today here then though please anyway
small slowly simple easy gently early off out up
""".split())
STARTING_AT = frozenset(("with", "on", "about"))

# "start out" and "start off" name nothing on their own, so the ask reads as the bare one - but
# only when nothing follows them: "how do i start out in gardening" starts out *in gardening*, and
# "how do i start out on my own" in a business. Read as the bare ask, a person trying a few
# hobbies in a row was answered from the answer before it ("start out in running", then "start out
# in gardening" told to jog), and "start out in the morning" was handed the card from the line
# before (@clever-latch, #answers). A preposition after it asks for the word after that one, the
# same way the bare ask looks past "with" and "on"; anything else after it is the thing started.
STARTING_OUT = re.compile(
    r"\b(?:start|begin)(?:ed|ing)?\s+(?:out|off)\s+([a-z']+)(?:\s+([a-z']+))?", re.I)
STARTING_INTO = frozenset(("in", "into", "at", "for", "as"))


def _starting_out_names_a_thing(line):
    """True when what is started out *into* is in the line: "start out in gardening"."""
    found = STARTING_OUT.search(line)
    if found is None:
        return False
    first, second = found.group(1), found.group(2) or ""
    if first in STARTING_INTO or first in STARTING_AT:
        return bool(second) and second not in STARTING_BACK
    return first not in STARTING_BACK


def says_where_to_start(text):
    """START_ASK for a line that asks which part of the answer to do first, and names no starting.

    "Where do i start", "how do i begin with it" and "what should i do first" lean on the answer
    in hand. "How do i start running", "how do i start saving", "how do i start learning guitar"
    and "how do i start out in gardening" name a thing of their own and are answered by the entry
    for it.
    """
    line = str(text or "")
    if not START_ASK.search(line):
        return False
    if _starting_out_names_a_thing(line):
        return False
    found = STARTING_WHAT.search(line)
    if found is None:
        # A start ask leans on the answer in hand only when the line names nothing of its own:
        # "where do i start" and "what should i try first" do, while "my laptop keeps dropping
        # the wifi in the back room, what should i try first" names a laptop and a wifi, and it
        # was handed the first step of the sleep answer given the turn before. A line with a
        # context clause in it is a question about that context, whatever it asks at the end.
        return len(_names_a_thing_of_its_own(line)) < 2
    first, second = found.group(1), found.group(2) or ""
    if first in STARTING_AT:
        return not second or second in STARTING_BACK
    return first in STARTING_BACK

# "what else can i do", "anything else i can try", "and what else": one more thing out of the
# answer just given. A line with a thing of its own in it keeps its own answer, so this is only
# read where the answer is what the line leans on.
MORE_ASK = re.compile(r"\bwhat else (?:can|could|should|would) (?:i|we)\b|"
                      r"\bwhat else (?:is there|works|helped|helps|do i do)\b|"
                      r"\banything else (?:i|we) (?:can|could|should) (?:do|try)\b|"
                      r"\bis there anything else\b|"
                      # "what else could it be" asks for another explanation of the trouble, not
                      # for another thing to do, so the step of the last answer is not the reply.
                      r"\b(?:and )?what else\b(?!\s+(?:could|would|might|is|are|was|were)\s+it\b)",
                      re.I)

# "any ideas", "what do you suggest", "what would you pick", "any other suggestions": the same ask
# as "what else", in the words people use when they want an option rather than another thing to do.
# They name nothing of their own, so no entry can answer them, and until this reading they fell to
# the plain hedge ("That's most of what I know on it", "A search should sort you out quickly") a
# turn after the subject had been answered in full - the aimless turn a friend never gives.
# The whole line has to be the ask: "any ideas for a day out with the kids" names a subject of its
# own, and the entries for it answer from its own words.
IDEAS_ASK = (r"anything (?:else|more|other)|"
             r"(?:any|some) (?:other |more |different )?"
             r"(?:ideas?|suggestions?|thoughts?|recommendations?|options?|tips?)|"
             r"what (?:do|would|can|should) you (?:suggest|recommend|pick|choose|go for|advise)|"
             r"what would you (?:pick|choose|go for|do)|"
             r"your (?:ideas|suggestions|thoughts|recommendations)|"
             r"ideas|suggestions")
IDEAS_ONLY = re.compile(
    r"^\W*(?:(?:and|so|ok|okay|right|well|alright|then|but)\b[\s,]+)*(?:" + IDEAS_ASK + r")" +
    r"\W*(?:[\s,]+(?:then|please|now|tho|though|thanks|ta))?\W*$", re.I)


def a_more_ask(text):
    """Whether the line asks for the next part of the answer in hand, said either way."""
    said = str(text or "")
    return bool(MORE_ASK.search(said) or IDEAS_ONLY.match(said))


# The same ask written with the doing in it: "how do i clean it off", "how do i get rid of the
# smell", "how do i fix it". The pronoun is what makes it the answer's own business; a line that
# names a thing of its own ("how do i clean a cast iron pan") has its own entry and its own answer.
# "how do i word it", "how do i say no", "how do i explain it": a line about the saying, not
# about the doing. The step of the last answer is not the answer to it - there is a module that
# puts the words together - so the move steps aside and leaves the turn to it.
# "Bring it up", "raise it", "mention it" are the same ask: they name no words and no doing, so
# they are listed beside the verbs that say the saying outright. Only a pointed-back object counts
# ("raise the money" is a doing), which keeps the reading narrow.
WORDING = re.compile(r"\bhow (?:do|can|should|could|would|might) (?:i|we)\s+(?:"
                     r"(?:word|write|say|phrase|put|explain|draft|reply|tell|ask|answer)\b"
                     r"|(?:bring|raise|mention|broach|approach)\s+"
                     r"(?:it|that|this|them|the (?:subject|issue|matter|problem))\b"
                     r")", re.I)

HOW_IT = re.compile(r"\bhow (?:do|can|should|could|would|might|shall) (?:i|we)\s+"
                    r"(?:[a-z']+\s+){0,3}(?:it|that|this|them|these|those)\b", re.I)


def _places_to_cut(head):
    """Where a long instruction could end: at a qualifier, or at a bracket that explains it.

    A qualifier that is the last word leaves nothing to cut, and one that is followed by a
    preposition ("put a bowl under it and turn the water off at the stopcock") is the second half
    of the phrase rather than its end, so both are passed over.
    """
    spots = []
    for found in QUALIFIER.finditer(head):
        after = head[found.end():].strip().split()
        if not after:
            continue
        if after[0].lower() in OPENERS:
            continue
        spots.append(found.start())
    for index, char in enumerate(head):
        if char == "(" and ")" in head[index:]:
            spots.append(index)
    return sorted(set(spots))


def _inside_a_bracket(text, at):
    """Whether the character at `at` sits inside a bracket that has not closed by then."""
    return text.count("(", 0, at) > text.count(")", 0, at)


# A list item that is a fact about the world rather than a thing to do is not a step: "the rent is
# due on friday" says how things are, and "same wake-up time every day" says what to do.
# What the words before a colon say the list is: a list of things that work or things to do is the
# answer's instructions, a list of things to learn or of objects is not.
LIST_LEAD = re.compile(r"\b(?:works?|working|helps?|helped|things to do|to do|steps?|rules?|"
                       r"habits?|ways?|tips?|start|begin|try|keep|stick to|do these|do this)\b",
                       re.I)

# A lead that says what the tail is rather than how to do it announces a list of things, and a
# list of things is not the method: "learn four things and the rest follows: pasta with a sauce,
# an omelette, a tray of roasted vegetables" names dishes to try, and handing the first of them over
# as the step ("learn four things and the rest follows: pasta with a sauce") answers nothing.
NOT_A_TAIL = re.compile(r"\b(?:things|rest|following|list|these|those|steps|rules|ways|tips|"
                        r"habits|ideas|examples|reasons)\b", re.I)

NOT_A_DOING = re.compile(r"\b(?:you|your|i|we|they|he|she|it|its|their)\b|"
                         r"\b(?:is|are|was|were|has|have|had|means|meant)\b", re.I)


def _a_list_item(part):
    """The first item of a list the answer gives after a colon, when no item opens on a verb.

    "The things that work: same wake-up time every day, no caffeine after early afternoon, a cool
    dark room" is three things to do and not one of them opens on a verb, so a reader that wants
    the verb first found nothing in it and went on to the next sentence - "ask a GP", which is the
    last resort at the end of the answer, not the first thing to do.
    """
    if ":" not in part:
        return ""
    lead = part.split(":")[0]
    if not LIST_LEAD.search(lead):
        # "Learn four things and the rest follows: pasta with a sauce, an omelette": the list is a
        # set of things the answer names, not the things to do, and its first item is a dish. The
        # sentence that says what to do with them is the one after it.
        return ""
    items = [p.strip(" .:;") for p in _pieces(part)][1:]
    items = [p for p in items if p]
    if len(items) < 2:
        return ""
    first = items[0]
    words = first.split()
    if not 3 <= len(words) <= 8:
        return ""
    if NOT_A_DOING.search(first) or topics.RED_FLAG.match(first) or NOT_A_STEP.match(first):
        return ""
    # An item with a verb of its own is read by the verb path above; one that has a verb but does
    # not open on it is a fact about the thing ("most run classes for complete beginners"), not a
    # thing to do.
    from ..compose.verdict import IMPERATIVES

    verbs = set(IMPERATIVES) | set(MOVE_VERBS)
    if any(word.strip(".,!?;:'\"").lower() in verbs for word in words):
        return ""
    return first


def _pieces(part):
    """The instructions of one sentence, split at its colons and commas.

    Nothing is split inside a bracket: "turn the boiler off at the wall switch (not at the fuse
    board, you want the pump to run on for a minute first)" is one instruction with its reason in
    brackets, and splitting at that comma handed over half of it, bracket still open.
    """
    marks = [f for f in PIECE_END.finditer(part) if not _inside_a_bracket(part, f.start())]
    out, start, listed = [], 0, False
    for index, found in enumerate(marks):
        if found.group().strip() == "," and not listed:
            # A comma only splits an instruction when what follows it is one of its own: the
            # clause has to open on a verb, once the connector in front of it is off ("then lift
            # the burnt layer", "and check what your contract says"). "Pick one wake-up time and
            # keep it every day for two weeks, weekends included" and "Check the labels on
            # chocolate, muesli, pesto and satay, and anything marked may contain nuts" carry on
            # the same instruction - a detail and a last item in a list - and cutting there threw
            # away the very words that make the step work.
            end = marks[index + 1].start() if index + 1 < len(marks) else len(part)
            after = part[found.end():end].strip(" ,;:.")
            after = re.sub(r"^(?:and|then|but|also|so|next|plus)\s+", "", after, flags=re.I)
            if not _opens_on_a_verb(after):
                continue
        if found.group().strip() == ":" and not listed:
            keeps, at = _the_colon_tail_kept(part, marks, index, start, found)
            if keeps is None:
                # The head says what the tail is ("learn four things and the rest follows: pasta
                # with a sauce, an omelette"): a lead-in and the list it leads are not an
                # instruction, and the head on its own says nothing to do.
                start, listed = len(part), True
                continue
            if keeps:
                # The colon does not end the instruction: what follows it is the method it is
                # done by or the reason it is worth doing, and the step is the whole of it.
                if at is None:
                    continue
                out.append(keeps)
                start = at
                listed = True
                continue
        out.append(part[start:found.start()])
        start = found.end()
        listed = listed or found.group().strip() == ":"
    out.append(part[start:])
    return out


# A tail that opens on one of these is the questions themselves: "ask the ward three things
# today: who is in charge of their care, what the plan is, and what has to happen next".
A_QUESTION = re.compile(r"^\s*(?:who|what|which|when|where|why|how|whether)\b", re.I)


def _the_tail_asks_a_question(part, marks, index, found):
    """True when what follows the colon is the questions to put, not a list of things to try."""
    end = marks[index + 1].start() if index + 1 < len(marks) else len(part)
    return bool(A_QUESTION.match(part[found.end():end].strip(" ,;.")))


def _the_colon_tail_kept(part, marks, index, start, found):
    """The instruction with its colon tail, when the tail belongs to it rather than to a list.

    "Open a lifetime ISA and put a monthly standing order into it: that adds 25%", "start with
    run-walk: one minute of easy jogging, two minutes of walking", "pick one wake-up time for two
    weeks, weekends included: the morning light is what sets the clock" - the words before the
    colon are the whole of the instruction and the colon gives its method or its reason, so
    cutting there handed over a headline with the part that makes it work gone ("Split your time
    in three.").

    A colon after a noun phrase still opens a list, and a list is read item by item: "the things
    that work: same wake-up time every day, no caffeine" has no verb in front of its colon, so
    this leaves it alone. Returns (the piece to hand over, where the next piece starts) - the
    piece is "" when the colon splits as before, None when the head only announces a list of
    things, and the offset is None when the whole of the sentence after it belongs to this
    instruction.
    """
    head = part[start:found.start()].strip(" ,;")
    if not _opens_on_a_verb(head):
        return "", None
    if NOT_A_TAIL.search(head) and not _the_tail_asks_a_question(part, marks, index, found):
        # A verb phrase that only announces what the tail is: "learn four things and the rest
        # follows: pasta with a sauce, an omelette" leads a list of things to try, and neither
        # the lead nor its list is a thing to do. Unless the tail is the questions themselves:
        # "ask the ward three things today: who is in charge of their care, what the plan is"
        # names what to ask, and asking it is the step.
        return None, None
    tail = part[found.end():]
    if len((head + ": " + tail).split()) <= STEP_WITH_ITS_METHOD:
        return head + ": " + tail.rstrip(" ,;"), None
    # The tail is longer than a step with its method: the step is the instruction and the first
    # item of the tail, and the rest of the list is what a further ask gets.
    for later in marks[index + 1:]:
        if later.group().strip() not in (",", ";"):
            continue
        first = part[found.end():later.start()].strip(" ,;")
        if not first:
            continue
        piece = head + ": " + first
        if len(piece.split()) <= STEP_WITH_ITS_METHOD:
            return piece, later.end()
        return "", None
    return "", None


def _opens_on_a_verb(text):
    """Whether this clause starts on a verb, which is what makes it an instruction of its own."""
    from ..compose.verdict import IMPERATIVES

    words = text.strip(" .,:;").split()
    if not words:
        return False
    return words[0].lower() in IMPERATIVES or words[0].lower() in MOVE_VERBS


# A word that is both a verb and a noun of the thing ("pay", "work", "change", "test", "start")
# opens an instruction ("Pay by card at the till") and a statement ("Pay is at least the apprentice
# minimum wage"), and only the sentence says which. A finite verb straight after it makes the
# sentence a statement about the thing, and a statement is not a step to hand back: an
# apprenticeship definition handed its "Pay is at least the apprentice minimum wage and more on
# most schemes" over as the first thing to do (@blue-hedgehog, @sky-tuna, #6152).
DECLARATIVE = re.compile(r"^(?:[a-z']+\s+)(?:is|are|was|were|has|have|had|can|cannot|will|would|"
                         r"should|takes?|gives?|means?|costs?|comes?|goes?|does|did|gets?|keeps?)\b",
                         re.I)
# The sentences that ask rather than tell: an interrogative never opens a step ("do the theory
# test early" is one and starts with a verb, so verbs stay out of this), and "tell me what you
# last enjoyed" is the bot asking a question with the question mark left off.
QUESTIONS_THAT_ARE_NOT_STEPS = re.compile(
    r"^(?:what|which|how|when|where|who|why|tell me|let me know)\b", re.I)


def _the_steps(said):
    """Every instruction in the answer, in the order the answer gives them.

    `_the_first_step` wants the first one; a "what else can i do" wants the first one that is not
    the thing the person has just said did not work, so both read the answer through this.
    """
    from ..compose.verdict import IMPERATIVES

    verbs = frozenset(IMPERATIVES) | frozenset(MOVE_VERBS)
    for part in [p.strip() for p in SENTENCE.split(str(said).strip()) if p.strip()]:
        if topics.RED_FLAG.match(part):
            continue
        # "If you get them most days, keep a short diary of sleep for two weeks": what to do about
        # a pattern, not the first thing to do for the headache the person has this afternoon, so
        # the whole sentence is passed over the way `_a_move` passes it. A condition that is the
        # answer's only instruction still leaves this reader nothing, which is right: the line is
        # then answered by the move reader, which reads the same condition the same way.
        if CONDITION_CLAUSE.match(part):
            continue
        found = []
        for piece in _pieces(part):
            head = piece.strip(" .:;")
            # "Keep walking, and put a hot water bottle on it at night": the second instruction of
            # an answer starts with the connector, and a reader that wants the verb first skipped
            # it whole and found nothing else.
            head = re.sub(r"^(?:and|then|but|also|so|next|plus)\s+", "", head, flags=re.I)
            if not head or topics.RED_FLAG.match(head) or NOT_A_STEP.match(head):
                continue
            if A_MENU.search(head):
                continue
            if DECLARATIVE.match(head):
                continue  # a statement about the thing, not something to do
            # A question is not a step, even the bot's own: "i want to write a book" then "i dont
            # know where to start" was handed "Start with this: Tell me what you last enjoyed and
            # I'll narrow it down." - the answer's own question read back as the thing to do.
            if head.endswith("?") or QUESTIONS_THAT_ARE_NOT_STEPS.match(head):
                continue
            words = head.split()
            # A step that carries its method after a colon is already the whole of it, and the
            # words of the method ("before you change anything: the subscriptions you forgot")
            # read as qualifiers that are not there. `_the_colon_tail_kept` has cut it to size.
            if ":" in head:
                limit, cut_words = STEP_WITH_ITS_METHOD, STEP_WITH_ITS_METHOD
            else:
                limit, cut_words = STEP_WORDS, CUT_WORDS
            if len(words) > cut_words and words[0].lower() not in NEEDS_COMPLEMENT:
                # The verb phrase is the step and the qualifier after it is detail. Without the
                # cut a long instruction was skipped whole and the ask got the paragraph instead.
                # A qualifier that is the second half of a phrasal verb ("carry on with normal
                # activity") is not where the step ends, so the cut waits for the next one, and
                # a cut that would leave too little goes uncut: a sentence handed over whole
                # still reads, a sentence cut mid-phrase does not ("put the immersion and any
                # room heaters").
                cut = None
                for at in _places_to_cut(head):
                    if _inside_a_bracket(head, at):
                        # "turn the boiler off at the wall switch (not at the fuse board...)": the
                        # words in the bracket are the reason for the step, and a cut there hands
                        # over "turn the boiler off at the wall switch (not".
                        continue
                    left = head[:at].strip(" ,;:.").split()
                    if len(left) < SHORT_STEP:
                        continue
                    if left[-1].lower() in DANGLING:
                        # "clear the vents with a can of air and check what is": the cut landed
                        # past the ending of the clause, so this is not where the step ends.
                        continue
                    cut = at
                    break
                if cut:
                    head = head[:cut].strip(" ,;:.")
                    words = head.split()
            if not 3 <= len(words) <= limit:
                # A piece too long to hand over whole still opens on one instruction: "Each week
                # add a minute to the jog and take one off the walk, and in about eight weeks you
                # will run 20 minutes without stopping" promises and instructs in one sentence,
                # and the reader passed the whole thing over - so a "what next" through the
                # running plan skipped the week-on-week bit the plan is made of.
                first_half = _the_first_instruction_in_a_long_piece(head, verbs)
                if first_half is None:
                    continue
                head, words = first_half, first_half.split()
            if words[0].lower() not in verbs \
                    and not _a_verb_after_a_leading_phrase(head, verbs):
                continue
            # "The thing to do first: fix the wake-up time first" says first twice.
            trimmed = re.sub(r"\s+(?:first|next)$", "", head, flags=re.I)
            # ...but "first" is sometimes part of the phrase rather than a word said twice:
            # "keep them apart behind a baby gate at first, feed each one on their own side of it"
            # was handed over as "The first thing to do: Keep them apart behind a baby gate at." -
            # a step that stops mid-phrase and reads as a typo. Only a bare "first" at the end of
            # a step is the repeated word, so the trim is kept only when the step still ends on
            # something a sentence can end on.
            if trimmed.split() and trimmed.split()[-1].lower() not in DANGLING:
                head = trimmed
            found.append(head[0].lower() + head[1:])
        for step in found:
            yield step
        if not found:
            item = _a_list_item(part)
            if item:
                yield item[0].lower() + item[1:]


def _the_next_step(said, memory):
    """One thing out of the answer past the first, which they have not already had or tried.

    "ive tried stretching" then "what else can i do" is a person two things into a list, and the
    next item is the whole reply: handing back the stretch they just told us did nothing, or the
    paragraph they are working through, is not.

    The first instruction is skipped: the whole answer was handed over a turn ago, so "what else"
    asks for what comes after it, and giving the opening sentence back with "there is this one
    too" in front of it is the same thing said again with a new label.
    """
    steps = list(_the_steps(said))
    for step in steps[1:]:
        if topics.RED_FLAG.match(step):
            # A health answer ends with the warning ("See a GP if it is no better in a fortnight"),
            # and handing that over as "one more thing you can do" makes the person's afternoon
            # worse, not better. The same skip `_a_move` makes, for the same reason.
            continue
        if _already_repeated(step, memory) or _they_say_they_tried(step, memory):
            continue
        return step
    return None


def _the_first_step(said):
    """The first thing to do in the answer, read more generously than `_a_move`.

    The move reader above is tuned for a line that asks back at the answer generally, so it only
    takes a verb phrase it recognises and only when the phrase is short. A "where do i start" is
    a narrower ask, and the entries answer it with verbs that list does not have ("track two
    weeks of what leaves the account", "run a hot service wash"), so this one takes those verbs
    and cuts a long instruction at its qualifier: the verb phrase is the step, the rest is detail.
    """
    # Forwards, not backwards as `_a_move` reads it: a "where do i start" wants the first thing
    # to do, and an answer that opens with a fact still gives its steps in order after it.
    for step in _the_steps(said):
        return step
    return None


# "what is a mortgage", "what does a mortgage mean", "whats a mortgage": the line asks what the
# thing is, not what to do about it, so the answer it gets is a definition. A definition has no
# work in it at all - which is why a how-to question after one can only be a new question about
# the same subject, never the answer said again under a lead.
WHAT_IT_IS = re.compile(r"^\s*(?:what(?:'s|s| is| are| does| do| did)\b|"
                        r"tell me (?:about|what)\b|define\b|meaning of\b)", re.I)


def _a_new_work(text, asked):
    """True when a how-to question follows a definition of the same thing.

    "what is an apprenticeship" then "how do i get one": the definition answered what the thing
    is, and the person now asks how to get one, which its own entry answers ("apply to them like
    jobs, because that is what they are"). Handed the definition back they got its first fact as
    if it were a step: "Start with this: Pay is at least the apprentice minimum wage"
    (@blue-hedgehog, @sky-tuna, #6152). A line that only asks back at the answer ("how do i use
    it", "how do i do that", "where do i start") names no doing of its own, and "can i save it"
    is answered from the answer by its own reader, so neither comes here.
    """
    line = str(text or "")
    if asks_to_put_it_right(line) or HOW_IT.search(line):
        return False
    if not WHAT_IT_IS.match(str(asked or "")):
        return False
    return bool(_doings(line))


def asks_which_part(text):
    """Whether the line asks which part of the answer to do first, and names no doing of its own.

    "Where do i start", "what should i do first", "where should i begin with this": the whole of
    the line is the ask, so it is answered from the answer in hand and never by a fresh lookup.
    "How do i clean it" is not this: it names a doing ("clean") that may be a question of its own
    and a neighbouring entry answers it well, so the lookup keeps that line and this reader stays
    out of it.
    """
    line = str(text or "")
    if not line.strip() or WORDING.search(line):
        return False
    return bool(asks_for_the_move(line)) and not HOW_IT.search(line)


def _leads_for(text):
    """The lead-ins that answer this ask: the thing to do, or the thing to change."""
    return CHANGE_LEADS if CHANGE_ASK.search(text or "") else MOVE_LEADS


def _a_lead_for(leads, step, memory, text):
    """One lead out of `leads`, and never one that says what the step's first word says.

    Every lead in these pools marks the step as the first thing, which is the whole point of it -
    except when the step opens on its own "Start with": then the reply says start twice, and to
    somebody who asked where to start that reads like a machine that did not hear the question.
    Only the lead can give way, because the step is the answer's own wording and trimming it is
    how a step stops being the answer's. A placeholder is not a word of the lead, so it comes out
    before the lead is read.
    """
    if STEP_SAYS_FIRST.search(str(step or "").strip()):
        leads = tuple(lead for lead in leads
                      if not LEAD_SAYS_FIRST.search(re.sub(r"\{[a-z_]+\}", " ", lead)))
        leads = leads or NOW_LEADS
    return pick(leads, memory, text)


def the_move(text, said, memory):
    """The first step of the answer just given, when the line is asking which part to do.

    "Where do i start" a turn after the answer has already been on the screen is not a request
    for the paragraph again: the knowledge base reaches the same entry and frames it "Same as
    before: <the whole of it>", which tells a person who has just read it nothing. The step is
    already in the answer, so it is handed over in the answer's own words.
    """
    if not isinstance(said, str) or not said.strip():
        return None
    if not asks_for_the_move(text):
        return None
    if WORDING.search(str(text or "")):
        return None
    if re.search(r"\bhow (?:long|much|many|often|far|hot|soon)\b", str(text or ""), re.I):
        return None  # a figure is asked for, not the first step
    step = _the_first_step(said)
    if not step or _already_repeated(step, memory):
        return None
    if not isinstance(memory, dict):
        return None
    if _they_say_they_tried(step, memory):
        # "ive tried a hot wash already" then "what else can i do": the first step of the answer
        # is the thing they just said did not work, and handing it back is the one reply a friend
        # never gives. The tried pools have the next step; this one steps aside for them.
        return None
    _wording = step[:1].upper() + step[1:]
    return _handed_back(memory, _a_lead_and_a_step(
        _a_lead_for(_leads_for(text), _wording, memory, text), _wording))


def _they_say_they_tried(step, memory):
    """True when a line just before this one reports having done this very thing.

    The report does not have to be the bare "i tried that" the tried pools read: "ive tried a hot
    wash already" names the thing it tried, and that is exactly the one the move must not hand
    back.
    """
    mine = {word for word in re.findall(r"[a-z']+", step.lower()) if len(word) > 2}
    if not mine:
        return False
    for turn in (memory.get("turns") or [])[-3:]:
        if not isinstance(turn, dict):
            continue
        line = str(turn.get("user") or "").lower()
        if not ATTEMPT.search(line):
            continue
        said = {word for word in re.findall(r"[a-z']+", line) if len(word) > 2}
        shared = mine & said
        # One long word that is the same word is enough ("ive tried walking" against "keep
        # walking and carry on"): the person named the very thing, and handing it back is the
        # reply that reads as not listening.
        if len(shared) >= 2 or any(len(word) >= 5 for word in shared):
            return True
    return False


# A line that says the person has already had a go: the move must not be the thing they had a go
# at. "tried" is here as well as in `tried`'s own patterns because those read the bare "i tried
# that", and the line that matters names what it tried.
ATTEMPT = re.compile(r"\b(?:tried|trying|already|gave it|had a go|no luck|used)\b", re.I)


# The figures a follow-up can ask for, and the figure in the answer that answers each one. The
# words are the ask itself; the second pattern is what the answer has to contain for that ask to
# be answered from it.
FIGURE_ASKS = (
    ("time", re.compile(
        r"\bhow\s+(?:long|soon|quick(?:ly)?|longer)\b"
        r"|\bhow\s+many\s+(?:seconds?|minutes?|mins?|hours?|hrs?|days?|weeks?|months?|years?|nights?)\b"
        r"|\bwhat\s+(?:time|timing)\b", re.I),
     re.compile(
        r"\b(?:\d+(?:\.\d+)?|a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
        r"fifteen|twenty|thirty|forty|forty-five|fifty|sixty|ninety)\s*(?:\w+\s+to\s+)?"
        r"(?:seconds?|secs?|minutes?|mins?|hours?|hrs?|days?|weeks?|wks?|months?|years?|nights?)\b",
        re.I)),
    ("heat", re.compile(r"\bhow\s+(?:hot|warm)\b|\bwhat\s+(?:temperature|heat|gas\s+mark)\b", re.I),
     re.compile(r"\b(?:\d{2,3}\s*(?:°|degrees?|c\b|celsius|f\b|fahrenheit)|gas\s+mark\s+\d|"
                r"mark\s+\d\b)", re.I)),
    ("amount", re.compile(r"\bhow\s+(?:much|many)\b", re.I),
     re.compile(r"(?:£\s?\d|\b\d+\s*(?:g|kg|grams?|ml|l|litres?|pints?|cups?|tbsp|tsp|oz|ounces?)\b)",
                re.I)),
    ("often", re.compile(r"\bhow\s+often\b|\bhow\s+many\s+times\b", re.I),
     re.compile(r"\b(?:once|twice|three\s+times|\d+\s+times)\b[^.?!]{0,25}"
                r"\b(?:a|per|every)\s+(?:day|week|month|year|night)\b", re.I)),
)

# The words a line that asks for a figure and nothing else is made of: the ask, the pronoun that
# points at the thing already on the screen, and the verb the figure belongs to. A line that names
# anything more ("how long should i cook the rice", "how much do i need for the deposit") has an
# answer of its own and is left to it.
FIGURE_WORDS = frozenset("""
    how long soon quickly quick longer much many often hot warm what time timing temperature heat
    gas mark should shall can could would will may might must do does did is are was were am
    i we you they he she it its that this these those them there and so ok okay but then again
    also just really leave left need use take cook bake keep wait soak boil simmer rest run
    sit stand stay lie hang dry cool warm heat set settle marinate marinade prove rise chill
    exercise give put apply wear change replace before after for in on at to it too much
    before afterwards after that
""".split())

# A verb of saying something does not name the thing that would have an answer of its own:
# "how long do i wait before asking", "how long should i wait before telling her" and "how long
# before i say something" all ask for the wait in the answer just given. The word the question
# ends on used to stand in the way - "asking" was read as a thing of its own - so the sentence
# with the figure in it was never handed back. A line that does name the thing ("before asking
# for a refund", "before telling my boss") keeps its own answer, because that word is not here.
FIGURE_SAYING = frozenset("""
    ask asking say saying tell telling mention mentioning bring bringing raise raising
    broach broaching approach approaching him her them
""".split())


def the_figure_asked(text, memory):
    """The sentence of the last answer that carries the figure this line asks for, or None.

    "how long should i leave it", a turn after the bot said "Wipe it, shake out the port, and
    leave it in a warm dry place for 24 hours", got the search hedge: the answers machinery goes
    looking for an entry keyed on this line, and the line names no thing, so nothing is found -
    while the figure asked for is in the answer already on the screen. The figure is handed back
    in the answer's own sentence, so the person gets "leave it in a warm dry place for 24 hours"
    rather than a shrug.

    Narrow on purpose: the line must ask for one kind of figure and name nothing else, the answer
    must be a knowledge answer from a turn or two ago, and the sentence handed back must carry a
    figure of the kind asked for.
    """
    if not isinstance(memory, dict):
        return None
    clean = " ".join(str(text or "").lower().split())
    if not clean:
        return None
    asked = None
    for _name, ask, figure in FIGURE_ASKS:
        if ask.search(clean):
            asked = ask, figure
            break
    if asked is None:
        return None
    ask, figure = asked
    rest = [word for word in re.findall(r"[a-z']+", ask.sub(" ", clean))
            if word not in FIGURE_WORDS and word not in FIGURE_SAYING]
    if rest:
        return None  # the line names a thing of its own: that thing has an answer
    seen_a_card = False
    for back, turn in enumerate(reversed((memory.get("turns") or [])[-LOOK_BACK:]), 1):
        if not isinstance(turn, dict):
            break
        # A knowledge answer, a turn or two back. Short answers count here, unlike in
        # `_recent_answers`: "40 to 45 minutes." is a whole answer, and it is exactly the sentence
        # a later "how long should i rest it" wants rather than the paragraph behind it.
        if turn.get("module") != "answers":
            continue
        said = str(turn.get("bot") or "").strip()
        if not said or HEDGE.search(said) or said.rstrip().endswith("?"):
            continue
        if len(said) < 50 and not figure.search(said):
            continue  # a stock line is not an answer with a figure in it
        if back > 1 and not _about_the_same_thing(str(turn.get("user") or ""), said, memory):
            continue  # the chat has moved on: an older answer is not what this line leans on
        for part in _sentences(said):
            part = part.strip().rstrip(" ;")
            if part and figure.search(part) and not _already_repeated(part, memory):
                return part[:1].upper() + part[1:] + ("" if part[-1:] in ".!?" else ".")
    return None


# Not every follow-up asks for a figure. "is the food still ok" after a card on a freezer door,
# "do i need to prick them" after one on jacket potatoes, "where do i start" after one on sorting
# out money: each names the thing in a word the card itself never has to use ("food", "them"),
# and each reached the search hedge, which tells a person to go and look up the thing the bot has
# just told them about. What the card has is a sentence of the kind asked for, and none of these
# asks needs a figure for it to be handed back.
STILL_SAFE = re.compile(
    r"\bstill\s+(?:ok|okay|good|fine|safe|edible|alright)\b|\bis\s+(?:it|that|this)\s+"
    r"(?:safe|alright|fine|ok|okay|good)\b|\bcan\s+i\s+still\b|\bsafe\s+(?:to|for)\b",
    re.I)
SAID_SAFE = re.compile(
    r"\b(?:safe|fine|okay|ok|keep|keeps|kept|bin|binned|binning|throw|thrown|eat|eaten|edible|"
    r"cooked|refreeze|put\s+back|nothing\s+needs|no\s+need)\b", re.I)
DO_I_NEED_TO = re.compile(
    r"\bdo\s+i\s+(?:need|have)\s+to\b|\bhave\s+i\s+got\s+to\b|\bshould\s+i\b|"
    r"\bam\s+i\s+meant\s+to\b|\bdo\s+you\s+have\s+to\b", re.I)
A_MOVE = re.compile(
    r"\b(?:prick|cut|turn|stir|cover|leave|put|add|check|wash|rinse|soak|rest|shake|score|"
    r"season|test|wait|ask|keep|write|print|sign|ring|call|book|take|use|give|hold|open|close|"
    r"run|cook|bake|boil|simmer|freeze|defrost|empty|clean|wipe|change|replace)\b", re.I)
WHERE_TO_START = re.compile(
    r"\bwhere\s+(?:do|should|would|can|shall)\s+i\s+(?:really\s+|even\s+)?(?:start|begin)\b"
    r"|\bwhere\s+to\s+start\b|\bwhat\s+(?:do|should)\s+i\s+(?:do|try)\s+first\b"
    r"|\bhow\s+do\s+i\s+(?:start|begin|get\s+going)\b|\bwhere\s+do\s+i\s+(?:go|look)\b",
    re.I)

# The kinds of sentence a card can hand back when no figure is asked for: the ask, and the mark
# that says the card has the sentence. `None` means the card's own opening, which is the first
# step of what it tells the person to do.
PART_ASKS = (
    # "When does it wear off" and "how long does it last" are the same ask about the same figure,
    # and so is "when will the numbness go": the card in hand usually states it outright ("wears
    # off after an hour to three hours", "keeps 24 hours in the fridge"), so all of them are read
    # here rather than only the first shape. "How long" is the commonest way of asking it and was
    # missing, which left "how long does the numbness last" with the search hedge.
    ("time", re.compile(r"\bwhen\s+(?:does|do|will|would|should|can|is|are)\b|"
                        r"\bhow\s+(?:soon|long)\b|\bhow\s+(?:much\s+)?longer\b", re.I), FIGURE_ASKS[0][2]),
    ("start", WHERE_TO_START, None),
    ("safe", STILL_SAFE, SAID_SAFE),
    ("move", DO_I_NEED_TO, A_MOVE),
)

# The words that stand in for the thing the chat is on rather than naming a new one. "Is the food
# still ok" after a card about a freezer door names the topic of the card in a general word, and
# the card is free to answer it. A word that names a thing the card does not have ("manchester",
# in "how long does it take to get to manchester" after a card on marinades) is not one of these,
# and a card that never says it cannot answer for it.
PART_STAND_INS = frozenset("""
    food foods stuff thing things bit bits part parts piece pieces kit gear item items
    water drink milk meat rest lot lots everything anything something nothing else
    job work house home place places one plant plants garden washing clothes
""".split())


def _the_keys_of(said, memory):
    """The words the entry behind an answer was keyed on, or an empty set.

    `memory["entry_answers"]` keeps the keys of every card this chat was given, and a follow-up
    can be about the card without using a word of the card's own sentences: "where do i start"
    after a card on sorting out money says nothing about money, and the card's keys do.
    """
    head = " ".join(str(said or "").split())[:60]
    for record in (memory or {}).get("entry_answers") or ():
        if not isinstance(record, dict):
            continue
        text = " ".join(str(record.get("text") or "").split())
        if text and text[:60] == head:
            return {str(key).lower() for key in (record.get("keys") or ())}
    return set()


# A sentence that only follows another one is not a reply: "Then put the phone down and let the
# answer come or not." was handed back to "should i ask her", where it reads as an instruction to
# stop asking. A part of a card has to stand up on its own.
NOT_ALONE = re.compile(r"^(?:then|after that|afterwards?|next|also|and|but|or|so|instead|"
                       r"either|once|while|because|which|that|this|it|they|them|he|she)\b", re.I)
PART_OPENS = frozenset("""
    then afterwards next also and but or so instead either once while because which
""".split())


def answers_nothing(reply):
    """True when the reply is one of the bot's own ways of not answering this turn.

    The composer has a handful of lines for a question it cannot take on: the search hedge, the
    note that there is nothing to stand behind, "two goes at the same thing is enough", "that is
    in the answer above", "tell me what you've got so far". All of them are the right reply when
    there is nothing else to say, and all of them are the wrong reply when the card on the screen
    already says part of the answer, which is what `the_part_asked` and `what_it_knows` are for.
    """
    if not reply:
        return False
    # Taken inside the call: this module is read by the composer as it loads, and binding these
    # at the top would leave them built from a half-loaded `fallback`.
    from ..compose import fallback
    from ..compose import verdict
    if fallback._is_a_hedge(reply) or fallback._nothing_to_stand_behind(reply):
        return True
    return fallback._in_a_pool(reply, (fallback.SAME_AGAIN,
                                       fallback.HELP_ALREADY,
                                       fallback.TIPS_LINES,
                                       fallback.TIPS_THING,
                                       fallback.TRIED_NO_CHANGE_ELSEWHERE,
                                       verdict.ALL_OF_IT_LINES))


def the_advice_was_to_get_seen(memory):
    """True when the bot has already told them to be seen today - 111, A&E, a GP, a vet.

    A follow-up after that is about everything else, and the card's own sentence put in front of
    the advice again reads as the bot talking over what it just said.
    """
    from . import stuck
    return stuck.the_advice_was_to_get_seen(memory)


def the_part_asked(text, memory):
    """The sentence of a card in hand that answers this follow-up, or None.

    "is the food still ok", two turns after the bot's answer about a freezer door, got "A quick
    search online will get you a solid answer": the answers machinery looks for an entry keyed on
    this line, finds none, and the card that would answer it is already on the screen. So the
    sentence of that card which says what is safe, or which step has to be done, or the step it
    says to take first, is handed back in the card's own words.

    Narrow on purpose. The ask has to be one of the three kinds above, the answer has to be a
    knowledge card from the last few turns, and the card has to be about the thing the line names
    or about the thing the chat is still on. Nothing is invented: the sentence is the bot's own.
    """
    if not isinstance(memory, dict):
        return None
    clean = " ".join(str(text or "").lower().split())
    if not clean:
        return None
    kind = None
    for name, ask, mark in PART_ASKS:
        if ask.search(clean):
            kind = name, mark
            break
    if kind is None:
        return None
    name, mark = kind
    if name == "move" and not _whether_to(clean):
        # "should i ask her", "should i text him": a card says what to do and why, never yes or
        # no, so there is no sentence of it that answers a decision about a person. The step-shaped
        # asks that a card can settle ("do i need to prick them") name a move on the thing, and
        # only those are left to the sentence below; the rest are the composer's to answer.
        return None
    asked_words = topics.words(clean)
    if name == "move":
        # The verb the ask is made with names what is being asked about, not a subject of its
        # own: "do i need to prick them" asks about pricking, and a card that never says the
        # word has nothing to hand back. So the verb right after the ask is taken out of the
        # subject, and a thing named later in the line ("do i need to move the fridge") is not.
        for _name2, ask2, _mark2 in PART_ASKS:
            if _mark2 is None:
                continue
            found = ask2.search(clean)
            if not found:
                continue
            asked_words = [word for word in asked_words
                           if word not in re.findall(r"[a-z']+", found.group(0))]
            break
    if name == "move":
        _step = _whether_to(clean)
        if not [word for word in _step.split()[2:] if word not in PART_STAND_INS][1:]:
            # The step names no thing - "should i rest", "should i wait" - so it is about the
            # person and not about anything the card is on. Nothing of the card can answer it.
            return None
    asked = [word for word in asked_words
             if len(word) > 2 and not word.isdigit() and word not in topics.STOPWORDS
             and word not in ASK and word not in ASK_VERB and word not in TIME
             and word not in FILLER and word not in SELF and word not in PART_STAND_INS]
    # A yes/no about still being able to do something with the thing ("can i still eat the ones
    # that look alright", "can i still wear these") is settled by the card only when the card says
    # that doing. The blight card says how to slow blight and never says whether the fruit is safe
    # to eat; its opening was handed back as though it answered, and the person was left with a
    # paragraph about binning leaves. The doing is in `ASK_VERB`, so it is not in `asked` at all,
    # and with nothing else named the guard below had nothing to test.
    doing = ""
    still = STILL_ASKS.match(clean)
    if still:
        doing_words = re.findall(r"[a-z']+", still.group("rest"))
        if doing_words:
            doing = _a_stem(doing_words[0])
    seen_a_card = False
    for back, turn in enumerate(reversed((memory.get("turns") or [])[-LOOK_BACK:]), 1):
        if not isinstance(turn, dict):
            break
        # A knowledge card, and only a knowledge card: the composer's own lines have no answer
        # behind them to hand back.
        if turn.get("module") != "answers":
            continue
        said = str(turn.get("bot") or "").strip()
        if not said or HEDGE.search(said) or said.rstrip().endswith("?"):
            continue
        if len(said) < 50:
            continue  # a stock line, not a card
        keys = _the_keys_of(said, memory)
        on_the_card = bool(asked) and bool(set(asked) & keys)
        if not asked and seen_a_card:
            # The line names nothing at all ("where do i start"), so the card it leans on is the
            # newest one in the chat: a card further back has been answered over since.
            continue
        seen_a_card = True
        if asked and back > 1 and not on_the_card and not _about_the_same_thing(
                str(turn.get("user") or ""), said, memory):
            continue  # the chat has moved on: an older card is not what this line leans on
        if not asked and back > 1 and not _the_chat_is_still_on(said, memory):
            # A line that names nothing of its own ("and should i put it in writing") leans on the
            # newest card only. An older one is a different subject: the card about a tired child
            # was handed back for a question about shift changes, with the NHS site on the end of
            # it. The card has to share a word with the last few lines to be the one in hand.
            continue
        for index, part in enumerate(_sentences(said)):
            part = part.strip().rstrip(" ;")
            if len(part.split()) < 4:
                continue
            if part.lower().endswith("?"):
                continue
            if NOT_ALONE.match(part):
                continue  # a sentence that only follows the one before it is not a reply
            if name == "start":
                if index > 0:
                    break  # the start is the card's opening, and nothing further down it
            else:
                if not mark.search(part):
                    continue
                if CONDITION_CLAUSE.match(part) or NOT_A_MOVE.match(part):
                    continue
            if asked and not on_the_card and not any(word in part.lower() for word in asked):
                continue
            if doing and doing not in {_a_stem(word) for word in re.findall(r"[a-z']+",
                                                                            part.lower())}:
                continue  # the card never says this doing, so nothing of it answers the line
            if _already_repeated(part, memory):
                continue
            return part[:1].upper() + part[1:] + ("" if part[-1:] in ".!?" else ".")
    return None


# The rest of an answer lives somewhere, and the subject of the chat says where. Not a fact about
# the world - a place to look, one per subject the understanding engine already names
# (`bot/understanding/topics.py`), so nothing here goes stale.
WHERE_TO_LOOK = {
    "cooking": "the packet or a cookery site",
    "food-and-drink": "the label or a cookery site",
    "health": "the NHS site or a pharmacist",
    "fitness": "a coach or the NHS site",
    "sleep": "the NHS site",
    "money": "the official page, gov.uk or your bank",
    "work": "your contract or ACAS",
    "school-and-study": "the school's own notice or the exam board",
    "science": "a textbook or the Royal Society site",
    "history": "a museum's own page",
    "geography-and-travel": "a map app or the operator's own site",
    "technology": "the maker's support page",
    "home-and-diy": "the maker's instructions or a qualified trade",
    "garden-and-plants": "the RHS site or the plant's own label",
    "pets": "your vet",
    "family-and-parenting": "your GP or the NHS site",
    "friends-and-relationships": "the person themselves",
    "shopping": "the shop's own listing",
    "cars": "the handbook or a garage",
    "entertainment": "a listings site",
    "sport": "the club or the governing body's site",
    "language-and-writing": "a dictionary",
    "feelings": "a friend who knows you, or your GP",
    "maths-and-numbers": "a calculator",
    "nature-and-weather": "the Met Office site",
}
WHERE_TO_LOOK_DEFAULT = "a search"

# The place to settle it is read off the card the person is looking at, not off the topic of the
# line that asked for it. "formula left out for 3 hours" is read as a sport topic - Formula 1 -
# so a question about reheating a baby's bottle was told to look at "the club or the governing
# body's site". The card's own words say what the chat is about, and they are on the screen, so
# they pick the place; the topic is only the fallback.
WHERE_TO_LOOK_WORDS = (
    (("baby", "formula", "bottle", "breastfeed", "nappy", "weaning"), "the NHS site or a health visitor"),
    (("boiler", "radiator", "thermostat", "bleed"), "the maker's instructions or a gas engineer"),
    (("extractor", "socket", "fuse", "appliance", "plug", "wiring"), "the maker's manual or an electrician"),
    (("oven", "roast", "bake", "boil", "fry", "pan", "saucepan", "dough", "oven's"), "the packet or a cookery site"),
    (("dose", "tablet", "antibiotic", "paracetamol", "ibuprofen", "prescription"), "a pharmacist or the leaflet in the box"),
    (("battery", "charger", "router", "app", "software", "phone"), "the maker's support page"),
    (("mortgage", "overdraft", "pension", "tax", "benefit", "allowance"), "the official page, gov.uk or your bank"),
    (("lease", "landlord", "deposit", "tenancy"), "your contract or the council's housing team"),
    # A card about a passport or a visa is a card about a rule only one office can state: "can i
    # still fly in may" was told "a map app or the operator's own site", which is where the topic of
    # the change is, not where the answer is.
    (("passport", "visa", "embassy", "renewal"), "the passport office's own site"),
    (("weed", "soil", "compost", "prune", "seedling", "plant"), "the RHS site or the plant's own label"),
    (("puppy", "kitten", "vet", "dog", "cat"), "your vet"),
    (("stitch", "sew", "hem", "zip", "fabric", "garment"), "the care label or a tailor"),
)

# The ask whose gap this reading can name: a yes/no about doing a step - "do i need to prick
# them", "should i prick the shell", "am i meant to score the fat". The rest of the line becomes
# "whether to ..." and reads as the one thing the card in hand never said.
A_MOVE_WORDS = frozenset("""
    prick cut score slash stab turn stir cover uncover leave put add check wash rinse soak scrub use try
    rest shake season salt test taste wait keep freeze defrost empty clean wipe change replace
    trim peel chop slice mix whisk knead roll fill drain squeeze press
    bleed flush prime seal grease oil sand paint varnish glue screw tighten loosen unplug plug
    switch reset restart reboot charge update install download back defrost refrigerate reheat
    tin jar bottle label marinate brine gut bone stuff ice chill cool warm heat preheat blind
    line flour dust glaze baste carve prove rise fold beat cream sieve sift blend mash grate zest
    juice deseed core hull soak de-ice descale unblock plunge rod hoover vacuum mop dust sweep
    water feed prune repot stake tie mulch mow scarify aerate
""".split())

WHETHER_ASKS = (
    re.compile(r"\b(?:do|did)\s+i\s+(?:need|have|got)\s+(?:to\s+)?(?P<rest>[^?!]+)", re.I),
    re.compile(r"\bshould\s+i\s+(?:be\s+|just\s+|still\s+)?(?P<rest>[^?!]+)", re.I),
    re.compile(r"\bam\s+i\s+(?:meant|supposed)\s+(?:to\s+)?(?P<rest>[^?!]+)", re.I),
    # Permission, which is the same question about the same step: "can i just use bleach" after
    # the card on moths, "is it ok to put it in the wash" after the card on a stain. The card
    # never says yes or no, so what comes back is the card's own sentence and the one place that
    # settles it - never an invented yes.
    re.compile(r"\bcan\s+i\s+(?:just|still|safely|even)?\s*(?P<rest>[^?!]+)", re.I),
    re.compile(r"\bis\s+it\s+(?:ok|okay|safe|alright|fine)\s+to\s+(?P<rest>[^?!]+)", re.I),
)


# A yes/no about a method rather than a step of the card's own: "will beer traps do anything"
# after the card on slugs, "does vinegar work on weeds", "would a dehumidifier help", "is a fan
# enough". The card never covered that method, and the reply used to be "I'm not sure about that
# one - a quick search online will get you a solid answer", which throws away the card still on
# the screen. What the card does cover comes back, and only then the one place with the rest.
METHOD_ASKS = (
    re.compile(r"\b(?:will|would|does|do|did|is|are|can|could)\s+(?P<rest>[^?!]{3,40}?)\s+"
               r"(?:work|works|help|helps|do\s+anything|do\s+it|do\s+the\s+job|"
               r"(?:be\s+)?enough|(?:be\s+)?any\s+good|be\s+ok\b|be\s+okay|"
               r"be\s+worth\s+(?:it|doing))\b[^?!]*", re.I),
)
# The words that name no method at all: "will it work", "would that help". A pronoun leans on
# something the bot cannot see, and the card in hand may already be that something.
NOT_A_METHOD = frozenset("""
    it that this they those these there he she i we you one ones
""".split())

# Words that say how well something works rather than what is being asked about. "does a harness
# work better" asks about the harness, and a card that says "A front-clip harness or head halter
# helps while he learns" answers it; the "work better" is the frame of the question. Left in, they
# made every such ask a gap the card had to fill word for word, and the card in hand was passed
# over for a place that knows nothing of it.
A_QUALITY = frozenset("""
    work works worked working better best help helps helped worth enough good fine okay ok
    safe still anymore actually really even than
""".split())


# A yes/no about still being able to do something with the thing in hand. Unlike the two families
# above, there is no step named ("the ones", "them"), so the clause itself is what the card is
# asked about.
STILL_ASKS = re.compile(
    r"^(?:(?:and|but|so|or)\s+)?"
    r"(?P<aux>can|could|may|should|would)\s+(?P<who>i|we)\s+still\s+(?P<rest>[a-z].*)$", re.I)


def _whether_to(clean):
    """The step the line asks about, as "whether to <it>", or "".

    The step has to start with a verb of doing a thing to something, and be short: "should i take
    her tonight" and "what should i bring" are not asks about a step in hand, and "whether to
    bring" is not a sentence. Only ever a yes/no about a move on the thing the answer was about.
    """
    for shape in WHETHER_ASKS:
        found = shape.search(clean)
        if not found:
            continue
        rest = " ".join(found.group("rest").split()).strip(" .,")
        words_of_it = rest.split()
        if not words_of_it or len(words_of_it) > 5:
            continue
        if words_of_it[0] not in A_MOVE_WORDS:
            continue
        return "whether to " + rest
    for shape in METHOD_ASKS:
        found = shape.search(clean)
        if not found:
            continue
        rest = " ".join(found.group("rest").split()).strip(" .,")
        words_of_it = rest.split()
        if not words_of_it or len(words_of_it) > 5:
            continue
        if words_of_it[0] in NOT_A_METHOD:
            continue
        return "whether to use " + rest
    # A yes/no about still being able to use the thing on the screen: "can i still eat the ones
    # that look alright", "can i still wear them". The thing is a stand-in ("the ones", "them") or
    # the chat's own subject, so there is no move-word to test; the card is asked whether it covers
    # the doing, and where it does not, the reply says so in the person's own words and names the
    # one place that settles it. The clause is kept grammatical ("whether i can still eat ..."),
    # because it is said back to them in the gap line.
    found = STILL_ASKS.match(clean)
    if found:
        return ("whether " + found.group("who").lower() + " " + found.group("aux").lower()
                + " still " + " ".join(found.group("rest").split()).strip(" .,"))
    return ""


def _a_stem(word):
    """"preheat" and "preheating" are one word said in two forms.

    The gap this reads is a step the card never covered, and a card that says "about five minutes
    preheating" has covered "and how long should i preheat it". Comparing the words as typed said
    it had not, and the reply then told the person the packet knows - about the number the card in
    front of them had just given.
    """
    word = str(word or "").lower()
    for suffix in ("ing", "ings", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            word = word[: -len(suffix)]
            break
    if word.endswith("e") and len(word) > 4:
        word = word[:-1]
    return word


# The frame words of a reply, not its subject. "Count the sleep first" and "Say the one thing that
# matters first, then the rest" share "first" and nothing else, and on that one word the card about
# a child's sleep counted as still on a chat about putting a shift change in writing.
NOT_A_SUBJECT = frozenset("""
    first thing things one ones rest bit part way ways sort kind lot next still even actually
    really everything anything something nothing else another
""".split())


def _the_chat_is_still_on(said, memory):
    """True when the card is the one the chat is still on, not just one it passed through.

    Two things make a card the one in hand. Its words (and the words it is keyed on, because a
    card written for the person's own line never says them back - "slugs" becomes "them") touch
    the line just given, or they touch the reply just given, which is how a card stays in hand
    when the bot has been handing parts of it back. A card four turns back that shares a word with
    one of the lines in between is a different thing: the child-sleep card came back for a
    question about putting a shift change in writing, because "my kid is 6" was still in the last
    three lines. The reply just given there was "Say the one thing that matters first", which is
    about nothing in that card, and the line just given was about writing it down.
    """
    words = set(re.findall(r"[a-z']+", str(said or "").lower()))
    words |= {word for word in _the_keys_of(said, memory) if len(word) > 2}
    words = {word for word in words
             if len(word) > 2 and word not in topics.STOPWORDS and word not in NOT_A_SUBJECT}
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return False
    last = turns[-1]
    for side in ("bot", "user"):
        here = {word for word in re.findall(r"[a-z']+", str(last.get(side) or "").lower())
                if len(word) > 2 and word not in topics.STOPWORDS
                and word not in NOT_A_SUBJECT}
        if words & here:
            return True
    return False


def _where_the_rest_is(said, memory, turn, ask=""):
    """The one place that settles what an answer in hand does not cover, read off the answer.

    Where the rest of it lives is read off the card's own line, not the ask: "should i keep
    driving" carries no subject, and the subject of the chat is what the answer was about. The
    card's own words, and the entries it came from, go in too: a timings card for a roast says
    "20 minutes per 500g ... a 2kg bird" and names no oven at all, while the entry behind it is
    keyed on one. Without them the place came from the topic of the turn that asked for the
    figure - "how long does it take anyway" reads as maths, and the reply offered "a calculator"
    for whether to cover a chicken with foil.
    """
    card_words = " ".join(re.findall(r"[a-z']+", str(said or "").lower()))
    card_words = (card_words + " " + " ".join(sorted(_the_keys_of(said, memory)))).strip()
    for needles, place in WHERE_TO_LOOK_WORDS:
        if any(re.search(r"\b" + word + r"\b", card_words) for word in needles):
            return place
    # The topic of the turn that fetched the card is the last resort, and only counts when the ask
    # is on that same topic. A card about a dog that pulls on the lead was fetched by a turn read
    # as maths ("how long until it works"), and "does a harness work better" was told that a
    # calculator would know more than the bot - the card itself said a front-clip harness helps.
    # Where the ask is on another topic, no place is named and the line is left to whatever else
    # can answer it: a place read off the wrong turn is worse than none.
    try:
        card_read = understand(str((turn or {}).get("user") or "")) or {}
        card_topic = str(card_read.get("topic") or "")
    except Exception:
        card_topic = ""
    if ask:
        # A card fetched by a turn read as another subject says nothing about where the rest of
        # this line lives. "how long until it works" in a chat about a dog that pulls on the lead
        # reads as maths, and "does a harness work better" was told that "a calculator" would know
        # more than the bot. Where the two topics part, the honest place is the general one.
        try:
            ask_topic = str((understand(ask) or {}).get("topic") or "")
        except Exception:
            ask_topic = ""
        if card_topic and ask_topic and card_topic != ask_topic:
            return WHERE_TO_LOOK_DEFAULT
    return WHERE_TO_LOOK.get(card_topic, WHERE_TO_LOOK_DEFAULT)


def what_it_knows(text, memory):
    """What the answer in hand does know, when the follow-up asks something it never covered.

    "how do i soft boil an egg" is answered with the timings, and the follow-up "do i need to
    prick them" met "That's beyond what I know well, sorry. Searching for it will turn up better
    sources" - as if the chat had not already answered half of it. The card is still on the
    screen and the part of it that matters here is still true, so it comes back in the card's own
    words, and the bit the card does not cover is named as a gap with the one place that knows it.
    A search on its own is not a reply; this gives what the bot can, and only then points on.

    Narrow on purpose. The card has to be a knowledge card from the last few turns, the ask has
    to be a yes/no about a step, and the step has to be one the card never mentions - where the
    card does name it, the answer is already there and `the_part_asked` hands it back instead.
    """
    if not isinstance(memory, dict):
        return None
    clean = " ".join(str(text or "").lower().split()).strip(" ?!.")
    if not clean:
        return None
    whether = _whether_to(clean)
    if not whether:
        return None
    # The step, not the frame of the ask: "whether to preheat it" is about preheating, and
    # counting the word "whether" as part of it made every step read as one the card lacked.
    asked = [word for word in topics.words(" ".join(whether.split()[2:]))
             if len(word) > 2 and not word.isdigit() and word not in topics.STOPWORDS
             and word not in ASK and word not in ASK_VERB and word not in TIME
             and word not in FILLER and word not in SELF and word not in PART_STAND_INS]
    if not asked:
        return None
    seen_a_card = False
    gap = ""
    for back, turn in enumerate(reversed((memory.get("turns") or [])[-LOOK_BACK:]), 1):
        if not isinstance(turn, dict) or turn.get("module") != "answers":
            continue
        said = str(turn.get("bot") or "").strip()
        if not said or HEDGE.search(said) or said.rstrip().endswith("?"):
            continue
        if len(said) < 50:
            continue  # a stock line, not a card
        if set(asked) & _the_keys_of(said, memory):
            continue  # the card does answer this: not a gap
        on_the_card = {_a_stem(word) for word in re.findall(r"[a-z']+", said.lower())}
        named = [word for word in asked if _a_stem(word) in on_the_card]
        missing = [word for word in asked
                   if _a_stem(word) not in on_the_card and word not in A_QUALITY]
        if named and not missing:
            # The card says the step, in one form of the word or another, so there is no gap to
            # name: the sentence of it that carries the step is the answer, and no place is
            # offered for a figure the bot has just given.
            for sentence in _sentences(said):
                sentence = sentence.strip().rstrip(" ;")
                if len(sentence.split()) < 4 or sentence.lower().endswith("?"):
                    continue
                if {_a_stem(word) for word in asked} & {
                        _a_stem(word) for word in re.findall(r"[a-z']+", sentence.lower())}:
                    # The card says the step and then goes on about something else ("... with the
                    # door shut, with the shelf 10cm or so below the element"): the part that
                    # answers the ask is up to the colon, and handing the whole sentence back is
                    # the answer they have already read, which the composer sets aside.
                    head = sentence.split(":")[0] if ":" in sentence else sentence
                    if len(head.split()) < 4:
                        head = sentence
                    return head[:1].upper() + head[1:] + ("" if head[-1:] in ".!?\"" else ".")
            continue  # nothing of the card says it in a sentence of its own
        # The newest card comes first, and an older one is reached only when the newer cards do
        # not name the thing the line asks about: the answer to "how long until it works" is a cut
        # of the dog-lead card, and the sentence about the front-clip harness was in the card it
        # was cut from. The older card has to be on the subject of the chat as well.
        seen_a_card = True
        first_card = back <= 1 or not any(
            isinstance(t, dict) and t.get("module") == "answers"
            for t in (memory.get("turns") or [])[-back + 1:])
        if back > 1 and not _the_chat_is_still_on(said, memory):
            # The line itself often names nothing ("and should i put it in writing"), so the loose
            # test the rest of this module makes hands back a card the chat has nothing to do
            # with - the tired-child card, six turns into a chat about shift changes, with the NHS
            # site on the end of it. The card has to share a word with the last few lines.
            continue  # the chat has moved on
        if (back > 1 and not first_card
                and not _about_the_same_thing(str(turn.get("user") or ""), said, memory)):
            # An older card is only reached for when the chat is still on it as well: this is the
            # test every other reader of a card makes, and the newest card - the one on the
            # screen - does not have to pass it, because the subject of a fragment ("can i still
            # eat the ones that look alright") is not the subject of the card.
            continue  # the chat has moved on
        # The step has to be a step on the thing the card is about: said with a pronoun ("should
        # i cover it", "can i just use it on them") or with a word of the card's own ("should i
        # cover the chicken"). A bare move with neither - "should i rest" after an answer about
        # digging a bed - is a new question about the person, and handing back "Take one bed about
        # a metre by two" as the answer to a sore back is worse than saying it cannot call it.
        move_words = [w for w in whether.split()[2:] if w not in PART_STAND_INS]
        on_the_card = {_a_stem(word) for word in re.findall(r"[a-z']+", said.lower())}
        if not move_words[1:]:
            # "should i rest", "should i wait": the move has no object, so it is about the person
            # rather than about anything on the card. An answer about digging a bed settles nothing
            # about a sore back, and handing its step back as the reply is worse than saying so.
            continue
        part = ""
        lead = ""
        for sentence in _sentences(said):
            sentence = sentence.strip().rstrip(" ;")
            if len(sentence.split()) < 4 or sentence.lower().endswith("?"):
                # A card often opens with the whole answer in three words - "Bin it." on a bottle
                # left out too long - and dropping it because it is short leaves "a made-up bottle
                # is two hours old" as the reply to "can i just reheat it". So the short opening is
                # kept and put in front of the sentence that carries the detail.
                if not lead and sentence and not sentence.lower().endswith("?") \
                        and len(sentence.split()) >= 2 and not NOT_ALONE.match(sentence):
                    lead = sentence
                continue
            if _already_repeated(sentence, memory):
                continue
            if {_a_stem(word) for word in asked} & {
                    _a_stem(word) for word in re.findall(r"[a-z']+", sentence.lower())}:
                # The card's own sentence says the step, so there is no gap to name: "should i
                # keep driving" is answered by "Grinding means the pads are down to metal: stop
                # driving and get them changed", and telling them the rest is elsewhere would
                # talk over the answer already in hand.
                return None
            part = sentence
            break
        look = _where_the_rest_is(said, memory, turn, ask=clean)
        if not look:
            return None
        if not part:
            # The card has been read out in full already - every sentence of it is one the person
            # has just had - so there is no part of it left to hand back, and saying one again
            # would only repeat the answer. What is left of a fallback is still worth saying: the
            # step the card never covered, named, and the one place that covers it, read off the
            # card's own words. "will beer traps do anything" came to the search hedge because
            # "beer" reads as food and drink on its own; the card in hand is about slugs, and the
            # place that settles it is the garden one.
            # Held, not returned: a card further back may name the thing this one does not (the
            # answer to "how long until it works" is a cut of the dog-lead card, without the
            # sentence about the front-clip harness that the whole card has), and a card that
            # names it answers the line properly. The gap is only said once every card in reach
            # has been asked.
            gap = ("On " + whether + ", " + look + " will know more than I can - nothing I have"
                   " covers it.")
            continue
        head = part[:1].upper() + part[1:] + ("" if part[-1:] in ".!?\"" else ".")
        if lead:
            head = lead[:1].upper() + lead[1:] + " " + head
        if len(clean) % 2:
            return head + " On " + whether + ", " + look + " will know more than I can."
        return head + " That is what I can tell you; on " + whether + ", " + look + " will say."
    return gap or None


# The figures a person gives about their own life, asked back late in the chat. "i need 20 grand"
# on the second turn and "what was my deposit target again" eight turns later reached the
# knowledge machinery, which looks for an entry keyed on "deposit target", found none, and
# answered with the search hedge - while the figure was in the chat the whole time. The same
# with "and how many people" after "a roast on sunday for 8 people", "how long have i got until
# the move" after "we're moving house in 6 weeks", and "and how many bedrooms" after "its a 3 bed
# with a garden".
#
# `the_figure_asked` above answers an ask that names nothing at all, out of the bot's last answer.
# This is its other half: the ask names the thing the figure is for, and the figure is one the
# person gave themselves a few turns up. The shape is narrow, so a question about the world is
# never answered with a number out of the chat:
#   * the line has to ask for the figure back ("what was my ... again", "what did i say ...",
#     "how many/long/much ...") and be short;
#   * it has to name the thing the figure is for, and at least half of what it names has to be in
#     a line the person said - so "how many people live in london" does not take the eight from
#     the dinner, which is the one word it shares with it;
#   * the figure has to sit in that line or the two lines after it, so a number given for
#     something else in the same chat is not handed over;
#   * where the ask says which kind of figure it wants ("how many" against "how long"), only that
#     kind comes back, and a line with two different kinds on it hands nothing back at all.
GAVE_ASKS = re.compile(
    r"\bwhat(?:'s|s|\s+(?:was|were|is|are))\s+(?:my|our|the)\b"  # what was / what's my target
    r"|\bwhat\s+did\s+(?:i|we)\s+(?:say|tell)\b"            # what did i say i need
    r"|\bhow\s+(?:long|much|many|often|soon)\b"             # and how many people
    r"|\bwhat\s+was\s+it\s+(?:i|we)\b"                      # what was it i wanted
    # Pay asked for without "how much" in it: "what do i earn", "whats my wage". The word for the
    # pay is in the ask, so a figure given for something else in the chat is not its answer.
    # A word about when may stand between "my" and the pay: "whats my current salary" is the same
    # ask as "whats my salary", and it named nothing at all because the pay word was not the next
    # one. Not "monthly" or "gross": those name a different figure from the one they gave.
    r"|\bwhat(?:'s|s|\s+is|\s+are|\s+do|\s+does|\s+did)\s+(?:i|we|my|our)\s+"
    r"(?:(?:current|exact|actual)\s+)?"
    r"(?:earn|earns|earning|make|makes|paid|pay|pays|wage|wages|salary|salaries|income)\b", re.I)
# The words that only frame the ask, so they never count as the thing the figure is for. It is
# FIGURE_WORDS plus the ones this shape is built from - the remembering, the pointing back, and
# the words that hold an ask together.
ASK_FRAME = FIGURE_WORDS | frozenset("""
    said say says saying tell told telling mention mentioned remember remembers remember forgot
    recall earlier before after since again exactly actually probably guess think know my our
    the a an i we you it its thing things one ones number figure what whats which was were is are did
    do does have has had got left until till by about story now been
""".split())
# One figure, said the way people say it: money with its sign or its word, a length of time with
# its unit, and a count with the thing counted ("8 people", "3 bed", "40 boxes"). The count is
# last, so "20 grand" is money and "6 weeks" is a length of time before either is read as a count.
A_FIGURE = re.compile(
    r"(?P<money>£\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:k|grand|thousand|m)\b)?"
    r"|\b(?<![\d.])\d[\d,]*(?:\.\d+)?\s?(?:grand|k|quid|pounds?|dollars?|euros?|bucks)\b)"
    r"|(?P<time>\b(?<![\d.])\d[\d,]*(?:\.\d+)?\s*"
    r"(?:seconds?|secs?|minutes?|mins?|hours?|hrs?|days?|weeks?|wks?|months?|years?|nights?)\b"
    r"|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+"
    r"(?:seconds?|minutes?|hours?|days?|weeks?|months?|years?|nights?)\b"
    # "ive had it for a week", "about a month now", "a couple of days": people give a length
    # with an article far more often than with a number word, and "for a week now" was not a
    # figure at all, so a later "how long have i had it" found nothing to give back.
    r"|\b(?:about\s+|around\s+|nearly\s+|over\s+|under\s+)?(?:a|an)\s+"
    r"(?:second|minute|hour|day|week|month|year|night)\b"
    r"|\b(?:a\s+)?(?:couple\s+of|few|couple)\s+"
    r"(?:seconds?|minutes?|hours?|days?|weeks?|months?|years?|nights?)\b"
    r"|\bhalf\s+an?\s+(?:hour|day|week|month)\b)"
    # A share is a figure of its own, read whole: "the deposit is 10 per cent of 180 thousand" was
    # read as the count "10 per" and "what was the deposit again" answered "You said 10 per.",
    # with the rest of their words dropped. "20 percent" was already one figure; "20%" was none.
    r"|(?P<share>\b(?<![\d.])\d[\d,]*(?:\.\d+)?\s?(?:%|per\s?cent\b|percent\b))"
    r"|(?P<count>\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"(?<![\d.])\d[\d,]*(?:\.\d+)?)\s+[a-z][a-z-]{2,}\b)"
    # a bare figure is an amount when the ask asks how much: "i also owe 2000 on a credit card"
    r"|(?P<amount>\b(?<![\d.])\d[\d,]{2,}\b)", re.I)
# How many turns back the thing and its figure can be. Short on purpose: a long chat has other
# numbers by now, and the person means the one from the stretch they are still in.
GAVE_LOOK_BACK = 8
# The nouns that name the kind of figure rather than the thing it is for. "what was my deposit
# target again" is looked up by "deposit", not by "target": the ask says what it wants back, and
# the word for that is in the ask and in no line the person said.
# What a person is paid, said any of the ways there are. The figure is the same money whichever
# word is used for it, and only the word changed between the two lines: "i get paid 2000 a month"
# then "how much do i earn" got the search hedge, while "i earn 2000 a month" answered "You said
# 2000", and "my salary is 30000 a year" then "how much do i earn" the same. The words are stems,
# because "wages" and "earning" arrive with their endings on.
PAY_FAMILY = frozenset("""earn earning earned pay paid pays payslip wage salary income make making
made takehome""".split())
# A word that names pay, whether as the thing asked about or as the verb in the ask: "how much do
# i make" names the pay as plainly as "how much do i earn" and arrived naming nothing at all,
# because "make" is a stopword the keywords drop.
A_PAY_WORD = re.compile(
    r"\b(?:earn|earns|earning|earnings|pay|pays|paid|wage|wages|salary|salaries|income|"
    r"make|makes|making|made)\b", re.I)
# Pay asked for as a bare verb at the end of the ask: "how much do i make" wants the figure, and
# "what do i make of this" does not, so only the ask that stops there is read as an ask about pay.
A_PAY_VERB_AT_THE_END = re.compile(r"\b(?:make|makes|earn|earns|paid|pay)\s*[.?!]*\s*$", re.I)
# Pay asked about for a view rather than for the figure: "whats my pay like", "is my wage fair".
# The figure is theirs and it is true, and it is still not what they asked.
# Pay said as two words no keyword joins: "i take home 1800 a month" is the wage, and the store
# read "take home" as the shops - "how much do i earn" after it got the duty-free card.
A_TAKE_HOME = re.compile(r"\btak(?:e|es|en|ing)\s+home\b", re.I)
# "im on 2000 a month" is a wage said with no word of the family in it, like "take home".
A_IM_ON_A_FIGURE = re.compile(
    r"\b(?:i'?m|i am|we'?re|we are)\s+on\s+(?:about\s+|roughly\s+|around\s+)?"
    r"[\u00a3$£]?\s*\d", re.I)
A_PAY_JUDGEMENT = re.compile(
    r"\b(?:like|worth|enough|fair|reasonable|normal|average|typical|good|bad|ok|okay|"
    r"competitive)\b", re.I)
# A word about when, not about what: "whats my current salary" and "how much do i earn currently"
# add nothing the wage did not say, and they arrived naming a word in no line, so the pay ask was
# refused as a qualifier it is not. Only the pay asks drop these, because a qualifier anywhere else
# can be the whole question.
PAY_WHEN_WORDS = frozenset("""current currently presently now moment latest today exact exactly
    actual precisely roughly""".split())
# What kind of figure an ask wants, not which one: a length of time, and the words that point at
# their own trip with it. "days" in an ask is the unit the answer will be in, never the thing the
# figure was given for, so a bare one of these is not a thing for the ask to have named.
A_MEASURE_WORD = frozenset("""
    day days night nights week weeks weekend weekends month months year years hour hours minute
    minutes morning mornings afternoon afternoons evening evenings time times while""".split())
A_DOING_WORD = frozenset("""going away off there gone staying travelled traveled travelling
    traveling returning back doing""".split())


FIGURE_NOUNS = frozenset("""target amount total figure count number budget price cost age date
    sum score""".split())
# The words that name a goal and nothing else. An ask whose only content word is one of these
# names no thing for the figure, so the thing is the goal they set: "what was my target again"
# after "i'm trying to save 8000 for a van" is the 8000. The figure is read from the line that
# states the goal, not from a rate they put by, which is how they get there and not the target.
GOAL_NOUNS = frozenset("target goal aim objective ambition".split())
A_GOAL_LINE = re.compile(
    r"\b(?:save|saving|saved|need|needs|needed|want|wants|wanted|aim|aiming|goal|target|"
    r"objective|ambition|trying|try|plan|planning|afford)\b", re.I)
# A rate is how they reach the goal, not the goal: "i can put by 250 a month" is not the target
# when the line before it said "i'm trying to save 8000 for a van".
A_RATE_LINE = re.compile(
    r"\b\d[\d,.]*\s*(?:a|an|per|each|every)\s+"
    r"(?:day|week|month|year|fortnight)\b"
    r"|\b(?:a|per|each|every)\s+(?:day|week|month|year|fortnight)\b", re.I)
# A line that asks is not a figure given: "how many roast potatoes do i need for 8" has an eight
# in it, and it is the number they are waiting for, not one they gave.
A_QUESTION = re.compile(
    r"\W*(?:how|what|which|when|where|who|why|do|did|does|can|could|should|would|will|shall|"
    r"is|are|was|were|have|has)\b", re.I)


# "were away for 3 nights", "were going on friday", "were off to spain": people type "we're" as
# "were", and a line that opens with it is a statement about themselves, not a question. Read as a
# question the line gave no figure at all, so "how many nights is that" after it found nothing to
# give back and the chat punted. Only the words that really ask keep it a question: "were you
# there", "were there any problems", "were we meant to book". "were there friday to monday" is a
# statement too and is left unread, because "were there" alone is a question far more often.
A_WERE_ASKS = re.compile(
    r"\A\s*were\s+(?:i|you|we|they|he|she|it|there|any|all|none|not|this|these|those|either)\b",
    re.I)


def the_plain_line(line):
    """The line with "were" read as "we are" where that is what it says, and otherwise as it is."""
    text = str(line or "")
    if A_WERE_ASKS.match(text) or not re.match(r"\A\s*were\s+\w", text, re.I):
        return text
    return re.sub(r"\A(\s*)were\b", r"\1we are", text, count=1, flags=re.I)


# What stands in front of a length that makes it a rate rather than a length: "250 a month",
# "twice a week", "£20 a day", "once a fortnight", "each month".
A_RATE_OF_TIME = re.compile(
    r"(?:\d|\u00a3|\$|\u20ac)\s*$"
    r"|\b(?:once|twice|thrice|times|per|each|every|a|an)\s*$", re.I)
# What after a length makes it a time of day rather than a length had: "20 minutes before food",
# "an hour after the dose", "two weeks after the crash". "ago" is not here: "i started two weeks
# ago" is a length they have had.
A_SCHEDULED_AFTER = re.compile(r"\s*(?:before|after|past|prior\s+to)\b", re.I)
# A length they have in front of them, not a slot in the day: "i have 3 weeks till the first paper",
# "we've got two weeks until the move". The words in front of the figure say it is theirs to count.
A_HAS_THE_LENGTH = re.compile(r"\b(?:have|has|had|got|there's|there\s+are|there\s+is)\b", re.I)


# An ask that wants a name, a judgement or a conversion is not asking for a figure back, and a
# figure from the chat would answer a question they did not ask: "how much coffee is too much"
# after "i drink two coffees a day" is about coffee, not about their two, and "so 320 miles is how
# many km" is a sum. Both reached the figure reader because they share a word with the line that
# holds the number.
NOT_A_FIGURE_ASK = re.compile(
    r"\b(?:called|named|call|spell|spelt|means?|stand\s+for)\b"   # what are my dogs called
    r"|\btoo\s+(?:much|many)\b"                                    # how much coffee is too much
    r"|\benough\b|\bsafe\b|\bhealthy\b|\brecommend\b"
    r"|\b(?:is|are|was|were)\s+how\s+(?:many|much)\b"             # 320 miles is how many km
    r"|\bhow\s+do\s+i\b"
    # A total is added up, not remembered: "i spent 300 on food" and "i spent 50 on petrol", then
    # "how much have i spent" wants 350, and handing back the first figure is worse than nothing.
    # Unless the line says it is remembering: "how much did i say the flights were" is not a sum,
    # and its answer is the 300 they gave.
    r"|\bhow\s+much\s+(?:have|has|did)\s+(?:i|we|they)\b"
    r"(?!\s+(?:say|said|tell|told|mention|mentioned))"
    r"|\b(?:in total|altogether|all together|so far)\b",
    re.I)
# A plan of their own in the ask ("how long before the move should i start") still asks for the
# time they were given. It only makes an ask a question about the world when the figure wanted is
# a count or an amount: "how much coffee can i drink" after "i drink two coffees a day" is about
# coffee, and the two in the chat is not the answer.
A_PLAN_ASK = re.compile(r"\b(?:should|can|could|shall)\s+(?:i|we)\b", re.I)
# A question about the plan itself is not a question about a figure: "so whats the plan for
# cornwall then" wants the plan, and handing back the one duration in it - "You said a week." -
# answers something else. A plan is the composer's to give and no number stands in for it.
A_THE_PLAN_ASK = re.compile(
    r"\bwhat(?:'s|s|\s+is|\s+are|\s+was|\s+were)?\s+(?:the|a|our|my)\s+plan\b"
    r"|\bwhat\s+(?:do|does|should)\s+(?:i|we)\s+do\s+(?:first|next)\b", re.I)
# A duration asked back with nothing named at all: "and how long did i say its been", "how long
# have i had it now". `the_figure_asked` answers this shape out of the bot's last answer; this is
# the person's own line, which is where the two weeks came from in the first place. Only these
# wordings, because "how long do i leave it now" is the same shape and is a question about the
# world that the answer on the screen carries.
# The thing a recall ask names after the cue that asks for the figure back: "how many people did i
# say *the hall* holds" asks about the hall, and the 30 people in the chat are not the answer to
# it. The words after the cue are the rest of the person's own sentence, and only a noun phrase
# with a determiner in front of it names anything: "were coming" and "i do" continue the ask and
# name nothing.
A_THING_NAMED_AFTER_THE_CUE = re.compile(
    r"\b(?:did|do|does|was|were|am|are)\s+(?:i|we)\s+"
    r"(?:say|said|tell|told|think|want|wanted|need|needed|do|does|did)?\s*"
    r"(?:the|a|an|my|our|his|her|their|your)\s+[a-z]", re.I)
# The same for an amount: a line that names nothing and asks a figure back is answered from the
# one figure of that kind in the chat. "we need 30k for the deposit" then "how much do we need
# again" named no key the store keeps, so the figure reader answered nothing and the turn went to
# a card about deposits that said no figure at all.
A_BARE_AMOUNT_ASK = re.compile(
    # The pronoun has to end the ask: "and how much is that a year" asks for the amount turned into
    # a year, and handing the 300 back as "You said 300 now." answers a sum with the number in it.
    r"\bhow\s+much\s+(?:was|is|were|are)\s+(?:it|that|this|they|those|these)"
    r"\s*(?:again|now|then)?\s*[.?!]*\s*\Z"
    # The pronoun's verb has to be the whole ask: "how much do we need again" wants the 30k back,
    # while "how much do i need for a deposit" asks what a deposit takes and is a question about
    # the world - the 6000 they have put by is not the answer to it. A purpose or a subject after
    # the verb is what tells the two apart, so only a neutral tail may follow it.
    r"|\bhow\s+much\s+(?:did|do|does)\s+(?:i|we)\s+(?:say|need|want|have|owe|pay|spend|agree)"
    r"\s*(?:again|now|then|already|so\s+far|in\s+total|altogether|for\s+it)?\s*[.?!]*\s*\Z"
    r"|\bremind\s+me\s+how\s+much\b", re.I)
A_BARE_DURATION_ASK = re.compile(
    r"\bdid\s+i\s+(?:say|want|choose|pick)\b"
    r"|\bhow\s+long\s+(?:am|are|was|were)\s+(?:i|we)\s+"
    r"(?:going|away|out|there|staying|off)\b"
    r"|\bhow\s+long\s+have\s+i\s+had\b|\bhave\s+i\s+had\b"
    r"|\bhow\s+long\s+(?:has|have)\s+(?:it|that|this)\s+been\b"
    r"|\bhow\s+long\s+(?:was|is)\s+(?:it|that)\b", re.I)
# The same ask with the thing named instead of the pronoun: "how long has my back been like this
# now" says the back, so the bare shape above stood down and the entry for a back took the turn -
# three turns after the person had said "my lower back has been sore for about 3 weeks", the reply
# told them how to keep a back quiet instead of the three weeks. It is a construction and not a
# word list: how long + has/have + a phrase with a possessive in it + been + a tail that points
# back at the thing in hand. "how long has my chicken been in the fridge" is not one - its tail
# says where the chicken is, not that it is the same chicken the chat has been on.
A_HOW_LONG_ITS_BEEN = re.compile(
    r"\bhow\s+long\s+(?:has|have|had)\s+(?:[\w']+\s+){1,5}been\s+"
    r"(?:like\s+(?:this|that)|going\s+on|that\s+way|this\s+way|now|so\s+far)\b", re.I)
_OWNS_THE_THING = re.compile(r"\b(?:my|our|his|her|their|the)\b", re.I)


def how_long_its_been(text):
    """True when the line asks how long the person's own thing has been like this."""
    found = A_HOW_LONG_ITS_BEEN.search(" ".join(str(text or "").lower().split()))
    return bool(found and _OWNS_THE_THING.search(found.group(0)))
# A line that asks is not a line that gives one back: "and how much is that a year" carries "a
# year" inside the question, and a length a person gave about their own life is the other kind of
# line. The leading "and", "but", "sorry" and the like are stripped first, so a question that
# opens softly is still a question.
A_LINE_THAT_ASKS = re.compile(
    r"\A(?:\W*(?:and|but|so|ok|okay|also|then|well|now|hmm|oh|yeah|yes|right|actually|sorry|"
    r"plus|just)\b[\s,]*)*" + A_QUESTION.pattern, re.I)
# A line that takes a figure back: "no, 45", "actually three", "make it 900". Only a correction
# that carries a figure of the same kind changes what comes back - "no pork remember" takes back
# no number, and the eight in the dinner is still the answer to "and how many people". It has to
# open the line: "no, 45", "sorry, 3 cats", "my mistake, 800", "make it
# 900". Three words in, "i want to make it to 30 countries" is a plan and not a figure taken
# back, and it was read as one because it says "make it".
A_CORRECTION = re.compile(
    r"^[\s,.\-]*(?:(?:oh|ok|okay|and|but|so|well|sorry|no|nope|actually|wait|oops|correction|"
    r"my mistake|it'?s)\b[\s,;:.-]*){1,3}"
    r"|^[\s,.\-]*(?:make\s+(?:it|that)|i\s+mean|we\s+mean|scratch\s+that|i\s+meant|"
    r"we\s+meant)\b", re.I)
# A correction word at the end of the line is the same correction: "we have two cats" then "its 3
# actually" takes the two back the way "no, 3 cats" does. The shapes above all open with the word,
# so this line was never read as a correction and the ask "how many cats do i have" answered "You
# said two cats." over a store that held three. The head has to state nothing of its own - the
# same rule the memory readers use - or "my mum is 70 actually" would put its 70 in the budget.
A_MARKER_AT_THE_END = re.compile(r"\s+(?:actually|really|honestly)\s*[.!?]*\s*$", re.I)

def _a_line_that_corrects(line):
    """Whether a line takes a figure back, whether it opens with the word or ends with it."""
    said = str(line or "")
    if A_CORRECTION.search(said):
        return True
    found = A_MARKER_AT_THE_END.search(said)
    if found is None:
        return False
    head = said[:found.start()].strip()
    if not head or len(head.split()) > 8:
        return False
    return not facts.extract(head)

# A correction says a number even when the figure reader cannot read it: "actually there are three
# of them" takes the two back and gives no figure of its own, so nothing safely comes back.
A_NUMBER_WORD = re.compile(
    r"\b(?:\d[\d,]*(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|"
    r"twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|"
    r"forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand)\b", re.I)
# The words after a counted figure that join it to the rest of the sentence: "500 for the trip" is
# five hundred and not "500 for", and "300 each" keeps its each.
JOINERS = frozenset("""a an the and or but so of to in on at for with from by as then that this
    is are was were it them us you""".split())
# The words that join a figure to the rest of the sentence: a preposition, a joiner, or the reason
# the figure was corrected or explained. None of them is the figure, so none is said back with it.
FIGURE_TAIL = JOINERS | frozenset("""because cos coz cuz cause since""".split())

# A line that adds to a counted thing: "actually one more is coming", "another ones coming",
# "plus one of my mates". The count said before it is no longer the count they have, the same way
# a loss makes it out of date - and a stale count handed back as "you said 8 people" is worse
# than the card that knows nothing.
A_ONE_MORE = re.compile(r"\b(?:more|extra|other|others|fewer|less)\b", re.I)
A_GAIN = re.compile(
    r"\b(?:one|two|three|four|\d+|another)\s+(?:more|extra|other)\b"
    r"|\banother\s+(?:one|guest|person|adult|kid|child|friend|mate|of)\b"
    r"|\bplus\s+(?:one|two|three|\d+)\b|\bone\s+of\s+(?:my|our)\b", re.I)
A_GROUP_WORD = re.compile(r"\b(?:us|we|them|they|people|guests?|party)\b", re.I)
# A line that takes one of a counted thing away: "one of them died last week", "we gave the cat
# away". The count in the chat is no longer the count they have, and the store reads these itself.
A_LOSS = re.compile(
    r"\b(?:died|passed away|put (?:him|her|it|them) down|gave\b[^.?!]{0,20}\baway"
    r"|rehomed|sold|stolen|went missing|ran away|eaten|no longer|not any ?more)\b"
    r"|\bone\s+of\s+(?:them|those|these|the)\b|\bgave\s+one\b|\bone\s+(?:away|off|back)\b",
    re.I)


# A list of ages: "aged 4 and 7", "aged four and seven", "4 and 7 years old". A line shaped like
# that is naming the members of a group one by one, and the size of the group is how many members
# there are - so the first number in the list is not the count. "i have kids aged 4 and 7" asked
# "how many kids do i have" was answered "You said 4 kids."
_A_AGE = r"(?:\d[\d,]*(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
A_LIST_OF_AGES = re.compile(
    r"\b(?:aged?|ages)\s*" + _A_AGE + r"\b\s*(?:and|&|,)\s*" + _A_AGE + r"\b"
    r"|\b" + _A_AGE + r"\b\s*(?:and|&|,)\s*" + _A_AGE
    + r"\b\s*(?:years?|yrs?)(?:\s+old)?\b",
    re.I)


def _a_list_of_ages(line):
    """Whether the line lists ages, which names the members of a group rather than its size."""
    return bool(A_LIST_OF_AGES.search(str(line or "")))


def _something_gone(lines, at, words):
    """Whether a later line says one of the counted things is gone, so the count is out of date."""
    for later in lines[at + 1:]:
        if not later:
            continue
        if A_GAIN.search(later) and A_GROUP_WORD.search(later):
            # "one more is coming" / "another of my mates is coming too": the group grew, so the
            # count given before it is not the count they have.
            return True
        if not A_LOSS.search(later):
            continue
        said = topics.keywords(later)
        if any(_the_same_word(word, other) for word in words for other in said):
            return True
        if "one" in A_LOSS.search(later).group(0).lower():
            return True   # "one of them died", "we gave one away": a count that went down
    return False


# The ask's own word for the thing counted: "how many missed calls do i have" is calls. The
# figure regex takes the words after the number as far as it can, so "5 missed calls" comes back
# as "5 missed" and "i weigh 80 kilos" as "80 kilos": the ask puts the noun back.
COUNT_ASK = re.compile(r"\bhow\s+many\s+([a-z'&-]+(?:\s+[a-z'&-]+){0,3})", re.I)
# A period word names when a thing happens, not how many of a thing there are. "how many a week
# do we have" after "we get a takeaway three times a week" was answered "You said three week." -
# the count of weeks is nothing they gave, and the sentence reads as a mistake. Where the figure on
# their line is a rate, the ask is the rate said back, and `bot/memory/rates.py` has the words for
# it (`You get a takeaway three times a week.`), so this reader steps out of the way.
PERIOD_WORD = frozenset("""hour hours day days week weeks fortnight fortnights month months
    year years night nights morning mornings evening evenings weekend weekends christmas""".split())
A_RATE_IN_THE_FIGURE = re.compile(
    r"\b(?:once|twice|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d+)\s+times?\b"
    r"|\bevery\s+(?:\w+\s+)?(?:hour|day|week|fortnight|month|year|morning|evening|night|weekend)\b",
    re.I)


# A figure written as a word and the same figure written as a digit, so "for eight" in an ask and
# "8 people" in a line are read as one number rather than two.
THE_SAME_NUMBER = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7",
    "eight": "8", "nine": "9", "ten": "10", "eleven": "11", "twelve": "12", "fifteen": "15",
    "twenty": "20", "thirty": "30", "forty": "40", "fifty": "50", "sixty": "60",
    "seventy": "70", "eighty": "80", "ninety": "90", "hundred": "100", "thousand": "1000",
}
A_PLURAL_ONLY_NOUN = frozenset("""people children men women feet teeth""".split())


def _the_ask_gave_that_figure(number, clean):
    """Whether the ask itself names the figure the reading found.

    A number in the ask - "for 8", "how many for 10 people" - is the ask's own quantity, so it is
    not a figure the person gave earlier and saying it back claims a recall that did not happen.
    """
    number = str(number or "").strip().lower()
    if not number:
        return False
    first = number.split()[0]
    looked = {first, THE_SAME_NUMBER.get(first, first)}
    for other in A_NUMBER_WORD.findall(clean):
        if other == first or THE_SAME_NUMBER.get(other, other) in looked:
            return True
        if other[:1].isalpha() and first[:1].isalpha() and _the_same_word(first, other):
            return True
    return False


def _a_count_of_one_with_a_plural(number, noun):
    """Whether a count of one is about to be said with a noun in the plural: "one people"."""
    if str(number).strip().lower() not in ("1", "one", "a", "single"):
        return False
    word = (noun.split() or [""])[-1].lower()
    if not word:
        return False
    return word in A_PLURAL_ONLY_NOUN or word.endswith("s")


def _the_thing_counted(clean, said):
    """The ask's word for the thing counted, with the figure's own modifier when it has one."""
    match = COUNT_ASK.search(clean)
    if not match:
        return ""
    phrase = match.group(1).split()
    words = [word for word in phrase
             if word not in topics.STOPWORDS and word not in ASK_FRAME
             and word not in FIGURE_NOUNS]
    if not words:
        return ""
    tail = said.split()[-1].lower()
    # "two flat tyres" / "5 missed calls": the ask says the modifier in front of the noun, so the
    # whole pair is the thing, and "two tyres" would drop a word the person said.
    for one, other in zip(phrase, phrase[1:]):
        if other in words and _the_same_word(one, tail):
            return one + " " + other
    for word in words:
        if _the_same_word(word, tail):
            return word
    return words[-1]


def _figures_in(line):
    """The figures a line gives, as (kind, the words used, the number, whether it counted).

    A figure that belongs to somebody else is not one they gave: "my mum has three brothers" is
    the mother's count, and "how many brothers do i have" must not be answered with it. The
    subject of the clause is read by the store's own reader (`facts.subject`), so a relation, a
    pronoun or a name is somebody else everywhere at once.
    """
    text = str(line or "")
    if not text or "?" in text or A_QUESTION.match(text):
        return []
    out = []
    for match in A_FIGURE.finditer(text):
        if match.group("time") and A_RATE_OF_TIME.search(text[:match.start()]):
            # "im putting by 250 a month", "twice a week", "£20 a day": a rate, not a length. The
            # article form above reads the "a month" in it, and a later "how many months is that
            # again" - the sum the chat worked out - was answered "You said a month.".
            continue
        if (match.group("time") and A_SCHEDULED_AFTER.match(text[match.end():])
                and not A_HAS_THE_LENGTH.search(text[:match.start()])):
            # "i take the tablets 20 minutes before food" is when to take them, not a length they
            # have had: "how long have i had it now" answered "You said 20 minutes." But "i have 3
            # weeks till the first paper" is a length they have, and the count is theirs.
            continue
        said = " ".join(match.group(0).split()).rstrip(" ,.;:")
        if not said:
            continue
        if match.group("count") and A_ONE_MORE.match(" ".join(said.split()[1:])):
            # "actually one more is coming so theres 10 of us now": a count word with "more",
            # "extra" or "other" after it is how many were added, not how many there are. Read as
            # a count it answered "how many people is it for again" with "One people".
            continue
        try:
            whose, _who = facts.subject(text, match.start())
        except Exception:  # noqa: BLE001 - a reading that cannot run keeps the figure theirs
            whose = ""
        if whose == "other":
            continue
        counted = match.group("count") is not None
        kind = "time" if match.group("time") else "amount"
        if match.group("share"):
            # Said back whole and never as a count: "You said 10 per cent." A share is the figure
            # the person gave, and every way of writing one reads the same.
            digits = re.match(r"\s*([\d][\d,]*(?:\.\d+)?)", match.group(0))
            number = digits.group(1) if digits else said
            out.append((kind, number + " per cent", number, False))
            continue
        if counted and said.lower().endswith(" per"):
            # "3 per box" is three of them: "per" joins a count to what it is counted in, so it
            # comes off with the rest of the tail rather than being said back as part of it.
            said = said[:-4].rstrip(" ,.;:")
        # The words a figure is joined to the rest of the sentence by are not part of it: "500
        # for the trip" is five hundred, not "500 for", and a figure given with the reason it
        # changed - "actually i mean 75 because i lost some" - is 75, not "75 because". Both
        # shapes were handed back whole ("You said 75 because."), so the tail comes off every
        # figure and not only a count.
        words = said.split()
        while len(words) > 1 and words[-1].lower() in FIGURE_TAIL:
            words.pop()
        # The punctuation is the sentence's, not the figure's: "actually my brother cant come so
        # 5, and theres a dog" is read as the count "5, and", and the comma stayed on the number -
        # "You said 5,." and "5, - that's what you told me." both said it back with a comma that
        # belongs to the sentence. A comma is part of the number only when there are digits on
        # both sides of it ("£1,500"), so any other one ends the figure: "its 2, not 3" is 2.
        said = re.split(r"(?<!\d),|,(?!\d)", " ".join(words))[0]
        said = said.rstrip(" ,.;:")
        number = (said.split()[0] if counted else said).rstrip(" ,.;:")
        if not number:
            continue
        out.append((kind, said, number, counted))
    return out


# Money paid for a thing is not the thing. "we paid 2000 for the venue" gives a figure for what
# the venue cost, and "what did i say the venue was" asks what the venue *is* - the name of the
# place, which that line never gave. The figure was handed over anyway ("You said 2000."), so the
# person asking what the venue was got its price. An ask for the money carries its own word for
# it ("how much did i say the venue was", "what did i say i paid for the venue"), and then the
# figure is the answer.
_MONEY_PAID_FOR = re.compile(
    r"\b(?:paid|pay|pays|spent|spend|cost|costs|charged|gave|give|offered|quoted|put|set)\b"
    r"[^.?!]{0,25}?[\u00a3$\u20ac]?\s?\d[\d.,]*[^.?!]{0,25}?\b(?:for|on|towards)\b", re.I)
_AN_AMOUNT_WANTED = re.compile(
    r"\bhow\s+(?:much|many)\b|\bcost\b|\bcosts\b|\bprice\b|\bpaid\b|\bpay\b"
    r"|\bspent\b|\bspend\b|\bbudget\b|\bfee\b|\btotal\b|\bworth\b", re.I)


def _money_paid_for_a_thing(clean, line):
    """True when the line's figure is money spent on a thing, and the ask wants the thing itself."""
    if _AN_AMOUNT_WANTED.search(clean):
        return False
    return bool(_MONEY_PAID_FOR.search(line))


def _one_figure(found, kind):
    """The figure of the kind asked for, or () when the line holds none or holds two kinds."""
    if not found:
        return ()
    if kind:
        found = [one for one in found if one[0] == kind]
    elif len({one[0] for one in found}) > 1:
        return ()   # a length of time and an amount on one line: which one is not known
    return found[0] if found else ()


def _a_bare_count(figure):
    """Whether a figure is the number on its own, with nothing saying what it counts.

    The span line is written for a figure a person gave in their own words with its unit -
    "\u00a3250 a month - that's what you told me" - and with no unit in it the line reads as a
    template cut short. A count said back is just the count: "You said 5."
    """
    words = str(figure or "").split()
    return len(words) == 1 and bool(A_NUMBER_WORD.fullmatch(words[0]))


def _the_same_word(one, other):
    """Whether two words are the same thing said twice: "move" and "moving", "bed" and "bedrooms"."""
    first, second = topics.stem(one), topics.stem(other)
    if first == second:
        return True
    if topics.forms(first) & topics.forms(second):
        # The same verb with an ending on and off: "how much was i *putting* away" asks about the
        # line that said "i *put* 400 a month away", and "putting" and "put" share no prefix. The
        # short forms are the ones the prefix rule below cannot reach, so they are matched as a
        # family (topics.forms), which is how the rest of the store reads a word family.
        return True
    # A room counted by its name and by its rooms: "its a 3 bed", "how many bedrooms". The short
    # word is too short for the prefix rule below, and it is the shape people use for a house.
    for shorter, longer in ((first, second), (second, first)):
        if longer.endswith("room") and longer[:-4] == shorter:
            return True
    if first in PAY_FAMILY and second in PAY_FAMILY:
        # Pay said as a wage on one line and as being paid on another: the same money, so the ask
        # under either word is answered by the figure given under the other.
        return True
    return (len(first) >= 4 and len(second) >= 4
            and (first.startswith(second) or second.startswith(first)))


def _the_corrected(lines, at, kind, found):
    """The figure a later line takes back to, or the one it was given, or () when it is unsure.

    "my budget is 500" / "make it 900" / "what is my budget": the last figure they said for the
    thing is the one they mean. A correction with no figure in it ("no pork remember") takes
    nothing back, so the figure stands.
    """
    for later in lines[at + 1:]:
        if not later or not _a_line_that_corrects(later) or A_LINE_THAT_ASKS.search(later):
            continue    # "and how much is that a year" opens like a correction and asks a question
        got = _one_figure(_figures_in(later), kind)
        if got:
            found = got
        elif A_NUMBER_WORD.search(later) and kind != "time":
            # A number was taken back and the new one cannot be read: say nothing. A length is
            # the one kind where a bare number is not a length at all - "its a 3 bed with a
            # garden" opens like a correction and carries the 3 of the bedrooms, and reading it
            # as a new length took back the six weeks the person gave about the move.
            return ()
    return found


# A recall ask points back with the person's own words: "what did i tell you", "did i say".
A_TOLD_BACK = re.compile(
    r"\b(?:did\s+i\s+(?:say|tell|mention)|what\s+did\s+i\s+(?:say|tell)"
    r"|what\s+was\s+it\s+i\s+(?:said|told)|how\s+(?:long|many|much)\s+did\s+i\s+(?:say|tell))\b",
    re.I)
# Words that frame a recall ask and never name the thing a length is about. "sorry" and "going"
# get there from the apology shape, and both would otherwise count as the thing asked about.
NOT_A_THING_ASKED = frozenset((
    "sorry", "apologise", "apologize", "going", "told", "tell", "said", "say", "mention",
    "remember", "again", "asked", "ask"))


def _the_length_they_mean(clean, lines, spoken=()):
    """The length a recall ask points at, in the person's own words, or "".

    Two lengths in a chat is normally a question of which, so the thing the ask names decides:
    "how long did i tell you the headaches been going on" picks the line about the headache even
    when the person also said a root canal was a month ago. With nothing named to go on, the one
    length they gave anywhere is the answer, and a corrected one is read as corrected. Anything
    still unclear is left to the module that knows the thing, so this says "" rather than guess.

    `spoken` is what the bot itself said in the same window. A word of the ask that no line of
    theirs carries is not always a new thing: "sorry, how long did i tell you it has been sore"
    after "i hurt my shoulder about a week ago" was left unanswered because the person's line says
    "hurt" and the ask says "sore", a word only the replies had used. When every word the ask adds
    to the cue is a word the chat has already used, the ask is naming nothing new and the one length
    in the chat is the one they mean - while "how long did i say the shop was open" still names a
    thing the chat has never mentioned, and is still left alone.
    """
    wanted = [word for word in topics.keywords(clean)
              if word not in ASK_FRAME and word not in NOT_A_THING_ASKED]
    if wanted and spoken:
        theirs = [other for line in lines for other in topics.keywords(line)]
        heard = [other for line in spoken for other in topics.keywords(line)]
        new = [word for word in wanted
               if not any(_the_same_word(word, other) for other in theirs)]
        if new and all(any(_the_same_word(word, other) for other in heard) for word in new):
            wanted = []
    named, anywhere = [], []
    for back, line in enumerate(lines):
        if A_LINE_THAT_ASKS.search(line):
            continue    # a question the person asked is not a length the person gave
        figures = [one for one in _figures_in(line) if one[0] == "time"]
        if not figures:
            continue
        anywhere.append((back, figures))
        words = topics.keywords(line)
        if any(_the_same_word(word, other) for word in wanted for other in words):
            named.append((back, figures))
    # When the ask names something, only a line that names it counts: "how long did i say the shop
    # was open" is not answered with the length of the commute just because that is the only length
    # in the chat. With nothing named, the one length they gave anywhere is the answer.
    for pool in ((named,) if wanted else (named, anywhere)):
        if not pool:
            continue
        distinct = {one[1].lower() for _back, figures in pool for one in figures}
        if len(distinct) == 1:
            back, figures = pool[-1]
            # "my back has hurt for two weeks" / "actually its been three weeks" - the later line
            # is the one they mean, and it names neither the back nor anything else.
            later = _the_corrected(lines, back, "time", figures[-1])
            return (later or figures[-1])[1]
        if A_CORRECTION.search(lines[pool[-1][0]]):
            return pool[-1][1][-1][1]
    return ""


def _the_figure_of_a_goal(lines, kind, wanted=()):
    """The figure on the line where the person set a goal, or () when there is none.

    A goal is the amount they are trying to reach, so a rate they put by is skipped even though
    it is a figure of the same kind. Where the line states both an amount and a length ("save
    8000 over two years") and the ask names neither ("what was my target again"), the amount is
    the target and the length is how long it takes. A word the ask adds besides the goal noun
    ("the van", "savings") narrows which goal it is, so the line has to carry it too.
    """
    for at, line in enumerate(lines):
        if not line or A_LINE_THAT_ASKS.search(line) or not A_GOAL_LINE.search(line):
            continue
        if A_RATE_LINE.search(line):
            continue
        words = topics.keywords(line)
        narrowing = [word for word in wanted if word not in GOAL_NOUNS]
        if not all(any(_the_same_word(word, other) for other in words) for word in narrowing):
            continue
        found = _one_figure(_figures_in(line), kind)
        if not found and kind is None:
            found = _one_figure(_figures_in(line), "amount")
        if found:
            # A later line that puts the goal right is the goal: "i need 20 grand" / "make it
            # 30" / "what was my target again" is the 30.
            return _the_corrected(lines, at, kind, found)
    return ()

def _the_figure_counts_the_thing(text, figure):
    """True when a figure is an answer to an ask that names a thing, or the ask names nothing.

    A number answers a number's question, and an ask that names the thing it wants back is not
    one: "what did i say about lisbon", asked after "im saving 3000 for a trip to lisbon" and
    "the flights are about 120 each", was answered "You said 3000." - a figure given two lines
    after the thing the ask named, with nothing on it to say what the figure is of. The same
    shape answered "what did i say about the tap" with "About a week", a length from a line about
    something else.

    So the figure comes back only when it carries the thing asked about ("what did i say about
    the cats" after "i have two cats" is "two cats"). When it does not, the answer is the line
    that names the thing, chosen by the one check in bot/memory/history.py and quoted below.
    """
    thing = history.the_thing_they_named(text)
    if not thing:
        return True
    named = set(topics.content(thing))
    return bool(named & set(topics.content(str(figure or ""))))


# A line that narrows or qualifies the one before it and says nothing on its own. It is short, and
# its thing is the thing in the line above it: "the ones that are open on sunday", "the cheaper
# ones", "ones open late", "closed ones too", "not too scary", "something shorter", "since
# tuesday", "wide ones". Each is a person narrowing the answer in front of them, not a fact about
# them, and quoted on its own it is their fragment with nothing in it.
A_NARROWING_ONLY = re.compile(
    r"""^(?:(?:ok|okay|and|or|also|but|then|so|just|only|maybe|actually)[\s,]+)*
        (?:
            (?:the|those|these|any|some|other|both|all)(?:\s+[a-z']+){0,3}\s+(?:one|ones)
          | (?:one|ones)
          | [a-z']+\s+(?:one|ones)
          | (?:something|anything|everything)\s+[a-z']+
          | (?:not|no)\s+(?:too|very|that|so|more|as)\s+[a-z']+
          | (?:a\s+bit\s+)?(?:cheaper|closer|nearer|bigger|smaller|longer|shorter|quicker|faster|
                easier|simpler|warmer|colder|quieter|lighter|nicer|better|worse)\b
          | (?:since|before|after|from|until|till|by|around|near|in|on|at)\s+[\w' ]{1,24}
        )
        (?:\s+[a-z']+)*
        \s*[.!]?$""", re.I | re.X)

# How long a line can be and still be a narrowing: past seven words it carries a thing of its own
# ("the ones that are open on sunday and deliver, place at the corner of the high street").
A_NARROWING_WORDS = 7

def a_narrowing_and_its_line(line, memory):
    """The line `line` narrows, with `line` after it, or None.

    A recall finds the line that carries the word asked about, and the last one can be a narrowing
    of the line above it: "any chemist in the area" / "the ones that are open on sunday", then
    "what did i say about sunday". The only line with "sunday" in it is the narrowing, so the
    answer was `You said: "the ones that are open on sunday"` - their own fragment, which says
    nothing about them and nothing about the chemist either. What they are asking about is the
    line the fragment narrows, so it is said with the narrowing after it.

    The narrowing must be the line *right after* the one it narrows: a short line three turns
    later is about whatever that turn was about. It must be a narrowing on its own terms (see
    `A_NARROWING_ONLY`), so "i bought new tyres" is never read as one, and the line it narrows
    must state a thing - a question narrowed is the chat still looking for the thing.
    """
    said = " ".join(str(line or "").split())
    if not said or "?" in said or len(said.split()) > A_NARROWING_WORDS:
        return None
    if not A_NARROWING_ONLY.match(said):
        return None
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return None
    lines = [" ".join(str(turn.get("user") or "").split()) for turn in turns
             if isinstance(turn, dict)]
    places = [at for at, text in enumerate(lines) if text == said]
    if not places or not places[-1]:
        return None
    before = lines[places[-1] - 1]
    if (not before or "?" in before or len(before.split()) < 2
            or not topics.content(before) or A_NARROWING_ONLY.match(before)):
        return None
    return before, said

def _the_turn_that_names_it(text, memory):
    """The line they said about the thing the ask names, quoted back, or None."""
    row = history.the_earlier_turn(memory, text)
    line = " ".join(str((row or {}).get("user") or "").split()).rstrip(" .!?")
    if not line:
        return None
    pair = a_narrowing_and_its_line(line, memory)
    if pair:
        # "the ones that are open on sunday" alone says nothing: the thing asked about is in the
        # line it narrows, so both are said (`a_narrowing_and_its_line`).
        before, after = pair
        return pick(["You said: \"" + before + "\" \u2014 then \"" + after + "\".",
                     "Your own words were: \"" + before + "\", then \"" + after + "\".",
                     "That was: \"" + before + "\" \u2014 then \"" + after + "\"."], memory)
    return pick(["You said: \"" + line + "\"",
                 "Your own words were: \"" + line + "\"",
                 "That was: \"" + line + "\""], memory)


def the_figure_they_gave(text, memory):
    """The figure a person gave earlier and asks for again, or None.

    Only a line that asks for the figure back, names the thing it is for, and has that thing and
    the figure in the chat within the last few turns is answered. Everything else is left to the
    module that knows about the thing asked.
    """
    if not isinstance(memory, dict):
        return None
    clean = " ".join(str(text or "").lower().split())
    if not clean or len(clean.split()) > 16 or not GAVE_ASKS.search(clean):
        return None
    if NOT_A_FIGURE_ASK.search(clean):
        return None
    # A "how many" ask is a count, and the count store keeps counts as counts: "i have two
    # brothers and one sister" is filed as two numbers, so "how many brothers and sisters do i
    # have" is answered from both. Read here as a figure said back it returned only the first
    # number ("You said two brothers."), and the sister was dropped. Where the store holds the
    # count, the store's answer is the whole one. A count another reader keeps (children, cats)
    # is left to that reader, which knows the word the person used.
    counting = COUNT_ASK.search(clean)
    if counting:
        counted = counts.answer(clean, memory)
        if counted:
            return counted
        if any(word in counts.THEIRS for word in counting.group(1).split()):
            return None
    wanted = [word for word in topics.keywords(clean) if word not in ASK_FRAME]
    if A_PAY_WORD.search(clean):
        # "whats my current salary": the word after "my" says when the figure is wanted, not which
        # figure, and it is in no line they said, so it must not stand in the way of the pay word
        # that is. "whats my salary after tax" keeps "tax" and is still refused.
        wanted = [word for word in wanted if word not in PAY_WHEN_WORDS]
    if not wanted and A_PAY_WORD.search(clean) and A_PAY_VERB_AT_THE_END.search(clean):
        # "how much do i make" carries its pay in a word the keywords drop, so the ask named
        # nothing at all and the figure in the chat went unread: the family word stands in.
        wanted = ["pay"]
    if len(wanted) > 4:
        return None    # too much to be about one thing
    goal_named = any(word in GOAL_NOUNS for word in wanted)
    # "how many times a week" asks how often, and no count is that answer: the kind is read from
    # the most particular frame first, because "how many" alone would take a distance for it.
    kind = None
    for name in ("often", "time", "heat", "amount"):
        for one_name, ask, _figure in FIGURE_ASKS:
            if one_name == name and ask.search(clean):
                kind = name
                break
        if kind:
            break
    if kind in (None, "amount", "heat") and (A_PLAN_ASK.search(clean)
                                             or A_THE_PLAN_ASK.search(clean)):
        return None
    # The lines are read as the person typed them, so "were away for 3 nights" is a statement and
    # not a question: see `the_plain_line`.
    all_lines = [the_plain_line(str(turn.get("user") or "")) for turn in (memory.get("turns") or [])
                 if isinstance(turn, dict)]
    lines = all_lines[-GAVE_LOOK_BACK:]
    spoken = [str(turn.get("bot") or "") for turn in (memory.get("turns") or [])
              if isinstance(turn, dict)][-GAVE_LOOK_BACK:]
    # An ask that points back with the person's own words ("did i tell you", "what did i say") and
    # asks a length: the length they gave is the answer even when the thing named is not one of
    # the words on the line. "sorry, how long did i tell you the headaches been going on" after
    # "ive had a headache for four days" matched no line - the ask says "headaches", the line says
    # "headache", and "sorry" and "going" are the only other words - so the chat read the apology
    # and left the question. A length a person gives about their own life is theirs.
    if kind == "time" and A_TOLD_BACK.search(clean):
        said = _the_length_they_mean(clean, lines, spoken)
        if said:
            if not _the_figure_counts_the_thing(clean, said):
                return _the_turn_that_names_it(text, memory)
            return pick(["You said " + said + ".",
                         said[:1].upper() + said[1:] + " \u2014 that's what you told me."],
                        memory)
    if goal_named:
        # A goal is set once and asked about many turns later, so it is read from the whole chat
        # and not the last few lines: "i'm trying to save 8000 for a van", ten turns of other
        # talk, then "what was my target again" is still the 8000. The shorter window is for the
        # figures a line gives in passing, which a later line can take back.
        found = _the_figure_of_a_goal(all_lines, kind, wanted)
        if found:
            figure = found[1]
            return pick(["You said " + figure + ".",
                         figure[:1].upper() + figure[1:] + " \u2014 that's what you told me."],
                        memory)
    if wanted:
        # A word the ask adds after the figure it wants back is not the thing the figure is for:
        # "how many people did i say were coming" asks about the people, and "were coming" is the
        # rest of their own sentence. A word that is in no line they said cannot be what the
        # figure was given for, so it is dropped and the words that are in a line are the ones
        # looked for. With every word dropped the ask names nothing at all, and the bare shape
        # below decides whether one figure in the chat is the answer.
        said = [other for line in lines for other in topics.keywords(line)]
        # "take home" is the pay said in two words with no word of the family in it, and the two
        # are not a keyword the way "wage" is: the phrase stands for the family word.
        said += ["takehome" for line in lines if A_TAKE_HOME.search(line)]
        # "im on 2000 a month" is a wage with no word of the family in it. It is kept as one
        # so the ask for the pay is answered by it: the store files that line under the
        # budget, and "how much do i make" named nothing at all before this.
        said += ["pay" for line in lines if A_IM_ON_A_FIGURE.search(line)]
        kept = [word for word in wanted
                if any(_the_same_word(word, other) for other in said)]
        named = [word for word in wanted
                 if word not in A_MEASURE_WORD and word not in A_DOING_WORD]
        if named and not any(word in kept for word in named):
            # The ask named a thing of its own and no line holds it, so a measure is all that is
            # left to match on. A measure word says what kind of figure is wanted, never which
            # one: "how many days holiday do i get" after "we went to york for four days" asks
            # about the world, and four days is not its answer.
            return None
        if A_PAY_WORD.search(clean) and (A_PAY_JUDGEMENT.search(clean)
                                         or len(kept) < len(wanted)):
            # Pay is the one thing people ask about with a qualifier on it, and the qualifier is
            # the whole question: "how much do i get paid for overtime" and "whats my pay like"
            # and "how much do i pay for rent" name a figure this chat does not hold, and the
            # wage they gave is not the answer to any of them.
            return None
        if not A_THING_NAMED_AFTER_THE_CUE.search(clean):
            # Unless the words after the cue name a thing of their own: "the hall" is a thing
            # the ask is about, and a figure given for something else is not its answer.
            wanted = kept
    if _the_store_keeps_this_figure(clean, memory):
        # The store keeps the figure under the thing asked about, and its own recall of it is the
        # record the chat settled on. Answering from the scan here read the line before the
        # correction: "my budget is 500" / "change that to 650" / "what is my budget" answered
        # 500 while the store held 650, and the turn the store had answered properly was lost.
        return None
    if not wanted:
        # Names nothing at all, and asks a figure back - a length of time or an amount: one figure
        # of that kind in the chat is the one they mean, and two of them is a question of which.
        bare = (A_BARE_AMOUNT_ASK.search(clean) if kind == "amount"
                else A_BARE_DURATION_ASK.search(clean) if kind == "time" else None)
        if not bare:
            return None
        found = [(back, one[1]) for back, line in enumerate(lines)
                 if not A_LINE_THAT_ASKS.search(line)
                 for one in _figures_in(line) if one[0] == kind]
        distinct = {one.lower() for _back, one in found}
        if len(distinct) != 1:
            # They gave a length and then took it back: "my back has been bad for a week" /
            # "actually its been two weeks" / "how long have i had it now" was answered "Six
            # weeks." - the follow-up in the back answer - because two lengths in the chat read as
            # a question of which. A line that opens as a correction is the one they mean, and
            # only when it is the last length they said.
            corrected = [one for back, one in found if A_CORRECTION.search(lines[back])]
            if not corrected or found[-1][1] != corrected[-1]:
                return None
            figure = corrected[-1]
        else:
            figure = found[0][1]
        if not _the_figure_counts_the_thing(clean, figure):
            return _the_turn_that_names_it(text, memory)
        return pick(["You said " + figure + ".",
                     figure[:1].upper() + figure[1:] + " \u2014 that's what you told me."],
                    memory)
    best = None
    for back in range(len(lines) - 1, -1, -1):
        line = lines[back]
        if not line or A_LINE_THAT_ASKS.search(line):
            continue    # a question the person asked is not a line that gave a figure
        said = topics.keywords(line)
        if A_TAKE_HOME.search(line):
            said = said + ["takehome"]    # the same phrase, on the line being read now
        if A_IM_ON_A_FIGURE.search(line):
            said = said + ["pay"]    # "im on 2000 a month": a wage with no family word in it
        core = [word for word in wanted if word not in FIGURE_NOUNS] or wanted
        if not all(any(_the_same_word(word, other) for other in said) for word in core):
            continue    # the line does not say the thing the figure is for
        shared = [word for word in wanted
                  if any(_the_same_word(word, other) for other in said)]
        figures = _figures_in(line)
        found = _one_figure(figures, kind)
        if not found:
            continue    # no figure of the kind asked for on the line the thing was said on
        beside = _the_figure_beside_the_thing(figures, core)
        if beside:
            # The figure the line puts next to the thing the ask names outranks the first figure
            # on the line: two brothers and one sister is one sister when sisters is the ask.
            found = beside
        if COUNT_ASK.search(clean) and _a_list_of_ages(line):
            # A line that lists ages names the children one at a time, so its first number is not
            # how many there are. The store counts the list itself.
            continue
        if _money_paid_for_a_thing(clean, line):
            # The figure on this line is what the thing cost, not the thing the ask wants: see
            # _MONEY_PAID_FOR. The line is left to whoever answers about the thing itself.
            continue
        found = _the_corrected(lines, back, kind, found)
        if not found:
            continue
        many = _every_figure_the_ask_names(wanted, line, kind)
        last = (found[1].split() or [""])[-1]
        if _something_gone(lines, back, [word for word in said if word in shared] + [last]):
            continue    # the count they gave is not the count they have any more
        # More of the ask's own words on the line first, then the later line: a chat can hold two
        # figures of the same kind, and "how many days did i say i was off" after "we fly out for
        # 10 days" and "im off work for 5 days" asks about the one just said. The tie broke the
        # other way round - the earliest line won - and handed back the flight's 10 days.
        score = (len(shared), back)
        if best is None or score > best[0]:
            best = (score, found, shared, many)
    if best is None:
        return None
    _score, (kind_of, said, number, counted), shared, many = best
    if many:
        # Every figure the ask named, in the person's own words: "two brothers and one sister".
        return pick(["You said " + many + ".",
                     many[:1].upper() + many[1:] + " \u2014 that's what you told me."], memory)
    noun = _the_thing_counted(clean, said) if counted else ""
    if (counted and noun and noun.split()[-1].lower() in PERIOD_WORD
            and A_RATE_IN_THE_FIGURE.search(said)):
        # The thing they gave is a rate, and the ask names the period rather than the doing: the
        # count of weeks is not a fact, so the rate is said back in the doing's own words instead.
        return None
    if noun and number.lower() in ("1", "one") and noun.endswith("s") and not noun.endswith("ss"):
        noun = noun[:-1]   # "one kid", not "one kids"
    figure = (number + " " + noun).strip() if noun else said
    if _the_ask_gave_that_figure(number, clean):
        # A figure in the ask is the ask's own, not one they gave: "how many roast potatoes do i
        # need for 8" said back "8 potatoes - that's what you told me." about a line that said
        # eight *people*. The number the ask carries is what the ask is about, so it is not
        # evidence of anything they said, and the reading steps out of the way.
        return None
    if noun and _a_count_of_one_with_a_plural(number, noun):
        # "One people - that's what you told me." A count of one said back with a plural noun is
        # not a sentence anybody writes, and the reading cannot tell "one more is coming" from
        # one of the group: it steps out of the way and lets the store count the group itself.
        return None
    if not _the_figure_counts_the_thing(clean, figure):
        return _the_turn_that_names_it(text, memory)
    if _a_bare_count(figure):
        return pick(["You said " + figure + ".", figure + ", as you said."], memory)
    return pick(["You said " + figure + ".",
                 figure[:1].upper() + figure[1:] + " \u2014 that's what you told me."], memory)

A_FIGURE_WORD = re.compile(
    r"\d|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty"
    r"|thirty|forty|fifty|sixty|ninety|hundred|thousand)\b", re.I)


def _the_store_keeps_this_figure(clean, memory):
    """Whether the store keeps a figure under the thing this ask names.

    The figure reader is for the figures the store does not keep: it scans the lines the person
    said and works out which one the ask is about. A figure the store holds under a key is a
    different thing - the store's own recall says it, in its own words, and it is the record the
    chat settled on. "my budget is 500" then "change that to 650" leaves 650 under "budget", and
    the scan could only find the line that says the word, which is the one before the correction.
    So where the ask names a key the store holds a figure under, this reading steps out of the way
    and the store answers it.
    """
    if not isinstance(memory, dict):
        return False
    asked = set(topics.keywords(clean))
    if not asked:
        return False
    for entry in reversed(list(memory.get("facts_log") or [])):
        if not isinstance(entry, dict):
            continue
        value = " ".join(str(entry.get("value") or "").split())
        if not value or not A_FIGURE_WORD.search(value):
            continue
        key_words = topics.keywords(str(entry.get("key") or "").replace("_", " "))
        if not key_words:
            continue
        if not any(_the_same_word(word, other) for word in key_words for other in asked):
            continue
        said_on = str(entry.get("text") or "")
        if said_on and A_LINE_THAT_ASKS.search(said_on):
            continue    # a question is not a line that gave a figure
        return True
    return False


# The words that make a line a request for something said earlier rather than a question about the
# world: "how much was i putting away" asks back a figure of theirs, "how much should i save each
# month" asks me. `the_figure_they_gave` answers either shape, so this cue is what decides whether
# the store may take a turn the composer has already given a reply of its own to.
# The cue itself lives in bot/memory/recall.py (`looks_back`), one list for the whole bot, so a
# new wording of the same ask ("remind me how many nights") reaches this reader too. The name is
# kept for the importers that predate the move.
A_RECALL_CUE = recall.LOOKS_BACK


# A line that says out loud it is asking about the chat: "what did i say", "remind me how many
# nights", "what was my excess again". These carry their own proof, so they are read even when the
# thing named is not a word of the line they are answered from.
A_POINTS_BACK_HARD = re.compile(
    # "before" and "back to" are not here: they order things in time in an ask about the future
    # too ("how long before the move should i start"), and the line that says out loud that it is
    # about what was said is "again", "remind", "you said" and the rest of this list.
    r"\b(?:again|remind\w*|remember|recall|earlier|same\s+(?:again|one))\b"
    r"|\b(?:you|u)\s+(?:said|told)\b|\btold\s+me\b"
    r"|\bwhat(?:'s|s|\s+is|\s+are|\s+was|\s+were)?\s+(?:my|our)\b"
    r"|\bwhat\s+did\s+(?:i|we)\s+(?:say|tell)\b"
    # A first person with "be", "do" or "have" in the ask makes it about the person's own chat,
    # whatever the wording: "how many people am i catering for" asks about the 30 they just said,
    # where "how many people live in paris" has no first person and stays a question about the
    # world. A modal is advice and not a look-back: "how long before the move should i start" is
    # the packing, and their "6 weeks" is not the answer to it.
    r"|\b(?:am|are|did|do|does|was|were|have|has|had)\s+(?:i|we)\b", re.I)


def _the_figure_beside_the_thing(figures, words):
    """The figure the line says next to the thing the ask names, or None.

    A line can give a figure for each of two things - "i have two brothers and one sister" - and
    the first figure on the line is the wrong one to say back when the ask names the second:
    "how many sisters do i have" was answered "You said two sisters." A figure belongs to the
    words it is said with, so the phrase the store kept beside the number is where the thing the
    ask names is looked for.
    """
    for figure in figures:
        beside = topics.keywords(figure[1])
        if any(_the_same_word(word, other) for word in words for other in beside):
            return figure
    return None


def _every_figure_the_ask_names(wanted, line, kind):
    """Every figure the line gives for the things the ask names, said as one phrase, or "".

    "how many brothers and sisters do i have" names two kinds of thing, and the line that holds
    the answer - "i have two brothers and one sister" - gives a figure for each of them. Saying
    the first one back ("You said two brothers.") drops the sister, which is half the answer and
    wrong about the other half (deck row `how-many-02`). While the ask names more than one of
    them and the line gives a figure for each, they are all said back, joined the way the person
    joined them.
    """
    named = [word for word in wanted if word not in ASK_FRAME and word not in FIGURE_NOUNS]
    if len(named) < 2:
        return ""
    figures = [one for one in _figures_in(line) if not kind or one[0] == kind]
    if len(figures) < 2:
        return ""
    taken = []
    for word in named:
        for figure in figures:
            if figure in taken:
                continue
            if any(_the_same_word(word, other) for other in topics.keywords(figure[1])):
                taken.append(figure)
                break
    if len(taken) < 2:
        return ""
    parts = [figure[1] for figure in taken]
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def asked_back(text, memory):
    """The figure a recall ask wants back, or None when the line is not one.

    `the_figure_they_gave` is only reached where the composer has nothing, so a recall ask the
    composer thinks it has answered was lost: "how much was i putting away" was met with "I can't
    look up live prices, sorry" and "what was my excess again" with "That is everything I have on
    that one, so I would only repeat myself" - while the 400 and the 100 were in the person's own
    lines. The cue keeps a question about the world out: "how much should i save each month" is
    not asking me what they said, and their 200 is not the answer to it.
    """
    if not isinstance(text, str) or not isinstance(memory, dict):
        return None
    if not recall.looks_back(text):
        return None
    if not A_POINTS_BACK_HARD.search(text) and recall.the_earlier_turn(text, memory) is None:
        # The cue list is shared with every other reader now, so it holds the weak cues too: "how
        # many people live in london" and "how much coffee is too much" point back at nothing and
        # were answered "You said 30 people live." The line has to name something a line already
        # carries, unless it says out loud that it is asking about what they said.
        return None
    figure = the_figure_they_gave(text, memory)
    if figure:
        return figure
    # A count asked about the job rather than about the people ("how many am i cooking for again",
    # two turns after "a roast for 8 people on sunday") names nothing the chat said - "cooking" is
    # in no line they typed - so the figure reader above declines, and the ask went to a menu card
    # that shares the word "cook" with it. The count of the people is a figure they gave, and it is
    # read where every other count is read (`bot/memory/counts.py`), so an ask the store can answer
    # is a recall ask here too: one reading of what was said, whichever file holds it.
    try:
        from . import counts as _counts
        said = _counts.answer(text, memory)
    except Exception:  # noqa: BLE001 - a reader that fails is no ask
        return None
    return said or None


def carries_the_figure(figure, reply):
    """Whether a reply already says the figure the person asked back.

    A reply that names it answered the ask, whatever else it says; one that does not is the
    composer making conversation about a question it did not answer, and the figure is the answer.
    """
    said = str(reply or "")
    numbers = re.findall(r"\d[\d,]*", str(figure or ""))
    if numbers:
        for number in numbers:
            if not re.search(r"(?<![\d,.])" + re.escape(number) + r"(?!\d)", said):
                return False
        return True
    words = [word for word in topics.keywords(figure) if not word.isdigit()]
    low = said.lower()
    return bool(words) and all(word in low for word in words)


# The same question, in the same words, later in the chat. People do this all the time: they ask
# something, get an answer, talk about something else for a turn or two, and ask it again - and by
# then the pronouns in it point at whatever was said last, so the reading is of the wrong thing.
# "im sam, i want to run a half marathon in october" / "how many weeks is that away" (46 weeks,
# in October) / "i get a sore knee after about 3k" / "how long will that take to get better" /
# "how many weeks is that away" - and the last line, word for word the second, came back "I don't
# know enough to answer that honestly": the "that" was read as the knee, the store stood down, and
# the only candidate left was the fallback. Nothing in the chat contradicted the answer of 46
# weeks, so the honest reply is that answer again.
#
# Narrow on purpose: the line has to be the earlier line's own words (so a new question that
# merely shares a subject is read on its own), the earlier answer has to be a real answer rather
# than a hedge or a question, at least one turn has to have gone by (a line repeated straight
# away is "did you hear me", answered by `SAY_AGAIN_LEADS`), and nothing said since may have
# changed the thing the answer was about ("actually we've moved it to the 21st" ends it, because
# the old answer would then be a wrong fact rather than a helpful one).
#
# The wording it comes back in is `topics.said_again`'s ("Same as before: ..." and the two after
# it), not a lead-in of this module's own: see `_the_answer_again`.
#
# A line that changes the thing an answer was about. Any of these between the two asks ends the
# repeat: the earlier answer is then about a plan that is no longer the plan.
CHANGED_IT = re.compile(
    r"\b(?:actually|instead|changed|change of plan|moved it|moved to|now it'?s|now we'?re|"
    r"no longer|swapped|postponed|cancell?ed|put it back|make it|makes it|we'?ve moved)\b", re.I)


def _the_same_words(one, other):
    """Whether two lines are the same question in the same words."""
    def bare(line):
        return " ".join(re.sub(r"[^a-z0-9]+", " ", str(line or "").lower()).split())
    return bare(one) == bare(other) and len(bare(one).split()) >= 4


def _shortened(said):
    """The answer, kept whole up to a paragraph, so a repeat is not a wall of text again."""
    said = " ".join(str(said or "").split())
    if len(said) <= 320:
        return said
    kept = ""
    for part in _sentences(said):
        if kept and len(kept) + len(part) > 320:
            break
        kept = (kept + " " + part).strip()
    return kept or said


def _the_answer_again(said, memory):
    """The earlier answer, framed as the repeat it is, in the frames the chat already knows.

    The wording is not this module's to invent: `topics.said_again` says an answer again in the
    same words is what a machine does, frames it, and moves the lead-in on with each repeat - and
    every frame in the codebase is listed in `again.FRAMES`, so a lead-in written here would make
    the answer read as new words to every caller that asks whether the chat has said this already.
    So the repeat is handed to that, and when the answer is further back than it looks the first
    of the same three frames is used.
    """
    framed = topics.said_again(said, memory)
    if framed:
        return framed
    return topics.REPEAT[0].format(reply=_shortened(said))


def the_same_question_again(text, memory):
    """The answer this same question got earlier in the chat, or None.

    See the note above: only the line's own words, only an answer that was an answer, only with a
    turn in between, and never once the chat has changed the thing that answer was about.
    """
    if not isinstance(memory, dict):
        return None
    turns = memory.get("turns")
    if not isinstance(turns, list) or len(turns) < 3:
        return None
    clean = str(text or "").strip()
    if len(clean.split()) < 4:
        return None
    for back, turn in enumerate(reversed(turns[:-2])):
        if not isinstance(turn, dict):
            continue
        if not _the_same_words(clean, turn.get("user")):
            continue
        said = str(turn.get("bot") or "").strip()
        if not said or len(said) < 40:
            continue
        if HEDGE.search(said) or said.rstrip().endswith("?"):
            continue  # a hedge or a question is not an answer to hand back
        index = len(turns) - 2 - back
        between = [str((t or {}).get("user") or "") for t in turns[index + 1:-1]
                   if isinstance(t, dict)]
        if any(CHANGED_IT.search(line) for line in between):
            return None  # the answer of then is about a plan that has since changed
        return _the_answer_again(said, memory)
    return None
