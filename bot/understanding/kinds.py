"""What kind of line this is: the broad kind, the finer intent, and what it asks for.

`kind` keeps the four values other lanes already read (empty, greeting, thanks, question,
statement). `intent` and `asks` say more, and every richer answer is a new key, so a module
written against `kind` keeps working.

The classification is driven by small word sets, checked in order from the most specific
reading to the most general, so adding a word to one set improves every line that uses it.
"""
import re

from . import lexicon
from .normalize import (KIN, UP_TO_LEADS, background_clause, background_positions,
                        opens_without_subject, strip_leaders)

NEGATIONS = lexicon.NEGATIONS
# "can't you come earlier" and "isn't it lovely" deny nothing: the negation sits in front of the
# subject, so the clause still asks. After one of these it is a tag of the question.
PRONOUNS = frozenset("i you we they he she it there that this these those one".split())
# "no", "nobody", "nothing" are what the clause is about, not a denial of the verb, so
# "is nothing working today" still asks.
SUBJECT_NEGATIONS = frozenset("no nobody none nothing neither nor".split())

# "good day", "greetings" and "salutations" are hellos people write in full and the reading
# never saw: each was answered as a statement about something ("Ha, fair enough. I'm here if
# you want a hand with anything"). They are the same hello as "hi" and nothing else, so a line
# made of one of them and a friendly tail is the hello, and a line that goes on to say something
# stays what it says ("greetings, my boiler is leaking" is the boiler).
GREETINGS = ("hi", "hello", "hey", "hiya", "morning", "good morning", "good afternoon",
             "good evening", "evening", "yo", "howdy", "good day", "greetings",
             "salutations")
FAREWELLS = ("bye", "goodbye", "see you", "see ya", "later", "night", "good night",
             "talk later", "take care", "ttyl", "gtg", "cya", "best wishes", "best regards",
             "kind regards", "warm regards",
             # The short ways out people type, and the ones that say "you" in the middle - "see
             # you later" and "talk to you later" are the same goodbye as "later", and the reading
             # that looks for "you" took them for a question about the bot. "ciao" is left out on
             # purpose: it opens a chat as often as it ends one, so it stays with the greeting.
             "ttfn", "cheerio", "laters", "adios", "night night", "nighty night",
             "ta ta", "see you later", "see you soon", "talk to you later",
             "speak later", "speak to you later", "catch you later", "bye for now")
THANKS = ("thanks", "thank you", "thx", "cheers", "ty", "ta", "much appreciated",
          "appreciate", "appreciated", "appreciate it")

QUESTION_WORDS = frozenset("what why how when where who which whose".split())
# A thanks that carries an ask is shaped like one in two ways: a question word, or an ask frame
# of its own. The frame is what people write when they thank you and then ask for advice on
# something: "thanks, any tips for a cold", "thanks, tips for a stain", "thanks, looking for a
# recipe for two". "advice on" only counts when the advice has not been given yet, so "thanks for
# the advice on my back" stays the thank you it is.
THANKS_ASK_NOUNS = frozenset("advice tip tips idea ideas suggestion suggestions".split())
THANKS_ASK_PREPS = frozenset("for on about with".split())
THANKS_ASK_WORDS = frozenset("any need needs looking".split())
GIVEN_ADVICE = frozenset("the your my our his her its their this that no".split())
QUESTION_STARTS = {"what", "why", "how", "when", "where", "who", "which", "whose", "can",
                   "could", "should", "would", "is", "are", "do", "does", "did", "will",
                   "have", "has", "am", "was", "were", "may", "might", "shall"}
# A question that opens with one of these wants a yes or a no: "can i take ibuprofen".
YESNO_STARTS = QUESTION_STARTS - {"what", "why", "how", "when", "where", "who", "which",
                                  "whose"}


# `yh`, `yhh` and `ye` are how a lot of people type "yes", and without them in this list a bare
# "yh" read as an ordinary statement and got "I'm listening - say more if it helps." - the shrug,
# not the answer a yes gets. `ye` is the oldest spelling of "you" and only survives in set
# phrases ("ye olde"), which is a trade worth making: "ye i did" and "ye it was" are answers,
# and a line that needs `ye` as "you" ("ye know what i mean") still has its other words.
AFFIRM = frozenset("yes yeah yep yup yh yhh yhhh ye sure ok okay definitely absolutely correct "
                   "right probably "
                   "maybe perhaps likely "
                   "true exactly indeed agreed fine cool great nice good perfect sounds "
                   "works deal done sweet brilliant".split())
DENY = frozenset("no nope nah never not nothing none neither".split())
ACK = frozenset("ok okay cool nice great good fine sure right got understand understood "
                "thanks aha ah oh wow really hmm hm mmm alright k gotcha you me same maybe "
                "perhaps probably likely haha hehe lol fair true".split())
LAUGH = frozenset(lexicon.LAUGHTER)
# Words of politeness that do not change what a short reply means: "yes please" is a yes.
POLITE = frozenset("please pls plz ta mate".split())

# Asking for a recommendation, an opinion, or a decision.
RECOMMEND = frozenset("recommend suggest recommendation suggestion advice idea ideas "
                      "options option pick choose best better worth".split())
# "tip" is three different things: advice asked for ("any tips for a roast"), money left for
# someone ("a 10% tip"), and what a person does ("he tips well", "tip the delivery driver").
# Only the advice reading belongs in RECOMMEND, and it needs a frame around it:
#   plural "tips"/"hints"/"pointers"  - nearly always advice, unless a subject in front makes
#                                       it a verb;
#   singular "tip"/"hint"/"pointer"   - nearly always a thing, unless something asks for some
#                                       ("any tip on painting a door").
TIPS = re.compile(r"\b(tips|hints|pointers|tip|hint|pointer)\b")
TIPS_WANTED = re.compile(r"\b(?:any|some|a few|few|got|need|needs|wanted|looking for|share|"
                         r"send|give(?: me)?)\s+(?:\w+\s+){0,2}$")
# "tips for a roast", "tips on painting", "tips for the garden" say what the advice is about.
TIPS_ABOUT = re.compile(r"\s+(?:for|on|about|when|to)\s+\w")
# a subject in front makes "tips" a verb, and an amount in front makes a tip money
TIPS_SUBJECT = re.compile(r"\b(?:i|you|we|they|he|she|it|who|that|this|people|everyone|"
                          r"nobody|someone)\s*$")
TIPS_AMOUNT = re.compile(r"(?:\d|%|\b(?:a|the)\s+\w+\s*%)\s*$")
# Asking for help without a question word in front of it: "anything i can do about it", "any way
# of making it easier", "anything that helps", "is there any way to save it". The line is a
# request for steps, but nothing in it opens like a question, so it used to read as a statement
# with nothing asked and got the stock nod. What it asks for is the same thing "what can i do"
# asks for, so it says "steps" too. A negation in front of the ask turns it back into a
# statement about there being nothing to do ("there isnt anything i can do", "i dont see any way
# to fix it"), which is a fact to answer, not a request.
HELP_ASK = re.compile(
    r"\b(?:anything|something)\s+(?:else\s+)?(?:i|we|you)\s+(?:can|could|should|might|would)\s+"
    r"(?:do|try|use|take|add|change)\b"
    r"|\b(?:anything|something)\s+(?:else\s+)?(?:that|which)\s+(?:helps|would help|might help|"
    r"will help|works)\s*[?.!]*\s*$"
    r"|\bany\s+(?:way|ways)\s+(?:of|to|round)\b"
    r"|\bis there any\s+(?:way|ways|thing)\s+(?:of|to|i|we|you|else)\b")
# What follows the ask decides it: "anything i can do is never enough" and "any way to get there is
# fine" are statements about the ask, not asks. The tail is searched, not matched at its start:
# after "any way to" comes a verb phrase ("to get there is fine"), so a check anchored at the
# match would only ever see the verb and let every statement built on the shape through.
HELP_ASK_SUBJECT = re.compile(
    r"\b(?:is|was|are|were|seems|seemed|feels|felt|sounds|sounded|helps|helped|works|worked|"
    r"suits|suited|fits|fitted|does|did|its|thats|im|youre|"
    r"(?:would|will|might|must|could|can|may) be)\b")
# "any way to put it, it hurts": the line goes on after the ask to say what it really says, so the
# ask is part of the sentence and not the whole of it. norm_text keeps a clause break as " | ", so a
# clause with two words or more after the ask means the line has its own ending already.
HELP_ASK_TAIL_CLAUSE = re.compile(r"\|\s*\w+\s+\w+")
HELP_ASK_NOT = re.compile(
    r"\b(?:no|not|isnt|isn't|wasnt|wasn't|arent|aren't|cant|can't|couldnt|couldn't|dont|don't|"
    r"doesnt|doesn't|didnt|didn't|never|nothing|without|hardly)\b")
# A line that names something of its own is asking about that thing, not for a way in: "is there
# anything i can do about the mole on my back" wants the mole answered (or an honest "I don't
# know"), not "what have you tried so far", which nobody can answer about a mole. So the ask has
# to stand alone, with no possession ("my", "our") and no "the <thing>" in the line.
HELP_ASK_OWN_SUBJECT = re.compile(
    r"\b(?:my|our|his|her|their|your|the|a|an)\s+[a-z]")


def _asks_for_help(text):
    """True when the line asks for help in a shape that does not open like a question.

    "anything i can do about it", "any way of making it easier", "anything that helps". The ask
    has to be the line's own question, so a negation before it ("there isnt anything i can do")
    or a copula after it ("anything i can do is never enough") leaves the line a statement.
    """
    if HELP_ASK_OWN_SUBJECT.search(text):
        return False
    for match in HELP_ASK.finditer(text):
        if HELP_ASK_NOT.search(text[:match.start()]):
            continue
        tail = text[match.end():]
        if HELP_ASK_SUBJECT.search(tail) or HELP_ASK_TAIL_CLAUSE.search(tail):
            continue
        return True
    return False

# A judgement asked about the thing just said, with nothing named in its place: "is that bad",
# "is that normal", "should i worry", "will it get worse". The line is a yes/no question and its
# whole content is the judgement, so the answer is in what the bot itself last said - but only a
# module that reads the previous turn can give it. Read as an ordinary short line it was an
# acknowledgement ("is that bad" got "Sounds good.", which agrees the fault is fine), so the
# reading names it for whoever can answer it.
VERDICT_ASK = re.compile(
    r"(?:and |so |but |ok |okay |also |sorry |oh |hmm )*"
    r"(?:"
    r"(?:is|was|are|were|does|do|did) (?:that|this|it)(?: all)?"
    r"(?: (?:really|actually|very|too|that|so))?"
    r"(?: (?:bad|normal|serious|dangerous|ok|okay|fine|safe|common|"
    r"a|much of a) ?"
    r"(?:problem|worry|issue|big deal)?"
    r"| (?:going to|gonna) (?:get|be) worse"
    r"| (?:going to|gonna) (?:spread|get worse))"
    r"|(?:is|was) (?:that|this|it)(?: (?:going to|gonna))? (?:get worse|getting worse|spread|serious)"
    r"|(?:is|was) (?:he|she|they) right"
    r"|(?:are|were|is|was) (?:they|these|those) (?:safe|ok|okay|fine|normal|bad|a problem|a risk|any good)"
    r"|(?:should|do|ought) i (?:be )?(?:worried|worry|worrying|bother)"
    r"|does (?:that|this|it) matter"
    r"|will (?:that|this|it) (?:get|be) (?:worse|ok|okay|fine)"
    r")"
    r"(?: then| though| honestly)?")


# The words that make a line a question about something other than what the bot just said.
QUESTION_WORD = re.compile(r"\b(?:why|when|where|how|who|whom|whose|which|what)\b")


def _asks_a_verdict(text):
    """True when the line asks for a judgement of the thing just said.

    The verdict is usually the whole line ("is that bad"), and the cap below is what keeps a line
    with a subject of its own out. But the same question is asked after the thing it is about, and
    that line carries no reading at all by the whole-line form: "my resting heart rate is 90 is
    that bad", "i left the chicken out all night is it safe", "they said two weeks is that normal"
    (48 of the deck's 60,260 turns got no shape of their own this way, and 18 more got a wrong one).
    The tail is read by the same pattern, and the cap stays on the *verdict clause* rather than on
    the line, so a short statement in front of the verdict does not hide it.
    """
    flat = re.sub(r"[^a-z0-9 ]+", " ", (text or "").lower())
    flat = re.sub(r"\s+", " ", flat).strip()
    if not flat:
        return False
    words = flat.split()
    if len(words) > 30:
        return False          # a long line is a statement with its own subject, not this ask
    if VERDICT_ASK.fullmatch(flat) is not None:
        return True
    # The verdict at the end, from any word that leaves at most seven of them: the pattern itself
    # is what says a verdict is there, so a "did" or an "is" inside the statement matches nothing.
    # The words in front must be a statement, though: "when should i worry" and "and why does it
    # matter" end on a verdict pattern word for word, and both ask a different question - a when
    # and a why - so a question word before the verdict keeps that reading.
    for start in range(1, len(words) - 1):
        if len(words) - start > 7:
            continue
        if QUESTION_WORD.search(" ".join(words[:start])):
            return False
        if VERDICT_ASK.fullmatch(" ".join(words[start:])) is not None:
            return True
    return False


# A line that only rules something out is not a new subject, it is a limit on the last answer:
# "recommend a film" / "no horror" is still a film line, and "training the lead" / "no treats"
# is still the dog. Read as a fresh line, the word after "no" becomes the topic and the bot
# answers the thing the person just ruled out (a horror list, a spaghetti bolognese).
# The shapes below are the ones people type. Each keeps the thing it rules out, so the composer
# can take it out of the answer above instead of starting again.
LIMIT_SHAPES = (
    ("no", re.compile(r"\bno\s+(?:more\s+)?([a-z][a-z' -]*?)\s*$")),
    ("nothing", re.compile(r"\bnothing\s+([a-z][a-z' -]*?)\s*$")),
    # "not spicy" is not a limit on anything, it is what the person says the food is not; the
    # word that makes it a limit is the one that turns a degree down ("not too spicy").
    ("not", re.compile(r"\bnot\s+(?:too|very|that|so|any)\s+([a-z][a-z' -]*?)\s*$")),
    # "not the sad ones" is the same limit said with the group spelled out: the plural stand-in
    # at the end says it is one of a set already on the screen, so the article in front is not
    # the person starting a sentence about a thing ("not the best" stays a verdict).
    ("not_the", re.compile(r"\bnot\s+the\s+([a-z][a-z' -]*?)\s+ones?\s*$")),
    ("without", re.compile(r"\bwithout\s+(?:the\s+|any\s+)?([a-z][a-z' -]*?)\s*$")),
    ("skip", re.compile(r"\b(?:skip|hold|drop|minus|leave out)\s+(?:the\s+|any\s+)?"
                        r"([a-z][a-z' -]*?)\s*$")),
    ("dont", re.compile(r"\bi\s+(?:dont|do not|can't|cant|can not)\s+(?:eat|drink|like|want|"
                        r"have)\s+([a-z][a-z' -]*?)\s*$")),
    ("allergic", re.compile(r"\bi\s+(?:am|m)\s+allergic\s+to\s+([a-z][a-z' -]*?)\s*$")),
)
# The softeners a person puts round a limit, front and back ("ok, no garlic please").
LIMIT_SOFT_BEFORE = re.compile(
    r"^(?:ok|okay|so|and|but|well|right|then|also|honestly|hmm|oh|ah|actually|btw)\b[\s,]*")
LIMIT_SOFT_AFTER = re.compile(
    r"[\s,]*(?:please|pls|thanks|thank you|then|though|tbh|honestly|lol|for me|this time|"
    r"at all|i guess|i suppose|to be honest|as well|instead)\s*$")
# A limit names a thing, not a sentence: three words is the most a dish, a genre or a pet food
# takes ("no more horror films"), and a verb inside it means the person is describing something.
LIMIT_ROOM = 3
# Words that fill "no ___" and "not ___" without ruling anything out: "no idea", "not sure",
# "no way", "not bad". None of them is a thing to take out of an answer, and read as one they
# would turn a shrug into a limit on the last line.
LIMIT_REFUSAL = frozenset("""idea clue way sure bad good luck doubt joke point matter rush hurry
wonder worries worry problem bother chance need thanks ta worries offence offense kidding
question answer option options choice change pain help helps well right myself yourself self
left yet though either sorry wait enough much many more less quite finished still now bake
since until after before""".split())
# A thing starts with a word that introduces something else, or continues a sentence the person
# is still writing: "nothing with subtitles", "not since breakfast" and "no, not shellfish" are
# not a thing taken away, and read as one they would empty an answer of the wrong part.
# A date or a number is not a thing to take out of an answer: "no, june" and "no, 8 kilos" are
# the person correcting what they said, and read as limits they would empty the last answer of
# the month or the figure they have just put right.
LIMIT_A_FACT = frozenset("""january february march april may june july august september october
november december monday tuesday wednesday thursday friday saturday sunday today tomorrow
yesterday morning afternoon evening night week weekend month year
one two three four five six seven eight nine ten eleven twelve twenty thirty forty fifty
hundred thousand couple few half lot""".split())
LIMIT_NOT_A_START = frozenset("""with without about for from by like not probably maybe wait sorry
enough too very much many more less just only at all and or but so then also""".split())
# A thing is named by its last word: "no checked bag", "no boiled sweets" and "no baked beans"
# all end on the thing itself. A limit whose last word is a past tense is a sentence about what
# happened - "nothing got decided", "no one asked" - and read as a thing it takes a clause out of
# the answer above: "how did the meeting go" / "nothing got decided" was answered "Right - no got
# decided, then." A state people do limit ("not too tired", "no felt tip") is not a past tense, so
# this only turns away the sentences.
PAST_ENDS = re.compile(r"^(?:[a-z]{3,}(?:ed|ought|aught)|went|got|came|said|saw|made|took|gave|"
                       r"found|lost|left|ran|broke|fell|kept|met|paid|put|sent|sat|stood|"
                       r"thought|told|won|wrote|bought|brought|caught|chose|drove|flew|forgot|"
                       r"heard|held|hit|knew|ate|drank|slept|woke|bit|spoke|spent|built|burnt|"
                       r"burned|grew|threw|been|being)$")
# The word after "nothing" has to be the thing being ruled out, and people say "nothing works",
# "nothing helps", "nothing changes" - a whole clause with the thing left out, where the word
# after "nothing" is the verb. Read as a thing, it took "works" out of the answer above:
# "my laptop is broken" / "nothing works" was answered "Nothing there was about works, so the
# answer holds." A limit always names something, so a common verb is not one - the opposite of
# PAST_ENDS above, which turns away the sentences with a past tense in them. Only the third-person
# present is listed, because a rule about the "-s" ending would throw away "no sweets",
# "no crisps" and "no horror films", which are limits.
A_THING_NOT_A_CLAIM = frozenset("""works work helps help changes happens matters seems makes does goes
comes gets stops starts fixes fits runs moves shows feels looks sounds costs needs stays keeps turns
grows hurts adds counts means bothers lives takes gives brings appeals excites suits
satisfies interests improves settles lasts ends agrees sticks sorts arrives
# The irregular pasts, which no ending rule reaches: "nothing got sorted", "nothing came of it",
# "nothing went right", "nothing did". Each of those was answered with the answer described back
# at the person - "Nothing there was about got sorted, so the answer holds" - so the verb is
# listed in the tense it is said in as well as the one the list starts in.
got came went did was were""".split())
# The same words said in another tense: "nothing helped", "nothing has worked", "nothing is
# working". The reading looks at the last word of the limit, so the ending is stripped before the
# list is asked - the two forms that are a claim are the past tense and the "-ing", and neither is
# a thing anybody limits ("no sweets" strips to "sweet", which is not on the list).
CLAIM_ENDS = ((3, "ing"), (1, "s"), (2, "ed"), (1, "d"))
# The list is written in one tense and people say these words in every tense: "nothing works",
# "nothing worked", "nothing has worked", "nothing changed". The list's own "changes" and the
# line's "changed" are the same claim, but neither is the other word, so both sides are cut back
# to a stem before the list is asked. "moved" leaves "move" and meets "moves"; the -ed cut that
# leaves "mov" is why more than one stem is tried. A doubled consonant is undone for the same
# reason: "stopped" is "stop", which is what "stops" leaves.
CLAIM_STEMS = frozenset(form[:-1] if form.endswith("s") and len(form) > 3 else form
                        for form in A_THING_NOT_A_CLAIM)


def _claim_forms(word):
    """The stems a word could be, so "changed", "changes" and "change" all answer to one."""
    forms = {word}
    for cut, _suffix in CLAIM_ENDS:
        if len(word) > cut + 2:
            forms.add(word[:-cut])
    if word.endswith("ing"):
        forms.add(word[:-3] + "e")
    for form in list(forms):
        if len(form) > 3 and form[-1] == form[-2]:
            forms.add(form[:-1])
    return {form[:-1] if form.endswith("s") and len(form) > 3 else form for form in forms}


def names_a_claim(word):
    """True when the word after "nothing" is the verb of a clause with its object left out."""
    word = str(word or "").lower()
    if word in A_THING_NOT_A_CLAIM:
        return True
    return any(form in CLAIM_STEMS for form in _claim_forms(word))


LIMIT_NOT_A_THING = frozenset("""i me my we you he she they it them us her him his hers its our
ours your yours their theirs mine whom is are was were be been
am do does did have has had can could would should will just really very too so much any some
the a an of to for in on at and or but if that this these those there here what when where who
something anything everything nothing other else matter way bit lot lots one ones thing things
to""".split())


# A thing the line says it does NOT mean is not what the line is about. "i want to save money" /
# "for a holiday not a house" got the house-left-empty card, because "house" opens that entry and
# "holiday" closes it, and the person had said the opposite of the house. The words stay in the
# line, so it can still be said back whole; only the reader that answers it skips them, the way it
# already skips an intensifier ("what on earth is wrong with my boiler" is about the boiler).
# The article is what makes it a thing being ruled out rather than a verb being denied: "i could
# not sleep" rules out no sleep and is the insomnia card, "not a house" rules out a house.
RULED_OUT = re.compile(
    r"\b(?:not\s+(?:a|an|the)|rather than\s+(?:a|an|the)?|instead of\s+(?:a|an|the)?)"
    r"\s+([a-z][a-z'’-]*(?:\s+[a-z][a-z'’-]*){0,2})", re.I)

# Words that end the thing being ruled out: what follows them is the rest of the sentence.
RULED_OUT_ENDS = frozenset("""and but or so because if when then please though although actually
really either too now tonight today anyway for with in on at to of is are was were be been do does
did have has had can could would should will""".split())


# The words a line spends on asking rather than on naming a thing. A ruling-out needs a thing to
# be a ruling-out OF: "for a holiday not a house" contrasts a house with a holiday, while
# "recommend a film" / "not a series" has nothing in front of the cue but the ask, and there the
# ruling-out is the question (a film, not a series) rather than a correction.
RULED_OUT_NO_THING = frozenset("""what about recommend recommends suggest show give find is are was
were do does did can could would should will you u ur me my i we us the a an of to for in on at
and but or so if when then there here this that these those it its be been have has had any some
please thanks ok okays just also too more most than rather instead not no yes something anything
anything""".split())


_A_CLASS_OF_THING = []


def _a_class_of_thing():
    """The words of a class a refusal can be handed back inside ("not a thriller", "not tablets")."""
    if not _A_CLASS_OF_THING:
        from ..compose.ruledout import RULED_OUT_CLASS, RULED_OUT_INSTANCES
        words = set(RULED_OUT_CLASS)
        for members in RULED_OUT_INSTANCES.values():
            words |= set(members)
        _A_CLASS_OF_THING.append(frozenset(words))
    return _A_CLASS_OF_THING[0]


# A ruling-out is only a correction when the line says it is one: the person has already said
# something and is putting it right. "i want my money back not a repair" is a question about the
# two of them together - the refund-you-choose-instead-of-a-repair card is the answer - and read
# as "i want my money back" alone it lost that card. "actually i mean for a holiday not a house"
# is putting right the house the saving answer had taken.
RULED_OUT_CORRECTION = re.compile(
    r"\b(?:actually|i mean|sorry|make that|on second thoughts?|rather|instead|no,|nope)\b", re.I)


def _ruled_out_of(text):
    """The words of a thing the line says it does not mean, for the reader to skip.

    "for a holiday not a house" hands over ["house"]; "a laptop not a tablet" hands over
    ["tablet"]. A cue with no article in front of it is a verb being denied ("i could not
    sleep"), not a thing ruled out, so nothing comes of it, and a cue with nothing in front of it
    but the ask rules nothing out: "recommend a film" / "not a series" is a question about films,
    and its reader needs the word "series" to tell one from the other.
    """
    if not text:
        return []
    gone = []
    for match in RULED_OUT.finditer(text):
        said_before = text[:match.start()]
        before = [word.strip(" .,!?;:\'\u2019").lower() for word in said_before.split()][-3:]
        if not [word for word in before if word and word not in RULED_OUT_NO_THING]:
            continue
        # A class of thing the refusal composer can hand back is left to it: "i fancy a film but
        # not a scary one" is answered inside the answer they have (the same films, not the scary
        # ones), and read as a bare "i fancy a film" it loses the films they turned down and the
        # words they gave the turn after.
        if [word for word in match.group(1).split() if word.lower() in _a_class_of_thing()]:
            continue
        # "a cheap one not a gaming one" contrasts two of the same thing, and the "one" at the
        # end is what says so: the gaming laptop is not the thing asked about, the cheap one is.
        same_thing = match.group(1).split()[-1].lower() in ("one", "ones")
        if not same_thing and not RULED_OUT_CORRECTION.search(said_before):
            continue
        for word in match.group(1).split():
            word = word.strip(" .,!?;:'\u2019\u201c\u201d")
            if not word:
                break
            if word.lower() in RULED_OUT_ENDS:
                break
            gone.append(word)
            if len(gone) >= 4:
                break
    return gone


def _limit_of(text):
    """The thing the line rules out, or None when the line says more than that.

    The whole line has to be the limit, with only the softeners people put round one. "no
    horror" is a limit; "no horror but i liked the last one" is a line of its own, and "no
    thanks" rules out nothing at all.
    """
    if not text:
        return None
    ask = " ".join(text.replace("|", " ").split()).strip(" .,!?").lower()
    for _ in range(3):
        shorter = LIMIT_SOFT_BEFORE.sub("", ask)
        if shorter != ask:
            ask = shorter
        shorter = LIMIT_SOFT_AFTER.sub("", ask).strip(" .,!?")
        if shorter != ask:
            ask = shorter
        if ask == LIMIT_SOFT_BEFORE.sub("", LIMIT_SOFT_AFTER.sub("", ask)).strip(" .,!?"):
            break
    for _name, shape in LIMIT_SHAPES:
        match = shape.search(ask)
        if match is None:
            continue
        thing = " ".join(match.group(1).split()).strip(" .,!?")
        words = thing.split()
        if len(words) > 1 and words[-1] in ("one", "ones"):
            # "no sad ones", "not the long ones": the last word stands in for the thing rather
            # than naming it, and it is on LIMIT_NOT_A_THING, so read as the thing it refused
            # the whole limit: "recommend a film" / "no sad ones" was answered with the warm
            # list and the limit unheard. "no one" is a single word and stays refused.
            thing = " ".join(words[:-1])
            words = thing.split()
        if not words or len(words) > LIMIT_ROOM:
            continue
        if any(word in LIMIT_NOT_A_THING for word in words):
            continue
        if any(word in LIMIT_REFUSAL for word in words):
            continue
        if words[0] in LIMIT_NOT_A_START:
            continue
        if PAST_ENDS.match(words[-1]):
            continue
        if ask.startswith("nothing") and names_a_claim(words[-1]):
            # Only a line that opens with "nothing": "no work" and "no costs" are limits on an
            # answer about work, and their words are on the list.
            continue
        if any(word in LIMIT_A_FACT or word.isdigit() for word in words):
            continue
        # The limit has to be the whole line: what is in front of it may be a softener only.
        before = ask[:match.start()].strip(" .,!?")
        if before and not LIMIT_SOFT_BEFORE.sub("", before + " ") == "":
            continue
        return thing
    return None


RECOMMEND_PHRASES = ("any good", "something good", "anything good", "worth watching",
                     "worth reading", "what should i watch", "what should i read",
                     "any ideas", "what would you recommend", "what do you recommend",
                     "help me choose", "help me pick", "any suggestions")
OPINION = ("what do you think", "what about you", "your favourite", "your favorite",
           "do you like", "do you prefer", "would you rather", "in your opinion",
           "what would you", "how about you")
CHOICE = (" or ", "better than", "instead of", "vs", "versus")

# Two ends of one scale about one thing are not a choice of two options. "is easter early or late
# this year" asks where the date falls, and the word "or" alone was enough to hand it the
# light-choice answer ("toss a coin and see if you are disappointed"), which is a shrug at a
# question the calendar answers. Each pair is (word, its opposite) as people type them.
OPPOSITE_PAIRS = (
    ("early", "late"), ("earlier", "later"), ("sooner", "later"), ("soon", "late"),
    ("hot", "cold"), ("warm", "cold"), ("big", "small"), ("large", "small"),
    ("long", "short"), ("high", "low"), ("good", "bad"), ("better", "worse"),
    ("wet", "dry"), ("sunny", "rainy"), ("fast", "slow"), ("quick", "slow"),
    ("cheap", "expensive"), ("busy", "quiet"), ("loud", "quiet"), ("full", "empty"),
    ("deep", "shallow"), ("heavy", "light"), ("thick", "thin"), ("wide", "narrow"),
    ("hard", "soft"), ("early", "on time"),
    # A thing is in or out, not one of two things to pick: "is the tide in or out" was read as a
    # choice and answered "Out. I wouldn't spend another minute on it". The two words sit either
    # side of one "or" about one subject, which is what this table is for.
    ("in", "out"),
)


# The words a line asking how something is starts with. Two ends of one scale are a scale only
# when the line is asking about one thing: "is easter early or late this year" wants the range,
# while "long or short hair" and "shall i have a long or short break" are two things to pick
# between, and standing the choice down there left the line with no ask at all and a shrug.
SCALE_ASK = re.compile(r"^\s*(?:is|are|was|were|will|would|should|when|what|how|which|be)\b")


def two_ends_of_one_scale(text):
    """True when the "or" in the line joins opposites rather than two things to pick between."""
    if not (SCALE_ASK.match(text) or "sooner or later" in text):
        return False
    for one, other in OPPOSITE_PAIRS:
        for first, second in ((one, other), (other, one)):
            # The two words have to sit either side of the "or" with nothing naming a thing
            # between them: "early or late" is one scale, "the early train or the late one" is
            # a choice between two trains.
            if re.search(rf"\b(?:the |a |an )?{first}\s+or\s+(?:the |a |an )?{second}\b",
                         text):
                return True
    return False
# "or" joins a choice only when the person has not already turned both sides down. "i dont want a
# dog or a cat" was read as a choice ask, and the composer answered "Cat." - a pick between the two
# things the person had just said no to - and "not pizza or curry" was quoted back as an option
# ("If you were hoping I'd say \"not pizza\", then you've decided already"). The tell is in front of
# the "or": a want, a like or a can-have that is negated, or a line that opens with the refusal.
# A choice put as a doubt ("i cant decide, pizza or curry") is untouched: the negation there is on
# deciding, not on either thing.
REFUSED_PAIR = re.compile(
    r"^\s*(?:no|not|never|without|neither)\b"
    r"|\b(?:dont|don'?t|do not|doesnt|doesn'?t|didnt|didn'?t|wont|won'?t|wouldnt|wouldn'?t|"
    r"cant|can'?t|cannot|shouldnt|shouldn'?t)\s+(?:\w+\s+){0,2}?"
    r"(?:want|wants|wanted|like|likes|love|eat|eating|have|having|drink|drinking|wear|do|doing|"
    r"need|needs|use|fancy|stand|bother|manage)\b"
    r"|\ballergic\b|\bhate\b")


def _turns_the_pair_down(text):
    """True when the thing before the "or" turns both sides down rather than asking which."""
    head = str(text or "").lower().split(" or ")[0]
    return bool(REFUSED_PAIR.search(head))


COMPARE = ("difference between", "different from", "compare", "which one", "or is it")

REQUEST = frozenset("help need want trying wanna please tell show explain give write make "
                    "how".split())
STEPS = ("how do i", "how can i", "how should i", "what should i", "step by step",
         "walk me through", "get started", "how to")
# "steps" on its own is an ask for the steps, but as a substring it is also the start of every
# step-relation: "my stepson is 21" was read as somebody asking to be walked through something,
# so a plain telling about the son came back as the search hedge. The word is matched whole.
STEPS_WORD = re.compile(r"\bsteps\b")
WRITE = ("write", "word", "phrase", "say", "message", "text to", "email to", "letter",
         "poem", "speech", "bio", "caption", "wish")
# The words for a low day that are also ordinary words for a thing, a place or a measurement:
# "an empty shelf", "the flat is cold", "a blank page", "my fingers went numb", "the kitchen is
# a mess", "moved into a new flat". They are how somebody feels only when the speaker is the
# subject - "im empty", "i feel flat", "im in a bad mood" - so these cues are read with
# `_speaker_before` as well. Words that are only ever a feeling ("miserable", "gutted") are not
# here and need no check.
# A comparison is only the speaker's state when the speaker is the one it is said of: "i feel
# worse" and "im no better" are how they are, while "the traffic is worse today", "its getting
# worse" about a leak and "it could be worse" name the state of something else. Kept apart from
# SELF_ONLY_CUES so the sad list, which is built from that tuple, does not pick "worse" up: a
# state that got worse is the body's news, and the answer for it is rest, not a walk.
A_COMPARISON = frozenset(("worse",))
SELF_ONLY_CUES = (
    "empty", "flat", "hollow", "blank", "numb",
    "rubbish", "crap", "rotten", "rough", "lousy",
    "like a failure", "like a mess", "like rubbish", "like crap", "like a burden",
    "like a fraud", "a mess",
    "in a bad mood", "in a low mood", "in a foul mood", "in a mood", "in a state",
    "in a right state", "out of sorts", "off colour", "off form",
)
# The same shape said in several words, and the phrases sit here rather than in the sad list
# because each names its own feeling: a carpet is worn thin, a credit card is at its limit, a
# branch is at breaking point. "the carpet is worn thin" and "the card is at my limit" are the
# carpet and the card; "im worn thin", "im at my wits end", "im beside myself" and "im at the
# end of my patience" are somebody's day. "im at the end of my rope" is the hopelessness list's,
# so it is left out on purpose - that one is a crisis cue, not a mood.
# The words for being lost in something are also the words for a form, a recipe and a plan being
# hard to follow: "the instructions are confusing", "there was confusion about the dates". They
# are the confused key's, and they are the speaker's own only when the speaker is the subject -
# so the check is here rather than in SELF_ONLY_CUES, which is the sad list's.
CONFUSED_SELF_ONLY = frozenset(("confused", "confusing", "confusion", "muddled", "baffled",
                                "bewildered", "puzzled"))
# A word that names what a person does to other people is a label on them, not a mood of theirs:
# "im boring" and "my mum says im boring" are somebody's verdict, and read as the person's own
# boredom the line got "Try something with your hands: a new recipe, a jigsaw, or one drawer
# tidied" - an answer to a complaint nobody made. The same word names a mood when a thing is its
# subject ("the film was boring", "work was exhausting"), which is the reading that stays.
LABEL_ON_A_PERSON = frozenset((
    "boring", "annoying", "tiring", "exhausting", "draining", "knackering", "frustrating",
    "depressing", "embarrassing",
))
THING_OR_PERSON_CUES = frozenset((
    "worn thin", "worn to a thread", "at my limit", "at breaking point",
    "at my wits end", "at my wits' end", "beside myself", "at the end of my patience",
    "reaching the end of my rope",
    # A worry is said of things as well as people - "the news is worrying", "the cough is
    # worrying me", "my mum is worrying about money" - and "worn down" is said of stairs. Read
    # as the speaker's state wherever the word appears, all of those would claim the person in
    # the line is the one who is anxious, so they are read only where the line says the state
    # is the speaker's own: "im worrying", "im stressing about money", "im worn down by the kids".
    "worrying", "stressing", "stressed out", "overthinking", "obsessing", "spiralling",
    "spiraling", "worn down",
))
# One of those phrases is also the money row's. `bot/knowledge/money.py` keys the `cant-pay`
# answer on "at my limit", and puts the period words in that row on purpose: "i'm at my limit
# every month" says the money is the month, not that somebody has had enough. A period in the
# line is what says which, so the phrase is no mood when one is there - the card or the budget
# keeps the answer it had. "im at my limit with the kids" and "im at my limit" have no period
# and stay a feeling.
# A day, a week or a month the speaker had, told with a state word in front of it: "i had a low
# day", "ive had a low few weeks", "today was a low day". The state word stands in front of the
# period and not in front of the speaker, so the speaker check below never sees a person as its
# subject and the line read as news about a thing - "Thanks for telling me" for a low day. The
# period is what makes the state the person's: a thing's own reading stays a thing ("the battery
# was low all day"), and a day that was busy is still busy ("i had a mad day").
OWN_PERIOD_NOUNS = frozenset("""day days week weeks month months year years weekend weekends
night nights morning mornings afternoon afternoons evening evenings shift shifts term""".split())
# What may stand between the state word and the period it is said of: "a low few weeks", "a low
# old week", "a low sort of day".
OWN_PERIOD_FILLER = frozenset("""a an the one few couple of real proper whole entire bit those
these sort kind old long bad""".split())
# The heads that make a period the speaker's own: the person, the day, or the part of it they
# are in. Anything else - "the battery was low all day", "his week was low" - is not their state.
OWN_PERIOD_HEADS = frozenset("""i we i've ive me today yesterday tonight""".split())
OWN_PERIOD_STOPS = frozenset("""and but because so though while if when than then that which
who whose after before since until""".split())
# A state word whose sense in front of a period is the period's own kind, not the person's: "a mad
# day" is a busy one and "a flat week" a dull one. (A separate fix reads `mad` as a thing's state
# everywhere; this list is what keeps the fallback below from inventing an anger for a busy day.)
NOT_THE_SPEAKERS_DAY = frozenset(("mad", "flat", "dead", "mental", "wild", "slow", "heavy"))
# How far back the head of the clause may be: "i had a really bad low week" names the speaker
# three words before the state, and a longer run than that is another clause.
OWN_PERIOD_REACH = 6

PERIOD_CUES = frozenset(("at my limit",))
A_PERIOD = re.compile(
    r"\b(?:every|each|this|next|last|a|per)\s+"
    r"(?:(?:single|whole|full|other|coming|past|few|one|more)\s+)*"
    r"(?:month|week|fortnight|pay ?day|paycheck|wage)\b"
    r"|\bmonthly\b|\bweekly\b|\bfortnightly\b|\bpay ?day\b")
# A period says the line is about money only when the money is named: a month is a billing cycle
# ("every single month", "with the electric every month"), a money word is what the limit is
# going on (the rent, the bill, the overdraft). A week with nothing else named is how long a
# person can keep going, so "im at my limit every single week" is somebody's week and not a
# card, and so is "im at my limit any week now", which is a point in time rather than a run of
# them ("any" is deliberately not a period word).
# A month is a billing cycle and so is a payday, but a paycheck is a word the money row does
# not yet answer: it carries "pay" and "pay cheque", and a line typed as one word would read as
# money with no card to answer it ("I'm listening"). The word is left as a period and not as a
# month, so "im at my limit every paycheck" stays the person's week, the way it does on main,
# until the row learns the joined spelling.
A_MONTH_PERIOD = re.compile(r"\b(?:month|monthly)\b|\bpay ?day\b")
A_MONEY_SUBJECT = re.compile(
    r"\b(?:rent|mortgage|bills?|electric(?:ity)?|gas|water|council tax|overdraft"
    r"|credit card|loan|debt|debts|childcare|nursery fees|fees|fuel|heating)\b")
# The limit is about a person or a day's work, not about money: "with the kids" and "at work"
# are somebody's week however long it runs.
A_LIMIT_ABOUT_PEOPLE = re.compile(
    r"\b(?:with (?:the|my|our|their|his|her|these|those)\s+"
    r"(?:kids?|children|child|family|mum|mom|dad|parents|partner|husband|wife|boss|team)"
    r"|at work|at school|at college)\b")
# A limit with nothing but a period after it, which the card has always answered, keeps its
# answer even when a month is not named: "im at my limit every single week" stays the person's
# week, so the card needs the month or the money and nothing that says the limit is about
# people.


# "im beside myself laughing", "im beside myself with laughter": the phrase says what the
# laughing is like, not how the person is, so a cue with laughter after it is no mood at all.
LAUGHED_OFF_AFTER = re.compile(
    r"(?:with\s+|in\s+)?(?:laughter|laughing|laughs|cracking up|stitches)\b")


def _laughed_off(text, cue):
    """True when the phrase is followed by laughter: "im beside myself laughing"."""
    for match in re.finditer(r"\b" + re.escape(cue) + r"\b", text):
        if LAUGHED_OFF_AFTER.match(text[match.end():].strip()):
            return True
    return False
# The rest say "myself" or a whole clause, so they cannot be said of a thing and need no
# speaker check: "im not myself", "i dont feel like myself", "i feel nothing". The words are
# the normalised ones, because "dont" is read as "do not" before this runs.
SAD_PLAIN_CUES = (
    "dead inside", "feel nothing", "like nothing matters", "not myself", "not feeling myself",
    "not been myself", "do not feel myself", "do not feel like myself", "have not felt myself",
    "have not been myself",
)
# The words above that also describe a thing, a day or a job: "work has been awful lately", "my
# energy is low", "the windscreen is shattered", "ive spent the rent". They are somebody's state
# only when the speaker is the subject, so they carry the same check as SELF_ONLY_CUES without
# being added to the sad list.
# A mood that is also a doing or a thing: "the past tense was wrong", "the match wiped out",
# "he whacked the nail in", "the glass shattered", "i was zonked by the heat of the day".
# A fire, a sea, a pan and a bulb can rage, seethe, fume and be incandescent; only a person is
# furious about it, so the word before one of those has to be a person: "im seething" counts,
# "the sea was seething" does not.
SELF_ONLY_STATE = frozenset(
    "low awful hopeless worthless shattered wiped wasted spent "
    "tense pooped whacked zonked "
    # "im blue" is the mood; the sky, a door and a pair of jeans are the colour.
    "blue "
    "raging fuming seething incandescent".split())
# The same kind of word that a body can be as well: "my stomach is upset" is a stomach.
BODY_STATE_CUES = frozenset(("upset", "low", "awful", "rough", "rotten"))

# "flat out" is a full week and "flat broke" is no money: the idiom, not the state.
# "flat out" is a full week and "flat broke" is no money; "in a mood for pizza" is an appetite.
# Each is the idiom, not the state.
# "cheap and cheerful" is a kind of place or option, not a person's mood: "cheap and cheerful is
# fine" answered the happy pool ("That's a good feeling to carry into the rest of the day") to a
# line agreeing to a cheaper trip.
IDIOM_STATES = re.compile(r"\bflat\s+(?:out|broke)\b|\bflat as (?:a|an) \w+|"
                          r"\bcheap\s+and\s+cheerful\b|"
                          r"\bin (?:a|the) mood for\b|"
                          r"\b(?:bit of a|a bit of a|a right|a proper)\s+"
                          # "what a mad one" is left out on purpose: with nothing after it, it
                          # is the day they had, and the shell keeps that reading
                          r"(?:mad|weird|strange|funny|odd|daft|curious)\s+one\b")


# A heart breaks in a shape no single feeling word is in: "my heart is broken and i dont know
# what to do" named no feeling at all, so it was filed as news and answered "Got it. Is there
# anything you'd like a hand with?" while "im heartbroken" got the sorry-and-a-walk reply. The
# heart is the thing that is broken, in pieces, shattered, torn, aching or heavy, and the words
# between "heart" and the state are the ones people put there ("still", "completely", "so").
# A heart that is racing, pounding or fluttering is a body rather than a feeling and stays one:
# none of these shapes is how a pulse is described. "heartbreaking" is left out on purpose - it
# is said of a film or a story, which is a thing, and not of how the person is.
HEART_DEGREES = (r"(?:still|really|so|very|totally|completely|utterly|absolutely|just|all|"
                  r"now|quite|too|already|a bit|kind of|sort of)")
HEART_IN_A_STATE = re.compile(
    r"\bheart(?:s|'s)?\b"
    r"(?:\s+(?:is|was|feels|felt|seems|has|had|been))*"
    r"(?:\s+" + HEART_DEGREES + r")*"
    r"\s+(?:broken|shattered|torn|in pieces|aching|aches|breaks|heavy|breaking)\b")
# The broken heart said as an adjective, which is how most people type it: "broken hearted",
# "heart-broken", and the one word "heartbroken" that puts the same two words the other way
# round. "heartbreaking" is left out: it is said of a film or a story, not of a person.
BROKEN_HEARTED = re.compile(r"\b(?:broken[\s-]?hearted|heart[\s-]?broken)\b")
# The broken heart said as a thing rather than a state: "i have a broken heart", "i dont know
# what to do with a broken heart".
A_BROKEN_HEART = re.compile(r"\b(?:a|an|my|our|her|his|their|your)\s+broken\s+heart\b")
BROKE_A_HEART = re.compile(r"\b(?:broke|breaks|breaking|break)\s+(?:my|our|her|his|their|your)\s+heart\b")

EMOTION_WORDS = {
    "sad": ("sad", "unhappy", "miserable", "gutted", "heartbroken", "cry", "crying", "tears",
            "disappointed", "devastated", "weepy", "tearful", "homesick", "rotten", "lousy",
            "meh", "rough", "crap", "rubbish", "fed up", "numb", "blue",
            # The phrases for having had enough: "im at my wits end", "im at my limit", "im at
            # the end of my patience". They were answered "I'm listening" or "Thanks for telling
            # me". They are worn down, the way "im so fed up" is, and not the worry of "im
            # beside myself" - that one is the anxious list's.
            "at my wits end", "at my wits' end", "at my limit", "at breaking point",
            "at the end of my patience", "reaching the end of my rope",
            # The everyday words for a low day that were read as a name or a shrug: "im glum",
            # "im mopey", "im despondent", "im a bit blah".
            "glum", "mopey", "teary", "downhearted", "despondent", "blah", "bleh",
            # The plain words people use for a low day that this list was missing: "im low",
            # "im upset", "i feel awful", "i feel hopeless", "im still grieving".
            "low", "upset", "awful", "hopeless", "worthless", "grieving", "mourning",
            "despair", "despairing", "in a dark place", "emotional") \
        + SELF_ONLY_CUES + SAD_PLAIN_CUES,
    "lonely": ("lonely", "alone", "isolated", "left out"),
    "angry": ("angry", "annoyed", "furious", "cross", "irritated", "frustrated", "mad",
              "grumpy", "cheesed off",
              # "im mardy with everyone", "im snappy today", "im a bit ratty", and "im mardy"
              # is the northern word for grumpy - without these the line read as an
              # introduction and answered "Nice to meet you, Mardy".
              "cranky", "snappy", "tetchy", "ratty", "mardy",
              # The words people reach for when they are past annoyed: "im livid", "im
              # seething", "im fuming", "im raging". The lexicon already held "livid" and
              # "raging" as feelings but the reading did not, so "im seething" was answered
              # "Thanks for telling me" - the bot heard no feeling at all.
              "livid", "seething", "fuming", "raging", "seeing red", "incandescent",
              # The plain idioms for a bad temper, none of which said anything before: "im
              # brassed off", "im narked", "im miffed", "im in a strop". "hacked off" is left
              # out on purpose: hacking the dead wood off a hedge is the same two words.
              "brassed off", "narked", "miffed", "in a strop"),
    "anxious": ("anxious", "worried", "nervous", "scared", "afraid", "stressed", "stress",
                "panic", "panicking", "overwhelmed", "dreading", "bricking it",
                # "bricking" on its own is left out on purpose: it is a single word, and a
                # single word in this table has to be a feeling the lexicon holds, or a line
                # about bricking up a doorway is read as nerves. The phrases carry the idiom.
                "bricking myself", "shitting myself", "crapping myself",
                "shitting it", "crapping it", "cacking myself", "cacking it",
                "shitting bricks", "butterflies",
                "on edge", "nervous wreck", "worried sick", "freaking out", "petrified", "anxiety",
                "terrified", "panicky", "in bits", "restless",
                # "im all jittery about the scan", "im antsy", "im edgy", "im tense".
                # "im aprehensive about the results" is the same feeling one letter out.
                "jittery", "antsy", "edgy", "tense", "apprehensive",
                # "im beside myself" is the one of these that is worry, and it was read as a
                # name and answered "Nice to meet you, Beside" before this. "at the end of my
                # rope" is left out of both lists on purpose: that one is the hopelessness
                # list's, and it is a crisis cue rather than a mood.
                "beside myself",
                # The doing form of a worry, which is how most people say it: "im worrying",
                # "im stressing about money", "im overthinking a text". The list held the
                # adjective and the noun - "worried", "stress", "panic" - so these named no
                # feeling at all and were answered "I'm listening - say more if it helps" or
                # "Thanks for telling me", the two lines STYLE.md calls the worst answers there
                # are. "panicking" was already here, so the frame reads the -ing form of a
                # feeling; it was only the words that were missing. "stressed out" was in the
                # lexicon as a feeling and not in this list, so the longer way of saying
                # "stressed" was the one that said nothing.
                "worrying", "stressing", "stressed out", "overthinking", "obsessing",
                "spiralling", "spiraling"),
    "tired": ("tired", "exhausted", "knackered", "worn out", "drained", "no energy",
              "burned out", "burnt out", "shattered", "wiped out", "wiped",
              # "im zonked after the night shift", "im pooped", "im whacked", and "im
              # frazzled", which said no state at all and got a listening noise.
              "zonked", "pooped", "whacked", "frazzled",
              # Worn down rather than out of steam all at once: "im worn thin", "im worn to a
              # thread".
              # "im worn down" is the plainest way of saying it and it named no feeling, so a
              # person worn down by a month of nights got "I'm listening".
              "worn thin", "worn to a thread", "worn down",
              # "my brain is fried", "im fried": nothing left to think with.
              "fried",
              # The same thing said as what the tiredness stops them doing, or as a tank:
              # "i cant even think straight", "im running on empty", "im running on fumes",
              # "my head is mush", "i can barely keep my eyes open".
              "think straight", "running on empty", "running on fumes", "head is mush",
              "heads mush", "keep my eyes open",
              # "im dead after today", "im dead on my feet", "im dead": the way people say
              # they have nothing left. The word is also the bereavement word, so it is in
              # `ALWAYS_SELF_ONLY` below - it only counts in the "im" frame, and "my dad is
              # dead" and "my phone is dead" are not this at all.
              "dead"),
    "happy": ("happy", "glad", "delighted", "thrilled", "pleased", "excited", "proud",
              "relieved", "chuffed", "awesome", "hopeful", "cheerful"),
    "grateful": ("grateful", "thankful", "appreciate"),
    "bored": ("bored", "boring", "nothing to do"),
    # Not knowing which way is up is a feeling of its own, and the reading had no key for it:
    # "im confused", "i feel muddled" and "i dont understand" named nothing, so they were
    # answered "Thanks for telling me — I'm here if you want to dig into any of that", the line
    # the bot gives a message it has heard nothing in. It is not "stuck" (nothing is in the way)
    # and not "scattered" (the mind is holding still and going over one thing): what a confused
    # person needs is a question that makes the missing bit easy to say. "confusing", "confusion"
    # and "muddled" are also said of a form, a set of instructions and a plan, so they sit in
    # CONFUSED_SELF_ONLY as well and are the speaker's only when the speaker is the subject.
    # "i cant get my head round this" is the same state said with a picture instead of a word,
    # and it read as nothing at all: the line got "I'm listening - say more if it helps", which
    # is what the bot says when it has heard nothing in a message. The person is not tired and
    # not stuck for a fact: they cannot follow this, and the confused pool asks which part is
    # foggy, which is the question that gets them talking.
    "confused": ("confused", "confusing", "confusion", "bewildered", "baffled", "muddled",
                 "puzzled", "dont understand", "do not understand", "dont get it",
                 "do not get it", "does not make sense", "makes no sense",
                 # The picture carries its own no: "i cant get my head round this" is not the
                 # state denied, it is the state said. The negated forms are listed whole for
                 # that reason - a cue without the "cant" in it would also fire on "i get my
                 # head round it", which is a person saying they do follow it.
                 "cant get my head round", "cant get my head around", "cant get my head straight",
                 "cannot get my head round", "cannot get my head around",
                 # normalise expands "cant" to "can not" for the words list, and the reading is
                 # made on that text, so the spaced form is the one it meets most often.
                 "can not get my head round", "can not get my head around",
                 "cannot get my head straight", "can not get my head straight",
                 "cant make head nor tail", "cannot make head nor tail",
                 "can not make head nor tail",
                 # "or" is what half the people who write it type.
                 "cant make head or tail", "cannot make head or tail",
                 "can not make head or tail",
                 "struggling to understand", "struggling to follow"),
    # The morning after, and the other ways a person says they are not well today. These are
    # states, not moods, and none of them is a name: "im hungover" was read as an introduction
    # and answered "Nice to meet you, Hungover". They are their own key so that a line which
    # asks what to do ("im hungover what should i do") still reaches the hangover entry instead
    # of a mood pool, and so that a plain "im hungover" gets the water-and-rest answer.
    "unwell": ("hungover", "hung over", "hangover", "under the weather", "run down",
               # "im feeling worse", "i feel worse today", "im no better": how a person says a
               # state has got worse, which is the commonest way a bad day is told in a second
               # turn. None of it named a state - "worse" is a comparison and "better" is the
               # good one - so "i feel worse" was answered "Thanks for telling me".
               "worse",
               "run-down", "jet lagged", "jet-lagged",
               # "cream crackered" is rhyming slang for knackered, and "crackered" is what
               # people write when they shorten it: without them the line named no state at all
               # and got the stock "Thanks for telling me".
               "cream crackered", "crackered"),
    # A condition somebody has is not a name, and it is not a mood either: "im bipolar" was
    # answered "Nice to meet you, Bipolar", and the store kept the name for the rest of the chat.
    # Its own key so that a line which asks something ("im bipolar and my meds have changed")
    # keeps its own reading, and so the memory store - which builds its "not a name" list from
    # every value here - stops filing the word as a person.
    "condition": ("bipolar", "schizophrenic", "anorexic", "bulimic", "narcoleptic", "psychotic",
                  "infertile", "sterile", "paranoid", "transgender", "nonbinary", "hiv"),
}
# Words that are only a state of the speaker's, whatever else they mean. They are not in
# `SELF_ONLY_CUES`, because that set is appended to the sad list's own words, and a word here
# belongs to one feeling: "dead" is tired ("im dead after today"), not sad, and "my dad is dead"
# is a bereavement that this file must not read as a mood at all.
ALWAYS_SELF_ONLY = frozenset((
    "dead", "fried", "running on empty", "running on fumes"))
# Feelings that are said as a "not", where the not is the feeling and not a denial of it: "i cant
# think straight" is being exhausted, and `denied` reads the "cant" as the line saying it is not
# so; "i can barely keep my eyes open" is the same with "barely". The opposite way round as well:
# the cue with no not in front of it is not the feeling, so "i can think straight now" and "i can
# keep my eyes open" stay nothing at all.
SAID_AS_A_NEGATION = frozenset(("think straight", "keep my eyes open"))
# A feeling word that is also half of an idiom, with the idiom spelled out: the word is not
# the feeling there. "im dead set on going" is a plan and "im dead right" is being sure, and
# neither is being tired. A cue only needs an entry here when the words after it would
# otherwise read as somebody's state ("dead on my feet" is tired, "dead set on" is not).
NOT_A_MOOD_THERE = {
    "dead": re.compile(r"\bdead\s+(?:set|right|against|certain|last|heat|giveaway|cert|"
                       r"keen|to me|to the world)\b"
                       # "im so dead" is being in trouble, usually with a time attached ("im so
                       # dead tomorrow"), not being out of energy - "im dead" and "im dead after
                       # today" already say that.
                       r"|\bso dead\b"),
    "fried": re.compile(r"\bfried\s+(?:rice|chicken|egg|eggs|bread|onion|potatoes|tomatoes|"
                        r"fish)\b"),
    # "think straight" says how the tiredness is, unless the words give it a subject: "he cant
    # think straight" and "my boss cant think straight" are somebody else's morning, and
    # `_state_owner` would have to say whose it is for a reply to use it.
    "think straight": re.compile(r"\b(?:he|she|they|my|his|her|their|its)\b[^.|]{0,20}"
                                 r"\bthink straight\b"),
}
# The names above whose words are the good ones. Denying a good word is a complaint about it
# rather than a denial of the state ("i am not happy about it", "im not pleased"), so the name
# stays and `polarity` carries the minus.
GOOD_EMOTION_NAMES = frozenset(("happy", "grateful"))
NEGATIVE = frozenset("""sad unhappy miserable gutted heartbroken cry crying tears disappointed
devastated lonely alone angry annoyed furious frustrated mad anxious worried nervous scared
afraid stressed panic overwhelmed dreading tired exhausted knackered drained sick ill hurt
pain ache sore worse worst hate awful terrible horrible bad fail failed failing lost lose
hate rubbish useless stupid annoyed upset""".split())
POSITIVE = frozenset("""happy glad delighted thrilled pleased excited proud relieved grateful
thankful love loved lovely great good nice brilliant wonderful perfect amazing fantastic
fun funny enjoy enjoyed success succeeded won win calm relaxed fine okay""".split())
# The words a line is said *to* rather than about: "thanks love", "morning pet", "cheers duck".
# They are feeling words too, so a short line that finishes with one was read as carrying a
# feeling: "thanks love" came back with a shrug where "thanks mate" is answered "No problem at
# all.", because the thank you stopped looking like one. The word is the person being spoken
# to, so it is not a feeling, and only the last word of a line people say to somebody counts.
TERMS_OF_ADDRESS = frozenset("""love mate pet hun honey sweetheart duck ducky flower sunshine
    pal bud chick dear darling babe lass lad bella""".split())
ADDRESSED_LINES = frozenset("""thanks thank cheers ta hello hi hiya hey morning afternoon
    evening night bye goodbye yes no ok okay alright right please sorry""".split())
# "ok" is a feeling only when it is said about somebody's state ("im ok", "i am doing ok"). On
# its own it is an acknowledgement ("ok so", "ok bye") or a permission question ("is it ok to
# leave an 11 year old home alone"), and counting those as a good feeling wiped out the bad
# one in the line.
OK_WORDS = frozenset(("ok", "okay", "okey"))
# The words for a good day that are also another thing: "grand" is a sum of money, "sound"
# is a noise, "chill" is a cold, "content" is what is in a letter. Said about the speaker they
# are how the person is - "im grand ta", "im sound thanks", "im chill" - so they count as a good
# feeling only there, and "the sound of the boiler" or "the content of the email" carries none.
SAYS_HOW_THEY_ARE = frozenset("""alright alrighty grand sound chill content brill mint
    sorted""".split())
STATING_VERB = frozenset("""am is are was were feel feels feeling felt do does doing be been
    seem seems look looking""".split())
SPEAKER = frozenset(("i", "we"))
NEWS = ("i just", "i finally", "today i", "yesterday i", "we got", "we are getting",
        "i got", "i have just", "i have just", "guess what", "big news", "i start",
        "i started", "i finished", "i passed", "i failed", "i moved", "we moved")
ABOUT_BOT = ("are you a bot", "are you real", "are you human", "are you an ai",
             "are you alive", "are you ok", "do you have feelings", "your name",
             "do you remember", "can you remember", "how old are you", "what are you called",
             "are you a chatbot", "are you a person")
ABOUT_BOT_END = ("what are you", "who are you", "what are you exactly")
ROBOT_WORDS = frozenset("bot chatbot robot ai human person machine program real alive".split())
# A man, a woman or a sex word is the bot's own only when the line asks whether it is one.
# "do you like men" asks for an opinion, so the man is the thing liked, and the answer to a
# taste is the bot's own view ("No strong view on that one. What's yours?") rather than the
# line that says what the bot is.
GENDER_WORDS = frozenset("male female man woman men women boy girl".split())
TASTE_VERBS = frozenset("like love prefer fancy enjoy hate dislike".split())


def _a_person_they_like(norm):
    """True when a sex word is what the bot is asked to like, not what it is."""
    for at, word in enumerate(norm):
        if word in TASTE_VERBS and set(norm[at + 1:]) & GENDER_WORDS:
            return True
    return False


# The internet and the data are the bot's own only in a line that also says what it was made or
# trained on. "were you trained on the internet" is about the bot; "what are you using my data
# for" is about the person's own data and keeps the phone answer it had.
LEARNED_ON = frozenset("data internet".split())


def _a_thing_they_own(norm):
    """True when the data or the internet in the line is not what the bot was made of."""
    if not set(norm) & LEARNED_ON:
        return False
    return not set(norm) & (SELF_ASK - LEARNED_ON)


# The products people name when they think there is a model behind the bot. A line that names
# one says what the bot is ("so youre claude"); an ask that names one asks whether there is a
# model under this at all, which is the reading that already had the answer for it.
ASSISTANT_NAMES = frozenset("claude chatgpt gpt gemini copilot siri alexa bard".split())
# The ask has to be the whole line: "is this chatgpt good for essays" is about the essays, and
# "are you claude" is the one that asks what is under the bot.
PRODUCT_ASK_WORDS = 7
PRODUCT_ASK_TAIL = frozenset("then really though now huh yeah or not at all literally exactly "
                             "still please pls tho".split())

# A question whose every word is about the bot is about the bot, however it is phrased: "do
# you have hobbies", "who made you", "what should i call you". SELF_WORDS are the words that
# only a question about the bot uses; SELF_ASK are the ones that make the ask about it, so a
# line with a "you" in it that names anything else ("how do you spell necessary", "what can
# you do with leftover rice") is left to the topic. Nothing here is matched alone: the whole
# line has to be made of these words for the reading to call it about the bot.
SELF_WORDS = frozenset("""you your yourself yours
name called call
made make create created built build built trained train programmed program designed design
wrote written
origin creator
hobbies hobby fun looking look looks
plans plan
bored busy tired awake
feel feelings dream dreams dreamt sleep eat
real alive human person bot robot ai chatgpt gpt claude gemini copilot siri alexa bard
understand remember recall forget
chat talking talk chats answering answer
doing get
from tell
heart soul souls emotion internet data male female man woman men women
model models llm llms personality single married live learn learnt asleep
cry laugh hungry drunk boy girl gender old young
okay ok alright fine""".split())
SELF_ASK = frozenset("""name called call made make create created built build trained train
programmed program designed design wrote written origin creator hobbies hobby fun looking look
looks plans plan bored busy real alive human person bot robot ai chatgpt gpt claude gemini
copilot siri alexa bard understand
remember recall forget get from tell heart soul souls emotion internet data
male female man woman men women personality single married live sleep eat dream dreams
asleep cry laugh hungry drunk boy girl gender old young""".split())
SELF_FILLER = frozenset("""what why how who where when which whose is are was were am do does
did can could will would shall should have has had a an the any some your you yourself yours
i me my at from about like of for to with now then today tonight ever actually really even
still just so much very both all or either on in by using up and so then ok okay""".split())
# "not" is a filler only in front of the bot's own name ("youre not chatgpt", "are you not
# real"). Behind any other verb it is the line's own negative, and the clause it opens is
# about something else: "what do you do when you cant sleep" is a question about sleep, and
# reading it as a question about the bot answered it with the identity line.
# A contraction carries its "not" in front of the subject, so "cant you sleep" reaches this
# line as "can not you sleep" with the bot two words after the not; and the subject can sit in
# front of the auxiliary too ("you cant sleep" is "you can not sleep"). The bot is the subject
# of that clause in both, and the clause is the whole line, so the not is still the bot's own.
NOT_AFTER_THE_BOT = frozenset("you youre your u ur ya are is this it thats that".split())
# The bot word that stands right after a "not" came with the contraction: "cant you sleep",
# "wouldnt you like to know", "didnt you understand me" are all somebody asking about the bot.
NOT_BEFORE_THE_BOT = frozenset("you u ur ya your yourself yours".split())
# The word a "not" leans on when the subject came first: "you can not sleep".
NOT_AUX = frozenset("""can could will would do does did are is was were am have has had
    should shall""".split())
# A clause of the line's own opens here, and the bot named after it is the person's, not the
# line's subject: "what do you do when you cant sleep" keeps its sleep question.
CLAUSE_OPENERS = frozenset("""when whenever if once after before until till while since
    as because unless though although""".split())
# What the bot can do, asked about the bot itself: "what can you do?", "what can you help
# with?". It is about the bot only when nothing else follows: "what can you do with leftover
# rice", "what can you help me cook tonight", "what do you do when your boiler breaks" ask
# about the rice, the dinner and the boiler, and the topic has to decide those.
CAPABILITY = ("what can you do", "what do you do", "how do you work", "what can you help",
              "how can you help", "how do you help", "what can i ask you",
              "what are you good at", "what are you for", "what kind of things can you help")
CAPABILITY_FILLER = frozenset("actually exactly really just still even then now here please "
                              "mate pal though anyway so also "
                              # An "else" or "other" in front of the ask asks the same thing:
                              # "what else do you do", "what other things can you do" are what
                              # a person says after "are you a bot", and the doings pool was
                              # answering them "Nothing much, honestly - no day of my own to
                              # spend." A lead word in front ("so what else do you do", "and
                              # what else can you do") is the same ask too.
                              "else other and but oh yeah ok okay well um hmm".split())
# "else" and "other" are not carriers when a subject follows them, so the subject test below
# still keeps "what else can you do about my leaking boiler" as an ask about the boiler.
# Words that carry no subject of their own, so "with" in "what can you help with" is not one.
# Articles are carriers too because a real subject keeps its noun: "what do you do with a spare
# room" is still about the room. "living" is the one that is only ever the idiom: "what do you do
# for a living" asks what the bot does, and it was read as a question about a living.
# A time or an occasion is not a subject either: "what can you do this weekend", "what do you do
# on weekends", "what can you do in five minutes". The words that make up the time phrase carry
# nothing, and a real subject on the end still keeps its noun, so "what can you do with two
# apples" is about the apples and "what can you do on a rainy day" keeps its day.
CAPABILITY_CARRIER = frozenset("""
    with for about me us at in on during here around then now any anything
    a an the living this that these those next last another more some all
    usually often
    tonight today tomorrow later evening morning afternoon night week weekend
    time times day days evening evenings night nights week weeks weekend weekends
    month months year years hour hours minute minutes second seconds while bit
    one two three four five ten fifteen twenty thirty sixty couple few half
""".split())
CORRECTION = ("i meant", "i mean", "sorry i meant", "rather than", "not ", "actually i",
              "correction", "i said", "no wait", "wait no", "oops i meant", "scratch that")
# Asking the bot what it is doing is conversation, not a question about the world: "what u up
# to", "what you been up to", "you up to much", "much going on". The test is the whole line, so
# a line that names anything else ("what are you doing about the leak", "what are you doing on
# saturday") keeps its own kind and its own topic.
# The words that turn "going on" into a question about the world ("anything going on tonight").
GOING_ON_WHEN = frozenset("""tonight today tomorrow later week weeks weekend morning evening
    night saturday sunday monday tuesday wednesday thursday friday now""".split())
DOING_FILLER = frozenset("""what whats u you ya r are is doing do up to too much been have
    has lately now today tonight then at the moment anything something nothing going on this
    week new else still with watcha whatcha wotcha watchu whatchu doin mate pal buddy love
    lovey hon hun then friend""".split())
# A day already spent, said after the ask: "what have you been up to at the weekend", "what did
# you do yesterday", "where were you last night". The bot has no Saturday ahead of it, so a day
# still coming is left alone and keeps the fence above: "what are you doing on saturday" is the
# plan the person is asking about. The past auxiliary is what tells the two apart.
BEEN_WHEN = frozenset("""yesterday today last night nights morning mornings afternoon afternoon
    evening evenings weekend weekends week weeks day days these all the at over on in this since
    so far lately recently""".split())
BEEN_SAID = frozenset("""did done been were was had doing do up where get got""".split())
# A span of time the bot is supposed to have spent somewhere: "where have you been all day",
# "where have you been lately", "where were you last night". The line is a place question, but
# the place asked about is the bot's own time, and the answer "no address" is the answer to a
# different question. Without a span the plain "where have you been" keeps its place reading,
# which the chat module answers honestly ("nowhere you could visit"). "hiding" is here because
# "where have you been hiding" is the same ask with a joke in it.
SPENT_TIME = frozenset("""all whole day days night nights week weeks lately recently since far
    these hiding""".split())
STILL_COMING = frozenset("""tomorrow tonight later next""".split())

SMALL_TALK = ("how are you", "how is it going", "how's it going", "how is your day",
              "how's your day", "nice to meet you", "what's up", "how do you do",
              "lovely weather", "freezing", "raining", "sunny", "long week", "busy day")
ASK_KEYS = ("how_long", "how_much", "how_many", "how_often", "what", "why", "how", "when",
            "where", "who", "which", "yesno", "choice", "recommend", "steps", "opinion",
            "compare", "definition", "write", "maths", "list")
# Short lines that answer the bot's last turn rather than start a new thought.
SHORT_REPLIES = ("not much", "nothing much", "same here", "me too", "you too", "no idea",
                 "not really", "sort of", "kind of", "fair enough", "sounds good",
                 "sounds great", "good idea", "will do", "i will", "i agree", "me neither",
                 "makes sense", "got it", "for sure", "why not", "of course", "i guess",
                 "that is fair", "no worries", "all good", "very funny", "so true",
                 "not bad", "not a lot", "not a clue", "no bother", "i suppose", "guess so",
                 "u too", "you as well", "same to you", "back at you", "hbu", "wbu", "nmu",
                 "true that", "fair point", "good point", "my pleasure", "any time",
                 "not really sure", "i think so", "hopefully", "probably", "definitely",
                 "absolutely", "exactly", "agreed", "correct", "right", "true",
                 "i dont know", "dont know", "i dunno", "dunno", "who knows", "no clue",
                 "search me", "you know", "not sure", "no idea to be honest",
                 "i do not know", "do not know", "not much", "how about you",
                 "i know right", "you are welcome", "no problem", "same old", "same as always",
                 "what about you", "not too bad")
# Idioms of agreement whose words are the shape of a request: "tell me about it" is "I know,
# you're telling me", not an ask for a briefing, and "you can say that again" is the same
# agreement said louder. The whole line has to be the idiom, so "tell me about the boiler" is
# still the ask its words look like. Kept apart from SHORT_REPLIES because the reply these
# want is not the flat ack: the person has just agreed with something the bot said, so the
# answer carries the agreement back and leaves the floor open.
# Written the way the normaliser spells a line: the apostrophe is gone and the contractions are
# opened out ("don't i know it" arrives as "do not i know it").
AGREEMENT_IDIOMS = ("tell me about it", "you are telling me", "do not i know it",
                    "you can say that again", "you are not wrong", "preaching to the choir",
                    "you and me both", "i know right", "i hear that", "amen to that")


def agreement_of(text):
    """The idiom of agreement the whole line is, or None: "tell me about it", "you and me both".

    The idiom has to be the whole line, or the whole of its first clause: "tell me about it, i
    had one last year" agrees and then says why, and the normaliser writes the clause mark that
    tells the two apart. Anything tighter is the ask the words look like - "tell me about the
    boiler", and also "tell me about it properly", which wants a fuller answer and not a nod.
    """
    said = " ".join(text.lower().replace(",", " ").split())
    first = " ".join(said.split("|")[0].split())
    flat = " ".join(said.replace("|", " ").split())
    return next((phrase for phrase in AGREEMENT_IDIOMS
                 if flat == phrase or first == phrase), None)
EVENT_WORDS = frozenset("""asked told said got went started finished had was were just
today yesterday tomorrow week weekend month year moved passed failed lost found bought sold
paid booked applied interview job trip visit party birthday meeting doctor dentist school
work flat house car dog cat baby wedding holiday""".split())
MATH_WORDS = frozenset("plus minus times divide divided percent percentage half double "
                       "triple sum total average calculate equals".split())
DEFINITION = ("what is a", "what is an", "what are", "what does", "difference between",
              "meaning of", "explain")
# "what are" is the start of two different asks. Said of a thing it asks what the thing is
# ("what are capers", "what are the rules"), which is a definition. Said of a person it asks
# what they are doing with their time ("what are you up to", "what are you doing today",
# "what are we having for dinner"), which is a question, not a definition, and reading it as
# one sent the line to the search hedge instead of the answer.
ASKS_ABOUT_A_PERSON = re.compile(r"\bwhat (?:is|are|r) (?:you|u|ya|we|us|they)\b")

# A bare "what is X", with no article, is the same definition ask: "what is burnout", "what is
# copd", "what is polenta". The phrase list above needs "what is a" or "what is an", so 208 of the
# 266 bare forms on the deck carried no definition at all: the reply was a proper definition and
# there was no label to read it against.
BARE_DEFINITION = re.compile(
    r"^\s*(?:(?:and|but|so|then|ok|okay|right|oh|well|now|sorry|hi|hello|please)\s+)*"
    r"what(?:'s|s| is| are| was)?\s+(?:is|are|was)\s+([a-z][a-z'\u2019-]{1,28})"
    # Not a definition: something compared or judged ("whats french food like", "what is scotland
    # for a weekend"), a purpose ("what is this for"), a live figure or listing ("what is today's
    # date", "whats showing at the odeon", "what is the weather").
    r"(?![^?]*\b(?:like|for|worth|good|cheap|cheapest|easier|easiest|better|best|worse|worst|"
    r"date|time|day|weather|price|cost|news|forecast|temperature|showing|playing|opening|"
    r"score|length|size)\b)", re.I)
# The head word of a bare "what is X" that names nothing to define: an article or pronoun ("what
# is it", "what is this"), a preposition ("what is in the fridge", "whats behind it"), a state
# ("what is happening", "whats coming up"), a number ("what is two thirds of a cup"), or a word
# for no particular thing ("whats something cheap to do tonight").
NOT_A_DEFINITION_HEAD = frozenset("""a an the my your our his her their its this that these
those it i you we they he she there on in up out off about wrong going happening happened next
new best better missing too more most so all any some not just for to with from of at by under
over behind inside between near against than left coming showing playing occurring eating cooking
red one none something anything nothing everything someone anyone everyone two three four five
six seven eight nine ten half quarter third quarter percent percent cheapest easiest quickest
longest shortest biggest smallest largest worth nice easy good double triple eleven twelve thirteen fourteen fifteen sixteen seventeen
eighteen nineteen twenty thirty forty
fifty sixty seventy eighty ninety hundred thousand million""".split())

def _has_any(text, phrases):
    return any(phrase in text for phrase in phrases)


# The greetings and weather words, as the normalised line spells them: the apostrophe is gone by
# then, so "how's it going" arrives as "how is it going".
SMALL_TALK_WORDS = tuple(tuple(phrase.replace("'s", " is").replace("'", "").split())
                         for phrase in SMALL_TALK)
# What may be left over once the greeting itself is taken out and the line is still only small
# talk: the filler of a spoken greeting ("how are you doing then mate", "sunny again today"), the
# greeting that came in front of it ("hiya, how are you doing") and the short function words that
# carry it. A word that names something - a thing, a job, a dish, a verb of doing - is a second
# subject, so the line is not small talk: "raining cats and dogs" is a saying, "the pipes are
# freezing" is about the plumbing and "how are you supposed to defrost a turkey" is a cooking
# question.
# What people call each other in a greeting: a term of address is filler, not a subject, so
# "how are you today my friend" is a greeting and not a line about a friend.
ADDRESS_WORDS = frozenset("""love hun hunny hon dear darling duck pet chuck sweetheart sweetie
    son sunshine mate mates friend friends guys folks""".split())
SMALL_TALK_LEFTOVER = frozenset("""
a an the for of in on out up there here it its is are was were be been am has
and or so but then now again today tonight tomorrow lately already still very really too
quite just all right well good fine bad ok okay not no thanks thank you thx ta cheers ty
u ya mate mates friend friends guys folks everybody everyone hope your way doing going
getting had have last this week month day morning evening night long busy how what about
with us we i around yet even ever only mostly to at by from much appreciated appreciate
my your our their both all two
""".split()) | ADDRESS_WORDS | frozenset(word for greeting in GREETINGS for word in greeting.split())


def small_talk_only(norm):
    """True when the line is a greeting or a word about the weather and nothing else.

    The greeting is taken out first and what is left has to be filler, which is what keeps the
    phrase from matching inside a longer thought: "raining" is small talk in "raining again"
    and weather in "raining cats and dogs"; "how are you" is a greeting, and "how are you
    supposed to defrost a turkey" is a question about a turkey.
    """
    if not norm or len(norm) > 10:
        return False
    for phrase in SMALL_TALK_WORDS:
        size = len(phrase)
        for at in range(len(norm) - size + 1):
            if tuple(norm[at:at + size]) != phrase:
                continue
            rest = set(norm[:at]) | set(norm[at + size:])
            if not rest - SMALL_TALK_LEFTOVER:
                return True
    return False


# What a feeling word can be followed by and still be about how someone feels: a preposition
# ("mad at him"), a connective ("sad that it rained"), a time word that ends the thought
# ("im mad now"). Anything else after it makes the word describe that thing instead: "a mad
# day", "mad busy", "a sad film" say nothing about how the person feels.
CUE_FOLLOW = frozenset("""at with about of by from for in on into onto upon out up down off
away back over under than if as while since during after before until though although unless
around through toward towards even again too also just still yet ever never always sometimes
often usually mostly all any some every each both either neither most much more less least
enough quite pretty really very so that when because and but or now today yesterday tonight
this these those tbh tho atm rn lol haha innit actually
inside outside deep down lately
tomorrow honestly though still lately recently afterwards anyway here there one
i me my mine myself you your yours yourself he him his she her hers it its itself we us our
ours ourselves they them their theirs themselves who whom whose what why how where which
whether is are was were am be been being will would shall should can could may might must
have has had having do does did doing done dont didnt doesnt wont cant im ive ill id youre
theyre thats its gonna going gotta
to as please pls thanks thank cheers sorry sick stiff silly rotten
mate man bro dude guys folks everyone everybody buddy pal bud hon hun love sir madam team""".split())

# The openers of a phrase that says what a thing was like ("a mad day", "a sad film") rather
# than how someone feels. When one of these follows a feeling word, the words after it decide:
# a phrase with a verb in it is still about the person ("im mad the dog ate it"), a bare noun
# phrase is about the thing ("a mad day at work").
PHRASE_OPENERS = frozenset("""the a an this that these those my your his her its our their some
any no every each another one""".split())
# Words that say the words after a feeling word are a clause of their own: a helper verb, a
# verb written in the past, or one of the ordinary irregular ones people use about a day.
CLAUSE_VERBS = frozenset("""went got came said saw made took gave found lost left ran broke fell
kept met paid put sent sat stood thought told won wrote bought brought caught chose drove flew
forgot heard held hit knew ate drank slept woke bit spoke spent built burnt burned grew threw""".split())

# Words that say a clause follows a feeling word when the words themselves do not: a helper, or
# the negations that repair one ("im gutted mum will not come", "im worried she did not eat").
CLAUSE_HELPERS = frozenset("""is are was were am be been being will would shall should can
could may might must have has had having do does did doing not never just still already yet""".split())
# A feeling word in front of one of these is still about the person, because the noun is a state
# a person is in and not a thing beside them: "im in a mad mood", "i was in a low state", "shes
# in a right temper". Only the article in front of it says so - "we went to a mad place" names a
# place - so the words before the feeling have to end on "in a"/"of a" and the like.
STATE_NOUNS = frozenset("""mood state spirits temper frame mind head shape form headspace
mindset humour humor moodstate""".split())
STATE_TAIL = re.compile(r"\b(?:in|of)\s+(?:a|an|such\s+a|a\s+right|a\s+real|a\s+proper|"
                        r"the|this|that)\s*$")

# "i am gutted", "i was scared", "i feel low": the feeling is the speaker's own, so a clause
# after it is what the feeling is about rather than a description of a thing.
SPEAKER_TAIL = re.compile(r"\bi (?:am|was|feel|felt|have been|had been|do feel|did feel"
                          r"|am feeling|was feeling|been feeling|have been feeling"
                          r"|had been feeling)$"
                          # "i woke up feeling numb", "i sat there feeling empty": the feeling
                          # verb is what matters, whichever words came before it.
                          r"|\bi(?: \w+){1,3} (?:feel|feeling|felt)$"
                          # "we are shattered", "we were gutted": the same state said of us.
                          r"|\b(?:we|us) (?:are|were|feel|felt|have been|had been|do feel"
                          r"|did feel|are feeling|were feeling|been feeling)$"
                          r"|\bwe(?: \w+){1,3} (?:feel|feeling|felt)$"
                          # "were shattered": people write "we're" as "were".
                          r"|^were$")


def cue_about_person(text, cue):
    """True when this feeling word says how someone feels, not what something was like.

    The word is found whole ("mad" is not in "made"), and it counts when it ends a clause or
    is followed by a preposition, a connective or a time word: "im mad", "she was cross with
    me", "driving me mad", "mad at my sister", "im mad now". It does not count when it comes
    straight before another word: "a mad day", "mad busy", "a sad film", "happy birthday".
    """
    if cue in PARTICLE_STATES:
        for found in re.finditer(r"\b" + re.escape(cue) + r"\b", text):
            if _a_direction(text, found.start()):
                return False      # "im going down the pub" is a place, not a low
    if cue.split()[-1] in CUE_FOLLOW:
        # The cue ends on a preposition or a connective ("feel awful about", "no one to
        # talk to"): it already reads as how someone feels, so what follows adds nothing.
        return bool(re.search(r"\b" + re.escape(cue) + r"\b", text))
    for match in re.finditer(r"\b" + re.escape(cue) + r"\b", text):
        if _a_verb_holds_it(text, match.start()):
            # "im moving flat on saturday" is a move to a flat, not a low mood: the verb in
            # front of the word takes it as its object, so the word is a thing here.
            continue
        rest = text[match.end():].lstrip()
        if not rest or rest[0] in ".,!?;:-|":
            return True
        following = rest.split()[0].strip(".,!?;:-|")
        if not following or following.lower() in CUE_FOLLOW:
            return True
        if following[:1].isupper() and following.lower() not in lexicon.COMMON:
            # A name after the feeling is the person being spoken to: "im mad Jess".
            return True
        if following.lower() in STATE_NOUNS and _state_before(text, match.start()):
            # "im in a mad mood" is the speaker's own state; "we went to a mad place" is a place.
            return True
        if following.lower() in PHRASE_OPENERS and _clause_follows(rest):
            # "im mad the dog ate the sausages" is a feeling and a clause; "a mad day at work"
            # is a phrase about the day, with no verb in it.
            return True
        if _speaker_before(text, match.start()) and _verb_after(rest):
            # A person is not a description. "im gutted mum cancelled" opens on a noun that is
            # nobody's phrase opener, so the words after it are read instead: a verb there is a
            # clause about the person's feeling, and "im mad busy today" has none.
            return True
    return False


# Words ending in -ing that are things or names, so the guard below leaves them alone: "im at the
# building in the morning" is not a verb holding the word after it.
ING_THINGS = frozenset("""morning evening ceiling building wedding pudding clothing shopping
    offering meeting parking lighting heating bedding flooring roofing fencing bedding
    thing something nothing anything everything king ring string spring wing sing bring swing
    going being doing having making taking coming""".split())

# The -ing words that take no object. "im moving flat" and "im renting flat" are a move and a
# tenancy: the verb in front of the feeling word takes it as the thing the verb acts on. A verb of
# posture, movement or becoming takes no object at all - what follows it is what the person is
# doing it *as*, or where they are - so "im sitting sad", "im running flat", "im becoming sad"
# and "im staying sad" are all the person's own state, said with the verb still going on. Read as
# objects, ten of those lines lost the condolence they had and got a card about the next thing.
ING_TAKES_NO_OBJECT = frozenset("""
    act acting appear appearing arrive arriving become becoming come coming fall falling feel
    feeling get getting go going grow growing keep keeping lie lying live living look looking
    remain remaining rest resting rise rising run running seem seeming sit sitting sleep sleeping
    sound sounding stand standing stay staying turn turning wait waiting walk walking work
    working""".split())


def _a_verb_holds_it(text, at):
    """True when the word in front of a feeling word is a verb doing something to it.

    "im moving flat on saturday" is a move to a flat and "im renting flat next month" is about
    the tenancy, but both read as a low mood because a feeling word followed by a preposition
    counted as the person's own state. An -ing word in front of it is the verb that takes it as
    its object, wherever the person cue sits - but only a verb that can take an object at all
    (ING_TAKES_NO_OBJECT), because "im sitting sad" is the person's own state with a verb going
    on beside it, not a thing done to the sadness. A copula or a feeling verb is let through,
    because those are what make the word describe the person: "i was feeling flat", "my tomato
    plants are looking sad".
    """
    words = [word.strip(".,!?;:-|\"'").lower() for word in text[:at].split()]
    if not words:
        return False
    last = words[-1]
    return (last.endswith("ing") and last not in FEELING_CUES_BEFORE
            and last not in ING_THINGS and last not in ING_TAKES_NO_OBJECT)


def _state_before(text, at):
    """True when the words before a feeling word say the state is the speaker's own.

    "im in a mad mood", "i was in such a low state", "in a right temper": a preposition and an
    article in front of the feeling word are what make the state noun next to it the person's.
    """
    words = [word.strip(".,!?;:-|\"'").lower() for word in text[:at].split()]
    return bool(STATE_TAIL.search(" ".join(words[-4:])))


def _speaker_before(text, at):
    """True when the words in front of a feeling word make it the speaker's own state.

    "i am gutted", "i was scared", "i feel low", with a degree word allowed in between
    ("im so gutted"). It says nothing about "i have a mad idea" or "we had a mad time".

    The words are read as typed, so the short forms are spelled out first: people write "im"
    far more often than "i am", and "im gutted mum cancelled" is the same feeling as "i am
    gutted my mum cancelled".
    """
    words = [word.strip(".,!?;:-|\"'").lower() for word in text[:at].split()]
    while words and words[-1] in FEELING_FILLER:
        words.pop()
    tail = " ".join(words[-5:])
    tail = re.sub(r"\bi'?m\b", "i am", tail)
    tail = re.sub(r"\bi'?ve\b", "i have", tail)
    if SPEAKER_TAIL.search(tail):
        return True
    # "my mood is low", "my energy is low", "my anxiety is bad": the speaker's own mood,
    # energy or nerves, named as a thing. Any other thing is still a thing ("my back is sore").
    recent = words[-4:]
    if "my" in recent:
        for word in recent[recent.index("my") + 1:]:
            if word in MOOD_NOUNS:
                return True
    return False


def _verb_after(rest):
    """True when a clause follows a feeling word: a helper or a verb in the next few words."""
    words = [word.strip(".,!?;:-|\"'").lower() for word in rest.split()[:5]]
    for word in words:
        if word in CLAUSE_HELPERS or word in CLAUSE_VERBS:
            return True
        if len(word) > 3 and word.endswith(("ed", "ing")):
            return True
    return False


def _clause_follows(rest):
    """True when the words after a feeling word are a clause: "the dog ate it", "my sister
    forgot my birthday". False for a bare phrase that describes the thing: "day at work".
    """
    words = [word.strip(".,!?;:-|'\"") for word in rest.split()]
    end = len(words)
    for i, word in enumerate(words):
        if word and word[-1] in ".,!?;:-|":
            end = i + 1
            break
    clause = [word.lower() for word in words[:min(end, 8)] if word]
    if not clause:
        return False
    for word in clause[1:]:
        if word in CUE_FOLLOW or word in CLAUSE_VERBS or word.endswith("ed"):
            return True
    return False


# A body part is "upset" too, and that is a stomach rather than a mood: "my stomach is upset".
BODY_SUBJECT = frozenset("""stomach tummy gut belly back leg legs arm arms head throat chest skin
eye eyes ear ears tooth teeth stomachs""".split())


def _a_body_part_before(text, cue):
    """True for "my stomach is upset", where the word before the cue is a body part."""
    for match in re.finditer(r"\b" + re.escape(cue) + r"\b", text):
        before = [word.strip(".,!?;:-|\"'").lower() for word in text[:match.start()].split()]
        before = [word for word in before if word not in FEELING_FILLER and word != "is"]
        if before and before[-1] in BODY_SUBJECT:
            return True
    return False


# The words that can stand between a person and their state: "im so shattered", "they were
# really low", "my mum is pretty awful".
STATE_JOINERS = frozenset("""am is are was were be been being feel feels feeling felt still
really very so too pretty quite a bit little just now also always lately today tonight""".split())


# A state word that is also something a person does takes an object: "i wiped out the savings"
# and "he upset the cart" are actions, not how somebody is. A determiner or a possessive after
# the word is the object, so the state has to stop first (at a clause word, or the end of the line).
OBJECT_MARKERS = frozenset("""the a an my your his her their our this that these those
another every some any no""".split())
# A demonstrative in front of a time word opens a time phrase, not an object: "i feel low this
# week" names when the week was, and "im shattered every morning" the mornings. The week is not
# something the person felt low out of, the way "i wiped out the savings" is.
TIME_MARKERS = frozenset("this that these those every each".split())
TAIL_STOPS = frozenset("""after before since until when if and but so because though while
than then too also still now today tonight lately recently honestly about at in on of for to
with by from as like""".split())


def _takes_an_object(text, end):
    """True when what follows a state cue turns it into an action with an object."""
    words = [word.strip(".,!?;:-|\"'").lower() for word in text[end:].split()]
    for pos, word in enumerate(words):
        if not word or word in TAIL_STOPS:
            return False
        if word in OBJECT_MARKERS:
            after = words[pos + 1:pos + 2]
            if word in TIME_MARKERS and after and after[0] in TIME_FILLERS:
                return False       # "i feel low this week": the week is when, not an object
            return True
    return False


def _object_after(text, cue):
    """True when any place this cue occurs in the line is followed by an object."""
    return any(_takes_an_object(text, match.end())
               for match in re.finditer(r"\b" + re.escape(cue) + r"\b", text))


def _state_cue(cue):
    """The word in `SELF_ONLY_STATE` this cue is built on, or None: "wiped out" is "wiped"."""
    if cue in SELF_ONLY_STATE:
        return cue
    head = cue.split()[0]
    return head if head in SELF_ONLY_STATE else None


# A state word that is also what an animal does: "im pooped" is tired, "the dog pooped on the
# carpet" is the dog. The state has to be carried by a copula or a feeling verb, so the same word
# said of a pet with nothing in front of it is the pet's doing.
VERB_ONLY_STATE = frozenset("pooped".split())
# What carries a state onto a subject: "im pooped", "i was pooped after the run", "we both feel
# pooped". Intensifiers between it and the word are skipped ("im so pooped").
COPULA_BEFORE = frozenset("""im am is are was were be been being feel feels felt feeling
get gets got gettin look looks looked seem seems seemed sound sounds sounded""".split())


def _a_copula_before(text, start):
    """True when a copula or a feeling verb comes just before `start`: "im so pooped"."""
    words = [word.strip(".,!?;:-|\"'").lower() for word in text[:start].split()]
    while words and (words[-1] in FEELING_FILLER or words[-1] in ("both", "all")):
        words.pop()
    return bool(words) and words[-1] in COPULA_BEFORE


def _state_of_a_person(text, cue):
    """True when a person is what the feeling word is said of: "im low", "they were shattered".

    The word before the cue is the subject, skipping the joiners, so a thing is still a thing:
    "the battery is low", "the windscreen is shattered", "work has been awful lately".
    """
    for match in re.finditer(r"\b" + re.escape(cue) + r"\b", text):
        if cue in SUPPLY_WORDS and _about_a_supply(text, match.end()):
            continue                       # "im low on milk": a shortage, not a mood
        if cue in VERB_ONLY_STATE and not _a_copula_before(text, match.start()):
            continue                       # "the dog pooped on the carpet": the pet's verb
        if _takes_an_object(text, match.end()):
            continue
        words = [word.strip(".,!?;:-|\"'").lower() for word in text[:match.start()].split()]
        while words and (words[-1] in STATE_JOINERS or words[-1] in FEELING_FILLER):
            words.pop()
        if not words:
            return True                    # "feeling low today": no noun, so the speaker
        subject = words[-1]
        if subject in PERSON_SUBJECT or subject in OTHER_PEOPLE:
            return True
        if subject in MOOD_NOUNS and "my" in words[:-1][-3:]:
            return True                    # "my mood is low", "my energy is low"
        if _speaker_before(text, match.start()):
            return True                    # "i feel low", "we were shattered"
        return False
    return False


def _said_of_the_speaker(text, cue):
    """True when this cue comes straight after a self cue: "im empty", "i feel out of sorts".

    A word that is also an ordinary word for a thing needs it: "the flat is cold" and "an empty
    shelf" name a thing's state, and "a blank page" a page's.
    """
    for match in re.finditer(r"\b" + re.escape(cue) + r"\b", text):
        if _speaker_before(text, match.start()):
            return True
    return False


# A word that rates what somebody can do is not a mood: "im crap at maths" and "she's rubbish
# at school" are about ability, and the same word on its own is the mood ("im crap today").
# The reply side keeps its own copy of this list; both say the same thing.
ABILITY_AT = re.compile(r"\b(?:bad|crap|rubbish|rough|useless|hopeless|terrible|awful|lousy|"
                        r"poor|worse|worst)\s+(?:at|with)\b")


# A feeling word in front of its own episode is still the feeling: "im having a panic attack",
# "she had two anxiety attacks". A word that runs on into another word usually describes that
# word ("a mad day"), but these nouns name nothing except the feeling itself, so they cannot
# turn it into a description.
EPISODE_NOUNS = frozenset("attack attacks episode episodes spell spells".split())


def _names_an_episode(text, cue):
    """True for "panic attack": the cue runs into the noun for its own episode."""
    for match in re.finditer(r"\b" + re.escape(cue) + r"\b\s+(\w+)", text):
        if match.group(1).lower() in EPISODE_NOUNS:
            return True
    return False


# "down" says how somebody is, and it is a direction or a particle just as often: "turn the heat
# down", "keep it down", "a down sleeping bag", "coming down with a cold". The feeling list never
# carried the word, so "i have been down all week" was read as news and handed back as an echo.
# It names a feeling only in the shape that leaves no other reading - a copula or a feeling verb
# right before it ("im down", "feeling down today", "i have been a bit down all week"), the
# speaker or somebody named having it, and nothing after it that makes it agreement or a shortage
# ("im down for that", "down to my last tenner"). The list stays a list of one: the same rule on
# "bad", "terrible" or "heavy" reads a bad back, a terrible cough and heavy legs as a low day.
STATE_AS_FEELING = frozenset(("down",))
# What the word is followed by when it is agreement or a shortage rather than a mood.
FEELING_NOT_MOOD = frozenset("""for to on at""".split())
# The only words allowed between the verb and the state: degrees, and the small adverbs people
# put there. Anything else means the verb belongs to another word - "coming down with a cold",
# "get him to sit down" - and the state there is a particle or an adjective, not the feeling.
FEELING_FILLER = frozenset("""a an bit little lot kind kinda sort so too very really quite pretty
    just still always again now today totally honestly also either all more most less as
    enough well""".split())
# The words that can make a state word describe somebody: a copula or a feeling verb. "a" and
# "the" are in `COPULA` because they let a state describe the noun after them ("a bit low"), and
# a determiner before "down" is the opposite case - "a down sleeping bag", "the down pillow".
FEELING_COPULA = frozenset("""am is are was were be been being feel feels feeling felt get gets
    getting got seem seems seemed look looks looking sound sounds sounded""".split())
# Words that stand between a person and a feeling word without taking it as their object: the
# copulas and the feeling verbs ("i was feeling flat", "the plants are looking sad"). Every other
# -ing word in that place is doing something to the next word.
FEELING_CUES_BEFORE = FEELING_COPULA | frozenset("feel feels feeling felt".split())


def a_broken_heart_shape(text):
    """True when the line says a heart is broken, in any of the shapes people type it."""
    low = " ".join(str(text or "").lower().replace("\u2019", "'").split())
    return bool(HEART_IN_A_STATE.search(low) or BROKEN_HEARTED.search(low)
                or BROKE_A_HEART.search(low) or A_BROKEN_HEART.search(low))


# The words that put the broken heart on somebody else: "her heart is broken" is a friend's
# trouble, and the sad pool's advice is written for the person who is in it.
NOT_THEIR_OWN = frozenset("""her his their your mum mom mother dad father son daughter husband
    wife partner friend sister brother child kid boss neighbour neighbour's nan gran""".split())

# The people a heart can belong to without being the speaker's. "she is heartbroken" and
# "my dad was broken hearted" are somebody else's trouble, and the card about a broken heart is
# written for the person who is in it. Only a person who is the *subject* of the line counts:
# "her heart is broken" puts the heart itself first, and a heart is a part of a person, so
# reading whose it is takes more than the word in front of it.
A_PERSON_ELSE = frozenset("""mum mom mother dad father son daughter husband wife partner
    friend sister brother child kid boss neighbour nan gran""".split())
A_PERSON_IS_THE_SUBJECT = re.compile(r"^(?:he|she|they|him|them)\b")
# A heart said as the thing the line is about: "his heart is broken", "my mums heart is broken".
# A heart is a part of a person, and whose it is takes reading the person, not the word in front
# of it - so a line that makes the heart the subject is left to the row that already answered it.
A_POSSESSED_HEART = re.compile(r"\b(?:my|our|her|his|their|your|the|a|an)\s+(?:\w+'?s\s+)?hearts?\b")


def _somebody_elses_heart(text):
    """True when the broken heart the line names is somebody else's, and the line says whose.

    "she is heartbroken" and "my mum is heartbroken" give another person as the subject and the
    feeling after it, which is their state and not the speaker's. It is read from the words,
    because there is no state word here for `_state_owner` to hang an owner on - "heartbroken"
    is a feeling but not a state word - so without this the line is nobody's, and the speaker's
    card answers somebody else's trouble.
    """
    low = " ".join(str(text or "").lower().replace("\u2019", "'").split())
    if not a_broken_heart_shape(low) or _a_broken_heart_is_theirs(low):
        return False
    if A_POSSESSED_HEART.search(low):
        return False                     # "his heart is broken": the heart is the thing said
    if A_PERSON_IS_THE_SUBJECT.match(low):
        return True                      # "she is heartbroken", "they are broken hearted"
    words = low.split()
    if len(words) > 1 and words[0] in ("my", "our", "the"):
        person = words[1].strip(".,!?'\"")
        if person in A_PERSON_ELSE or person[:-1] in A_PERSON_ELSE:
            if words[2:3] in (["heart"], ["hearts"]):
                # "my mums heart is broken" - the possessive apostrophe is often missing, so the
                # heart sitting right after the person is the case this reads anyway: the heart
                # is the thing the line is about, and whose it is takes more than that.
                return False
            return True                  # "my mum is heartbroken", "my wife said she is heartbroken"
    return False


HAVE_A_BROKEN_HEART = re.compile(r"\b(?:i have|i've got|ive got|i got|i had)\b[^.]{0,24}broken heart")


def _a_broken_heart_is_theirs(text):
    """True when the heart the line breaks is the speaker's own.

    "my heart is broken" and "im broken hearted" are the person's, and so is "i have a broken
    heart". "her heart is broken" and "my mum's heart is broken"
    are somebody else's, and "how do i get over a broken heart" is one in general - the sad
    pool's advice is written for the person who is in it, so only the speaker's own heart
    counts. The owner is read from the word in front of the heart, because that is where the
    line puts it, and a name or a relation with an "s" on it ("mums heart", "friends heart")
    is as much somebody else's as "her".
    """
    low = " ".join(str(text or "").lower().replace("\u2019", "'").split())
    if not a_broken_heart_shape(low):
        return False
    words = low.split()
    starts = [match.start() for match in
              (re.search(r"\bhearts?\b", low), re.search(r"\bbroken\b", low)) if match]
    at = len(low[:min(starts)].split()) if starts else 0
    window = words[max(0, at - 2):at]
    owner = window[-1] if window else ""
    if HAVE_A_BROKEN_HEART.search(low):
        return True                      # "i have a broken heart"
    if BROKE_A_HEART.search(low):
        return False    # "he broke my heart" is an event, and the break-up answer has it
    if owner in NOT_THEIR_OWN or owner.endswith("'s") or (
            owner.endswith("s") and owner not in ("is", "was", "this", "its", "us")):
        return False                     # "her heart", "my mum's heart", "mums heart"
    if any(word in ("my", "our") for word in window):
        return True                      # "my heart", "my poor heart"
    if owner in ("a", "an", "the"):
        return False                     # "a broken heart" is the thing being talked about
    return not re.search(r"\b(?:her|his|their|your)\b", low) \
        and bool(re.match(r"^(?:i|im|i'm|ive|i've|we|we're|weve|we've|our)\b", low))

# The polite way of saying a day is not great. These are the whole answer to "how are you", and
# they carry no word of mood at all, so "could be better" was read as no feeling and got a search
# hedge ("that's beyond what I know well, sorry. Searching for it will turn up better sources").
# The line has to be made of nothing else, because the same words compare things: "the sauce
# could be better" is about the sauce, "ive been better since the op" is good news, and
# "i couldnt have been better" is the best day of their life.
HEDGED_LOW = frozenset((
    "could be better", "could be better i suppose", "been better", "not so good", "not too good",
    "not so great", "not that good", "not that great", "so so"))
# The good answer with a shrug on the end. "fine i guess" is not fine: it is fine with a doubt
# after it, and the composer answers the bare "fine" with "Fair enough", which is the reply to
# somebody who does not want to talk about it. The doubt has to be the last thing in the line,
# and what it is doubting has to be the whole answer, so "ok thanks" stays the fine it is and
# "i did well i guess" is not read as a low. "not bad" is deliberately not here: it is already a
# fine, and "not bad i suppose" is the same fine said more carefully - "glad to hear it" is the
# right reply to it, not the sad pool.
HEDGED_DOUBT = ("i suppose", "suppose", "i guess", "guess", "ig", "i spose", "s'pose", "i gues")
HEDGED_OK = frozenset((
    "ok", "okay", "fine", "alright", "all right", "good", "well", "grand", "not too shabby"))
# The words a person wraps the answer in, which are not part of it: "could be better thanks",
# "been better tbh", "well, could be better". Taken off both ends, and only from the ends, so
# "im better than i was" and "the sauce could be better" keep their words.
HEDGED_WRAPPER = frozenset("""
    im i am well yeh yeah yep oh ah eh hmm hm its it it's is honestly to be totally quite
    thanks thank you ta tbh tbf lol ig i guess suppose today love mate and you you
    honest really sure actually kinda sorta atm currently now very pretty
""".split())


def _a_hedged_low(text):
    """True when the whole line is the polite way of saying not great: "could be better".

    The reading hands this the line with a bar where one clause ends and the next begins
    ("could be better | you"), so the bar is punctuation like the rest of it.
    """
    words = [word.strip(".,!?;:-'\"|") for word in str(text or "").lower().split()]
    words = [word for word in words if word]
    doubted = False
    for phrase in HEDGED_DOUBT:
        count = len(phrase.split())
        if len(words) > count and " ".join(words[-count:]) == phrase:
            words = words[:-count]
            doubted = True
            break
    while words and words[0] in HEDGED_WRAPPER:
        words.pop(0)
    while words and words[-1] in HEDGED_WRAPPER:
        words.pop()
    answer = " ".join(words)
    return answer in HEDGED_LOW or (doubted and answer in HEDGED_OK)


def _copula_just_before(words, pos):
    """True when a copula or feeling verb sits directly before the word, degrees aside."""
    for word in reversed(words[:pos]):
        if word in FEELING_FILLER:
            continue
        return word in FEELING_COPULA
    return False


def _state_as_feeling(text):
    """True when a state word of the list above is the speaker's mood in this line."""
    words = [word.strip(".,!?;:-|\"'") for word in text.lower().split()]
    for pos, word in enumerate(words):
        if word not in STATE_AS_FEELING:
            continue
        if _thing_turned_down(words, pos):
            continue                       # "turn the heat down", "keep it down"
        if not _copula_just_before(words, pos):
            continue                       # "a down sleeping bag", "coming down with a cold"
        if _particle_is_a_place(words, pos):
            continue                       # "im going down the pub", "down the stairs"
        after = words[pos + 1] if pos + 1 < len(words) else ""
        if after in FEELING_NOT_MOOD:
            continue                       # "im down for that", "im terrible at maths"
        if _whose_state(words, pos) in ("self", "other"):
            return True                    # "im down", "she is really down", "my dog seems down"
    return False


# A thing that is doing something to the person, said with a verb instead of a word for how
# they are: "work is stressing me out", "the kids are tiring me out", "this is worrying me".
# The feeling is in the verb's -ing, the person it happens to is "me", and nothing in the line
# is a word this file's lists know - so `work is stressing me out` read as no mood at all and
# was answered "Got it. Is there anything you'd like a hand with?" while "im stressed about
# work" got the stressed pool. The verb says which feeling: the stem is the state.
WORK_ON_ME = {
    "stresses": "anxious", "stressing": "anxious", "strains": "anxious",
    "straining": "anxious", "worries": "anxious", "worrying": "anxious", "worried": "anxious",
    "frets": "anxious", "fretting": "anxious",
    "drains": "tired", "draining": "tired", "drained": "tired",
    "tires": "tired", "tiring": "tired", "exhausts": "tired", "exhausting": "tired",
    "exhausted": "tired", "wears": "tired", "wearing": "tired", "wore": "tired",
    "worn": "tired",
    "annoys": "angry", "annoying": "angry", "annoyed": "angry",
    "irritates": "angry", "irritating": "angry", "irritated": "angry",
    "frustrates": "angry", "frustrating": "angry", "frustrated": "angry",
    "bugs": "angry", "bugging": "angry", "bugged": "angry",
    "bothers": "angry", "bothering": "angry", "bothered": "angry",
    "winds": "angry", "winding": "angry",
    "upsets": "sad", "upsetting": "sad", "depresses": "sad", "depressing": "sad",
    "depressed": "sad",
    "scares": "anxious", "scaring": "anxious", "scared": "anxious",
    "frightens": "anxious", "frightening": "anxious", "frightened": "anxious",
    "confuses": "confused", "confusing": "confused", "confused": "confused",
}
# The words that may sit between the verb and the person it acts on ("stressing me right out").
ACT_ON_FILLER = frozenset("""so right really totally absolutely just always still all quite""".split())
# The parts of the body a line can name as the thing doing it. `BODY_SUBJECT` above is the list
# a state word is read against; a joint that aches is the same case for this rule ("my knee is
# bothering me") and is added here rather than there.
PARTS_OF_ME = BODY_SUBJECT | frozenset("""knee knees shoulder shoulders hip hips neck ankle
    ankles wrist wrists hand hands finger fingers toe toes elbow elbows foot feet jaw tooth
    teeth sinuses earache toothache headache migraine backache""".split())
# The words that may sit in front of the verb without making it somebody else's: the copulas
# a thing gets ("the noise is bothering me"), the adverbs people put there, and the words that
# make a habit of it ("it keeps waking me up").
ACT_ON_LEAD = frozenset("""am is are was were be been being keep keeps kept get gets got
    always every still just really totally so very all quite sometimes often daily""".split())


def _works_on_the_speaker(text):
    """The feeling a thing does to the speaker, or None: "work is stressing me out".

    Only the shape <thing> <verb> me/us, and only a verb whose stem is a feeling, so "he
    stressed the point" is not it. The person acted on has to be "me" or "us": "the kids are
    tiring my mum out" is her state, not the speaker's.
    """
    words = [word.strip(".,!?;:-|\"'()").lower() for word in str(text or "").split()]
    for pos, word in enumerate(words):
        feeling = WORK_ON_ME.get(word)
        if not feeling:
            continue
        lead = None
        for back in range(pos - 1, max(pos - 4, -1), -1):
            if words[back] in ACT_ON_FILLER or words[back] in ACT_ON_LEAD:
                continue
            lead = words[back]
            break
        if lead in ("i", "i'm", "im", "me", "my", "myself", "we", "our"):
            continue                   # "im stressing me out" is nobody's line
        named = [word for word in words[max(pos - 4, 0):pos] if word not in ACT_ON_FILLER]
        if any(word in PARTS_OF_ME for word in named):
            # "my knee is bothering me", "my back is annoying me": the thing doing it is a part
            # of the body, so the line is about a pain and not about a temper. The anger pool's
            # "walk it off for ten minutes before you reply to anyone" is advice about somebody
            # who annoyed you, and it was worse here than the line's shrug.
            continue
        if lead and (lead.endswith("nt") or lead in ("not", "never", "no")):
            continue                   # "it doesnt stress me out" is not being stressed
        acted_on = None
        for ahead in range(pos + 1, min(pos + 4, len(words))):
            if words[ahead] in ACT_ON_FILLER:
                continue
            acted_on = words[ahead]
            break
        if acted_on not in ("me", "us"):
            continue                   # "...is tiring my mum out": her state, not the speaker's
        return feeling
    return None


def _skeleton(word):
    """A word with its vowels taken out: the letters that carry how it sounds."""
    return "".join(letter for letter in word.lower()
                   if letter.isalpha() and letter not in "aeiouy")


_SOUND_CUES = None


def _sound_cues():
    """({skeleton: {emotion name: cues}}, every single feeling word) this file knows."""
    global _SOUND_CUES
    if _SOUND_CUES is None:
        index = {}
        known = set()
        for name, cues in EMOTION_WORDS.items():
            for cue in cues:
                if " " in cue:
                    continue
                known.add(cue)
                if len(cue) < 4:
                    continue
                index.setdefault(_skeleton(cue), {}).setdefault(name, []).append(cue)
        _SOUND_CUES = (index, known)
    return _SOUND_CUES


def feeling_by_sound(word):
    """The feeling a word is the sound of, when it is not the feeling's spelling, or None.

    People type "im board" for bored, "im tried" for tired, "im anxty" for anxiety. Each is
    another word or no word, so the misspelling fixer may not touch it - but in the "im" frame
    the word says how the person is, and the vowels are what chat typing loses. Only a word
    that keeps the feeling's consonants, in order and with the same first letter, is read this
    way, and only when one feeling matches: "board" is bored, "im cory" and "im karen" stay
    names because no feeling sounds like them.
    """
    if not isinstance(word, str):
        return None
    low = word.strip().strip(".,!?;:'\"()").lower()
    if len(low) < 4 or not low.isalpha():
        return None
    index, known = _sound_cues()
    if low in known:
        return None      # the feeling as it is spelt: the reading's own rules decide
    if low in lexicon.COMMON_NAMES:
        # A name is not a feeling however it sounds: "im lisa" shares "lose"'s consonants and
        # "im alan" shares "lonely"'s, and both are the second line of a chat ("hi im lisa").
        return None
    matches = index.get(_skeleton(low)) or {}
    found = sorted({name for name, cues in matches.items()
                    if any(cue[:1] == low[:1] for cue in cues)})
    return found[0] if len(found) == 1 else None


# "im board", "i am tried", "i feel anxty": the frame that makes a word the person's state.
FEELING_SOUND_FRAME = re.compile(r"\b(?:im|i am|i feel|i felt)\s+(?!not\b|never\b|no\b)"
                                 r"(?:(?:so|really|very|totally|proper|dead|well|quite|pretty|"
                                 r"slightly|kinda|kind of|a bit|a little|a tad)\s+)*"
                                 r"([a-z]{4,})\b")


# What may follow a feeling word: a complement ("bored of this", "anxious about it"), a
# degree with nothing after it, or the end of the clause. A word that is a thing as well is
# only the feeling when one of these follows - "im board certified", "im board exams" and
# "im board paper" are about a board, and the deck has nobody who is bored certified.
SOUND_FOLLOWS = frozenset("""of at in with about over by again today tonight now already too
    as anymore stiff out""".split())


def _a_feeling_can_end_here(text, end):
    """True when what follows the word lets it be the state rather than the thing."""
    rest = text[end:].lstrip()
    if not rest or rest[0] in ".,!?;:":
        return True
    return rest.split()[0].strip(".,!?;:'\"") in SOUND_FOLLOWS


def _feeling_said_as_a_sound(text):
    """The feeling a word straight after "im" is the sound of, or None."""
    for match in FEELING_SOUND_FRAME.finditer(text):
        if _takes_an_object(text, match.end()):
            continue    # "im cross the road" is crossing it, and a word is not a mood there
        if not _a_feeling_can_end_here(text, match.end()):
            continue    # "im board certified" is a board
        name = feeling_by_sound(match.group(1))
        if name:
            return name
    return None


def _a_period_of_their_own(text, cue):
    """True when the state word describes a day or a week the speaker had.

    "i had a low day", "ive had a low few weeks", "today was a low day": the state stands in
    front of the period, so nothing in front of it is a person. The head of the clause has to be
    the speaker or the day itself, or the period belongs to something else ("the battery was low
    all day") and the state is that thing's.
    """
    for match in re.finditer(r"\b" + re.escape(cue) + r"\b", text):
        after = [word.strip(".,!?;:-|\"'").lower() for word in text[match.end():].split()]
        seen = 0
        while after and seen < 3 and after[0] in OWN_PERIOD_FILLER:
            after.pop(0)
            seen += 1
        if not after or after[0] not in OWN_PERIOD_NOUNS:
            continue
        before = [word.strip(".,!?;:-|\"'()").lower() for word in text[:match.start()].split()]
        for word in reversed(before[-OWN_PERIOD_REACH:]):
            if word in OWN_PERIOD_STOPS:
                break
            if word in OWN_PERIOD_HEADS:
                return True
    return False


# A thing that acts on the speaker is a feeling about the speaker, and the thing is its cause.
# "work is stressing me out", "my mum is doing my head in", "the kids are wearing me out" all read
# as no mood at all: the only feeling word in the line is a verb with the speaker as its object,
# and the cue table wants the word said *of* someone ("im stressed"). So each line was answered
# with its own words read back - "Got it - work is stressing you out." - or with a card about the
# noun instead of the feeling ("my mum is doing my head in" got the anxiety-and-sleep card). The
# verb says which feeling it is, and the subject in front of it is the cause, which is what the
# answer should be asking about.
ACTS_ON_THE_SPEAKER = (
    (r"(?:stress|stresses|stressing|overwhelm|overwhelms|overwhelming|worry|worries|worrying|"
     r"panic|panics|panicking)\s+(?:me\b|my head\b)", "anxious"),
    (r"(?:wear|wears|wearing|wore|tire|tires|tiring|exhaust|exhausts|exhausting|drain|drains|"
     r"draining|kill|kills|killing|knacker|knackers|knackering)\s+me\b", "tired"),
    (r"(?:get|gets|getting|got|bring|brings|bringing|brought)\s+me\s+(?:down|low)\b", "sad"),
    (r"(?:do|does|doing|done)\s+my\s+(?:head|brain|nut|swede)\s+in\b", "anxious"),
    (r"(?:drive|drives|driving|drove)\s+me\s+(?:mad|crazy|nuts|mental|insane|"
     r"up the wall|round the bend|round the twist)\b", "angry"),
    (r"(?:annoy|annoys|annoying|irritate|irritates|irritating|frustrate|frustrates|frustrating|"
     r"bug|bugs|bugging|wind|winds|winding)\s+me\s+up\b", "angry"),
)
# ... and not when the person is joking about it: "this is killing me lol" is a laugh, and a line
# that laughs at itself is not asking for a feeling answer.
LAUGH_AT_THE_END = re.compile(r"\b(?:lol|lmao|haha|hah|heh|jk|joking|kidding|honestly)\b[\s.!?]*$")
# A part of the body is the subject of its own line and has its own card: "my back is killing me"
# is a back, and "my feet are killing me" is a long day standing up. The verb is the same as in
# "the commute is killing me", so what is in front of it decides.
A_BODY_SUBJECT = frozenset(
    "back neck knee knees feet foot leg legs arm arms hand hands shoulder shoulders hip hips "
    "ankle ankles wrist wrists elbow elbows joint joints muscle muscles tooth teeth jaw ear ears "
    "eye eyes head stomach chest ribs rib side spine sciatica period periods boob boobs tit tits "
    "throat shoulder-blade".split())


def _acts_on_the_speaker(text):
    """The feeling a line about something acting on the speaker carries, or None."""
    if LAUGH_AT_THE_END.search(text):
        return None
    for pattern, name in ACTS_ON_THE_SPEAKER:
        for match in re.finditer(r"\b(?:" + pattern + ")", text):
            before = text[:match.start()].split()[-2:]
            if any(word.strip(".,!?;:'\"") in A_BODY_SUBJECT for word in before):
                continue
            return name
    return None
# "im getting worse" is the same state as "im worse", and only the first person is read this way:
# "its getting worse" about a leak, a cough or the traffic names something else's state.
GETTING_WORSE = re.compile(r"\b(i'?m|i am)\s+getting\s+(worse)\b", re.I)
# "im no better" is the comparison said the other way round, and it is the one people use about a
# medicine that has not worked. "better" alone is not read as a state - "im a bit better" is the
# good news, and the pool that answers it is the one that says keep going - so only the denial is
# folded into the comparison the reading already knows.
NO_BETTER = re.compile(r"\bno\s+better\b", re.I)
# "worse off" and "no better off" are about money or circumstances, not the body: "we re no better
# off than last year" is a year's wages, and the comparison has to be taken out of the line before
# anything reads it as a state.
BETTER_OFF = re.compile(r"\b(?:no\s+)?better\s+off\b|\bworse\s+off\b", re.I)
# A good word the line says has been missing is not that mood. "i cant remember the last time i
# felt happy" names "happy" with no negator near enough for `denied` to see (the polarity came out
# 1), so the mood was read as happy and the happy pool answered "That's a good place to be. Enjoy
# it." to somebody saying they cannot remember being happy. What the line says is how long it has
# been, so the frame is read as the low it is: the memory denied ("cant remember the last time"),
# or the feeling said not to have been there ("havent felt happy in weeks").
GOOD_WORD_MISSING = re.compile(
    r"\b(?:cant|can\s*not|couldnt|could\s*not|dont|do\s*not|didnt|did\s*not|havent|have\s*not|"
    r"hasnt|has\s*not|hadnt|had\s*not|never|not)\b[^.?!;]{0,40}?"
    r"\b(?:remember|remembered|felt|feel|feeling|been|be|was|were)\b", re.I)
# A comparison is the other way round - "i havent felt this happy in years" and "i cant remember
# being this happy" both say they are happy now - so "this", "so", "that" or "as" in front of the
# good word keeps it.
GOOD_WORD_COMPARED = re.compile(
    r"\b(?:this|so|that|as)\s+(?:happy|glad|pleased|excited|proud|relieved|good|great|well|"
    r"content|calm|fine)\b", re.I)
# "couldnt be better", "never been better", "i couldnt have been better": a negated copula in
# front of a comparative is the highest praise, not a good word that has gone missing. The
# missing frame is about a state the person has not had ("i cant remember the last time i felt
# happy", "i havent been happy in weeks"), and a comparative cannot be missing: it compares two
# times, and "better" says the later one is good. Read as the missing frame, every "couldnt be
# better" was answered with the condolence - the fault this rule set out to fix, upside down.
GOOD_WORD_BY_COMPARISON = re.compile(r"\b(?:better|best)\b", re.I)


def emotion_of(text):
    """The feeling the line names about a person, or None: "a mad day" is a busy one."""
    text = BETTER_OFF.sub(" ", text)
    text = NO_BETTER.sub("worse", text)
    text = GETTING_WORSE.sub(lambda match: match.group(1) + " worse", text)
    text = IDIOM_STATES.sub(" ", text)
    text = ABILITY_AT.sub(" ", text)
    for name, cues in EMOTION_WORDS.items():
        for cue in cues:
            state = _state_cue(cue)
            if state and not _state_of_a_person(text, state):
                continue
            if cue in BODY_STATE_CUES:
                if _a_body_part_before(text, cue) or _object_after(text, cue):
                    continue
            idiom = NOT_A_MOOD_THERE.get(cue)
            if idiom is not None and idiom.search(text):
                continue
            if cue in LABEL_ON_A_PERSON and _said_of_the_speaker(text, cue):
                continue
            if (cue in SELF_ONLY_CUES or cue in ALWAYS_SELF_ONLY or cue in THING_OR_PERSON_CUES
                    or cue in CONFUSED_SELF_ONLY
                    or cue in A_COMPARISON) and not _said_of_the_speaker(text, cue):
                continue
            if cue in THING_OR_PERSON_CUES and _laughed_off(text, cue):
                continue
            if (cue in PERIOD_CUES and A_PERIOD.search(text)
                    and not A_LIMIT_ABOUT_PEOPLE.search(text)
                    and (A_MONTH_PERIOD.search(text) or A_MONEY_SUBJECT.search(text))):
                continue
            if cue in SAID_AS_A_NEGATION and not denied(text, cue):
                continue
            # A good word that is ruled out is still the word the line carries: the sign comes
            # from `polarity`, and the name from here (README: "i am not happy about it" is
            # polarity -1 with emotion happy). So only a bad feeling is skipped when the line
            # denies it, because denying "sad" is not being sad.
            if name not in GOOD_EMOTION_NAMES and cue not in SAID_AS_A_NEGATION and denied(text, cue):
                continue
            if (name in GOOD_EMOTION_NAMES and GOOD_WORD_MISSING.search(text)
                    and not GOOD_WORD_COMPARED.search(text)
                    and not GOOD_WORD_BY_COMPARISON.search(text)):
                # A good word said to be missing is missed, not felt: the pool for a low is the
                # answer a friend gives to "i cant remember the last time i felt happy".
                return "sad"
            if cue_about_person(text, cue) or _names_an_episode(text, cue):
                return name
    acted = _acts_on_the_speaker(text)
    if acted:
        return acted
    if a_broken_heart_shape(text):
        return "sad"          # "my heart is broken" is the low said with the heart as the thing
    sounded = _feeling_said_as_a_sound(text)
    if sounded:
        return sounded
    # A thing doing something to the person: "work is stressing me out" names the feeling in
    # the verb, and the person it happens to is the speaker.
    worked_on = _works_on_the_speaker(text)
    if worked_on:
        return worked_on
    if _state_as_feeling(text):
        return "sad"
    # Last, and only for a line that has read as no mood at all, so nothing that already had a
    # reading can move: a day or a week the speaker had, told with a state word.
    for name, cues in EMOTION_WORDS.items():
        if name in GOOD_EMOTION_NAMES:
            continue
        for cue in cues:
            if cue in NOT_THE_SPEAKERS_DAY or cue in PERIOD_CUES:
                continue
            if denied(text, cue):
                continue
            if _a_period_of_their_own(text, cue):
                return name
    return None


# A demonstrative after a preposition stands for the thing already in play: "what do you do
# about that", "what can you do for it", "what do you do with these" are all about the thing and
# not about the bot. The carrier set below holds "about", "that" and "it" as words that carry no
# subject of their own, which is right for "what can you help with" and wrong the moment the two
# come together, because then the thing being pointed at is the subject.
REFERRING = frozenset("about for with to in on".split())
POINTED_AT = frozenset("this that these those it them".split())


def _capability_question(norm):
    """True for "what can you do?" and "what can you help with?"; False when the phrase is
    followed by something the person wants done ("with leftover rice", "me cook tonight") or
    points back at the thing in play ("about that", "for it")."""
    compact = [word for word in norm if word not in CAPABILITY_FILLER]
    for phrase in CAPABILITY:
        wanted = phrase.split()
        for start in range(len(compact) - len(wanted) + 1):
            if compact[start:start + len(wanted)] != wanted:
                continue
            tail = compact[start + len(wanted):]
            rest = [word for word in tail if word not in CAPABILITY_CARRIER]
            if rest:
                return False
            if any(word in REFERRING and i + 1 < len(tail) and tail[i + 1] in POINTED_AT
                   for i, word in enumerate(tail)):
                return False
            return True
    return False


# Questions about how the bot sees the person, rather than about a thing the person names:
# "do you like me", "what do you think of me", "are we friends". Read as ordinary questions they
# were answered as an opinion about something ("I'm easy on it - it's not a hill I'd argue from")
# or with the knowledge shrug. "do you like pizza" names something else and is left alone.
ME_ASKS = ("what do you think of me", "what do you think about me", "what do you reckon of me",
           "what do you make of me", "do you like me", "do you love me", "do you care about me",
           "are you my friend", "are we friends", "am i your friend", "do you miss me",
           "would you miss me", "will you miss me", "do you hate me", "am i annoying you",
           "do you think about me", "do you think of me", "do you ever think about me",
           "are you annoyed with me", "do you like talking to me", "do you enjoy talking to me",
           "do you like chatting to me", "do you like me talking to you")
# What people put after the ask and still leave it the ask: a tag of time ("what do you think of
# me so far"), of honesty ("... tbh") or of uncertainty ("... though"). A tag is not a new
# subject, so the phrase is still the whole question - "what do you think of me so far" was
# answered with the search shrug while "what do you think of me" had its own reply.
ME_TAIL = ("then", "though", "tho", "now", "honestly", "really", "lol", "haha",
           "tbh", "tbf", "ngl", "anyway", "still",
           # "so far", "at all": the two-word tags people end the ask with. Both words are
           # peeled from the end, so the ask underneath them is read as the whole question.
           "far", "so", "all", "at")
ME_LEAD = ("so", "ok", "okay", "oh", "yeah", "but", "well", "and", "honestly")


def _asks_how_the_bot_sees_me(norm):
    """True when the whole line asks the bot what it makes of the person.

    A tag of honesty is not a new subject: "what do you think of me tbh" is the same ask, and
    the chat-speak repair turns that tag into the words "to be honest" before this reads the
    line, so the softening phrases people end a feeling with are peeled off first. The same
    repair can also turn the "me" before the tag into "my" ("what do you think of me tbh" reads
    as "what do you think of my to be honest"), which is why the pronoun is read back: the ask
    is the ask, and the word in front of a tag is not a noun for the repair to fix.
    """
    words = list(norm)
    changed = True
    while changed and words:
        changed = False
        for phrase in MOOD_TAIL:
            size = len(phrase.split())
            if size < len(words) and words[-size:] == phrase.split():
                del words[-size:]
                changed = True
        while words and words[0] in ME_LEAD:
            words.pop(0)
            changed = True
        while words and words[-1] in ME_TAIL:
            words.pop()
            changed = True
    ask = words[:-1] + ["me"] if words and words[-1] == "my" else words
    return " ".join(words) in ME_ASKS or " ".join(ask) in ME_ASKS


# A line can ask who it is talking to without saying "you": "who is this" and "who am i
# talking to" are the plainest ways to ask the bot what it is, and both were read as naming
# nothing, so they got the search shrug. The ask is about the addressee only when the whole
# line is the ask, which is what these two shapes are; "who is it" is left out because that is
# as often a knock at the door, and "who is that" a third person in a story.
WHO_TALKING = frozenset("""talk talking speak speaking chat chatting message messaging
    text texting""".split())
WHO_A_THING = frozenset("""bot robot chatbot ai machine computer program human person""".split())
# The word a person adds to the end of the ask without changing it: "who did i just talk to
# then", "who am i talking to anyway". It is stripped before the shape is matched, so the
# same ask with a question tag on it is the same ask.
WHO_TAIL = frozenset("then please pls anyway again".split())


def _asks_who_this_is(norm):
    """True for the whole-line ask about who the person is talking to."""
    words = tuple(norm)
    while words and words[-1] in WHO_TAIL:
        words = words[:-1]
    if words in (("who", "is", "this"), ("who", "am", "i", "talking", "to"),
                 ("who", "am", "i", "speaking", "to"), ("who", "am", "i", "speaking", "with"),
                 ("who", "am", "i", "chatting", "to"), ("who", "am", "i", "chatting", "with"),
                 ("who", "am", "i", "talking", "with"), ("who", "was", "i", "talking", "to"),
                 ("who", "was", "i", "speaking", "to"), ("who", "was", "i", "speaking", "with")):
        return True
    if words[:4] == ("who", "have", "i", "been") and len(words) in (6, 7):
        return words[4] in WHO_TALKING and words[5] in ("to", "with")
    if words[:3] in (("who", "did", "i"), ("who", "was", "i"), ("who", "am", "i")) \
            and len(words) in (5, 6):
        if len(words) == 6 and words[3] != "just":
            return False
        at = 1 if len(words) == 6 else 0
        return words[3 + at] in WHO_TALKING and words[4 + at] in ("to", "with")
    if words[:3] in (("am", "i", "talking"), ("am", "i", "speaking"), ("am", "i", "chatting")):
        if len(words) == 5 and words[3] in ("to", "with"):
            return words[4] in WHO_A_THING or words[4] in ("a", "an")
        if len(words) == 6 and words[3] in ("to", "with") and words[4] in ("a", "an"):
            return words[5] in WHO_A_THING
    if words[:2] in (("is", "this"), ("is", "it")) and len(words) in (3, 4, 5):
        rest = words[2:]
        if rest and rest[0] in ("a", "an"):
            rest = rest[1:]
        if rest and rest[0] == "real":
            rest = rest[1:]
        return bool(rest) and all(word in WHO_A_THING for word in rest)
    return False


# "where are you" and "where do you live" ask where the bot is, which is its own answer ("nowhere
# you could visit") rather than the one that says what it is. The tail is only the words a person
# adds to the ask itself; a real place after it ("where are you going on holiday") is their own
# subject and keeps its answer.
WHERE_BOT_TAIL = frozenset("""from based located at out of exactly then now though really actually
    please pls mate live living staying originally today currently""".split())


def _asks_where_the_bot_is(norm):
    """True for the whole-line ask about where the bot is."""
    words = tuple(norm)
    if not words or words[0] not in ("where", "whereabouts"):
        return False
    rest = words[1:]
    if rest[:2] == ("are", "you"):
        rest = rest[2:]
    elif rest[:2] == ("do", "you") and rest[2:3] == ("live",):
        rest = rest[3:]
    elif rest[:2] == ("you", "live"):
        rest = rest[2:]
    else:
        return False
    return all(word in WHERE_BOT_TAIL for word in rest)
# "how do i answer tell me about yourself", "what do i say when they ask what are you doing at
# the moment": the question in the line is somebody else's - an interviewer's - and the person
# wants the answer to give them, not the bot's own. The words ask about the bot only as a
# quotation, so every about-the-bot kind stands down and the knowledge base answers the line.
# The frame needs an ask about answering (answer, say, reply, respond); "how do i get you to
# listen" and "what do you say to that" are not it.
ANSWERING_A_QUOTED_ASK = re.compile(
    r"\b(?:how\s+(?:do|should|would|can|might|to)\s*(?:i|you|we)?|how\s+to|"
    r"what\s+(?:do|should)\s*(?:i|you|we)?)\s*[^.?!]{0,20}?"
    r"\b(?:answer|say|reply|respond)\b[^.?!]{0,40}?"
    r"\b(?:what|who|where|why|how|when|tell\s+me|do\s+you|are\s+you|can\s+you|your)\b",
    re.IGNORECASE)


# "how long can we talk for", "is there a limit to how long we can talk", "have you got all
# day", "how many messages can i send you". How long this conversation can run, and whether the
# person is keeping the bot too long. Nothing about the bot is on the web to look up, so the
# search hedge answered the question with the wrong advice, and the message template answered
# "how many messages can i send you" with three lines to write to somebody else.
# Every shape below names this conversation - talk, chat, keep going, all day - or asks the bot
# for its time, so a question about the person's own time keeps its own answer: "how long can i
# keep it in the fridge", "how long have i got to send this form" and "how many messages should
# i send my landlord" are not this. Each shape is read on the whole line, never on one word.
WHILE_ASK = re.compile(
    r"\bhow\s+long\s+(?:can|could|may|might|will|would|do|does)\s+(?:we|i|you|u|this)\s+"
    # The verbs of talking, and only those: "how long can i last without food" and "how long will
    # this last" name a thing of their own and are nobody's question about the chat.
    r"(?:[a-z]+\s+){0,2}?(?:talk|chat|keep\s+(?:going|talking|chatting)|carry\s+on|go\s+on)\b"
    # The bot's own time, and only that: "how long have you got" is the ask, while "how long
    # have you got to pay the bill" is about the bill and keeps its own answer.
    r"|\bhow\s+long\s+(?:have|has|do|does|did)\s+(?:you|u)\s+(?:got|have)\b"
    # "left" has to end the line: "how long have you got left" is the ask, while "how long have
    # you got left on the parking" is about the parking and keeps its own answer.
    # "for" has to be followed by the person or the moment, so "how long have you got for lunch
    # today" stays the lunch question it is.
    r"(?=\s*(?:$|[.!?]|for\s+(?:you|me|us|now|today)\b|on\s+you\b|today\b|now\b|then\b"
    r"|and\b|so\b|to\s+(?:talk|chat|keep\s+going|carry\s+on|go\s+on)\b)"
    r"|\s+left\s*[.!?]?$)"
    r"|\bhow\s+long\s+(?:are|will)\s+(?:you|u)\s+(?:be\s+)?(?:here|around|on)\b"
    r"|\bhave\s+(?:you|u)\s+got\s+(?:all\s+day|time|much\s+time)\b"
    # "we", not "i": "should i keep going" is the person's own activity - a run, a course, a row
    # - and "do you mind if i keep going" is said to the bot about the conversation.
    r"|\b(?:can|could|shall|should|may)\s+we\s+keep\s+(?:talking|going|chatting|on)\b"
    r"|\bdo\s+(?:you|u)\s+mind\s+if\s+i\s+(?:keep|carry|ramble)\b"
    r"|\bhow\s+much\s+time\s+(?:have|has|do)\s+(?:you|u|we)\s+(?:got|have)\b"
    r"|\bhow\s+many\s+(?:messages?|questions?|things)\s+can\s+i\s+(?:send|ask|give)\b"
    r"|\blimit\s+(?:on|to)\s+how\s+long\b[\s\S]{0,24}?\b(?:talk|chat|go\s+on|carry\s+on|"
    r"keep\s+going)\b")


# "am i boring you", "am i keeping you up", "do you want me to stop", "am i talking too much",
# "am i rambling", "do you mind me going on". The person is checking whether they are being a
# nuisance, which is a question about this conversation and only the bot can answer it. The
# search hedge answered eleven of these ("a quick search online will get you a solid answer"),
# the identity card answered "are you bored of me", and "am i boring you" was told to try a
# jigsaw - none of them answers the question somebody asked. Every shape here has the person or
# the talk as its subject and is in the present tense, so a line about a thing being dull ("the
# film was boring", "my job is boring") is not this.
KEEPING_ASK = re.compile(
    r"\bam i\s+(?:boring\s+(?:you|u)\b|keeping\s+(?:you|u)\b|a\s+bore\b|boring\b"
    r"|(?:talking|talk|going\s+on|rambling|wittering|waffling|droning)\s+too\s+much\b"
    # "going on" has to be the end of the line, or carry a qualifier of its own: "am i going on a
    # diet", "am i going on holiday" and "am i going on the bus" are plans, not the talk.
    r"|going\s+on(?:\s+(?:a\s+bit|and\s+on|too\s+long|like\s+this))?(?:\s*[.!?]\s*$|\s*$)"
    r"|rambling\b|wittering\b"
    r"|waffling\b|droning\s+on\b|wasting\s+(?:your|ur)\s+time\b)"
    r"|\bis\s+(?:this|it)\s+(?:boring\s+(?:you|u)\b|boring\b|dull\b|too\s+much\s+detail\b"
    r"|going\s+on\s+a\s+bit\b)"
    r"|\bdo i\s+(?:talk|go\s+on|ramble|witter|waffle)\s+too\s+much\b"
    r"|\bare (?:you|u)\s+(?:bored\s+(?:of|with)\s+(?:me|us|this|it)\b"
    r"|sick\s+of\s+me\b|fed\s+up\s+(?:of|with)\s+me\b|had\s+enough\s+of\s+me\b)"
    r"|\bdo you\s+mind\s+(?:me|my)\s+(?:going\s+on|talking|rambling|wittering)\b"
    r"|\b(?:am i|are we|was i)\s+wasting\s+(?:your|ur)\s+time\b")


# "do you want me to stop", "shall i go": the same question as above, but only when the stop is
# the whole of the line. "where should i go", "how often should i go", "should i stop for a bit"
# and "the oil light came on while i was driving, should i stop" are about the person's evening,
# their gym or their car, and "shall i stop taking the tablets" has a card of its own - every one
# of them would be answered "Not at all, carry on" by a search on the words alone.
STOP_ASK = re.compile(
    r"(?:(?:do|would)\s+(?:you|u)\s+want\s+me\s+to"
    r"|(?:do|would)\s+(?:you|u)\s+like\s+me\s+to"
    r"|(?:shall|should)\s+i"
    r"|(?:can|could)\s+i)\s+"
    r"(?:stop|quit|shut\s+up|leave\s+it)(?:\s+(?:now|then|talking|chatting|going\s+on))?"
    # A bare "go" is a plan - "should i go", "shall i go home", "should i go to the doctor" - so
    # it only counts when the bot is the one being left: "do you want me to go".
    r"|(?:do|would)\s+(?:you|u)\s+(?:want|like)\s+me\s+to\s+go(?:\s+now)?")
STOP_ASK_FILLER = frozenset("""so and but ok okay well now then sorry hmm erm um oh ah hey hi
right alright just also btw honestly""".split())


def a_stop_ask(line):
    """True when the whole line asks whether the person should stop or go."""
    words = [word for word in str(line or "").lower().replace(",", " ").split()
             if word not in ("", " ")]
    while words and words[0].strip(".,!?") in STOP_ASK_FILLER:
        words.pop(0)
    return bool(STOP_ASK.fullmatch(" ".join(words).strip(" .!?")))


def _about_bot_kind(text, words, norm=()):
    """Which kind of about-the-bot question this is, or None.

    "memory" asks what the bot remembers, "help" what it can do, and "identity" what it is;
    "warmth" asks what it makes of the person, which is the one ask about the bot that is about
    both of them. The reply modules pick the phrasing from this, so each kind is read on the
    words that actually ask it and nothing else is pulled in.
    """
    bare = " " + text.strip() + " "
    # `text` is the line with its clauses marked ("how long | can we talk for"), so the whole
    # sentence is read from it with the marks taken out: a shape split across two clauses ("is
    # there a limit to how long | we can talk") is one question.
    flat = (text or "").replace(" | ", " ").replace("|", " ")
    if WHILE_ASK.search(flat):
        # Before the memory branch, which answers "how long have you got" with the line about
        # keeping only this conversation - a question about the bot's memory put to somebody
        # asking about its time.
        return "while"
    if KEEPING_ASK.search(flat) or a_stop_ask(flat):
        return "keeping"
    if _asks_where_the_bot_is(norm):
        return "where"
    if _asks_who_this_is(norm):
        return "identity"
    if ANSWERING_A_QUOTED_ASK.search(text or "") and not _self_ask(norm):
        return None
    if _asks_how_the_bot_sees_me(norm):
        return "warmth"
    if "remember" in words and {"you", "your"} & words:
        return "memory"
    if _capability_question(list(norm)):
        return "help"
    if _asks_if_the_bot_is_a_product(norm):
        return "model"
    if _recalls_their_own_line(norm):
        # "what did i just tell you" is the person asking for their own line back: the "you" is
        # who they told it to and the verb is theirs. Read as a self-ask it was answered with the
        # line that says what the bot is ("I'm a chatbot - here to help and chat"), which says
        # nothing to somebody asking what they had just said, and the store's recall never ran.
        return None
    if _asks_what_is_new_with_the_bot(norm):
        # "what's new with you", "anything new with you", "what's been happening with you": the
        # bot's own side of the chat in the words that name "new" rather than a verb of doing.
        return "doings"
    if _asks_what_the_bot_has_been_doing(norm):
        # "what did you do at the weekend", "where were you last night": the bot's own past,
        # which it answers plainly rather than with the search hedge or a recap of the person's
        # line. Read before the generic self-ask, which caught "what did you get up to". The
        # manners question with no past in it ("what are you up to", "wuu2") keeps its own
        # reading and its own answer.
        return "doings"
    if _asks_whether_the_bot_is_about(norm):
        return "doings"
    if _asks_how_it_spends_its_time(norm):
        # "how do you spend your time", "what do you do with your day": the same ask as "what are
        # you up to" with the verb named. Read as an ordinary question it reached the search hedge
        # ("I don't know enough to answer that honestly"), which is no answer to a friendly
        # question about the bot's own day.
        return "doings"
    if (_asks_what_the_bot_is_doing(norm) and {"you", "u", "ya"} & words
            and words & ASKS_IF_ANYTHING):
        # "you doing anything tonight", "u up to anything this weekend", "are you up to much":
        # the same ask as "what are you up to", said from the front and with the time still to
        # come, so the past-ask reader stands aside and the manners opener is not there to catch
        # it. Read as smalltalk the evening card claimed it ("Give the evening a shape") on a
        # line that asked about the bot's evening, not the person's. The `you` has to be in the
        # line: "doing anything tonight" is the person's own evening and stays where it is.
        return "doings"
    if _asks_about_its_experience(norm):
        # "have you ever been to paris": the bot's own past, asked as an experience rather than
        # as a stretch of time. Same pool with a pool of its own for the "never" answer.
        return "doings"
    if _self_ask(norm):
        return "memory" if {"remember", "recall", "forget"} & words else "identity"
    if _how_long_itself(norm) or _when_itself(norm):
        # "how long have you been going" is a question about the bot's own history, and there is
        # only ever one answer to it: nothing came before this chat. The pool that says that is
        # the memory one, so the kind is "memory" rather than a word of its own - the composer
        # would otherwise answer a question about time with its line about having no address.
        return "memory"
    if _counts_its_own_doings(norm):
        # A tally of the bot's own chats or days: there is no such number to give, and the
        # memory answer is the honest one, so it is read the same way as "what do you remember".
        return "memory"
    if A_YOUR_KIN.search(" ".join(norm)) or A_YOUR_OWN_THING.search(" ".join(norm)):
        return "life"
    if (A_HOW_MANY_OF_THE_BOTS_OWN.search(" ".join(norm))
            and set(norm) & BOT_LIFE):
        return "life"
    if A_WHAT_ITS_LIKE.search(" ".join(norm)):
        return "identity"
    if _asks_about_its_own_life(norm):
        return "life"
    if _has_any(bare, ABOUT_BOT) or text.strip().endswith(ABOUT_BOT_END):
        return "identity"
    if {"you", "your"} & words and words & ROBOT_WORDS and "are" in words:
        return "identity"
    return None


# A word of mood or condition. "low" is a state when a person has it; it is a setting, a
# battery, or a shelf when a thing has it. `state_owner` says whose it is, so that a reply
# module consoles a person who is low and not a person who is asking about low heat.
STATE_WORDS = frozenset("""
low down rough tough hard heavy flat empty rubbish crap awful terrible horrible grim bad good
fine better worse ok okay upset sad miserable unhappy disappointed gutted stressed anxious
worried nervous scared frightened angry annoyed furious irritated frustrated bored tired
exhausted knackered shattered drained wiped sleepy swamped overwhelmed snowed fed unwell
poorly sick ill
mad cross fuming livid seething raging irate miffed peeved riled
""".split())
# The state belongs to the person when the thing it sits on is the person's own body, day or
# mood: "a rough day", "my back is sore", "a bad week at work".
PERSON_NOUNS = frozenset("""
day days week weeks month months year years night nights morning mornings evening weekend
term shift shifts sleep time times life mood work job school college uni class classes exam
exams test deadline presentation interview head back leg legs arm arms hand hands shoulder
shoulders knee knees foot feet ankle ankles neck chest stomach tummy hip hips throat eye eyes
ear ears tooth teeth skin hair voice nerves body health
""".split())
# Anybody a person can be low about is worth a kind word, so their state counts as the line's.
OTHER_PEOPLE = frozenset("""
he she they him her them his hers their mum mom dad mother father son daughter kid kids baby
babies toddler toddlers child children infant newborn boy boys girl girls teenager teen lad
partner husband wife boyfriend girlfriend friend friends brother sister family colleague boss
neighbour neighbor uncle aunt cousin gran grandma grandad grandpa nan nana mate mates
dog dogs puppy pup cat cats kitten doggy hamster rabbit rabbits guinea budgie parrot pet pets
""".split())
# A feeling can be a noun too, and then it is the person's own: "my anxiety is bad today". A
# head, a brain or a mind is the person's too, and not a thing that happens to be near them:
# "my brain is fried" is how they are, while "my back is sore" is still the back.
MOOD_NOUNS = frozenset("""anxiety stress worry worries nerves mood depression grief sadness
anger panic fear energy confidence motivation appetite sleep loneliness doubt
head brain mind memory concentration focus""".split())
PERSON_SUBJECT = frozenset("i im me us we myself ourselves nobody nothing everything things".split())
# Words skipped when looking back for the subject of a state word: auxiliaries, adverbs and
# determiners all sit between the subject and its state ("i have been really fed up").
BEFORE_STATE = frozenset("""
am is are was were be been being have has had having do does did feel feels feeling felt get
gets getting got seem seems seemed look looks looked sound sounds sounded taste tastes tasted
a an the so very really quite pretty too bit little lot kind kinda touch just still always again now
 today honestly totally all as than and but then of at with about over on in for from by my your
our their his its am i am not no never still even both either
will would shall should can could may might must wont cant cannot couldnt shouldnt wouldnt
ok okay right well cool sure yeah yep yes alright oh ah hmm hey hi so
""".split()) - {"i"}
# Words that end a state word's reach forward: "tired of work" is still the person who is tired.
PERSON_PREPOSITIONS = frozenset("of with about in at on".split())
# A word that starts a new clause: what follows it is not the noun this state belongs to
# ("pretty low since i moved here").
CONJUNCTIONS = frozenset("since because when while until though although if after before "
                         "whenever and but or yet".split())
BETWEEN_STATE_AND_NOUN = frozenset("""
a an the bit little lot of kind kinda up down out off on at with about over in for from by my
your our their his its so very really quite pretty too just still always again now today
honestly totally all as than
""".split())

# A word after the state that says when, not what: "i have been low all week", "feeling down
# lately". Without this the last word of such a line was read as the thing the state belongs to.
TIME_FILLERS = frozenset("""
morning afternoon evening night tonight noon midnight week weekend month year lately recently
afterwards afterward yesterday tomorrow nowadays midweek
""".split())

# What people put after a feeling to soften it. It says how they say it, not what they feel, so
# it is not the thing the feeling is about: "bit tired to be fair" and "bit rough to be honest"
# were read as a *thing* that is tired, because a word after the state word was taken for the
# noun it belongs to - and a reply that only consoles the person then consoled nobody.
MOOD_TAIL = ("to be honest", "if i am honest", "if im honest", "to be fair", "to tell the truth",
             "to be truthful", "to be blunt", "if anything", "i must say", "i suppose", "i guess")
MOOD_TAIL_WORDS = frozenset("tbh tbf ngl honestly though tho".split())
# The phrase is only filler when the clause still stands without it. "im not going to be honest"
# is about being honest, and the verb in front of the phrase is what says so.
MOOD_TAIL_TAKEN = frozenset("""going go goes went want wants wanted need needs needed try tries
    trying tried mean means meant promise promised learn learned learnt used rather hope hoping
    hate hates love loves have has had like likes prefer plan planning""".split())


def _without_mood_tail(clause):
    """The clause as it reads without the words people soften a feeling with on the end."""
    words = list(clause)
    changed = True
    while changed and words:
        changed = False
        if words[-1] in MOOD_TAIL_WORDS:
            words.pop()
            changed = True
            continue
        for phrase in MOOD_TAIL:
            size = len(phrase.split())
            if size >= len(words) or words[-size:] != phrase.split():
                continue
            if words[-size - 1] in MOOD_TAIL_TAKEN:
                continue          # "not going to be honest" is about being honest
            del words[-size:]
            changed = True
            break
    return words


def _last_subject_pos(words):
    """Where the last word of a clause that could be the thing its state is about sits."""
    for pos in range(len(words) - 1, -1, -1):
        word = words[pos]
        if word in BEFORE_STATE:
            continue
        if len(word) > 4 and (word.endswith("ly") or word.endswith("ing")):
            continue               # "actually doing fine": an adverb or a verb, not a subject
        if word.replace(".", "").isdigit() or word in NUMBER_WORDS:
            continue               # "my mum is 78 and not very good": a number is no subject
        return pos
    return None


def _last_subject(words):
    """The last word of a clause that could be the thing its state is about."""
    pos = _last_subject_pos(words)
    return None if pos is None else words[pos]


# "down" and "up" are as often a direction as a mood: "cant keep anything down", "turn the
# heat down". They carry a state only when a copula or a feeling verb comes first
# ("i am a bit down", "feeling down today").
PARTICLE_STATES = frozenset("down up out off in on".split())
# "ill" is a state only where a copula or a feeling verb makes it one: "she is ill" yes,
# "ill try that, thanks" is "I will", so a bare "ill" without one says nothing.
COPULA_STATES = frozenset("ill".split())
# Words that are a mood as well as an everyday noun: "a new flat" is a home, "i feel flat" is not.
NOUN_STATES = frozenset("flat".split())
# A state word followed by one of these and a thing is a shortage of the thing, not a mood:
# "im low on milk", "we are low on petrol", "im low in iron". The person who has run out of
# milk is not having a low day, so a supply takes the state off the person.
SUPPLY_WORDS = frozenset("low short".split())
SUPPLY_PREPOSITIONS = frozenset("on in of".split())
# The things a person can be low on and still be saying how they are: "im low on energy" is
# tiredness and "im low on confidence" is nerves, so a shortage of one of these is the mood and
# not a fact about the cupboard. Everything else that runs out (milk, petrol, tablets) is a
# supply, and a condolence for it is the wrong reply.
OWN_RESERVES = frozenset("""energy patience confidence motivation enthusiasm inspiration hope
    sleep focus concentration attention steam willpower batteries charge ideas""".split())
DEGREE = frozenset("""bit little lot kind sort very really so too pretty quite more most less
as enough""".split())
DETERMINERS = frozenset("the a an my your our their his her its this that these those it them".split())

# A state word that is also a particle ("down", "up", "off") is the way somewhere just as often
# as the way somebody is, and `cue_about_person` counts a particle whenever a preposition follows
# it, so "im going down the pub" was read as a low and answered with "Sorry to hear that. A walk
# and someone to talk to usually help more than sitting with it." The words of going are what say
# it is a place, and so is an article and a noun that is not a time - "down the shop", "down the
# road", "up the stairs" - while "down this week" and "down the whole week" keep their feeling.
MOTION_WORDS = frozenset("""go goes going went gone walk walks walking walked wander wandering
    head heads heading headed run runs running ran drive drives driving drove ride rides riding
    rode cycle cycles cycling cycled pop pops popping popped come comes coming came hurry hurries
    hurrying stumble stumbling jog jogs jogging climb climbing jump jumping fall falls falling
    fell race racing rush rushing dash dashing nip nipping shuffle shuffling off""".split())
# The nouns that make an article and a noun a length of time rather than a place: "im down the
# whole week" is a mood, and the adjective in front of the noun is why the noun is looked for
# rather than the next word.
TIME_AFTER_A_PARTICLE = frozenset("""week weeks month months year years morning mornings
    afternoon evenings evening night nights weekend weekends time times term terms day days
    while bit moment minute minutes hour hours""".split())


def _particle_is_a_place(words, pos):
    """True when the particle at `pos` is a place or a movement, not how somebody is.

    "im going down the pub", "im off down the road", "walking up the hill", "down the stairs": a
    word of going in front of it, or an article and a noun that is not a length of time behind
    it. "im down the pub" is the same line with the going left out.
    """
    if pos and words[pos - 1] in MOTION_WORDS:
        return True
    if len(words) - pos < 2 or words[pos + 1] not in DETERMINERS:
        return False
    return not any(word in TIME_AFTER_A_PARTICLE for word in words[pos + 2:pos + 5])


def _a_direction(text, at):
    """True when the particle at the character offset `at` is a place, not a feeling."""
    words = [word.strip(".,!?;:-|\"'") for word in text.lower().split()]
    pos = len(text[:at].lower().split())
    return pos < len(words) and _particle_is_a_place(words, pos)

MANIPULATE = frozenset("""turn turns turned turning keep keeps kept keeping put puts putting set
sets setting hold holds holding let lets letting shut shuts shutting slow slows slowing calm
calms calming take takes taking bring brings bringing""".split())
COPULA = frozenset("""am is are was were be been being feel feels feeling felt get gets getting
got seem seems look looks sound sounds still very really quite pretty so too bit little a""".split())


def _copula_before(words, pos):
    """True when the word before the state is a copula or a feeling verb, not a thing."""
    for word in reversed(words[:pos]):
        if word in COPULA:
            return True
        if word in BEFORE_STATE:
            continue
        return False
    return True            # nothing came before it here: the clause before carried the subject


def _noun_reading(words, pos):
    """True when the word here is a plain noun: "a new flat", "the flat"."""
    if pos and words[pos - 1] in DEGREE:
        return False
    return any(word in DETERMINERS for word in words[max(0, pos - 2):pos])


def _thing_turned_down(words, pos):
    """"turn the heat down", "shut it down": a verb, a thing, then a particle."""
    if pos < 2 or words[pos - 2] not in DETERMINERS:
        return False
    return pos == 2 or words[pos - 3] in MANIPULATE


NUMBER_WORDS = frozenset("one two three four five six seven eight nine ten eleven twelve".split())
# A named event is not an object: "the funeral was awful", "the exam went badly" are things that
# happened to the speaker, so the state word describes how it was for them, not the event.
EVENT_NOUNS = frozenset("""funeral christening wake christmas easter birthday wedding anniversary
exam exams interview scan operation surgery birth labour induction move housewarming holiday
holidays honeymoon funeral term semester deadline appraisal review probation""".split())


def _is_person(word):
    """True when the word can be the one who has a feeling: "i", "my mum", "my son"."""
    return (word in PERSON_SUBJECT or word in PERSON_NOUNS or word in MOOD_NOUNS
            or word in OTHER_PEOPLE or word in {"that", "this", "it"})


def _names_a_thing(words, at):
    """True when the word at `at` is a thing that was named: "the soup", "my phone battery"."""
    if words[at] in EVENT_NOUNS:
        return False               # "the funeral was awful": an event is the speaker's own
    return any(word in DETERMINERS for word in words[max(0, at - 3):at])


# The pronoun a relative clause opens with: the state after it belongs to the noun before it.
RELATIVE_SUBJECTS = frozenset(("that", "which", "who"))


def _names_somebody_else(words, at):
    """True when the words up to `at` name a person rather than a thing: "my 5 year old"."""
    return words[at] == "old" and "year" in words[max(0, at - 3):at]


def _whose_state(words, pos, head=None):
    """"self", "other" or "thing": whose state the word at `pos` is, as far as this clause says.

    `head` is where the state word starts when it is more than one word ("fed up"), so the
    subject is looked for before the whole state and the rest is read after it.
    """
    following = [word for word in words[pos + 1:]]
    subject_at = _last_subject_pos(words[:pos if head is None else head])
    if subject_at is not None and words[subject_at] in RELATIVE_SUBJECTS:
        # A relative clause is about the noun in front of it: "i have a houseplant that looks
        # sad" is about the houseplant, and "i have a lawn that looks sad" about the lawn. The
        # pronoun was read as the subject, it is not a person, and the state fell back to the
        # speaker - so the sad pool consoled someone about their lawn.
        earlier = _last_subject_pos(words[:subject_at])
        if earlier is not None:
            subject_at = earlier
    subject = None if subject_at is None else words[subject_at]
    if subject is not None and _copula_before(words, pos):
        # "i feel better today", "she is really down", "my dog has been sick": after a copula
        # or a feeling verb the state describes the subject, whatever loose words come after
        # it. Without this the unknown word at the end of the line made it a thing's state.
        if subject in OTHER_PEOPLE or _names_somebody_else(words, subject_at):
            return "other"
        if _is_person(subject):
            return "self"
        if _names_a_thing(words, subject_at):
            return "thing"         # "the soup tastes awful"
        return "self"              # "christmas will be hard": an event, hard for the speaker
    if following and following[0] in PERSON_PREPOSITIONS:
        if subject in OTHER_PEOPLE:
            return "other"     # "she is worried about the exam": her worry, not the speaker's
        if subject is not None and not _is_person(subject):
            return "thing"     # "the sun is low in the sky": a thing of the weather
        return "self"          # "tired of the noise", "worried about the exam"
    for word in following:
        if word in CONJUNCTIONS:
            break
        if word in BETWEEN_STATE_AND_NOUN or word in TIME_FILLERS:
            continue
        if word.endswith("ly") and len(word) > 4:
            continue            # "a bit down lately": an adverb, not the noun it belongs to
        if word in DETERMINERS:
            continue            # "down this road": the noun after it is the one that decides
        if word.endswith("ing") and len(word) > 4:
            return "self"       # "nervous speaking in front of people": a thing the person does
        if word in OTHER_PEOPLE:
            return "other"      # "my toddler is very sleepy": the child, not the person
        if word in PERSON_NOUNS or word in MOOD_NOUNS:
            return "self"
        return "thing"
    if subject is None:
        return "self"          # "feeling low today": no noun, so it is the person speaking
    if subject in OTHER_PEOPLE:
        return "other"      # "she is stressed about the exam", "my son is unwell"
    if subject in PERSON_SUBJECT or subject in PERSON_NOUNS:
        return "self"
    if subject in MOOD_NOUNS:
        return "self"
    if subject in {"that", "this", "it"}:
        return "self"          # "that sounds awful": the person is reacting to something
    if _names_a_thing(words, subject_at):
        return "thing"         # "the soup tastes awful", "my phone battery is low": a named thing
    return "self"              # "christmas will be hard": an event, and hard for the speaker


BE_FORMS = frozenset("am is are was were".split())
# A state can be carried over to somebody without the state word being said again: "my plant is
# sad and so am i", "my plant is sad, me too", "my plant looks sad and i am too". The words after
# the state word are the only thing that says whose the second state is.
ECHO_CARRIERS = frozenset("""so and but yet or then as well too also just same here yes
me i we us im m""".split())


def _echoed_state(words):
    """"self", "other" or None: whose state a tail after a state word carries over, if any.

    `words` is what follows the state word ("and so am i", "me too", "and the kids too"). A tail
    that names no person carries nothing: "so is the weather" is not somebody's state.
    """
    if not words or len(words) > 6:
        return None
    carried = ((words[0] == "so" and len(words) > 1 and words[1] in BE_FORMS)
               or words[-1:] == ["too"]
               or words[-2:] == ["as", "well"]
               or words[-1:] == ["also"]
               or words[:2] == ["same", "here"]
               # "and i am": the person and a be-verb with nothing after it
               or (len(words) == 2 and words[0] in PERSON_SUBJECT and words[1] in BE_FORMS))
    if not carried:
        return None
    if words[:2] in (["same", "here"], ["me", "too"], ["same", "same"]):
        return "self"                # "same here" and "me too" name the speaker on their own
    if any(word in PERSON_SUBJECT for word in words):
        return "self"                # "and so am i", "me too"
    if any(word in OTHER_PEOPLE for word in words):
        return "other"               # "and so are the kids", "and my mum too"
    return None


def _carried_over(words, state_at):
    """The owner an echo after the state word hands the same state to, or None.

    The echo sits in the same clause as the state word more often than not ("my plant is sad and
    so am i" is one clause), so it is read from the words after the state rather than from a
    clause of its own.
    """
    tail = words[state_at + 1:] if state_at is not None else words
    while tail and tail[0] in CONJUNCTIONS:
        tail = tail[1:]
    return _echoed_state(tail)


def _state_owner(clauses):
    """"self", "other", "thing" or None: whose state the line names, if it names one."""
    owner = None
    carried = None             # the subject of the clause before: "i am so low today"
    # "work is stressing me out", "the kids are tiring me out": the state is the speaker's,
    # even though the sentence's subject is the thing. Without this the mood pools stand down
    # because the line names a thing of its own, and the person gets "Got it. Is there anything
    # you'd like a hand with?" for a line that says how they are.
    if _works_on_the_speaker(" ".join(
            " ".join(str(word) for word in clause) if isinstance(clause, (list, tuple))
            else str(clause) for clause in clauses)):
        return "self"
    for clause in clauses:
        words = _without_mood_tail(clause)
        # A clause that says "so am i" or "me too" carries the state named before it over to
        # whoever it names, without repeating the state word.
        if owner is not None and not any(word in STATE_WORDS for word in words):
            echo = _echoed_state(words)
            if echo == "self":
                return "self"
            if echo:
                owner = echo
        state_at = None
        for pos, word in enumerate(words):
            if word not in STATE_WORDS:
                continue
            state_at = pos
            if word in NOUN_STATES and _noun_reading(words, pos):
                continue                 # "moved into a new flat" is a home, not a mood
            if word in PARTICLE_STATES:
                if _thing_turned_down(words, pos):
                    owner = "thing"          # "turn the heat down": a knob, not a mood
                    continue
                if not _copula_before(words, pos):
                    continue                 # "keep anything down" is no mood either
            if word in COPULA_STATES and (pos == 0 or not _copula_before(words, pos)):
                continue                     # "ill try that, thanks" is not being ill
            head = None
            if word == "fed":
                if "up" not in words[pos + 1:pos + 2]:
                    continue
                head, pos = pos, pos + 1   # "fed up" is one state; the rest follows "up"
            whose = _whose_state(words, pos, head)
            if whose is None and carried in PERSON_SUBJECT | PERSON_NOUNS:
                whose = "self"      # the subject of the clause before: "im low, work is hard"
            if whose == "self":
                return "self"       # the person's own state is the one worth answering
            if whose:
                owner = whose
        if owner is not None:
            echo = _carried_over(words, state_at)
            if echo == "self":
                return "self"      # "... and so am i": the person is in the state too
            if echo:
                owner = echo
        carried = _last_subject(words) or carried
    return owner


def _about_a_supply(text, end):
    """True when the state word ending at `end` is followed by "on/in/of" and a thing.

    "im low on milk", "we are low on petrol", "im low in iron": the state is a shortage of the
    thing, so it is not the person's mood. The person who has run out of milk is not having a
    low day, and neither is a car that is low on petrol.
    """
    rest = [word.strip(".,!?;:-|\"'").lower() for word in text[end:].split()]
    if len(rest) < 2 or rest[0] not in SUPPLY_PREPOSITIONS:
        return False
    thing = rest[1]
    return thing not in OTHER_PEOPLE and thing not in PERSON_NOUNS \
        and thing not in PERSON_SUBJECT


def shortage_of(text):
    """The thing the line says has run out, or None when nothing has.

    `_about_a_supply` already keeps a mood word off "im low on milk", but leaving the line with
    no mood in it is not enough: the composer's own feeling cue ("im low") matched anyway and
    the person who was out of milk got the condolence for a low day. Naming the thing here means
    every module reads a shortage of milk instead of a mood, once, for every turn.
    """
    words = [word.strip(".,!?;:-|\"'").lower() for word in text.split()]
    for at, word in enumerate(words):
        if word not in SUPPLY_WORDS or at + 2 >= len(words):
            continue
        if words[at + 1] not in SUPPLY_PREPOSITIONS:
            continue
        thing = words[at + 2]
        # A word that only points at the thing ("the sun is low in the sky", "low in the
        # morning") is not the thing: the supply is what it names, so nothing is named here.
        if thing in DETERMINERS or thing in OWN_RESERVES or thing in OTHER_PEOPLE:
            continue
        if thing in PERSON_NOUNS or thing in PERSON_SUBJECT:
            continue
        return thing
    # "ive run out of tea bags" names no state word at all, so no supply shape above finds it.
    out = re.search(r"\b(?:run|ran|running) out of ([a-z]+)", text)
    if out and out.group(1) not in OWN_RESERVES and out.group(1) not in DETERMINERS:
        return out.group(1)
    return None


# The things a question about the bot's own life is made of: what a person has and a program
# does not. "do you have kids", "have you got a pet", "what's your job", "do you get paid" all
# name one of these and nothing else, so the bot is the subject of the line. A question to the
# bot that names something of the world keeps its own topic: "do you have a recipe for soda
# bread", "do you have a dog lead i can borrow", "do you have any tips for kids parties" all
# carry a word outside this set.
BOT_LIFE = frozenset("""
family families kid kids child children son daughter mum mom mother father dad daddy parents
parent brother brothers sister sisters sibling siblings gran grans grandma grandmas grandad
grandads grandpa grandparents grandparent uncle uncles aunt aunts auntie aunties cousin cousins
niece nephews relatives relative partner husband wife girlfriend boyfriend friends friend
home house flat apartment town hometown address pets pet dog dogs cat cats kitten puppy hamster
rabbit budgie garden
job jobs work boss manager managers employer colleague colleagues coworker coworkers wages wage
salary paycheck pay paid money bank account mortgage bills rent
body face hands feet hair
birthday age born
name nickname
car cars
""".split())
# The words an ask about the bot's own life is carried by: the ask itself, articles and the few
# everyday words that say nothing about the world. Nothing that could name a subject is here,
# so "do you have a dog lead" and "how's your day" keep their own reading.
BOT_LIFE_FILLER = frozenset("""
a an any some the your you u ur yourself yours own much many really actually ever then now
yet already also too about of for at in on like and or there both coming come came best
""".split())
# The shapes the ask takes. A line has to be one of these and be made of the words above, so a
# question that turns the same words on the world ("do you have a dog that bites") is not read
# as a question about the bot.
BOT_LIFE_ASK = re.compile(r"""
    (?: (?:do|does|did)\s+(?:you|u|ya)\s+(?:have|has|got|get|own|need|want)
      | (?:have|has)\s+(?:you|u|ya)\s+got
      | (?:what|whats|what's|who|whos|who's|whose|which|how)\s+
        (?:is|are|was|were|s|does|do)?\s*(?:your|ur)
      | (?:are|is|was|were)\s+(?:you|u)\s+(?:a|an)
      # "were your mum and dad there", "was your brother there too", "are your parents
      # coming": the thing asked about is the bot's own family, said from the front with no
      # "do you have" in it. Read as an ordinary question it reached the search hedge - "I
      # don't know enough to answer that honestly" to somebody asking whether the bot's mum
      # was at a party - when the bot knows the answer perfectly well: no family at all. The
      # rest-gate below still has to pass, so "is your shop open" and "were your prices
      # online" name something outside the bot's own life and are left alone.
      | (?:are|is|was|were)\s+(?:your|ur)
    )\s*
""", re.VERBOSE)


# "How long have you been going", "how long have you been around", "since when have you been
# here", "how long have you been talking to people": the subject is the bot and the span asked
# about is its own life, which it can answer (nothing before this chat, nothing after it). Read
# as an ordinary "how long" the line was a maths reading, so the savings entry answered "how long
# have you been talking to people" with a line about a queue at the kettle, and "how long have
# you been around" got the search hedge. Only the words a life like that is described with may
# follow the ask, so "how long have you been cooking that stew" and "how long have you been a
# teacher" keep whatever they were.
ITSELF_LONG = re.compile(r"""
    ^\s*(?:so\s+|ok\s+|okay\s+|ah\s+|oh\s+|and\s+|but\s+)*
    (?: how\s+(?:long|many\s+years)
      | how\s+old
      | since\s+when
    )
    \s+(?:have|has|did)\s+(?:you|u|ya)\s+(?:been|be|start|started|go|going|got|get)
    \b
""", re.VERBOSE)
# What can follow the ask when the bot's own life is what was asked about. A real subject on the
# end ("cooking that stew", "a teacher", "the book club") is outside this list and keeps its
# reading, because the person is asking how long the bot has been doing a thing of the world.
ITSELF_LIFE = frozenset("""
going around round about here there online alive running working doing this that it stuff
things talking chatting answering people folks folk to with us in on at now
""".split())


def _how_long_itself(norm):
    """True when the line asks how long the bot itself has been going.

    "how long have you been going", "how long have you been around", "how long have you been
    talking to people": the answer is the bot's own and there is nothing in the world to measure
    or look up, so the line is about the bot. A word of the world after the ask ("how long have
    you been cooking that stew") leaves the line to the topic it names.
    """
    said = " ".join(norm)
    match = ITSELF_LONG.match(said)
    if not match:
        return False
    return not set(said[match.end():].split()) - ITSELF_LIFE


# "When did you start", "when were you built", "how long ago did you start": the same question
# about the bot's own beginning, said the other way round. Read as an ordinary "when" it was the
# search hedge - "that's beyond what I know well, sorry" - which is the one answer a question
# about itself must not get. The tail is the same fence as the "how long" ask, and a shorter one:
# "when did you start running" is a person asking about exercise, so none of the doing words
# count on their own here.
ITSELF_WHEN = re.compile(r"""
    ^\s*(?:so\s+|ok\s+|okay\s+|ah\s+|oh\s+|and\s+|but\s+)*
    (?: when\s+did\s+you\s+(?:start|begin|first\s+start)
      | when\s+were\s+you\s+(?:made|built|started|made\s+up)
      | how\s+long\s+ago\s+did\s+you\s+(?:start|begin)
    )
    \b
""", re.VERBOSE)
# What may follow the "when" ask. Nothing at all is the commonest, and these are the words the
# bot's own life is said with and nothing else: a thing of the world after the ask ("running",
# "your job", "the diet") is outside the list and keeps its reading.
ITSELF_WHEN_TAIL = frozenset("""
going out this that it stuff then today now here online working answering helping
""".split())


def _when_itself(norm):
    """True when the line asks when the bot itself started.

    "when did you start", "when were you built", "how long ago did you start": the answer is the
    bot's own (nothing came before this chat), so the line is about the bot and the knowledge
    base has nothing to look up.
    """
    said = " ".join(norm)
    match = ITSELF_WHEN.match(said)
    if not match:
        return False
    return not set(said[match.end():].split()) - ITSELF_WHEN_TAIL


# The bot's own doings, in the words people use to ask the size of them: "how many people
# have you talked to", "how many questions do people ask you", "how many conversations have
# you had". A count of one of these is a question about what the bot does, not a sum to work
# out, so it is read as a question about the bot and the maths entry never sees it.
BOT_DOINGS = frozenset("""
talk talked talking speaks spoke spoken speaking chat chatted chatting answer answered
answering ask asked asking help helped helping heard listening sent send messages messaged
met meet meets
""".split())
# What a count of the bot's doings is a count of. "people" and "questions" are in it because
# the doing beside them is the bot's: "how many people have you talked to" counts the bot's
# chats, and "how many questions do people ask you" counts the bot's day. A count of a thing
# of the world ("how many eggs have you got", "how many people are coming to dinner") is none
# of this and keeps its reading.
BOT_COUNTED = frozenset("""
people person persons conversation conversations chat chats message messages question questions
folk folks
""".split())
COUNT_OPENERS = frozenset("so and but then also".split())
# Who the doing is done by, when it is not the bot itself. "how many questions do people ask
# you" counts the bot's day because "people" is nobody in particular; "how many questions does
# the doctor ask you" is the doctor's count, and the person is the one being asked, so it is not
# a question about the bot at all. The list is closed on purpose: a doer it does not hold is a
# third party the line named, and that line keeps its own reading.
# "have" is only a doing when what is counted is the chat itself: "how many conversations did
# you have today" is the bot's day, while "how many people have you got coming" is the person's
# dinner, and "how many eggs have you got" is the fridge. So the plain "have" needs the count to
# be a chat before it counts as something the bot did.
BOT_HAVE = frozenset("have has had having".split())
BOT_CHATS = frozenset("""
chat chats conversation conversations talk talks discussion discussions catch-up
""".split())


BOT_DOERS = frozenset("""
you u ya yourself people person folk folks anyone anybody somebody someone everybody everyone
they customers users guests strangers visitors readers
""".split())
# Words that can stand between the doer and its doing: "have you actually talked to", "did you
# ever chat". A word outside this set is the doer.
COUNT_FILLERS = frozenset("""
have has had having do does did done been being be is are was were ever already just really
also still not never once yet actually even only so far before since
""".split())


def _counts_its_own_doings(norm):
    """True when the line counts something of the bot's own life rather than working a sum out.

    "how many people have you talked to" is a question about the bot, and read as a number it
    reached the maths entry and answered a stranger with a porridge recipe. The line has to
    open on "how many/much", count a thing the bot's doings happen to (people, conversations,
    questions), say "you", and name one of those doings.
    """
    words = list(norm)
    at = 0
    while at < len(words) and words[at] in COUNT_OPENERS:
        at += 1
    if words[at:at + 2] not in (["how", "many"], ["how", "much"]):
        return False
    rest = words[at + 2:]
    if not set(rest) & BOT_COUNTED or not {"you", "u", "ya", "your", "ur"} & set(rest):
        return False
    # "had" is the doing in "how many conversations have you had": the count is the bot's day.
    # The first doing is not always the one with a doer ("messages" is a doing in "how many
    # messages have you sent"), so every doing in the line is asked about its doer.
    return any(_the_doer_is_the_bot(rest, i) for i, w in enumerate(rest)
               if w in BOT_DOINGS or w in BOT_HAVE and _a_count_of_chats(rest))


def _a_count_of_chats(rest):
    """True when what the line counts is the chat itself ("how many chats did you have today")."""
    return bool(set(rest) & BOT_CHATS)


def _the_doer_is_the_bot(rest, doing):
    """Whether the doing at `doing` is the bot's own, or nobody-in-particular's.

    "how many people have you talked to" is the bot talking, and "how many questions do people
    ask you" is the bot being asked: both count the bot's day. "how many questions does the
    doctor ask you" is the doctor asking, and the only person it is about is the one typing, so
    the memory answer would be a reply to a question nobody asked. Walking back over the
    auxiliaries and the adverbs lands on the doer, and the doer has to be the bot or a word that
    names nobody in particular.
    """
    at = doing - 1
    while at >= 0 and (rest[at] in COUNT_FILLERS or rest[at].endswith("ly")):
        at -= 1
    return at >= 0 and rest[at] in BOT_DOERS


def _asks_about_its_experience(norm):
    """True for "have you ever ..." put to the bot about a life it has not had.

    "have you ever had a day like that", "have you ever been in love", "were you ever ill": the
    thing asked about is the bot's own experience, and a program has none, so the honest answer
    is that nothing like that has happened to it. All three went to the search hedge, which asked
    the person to go and look it up as though they had asked about the world.

    What keeps this from taking turns it should not answer is the vocabulary, the same way the
    other asks about the bot's life are held: every word after the ask has to be a word of a life
    (been, had, felt, ill, love, a day) or a word that says nothing on its own. A line that names
    a thing of the world is a question about that thing and keeps its own answer - "have you ever
    eaten a jacket potato" is the potato recipe, "have you ever seen a double yolk egg" is the egg
    card, "have you ever heard of truffle oil" is a knowledge ask. A problem of theirs in the same
    breath is theirs too ("have you ever seen my boiler do this").
    """
    words = list(norm)
    if not words:
        return False
    said = " ".join(words)
    match = EXPERIENCE_ASK.match(said)
    if not match:
        return False
    rest = said[match.end():].split()
    if not rest:
        return False
    if set(rest) & THEIR_PROBLEM:
        return False
    return all(word in EXPERIENCE_WORDS or word in BOT_LIFE or word in BOT_LIFE_FILLER
               for word in rest)


# "Have you ever ..." put to the bot. The past tense only: "do you ever get tired" asks how the
# bot is now, which has its own reading and its own answer. The courtesy in front of the ask is
# allowed, and so is a leading conjunction, because people keep talking in one breath. Nothing
# that says what the line is about is allowed in front of the ask: "my nan asked have you ever
# been to spain" is a line about the nan.
EXPERIENCE_ASK = re.compile(r"""^(?:(?:and|so|but|oh|well|ok|okay|right|hey|hi|yeah|actually|
honestly|just)\s+)*(?:have|has|did|were|was)\s+(?:you|u|ya)\s+(?:ever|once)\b""",
    re.VERBOSE)
# The words a life is described with: what was done and how it felt. Nothing here names a thing
# the bot could be asked about, so a line made of these is about the bot itself.
EXPERIENCE_WORDS = frozenset("""
been be being was were had have got get went gone go going done do did seen see saw felt feel
tried try made make met meet ate eaten eat drank drunk smoked ridden rode driven drove worn wore
lived live cry cried laugh laughed hurt love loved hate hated kiss kissed miss missed win won lose
lost give gave given giving keep kept run ran swim swam cook cooked
up down through ill sick unwell happy sad tired lonely scared frightened angry upset worried
glad proud bored excited drunk lost
day days night nights week weeks month months year years time times life lived world holiday
holidays
thing things something anything nothing one ones kind sort bit lot lots
it them that this these those there before once ever really actually
myself yourself
""".split())
# A problem of theirs in the hand: the line is about the thing, and the module that knows the
# thing answers it. A "like that" after the ask is not this country - "have you ever had a day
# like that" is small talk about the day, not a fault.
THEIR_PROBLEM = frozenset("""
my our me us mine ours happen happens happened occurring seems broken broke leaking dripping noisy
""".split())


# "what's it like being you" asks what it is like to be the bot - no day, no dinner, no family -
# and the honest answer is the one that says what the bot is. Read as an ordinary question it
# reached the search hedge, which is no answer at all to a question about itself.
# The words that make "your" a question about the bot's family rather than about a thing: "were
# your parents there", "were your parents at the wedding", "are your gran and grandad coming". The
# all-words gate in `_asks_about_its_own_life` cannot carry these, because the wedding and the
# hospital name the world and would take the line out of the bot's own vocabulary - while the
# answer is the same one either way, that there is no family to have been anywhere. A kin word
# straight after "your" is enough on its own; "was your car in the garage" is not kin and keeps
# the gate.
KIN = frozenset("""family families kid kids child children son daughter mum mom mother father dad
    daddy parents parent brother brothers sister sisters sibling siblings gran grans grandma
    grandmas grandad grandads grandpa grandparents grandparent uncle uncles aunt aunts auntie
    aunties cousin cousins niece nephews relatives relative partner husband wife girlfriend
    boyfriend""".split())
# The same ask with an auxiliary or a follow-up in front of it: "do your parents live near you"
# (the ask is a life of its own, not "were your parents there"), "what about your sisters", "and
# your brother". The kin word still has to be the word straight after "your", so "do your prices
# include vat", "did your delivery arrive" and "and your car insurance" keep their own reading.
A_YOUR_KIN = re.compile(
    r"\b(?:"
    r"(?:was|were|are|is)\s+(?:your|ur|yours)\s+(?:" + "|".join(sorted(KIN)) + r")"
    r"|(?:do|does|did|have|has)\s+(?:your|ur)\s+(?:" + "|".join(sorted(KIN)) + r")"
    r")\b")
# "what about your job", "how about your dog", "and your bills": the ask about the bot's own life
# said as a follow-up, with no verb at all. Every word a life like that is described with counts
# here (not only kin), because the thing named is the bot's own - there is no job, no dog and no
# bill on this side - and the answer is the same one. It has to be "your" straight after the
# follow-up, so "what about your interview" and "how about your neighbour's dog" keep theirs.
A_YOUR_OWN_THING = re.compile(
    r"\b(?:(?:what|how)\s+about|and)\s+(?:your|ur)\s+(?:"
    + "|".join(sorted(BOT_LIFE)) + r")(?:\s+(?:too|then|either|as\s+well))?\s*[?.!]*$")

# "how many brothers have you got", "how many kids do you have": the same ask about the bot's own
# life with a count in front of it. The shape in BOT_LIFE_ASK has the person word after the verb,
# so a count in front ("how many brothers have you got") matches nothing and the line reached the
# search hedge - a search cannot say how many brothers the bot has, and the answer is none.
A_HOW_MANY_OF_THE_BOTS_OWN = re.compile(
    r"\b(?:how|what)\s+many\s+\w+(?:\s+\w+)?\s+(?:have|has|do|does)\s+(?:you|u|ya)\b")

A_WHAT_ITS_LIKE = re.compile(r"\b(?:what|whats|what's)\b.*\blike\s+being\s+(?:you|u|ya)\b")


def _asks_about_its_own_life(norm):
    """True when the line asks about the bot's own life and names nothing of the world.

    "do you have kids", "have you got a pet", "what's your job", "do you get paid": the subject
    is the bot and the thing asked about is one a program does not have, so there is nothing in
    the world to look up and a search hedge is no answer. Every word has to be a thing of that
    kind, so a line that names anything else is left alone.
    """
    words = list(norm)
    if not words or not {"you", "u", "ya", "your", "ur", "yours", "yourself"} & set(words):
        return False
    match = BOT_LIFE_ASK.match(" ".join(words))
    if not match:
        return False
    rest = " ".join(words)[match.end():].split()
    if not rest or set(rest) - BOT_LIFE - BOT_LIFE_FILLER:
        return False
    return bool(set(rest) & BOT_LIFE)


# A line can open on "and" and still be the same question ("and who made you"). The one place
# that matters is the maker question: the reply that names the bot's maker is picked by the
# phrase at the start of the line, so an opening "and" takes that answer away and leaves the
# general "what are you" one. Only that shape is held back - "and do you sleep" keeps the
# answer it had either way, and a line that opens on any other conjunction is unchanged.
JOIN_OPENERS = frozenset("and".split())
# "how old is your boy" is a question about somebody else's child, not about the bot: a person
# word after a possessive names the person the line is about, so "your boy", "my girl" and
# "your son" take the line out of the bot's own vocabulary. The bot's own words ("are you a
# boy or a girl", "how old are you") carry no possessive and are read as before.
A_PERSON_AFTER_A_POSSESSIVE = frozenset("""boy girl son daughter child kid baby man woman
    brother sister mum mom dad mother father friend wife husband partner""".split())

# "do you learn from me" is about what the bot keeps from one chat to the next, and the honest
# answer to it is the memory one ("nothing carries over"), so a line that says the bot takes
# something *from* the person is left to the module that knows. The words that ask it are small.
LEARNING_WORDS = frozenset("""learn learns learnt learned learning remember remembers
    remembered recall recalls forget forgets pick picks take takes keep keeps""".split())
# "do you have a boy or a girl" asks about a child of the person's, not about the bot's sex:
# a person word after "have a" names somebody in the family. "are you a boy" and "are you a
# girl" have no "have" and are read as the bot's own words.
A_HAVING = frozenset("""have has had having got gets getting want wants wanted expecting
    trying planning""".split())
CHILD_NOUNS = frozenset("""boy girl son daughter child kid kids baby babies twins""".split())
POSSESSIVE_WORDS = frozenset("your my our his her their".split())
MAKER_WORDS = frozenset("made make makes making created create built build built trained "
                        "programmed program designed wrote written".split())


def _the_bots_own_not(norm, i):
    """True when the "not" at this position is the bot's own negative, not a clause's.

    Three places it stands at: right after the bot ("youre not chatgpt", "are you not real",
    "you not being real is fine"), right before it because a contraction carries the not in
    front of the subject ("cant you sleep", "didnt you understand me"), and after a subject
    that came first ("you cant sleep" is "you can not sleep"). The last one is only read that
    way when nothing opens a clause of the line's own in front of it, because "what do you do
    when you cant sleep" is a question about the night and the bot in it is the person.
    """
    if i + 1 < len(norm) and norm[i + 1] in NOT_BEFORE_THE_BOT:
        return True
    if i >= 1 and norm[i - 1] in NOT_AFTER_THE_BOT:
        return True
    if (i >= 2 and norm[i - 2] in NOT_BEFORE_THE_BOT and norm[i - 1] in NOT_AUX
            and (i < 3 or norm[i - 3] not in CLAUSE_OPENERS)):
        return True
    return False


# "what did i just tell you", "what have i said about my mum", "what did i ask you": the person
# is the one who said it, and the bot is who they said it to, so the line is about the chat and
# not about the bot.
_I_SAID_IT = re.compile(
    r"^\W*(?:(?:and|but|so|ok|okay|right|now|then|wait)[,. ]+)*"
    r"(?:what|which|when|where)\b[^.?!]*?\bi\b[^.?!]*?"
    r"\b(?:said|say|told|tell|mentioned|mention|asked|ask)\b", re.I)


def _recalls_their_own_line(norm):
    """True when the line asks for something the person themselves said."""
    return bool(_I_SAID_IT.match(" ".join(str(word) for word in norm if word)))


def _self_ask(norm):
    """True when the whole line is a question about the bot and names nothing else.

    "do you have hobbies", "who made you", "what should i call you" qualify. "how do you spell
    necessary" and "what can you do with leftover rice" do not, because a word outside the
    bot's own vocabulary is in the line, so the topic keeps them.
    """
    words = set(norm)
    if not words or not words & {"you", "your", "yourself", "yours"}:
        return False
    if not words & SELF_ASK:
        return False
    if _a_person_they_like(norm) or _a_thing_they_own(norm):
        return False
    if norm and norm[0] in JOIN_OPENERS and words & MAKER_WORDS:
        return False      # "and who made you" is the maker question, not the identity one
    if any(norm[i] in POSSESSIVE_WORDS and norm[i + 1] in A_PERSON_AFTER_A_POSSESSIVE
           for i in range(len(norm) - 1)):
        return False      # "how old is your boy" is about a child, not about the bot
    if any(norm[i] in LEARNING_WORDS and norm[i + 1] == "from" for i in range(len(norm) - 1)):
        return False      # "do you learn from me" asks what the bot keeps, not what it is
    if set(norm) & A_HAVING and set(norm) & CHILD_NOUNS:
        return False      # "do you have a boy or a girl" asks about a child, not the bot
    left = words - SELF_WORDS - SELF_FILLER - {"you", "your", "yourself", "yours"}
    if "not" in words:
        # Right after the bot it is the bot's own negative ("youre not chatgpt"). Behind another
        # verb it opens a clause about something else, and that clause is the line's subject.
        if any(norm[i] == "not" and not _the_bots_own_not(norm, i)
               for i in range(1, len(norm))):
            return False
        left = left - {"not"}
    return not left


def _about_bot(text, words, norm=()):
    """True when the line asks about the bot itself, not about something it was asked to do."""
    return _about_bot_kind(text, words, norm) is not None


def _asks_if_the_bot_is_a_product(norm):
    """True for a yes/no ask that names an assistant product: "are you claude".

    "are you claude" asks whether there is a model under this, which is the "model" kind and not
    the "identity" one, so the answer that says there is no model keeps the turn. The same words
    as a statement ("so youre claude") say what the bot is, not what it is made of.
    """
    if len(norm) < 2 or len(norm) > PRODUCT_ASK_WORDS or norm[0] not in ("are", "is"):
        return False
    if set(norm) & ROBOT_WORDS:
        return False                      # "are you a bot", "are you real" keep the identity line
    tail = list(norm)
    while tail and tail[-1] in PRODUCT_ASK_TAIL:
        tail.pop()                        # "are you claude then", "is this really claude"
    return len(tail) > 1 and tail[-1] in ASSISTANT_NAMES


def _starts_with(words, phrases):
    bare = " ".join(words)
    return any(bare == p or bare.startswith(p + " ") for p in phrases)


# People put one interjection in front of a courtesy: "aw thanks", "oh cheers", "ahh thank you".
# The filler says nothing on its own, so the thanks is still the whole line and the reply is
# still "any time" rather than the nod the line was getting.
BEFORE_COURTESY = frozenset("aw aww ah ahh oh ohh ooh awe ha haha um umm er hmm".split())


def without_filler(norm):
    """This line with one interjection taken off the front, or the line itself."""
    if len(norm) > 1 and norm[0] in BEFORE_COURTESY:
        return norm[1:]
    return norm


# "thank you card", "thank you letter", "thanks message": the courtesy word is part of the
# name of a thing to write, and the line is about writing it, not about the bot's last answer.
COURTESY_THING = frozenset("""card cards letter letters message messages note notes mail
    email emails text texts speech poem poem story banner sign tag tags gift gifts present
    presents cake wine chocolates flowers box bag""".split())


def _a_thing_named_after_the_courtesy(norm):
    """True when the courtesy word is the first half of a thing's name: "thank you card"."""
    rest = _after_thanks(norm)
    return bool(rest) and rest[0] in COURTESY_THING


def _after_thanks(norm):
    """The words left when a leading "thanks" is taken off, or None if it is not there."""
    for phrase in sorted(THANKS, key=len, reverse=True):
        words = phrase.split()
        if norm[:len(words)] == words:
            rest = norm[len(words):]
            if rest[:1] and rest[0] in COURTESY_THING:
                return None                     # "thank you card for a wedding present"
            return rest
    return None


def the_line_after_a_courtesy(norm):
    """The words a line goes on with after a leading "thanks", or None if it starts with one.

    A thank-you is often a wrapper round a line that still needs an answer ("thanks, my boss
    is a nightmare"), and the caller needs to see the line inside it.
    """
    return _after_thanks(without_filler(norm))


# A fault, a pain or a thing that has stopped working. After a courtesy opener one of these
# still needs an answer, so the thanks is a wrapper, not the whole line.
NEEDS_ANSWER = frozenset("""hurt hurts hurting hurt ache aches aching pain painful sore agony
    worse worst not never wont cant cannot dont doesnt didnt isnt arent wasnt weren kept
    killing killed
    keeps stopped stops broken broke breaks leaking leaks leak stuck died dead die rash
    swollen bleeding bled sick unwell slow noisy noise smells burning stings itches
    problem problems wrong stuck rubbish awful terrible worried worrying scared""".split())

# A symptom or an accident, which is the other way a person says something still needs an
# answer: "thanks, i have a headache" and "thanks, i slipped in the garden" are the same shape
# as the boiler, and the ache or the fall is the news, not the sign-off. The compound aches
# (headache, toothache, backache, earache, stomach ache) come from the ending rather than a
# list, because people make new ones ("eye ache") as they type. A fall is only an accident
# with a place to fall: "i fell asleep" and "i fell for it" say nothing is wrong.
STILL_WRONG = re.compile(r"""
    \b(?:
        (?!cache\b)\w*ache | fever(?:ish)? | cough(?:ing)? | dizzy | nauseous? | vomit(?:ing)?
      | shiver(?:s|ing|y)? | chills | dehydrat\w+
      | (?:have|has|had|got|gotten|running|caught|catch|my|his|her|their|your)
        \s+(?:an?\s+)?(?:high\s+|slight\s+|bit\s+of\s+a\s+|touch\s+of\s+a\s+)?temperature
    )\b
""", re.X)

# "temperature" is the oven's just as often, and a line about the oven says nothing is wrong:
# only a person who has one is ill ("thanks, i have a temperature"), so the illness word needs
# the person word in front of it, which is what the pattern above asks for.
#
# A fall names where it happened; finding something names what was found ("i stumbled on your
# blog"), and a forgotten thing is not a fall ("it slipped my mind"). So a slip or a stumble
# counts as an accident unless the words after it name a thing found rather than a place.
FOUND = frozenset("""blog article post page site website video photo picture recipe thread
    comment question quiz idea story podcast episode book film answer deal bargain
    mind""".split())
# The words that follow a slip when nothing was fallen over: something was come across, or a
# thing slipped out of place, and neither of those is an accident.
SLIPPED_FROM = frozenset("across upon into through by away past".split())
FALL = frozenset("fallen fainted".split())
# Every word a fall is said with, so a line that says one can be asked what kind of fall it was:
# "i fell asleep at nine" is not an accident and "i slipped in the garden" is.
FELL_WORDS = FALL | frozenset("""fell fall falls falling tripped tripping slipped slipping
    stumbled stumbling collapsed collapse""".split())


def _a_fall(rest):
    """Did the rest of the line say somebody fell, rather than found or forgot something?"""
    for index, word in enumerate(rest):
        if word in FALL or word.startswith("collaps"):
            return True
        if word == "fell":
            after = rest[index + 1] if index + 1 < len(rest) else ""
            if after not in ("asleep", "for", "into", "in", "behind", "out"):
                return True
            continue
        if word in ("tripped", "slipped", "slipping", "stumbled", "stumbling"):
            after = rest[index + 1:index + 7]
            if after[:1] and after[0] in SLIPPED_FROM:
                continue                       # "i stumbled across a great recipe"
            if [one for one in after if one in FOUND]:
                continue                       # "i stumbled on your blog", "it slipped my mind"
            return True
    return False


# Words a greeting can carry without saying anything else: "hi there", "morning all",
# "hey, quick question", "hiya, hope you are well".
GREETING_TAIL = frozenset("""there again all folks friends everyone everybody guys you your
    mate quick question hope hopes hoping doing day today going well good thanks thank then
    too also just so how are is it things up sup life ok okay alright fine here back""".split())
# How a line gives its own name: "hi, I'm Sam", "good morning, my name is Priya".
INTRODUCES = (("my", "name", "is"), ("the", "name", "is"), ("i", "am"), ("im",),
              ("call", "me"), ("this", "is"), ("its",))


def _after_greeting(norm):
    """The words left when a leading greeting is taken off, or None if there is not one."""
    for phrase in sorted(GREETINGS, key=len, reverse=True):
        words = phrase.split()
        if norm[:len(words)] == words:
            return norm[len(words):]
    return None


def after_greeting(norm):
    """The words a line says after a leading hello, or None when it opens with none.

    For the readers that answer what a line says rather than how it opens: "hi, I'm
    vegetarian" says the diet and the hello only opens it, and a module that can answer the
    diet needs the rest of the words.
    """
    return _after_greeting(list(norm or []))


# Words that only fill out a goodbye, so a line made of them and a farewell is still just the
# goodbye: "night night", "bye everyone", "right then, good night". Nothing that names its own
# subject is here - "night feeds are killing me" is a line about the feeds, not a goodnight.
FAREWELL_TAIL = frozenset("""then ok okay right well so all everyone everybody guys folks mates
    now for to soon later tomorrow tonight night good xx xxx love hun""".split())


# "night then, thanks" is still a goodnight: the words a goodbye is said with and nothing else.
_SAID_ON_ITS_OWN = frozenset(
    [word for phrase in THANKS + FAREWELLS for word in phrase.split()])
_THANKS_WORDS = frozenset([word for phrase in THANKS for word in phrase.split()])
# A goodnight is often said with a wish for the night in front of it: "night night, sleep well".
_NIGHT_WISHES = ("sleep well", "sleep tight", "sleep good", "sweet dreams", "rest well",
                 "night night")
_WISH_WORDS = frozenset(" ".join(_NIGHT_WISHES).split())


def _after_farewell(norm):
    """The words left when a leading farewell is taken off, or None if there is not one."""
    for phrase in sorted(FAREWELLS, key=len, reverse=True):
        words = phrase.split()
        if norm[:len(words)] == words:
            return norm[len(words):]
    return None


def farewell_only(norm):
    """True when the line is a goodbye, not a goodbye wrapped round something to answer.

    A farewell word is an ordinary word in its own right - "night" is when the baby wakes,
    "later" is when something happens, "care" is what a nurse gives - so the goodbye has to be
    the whole line. "night night", "good night all" and "see you tomorrow" are goodbyes; "night
    feeds are killing me", "night shift this week", "good night routine for a baby" and "take
    care of your mum" are lines about something, and the answer belongs to what they say.
    """
    rest = _after_farewell(norm)
    if rest is None:
        return False
    if set(rest) & NEEDS_ANSWER:
        return False
    left = [word for word in rest if word not in _WISH_WORDS]
    if len(left) < len(rest) and all(word in FAREWELL_TAIL or word in POLITE for word in left):
        # "night night, sleep well" and "good night, sweet dreams" wish the night well on the way
        # out; a wish with anything else in it ("sleep well now the baby is older") is news.
        return True
    if rest and rest[0] in _THANKS_WORDS:
        # "bye, thanks for the help" says thank you on the way out, which is still the way out.
        return True
    # A goodbye is said to somebody: "bye love", "night pet", "ciao bella" and "bye duck" are
    # still the goodbye, and the name it is said to does not make it a line about them.
    return all(word in FAREWELL_TAIL or word in POLITE or word in _SAID_ON_ITS_OWN
               or word in TERMS_OF_ADDRESS for word in rest)


def greeting_only(norm):
    """True when the line is a hello, not a hello wrapped round something to answer.

    "hi", "morning all" and "hey, quick question" are greetings, and so is "hi, I'm Sam",
    which gives a name and nothing else. "hi, my boiler is leaking" is a report: the rest of
    the line decides the kind, because a hello-shaped answer to a leaking boiler is useless.
    """
    rest = _after_greeting(norm)
    if rest is None:
        return False
    if all(word in GREETING_TAIL or word in POLITE for word in rest):
        return True
    # A greeting with two words of small talk after it is still a greeting: "Morning! Finally
    # Friday." Nothing that hurts or has stopped working counts, so "hi it hurts" is not one,
    # and neither does anything that says what the person is or has ("hi, im vegetarian", "hi,
    # im diabetic", "hi, im 34"): those two words are the whole of the line, and the hello is
    # only how it opens.
    if len(rest) <= 2 and not set(rest) & NEEDS_ANSWER \
            and not _says_what_they_are(rest):
        return True
    for lead in INTRODUCES:
        if tuple(rest[:len(lead)]) != lead:
            continue
        # "hi, I'm called Sam" names the person in the same words as the store's own name
        # reading, and the naming word is not part of the name.
        tail = [word for word in rest[len(lead):] if word not in NAMING_WORDS]
        # A name is the whole of what is left, and a line that goes on to ask something is
        # not a greeting: "hi, I'm Sam, my boiler is leaking" needs the boiler answered.
        if not 1 <= len(tail) <= 2:
            return False
        # Whether the word after "I'm" is a name is the fact store's reading, because it is the
        # only reading that can tell "hi, I'm Sam" from "hi, I'm a nurse" and "hi, I'm
        # vegetarian". Counting any short tail as a name read every hello in front of what the
        # person is as a greeting, and the only answer left was "what would you like to talk
        # about?"
        return all(_a_name(word) for word in tail)
    return False


# The words a name is given with, which are not part of it: "hi, I'm called Sam".
NAMING_WORDS = frozenset(("called", "named", "name", "names"))


def _says_what_they_are(rest):
    """Whether the words after a hello say what the person is, has or does.

    A hello with a name after it is a greeting ("hi, I'm Sam"), and the same hello with a fact
    after it is a person telling you the fact ("hi, I'm vegetarian", "hi, im diabetic"): the
    words are the whole of the line in the second, and the hello is only how it opens. Which
    one it is, is the fact store's reading (`facts.about_themselves`) - the only reading that
    can tell a name from a fact about the person - and it is the same question the store asks
    before it says the fact back (`bot/memory/ack.py`). Imported here because the fact store
    reads this module.
    """
    from ..memory.facts import about_themselves
    return bool(about_themselves(" ".join(rest)))


def _a_name(word):
    """Whether a word said after "I'm" is a name: "hi, I'm Sam" against "hi, I'm a nurse"."""
    from ..memory.facts import reads_as_a_name
    return bool(reads_as_a_name(word))


# A line that says the help was good without using a thanks word: "that helps", "ok that helps",
# "that really helps", "that helped a lot", "thats helpful". The person is closing the turn on
# the answer just given, so the line is a thank-you for the same reason "thanks" is: there is
# nothing in it left to answer, and the topic the conversation is on must not pull it back to
# the entry that was just read. Only a whole line counts, so "what helps a headache" and
# "that helps my back" keep their own answer.
HELP_WAS_GOOD = frozenset((
    "that helps", "this helps",
    "that really helps", "this really helps",
    "that helps a lot", "that helps loads", "that helps so much",
    "that helped", "this helped",
    "that really helped", "this really helped",
    "that helped a lot", "that helped loads", "that helped so much",
    "thats helpful", "that is helpful", "that was helpful",
    "this is helpful", "this was helpful",
))
# The agreement in front of a praise says nothing and does not stop it being one.
BEFORE_HELP_WAS_GOOD = frozenset("ok okay yeah yep yes ah oh right cool so".split())
# The softener after the praise says nothing either: "that helps actually", "that really helps
# tbh", "that helped a lot honestly". Read without it the line said the help was good, and a
# softener is not news: it was read as a statement about nothing, and answered with the filler
# "Got it. Is there anything you'd like a hand with?" right after the person said it worked.
AFTER_HELP_WAS_GOOD = frozenset("""actually tbh honestly really though tho anyway now then
    mind cheers thanks""".split())
# A softener the chat table spells out in full: "tbh" is read as "to be honest", so the tail is
# three words rather than one and the words have to come off together.
AFTER_HELP_WAS_GOOD_SAID_OUT = ("to be honest", "to be fair", "if im honest", "if i am honest",
                                "in all honesty", "to tell the truth")


def _says_the_help_was_good(norm):
    """True when the whole line says the last answer helped, without a thanks word."""
    words = list(norm)
    while len(words) > 2 and words[0] in BEFORE_HELP_WAS_GOOD:
        words = words[1:]
    while len(words) > 2:
        said = " ".join(words)
        tail = next((phrase.split() for phrase in AFTER_HELP_WAS_GOOD_SAID_OUT
                     if said.endswith(" " + phrase)), None)
        if tail is None and words[-1] in AFTER_HELP_WAS_GOOD:
            tail = [words[-1]]
        if tail is None or len(words) - len(tail) < 2:
            break
        words = words[:-len(tail)]
    return " ".join(words) in HELP_WAS_GOOD


def _thanks_only(norm, clauses=None):
    """True when "thanks" is the whole line, not a wrapper round a problem.

    "thanks, that worked" and "thanks for staying with me" are thanks; "thanks, my boiler
    keeps losing pressure" reports a fault, and the answer belongs to the boiler, so the
    rest of the line decides the kind.
    """
    rest = _after_thanks(norm)
    if rest is None:
        return False
    if set(rest) & NEEDS_ANSWER:
        return False
    if STILL_WRONG.search(" ".join(rest)):
        return False
    if _a_clause_of_its_own(rest, clauses):
        return False
    return not _a_fall(rest)


# What a thank-you is about, so words that open with one are still part of it: "thanks, that
# worked", "thank you, this helps".
THANKS_ABOUT = frozenset("that this it they them those these which".split())
# News that things are better is a thank-you with the news on it, not a new subject: "thanks,
# i feel much better now", "thanks, the pain has gone".
BETTER = frozenset("""better best glad happy pleased relieved easier lighter improved gone
    tried try trying worked works""".split())
# A thank-you said on the way out is still a thank-you: "thanks, im off to bed", "cheers, i'm
# going to turn in". Nothing in it needs an answer.
# A thank-you that says something about the person being thanked is still a thank-you: "thanks,
# i owe you one", "thanks, you're a star".
SAYS_ABOUT_YOU = frozenset("you your yours u ya".split())
# A compliment about the thing the bot helped with is still part of the thank-you: "thanks, the
# oven temperature was perfect", "thanks, the cake was delicious". The person is closing the turn
# on a good note and there is nothing in it to answer.
PRAISING = frozenset("""perfect great brilliant lovely delicious gorgeous superb spot amazing
    excellent wonderful nice good marvellous marvelous fantastic smashing""".split())
# Praise said with a verb rather than an adjective, which is how people report back on advice
# that worked: "thanks, my son loved it", "cheers, the kids enjoyed it", "thanks, it went down
# well". The thing was good, and there is nothing left to answer.
PRAISING_VERB = frozenset("""loved love loves liked like likes enjoyed enjoy enjoys adored
    devoured demolished wolfed""".split())
# The same praise said as a phrase: "cheers, the stew went down well", "it went down a treat".
PRAISE_SAID = re.compile(r"\b(?:went|gone)\s+down\s+(?:well|a\s+treat|great|nicely)\b")
# A thing praised and then complained about in the same breath is the complaint.
TURNED_ROUND = frozenset("but though although except however".split())
# A thank-you reporting a step of the advice that the person has just done is still a
# thank-you: "thanks, i cleared the cache", "cheers, i restarted the router", "thanks, i put
# it on charge". They did what the bot said and came back to say so, and the answer to the
# turn before is the answer they wanted.
STEP_VERBS = frozenset("""cleared restarted rebooted reinstalled uninstalled deleted removed
    emptied cleaned washed rinsed changed swapped reset updated charged plugged poured soaked
    drained defrosted tried gave followed did put set""".split())
# The step verbs that take almost any object, so that the object cannot tell a step from an
# accident: "i put my back out", "i gave my notice in", "i did my back in", "i changed my mind".
STEP_ANY_OBJECT = frozenset("put set did gave changed".split())
# A step reported as having gone wrong is not a thank-you any more: "thanks, i cleared the
# cache but it is no better", "thanks, i booked the wrong day".
STEP_WRONG = frozenset("""wrong mistake error errors failed fails broken broke wont cant
    stopped worse nothing none no not still again""".split())
SIGNING_OFF = re.compile(r"""
    \b(?:i'?m|im|i\s+am|we'?re|were|we\s+are)\s+(?:off|away|going|turning\s+in|heading)\b
    | \b(?:good\s*night|goodnight|bedtime|off\s+to\s+bed|turning\s+in)\b
    | \bnothing\s+(?:else|more|left)\b | \bnothing\s+to\s+do\b
    """, re.X)


def _a_clause_of_its_own(rest, clauses=None):
    """True when the rest of a line that opens with a thank-you says something of its own.

    A thank-you at the front of a line is a wrapper round what follows it, and what follows it
    is often the point: "cheers, im skint till friday" is news about the week, and read as a
    thank-you it was answered with the answer to the turn before, all over again. The
    thank-you does hold what comes after it when that is short ("thanks, it worked"), opens
    with what the thanks is about ("thanks, that explains the boiler"), is agreement ("thanks,
    that worked a treat"), or says things are better ("thanks, i feel much better now"). A
    clause of four words or more that does none of those is the line, and the line needs an
    answer.
    """
    if not rest or rest[0] in THANKS_ABOUT:
        return False
    if _starts_with(rest, THANKS):
        return False      # "much appreciated, thanks for the tips" is two thank-yous in a row
    if len(rest) < 4:
        return False
    if _a_step_done(rest):
        # A step of the advice done and reported back is still a thank-you; one that did not
        # work is the news: "thanks, i cleared the cache but it is no better".
        return _the_step_went_wrong(rest)
    if _agrees(rest) or set(rest) & BETTER:
        return False
    if _praises_the_thing(rest):
        return False      # "thanks, the cake was delicious"
    if set(rest) & SAYS_ABOUT_YOU:
        return False      # "thanks, i owe you one", "thanks, you're a star"
    if _a_fall_that_is_not_one(rest):
        return False      # "thanks, i fell asleep at nine", "thanks, i fell for it"
    if "temperature" in rest:
        # STILL_WRONG has already ruled out a person with one, so this is the oven's: "thanks, i
        # need a higher temperature" is how the baking went, not news.
        return False
    if SIGNING_OFF.search(" ".join(rest)):
        return False
    for clause in (clauses or [])[1:]:
        if len(clause) >= 4 and clause[0] not in THANKS_ABOUT:
            return True
    return False


def _a_step_done(rest):
    """True when the rest of the line reports doing a step of the advice, and nothing went wrong.

    "thanks, i cleared the cache" and "cheers, i restarted the router" are the person saying they
    did what the bot suggested. The step is named as a thing being acted on ("the", "my", "it"),
    so a line about the person's own day keeps its own answer: "thanks, i booked a table for
    friday" is still news, and "thanks, i tried the new place on saturday" is a thing they did
    rather than a report back. A step that went wrong is the news, not the thank-you.
    """
    if len(rest) < 3 or rest[0] not in ("i", "we"):
        return False
    if rest[1] not in STEP_VERBS and not (rest[1] == "gave" and "go" in rest[2:4]):
        return False
    after = rest[2:]
    if rest[1] in ("tried", "swapped"):
        # "i tried the new place on saturday" is a thing they did, not a report back on advice.
        return after[:1] == ["it"]
    if rest[1] in STEP_ANY_OBJECT and after[:1] not in (["it"], ["the"]):
        # A step verb takes almost any object, so "the"/"my" alone made an accident read as a
        # report back: "thanks, i put my back out" is the state the person ended up in, and a
        # person whose back has gone must not be told "no problem at all". What a step acts on is
        # what the bot named ("the cache") or "it"; "my" is how a thing of the person's own gets
        # named ("restarted my router"), and no verb that takes anything keeps it.
        return False
    return "the" in after or "my" in after or after[:1] == ["it"]


def _the_step_went_wrong(rest):
    """True when a step of the advice is reported as having failed."""
    return bool(set(rest[2:]) & STEP_WRONG)


def _a_fall_that_is_not_one(rest):
    """True when the rest names a fall that is not one, so it stays part of the thank-you.

    "thanks, i fell asleep at nine" and "thanks, i fell for it" say something went well; the
    words are the ones an accident uses, and an accident is what makes the line news, so the
    rest of the line has to say what kind of fall it was. _a_fall already tells those two from
    "thanks, i slipped in the garden".
    """
    if not set(rest) & FELL_WORDS:
        return False
    return not _a_fall(rest)


def _praises_the_thing(rest):
    """True when what follows the thank-you is a compliment about a thing, not news of its own.

    "thanks, the oven temperature was perfect" and "thanks, the cake was delicious" praise the
    thing the bot helped with and need no answer, so the thank-you still holds the line. Praise
    said of the speaker ("thanks, im good now") is a thank-you too. A thing praised and then
    complained about in the same breath is the complaint: "the meal was good but the service was
    slow".
    """
    if not (set(rest) & (PRAISING | PRAISING_VERB) or PRAISE_SAID.search(" ".join(rest))):
        return False
    return not set(rest) & TURNED_ROUND


# The words people put in front of a "thanks" as they answer the bot: "pretty good thanks",
# "that helps a lot thanks", "not bad ta". A line ending in thanks counts as thanks when
# everything before it is one of these, so a line that also reports something keeps its kind
# ("the flat is freezing thanks" is still news about the flat).
AGREE_TAIL = frozenset("""it that this these those all so much very quite a an lot bit really
    pretty good great fine nice cool ok okay lovely brilliant magic perfect spot better best
    well helps helped works worked working doing do does is was been am are you your not no
    too to and now enough still same here there just also then
    love loved loving like liked liking righto alright ace grand decent pleased glad happy
    kind kindest thoughtful generous sweet
    one ones of""".split()) | AFFIRM

# "not bad" and "not too bad" are agreement; "bad" on its own is not, so it only counts
# in a line that also says "not".
AGREE_AFTER_NOT = frozenset("bad half wrong shabby".split())

# After "not", these words are skipped before the word that decides: "not too bad thanks",
# "not that good thanks".
NOT_FILLER = frozenset("too that so very much all quite a an to even really feeling".split())

# The noise a person writes in front of a thank you. It says nothing about the line, and it is
# not an agreement either: "oh thanks" is a thank you with a sound in front of it, where
# "sounds good thanks" is an answer. Read as an agreement, "oh thanks" and "ah thanks" were
# answered "Fair enough." - a shrug at the offer - instead of "No problem at all.".
THANKS_NOISE = frozenset("oh ah aha aah ahh ohh ooh aw aww mm mmm".split())

# The name a short line is said to, at the end of it: "thanks love", "thanks pet", "cheers
# duck", "morning hen". It names the person being spoken to, not a feeling and not a thing the
# line is about, so the line is the thank you (or the hello) with a name after it. Read as a
# word of its own, "love" made "thanks love" a good feeling, and the thank you behind it was
# answered "Fair enough.".
ADDRESSED = frozenset("""love mate pet hun duck sunshine hen flower chuck dear pal buddy
    babes shug lovey""".split())


def _agrees(rest):
    """Whether every word before the thanks is agreement, so the thanks is the whole answer.

    "not" is the hard part: "not bad thanks" agrees, and "still not working thanks" does not,
    because the person has just told you their thing is still broken. So what follows "not" is
    the word that decides.
    """
    if "not" not in rest:
        return all(word in AGREE_TAIL for word in rest)
    after = rest[rest.index("not") + 1:]
    while after and after[0] in NOT_FILLER:
        after = after[1:]
    if not (after and after[0] in AGREE_AFTER_NOT):
        return False
    return all(word in AGREE_TAIL or word in AGREE_AFTER_NOT for word in after)


def _ends_with_thanks(norm):
    """True when a short line ends in thanks: "pretty good thanks", "brilliant thanks".

    People answer the bot and thank it in one breath, and the tail is the whole point of the
    line: "loving it thanks" is thanks, not news.
    """
    # A name at the end is the person the line is said to, not part of what it says, so the
    # thank you is looked for in front of it: "thanks pet", "oh thanks love".
    said_to = len(norm)
    while said_to and norm[said_to - 1] in ADDRESSED:
        said_to -= 1
    line = norm[:said_to]
    named = said_to < len(norm)
    for phrase in sorted(THANKS, key=len, reverse=True):
        words = phrase.split()
        if len(line) > len(words) and line[-len(words):] == words:
            # The noise in front of a thank you is not part of it either, and a line with
            # nothing else in it is the thank you itself: "oh thanks", "mm thanks".
            rest = [word for word in line[:-len(words)] if word not in THANKS_NOISE]
            if not rest:
                return True
            if len(rest) > 6:
                continue
            if set(rest) <= (AFFIRM | ACK) and not named:
                continue      # "sounds good thanks" is already an answer: leave it an ack
            if rest[:1] and rest[0] in {"no", "nope", "nah", "never", "naw"}:
                continue      # "no thanks" is a refusal, and the refusal is the point
            if not _agrees(rest):
                continue      # "still not working thanks" is a fault, not a thank-you
            return True
    return False
# A line that says a question is coming, or asks for help without saying what with: "can i ask
# you something", "i have a question", "i need some advice", "can you help me with something".
# Nothing in it can be answered yet, so it is not a question about the world; the reply is to
# invite them to go on. Every word has to be part of the frame, so "can i ask you something
# about my boiler" stays a boiler question.
OPENING_FRAME = re.compile(r"""
    \b(?:can|could|may|might)\s+i\s+ask\s+(?:you\s+)?(?:something|somethin|a\s+question|one\s+thing|advice|for\s+advice|your\s+advice)\b
  | \b(?:i|ive)?\s*(?:have|got|has)\s+(?:a\s+|one\s+|quick\s+)?question\b
  | \bquick\s+question\b
  | \b(?:i|we)\s+(?:need|want|would\s+like|could\s+use)\s+(?:(?:some|a\s+bit\s+of)\s+)?(?:your\s+)?advice\b
  | \b(?:can|could|would|will)\s+you\s+help\s+me\s+(?:with\s+something|with\s+a\s+thing|with\s+one\s+thing|out\s+with\s+something)\b
  | \bmind\s+if\s+i\s+ask\s+(?:you\s+)?(?:something|a\s+question)\b
  | \bi\s+(?:want|need)\s+to\s+ask\s+you\s+(?:something|a\s+question)\b
""", re.X)
OPENING_WORDS = frozenset("""can could may might i ask you something somethin a one thing
    question quick have got has ive we need want would like use some bit of for your advice
    help me with out will to if mind is it""".split())
OPENING_MAX = 9
# The other thing people say before they say anything: they want to talk, or to get something
# off their chest. It is the same reading as a question that is coming - nothing in it can be
# answered yet, so the reply is to make it easy to go on - and the same guard: the whole line
# has to be the frame, so "i need to talk to my sister" and "i want to vent about work" keep
# the person and the subject they name.
# The talk words people use for the same ask. "vent" and "rant" are the loud ones; a whinge, a
# grumble and an offload are the same request to be listened to, and they were answered as
# questions about the world ("What kind of whinge do you usually go for?").
TALK_ASK_VERBS = r"(?:vent|rant|moan|whinge|grumble|offload|unload)"
# What the ask may say after the verb and still be the whole line: "can i vent about it",
# "can i talk about this" ("can i talk about it" was read as the speech-therapy question),
# "can i have a moan here", "i need to talk first".
TALK_TAIL_WORDS = (r"(?:\s+(?:a\s+bit|a\s+minute|a\s+sec|a\s+moment|one\s+thing|"
                   r"for\s+a\s+minute|for\s+a\s+bit|about\s+something|about\s+it|"
                   r"about\s+this|to\s+you|to\s+someone|on\s+you|here|first))*")
# How a person asks leave to do any of it: the permission ask, with the person in it.
TALK_ASK_OPENERS = (r"(?:(?:can|could|may)\s+(?:i|we)|do\s+you\s+mind\s+if\s+i|"
                    r"would\s+you\s+mind\s+if\s+i|is\s+it\s+ok\s+if\s+i|"
                    r"is\s+it\s+okay\s+if\s+i)")
TALK_OPENING = re.compile("|".join((
    # "i just want to vent", "im going to vent", "we need a moan"
    r"(?:i\s+|we\s+)?(?:just\s+|really\s+|honestly\s+|properly\s+)?(?:am\s+|are\s+)?"
    r"(?:(?:want|wanna|need|have|got|gotta|planning|going|gonna)\s+)?(?:to\s+)?"
    + TALK_ASK_VERBS + TALK_TAIL_WORDS,
    # "can i rant", "could we have a moan"
    r"(?:can|could|may)\s+(?:i|we)\s+(?:just\s+)?(?:have\s+a\s+)?" + TALK_ASK_VERBS
    + TALK_TAIL_WORDS,
    # "im going to have a proper rant", "i need a rant", "a quick moan"
    r"(?:i\s+|we\s+)?(?:just\s+)?(?:am\s+|are\s+)?(?:going\s+to\s+|gonna\s+)?"
    r"(?:(?:want|wanna|need|have|got|gotta)\s+(?:to\s+)?)?(?:have\s+)?a\s+"
    r"(?:proper\s+|good\s+|quick\s+|little\s+)?(?:vent|rant|moan|whinge|grumble)"
    + TALK_TAIL_WORDS,
    # "i need to get something off my chest", "can i get this off my chest"
    r"(?:i\s+)?(?:just\s+)?(?:(?:want|wanna|need|have|got|gotta)\s+(?:to\s+)?"
    r"|(?:can|could|may)\s+i\s+|let\s+me\s+)(?:get\s+)?"
    r"(?:something|somethin|this|it)\s+off\s+my\s+chest",
    # "i need to talk", "i want to talk to you about something", "we should talk"
    r"(?:i\s+|we\s+)?(?:just\s+|really\s+)?(?:am\s+|are\s+)?"
    r"(?:(?:want|wanna|need|have|got|gotta|going)\s+(?:to\s+)?"
    r"|(?:can|could|may)\s+(?:i|we)\s+)"
    r"talk" + TALK_TAIL_WORDS,
    # "i need someone to talk to"
    r"(?:i\s+)?(?:need|want|would\s+like)\s+"
    r"(?:someone|somebody|anyone|anybody)\s+to\s+talk\s+to",
    # "can i have a word", "i need a word"
    #
    # Saying something is coming is not the same as asking for room to say it, and the lines
    # below are left to the card that already answers them well: "i have something to tell you"
    # and "can i tell you something" get "Of course. Take your time.", and "got something on my
    # mind" gets "Going round it that many times is exhausting. Say it out to me - what keeps
    # coming back?". Read as an opener, all three got "Ask away, I'm listening. What's going
    # on?" instead, which asks a question in the same breath as giving room - the one thing a
    # person about to say something hard does not need. They are also the lines where the
    # person has already decided to speak, so there is nothing to make easier.
    r"(?:can|could|may)\s+i\s+(?:have\s+a\s+word)",
    r"(?:i\s+)?(?:need|want)\s+a\s+word",
    # Asking for the bot's ear is the same ask with the same answer - "can i run something by
    # you" was a search hedge, "can i get a second opinion" said it would rather not guess -
    # and each phrase holds "you", so it cannot be about anything else.
    TALK_ASK_OPENERS + r"\s+"
    r"(?:run|bounce|try|talk\s+through)\s+"
    r"(?:something|somethin|this|that|it|an?\s+idea|one\s+thing|a\s+couple\s+of\s+things|"
    r"a\s+few\s+things|some\s+ideas?)\s+(?:by|past|off)\s+you" + TALK_TAIL_WORDS,
    TALK_ASK_OPENERS + r"\s+"
    r"(?:pick\s+your\s+brains?|bend\s+your\s+ear)" + TALK_TAIL_WORDS,
    TALK_ASK_OPENERS + r"\s+"
    r"(?:tell\s+you\s+what\s+happened|share\s+(?:something|this|it)\s+with\s+you|"
    r"have\s+a\s+second\s+opinion|get\s+a\s+second\s+opinion)" + TALK_TAIL_WORDS,
)))
# The line can be wrapped in a word that says nothing but that they are starting ("right, im
# going to vent", "ok so i need to get this off my chest") and end in one that only softens it
# ("... tbh", "... if that's ok"). Either side is taken off before the frame is matched, so the
# frame itself stays the whole line and a subject named in it is still a subject.
TALK_HEAD = frozenset("""right ok okay so look well honestly listen alright now then""".split())
TALK_TAIL = (("to", "be", "honest"), ("if", "that", "is", "ok"), ("if", "thats", "ok"),
             ("now",), ("please",), ("then",), ("thanks",), ("right",), ("actually",),
             ("quickly",), ("quick",), ("mate",))


def _talk_opening(text):
    """True when the whole line asks for room to talk, with nothing named yet in it."""
    words = text.split()
    changed = True
    while words and changed:
        changed = False
        if words[0] in TALK_HEAD:
            words, changed = words[1:], True
        for tail in TALK_TAIL:
            if len(words) > len(tail) + 1 and tuple(words[-len(tail):]) == tail:
                words, changed = words[:-len(tail)], True
                break
    return bool(words) and bool(TALK_OPENING.fullmatch(" ".join(words)))


def talk_frame(norm):
    """True when the whole line asks for room to talk and names nothing in it.

    `opening_line` uses this, and so does the reading: the frame is the whole line, so a word
    inside it ("run", "brain", "share") is not a subject, and an answer that matched one of them
    ("can i run something by you" found the fitness entry) is not an answer to this line.
    """
    text = " ".join(word for word in norm if word)
    return bool(text) and _talk_opening(text)


def opening_line(norm):
    """True when the line only says a question is coming, or asks for advice in general."""
    words = [word for word in norm if word]
    if not words:
        return False
    text = " ".join(words)
    if _talk_opening(text):
        return True
    if len(words) > OPENING_MAX:
        return False
    if words[0] in {"have", "do", "does", "did"}:
        return False  # "have you got a question" asks the bot, it does not offer one
    if not all(word in OPENING_WORDS for word in words):
        return False
    return bool(OPENING_FRAME.search(text))




def _short_reply(text):
    """True when the whole line is one of the set replies people give after a question."""
    for phrase in SHORT_REPLIES:
        if text == phrase or text.startswith(phrase + " "):
            return True
    return False


# Saying you will do the thing the bot just suggested is an answer to the bot, not news about
# yourself. People leave the "I" off when they type quickly ("will give it a go", "gonna try
# that", "give it a go"), and the line then has no first person in it, which is what makes it
# look like a report and earns the "I don't know enough to answer that" shrug.
COMMIT_OPEN = frozenset("""will wont would gonna going sall ill il id weve well lets let""".split())
COMMIT_TRY = frozenset("""try give go see have take""".split())
# The subject people still type ("i will try that") and the spellings that carry both the
# subject and the "will" in one word ("ill give it a go", "id try that").
COMMIT_SUBJECT = frozenset("i we".split())
COMMIT_ALONE = ("give it a go", "give it a try", "give that a go", "give that a try",
                "give it a shot", "have a go", "have a try", "give it a whirl",
                "try that", "try it", "try this")
COMMIT_ALONE_TAIL = ("let you know", "sounds like a plan")
# A hedged commitment: "might give that a go", "could do that", "nice one, might do that". The
# hedge is not a "will", so the words after it have to be the whole commitment on their own -
# a bare "have" or "go" is something else entirely ("i might have a cold", "i could go for a
# coffee"), which is why these openers do not simply join COMMIT_OPEN.
HEDGED_COMMIT = frozenset("might could may".split())
HEDGED_ALONE = COMMIT_ALONE + ("do that", "do it", "go for it", "ring them", "call them")
# Talking themselves into it: "worth a try", "cant hurt", "no harm in giving it a go". The
# phrase carries the whole agreement at the front of the line, so at most a short tail follows
# it. "no harm in trying" opened on "no" and read as a denial before this.
COMMIT_NO_HARM = ("worth a try", "worth a go", "worth trying", "worth a shot",
                  "cant hurt", "cannot hurt", "no harm in", "nothing to lose")
# The words in front of a decision the person is still making ("i suppose its worth a try",
# "maybe worth a go"): they hedge the agreement, they do not stop it being one.
HEDGE_LEAD_ONE = frozenset("maybe probably suppose guess honestly".split())
HEDGE_LEAD_TWO = ("i suppose", "i guess", "i think", "i reckon")
# The thing that is worth trying is said in front of the phrase ("it cant hurt", "that worth a
# go"), and a "cannot" is two words by the time the reading gets it.
NO_HARM_SUBJECT = frozenset("it its that this there".split())
# What a commitment never carries: a question ("will i give it a go?"), or a second person as
# the thing given to ("will give you a ring" is a plan about someone else).
COMMIT_STOP = frozenset("""you u ya your yourself yall""".split())


def _cant_for_cannot(words):
    """The line as one string, with a split "can not" written back as "cant".

    The reading takes the apostrophe out ("cant" arrives as `can not`), and the phrases that
    carry an agreement are typed with the apostrophe left out, so the two have to be joined.
    """
    joined = []
    index = 0
    while index < len(words):
        if words[index] == "can" and words[index + 1:index + 2] == ["not"]:
            joined.append("cant")
            index += 2
            continue
        joined.append(words[index])
        index += 1
    return " ".join(joined)


def _agrees_to_try(norm):
    """True when the line is the person agreeing to do what was just suggested.

    "will give it a go", "gonna try that", "ok give it a go": the subject is dropped and the
    whole line is the commitment, so the only thing it can answer is the bot's last turn.
    """
    words = [word for word in norm if word and word != "|"]
    if not words or len(words) > 9:
        return False
    if any(word in QUESTION_WORDS or word in COMMIT_STOP for word in words):
        return False
    bare = " ".join(words)
    hedged = list(words)
    while hedged:
        if hedged[0] in HEDGE_LEAD_ONE:
            hedged = hedged[1:]
        elif " ".join(hedged[:2]) in HEDGE_LEAD_TWO:
            hedged = hedged[2:]
        else:
            break
    said = _cant_for_cannot(hedged)
    if said.split()[:1] and said.split()[0] in NO_HARM_SUBJECT:
        said = " ".join(said.split()[1:])
    if 0 < len(said.split()) <= 7 and any(said == phrase or said.startswith(phrase + " ")
                                          for phrase in COMMIT_NO_HARM):
        return True
    # The phrases that carry the whole agreement on their own. "try that" is the whole line;
    # "try that new thai place on friday" names something for later, and the plan reading is
    # the one that answers it, so a phrase only takes a short tail.
    if bare in COMMIT_ALONE:
        return True
    if any(bare.startswith(phrase + " ") and len(words) <= 5 for phrase in COMMIT_ALONE):
        return True
    if any(bare == phrase or bare.startswith(phrase + " ") for phrase in COMMIT_ALONE_TAIL):
        return True
    lead = strip_leaders(words)
    if lead[:1] and lead[0] in AFFIRM:
        lead = lead[1:]                       # "yes, i will try that"
        if lead[:1] == ["one"]:
            lead = lead[1:]                   # "nice one, might do that"
    if lead[:1] and lead[0] in COMMIT_SUBJECT:
        lead = lead[1:]                       # "ok i will try that"
    if lead[:1] and lead[0] in HEDGED_COMMIT:
        rest = " ".join(lead[1:])
        return any(rest == phrase or rest.startswith(phrase + " ")
                   for phrase in HEDGED_ALONE)
    if lead[:1] and lead[0] in COMMIT_SUBJECT:
        lead = lead[1:]                       # "ok i will try that"
    # Without the "will" the line is not a commitment: "i have a sore throat" and "take vat
    # off 240" open on the same verbs and report something completely different.
    if not lead or lead[0] not in COMMIT_OPEN:
        return False
    lead = lead[1:]                           # "will try that", "gonna give it a go"
    if lead[:1] == ["to"]:
        lead = lead[1:]                       # "going to try that"
    return bool(lead) and lead[0] in COMMIT_TRY


# A line that opens by asking whoever is there ("anyone know", "does anyone have") is a
# question to the room, not a statement about anyone: "anyone know a good plumber" wants a
# recommendation, and "any1 got a spare ticket" wants one too.
ASK_THE_ROOM = frozenset("""anyone anybody somebody someone everyone everybody any1 some1
    every1 evry1 no1""".split())
# "anyone/anybody" almost always ask the room; "someone/everyone" report as often as they ask.
ASK_THE_ROOM_ANY = frozenset("""anyone anybody any1""".split())
ASK_THE_ROOM_WANTS = frozenset("""where if how what which whether why who whom whose
    a an any some""".split())
ASK_THE_ROOM_VERB = frozenset("""know knows knew got have has had recommend recommends
    suggest suggests tried try seen see use uses found find want wants need needs""".split())


def _asks_the_room(stripped):
    """True when an open collective subject asks the room for something.

    "anyone/anybody know a plumber" asks. "someone got hurt", "everyone got the memo",
    "some1 found my keys" are reports: only a question word after the verb ("some1 know
    where to get tyres") turns a someone/everyone line into a question.
    """
    if len(stripped) < 2 or stripped[0] not in ASK_THE_ROOM:
        return False
    if stripped[1] not in ASK_THE_ROOM_VERB:
        return False
    if stripped[0] in ASK_THE_ROOM_ANY:
        return True
    if stripped[1] not in ASK_FOR_A_NAME:
        return False
    return len(stripped) > 2 and stripped[2] in ASK_THE_ROOM_WANTS


# The end of a line can ask for the answer without a question word in it: "i have a wedding in
# june and i need a dress, any ideas". These are the words that make the last clause of a line
# the ask rather than a second thing said.
TAIL_ASKS = frozenset("""ideas idea thoughts thought advice tips tip suggestions suggestion
    recommendations recommendation help pointers""".split())
TAIL_ASK_FILLER = frozenset("""any some more your please a quick few""".split())
# A setup is the situation a person describes before they ask; past a couple of sentences it is
# not a setup any more but two things said, and the reply belongs to the second half anyway.
SETUP_MOST_WORDS = 45
# Clauses that only hold the line together. "thanks, what should i cook tonight" has no setup:
# the person has said nothing about their situation yet.
SETUP_NOTHING = frozenset("""thanks thank you ta cheers hi hello hey morning evening goodnight ok
    okay right so well and but oh ah hmm um yeah yes no anyway alright lol haha lmao""".split())
# Words that join a situation to the question and name nothing in it. A setup made only of these
# is not a situation: "since when have you been about" reads "since" as the setup and "when have
# you been about" as the ask, and the answer is held to a word that says nothing.
SETUP_CONNECTIVES = frozenset("""since because cos cause and but so if when while although
    though as then also plus or with for to of in on at by from that it its this these those
    there here neither nor either both too same me""".split())


def _asks_at_the_end(clause):
    """True when the last clause asks for the answer without a question word."""
    stripped = strip_leaders(clause) or clause
    if not stripped:
        return False
    if _opens_question(stripped):
        return True
    return bool(set(stripped) & TAIL_ASKS) and set(stripped) <= (TAIL_ASKS | TAIL_ASK_FILLER)


# A setup that only frames the question sets nothing up: "never mind, what is the tax deadline",
# "quick question, what time does tesco close", "honestly, what do i do". The situation these
# lines ask about is not in them, and the answer must not be held to the frame.
FRAME_NOT_A_SETUP = re.compile(
    r"^(?: (?:and |but |oh |well |so |ok |okay |right |no )?"
    r"(?:never mind|nevermind|i mean|i meant|you know what i mean|i dunno|dunno"
    r"|not sure|no idea|honestly|sorry|one more thing|one thing|another thing|quick one"
    r"|back to \w+(?: \w+){0,2}"
    r"|of course|fair enough|me too|same here|no worries|anyway|just wondering"
    r"|just asking|quick question|random question|random one|hi|hey|hello|hiya"
    r"|good question)\b(?: .{0,12})?)+$")


# A frame said at the very front of a situation, inside it rather than instead of it: the
# question is still about the situation, and the words of the frame are not part of it.
A_FRAME_IN_FRONT = re.compile(
    r"^(?:(?:hi|hiya|hey|hello|morning|evening|ok|okay|right|well|also|i mean|i meant"
    r"|honestly|sorry|cheers"
    r"|thanks|thank you|no worries|quick one|quick question|random question|random one"
    r"|one more thing|another thing|just wondering|just asking|lol|haha|lmao|anyway"
    r"|bit of a random one|bit random|random one|and|but|so)(?:[\s,.-]+|$))+", re.I)


def _says_nothing_but_the_floor(clause):
    """Whether the clause is only the words that hold a conversation together.

    "thanks, what should i cook tonight" says nothing about a situation, and neither does
    "ok thanks. also, should i worry about the damp patch" - the courtesy and the "also" are the
    turn, not the situation, and the answer must not be held to them.
    """
    words = set(strip_leaders(clause) or clause)
    return not words or words <= (SETUP_NOTHING | SETUP_CONNECTIVES)


def the_setup(line):
    """The situation a line describes before the question it ends on, else None.

    "friends are coming for sunday lunch and one of them is vegan, what can i cook that everyone
    will eat" says the situation and then asks; the ask is what the line is about (it is
    `focus`) and the setup is what the answer has to hold to. Read whole, the situation's words
    are the ones a reply is found by, and the answer goes to the situation instead of the
    question: "my son has a football match on saturday and its freezing, what should he wear" is
    answered with the temperature a baby's room should be, because the only thing the line named
    that a card knows about is the freezing.

    Two questions in one line have no setup ("what is your name and how old are you"): the
    second is another ask, not the condition for the first.
    """
    clauses = [clause for clause in (line.get("clauses") or []) if clause]
    if len(clauses) < 2:
        return None
    ask_at = None
    for index in range(len(clauses) - 1, 0, -1):
        if _asks_at_the_end(clauses[index]):
            ask_at = index
            break
    if ask_at is None:
        return None
    before = clauses[:ask_at]
    if any(_opens_question(clause) for clause in before):
        return None
    if all(_says_nothing_but_the_floor(clause) for clause in before):
        return None
    # The situation's words are the ones a card is found by, so the courtesy or the frame in
    # front of it is not part of it: "hiya, quick one - my 14 year old wants her ears pierced" is
    # a question about the piercing, and "hiya" and "quick one" would only be noise in the search.
    setup = " ".join(" ".join(strip_leaders(clause) or clause) for clause in before)
    setup = A_FRAME_IN_FRONT.sub("", setup).strip(" ,-")
    if not setup:
        # Only the frame was there: "lol ok anyway, whats for dinner" says nothing to hold to.
        return None
    if len(setup.split()) > SETUP_MOST_WORDS:
        return None
    if FRAME_NOT_A_SETUP.match(" " + setup):
        return None
    if not set(setup.split()) - SETUP_CONNECTIVES:
        # "since, when have you been about": the words before the ask join it, they do not
        # describe anything the answer has to hold to.
        return None
    return setup


def _opens_question(clause):
    """True when a clause opens like a question ("is 8gb enough"), not like an order."""
    stripped = strip_leaders(clause) or clause
    if _asks_the_room(stripped):
        return True
    if not stripped or stripped[0] not in QUESTION_STARTS:
        return False
    if (len(stripped) > 2 and stripped[1] in NEGATIONS
            and stripped[1] not in SUBJECT_NEGATIONS
            and stripped[2] not in PRONOUNS):
        # "has not paid", "will not charge" deny a thing; "can't you come earlier" asks one
        return False
    if stripped[0] == "do" and len(stripped) > 1 and stripped[1] in QUESTION_WORDS:
        return False                      # "do what you can" is an order, not a question
    if (stripped[0] in YESNO_STARTS and len(stripped) > 1
            and _verb_form(stripped[1], stripped[0])):
        return False    # "will do", "were thinking of getting a cat": a verb, not a subject
    if len(stripped) > 1 and opens_without_subject(stripped, 0):
        return False    # "am off to bed", "were shattered", "have no idea"
    return True


# What a bare "any tips" is made of: the ask itself, with nothing it is tips about.
TIPS_FRAME = frozenset("""any some few got get need needs needed wanted looking look for
    share send give me us please pls thanks thank you tips tip hints hint pointers pointer
    advice a an the and or to on about this that it is are do have has i u my""".split())


# A line can say a question is coming without asking it: "got a q abt me boiler", "quick
# question about my tax", "can i ask you something". Nothing has been asked yet, so no entry can
# answer it, and the labels above (which all name something wanted *in* the line) are wrong for
# it. What the person wants is room to ask, so it is its own label and the reply invites it.
# `q` and `qs` are how people type "question"; a third-person line ("she asks too many
# questions") is left alone, and a line with the question already in it ("quick q what time do
# you close") is answered rather than invited.
QUESTION_NOUNS = frozenset("q qs question questions query queries".split())
ASKING_VERBS = frozenset("ask asks asked asking".split())
ASK_ABOUT = frozenset("about abt bout re regarding on with something anything".split())
# "any" is left out on purpose: "any questions" is the speaker offering to take them, not
# saying they have one. A line that does have one says so with "got", "have", "quick" or "ask".
ASK_FRAMES = frozenset("""a an and another ask asked asking but can could daft got have has
    hey hi i ive just little may mind need one please pls quick random silly small sorry stupid
    wanna want we would will""".split())
# The verbs that make a question noun an ask that already happened: "she asked me the same
# question three times yesterday" is not a question on its way, and widening the window to the
# noun was reading it as one. "ask" itself is not here: "can i ask a quick question" is coming.
PAST_ASK = frozenset("asked told answered repeated mentioned".split())
ALREADY_ASKED = frozenset("""what why how when where who which whose whether""".split())
# The verb "ask" only says a question is coming when the bot is the one being asked: "can i ask
# about my rads", "i want to ask you something". "i will ask about the shifts", "ill ask her when
# shes back" and "can i ask my boss for a raise" are asking someone else, so nothing is coming
# here and the line is answered (or noted) for what it says.
# The wants and needs are modals here too: "i want to ask about the boiler" and "i need to ask
# about the deposit" are the person asking the bot, and the word after "ask" still has to be
# `you`, `about` or a question noun, so "i want to ask my boss for a raise" stays out.
ASK_MODALS = frozenset("can could may might want wants wanted wanna need needs needed".split())
# The auxiliaries and the adverbs do the same job as the modals here, because the "ask" is not
# always in front of its modal: "im asking about my rads", "i was asking about my rads", "just
# asking about the deposit" and "im just asking about the deposit" are all the person asking the
# bot, and the bot answering those with a shrug was the coldest thing in the conversation. The
# word after "ask" still has to be `you`, `about` or a question noun, so "i was asking her about
# the shifts" is still asking somebody else.
ASK_AUX = frozenset("""am is are was were im be been being just only still actually ever also
    always""".split())
ASK_TARGET = frozenset("you u something somethin anyone anybody".split())
# The verbs that hand the asking over: "give me a quiz question", "ask me a question", "quiz
# me", "throw me a question". The person is the one who will answer, so the question is what
# the line wants, not something it is about to say, and reading it as `question_coming` got it
# the invitation meant for the other direction ("Ask away, I'm listening" to someone who has
# just asked to be asked). Only a hand-over to the speaker counts: `me` and `us` after the verb.
# A promise keeps its reading, because the speaker is the one who will ask: "can i ask you a
# question", "i have a question for you", "let me ask you something".
HAND_OVER_VERBS = frozenset("""give gives gave send sends sent throw throws threw chuck chucks
    hit hits fire fires read reads bring brings brought pass passes offer offers ask asks quiz
    quizzes test tests""".split())
HAND_OVER_TO = frozenset("me us".split())
# What the person puts forward instead of themselves: "test my knowledge", "test our trivia",
# "quiz my brain". A possessive and one of these is the same ask as "quiz me".
HAND_OVER_MINE = frozenset("knowledge trivia quiz quizzes iq memory brain".split())
# The words that can sit in front of the hand-over and still leave the speaker as the one asking:
# a modal or a courtesy. Any other word in front of the verb is a subject of its own, and a third
# person handing the question over is somebody else's business: "she gave me a question to answer",
# "he asked me a question", "my daughter asked me a question" keep the reading they had.
HAND_OVER_LEADS = frozenset("""please pls plz kindly just maybe perhaps ok okay so and then now
    also quick quickly""".split())
HAND_OVER_MODALS = frozenset("can could will would should".split())
# The subjects a hand-over can stand behind and still be the speaker's ask: "can you quiz me" and
# "could u ask me one" put the bot's name in front of the verb. Any subject without a modal in
# front of it is somebody else doing the handing over, and that question is not on its way to
# this person at all: "she quizzed me", "my daughter asked me a question".
HAND_OVER_SUBJECTS = frozenset("you u ya".split())


def _hands_a_question_to_the_speaker(norm):
    """True when the line itself asks for a question to answer: "quiz me", "give me a question".

    The verb has to open the line, or stand behind nothing but a modal or a courtesy, so the
    person is the one doing the asking. "she quizzed me" and "he asked me a question" are a
    question that already happened to somebody, and reading them as a request to be quizzed put
    a general-knowledge question in front of a person who had said nothing of the kind.
    """
    words = [word for word in norm if word and word != "|"]
    for at, word in enumerate(words[:-1]):
        if word not in HAND_OVER_VERBS:
            continue
        handed_to = (words[at + 1] in HAND_OVER_TO
                     or (words[at + 1] in ("my", "our") and at + 2 < len(words)
                         and words[at + 2] in HAND_OVER_MINE))
        if not handed_to:
            continue
        before = words[:at]
        if not before:
            return True                                # "quiz me", "give me a question"
        modal = any(w in HAND_OVER_MODALS for w in before)
        if not all(w in HAND_OVER_LEADS or w in HAND_OVER_MODALS
                   or (modal and w in HAND_OVER_SUBJECTS) for w in before):
            continue                                   # a subject of its own: somebody else
        if modal or not any(w in HAND_OVER_SUBJECTS for w in before):
            return True                                # "can you quiz me", "please ask me one"
    return False


def _asks_a_question_coming(norm, text):
    """True when the line says a question is coming without asking it yet."""
    if not 0 < len(norm) <= 12 or "?" in text or set(norm) & ALREADY_ASKED:
        return False
    if _hands_a_question_to_the_speaker(norm):
        # "give me a quiz question" hands the asking to the bot: the question is what the line
        # wants, not something it is about to say. A third person handing one over ("she gave me
        # a question to answer") is not this person asking, so that line reads as it always did.
        return False
    if norm[0] in {"do", "does", "did", "any"}:
        # "does anyone have any questions" is asking the room, and "any questions" is
        # offering to take them: neither is the speaker saying they have one.
        return False
    if norm[0] in {"have", "has"} and len(norm) > 1 and norm[1] in {"you", "u", "anyone",
                                                                  "anybody", "any", "they"}:
        return False     # "have you got a question" asks the bot, it does not offer one
    for at, word in enumerate(norm[:5]):
        if word == "asked" and at == 1 and norm[0] in {"i", "we"}:
            continue     # "i asked about the boiler" is a past ask, not one on its way
        if set(norm[:at]) & PAST_ASK:
            continue     # "she asked me the same question three times": the ask already happened
        after = norm[at + 1] if at + 1 < len(norm) else ""
        asked_here = (word in ASKING_VERBS
                      and after in ASK_TARGET | ASK_ABOUT
                      and (at == 0  # "ask about the rota": the verb opens the line
                           or any(before in ASK_MODALS | ASK_AUX for before in norm[:at])
                           or after in ASK_TARGET))
        named = word in QUESTION_NOUNS or asked_here
        if not named:
            continue
        if at == 0 or any(before in ASK_FRAMES for before in norm[:at]):
            return True
    return False


def _asks_for_tips(text, norm=()):
    """True when a tip word here asks for advice, not a tip being left or given.

    "any tips for a roast", "tips for a job interview", "got any hints about sourdough" and
    "any tip on painting a door" ask; "a 10% tip", "he tips well", "tip the delivery driver"
    and "the tip of my knife broke" are about a thing or an action.

    A bare "any tips" with nothing in the line it is tips about is not read as an ask: the
    subject it follows in the conversation (a bad night's sleep) is what an answer needs, and
    turning the line into a request only swaps the ack for "I would rather not guess".
    """
    about = [word for word in norm if word not in TIPS_FRAME]
    for match in TIPS.finditer(text):
        before, after = text[:match.start()], text[match.end():]
        if TIPS_AMOUNT.search(before):
            continue
        if TIPS_WANTED.search(before):
            if about:
                return True
            continue
        if match.group(1) in ("tips", "hints", "pointers"):
            if TIPS_SUBJECT.search(before):
                continue
            if TIPS_ABOUT.match(after) or not after.strip(" ?.!,"):
                return True
    return False
# People ask the bot things without the auxiliary: "u think i should quit coffee", "you
# reckon i should go", "you seen this film". The subject is the bot, so the line opens like a
# statement but asks a question.
YOU_WORDS = frozenset("you u ya ur dya".split())
# Only the verbs that ask the bot for its view. A verb that takes an object ("you seen this
# film", "you saw that coming") is a remark as often as a question, so it is left alone.
ASK_VERBS = frozenset("think reckon guess recommend suggest mind".split())
# What comes after the verb decides it: "you think i should quit" asks, "you think too much"
# does not, and "you got this" is a statement of fact.
ASK_FOLLOW = frozenset("""i we us ill im id it its that this these those she he they them
there my your our their should can could will would shall is are was were do does did if
whether what when where who which why how any anything something someone""".split())


def _asks_the_bot(norm):
    """True when the line asks the bot something in the second person."""
    if len(norm) < 3:
        return False
    return (norm[0] in YOU_WORDS and norm[1] in ASK_VERBS and norm[2] in ASK_FOLLOW)

# A person drops the "is there" and the question mark: "any word on the job", "any luck with the
# boiler", "any chance of a refund" are questions about the thing after the link, and read as
# statements they got the shrug instead of an answer ("I'm listening - say more if it helps").
# The word in front is only the kind of answer wanted, never the subject.
# "news" is left out on purpose: asking for the news asks for a briefing, and the honest "I
# can't see the news from here" already answers it. Read as a question about the thing, the bot
# answered it from the small-talk pool instead ("None that I know of. What's been the best bit of
# your week?"), which is no answer to "any news on the trains".
# "progress" and "update" are left out: they ask how a thing the person has in hand is getting
# on ("any progress on the leak", "any update on my parcel"), and no card knows that, so read as
# a question the bot searched and said so - where the nod the line got before was the honest
# reply. The words here ask for something the bot can answer from what it knows.
ANY_ANSWER_WANTED = frozenset("""word words luck idea ideas chance chances
    joy sign signs hint hints intel new else""".split())
ANY_ANSWER_LINKS = frozenset("on about with from of for regarding concerning re".split())
# An ask for a list already asks, so the frame adds nothing to it: "any ideas for a cheap night
# out" is a request for suggestions, and read as a question it lost the list answer and got a
# shrug. Only the plural of a list word is here, because it is the only one of the answer words
# that asks the same thing the frame adds to the others.
ANY_ALREADY_ASKS = frozenset(("idea", "ideas"))

def after_any_link(norm):
    """The words after the link in "any news about X", or () when the line is another shape.

    The tuple is what the line is about: "any word on the job" is about the job, and read whole
    the topic was the word it was asked with. A line that only says the kind of answer wanted
    ("any luck?") has nothing after the link, so it keeps the conversation's subject, and so does
    one that puts the whole ask after it ("any idea how to stop him"): there the ask is the line
    and the thing it is about came from the turns before.
    """
    if not norm or norm[0] not in ("any", "anything"):
        return ()
    if len(norm) < 2 or norm[1] not in ANY_ANSWER_WANTED:
        return ()
    for at in range(2, len(norm)):
        if norm[at] in ANY_ANSWER_LINKS:
            return tuple(norm[at + 1:])
    return ()


def _asks_after_any(norm):
    """True for "any word on the job" and its cousins, which ask without a question mark.

    It has to name the thing after the link. "any luck" and "any ideas" on their own are
    already read as well as they can be, and a bare frame says nothing new about the line.
    """
    if not norm or len(norm) < 2 or norm[1] in ANY_ALREADY_ASKS:
        return False
    about = after_any_link(norm)
    return bool(about) and not _names_a_person(about)


def _names_a_person(words):
    """True when the tail of an "any word about X" names a person rather than a thing."""
    return any(words[at] in OWNS_A_PERSON and words[at + 1] in A_PERSON_NAMED
               for at in range(len(words) - 1))

# Asking the room for a name is asking for a recommendation: "anyone know a good plumber".
ASK_FOR_A_NAME = frozenset("""know knows knew recommend recommends suggest suggests
    found find""".split())


# "best" and "better" ask for a recommendation when they pick out one thing ("the best way",
# "a better option"). After a word that says how somebody is doing they are not asking for
# anything: "i feel better today", "im doing much better", "i want to eat better" are reports
# about the speaker, and an ask read into them makes the bot answer a statement with a hedge.
COMPARATIVE = frozenset(("best", "better"))
DESCRIBES = frozenset((
    "feel", "feels", "feeling", "felt", "do", "does", "did", "doing", "done", "get", "gets",
    "getting", "got", "look", "looks", "looking", "seem", "seems", "am", "is", "are", "was",
    "were", "be", "being", "been", "much", "any", "lot", "sleep", "sleeping", "slept", "eat",
    "eating", "ate", "cope", "coping", "manage", "managing",
))
# A comparative followed by one of these is about how somebody is: "better thanks", "better
# today". "better than" and "the best way" pick something out, so they still ask.
AFTER_COMPARATIVE = frozenset((
    "thanks", "thank", "today", "tomorrow", "yesterday", "now", "tonight", "though", "again",
    "yet", "already", "honestly", "actually", "here", "since", "after",
))
# In front of the word for a person the comparative names that person and picks nothing out: "my
# best friend is getting married in june", "im the best man", "my better half is cooking". Read
# as a request they went looking for advice nobody had offered and got the search hedge - the
# wedding line was answered "I'm not sure about that one, sorry - I'd rather not guess" - while
# the same news with "close" or "oldest" in front of it was answered properly. Only the words a
# person is called, so "the best way", "the best time" and "a better option" still ask.
A_PERSON_AFTER = frozenset("""
    friend friends friend's friends' mate mates mate's pal pals man men woman women half buddy
    bud fella lad matey mother father sister brother son daughter partner wife husband
    wishes regards
""".split())
# "any word from my sister" asks about a person, and nothing in the knowledge base knows her: as
# a question it turned a listening reply into a search punt, which is worse than what it had. A
# tail that names a person is left as it was; a service is not a person and keeps its answer
# ("any word from the vet" reaches the vet card).
A_PERSON_NAMED = (A_PERSON_AFTER_A_POSSESSIVE | KIN | A_PERSON_AFTER
                  | frozenset("""boss bosses manager managers colleague colleagues
                      neighbour neighbours neighbor neighbors teacher teachers doctor
                      doctors gp dentist dentist's""".split()))
OWNS_A_PERSON = frozenset(("my", "our", "his", "her", "your", "their", "me"))
# " or " and "better than" compare things; a bare substring is not enough, because "better
# thanks" contains "better than".
COMPARISON = re.compile(r"(?:\s+or\s+|\bbetter than\b|\binstead of\b|\bversus\b|\bvs\b)")


# "How about you", "what about yourself", "and you": the question turned back on the bot. Read
# as an ordinary question it asks for a fact the bot does not have, and gets "that's beyond what
# I know well, sorry - searching for it will turn up better sources", which is the wrong reply to
# "hbu" after the bot has asked how the day went.
ASKS_IT_BACK = ("how about you", "what about you", "how about yourself", "what about yourself",
                "and you", "and yourself", "you yourself", "what about u", "how about u",
                "how about yours", "what about yours", "and yours")


# "and" is part of the phrase itself ("and you"), so it is not stripped here.
FILLER_BEFORE = ("so", "ok", "okay", "oh", "yeah", "but", "well")
# A filler on the end of the question does not make it a new question: "how about you then".
FILLER_AFTER = ("then", "though", "now", "anyway", "huh", "eh")
# "bout" is how people write "about", but it is also a real word, so it is only read this way
# inside these two phrases, never by the normaliser.
BOUT = {"bout": "about"}


def _ask_words(norm):
    """The words of a line that may be a question turned back, fillers and "bout" removed."""
    words = [BOUT.get(word, word) for word in norm]
    while words and words[0] in FILLER_BEFORE:
        words.pop(0)
    while words and words[-1] in FILLER_AFTER:
        words.pop()
    return words


def _asks_it_back(norm):
    """True when the whole line is the question turned back on the bot."""
    return " ".join(_ask_words(norm)) in ASKS_IT_BACK


# The greetings people type without the words "how are you": "hows u" reads as "how is you",
# "hows things" as "how is things", "how you doing", "what u saying", "u ok". The small-talk
# list holds the phrases as said, and these are the same greeting with the verb or the subject
# written another way, so they are read as a shape instead of one phrase per spelling. Every
# word has to be part of the greeting - "how is life in spain" and "how are you supposed to
# defrost a turkey" name something, so they are questions and not a greeting.
GREETING_ASK_WORDS = frozenset("""
    how what whats is are was were am be been r u ya you your yours yourself yourselves the
    things everything life day days week weekend evening morning night
    going doing doin do been getting keeping saying say much
    today tonight then now lately anyway mate love friend
    all alright ok okay good fine well too so it have has having
""".split())
# The words that stand for the person being asked after: "hows things", "hows life". They are
# the subject of the greeting, so a line has to have one of these or a "you" to be one.
GREETING_ASK_SUBJECT = frozenset("""you u ya your yours yourself yourselves things everything
    life day days week weekend evening morning night""".split())
# A line that is only "u ok", "you alright", "you good" is the same greeting with the "how" left
# off. It is told apart from the short agreement "you too" by the state word, which an agreement
# does not have.
GREETING_ASK_STATE = frozenset("ok okay alright good fine well".split())
GREETING_ASK_ABOUT_SOMETHING = frozenset("with about to for if when on at in".split())
# The short shape has no "how" in it, so the person has to be named for it to be the greeting:
# "you good" and "u ok" ask after the bot, and "good morning" and "good day" are greetings that
# say nothing about how anyone is.
GREETING_ASK_SECOND_PERSON = frozenset("you u ya your yours yourself yourselves".split())
# A greeting that opens on "what" is the "what are you saying" shape and nothing else: the same
# words with a day in them ask the date ("what day is it"), and "what are you doing" asks how
# the bot fills its time, which has its own answer.
GREETING_WHAT_SAYING = frozenset("""what are is r you u ya saying say sayin then now there
    mate all""".split())


def asks_how_i_am(norm):
    """True when the whole line asks the bot how it is, however the greeting is spelled.

    This is the greeting as a shape, so it does not depend on which spelling of it a phrase
    list happens to hold: "how you been", "hows everything" and "what u saying" are the same
    question as "how are you", and the caller that answers one answers them all. A state word
    followed by "with", "about", "to" and the rest asks about something else ("you ok with
    that", "you alright to drive"), so the short shape stands down for it.
    """
    # "hows everything with you" and "how are you doing with yourself": the person adds "with
    # you" to the same greeting, so the tag is dropped rather than read as asking about a thing.
    while len(norm) > 2 and norm[-2] == "with" and norm[-1] in GREETING_ASK_SECOND_PERSON:
        norm = norm[:-2]
    if not norm or len(norm) > 8:
        return False
    words = set(norm)
    if not words & GREETING_ASK_SUBJECT:
        return False
    if norm[0] == "what":
        return words <= GREETING_WHAT_SAYING
    if norm[0] != "how":
        if len(norm) > 4 or not words & GREETING_ASK_STATE \
                or not words & GREETING_ASK_SECOND_PERSON:
            return False
        at = next(index for index, word in enumerate(norm) if word in GREETING_ASK_STATE)
        # The person comes before the state in the greeting ("u ok", "you good"); a line that
        # puts the state first and the person after it agrees with what was just said ("ok nah
        # ur right"), which is not a question about the bot.
        if not any(word in GREETING_ASK_SECOND_PERSON for word in norm[:at]):
            return False
        return not (len(norm) > at + 1 and norm[at + 1] in GREETING_ASK_ABOUT_SOMETHING)
    return words <= GREETING_ASK_WORDS


# A line that ends in one of these is asking to be told it is true, not telling news:
# "im in a union so that should help right", "nowt wrong with the boiler, its just noisy innit".
# "right" is also an adjective ("i cant do anything right", "ur right"), so it only counts
# after a word that can end a statement, never after the words that make "right" a complement.
TAG_RIGHT_NOT = frozenset("""i me my mine you your yours he him his she her hers it its we us our
    ours they them their theirs this that these those there here what who which whose
    all any anything everything something nothing none both each either neither another
    such same very quite too so just still even only also always never ever really pretty
    probably maybe perhaps definitely certainly nearly almost exactly absolutely totally
    completely obviously clearly simply possibly surely indeed actually basically honestly
    literally truly about around much many more most less least enough not no yes yeah ok
    okay right
    is are was were am be been being do does did done have has had having can could will
    would shall should may might must need ought feel feels felt look looks looked seem
    seems seemed sound sounds sounded taste tastes tasted smell smells smelled get gets got
    gotten go goes went gone keep keeps kept turn turns turned make makes made put puts set
    sets work works worked
    off on out up down in back over through round around at
    fine ok okay alright good better worse ready done sorted""".split())
TAG_ENDINGS = frozenset(("right", "innit"))
# A tag on a plan or an event is an announcement, not a claim to be checked: "my nan is coming
# sunday right" wants a warm nod, and the question path answers it with a search hedge. The
# words of a day, a time or a meal are what make it a plan; "i take one of these a day" is a
# routine, and a time after "at" ("picking me up at eight") is when something happens.
TAG_PLAN = GOING_ON_WHEN | frozenset("""day days dinner lunch breakfast tea supper later soon
    next""".split())
TAG_TIME_NUMBER = frozenset("""one two three four five six seven eight nine ten eleven twelve
    half""".split())


# A tag is a question only when the body says something the bot could check: a modal ("that
# should help", "i can get a chargeback") or a fact verb ("she gets the payment", "you said").
# News is not checkable - "i got the job right", "i passed", "my sister had the baby", "we are
# off to spain" - and those want the warm reply they already get, not a search hedge. Nor is a
# plain fact about someone's life ("she works at the hospital right", "you pay at the machine
# right"): the bot cannot check it, so a search hedge is the wrong reply there too. The verb
# has to be one that asks for a rule or a fact to be confirmed, not just any verb.
TAG_CHECKABLE = frozenset("""should shouldnt shall can cant could couldnt will wont would wouldnt
    may might must ought needs need gets said says told tells""".split())


def _tag_tells_a_plan(norm):
    """True when the body of the line before the tag is a plan or an event with a time."""
    body = norm[:-1]
    if any(word in TAG_PLAN for word in body):
        return True
    return any(word == "at" and body[index + 1] in TAG_TIME_NUMBER
               for index, word in enumerate(body[:-1]))


def _tag_checks_a_fact(norm):
    """True when the body before the tag says something the bot could confirm."""
    body = norm[:-1]
    for index, word in enumerate(body[:-1]):
        # "it should be fine innit", "we should be there by six right": a modal before "be" is
        # how something is expected to turn out, not a fact the bot can check. The question path
        # answers those with a search hedge, which is worse than the warm nod they had.
        if word in TAG_CHECKABLE and body[index + 1] == "be":
            return False
    return any(word in TAG_CHECKABLE for word in body)


def _asks_for_confirmation(norm):
    """True when the line ends by asking the other person to agree with it.

    The tag is not a question word, so the line used to read as news and got "Noted: ..."
    or "I'm listening" instead of an answer. Only the end of the line is read, and "right"
    needs a word in front that can end a statement: "im board right" is a tag, while
    "im doing everything right", "ur right" and "i cant do anything right" are not.
    """
    if len(norm) < 3 or norm[-1] not in TAG_ENDINGS:
        return False
    if (_opens_question(norm) or _asks_the_bot(norm) or _tag_tells_a_plan(norm)
            or not _tag_checks_a_fact(norm)):
        return False
    if norm[-1] == "right":
        # A word that is doing something is the complement, not a statement the tag agrees
        # with: "i keep getting the timing right", "nothing is going right", "turn right".
        # The base forms are in TAG_RIGHT_NOT; the -ing and -ed family is a rule.
        if norm[-2].endswith(("ing", "ed")):
            return False
        return norm[-2] not in TAG_RIGHT_NOT
    return len(norm) >= 4


# The same question with the day named: "how about your day", "what about your weekend", "was
# your day good". "your" makes the day the bot's own, so nothing in the world is being asked
# either - read as an ordinary question it goes to the knowledge base and gets "I don't know
# enough to answer that honestly". Only a day word after "your" counts, and the line has to end
# there (or on how it went), so "what about your day at the beach" is still about the beach.
BOT_DAY_WORDS = "|".join(("day", "weekend", "week", "evening", "morning", "night"))
BOT_DAY_SHAPES = tuple(re.compile(pattern.format(day=BOT_DAY_WORDS)) for pattern in (
    r"(?:how|what) about (?:your|ur) (?:{day})(?: (?:been|going|gone|so far))?",
    r"(?:how|what) about yours",
    r"and (?:your|ur) (?:{day})(?: (?:been|going|gone|so far))?",
    r"and yours",
    r"(?:how|what)(?:s|'s| is| was| are| were) (?:your|ur) (?:{day})"
    r"(?: (?:been|going|gone|good|ok|okay|fine|busy|alright|so far))?",
    r"(?:was|were|is|are|did) (?:your|ur) (?:{day})(?: (?:good|ok|okay|fine|busy|alright|nice))?",
    r"(?:did|have|had) you have a (?:good|nice|ok|okay|busy|long|lovely|great) (?:{day})",
    r"hope (?:you had|youre having|you are having) a (?:good|nice|lovely|great|ok|okay) (?:{day})",
))


def _asks_about_the_bot_day(norm):
    """True when the whole line asks the bot about its own day."""
    words = _ask_words(norm)
    if not words:
        return False
    line = " ".join(words)
    return any(shape.fullmatch(line) for shape in BOT_DAY_SHAPES)


# The indefinite a line asks about fills its time with: "you doing anything tonight", "u up to
# something this weekend". The bot's own doings read from the front, and only these words make
# it that ask - "you up to much" and "what are you up to tonight" are the manners question the
# warmth pool already answers, and the honest short answer is colder than the warm one there.
ASKS_IF_ANYTHING = frozenset("anything something nothing owt".split())
# The same ask with the verb named: "how do you spend your time", "what do you do with your day",
# "how do you fill your evenings". The person is asking what the bot's day is made of, so the
# question is read as the bot's own doings rather than left to the search hedge.
SPENDS_ITS_TIME = re.compile(
    r"\b(?:how|what)\b[^.]{0,24}?\b(?:spend|spends|spending|fill|fills|filling|use|uses)\b"
    r"[^.]{0,20}?\b(?:your|you)\b[^.]{0,16}\b(?:time|day|days|evening|evenings|hours?|"
    r"life|nights?)\b|\b(?:what do|what does)\s+you\s+do\s+(?:all\s+)?(?:day|with your|"
    r"during the|in the)\b")


def _asks_how_it_spends_its_time(norm):
    """True for "how do you spend your time" and its neighbours, in the words they are typed."""
    if not norm or len(norm) > 12:
        return False
    words = set(norm)
    if not words & {"you", "u", "ya", "your", "ur"}:
        return False
    return bool(SPENDS_ITS_TIME.search(" ".join(norm)))

# A short line asking whether the bot is about at a time: "you busy tonight", "u got much on
# tonight", "you about tomorrow", "you free this weekend". The line has the bot as its subject and
# a time, and that is the whole of it - read as nothing in particular it got the opening line
# ("I'm a chatbot - here to help and chat"), which is no answer to somebody working out whether
# there is anybody here this evening. The bot's own doings answer it, as they answer the same ask
# with an indefinite in it.
ABOUT_AT_A_TIME = frozenset("""tonight tomorrow today later weekend weekends morning afternoon
    evening night now soon week""".split())
# The words that ask it without a time: "you busy", "u free".
FREE_OR_BUSY = frozenset("busy free".split())
# A short ask about the bot itself has no first person in it: "im busy tonight" is the person's
# own evening and nothing to do with the bot.
FIRST_PERSON = frozenset("i im id ive me my mine we us our".split())
# The words that make a short line the manners question rather than this ask, kept with the arm
# that reads them so the two cannot drift.
MANNERS_WORDS = frozenset("up doing much keeps keeping".split())


def _asks_whether_the_bot_is_about(norm):
    """True for "you busy tonight" and its neighbours: the bot, a time, and nothing else."""
    if not norm or len(norm) > 6:
        return False
    words = set(norm)
    if not words & {"you", "u", "ya", "ur", "your"}:
        return False
    if words & FIRST_PERSON:
        return False
    if words & MANNERS_WORDS:
        # "what are you up to tonight" and "you up to much" are the manners question, and the warm
        # answers they have ("No plans. I'm around if you want to talk something through.") are
        # better than the bot's honest nothing.
        return False
    return bool(words & ABOUT_AT_A_TIME) or bool(words & FREE_OR_BUSY)


MANNERS_OPENERS = frozenset("what whats wats".split())
# When the same ask names a time: "what are you up to later", "what are you up to this weekend",
# "what are you doing after work tomorrow". Every other word of the line still has to be the ask
# itself, so "what are you doing at the weekend with the kids" stays a line about the kids.
WHEN_IN_THE_ASK = frozenset("""later tomorrow morning afternoon evening night weekend weekends
    week weekdays this these days coming soon next""".split())
# The spellings of "what are you" said out loud: "watcha up to", "whatcha doing". No dictionary
# has any of them, and the words after them say which is meant - "up to" and "doing" are this
# ask, "mean" is not.
SAYS_WHAT_ARE_YOU = frozenset("watcha whatcha wotcha watchu whatchu watchya whatchya".split())


# The words "what keeps you busy" is made of: the ask, the verb the other way round, the person,
# "busy", and the handful of words a person adds to the same question.
KEEPS_BUSY_SHAPE = frozenset("""what whats wats is keeps keeping you u ya busy so then mate
    today tonight now lately these days though anyway""".split())


def the_manners_question(norm):
    """True when the whole line asks how the bot is filling its time, however it is spelled.

    "what are you up to", "whatcha doing today", "watcha up to mate". The same words put any
    other way are a different ask: "u up" is whether anyone is there, and "what are you doing
    with that" is about the thing in the person's hand, so the line has to open on `what` and
    be made of nothing but the ask itself.
    """
    # A greeting in front of the ask is the same ask: "hey whatcha doing today", "hiya what are
    # you up to". Read as anything else the lead word made the opener test fail, and the ask
    # then read as a plan about the person's own week ("Pick two things and put them in the diary
    # by Friday") - black-lantern's find on this row.
    lead = 0
    while lead < len(norm) and norm[lead] in UP_TO_LEADS:
        lead += 1
    norm = norm[lead:]
    if not norm or (norm[0] not in MANNERS_OPENERS and norm[0] not in SAYS_WHAT_ARE_YOU):
        return False
    words = set(norm)
    if not {"you", "u", "ya"} & words and norm[0] not in SAYS_WHAT_ARE_YOU:
        return False
    if "been" in words and {"do", "doing"} & words:
        # "what have you been doing" is the literal past ask - the bot has no yesterday, and the
        # answer that says so is the bot's own doings, not a greeting.
        return False
    if "busy" in words and {"keeps", "keeping"} & words:
        # "what keeps you busy", "whats keeping you busy": the same ask with the verb the other
        # way round. The shape is named, because "what keeps you up at night" says "up" and is a
        # question about what worries somebody, not about how they fill the day.
        return words <= KEEPS_BUSY_SHAPE
    if not {"up", "doing", "doin", "do", "at", "been"} & words:
        return False
    if words & WHEN_IN_THE_ASK and not {"up", "doing", "doin", "at", "been"} & words:
        # "what do you do on weekends" asks what the bot is for, and the capabilities card is
        # that answer. Only the ask that names a time *and* a doing is this one: "what are you
        # up to later", "what are you doing on saturday".
        return False
    return all(word in DOING_FILLER or word in WHEN_IN_THE_ASK for word in norm)


# "What's new with you", "anything new with you", "what's going on with you", "what's been
# happening with you": the same ask as "what have you been up to" - the bot's own side of the
# chat - said with the word "new" or with "going on" instead of a verb of doing, so neither
# reader below saw it. All of them went to the search hedge ("That's beyond what I know well,
# sorry. Searching for it will turn up better sources") or to the nod, while the ask one word
# away from it ("what have you been up to") got the honest answer.
#
# The shape is closed by its own vocabulary and by the owner: the words have to be the ask, the
# "new"/"going on"/"happening" frame, and a word for the bot, with nothing named after it. That
# keeps "what's new with my car", "what's new at work", "what's new in town", "what's new with
# the world" (the news) and "what's new with the kids" out of it: every one of them names a thing
# the bot has no side of. A span of time ahead ("what's new with you tonight") is a presence
# check, and it keeps its own reading.
# "whats" is read as two words ("what is") and "whats been" as "what has been", so the two
# little verbs the fixer puts back are here beside the ask words.
NEW_ASK_WORDS = frozenset("""what whats is was has have u you ya your yours with in on going
    happening been new anything something nothing else tell me us mate pal friend hey hi hello
    so and now then lately world side day days weekend week""".split())
NEW_FRAME = frozenset("new going happening been".split())
NEW_ASK_AHEAD = frozenset("""tonight tomorrow later next saturday sunday monday tuesday
    wednesday thursday friday""".split())


def _asks_what_is_new_with_the_bot(norm):
    """True for "what's new with you" and the same ask in the words people type it in."""
    words = set(norm)
    if not words or len(norm) > 9:
        return False
    if not words & {"you", "u", "ya", "your", "yours"}:
        return False
    if not words & NEW_FRAME:
        return False
    if words & NEW_ASK_AHEAD:
        return False
    return words <= NEW_ASK_WORDS


def _asks_what_the_bot_is_doing(norm):
    """True for a line whose whole content is asking the bot how it is filling its time."""
    if not norm or len(norm) > 10:
        return False
    if not ({"doing", "do"} & set(norm) or norm[-1] in ("to", "much", "on")
            or "up" in norm):
        return False
    # "going on" also names things happening in the world, so a line that says when it is
    # asks what is on: "anything going on tonight" and "much going on this week" are about the
    # evening, not about the bot. Without a time word it is the bot's own doings.
    if {"going", "on"} <= set(norm) and set(norm) & GOING_ON_WHEN:
        return False
    if all(word in DOING_FILLER for word in norm):
        return True
    return _asks_what_the_bot_has_been_doing(norm)


def _asks_what_the_bot_has_been_doing(norm):
    """True for the same ask with the time named, as long as that time has already gone.

    "what did you do yesterday", "what were you up to at the weekend", "where were you last
    night": the bot has no yesterday and no Saturday, so the honest answer is that it has
    nothing of its own to report. Read as ordinary questions these went to the search hedge, to
    the weekend-plan advice, or to "we're still at the beginning" as if the person had said what
    they did. A day still to come is not this ask (`STILL_COMING`), and neither is a line that
    puts the past auxiliary to work on a thing: "what did you do with the leftover paint".
    """
    words = set(norm)
    if not words & {"you", "u", "ya", "your", "yours"}:
        return False
    if words & STILL_COMING:
        return False
    if not words & BEEN_SAID:
        return False
    # A day behind them and a past auxiliary are what make it the same ask as "what have you
    # been doing": "what do you do at the weekend" is a different question, and the manners
    # question in the present tense ("what are you up to", "wuu2") is a different one again.
    if not words & {"did", "done", "been", "were", "was", "had"} and not words & BEEN_WHEN:
        return False
    if ("where" in words and words & SPENT_TIME
            and words & {"have", "has", "been", "were", "was"}):
        # "where have you been all day", "where have you been hiding", "where were you last
        # night": a place question about time the bot is supposed to have spent. Read as a
        # place, the chat module's address line does not fit ("nowhere you could visit" answers
        # where it is, not where it was); read as nothing, all three went to the search hedge.
        return True
    # The english `do` has to be in the line, or the ask is about something else. Two readers
    # sent back the same two families without it: "where were you" is a question about a place
    # (the bot answers it by saying it has no address, which is the answer) and "what have you
    # been up to" is a greeting, whose warm answer is the small-talk one. "what have you been
    # doing", "what did you do yesterday" and "what did you get up to" keep the ask they had.
    if not words & {"do", "does", "did", "done", "doing"}:
        return False
    return all(word in DOING_FILLER or word in BEEN_WHEN or word in BEEN_SAID for word in norm)


def _wants_a_recommendation(norm, text):
    """Whether the words ask the bot to pick something out, rather than describe the speaker."""
    if set(norm) & COMPARATIVE and COMPARISON.search(" " + text + " "):
        return True                  # "which is better, tea or coffee" is picking, not reporting
    for index, word in enumerate(norm):
        if word not in COMPARATIVE:
            continue
        before = norm[index - 1] if index else ""
        after = norm[index + 1] if index + 1 < len(norm) else ""
        if after in A_PERSON_AFTER and not (
                after in ("man", "woman") and norm[index + 2:index + 3] == ["for"]):
            continue                 # "my best friend", "im the best man" name somebody
        if before not in DESCRIBES and after not in AFTER_COMPARATIVE:
            return True
    return bool(set(norm) & (RECOMMEND - COMPARATIVE))


# A thank you is said *for* something, and that something is what the bot has already given:
# "thanks for the advice", "cheers for the pointers", "thanks a lot for all your ideas". The
# advice word there is the object of "for", so it is not a request for one - but read as a
# request it turned a plain thank you into a question and the bot answered it with the search
# hedge. Only the words a gratitude "for" takes are the object, so a request of its own after
# the thanks is still an ask ("thanks, any advice for my sleep", "thanks for the tip, now how
# do i clean the oven").
GRATITUDE_OBJECT = frozenset("""a an the all any some your his her their our my that this these
    those lot lots loads much very so really again both few bit kind sort great good helpful
    useful nice lovely brilliant ever indeed awfully terribly truly too help support""".split())
# The words a thank-you uses to join one thing it is for to the next: "thanks for the help and
# the advice", "thanks for the tips, the pointers". None of them names an ask.
GRATITUDE_JOINERS = frozenset(["and", "plus", ",", "&"])
# The words that can open the thing a thank you is for but cannot carry on inside it: "thanks
# for the pointers, any suggestions for tomorrow" asks, and the comma is not even in `norm`, so
# without this the object walks over "any suggestions" and eats the ask. They are only asked
# about past the first word, so "thanks for any advice" still thanks.
GRATITUDE_ASK_AGAIN = frozenset("any some what how which more another".split())
TIP_WORDS = frozenset("tips hints pointers tip hint pointer".split())
COURTESY_WORD = frozenset(word for phrase in THANKS for word in phrase.split())


def _the_thing_a_thank_you_is_for(norm):
    """The (start, end) of the words a thank you's "for" takes, or None when it is not one.

    "thanks for the advice", "thanks a lot for the pointers", "thank you for the ideas": the
    words before the "for" are the courtesy itself and words that only measure it.
    """
    if not norm or not _starts_with(norm, THANKS):
        return None
    for at, word in enumerate(norm[:5]):
        if word != "for":
            continue
        if any(w not in COURTESY_WORD and w not in GRATITUDE_OBJECT for w in norm[:at]):
            continue                     # "thanks, any advice for my sleep": not a gratitude for
        end = at + 1
        while end < len(norm) and norm[end] in GRATITUDE_OBJECT | RECOMMEND | TIP_WORDS:
            if end > at + 1 and norm[end] in GRATITUDE_ASK_AGAIN:
                break                # "thanks for the tips any ideas for tomorrow" asks
            end += 1
        if end > at + 1:
            # The thing thanked for can be a list of them, so a joiner followed by more of the
            # same words stays inside the object. "thanks for the advice and how do i clean the
            # oven" stops at "and", because "how" is not one of those words.
            while end + 1 < len(norm) and norm[end] in GRATITUDE_JOINERS:
                run = end + 1
                while run < len(norm) and norm[run] in GRATITUDE_OBJECT | RECOMMEND | TIP_WORDS:
                    run += 1
                if run == end + 1:
                    break
                if run < len(norm) and norm[run] == "for":
                    break                # "thanks for the tips and any ideas for dinner" asks
                end = run
            return at, end
    return None


def _asks(norm, text):
    """What the line asks for, as a set of short labels."""
    thing = _the_thing_a_thank_you_is_for(norm)
    if thing:
        # A thank you is said for something, and that something names no ask of its own:
        # "thanks for the ideas" thanks the bot, where "thanks, any ideas for dinner" asks.
        # Everything outside the object still asks - "thanks for the tip, now how do i clean
        # the oven" is a question about the oven - so those words are what the labels come from.
        left = norm[:thing[0]] + norm[thing[1]:]
        return _ask_labels(left, " " + " ".join(left) + " ")
    return _ask_labels(norm, text)


# The figures in a line that are a date and not a quantity: "the 3rd of may", "3 may", "may 3",
# "on the 21st". They are taken out before a line is read for arithmetic, so a birthday is never a
# sum to work out (see `_ask_labels`).
A_DATE_FIGURE = re.compile(
    r"\b\d{1,2}(?:st|nd|rd|th)\b"
    r"|\b\d{1,2}\s+(?:of\s+)?(?:january|february|march|april|may|june|july|august|september|"
    r"october|november|december)\b"
    r"|\b(?:january|february|march|april|may|june|july|august|september|october|november|"
    r"december)\s+\d{1,2}\b",
    re.I)


def _a_bare_definition(text):
    """True for a bare "what is X" that asks what the thing is, and False for the rest.

    The head word decides most of it (see NOT_A_DEFINITION_HEAD), and a possessive head - "what
    is peru's capital" - asks about somebody's thing rather than the meaning of a word.
    """
    found = BARE_DEFINITION.search(text)
    if not found:
        return False
    head = found.group(1).lower()
    if head.endswith(("'s", "\u2019s")) or re.search(r"\d", head):
        return False
    # The apostrophe is gone by the time the line is read, so "peru's capital" arrives as "peru s
    # capital": a lone "s" after the head is the possessive, and the line asks about a thing that
    # belongs to something rather than what a word means.
    if re.match(r"\s*s\b", text[found.end():]):
        return False
    return head not in NOT_A_DEFINITION_HEAD


def _ask_labels(norm, text):
    """The asks the line itself makes, gratitude already taken off."""
    asks = set()
    words = set(norm)
    if _asks_the_room(norm) and norm[1] in ASK_FOR_A_NAME:
        asks.add("recommend")
    if "how" in words:
        if "long" in words:
            asks.add("how_long")
        elif "much" in words or "many" in words:
            asks.add("how_much")
        elif "often" in words or "frequently" in words:
            asks.add("how_often")
        else:
            asks.add("how")
    for label in ("what", "why", "when", "where", "who", "which"):
        if label in words:
            asks.add(label)
    if _wants_a_recommendation(norm, text) or _has_any(text, RECOMMEND_PHRASES) \
            or _asks_for_tips(text, norm):
        asks.add("recommend")
    if _has_any(text, STEPS) or STEPS_WORD.search(text) or _asks_for_help(text):
        asks.add("steps")
    if _has_any(text, OPINION):
        asks.add("opinion")
    if _has_any(text, COMPARE) or words & {"vs", "versus"}:
        asks.add("compare")
    if not ASKS_ABOUT_A_PERSON.search(text) and (
            _has_any(text, DEFINITION) or _a_bare_definition(text)):
        asks.add("definition")
    # "the 3rd of may" is a date, not a sum: an ordinal, or a day of a month, names a position on
    # a calendar, and counting it as arithmetic made the birthday line ask for an amount. What is
    # left after the dates are taken out is the arithmetic in the line.
    digits = bool(re.search(r"\d", A_DATE_FIGURE.sub(" ", text)))
    if words & MATH_WORDS or "%" in text or (digits and ({"of", "each", "per", "split"} & words)):
        asks.add("maths")
    if _has_any(text, (" or ",)) and not two_ends_of_one_scale(text) \
            and not _turns_the_pair_down(text):
        asks.add("choice")
    if words & {"list", "ideas", "options", "examples", "suggest"}:
        asks.add("list")
    if words & {"write", "word", "rewrite", "draft"}:
        asks.add("write")
    if _asks_a_question_coming(norm, text):
        asks.add("question_coming")
    return sorted(asks)


# A line with no verb and no self in it that just names a thing and a place is a request for
# options, not news: "restaurants in edinburgh", "museums in rome", "things to do in lisbon with
# kids". The person is asking what to pick there. It is never a reply to the bot's last turn.
NOUN_REQUEST_MAX = 8
PLACE_WORD = frozenset("in at near around from to".split())
NOUN_REQUEST_SELF = frozenset("""i me my mine we our us myself your you it its he she they
    there here that this""".split())
VERBISH = frozenset("""is are was were am be been being have has had do does did done go goes
    going went gone plan planning planned visit visiting visited stay staying live living work
    working like love hate want need get got take took make made book booked fly flying drive
    driving rent rented see saw seen eat ate eaten drink drank cook cooked watch watched play
    played read come came coming think thought know knew say said tell told try tried start
    started stop stopped leave left move moved should would could will can may might must""".split())


# After an auxiliary a bare verb or a progressive form is the verb of the clause, not the thing
# it is about: "will do", "might do that", "were thinking of getting a cat". A subject is a
# pronoun, a determiner or a noun, so a question never puts one of these right after the
# auxiliary. Words that are as often nouns are left out ("is work busy", "is help available",
# "is cooked chicken still ok"): the -ed forms are adjectives there, and the bare ones are
# things.
BARE_VERBS = frozenset("""do give get go try keep sort call tell know feel be been have wait
    stop start find leave come put use take see say think love like want""".split())
VERB_FORMS = BARE_VERBS | frozenset(
    stem[:-1] + "ing" if stem.endswith("e") else stem + "ing"
    for stem in VERBISH - {"is", "are", "was", "were", "am", "be", "been", "being"}
    if len(stem) > 2 and stem.isalpha())


# The same verbs said of a thing rather than by the person: "the heating comes on", "it settles at
# the top", "the pump catches". A report about the thing is written that way, and the -ed and -ing
# tests miss it, so the word was read as the part of the answer the follow-up named - "its a
# banging sound when the heating comes on" after the banging card came back "Same for comes: ...",
# a lead-in about a word nobody was talking about. The tense of a verb is the same verb.
def _third_person(stem):
    if len(stem) > 2 and stem.endswith("y") and stem[-2] not in "aeiouy":
        return stem[:-1] + "ies"
    if stem.endswith(("s", "sh", "ch", "x", "z", "o")):
        return stem + "es"
    return stem + "s"


VERB_THIRD = frozenset(
    _third_person(word) for word in (VERBISH | BARE_VERBS)
    if word.isalpha() and word not in {"is", "are", "am", "be", "been", "being"})


# An -ing word after a present or a modal auxiliary is the subject of the question, not the
# clause's verb: "is cooking with gas cheaper", "will cooking it longer make it tender" and
# "is running water safe to drink" all ask something. Only a past or plural auxiliary leaves the
# person out, which is where the progressive verb shows up: "were driving up to scotland".
PAST_AUX = frozenset("""was were been had has have""".split())


def _verb_form(word, auxiliary=""):
    """True when this word is a verb here rather than a thing the question is about."""
    if word.endswith("ing") and auxiliary not in PAST_AUX:
        return False
    return word in VERB_FORMS


def noun_phrase_request(line):
    """True for a verbless line that names a thing and a place: a request for options there."""
    words = [word for word in line["norm"] if word]
    if not words or len(words) > NOUN_REQUEST_MAX or line["signals"]["question_mark"]:
        return False
    if any(word in NOUN_REQUEST_SELF for word in words):
        return False
    # An infinitive is not a verb here: "things to do in edinburgh" asks what to do there.
    if any(word in VERBISH and words[index - 1:index] != ["to"]
           for index, word in enumerate(words)):
        return False
    return len(words) >= 2 and any(word in PLACE_WORD for word in words)


# An interest the person has taken up, said in the shapes that carry no other clue: "im into
# running", "im really into baking at the moment", "ive got into yoga", "im getting into
# gardening". The knowledge base already answers the asking shape ("i want to get into running"
# gets the run-walk plan) because the word "get into" is in its key, but it cannot take the bare
# "into": "shes 30 and into running" is a detail about somebody else, not a request for a plan.
# So the reading says whose interest it is and what it is in, and a module can answer the
# person's own without widening the word.
INTEREST_HEAD = re.compile(
    r"^\W*(?:i\s*m|im|i am|i\s*ve|ive|i have|we\s*re|were|we are|i\s+got|we\s+got)\s+"
    r"(?:really\s+|so\s+|very\s+much\s+|very\s+|well\s+|quite\s+|now\s+|also\s+"
    r"|totally\s+|still\s+)?"
    r"(?:(?:getting|got|started)\s+(?:back\s+)?|back\s+)?(?:into|in to)\s+(?P<thing>[a-z' -]+?)\s*[.!]*$",
    re.I)
# The thing has to be an activity, not a person ("im into him"), a fix they are in ("im into
# debt") or a phrase that is not an activity at all ("i got into a fight", "into trouble").
INTEREST_NOT = frozenset("""not a an the this that these those some any my our his her their your
    him her them us me you it fight fights argument arguments row rows trouble debt debts
    hospital bed prison it him""".split())
# How often or when, said after the activity ("im into netball on wednesdays", "im into parkrun
# every saturday"): the day is when they do it, not part of its name, so the reply names the
# activity alone. A day that is the activity keeps its line ("im into sunday roasts" is cooking).
INTEREST_TAIL = re.compile(
    r"\s+(?:at the moment|right now|now|these days|lately|recently|a lot|lots|again"
    # "im into baking too" is into baking: the "too" belongs to the line, not to the name of
    # the thing, and a reply that says "the baking too" reads as if somebody else were baking.
    r"|too|as well|also"
    r"|on\s+(?:mon|tues|wednes|thurs|fri|satur|sun)days?"
    r"|every\s+(?:day|week|weekend|morning|evening|night|"
    r"mon|tues|wednes|thurs|fri|satur|sun)days?"
    r"|at\s+the\s+weekend|after\s+work|in\s+the\s+evenings?)$", re.I)


# "ive got into yoga" and "im getting into gardening" are somebody starting out; "im into
# running" is somebody already at it. The two want different answers - the plan for a beginner
# against the tip for the thing they do - so the reading keeps them apart (`shape`).
STARTED_OUT = re.compile(r"\b(?:got|getting|started)\s+(?:back\s+)?into\b", re.I)


# Going back to something they used to do is a taking up of its own: "i got back into chess"
# wants "what got you back into it", not "what made you start", which reads as if they never had.
BACK_INTO = re.compile(r"\bback\s+into\b", re.I)


def taking_up(line, read=None):
    """The activity the person is into, else None: `{"text", "words", "shape"}`.

    `text` is the activity as typed ("im really into baking at the moment" -> "baking"), `words`
    the same split up for matching, and `shape` is "started" for somebody beginning it ("ive got
    into yoga", "im getting into gardening") and "doing" for somebody already at it ("im into
    running").
    """
    text = str((read or {}).get("clean") or line.get("text") or "")
    # The apostrophe is dropped here only, so "i'm", "i’m" and "im" are one shape and the word
    # after "into" is read as typed.
    text = re.sub(r"['’]", "", text).strip()
    if not text or " not " in " %s " % text.lower():
        return None
    if re.match(r"\W*(?:am|is|are|was|were)\s+(?:i|we|you|they|he|she)\b", text, re.I):
        return None  # "are you into running" asks about them, not the person telling you
    match = INTEREST_HEAD.match(text)
    if not match:
        return None
    thing = INTEREST_TAIL.sub("", match.group("thing").strip(" .,!?")).strip()
    words = thing.split()
    if not words or len(words) > 4:
        return None
    if words[0] in INTEREST_NOT or (len(words) > 1 and words[1] in INTEREST_NOT):
        return None
    thing = thing.lower()
    if not thing:
        return None
    return {"text": thing, "words": words,
            "shape": "started" if STARTED_OUT.search(text) else "doing",
            "back": bool(BACK_INTO.search(text))}


# A clause that opens like a question can be the end of the sentence instead, when the clause
# before it only names the thing: "my cat, milo, is shy with visitors" says how the cat is, and
# "the boiler, which is old, keeps cutting out" says what the boiler does. The commas split the
# name of the thing off from what is said about it, and neither half is a question. A greeting
# or a "sorry" in front of a real question is not a subject, so "hi, is the shop open" and
# "sorry, where is the station" still ask, and so does "my car, is the battery dead": there the
# clause after the comma is the person's question about the car.
WH_CONTINUES = frozenset("which who whom whose that".split())
NOT_A_SUBJECT = frozenset(
    [word for phrase in GREETINGS + THANKS + FAREWELLS for word in phrase.split()]
    + list(ACK) + list(LAUGH)
    + "sorry please oh ah well right yes no yeah yep nope hmm and so but also just".split())
SUBJECT_OF_ITS_OWN = PRONOUNS | frozenset(
    """anyone someone everyone nobody anybody somebody one""".split())


def _bare_subject(clause):
    """True when a clause only names the thing: "my cat", "the boiler", "milo".

    A clause with a verb in it says something about the thing, so a question after it is the
    person's own question ("my back hurts, can i take ibuprofen").
    """
    if not clause:
        return False
    for word in clause:
        if word in VERBISH or (len(word) > 3 and word.endswith(("ed", "ing"))):
            return False
    first = clause[0]
    if first in DETERMINERS:
        return True
    return len(clause) == 1 and first not in NOT_A_SUBJECT


def _continues_the_sentence(clauses, index):
    """True when this clause only finishes the sentence the clause before it started."""
    if index < 1 or not _bare_subject(clauses[index - 1]):
        return False
    clause = clauses[index]
    if any(word in SUBJECT_OF_ITS_OWN for word in clause[1:3]):
        return False                       # "my car, does it start"
    if clause[0] in WH_CONTINUES:
        return True                        # "the boiler, which is old"
    if clause[0] not in YESNO_STARTS:
        return False
    # "my cat, milo, is shy with visitors": a name sits between the noun phrase and what is
    # said about it. Without the name there is nothing for the clause to belong to.
    return index >= 2 and _bare_subject(clauses[index - 2])
# A word that turns the feeling after it the other way: "not fine" is not fine, "not bad" is
# good. Checked a few words back, so "i am really not fine" and "im not feeling great" count.
NEGATORS = frozenset("""not no never neither nor hardly barely cannot cant dont doesnt didnt
    isnt arent wasnt werent wont wouldnt shouldnt couldnt aint nothing""".split())
# A negator turns the next feeling word and nothing else, and it reaches over the words that
# only say how much ("not really fine", "not bad at all"). Any other word in between ends it,
# because there the negator belongs to that word and not to the feeling: "i cant stop crying"
# and "i cant help feeling sad" are more of the feeling, not less, and "she shouldnt be living
# alone" is a worry, not a comfort.
NEGATION_SKIP = frozenset("""really very so too much quite pretty true honestly actually
    totally completely absolutely seriously still even at all bit little kind sort feeling
    feel felt a an the""".split())

# A feeling word the line takes back. "im not stressed", "im not in pain", "im not having a
# panic attack": the negator reaches over the words that only say how, how much or which one
# ("not really sad", "not having a panic attack", "not in any pain"), and over nothing else -
# "i cant stop crying" is still the crying. Read as the state itself, a denial was the opposite
# line: "im not stressed" got the good-news line and "im not having a panic attack" got the
# panic card.
DENY_BETWEEN = NEGATION_SKIP | frozenset("""in at on for under any more most all about much
    having had havent been being be am is are was were got get getting a an the""".split())
DENY_BEFORE = re.compile(
    r"\b(?:" + "|".join(sorted(NEGATORS)) + r")\b"
    r"(?:\s+(?:" + "|".join(sorted(DENY_BETWEEN)) + r")){0,4}\s*$", re.I)


def denied(text, cue):
    """True when this feeling word is the thing the line rules out, not the state it is in."""
    for match in re.finditer(r"\b" + re.escape(cue) + r"\b", text):
        if DENY_BEFORE.search(text[:match.start()]):
            return True
    return False


def _a_state_of_the_speaker(norm, index):
    """True when the word at `index` is said about how the speaker is: "im ok", "im not ok",
    "we are doing ok". The words in between are the verb, a negator and the amount."""
    verb = False
    back = index - 1
    while back >= 0 and index - back <= 4:
        word = norm[back]
        if word in SPEAKER:
            return verb
        if word in STATING_VERB:
            verb = True
        elif word not in NEGATORS and word not in NEGATION_SKIP:
            return False
        back -= 1
    return False


# Someone in authority wanting a word is a kind of line of its own. "my sons teacher wants a
# word", "the council have written to me", "hr want to see me on friday" are not trouble (nothing
# has gone wrong yet), not news worth congratulating and not a fact to file away; the person is
# waiting to find out what it is about, and every one of them came back as an echo of the line.
# So the reading names the shape: someone who can call you in, and what they want (a word, a
# meeting, a letter, a phone call).
SUMMONS_WHO = frozenset("""
teacher teachers head headteacher headmaster headmistress school nursery college tutor lecturer
boss manager supervisor employer hr payroll council housing landlord lettings letting agency
dwp benefits tax hmrc bank gp doctor surgery dentist hospital consultant midwife police
probation court solicitor immigration ofsted office
""".split())
# Who can call you in often takes two words.
SUMMONS_WHO_PHRASES = ("social services", "health visitor", "home office", "tax office",
                       "job centre", "jobcentre", "letting agent", "letting agents",
                       "the council", "the school", "the office", "the bank", "the head")
# What they ask for: a word with you, not a job for you. "my boss wants me to work saturday" is
# a request to the person and gets no letter-and-meeting line.
SUMMONS_SEE = ("a word", "a quick word", "to see", "to talk", "a chat", "a meeting", "to meet",
               "to discuss", "to speak", "to come in", "asked me in", "called me in",
               "for a chat", "an appointment", "to interview")
SUMMONS_WRITTEN = ("written to me", "wrote to me", "sent me a letter", "sent a letter",
                   "a letter from", "letter arrived", "letter came", "in writing")
# A letter named before the who is a summons only when it is a letter that came to the speaker.
# "i need a letter from my doctor" and "i asked for a letter from the bank" are the speaker
# asking for one, and "i sent a letter to the council last week and no reply" is their own letter
# going out: telling any of those how to answer the letter is the wrong direction.
LETTER_RECEIVED = frozenset("""got received had came come arrives arrived""".split())
LETTER_ASKED_FOR = frozenset("""need needs wanted want wants asked ask asking sent send
    sending wrote write writing expecting waiting chase chased requested requesting
    wanting""".split())
# A letter that came to somebody else is not a summons to the speaker: "my neighbour got a
# letter from the council", "my wife got a letter from the school". The possessive in front of
# the received letter names whose it is, and it is the speaker's own only when it names the
# letter itself - "i got my letter from the council" is still theirs.
LETTER_SOMEONE_ELSES = frozenset("my his her their our".split())
LETTER_ITSELF = frozenset("letter letters note email reply".split())
SUMMONS_RANG = ("rang me", "phoned me", "called me", "left a message", "rang about",
                "phoned about", "called about", "rang the house")
# A call that has already happened is not a call to make: "the bank rang me back and said it was
# fine", "the council rang me today", "my boss rang me and told me not to worry". The ring-back
# line is right for a call to return, so the words that date the call take the shape away.
SUMMONS_CALL_DONE = frozenset("""back today yesterday tonight morning afternoon evening
    earlier already just then""".split())
SUMMONS_SAID = frozenset("said says told tells explained apologised apologized asked confirmed""".split())
# Someone who "has a meeting" or "has an appointment" has their own diary, not a want to see you:
# "my boss has a meeting with hr" and "the school has an appointment slot" are not summonses. So
# possession is not wanting, and the wanting verbs are the ones that name a person being called in.
SUMMONS_WANTS = ("want", "wants", "wanted", "needs", "needed", "asked", "asking",
                 "would like", "requested", "told me")
# The words that make it someone asking for you rather than you asking for them: whoever is
# wanting or writing has to be named before them. "the doctor wants to see me" is a summons,
# "i want to see a doctor" is the speaker's own plan.
SUMMONS_VERB = frozenset(SUMMONS_WANTS) | frozenset("""written wrote rang phoned called sent
    letter message""".split())
# "the letting agent still hasnt called me back" is a complaint about a call that never came.
SUMMONS_NOT = frozenset("""not hasnt havent didnt doesnt dont wont never no still yet""".split())


def _asks_for_it_rather_than_got_it(norm):
    """Whether the asking or sending word comes before the letter that arrived.

    "i asked for a letter from the bank" is the speaker asking for one, so advice on how to
    answer it is the wrong direction. But a letter that arrived can ask for something itself -
    "i got a letter from the council asking me to call" is still a letter to them, and the word
    that names the asking sits after the word that says it arrived. So the veto only reaches as
    far as the received word, the same way `_a_letter_someone_else_got` places the possessive.
    """
    arrived = next((index for index, word in enumerate(norm)
                    if word in LETTER_RECEIVED), None)
    if arrived is None:
        return False
    return any(word in LETTER_ASKED_FOR for word in norm[:arrived + 1])


def _a_letter_someone_else_got(norm, verb):
    """Whether a possessive in front of the letter names a person other than the speaker.

    "my neighbour got a letter from the council" and "my wife got a letter from the school" are
    letters to them, not to the person writing, so there is nothing for them to answer. The
    possessive has to sit before the letter word to count, and "i got my letter from the
    council" names the letter itself, so that one keeps its summons.
    """
    for index, word in enumerate(norm[:verb]):
        if word in LETTER_SOMEONE_ELSES:
            after = norm[index + 1] if index + 1 < len(norm) else ""
            if after and after not in LETTER_ITSELF:
                return True
    return False


def summons_of(norm, kind):
    """{"who", "shape"} when the line is someone wanting a word with the speaker, else None.

    `who` is the office or person who can call them in, `shape` is what they asked for:
    "see" (wants a word, a meeting), "written" (a letter) or "rang" (a phone call). A question
    is left alone: "what do i do if the council write to me" is asking for advice, not news.
    """
    if not norm or kind == "question":
        return None
    words = set(norm)
    who = None
    at = None
    for phrase in SUMMONS_WHO_PHRASES:
        if phrase in " ".join(norm):
            who = phrase
            at = norm.index(phrase.split()[0])
            break
    if who is None:
        who = next((word for word in norm if word in SUMMONS_WHO), None)
        at = norm.index(who) if who else None
    if who is None:
        return None
    # Whoever wants the word has to be named before the wanting, and it cannot be a call that
    # never came: see SUMMONS_VERB and SUMMONS_NOT.
    # The verb that carries the asking, not the "has" in front of it: the negator to look for
    # sits before "written" ("the bank hasnt written to me"), so the window has to start there.
    verb = next((index for index, word in enumerate(norm)
                 if word in SUMMONS_VERB and word not in ("has", "have")), None)
    if verb is None:
        verb = next((index for index, word in enumerate(norm) if word in SUMMONS_VERB), None)
    joined = " " + " ".join(norm) + " "
    # A letter is named before the who as often as after it ("i got a letter from the council",
    # "a letter came from the school"), and there the who follows the one word that carries the
    # asking. Only a letter may be read that way: "the council want a word" said the other way
    # round would let "i want to see the doctor" through.
    letter_first = (verb is not None and at > verb
                    and any(phrase in joined for phrase in SUMMONS_WRITTEN)
                    and any(word in LETTER_RECEIVED for word in norm)
                    and not _asks_for_it_rather_than_got_it(norm)
                    and not _a_letter_someone_else_got(norm, verb))
    if verb is None or (at > verb and not letter_first):
        return None
    if any(word in SUMMONS_NOT for word in norm[max(0, verb - 3):verb]):
        return None
    if letter_first or any(phrase in joined for phrase in SUMMONS_WRITTEN):
        return {"who": who, "shape": "written"}
    rang = next((phrase for phrase in SUMMONS_RANG if phrase in joined), None)
    if rang:
        # The words after the ring decide whether it is a call to make or one that came:
        # "school rang about my lad" is open, "the bank rang me back and said it was fine" is not.
        gap = joined.split(rang, 1)[1].split()[:3]
        if not set(gap) & SUMMONS_CALL_DONE and not set(gap) & SUMMONS_SAID:
            return {"who": who, "shape": "rang"}
    if not words & set(SUMMONS_WANTS):
        return None
    if any(phrase in joined for phrase in SUMMONS_SEE):
        return {"who": who, "shape": "see"}
    return None


def _said_to_somebody(norm, index):
    """True when this word closes a short line as the person it is said to.

    "thanks love", "morning pet", "cheers duck" and "night night love" end with a name for the
    person, and the line above it is one of the ones people say to somebody: a thanks, a
    greeting, a goodbye, a yes or a no. Anything else keeps its feeling word ("i love it",
    "theres no love between them", "i love").
    """
    if index != len(norm) - 1 or not 2 <= len(norm) <= 3:
        return False
    return norm[0] in ADDRESSED_LINES

# "an upset stomach" is not an upset person. `upset`, `bad` and `sick` are feelings when they
# stand on their own, and the name of what is wrong with a stomach when a stomach follows them,
# so the line is a body complaint and not a mood: the warm "what would make today a bit easier"
# line was the answer to "i have an upset stomach" while the rehydration advice sat unread.
STOMACH_WORDS = frozenset("""stomach stomachs tummy tummies belly bellies gut guts bowel bowels
    insides""".split())
# Only "upset" takes the body: "a bad stomach" and "a bad back" name how bad it is, which is a
# complaint and stays a bad line, while "upset" on its own is a mood about something else.
BODY_STATE_WORDS = frozenset("upset".split())


def _a_body_not_a_mood(norm, index):
    """True when the feeling word at `index` is naming what is wrong with the stomach."""
    forward = norm[index + 1] if index + 1 < len(norm) else None
    return forward in STOMACH_WORDS

# The same question handed back: "not bad, and you?", "im fine thanks, yourself".
BACK_AT = frozenset("you yourself u urself ya".split())
# "and you" and "about you"; not "to you" or "of you", which are the object of the line's own
# verb ("i miss talking to you", "thinking of you").
BACK_JOIN = frozenset("and about".split())
# "what about you", "how about you": the question coming back on its own.
BACK_ASKING = frozenset(("what", "how"))
# "me and you" and "you and me" are one subject, not a question back.
BACK_NOT_A_SUBJECT = frozenset("me us him her them i we my our your".split())
# What people put in front of the "yourself" they are handing back: how they are and the thanks
# that goes with it. No verb is in here, so "i love you" keeps its own reply, and "thank" is out
# because "thank you" is a thank-you on its own.
BACK_AFTER = frozenset("""thanks cheers ta ok okay alright fine good great well grand sound
    chill brill mint content lovely nice brilliant wonderful perfect amazing fantastic happy glad
    relaxed calm not bad tired rough meh shattered knackered wrecked awful terrible so very
    really doing feeling mate man
    complain same always
    working work busy off home out just finishing finishing up sorted done""".split())


def _asks_what_was_meant(text):
    """True when the whole line asks what the bot's own last answer meant.

    "what do you mean", "what does that mean", "how do you mean it" and the half a dozen ways
    people type the same question ("wot u mean", "wdym", "whatcha mean", "whaddya mean by
    that") name nothing of their own: they point at the line just given. The knowledge base read
    them as a follow-up on the subject of the last answer and took the word "mean" for the thing
    named, so after "my tomato plants have blight" the person got "The same goes for the wot u
    mean: cut off and bin the affected leaves" - their own slip said back at them as the thing
    being asked about, and the composer's own reply ("Just this: Brown-black patches ...") was
    the right one all along.

    The spellings are read in one place already, by the reply that answers this question
    (`bot/memory/meant.py::MEAN`), so this borrows that rule rather than keeping a second list
    that falls behind it. A thing named after "mean" is not this reading: "what does the boiler
    pressure mean", "what does it mean to be a good friend" and "what does mean reversion mean"
    are questions about a thing, and their card keeps the turn.
    """
    asked = str(text or "").strip()
    if not asked:
        return False
    from ..memory import meant

    return bool(meant.MEAN.match(asked))


# "what does that mean for my mortgage": the meaning is being applied to a thing of theirs. The
# thing is the question when it has just been talked about ("... for my pay" after a payslip),
# and it is a question of its own when it has not - see
# `bot/understanding/__init__.py::_the_meaning_is_applied_to_what_was_said`.
MEANT_APPLIED_TO = re.compile(r"\bfor\s+(?:my|our)\s+([a-z'\u2019-]+)", re.I)


def _asks_back(norm):
    """True when the line ends by handing the question back to the bot.

    "not bad, and you?", "im fine thanks, yourself", "good thanks, u?" answer how the person is
    and ask the bot the same thing in one breath. The reading called the whole line news about
    them, so the reply said neither how the bot was nor took the question: "im fine thanks,
    yourself" was answered "Thanks for telling me - I'm here if you want to dig into any of
    that", which answers neither half.

    Only the end of the line counts, and the "you" has to be a question rather than the object
    of the line's own verb: "i love you", "is it ok with you", "i miss talking to you",
    "thanks, youre alright you" and "i saw your mum and you" are none of them questions back.
    """
    words = [word for word in norm if word]
    if len(words) < 2 or words[-1] not in BACK_AT:
        return False
    # "and you?", "what about you", "how about you": the question back is the whole line, with
    # nothing about the person in front of it.
    if (len(words) == 2 and words[0] in BACK_JOIN) or \
            (len(words) == 3 and words[0] in BACK_ASKING and words[1] in BACK_JOIN):
        return True
    # "me and you" is one subject, not a question back.
    if len(words) > 2 and words[-3] in BACK_NOT_A_SUBJECT:
        return False
    # "thanks, youre alright you": the last "you" is a reprise of the one in front of it.
    if any(word in BACK_AT or word in {"youre", "your"} for word in words[:-1]):
        return False
    if words[-2] == "about" and not any(word in BACK_ASKING for word in words[:-2]):
        # "im worried about you", "im sad about you", "im confused about you": the "you" is
        # what the feeling is about, not the question handed back. An asking word anywhere in
        # front of it makes it a question back ("im skint, what about you"), and the join list
        # cannot tell the two apart on its own: the emotion in front of the "about" made every
        # worried-about-you line read as "im fine, thanks for asking after me".
        return False
    if words[-2] in BACK_JOIN:
        # "not bad, and you?": something has to be said about how they are in front of the join,
        # in the sign the line carries or in a feeling word of its own ("im fed up, and you",
        # which carries no sign either way), or in a word that says how they are without a sign
        # at all: "thanks, and you?", "cheers, and you", "same as always, and you". The reprise
        # guard above has already turned away the lines whose "you" is not a question, so the
        # words in front of the join here are about the person. "i saw your mum and you" keeps
        # what it had because of the "your".
        return (_polarity(norm) != 0 or emotion_of(" ".join(words)) is not None
                or any(word in BACK_AFTER for word in words[:-2]))
    # "im fine, you?" and "thanks, yourself": no joining word, so the word in front has to be
    # one of the words for how they are. "i love you" ends the same way and is not on offer.
    return words[-2] in BACK_AFTER


def says_how_they_are(norm):
    """True when the line says how the speaker is with a word that is also another thing.

    "im grand", "im sound thanks", "im chill": the reading has to see a feeling there, or the
    line reads as news and the bot answers a bare "im chill" with "Say more if it helps".
    "the sound of the boiler" and "the content of the email" are the other thing, so the word
    only counts when it is said about the person.
    """
    return any(word in SAYS_HOW_THEY_ARE and _a_state_of_the_speaker(norm, index)
               for index, word in enumerate(norm))


# A thing said to be a joke, a nightmare, a shambles. The noun is a verdict on the thing, not a
# request: "my landlord is a joke" is a person with a problem, and it was answered with a punchline
# because the line had the word "joke" in it and nothing said the word was the verdict. "it was a
# joke" is left alone - the subject is a pronoun, so the person is saying they were kidding.
VERDICT_NOUNS = frozenset("""joke nightmare disaster shambles mess farce ripoff con
    circus zoo mockery sham travesty letdown disappointment pain drag headache minefield
    slog waste fiasco scandal pantomime horror""".split())
COPULAS = frozenset("is are was were am be being been becomes became".split())
# The words that can sit between the copula and the verdict and only say how much: "a complete
# joke", "a total shambles", "a bit of a nightmare" (read from the verdict back to the copula).
VERDICT_FILLER = frozenset("""a an the total complete absolute utter right proper real massive
    huge bloody bit of on one big fat""".split())
# The same verdict as an adjective: "my landlord is useless" is the complaint "my landlord is a
# joke" makes, and it read as no feeling at all, so the line got "Got it. Is there anything you'd
# like a hand with?" and the person had to say it again. Only the verdicts are here. The state of
# a thing ("broken", "dead", "knackered", "stuck") has its own how-to-fix answer and keeps it, and
# "awful"/"terrible" already carry a feeling that the pools they reach are built for.
VERDICT_ADJECTIVES = frozenset("""useless pointless hopeless rubbish crap shit shite garbage
    trash pathetic""".split())
# A pronoun subject is the person talking about what they said or did, not a thing they are
# complaining about: "it was a joke", "that was a disaster" (a burnt cake, not a complaint).
PRONOUN_SUBJECT = frozenset("it that this there he she they we i you".split())
# A subject that asks names nothing: "what is a joke", "who is a nightmare" are questions about
# the words, and read as a verdict they lose their answer ("what is a joke" told one, and stopped).
ASKING_SUBJECT = frozenset("""what which who whom whose how why when where whatever whoever
    whichever whenever wherever""".split())
# A period of time said to be rubbish is a report of a mood rather than a thing to be put right:
# "the week was rubbish" already gets the question that helps ("what has made it like that"), and
# taking it as a verdict loses that question.
NOT_A_THING = frozenset("""week weekend day month year morning evening night afternoon term
    shift holiday trip time""".split())


def a_bad_verdict(norm, index):
    """True when the word at `index` is a verdict on a thing named before it: "my job is a joke"."""
    if index >= len(norm) or (norm[index] not in VERDICT_NOUNS
                             and norm[index] not in VERDICT_ADJECTIVES):
        return False
    back = index - 1
    while back >= 0 and norm[back] in VERDICT_FILLER:
        back -= 1          # "a complete joke", "a bit of a nightmare"
    if back < 0 or norm[back] not in COPULAS:
        return False
    subject = back - 1
    if (subject < 0 or norm[subject] in PRONOUN_SUBJECT or norm[subject] in ASKING_SUBJECT
            or norm[subject] in COPULAS or norm[subject] in NOT_A_THING):
        return False
    return True


def verdicts_a_thing(clean):
    """True when the line calls something a joke, a nightmare, a shambles.

    Read by the module that hands out jokes, and by the composer: "my landlord is a joke" has the
    word in it and is a person with a problem, and a punchline under it is the bot not reading the
    line at all. The sentence is tidied the way the reading tidies it, so "the trains are a total
    joke" counts.
    """
    text = " ".join(str(clean or "").lower().replace("\u2019", "'").replace("'", "").split())
    norm = [word for word in (re.sub(r"[^a-z0-9]+", "", part) for part in text.split()) if word]
    return any(a_bad_verdict(norm, index) for index in range(len(norm)))


def _polarity(norm):
    """-1, 0 or 1 for the feeling the line carries, with a negation turning it the other way.

    "im not fine", "not feeling great" and "im not ok" carry a bad feeling even though every
    feeling word in them is a good one, and "not bad" carries a good one. A line with words
    both ways ("tired but happy") stays 0.

    A negator turns the next feeling word only, so "i cant stop crying" and "i cant help
    feeling sad" stay bad: there the negated verb is not about the feeling. "ok" counts only
    as somebody's state ("im ok"), because on its own it is an acknowledgement or a question
    about permission.
    ''worry'' is left out on purpose: "should i worry about my knee" is a question about
    whether to worry, not a line with a bad feeling in it.
    """
    score = 0
    negated = False
    for index, word in enumerate(norm):
        if word in NEGATORS:
            negated = True
            continue
        if word in TERMS_OF_ADDRESS and _said_to_somebody(norm, index):
            negated = False
            continue
        if word in OK_WORDS or word in SAYS_HOW_THEY_ARE:
            feeling = 1 if _a_state_of_the_speaker(norm, index) else None
        elif word in POSITIVE:
            feeling = 1
        elif word in NEGATIVE:
            feeling = (-1 if word not in BODY_STATE_WORDS or not _a_body_not_a_mood(norm, index)
                       else None)
        elif a_bad_verdict(norm, index):
            # "my landlord is a joke" carries the complaint whatever the word is worth elsewhere
            # in the line: the noun is what they think of the thing they named.
            feeling = -1
        else:
            feeling = None
        if feeling is None:
            if word not in NEGATION_SKIP:
                negated = False
            continue
        score += -feeling if negated else feeling
        negated = False
    return (score > 0) - (score < 0)


def _thanks_still_asks(norm):
    """True when a thanks is followed by an ask that has no question word of its own.

    A person who thanks the bot and then asks for advice on something often writes no question
    word at all: "thanks, any tips for a cold". The advice word is the ask there, while in
    "thanks for the advice" the same word is only what they are thanking the bot for.
    """
    words = list(norm)
    for index, word in enumerate(words):
        if word not in THANKS_ASK_WORDS:
            continue
        back = words[index - 1] if index else ""
        if back in GIVEN_ADVICE:
            continue            # "thanks, no need": a comment, not an ask
        return True
    for index, word in enumerate(words):
        if word not in THANKS_ASK_NOUNS:
            continue
        back = words[index - 1] if index else ""
        if back in GIVEN_ADVICE:
            continue            # "for the advice on my back": the advice was already given
        if (index + 2 < len(words) and words[index + 1] in THANKS_ASK_PREPS
                and words[index + 2].isalpha()):
            return True
    return False


# A line that only picks something out and leaves the subject to the turn before it: "the best
# time to visit", "any good places to eat", "and the cheapest way to get there". Every one of
# them is a question with its "what is" left off, and read as a statement it named nothing to
# answer and got a search hedge.
PICKING = frozenset("""best better cheapest cheaper good great nice decent place places way ways
    time times thing things option options spot spots area areas""".split())
# A "to" and a verb after it: what makes the frame an ask ("to visit", "to eat", "to get").
TO_A_VERB = re.compile(r"\bto\s+[a-z]+", re.I)
# The words that make a line say something about a subject rather than ask about one.
SAYS_WHAT_IT_IS = frozenset("""is are was were am im i'm its it's be been""".split())


# A frame with its subject left out opens on the frame itself, not on a person or a thing of the
# line's own: "the best...", "a good...", "any good...", and the "and" that introduces a follow-up.
OPENS_A_FRAME = frozenset("""the a an any some and also best better cheapest cheaper good great
    nice decent""".split())

# The words that pick one thing out of many and ask for it, whether or not the line found an
# ask word of its own: "a good place to eat", "the cheapest one to get".
PICKING_QUALITY = frozenset("best better cheapest cheaper good great nice decent".split())


def _only_the_ask(norm, asks, text):
    """True when the line is nothing but a frame asking after something the last turn named.

    "the best time to visit" is not a statement about the best time: it is the question "what
    is the best time to visit?" with the subject left out, which is how people follow up. The
    line names nobody ("i"/"we" makes it a statement about what they want), says nothing about
    a subject ("is"/"was"), and is a short frame - a thing word, a quality or an ask, and "to
    <verb>". A frame that picks one thing out is asking for a recommendation even when the ask
    words missed it: "a good place to eat" asks for one as plainly as "the best way to eat".
    """
    words = [word for word in norm if word not in POLITE]
    if not words or len(words) > 8:
        return False
    if set(words) & (SPEAKER | SAYS_WHAT_IT_IS):
        return False
    if words[0] not in OPENS_A_FRAME:
        return False  # "my mum has a good recipe to follow" is about the recipe
    if not set(words) & PICKING or not TO_A_VERB.search(str(text)):
        return False
    return bool(asks) or bool(set(words) & PICKING_QUALITY)


def classify(line):
    text = line["norm_text"]
    norm = line["norm"]
    words = set(norm)
    signals = line["signals"]

    clauses = line["clauses"]
    opens_like_question = any(_opens_question(clause) and not _continues_the_sentence(clauses, at)
                              for at, clause in enumerate(clauses))
    asks = _asks(norm, " " + text + " ")
    turned_back = _asks_it_back(norm) or _asks_about_the_bot_day(norm)
    tag = _asks_for_confirmation(norm)

    # A question is what needs answering, even when it comes after a "hi" or a "thanks":
    # "Thanks! Which one should we start with?" is a question, "Thanks, that helped" is not.
    # The ask can be later in the line and still be the point of it: "thanks, one more thing -
    # how do i clean the oven" is a question about the oven, and read as a thank you it got the
    # reply for the thanks and no oven at all. What must not count is a thanks that only
    # comments, and a comment carries an asking word of its own: "thanks, that explains the
    # boiler" finds the definition ask on "explains", and "thanks for the advice" the tips ask
    # on "advice" - neither asks the bot for anything, and read as a question the advice line
    # was sent looking for an answer to a line that thanks the bot for the last one. So an ask
    # is not enough on its own: the line has to be shaped like a question too, with a question
    # mark, a question word, or an ask frame ("thanks, any tips for a cold").
    kind = "statement"
    courtesy = without_filler(norm)
    if not norm:
        kind = "empty"
    elif (signals["question_mark"] or _opens_question(norm) or opens_like_question
          or _asks_the_bot(norm) or _asks_for_help(text) or tag or _asks_after_any(norm)
          or (asks and _starts_with(norm, THANKS)
              and (signals["question_mark"] or set(norm) & QUESTION_WORDS
                   or _thanks_still_asks(norm)))):
        kind = "question"
    elif _only_the_ask(norm, asks, text):
        # A frame asking after the subject the last turn named is a question, not a statement:
        # "whats the capital of australia" then "and the best time to visit" was read as a
        # statement about nothing, so the subject was never put back and the line got a hedge.
        # A frame that picks one thing out asks for a recommendation, and its reading says so.
        kind = "question"
        asks = sorted(set(asks) | {"recommend"})
    elif _starts_with(norm, GREETINGS) and greeting_only(norm):
        kind = "greeting"
    elif ((_starts_with(courtesy, THANKS) and _thanks_only(courtesy, clauses))
          or _says_the_help_was_good(norm)):
        kind = "thanks"
    elif _ends_with_thanks(courtesy):
        kind = "thanks"

    if turned_back:
        asks = []
    if kind != "question":
        # A question word inside the clause that says when or where is not an ask: "it started
        # this morning when i was in the garden" asks nothing, so `when` is background too.
        behind = {norm[index] for index in background_clause(norm) | background_positions(norm)}
        asks = [ask for ask in asks if ask not in behind]
    if kind == "question" and (
            (not turned_back
             and any(strip_leaders(clause)[:1] and strip_leaders(clause)[0] in YESNO_STARTS
                     for clause in line["clauses"]))
            or tag):
        asks = sorted(set(asks) | {"yesno"})
    short = len(norm) <= 3
    bare = [word for word in norm if word not in POLITE]
    # A bad feeling the line rules out is not the bad feeling: "im not stressed" is the person
    # narrowing the cause, and "im not in pain" is not pain. The good words stay as they are,
    # because a good one that is ruled out is the bad feeling ("im not happy", "not feeling
    # great"), and `_polarity` already turns it the other way.
    denied_bad = {word for word in words if word in NEGATIVE and denied(text, word)}

    intent = "statement"
    if kind == "empty":
        intent = "empty"
    elif signals["laughter"] and len(norm) <= 5:
        intent = "laugh"
    elif _starts_with(strip_leaders(norm), FAREWELLS) and farewell_only(strip_leaders(norm)):
        # The goodbye is read before the reading that looks for "you": "see you later" and
        # "ttyl" (which the lexicon writes out as "talk to you later") are the way out, and
        # "can you talk later" is not, because it does not open with the farewell. The leaders
        # are taken off first, because a goodbye is preceded by one as often as not: "ok bye
        # ttfn", "right then, good night".
        intent = "farewell"
    elif _about_bot(text, words, norm):
        intent = "about_bot"
    elif kind == "greeting":
        intent = "greeting"
    elif kind == "thanks":
        intent = "thanks"
    elif _has_any(" " + text + " ", CORRECTION) and ("meant" in words or "mean" in words):
        intent = "correction"
    elif (_asks_it_back(norm) or _asks_about_the_bot_day(norm)
          or _asks_what_the_bot_is_doing(norm) or the_manners_question(norm)
          or asks_how_i_am(norm)):
        intent = "smalltalk"
    elif agreement_of(text):
        intent = "ack"
    elif _short_reply(text) and len(norm) <= 6:
        intent = "ack"
    elif kind == "statement" and _agrees_to_try(norm):
        intent = "ack"
    elif (norm[0] in {"no", "nah", "nope", "never"} and len(norm) <= 5
          and norm[1:2] != ["one"]):
        intent = "deny"
    elif norm[0] in ACK and len(norm) <= 4:
        intent = "ack"
    elif len(bare) <= 3 and set(bare) <= AFFIRM:
        intent = "affirm"
    elif len(bare) <= 3 and set(bare) <= DENY:
        intent = "deny"
    elif len(bare) <= 3 and (set(bare) <= ACK or set(bare) <= LAUGH):
        intent = "ack"
    elif small_talk_only(norm):
        intent = "smalltalk"
    elif kind == "question":
        intent = "question"
    elif ("recommend" in asks or _asks_for_tips(text, norm) or _has_any(text, STEPS)
          or words & {"help", "need", "want"}):
        intent = "request"
    elif norm[:1] and norm[0] in {"tell", "explain", "show", "give", "write", "make"}:
        intent = "request"
    elif "i" in words and (any(w in NEGATIVE or w in POSITIVE for w in words
                                  if w not in denied_bad)
                            or says_how_they_are(norm)):
        intent = "feeling"
    elif ("i" in words or _acts_on_the_speaker(text)) and emotion_of(text):
        # "im terrified", "im petrified": the emotion reader knows the word even when the plain
        # feeling lists do not, and the speaker is the one who has it, so the same line must not
        # read as news while "im scared" reads as a feeling. A thing that acts on the speaker
        # counts the same way: "work is stressing me out" has no "i" in it, and read as news it
        # was answered with its own words back ("Money is stressing you out - noted.").
        intent = "feeling"
    elif _has_any(" " + text + " ", NEWS):
        intent = "news"
    elif {"i", "me", "my", "we", "our"} & words and (words & EVENT_WORDS or len(norm) <= 12):
        intent = "news"
    elif _has_any(text, OPINION) or (words & {"think"} and kind == "question"):
        intent = "opinion"

    state_owner = _state_owner(line["clauses"])
    limit = _limit_of(text)
    suggestion = _a_suggestion_from_someone(norm, text)
    ruled_out = _ruled_out_of(text)
    emotion = None
    if "i" in words or "im" in words or "my" in words or kind != "question":
        emotion = emotion_of(text)
    if state_owner in (None, "thing") and _somebody_elses_heart(text):
        # Somebody else's broken heart is their trouble: the pool for the person in it stands
        # aside, and the same arm keeps the heartbreak row from answering about the speaker.
        state_owner = "other"
    if emotion and state_owner in (None, "thing") and _a_broken_heart_is_theirs(text):
        # A heart is a part of a person, so `_whose_state` calls it a thing, and a thing's state
        # is not the person's mood (bot/modules/chat.py stands the sad pool down on it). A broken
        # heart is not a body fault either - the health reader has nothing to say about it - it
        # is how the person is, said the long way round, so the owner is the person.
        state_owner = "self"
    if not emotion and _a_hedged_low(line.get("clean") or text):
        # "could be better", "been better", "not so good": a low said politely, with no word of
        # mood in it for the feeling reader to find.
        emotion = "sad"
        if state_owner in (None, "thing"):
            state_owner = "self"
    polarity = _polarity(norm)
    shortage = shortage_of(text)
    if shortage and emotion is None:
        # Nothing in the line names a mood of anybody's - the only state word in it is the one a
        # supply took off ("im low on milk") - so no state is being said of the speaker either.
        state_owner = None

    return {
        "kind": kind,
        "intent": intent,
        "asks": asks,
        # True when the end of the line is a tag asking to be agreed with ("... right",
        # "... innit"), so a module can tell a confirmation from a question about the world.
        "tag": tag,
        "emotion": emotion,
        "state_owner": state_owner,
        # The thing the line says has run out ("im low on milk" is milk, "im out of tea bags" is
        # tea), or None. A shortage is not a mood, and it is not the speaker's state either, so
        # the pools that answer a feeling stand down when this is set.
        "shortage": shortage,
        "polarity": polarity,
        "short": short,
        "first_person": bool(words & {"i", "me", "my", "we", "our", "us", "myself"}),
        "asks_opinion": "opinion" in asks,
        "asks_recommendation": "recommend" in asks,
        "asks_steps": "steps" in asks,
        "help_ask": _asks_for_help(text),
        "asks_a_verdict": _asks_a_verdict(text),
        "about_bot": intent == "about_bot",
        "about_bot_kind": (_about_bot_kind(text, words, norm)
                           if intent == "about_bot" else None),
        # A "how many" asked about the bot's own doings ("how many people have you talked to"):
        # the bot has no tally to give, and the memory answer describes what it remembers rather
        # than saying there is no number, so the composer needs to know which one it is.
        "counts_the_bots_own_day": _counts_its_own_doings(norm),
        "replies_to_bot": intent in ("affirm", "deny", "ack", "laugh"),
        "agrees_to_try": _agrees_to_try(norm),
        "wants_a_quiz": _hands_a_question_to_the_speaker(norm),
        # The idiom of agreement the whole line is ("tell me about it", "you and me both"), or
        # None. It is an ack, and a warmer one than "got it": the person has just agreed with
        # something, so the reply agrees back and asks nothing of them.
        "agreement": agreement_of(text),
        # Someone who can call them in wanting a word (see SUMMONS_WHO above): the shape the
        # reply needs, because "not knowing what it is about is the worst bit" is an answer to
        # a letter or a meeting and not to a question about one.
        "summons": summons_of(norm, kind),
        # The line answers how the person is and hands the question back in the same breath
        # ("not bad, and you?", "im fine thanks, yourself"): a reply that only answers the
        # person answers half of it. See `_asks_back`.
        "asks_back": _asks_back(norm),
        # True when the whole line asks what the bot's own last answer meant ("what do you
        # mean", "what does that mean", "wot u mean", "wdym"): it names nothing of its own, so
        # no knowledge entry is its answer and the store says the last answer again. See
        # `_asks_what_was_meant`.
        "asks_what_was_meant": _asks_what_was_meant(text),
        # The thing a line that only rules something out takes away ("no horror", "no treats",
        # "without the garlic"), as a list, plus the flag the composer reads. A line that says
        # more than a limit is not one, so "no horror but the last one was good" stays its own.
        "excludes": [limit] if limit else [],
        # The things the line says it does not mean, so a reader answering it can skip their
        # words: "for a holiday not a house" is a question about a holiday.
        "ruled_out": ruled_out,
        "constraint": limit is not None,
        # Advice somebody else gave the person ("my mate said i should try it", "the doctor told
        # me to rest") as {"who", "source"}, or None. The doing in it is still to come, so a
        # reply that asks how it went is about a day that has not happened: the composer answers
        # the plan instead. See A_REPORTED_VERB.
        "suggestion": suggestion,
    }


# What a person does on a set day, or keeps doing: "every day", "twice a week", "most days",
# "on a tuesday". ("on tuesday" is one Tuesday; only the article makes it a habit.)
ROUTINE_SHAPE = re.compile(
    r"\b(?:every (?:day|week|month|morning|evening|afternoon|night|weekend|other day)|"
    r"every (?:mon|tues|wednes|thurs|fri|satur|sun)day|"
    r"each (?:day|week|morning|evening)|most (?:days|weeks|mornings|evenings)|"
    r"(?:once|twice|three times|four times|a few times) a (?:day|week|month)|"
    r"on (?:a|an) (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|"
    r"at the weekend)\b", re.I)
# A routine is not a fault: "i get headaches most days" is a symptom to answer, and the card
# about it is the right reply. Nor is it a feeling ("i cry every morning") or a row, and those
# have their own readers. The words here are the ones that turn a routine into a complaint.
ROUTINE_IS_A_FAULT = re.compile(
    r"\b(?:pain|pains|\w*ache|\w*aches|aching|hurts?|hurting|sore|sick|ill|unwell|worse|worst|"
    r"worried|anxious|panic|cry|crying|cried|shout|shouting|shouted|argue|arguing|fight|"
    r"fighting|bleed|bleeding|blood|swollen|rash|fever|cough|coughing|vomit|vomiting|"
    r"dizzy|numb|sneeze|sneezing|stopped|stopping|wont stop|won't stop|leak|leaking|"
    r"broken|broke|craving|crave)\b", re.I)
# A routine they no longer keep is not a routine: "we used to talk every day" is about the past,
# and "that's a proper routine" is the wrong thing to say about it.
ROUTINE_IN_THE_PAST = re.compile(r"\b(?:used to|didn'?t use to|would (?:always |often )?\w+|"
                                 r"back then|years ago|in those days)\b", re.I)
# The person is the one doing it: "i walk the dog every day" is their routine, while "my dog
# barks at the postman every day" is the dog's behaviour, which is a question about the dog.
_ROUTINE_SUBJECT = re.compile(r"^\s*(?:and\s+|so\s+|well\s+|oh\s+)?(?:i|i(?:'m|ve|d)|we|we(?:'re|ve))\b",
                              re.I)


# The hours someone works are said as a shape of the week, and "on lates" is a shift, not a
# period that is late: "im on lates this week" was answered with the late-period card. The
# patterns need the shift word or the "on lates"/"earlies" shape, so "im late for work" and
# "my period is late" keep their own readings.
SHIFT_LATE = re.compile(
    r"\b(?:(?:i|we|im|i'm|we're|were)\s+)?(?:am|are|'m|'re|was|were)?\s*"
    r"(?:on|back on|working|work|doing|do)\s+(?:the\s+)?(?:lates|late shifts?)\b"
    r"|\bon (?:the )?lates\b|\blates (?:all|this|next|every|for)\b|\blate shifts?\b", re.I)
SHIFT_EARLY = re.compile(
    r"\b(?:(?:i|we|im|i'm|we're|were)\s+)?(?:am|are|'m|'re|was|were)?\s*"
    r"(?:on|back on|working|work|doing|do)\s+(?:the\s+)?(?:earlies|early shifts?)\b"
    r"|\bon (?:the )?earlies\b|\bearlies (?:all|this|next|every|for)\b|\bearly shifts?\b",
    re.I)
SHIFT_NIGHT = re.compile(
    r"\b(?:night shifts?|on nights|work(?:ing)? nights|nights this week)\b", re.I)


def shift_worked(text):
    """The shift pattern the line names ("late", "early", "night"), or None.

    "im on lates this week" and "im on earlies" are how half the working country says a week of
    two-till-ten or six-till-two. They are the hours of the week, not a late period: the word
    "lates" was read as "late" and reached the cycle card.
    """
    text = text if isinstance(text, str) else ""
    if SHIFT_NIGHT.search(text):
        return "night"
    if SHIFT_LATE.search(text):
        return "late"
    if SHIFT_EARLY.search(text):
        return "early"
    return None


# What somebody else says the person should do is not a day the person has had. "my mate said i
# should try that new pizza place" was answered "How was it, overall?", "i was told to rest" got
# "Good to hear. What was the best bit?" and "my sister says i would like that show" got "That
# show - fair enough. What's stopped it happening so far?": the past tense of "said" and "told",
# the short flat shape and the "i" in the reported clause read as an account of the person's own
# day, and nothing in the line has happened at all. A suggestion is a plan with somebody else's
# name on it, so the reading says who said it, and a reply about the plan is the one that fits.
A_REPORTED_VERB = re.compile(
    r"\b(?:said|says|say|told|tells|tell|reckons?|reckoned|thinks?|thought|suggests?|suggested|"
    r"recommends?|recommended|advises?|advised|insists?|insisted|keeps? (?:saying|telling me)|"
    r"wants? me to|wanted me to|nagged? me to|pushing me to|going on at me to)\b", re.I)
# The clause that holds the suggestion, and whose doing it is: the person being advised is the
# speaker ("i should", "me to rest"), so "i told him to stop" - advice given rather than
# received - is not this shape, and neither is a report of something done ("she said i was late").
A_SUGGESTED_CLAUSE = re.compile(
    r"\b(?:i|we) (?:should|shouldnt|shouldn't|ought|need|needed|have) (?:to )?"
    r"|\b(?:told|asked|tells|asks|wants?|wanted|nagged|pushing|pushed) me to\b"
    r"|\b(?:i would|id|i'd) (?:like|love|rather|be better|better off)\b", re.I)
# The passive puts the verb inside the clause instead of in front of it: "i was told to rest",
# "ive been told to slow down". The doing is still to come, so it is the same line.
A_TOLD_TO = re.compile(r"\b(?:was|were|am|im|been|be|got) told to\b", re.I)
# Advice to do nothing is not a plan to start, and the plan pools ask what the first step would
# be: "my mate said i shouldnt bother" was answered "Your mate may be onto something. What's the
# first step you could do this week?" - the opposite of what the mate said. Nor is waiting advice
# to act on. Both keep whatever reply they had.
A_NOT_A_SUGGESTION = re.compile(
    r"\b(?:shouldnt|shouldn't|should not|ought not|dont bother|don't bother|no point in|"
    r"not worth (?:it|the|bothering)|wait and see|sit tight|hold off|hang on|leave it for now|"
    r"think about it)\b", re.I)
# Who said it, in the line's own words: "my mate", "the doctor", "a friend", "my sister".
A_SAID_BY = re.compile(
    r"\b(?:my|the|a|an|our|his|her|their) (?:[\w'-]+ ){0,2}?"
    r"(?:mate|friend|mum|mom|mam|mother|dad|father|sister|brother|wife|husband|partner|son|"
    r"daughter|gran|nan|grandma|grandad|neighbour|neighbor|colleague|coworker|boss|manager|"
    r"doctor|gp|nurse|physio|physiotherapist|consultant|surgeon|midwife|dentist|pharmacist|"
    r"therapist|counsellor|counselor|trainer|coach|teacher|tutor|landlord|lads|girls|bloke|"
    r"fella|chap|someone|somebody)\b", re.I)
# Nobody in particular: "everyone says i should try yoga", "they told me to rest". The pool has
# a line for it, so the reading says the line names no one rather than leaving it to a pronoun.
A_SAID_BY_ANYONE = re.compile(r"\b(?:everyone|everybody|people|they|he|she)\b", re.I)


def _a_suggestion_from_someone(norm, text):
    """The advice somebody else gave, as {"who": "Your mate", "source": "my mate"}, or None.

    Two parts, and both are needed: a report ("said", "says", "told", "reckons", "wants me
    to", "i was told to") and a clause that is advice to the speaker ("i should", "me to rest").
    A report of a fact is somebody else's news and keeps its own reading, and a suggestion with
    no report in it ("i should try running") is the person's own plan, which the composer has.

    The name comes from the line where the line gives one, because "Your mate may be onto
    something" is a warmer reply than the same line with nobody in it. "my" becomes "Your":
    the bot is not in the family.
    """
    said = " " + " ".join(norm) + " "
    report = A_REPORTED_VERB.search(said)
    if not report:
        return None
    if not (A_SUGGESTED_CLAUSE.search(said, report.start()) or A_TOLD_TO.search(said)):
        return None
    if A_NOT_A_SUGGESTION.search(said):
        return None
    before = said[:report.start()]
    named = None
    for found in A_SAID_BY.finditer(before):
        named = found.group(0).strip()
    if named:
        words = named.split()
        if words[0] in ("my", "our"):
            words[0] = "your"
        who = " ".join(words)
    elif A_SAID_BY_ANYONE.search(before):
        who = ""
    else:
        who = ""
    return {"who": who[:1].upper() + who[1:], "source": named or ""}


def is_a_routine(line, read=None):
    """True when the line reports a routine the speaker keeps, rather than asking about one.

    "i walk the dog every day", "we eat out twice a month", "i water the plants every morning":
    the person is the one doing it, the line asks nothing, and nothing in it is a fault or a
    feeling. A card is about the thing a line names; on a routine the thing is what they do it
    to, and the routine is the news, so a module that would answer the thing stands aside and
    the habit tail says the routine back (bot/memory/ack.py::_plain).

    False for a question ("how often should i walk the dog"), for a line whose subject is
    something else ("my dog barks at the postman every day"), for a symptom ("i get headaches
    most days") and for a feeling ("i cry every morning").
    """
    read = read or {}
    if read.get("kind") not in ("statement", "news", None):
        return False
    if read.get("asks"):
        return False
    text = str(line.get("plain") or line.get("clean") or line.get("text") or "").strip()
    if not text or text.endswith("?"):
        return False
    if not _ROUTINE_SUBJECT.match(text):
        return False
    if ROUTINE_IS_A_FAULT.search(text) or ROUTINE_IN_THE_PAST.search(text):
        return False
    return bool(ROUTINE_SHAPE.search(text))


# --- the home somebody lives in now ----------------------------------------------------------
# "my mum moved into a home last month", "my nan is in a home too", "i feel guilty about not
# visiting my dad in the home". A home after "in the" or "into a" is where a person lives now,
# and every one of those lines was answered as guests arriving at the speaker's flat ("Give them
# the best bed and plan one shared outing a day") or as a move into a new one ("On the first
# night you need the bed made, toilet roll, a kettle..."), or said back as a fact ("Noted: your
# nan is in a home too shes 88"). None of them is a reply to the news.
CARE_HOME_PLACE = re.compile(
    r"\b(?:in|into|at)\s+(?:a|the)\s+(?:care\s+|nursing\s+|residential\s+)?home\b", re.I)
# Not that place: working from home is an office, a home town is where somebody grew up, and a
# home birth is neither. The article is what keeps "at home" out.
CARE_HOME_NOT = re.compile(r"\b(?:work|works|working|worked|stay|staying)\s+from\s+home\b"
                           r"|\bhome\s+(?:town|office|made|birth|baked)\b", re.I)
# The words a family uses that the relation list is not built from: "my nan is in a home too",
# "my mam moved in last month", "my mother-in-law".
CARE_HOME_KIN = frozenset("""nan nana mam mammy mate mates grannie grandaddy mother-in-law
    father-in-law sister-in-law brother-in-law son-in-law daughter-in-law""".split())
CARE_HOME_MOVED = re.compile(r"\b(?:moved|moves|moving|went|goes|gone|going|put|puts|putting"
                             r"|decided|decision|agreed|arranged|sorted)\b", re.I)
CARE_HOME_VISIT = re.compile(r"\b(?:visit|visits|visiting|visited|see|seeing|saw|"
                             r"bring|brings|bringing|brought|take her|take him|take them)\b", re.I)
CARE_HOME_GUILT = re.compile(r"\b(?:guilt|guilty|selfish|should have|shouldve|my fault|blame"
                             r"|couldnt cope|could not cope|no choice|heartbroken|awful)\b", re.I)


# A line that asks what to bring or take to somebody, with nobody and nothing named in it: "what
# should i bring her", "should i take him anything", "what can i bring". The whole sentence is
# about the person the conversation has already placed, and read word by word it is about the
# verb "bring" and nothing else - which is a customs allowance.
CARE_HOME_BRING_ASKS = re.compile(
    r"\b(?:what|anything|something|whats|should i|shall i|can i|could i|do i|did i|"
    r"is there anything)\b", re.I)
CARE_HOME_BRING_WORD = re.compile(r"\b(?:bring|brings|bringing|take|takes|taking)\b", re.I)
CARE_HOME_BRING_WHO = re.compile(r"\b(?:her|him|them|she|he|they)\b", re.I)


def a_home_carried_forward(text, earlier_lines):
    """The care home a line with no home in it is about, read from the conversation, or None.

    "my mum moved into a home last month" places somebody; "what should i bring her" two turns
    later is about that same visit, and on its own the only word in it that means anything is
    "bring" - so the answer was the customs allowance ("Coming into the UK you can bring 4 litres
    of spirits"). The line names neither a person nor a thing, so the subject is only clear from
    the turn before it: that is what this reads, and `carried` says where the reading came from.
    """
    line = re.sub(r"['\u2019]", "", str(text or "")).strip()
    if not line or a_care_home(line):
        return None
    if not (CARE_HOME_BRING_ASKS.search(line) and CARE_HOME_BRING_WORD.search(line)
            and CARE_HOME_BRING_WHO.search(line)):
        return None
    for earlier in reversed(list(earlier_lines or ())):
        read = a_care_home(earlier)
        if read:
            carried = dict(read)
            carried["shape"] = "bring"
            carried["carried"] = str(earlier)
            return carried
    return None


def a_care_home(text):
    """The person living in a care home a line is about, or None.

    `shape` says what the line is about there: "guilt" when it names the feeling, "visiting" when
    it is about going, "moved" when somebody has just gone in, and "in" for the plain statement.
    """
    from .topics import RELATIONS   # a local import: topics imports this module
    line = re.sub(r"['\u2019]", "", str(text or "")).strip()
    if not line or not CARE_HOME_PLACE.search(line) or CARE_HOME_NOT.search(line):
        return None
    lowered = line.lower()
    who, relation = "", None
    for match in re.finditer(r"\b(?:my|our|your)\s+([a-z][a-z-]*)", lowered):
        if match.group(1) in RELATIONS or match.group(1) in CARE_HOME_KIN:
            relation = match.group(1)
            who = " ".join(match.group(0).split())
            break
    if not who:
        for word in ("shes", "hes", "she", "he", "they", "theyre"):
            if re.search(r"\b%s\b" % word, lowered):
                who = word
                break
    if not who:
        return None  # "the home" with nobody named is not news about a person
    if relation in ("husband", "father", "dad", "son", "brother", "uncle", "cousin", "grandad",
                    "grandpa", "grandfather", "granddad", "partner", "boyfriend", "friend",
                    "male friend", "nephew", "stepdad", "stepfather"):
        pronoun = "he"
    elif relation in ("wife", "mother", "mum", "mom", "daughter", "sister", "aunt", "gran",
                      "granny", "grandma", "grandmother", "partner", "girlfriend", "friend",
                      "niece", "stepmum", "stepmother", "nan", "nana", "mam", "mammy",
                      "grannie", "mother-in-law", "sister-in-law", "daughter-in-law"):
        pronoun = "she"
    elif relation in ("kids", "children", "child", "parents", "friends", "mates", "mate"):
        pronoun = "they"
    elif who in ("he", "hes"):
        pronoun = "he"
    elif who in ("she", "shes"):
        pronoun = "she"
    else:
        pronoun = "they"   # the line does not say, and "they" is never wrong
    if relation in ("kids", "children", "parents", "friends"):
        pronoun = "they"
    if CARE_HOME_GUILT.search(lowered):
        shape = "guilt"
    elif CARE_HOME_VISIT.search(lowered):
        shape = "visiting"
    elif CARE_HOME_MOVED.search(lowered):
        shape = "moved"
    else:
        shape = "in"
    return {"text": " ".join(CARE_HOME_PLACE.search(line).group(0).split()),
            "who": who, "relation": relation, "pronoun": pronoun, "shape": shape}


# --- does the answer hold for the day, or does it stand still ------------------------------
#
# `understood["over_time"]`: whether the answer to a question holds only for the day, or stands
# still, and `over_time_what` names what moves when it does. One key, because the routing lane's
# hedge for a live ask (`LIVE_WORLD_ASK` in bot/compose/fallback.py) is the same question.
#
# Two questions can look the same and want opposite replies:
#
#     how much is a single to leeds     a price, and a price is only right for a while
#     how many people live in leeds     a count, and a count is the same answer next year
#
# The first has to be answered as *the figure now* - named as a figure, checked, or asked about
# ("is that off-peak?") - because a price, an opening time or a train time is a fact with a date
# on it. The second can be answered as the fact it is. A module that gives a live figure as
# though it were settled, or hedges a settled one as though it might have moved, is worse than
# one that does neither, and until now the reading said nothing that let a module tell the two
# apart. `bot/compose/rule.py` names the same line in its own docstring: it holds no rule
# because "a live price or a surgery's opening hours" would go out of date.
#
# **What decides it is the thing asked about, never the word for freshness.** "latest",
# "current", "now", "today", "these days" and "in the world" are not evidence either way: a
# person asking for the latest phone is asking about a thing with versions, and a person asking
# about the biggest thing in the world is asking about a record. Read the noun the question is
# about, and the shape of the ask, and neither answer rests on the word "latest" or "world".
#
# The reading is three-valued, and the third value is the honest one:
#
# * ``True`` - it holds for the day, with what moves named in `over_time_what`: a `price`, a
#   surgery's `hours`, the `weather`, the `news`, a thing's `availability`, a `timetable`, a
#   `rate`, an `event`.
# * ``False`` - a fact that stands still: a count, a superlative, a definition, a working, a
#   history, a measurement, a method, a conversion. Positive evidence of one of those shapes is
#   what it takes.
# * ``None`` - neither is said (`my back hurts`, `idk`, or a question like `whats the latest
#   iphone` whose subject names no class here). A module must be able to tell "stands still"
#   from "not said", which is why this is not a bare false.
#
# A live subject beats a settled shape, because the shape is what is being asked *about* the
# live thing: `how much does a season ticket cost` is a `how much` that comes out as a price,
# and `how many tickets are left` is a `how many` that comes out as availability.

_MONEY_NOUN = re.compile(
    r"\b(?:price[sd]?|pricing|cost[s]?|costing|charge[sd]?|fare[s]?|fee[s]?|rent|rental|"
    r"salary|salaries|wage[s]?|expensive|cheaper|cheapest|cheap|how\s+much\s+money)\b")
# A money word is not an ask for a figure. "can i withhold rent", "does paye come out of my
# wages", "is a dog expensive" and "can i pay by card at the tip" all name money and none of them
# asks what anything costs. What makes a price is the shape of the ask - how much, what does it
# cost, what is the price of, what is it worth, which is cheapest - so that is what the class is,
# and a money word on its own says nothing.
_A_PRICE_ASK = re.compile(
    r"\bhow\s+much\s+(?:is|are|was|were|will|would|does|do|did|should|can|could|might|"
    r"is\s+it|do\s+they|do\s+you|do\s+i|does\s+it)\b|"
    r"\bprice[sd]?\s+(?:of|for|on)\b|\bcost\s+of\b|"
    r"\bwhats?\s+(?:the\s+)?(?:price|cost|charge|fare|fee|rent)\b|"
    r"\bwhat\s+(?:is|are)\s+the\s+(?:price|cost|charge|fare|fee|rent)\b|"
    r"\bwhat\s+(?:does|do|will|would|should)\b[^?]{0,30}?\b(?:cost|charge)\b|"
    r"\bwhats?\s+(?:it|that|this|they|one)\s+worth\b|\bhow\s+much\s+(?:money|for)\b|"
    r"\bcheapest\b|\bdeals?\s+on\b|\bon\s+offer\b|\bdiscount(?:s|ed)?\b|"
    r"\b(?:anything|something|any|some)\s+(?:a\s+bit\s+|much\s+)?cheaper\b|"
    r"\bis\s+(?:there|that|it)\s+cheaper\b|\bcheaper\s+(?:than|option|ones?|deal)\b|"
    r"\bprice\s+match\b|"
    # A comparison of what things cost is a price question with no figure in it, and so is the
    # rate a trade charges: "is a stamp cheaper online", "whats the going rate for a plumber".
    r"\b(?:cheaper|more\s+expensive|dearer|pricier|costlier|better\s+value)\b|"
    r"\b(?:going|market|typical|average|usual|standard|ballpark)\s+"
    r"(?:rate|price|cost|fee|charge)\b")
# Who holds an office is a fact with a date on it: the answer was different last year and will be
# different again, so it is not the bot's to state from memory. "who is the prime minister" and
# "whos the ceo of twitter" are askable; "who is the queen" is not askable as a post.
_A_POST_HOLDER = re.compile(
    r"\bwho(?:s|\s+is|\s+are)?\s+(?:the\s+|our\s+)?(?:prime\s+minister|pm|president|"
    r"chancellor|home\s+secretary|first\s+minister|mayor|mp|meps?|ceo|chief\s+executive|"
    r"head\s+teacher|manager|coach|owner|chair(?:man|woman|person)?)\b"
    r"(?![^?]*\b(?:of\s+the\s+year|ever|all\s+time|alive|dead)\b)")
# How much a thing weighs or holds is a fact about the thing, whatever the words: "how much does
# a jar of coffee weigh" is a measurement, not a price.
# A person's own spending is not a figure the world holds: the bot was not there.
_A_HOW_MUCH_I_SPENT = re.compile(
    r"\bhow\s+much\s+(?:did|have|has|do)\s+(?:i|we)\s+(?:spend|spent|pay|paid|earn|earned|"
    r"save|saved)\b")
# The same holds for a figure about the person's own account, whatever verb asks it. "how much am
# i paying for my subscription" is not a price the world sets: the bot cannot see their bill, their
# subscription or their account, and the reply that answers it ("what you pay is on your own bill")
# is a better one than a price card. Only the `did i spend` shape was fenced, so `am i paying`
# fell through to the bare `how much` in `_A_COUNT` and read as a price. What makes the figure
# theirs is the person doing the paying, or a possessive on the thing billed - and neither is a
# word about time, so this is a fence and not a class of its own.
_A_MY_OWN_FIGURE = re.compile(
    r"\b(?:am|do|will|would|should|have|did|can)\s+i\s+(?:be\s+)?(?:paying|charged|billed|"
    r"spending|getting\s+charged)\b|"
    r"\bmy\s+(?:own\s+)?(?:bill|bills|subscription|subscriptions|account|card|statement|"
    r"tariff|contract|plan|direct\s+debit|standing\s+order|invoice|receipt|payslip|quota|"
    r"allowance)\b")
# A measure in, "in" or "to", a measure out is a conversion, and a conversion is arithmetic: the
# numbers do not move. "how much is 200g in cups" and "how much is 180c in fahrenheit" were read as
# prices because "how much" is the price ask and nothing said otherwise. A quantity of money on
# either side is an exchange rate, and a rate does move, so a money word keeps the line live.
_MONEY = re.compile(
    r"\b(?:dollars?|euros?|quid|cents?|yen|rupees?|pence|money|cash)\b")
_UNITS = (r"g|kg|kilos?|kilograms?|grams?|oz|ounces?|lbs?|pounds?|ml|l|millilit(?:re|er)s?|"
          r"litres?|liters?|cups?|tbsp|tsp|"
          r"tablespoons?|teaspoons?|celsius|fahrenheit|centigrade|degrees|stone|inches?|inch|"
          r"cm|mm|metres?|meters?|feet|foot|ft|miles?|km|yards?|pints?|quarts?|gallons?")
# The units that are never a thing you buy by the one - a cup of coffee and a pint of milk are
# prices. So a measure with no "of" after it is a measure, and one with "of" is what it costs.
_UNITS_BOUGHT = (r"g|kg|kilos?|kilograms?|grams?|oz|ounces?|lbs?|ml|l|millilit(?:re|er)s?|"
                 r"litres?|liters?|cups?|tbsp|tsp|"
                 r"tablespoons?|teaspoons?|celsius|fahrenheit|centigrade|degrees|stone|"
                 r"inches?|inch|cm|mm|metres?|meters?|feet|foot|ft|miles?|km|yards?")
# A number with a unit and then what it is of is an amount of a thing, and an amount of a thing
# costs money: "how much is 500 ml of paint" is a price and not a sum, even though the arithmetic
# reading hears "how much is 500".
_A_AN_AMOUNT_OF_A_THING = re.compile(
    r"\b\d+\s*(?:" + _UNITS + r")\b\s+(?:of|in)\b|"
    r"\b(?:a|an|one|two|three|half|quarter)\s+(?:" + _UNITS_BOUGHT + r")\s+of\b")
_A_A_CONVERSION = re.compile(
    r"\bhow\s+(?:much|many)\b[^?]{0,30}?\b(?:\d+)?\s*(?:" + _UNITS +
    r")\b\s+(?:in|to|into)\s+\w")
_A_HOW_MUCH_OF_A_UNIT = re.compile(
    r"\bhow\s+much\s+(?:is|are|was)\s+(?:a\s+|an\s+|one\s+)?[\d\w\s]{0,12}?\b(?:" +
    _UNITS_BOUGHT + r")\b(?!\s+of\b)")
# "what time is it" is the clock, not a place's hours.
_A_THE_CLOCK = re.compile(r"\bwhat\s+time\s+is\s+it\b|\bwhats\s+the\s+time\b")
_A_HOW_MUCH_IT_HOLDS = re.compile(
    r"\bhow\s+much\s+(?:\w+\s+){0,2}(?:does|do|is|are|will|would|should|must|can)\b"
    r"[^?]{0,60}?\b(?:weigh|weighs|hold|holds|contain|"
    r"contains|measure|measures|store|stores|sleep|sleeps|eat|eats|drink|drinks|feed|feeds|"
    r"lift|lifts|take|takes|need|needs|use|uses|burn|burns|grow|grows|train|exercise|"
    r"practise|practice|study|water|feed|give|have|put|add)\b")
# How much somebody is loved, missed or cared about is not a figure at all.
# "how much exercise is enough" asks for an amount, not for a figure.
_A_HOW_MUCH_ENOUGH = re.compile(
    r"\bhow\s+much\b[^?]{0,40}?\b(?:enough|too\s+much|too\s+little|of\s+it)\b|"
    r"\bhow\s+much\s+of\b")
_A_HOW_MUCH_IS_IN = re.compile(
    r"\bhow\s+much\s+(?:is|are)\s+(?:there\s+)?left\b|"
    r"\bhow\s+much\s+(?:is|are)\s+(?:in|left\s+in)\b|"
    r"\bhow\s+much\s+(?:\w+\s+)?in\s+(?:a|an|one|the|\d)\b|"
    r"\bhow\s+much\s+(?:\w+\s+){0,2}for\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|"
    r"ten|twenty)\b[^?]{0,20}\b(?:people|persons?|portions?|servings?|guests?|adults?|kids?)\b|"
    r"\bhow\s+much\s+(?:\w+\s+){0,2}per\s+(?:person|head|portion|serving)\b")
_A_HOW_MUCH_A_FEELING = re.compile(
    r"\bhow\s+much\s+(?:do|does|did)\s+(?:you|i|we|he|she|they)\s+(?:love|care|miss)\b")
# A sum is settled before any class is looked for: "how much is 2 plus 2" is arithmetic, and so
# is "whats 20% of 50". The reading already files some of these under `asks: maths`, and the
# digits or the sign appear in the line itself.
_A_ARITHMETIC = re.compile(
    r"\d\s*(?:\+|\*|x|/|plus|minus|times|divided\s+by|multiplied\s+by)\s*\d|"
    r"\d\s+-\s+\d|"
    r"\b(?:percent|per\s?cent)\b|\d\s*%|\bwhats\s+\d+\s*%|"
    r"\b(?:plus|minus|divided\s+by|multiplied\s+by)\s+(?:\d+|one|two|three|four|five|six|seven|"
    r"eight|nine|ten|twenty|thirty|fifty|hundred|thousand)\b")
_A_HAS_A_NUMBER = re.compile(r"\d|\b(?:one|two|three|four|five|six|seven|eight|nine|ten)\b")
# A difference between two things is a fact about them, not about today: "whats the difference
# between weather and climate" names the sky and asks for neither today's rain nor this week's.
_A_A_DIFFERENCE = re.compile(
    r"\b(?:whats|what\s+is|what\s+was)\s+the\s+difference\b|\bdifference\s+between\b|"
    r"\bhow\s+(?:do|does)\s+\w+\s+differ\b|"
    r"\bhow\s+(?:is|are|was|were)\b[^?]{0,40}?\b(?:different|differs?|distinct)\s+"
    r"(?:from|to|than)\b")
# Asking the bot whether it saw something is a question about the bot, not a request for the news.
_A_DID_YOU_SEE = re.compile(
    r"\bdid\s+you\s+(?:see|hear|watch|read|catch|catch\s+up\s+on)\b|"
    r"\bhave\s+you\s+(?:seen|heard|watched|read)\b|\bdid\s+you\s+know\b")
# A record is a fact about the world that a superlative states, and people state it as a bare
# noun as often as they ask it: "the biggest country in the world" is a request for the answer.
_A_BARE_RECORD = re.compile(
    r"^\s*(?:(?:and|so|but|then)\s+)?(?:the|whats\s+the|what\s+is\s+the|which\s+is\s+the)?\s*"
    r"(?:biggest|largest|tallest|longest|smallest|deepest|highest|oldest|fastest|richest|"
    r"most\s+populous)\b")
# A year that has gone settles whatever is in the line: nothing about 1966 is today's version of
# anything, however live the words around it are.
_A_PAST_YEAR = re.compile(r"\b(?:back\s+)?in\s+(?:1[0-9]{3}|20[0-2][0-9])\b")
# A war that has been fought is history, however it is asked about.
_A_HISTORY_ITSELF = re.compile(
    r"\b(?:first|second|third|1st|2nd|world)\s+world\s+war\b|\bworld\s+war\s+(?:one|two|1|2|ii)\b|"
    r"\bthe\s+(?:great\s+)?war\b")
# The age of the world itself is a date and not a figure that moves.
# How hot, deep, tall or heavy a thing itself is is a measurement of that thing, and the same
# figure next year: "how hot is lava", "how hot is a scotch bonnet", "how deep is the ocean". What
# makes a line the weather is asking how it is *here and now* - "it", "outside", "today".
_A_HOW_A_THING_MEASURES = re.compile(
    r"\bhow\s+(?:hot|cold|warm|deep|tall|high|heavy|big|large|long|wide|fast|strong)\s+"
    r"(?:is|are|was|were)\s+(?!it\b|outside\b|today\b|tonight\b|this\b|the\s+weather\b)")
# A traffic light is not traffic: the lights on a road, or the label on a packet.
_A_A_TRAFFIC_LIGHT = re.compile(r"\btraffic\s+lights?\b")
# A plan about the weather is the plan, not the forecast: "what should we do about the weather
# plan", "weather permitting".
_A_A_PLAN_ABOUT_THE_WEATHER = re.compile(
    r"\b(?:the\s+)?weather\s+(?:plan|plans|permitting|dependent|depending)\b")
# What makes a line about the sky rather than about a thing: it asks how it is here and now.
_A_WEATHER_HERE = re.compile(
    r"\b(?:is|will)\s+it\s+(?:be\s+)?(?:going\s+to\s+)?(?:rain|snow|sunny|windy|hot|cold)\b|"
    r"\bhow\s+(?:hot|cold|warm|windy)\s+(?:is|will)\s+it\b|"
    r"\b(?:today|tonight|tomorrow|this\s+(?:week|weekend|morning|afternoon|evening)|"
    r"outside|right\s+now|at\s+the\s+moment)\b")
_A_HOW_OLD_IS_THE_WORLD = re.compile(
    r"\bhow\s+old\s+is\s+the\s+(?:earth|world|universe|planet|sun|moon)\b")
_MONEY_ASKED = re.compile(
    r"\bhow\s+much\s+(?:is|are|was|were|will|would|does|do)\b(?!\s+(?:too|enough|of)\b)")
# "how much for a ticket" asks the same thing without a verb.
_MONEY_FOR = re.compile(r"\bhow\s+much\s+for\b")

# A place's own times. "is it open" and "what time does it close" are the same ask, and both
# are worth checking before a person travels.
# The verb of opening has to be about a place, so a thing has to be behind it: "is tesco open
# now", "is it open", "are the shops open on sunday", "what time does the surgery close". Without
# a thing - "the heating starts", "what time do i clock in" - the verb is somebody else's
# business, so "start" and "finish" are not here at all, and a place's times are never the
# person's own diary.
# A place is named with more than one word as often as with one: the post office, the swimming pool,
# the station ticket office. The verb of opening is still the same ask, so the thing in front of it
# is looked for as a place however many words it is, and the folder that keeps the hours is the one
# that fixes them - "is the post office open" is as much a place's times as "is tesco open".
_A_PLACE_THAT_KEEPS_HOURS = re.compile(
    r"\b(?:shops?|stores?|supermarkets?|gyms?|pools?|librar(?:y|ies)|chemists?|"
    r"pharmac(?:y|ies)|surger(?:y|ies)|doctors?|dentists?|banks?|garages?|stations?|offices?|"
    r"centres?|centers?|clinics?|cafes?|pubs?|restaurants?|takeaways?|chippys?|markets?|"
    r"museums?|halls?|churches?|schools?|colleges?|tips?|dumps?|post\s+office|"
    r"leisure\s+centre|swimming\s+pool|garden\s+centre|car\s+park)\b")
# The same list, as the thing the line has to name before a day word can make a verb of opening an
# ask about hours: "is the post office open today" is the hours, "is the front door open today" is
# a door. So the day-word arms below require a place, and a door, a lid, a window, an eye or a
# fridge door is therefore never one - however the line words the day.
_A_LINE_THAT_NAMES_A_PLACE = r"(?=[^\n]*" + _A_PLACE_THAT_KEEPS_HOURS.pattern + r")"
# A place word is not enough on its own: "is the garage door open today" names a garage and asks
# about a door, so a door, a gate, a window, a lid or an eye right before the verb of opening is the
# thing that opens, and no hours. This is the fence the place word alone cannot keep.
_NOT_A_FITTING_THAT_OPENS = (r"(?![^\n]*\b(?:doors?|gates?|windows?|lids?|drawers?|eyes?|"
                            r"mouth|flaps?|valves?|caps?|tins?|jars?|boxes?)\s+"
                            r"(?:open|opens|closed|closes|shut|shuts)\b)")
# The day the ask is about. Words of now and a day of the week are what turn "open" into a question
# about hours; on their own they are not one ("the window is open").
_A_DAY_WORD = (r"(?:today|tonight|tomorrow|now|this\b|on\b|at\b|until\b|till\b|late\b|"
               r"for\s+the\s+day|,)")
# Who may use a place is not when it is open: `is the swimming pool open to non members`, `is the
# shop open to offers`, `is the cafe open for lunch`. The word after the verb of opening is the
# whole difference - "open to" and "open for" name the people or the purpose - unless what follows
# is the day itself ("open for the day", "open to the public today" is still not hours, but "open
# for the day" is), so the fence looks at the word after it.
_NOT_OPEN_TO_SOMEBODY = (r"(?![^\n]*\b(?:open|opens)\s+(?:to|for)\s+"
                         r"(?!(?:today|tonight|tomorrow|now|late|the\s+day|the\s+weekend|"
                         r"the\s+summer|christmas|easter)\b))")
_HOURS = re.compile(
    r"\bopening\s+(?:hours?|times?)\b|\bclosing\s+time\b|\blate\s+opening\b|"
    r"\bbank\s+holiday\s+hours\b|"
    r"\b(?:open|opens|closed?|closes|shuts?)\s+(?:until|till|at|on|late|early)\b|"
    + _A_LINE_THAT_NAMES_A_PLACE + _NOT_A_FITTING_THAT_OPENS + _NOT_OPEN_TO_SOMEBODY +
    r"\b(?:is|are|was|were|does|do|will)\s+(?:[\w']+\s+){0,4}?(?:open|opens)\s+"
    r"(?:today|tonight|tomorrow|now|this\s+\w+)\b|"
    + _A_LINE_THAT_NAMES_A_PLACE + _NOT_A_FITTING_THAT_OPENS + _NOT_OPEN_TO_SOMEBODY +
    r"\b(?:is|are|was|were)\s+(?:[\w']+\s+){0,3}?(?:open|opens|closed|closes|shut|shuts)\b"
    r"(?=\s*" + _A_DAY_WORD + r")|"
    + _NOT_A_FITTING_THAT_OPENS + _NOT_OPEN_TO_SOMEBODY +
    r"\b(?:is|are|was|were|does|do)\s+(?:the\s+|a\s+)?(?:\w+\s+){0,2}?"
    + _A_PLACE_THAT_KEEPS_HOURS.pattern + r"\s+(?:open|opens|closed|closes|shut|shuts)\b|"
    + _NOT_A_FITTING_THAT_OPENS + _NOT_OPEN_TO_SOMEBODY +
    _A_PLACE_THAT_KEEPS_HOURS.pattern + r"\s+(?:\w+\s+){0,2}?"
    r"(?:open|opens|closed|closes|shut|shuts)\b(?=\s*" + _A_DAY_WORD + r")|"
    + _NOT_OPEN_TO_SOMEBODY +
    r"\b(?:is|are|was|were)\s+(?:it|they|there(?:\s+anywhere)?|"
    r"(?:the|this|that|my|our|your|any)\s+\w+|"
    r"\w+)\s+open\b|"
    r"\bwhat\s+times?\s+(?:does|do|is|are|will)\b|"
    r"\b(?:when|what\s+times?)\b[^?]{0,30}?\b(?:open|opens|close|closes|closed|shut|shuts)\b")

# Today's sky, not the word for it. Rain and snow as advice ("how do i drive in snow"), as a
# cause ("why does thunder happen") or as a memory ("my wipers judder when its raining") are all
# about something else, so the sky has to be asked about: it is going to rain, the forecast, the
# weather, how hot it is today.
_WEATHER = re.compile(
    r"\bweather\b|\bforecast\b|\bumbrella\b|"
    r"\bhow\s+(?:hot|cold|warm|windy)\s+(?:is|will)\s+it\b|"
    r"\b(?:is|will)\s+it\s+(?:be\s+)?(?:going\s+to\s+)?(?:rain|snow|be\s+sunny|be\s+windy|"
    r"be\s+stormy|be\s+hot|be\s+cold)\b|"
    r"\bit\s+(?:is|will|should|might)\s+(?:be\s+)?(?:rain|snow|sunny|windy|stormy)\b|"
    r"\bheat\s?wave\b|\bcold\s+snap\b|\btemperature\s+(?:today|tomorrow|outside)\b")

# The day's news, not every word that lives in it. "score" is a credit score as often as a
# football one, "results" are exam results, and "whats going on with you" is about the bot, so a
# score has to be *the* score or a fixture, results belong to a match, and the news has to be
# asked for: the news, any news, the latest on, what happened, who won, the score.
_NEWS = re.compile(
    r"\bnews\b|\bheadlines?\b|"
    r"\b(?:whats|what\s+is|what\s+was|anything|any|the\s+latest|latest|breaking|got\s+any)\s+"
    r"(?:the\s+)?(?:news|headlines?)\b|"
    r"\b(?:latest|update[s]?)\s+(?:on|about)\b|"
    r"\b(?:news|press|newspaper)\s+stor(?:y|ies)\s+(?:on|about)\b|"
    r"\b(?:the|any|more)\s+word\s+(?:on|about)\b|"
    r"\bwhats\s+going\s+on\s+(?:in|at|with)\s+the\s+(?:world|news|country|city)\b|"
    r"\bwhats\s+(?:happened|happening)\b|\bwhat\s+(?:is|was)\s+happening\b|"
    r"\belections?\s+(?:today|tonight|this\s+(?:week|year)|results?)\b|"
    r"\bwho\s+won\b|\bwho(?:s|\s+is)\s+winning\b|\bdid\s+(?:\w+\s+){0,3}win\b|"
    r"\bhas\s+(?:\w+\s+){0,3}(?:won|finished|played)\b|"
    r"\bthe\s+score\b|\bwhats\s+the\s+score\b|\bleague\s+table\b|\bthe\s+table\b|"
    r"\bmatch\s+result\b|\b(?:the\s+)?results?\s+(?:of|from)\s+the\s+(?:match|game)\b|"
    r"\btransfers?\s+(?:news|today|latest)\b")

_AVAILABILITY = re.compile(
    r"\b(?:in\s+stock|stock\s+levels?|available|availability|unavailable|sold\s+out|"
    r"vacanc(?:y|ies)|hiring|waiting\s+list|"
    r"bookings?\s+(?:open|available|left|for)|"
    r"(?:make|get|book|check|change|cancel|move|confirm)\s+(?:a\s+|my\s+|the\s+)?booking\b|"
    r"(?:tickets?|places?|spaces?|seats?|rooms?|jobs?|appointments?)\s+(?:\w+\s+){0,2}"
    r"(?:left|going|available|free)\b)")

_TIMETABLE = re.compile(
    r"\b(?:timetables?|next\s+(?:train|bus|flight|boat|ferry|coach)|departures?|arrivals?|"
    r"delay(?:s|ed)?|roadworks?|bus\s+times?|train\s+times?|flight\s+times?|"
    r"traffic\s+(?:report|news|today|now|on\s+the)|"
    r"\bare\s+(?:the\s+)?(?:trains|buses|tubes|flights|ferries|trams)\s+running\b|"
    r"\bis\s+the\s+(?:m\d+|a\d+|motorway|road|bridge|tunnel)\s+(?:closed|open|blocked)\b|"
    r"what\s+time\s+(?:is|does)\s+the\s+(?:train|bus|flight))\b")

# A scheduled service - a train, a bus, a flight, a coach, a ferry, a tram - is not a live thing
# on its own: "how many trains are there in the uk" is a count of rolling stock and the same
# answer next year. What makes it live is being asked about *on a day or at a time*: the thing
# asked about is then the timetable and not the vehicle, whatever shape the ask has. So the two
# have to be there together, and the shape (a count, a superlative) loses to them.
# A time people say in place of the service - "the 8.15", "the 18.20" - names a train, a bus or a
# flight when a verb of going follows it ("is the 8.15 running"), and names nothing when it does
# not ("whats on the 7.30 news").
_A_SERVICE = re.compile(
    r"\b(?:trains?|buses?|bus|trams?|tubes?|underground|metro|flights?|ferry|ferries|"
    r"coach(?:es)?|platform|departures?|arrivals?)\b|"
    r"\bthe\s+\d{1,3}(?:[:.]\d{2})?(?=\s*(?:running|run|runs|leaves|leaving|departs?|"
    r"departing|due|arrives?|arriving|go|goes|going|take|takes|train|bus|flight))")
_A_DAY_OR_TIME = re.compile(
    r"\b(?:today|tonight|tomorrow|yesterday|this\s+(?:morning|afternoon|evening|weekend|week)|"
    r"next\s+(?:week|weekend)|monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"weekends?|bank\s+holiday|christmas|easter)\b|\b\d{1,2}[:.]\d{2}\b|"
    r"\bo'?clock\b|\b\d{1,2}\s?(?:am|pm)\b|\bhalf\s+past\b|\bhow\s+often\b")


class _AServiceOnADay:
    """A named service and a day or a time, both of which have to be there."""

    def __init__(self, service, when):
        self.service, self.when = service, when

    def search(self, text):
        service = self.service.search(text)
        if service is None:
            return None
        when = self.when.search(text)
        if when is None:
            return None
        return service if service.start() <= when.start() else when


# A service's state is the timetable too: a train that is late, cancelled or on time, a bus on
# strike. It is the day's version of the timetable, not a fact about trains in general.
_A_SERVICE_STATE = re.compile(
    r"\b(?:trains?|buses?|bus|flights?|coach(?:es)?|ferry|ferries|trams?)\b.{0,40}?"
    r"\b(?:late|delayed|cancell?ed|on\s+time|on\s+strike|diverted|full\s+up)\b")

_SERVICE_ON_A_DAY = _AServiceOnADay(_A_SERVICE, _A_DAY_OR_TIME)

# A rate is a figure the world keeps changing under the person's feet: it is not the bot's to
# state from memory even when it is right this month.
_RATE = re.compile(
    r"\b(?:interest\s+rate[s]?|exchange\s+rate[s]?|tax\s+rate[s]?|inflation|mortgage\s+rate[s]?|"
    r"minimum\s+wage|price\s+cap|energy\s+cap|"
    r"national\s+insurance\s+(?:rate|contribution[s]?|percent|%)|stamp\s+duty|vat|"
    r"base\s+rate)\b")

_EVENT = re.compile(
    r"\b(?:whats\s+on|what\s+is\s+on|anything\s+on(?!\s+(?:a|an|the|my|your|about|for)\b)|"
    r"events?\s+on|gig\s+guide|show\s+times?|"
    r"cinema\s+times?|fixtures?|opening\s+night|when\s+is\s+the\s+\w+\s+on\b)\b")

# The order the classes are read in: the narrower class first, so "how much is the minimum
# wage" is a rate rather than a wage, and "what time does the bus leave" is a timetable rather
# than a place's hours.
# A word for freshness says the thing is today's version; it does not say the thing is not that
# thing. "what is the latest score" is the score, so the class lookup reads the line without it.
# It is dropped only here: "what is the latest iphone" is still not a definition (see _A_DEFINITION).
_A_FRESHENING = re.compile(
    r"\b(?:latest|current|newest|most\s+recent|up[\s-]to[\s-]date)\s+"
    r"(?!(?:on|about|of|in|from|at|with)\b)")

_CHANGING = (
    ("rate", _RATE),
    ("price", _A_PRICE_ASK),
    ("post", _A_POST_HOLDER),
    ("timetable", _SERVICE_ON_A_DAY),
    ("timetable", _A_SERVICE_STATE),
    ("timetable", _TIMETABLE),
    ("hours", _HOURS),
    ("weather", _WEATHER),
    ("news", _NEWS),
    ("availability", _AVAILABILITY),
    ("event", _EVENT),
)

# An explanation or a how-to is a fact about the world, not today's version of it. "how do
# weather forecasts get it wrong so often" is asking how a thing works, "how do i drive in the
# rain" how to do it, and "what causes train delays" what makes them - none of them is asking
# what the weather is doing or when the next train goes, so the live noun does not decide them.
# A line that also says *now* ("why is my train late today") is about today after all.
_A_HOW_IT_WORKS = re.compile(
    r"\bhow\s+(?:do|does|did)\b|\bwhy\s+(?:do|does|did)\b|\bwhat\s+causes?\b|"
    r"\bwhat\s+caused\b|\bhow\s+come\b")
# "when should i start", "what time do we leave" - the ask is about the person's own plan, not
# about a place's hours or a service's timetable, however the nouns around it read.
_A_MY_OWN_PLAN = re.compile(
    r"\b(?:when|what\s+time)\s+(?:(?:should|shall|do|does|can|could|will|would|must|might|"
    r"had\s+better)\s+)?(?:i|we|you)\b(?!\s+(?:open|opens|close|closes|shut|shuts|serve|"
    r"serves|trade|trades)\b)")
# What time their own appointment is, is their diary and not a place's hours: "what time is the
# funeral", "what time is my scan". A match or a fixture is still a fixture.
_A_AN_OCCASION_OF_THEIR_OWN = re.compile(
    r"\b(?:what|which)\s+time\s+(?:is|are|was|were|does|do|did|will|would)\b.{0,25}?"
    r"\b(?:funeral|wake|meeting|appointment|interview|scan|operation|procedure|checkup|"
    r"check-up|assessment|induction|shift|session|court|hearing|viewing)\b")
_A_SAYS_NOW = re.compile(
    r"\b(?:today|tonight|tomorrow|right\s+now|at\s+the\s+moment|this\s+(?:morning|"
    r"afternoon|evening|week|weekend)|currently|still)\b")

# A sealed fact, in the shapes people ask for one. Each of these is the same answer in ten
# years: a count, a record, a definition, a working, a history, a method.
_A_HOW_MANY = re.compile(r"\bhow\s+many\b")
_A_COUNT = re.compile(r"\bhow\s+many\b|\bhow\s+far\s+is\b|\bhow\s+long\s+is\b|\bhow\s+much\b")
_A_RECORD = re.compile(
    r"\bthe\s+(?:biggest|largest|tallest|oldest|youngest|longest|shortest|highest|lowest|"
    r"deepest|shallowest|fastest|slowest|smallest|richest|poorest|wealthiest|heaviest|"
    r"lightest|widest|narrowest|thinnest|strongest|busiest|rarest|commonest|most\s+common|most\s+popular|"
    r"most\s+\w+|least\s+\w+)\b")
# A definition names the thing. A word for freshness, for the best one or for the main one is not
# the thing: "what is the latest iphone" names a model that changes every year and settles nothing,
# while "what is the latest news" is the news and is settled by its own class.
_A_DEFINITION = re.compile(
    r"\bwhat\s+(?:is|are|was|were)\s+(?:(?:a|an|the)\s+)?"
    r"(?!(?:latest|newest|current|best|worst|main|right|usual|cheapest|nearest|the|a|an|it|that|this|they|these|those)\b)\w+|"
    r"\bwhat\s+does\s+\w+\s+mean\b|"
    r"\bwhat\s+is\s+the\s+meaning\b|\bwhat\s+does\s+(?:a|an|the)?\s*\w+\s+do\b")
_A_WORKING = re.compile(r"\bhow\s+(?:does|do)\b.{0,40}\bwork\b|"
                        r"\bwhy\s+(?:does|do|is|are|did)\b")
_A_HISTORY = re.compile(
    r"\bwhen\s+(?:was|were|did)\b.*\b(?:built|invented|discovered|founded|written|composed|"
    r"painted|made|begin|began|start|end|ended|happen|happened|become)\b|"
    r"\bwho\s+(?:invented|discovered|founded|wrote|composed|built|painted)\b|"
    r"\bhistory\s+of\b")
# A measurement of a thing that does not move: "how tall is everest", "how deep is the ocean".
# "how old is the queen" is left out on purpose - an age is a figure with a date on it.
_A_MEASURE = re.compile(
    r"\bhow\s+(?:tall|high|deep|wide|long|heavy|big|far)\s+is\b|"
    r"\bhow\s+far\s+away\b")
# What a thing is made of is a fact about the thing, not a figure with a date on it.
_A_MADE_OF = re.compile(r"\bmade\s+(?:of|from|out\s+of)\b")
_A_METHOD = re.compile(
    r"\bhow\s+to\b|\bhow\s+(?:do|can|should)\s+(?:i|you|we)\b|\bhow\s+long\s+(?:do|does|should|to)\s+.*"
    r"\b(?:cook|boil|bake|roast|keep|last|take|soak|chill|freeze)\b|"
    r"\bhow\s+often\s+should\s+i\b")

# A line that asks what a *word* means is not asking what the thing is doing: "what does available
# mean" and "what does opening hours mean" were read as the availability and the hours, because the
# live word is the very word being defined. The ask names the word itself, so it settles.
_A_WORD_MEANS = re.compile(
    r"\bwhat\s+(?:does|do|did)\b.{1,40}?\bmean\b\s*[?!.]*\s*$|"
    r"\bwhats?\s+(?:is\s+)?the\s+meaning\s+of\b|\bwhat\s+is\s+(?:the\s+)?meaning\b|"
    r"\bwhat\s+is\s+the\s+definition\s+of\b|\bwhat\s+do\s+you\s+mean\s+by\b|"
    r"\bdefine\b")

_SETTLED = (_A_COUNT, _A_RECORD, _A_DEFINITION, _A_WORKING, _A_HISTORY, _A_MEASURE,
            _A_MADE_OF, _A_METHOD)

# A conversion is arithmetic: the numbers do not move.
_SEALED_ASKS = frozenset(("maths",))


# A line asks something when it says so: an ask the reading already labelled, a question mark,
# a question word anywhere in it, or an auxiliary on the front ("is the shop open", "any jobs
# going"). The label alone is not enough - "any news on the strike" and "timetable for the 42"
# are asks the rest of the reading files as a statement - and a question word anywhere is the
# general rule for the rest, because a line that carries one is asking or quoting an ask.
# A question word only makes a line an ask at the front of it, behind an opener at most. Inside a
# statement it belongs to a relative clause and asks nothing: "the oven door drops when i open
# it" is a report about a door, not a question about opening hours.
_ASKS_WITH_A_QUESTION_WORD = re.compile(
    r"^\s*(?:(?:and|but|so|then|also|ok|okay|right|oh|well|now|sorry|ta|hi|hello|"
    r"excuse\s+me)\s+)*(?:what|whats|what's|when|whens|where|which|who|whose|why|how|"
    r"hows|how's)\b")
# A second question in the same line starts a new clause with an auxiliary: "my train was 40
# minutes late, can i get money back" is two questions and the second one is what they want.
_ASKS_MID_LINE = re.compile(
    r"\b(?:is|are|was|were|do|does|did|can|could|will|would|shall|should|am|have|has|had)\s+"
    r"(?:i|we|you|they)\b")
_ASKS_AFTER_A_COMMA = re.compile(
    r",\s*(?:(?:and|but|so|then|also)\s+)?(?:is|are|was|were|do|does|did|can|could|will|"
    r"would|shall|should|am|have|has|had)\s+(?:i|you|we|they|it|he|she|there|the\s+\w+)\b")
# A question word that starts a new clause after a comma is a second question, whatever the
# clause before it was: "she said shes leaving, what should i do" is a report and an ask.
_ASKS_AFTER_A_COMMA_WORD = re.compile(
    r",\s*(?:(?:and|but|so|then|also)\s+)?(?:what|whats|when|whens|where|which|who|why|how|"
    r"hows)\b")
_ASKS_WITH_AN_AUXILIARY = re.compile(
    r"^(?:is|are|was|were|do|does|did|can|could|will|would|shall|should|has|have|had|any|"
    r"anything|anyone|anyway|tell)\b")


# A question word inside what somebody knows or what was told them asks nothing: "i know what the
# price is" and "i told him what time it starts" are reports, and reporting that you know a figure
# is not asking for it. The verb has to be on the front of the line for that, so "do you know what
# the price is" keeps asking, which is what it is.
_A_REPORTS_THE_ASK = re.compile(
    r"^\s*(?:(?:and|but|so|then|also|well|oh|anyway)\s+)*(?:i|we|they|he|she|everyone|"
    r"someone)\s+(?:already\s+|still\s+|just\s+|now\s+|never\s+|definitely\s+)?"
    r"(?:know|knows|knew|told|tell|tells|said|says|explained|explains|mentioned|mentions|"
    r"remember|remembers|reminded|found\s+out)\b")


def _a_line_asks(read, said):
    """Whether the line asks for something to be told or checked, so a fact is what it wants.

    A request to *do* something - "i need to cancel my booking" - is not an ask about the world,
    so only a question counts here. The things a line was read as asking about (`asks`) and a
    question mark stand on their own.
    """
    if read.get("kind") == "question":
        return True
    if _A_REPORTS_THE_ASK.search(said):
        # The question word is inside the report, so only a question on the front of the line or
        # a question mark makes it an ask.
        return bool("?" in said or _ASKS_WITH_A_QUESTION_WORD.search(said)
                    or _ASKS_WITH_AN_AUXILIARY.match(said.strip())
                    or _ASKS_AFTER_A_COMMA_WORD.search(said.replace(" ,", ",")))
    if read.get("asks"):
        return True
    if read.get("intent") == "question":
        return True
    if "?" in said:
        return True
    return bool(_ASKS_WITH_A_QUESTION_WORD.search(said)
                or _ASKS_MID_LINE.search(said)
                or _ASKS_AFTER_A_COMMA.search(said.replace(" ,", ","))
                or _ASKS_WITH_AN_AUXILIARY.match(said.strip()))


def _as_typed(line):
    """The line exactly as it was typed, lower case and padded, signs and digits kept."""
    said = line.get("text") or line.get("clean") or ""
    if not isinstance(said, str):
        said = ""
    return " " + said.strip().lower() + " "


def _carried_on(read, previous, words):
    """The reading a short follow-up carries on from the last line, or None.

    After "how much is a single to leeds", "and a return" and "is it cheaper after 9" ask the same
    question about the same kind of thing, and read on their own they say nothing about it. The
    carry-on needs all of: this line read as a follow-up, few words, the last line's answer still
    standing, and a different line than the last one - so "and the icing" after a cake is not a
    price, and a reading written during the same turn never carries itself on.
    """
    if not isinstance(previous, dict) or not previous.get("over_time"):
        return None
    if not read.get("followup") or len(words) > _A_FOLLOW_UP_WORDS:
        return None
    if previous.get("text") and previous.get("text") == read.get("text"):
        return None
    return True, previous.get("over_time_what")


def _text(line):
    """The line for matching, in the spelling the writer meant, space-padded for whole words."""
    said = line.get("plain") or line.get("clean") or ""
    if not isinstance(said, str):
        said = ""
    return " " + said.strip().lower() + " "


# The thing itself, with no verb and no question in it, is the world's version asked for: "the
# news", "any headlines", "opening hours", "any delays on the trains this morning", "and the
# weather". A report about the same thing is not an ask, so a verb of being or seeming after the
# noun takes the line back: "the weather looks bad this weekend", "i heard the news".
_BARE_LIVE_LEAD = (r"^\s*(?:(?:and|so|but|then|also|ok|okay|right|oh)\s+|"
                   r"(?:what|how)\s+about\s+)?")
_A_BARE_LIVE = (
    ("news", re.compile(_BARE_LIVE_LEAD + r"(?:the\s+|any\s+|got\s+any\s+)?(?:news|headlines?)\b")),
    ("hours", re.compile(_BARE_LIVE_LEAD + r"(?:the\s+|any\s+)?(?:opening\s+(?:hours|times)|"
                                              r"opening|closing\s+time|bank\s+holiday\s+hours)\b")),
    ("timetable", re.compile(_BARE_LIVE_LEAD + r"(?:the\s+|any\s+)?(?:delays?|roadworks?|"
                                                  r"traffic|bus\s+times?|train\s+times?|"
                                                  r"departures|arrivals|timetable)\b")),
    ("weather", re.compile(_BARE_LIVE_LEAD + r"(?:the\s+|any\s+)?(?:weather|forecast)\b")),
    ("price", re.compile(_BARE_LIVE_LEAD + r"(?:the\s+|any\s+)?(?:price|prices|cost|costs|"
                                            r"fares?|ticket\s+prices?)\b")),
)
_A_REPORTS = re.compile(
    r"\b(?:looks?|looked|seems?|seemed|sounds?|sounded|feels?|felt|was|were|is|are|has|have|"
    r"had|said|says|told|hear|heard|got|get|gets|makes?|made|turns?|turned|went|goes|"
    r"coming|comes|hit|hits|does|doesnt|did|didnt|wont|cant|helps?|ruined|spoils?)\b")

# A line with no question in it that is nothing but the thing itself - "timetable for the 42",
# "bus times", "opening hours" - is a request for that thing. The class word has to be at the
# front, behind nothing but a determiner, and the line has to be no longer than the thing and
# its qualifier, so "i checked the timetable yesterday" and "the price went up again" stay
# statements.
_A_BARE_ASK = 4
# A line that is the thing itself runs a little longer than a bare noun: "any delays on the
# trains this morning" is five words and no verb.
_A_BARE_LIVE_WORDS = 9
# How long a follow-up can be and still be nothing but the question it carries on.
_A_FOLLOW_UP_WORDS = 7
# What may follow the thing itself in a short request for it: when, or a please.
_A_BARE_TAIL = re.compile(
    r"^(?:for|on|at|in|this|next|today|tonight|tomorrow|now|here|there|please|pls|thanks|ta|"
    r"anyone|anywhere)\b")
_A_DETERMINER = frozenset(("", "the", "a", "an", "any", "your", "this", "our", "these"))


def over_time(line, read, previous=None, carrying_on=False):
    """Whether the line asks about something that holds only for the day: (True/False/None, what).

    See the module docstring. `what` is the class of changing thing (`price`, `hours`,
    `weather`, `news`, `availability`, `timetable`, `rate`, `event`, `post`) when the answer is
    True, and None for the other two answers. `previous` is the last turn's reading, used only
    for a follow-up that says nothing of its own: `carrying_on` asks for that second look alone,
    once the reading of this line is complete, and answers None when the line carries nothing on.
    """
    read = read if isinstance(read, dict) else {}
    text = _text(line if isinstance(line, dict) else {})
    asking = _a_line_asks(read, text)
    words = text.split()
    bare = len(words) <= _A_BARE_ASK
    if asking and _A_HOW_IT_WORKS.search(text) and not _A_SAYS_NOW.search(text):
        return False, None
    # A sum is arithmetic, and a year that has gone is a date: both are settled before any class
    # is looked for, whichever live word sits next to them.
    if _A_ARITHMETIC.search(text) or _A_ARITHMETIC.search(_as_typed(line)):
        return False, None
    if (_SEALED_ASKS & set(read.get("asks") or ()) and _A_HAS_A_NUMBER.search(text)
            and not _A_AN_AMOUNT_OF_A_THING.search(text)):
        return False, None
    if (_A_PAST_YEAR.search(text) or _A_HOW_OLD_IS_THE_WORLD.search(text)
            or _A_HISTORY_ITSELF.search(text)):
        return False, None
    if _A_A_DIFFERENCE.search(text):
        return False, None
    # How hot, deep or heavy a named thing is is a measurement of that thing, not the sky here.
    if _A_HOW_A_THING_MEASURES.search(text) and not _A_WEATHER_HERE.search(text):
        return False, None
    # A traffic light is not traffic, and "the weather plan" is a plan about the weather.
    if _A_A_TRAFFIC_LIGHT.search(text):
        return None, None
    if _A_A_PLAN_ABOUT_THE_WEATHER.search(text) and not _A_WEATHER_HERE.search(text):
        return None, None
    # A quantity of a thing is a fact about the thing: how much water a bath holds, how much
    # water a day to drink, how much pasta for four. None of it is a figure the world sets.
    if (_A_HOW_MUCH_IT_HOLDS.search(text) or _A_HOW_MUCH_IS_IN.search(text)
            or _A_HOW_MUCH_ENOUGH.search(text) or _A_HOW_MUCH_A_FEELING.search(text)):
        return False, None
    if _A_AN_OCCASION_OF_THEIR_OWN.search(text):
        return None, None
    # A conversion is arithmetic and a measure of a unit is a fact about the unit, unless a money
    # word is in the line: "how much is a pint of milk" is what it costs.
    if not _MONEY.search(text) and (_A_A_CONVERSION.search(text)
                                    or _A_HOW_MUCH_OF_A_UNIT.search(text)):
        return False, None
    if _A_HOW_MUCH_I_SPENT.search(text) or _A_MY_OWN_FIGURE.search(text):
        return None, None
    if _A_THE_CLOCK.search(text):
        return None, None
    if _A_DID_YOU_SEE.search(text):
        return None, None
    if _A_BARE_RECORD.search(text) and not asking:
        return False, None
    # A word for freshness does not change what the thing is: "what is the latest score" is the
    # score and "the current price of petrol" is the price.
    fresh = _A_FRESHENING.sub(" ", text)
    if _A_WORD_MEANS.search(text):
        return False, None
    # The thing itself and nothing else is the world's version asked for.
    for what, pattern in _A_BARE_LIVE:
        found = pattern.search(fresh)
        if found and not _A_REPORTS.search(text) and len(words) <= _A_BARE_LIVE_WORDS:
            return True, what
    for what, pattern in _CHANGING:
        found = pattern.search(fresh)
        if not found:
            continue
        # A person's own plan is not a place's hours or a service's timetable.
        if what in ("hours", "timetable", "event") and _A_MY_OWN_PLAN.search(text):
            continue
        # "what is stamp duty", "what is inflation": the line asks what the live word itself is,
        # which is a definition and settles. With a determiner the line asks for the thing's
        # state instead - "what is the weather", "what is the price" - and stays live.
        if (_A_DEFINITION.search(text)
                and fresh[:found.start()].strip() in ("what is", "what are", "whats", "what's")
                and not fresh[found.end():].strip(" ?!.,")):
            return False, None
        if asking:
            return True, what
        # A short line that is the thing itself, with nothing said about it, is a request for
        # the world's version: "timetable for the 42", "bus times", "opening hours". A statement
        # about the thing is not - "inflation is 4", "the weather doesnt help" - so the line has
        # to run out after the class word, or carry only a tail that says when.
        if bare and not _A_REPORTS.search(text):
            tail = fresh[found.end():].strip()
            if (fresh[:found.start()].strip() in _A_DETERMINER
                    and (not tail or _A_BARE_TAIL.match(tail))):
                return True, what
    if carrying_on:
        return _carried_on(read, previous, words)
    if not asking:
        return None, None
    if _SEALED_ASKS & set(read.get("asks") or ()):
        return False, None
    for pattern in _SETTLED:
        if pattern.search(text):
            return False, None
    return None, None
